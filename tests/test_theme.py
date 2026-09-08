import unittest

from src.ui.design import palette_for


class ThemePaletteTests(unittest.TestCase):
    def test_light_and_dark_have_distinct_surfaces(self):
        self.assertNotEqual(palette_for(False).surface, palette_for(True).surface)
        self.assertNotEqual(palette_for(False).text, palette_for(True).text)

    def test_dark_semantic_colors_are_not_plain_white_controls(self):
        dark = palette_for(True)
        self.assertNotEqual(dark.button.lower(), "#ffffff")
        self.assertNotEqual(dark.selection, dark.surface)
        self.assertNotEqual(dark.accent, dark.danger)


if __name__ == "__main__":
    unittest.main()
