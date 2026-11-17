"""Showing the working: calculation steps, engineering events, verification and the PDF report."""

from __future__ import annotations

import json

import pytest

from nemo.data import get_material, smallest_shackle_for
from nemo.loads import LiftScenario, padeye_loads
from nemo.parts.padeye import PadeyeDesign, check_padeye
from nemo.parts.padeye.pipeline import run_padeye_job
from nemo.parts.padeye.sizing import PadeyeJob
from nemo.parts.padeye.working import explain, load_steps
from nemo.report_pdf import build_report_pdf, markup
from nemo.rules import ASMEBTH1
from nemo.verification import cad_volume, padeye_hand_calculation

LOADS = padeye_loads(LiftScenario(4000, 2, 60))


def report(design):
    return explain(check_padeye(design, material=get_material("S355"), shackle=smallest_shackle_for(LOADS.sling_force_t),
                                loads=LOADS, rule_set=ASMEBTH1()))


@pytest.mark.parametrize("design", [
    PadeyeDesign(20, 45, 21, 200, 90, 8),
    PadeyeDesign(12, 45, 21, 200, 90, 8, cheek_thickness_mm=5, cheek_radius_mm=40, cheek_weld_leg_mm=5),
])
def test_every_check_shows_its_working(design):
    r = report(design)
    for c in r.checks:
        assert c.working, c.id


def test_working_results_match_the_check_values():
    r = report(PadeyeDesign(20, 45, 21, 200, 90, 8))
    for check_id in ("head_tension", "head_fracture", "head_shear_out", "head_bearing"):
        c = r.check(check_id)
        allowed = next(s for s in c.working if s.label == "Allowed load")
        assert allowed.value * 1000 == pytest.approx(c.capacity)
        assert c.working[-1].value * 1000 == pytest.approx(c.demand)
    for check_id in ("base_combined", "base_shear", "base_weld"):
        c = r.check(check_id)
        assert any(s.value == pytest.approx(c.demand) for s in c.working)


def test_load_steps_follow_the_hand_calculation():
    steps = load_steps(LiftScenario(4000, 2, 60), LOADS)
    assert [s.symbol for s in steps] == ["W", "V", "F", "H", "Q"]
    assert steps[2].value == pytest.approx(22.6476, rel=1e-4)
    assert "sin 60.0°" in steps[2].substituted


def test_formula_markup():
    assert markup("P_t = C_r F_u") == "P<sub>t</sub> = C<sub>r</sub> F<sub>u</sub>"
    assert markup("b_{eff} ≤ 4t^2") == "b<sub>eff</sub> ≤ 4t<super>2</super>"


def test_fast_benchmarks_pass():
    for bench in (padeye_hand_calculation(), cad_volume()):
        assert bench["comparisons"]
        assert all(c["passed"] for c in bench["comparisons"])


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    run_dir = tmp_path_factory.mktemp("run")
    run_padeye_job(PadeyeJob(LiftScenario(3000, 2, 60)), run_dir, project_name="Test", fea_levels=(1.0,))
    return run_dir


def test_run_writes_an_ordered_engineering_log(run):
    events = json.loads((run / "engineering-log.json").read_text(encoding="utf-8"))
    kinds = [e["kind"] for e in events]
    assert kinds[0] == "start" and kinds[-1] == "done"
    assert kinds.index("loads") < kinds.index("shackles") < kinds.index("design_found") < kinds.index("cad") < kinds.index("solve")
    times = [e["t"] for e in events]
    assert times == sorted(times)
    solve = next(e for e in events if e["kind"] == "solve")
    assert solve["balance_error"] < 1e-6
    mesh = next(e for e in events if e["kind"] == "mesh")
    assert len(mesh["surface"]["positions"]) % 3 == 0


def test_run_lists_every_design_tried(run):
    lines = (run / "designs-evaluated.csv").read_text(encoding="utf-8").splitlines()
    results = json.loads((run / "results.json").read_text(encoding="utf-8"))
    assert len(lines) > 1000
    assert len(lines) - 1 <= results["search"]["evaluations"]


def test_pdf_report_builds(run):
    pdf = build_report_pdf(run, "lightest", project_name="Test", run_name="20261116-120000-000000", target=run / "r.pdf")
    data = pdf.read_bytes()
    assert data.startswith(b"%PDF")
    assert data.count(b"/Type /Page") >= 10
