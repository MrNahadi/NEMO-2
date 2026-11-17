"""Advanced settings: oblique slings on padeyes, bracket flexibility, fin astern condition and stock bearings."""

from __future__ import annotations

import math

import pytest

from nemo.data import shackle_side_load_factor, shackles
from nemo.loads import LiftScenario, padeye_loads
from nemo.parts.bracket.checks import check_bracket
from nemo.parts.bracket.job import BracketJob, span_analysis
from nemo.parts.bracket.sizing import size_bracket
from nemo.parts.padeye.sizing import PadeyeJob, size_padeye
from nemo.parts.padeye.working import explain
from nemo.parts.stabilizer.checks import check_fin
from nemo.parts.stabilizer.job import FinJob
from nemo.parts.stabilizer.sizing import size_fin


# ------------------------------------------------------------------ padeye
def test_oblique_sling_components_by_hand():
    s = LiftScenario(5000, 2, 60.0, out_of_plane_angle_deg=30.0)
    loads = padeye_loads(s)
    f = 5000 * 9.80665 / 2 / math.sin(math.radians(60))
    assert loads.sling_force_n == pytest.approx(f)
    assert loads.horizontal_n == pytest.approx(f * math.cos(math.radians(60)) * math.cos(math.radians(30)))
    assert loads.side_n == pytest.approx(f * math.cos(math.radians(60)) * math.sin(math.radians(30)))
    assert loads.side_angle_deg == pytest.approx(math.degrees(math.asin(0.5 * 0.5)))
    # The in-plane part and the sideways part add back up to the sling force.
    assert math.hypot(math.hypot(loads.horizontal_n, loads.vertical_n), loads.side_n) == pytest.approx(f)


def test_lined_up_padeye_is_unchanged_and_allowance_still_applies():
    plain = padeye_loads(LiftScenario(5000, 2, 60.0))
    assert plain.side_angle_deg == 0.0 and plain.side_n == pytest.approx(0.05 * plain.sling_force_n)
    small = padeye_loads(LiftScenario(5000, 2, 60.0, out_of_plane_angle_deg=2.0))
    assert small.side_n == pytest.approx(0.05 * small.sling_force_n)  # the allowance is larger than the real part


@pytest.mark.parametrize("angle,factor", [(0, 1.0), (10, 1.0), (15, 0.85), (25, 0.75), (40, 0.70), (50, 0.60), (60, 0.55), (90, 0.50)])
def test_crosby_side_loading_table(angle, factor):
    small = next(s for s in shackles() if s.wll_t == 4.75)
    assert shackle_side_load_factor(small, angle) == factor


def test_large_shackles_allow_only_small_side_angles():
    big = next(s for s in shackles() if s.wll_t == 150.0)
    assert shackle_side_load_factor(big, 4) == 1.0
    assert shackle_side_load_factor(big, 8) == 0.85
    assert shackle_side_load_factor(big, 15) == 0.0


def test_oblique_sling_needs_a_bigger_shackle():
    lined_up = size_padeye(PadeyeJob(LiftScenario(5000, 2, 60.0)), quick=True)
    oblique = explain(size_padeye(PadeyeJob(LiftScenario(5000, 2, 60.0, out_of_plane_angle_deg=45.0)), quick=True))
    assert oblique.shackle.wll_t > lined_up.shackle.wll_t
    rating = oblique.check("shackle_rating")
    assert rating.capacity == pytest.approx(0.75 * oblique.shackle.wll_t)
    assert rating.working[-1].value == pytest.approx(rating.capacity)
    assert "side loading" in rating.source


def test_oblique_angle_round_trips_through_the_job():
    job = PadeyeJob(LiftScenario(5000, 2, 60.0, out_of_plane_angle_deg=20.0))
    assert PadeyeJob.from_dict(job.to_dict()).scenario.out_of_plane_angle_deg == 20.0
    assert PadeyeJob.from_dict({"lift": {"lifted_mass_kg": 1000}}).scenario.out_of_plane_angle_deg == 0.0


# ----------------------------------------------------------------- bracket
def test_bracket_flexibility_lowers_the_frequency_by_dunkerley():
    job = BracketJob(pipe_nps="12")
    design = size_bracket(job, quick=True).design
    span = span_analysis(job, job.loads)
    report = check_bracket(design, job, job.loads, span, working=True)
    c = report.check("support_vibration")
    f_n, f_b, f_c = span.natural_hz, c.details["bracket_hz"], c.details["combined_hz"]
    assert f_c == pytest.approx(1.0 / math.sqrt(1.0 / f_n**2 + 1.0 / f_b**2))
    assert f_c < f_n
    k = job.loads.down_n / report.values["deflection_mm"] * 1000.0
    assert f_b == pytest.approx(math.sqrt(k / (job.loads.static_n / 9.80665)) / (2 * math.pi))
    assert c.working[-2].value == pytest.approx(f_c)


def test_bracket_flexibility_can_be_switched_off():
    job = BracketJob(include_bracket_flexibility=False)
    report = check_bracket(size_bracket(job, quick=True).design, job, job.loads, span_analysis(job, job.loads))
    assert all(c.id != "support_vibration" for c in report.checks)


# --------------------------------------------------------------------- fin
def test_astern_force_and_torque_by_hand():
    job = FinJob()
    loads = job.loads
    k1 = (min(job.span_m**2 / job.area_m2, 2.0) + 2.0) / 3.0
    v_ast = 0.5 * job.speed_kn
    cr = k1 * 0.80 * 0.8 * 132 * job.area_m2 * v_ast**2
    assert loads.astern_speed_kn == pytest.approx(v_ast)
    assert loads.astern_force_n == pytest.approx(cr)
    assert loads.astern_torque_nm == pytest.approx(cr * job.chord_m * (0.66 - job.stock_position))
    assert loads.astern_stock_moment_nm == pytest.approx(cr * (0.5 * job.span_m + job.bearing_gap_mm / 1000))


def test_astern_governs_the_twist_when_the_stock_is_far_forward():
    job = FinJob(stock_position=0.2, front_spar=0.1, speed_kn=12.0, astern_speed_kn=12.0)
    report = check_fin(size_fin(job, quick=True).design, job, job.loads)
    assert job.loads.astern_torque_nm > job.loads.torque_nm
    assert report.check("stock_torsion").details["condition"] == "astern"


def test_bearing_reactions_and_lengths():
    job = FinJob(check_bearings=True, bearing_spacing_mm=800.0)
    loads = job.loads
    a = 0.5 * job.span_m + job.bearing_gap_mm / 1000
    assert loads.outer_bearing_n == pytest.approx(loads.design_force_n * (a + 0.8) / 0.8)
    assert loads.inner_bearing_n == pytest.approx(loads.design_force_n * a / 0.8)
    report = size_fin(job, quick=True)
    outer = report.check("outer_bearing")
    d_b = report.design.stock_diameter_mm + 16.0
    assert outer.demand == pytest.approx(loads.outer_bearing_n / (5.5 * d_b))
    assert outer.capacity == pytest.approx(1.2 * d_b)
    assert outer.passed


def test_close_bearings_make_the_stock_bigger():
    plain = size_fin(FinJob(), quick=True)
    close = size_fin(FinJob(check_bearings=True, bearing_spacing_mm=400.0), quick=True)
    assert close.design.stock_diameter_mm > plain.design.stock_diameter_mm
    assert close.check("outer_bearing").passed


def test_fin_defaults_keep_bearings_off():
    report = size_fin(FinJob(), quick=True)
    assert all(not c.id.endswith("_bearing") for c in report.checks)
    assert FinJob.from_dict(FinJob(check_bearings=True, bearing_material="bronze").to_dict()).bearing_material == "bronze"
