"""Hand-calculation working for padeye loads and checks (ASME BTH-1).

``explain`` adds the working to a finished check report. It is kept separate
from ``check_padeye`` so the sizing search, which checks tens of thousands of
designs, does not build text it never shows.

Formula strings use a small markup understood by the app and the report:
``X_t`` or ``X_{eff}`` for subscripts and ``x^2`` for superscripts.
"""

from __future__ import annotations

import math
from dataclasses import replace

from ...checks import CheckResult
from ...loads import STANDARD_GRAVITY, LiftScenario, PadeyeLoads
from ...working import Step, kn, num
from .checks import MIN_HOLE_CLEARANCE_MM, SHACKLE_JAW_CLEARANCE_MM, SHACKLE_MIN_FILL_FRACTION, PadeyeCheckReport, minimum_fillet_size_mm


def load_steps(scenario: LiftScenario, loads: PadeyeLoads) -> list[Step]:
    g = STANDARD_GRAVITY
    n = scenario.carrying_points
    theta = scenario.sling_angle_deg
    common = [
        Step("Weight of the load", "W", "W = m · g",
             f"W = {num(scenario.lifted_mass_kg, 0)} kg × {g} m/s²",
             scenario.lifted_mass_kg * g / 1000, "kN"),
        Step("Vertical force on one padeye", "V", "V = W · DAF / n_c",
             f"V = {num(scenario.lifted_mass_kg * g / 1000)} kN × {num(scenario.dynamic_factor, 2)} / {n}",
             loads.vertical_n / 1000, "kN",
             note="n_c is the number of lifting points assumed to carry the load."),
        Step("Force along the sling", "F", "F = V / sin θ",
             f"F = {kn(loads.vertical_n)} / sin {num(theta, 1)}°",
             loads.sling_force_n / 1000, "kN",
             note=f"Equal to {num(loads.sling_force_t, 2)} t, compared with the shackle rating."),
    ]
    beta = scenario.out_of_plane_angle_deg
    if beta <= 0.0:
        return [*common, *_in_line_steps(scenario, loads, theta)]
    return [
        *common,
        Step("In-plane horizontal part of the sling force", "H", "H = F · cos θ · cos β",
             f"H = {kn(loads.sling_force_n)} × cos {num(theta, 1)}° × cos {num(beta, 1)}°",
             loads.horizontal_n / 1000, "kN",
             note="β is the angle between the sling and the padeye plate, seen from above."),
        Step("Sideways part from the oblique sling", "Q_s", "Q_s = F · cos θ · sin β",
             f"Q_s = {kn(loads.sling_force_n)} × cos {num(theta, 1)}° × sin {num(beta, 1)}°",
             loads.side_from_angle_n / 1000, "kN"),
        Step("Side-load angle on the shackle", "γ", "γ = asin(cos θ · sin β)",
             f"γ = asin(cos {num(theta, 1)}° × sin {num(beta, 1)}°)", loads.side_angle_deg, "°",
             note="The angle between the sling and the plane of the padeye. The shackle's rating is reduced for it."),
        Step("Sideways force used", "Q", "Q = max(Q_s, k · F)",
             f"Q = max({kn(loads.side_from_angle_n)}, {num(scenario.side_load_fraction * 100, 1)}% × {kn(loads.sling_force_n)})",
             loads.side_n / 1000, "kN",
             note="The allowance k still applies when the real sideways part is smaller."),
    ]


def _in_line_steps(scenario: LiftScenario, loads: PadeyeLoads, theta: float) -> list[Step]:
    return [
        Step("Horizontal part of the sling force", "H", "H = F · cos θ",
             f"H = {kn(loads.sling_force_n)} × cos {num(theta, 1)}°",
             loads.horizontal_n / 1000, "kN"),
        Step("Sideways allowance", "Q", "Q = k · F",
             f"Q = {num(scenario.side_load_fraction * 100, 1)}% × {kn(loads.sling_force_n)}",
             loads.side_n / 1000, "kN",
             note="Allows for the sling not lining up perfectly with the padeye."),
    ]


def explain(report: PadeyeCheckReport) -> PadeyeCheckReport:
    """Return the same report with working attached to every check."""
    d, m, s, loads, rs = report.design, report.material, report.shackle, report.loads, report.rule_set
    v = report.values
    t_main = d.main_thickness_mm
    t = d.total_thickness_mm
    dh, dp = d.hole_diameter_mm, s.pin_diameter_mm
    r = d.head_radius_at_hole_mm
    fu, fy_head, fy_main = m.tensile_strength_mpa, v["yield_head_mpa"], v["yield_main_mpa"]
    nd, nd_pin = rs.nd, rs.nd_pin_connection
    f = loads.sling_force_n
    demand = Step("Demand: sling force on the padeye", "F", "F", f"F = {kn(f)} (see forces)", f / 1000, "kN")
    t_note = f"t = {num(t_main, 0)} mm main plate" + (f" + 2 × {num(d.cheek_thickness_mm, 0)} mm cheek plates" if d.has_cheeks else "")

    steps: dict[str, list[Step]] = {}

    if "strength_reduction_factor_cr" in v:
        be = r - dh / 2
        cr = v["strength_reduction_factor_cr"]
        beff = v["effective_width_mm"]
        b3 = be * 0.6 * (fu / fy_head) * math.sqrt(dh / be)
        common = [
            Step("Thickness at the hole", "t", "t = t_{main} + 2 t_c", t_note, t, "mm"),
            Step("Strength reduction for pin clearance", "C_r", "C_r = 1 − 0.275 √(1 − D_p^2 / D_h^2)",
                 f"C_r = 1 − 0.275 √(1 − {num(dp, 1)}² / {num(dh, 1)}²)", cr, ""),
            Step("Net width beside the hole", "b_e", "b_e = R − D_h / 2",
                 f"b_e = {num(r, 0)} − {num(dh, 1)} / 2", be, "mm"),
        ]
        steps["head_tension"] = common + [
            Step("Effective width", "b_{eff}", "b_{eff} = min(b_e, 4t, 0.6 (F_u / F_y) √(D_h / b_e) b_e)",
                 f"b_{{eff}} = min({num(be)}, {num(4 * t)}, {num(b3)})", beff, "mm"),
            Step("Allowed load", "P_t", "P_t = C_r F_u · 2 t b_{eff} / (1.20 N_d)",
                 f"P_t = {num(cr)} × {num(fu, 0)} × 2 × {num(t, 0)} × {num(beff)} / {num(nd_pin, 2)}",
                 report.check("head_tension").capacity / 1000, "kN"),
            demand,
        ]
        steps["head_fracture"] = common + [
            Step("Allowed load", "P_b", "P_b = C_r F_u [1.13 (R − D_h/2) + 0.92 b_e / (1 + b_e/D_h)] t / (1.20 N_d)",
                 f"P_b = {num(cr)} × {num(fu, 0)} × [1.13 × {num(r - dh / 2)} + 0.92 × {num(be)} / (1 + {num(be)}/{num(dh, 1)})] × {num(t, 0)} / {num(nd_pin, 2)}",
                 report.check("head_fracture").capacity / 1000, "kN"),
            demand,
        ]
        phi = v["shear_plane_angle_deg"]
        z = v["curvature_loss_mm"]
        a = r - dh / 2
        steps["head_shear_out"] = [
            common[0],
            Step("Shear plane angle", "φ", "φ = 55° · D_p / D_h", f"φ = 55° × {num(dp, 1)} / {num(dh, 1)}", phi, "°"),
            Step("Material above the hole", "a", "a = R − D_h / 2", f"a = {num(r, 0)} − {num(dh, 1)} / 2", a, "mm"),
            Step("Loss from the curved edge", "Z", "Z = r − √(r^2 − (D_p/2 · sin φ)^2)",
                 f"Z = {num(r, 0)} − √({num(r, 0)}² − ({num(dp / 2)} × sin {num(phi, 1)}°)²)", z, "mm"),
            Step("Area of the two shear planes", "A_v", "A_v = 2 [a + D_p/2 (1 − cos φ) − Z] t",
                 f"A_v = 2 × [{num(a)} + {num(dp / 2)} × (1 − cos {num(phi, 1)}°) − {num(z)}] × {num(t, 0)}",
                 v["shear_area_mm2"], "mm²"),
            Step("Allowed load", "P_v", "P_v = 0.70 F_u A_v / (1.20 N_d)",
                 f"P_v = 0.70 × {num(fu, 0)} × {num(v['shear_area_mm2'])} / {num(nd_pin, 2)}",
                 report.check("head_shear_out").capacity / 1000, "kN"),
            demand,
        ]
        coeff = 1.25 if rs.service_class == 0 else 0.63
        steps["head_bearing"] = [
            common[0],
            Step("Allowed load", "P_p", "P_p = C F_y D_p t / N_d",
                 f"P_p = {coeff} × {num(fy_head, 0)} × {num(dp, 1)} × {num(t, 0)} / {num(nd, 2)}",
                 report.check("head_bearing").capacity / 1000, "kN",
                 note=f"C = {coeff} for service class {rs.service_class}. F_y is the lower yield of the plates at the hole."),
            demand,
        ]
        steps["pin_hole_fit"] = [
            Step("Pin to hole ratio", "D_p/D_h", "D_p / D_h ≥ 0.90", f"{num(dp, 1)} / {num(dh, 1)}", dp / dh, ""),
        ]
        steps["hole_clearance"] = [
            Step("Smallest hole that fits", "D_{min}", "D_{min} = D_p + 1 mm", f"D_{{min}} = {num(dp, 1)} + {MIN_HOLE_CLEARANCE_MM:g}", dp + MIN_HOLE_CLEARANCE_MM, "mm"),
            Step("Hole diameter chosen", "D_h", "D_h", f"D_h = {num(dh, 1)}", dh, "mm"),
        ]

    if d.has_cheeks:
        c = report.check("cheek_weld")
        share = c.details["load_per_cheek_n"]
        throat = 0.7071 * d.cheek_weld_leg_mm
        length = 2 * math.pi * d.cheek_radius_mm
        steps["cheek_weld"] = [
            Step("Load carried by one cheek plate", "F_c", "F_c = F · t_c / t",
                 f"F_c = {kn(f)} × {num(d.cheek_thickness_mm, 0)} / {num(t, 0)}", share / 1000, "kN"),
            Step("Weld throat", "a", "a = 0.707 w", f"a = 0.707 × {num(d.cheek_weld_leg_mm, 0)}", throat, "mm"),
            Step("Weld length around the cheek", "L_w", "L_w = 2π R_c", f"L_w = 2π × {num(d.cheek_radius_mm, 0)}", length, "mm"),
            Step("Weld stress", "f_w", "f_w = F_c / (L_w a)", f"f_w = {num(share, 0)} / ({num(length)} × {num(throat)})", c.demand, "MPa"),
            _weld_allow(rs, report),
        ]

    base = report.check("base_combined").details
    length, h = d.base_length_mm, d.hole_height_mm
    e_mod = m.elastic_modulus_mpa
    lam = h * length / t_main**2
    steps["base_combined"] = [
        Step("Pulling stress", "f_a", "f_a = V / (L t)", f"f_a = {num(loads.vertical_n, 0)} / ({num(length, 0)} × {num(t_main, 0)})", base["axial_mpa"], "MPa"),
        Step("In-plane bending stress", "f_{bx}", "f_{bx} = H h / (t L^2 / 6)",
             f"f_{{bx}} = {num(loads.horizontal_n, 0)} × {num(h, 0)} / ({num(t_main, 0)} × {num(length, 0)}² / 6)", base["bending_in_plane_mpa"], "MPa"),
        Step("Sideways bending stress", "f_{by}", "f_{by} = Q h / (L t^2 / 6)",
             f"f_{{by}} = {num(loads.side_n, 0)} × {num(h, 0)} / ({num(length, 0)} × {num(t_main, 0)}² / 6)", base["bending_side_mpa"], "MPa"),
        Step("Allowed tension", "F_t", "F_t = F_y / N_d", f"F_t = {num(fy_main, 0)} / {num(nd, 2)}", base["allow_tension_mpa"], "MPa"),
        Step("Allowed in-plane bending", "F_{bx}", "λ = h L / t^2, then BTH-1 rectangular-bar rule",
             f"λ = {num(h, 0)} × {num(length, 0)} / {num(t_main, 0)}² = {num(lam)} (limit for full strength {num(0.08 * e_mod / fy_main)})",
             base["allow_bending_in_plane_mpa"], "MPa",
             note="Long thin plates bent on edge can buckle sideways; λ measures that risk."),
        Step("Allowed sideways bending", "F_{by}", "F_{by} = 1.25 F_y / N_d", f"F_{{by}} = 1.25 × {num(fy_main, 0)} / {num(nd, 2)}", base["allow_bending_side_mpa"], "MPa"),
        Step("Combined use", "U", "U = f_a/F_t + f_{bx}/F_{bx} + f_{by}/F_{by}",
             f"U = {num(base['axial_mpa'])}/{num(base['allow_tension_mpa'])} + {num(base['bending_in_plane_mpa'])}/{num(base['allow_bending_in_plane_mpa'])} + {num(base['bending_side_mpa'])}/{num(base['allow_bending_side_mpa'])}",
             report.check("base_combined").demand, "", note="Must not exceed 1.0."),
    ]
    shear = report.check("base_shear")
    steps["base_shear"] = [
        Step("Shear stress", "f_v", "f_v = √(H^2 + Q^2) / (L t)",
             f"f_v = √({num(loads.horizontal_n, 0)}² + {num(loads.side_n, 0)}²) / ({num(length, 0)} × {num(t_main, 0)})", shear.demand, "MPa"),
        Step("Allowed shear", "F_v", "F_v = F_y / (√3 N_d)", f"F_v = {num(fy_main, 0)} / (√3 × {num(nd, 2)})", shear.capacity, "MPa"),
    ]
    weld = report.check("base_weld")
    throat = weld.details["throat_mm"]
    steps["base_weld"] = [
        Step("Weld throat", "a", "a = 0.707 w", f"a = 0.707 × {num(d.weld_leg_mm, 0)}", throat, "mm"),
        Step("Normal stress on the weld", "f_n", "f_n = V/A_w + H h/S_x + Q h/S_y",
             f"A_w = 2 × {num(length, 0)} × {num(throat)}; S_x = 2 a L²/6; S_y = L a (t + a)", weld.details["normal_mpa"], "MPa"),
        Step("Shear stress on the weld", "f_s", "f_s = √(H^2 + Q^2) / A_w",
             f"f_s = √({num(loads.horizontal_n, 0)}² + {num(loads.side_n, 0)}²) / {num(2 * length * throat, 0)}", weld.details["shear_mpa"], "MPa"),
        Step("Resultant on the throat", "f_w", "f_w = √(f_n^2 + f_s^2)", f"f_w = √({num(weld.details['normal_mpa'])}² + {num(weld.details['shear_mpa'])}²)", weld.demand, "MPa"),
        _weld_allow(rs, report),
    ]
    side_factor = report.check("shackle_rating").details.get("side_load_factor", 1.0)
    steps["shackle_rating"] = [
        Step("Sling force in tonnes", "F/g", "F / g", f"{kn(f)} / 9.807", loads.sling_force_t, "t"),
        Step("Shackle working load limit", "WLL", "WLL", s.label, s.wll_t, "t"),
    ]
    if round(loads.side_angle_deg) > 0:
        steps["shackle_rating"] += [
            Step("Side-loading reduction", "r", "r from the maker's table at γ",
                 f"γ = {num(loads.side_angle_deg, 1)}° from in-line", side_factor, "",
                 note="Crosby: 100% up to 10°, 85% to 20°, 75% to 30°, 70% to 45°, 60% to 55°, 55% to 70°, 50% to 90°. "
                      "Shackles over 3 in: 100% to 5°, 85% to 10°, analysis beyond."),
            Step("Rating at this angle", "r · WLL", "r · WLL", f"{num(side_factor, 2)} × {num(s.wll_t, 2)} t", side_factor * s.wll_t, "t"),
        ]
    steps["shackle_fit"] = [
        Step("Space needed in the jaw", "t + c", "t + 2 mm", f"{num(t, 0)} + {SHACKLE_JAW_CLEARANCE_MM:g}", t + SHACKLE_JAW_CLEARANCE_MM, "mm"),
        Step("Shackle jaw width", "J", "J", s.label, s.jaw_width_mm, "mm"),
    ]
    steps["shackle_fill"] = [
        Step("Thinnest padeye that fills the jaw", "0.6 J", "0.6 J", f"0.6 × {num(s.jaw_width_mm, 1)}", SHACKLE_MIN_FILL_FRACTION * s.jaw_width_mm, "mm"),
        Step("Padeye thickness at the hole", "t", "t", t_note, t, "mm"),
    ]
    steps["base_weld_size"] = [
        Step("Smallest fillet allowed", "w_{min}", "AWS D1.1 table", f"plate {num(t_main, 0)} mm", minimum_fillet_size_mm(t_main), "mm"),
        Step("Weld chosen", "w", "w", f"w = {num(d.weld_leg_mm, 0)}", d.weld_leg_mm, "mm"),
    ]
    if d.has_cheeks:
        thick = max(d.cheek_thickness_mm, t_main)
        steps["cheek_weld_size"] = [
            Step("Smallest fillet allowed", "w_{min}", "AWS D1.1 table", f"thicker part {num(thick, 0)} mm", minimum_fillet_size_mm(thick), "mm"),
            Step("Weld chosen", "w", "w", f"w = {num(d.cheek_weld_leg_mm, 0)}", d.cheek_weld_leg_mm, "mm"),
        ]
    if "hole_fits_pin" in {c.id for c in report.checks}:
        steps["hole_fits_pin"] = [
            Step("Smallest hole that fits", "D_{min}", "D_{min} = D_p + 1 mm", f"D_{{min}} = {num(dp, 1)} + 1", dp + 1, "mm"),
        ]

    checks: list[CheckResult] = [replace(c, working=tuple(steps.get(c.id, ()))) for c in report.checks]
    return replace(report, checks=tuple(checks))


def _weld_allow(rs, report: PadeyeCheckReport) -> Step:
    cap = report.check("base_weld").capacity
    exx = cap * 1.20 * rs.nd / 0.60
    return Step("Allowed weld stress", "F_w", "F_w = 0.60 E_{xx} / (1.20 N_d)",
                f"F_w = 0.60 × {num(exx, 0)} / (1.20 × {num(rs.nd, 2)})", cap, "MPa",
                note="E_{xx} is the weld metal strength (E70XX / E7018 class electrodes).")
