"""Stabilizer fin job and its loads.

The fin is a rectangular NACA 00xx foil of span b and chord c, turning on a
stock at a fraction of the chord from the leading edge. The hull acts as a
reflection plane at the root, so the effective aspect ratio is 2 b / c.

Lift at the largest fin angle comes from two independent methods and the
larger is used for the structure:

* NEMO's foil model: Whicker and Fehlner's low-aspect-ratio lift
  (``nemo.hydro``), L = 1/2 rho V^2 A C_L;
* IACS UR S10's empirical rudder force C_R = K1 K2 K3 132 A V^2.

The force acts at mid-span (uniform loading, which is on the safe side of the
elliptic 0.42 b) and at a third of the chord from the leading edge (UR S10's
a = 0.33 for the ahead condition), which sets the twisting moment on the stock.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field

from ...data import get_material
from ...hydro import KNOT, SEA_WATER_DENSITY, cavitation_number, pressure_peak, whicker_fehlner
from ...rules import IACSS10, get_rule_set
from ...rules.iacs_s10 import BEARING_MATERIALS
from ...working import Step, num

CENTRE_OF_PRESSURE_CHORD = 0.33  # UR S10 a, ahead condition
CENTRE_OF_PRESSURE_SPAN = 0.50


@dataclass(frozen=True)
class FinJob:
    speed_kn: float = 18.0
    span_m: float = 1.4
    chord_m: float = 1.2
    thickness_ratio: float = 0.20
    max_angle_deg: float = 22.0
    stock_position: float = 0.35
    depth_m: float = 3.0
    draught_m: float = 5.0
    bearing_gap_mm: float = 200.0
    material_id: str = "AH36"
    stock_material_id: str = "42CRMO4_QT"
    plate_thicknesses_mm: tuple[float, ...] = (8.0, 10.0, 12.0, 15.0, 20.0, 25.0)
    front_spar: float = 0.15
    rear_spar: float = 0.65
    deflection_limit_mm: float = 10.0
    rule_set_id: str = "iacs-ur-s10"
    # Advanced settings. The defaults keep a simple job simple: the astern case needs no input (UR S10's least
    # astern speed is half the ahead speed), and the bearing check stays off until the bearings are known.
    include_astern: bool = True
    astern_speed_kn: float = 0.0  # 0 = use UR S10's minimum, half the ahead speed
    check_bearings: bool = False
    bearing_spacing_mm: float = 800.0  # outer to inner stock bearing
    bearing_material: str = "synthetic"

    @property
    def material(self):
        return get_material(self.material_id)

    @property
    def stock_material(self):
        return get_material(self.stock_material_id)

    @property
    def rule_set(self) -> IACSS10:
        return get_rule_set(self.rule_set_id)

    @property
    def area_m2(self) -> float:
        return self.span_m * self.chord_m

    @property
    def effective_aspect_ratio(self) -> float:
        return 2.0 * self.span_m / self.chord_m

    def problems(self) -> list[str]:
        p: list[str] = []
        try:
            self.material, self.stock_material  # noqa: B018
        except KeyError as exc:
            return [str(exc).strip("'")]
        if not (3.0 <= self.speed_kn <= 40.0):
            p.append("Ship speed must be between 3 and 40 knots.")
        if not (0.3 <= self.span_m <= 6.0) or not (0.3 <= self.chord_m <= 5.0):
            p.append("Fin span and chord must be between 0.3 m and 6 m.")
        elif not (0.5 <= self.span_m / self.chord_m <= 3.0):
            p.append("The span should be between half and three times the chord for this load model.")
        if not (0.10 <= self.thickness_ratio <= 0.25):
            p.append("Foil thickness must be between 10% and 25% of the chord.")
        if not (5.0 <= self.max_angle_deg <= 30.0):
            p.append("The largest fin angle must be between 5° and 30°.")
        if not (0.15 <= self.stock_position <= 0.5):
            p.append("The stock should be between 15% and 50% of the chord from the leading edge.")
        if not (self.front_spar < self.stock_position < self.rear_spar):
            p.append("The stock must pass between the front and rear spars.")
        if self.depth_m <= 0 or self.draught_m <= 0:
            p.append("Depth and draught must be greater than 0 m.")
        if not (50.0 <= self.bearing_gap_mm <= 2000.0):
            p.append("The distance from the fin root to the outer bearing must be between 50 mm and 2000 mm.")
        if not self.plate_thicknesses_mm:
            p.append("Tick at least one plate thickness your workshop has.")
        if not (1.0 <= self.deflection_limit_mm <= 100.0):
            p.append("The tip deflection limit must be between 1 mm and 100 mm.")
        if self.include_astern and not (0.0 <= self.astern_speed_kn <= self.speed_kn):
            p.append("The astern speed must be between 0 (use the rule minimum) and the ahead speed.")
        if self.check_bearings:
            if not (100.0 <= self.bearing_spacing_mm <= 5000.0):
                p.append("The distance between the two stock bearings must be between 100 mm and 5000 mm.")
            if self.bearing_material not in BEARING_MATERIALS:
                p.append("Choose the stock bearing material.")
        return p

    @property
    def astern_speed_used_kn(self) -> float:
        return max(self.astern_speed_kn, IACSS10.astern_min_speed_fraction * self.speed_kn)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["plate_thicknesses_mm"] = list(self.plate_thicknesses_mm)
        data["part"] = "stabilizer"
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "FinJob":
        kwargs = {}
        for name, value in asdict(cls()).items():
            if data.get(name) is None:
                continue
            raw = data[name]
            kwargs[name] = tuple(float(v) for v in raw) if isinstance(value, tuple) else type(value)(raw)
        return cls(**kwargs)

    @property
    def loads(self) -> "FinLoads":
        return fin_loads(self)


@dataclass(frozen=True)
class FinLoads:
    speed_ms: float
    lift_coefficient: float
    lift_slope_per_rad: float
    nemo_lift_n: float
    ur_s10_force_n: float
    design_force_n: float
    lever_m: float
    torque_nm: float
    root_moment_nm: float
    stock_moment_nm: float
    section_angle_deg: float
    cp_min: float
    cavitation_number: float
    extra: dict = field(default_factory=dict)
    # Astern condition (UR S10.2.1): zero when it is not included.
    astern_speed_kn: float = 0.0
    astern_force_n: float = 0.0
    astern_lever_m: float = 0.0
    astern_torque_nm: float = 0.0
    astern_stock_moment_nm: float = 0.0
    # Stock bearing reactions under the design force, when the bearing check is on.
    outer_bearing_n: float = 0.0
    inner_bearing_n: float = 0.0

    def to_dict(self) -> dict:
        data = {k: v for k, v in asdict(self).items() if k != "extra"}
        data.update(self.extra)
        data["sling_force_n"] = self.design_force_n
        data["sling_force_t"] = self.design_force_n / 9.80665 / 1000.0
        return data


def fin_loads(job: FinJob) -> FinLoads:
    issues = job.problems()
    if issues:
        raise ValueError(" ".join(issues))
    v = job.speed_kn * KNOT
    area = job.area_m2
    cl, slope = whicker_fehlner(job.effective_aspect_ratio, job.max_angle_deg)
    lift = 0.5 * SEA_WATER_DENSITY * v**2 * area * cl
    cr = IACSS10.rudder_force_n(area, job.speed_kn, job.span_m**2 / area)
    force = max(lift, cr)
    lever = max(job.chord_m * abs(CENTRE_OF_PRESSURE_CHORD - job.stock_position), 0.1 * job.chord_m)
    torque = force * lever
    arm = CENTRE_OF_PRESSURE_SPAN * job.span_m
    alpha_2d, cp_min = pressure_peak(job.thickness_ratio, cl)
    lever_bearing = arm + job.bearing_gap_mm / 1000.0
    astern = {}
    if job.include_astern:
        v_ast = job.astern_speed_used_kn
        cr_ast = IACSS10.rudder_force_n(area, v_ast, job.span_m**2 / area, k2=IACSS10.k2_naca_astern, astern=True)
        lever_ast = job.chord_m * abs(IACSS10.astern_lever_fraction - job.stock_position)
        astern = {"astern_speed_kn": v_ast, "astern_force_n": cr_ast, "astern_lever_m": lever_ast,
                  "astern_torque_nm": cr_ast * lever_ast, "astern_stock_moment_nm": cr_ast * lever_bearing}
    bearings = {}
    if job.check_bearings:
        spacing = job.bearing_spacing_mm / 1000.0
        bearings = {"outer_bearing_n": force * (lever_bearing + spacing) / spacing,
                    "inner_bearing_n": force * lever_bearing / spacing}
    return FinLoads(
        speed_ms=v, lift_coefficient=cl, lift_slope_per_rad=slope, nemo_lift_n=lift, ur_s10_force_n=cr,
        design_force_n=force, lever_m=lever, torque_nm=torque, root_moment_nm=force * arm,
        stock_moment_nm=force * (arm + job.bearing_gap_mm / 1000.0), section_angle_deg=alpha_2d, cp_min=cp_min,
        cavitation_number=cavitation_number(job.depth_m, v),
        extra={"area_m2": area, "effective_aspect_ratio": job.effective_aspect_ratio, "span_arm_m": arm},
        **astern, **bearings,
    )


def load_steps(job: FinJob, loads: FinLoads) -> list[Step]:
    a = job.effective_aspect_ratio
    k1 = (min(job.span_m**2 / job.area_m2, 2.0) + 2.0) / 3.0
    return [
        Step("Ship speed", "V", "V = v_{kn} × 0.5144", f"V = {num(job.speed_kn, 1)} kn × 0.5144", loads.speed_ms, "m/s"),
        Step("Effective aspect ratio", "A_e", "A_e = 2 b / c (hull as a mirror)", f"A_e = 2 × {num(job.span_m, 2)} / {num(job.chord_m, 2)}", a, ""),
        Step("Lift slope", "dC_L/dα", "0.9 · 2π A_e / (√(A_e^2 + 4) + 1.8)",
             f"0.9 × 2π × {num(a)} / (√({num(a)}² + 4) + 1.8)", loads.lift_slope_per_rad, "per rad",
             note="Whicker and Fehlner (1958), low-aspect-ratio control surfaces, no sweep."),
        Step("Lift coefficient at the largest angle", "C_L", "C_L = (dC_L/dα) α + (C_{Dc} / A_e) α^2",
             f"C_L = {num(loads.lift_slope_per_rad)} × {num(math.radians(job.max_angle_deg))} + (0.8 / {num(a)}) × {num(math.radians(job.max_angle_deg))}²",
             loads.lift_coefficient, "", note="The second term is cross-flow lift, which matters at low aspect ratio."),
        Step("Lift, NEMO's foil model", "L", "L = ½ ρ V^2 A C_L",
             f"L = 0.5 × 1025 × {num(loads.speed_ms)}² × {num(job.area_m2)} × {num(loads.lift_coefficient)}", loads.nemo_lift_n / 1000, "kN"),
        Step("Rudder force, IACS UR S10", "C_R", "C_R = K_1 K_2 K_3 132 A V^2",
             f"C_R = {num(k1)} × 1.10 × 0.8 × 132 × {num(job.area_m2)} × {num(max(job.speed_kn, (job.speed_kn + 20) / 3), 1)}²",
             loads.ur_s10_force_n / 1000, "kN", note="K_2 = 1.10 for NACA sections, K_3 = 0.8 outside the propeller jet."),
        Step("Design force", "F", "F = max(L, C_R)", f"F = max({num(loads.nemo_lift_n, 0)}, {num(loads.ur_s10_force_n, 0)}) N",
             loads.design_force_n / 1000, "kN"),
        Step("Twisting moment on the stock", "Q", "Q = F c |0.33 − x_s/c|, at least 0.1 F c",
             f"Q = {num(loads.design_force_n, 0)} × {num(loads.lever_m, 3)} m", loads.torque_nm / 1000, "kN·m"),
        Step("Bending at the fin root", "M_r", "M_r = F × 0.5 b", f"M_r = {num(loads.design_force_n, 0)} × {num(0.5 * job.span_m, 3)} m",
             loads.root_moment_nm / 1000, "kN·m"),
        Step("Bending at the outer bearing", "M_s", "M_s = F (0.5 b + l_g)",
             f"M_s = {num(loads.design_force_n, 0)} × ({num(0.5 * job.span_m, 3)} + {num(job.bearing_gap_mm / 1000, 3)}) m",
             loads.stock_moment_nm / 1000, "kN·m"),
    ] + _astern_steps(job, loads) + _bearing_steps(job, loads)


def _astern_steps(job: FinJob, loads: FinLoads) -> list[Step]:
    if not job.include_astern:
        return []
    k1 = (min(job.span_m**2 / job.area_m2, 2.0) + 2.0) / 3.0
    return [
        Step("Astern speed", "V_a", "V_a = max(astern speed, 0.5 V)",
             f"V_a = max({num(job.astern_speed_kn, 1)}, 0.5 × {num(job.speed_kn, 1)}) kn", loads.astern_speed_kn, "kn",
             note="UR S10.2.1.1: the astern speed is not to be taken less than half the ahead speed."),
        Step("Rudder force astern, IACS UR S10", "C_{Ra}", "C_{Ra} = K_1 K_2 K_3 132 A V_a^2",
             f"C_{{Ra}} = {num(k1)} × 0.80 × 0.8 × 132 × {num(job.area_m2)} × {num(loads.astern_speed_kn, 1)}²",
             loads.astern_force_n / 1000, "kN", note="K_2 = 0.80 for NACA sections astern (UR S10 Table 1)."),
        Step("Twisting moment astern", "Q_a", "Q_a = C_{Ra} c |0.66 − x_s/c|",
             f"Q_a = {num(loads.astern_force_n, 0)} × {num(loads.astern_lever_m, 3)} m", loads.astern_torque_nm / 1000, "kN·m",
             note="Going astern the centre of pressure moves aft, to 0.66 of the chord (UR S10.2.1.2)."),
        Step("Bending at the outer bearing astern", "M_{sa}", "M_{sa} = C_{Ra} (0.5 b + l_g)",
             f"M_{{sa}} = {num(loads.astern_force_n, 0)} × {num(0.5 * job.span_m + job.bearing_gap_mm / 1000, 3)} m",
             loads.astern_stock_moment_nm / 1000, "kN·m"),
    ]


def _bearing_steps(job: FinJob, loads: FinLoads) -> list[Step]:
    if not job.check_bearings:
        return []
    a = 0.5 * job.span_m + job.bearing_gap_mm / 1000.0
    l = job.bearing_spacing_mm / 1000.0
    return [
        Step("Outer bearing reaction", "P_1", "P_1 = F (a + l) / l", f"P_1 = {num(loads.design_force_n, 0)} × ({num(a, 3)} + {num(l, 3)}) / {num(l, 3)}",
             loads.outer_bearing_n / 1000, "kN", note="a: outer bearing to the fin force; l: between the two stock bearings."),
        Step("Inner bearing reaction", "P_2", "P_2 = F a / l", f"P_2 = {num(loads.design_force_n, 0)} × {num(a, 3)} / {num(l, 3)}",
             loads.inner_bearing_n / 1000, "kN"),
    ]
