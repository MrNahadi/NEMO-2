"""A stress study on three meshes, shared by the bracket and the fin stock.

The padeye has its own loop (``parts/padeye/fea.py``); this one is the same
method with the part-specific pieces passed in: how to find the fixed face,
which loads to apply, and which region's peak stress is the assessed result
(away from the modelling singularity at the fixed face).

The results use the same keys as the padeye study so the app and the report
read them the same way. ``head_von_mises_mpa`` is the peak in the assessed
region.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from .fea import StaticResult, SurfaceLoad, mesh_part, solve_static, to_skfem
from .runlog import emit_solve, surface_mesh

MESH_LEVELS = (1.0, 0.7, 0.5)
CONVERGED_CHANGE = 0.05


@dataclass(frozen=True)
class Level:
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
class Study:
    levels: tuple[Level, ...]
    yield_strength_mpa: float
    final: StaticResult
    region: str
    extra: dict = field(default_factory=dict)

    @property
    def head_von_mises_mpa(self) -> float:
        return self.levels[-1].head_von_mises_mpa

    @property
    def convergence_change(self) -> float:
        if len(self.levels) < 2:
            return float("nan")
        a, b = self.levels[-2].head_von_mises_mpa, self.levels[-1].head_von_mises_mpa
        return abs(b - a) / b

    def to_dict(self) -> dict:
        converged = len(self.levels) >= 2 and self.convergence_change <= CONVERGED_CHANGE
        return {
            "head_von_mises_mpa": self.head_von_mises_mpa,
            "factor_of_safety_on_yield": self.yield_strength_mpa / self.head_von_mises_mpa,
            "yield_strength_mpa": self.yield_strength_mpa,
            "convergence_change": self.convergence_change,
            "converged": converged,
            "region": self.region,
            "levels": [lvl.to_dict() for lvl in self.levels],
            **self.extra,
        }


def run_study(
    part,
    *,
    key: str,
    levels: tuple[float, ...],
    global_size_mm: float,
    local_size_mm: float | None,
    refine_surface=None,
    refine_distance_mm: float | None = None,
    elastic_modulus_mpa: float,
    poisson_ratio: float,
    yield_mpa: float,
    fixed: Callable,
    loads: Callable[[object], list[SurfaceLoad]],
    region: Callable[[np.ndarray], np.ndarray],
    region_label: str,
    emit: Callable[[str, dict], None] | None = None,
    extra: dict | None = None,
) -> Study:
    send = emit or (lambda kind, data: None)
    results: list[Level] = []
    final: StaticResult | None = None
    for i, factor in enumerate(levels, start=1):
        g = global_size_mm * factor
        loc = (local_size_mm or global_size_mm) * factor
        mesh = to_skfem(mesh_part(part, global_size_mm=g, local_size_mm=loc if local_size_mm else None,
                                  refine_surface=refine_surface, refine_distance_mm=refine_distance_mm))
        info = {"target": key, "level": i, "levels": len(levels), "nodes": int(mesh.p.shape[1]),
                "elements": int(mesh.t.shape[1]), "global_size_mm": g, "hole_size_mm": loc}
        if i == 1:
            info["surface"] = surface_mesh(mesh)
        send("mesh", info)
        send("solve_start", {"target": key, "level": i, "equations": int(3 * (mesh.p.shape[1] + mesh.edges.shape[1]))})
        result = solve_static(mesh, elastic_modulus_mpa=elastic_modulus_mpa, poisson_ratio=poisson_ratio,
                              fixed_facets=fixed(mesh), loads=loads(mesh))
        peak = result.max_von_mises_where(region(mesh.p))
        results.append(Level(
            level=i, global_size_mm=g, local_size_mm=loc, elements=result.element_count, dofs=result.dof_count,
            head_von_mises_mpa=peak, max_von_mises_mpa=result.max_von_mises_mpa,
            max_displacement_mm=result.max_displacement_mm,
            applied_force_n=tuple(float(v) for v in result.applied_force_n),
            reaction_force_n=tuple(float(v) for v in result.reaction_force_n),
            reaction_balance_error=result.reaction_balance_error, solve_seconds=result.solve_seconds,
        ))
        emit_solve(send, key, i, result, peak)
        final = result
    assert final is not None
    study = Study(levels=tuple(results), yield_strength_mpa=yield_mpa, final=final, region=region_label, extra=extra or {})
    send("fea_done", {"target": key, **study.to_dict()})
    return study
