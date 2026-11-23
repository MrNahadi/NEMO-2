"""Programmatically extract all presentation metrics from raw NEMO run artifacts.

Reads ONLY raw solver/verification JSON and CSV outputs under
`reports/project-report/data/` and writes `deck-data.json` with explicit source
provenance paths. Zero hand-transcribed numbers from prose summaries.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = REPO_ROOT / "reports" / "project-report" / "data"
OUT_JS_PATH = Path(__file__).resolve().parent / "deck-data-inline.js"


def load_json(rel: str) -> dict | list:
    return json.loads((DATA_ROOT / rel).read_text(encoding="utf-8"))


def count_csv_rows(rel: str) -> int:
    with (DATA_ROOT / rel).open("r", encoding="utf-8", newline="") as f:
        return sum(1 for _ in csv.DictReader(f))


def summarize_part(part: str, run_rel: str) -> dict:
    r = load_json(f"{run_rel}/results.json")
    csv_rows = count_csv_rows(f"{run_rel}/designs-evaluated.csv")

    designs = {}
    for d in r["designs"]:
        cr = d["check_report"]
        fea = d["fea"]
        checks_by_id = {c["id"]: c for c in cr["checks"]}
        levels = fea["levels"]
        max_bal_err = max(lv["reaction_balance_error"] for lv in levels)
        designs[d["key"]] = {
            "label": d["label"],
            "target_utilization": d["target_utilization"],
            "mass_kg": cr["mass_kg"],
            "governing_id": cr["governing"],
            "governing_title": checks_by_id[cr["governing"]]["title"],
            "governing_utilization": checks_by_id[cr["governing"]]["utilization"],
            "governing_source": checks_by_id[cr["governing"]]["source"],
            "passed": cr["passed"],
            "design": cr["design"],
            "shackle": cr.get("shackle"),
            "span": cr.get("span"),
            "checks": [
                {
                    "id": c["id"],
                    "title": c["title"],
                    "demand": c["demand"],
                    "capacity": c["capacity"],
                    "unit": c["unit"],
                    "utilization": c["utilization"],
                    "passed": c["passed"],
                    "severity": c["severity"],
                    "source": c["source"],
                }
                for c in cr["checks"]
            ],
            "fea": {
                "model": fea.get("model"),
                "region": fea.get("region"),
                "head_von_mises_mpa": fea["head_von_mises_mpa"],
                "yield_strength_mpa": fea["yield_strength_mpa"],
                "factor_of_safety_on_yield": fea["factor_of_safety_on_yield"],
                "convergence_change": fea["convergence_change"],
                "convergence_change_pct": fea["convergence_change"] * 100.0,
                "converged": fea["converged"],
                "hand_stress_mpa": fea.get("hand_stress_mpa"),
                "hand_label": fea.get("hand_label"),
                "max_reaction_balance_error": max_bal_err,
                "levels": [
                    {
                        "level": lv["level"],
                        "elements": lv["elements"],
                        "dofs": lv["dofs"],
                        "head_von_mises_mpa": lv["head_von_mises_mpa"],
                        "max_von_mises_mpa": lv["max_von_mises_mpa"],
                        "max_displacement_mm": lv["max_displacement_mm"],
                        "reaction_balance_error": lv["reaction_balance_error"],
                        "solve_seconds": lv["solve_seconds"],
                    }
                    for lv in levels
                ],
            },
        }

    return {
        "source_path": f"reports/project-report/data/{run_rel}/results.json",
        "csv_path": f"reports/project-report/data/{run_rel}/designs-evaluated.csv",
        "csv_rows": csv_rows,
        "seconds": r["seconds"],
        "rule_set": r["rule_set"],
        "job": r["job"],
        "loads": r["loads"],
        "material": r["material"],
        "stock_material": r.get("stock_material"),
        "search": {
            "combinations": r["search"]["combinations"],
            "evaluations": r["search"]["evaluations"],
            "skipped": r["search"]["skipped"],
        },
        "designs": designs,
    }


def main() -> None:
    cases = load_json("cases.json")
    verification = load_json("verification.json")
    sweeps = load_json("sweeps.json")
    advanced = load_json("advanced.json")

    runs = {}
    for part, info in cases.items():
        run_rel = info["run_dir"].replace("\\", "/")
        runs[part] = summarize_part(part, run_rel)

    # Aggregate verified metrics across all 3 runs & 6 benchmarks
    total_evaluations = sum(runs[p]["search"]["evaluations"] for p in runs)
    all_designs = [d for p in runs for d in runs[p]["designs"].values()]
    total_fea_designs = len(all_designs)
    total_fea_solves = sum(len(d["fea"]["levels"]) for d in all_designs)
    max_conv_pct = max(d["fea"]["convergence_change_pct"] for d in all_designs)
    worst_bal_err = max(d["fea"]["max_reaction_balance_error"] for d in all_designs)
    all_converged = all(d["fea"]["converged"] for d in all_designs)

    # Verification benchmark summary
    vv_benchmarks = []
    max_vv_fea_err = 0.0
    max_vv_hand_err = 0.0
    max_vv_cad_err = 0.0
    for b in verification["benchmarks"]:
        comps = b["comparisons"]
        max_abs_err = max(abs(c["error_percent"]) for c in comps)
        if b["id"] in ("cantilever", "plate-hole", "stock-beam"):
            max_vv_fea_err = max(max_vv_fea_err, max_abs_err)
        elif b["id"] == "padeye-hand-calc":
            max_vv_hand_err = max(max_vv_hand_err, max_abs_err)
        elif b["id"] == "cad-volume":
            max_vv_cad_err = max(max_vv_cad_err, max_abs_err)
        vv_benchmarks.append(
            {
                "id": b["id"],
                "title": b["title"],
                "source": b["source"],
                "passed": b["passed"],
                "seconds": b["seconds"],
                "mesh": b.get("mesh"),
                "comparisons": comps,
            }
        )

    # Fin lift ratio (Whicker-Fehlner vs IACS UR S10)
    fin_loads = runs["stabilizer"]["loads"]
    fin_lift_excess_pct = (
        (fin_loads["nemo_lift_n"] - fin_loads["ur_s10_force_n"])
        / fin_loads["ur_s10_force_n"]
        * 100.0
    )
    cav_margin_pct = (
        (fin_loads["cavitation_number"] - abs(fin_loads["cp_min"]))
        / fin_loads["cavitation_number"]
        * 100.0
    )

    out = {
        "provenance": {
            "cases": "reports/project-report/data/cases.json",
            "verification": "reports/project-report/data/verification.json",
            "sweeps": "reports/project-report/data/sweeps.json",
            "advanced": "reports/project-report/data/advanced.json",
            "runs": {p: runs[p]["source_path"] for p in runs},
        },
        "summary": {
            "benchmarks_passed": sum(1 for b in vv_benchmarks if b["passed"]),
            "benchmarks_total": len(vv_benchmarks),
            "verification_seconds": verification["seconds_total"],
            "max_vv_fea_error_pct": max_vv_fea_err,
            "max_vv_hand_error_pct": max_vv_hand_err,
            "max_vv_cad_error_pct": max_vv_cad_err,
            "total_evaluations": total_evaluations,
            "total_fea_designs": total_fea_designs,
            "total_fea_solves": total_fea_solves,
            "all_fea_converged": all_converged,
            "max_fea_convergence_change_pct": max_conv_pct,
            "worst_reaction_balance_error": worst_bal_err,
            "fin_lift_excess_over_urs10_pct": fin_lift_excess_pct,
            "fin_18kn_cavitation_margin_pct": cav_margin_pct,
        },
        "verification": {
            "nemo_version": verification["nemo_version"],
            "passed": verification["passed"],
            "seconds_total": verification["seconds_total"],
            "benchmarks": vv_benchmarks,
        },
        "runs": runs,
        "sweeps": sweeps,
        "advanced": advanced,
    }

    OUT_JS_PATH.write_text(
        "window.NEMO_DATA = " + json.dumps(out, indent=2) + ";\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUT_JS_PATH}")
    print(json.dumps(out["summary"], indent=2))


if __name__ == "__main__":
    main()
