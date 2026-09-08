import unittest

from src.ui.design import glass_palette, palette_for, with_alpha


class GlassDesignTests(unittest.TestCase):
    def test_alpha_helper_produces_qt_rgba(self):
        self.assertEqual(with_alpha("#007AFF", 0.5), "rgba(0, 122, 255, 128)")

    def test_glass_surfaces_are_translucent_in_both_themes(self):
        for dark in (False, True):
            glass = glass_palette(palette_for(dark), dark)
            self.assertTrue(glass.window.startswith("rgba("))
            self.assertNotIn(", 255)", glass.window)
            self.assertNotEqual(glass.sidebar, glass.content)

    def test_invalid_color_is_rejected(self):
        with self.assertRaises(ValueError):
            with_alpha("white", 0.5)


if __name__ == "__main__":
    unittest.main()
