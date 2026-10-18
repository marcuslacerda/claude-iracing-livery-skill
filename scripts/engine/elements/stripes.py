"""Longitudinal stripes: run the whole side, dive into the front fender, climb again over the rear
quarter, and (optionally) wrap across the rear bumper as one continuous band set. This is the design
language that reads best in the sim: stripes that cross panels tie the car together.

Paths are in car coordinates: [(x, h), ...] with x along the template (nose..tail) and h the height
fraction (0 = sill, 1 = belt line). Both sides are drawn from the same path.
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image

from ..draw import SSDraw, hex2rgb
from ..rig import CalibrationError
from .gradient import smoothstep

# a gentle dive over the front fender and a milder one over the rear quarter (Cup-proven knots)
DEFAULT_KNOTS = [(200, 0.12), (420, 0.22), (760, 0.50), (1250, 0.50), (1600, 0.37), (1840, 0.30)]


def smooth_path(knots, step=8):
    """Cosine S-curves between knots -> a dense [(x, h), ...] path."""
    out = []
    for (x0, h0), (x1, h1) in zip(knots[:-1], knots[1:]):
        for x in np.arange(x0, x1, step):
            v = (x - x0) / (x1 - x0)
            out.append((float(x), h0 + (h1 - h0) * 0.5 * (1 - math.cos(math.pi * v))))
    out.append(knots[-1])
    return out


def offset(path, dh):
    return [(x, h + dh) for x, h in path]


def trio(path, colors, widths=(22, 84, 30), offsets=(-0.12, 0.0, 0.13)):
    """Three bands around a path: colors = [(light, dark), ...] per band (light at the nose, dark at
    the tail). Returns the `bands` list `longitudinal` takes."""
    bands = []
    for dh, w, (light, dark) in zip(offsets, widths, colors):
        p = path if dh == 0 else offset(path, dh)
        bands.append((p, w, hex2rgb(light), hex2rgb(dark)))
    return bands


def longitudinal(rig, canvas: Image.Image, bands, fade=(0.26, 0.89), ss=4):
    """Draw bands [(path, width_px, light_rgb, dark_rgb), ...] on both sides; each band's colour fades
    from light at the nose to dark at the tail with a smoothstep over `fade` (fractions of the length)."""
    N = rig.N
    x0, x1 = rig.spec.length
    tx = smoothstep(np.clip((np.arange(N) - x0) / (x1 - x0), 0, 1), fade[0], fade[1]).astype(np.float32)
    for pts, w, light, dark in bands:
        layer = Image.new("RGBA", (N, N), (0, 0, 0, 0))
        for side in rig.spec.sides:
            rig.side_polyline(layer, pts, light, w, side, ss=ss)
        a = np.array(layer)[..., 3]
        row = (np.array(light, np.float32)[None, :] * (1 - tx)[:, None]
               + np.array(dark, np.float32)[None, :] * tx[:, None])
        rgb = np.repeat(row[None, :, :], N, axis=0).astype(np.uint8)
        canvas.alpha_composite(Image.fromarray(np.dstack([rgb, a]), "RGBA"))


def rear_bumper_wrap(rig, canvas: Image.Image, bands, h_end=0.22, wave_amp=12, wave_cycles=2,
                     end_lift=36.0, end_from=0.28, ss=4):
    """Continue the stripes across the rear bumper: bands = [(dh, width_px, rgb), ...] around the
    height `h_end` (side units), with one gentle wave and ends rising toward the corners to meet the
    side stripes coming down. Needs car.toml [bumper_rear] (island, x_range, h_top, y_top, px_per_h,
    side_px_per_h, canvas)."""
    cfg = rig.spec.section("bumper_rear")
    if not cfg:
        raise CalibrationError(f"{rig.spec.slug} has no [bumper_rear] calibration: stripes can't wrap the rear bumper")
    N = rig.N
    H_TOP, Y_TOP, PX_PER_H = cfg["h_top"], cfg["y_top"], cfg["px_per_h"]
    SIDE_PX_PER_H = cfg.get("side_px_per_h", 516)
    cw, ch = cfg.get("canvas", (1300, 300))

    def y_of_h(h):
        return Y_TOP + (H_TOP - h) * PX_PER_H

    bx0, bx1 = cfg["x_range"]
    xs_b = np.linspace(bx0, bx1, 160)
    u = (xs_b - bx0) / (bx1 - bx0)
    wave = wave_amp * np.sin(2 * np.pi * u * wave_cycles + np.pi / 2) * (1 - np.cos(2 * np.pi * u)) / 2
    e = np.clip((np.abs(u - 0.5) - end_from) / (0.5 - end_from), 0, 1)
    wave = wave + end_lift * 0.5 * (1 - np.cos(np.pi * e))
    big = Image.new("RGBA", (cw * ss, ch * ss), (0, 0, 0, 0))
    bd = SSDraw(big, ss)
    for dh, w, dark in bands:
        yc_b = y_of_h(h_end + dh) - wave
        hw = w * PX_PER_H / SIDE_PX_PER_H / 2                                 # side px -> bumper px
        band = ([(x, y - hw) for x, y in zip(xs_b, yc_b)]
                + [(x, y + hw) for x, y in zip(xs_b[::-1], yc_b[::-1])])
        bd.polygon(band, fill=tuple(hex2rgb(dark)) + (255,))
    bump = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    bump.alpha_composite(big.resize((cw, ch), Image.LANCZOS), (0, 0))
    a = np.array(bump)[..., 3] * rig.masks[cfg["island"]]
    bump.putalpha(Image.fromarray(a.astype(np.uint8)))
    canvas.alpha_composite(bump)
