"""Pop art in the spirit of Romero Britto: organic cells with thick black outlines, smiling heart, sun and fish (Porsche Cup).

pop-britto: pop art inspired by Romero Britto (original art, no copied works). The whole car is cut
into organic cells with thick black outlines (also along every panel edge); each cell is a flat
saturated colour or a pattern (diagonal stripes, dots, checks, zigzag, waves). Smiling heart on a white
balloon with a thick wordmark band (brand.toml text) on the free hood (between the vents and the windshield, tip in
the gap between the vents), segmented sun on the roof, a big segmented fish on a white bubble in the
area behind each door, smile on the front bumper (one row of straight rounded white teeth, continuous
black lip, red mouth), pink wing with white dots and the brand logo + wordmark on a white plate, yellow
mirrors and endplates with black dots, clean white circle for the number. Glossy lacquer everywhere
(roughness 25), black lines a little less glossy (60). density=large (clean, reads from afar) | small."""
import math

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from scipy.spatial import Delaunay, cKDTree

from engine.draw import fit, hex2rgb, render_text
from engine.elements import shark_mouth
from engine.elements import lockup
from engine.starters import logo, text

PARAMS = {"density": "large", "seed": 7, "text": ""}
CAR = "porsche9922cup"

PINK, YELLOW, CYAN, LIME, ORANGE, PURPLE = (hex2rgb(h) for h in
                                            ("ff2d87", "ffd400", "00a8e8", "7ed321", "ff7a00", "9511dd"))
WHITE, BLACK = (255, 255, 255), (14, 14, 16)
PRIMARIES = [PINK, YELLOW, CYAN, LIME, ORANGE, PURPLE, WHITE]
KINDS = ["stripes", "dots", "checker", "zigzag", "waves"]
# spacing = cell size (px on the 2048 template, ~2.6 mm/px on the Cup), line = outline width (~2.5 cm)
DENSITY = {"large": dict(spacing=270, line=11, period=44, solid=0.5),
           "small": dict(spacing=125, line=9, period=26, solid=0.4)}
SS = 4
MOUTH = (196, 16, 52)


# ---- patterns: coverage (0..1) of the secondary colour, anti-aliased (f = signed distance in px) ----
def pattern_alpha(kind, x, y, period, angle):
    c, s = np.cos(angle), np.sin(angle)
    u, v = x * c + y * s, -x * s + y * c
    P = period
    if kind == "stripes":
        f = P / 4 - np.abs(np.mod(v, P) - P / 2)
    elif kind == "zigzag":
        tri = np.abs(np.mod(u / P, 1.0) - 0.5) * 2
        f = (P / 4 - np.abs(np.mod(v + tri * P * 0.7, P) - P / 2)) * 0.8
    elif kind == "waves":
        f = P / 4 - np.abs(np.mod(v + np.sin(u / P * np.pi) * P * 0.4, P) - P / 2)
    elif kind == "dots":
        row = np.floor(v / P)
        du = np.mod(u + np.mod(row, 2) * P / 2, P) - P / 2
        dv = np.mod(v, P) - P / 2
        f = P * 0.24 - np.hypot(du, dv)
    elif kind == "checker":
        sign = np.where((np.mod(u, 2 * P) < P) ^ (np.mod(v, 2 * P) < P), 1.0, -1.0)
        f = sign * np.minimum(np.abs(np.mod(u + P / 2, P) - P / 2), np.abs(np.mod(v + P / 2, P) - P / 2))
    else:
        return np.zeros_like(x, dtype=np.float32)
    return np.clip(f + 0.5, 0, 1).astype(np.float32)


def secondary_for(c1, rng):
    """Britto pairs flat colours with black or white patterns, now and then with another colour."""
    if rng.random() < 0.2:
        return tuple(PRIMARIES[rng.integers(0, 6)]) if c1 == WHITE else rng.choice([c for c in PRIMARIES[:6] if c != c1])
    if c1 == WHITE:
        return BLACK
    return BLACK if rng.random() < 0.55 else WHITE


# ---- the cell field over the whole template -----------------------------------------------------------
def cell_field(rig, cfg, rng, skip):
    N, S = rig.N, cfg["spacing"]
    g = np.arange(-S, N + S, S, dtype=np.float32)
    pts = np.array([(x + rng.uniform(-0.42, 0.42) * S, y + rng.uniform(-0.42, 0.42) * S) for x in g for y in g])
    n = len(pts)

    # colour + pattern per cell, different from the Delaunay neighbours
    indptr, nbrs = Delaunay(pts).vertex_neighbor_vertices
    col = [-1] * n; kind = [""] * n
    for i in rng.permutation(n):
        near = nbrs[indptr[i]:indptr[i + 1]]
        used = {col[j] for j in near}
        free = [k for k in range(len(PRIMARIES)) if k not in used and (k != 6 or rng.random() < 0.6)]
        col[i] = int(rng.choice(free)) if free else int(rng.integers(0, len(PRIMARIES)))
        if rng.random() < cfg["solid"]:
            kind[i] = "solid"
        else:
            usedk = {kind[j] for j in near}
            k = [x for x in KINDS if x not in usedk] or KINDS
            kind[i] = str(rng.choice(k))
    c1 = np.array([PRIMARIES[c] for c in col], np.float32)
    c2 = np.array([secondary_for(PRIMARIES[c], rng) for c in col], np.float32)
    angle = np.radians(rng.choice([0, 30, 45, 60, 90, 120, 135, 150], n))
    period = cfg["period"] * rng.uniform(0.8, 1.25, n)

    # organic cells: Voronoi in a gently warped space; (d2 - d1) / 2 ~ distance to the cell border
    yy, xx = np.nonzero(rig.paintable)
    x, y = xx.astype(np.float32), yy.astype(np.float32)
    A, ph = 0.16 * S, rng.uniform(0, 2 * np.pi, 4)
    xw = x + A * np.sin(2 * np.pi * y / (1.6 * S) + ph[0]) + 0.5 * A * np.sin(2 * np.pi * (x + y) / (0.9 * S) + ph[1])
    yw = y + A * np.sin(2 * np.pi * x / (1.6 * S) + ph[2]) + 0.5 * A * np.sin(2 * np.pi * (x - y) / (0.9 * S) + ph[3])
    d, idx = cKDTree(pts).query(np.c_[xw, yw], k=2, workers=-1)
    cell = idx[:, 0]
    edge = (d[:, 1] - d[:, 0]) / 2

    rgb = c1[cell].copy()
    for k in KINDS:
        sel = np.nonzero(np.array([kind[c] == k for c in range(n)])[cell])[0]
        if len(sel):
            cs = cell[sel]                                                  # per-cell angle and period
            a = pattern_alpha(k, x[sel], y[sel], period[cs], angle[cs])
            rgb[sel] = c1[cell[sel]] * (1 - a[:, None]) + c2[cell[sel]] * a[:, None]

    base = np.zeros((N, N, 3), np.float32)
    base[yy, xx] = rgb
    line = np.zeros((N, N), np.float32)
    line[yy, xx] = np.clip(cfg["line"] / 2 - edge + 0.5, 0, 1)
    line[skip] = 0
    return base, line


def panel_outlines(rig, width):
    """Black outline along every UV island edge: half the width on each side of a seam, so two panels
    that meet on the car show one full-width line (Britto's contour around every shape)."""
    ids = rig.T.ids
    b = ~rig.paintable.copy()
    b[:, 1:] |= ids[:, 1:] != ids[:, :-1]; b[:, :-1] |= ids[:, 1:] != ids[:, :-1]
    b[1:, :] |= ids[1:, :] != ids[:-1, :]; b[:-1, :] |= ids[1:, :] != ids[:-1, :]
    dist = ndimage.distance_transform_edt(~b)
    return np.clip(width / 2 - dist + 0.5, 0, 1).astype(np.float32) * rig.paintable


def pattern_islands(rig, base, line_skip, targets, c1, c2, kind, period, angle=0.0):
    m = rig.mask(targets)
    yy, xx = np.nonzero(m)
    a = pattern_alpha(kind, xx.astype(np.float32), yy.astype(np.float32), period, angle)[:, None]
    base[yy, xx] = np.array(c1, np.float32) * (1 - a) + np.array(c2, np.float32) * a
    line_skip |= m


# ---- sprites (drawn at SS x, outlines as round-joint strokes) ---------------------------------------
class Sprite:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.arr = np.zeros((h * SS, w * SS, 4), np.uint8)

    def mask(self, pts=None, ellipse=None):
        m = Image.new("L", (self.w * SS, self.h * SS), 0)
        d = ImageDraw.Draw(m)
        if pts is not None:
            d.polygon([(px * SS, py * SS) for px, py in pts], fill=255)
        if ellipse is not None:
            d.ellipse([v * SS for v in ellipse], fill=255)
        return np.array(m) > 127

    def fill(self, m, c1, c2=None, kind="solid", period=30, angle=0.0):
        yy, xx = np.nonzero(m)
        if kind == "solid" or c2 is None:
            self.arr[yy, xx, :3] = c1
        else:
            a = pattern_alpha(kind, xx.astype(np.float32), yy.astype(np.float32), period * SS, angle)[:, None]
            self.arr[yy, xx, :3] = (np.array(c1) * (1 - a) + np.array(c2) * a).astype(np.uint8)
        self.arr[yy, xx, 3] = 255

    def image(self):
        return Image.fromarray(self.arr, "RGBA")

    def finish(self, strokes, width):
        """strokes: list of point lists (closed when first == last), drawn black on top."""
        big = self.image()
        d = ImageDraw.Draw(big)
        for pts in strokes:
            sp = [(px * SS, py * SS) for px, py in pts]
            d.line(sp, fill=BLACK + (255,), width=int(width * SS), joint="curve")
            r = width * SS / 2
            for px, py in (sp[0], sp[-1]):
                d.ellipse([px - r, py - r, px + r, py + r], fill=BLACK + (255,))
        return big.resize((self.w, self.h), Image.LANCZOS)


def closed(pts):
    return list(pts) + [pts[0]]


def arc(cx, cy, rx, ry, a0, a1, n=40):
    return [(cx + rx * math.cos(t), cy + ry * math.sin(t)) for t in np.linspace(a0, a1, n)]


def heart_balloon(label, lw):
    """Heart (lobes up) on a white heart-shaped halo, band across it wider than the heart.
    Sprite: width = across the car, height = along it (top = windshield side)."""
    W, H = 470, 255
    s = Sprite(W, H)
    t = np.linspace(0, 2 * np.pi, 260)
    hx, hy = 16 * np.sin(t) ** 3, -(13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t))
    hw, hh, top = 350, H - 34, 17
    sx, sy = hw / (hx.max() - hx.min()), hh / (hy.max() - hy.min())
    heart = [(W / 2 + a * sx, top + (b - hy.min()) * sy) for a, b in zip(hx, hy)]
    hm = s.mask(heart)
    halo_r = 15 * SS
    halo = ndimage.distance_transform_edt(~hm) <= halo_r
    s.fill(halo, WHITE)
    split = [(W / 2 + 16 * math.sin(v * 3.2), top + hh * 0.13 + v * hh * 0.85) for v in np.linspace(0, 1, 30)]
    right = s.mask(split + [(W, H), (W, 0)])
    s.fill(hm & ~right, PINK)
    s.fill(hm & right, ORANGE, BLACK, "stripes", 20, math.radians(45))
    # face in the upper half (the band takes the lower middle)
    ex, ey, erx, ery = hw * 0.20, top + hh * 0.27, hw * 0.065, hh * 0.085
    strokes = []
    for cx in (W / 2 - ex, W / 2 + ex):
        s.fill(s.mask(ellipse=(cx - erx, ey - ery, cx + erx, ey + ery)), WHITE)
        s.fill(s.mask(ellipse=(cx - erx * 0.45, ey - ery * 0.2, cx + erx * 0.45, ey + ery * 0.7)), BLACK)
        strokes.append(closed(arc(cx, ey, erx, ery, 0, 2 * np.pi)))
    for cx in (W / 2 - hw * 0.34, W / 2 + hw * 0.34):
        s.fill(s.mask(ellipse=(cx - 18, ey + 22 - 13, cx + 18, ey + 22 + 13)), YELLOW)
        strokes.append(closed(arc(cx, ey + 22, 18, 13, 0, 2 * np.pi)))
    strokes.append(arc(W / 2, top + hh * 0.33, hw * 0.12, hh * 0.08, 0.15 * np.pi, 0.85 * np.pi))
    by0, by1 = top + hh * 0.47, top + hh * 0.72
    ban = [(6, by0 + 5), (W - 6, by0 - 5), (W - 6, by1 - 5), (6, by1 + 5)]
    s.fill(s.mask(ban), WHITE)
    # halo outline = boundary of the halo mask, traced as the iso-line of the distance field
    out = s.image()
    edge = np.abs(ndimage.distance_transform_edt(~hm) - halo_r) <= lw * SS / 2
    arr = np.array(out)
    arr[edge] = BLACK + (255,)
    out = Image.fromarray(arr, "RGBA")
    big = out
    d = ImageDraw.Draw(big)
    for pts in [closed(heart), split[:-3], closed(ban)] + strokes:
        d.line([(px * SS, py * SS) for px, py in pts], fill=BLACK + (255,), width=int(lw * SS), joint="curve")
    out = big.resize((W, H), Image.LANCZOS)
    txt = fit(render_text(label, 80, color=BLACK), W - 50, (by1 - by0) * 0.74)
    txt = txt.rotate(math.degrees(math.atan2(10, W - 12)), expand=True, resample=Image.BICUBIC)
    out.alpha_composite(txt, (int(W / 2 - txt.width / 2), int((by0 + by1) / 2 - txt.height / 2)))
    return out


def sun_sprite(lw, rng):
    W = 440
    s = Sprite(W, W)
    c, r0, r1, n = W / 2, W * 0.25, W * 0.485, 14
    strokes = []
    cols = [ORANGE, PINK, CYAN, LIME, PURPLE, YELLOW, ORANGE, PINK, CYAN, LIME, PURPLE, YELLOW, PINK, CYAN]
    for i in range(n):
        a = 2 * np.pi * i / n
        hw = np.pi / n * 0.78
        ray = [(c + r0 * 0.92 * math.cos(a - hw), c + r0 * 0.92 * math.sin(a - hw)),
               (c + r1 * math.cos(a), c + r1 * math.sin(a)),
               (c + r0 * 0.92 * math.cos(a + hw), c + r0 * 0.92 * math.sin(a + hw))]
        kind = ["solid", "dots", "stripes"][i % 3]
        sec = WHITE if cols[i] in (PURPLE, PINK, CYAN) else BLACK
        s.fill(s.mask(ray), cols[i], sec, kind, 16, a)
        strokes.append(closed(ray))
    ring = s.mask(ellipse=(c - r0, c - r0, c + r0, c + r0))
    s.fill(ring, YELLOW)
    inner = r0 * 0.78
    s.fill(s.mask(ellipse=(c - inner, c - inner, c + inner, c + inner)) & ring, YELLOW)
    s.fill(ring & ~s.mask(ellipse=(c - inner, c - inner, c + inner, c + inner)), ORANGE, YELLOW, "dots", 13)
    strokes += [closed(arc(c, c, r0, r0, 0, 2 * np.pi, 80)), closed(arc(c, c, inner, inner, 0, 2 * np.pi, 80))]
    # face: closed happy eyes, cheeks, big smile
    for ex in (c - inner * 0.38, c + inner * 0.38):
        strokes.append(arc(ex, c - inner * 0.18, inner * 0.17, inner * 0.14, 1.1 * np.pi, 1.9 * np.pi, 20))
        s.fill(s.mask(ellipse=(ex - 14, c + inner * 0.12 - 10, ex + 14, c + inner * 0.12 + 10)), PINK)
    strokes.append(arc(c, c + inner * 0.12, inner * 0.42, inner * 0.36, 0.12 * np.pi, 0.88 * np.pi, 30))
    return s.finish(strokes, lw)


def fish_sprite(lw):
    """Fish in profile facing LEFT (head at small x), body cut into coloured segments."""
    W, H = 360, 210
    s = Sprite(W, H)
    x0, x1, cy, hh = W * 0.05, W * 0.76, H * 0.5, H * 0.43
    u = np.linspace(0, 1, 60)
    half = hh * np.sin(np.pi * (u ** 0.75)) ** 0.85
    xs = x0 + u * (x1 - x0)
    body = [(px, cy - h) for px, h in zip(xs, half)] + [(px, cy + h) for px, h in zip(xs[::-1], half[::-1])]
    bm = s.mask(body)
    tail = [(x1 - 14, cy), (W * 0.985, H * 0.08), (W * 0.90, cy), (W * 0.985, H * 0.92)]
    s.fill(s.mask(tail) & ~bm, PURPLE, WHITE, "stripes", 14, math.radians(90))
    # segments: wavy boundaries across the body
    cuts = [0.30, 0.52, 0.74]
    lines, prev = [], np.zeros_like(bm)
    fills = [(YELLOW, None, "solid"), (CYAN, WHITE, "dots"), (PINK, BLACK, "stripes"), (LIME, BLACK, "checker")]
    for i in range(4):
        if i < 3:
            xc = x0 + cuts[i] * (x1 - x0)
            ln = [(xc + 10 * math.sin(v * 2 * np.pi), H * v) for v in np.linspace(0, 1, 30)]
            left = s.mask(ln + [(0, H), (0, 0)])
            lines.append(ln)
        else:
            left = np.ones_like(bm)
        seg = bm & left & ~prev
        c1, c2, k = fills[i]
        s.fill(seg, c1, c2, k, 18, math.radians(30))
        prev |= seg
    # eye + mouth + fin
    ex, ey, er = W * 0.15, H * 0.40, H * 0.085
    s.fill(s.mask(ellipse=(ex - er, ey - er, ex + er, ey + er)), WHITE)
    s.fill(s.mask(ellipse=(ex - er * 0.45, ey - er * 0.3, ex + er * 0.45, ey + er * 0.6)), BLACK)
    fin = [(W * 0.40, cy + 6), (W * 0.52, cy + 6), (W * 0.47, cy + hh * 0.75)]
    s.fill(s.mask(fin), ORANGE)
    strokes = [closed(body), closed(tail), closed(fin), closed(arc(ex, ey, er, er, 0, 2 * np.pi)),
               arc(W * 0.09, H * 0.55, W * 0.035, H * 0.05, 0.1 * np.pi, 0.8 * np.pi, 12)]
    # segment lines only inside the body: clip by drawing them, then masking with the body
    out = s.finish(strokes, lw)
    seg = Sprite(W, H).finish(lines, lw)
    a = np.array(seg)[..., 3:4].astype(np.float32) / 255 * (np.array(Image.fromarray(bm.astype(np.uint8) * 255).resize((W, H), Image.LANCZOS))[..., None] / 255)
    o = np.array(out).astype(np.float32)
    o[..., :3] = o[..., :3] * (1 - a) + np.array(BLACK) * a
    return Image.fromarray(o.clip(0, 255).astype(np.uint8), "RGBA")


def fish_emblem(lw, w=406):
    """The fish on a white bubble with a black outline, so it reads over the busy cells."""
    fish = fish_sprite(lw)
    fish = fish.resize((w, int(w * fish.height / fish.width)), Image.LANCZOS)
    W, H = w + 36, fish.height + 30
    s = Sprite(W, H)
    t = np.linspace(0, 2 * np.pi, 120)
    blob = [(W / 2 + (W / 2 - 8) * math.cos(a) * (1 + 0.04 * math.sin(3 * a)),
             H / 2 + (H / 2 - 8) * math.sin(a) * (1 + 0.05 * math.cos(2 * a))) for a in t]
    s.fill(s.mask(blob), WHITE)
    out = s.finish([closed(blob)], lw)
    out.alpha_composite(fish, ((W - fish.width) // 2, (H - fish.height) // 2))
    return out


def number_circle(lw, r=104):
    s = Sprite(2 * r + 8, 2 * r + 8)
    c = r + 4
    s.fill(s.mask(ellipse=(c - r, c - r, c + r, c + r)), WHITE)
    return s.finish([closed(arc(c, c, r, r, 0, 2 * np.pi, 120))], lw * 1.3)


def smile(rig, paint, lw):
    """Mouth lens from the calibrated shark-mouth geometry without its teeth, then one row of straight
    rounded teeth hanging from the upper lip. On island 7 smaller x = LOWER on the car."""
    shark_mouth.draw(rig, paint, dark=MOUTH, lip=BLACK, tooth=WHITE, teeth=False)
    cfg = rig.spec.section("mouth")
    arr = np.array(paint.canvas)
    red = (np.abs(arr[..., :3].astype(int) - np.array(MOUTH)).sum(axis=2) < 40) & rig.masks["bumper_front_low"]
    yc, half, pitch = cfg["centre_y"], cfg["half"], 40
    x0, y0, x1, y1 = 0, 760, 220, 1900
    big = Image.new("RGBA", ((x1 - x0) * SS, (y1 - y0) * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)

    def tooth(yc_, xa, xb, w):
        """Rounded rectangle spanning x xa..xb (template), y yc_ +- w/2, black outline."""
        bx = [(min(xa, xb) - x0) * SS, (yc_ - w / 2 - y0) * SS, (max(xa, xb) - x0) * SS, (yc_ + w / 2 - y0) * SS]
        r = int(w * 0.32 * SS)
        d.rounded_rectangle(bx, radius=r, fill=BLACK + (255,))
        o = int(2.5 * SS)
        d.rounded_rectangle([bx[0] + o, bx[1] + o, bx[2] - o, bx[3] - o], radius=max(1, r - o), fill=WHITE + (255,))

    for y in range(yc - half + 24, yc + half - 18, pitch):
        col = red[y + pitch // 2, x0:x1]
        hi = np.nonzero(col)[0]
        if not len(hi):
            continue
        hi = int(hi.max())
        lo = hi
        while lo > 0 and col[lo - 1]:                                       # the red run under the upper lip
            lo -= 1
        if hi - lo < 34:
            continue
        L = min(30, 0.45 * (hi - lo))
        tooth(y + pitch / 2, hi + x0 + 4, hi + x0 - L, pitch - 5)             # one row hanging from the lip
    layer = big.resize((x1 - x0, y1 - y0), Image.LANCZOS)
    full = Image.new("RGBA", paint.canvas.size, (0, 0, 0, 0))
    full.alpha_composite(layer, (x0, y0))
    a = np.array(full)
    a[..., 3] = (a[..., 3] * rig.masks["bumper_front_low"]).astype(np.uint8)
    paint.canvas.alpha_composite(Image.fromarray(a, "RGBA"))


def brand_lockup(p, height, color):
    """brand.toml logo + wordmark side by side, or the wordmark alone when there is no logo."""
    mark = logo(height)
    if mark is None:
        return render_text(text(p), height, color=color)
    return lockup.horizontal(mark, text(p), height, color=color)


def wing_logo(p, lw):
    lock = fit(brand_lockup(p, 160, BLACK), 250, 62)
    W, H = lock.width + 34, lock.height + 24
    big = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    r, o = 18 * SS, int(lw * 0.8 * SS)
    d.rounded_rectangle([0, 0, W * SS - 1, H * SS - 1], radius=r, fill=BLACK + (255,))
    d.rounded_rectangle([o, o, W * SS - 1 - o, H * SS - 1 - o], radius=r - o, fill=WHITE + (255,))
    out = big.resize((W, H), Image.LANCZOS)
    out.alpha_composite(lock, ((W - lock.width) // 2, (H - lock.height) // 2))
    return out


def side_put(rig, paint, sprite, x, h, key):
    """Sprite drawn as seen from the LEFT side (front = left); the right side island is upside down,
    so it gets a vertical flip (head still toward the nose)."""
    s = rig.side(key)
    clip = rig.masks[s.island].astype(np.float32)
    spr = sprite.transpose(Image.FLIP_TOP_BOTTOM) if s.car_down_y < 0 else sprite
    rig.put(paint, spr, (x, rig.side_y(key, h)), 0, matte=False, clip=clip)


def design(rig, p=PARAMS):
    cfg = DENSITY.get(p.get("density", "large"), DENSITY["large"])
    rng = np.random.default_rng(int(p.get("seed", 7)))
    lw = cfg["line"]
    skip = np.zeros((rig.N, rig.N), bool)
    base = np.zeros((rig.N, rig.N, 3), np.float32)
    pattern_islands(rig, base, skip, ["wing"], PINK, WHITE, "dots", 30)
    pattern_islands(rig, base, skip, ["mirrors", "endplate_l35", "endplate_r38", "endplate_l36", "endplate_r37"],
                       YELLOW, BLACK, "dots", 24)
    cells, line = cell_field(rig, cfg, rng, skip)
    base[~skip] = cells[~skip]
    line = np.maximum(line, panel_outlines(rig, lw))
    base = base * (1 - line[..., None]) + np.array(BLACK, np.float32) * line[..., None]
    paint = rig.to_canvas(base)

    smile(rig, paint, lw)
    # hood: heart balloon over the free lid between the vents (x ~505) and the windshield (x ~690);
    # the tip runs down the gap between the two vents
    rig.place("hood", paint, heart_balloon(text(p), lw), fit=False, dx=-36, matte=False)
    rig.place("roof", paint, sun_sprite(lw, rng), max=(430, 430), matte=False)
    rig.place("wing_centre", paint, wing_logo(p, lw), max=(284, 92), matte=False)
    fish = fish_emblem(lw)
    for key in rig.spec.sides:
        side_put(rig, paint, fish, 1175, 0.40, key)
        side_put(rig, paint, number_circle(lw), 842, 0.415, key)

    rgbf = np.array(paint.canvas.convert("RGB")).astype(np.float32)
    dark = np.clip((60 - rgbf.max(axis=2)) / 30, 0, 1)
    paint.roughness = (rig.paintable.astype(np.float32), (25 + 35 * dark).astype(np.float32))
    paint.logo_roughness = 25.0
    return paint
