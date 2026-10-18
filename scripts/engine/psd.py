"""Reading the official PSD template (psd-tools, imported lazily: `render` never needs it).

The templates are iRacing's copyrighted material: the user downloads them from
https://www.iracing.com/painttextures/ (member login) and keeps them in <workspace>/templates/<car>/.
Nothing read from them is ever committed to this repository.
"""
from __future__ import annotations

import re
from pathlib import Path

from PIL import Image, ImageDraw

# layer-name substrings worth exporting by default (case-insensitive); the car patterns are skipped
# because there are dozens and they are only useful as a contact sheet
DEFAULT_WANTED = ["Wire", "Mask", "Car_Mandatory", "Paintable_Area_Base", "Main_Car_Body", "Sponsor Blocks",
                  "Number Blocks", "Windshield", "Car_decal", "Spec", "Parts", "Color_Change", "Logos"]


def _open(psd_path):
    try:
        from psd_tools import PSDImage
    except ImportError as e:  # pragma: no cover
        raise SystemExit("psd-tools is not installed (it is declared in scripts/paint.py's header; "
                         "run through `uv run scripts/paint.py ...`)") from e
    return PSDImage.open(str(psd_path))


def inspect(psd_path) -> str:
    """The layer tree as text (visibility, kind, bbox, blend mode, opacity, masks)."""
    psd = _open(psd_path)
    lines = [f"{psd_path} {psd.size} {psd.color_mode} depth={psd.depth} channels={psd.channels}"]

    def walk(layer, depth=0):
        vis = "V" if layer.visible else "-"
        extra = ""
        if hasattr(layer, "blend_mode"):
            extra += f" blend={layer.blend_mode.name.lower()}"
        extra += f" op={layer.opacity}"
        if layer.has_mask():
            extra += " MASK"
        if layer.has_clip_layers():
            extra += " clip"
        try:
            bb = layer.bbox
        except Exception:
            bb = None
        lines.append(f"{'  ' * depth}[{vis}] {layer.kind:9s} {layer.name!r} bbox={bb}{extra}")
        if layer.is_group():
            for ch in layer:
                walk(ch, depth + 1)

    for layer in psd:
        walk(layer)
    return "\n".join(lines)


def export_layers(psd_path, out_dir, wanted=None, skip=("car_pattern",)) -> list[Path]:
    """Export pixel layers whose full path contains any of `wanted` (empty = all) as full-canvas RGBA PNGs."""
    psd = _open(psd_path)
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    W, H = psd.size
    wanted = DEFAULT_WANTED if wanted is None else wanted
    written: list[Path] = []

    def walk(layer, path=""):
        name = f"{path}/{layer.name}" if path else layer.name
        if layer.is_group():
            for ch in layer:
                walk(ch, name)
            return
        if any(s.lower() in name.lower() for s in skip):
            return
        if wanted and not any(w.lower() in name.lower() for w in wanted):
            return
        img = layer.topil()
        if img is None:
            return
        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        canvas.paste(img.convert("RGBA"), (layer.left, layer.top))
        fn = re.sub(r"[^A-Za-z0-9_.-]+", "_", name) + ".png"
        canvas.save(out_dir / fn)
        written.append(out_dir / fn)

    for layer in psd:
        walk(layer)
    return written


def contact_sheet(psd_path, out_png, cell=340, cols=6) -> int:
    """All car_pattern layers of the "Car Patterns" group on one sheet (how iRacing itself segments panels)."""
    psd = _open(psd_path)
    groups = []

    def walk(layer):
        if layer.is_group():
            if "pattern" in layer.name.lower():
                groups.append(layer)
            for ch in layer:
                walk(ch)

    for layer in psd:
        walk(layer)
    layers = [l for g in groups for l in g if not l.is_group() and "spec" not in l.name.lower()]
    layers.sort(key=lambda l: l.name)
    if not layers:
        return 0
    rows = (len(layers) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell, rows * cell), "white"); d = ImageDraw.Draw(sheet)
    for i, l in enumerate(layers):
        im = l.topil()
        if im is None:
            continue
        im = im.convert("RGB").resize((cell - 10, cell - 10), Image.LANCZOS)
        x, y = (i % cols) * cell, (i // cols) * cell
        sheet.paste(im, (x + 5, y + 5)); d.text((x + 8, y + 8), l.name, fill="black")
    Path(out_png).parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_png)
    return len(layers)
