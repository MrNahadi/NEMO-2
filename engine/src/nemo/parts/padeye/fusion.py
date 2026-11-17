"""Padeye data exchanged with Fusion: the build request, edited-design checks and cross-check results."""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

from ...data import get_material, shackles
from .checks import check_padeye
from .geometry import PadeyeDesign
from .sizing import PadeyeJob
from .working import explain

# Fusion user parameter names. Kept short so they are easy to type in Fusion's Change Parameters dialog.
PARAMETERS = (
    ("nemo_t", "main_thickness_mm", "Main plate thickness"),
    ("nemo_R", "head_radius_mm", "Head radius"),
    ("nemo_Dh", "hole_diameter_mm", "Hole diameter"),
    ("nemo_L", "base_length_mm", "Base length"),
    ("nemo_h", "hole_height_mm", "Hole height above base"),
    ("nemo_tc", "cheek_thickness_mm", "Cheek plate thickness (0 = none)"),
    ("nemo_Rc", "cheek_radius_mm", "Cheek plate radius"),
    ("nemo_w", "weld_leg_mm", "Base fillet weld leg"),
    ("nemo_wc", "cheek_weld_leg_mm", "Cheek fillet weld leg"),
)


def load_entry(run_dir: Path, design_key: str) -> tuple[dict, dict]:
    results = json.loads((run_dir / "results.json").read_text(encoding="utf-8"))
    entry = next((d for d in results["designs"] if d["key"] == design_key), None)
    if entry is None:
        raise KeyError(design_key)
    return results, entry


def build_request(run_dir: Path, design_key: str, *, project_id: str, project_name: str, run_name: str,
                  sheet_url: str) -> dict:
    """Everything the connector needs to build the design as a parametric Fusion model."""
    results, entry = load_entry(run_dir, design_key)
    report = entry["check_report"]
    design = report["design"]
    material = results["material"]
    return {
        "project_id": project_id,
        "project_name": project_name,
        "run": run_name,
        "design_key": design_key,
        "design_label": entry["label"].split(" (")[0],
        "parameters": [
            {"name": name, "field": field, "label": label, "value_mm": float(design[field])}
            for name, field, label in PARAMETERS
        ],
        "material": {"id": material["id"], "name": material["name"], "density_kg_m3": material["density_kg_m3"]},
        "nemo_volume_mm3": entry["cad_volume_mm3"],
        "nemo_mass_kg": report["mass_kg"],
        "sling_angle_deg": results["job"]["lift"]["sling_angle_deg"],
        "sheet_url": sheet_url,
    }


def record_model(run_dir: Path, design_key: str, result: dict) -> dict:
    """Store what Fusion reported about the model it built, with the comparison against NEMO."""
    _, entry = load_entry(run_dir, design_key)
    nemo_volume = entry["cad_volume_mm3"]
    volume = float(result.get("volume_mm3") or 0.0)
    record = {
        **result,
        "nemo_volume_mm3": nemo_volume,
        "nemo_mass_kg": entry["check_report"]["mass_kg"],
        "volume_difference": (volume - nemo_volume) / nemo_volume if nemo_volume and volume else None,
        "recorded_at": _now(),
    }
    folder = run_dir / "designs" / design_key
    (folder / "fusion-model.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    (folder / "calculation-report.pdf").unlink(missing_ok=True)  # rebuilt with the Fusion model noted
    return record


def check_edited(run_dir: Path, design_key: str, values_mm: dict[str, float]) -> dict:
    """Re-run every check on a padeye whose dimensions were edited in Fusion."""
    results, entry = load_entry(run_dir, design_key)
    original = entry["check_report"]["design"]
    fields = {field: float(values_mm.get(name, original[field])) for name, field, _ in PARAMETERS}
    if fields["cheek_thickness_mm"] <= 0.05:
        fields.update(cheek_thickness_mm=0.0, cheek_radius_mm=0.0, cheek_weld_leg_mm=0.0)
    design = PadeyeDesign(**fields)
    problems = design.problems()
    if problems:
        return {"ok": False, "problems": problems, "design": design.to_dict()}
    job = PadeyeJob.from_dict(results["job"])
    shackle_info = entry["check_report"]["shackle"]
    shackle = next(s for s in shackles() if math.isclose(s.wll_t, shackle_info["wll_t"])
                   and math.isclose(s.pin_diameter_mm, shackle_info["pin_diameter_mm"]))
    report = explain(check_padeye(design, material=get_material(job.material_id), shackle=shackle, loads=job.loads,
                                  rule_set=job.rule_set, electrode_strength_mpa=job.electrode_strength_mpa))
    governing = report.governing
    changed = {f: (original[f], fields[f]) for f in fields if not math.isclose(float(original[f]), fields[f], abs_tol=1e-6)}
    summary = {
        "ok": True,
        "passed": report.passed,
        "mass_kg": report.mass_kg,
        "nemo_mass_kg": entry["check_report"]["mass_kg"],
        "governing": {"title": governing.title, "use": governing.utilization},
        "changed": {k: {"from": a, "to": b} for k, (a, b) in changed.items()},
        "checks": [
            {"id": c.id, "title": c.title, "use": c.utilization, "passed": c.passed, "severity": c.severity}
            for c in report.checks
        ],
        "design": design.to_dict(),
        "checked_at": _now(),
    }
    path = run_dir / "designs" / design_key / "fusion-checks.json"
    history = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    history.append(summary)
    path.write_text(json.dumps(history[-50:], indent=2), encoding="utf-8")
    return summary


def record_crosscheck(run_dir: Path, design_key: str, *, reaction_n: float | None, peak_stress_mpa: float | None,
                      max_displacement_mm: float | None, checked_by: str, notes: str = "") -> dict:
    """Store the Fusion Static Stress results typed in by the engineer, compared with NEMO's own FEA."""
    _, entry = load_entry(run_dir, design_key)
    fea = entry.get("fea") or {}
    finest = (fea.get("levels") or [{}])[-1]
    applied = finest.get("applied_force_n")
    nemo_reaction = math.sqrt(sum(v * v for v in applied)) if applied else None

    def diff(fusion: float | None, nemo: float | None) -> float | None:
        if fusion is None or not nemo:
            return None
        return (fusion - nemo) / nemo

    record = {
        "reaction_n": reaction_n,
        "peak_stress_mpa": peak_stress_mpa,
        "max_displacement_mm": max_displacement_mm,
        "checked_by": checked_by.strip(),
        "notes": notes.strip(),
        "nemo_reaction_n": nemo_reaction,
        "nemo_peak_stress_mpa": fea.get("head_von_mises_mpa"),
        "nemo_max_displacement_mm": finest.get("max_displacement_mm"),
        "reaction_difference": diff(reaction_n, nemo_reaction),
        "stress_difference": diff(peak_stress_mpa, fea.get("head_von_mises_mpa")),
        "displacement_difference": diff(max_displacement_mm, finest.get("max_displacement_mm")),
        "recorded_at": _now(),
    }
    record["agrees"] = all(
        d is None or abs(d) <= tol
        for d, tol in ((record["reaction_difference"], 0.02), (record["stress_difference"], 0.15))
    ) and record["stress_difference"] is not None
    folder = run_dir / "designs" / design_key
    (folder / "fusion-crosscheck.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    (folder / "calculation-report.pdf").unlink(missing_ok=True)  # rebuilt with the cross-check filled in
    return record


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
