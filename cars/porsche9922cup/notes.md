# Porsche 911 GT3 Cup (992.2) — what works, what doesn't

Everything below was learned in the sim (screenshots of the Paint Shop and test sessions) while painting
this car. Most of it generalises: see `docs/lessons.md` for the cross-car rules.

## Works

- **Longitudinal stripes that dive into the fender** (the `stripes` element / starter): they tie the door,
  quarter and bumper together and the car reads as one piece. Checked across panels in the 3D Paint Shop
  (door → quarter, hood → banner → roof → engine lid).
- **Near-black satin body (10,14,19 at roughness 140) with glossy logos (roughness 33).** The template's
  carbon parts (splitter, diffuser, ducts, roughness ≈127, near-black) become the same material as the body,
  so the car reads as a whole. With a glossy body (roughness 33) the carbon stands out as separate parts.
  Roughness is independent of colour: "satin + glossy logos" works with any palette.
- **The shark mouth** (`shark_mouth` element): a lens open at the centre and closed near the tyres; the upper
  lip starts at the headlight base and falls, the lower lip starts at the splitter and rises; teeth scale with
  the opening; the intakes are painted as a dark interior; the lower teeth continue onto islands 20/21.
- **Logo alone on the roof** as the brand hero (reads from the front, rotate -90), hood kept clean.
- **Big flat shapes on the doors** survive the door-handle recess; detailed logos and text go below the
  handle line and behind the number (`doors_low`).

- **Centre stripes over the top of the car** (hood → banner → roof → lid → wing → rear bumper, plus the
  lower front bumper): measure them on the official `car_pattern_002` axis (`[stripe_axes]`) and they line
  up across every seam, centred or offset.
- **Pop art cells with an outline on every panel seam**: black lines on the UV island edges become the
  car's panel lines, so the cells and the panels read as one drawing.
- **Weathering where a real car gets dirty**: rust and soot concentrated on the gunmetal bumpers, sills,
  behind the rear wheels and around the hood vents reads as an old ship; spread evenly it reads as noise.
- **Real metallic** (spec R 120) with roughness 40 gives the "wet metal" look; keep neon and code at
  metallic 0 and roughness ~4.
- **Frame the number** with a white circle at (842, h 0.415), r=104: the sim's number fits inside.

## Doesn't work / watch out

- **Front-fender art above h≈0.55** (x 300–450): another island starts there, art gets cut.
- **Art over the hood vents** (x 405–505): they are holes on the car; use the free lid x 505–690 and the
  gap between the vents.

- **Islands lie.** The right side is drawn upside down; the wing endplates sit in the "nose" zone of the UV;
  island 25 appears 4× on the car (hood and engine lid). Any "colour by UV position" needs the per-island
  fixups in car.toml.
- **Small parts reuse big parts' texture.** The fender louver slats sample the sill at x<720: flags on the
  sill showed up inside the louvers. Keep sill art between the wheels (x≈720–1300) on a plain background.
- **The door handle distorts.** Recess at x≈1150–1270, door height ≈0.45–0.55 (dense mesh): the apex mark
  came out bent there.
- **Wing mounts distort or hide art.** The swan necks sit on the top face at ≈25% and ≈73% of the span
  (x≈1435–1475 and 1795–1835). Never a wide lockup across them: centre text between them, symbols on the ends.
- **Front bumper island 7 has an inverted vertical axis** (smaller x = lower). The intake walls 20/21 are
  separate pieces: 21 upright, 20 = VERTICAL flip of 21 (neither rotation nor horizontal flip; 3 rounds).
  Rule: for a mirrored pair of small islands, test all 4 transforms (0°, 180°, flip H, flip V) in a
  calibration round before assuming "same as the sides".
- **Jagged curved edges = missing anti-aliasing.** Pillow draws polygons without smoothing and the bumper
  corners have few texels per cm. Draw curves at 4x (`SSDraw`) and downsample with LANCZOS; never thick
  `line()` calls for curved outlines (joint spikes): draw the band as a polygon.
- **The number comes from the sim**, on the front-lower door (x≈780–1000), larger than the template's Number
  Block, in the Paint Shop colour. No logo there; on a dark body tell the user to change the number colour.
- **Windshield:** only the top banner is paintable, and iRacing's name/number covers its centre.
- **Small text:** variable fonts (Bahnschrift) break below ~24 px; use Segoe UI Bold (`text` role) and never
  below ~19 px on the 2048 TGA.
- `louver_offset`: +16 px made the louver art worse in the sim; the island is not a pure translation of the
  side. Kept at 0.

## Reading orientation (confirmed)

- Hood and roof read from the front of the car (`rotate = -90`).
- Wing: the top face is the lower half of the island and reads from behind with `rotate = 0` (the official
  "PORSCHE" pattern reads from the front: don't copy it).
- Right door `rotate = 180`, left door `rotate = 0`.
