"""Find buildable pipe support brackets.

The seat length follows from where the pipe is and the U-bolt size. For every
pair of stock plate thicknesses (seat, knees), Nelder-Mead sizes the knee depth
and the seat width for the least steel with every check within its target.
The welds are then set to the smallest standard size that passes and the
dimensions rounded up to 5 mm. The U-bolt is the smallest one that passes, but
not smaller than NEMO's minimum for the pipe size.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from typing import Callable

from ...data import piping
from ...optimize import nelder_mead
from ..padeye.checks import minimum_fillet_size_mm
from ..padeye.sizing import TARGETS, WELD_SIZES_MM, NoFeasibleDesign
from .checks import check_bracket
from .geometry import HOLE_CLEARANCE_MM, BracketDesign
from .job import BracketJob, BracketLoads, SpanResult, span_analysis

EVALUATED_COLUMNS = ("target", "seat_mm", "knee_mm", "seat_width_mm", "knee_depth_mm", "seat_length_mm",
                     "root_weld_mm", "knee_weld_mm", "ubolt_mm", "mass_kg", "highest_use", "passes_target")
REFERENCE_WELD_MM = 6.0
SAMPLE_BATCH, SAMPLES_PER_BATCH = 300, 40
Emit = Callable[[str, dict], None]


def min_ubolt_mm(od_mm: float) -> float:
    """NEMO practice: a U-bolt sturdy enough to handle and tighten for the pipe size."""
    return 10.0 if od_mm < 60 else 12.0 if od_mm < 170 else 16.0 if od_mm < 280 else 20.0


@dataclass(frozen=True)
class SizedBracket:
    key: str
    label: str
    target_utilization: float
    report: object

    @property
    def design(self) -> BracketDesign:
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


@dataclass
class _Ctx:
    job: BracketJob
    loads: BracketLoads
    span: SpanResult
    stats: Stats = field(default_factory=Stats)
    emit: Emit | None = None
    target: str = ""
    buffer: list = field(default_factory=list)

    def send(self, kind: str, data: dict) -> None:
        if self.emit:
            self.emit(kind, data)

    def record(self, report, feasible: bool) -> None:
        if self.emit is None:
            return
        d = report.design
        use = _strength_use(report)
        self.stats.evaluated.append((self.target, d.seat_thickness_mm, d.knee_thickness_mm, d.seat_width_mm, d.knee_depth_mm,
                                     d.seat_length_mm, d.root_weld_mm, d.knee_weld_mm, d.ubolt_diameter_mm,
                                     report.mass_kg, use, feasible))
        self.buffer.append([round(report.mass_kg, 4), round(use, 4), feasible])
        if len(self.buffer) >= SAMPLE_BATCH:
            self.flush()

    def flush(self) -> None:
        if not self.buffer or self.emit is None:
            self.buffer.clear()
            return
        stride = max(1, len(self.buffer) // SAMPLES_PER_BATCH)
        points = self.buffer[::stride]
        ok = [p for p in self.buffer if p[2]]
        if ok:
            points.append(min(ok, key=lambda p: p[0]))
        self.send("samples", {"target": self.target, "points": points, "evaluations": self.stats.evaluations})
        self.buffer.clear()


def _context(job: BracketJob) -> _Ctx:
    issues = job.problems()
    if issues:
        raise ValueError(" ".join(issues))
    loads = job.loads
    return _Ctx(job=job, loads=loads, span=span_analysis(job, loads))


def size_bracket(job: BracketJob, *, cap: float = 1.0, quick: bool = False):
    ctx = _context(job)
    return _search(ctx, cap, quick)


def shortlist_brackets(job: BracketJob, *, progress=None, emit: Emit | None = None) -> tuple[list[SizedBracket], Stats]:
    ctx = _context(job)
    ctx.emit = emit
    ctx.send("span", ctx.span.to_dict())
    found: list[SizedBracket] = []
    for i, (key, label, cap) in enumerate(TARGETS):
        if progress:
            progress(f"Finding the {label.split(' (')[0].lower()} design", i / len(TARGETS))
        ctx.target = key
        ctx.send("search_start", {"target": key, "label": label, "max_use": cap, "index": i, "count": len(TARGETS)})
        try:
            report = _search(ctx, cap, quick=False)
        except NoFeasibleDesign as exc:
            ctx.flush()
            ctx.send("design_missing", {"target": key, "reason": str(exc)})
            if not found:
                raise
            continue
        ctx.flush()
        duplicate = any(report.design == f.design for f in found)
        ctx.send("design_found", {"target": key, "label": label, "duplicate": duplicate, "mass_kg": report.mass_kg,
                                  "max_use": _strength_use(report), "governing": report.governing.title,
                                  "design": report.design.to_dict()})
        if not duplicate:
            found.append(SizedBracket(key, label, cap, check_bracket(report.design, job, ctx.loads, ctx.span, working=True)))
    return found, ctx.stats


# ------------------------------------------------------------------ search
def _ubolt(ctx: _Ctx, cap: float) -> float:
    """Smallest U-bolt diameter whose legs pass, independent of the plates."""
    job, loads = ctx.job, ctx.loads
    od = job.pipe.od_mm
    grade = job.ubolt_grade
    rs = job.rule_set
    for size in piping()["ubolts"]["sizes"]:
        d = size["diameter_mm"]
        if d < min_ubolt_mm(od):
            continue
        tension = loads.up_n / 2.0 + loads.across_n * (od / 2.0) / (od + d)
        f_t, f_v = tension / size["tensile_area_mm2"], loads.across_n / 2.0 / size["tensile_area_mm2"]
        u = (f_t / rs.allowable_bolt_tension_mpa(grade["tensile_strength_mpa"])) ** 2 + \
            (f_v / (0.45 * grade["tensile_strength_mpa"] / rs.omega_bolt)) ** 2
        if u <= cap:
            return d
    raise NoFeasibleDesign("No U-bolt in NEMO's table is strong enough. Use a stronger U-bolt grade or a clamp designed for the load.")


def _search(ctx: _Ctx, cap: float, quick: bool):
    job = ctx.job
    mat = job.material
    d_ub = _ubolt(ctx, cap)
    od = job.pipe.od_mm
    e = job.pipe_offset_mm
    hole = d_ub + HOLE_CLEARANCE_MM
    length = 5.0 * math.ceil((e + (od + d_ub) / 2.0 + 1.5 * hole) / 5.0)
    plates = sorted(t for t in set(job.plate_thicknesses_mm) if t <= mat.max_thickness_mm)
    if not plates:
        raise NoFeasibleDesign(f"None of the ticked plate thicknesses is covered by the {mat.name} data.")
    combos = [(ts, tk) for ts in plates for tk in plates if tk <= ts]
    best = None
    for index, (ts, tk) in enumerate(combos, start=1):
        ctx.stats.combinations += 1
        b_min = 2.0 * tk + 2.0 * d_ub + 10.0
        lower = (length * b_min * ts + length * 0.3 * length * tk) * 1e-9 * mat.density_kg_m3
        info = {"target": ctx.target, "index": index, "count": len(combos), "plate_mm": ts, "cheek_mm": tk,
                "ubolt_mm": d_ub, "evaluations": ctx.stats.evaluations}
        if best is not None and lower >= best.mass_kg:
            ctx.stats.skipped += 1
            ctx.send("combination", {**info, "outcome": "skipped",
                                     "reason": f"Even its smallest bracket ({lower:.2f} kg) is heavier than the best so far ({best.mass_kg:.2f} kg)."})
            continue
        report = _size_combination(ctx, ts, tk, d_ub, length, b_min, cap, quick)
        improved = report is not None and (best is None or report.mass_kg < best.mass_kg)
        if improved:
            best = report
        ctx.flush()
        ctx.send("combination", {**info, "evaluations": ctx.stats.evaluations,
                                 "outcome": "best" if improved else ("passed" if report else "no design"),
                                 "mass_kg": report.mass_kg if report else None})
    if best is None:
        raise NoFeasibleDesign("No bracket passed every check with the plate thicknesses given. Tick thicker plate, "
                               "shorten the support spacing, or move the pipe closer to the bulkhead.")
    return best


def _size_combination(ctx, ts, tk, d_ub, length, b_min, cap, quick):
    job = ctx.job
    od = job.pipe.od_mm
    b_max = max(3.0 * od, b_min + 150.0)

    def make(x) -> BracketDesign:
        depth = length * (0.3 + 1.2 * x[0])
        width = b_min + x[1] * (b_max - b_min)
        return BracketDesign(length, width, ts, depth, tk, job.pipe_offset_mm, od, d_ub, REFERENCE_WELD_MM, REFERENCE_WELD_MM)

    def objective(x) -> float:
        ctx.stats.evaluations += 1
        design = make(x)
        if design.problems():
            return 1e9
        report = _evaluate(ctx, design)
        if report is None:
            return 1e9
        violation = _violation(report, cap)
        ctx.record(report, violation <= 0)
        return report.mass_kg * (1.0 + 1e3 * violation)

    starts = [[0.4, 0.2]] if quick else [[0.4, 0.2], [0.15, 0.05], [0.8, 0.5]]
    best_x, best_val = None, math.inf
    for start in starts:
        result = nelder_mead(objective, start, max_iter=60 if quick else 160)
        if result.value < best_val:
            best_x, best_val = result.x, result.value
    if best_x is None or best_val >= 1e9:
        return None
    design = make(best_x)
    for _ in range(40):
        rounded = replace(design, knee_depth_mm=5.0 * math.ceil(design.knee_depth_mm / 5.0 - 1e-9),
                          seat_width_mm=5.0 * math.ceil(design.seat_width_mm / 5.0 - 1e-9))
        if rounded.problems():
            return None
        report = _evaluate(ctx, rounded)
        if report is not None and _violation(report, cap) <= 0:
            return report
        design = replace(design, knee_depth_mm=design.knee_depth_mm * 1.04, seat_width_mm=design.seat_width_mm * 1.02)
    return None


def _evaluate(ctx: _Ctx, design: BracketDesign):
    job, loads, span = ctx.job, ctx.loads, ctx.span
    trial = check_bracket(design, job, loads, span)
    thick = max(design.seat_thickness_mm, design.knee_thickness_mm)
    root = _weld_for(trial.check("root_weld").utilization, design.root_weld_mm, thick,
                     min(design.seat_thickness_mm, design.knee_thickness_mm))
    knee = _weld_for(trial.check("knee_weld").utilization, design.knee_weld_mm, thick, design.knee_thickness_mm)
    if root is None or knee is None:
        return None
    return check_bracket(replace(design, root_weld_mm=root, knee_weld_mm=knee), job, loads, span)


def _weld_for(use: float, leg: float, thicker: float, max_leg: float):
    needed = max(leg * use * 1.02, minimum_fillet_size_mm(thicker))
    for size in WELD_SIZES_MM:
        if needed - 1e-9 <= size <= max_leg + 1e-9:
            return size
    return None


def _violation(report, cap: float) -> float:
    total = 0.0
    for c in report.required_checks:
        if c.category == "span":
            continue  # the pipe span does not depend on the bracket
        limit = cap if c.category == "strength" else 1.0
        excess = c.utilization - limit
        if excess > 0:
            total += excess * excess
    return total


def _strength_use(report) -> float:
    return max(c.utilization for c in report.required_checks if c.category == "strength")
