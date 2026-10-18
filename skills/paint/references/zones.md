# Zones: the vocabulary a design speaks

A calibrated car (`cars/<car>/car.toml`) declares named **zones** (where a sprite goes: centre pixel,
rotation so it reads correctly, fit box) and **pairs** (one name = both sides). Designs call
`rig.place("<zone>", paint, sprite)` and never touch pixel coordinates. The standard vocabulary every
calibrated car should provide:

| Zone | Where | Use it for |
|---|---|---|
| `hood` | front lid, between the vents and the windshield; reads from the front | main logo / lockup |
| `roof` | roof panel; reads from the front | the brand hero (logo alone, big) |
| `doors` (pair) | door centre, both sides | **big flat shapes only** (crosses the handle recess) |
| `doors_low` (pair) | below the handle line, behind the number, both sides | detailed logos, text |
| `wing_centre` | rear wing top face, between the mounts; reads from behind | wordmark / text |
| `wing_ends` (pair) | the two outer ends of the wing top face | small symbols |
| `quarters` (pair) | rear quarter panel sponsor block, both sides | small lockups |
| `front_bumper` | central face of the lower front bumper | a row of small items (flags, badges) |

Plus side helpers in car coordinates (x along the template nose→tail, h = 0 at the sill … 1 at the
belt line): `rig.side_band(base, color, h0, h1)`, `rig.side_polyline(img, [(x, h), ...], color, width, side)`,
`rig.sills(paint, sprite, h=0.14)`; and island groups for flat colour: `rig.islands("accent")` → mirrors,
wing, endplates; `rig.islands("tail")` → the tail parts that the UV places near the nose.

`rig.has_zone(name)` is True when the car has it; `engine.starters.place_if` places only then, so a
starter degrades gracefully on a partially calibrated car.

## `rig.place` options

```python
rig.place("doors_low", paint, sprite, fit=True, max=None, dx=0, dy=0, matte=True, rotate=None)
```

- `fit`: scale the sprite into the zone's `max` box (or `max=(w, h)` passed here). `fit=False` places it as-is.
- `dx`, `dy`: shift in px along the car / **down** the car (the rig knows which way is down on each island).
- `matte`: record the sprite's alpha in the logo mask. The spec map gives that mask `paint.logo_roughness`
  (200 = matte by default, 33 = glossy). Set `matte=False` for things that should keep the body finish.
- `rotate`: override the zone's rotation (rarely needed).

## Elements (`engine.elements`)

| Element | Call | Needs |
|---|---|---|
| `gradient.solid / two_stop / three_stop` | `base = gradient.two_stop(rig, c0, c1, start, end)` | `[axes] length` |
| `gradient.shade_sides(rig, base, floor, span)` | darker toward the sill | `[sides]` |
| `gradient.paint_islands(rig, base, "accent", color)` | flat colour on islands/groups | `[islands]`, `[groups]` |
| `stripes.longitudinal(rig, canvas, bands)` | stripes on both sides, light→dark along the car | `[sides]` |
| `stripes.rear_bumper_wrap(rig, canvas, bands6)` | continue across the rear bumper | `[bumper_rear]` |
| `shark_mouth.draw(rig, paint, dark=, lip=, tooth=, teeth=)` | the mouth + intake walls | `[mouth]` |
| `lockup.horizontal(mark, text, height)` / `stacked` | logo + wordmark sprite | – |
| `plate.with_plate(sprite, pad, radius, color)` | rounded plate behind a sprite | – |
| `flags.row(("BR", "MX"))` / `draw_flag` | framed flag row | – |

Drawing helpers in `engine.draw`: `hex2rgb`, `load_sprite`, `silhouette` (logo as a shape),
`fit`, `render_text(text, height, font="display"|"text"|"mono", color)`, `SSDraw`/`supersampled`/`downsample`
(draw curves at 4x), `band_polygon`/`stroke_band` (curved strokes without joint spikes).

## The Paint object

`paint = rig.to_canvas(base)` → `paint.canvas` (RGBA image you can composite onto), `paint.matte`
(logo mask), `paint.roughness = (mask, values)` for the body finish, `paint.logo_roughness`.
`engine.starters.finish(rig, paint, satin=True)` sets the satin-body/glossy-logo combination.
