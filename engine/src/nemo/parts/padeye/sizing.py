"""Find buildable padeye designs for a lifting job.

Discrete choices (shackle, main plate thickness, cheek plate thickness) are
enumerated from the yard's stock. For each combination, Nelder-Mead sizes the
continuous dimensions (head radius, base length, cheek radius) for least plate
mass while every required check stays within its limit. Weld sizes are then set
to the smallest standard size that passes. Dimensions are rounded up to whole
millimetres (base length to 5 mm) so the result can be marked out and cut.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from typing import Callable

from ...data import Material, Shackle, get_material, plate_stock, shackles
from ...loads import LiftScenario, PadeyeLoads, padeye_loads
from ...optimize import nelder_mead
from ...rules import ASMEBTH1, get_rule_set
from .checks import (
    DEFAULT_ELECTRODE_STRENGTH_MPA,
    SHACKLE_JAW_CLEARANCE_MM,
    SHACKLE_MIN_FILL_FRACTION,
    PadeyeCheckReport,
    check_padeye,
    minimum_fillet_size_mm,
)
from .geometry import PadeyeDesign
from .working import explain

WELD_SIZES_MM = (3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 20.0)
MAX_BASE_WELD_FRACTION = 0.75  # NEMO practice: fillet leg at most 3/4 of the plate it joins
SAMPLE_BATCH = 400
SAMPLES_PER_BATCH = 40
EVALUATED_COLUMNS = ("target", "shackle_wll_t", "main_plate_mm", "cheek_plate_mm", "head_radius_mm",
                     "cheek_radius_mm", "base_length_mm", "hole_height_mm", "base_weld_mm", "cheek_weld_mm",
                     "mass_kg", "highest_use", "passes_target")

Emit = Callable[[str, dict], None]
SHACKLE_SIZES_TRIED = 3
REFERENCE_WELD_MM = 10.0

TARGETS = (
    ("lightest", "Lightest", 1.00),
    ("balanced", "Balanced (at least 15% spare)", 0.85),
    ("robust", "Extra margin (at least 30% spare)", 0.70),
)


@dataclass(frozen=True)
class PadeyeJob:
    """Everything the user tells NEMO about a padeye job."""

    scenario: LiftScenario
    material_id: str = "S355"
    plate_thicknesses_mm: tuple[float, ...] = tuple(plate_stock()["default_selected_mm"])
    allow_cheek_plates: bool = True
    rule_set_id: str = "asme-bth-1"
    design_category: str = "B"
    service_class: int = 0
    fill_shackle_jaw: bool = True
    electrode_strength_mpa: float = DEFAULT_ELECTRODE_STRENGTH_MPA

    @property
    def material(self) -> Material:
        return get_material(self.material_id)

    @property
    def rule_set(self) -> ASMEBTH1:
        return get_rule_set(self.rule_set_id, design_category=self.design_category, service_class=self.service_class)

    @property
    def loads(self) -> PadeyeLoads:
        return padeye_loads(self.scenario)

    def to_dict(self) -> dict:
        s = self.scenario
        return {
            "part": "padeye",
            "lift": {
                "lifted_mass_kg": s.lifted_mass_kg,
                "lift_points": s.lift_points,
                "sling_angle_deg": s.sling_angle_deg,
                "dynamic_factor": s.dynamic_factor,
                "points_carrying": s.points_carrying,
                "side_load_fraction": s.side_load_fraction,
            },
            "material_id": self.material_id,
            "plate_thicknesses_mm": list(self.plate_thicknesses_mm),
            "allow_cheek_plates": self.allow_cheek_plates,
            "rule_set_id": self.rule_set_id,
            "design_category": self.design_category,
            "service_class": self.service_class,
            "fill_shackle_jaw": self.fill_shackle_jaw,
            "electrode_strength_mpa": self.electrode_strength_mpa,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PadeyeJob":
        lift = data["lift"]
        defaults = cls(LiftScenario(1.0))
        return cls(
            scenario=LiftScenario(
                lifted_mass_kg=float(lift["lifted_mass_kg"]),
                lift_points=int(lift.get("lift_points", 2)),
                sling_angle_deg=float(lift.get("sling_angle_deg", 60.0)),
                dynamic_factor=float(lift.get("dynamic_factor", 1.0)),
                points_carrying=None if lift.get("points_carrying") is None else int(lift["points_carrying"]),
                side_load_fraction=float(lift.get("side_load_fraction", 0.05)),
            ),
            material_id=str(data.get("material_id", defaults.material_id)),
            plate_thicknesses_mm=tuple(float(t) for t in data.get("plate_thicknesses_mm", defaults.plate_thicknesses_mm)),
            allow_cheek_plates=bool(data.get("allow_cheek_plates", True)),
            rule_set_id=str(data.get("rule_set_id", defaults.rule_set_id)),
            design_category=str(data.get("design_category", defaults.design_category)),
            service_class=int(data.get("service_class", 0)),
            fill_shackle_jaw=bool(data.get("fill_shackle_jaw", True)),
            electrode_strength_mpa=float(data.get("electrode_strength_mpa", DEFAULT_ELECTRODE_STRENGTH_MPA)),
        )


@dataclass(frozen=True)
class SizedPadeye:
    key: str
    label: str
    target_utilization: float
    report: PadeyeCheckReport

    @property
    def design(self) -> PadeyeDesign:
        return self.report.design

    @property
    def mass_kg(self) -> float:
        return self.report.mass_kg


@dataclass
class SizingStats:
    combinations: int = 0
    evaluations: int = 0
    skipped: int = 0
    evaluated: list[tuple] = field(default_factory=list)  # rows matching EVALUATED_COLUMNS


class NoFeasibleDesign(ValueError):
    """No design meets the job with the stock and options given."""


@dataclass
class _Context:
    job: PadeyeJob
    loads: PadeyeLoads
    material: Material
    rule_set: ASMEBTH1
    stats: SizingStats = field(default_factory=SizingStats)
    emit: "Emit | None" = None
    target: str = ""
    _buffer: list[list] = field(default_factory=list)

    def send(self, kind: str, data: dict) -> None:
        if self.emit is not None:
            self.emit(kind, data)

    def record(self, report: PadeyeCheckReport, feasible: bool) -> None:
        """Log one design the optimizer tried (only when someone is listening)."""
        if self.emit is None:
            return
        d = report.design
        use = _max_strength_use(report)
        self.stats.evaluated.append((self.target, report.shackle.wll_t, d.main_thickness_mm, d.cheek_thickness_mm,
                               d.head_radius_mm, d.cheek_radius_mm, d.base_length_mm, d.hole_height_mm,
                               d.weld_leg_mm, d.cheek_weld_leg_mm, report.mass_kg, use, feasible))
        self._buffer.append([round(report.mass_kg, 4), round(use, 4), feasible])
        if len(self._buffer) >= SAMPLE_BATCH:
            self.flush()

    def flush(self) -> None:
        """Send a thinned batch of tried designs for the live chart."""
        if not self._buffer or self.emit is None:
            self._buffer.clear()
            return
        stride = max(1, len(self._buffer) // SAMPLES_PER_BATCH)
        points = self._buffer[::stride]
        feasible = [p for p in self._buffer if p[2]]
        if feasible:
            points.append(min(feasible, key=lambda p: p[0]))
        self.send("samples", {"target": self.target, "points": points, "evaluations": self.stats.evaluations})
        self._buffer.clear()


def size_padeye(
    job: PadeyeJob,
    *,
    max_utilization: float = 1.0,
    quick: bool = False,
) -> PadeyeCheckReport:
    """Lightest buildable padeye whose strength checks stay at or below ``max_utilization``."""
    ctx = _context(job)
    return _search(ctx, max_utilization, quick)


def shortlist_padeyes(
    job: PadeyeJob,
    *,
    progress: Callable[[str, float], None] | None = None,
    emit: Emit | None = None,
) -> tuple[list[SizedPadeye], SizingStats]:
    """Up to three designs: lightest, balanced and extra margin. Duplicates are dropped.

    ``emit(kind, data)`` receives engineering events while the search runs:
    ``shackles``, ``search_start``, ``combination``, ``samples`` and ``design_found``.
    """
    ctx = _context(job)
    ctx.emit = emit
    candidates = _shackle_candidates(ctx.loads.sling_force_t)
    ctx.send("shackles", {
        "sling_force_t": ctx.loads.sling_force_t,
        "candidates": [_shackle_dict(s) for s in candidates],
        "rule": "Smallest catalogued shackle whose working load limit covers the sling force, plus the next two sizes.",
    })
    found: list[SizedPadeye] = []
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
        duplicate = any(_same(report.design, f.design) for f in found)
        ctx.send("design_found", {
            "target": key,
            "label": label,
            "duplicate": duplicate,
            "mass_kg": report.mass_kg,
            "max_use": _max_strength_use(report),
            "governing": report.governing.title,
            "design": report.design.to_dict(),
            "shackle": _shackle_dict(report.shackle),
        })
        if duplicate:
            continue
        found.append(SizedPadeye(key, label, cap, explain(report)))
    if progress:
        progress("Done", 1.0)
    return found, ctx.stats


# ------------------------------------------------------------------ search
def _context(job: PadeyeJob) -> _Context:
    issues = job.scenario.problems()
    if issues:
        raise ValueError(" ".join(issues))
    if not job.plate_thicknesses_mm:
        raise ValueError("Tick at least one plate thickness your workshop has.")
    return _Context(job=job, loads=job.loads, material=job.material, rule_set=job.rule_set)


def _search(ctx: _Context, cap: float, quick: bool) -> PadeyeCheckReport:
    job, loads, material = ctx.job, ctx.loads, ctx.material
    candidates = _shackle_candidates(loads.sling_force_t)
    thicknesses = sorted(t for t in set(job.plate_thicknesses_mm) if t <= material.max_thickness_mm)
    if not thicknesses:
        raise NoFeasibleDesign(f"None of the ticked plate thicknesses is covered by the {material.name} data.")

    best: PadeyeCheckReport | None = None
    reasons: set[str] = set()
    for shackle in candidates:
        jaw = shackle.jaw_width_mm
        combos = []
        for t in thicknesses:
            cheek_options = [0.0]
            if job.allow_cheek_plates:
                cheek_options += [tc for tc in thicknesses if tc <= t]
            for tc in cheek_options:
                total = t + 2 * tc
                if total + SHACKLE_JAW_CLEARANCE_MM > jaw:
                    reasons.add("too_thick")
                    continue
                if job.fill_shackle_jaw and total < SHACKLE_MIN_FILL_FRACTION * jaw:
                    reasons.add("too_thin")
                    continue
                combos.append((t, tc))
        for index, (t, tc) in enumerate(combos, start=1):
            ctx.stats.combinations += 1
            lower = _lower_bound_mass(shackle, t, tc, material)
            info = {"target": ctx.target, "index": index, "count": len(combos), "shackle_wll_t": shackle.wll_t,
                    "plate_mm": t, "cheek_mm": tc, "evaluations": ctx.stats.evaluations}
            if best is not None and lower >= best.mass_kg:
                ctx.stats.skipped += 1
                ctx.send("combination", {**info, "outcome": "skipped",
                                         "reason": f"Even its smallest possible padeye ({lower:.2f} kg) is heavier than the best so far ({best.mass_kg:.2f} kg)."})
                continue
            report = _size_combination(ctx, shackle, t, tc, cap, quick)
            improved = report is not None and (best is None or report.mass_kg < best.mass_kg)
            if improved:
                best = report
            ctx.flush()
            ctx.send("combination", {**info, "evaluations": ctx.stats.evaluations,
                                     "outcome": "best" if improved else ("passed" if report else "no design"),
                                     "mass_kg": report.mass_kg if report else None})
        if best is not None:
            break  # the smallest shackle that works gives the lightest padeye
    if best is None:
        raise NoFeasibleDesign(_explain(reasons, candidates, job))
    return best


def _size_combination(
    ctx: _Context, shackle: Shackle, t: float, tc: float, cap: float, quick: bool
) -> PadeyeCheckReport | None:
    dh = _hole_for(shackle)
    r_min, r_max = _head_radius_range(dh)
    use_cheeks = tc > 0
    if use_cheeks and r_max - dh / 2 <= 10:
        return None

    def make(x: list[float]) -> PadeyeDesign:
        r = r_min + x[0] * (r_max - r_min)
        length = 2 * r + x[1] * 6 * r
        rc = 0.0
        if use_cheeks:
            rc_lo = dh / 2 + 10
            rc = rc_lo + x[2] * max(r - rc_lo, 0.0)
        return PadeyeDesign(
            main_thickness_mm=t,
            head_radius_mm=r,
            hole_diameter_mm=dh,
            base_length_mm=length,
            hole_height_mm=max(r, 2.0 * shackle.pin_diameter_mm),
            weld_leg_mm=REFERENCE_WELD_MM,
            cheek_thickness_mm=tc,
            cheek_radius_mm=rc,
            cheek_weld_leg_mm=REFERENCE_WELD_MM if use_cheeks else 0.0,
        )

    def objective(x: list[float]) -> float:
        ctx.stats.evaluations += 1
        design = make(x)
        if design.problems():
            return 1e9
        report = _evaluate(ctx, design, shackle)
        if report is None:
            return 1e9
        violation = _violation(report, cap)
        ctx.record(report, violation <= 0.0)
        return report.mass_kg * (1.0 + 1e3 * violation)

    starts = [[0.4, 0.3, 0.6]] if quick else [[0.4, 0.3, 0.6], [0.15, 0.1, 0.9], [0.8, 0.6, 0.3]]
    dims = 3 if use_cheeks else 2
    best_x, best_val = None, math.inf
    for start in starts:
        result = nelder_mead(objective, start[:dims], max_iter=80 if quick else 200)
        if result.value < best_val:
            best_x, best_val = result.x, result.value
    if best_x is None or best_val >= 1e9:
        return None

    design = make(best_x)
    return _finalise(ctx, design, shackle, cap)


def _finalise(ctx: _Context, design: PadeyeDesign, shackle: Shackle, cap: float) -> PadeyeCheckReport | None:
    """Round to buildable sizes and grow the design until every check passes."""
    for _ in range(40):
        rounded = _round_up(design)
        if rounded.problems():
            return None
        report = _evaluate(ctx, rounded, shackle)
        if report is not None and _violation(report, cap) <= 0.0:
            return report
        design = replace(
            design,
            head_radius_mm=design.head_radius_mm * 1.02,
            base_length_mm=design.base_length_mm * 1.03,
            hole_height_mm=max(design.head_radius_mm * 1.02, 2.0 * shackle.pin_diameter_mm),
        )
    return None


def _evaluate(ctx: _Context, design: PadeyeDesign, shackle: Shackle) -> PadeyeCheckReport | None:
    """Check a design after choosing the smallest standard welds that pass."""
    job, rs = ctx.job, ctx.rule_set
    trial = check_padeye(design, material=ctx.material, shackle=shackle, loads=ctx.loads, rule_set=rs,
                         electrode_strength_mpa=job.electrode_strength_mpa)
    base_leg = _weld_for(trial.check("base_weld").utilization, design.weld_leg_mm, design.main_thickness_mm,
                         MAX_BASE_WELD_FRACTION * design.main_thickness_mm)
    if base_leg is None:
        return None
    cheek_leg = 0.0
    if design.has_cheeks:
        cheek_leg = _weld_for(trial.check("cheek_weld").utilization, design.cheek_weld_leg_mm,
                              max(design.cheek_thickness_mm, design.main_thickness_mm), design.cheek_thickness_mm)
        if cheek_leg is None:
            return None
    final = replace(design, weld_leg_mm=base_leg, cheek_weld_leg_mm=cheek_leg)
    return check_padeye(final, material=ctx.material, shackle=shackle, loads=ctx.loads, rule_set=rs,
                        electrode_strength_mpa=job.electrode_strength_mpa)


def _weld_for(utilization_at_leg: float, leg: float, thicker_part: float, max_leg: float) -> float | None:
    needed = leg * utilization_at_leg * 1.02  # small allowance: throat separation changes slightly with size
    minimum = max(needed, minimum_fillet_size_mm(thicker_part))
    for size in WELD_SIZES_MM:
        if size >= minimum - 1e-9 and size <= max_leg + 1e-9:
            return size
    return None


def _violation(report: PadeyeCheckReport, cap: float) -> float:
    total = 0.0
    for c in report.required_checks:
        limit = cap if c.category == "strength" else 1.0
        excess = c.utilization - limit
        if excess > 0:
            total += excess * excess
    return total


# ----------------------------------------------------------------- helpers
def _max_strength_use(report: PadeyeCheckReport) -> float:
    return max(c.utilization for c in report.required_checks if c.category == "strength")


def _shackle_dict(s: Shackle) -> dict:
    return {"label": s.label, "wll_t": s.wll_t, "pin_diameter_mm": s.pin_diameter_mm,
            "jaw_width_mm": s.jaw_width_mm, "hole_mm": _hole_for(s)}


def _shackle_candidates(sling_t: float) -> list[Shackle]:
    adequate = [s for s in shackles() if s.wll_t >= sling_t]
    if not adequate:
        largest = shackles()[-1]
        raise NoFeasibleDesign(
            f"The sling force on each padeye is {sling_t:.1f} t, more than the largest shackle in the "
            f"table ({largest.wll_t:g} t). Use more lifting points or a different lifting arrangement."
        )
    return adequate[:SHACKLE_SIZES_TRIED]


def _hole_for(shackle: Shackle) -> float:
    """Hole diameter for a shackle pin: pin + max(1 mm, 4%), rounded up to 0.5 mm."""
    raw = shackle.pin_diameter_mm + max(1.0, 0.04 * shackle.pin_diameter_mm)
    return math.ceil(raw * 2.0) / 2.0


def _head_radius_range(dh: float) -> tuple[float, float]:
    return dh / 2 + max(0.25 * dh, 5.0), dh / 2 + 3.0 * dh + 30.0


def _lower_bound_mass(shackle: Shackle, t: float, tc: float, material: Material) -> float:
    dh = _hole_for(shackle)
    r = _head_radius_range(dh)[0]
    design = PadeyeDesign(t, r, dh, 2 * r, max(r, 2 * shackle.pin_diameter_mm), 3.0,
                          cheek_thickness_mm=0.0)
    mass = design.steel_mass_kg(material)
    if tc > 0:
        ring = math.pi * ((dh / 2 + 10) ** 2 - dh**2 / 4) * tc * 2
        mass += ring * 1e-9 * material.density_kg_m3
    return mass


def _round_up(design: PadeyeDesign) -> PadeyeDesign:
    r = math.ceil(design.head_radius_mm - 1e-9)
    rc = min(math.ceil(design.cheek_radius_mm - 1e-9), r) if design.has_cheeks else 0.0
    length = 5.0 * math.ceil(design.base_length_mm / 5.0 - 1e-9)
    height = math.ceil(max(design.hole_height_mm, r) - 1e-9)
    return replace(design, head_radius_mm=float(r), cheek_radius_mm=float(rc),
                   base_length_mm=float(length), hole_height_mm=float(height))


def _same(a: PadeyeDesign, b: PadeyeDesign) -> bool:
    return a == b


def _explain(reasons: set[str], candidates: list[Shackle], job: PadeyeJob) -> str:
    jaw = candidates[-1].jaw_width_mm
    if reasons == {"too_thick"}:
        return (
            f"Every plate thickness you ticked is too thick for the shackle jaw ({jaw:g} mm). "
            "Tick thinner plate."
        )
    if reasons == {"too_thin"}:
        return (
            f"The plates you ticked are too thin to fill the shackle jaw. Tick thicker plate, "
            "allow cheek plates, or switch off the jaw-fill rule."
        )
    return (
        "No padeye passed every check with the plate thicknesses and options given. "
        "Tick more plate thicknesses, allow cheek plates, or choose a stronger material."
    )
