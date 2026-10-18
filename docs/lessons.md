# Lessons: what works and what doesn't when painting iRacing cars with code

Collected in the sim (Paint Shop screenshots and test sessions), car by car. Per-car specifics live in
`cars/<car>/notes.md`; this page is what carries over.

## Process

- **Calibrate before you draw.** A numbered test paint (`islandtest`) plus screenshots settles in one
  round what reading the PSD only guesses: which island is which, which way it reads, which ones repeat.
- **Preview in the Paint Shop** ("Show Custom Paint"), not in a session. Sessions are for reflections and
  the spec map.
- **One paint per car at a time**; every paint is regenerable from its design file, so `out/` is a cache.
- **Geometry in data, drawing in code.** Where things are (`car.toml`) is fixed once per car; what to draw
  (a design) is written per paint. One position fix applies to every paint.
- **Look before you show.** Open the previews yourself and check them against the brief; iterate on
  parameters first, on code second.

## Design

- **Stripes that cross panels tie the car together**: longitudinal bands that run the whole side, dive into
  the front fender and wrap the rear bumper read as one piece. Check continuity door → quarter and
  hood → banner → roof → engine lid in the 3D view.
- **Satin body + glossy logos** (roughness 140 / 33) reads as one material with the carbon parts
  (roughness ≈127); a glossy body makes the carbon stand out as separate parts. Finish is independent of
  colour, so it works with any palette.
- **One big brand hero** (the logo alone on the roof) beats a lockup on every panel.
- **Big flat shapes survive dense mesh** (door handle recess); detail and text go where the mesh is flat
  (below the handle line, behind the number).
- **Brand logos are shapes, not fonts.** Extract the mask from the official artwork; never redraw a mark
  or set it in a lookalike font.

## Rendering

- **Anti-aliasing is on you.** Pillow draws polygons without smoothing; bumper corners have few texels per
  cm. Draw curves at 4x and downsample with LANCZOS. Never thick `line()` strokes for curves: the joints
  leave spikes; draw the band as a polygon (curve + offset curve).
- **Small text ≥ 19 px** on the 2048 template, and no variable font below ~24 px (Bahnschrift breaks);
  Segoe UI Bold / Consolas Bold for small text.
- **Islands lie.** Expect mirrored sides, upside-down pieces, parts far from their neighbours, one island
  drawn in four places. Colour by position needs per-island fixups.
- **Small parts reuse big parts' texture** (louver slats sampling the sill). Keep the sampled area plain.
- **The number comes from the sim**, bigger than the Number Block, in the Paint Shop colour: keep that
  area clean and tell the user to change the number colour on dark bodies.
- **Inverted axes exist** (smaller x = lower on the Cup's front bumper). Write the direction down.
- **For mirrored pairs of small islands, test all four transforms** before assuming.

## The files

- `car_<id>.tga` 24-bit RLE, `car_spec_<id>.tga` 32-bit RLE, 2048×2048, in `Documents\iRacing\paint\<CarPath>\`.
- Spec map: R metallic, G roughness (white = matte), B clear coat, A specular mask. Stamps (number, iRacing
  decals) inherit the spec under them. Chrome needs a near-white base.
- `.mip` is regenerated when the `.tga` is newer; `Ctrl+R` in a session forces it.
- Only you see a local paint; Trading Paints is how others see it.

Sources: iRacing Paint Textures (iracing.com/painttextures), Trading Paints help (spec map, Showroom
tips, Mattedor, ghosted logos), BeamNG's UV-unwrapping docs for why islands overlap and mirror.
