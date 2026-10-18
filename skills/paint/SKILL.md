---
name: paint
description: Designs, renders and installs a custom iRacing livery (paint TGA + spec map) for a calibrated car from a plain-language description — colours, stripes, a shark mouth, the user's own logo and wordmark — then shows previews, iterates, and copies the files into the iRacing paint folder on request. Use when someone wants to paint, repaint, tweak, preview or install a custom paint / livery / skin for an iRacing car, or asks what paints are possible. Runs 100% locally with Python + uv; the official templates stay on the user's machine.
---

# paint

Turn a sentence ("black satin with amber stripes and my logo on the hood") into `car_<id>.tga` +
`car_spec_<id>.tga` for the car, with previews the user approves before anything touches the sim.
The heavy lifting is deterministic: `scripts/paint.py render` draws the design on the car's
calibrated rig and writes the TGAs. Your job is to pick the right starter, write or edit a small
Python design file for the user (they never need to read it), look at the previews, and iterate.

Read [`references/workflow.md`](references/workflow.md) for the exact commands,
[`references/zones.md`](references/zones.md) for the vocabulary a design uses,
[`references/iracing-rules.md`](references/iracing-rules.md) for what the sim does with the files, and
[`references/licensing.md`](references/licensing.md) before touching templates or third-party logos.
The starters catalogue is [`../../designs/README.md`](../../designs/README.md): read it before proposing
a starter so you offer documented variations instead of inventing.

## Paths and the first command

The scripts live next to this file: `<plugin root>/scripts/paint.py`, where the plugin root is the
folder two levels above this SKILL.md. Resolve that absolute path once and reuse it; always quote
it. `${CLAUDE_PLUGIN_ROOT}` is empty under PowerShell, so don't rely on it. Every call is:

```
uv run "<plugin root>/scripts/paint.py" <subcommand> ...
```

`uv` resolves the dependencies declared in the script's header on first run (nothing else to install).
No `pyproject.toml` is needed in the working directory.

First, always: `status`. It prints the profile (customer id, iRacing paint folder, workspace), the
known cars with their calibration status, and whether `uv` is on PATH. If there is no profile yet, hand
over to the `setup` skill (`/iracing-livery:setup`) and come back.

## Permission before touching the user's machine

Say what you are about to do, in one sentence, and wait for a yes before:

- listing the iRacing paint folder (`cars --scan` prints folder names and the TGAs in them, nothing else);
- **installing into the sim** (`--deploy` copies two files into `<paint dir>/<CarPath>/`, overwriting
  the paint currently installed for that car — one paint per car at a time);
- reading an image the user did not hand you (their logo, a screenshot).

Rendering into the workspace is just doing the job; no need to ask.

## Workflow

1. **Which car?** The profile has `main_car`; otherwise ask. Only cars with status `calibrated` can be
   painted (`cars`). A car with status `islands` or `stub` needs the `calibrate` skill first — say so and
   offer to start it.
2. **Understand the brief.** Colours (hex or names → pick a hex), finish (glossy vs satin), motifs
   (stripes, two-tone, shark mouth, solid, sponsor pack), where the logo and the wordmark go. If the
   user has a logo and `brand.toml` has none, ask for a PNG (transparent background, or dark on white),
   copy it to `<workspace>/assets/`, and point `logo = "assets/<file>"` in `<workspace>/brand.toml` at it.
   Logos are shapes: never redraw a brand by hand or from a font.
3. **Pick a starter** from `designs --doc` / `designs/README.md`. Most briefs are a starter plus
   parameters: try `render --design <starter> --set key=value ...` first (no file). When the brief needs
   more than parameters, `new-design <name> --from <starter>` copies it into
   `<workspace>/designs/<name>.py` and you edit that file (see `references/zones.md` for the API).
   Never edit files inside the plugin folder; everything the user owns lives in the workspace.
4. **Render and LOOK.** `render --car <car> --design <name>` writes `car.png`, `preview_wire.png` and
   `preview_<zone>.png` into `<workspace>/work/<car>/out/<name>/`. Open the previews (you can view
   images) and check them against the brief yourself before showing them: text readable, nothing on the
   number area, nothing crossing the wing mounts, stripes continuous across panels. Then show the
   user `car.png` plus the two or three crops that matter and ask what to change.
5. **Iterate** on the parameters or the design file. Keep the user's words in the file's docstring so
   `designs` lists it meaningfully.
6. **Install** only on an explicit yes: `render ... --deploy`. Then tell them: open iRacing's Paint
   Shop with "Show Custom Paint" on (no session needed), or press `Ctrl+R` in a session to reload the
   `.mip`. Only they see a local paint; sharing with others needs Trading Paints.
7. **Close the loop.** If they report something off in the sim (a logo bent at the door handle, a
   stripe cut at the louver), that is calibration knowledge: fix the design, and if it is about the car
   itself, note it in the car's `notes.md` (workspace copy) so the next design doesn't repeat it.

## Golden rules (sim-verified, don't relearn them)

- **The number comes from the sim**, drawn on the front-lower part of the door (x≈780–1000 on the
  Cup) in the Paint Shop colour: never put a logo there. On a dark body, tell the user to change the
  number colour in the Paint Shop.
- **Small text ≥ 19 px** on the 2048 template, and never a variable font (`display` role) below ~24 px:
  use `font="text"` for small text.
- **Detailed logos go below the door-handle line** (`doors_low`); only big flat shapes survive on `doors`.
- **Wing art only in the three free zones** (`wing_centre`, `wing_ends`); never a wide lockup across
  the mounts.
- **Satin body (roughness 140) + glossy logos (33)** is the finish that reads best; it is a parameter
  (`satin`) on every starter.
- **Curves are drawn at 4x and downsampled** (the elements do it); never thick `line()` strokes.
- Islands lie: colour by position needs the car's fixups (already in car.toml for calibrated cars).

## What this skill does not do

- No upload anywhere, no Trading Paints integration (see `references/iracing-rules.md` for sharing).
- No new-car calibration (that is `calibrate`), no profile changes (that is `setup`).
- It never redistributes iRacing's templates or any logo; see `references/licensing.md`.
