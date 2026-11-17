"""Stabilizer fin structure: NACA 00xx skin, two spars, ribs and a solid stock.

Axes: x along the chord from the leading edge, y across the foil (the lift
direction), z along the span from the root (hull) to the tip. The stock axis
is at x = x_s c. The fin body is a box girder: the skin between the front and
rear spars plus the two spar webs. The nose and tail skin keep the shape but
are not counted in the root section, which is on the safe side.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass

import numpy as np

from ...hydro import naca_thickness

AREA_FACTOR = 0.68088  # area of a NACA 00xx section (closed trailing edge) = AREA_FACTOR t c^2


@dataclass(frozen=True)
class FinSection:
    inertia_mm4: float
    y_max_mm: float
    box_area_mm2: float
    web_heights_mm: tuple[float, float]
    perimeter_mm: float

    @property
    def section_modulus_mm3(self) -> float:
        return self.inertia_mm4 / self.y_max_mm


@dataclass(frozen=True)
class FinDesign:
    span_mm: float
    chord_mm: float
    thickness_ratio: float
    stock_position: float
    front_spar: float
    rear_spar: float
    skin_mm: float
    web_mm: float
    rib_spacing_mm: float
    stock_diameter_mm: float
    bearing_gap_mm: float

    def to_dict(self) -> dict:
        return asdict(self)

    def problems(self) -> list[str]:
        p = []
        for label, value in (("Skin", self.skin_mm), ("Spar web", self.web_mm), ("Rib spacing", self.rib_spacing_mm),
                             ("Stock diameter", self.stock_diameter_mm)):
            if not value > 0:
                p.append(f"{label} must be greater than 0 mm.")
        if not p and self.stock_diameter_mm > 0.9 * 2.0 * self.half_thickness_at(self.stock_position):
            p.append("The stock is too thick to fit inside the foil at its position.")
        return p

    def half_thickness_at(self, x_fraction: float) -> float:
        return float(naca_thickness(np.array([x_fraction]), self.thickness_ratio)[0]) * self.chord_mm

    @property
    def rib_count(self) -> int:
        return int(math.ceil(self.span_mm / self.rib_spacing_mm - 1e-9)) + 1

    @property
    def rib_pitch_mm(self) -> float:
        return self.span_mm / (self.rib_count - 1)

    @property
    def spar_spacing_mm(self) -> float:
        return (self.rear_spar - self.front_spar) * self.chord_mm

    def outline(self, points: int = 121) -> list[tuple[float, float]]:
        beta = np.linspace(0.0, math.pi, points)
        x = 0.5 * (1.0 - np.cos(beta))
        y = naca_thickness(x, self.thickness_ratio)
        upper = [(float(a) * self.chord_mm, float(b) * self.chord_mm) for a, b in zip(x, y)]
        lower = [(float(a) * self.chord_mm, -float(b) * self.chord_mm) for a, b in zip(x[::-1][1:-1], y[::-1][1:-1])]
        return upper + lower

    def section(self) -> FinSection:
        c, t = self.chord_mm, self.skin_mm
        x = np.linspace(self.front_spar, self.rear_spar, 241)
        y = naca_thickness(x, self.thickness_ratio) * c
        xs = x * c
        ds = np.hypot(np.diff(xs), np.diff(y))
        ym = 0.5 * (y[:-1] + y[1:])
        skin_i = 2.0 * float(np.sum(t * ds * ym**2))  # upper and lower skin
        h_f, h_r = 2.0 * y[0], 2.0 * y[-1]
        web_i = self.web_mm * (h_f**3 + h_r**3) / 12.0
        box = float(np.trapezoid(2.0 * y, xs))
        full = np.linspace(0.0, 1.0, 801)
        yf = naca_thickness(full, self.thickness_ratio) * c
        perimeter = 2.0 * float(np.sum(np.hypot(np.diff(full * c), np.diff(yf))))
        return FinSection(inertia_mm4=skin_i + web_i, y_max_mm=float(y.max()) + t / 2.0, box_area_mm2=box,
                          web_heights_mm=(float(h_f), float(h_r)), perimeter_mm=perimeter)

    # -------------------------------------------------------------- mass
    def foil_area_mm2(self) -> float:
        return AREA_FACTOR * self.thickness_ratio * self.chord_mm**2

    def stock_length_mm(self) -> float:
        """Stock from the outer bearing into the fin, to mid-span."""
        return self.bearing_gap_mm + 0.5 * self.span_mm

    def volumes_mm3(self) -> dict[str, float]:
        sec = self.section()
        return {
            "skin": sec.perimeter_mm * self.span_mm * self.skin_mm,
            "spars": sum(sec.web_heights_mm) * self.span_mm * self.web_mm,
            "ribs": self.rib_count * self.foil_area_mm2() * self.web_mm,
            "stock": math.pi / 4.0 * self.stock_diameter_mm**2 * self.stock_length_mm(),
        }

    def masses_kg(self, plate, stock) -> dict[str, float]:
        v = self.volumes_mm3()
        out = {k: v[k] * 1e-9 * (stock.density_kg_m3 if k == "stock" else plate.density_kg_m3) for k in v}
        out["total"] = sum(out.values())
        return out
