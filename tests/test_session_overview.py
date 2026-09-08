import unittest

from src.ui.workbench.session_overview import format_bytes


class SessionOverviewTests(unittest.TestCase):
    def test_formats_traffic_sizes_compactly(self):
        self.assertEqual(format_bytes(512), "512 B")
        self.assertEqual(format_bytes(1536), "1.5 KB")
        self.assertEqual(format_bytes(2 * 1024 * 1024), "2.0 MB")


if __name__ == "__main__":
    unittest.main()
