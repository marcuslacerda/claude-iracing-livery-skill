# What the sim does with the files (iRacing + Trading Paints, curated)

- **Files**: `Documents\iRacing\paint\<CarPath>\car_<customer id>.tga` (24-bit, or 32 with alpha) and
  `car_spec_<customer id>.tga` (32-bit), 2048×2048 (1024 accepted). The sim converts them to `.mip`
  and reloads when the `.tga` is newer than the `.mip` (or there is no `.mip`). `Ctrl+R` inside a
  session regenerates the `.mip` without restarting. The iRacing UI's **Paint Shop** ("Show Custom
  Paint" on) renders the TGA in 3D without a session: that is the fast preview.
- **One paint per car at a time**: deploying overwrites the installed one. Every design is regenerable
  from its file, so the workspace `out/` folders are a cache.
- **Spec map (PBR)**: R = metallic (white = metallic), G = roughness (white = matte, black = mirror),
  B = clear coat ("normally left white" in iRacing's doc; the Cup template ships 0 and it works),
  A = specular mask. Cars with default decals may show ghosted logos under a custom paint; the spec map
  fixes that too. Chrome/metallic surfaces need a very light base colour (chrome ≈ white).
- **Stamps** (the number, iRacing's sponsor decals) have no material of their own: they inherit the
  spec map of the pixels they land on. Paint the number area with the finish you want on the number.
- **The number** is drawn by the sim (front-lower door on the Cup, x≈780–1000), larger than the
  template's Number Block, in the colour set in the Paint Shop.
- Some cars use different parts by track type (oval vs road wing/nose): check both when the car has
  that variation (the Cup doesn't).
- **Only the owner sees a local TGA.** For others to see it you need **Trading Paints** (its client
  uploads your paint and downloads the others'); their terms apply to what you upload.
- Templates: https://www.iracing.com/painttextures/ (member login). Spec map:
  https://help.tradingpaints.com/painting/how-do-i-create-a-spec-map-file-for-use-in-iracing/ ;
  alignment across panels: https://blog.tradingpaints.com/5-tips-for-showroom-success/ ;
  matte starter: https://blog.tradingpaints.com/spec-map-starter-the-mattedor/ ; ghosted logos:
  https://help.tradingpaints.com/kb/guide/en/on-some-vehicles-logos-appear-faintly-ghosted-underneath-my-custom-paint-how-can-i-prevent-this-P4SLpKyS9W/Steps/2489239 ;
  why UV islands overlap/mirror: https://documentation.beamng.com/modding/vehicle/vehicle-art/uv-unwrapping/
