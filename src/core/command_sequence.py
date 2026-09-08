"""Background runner for ordered quick-command sequences."""

import threading
from typing import Any, Callable, Dict, List

from PyQt6.QtCore import QObject, pyqtSignal


class CommandSequenceRunner(QObject):
    """Execute enabled commands without blocking the Qt event loop."""

    command_sent = pyqtSignal(str, str)
    command_result = pyqtSignal(int, bool, int)
    completed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._stop_event = threading.Event()
        self._thread = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(
        self,
        commands: List[Dict[str, Any]],
        default_format: str,
        send: Callable[[str, str], bool],
    ) -> bool:
        if self.is_running:
            return False
        selected = [command.copy() for command in commands if command.get("enabled", True)]
        if not selected:
            return False

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            args=(selected, default_format, send),
            daemon=True,
        )
        self._thread.start()
        return True

    def stop(self):
        self._stop_event.set()

    def _run(self, commands, default_format, send):
        try:
            for index, command_data in enumerate(commands):
                if self._stop_event.is_set():
                    break
                command = str(command_data.get("command", "")).strip()
                if not command:
                    continue
                format_type = "HEX" if command_data.get("is_hex", False) else default_format
                self.command_sent.emit(command, format_type)
                success = send(command, format_type)
                byte_count = self._byte_count(command, format_type)
                self.command_result.emit(index, success, byte_count)
                delay = max(0, int(command_data.get("delay", 1000)))
                if self._stop_event.wait(delay / 1000.0):
                    break
        finally:
            self.completed.emit()

    @staticmethod
    def _byte_count(command: str, format_type: str) -> int:
        try:
            if format_type == "HEX":
                value = "".join(c for c in command if c in "0123456789abcdefABCDEF")
                if len(value) % 2:
                    value = "0" + value
                return len(bytes.fromhex(value))
            encoding = "ascii" if format_type == "ASCII" else "utf-8"
            return len(command.encode(encoding, errors="replace"))
        except (ValueError, UnicodeError):
            return 0
