# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pillow>=12,<13",
#   "numpy>=1.26",
#   "scipy>=1.11",
#   "psd-tools>=1.10",
# ]
# ///
"""iracing-livery: design, render and install custom iRacing paints from the official templates.

    uv run "<plugin>/scripts/paint.py" status
    uv run "<plugin>/scripts/paint.py" setup --workspace <dir> --customer-id 123456 --paint-dir "<Documents>/iRacing/paint"
    uv run "<plugin>/scripts/paint.py" cars [--scan]
    uv run "<plugin>/scripts/paint.py" prepare --car porsche9922cup [--psd <file.psd>]
    uv run "<plugin>/scripts/paint.py" islandtest --car porsche9922cup [--deploy]
    uv run "<plugin>/scripts/paint.py" scaffold --car <carpath> --car-id 169 --name "Porsche 992 GT3 R"
    uv run "<plugin>/scripts/paint.py" designs [--doc]
    uv run "<plugin>/scripts/paint.py" new-design my_livery --from stripes
    uv run "<plugin>/scripts/paint.py" render --car porsche9922cup --design my_livery [--set body=#111111] [--deploy]
    uv run "<plugin>/scripts/paint.py" compare a.tga b.tga [--diff diff.png]

Every subcommand accepts --workspace <dir> (else $IRACING_LIVERY_HOME, else the profile's workspace,
else ~/.iracing-livery). The profile itself always lives at ~/.iracing-livery/profile.json.
Nothing here touches the network. `--deploy` writes only inside <iracing paint dir>/<CarPath>/.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from engine import fonts, paths  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


# ---- context -------------------------------------------------------------------------------------
class Ctx:
    def __init__(self, args):
        self.args = args
        self.profile = paths.load_profile()
        self.ws = paths.Workspace(paths.resolve_workspace(getattr(args, "workspace", None), self.profile))
        dirs = []
        if self.profile.get("fonts_dir"):
            dirs.append(Path(self.profile["fonts_dir"]).expanduser())
        dirs.append(self.ws.fonts)
        fonts.SEARCH_DIRS = [d for d in dirs if d.is_dir()]
        from engine import brand
        brand.WORKSPACE = self.ws.root
        brand.reset()
        for p in self.ws.sys_path_entries():
            if p not in sys.path:
                sys.path.append(p)

    # -- cars --
    def car(self, name: str):
        """(CarSpec, car_dir, source) for a slug / CarPath; errors with the known list."""
        from engine.rig import CarSpec
        hit = self.ws.find_car(name)
        if not hit:
            known = ", ".join(self.ws.car_dirs()) or "(none)"
            raise SystemExit(f"unknown car {name!r}. Known: {known}. New car? run `scaffold --car {name} ...` after `prepare`.")
        d, src = hit
        return CarSpec.load(d / "car.toml"), d, src

    def layers_dir(self, slug: str, override=None) -> Path:
        d = Path(override).expanduser() if override else self.ws.car_work(slug)["layers"]
        if not d.is_dir() or not any(d.glob("*.png")):
            raise SystemExit(f"no exported layers for {slug} in {d}\n"
                             f"  -> put the PSD in {self.ws.template_dir(slug)} and run: paint.py prepare --car {slug}")
        return d

    def template(self, spec, layers_dir=None):
        from engine.template import Template
        return Template(self.layers_dir(spec.slug, layers_dir), spec.min_island_area)

    def cid(self) -> str:
        cid = getattr(self.args, "cid", None) or self.profile.get("customer_id")
        if not cid:
            raise SystemExit("no customer id: pass --cid or run `setup --customer-id <id>` "
                             "(iracing.com -> My Account shows it; it's also the number in car_<id>.tga)")
        return str(cid)

    def deploy_dir(self, spec) -> Path:
        override = getattr(self.args, "deploy_dir", None)
        if override:
            return Path(override).expanduser()
        base = self.profile.get("iracing_paint_dir")
        if not base:
            cands = paths.paint_dir_candidates()
            if len(cands) == 1:
                base = cands[0]
            else:
                raise SystemExit("no iRacing paint folder in the profile: run `setup --paint-dir <Documents>/iRacing/paint` "
                                 f"(candidates found: {[str(c) for c in cands] or 'none'})")
        return Path(base).expanduser() / spec.car_path


# ---- helpers -------------------------------------------------------------------------------------
def parse_set(items, defaults: dict) -> dict:
    """--set key=value ... with values coerced to the type of the design's default."""
    out = {}
    for item in items or []:
        if "=" not in item:
            raise SystemExit(f"--set expects key=value, got {item!r}")
        k, v = item.split("=", 1)
        k = k.strip(); v = v.strip()
        d = defaults.get(k)
        if isinstance(d, bool):
            out[k] = v.lower() in ("1", "true", "yes", "on")
        elif isinstance(d, int) and not isinstance(d, bool):
            out[k] = int(float(v))
        elif isinstance(d, float):
            out[k] = float(v)
        elif isinstance(d, (list, tuple)):
            try:
                out[k] = type(d)(json.loads(v))
            except json.JSONDecodeError:
                out[k] = type(d)(x.strip() for x in v.split(","))
        else:
            if d is None and k not in defaults:
                print(f"note: {k!r} is not a PARAMS key of this design; set anyway", file=sys.stderr)
            out[k] = v
    return out


def load_design(path: Path):
    if str(path.parent) not in sys.path:          # starters share designs/_common.py
        sys.path.append(str(path.parent))
    spec = importlib.util.spec_from_file_location(f"livery_design_{path.stem}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fn = getattr(mod, "design", None)
    if fn is None or not callable(fn):
        raise SystemExit(f"{path} has no `design(rig, params)` function")
    return mod, fn, dict(getattr(mod, "PARAMS", {})), getattr(mod, "CAR", None)


def design_meta(path: Path) -> dict:
    try:
        mod, fn, params, car = load_design(path)
        doc = (mod.__doc__ or fn.__doc__ or "").strip().splitlines()
        return {"name": path.stem, "params": params, "car": car, "doc": doc[0] if doc else "", "error": None}
    except SystemExit as e:
        return {"name": path.stem, "params": {}, "car": None, "doc": "", "error": str(e)}
    except Exception as e:  # a broken design must not break the listing
        return {"name": path.stem, "params": {}, "car": None, "doc": "", "error": f"{type(e).__name__}: {e}"}


def fmt_param(v):
    if isinstance(v, str):
        return f'"{v}"'
    return json.dumps(v) if isinstance(v, (list, tuple, dict)) else str(v)


def cmd_version(tool):
    try:
        return subprocess.run([tool, "--version"], capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:
        return None


# ---- commands ------------------------------------------------------------------------------------
def cmd_status(ctx: Ctx):
    p = ctx.profile
    print(f"profile      {paths.PROFILE_PATH} {'(exists)' if paths.PROFILE_PATH.exists() else '(not created yet: run setup)'}")
    print(f"workspace    {ctx.ws.root} {'(exists)' if ctx.ws.root.is_dir() else '(missing)'}")
    print(f"customer_id  {p.get('customer_id') or '-'}")
    pd = p.get("iracing_paint_dir")
    print(f"paint dir    {pd or '-'} {'(ok)' if pd and Path(pd).expanduser().is_dir() else ''}")
    if not pd:
        for c in paths.paint_dir_candidates():
            print(f"             candidate: {c}")
    print(f"main car     {p.get('main_car') or '-'}")
    print(f"brand.toml   {'yes' if ctx.ws.brand_toml.exists() else 'no'}")
    print(f"python       {platform.python_version()}   uv {cmd_version('uv') or 'not on PATH'}")
    print(f"plugin root  {paths.PLUGIN_ROOT}")
    print()
    cmd_cars(ctx)


def car_status_row(ctx: Ctx, slug: str, d: Path, src: str) -> dict:
    from engine.rig import CarSpec
    spec = CarSpec.load(d / "car.toml")
    work = ctx.ws.car_work(slug)
    psd = ctx.ws.find_psd(slug, spec.template_psd)
    layers = work["layers"].is_dir() and any(work["layers"].glob("*.png"))
    islands = (work["islands"] / "islands.json").exists() or (d / "islands.json").exists()
    from engine.islands import panel_names
    named = len(panel_names(d / "panels.md"))
    return {"slug": slug, "name": spec.name, "car_path": spec.car_path, "source": src, "status": spec.status,
            "template": bool(psd), "layers": bool(layers), "islands": bool(islands), "panels_named": named,
            "zones": len(spec.zones), "dir": str(d)}


def cmd_cars(ctx: Ctx):
    rows = [car_status_row(ctx, slug, d, src) for slug, (d, src) in ctx.ws.car_dirs().items()]
    if ctx.args.json:
        print(json.dumps(rows, indent=2)); return
    if not rows:
        print("no cars known (plugin cars/ and workspace cars/ are empty)")
    else:
        print(f"{'car':18} {'status':11} {'psd':4} {'layers':6} {'islands':7} {'named':5} {'zones':5} source   name")
        for r in rows:
            print(f"{r['slug']:18} {r['status']:11} {'yes' if r['template'] else '-':4} {'yes' if r['layers'] else '-':6} "
                  f"{'yes' if r['islands'] else '-':7} {r['panels_named']:5} {r['zones']:5} {r['source']:8} {r['name']}")
    if ctx.args.scan:
        base = ctx.profile.get("iracing_paint_dir")
        cands = [Path(base).expanduser()] if base else paths.paint_dir_candidates()
        for c in cands:
            if c.is_dir():
                print(f"\nCarPaths in {c} (each folder = one car you have painted or iRacing created):")
                for d in sorted(x for x in c.iterdir() if x.is_dir()):
                    tgas = [t.name for t in d.glob("car_*.tga")]
                    print(f"  {d.name:28} {' '.join(tgas)}")


def cmd_profile(ctx: Ctx):
    p = dict(ctx.profile)
    changed = False
    for item in ctx.args.set or []:
        k, v = item.split("=", 1)
        p[k.strip()] = v.strip()
        changed = True
    if changed:
        paths.save_profile(p)
        print(f"wrote {paths.PROFILE_PATH}")
    print(json.dumps(p, indent=2))


def cmd_setup(ctx: Ctx):
    p = dict(ctx.profile)
    a = ctx.args
    if a.workspace:
        p["workspace"] = str(Path(a.workspace).expanduser().resolve())
    if a.customer_id:
        p["customer_id"] = str(a.customer_id)
    if a.paint_dir:
        pd = Path(a.paint_dir).expanduser()
        if not pd.is_dir():
            raise SystemExit(f"paint dir does not exist: {pd}")
        p["iracing_paint_dir"] = str(pd.resolve())
    if a.main_car:
        p["main_car"] = paths.slugify(a.main_car)
    if a.fonts_dir:
        p["fonts_dir"] = str(Path(a.fonts_dir).expanduser().resolve())
    p.setdefault("workspace", str(ctx.ws.root))
    paths.save_profile(p)
    ws = paths.Workspace(Path(p["workspace"])).ensure()
    if not ws.brand_toml.exists():
        ws.brand_toml.write_text(BRAND_TEMPLATE, encoding="utf-8")
    print(f"profile   {paths.PROFILE_PATH}")
    print(f"workspace {ws.root} (templates/ work/ cars/ designs/ lib/ assets/ fonts/)")
    print(f"brand     {ws.brand_toml}")
    print(json.dumps(p, indent=2))


BRAND_TEMPLATE = '''# Your brand, read by every design (engine.brand). Paths are relative to this workspace.
text = "@YOURNAME"           # wordmark text used by starters (sponsor, stripes ...)
# logo = "assets/logo.png"   # a PNG with transparency (or a dark logo on white); used as a SHAPE
# logo_mono = "assets/logo-mono.png"

[colors]
primary = "#9511dd"
accent  = "#e8a33d"
body    = "#0a0e13"
'''


def cmd_prepare(ctx: Ctx):
    from engine import islands as isl
    from engine import psd as psdmod
    from engine.template import Template
    a = ctx.args
    slug = paths.slugify(a.car)
    hit = ctx.ws.find_car(slug)
    spec = None
    if hit:
        from engine.rig import CarSpec
        spec = CarSpec.load(hit[0] / "car.toml")
    min_area = a.min_area or (spec.min_island_area if spec else 6000)
    work = ctx.ws.car_work(slug)
    psd = Path(a.psd).expanduser() if a.psd else ctx.ws.find_psd(slug, spec.template_psd if spec else None)
    if a.layers_dir:
        src = Path(a.layers_dir).expanduser()
        work["layers"].mkdir(parents=True, exist_ok=True)
        n = 0
        for f in src.glob("*.png"):
            shutil.copy2(f, work["layers"] / f.name); n += 1
        print(f"copied {n} layer PNGs from {src}")
    elif psd and psd.exists() and (a.psd or a.force or not (work["layers"].is_dir() and any(work["layers"].glob("*.png")))):
        print(f"exporting layers from {psd.name} ...")
        work["layers"].mkdir(parents=True, exist_ok=True)
        (work["root"] / "layers.txt").write_text(psdmod.inspect(psd), encoding="utf-8")
        written = psdmod.export_layers(psd, work["layers"], a.layers or None)
        print(f"wrote {len(written)} layers to {work['layers']} (tree in layers.txt)")
        try:
            n = psdmod.contact_sheet(psd, work["preview"] / "patterns_sheet.png")
            if n:
                print(f"wrote {work['preview'] / 'patterns_sheet.png'} ({n} patterns)")
        except Exception as e:
            print(f"note: no contact sheet ({e})")
    elif not (work["layers"].is_dir() and any(work["layers"].glob("*.png"))):
        raise SystemExit(f"no PSD for {slug}: put the official template (iracing.com/painttextures, member login) in\n"
                         f"  {ctx.ws.template_dir(slug)}\n  or pass --psd <file>. (Templates are iRacing's: never share them.)")
    T = Template(work["layers"], min_area, cache=True)
    manifest = T.manifest()
    (work["layers"] / "manifest.json").write_text(json.dumps({"min_island_area": min_area, "roles": manifest}, indent=2), encoding="utf-8")
    missing = [r for r in ("mask", "wire", "spec_r_base", "spec_g_base", "spec_b_base") if not manifest.get(r)]
    if missing:
        raise SystemExit(f"layers exported but these roles were not found: {missing}; see {work['root'] / 'layers.txt'}")
    if not manifest.get("spec_alpha"):
        print("note: this template has no Spec Alpha layer; the spec map alpha will be 255 on the paintable area, 0 elsewhere")
    info = isl.compute(T)
    out = isl.write_map(T, info, work["islands"], downscale=1024)
    print(f"{len(info)} islands (min area {min_area}) -> {out['json']}, {out['map']}")
    ref = (hit[0] / "islands.json") if hit else None
    if ref and ref.exists():
        old = isl.load_info(ref)
        if set(old) != set(info) or any(old[k]["bbox"] != info[k]["bbox"] for k in info if k in old):
            print(f"WARNING: islands differ from the calibrated {ref} (template updated?). "
                  f"Check seeds in car.toml: `paint.py cars` and a render will report mismatches.")
        else:
            print("islands match the calibrated islands.json")
    print("next: `islandtest --car {0} --deploy`, screenshot the Paint Shop, fill panels.md".format(slug)
          if not spec or spec.status != "calibrated" else f"ready: `render --car {slug} --design <name>`")


def cmd_islandtest(ctx: Ctx):
    from engine import islands as isl
    spec, d, _ = ctx.car(ctx.args.car)
    T = ctx.template(spec, ctx.args.layers_dir)
    names = isl.panel_names(d / "panels.md")
    out = ctx.ws.car_work(spec.slug)["out"] / "islandtest"
    res = isl.islandtest(T, out, ctx.cid(), names, title=spec.name)
    print(f"wrote {out} ({res['count']} islands): {res['paint'].name}, {res['spec'].name}, legend.png, preview_wire.png")
    if ctx.args.deploy:
        dep = ctx.deploy_dir(spec); dep.mkdir(parents=True, exist_ok=True)
        for key in ("paint", "spec"):
            shutil.copy2(res[key], dep / res[key].name)
        print(f"deployed to {dep} -> open the Paint Shop (Show Custom Paint) or Ctrl+R in the sim, then screenshot")


def cmd_scaffold(ctx: Ctx):
    from engine import islands as isl
    a = ctx.args
    slug = paths.slugify(a.car)
    car_path = a.car_path or a.car
    dest = ctx.ws.cars / slug
    if (dest / "car.toml").exists() and not a.force:
        raise SystemExit(f"{dest / 'car.toml'} exists (use --force to overwrite)")
    work = ctx.ws.car_work(slug)
    info_path = work["islands"] / "islands.json"
    if not info_path.exists():
        raise SystemExit(f"no {info_path}: run `prepare --car {slug}` first")
    info = isl.load_info(info_path)
    size = 2048
    dest.mkdir(parents=True, exist_ok=True)
    lines = [f"# {a.name or car_path} - calibration scaffold (fill as the islandtest screenshots come in; see docs/new-car.md)",
             "", "[car]", f'slug = "{slug}"', f'car_path = "{car_path}"']
    if a.car_id:
        lines.append(f"car_id = {int(a.car_id)}")
    lines += [f'name = "{a.name or car_path}"']
    psd = ctx.ws.find_psd(slug)
    if psd:
        lines.append(f'template_psd = "{psd.name}"')
    lines += [f"min_island_area = {a.min_area or 6000}", f"size = {size}", 'status = "islands"', "",
              "[axes]", f"length = [0, {size}]        # TODO: x of the nose and of the tail on the side islands",
              f"centre_y = {size // 2}         # TODO: centreline y of the hood/roof band", "",
              "# One entry per island found by `prepare` (id = number in islands_map.png, seed = a pixel inside it).",
              "# Rename them as the screenshots confirm what they are (roof, side_r, side_l, hood, wing ...).",
              "[islands]"]
    for k in sorted(info):
        v = info[k]
        lines.append(f"island_{k:02d} = {{ id = {k}, seed = [{v['label_xy'][0]}, {v['label_xy'][1]}] }}   # bbox {v['bbox']}, area {v['area']}")
    lines += ["", "[groups]", "# tail = [\"...\"]", "", "# [[fixups]]", "# targets = \"tail\"", "# sample = [x, y]", "",
              "[sides]", "# x_range = [190, 1840]", "# [sides.R]", "# island = \"side_r\"", "# sill = 633", "# belt = 1149",
              "# louver = \"louver_r\"", "# car_down_y = -1", "# [sides.L] ...", "",
              "[zones]", "# hood = { centre = [x, y], rotate = -90, max = [430, 140] }",
              "# doors_low_r = { centre = [x, y], rotate = 180, max = [280, 110], car_down_y = -1 }", "",
              "[pairs]", "# doors_low = [\"door_low_r\", \"door_low_l\"]", "", "[preview_crops]",
              "# hood = [x0, y0, x1, y1]", ""]
    (dest / "car.toml").write_text("\n".join(lines), encoding="utf-8")
    md = [f"# {a.name or car_path} - panel map (car_id {a.car_id or '?'}, CarPath `{car_path}`)", "",
          "Numbering = `islands_map.png` (template px, origin top-left). Confidence: ✅ confirmed in the sim with the",
          "islandtest paint; ⚠️ inferred from the template, confirm.", "",
          "| # | Panel | bbox (x0,y0,x1,y1) | Conf. | Notes |", "|---|-------|--------------------|-------|-------|"]
    for k in sorted(info):
        b = info[k]["bbox"]
        md.append(f"| {k} |  | {b[0]},{b[1]} – {b[2]},{b[3]} | ⚠️ |  |")
    md += ["", "## Validated in the sim", "", "- (date) islandtest round 1: ...", ""]
    (dest / "panels.md").write_text("\n".join(md), encoding="utf-8")
    (dest / "notes.md").write_text(f"# {a.name or car_path} - what works / what doesn't\n\n- (nothing yet)\n", encoding="utf-8")
    for f in ("islands.json", "islands_map_1024.png"):
        if (work["islands"] / f).exists():
            shutil.copy2(work["islands"] / f, dest / ("islands_map.png" if f.startswith("islands_map") else f))
    print(f"scaffolded {dest}: car.toml ({len(info)} islands), panels.md, notes.md, islands.json, islands_map.png")
    print(f"next: `islandtest --car {slug} --deploy`, screenshot the Paint Shop, name the islands")


def cmd_designs(ctx: Ctx):
    files = ctx.ws.design_files()
    metas = [(name, src, design_meta(path)) for name, (path, src) in files.items()]
    if ctx.args.json:
        print(json.dumps([{"name": n, "source": s, **m} for n, s, m in metas], indent=2)); return
    if ctx.args.doc:
        print("| Starter | Car | What it does | Parameters (default) |")
        print("|---|---|---|---|")
        for n, s, m in metas:
            if s != "plugin":
                continue
            params = ", ".join(f"`{k}` = {fmt_param(v)}" for k, v in m["params"].items()) or "-"
            print(f"| `{n}` | {m['car'] or 'any calibrated'} | {m['doc']} | {params} |")
        return
    if not metas:
        print("no designs found"); return
    for n, s, m in metas:
        tag = "starter" if s == "plugin" else s
        if m["error"]:
            print(f"{n:24} [{tag}] BROKEN: {m['error']}"); continue
        print(f"{n:24} [{tag}] {m['doc']}")
        for k, v in m["params"].items():
            print(f"{'':24}   {k} = {fmt_param(v)}")
        if m["car"]:
            print(f"{'':24}   car: {m['car']}")


def cmd_new_design(ctx: Ctx):
    a = ctx.args
    name = a.name.replace("-", "_")
    src = ctx.ws.find_design(a.from_)
    if not src:
        raise SystemExit(f"unknown starter {a.from_!r}; see `designs`")
    dest = ctx.ws.designs / f"{name}.py"
    if dest.exists() and not a.force:
        raise SystemExit(f"{dest} exists (use --force to overwrite)")
    ctx.ws.designs.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src[0], dest)
    print(f"created {dest} from {src[0].name} - edit PARAMS / design(), then: render --car <car> --design {name}")


def cmd_render(ctx: Ctx):
    from engine.rig import Paint, Rig
    a = ctx.args
    hit = ctx.ws.find_design(a.design)
    if not hit:
        known = ", ".join(ctx.ws.design_files()) or "(none)"
        raise SystemExit(f"unknown design {a.design!r}. Known: {known}")
    dpath, dsrc = hit
    mod, fn, params, car_req = load_design(dpath)
    car_name = a.car or car_req or ctx.profile.get("main_car")
    if not car_name:
        raise SystemExit("which car? pass --car <slug> (or set main_car in the profile)")
    spec, cdir, _ = ctx.car(car_name)
    if car_req and paths.slugify(car_req) != spec.slug:
        print(f"warning: design {dpath.stem} was written for {car_req}, rendering on {spec.slug}", file=sys.stderr)
    params.update(parse_set(a.set, params))
    T = ctx.template(spec, a.layers_dir)
    rig = Rig(spec, T)
    result = fn(rig, params) if fn.__code__.co_argcount >= 2 else fn(rig)
    if isinstance(result, dict):                       # legacy shape: dict(canvas, roughness_map, matte_value)
        result = Paint(canvas=result["canvas"], matte=getattr(rig, "_legacy_matte", None),
                       roughness=result.get("roughness_map"), logo_roughness=result.get("matte_value", 200.0))
    if not isinstance(result, Paint):
        raise SystemExit(f"design() must return the Paint it got from rig.to_canvas(), got {type(result).__name__}")
    name = a.name or dpath.stem.replace("_", "-")
    out = Path(a.out).expanduser() if a.out else ctx.ws.car_work(spec.slug)["out"] / name
    files = rig.export(result, out, ctx.cid(), deploy=ctx.deploy_dir(spec) if a.deploy else None)
    print(f"wrote {out}")
    for k, v in files.items():
        if k != "deployed_to":
            print(f"  {Path(v).name}")
    if "deployed_to" in files:
        print(f"deployed to {files['deployed_to']} -> Paint Shop (Show Custom Paint) or Ctrl+R in the sim")
    if not a.deploy:
        print("(not installed in the sim: add --deploy when the previews look right)")


def cmd_compare(ctx: Ctx):
    from engine.tga import compare
    res = compare(ctx.args.a, ctx.args.b, tol=ctx.args.tol, diff_png=ctx.args.diff)
    print(json.dumps(res, indent=2))
    sys.exit(0 if res.get("n_diff") == 0 else 1)


def cmd_inspect(ctx: Ctx):
    from engine import psd as psdmod
    print(psdmod.inspect(Path(ctx.args.psd).expanduser()))


# ---- parser --------------------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="paint.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--workspace", default=argparse.SUPPRESS,
                        help="workspace dir (else $IRACING_LIVERY_HOME, profile, ~/.iracing-livery)")
    p.add_argument("--workspace", default=None, help=argparse.SUPPRESS)
    sub0 = p.add_subparsers(dest="cmd", required=True)

    class _Sub:
        def add_parser(self, name, **kw):
            return sub0.add_parser(name, parents=[common], **kw)

    sub = _Sub()

    s = sub.add_parser("status", help="profile, workspace, tools, cars"); s.set_defaults(fn=cmd_status, json=False, scan=False)
    s = sub.add_parser("cars", help="known cars and their calibration status")
    s.add_argument("--scan", action="store_true", help="also list the CarPath folders in the iRacing paint dir")
    s.add_argument("--json", action="store_true"); s.set_defaults(fn=cmd_cars)
    s = sub.add_parser("profile", help="show / set profile values (customer_id, iracing_paint_dir, main_car, workspace, fonts_dir)")
    s.add_argument("--set", action="append", metavar="KEY=VALUE"); s.set_defaults(fn=cmd_profile)
    s = sub.add_parser("setup", help="write the profile and create the workspace tree")
    s.add_argument("--customer-id"); s.add_argument("--paint-dir"); s.add_argument("--main-car"); s.add_argument("--fonts-dir")
    s.set_defaults(fn=cmd_setup)
    s = sub.add_parser("prepare", help="export layers from the PSD and compute the UV islands")
    s.add_argument("--car", required=True); s.add_argument("--psd"); s.add_argument("--layers-dir", help="reuse already exported PNGs")
    s.add_argument("--layers", nargs="*", help="layer-name substrings to export (default: the useful set)")
    s.add_argument("--min-area", type=int); s.add_argument("--force", action="store_true", help="re-export even if layers exist")
    s.set_defaults(fn=cmd_prepare)
    s = sub.add_parser("islandtest", help="calibration paint: every island numbered")
    s.add_argument("--car", required=True); s.add_argument("--cid"); s.add_argument("--deploy", action="store_true")
    s.add_argument("--deploy-dir"); s.add_argument("--layers-dir"); s.set_defaults(fn=cmd_islandtest)
    s = sub.add_parser("scaffold", help="create cars/<car>/ in the workspace from the computed islands")
    s.add_argument("--car", required=True, help="CarPath or slug"); s.add_argument("--car-path"); s.add_argument("--car-id")
    s.add_argument("--name"); s.add_argument("--min-area", type=int); s.add_argument("--force", action="store_true")
    s.set_defaults(fn=cmd_scaffold)
    s = sub.add_parser("designs", help="list designs (starters + workspace)")
    s.add_argument("--doc", action="store_true", help="markdown catalogue of the starters")
    s.add_argument("--json", action="store_true"); s.set_defaults(fn=cmd_designs)
    s = sub.add_parser("new-design", help="copy a starter into the workspace")
    s.add_argument("name"); s.add_argument("--from", dest="from_", default="solid"); s.add_argument("--force", action="store_true")
    s.set_defaults(fn=cmd_new_design)
    s = sub.add_parser("render", help="render a design for a car (TGA + spec + previews)")
    s.add_argument("--car"); s.add_argument("--design", required=True); s.add_argument("--set", action="append", metavar="KEY=VALUE")
    s.add_argument("--cid"); s.add_argument("--deploy", action="store_true"); s.add_argument("--deploy-dir")
    s.add_argument("--out"); s.add_argument("--name", help="output folder name (default: the design name)")
    s.add_argument("--layers-dir"); s.set_defaults(fn=cmd_render)
    s = sub.add_parser("compare", help="pixel comparison of two TGA/PNG files")
    s.add_argument("a"); s.add_argument("b"); s.add_argument("--tol", type=int, default=0); s.add_argument("--diff")
    s.set_defaults(fn=cmd_compare)
    s = sub.add_parser("inspect", help="print a PSD's layer tree"); s.add_argument("psd"); s.set_defaults(fn=cmd_inspect)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    ctx = Ctx(args)
    args.fn(ctx)


if __name__ == "__main__":
    main()
