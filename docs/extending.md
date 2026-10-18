# Extending without a pull request

Everything you customise lives in your workspace (chosen in `setup`; default `~/.iracing-livery`),
never inside the plugin folder, which Claude Code replaces on update. Lookup order is always
**workspace first, then plugin**, so a workspace file with the same name wins.

## Level 1 — no file: starter + brand.toml + parameters

```toml
# <workspace>/brand.toml
text = "@MYTEAM"
logo = "assets/logo.png"      # transparent PNG, or a dark logo on white (used as a shape)
[colors]
primary = "#1e3a8a"
accent  = "#e8a33d"
body    = "#0a0e13"
```

```
paint.py render --car porsche9922cup --design stripes --set body=#ffffff --set stripe=#1e3a8a
```

Every starter reads `brand.toml` for the empty parameters and `--set` overrides anything.

## Level 2 — your own design file

```
paint.py new-design my_livery --from stripes
```

creates `<workspace>/designs/my_livery.py` — a copy of the starter you (or Claude) edit. It is a
Python file, but the shape is small and fixed:

```python
"""One line that describes it."""
from engine.draw import render_text
from engine.elements import gradient, stripes
from engine.starters import color, finish, mark_or_wordmark, place_if, text

PARAMS = {"body": "#0a0e13", "stripe": "#e8a33d", "text": "", "satin": True}
CAR = None

def design(rig, p=PARAMS):
    paint = rig.to_canvas(rig.fixups(gradient.solid(rig, color(p, "body", "#0a0e13"))))
    ...
    return finish(rig, paint, p["satin"])
```

`rig.place("<zone>", paint, sprite)` is the whole placement API (zones in
`skills/paint/references/zones.md`); elements are listed in `designs/README.md`.

## Level 3 — your own elements and symbols

`<workspace>/lib/<name>.py` is importable from any of your designs as `from lib.<name> import ...`:
a symbol drawn in code, a motif, a palette, a helper that places your sponsor pack. The engine's
drawing helpers (`engine.draw`: `SSDraw`, `band_polygon`, `fit`, `place`, `render_text`,
`silhouette`) are there for it.

## Your own car calibration

`<workspace>/cars/<slug>/car.toml` overrides the plugin's for that slug. That is where `scaffold`
writes a new car and where you can also tweak a shipped one (a different `louver_offset`, an extra
zone). See `docs/new-car.md`.

## What belongs in a pull request

Only generic things: a calibrated car folder, a new element in `scripts/engine/elements/`, a new
starter (brand-free, with `PARAMS` and a docstring; regenerate the catalogue with
`paint.py designs --doc`), a fix. Not: your brand, your logo, a third-party logo, a template.
