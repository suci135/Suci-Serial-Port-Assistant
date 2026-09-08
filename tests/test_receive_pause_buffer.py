import unittest

from src.core.receive_pause_buffer import ReceivePauseBuffer


class ReceivePauseBufferTests(unittest.TestCase):
    def test_unpaused_data_bypasses_buffer(self):
        buffer = ReceivePauseBuffer(4)
        self.assertTrue(buffer.append(b"123"))
        self.assertEqual(buffer.byte_count, 0)

    def test_paused_buffer_keeps_newest_data_and_reports_drops(self):
        buffer = ReceivePauseBuffer(4)
        buffer.set_paused(True)
        self.assertFalse(buffer.append(b"12"))
        self.assertFalse(buffer.append(b"345"))
        payload, dropped = buffer.drain()
        self.assertEqual(payload, b"345")
        self.assertEqual(dropped, 2)

    def test_oversized_chunk_keeps_its_tail(self):
        buffer = ReceivePauseBuffer(3)
        buffer.set_paused(True)
        buffer.append(b"12345")
        self.assertEqual(buffer.drain(), (b"345", 2))


if __name__ == "__main__":
    unittest.main()
