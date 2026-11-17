"""Padeye checks compared with an independent hand calculation.

Worked example (calculated by hand, step by step, before running the code):

Lift: 4,000 kg on 2 padeyes, slings at 60 degrees from horizontal, no extra
dynamic factor, 5% sideways load.
  vertical per padeye  V = 4000 x 9.80665 / 2          = 19,613.3 N
  sling force          F = V / sin 60                   = 22,647.6 N  (2.309 t)
  in-plane horizontal  H = F cos 60                     = 11,323.8 N
  sideways             Q = 0.05 F                       =  1,132.4 N
Shackle: smallest Crosby G-2130 >= 2.309 t is 3.25 t: jaw 26.9 mm, pin 19.1 mm.
Padeye: S355, main plate 20 mm (Fy = 345 MPa for 16-40 mm, Fu = 470 MPa),
head radius R = 45, hole 21, base 200, hole height 90, base weld leg 8.
ASME BTH-1 design category B: Nd = 3.00, pin-connected plates 1.20 Nd = 3.60.

Head
  Cr   = 1 - 0.275 sqrt(1 - (19.1/21)^2)                = 0.885696
  be   = 45 - 10.5                                      = 34.5 mm
  beff = min(34.5, 80, 34.5 x 0.6 x 470/345 x sqrt(21/34.5)) = 22.0013 mm
  Pt   = Cr Fu 2 t beff / 3.6                           = 101,763 N
  Pb   = Cr Fu [1.13 x 34.5 + 0.92 x 34.5 / (1 + 34.5/21)] t / 3.6 = 117,933 N
  phi  = 55 x 19.1/21                                   = 50.0238 deg
  Z    = 45 - sqrt(45^2 - (9.55 sin phi)^2)             = 0.59907 mm
  Av   = 2 (34.5 + 9.55 (1 - cos phi) - Z) 20           = 1,492.61 mm2
  Pv   = 0.70 x 470 x Av / 3.6                          = 136,408 N
  Pp   = 1.25 x 345 x 19.1 x 20 / 3                     = 54,912.5 N
Base section (200 x 20)
  axial 19,613.3/4000 = 4.9033 MPa; in-plane bending 11,323.8 x 90 / 133,333 = 7.6436 MPa
  side bending 1,132.4 x 90 / 13,333 = 7.6436 MPa
  Lb d / t^2 = 90 x 200 / 400 = 45 < 0.08 E/Fy = 48.70, so Fb = 1.25 Fy / Nd = 143.75 MPa
  interaction = 4.9033/115 + 7.6436/143.75 + 7.6436/143.75 = 0.14898
Base weld (two 8 mm fillets, throat 5.6568 mm, separation 25.6568 mm)
  normal = 19,613.3/2262.72 + 1,019,142/75,424 + 101,914/29,027.0 = 25.691 MPa
  shear  = 11,380.3/2262.72 = 5.0295 MPa; resultant = 26.179 MPa
  allowable = 0.60 x 482 / 3.6 = 80.333 MPa
Mass: outline area 16,533.7 mm2 (including hole removal) x 20 mm x 7850 kg/m3 = 2.5958 kg
"""

from __future__ import annotations

import pytest

from nemo.data import get_material, smallest_shackle_for
from nemo.loads import LiftScenario, padeye_loads
from nemo.parts.padeye import PadeyeDesign, check_padeye
from nemo.rules import ASMEBTH1

REL = 1e-3


@pytest.fixture()
def report():
    loads = padeye_loads(LiftScenario(lifted_mass_kg=4000, lift_points=2, sling_angle_deg=60))
    shackle = smallest_shackle_for(loads.sling_force_t)
    design = PadeyeDesign(
        main_thickness_mm=20,
        head_radius_mm=45,
        hole_diameter_mm=21,
        base_length_mm=200,
        hole_height_mm=90,
        weld_leg_mm=8,
    )
    return check_padeye(
        design,
        material=get_material("S355"),
        shackle=shackle,
        loads=loads,
        rule_set=ASMEBTH1(design_category="B"),
    )


def test_loads(report):
    loads = report.loads
    assert loads.vertical_n == pytest.approx(19613.3, rel=REL)
    assert loads.sling_force_n == pytest.approx(22647.6, rel=REL)
    assert loads.horizontal_n == pytest.approx(11323.8, rel=REL)
    assert loads.side_n == pytest.approx(1132.38, rel=REL)
    assert loads.sling_force_t == pytest.approx(2.309, rel=REL)


def test_shackle_selection(report):
    assert report.shackle.wll_t == 3.25
    assert report.shackle.pin_diameter_mm == 19.1
    assert report.shackle.jaw_width_mm == 26.9


def test_head_capacities(report):
    assert report.values["strength_reduction_factor_cr"] == pytest.approx(0.885696, rel=REL)
    assert report.values["effective_width_mm"] == pytest.approx(22.0013, rel=REL)
    assert report.check("head_tension").capacity == pytest.approx(101763, rel=REL)
    assert report.check("head_fracture").capacity == pytest.approx(117933, rel=REL)
    assert report.values["shear_plane_angle_deg"] == pytest.approx(50.0238, rel=REL)
    assert report.values["curvature_loss_mm"] == pytest.approx(0.59907, rel=REL)
    assert report.values["shear_area_mm2"] == pytest.approx(1492.61, rel=REL)
    assert report.check("head_shear_out").capacity == pytest.approx(136408, rel=REL)
    assert report.check("head_bearing").capacity == pytest.approx(54912.5, rel=REL)


def test_base_section(report):
    combined = report.check("base_combined")
    assert combined.details["axial_mpa"] == pytest.approx(4.9033, rel=REL)
    assert combined.details["bending_in_plane_mpa"] == pytest.approx(7.6436, rel=REL)
    assert combined.details["bending_side_mpa"] == pytest.approx(7.6436, rel=REL)
    assert combined.details["allow_bending_in_plane_mpa"] == pytest.approx(143.75, rel=REL)
    assert combined.demand == pytest.approx(0.14898, rel=REL)
    assert report.check("base_shear").demand == pytest.approx(2.84508, rel=REL)
    assert report.check("base_shear").capacity == pytest.approx(66.3953, rel=REL)


def test_base_weld(report):
    weld = report.check("base_weld")
    assert weld.details["normal_mpa"] == pytest.approx(25.691, rel=REL)
    assert weld.details["shear_mpa"] == pytest.approx(5.0295, rel=REL)
    assert weld.demand == pytest.approx(26.179, rel=REL)
    assert weld.capacity == pytest.approx(80.333, rel=REL)


def test_mass(report):
    assert report.design.main_plate_area_mm2() == pytest.approx(16533.7, rel=REL)
    assert report.mass_kg == pytest.approx(2.5958, rel=REL)


def test_overall_result(report):
    assert report.passed
    # The 3.25 t shackle is used at 2.309 / 3.25 = 71%; the plate's worst check is bearing at 41%.
    assert report.governing.id == "shackle_rating"
    assert report.governing.utilization == pytest.approx(2.309 / 3.25, rel=REL)
    plate = [c for c in report.required_checks if c.category == "strength" and c.id != "shackle_rating"]
    worst_plate = max(plate, key=lambda c: c.utilization)
    assert worst_plate.id == "head_bearing"
    assert worst_plate.utilization == pytest.approx(22647.6 / 54912.5, rel=REL)
