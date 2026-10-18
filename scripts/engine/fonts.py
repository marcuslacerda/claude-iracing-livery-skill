"""Font lookup by ROLE with fallbacks, so a missing font never crashes a render.

iRacing is Windows-only, so the default candidates are Windows system fonts (used in place, never
copied). Resolution per candidate: absolute path -> search dirs (profile `fonts_dir`, then
<workspace>/fonts) -> bare file name (Pillow searches the system font folders). If nothing resolves,
Pillow's built-in scalable font is used and a single warning is printed.

Rule from the field: variable fonts (Bahnschrift) render broken glyphs below ~24 px in Pillow; use
the `text` role (Segoe UI Bold) for small text and never go below ~19 px on the 2048 TGA.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import ImageFont

ROLES: dict[str, list[str]] = {
    "display": ["bahnschrift.ttf", "segoeuib.ttf", "arialbd.ttf"],   # big wordmarks (variable font, Bold axis)
    "text": ["segoeuib.ttf", "arialbd.ttf"],                          # small text, no variable axes
    "mono": ["consolab.ttf", "cour.ttf"],
    "jp": ["msgothic.ttc", "YuGothB.ttc", "meiryob.ttc"],             # katakana / kanji (decorative)
    "ui": ["arial.ttf", "segoeui.ttf"],                               # legends / calibration numbers
    "ui_bold": ["arialbd.ttf", "segoeuib.ttf"],
}
SEARCH_DIRS: list[Path] = []          # set by the CLI from profile.fonts_dir and <workspace>/fonts
_warned: set[str] = set()


def candidates(role_or_name: str) -> list[str]:
    return list(ROLES.get(role_or_name, [role_or_name]))


def resolve_path(name: str) -> str:
    p = Path(name).expanduser()
    if p.is_absolute() and p.exists():
        return str(p)
    for d in SEARCH_DIRS:
        if (Path(d) / name).exists():
            return str(Path(d) / name)
    return name  # bare name: let Pillow search the system font directories


def font(role_or_name: str, size: int, weight: str | None = None) -> ImageFont.FreeTypeFont:
    """A FreeType font for a role (`display`, `text`, `mono`, `ui`, `ui_bold`), a file name or a path.
    `weight` selects a named variation on variable fonts (e.g. "Bold" on Bahnschrift); ignored otherwise."""
    size = max(1, int(size))
    for cand in candidates(role_or_name):
        try:
            f = ImageFont.truetype(resolve_path(cand), size)
        except OSError:
            continue
        if weight:
            try:
                f.set_variation_by_name(weight)
            except Exception:
                pass
        return f
    if role_or_name not in _warned:
        _warned.add(role_or_name)
        print(f"warning: no font found for {role_or_name!r} (tried {candidates(role_or_name)}); "
              f"using Pillow's built-in font - text will look different", file=sys.stderr)
    try:
        return ImageFont.load_default(size)
    except TypeError:                      # Pillow < 10.1
        return ImageFont.load_default()
