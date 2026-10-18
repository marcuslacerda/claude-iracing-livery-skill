# Adding a car

A car is "calibrated" when `cars/<slug>/car.toml` names its islands, declares the sides, the fixups and
the standard zones (`hood`, `roof`, `doors`, `doors_low`, `wing_centre`, `wing_ends`, `quarters`,
`front_bumper`). Until then it shows as `islands` or `stub` in `paint.py cars` and only `islandtest`
works on it. The `calibrate` skill walks Claude and the user through this; the steps, for a human:

1. **Template.** Download the car's PSD from iracing.com/painttextures (member login) into
   `<workspace>/templates/<slug>/` (slug = CarPath, spaces → `-`). It stays there; never commit it.
2. **`paint.py prepare --car <carpath>`** exports the layers (`work/<slug>/layers/`, with `layers.txt`
   and `manifest.json` saying which file plays which role) and computes the islands
   (`work/<slug>/islands/islands.json`, `islands_map.png`). If a role is missing, check `layers.txt`
   and pass `--layers <substrings>`.
3. **`paint.py scaffold --car <carpath> --car-id <n> --name "<name>"`** writes
   `<workspace>/cars/<slug>/`: `car.toml` with one `island_NN` per island (seed pre-filled), a blank
   `panels.md` table, `notes.md`, `islands.json`, `islands_map.png`.
4. **`paint.py islandtest --car <slug> --deploy`**, then screenshots in the Paint Shop (front ¾ both
   sides, sides, rear ¾, top, close-ups of mirrors, wing, bumper corners, door handle, sills).
   `legend.png` maps colour + number → island.
5. **Name the islands** in `panels.md` and `car.toml` (`roof`, `side_r`, `side_l`, `hood`, `wing`,
   `bumper_rear`, `bumper_front_low`, `mirror_*`, `endplate_*` …), noting orientation and repeats.
6. **Geometry**: `[sides.R]`/`[sides.L]` (sill and belt y; `car_down_y = -1` when the side is drawn
   upside down), `[axes]` (nose/tail x, centreline y), `[[fixups]]` for islands that render elsewhere
   than their UV position, `[zones]` from the template's Sponsor/Number Blocks, `[pairs]`,
   `[preview_crops]`. Optional: `[bumper_rear]` for the stripes wrap, `[mouth]` for the shark mouth.
7. **Verify with text**: `paint.py render --car <slug> --design solid --set text=TEST --deploy` and
   look: readable, right place, right way up on hood/doors/wing. Fix `rotate`/`centre`, repeat. For
   mirrored small islands, test all four transforms.
8. Set `status = "calibrated"`, log the rounds in `panels.md`, lessons in `notes.md`.
9. **Pull request**: copy `cars/<slug>/` (car.toml, panels.md, notes.md, islands.json, islands_map.png —
   nothing from the PSD) into this repo's `cars/` and open a PR. Keep `islands_map.png` at 1024 px.

Reference: `cars/porsche9922cup/` is a complete example, with `panels.md` recording every sim round.
