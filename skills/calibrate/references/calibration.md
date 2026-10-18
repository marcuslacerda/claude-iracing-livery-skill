# Calibration rules (learned the hard way on the Porsche Cup; assume they hold for every car)

1. **Islandtest before drawing.** One colour + number per island, screenshot in the sim, table in
   `panels.md`. It solved in one round what analysing the PSD only "inferred" (mirrored, rotated, reused
   islands). Never trust an island's position on the template to know where it lands on the car.
2. **Fast preview = the iRacing UI Paint Shop** ("Show Custom Paint" on): it renders the TGA in 3D
   without a session. A test session is only needed to judge reflections and the spec map on track.
3. **Islands lie.** Expect: one side drawn upside down; wing endplates in the "nose" zone of the UV; a
   single island appearing several times on the car (plates near the headlights and on the engine lid);
   mirrors far from the doors. Any colour-by-position needs `[[fixups]]`.
4. **Small parts reuse big parts' texture.** Louver slats sampled the sill at x<720 on the Cup: flags on
   the sill appeared inside the louvers. Keep sill art between the wheels on a plain background, and
   note such couplings in `notes.md`.
5. **Dense-mesh areas distort detail** (door-handle recess, wing mounts). Mark them in `panels.md` and
   give the car a safe `doors_low` zone and wing zones that avoid the mounts.
6. **Inverted axes exist**: on the Cup's lower front bumper, smaller x = lower on the car. Write the
   axis direction in the island's note.
7. **Mirrored pairs of small islands: test all 4 transforms** (0°, 180°, flip H, flip V) in a
   calibration round before assuming "same as the sides". The Cup's intake walls took 3 rounds: 21 as
   drawn, 20 = VERTICAL flip (neither 180° nor horizontal flip).
8. **Reading orientation must be verified with text**, not inferred: render `solid --set text=TEST`
   and look. Hood/roof typically read from the front (rotate -90 on the Cup's layout), the wing's top
   face from behind, one door 180° from the other.
9. **Catch-all island**: the biggest island (number 1) often includes every unenclosed paintable
   pixel, so its bbox is the whole canvas. Give it a `clip` box in car.toml (the real panel's bbox).
10. **Keep `min_island_area` in car.toml** (default 6000): islands.json, islandtest and the rig must
    use the same value or the numbers won't match.
11. **Spec defaults** come from the template's own layers; some templates have no Spec Alpha layer
    (the GT3 R, the MX-5): the engine then uses 255 on the paintable area and 0 elsewhere, which is
    what the Cup's layer does. Check the spec in a test session once per car.
12. **Record everything** in `panels.md` (one line per round with the date) and `notes.md` (what
    works / what doesn't). That log is the product: the next design, and the next person, start from it.

## Screenshot checklist to ask for

front ¾ left · front ¾ right · left side straight · right side straight · rear ¾ · top-down (roof,
hood, engine lid) · close-up: mirrors · close-up: wing (top face + endplates) · close-up: front bumper
corners and intakes · close-up: door handle area and sills.
