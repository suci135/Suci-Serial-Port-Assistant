import tempfile
import unittest
from pathlib import Path

from src.core.send_history import SendHistoryStore


class SendHistoryStoreTests(unittest.TestCase):
    def test_history_is_unique_bounded_and_persistent(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "history.json"
            store = SendHistoryStore(path, maximum=2)
            store.add("first", "UTF-8")
            store.add("01 02", "HEX")
            store.add("first", "UTF-8")
            store.add("third", "ASCII")

            reloaded = SendHistoryStore(path, maximum=2)
            self.assertEqual(
                reloaded.recent(),
                [
                    {"format": "ASCII", "text": "third"},
                    {"format": "UTF-8", "text": "first"},
                ],
            )

    def test_clear_is_persistent(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "history.json"
            store = SendHistoryStore(path)
            store.add("AT", "ASCII")
            store.clear()
            self.assertEqual(SendHistoryStore(path).recent(), [])


if __name__ == "__main__":
    unittest.main()
