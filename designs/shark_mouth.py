"""A shark mouth on the front bumper (lips, teeth, dark intakes) over a two-tone body, satin finish with glossy logos."""
from engine.draw import render_text
from engine.elements import gradient, shark_mouth

from engine.starters import accent_islands, color, finish, mark_or_wordmark, place_if, text

PARAMS = {
    "nose": "#bc8ae1",          # body colour at the nose; "" = brand.toml [colors].lilac / primary
    "tail": "#9511dd",          # body colour at the tail; "" = brand.toml [colors].primary
    "mouth": "#0c0a10",         # the dark interior
    "lip": "#6e0c46",           # both lips
    "tooth": "#f0ece4",         # teeth (the tow-hook tooth is `hook_tooth`)
    "hook_tooth": "#c81e1e",
    "teeth": True,
    "accent": "#e8a33d",        # mirrors / wing / endplates; "" = none
    "text": "",
    "text_color": "#0a0e13",
    "logo_tint": "",
    "logo_height": 400,
    "satin": True,
}
CAR = None   # needs a car with [mouth] calibration (porsche9922cup today)


def design(rig, p=PARAMS):
    nose = color(p, "nose", "#bc8ae1") if p.get("nose") else color(p, "lilac", color(p, "primary", "#bc8ae1"))
    tail = color(p, "tail", "#9511dd") if p.get("tail") else color(p, "primary", "#9511dd")
    base = gradient.two_stop(rig, nose, tail, 0.26, 0.89)
    accent_islands(rig, base, color(p, "accent", "#e8a33d") if p.get("accent") else None)
    paint = rig.to_canvas(rig.fixups(base))
    shark_mouth.draw(rig, paint, dark=color(p, "mouth", "#0c0a10"), lip=color(p, "lip", "#6e0c46"),
                     tooth=color(p, "tooth", "#f0ece4"), hook_tooth=color(p, "hook_tooth", "#c81e1e"),
                     wall_body=nose, teeth=bool(p["teeth"]))
    mark = mark_or_wordmark(p, p["logo_height"], p["text_color"], p["logo_tint"])
    place_if(rig, "roof", paint, mark)
    place_if(rig, "doors_low", paint, mark)
    place_if(rig, "wing_centre", paint, render_text(text(p), 60, color=p["text_color"]))
    return finish(rig, paint, p["satin"])
