"""PDF calculation package for the pipe support bracket and the stabilizer fin.

Same layout and page frame as the padeye report (``report_pdf``): summary,
design basis, fabrication drawing, the part's special analysis (pipe span or
foil loads), design search, calculation sheets, FEA, limitations and the
audit trail. Built only from the saved run folder.
"""

from __future__ import annotations

import json
import math
from datetime import datetime
from html import escape
from pathlib import Path

import matplotlib.pyplot as plt
from reportlab.graphics.shapes import Circle, Drawing, Line, PolyLine, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import BaseDocTemplate, CondPageBreak, Frame, KeepTogether, PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle

from . import __version__
from .report_pdf import (
    A4, ACCENT, CONTENT_W, FAIL, FOOTER_H, HEADER_H, INK, MARGIN, MUTED, PAGE_H, PASS, RULE, _clean, _convergence_figure,
    _dim, _fonts, _kv, _NumberedCanvas, _png, _search_figure, _sha256, _status, _styles, _surface_figure, _table, _value,
    _working_table, kn, markup, n,
)

TITLES = {"pipe-bracket": ("Pipe support bracket", "Pipe support bracket calculation"),
          "stabilizer": ("Stabilizer fin", "Stabilizer fin calculation")}


# ------------------------------------------------------------------ drawings
def _hatch(d: Drawing, x0: float, y0: float, x1: float, y1: float, vertical: bool) -> None:
    d.add(Line(x0, y0, x1, y1, strokeColor=INK, strokeWidth=0.7))
    steps = int((abs(y1 - y0) if vertical else abs(x1 - x0)) / 6)
    for i in range(steps + 1):
        if vertical:
            y = y0 + (y1 - y0) * i / max(steps, 1)
            d.add(Line(x0, y, x0 - 4, y - 4, strokeColor=MUTED, strokeWidth=0.35))
        else:
            x = x0 + (x1 - x0) * i / max(steps, 1)
            d.add(Line(x, y0, x - 4, y0 - 4, strokeColor=MUTED, strokeWidth=0.35))


def _bracket_drawing(dz: dict, pipe: dict) -> Drawing:
    width, height = CONTENT_W, 110 * mm
    d = Drawing(width, height)
    d.add(Rect(0, 0, width, height, strokeColor=RULE, strokeWidth=0.6, fillColor=None))
    length, b, ts = dz["seat_length_mm"], dz["seat_width_mm"], dz["seat_thickness_mm"]
    hk, tk, e, od = dz["knee_depth_mm"], dz["knee_thickness_mm"], dz["pipe_offset_mm"], dz["pipe_od_mm"]
    tall = od + ts + hk
    scale = min((width / 2 - 60) / (length + 10), (height - 50) / tall)
    scale = min(scale, (height - 64) / tall)
    ox, oy = 40, 40 + hk * scale

    def P(x, z):
        return ox + x * scale, oy + z * scale

    # Side elevation
    _hatch(d, ox, oy - (hk + ts + 10) * scale, ox, oy + (od + 10) * scale, vertical=True)
    pts = [*P(0, 0), *P(length, 0), *P(length, -ts), *P(0, -ts)]
    d.add(Polygon(pts, fillColor=colors.HexColor("#f2f2f2"), strokeColor=INK, strokeWidth=1.0))
    d.add(Polygon([*P(0, -ts), *P(length, -ts), *P(0, -ts - hk)], fillColor=colors.HexColor("#e9e9e9"), strokeColor=INK, strokeWidth=1.0))
    cx, cy = P(e, od / 2)
    d.add(Circle(cx, cy, od / 2 * scale, fillColor=None, strokeColor=ACCENT, strokeWidth=1.0))
    for x in (e - (od + dz["ubolt_diameter_mm"]) / 2, e + (od + dz["ubolt_diameter_mm"]) / 2):
        x0, y0 = P(x, -ts)
        _, y1 = P(x, od / 2)
        d.add(Line(x0, y0, x0, y1, strokeColor=MUTED, strokeWidth=0.8, strokeDashArray=[3, 2]))
    lx, ly = P(0, -ts - hk)
    rx, _ = P(length, 0)
    _dim(d, lx, ly, rx, ly, f"{length:g}", -12)
    _dim(d, lx, ly, lx, P(0, -ts)[1], f"{hk:g}", -14, horizontal=False)
    ex0, ey = P(0, od + 6)
    d.add(Line(ex0, ey, cx, ey, strokeColor=INK, strokeWidth=0.45))
    d.add(String((ex0 + cx) / 2, ey + 2, f"{e:.0f} to pipe centre", fontName="Inter", fontSize=7, textAnchor="middle", fillColor=INK))
    d.add(String(ox + length * scale / 2, height - 10, "SIDE ELEVATION", fontName="Inter-Medium", fontSize=7, textAnchor="middle", fillColor=MUTED))

    # Plan
    px0 = width / 2 + 30
    s2 = min((width / 2 - 70) / (length + 10), (height - 50) / (b + 10))

    def Q(x, y):
        return px0 + x * s2, height / 2 + y * s2

    _hatch(d, px0, Q(0, -b / 2 - 8)[1], px0, Q(0, b / 2 + 8)[1], vertical=True)
    d.add(Polygon([*Q(0, -b / 2), *Q(length, -b / 2), *Q(length, b / 2), *Q(0, b / 2)], fillColor=colors.HexColor("#f2f2f2"), strokeColor=INK, strokeWidth=1.0))
    for side in (-1, 1):
        y0 = side * (b / 2 - tk)
        d.add(Line(*Q(0, y0), *Q(length, y0), strokeColor=MUTED, strokeWidth=0.5, strokeDashArray=[3, 2]))
    for x in (e - (od + dz["ubolt_diameter_mm"]) / 2, e + (od + dz["ubolt_diameter_mm"]) / 2):
        hx, hy = Q(x, 0)
        d.add(Circle(hx, hy, (dz["ubolt_diameter_mm"] + 2) / 2 * s2, fillColor=colors.white, strokeColor=INK, strokeWidth=0.8))
    ax0, ay = Q(0, -b / 2)
    ax1, _ = Q(length, -b / 2)
    _dim(d, ax0, ay, ax1, ay, f"{length:g}", -10)
    bx, by0 = Q(length, -b / 2)
    _, by1 = Q(length, b / 2)
    _dim(d, bx, by0, bx, by1, f"{b:g}", 14, horizontal=False)
    d.add(String(px0 + length * s2 / 2, height - 10, "PLAN ON SEAT", fontName="Inter-Medium", fontSize=7, textAnchor="middle", fillColor=MUTED))
    d.add(String(8, 8, f"All dimensions in mm. Seat {ts:g} mm, knees 2 × {tk:g} mm flush with the seat edges (dashed). "
                       f"Pipe {pipe['label']}. Do not scale.", fontName="Inter", fontSize=6.5, fillColor=MUTED))
    return d


def _fin_drawing(dz: dict, outline: list) -> Drawing:
    width, height = CONTENT_W, 100 * mm
    d = Drawing(width, height)
    d.add(Rect(0, 0, width, height, strokeColor=RULE, strokeWidth=0.6, fillColor=None))
    c, span = dz["chord_mm"], dz["span_mm"]
    scale = (width * 0.55 - 30) / c
    ox, oy = 20, height * 0.55

    def P(x, y):
        return ox + x * scale, oy + y * scale

    pts = []
    for x, y in outline:
        pts += list(P(x, y))
    d.add(Polygon(pts, fillColor=colors.HexColor("#f2f2f2"), strokeColor=INK, strokeWidth=1.0))
    for frac in (dz["front_spar"], dz["rear_spar"]):
        half = [abs(y) for x, y in outline if abs(x - frac * c) < c / 80] or [0]
        x0, y0 = P(frac * c, -max(half))
        _, y1 = P(frac * c, max(half))
        d.add(Line(x0, y0, x0, y1, strokeColor=INK, strokeWidth=max(dz["web_mm"] * scale, 0.8)))
    sx, sy = P(dz["stock_position"] * c, 0)
    d.add(Circle(sx, sy, dz["stock_diameter_mm"] / 2 * scale, fillColor=colors.HexColor("#d9d9d9"), strokeColor=INK, strokeWidth=0.8))
    lx, ly = P(0, -max(abs(y) for _, y in outline) - 8)
    rx, _ = P(c, 0)
    _dim(d, lx, ly, rx, ly, f"{c:g} chord", -10)
    d.add(String(ox + c * scale / 2, height - 10, "SECTION THROUGH THE FIN", fontName="Inter-Medium", fontSize=7, textAnchor="middle", fillColor=MUTED))
    # Planform
    px0 = width * 0.62
    s2 = min((width * 0.36 - 20) / c, (height - 40) / (span + dz["bearing_gap_mm"]))
    base = 22

    def Q(x, z):
        return px0 + x * s2, base + (z + dz["bearing_gap_mm"]) * s2

    d.add(Polygon([*Q(0, 0), *Q(c, 0), *Q(c, span), *Q(0, span)], fillColor=colors.HexColor("#f2f2f2"), strokeColor=INK, strokeWidth=1.0))
    pitch = dz["span_mm"] / max(math.ceil(span / dz["rib_spacing_mm"] - 1e-9), 1)
    z = 0.0
    while z <= span + 1e-6:
        d.add(Line(*Q(0, z), *Q(c, z), strokeColor=MUTED, strokeWidth=0.6))
        z += pitch
    xs = dz["stock_position"] * c
    d.add(Rect(Q(xs, 0)[0] - dz["stock_diameter_mm"] / 2 * s2, Q(0, -dz["bearing_gap_mm"])[1], dz["stock_diameter_mm"] * s2,
               (dz["bearing_gap_mm"] + 0.5 * span) * s2, fillColor=colors.HexColor("#d9d9d9"), strokeColor=INK, strokeWidth=0.6))
    hx0, hy = Q(-0.1 * c, 0)
    d.add(Line(hx0, hy, Q(1.1 * c, 0)[0], hy, strokeColor=INK, strokeWidth=0.9))
    d.add(String(Q(1.1 * c, 0)[0] + 2, hy - 2, "hull", fontName="Inter", fontSize=6.5, fillColor=MUTED))
    d.add(String(px0 + c * s2 / 2, height - 10, "PLANFORM, RIBS AND STOCK", fontName="Inter-Medium", fontSize=7, textAnchor="middle", fillColor=MUTED))
    d.add(String(8, 8, "All dimensions in mm. Spars shown at their chord positions; the stock runs from the outer bearing to mid-span.",
                 fontName="Inter", fontSize=6.5, fillColor=MUTED))
    return d


# --------------------------------------------------------------- figures
def _frequency_figure(span: dict):
    fig, ax = plt.subplots(figsize=(6.6, 2.0))
    names = [e["name"] for e in span["excitations"]]
    freqs = [e["hz"] for e in span["excitations"]]
    for i, f in enumerate(freqs):
        ax.axvspan(f * 0.8, f * 1.2, ymin=0, ymax=1, color="#f3d6d1", alpha=0.6, linewidth=0)
        ax.axvline(f, color="#c0341d", linewidth=0.8)
        ax.text(f, 1.02 + 0.12 * (i % 2), names[i], rotation=0, fontsize=6, ha="center", transform=ax.get_xaxis_transform(), color="#7a2a1d")
    ax.axvline(span["natural_hz"], color="#0a6fd6", linewidth=2.0)
    ax.text(span["natural_hz"], 0.5, f"  pipe span {span['natural_hz']:.1f} Hz", color="#0a6fd6", fontsize=7, transform=ax.get_xaxis_transform())
    ax.set_yticks([])
    ax.set_xlim(0, max(freqs + [span["natural_hz"]]) * 1.35)
    ax.set_xlabel("Frequency (Hz). Shaded: within 20% of an excitation", fontsize=7)
    _clean(ax)
    ax.spines["left"].set_visible(False)
    return fig


def _cp_figure(hydro: dict):
    fig, ax = plt.subplots(figsize=(4.2, 2.6))
    up = list(zip(*hydro["upper"]))
    lo = list(zip(*hydro["lower"]))
    ax.plot(up[0], up[1], color="#1a1a1a", linewidth=1.1, label="Suction side")
    ax.plot(lo[0], lo[1], color="#8a8a8a", linewidth=1.1, label="Pressure side")
    ax.axhline(-hydro["cavitation_number"], color="#c0341d", linestyle="--", linewidth=0.9)
    ax.text(0.98, -hydro["cavitation_number"], " cavitation", color="#c0341d", fontsize=6.5, ha="right", va="bottom")
    ax.invert_yaxis()
    ax.set_xlabel("Position along the chord, x/c", fontsize=7)
    ax.set_ylabel("Pressure coefficient C_p", fontsize=7)
    ax.legend(fontsize=6.5, frameon=False)
    _clean(ax)
    return fig


# ------------------------------------------------------------------ report
def build_part_report(run_dir: Path, results: dict, design_key: str, *, project_name: str, run_name: str, target: Path) -> Path:
    _fonts()
    s = _styles()
    part = results["part"]
    title, kind = TITLES[part]
    entry = next((x for x in results["designs"] if x["key"] == design_key), None)
    if entry is None:
        raise KeyError(design_key)
    report, dz, fea = entry["check_report"], entry["check_report"]["design"], entry.get("fea")
    rule, material, loads, job = results["rule_set"], results["material"], results["loads"], results["job"]
    created = results.get("created_at", "")
    date = datetime.fromisoformat(created).astimezone().strftime("%d %b %Y") if created else datetime.now().strftime("%d %b %Y")
    doc_no = f"NEMO-{run_name[:8]}-{run_name[9:15]}-{design_key[:1].upper()}"
    meta = {"project": project_name, "doc": doc_no, "rev": "A", "date": date, "design": entry["label"].split(" (")[0], "kind": kind}
    surface = None
    if entry["files"].get("stress_surface") and (run_dir / entry["files"]["stress_surface"]).exists():
        surface = json.loads((run_dir / entry["files"]["stress_surface"]).read_text(encoding="utf-8"))
    log_path = run_dir / "engineering-log.json"
    events = json.loads(log_path.read_text(encoding="utf-8")) if log_path.exists() else []
    governing = next(c for c in report["checks"] if c["id"] == report["governing"])
    passed = report["passed"]
    fea_ok = bool(fea and fea["converged"] and fea["factor_of_safety_on_yield"] >= 1.0)
    story: list = []

    # ------------------------------------------------------------ 1 Summary
    story += [Spacer(1, 6 * mm), Paragraph(title, s["title"]),
              Paragraph(f"{escape(entry['label'])} design for {escape(project_name)}", s["subtitle"]), Spacer(1, 6 * mm)]
    failing = [c for c in report["checks"] if c["severity"] == "required" and not c["passed"]]
    note = "" if passed else " Failing: " + ", ".join(escape(c["title"]) for c in failing) + "."
    box = Table([[Paragraph(
        f"<font color='{(PASS if passed else FAIL).hexval()}'><b>{'Passes' if passed else 'Does not pass'} every required check</b></font>"
        f"<br/><font size=7.6 color='#5c5c5c'>Governing check: {escape(governing['title'])}, {governing['utilization'] * 100:.0f}% of capacity. "
        f"Stress check: {'pass' if fea_ok else ('not run' if not fea else 'review')}.{note}</font>", s["body"])]], colWidths=[CONTENT_W])
    box.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.9, PASS if passed else FAIL), ("LEFTPADDING", (0, 0), (-1, -1), 8),
                             ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    story += [box, Spacer(1, 5 * mm)]
    if part == "pipe-bracket":
        span = report["span"]
        rows = [("Pipe", report["pipe"]["label"] + ", " + report["pipe"]["material"]),
                ("Support spacing", f"{job['span_m']:g} m (NEMO's recommended maximum {span['recommended_m']:.1f} m)"),
                ("Downward design force", f"{kn(loads['down_n'])} ({n(1 + job['accel_vertical_g'], 2)} g)"),
                ("Seat plate", f"{dz['seat_length_mm']:g} × {dz['seat_width_mm']:g} × {dz['seat_thickness_mm']:g} mm"),
                ("Knees", f"2 × {dz['knee_thickness_mm']:g} mm, {dz['knee_depth_mm']:g} mm deep at the bulkhead"),
                ("U-bolt", report["ubolt"]["label"]),
                ("Welds", f"{dz['root_weld_mm']:g} mm to the bulkhead, {dz['knee_weld_mm']:g} mm knees to seat"),
                ("Steel mass", f"{n(report['mass_kg'], 2)} kg {material['name']}")]
    else:
        m = report["masses_kg"]
        rows = [("Fin", f"{dz['span_mm']:g} mm span × {dz['chord_mm']:g} mm chord, NACA 00{dz['thickness_ratio'] * 100:.0f}"),
                ("Design force", f"{kn(loads['design_force_n'])} at {job['max_angle_deg']:g}°, {job['speed_kn']:g} kn"),
                ("Skin / webs", f"{dz['skin_mm']:g} mm / {dz['web_mm']:g} mm {material['name']}"),
                ("Ribs", f"{report['ribs']} at {report['rib_pitch_mm']:.0f} mm"),
                ("Stock", f"Ø{dz['stock_diameter_mm']:g} mm {report['stock_material']['name']}"),
                ("Mass", f"{n(m['total'], 1)} kg (structure {n(m['total'] - m['stock'], 1)} kg, stock {n(m['stock'], 1)} kg)")]
    rows.append(("Design rules", rule["name"]))
    if fea:
        rows.append(("Peak stress (FEA)", f"{n(fea['head_von_mises_mpa'], 1)} MPa, {escape(fea['region'])}"))
    left = _kv(rows, s, widths=(38 * mm, 64 * mm))
    if surface:
        img = _png(_surface_figure(surface, stress=False, yield_mpa=1, width_in=3.1, height_in=3.1), 70)
        story.append(Table([[left, img]], colWidths=[104 * mm, CONTENT_W - 104 * mm], style=[("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    else:
        story.append(left)
    sections = ["1  Summary", "2  Design basis", "3  Fabrication drawing",
                "4  Pipe span and vibration" if part == "pipe-bracket" else "4  Foil loads and cavitation",
                "5  Design search", "6  Calculation sheets", "7  Finite element analysis", "8  Fusion cross-check",
                "9  Limitations", "A  Audit trail"]
    story += [Spacer(1, 6 * mm), Paragraph("Contents", s["h2"]), Paragraph("<br/>".join(sections), s["body"]), Spacer(1, 6 * mm),
              Paragraph("Revision history", s["h2"]),
              _table([["Rev", "Date", "Description", "By"], ["A", date, "First issue, generated from run " + run_name, f"NEMO {__version__}"]],
                     [12 * mm, 26 * mm, CONTENT_W - 68 * mm, 30 * mm]),
              Spacer(1, 4 * mm),
              Paragraph("This calculation is a design aid. A competent engineer must review it, with the supporting structure and the "
                        "welding procedure, before the part is made or fitted. The vessel's classification society can require other "
                        "rules and change the result.", s["small"]), PageBreak()]

    # ------------------------------------------------------- 2 Design basis
    story.append(Paragraph("2  Design basis", s["h1"]))
    story.append(Paragraph("2.1  Forces", s["h2"]))
    story.append(_working_table(results.get("load_steps", []), s))
    story.append(Paragraph("2.2  Materials", s["h2"]))
    mats = [("Plate", f"{material['name']}. {material['source']}"),
            ("Elastic modulus, density", f"{n(material['elastic_modulus_gpa'], 0)} GPa, {n(material['density_kg_m3'], 0)} kg/m³")]
    if part == "stabilizer":
        st = results["stock_material"]
        mats.append(("Stock", f"{st['name']}. {st['source']}"))
        mats.append(("Material factors k", f"plate {n(report['values']['k_plate'], 3)}, stock {n(report['values']['k_stock'], 3)} (UR S10.1.3.5)"))
    story.append(_kv(mats, s))
    story.append(Paragraph("2.3  Design rules", s["h2"]))
    if part == "pipe-bracket":
        story.append(_kv([("Rule set", rule["name"]),
                          ("Safety factors Ω", f"tension {rule['omega_tension']}, flexure {rule['omega_flexure']}, shear {rule['omega_shear']}, "
                                               f"welds {rule['omega_weld']}, bolts {rule['omega_bolt']}"),
                          ("Ship motions", f"vertical {job['accel_vertical_g']:g} g, athwartships {job['accel_transverse_g']:g} g, "
                                           f"fore and aft {job['accel_longitudinal_g']:g} g, entered for this job"),
                          ("Weld metal, F_EXX", f"{n(job['electrode_strength_mpa'], 0)} MPa (E70XX class)")], s))
        story.append(Paragraph("The ship-motion accelerations are inputs. Confirm them against the vessel's class rules or design basis.", s["caption"]))
    else:
        story.append(_kv([("Rule set", rule["name"]),
                          ("Load model", "Whicker and Fehlner (1958) low-aspect-ratio lift, compared with UR S10.2 rudder force; the larger is used"),
                          ("Hydrodynamic pressure", "Hess-Smith panel method of the NACA section (NEMO, verified against exact solutions)")], s))
    story.append(PageBreak())

    # -------------------------------------------------- 3 Fabrication drawing
    story.append(Paragraph("3  Fabrication drawing", s["h1"]))
    density = material["density_kg_m3"] * 1e-9
    if part == "pipe-bracket":
        story.append(_bracket_drawing(dz, report["pipe"]))
        seat_mass = (dz["seat_length_mm"] * dz["seat_width_mm"] - 2 * math.pi * (dz["ubolt_diameter_mm"] + 2) ** 2 / 4) * dz["seat_thickness_mm"] * density
        knee_mass = 0.5 * dz["seat_length_mm"] * dz["knee_depth_mm"] * dz["knee_thickness_mm"] * density
        parts = [["Item", "Part", "Material", "Thickness", "Qty", "Mass each"],
                 ["1", f"Seat plate {dz['seat_length_mm']:g} × {dz['seat_width_mm']:g}, two Ø{dz['ubolt_diameter_mm'] + 2:g} holes", material["name"], f"{dz['seat_thickness_mm']:g} mm", "1", f"{n(seat_mass, 2)} kg"],
                 ["2", f"Knee, triangle {dz['seat_length_mm']:g} × {dz['knee_depth_mm']:g}", material["name"], f"{dz['knee_thickness_mm']:g} mm", "2", f"{n(knee_mass, 2)} kg"],
                 ["3", report["ubolt"]["label"] + ", with nuts and washers", "", "", "1", ""]]
        notes = [f"Weld seat and knees to the bulkhead with {dz['root_weld_mm']:g} mm fillets on both sides.",
                 f"Weld the knees to the seat with {dz['knee_weld_mm']:g} mm fillets on both sides, full length.",
                 "The bulkhead behind the bracket must be checked for the same forces; fit a backing stiffener if it is thin plate.",
                 "Snipe the knee toe and the bracket corners to clear existing welds where needed.",
                 "Cutting profiles are supplied as DXF at full size (layer CUT)."]
    else:
        story.append(_fin_drawing(dz, json.loads(json.dumps(_fin_outline(dz)))))
        m = report["masses_kg"]
        parts = [["Item", "Part", "Material", "Thickness", "Qty", "Mass"],
                 ["1", "Skin plating, both sides", material["name"], f"{dz['skin_mm']:g} mm", "1 set", f"{n(m['skin'], 1)} kg"],
                 ["2", f"Spars at {dz['front_spar'] * 100:.0f}% and {dz['rear_spar'] * 100:.0f}% chord", material["name"], f"{dz['web_mm']:g} mm", "2", f"{n(m['spars'], 1)} kg"],
                 ["3", "Ribs, profile cut", material["name"], f"{dz['web_mm']:g} mm", str(report["ribs"]), f"{n(m['ribs'], 1)} kg"],
                 ["4", f"Stock Ø{dz['stock_diameter_mm']:g}", report["stock_material"]["name"], "", "1", f"{n(m['stock'], 1)} kg"]]
        notes = ["Weld the skin to spars and ribs as UR S10.1.4 requires; use full penetration welds to heavy parts.",
                 "The stock-to-fin connection (hub, cone or flange) is not designed here; it needs its own calculation.",
                 "Rib profiles are supplied as DXF at full size (layer CUT)."]
    story += [Spacer(1, 4 * mm), Paragraph("Parts list", s["h2"]),
              _table([row if i == 0 else [row[0], Paragraph(escape(row[1]), s["cell"]), Paragraph(escape(row[2]), s["cell"]), *row[3:]] for i, row in enumerate(parts)],
                     [12 * mm, 70 * mm, 50 * mm, 18 * mm, 14 * mm, CONTENT_W - 164 * mm], align_right=(3, 4, 5)),
              Paragraph("Notes", s["h2"]), Paragraph("<br/>".join(f"{i}.  {escape(t)}" for i, t in enumerate(notes, 1)), s["body"]), PageBreak()]

    # ------------------------------------------------- 4 Special analysis
    if part == "pipe-bracket":
        span = report["span"]
        story.append(Paragraph("4  Pipe span and vibration", s["h1"]))
        story.append(Paragraph("The pipe between two supports is a beam. Its natural frequency must stay clear of the frequencies the "
                               "propeller and the engine shake the ship at, and it must not bend or sag too much.", s["body"]))
        story.append(_png(_frequency_figure(span), CONTENT_W / mm))
        story.append(_working_table(span["steps"], s))
        story.append(Paragraph("Excitation frequencies", s["h2"]))
        story.append(_table([["Source", "Frequency", "Separation from the pipe span"]] +
                            [[e["name"], f"{n(e['hz'], 2)} Hz", f"{abs(span['natural_hz'] - e['hz']) / e['hz'] * 100:.0f}%"] for e in span["excitations"]],
                            [70 * mm, 30 * mm, CONTENT_W - 100 * mm], align_right=(1, 2)))
    else:
        hydro = next((e for e in events if e["kind"] == "hydro"), None)
        story.append(Paragraph("4  Foil loads and cavitation", s["h1"]))
        story.append(Paragraph(
            f"NEMO's foil model gives {kn(loads['nemo_lift_n'])} and UR S10's rudder formula gives {kn(loads['ur_s10_force_n'])}; "
            f"the structure is designed for the larger, {kn(loads['design_force_n'])}. The pressure around the section comes from the panel method "
            f"at the 2D angle that gives the same lift ({loads['section_angle_deg']:.1f}°).", s["body"]))
        if hydro:
            story.append(_png(_cp_figure(hydro), 110))
            story.append(Paragraph(f"Lowest pressure coefficient {loads['cp_min']:.2f} against cavitation number {loads['cavitation_number']:.2f} "
                                   f"at {job['depth_m']:g} m depth. Cavitation starts where the curve crosses the dashed line.", s["caption"]))
    story.append(PageBreak())

    # --------------------------------------------------- 5 Design search
    story.append(Paragraph("5  Design search", s["h1"]))
    search = results["search"]
    method = ("For every pair of stock plates (seat, knees) a bounded Nelder-Mead search sized the knee depth and seat width for the least steel."
              if part == "pipe-bracket" else
              "For every pair of stock plates (skin, webs) NEMO tried every rib spacing from 150 to 1000 mm in 25 mm steps and sized the stock to UR S10.")
    story.append(Paragraph(f"{method} In total it checked {n(search['evaluations'], 0)} designs across {search['combinations']} combinations.", s["body"]))
    csv_path = run_dir / "designs-evaluated.csv"
    if csv_path.exists():
        fig, count = _search_figure(csv_path, design_key, report["mass_kg"], entry["target_utilization"])
        story += [Spacer(1, 3 * mm), _png(fig, CONTENT_W / mm), Paragraph(f"Each dot is one of the {n(count, 0)} designs tried for this target.", s["caption"])]
    rows = [["Design", "Mass", "Highest use", "Governing check"]]
    for other in results["designs"]:
        orp = other["check_report"]
        og = next(c for c in orp["checks"] if c["id"] == orp["governing"])
        rows.append([other["label"].split(" (")[0] + (" (this report)" if other["key"] == design_key else ""),
                     f"{n(orp['mass_kg'], 2)} kg", f"{og['utilization'] * 100:.0f}%", og["title"]])
    story += [Paragraph("Designs offered", s["h2"]), _table(rows, [50 * mm, 26 * mm, 26 * mm, CONTENT_W - 102 * mm], align_right=(1, 2)), PageBreak()]

    # ----------------------------------------------- 6 Calculation sheets
    story.append(Paragraph("6  Calculation sheets", s["h1"]))
    story.append(Paragraph("Use = demand / capacity; up to 100% passes. Practice checks are workshop or industry rules, not code "
                           "clauses. Advice items do not fail the design on their own.", s["body"]))
    rows = [["", "Check", "Demand", "Capacity", "Use", "Result"]]
    extra = []
    for i, c in enumerate(report["checks"], 1):
        label, colour = _status(c)
        rows.append([f"6.{i}", Paragraph(markup(c["title"]), s["cell"]), _value(c["demand"], c["unit"]), _value(c["capacity"], c["unit"]),
                     f"{c['utilization'] * 100:.0f}%", label])
        extra += [("TEXTCOLOR", (5, i), (5, i), colour), ("FONT", (5, i), (5, i), "Inter-SemiBold", 7.4)]
    story += [Spacer(1, 2 * mm), _table(rows, [11 * mm, 74 * mm, 26 * mm, 26 * mm, 16 * mm, CONTENT_W - 153 * mm], align_right=(2, 3, 4), style_extra=extra)]
    for i, c in enumerate(report["checks"], 1):
        label, colour = _status(c)
        block = [Paragraph(f"6.{i}  {markup(c['title'])}", s["h2"]), Paragraph(f"{escape(c['source'])}. {escape(c['explanation'])}", s["small"]), Spacer(1, 1.5 * mm)]
        if c.get("working"):
            block.append(_working_table(c["working"], s))
        block += [Spacer(1, 1.2 * mm), Paragraph(
            f"Demand {_value(c['demand'], c['unit'])} against capacity {_value(c['capacity'], c['unit'])}: use {c['utilization'] * 100:.1f}%  "
            f"<font color='{colour.hexval()}'><b>{label}</b></font>", s["body"])]
        story += [CondPageBreak(42 * mm), KeepTogether(block)]
    story.append(PageBreak())

    # ------------------------------------------------------------ 7 FEA
    story.append(Paragraph("7  Finite element analysis", s["h1"]))
    if not fea:
        story.append(Paragraph("The stress check was not run for this design.", s["body"]))
    else:
        if part == "pipe-bracket":
            model = [("Geometry", "The exported STEP solid: seat plate and both knees as one body. Welds not modelled."),
                     ("Support", "Faces against the bulkhead fixed in all directions"),
                     ("Load", f"F_z = {kn(loads['down_n'])} down, F_x = {kn(loads['across_n'])} across and F_y = {kn(loads['along_n'])} along the pipe, "
                              f"spread over a {fea['load_strip_mm']:.0f} mm strip of the seat under the pipe")]
        else:
            model = [("Geometry", "The stock: a solid shaft from the outer bearing to 0.6 of the span. The fin body is a thin box that the "
                                  "hand calculation covers (section 6)."),
                     ("Support", "Stock fixed at the outer bearing"),
                     ("Load", f"F = {kn(loads['design_force_n'])} and Q = {n(loads['torque_nm'] / 1000, 2)} kN·m spread over the stock between 0.4 and 0.6 of the span")]
        model += [("Elements", "Quadratic tetrahedra (10-node), linear elastic"), ("Assessed region", fea["region"])]
        story += [Paragraph("7.1  Model", s["h2"]), _kv(model, s), Paragraph("7.2  Mesh convergence", s["h2"])]
        mrows = [["Mesh", "Element size", "Elements", "Equations", "Peak stress", "Largest movement", "Solve time"]]
        for lvl in fea["levels"]:
            mrows.append([str(lvl["level"]), f"{n(lvl['global_size_mm'], 1)} mm", n(lvl["elements"], 0), n(lvl["dofs"], 0),
                          f"{n(lvl['head_von_mises_mpa'], 1)} MPa", f"{n(lvl['max_displacement_mm'], 4)} mm", f"{n(lvl['solve_seconds'], 1)} s"])
        story.append(_table(mrows, [11 * mm, 26 * mm, 20 * mm, 22 * mm, 30 * mm, 30 * mm, CONTENT_W - 139 * mm], align_right=(2, 3, 4, 5, 6)))
        conv = _png(_convergence_figure(fea["levels"]), 80)
        hand = fea.get("hand_stress_mpa")
        compare = (f" Hand calculation for the same place ({escape(fea.get('hand_label') or 'beam theory')}): {n(hand, 1)} MPa, "
                   f"{(fea['head_von_mises_mpa'] / hand - 1) * 100:+.0f}% from the FEA.") if hand else ""
        story.append(Table([[conv, Paragraph(
            f"The peak stress changed by <b>{fea['convergence_change'] * 100:.2f}%</b> between the two finest meshes (target 5% or less).{compare}",
            s["body"])]], colWidths=[84 * mm, CONTENT_W - 84 * mm], style=[("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
        if surface:
            story += [CondPageBreak(90 * mm), Paragraph("7.3  Stress contours", s["h2"]),
                      _png(_surface_figure(surface, stress=True, yield_mpa=fea["yield_strength_mpa"], width_in=5.0, height_in=3.4), 130),
                      Paragraph(f"Von Mises stress on the finest mesh, scale 0 to yield ({n(fea['yield_strength_mpa'], 0)} MPa).", s["caption"])]
        last = fea["levels"][-1]
        ap, re_ = last["applied_force_n"], last["reaction_force_n"]
        story += [Paragraph("7.4  Force balance", s["h2"]),
                  _table([["", "X", "Y", "Z"], ["Applied load", *map(kn, ap)], ["Support reaction", *map(kn, re_)],
                          ["Sum", *(kn(0.0 if abs(a + b) < 0.5 else a + b) for a, b in zip(ap, re_))]],
                         [40 * mm] + [(CONTENT_W - 40 * mm) / 3] * 3, align_right=(1, 2, 3)),
                  Paragraph(f"Relative balance error {last['reaction_balance_error']:.1e}.", s["caption"]),
                  Paragraph("7.5  Result", s["h2"]),
                  Paragraph(f"Peak von Mises stress {n(fea['head_von_mises_mpa'], 1)} MPa against yield {n(fea['yield_strength_mpa'], 0)} MPa: "
                            f"safety factor on yield <b>{n(fea['factor_of_safety_on_yield'], 2)}</b>. "
                            f"<font color='{(PASS if fea_ok else FAIL).hexval()}'><b>{'PASS' if fea_ok else 'REVIEW'}</b></font>.", s["body"])]
    story.append(PageBreak())

    # ---------------------------------------------- 8 Fusion cross-check
    story += _fusion_section(part, results, entry, s)

    # --------------------------------------------------- 9 Limitations
    story.append(Paragraph("9  Limitations", s["h1"]))
    if part == "pipe-bracket":
        limits = ["The bulkhead or deck the bracket is welded to must be checked separately for the same forces.",
                  "Ship-motion accelerations are inputs; they are not calculated from a class rule.",
                  "The support is a sliding guide. Pipe anchors, thermal expansion and water hammer loads are not covered.",
                  "The pipe span frequency assumes rigid supports and a simply supported span; flexible brackets lower it.",
                  "Fatigue of the welds under vibration is not checked.",
                  "No corrosion allowance is included."]
    else:
        limits = ["The hull structure around the fin, the bearings and the stock housing are not designed here.",
                  "The stock-to-fin connection (hub, cone or flange) needs its own calculation.",
                  "The load model is quasi-static; dynamic fin motion, slamming and fatigue are not covered.",
                  "The fin body is checked as a box girder by hand calculation; only the stock has a 3D stress model.",
                  "Cavitation is an estimate from 2D section pressures; tip vortex cavitation is not covered."]
    story += [Paragraph("<br/>".join(f"{i}.  {escape(t)}" for i, t in enumerate(limits, 1)), s["body"]), PageBreak()]

    # ------------------------------------------------------ A Audit trail
    story.append(Paragraph("A  Audit trail", s["h1"]))
    start = next((e for e in events if e["kind"] == "start"), {})
    story += [Paragraph("Software", s["h2"]),
              _kv([("NEMO", __version__), ("Python", start.get("python", "-")), ("Run", run_name), ("Run time", f"{n(results.get('seconds', 0), 1)} s")], s),
              Paragraph("Inputs as entered", s["h2"]),
              _kv([(k.replace("_", " "), ", ".join(f"{v:g}" for v in val) if isinstance(val, list) else str(val)) for k, val in job.items() if k != "part"], s)]
    files = [("results.json", "Summary of the run")] + [(entry["files"][k], d) for k, d in (("step", "3D model"), ("dxf", "Cutting profile"), ("stl", "Mesh for viewing"))]
    files += [("engineering-log.json", "Every engineering event"), ("designs-evaluated.csv", "Every design the search tried")]
    frows = [["File", "Contents", "SHA-256 (first 16)"]]
    for rel, desc in files:
        path = run_dir / rel
        if path.exists():
            frows.append([Paragraph(escape(rel.replace("\\", "/")), s["cell"]), desc, _sha256(path)[:16]])
    story += [Paragraph("Files in this run", s["h2"]), _table(frows, [70 * mm, 52 * mm, CONTENT_W - 122 * mm])]

    target.parent.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(str(target), pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN, topMargin=MARGIN + HEADER_H + 5 * mm,
                          bottomMargin=MARGIN + FOOTER_H + 5 * mm, title=f"{project_name} - {title.lower()} calculation",
                          author=f"NEMO {__version__}", subject=doc_no)
    frame = Frame(MARGIN, MARGIN + FOOTER_H + 5 * mm, CONTENT_W, PAGE_H - 2 * MARGIN - HEADER_H - FOOTER_H - 10 * mm,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="page", frames=[frame])])
    doc.build(story, canvasmaker=lambda *a, **k: _NumberedCanvas(*a, meta=meta, **k))
    return target


# ------------------------------------------------------- Fusion cross-check
GRADE_LABELS = {"GRADE_A": "Grade A", "AH36": "AH36", "42CRMO4_QT": "42CrMo4", "AL5083_H111": "5083-H111"}


def _material_text(material: dict, yield_mpa: float) -> str:
    from .data import get_material

    nu = get_material(material["id"]).poisson_ratio
    grade = GRADE_LABELS.get(material["id"], material["id"].replace("_", " "))
    return (f"{material['name']}: E {n(material['elastic_modulus_gpa'], 0)} GPa, Poisson's ratio {nu:.2f}, density "
            f"{n(material['density_kg_m3'], 0)} kg/m\u00b3, yield {n(yield_mpa, 0)} MPa, ultimate "
            f"{n(material['tensile_strength_mpa'], 0)} MPa. Fusion's library has no {grade}, and its generic Steel has a "
            "207 MPa yield: copy Steel (Manage Physical Materials, pencil-and-arrow icon), enter these values on its "
            "Physical tab, then choose the copy in Study Materials")


def _fusion_section(part: str, results: dict, entry: dict, s: dict) -> list:
    """Section 8: the values for repeating NEMO's stress check in Autodesk Fusion by hand, from the STEP file."""
    fea = entry.get("fea")
    dz = entry["check_report"]["design"]
    out: list = [Paragraph("8  Fusion cross-check", s["h1"])]
    if not fea:
        return out + [Paragraph("The stress check was not run for this design, so there is nothing to compare.", s["body"])]
    last = fea["levels"][-1]
    ap = last["applied_force_n"]
    total = math.sqrt(sum(v * v for v in ap))
    finest = last.get("global_size_mm") or 0.0
    if part == "pipe-bracket":
        e = dz["pipe_offset_mm"]
        strip = fea.get("load_strip_mm") or 0.0
        keep_out = 1.5 * max(dz["seat_thickness_mm"], dz["knee_thickness_mm"])
        intro = ("Use these values to repeat the stress check independently in Autodesk Fusion (Simulation, Static Stress). "
                 f"Open {escape(entry['files']['step'].replace(chr(92), '/').split('/')[-1])} from this run, in millimetres.")
        rows = [
            ["1", "Study type", "Static Stress"],
            ["2", "Axes", "As in the STEP file: x out from the bulkhead, y along the pipe, z up; the seat top is at z = 0"],
            ["3", "Material", _material_text(results["material"], fea["yield_strength_mpa"])],
            ["4", "Fixed constraint", "Every face lying on the bulkhead (x = 0): the end of the seat and the ends of both knees"],
            ["5", "Load face", f"Split the seat top face (Design, Modify, Split Face) with planes at x = {n(e - strip / 2, 1)} mm and "
                              f"x = {n(e + strip / 2, 1)} mm. The strip between them, {n(strip, 1)} mm wide under the pipe, carries the load"],
            ["6", "Force on the strip", f"X {kn(ap[0])}, Y {kn(ap[1])}, Z {kn(ap[2])} (total {kn(total)})"],
            ["7", "Mesh", f"Element size about {n(finest, 1)} mm, finer near the bulkhead; at least 3 elements through each plate"],
            ["8", "Reaction", f"Total of the Reaction Force result equals {kn(total)} within 2%"],
            ["9", "Peak stress", f"Probe the von Mises stress at x \u2265 {n(keep_out, 0)} mm, clear of the bulkhead face, not the legend "
                                 f"maximum (that sits on the fixed edges). NEMO found {n(fea['head_von_mises_mpa'], 1)} MPa; within 15% agrees. "
                                 f"Hand value for the seat between the knees: {n(fea.get('hand_stress_mpa') or 0, 1)} MPa"],
        ]
    else:
        d = dz["stock_diameter_mm"]
        gap, span = dz["bearing_gap_mm"], dz["span_mm"]
        length = gap + 0.6 * span
        stock_file = entry["files"].get("stock_step")
        model = (f"Open {escape(stock_file.replace(chr(92), '/').split('/')[-1])} from this run, in millimetres: the stock alone, as NEMO models it"
                 if stock_file else f"Make a solid cylinder \u00d8{n(d, 0)} mm, {n(length, 0)} mm long: the stock alone, as NEMO models it")
        intro = ("NEMO's stress check models the stock, which carries every load from the fin into the ship; the thin fin body is "
                 "covered by the hand calculation in section 6. Repeat the stock check independently in Autodesk Fusion "
                 "(Simulation, Static Stress) with these values.")
        rows = [
            ["1", "Study type", "Static Stress"],
            ["2", "Model", model + f". Its axis is z; the outer bearing end is at z = {n(-gap, 0)} mm and the free end at z = {n(0.6 * span, 0)} mm"],
            ["3", "Material", _material_text(results["stock_material"], fea["yield_strength_mpa"])],
            ["4", "Fixed constraint", "The flat end face at the outer bearing"],
            ["5", "Load face", f"Split the round face (Design, Modify, Split Face) with a plane {n(gap + 0.4 * span, 0)} mm from the bearing end. "
                              f"The last {n(0.2 * span, 0)} mm, up to the free end, carries the loads"],
            ["6", "Force on that face", f"Y {kn(ap[1])}, across the stock (total {kn(total)})"],
            ["7", "Moment on that face", f"{n(results['loads']['torque_nm'] / 1000, 2)} kN\u00b7m about the stock axis (z)"],
            ["8", "Mesh", f"Element size about {n(finest, 0)} mm"],
            ["9", "Reaction", f"Total of the Reaction Force result equals {kn(total)} within 2%"],
            ["10", "Peak stress", f"Probe the von Mises stress on the surface {n(0.5 * d, 0)} mm from the bearing end, on the side facing "
                                  f"along y, not the legend maximum (that sits on the fixed edge). NEMO found "
                                  f"{n(fea['head_von_mises_mpa'], 1)} MPa and beam theory gives {n(fea.get('hand_stress_mpa') or 0, 1)} MPa; "
                                  "within 15% agrees"],
        ]
    table = _table([["Step", "Setting", "Value"]] + [[a, b, Paragraph(c, s["cell"])] for a, b, c in rows],
                   [12 * mm, 34 * mm, CONTENT_W - 46 * mm])
    blank = _table([["Result in Fusion", "Value", "Agrees with NEMO?"], ["Reaction force", "", ""], ["Peak stress", "", ""],
                    ["Largest movement", "", ""], ["Checked by / date", "", ""]],
                   [60 * mm, 60 * mm, CONTENT_W - 120 * mm],
                   style_extra=[("BOTTOMPADDING", (0, 1), (-1, -1), 10), ("TOPPADDING", (0, 1), (-1, -1), 10),
                                ("GRID", (0, 0), (-1, -1), 0.4, RULE)])
    return out + [Paragraph(intro, s["body"]), Spacer(1, 2 * mm), table, Spacer(1, 5 * mm), blank,
                  Paragraph("Fill in by hand and sign. Movement is for information only: it depends on how each program models the "
                            "support.", s["caption"]), PageBreak()]


def _fin_outline(dz: dict) -> list:
    from .parts.stabilizer.geometry import FinDesign

    return FinDesign(**dz).outline(121)


__all__ = ["PolyLine", "build_part_report"]
