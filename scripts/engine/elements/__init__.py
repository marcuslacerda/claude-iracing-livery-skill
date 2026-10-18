"""Reusable, brand-free motifs. Every element is a function `fn(rig, paint_or_canvas, **options)` that
draws onto the paint using the car's calibration (zones, sides, extra sections in car.toml) and raises
a clear CalibrationError when the car lacks what it needs.

    gradient     nose-to-tail colour ramps, side shading
    stripes      longitudinal stripes that dive into the fender, and their wrap across the rear bumper
    shark_mouth  the front-bumper mouth (lens, lips, teeth, dark intakes, intake walls)
    lockup       logo + wordmark in one sprite
    plate        rounded plates behind sprites (legibility on busy backgrounds)
    flags        simplified national flags and a framed row of them
"""
from . import flags, gradient, lockup, plate, shark_mouth, stripes  # noqa: F401

__all__ = ["flags", "gradient", "lockup", "plate", "shark_mouth", "stripes"]
