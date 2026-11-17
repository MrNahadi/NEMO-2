"""Linear-elastic static stress analysis with scikit-fem.

Quadratic (10-node equivalent, P2) displacement elements on a linear
tetrahedral mesh. Units: mm, N, MPa.

Loads are surface tractions on chosen boundary facets. Each traction is given
as a *shape* (how the load is spread) plus the total force it must add up to;
NEMO scales the shape so its resultant matches the force. That removes the
"typed the wrong load" class of mistakes: the applied total is computed and
reported back, and the support reactions are checked against it.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import pyamg
from scipy.sparse.linalg import spsolve
from skfem import Basis, ElementTetP2, ElementVector, FacetBasis, Functional, LinearForm, MeshTet, asm, condense
from skfem.helpers import dot
from skfem.models.elasticity import lame_parameters

from .mesh import TetMesh

TractionShape = Callable[[np.ndarray], np.ndarray]
"""Maps facet quadrature point coordinates (3, nf, nq) to a traction (3, nf, nq)."""

DIRECT_SOLVER_DOF_LIMIT = 6_000


@dataclass(frozen=True)
class SurfaceLoad:
    name: str
    facets: np.ndarray
    shape: TractionShape
    total_force_n: np.ndarray  # (3,) target resultant
    total_moment_nmm: np.ndarray | None = None  # (3,) target moment, for loads whose force resultant is zero
    moment_about: tuple[float, float, float] = (0.0, 0.0, 0.0)
    absorb: bool = False  # aim for total_force_n minus what the loads before it already apply


@dataclass(frozen=True)
class StaticResult:
    mesh: MeshTet
    displacement: np.ndarray  # (3, n_vertices), mm
    von_mises_nodal: np.ndarray  # (n_vertices,), MPa, averaged at vertices
    applied_force_n: np.ndarray  # (3,)
    reaction_force_n: np.ndarray  # (3,)
    dof_count: int
    element_count: int
    solve_seconds: float
    loads_applied: dict[str, np.ndarray] = field(default_factory=dict)
    solver_method: str = "direct"
    residual_history: tuple[float, ...] = ()
    relative_residual: float = 0.0

    @property
    def max_displacement_mm(self) -> float:
        return float(np.max(np.linalg.norm(self.displacement, axis=0)))

    @property
    def max_von_mises_mpa(self) -> float:
        return float(np.max(self.von_mises_nodal))

    def max_von_mises_where(self, mask: np.ndarray) -> float:
        values = self.von_mises_nodal[mask]
        return float(values.max()) if values.size else 0.0

    @property
    def reaction_balance_error(self) -> float:
        """|applied + reaction| / |applied|. Near zero when loads balance."""
        applied = np.linalg.norm(self.applied_force_n)
        if applied == 0:
            return 0.0
        return float(np.linalg.norm(self.applied_force_n + self.reaction_force_n) / applied)


def to_skfem(mesh: TetMesh) -> MeshTet:
    return MeshTet(mesh.points.astype(float), mesh.tets.astype(np.int64))


def boundary_facets(
    mesh: MeshTet,
    where: Callable[[np.ndarray], np.ndarray],
    normal_filter: Callable[[np.ndarray], np.ndarray] | None = None,
) -> np.ndarray:
    """Boundary facets whose midpoints satisfy ``where`` (and optionally whose
    unit normals satisfy ``normal_filter``)."""
    facets = mesh.facets_satisfying(where, boundaries_only=True)
    if normal_filter is None or facets.size == 0:
        return facets
    corners = mesh.p[:, mesh.facets[:, facets]]  # (3, 3 corners, nf)
    normal = np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0], axis=0)
    normal /= np.linalg.norm(normal, axis=0)
    return facets[normal_filter(normal)]


def solve_static(
    mesh: TetMesh | MeshTet,
    *,
    elastic_modulus_mpa: float,
    poisson_ratio: float,
    fixed_facets: np.ndarray,
    loads: list[SurfaceLoad],
) -> StaticResult:
    m = mesh if isinstance(mesh, MeshTet) else to_skfem(mesh)
    if fixed_facets.size == 0:
        raise ValueError("No supported (fixed) surface was found on the model.")
    element = ElementVector(ElementTetP2())
    basis = Basis(m, element)
    lam, mu = lame_parameters(elastic_modulus_mpa, poisson_ratio)

    start = time.perf_counter()
    stiffness = _assemble_elasticity(m, basis, lam, mu)

    force = np.zeros(basis.N)
    applied_total = np.zeros(3)
    applied: dict[str, np.ndarray] = {}
    for load in loads:
        if load.facets.size == 0:
            raise ValueError(f"No surface was found for the load '{load.name}'.")
        f_vec, resultant = _assemble_traction(m, element, load)
        if load.total_moment_nmm is not None:
            moment = _traction_moment(m, element, load)
            target_m = np.asarray(load.total_moment_nmm, dtype=float)
            if np.linalg.norm(target_m) == 0:
                continue
            scale = float(target_m @ moment / (moment @ moment))
            force += scale * f_vec
            applied[load.name] = scale * resultant
            applied_total += scale * resultant
            continue
        target = np.asarray(load.total_force_n, dtype=float)
        if load.absorb:
            target = target - applied_total
        if np.linalg.norm(target) == 0:
            continue
        scale = float(target @ resultant / (resultant @ resultant))
        force += scale * f_vec
        applied[load.name] = scale * resultant
        applied_total += scale * resultant

    fixed = basis.get_dofs(fixed_facets).all()
    free = np.setdiff1d(np.arange(basis.N), fixed)
    u = np.zeros(basis.N)
    a_ff, b_f, _, _ = condense(stiffness, force, D=fixed)
    method = "direct"
    history: list[float] = []
    if free.size <= DIRECT_SOLVER_DOF_LIMIT:
        u[free] = spsolve(a_ff.tocsc(), b_f)
    else:
        near_null = _rigid_body_modes(basis)[free]
        solver = pyamg.smoothed_aggregation_solver(
            a_ff.tocsr(),
            B=near_null,
            strength=("symmetric", {"theta": 0.0}),
            smooth=("energy", {}),
            max_coarse=500,
        )
        residuals: list[float] = []
        u[free] = solver.solve(b_f, tol=1e-10, accel="cg", maxiter=600, residuals=residuals)
        method = "multigrid"
        if residuals:
            history = [float(r / max(residuals[0], 1e-30)) for r in residuals]
        if residuals and residuals[-1] > 1e-8 * max(residuals[0], 1e-30):
            # Fall back to the slower but dependable direct solver.
            u[free] = spsolve(a_ff.tocsc(), b_f)
            method = "direct (after multigrid stalled)"
    elapsed = time.perf_counter() - start
    relative_residual = float(np.linalg.norm(a_ff @ u[free] - b_f) / max(np.linalg.norm(b_f), 1e-30))

    # K u = f + r, so the support reaction acting on the part is r = K u - f.
    residual = stiffness @ u - force
    split = basis.split_indices()
    fixed_mask = np.zeros(basis.N, dtype=bool)
    fixed_mask[fixed] = True
    reaction = np.array([residual[idx[fixed_mask[idx]]].sum() for idx in split])

    displacement = np.vstack([u[idx][: m.p.shape[1]] for idx in _vertex_dofs(basis)])
    vm = _nodal_von_mises(m, element, u, lam, mu)

    return StaticResult(
        mesh=m,
        displacement=displacement,
        von_mises_nodal=vm,
        applied_force_n=applied_total,
        reaction_force_n=reaction,
        dof_count=int(basis.N),
        element_count=int(m.t.shape[1]),
        solve_seconds=elapsed,
        loads_applied=applied,
        solver_method=method,
        residual_history=tuple(history),
        relative_residual=relative_residual,
    )


# ---------------------------------------------------------------- internals
def _assemble_traction(m: MeshTet, element, load: SurfaceLoad) -> tuple[np.ndarray, np.ndarray]:
    fb = FacetBasis(m, element, facets=load.facets, intorder=4)

    @LinearForm
    def traction_form(v, w):
        return dot(load.shape(w.x), v)

    vector = asm(traction_form, fb)

    resultant = np.zeros(3)
    for comp in range(3):

        @Functional
        def component(w, comp=comp):
            return load.shape(w.x)[comp]

        resultant[comp] = asm(component, fb)
    return vector, resultant


def _traction_moment(m: MeshTet, element, load: SurfaceLoad) -> np.ndarray:
    """Moment of the unscaled traction shape about ``load.moment_about``."""
    fb = FacetBasis(m, element, facets=load.facets, intorder=4)
    origin = np.asarray(load.moment_about, dtype=float)
    out = np.zeros(3)
    for comp in range(3):

        @Functional
        def component(w, comp=comp):
            t = load.shape(w.x)
            r = [w.x[i] - origin[i] for i in range(3)]
            cross = (r[1] * t[2] - r[2] * t[1], r[2] * t[0] - r[0] * t[2], r[0] * t[1] - r[1] * t[0])
            return cross[comp]

        out[comp] = asm(component, fb)
    return out


def _assemble_elasticity(m: MeshTet, vector_basis: Basis, lam: float, mu: float):
    """Isotropic linear-elastic stiffness matrix, assembled in vectorised blocks.

    Equivalent to ``asm(linear_elasticity(lam, mu), vector_basis)`` but much
    faster: it builds element matrices from the scalar P2 shape-function
    gradients with a few ``einsum`` calls instead of one call per pair of shape
    functions. Local DOF order matches skfem's ``ElementVector``: scalar
    function ``a``, component ``i`` -> local index ``3 * a + i``.
    """
    scalar = Basis(m, ElementTetP2(), intorder=2)
    grads = np.stack([phi[0].grad for phi in scalar.basis])  # (10, 3, nel, nq)
    dx = scalar.dx  # (nel, nq)
    element_dofs = vector_basis.element_dofs  # (30, nel)
    n_local = element_dofs.shape[0]
    eye = np.eye(3)
    rows, cols, vals = [], [], []
    block = 4000
    for start in range(0, dx.shape[0], block):
        g = grads[:, :, start:start + block]
        w = dx[start:start + block]
        k_lambda = np.einsum("aieq,bjeq,eq->eaibj", g, g, w, optimize=True)
        k_shear = np.einsum("ajeq,bieq,eq->eaibj", g, g, w, optimize=True)
        k_lap = np.einsum("akeq,bkeq,eq->eab", g, g, w, optimize=True)
        ke = lam * k_lambda + mu * k_shear + mu * np.einsum("eab,ij->eaibj", k_lap, eye)
        ke = ke.reshape(-1, n_local, n_local)
        dofs = element_dofs[:, start:start + block].T  # (nb, 30)
        rows.append(np.repeat(dofs, n_local, axis=1).ravel())
        cols.append(np.tile(dofs, (1, n_local)).ravel())
        vals.append(ke.ravel())
    from scipy.sparse import coo_matrix

    n = vector_basis.N
    return coo_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(n, n)).tocsr()


def _vertex_dofs(basis: Basis) -> list[np.ndarray]:
    """For each displacement component, the DOF index at each mesh vertex."""
    nodal = basis.nodal_dofs  # (3 components, n_vertices) for vector P2
    return [nodal[c] for c in range(3)]


def _rigid_body_modes(basis: Basis) -> np.ndarray:
    locs = basis.doflocs
    centre = locs.mean(axis=1, keepdims=True)
    x, y, z = locs - centre
    modes = np.zeros((basis.N, 6))
    ix, iy, iz = basis.split_indices()
    modes[ix, 0] = 1.0
    modes[iy, 1] = 1.0
    modes[iz, 2] = 1.0
    modes[iy, 3], modes[iz, 3] = -z[iy], y[iz]
    modes[ix, 4], modes[iz, 4] = z[ix], -x[iz]
    modes[ix, 5], modes[iy, 5] = -y[ix], x[iy]
    return modes


def _nodal_von_mises(m: MeshTet, element, u: np.ndarray, lam: float, mu: float) -> np.ndarray:
    """Von Mises stress at element corners, averaged at each vertex."""
    corners = np.array([[0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
    weights = np.full(4, 1.0 / 24.0)
    basis = Basis(m, element, quadrature=(corners, weights))
    grad = basis.interpolate(u).grad  # (3, 3, n_elements, 4)
    eps = 0.5 * (grad + np.transpose(grad, (1, 0, 2, 3)))
    trace = eps[0, 0] + eps[1, 1] + eps[2, 2]
    s = 2.0 * mu * eps
    for i in range(3):
        s[i, i] += lam * trace
    vm = np.sqrt(
        0.5 * ((s[0, 0] - s[1, 1]) ** 2 + (s[1, 1] - s[2, 2]) ** 2 + (s[2, 2] - s[0, 0]) ** 2)
        + 3.0 * (s[0, 1] ** 2 + s[1, 2] ** 2 + s[2, 0] ** 2)
    )  # (n_elements, 4)

    # Corner order in the reference element matches m.t rows.
    total = np.zeros(m.p.shape[1])
    count = np.zeros(m.p.shape[1])
    np.add.at(total, m.t.T.ravel(), vm.ravel())
    np.add.at(count, m.t.T.ravel(), 1.0)
    return total / np.maximum(count, 1.0)
