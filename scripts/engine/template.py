"""The exported template layers of one car and its UV islands.

Layers are resolved by ROLE (case-insensitive substrings of the file name), not by the exact name
iRacing gave them, so templates with slightly different layer naming still work. Run
`paint.py prepare` to export them from the PSD; `layers.txt` next to them lists what was found.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROLES: dict[str, list[list[str]]] = {
    # each role: a list of alternatives; an alternative is a list of substrings that must ALL match
    "mask": [["mask"]],
    "wire": [["wire"]],
    "spec_r_base": [["red_channel", "base_paint"], ["metallic", "base"]],
    "spec_g_base": [["green_channel", "base_paint"], ["roughness", "base"]],
    "spec_b_base": [["blue_channel", "base_paint"], ["clearcoat", "base"]],
    "spec_r_parts": [["red_channel", "parts"], ["metallic", "parts"]],
    "spec_g_parts": [["green_channel", "parts"], ["roughness", "parts"]],
    "spec_b_parts": [["blue_channel", "parts"], ["clearcoat", "parts"]],
    "spec_alpha": [["spec_alpha"], ["spec", "alpha"]],
    "sponsor_blocks": [["sponsor_block"]],
    "number_blocks": [["number_block"]],
    "mandatory": [["mandatory"]],
    "base": [["paintable_area_base"], ["main_car_body"]],
}


class LayerNotFound(FileNotFoundError):
    pass


class Template:
    def __init__(self, layers_dir, min_island_area: int = 6000, cache: bool = True):
        self.dir = Path(layers_dir)
        if not self.dir.is_dir():
            raise LayerNotFound(f"no exported layers in {self.dir} (run: paint.py prepare --car <car>)")
        self.min_island_area = int(min_island_area)
        self._files = sorted(p for p in self.dir.glob("*.png"))
        mask = np.array(Image.open(self.path("mask")))
        self.paintable = mask[..., 3] < 128           # the Mask layer is opaque over the non-paintable area
        self.size = int(mask.shape[0])
        self.ids = self._load_or_compute_ids(cache)

    # ---- layer resolution -----------------------------------------------------------------------
    def resolve(self, role: str) -> Path | None:
        if (self.dir / f"{role}.png").exists():       # an exact file name still works
            return self.dir / f"{role}.png"
        for alternative in ROLES.get(role, [[role]]):
            hits = [p for p in self._files if all(s.lower() in p.name.lower() for s in alternative)]
            if hits:
                return sorted(hits, key=lambda p: len(p.name))[0]
        return None

    def path(self, role: str) -> Path:
        p = self.resolve(role)
        if p is None:
            names = ", ".join(f.name for f in self._files) or "(none)"
            raise LayerNotFound(f"no layer for role {role!r} in {self.dir}; have: {names}")
        return p

    def has(self, role: str) -> bool:
        return self.resolve(role) is not None

    def layer(self, role: str) -> Image.Image:
        return Image.open(self.path(role)).convert("RGBA")

    def manifest(self) -> dict:
        out = {}
        for role in ROLES:
            p = self.resolve(role)
            out[role] = p.name if p else None
        return out

    # ---- islands ----------------------------------------------------------------------------------
    def _cache_key(self) -> str:
        h = hashlib.sha1()
        for role in ("mask", "wire"):
            p = self.path(role)
            st = p.stat()
            h.update(f"{p.name}:{st.st_size}:{st.st_mtime_ns}".encode())
        h.update(str(self.min_island_area).encode())
        return h.hexdigest()[:16]

    def _load_or_compute_ids(self, cache: bool) -> np.ndarray:
        cache_file = self.dir / f".islands-{self.min_island_area}.npz"
        key = self._cache_key()
        if cache and cache_file.exists():
            try:
                z = np.load(cache_file)
                if str(z["key"]) == key:
                    return z["ids"]
            except Exception:
                pass
        ids = compute_island_ids(self.paintable, np.array(Image.open(self.path("wire"))), self.min_island_area)
        if cache:
            try:
                np.savez_compressed(cache_file, ids=ids, key=np.array(key))
            except OSError:
                pass
        return ids

    def island_mask(self, x: int, y: int) -> np.ndarray:
        """Boolean mask of the UV island containing template pixel (x, y)."""
        i = self.ids[y, x]
        if i == 0:
            raise ValueError(f"({x},{y}) is not inside a paintable island")
        return self.ids == i

    def island_id(self, x: int, y: int) -> int:
        return int(self.ids[y, x])

    def wire_overlay(self, rgb_img: Image.Image, scale: int = 1500) -> Image.Image:
        """Downscaled preview of a paint with the wireframe on top."""
        out = Image.alpha_composite(rgb_img.convert("RGBA"), self.layer("wire"))
        return out.convert("RGB").resize((scale, scale), Image.LANCZOS)


def compute_island_ids(paintable: np.ndarray, wire: np.ndarray, min_area: int) -> np.ndarray:
    """Label the paintable area into UV islands. The Wire layer draws island outlines in pure green:
    those pixels are separators. Small components (< min_area) are merged into their nearest big one.
    Islands are numbered by decreasing area (1 = biggest). ONE implementation for islands.json,
    islandtest and the rig, so the numbers always agree."""
    edge = (wire[..., 3] > 0) & (wire[..., 1] > 200) & (wire[..., 0] < 50) & (wire[..., 2] < 50)
    edge = ndimage.binary_dilation(edge, iterations=1)
    core = ndimage.binary_erosion(paintable & ~edge, iterations=1)
    lab, n = ndimage.label(core)
    sizes = ndimage.sum(core, lab, range(1, n + 1))
    keep = [int(i) + 1 for i in np.argsort(-sizes) if sizes[i] >= min_area]
    dist, (iy, ix) = ndimage.distance_transform_edt(lab == 0, return_indices=True)
    full = lab[iy, ix]
    full[~paintable] = 0
    ids = np.zeros_like(full)
    for new, old in enumerate(keep, start=1):
        ids[full == old] = new
    return ids
