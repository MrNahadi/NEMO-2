"""Flat cutting profiles (DXF) for plasma, laser or oxy-fuel cutting tables.

Drawn at full size in millimetres. Cut lines are on layer ``CUT``; labels on
layer ``TEXT`` (most cutting software ignores or can be told to ignore it).
Cheek plates are laid out to the right of the main plate.
"""

from __future__ import annotations

import math
from pathlib import Path

import ezdxf
from ezdxf import units

from .geometry import PadeyeDesign

LABEL_HEIGHT_MM = 6.0
PART_GAP_MM = 30.0


def write_cutting_dxf(
    design: PadeyeDesign,
    path: str | Path,
    *,
    material_name: str,
    quantity: int = 1,
    project_name: str = "",
) -> Path:
    issues = design.problems()
    if issues:
        raise ValueError(" ".join(issues))

    doc = ezdxf.new("R2010", setup=True)
    doc.units = units.MM
    doc.layers.add("CUT", color=7)
    doc.layers.add("TEXT", color=3)
    msp = doc.modelspace()

    pts = design.outline_points()
    cx, cy = pts["centre"]
    r = design.head_radius_mm
    cut = {"layer": "CUT"}

    msp.add_line(pts["base_left"], pts["base_right"], dxfattribs=cut)
    msp.add_line(pts["base_right"], pts["tangent_right"], dxfattribs=cut)
    msp.add_arc(
        (cx, cy),
        r,
        math.degrees(pts["arc_start_rad"]),
        math.degrees(pts["arc_end_rad"]),
        dxfattribs=cut,
    )
    msp.add_line(pts["tangent_left"], pts["base_left"], dxfattribs=cut)
    msp.add_circle((cx, cy), design.hole_diameter_mm / 2.0, dxfattribs=cut)

    label_x = -design.base_length_mm / 2.0
    _label(
        msp,
        [
            f"MAIN PLATE  {design.main_thickness_mm:g} mm  {material_name}",
            f"QTY {quantity}",
            project_name,
        ],
        (label_x, -LABEL_HEIGHT_MM * 2.0),
    )

    if design.has_cheeks:
        rc = design.cheek_radius_mm
        x0 = design.base_length_mm / 2.0 + PART_GAP_MM + rc
        for i in range(2):
            ccx = x0 + i * (2.0 * rc + PART_GAP_MM)
            msp.add_circle((ccx, cy), rc, dxfattribs=cut)
            msp.add_circle((ccx, cy), design.hole_diameter_mm / 2.0, dxfattribs=cut)
        _label(
            msp,
            [f"CHEEK PLATE  {design.cheek_thickness_mm:g} mm  {material_name}", f"QTY {2 * quantity}"],
            (x0 - rc, cy - rc - LABEL_HEIGHT_MM * 2.0),
        )

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(target)
    return target


def _label(msp, lines: list[str], origin: tuple[float, float]) -> None:
    x, y = origin
    for i, text in enumerate(line for line in lines if line):
        msp.add_text(
            text,
            height=LABEL_HEIGHT_MM,
            dxfattribs={"layer": "TEXT", "insert": (x, y - i * LABEL_HEIGHT_MM * 1.6)},
        )
