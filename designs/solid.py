"""One flat body colour, accent on mirrors/wing, the logo on the hood and doors, wordmark on the wing."""
from engine.draw import render_text
from engine.elements import gradient

from engine.starters import accent_islands, color, finish, mark_or_wordmark, place_if, text

PARAMS = {
    "body": "#1a1a1a",          # body colour (hex); "" = brand.toml [colors].body
    "accent": "#e8a33d",        # mirrors / wing / endplates; "" = none
    "text": "",                 # wordmark; "" = brand.toml text
    "text_color": "#ffffff",
    "logo_tint": "",            # tint the logo shape with this colour; "" = logo as-is
    "logo_height": 300,         # px on the 2048 template before fitting into each zone
    "satin": False,             # satin body (roughness 140) with glossy logos (33)
}
CAR = None   # any calibrated car


def design(rig, p=PARAMS):
    base = gradient.solid(rig, color(p, "body", "#1a1a1a"))
    accent_islands(rig, base, color(p, "accent", "#e8a33d") if p.get("accent") != "" else None)
    paint = rig.to_canvas(rig.fixups(base))
    mark = mark_or_wordmark(p, p["logo_height"], p["text_color"], p["logo_tint"])
    place_if(rig, "hood", paint, mark)
    place_if(rig, "doors_low", paint, mark)
    place_if(rig, "wing_centre", paint, render_text(text(p), 60, color=p["text_color"]))
    return finish(rig, paint, p["satin"])
