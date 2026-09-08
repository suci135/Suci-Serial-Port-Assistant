import unittest

from src.core.unit_converter import UNIT_GROUPS, convert, format_value


class UnitConverterTests(unittest.TestCase):
    def test_embedded_data_units(self):
        units = {unit.symbol: unit for unit in UNIT_GROUPS["数据"]}
        self.assertEqual(convert(8, units["b"], units["B"]), 1)
        self.assertEqual(convert(1, units["GB"], units["MB"]), 1024)
        self.assertEqual(convert(1, units["MB"], units["KB"]), 1024)
        self.assertEqual(convert(1, units["KB"], units["B"]), 1024)
        self.assertEqual(convert(1, units["B"], units["b"]), 8)

    def test_capacitance_units(self):
        units = {unit.symbol: unit for unit in UNIT_GROUPS["电容"]}
        self.assertEqual(convert(1, units["F"], units["μF"]), 1_000_000)
        self.assertAlmostEqual(convert(470, units["nF"], units["μF"]), 0.47)

    def test_temperature_offsets(self):
        units = {unit.symbol: unit for unit in UNIT_GROUPS["温度"]}
        self.assertAlmostEqual(convert(0, units["°C"], units["°F"]), 32)
        self.assertAlmostEqual(convert(273.15, units["K"], units["°C"]), 0)

    def test_format_value_avoids_float_noise(self):
        self.assertEqual(format_value(0.47), "0.47")


if __name__ == "__main__":
    unittest.main()
