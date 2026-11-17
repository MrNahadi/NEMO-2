"""Stabilizer fin checks: IACS UR S10 for the stock and the fin body, plus buckling, stiffness and cavitation."""

from __future__ import annotations

import math

from ...checks import CheckResult, PartCheckReport
from ...rules import IACSS10
from ...rules.iacs_s10 import BEARING_MATERIALS, BEARING_MAX_LENGTH_RATIO, bearing_clearance_mm
from ...working import Step, num
from .geometry import FinDesign
from .job import FinJob, FinLoads

BUCKLING_FACTOR = 1.5


def stock_stresses(diameter_mm: float, moment_nm: float, torque_nm: float) -> tuple[float, float, float]:
    """UR S10.4.2: sigma_b = 10.2 M / D^3 x 1e3, tau = 5.1 Q / D^3 x 1e3, sigma_e = sqrt(sigma_b^2 + 3 tau^2)."""
    d3 = diameter_mm**3
    sb = 10.2 * moment_nm / d3 * 1e3
    tau = 5.1 * torque_nm / d3 * 1e3
    return sb, tau, math.hypot(sb, math.sqrt(3.0) * tau)


def stock_cases(loads: FinLoads) -> list[tuple[str, float, float, float]]:
    """(condition, force N, bending moment at the outer bearing N m, twisting moment N m): ahead, and astern if included."""
    cases = [("ahead", loads.design_force_n, loads.stock_moment_nm, loads.torque_nm)]
    if loads.astern_force_n > 0:
        cases.append(("astern", loads.astern_force_n, loads.astern_stock_moment_nm, loads.astern_torque_nm))
    return cases


def bearing_lengths(job: FinJob, loads: FinLoads, stock_mm: float) -> list[tuple[str, float, float, float, float]]:
    """(name, reaction N, bearing diameter mm, required length mm, longest allowed mm) for the two stock bearings."""
    if not job.check_bearings:
        return []
    mat = BEARING_MATERIALS[job.bearing_material]
    d_b = stock_mm + 2.0 * mat["liner_mm"]
    out = []
    for name, p in (("outer", loads.outer_bearing_n), ("inner", loads.inner_bearing_n)):
        out.append((name, p, d_b, p / (mat["pressure_mpa"] * d_b), BEARING_MAX_LENGTH_RATIO * d_b))
    return out


def buckling_stress(t_mm: float, width_mm: float, length_mm: float, e_mpa: float, nu: float, fy: float) -> tuple[float, float, float]:
    """Elastic buckling of a plate panel loaded along ``length`` (simply supported edges), with Johnson-Ostenfeld correction."""
    ratio = length_mm / width_mm
    k = min((m / ratio + ratio / m) ** 2 for m in range(1, 8))
    elastic = k * math.pi**2 * e_mpa / (12.0 * (1.0 - nu**2)) * (t_mm / width_mm) ** 2
    critical = elastic if elastic <= fy / 2.0 else fy * (1.0 - fy / (4.0 * elastic))
    return k, elastic, critical


def check_fin(design: FinDesign, job: FinJob, loads: FinLoads) -> PartCheckReport:
    issues = design.problems()
    if issues:
        raise ValueError(" ".join(issues))
    rs = job.rule_set
    plate, stock = job.material, job.stock_material
    fy_p = plate.yield_strength_mpa(max(design.skin_mm, design.web_mm))
    k_p = IACSS10.material_factor(fy_p, plate.tensile_strength_mpa)
    fy_s = stock.yield_strength_mpa(design.stock_diameter_mm)
    k_s = IACSS10.material_factor(fy_s, stock.tensile_strength_mpa)
    sec = design.section()
    f, q = loads.design_force_n, loads.torque_nm
    src = rs.name
    checks: list[CheckResult] = []
    d = design.stock_diameter_mm

    # ---------------------------------------------------------------- stock
    # Ahead, and astern when included (UR S10.2.1). Each check reports the worse condition and shows both.
    results = [(name, force, m, tq, *stock_stresses(d, m, tq)) for name, force, m, tq in stock_cases(loads)]
    worst_t = max(results, key=lambda r: r[5])
    worst_e = max(results, key=lambda r: r[6])
    sb, tau, se = results[0][4], results[0][5], results[0][6]
    both = len(results) > 1
    t_steps = []
    e_steps = []
    for name, force, m, tq, sb_i, tau_i, se_i in results:
        tag = f", {name}" if both else ""
        lever = loads.lever_m if name == "ahead" else loads.astern_lever_m
        t_steps += [Step(f"Twisting moment{tag}", "Q", "Q = F × lever", f"Q = {num(force, 0)} N × {num(lever, 3)} m", tq / 1000, "kN·m"),
                    Step(f"Torsional stress{tag}", "τ_t", "τ_t = 5.1 Q / D^3 × 10^3", f"τ_t = 5.1 × {num(tq, 0)} / {num(d, 0)}³ × 10³", tau_i, "MPa")]
        e_steps += [Step(f"Bending moment at the bearing{tag}", "M", "M = F (0.5 b + l_g)", f"M = {num(force, 0)} N × {num(m / force, 3)} m", m / 1000, "kN·m"),
                    Step(f"Bending stress{tag}", "σ_b", "σ_b = 10.2 M / D^3 × 10^3", f"σ_b = 10.2 × {num(m, 0)} / {num(d, 0)}³ × 10³", sb_i, "MPa"),
                    Step(f"Equivalent stress{tag}", "σ_e", "σ_e = √(σ_b^2 + 3 τ_t^2)", f"σ_e = √({num(sb_i)}² + 3 × {num(tau_i)}²)", se_i, "MPa")]
    if both:
        t_steps.append(Step("Worse condition", "τ_t", "max(ahead, astern)", worst_t[0], worst_t[5], "MPa"))
        e_steps.append(Step("Worse condition", "σ_e", "max(ahead, astern)", worst_e[0], worst_e[6], "MPa"))
    checks.append(CheckResult(
        id="stock_torsion", title="Stock twisting", demand=worst_t[5], capacity=rs.stock_torsion_mpa / k_s, unit="MPa",
        source=f"{src}.4.1: torsional stress in the stock" + (", ahead and astern" if both else ""),
        explanation=("The lift acts behind or ahead of the stock and twists it."
                     + (" Going astern the centre of pressure moves aft, so the twist can be larger at a lower speed." if both else "")),
        details={"condition": worst_t[0]},
        working=(*t_steps,
                 Step("Material factor", "k", "k = (235 / R_{eH})^{0.75}", f"R_{{eH}} = min({num(fy_s, 0)}, 0.7 × {num(stock.tensile_strength_mpa, 0)}, 450)", k_s, ""),
                 Step("Allowed", "τ_{all}", "τ_{all} = 68 / k", f"68 / {num(k_s)}", rs.stock_torsion_mpa / k_s, "MPa")),
    ))
    checks.append(CheckResult(
        id="stock_combined", title="Stock bending and twisting at the outer bearing", demand=worst_e[6],
        capacity=rs.stock_equivalent_mpa / k_s, unit="MPa",
        source=f"{src}.4.2: equivalent stress in the stock" + (", ahead and astern" if both else ""),
        explanation="Where the stock leaves the hull bearing it carries the whole bending moment from the fin as well as the twist.",
        details={"condition": worst_e[0]},
        working=(*e_steps,
                 Step("Allowed", "σ_{all}", "σ_{all} = 118 / k", f"118 / {num(k_s)}", rs.stock_equivalent_mpa / k_s, "MPa")),
    ))
    if job.check_bearings:
        mat = BEARING_MATERIALS[job.bearing_material]
        for name, p, d_b, length, longest in bearing_lengths(job, loads, d):
            clearance = bearing_clearance_mm(d_b, mat["metallic"])
            checks.append(CheckResult(
                id=f"{name}_bearing", title=f"{name.capitalize()} stock bearing length", demand=length, capacity=longest, unit="mm",
                source=f"{src}.8.2 and 8.3: bearing surface P / q_a, length at most {BEARING_MAX_LENGTH_RATIO:g} × diameter",
                category="fit",
                explanation=(f"The {name} bearing must be long enough to keep the surface pressure within the limit for "
                             f"{mat['name'].lower()}, without being longer than {BEARING_MAX_LENGTH_RATIO:g} times its diameter. "
                             f"Fit a bearing at least {length:.0f} mm long."),
                details={"reaction_n": p, "diameter_mm": d_b, "required_length_mm": length, "clearance_mm": clearance},
                working=(Step("Bearing reaction", f"P_{1 if name == 'outer' else 2}", "from the two-bearing support", f"{name} bearing", p / 1000, "kN"),
                         Step("Bearing diameter over the liner", "d_b", "d_b = D + 2 t_{liner}", f"d_b = {num(d, 0)} + 2 × {num(mat['liner_mm'], 0)}", d_b, "mm",
                              note=f"Least liner or bush thickness {num(mat['liner_mm'], 0)} mm (UR S10.8.1)."),
                         Step("Allowable surface pressure", "q_a", "UR S10 Table 3", mat["name"], mat["pressure_mpa"], "MPa"),
                         Step("Least bearing length", "L", "L = P / (q_a d_b)", f"L = {num(p, 0)} / ({num(mat['pressure_mpa'], 1)} × {num(d_b, 0)})", length, "mm"),
                         Step("Longest allowed", "1.2 d_b", "1.2 d_b", f"1.2 × {num(d_b, 0)}", longest, "mm"),
                         Step("Bearing clearance on the diameter, at least", "c", "d_b/1000 + 1 (metal), 1.5 mm (non-metallic)",
                              mat["name"], clearance, "mm", note="UR S10.8.4.")),
            ))
    room = 0.9 * 2.0 * design.half_thickness_at(design.stock_position)
    checks.append(CheckResult(
        id="stock_fit", title="Stock fits inside the foil", demand=d, capacity=room, unit="mm", source="NEMO practice",
        basis="practice", category="fit",
        explanation="The stock and its housing must fit inside the foil at the stock position, with room for the skin.",
        working=(Step("Foil thickness at the stock", "t_s", "t_s = 2 y_t(x_s)", f"x_s = {num(design.stock_position * 100, 0)}% of the chord", 2 * design.half_thickness_at(design.stock_position), "mm"),
                 Step("Largest stock", "0.9 t_s", "0.9 t_s", f"0.9 × {num(2 * design.half_thickness_at(design.stock_position))}", room, "mm")),
    ))

    # ------------------------------------------------------------- fin body
    m_root = loads.root_moment_nm * 1000.0
    s_box = sec.section_modulus_mm3
    sigma = m_root / s_box
    heights = sum(sec.web_heights_mm)
    q_t = q * 1000.0 / (2.0 * sec.box_area_mm2)
    tau_web = f / (design.web_mm * heights) + q_t / design.web_mm
    tau_skin = q_t / design.skin_mm
    equiv = math.hypot(sigma, math.sqrt(3.0) * tau_skin)
    checks.append(CheckResult(
        id="fin_bending", title="Fin body bending at the root", demand=sigma, capacity=rs.blade_bending_mpa / k_p, unit="MPa",
        source=f"{src}.5.1: bending stress in the rudder blade",
        explanation="The fin is a short wing fixed at the hull. Its skin and spars act as a box beam carrying the lift to the root.",
        working=(Step("Root moment", "M_r", "M_r = F × 0.5 b", f"M_r = {num(f, 0)} N × {num(0.5 * design.span_mm, 0)} mm", m_root / 1e6, "kN·m"),
                 Step("Box second moment", "I", "I = 2 ∫ t y^2 ds + t_w (h_f^3 + h_r^3) / 12",
                      f"skin {num(design.skin_mm, 0)} mm between {num(design.front_spar * 100, 0)}% and {num(design.rear_spar * 100, 0)}% chord, webs {num(design.web_mm, 0)} mm", sec.inertia_mm4, "mm⁴"),
                 Step("Bending stress", "σ_b", "σ_b = M_r y_{max} / I", f"σ_b = {num(m_root, 0)} × {num(sec.y_max_mm)} / {num(sec.inertia_mm4, 0)}", sigma, "MPa"),
                 Step("Allowed", "σ_{all}", "σ_{all} = 110 / k", f"110 / {num(k_p)}", rs.blade_bending_mpa / k_p, "MPa")),
    ))
    checks.append(CheckResult(
        id="fin_shear", title="Spar web shear at the root", demand=tau_web, capacity=rs.blade_shear_mpa / k_p, unit="MPa",
        source=f"{src}.5.1: shear stress in the rudder blade",
        explanation="The spar webs carry the lift as shear, and the closed box carries the twist as a shear flow around it.",
        working=(Step("Shear from lift", "τ_F", "τ_F = F / (t_w (h_f + h_r))", f"τ_F = {num(f, 0)} / ({num(design.web_mm, 0)} × {num(heights)})", f / (design.web_mm * heights), "MPa"),
                 Step("Shear flow from twist", "q_t", "q_t = Q / (2 A_{box})", f"q_t = {num(q * 1000, 0)} / (2 × {num(sec.box_area_mm2, 0)})", q_t, "N/mm",
                      note="Bredt's formula for a closed thin-walled section."),
                 Step("Web shear", "τ_w", "τ_w = τ_F + q_t / t_w", f"τ_w = {num(f / (design.web_mm * heights))} + {num(q_t)} / {num(design.web_mm, 0)}", tau_web, "MPa"),
                 Step("Allowed", "τ_{all}", "τ_{all} = 50 / k", f"50 / {num(k_p)}", rs.blade_shear_mpa / k_p, "MPa")),
    ))
    checks.append(CheckResult(
        id="fin_equivalent", title="Fin skin combined stress", demand=equiv, capacity=rs.blade_equivalent_mpa / k_p, unit="MPa",
        source=f"{src}.5.1: equivalent stress in the rudder blade",
        explanation="The skin is bent by the lift and sheared by the twist at the same time.",
        working=(Step("Skin shear from twist", "τ_s", "τ_s = q_t / t", f"τ_s = {num(q_t)} / {num(design.skin_mm, 0)}", tau_skin, "MPa"),
                 Step("Equivalent stress", "σ_e", "σ_e = √(σ_b^2 + 3 τ_s^2)", f"σ_e = √({num(sigma)}² + 3 × {num(tau_skin)}²)", equiv, "MPa"),
                 Step("Allowed", "σ_{all}", "σ_{all} = 120 / k", f"120 / {num(k_p)}", rs.blade_equivalent_mpa / k_p, "MPa")),
    ))

    # ------------------------------------------------------------ plating
    pitch = design.rib_pitch_mm
    spacing = design.spar_spacing_mm
    s_short, s_long = min(pitch, spacing) / 1000.0, max(pitch, spacing) / 1000.0
    t_min = IACSS10.min_plating_mm(panel_short_m=s_short, panel_long_m=s_long, draught_m=job.draught_m, force_n=f,
                                   area_m2=job.area_m2, k=k_p)
    checks.append(CheckResult(
        id="skin_thickness", title="Skin plate thickness", demand=t_min, capacity=design.skin_mm, unit="mm",
        source=f"{src}.5.2: rudder plating", category="fit",
        explanation="The rules set a least skin thickness from the panel size between ribs and spars, the draught and the fin force.",
        working=(Step("Panel", "s × b", "s = smaller, b = larger of rib pitch and spar spacing", f"{num(pitch, 0)} mm × {num(spacing, 0)} mm", s_short * 1000, "mm"),
                 Step("Least thickness", "t_{min}", "t = 5.5 s β √((T + C_R 10^{-4}/A) k) + 2.5",
                      f"s = {num(s_short, 3)} m, T = {num(job.draught_m, 1)} m, C_R = {num(f, 0)} N, A = {num(job.area_m2)} m², k = {num(k_p)}", t_min, "mm")),
    ))
    web_min = max(0.7 * t_min, 8.0)
    checks.append(CheckResult(
        id="web_thickness", title="Spar and rib web thickness", demand=web_min, capacity=design.web_mm, unit="mm",
        source=f"{src}.5.2: web plates at least 70% of the side plating and 8 mm", category="fit",
        explanation="Webs inside the fin must not be too thin compared with the skin.",
        working=(Step("Least web", "t_{w,min}", "max(0.7 t_{min}, 8 mm)", f"max(0.7 × {num(t_min)}, 8)", web_min, "mm"),),
    ))
    k_b, elastic, critical = buckling_stress(design.skin_mm, spacing, pitch, plate.elastic_modulus_mpa, plate.poisson_ratio, fy_p)
    checks.append(CheckResult(
        id="skin_buckling", title="Skin panel buckling", demand=sigma, capacity=critical / BUCKLING_FACTOR, unit="MPa",
        source="NEMO practice: plate buckling (Timoshenko) with Johnson-Ostenfeld correction, factor 1.5",
        basis="practice",
        explanation="On the side being squeezed by the bending, a skin panel between ribs and spars can buckle like a thin sheet.",
        working=(Step("Buckling coefficient", "k_b", "k_b = min over m of (m b/a + a/(m b))^2", f"a = {num(pitch, 0)} mm (rib pitch), b = {num(spacing, 0)} mm (spar spacing)", k_b, ""),
                 Step("Elastic buckling stress", "σ_E", "σ_E = k_b π^2 E / (12 (1 − ν^2)) (t/b)^2", f"t = {num(design.skin_mm, 0)} mm", elastic, "MPa"),
                 Step("With plasticity", "σ_{cr}", "σ_{cr} = σ_E, or F_y (1 − F_y/(4 σ_E)) above F_y/2", f"F_y = {num(fy_p, 0)} MPa", critical, "MPa"),
                 Step("Allowed", "σ_{cr}/1.5", "σ_{cr} / 1.5", f"{num(critical)} / 1.5", critical / BUCKLING_FACTOR, "MPa")),
    ))

    # ---------------------------------------------------------- stiffness
    e_mod = plate.elastic_modulus_mpa
    a_z, span = 0.5 * design.span_mm, design.span_mm
    tip = f * a_z**2 * (3.0 * span - a_z) / (6.0 * e_mod * sec.inertia_mm4)
    checks.append(CheckResult(
        id="tip_deflection", title="Fin tip deflection", demand=tip, capacity=job.deflection_limit_mm, unit="mm",
        source="Design limit set for this job", basis="practice", category="stiffness",
        explanation="A fin that bends too much changes its angle and loads the stock bearings unevenly.",
        working=(Step("Tip deflection", "δ", "δ = F a^2 (3 b − a) / (6 E I), a = b/2", f"δ = {num(f, 0)} × {num(a_z, 0)}² × (3 × {num(span, 0)} − {num(a_z, 0)}) / (6 × {num(e_mod, 0)} × {num(sec.inertia_mm4, 0)})", tip, "mm"),),
    ))

    # ---------------------------------------------------------- cavitation
    checks.append(CheckResult(
        id="cavitation", title="Cavitation at the largest fin angle", demand=-loads.cp_min, capacity=loads.cavitation_number,
        unit="ratio", source="Panel method pressure against the cavitation number", basis="practice", category="fit", severity="advice",
        explanation=("If the lowest pressure on the foil falls below the vapour pressure of the water, bubbles form and collapse "
                     "on the skin. It erodes the fin and adds noise. Reduce the largest angle or the speed at which it is used."),
        working=(Step("Section angle for the same lift", "α_{2D}", "α_{2D} = C_L / (dC_l/dα)_{2D}", f"C_L = {num(loads.lift_coefficient)}", loads.section_angle_deg, "°",
                      note="The 2D lift slope comes from NEMO's panel method of the NACA section."),
                 Step("Lowest pressure coefficient", "−C_{p,min}", "panel method at α_{2D}", f"{design.thickness_ratio * 100:.0f}% thick NACA 00 section", -loads.cp_min, ""),
                 Step("Cavitation number", "σ", "σ = (p_a + ρ g h − p_v) / (½ ρ V^2)", f"h = {num(job.depth_m, 1)} m, V = {num(loads.speed_ms)} m/s", loads.cavitation_number, "")),
    ))

    masses = design.masses_kg(plate, stock)
    values = {"yield_plate_mpa": fy_p, "yield_stock_mpa": fy_s, "k_plate": k_p, "k_stock": k_s,
              "box_inertia_mm4": sec.inertia_mm4, "root_stress_mpa": sigma, "skin_min_mm": t_min,
              "tip_deflection_mm": tip, "stock_equivalent_mpa": worst_e[6]}
    return PartCheckReport(design=design, material=plate, loads=loads, rule_set=rs, checks=tuple(checks),
                           mass_kg=masses["total"], values=values,
                           extra={"masses_kg": masses, "stock_material": {"id": stock.id, "name": stock.name},
                                  "ribs": design.rib_count, "rib_pitch_mm": pitch})
