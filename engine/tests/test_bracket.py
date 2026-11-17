"""Pipe support bracket: loads by hand, pipe span, checks, sizing, CAD and FEA."""

from __future__ import annotations

import math

import pytest

from nemo.parts.bracket import BracketDesign, BracketJob, bracket_loads, check_bracket, span_analysis
from nemo.parts.bracket.cad import build_bracket
from nemo.parts.bracket.fea import analyse_bracket
from nemo.parts.bracket.sizing import size_bracket

JOB = BracketJob()  # NPS 4 STD carbon steel, sea water, 3 m spacing


def test_pipe_weight_by_hand():
    loads = bracket_loads(JOB)
    od, wall = 114.3, 6.02
    bore = od - 2 * wall
    pipe = math.pi / 4 * (od**2 - bore**2) * 1e-6 * 7850
    water = math.pi / 4 * bore**2 * 1e-6 * 1025
    assert loads.mass_per_m["pipe"] == pytest.approx(pipe, rel=1e-9)
    assert loads.mass_per_m["contents"] == pytest.approx(water, rel=1e-9)
    w = 1.25 * (pipe + water) * 9.80665 * 3.0
    assert loads.static_n == pytest.approx(w, rel=1e-9)
    assert loads.down_n == pytest.approx(2.0 * w)
    assert loads.across_n == pytest.approx(0.8 * w)  # fore and aft pipe: athwartships acceleration
    assert loads.along_n == pytest.approx(0.3 * 2.0 * w)
    assert loads.up_n == 0.0


def test_pipe_direction_picks_the_acceleration():
    loads = bracket_loads(BracketJob(pipe_direction="athwartships"))
    assert loads.across_n == pytest.approx(0.5 * loads.static_n)


def test_span_frequency_and_limits():
    loads = bracket_loads(JOB)
    span = span_analysis(JOB, loads)
    od, wall = 114.3, 6.02
    i = math.pi / 64 * (od**4 - (od - 2 * wall) ** 4) * 1e-12
    expected = math.pi / 2 * math.sqrt(203e9 * i / (loads.mass_per_m["total"] * 3.0**4))
    assert span.natural_hz == pytest.approx(expected, rel=1e-9)
    names = {n for n, _ in span.excitations}
    assert "Engine firing" in names and "Propeller blade rate" in names
    assert dict(span.excitations)["Engine firing"] == pytest.approx(6 * 750 / 60 / 2)
    # At the recommended spacing the pipe is at least 20% above the highest excitation.
    at_max = span_analysis(BracketJob(span_m=span.spans_m["frequency"]), bracket_loads(BracketJob(span_m=span.spans_m["frequency"])))
    assert at_max.natural_hz == pytest.approx(1.2 * max(f for _, f in span.excitations), rel=1e-6)


def test_section_properties_by_hand():
    d = BracketDesign(200, 100, 10, 80, 8, 110, 114.3, 12, 6, 6)
    sec = d.section_at(0.0)
    a_f, a_w = 100 * 10, 2 * 8 * 80
    zc = (a_f * -5 + a_w * -50) / (a_f + a_w)
    iy = 100 * 10**3 / 12 + a_f * (-5 - zc) ** 2 + 2 * 8 * 80**3 / 12 + a_w * (-50 - zc) ** 2
    assert sec.centroid_z_mm == pytest.approx(zc)
    assert sec.inertia_y_mm4 == pytest.approx(iy)
    assert d.section_at(200.0).knee_depth_mm == 0.0


def test_vibration_check_fails_near_an_excitation():
    loads = bracket_loads(JOB)
    span = span_analysis(JOB, loads)
    resonant = BracketJob(engine_rpm=span.natural_hz * 60 * 2 / 6)  # firing exactly at the pipe span frequency
    r = check_bracket(size_bracket(resonant).design, resonant, resonant.loads, span_analysis(resonant, resonant.loads))
    assert not r.check("pipe_vibration").passed
    assert not r.passed


def test_sizing_finds_a_buildable_bracket():
    report = size_bracket(JOB)
    d = report.design
    assert all(c.passed for c in report.required_checks if c.category != "span")
    assert d.seat_thickness_mm in JOB.plate_thicknesses_mm and d.knee_thickness_mm in JOB.plate_thicknesses_mm
    assert d.knee_depth_mm % 5 == 0 and d.seat_width_mm % 5 == 0
    assert not d.problems()
    worked = check_bracket(d, JOB, JOB.loads, span_analysis(JOB, JOB.loads), working=True)
    assert all(c.working for c in worked.checks)


def test_heavier_pipe_needs_more_steel():
    light = size_bracket(JOB)
    heavy_job = BracketJob(pipe_nps="8", span_m=3.0)
    heavy = size_bracket(heavy_job)
    assert heavy.mass_kg > light.mass_kg


def test_cad_volume_matches_formula():
    d = size_bracket(JOB).design
    solid = build_bracket(d)
    assert solid.solid_count == 1
    assert solid.volume_mm3 == pytest.approx(d.volume_mm3(), rel=1e-6)


def test_fea_balances_and_is_near_the_hand_calculation():
    report = check_bracket(size_bracket(JOB).design, JOB, JOB.loads, span_analysis(JOB, JOB.loads))
    study = analyse_bracket(report.design, material=JOB.material, loads=JOB.loads, levels=(1.0,))
    level = study.levels[-1]
    assert level.reaction_balance_error < 1e-8
    assert level.applied_force_n[2] == pytest.approx(-JOB.loads.down_n, rel=1e-9)
    hand = max(report.values["governing_stress_mpa"], report.check("seat_bending").demand)
    assert 0.5 * hand < study.head_von_mises_mpa < 2.0 * hand
