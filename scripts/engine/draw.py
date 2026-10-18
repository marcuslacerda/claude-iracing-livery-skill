"""Sprite helpers shared by every design: colours, text, fitting and placing, super-sampled drawing.

All sprites are RGBA with a transparent background. `place` composites onto a canvas and returns
the sprite's alpha as a float mask (designs accumulate it as the "logo" mask for the spec map).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from . import fonts

WHITE = (255, 255, 255)


def hex2rgb(h) -> tuple[int, int, int]:
    """'#9511dd' / '9511dd' / (149, 17, 221) -> (149, 17, 221)."""
    if isinstance(h, (tuple, list)):
        return tuple(int(v) for v in h[:3])
    h = str(h).strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


rgb = hex2rgb


def load_sprite(path) -> Image.Image:
    """A PNG (ideally with transparency) as an RGBA sprite."""
    return Image.open(Path(path).expanduser()).convert("RGBA")


def silhouette(img: Image.Image, color, alpha_from="auto") -> Image.Image:
    """Turn an image into a flat-colour sprite using its transparency (or its darkness, for an opaque
    logo on white) as the shape. This is how brand marks come in: as shapes, never re-drawn by hand."""
    img = img.convert("RGBA")
    a = np.asarray(img)[..., 3]
    if alpha_from == "luma" or (alpha_from == "auto" and a.min() == 255):
        lum = np.asarray(img.convert("L")).astype(np.float32)
        a = (255 - lum).astype(np.uint8)
    out = Image.new("RGBA", img.size, tuple(hex2rgb(color)) + (0,))
    out.putalpha(Image.fromarray(a, "L"))
    return out


def fit(img: Image.Image, max_w, max_h) -> Image.Image:
    """Scale to fit inside max_w x max_h keeping the aspect ratio (up or down)."""
    s = min(max_w / img.width, max_h / img.height)
    return img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.LANCZOS)


def place(canvas: Image.Image, sprite: Image.Image, center, rotate=0, clip=None) -> np.ndarray:
    """Paste an RGBA sprite centred at (x, y) after rotating `rotate` degrees (counter-clockwise).
    clip: boolean mask (H, W); sprite alpha outside it is dropped. Sprites that extend past the canvas
    edge are cropped, never an error. Returns the sprite alpha as a float (H, W) mask."""
    spr = sprite.rotate(rotate, expand=True, resample=Image.BICUBIC)
    x0, y0 = int(center[0] - spr.width / 2), int(center[1] - spr.height / 2)
    W, H = canvas.size
    cx0, cy0 = max(0, -x0), max(0, -y0)
    cx1, cy1 = min(spr.width, W - x0), min(spr.height, H - y0)
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    if cx1 > cx0 and cy1 > cy0:
        if (cx0, cy0, cx1, cy1) != (0, 0, spr.width, spr.height):
            spr = spr.crop((cx0, cy0, cx1, cy1))
        layer.alpha_composite(spr, (x0 + cx0, y0 + cy0))
    a = np.array(layer)[..., 3].astype(np.float32) / 255.0
    if clip is not None:
        a = a * clip
        layer.putalpha(Image.fromarray((a * 255).astype(np.uint8)))
    canvas.alpha_composite(layer)
    return a


def render_text(text: str, height: int, font="display", color=WHITE, weight="Bold", pad=4) -> Image.Image:
    """Single-line text as a tight RGBA sprite of roughly the given cap height.
    `font` is a role (`display`, `text`, `mono`), a font file name or a path (see engine.fonts)."""
    f = fonts.font(font, int(height * 1.35), weight)
    tmp = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    bb = tmp.textbbox((0, 0), text, font=f)
    img = Image.new("RGBA", (bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((pad - bb[0], pad - bb[1]), text, font=f, fill=tuple(hex2rgb(color)) + (255,))
    return img


# ---- curves and bands (anti-aliased outlines) --------------------------------------------------
def qbezier(p0, p1, p2, n=200) -> np.ndarray:
    t = np.linspace(0, 1, n)[:, None]
    return (1 - t) ** 2 * np.array(p0) + 2 * (1 - t) * t * np.array(p1) + t ** 2 * np.array(p2)


def band_polygon(pts, w):
    """Polygon of a stroke of width w along a polyline (offset by the normals): curved outlines must
    be drawn as polygon bands, never as thick `line()` calls, which leave spikes at the joints."""
    pts = np.asarray(pts, np.float64)
    d = np.gradient(pts, axis=0)
    n = np.stack([-d[:, 1], d[:, 0]], axis=1)
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
    left = pts + n * w / 2
    right = pts - n * w / 2
    return [tuple(p) for p in left] + [tuple(p) for p in right[::-1]]


def stroke_band(draw: ImageDraw.ImageDraw, pts, w, fill):
    """A polygon band with round caps."""
    draw.polygon(band_polygon(pts, w), fill=fill)
    for p in (pts[0], pts[-1]):
        draw.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=fill)


class SSDraw:
    """ImageDraw wrapper that draws at `ss`x resolution with an origin offset. Draw curved shapes with
    it on a big image, then `resize(..., Image.LANCZOS)` down: Pillow has no polygon anti-aliasing and
    bumper corners have few texels per cm, so every step shows in the sim otherwise."""

    def __init__(self, img, ss, ox=0, oy=0):
        self.d = ImageDraw.Draw(img); self.ss = ss; self.ox = ox; self.oy = oy

    def _p(self, pts):
        return [((x - self.ox) * self.ss, (y - self.oy) * self.ss) for x, y in pts]

    def _b(self, box):
        return [(box[0] - self.ox) * self.ss, (box[1] - self.oy) * self.ss,
                (box[2] - self.ox) * self.ss, (box[3] - self.oy) * self.ss]

    def polygon(self, pts, fill=None):
        self.d.polygon(self._p(pts), fill=fill)

    def line(self, pts, fill=None, width=1, joint=None):
        self.d.line(self._p(pts), fill=fill, width=int(width * self.ss), joint=joint)

    def ellipse(self, box, fill=None):
        self.d.ellipse(self._b(box), fill=fill)

    def rectangle(self, box, fill=None):
        self.d.rectangle(self._b(box), fill=fill)


def supersampled(size, ss=4, bg=(0, 0, 0, 0)):
    """(big image, SSDraw) pair for drawing a `size` sprite at ss x; finish with `downsample(big, size)`."""
    big = Image.new("RGBA", (size[0] * ss, size[1] * ss), bg)
    return big, SSDraw(big, ss)


def downsample(big: Image.Image, size) -> Image.Image:
    return big.resize(tuple(size), Image.LANCZOS)
