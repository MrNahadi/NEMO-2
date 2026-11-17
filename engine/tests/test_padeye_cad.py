"""Padeye 3D model and cutting profile."""

from __future__ import annotations

import math
import random

import ezdxf
import pytest
from build123d import import_step

from nemo.parts.padeye import PadeyeDesign
from nemo.parts.padeye.cad import build_padeye
from nemo.parts.padeye.dxf import write_cutting_dxf

BASE = PadeyeDesign(20, 45, 21, 200, 90, 8)
WITH_CHEEKS = PadeyeDesign(12, 60, 36, 260, 120, 8, cheek_thickness_mm=6, cheek_radius_mm=50, cheek_weld_leg_mm=5)


def random_designs(count: int, seed: int = 42) -> list[PadeyeDesign]:
    rng = random.Random(seed)
    designs = []
    while len(designs) < count:
        hole = rng.uniform(12, 90)
        head = rng.uniform(hole / 2 + 10, hole / 2 + 120)
        t = rng.choice([8, 10, 12, 15, 20, 25, 30, 40])
        cheeks = rng.random() < 0.4
        d = PadeyeDesign(
            main_thickness_mm=t,
            head_radius_mm=head,
            hole_diameter_mm=hole,
            base_length_mm=rng.uniform(1.2 * head, 4.0 * head),
            hole_height_mm=rng.uniform(head, head + 200),
            weld_leg_mm=8,
            cheek_thickness_mm=rng.choice([5, 6, 8, 10]) if cheeks else 0.0,
            cheek_radius_mm=rng.uniform(hole / 2 + 8, head) if cheeks else 0.0,
            cheek_weld_leg_mm=5 if cheeks else 0.0,
        )
        if not d.problems():
            designs.append(d)
    return designs


@pytest.mark.parametrize("design", random_designs(50), ids=lambda d: f"t{d.main_thickness_mm:g}_R{d.head_radius_mm:.0f}")
def test_cad_volume_matches_formula(design):
    solid = build_padeye(design)
    assert solid.solid_count == 1
    assert solid.volume_mm3 == pytest.approx(design.volume_mm3(), rel=0.01)


def test_cad_dimensions():
    (x0, y0, z0), (x1, y1, z1) = build_padeye(WITH_CHEEKS).bounding_box_mm()
    assert (x0, x1) == pytest.approx((-130, 130), abs=1e-6)
    assert (y0, y1) == pytest.approx((-12, 12), abs=1e-6)
    assert (z0, z1) == pytest.approx((0, 180), abs=1e-6)


def test_step_round_trip(tmp_path):
    solid = build_padeye(WITH_CHEEKS)
    path = solid.export_step(tmp_path / "padeye.step")
    reimported = import_step(str(path))
    assert reimported.volume == pytest.approx(solid.volume_mm3, rel=0.005)


def test_stl_export(tmp_path):
    path = build_padeye(BASE).export_stl(tmp_path / "padeye.stl")
    assert path.stat().st_size > 1000


def test_dxf_profile_is_closed_and_full_size(tmp_path):
    path = write_cutting_dxf(WITH_CHEEKS, tmp_path / "padeye.dxf", material_name="S355", quantity=2)
    doc = ezdxf.readfile(path)
    assert doc.units == ezdxf.units.MM
    cut = [e for e in doc.modelspace() if e.dxf.layer == "CUT"]
    lines = [e for e in cut if e.dxftype() == "LINE"]
    arcs = [e for e in cut if e.dxftype() == "ARC"]
    circles = [e for e in cut if e.dxftype() == "CIRCLE"]
    assert (len(lines), len(arcs), len(circles)) == (3, 1, 5)  # outline, hole, 2 cheeks x 2 circles

    arc = arcs[0]
    ends = [
        (arc.dxf.center.x + arc.dxf.radius * math.cos(math.radians(a)),
         arc.dxf.center.y + arc.dxf.radius * math.sin(math.radians(a)))
        for a in (arc.dxf.start_angle, arc.dxf.end_angle)
    ]
    line_points = [(p.x, p.y) for e in lines for p in (e.dxf.start, e.dxf.end)]
    for end in ends:
        assert any(math.dist(end, p) < 1e-6 for p in line_points)
    assert arc.dxf.radius == pytest.approx(60)
    hole = min(circles, key=lambda c: (c.dxf.center.x, c.dxf.radius))
    assert hole.dxf.radius == pytest.approx(18)
