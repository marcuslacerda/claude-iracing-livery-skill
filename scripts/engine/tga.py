"""TGA in/out and pixel comparison (regression checks)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image


def save_tga(img: Image.Image, path, alpha: bool = False) -> Path:
    """iRacing wants 24-bit (paint) or 32-bit (spec map) RLE-compressed TGA."""
    path = Path(path)
    img = img.convert("RGBA" if alpha else "RGB")
    img.save(path, compression="tga_rle")
    return path


def load(path) -> np.ndarray:
    return np.asarray(Image.open(path))


def compare(a, b, tol: int = 0, diff_png=None) -> dict:
    """Decoded-pixel comparison of two images (TGA/PNG). Encoding differences are irrelevant."""
    A, B = load(a), load(b)
    res = {"a": str(a), "b": str(b), "shape_a": list(A.shape), "shape_b": list(B.shape)}
    if A.shape != B.shape:
        res.update(shape_ok=False, n_diff=-1, max_abs=-1, pct=100.0, bbox=None)
        return res
    d = np.abs(A.astype(np.int16) - B.astype(np.int16))
    if d.ndim == 3:
        d = d.max(axis=2)
    bad = d > tol
    n = int(bad.sum())
    res.update(shape_ok=True, n_diff=n, max_abs=int(d.max()), pct=round(100.0 * n / bad.size, 4))
    if n:
        ys, xs = np.nonzero(bad)
        res["bbox"] = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    else:
        res["bbox"] = None
    if diff_png:
        vis = np.zeros(bad.shape + (3,), np.uint8)
        vis[..., 0] = np.clip(d * 4, 0, 255)
        vis[bad] = (255, 255, 255)
        Image.fromarray(vis, "RGB").save(diff_png)
        res["diff_png"] = str(diff_png)
    return res
