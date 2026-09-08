import unittest

from src.core.receive_render_buffer import ReceiveRenderBuffer


class ReceiveRenderBufferTests(unittest.TestCase):
    def test_coalesces_chunks_and_drains_in_batches(self):
        buffer = ReceiveRenderBuffer(16)
        buffer.append(b"12")
        buffer.append(b"345")
        self.assertEqual(buffer.drain(3), (b"123", 0))
        self.assertEqual(buffer.drain(3), (b"45", 0))

    def test_overflow_keeps_newest_bytes(self):
        buffer = ReceiveRenderBuffer(4)
        buffer.append(b"12")
        buffer.append(b"3456")
        self.assertEqual(buffer.drain(), (b"3456", 2))

    def test_clear_discards_pending_data_and_drop_count(self):
        buffer = ReceiveRenderBuffer(2)
        buffer.append(b"123")
        buffer.clear()
        self.assertEqual(buffer.drain(), (b"", 0))


if __name__ == "__main__":
    unittest.main()
