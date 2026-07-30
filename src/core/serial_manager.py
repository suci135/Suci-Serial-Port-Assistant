"""
串口管理器
"""

import asyncio
import serial
import serial.tools.list_ports
from typing import List, Optional, Callable, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal
import threading
import time
from .data_framer import DataFrameParser


class SerialDevice:
    """串口设备信息"""
    
    def __init__(self, port_info):
        self.port = port_info.device
        self.description = port_info.description
        self.hwid = port_info.hwid
        self.vid = port_info.vid
        self.pid = port_info.pid
        self.serial_number = port_info.serial_number
        self.manufacturer = port_info.manufacturer
        self.product = port_info.product
    
    @property
    def display_name(self) -> str:
        """显示名称"""
        if self.description and self.description != "n/a":
            return f"{self.port} - {self.description}"
        return self.port
    
    def __str__(self):
        return self.display_name


class SerialManager(QObject):
    """串口管理器"""
    
    # 信号定义
    device_connected = pyqtSignal()
    device_disconnected = pyqtSignal()
    data_received = pyqtSignal(bytes)
    error_occurred = pyqtSignal(str)
    connecting_status = pyqtSignal(str)  # 连接状态信号
    
    def __init__(self):
        super().__init__()
        self._serial: Optional[serial.Serial] = None
        self._is_connected = False
        self._read_thread: Optional[threading.Thread] = None
        self._stop_reading = threading.Event()
        self._reconnect_stop = threading.Event()
        self._reconnect_thread: Optional[threading.Thread] = None
        self._last_port: Optional[str] = None
        self._manual_disconnect = False
        self._auto_reconnect = True
        self._frame_parser = DataFrameParser()
        self._config = {
            'baudrate': 9600,
            'bytesize': serial.EIGHTBITS,
            'parity': serial.PARITY_NONE,
            'stopbits': serial.STOPBITS_ONE,
            'timeout': 1.0,
            'xonxoff': False,
            'rtscts': False,
            'dsrdtr': False
        }
    
    @staticmethod
    def list_devices() -> List[SerialDevice]:
        """列出所有可用的串口设备"""
        ports = serial.tools.list_ports.comports()
        return [SerialDevice(port) for port in ports]
    
    def configure(self, config: Dict[str, Any]):
        """配置串口参数（支持动态修改）"""
        # 映射配置参数
        if 'baud_rate' in config:
            self._config['baudrate'] = config['baud_rate']
        
        if 'data_bits' in config:
            data_bits_map = {5: serial.FIVEBITS, 6: serial.SIXBITS, 
                           7: serial.SEVENBITS, 8: serial.EIGHTBITS}
            self._config['bytesize'] = data_bits_map.get(config['data_bits'], serial.EIGHTBITS)
        
        if 'parity' in config:
            parity_map = {'None': serial.PARITY_NONE, 'Even': serial.PARITY_EVEN,
                         'Odd': serial.PARITY_ODD, 'Mark': serial.PARITY_MARK,
                         'Space': serial.PARITY_SPACE}
            self._config['parity'] = parity_map.get(config['parity'], serial.PARITY_NONE)
        
        if 'stop_bits' in config:
            stop_bits_map = {1: serial.STOPBITS_ONE, 1.5: serial.STOPBITS_ONE_POINT_FIVE,
                           2: serial.STOPBITS_TWO}
            self._config['stopbits'] = stop_bits_map.get(config['stop_bits'], serial.STOPBITS_ONE)
        
        if 'flow_control' in config:
            flow_control = config['flow_control']
            self._config['xonxoff'] = flow_control == 'XON/XOFF'
            self._config['rtscts'] = flow_control == 'RTS/CTS'
            self._config['dsrdtr'] = flow_control == 'DSR/DTR'
        
        if 'read_timeout' in config:
            self._config['timeout'] = config['read_timeout']
        
        # 如果已连接，动态应用配置
        if self._is_connected and self._serial and self._serial.is_open:
            try:
                if 'baud_rate' in config:
                    self._serial.baudrate = self._config['baudrate']
                if 'data_bits' in config:
                    self._serial.bytesize = self._config['bytesize']
                if 'parity' in config:
                    self._serial.parity = self._config['parity']
                if 'stop_bits' in config:
                    self._serial.stopbits = self._config['stopbits']
                if 'flow_control' in config:
                    self._serial.xonxoff = self._config['xonxoff']
                    self._serial.rtscts = self._config['rtscts']
                    self._serial.dsrdtr = self._config['dsrdtr']
                if 'read_timeout' in config:
                    self._serial.timeout = self._config['timeout']
            except Exception as e:
                self.error_occurred.emit(f"动态修改配置失败: {str(e)}")
    
    def connect(self, port: str, suppress_error: bool = False) -> bool:
        """连接到指定串口"""
        self._manual_disconnect = False
        self._last_port = port
        if self._is_connected:
            self.disconnect()
        
        try:
            self.connecting_status.emit("正在连接...")
            self._serial = serial.Serial(port, **self._config)
            self._is_connected = True
            self._start_reading()
            self.connecting_status.emit("")
            self.device_connected.emit()
            return True
        except serial.SerialException as e:
            self.connecting_status.emit("")
            if not suppress_error:
                self.error_occurred.emit(f"连接串口失败: {str(e)}")
            return False
    
    def disconnect(self):
        """断开串口连接"""
        self._manual_disconnect = True
        self._reconnect_stop.set()
        if not self._is_connected:
            return
        
        self._is_connected = False
        self._stop_reading.set()
        
        if self._read_thread and self._read_thread.is_alive():
            self._read_thread.join(timeout=2.0)
        
        if self._serial and self._serial.is_open:
            self._serial.close()
        
        self._serial = None
        self._stop_reading.clear()
        self._frame_parser.reset()
        self.device_disconnected.emit()

    def set_auto_reconnect(self, enabled: bool):
        """Enable or disable reconnect attempts after an unexpected disconnect."""
        self._auto_reconnect = enabled
        if not enabled:
            self._reconnect_stop.set()

    def set_frame_separator(self, separator: Optional[bytes]):
        """Use a separator for complete frames, or None for idle flushing."""
        self._frame_parser.separator = separator
        self._frame_parser.reset()

    def _handle_unexpected_disconnect(self, error: str):
        if not self._is_connected:
            return
        self._is_connected = False
        self._stop_reading.set()
        if self._serial and self._serial.is_open:
            self._serial.close()
        self._serial = None
        self.error_occurred.emit(f"串口已断开: {error}")
        self.device_disconnected.emit()
        if self._auto_reconnect and not self._manual_disconnect and self._last_port:
            self._start_reconnect()

    def _start_reconnect(self):
        if self._reconnect_thread and self._reconnect_thread.is_alive():
            return
        self._reconnect_stop.clear()
        self._reconnect_thread = threading.Thread(target=self._reconnect_loop, daemon=True)
        self._reconnect_thread.start()

    def _reconnect_loop(self):
        while not self._reconnect_stop.wait(2.0):
            if self._manual_disconnect or not self._last_port:
                return
            self.connecting_status.emit("正在重连...")
            if self.connect(self._last_port, suppress_error=True):
                return
        self.connecting_status.emit("")
    
    def _start_reading(self):
        """启动数据读取线程"""
        self._stop_reading.clear()
        self._read_thread = threading.Thread(target=self._read_loop, daemon=True)
        self._read_thread.start()
    
    def _read_loop(self):
        """数据读取循环"""
        buffer = bytearray()
        last_data_time = time.time()
        
        while not self._stop_reading.is_set() and self._is_connected:
            try:
                if self._serial and self._serial.in_waiting > 0:
                    data = self._serial.read(self._serial.in_waiting)
                    if data:
                        buffer.extend(data)
                        last_data_time = time.time()
                
                # 如果缓冲区有数据且超过一定时间没有新数据，则发送缓冲区数据
                current_time = time.time()
                if buffer and (current_time - last_data_time) > 0.01:  # 10ms 超时
                    if self._frame_parser.separator:
                        for frame in self._frame_parser.feed(bytes(buffer)):
                            self.data_received.emit(frame)
                    else:
                        self.data_received.emit(bytes(buffer))
                    buffer.clear()
                
                time.sleep(0.001)  # 1ms 延迟
                
            except serial.SerialException as e:
                if self._is_connected:
                    err_msg = str(e)
                    # 设备真正断开才报错弹窗，临时读取异常只打印日志
                    if self._serial and not self._serial.is_open:
                        self._handle_unexpected_disconnect(err_msg)
                        break
                    else:
                        print(f"[SerialManager] 读取异常(忽略): {err_msg}")
                        continue
            except Exception as e:
                if self._is_connected:
                    print(f"[SerialManager] 未知异常(忽略): {str(e)}")
                    continue
        
        # 发送剩余缓冲区数据
        if buffer:
            if self._frame_parser.separator:
                for frame in self._frame_parser.feed(bytes(buffer)):
                    self.data_received.emit(frame)
                remaining = self._frame_parser.flush()
                if remaining:
                    self.data_received.emit(remaining)
            else:
                self.data_received.emit(bytes(buffer))
    
    def send_data(self, data: bytes) -> bool:
        """发送数据"""
        if not self._is_connected or not self._serial:
            self.error_occurred.emit("设备未连接")
            return False
        
        try:
            bytes_written = self._serial.write(data)
            self._serial.flush()
            return bytes_written == len(data)
        except serial.SerialException as e:
            self.error_occurred.emit(f"发送数据失败: {str(e)}")
            return False
    
    def send_hex_string(self, hex_string: str) -> bool:
        """发送十六进制字符串"""
        try:
            # 移除空格和非十六进制字符
            hex_string = ''.join(c for c in hex_string if c in '0123456789ABCDEFabcdef')
            if len(hex_string) % 2 != 0:
                hex_string = '0' + hex_string  # 补齐奇数长度
            
            data = bytes.fromhex(hex_string)
            return self.send_data(data)
        except ValueError as e:
            self.error_occurred.emit(f"十六进制格式错误: {str(e)}")
            return False
    
    def send_text(self, text: str, encoding: str = 'utf-8') -> bool:
        """发送文本数据"""
        try:
            data = text.encode(encoding)
            return self.send_data(data)
        except UnicodeEncodeError as e:
            self.error_occurred.emit(f"文本编码失败: {str(e)}")
            return False
    
    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._is_connected
    
    @property
    def current_port(self) -> Optional[str]:
        """当前连接的端口"""
        return self._serial.port if self._serial else None
    
    @property
    def connection_info(self) -> Dict[str, Any]:
        """连接信息"""
        if not self._is_connected or not self._serial:
            return {}
        
        return {
            'port': self._serial.port,
            'baudrate': self._serial.baudrate,
            'bytesize': self._serial.bytesize,
            'parity': self._serial.parity,
            'stopbits': self._serial.stopbits,
            'timeout': self._serial.timeout,
            'xonxoff': self._serial.xonxoff,
            'rtscts': self._serial.rtscts,
            'dsrdtr': self._serial.dsrdtr
        }
