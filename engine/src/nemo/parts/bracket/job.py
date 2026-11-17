"""Pipe support bracket job: the pipe, the ship motions, and the forces on one bracket.

Axes on the bracket: x out from the bulkhead, y along the pipe, z up. The pipe
runs parallel to the bulkhead and sits on the bracket's seat plate at a
distance e from the bulkhead, held by a U-bolt.

Forces on one bracket come from the weight of the pipe span it carries (pipe,
contents and insulation), multiplied by the ship-motion accelerations:

* vertical: W (1 + a_v), and uplift W (a_v - 1) when a_v is more than 1 g;
* horizontal, across the pipe: W a_h, where a_h is the athwartships or
  fore-and-aft acceleration depending on which way the pipe runs;
* along the pipe: friction mu W (1 + a_v). The support is a sliding guide;
  axial inertia of the run goes to the pipe anchors.

The accelerations are inputs. NEMO's starting values are conservative for most
positions on a ship but are not taken from a class rule; enter the values from
the vessel's design basis or class rules (for example DNV-RU-SHIP Pt.3 Ch.4).
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field

from ...data import Material, find_by_id, get_material, piping, plate_stock
from ...loads import STANDARD_GRAVITY
from ...rules import get_rule_set
from ...working import Step, num

DEFAULT_ELECTRODE_STRENGTH_MPA = 482.0
DIRECTIONS = ("fore_aft", "athwartships")


@dataclass(frozen=True)
class Pipe:
    nps: str
    dn: int
    od_mm: float
    wall_mm: float
    schedule: str
    material: dict

    @property
    def bore_mm(self) -> float:
        return self.od_mm - 2.0 * self.wall_mm

    @property
    def metal_area_mm2(self) -> float:
        return math.pi / 4.0 * (self.od_mm**2 - self.bore_mm**2)

    @property
    def inertia_mm4(self) -> float:
        return math.pi / 64.0 * (self.od_mm**4 - self.bore_mm**4)

    @property
    def section_modulus_mm3(self) -> float:
        return self.inertia_mm4 / (self.od_mm / 2.0)

    @property
    def label(self) -> str:
        return f"NPS {self.nps} (DN {self.dn}) {self.schedule}, {self.od_mm:g} × {self.wall_mm:g} mm"


@dataclass(frozen=True)
class BracketJob:
    pipe_nps: str = "4"
    schedule: str = "STD"
    pipe_material_id: str = "CS"
    fluid_id: str = "sea_water"
    insulation_id: str = "none"
    insulation_thickness_mm: float = 0.0
    span_m: float = 3.0
    continuity_factor: float = 1.25
    pipe_direction: str = "fore_aft"
    accel_vertical_g: float = 1.0
    accel_transverse_g: float = 0.8
    accel_longitudinal_g: float = 0.5
    friction: float = 0.3
    gap_mm: float = 50.0
    material_id: str = "GRADE_A"
    plate_thicknesses_mm: tuple[float, ...] = (6.0, 8.0, 10.0, 12.0, 15.0, 20.0)
    ubolt_grade_id: str = "4.6"
    propeller_rpm: float = 120.0
    propeller_blades: int = 4
    engine_rpm: float = 750.0
    engine_cylinders: int = 6
    engine_stroke: int = 4
    frequency_margin: float = 0.20
    deflection_limit_mm: float = 1.0
    electrode_strength_mpa: float = DEFAULT_ELECTRODE_STRENGTH_MPA
    rule_set_id: str = "aisc-360-asd"

    # ------------------------------------------------------------ lookups
    @property
    def pipe(self) -> Pipe:
        data = piping()
        entry = next((p for p in data["pipes"] if p["nps"] == self.pipe_nps), None)
        if entry is None:
            raise ValueError(f"NEMO has no pipe size NPS {self.pipe_nps}.")
        if self.schedule not in entry["wall_mm"]:
            raise ValueError(f"Schedule {self.schedule} is not listed for NPS {self.pipe_nps}.")
        return Pipe(entry["nps"], entry["dn"], entry["od_mm"], entry["wall_mm"][self.schedule], self.schedule,
                    find_by_id(data["pipe_materials"], self.pipe_material_id, "pipe material"))

    @property
    def fluid(self) -> dict:
        return find_by_id(piping()["fluids"], self.fluid_id, "fluid")

    @property
    def insulation(self) -> dict:
        return find_by_id(piping()["insulation"], self.insulation_id, "insulation")

    @property
    def ubolt_grade(self) -> dict:
        return find_by_id(piping()["ubolts"]["grades"], self.ubolt_grade_id, "U-bolt grade")

    @property
    def material(self) -> Material:
        return get_material(self.material_id)

    @property
    def rule_set(self):
        return get_rule_set(self.rule_set_id)

    @property
    def horizontal_accel_g(self) -> float:
        """Acceleration across the pipe, in the horizontal plane."""
        return self.accel_transverse_g if self.pipe_direction == "fore_aft" else self.accel_longitudinal_g

    @property
    def insulation_mm(self) -> float:
        return self.insulation_thickness_mm if self.insulation["density_kg_m3"] > 0 else 0.0

    @property
    def pipe_offset_mm(self) -> float:
        """Bulkhead to pipe centre: the gap, the insulation and half the pipe."""
        return self.gap_mm + self.insulation_mm + self.pipe.od_mm / 2.0

    # --------------------------------------------------------- validation
    def problems(self) -> list[str]:
        p: list[str] = []
        try:
            self.pipe, self.fluid, self.insulation, self.ubolt_grade, self.material  # noqa: B018
        except (KeyError, ValueError) as exc:
            return [str(exc).strip("'")]
        if not (0.3 <= self.span_m <= 15.0):
            p.append("Support spacing must be between 0.3 m and 15 m.")
        if not (1.0 <= self.continuity_factor <= 1.5):
            p.append("The continuity factor must be between 1.0 and 1.5.")
        if self.pipe_direction not in DIRECTIONS:
            p.append("Say whether the pipe runs fore and aft or athwartships.")
        for label, value in (("Vertical", self.accel_vertical_g), ("Athwartships", self.accel_transverse_g),
                             ("Fore-and-aft", self.accel_longitudinal_g)):
            if not (0.0 <= value <= 3.0):
                p.append(f"{label} acceleration must be between 0 and 3 g.")
        if not (0.0 <= self.friction <= 1.0):
            p.append("Friction must be between 0 and 1.")
        if not (10.0 <= self.gap_mm <= 1000.0):
            p.append("The gap to the bulkhead must be between 10 mm and 1000 mm.")
        if self.insulation["density_kg_m3"] > 0 and not (10.0 <= self.insulation_thickness_mm <= 200.0):
            p.append("Insulation thickness must be between 10 mm and 200 mm.")
        if not self.plate_thicknesses_mm:
            p.append("Tick at least one plate thickness your workshop has.")
        if self.propeller_rpm <= 0 or self.propeller_blades < 2:
            p.append("Enter the propeller speed and number of blades.")
        if self.engine_rpm <= 0 or self.engine_cylinders < 1 or self.engine_stroke not in (2, 4):
            p.append("Enter the engine speed, number of cylinders and whether it is 2- or 4-stroke.")
        if not (0.05 <= self.frequency_margin <= 0.5):
            p.append("The frequency margin must be between 5% and 50%.")
        if not (0.1 <= self.deflection_limit_mm <= 10.0):
            p.append("The deflection limit must be between 0.1 mm and 10 mm.")
        return p

    # ------------------------------------------------------------ dict io
    def to_dict(self) -> dict:
        data = asdict(self)
        data["plate_thicknesses_mm"] = list(self.plate_thicknesses_mm)
        data["part"] = "pipe-bracket"
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "BracketJob":
        defaults = cls()
        kwargs = {}
        for name, value in asdict(defaults).items():
            if name not in data or data[name] is None:
                continue
            raw = data[name]
            if isinstance(value, tuple):
                kwargs[name] = tuple(float(v) for v in raw)
            elif isinstance(value, bool):
                kwargs[name] = bool(raw)
            elif isinstance(value, int):
                kwargs[name] = int(raw)
            elif isinstance(value, float):
                kwargs[name] = float(raw)
            else:
                kwargs[name] = str(raw)
        return cls(**kwargs)

    @property
    def loads(self) -> "BracketLoads":
        return bracket_loads(self)


@dataclass(frozen=True)
class BracketLoads:
    mass_per_m: dict  # kg/m by part: pipe, contents, insulation, total
    weight_per_m_n: float
    static_n: float  # W, the share of the span on one bracket
    down_n: float
    up_n: float
    across_n: float  # horizontal, across the pipe (bracket x)
    along_n: float  # along the pipe (friction)
    accel: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "mass_per_m": dict(self.mass_per_m),
            "weight_per_m_n": self.weight_per_m_n,
            "static_n": self.static_n,
            "down_n": self.down_n,
            "up_n": self.up_n,
            "across_n": self.across_n,
            "along_n": self.along_n,
            "accel": dict(self.accel),
            # Keys the shared screens read for every part.
            "sling_force_n": self.down_n,
            "sling_force_t": self.down_n / STANDARD_GRAVITY / 1000.0,
        }


def bracket_loads(job: BracketJob) -> BracketLoads:
    issues = job.problems()
    if issues:
        raise ValueError(" ".join(issues))
    pipe = job.pipe
    bore = pipe.bore_mm
    ins = job.insulation_mm
    to_m2 = 1e-6
    pipe_kg = pipe.metal_area_mm2 * to_m2 * pipe.material["density_kg_m3"]
    contents_kg = math.pi / 4 * bore**2 * to_m2 * job.fluid["density_kg_m3"]
    ins_kg = math.pi / 4 * ((pipe.od_mm + 2 * ins) ** 2 - pipe.od_mm**2) * to_m2 * job.insulation["density_kg_m3"]
    total = pipe_kg + contents_kg + ins_kg
    w_per_m = total * STANDARD_GRAVITY
    static = job.continuity_factor * w_per_m * job.span_m
    av, ah = job.accel_vertical_g, job.horizontal_accel_g
    down = static * (1.0 + av)
    return BracketLoads(
        mass_per_m={"pipe": pipe_kg, "contents": contents_kg, "insulation": ins_kg, "total": total},
        weight_per_m_n=w_per_m,
        static_n=static,
        down_n=down,
        up_n=static * max(av - 1.0, 0.0),
        across_n=static * ah,
        along_n=job.friction * down,
        accel={"vertical_g": av, "across_g": ah, "direction": job.pipe_direction},
    )


def load_steps(job: BracketJob, loads: BracketLoads) -> list[Step]:
    pipe = job.pipe
    m = loads.mass_per_m
    across = "athwartships" if job.pipe_direction == "fore_aft" else "fore and aft"
    steps = [
        Step("Pipe metal per metre", "m_p", "m_p = π/4 (D^2 − d^2) ρ_p",
             f"m_p = π/4 × ({num(pipe.od_mm)}² − {num(pipe.bore_mm)}²) mm² × {num(pipe.material['density_kg_m3'], 0)} kg/m³",
             m["pipe"], "kg/m"),
        Step("Contents per metre", "m_f", "m_f = π/4 d^2 ρ_f",
             f"m_f = π/4 × {num(pipe.bore_mm)}² mm² × {num(job.fluid['density_kg_m3'], 0)} kg/m³ ({job.fluid['name'].lower()})",
             m["contents"], "kg/m"),
    ]
    if m["insulation"] > 0:
        steps.append(Step("Insulation per metre", "m_i", "m_i = π/4 ((D + 2 t_i)^2 − D^2) ρ_i",
                          f"m_i = π/4 × ({num(pipe.od_mm + 2 * job.insulation_mm)}² − {num(pipe.od_mm)}²) mm² × {num(job.insulation['density_kg_m3'], 0)} kg/m³",
                          m["insulation"], "kg/m"))
    steps += [
        Step("Weight per metre", "q", "q = (m_p + m_f + m_i) g", f"q = {num(m['total'])} kg/m × 9.807 m/s²",
             loads.weight_per_m_n, "N/m"),
        Step("Weight on one bracket", "W", "W = k_c q S",
             f"W = {num(job.continuity_factor, 2)} × {num(loads.weight_per_m_n)} N/m × {num(job.span_m, 2)} m",
             loads.static_n / 1000, "kN",
             note="k_c allows for the pipe being continuous over several supports, which puts more than one span's weight on some of them."),
        Step("Downward force", "F_z", "F_z = W (1 + a_v)", f"F_z = {num(loads.static_n, 0)} N × (1 + {num(job.accel_vertical_g, 2)})",
             loads.down_n / 1000, "kN", note="a_v is the vertical ship-motion acceleration in g, on top of gravity."),
        Step("Force across the pipe", "F_x", "F_x = W a_h", f"F_x = {num(loads.static_n, 0)} N × {num(job.horizontal_accel_g, 2)}",
             loads.across_n / 1000, "kN", note=f"The pipe runs {'fore and aft' if job.pipe_direction == 'fore_aft' else 'athwartships'}, so a_h is the {across} acceleration."),
        Step("Friction along the pipe", "F_y", "F_y = μ F_z", f"F_y = {num(job.friction, 2)} × {num(loads.down_n, 0)} N",
             loads.along_n / 1000, "kN", note="The support is a sliding guide; the pipe anchors take the axial inertia of the run."),
    ]
    if loads.up_n > 0:
        steps.append(Step("Uplift", "F_u", "F_u = W (a_v − 1)", f"F_u = {num(loads.static_n, 0)} × ({num(job.accel_vertical_g, 2)} − 1)",
                          loads.up_n / 1000, "kN"))
    return steps


# ------------------------------------------------------------ pipe span
def excitations(job: BracketJob) -> list[tuple[str, float]]:
    shaft = job.propeller_rpm / 60.0
    engine = job.engine_rpm / 60.0
    firing = job.engine_cylinders * engine / (2.0 if job.engine_stroke == 4 else 1.0)
    return [
        ("Propeller shaft rotation", shaft),
        ("Propeller blade rate", job.propeller_blades * shaft),
        ("Blade rate, second harmonic", 2 * job.propeller_blades * shaft),
        ("Engine rotation", engine),
        ("Engine firing", firing),
    ]


@dataclass(frozen=True)
class SpanResult:
    natural_hz: float
    excitations: tuple[tuple[str, float], ...]
    nearest: tuple[str, float]
    separation: float
    pipe_stress_mpa: float
    pipe_allow_mpa: float
    sag_mm: float
    spans_m: dict
    recommended_m: float
    steps: tuple = ()

    def to_dict(self) -> dict:
        return {
            "natural_hz": self.natural_hz,
            "excitations": [{"name": n, "hz": f} for n, f in self.excitations],
            "nearest": {"name": self.nearest[0], "hz": self.nearest[1]},
            "separation": self.separation,
            "pipe_stress_mpa": self.pipe_stress_mpa,
            "pipe_allow_mpa": self.pipe_allow_mpa,
            "sag_mm": self.sag_mm,
            "spans_m": dict(self.spans_m),
            "recommended_m": self.recommended_m,
            "steps": [s.to_dict() for s in self.steps],
        }


SAG_LIMIT_MM = 2.5  # MSS SP-58 style span guidance for sustained sag


def span_analysis(job: BracketJob, loads: BracketLoads) -> SpanResult:
    """The pipe between supports: natural frequency, bending stress, sag and the longest sensible spacing."""
    pipe = job.pipe
    e_mpa = pipe.material["elastic_modulus_gpa"] * 1000.0
    ei_nm2 = e_mpa * 1e6 * pipe.inertia_mm4 * 1e-12
    mass = loads.mass_per_m["total"]
    span = job.span_m
    natural = (math.pi / 2.0) * math.sqrt(ei_nm2 / (mass * span**4))
    exc = tuple(excitations(job))
    nearest = min(exc, key=lambda e: abs(natural - e[1]) / e[1])
    separation = abs(natural - nearest[1]) / nearest[1]

    q = loads.weight_per_m_n / 1000.0  # N/mm
    q_design = q * math.hypot(1.0 + job.accel_vertical_g, job.horizontal_accel_g)
    span_mm = span * 1000.0
    moment = q_design * span_mm**2 / 10.0
    stress = moment / pipe.section_modulus_mm3
    allow = job.rule_set.allowable_bending_mpa(pipe.material["yield_strength_mpa"])
    sag = 5.0 * q * span_mm**4 / (384.0 * e_mpa * pipe.inertia_mm4)

    f_target = (1.0 + job.frequency_margin) * max(f for _, f in exc)
    spans = {
        "stress": math.sqrt(10.0 * pipe.section_modulus_mm3 * allow / q_design) / 1000.0,
        "sag": (SAG_LIMIT_MM * 384.0 * e_mpa * pipe.inertia_mm4 / (5.0 * q)) ** 0.25 / 1000.0,
        "frequency": ((math.pi / 2.0) ** 2 * ei_nm2 / (mass * f_target**2)) ** 0.25,
    }
    recommended = math.floor(min(spans.values()) * 10.0) / 10.0
    steps = (
        Step("Pipe bending stiffness", "EI", "EI = E π/64 (D^4 − d^4)",
             f"EI = {num(e_mpa, 0)} MPa × {num(pipe.inertia_mm4, 0)} mm⁴", ei_nm2, "N·m²"),
        Step("Natural frequency of one span", "f_n", "f_n = (π/2) √(EI / (m S^4))",
             f"f_n = (π/2) × √({num(ei_nm2, 0)} / ({num(mass)} × {num(span, 2)}⁴))", natural, "Hz",
             note="Simply supported span: the lowest, safest estimate."),
        Step("Nearest excitation", "f_e", nearest[0], f"f_e = {num(nearest[1])} Hz", nearest[1], "Hz"),
        Step("Separation", "Δ", "Δ = |f_n − f_e| / f_e", f"Δ = |{num(natural)} − {num(nearest[1])}| / {num(nearest[1])}",
             separation * 100, "%", note=f"Must be at least {num(job.frequency_margin * 100, 0)}%."),
        Step("Pipe bending between supports", "σ_p", "σ_p = q_d S^2 / (10 Z)",
             f"σ_p = {num(q_design, 4)} N/mm × {num(span_mm, 0)}² / (10 × {num(pipe.section_modulus_mm3, 0)})", stress, "MPa",
             note="q_d is the pipe weight with the vertical and horizontal accelerations combined; S²/10 for a continuous pipe."),
        Step("Sag under its own weight", "δ_p", "δ_p = 5 q S^4 / (384 E I)",
             f"δ_p = 5 × {num(q, 4)} × {num(span_mm, 0)}⁴ / (384 × {num(e_mpa, 0)} × {num(pipe.inertia_mm4, 0)})", sag, "mm"),
        Step("Longest spacing", "S_{max}", "smallest of the stress, sag and frequency limits",
             f"stress {num(spans['stress'], 2)} m, sag {num(spans['sag'], 2)} m, frequency {num(spans['frequency'], 2)} m", recommended, "m",
             note=f"The frequency limit keeps f_n {num(job.frequency_margin * 100, 0)}% above the highest excitation ({num(max(f for _, f in exc))} Hz)."),
    )
    return SpanResult(natural, exc, nearest, separation, stress, allow, sag, spans, recommended, steps)
