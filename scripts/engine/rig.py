"""The rig: WHERE things are on one car's template, loaded from `cars/<car>/car.toml`.

Designs only say WHAT to draw; they talk to the rig through a small vocabulary of named zones
(`hood`, `roof`, `doors`, `doors_low`, `wing_centre`, `wing_ends`, `quarters`, `front_bumper` ...)
and side helpers (bands and polylines in car coordinates: x along the car, h = height fraction from
the sill (0) to the belt line (1)). Every number in car.toml is sim-verified or marked otherwise in
the car's panels.md.

    rig = Rig(CarSpec.load(car_dir / "car.toml"), Template(layers_dir))
    paint = rig.to_canvas(rig.fixups(rig.fill((20, 20, 24))))
    rig.place("hood", paint, logo_sprite)
    rig.export(paint, out_dir, customer_id)
"""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image

from .draw import fit as _fit
from .draw import place as _place
from .spec import spec_map
from .template import Template
from .tga import save_tga


class CalibrationError(RuntimeError):
    pass


@dataclass
class Island:
    name: str
    id: int | None
    seed: tuple[int, int]
    clip: tuple[int, int, int, int] | None = None


@dataclass
class Zone:
    name: str
    centre: tuple[float, float]
    rotate: float = 0.0
    max: tuple[int, int] | None = None
    car_down_y: int = 1            # +1 if "down on the car" is +y on the template, -1 if the island is upside down
    island: str | None = None
    note: str = ""


@dataclass
class Side:
    key: str
    island: str
    sill: float
    belt: float
    louver: str | None = None
    car_down_y: int = 1


@dataclass
class Paint:
    """A paint in progress: the RGBA canvas plus what the spec map needs to know about it."""
    canvas: Image.Image
    matte: np.ndarray                       # float HxW: where logos were placed (gets `logo_roughness`)
    roughness: tuple | None = None          # (float mask, float HxW roughness values) for the body
    logo_roughness: float = 200.0           # G value under the logo mask (33 = glossy, 200 = matte)
    notes: list[str] = field(default_factory=list)

    @property
    def size(self):
        return self.canvas.size


class CarSpec:
    def __init__(self, data: dict, path: Path | None = None):
        self.data = data
        self.path = Path(path) if path else None
        car = data.get("car", {})
        self.slug: str = car.get("slug") or (self.path.parent.name if self.path else "car")
        self.car_path: str = car.get("car_path", self.slug)
        self.car_id = car.get("car_id")
        self.name: str = car.get("name", self.slug)
        self.template_psd: str | None = car.get("template_psd")
        self.min_island_area: int = int(car.get("min_island_area", 6000))
        self.size: int = int(car.get("size", 2048))
        axes = data.get("axes", {})
        self.length: tuple[int, int] = tuple(axes.get("length", (0, self.size)))
        self.centre_y: int = int(axes.get("centre_y", self.size // 2))
        self.islands: dict[str, Island] = {
            k: Island(k, v.get("id"), tuple(v["seed"]), tuple(v["clip"]) if v.get("clip") else None)
            for k, v in data.get("islands", {}).items()}
        self.groups: dict[str, list[str]] = {k: list(v) for k, v in data.get("groups", {}).items()}
        self.fixups: list[dict] = list(data.get("fixups", []))
        sides = data.get("sides", {})
        self.sides: dict[str, Side] = {}
        for key, v in sides.items():
            if isinstance(v, dict):
                self.sides[key] = Side(key, v["island"], float(v["sill"]), float(v["belt"]),
                                       v.get("louver"), int(v.get("car_down_y", 1 if v["sill"] > v["belt"] else -1)))
        self.sides_x_range: tuple[int, int] = tuple(sides.get("x_range", (0, self.size)))
        self.louver_offset: tuple[int, int] = tuple(sides.get("louver_offset", (0, 0)))
        self.zones: dict[str, Zone] = {
            k: Zone(k, tuple(v["centre"]), float(v.get("rotate", 0)), tuple(v["max"]) if v.get("max") else None,
                    int(v.get("car_down_y", 1)), v.get("island"), v.get("note", ""))
            for k, v in data.get("zones", {}).items()}
        self.pairs: dict[str, list[str]] = {k: list(v) for k, v in data.get("pairs", {}).items()}
        self.preview_crops: dict[str, tuple] = {k: tuple(v) for k, v in data.get("preview_crops", {}).items()}

    @classmethod
    def load(cls, path) -> "CarSpec":
        path = Path(path)
        if path.is_dir():
            path = path / "car.toml"
        with open(path, "rb") as f:
            return cls(tomllib.load(f), path)

    def section(self, name: str) -> dict | None:
        """Extra calibration sections used by elements (e.g. `mouth`, `bumper_rear`)."""
        return self.data.get(name)

    @property
    def status(self) -> str:
        if self.zones:
            return "calibrated"
        if self.islands:
            return "islands"
        return "stub"

    @property
    def dir(self) -> Path | None:
        return self.path.parent if self.path else None


class Rig:
    def __init__(self, spec: CarSpec, template: Template):
        self.spec = spec
        self.T = template
        self.N = template.size
        self.paintable = template.paintable
        self.centre_y = spec.centre_y
        self.masks: dict[str, np.ndarray] = {}
        problems = []
        for name, isl in spec.islands.items():
            sx, sy = isl.seed
            found = template.island_id(sx, sy)
            if found == 0:
                problems.append(f"{name}: seed {isl.seed} is not inside a paintable island")
                continue
            if isl.id is not None and found != isl.id:
                problems.append(f"{name}: seed {isl.seed} lands on island {found}, car.toml says {isl.id}")
                continue
            m = template.ids == found
            if isl.clip:
                x0, y0, x1, y1 = isl.clip
                box = np.zeros_like(m)
                box[y0:y1 + 1, x0:x1 + 1] = True
                m = m & box
            self.masks[name] = m
        if problems:
            raise CalibrationError(
                "island numbering does not match car.toml (template changed? wrong min_island_area?):\n  "
                + "\n  ".join(problems)
                + "\nRe-run `paint.py prepare --car <car>` and re-check panels.md / car.toml.")

    # ---- islands and groups ---------------------------------------------------------------------
    def islands(self, name_or_group) -> list[str]:
        """Resolve an island name, a group name or a list of either into island names."""
        if isinstance(name_or_group, (list, tuple)):
            return [n for item in name_or_group for n in self.islands(item)]
        if name_or_group in self.spec.groups:
            return list(self.spec.groups[name_or_group])
        if name_or_group in self.masks:
            return [name_or_group]
        raise KeyError(f"unknown island or group {name_or_group!r} for {self.spec.slug}; "
                       f"known: {', '.join(self.masks)}")

    def mask(self, name_or_group) -> np.ndarray:
        m = np.zeros((self.N, self.N), bool)
        for n in self.islands(name_or_group):
            m |= self.masks[n]
        return m

    # ---- base colour --------------------------------------------------------------------------
    def fill(self, color) -> np.ndarray:
        """Flat RGB float base."""
        base = np.empty((self.N, self.N, 3), np.float32)
        base[...] = np.array(color, np.float32)
        return base

    def fill_by_length(self, color_fn) -> np.ndarray:
        """RGB float base where colour depends only on car-length x (nose..tail). color_fn(t in 0..1) -> rgb."""
        x0, x1 = self.spec.length
        t = np.clip((np.arange(self.N) - x0) / (x1 - x0), 0, 1)
        row = np.array([color_fn(v) for v in t], np.float32)
        return np.repeat(row[None, :, :], self.N, axis=0)

    def fixups(self, base: np.ndarray) -> np.ndarray:
        """Islands whose UV position lies about where they are on the car get the colour sampled
        elsewhere (car.toml [[fixups]]: targets = island/group, sample = [x, y]). In place."""
        samples = [(fx, base[fx["sample"][1], fx["sample"][0]].copy()) for fx in self.spec.fixups]
        for fx, colour in samples:
            for k in self.islands(fx["targets"]):
                base[self.masks[k]] = colour
        return base

    def to_canvas(self, base: np.ndarray) -> Paint:
        canvas = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
        return Paint(canvas=canvas, matte=np.zeros((self.N, self.N), np.float32))

    # ---- zones --------------------------------------------------------------------------------
    def has_zone(self, name: str) -> bool:
        return name in self.spec.zones or name in self.spec.pairs

    def zones_for(self, name: str) -> list[Zone]:
        if name in self.spec.pairs:
            return [self.spec.zones[z] for z in self.spec.pairs[name]]
        if name in self.spec.zones:
            return [self.spec.zones[name]]
        raise KeyError(f"{self.spec.slug} has no zone {name!r}; known: "
                       f"{', '.join(list(self.spec.zones) + list(self.spec.pairs))}")

    def zone(self, name: str) -> Zone:
        return self.zones_for(name)[0]

    def put(self, paint: Paint, sprite: Image.Image, centre, rotate=0, matte=True, clip=None) -> np.ndarray:
        """Raw placement at a template pixel (clipped to the paintable area)."""
        a = _place(paint.canvas, sprite, centre, rotate=rotate, clip=self.paintable if clip is None else clip)
        if matte:
            paint.matte = np.maximum(paint.matte, a)
        return a

    def place(self, zone: str, paint: Paint, sprite: Image.Image, *, fit=True, max=None, dx=0, dy=0,
              matte=True, rotate=None) -> np.ndarray:
        """Place a sprite in a zone (or in every zone of a pair). `fit` scales it into the zone's
        `max` box (or `max=(w, h)` given here); dx/dy shift it along the car / down the car in px."""
        total = np.zeros((self.N, self.N), np.float32)
        for z in self.zones_for(zone):
            spr = sprite
            box = max or z.max
            if fit and box:
                spr = _fit(sprite, box[0], box[1])
            centre = (z.centre[0] + dx, z.centre[1] + z.car_down_y * dy)
            total = np.maximum(total, self.put(paint, spr, centre, z.rotate if rotate is None else rotate, matte))
        return total

    # ---- sides (car coordinates: x along the car, h = 0 sill .. 1 belt) -------------------------
    def side(self, key: str) -> Side:
        try:
            return self.spec.sides[key]
        except KeyError:
            raise KeyError(f"{self.spec.slug} has no side {key!r} (car.toml [sides.R] / [sides.L])")

    def side_y(self, side: str, h: float) -> float:
        s = self.side(side)
        return s.sill + (s.belt - s.sill) * h

    def side_height(self) -> np.ndarray:
        """float array: height fraction (0 sill .. 1 belt) for pixels of the side islands, 0 elsewhere."""
        yy = np.arange(self.N)[:, None].astype(np.float32)
        out = np.zeros((self.N, self.N), np.float32)
        for s in self.spec.sides.values():
            h = np.clip((yy - s.sill) / (s.belt - s.sill), 0, 1)
            out[self.masks[s.island]] = np.broadcast_to(h, (self.N, self.N))[self.masks[s.island]]
        return out

    def sides_mask(self) -> np.ndarray:
        m = np.zeros((self.N, self.N), bool)
        for s in self.spec.sides.values():
            m |= self.masks[s.island]
        return m

    def side_band(self, base: np.ndarray, color, h0: float, h1: float, x0=None, x1=None) -> np.ndarray:
        """Paint a longitudinal band between height fractions h0..h1 on both sides (in place, float base)."""
        hh = self.side_height()
        xr = self.spec.sides_x_range
        x0 = xr[0] if x0 is None else x0
        x1 = xr[1] if x1 is None else x1
        xx = np.arange(self.N)[None, :]
        for s in self.spec.sides.values():
            m = self.masks[s.island] & (hh >= h0) & (hh <= h1)
            m &= (xx >= x0) & (xx <= x1)
            base[m] = color
        return base

    def side_polyline(self, img: Image.Image, pts_h, color, width, side: str, ss=4):
        """Draw a stroke given as [(x, h), ...] in car coords on one side island (RGBA image, in place).
        Drawn as a polygon band at ss x resolution (no joint spikes, anti-aliased edges). Also clipped
        onto that side's fender-louver island, shifted by the car's louver_offset."""
        s = self.side(side)
        N = self.N
        pts = [(x, self.side_y(side, h)) for x, h in pts_h]
        if len(pts) == 2:                                                      # straight: densify for the normals
            (xa, ya), (xb, yb) = pts
            pts = [(xa + (xb - xa) * t, ya + (yb - ya) * t) for t in np.linspace(0, 1, 8)]
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        bx0, by0 = int(min(xs) - width - 2), int(min(ys) - width - 2)
        bx1, by1 = int(max(xs) + width + 2), int(max(ys) + width + 2)
        big = Image.new("RGBA", ((bx1 - bx0) * ss, (by1 - by0) * ss), (0, 0, 0, 0))
        from PIL import ImageDraw
        d = ImageDraw.Draw(big)
        col = tuple(color) + (255,)
        for (xa, ya), (xb, yb) in zip(pts[:-1], pts[1:]):
            dx, dy = xb - xa, yb - ya
            L = (dx * dx + dy * dy) ** 0.5 or 1.0
            nx, ny = -dy / L * width / 2, dx / L * width / 2
            quad = [(xa + nx, ya + ny), (xb + nx, yb + ny), (xb - nx, yb - ny), (xa - nx, ya - ny)]
            d.polygon([((x - bx0) * ss, (y - by0) * ss) for x, y in quad], fill=col)
        for p in pts:
            d.ellipse([(p[0] - bx0 - width / 2) * ss, (p[1] - by0 - width / 2) * ss,
                       (p[0] - bx0 + width / 2) * ss, (p[1] - by0 + width / 2) * ss], fill=col)
        layer = Image.new("RGBA", (N, N), (0, 0, 0, 0))
        layer.alpha_composite(big.resize((bx1 - bx0, by1 - by0), Image.LANCZOS), (bx0, by0))
        a = np.array(layer)[..., 3] * self.masks[s.island]
        if s.louver and s.louver in self.masks:
            dx, dy = self.spec.louver_offset
            shifted = layer.transform(layer.size, Image.AFFINE, (1, 0, -dx, 0, 1, -(dy * s.car_down_y)))
            a_louver = np.array(shifted)[..., 3] * self.masks[s.louver]
            rgb = np.where((a_louver > 0)[..., None], np.array(shifted)[..., :3], np.array(layer)[..., :3])
            a = np.maximum(a, a_louver)
        else:
            rgb = np.array(layer)[..., :3]
        layer = Image.fromarray(np.dstack([rgb, np.zeros_like(a)]).astype(np.uint8), "RGBA")
        layer.putalpha(Image.fromarray(a.astype(np.uint8)))
        img.alpha_composite(layer)

    def sills(self, paint: Paint, sprite: Image.Image, x_centre=None, h=0.10, matte=False):
        """A strip along the rocker panel of both sides (h = height fraction above the sill)."""
        xr = self.spec.sides_x_range
        x_centre = (xr[0] + xr[1]) // 2 if x_centre is None else x_centre
        for key, s in self.spec.sides.items():
            rot = 180 if s.car_down_y < 0 else 0
            self.put(paint, sprite, (x_centre, self.side_y(key, h)), rot, matte)

    # ---- export -------------------------------------------------------------------------------
    def export(self, paint: Paint, out_dir, cid, deploy=None, crops=None) -> dict:
        out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
        rgb = paint.canvas.convert("RGB")
        files = {"paint": out / f"car_{cid}.tga", "spec": out / f"car_spec_{cid}.tga",
                 "png": out / "car.png", "wire": out / "preview_wire.png"}
        save_tga(rgb, files["paint"])
        spec = spec_map(self.T, roughness_override=(paint.matte, paint.logo_roughness), roughness_map=paint.roughness)
        save_tga(spec, files["spec"], alpha=True)
        rgb.save(files["png"])
        self.T.wire_overlay(rgb).save(files["wire"])
        for name, box in (crops or self.spec.preview_crops).items():
            files[f"preview_{name}"] = out / f"preview_{name}.png"
            rgb.crop(box).save(files[f"preview_{name}"])
        if deploy:
            deploy = Path(deploy); deploy.mkdir(parents=True, exist_ok=True)
            for key in ("paint", "spec"):
                (deploy / files[key].name).write_bytes(files[key].read_bytes())
            files["deployed_to"] = deploy
        return files
