"""Pipe support bracket shape: a seat plate with two triangular knees, welded to a bulkhead.

Axes: x out from the bulkhead face (x = 0), y along the pipe, z up with the top
of the seat at z = 0. The seat plate is L long (out from the bulkhead), b wide
(along the pipe) and t_s thick. Two knees of thickness t_k sit flush with the
seat's side edges, so the U-bolt holes on the centre line are clear of them.
Each knee is a right triangle: h_k deep at the bulkhead, running to the seat
tip. The pipe centre is e from the bulkhead; the U-bolt legs pass through two
holes at x = e +/- s/2, with s = D + d (pipe diameter plus U-bolt diameter).
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass

from ...data import Material

HOLE_CLEARANCE_MM = 2.0


@dataclass(frozen=True)
class Section:
    x_mm: float
    knee_depth_mm: float
    area_mm2: float
    centroid_z_mm: float
    inertia_y_mm4: float
    s_top_mm3: float
    s_bottom_mm3: float
    inertia_z_mm4: float
    s_side_mm3: float
    flange_first_moment_mm3: float
    shear_area_mm2: float

    @property
    def s_min_mm3(self) -> float:
        return min(self.s_top_mm3, self.s_bottom_mm3)


@dataclass(frozen=True)
class BracketDesign:
    seat_length_mm: float
    seat_width_mm: float
    seat_thickness_mm: float
    knee_depth_mm: float
    knee_thickness_mm: float
    pipe_offset_mm: float
    pipe_od_mm: float
    ubolt_diameter_mm: float
    root_weld_mm: float
    knee_weld_mm: float

    def to_dict(self) -> dict:
        return asdict(self)

    # ------------------------------------------------------------ derived
    @property
    def hole_diameter_mm(self) -> float:
        return self.ubolt_diameter_mm + HOLE_CLEARANCE_MM

    @property
    def leg_spacing_mm(self) -> float:
        return self.pipe_od_mm + self.ubolt_diameter_mm

    @property
    def hole_positions_mm(self) -> tuple[float, float]:
        half = self.leg_spacing_mm / 2.0
        return self.pipe_offset_mm - half, self.pipe_offset_mm + half

    @property
    def clear_width_mm(self) -> float:
        """Width of seat between the knees."""
        return self.seat_width_mm - 2.0 * self.knee_thickness_mm

    @property
    def knee_span_mm(self) -> float:
        """Seat span between the knee centre lines."""
        return self.seat_width_mm - self.knee_thickness_mm

    @property
    def knee_free_edge_mm(self) -> float:
        return math.hypot(self.seat_length_mm, self.knee_depth_mm)

    def knee_depth_at(self, x: float) -> float:
        return max(self.knee_depth_mm * (1.0 - x / self.seat_length_mm), 0.0)

    # --------------------------------------------------------- validation
    def problems(self) -> list[str]:
        p: list[str] = []
        for label, value in (("Seat length", self.seat_length_mm), ("Seat width", self.seat_width_mm),
                             ("Seat thickness", self.seat_thickness_mm), ("Knee depth", self.knee_depth_mm),
                             ("Knee thickness", self.knee_thickness_mm), ("Pipe diameter", self.pipe_od_mm),
                             ("U-bolt diameter", self.ubolt_diameter_mm), ("Bulkhead weld", self.root_weld_mm),
                             ("Knee weld", self.knee_weld_mm)):
            if not value > 0:
                p.append(f"{label} must be greater than 0 mm.")
        if p:
            return p
        near, far = self.hole_positions_mm
        if near - self.hole_diameter_mm / 2.0 < self.root_weld_mm + 10.0:
            p.append("The U-bolt hole nearest the bulkhead clashes with the bulkhead weld. Move the pipe out.")
        if self.seat_length_mm - far < 1.5 * self.hole_diameter_mm:
            p.append("The outer U-bolt hole is too close to the end of the seat.")
        if self.clear_width_mm < 2.0 * self.ubolt_diameter_mm + 10.0:
            p.append("The seat is too narrow between the knees for the U-bolt nut and washer.")
        if self.pipe_offset_mm >= self.seat_length_mm:
            p.append("The pipe must sit on the seat.")
        return p

    # ----------------------------------------------------------- section
    def section_at(self, x: float) -> Section:
        """Cross-section of the arm at distance x from the bulkhead (seat flange plus two knee webs)."""
        b, ts, tk = self.seat_width_mm, self.seat_thickness_mm, self.knee_thickness_mm
        h = self.knee_depth_at(x)
        a_f, z_f = b * ts, -ts / 2.0
        a_w, z_w = 2.0 * tk * h, -ts - h / 2.0
        area = a_f + a_w
        zc = (a_f * z_f + a_w * z_w) / area
        iy = b * ts**3 / 12.0 + a_f * (z_f - zc) ** 2 + 2.0 * tk * h**3 / 12.0 + a_w * (z_w - zc) ** 2
        top, bottom = -zc, zc - (-ts - h)
        iz = ts * b**3 / 12.0 + 2.0 * (h * tk**3 / 12.0 + tk * h * (b / 2.0 - tk / 2.0) ** 2)
        return Section(
            x_mm=x, knee_depth_mm=h, area_mm2=area, centroid_z_mm=zc, inertia_y_mm4=iy,
            s_top_mm3=iy / top, s_bottom_mm3=iy / bottom, inertia_z_mm4=iz, s_side_mm3=iz / (b / 2.0),
            flange_first_moment_mm3=a_f * (z_f - zc), shear_area_mm2=a_w + a_f,
        )

    # -------------------------------------------------------------- mass
    def seat_volume_mm3(self) -> float:
        holes = 2.0 * math.pi * self.hole_diameter_mm**2 / 4.0 * self.seat_thickness_mm
        return self.seat_length_mm * self.seat_width_mm * self.seat_thickness_mm - holes

    def knee_volume_mm3(self) -> float:
        """One knee."""
        return 0.5 * self.seat_length_mm * self.knee_depth_mm * self.knee_thickness_mm

    def volume_mm3(self) -> float:
        return self.seat_volume_mm3() + 2.0 * self.knee_volume_mm3()

    def steel_mass_kg(self, material: Material) -> float:
        return self.volume_mm3() * 1e-9 * material.density_kg_m3

    def weld_length_mm(self) -> float:
        """All fillet weld: both sides of the seat and knees at the bulkhead, and the knees to the seat."""
        return 2.0 * self.seat_width_mm + 4.0 * self.knee_depth_mm + 4.0 * self.seat_length_mm
