"""Bounded buffer used while terminal rendering is paused."""

from collections import deque
from typing import Deque, Tuple


class ReceivePauseBuffer:
    def __init__(self, maximum_bytes: int = 512 * 1024):
        self.maximum_bytes = max(1, int(maximum_bytes))
        self.paused = False
        self._chunks: Deque[bytes] = deque()
        self.byte_count = 0
        self.dropped_bytes = 0

    def set_paused(self, paused: bool):
        self.paused = bool(paused)

    def append(self, data: bytes) -> bool:
        """Buffer data when paused; return True when it should render now."""
        if not self.paused:
            return True
        chunk = bytes(data)
        if len(chunk) > self.maximum_bytes:
            self.dropped_bytes += len(chunk) - self.maximum_bytes
            chunk = chunk[-self.maximum_bytes :]
        while self._chunks and self.byte_count + len(chunk) > self.maximum_bytes:
            removed = self._chunks.popleft()
            self.byte_count -= len(removed)
            self.dropped_bytes += len(removed)
        self._chunks.append(chunk)
        self.byte_count += len(chunk)
        return False

    def drain(self) -> Tuple[bytes, int]:
        payload = b"".join(self._chunks)
        dropped = self.dropped_bytes
        self._chunks.clear()
        self.byte_count = 0
        self.dropped_bytes = 0
        return payload, dropped

    def clear(self):
        self._chunks.clear()
        self.byte_count = 0
        self.dropped_bytes = 0
