"""Thread-safe session recording for serial and BLE traffic."""

import csv
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Union


class SessionRecorder:
    """Persist raw traffic without making the UI or transport layer file-aware."""

    def __init__(self):
        self._file = None
        self._writer = None
        self._lock = threading.Lock()
        self.path: Optional[Path] = None

    @property
    def is_recording(self) -> bool:
        return self._file is not None

    def start(self, path: Union[str, Path]) -> bool:
        with self._lock:
            if self._file is not None:
                return False
            try:
                target = Path(path)
                target.parent.mkdir(parents=True, exist_ok=True)
                self._file = target.open("w", encoding="utf-8-sig", newline="")
                self._writer = csv.writer(self._file)
                self._writer.writerow(["timestamp", "direction", "length", "hex", "text"])
                self._file.flush()
                self.path = target
                return True
            except OSError:
                self._file = None
                self._writer = None
                self.path = None
                return False

    def record(self, direction: str, data: bytes, timestamp: Optional[str] = None) -> None:
        if not data:
            return
        with self._lock:
            if self._writer is None or self._file is None:
                return
            stamp = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            text = data.decode("utf-8", errors="replace")
            self._writer.writerow([stamp, direction, len(data), data.hex(" ").upper(), text])
            self._file.flush()

    def stop(self) -> Optional[Path]:
        with self._lock:
            path = self.path
            if self._file is not None:
                self._file.close()
            self._file = None
            self._writer = None
            self.path = None
            return path
