"""Padeye checks behave the way an engineer expects."""

from __future__ import annotations

import math
from dataclasses import replace

import pytest

from nemo.data import get_material, shackles, smallest_shackle_for
from nemo.loads import LiftScenario, padeye_loads
from nemo.parts.padeye import PadeyeDesign, check_padeye, minimum_fillet_size_mm
from nemo.rules import ASMEBTH1, get_rule_set

BASE = PadeyeDesign(
    main_thickness_mm=20,
    head_radius_mm=45,
    hole_diameter_mm=21,
    base_length_mm=200,
    hole_height_mm=90,
    weld_leg_mm=8,
)
LOADS = padeye_loads(LiftScenario(lifted_mass_kg=4000, lift_points=2, sling_angle_deg=60))
SHACKLE = smallest_shackle_for(LOADS.sling_force_t)
STEEL = get_material("S355")


def run(design=BASE, loads=LOADS, shackle=SHACKLE, rule_set=None, material=STEEL):
    return check_padeye(
        design, material=material, shackle=shackle, loads=loads, rule_set=rule_set or ASMEBTH1()
    )


def test_thinner_plate_is_lighter_and_weaker():
    thick, thin = run(), run(replace(BASE, main_thickness_mm=12))
    assert thin.mass_kg < thick.mass_kg
    for check_id in ("head_tension", "head_bearing", "head_shear_out", "head_fracture"):
        assert thin.check(check_id).capacity < thick.check(check_id).capacity


def test_bigger_head_increases_head_strength():
    small, big = run(), run(replace(BASE, head_radius_mm=60))
    assert big.check("head_shear_out").capacity > small.check("head_shear_out").capacity
    assert big.check("head_fracture").capacity > small.check("head_fracture").capacity
    assert big.mass_kg > small.mass_kg


def test_category_a_allows_more_than_b():
    a = run(rule_set=ASMEBTH1(design_category="A"))
    b = run(rule_set=ASMEBTH1(design_category="B"))
    assert a.check("head_bearing").capacity == pytest.approx(1.5 * b.check("head_bearing").capacity)


def test_high_cycle_service_reduces_bearing():
    low = run(rule_set=ASMEBTH1(service_class=0))
    high = run(rule_set=ASMEBTH1(service_class=2))
    assert high.check("head_bearing").capacity == pytest.approx(
        low.check("head_bearing").capacity * 0.63 / 1.25
    )


def test_cheek_plates_add_bearing_and_need_welds():
    with_cheeks = run(
        replace(BASE, main_thickness_mm=12, cheek_thickness_mm=5, cheek_radius_mm=40, cheek_weld_leg_mm=5)
    )
    without = run(replace(BASE, main_thickness_mm=12))
    assert with_cheeks.check("head_bearing").capacity > without.check("head_bearing").capacity
    assert with_cheeks.check("cheek_weld").demand > 0
    assert with_cheeks.design.total_thickness_mm == 22


def test_steeper_sling_reduces_base_bending():
    flat = run(loads=padeye_loads(LiftScenario(4000, 2, sling_angle_deg=45)))
    steep = run(loads=padeye_loads(LiftScenario(4000, 2, sling_angle_deg=90)))
    assert steep.check("base_combined").details["bending_in_plane_mpa"] == pytest.approx(0, abs=1e-6)
    assert flat.check("base_combined").demand > steep.check("base_combined").demand


def test_overload_fails():
    heavy = padeye_loads(LiftScenario(lifted_mass_kg=40000, lift_points=2, sling_angle_deg=60))
    result = run(loads=heavy, shackle=smallest_shackle_for(heavy.sling_force_t))
    assert not result.passed


def test_thick_padeye_does_not_fit_small_shackle():
    result = run(replace(BASE, main_thickness_mm=30))
    assert not result.check("shackle_fit").passed
    assert not result.passed


def test_advice_does_not_fail_design():
    # 3.25 t shackle jaw 26.9 mm; a 12 mm plate fills less than 60% of it.
    result = run(replace(BASE, main_thickness_mm=12, head_radius_mm=60, base_length_mm=260))
    assert not result.check("shackle_fill").passed
    assert result.check("shackle_fill").severity == "advice"
    assert all(c.passed for c in result.required_checks) == result.passed


def test_pin_larger_than_hole_is_reported():
    result = run(replace(BASE, hole_diameter_mm=18))
    assert not result.check("hole_fits_pin").passed


def test_invalid_geometry_is_explained():
    with pytest.raises(ValueError, match="hole height"):
        run(replace(BASE, hole_height_mm=30))
    with pytest.raises(ValueError, match="larger than the padeye head"):
        run(replace(BASE, hole_diameter_mm=95))


def test_geometry_area_matches_numeric_outline():
    design = replace(BASE, base_length_mm=260, hole_height_mm=120, head_radius_mm=55)
    poly = design.outline_polyline(arc_segments=4000)
    numeric = 0.5 * sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]))
    numeric -= math.pi * design.hole_diameter_mm**2 / 4
    assert design.main_plate_area_mm2() == pytest.approx(numeric, rel=1e-5)


def test_lift_scenario_validation():
    with pytest.raises(ValueError, match="Sling angle"):
        padeye_loads(LiftScenario(1000, 2, sling_angle_deg=5))
    with pytest.raises(ValueError, match="points carrying"):
        padeye_loads(LiftScenario(1000, 4, points_carrying=5))


def test_points_carrying_increases_load():
    all_four = padeye_loads(LiftScenario(8000, 4, 60))
    two_of_four = padeye_loads(LiftScenario(8000, 4, 60, points_carrying=2))
    assert two_of_four.sling_force_n == pytest.approx(2 * all_four.sling_force_n)


def test_material_yield_depends_on_thickness():
    s355 = get_material("S355")
    assert s355.yield_strength_mpa(16) == 355
    assert s355.yield_strength_mpa(20) == 345
    with pytest.raises(ValueError):
        s355.yield_strength_mpa(150)


def test_shackle_table_is_ordered_and_selects_smallest():
    wlls = [s.wll_t for s in shackles()]
    assert wlls == sorted(wlls)
    assert smallest_shackle_for(2.0).wll_t == 2.0
    assert smallest_shackle_for(2.01).wll_t == 3.25
    with pytest.raises(ValueError):
        smallest_shackle_for(500)


def test_minimum_fillet_sizes():
    assert minimum_fillet_size_mm(6) == 3
    assert minimum_fillet_size_mm(10) == 5
    assert minimum_fillet_size_mm(19) == 6
    assert minimum_fillet_size_mm(25) == 8


def test_rule_set_registry():
    rs = get_rule_set("asme-bth-1", design_category="A")
    assert rs.nd == 2.0
    with pytest.raises(KeyError):
        get_rule_set("dnv-st-0378")


def test_report_serialises():
    data = run().to_dict()
    assert data["passed"] is True
    assert {c["id"] for c in data["checks"]} >= {"head_bearing", "base_weld", "shackle_rating"}
