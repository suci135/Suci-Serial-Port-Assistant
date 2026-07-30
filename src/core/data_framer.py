"""Small, reusable helpers for turning a byte stream into application frames."""

from __future__ import annotations

from typing import List, Optional


class DataFrameParser:
    """Parse separator-terminated frames while preserving byte boundaries."""

    def __init__(self, separator: Optional[bytes] = None):
        self.separator = separator
        self._buffer = bytearray()

    def feed(self, data: bytes) -> List[bytes]:
        if data:
            self._buffer.extend(data)
        if not self.separator:
            return []
        frames: List[bytes] = []
        while self.separator in self._buffer:
            index = self._buffer.index(self.separator) + len(self.separator)
            frames.append(bytes(self._buffer[:index]))
            del self._buffer[:index]
        return frames

    def flush(self) -> bytes:
        frame = bytes(self._buffer)
        self._buffer.clear()
        return frame

    def reset(self) -> None:
        self._buffer.clear()
