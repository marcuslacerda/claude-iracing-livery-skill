"""The user's brand, declared once in <workspace>/brand.toml and read by every design:

    text = "@MYTEAM"                 # wordmark text
    logo = "assets/logo.png"         # a PNG with transparency (or a dark logo on white)
    logo_mono = "assets/logo-mono.png"
    [colors]
    primary = "#9511dd"
    accent  = "#e8a33d"
    body    = "#0a0e13"

Brand marks are SHAPES, not fonts: ask for the image and use its transparency (or darkness) as the
mask. Nothing here is specific to any brand.
"""
from __future__ import annotations

import tomllib
from pathlib import Path

from PIL import Image

from . import paths
from .draw import hex2rgb, load_sprite, silhouette

WORKSPACE: Path | None = None      # set by the CLI; otherwise resolved from the profile on first use


class Brand:
    def __init__(self, data: dict, root: Path | None):
        self.data = data
        self.root = Path(root) if root else None
        self.text: str = data.get("text", "")
        self.colors: dict[str, str] = dict(data.get("colors", {}))
        self._logo = data.get("logo")
        self._logo_mono = data.get("logo_mono")

    def _path(self, p) -> Path | None:
        if not p:
            return None
        p = Path(p).expanduser()
        if not p.is_absolute() and self.root:
            p = self.root / p
        return p if p.exists() else None

    @property
    def logo(self) -> Path | None:
        return self._path(self._logo)

    @property
    def logo_mono(self) -> Path | None:
        return self._path(self._logo_mono) or self.logo

    def color(self, name: str, default=None):
        """RGB tuple of a named brand colour, or `default` (hex or tuple) when it isn't declared."""
        v = self.colors.get(name, default)
        return hex2rgb(v) if v is not None else None

    def logo_sprite(self, height: int | None = None, color=None, mono=False) -> Image.Image | None:
        """The logo as an RGBA sprite; `color` tints its shape (silhouette); `height` scales it."""
        p = self.logo_mono if mono else self.logo
        if p is None:
            return None
        if color is not None:
            img = mask_from_image(p, color, height)
        else:
            img = load_sprite(p)
            if height:
                w = int(img.width * height / img.height)
                img = img.resize((max(1, w), height), Image.LANCZOS)
        return img

    def __bool__(self):
        return bool(self.data)


def mask_from_image(path, color, height: int | None = None) -> Image.Image:
    """A flat-colour sprite from an image's transparency (or darkness, for a logo on white), scaled
    to `height` keeping the aspect ratio."""
    img = silhouette(load_sprite(path), color)
    if height:
        w = int(img.width * height / img.height)
        img = img.resize((max(1, w), height), Image.LANCZOS)
    return img


def load(workspace=None) -> Brand:
    root = Path(workspace) if workspace else (WORKSPACE or paths.resolve_workspace())
    toml = Path(root) / "brand.toml"
    if toml.exists():
        with open(toml, "rb") as f:
            return Brand(tomllib.load(f), root)
    return Brand({}, root)


class _Lazy:
    """`from engine.brand import brand` inside a design: resolved against the workspace on first use."""
    _b: Brand | None = None

    def _get(self) -> Brand:
        if self._b is None:
            self._b = load()
        return self._b

    def __getattr__(self, item):
        return getattr(self._get(), item)

    def __bool__(self):
        return bool(self._get())


brand = _Lazy()


def reset():
    brand._b = None
