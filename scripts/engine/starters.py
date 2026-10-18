"""Shared helpers for the starter designs (and for any design you write).

Resolution rule for every starter: a PARAMS value wins when set; an empty value ("" / 0 / None) falls
back to <workspace>/brand.toml; and when the brand doesn't declare it either, the built-in fallback.
"""
from __future__ import annotations

import numpy as np

from .brand import brand
from .draw import hex2rgb, render_text
from .elements import gradient


def color(p: dict, key: str, fallback):
    """RGB from PARAMS[key], else brand.toml [colors].<key>, else `fallback`."""
    v = p.get(key)
    if v:
        return hex2rgb(v)
    b = brand.color(key, None)
    return b if b is not None else hex2rgb(fallback)


def text(p: dict, fallback="@YOURNAME") -> str:
    return p.get("text") or brand.text or fallback


def logo(height: int, tint=None):
    """The brand logo as a sprite at `height` (tinted to `tint` when given), or None when brand.toml has none."""
    try:
        return brand.logo_sprite(height, color=hex2rgb(tint) if tint else None)
    except Exception as e:  # unreadable file etc.: fall back to text, never crash a render
        print(f"note: brand logo not used ({e})")
        return None


def mark_or_wordmark(p: dict, height: int, text_color, tint=None):
    """The brand logo, or the wordmark text when there is no logo (so every starter renders without one)."""
    spr = logo(height, tint)
    return spr if spr is not None else render_text(text(p), max(24, int(height * 0.6)), color=text_color)


def place_if(rig, zone: str, paint, sprite, **kw):
    """Place only when the car has that zone (partially calibrated cars still render)."""
    if sprite is None or not rig.has_zone(zone):
        return None
    return rig.place(zone, paint, sprite, **kw)


def accent_islands(rig, base, accent):
    """Mirrors / wing / endplates in the accent colour when the car declares an `accent` group."""
    if accent and "accent" in rig.spec.groups:
        gradient.paint_islands(rig, base, "accent", accent)
    return base


def finish(rig, paint, satin: bool, body_roughness=140.0, logo_roughness=33.0):
    """Satin body with glossy logos (the finish that read best in the sim), or the template's default gloss."""
    if satin:
        paint.roughness = (rig.paintable.astype(np.float32), np.full((rig.N, rig.N), float(body_roughness), np.float32))
        paint.logo_roughness = float(logo_roughness)
    return paint
