"""Where things live.

Fixed location (the only one):   ~/.iracing-livery/profile.json
    customer_id, iracing_paint_dir, main_car, workspace

Everything else is in the WORKSPACE the user picked during setup (default ~/.iracing-livery):
    brand.toml                      the user's logo / text / colours (see engine.brand)
    templates/<car>/*.psd           the official iRacing templates (downloaded by the user)
    work/<car>/{layers,islands,preview,out/<design>}
    cars/<car>/car.toml ...         the user's own car calibrations (override the plugin's)
    designs/<name>.py               the user's own designs (override the plugin's)
    lib/*.py                        the user's own reusable elements (importable as `lib.x`)
    assets/, fonts/

Lookup order for cars, designs and elements is always: workspace first, then the plugin.
Updating the plugin never touches the workspace.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
PLUGIN_ROOT = SCRIPTS_DIR.parent
PROFILE_DIR = Path.home() / ".iracing-livery"
PROFILE_PATH = PROFILE_DIR / "profile.json"
DEFAULT_WORKSPACE = PROFILE_DIR
ENV_WORKSPACE = "IRACING_LIVERY_HOME"
WORKSPACE_SUBDIRS = ("templates", "work", "cars", "designs", "lib", "assets", "fonts")

PAINT_DIR_CANDIDATES = (
    "~/Documents/iRacing/paint",
    "~/OneDrive/Documents/iRacing/paint",
    "~/OneDrive/Documentos/iRacing/paint",
    "~/Documentos/iRacing/paint",
)


def load_profile() -> dict:
    if PROFILE_PATH.exists():
        try:
            return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise SystemExit(f"{PROFILE_PATH} is not valid JSON ({e}); fix or delete it")
    return {}


def save_profile(profile: dict) -> Path:
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    PROFILE_PATH.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
    return PROFILE_PATH


def resolve_workspace(cli: str | os.PathLike | None = None, profile: dict | None = None) -> Path:
    """--workspace > $IRACING_LIVERY_HOME > profile.json["workspace"] > ~/.iracing-livery"""
    if cli:
        return Path(cli).expanduser().resolve()
    env = os.environ.get(ENV_WORKSPACE)
    if env:
        return Path(env).expanduser().resolve()
    profile = load_profile() if profile is None else profile
    if profile.get("workspace"):
        return Path(profile["workspace"]).expanduser().resolve()
    return DEFAULT_WORKSPACE


def slugify(car_path: str) -> str:
    """CarPath -> folder-safe slug ("mx5 mx52016" -> "mx5-mx52016"). Idempotent."""
    return re.sub(r"[^a-z0-9]+", "-", car_path.strip().lower()).strip("-")


def paint_dir_candidates() -> list[Path]:
    return [p for p in (Path(c).expanduser() for c in PAINT_DIR_CANDIDATES) if p.is_dir()]


class Workspace:
    def __init__(self, root: Path):
        self.root = Path(root)

    def __fspath__(self):
        return str(self.root)

    def __str__(self):
        return str(self.root)

    @property
    def templates(self): return self.root / "templates"
    @property
    def work(self): return self.root / "work"
    @property
    def cars(self): return self.root / "cars"
    @property
    def designs(self): return self.root / "designs"
    @property
    def lib(self): return self.root / "lib"
    @property
    def assets(self): return self.root / "assets"
    @property
    def fonts(self): return self.root / "fonts"
    @property
    def brand_toml(self): return self.root / "brand.toml"

    def ensure(self):
        for d in WORKSPACE_SUBDIRS:
            (self.root / d).mkdir(parents=True, exist_ok=True)
        return self

    def car_work(self, slug: str) -> dict[str, Path]:
        base = self.work / slug
        return {"root": base, "layers": base / "layers", "islands": base / "islands",
                "preview": base / "preview", "out": base / "out"}

    def template_dir(self, slug: str) -> Path:
        return self.templates / slug

    def find_psd(self, slug: str, hint: str | None = None) -> Path | None:
        d = self.template_dir(slug)
        if not d.is_dir():
            return None
        if hint and (d / hint).exists():
            return d / hint
        psds = sorted(d.glob("*.psd")) + sorted(d.glob("*.psb"))
        return psds[0] if psds else None

    # ---- lookup: workspace first, then plugin ------------------------------------------------
    def car_dirs(self) -> dict[str, tuple[Path, str]]:
        """slug -> (dir, source) with workspace overriding plugin."""
        out: dict[str, tuple[Path, str]] = {}
        for src, base in (("plugin", PLUGIN_ROOT / "cars"), ("workspace", self.cars)):
            if base.is_dir():
                for d in sorted(base.iterdir()):
                    if (d / "car.toml").exists():
                        out[d.name] = (d, src)
        return out

    def find_car(self, name: str) -> tuple[Path, str] | None:
        return self.car_dirs().get(slugify(name))

    def design_files(self) -> dict[str, tuple[Path, str]]:
        out: dict[str, tuple[Path, str]] = {}
        for src, base in (("plugin", PLUGIN_ROOT / "designs"), ("workspace", self.designs)):
            if base.is_dir():
                for f in sorted(base.glob("*.py")):
                    if not f.name.startswith("_"):
                        out[f.stem] = (f, src)
        return out

    def find_design(self, name_or_path: str) -> tuple[Path, str] | None:
        p = Path(name_or_path).expanduser()
        if p.suffix == ".py" and p.exists():
            return p.resolve(), "path"
        files = self.design_files()
        for key in (name_or_path, name_or_path.replace("-", "_")):
            if key in files:
                return files[key]
        return None

    def sys_path_entries(self) -> list[str]:
        """Directories a design may import from: `lib.<x>` from the workspace, `engine` from the plugin."""
        return [str(SCRIPTS_DIR), str(self.root)]
