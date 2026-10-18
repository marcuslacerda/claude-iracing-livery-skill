"""Simplified national flags (shapes only, readable at bumper size) and a framed row of them."""
from __future__ import annotations

from PIL import Image, ImageDraw

CODES = ("BR", "MX", "CO", "US", "AR", "DE", "IT", "FR", "GB", "ES", "PT", "NL", "JP")


def draw_flag(code: str, w: int, h: int) -> Image.Image:
    img = Image.new("RGB", (w, h), (255, 255, 255))
    d = ImageDraw.Draw(img)
    code = code.upper()
    if code == "BR":
        d.rectangle([0, 0, w, h], fill=(0, 155, 58))
        d.polygon([(w * 0.5, h * 0.08), (w * 0.92, h * 0.5), (w * 0.5, h * 0.92), (w * 0.08, h * 0.5)], fill=(254, 221, 0))
        r = h * 0.3
        d.ellipse([w * 0.5 - r, h * 0.5 - r, w * 0.5 + r, h * 0.5 + r], fill=(0, 39, 118))
        d.arc([w * 0.5 - r, h * 0.5 - r * 0.8, w * 0.5 + r, h * 0.5 + r * 1.6], 200, 340, fill=(255, 255, 255), width=max(2, h // 14))
    elif code == "MX":
        d.rectangle([0, 0, w / 3, h], fill=(0, 104, 71))
        d.rectangle([2 * w / 3, 0, w, h], fill=(206, 17, 38))
        r = h * 0.14
        d.ellipse([w / 2 - r, h / 2 - r, w / 2 + r, h / 2 + r], fill=(120, 80, 30))
    elif code == "CO":
        d.rectangle([0, 0, w, h / 2], fill=(252, 209, 22))
        d.rectangle([0, h / 2, w, 3 * h / 4], fill=(0, 56, 147))
        d.rectangle([0, 3 * h / 4, w, h], fill=(206, 17, 38))
    elif code == "US":
        for i in range(13):
            if i % 2 == 0:
                d.rectangle([0, i * h / 13, w, (i + 1) * h / 13], fill=(178, 34, 52))
        d.rectangle([0, 0, w * 0.4, h * 7 / 13], fill=(60, 59, 110))
        for row in range(5):
            for col in range(6):
                x = w * 0.4 * (col + 0.5) / 6
                y = h * 7 / 13 * (row + 0.5) / 5
                s = max(1, h // 40)
                d.ellipse([x - s, y - s, x + s, y + s], fill=(255, 255, 255))
    elif code == "AR":
        d.rectangle([0, 0, w, h / 3], fill=(116, 172, 223)); d.rectangle([0, 2 * h / 3, w, h], fill=(116, 172, 223))
    elif code == "DE":
        d.rectangle([0, 0, w, h / 3], fill=(0, 0, 0)); d.rectangle([0, h / 3, w, 2 * h / 3], fill=(221, 0, 0))
        d.rectangle([0, 2 * h / 3, w, h], fill=(255, 206, 0))
    elif code == "IT":
        d.rectangle([0, 0, w / 3, h], fill=(0, 146, 70)); d.rectangle([2 * w / 3, 0, w, h], fill=(206, 43, 55))
    elif code == "FR":
        d.rectangle([0, 0, w / 3, h], fill=(0, 85, 164)); d.rectangle([2 * w / 3, 0, w, h], fill=(239, 65, 53))
    elif code == "GB":
        d.rectangle([0, 0, w, h], fill=(1, 33, 105))
        d.line([(0, 0), (w, h)], fill=(255, 255, 255), width=max(2, h // 6)); d.line([(w, 0), (0, h)], fill=(255, 255, 255), width=max(2, h // 6))
        d.rectangle([w * 0.4, 0, w * 0.6, h], fill=(255, 255, 255)); d.rectangle([0, h * 0.35, w, h * 0.65], fill=(255, 255, 255))
        d.rectangle([w * 0.44, 0, w * 0.56, h], fill=(200, 16, 46)); d.rectangle([0, h * 0.41, w, h * 0.59], fill=(200, 16, 46))
    elif code == "ES":
        d.rectangle([0, 0, w, h], fill=(170, 21, 27)); d.rectangle([0, h / 4, w, 3 * h / 4], fill=(241, 191, 0))
    elif code == "PT":
        d.rectangle([0, 0, w * 0.4, h], fill=(0, 102, 0)); d.rectangle([w * 0.4, 0, w, h], fill=(255, 0, 0))
        r = h * 0.2
        d.ellipse([w * 0.4 - r, h / 2 - r, w * 0.4 + r, h / 2 + r], fill=(255, 204, 0))
    elif code == "NL":
        d.rectangle([0, 0, w, h / 3], fill=(174, 28, 40)); d.rectangle([0, 2 * h / 3, w, h], fill=(33, 70, 139))
    elif code == "JP":
        r = h * 0.3
        d.ellipse([w / 2 - r, h / 2 - r, w / 2 + r, h / 2 + r], fill=(188, 0, 45))
    return img


def row(codes, cell=(72, 50), inner=(66, 44), gap=34, frame=(255, 255, 255)) -> Image.Image:
    """Flags side by side, each on an opaque frame, as one RGBA sprite."""
    cw, ch = cell
    out = Image.new("RGBA", (len(codes) * cw + (len(codes) - 1) * gap, ch), (0, 0, 0, 0))
    pad = ((cw - inner[0]) // 2, (ch - inner[1]) // 2)
    for i, c in enumerate(codes):
        fr = Image.new("RGBA", (cw, ch), tuple(frame) + (255,))
        fr.paste(draw_flag(c, inner[0], inner[1]).convert("RGBA"), pad)
        out.alpha_composite(fr, (i * (cw + gap), 0))
    return out
