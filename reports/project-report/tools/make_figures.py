"""Figures for the project report, drawn from the runs in data/ (run make_report_data.py first).

Run from the engine folder:  .venv\\Scripts\\python.exe ..\\reports\\project-report\\tools\\make_figures.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker  # noqa: E402
import numpy as np  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402

from nemo.hydro import circle_contour, panel_solve, section_lift_slope  # noqa: E402
from nemo.parts.bracket.cad import build_bracket  # noqa: E402
from nemo.parts.bracket.geometry import BracketDesign  # noqa: E402
from nemo.parts.padeye.cad import build_padeye  # noqa: E402
from nemo.parts.padeye.geometry import PadeyeDesign  # noqa: E402
from nemo.parts.stabilizer.cad import build_fin  # noqa: E402
from nemo.parts.stabilizer.geometry import FinDesign  # noqa: E402
from nemo.report_pdf import _clean, _fonts, _search_figure, _surface_figure  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA, IMG = ROOT / "data", ROOT / "images"
INK, MUTED, ACCENT, RED = "#1a1a1a", "#8a8a8a", "#0a6fd6", "#c0341d"


def run(part: str) -> tuple[Path, dict]:
    cases = json.loads((DATA / "cases.json").read_text())
    d = DATA / cases[part]["run_dir"]
    return d, json.loads((d / "results.json").read_text())


def save(fig, name: str) -> None:
    fig.savefig(IMG / name, dpi=220, bbox_inches="tight", pad_inches=0.03, facecolor="white")
    plt.close(fig)
    print("wrote", name)


def cad_figure(part, view=(22, -58), size=(4.2, 3.6), colour=(0.72, 0.75, 0.79)):
    verts, tris = part.tessellate(0.2, 0.2)
    p = np.array([[v.X, v.Y, v.Z] for v in verts])
    t = np.array(tris)
    faces = p[t]
    n = np.cross(faces[:, 1] - faces[:, 0], faces[:, 2] - faces[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    light = np.array([0.45, -0.6, 0.66])
    shade = 0.45 + 0.55 * np.abs(n @ (light / np.linalg.norm(light)))
    rgb = np.clip(np.outer(shade, colour), 0, 1)
    fig = plt.figure(figsize=size)
    ax = fig.add_subplot(projection="3d")
    ax.add_collection3d(Poly3DCollection(faces, facecolors=rgb, edgecolors="none", linewidths=0))
    lo, hi = p.min(axis=0), p.max(axis=0)
    span, c = (hi - lo).max(), (lo + hi) / 2
    for setter, i in ((ax.set_xlim, 0), (ax.set_ylim, 1), (ax.set_zlim, 2)):
        setter(c[i] - span / 2, c[i] + span / 2)
    ax.set_box_aspect((1, 1, 1), zoom=1.35)
    ax.view_init(elev=view[0], azim=view[1])
    ax.set_axis_off()
    fig.subplots_adjust(0, 0, 1, 1)
    return fig


def models() -> None:
    _, pr = run("padeye")
    pd = PadeyeDesign(**pr["designs"][0]["check_report"]["design"])
    save(cad_figure(build_padeye(pd).part), "padeye-model.png")
    _, br = run("pipe-bracket")
    bd = BracketDesign(**br["designs"][0]["check_report"]["design"])
    save(cad_figure(build_bracket(bd).part, view=(24, -125)), "bracket-model.png")
    _, fr = run("stabilizer")
    fd = FinDesign(**fr["designs"][0]["check_report"]["design"])
    from build123d import Box, Pos

    whole = build_fin(fd).part
    cut = whole - Pos(fd.chord_mm / 2, 500.0, fd.span_mm / 2) * Box(fd.chord_mm * 1.5, 1000.0, fd.span_mm * 3)
    save(cad_figure(whole, view=(18, -62), size=(4.0, 4.4)), "fin-model.png")
    save(cad_figure(cut, view=(30, 70), size=(4.4, 4.4)), "fin-cutaway.png")


def stress() -> None:
    for part, name, kw in (("padeye", "padeye", {}), ("pipe-bracket", "bracket", {"view": (26, -125)}),
                           ("stabilizer", "fin-stock", {"view": (12, -40)})):
        d, res = run(part)
        entry = res["designs"][0]
        surface = json.loads((d / entry["files"]["stress_surface"]).read_text())
        y = entry["fea"]["yield_strength_mpa"]
        save(_surface_figure(surface, stress=True, yield_mpa=y, width_in=4.4, height_in=3.4, **kw), f"{name}-stress.png")
        if part == "padeye":
            des = entry["check_report"]["design"]
            save(_surface_figure(surface, stress=True, yield_mpa=y, view=(8, -90), width_in=4.4, height_in=3.4,
                                 zoom=(0.0, des["hole_height_mm"], des["head_radius_mm"] * 1.25)), "padeye-stress-head.png")
        mesh_event = next(e for e in json.loads((d / "engineering-log.json").read_text())
                          if e["kind"] == "mesh" and e.get("surface") and e["target"] == entry["key"])
        save(mesh_figure(mesh_event["surface"], kw.get("view", (22, -58))), f"{name}-mesh.png")


def mesh_figure(surface, view):
    p = np.asarray(surface["positions"]).reshape(-1, 3)
    t = np.asarray(surface["triangles"]).reshape(-1, 3)
    fig = plt.figure(figsize=(4.2, 3.4))
    ax = fig.add_subplot(projection="3d")
    ax.add_collection3d(Poly3DCollection(p[t], facecolors=(0.86, 0.88, 0.91), edgecolors=(0.2, 0.25, 0.3, 0.55), linewidths=0.15))
    lo, hi = p.min(axis=0), p.max(axis=0)
    span, c = (hi - lo).max(), (lo + hi) / 2
    for setter, i in ((ax.set_xlim, 0), (ax.set_ylim, 1), (ax.set_zlim, 2)):
        setter(c[i] - span / 2, c[i] + span / 2)
    ax.set_box_aspect((1, 1, 1), zoom=1.35)
    ax.view_init(elev=view[0], azim=view[1])
    ax.set_axis_off()
    fig.subplots_adjust(0, 0, 1, 1)
    return fig


def searches() -> None:
    for part, name in (("padeye", "padeye"), ("pipe-bracket", "bracket"), ("stabilizer", "fin")):
        d, res = run(part)
        e = res["designs"][0]
        fig, count = _search_figure(d / "designs-evaluated.csv", e["key"], e["check_report"]["mass_kg"], e["target_utilization"])
        fig.axes[0].set_xlabel("Steel mass (kg)", fontsize=7)
        save(fig, f"{name}-search.png")


def convergence() -> None:
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.3))
    for ax, (part, title) in zip(axes, (("padeye", "Padeye (head region)"), ("pipe-bracket", "Bracket (away from weld line)"),
                                        ("stabilizer", "Fin stock (near bearing)"))):
        _, res = run(part)
        f = res["designs"][0]["fea"]
        x = [lvl["elements"] for lvl in f["levels"]]
        y = [lvl["head_von_mises_mpa"] for lvl in f["levels"]]
        ax.plot(x, y, "-o", color=INK, markersize=3.5, linewidth=1.1)
        if f.get("hand_stress_mpa"):
            ax.axhline(f["hand_stress_mpa"], color=ACCENT, linestyle="--", linewidth=0.9)
            ax.text(x[0], f["hand_stress_mpa"], " hand calculation", fontsize=6, color=ACCENT, va="bottom")
        ax.set_xscale("log")
        ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
        ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
        ax.set_xticks(x)
        ax.tick_params(axis="x", labelsize=6)
        mid, span = np.mean(y), max(max(y) - min(y), np.mean(y) * 0.15)
        lo = min(min(y), f.get("hand_stress_mpa") or min(y))
        hi = max(max(y), f.get("hand_stress_mpa") or max(y))
        ax.set_ylim(lo - span, hi + span)
        ax.set_title(title, fontsize=7.5)
        ax.set_xlabel("Elements", fontsize=7)
        _clean(ax)
        del mid
    axes[0].set_ylabel("Peak von Mises stress (MPa)", fontsize=7)
    fig.tight_layout()
    save(fig, "convergence.png")


def bracket_span() -> None:
    _, res = run("pipe-bracket")
    span = res["designs"][0]["check_report"]["span"]
    sweeps = json.loads((DATA / "sweeps.json").read_text())
    fig, ax = plt.subplots(figsize=(6.6, 2.8))
    s = np.linspace(1.2, 6.5, 300)
    from nemo.parts.bracket.job import BracketJob, span_analysis

    fn = [span_analysis(BracketJob(span_m=float(v)), BracketJob(span_m=float(v)).loads).natural_hz for v in s]
    for e in span["excitations"]:
        ax.axhspan(e["hz"] * 0.8, e["hz"] * 1.2, color="#f3d6d1", alpha=0.6, linewidth=0)
        ax.axhline(e["hz"], color=RED, linewidth=0.7)
        ax.text(6.55, e["hz"], e["name"], fontsize=6, va="center", color="#7a2a1d")
    ax.plot(s, fn, color=ACCENT, linewidth=1.6, label="Pipe span natural frequency")
    for p in sweeps["bracket_span"]:
        ok = p["separation"] >= 0.2
        ax.scatter([p["span_m"]], [p["natural_hz"]], s=18, color=INK if ok else RED, zorder=5)
    ax.axvline(span["recommended_m"], color=MUTED, linestyle="--", linewidth=0.8)
    ax.text(span["recommended_m"], 1.6, f" recommended\n maximum {span['recommended_m']} m", fontsize=6, color=MUTED)
    ax.set_yscale("log")
    ax.set_ylim(1.5, 160)
    ax.set_xlim(1.2, 6.5)
    ax.set_xlabel("Support spacing (m)", fontsize=7)
    ax.set_ylabel("Frequency (Hz)", fontsize=7)
    _clean(ax)
    save(fig, "bracket-span-frequency.png")

    fig, ax1 = plt.subplots(figsize=(5.6, 2.6))
    b = sweeps["bracket"]
    od = [p["od_mm"] for p in b]
    ax1.plot(od, [p["recommended_m"] for p in b], "-o", color=ACCENT, markersize=3.5, label="Recommended spacing")
    ax1.plot(od, [p["spans_m"]["sag"] for p in b], "--", color=MUTED, linewidth=0.9, label="Sag limit")
    ax1.set_xlabel("Pipe outside diameter (mm)", fontsize=7)
    ax1.set_ylabel("Support spacing (m)", fontsize=7)
    ax2 = ax1.twinx()
    ax2.plot(od, [p["mass_kg"] for p in b], "-s", color=INK, markersize=3, label="Bracket mass (3 m spacing)")
    ax2.set_ylabel("Bracket mass (kg)", fontsize=7)
    ax2.tick_params(labelsize=6.5)
    lines = ax1.get_lines() + ax2.get_lines()
    ax1.legend(lines, [ln.get_label() for ln in lines], fontsize=6.5, frameon=False, loc="upper left")
    _clean(ax1)
    save(fig, "bracket-size-sweep.png")


def fin() -> None:
    d, res = run("stabilizer")
    log = json.loads((d / "engineering-log.json").read_text())
    h = next(e for e in log if e["kind"] == "hydro")
    fig, ax = plt.subplots(figsize=(4.6, 2.7))
    up, lo = np.array(h["upper"]), np.array(h["lower"])
    ax.plot(up[:, 0], up[:, 1], color=INK, linewidth=1.1, label="Suction side")
    ax.plot(lo[:, 0], lo[:, 1], color=MUTED, linewidth=1.1, label="Pressure side")
    ax.axhline(-h["cavitation_number"], color=RED, linestyle="--", linewidth=0.9)
    ax.text(0.98, -h["cavitation_number"], f"cavitation, σ = {h['cavitation_number']:.2f}", color=RED, fontsize=6.5, ha="right", va="bottom")
    ax.invert_yaxis()
    ax.set_xlabel("x / c", fontsize=7)
    ax.set_ylabel("Pressure coefficient $C_p$", fontsize=7)
    ax.legend(fontsize=6.5, frameon=False, loc="lower right")
    _clean(ax)
    save(fig, "fin-pressure.png")

    sw = json.loads((DATA / "sweeps.json").read_text())["fin"]
    v = [p["speed_kn"] for p in sw]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.0, 2.6))
    a1.plot(v, [p["nemo_lift_kn"] for p in sw], "-o", color=INK, markersize=3.5, label="Whicker-Fehlner lift")
    a1.plot(v, [p["ur_s10_kn"] for p in sw], "-s", color=MUTED, markersize=3, label="UR S10 rudder force")
    a1.set_xlabel("Ship speed (kn)", fontsize=7)
    a1.set_ylabel("Fin force (kN)", fontsize=7)
    a1.legend(fontsize=6.5, frameon=False)
    _clean(a1)
    a2.plot(v, [p["sigma"] for p in sw], "-o", color=ACCENT, markersize=3.5, label="Cavitation number σ")
    a2.axhline(-sw[0]["cp_min"], color=RED, linestyle="--", linewidth=0.9, label="$-C_{p,min}$ at 22°")
    a2.set_xlabel("Ship speed (kn)", fontsize=7)
    a2.set_ylabel("Pressure ratio", fontsize=7)
    a2.legend(fontsize=6.5, frameon=False)
    _clean(a2)
    fig.tight_layout()
    save(fig, "fin-speed-sweep.png")

    fig, ax = plt.subplots(figsize=(4.6, 2.5))
    ax.plot(v, [p["stock_mm"] for p in sw], "-o", color=INK, markersize=3.5, label="Stock diameter")
    ax.set_xlabel("Ship speed (kn)", fontsize=7)
    ax.set_ylabel("Stock diameter (mm)", fontsize=7)
    ax2 = ax.twinx()
    ax2.plot(v, [p["mass_kg"] for p in sw], "-s", color=ACCENT, markersize=3, label="Fin mass")
    ax2.set_ylabel("Fin mass (kg)", fontsize=7)
    ax2.tick_params(labelsize=6.5)
    lines = ax.get_lines() + ax2.get_lines()
    ax.legend(lines, [ln.get_label() for ln in lines], fontsize=6.5, frameon=False, loc="upper left")
    _clean(ax)
    save(fig, "fin-stock-sweep.png")


def padeye_sweep() -> None:
    sw = json.loads((DATA / "sweeps.json").read_text())["padeye"]
    fig, ax = plt.subplots(figsize=(5.4, 2.7))
    for angle, colour, mark in ((45, RED, "o"), (60, INK, "s"), (90, ACCENT, "^")):
        pts = [p for p in sw if p["angle"] == angle and p["mass_kg"]]
        ax.plot([p["load_t"] for p in pts], [p["mass_kg"] for p in pts], f"-{mark}", color=colour, markersize=3.5,
                linewidth=1.1, label=f"Slings at {angle}°")
    ax.set_xlabel("Load lifted on two padeyes (t)", fontsize=7)
    ax.set_ylabel("Padeye plate mass (kg)", fontsize=7)
    ax.legend(fontsize=6.5, frameon=False)
    _clean(ax)
    save(fig, "padeye-load-sweep.png")


def panel_validation() -> None:
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.0, 2.8))
    xs, ys = circle_contour(160)
    r = panel_solve(xs, ys, 0.0)
    theta = np.arctan2(0.5 * (ys[:-1] + ys[1:]), 0.5 * (xs[:-1] + xs[1:]) - 0.5)
    order = np.argsort(theta)
    a1.plot(np.degrees(theta[order]), r.cp[order], color=INK, linewidth=1.1, label="Panel method, 160 panels")
    tt = np.linspace(-math.pi, math.pi, 300)
    a1.plot(np.degrees(tt), 1 - 4 * np.sin(tt) ** 2, "--", color=ACCENT, linewidth=0.9, label="Exact, $1 - 4\\sin^2\\theta$")
    a1.set_xlabel("Angle round the circle (°)", fontsize=7)
    a1.set_ylabel("$C_p$", fontsize=7)
    a1.legend(fontsize=6.5, frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.02), ncol=2, handlelength=1.6, columnspacing=1.0)
    _clean(a1)
    t = np.linspace(0.08, 0.25, 9)
    a2.plot(t * 100, [section_lift_slope(float(v)) for v in t], "-o", color=INK, markersize=3, label="Panel method")
    a2.plot(t * 100, 2 * math.pi * (1 + 0.77 * t), "--", color=ACCENT, linewidth=0.9, label="$2\\pi(1 + 0.77\\,t/c)$")
    a2.axhline(2 * math.pi, color=MUTED, linewidth=0.7)
    a2.text(8, 2 * math.pi, " thin aerofoil, 2π", fontsize=6, color=MUTED, va="bottom")
    a2.set_xlabel("Section thickness t/c (%)", fontsize=7)
    a2.set_ylabel("Lift slope (per rad)", fontsize=7)
    a2.legend(fontsize=6.5, frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.02), ncol=2, handlelength=1.6, columnspacing=1.0)
    _clean(a2)
    fig.tight_layout()
    save(fig, "panel-validation.png")


def verification_chart() -> None:
    v = json.loads((DATA / "verification.json").read_text())
    rows = [(f"{b['title']}: {c['quantity']}", abs(c["error_percent"]), c["tolerance_percent"]) for b in v["benchmarks"]
            for c in b["comparisons"] if c["tolerance_percent"] >= 0.01 and "reaction" not in c["quantity"].lower()]
    fig, ax = plt.subplots(figsize=(6.8, 0.22 * len(rows) + 0.8))
    y = np.arange(len(rows))[::-1]
    ax.barh(y, [r[2] for r in rows], color="#e8eef8", edgecolor="none", label="Tolerance")
    ax.barh(y, [max(r[1], 1e-4) for r in rows], height=0.45, color=INK, label="NEMO error")
    ax.set_yticks(y)
    ax.set_yticklabels([r[0].replace("_{eff}", "eff").replace("_r", "r") for r in rows], fontsize=5.8)
    ax.set_xscale("log")
    ax.set_xlabel("Error against the reference (%), log scale", fontsize=7)
    ax.legend(fontsize=6.5, frameon=False, loc="lower right")
    _clean(ax)
    save(fig, "verification.png")


if __name__ == "__main__":
    _fonts()
    IMG.mkdir(exist_ok=True)
    models()
    stress()
    searches()
    convergence()
    bracket_span()
    fin()
    padeye_sweep()
    panel_validation()
    verification_chart()
