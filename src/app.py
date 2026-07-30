"""Application composition and event-loop entry point."""

import asyncio
import sys

import qasync
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtWidgets import QApplication

from .core.app_config import AppConfig
from .core.resources import resource_path
from .ui.main_window import MainWindow


def main() -> None:
    """Create the application and start its Qt/asyncio event loop."""
    app = QApplication(sys.argv)
    app.setApplicationName("Serial Port Assistant")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("BaudDance")

    font_id = QFontDatabase.addApplicationFont(
        resource_path("src/resource/AlimamaFangYuanTiVF-Thin-2.ttf")
    )
    families = QFontDatabase.applicationFontFamilies(font_id) if font_id != -1 else []
    font_family_name = families[0] if families else "Microsoft YaHei"
    font = QFont(font_family_name)
    font.setPointSize(9)
    app.setFont(font)
    app.setProperty("fontFamily", font_family_name)

    window = MainWindow(AppConfig())
    window.show()

    def on_app_state_changed(state):
        if state == Qt.ApplicationState.ApplicationActive and window.isMinimized():
            window.showNormal()
            window.raise_()
            window.activateWindow()

    app.applicationStateChanged.connect(on_app_state_changed)
    with qasync.QEventLoop(app) as loop:
        asyncio.set_event_loop(loop)
        loop.run_forever()
