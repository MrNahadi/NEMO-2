"""Full pipe support bracket run: span analysis, shortlist, 3D models, cutting files and FEA.

Writes the same run folder layout as the padeye (results.json, the
engineering log, every design tried, and designs/<key>/ files).
"""

from __future__ import annotations

import csv
import json
import platform
import time
from datetime import datetime, timezone
from pathlib import Path

from ... import __version__
from ...fea_study import MESH_LEVELS
from ...runlog import EngineeringLog, stress_surface
from .cad import build_bracket, write_cutting_dxf
from .fea import analyse_bracket
from .job import BracketJob, load_steps
from .sizing import EVALUATED_COLUMNS, shortlist_brackets


def run_bracket_job(job: BracketJob, run_dir: Path, *, project_name: str = "", progress=None,
                    fea_levels: tuple[float, ...] = MESH_LEVELS, run_fea: bool = True,
                    log: EngineeringLog | None = None) -> dict:
    started = time.perf_counter()
    report_progress = progress or (lambda message, fraction: None)
    log = log or EngineeringLog()
    emit = log.emit
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    loads = job.loads
    material = job.material
    emit("start", {"nemo_version": __version__, "python": platform.python_version(), "part": "pipe-bracket",
                   "rule_set": job.rule_set.describe(),
                   "material": {"id": material.id, "name": material.name, "source": material.source},
                   "plates_mm": list(job.plate_thicknesses_mm), "fea_levels": list(fea_levels) if run_fea else []})
    report_progress("Working out the forces", 0.01)
    steps = [s.to_dict() for s in load_steps(job, loads)]
    emit("loads", {"steps": steps, **loads.to_dict()})

    report_progress("Checking the pipe span", 0.02)
    designs, stats = shortlist_brackets(job, progress=lambda m, f: report_progress(m, 0.03 + 0.25 * f), emit=emit)
    emit("search_done", {"combinations": stats.combinations, "evaluations": stats.evaluations,
                         "skipped": stats.skipped, "designs": [d.key for d in designs]})

    summary_designs = []
    for index, item in enumerate(designs):
        share = 0.7 / len(designs)
        base = 0.28 + index * share
        name = item.label.split(" (")[0].lower()
        folder = run_dir / "designs" / item.key
        folder.mkdir(parents=True, exist_ok=True)
        report_progress(f"Building the 3D model ({name})", base)
        solid = build_bracket(item.design)
        formula = item.design.volume_mm3()
        emit("cad", {"target": item.key, "volume_mm3": solid.volume_mm3, "formula_volume_mm3": formula,
                     "difference": (solid.volume_mm3 - formula) / formula, "solids": solid.solid_count, "mass_kg": item.mass_kg})
        step = solid.export_step(folder / "bracket.step")
        stl = solid.export_stl(folder / "bracket.stl")
        dxf = write_cutting_dxf(item.design, folder / "bracket-cutting.dxf", material_name=material.name, project_name=project_name)
        fea_summary = None
        if run_fea:
            report_progress(f"Running the stress check ({name})", base + share * 0.2)
            arm = item.report.values["governing_stress_mpa"]
            seat = item.report.check("seat_bending").demand
            study = analyse_bracket(item.design, material=material, loads=loads, levels=fea_levels, emit=emit, key=item.key,
                                    hand_stress_mpa=max(arm, seat),
                                    hand_label="seat plate between the knees" if seat >= arm else "bracket arm bending")
            fea_summary = study.to_dict()
            (folder / "stress-surface.json").write_text(json.dumps(stress_surface(study.final)), encoding="utf-8")
        summary_designs.append({
            "key": item.key, "label": item.label, "target_utilization": item.target_utilization,
            "check_report": item.report.to_dict(), "cad_volume_mm3": solid.volume_mm3, "fea": fea_summary,
            "files": {"step": str(step.relative_to(run_dir)), "stl": str(stl.relative_to(run_dir)),
                      "dxf": str(dxf.relative_to(run_dir)),
                      "stress_surface": f"designs/{item.key}/stress-surface.json" if run_fea else None},
        })

    with (run_dir / "designs-evaluated.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(EVALUATED_COLUMNS)
        writer.writerows(stats.evaluated)
    seconds = time.perf_counter() - started
    emit("done", {"seconds": seconds})
    summary = {
        "nemo_results_version": 2,
        "part": "pipe-bracket",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "job": job.to_dict(),
        "loads": loads.to_dict(),
        "load_steps": steps,
        "rule_set": job.rule_set.describe(),
        "material": {"id": material.id, "name": material.name, "source": material.source,
                     "tensile_strength_mpa": material.tensile_strength_mpa,
                     "elastic_modulus_gpa": material.elastic_modulus_gpa, "density_kg_m3": material.density_kg_m3},
        "search": {"combinations": stats.combinations, "evaluations": stats.evaluations, "skipped": stats.skipped},
        "designs": summary_designs,
        "files": {"engineering_log": "engineering-log.json", "designs_evaluated": "designs-evaluated.csv"},
        "seconds": seconds,
    }
    (run_dir / "engineering-log.json").write_text(json.dumps(log.events), encoding="utf-8")
    (run_dir / "results.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    report_progress("Done", 1.0)
    return summary
