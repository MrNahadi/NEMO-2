"""3D models of the stabilizer fin: the whole fin (for STEP) and the stock (for the stress check).

Axes as in ``geometry.py``: x along the chord, y across the foil, z along the
span from the hull (z = 0) to the tip. The stock runs from the outer bearing
(z = -bearing gap) into the fin.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import ezdxf
import numpy as np
from build123d import Box, BuildLine, BuildSketch, Cylinder, Part, Plane, Polyline, Pos, export_step, export_stl, extrude, make_face

from ...hydro import naca_thickness
from .geometry import FinDesign


@dataclass(frozen=True)
class FinSolid:
    part: Part
    design: FinDesign

    @property
    def volume_mm3(self) -> float:
        return float(self.part.volume)

    @property
    def solid_count(self) -> int:
        return len(self.part.solids())

    def export_step(self, path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not export_step(self.part, str(target)):
            raise RuntimeError(f"STEP export failed: {target}")
        return target

    def export_stl(self, path, tolerance_mm: float = 0.2) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not export_stl(self.part, str(target), tolerance=tolerance_mm):
            raise RuntimeError(f"STL export failed: {target}")
        return target


def inner_outline(design: FinDesign, points: int = 90) -> list[tuple[float, float]]:
    """Inside of the skin, trimmed where the foil gets too thin to have an inside."""
    c, t = design.chord_mm, design.skin_mm
    x = np.linspace(0.0, 1.0, 2001)
    y = naca_thickness(x, design.thickness_ratio) * c
    slope = np.gradient(y, x * c)
    inner = y - t * np.sqrt(1.0 + slope**2)
    ok = np.where(inner > 0.75 * t)[0]
    x0, x1 = x[ok[0]], x[ok[-1]]
    xs = np.linspace(x0, x1, points)
    ys = np.interp(xs, x, inner)
    upper = [(float(a) * c, float(b)) for a, b in zip(xs, ys)]
    lower = [(float(a) * c, -float(b)) for a, b in zip(xs[::-1], ys[::-1])]
    return upper + lower + [upper[0]]


def _prism(points: list[tuple[float, float]], z0: float, height: float) -> Part:
    with BuildSketch(Plane.XY.offset(z0)) as sketch:
        with BuildLine():
            Polyline(*points)
        make_face()
    return extrude(sketch.sketch, amount=height)


def build_fin(design: FinDesign) -> FinSolid:
    outer_pts = design.outline(161)
    outer = _prism(outer_pts + [outer_pts[0]], 0.0, design.span_mm)
    inner_pts = inner_outline(design)
    inner = _prism(inner_pts, 0.0, design.span_mm)
    solid = outer - inner
    c = design.chord_mm
    tw = design.web_mm
    deep = 2.0 * design.half_thickness_at(design.stock_position) + 10.0
    for frac in (design.front_spar, design.rear_spar):
        spar = Pos(frac * c, 0.0, design.span_mm / 2.0) * Box(tw, deep, design.span_mm)
        solid = solid + (spar & inner)
    pitch = design.rib_pitch_mm
    for i in range(design.rib_count):
        z = min(max(i * pitch - tw / 2.0, 0.0), design.span_mm - tw)
        solid = solid + _prism(inner_pts, z, tw)
    xs = design.stock_position * c
    length = design.stock_length_mm()
    stock = Pos(xs, 0.0, -design.bearing_gap_mm + length / 2.0) * Cylinder(design.stock_diameter_mm / 2.0, length)
    return FinSolid(part=solid + stock, design=design)


def formula_volume_mm3(design: FinDesign) -> float:
    return sum(design.volumes_mm3().values())


STOCK_EXTENSION = 0.6  # the stress model's stock runs to 0.6 of the span; the load is spread over 0.4 to 0.6


def build_stock(design: FinDesign) -> Part:
    """The stock alone, from the outer bearing (z = -gap) to 0.6 of the span, axis on z through x = 0, y = 0."""
    length = design.bearing_gap_mm + STOCK_EXTENSION * design.span_mm
    return Pos(0.0, 0.0, -design.bearing_gap_mm + length / 2.0) * Cylinder(design.stock_diameter_mm / 2.0, length)


def write_cutting_dxf(design: FinDesign, path, *, material_name: str, project_name: str = "") -> Path:
    """Rib profile (cut one per rib) and the skin development length, full size."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    doc = ezdxf.new("R2010", units=4)
    doc.layers.add("CUT", color=7)
    doc.layers.add("NOTES", color=8)
    msp = doc.modelspace()
    pts = inner_outline(design)
    msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "CUT"})
    xs = design.stock_position * design.chord_mm
    msp.add_circle((xs, 0.0), design.stock_diameter_mm / 2.0 + 1.0, dxfattribs={"layer": "CUT"})
    for frac in (design.front_spar, design.rear_spar):
        h = design.half_thickness_at(frac) - design.skin_mm
        msp.add_lwpolyline([(frac * design.chord_mm - design.web_mm / 2, -h), (frac * design.chord_mm + design.web_mm / 2, -h),
                            (frac * design.chord_mm + design.web_mm / 2, h), (frac * design.chord_mm - design.web_mm / 2, h)],
                           close=True, dxfattribs={"layer": "NOTES"})
    notes = [
        f"{project_name} stabilizer fin rib" if project_name else "Stabilizer fin rib",
        f"Rib {design.web_mm:g} mm {material_name}, qty {design.rib_count}; slots for the spars shown on layer NOTES",
        f"Stock hole {design.stock_diameter_mm + 2:g} mm at {design.stock_position * 100:.0f}% chord. All dimensions mm, full size.",
        f"Skin {design.skin_mm:g} mm, developed girth {design.section().perimeter_mm:.0f} mm, length {design.span_mm:g} mm.",
    ]
    top = design.half_thickness_at(0.3) + 20.0
    for i, text in enumerate(notes):
        msp.add_text(text, height=max(design.chord_mm / 120.0, 4.0), dxfattribs={"layer": "NOTES"}).set_placement(
            (0.0, top + max(design.chord_mm / 70.0, 7.0) * (len(notes) - i)))
    doc.saveas(target)
    return target


__all__ = ["FinSolid", "build_fin", "build_stock", "formula_volume_mm3", "math", "write_cutting_dxf"]
