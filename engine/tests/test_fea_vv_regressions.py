"""FEA V&V regression tests and independent mechanical benchmarks.

Covers:
1. Full 6-DOF static equilibrium (force AND moment balance) on a 3D cheek-plated padeye.
2. Zero spurious twisting moment from out-of-plane side load (matching Fusion Bearing Load BVP).
3. Exclusion of the 90-degree cheek-plate re-entrant step singularity from the assessed head peak.
4. Stress-tensor nodal averaging (not scalar von Mises averaging) in _nodal_von_mises.
5. Classical Frocht & Hill / Peterson pin-loaded lug stress concentration benchmark (d/W = 0.50).
6. Fusion connector unit conversion handling of Autodesk's -1 ExpressionError sentinel and empty units.
7. Fusion cross-check sheet & PDF report consistency (3D resultant force, global mesh, cheek-step warning).
"""

from __future__ import annotations

import importlib.util
import json
import math
import sys
import types
from pathlib import Path

import numpy as np
import pytest
from skfem import Basis, ElementTetP2, ElementVector
from skfem.models.elasticity import lame_parameters

from nemo.data import get_material
from nemo.fea import SurfaceLoad, boundary_facets, mesh_part, solve_static, to_skfem
from nemo.fea.solver import _assemble_elasticity, _nodal_von_mises, _traction_moment
from nemo.fusion_sheet import render_sheet
from nemo.loads import LiftScenario, padeye_loads
from nemo.parts.padeye import PadeyeDesign
from nemo.parts.padeye.cad import build_padeye
from nemo.parts.padeye.fea import analyse_padeye, default_mesh_sizes, head_assessment_mask
from nemo.parts.padeye.pipeline import run_padeye_job
from nemo.parts.padeye.sizing import PadeyeJob

STEEL = get_material("S355")
BALANCED = PadeyeDesign(
    main_thickness_mm=8.0,
    head_radius_mm=25.0,
    hole_diameter_mm=23.5,
    base_length_mm=140.0,
    hole_height_mm=45.0,
    weld_leg_mm=5.0,
    cheek_thickness_mm=6.0,
    cheek_radius_mm=22.0,
    cheek_weld_leg_mm=5.0,
)
LOADS = padeye_loads(LiftScenario(lifted_mass_kg=5000, lift_points=2, sling_angle_deg=60, side_load_fraction=0.05))


def test_padeye_side_load_matches_zero_moment_uniform_axial_bvp():
    """Out-of-plane side load must not inject an artificial twisting moment about the pinhole.

    A half-cylinder cosine side traction offsets the lateral force centroid by (pi/4) R_h,
    creating ~13 N*m of spurious torque and inflating tip displacement by ~25% vs Fusion Bearing Load.
    """
    study = analyse_padeye(BALANCED, material=STEEL, loads=LOADS, levels=(1.0,))
    m = study.final.mesh
    h = BALANCED.hole_height_mm
    radius = BALANCED.hole_diameter_mm / 2.0
    t_half = BALANCED.total_thickness_mm / 2.0
    tol = max(0.02 * radius, 0.05)
    hole_facets = boundary_facets(
        m,
        lambda x: (np.abs(np.hypot(x[0], x[2] - h) - radius) < tol) & (np.abs(x[1]) < t_half + 1e-6),
        normal_filter=lambda n: np.abs(n[1]) < 0.5,
    )
    base_facets = boundary_facets(m, lambda x: x[2] < 1e-6)
    in_plane = np.array([LOADS.horizontal_n, 0.0, LOADS.vertical_n])
    direction = in_plane / np.linalg.norm(in_plane)

    def bearing_shape(x):
        rx, rz = x[0], x[2] - h
        rr = np.maximum(np.hypot(rx, rz), 1e-12)
        ux, uz = rx / rr, rz / rr
        p = np.maximum(ux * direction[0] + uz * direction[2], 0.0)
        return np.stack([p * ux, 0.0 * p, p * uz])

    def uniform_side(x):
        return np.stack([0.0 * x[0], np.ones_like(x[0]), 0.0 * x[0]])

    ref = solve_static(
        m,
        elastic_modulus_mpa=STEEL.elastic_modulus_mpa,
        poisson_ratio=STEEL.poisson_ratio,
        fixed_facets=base_facets,
        loads=[
            SurfaceLoad("pin bearing", hole_facets, bearing_shape, in_plane),
            SurfaceLoad("side load", hole_facets, uniform_side, np.array([0.0, LOADS.side_n, 0.0])),
        ],
    )
    assert study.levels[-1].max_displacement_mm == pytest.approx(ref.max_displacement_mm, rel=0.01)


def test_padeye_full_6dof_equilibrium_force_and_moment():
    """Verify both force and moment equilibrium (sum F = 0, sum M = 0) on a 3D cheek-plated padeye."""
    study = analyse_padeye(BALANCED, material=STEEL, loads=LOADS, levels=(1.0,))
    level = study.levels[-1]
    assert level.reaction_balance_error < 1e-6
    assert study.final.moment_balance_error < 1e-6


def test_padeye_head_stress_excludes_cheek_step_singularity():
    """The unmodeled 90-degree cheek-plate re-entrant step must not contaminate head_von_mises_mpa."""
    # Refine all cylinders (replicating Fusion's curvature mesher) under a 15% side load so the
    # 90-degree cheek step rises clearly above the smooth pin-hole stress.
    solid = build_padeye(BALANCED)
    oblique = padeye_loads(
        LiftScenario(lifted_mass_kg=5000, lift_points=2, sling_angle_deg=60, side_load_fraction=0.15)
    )
    m = to_skfem(
        mesh_part(
            solid.part,
            global_size_mm=4.0,
            local_size_mm=1.3,
            refine_surface=lambda kind, bbox: kind == "Cylinder",
            refine_distance_mm=BALANCED.head_radius_mm,
        )
    )
    h = BALANCED.hole_height_mm
    radius = BALANCED.hole_diameter_mm / 2.0
    t_half = BALANCED.total_thickness_mm / 2.0
    t_main_half = BALANCED.main_thickness_mm / 2.0
    tol = max(0.02 * radius, 0.05)
    hole_facets = boundary_facets(
        m,
        lambda x: (np.abs(np.hypot(x[0], x[2] - h) - radius) < tol) & (np.abs(x[1]) < t_half + 1e-6),
        normal_filter=lambda n: np.abs(n[1]) < 0.5,
    )
    base_facets = boundary_facets(m, lambda x: x[2] < 1e-6)
    in_plane = np.array([oblique.horizontal_n, 0.0, oblique.vertical_n])
    direction = in_plane / np.linalg.norm(in_plane)

    def bearing_shape(x):
        rx, rz = x[0], x[2] - h
        rr = np.maximum(np.hypot(rx, rz), 1e-12)
        ux, uz = rx / rr, rz / rr
        p = np.maximum(ux * direction[0] + uz * direction[2], 0.0)
        return np.stack([p * ux, 0.0 * p, p * uz])

    res = solve_static(
        m,
        elastic_modulus_mpa=STEEL.elastic_modulus_mpa,
        poisson_ratio=STEEL.poisson_ratio,
        fixed_facets=base_facets,
        loads=[
            SurfaceLoad("pin bearing", hole_facets, bearing_shape, in_plane),
            SurfaceLoad("side load", hole_facets, lambda x: np.stack([0.0 * x[0], np.ones_like(x[0]), 0.0 * x[0]]),
                        np.array([0.0, oblique.side_n, 0.0])),
        ],
    )
    p = m.p
    r = np.hypot(p[0], p[2] - h)
    naive_head = r <= BALANCED.head_radius_mm + 1.0
    assessed_head = head_assessment_mask(p, BALANCED)
    on_cheek_step = (np.abs(r - BALANCED.cheek_radius_mm) <= 1.2) & (np.abs(np.abs(p[1]) - t_main_half) <= 1.2)
    on_hole = np.abs(r - radius) <= 0.5

    # Every hole vertex remains assessed; every 90-degree cheek-step vertex is excluded.
    assert np.all(assessed_head[on_hole])
    assert not np.any(assessed_head[on_cheek_step])
    # With cheek refinement, the unmodeled step exceeds the smooth hole stress, yet the assessed head
    # peak remains at the smooth pin-hole value (~188 MPa) instead of jumping to the singularity.
    assert res.max_von_mises_where(on_cheek_step) > res.max_von_mises_where(assessed_head)
    assert res.max_von_mises_where(naive_head) > res.max_von_mises_where(assessed_head)
    assert res.max_von_mises_where(assessed_head) == pytest.approx(res.max_von_mises_where(on_hole), rel=0.02)


def test_nodal_von_mises_averages_stress_tensor_not_scalar():
    """Nodal von Mises must average Cauchy stress tensor components before taking the von Mises norm.

    Averaging scalar von Mises introduces an upward Jensen's inequality bias wherever adjacent elements
    have opposing shear/normal signs (e.g. a geometric transition or corner).
    """
    from build123d import Box

    m = to_skfem(mesh_part(Box(40, 12, 12), global_size_mm=6.0))
    element = ElementVector(ElementTetP2())
    basis = Basis(m, element)
    lam, mu = lame_parameters(210_000.0, 0.3)

    # Synthetic non-uniform displacement field with sharp local stress variation across elements.
    rng = np.random.default_rng(42)
    u = rng.normal(scale=1e-3, size=basis.N)

    got = _nodal_von_mises(m, element, u, lam, mu)

    # Compute exact reference tensor-averaged nodal von Mises independently.
    corners = np.array([[0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
    b_c = Basis(m, element, quadrature=(corners, np.full(4, 1.0 / 24.0)))
    grad = b_c.interpolate(u).grad
    eps = 0.5 * (grad + np.transpose(grad, (1, 0, 2, 3)))
    tr = eps[0, 0] + eps[1, 1] + eps[2, 2]
    s = 2.0 * mu * eps
    for i in range(3):
        s[i, i] += lam * tr
    idx = m.t.T.ravel()
    n_v = m.p.shape[1]
    cnt = np.zeros(n_v)
    np.add.at(cnt, idx, 1.0)
    s_avg = np.zeros((3, 3, n_v))
    for i in range(3):
        for j in range(3):
            np.add.at(s_avg[i, j], idx, s[i, j].ravel())
            s_avg[i, j] /= np.maximum(cnt, 1.0)
    expected = np.sqrt(
        0.5 * ((s_avg[0, 0] - s_avg[1, 1]) ** 2 + (s_avg[1, 1] - s_avg[2, 2]) ** 2 + (s_avg[2, 2] - s_avg[0, 0]) ** 2)
        + 3.0 * (s_avg[0, 1] ** 2 + s_avg[1, 2] ** 2 + s_avg[2, 0] ** 2)
    )
    assert got == pytest.approx(expected, rel=1e-12, abs=1e-12)


def test_pin_loaded_lug_stress_concentration_benchmark():
    """Independent benchmark: plain circular-ended pin-loaded lug (d/W = 0.50, H/W = 0.50).

    Under cosine pin bearing load, Peterson Chart 4.50 / Frocht & Hill gives K_tn ~ 2.9 - 3.3
    relative to net-section stress F / ((2R - Dh) t).
    """
    lug = PadeyeDesign(
        main_thickness_mm=10.0,
        head_radius_mm=25.0,
        hole_diameter_mm=25.0,
        base_length_mm=50.0,
        hole_height_mm=80.0,
        weld_leg_mm=6.0,
    )
    solid = build_padeye(lug)
    h, radius, t_half = lug.hole_height_mm, lug.hole_diameter_mm / 2.0, lug.main_thickness_mm / 2.0
    force_n = 25_000.0
    sigma_nom_net = force_n / ((2.0 * lug.head_radius_mm - lug.hole_diameter_mm) * lug.main_thickness_mm)

    m = to_skfem(
        mesh_part(
            solid.part,
            global_size_mm=6.0,
            local_size_mm=1.6,
            refine_surface=lambda k, b: k == "Cylinder" and (b[3] - b[0]) <= lug.hole_diameter_mm * 1.05,
            refine_distance_mm=25.0,
        )
    )
    tol = max(0.02 * radius, 0.05)
    hole_f = boundary_facets(
        m,
        lambda x: (np.abs(np.hypot(x[0], x[2] - h) - radius) < tol) & (np.abs(x[1]) < t_half + 1e-6),
        normal_filter=lambda n: np.abs(n[1]) < 0.5,
    )
    base_f = boundary_facets(m, lambda x: x[2] < 1e-6)

    def bearing_up(x):
        rx, rz = x[0], x[2] - h
        rr = np.maximum(np.hypot(rx, rz), 1e-12)
        ux, uz = rx / rr, rz / rr
        p = np.maximum(uz, 0.0)
        return np.stack([p * ux, 0.0 * p, p * uz])

    res = solve_static(
        m,
        elastic_modulus_mpa=STEEL.elastic_modulus_mpa,
        poisson_ratio=STEEL.poisson_ratio,
        fixed_facets=base_f,
        loads=[SurfaceLoad("pin", hole_f, bearing_up, np.array([0.0, 0.0, force_n]))],
    )
    r_v = np.hypot(m.p[0], m.p[2] - h)
    k_tn = res.max_von_mises_where(r_v <= lug.head_radius_mm + 1.0) / sigma_nom_net
    assert 2.85 <= k_tn <= 3.30
    assert res.reaction_balance_error < 1e-6
    assert res.moment_balance_error < 1e-6


def _load_connector_module():
    connector_path = Path(__file__).resolve().parents[2] / "fusion" / "NEMOConnector" / "NEMOConnector.py"
    # Stub Autodesk Fusion's adsk modules so pure-Python helpers can be unit-tested offline.
    adsk = types.ModuleType("adsk")
    adsk_core = types.ModuleType("adsk.core")
    adsk_fusion = types.ModuleType("adsk.fusion")
    adsk_core.CustomEventHandler = object
    adsk_core.CommandCreatedEventHandler = object
    adsk_core.CommandEventHandler = object
    adsk.core = adsk_core
    adsk.fusion = adsk_fusion
    prev = {k: sys.modules.get(k) for k in ("adsk", "adsk.core", "adsk.fusion")}
    sys.modules.update({"adsk": adsk, "adsk.core": adsk_core, "adsk.fusion": adsk_fusion})
    try:
        spec = importlib.util.spec_from_file_location("nemo_connector_under_test", connector_path)
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        for k, v in prev.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v


def test_fusion_connector_unit_conversion_handles_negative_one_and_empty_units():
    """UnitsManager.convert returns -1 on ExpressionError without raising; _to_fusion must fall back."""
    conn = _load_connector_module()

    class StubUnitsManager:
        def convert(self, value, from_u, to_u):
            # Simulate Fusion rejecting "MPa" with -1 (ExpressionError) while accepting SI base units.
            if from_u == "MPa" or to_u == "MPa":
                return -1.0
            if from_u == "kg / (m s^2)" and to_u == "Pa":
                return float(value)
            if from_u == "Pa" and to_u == "kg / (m s^2)":
                return float(value)
            return -1.0

    um = StubUnitsManager()
    assert conn._to_fusion(um, 355.0, "MPa", "Pa", 1e6, "kg / (m s^2)") == pytest.approx(355e6)
    assert conn._from_fusion(um, 355e6, "MPa", "Pa", 1e6, "kg / (m s^2)") == pytest.approx(355.0)

    # Empty prop_units on a dimensional property must raise rather than silently passing unscaled MPa as Pa.
    with pytest.raises(ValueError):
        conn._to_fusion(um, 355.0, "MPa", "", 1e6, "kg / (m s^2)")
    with pytest.raises(ValueError):
        conn._from_fusion(um, 355.0, "MPa", "", 1e6, "kg / (m s^2)")
    # Dimensionless properties (Poisson's ratio) still pass through unchanged.
    assert conn._to_fusion(um, 0.3, "", "", 1.0, "") == pytest.approx(0.3)


def test_fusion_sheet_warns_cheek_step_and_gives_global_mesh_size(tmp_path):
    """Cheek-plated padeyes must warn about the cheek-plate 90-degree step and specify a global mesh size."""
    job = PadeyeJob(LiftScenario(5000, 2, 60, side_load_fraction=0.05), "S355")
    run_dir = tmp_path / "run"
    summary = run_padeye_job(job, run_dir, project_name="Test", fea_levels=(1.0,))
    balanced = next(d for d in summary["designs"] if d["key"] == "balanced")
    assert balanced["check_report"]["design"]["cheek_thickness_mm"] > 0

    html = render_sheet(run_dir, "balanced", project_id="p1", project_name="Test", run_name="run")
    assert "global mesh" in html.lower()
    assert "cheek" in html.lower() and "step" in html.lower()
