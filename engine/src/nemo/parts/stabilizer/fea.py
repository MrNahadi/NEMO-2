"""Built-in stress analysis of the fin stock.

The fin body is a thin-walled box that a solid tetrahedral mesh cannot model
at a sensible size, so the stress check is run on the stock, which is the part
the rules size and which carries every load from the fin into the ship:

* Support: the stock fixed at the outer bearing (z = -gap).
* Load: the fin force spread evenly over the stock surface between 0.4 and 0.6
  of the span, so it acts at mid-span as in the hand calculation, and the
  twisting moment as a tangential traction over the same surface.
* The assessed result is the peak von Mises stress from half a diameter
  outboard of the bearing face (clear of the fixed-face singularity) to the
  start of the loaded length. It is compared with beam theory at the same
  section, which is NEMO's check that the model is right.
"""

from __future__ import annotations

import math

import numpy as np

from ...fea import SurfaceLoad, boundary_facets
from ...fea_study import MESH_LEVELS, Study, run_study
from .cad import STOCK_EXTENSION, build_stock
from .checks import stock_stresses
from .geometry import FinDesign
from .job import FinLoads


def analyse_stock(design: FinDesign, *, material, loads: FinLoads, levels=MESH_LEVELS, emit=None, key: str = "") -> Study:
    part = build_stock(design)
    d = design.stock_diameter_mm
    r = d / 2.0
    gap, span = design.bearing_gap_mm, design.span_mm
    z_lo, z_hi = 0.4 * span, STOCK_EXTENSION * span
    z_check = -gap + 0.5 * d
    force = loads.design_force_n
    torque = loads.torque_nm * 1000.0

    def fixed(mesh):
        return boundary_facets(mesh, lambda x: x[2] < -gap + 1e-6)

    def load_list(mesh):
        band = boundary_facets(mesh, lambda x: (x[2] > z_lo) & (x[2] < z_hi) & (np.hypot(x[0], x[1]) > r * 0.8),
                               normal_filter=lambda n: np.abs(n[2]) < 0.2)
        def across(x):
            return np.stack([0 * x[0], 1 + 0 * x[0], 0 * x[0]])
        def twist(x):
            rr = np.maximum(np.hypot(x[0], x[1]), 1e-9)
            return np.stack([-x[1] / rr, x[0] / rr, 0 * x[0]])
        return [
            SurfaceLoad("fin twist", band, twist, np.zeros(3), total_moment_nmm=np.array([0.0, 0.0, torque]),
                        moment_about=(0.0, 0.0, 0.5 * span)),
            SurfaceLoad("fin force", band, across, np.array([0.0, force, 0.0]), absorb=True),
        ]

    lever = 0.5 * span - z_check
    sb, tau, se = stock_stresses(d, force * lever / 1000.0, loads.torque_nm)
    yield_mpa = material.yield_strength_mpa(d)
    return run_study(
        part, key=key, levels=levels, global_size_mm=max(d / 4.5, 6.0), local_size_mm=None,
        elastic_modulus_mpa=material.elastic_modulus_mpa, poisson_ratio=material.poisson_ratio, yield_mpa=yield_mpa,
        fixed=fixed, loads=load_list, region=lambda p: (p[2] >= z_check) & (p[2] <= z_lo - 0.5 * d),
        region_label=f"stock from {0.5 * d:.0f} mm outboard of the bearing to the loaded length", emit=emit,
        extra={"hand_stress_mpa": se, "hand_label": "stock, beam theory with bending and twist", "hand_section_mm": z_check + gap,
               "hand_bending_mpa": sb, "hand_torsion_mpa": tau, "model": "stock"},
    )


__all__ = ["analyse_stock", "math"]
