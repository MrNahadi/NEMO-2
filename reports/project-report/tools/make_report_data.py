"""Run the three case studies, the verification suite and the parameter sweeps for the project report.

Writes into reports/project-report/data/:
    runs/<part>/           full run folders (results.json, engineering log, STEP, DXF, PDF report)
    verification.json      the Verification page benchmarks
    sweeps.json            parameter sweeps used for the trend figures
    facts.json             every number quoted in the report, collected in one place

Run from the engine folder:  .venv\\Scripts\\python.exe ..\\reports\\project-report\\tools\\make_report_data.py
"""

from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "data"

from nemo import verification  # noqa: E402
from nemo.parts.bracket.job import BracketJob  # noqa: E402
from nemo.parts.bracket.pipeline import run_bracket_job  # noqa: E402
from nemo.parts.bracket.sizing import size_bracket  # noqa: E402
from nemo.parts.padeye.pipeline import run_padeye_job  # noqa: E402
from nemo.parts.padeye.sizing import NoFeasibleDesign, PadeyeJob, size_padeye  # noqa: E402
from nemo.parts.stabilizer.job import FinJob  # noqa: E402
from nemo.parts.stabilizer.pipeline import run_fin_job  # noqa: E402
from nemo.parts.stabilizer.sizing import size_fin  # noqa: E402
from nemo.report_pdf import build_report_pdf  # noqa: E402

CASES = {
    "padeye": ("Engine room lift", PadeyeJob.from_dict({"lift": {"lifted_mass_kg": 5000, "lift_points": 2, "sling_angle_deg": 60}}),
               run_padeye_job),
    "pipe-bracket": ("Engine room seawater line", BracketJob(), run_bracket_job),
    "stabilizer": ("Patrol boat stabilizer", FinJob(), run_fin_job),
}


def run_cases() -> dict:
    out = {}
    for part, (name, job, runner) in CASES.items():
        run_dir = OUT / "runs" / part / "20270115-090000-000000"
        shutil.rmtree(run_dir.parent, ignore_errors=True)
        t = time.perf_counter()
        summary = runner(job, run_dir, project_name=name)
        seconds = time.perf_counter() - t
        for d in summary["designs"]:
            build_report_pdf(run_dir, d["key"], project_name=name, run_name=run_dir.name,
                             target=run_dir / "designs" / d["key"] / "calculation-report.pdf")
        out[part] = {"name": name, "seconds": seconds, "run_dir": str(run_dir.relative_to(OUT))}
        print(part, f"{seconds:.1f} s", [d["key"] for d in summary["designs"]], flush=True)
    return out


def sweeps() -> dict:
    res: dict = {"padeye": [], "bracket": [], "fin": []}
    for angle in (45, 60, 90):
        for t in (1, 2, 5, 10, 20, 30, 40):
            job = PadeyeJob.from_dict({"lift": {"lifted_mass_kg": t * 1000, "lift_points": 2, "sling_angle_deg": angle}})
            try:
                r = size_padeye(job)
                res["padeye"].append({"angle": angle, "load_t": t, "mass_kg": r.mass_kg, "sling_t": job.loads.sling_force_t,
                                      "shackle_t": r.shackle.wll_t, "governing": r.governing.title,
                                      "use": r.governing.utilization, "plate_mm": r.design.main_thickness_mm,
                                      "cheeks": r.design.has_cheeks})
            except NoFeasibleDesign as exc:
                res["padeye"].append({"angle": angle, "load_t": t, "mass_kg": None, "reason": str(exc)})
    for nps in ("2", "3", "4", "6", "8", "10", "12"):
        job = BracketJob(pipe_nps=nps)
        loads = job.loads
        from nemo.parts.bracket.job import span_analysis

        span = span_analysis(job, loads)
        try:
            r = size_bracket(job)
            mass, gov, use = r.mass_kg, r.governing.title, r.governing.utilization
        except NoFeasibleDesign:
            mass, gov, use = None, None, None
        res["bracket"].append({"nps": nps, "od_mm": job.pipe.od_mm, "down_kn": loads.down_n / 1000, "mass_kg": mass,
                               "governing": gov, "use": use, "natural_hz": span.natural_hz,
                               "recommended_m": span.recommended_m, "spans_m": span.spans_m})
    for span_m in (1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0):
        job = BracketJob(span_m=span_m)
        from nemo.parts.bracket.job import span_analysis

        s = span_analysis(job, job.loads)
        res.setdefault("bracket_span", []).append({"span_m": span_m, "natural_hz": s.natural_hz, "separation": s.separation,
                                                   "nearest": s.nearest[0], "pipe_stress_mpa": s.pipe_stress_mpa})
    for speed in (10, 12, 14, 16, 18, 20, 22, 24):
        job = FinJob(speed_kn=speed)
        L = job.loads
        try:
            r = size_fin(job)
            mass, stock, gov = r.mass_kg, r.design.stock_diameter_mm, r.governing.title
        except NoFeasibleDesign:
            mass, stock, gov = None, None, None
        res["fin"].append({"speed_kn": speed, "nemo_lift_kn": L.nemo_lift_n / 1000, "ur_s10_kn": L.ur_s10_force_n / 1000,
                           "design_kn": L.design_force_n / 1000, "torque_knm": L.torque_nm / 1000, "cp_min": L.cp_min,
                           "sigma": L.cavitation_number, "mass_kg": mass, "stock_mm": stock, "governing": gov})
    return res


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    what = set(sys.argv[1:]) or {"cases", "verification", "sweeps"}
    if "verification" in what:
        t = time.perf_counter()
        v = verification.run_all()
        v["seconds_total"] = time.perf_counter() - t
        (OUT / "verification.json").write_text(json.dumps(v, indent=2), encoding="utf-8")
        print("verification", v["passed"], f"{v['seconds_total']:.1f} s", flush=True)
    if "sweeps" in what:
        (OUT / "sweeps.json").write_text(json.dumps(sweeps(), indent=2), encoding="utf-8")
        print("sweeps done", flush=True)
    if "cases" in what:
        (OUT / "cases.json").write_text(json.dumps(run_cases(), indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
