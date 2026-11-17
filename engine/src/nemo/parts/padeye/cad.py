"""3D solid model of a padeye (build123d / OpenCASCADE).

Axes: x along the base, z up (hole centre at z = hole_height), y through the
plate thickness with the main plate centred on y = 0. The base face lies on
z = 0. Welds are not modelled as solids.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from build123d import (
    BuildLine,
    BuildSketch,
    Cylinder,
    Line,
    Part,
    Plane,
    Pos,
    Rot,
    ThreePointArc,
    export_step,
    export_stl,
    extrude,
    make_face,
)

from .geometry import PadeyeDesign


@dataclass(frozen=True)
class PadeyeSolid:
    part: Part
    design: PadeyeDesign

    @property
    def volume_mm3(self) -> float:
        return float(self.part.volume)

    @property
    def solid_count(self) -> int:
        return len(self.part.solids())

    def bounding_box_mm(self) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
        box = self.part.bounding_box()
        return (box.min.X, box.min.Y, box.min.Z), (box.max.X, box.max.Y, box.max.Z)

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


def build_padeye(design: PadeyeDesign) -> PadeyeSolid:
    issues = design.problems()
    if issues:
        raise ValueError(" ".join(issues))

    pts = design.outline_points()
    h = design.hole_height_mm
    r = design.head_radius_mm
    t = design.main_thickness_mm

    # Plane.XZ maps sketch (x, y) to world (x, z) and extrudes along y.
    with BuildSketch(Plane.XZ) as outline:
        with BuildLine():
            Line(pts["base_left"], pts["base_right"])
            Line(pts["base_right"], pts["tangent_right"])
            ThreePointArc(pts["tangent_right"], (0.0, h + r), pts["tangent_left"])
            Line(pts["tangent_left"], pts["base_left"])
        make_face()
    main = extrude(outline.sketch, amount=t / 2.0, both=True)

    solid = main
    if design.has_cheeks:
        tc = design.cheek_thickness_mm
        offset = t / 2.0 + tc / 2.0
        for side in (-1.0, 1.0):
            cheek = Pos(0.0, side * offset, h) * Rot(90, 0, 0) * Cylinder(design.cheek_radius_mm, tc)
            solid = solid + cheek

    drill_length = design.total_thickness_mm + 10.0
    hole = Pos(0.0, 0.0, h) * Rot(90, 0, 0) * Cylinder(design.hole_diameter_mm / 2.0, drill_length)
    solid = solid - hole

    return PadeyeSolid(part=solid, design=design)


__all__ = ["PadeyeSolid", "build_padeye"]
