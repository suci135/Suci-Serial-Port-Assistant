"""Generate high-DPI Inno Setup branding from the application icon."""

from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ICON = ROOT / "src" / "resource" / "Assistant.png"
OUTPUT_DIR = ROOT / "build_assets" / "installer"


def vertical_gradient(size, top, bottom):
    image = Image.new("RGB", size, top)
    pixels = image.load()
    height = max(1, size[1] - 1)
    for y in range(size[1]):
        ratio = y / height
        color = tuple(round(a + (b - a) * ratio) for a, b in zip(top, bottom))
        for x in range(size[0]):
            pixels[x, y] = color
    return image.convert("RGBA")


def add_soft_shapes(image, dark):
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")
    blue = (10, 132, 255, 34 if dark else 28)
    orange = (255, 159, 10, 24 if dark else 20)
    draw.ellipse((-160, -100, 360, 420), fill=blue)
    draw.ellipse((170, 610, 650, 1090), fill=orange)
    draw.rounded_rectangle(
        (44, 730, 326, 774), radius=22,
        fill=(255, 255, 255, 18) if dark else (255, 255, 255, 120),
    )
    draw.rounded_rectangle(
        (126, 794, 448, 838), radius=22,
        fill=(10, 132, 255, 90 if dark else 72),
    )
    draw.ellipse((64, 743, 82, 761), fill=(48, 209, 88, 230))
    draw.ellipse((146, 807, 164, 825), fill=(255, 255, 255, 220))
    image.alpha_composite(overlay)


def add_logo_surface(image, dark):
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")
    draw.rounded_rectangle(
        (48, 118, 444, 594),
        radius=58,
        fill=(255, 255, 255, 238 if dark else 118),
        outline=(255, 255, 255, 42 if dark else 130),
        width=2,
    )
    image.alpha_composite(overlay)


def contain(image, size):
    copy = image.copy()
    copy.thumbnail(size, Image.Resampling.LANCZOS)
    return copy


def build_wizard(icon, dark):
    background = vertical_gradient(
        (492, 942),
        (28, 28, 30) if dark else (247, 250, 255),
        (18, 18, 20) if dark else (222, 235, 255),
    )
    add_soft_shapes(background, dark)
    add_logo_surface(background, dark)
    logo = contain(icon, (390, 520))
    x = (background.width - logo.width) // 2
    background.alpha_composite(logo, (x, 150))
    return background.convert("RGB")


def build_small(icon, dark):
    canvas = Image.new(
        "RGBA", (256, 256),
        (44, 44, 46, 255) if dark else (245, 249, 255, 255),
    )
    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.rounded_rectangle(
        (8, 8, 248, 248), radius=54,
        fill=(50, 50, 52, 255) if dark else (255, 255, 255, 255),
        outline=(69, 69, 73, 255) if dark else (210, 226, 248, 255),
        width=4,
    )
    # The full logo contains text that becomes illegible in the 58 px header
    # slot. Use the recognizable serial-port mark only at small sizes.
    mark_source = icon.crop((74, 0, 700, 515))
    mark = contain(mark_source, (196, 196))
    canvas.alpha_composite(mark, ((256 - mark.width) // 2, (256 - mark.height) // 2))
    return canvas


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    icon = Image.open(SOURCE_ICON).convert("RGBA")
    build_wizard(icon, False).save(OUTPUT_DIR / "wizard-light.png", optimize=True)
    build_wizard(icon, True).save(OUTPUT_DIR / "wizard-dark.png", optimize=True)
    build_small(icon, False).save(OUTPUT_DIR / "wizard-small-light.png", optimize=True)
    build_small(icon, True).save(OUTPUT_DIR / "wizard-small-dark.png", optimize=True)
    print(f"Installer visuals generated in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
