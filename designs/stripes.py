"""Three longitudinal stripes that run the whole side, dive into the front fender and wrap the rear bumper; logo on the roof and doors."""
from engine.draw import render_text
from engine.elements import gradient, stripes

from engine.starters import accent_islands, color, finish, mark_or_wordmark, place_if, text

PARAMS = {
    "body": "#0a0e13",          # body colour; "" = brand.toml [colors].body
    "stripe": "#e8a33d",        # centre band colour (at the nose); "" = brand.toml [colors].accent
    "stripe_tail": "#a86a1c",   # centre band colour at the tail (fades along the car)
    "outer": "#86145a",         # the two outer bands
    "outer_tail": "#6e0c46",
    "widths": [22, 84, 30],     # px of the three bands (outer, centre, outer)
    "height": 0.50,             # stripe height on the door (0 = sill, 1 = belt line)
    "dive": True,               # dive into the front fender (else flat along the car)
    "wrap_rear": True,          # continue across the rear bumper when the car is calibrated for it
    "accent": "",               # mirrors / wing / endplates; "" = same as `stripe`
    "text": "",
    "text_color": "#e9e4d9",
    "logo_tint": "",
    "logo_height": 400,
    "satin": True,
}
CAR = None


def design(rig, p=PARAMS):
    body = color(p, "body", "#0a0e13")
    main = color(p, "stripe", "#e8a33d") if p.get("stripe") else color(p, "accent", "#e8a33d")
    base = gradient.solid(rig, body)
    accent_islands(rig, base, color(p, "accent", "#e8a33d") if p.get("accent") else main)
    paint = rig.to_canvas(rig.fixups(base))
    if rig.spec.sides:
        h = float(p["height"])
        knots = ([(200, h - 0.38), (420, h - 0.28), (760, h), (1250, h), (1600, h - 0.13), (1840, h - 0.20)]
                 if p["dive"] else [(190, h), (1840, h)])
        path = stripes.smooth_path(knots) if p["dive"] else knots
        outer, outer_tail = color(p, "outer", "#86145a"), color(p, "outer_tail", "#6e0c46")
        main_tail = color(p, "stripe_tail", "#a86a1c")
        bands = stripes.trio(path, [(outer, outer_tail), (main, main_tail), (outer, outer_tail)], widths=tuple(p["widths"]))
        stripes.longitudinal(rig, paint.canvas, bands)
        if p["wrap_rear"] and rig.spec.section("bumper_rear"):
            w = p["widths"]
            stripes.rear_bumper_wrap(rig, paint.canvas, [(-0.12, w[0], outer_tail), (0.0, w[1], main_tail), (0.13, w[2], outer_tail)],
                                     h_end=0.22)
    mark = mark_or_wordmark(p, p["logo_height"], p["text_color"], p["logo_tint"])
    place_if(rig, "roof", paint, mark)
    place_if(rig, "doors_low", paint, mark)
    place_if(rig, "wing_centre", paint, render_text(text(p), 60, color=p["text_color"]))
    return finish(rig, paint, p["satin"])
