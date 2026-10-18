"""The spec map (PBR): R = metallic, G = roughness (white = matte, black = mirror), B = clear coat,
A = specular mask. Rebuilt from the template's own default layers (Base Paint under Parts), with the
design's roughness overrides blended in. Stamps (the number, iRacing's sponsors) have no material of
their own: they inherit the spec of the pixels they land on.
"""
from __future__ import annotations

import numpy as np
from PIL import Image

from .template import Template


def spec_map(T: Template, roughness_override=None, roughness_map=None, metallic_map=None) -> Image.Image:
    """roughness_override: (float mask 0..1, value) blended into G last (the logo/matte mask).
    roughness_map / metallic_map: (float mask 0..1, float HxW of G / R values) blended before the Parts
    layer is applied, so mechanical parts keep the template's own material."""
    info = {}

    def chan(base_role, parts_role, design_map=None):
        base = np.array(T.layer(base_role)).astype(np.float32)
        out = base[..., 0].copy()
        if design_map is not None:
            m, vals = design_map
            out = vals * m + out * (1 - m)
        if T.has(parts_role):
            parts = np.array(T.layer(parts_role)).astype(np.float32)
            a = parts[..., 3] / 255.0
            out = parts[..., 0] * a + out * (1 - a)
        return out

    r = chan("spec_r_base", "spec_r_parts", metallic_map)
    g = chan("spec_g_base", "spec_g_parts", roughness_map)
    b = chan("spec_b_base", "spec_b_parts")
    if T.has("spec_alpha"):
        a = np.array(T.layer("spec_alpha")).astype(np.float32)[..., 0]
        info["alpha"] = T.path("spec_alpha").name
    else:
        # templates without a Spec Alpha layer (e.g. the 992 GT3 R): specular on the paint, none on the
        # mechanical parts - the same convention the Cup's own layer follows
        a = np.where(T.paintable, 255.0, 0.0).astype(np.float32)
        info["alpha"] = "(no spec alpha layer: 255 on the paintable area, 0 elsewhere)"
    if roughness_override is not None:
        m, val = roughness_override
        g = val * m + g * (1 - m)
    img = Image.fromarray(np.dstack([r, g, b, a]).clip(0, 255).astype(np.uint8), "RGBA")
    img.info["spec_sources"] = info
    return img
