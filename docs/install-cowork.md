# Install in Claude Cowork (alternative)

Cowork (the desktop app's agent mode) installs the same plugin from the same repository:

1. **Customize → Plugins → Add → Add marketplace**, paste `marcuslacerda/claude-iracing-livery-skill`
   (or the full GitHub URL), then install **iRacing Livery**. Alternatively **Add → Upload plugin**
   with a zip of this repository (it contains `.claude-plugin/plugin.json`).
2. A plugin installed this way is saved to your account, so its skills also appear in Claude Code
   as `iracing-livery@synced`.
3. `uv` must be installed on the PC (see [install-claude-code.md](install-claude-code.md), step 1).

## What to check before relying on it

The skills run `uv run scripts/paint.py` on your machine, read your iRacing paint folder and write
two TGA files into it. That works in a Cowork session running **on the Windows PC where iRacing is
installed**, with file access granted to the paint folder and the workspace. It does not work in the
web chat (no local files, no local commands). If a Cowork session cannot run local commands in your
setup, use Claude Code, which is the primary target of this plugin.

Everything else — onboarding, the workspace, templates, previews — is identical.
