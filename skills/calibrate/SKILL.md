---
name: calibrate
description: Calibrates a new iRacing car for custom painting — exports the official template's layers, numbers its UV islands, installs a calibration paint, reads the user's Paint Shop screenshots to map every island to a real panel (roof, doors, hood, wing, mirrors ...) and writes the car's car.toml and panels.md so designs can be rendered on it. Use when the user wants to paint a car the plugin doesn't know yet (status `islands` or `stub` in `cars`), asks "how do I start painting the <car>", pastes screenshots of a numbered test paint, says an island came out mirrored/rotated, or reports iRacing updated a template.
---

# calibrate

Every iRacing car is a different UV layout, and **the template lies about where islands land on the
car** (mirrored sides, parts drawn upside down, one island reused four times, wing endplates sitting
in the "nose" zone). The only reliable method is empirical: paint every island in its own colour with
its number on it, install it, and read the numbers off the real car in the Paint Shop. That is this
skill. The result is `cars/<car>/car.toml` (islands, fixups, sides, zones) + `panels.md` (the evidence)
in the user's workspace, which the `paint` skill then uses. Read
[`references/calibration.md`](references/calibration.md) for the hard-won rules before you start,
and [`../paint/references/zones.md`](../paint/references/zones.md) for what a finished car.toml must offer.

Commands: `uv run "<plugin root>/scripts/paint.py" ...` (plugin root = two folders above this file;
resolve it once, quote it). Workspace, profile and permissions as in the `paint` skill: say what you
will do before listing folders or installing into the sim, and wait for a yes.

## Workflow

1. **Identify the car.** `cars --scan` lists the CarPath folders in the iRacing paint dir (ask first);
   the CarPath is the folder name (`porsche992rgt3`, `mx5 mx52016` …). `cars` shows what the plugin
   already knows: `calibrated` (done), `islands` (layers and islands exist, panels not named), `stub`.
2. **Template.** Ask the user to download the car's PSD from https://www.iracing.com/painttextures/
   (member login) and save it in `<workspace>/templates/<slug>/` (slug = CarPath with spaces → `-`).
   Then `prepare --car <carpath>`: exports the useful layers, writes `layers.txt` (the layer tree) and
   `manifest.json` (which file plays which role), computes the islands → `work/<slug>/islands/`
   (`islands.json`, `islands_map.png`). If a role is missing (mask/wire/spec channels), read
   `layers.txt` and pass `--layers <substrings>` to export the right ones.
3. **Scaffold** (new car only): `scaffold --car <carpath> --car-id <n> --name "<name>"` writes
   `<workspace>/cars/<slug>/car.toml` (one `island_NN` entry per island, seeds pre-filled), `panels.md`
   (one row per island, all ⚠️), `notes.md`, `islands.json`, `islands_map.png`. The car_id is the
   number iRacing uses in the template's file name / download page.
4. **Calibration paint.** `islandtest --car <slug> --deploy` (ask first). Tell the user: open the
   Paint Shop with "Show Custom Paint", take screenshots of the car from the front, both sides, rear,
   above, and close-ups of mirrors / wing / bumper corners, and paste them here. `legend.png` in
   `work/<slug>/out/islandtest/` maps colour+number → island.
5. **Read the screenshots** (you can view images). For each visible number: which panel is it, which
   way does it read (upright / upside down / mirrored), does the same number appear in several places?
   Also open `islands_map.png` to see each island's shape on the template. Fill `panels.md` (name,
   confidence ✅ with the date, notes) and rename the islands in `car.toml` with the standard names
   (`roof`, `side_r`, `side_l`, `hood`, `wing`, `bumper_front_low`, `bumper_rear`, `mirror_*`, …).
6. **Geometry.** From the sides' bbox: `[sides.R]` / `[sides.L]` with `sill` and `belt` y (the sill is
   the bottom edge of the island as it reads on the car; for an upside-down side the sill y is SMALLER
   than the belt y → `car_down_y = -1`). `[axes] length` = nose x and tail x on the side islands;
   `centre_y` = centreline of the hood/roof band. `[[fixups]]` for every island that renders somewhere
   else than its UV position suggests (tail parts near the nose, mirrors, repeated plates): sample a
   pixel in the panel it belongs to. `[zones]`: centre = middle of the sponsor block (the template's
   `Sponsor Blocks` / `Number Blocks` layers show them: `inspect` lists them, `prepare` exports them),
   `rotate` so text reads correctly (test with a render), `max` = the block size minus a margin.
7. **Verify with a real render**: `render --car <slug> --design solid --set text=TEST` then
   `--deploy` (ask) and screenshots again: is the text readable on the hood/doors/wing, in the right
   place and the right way up? Adjust `rotate` / `centre` and repeat. For a mirrored pair of small
   islands, test all four transforms before assuming (`flip` in a `[[...pieces]]` section or a
   separate zone with its own `rotate`).
8. **Status.** When the standard zones exist, set `status = "calibrated"` in `[car]`. The car now
   shows `calibrated` in `cars` and every starter renders on it. Log the rounds in `panels.md`
   ("Validated in the sim") and the lessons in `notes.md`.
9. **Contribute back** (offer, don't push): the car folder (`car.toml`, `panels.md`, `notes.md`,
   `islands.json`, `islands_map.png` — nothing from the PSD itself) is exactly what a pull request to
   the plugin needs so the next person skips this. See `docs/new-car.md` in the plugin.

## When the template changed

`prepare` warns when the freshly computed islands differ from the calibrated `islands.json`; a render
raises `CalibrationError` when a seed no longer lands on its island number. Re-run `prepare`, compare
the two maps, fix the numbers in car.toml (names stay), and re-verify with a `solid` render.
