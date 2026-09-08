import unittest

from src.ui.responsive_layout import layout_state_for_width


class ResponsiveLayoutPolicyTests(unittest.TestCase):
    def test_narrow_width_hides_side_panes(self):
        state = layout_state_for_width(899)
        self.assertFalse(state.show_navigation)
        self.assertFalse(state.show_inspector)
        self.assertTrue(state.compact_toolbar)

    def test_medium_width_keeps_navigation(self):
        state = layout_state_for_width(1000)
        self.assertTrue(state.show_navigation)
        self.assertFalse(state.show_inspector)

    def test_standard_width_uses_three_panes_with_compact_toolbar(self):
        state = layout_state_for_width(1180)
        self.assertTrue(state.show_navigation)
        self.assertTrue(state.show_inspector)
        self.assertTrue(state.compact_toolbar)

    def test_wide_width_exposes_full_toolbar(self):
        state = layout_state_for_width(1320)
        self.assertTrue(state.show_navigation)
        self.assertTrue(state.show_inspector)
        self.assertFalse(state.compact_toolbar)


if __name__ == "__main__":
    unittest.main()
