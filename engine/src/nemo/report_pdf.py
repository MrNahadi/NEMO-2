"""PDF calculation package for one padeye design.

Laid out like an engineering calculation report: a document number, revision
and sign-off boxes on every page, a dimensioned fabrication drawing with a
parts list, calculation sheets with the working for every check, FEA figures
(mesh convergence, stress contours, force balance), a Fusion cross-check sheet
and an audit trail of the run.

Built only from a saved run folder, so the report always matches the run.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
from datetime import datetime
from html import escape
from importlib import resources
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402
from reportlab.graphics.shapes import Circle, Drawing, Line, PolyLine, Polygon, Rect, String  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.enums import TA_LEFT, TA_RIGHT  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle  # noqa: E402
from reportlab.lib.units import mm  # noqa: E402
from reportlab.pdfbase import pdfmetrics  # noqa: E402
from reportlab.pdfbase.ttfonts import TTFont  # noqa: E402
from reportlab.pdfgen import canvas as pdfcanvas  # noqa: E402
from reportlab.platypus import (  # noqa: E402
    BaseDocTemplate,
    CondPageBreak,
    Frame,
    Image,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from . import __version__  # noqa: E402
from .parts.padeye.geometry import PadeyeDesign  # noqa: E402

# ------------------------------------------------------------------ styling
INK = colors.HexColor("#1a1a1a")
MUTED = colors.HexColor("#5c5c5c")
FAINT = colors.HexColor("#8a8a8a")
RULE = colors.HexColor("#c8c8c8")
HAIR = colors.HexColor("#e2e2e2")
FILL = colors.HexColor("#f3f3f3")
ACCENT = colors.HexColor("#0a6fd6")
PASS = colors.HexColor("#1a7f4b")
FAIL = colors.HexColor("#c0341d")
ADVICE = colors.HexColor("#a85a00")

PAGE_W, PAGE_H = A4
MARGIN = 14 * mm
HEADER_H = 15 * mm
FOOTER_H = 16 * mm
CONTENT_W = PAGE_W - 2 * MARGIN

STRESS_CMAP = LinearSegmentedColormap.from_list("nemo", ["#1f4fbf", "#2bb3c0", "#8ad15c", "#f2c94c", "#e5484d"])

_FONTS_READY = False


def _fonts() -> None:
    global _FONTS_READY
    if _FONTS_READY:
        return
    folder = resources.files("nemo.data").joinpath("fonts")
    for name, file in (("Inter", "Inter-Regular.ttf"), ("Inter-Medium", "Inter-Medium.ttf"),
                       ("Inter-SemiBold", "Inter-SemiBold.ttf"), ("Inter-Italic", "Inter-Italic.ttf")):
        with resources.as_file(folder.joinpath(file)) as path:
            pdfmetrics.registerFont(TTFont(name, str(path)))
    pdfmetrics.registerFontFamily("Inter", normal="Inter", bold="Inter-SemiBold", italic="Inter-Italic",
                                  boldItalic="Inter-SemiBold")
    from matplotlib import font_manager

    for file in ("Inter-Regular.ttf", "Inter-Medium.ttf", "Inter-SemiBold.ttf"):
        with resources.as_file(folder.joinpath(file)) as path:
            font_manager.fontManager.addfont(str(path))
    matplotlib.rcParams["font.family"] = "Inter"
    _FONTS_READY = True


def _styles() -> dict[str, ParagraphStyle]:
    base = ParagraphStyle("body", fontName="Inter", fontSize=8.6, leading=12.2, textColor=INK)
    return {
        "body": base,
        "small": ParagraphStyle("small", parent=base, fontSize=7.4, leading=10, textColor=MUTED),
        "cell": ParagraphStyle("cell", parent=base, fontSize=7.8, leading=10.2),
        "cellr": ParagraphStyle("cellr", parent=base, fontSize=7.8, leading=10.2, alignment=TA_RIGHT),
        "cellm": ParagraphStyle("cellm", parent=base, fontSize=7.4, leading=9.6, textColor=MUTED),
        "h1": ParagraphStyle("h1", parent=base, fontName="Inter-SemiBold", fontSize=13, leading=17, spaceBefore=4, spaceAfter=6),
        "h2": ParagraphStyle("h2", parent=base, fontName="Inter-SemiBold", fontSize=9.6, leading=13, spaceBefore=10, spaceAfter=4),
        "title": ParagraphStyle("title", parent=base, fontName="Inter-SemiBold", fontSize=24, leading=28),
        "subtitle": ParagraphStyle("subtitle", parent=base, fontSize=11, leading=15, textColor=MUTED),
        "caption": ParagraphStyle("caption", parent=base, fontSize=7.2, leading=9.6, textColor=MUTED, alignment=TA_LEFT),
    }


def markup(text: str) -> str:
    """Formula markup (X_t, X_{eff}, x^2) to reportlab paragraph markup."""
    out = escape(text, quote=False)
    out = re.sub(r"_\{([^}]*)\}", r"<sub>\1</sub>", out)
    out = re.sub(r"(?<=[A-Za-zα-ωΑ-Ω])_([A-Za-z0-9])", r"<sub>\1</sub>", out)
    out = re.sub(r"\^\{([^}]*)\}", r"<super>\1</super>", out)
    out = re.sub(r"\^([0-9])", r"<super>\1</super>", out)
    return out


def n(value: float, digits: int = 2) -> str:
    return f"{value:,.{digits}f}".replace(",", "\u2009")


def kn(newtons: float) -> str:
    return f"{n(newtons / 1000, 2)} kN"


# --------------------------------------------------------------- page frame
class _NumberedCanvas(pdfcanvas.Canvas):
    """Draws 'page x of y' once the total is known."""

    def __init__(self, *args, meta: dict, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved: list[dict] = []
        self._meta = meta

    def showPage(self):  # noqa: N802 - reportlab API
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved)
        for state in self._saved:
            self.__dict__.update(state)
            _frame(self, self._pageNumber, total, self._meta)
            super().showPage()
        super().save()


def _frame(c: pdfcanvas.Canvas, page: int, total: int, meta: dict) -> None:
    c.saveState()
    left, right = MARGIN, PAGE_W - MARGIN
    top = PAGE_H - MARGIN
    # Header band
    c.setStrokeColor(INK)
    c.setLineWidth(0.8)
    c.line(left, top - HEADER_H, right, top - HEADER_H)
    c.setFont("Inter-SemiBold", 9.5)
    c.setFillColor(INK)
    c.drawString(left, top - 6.2 * mm, "NEMO")
    c.setFont("Inter", 8)
    c.setFillColor(MUTED)
    c.drawString(left + 13 * mm, top - 6.2 * mm, meta.get("kind", "Lifting padeye calculation"))
    c.drawString(left, top - 11 * mm, meta["project"])
    c.setFont("Inter", 7.2)
    for (label, value), x in zip((("Document", meta["doc"]), ("Revision", meta["rev"]), ("Page", f"{page} of {total}")),
                                 (right - 92 * mm, right - 40 * mm, right - 20 * mm)):
        c.setFillColor(FAINT)
        c.drawString(x, top - 5.6 * mm, label)
        c.setFillColor(INK)
        c.setFont("Inter-Medium", 7.6)
        c.drawString(x, top - 10.4 * mm, value)
        c.setFont("Inter", 7.2)
    # Footer title block
    bottom = MARGIN
    c.setStrokeColor(INK)
    c.setLineWidth(0.8)
    c.line(left, bottom + FOOTER_H, right, bottom + FOOTER_H)
    cells = (("Prepared", f"NEMO {__version__}"), ("Date", meta["date"]), ("Checked", ""), ("Approved", ""),
             ("Design", meta["design"]))
    width = (right - left) / len(cells)
    c.setLineWidth(0.4)
    c.setStrokeColor(RULE)
    for i, (label, value) in enumerate(cells):
        x = left + i * width
        if i:
            c.line(x, bottom + 3 * mm, x, bottom + FOOTER_H - 2 * mm)
        c.setFont("Inter", 6.6)
        c.setFillColor(FAINT)
        c.drawString(x + 2 * mm, bottom + FOOTER_H - 5 * mm, label)
        c.setFont("Inter-Medium", 7.6)
        c.setFillColor(INK)
        c.drawString(x + 2 * mm, bottom + FOOTER_H - 10 * mm, value)
    c.setFont("Inter", 6.4)
    c.setFillColor(FAINT)
    c.drawString(left, bottom - 4 * mm, "Design aid only. A competent engineer must review this calculation before fabrication or use.")
    c.restoreState()


# --------------------------------------------------------------- utilities
def _table(rows, widths, *, header=True, align_right=(), zebra=False, style_extra=()):
    t = Table(rows, colWidths=widths, repeatRows=1 if header else 0)
    style = [
        ("FONT", (0, 0), (-1, -1), "Inter", 7.8),
        ("TEXTCOLOR", (0, 0), (-1, -1), INK),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.2),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, HAIR),
    ]
    if header:
        style += [
            ("FONT", (0, 0), (-1, 0), "Inter-Medium", 7.2),
            ("TEXTCOLOR", (0, 0), (-1, 0), MUTED),
            ("BACKGROUND", (0, 0), (-1, 0), FILL),
            ("LINEBELOW", (0, 0), (-1, 0), 0.6, RULE),
            ("LINEABOVE", (0, 0), (-1, 0), 0.6, RULE),
        ]
    for col in align_right:
        style.append(("ALIGN", (col, 0), (col, -1), "RIGHT"))
    if zebra:
        for r in range(1 if header else 0, len(rows)):
            if r % 2 == 0:
                style.append(("BACKGROUND", (0, r), (-1, r), colors.HexColor("#fafafa")))
    t.setStyle(TableStyle(style + list(style_extra)))
    return t


def _kv(rows, s, widths=(52 * mm, None)):
    data = [[Paragraph(markup(k), s["cellm"]), Paragraph(markup(v), s["cell"])] for k, v in rows]
    w = [widths[0], CONTENT_W - widths[0]] if widths[1] is None else list(widths)
    return _table(data, w, header=False)


def _working_table(steps: list[dict], s, width: float = CONTENT_W) -> Table:
    rows = [["Quantity", "Formula", "With values", "Result"]]
    for st in steps:
        rows.append([
            Paragraph(markup(st["label"]), s["cell"]),
            Paragraph(markup(st["formula"]), s["cell"]),
            Paragraph(markup(st["substituted"]), s["cellm"]),
            Paragraph(f"<b>{markup(st['result'])}</b>", s["cellr"]),
        ])
    k = width / CONTENT_W
    return _table(rows, [40 * mm * k, 46 * mm * k, 72 * mm * k, width - 158 * mm * k])


def _status(check: dict) -> tuple[str, colors.Color]:
    if check["passed"]:
        return "PASS", PASS
    if check["severity"] == "advice":
        return "ADVICE", ADVICE
    return "FAIL", FAIL


def _value(value: float, unit: str) -> str:
    if unit == "N":
        return kn(value)
    if unit == "ratio":
        return n(value, 3)
    if unit == "t":
        return f"{n(value, 2)} t"
    return f"{n(value, 1)} {unit}"


def _png(fig, width_mm: float) -> Image:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=220, bbox_inches="tight", pad_inches=0.02, facecolor="white")
    plt.close(fig)
    buf.seek(0)
    img = Image(buf)
    ratio = img.imageHeight / img.imageWidth
    img.drawWidth = width_mm * mm
    img.drawHeight = width_mm * mm * ratio
    return img


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


# ----------------------------------------------------------------- figures
def _surface_figure(surface: dict, *, stress: bool, yield_mpa: float, view=(22, -58), width_in=4.6, height_in=3.6,
                    zoom: tuple[float, float, float] | None = None):
    p = np.asarray(surface["positions"], dtype=float).reshape(-1, 3)
    tri = np.asarray(surface["triangles"], dtype=int).reshape(-1, 3)
    verts = p[tri]
    normal = np.cross(verts[:, 1] - verts[:, 0], verts[:, 2] - verts[:, 0])
    normal /= np.maximum(np.linalg.norm(normal, axis=1, keepdims=True), 1e-12)
    light = np.array([0.45, -0.6, 0.66])
    shade = 0.55 + 0.45 * np.abs(normal @ (light / np.linalg.norm(light)))
    if stress:
        vm = np.asarray(surface["von_mises"], dtype=float)[tri].mean(axis=1)
        rgb = STRESS_CMAP(np.clip(vm / yield_mpa, 0, 1))[:, :3]
        face = np.clip(rgb * (0.75 + 0.25 * shade[:, None]), 0, 1)
    else:
        face = np.repeat((0.42 + 0.42 * shade)[:, None], 3, axis=1) * np.array([0.96, 0.98, 1.0])
    fig = plt.figure(figsize=(width_in, height_in))
    ax = fig.add_subplot(projection="3d")
    ax.add_collection3d(Poly3DCollection(verts, facecolors=face, edgecolors="none", linewidths=0))
    lo, hi = p.min(axis=0), p.max(axis=0)
    if zoom:
        cx, cz, r = zoom
        lo = np.array([cx - r, lo[1], cz - r])
        hi = np.array([cx + r, hi[1], cz + r])
    span = (hi - lo).max()
    centre = (lo + hi) / 2
    ax.set_xlim(centre[0] - span / 2, centre[0] + span / 2)
    ax.set_ylim(centre[1] - span / 2, centre[1] + span / 2)
    ax.set_zlim(centre[2] - span / 2, centre[2] + span / 2)
    ax.set_box_aspect((1, 1, 1), zoom=1.45)
    ax.view_init(elev=view[0], azim=view[1])
    ax.set_axis_off()
    if stress:
        sm = plt.cm.ScalarMappable(cmap=STRESS_CMAP, norm=plt.Normalize(0, yield_mpa))
        bar = fig.colorbar(sm, ax=ax, shrink=0.62, pad=0.02, aspect=22)
        bar.set_label("von Mises stress (MPa)", fontsize=7)
        bar.ax.tick_params(labelsize=6.5)
    fig.subplots_adjust(0, 0, 1, 1)
    return fig


def _convergence_figure(levels: list[dict]):
    fig, ax = plt.subplots(figsize=(3.3, 2.2))
    x = [lvl["elements"] for lvl in levels]
    y = [lvl["head_von_mises_mpa"] for lvl in levels]
    ax.plot(x, y, "-o", color="#1a1a1a", markersize=4, linewidth=1.2)
    for xi, yi in zip(x, y):
        ax.annotate(f"{yi:.1f}", (xi, yi), textcoords="offset points", xytext=(0, 6), ha="center", fontsize=6.5)
    ax.set_xscale("log")
    ax.set_xlabel("Elements", fontsize=7)
    ax.set_ylabel("Peak stress near hole (MPa)", fontsize=7)
    lo, hi = min(y), max(y)
    pad = max((hi - lo) * 2, hi * 0.08)
    ax.set_ylim(lo - pad, hi + pad)
    _clean(ax)
    return fig


def _search_figure(csv_path: Path, key: str, chosen_mass: float, cap: float):
    mass, use, ok = [], [], []
    with csv_path.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["target"] != key:
                continue
            mass.append(float(row["mass_kg"]))
            use.append(float(row["highest_use"]) * 100)
            ok.append(row["passes_target"] == "True")
    fig, ax = plt.subplots(figsize=(6.6, 2.6))
    if mass:
        m, u, f = np.array(mass), np.array(use), np.array(ok)
        keep = u < 400
        ax.scatter(m[keep & ~f], u[keep & ~f], s=3, color="#b9b9b9", linewidths=0, label="Fails a check")
        ax.scatter(m[keep & f], u[keep & f], s=3, color="#1a1a1a", linewidths=0, label="Passes every check")
        ax.set_xlim(0, np.percentile(m, 98) * 1.1)
    ax.axhline(cap * 100, color="#c0341d", linewidth=0.9, linestyle="--")
    ax.text(ax.get_xlim()[1], cap * 100, f" limit {cap * 100:.0f}%", va="center", ha="left", fontsize=6.5, color="#c0341d")
    ax.scatter([chosen_mass], [cap * 100], s=40, facecolors="none", edgecolors="#0a6fd6", linewidths=1.4, zorder=5)
    ax.annotate("chosen design", (chosen_mass, cap * 100), textcoords="offset points", xytext=(6, 14), fontsize=6.5, color="#0a6fd6",
                arrowprops={"arrowstyle": "-", "color": "#0a6fd6", "linewidth": 0.6})
    ax.set_ylim(0, max(cap * 100 * 2.2, 120))
    ax.set_xlabel("Plate mass (kg)", fontsize=7)
    ax.set_ylabel("Highest check use (%)", fontsize=7)
    ax.legend(fontsize=6.5, frameon=False, loc="upper right", markerscale=3)
    _clean(ax)
    return fig, len(mass)


def _clean(ax) -> None:
    ax.tick_params(labelsize=6.5, length=2.5, color="#999999")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#999999")
        ax.spines[side].set_linewidth(0.6)
    ax.grid(True, linewidth=0.3, color="#e5e5e5")


# ---------------------------------------------------- fabrication drawing
def _arrowhead(d: Drawing, x: float, y: float, angle: float, size: float = 5.0) -> None:
    a1, a2 = angle + math.radians(160), angle - math.radians(160)
    d.add(Polygon([x, y, x + size * math.cos(a1), y + size * math.sin(a1), x + size * math.cos(a2), y + size * math.sin(a2)],
                  fillColor=INK, strokeColor=INK, strokeWidth=0.3))


def _dim(d: Drawing, x1, y1, x2, y2, text, offset, *, horizontal=True):
    """Linear dimension with extension lines, arrows and a centred value."""
    thin = dict(strokeColor=INK, strokeWidth=0.45)
    if horizontal:
        yd = y1 + offset
        d.add(Line(x1, y1, x1, yd + math.copysign(3, offset), **thin))
        d.add(Line(x2, y2, x2, yd + math.copysign(3, offset), **thin))
        d.add(Line(x1, yd, x2, yd, **thin))
        _arrowhead(d, x1, yd, math.pi)
        _arrowhead(d, x2, yd, 0)
        d.add(String((x1 + x2) / 2, yd + 2.2, text, fontName="Inter", fontSize=7, textAnchor="middle", fillColor=INK))
    else:
        xd = x1 + offset
        d.add(Line(x1, y1, xd + math.copysign(3, offset), y1, **thin))
        d.add(Line(x2, y2, xd + math.copysign(3, offset), y2, **thin))
        d.add(Line(xd, y1, xd, y2, **thin))
        _arrowhead(d, xd, y1, -math.pi / 2)
        _arrowhead(d, xd, y2, math.pi / 2)
        lab = String(xd - 2.5, (y1 + y2) / 2 - 2.5, text, fontName="Inter", fontSize=7, textAnchor="end", fillColor=INK)
        d.add(lab)


def _leader(d: Drawing, x, y, angle, length, text):
    ex, ey = x + length * math.cos(angle), y + length * math.sin(angle)
    d.add(Line(x, y, ex, ey, strokeColor=INK, strokeWidth=0.45))
    _arrowhead(d, x, y, angle + math.pi)
    shelf = 16 if math.cos(angle) >= 0 else -16
    d.add(Line(ex, ey, ex + shelf, ey, strokeColor=INK, strokeWidth=0.45))
    d.add(String(ex + shelf + (2 if shelf > 0 else -2), ey - 2.4, text, fontName="Inter", fontSize=7,
                 textAnchor="start" if shelf > 0 else "end", fillColor=INK))


def _fabrication_drawing(design: PadeyeDesign, sling_angle: float) -> Drawing:
    width, height = CONTENT_W, 118 * mm
    d = Drawing(width, height)
    d.add(Rect(0, 0, width, height, strokeColor=RULE, strokeWidth=0.6, fillColor=None))
    top = design.hole_height_mm + design.head_radius_mm
    total_t = design.total_thickness_mm
    front_w, side_w = design.base_length_mm, max(total_t, 1)
    avail_w = width - 120
    scale = min(avail_w * 0.74 / front_w, (height - 70) / top, (avail_w * 0.26) / max(side_w * 4, 1) * 4)
    scale = min(scale, (height - 70) / top)
    ox, oy = 52 + front_w * scale / 2, 34

    def P(x, y):
        return ox + x * scale, oy + y * scale

    # Front view
    pts = []
    for x, y in design.outline_polyline(arc_segments=120):
        pts += list(P(x, y))
    d.add(Polygon(pts, fillColor=colors.HexColor("#f6f6f6"), strokeColor=INK, strokeWidth=1.0))
    cx, cy = P(0, design.hole_height_mm)
    if design.has_cheeks:
        d.add(Circle(cx, cy, design.cheek_radius_mm * scale, fillColor=None, strokeColor=INK, strokeWidth=0.8))
    d.add(Circle(cx, cy, design.hole_diameter_mm / 2 * scale, fillColor=colors.white, strokeColor=INK, strokeWidth=1.0))
    reach = design.head_radius_mm * scale + 8
    dash = dict(strokeColor=MUTED, strokeWidth=0.35, strokeDashArray=[6, 2, 1.5, 2])
    d.add(Line(cx - reach, cy, cx + reach, cy, **dash))
    d.add(Line(cx, oy - 6, cx, cy + reach, **dash))
    # Ground hatch under the base
    bx0, by = P(-front_w / 2 - 10, 0)
    bx1, _ = P(front_w / 2 + 10, 0)
    d.add(Line(bx0, by, bx1, by, strokeColor=INK, strokeWidth=0.6))
    step = 6
    x = bx0
    while x < bx1:
        d.add(Line(x, by, x - 4, by - 4, strokeColor=MUTED, strokeWidth=0.35))
        x += step
    # Sling direction
    a = math.radians(sling_angle)
    sx, sy = cx + (design.head_radius_mm * scale + 6) * math.cos(a), cy + (design.head_radius_mm * scale + 6) * math.sin(a)
    ex, ey = sx + 26 * math.cos(a), sy + 26 * math.sin(a)
    d.add(Line(sx, sy, ex, ey, strokeColor=ACCENT, strokeWidth=1.2))
    _arrowhead(d, ex, ey, a, 6)
    d.add(String(ex + 3, ey + 2, f"F at {sling_angle:g}°", fontName="Inter", fontSize=7, fillColor=ACCENT))

    # Dimensions
    lx, _ = P(-front_w / 2, 0)
    rx, _ = P(front_w / 2, 0)
    _dim(d, lx, by, rx, by, f"{design.base_length_mm:g}", -18)
    _dim(d, lx, by, lx, cy, f"{design.hole_height_mm:g}", -16, horizontal=False)
    _leader(d, cx + design.head_radius_mm * scale * math.cos(math.radians(125)),
            cy + design.head_radius_mm * scale * math.sin(math.radians(125)), math.radians(125), 22,
            f"R{design.head_radius_mm:g}")
    _leader(d, cx + design.hole_diameter_mm / 2 * scale * math.cos(math.radians(-35)),
            cy + design.hole_diameter_mm / 2 * scale * math.sin(math.radians(-35)), math.radians(-35),
            max(design.head_radius_mm * scale, 30), f"Ø{design.hole_diameter_mm:g} hole")
    if design.has_cheeks:
        _leader(d, cx + design.cheek_radius_mm * scale * math.cos(math.radians(205)),
                cy + design.cheek_radius_mm * scale * math.sin(math.radians(205)), math.radians(205), 26,
                f"Cheek R{design.cheek_radius_mm:g}")
    d.add(String(ox, height - 10, "FRONT VIEW", fontName="Inter-Medium", fontSize=7, textAnchor="middle", fillColor=MUTED))

    # Side view (section through thickness)
    sx0 = ox + front_w * scale / 2 + 70
    t, tc = design.main_thickness_mm, design.cheek_thickness_mm

    def S(x, y):
        return sx0 + x * scale, oy + y * scale

    x0, y0 = S(-t / 2, 0)
    d.add(Rect(x0, y0, t * scale, top * scale, fillColor=colors.HexColor("#f6f6f6"), strokeColor=INK, strokeWidth=1.0))
    if design.has_cheeks:
        for side in (-1, 1):
            xa = t / 2 if side > 0 else -t / 2 - tc
            rx0, ry0 = S(xa, design.hole_height_mm - design.cheek_radius_mm)
            d.add(Rect(rx0, ry0, tc * scale, 2 * design.cheek_radius_mm * scale, fillColor=colors.HexColor("#ececec"),
                       strokeColor=INK, strokeWidth=0.9))
    hidden = dict(strokeColor=MUTED, strokeWidth=0.45, strokeDashArray=[3, 2])
    for dy in (-1, 1):
        hx0, hy = S(-total_t / 2, design.hole_height_mm + dy * design.hole_diameter_mm / 2)
        hx1, _ = S(total_t / 2, 0)
        d.add(Line(hx0, hy, hx1, hy, **hidden))
    w = design.weld_leg_mm * scale
    for side in (-1, 1):
        xs, ys = S(side * t / 2, 0)
        d.add(Polygon([xs, ys, xs + side * w, ys, xs, ys + w], fillColor=INK, strokeColor=INK, strokeWidth=0.3))
    gx0, gy = S(-total_t / 2 - 12, 0)
    gx1, _ = S(total_t / 2 + 12, 0)
    d.add(Line(gx0, gy, gx1, gy, strokeColor=INK, strokeWidth=0.6))
    tx0, tyt = S(-t / 2, top)
    tx1, _ = S(t / 2, top)
    _dim(d, tx0, tyt, tx1, tyt, f"{t:g}", 14)
    if design.has_cheeks:
        cx0, cyt = S(t / 2, design.hole_height_mm + design.cheek_radius_mm)
        cx1, _ = S(t / 2 + tc, 0)
        d.add(String(cx1 + 3, cyt - 8, f"{tc:g} cheek", fontName="Inter", fontSize=7, fillColor=INK))
    wx, wy = S(t / 2 + design.weld_leg_mm, design.weld_leg_mm / 2)
    _leader(d, wx, wy, math.radians(20), 22, f"{design.weld_leg_mm:g} fillet, both sides")
    sv_x, _ = S(0, 0)
    d.add(String(sv_x, height - 10, "SIDE VIEW", fontName="Inter-Medium", fontSize=7, textAnchor="middle", fillColor=MUTED))

    d.add(String(8, 8, f"All dimensions in mm. Drawn at 1:{1 / (scale / (72 / 25.4)):.1f} on A4. Do not scale; use the dimensions.",
                 fontName="Inter", fontSize=6.5, fillColor=MUTED))
    return d


def _force_diagram(design: PadeyeDesign, loads: dict) -> Drawing:
    width, height = 62 * mm, 58 * mm
    d = Drawing(width, height)
    top = design.hole_height_mm + design.head_radius_mm
    scale = min((width - 30) / design.base_length_mm, (height - 30) / top) * 0.85
    ox, oy = width / 2 - 8, 12
    pts = []
    for x, y in design.outline_polyline(arc_segments=60):
        pts += [ox + x * scale, oy + y * scale]
    d.add(Polygon(pts, fillColor=colors.HexColor("#f2f2f2"), strokeColor=INK, strokeWidth=0.8))
    cx, cy = ox, oy + design.hole_height_mm * scale
    d.add(Circle(cx, cy, design.hole_diameter_mm / 2 * scale, fillColor=colors.white, strokeColor=INK, strokeWidth=0.8))
    a = math.radians(loads["sling_angle_deg"])
    length = 34
    ex, ey = cx + length * math.cos(a), cy + length * math.sin(a)
    d.add(Line(cx, cy, ex, ey, strokeColor=ACCENT, strokeWidth=1.4))
    _arrowhead(d, ex, ey, a, 6)
    d.add(String(ex + 2, ey + 3, "F", fontName="Inter-SemiBold", fontSize=8, fillColor=ACCENT))
    comp = dict(strokeColor=MUTED, strokeWidth=0.6, strokeDashArray=[2, 1.5])
    d.add(Line(cx, cy, ex, cy, **comp))
    d.add(Line(ex, cy, ex, ey, **comp))
    d.add(String((cx + ex) / 2, cy - 8, "H", fontName="Inter", fontSize=7, fillColor=MUTED, textAnchor="middle"))
    d.add(String(ex + 3, (cy + ey) / 2, "V", fontName="Inter", fontSize=7, fillColor=MUTED))
    d.add(PolyLine([cx + 12, cy, cx + 12 * math.cos(a / 2) * 1.0, cy + 12 * math.sin(a / 2)], strokeColor=MUTED, strokeWidth=0.4))
    d.add(String(cx + 14, cy + 3, "θ", fontName="Inter", fontSize=7, fillColor=MUTED))
    bx0, bx1 = ox - design.base_length_mm / 2 * scale - 6, ox + design.base_length_mm / 2 * scale + 6
    x = bx0
    d.add(Line(bx0, oy, bx1, oy, strokeColor=INK, strokeWidth=0.6))
    while x < bx1:
        d.add(Line(x, oy, x - 3, oy - 3, strokeColor=MUTED, strokeWidth=0.3))
        x += 4.5
    return d


# ------------------------------------------------------------------ report
def build_report_pdf(run_dir: Path, design_key: str, *, project_name: str, run_name: str, target: Path) -> Path:
    _fonts()
    s = _styles()
    results = json.loads((run_dir / "results.json").read_text(encoding="utf-8"))
    if results.get("part", "padeye") != "padeye":
        from .report_parts import build_part_report

        return build_part_report(run_dir, results, design_key, project_name=project_name, run_name=run_name, target=target)
    entry = next((x for x in results["designs"] if x["key"] == design_key), None)
    if entry is None:
        raise KeyError(design_key)
    report = entry["check_report"]
    design = PadeyeDesign(**report["design"])
    loads = results["loads"]
    lift = results["job"]["lift"]
    rule = results["rule_set"]
    material = results["material"]
    shackle = report["shackle"]
    values = report["values"]
    fea = entry.get("fea")
    created = results.get("created_at", "")
    date = (datetime.fromisoformat(created).astimezone().strftime("%d %b %Y") if created else datetime.now().strftime("%d %b %Y"))
    doc_no = f"NEMO-{run_name[:8]}-{run_name[9:15]}-{design_key[:1].upper()}"
    meta = {"project": project_name, "doc": doc_no, "rev": "A", "date": date, "design": entry["label"].split(" (")[0]}
    surface = None
    if entry["files"].get("stress_surface"):
        path = run_dir / entry["files"]["stress_surface"]
        if path.exists():
            surface = json.loads(path.read_text(encoding="utf-8"))

    story: list = []
    governing = next(c for c in report["checks"] if c["id"] == report["governing"])
    passed = report["passed"]
    fea_ok = bool(fea and fea["converged"] and fea["factor_of_safety_on_yield"] >= 1.0)

    # ---------------------------------------------------------- 1 Summary
    story += [Spacer(1, 6 * mm), Paragraph("Lifting padeye", s["title"]),
              Paragraph(f"{escape(entry['label'])} design for {escape(project_name)}", s["subtitle"]), Spacer(1, 6 * mm)]
    verdict = Table([[Paragraph(
        f"<font color='{(PASS if passed else FAIL).hexval()}'><b>{'Passes' if passed else 'Does not pass'} every required check</b></font>"
        f"<br/><font size=7.6 color='#5c5c5c'>Governing check: {escape(governing['title'])}, "
        f"{governing['utilization'] * 100:.0f}% of capacity. Stress check: "
        f"{'pass' if fea_ok else ('not run' if not fea else 'review')}.</font>", s["body"])]],
        colWidths=[CONTENT_W])
    verdict.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.9, PASS if passed else FAIL),
                                 ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 7),
                                 ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    story.append(verdict)
    story.append(Spacer(1, 5 * mm))
    summary_rows = [
        ("Load lifted", f"{n(lift['lifted_mass_kg'], 0)} kg on {lift['lift_points']} padeyes, slings at {lift['sling_angle_deg']:g}°"),
        ("Sling force on one padeye", f"{kn(loads['sling_force_n'])} ({n(loads['sling_force_t'], 2)} t)"),
        ("Shackle", shackle["label"]),
        ("Main plate", f"{design.main_thickness_mm:g} mm {material['name']}"),
        ("Cheek plates", f"2 × {design.cheek_thickness_mm:g} mm, R{design.cheek_radius_mm:g}" if design.has_cheeks else "None"),
        ("Plate mass", f"{n(report['mass_kg'], 2)} kg (weld metal not included)"),
        ("Design rules", f"{rule['name']}, category {rule['design_category']}, service class {rule['service_class']}"),
    ]
    if fea:
        summary_rows.append(("Peak stress (FEA)", f"{n(fea['head_von_mises_mpa'], 1)} MPa, safety factor on yield {n(fea['factor_of_safety_on_yield'], 2)}"))
    left = _kv(summary_rows, s, widths=(38 * mm, 64 * mm))
    if surface:
        img = _png(_surface_figure(surface, stress=False, yield_mpa=1, width_in=3.1, height_in=3.1), 70)
        story.append(Table([[left, img]], colWidths=[104 * mm, CONTENT_W - 104 * mm],
                           style=[("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    else:
        story.append(left)
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Contents", s["h2"]))
    contents = ["1  Summary", "2  Design basis", "3  Fabrication drawing", "4  Design search", "5  Calculation sheets",
                "6  Finite element analysis", "7  Fusion cross-check sheet", "8  Limitations", "A  Audit trail"]
    story.append(Paragraph("<br/>".join(contents), s["body"]))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Revision history", s["h2"]))
    story.append(_table([["Rev", "Date", "Description", "By"], ["A", date, "First issue, generated from run " + run_name, f"NEMO {__version__}"]],
                        [12 * mm, 26 * mm, CONTENT_W - 68 * mm, 30 * mm]))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        "This calculation is a design aid. A competent engineer must review it, together with the supporting structure, "
        "the rigging arrangement and the welding procedure, before the padeye is made or used. The vessel's classification "
        "society, flag state or lift contract can require other rules and change the result.", s["small"]))
    story.append(PageBreak())

    # ------------------------------------------------------ 2 Design basis
    story.append(Paragraph("2  Design basis", s["h1"]))
    story.append(Paragraph("2.1  Forces on one padeye", s["h2"]))
    lw = _working_table(results.get("load_steps", []), s, width=CONTENT_W - 66 * mm)
    story.append(Table([[lw, _force_diagram(design, loads)]], colWidths=[CONTENT_W - 64 * mm, 64 * mm],
                       style=[("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    story.append(Paragraph("θ: sling angle from horizontal. The padeye plate lies in the plane of its sling.", s["caption"]))
    story.append(Paragraph("2.2  Material", s["h2"]))
    story.append(_kv([
        ("Grade", material["name"]),
        ("Standard", material["source"]),
        ("Yield strength used, F_y", f"{n(values['yield_main_mpa'], 0)} MPa main plate; {n(values['yield_head_mpa'], 0)} MPa at the hole"),
        ("Tensile strength, F_u", f"{n(material['tensile_strength_mpa'], 0)} MPa"),
        ("Elastic modulus, E", f"{n(material['elastic_modulus_gpa'], 0)} GPa"),
        ("Density", f"{n(material['density_kg_m3'], 0)} kg/m³"),
    ], s))
    story.append(Paragraph("2.3  Shackle", s["h2"]))
    story.append(_kv([
        ("Shackle", shackle["label"]),
        ("Working load limit", f"{shackle['wll_t']:g} t (minimum breaking strength 6 × WLL)"),
        ("Pin diameter, D_p", f"{n(shackle['pin_diameter_mm'], 1)} mm"),
        ("Jaw width", f"{n(shackle['jaw_width_mm'], 1)} mm"),
        ("Source", "The Crosby Group, G-2130 / S-2130 bolt type anchor shackles, 2019 catalogue"),
    ], s))
    story.append(Paragraph("2.4  Design rules and factors", s["h2"]))
    story.append(_kv([
        ("Rule set", rule["name"]),
        ("Design category", f"{rule['design_category']} ({'uncertain loads or severe conditions' if rule['design_category'] == 'B' else 'predictable loads'})"),
        ("Design factor, N_d", n(rule["design_factor"], 2)),
        ("Pin-connected plates", f"1.20 N_d = {n(rule['pin_connection_design_factor'], 2)}"),
        ("Service class", f"{rule['service_class']}"),
        ("Dynamic factor", n(lift["dynamic_factor"], 2)),
        ("Weld metal, E_{xx}", f"{n(results['job'].get('electrode_strength_mpa', 482), 0)} MPa (E70XX class)"),
    ], s))
    story.append(PageBreak())

    # --------------------------------------------------- 3 Fabrication drawing
    story.append(Paragraph("3  Fabrication drawing", s["h1"]))
    story.append(_fabrication_drawing(design, lift["sling_angle_deg"]))
    story.append(Spacer(1, 4 * mm))
    density = material["density_kg_m3"] * 1e-9
    main_mass = design.main_plate_area_mm2() * design.main_thickness_mm * density
    parts = [["Item", "Part", "Material", "Thickness", "Qty", "Mass each"],
             ["1", "Main plate, profile cut, Ø" + f"{design.hole_diameter_mm:g} hole", material["name"], f"{design.main_thickness_mm:g} mm", "1", f"{n(main_mass, 2)} kg"]]
    if design.has_cheeks:
        cheek_mass = design.cheek_area_mm2() * design.cheek_thickness_mm * density
        parts.append(["2", f"Cheek plate, ring R{design.cheek_radius_mm:g} / Ø{design.hole_diameter_mm:g}", material["name"],
                      f"{design.cheek_thickness_mm:g} mm", "2", f"{n(cheek_mass, 2)} kg"])
    story.append(Paragraph("Parts list", s["h2"]))
    story.append(_table(parts, [12 * mm, 70 * mm, 46 * mm, 20 * mm, 12 * mm, CONTENT_W - 160 * mm], align_right=(3, 4, 5)))
    notes = [
        f"Base: {design.weld_leg_mm:g} mm fillet weld both sides, full length {design.base_length_mm:g} mm"
        + (f". Cheek plates: {design.cheek_weld_leg_mm:g} mm fillet weld all round, both cheeks." if design.has_cheeks else "."),
        "Bore the hole after welding the cheek plates, so the hole is round and the plates line up.",
        "Weld to a qualified procedure. Inspect welds as the lift plan or class requires.",
        "Orient the padeye in the plane of the sling. Check the supporting structure separately.",
        "Cutting profiles are supplied as DXF at full size (layer CUT).",
    ]
    story.append(Paragraph("Notes", s["h2"]))
    story.append(Paragraph("<br/>".join(f"{i}.  {escape(t)}" for i, t in enumerate(notes, 1)), s["body"]))
    story.append(PageBreak())

    # ------------------------------------------------------ 4 Design search
    story.append(Paragraph("4  Design search", s["h1"]))
    search = results["search"]
    story.append(Paragraph(
        f"NEMO tried every stock plate thickness and cheek plate combination that fits the shackle, and for each one "
        f"used a bounded Nelder-Mead search over head radius, base length and cheek radius for the least mass with every "
        f"strength check at or below its target. In total it checked {n(search['evaluations'], 0)} designs across "
        f"{search['combinations']} combinations and skipped {search['skipped']} that could not beat the best found. "
        f"Each design was then rounded up to whole millimetres (base length to 5 mm) and the smallest standard welds were chosen.",
        s["body"]))
    csv_path = run_dir / "designs-evaluated.csv"
    if csv_path.exists():
        fig, count = _search_figure(csv_path, design_key, report["mass_kg"], entry["target_utilization"])
        story.append(Spacer(1, 3 * mm))
        story.append(_png(fig, CONTENT_W / mm))
        story.append(Paragraph(f"Each dot is one of the {n(count, 0)} designs tried for this target. The chosen design is the "
                               "lightest one at or below the limit after rounding to buildable sizes.", s["caption"]))
    story.append(Paragraph("Designs offered", s["h2"]))
    rows = [["Design", "Plate", "Cheeks", "R", "Base", "Weld", "Shackle", "Mass", "Highest use"]]
    for other in results["designs"]:
        od, orp = other["check_report"]["design"], other["check_report"]
        og = next(c for c in orp["checks"] if c["id"] == orp["governing"])
        rows.append([other["label"].split(" (")[0] + (" (this report)" if other["key"] == design_key else ""),
                     f"{od['main_thickness_mm']:g}", f"{od['cheek_thickness_mm']:g}" if od["cheek_thickness_mm"] else "-",
                     f"{od['head_radius_mm']:g}", f"{od['base_length_mm']:g}", f"{od['weld_leg_mm']:g}",
                     f"{orp['shackle']['wll_t']:g} t", f"{n(orp['mass_kg'], 2)} kg", f"{og['utilization'] * 100:.0f}%"])
    story.append(_table(rows, [38 * mm, 15 * mm, 15 * mm, 13 * mm, 15 * mm, 13 * mm, 20 * mm, 22 * mm, CONTENT_W - 151 * mm],
                        align_right=(1, 2, 3, 4, 5, 6, 7, 8)))
    story.append(Paragraph("Dimensions in mm.", s["caption"]))
    story.append(PageBreak())

    # -------------------------------------------------- 5 Calculation sheets
    story.append(Paragraph("5  Calculation sheets", s["h1"]))
    story.append(Paragraph("Each check compares the demand on the padeye with the capacity allowed by the rules. "
                           "Use = demand / capacity; up to 100% passes. Practice checks are workshop or rigging rules, "
                           "not design-code clauses. Advice items do not fail the design on their own.", s["body"]))
    rows = [["", "Check", "Demand", "Capacity", "Use", "Result"]]
    style_extra = []
    for i, c in enumerate(report["checks"], 1):
        label, colour = _status(c)
        rows.append([f"5.{i}", Paragraph(markup(c["title"]), s["cell"]), _value(c["demand"], c["unit"]),
                     _value(c["capacity"], c["unit"]), f"{c['utilization'] * 100:.0f}%", label])
        style_extra += [("TEXTCOLOR", (5, i), (5, i), colour), ("FONT", (5, i), (5, i), "Inter-SemiBold", 7.4)]
    story.append(Spacer(1, 2 * mm))
    story.append(_table(rows, [11 * mm, 74 * mm, 26 * mm, 26 * mm, 16 * mm, CONTENT_W - 153 * mm],
                        align_right=(2, 3, 4), style_extra=style_extra))
    for i, c in enumerate(report["checks"], 1):
        label, colour = _status(c)
        block = [
            Paragraph(f"5.{i}  {markup(c['title'])}", s["h2"]),
            Paragraph(f"{escape(c['source'])}. {escape(c['explanation'])}", s["small"]),
            Spacer(1, 1.5 * mm),
        ]
        if c.get("working"):
            block.append(_working_table(c["working"], s))
        verdict_line = (f"Demand {_value(c['demand'], c['unit'])} against capacity {_value(c['capacity'], c['unit'])}: "
                        f"use {c['utilization'] * 100:.1f}%  "
                        f"<font color='{colour.hexval()}'><b>{label}</b></font>")
        block.append(Spacer(1, 1.2 * mm))
        block.append(Paragraph(verdict_line, s["body"]))
        story.append(CondPageBreak(42 * mm))
        story.append(KeepTogether(block))
    story.append(PageBreak())

    # --------------------------------------------------------------- 6 FEA
    story.append(Paragraph("6  Finite element analysis", s["h1"]))
    if not fea:
        story.append(Paragraph("The stress check was not run for this design.", s["body"]))
    else:
        story.append(Paragraph("6.1  Model", s["h2"]))
        story.append(_kv([
            ("Geometry", "The exported STEP solid (main plate and cheek plates as one body). Welds not modelled."),
            ("Elements", "Quadratic tetrahedra (10-node), linear elastic, isotropic"),
            ("Material", f"E = {n(material['elastic_modulus_gpa'], 0)} GPa, ν = 0.30"),
            ("Support", "Base face fixed in all directions (welded to rigid structure)"),
            ("Pin load", f"Cosine pressure on the half of the hole facing the sling, scaled to F = {kn(loads['sling_force_n'])} at {lift['sling_angle_deg']:g}°"),
            ("Side load", f"Same distribution, scaled to Q = {kn(loads['side_n'])} through the plate"),
            ("Solver", "scikit-fem assembly; multigrid-preconditioned conjugate gradients, direct solver for small models"),
        ], s))
        story.append(Paragraph("6.2  Mesh convergence", s["h2"]))
        mrows = [["Mesh", "Element size, hole / overall", "Elements", "Equations", "Peak stress near hole", "Largest movement", "Solve time"]]
        for lvl in fea["levels"]:
            mrows.append([str(lvl["level"]), f"{n(lvl['local_size_mm'], 2)} / {n(lvl['global_size_mm'], 1)} mm",
                          n(lvl["elements"], 0), n(lvl["dofs"], 0), f"{n(lvl['head_von_mises_mpa'], 1)} MPa",
                          f"{n(lvl['max_displacement_mm'], 4)} mm", f"{n(lvl['solve_seconds'], 1)} s"])
        mesh_table = _table(mrows, [11 * mm, 38 * mm, 18 * mm, 20 * mm, 28 * mm, 24 * mm, CONTENT_W - 139 * mm], align_right=(2, 3, 4, 5, 6))
        story.append(mesh_table)
        story.append(Spacer(1, 3 * mm))
        conv = _png(_convergence_figure(fea["levels"]), 80)
        conv_text = Paragraph(
            f"The peak stress changed by <b>{fea['convergence_change'] * 100:.2f}%</b> between the two finest meshes "
            f"(target 5% or less), so the result does not depend on the mesh. "
            "The sharp corner where the base meets the fixed support is a known modelling singularity; stress there keeps "
            "rising as the mesh gets finer, so the reported peak is taken in the head region only.", s["body"])
        story.append(Table([[conv, conv_text]], colWidths=[84 * mm, CONTENT_W - 84 * mm],
                           style=[("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
        if surface:
            story.append(CondPageBreak(90 * mm))
            story.append(Paragraph("6.3  Stress contours", s["h2"]))
            whole = _png(_surface_figure(surface, stress=True, yield_mpa=fea["yield_strength_mpa"], width_in=3.6, height_in=3.2), 88)
            head = _png(_surface_figure(surface, stress=True, yield_mpa=fea["yield_strength_mpa"], view=(8, -90), width_in=3.6, height_in=3.2,
                                        zoom=(0.0, design.hole_height_mm, design.head_radius_mm * 1.25)), 88)
            story.append(Table([[whole, head]], colWidths=[CONTENT_W / 2] * 2, style=[("LEFTPADDING", (0, 0), (-1, -1), 0)]))
            story.append(Paragraph(f"Von Mises stress on the finest mesh, scale 0 to yield ({n(fea['yield_strength_mpa'], 0)} MPa). "
                                   "Left: whole padeye. Right: head, viewed along the hole.", s["caption"]))
        last = fea["levels"][-1]
        story.append(Paragraph("6.4  Force balance", s["h2"]))
        ap, re_ = last["applied_force_n"], last["reaction_force_n"]
        story.append(_table([["", "X (along base)", "Y (through plate)", "Z (up)"],
                             ["Applied load", kn(ap[0]), kn(ap[1]), kn(ap[2])],
                             ["Support reaction", kn(re_[0]), kn(re_[1]), kn(re_[2])],
                             ["Sum", *(kn(0.0 if abs(a + b) < 0.5 else a + b) for a, b in zip(ap, re_))]],
                            [40 * mm] + [(CONTENT_W - 40 * mm) / 3] * 3, align_right=(1, 2, 3)))
        story.append(Paragraph(f"Relative balance error {last['reaction_balance_error']:.1e}. The load applied in the model "
                               "is the load calculated in section 2; nothing is typed by hand.", s["caption"]))
        story.append(Paragraph("6.5  Result", s["h2"]))
        story.append(Paragraph(
            f"Peak von Mises stress near the hole {n(fea['head_von_mises_mpa'], 1)} MPa against yield "
            f"{n(fea['yield_strength_mpa'], 0)} MPa: safety factor on yield <b>{n(fea['factor_of_safety_on_yield'], 2)}</b>. "
            f"<font color='{(PASS if fea_ok else FAIL).hexval()}'><b>{'PASS' if fea_ok else 'REVIEW'}</b></font>. "
            "The peak is a local contact stress under the pin and is higher than the average stresses ASME BTH-1 limits, "
            "so its safety factor is lower than the code's design factor. It must stay below yield.", s["body"]))
    story.append(PageBreak())

    # -------------------------------------------------- 7 Fusion cross-check
    story.append(Paragraph("7  Fusion cross-check sheet", s["h1"]))
    story.append(Paragraph("Use these values to repeat the stress check independently in Autodesk Fusion (Simulation, "
                           "Static Stress). Open the STEP file from this run, in millimetres.", s["body"]))
    ap = fea["levels"][-1]["applied_force_n"] if fea else [loads["horizontal_n"], loads["side_n"], loads["vertical_n"]]
    story.append(Spacer(1, 2 * mm))
    story.append(_table([["Step", "Setting", "Value"],
                         ["1", "Study type", "Static Stress"],
                         ["2", "Material", f"{material['name']}: E {n(material['elastic_modulus_gpa'], 0)} GPa, ν 0.30, density {n(material['density_kg_m3'], 0)} kg/m³, yield {n(values['yield_main_mpa'], 0)} MPa"],
                         ["3", "Fixed constraint", "Flat base face, all directions"],
                         ["4", "Bearing load on hole", f"Total {kn(loads['sling_force_n'])} at {lift['sling_angle_deg']:g}° from the base, in the plane of the plate"],
                         ["5", "Force components", f"X {kn(ap[0])}, Y {kn(ap[1])}, Z {kn(ap[2])}"],
                         ["6", "Expected reaction", f"X {kn(-ap[0])}, Y {kn(-ap[1])}, Z {kn(-ap[2])}"],
                         ["7", "Mesh", "Local refinement on the hole, at least 3 elements through the thickness"],
                         ["8", "Compare", f"Reaction equals the applied load within 2%; peak stress near the hole within 15% of {n(fea['head_von_mises_mpa'], 1) if fea else '-'} MPa"]],
                        [12 * mm, 40 * mm, CONTENT_W - 52 * mm]))
    story.append(Spacer(1, 6 * mm))
    folder = run_dir / "designs" / design_key
    xc_path, fm_path = folder / "fusion-crosscheck.json", folder / "fusion-model.json"
    xc = json.loads(xc_path.read_text(encoding="utf-8")) if xc_path.exists() else None
    fm = json.loads(fm_path.read_text(encoding="utf-8")) if fm_path.exists() else None

    def pct(d):
        return "-" if d is None else f"{d * 100:+.1f}%"

    def when(stamp: str | None) -> str:
        try:
            return datetime.fromisoformat(stamp).astimezone().strftime("%d %b %Y, %H:%M")
        except (TypeError, ValueError):
            return stamp or "-"

    if xc:
        rows = [["Result", "Fusion", "NEMO", "Difference"],
                ["Reaction force", kn(xc["reaction_n"]) if xc["reaction_n"] is not None else "-",
                 kn(xc["nemo_reaction_n"]) if xc["nemo_reaction_n"] else "-", pct(xc["reaction_difference"])],
                ["Peak stress near hole", f"{n(xc['peak_stress_mpa'], 1)} MPa" if xc["peak_stress_mpa"] is not None else "-",
                 f"{n(xc['nemo_peak_stress_mpa'], 1)} MPa" if xc["nemo_peak_stress_mpa"] else "-", pct(xc["stress_difference"])],
                ["Largest movement", f"{n(xc['max_displacement_mm'], 4)} mm" if xc["max_displacement_mm"] is not None else "-",
                 f"{n(xc['nemo_max_displacement_mm'], 4)} mm" if xc["nemo_max_displacement_mm"] else "-", pct(xc["displacement_difference"])]]
        story.append(Paragraph("Fusion results recorded", s["h2"]))
        story.append(_table(rows, [50 * mm, 40 * mm, 40 * mm, CONTENT_W - 130 * mm], align_right=(1, 2, 3)))
        story.append(Spacer(1, 2 * mm))
        verdict = "agrees with" if xc["agrees"] else "differs from"
        story.append(Paragraph(
            f"Recorded {escape(when(xc['recorded_at']))}{' by ' + escape(xc['checked_by']) if xc['checked_by'] else ''}. "
            f"The Fusion study <b>{verdict}</b> NEMO (reaction within 2%, peak stress within 15%; movement is for information only).", s["caption"]))
    else:
        story.append(_table([["Result in Fusion", "Value", "Agrees with NEMO?"], ["Reaction force", "", ""], ["Peak stress near hole", "", ""],
                             ["Largest movement", "", ""], ["Checked by / date", "", ""]],
                            [60 * mm, 60 * mm, CONTENT_W - 120 * mm],
                            style_extra=[("BOTTOMPADDING", (0, 1), (-1, -1), 10), ("TOPPADDING", (0, 1), (-1, -1), 10),
                                         ("GRID", (0, 0), (-1, -1), 0.4, RULE)]))
        story.append(Paragraph("Fill in by hand, or use the NEMO cross-check sheet inside Fusion to record the results "
                               "and reissue this report.", s["caption"]))
    if fm:
        built_in = f" in Fusion {fm['fusion_version']}" if fm.get("fusion_version") else ""
        vol = fm.get("volume_difference")
        vol_text = "-" if vol is None else f"{vol * 100:+.2f}%"
        story.append(Paragraph(
            f"Fusion model built{escape(built_in)} from NEMO's parameters on {escape(when(fm.get('recorded_at')))}: "
            f"{'parametric' if fm.get('parametric') else 'fixed geometry'}, volume "
            f"{n(fm['volume_mm3'], 0)} mm³ against NEMO's {n(fm['nemo_volume_mm3'], 0)} mm³ ({vol_text}).",
            s["caption"]))

    # ------------------------------------------------------- 8 Limitations
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph("8  Limitations", s["h1"]))
    limits = [
        "The supporting deck, bulkhead or member must be checked separately for the same forces.",
        "Lamellar tearing of thick supporting plate is not checked. Use through-thickness (Z-grade) plate where required.",
        f"Fatigue is covered only through the chosen service class ({rule['service_class']}).",
        "No corrosion allowance is included. Add one if the padeye stays in service.",
        "Shackle ratings assume an in-line pull. Apply the maker's reduction for side loading.",
        "Welds are assumed sound, made and inspected to a qualified procedure.",
        "Proof load testing is not covered and may be required by the lifting standard for the job.",
    ]
    story.append(Paragraph("<br/>".join(f"{i}.  {escape(t)}" for i, t in enumerate(limits, 1)), s["body"]))
    story.append(PageBreak())

    # ---------------------------------------------------------- A Audit trail
    story.append(Paragraph("A  Audit trail", s["h1"]))
    log_path = run_dir / "engineering-log.json"
    events = json.loads(log_path.read_text(encoding="utf-8")) if log_path.exists() else []
    start = next((e for e in events if e["kind"] == "start"), {})
    story.append(Paragraph("Software", s["h2"]))
    story.append(_kv([
        ("NEMO", __version__),
        ("Python", start.get("python", "-")),
        ("Run", run_name),
        ("Run time", f"{n(results.get('seconds', 0), 1)} s"),
        ("Libraries", "build123d / OpenCASCADE (geometry), Gmsh (mesh), scikit-fem and PyAMG (FEA), ReportLab (this report)"),
    ], s))
    story.append(Paragraph("Inputs as entered", s["h2"]))
    job = results["job"]
    story.append(_kv([
        ("Lifted mass", f"{n(lift['lifted_mass_kg'], 0)} kg"),
        ("Lifting points / carrying", f"{lift['lift_points']} / {lift['points_carrying'] or lift['lift_points']}"),
        ("Sling angle", f"{lift['sling_angle_deg']:g}°"),
        ("Dynamic factor", n(lift["dynamic_factor"], 2)),
        ("Sideways allowance", f"{lift['side_load_fraction'] * 100:g}%"),
        ("Material", job["material_id"]),
        ("Plates in stock", ", ".join(f"{t:g}" for t in job["plate_thicknesses_mm"]) + " mm"),
        ("Cheek plates allowed", "Yes" if job["allow_cheek_plates"] else "No"),
        ("Keep 60% jaw fill", "Yes" if job["fill_shackle_jaw"] else "No"),
    ], s))
    story.append(Paragraph("Stage timings", s["h2"]))
    stages = []
    for e in events:
        if e["kind"] in ("loads", "shackles", "search_done", "cad", "fea_done", "done"):
            label = {"loads": "Forces calculated", "shackles": "Shackles chosen", "search_done": "Design search finished",
                     "cad": f"3D model built ({e.get('target', '')})", "fea_done": f"Stress check finished ({e.get('target', '')})",
                     "done": "Run finished"}[e["kind"]]
            stages.append([f"{n(e['t'], 1)} s", label])
    if stages:
        story.append(_table([["Time", "Event"]] + stages, [24 * mm, CONTENT_W - 24 * mm], align_right=(0,)))
    story.append(Paragraph("Files in this run", s["h2"]))
    files = [("results.json", "Summary of the run")]
    files += [(entry["files"][k], d) for k, d in (("step", "3D model"), ("dxf", "Cutting profile"), ("stl", "Mesh for viewing"))]
    files += [("engineering-log.json", "Every engineering event, in order"), ("designs-evaluated.csv", "Every design the search tried")]
    frows = [["File", "Contents", "SHA-256 (first 16)"]]
    for rel, desc in files:
        path = run_dir / rel
        if path.exists():
            frows.append([Paragraph(escape(rel.replace("\\", "/")), s["cell"]), desc, _sha256(path)[:16]])
    story.append(_table(frows, [70 * mm, 52 * mm, CONTENT_W - 122 * mm]))
    story.append(Paragraph("The checksum identifies each file exactly: a file changed after this report was issued will have a different checksum.", s["caption"]))

    target.parent.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(str(target), pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
                          topMargin=MARGIN + HEADER_H + 5 * mm, bottomMargin=MARGIN + FOOTER_H + 5 * mm,
                          title=f"{project_name} - padeye calculation", author=f"NEMO {__version__}",
                          subject=doc_no)
    frame = Frame(MARGIN, MARGIN + FOOTER_H + 5 * mm, CONTENT_W, PAGE_H - 2 * MARGIN - HEADER_H - FOOTER_H - 10 * mm,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="page", frames=[frame])])
    doc.build(story, canvasmaker=lambda *a, **k: _NumberedCanvas(*a, meta=meta, **k))
    return target
