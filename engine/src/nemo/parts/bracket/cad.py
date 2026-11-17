"""3D solid and cutting profiles of a pipe support bracket.

Axes as in ``geometry.py``: x out from the bulkhead, y along the pipe, z up,
seat top at z = 0. Welds are not modelled as solids.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import ezdxf
from build123d import Box, BuildSketch, Cylinder, Part, Plane, Polygon, Pos, export_step, export_stl, extrude

from .geometry import BracketDesign


@dataclass(frozen=True)
class BracketSolid:
    part: Part
    design: BracketDesign

    @property
    def volume_mm3(self) -> float:
        return float(self.part.volume)

    @property
    def solid_count(self) -> int:
        return len(self.part.solids())

    def export_step(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not export_step(self.part, str(target)):
            raise RuntimeError(f"STEP export failed: {target}")
        return target

    def export_stl(self, path: str | Path, tolerance_mm: float = 0.05) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not export_stl(self.part, str(target), tolerance=tolerance_mm):
            raise RuntimeError(f"STL export failed: {target}")
        return target


def build_bracket(design: BracketDesign) -> BracketSolid:
    issues = design.problems()
    if issues:
        raise ValueError(" ".join(issues))
    length, width, ts = design.seat_length_mm, design.seat_width_mm, design.seat_thickness_mm
    tk, depth = design.knee_thickness_mm, design.knee_depth_mm
    solid = Pos(length / 2.0, 0.0, -ts / 2.0) * Box(length, width, ts)
    for x in design.hole_positions_mm:
        solid = solid - Pos(x, 0.0, -ts / 2.0) * Cylinder(design.hole_diameter_mm / 2.0, ts * 3.0)
    # Plane.XZ maps sketch (x, y) to world (x, z); the knee is extruded both ways through its thickness.
    with BuildSketch(Plane.XZ) as sketch:
        Polygon((0.0, -ts), (length, -ts), (0.0, -ts - depth), align=None)
    knee = extrude(sketch.sketch, amount=tk / 2.0, both=True)
    offset = width / 2.0 - tk / 2.0
    for side in (-1.0, 1.0):
        solid = solid + Pos(0.0, side * offset, 0.0) * knee
    return BracketSolid(part=solid, design=design)


def write_cutting_dxf(design: BracketDesign, path: str | Path, *, material_name: str, project_name: str = "") -> Path:
    """Full-size cutting profiles: the seat plate with its U-bolt holes and one knee (cut two)."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    doc = ezdxf.new("R2010", units=4)
    doc.layers.add("CUT", color=7)
    doc.layers.add("NOTES", color=8)
    msp = doc.modelspace()
    length, width = design.seat_length_mm, design.seat_width_mm
    msp.add_lwpolyline([(0, 0), (length, 0), (length, width), (0, width)], close=True, dxfattribs={"layer": "CUT"})
    for x in design.hole_positions_mm:
        msp.add_circle((x, width / 2.0), design.hole_diameter_mm / 2.0, dxfattribs={"layer": "CUT"})
    gap = 40.0
    x0 = length + gap
    msp.add_lwpolyline([(x0, 0), (x0 + length, 0), (x0, design.knee_depth_mm)], close=True, dxfattribs={"layer": "CUT"})
    notes = [
        f"{project_name} pipe support bracket" if project_name else "Pipe support bracket",
        f"Seat plate {design.seat_thickness_mm:g} mm {material_name}, qty 1, edge against the bulkhead at x = 0",
        f"Knee {design.knee_thickness_mm:g} mm {material_name}, qty 2, short leg against the bulkhead",
        f"Holes {design.hole_diameter_mm:g} mm for the U-bolt. All dimensions mm, full size.",
    ]
    top = max(width, design.knee_depth_mm) + 15.0
    for i, text in enumerate(notes):
        msp.add_text(text, height=4.0, dxfattribs={"layer": "NOTES"}).set_placement((0, top + 7.0 * (len(notes) - i)))
    doc.saveas(target)
    return target
