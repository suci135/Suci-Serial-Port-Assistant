"""Bounded buffer that coalesces high-frequency receive events for UI rendering."""


class ReceiveRenderBuffer:
    """Keep the UI responsive without affecting acquisition or recording."""

    def __init__(self, maximum_bytes: int = 1024 * 1024):
        self.maximum_bytes = max(1, int(maximum_bytes))
        self._data = bytearray()
        self.dropped_bytes = 0

    @property
    def byte_count(self) -> int:
        return len(self._data)

    def append(self, data: bytes):
        chunk = bytes(data)
        overflow = len(self._data) + len(chunk) - self.maximum_bytes
        if overflow > 0:
            removed = min(overflow, len(self._data))
            if removed:
                del self._data[:removed]
            chunk_overflow = overflow - removed
            if chunk_overflow:
                chunk = chunk[chunk_overflow:]
            self.dropped_bytes += overflow
        self._data.extend(chunk)

    def drain(self, maximum_bytes: int = None):
        if maximum_bytes is None:
            count = len(self._data)
        else:
            count = min(len(self._data), max(1, int(maximum_bytes)))
        payload = bytes(self._data[:count])
        del self._data[:count]
        dropped = self.dropped_bytes
        self.dropped_bytes = 0
        return payload, dropped

    def clear(self):
        self._data.clear()
        self.dropped_bytes = 0
