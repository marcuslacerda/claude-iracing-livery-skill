# Licensing

**This repository** (code, skills, docs, calibrations) is MIT-licensed, © Marcus Lacerda. It is not
affiliated with, endorsed by or associated with iRacing.com Motorsport Simulations, Trading Paints,
Porsche, Mazda or any other manufacturer or brand.

## iRacing's paint templates

The PSD templates are iRacing's copyrighted material, available to members at
https://www.iracing.com/painttextures/. This repository does not contain them and never will; users
download them with their own membership into their workspace. The layers exported from a template
(`work/<car>/layers/`), the renders and the TGAs are local files that stay on the user's machine:
`.gitignore` excludes `*.psd`, `layers/`, `out/`, `work/`, `*.tga` and `*.mip`, and CI fails if any
are tracked.

`cars/<car>/islands.json`, `islands_map.png` (1024 px) and `panels.md` are calibration data derived
from a template: island numbers, bounding boxes, a reduced wireframe diagram with those numbers, and
notes on what each island is. They are published so that users don't have to redo the calibration,
and they are not a usable template. They will be removed at iRacing's request. The same goes for the
`preview_wire.png` of each example in `examples/<car>/<name>/`: the paint with the wireframe on top,
reduced to 1024 px like `islands_map.png`.

## Logos and trademarks

The repository contains no third-party logos. Example images (`examples/<car>/<name>/`) are renders of
the designs with the author's own wordmark and logo (@lacerdapex), as illustration only; the MIT licence
covers the code, not that mark. The designs themselves draw no logo: they use whatever the user's
`brand.toml` points to. A user's logo is the user's
affair; painting someone else's mark is subject to that owner's rights, to iRacing's sporting code and
to Trading Paints' terms of service when shared. The skills refuse to add third-party marks to the
public designs and tell users when a brief involves one.

## Fonts

The engine uses Windows system fonts in place (Bahnschrift, Segoe UI, Arial, Consolas, MS Gothic / Yu Gothic for katakana) and never
redistributes them. User-supplied fonts in `<workspace>/fonts/` are under their own licences.

## Output

The TGAs a user renders are theirs. What they upload to Trading Paints is governed by Trading Paints'
terms. Natural Earth data, if used in a user's design, is public domain.
