"""Pipe support bracket checks (AISC 360-16 ASD, with the pipe span checks).

The arm is a beam cantilevered from the bulkhead: the seat plate is its top
flange and the two knees its webs. Because the knees taper to the tip, the
most stressed section is not always at the bulkhead, so the arm is checked at
60 stations between the bulkhead and the pipe and the worst one is reported.

``working=True`` adds the hand-calculation steps. The sizing search checks
thousands of designs and leaves them out.
"""

from __future__ import annotations

import math
from dataclasses import replace

from ...checks import CheckResult, PartCheckReport
from ...data import piping
from ...loads import STANDARD_GRAVITY
from ...working import Step, num
from ..padeye.checks import minimum_fillet_size_mm
from .geometry import BracketDesign
from .job import BracketJob, BracketLoads, SpanResult

STATIONS = 60
KNEE_EDGE_RATIO = 50.0  # free edge of an unflanged knee, in thicknesses, for 235 MPa steel


def ubolt_for(diameter_mm: float) -> dict:
    return next(u for u in piping()["ubolts"]["sizes"] if abs(u["diameter_mm"] - diameter_mm) < 1e-6)


def arm_forces(design: BracketDesign, loads: BracketLoads, x: float, zc: float) -> tuple[float, float, float]:
    """Bending moments (N mm) about y and z, and axial force (N), at x from the bulkhead."""
    arm = max(design.pipe_offset_mm - x, 0.0)
    rise = design.pipe_od_mm / 2.0 - zc  # pipe centre above the section's neutral axis
    my = loads.down_n * arm + loads.across_n * rise
    mz = loads.along_n * arm
    return my, mz, loads.across_n


def check_bracket(design: BracketDesign, job: BracketJob, loads: BracketLoads, span: SpanResult, *,
                  working: bool = False) -> PartCheckReport:
    issues = design.problems()
    if issues:
        raise ValueError(" ".join(issues))
    rs = job.rule_set
    mat = job.material
    ts, tk, b, e = design.seat_thickness_mm, design.knee_thickness_mm, design.seat_width_mm, design.pipe_offset_mm
    fy = min(mat.yield_strength_mpa(ts), mat.yield_strength_mpa(tk))
    e_mod = mat.elastic_modulus_mpa
    g_mod = e_mod / (2.0 * (1.0 + mat.poisson_ratio))
    ft, fb, fv = rs.allowable_tension_mpa(fy), rs.allowable_bending_mpa(fy), rs.allowable_shear_mpa(fy)
    fw = rs.allowable_weld_shear_mpa(job.electrode_strength_mpa)
    src = rs.name
    checks: list[CheckResult] = []
    steps: dict[str, list[Step]] = {}

    # --------------------------------------------------- arm, station by station
    worst = None
    v = max(loads.down_n, loads.up_n)
    worst_shear = None
    deflection = 0.0
    dx = e / STATIONS
    for i in range(STATIONS + 1):
        x = i * dx
        sec = design.section_at(x)
        my, mz, n = arm_forces(design, loads, x, sec.centroid_z_mm)
        u = n / sec.area_mm2 / ft + my / sec.s_min_mm3 / fb + mz / sec.s_side_mm3 / fb
        if worst is None or u > worst[0]:
            worst = (u, sec, my, mz, n)
        tau = v / sec.shear_area_mm2
        if worst_shear is None or tau > worst_shear[0]:
            worst_shear = (tau, sec)
        weight = 1.0 if i in (0, STATIONS) else (4.0 if i % 2 else 2.0)
        arm = e - x
        deflection += weight * (loads.down_n * arm**2 / (e_mod * sec.inertia_y_mm4) + loads.down_n / (g_mod * sec.shear_area_mm2))
    deflection *= dx / 3.0

    u, sec, my, mz, n = worst
    checks.append(CheckResult(
        id="arm_bending", title="Bending along the bracket arm", demand=u, capacity=1.0, unit="ratio",
        source=f"{src}: combined axial force and flexure (Chapter H)",
        explanation=("The pipe pushes down at the end of a short beam. The seat plate and the two knees act together "
                     "as that beam. NEMO checks 60 sections between the bulkhead and the pipe; the tapering knees "
                     "mean the worst one is not always at the bulkhead."),
        details={"station_mm": sec.x_mm, "axial_mpa": n / sec.area_mm2, "bending_mpa": my / sec.s_min_mm3,
                 "side_bending_mpa": mz / sec.s_side_mm3},
    ))
    tau, ssec = worst_shear
    checks.append(CheckResult(
        id="arm_shear", title="Shear in the arm", demand=tau, capacity=fv, unit="MPa",
        source=f"{src}: shear yield of plate webs (Chapter G)",
        explanation="The vertical force passes back to the bulkhead as shear through the knees and the seat.",
        details={"station_mm": ssec.x_mm},
    ))

    # ------------------------------------------------------ welds to the bulkhead
    root = design.section_at(0.0)
    a = 0.7071 * design.root_weld_mm
    h = design.knee_depth_mm
    lines = [(b, 0.0, False), (b, -ts, False)] + [(h, -ts - h / 2.0, True)] * 4  # (length, centre z, vertical)
    aw = a * sum(length for length, _, _ in lines)
    zw = sum(a * length * z for length, z, _ in lines) / aw
    iw = sum(a * (length**3 / 12.0 if vertical else 0.0) + a * length * (z - zw) ** 2 for length, z, vertical in lines)
    iwz = 2.0 * a * b**3 / 12.0 + 4.0 * a * h * (b / 2.0) ** 2
    my0, mz0, n0 = arm_forces(design, loads, 0.0, zw)
    c_w = max(-zw, zw + ts + h)
    fn = n0 / aw + my0 * c_w / iw + mz0 * (b / 2.0) / iwz
    fs = math.hypot(v, loads.along_n) / aw
    f_root = math.hypot(fn, fs)
    checks.append(CheckResult(
        id="root_weld", title="Welds to the bulkhead", demand=f_root, capacity=fw, unit="MPa",
        source=f"{src}: fillet welds, J2.4 (elastic method)",
        explanation=("Fillet welds on both sides of the seat and of each knee hold the bracket to the bulkhead. The "
                     "bending and the forces are shared over the whole weld group and combined on the throat."),
        details={"normal_mpa": fn, "shear_mpa": fs, "throat_mm": a},
    ))

    # ---------------------------------------------------------- knee to seat welds
    ak = 0.7071 * design.knee_weld_mm
    flow = v * abs(root.flange_first_moment_mm3) / root.inertia_y_mm4
    f_knee = flow / (4.0 * ak)
    checks.append(CheckResult(
        id="knee_weld", title="Knee-to-seat welds", demand=f_knee, capacity=fw, unit="MPa",
        source=f"{src}: fillet welds, J2.4 (shear flow VQ/I)",
        explanation="The welds between the knees and the seat make them work as one beam. They carry the shear flow.",
        details={"shear_flow_n_per_mm": flow},
    ))

    # ---------------------------------------------------------------- seat plate
    ub = ubolt_for(design.ubolt_diameter_mm)
    tension = loads.up_n / 2.0 + loads.across_n * (design.pipe_od_mm / 2.0) / design.leg_spacing_mm
    span_seat = design.knee_span_mm
    w_eff = min(design.seat_length_mm, span_seat)
    m_seat = max(loads.down_n * span_seat / 8.0, tension * span_seat / 4.0)
    f_seat = m_seat / (w_eff * ts**2 / 6.0)
    fb_plate = rs.allowable_bending_mpa(fy, shape_factor=1.5)
    checks.append(CheckResult(
        id="seat_bending", title="Seat plate between the knees", demand=f_seat, capacity=fb_plate, unit="MPa",
        source=f"{src}: flexure of plates about their weak axis (F11)",
        explanation=("Between the two knees the seat plate spans like a small beam, carrying the pipe resting on it or "
                     "the pull of a U-bolt leg."),
        details={"moment_nmm": m_seat, "effective_width_mm": w_eff},
    ))

    # -------------------------------------------------------------------- U-bolt
    grade = job.ubolt_grade
    shear = loads.across_n / 2.0
    f_t, f_v = tension / ub["tensile_area_mm2"], shear / ub["tensile_area_mm2"]
    ft_b = rs.allowable_bolt_tension_mpa(grade["tensile_strength_mpa"])
    fv_b = 0.45 * grade["tensile_strength_mpa"] / rs.omega_bolt
    interaction = (f_t / ft_b) ** 2 + (f_v / fv_b) ** 2
    checks.append(CheckResult(
        id="ubolt", title="U-bolt legs", demand=interaction, capacity=1.0, unit="ratio",
        source=f"{src}: bolts in tension and shear, J3.6 and J3.7 (elliptical interaction)",
        explanation=("The U-bolt stops the pipe sliding off sideways and lifting. Each leg is pulled and sheared; the "
                     "two effects are combined."),
        details={"tension_n": tension, "shear_n": shear, "thread": ub["thread"]},
    ))

    # ----------------------------------------------------------------- stiffness
    checks.append(CheckResult(
        id="deflection", title="Bracket deflection under the pipe", demand=deflection,
        capacity=job.deflection_limit_mm, unit="mm", source="Design limit set for this job", basis="practice",
        category="stiffness",
        explanation="A bracket that bends too much lets the pipe sag and vibrate. This is the drop at the pipe under the design load.",
    ))

    # ------------------------------------------------------------------ advice
    edge_limit = KNEE_EDGE_RATIO * tk * math.sqrt(235.0 / fy)
    checks.append(CheckResult(
        id="knee_edge", title="Knee free edge", demand=design.knee_free_edge_mm, capacity=edge_limit, unit="mm",
        source="NEMO practice, after ship-structure bracket rules (unflanged free edge up to 50 t √(235/F_y))",
        basis="practice", category="fit", severity="advice",
        explanation="A long, thin free edge on a knee can buckle. Past this length, flange the edge or fit a face bar.",
    ))
    thick = max(ts, tk)
    checks.append(CheckResult(
        id="root_weld_size", title="Bulkhead weld size", demand=minimum_fillet_size_mm(thick), capacity=design.root_weld_mm,
        unit="mm", source="AWS D1.1 minimum fillet weld size", basis="practice", category="fit", severity="advice",
        explanation="Very small welds on thick plate cool too fast and can crack.",
    ))
    checks.append(CheckResult(
        id="knee_weld_size", title="Knee weld size", demand=minimum_fillet_size_mm(thick), capacity=design.knee_weld_mm,
        unit="mm", source="AWS D1.1 minimum fillet weld size", basis="practice", category="fit", severity="advice",
        explanation="Very small welds on thick plate cool too fast and can crack.",
    ))

    # -------------------------------------------------------------- pipe span
    checks += _span_checks(job, span)
    flex = _support_vibration(job, loads, span, deflection) if job.include_bracket_flexibility else None
    if flex:
        checks.append(flex[0])

    values = {"yield_mpa": fy, "allow_tension_mpa": ft, "allow_bending_mpa": fb, "allow_shear_mpa": fv,
              "allow_weld_mpa": fw, "deflection_mm": deflection, "governing_station_mm": sec.x_mm,
              "governing_stress_mpa": n / sec.area_mm2 + my / sec.s_min_mm3 + mz / sec.s_side_mm3,
              "root_inertia_mm4": root.inertia_y_mm4, "ubolt_tension_n": tension}
    report = PartCheckReport(
        design=design, material=mat, loads=loads, rule_set=rs, checks=tuple(checks),
        mass_kg=design.steel_mass_kg(mat), values=values,
        extra={"pipe": {"label": job.pipe.label, "od_mm": job.pipe.od_mm, "wall_mm": job.pipe.wall_mm,
                        "material": job.pipe.material["name"]},
               "ubolt": {"label": f"{ub['thread']} U-bolt, {grade['name']}", "thread": ub["thread"],
                         "diameter_mm": ub["diameter_mm"]},
               "span": span.to_dict()},
    )
    if not working:
        return report
    report = _with_working(report, job, loads, span, worst, worst_shear, (lines, a, aw, zw, iw, iwz, c_w, fn, fs, my0, mz0),
                           (flow, ak), (tension, span_seat, w_eff, m_seat, fb_plate), (ub, f_t, f_v, ft_b, fv_b, shear), deflection)
    if flex:
        report = replace(report, checks=tuple(replace(c, working=flex[1]) if c.id == "support_vibration" else c
                                              for c in report.checks))
    return report


def _support_vibration(job: BracketJob, loads: BracketLoads, span: SpanResult, deflection_mm: float):
    """The pipe span on flexible brackets: Dunkerley's combination of the span and bracket frequencies.

    The span frequency assumes rigid supports. The bracket is a spring under the pipe's share of the span, with
    its own frequency f_b = (1/2 pi) sqrt(k / m), k = F_z / delta and m = W / g. Dunkerley's lower bound
    1/f^2 = 1/f_n^2 + 1/f_b^2 then gives the frequency of the pipe on its brackets (Blevins, Formulas for
    Natural Frequency and Mode Shape). It must keep the same margin from every excitation.
    """
    if deflection_mm <= 0 or loads.static_n <= 0:
        return None
    k_n_per_m = loads.down_n / deflection_mm * 1000.0
    mass_kg = loads.static_n / STANDARD_GRAVITY
    f_bracket = math.sqrt(k_n_per_m / mass_kg) / (2.0 * math.pi)
    f_n = span.natural_hz
    f_c = 1.0 / math.sqrt(1.0 / f_n**2 + 1.0 / f_bracket**2)
    nearest = min(span.excitations, key=lambda e: abs(f_c - e[1]) / e[1])
    separation = abs(f_c - nearest[1]) / nearest[1]
    # When the span already fails on rigid supports, a stiffer bracket cannot fix it: leave it out of the sizing.
    category = "stiffness" if span.separation >= job.frequency_margin else "span"
    check = CheckResult(
        id="support_vibration", title="Pipe on its brackets clear of vibration", demand=job.frequency_margin,
        capacity=separation, unit="ratio", basis="practice", category=category,
        source=(f"NEMO practice: Dunkerley's combination of the pipe span and bracket frequencies, at least "
                f"{job.frequency_margin * 100:.0f}% from every excitation"),
        explanation=(f"The span check assumes the brackets do not move. A bracket bends a little under the pipe, which "
                     f"lowers the frequency of the whole run from {f_n:.1f} Hz to {f_c:.1f} Hz. Nearest excitation: "
                     f"{nearest[0].lower()}, {nearest[1]:.1f} Hz."),
        details={"bracket_hz": f_bracket, "combined_hz": f_c, "stiffness_n_per_mm": k_n_per_m / 1000.0},
    )
    steps = (
        Step("Bracket stiffness under the pipe", "k", "k = F_z / δ", f"k = {num(loads.down_n, 0)} N / {num(deflection_mm, 4)} mm",
             k_n_per_m / 1e6, "kN/mm"),
        Step("Pipe mass on one bracket", "m", "m = W / g", f"m = {num(loads.static_n, 0)} N / 9.807", mass_kg, "kg"),
        Step("Bracket frequency", "f_b", "f_b = (1 / 2π) √(k / m)", f"f_b = √({num(k_n_per_m, 0)} / {num(mass_kg, 1)}) / 2π", f_bracket, "Hz"),
        Step("Pipe span on rigid supports", "f_n", "from the span check", f"f_n = {num(f_n)} Hz", f_n, "Hz"),
        Step("Pipe on its brackets", "f", "1/f^2 = 1/f_n^2 + 1/f_b^2", f"f = 1 / √(1/{num(f_n)}² + 1/{num(f_bracket)}²)", f_c, "Hz",
             note="Dunkerley's method. It errs low, so it is on the safe side for frequencies above the excitations."),
        Step("Separation", "Δ", "Δ = |f − f_e| / f_e", f"Δ = |{num(f_c)} − {num(nearest[1])}| / {num(nearest[1])}", separation * 100, "%",
             note=f"Must be at least {num(job.frequency_margin * 100, 0)}%."),
    )
    return check, steps


def _span_checks(job: BracketJob, span: SpanResult) -> list[CheckResult]:
    exc = ", ".join(f"{name.lower()} {f:.1f} Hz" for name, f in span.excitations)
    return [
        CheckResult(
            id="pipe_vibration", title="Pipe span clear of vibration", demand=job.frequency_margin,
            capacity=span.separation, unit="ratio", basis="practice", category="span",
            source=f"NEMO practice: natural frequency at least {job.frequency_margin * 100:.0f}% from every excitation",
            explanation=(f"The pipe between two supports has a natural frequency of {span.natural_hz:.1f} Hz. If it is "
                         f"close to a frequency the propeller or engine shakes the ship at ({exc}), the pipe "
                         "resonates and its welds and supports crack. Change the support spacing to move it."),
        ),
        CheckResult(
            id="pipe_stress", title="Pipe bending between supports", demand=span.pipe_stress_mpa,
            capacity=span.pipe_allow_mpa, unit="MPa", basis="practice", category="span",
            source=f"{job.rule_set.name}: flexure, applied to the pipe as a continuous beam",
            explanation="The pipe itself bends between supports under its weight and the ship's motion.",
        ),
        CheckResult(
            id="pipe_sag", title="Pipe sag between supports", demand=span.sag_mm, capacity=2.5, unit="mm",
            basis="practice", category="span", severity="advice",
            source="MSS SP-58 / SP-69 style span guidance (2.5 mm sag)",
            explanation="Too much sag lets liquid collect at low points and makes the pipe look and act loose.",
        ),
        CheckResult(
            id="span_limit", title="Support spacing within NEMO's recommended maximum", demand=job.span_m,
            capacity=span.recommended_m, unit="m", basis="practice", category="span", severity="advice",
            source="NEMO: smallest of the stress, sag and frequency limits",
            explanation=(f"The longest spacing that keeps this pipe within the stress and sag limits and its natural "
                         f"frequency above every excitation is {span.recommended_m:.1f} m. A longer spacing can still be "
                         "acceptable when the frequency sits in a gap between excitations; the vibration check above "
                         "decides that."),
        ),
    ]


def _with_working(report, job, loads, span, worst, worst_shear, weld, knee, seat, bolt, deflection) -> PartCheckReport:
    from dataclasses import replace

    d = report.design
    v = report.values
    fy = v["yield_mpa"]
    rs = report.rule_set
    u, sec, my, mz, n = worst
    om = rs.omega_flexure
    steps: dict[str, list[Step]] = {}
    steps["arm_bending"] = [
        Step("Section checked", "x", "worst of 60 sections from the bulkhead to the pipe",
             f"x = {num(sec.x_mm, 0)} mm, knee depth {num(sec.knee_depth_mm, 0)} mm", sec.x_mm, "mm"),
        Step("Second moment of area", "I_y", "I_y = Σ (b t^3/12 + A d^2), seat plus two knees",
             f"seat {num(d.seat_width_mm, 0)} × {num(d.seat_thickness_mm, 0)}, knees 2 × {num(d.knee_thickness_mm, 0)} × {num(sec.knee_depth_mm, 0)}",
             sec.inertia_y_mm4, "mm⁴"),
        Step("Bending moment", "M_y", "M_y = F_z (e − x) + F_x (D/2 − z̄)",
             f"M_y = {num(loads.down_n, 0)} × {num(d.pipe_offset_mm - sec.x_mm, 0)} + {num(loads.across_n, 0)} × {num(d.pipe_od_mm / 2 - sec.centroid_z_mm, 0)}",
             my / 1e6, "kN·m"),
        Step("Bending stress", "f_b", "f_b = M_y / S_{min}", f"f_b = {num(my, 0)} / {num(sec.s_min_mm3, 0)}", my / sec.s_min_mm3, "MPa"),
        Step("Sideways bending stress", "f_{bz}", "f_{bz} = F_y (e − x) / S_z", f"f_{{bz}} = {num(mz, 0)} / {num(sec.s_side_mm3, 0)}", mz / sec.s_side_mm3, "MPa"),
        Step("Axial stress", "f_a", "f_a = F_x / A", f"f_a = {num(n, 0)} / {num(sec.area_mm2, 0)}", n / sec.area_mm2, "MPa"),
        Step("Allowed bending", "F_b", "F_b = F_y / Ω_b", f"F_b = {num(fy, 0)} / {num(om, 2)}", v["allow_bending_mpa"], "MPa",
             note="First-yield moment, because the knees are not compact plates."),
        Step("Combined use", "U", "U = f_a/F_t + f_b/F_b + f_{bz}/F_b",
             f"U = {num(n / sec.area_mm2)}/{num(v['allow_tension_mpa'])} + {num(my / sec.s_min_mm3)}/{num(v['allow_bending_mpa'])} + {num(mz / sec.s_side_mm3)}/{num(v['allow_bending_mpa'])}",
             u, "", note="Must not exceed 1.0."),
    ]
    tau, ssec = worst_shear
    steps["arm_shear"] = [
        Step("Shear force", "V", "V = max(F_z, F_u)", f"V = {num(max(loads.down_n, loads.up_n), 0)} N", max(loads.down_n, loads.up_n) / 1000, "kN"),
        Step("Shear area", "A_v", "A_v = 2 t_k h(x) + b t_s", f"at x = {num(ssec.x_mm, 0)} mm: 2 × {num(d.knee_thickness_mm, 0)} × {num(ssec.knee_depth_mm, 0)} + {num(d.seat_width_mm, 0)} × {num(d.seat_thickness_mm, 0)}",
             ssec.shear_area_mm2, "mm²"),
        Step("Shear stress", "f_v", "f_v = V / A_v", f"f_v = {num(max(loads.down_n, loads.up_n), 0)} / {num(ssec.shear_area_mm2, 0)}", tau, "MPa"),
        Step("Allowed shear", "F_v", "F_v = 0.6 F_y / Ω_v", f"F_v = 0.6 × {num(fy, 0)} / {num(rs.omega_shear, 2)}", v["allow_shear_mpa"], "MPa"),
    ]
    lines, a, aw, zw, iw, iwz, c_w, fn, fs, my0, mz0 = weld
    fw = v["allow_weld_mpa"]
    weld_allow = Step("Allowed weld stress", "F_w", "F_w = 0.60 F_{EXX} / Ω_w", f"F_w = 0.60 × {num(job.electrode_strength_mpa, 0)} / {num(rs.omega_weld, 2)}", fw, "MPa")
    steps["root_weld"] = [
        Step("Weld throat", "a", "a = 0.707 w", f"a = 0.707 × {num(d.root_weld_mm, 0)}", a, "mm"),
        Step("Weld group area", "A_w", "A_w = a (2 b + 4 h_k)", f"A_w = {num(a)} × (2 × {num(d.seat_width_mm, 0)} + 4 × {num(d.knee_depth_mm, 0)})", aw, "mm²"),
        Step("Weld group second moment", "I_w", "I_w = Σ a L (z − z̄_w)^2 + knee lines a h^3/12", f"neutral axis z̄_w = {num(zw)} mm", iw, "mm⁴"),
        Step("Normal stress on the weld", "f_n", "f_n = F_x/A_w + M_y c/I_w + M_z (b/2)/I_{wz}",
             f"M_y = {num(my0 / 1e6, 3)} kN·m, c = {num(c_w)} mm, M_z = {num(mz0 / 1e6, 4)} kN·m", fn, "MPa"),
        Step("Shear on the weld", "f_s", "f_s = √(V^2 + F_y^2) / A_w", f"f_s = √({num(max(loads.down_n, loads.up_n), 0)}² + {num(loads.along_n, 0)}²) / {num(aw, 0)}", fs, "MPa"),
        Step("Resultant on the throat", "f_w", "f_w = √(f_n^2 + f_s^2)", f"f_w = √({num(fn)}² + {num(fs)}²)", math.hypot(fn, fs), "MPa"),
        weld_allow,
    ]
    flow, ak = knee
    root = d.section_at(0.0)
    steps["knee_weld"] = [
        Step("First moment of the seat", "Q", "Q = b t_s (z_f − z̄)", f"Q = {num(d.seat_width_mm, 0)} × {num(d.seat_thickness_mm, 0)} × {num(abs(-d.seat_thickness_mm / 2 - root.centroid_z_mm))}", abs(root.flange_first_moment_mm3), "mm³"),
        Step("Shear flow", "q", "q = V Q / I_y", f"q = {num(max(loads.down_n, loads.up_n), 0)} × {num(abs(root.flange_first_moment_mm3), 0)} / {num(root.inertia_y_mm4, 0)}", flow, "N/mm"),
        Step("Weld stress", "f_w", "f_w = q / (4 × 0.707 w_k)", f"f_w = {num(flow)} / (4 × {num(ak)})", flow / (4 * ak), "MPa", note="Two knees, welded on both sides."),
        weld_allow,
    ]
    tension, span_seat, w_eff, m_seat, fb_plate = seat
    steps["seat_bending"] = [
        Step("Span between knees", "l", "l = b − t_k", f"l = {num(d.seat_width_mm, 0)} − {num(d.knee_thickness_mm, 0)}", span_seat, "mm"),
        Step("Moment", "M", "M = max(F_z l / 8, T l / 4)", f"max({num(loads.down_n, 0)} × {num(span_seat, 0)} / 8, {num(tension, 0)} × {num(span_seat, 0)} / 4)", m_seat / 1e6, "kN·m"),
        Step("Plate strip resisting", "w", "w = min(L, l)", f"w = min({num(d.seat_length_mm, 0)}, {num(span_seat, 0)})", w_eff, "mm"),
        Step("Bending stress", "f_b", "f_b = 6 M / (w t_s^2)", f"f_b = 6 × {num(m_seat, 0)} / ({num(w_eff, 0)} × {num(d.seat_thickness_mm, 0)}²)", m_seat / (w_eff * d.seat_thickness_mm**2 / 6), "MPa"),
        Step("Allowed", "F_b", "F_b = 1.5 F_y / Ω_b", f"F_b = 1.5 × {num(fy, 0)} / {num(om, 2)}", fb_plate, "MPa", note="Z/S = 1.5 for a plate bent flat."),
    ]
    ub, f_t, f_v, ft_b, fv_b, shear = bolt
    steps["ubolt"] = [
        Step("Tension in one leg", "T", "T = F_u/2 + F_x (D/2) / s", f"T = {num(loads.up_n, 0)}/2 + {num(loads.across_n, 0)} × {num(d.pipe_od_mm / 2)} / {num(d.leg_spacing_mm)}", tension, "N",
             note="s is the distance between the legs."),
        Step("Shear in one leg", "V_b", "V_b = F_x / 2", f"V_b = {num(loads.across_n, 0)} / 2", shear, "N"),
        Step("Stresses on the thread", "f_t, f_v", "f = force / A_s", f"A_s = {num(ub['tensile_area_mm2'], 1)} mm² ({ub['thread']})", f_t, "MPa", note=f"f_v = {num(f_v)} MPa"),
        Step("Allowed", "F_t, F_v", "F_t = 0.75 F_u / Ω, F_v = 0.45 F_u / Ω", f"F_t = {num(ft_b)}, F_v = {num(fv_b)}", ft_b, "MPa"),
        Step("Interaction", "U", "U = (f_t/F_t)^2 + (f_v/F_v)^2", f"U = ({num(f_t)}/{num(ft_b)})² + ({num(f_v)}/{num(fv_b)})²", report.check("ubolt").demand, ""),
    ]
    steps["deflection"] = [
        Step("Drop at the pipe", "δ", "δ = ∫ F_z (e − x)^2 / (E I(x)) dx + ∫ F_z / (G A_v(x)) dx",
             "Simpson's rule over the 60 sections, bending plus shear", deflection, "mm"),
        Step("Limit", "δ_{max}", "set for this job", f"{num(job.deflection_limit_mm, 2)} mm", job.deflection_limit_mm, "mm"),
    ]
    steps["knee_edge"] = [
        Step("Free edge length", "l_e", "l_e = √(L^2 + h_k^2)", f"l_e = √({num(d.seat_length_mm, 0)}² + {num(d.knee_depth_mm, 0)}²)", d.knee_free_edge_mm, "mm"),
        Step("Limit", "l_{max}", "l_{max} = 50 t_k √(235 / F_y)", f"l_{{max}} = 50 × {num(d.knee_thickness_mm, 0)} × √(235 / {num(fy, 0)})", report.check("knee_edge").capacity, "mm"),
    ]
    thick = max(d.seat_thickness_mm, d.knee_thickness_mm)
    for cid, leg in (("root_weld_size", d.root_weld_mm), ("knee_weld_size", d.knee_weld_mm)):
        steps[cid] = [
            Step("Smallest fillet allowed", "w_{min}", "AWS D1.1 table", f"thicker part {num(thick, 0)} mm", report.check(cid).demand, "mm"),
            Step("Weld chosen", "w", "w", f"w = {num(leg, 0)}", leg, "mm"),
        ]
    span_steps = list(span.steps)
    steps["pipe_vibration"] = span_steps[:4]
    steps["pipe_stress"] = [span_steps[4], Step("Allowed", "F_b", "F_b = F_y / Ω_b", f"F_b = {num(job.pipe.material['yield_strength_mpa'], 0)} / {num(om, 2)}", span.pipe_allow_mpa, "MPa")]
    steps["pipe_sag"] = [span_steps[5]]
    steps["span_limit"] = [span_steps[6]]
    checks = tuple(replace(c, working=tuple(steps.get(c.id, ()))) for c in report.checks)
    return replace(report, checks=checks)
