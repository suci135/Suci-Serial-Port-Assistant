"""
蓝牙管理器 - 支持多种蓝牙库
"""

import asyncio
import threading
import time
from typing import List, Optional, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal

# 尝试导入蓝牙库
BLUETOOTH_BACKEND = None
try:
    import bluetooth
    BLUETOOTH_BACKEND = 'pybluez'
    print("使用 PyBluez 蓝牙库")
except ImportError:
    try:
        import bleak
        BLUETOOTH_BACKEND = 'bleak'
        print("使用 Bleak 蓝牙库")
    except ImportError:
        BLUETOOTH_BACKEND = None
        print("警告: 未安装蓝牙库，蓝牙功能不可用")
        print("  Windows 推荐: pip install bleak")
        print("  Linux/macOS: pip install pybluez")


class BluetoothDevice:
    """蓝牙设备信息"""
    
    def __init__(self, address: str, name: str = None):
        self.address = address
        self.name = name or "未知设备"
    
    @property
    def display_name(self) -> str:
        """显示名称"""
        return f"{self.name} ({self.address})"
    
    def __str__(self):
        return self.display_name


class BluetoothManager(QObject):
    """蓝牙管理器 - 支持 PyBluez 和 Bleak"""
    
    # 信号定义
    device_connected = pyqtSignal()
    device_disconnected = pyqtSignal()
    data_received = pyqtSignal(bytes)
    error_occurred = pyqtSignal(str)
    scan_completed = pyqtSignal(list)  # 扫描完成信号
    connecting_status = pyqtSignal(str)  # 连接状态信号
    
    def __init__(self):
        super().__init__()
        self._socket = None
        self._client = None  # Bleak client
        self._is_connected = False
        self._read_thread: Optional[threading.Thread] = None
        self._stop_reading = threading.Event()
        self._current_device: Optional[BluetoothDevice] = None
        self._loop = None  # asyncio loop for Bleak
        
        # BLE 特征 UUID（通用串口服务）
        # Nordic UART Service (NUS) - 默认值
        self.UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
        self.UART_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"  # 写入
        self.UART_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"  # 通知
        
        # 实际使用的 UUID（连接时自动检测）
        self._write_char_uuid = None
        self._notify_char_uuid = None
        
        if not BLUETOOTH_BACKEND:
            print("蓝牙功能不可用")
    
    @staticmethod
    def is_available() -> bool:
        """检查蓝牙功能是否可用"""
        return BLUETOOTH_BACKEND is not None
    
    @staticmethod
    def get_backend() -> Optional[str]:
        """获取当前使用的蓝牙后端"""
        return BLUETOOTH_BACKEND
    
    def scan_devices(self, duration: int = 8) -> List[BluetoothDevice]:
        """扫描附近的蓝牙设备"""
        if not BLUETOOTH_BACKEND:
            self.error_occurred.emit("蓝牙功能不可用，请安装蓝牙库")
            return []
        
        if BLUETOOTH_BACKEND == 'pybluez':
            return self._scan_devices_pybluez(duration)
        elif BLUETOOTH_BACKEND == 'bleak':
            return self._scan_devices_bleak(duration)
        
        return []
    
    def _scan_devices_pybluez(self, duration: int) -> List[BluetoothDevice]:
        """使用 PyBluez 扫描设备"""
        try:
            print(f"开始扫描蓝牙设备（PyBluez），持续 {duration} 秒...")
            nearby_devices = bluetooth.discover_devices(
                duration=duration,
                lookup_names=True,
                flush_cache=True
            )
            
            devices = []
            for addr, name in nearby_devices:
                devices.append(BluetoothDevice(addr, name))
            
            print(f"扫描完成，发现 {len(devices)} 个设备")
            self.scan_completed.emit(devices)
            return devices
            
        except Exception as e:
            error_msg = f"扫描蓝牙设备失败: {str(e)}"
            print(error_msg)
            self.error_occurred.emit(error_msg)
            return []
    
    def _scan_devices_bleak(self, duration: int) -> List[BluetoothDevice]:
        """使用 Bleak 扫描设备"""
        try:
            from bleak import BleakScanner
            import threading
            
            print(f"开始扫描蓝牙设备（Bleak），持续 {duration} 秒...")
            
            # 使用线程来运行异步扫描，避免事件循环冲突
            result = {'devices': [], 'error': None}
            
            def scan_thread():
                try:
                    import asyncio
                    # 在新线程中创建新的事件循环
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    async def scan():
                        devices_found = await BleakScanner.discover(timeout=duration)
                        return devices_found
                    
                    devices_found = loop.run_until_complete(scan())
                    loop.close()
                    
                    result['devices'] = devices_found
                except Exception as e:
                    result['error'] = str(e)
            
            thread = threading.Thread(target=scan_thread, daemon=True)
            thread.start()
            thread.join(timeout=duration + 5)  # 扫描时间 + 5秒缓冲
            
            if result['error']:
                raise Exception(result['error'])
            
            devices = []
            for device in result['devices']:
                name = device.name or "未知设备"
                devices.append(BluetoothDevice(device.address, name))
            
            print(f"扫描完成，发现 {len(devices)} 个设备")
            self.scan_completed.emit(devices)
            return devices
            
        except OSError as e:
            # Windows 蓝牙未就绪错误
            if "WinError -2147020577" in str(e) or "设备未就绪" in str(e):
                error_msg = "蓝牙适配器未就绪\n\n请检查：\n1. 蓝牙是否已开启\n2. 蓝牙驱动是否正常\n3. 是否有蓝牙硬件"
            else:
                error_msg = f"扫描蓝牙设备失败: {str(e)}"
            print(error_msg)
            self.error_occurred.emit(error_msg)
            return []
        except Exception as e:
            error_msg = f"扫描蓝牙设备失败: {str(e)}"
            print(error_msg)
            self.error_occurred.emit(error_msg)
            return []
    
    def connect(self, address: str, port: int = 1) -> bool:
        """连接到指定蓝牙设备
        
        Args:
            address: 蓝牙设备地址 (MAC地址)
            port: RFCOMM端口号（仅 PyBluez），默认为1
        """
        if not BLUETOOTH_BACKEND:
            self.error_occurred.emit("蓝牙功能不可用")
            return False
        
        if self._is_connected:
            self.disconnect()
        
        if BLUETOOTH_BACKEND == 'pybluez':
            return self._connect_pybluez(address, port)
        elif BLUETOOTH_BACKEND == 'bleak':
            return self._connect_bleak(address)
        
        return False
    
    def _connect_pybluez(self, address: str, port: int) -> bool:
        """使用 PyBluez 连接"""
        try:
            print(f"正在连接到蓝牙设备（PyBluez）: {address}:{port}")
            self._socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self._socket.connect((address, port))
            self._socket.settimeout(1.0)
            
            self._is_connected = True
            self._current_device = BluetoothDevice(address)
            self._start_reading()
            
            print("蓝牙连接成功")
            self.device_connected.emit()
            return True
            
        except Exception as e:
            error_msg = f"连接蓝牙设备失败: {str(e)}"
            print(error_msg)
            self.error_occurred.emit(error_msg)
            return False
    
    def _connect_bleak(self, address: str) -> bool:
        """使用 Bleak 连接"""
        try:
            from bleak import BleakClient
            import threading
            
            print(f"正在连接到蓝牙设备（Bleak）: {address}")
            self.connecting_status.emit("正在连接...")
            
            # 使用线程来运行异步连接，避免事件循环冲突
            result = {'success': False, 'error': None, 'client': None, 'services': None}
            
            # 创建一个持久的后台线程来运行事件循环
            def event_loop_thread():
                try:
                    import asyncio
                    # 在新线程中创建新的事件循环
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result['loop'] = loop
                    
                    async def connect_async():
                        # 增加连接超时时间到 30 秒
                        client = BleakClient(address, timeout=30.0)
                        await client.connect()
                        
                        # 获取所有服务和特征（使用 services 属性）
                        services = client.services
                        
                        # 尝试查找可用的写入和通知特征
                        write_char = None
                        notify_char = None
                        
                        # 查找同时支持 write 和 notify 的特征（优先）
                        for service in services:
                            for char in service.characteristics:
                                props = char.properties
                                # 如果同时支持写入和通知，优先使用这个
                                if "notify" in props and ("write" in props or "write-without-response" in props):
                                    write_char = char.uuid
                                    notify_char = char.uuid
                                    print(f"找到双向特征（读写）: {char.uuid}")
                                    break
                            if write_char and notify_char:
                                break
                        
                        # 如果没找到双向特征，分别查找
                        if not write_char or not notify_char:
                            for service in services:
                                for char in service.characteristics:
                                    props = char.properties
                                    
                                    # 查找通知特征
                                    if not notify_char and "notify" in props:
                                        notify_char = char.uuid
                                        print(f"找到通知特征: {char.uuid}")
                                    
                                    # 查找写入特征
                                    if not write_char:
                                        if "write-without-response" in props:
                                            write_char = char.uuid
                                            print(f"找到写入特征(无响应): {char.uuid}")
                                        elif "write" in props:
                                            write_char = char.uuid
                                            print(f"找到写入特征: {char.uuid}")
                        
                        # 启动通知接收
                        if notify_char:
                            try:
                                await client.start_notify(notify_char, self._notification_handler)
                                print(f"已启动通知接收: {notify_char}")
                            except Exception as e:
                                print(f"启动通知失败: {e}")
                        else:
                            print("警告: 未找到通知特征，无法接收数据")
                        
                        return client, write_char, notify_char
                    
                    # 执行连接
                    client, write_char, notify_char = loop.run_until_complete(connect_async())
                    result['client'] = client
                    result['write_char'] = write_char
                    result['notify_char'] = notify_char
                    result['success'] = client.is_connected
                    
                    # 保持事件循环运行，处理通知
                    print("BLE 事件循环开始运行...")
                    loop.run_forever()
                    print("BLE 事件循环已停止")
                    
                except Exception as e:
                    result['error'] = str(e)
                    print(f"事件循环错误: {e}")
            
            # 启动事件循环线程
            loop_thread = threading.Thread(target=event_loop_thread, daemon=True)
            loop_thread.start()
            
            # 等待连接完成
            import time
            timeout = 35
            start_time = time.time()
            while time.time() - start_time < timeout:
                if result.get('success') or result.get('error'):
                    break
                time.sleep(0.1)
            
            if result.get('error'):
                self.connecting_status.emit("")
                raise Exception(result['error'])
            
            if result.get('success') and result.get('client'):
                self._client = result['client']
                self._loop = result.get('loop')
                self._write_char_uuid = result.get('write_char') or self.UART_RX_CHAR_UUID
                self._notify_char_uuid = result.get('notify_char') or self.UART_TX_CHAR_UUID
                self._is_connected = True
                self._current_device = BluetoothDevice(address)
                
                print(f"蓝牙连接成功")
                print(f"使用写入特征: {self._write_char_uuid}")
                print(f"使用通知特征: {self._notify_char_uuid}")
                self.connecting_status.emit("")
                self.device_connected.emit()
                return True
            else:
                self.connecting_status.emit("")
                error_msg = "连接超时或失败，请确保：\n1. 设备在范围内\n2. 设备未被其他程序占用\n3. 设备支持 BLE 连接"
                print(error_msg)
                self.error_occurred.emit(error_msg)
                return False
            
        except Exception as e:
            self.connecting_status.emit("")
            error_msg = f"连接蓝牙设备失败: {str(e)}"
            print(error_msg)
            self.error_occurred.emit(error_msg)
            if self._loop:
                try:
                    self._loop.call_soon_threadsafe(self._loop.stop)
                except:
                    pass
                self._loop = None
            return False
    
    def _notification_handler(self, sender, data: bytearray):
        """BLE 通知处理器"""
        if data:
            print(f"收到 BLE 数据: {len(data)} 字节 - {data.hex()}")
            self.data_received.emit(bytes(data))
    
    def disconnect(self):
        """断开蓝牙连接"""
        if not self._is_connected:
            return
        
        print("正在断开蓝牙连接...")
        self._is_connected = False
        self._stop_reading.set()
        
        if self._read_thread and self._read_thread.is_alive():
            self._read_thread.join(timeout=2.0)
        
        if BLUETOOTH_BACKEND == 'pybluez' and self._socket:
            try:
                self._socket.close()
            except:
                pass
            self._socket = None
        elif BLUETOOTH_BACKEND == 'bleak' and self._client:
            try:
                # 在事件循环中断开连接
                if self._loop and not self._loop.is_closed():
                    async def disconnect_async():
                        if self._client and self._client.is_connected:
                            await self._client.disconnect()
                    
                    # 调度断开任务
                    future = asyncio.run_coroutine_threadsafe(disconnect_async(), self._loop)
                    try:
                        future.result(timeout=2.0)
                    except:
                        pass
                    
                    # 停止事件循环
                    self._loop.call_soon_threadsafe(self._loop.stop)
            except Exception as e:
                print(f"断开连接错误: {e}")
            
            self._client = None
            self._loop = None
        
        self._current_device = None
        self._stop_reading.clear()
        print("蓝牙已断开")
        self.device_disconnected.emit()
    
    def _start_reading(self):
        """启动数据读取线程"""
        self._stop_reading.clear()
        self._read_thread = threading.Thread(target=self._read_loop, daemon=True)
        self._read_thread.start()
    
    def _read_loop(self):
        """数据读取循环"""
        if BLUETOOTH_BACKEND == 'pybluez':
            self._read_loop_pybluez()
        elif BLUETOOTH_BACKEND == 'bleak':
            self._read_loop_bleak()
    
    def _read_loop_pybluez(self):
        """PyBluez 读取循环"""
        buffer = bytearray()
        last_data_time = time.time()
        
        while not self._stop_reading.is_set() and self._is_connected:
            try:
                if self._socket:
                    try:
                        data = self._socket.recv(1024)
                        if data:
                            buffer.extend(data)
                            last_data_time = time.time()
                    except bluetooth.BluetoothError as e:
                        if "timed out" not in str(e).lower():
                            raise
                
                current_time = time.time()
                if buffer and (current_time - last_data_time) > 0.01:
                    self.data_received.emit(bytes(buffer))
                    buffer.clear()
                
                time.sleep(0.001)
                
            except Exception as e:
                if self._is_connected:
                    error_msg = f"读取数据失败: {str(e)}"
                    print(error_msg)
                    self.error_occurred.emit(error_msg)
                break
        
        if buffer:
            self.data_received.emit(bytes(buffer))
    
    def _read_loop_bleak(self):
        """Bleak 读取循环 - BLE 使用通知机制"""
        # BLE 设备通过通知机制接收数据，已在连接时设置
        # 这里保持线程运行以维持连接
        print("Bleak 读取线程启动（使用通知机制接收数据）")
        while not self._stop_reading.is_set() and self._is_connected:
            time.sleep(0.1)
        print("Bleak 读取线程结束")
    
    def send_data(self, data: bytes) -> bool:
        """发送数据"""
        if not self._is_connected:
            self.error_occurred.emit("设备未连接")
            return False
        
        if BLUETOOTH_BACKEND == 'pybluez':
            return self._send_data_pybluez(data)
        elif BLUETOOTH_BACKEND == 'bleak':
            return self._send_data_bleak(data)
        
        return False
    
    def _send_data_pybluez(self, data: bytes) -> bool:
        """使用 PyBluez 发送数据"""
        try:
            self._socket.send(data)
            return True
        except Exception as e:
            error_msg = f"发送数据失败: {str(e)}"
            print(error_msg)
            self.error_occurred.emit(error_msg)
            return False
    
    def _send_data_bleak(self, data: bytes) -> bool:
        """使用 Bleak 发送数据"""
        if not self._write_char_uuid:
            error_msg = "未找到可写入的特征，无法发送数据"
            print(error_msg)
            self.error_occurred.emit(error_msg)
            return False
        
        try:
            import asyncio
            
            print(f"[BLE发送] 使用特征: {self._write_char_uuid}")
            print(f"[BLE发送] 数据长度: {len(data)} 字节")
            print(f"[BLE发送] 数据内容: {data}")
            print(f"[BLE发送] HEX: {data.hex()}")
            
            # 直接在事件循环中调度任务，不阻塞
            if self._loop and not self._loop.is_closed():
                async def write_async():
                    try:
                        # 尝试使用带响应的写入（response=True）
                        await self._client.write_gatt_char(self._write_char_uuid, data, response=True)
                        print(f"[BLE发送] ✓ 成功发送 {len(data)} 字节（带响应）")
                    except Exception as e:
                        # 如果带响应失败，尝试不带响应
                        print(f"[BLE发送] 带响应写入失败，尝试无响应模式: {e}")
                        try:
                            await self._client.write_gatt_char(self._write_char_uuid, data, response=False)
                            print(f"[BLE发送] ✓ 成功发送 {len(data)} 字节（无响应）")
                        except Exception as e2:
                            print(f"[BLE发送] ✗ 发送失败: {e2}")
                            self.error_occurred.emit(f"发送数据失败: {str(e2)}")
                
                # 使用 call_soon_threadsafe 非阻塞调度
                asyncio.run_coroutine_threadsafe(write_async(), self._loop)
                return True
            else:
                error_msg = "蓝牙连接已断开"
                print(error_msg)
                self.error_occurred.emit(error_msg)
                return False
                
        except Exception as e:
            error_msg = f"发送数据失败: {str(e)}"
            print(error_msg)
            self.error_occurred.emit(error_msg)
            return False
    
    def send_hex_string(self, hex_string: str) -> bool:
        """发送十六进制字符串"""
        try:
            hex_string = ''.join(c for c in hex_string if c in '0123456789ABCDEFabcdef')
            if len(hex_string) % 2 != 0:
                hex_string = '0' + hex_string
            
            data = bytes.fromhex(hex_string)
            return self.send_data(data)
        except ValueError as e:
            error_msg = f"十六进制格式错误: {str(e)}"
            print(error_msg)
            self.error_occurred.emit(error_msg)
            return False
    
    def send_text(self, text: str, encoding: str = 'utf-8') -> bool:
        """发送文本数据"""
        try:
            data = text.encode(encoding)
            print(f"[蓝牙发送文本] 原始: {text}")
            print(f"[蓝牙发送文本] 编码: {encoding}")
            print(f"[蓝牙发送文本] 字节: {data}")
            print(f"[蓝牙发送文本] HEX: {data.hex()}")
            return self.send_data(data)
        except UnicodeEncodeError as e:
            error_msg = f"文本编码失败: {str(e)}"
            print(error_msg)
            self.error_occurred.emit(error_msg)
            return False
    
    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._is_connected
    
    @property
    def current_device(self) -> Optional[BluetoothDevice]:
        """当前连接的设备"""
        return self._current_device
    
    @property
    def connection_info(self) -> Dict[str, Any]:
        """连接信息"""
        if not self._is_connected or not self._current_device:
            return {}
        
        return {
            'address': self._current_device.address,
            'name': self._current_device.name,
            'type': f'Bluetooth ({BLUETOOTH_BACKEND})'
        }
