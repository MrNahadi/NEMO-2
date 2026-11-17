"""Built-in finite element analysis: Gmsh meshing + scikit-fem linear elasticity."""

from .mesh import TetMesh, mesh_part
from .solver import StaticResult, SurfaceLoad, boundary_facets, solve_static, to_skfem

__all__ = ["StaticResult", "SurfaceLoad", "TetMesh", "boundary_facets", "mesh_part", "solve_static", "to_skfem"]
