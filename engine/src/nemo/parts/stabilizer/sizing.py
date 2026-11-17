"""Size the internal structure of the stabilizer fin.

The outer foil (span, chord, section) is fixed by the hydrodynamic design. For
every stock plate thickness pair (skin, webs) NEMO tries every rib spacing
from 150 mm to 1000 mm in 25 mm steps, and sizes the stock to the smallest
5 mm step that passes the UR S10 stock checks. The lightest fin that passes
every check within its target is kept.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable

from ...rules import IACSS10
from ..padeye.sizing import TARGETS, NoFeasibleDesign
from .checks import bearing_lengths, check_fin, stock_cases
from .geometry import FinDesign
from .job import FinJob, FinLoads

EVALUATED_COLUMNS = ("target", "skin_mm", "web_mm", "rib_spacing_mm", "ribs", "stock_mm", "mass_kg", "highest_use", "passes_target")
RIB_SPACINGS = tuple(range(150, 1001, 25))
Emit = Callable[[str, dict], None]


@dataclass(frozen=True)
class SizedFin:
    key: str
    label: str
    target_utilization: float
    report: object

    @property
    def design(self) -> FinDesign:
        return self.report.design

    @property
    def mass_kg(self) -> float:
        return self.report.mass_kg


@dataclass
class Stats:
    combinations: int = 0
    evaluations: int = 0
    skipped: int = 0
    evaluated: list[tuple] = field(default_factory=list)


def stock_diameter(job: FinJob, loads: FinLoads, cap: float) -> float:
    """Smallest stock (5 mm steps) meeting UR S10.4 torsion and combined stress at ``cap`` of the allowable."""
    stock = job.stock_material
    rs = job.rule_set
    d = 40.0
    while d <= 1000.0:
        k = IACSS10.material_factor(stock.yield_strength_mpa(d), stock.tensile_strength_mpa)
        d3 = d**3
        ok = True
        for _, _, moment, torque in stock_cases(loads):  # ahead, and astern when included
            tau = 5.1 * torque / d3 * 1e3
            sb = 10.2 * moment / d3 * 1e3
            ok = ok and tau <= cap * rs.stock_torsion_mpa / k and math.hypot(sb, math.sqrt(3) * tau) <= cap * rs.stock_equivalent_mpa / k
        # The bearings must fit within UR S10's 1.2 x diameter; a bigger stock gives them more surface.
        ok = ok and all(length <= longest for _, _, _, length, longest in bearing_lengths(job, loads, d))
        if ok:
            return d
        d += 5.0
    raise NoFeasibleDesign("The stock would have to be more than 1 m across. Reduce the fin size, the speed or the largest angle.")


def _design(job: FinJob, skin: float, web: float, ribs: float, stock: float) -> FinDesign:
    return FinDesign(job.span_m * 1000.0, job.chord_m * 1000.0, job.thickness_ratio, job.stock_position, job.front_spar,
                     job.rear_spar, skin, web, float(ribs), stock, job.bearing_gap_mm)


def _violation(report, cap: float) -> float:
    total = 0.0
    for c in report.required_checks:
        limit = cap if c.category == "strength" else 1.0
        if c.utilization > limit:
            total += (c.utilization - limit) ** 2
    return total


def _use(report) -> float:
    return max(c.utilization for c in report.required_checks if c.category == "strength")


def size_fin(job: FinJob, *, cap: float = 1.0, emit: Emit | None = None, target: str = "", stats: Stats | None = None,
             quick: bool = False):
    issues = job.problems()
    if issues:
        raise ValueError(" ".join(issues))
    loads = job.loads
    stats = stats or Stats()
    send = emit or (lambda kind, data: None)
    d_stock = stock_diameter(job, loads, cap)
    plates = sorted(t for t in set(job.plate_thicknesses_mm) if t <= job.material.max_thickness_mm)
    combos = [(s, w) for s in plates for w in plates if w >= 8.0]
    spacings = RIB_SPACINGS[::4] if quick else RIB_SPACINGS
    if not combos:
        raise NoFeasibleDesign("Tick at least one plate of 8 mm or more: UR S10 needs webs of at least 8 mm.")
    best = None
    points = []
    for index, (skin, web) in enumerate(combos, start=1):
        stats.combinations += 1
        found = None
        for ribs in spacings:
            stats.evaluations += 1
            design = _design(job, skin, web, ribs, d_stock)
            if design.problems():
                continue
            report = check_fin(design, job, loads)
            ok = _violation(report, cap) <= 0
            stats.evaluated.append((target, skin, web, ribs, design.rib_count, d_stock, report.mass_kg, _use(report), ok))
            points.append([round(report.mass_kg, 3), round(_use(report), 4), ok])
            if ok and (found is None or report.mass_kg < found.mass_kg):
                found = report
        improved = found is not None and (best is None or found.mass_kg < best.mass_kg)
        if improved:
            best = found
        send("combination", {"target": target, "index": index, "count": len(combos), "plate_mm": skin, "cheek_mm": web,
                             "evaluations": stats.evaluations, "outcome": "best" if improved else ("passed" if found else "no design"),
                             "mass_kg": found.mass_kg if found else None})
    if points:
        stride = max(1, len(points) // 120)
        sample = points[::stride]
        if best is not None:
            sample.append([round(best.mass_kg, 3), round(_use(best), 4), True])
        send("samples", {"target": target, "points": sample, "evaluations": stats.evaluations})
    if best is None:
        raise NoFeasibleDesign("No fin structure passed every check with the plates given. Tick thicker plate, or reduce the "
                               "speed or the largest fin angle.")
    return best


def shortlist_fins(job: FinJob, *, progress=None, emit: Emit | None = None) -> tuple[list[SizedFin], Stats]:
    loads = job.loads
    send = emit or (lambda kind, data: None)
    stats = Stats()
    found: list[SizedFin] = []
    for i, (key, label, cap) in enumerate(TARGETS):
        if progress:
            progress(f"Finding the {label.split(' (')[0].lower()} design", i / len(TARGETS))
        send("search_start", {"target": key, "label": label, "max_use": cap, "index": i, "count": len(TARGETS)})
        try:
            report = size_fin(job, cap=cap, emit=emit, target=key, stats=stats)
        except NoFeasibleDesign as exc:
            send("design_missing", {"target": key, "reason": str(exc)})
            if not found:
                raise
            continue
        duplicate = any(report.design == f.design for f in found)
        send("design_found", {"target": key, "label": label, "duplicate": duplicate, "mass_kg": report.mass_kg,
                              "max_use": _use(report), "governing": report.governing.title, "design": report.design.to_dict()})
        if not duplicate:
            found.append(SizedFin(key, label, cap, report))
    del loads
    return found, stats
