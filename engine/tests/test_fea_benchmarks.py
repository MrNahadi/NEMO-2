"""Built-in FEA checked against problems with known answers.

1. Cantilever beam with an end load (beam theory with shear deflection).
2. Wide plate with a central hole in tension (stress concentration factor).
"""

from __future__ import annotations

import numpy as np
import pytest
from build123d import Box, Cylinder, Pos

from nemo.fea import SurfaceLoad, boundary_facets, mesh_part, solve_static, to_skfem

E = 210_000.0  # MPa
NU = 0.3


def test_cantilever_tip_deflection_and_bending_stress():
    length, width, depth, load = 200.0, 20.0, 20.0, 1000.0
    beam = Pos(length / 2, 0, 0) * Box(length, width, depth)
    m = to_skfem(mesh_part(beam, global_size_mm=5.0))

    fixed = boundary_facets(m, lambda x: x[0] < 1e-6)
    end = boundary_facets(m, lambda x: x[0] > length - 1e-6)
    result = solve_static(
        m,
        elastic_modulus_mpa=E,
        poisson_ratio=NU,
        fixed_facets=fixed,
        loads=[SurfaceLoad("end", end, lambda x: np.stack([0 * x[0], 0 * x[0], 1 + 0 * x[0]]),
                           np.array([0.0, 0.0, -load]))],
    )

    inertia = width * depth**3 / 12
    shear_modulus = E / (2 * (1 + NU))
    expected = load * length**3 / (3 * E * inertia) + load * length / (5 / 6 * shear_modulus * width * depth)
    tip = np.abs(m.p[0] - length) < 1e-6
    tip_deflection = -result.displacement[2, tip].mean()
    assert tip_deflection == pytest.approx(expected, rel=0.03)

    mid_surface = (np.abs(m.p[0] - length / 2) < 3.0) & (np.abs(np.abs(m.p[2]) - depth / 2) < 1e-6)
    expected_stress = load * (length / 2) * (depth / 2) / inertia  # 75 MPa
    assert result.max_von_mises_where(mid_surface) == pytest.approx(expected_stress, rel=0.04)

    assert result.reaction_balance_error < 1e-6
    assert result.applied_force_n == pytest.approx([0, 0, -load], abs=1e-6)


def test_plate_with_hole_stress_concentration():
    width, length, thickness, hole = 200.0, 800.0, 10.0, 20.0
    stress = 100.0
    plate = Box(length, width, thickness) - Cylinder(hole / 2, thickness * 2)

    def near_hole(kind, bbox):
        return kind == "Cylinder" and (bbox[3] - bbox[0]) < hole * 1.5

    m = to_skfem(mesh_part(plate, global_size_mm=12.0, local_size_mm=0.9,
                           refine_surface=near_hole, refine_distance_mm=40.0))
    fixed = boundary_facets(m, lambda x: x[0] < -length / 2 + 1e-6)
    pulled = boundary_facets(m, lambda x: x[0] > length / 2 - 1e-6)
    result = solve_static(
        m,
        elastic_modulus_mpa=E,
        poisson_ratio=NU,
        fixed_facets=fixed,
        loads=[SurfaceLoad("tension", pulled, lambda x: np.stack([1 + 0 * x[0], 0 * x[0], 0 * x[0]]),
                           np.array([stress * width * thickness, 0.0, 0.0]))],
    )

    # Heywood: Kt(net) = 2 + (1 - d/W)^3; Kt(gross) = Kt(net) / (1 - d/W) = 3.032 for d/W = 0.1
    ratio = hole / width
    kt_gross = (2 + (1 - ratio) ** 3) / (1 - ratio)
    at_hole = np.hypot(m.p[0], m.p[1]) < hole / 2 + 0.5
    peak = result.max_von_mises_where(at_hole)
    assert peak / stress == pytest.approx(kt_gross, rel=0.05)
    assert result.reaction_balance_error < 1e-6
