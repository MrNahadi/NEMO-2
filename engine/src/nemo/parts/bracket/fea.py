"""Built-in stress analysis of a pipe support bracket.

Model:

* Support: the faces against the bulkhead (x = 0) fully fixed, as if welded to
  a rigid bulkhead.
* Pipe load: the downward force, the force across the pipe and the friction
  along it, spread evenly over a strip of the seat top under the pipe.
* The assessed result is the peak von Mises stress away from the bulkhead
  face. The sharp corners where the plates meet the fixed face are a
  modelling singularity, so a strip 1.5 plate thicknesses wide next to it is
  left out, the same way the padeye result is read in the head region.
"""

from __future__ import annotations

import numpy as np

from ...fea import SurfaceLoad, boundary_facets
from ...fea_study import MESH_LEVELS, Study, run_study
from .cad import build_bracket
from .geometry import BracketDesign
from .job import BracketLoads


def analyse_bracket(design: BracketDesign, *, material, loads: BracketLoads, levels=MESH_LEVELS, emit=None, key: str = "",
                    hand_stress_mpa: float | None = None, hand_label: str = "") -> Study:
    solid = build_bracket(design)
    thin = min(design.seat_thickness_mm, design.knee_thickness_mm)
    global_size = float(np.clip(1.2 * thin, 4.0, 20.0))
    e = design.pipe_offset_mm
    strip = max(0.25 * design.pipe_od_mm, 2.5 * design.seat_thickness_mm, 1.5 * global_size)
    keep_out = 1.5 * max(design.seat_thickness_mm, design.knee_thickness_mm)

    def at_bulkhead(kind, bbox) -> bool:
        return kind == "Plane" and abs(bbox[0]) < 1e-6 and abs(bbox[3]) < 1e-6

    def fixed(mesh):
        return boundary_facets(mesh, lambda x: x[0] < 1e-6)

    def load_list(mesh):
        patch = boundary_facets(mesh, lambda x: (x[2] > -1e-6) & (np.abs(x[0] - e) < strip / 2.0),
                                normal_filter=lambda n: np.abs(n[2]) > 0.9)
        def uniform(direction):
            return lambda x: np.stack([direction[0] + 0 * x[0], direction[1] + 0 * x[0], direction[2] + 0 * x[0]])
        return [
            SurfaceLoad("pipe weight", patch, uniform((0.0, 0.0, -1.0)), np.array([0.0, 0.0, -loads.down_n])),
            SurfaceLoad("across the pipe", patch, uniform((1.0, 0.0, 0.0)), np.array([loads.across_n, 0.0, 0.0])),
            SurfaceLoad("along the pipe", patch, uniform((0.0, 1.0, 0.0)), np.array([0.0, loads.along_n, 0.0])),
        ]

    return run_study(
        solid.part, key=key, levels=levels, global_size_mm=global_size, local_size_mm=0.6 * global_size,
        refine_surface=at_bulkhead, refine_distance_mm=4.0 * design.seat_thickness_mm,
        elastic_modulus_mpa=material.elastic_modulus_mpa, poisson_ratio=material.poisson_ratio,
        yield_mpa=min(material.yield_strength_mpa(design.seat_thickness_mm), material.yield_strength_mpa(design.knee_thickness_mm)),
        fixed=fixed, loads=load_list, region=lambda p: p[0] >= keep_out,
        region_label=f"away from the bulkhead face (x ≥ {keep_out:.0f} mm)", emit=emit,
        extra={"hand_stress_mpa": hand_stress_mpa, "hand_label": hand_label, "load_strip_mm": strip},
    )
