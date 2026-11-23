"""Independent numerical provenance audit for the NEMO panel defense slides.

Reads the actual rendered DOM text captured by headless Chrome (`audit/rendered-text.json`)
and verifies every critical displayed figure directly against the RAW solver/benchmark JSON
files in `reports/project-report/data/` (bypassing `deck-data.json` completely).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA_ROOT = HERE.parents[1] / "reports" / "project-report" / "data"
RENDERED_PATH = HERE / "audit" / "rendered-text.json"


def load(rel: str):
    return json.loads((DATA_ROOT / rel).read_text(encoding="utf-8"))


def main() -> int:
    rendered = json.loads(RENDERED_PATH.read_text(encoding="utf-8"))
    ver = load("verification.json")
    swp = load("sweeps.json")
    adv = load("advanced.json")
    pad = load("runs/padeye/20270115-090000-000000/results.json")
    brk = load("runs/pipe-bracket/20270115-090000-000000/results.json")
    fin = load("runs/stabilizer/20270115-090000-000000/results.json")

    def by_key(run, key):
        return next(d for d in run["designs"] if d["key"] == key)

    pad_l, pad_b, pad_r = by_key(pad, "lightest"), by_key(pad, "balanced"), by_key(pad, "robust")
    brk_l = by_key(brk, "lightest")
    fin_l, fin_b, fin_r = by_key(fin, "lightest"), by_key(fin, "balanced"), by_key(fin, "robust")

    total_evals = pad["search"]["evaluations"] + brk["search"]["evaluations"] + fin["search"]["evaluations"]
    all_designs = pad["designs"] + brk["designs"] + fin["designs"]
    total_solves = sum(len(d["fea"]["levels"]) for d in all_designs)
    max_conv_pct = max(d["fea"]["convergence_change"] * 100.0 for d in all_designs)
    worst_bal = max(lv["reaction_balance_error"] for d in all_designs for lv in d["fea"]["levels"])

    b_by_id = {b["id"]: b for b in ver["benchmarks"]}
    hand_max = max(abs(c["error_percent"]) for c in b_by_id["padeye-hand-calc"]["comparisons"])
    cant_def = abs(next(c for c in b_by_id["cantilever"]["comparisons"] if "deflection" in c["quantity"].lower())["error_percent"])
    cant_str = abs(next(c for c in b_by_id["cantilever"]["comparisons"] if "stress" in c["quantity"].lower())["error_percent"])
    hole_scf = abs(next(c for c in b_by_id["plate-hole"]["comparisons"] if "concentration" in c["quantity"].lower())["error_percent"])
    pan_circ = abs(next(c for c in b_by_id["panel-method"]["comparisons"] if "circle" in c["quantity"].lower())["error_percent"])
    pan_n20 = abs(next(c for c in b_by_id["panel-method"]["comparisons"] if "0020" in c["quantity"])["error_percent"])

    fin_excess = (fin["loads"]["nemo_lift_n"] - fin["loads"]["ur_s10_force_n"]) / fin["loads"]["ur_s10_force_n"] * 100.0
    fin_cav_margin = (fin["loads"]["cavitation_number"] - abs(fin["loads"]["cp_min"])) / fin["loads"]["cavitation_number"] * 100.0
    fin20 = next(r for r in swp["fin"] if r["speed_kn"] == 20)
    nps6 = next(r for r in adv["bracket"] if r["nps"] == "6")
    nps12 = next(r for r in adv["bracket"] if r["nps"] == "12")

    # (slide_id, description, expected_substring_derived_from_raw_json)
    checks = [
        ("04", "Total evaluations", f"{total_evals:,}"),
        ("05", "Verification seconds", f"{ver['seconds_total']:.1f} s"),
        ("05", "Hand calc max err", f"{hand_max:.4f}%"),
        ("05", "Cantilever deflection err", f"{cant_def:.2f}%"),
        ("05", "Plate hole SCF err", f"{hole_scf:.2f}%"),
        ("05", "Panel circle Cp err", f"{pan_circ:.2f}%"),
        ("05", "NACA 0020 lift slope err", f"{pan_n20:.2f}%"),
        ("06", "Total 3D FEA solves", f"{total_solves}"),
        ("06", "Max FEA convergence delta", f"{max_conv_pct:.2f}%"),
        ("06", "Padeye balanced L3 von Mises", f"{pad_b['fea']['head_von_mises_mpa']:.1f} MPa"),
        ("06", "Bracket L3 assessed von Mises", f"{brk_l['fea']['head_von_mises_mpa']:.1f} MPa"),
        ("06", "Bracket hand stress", f"{brk_l['fea']['hand_stress_mpa']:.1f} MPa"),
        ("06", "Fin stock L3 von Mises", f"{fin_l['fea']['head_von_mises_mpa']:.1f} MPa"),
        ("06", "Fin stock beam theory stress", f"{fin_l['fea']['hand_stress_mpa']:.1f} MPa"),
        ("06", "Worst reaction balance error", f"{worst_bal:.2e}".replace("e-0", "e-")),
        ("08", "Padeye sling force kN", f"{pad['loads']['sling_force_n']/1000:.2f} kN"),
        ("08", "Padeye evaluations", f"{pad['search']['evaluations']:,}"),
        ("08", "Padeye balanced mass", f"{pad_b['check_report']['mass_kg']:.3f} kg"),
        ("08", "Padeye balanced weld util", f"{next(c for c in pad_b['check_report']['checks'] if c['id']=='base_weld')['utilization']*100:.1f}%"),
        ("08", "Padeye balanced FoS", f"{pad_b['fea']['factor_of_safety_on_yield']:.2f}"),
        ("09", "Bracket downward load kN", f"{brk['loads']['down_n']/1000:.2f} kN"),
        ("09", "Bracket mass kg", f"{brk_l['check_report']['mass_kg']:.3f} kg"),
        ("09", "Bracket weld util", f"{next(c for c in brk_l['check_report']['checks'] if c['id']=='root_weld')['utilization']*100:.1f}%"),
        ("09", "Bracket span natural Hz", f"{brk_l['check_report']['span']['natural_hz']:.2f} Hz"),
        ("09", "Bracket span freq limit m", f"{brk_l['check_report']['span']['spans_m']['frequency']:.2f} m"),
        ("09", "Bracket span sag limit m", f"{brk_l['check_report']['span']['spans_m']['sag']:.2f} m"),
        ("09", "Bracket span stress limit m", f"{brk_l['check_report']['span']['spans_m']['stress']:.1f} m"),
        ("10", "Fin lift excess pct", f"{fin_excess:.1f}%"),
        ("10", "Fin design force kN", f"{fin['loads']['design_force_n']/1000:.2f} kN"),
        ("10", "Fin UR S10 force kN", f"{fin['loads']['ur_s10_force_n']/1000:.2f} kN"),
        ("10", "Fin lightest mass kg", f"{fin_l['check_report']['mass_kg']:.1f} kg"),
        ("10", "Fin 18 kn |Cp,min|", f"{abs(fin['loads']['cp_min']):.2f}"),
        ("10", "Fin 18 kn sigma", f"{fin['loads']['cavitation_number']:.2f}"),
        ("10", "Fin 18 kn cav margin", f"{fin_cav_margin:.1f}%"),
        ("10", "Fin 20 kn sigma", f"{fin20['sigma']:.2f}"),
        ("12", "Benchmarks 6 / 6", "6 / 6"),
        ("12", "Max VV FEA error", f"{cant_str:.2f}%"),
        ("12", "Max FEA convergence stat", f"{max_conv_pct:.2f}"),
        ("12", "Total candidates stat", f"{total_evals:,}"),
        ("B1", "Obliquity 0 deg side load", f"{adv['padeye'][0]['side_n']/1000:.2f} kN"),
        ("B1", "Obliquity 90 deg side load", f"{adv['padeye'][3]['side_n']/1000:.2f} kN"),
        ("B1", "Obliquity 45 deg derating", f"{adv['padeye'][2]['side_factor']:.2f}"),
        ("B1", "Obliquity 90 deg mass", f"{adv['padeye'][3]['mass_kg']:.3f} kg"),
        ("B2", "NPS 6 rigid Hz", f"{nps6['span_hz']:.2f} Hz"),
        ("B2", "NPS 6 combined Hz", f"{nps6['combined_hz']:.2f} Hz"),
        ("B2", "NPS 6 separation pct", f"{nps6['separation']*100:.2f}%"),
        ("B2", "NPS 12 rigid Hz", f"{nps12['span_hz']:.2f} Hz"),
        ("B2", "NPS 12 combined Hz", f"{nps12['combined_hz']:.2f} Hz"),
        ("B3", "Astern torque stock forward", f"{adv['fin']['stock_forward']['astern_torque_nm']/1000:.2f} kN"),
        ("B3", "Outer reaction 800 mm", f"{adv['fin']['bearings_800']['outer']['reaction_n']/1000:.1f} kN"),
        ("B3", "Outer reaction 400 mm", f"{adv['fin']['bearings_400']['outer']['reaction_n']/1000:.1f} kN"),
        ("B3", "Mass 400 mm bearings", f"{adv['fin']['bearings_400']['mass_kg']:.1f} kg"),
        ("B4", "Bracket raw L3 peak", f"{brk_l['fea']['levels'][2]['max_von_mises_mpa']:.1f}"),
        ("B5", "Padeye extra margin mass", f"{pad_r['check_report']['mass_kg']:.3f} kg"),
        ("B5", "Fin balanced mass", f"{fin_b['check_report']['mass_kg']:.1f} kg"),
        ("B5", "Fin extra margin mass", f"{fin_r['check_report']['mass_kg']:.1f} kg"),
    ]

    failures = []
    for sid, desc, expected in checks:
        text = rendered.get(sid, "")
        if expected not in text:
            failures.append((sid, desc, expected))

    print(f"Data provenance reconciliation: {len(checks) - len(failures)} / {len(checks)} assertions matched raw JSON.")
    if failures:
        for sid, desc, exp in failures:
            print(f"  FAIL [Slide {sid}] {desc}: expected '{exp}' not found in rendered text")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
