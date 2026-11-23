"""Generate Bitfield-tokenized dual-theme (ink & paper) vector SVG engineering plots.

Reads ONLY `deck-data.json` (extracted from raw solver outputs) and
`Bitfield/tokens.json`. Produces standalone `plots/<name>-ink.svg` and
`plots/<name>-paper.svg` files plus `plots/plots-inline.js` (using Bitfield CSS
custom properties so the HTML deck adapts instantaneously between `ink` and
`paper` themes with bundled Geist / Geist Mono fonts).
"""

from __future__ import annotations

import json
import math
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOKENS_PATH = HERE / "vendor" / "bitfield" / "tokens.json"
DATA_JS_PATH = HERE / "deck-data-inline.js"
PLOTS_DIR = HERE / "plots"


def load_theme_palettes() -> dict[str, dict[str, str]]:
    raw = json.loads(TOKENS_PATH.read_text(encoding="utf-8"))
    tokens = raw["color"]["tokens"]
    base: dict[str, dict[str, str]] = {"ink": {}, "paper": {}}
    for t in tokens:
        val = t["value"]
        if isinstance(val, dict):
            base["ink"][t["name"]] = val["ink"]
            base["paper"][t["name"]] = val["paper"]
        else:
            base["ink"][t["name"]] = val
            base["paper"][t["name"]] = val
    # Resolve {ref} pointers
    for theme in ("ink", "paper"):
        for k, v in list(base[theme].items()):
            if v.startswith("{") and v.endswith("}"):
                base[theme][k] = base[theme][v[1:-1]]
    # CSS variable palette for inline HTML embedding
    css_vars = {t["name"]: f"var(--{t['name']})" for t in tokens}
    return {"ink": base["ink"], "paper": base["paper"], "css": css_vars}


def svg_wrap(w: int, h: int, body: str, c: dict[str, str], title: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'role="img" aria-label="{escape(title)}" '
        f'style="width:100%;height:100%;display:block;font-family:\'Geist Mono\',monospace;">\n'
        f'  <rect x="0" y="0" width="{w}" height="{h}" fill="{c["panel"]}" stroke="{c["line-strong"]}" stroke-width="1"/>\n'
        f"{body}\n"
        f"</svg>\n"
    )


def header_band(w: int, kicker: str, right_tag: str, c: dict[str, str]) -> str:
    return (
        f'  <rect x="0" y="0" width="{w}" height="44" fill="{c["panel-2"]}"/>\n'
        f'  <line x1="0" y1="44" x2="{w}" y2="44" stroke="{c["line-strong"]}" stroke-width="1"/>\n'
        f'  <text x="20" y="27" fill="{c["ink"]}" font-size="14" letter-spacing="0.8">{escape(kicker.upper())}</text>\n'
        f'  <text x="{w - 20}" y="27" fill="{c["ink-muted"]}" font-size="13" text-anchor="end" letter-spacing="0.6">{escape(right_tag.upper())}</text>\n'
    )


def plot_vv_benchmarks(data: dict, c: dict[str, str]) -> str:
    w, h = 880, 620
    benches = data["verification"]["benchmarks"]
    # Select representative headline comparison per benchmark
    rows = []
    for b in benches:
        comps = b["comparisons"]
        if b["id"] == "padeye-hand-calc":
            worst = max(comps, key=lambda x: abs(x["error_percent"]))
            rows.append(("HAND CALC (11 CHECKS)", abs(worst["error_percent"]), worst["tolerance_percent"], f"{abs(worst['error_percent']):.4f}%", "green-text", "MAX ERR"))
        elif b["id"] == "cad-volume":
            worst = max(comps, key=lambda x: abs(x["error_percent"]))
            rows.append(("CAD VOLUME (3 SOLIDS)", abs(worst["error_percent"]), worst["tolerance_percent"], "<1e-13%", "green-text", "EXACT"))
        elif b["id"] == "cantilever":
            d = next(x for x in comps if "deflection" in x["quantity"].lower())
            s = next(x for x in comps if "stress" in x["quantity"].lower())
            rows.append(("TIMOSHENKO DEFLECTION", abs(d["error_percent"]), d["tolerance_percent"], f"{abs(d['error_percent']):.2f}%", "blue-text", f"TOL {d['tolerance_percent']:.0f}%"))
            rows.append(("TIMOSHENKO BENDING", abs(s["error_percent"]), s["tolerance_percent"], f"{abs(s['error_percent']):.2f}%", "blue-text", f"TOL {s['tolerance_percent']:.0f}%"))
        elif b["id"] == "plate-hole":
            k = next(x for x in comps if "concentration" in x["quantity"].lower())
            rows.append(("HEYWOOD HOLE SCF", abs(k["error_percent"]), k["tolerance_percent"], f"{abs(k['error_percent']):.2f}%", "orange-text", f"TOL {k['tolerance_percent']:.0f}%"))
        elif b["id"] == "panel-method":
            ci = next(x for x in comps if "circle" in x["quantity"].lower())
            n20 = next(x for x in comps if "0020" in x["quantity"])
            rows.append(("PANEL CIRCLE CP,MIN", abs(ci["error_percent"]), ci["tolerance_percent"], f"{abs(ci['error_percent']):.2f}%", "green-text", f"TOL {ci['tolerance_percent']:.1f}%"))
            rows.append(("NACA 0020 LIFT SLOPE", abs(n20["error_percent"]), n20["tolerance_percent"], f"{abs(n20['error_percent']):.2f}%", "blue-text", f"TOL {n20['tolerance_percent']:.0f}%"))
        elif b["id"] == "stock-beam":
            st = next(x for x in comps if "stress" in x["quantity"].lower())
            rows.append(("FIN STOCK BEAM FEA", abs(st["error_percent"]), st["tolerance_percent"], f"{abs(st['error_percent']):.2f}%", "green-text", f"TOL {st['tolerance_percent']:.0f}%"))

    parts = [header_band(w, "V&V BENCHMARKS · ERROR VS TOLERANCE", "6 / 6 PASS · 60.0 S", c)]
    x0, x1 = 278, 720
    bar_w = x1 - x0
    max_pct = 5.0
    y_top = 86
    row_h = 56

    # Grid lines at 0, 1, 2, 3, 4, 5%
    for tick in range(0, 6):
        gx = x0 + (tick / max_pct) * bar_w
        stroke = c["line-strong"] if tick == 0 else c["line"]
        parts.append(f'  <line x1="{gx:.1f}" y1="{y_top - 14}" x2="{gx:.1f}" y2="{y_top + len(rows)*row_h - 6}" stroke="{stroke}" stroke-width="1"/>')
        parts.append(f'  <text x="{gx:.1f}" y="{y_top + len(rows)*row_h + 18}" fill="{c["ink-muted"]}" font-size="13" text-anchor="middle">{tick}%</text>')

    parts.append(f'  <text x="{(x0+x1)/2:.1f}" y="{y_top + len(rows)*row_h + 44}" fill="{c["ink-muted"]}" font-size="13" text-anchor="middle" letter-spacing="0.7">ABSOLUTE ERROR AGAINST ANALYTICAL / PUBLISHED REFERENCE (%)</text>')

    for idx, (label, err, tol, err_txt, tone, tol_txt) in enumerate(rows):
        y = y_top + idx * row_h
        cy = y + 20
        # Tolerance bracket band
        tol_x = x0 + min(tol, max_pct) / max_pct * bar_w
        parts.append(f'  <rect x="{x0}" y="{y + 6}" width="{tol_x - x0:.1f}" height="28" fill="{c["panel-2"]}"/>')
        parts.append(f'  <line x1="{tol_x:.1f}" y1="{y + 4}" x2="{tol_x:.1f}" y2="{y + 36}" stroke="{c["line-strong"]}" stroke-width="1.5" stroke-dasharray="3,2"/>')
        # Error bar
        ew = max(4.0, (min(err, max_pct) / max_pct) * bar_w)
        parts.append(f'  <rect x="{x0}" y="{y + 11}" width="{ew:.1f}" height="18" fill="{c[tone]}"/>')
        # Label left
        parts.append(f'  <text x="{x0 - 14}" y="{cy + 4}" fill="{c["ink"]}" font-size="13" text-anchor="end">{escape(label)}</text>')
        # Value right
        parts.append(f'  <text x="{x1 + 16}" y="{cy + 4}" fill="{c[tone]}" font-size="14">{escape(err_txt)}</text>')
        parts.append(f'  <text x="{w - 20}" y="{cy + 4}" fill="{c["ink-muted"]}" font-size="12" text-anchor="end">{escape(tol_txt)}</text>')

    # Legend footer
    fy = h - 22
    parts.append(f'  <rect x="20" y="{fy - 11}" width="12" height="12" fill="{c["green-text"]}"/>')
    parts.append(f'  <text x="38" y="{fy}" fill="{c["ink-muted"]}" font-size="12">MEASURED ERROR</text>')
    parts.append(f'  <rect x="195" y="{fy - 11}" width="12" height="12" fill="{c["panel-2"]}" stroke="{c["line-strong"]}" stroke-width="1"/>')
    parts.append(f'  <text x="213" y="{fy}" fill="{c["ink-muted"]}" font-size="12">ALLOWABLE TOLERANCE BAND</text>')
    parts.append(f'  <text x="{w - 20}" y="{fy}" fill="{c["ink-muted"]}" font-size="12" text-anchor="end">REACTION BALANCE ERR &lt; 1E-10%</text>')
    return svg_wrap(w, h, "\n".join(parts), c, "Verification benchmarks error versus tolerance")


def plot_fea_convergence(data: dict, c: dict[str, str]) -> str:
    w, h = 880, 620
    pad_lv = data["runs"]["padeye"]["designs"]["balanced"]["fea"]["levels"]
    brk_lv = data["runs"]["pipe-bracket"]["designs"]["lightest"]["fea"]["levels"]
    fin_lv = data["runs"]["stabilizer"]["designs"]["lightest"]["fea"]["levels"]

    series = [
        ("PADEYE BALANCED (ASSESSED)", pad_lv, "head_von_mises_mpa", "green-text", False, "0.38%"),
        ("FIN STOCK LIGHTEST (ASSESSED)", fin_lv, "head_von_mises_mpa", "blue-text", False, "0.12%"),
        ("BRACKET SEAT (ASSESSED x>=9mm)", brk_lv, "head_von_mises_mpa", "yellow-text", False, "0.70%"),
        ("BRACKET RAW PEAK (SINGULARITY)", brk_lv, "max_von_mises_mpa", "orange-text", True, "+31.6%"),
    ]

    parts = [header_band(w, "3-LEVEL TET10 MESH CONVERGENCE", "CONVERGENCE GATE: <= 5.0%", c)]
    x0, x1 = 92, 610
    y0, y1 = 84, 468
    # Normalize each series to Level 1 = 100%
    y_min, y_max = 90.0, 140.0

    def map_x(lv_idx: int) -> float:
        return x0 + (lv_idx / 2.0) * (x1 - x0)

    def map_y(val: float) -> float:
        return y1 - (val - y_min) / (y_max - y_min) * (y1 - y0)

    # Gate band: 95% to 105%
    gy_top, gy_bot = map_y(105.0), map_y(95.0)
    parts.append(f'  <rect x="{x0}" y="{gy_top:.1f}" width="{x1 - x0}" height="{gy_bot - gy_top:.1f}" fill="{c["panel-2"]}"/>')
    parts.append(f'  <text x="{x1 - 8}" y="{gy_top + 16:.1f}" fill="{c["ink-muted"]}" font-size="12" text-anchor="end">+-5% CONVERGENCE BAND</text>')

    for yv in [90, 100, 110, 120, 130, 140]:
        py = map_y(yv)
        stroke = c["line-strong"] if yv == 100 else c["line"]
        parts.append(f'  <line x1="{x0}" y1="{py:.1f}" x2="{x1}" y2="{py:.1f}" stroke="{stroke}" stroke-width="1"/>')
        parts.append(f'  <text x="{x0 - 12}" y="{py + 4:.1f}" fill="{c["ink-muted"]}" font-size="13" text-anchor="end">{yv}%</text>')

    lv_labels = [
        ("LEVEL 1", "COARSE (1.0x)"),
        ("LEVEL 2", "MEDIUM (0.7x)"),
        ("LEVEL 3", "FINE (0.5x)"),
    ]
    for i, (t1, t2) in enumerate(lv_labels):
        px = map_x(i)
        parts.append(f'  <line x1="{px:.1f}" y1="{y0}" x2="{px:.1f}" y2="{y1}" stroke="{c["line"]}" stroke-width="1"/>')
        parts.append(f'  <text x="{px:.1f}" y="{y1 + 24}" fill="{c["ink"]}" font-size="13" text-anchor="middle">{t1}</text>')
        parts.append(f'  <text x="{px:.1f}" y="{y1 + 42}" fill="{c["ink-muted"]}" font-size="12" text-anchor="middle">{t2}</text>')

    parts.append(f'  <text x="26" y="{(y0+y1)/2:.1f}" fill="{c["ink-muted"]}" font-size="13" text-anchor="middle" transform="rotate(-90 26 {(y0+y1)/2:.1f})">STRESS RELATIVE TO LEVEL 1 (%)</text>')

    for label, levels, key, tone, dashed, delta_txt in series:
        base = levels[0][key]
        pts = [(map_x(i), map_y(lv[key] / base * 100.0)) for i, lv in enumerate(levels)]
        d_str = " ".join(f"{'M' if i == 0 else 'L'}{px:.1f} {py:.1f}" for i, (px, py) in enumerate(pts))
        dash_attr = ' stroke-dasharray="7,4"' if dashed else ""
        parts.append(f'  <path d="{d_str}" fill="none" stroke="{c[tone]}" stroke-width="2.5"{dash_attr}/>')
        for px, py in pts:
            parts.append(f'  <rect x="{px - 4.5:.1f}" y="{py - 4.5:.1f}" width="9" height="9" fill="{c["panel"]}" stroke="{c[tone]}" stroke-width="2"/>')

    # Right summary readout panel
    rx = 632
    rw = w - rx - 20
    parts.append(f'  <rect x="{rx}" y="{y0}" width="{rw}" height="{y1 - y0}" fill="{c["panel-2"]}" stroke="{c["line-strong"]}" stroke-width="1"/>')
    parts.append(f'  <text x="{rx + 14}" y="{y0 + 26}" fill="{c["ink"]}" font-size="13" letter-spacing="0.6">L3 ASSESSED STRESS</text>')
    parts.append(f'  <line x1="{rx}" y1="{y0 + 38}" x2="{rx + rw}" y2="{y0 + 38}" stroke="{c["line"]}" stroke-width="1"/>')

    cards = [
        ("PADEYE BALANCED", f"{pad_lv[2]['head_von_mises_mpa']:.1f} MPa", f"DELTA {data['runs']['padeye']['designs']['balanced']['fea']['convergence_change_pct']:.2f}% · {pad_lv[2]['dofs']:,} DOF", "green-text"),
        ("FIN STOCK", f"{fin_lv[2]['head_von_mises_mpa']:.1f} MPa", f"DELTA {data['runs']['stabilizer']['designs']['lightest']['fea']['convergence_change_pct']:.2f}% · {fin_lv[2]['dofs']:,} DOF", "blue-text"),
        ("BRACKET SEAT", f"{brk_lv[2]['head_von_mises_mpa']:.1f} MPa", f"DELTA {data['runs']['pipe-bracket']['designs']['lightest']['fea']['convergence_change_pct']:.2f}% · {brk_lv[2]['dofs']:,} DOF", "yellow-text"),
        ("BRACKET RAW PEAK", f"{brk_lv[2]['max_von_mises_mpa']:.1f} MPa", f"SINGULARITY: {brk_lv[0]['max_von_mises_mpa']:.1f} -> {brk_lv[2]['max_von_mises_mpa']:.1f}", "orange-text"),
    ]
    for i, (nm, val, sub, tone) in enumerate(cards):
        cy = y0 + 64 + i * 78
        parts.append(f'  <rect x="{rx + 14}" y="{cy - 11}" width="10" height="10" fill="{c[tone]}"/>')
        parts.append(f'  <text x="{rx + 32}" y="{cy - 2}" fill="{c["ink"]}" font-size="12">{nm}</text>')
        parts.append(f'  <text x="{rx + 14}" y="{cy + 22}" fill="{c[tone]}" font-size="20">{val}</text>')
        parts.append(f'  <text x="{rx + 14}" y="{cy + 40}" fill="{c["ink-muted"]}" font-size="11">{sub}</text>')

    # Footer note
    parts.append(f'  <line x1="20" y1="538" x2="{w - 20}" y2="538" stroke="{c["line"]}" stroke-width="1"/>')
    parts.append(f'  <text x="20" y="566" fill="{c["ink"]}" font-size="13">REACTION EQUILIBRIUM ACROSS ALL 21 SOLVES: WORST FORCE ERROR = {data["summary"]["worst_reaction_balance_error"]:.2e}</text>')
    parts.append(f'  <text x="20" y="592" fill="{c["ink-muted"]}" font-size="12">SOURCE: DATA/RUNS/*/20270115-090000-000000/RESULTS.JSON · QUADRATIC TET10 (SCIKIT-FEM + PYAMG)</text>')
    return svg_wrap(w, h, "\n".join(parts), c, "Three-level quadratic tetrahedral FEA mesh convergence")


def plot_padeye_sweep(data: dict, c: dict[str, str]) -> str:
    w, h = 880, 620
    rows = data["sweeps"]["padeye"]
    parts = [header_band(w, "PADEYE SWEEP · LOAD, SLING ANGLE & GOVERNING MODE", "ASME BTH-1 CAT. B · S355", c)]

    x0, x1 = 90, 840
    y0, y1 = 84, 470
    max_load, max_mass = 42.0, 8.0

    def mx(v: float) -> float:
        return x0 + (v / max_load) * (x1 - x0)

    def my(v: float) -> float:
        return y1 - (v / max_mass) * (y1 - y0)

    # Grid
    for yv in [0, 2, 4, 6, 8]:
        py = my(yv)
        parts.append(f'  <line x1="{x0}" y1="{py:.1f}" x2="{x1}" y2="{py:.1f}" stroke="{c["line-strong"] if yv == 0 else c["line"]}" stroke-width="1"/>')
        parts.append(f'  <text x="{x0 - 12}" y="{py + 4:.1f}" fill="{c["ink-muted"]}" font-size="13" text-anchor="end">{yv} kg</text>')

    for xv in [0, 5, 10, 20, 30, 40]:
        px = mx(xv)
        parts.append(f'  <line x1="{px:.1f}" y1="{y0}" x2="{px:.1f}" y2="{y1}" stroke="{c["line-strong"] if xv == 0 else c["line"]}" stroke-width="1"/>')
        parts.append(f'  <text x="{px:.1f}" y="{y1 + 22}" fill="{c["ink-muted"]}" font-size="13" text-anchor="middle">{xv} t</text>')

    parts.append(f'  <text x="{(x0+x1)/2:.1f}" y="{y1 + 48}" fill="{c["ink-muted"]}" font-size="13" text-anchor="middle">LIFTED MASS ON TWO SLING POINTS (TONNES)</text>')
    parts.append(f'  <text x="26" y="{(y0+y1)/2:.1f}" fill="{c["ink-muted"]}" font-size="13" text-anchor="middle" transform="rotate(-90 26 {(y0+y1)/2:.1f})">LIGHTEST PADEYE MASS (KG)</text>')

    gov_color = {
        "Base weld strength": "green-text",
        "Pulling and bending at the base": "blue-text",
        "Splitting above the hole": "orange-text",
        "Shackle is rated for the load": "yellow-text",
    }

    angle_style = {
        45: ("45 DEG SLING", ""),
        60: ("60 DEG SLING", "8,4"),
        90: ("90 DEG VERTICAL", "3,3"),
    }

    for angle in (45, 60, 90):
        pts_data = sorted([r for r in rows if r["angle"] == angle], key=lambda r: r["load_t"])
        d_str = " ".join(f"{'M' if i == 0 else 'L'}{mx(r['load_t']):.1f} {my(r['mass_kg']):.1f}" for i, r in enumerate(pts_data))
        lbl, dash = angle_style[angle]
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        parts.append(f'  <path d="{d_str}" fill="none" stroke="{c["line-strong"]}" stroke-width="2"{dash_attr}/>')
        last = pts_data[-1]
        parts.append(f'  <text x="{mx(last["load_t"]) - 4:.1f}" y="{my(last["mass_kg"]) - 12:.1f}" fill="{c["ink"]}" font-size="12" text-anchor="end">{lbl}</text>')
        for r in pts_data:
            px, py = mx(r["load_t"]), my(r["mass_kg"])
            tc = gov_color.get(r["governing"], "ink")
            parts.append(f'  <rect x="{px - 5:.1f}" y="{py - 5:.1f}" width="10" height="10" fill="{c[tc]}" stroke="{c["panel"]}" stroke-width="1.5"/>')

    # Callout for 5t @ 60 deg case study
    cx, cy = mx(5), my(0.305)
    parts.append(f'  <line x1="{cx:.1f}" y1="{cy - 8:.1f}" x2="{cx + 55:.1f}" y2="{cy - 72:.1f}" stroke="{c["green-text"]}" stroke-width="1.5"/>')
    parts.append(f'  <rect x="{cx + 55:.1f}" y="{cy - 102:.1f}" width="275" height="44" fill="{c["panel-2"]}" stroke="{c["green-text"]}" stroke-width="1"/>')
    parts.append(f'  <text x="{cx + 67:.1f}" y="{cy - 82:.1f}" fill="{c["green-text"]}" font-size="12">CASE STUDY: 5 t @ 60 DEG</text>')
    parts.append(f'  <text x="{cx + 67:.1f}" y="{cy - 66:.1f}" fill="{c["ink"]}" font-size="12">0.305 KG LIGHTEST · 0.432 KG BAL</text>')

    # Legend for governing checks
    parts.append(f'  <line x1="20" y1="536" x2="{w - 20}" y2="536" stroke="{c["line"]}" stroke-width="1"/>')
    leg = [
        ("BASE WELD", "green-text", 20),
        ("BASE COMBINED", "blue-text", 180),
        ("HEAD FRACTURE", "orange-text", 365),
        ("SHACKLE WLL", "yellow-text", 560),
    ]
    for txt, tone, lx in leg:
        parts.append(f'  <rect x="{lx}" y="553" width="11" height="11" fill="{c[tone]}"/>')
        parts.append(f'  <text x="{lx + 18}" y="563" fill="{c["ink"]}" font-size="12">{txt}</text>')
    parts.append(f'  <text x="20" y="594" fill="{c["ink-muted"]}" font-size="12">SOURCE: REPORTS/PROJECT-REPORT/DATA/SWEEPS.JSON#PADEYE (21 DESIGNS)</text>')
    return svg_wrap(w, h, "\n".join(parts), c, "Padeye mass and governing mode across lifted load and sling angle")


def plot_bracket_vibration(data: dict, c: dict[str, str]) -> str:
    w, h = 880, 620
    rows = data["sweeps"]["bracket_span"]
    span_info = data["runs"]["pipe-bracket"]["designs"]["lightest"]["span"]
    parts = [header_band(w, "DN100 SEAWATER LINE · SPAN FREQUENCY VS EXCITATION", "AISC 360-16 · +-20% BANDS", c)]

    x0, x1 = 92, 840
    y0, y1 = 84, 468
    s_min, s_max = 1.4, 6.2
    f_min, f_max = 0.0, 75.0

    def mx(s: float) -> float:
        return x0 + (s - s_min) / (s_max - s_min) * (x1 - x0)

    def my(f: float) -> float:
        return y1 - (min(f, f_max) - f_min) / (f_max - f_min) * (y1 - y0)

    # Excitation +-20% forbidden bands
    excitations = [
        ("ENGINE FIRING 37.5 HZ", 37.5, "orange-text", "end"),
        ("2X BLADE RATE 16.0 HZ", 16.0, "blue-text", "end"),
        ("BLADE RATE 8.0 HZ", 8.0, "yellow-text", "start"),
    ]
    for name, hz, tone, align in excitations:
        top = my(hz * 1.2)
        bot = my(hz * 0.8)
        mid = my(hz)
        parts.append(f'  <rect x="{x0}" y="{top:.1f}" width="{x1 - x0}" height="{bot - top:.1f}" fill="{c["panel-2"]}"/>')
        parts.append(f'  <line x1="{x0}" y1="{mid:.1f}" x2="{x1}" y2="{mid:.1f}" stroke="{c[tone]}" stroke-width="1.5" stroke-dasharray="6,4"/>')
        tx = x1 - 8 if align == "end" else x0 + 8
        parts.append(f'  <text x="{tx}" y="{mid - 6:.1f}" fill="{c[tone]}" font-size="12" text-anchor="{align}">{name} (+-20%)</text>')

    # Grid lines
    for yv in [0, 15, 30, 45, 60, 75]:
        py = my(yv)
        parts.append(f'  <line x1="{x0}" y1="{py:.1f}" x2="{x1}" y2="{py:.1f}" stroke="{c["line-strong"] if yv == 0 else c["line"]}" stroke-width="1"/>')
        parts.append(f'  <text x="{x0 - 12}" y="{py + 4:.1f}" fill="{c["ink-muted"]}" font-size="13" text-anchor="end">{yv} Hz</text>')

    for xv in [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0]:
        px = mx(xv)
        parts.append(f'  <line x1="{px:.1f}" y1="{y0}" x2="{px:.1f}" y2="{y1}" stroke="{c["line"]}" stroke-width="1"/>')
        parts.append(f'  <text x="{px:.1f}" y="{y1 + 22}" fill="{c["ink-muted"]}" font-size="13" text-anchor="middle">{xv:.1f} m</text>')

    # Recommended frequency-limited max span vertical marker (2.35 m) and sag limit (4.70 m)
    rx_freq = mx(span_info["spans_m"]["frequency"])
    rx_sag = mx(span_info["spans_m"]["sag"])
    parts.append(f'  <line x1="{rx_freq:.1f}" y1="{y0}" x2="{rx_freq:.1f}" y2="{y1}" stroke="{c["green-text"]}" stroke-width="2"/>')
    parts.append(f'  <text x="{rx_freq + 8:.1f}" y="{y0 + 18}" fill="{c["green-text"]}" font-size="12">FREQ LIMIT {span_info["spans_m"]["frequency"]:.2f} m</text>')
    parts.append(f'  <line x1="{rx_sag:.1f}" y1="{y0}" x2="{rx_sag:.1f}" y2="{y1}" stroke="{c["line-strong"]}" stroke-width="1.5" stroke-dasharray="4,3"/>')
    parts.append(f'  <text x="{rx_sag + 8:.1f}" y="{y0 + 18}" fill="{c["ink-muted"]}" font-size="12">SAG LIMIT {span_info["spans_m"]["sag"]:.2f} m</text>')

    # Smooth curve f_n = f_3 * (3/S)^2
    f3 = span_info["natural_hz"]
    curve_pts = []
    for k in range(0, 90):
        sv = 1.82 + (6.1 - 1.82) * k / 89.0
        fv = f3 * (3.0 / sv) ** 2
        if fv <= f_max:
            curve_pts.append((mx(sv), my(fv)))
    d_str = " ".join(f"{'M' if i == 0 else 'L'}{px:.1f} {py:.1f}" for i, (px, py) in enumerate(curve_pts))
    parts.append(f'  <path d="{d_str}" fill="none" stroke="{c["ink"]}" stroke-width="2.5"/>')

    # Sweep points (skip 1.5 m = 110.3 Hz off top, annotate instead)
    for r in rows:
        if r["natural_hz"] > f_max:
            continue
        px, py = mx(r["span_m"]), my(r["natural_hz"])
        ok = r["separation"] >= 0.20
        tc = "green-text" if ok else "orange-text"
        parts.append(f'  <rect x="{px - 5.5:.1f}" y="{py - 5.5:.1f}" width="11" height="11" fill="{c[tc]}" stroke="{c["panel"]}" stroke-width="1.5"/>')
        if r["span_m"] in (2.5, 3.0, 4.0):
            if r["span_m"] == 2.5:
                dx, dy, anch = 10, -10, "start"
            elif r["span_m"] == 3.0:
                dx, dy, anch = 12, -10, "start"
            else:
                dx, dy, anch = 0, 22, "middle"
            tag = f"{r['span_m']:.1f}m: {r['natural_hz']:.1f}Hz ({r['separation']*100:.0f}%)"
            parts.append(f'  <text x="{px + dx:.1f}" y="{py + dy:.1f}" fill="{c[tc]}" font-size="12" text-anchor="{anch}">{tag}</text>')

    parts.append(f'  <text x="{(x0+x1)/2:.1f}" y="{y1 + 48}" fill="{c["ink-muted"]}" font-size="13" text-anchor="middle">PIPE SUPPORT SPACING S (METRES) · STRESS LIMIT = {span_info["spans_m"]["stress"]:.1f} m</text>')
    parts.append(f'  <text x="26" y="{(y0+y1)/2:.1f}" fill="{c["ink-muted"]}" font-size="13" text-anchor="middle" transform="rotate(-90 26 {(y0+y1)/2:.1f})">NATURAL FREQUENCY FN (HZ)</text>')

    parts.append(f'  <line x1="20" y1="536" x2="{w - 20}" y2="536" stroke="{c["line"]}" stroke-width="1"/>')
    parts.append(f'  <rect x="20" y="553" width="11" height="11" fill="{c["green-text"]}"/>')
    parts.append(f'  <text x="38" y="563" fill="{c["ink"]}" font-size="12">CLEAR (>= 20% SEPARATION)</text>')
    parts.append(f'  <rect x="290" y="553" width="11" height="11" fill="{c["orange-text"]}"/>')
    parts.append(f'  <text x="308" y="563" fill="{c["ink"]}" font-size="12">RESONANCE RISK (&lt; 20%: 2.5m, 4.0m, 6.0m)</text>')
    parts.append(f'  <text x="20" y="594" fill="{c["ink-muted"]}" font-size="12">SOURCE: DATA/SWEEPS.JSON#BRACKET_SPAN &amp; RUNS/PIPE-BRACKET/RESULTS.JSON</text>')
    return svg_wrap(w, h, "\n".join(parts), c, "Pipe span natural frequency versus machinery excitation bands")


def plot_fin_sweep(data: dict, c: dict[str, str]) -> str:
    w, h = 880, 620
    rows = data["sweeps"]["fin"]
    parts = [header_band(w, "STABILIZER FIN · LIFT MODEL & CAVITATION ENVELOPE", "NACA 0020 · 22 DEG · 3 m DEPTH", c)]

    x0, x1 = 92, 836
    v_min, v_max = 10.0, 24.0

    def mx(v: float) -> float:
        return x0 + (v - v_min) / (v_max - v_min) * (x1 - x0)

    # Top strip: Force (kN)
    ty0, ty1 = 74, 266
    f_max = 160.0

    def my_f(f: float) -> float:
        return ty1 - (f / f_max) * (ty1 - ty0)

    parts.append(f'  <text x="{x0}" y="{ty0 - 10}" fill="{c["ink"]}" font-size="12" letter-spacing="0.6">A · DESIGN NORMAL FORCE (KN): WHICKER-FEHLNER VS IACS UR S10</text>')
    for yv in [0, 40, 80, 120, 160]:
        py = my_f(yv)
        parts.append(f'  <line x1="{x0}" y1="{py:.1f}" x2="{x1}" y2="{py:.1f}" stroke="{c["line-strong"] if yv == 0 else c["line"]}" stroke-width="1"/>')
        parts.append(f'  <text x="{x0 - 10}" y="{py + 4:.1f}" fill="{c["ink-muted"]}" font-size="12" text-anchor="end">{yv}</text>')

    d_wf = " ".join(f"{'M' if i == 0 else 'L'}{mx(r['speed_kn']):.1f} {my_f(r['nemo_lift_kn']):.1f}" for i, r in enumerate(rows))
    d_s10 = " ".join(f"{'M' if i == 0 else 'L'}{mx(r['speed_kn']):.1f} {my_f(r['ur_s10_kn']):.1f}" for i, r in enumerate(rows))
    parts.append(f'  <path d="{d_wf}" fill="none" stroke="{c["green-text"]}" stroke-width="2.5"/>')
    parts.append(f'  <path d="{d_s10}" fill="none" stroke="{c["blue-text"]}" stroke-width="2" stroke-dasharray="7,4"/>')
    for r in rows:
        parts.append(f'  <rect x="{mx(r["speed_kn"]) - 4:.1f}" y="{my_f(r["nemo_lift_kn"]) - 4:.1f}" width="8" height="8" fill="{c["green-text"]}"/>')
        parts.append(f'  <rect x="{mx(r["speed_kn"]) - 3.5:.1f}" y="{my_f(r["ur_s10_kn"]) - 3.5:.1f}" width="7" height="7" fill="{c["blue-text"]}"/>')

    # Annotate 18 kn
    x18 = mx(18.0)
    parts.append(f'  <line x1="{x18:.1f}" y1="{ty0}" x2="{x18:.1f}" y2="492" stroke="{c["line-strong"]}" stroke-width="1" stroke-dasharray="3,3"/>')
    parts.append(f'  <text x="{x18 - 10:.1f}" y="{my_f(80.49) - 12:.1f}" fill="{c["green-text"]}" font-size="12" text-anchor="end">80.5 kN (+20.6%)</text>')
    parts.append(f'  <text x="{x18 + 10:.1f}" y="{my_f(66.74) + 16:.1f}" fill="{c["blue-text"]}" font-size="12">UR S10: 66.7 kN</text>')

    # Bottom strip: Cavitation number vs |Cp,min| = 2.91
    by0, by1 = 312, 492
    s_max = 10.0

    def my_s(sv: float) -> float:
        return by1 - (sv / s_max) * (by1 - by0)

    cp_abs = abs(rows[0]["cp_min"])
    py_cp = my_s(cp_abs)
    # Cavitating region (below |Cp,min|)
    parts.append(f'  <rect x="{x0}" y="{py_cp:.1f}" width="{x1 - x0}" height="{by1 - py_cp:.1f}" fill="{c["panel-2"]}"/>')
    parts.append(f'  <text x="{x0 + 10}" y="{by1 - 12}" fill="{c["orange-text"]}" font-size="12">CAVITATION INCEPTION ZONE (SIGMA &lt; |CP,MIN| = {cp_abs:.2f})</text>')

    parts.append(f'  <text x="{x0}" y="{by0 - 10}" fill="{c["ink"]}" font-size="12" letter-spacing="0.6">B · CAVITATION NUMBER SIGMA VS HESS-SMITH SUCTION PEAK |CP,MIN|</text>')
    for yv in [0, 2, 4, 6, 8, 10]:
        py = my_s(yv)
        parts.append(f'  <line x1="{x0}" y1="{py:.1f}" x2="{x1}" y2="{py:.1f}" stroke="{c["line-strong"] if yv == 0 else c["line"]}" stroke-width="1"/>')
        parts.append(f'  <text x="{x0 - 10}" y="{py + 4:.1f}" fill="{c["ink-muted"]}" font-size="12" text-anchor="end">{yv}</text>')

    parts.append(f'  <line x1="{x0}" y1="{py_cp:.1f}" x2="{x1}" y2="{py_cp:.1f}" stroke="{c["orange-text"]}" stroke-width="2" stroke-dasharray="6,4"/>')
    d_sig = " ".join(f"{'M' if i == 0 else 'L'}{mx(r['speed_kn']):.1f} {my_s(r['sigma']):.1f}" for i, r in enumerate(rows))
    parts.append(f'  <path d="{d_sig}" fill="none" stroke="{c["ink"]}" stroke-width="2.5"/>')
    for r in rows:
        px, py = mx(r["speed_kn"]), my_s(r["sigma"])
        tc = "green-text" if r["sigma"] >= cp_abs else "orange-text"
        parts.append(f'  <rect x="{px - 4.5:.1f}" y="{py - 4.5:.1f}" width="9" height="9" fill="{c[tc]}" stroke="{c["panel"]}" stroke-width="1.5"/>')

    parts.append(f'  <text x="{x18 + 8:.1f}" y="{my_s(2.95) - 14:.1f}" fill="{c["green-text"]}" font-size="12">18 kn: SIGMA 2.95 (+1.5%)</text>')
    parts.append(f'  <text x="{mx(22.0):.1f}" y="{my_s(4.25):.1f}" fill="{c["orange-text"]}" font-size="12" text-anchor="middle">20-24 kn CAVITATES</text>')

    for r in rows:
        px = mx(r["speed_kn"])
        parts.append(f'  <text x="{px:.1f}" y="{by1 + 22}" fill="{c["ink-muted"]}" font-size="13" text-anchor="middle">{r["speed_kn"]} kn</text>')

    parts.append(f'  <text x="{(x0+x1)/2:.1f}" y="{by1 + 46}" fill="{c["ink-muted"]}" font-size="13" text-anchor="middle">VESSEL SERVICE SPEED (KNOTS) · STOCK DIAMETER RISES 110 -> 195 MM</text>')
    parts.append(f'  <line x1="20" y1="556" x2="{w - 20}" y2="556" stroke="{c["line"]}" stroke-width="1"/>')
    parts.append(f'  <text x="20" y="586" fill="{c["ink-muted"]}" font-size="12">SOURCE: REPORTS/PROJECT-REPORT/DATA/SWEEPS.JSON#FIN (10-24 KN)</text>')
    return svg_wrap(w, h, "\n".join(parts), c, "Stabilizer fin hydrodynamic force and cavitation envelope across speed")


def plot_padeye_obliquity(data: dict, c: dict[str, str]) -> str:
    w, h = 880, 620
    rows = data["advanced"]["padeye"]
    parts = [header_band(w, "BACKUP B1 · OUT-OF-PLANE OBLIQUITY & SHACKLE DERATING", "5 t LIFT · 60 DEG SLING · S355", c)]

    x0, x1 = 94, 836
    y0, y1 = 92, 456
    bar_w = 110
    xs = [x0 + 80 + i * 185 for i in range(len(rows))]
    max_side_kn = 16.0

    def my(kn: float) -> float:
        return y1 - (kn / max_side_kn) * (y1 - y0)

    for yv in [0, 4, 8, 12, 16]:
        py = my(yv)
        parts.append(f'  <line x1="{x0}" y1="{py:.1f}" x2="{x1}" y2="{py:.1f}" stroke="{c["line-strong"] if yv == 0 else c["line"]}" stroke-width="1"/>')
        parts.append(f'  <text x="{x0 - 12}" y="{py + 4:.1f}" fill="{c["ink-muted"]}" font-size="13" text-anchor="end">{yv} kN</text>')

    parts.append(f'  <text x="26" y="{(y0+y1)/2:.1f}" fill="{c["ink-muted"]}" font-size="13" text-anchor="middle" transform="rotate(-90 26 {(y0+y1)/2:.1f})">OUT-OF-PLANE SIDE LOAD (KN)</text>')

    for i, r in enumerate(rows):
        cx = xs[i]
        side_kn = r["side_n"] / 1000.0
        top = my(side_kn)
        derated = r["side_factor"] < 1.0
        tone = "orange-text" if derated else "green-text"
        parts.append(f'  <rect x="{cx - bar_w/2:.1f}" y="{top:.1f}" width="{bar_w}" height="{y1 - top:.1f}" fill="{c[tone]}"/>')
        parts.append(f'  <text x="{cx:.1f}" y="{top - 12:.1f}" fill="{c[tone]}" font-size="15" text-anchor="middle">{side_kn:.2f} kN</text>')
        plate_txt = f"{int(r['main_plate_mm'])}+{int(r['cheek_mm'])}mm" if r["cheek_mm"] > 0 else f"{int(r['main_plate_mm'])}mm SOLID"
        parts.append(f'  <text x="{cx:.1f}" y="{y1 + 24}" fill="{c["ink"]}" font-size="14" text-anchor="middle">BETA {int(r["beta_deg"])} DEG</text>')
        parts.append(f'  <text x="{cx:.1f}" y="{y1 + 44}" fill="{c["ink-muted"]}" font-size="12" text-anchor="middle">{r["mass_kg"]:.3f} kg · {plate_txt}</text>')
        parts.append(f'  <text x="{cx:.1f}" y="{y1 + 64}" fill="{c[tone]}" font-size="12" text-anchor="middle">{r["shackle_wll_t"]:.2f}t x {r["side_factor"]:.2f}</text>')

    parts.append(f'  <line x1="20" y1="548" x2="{w - 20}" y2="548" stroke="{c["line"]}" stroke-width="1"/>')
    parts.append(f'  <text x="20" y="576" fill="{c["ink"]}" font-size="12">DERATING THRESHOLD: SIDE ANGLE &gt; 15 DEG TRIGGERS 0.75 SHACKLE FACTOR (45 DEG, 90 DEG)</text>')
    parts.append(f'  <text x="20" y="598" fill="{c["ink-muted"]}" font-size="12">SOURCE: REPORTS/PROJECT-REPORT/DATA/ADVANCED.JSON#PADEYE</text>')
    return svg_wrap(w, h, "\n".join(parts), c, "Padeye side load and shackle derating across out-of-plane obliquity")


def plot_bracket_dunkerley(data: dict, c: dict[str, str]) -> str:
    w, h = 880, 620
    rows = data["advanced"]["bracket"]
    parts = [header_band(w, "BACKUP B2 · RIGID SPAN VS DUNKERLEY COMBINED MODE", "3.0 m SPAN · ENGINE FIRING 37.5 HZ", c)]

    x0, x1 = 92, 836
    y0, y1 = 84, 468
    f_max = 75.0

    def my(f: float) -> float:
        return y1 - (f / f_max) * (y1 - y0)

    # Engine firing 37.5 Hz +-20% band (30 to 45 Hz)
    bt, bb = my(45.0), my(30.0)
    parts.append(f'  <rect x="{x0}" y="{bt:.1f}" width="{x1 - x0}" height="{bb - bt:.1f}" fill="{c["panel-2"]}"/>')
    parts.append(f'  <line x1="{x0}" y1="{my(37.5):.1f}" x2="{x1}" y2="{my(37.5):.1f}" stroke="{c["orange-text"]}" stroke-width="1.5" stroke-dasharray="6,4"/>')
    parts.append(f'  <text x="{x1 - 8}" y="{my(37.5) - 6:.1f}" fill="{c["orange-text"]}" font-size="12" text-anchor="end">ENGINE FIRING 37.5 HZ (+-20% BAND)</text>')

    for yv in [0, 15, 30, 45, 60, 75]:
        py = my(yv)
        parts.append(f'  <line x1="{x0}" y1="{py:.1f}" x2="{x1}" y2="{py:.1f}" stroke="{c["line-strong"] if yv == 0 else c["line"]}" stroke-width="1"/>')
        parts.append(f'  <text x="{x0 - 12}" y="{py + 4:.1f}" fill="{c["ink-muted"]}" font-size="13" text-anchor="end">{yv} Hz</text>')

    xs = [x0 + 54 + i * 106 for i in range(len(rows))]
    d_rigid = " ".join(f"{'M' if i == 0 else 'L'}{xs[i]:.1f} {my(r['span_hz']):.1f}" for i, r in enumerate(rows))
    d_comb = " ".join(f"{'M' if i == 0 else 'L'}{xs[i]:.1f} {my(r['combined_hz']):.1f}" for i, r in enumerate(rows))
    parts.append(f'  <path d="{d_rigid}" fill="none" stroke="{c["blue-text"]}" stroke-width="2" stroke-dasharray="7,4"/>')
    parts.append(f'  <path d="{d_comb}" fill="none" stroke="{c["green-text"]}" stroke-width="2.5"/>')

    for i, r in enumerate(rows):
        px = xs[i]
        yr, yc = my(r["span_hz"]), my(r["combined_hz"])
        parts.append(f'  <line x1="{px:.1f}" y1="{yr:.1f}" x2="{px:.1f}" y2="{yc:.1f}" stroke="{c["line-strong"]}" stroke-width="1.5"/>')
        parts.append(f'  <rect x="{px - 4:.1f}" y="{yr - 4:.1f}" width="8" height="8" fill="{c["blue-text"]}"/>')
        tc = "green-text" if r["passed"] else "orange-text"
        parts.append(f'  <rect x="{px - 5:.1f}" y="{yc - 5:.1f}" width="10" height="10" fill="{c[tc]}" stroke="{c["panel"]}" stroke-width="1.5"/>')
        parts.append(f'  <text x="{px:.1f}" y="{y1 + 22}" fill="{c["ink"]}" font-size="13" text-anchor="middle">NPS {r["nps"]}</text>')
        parts.append(f'  <text x="{px:.1f}" y="{y1 + 40}" fill="{c[tc]}" font-size="11" text-anchor="middle">{r["combined_hz"]:.1f} Hz</text>')

    # Highlight NPS 6 direct hit
    px6 = xs[3]
    py6 = my(rows[3]["combined_hz"])
    parts.append(f'  <text x="{px6 + 12:.1f}" y="{py6 + 22:.1f}" fill="{c["orange-text"]}" font-size="12">NPS 6: 39.1 -> 37.25 Hz (0.67%)</text>')

    parts.append(f'  <text x="26" y="{(y0+y1)/2:.1f}" fill="{c["ink-muted"]}" font-size="13" text-anchor="middle" transform="rotate(-90 26 {(y0+y1)/2:.1f})">NATURAL FREQUENCY (HZ)</text>')
    parts.append(f'  <line x1="20" y1="538" x2="{w - 20}" y2="538" stroke="{c["line"]}" stroke-width="1"/>')
    parts.append(f'  <rect x="20" y="554" width="11" height="11" fill="{c["blue-text"]}"/>')
    parts.append(f'  <text x="38" y="564" fill="{c["ink"]}" font-size="12">RIGID-SUPPORT SPAN FN</text>')
    parts.append(f'  <rect x="260" y="554" width="11" height="11" fill="{c["green-text"]}"/>')
    parts.append(f'  <text x="278" y="564" fill="{c["ink"]}" font-size="12">DUNKERLEY COMBINED (PASS)</text>')
    parts.append(f'  <rect x="520" y="554" width="11" height="11" fill="{c["orange-text"]}"/>')
    parts.append(f'  <text x="538" y="564" fill="{c["ink"]}" font-size="12">FAIL (&lt; 20%: NPS 2, NPS 6)</text>')
    parts.append(f'  <text x="20" y="596" fill="{c["ink-muted"]}" font-size="12">SOURCE: REPORTS/PROJECT-REPORT/DATA/ADVANCED.JSON#BRACKET</text>')
    return svg_wrap(w, h, "\n".join(parts), c, "Pipe rigid-span versus Dunkerley combined natural frequency")


def main() -> None:
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    palettes = load_theme_palettes()
    raw_js = DATA_JS_PATH.read_text(encoding="utf-8").strip()
    raw_json = raw_js.removeprefix("window.NEMO_DATA =").rstrip(";").strip()
    data = json.loads(raw_json)

    generators = {
        "vv-benchmarks": plot_vv_benchmarks,
        "fea-convergence": plot_fea_convergence,
        "padeye-sweep": plot_padeye_sweep,
        "bracket-vibration": plot_bracket_vibration,
        "fin-sweep": plot_fin_sweep,
        "padeye-obliquity": plot_padeye_obliquity,
        "bracket-dunkerley": plot_bracket_dunkerley,
    }

    inline_map = {name: fn(data, palettes["css"]) for name, fn in generators.items()}
    js_out = "window.NEMO_PLOTS = " + json.dumps(inline_map, indent=2) + ";\n"
    (PLOTS_DIR / "plots-inline.js").write_text(js_out, encoding="utf-8")
    print(f"Generated plots-inline.js ({len(generators)} dual-theme SVGs) in {PLOTS_DIR}")


if __name__ == "__main__":
    main()
