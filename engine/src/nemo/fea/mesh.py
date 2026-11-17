"""Tetrahedral meshing of solid models with Gmsh.

The solid is passed to Gmsh as a BREP file (exact OpenCASCADE geometry, in mm).
Element size is set globally, with optional local refinement on chosen
surfaces (for example a pin hole) using a distance field.
"""

from __future__ import annotations

import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import gmsh
import numpy as np
from build123d import Part, export_brep

# Gmsh is a global, single-threaded library. Serialise all access.
_GMSH_LOCK = threading.Lock()

SurfacePredicate = Callable[[str, tuple[float, float, float, float, float, float]], bool]


@dataclass(frozen=True)
class TetMesh:
    points: np.ndarray  # (3, n_nodes), mm
    tets: np.ndarray  # (4, n_elements), node indices
    global_size_mm: float
    local_size_mm: float | None

    @property
    def node_count(self) -> int:
        return int(self.points.shape[1])

    @property
    def element_count(self) -> int:
        return int(self.tets.shape[1])


def mesh_part(
    part: Part,
    *,
    global_size_mm: float,
    local_size_mm: float | None = None,
    refine_surface: SurfacePredicate | None = None,
    refine_distance_mm: float | None = None,
) -> TetMesh:
    """Mesh a solid with linear tetrahedra.

    ``refine_surface(kind, bbox)`` returns True for surfaces that need the
    ``local_size_mm``. ``kind`` is Gmsh's surface type (for example
    ``"Cylinder"`` or ``"Plane"``); ``bbox`` is (xmin, ymin, zmin, xmax, ymax, zmax).
    The size grows back to ``global_size_mm`` over ``refine_distance_mm``.
    """
    if global_size_mm <= 0:
        raise ValueError("Mesh size must be greater than 0.")
    with tempfile.TemporaryDirectory() as tmp:
        brep = Path(tmp) / "part.brep"
        export_brep(part, str(brep))
        with _GMSH_LOCK:
            return _mesh_brep(brep, global_size_mm, local_size_mm, refine_surface, refine_distance_mm)


def _mesh_brep(
    brep: Path,
    global_size: float,
    local_size: float | None,
    refine_surface: SurfacePredicate | None,
    refine_distance: float | None,
) -> TetMesh:
    gmsh.initialize(interruptible=False)
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.option.setNumber("General.Verbosity", 1)
        gmsh.model.add("nemo")
        gmsh.model.occ.importShapes(str(brep))
        gmsh.model.occ.synchronize()

        gmsh.option.setNumber("Mesh.MeshSizeMax", global_size)
        gmsh.option.setNumber("Mesh.MeshSizeMin", (local_size or global_size) * 0.5)
        gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
        gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 12)
        gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
        gmsh.option.setNumber("Mesh.Algorithm3D", 10)  # HXT: fast, robust
        gmsh.option.setNumber("Mesh.Optimize", 1)

        if local_size and refine_surface:
            chosen = []
            for dim, tag in gmsh.model.getEntities(2):
                kind = gmsh.model.getType(dim, tag)
                bbox = tuple(gmsh.model.getBoundingBox(dim, tag))
                if refine_surface(kind, bbox):
                    chosen.append(tag)
            if chosen:
                dist = gmsh.model.mesh.field.add("Distance")
                gmsh.model.mesh.field.setNumbers(dist, "SurfacesList", chosen)
                gmsh.model.mesh.field.setNumber(dist, "Sampling", 60)
                thr = gmsh.model.mesh.field.add("Threshold")
                gmsh.model.mesh.field.setNumber(thr, "InField", dist)
                gmsh.model.mesh.field.setNumber(thr, "SizeMin", local_size)
                gmsh.model.mesh.field.setNumber(thr, "SizeMax", global_size)
                gmsh.model.mesh.field.setNumber(thr, "DistMin", 0.0)
                gmsh.model.mesh.field.setNumber(thr, "DistMax", refine_distance or 5.0 * global_size)
                gmsh.model.mesh.field.setAsBackgroundMesh(thr)

        gmsh.model.mesh.generate(3)

        node_tags, coords, _ = gmsh.model.mesh.getNodes()
        points = coords.reshape(-1, 3).T
        index = np.full(int(node_tags.max()) + 1, -1, dtype=np.int64)
        index[node_tags.astype(np.int64)] = np.arange(node_tags.size)

        _, elem_nodes = gmsh.model.mesh.getElementsByType(4)  # 4-node tetrahedra
        tets = index[elem_nodes.astype(np.int64)].reshape(-1, 4).T
        if tets.size == 0:
            raise RuntimeError("Meshing produced no tetrahedra.")

        used = np.unique(tets)
        if used.size != points.shape[1]:
            remap = np.full(points.shape[1], -1, dtype=np.int64)
            remap[used] = np.arange(used.size)
            points = points[:, used]
            tets = remap[tets]
        return TetMesh(points=np.ascontiguousarray(points), tets=np.ascontiguousarray(tets),
                       global_size_mm=global_size, local_size_mm=local_size)
    finally:
        gmsh.finalize()
