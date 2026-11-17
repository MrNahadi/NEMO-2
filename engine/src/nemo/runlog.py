"""Shared pieces of every part's run: the engineering event log and stress-plot export."""

from __future__ import annotations

import threading
import time
from typing import Callable

import numpy as np

from .fea import StaticResult

Progress = Callable[[str, float], None]
Listener = Callable[[dict], None]


class EngineeringLog:
    """Ordered engineering events. Thread-safe; readers take slices by index."""

    def __init__(self, listener: Listener | None = None) -> None:
        self.events: list[dict] = []
        self._start = time.perf_counter()
        self._lock = threading.Lock()
        self._listener = listener

    def emit(self, kind: str, data: dict) -> None:
        with self._lock:
            event = {"seq": len(self.events), "t": round(time.perf_counter() - self._start, 3), "kind": kind, **data}
            self.events.append(event)
        if self._listener:
            self._listener(event)

    def since(self, index: int) -> list[dict]:
        with self._lock:
            return self.events[index:]


def stress_surface(result: StaticResult, decimals: int = 3) -> dict:
    """Outer surface triangles with von Mises stress per vertex, for the 3D viewer."""
    m = result.mesh
    facets = m.facets[:, m.boundary_facets()]  # (3, n_tri)
    used, inverse = np.unique(facets, return_inverse=True)
    triangles = inverse.reshape(3, -1).T
    points = m.p[:, used].T
    return {
        "units": {"length": "mm", "stress": "MPa", "displacement": "mm"},
        "positions": np.round(points, decimals).ravel().tolist(),
        "triangles": triangles.astype(int).ravel().tolist(),
        "von_mises": np.round(result.von_mises_nodal[used], 2).tolist(),
        "displacement": np.round(result.displacement[:, used].T, 5).ravel().tolist(),
        "max_von_mises": float(result.max_von_mises_mpa),
    }


def surface_mesh(mesh) -> dict:
    """Outer surface triangles of a mesh (engine axes, mm), for drawing it as a wireframe."""
    facets = mesh.facets[:, mesh.boundary_facets()]
    used, inverse = np.unique(facets, return_inverse=True)
    return {
        "positions": np.round(mesh.p[:, used].T, 2).ravel().tolist(),
        "triangles": inverse.reshape(3, -1).T.astype(int).ravel().tolist(),
    }


def emit_solve(send, key: str, level: int, result, region_mpa: float) -> None:
    """The 'solve' event every part's FEA sends after each mesh level."""
    history = list(result.residual_history)
    step = max(1, len(history) // 120)
    send("solve", {"target": key, "level": level, "equations": result.dof_count, "method": result.solver_method,
                   "residuals": history[::step] + ([history[-1]] if history and (len(history) - 1) % step else []),
                   "iterations": len(history), "relative_residual": result.relative_residual,
                   "seconds": result.solve_seconds, "head_von_mises_mpa": region_mpa,
                   "max_displacement_mm": result.max_displacement_mm,
                   "applied_force_n": tuple(float(v) for v in result.applied_force_n),
                   "reaction_force_n": tuple(float(v) for v in result.reaction_force_n),
                   "balance_error": result.reaction_balance_error})
