import unittest

from src.core.ascii_catalog import ascii_entries


class AsciiCatalogTests(unittest.TestCase):
    def test_catalog_contains_all_seven_bit_values(self):
        entries = ascii_entries()
        self.assertEqual(len(entries), 128)
        self.assertEqual([entry.decimal for entry in entries], list(range(128)))

    def test_common_control_and_printable_values(self):
        entries = ascii_entries()
        self.assertEqual((entries[10].name, entries[10].hexadecimal), ("LF", "0A"))
        self.assertEqual((entries[13].name, entries[13].hexadecimal), ("CR", "0D"))
        self.assertEqual(entries[65].character, "A")
        self.assertEqual(entries[127].name, "DEL")


if __name__ == "__main__":
    unittest.main()
