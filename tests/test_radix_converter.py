import unittest

from src.core.radix_converter import convert_integer, parse_integer


class RadixConverterTests(unittest.TestCase):
    def test_auto_detects_common_prefixes(self):
        self.assertEqual(parse_integer("0b1111"), 15)
        self.assertEqual(parse_integer("0o17"), 15)
        self.assertEqual(parse_integer("0x0F"), 15)

    def test_accepts_grouped_input(self):
        result = convert_integer("1111 1111", 2)
        self.assertEqual(result.decimal, "255")
        self.assertEqual(result.hexadecimal, "FF")
        self.assertEqual(result.byte_hex, "FF")

    def test_accepts_calculator_style_decimal_grouping(self):
        result = convert_integer("312,345", 10)
        self.assertEqual(result.hexadecimal, "4C419")

    def test_fixed_width_uses_twos_complement(self):
        result = convert_integer("-1", 10, 16)
        self.assertEqual(result.binary, "1" * 16)
        self.assertEqual(result.hexadecimal, "FFFF")
        self.assertEqual(result.byte_hex, "FF FF")
        self.assertEqual(result.decimal, "-1")

    def test_fixed_width_preserves_leading_zero_bytes(self):
        result = convert_integer("1", 10, 32)
        self.assertEqual(result.hexadecimal, "00000001")
        self.assertEqual(result.byte_hex, "00 00 00 01")

    def test_rejects_prefix_mismatch_and_overflow(self):
        with self.assertRaises(ValueError):
            convert_integer("0x10", 10)
        with self.assertRaises(ValueError):
            convert_integer("256", 10, 8)


if __name__ == "__main__":
    unittest.main()
