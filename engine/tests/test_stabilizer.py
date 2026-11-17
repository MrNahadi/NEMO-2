"""Stabilizer fin: hydrodynamics, IACS UR S10 checks, sizing, CAD and the stock FEA."""

from __future__ import annotations

import math

import pytest

from nemo.hydro import circle_contour, naca_00xx, panel_solve, section_lift_slope, whicker_fehlner
from nemo.parts.stabilizer import FinJob, check_fin
from nemo.parts.stabilizer.cad import build_fin
from nemo.parts.stabilizer.fea import analyse_stock
from nemo.parts.stabilizer.sizing import size_fin, stock_diameter
from nemo.rules import IACSS10

JOB = FinJob()


def test_panel_method_against_exact_flow_round_a_circle():
    xs, ys = circle_contour(160)
    result = panel_solve(xs, ys, 0.0)
    assert result.cp_min == pytest.approx(-3.0, abs=0.01)
    assert abs(result.cl) < 1e-9


def test_section_lift_slope_against_thick_foil_theory():
    for t in (0.12, 0.15, 0.20):
        assert section_lift_slope(t) == pytest.approx(2 * math.pi * (1 + 0.77 * t), rel=0.03)


def test_symmetric_section_has_no_lift_at_zero_angle():
    xs, ys = naca_00xx(0.15)
    assert abs(panel_solve(xs, ys, 0.0).cl) < 1e-6


def test_whicker_fehlner_values():
    cl, slope = whicker_fehlner(1.0, 0.0)
    assert slope == pytest.approx(0.9 * 2 * math.pi / (math.sqrt(5) + 1.8))
    cl20, _ = whicker_fehlner(1.0, 20.0)
    a = math.radians(20)
    assert cl20 == pytest.approx(slope * a + 0.8 * a**2)


def test_ur_s10_rudder_force_by_hand():
    # A = 1.68 m2, V = 18 kn, aspect ratio b^2/A = 1.4^2/1.68
    lam = 1.4**2 / 1.68
    expected = (lam + 2) / 3 * 1.10 * 0.8 * 132 * 1.68 * 18**2
    assert IACSS10.rudder_force_n(1.68, 18.0, lam) == pytest.approx(expected)
    assert IACSS10.rudder_force_n(1.0, 6.0, 1.0) == pytest.approx(1.0 * 1.10 * 0.8 * 132 * ((6 + 20) / 3) ** 2)


def test_material_factor():
    assert IACSS10.material_factor(235, 400) == pytest.approx(1.0)
    assert IACSS10.material_factor(355, 490) == pytest.approx((235 / 343) ** 0.75)  # 0.7 x 490 = 343 governs
    assert IACSS10.material_factor(650, 900) == pytest.approx((235 / 450) ** 0.75)  # capped at 450


def test_stock_for_pure_torsion_matches_ur_s10_formula():
    loads = JOB.loads
    no_bending = type(loads)(**{**loads.__dict__, "stock_moment_nm": 0.0, "astern_force_n": 0.0})
    d = stock_diameter(JOB, no_bending, 1.0)
    k = IACSS10.material_factor(JOB.stock_material.yield_strength_mpa(d), JOB.stock_material.tensile_strength_mpa)
    dt = 4.2 * (loads.torque_nm * k) ** (1 / 3)
    assert dt - 5.5 <= d <= dt + 5.5  # 5 mm steps; 4.2 is UR S10's rounding of (5.1e3 / 68)^(1/3)


def test_loads_use_the_larger_method():
    loads = JOB.loads
    assert loads.design_force_n == max(loads.nemo_lift_n, loads.ur_s10_force_n)
    assert loads.root_moment_nm == pytest.approx(loads.design_force_n * 0.5 * JOB.span_m)


def test_sizing_passes_and_grows_with_speed():
    slow = size_fin(JOB)
    assert slow.passed
    fast = size_fin(FinJob(speed_kn=22.0))
    assert fast.design.stock_diameter_mm > slow.design.stock_diameter_mm
    assert fast.mass_kg > slow.mass_kg


def test_fin_solid_is_one_piece_and_close_to_the_formula():
    report = size_fin(JOB)
    solid = build_fin(report.design)
    assert solid.solid_count == 1
    formula = sum(report.design.volumes_mm3().values())
    assert solid.volume_mm3 == pytest.approx(formula, rel=0.08)  # thin-wall formula


def test_stock_fea_matches_beam_theory():
    report = check_fin(size_fin(JOB).design, JOB, JOB.loads)
    study = analyse_stock(report.design, material=JOB.stock_material, loads=JOB.loads, levels=(1.0,))
    level = study.levels[-1]
    assert level.reaction_balance_error < 1e-8
    assert level.applied_force_n[1] == pytest.approx(JOB.loads.design_force_n, rel=1e-9)
    assert study.head_von_mises_mpa == pytest.approx(study.extra["hand_stress_mpa"], rel=0.04)
