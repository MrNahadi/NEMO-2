"""Verification benchmarks: NEMO against answers known from theory or by hand.

Each benchmark returns the reference working (so the reference itself can be
checked), and a list of comparisons with their error and tolerance. The same
functions are used by the automated tests and by the app's Verification page.
"""

from __future__ import annotations

import time
from typing import Callable

import numpy as np

from . import __version__
from .working import Step, num

Emit = Callable[[str, dict], None]

E_STEEL = 210_000.0
NU = 0.3


def _compare(quantity: str, reference: float, nemo: float, unit: str, tolerance_percent: float) -> dict:
    error = (nemo - reference) / reference * 100.0 if reference else 0.0
    return {
        "quantity": quantity,
        "reference": reference,
        "nemo": nemo,
        "unit": unit,
        "error_percent": error,
        "tolerance_percent": tolerance_percent,
        "passed": abs(error) <= tolerance_percent,
    }


def padeye_hand_calculation() -> dict:
    """Every ASME BTH-1 padeye value against a calculation done by hand beforehand."""
    from .data import get_material, smallest_shackle_for
    from .loads import LiftScenario, padeye_loads
    from .parts.padeye import PadeyeDesign, check_padeye
    from .rules import ASMEBTH1

    loads = padeye_loads(LiftScenario(lifted_mass_kg=4000, lift_points=2, sling_angle_deg=60))
    shackle = smallest_shackle_for(loads.sling_force_t)
    design = PadeyeDesign(20, 45, 21, 200, 90, 8)
    r = check_padeye(design, material=get_material("S355"), shackle=shackle, loads=loads, rule_set=ASMEBTH1())
    tol = 0.1
    # Values worked out by hand, step by step, before the code was written.
    comparisons = [
        _compare("Sling force F", 22_647.6, loads.sling_force_n, "N", tol),
        _compare("Strength reduction C_r", 0.885696, r.values["strength_reduction_factor_cr"], "", tol),
        _compare("Effective width b_{eff}", 22.0013, r.values["effective_width_mm"], "mm", tol),
        _compare("Tension through pinhole P_t", 101_763, r.check("head_tension").capacity, "N", tol),
        _compare("Fracture beyond pinhole P_b", 117_933, r.check("head_fracture").capacity, "N", tol),
        _compare("Shear plane area A_v", 1_492.61, r.values["shear_area_mm2"], "mm²", tol),
        _compare("Double plane shear P_v", 136_408, r.check("head_shear_out").capacity, "N", tol),
        _compare("Pin bearing P_p", 54_912.5, r.check("head_bearing").capacity, "N", tol),
        _compare("Base combined use", 0.14898, r.check("base_combined").demand, "", tol),
        _compare("Base weld stress", 26.179, r.check("base_weld").demand, "MPa", tol),
        _compare("Plate mass", 2.5958, r.mass_kg, "kg", tol),
    ]
    return {
        "setup": [
            Step("Lift", "", "4 000 kg on 2 padeyes, slings at 60°", "S355 plate 20 mm, R 45, hole 21, base 200, hole height 90, weld 8", 0, ""),
            Step("Design rules", "N_d", "ASME BTH-1 category B", "N_d = 3.00; pin connections 1.20 N_d = 3.60", 3.0, ""),
            Step("Shackle", "", "Smallest Crosby G-2130 ≥ 2.309 t", "3.25 t: pin 19.1 mm, jaw 26.9 mm", 3.25, "t"),
        ],
        "comparisons": comparisons,
    }


def cad_volume() -> dict:
    """3D solid volume against the exact area formula, with and without cheek plates."""
    from .parts.bracket.cad import build_bracket
    from .parts.bracket.geometry import BracketDesign
    from .parts.padeye import PadeyeDesign
    from .parts.padeye.cad import build_padeye

    plain = PadeyeDesign(20, 45, 21, 200, 90, 8)
    cheeks = PadeyeDesign(12, 60, 36, 260, 120, 8, cheek_thickness_mm=6, cheek_radius_mm=50, cheek_weld_leg_mm=5)
    bracket = BracketDesign(200, 100, 10, 80, 8, 110, 114.3, 12, 6, 6)
    return {
        "setup": [
            Step("Formula", "V", "V = A_{plate} t + 2 π (R_c^2 − D_h^2/4) t_c",
                 "A_{plate} from base corners, tangent points and head arc, minus the hole", 0, ""),
            Step("Pipe bracket", "V", "V = L b t_s − 2 π d^2/4 t_s + 2 × ½ L h_k t_k", "seat with two U-bolt holes plus two knees", 0, ""),
        ],
        "comparisons": [
            _compare("Plain padeye volume", plain.volume_mm3(), build_padeye(plain).volume_mm3, "mm³", 0.01),
            _compare("Padeye with cheek plates", cheeks.volume_mm3(), build_padeye(cheeks).volume_mm3, "mm³", 0.01),
            _compare("Pipe support bracket", bracket.volume_mm3(), build_bracket(bracket).volume_mm3, "mm³", 0.01),
        ],
    }


def panel_method() -> dict:
    """The foil pressure solver against exact potential flow and thick-foil theory."""
    import math

    from .hydro import circle_contour, panel_solve, section_lift_slope

    xs, ys = circle_contour(160)
    cp = panel_solve(xs, ys, 0.0).cp_min
    slope12, slope20 = section_lift_slope(0.12), section_lift_slope(0.20)
    ref12, ref20 = 2 * math.pi * (1 + 0.77 * 0.12), 2 * math.pi * (1 + 0.77 * 0.20)
    return {
        "setup": [
            Step("Circle in uniform flow", "C_{p,min}", "C_p = 1 − 4 sin^2 θ, lowest −3 at the sides", "160 panels", -3.0, ""),
            Step("Thick symmetric foil", "dC_l/dα", "dC_l/dα ≈ 2π (1 + 0.77 t/c)", "NACA 0012 and NACA 0020, 160 panels", ref12, "per rad"),
        ],
        "comparisons": [
            _compare("Lowest pressure on a circle", -3.0, cp, "", 0.5),
            _compare("NACA 0012 lift slope", ref12, slope12, "per rad", 3.0),
            _compare("NACA 0020 lift slope", ref20, slope20, "per rad", 3.0),
        ],
    }


def stock_beam_theory() -> dict:
    """The stress solver on a round shaft in bending and twist, against beam theory away from the support."""
    from .parts.stabilizer.fea import analyse_stock
    from .parts.stabilizer.geometry import FinDesign
    from .parts.stabilizer.job import FinJob

    job = FinJob()
    loads = job.loads
    design = FinDesign(1400, 1200, 0.20, 0.35, 0.15, 0.65, 10, 10, 350, 160, 200)
    study = analyse_stock(design, material=job.stock_material, loads=loads, levels=(1.0, 0.7))
    extra = study.extra
    return {
        "setup": [
            Step("Shaft", "D", "solid round stock fixed at the bearing", "Ø160 mm, 200 mm to the fin root, load at mid-span", 160, "mm"),
            Step("Beam theory", "σ_e", "σ_e = √(σ_b^2 + 3 τ^2), σ_b = 32 M / (π D^3), τ = 16 Q / (π D^3)",
                 f"section {num(extra['hand_section_mm'], 0)} mm from the bearing", extra["hand_stress_mpa"], "MPa"),
        ],
        "comparisons": [
            _compare("Equivalent stress near the bearing", extra["hand_stress_mpa"], study.head_von_mises_mpa, "MPa", 4.0),
            _compare("Support reaction", loads.design_force_n, float(-study.levels[-1].reaction_force_n[1]), "N", 1e-6),
        ],
        "mesh": {"elements": study.levels[-1].elements, "equations": study.levels[-1].dofs},
    }


def cantilever() -> dict:
    """Steel bar fixed at one end, pushed down at the other."""
    from build123d import Box, Pos

    from .fea import SurfaceLoad, boundary_facets, mesh_part, solve_static, to_skfem

    length, width, depth, load = 200.0, 20.0, 20.0, 1000.0
    m = to_skfem(mesh_part(Pos(length / 2, 0, 0) * Box(length, width, depth), global_size_mm=5.0))
    result = solve_static(
        m, elastic_modulus_mpa=E_STEEL, poisson_ratio=NU,
        fixed_facets=boundary_facets(m, lambda x: x[0] < 1e-6),
        loads=[SurfaceLoad("end", boundary_facets(m, lambda x: x[0] > length - 1e-6),
                           lambda x: np.stack([0 * x[0], 0 * x[0], 1 + 0 * x[0]]), np.array([0.0, 0.0, -load]))],
    )
    inertia = width * depth**3 / 12
    g = E_STEEL / (2 * (1 + NU))
    bending = load * length**3 / (3 * E_STEEL * inertia)
    shear = load * length / (5 / 6 * g * width * depth)
    stress = load * (length / 2) * (depth / 2) / inertia
    tip = np.abs(m.p[0] - length) < 1e-6
    mid = (np.abs(m.p[0] - length / 2) < 3.0) & (np.abs(np.abs(m.p[2]) - depth / 2) < 1e-6)
    return {
        "setup": [
            Step("Bar", "", "200 × 20 × 20 mm steel, fixed at one end", "E = 210 000 MPa, ν = 0.3, end load P = 1 000 N", 0, ""),
            Step("Second moment of area", "I", "I = b d^3 / 12", "I = 20 × 20³ / 12", inertia, "mm⁴"),
            Step("Bending deflection", "δ_b", "δ_b = P L^3 / (3 E I)", f"δ_b = 1000 × 200³ / (3 × 210000 × {num(inertia)})", bending, "mm"),
            Step("Shear deflection (Timoshenko)", "δ_s", "δ_s = P L / (κ G A), κ = 5/6",
                 f"δ_s = 1000 × 200 / (0.833 × {num(g)} × 400)", shear, "mm"),
            Step("Stress at mid-span surface", "σ", "σ = M c / I = P (L/2)(d/2) / I", f"σ = 1000 × 100 × 10 / {num(inertia)}", stress, "MPa"),
        ],
        "comparisons": [
            _compare("Tip deflection", bending + shear, float(-result.displacement[2, tip].mean()), "mm", 3.0),
            _compare("Bending stress at mid-span", stress, result.max_von_mises_where(mid), "MPa", 4.0),
            _compare("Support reaction", load, float(result.reaction_force_n[2]), "N", 1e-6),
        ],
        "mesh": {"elements": result.element_count, "equations": result.dof_count},
    }


def plate_with_hole() -> dict:
    """Wide plate with a small central hole, pulled at both ends: peak stress at the hole."""
    from build123d import Box, Cylinder

    from .fea import SurfaceLoad, boundary_facets, mesh_part, solve_static, to_skfem

    width, length, thickness, hole, stress = 200.0, 800.0, 10.0, 20.0, 100.0
    plate = Box(length, width, thickness) - Cylinder(hole / 2, thickness * 2)
    m = to_skfem(mesh_part(plate, global_size_mm=12.0, local_size_mm=0.9,
                           refine_surface=lambda k, b: k == "Cylinder" and (b[3] - b[0]) < hole * 1.5,
                           refine_distance_mm=40.0))
    result = solve_static(
        m, elastic_modulus_mpa=E_STEEL, poisson_ratio=NU,
        fixed_facets=boundary_facets(m, lambda x: x[0] < -length / 2 + 1e-6),
        loads=[SurfaceLoad("tension", boundary_facets(m, lambda x: x[0] > length / 2 - 1e-6),
                           lambda x: np.stack([1 + 0 * x[0], 0 * x[0], 0 * x[0]]),
                           np.array([stress * width * thickness, 0.0, 0.0]))],
    )
    ratio = hole / width
    kt_net = 2 + (1 - ratio) ** 3
    kt = kt_net / (1 - ratio)
    peak = result.max_von_mises_where(np.hypot(m.p[0], m.p[1]) < hole / 2 + 0.5)
    return {
        "setup": [
            Step("Plate", "", "800 × 200 × 10 mm steel with a 20 mm hole", "Pulled with 100 MPa average stress", 0, ""),
            Step("Stress concentration on net section (Heywood)", "K_{tn}", "K_{tn} = 2 + (1 − d/W)^3", "K_{tn} = 2 + (1 − 0.1)³", kt_net, ""),
            Step("On gross section", "K_t", "K_t = K_{tn} / (1 − d/W)", f"K_t = {num(kt_net)} / 0.9", kt, ""),
        ],
        "comparisons": [
            _compare("Stress concentration factor", kt, peak / stress, "", 5.0),
            _compare("Support reaction", stress * width * thickness, float(-result.reaction_force_n[0]), "N", 1e-6),
        ],
        "mesh": {"elements": result.element_count, "equations": result.dof_count},
    }


BENCHMARKS = (
    ("padeye-hand-calc", "Padeye checks against a hand calculation",
     "Every ASME BTH-1 value for one padeye, worked out by hand first.", "Hand calculation in the engineering manual", padeye_hand_calculation),
    ("cad-volume", "3D model volume against the exact formula",
     "The solid NEMO exports has exactly the volume the mass is calculated from.", "Exact geometry", cad_volume),
    ("cantilever", "Cantilever beam",
     "The stress solver against beam theory for a bar fixed at one end.", "Timoshenko beam theory", cantilever),
    ("plate-hole", "Plate with a hole",
     "The stress solver against the known peak stress at a hole, the same effect that governs a padeye.",
     "Heywood (1952), as given in Peterson's Stress Concentration Factors", plate_with_hole),
    ("panel-method", "Foil pressure solver",
     "The panel method used for the stabilizer fin, against exact flow round a circle and thick-foil lift theory.",
     "Potential flow theory; Abbott and von Doenhoff, Theory of Wing Sections", panel_method),
    ("stock-beam", "Fin stock against beam theory",
     "The stress solver on a round shaft that is bent and twisted, the load case of a stabilizer stock.",
     "Beam and torsion theory, as used in IACS UR S10.4", stock_beam_theory),
)


def run_all(emit: Emit | None = None) -> dict:
    send = emit or (lambda kind, data: None)
    results = []
    for index, (bid, title, description, source, func) in enumerate(BENCHMARKS):
        send("benchmark_start", {"id": bid, "title": title, "index": index, "count": len(BENCHMARKS)})
        started = time.perf_counter()
        try:
            out = func()
            entry = {
                "id": bid, "title": title, "description": description, "source": source,
                "setup": [s.to_dict() for s in out["setup"]], "comparisons": out["comparisons"],
                "mesh": out.get("mesh"), "passed": all(c["passed"] for c in out["comparisons"]), "error": None,
            }
        except Exception as exc:  # noqa: BLE001 - a broken benchmark is itself a result to show
            entry = {"id": bid, "title": title, "description": description, "source": source,
                     "setup": [], "comparisons": [], "mesh": None, "passed": False, "error": str(exc)}
        entry["seconds"] = time.perf_counter() - started
        results.append(entry)
        send("benchmark_done", entry)
    return {
        "nemo_version": __version__,
        "ran_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "passed": all(r["passed"] for r in results),
        "benchmarks": results,
    }


if __name__ == "__main__":  # pragma: no cover
    import json

    print(json.dumps(run_all(lambda k, d: print(k, d.get("title", ""))), indent=2, default=str)[:4000])
