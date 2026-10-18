"""UV islands as calibration artefacts: islands.json + the numbered map, and the "islandtest" paint
(every island in its own flat colour with its number stamped on it). An in-sim screenshot of the
islandtest paint is how a car's panel map gets confirmed - never trust where an island sits on the
template to know where it lands on the car.
"""
from __future__ import annotations

import colorsys
import json
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

from . import fonts
from .spec import spec_map
from .template import Template
from .tga import save_tga


def compute(T: Template) -> dict[int, dict]:
    """id -> {bbox, area, label_xy} in template pixels (label_xy = a point safely inside the island)."""
    ids = T.ids
    info: dict[int, dict] = {}
    for new in range(1, int(ids.max()) + 1):
        m = ids == new
        ys, xs = np.nonzero(m)
        if xs.size == 0:
            continue
        cy, cx = ndimage.center_of_mass(m)
        if not m[int(cy), int(cx)]:                          # concave shape: use the deepest point
            d = ndimage.distance_transform_edt(m)
            cy, cx = np.unravel_index(np.argmax(d), d.shape)
        info[new] = dict(bbox=[int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
                         area=int(m.sum()), label_xy=[int(cx), int(cy)])
    return info


def map_colour(i: int) -> tuple[int, int, int]:
    h = (i * 0.618033) % 1.0
    r, g, b = colorsys.hsv_to_rgb(h, 0.65 if i % 2 else 0.9, 0.95 if i % 3 else 0.6)
    return int(r * 255), int(g * 255), int(b * 255)


def test_colour(i: int) -> tuple[int, int, int]:
    """Spread hues, alternate saturation/value so neighbouring numbers never look alike."""
    h = (i * 0.618033988) % 1.0
    s = [1.0, 0.55, 0.85][i % 3]
    v = [0.95, 0.75, 1.0][(i // 3) % 3]
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return int(r * 255), int(g * 255), int(b * 255)


def _stamp_numbers(img: Image.Image, info: dict, size: int):
    d = ImageDraw.Draw(img)
    f = fonts.font("ui", size)
    for new, v in info.items():
        x, y = v["label_xy"]
        t = str(new)
        bb = d.textbbox((x, y), t, font=f, anchor="mm")
        d.rectangle([bb[0] - 6, bb[1] - 4, bb[2] + 6, bb[3] + 4], fill=(0, 0, 0))
        d.text((x, y), t, font=f, fill=(255, 255, 255), anchor="mm")


def write_map(T: Template, info: dict, out_dir: Path, downscale: int | None = None) -> dict[str, Path]:
    """islands.json + islands_map.png (numbers and colours over the wireframe, for humans and Claude)."""
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    ids = T.ids
    H, W = ids.shape
    calib = np.full((H, W, 3), 40, np.uint8)
    for new in info:
        calib[ids == new] = map_colour(new)
    wire = T.layer("wire")
    over = Image.fromarray(np.dstack([calib, np.where(ids > 0, 150, 0).astype(np.uint8)]), "RGBA")
    base = Image.new("RGBA", (W, H), (235, 235, 235, 255))
    m = Image.alpha_composite(Image.alpha_composite(base, over), wire).convert("RGB")
    _stamp_numbers(m, info, 34)
    paths = {"map": out_dir / "islands_map.png", "json": out_dir / "islands.json"}
    m.save(paths["map"])
    if downscale:
        paths["map_small"] = out_dir / f"islands_map_{downscale}.png"
        m.resize((downscale, downscale), Image.LANCZOS).save(paths["map_small"])
    paths["json"].write_text(json.dumps(info, indent=1), encoding="utf-8", newline="\n")
    return paths


def load_info(json_path) -> dict[int, dict]:
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    return {int(k): v for k, v in data.items()}


def panel_names(panels_md) -> dict[int, str]:
    """Island number -> panel name from the first two columns of panels.md (ranges like 35-40 allowed)."""
    names: dict[int, str] = {}
    if not panels_md or not Path(panels_md).exists():
        return names
    for line in Path(panels_md).read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2 or not re.match(r"^\d", cells[0]):
            continue
        nums: set[int] = set()
        for a, b in re.findall(r"(\d+)\s*[–-]\s*(\d+)", cells[0]):
            nums.update(range(int(a), int(b) + 1))
        for mm in re.findall(r"\d+", re.sub(r"\d+\s*[–-]\s*\d+", "", cells[0])):
            nums.add(int(mm))
        name = cells[1].replace("**", "").strip()
        if not name:
            continue
        for k in nums:
            names.setdefault(k, name)
    return names


def islandtest(T: Template, out_dir: Path, cid: str, names: dict[int, str] | None = None,
               title: str = "islandtest") -> dict:
    """The calibration paint: car_<cid>.tga (flat colour + number per island), the template's default
    spec map, legend.png (colour, number, name from panels.md) and preview_wire.png."""
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    names = names or {}
    ids = T.ids
    n = int(ids.max())
    paint = np.full((T.size, T.size, 3), 40, np.uint8)
    cols = {}
    for i in range(1, n + 1):
        cols[i] = test_colour(i)
        paint[ids == i] = cols[i]
    img = Image.fromarray(paint, "RGB")
    d = ImageDraw.Draw(img)
    for i in range(1, n + 1):
        m = ids == i
        if not m.any():
            continue
        dist = ndimage.distance_transform_edt(m)
        cy, cx = np.unravel_index(np.argmax(dist), dist.shape)   # deepest point of the island
        size = int(np.clip(dist.max() * 1.3, 28, 150))           # as big as the island allows
        f = fonts.font("ui_bold", size)
        t = str(i)
        bb = d.textbbox((cx, cy), t, font=f, anchor="mm")
        d.rectangle([bb[0] - 4, bb[1] - 2, bb[2] + 4, bb[3] + 2], fill=(0, 0, 0))
        d.text((cx, cy), t, font=f, fill=(255, 255, 255), anchor="mm")

    paths: dict = {"paint": out_dir / f"car_{cid}.tga", "spec": out_dir / f"car_spec_{cid}.tga",
                   "legend": out_dir / "legend.png", "preview": out_dir / "preview_wire.png"}
    save_tga(img, paths["paint"])
    save_tga(spec_map(T), paths["spec"], alpha=True)
    T.wire_overlay(img).save(paths["preview"])

    rowh, W = 34, 760
    leg = Image.new("RGB", (W, rowh * (n + 1) + 20), (24, 24, 24))
    ld = ImageDraw.Draw(leg)
    f = fonts.font("ui", 20); fb = fonts.font("ui_bold", 20)
    ld.text((12, 8), f"islandtest — {title}", font=fb, fill=(230, 230, 230))
    for i in range(1, n + 1):
        y = 10 + i * rowh
        ld.rectangle([12, y + 4, 52, y + rowh - 4], fill=cols[i])
        ld.text((64, y + 6), f"{i:>2}", font=fb, fill=(255, 255, 255))
        ld.text((100, y + 6), names.get(i, "(unnamed in panels.md)"), font=f, fill=(220, 220, 220))
    leg.save(paths["legend"])
    paths["count"] = n
    return paths
