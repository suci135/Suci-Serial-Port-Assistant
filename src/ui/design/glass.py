"""Glass-material color helpers shared by window and workbench styles."""

from dataclasses import dataclass

from .theme import ThemePalette


def with_alpha(hex_color: str, opacity: float) -> str:
    value = hex_color.lstrip("#")
    if len(value) != 6:
        raise ValueError("Glass colors must use #RRGGBB format")
    red, green, blue = (int(value[index:index + 2], 16) for index in (0, 2, 4))
    alpha = max(0, min(255, round(opacity * 255)))
    return f"rgba({red}, {green}, {blue}, {alpha})"


@dataclass(frozen=True)
class GlassPalette:
    window: str
    title: str
    sidebar: str
    content: str
    surface: str
    elevated: str
    input: str
    button: str
    button_hover: str
    border: str
    separator: str
    shadow: str
    highlight: str


def glass_palette(palette: ThemePalette, dark: bool) -> GlassPalette:
    if dark:
        return GlassPalette(
            window=with_alpha(palette.window, 0.78),
            title=with_alpha(palette.sidebar, 0.70),
            sidebar=with_alpha(palette.sidebar, 0.64),
            content=with_alpha(palette.content, 0.72),
            surface=with_alpha(palette.surface, 0.58),
            elevated=with_alpha(palette.elevated, 0.68),
            input=with_alpha(palette.input, 0.70),
            button=with_alpha(palette.button, 0.66),
            button_hover=with_alpha(palette.button_hover, 0.82),
            border=with_alpha("#FFFFFF", 0.14),
            separator=with_alpha("#FFFFFF", 0.10),
            shadow=with_alpha("#000000", 0.34),
            highlight=with_alpha("#FFFFFF", 0.10),
        )
    return GlassPalette(
        window=with_alpha(palette.window, 0.68),
        title=with_alpha("#FFFFFF", 0.62),
        sidebar=with_alpha("#F7F7FA", 0.60),
        content=with_alpha("#FBFBFD", 0.72),
        surface=with_alpha("#FFFFFF", 0.58),
        elevated=with_alpha("#FFFFFF", 0.72),
        input=with_alpha("#FFFFFF", 0.70),
        button=with_alpha("#FFFFFF", 0.56),
        button_hover=with_alpha("#FFFFFF", 0.82),
        border=with_alpha("#3C3C43", 0.18),
        separator=with_alpha("#3C3C43", 0.14),
        shadow=with_alpha("#182033", 0.18),
        highlight=with_alpha("#FFFFFF", 0.88),
    )
