"""Two colours easing into each other from the nose to the tail, logo on the roof and doors, wordmark on the wing."""
from engine.draw import render_text
from engine.elements import gradient

from engine.starters import accent_islands, color, finish, mark_or_wordmark, place_if, text

PARAMS = {
    "nose": "#bc8ae1",          # colour at the nose; "" = brand.toml [colors].lilac / primary
    "tail": "#9511dd",          # colour at the tail; "" = brand.toml [colors].primary
    "blend_start": 0.26,        # where the blend begins (fraction of the car length)
    "blend_end": 0.89,          # where it ends
    "accent": "",               # mirrors / wing / endplates; "" = none
    "text": "",
    "text_color": "#e9e4d9",
    "logo_tint": "",
    "logo_height": 400,
    "satin": False,
}
CAR = None


def design(rig, p=PARAMS):
    nose = color(p, "nose", "#bc8ae1") if p.get("nose") else color(p, "lilac", color(p, "primary", "#bc8ae1"))
    tail = color(p, "tail", "#9511dd") if p.get("tail") else color(p, "primary", "#9511dd")
    base = gradient.two_stop(rig, nose, tail, p["blend_start"], p["blend_end"])
    accent_islands(rig, base, color(p, "accent", "#e8a33d") if p.get("accent") else None)
    paint = rig.to_canvas(rig.fixups(base))
    mark = mark_or_wordmark(p, p["logo_height"], p["text_color"], p["logo_tint"])
    place_if(rig, "roof", paint, mark)
    place_if(rig, "doors_low", paint, mark)
    place_if(rig, "wing_centre", paint, render_text(text(p), 60, color=p["text_color"]))
    return finish(rig, paint, p["satin"])
