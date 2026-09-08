import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QEvent, QObject
from PyQt6.QtWidgets import QApplication, QLabel, QWidget

from src.core.app_config import AppConfig
from src.ui.main_window import MainWindow


class _TopLevelShowProbe(QObject):
    def __init__(self):
        super().__init__()
        self.widgets = []

    def eventFilter(self, watched, event):
        if (
            event.type() == QEvent.Type.Show
            and isinstance(watched, QWidget)
            and watched.isWindow()
        ):
            self.widgets.append(watched)
        return False


class ReceiveWidgetParentingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_receiving_does_not_show_a_top_level_timestamp_label(self):
        with tempfile.TemporaryDirectory() as directory:
            config = AppConfig.__new__(AppConfig)
            config.config_dir = Path(directory)
            config.config_file = config.config_dir / "config.json"
            config._config = config._get_default_config()
            window = MainWindow(config)
            probe = _TopLevelShowProbe()
            self.app.installEventFilter(probe)
            try:
                window.ui._display_received_data(b"CAN_OK\n")
                self.app.processEvents()
                timestamp_windows = [
                    widget
                    for widget in probe.widgets
                    if isinstance(widget, QLabel)
                    and widget.objectName() == "timestampLabel"
                ]
                self.assertEqual(timestamp_windows, [])
            finally:
                self.app.removeEventFilter(probe)
                window.close()


if __name__ == "__main__":
    unittest.main()
