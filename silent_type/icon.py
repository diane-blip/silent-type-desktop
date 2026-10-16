"""Silent Type's icon: the shushing-face emoji, drawn from Windows' own emoji font.

The artwork is Microsoft's Segoe UI Emoji, so it is rendered on each computer
rather than shipped in this repository. Ready shows the plain emoji; recording
and reading add a gold or light-gold dot; off is gray.

`python -m silent_type.icon` writes `silent_type/silent-type.ico` for the Start
menu shortcut and windows.
"""

import os
from functools import cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from . import theme

SHUSH = "\U0001f92b"
EMOJI_FONT = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts" / "seguiemj.ttf"
DOTS = {"recording": theme.ACCENT, "working": theme.ACCENT_LIGHT}
ICO = Path(__file__).with_name("silent-type.ico")


@cache
def _emoji(size):
    """The emoji alone, cropped and centered on a transparent square."""
    canvas = size * 2
    image = Image.new("RGBA", (canvas, canvas))
    try:
        font = ImageFont.truetype(str(EMOJI_FONT), int(size * 0.9))
        ImageDraw.Draw(image).text(
            (canvas // 2, canvas // 2), SHUSH, font=font, embedded_color=True, anchor="mm"
        )
    except OSError:
        # No emoji font: a plain amber face keeps the icon recognizable as Silent Type.
        ImageDraw.Draw(image).ellipse((size // 2, size // 2, size * 3 // 2, size * 3 // 2), fill="#f4b030")
    image = image.crop(image.getbbox())
    side = max(image.size)
    square = Image.new("RGBA", (side, side))
    square.paste(image, ((side - image.width) // 2, (side - image.height) // 2))
    return square.resize((size, size), Image.Resampling.LANCZOS)


def mark(size=256, state="ready"):
    image = _emoji(size).copy()
    if state == "off":
        gray = ImageOps.grayscale(image).convert("RGBA")
        gray.putalpha(image.getchannel("A"))
        return gray
    if state in DOTS:
        dot = size * 0.42
        ImageDraw.Draw(image).ellipse(
            (size - dot, size - dot, size - 1, size - 1),
            fill=DOTS[state],
            outline="white",
            width=max(1, size // 24),
        )
    return image


def write_ico(path=ICO):
    mark(256).save(path, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    return path


if __name__ == "__main__":
    print(write_ico())
