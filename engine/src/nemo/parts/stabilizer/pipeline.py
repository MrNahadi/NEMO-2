"""Full stabilizer fin run: foil loads, structure sizing, 3D models, rib profiles and the stock stress check."""

from __future__ import annotations

import csv
import json
import platform
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from build123d import export_step

from ... import __version__
from ...fea_study import MESH_LEVELS
from ...hydro import naca_00xx, panel_solve
from ...runlog import EngineeringLog, stress_surface
from .cad import build_fin, build_stock, formula_volume_mm3, write_cutting_dxf
from .fea import analyse_stock
from .job import FinJob, load_steps
from .sizing import EVALUATED_COLUMNS, shortlist_fins


def hydro_event(job: FinJob, loads) -> dict:
    xs, ys = naca_00xx(job.thickness_ratio)
    res = panel_solve(xs, ys, loads.section_angle_deg)
    n = len(res.cp) // 2
    lower = np.stack([res.x_mid[:n][::-1], res.cp[:n][::-1]], axis=1)
    upper = np.stack([res.x_mid[n:], res.cp[n:]], axis=1)
    return {
        "steps": [s.to_dict() for s in load_steps(job, loads)],
        "upper": np.round(upper[::2], 4).tolist(),
        "lower": np.round(lower[::2], 4).tolist(),
        "cp_min": loads.cp_min,
        "cavitation_number": loads.cavitation_number,
        "section_angle_deg": loads.section_angle_deg,
        **loads.to_dict(),
    }


def run_fin_job(job: FinJob, run_dir: Path, *, project_name: str = "", progress=None,
                fea_levels: tuple[float, ...] = MESH_LEVELS, run_fea: bool = True, log: EngineeringLog | None = None) -> dict:
    started = time.perf_counter()
    report_progress = progress or (lambda message, fraction: None)
    log = log or EngineeringLog()
    emit = log.emit
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    loads = job.loads
    plate, stock = job.material, job.stock_material
    emit("start", {"nemo_version": __version__, "python": platform.python_version(), "part": "stabilizer",
                   "rule_set": job.rule_set.describe(), "material": {"id": plate.id, "name": plate.name, "source": plate.source},
                   "plates_mm": list(job.plate_thicknesses_mm), "fea_levels": list(fea_levels) if run_fea else []})
    report_progress("Working out the foil loads", 0.01)
    steps = [s.to_dict() for s in load_steps(job, loads)]
    emit("loads", {"steps": steps, **loads.to_dict()})
    emit("hydro", hydro_event(job, loads))

    designs, stats = shortlist_fins(job, progress=lambda m, f: report_progress(m, 0.03 + 0.2 * f), emit=emit)
    emit("search_done", {"combinations": stats.combinations, "evaluations": stats.evaluations, "skipped": stats.skipped,
                         "designs": [d.key for d in designs]})
    summary_designs = []
    for index, item in enumerate(designs):
        share = 0.75 / len(designs)
        base = 0.23 + index * share
        name = item.label.split(" (")[0].lower()
        folder = run_dir / "designs" / item.key
        folder.mkdir(parents=True, exist_ok=True)
        report_progress(f"Building the 3D model ({name})", base)
        solid = build_fin(item.design)
        formula = formula_volume_mm3(item.design)
        emit("cad", {"target": item.key, "volume_mm3": solid.volume_mm3, "formula_volume_mm3": formula,
                     "difference": (solid.volume_mm3 - formula) / formula, "solids": solid.solid_count, "mass_kg": item.mass_kg})
        step = solid.export_step(folder / "fin.step")
        stl = solid.export_stl(folder / "fin.stl")
        stock_step = folder / "fin-stock.step"  # the stock alone, as NEMO's stress check models it, for a Fusion cross-check
        if not export_step(build_stock(item.design), str(stock_step)):
            raise RuntimeError(f"STEP export failed: {stock_step}")
        dxf = write_cutting_dxf(item.design, folder / "fin-rib-cutting.dxf", material_name=plate.name, project_name=project_name)
        fea_summary = None
        if run_fea:
            report_progress(f"Running the stress check on the stock ({name})", base + share * 0.3)
            study = analyse_stock(item.design, material=stock, loads=loads, levels=fea_levels, emit=emit, key=item.key)
            fea_summary = study.to_dict()
            (folder / "stress-surface.json").write_text(json.dumps(stress_surface(study.final)), encoding="utf-8")
        summary_designs.append({
            "key": item.key, "label": item.label, "target_utilization": item.target_utilization,
            "check_report": item.report.to_dict(), "cad_volume_mm3": solid.volume_mm3, "fea": fea_summary,
            "files": {"step": str(step.relative_to(run_dir)), "stl": str(stl.relative_to(run_dir)), "dxf": str(dxf.relative_to(run_dir)),
                      "stock_step": str(stock_step.relative_to(run_dir)),
                      "stress_surface": f"designs/{item.key}/stress-surface.json" if run_fea else None},
        })
    with (run_dir / "designs-evaluated.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(EVALUATED_COLUMNS)
        writer.writerows(stats.evaluated)
    seconds = time.perf_counter() - started
    emit("done", {"seconds": seconds})
    summary = {
        "nemo_results_version": 2, "part": "stabilizer",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "job": job.to_dict(), "loads": loads.to_dict(), "load_steps": steps, "rule_set": job.rule_set.describe(),
        "material": {"id": plate.id, "name": plate.name, "source": plate.source, "tensile_strength_mpa": plate.tensile_strength_mpa,
                     "elastic_modulus_gpa": plate.elastic_modulus_gpa, "density_kg_m3": plate.density_kg_m3},
        "stock_material": {"id": stock.id, "name": stock.name, "source": stock.source, "tensile_strength_mpa": stock.tensile_strength_mpa,
                           "elastic_modulus_gpa": stock.elastic_modulus_gpa, "density_kg_m3": stock.density_kg_m3},
        "search": {"combinations": stats.combinations, "evaluations": stats.evaluations, "skipped": stats.skipped},
        "designs": summary_designs,
        "files": {"engineering_log": "engineering-log.json", "designs_evaluated": "designs-evaluated.csv"},
        "seconds": seconds,
    }
    (run_dir / "engineering-log.json").write_text(json.dumps(log.events), encoding="utf-8")
    (run_dir / "results.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    report_progress("Done", 1.0)
    return summary
