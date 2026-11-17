"""Padeye sizing: buildable, code-checked designs from a job description."""

from __future__ import annotations

import time

import pytest

from nemo.loads import LiftScenario
from nemo.parts.padeye.sizing import (
    MAX_BASE_WELD_FRACTION,
    WELD_SIZES_MM,
    NoFeasibleDesign,
    PadeyeJob,
    shortlist_padeyes,
    size_padeye,
)

JOB = PadeyeJob(LiftScenario(lifted_mass_kg=20000, lift_points=4, sling_angle_deg=60))


@pytest.fixture(scope="module")
def shortlist():
    designs, stats = shortlist_padeyes(JOB)
    return designs


def test_every_shortlisted_design_passes(shortlist):
    assert len(shortlist) >= 2
    for item in shortlist:
        assert item.report.passed
        assert item.report.governing.utilization <= item.target_utilization + 1e-9


def test_more_margin_costs_more_steel(shortlist):
    masses = [s.mass_kg for s in shortlist]
    assert masses == sorted(masses)
    caps = [s.report.governing.utilization for s in shortlist]
    assert caps[0] >= caps[-1]


def test_designs_use_stock_and_buildable_sizes(shortlist):
    for item in shortlist:
        d = item.design
        assert d.main_thickness_mm in JOB.plate_thicknesses_mm
        assert d.cheek_thickness_mm == 0 or d.cheek_thickness_mm in JOB.plate_thicknesses_mm
        assert d.head_radius_mm == int(d.head_radius_mm)
        assert d.base_length_mm % 5 == 0
        assert d.weld_leg_mm in WELD_SIZES_MM
        assert d.weld_leg_mm <= MAX_BASE_WELD_FRACTION * d.main_thickness_mm
        assert d.hole_diameter_mm > item.report.shackle.pin_diameter_mm


def test_shackle_covers_sling_force(shortlist):
    for item in shortlist:
        assert item.report.shackle.wll_t >= JOB.loads.sling_force_t


def test_quick_sizing_is_fast_enough_for_live_preview():
    start = time.perf_counter()
    report = size_padeye(JOB, quick=True)
    assert time.perf_counter() - start < 1.0
    assert report.passed


def test_heavier_lift_needs_heavier_padeye():
    light = size_padeye(PadeyeJob(LiftScenario(5000, 2, 60)), quick=True)
    heavy = size_padeye(PadeyeJob(LiftScenario(30000, 2, 60)), quick=True)
    assert heavy.mass_kg > light.mass_kg
    assert heavy.shackle.wll_t > light.shackle.wll_t


def test_only_thin_plate_without_cheeks_is_explained():
    job = PadeyeJob(LiftScenario(20000, 4, 60), plate_thicknesses_mm=(6,), allow_cheek_plates=False)
    with pytest.raises(NoFeasibleDesign, match="too thin"):
        size_padeye(job)


def test_load_beyond_largest_shackle_is_explained():
    with pytest.raises(NoFeasibleDesign, match="largest shackle"):
        size_padeye(PadeyeJob(LiftScenario(400_000, 2, 60)))


def test_job_round_trips_through_dict():
    job = PadeyeJob(LiftScenario(1234, 3, 55, dynamic_factor=1.2, points_carrying=2), material_id="AH36",
                    plate_thicknesses_mm=(8, 10, 12), allow_cheek_plates=False, design_category="A")
    assert PadeyeJob.from_dict(job.to_dict()) == job
