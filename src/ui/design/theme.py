"""Semantic Apple-inspired color tokens for light and dark appearances."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ThemePalette:
    window: str
    sidebar: str
    content: str
    surface: str
    elevated: str
    input: str
    text: str
    secondary_text: str
    tertiary_text: str
    separator: str
    border: str
    button: str
    button_hover: str
    selection: str
    accent: str
    accent_hover: str
    accent_pressed: str
    success: str
    warning: str
    danger: str
    danger_hover: str
    inactive: str
    scroll_handle: str


LIGHT = ThemePalette(
    window="#F5F5F7",
    sidebar="#F0F0F2",
    content="#FAFAFC",
    surface="#FFFFFF",
    elevated="#FFFFFF",
    input="#FFFFFF",
    text="#1D1D1F",
    secondary_text="#6E6E73",
    tertiary_text="#8E8E93",
    separator="#E2E2E7",
    border="#D1D1D6",
    button="#E9E9ED",
    button_hover="#DEDEE3",
    selection="#DCEBFF",
    accent="#007AFF",
    accent_hover="#006EDB",
    accent_pressed="#005BB8",
    success="#34C759",
    warning="#FF9F0A",
    danger="#FF3B30",
    danger_hover="#E9342B",
    inactive="#8E8E93",
    scroll_handle="#B7B7BC",
)

DARK = ThemePalette(
    window="#1C1C1E",
    sidebar="#242426",
    content="#1C1C1E",
    surface="#2C2C2E",
    elevated="#323234",
    input="#242426",
    text="#F5F5F7",
    secondary_text="#AEAEB2",
    tertiary_text="#8E8E93",
    separator="#353537",
    border="#454549",
    button="#3A3A3C",
    button_hover="#48484A",
    selection="#153B66",
    accent="#0A84FF",
    accent_hover="#409CFF",
    accent_pressed="#0071E3",
    success="#30D158",
    warning="#FF9F0A",
    danger="#FF453A",
    danger_hover="#FF6961",
    inactive="#636366",
    scroll_handle="#5A5A5E",
)


def palette_for(dark: bool) -> ThemePalette:
    return DARK if dark else LIGHT
