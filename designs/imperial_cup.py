"""Sci-fi armour: warm white panels with seams and bolts, gunmetal bumpers, winged gear insignia; variant=rebel is a rusty scrapyard ship (Porsche Cup).

imperial-cup: alternate universe where a galactic empire sponsors a racing team (original insignia,
no official logos). Warm armour white with thin black panel seams, bolts, vents and technical stencils;
gunmetal lower front bumper, sills and rear bumper with dust/soot weathering; thin red belt-line
stripe; black winged hex-gear insignia on the hood (reads from the front); hull-panel grid on the roof
with "<code> // <WORDMARK>"; an invented geometric alphabet spelling the wordmark on the rear quarters;
kill marks (struck-through fighter silhouettes) under the window ahead of the door; black wing with
"VELOCITAS IMPERIUM"; red mirrors/endplates; black windshield banner "IMPERIAL RACING DIVISION".
Spec: white roughness 70, gunmetal 160, red 30.
variant=rebel -> "Rebel Scrapyard": dirty off-white, orange side stripes, patched panels in other
colours, rust, burn marks, more kill marks, orange accents, matte overall. code = unit code
(default TK-14 / RS-7)."""
import math

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

from engine.draw import fit, hex2rgb, render_text
from engine.starters import text

PARAMS = {"variant": "imperial", "code": "", "text": "", "seed": 3}
CAR = "porsche9922cup"
SS = 4

WHITE_ARMOR, GUNMETAL, RED = hex2rgb("f2f0ea"), hex2rgb("2b2e33"), hex2rgb("c8102e")
OFF_WHITE, ORANGE = hex2rgb("d9d2c3"), hex2rgb("ff6a13")
INK, SEAM = (16, 16, 18), (34, 35, 38)
PATCH_COLS = [hex2rgb(h) for h in ("9aa3a8", "6f7f8f", "b9a27c", "7d8a6a", "a7826a")]
RUST, RUST_DARK, SOOT, DUST = hex2rgb("a0582a"), hex2rgb("6e3518"), (18, 18, 20), (122, 112, 98)


# ---- noise ----------------------------------------------------------------------------------------
def fbm(N, rng, scales=(6, 14, 34, 90), weights=(0.45, 0.28, 0.17, 0.10), stretch=1.0):
    """Smooth value noise 0..1 (`stretch` > 1 elongates it along x, for streaks)."""
    out = np.zeros((N, N), np.float32)
    for s, w in zip(scales, weights):
        g = rng.random((s, max(2, int(s / stretch)))).astype(np.float32)
        out += w * np.array(Image.fromarray(g).resize((N, N), Image.BICUBIC))
    out -= out.min()
    return out / (out.max() + 1e-6)


def blend(base, mask_a, color):
    a = np.clip(mask_a, 0, 1)[..., None]
    base[:] = base * (1 - a) + np.array(color, np.float32) * a


# ---- sprites ------------------------------------------------------------------------------------------
def ss_canvas(w, h):
    big = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    return big, ImageDraw.Draw(big)


def P(pts):
    return [(x * SS, y * SS) for x, y in pts]


def down(big, w, h):
    return big.resize((w, h), Image.LANCZOS)


def insignia(color, broken=False):
    """Original winged hexagonal gear. Wide sprite (fits the hood box 430x140)."""
    W, H = 900, 300
    big, d = ss_canvas(W, H)
    c = tuple(color) + (255,)
    clear = (0, 0, 0, 0)
    cx, cy, ro, ri, n = W / 2, H / 2, 122, 100, 12
    pts = []
    for i in range(n):
        a = 2 * np.pi * i / n
        for da, r in ((-0.17, ri), (-0.10, ro), (0.10, ro), (0.17, ri)):
            pts.append((cx + r * math.cos(a + da), cy + r * math.sin(a + da)))
    d.polygon(P(pts), fill=c)
    hexa = lambda r, rot=0: [(cx + r * math.cos(rot + k * np.pi / 3), cy + r * math.sin(rot + k * np.pi / 3)) for k in range(6)]
    d.polygon(P(hexa(74, np.pi / 6)), fill=clear)
    d.polygon(P(hexa(46, np.pi / 6)), fill=c)
    d.ellipse([(cx - 15) * SS, (cy - 15) * SS, (cx + 15) * SS, (cy + 15) * SS], fill=clear)
    for s in (-1, 1):                                                          # swept wing blades
        for k in range(4):
            L, yt = 300 - k * 58, cy - 82 + k * 44
            sh = -32 - k * 6
            x_in = cx + s * (ro + 16)
            x_out = x_in + s * L
            d.polygon(P([(x_in, yt), (x_out, yt + sh), (x_out - s * 22, yt + sh + 28), (x_in, yt + 28)]), fill=c)
    if broken:                                                                 # scrapyard: crack + missing tooth
        d.line(P([(cx - 30, cy - ro - 5), (cx - 5, cy - 40), (cx - 25, cy + 10), (cx + 10, cy + ro + 5)]),
               fill=clear, width=10 * SS, joint="curve")
        d.polygon(P([(cx + ro * 0.75, cy - ro * 0.75), (cx + ro * 1.1, cy - ro * 0.45), (cx + ro * 0.6, cy - ro * 0.3)]), fill=clear)
    return down(big, W, H)


GLYPHS = {   # invented geometric alphabet: strokes in a 0.7 x 1 box (y down); unknown chars = a space
    "A": [[(0, 0), (0.7, 0), (0.35, 0.95), (0, 0)], [(0.35, 0.3), (0.35, 0.42)]],
    "B": [[(0, 0), (0, 1), (0.7, 1)], [(0, 0.5), (0.7, 0.2)]],
    "C": [[(0.7, 0), (0, 0), (0, 0.5), (0.5, 0.5)], [(0.2, 1), (0.7, 1)]],
    "D": [[(0.7, 0), (0, 0), (0, 1), (0.7, 1)], [(0.38, 0.33), (0.38, 0.67)]],
    "E": [[(0, 0), (0.7, 0)], [(0, 0.5), (0.5, 0.5)], [(0, 1), (0.3, 1)]],
    "F": [[(0, 1), (0, 0), (0.7, 0)], [(0.3, 0.5), (0.7, 0.5)]],
    "G": [[(0.7, 0), (0, 0.5), (0.7, 1)], [(0.45, 0.5), (0.7, 0.5)]],
    "H": [[(0, 0), (0, 1)], [(0.7, 0), (0.7, 1)], [(0.2, 0.5), (0.5, 0.5)]],
    "I": [[(0.35, 0), (0.35, 1)], [(0.1, 0), (0.6, 0)]],
    "J": [[(0.7, 0), (0.7, 1), (0, 0.7)]],
    "K": [[(0, 0), (0, 1)], [(0.7, 0), (0.25, 0.5), (0.7, 1)]],
    "L": [[(0, 0), (0.7, 0), (0, 1), (0.7, 1)]],
    "M": [[(0, 1), (0, 0), (0.35, 0.5), (0.7, 0), (0.7, 1)]],
    "N": [[(0, 1), (0, 0), (0.7, 1), (0.7, 0)]],
    "O": [[(0.35, 0), (0.7, 0.5), (0.35, 1), (0, 0.5), (0.35, 0)]],
    "P": [[(0, 0), (0.7, 0.5), (0, 1)], [(0.48, 0), (0.7, 0)]],
    "Q": [[(0, 0), (0.7, 0), (0.7, 0.7), (0, 0.7), (0, 0)], [(0.45, 0.85), (0.7, 1)]],
    "R": [[(0, 1), (0, 0), (0.7, 0), (0.7, 0.4)], [(0.3, 0.68), (0.7, 1)]],
    "S": [[(0.7, 0), (0, 0.3), (0.7, 0.7), (0, 1)]],
    "T": [[(0, 0), (0.7, 0)], [(0.35, 0), (0.35, 1)], [(0.15, 1), (0.55, 1)]],
    "U": [[(0, 0), (0, 1), (0.7, 1), (0.7, 0)]],
    "V": [[(0, 0), (0.35, 1), (0.7, 0)]],
    "W": [[(0, 0), (0.18, 1), (0.35, 0.5), (0.52, 1), (0.7, 0)]],
    "X": [[(0, 0.5), (0.35, 0), (0.7, 0.5), (0.35, 1), (0, 0.5)], [(0.35, 0.44), (0.35, 0.56)]],
    "Y": [[(0, 0), (0.35, 0.45), (0.7, 0)], [(0.35, 0.45), (0.35, 1)]],
    "Z": [[(0, 0), (0.7, 0), (0.7, 0.35)], [(0, 0.65), (0, 1), (0.7, 1)]],
    "0": [[(0, 0), (0.7, 0), (0.7, 1), (0, 1), (0, 0)], [(0, 1), (0.7, 0)]],
    "1": [[(0.35, 0), (0.35, 1)]],
    "2": [[(0, 0.2), (0.35, 0), (0.7, 0.2), (0, 1), (0.7, 1)]],
    "3": [[(0, 0), (0.7, 0), (0.3, 0.5), (0.7, 1), (0, 1)]],
    "4": [[(0.5, 1), (0.5, 0), (0, 0.65), (0.7, 0.65)]],
    "5": [[(0.7, 0), (0, 0), (0, 0.45), (0.7, 0.6), (0.5, 1), (0, 1)]],
    "6": [[(0.6, 0), (0, 0.6), (0.35, 1), (0.7, 0.7), (0, 0.6)]],
    "7": [[(0, 0), (0.7, 0), (0.25, 1)]],
    "8": [[(0.35, 0), (0.7, 0.25), (0, 0.75), (0.35, 1), (0.7, 0.75), (0, 0.25), (0.35, 0)]],
    "9": [[(0.7, 0.4), (0.35, 0), (0, 0.3), (0.7, 0.4), (0.1, 1)]],
}


def glyph_text(word, height, color):
    gw, gap, lw = 0.7 * height, 0.32 * height, 0.13 * height
    pad = lw
    W = int(len(word) * (gw + gap) - gap + 2 * pad) + 2
    H = int(height + 2 * pad) + 2
    big, d = ss_canvas(W, H)
    c = tuple(color) + (255,)
    for i, ch in enumerate(word):
        ox = pad + i * (gw + gap)
        for stroke in GLYPHS.get(ch, []):
            pts = [(ox + x * height, pad + y * height) for x, y in stroke]
            d.line(P(pts), fill=c, width=int(lw * SS), joint="curve")
    return down(big, W, H)


def fighter(w, h, color):
    big, d = ss_canvas(w, h)
    u = [(0.5, 0), (0.6, 0.45), (1, 0.72), (1, 0.84), (0.6, 0.74), (0.56, 1), (0.44, 1), (0.4, 0.74), (0, 0.84), (0, 0.72), (0.4, 0.45)]
    d.polygon(P([(x * (w - 2) + 1, y * (h - 2) + 1) for x, y in u]), fill=tuple(color) + (255,))
    return down(big, w, h)


def kill_marks(n, color, slash, cell=40):
    W, H = n * (cell + 10), cell + 6
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for i in range(n):
        img.alpha_composite(fighter(cell - 6, cell - 6, color), (i * (cell + 10) + 3, 6))
    big, d = ss_canvas(W, H)
    for i in range(n):
        x0 = i * (cell + 10)
        d.line(P([(x0 + 2, H - 3), (x0 + cell + 2, 4)]), fill=tuple(slash) + (255,), width=5 * SS)
    img.alpha_composite(down(big, W, H))
    return img


def vent(w=84, h=34, slots=4):
    big, d = ss_canvas(w, h)
    d.rounded_rectangle([0, 0, w * SS - 1, h * SS - 1], radius=6 * SS, fill=(58, 60, 64, 255))
    d.rounded_rectangle([3 * SS, 3 * SS, (w - 3) * SS, (h - 3) * SS], radius=4 * SS, fill=(40, 42, 46, 255))
    for k in range(slots):
        y = 7 + k * (h - 12) / slots
        d.rounded_rectangle([8 * SS, y * SS, (w - 8) * SS, (y + (h - 14) / slots * 0.6) * SS], radius=2 * SS, fill=(12, 12, 14, 255))
    return down(big, w, h)


def bolt(r=6):
    s = 2 * r + 2
    big, d = ss_canvas(s, s)
    d.ellipse([SS, SS, (s - 1) * SS, (s - 1) * SS], fill=(70, 72, 76, 255))
    d.ellipse([3 * SS, 3 * SS, (s - 3) * SS, (s - 3) * SS], fill=(150, 152, 156, 255))
    d.line([(r * SS + SS - 2.4 * SS, (r + 1) * SS), (r * SS + SS + 2.4 * SS, (r + 1) * SS)], fill=(50, 52, 56, 255), width=SS)
    return down(big, s, s)


def roof_plate(code, band, plate, rng):
    W, H = 440, 460
    big, d = ss_canvas(W, H)
    d.rounded_rectangle([0, 0, W * SS - 1, H * SS - 1], radius=12 * SS, fill=SEAM + (255,))
    d.rounded_rectangle([4 * SS, 4 * SS, (W - 4) * SS, (H - 4) * SS], radius=9 * SS, fill=tuple(plate) + (255,))
    g = 44
    darker = tuple(int(v * 0.86) for v in plate) + (255,)
    for i in range(1, W // g):
        for j in range(1, H // g):
            if rng.random() < 0.18:
                d.rectangle([(i * g - g + 4) * SS, (j * g - g + 4) * SS, (i * g) * SS, (j * g) * SS], fill=darker)
    for i in range(1, W // g + 1):
        d.line([(i * g * SS, 6 * SS), (i * g * SS, (H - 6) * SS)], fill=(120, 120, 118, 255), width=2 * SS)
    for j in range(1, H // g + 1):
        d.line([(6 * SS, j * g * SS), ((W - 6) * SS, j * g * SS)], fill=(120, 120, 118, 255), width=2 * SS)
    out = down(big, W, H)
    for i in range(1, W // g + 1, 2):
        for j in range(1, H // g + 1, 2):
            out.alpha_composite(bolt(4), (i * g - 5, j * g - 5))
    bh = 70
    strip = Image.new("RGBA", (W - 8, bh), tuple(band) + (255,))
    txt = fit(render_text(code, 40, font="mono", color=(240, 238, 232)), W - 50, 38)
    strip.alpha_composite(txt, ((strip.width - txt.width) // 2, (bh - txt.height) // 2))
    out.alpha_composite(strip, (4, H // 2 - bh // 2))
    for label, y in (("HULL SECTION 07", 20), ("DO NOT STEP", H - 46)):
        t = render_text(label, 20, font="text", color=(60, 60, 62))
        out.alpha_composite(t, ((W - t.width) // 2, y))
    return out


def wing_text(lines, color):
    rows = [render_text(t, 60, color=color) for t in lines]
    W = max(r.width for r in rows) + 10
    H = sum(r.height for r in rows) + 6
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    y = 0
    for r in rows:
        img.alpha_composite(r, ((W - r.width) // 2, y)); y += r.height + 6
    return img


# ---- placement helpers ----------------------------------------------------------------------------
def side_text(rig, paint, sprite, x, h, key, clip_island=True):
    """Text/marks read correctly on both sides: 180 degrees on the upside-down right side."""
    s = rig.side(key)
    clip = rig.masks[s.island].astype(np.float32) if clip_island else None
    rig.put(paint, sprite, (x, rig.side_y(key, h)), 180 if s.car_down_y < 0 else 0, matte=False, clip=clip)


def panel_seams(rig, width):
    ids = rig.T.ids
    b = ~rig.paintable.copy()
    for ax in (0, 1):
        dif = np.diff(ids, axis=ax) != 0
        if ax == 1:
            b[:, 1:] |= dif; b[:, :-1] |= dif
        else:
            b[1:, :] |= dif; b[:-1, :] |= dif
    dist = ndimage.distance_transform_edt(~b)
    return np.clip(width / 2 - dist + 0.5, 0, 1).astype(np.float32) * rig.paintable


def side_rect_mask(rig, key, x0, x1, h0, h1):
    s = rig.side(key)
    ya, yb = sorted((rig.side_y(key, h0), rig.side_y(key, h1)))
    m = np.zeros((rig.N, rig.N), bool)
    m[int(ya):int(yb), int(x0):int(x1)] = True
    return m & rig.masks[s.island]


# armour seams in car coords (x along the car, h 0 sill .. 1 roof line)
SIDE_SEAMS = [
    [(735, 0.22), (1215, 0.22)],
    [(1215, 0.14), (1215, 0.55), (1262, 0.63)],
    [(450, 0.86), (760, 0.745)],
    [(1560, 0.40), (1640, 0.47), (1800, 0.47)],
]
HOOD_SEAMS = [[(700, 1128), (545, 1128), (505, 1160)], [(700, 1542), (545, 1542), (505, 1510)]]


def design(rig, p=PARAMS):
    rebel = str(p.get("variant", "imperial")).lower().startswith("rebel")
    rng = np.random.default_rng(int(p.get("seed", 3)))
    N = rig.N
    body = OFF_WHITE if rebel else WHITE_ARMOR
    accent = ORANGE if rebel else RED
    base = rig.fill(body)
    rough = np.full((N, N), 150.0 if rebel else 70.0, np.float32)
    hh = rig.side_height()
    sides = rig.sides_mask()

    # gunmetal: lower front bumper (+ intake walls), sills, rear bumper
    gm = rig.mask(["bumper_front_low", "corner_r20", "corner_l21", "bumper_rear", "cup_panel"])
    gm |= sides & (hh <= 0.14)
    base[gm] = GUNMETAL
    rough[gm] = 175.0 if rebel else 160.0

    n1, n2 = fbm(N, rng), fbm(N, rng, stretch=3.0)
    blend(base, gm * 0.30 * np.clip((n1 - 0.45) * 3, 0, 1), DUST)            # dust
    blend(base, gm * 0.45 * np.clip((0.50 - n2) * 3, 0, 1), SOOT)            # soot streaks
    grime = sides & ~gm
    blend(base, grime * np.clip((0.34 - hh) / 0.34, 0, 1) ** 1.6 * (0.16 + 0.22 * n1) * (2.0 if rebel else 1.0), DUST)

    # wing black (imperial) / weathered off-white with orange (rebel); accents on mirrors + endplates
    wing = rig.mask("wing")
    acc = rig.mask(["mirrors", "endplate_l35", "endplate_r38", "endplate_l36", "endplate_r37"])
    if rebel:
        base[wing] = OFF_WHITE
        yy, xx = np.nonzero(wing)
        band = (yy > 168) & (yy < 186) | (yy > 226) & (yy < 236)
        base[yy[band], xx[band]] = ORANGE
    else:
        base[wing] = INK
    base[acc] = accent
    rough[acc] = 90.0 if rebel else 30.0
    base[rig.mask("banner")] = INK

    # belt-line stripe(s)
    stripe = np.zeros((N, N), bool)
    for h0, h1 in (((0.622, 0.655), (0.666, 0.676)) if rebel else ((0.64, 0.655),)):
        m = sides & (hh >= h0) & (hh <= h1)
        xx = np.arange(N)[None, :]
        m &= (xx >= 330) & (xx <= 1800)
        stripe |= m
    base[stripe] = accent
    rough[stripe] = 90.0 if rebel else 30.0

    if rebel:
        # patched panels (car coords), each with a dark border and rivets
        patches = [(1020, 1190, 0.26, 0.50), (450, 600, 0.68, 0.82), (1600, 1780, 0.66, 0.82), (1235, 1380, 0.46, 0.64)]
        for key in rig.spec.sides:
            for k, (x0, x1, h0, h1) in enumerate(patches):
                m = side_rect_mask(rig, key, x0, x1, h0, h1)
                base[m] = PATCH_COLS[(k + (key == "R")) % len(PATCH_COLS)]
                rough[m] = 120.0
                edge = m & ~ndimage.binary_erosion(m, iterations=3)
                base[edge] = SEAM
        hp = np.zeros((N, N), bool); hp[1180:1290, 560:680] = True; hp &= rig.mask("hood")
        base[hp] = PATCH_COLS[1]
        base[hp & ~ndimage.binary_erosion(hp, iterations=3)] = SEAM
        # rust: speckled blobs, more near the sills and on the bumpers
        n3 = fbm(N, rng, scales=(20, 50, 120, 260), weights=(0.3, 0.3, 0.25, 0.15))
        low = np.where(sides, np.clip((0.5 - hh) * 2, 0, 1), 0.08) + gm * 0.45
        rust = np.clip((n3 - 0.76 + 0.22 * low) * 7, 0, 1) * rig.paintable * np.where(wing, 0.35, 1.0)
        blend(base, rust * 0.85, RUST)
        blend(base, np.clip((n3 - 0.86 + 0.22 * low) * 8, 0, 1) * rig.paintable * np.where(wing, 0.35, 1.0), RUST_DARK)
        rough = np.maximum(rough, rust * 210)
        # burn marks: soot behind the rear wheels and around the hood vents, streaked along the car
        xx, yy = np.meshgrid(np.arange(N), np.arange(N))
        burn = np.zeros((N, N), np.float32)
        for key in rig.spec.sides:
            cy = rig.side_y(key, 0.35)
            burn = np.maximum(burn, np.exp(-(((xx - 1720) / 140.0) ** 2 + ((yy - cy) / 90.0) ** 2)))
        burn = np.maximum(burn, np.exp(-(((xx - 470) / 70.0) ** 2 + ((yy - 1335) / 220.0) ** 2)) * 0.7)
        burn *= (0.5 + 0.8 * n2) * rig.paintable
        blend(base, np.clip(burn, 0, 0.85), SOOT)
        rough = np.maximum(rough, burn * 190)
        blend(base, rig.paintable * 0.10 * n1, DUST)                         # overall grime

    seams = panel_seams(rig, 2.2)
    blend(base, seams, SEAM)
    paint = rig.to_canvas(base)

    # armour seams + bolts on the sides, seams on the hood
    for key in rig.spec.sides:
        for pts in SIDE_SEAMS:
            rig.side_polyline(paint.canvas, pts, SEAM, 2.5, key)
        for x in range(770, 1200, 64):
            side_text(rig, paint, bolt(5), x, 0.245, key)
        for h in (0.20, 0.32, 0.44):
            side_text(rig, paint, bolt(5), 1240, h, key)
    hood_layer = Image.new("RGBA", paint.canvas.size, (0, 0, 0, 0))
    dh = ImageDraw.Draw(hood_layer)
    for pts in HOOD_SEAMS:
        dh.line(pts, fill=SEAM + (255,), width=3, joint="curve")
    a = np.array(hood_layer); a[..., 3] = (a[..., 3] * rig.mask("hood")).astype(np.uint8)
    paint.canvas.alpha_composite(Image.fromarray(a, "RGBA"))

    # hood insignia, roof plate, wing motto, windshield banner
    rig.place("hood", paint, insignia(ORANGE if rebel else INK, broken=rebel), max=(430, 140), matte=False)
    plate_col = (196, 190, 176) if rebel else (222, 220, 213)
    word = text(p).lstrip("@").upper()
    code = p.get("code") or ("RS-7" if rebel else "TK-14")
    rig.place("roof", paint, roof_plate(f"{code} // {word}",
                                        (150, 64, 20) if rebel else INK, plate_col, rng), max=(430, 450), matte=False)
    motto = ["SCRAPYARD", "SQUADRON"] if rebel else ["VELOCITAS", "IMPERIUM"]
    rig.place("wing_centre", paint, wing_text(motto, INK if rebel else (240, 238, 232)), max=(280, 88), matte=False)
    btxt = "REBEL SCRAPYARD RACING" if rebel else "IMPERIAL RACING DIVISION"
    rig.put(paint, fit(render_text(btxt, 40, font="text", color=(240, 238, 232)), 470, 34), (933, 1336), -90,
            matte=False, clip=rig.mask("banner").astype(np.float32))

    # sides: the wordmark in the invented alphabet on the rear quarter, kill marks under the window,
    # vents and stencils
    glyphs = glyph_text(word, 44, INK)
    marks = kill_marks(8 if rebel else 5, INK, ORANGE if rebel else RED, cell=34 if rebel else 40)
    for key in rig.spec.sides:
        side_text(rig, paint, fit(glyphs, 250, 50), 1556, 0.555, key)
        side_text(rig, paint, fit(marks, 300 if rebel else 250, 42 if rebel else 44), 890, 0.585 if rebel else 0.595, key)
        side_text(rig, paint, vent(), 360, 0.56, key)
        side_text(rig, paint, vent(70, 30, 3), 1700, 0.74, key)
        side_text(rig, paint, render_text("MK-IV ARMOR", 20, font="text", color=SEAM), 1090, 0.42, key)
        side_text(rig, paint, render_text(code, 22, font="mono", color=SEAM), 1600, 0.84, key)

    # spec: red accents glossy (imperial), everything else from `rough`
    arr = np.array(paint.canvas.convert("RGB")).astype(np.int32)
    if not rebel:
        red = (arr[..., 0] > 150) & (arr[..., 1] < 70) & (arr[..., 2] < 90)
        rough[red] = 30.0
    paint.roughness = (rig.paintable.astype(np.float32), rough)
    paint.logo_roughness = 70.0
    return paint
