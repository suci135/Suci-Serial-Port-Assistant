"""
macOS 原生风格串口调试工具 UI - 支持串口和蓝牙
严格遵循 macOS Human Interface Guidelines
"""

import json
import os
import sys
from typing import List
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from datetime import datetime

from ..core.app_config import AppConfig
from ..core.quick_command_store import QuickCommandStore
from ..core.resources import resource_path as get_resource_path
from ..core.serial_manager import SerialManager, SerialDevice
from ..core.bluetooth_manager import BluetoothManager, BluetoothDevice


def resource_path(relative_path: str) -> str:
    """获取资源文件的绝对路径，兼容 PyInstaller 打包环境"""
    return get_resource_path(relative_path)


class MessageContainer(QWidget):
    """带 hover 事件的消息容器"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._copy_btn = None
        self._copied_label = None

    def set_copy_widgets(self, copy_btn, copied_label):
        self._copy_btn = copy_btn
        self._copied_label = copied_label

    def enterEvent(self, event):
        if self._copy_btn and self._copied_label and not self._copied_label.isVisible():
            self._copy_btn.setVisible(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self._copy_btn:
            self._copy_btn.setVisible(False)
        super().leaveEvent(event)


class MacOSSerialUI(QWidget):
    """macOS 风格串口调试助手主界面"""

    data_sent = pyqtSignal(bytes)
    display_sent_signal = pyqtSignal(str, str)  # 新增信号：用于显示发送的数据
    
    def __init__(self, config: AppConfig, serial_mgr: SerialManager):
        super().__init__()
        self.config = config
        self.serial_manager = serial_mgr
        self.serial_manager.set_auto_reconnect(
            self.config.get("serial.auto_reconnect", True)
        )
        self.bluetooth_manager = BluetoothManager()
        
        # 当前模式：'serial' 或 'bluetooth'
        self.current_mode = 'serial'
        
        # 统计数据
        self.sent_count = 0
        self.sent_bytes = 0
        self.received_count = 0
        self.received_bytes = 0

        # 消息记录（用于导出）
        self.message_log = []  # [{"time": str, "direction": str, "content": str}]

        # 黑夜模式状态
        self.is_dark_mode = False
        
        # 配置文件路径
        self.config_file = "quick_commands.json"
        self.quick_command_store = QuickCommandStore(self.config_file)
        
        # 快捷输入数据 - 从配置文件加载
        self.quick_commands = self.load_quick_commands()
        
        # 连接动画定时器
        self.connecting_timer = QTimer()
        self.connecting_timer.timeout.connect(self.update_connecting_animation)
        self.connecting_dots = 0
        
        self.init_ui()
        self.apply_macos_style()
        self.connect_signals()
        self.refresh_devices()
    
    def init_ui(self):
        """初始化 UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 顶部横线容器 - 确保与下方分界线对齐
        top_line_container = QHBoxLayout()
        top_line_container.setContentsMargins(0, 0, 0, 0)
        top_line_container.setSpacing(0)
        
        # 左侧空白区域（对应左侧边栏宽度）
        left_spacer = QWidget()
        left_spacer.setFixedWidth(179)  # 与左侧边栏宽度保持一致
        left_spacer.setObjectName("leftSpacer")
        top_line_container.addWidget(left_spacer)
        
        # 顶部横线
        title_separator = QFrame()
        title_separator.setObjectName("titleBottomSeparator")
        title_separator.setFrameShape(QFrame.Shape.HLine)
        title_separator.setFixedHeight(1)
        top_line_container.addWidget(title_separator, 1)
        
        main_layout.addLayout(top_line_container)
        
        # 主要内容区域
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # 左侧边栏
        left_sidebar = self.create_left_sidebar()
        content_layout.addWidget(left_sidebar)
        
        # 左中分界线
        left_center_separator = QFrame()
        left_center_separator.setObjectName("leftCenterSeparator")
        left_center_separator.setFrameShape(QFrame.Shape.VLine)
        left_center_separator.setFixedWidth(1)
        content_layout.addWidget(left_center_separator)
        
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
        
        main_layout.addLayout(content_layout)

    def create_left_sidebar(self):
        """创建左侧边栏 - 串口/蓝牙连接设置"""
        sidebar = QFrame()
        sidebar.setObjectName("leftSidebar")
        sidebar.setFixedWidth(179)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(10, 20, 10, 20)
        layout.setSpacing(10)
        
        # 模式选择
        mode_label = QLabel("模式")
        mode_label.setObjectName("compactLabel")
        layout.addWidget(mode_label)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["串口", "蓝牙"])
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        layout.addWidget(self.mode_combo)
        
        # 设备选择
        device_label = QLabel("设备")
        device_label.setObjectName("compactLabel")
        layout.addWidget(device_label)
        
        # 设备选择容器（包含下拉框和刷新按钮）
        device_container = QHBoxLayout()
        device_container.setSpacing(5)
        
        self.port_combo = QComboBox()
        device_container.addWidget(self.port_combo, 1)
        
        # 刷新/扫描按钮
        self.refresh_btn = QPushButton("⟳")
        self.refresh_btn.setObjectName("refreshButton")
        self.refresh_btn.setFixedSize(32, 32)
        self.refresh_btn.setToolTip("刷新设备列表")
        self.refresh_btn.clicked.connect(self.refresh_devices)
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        device_container.addWidget(self.refresh_btn)
        
        layout.addLayout(device_container)
        
        # 串口配置区域（容器）
        self.serial_config_widget = QWidget()
        serial_config_layout = QVBoxLayout(self.serial_config_widget)
        serial_config_layout.setContentsMargins(0, 0, 0, 0)
        serial_config_layout.setSpacing(10)
        
        # Baud Rate
        baud_label = QLabel("波特率")
        baud_label.setObjectName("compactLabel")
        serial_config_layout.addWidget(baud_label)
        self.baud_combo = QComboBox()
        self.baud_combo.setEditable(True)
        self.baud_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.baud_combo.setCurrentText("9600")
        serial_config_layout.addWidget(self.baud_combo)
        
        # Data Bits
        data_label = QLabel("数据位")
        data_label.setObjectName("compactLabel")
        serial_config_layout.addWidget(data_label)
        self.data_bits_combo = QComboBox()
        self.data_bits_combo.addItems(["5", "6", "7", "8"])
        self.data_bits_combo.setCurrentText("8")
        serial_config_layout.addWidget(self.data_bits_combo)
        
        # Stop Bits
        stop_label = QLabel("停止位")
        stop_label.setObjectName("compactLabel")
        serial_config_layout.addWidget(stop_label)
        self.stop_bits_combo = QComboBox()
        self.stop_bits_combo.addItems(["1", "1.5", "2"])
        self.stop_bits_combo.setCurrentText("1")
        serial_config_layout.addWidget(self.stop_bits_combo)
        
        # Parity
        parity_label = QLabel("校验位")
        parity_label.setObjectName("compactLabel")
        serial_config_layout.addWidget(parity_label)
        self.parity_combo = QComboBox()
        self.parity_combo.addItems(["None", "Even", "Odd"])
        self.parity_combo.setCurrentText("None")
        serial_config_layout.addWidget(self.parity_combo)
        
        layout.addWidget(self.serial_config_widget)
        
        # 蓝牙配置区域（容器）
        self.bluetooth_config_widget = QWidget()
        bluetooth_config_layout = QVBoxLayout(self.bluetooth_config_widget)
        bluetooth_config_layout.setContentsMargins(0, 0, 0, 0)
        bluetooth_config_layout.setSpacing(10)
        
        # PyBluez 配置（经典蓝牙）
        self.pybluez_config_widget = QWidget()
        pybluez_config_layout = QVBoxLayout(self.pybluez_config_widget)
        pybluez_config_layout.setContentsMargins(0, 0, 0, 0)
        pybluez_config_layout.setSpacing(10)
        
        # RFCOMM端口
        port_label = QLabel("RFCOMM端口")
        port_label.setObjectName("compactLabel")
        pybluez_config_layout.addWidget(port_label)
        self.rfcomm_port_spin = QSpinBox()
        self.rfcomm_port_spin.setRange(1, 30)
        self.rfcomm_port_spin.setValue(1)
        pybluez_config_layout.addWidget(self.rfcomm_port_spin)
        
        bluetooth_config_layout.addWidget(self.pybluez_config_widget)
        
        # 蓝牙提示信息
        bt_info = QLabel()
        bt_info.setObjectName("infoLabel")
        bt_info.setWordWrap(True)
        self.bt_info_label = bt_info
        bluetooth_config_layout.addWidget(bt_info)
        
        layout.addWidget(self.bluetooth_config_widget)
        
        # 默认隐藏蓝牙配置
        self.bluetooth_config_widget.hide()
        
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
        self.format_combo.setCurrentText("UTF-8")
        self.format_combo.setMinimumWidth(120)
        self.format_combo.setMaximumWidth(150)
        toolbar.addWidget(self.format_combo)
        
        toolbar.addSpacing(16)
        
        # 时间戳
        self.timestamp_check = QCheckBox("显示时间戳")
        self.timestamp_check.setChecked(True)
        self.timestamp_check.stateChanged.connect(self.toggle_timestamps)
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

        # 导出按钮
        self.export_btn = QPushButton("导出 Excel")
        self.export_btn.setObjectName("secondaryButton")
        self.export_btn.clicked.connect(self.export_to_excel)
        toolbar.addWidget(self.export_btn)
        
        layout.addLayout(toolbar)
        
        # 数据显示区 - 使用 QScrollArea + QWidget 实现气泡效果
        display_container = QFrame()
        display_container.setObjectName("dataDisplayContainer")
        display_container_layout = QVBoxLayout(display_container)
        display_container_layout.setContentsMargins(0, 0, 0, 0)
        display_container_layout.setSpacing(0)
        
        # 创建滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("chatScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # 创建消息容器
        self.messages_widget = QWidget()
        self.messages_widget.setObjectName("messagesWidget")
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setContentsMargins(10, 10, 10, 10)
        self.messages_layout.setSpacing(8)
        self.messages_layout.addStretch()
        
        self.scroll_area.setWidget(self.messages_widget)
        display_container_layout.addWidget(self.scroll_area)
        
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
        """创建右侧边栏 - 发送控制和快捷输入面板"""
        sidebar = QFrame()
        sidebar.setObjectName("rightSidebar")
        sidebar.setFixedWidth(350)  # 从380减少到350，进一步缩窄右侧
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(12)  # 减少间距
        
        # 发送区域标题
        send_title = QLabel("发送控制")
        send_title.setObjectName("sectionTitle")
        layout.addWidget(send_title)
        
        # 发送格式
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("格式:"))
        self.send_format_combo = QComboBox()
        self.send_format_combo.addItems(["HEX", "ASCII", "UTF-8"])
        self.send_format_combo.setCurrentText("UTF-8")
        format_layout.addWidget(self.send_format_combo)
        format_layout.addStretch()
        layout.addLayout(format_layout)
        
        # 输入区域
        input_container = QFrame()
        input_container.setObjectName("sendInputContainer")
        input_container.setMaximumHeight(100)  # 减少高度
        input_container_layout = QVBoxLayout(input_container)
        input_container_layout.setContentsMargins(0, 0, 0, 0)
        input_container_layout.setSpacing(0)
        
        self.send_input = QTextEdit()
        self.send_input.setObjectName("sendInput")
        self.send_input.setPlaceholderText("发送数据...")
        self.send_input.setMaximumHeight(96)  # 减少高度
        self.send_input.setFrameShape(QFrame.Shape.NoFrame)
        input_container_layout.addWidget(self.send_input)
        
        layout.addWidget(input_container)
        
        # 发送选项和按钮在同一行
        send_controls_layout = QHBoxLayout()
        
        # 发送选项
        self.add_newline = QCheckBox("\\n")
        self.add_carriage = QCheckBox("\\r")
        send_controls_layout.addWidget(self.add_newline)
        send_controls_layout.addWidget(self.add_carriage)
        send_controls_layout.addStretch()
        
        # 发送按钮
        self.send_btn = QPushButton("发送")
        self.send_btn.setObjectName("primaryButton")
        self.send_btn.setMinimumHeight(28)
        self.send_btn.clicked.connect(self.send_data)
        send_controls_layout.addWidget(self.send_btn)
        
        layout.addLayout(send_controls_layout)
        
        # 分隔线
        separator = QFrame()
        separator.setObjectName("sectionSeparator")
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFixedHeight(1)
        layout.addWidget(separator)
        
        # 快捷输入面板标题
        quick_title = QLabel("快捷输入")
        quick_title.setObjectName("sectionTitle")
        layout.addWidget(quick_title)
        
        # 快捷输入面板
        self.create_quick_input_panel(layout)
        
        # 底部按钮区域
        bottom_buttons = QHBoxLayout()
        bottom_buttons.setSpacing(8)
        bottom_buttons.addStretch()
        
        # GitHub 按钮
        self.github_btn = QPushButton()
        self.github_btn.setObjectName("githubButton")
        self.github_btn.setFixedSize(32, 32)
        self.github_btn.setToolTip("访问 GitHub 仓库")
        self.github_btn.clicked.connect(self.open_github)
        self.github_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 设置 GitHub 图标
        from PyQt6.QtGui import QIcon
        self.github_btn.setIcon(QIcon(resource_path("src/resource/GitHub.png")))
        self.github_btn.setIconSize(QSize(20, 20))
        
        # 黑夜模式按钮
        self.dark_mode_btn = QPushButton()
        self.dark_mode_btn.setObjectName("darkModeButton")
        self.dark_mode_btn.setFixedSize(32, 32)
        self.dark_mode_btn.setToolTip("切换黑夜模式")
        self.dark_mode_btn.clicked.connect(self.toggle_dark_mode)
        self.dark_mode_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 设置黑夜模式图标
        self.dark_mode_btn.setIcon(QIcon(resource_path("src/resource/dark.png")))
        self.dark_mode_btn.setIconSize(QSize(20, 20))
        
        bottom_buttons.addWidget(self.github_btn)
        bottom_buttons.addWidget(self.dark_mode_btn)
        layout.addLayout(bottom_buttons)
        
        return sidebar
    
    def create_quick_input_panel(self, parent_layout):
        """创建快捷输入面板"""
        # 面板标题和表头
        header_frame = QFrame()
        header_frame.setObjectName("quickInputHeader")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(8, 6, 8, 6)
        header_layout.setSpacing(8)
        
        # 表头标签
        content_label = QLabel("内容")
        content_label.setObjectName("headerLabel")
        header_layout.addWidget(content_label, 1)
        
        action_label = QLabel("操作")
        action_label.setObjectName("headerLabel")
        action_label.setFixedWidth(90)  # 从110减少到90，与操作按钮宽度一致
        action_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(action_label)
        
        parent_layout.addWidget(header_frame)
        
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setObjectName("quickInputScrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setMaximumHeight(250)  # 增加高度
        
        # 命令列表容器
        commands_widget = QWidget()
        commands_widget.setObjectName("quickInputCommands")
        self.commands_layout = QVBoxLayout(commands_widget)
        self.commands_layout.setContentsMargins(0, 0, 0, 0)
        self.commands_layout.setSpacing(2)
        
        # 创建命令行
        self.command_rows = []
        for i, cmd in enumerate(self.quick_commands):
            self.create_command_row(cmd, i)
        
        self.commands_layout.addStretch()
        scroll_area.setWidget(commands_widget)
        parent_layout.addWidget(scroll_area)
        
        # 添加新命令按钮
        add_btn = QPushButton("+ 添加命令")
        add_btn.setObjectName("addCommandButton")
        add_btn.clicked.connect(self.add_new_command)
        parent_layout.addWidget(add_btn)
    
    def create_command_row(self, cmd_data, index):
        """创建命令行"""
        row_frame = QFrame()
        row_frame.setObjectName("commandRow")
        row_layout = QHBoxLayout(row_frame)
        row_layout.setContentsMargins(4, 4, 4, 4)
        row_layout.setSpacing(4)
        
        # 命令内容（可编辑）- 现在占据更多空间
        content_container = QFrame()
        content_container.setObjectName("commandContentContainer")
        content_container_layout = QVBoxLayout(content_container)
        content_container_layout.setContentsMargins(10, 4, 10, 4)
        content_container_layout.setSpacing(2)
        
        command_edit = QLineEdit(cmd_data["command"])
        command_edit.setObjectName("commandEdit")
        command_edit.setPlaceholderText("输入命令...")
        command_edit.textChanged.connect(lambda text, idx=index: self.on_command_changed(idx, text))
        content_container_layout.addWidget(command_edit)
        
        # 描述现在也可以编辑
        desc_edit = QLineEdit(cmd_data["description"])
        desc_edit.setObjectName("commandDescriptionEdit")
        desc_edit.setPlaceholderText("输入描述...")
        desc_edit.textChanged.connect(lambda text, idx=index: self.on_description_changed(idx, text))
        content_container_layout.addWidget(desc_edit)
        
        row_layout.addWidget(content_container, 1)
        
        # 操作按钮
        action_layout = QHBoxLayout()
        action_layout.setSpacing(5)
        
        send_btn = QPushButton("发送")
        send_btn.setObjectName("quickSendButton")
        send_btn.clicked.connect(lambda checked, idx=index: self.send_quick_command(idx))
        action_layout.addWidget(send_btn)
        
        delete_btn = QPushButton("删除")
        delete_btn.setObjectName("deleteButton")
        delete_btn.clicked.connect(lambda checked, idx=index: self.delete_command(idx))
        action_layout.addWidget(delete_btn)
        
        action_widget = QWidget()
        action_widget.setLayout(action_layout)
        action_widget.setFixedWidth(90)  # 从110减少到90，给内容框更多空间
        row_layout.addWidget(action_widget)
        
        # 保存行数据
        row_data = {
            'frame': row_frame,
            'command_edit': command_edit,
            'desc_edit': desc_edit,  # 改为可编辑的输入框
            'send_btn': send_btn,
            'delete_btn': delete_btn
        }
        self.command_rows.append(row_data)
        self.commands_layout.addWidget(row_frame)
    
    def on_command_changed(self, index, text):
        """命令内容改变"""
        if index < len(self.quick_commands):
            self.quick_commands[index]["command"] = text
            self.save_quick_commands()  # 自动保存
    
    def on_description_changed(self, index, text):
        """描述内容改变"""
        if index < len(self.quick_commands):
            self.quick_commands[index]["description"] = text
            self.save_quick_commands()  # 自动保存
    
    def on_hex_changed(self, index, state):
        """HEX状态改变"""
        if index < len(self.quick_commands):
            self.quick_commands[index]["is_hex"] = state == Qt.CheckState.Checked.value
    
    def on_delay_changed(self, index, text):
        """延时改变"""
        if index < len(self.quick_commands):
            try:
                delay = int(text) if text else 1000
                self.quick_commands[index]["delay"] = delay
            except ValueError:
                pass
    
    def send_quick_command(self, index):
        """发送快捷命令"""
        # 获取当前管理器
        manager = self.serial_manager if self.current_mode == 'serial' else self.bluetooth_manager
        
        if not manager.is_connected:
            self.on_error("设备未连接")
            return
        
        if index >= len(self.quick_commands):
            return
        
        cmd_data = self.quick_commands[index]
        command = cmd_data["command"].strip()
        if not command:
            return
        
        # 使用发送控制面板选择的格式
        format_type = self.send_format_combo.currentText()
        
        # 先在UI显示发送的数据
        self.display_sent_data(command, format_type)
        
        # 在后台线程中发送，避免阻塞 UI
        import threading
        def send_thread():
            success = False
            
            if format_type == "HEX":
                success = manager.send_hex_string(command)
            elif format_type == "ASCII":
                success = manager.send_text(command, 'ascii')
            else:  # UTF-8
                success = manager.send_text(command, 'utf-8')
            
            if success:
                # 更新统计
                self.sent_count += 1
                self.sent_bytes += len(command.encode('utf-8'))
        
        thread = threading.Thread(target=send_thread, daemon=True)
        thread.start()
        
        # 立即更新统计
        self.update_stats()
    
    def add_new_command(self):
        """添加新命令"""
        new_cmd = {
            "name": f"自定义命令{len(self.quick_commands) + 1}",
            "command": "",
            "description": "自定义命令",
            "enabled": True,
            "delay": 1000,
            "is_hex": False
        }
        self.quick_commands.append(new_cmd)
        self.create_command_row(new_cmd, len(self.quick_commands) - 1)
        self.save_quick_commands()  # 保存配置
    
    def delete_command(self, index):
        """删除命令"""
        if index < len(self.quick_commands) and index < len(self.command_rows):
            # 移除UI
            row_data = self.command_rows[index]
            self.commands_layout.removeWidget(row_data['frame'])
            row_data['frame'].deleteLater()
            
            # 移除数据
            self.quick_commands.pop(index)
            self.command_rows.pop(index)
            
            # 重新索引剩余的命令
            self.refresh_command_indices()
            self.save_quick_commands()  # 保存配置
    
    def refresh_command_indices(self):
        """刷新命令索引"""
        # 重新创建所有命令行以更新索引
        for row_data in self.command_rows:
            self.commands_layout.removeWidget(row_data['frame'])
            row_data['frame'].deleteLater()
        
        self.command_rows.clear()
        for i, cmd in enumerate(self.quick_commands):
            self.create_command_row(cmd, i)

    def apply_macos_style(self):
        """应用 macOS 风格样式"""
        # 加载字体
        from PyQt6.QtGui import QFontDatabase
        font_id = QFontDatabase.addApplicationFont(resource_path("src/resource/AlimamaFangYuanTiVF-Thin-2.ttf"))
        if font_id != -1:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                font_family = font_families[0]
            else:
                font_family = "Microsoft YaHei"
        else:
            font_family = "Microsoft YaHei"
        
        # 根据模式选择颜色
        if self.is_dark_mode:
            # 黑夜模式颜色
            bg_color = "#1e1e1e"
            sidebar_bg = "#2d2d2d"
            text_color = "#ffffff"
            border_color = "#404040"
            display_bg = "#2a2a2a"  # 修复黑夜模式下数据显示背景
            display_text = "#ffffff"
            button_bg = "#404040"
        else:
            # 日间模式颜色
            bg_color = "#ffffff"
            sidebar_bg = "#f5f5f7"
            text_color = "#1d1d1f"
            border_color = "#d2d2d7"
            display_bg = "#f8f8f8"  # 日间模式数据显示背景
            display_text = "#1d1d1f"  # 日间模式文字颜色
            button_bg = "#f5f5f7"
        
        self.setStyleSheet(f"""
            QWidget {{
                color: {text_color};
                font-family: "{font_family}";
                font-weight: bold;
            }}
            
            QLabel, QPushButton, QComboBox, QCheckBox, QTextEdit {{
                font-family: "{font_family}";
                font-weight: bold;
            }}
            
            #leftSidebar {{
                background-color: {sidebar_bg};
                border-bottom-left-radius: 10px;
            }}
            
            #leftSpacer {{
                background-color: {sidebar_bg};
            }}
            
            #rightSidebar {{
                background-color: {sidebar_bg};
                border-bottom-right-radius: 10px;
            }}
            
            #titleBottomSeparator, #leftCenterSeparator, #centerRightSeparator {{
                background-color: {border_color};
                border: none;
            }}
            
            #centerContent {{
                background-color: {bg_color};
            }}
            
            #sidebarTitle {{
                font-size: 15px;
                font-weight: 600;
                color: {text_color};
            }}
            
            #fieldLabel {{
                font-size: 11px;
                font-weight: 500;
                color: {"#aaaaaa" if self.is_dark_mode else "#86868b"};
                text-transform: uppercase;
            }}
            
            QComboBox {{
                background-color: {bg_color};
                color: {text_color};
                border: 1px solid {border_color};
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
                image: url("{resource_path("src/resource/triangle.png").replace(os.sep, "/")}");
                width: 12px;
                height: 12px;
            }}
            
            QComboBox QAbstractItemView {{
                background-color: {bg_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 6px;
                selection-background-color: #0071e3;
                selection-color: white;
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
                background-color: {border_color};
                color: #86868b;
            }}
            
            #secondaryButton {{
                background-color: {button_bg};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 6px;
                padding: 6px 12px;
            }}
            
            #secondaryButton:hover {{
                background-color: {"#505050" if self.is_dark_mode else "#e8e8ed"};
            }}
            
            #statusFrame {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 6px;
            }}
            
            #statusDot {{
                color: {"#aaaaaa" if self.is_dark_mode else "#86868b"};
                font-size: 16px;
            }}
            
            #statusText {{
                color: {"#aaaaaa" if self.is_dark_mode else "#86868b"};
                font-size: 12px;
            }}
            
            #dataDisplayContainer {{
                background-color: {display_bg};
                border: 1px solid {border_color};
                border-radius: 12px;
                padding: 3px;
            }}
            
            #chatScrollArea {{
                background-color: {display_bg};
                border: none;
            }}
            
            #messagesWidget {{
                background-color: {display_bg};
            }}
            
            #chatScrollArea QScrollBar:vertical {{
                background-color: {sidebar_bg};
                width: 8px;
                border-radius: 4px;
            }}
            
            #chatScrollArea QScrollBar::handle:vertical {{
                background-color: {border_color};
                border-radius: 4px;
                min-height: 20px;
            }}
            
            #chatScrollArea QScrollBar::handle:vertical:hover {{
                background-color: #86868b;
            }}
            
            #dataDisplay {{
                background-color: {display_bg};
                color: {display_text};
                border: none;
                padding: 10px;
                line-height: 1.5;
            }}
            
            #sendInputContainer {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 8px;
                padding: 2px;
            }}
            
            #sendInput {{
                background-color: {bg_color};
                color: {text_color};
                border: none;
                padding: 6px;
            }}
            
            #sendInput:focus {{
                border: none;
            }}
            
            #historyList {{
                background-color: {bg_color};
                border: 1px solid {border_color};
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
                border: 1px solid {border_color};
                border-radius: 4px;
                background-color: {bg_color};
            }}
            
            QCheckBox::indicator:checked {{
                background-color: #0071e3;
                border-color: #0071e3;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
            }}
            
            #separator {{
                background-color: {border_color};
                max-height: 1px;
            }}
            
            #statsLabel {{
                color: #86868b;
                font-size: 12px;
            }}
            
            #darkModeButton, #githubButton {{
                background-color: {button_bg};
                border: 1px solid {border_color};
                border-radius: 16px;
                padding: 6px;
            }}
            
            #darkModeButton:hover, #githubButton:hover {{
                background-color: {border_color};
            }}
            
            #darkModeButton:pressed, #githubButton:pressed {{
                background-color: {border_color};
            }}
            
            /* 快捷输入面板样式 */
            #quickInputHeader {{
                background-color: {sidebar_bg};
                border: 1px solid {border_color};
                border-radius: 6px;
                margin-bottom: 4px;
            }}
            
            #headerLabel {{
                color: #86868b;
                font-size: 10px;
                font-weight: 600;
                text-transform: uppercase;
            }}
            
            #quickInputScrollArea {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 8px;
            }}
            
            #quickInputCommands {{
                background-color: {bg_color};
            }}
            
            #quickInputScrollArea QScrollBar:vertical {{
                background-color: {sidebar_bg};
                width: 8px;
                border-radius: 4px;
            }}
            
            #quickInputScrollArea QScrollBar::handle:vertical {{
                background-color: {border_color};
                border-radius: 4px;
                min-height: 20px;
            }}
            
            #quickInputScrollArea QScrollBar::handle:vertical:hover {{
                background-color: #86868b;
            }}
            
            #commandRow {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 6px;
                margin: 1px;
            }}
            
            #commandRow:hover {{
                background-color: {"#2a2a2a" if self.is_dark_mode else "#f8f8f8"};
            }}
            
            #commandContentContainer {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 4px;
            }}
            
            #commandEdit {{
                background-color: {bg_color};
                color: {text_color};
                border: none;
                padding: 2px 4px;
                font-size: 11px;
            }}
            
            #commandDescriptionEdit {{
                background-color: {bg_color};
                color: #86868b;
                border: none;
                padding: 2px 4px;
                font-size: 9px;
                font-weight: normal;
            }}
            
            #commandDescriptionEdit:focus {{
                color: {text_color};
            }}
            
            #quickSendButton {{
                background-color: #0071e3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;  # 减少左右padding
                font-size: 10px;
                font-weight: 500;
                min-width: 35px;  # 减少最小宽度
            }}
            
            #quickSendButton:hover {{
                background-color: #0077ed;
            }}
            
            #quickSendButton:pressed {{
                background-color: #006edb;
            }}
            
            #quickSendButton:disabled {{
                background-color: {border_color};
                color: #86868b;
            }}
            
            #deleteButton {{
                background-color: #ff3b30;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;  # 减少左右padding
                font-size: 10px;
                font-weight: 500;
                min-width: 35px;  # 减少最小宽度
            }}
            
            #deleteButton:hover {{
                background-color: #ff453a;
            }}
            
            #deleteButton:pressed {{
                background-color: #d70015;
            }}
            
            #addCommandButton {{
                background-color: {button_bg};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: 500;
            }}
            
            #addCommandButton:hover {{
                background-color: {"#404040" if self.is_dark_mode else "#e8e8ed"};
            }}
            
            #addCommandButton:pressed {{
                background-color: {"#505050" if self.is_dark_mode else "#d8d8dd"};
            }}
            
            /* 分区样式 */
            #sectionTitle {{
                color: {text_color};
                font-size: 13px;
                font-weight: 600;
                margin: 4px 0px;
            }}
            
            #sectionSeparator {{
                background-color: {border_color};
                border: none;
                margin: 8px 0px;
            }}
            
            /* 紧凑标签样式 */
            #compactLabel {{
                color: {text_color};
                font-size: 11px;
                font-weight: 500;
                margin: 2px 0px;
            }}
            
            /* 信息标签样式 */
            #infoLabel {{
                color: #86868b;
                font-size: 9px;
                font-weight: normal;
                margin: 2px 0px;
            }}
            
            /* 刷新按钮样式 */
            #refreshButton {{
                background-color: {button_bg};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
            }}
            
            #refreshButton:hover {{
                background-color: {"#404040" if self.is_dark_mode else "#e8e8ed"};
            }}
            
            #refreshButton:pressed {{
                background-color: {"#505050" if self.is_dark_mode else "#d8d8dd"};
            }}
            
            /* SpinBox 样式 */
            QSpinBox {{
                background-color: {bg_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 6px;
                padding: 6px 10px;
                min-height: 20px;
            }}
            
            QSpinBox:hover {{
                border-color: #0071e3;
            }}
            
            QSpinBox::up-button, QSpinBox::down-button {{
                background-color: {button_bg};
                border: none;
                width: 16px;
                border-radius: 3px;
            }}
            
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                background-color: {border_color};
            }}
            
            QSpinBox::up-arrow {{
                image: url("{resource_path("src/resource/triangle.png").replace(os.sep, "/")}");
                width: 8px;
                height: 8px;
            }}
            
            QSpinBox::down-arrow {{
                image: url("{resource_path("src/resource/triangle.png").replace(os.sep, "/")}");
                width: 8px;
                height: 8px;
            }}
        """)
    
    def on_mode_changed(self, mode_text: str):
        """模式切换"""
        # 如果已连接，先断开
        if self.is_any_connected():
            self.toggle_connection()
        
        if mode_text == "串口":
            self.current_mode = 'serial'
            self.serial_config_widget.show()
            self.bluetooth_config_widget.hide()
            self.refresh_btn.setToolTip("刷新串口列表")
        else:  # 蓝牙
            self.current_mode = 'bluetooth'
            self.serial_config_widget.hide()
            self.bluetooth_config_widget.show()
            self.refresh_btn.setToolTip("扫描蓝牙设备")
            
            # 检查蓝牙是否可用
            if not BluetoothManager.is_available():
                self.show_macos_alert(
                    "蓝牙不可用",
                    "蓝牙功能需要安装蓝牙库\n\n请运行: pip install bleak"
                )
            else:
                # 根据蓝牙后端显示不同的提示
                backend = BluetoothManager.get_backend()
                if backend == 'bleak':
                    self.bt_info_label.setText("BLE 模式\n自动检测设备特征")
                    self.pybluez_config_widget.hide()
                elif backend == 'pybluez':
                    self.bt_info_label.setText("经典蓝牙模式\n需要先配对设备")
                    self.pybluez_config_widget.show()
        
        self.refresh_devices()
    
    def is_any_connected(self) -> bool:
        """检查是否有任何连接"""
        if self.current_mode == 'serial':
            return self.serial_manager.is_connected
        else:
            return self.bluetooth_manager.is_connected
    
    def refresh_devices(self):
        """刷新设备列表"""
        if self.current_mode == 'serial':
            self.refresh_ports()
        else:
            self.scan_bluetooth_devices()
    
    def scan_bluetooth_devices(self):
        """扫描蓝牙设备"""
        if not BluetoothManager.is_available():
            return
        
        # 禁用刷新按钮，显示扫描中
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("...")
        self.port_combo.clear()
        self.port_combo.addItem("正在扫描...")
        
        # 在后台线程中扫描
        def scan_thread():
            devices = self.bluetooth_manager.scan_devices(duration=8)
            # 使用信号更新UI
            self.bluetooth_manager.scan_completed.emit(devices)
        
        import threading
        thread = threading.Thread(target=scan_thread, daemon=True)
        thread.start()
    
    def on_bluetooth_scan_completed(self, devices: List[BluetoothDevice]):
        """蓝牙扫描完成"""
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("⟳")
        self.port_combo.clear()
        
        if not devices:
            self.port_combo.addItem("未发现设备")
        else:
            for device in devices:
                self.port_combo.addItem(device.display_name, device.address)
    
    def connect_signals(self):
        """连接信号"""
        # 串口信号
        self.serial_manager.data_received.connect(self.on_data_received)
        self.serial_manager.device_connected.connect(self.on_device_connected)
        self.serial_manager.device_disconnected.connect(self.on_device_disconnected)
        self.serial_manager.error_occurred.connect(self.on_error)
        self.serial_manager.connecting_status.connect(self.on_connecting_status)
        
        # 蓝牙信号
        self.bluetooth_manager.data_received.connect(self.on_data_received)
        self.bluetooth_manager.device_connected.connect(self.on_device_connected)
        self.bluetooth_manager.device_disconnected.connect(self.on_device_disconnected)
        self.bluetooth_manager.error_occurred.connect(self.on_error)
        self.bluetooth_manager.scan_completed.connect(self.on_bluetooth_scan_completed)
        self.bluetooth_manager.connecting_status.connect(self.on_connecting_status)
        
        # 内部信号
        self.display_sent_signal.connect(self.display_sent_data)
        
        # 串口配置变更信号 - 支持动态修改
        self.baud_combo.currentTextChanged.connect(self.on_serial_config_changed)
        self.data_bits_combo.currentTextChanged.connect(self.on_serial_config_changed)
        self.stop_bits_combo.currentTextChanged.connect(self.on_serial_config_changed)
        self.parity_combo.currentTextChanged.connect(self.on_serial_config_changed)
    
    def refresh_ports(self):
        """刷新串口列表"""
        self.port_combo.clear()
        devices = SerialManager.list_devices()
        for device in devices:
            self.port_combo.addItem(device.display_name, device.port)
    
    def on_serial_config_changed(self):
        """串口配置变更 - 实时应用到已连接的串口"""
        if self.current_mode == 'serial' and self.serial_manager.is_connected:
            try:
                # 获取当前配置
                config = {
                    'baud_rate': int(self.baud_combo.currentText()),
                    'data_bits': int(self.data_bits_combo.currentText()),
                    'stop_bits': float(self.stop_bits_combo.currentText()),
                    'parity': self.parity_combo.currentText()
                }
                # 应用配置
                self.serial_manager.configure(config)
            except ValueError:
                # 忽略无效的输入值
                pass
    
    def toggle_connection(self):
        """切换连接状态"""
        if self.current_mode == 'serial':
            # 串口模式
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
                
                # 在后台线程中连接，避免阻塞 UI
                import threading
                def connect_thread():
                    self.serial_manager.connect(port)
                
                thread = threading.Thread(target=connect_thread, daemon=True)
                thread.start()
        else:
            # 蓝牙模式
            if self.bluetooth_manager.is_connected:
                self.bluetooth_manager.disconnect()
            else:
                address = self.port_combo.currentData()
                if not address:
                    self.on_error("请选择蓝牙设备")
                    return
                
                port = self.rfcomm_port_spin.value()
                
                # 在后台线程中连接，避免阻塞 UI
                import threading
                def connect_thread():
                    self.bluetooth_manager.connect(address, port)
                
                thread = threading.Thread(target=connect_thread, daemon=True)
                thread.start()
    
    def send_data(self):
        """发送数据"""
        # 获取当前管理器
        manager = self.serial_manager if self.current_mode == 'serial' else self.bluetooth_manager
        
        if not manager.is_connected:
            self.on_error("设备未连接")
            return
        
        text = self.send_input.toPlainText().strip()
        if not text:
            return
        
        # 保存原始文本用于显示
        display_text = text
        format_type = self.send_format_combo.currentText()
        
        # 先在UI显示发送的数据
        self.display_sent_data(display_text, format_type)
        
        # 清空输入框
        self.send_input.clear()
        
        # 添加换行符
        if self.add_newline.isChecked():
            text += '\n'
        if self.add_carriage.isChecked():
            text += '\r'
        
        # 在后台线程中发送，避免阻塞 UI
        import threading
        def send_thread():
            success = False
            
            if format_type == "HEX":
                success = manager.send_hex_string(text)
            elif format_type == "ASCII":
                success = manager.send_text(text, 'ascii')
            else:  # UTF-8
                success = manager.send_text(text, 'utf-8')
            
            if success:
                # 更新统计
                self.sent_count += 1
                self.sent_bytes += len(text.encode('utf-8'))
        
        thread = threading.Thread(target=send_thread, daemon=True)
        thread.start()
        
        # 立即更新统计
        self.update_stats()
    
    def display_sent_data(self, text: str, format_type: str):
        """在数据显示区显示发送的数据 - QQ聊天样式（右对齐，蓝色气泡）"""
        # 格式化显示
        if format_type == "HEX":
            try:
                hex_string = ''.join(c for c in text if c in '0123456789ABCDEFabcdef')
                if len(hex_string) % 2 != 0:
                    hex_string = '0' + hex_string
                data = bytes.fromhex(hex_string)
                display = ' '.join(f'{b:02X}' for b in data)
            except:
                display = text
        else:
            display = text
        
        try:
            # 获取时间戳
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # 创建气泡消息
            self.add_message_bubble(display, timestamp, is_sent=True)
        except Exception as e:
            import traceback
            traceback.print_exc()
    
    def toggle_timestamps(self):
        """切换时间戳显示"""
        show_timestamps = self.timestamp_check.isChecked()
        
        # 遍历所有消息容器，更新时间戳显示
        for i in range(self.messages_layout.count()):
            item = self.messages_layout.itemAt(i)
            if item and item.widget():
                message_container = item.widget()
                # 查找时间戳标签
                for child in message_container.findChildren(QLabel):
                    if child.objectName() == "timestampLabel":
                        child.setVisible(show_timestamps)
    
    def add_message_bubble(self, text: str, timestamp: str, is_sent: bool = True):
        """添加消息气泡"""
        # 记录消息用于导出
        self.message_log.append({
            "time": timestamp,
            "direction": "发送" if is_sent else "接收",
            "content": text,
        })

        # 创建消息容器（包含时间戳和气泡）
        message_container = MessageContainer()
        container_layout = QVBoxLayout(message_container)
        container_layout.setContentsMargins(0, 4, 0, 4)
        container_layout.setSpacing(2)
        
        # 时间戳（在气泡上方）
        time_label = QLabel(timestamp)
        time_label.setObjectName("timestampLabel")
        time_label.setAlignment(Qt.AlignmentFlag.AlignRight if is_sent else Qt.AlignmentFlag.AlignLeft)
        
        if self.timestamp_check.isChecked():
            # 显示时间戳
            time_label.setStyleSheet("""
                color: #86868b;
                font-size: 11px;
                background: transparent;
                padding: 2px 8px;
            """)
            time_label.setVisible(True)
        else:
            # 隐藏时间戳
            time_label.setVisible(False)
        
        container_layout.addWidget(time_label)
        
        # 气泡容器（用于左右对齐）
        bubble_container = QWidget()
        bubble_layout = QHBoxLayout(bubble_container)
        bubble_layout.setContentsMargins(0, 0, 0, 0)
        bubble_layout.setSpacing(0)
        
        # 创建气泡
        bubble = QFrame()
        bubble.setObjectName("sentBubble" if is_sent else "receivedBubble")
        bubble_content_layout = QVBoxLayout(bubble)
        bubble_content_layout.setContentsMargins(14, 10, 14, 10)
        bubble_content_layout.setSpacing(0)
        
        # 消息内容
        content_label = QLabel(text)
        content_label.setObjectName("bubbleContent")
        content_label.setWordWrap(True)
        content_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        bubble_content_layout.addWidget(content_label)
        
        # 设置气泡样式和对齐
        if is_sent:
            # 发送消息：右对齐，蓝色
            bubble_layout.addStretch()
            bubble_layout.addWidget(bubble)
            bubble.setStyleSheet("""
                #sentBubble {
                    background-color: #0071e3;
                    border-radius: 18px;
                    max-width: 400px;
                    min-width: 60px;
                }
                #bubbleContent {
                    color: #ffffff;
                    font-size: 14px;
                    background: transparent;
                }
            """)
        else:
            # 接收消息：左对齐，灰色
            bubble_layout.addWidget(bubble)
            bubble_layout.addStretch()
            bubble_color = "#e5e5ea" if not self.is_dark_mode else "#3a3a3c"
            text_color = "#000000" if not self.is_dark_mode else "#ffffff"
            bubble.setStyleSheet(f"""
                #receivedBubble {{
                    background-color: {bubble_color};
                    border-radius: 18px;
                    max-width: 400px;
                    min-width: 60px;
                }}
                #bubbleContent {{
                    color: {text_color};
                    font-size: 14px;
                    background: transparent;
                }}
            """)
        
        container_layout.addWidget(bubble_container)

        # 复制图标行：固定高度避免悬停时布局抖动
        copy_row = QWidget()
        copy_row.setFixedHeight(20)
        copy_row_layout = QHBoxLayout(copy_row)
        copy_row_layout.setContentsMargins(4, 0, 4, 0)
        copy_row_layout.setSpacing(0)

        copy_btn = QPushButton(copy_row)
        copy_btn.setFixedSize(16, 16)
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        icon_path = resource_path("src/resource/copy.png")
        copy_btn.setIcon(QIcon(icon_path))
        copy_btn.setIconSize(QSize(13, 13))
        copy_btn.setStyleSheet("QPushButton { background: transparent; border: none; }")
        copy_btn.setVisible(False)

        copied_label = QLabel("已复制", copy_row)
        copied_label.setStyleSheet("color: #34c759; font-size: 11px; background: transparent;")
        copied_label.setVisible(False)

        # 把 text 存到按钮属性上，避免闭包问题
        copy_btn.setProperty("msg_text", text)
        copy_btn.clicked.connect(self._on_copy_clicked)

        if is_sent:
            copy_row_layout.addStretch()
            copy_row_layout.addWidget(copied_label)
            copy_row_layout.addWidget(copy_btn)
        else:
            copy_row_layout.addWidget(copy_btn)
            copy_row_layout.addWidget(copied_label)
            copy_row_layout.addStretch()

        # 把 copy_btn / copied_label 存到 message_container 上供 hover 使用
        message_container.set_copy_widgets(copy_btn, copied_label)

        container_layout.addWidget(copy_row)

        # 插入到消息列表（在stretch之前）
        count = self.messages_layout.count()
        self.messages_layout.insertWidget(count - 1, message_container)
        
        # 自动滚动到底部
        if self.autoscroll_check.isChecked():
            QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(
                self.scroll_area.verticalScrollBar().maximum()
            ))

    def _on_copy_clicked(self):
        """复制按钮点击处理"""
        btn = self.sender()
        if btn is None:
            return
        msg_text = btn.property("msg_text")
        if msg_text:
            QApplication.clipboard().setText(msg_text)
        # 找到同级的 copied_label（btn 和 label 在同一个 copy_row 里）
        copy_row = btn.parent()
        if copy_row is None:
            return
        copied_label = None
        for child in copy_row.children():
            if isinstance(child, QLabel):
                copied_label = child
                break
        if copied_label is None:
            return
        btn.setVisible(False)
        copied_label.setVisible(True)
        QTimer.singleShot(1500, lambda: (
            copied_label.setVisible(False),
            btn.setVisible(True),
        ))
    
    
    def export_to_excel(self):
        """导出消息记录到 Excel"""
        if not self.message_log:
            self.show_macos_alert("提示", "没有可导出的消息记录")
            return
        try:
            import openpyxl
            from openpyxl.styles import PatternFill, Font, Alignment
        except ImportError:
            self.show_macos_alert("缺少依赖", "请先安装 openpyxl：\npip install openpyxl")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "导出 Excel", "消息记录.xlsx", "Excel 文件 (*.xlsx)"
        )
        if not path:
            return

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "消息记录"

        # 表头
        headers = ["时间", "方向", "内容"]
        ws.append(headers)
        header_fill_sent = PatternFill("solid", fgColor="0071E3")
        header_font = Font(bold=True, color="FFFFFF")
        for col, _ in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col)
            cell.fill = header_fill_sent
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        # 数据行
        sent_fill = PatternFill("solid", fgColor="D6EAFF")
        recv_fill = PatternFill("solid", fgColor="F2F2F7")
        for msg in self.message_log:
            ws.append([msg["time"], msg["direction"], msg["content"]])
            row = ws.max_row
            fill = sent_fill if msg["direction"] == "发送" else recv_fill
            for col in range(1, 4):
                ws.cell(row=row, column=col).fill = fill
                ws.cell(row=row, column=col).alignment = Alignment(wrap_text=True, vertical="center")

        # 列宽
        ws.column_dimensions["A"].width = 22
        ws.column_dimensions["B"].width = 8
        ws.column_dimensions["C"].width = 60

        wb.save(path)
        self.show_macos_alert("导出成功", f"已保存到：\n{path}")

    def clear_display(self):
        """清除显示"""
        # 清除所有消息气泡
        while self.messages_layout.count() > 1:  # 保留最后的stretch
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.sent_count = 0
        self.sent_bytes = 0
        self.received_count = 0
        self.received_bytes = 0
        self.message_log.clear()
        self.update_stats()
    
    def on_data_received(self, data: bytes):
        """接收到数据 - QQ聊天样式（左对齐，灰色气泡）"""
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
        
        try:
            # 获取时间戳
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # 创建气泡消息
            self.add_message_bubble(text, timestamp, is_sent=False)
        except Exception as e:
            import traceback
            traceback.print_exc()
    
    def on_connecting_status(self, status: str):
        """连接状态更新"""
        if status:
            # 开始连接动画
            self.connecting_dots = 0
            self.status_label.setText(status)
            self.status_indicator.setStyleSheet("color: #ff9500;")  # 橙色
            self.connecting_timer.start(500)  # 每500ms更新一次
            
            # 禁用连接按钮
            self.connect_btn.setEnabled(False)
        else:
            # 停止连接动画
            self.connecting_timer.stop()
            self.connect_btn.setEnabled(True)
    
    def update_connecting_animation(self):
        """更新连接动画"""
        self.connecting_dots = (self.connecting_dots + 1) % 4
        dots = "." * self.connecting_dots
        self.status_label.setText(f"正在连接{dots}")
    
    def on_device_connected(self):
        """设备已连接"""
        self.connecting_timer.stop()  # 停止连接动画
        self.connect_btn.setText("断开")
        self.connect_btn.setEnabled(True)
        self.status_indicator.setStyleSheet("color: #34c759;")  # 绿色
        
        if self.current_mode == 'serial':
            self.status_label.setText("串口已连接")
            # 保持串口配置控件启用，允许动态修改
            self.port_combo.setEnabled(False)  # 只禁用端口选择
            self.baud_combo.setEnabled(True)
            self.data_bits_combo.setEnabled(True)
            self.stop_bits_combo.setEnabled(True)
            self.parity_combo.setEnabled(True)
        else:
            self.status_label.setText("蓝牙已连接")
            # 禁用蓝牙配置控件
            self.port_combo.setEnabled(False)
            self.rfcomm_port_spin.setEnabled(False)
        
        # 禁用模式切换
        self.mode_combo.setEnabled(False)
        self.refresh_btn.setEnabled(False)
        
        # 启用发送控件
        self.send_btn.setEnabled(True)
    
    def on_device_disconnected(self):
        """设备已断开"""
        self.connecting_timer.stop()  # 停止连接动画
        self.connect_btn.setText("连接")
        self.connect_btn.setEnabled(True)
        self.status_indicator.setStyleSheet("color: #86868b;")  # 灰色
        self.status_label.setText("未连接")
        
        if self.current_mode == 'serial':
            # 启用串口配置控件
            self.port_combo.setEnabled(True)
            self.baud_combo.setEnabled(True)
            self.data_bits_combo.setEnabled(True)
            self.stop_bits_combo.setEnabled(True)
            self.parity_combo.setEnabled(True)
        else:
            # 启用蓝牙配置控件
            self.port_combo.setEnabled(True)
            self.rfcomm_port_spin.setEnabled(True)
        
        # 启用模式切换
        self.mode_combo.setEnabled(True)
        self.refresh_btn.setEnabled(True)
        
        # 禁用发送控件
        self.send_btn.setEnabled(False)
    
    def on_error(self, error_msg: str):
        """错误处理"""
        self.show_macos_alert("提示", error_msg)
    
    def update_stats(self):
        """更新统计信息"""
        self.sent_stats.setText(f"发送: {self.sent_count} ({self.sent_bytes} 字节)")
        self.received_stats.setText(f"接收: {self.received_count} ({self.received_bytes} 字节)")
    
    def toggle_dark_mode(self):
        """切换黑夜模式"""
        self.is_dark_mode = not self.is_dark_mode
        self.apply_macos_style()  # 重新应用样式
        
        # 通知主窗口更新样式
        main_window = self.parent()
        while main_window and not hasattr(main_window, 'apply_window_style'):
            main_window = main_window.parent()
        if main_window:
            main_window.update_theme(self.is_dark_mode)
    
    def open_github(self):
        """打开 GitHub 仓库"""
        import webbrowser
        webbrowser.open("https://github.com/suci135/Suci-Serial-Port-Assistant")
    
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
    
    def load_quick_commands(self):
        """从配置文件加载快捷命令"""
        return self.quick_command_store.load()
    
    def save_quick_commands(self):
        """保存快捷命令到配置文件"""
        self.quick_command_store.save(self.quick_commands)
