"""Colour ramps along the car (nose -> tail) and shading on the sides. All return/modify a float
RGB base (HxWx3) that you then pass through `rig.fixups` and `rig.to_canvas`."""
from __future__ import annotations

import numpy as np

from ..draw import hex2rgb


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def smoothstep(t, a, b):
    t = np.clip((t - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def solid(rig, color) -> np.ndarray:
    return rig.fill(hex2rgb(color))


def two_stop(rig, c0, c1, start=0.26, end=0.89) -> np.ndarray:
    """c0 at the nose, easing into c1 between `start` and `end` of the car length."""
    c0, c1 = hex2rgb(c0), hex2rgb(c1)
    return rig.fill_by_length(lambda t: lerp(c0, c1, smoothstep(t, start, end)))


def three_stop(rig, c0, c1, c2, first=(0.0, 0.45), second=(0.55, 1.0)) -> np.ndarray:
    """c0 -> c1 over `first`, then -> c2 over `second` (fractions of the car length)."""
    c0, c1, c2 = hex2rgb(c0), hex2rgb(c1), hex2rgb(c2)
    return rig.fill_by_length(
        lambda t: lerp(lerp(c0, c1, smoothstep(t, first[0], first[1])), c2, smoothstep(t, second[0], second[1])))


def shade_sides(rig, base: np.ndarray, floor=0.78, span=0.22) -> np.ndarray:
    """Darken the sides toward the sill: multiplier = floor + span * h (h = 0 at the sill, 1 at the belt)."""
    hh = rig.side_height()
    sides = rig.sides_mask()
    shade = (floor + span * hh)[..., None]
    base[sides] = (base * shade)[sides]
    return base


def paint_islands(rig, base: np.ndarray, targets, color) -> np.ndarray:
    """Flat colour on an island / group / list of them (e.g. mirrors and wing in the accent colour)."""
    col = np.array(hex2rgb(color), np.float32)
    for k in rig.islands(targets):
        base[rig.masks[k]] = col
    return base
