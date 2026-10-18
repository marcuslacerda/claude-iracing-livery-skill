"""The sponsor pack: big logo on the hood and doors, wordmark on the wing and rear quarters, a sill band with text."""
from PIL import Image

from engine.draw import render_text

from engine.starters import accent_islands, color, finish, mark_or_wordmark, place_if, text
from engine.elements import gradient

PARAMS = {
    "body": "#ffffff",          # body colour; "" = brand.toml [colors].body
    "accent": "#9511dd",        # mirrors / wing / endplates; "" = none
    "logo_tint": "",            # tint the logo shape (e.g. "#ffffff" on a dark body); "" = as-is
    "logo_height": 400,
    "text": "",                 # wordmark; "" = brand.toml text
    "text_color": "#0a0e13",
    "sill_text": "",            # text on the rocker-panel band; "" = none
    "sill_band": "#0a0e13",     # band colour
    "sill_text_color": "#ffffff",
    "satin": False,
}
CAR = None


def design(rig, p=PARAMS):
    base = gradient.solid(rig, color(p, "body", "#ffffff"))
    accent_islands(rig, base, color(p, "accent", "#9511dd") if p.get("accent") else None)
    paint = rig.to_canvas(rig.fixups(base))
    mark = mark_or_wordmark(p, p["logo_height"], p["text_color"], p["logo_tint"])
    place_if(rig, "hood", paint, mark)
    place_if(rig, "doors", paint, mark)                      # big flat marks survive the door-handle recess
    word = render_text(text(p), 60, color=p["text_color"])
    place_if(rig, "wing_centre", paint, word)
    place_if(rig, "quarters", paint, word)
    if p.get("sill_text") and rig.spec.sides:
        txt = render_text(p["sill_text"], 19, font="text", color=p["sill_text_color"])
        band = Image.new("RGBA", (max(580, txt.width + 40), 38), tuple(color(p, "sill_band", "#0a0e13")) + (255,))
        band.alpha_composite(txt, ((band.width - txt.width) // 2, (38 - txt.height) // 2))
        rig.sills(paint, band, h=0.14)
    return finish(rig, paint, p["satin"])
