"""Built-in stress analysis of a padeye.

Model (matches the Fusion cross-check study NEMO prints):

* Support: the base face (z = 0) fully fixed, as if welded to rigid structure.
* Pin load: the shackle pin presses on the half of the hole facing the sling,
  spread as a cosine (highest in line with the sling, zero at 90 degrees). It
  adds up exactly to the in-plane part of the sling force (the whole sling
  force when the padeye is lined up with its sling).
* Side load: the sideways (axial) force, spread uniformly around the hole bore
  so it exerts zero spurious twisting moment about the pinhole (matching
  Autodesk Fusion's Bearing Load axial distribution).
* Material: linear elastic. Stress is reported as von Mises.

The base edge where the fixed face meets the free faces—and, when cheek plates
are present, the unmodeled 90-degree re-entrant step where each cheek plate
meets the main plate—are linear-elastic modelling singularities whose peaks
diverge as the mesh gets finer. The head (hole region, clear of the cheek step)
result is the one compared with the code checks and checked for mesh
convergence.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

import numpy as np

from ...data import Material
from ...fea import StaticResult, SurfaceLoad, boundary_facets, mesh_part, solve_static, to_skfem
from ...loads import PadeyeLoads
from .cad import build_padeye
from .geometry import PadeyeDesign

MESH_LEVELS = (1.0, 0.7, 0.5)
CONVERGED_CHANGE = 0.05


@dataclass(frozen=True)
class PadeyeFEAResult:
    level: int
    global_size_mm: float
    local_size_mm: float
    elements: int
    dofs: int
    head_von_mises_mpa: float
    max_von_mises_mpa: float
    max_displacement_mm: float
    applied_force_n: tuple[float, float, float]
    reaction_force_n: tuple[float, float, float]
    reaction_balance_error: float
    solve_seconds: float

    def to_dict(self) -> dict:
        return dict(self.__dict__)


@dataclass(frozen=True)
class PadeyeFEAStudy:
    levels: tuple[PadeyeFEAResult, ...]
    yield_strength_mpa: float
    final: StaticResult

    @property
    def head_von_mises_mpa(self) -> float:
        return self.levels[-1].head_von_mises_mpa

    @property
    def factor_of_safety_on_yield(self) -> float:
        return self.yield_strength_mpa / self.head_von_mises_mpa

    @property
    def convergence_change(self) -> float:
        """Relative change in head stress between the last two mesh levels."""
        if len(self.levels) < 2:
            return float("nan")
        a, b = self.levels[-2].head_von_mises_mpa, self.levels[-1].head_von_mises_mpa
        return abs(b - a) / b

    @property
    def converged(self) -> bool:
        return len(self.levels) >= 2 and self.convergence_change <= CONVERGED_CHANGE

    def to_dict(self) -> dict:
        return {
            "head_von_mises_mpa": self.head_von_mises_mpa,
            "factor_of_safety_on_yield": self.factor_of_safety_on_yield,
            "yield_strength_mpa": self.yield_strength_mpa,
            "convergence_change": self.convergence_change,
            "converged": self.converged,
            "levels": [lvl.to_dict() for lvl in self.levels],
        }


def default_mesh_sizes(design: PadeyeDesign) -> tuple[float, float]:
    """Global and hole-region element sizes (mm) for mesh level 1."""
    global_size = max(min(design.main_thickness_mm, design.head_radius_mm / 2.5, design.base_length_mm / 8), 2.0)
    local_size = max(min(design.hole_diameter_mm * math.pi / 40.0, design.total_thickness_mm / 3.0), 0.6)
    return global_size, local_size


def head_assessment_mask(points: np.ndarray, design: PadeyeDesign) -> np.ndarray:
    """Vertices in the assessed head/pin-hole region, excluding the 90-degree cheek-plate step singularity."""
    r_head = np.hypot(points[0], points[2] - design.hole_height_mm)
    mask = r_head <= design.head_radius_mm + 1.0
    if design.has_cheeks:
        # Exclude the unmodeled 90-degree cheek-plate re-entrant corner (r = Rc, |y| = t_main/2),
        # where fillet welds are omitted and linear-elastic stress diverges with mesh refinement.
        t_main_half = design.main_thickness_mm / 2.0
        radius = design.hole_diameter_mm / 2.0
        step_keep_out = min(2.0, 0.25 * (design.cheek_radius_mm - radius))
        on_cheek_step = (np.abs(r_head - design.cheek_radius_mm) <= step_keep_out) & (
            np.abs(np.abs(points[1]) - t_main_half) <= step_keep_out
        )
        mask = mask & (~on_cheek_step)
    return mask


def analyse_padeye(
    design: PadeyeDesign,
    *,
    material: Material,
    loads: PadeyeLoads,
    levels: tuple[float, ...] = MESH_LEVELS,
    emit: Callable[[str, dict], None] | None = None,
    key: str = "",
) -> PadeyeFEAStudy:
    send = emit or (lambda kind, data: None)
    solid = build_padeye(design)
    h = design.hole_height_mm
    radius = design.hole_diameter_mm / 2.0
    t_half = design.total_thickness_mm / 2.0
    head_reach = design.head_radius_mm + 1.0

    # In-plane part of the sling force. With an oblique sling (second angle beta) it is F cos(gamma), and the
    # sideways part goes in side_force; with the padeye lined up it is the whole sling force.
    in_plane = np.array([loads.horizontal_n, 0.0, loads.vertical_n])
    direction = in_plane / np.linalg.norm(in_plane)
    bearing_force = in_plane
    side_force = np.array([0.0, loads.side_n, 0.0])

    def bearing_shape(x: np.ndarray) -> np.ndarray:
        rx, rz = x[0], x[2] - h
        rr = np.maximum(np.hypot(rx, rz), 1e-12)
        ux, uz = rx / rr, rz / rr
        p = np.maximum(ux * direction[0] + uz * direction[2], 0.0)
        return np.stack([p * ux, 0.0 * p, p * uz])

    def side_shape(x: np.ndarray) -> np.ndarray:
        # Uniform axial traction around the 360-degree hole bore: zero spurious moment about the pinhole
        # and consistent with Autodesk Fusion's Bearing Load axial component distribution.
        return np.stack([0.0 * x[0], np.ones_like(x[0]), 0.0 * x[0]])

    def is_hole_surface(kind: str, bbox) -> bool:
        return kind == "Cylinder" and (bbox[3] - bbox[0]) <= design.hole_diameter_mm * 1.05

    global_size, local_size = default_mesh_sizes(design)
    results: list[PadeyeFEAResult] = []
    final: StaticResult | None = None
    for i, factor in enumerate(levels, start=1):
        mesh = to_skfem(
            mesh_part(
                solid.part,
                global_size_mm=global_size * factor,
                local_size_mm=local_size * factor,
                refine_surface=is_hole_surface,
                refine_distance_mm=design.head_radius_mm,
            )
        )
        mesh_info = {"target": key, "level": i, "levels": len(levels), "nodes": int(mesh.p.shape[1]),
                     "elements": int(mesh.t.shape[1]), "global_size_mm": global_size * factor,
                     "hole_size_mm": local_size * factor}
        if i == 1:
            mesh_info["surface"] = surface_mesh(mesh)
        send("mesh", mesh_info)
        send("solve_start", {"target": key, "level": i, "equations": int(3 * (mesh.p.shape[1] + mesh.edges.shape[1]))})
        tol = max(0.02 * radius, 0.05)
        hole_facets = boundary_facets(
            mesh,
            lambda x: (np.abs(np.hypot(x[0], x[2] - h) - radius) < tol) & (np.abs(x[1]) < t_half + 1e-6),
            normal_filter=lambda n: np.abs(n[1]) < 0.5,
        )
        base_facets = boundary_facets(mesh, lambda x: x[2] < 1e-6)
        result = solve_static(
            mesh,
            elastic_modulus_mpa=material.elastic_modulus_mpa,
            poisson_ratio=material.poisson_ratio,
            fixed_facets=base_facets,
            loads=[
                SurfaceLoad("pin bearing", hole_facets, bearing_shape, bearing_force),
                SurfaceLoad("side load", hole_facets, side_shape, side_force),
            ],
        )
        head_nodes = head_assessment_mask(mesh.p, design)
        results.append(
            PadeyeFEAResult(
                level=i,
                global_size_mm=global_size * factor,
                local_size_mm=local_size * factor,
                elements=result.element_count,
                dofs=result.dof_count,
                head_von_mises_mpa=result.max_von_mises_where(head_nodes),
                max_von_mises_mpa=result.max_von_mises_mpa,
                max_displacement_mm=result.max_displacement_mm,
                applied_force_n=tuple(float(v) for v in result.applied_force_n),
                reaction_force_n=tuple(float(v) for v in result.reaction_force_n),
                reaction_balance_error=result.reaction_balance_error,
                solve_seconds=result.solve_seconds,
            )
        )
        r = results[-1]
        history = list(result.residual_history)
        step = max(1, len(history) // 120)
        send("solve", {"target": key, "level": i, "equations": r.dofs, "method": result.solver_method,
                       "residuals": history[::step] + ([history[-1]] if history and (len(history) - 1) % step else []),
                       "iterations": len(history), "relative_residual": result.relative_residual,
                       "seconds": r.solve_seconds, "head_von_mises_mpa": r.head_von_mises_mpa,
                       "max_displacement_mm": r.max_displacement_mm, "applied_force_n": r.applied_force_n,
                       "reaction_force_n": r.reaction_force_n, "balance_error": r.reaction_balance_error})
        final = result

    assert final is not None
    study = PadeyeFEAStudy(
        levels=tuple(results),
        yield_strength_mpa=material.yield_strength_mpa(design.main_thickness_mm),
        final=final,
    )
    send("fea_done", {"target": key, **study.to_dict()})
    return study


def surface_mesh(mesh) -> dict:
    """Outer surface triangles of a mesh (engine axes, mm), for drawing it as a wireframe."""
    facets = mesh.facets[:, mesh.boundary_facets()]
    used, inverse = np.unique(facets, return_inverse=True)
    return {
        "positions": np.round(mesh.p[:, used].T, 2).ravel().tolist(),
        "triangles": inverse.reshape(3, -1).T.astype(int).ravel().tolist(),
    }
