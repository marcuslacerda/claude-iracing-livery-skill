"""Logo + wordmark in one sprite."""
from __future__ import annotations

from PIL import Image, ImageDraw

from .. import fonts
from ..draw import WHITE, hex2rgb


def horizontal(mark: Image.Image, text: str, height: int, text_ratio=0.62, gap_ratio=0.22, color=WHITE,
               font="display", weight="Bold") -> Image.Image:
    """Mark on the left (rendered at `height`, composed as-is), wordmark on the right, vertically centred."""
    fs = int(height * text_ratio)
    f = fonts.font(font, fs, weight)
    tmp = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    bb = tmp.textbbox((0, 0), text, font=f)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    gap = int(height * gap_ratio)
    W = mark.width + gap + tw + 2
    img = Image.new("RGBA", (W, height), (0, 0, 0, 0))
    img.alpha_composite(mark, (0, 0))
    d = ImageDraw.Draw(img)
    d.text((mark.width + gap - bb[0], (height - th) // 2 - bb[1]), text, font=f, fill=tuple(hex2rgb(color)) + (255,))
    return img


def stacked(mark: Image.Image, text: str, height: int, text_ratio=0.28, gap_ratio=0.08, color=WHITE,
            font="display", weight="Bold") -> Image.Image:
    """Mark on top, wordmark under it, centred; total height = `height`."""
    fs = int(height * text_ratio)
    f = fonts.font(font, fs, weight)
    tmp = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    bb = tmp.textbbox((0, 0), text, font=f)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    gap = int(height * gap_ratio)
    mh = max(1, height - th - gap)
    m = mark.resize((max(1, int(mark.width * mh / mark.height)), mh), Image.LANCZOS)
    W = max(m.width, tw) + 2
    img = Image.new("RGBA", (W, height), (0, 0, 0, 0))
    img.alpha_composite(m, ((W - m.width) // 2, 0))
    ImageDraw.Draw(img).text(((W - tw) // 2 - bb[0], mh + gap - bb[1]), text, font=f,
                             fill=tuple(hex2rgb(color)) + (255,))
    return img
