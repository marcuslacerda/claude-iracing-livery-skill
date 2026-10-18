---
name: setup
description: First-run setup and maintenance for iRacing custom painting with this plugin — checks uv, finds the iRacing paint folder and the user's customer id, creates the workspace (templates, work files, own designs, brand.toml with logo/text/colours), and guides the download of a car's official template. Use when the user says "set up iRacing painting", changes PC or customer id, wants to move the workspace, asks where to download a template, or when the paint/calibrate skills find no profile.
---

# setup

Creates `~/.iracing-livery/profile.json` (the only fixed file) and the **workspace** where everything
of the user's lives. Commands: `uv run "<plugin root>/scripts/paint.py" ...` (plugin root = two
folders above this file; resolve it once, quote it).

## First run: ask one thing at a time, in a short back-and-forth

0. **`uv`**: run `uv --version` (or `status`). If it is missing, point to
   https://docs.astral.sh/uv/getting-started/installation/ (`winget install astral-sh.uv` on Windows,
   or the PowerShell one-liner); `uv` downloads a Python if none is installed. Nothing else to install.
1. **Customer ID** — the number iRacing puts in `car_<id>.tga`. Where to find it: iracing.com → My
   Account (Customer ID), or an existing `car_<id>.tga` in the paint folder. `cars --scan` (ask before
   listing) shows those file names.
2. **iRacing paint folder** — `status` prints the candidates it found (`Documents/iRacing/paint`, the
   OneDrive-synced variants, the Portuguese `Documentos`). Let the user confirm or give the path.
3. **Main car** — one of the CarPath folders (`cars --scan`); the `paint` skill defaults to it.
4. **Workspace** — where templates, work files, their own designs and `lib/` live. Suggest
   `~/.iracing-livery`; any folder works, and a folder synced by OneDrive (or kept next to their other
   projects) lets them continue on another PC by just installing the plugin and running setup again
   with the same path. It can be moved later (`setup --workspace <new>` after copying the folder).
5. Then:
   ```
   uv run "<plugin root>/scripts/paint.py" setup --workspace "<dir>" --customer-id <id> --paint-dir "<paint dir>" --main-car <carpath>
   ```
   creates the tree and a `brand.toml` template.
6. **Brand** (optional, but it makes every starter theirs): ask for the wordmark text (`@handle`,
   team name), the main colours, and a logo PNG (transparent background, or dark on white). Copy the
   PNG to `<workspace>/assets/` and fill `<workspace>/brand.toml` (`text`, `logo`, `[colors]`).
7. **Template for the main car**: if `cars` shows no `psd` for it, ask them to download the PSD from
   https://www.iracing.com/painttextures/ (member login; the templates are iRacing's, keep them local)
   into `<workspace>/templates/<slug>/` and run `prepare --car <slug>`. Calibrated cars (the Porsche
   992.2 Cup today) are then ready to paint; others go to the `calibrate` skill.
8. Finish with `status` and a one-line summary of what is where.

## Later

- `profile` prints the profile; `profile --set customer_id=…` / `--set iracing_paint_dir=…` edits it.
- New PC: install the plugin, run `setup --workspace <same folder>` with the customer id and paint
  dir; the workspace carries templates, work files and designs.
- `setup --fonts-dir <dir>` adds a folder of extra fonts for designs.
- Nothing here needs the network except the user's own browser for the template download.
