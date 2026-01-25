"""
macOS 原生风格串口调试工具 UI - 仅支持串口
严格遵循 macOS Human Interface Guidelines
"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from datetime import datetime

from ..core.app_config import AppConfig
from ..core.serial_manager import SerialManager, SerialDevice


class MacOSSerialUI(QWidget):
    """macOS 风格串口调试助手主界面"""
    
    data_sent = pyqtSignal(bytes)
    
    def __init__(self, config: AppConfig, serial_mgr: SerialManager):
        super().__init__()
        self.config = config
        self.serial_manager = serial_mgr
        
        # 统计数据
        self.sent_count = 0
        self.sent_bytes = 0
        self.received_count = 0
        self.received_bytes = 0
        
        self.init_ui()
        self.apply_macos_style()
        self.connect_signals()
        self.refresh_ports()
    
    def init_ui(self):
        """初始化 UI"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 左侧边栏
        left_sidebar = self.create_left_sidebar()
        main_layout.addWidget(left_sidebar)
        
        # 中间和右侧区域（包含横线）
        right_area = QWidget()
        right_area_layout = QVBoxLayout(right_area)
        right_area_layout.setContentsMargins(0, 0, 0, 0)
        right_area_layout.setSpacing(0)
        
        # 标题栏下方的横线
        title_separator = QFrame()
        title_separator.setObjectName("titleBottomSeparator")
        title_separator.setFrameShape(QFrame.Shape.HLine)
        title_separator.setFixedHeight(1)
        right_area_layout.addWidget(title_separator)
        
        # 中间和右侧内容
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # 中央内容区
        center_content = self.create_center_content()
        content_layout.addWidget(center_content, 1)
        
        # 中右分界线
        center_right_separator = QFrame()
        center_right_separator.setObjectName("centerRightSeparator")
        center_right_separator.setFrameShape(QFrame.Shape.VLine)
        center_right_separator.setFixedWidth(1)
        content_layout.addWidget(center_right_separator)
        
        # 右侧边栏
        right_sidebar = self.create_right_sidebar()
        content_layout.addWidget(right_sidebar)
        
        right_area_layout.addLayout(content_layout)
        
        main_layout.addWidget(right_area, 1)

    def create_left_sidebar(self):
        """创建左侧边栏 - 串口连接设置"""
        sidebar = QFrame()
        sidebar.setObjectName("leftSidebar")
        sidebar.setFixedWidth(220)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(16)
        
        # Port
        layout.addWidget(QLabel("端口"))
        self.port_combo = QComboBox()
        layout.addWidget(self.port_combo)
        
        # Baud Rate
        layout.addWidget(QLabel("波特率"))
        self.baud_combo = QComboBox()
        self.baud_combo.setEditable(True)
        self.baud_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.baud_combo.setCurrentText("9600")
        layout.addWidget(self.baud_combo)
        
        # Data Bits
        layout.addWidget(QLabel("数据位"))
        self.data_bits_combo = QComboBox()
        self.data_bits_combo.addItems(["5", "6", "7", "8"])
        self.data_bits_combo.setCurrentText("8")
        layout.addWidget(self.data_bits_combo)
        
        # Stop Bits
        layout.addWidget(QLabel("停止位"))
        self.stop_bits_combo = QComboBox()
        self.stop_bits_combo.addItems(["1", "1.5", "2"])
        self.stop_bits_combo.setCurrentText("1")
        layout.addWidget(self.stop_bits_combo)
        
        # Parity
        layout.addWidget(QLabel("校验位"))
        self.parity_combo = QComboBox()
        self.parity_combo.addItems(["None", "Even", "Odd"])
        self.parity_combo.setCurrentText("None")
        layout.addWidget(self.parity_combo)
        
        layout.addStretch()
        
        # 连接按钮
        self.connect_btn = QPushButton("连接")
        self.connect_btn.setObjectName("primaryButton")
        self.connect_btn.setMinimumHeight(32)
        self.connect_btn.clicked.connect(self.toggle_connection)
        layout.addWidget(self.connect_btn)
        
        # 状态指示
        status_frame = QFrame()
        status_frame.setObjectName("statusFrame")
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(8, 6, 8, 6)
        
        self.status_indicator = QLabel("●")
        self.status_indicator.setObjectName("statusDot")
        status_layout.addWidget(self.status_indicator)
        
        self.status_label = QLabel("未连接")
        self.status_label.setObjectName("statusText")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        layout.addWidget(status_frame)
        
        return sidebar

    def create_center_content(self):
        """创建中央内容区"""
        content = QFrame()
        content.setObjectName("centerContent")
        
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # 顶部工具栏
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)
        
        # 格式选择
        toolbar.addWidget(QLabel("格式:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["HEX", "ASCII", "UTF-8"])
        self.format_combo.setCurrentText("HEX")
        self.format_combo.setMaximumWidth(100)
        toolbar.addWidget(self.format_combo)
        
        toolbar.addSpacing(16)
        
        # 时间戳
        self.timestamp_check = QCheckBox("显示时间戳")
        self.timestamp_check.setChecked(True)
        toolbar.addWidget(self.timestamp_check)
        
        # 自动滚动
        self.autoscroll_check = QCheckBox("自动滚动")
        self.autoscroll_check.setChecked(True)
        toolbar.addWidget(self.autoscroll_check)
        
        toolbar.addStretch()
        
        # 清除按钮
        self.clear_btn = QPushButton("清除")
        self.clear_btn.setObjectName("secondaryButton")
        self.clear_btn.clicked.connect(self.clear_display)
        toolbar.addWidget(self.clear_btn)
        
        layout.addLayout(toolbar)
        
        # 数据显示区 - 使用容器实现圆角
        display_container = QFrame()
        display_container.setObjectName("dataDisplayContainer")
        display_container_layout = QVBoxLayout(display_container)
        display_container_layout.setContentsMargins(0, 0, 0, 0)
        display_container_layout.setSpacing(0)
        
        self.data_display = QTextEdit()
        self.data_display.setObjectName("dataDisplay")
        self.data_display.setReadOnly(True)
        self.data_display.setFrameShape(QFrame.Shape.NoFrame)
        display_container_layout.addWidget(self.data_display)
        
        layout.addWidget(display_container)
        
        # 底部状态栏
        status_bar = QHBoxLayout()
        status_bar.setSpacing(20)
        
        self.sent_stats = QLabel("发送: 0 (0 字节)")
        self.sent_stats.setObjectName("statsLabel")
        status_bar.addWidget(self.sent_stats)
        
        self.received_stats = QLabel("接收: 0 (0 字节)")
        self.received_stats.setObjectName("statsLabel")
        status_bar.addWidget(self.received_stats)
        
        status_bar.addStretch()
        
        layout.addLayout(status_bar)
        
        return content

    def create_right_sidebar(self):
        """创建右侧边栏 - 发送控制"""
        sidebar = QFrame()
        sidebar.setObjectName("rightSidebar")
        sidebar.setFixedWidth(240)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(16)
        
        # 标题
        # title = QLabel("发送")
        # title.setObjectName("sidebarTitle")
        # layout.addWidget(title)
        
        # 发送格式
        # format_label = QLabel("格式")
        # format_label.setObjectName("fieldLabel")
        # layout.addWidget(format_label)
        
        self.send_format_combo = QComboBox()
        self.send_format_combo.addItems(["HEX", "ASCII", "UTF-8"])
        self.send_format_combo.setCurrentText("HEX")
        layout.addWidget(self.send_format_combo)
        
        # 输入区域
        # input_label = QLabel("数据")
        # input_label.setObjectName("fieldLabel")
        # layout.addWidget(input_label)
        
        # 创建输入框容器以实现圆角
        input_container = QFrame()
        input_container.setObjectName("sendInputContainer")
        input_container.setMaximumHeight(124)  # 120 + 4 (上下padding)
        input_container_layout = QVBoxLayout(input_container)
        input_container_layout.setContentsMargins(0, 0, 0, 0)
        input_container_layout.setSpacing(0)
        
        self.send_input = QTextEdit()
        self.send_input.setObjectName("sendInput")
        self.send_input.setPlaceholderText("发送数据...")
        self.send_input.setMaximumHeight(120)
        self.send_input.setFrameShape(QFrame.Shape.NoFrame)
        input_container_layout.addWidget(self.send_input)
        
        layout.addWidget(input_container)
        
        # 发送选项
        options_layout = QHBoxLayout()
        self.add_newline = QCheckBox("\\n")
        self.add_carriage = QCheckBox("\\r")
        options_layout.addWidget(self.add_newline)
        options_layout.addWidget(self.add_carriage)
        options_layout.addStretch()
        layout.addLayout(options_layout)
        
        # 发送按钮
        self.send_btn = QPushButton("发送")
        self.send_btn.setObjectName("primaryButton")
        self.send_btn.setMinimumHeight(32)
        self.send_btn.clicked.connect(self.send_data)
        layout.addWidget(self.send_btn)
        
        layout.addStretch()
        
        return sidebar

    def apply_macos_style(self):
        """应用 macOS 风格样式"""
        # 加载字体
        from PyQt6.QtGui import QFontDatabase
        font_id = QFontDatabase.addApplicationFont("src/resource/fzzyjt.ttf")
        if font_id != -1:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                font_family = font_families[0]
            else:
                font_family = "Microsoft YaHei"
        else:
            font_family = "Microsoft YaHei"
        
        self.setStyleSheet(f"""
            QWidget {{
                color: #1d1d1f;
                font-family: "{font_family}";
            }}
            
            QLabel, QPushButton, QComboBox, QCheckBox, QTextEdit {{
                font-family: "{font_family}";
            }}
            
            #leftSidebar, #rightSidebar {{
                background-color: #f5f5f7;
                border-right: 1px solid #d2d2d7;
            }}
            
            #leftSidebar {{
                border-bottom-left-radius: 10px;
            }}
            
            #rightSidebar {{
                border-bottom-right-radius: 10px;
            }}
            
            #titleBottomSeparator {{
                background-color: #d2d2d7;
                border: none;
            }}
            
            #centerRightSeparator {{
                background-color: #d2d2d7;
                border: none;
            }}
            
            #centerContent {{
                background-color: #EEEEF0;
            }}
            
            #sidebarTitle {{
                font-size: 15px;
                font-weight: 600;
                color: #1d1d1f;
            }}
            
            #fieldLabel {{
                font-size: 11px;
                font-weight: 500;
                color: #86868b;
                text-transform: uppercase;
            }}
            
            QComboBox {{
                background-color: #ffffff;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                padding: 6px 10px;
                padding-right: 30px;
                min-height: 20px;
            }}
            
            QComboBox:hover {{
                border-color: #0071e3;
            }}
            
            QComboBox::drop-down {{
                border: none;
                width: 30px;
                subcontrol-origin: padding;
                subcontrol-position: center right;
            }}
            
            QComboBox::down-arrow {{
                image: url(src/resource/triangle.png);
                width: 12px;
                height: 12px;
            }}
            
            #primaryButton {{
                background-color: #0071e3;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }}
            
            #primaryButton:hover {{
                background-color: #0077ed;
            }}
            
            #primaryButton:pressed {{
                background-color: #006edb;
            }}
            
            #primaryButton:disabled {{
                background-color: #d2d2d7;
                color: #86868b;
            }}
            
            #secondaryButton {{
                background-color: #f5f5f7;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                padding: 6px 12px;
            }}
            
            #secondaryButton:hover {{
                background-color: #e8e8ed;
            }}
            
            #statusFrame {{
                background-color: #ffffff;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
            }}
            
            #statusDot {{
                color: #86868b;
                font-size: 16px;
            }}
            
            #statusText {{
                color: #86868b;
                font-size: 12px;
            }}
            
            #dataDisplayContainer {{
                background-color: #e8e8e8;
                border: 1px solid #d2d2d7;
                border-radius: 12px;
                padding: 3px;
            }}
            
            #dataDisplay {{
                background-color: #e8e8e8;
                color: #ffffff;
                border: none;
                padding: 10px;
                line-height: 1.5;
            }}
            
            #sendInputContainer {{
                background-color: #ffffff;
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                padding: 2px;
            }}
            
            #sendInput {{
                background-color: #ffffff;
                border: none;
                padding: 6px;
            }}
            
            #sendInput:focus {{
                border: none;
            }}
            
            #historyList {{
                background-color: #ffffff;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                padding: 4px;
            }}
            
            #historyList::item {{
                padding: 6px;
                border-radius: 4px;
            }}
            
            #historyList::item:hover {{
                background-color: #f5f5f7;
            }}
            
            #historyList::item:selected {{
                background-color: #0071e3;
                color: white;
            }}
            
            QCheckBox {{
                spacing: 6px;
            }}
            
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid #d2d2d7;
                border-radius: 4px;
                background-color: #ffffff;
            }}
            
            QCheckBox::indicator:checked {{
                background-color: #0071e3;
                border-color: #0071e3;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
            }}
            
            #separator {{
                background-color: #d2d2d7;
                max-height: 1px;
            }}
            
            #statsLabel {{
                color: #86868b;
                font-size: 12px;
            }}
        """)
    
    def connect_signals(self):
        """连接信号"""
        self.serial_manager.data_received.connect(self.on_data_received)
        self.serial_manager.device_connected.connect(self.on_device_connected)
        self.serial_manager.device_disconnected.connect(self.on_device_disconnected)
        self.serial_manager.error_occurred.connect(self.on_error)
    
    def refresh_ports(self):
        """刷新串口列表"""
        self.port_combo.clear()
        devices = SerialManager.list_devices()
        for device in devices:
            self.port_combo.addItem(device.display_name, device.port)
    
    def toggle_connection(self):
        """切换连接状态"""
        if self.serial_manager.is_connected:
            self.serial_manager.disconnect()
        else:
            port = self.port_combo.currentData()
            if not port:
                self.on_error("请选择串口")
                return
            
            # 配置串口参数
            config = {
                'baud_rate': int(self.baud_combo.currentText()),
                'data_bits': int(self.data_bits_combo.currentText()),
                'stop_bits': float(self.stop_bits_combo.currentText()),
                'parity': self.parity_combo.currentText()
            }
            self.serial_manager.configure(config)
            self.serial_manager.connect(port)
    
    def send_data(self):
        """发送数据"""
        if not self.serial_manager.is_connected:
            self.on_error("设备未连接")
            return
        
        text = self.send_input.toPlainText().strip()
        if not text:
            return
        
        # 添加换行符
        if self.add_newline.isChecked():
            text += '\n'
        if self.add_carriage.isChecked():
            text += '\r'
        
        # 根据格式发送
        format_type = self.send_format_combo.currentText()
        success = False
        
        if format_type == "HEX":
            success = self.serial_manager.send_hex_string(text)
        elif format_type == "ASCII":
            success = self.serial_manager.send_text(text, 'ascii')
        else:  # UTF-8
            success = self.serial_manager.send_text(text, 'utf-8')
        
        if success:
            self.sent_count += 1
            self.sent_bytes += len(text.encode('utf-8'))
            self.update_stats()
    
    def clear_display(self):
        """清除显示"""
        self.data_display.clear()
        self.sent_count = 0
        self.sent_bytes = 0
        self.received_count = 0
        self.received_bytes = 0
        self.update_stats()
    
    def on_data_received(self, data: bytes):
        """接收到数据"""
        self.received_count += 1
        self.received_bytes += len(data)
        self.update_stats()
        
        # 格式化显示
        format_type = self.format_combo.currentText()
        
        if format_type == "HEX":
            text = ' '.join(f'{b:02X}' for b in data)
        elif format_type == "ASCII":
            text = data.decode('ascii', errors='replace')
        else:  # UTF-8
            text = data.decode('utf-8', errors='replace')
        
        # 添加时间戳
        if self.timestamp_check.isChecked():
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            text = f"[{timestamp}] {text}"
        
        # 显示数据
        self.data_display.append(text)
        
        # 自动滚动
        if self.autoscroll_check.isChecked():
            scrollbar = self.data_display.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
    
    def on_device_connected(self):
        """设备已连接"""
        self.connect_btn.setText("断开")
        self.status_indicator.setStyleSheet("color: #34c759;")  # 绿色
        self.status_label.setText("已连接")
        
        # 禁用配置控件
        self.port_combo.setEnabled(False)
        self.baud_combo.setEnabled(False)
        self.data_bits_combo.setEnabled(False)
        self.stop_bits_combo.setEnabled(False)
        self.parity_combo.setEnabled(False)
        
        # 启用发送控件
        self.send_btn.setEnabled(True)
    
    def on_device_disconnected(self):
        """设备已断开"""
        self.connect_btn.setText("连接")
        self.status_indicator.setStyleSheet("color: #86868b;")  # 灰色
        self.status_label.setText("未连接")
        
        # 启用配置控件
        self.port_combo.setEnabled(True)
        self.baud_combo.setEnabled(True)
        self.data_bits_combo.setEnabled(True)
        self.stop_bits_combo.setEnabled(True)
        self.parity_combo.setEnabled(True)
        
        # 禁用发送控件
        self.send_btn.setEnabled(False)
    
    def on_error(self, error_msg: str):
        """错误处理"""
        self.show_macos_alert("提示", error_msg)
    
    def update_stats(self):
        """更新统计信息"""
        self.sent_stats.setText(f"发送: {self.sent_count} ({self.sent_bytes} 字节)")
        self.received_stats.setText(f"接收: {self.received_count} ({self.received_bytes} 字节)")
    
    def show_macos_alert(self, title: str, message: str):
        """显示 macOS 风格的提示框"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QGraphicsDropShadowEffect
        from PyQt6.QtCore import Qt, QRect
        from PyQt6.QtGui import QRegion, QPainterPath
        
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        dialog.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        dialog.setModal(True)
        
        # 主容器
        main_container = QWidget()
        main_container.setObjectName("alertContainer")
        main_container.setAutoFillBackground(True)
        main_container.setStyleSheet("""
            #alertContainer {{
                background-color: #ffffff;
                border-radius: 16px;
                border: 1px solid #d2d2d7;
            }}
            QWidget {{
                background-color: #ffffff;
            }}
            #alertTitle {{
                font-size: 14px;
                font-weight: 600;
                color: #1d1d1f;
                background-color: transparent;
            }}
            #alertMessage {{
                font-size: 12px;
                color: #1d1d1f;
                background-color: transparent;
            }}
            #alertButton {{
                background-color: #0071e3;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 28px;
                font-weight: 500;
                min-width: 80px;
            }}
            #alertButton:hover {{
                background-color: #0077ed;
            }}
            #alertButton:pressed {{
                background-color: #006edb;
            }}
        """)
        
        container_layout = QVBoxLayout(main_container)
        container_layout.setContentsMargins(24, 20, 24, 20)
        container_layout.setSpacing(16)
        
        # 标题
        title_label = QLabel(title)
        title_label.setObjectName("alertTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(title_label)
        
        # 消息
        message_label = QLabel(message)
        message_label.setObjectName("alertMessage")
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setWordWrap(True)
        message_label.setMinimumWidth(250)
        container_layout.addWidget(message_label)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        ok_button = QPushButton("确定")
        ok_button.setObjectName("alertButton")
        ok_button.clicked.connect(dialog.accept)
        ok_button.setCursor(Qt.CursorShape.PointingHandCursor)
        button_layout.addWidget(ok_button)
        button_layout.addStretch()
        container_layout.addLayout(button_layout)
        
        # 设置对话框布局
        dialog_layout = QVBoxLayout(dialog)
        dialog_layout.setContentsMargins(10, 10, 10, 10)
        dialog_layout.addWidget(main_container)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 4)
        main_container.setGraphicsEffect(shadow)
        
        dialog.exec()
