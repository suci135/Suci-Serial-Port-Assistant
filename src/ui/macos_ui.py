"""
macOS 原生风格串口调试工具 UI - 仅支持串口
严格遵循 macOS Human Interface Guidelines
"""

import json
import os
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
        
        # 黑夜模式状态
        self.is_dark_mode = False
        
        # 配置文件路径
        self.config_file = "quick_commands.json"
        
        # 快捷输入数据 - 从配置文件加载
        self.quick_commands = self.load_quick_commands()
        
        self.init_ui()
        self.apply_macos_style()
        self.connect_signals()
        self.refresh_ports()
    
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
        """创建左侧边栏 - 串口连接设置"""
        sidebar = QFrame()
        sidebar.setObjectName("leftSidebar")
        sidebar.setFixedWidth(179)  # 增加宽度，让左边区域更宽
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(10, 20, 10, 20)  # 进一步减少左右边距
        layout.setSpacing(10)  # 减少间距
        
        # Port
        port_label = QLabel("端口")
        port_label.setObjectName("compactLabel")
        layout.addWidget(port_label)
        self.port_combo = QComboBox()
        layout.addWidget(self.port_combo)
        
        # Baud Rate
        baud_label = QLabel("波特率")
        baud_label.setObjectName("compactLabel")
        layout.addWidget(baud_label)
        self.baud_combo = QComboBox()
        self.baud_combo.setEditable(True)
        self.baud_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.baud_combo.setCurrentText("9600")
        layout.addWidget(self.baud_combo)
        
        # Data Bits
        data_label = QLabel("数据位")
        data_label.setObjectName("compactLabel")
        layout.addWidget(data_label)
        self.data_bits_combo = QComboBox()
        self.data_bits_combo.addItems(["5", "6", "7", "8"])
        self.data_bits_combo.setCurrentText("8")
        layout.addWidget(self.data_bits_combo)
        
        # Stop Bits
        stop_label = QLabel("停止位")
        stop_label.setObjectName("compactLabel")
        layout.addWidget(stop_label)
        self.stop_bits_combo = QComboBox()
        self.stop_bits_combo.addItems(["1", "1.5", "2"])
        self.stop_bits_combo.setCurrentText("1")
        layout.addWidget(self.stop_bits_combo)
        
        # Parity
        parity_label = QLabel("校验位")
        parity_label.setObjectName("compactLabel")
        layout.addWidget(parity_label)
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
        self.send_format_combo.setCurrentText("HEX")
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
        self.send_btn.setMinimumHeight(28)  # 减少高度
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
        self.github_btn.setIcon(QIcon("src/resource/GitHub.png"))
        self.github_btn.setIconSize(QSize(20, 20))
        
        # 黑夜模式按钮
        self.dark_mode_btn = QPushButton()
        self.dark_mode_btn.setObjectName("darkModeButton")
        self.dark_mode_btn.setFixedSize(32, 32)
        self.dark_mode_btn.setToolTip("切换黑夜模式")
        self.dark_mode_btn.clicked.connect(self.toggle_dark_mode)
        self.dark_mode_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 设置黑夜模式图标
        self.dark_mode_btn.setIcon(QIcon("src/resource/dark.png"))
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
        if not self.serial_manager.is_connected:
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
        success = False
        
        if format_type == "HEX":
            success = self.serial_manager.send_hex_string(command)
        elif format_type == "ASCII":
            success = self.serial_manager.send_text(command, 'ascii')
        else:  # UTF-8
            success = self.serial_manager.send_text(command, 'utf-8')
        
        if success:
            self.sent_count += 1
            self.sent_bytes += len(command.encode('utf-8'))
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
        font_id = QFontDatabase.addApplicationFont("src/resource/AlimamaFangYuanTiVF-Thin-2.ttf")
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
                color: #1d1d1f;
            }}
            
            #fieldLabel {{
                font-size: 11px;
                font-weight: 500;
                color: #86868b;
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
                image: url(src/resource/triangle.png);
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
                background-color: #e8e8ed;
            }}
            
            #statusFrame {{
                background-color: {bg_color};
                border: 1px solid {border_color};
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
                background-color: {display_bg};
                border: 1px solid {border_color};
                border-radius: 12px;
                padding: 3px;
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
    
    def toggle_dark_mode(self):
        """切换黑夜模式"""
        self.is_dark_mode = not self.is_dark_mode
        print(f"黑夜模式: {self.is_dark_mode}")  # 调试信息
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
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # 如果配置文件不存在，返回默认配置
                return [
                    {"name": "重启模块", "command": "AT+RST", "description": "重启模块", "enabled": True, "delay": 1000, "is_hex": False},
                    {"name": "查询版本信息", "command": "AT+GMR", "description": "查询版本信息", "enabled": True, "delay": 1000, "is_hex": False},
                    {"name": "扫描WiFi热点", "command": "AT+CWLAP", "description": "扫描WiFi热点", "enabled": True, "delay": 1000, "is_hex": False},
                    {"name": "HEX测试数据", "command": "01 02 03 04", "description": "HEX测试数据", "enabled": False, "delay": 1000, "is_hex": True},
                    {"name": "连接WiFi网络", "command": "AT+CWJAP=\"SSID\",\"PASS\"", "description": "连接WiFi网络", "enabled": False, "delay": 1000, "is_hex": False},
                ]
        except Exception as e:
            print(f"加载快捷命令配置失败: {e}")
            # 返回默认配置
            return [
                {"name": "重启模块", "command": "AT+RST", "description": "重启模块", "enabled": True, "delay": 1000, "is_hex": False},
                {"name": "查询版本信息", "command": "AT+GMR", "description": "查询版本信息", "enabled": True, "delay": 1000, "is_hex": False},
                {"name": "扫描WiFi热点", "command": "AT+CWLAP", "description": "扫描WiFi热点", "enabled": True, "delay": 1000, "is_hex": False},
                {"name": "HEX测试数据", "command": "01 02 03 04", "description": "HEX测试数据", "enabled": False, "delay": 1000, "is_hex": True},
                {"name": "连接WiFi网络", "command": "AT+CWJAP=\"SSID\",\"PASS\"", "description": "连接WiFi网络", "enabled": False, "delay": 1000, "is_hex": False},
            ]
    
    def save_quick_commands(self):
        """保存快捷命令到配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.quick_commands, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存快捷命令配置失败: {e}")
