# Commands and files

All commands: `uv run "<plugin root>/scripts/paint.py" <subcommand>`. Add `--workspace <dir>` to any of
them to override the workspace (else `$IRACING_LIVERY_HOME`, else the profile, else `~/.iracing-livery`).

| Subcommand | What it does |
|---|---|
| `status` | profile, workspace, uv/python, cars table |
| `cars [--scan] [--json]` | known cars with status (`calibrated` / `islands` / `stub`), template/layers/islands present, named panels, zones; `--scan` lists the CarPath folders in the iRacing paint dir |
| `designs [--doc] [--json]` | every design (plugin starters + workspace) with its `PARAMS`; `--doc` prints the markdown catalogue |
| `render --car <car> --design <name\|path> [--set k=v ...] [--name <out>] [--deploy] [--deploy-dir D] [--cid N] [--out D]` | render; output in `<workspace>/work/<car>/out/<name>/` |
| `new-design <name> [--from <starter>] [--force]` | copy a starter into `<workspace>/designs/<name>.py` |
| `compare <a> <b> [--diff out.png] [--tol N]` | pixel comparison of two TGA/PNG (exit 1 when they differ) |
| `prepare --car <car> [--psd F] [--layers-dir D] [--force]` | export layers from the PSD and compute islands (calibrate skill) |
| `islandtest --car <car> [--deploy]` | calibration paint (calibrate skill) |
| `scaffold --car <carpath> --car-id N --name "..."` | car folder in the workspace (calibrate skill) |
| `setup ...` / `profile [--set k=v]` | profile and workspace (setup skill) |
| `inspect <file.psd>` | layer tree of a template |

## Output of a render

```
<workspace>/work/<car>/out/<name>/
  car_<cid>.tga           the paint (24-bit RLE)       -> <paint dir>/<CarPath>/ when --deploy
  car_spec_<cid>.tga      the spec map (32-bit RLE)    -> same
  car.png                 the whole template, for a first look
  preview_wire.png        the paint with the UV wireframe on top (1500 px)
  preview_<crop>.png      per-zone crops from car.toml [preview_crops] (hood, doors, wing, side, roof, front)
```

`--name` changes the output folder (default: the design name). Two renders of the same design with
different `--set` values should use different `--name`s so the user can compare them.

## A design file

`<workspace>/designs/<name>.py`:

```python
"""One line the user would recognise: 'black satin, amber stripes, logo on the hood'."""
from engine.draw import render_text
from engine.elements import gradient, stripes
from engine.starters import accent_islands, color, finish, mark_or_wordmark, place_if, text

PARAMS = {"body": "#0a0e13", "stripe": "#e8a33d", "text": "", "satin": True}   # what --set can change
CAR = None            # or "porsche9922cup" when it uses zones only that car has

def design(rig, p=PARAMS):
    base = gradient.solid(rig, color(p, "body", "#0a0e13"))          # float RGB base
    paint = rig.to_canvas(rig.fixups(base))                           # -> Paint (canvas + spec info)
    stripes.longitudinal(rig, paint.canvas, stripes.trio(stripes.smooth_path(stripes.DEFAULT_KNOTS),
                         [((134, 20, 86), (110, 12, 70)), (color(p, "stripe", "#e8a33d"), (168, 104, 28)),
                          ((134, 20, 86), (110, 12, 70))]))
    place_if(rig, "roof", paint, mark_or_wordmark(p, 400, "#e9e4d9"))
    place_if(rig, "wing_centre", paint, render_text(text(p), 60, color="#e9e4d9"))
    return finish(rig, paint, p["satin"])
```

Rules: `PARAMS` values are plain JSON types (hex strings for colours); an empty string means "take it
from brand.toml"; `design()` returns the `Paint` it got from `rig.to_canvas`. `--set key=value` is
coerced to the type of the default. Private helpers go in `<workspace>/lib/<x>.py` and are imported as
`from lib.x import ...`.

## brand.toml

```toml
text = "@YOURNAME"
logo = "assets/logo.png"        # transparent PNG (or a dark logo on white): used as a shape
[colors]
primary = "#9511dd"
accent  = "#e8a33d"
body    = "#0a0e13"
```

`engine.starters.color(p, "accent", fallback)` resolves PARAMS → brand → fallback; `mark_or_wordmark`
returns the logo sprite or, with no logo, the wordmark text, so every starter renders with or without one.
