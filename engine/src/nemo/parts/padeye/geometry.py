"""Padeye shape: dimensions, validation, outline and mass.

Coordinate system for the main plate outline: x along the base, y up from the
base, origin at the middle of the base. The hole centre is at (0, hole_height).
The plate outline is the convex hull of the base line and the circular head
(radius ``head_radius``), so the sides run straight from the base corners and
meet the head tangentially.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass

from ...data import Material


@dataclass(frozen=True)
class PadeyeDesign:
    main_thickness_mm: float
    head_radius_mm: float
    hole_diameter_mm: float
    base_length_mm: float
    hole_height_mm: float
    weld_leg_mm: float
    cheek_thickness_mm: float = 0.0
    cheek_radius_mm: float = 0.0
    cheek_weld_leg_mm: float = 0.0

    # ------------------------------------------------------------ derived
    @property
    def has_cheeks(self) -> bool:
        return self.cheek_thickness_mm > 0

    @property
    def total_thickness_mm(self) -> float:
        return self.main_thickness_mm + 2.0 * self.cheek_thickness_mm

    @property
    def head_radius_at_hole_mm(self) -> float:
        """Smallest radius of material around the hole through the full thickness."""
        if self.has_cheeks:
            return min(self.head_radius_mm, self.cheek_radius_mm)
        return self.head_radius_mm

    def to_dict(self) -> dict:
        return asdict(self)

    # --------------------------------------------------------- validation
    def problems(self) -> list[str]:
        p: list[str] = []
        positive = {
            "Main plate thickness": self.main_thickness_mm,
            "Head radius": self.head_radius_mm,
            "Hole diameter": self.hole_diameter_mm,
            "Base length": self.base_length_mm,
            "Hole height": self.hole_height_mm,
            "Base weld size": self.weld_leg_mm,
        }
        for label, value in positive.items():
            if not value > 0:
                p.append(f"{label} must be greater than 0 mm.")
        if p:
            return p
        if self.hole_diameter_mm >= 2.0 * self.head_radius_mm:
            p.append("The hole is larger than the padeye head. Make the head radius bigger.")
        if self.hole_height_mm < self.head_radius_mm:
            p.append("The hole is too close to the base: hole height must be at least the head radius.")
        if self.cheek_thickness_mm < 0:
            p.append("Cheek plate thickness cannot be negative.")
        if self.has_cheeks:
            if self.cheek_radius_mm <= self.hole_diameter_mm / 2.0:
                p.append("Cheek plates must be larger than the hole.")
            if self.cheek_radius_mm > self.head_radius_mm:
                p.append("Cheek plates cannot be larger than the padeye head.")
            if self.cheek_weld_leg_mm <= 0:
                p.append("Cheek plates need a weld size greater than 0 mm.")
        return p

    # ------------------------------------------------------------ outline
    def outline_points(self) -> dict:
        """Key points of the main plate outline (mm).

        Returns base corners, tangent points on the head, and the arc angles
        (radians, measured anticlockwise from +x about the hole centre).
        """
        half = self.base_length_mm / 2.0
        h = self.hole_height_mm
        r = self.head_radius_mm
        right = _tangent_angle((half, 0.0), (0.0, h), r, side=+1)
        left = _tangent_angle((-half, 0.0), (0.0, h), r, side=-1)
        return {
            "base_left": (-half, 0.0),
            "base_right": (half, 0.0),
            "tangent_right": (r * math.cos(right), h + r * math.sin(right)),
            "tangent_left": (r * math.cos(left), h + r * math.sin(left)),
            "arc_start_rad": right,
            "arc_end_rad": left,
            "centre": (0.0, h),
        }

    def outline_polyline(self, arc_segments: int = 96) -> list[tuple[float, float]]:
        """Closed outline as a list of points, anticlockwise, for drawing."""
        pts = self.outline_points()
        cx, cy = pts["centre"]
        start, end = pts["arc_start_rad"], pts["arc_end_rad"]
        sweep = (end - start) % (2.0 * math.pi)
        poly = [pts["base_left"], pts["base_right"]]
        for i in range(arc_segments + 1):
            ang = start + sweep * i / arc_segments
            poly.append((cx + self.head_radius_mm * math.cos(ang), cy + self.head_radius_mm * math.sin(ang)))
        return poly

    def main_plate_area_mm2(self) -> float:
        """Exact area of the main plate outline, minus the hole."""
        pts = self.outline_points()
        polygon = [pts["base_left"], pts["base_right"], pts["tangent_right"], pts["centre"], pts["tangent_left"]]
        sweep = (pts["arc_end_rad"] - pts["arc_start_rad"]) % (2.0 * math.pi)
        sector = 0.5 * self.head_radius_mm**2 * sweep
        hole = math.pi * self.hole_diameter_mm**2 / 4.0
        return _shoelace(polygon) + sector - hole

    def cheek_area_mm2(self) -> float:
        """Area of one cheek plate (a ring)."""
        if not self.has_cheeks:
            return 0.0
        return math.pi * (self.cheek_radius_mm**2 - self.hole_diameter_mm**2 / 4.0)

    def volume_mm3(self) -> float:
        main = self.main_plate_area_mm2() * self.main_thickness_mm
        cheeks = 2.0 * self.cheek_area_mm2() * self.cheek_thickness_mm
        return main + cheeks

    def steel_mass_kg(self, material: Material) -> float:
        """Plate mass, excluding weld metal."""
        return self.volume_mm3() * 1.0e-9 * material.density_kg_m3

    def base_weld_length_mm(self) -> float:
        """Total length of the double fillet weld along both faces at the base."""
        return 2.0 * self.base_length_mm

    def cheek_weld_length_mm(self) -> float:
        """Total length of fillet weld around both cheek plates."""
        if not self.has_cheeks:
            return 0.0
        return 2.0 * 2.0 * math.pi * self.cheek_radius_mm


def _tangent_angle(point: tuple[float, float], centre: tuple[float, float], radius: float, side: int) -> float:
    """Angle (about ``centre``) of the tangent point from ``point`` to a circle.

    ``side=+1`` picks the tangent on the anticlockwise side of the line from the
    centre to the point (the right-hand flank of the padeye); ``-1`` the other.
    """
    dx, dy = point[0] - centre[0], point[1] - centre[1]
    distance = math.hypot(dx, dy)
    if distance <= radius:
        raise ValueError("Base corner lies inside the padeye head; increase hole height or base length.")
    alpha = math.atan2(dy, dx)
    beta = math.acos(radius / distance)
    return alpha + side * beta


def _shoelace(points: list[tuple[float, float]]) -> float:
    total = 0.0
    for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1]):
        total += x1 * y2 - x2 * y1
    return 0.5 * total
