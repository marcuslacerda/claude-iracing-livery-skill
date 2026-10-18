"""Cyberpunk neon noir: wet metallic graphite, binary code rain, magenta/cyan neon, roof terminal, nerd stickers; variant=day turns the neon off (Porsche Cup).

neon-noir-2049: dystopian cyberpunk, rainy neon city on wet metal (original art). Dark bluish graphite
body (#0d1117), slightly metallic and wet, easing into deep purple (#5b0a8c) at the tail; binary code
rain (the ASCII bits of `code`, default the brand wordmark) falling down the sides in cyan-green
(#00ffc6), denser from the door back; roof terminal "> init <name>.exe_" with a fake telemetry log;
magenta neon (#ff2bd6) on the belt line and around the hood, cyan neon (#00e5ff) on the lower front
bumper and the wing; hood: brand logo + wordmark as a magenta neon sign (reads from the front), two
katakana columns, printed circuit, geometric eye between the vents; worn nerd stickers on the
front-lower door, under the number (pi, lambda, d20, pad, invader, 42, :wq, sudo, 404); rear bumper
barcode + QR + "REPLICANT UNIT // CUP-992.2"; wing "TEARS IN RAIN // LAP 01"; magenta mirrors and
endplates; windshield banner with the wordmark as a cyan LED display; rain drops and streaks,
scanlines on the roof and engine lid. Spec: body metallic 120 / roughness 40, neon and code max
gloss, stickers matte 180.
variant=day: concrete-grey body, neon off (bare glass tubes), matte. code=<text>: binary of another
text (e.g. car number + date of the first win: code="24 10.08.2026")."""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

from engine.draw import fit, hex2rgb, render_text
from engine.elements import gradient
from engine.elements import lockup
from engine.starters import logo, text

PARAMS = {"variant": "night", "code": "", "katakana": ["ネオンノワール", "サイバーレーサー"], "text": "", "seed": 5}
CAR = "porsche9922cup"
SS = 4

GRAPHITE, PURPLE, CONCRETE = hex2rgb("0d1117"), hex2rgb("5b0a8c"), hex2rgb("8b8d8c")
CODE, MAGENTA, CYAN = hex2rgb("00ffc6"), hex2rgb("ff2bd6"), hex2rgb("00e5ff")
TUBE, TUBE_HI = (96, 102, 108), (190, 196, 202)
MONO = "mono"
JP = "jp"


def fbm(N, rng, scales=(8, 20, 50, 130), weights=(0.4, 0.3, 0.2, 0.1)):
    out = np.zeros((N, N), np.float32)
    for s, w in zip(scales, weights):
        out += w * np.array(Image.fromarray(rng.random((s, s)).astype(np.float32)).resize((N, N), Image.BICUBIC))
    out -= out.min()
    return out / (out.max() + 1e-6)


def mix(a, b, t):
    return tuple(int(x + (y - x) * t) for x, y in zip(a, b))


# ---- neon from a line mask (distance field): hot core + soft glow; or a bare tube in daylight -------
def neon(base, lines, color, region, lit, core=4.0, glow=11.0, strength=0.85):
    dist = ndimage.distance_transform_edt(~lines)
    core_a = np.clip(core / 2 - dist + 0.5, 0, 1) * region
    hot_a = np.clip(core * 0.18 - dist + 0.5, 0, 1) * region
    if lit:
        g = (np.exp(-(dist / glow) ** 2) * strength * region)[..., None]
        base[:] = 255 - (255 - base) * (1 - g * np.array(color, np.float32) / 255)       # screen
        base[:] = base * (1 - core_a[..., None]) + np.array(color, np.float32) * core_a[..., None]
        base[:] = base * (1 - hot_a[..., None]) + np.array(mix(color, (255, 255, 255), 0.65), np.float32) * hot_a[..., None]
    else:
        base[:] = base * (1 - core_a[..., None]) + np.array(TUBE, np.float32) * core_a[..., None]
        base[:] = base * (1 - hot_a[..., None]) + np.array(TUBE_HI, np.float32) * hot_a[..., None]
    return core_a


def line_mask(N, segments, width=1):
    m = Image.new("L", (N, N), 0)
    d = ImageDraw.Draw(m)
    for pts in segments:
        d.line(pts, fill=255, width=width)
    return np.array(m) > 127


def neon_sprite(alpha, color, lit, pad=22, blur=9):
    """Neon sign from a shape's alpha (L image): glow + coloured core + white-hot centre."""
    W, H = alpha.width + 2 * pad, alpha.height + 2 * pad
    a = Image.new("L", (W, H), 0); a.paste(alpha, (pad, pad))
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if lit:
        g = np.array(a.filter(ImageFilter.GaussianBlur(blur))).astype(np.float32) * 0.9
        out = Image.fromarray(np.dstack([np.full((H, W, 3), color, np.uint8), g.clip(0, 255).astype(np.uint8)]), "RGBA")
        col, hot = color, mix(color, (255, 255, 255), 0.7)
    else:
        col, hot = TUBE, TUBE_HI
    core = Image.new("RGBA", (W, H), tuple(col) + (0,)); core.putalpha(a)
    out.alpha_composite(core)
    inner = a.filter(ImageFilter.MinFilter(3))
    h = Image.new("RGBA", (W, H), tuple(hot) + (0,)); h.putalpha(inner.point(lambda v: int(v * 0.85)))
    out.alpha_composite(h)
    return out


def stroke_alpha(w, h, draw_fn):
    big = Image.new("L", (w * SS, h * SS), 0)
    draw_fn(ImageDraw.Draw(big), SS)
    return big.resize((w, h), Image.LANCZOS)


# ---- sprites ------------------------------------------------------------------------------------------
def eye_alpha():
    def f(d, s):
        W, H = 84 * s, 44 * s
        lw = int(3.2 * s)
        top = [(W * t, H / 2 - H * 0.46 * math.sin(math.pi * t)) for t in np.linspace(0, 1, 40)]
        bot = [(W * t, H / 2 + H * 0.46 * math.sin(math.pi * t)) for t in np.linspace(0, 1, 40)]
        d.line(top, fill=255, width=lw, joint="curve"); d.line(bot, fill=255, width=lw, joint="curve")
        for r in (H * 0.32, H * 0.13):
            d.ellipse([W / 2 - r, H / 2 - r, W / 2 + r, H / 2 + r], outline=255, width=lw)
        d.ellipse([W / 2 - 3 * s, H / 2 - 3 * s, W / 2 + 3 * s, H / 2 + 3 * s], fill=255)
    return stroke_alpha(84, 44, f)


def katakana_column(text, size, color, alpha=230):
    rows = [render_text(ch, size, font=JP, color=color) for ch in text]
    W = max(r.width for r in rows); H = sum(r.height for r in rows)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); y = 0
    for r in rows:
        img.alpha_composite(r, ((W - r.width) // 2, y)); y += r.height
    img.putalpha(img.getchannel("A").point(lambda v: v * alpha // 255))
    return img


def terminal(lit, code_bits, user):
    W, H = 430, 440
    bg = (6, 9, 12) if lit else (34, 37, 40)
    fg = CODE if lit else (170, 176, 172)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    big = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    d.rounded_rectangle([0, 0, W * SS - 1, H * SS - 1], radius=14 * SS, fill=(CYAN if lit else TUBE) + (255,))
    d.rounded_rectangle([3 * SS, 3 * SS, (W - 3) * SS, (H - 3) * SS], radius=12 * SS, fill=bg + (255,))
    d.rectangle([3 * SS, 3 * SS, (W - 3) * SS, 38 * SS], fill=((20, 60, 70) if lit else (60, 64, 68)) + (255,))
    img = big.resize((W, H), Image.LANCZOS)
    hdr = render_text(f"tty1  {user}@cup-992:~", 20, font=MONO, color=(CYAN if lit else (200, 204, 206)))
    img.alpha_composite(hdr, (16, 10))
    lines = [f"> init {user}.exe_",
             "[ok] link telemetry ..... 60hz",
             "[ok] tyres  FL 82  FR 85",
             "[ok] tyres  RL 88  RR 87",
             "[!!] fuel 12.4L  stint 03",
             "[ok] S2 delta  -0.214",
             "[..] replicant test  PASS",
             "[ok] " + code_bits[:24],
             "> _"]
    y = 52
    for i, ln in enumerate(lines):
        col = (255, 255, 255) if (i == 0 and lit) else fg
        if ln.startswith("[!!]"):
            col = MAGENTA if lit else (210, 120, 190)
        t = fit(render_text(ln, 21, font=MONO, color=col), W - 32, 30)
        img.alpha_composite(t, (16, y)); y += 41
    a = np.array(img)
    a[::4, :, :3] = (a[::4, :, :3] * 0.72).astype(np.uint8)                    # scanlines
    return Image.fromarray(a, "RGBA")


def worn(img, rng):
    """Sticker wear: chipped edges and scratches (alpha holes), slight tilt."""
    a = np.array(img).astype(np.float32)
    h, w = a.shape[:2]
    n = np.array(Image.fromarray(rng.random((6, 6)).astype(np.float32)).resize((w, h), Image.BICUBIC))
    yy, xx = np.mgrid[0:h, 0:w]
    edge = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy)) / 6.0
    keep = np.clip((n * 1.6 + edge - 0.75) * 4, 0, 1)
    for _ in range(3):
        y0 = rng.uniform(0, h); sl = rng.uniform(-0.6, 0.6)
        keep[np.abs(yy - (y0 + sl * xx)) < 0.8] *= 0.25
    a[..., 3] *= keep
    out = Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA")
    return out.rotate(rng.uniform(-9, 9), expand=True, resample=Image.BICUBIC)


def sticker(kind, rng, size=40):
    BLK, WHT = (14, 14, 16), (240, 240, 236)
    spec = {"pi": ((255, 212, 0), BLK, "π"), "lambda": ((255, 122, 0), BLK, "λ"), "42": (CYAN, BLK, "42"),
            ":wq": (BLK, WHT, ":wq"), "sudo": ((200, 16, 46), WHT, "sudo"), "404": (WHT, BLK, "404"),
            "d20": (WHT, BLK, None), "pad": (MAGENTA, BLK, None), "invader": (BLK, (0, 255, 120), None)}
    bg, fg, txt = spec[kind]
    t = render_text(txt, 22, font=MONO, color=fg) if txt else None
    W = max(size, t.width + 10) if t else size
    big = Image.new("RGBA", (W * SS, size * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    d.rounded_rectangle([0, 0, W * SS - 1, size * SS - 1], radius=8 * SS, fill=tuple(bg) + (255,))
    s = SS
    if kind == "d20":                                                          # icosahedron outline
        c, r = (W * s / 2, size * s / 2), size * s * 0.38
        hexa = [(c[0] + r * math.cos(math.pi / 6 + k * math.pi / 3), c[1] + r * math.sin(math.pi / 6 + k * math.pi / 3)) for k in range(6)]
        d.polygon(hexa, outline=fg + (255,), width=int(2.2 * s))
        tri = [hexa[1], hexa[3], hexa[5]]
        d.polygon(tri, outline=fg + (255,), width=int(2.2 * s))
        for k, j in ((0, 1), (0, 5), (2, 1), (2, 3), (4, 3), (4, 5)):
            d.line([hexa[k], tri[[1, 3, 5].index(j)] if j in (1, 3, 5) else hexa[j]], fill=fg + (255,), width=int(1.6 * s))
    elif kind == "pad":                                                        # retro controller
        d.rounded_rectangle([5 * s, 12 * s, (W - 5) * s, (size - 10) * s], radius=8 * s, fill=fg + (255,))
        cx, cy = 13 * s, size * s / 2 + 1 * s
        d.rectangle([cx - 5 * s, cy - 1.6 * s, cx + 5 * s, cy + 1.6 * s], fill=tuple(bg) + (255,))
        d.rectangle([cx - 1.6 * s, cy - 5 * s, cx + 1.6 * s, cy + 5 * s], fill=tuple(bg) + (255,))
        for bx, by in ((W - 14, size / 2 + 3), (W - 9, size / 2 - 2)):
            d.ellipse([(bx - 2.6) * s, (by - 2.6) * s, (bx + 2.6) * s, (by + 2.6) * s], fill=tuple(bg) + (255,))
    elif kind == "invader":                                                    # 11x8 pixel art
        px = ["00100000100", "00010001000", "00111111100", "01101110110",
              "11111111111", "10111111101", "10100000101", "00011011000"]
        p, ox, oy = 3 * s, (W * s - 11 * 3 * s) / 2, (size * s - 8 * 3 * s) / 2
        for j, row in enumerate(px):
            for i, v in enumerate(row):
                if v == "1":
                    d.rectangle([ox + i * p, oy + j * p, ox + (i + 1) * p - 1, oy + (j + 1) * p - 1], fill=fg + (255,))
    img = big.resize((W, size), Image.LANCZOS)
    if t:
        img.alpha_composite(t, ((W - t.width) // 2, (size - t.height) // 2))
    return worn(img, rng)


def led_text(text, lit, pitch=5, rows=9):
    t = render_text(text, 80, font=MONO, color=(255, 255, 255))
    cols = max(1, round(t.width / t.height * rows))
    g = np.array(t.getchannel("A").resize((cols, rows), Image.BILINEAR)) > 90
    W, H = cols * pitch + 8, rows * pitch + 8
    big = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    on, off = (CYAN if lit else (120, 200, 210)), ((0, 46, 54) if lit else (40, 44, 48))
    r = pitch * 0.38 * SS
    for j in range(rows):
        for i in range(cols):
            cx, cy = (4 + i * pitch + pitch / 2) * SS, (4 + j * pitch + pitch / 2) * SS
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(on if g[j, i] else off) + (255,))
    img = big.resize((W, H), Image.LANCZOS)
    if lit:
        glow = img.getchannel("A").point(lambda v: v)
        lay = Image.new("RGBA", (W, H), CYAN + (0,))
        mask = np.array(img)[..., :3].max(axis=2) > 150
        lay.putalpha(Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3)).point(lambda v: v * 6 // 10))
        out = Image.new("RGBA", (W, H), (0, 0, 0, 0)); out.alpha_composite(img); out.alpha_composite(lay)
        return out
    return img


def barcode(w, h, rng, color):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x = 2
    while x < w - 3:
        bw = int(rng.choice([1, 1, 2, 3]))
        d.rectangle([x, 0, x + bw - 1, h - 1], fill=color + (255,))
        x += bw + int(rng.choice([1, 2, 2, 3]))
    return img


def qr(size, rng, color, n=21):
    m = rng.random((n, n)) < 0.5
    for oy, ox in ((0, 0), (0, n - 7), (n - 7, 0)):                           # finder squares
        m[oy:oy + 7, ox:ox + 7] = False
        m[oy, ox:ox + 7] = m[oy + 6, ox:ox + 7] = m[oy:oy + 7, ox] = m[oy:oy + 7, ox + 6] = True
        m[oy + 2:oy + 5, ox + 2:ox + 5] = True
    img = Image.fromarray(np.where(m[..., None], np.array(color + (255,), np.uint8), np.zeros(4, np.uint8)).astype(np.uint8), "RGBA")
    return img.resize((size, size), Image.NEAREST)


def side_put(rig, paint, sprite, x, h, key):
    s = rig.side(key)
    return rig.put(paint, sprite, (x, rig.side_y(key, h)), 180 if s.car_down_y < 0 else 0, matte=False,
                   clip=rig.masks[s.island].astype(np.float32))


# ---- design -------------------------------------------------------------------------------------------
def design(rig, p=PARAMS):
    lit = not str(p.get("variant", "night")).lower().startswith("day")
    rng = np.random.default_rng(int(p.get("seed", 5)))
    N = rig.N
    paintable = rig.paintable
    bits = "".join(f"{ord(c):08b}" for c in str(p.get("code") or text(p).lstrip("@")))
    sides = rig.sides_mask()
    hh = rig.side_height()

    # body: wet graphite easing into deep purple at the tail (night) / weathered concrete (day)
    if lit:
        tail = mix(GRAPHITE, PURPLE, 0.72)
        base = gradient.two_stop(rig, "#%02x%02x%02x" % GRAPHITE, "#%02x%02x%02x" % tail, 0.55, 1.0)
        n = fbm(N, rng)
        base += ((n - 0.5) * 14)[..., None]
    else:
        base = rig.fill(CONCRETE)
        n, n2 = fbm(N, rng), fbm(N, rng, scales=(60, 150, 300, 600))
        base += ((n - 0.5) * 34 + (n2 - 0.5) * 18)[..., None]
    base = rig.fixups(base)
    metal = np.full((N, N), 120.0 if lit else 20.0, np.float32)
    rough = np.full((N, N), 40.0 if lit else 165.0, np.float32)

    # mirrors + endplates magenta (day: unlit pink acrylic)
    acc = rig.mask(["mirrors", "endplate_l35", "endplate_r38", "endplate_l36", "endplate_r37"])
    base[acc] = MAGENTA if lit else mix(MAGENTA, CONCRETE, 0.45)
    metal[acc], rough[acc] = 0, 6 if lit else 60
    base[rig.mask("banner")] = (6, 7, 9)

    # scanlines on the roof and the engine lid (lines across the car)
    scan = rig.mask(["roof", "engine_lid"]) & ((np.arange(N)[None, :] % 4) == 0)
    base[scan] *= 0.80 if lit else 0.88

    # printed circuit on the hood, under everything
    hood = rig.mask("hood")
    segs = []
    for _ in range(26):
        x, y = rng.uniform(380, 700), rng.uniform(1090, 1580)
        pts = [(x, y)]
        for _ in range(int(rng.integers(3, 7))):
            dx, dy = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)][int(rng.integers(0, 8))]
            L = rng.uniform(18, 60)
            x, y = x + dx * L, y + dy * L
            pts.append((x, y))
        segs.append(pts)
    trace = Image.new("L", (N, N), 0); dt = ImageDraw.Draw(trace)
    for pts in segs:
        dt.line(pts, fill=255, width=2, joint="curve")
        ex, ey = pts[-1]
        dt.ellipse([ex - 4, ey - 4, ex + 4, ey + 4], outline=255, width=2)
    ta = (np.array(trace).astype(np.float32) / 255 * hood)[..., None] * (0.30 if lit else 0.45)
    tcol = np.array(CYAN if lit else (52, 56, 60), np.float32)
    base[:] = base * (1 - ta) + tcol * ta

    # rain: drops everywhere, streaks running down the sides
    drops = Image.new("RGBA", (N, N), (0, 0, 0, 0)); dd = ImageDraw.Draw(drops)
    lightc = (150, 175, 200) if lit else (210, 212, 210)
    ys, xs = np.nonzero(paintable)
    pick = rng.choice(len(xs), 3200, replace=False)
    for k in pick:
        x, y = int(xs[k]), int(ys[k]); r = rng.uniform(1.2, 3.6)
        dd.ellipse([x - r, y - r, x + r, y + r], fill=lightc + (int(rng.uniform(40, 90)),))
        dd.ellipse([x - r * 0.6, y - r * 0.6, x - r * 0.1, y - r * 0.1], fill=(255, 255, 255, 140))
        if sides[y, x] and rng.random() < 0.35:
            down = 1 if rig.masks["side_l"][y, x] else -1
            L = rng.uniform(20, 110)
            dd.line([(x, y), (x + rng.uniform(-2, 2), y + down * L)], fill=lightc + (int(rng.uniform(18, 40)),), width=1)
    da = np.array(drops).astype(np.float32)
    a = (da[..., 3:4] / 255) * paintable[..., None]
    base[:] = base * (1 - a) + da[..., :3] * a
    rough = np.where(a[..., 0] > 0.15, 8.0, rough)

    # binary code rain on the sides, denser from the door back (none over the number / stickers)
    code = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    f = 20
    glyph = {}
    for ch in "01":
        for head in (False, True):
            col = (230, 255, 248) if head else (CODE if lit else (24, 120, 100))
            g = render_text(ch, f, font=MONO, color=col)
            glyph[(ch, head, 1)] = g
            glyph[(ch, head, -1)] = g.rotate(180)
    pos = 0
    for key in rig.spec.sides:
        s = rig.side(key)
        for x in range(1010, 1830, 20):
            if rng.random() > 0.22 + 0.62 * (x - 1010) / 820:
                continue
            n_ch = int(rng.integers(5, 19))
            h_top = rng.uniform(0.35, 0.98)
            col_alpha = rng.uniform(0.35, 1.0)
            for i in range(n_ch):
                hc = h_top - i * 24 / 516
                if hc < 0.03:
                    break
                ch = bits[pos % len(bits)]; pos += 1
                head = i == n_ch - 1
                g = glyph[(ch, head, -s.car_down_y if s.car_down_y < 0 else 1)]
                fade = (0.25 + 0.75 * (i + 1) / n_ch) * col_alpha
                g2 = g.copy(); g2.putalpha(g.getchannel("A").point(lambda v, fa=fade: int(v * fa)))
                y = rig.side_y(key, hc)
                code.alpha_composite(g2, (int(x - g.width / 2), int(y - g.height / 2)))
    ca = np.array(code).astype(np.float32)
    a = (ca[..., 3] / 255) * sides
    if lit:
        glow = ndimage.gaussian_filter(a, 3) * 0.5
        base[:] = 255 - (255 - base) * (1 - glow[..., None] * np.array(CODE, np.float32) / 255)
    base[:] = base * (1 - a[..., None]) + ca[..., :3] * a[..., None]
    metal = np.where(a > 0.2, 0.0, metal); rough = np.where(a > 0.2, 5.0, rough)

    # neon tubes
    neon_cores = np.zeros((N, N), np.float32)
    belt = line_mask(N, [[(330, rig.side_y(k, 0.645)), (1800, rig.side_y(k, 0.645))] for k in rig.spec.sides], 1)
    neon_cores = np.maximum(neon_cores, neon(base, belt, MAGENTA, sides.astype(np.float32), lit))
    hood_full = ndimage.binary_fill_holes(hood)
    din = ndimage.distance_transform_edt(hood_full)
    ring = (din > 16.5) & (din <= 17.5)
    neon_cores = np.maximum(neon_cores, neon(base, ring, MAGENTA, hood.astype(np.float32), lit))
    front = line_mask(N, [[(146, 845), (146, 1825)]], 1)
    neon_cores = np.maximum(neon_cores, neon(base, front, CYAN, rig.mask("bumper_front_low").astype(np.float32), lit))
    wing = rig.mask("wing")
    wl = line_mask(N, [[(1280, 158), (1990, 158)], [(1280, 252), (1990, 252)]], 1)
    neon_cores = np.maximum(neon_cores, neon(base, wl, CYAN, wing.astype(np.float32), lit, core=3.5, glow=8))
    metal = np.where(neon_cores > 0.3, 0.0, metal); rough = np.where(neon_cores > 0.3, 4.0, rough)

    paint = rig.to_canvas(base)
    glossy = np.zeros((N, N), np.float32)
    matte = np.zeros((N, N), np.float32)

    # hood: brand neon sign, katakana columns, geometric eye between the vents
    mark = logo(120)
    lock = (lockup.horizontal(mark, text(p), 120) if mark is not None else render_text(text(p), 120)).getchannel("A")
    sign = neon_sprite(lock, MAGENTA, lit)
    glossy = np.maximum(glossy, rig.place("hood", paint, sign, max=(340, 110), dx=17, matte=False))
    jcol = CYAN if lit else (58, 62, 66)
    for text_, y in zip((list(p.get("katakana") or PARAMS["katakana"]) * 2)[:2], (1150, 1522)):
        col = katakana_column(text_, 24, jcol, 210 if lit else 240)
        glossy = np.maximum(glossy, rig.put(paint, col, (590, y), -90, matte=False, clip=hood.astype(np.float32)))
    glossy = np.maximum(glossy, rig.put(paint, neon_sprite(eye_alpha(), CYAN, lit, pad=10, blur=5), (452, 1335), -90,
                                        matte=False, clip=hood.astype(np.float32)))

    # roof terminal, wing text, LED banner
    glossy = np.maximum(glossy, rig.place("roof", paint, terminal(lit, bits, text(p).lstrip("@").lower()), max=(430, 440), matte=False))
    wt = render_text("TEARS IN RAIN // LAP 01", 26, font=MONO, color=(CYAN if lit else (40, 44, 48)))
    if lit:
        wt = neon_sprite(wt.getchannel("A"), CYAN, True, pad=8, blur=4)
    glossy = np.maximum(glossy, rig.place("wing_centre", paint, wt, max=(284, 60), matte=False))
    rig.put(paint, fit(led_text(text(p), lit), 460, 50), (933, 1336), -90, matte=False,
            clip=rig.mask("banner").astype(np.float32))

    # stickers: a cluster on the front-lower door, ahead of and under the number (laid out by width)
    for key in rig.spec.sides:
        order = rng.permutation(len(kinds := ["pi", "lambda", "d20", "pad", "invader", "42", ":wq", "sudo", "404"]))
        x, h = 742, 0.195
        for k in order:
            st = sticker(kinds[k], rng, 36)
            if x + st.width > 1060:
                x, h = 742, 0.105
            matte = np.maximum(matte, side_put(rig, paint, st, x + st.width / 2, h, key))
            x += st.width + 4

    # rear bumper: barcode, decorative QR, unit label
    rb = rig.mask("bumper_rear").astype(np.float32)
    dcol = (225, 228, 232) if lit else (24, 26, 28)
    for spr, c in ((render_text("REPLICANT UNIT // CUP-992.2", 24, font=MONO, color=dcol), (631, 92)),
                   (barcode(150, 40, rng, dcol), (420, 140)), (qr(46, rng, dcol), (845, 140))):
        matte = np.maximum(matte, rig.put(paint, spr, c, 0, matte=False, clip=rb))

    # spec: wet metal body, max-gloss neon/code/LED, matte stickers and decals
    rough = np.where(glossy > 0.3, 6.0 if lit else 40.0, rough)
    metal = np.where(glossy > 0.3, 0.0, metal)
    rough = np.where(matte > 0.3, 180.0, rough)
    metal = np.where(matte > 0.3, 0.0, metal)
    paint.metallic = (paintable.astype(np.float32), metal)
    paint.roughness = (paintable.astype(np.float32), rough)
    paint.logo_roughness = 40.0
    return paint
