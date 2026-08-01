import unittest

from src.core.payload_codec import analyze_payload


class PayloadCodecTests(unittest.TestCase):
    def test_hex_accepts_common_separators_and_prefixes(self):
        result = analyze_payload("0x01, 02;A0 ff", "HEX")
        self.assertTrue(result.valid)
        self.assertEqual(result.payload, b"\x01\x02\xa0\xff")
        self.assertEqual(result.normalized, "01 02 A0 FF")

    def test_hex_rejects_half_bytes_and_invalid_characters(self):
        self.assertFalse(analyze_payload("ABC", "HEX").valid)
        self.assertFalse(analyze_payload("01 GG", "HEX").valid)

    def test_ascii_rejects_non_ascii_characters(self):
        self.assertFalse(analyze_payload("串口", "ASCII").valid)

    def test_suffixes_are_in_crlf_order_and_included_in_count(self):
        result = analyze_payload("OK", "UTF-8", True, True)
        self.assertEqual(result.payload, b"OK\r\n")
        self.assertEqual(result.byte_count, 4)


if __name__ == "__main__":
    unittest.main()
