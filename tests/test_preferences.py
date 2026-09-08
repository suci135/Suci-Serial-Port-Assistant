import unittest
from datetime import datetime

from src.core.app_config import AppConfig
from src.core.format_preferences import normalize_data_format
from src.core.time_format import millisecond_timestamp


class PreferenceTests(unittest.TestCase):
    def test_default_and_normalized_formats_are_ascii(self):
        config = AppConfig.__new__(AppConfig)._get_default_config()
        self.assertEqual(config["display"]["data_format"], "ASCII")
        self.assertEqual(config["send"]["data_format"], "ASCII")
        self.assertEqual(normalize_data_format("ascii"), "ASCII")
        self.assertEqual(normalize_data_format("utf8"), "UTF-8")

    def test_legacy_config_migrates_without_window_dimensions(self):
        legacy = {
            "display": {"data_format": "hex"},
            "window": {"width": 1600, "height": 900, "maximized": True},
        }
        migrated = AppConfig._migrate_config(legacy)
        AppConfig._merge_defaults(
            migrated, AppConfig.__new__(AppConfig)._get_default_config()
        )
        self.assertEqual(migrated["display"]["data_format"], "ASCII")
        self.assertEqual(migrated["send"]["data_format"], "ASCII")
        self.assertNotIn("width", migrated["window"])
        self.assertNotIn("maximized", migrated["window"])

    def test_timestamp_has_exactly_three_fractional_digits(self):
        value = datetime(2026, 8, 3, 12, 34, 56, 123456)
        self.assertEqual(millisecond_timestamp(value), "12:34:56.123")


if __name__ == "__main__":
    unittest.main()
