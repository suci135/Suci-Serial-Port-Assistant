#!/usr/bin/env python3
"""
Suci串口助手 - Python 版本
BaudDance Serial Assistant - Python Version

基于 PyQt6 的现代化串口调试工具，macOS 原生风格
"""

import sys
import asyncio
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import qasync

from src.ui.macos_ui import MacOSSerialUI
from src.core.app_config import AppConfig
from src.core.serial_manager import SerialManager


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        
        # 初始化管理器
        self.serial_manager = SerialManager()
        
        # 设置窗口为无边框
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        # 设置窗口
        self.setWindowTitle("Suci的串口助手")
        self.setMinimumSize(900, 600)
        self.resize(1100, 700)
        
        # 设置窗口图标
        from PyQt6.QtGui import QIcon
        self.setWindowIcon(QIcon("src/resource/Assistant.png"))
        
        # 创建主容器
        main_container = QWidget()
        main_container.setObjectName("mainContainer")
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建自定义标题栏
        self.title_bar = self.create_title_bar()
        main_layout.addWidget(self.title_bar)
        
        # 创建 UI
        self.ui = MacOSSerialUI(config, self.serial_manager)
        main_layout.addWidget(self.ui)
        
        self.setCentralWidget(main_container)
        
        # 应用 macOS 窗口样式
        self.apply_window_style()
        
        # 用于窗口拖动
        self.drag_position = None
        
        # 保存窗口默认大小和位置
        self.default_geometry = self.geometry()
        self.is_fullscreen = False
    
    def apply_window_style(self):
        """应用窗口样式"""
        self.setStyleSheet("""
            #mainContainer {
                background: #F5F5F7;
                border: 1px solid #d2d2d7;
                border-radius: 10px;
            }
        """)
    
    def update_theme(self, is_dark_mode):
        """更新主题"""
        if is_dark_mode:
            # 黑夜模式
            bg_color = "#1e1e1e"
            border_color = "#404040"
            title_bg = "#2d2d2d"
        else:
            # 日间模式
            bg_color = "#F5F5F7"
            border_color = "#d2d2d7"
            title_bg = "#F5F5F7"
        
        self.setStyleSheet(f"""
            #mainContainer {{
                background: {bg_color};
                border: 1px solid {border_color};
                border-radius: 10px;
            }}
        """)
        
        # 更新标题栏样式
        self.title_bar.setStyleSheet(f"""
            #titleBar {{
                background-color: {title_bg};
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }}
            .macButton {{
                width: 12px;
                height: 12px;
                border-radius: 6px;
                border: none;
            }}
            .macButton:hover {{
                opacity: 0.8;
            }}
            #closeBtn {{
                background-color: #ED6A5E;
            }}
            #minimizeBtn {{
                background-color: #F4BF4F;
            }}
            #maximizeBtn {{
                background-color: #61C554;
            }}
            #titleLabel {{
                color: {"#ffffff" if is_dark_mode else "#1d1d1f"};
                font-weight: 500;
            }}
            #titleSeparator {{
                background-color: {border_color};
                border: none;
            }}
        """)
    
    def create_title_bar(self):
        """创建自定义标题栏"""
        from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QFrame
        
        title_bar = QWidget()
        title_bar.setObjectName("titleBar")
        title_bar.setFixedHeight(40)
        title_bar.setStyleSheet("""
            #titleBar {
                background-color: #F5F5F7;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
            .macButton {
                width: 12px;
                height: 12px;
                border-radius: 6px;
                border: none;
            }
            .macButton:hover {
                opacity: 0.8;
            }
            #closeBtn {
                background-color: #ED6A5E;
            }
            #minimizeBtn {
                background-color: #F4BF4F;
            }
            #maximizeBtn {
                background-color: #61C554;
            }
            #titleLabel {
                color: #1d1d1f;
                font-weight: 500;
            }
            #titleSeparator {
                background-color: #d2d2d7;
                border: none;
            }
        """)
        
        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 左侧按钮组容器
        left_buttons = QWidget()
        left_buttons.setFixedWidth(219)
        left_layout = QHBoxLayout(left_buttons)
        left_layout.setContentsMargins(12, 0, 12, 0)
        left_layout.setSpacing(8)
        
        close_btn = QPushButton()
        close_btn.setObjectName("closeBtn")
        close_btn.setProperty("class", "macButton")
        close_btn.setFixedSize(12, 12)
        close_btn.clicked.connect(self.close)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        minimize_btn = QPushButton()
        minimize_btn.setObjectName("minimizeBtn")
        minimize_btn.setProperty("class", "macButton")
        minimize_btn.setFixedSize(12, 12)
        minimize_btn.clicked.connect(self.showMinimized)
        minimize_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        maximize_btn = QPushButton()
        maximize_btn.setObjectName("maximizeBtn")
        maximize_btn.setProperty("class", "macButton")
        maximize_btn.setFixedSize(12, 12)
        maximize_btn.clicked.connect(self.toggle_maximize)
        maximize_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        left_layout.addWidget(close_btn)
        left_layout.addWidget(minimize_btn)
        left_layout.addWidget(maximize_btn)
        left_layout.addStretch()
        
        layout.addWidget(left_buttons)
        
        # 第一条分隔线
        separator1 = QFrame()
        separator1.setObjectName("titleSeparator")
        separator1.setFrameShape(QFrame.Shape.VLine)
        separator1.setFixedWidth(1)
        layout.addWidget(separator1)
        
        # 中间标题
        layout.addStretch()
        title_label = QLabel("Suci的串口助手")
        title_label.setObjectName("titleLabel")
        layout.addWidget(title_label)
        layout.addStretch()
        
        # 右侧按钮组容器
        right_buttons = QWidget()
        right_buttons.setFixedWidth(240)  # 240是右侧边栏宽度
        right_layout = QHBoxLayout(right_buttons)
        right_layout.setContentsMargins(12, 0, 12, 0)
        right_layout.setSpacing(8)
        
        right_layout.addStretch()
        
        close_btn_r = QPushButton()
        close_btn_r.setObjectName("closeBtn")
        close_btn_r.setProperty("class", "macButton")
        close_btn_r.setFixedSize(12, 12)
        close_btn_r.clicked.connect(self.close)
        close_btn_r.setCursor(Qt.CursorShape.PointingHandCursor)
        
        minimize_btn_r = QPushButton()
        minimize_btn_r.setObjectName("minimizeBtn")
        minimize_btn_r.setProperty("class", "macButton")
        minimize_btn_r.setFixedSize(12, 12)
        minimize_btn_r.clicked.connect(self.showMinimized)
        minimize_btn_r.setCursor(Qt.CursorShape.PointingHandCursor)
        
        maximize_btn_r = QPushButton()
        maximize_btn_r.setObjectName("maximizeBtn")
        maximize_btn_r.setProperty("class", "macButton")
        maximize_btn_r.setFixedSize(12, 12)
        maximize_btn_r.clicked.connect(self.toggle_maximize)
        maximize_btn_r.setCursor(Qt.CursorShape.PointingHandCursor)
        
        right_layout.addWidget(maximize_btn_r)
        right_layout.addWidget(minimize_btn_r)
        right_layout.addWidget(close_btn_r)
        
        layout.addWidget(right_buttons)
        
        return title_bar
    
    def toggle_maximize(self):
        """切换全屏状态"""
        if self.is_fullscreen:
            # 恢复到默认大小
            self.setGeometry(self.default_geometry)
            self.is_fullscreen = False
        else:
            # 保存当前大小和位置作为默认值
            if not self.isMaximized() and not self.isFullScreen():
                self.default_geometry = self.geometry()
            # 进入全屏
            self.showFullScreen()
            self.is_fullscreen = True
    
    def mousePressEvent(self, event):
        """鼠标按下事件 - 用于拖动窗口"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 只在标题栏区域允许拖动
            if event.position().y() <= 40:
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 拖动窗口"""
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position is not None:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        self.drag_position = None


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("Serial Port Assistant")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("BaudDance")
    
    # 设置字体
    from PyQt6.QtGui import QFontDatabase
    font_id = QFontDatabase.addApplicationFont("src/resource/ZiTiGuanJiaFangSongTi-2.ttf")
    if font_id != -1:
        font_families = QFontDatabase.applicationFontFamilies(font_id)
        if font_families:
            font = QFont(font_families[0])
            font_family_name = font_families[0]
        else:
            font = QFont("Microsoft YaHei")
            font_family_name = "Microsoft YaHei"
    else:
        font = QFont("Microsoft YaHei")
        font_family_name = "Microsoft YaHei"
    
    font.setPointSize(9)
    app.setFont(font)
    
    # 保存字体名称供样式使用
    app.setProperty("fontFamily", font_family_name)
    
    # 初始化配置
    config = AppConfig()
    
    # 创建主窗口
    window = MainWindow(config)
    window.show()
    
    # 运行事件循环
    with qasync.QEventLoop(app) as loop:
        asyncio.set_event_loop(loop)
        loop.run_forever()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass