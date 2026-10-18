# Install in Claude Code (recommended)

## 1. `uv`

The scripts run with [`uv`](https://docs.astral.sh/uv/), which also downloads a Python if you have
none. In PowerShell:

```powershell
winget install astral-sh.uv
```

or the official one-liner from https://docs.astral.sh/uv/getting-started/installation/. Open a new
terminal afterwards and check `uv --version`.

## 2. The plugin

In a Claude Code session (terminal, VS Code or the desktop app's Code tab):

```
/plugin marketplace add marcuslacerda/claude-iracing-livery-skill
/plugin install iracing-livery@lacerdapex-livery
```

One-step form (Claude Code 2.1.275+): `/plugin install iracing-livery --marketplace marcuslacerda/claude-iracing-livery-skill`.
From a shell: `claude plugin install iracing-livery --marketplace marcuslacerda/claude-iracing-livery-skill`.
Desktop app: Code tab → **+** → Plugins → Add plugin, paste the repository.

Pick the *user* scope when asked so the skills are available in every folder. Updates: third-party
marketplaces don't auto-update by default; run `/plugin marketplace update lacerdapex-livery` now and then.

## 3. First run

Say **"set up iRacing painting for me"** (or `/iracing-livery:setup`). Claude asks for your iRacing
customer id, your paint folder, where to keep your workspace and your brand, and points you to the
template download. Then **"paint my Porsche Cup …"**.

The three commands are `/iracing-livery:paint`, `/iracing-livery:calibrate`, `/iracing-livery:setup`;
you can also just describe what you want.

## From source (no plugin system)

```powershell
git clone https://github.com/marcuslacerda/claude-iracing-livery-skill
Copy-Item -Recurse .\claude-iracing-livery-skill\skills\paint     $HOME\.claude\skills\iracing-livery-paint
Copy-Item -Recurse .\claude-iracing-livery-skill\skills\calibrate $HOME\.claude\skills\iracing-livery-calibrate
Copy-Item -Recurse .\claude-iracing-livery-skill\skills\setup     $HOME\.claude\skills\iracing-livery-setup
```

The skills call `scripts/paint.py` relative to the repository, so keep the clone and tell Claude where
it is the first time ("the livery scripts are in C:\...\claude-iracing-livery-skill"). The plugin route
avoids this.

## Troubleshooting

- `uv` not found after installing → open a new terminal (PATH is read at start).
- "no exported layers for <car>" → the PSD isn't in `<workspace>/templates/<car>/` yet, or `prepare` didn't run.
- "island numbering does not match car.toml" → iRacing updated the template: `prepare --car <car> --force`
  and compare the island maps (see the `calibrate` skill).
- Fonts look different → the engine uses Windows fonts (Bahnschrift, Segoe UI, Arial); on another OS put
  TTFs in `<workspace>/fonts/`.
- The sim doesn't show the new paint → it reloads when `car_<id>.tga` is newer than the `.mip`; press
  `Ctrl+R` in the session, or check the customer id in the file name.
