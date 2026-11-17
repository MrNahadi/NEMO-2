"""Data for the advanced-settings section of the project report (no FEA, so it runs in about a minute).

Run from engine/:  .venv\\Scripts\\python.exe ..\\reports\\project-report\\tools\\make_advanced_data.py
Writes data/advanced.json.
"""

from __future__ import annotations

import json
from pathlib import Path

from nemo.loads import LiftScenario
from nemo.parts.bracket.checks import check_bracket
from nemo.parts.bracket.job import BracketJob, span_analysis
from nemo.parts.bracket.sizing import size_bracket
from nemo.parts.padeye.sizing import PadeyeJob, size_padeye
from nemo.parts.stabilizer.job import FinJob
from nemo.parts.stabilizer.sizing import size_fin

DATA = Path(__file__).resolve().parent.parent / "data"


def padeye() -> list[dict]:
    out = []
    for beta in (0.0, 20.0, 45.0, 90.0):
        job = PadeyeJob(LiftScenario(5000, 2, 60.0, out_of_plane_angle_deg=beta))
        loads = job.loads
        report = size_padeye(job)
        rating = report.check("shackle_rating")
        gov = report.governing
        out.append({
            "beta_deg": beta, "side_angle_deg": loads.side_angle_deg, "horizontal_n": loads.horizontal_n,
            "side_n": loads.side_n, "shackle": report.shackle.label, "shackle_wll_t": report.shackle.wll_t,
            "side_factor": rating.details["side_load_factor"], "rated_t": rating.capacity, "shackle_use": rating.utilization,
            "main_plate_mm": report.design.main_thickness_mm, "cheek_mm": report.design.cheek_thickness_mm,
            "mass_kg": report.mass_kg, "governing": gov.title, "governing_use": gov.utilization,
        })
        print("padeye", beta, out[-1]["shackle"], round(out[-1]["mass_kg"], 3), out[-1]["governing"])
    return out


def bracket() -> list[dict]:
    out = []
    for nps in ("2", "3", "4", "6", "8", "10", "12"):
        job = BracketJob(pipe_nps=nps)
        span = span_analysis(job, job.loads)
        report = check_bracket(size_bracket(job).design, job, job.loads, span)
        c = report.check("support_vibration")
        out.append({"nps": nps, "span_hz": span.natural_hz, "bracket_hz": c.details["bracket_hz"],
                    "combined_hz": c.details["combined_hz"], "separation": c.capacity, "use": c.utilization,
                    "passed": c.passed, "category": c.category, "mass_kg": report.mass_kg,
                    "rigid_separation": span.separation})
        print("bracket", nps, round(c.details["combined_hz"], 2), c.passed)
    return out


def fin() -> dict:
    cases = {}
    for key, job in (("default", FinJob()),
                     ("stock_forward", FinJob(stock_position=0.20, front_spar=0.10, speed_kn=12.0, astern_speed_kn=12.0)),
                     ("bearings_800", FinJob(check_bearings=True, bearing_spacing_mm=800.0)),
                     ("bearings_400", FinJob(check_bearings=True, bearing_spacing_mm=400.0))):
        loads = job.loads
        report = size_fin(job)
        row = {"astern_speed_kn": loads.astern_speed_kn, "astern_force_n": loads.astern_force_n,
               "astern_torque_nm": loads.astern_torque_nm, "astern_moment_nm": loads.astern_stock_moment_nm,
               "ahead_torque_nm": loads.torque_nm, "stock_mm": report.design.stock_diameter_mm, "mass_kg": report.mass_kg,
               "torsion_condition": report.check("stock_torsion").details["condition"],
               "torsion_use": report.check("stock_torsion").utilization,
               "combined_condition": report.check("stock_combined").details["condition"],
               "combined_use": report.check("stock_combined").utilization}
        if job.check_bearings:
            for side in ("outer", "inner"):
                c = report.check(f"{side}_bearing")
                row[side] = {"reaction_n": c.details["reaction_n"], "diameter_mm": c.details["diameter_mm"],
                             "length_mm": c.demand, "longest_mm": c.capacity, "use": c.utilization,
                             "clearance_mm": c.details["clearance_mm"]}
        cases[key] = row
        print("fin", key, row["stock_mm"], round(row["mass_kg"], 1), row["torsion_condition"])
    return cases


def main() -> None:
    data = {"padeye": padeye(), "bracket": bracket(), "fin": fin()}
    (DATA / "advanced.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    print("wrote", DATA / "advanced.json")


if __name__ == "__main__":
    main()
