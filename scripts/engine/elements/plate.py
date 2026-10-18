"""Rounded plates behind sprites: legibility on busy backgrounds, and framed tiles."""
from __future__ import annotations

from PIL import Image, ImageDraw

from ..draw import hex2rgb


def rounded_plate(size, radius, color, alpha=255) -> Image.Image:
    img = Image.new("RGBA", tuple(size), (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=radius,
                                          fill=tuple(hex2rgb(color)) + (alpha,))
    return img


def with_plate(sprite: Image.Image, pad, radius, color, alpha=230) -> Image.Image:
    """Put a rounded plate behind a sprite."""
    plate = rounded_plate((sprite.width + 2 * pad, sprite.height + 2 * pad), radius, color, alpha)
    plate.alpha_composite(sprite, (pad, pad))
    return plate


def framed(sprite: Image.Image, pad, color=(255, 255, 255)) -> Image.Image:
    """A sprite on an opaque rectangular frame (e.g. a flag with a white border)."""
    fr = Image.new("RGBA", (sprite.width + 2 * pad, sprite.height + 2 * pad), tuple(hex2rgb(color)) + (255,))
    fr.paste(sprite.convert("RGBA"), (pad, pad))
    return fr
