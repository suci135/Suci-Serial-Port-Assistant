#!/usr/bin/env python3
"""
Suci串口助手 - Python 版本
BaudDance Serial Assistant - Python Version

基于 PyQt6 的现代化串口调试工具，macOS 原生风格
"""

import sys
import asyncio
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QSizePolicy
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QAbstractAnimation, QEvent
from PyQt6.QtGui import QFont, QMouseEvent
import qasync

from src.ui.macos_ui import MacOSSerialUI
from src.core.app_config import AppConfig
from src.core.serial_manager import SerialManager


def resource_path(relative_path: str) -> str:
    """获取资源文件的绝对路径，兼容 PyInstaller 打包环境"""
    from src.core.resources import resource_path as get_resource_path
    return get_resource_path(relative_path)


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
        self.setMouseTracking(True)
        
        # 设置窗口
        self.setWindowTitle("Suci的串口/蓝牙助手")
        self.setMinimumSize(900, 600)
        self.resize(1100, 700)
        
        # 设置窗口图标
        from PyQt6.QtGui import QIcon
        self.setWindowIcon(QIcon(resource_path("src/resource/Assistant.png")))
        
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
        self.ui.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        main_layout.addWidget(self.ui)
        
        self.setCentralWidget(main_container)
        
        # 应用 macOS 窗口样式
        self.apply_window_style()
        
        # 用于窗口拖动
        self.drag_position = None
        self._resize_edges = Qt.Edge(0)
        self._resize_start_position = None
        self._resize_start_geometry = None
        self._resize_margin = 8
        self._dragging_window = False
        self._event_filter_installed = False
        
        # 保存窗口默认大小和位置
        self.default_geometry = self.geometry()
        self.is_fullscreen = False
        
        # 创建动画对象
        self.resize_animation = QPropertyAnimation(self, b"geometry")
        self.resize_animation.setDuration(420)
        self.resize_animation.setEasingCurve(QEasingCurve.Type.InOutQuart)

    def showEvent(self, event):
        if not self._event_filter_installed:
            self.installEventFilter(self)
            for child in self.findChildren(QWidget):
                child.installEventFilter(self)
            self._event_filter_installed = True
        super().showEvent(event)

    def _window_edges_at(self, position):
        """Return the resize edges under a global mouse position."""
        rect = self.frameGeometry()
        margin = self._resize_margin
        edges = Qt.Edge(0)
        if rect.left() <= position.x() <= rect.left() + margin:
            edges |= Qt.Edge.LeftEdge
        elif rect.right() - margin <= position.x() <= rect.right():
            edges |= Qt.Edge.RightEdge
        if rect.top() <= position.y() <= rect.top() + margin:
            edges |= Qt.Edge.TopEdge
        elif rect.bottom() - margin <= position.y() <= rect.bottom():
            edges |= Qt.Edge.BottomEdge
        return edges

    @staticmethod
    def _resize_cursor(edges):
        if edges in (Qt.Edge.LeftEdge, Qt.Edge.RightEdge):
            return Qt.CursorShape.SizeHorCursor
        if edges in (Qt.Edge.TopEdge, Qt.Edge.BottomEdge):
            return Qt.CursorShape.SizeVerCursor
        if edges in (Qt.Edge.TopEdge | Qt.Edge.LeftEdge,
                     Qt.Edge.BottomEdge | Qt.Edge.RightEdge):
            return Qt.CursorShape.SizeFDiagCursor
        if edges in (Qt.Edge.TopEdge | Qt.Edge.RightEdge,
                     Qt.Edge.BottomEdge | Qt.Edge.LeftEdge):
            return Qt.CursorShape.SizeBDiagCursor
        return Qt.CursorShape.ArrowCursor

    def _apply_manual_resize(self, position):
        if not self._resize_edges or self._resize_start_geometry is None:
            return

        start = self._resize_start_geometry
        delta = position - self._resize_start_position
        left, top, right, bottom = start.left(), start.top(), start.right(), start.bottom()
        edges = self._resize_edges

        if edges & Qt.Edge.LeftEdge:
            left = min(left + delta.x(), right - self.minimumWidth() + 1)
        if edges & Qt.Edge.RightEdge:
            right = max(right + delta.x(), left + self.minimumWidth() - 1)
        if edges & Qt.Edge.TopEdge:
            top = min(top + delta.y(), bottom - self.minimumHeight() + 1)
        if edges & Qt.Edge.BottomEdge:
            bottom = max(bottom + delta.y(), top + self.minimumHeight() - 1)

        self.setGeometry(left, top, right - left + 1, bottom - top + 1)

    def eventFilter(self, watched, event):
        """Handle resize gestures even when the pointer is over child widgets."""
        if (watched is self or self.isAncestorOf(watched)) and isinstance(event, QMouseEvent):
            event_type = event.type()
            if event_type in (QEvent.Type.MouseButtonPress,
                              QEvent.Type.MouseMove,
                              QEvent.Type.MouseButtonRelease):
                position = event.globalPosition().toPoint()

                if event_type == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                    edges = self._window_edges_at(position)
                    if edges:
                        self._resize_edges = edges
                        self._resize_start_position = position
                        self._resize_start_geometry = self.geometry()
                        self._dragging_window = False
                        return True

                    is_title_child = watched is self.title_bar or self.title_bar.isAncestorOf(watched)
                    is_button = isinstance(watched, QPushButton)
                    if is_title_child and not is_button:
                        self._dragging_window = True
                        self._resize_start_position = position - self.frameGeometry().topLeft()
                        return True

                elif event_type == QEvent.Type.MouseMove:
                    if self._resize_edges:
                        self._apply_manual_resize(position)
                        return True
                    if self._dragging_window and event.buttons() & Qt.MouseButton.LeftButton:
                        self.move(position - self._resize_start_position)
                        return True
                    if not (event.buttons() & Qt.MouseButton.LeftButton):
                        self.setCursor(self._resize_cursor(self._window_edges_at(position)))

                elif event_type == QEvent.Type.MouseButtonRelease:
                    if self._resize_edges or self._dragging_window:
                        self._resize_edges = Qt.Edge(0)
                        self._resize_start_position = None
                        self._resize_start_geometry = None
                        self._dragging_window = False
                        self.unsetCursor()
                        return True

        return super().eventFilter(watched, event)
    
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
        left_buttons.setFixedWidth(179)  # 从219减少到179，匹配左侧边栏宽度
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
        title_label = QLabel("Suci的串口/蓝牙助手")
        title_label.setObjectName("titleLabel")
        layout.addWidget(title_label)
        layout.addStretch()
        
        # 右侧按钮组容器
        right_buttons = QWidget()
        right_buttons.setFixedWidth(350)  # 匹配新的右侧边栏宽度
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
        """切换全屏状态 - 带平滑动画"""
        from PyQt6.QtCore import QRect
        from PyQt6.QtWidgets import QApplication

        # 停止正在进行的动画
        from PyQt6.QtCore import QAbstractAnimation
        if self.resize_animation.state() == QAbstractAnimation.State.Running:
            self.resize_animation.stop()

        # 断开之前的 finished 信号，避免重复触发
        try:
            self.resize_animation.finished.disconnect()
        except TypeError:
            pass

        if self.is_fullscreen:
            # 恢复到默认大小 - 带动画
            self.resize_animation.setStartValue(self.geometry())
            self.resize_animation.setEndValue(self.default_geometry)
            self.resize_animation.finished.connect(lambda: setattr(self, 'is_fullscreen', False))
            self.resize_animation.start()
        else:
            # 保存当前大小和位置作为默认值
            if not self.isMaximized() and not self.isFullScreen():
                self.default_geometry = self.geometry()

            # 获取屏幕尺寸
            screen = QApplication.primaryScreen().availableGeometry()

            # 进入全屏 - 带动画
            self.resize_animation.setStartValue(self.geometry())
            self.resize_animation.setEndValue(screen)
            self.resize_animation.finished.connect(lambda: setattr(self, 'is_fullscreen', True))
            self.resize_animation.start()
    
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

    def changeEvent(self, event):
        """监听窗口状态变化 - 支持任务栏点击最小化/复原"""
        from PyQt6.QtCore import QEvent
        if event.type() == QEvent.Type.WindowStateChange:
            if not (self.windowState() & Qt.WindowState.WindowMinimized):
                self.show()
                self.raise_()
                self.activateWindow()
        super().changeEvent(event)

    def toggle_window_visibility(self):
        """任务栏点击：最小化 / 复原切换"""
        if self.isMinimized():
            self.showNormal()
            self.raise_()
            self.activateWindow()
        else:
            self.showMinimized()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("Serial Port Assistant")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("BaudDance")
    
    # 设置字体
    from PyQt6.QtGui import QFontDatabase
    font_id = QFontDatabase.addApplicationFont(resource_path("src/resource/AlimamaFangYuanTiVF-Thin-2.ttf"))
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

    # 监听应用激活事件：点击任务栏图标时最小化/复原
    def on_app_state_changed(state):
        from PyQt6.QtCore import Qt
        if state == Qt.ApplicationState.ApplicationActive:
            if window.isMinimized():
                window.showNormal()
                window.raise_()
                window.activateWindow()

    app.applicationStateChanged.connect(on_app_state_changed)
    
    # 运行事件循环
    with qasync.QEventLoop(app) as loop:
        asyncio.set_event_loop(loop)
        loop.run_forever()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
