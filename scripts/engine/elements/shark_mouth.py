"""The shark mouth on the front bumper.

A lens open at the centre and closed near the tyres: the upper lip starts at the headlight base and
falls toward the corners, the lower lip starts at the splitter and rises; everything between is
painted dark so the air intakes read as the open mouth; teeth hang from the lips and scale with the
opening; the lower teeth continue onto the intake-wall islands. Shapes are drawn 4x and downsampled.

Geometry comes from car.toml [mouth] (sim-verified per car); colours and options are the design's.
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image

from ..draw import SSDraw, hex2rgb
from ..rig import CalibrationError

OFF_WHITE = (240, 236, 228)


def draw_tooth(md, base, direction, length, width, color, rng=None, lean=0.0):
    """Natural-looking tooth: slightly convex sides (quadratic curves) and a rounded tip.
    base = (x, y) centre of the base; direction = unit vector base -> tip; lean = sideways tip offset (px)."""
    dx, dy = direction
    px, py = -dy, dx                                                          # sideways unit
    if rng is not None:
        length *= rng.uniform(0.86, 1.10); width *= rng.uniform(0.92, 1.08); lean += rng.uniform(-3, 3)
    bx, by = base
    r = max(2.0, width * 0.11)
    length -= r                                                               # rounded tip stays inside the length
    tip = (bx + dx * length + px * lean, by + dy * length + py * lean)
    l0 = (bx + px * width / 2, by + py * width / 2)
    r0 = (bx - px * width / 2, by - py * width / 2)
    cl = (bx + dx * length * 0.5 + px * width * 0.52, by + dy * length * 0.5 + py * width * 0.52)
    cr = (bx - px * width * 0.52 + dx * length * 0.5, by - py * width * 0.52 + dy * length * 0.5)

    def q(p0, c, p1, n=12):
        return [((1 - s) ** 2 * p0[0] + 2 * (1 - s) * s * c[0] + s * s * p1[0],
                 (1 - s) ** 2 * p0[1] + 2 * (1 - s) * s * c[1] + s * s * p1[1]) for s in np.linspace(0, 1, n)]

    pts = q(l0, cl, tip) + q(tip, cr, r0)
    md.polygon(pts, fill=color)
    md.ellipse([tip[0] - r, tip[1] - r, tip[0] + r, tip[1] + r], fill=color)   # rounds the tip, no protrusion


def draw(rig, paint, *, dark=(12, 10, 16), lip=(110, 12, 70), tooth=OFF_WHITE, hook_tooth=(200, 30, 30),
         wall_body=None, teeth=True, ss=4):
    """Draw the mouth (and the intake walls when calibrated) onto `paint`.
    dark: interior; lip: both lips; tooth: teeth colour; hook_tooth: the bigger tooth at the tow hook;
    wall_body: body colour below the lower lip on the intake walls (default: sampled from the canvas)."""
    cfg = rig.spec.section("mouth")
    if not cfg:
        raise CalibrationError(f"{rig.spec.slug} has no [mouth] calibration in car.toml (see docs/new-car.md)")
    canvas = paint.canvas if hasattr(paint, "canvas") else paint
    N = rig.N
    SS = ss
    DARK, LIP = tuple(hex2rgb(dark)) + (255,), tuple(hex2rgb(lip)) + (255,)
    TOOTH, RED = tuple(hex2rgb(tooth)) + (255,), tuple(hex2rgb(hook_tooth)) + (255,)

    yc0, half, x_meet = cfg["centre_y"], cfg["half"], cfg["x_meet"]
    X_LIP, FLAT_HALF, DROP_EXP = cfg["x_lip"], cfg["flat_half"], cfg["drop_exp"]
    floor_a, floor_b = cfg["floor"]
    fe0, fe1 = cfg["floor_ease"]
    re0, re1 = cfg["rise_ease"]
    lip_up, lip_low = cfg.get("lip_width", (14, 10))

    def ease(v):                                                              # cosine ease-in-out, 0..1 -> 0..1
        v = min(1.0, max(0.0, v))
        return 0.5 * (1 - math.cos(math.pi * v))

    def x_up(y):                                                              # flat over the hood, then a sine drop
        d = abs(y - yc0)
        if d <= FLAT_HALF:
            return float(X_LIP)
        u = min(1.0, (d - FLAT_HALF) / (half - FLAT_HALF)) ** DROP_EXP
        return X_LIP - (X_LIP - x_meet) * ease(u)

    def x_low(y):                                                             # cosine dip to the floor, cosine rise
        u = min(1.0, abs(y - yc0) / half)
        floor = floor_a - floor_b * ease((u - fe0) / fe1)
        return floor + (x_meet - floor) * ease((u - re0) / re1)

    REG = tuple(cfg["region"])
    big = Image.new("RGBA", ((REG[2] - REG[0]) * SS, (REG[3] - REG[1]) * SS), (0, 0, 0, 0))
    md = SSDraw(big, SS, REG[0], REG[1])
    ys = list(range(yc0 - half, yc0 + half + 1, 2))
    up = [(x_up(y), y) for y in ys]
    low = [(x_low(y), y) for y in ys]
    md.polygon(up + list(reversed(low)), fill=DARK)                           # interior
    md.polygon([(x + lip_up, y) for x, y in up] + list(reversed(up)), fill=LIP)        # upper lip (polygon band)
    md.polygon(low + [(x - lip_low, y) for x, y in reversed(low)], fill=LIP)           # lower lip
    HOOK_Y = cfg.get("hook_y")
    pitch = cfg["pitch"]
    t_from, t_to = cfg.get("teeth_margin", (30, 20))
    intake = cfg.get("intake_y")
    if teeth:
        rng = np.random.default_rng(cfg.get("seed", 24))
        for yc in range(yc0 - half + t_from, yc0 + half - t_to, pitch):       # upper teeth sized by the opening
            h = x_up(yc) - x_low(yc)
            if h < 20:
                continue
            th = min(54, 0.55 * h); tw = min(36, 0.8 * th)
            red = HOOK_Y is not None and abs(yc - HOOK_Y) < pitch / 2
            draw_tooth(md, (x_up(yc) - 4, yc), (-1, 0), th * (1.25 if red else 1), tw * (1.3 if red else 1),
                       RED if red else TOOTH, rng)
            if intake and intake[0] < yc < intake[1]:                         # centre = air intake: no lower teeth
                continue
            th2 = min(30, 0.32 * h); tw2 = min(24, 0.8 * th2)
            draw_tooth(md, (x_low(yc) + 3, yc + pitch / 2), (1, 0), th2, tw2, TOOTH, rng)
    mouth = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    mouth.alpha_composite(big.resize((REG[2] - REG[0], REG[3] - REG[1]), Image.LANCZOS), (REG[0], REG[1]))
    m7 = rig.masks[cfg["island"]]
    mouth.putalpha(Image.fromarray((np.array(mouth)[..., 3] * m7).astype(np.uint8)))
    canvas.alpha_composite(mouth)

    walls = cfg.get("walls")
    if not walls:
        return
    # intake walls: separate islands. Draw the lower lip + teeth on a sprite in "car space" (y down =
    # car down, x = inboard -> outboard) and transform per piece as calibrated (mirrors lie: test all 4).
    sw, sh = walls["size"]
    X7_TOP, X7_BOT = walls["x7_top"], walls["x7_bot"]
    Y7_IN, Y7_OUT = walls["y7_in"], walls["y7_out"]
    X7_TOP_UP = walls["x7_top_up"]
    UP_SCALE, UP_SHIFT_OUT = walls["up_scale"], walls["up_shift_out"]
    span = Y7_OUT - Y7_IN

    def sx(y7): return (y7 - Y7_IN) / (Y7_OUT - Y7_IN) * sw
    def sy(x7): return (X7_TOP - x7) / (X7_TOP - X7_BOT) * sh
    def sy_up(x7): return (X7_TOP_UP - x7) / (X7_TOP_UP - X7_BOT) * sh

    if wall_body is None:
        first = walls["pieces"][0]
        seed = rig.spec.islands[first["island"]].seed
        wall_body = tuple(int(v) for v in np.array(canvas)[seed[1], seed[0], :3])
    BODY = tuple(hex2rgb(wall_body)) + (255,)

    def build_wall(extra_out):
        spr = Image.new("RGBA", (sw * SS, sh * SS), DARK)
        sd = SSDraw(spr, SS)
        low_pts = [(sx(y7), sy(x_low(y7))) for y7 in np.linspace(Y7_IN, Y7_OUT, 40)]
        sd.polygon(low_pts + [(sw, sh), (0, sh)], fill=BODY)                 # body colour below the lower lip
        sd.polygon(low_pts + [(x, y + lip_low) for x, y in reversed(low_pts)], fill=LIP)
        if not teeth:
            return spr.resize((sw, sh), Image.LANCZOS)
        rng2 = np.random.default_rng(walls.get("seed", 21))
        uppers = [y7 for y7 in range(yc0 - half + t_from, yc0 + half - t_to, pitch) if Y7_IN - 20 <= y7 <= Y7_OUT + 20]
        uppers.sort(key=lambda y: -sx(y))                                     # outboard first
        for i, y7 in enumerate(uppers):
            h = x_up(y7) - x_low(y7)
            th = min(54, 0.55 * h) * sh / (X7_TOP_UP - X7_BOT) * UP_SCALE
            tw = min(36, 0.8 * min(54, 0.55 * h)) * sw / span * UP_SCALE
            # sim-verified: index 0 falls outside the piece; the visible teeth are 1 (outer) and 2 (inner)
            lean = -0.2 * th if i == 1 else 0.0                               # outer visible tooth leans outboard
            shift = UP_SHIFT_OUT + (20 if i == 2 else 0) + (extra_out if i in (1, 2) else 0)
            draw_tooth(sd, (sx(y7) + shift, sy_up(x_up(y7) - 4)), (0, 1), th, tw, TOOTH, rng2, lean=lean)
        for y7 in range(yc0 - half + t_from, yc0 + half - t_to, pitch):
            y7b = y7 + pitch / 2
            if Y7_IN - 10 <= y7b <= Y7_OUT + 10:
                h = x_up(y7b) - x_low(y7b)
                th2 = min(30, 0.32 * h); tw2 = min(24, 0.8 * th2)
                draw_tooth(sd, (sx(y7b), sy(x_low(y7b) + 3)), (0, -1), th2 * sh / (X7_TOP - X7_BOT),
                           tw2 * sw / span, TOOTH, rng2)
        return spr.resize((sw, sh), Image.LANCZOS)

    FLIPS = {"vertical": Image.FLIP_TOP_BOTTOM, "horizontal": Image.FLIP_LEFT_RIGHT, "rotate180": Image.ROTATE_180}
    for piece in walls["pieces"]:
        s = build_wall(piece.get("extra_out", 0))
        flip = piece.get("flip", "none")
        if flip in FLIPS:
            s = s.transpose(FLIPS[flip])
        layer = Image.new("RGBA", (N, N), (0, 0, 0, 0))
        layer.alpha_composite(s, tuple(piece["box"]))
        a = np.array(layer)[..., 3] * rig.masks[piece["island"]]
        layer.putalpha(Image.fromarray(a.astype(np.uint8)))
        canvas.alpha_composite(layer)
