"""IACS UR S10 "Rudders, sole pieces and rudder horns" (Rev.8, 2025), used for stabilizer fins.

A roll-stabilizer fin is an all-movable foil on a stock, like a spade rudder,
so NEMO checks it with the rudder requirements:

* rudder force C_R = K1 K2 K3 132 A V^2 (S10.2.1.1), as an empirical
  cross-check of NEMO's own foil load model;
* stock torsion tau_t <= 68 / k and combined stress
  sigma_e = sqrt(sigma_b^2 + 3 tau_t^2) <= 118 / k (S10.4);
* blade (fin body) bending <= 110 / k, shear <= 50 / k, equivalent <= 120 / k
  (S10.5.1);
* minimum side plating thickness (S10.5.2) and web thickness (S10.5.2).

The material factor k = (235 / R_eH)^e, e = 0.75 for R_eH > 235 MPa, with R_eH
not taken greater than 0.7 sigma_T or 450 MPa (S10.1.3.5).

Units: N, mm, MPa unless stated.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class IACSS10:
    id = "iacs-ur-s10"
    name = "IACS UR S10"
    full_name = "IACS UR S10, Rudders, sole pieces and rudder horns (Rev.8, 2025), applied to a stabilizer fin"

    stock_torsion_mpa: float = 68.0
    k2_naca_astern: float = 0.80  # Table 1, NACA-00 series, astern condition
    astern_lever_fraction: float = 0.66  # S10.2.1.2, alpha astern
    astern_min_speed_fraction: float = 0.5  # S10.2.1.1, V_astern not less than 0.5 V
    stock_equivalent_mpa: float = 118.0
    blade_bending_mpa: float = 110.0
    blade_shear_mpa: float = 50.0
    blade_equivalent_mpa: float = 120.0

    def describe(self) -> dict:
        return {"id": self.id, "name": self.full_name, "design_factor": 235.0 / self.blade_bending_mpa}

    @staticmethod
    def effective_yield_mpa(yield_mpa: float, tensile_mpa: float) -> float:
        return min(yield_mpa, 0.7 * tensile_mpa, 450.0)

    @classmethod
    def material_factor(cls, yield_mpa: float, tensile_mpa: float) -> float:
        reh = cls.effective_yield_mpa(yield_mpa, tensile_mpa)
        exponent = 0.75 if reh > 235.0 else 1.0
        return (235.0 / reh) ** exponent

    @staticmethod
    def rudder_force_n(area_m2: float, speed_kn: float, aspect_ratio: float, *, k2: float = 1.10, k3: float = 0.8,
                       astern: bool = False) -> float:
        """S10.2.1.1. K2 = 1.10 for NACA-00 profiles ahead (0.80 astern); K3 = 0.8 outside the propeller jet.

        Ahead, a speed under 10 knots is replaced by (V + 20) / 3. Astern, the astern speed is used as given
        (the caller applies the minimum of half the ahead speed).
        """
        speed = speed_kn if (astern or speed_kn >= 10.0) else (speed_kn + 20.0) / 3.0
        k1 = (min(aspect_ratio, 2.0) + 2.0) / 3.0
        return k1 * k2 * k3 * 132.0 * area_m2 * speed**2

    @staticmethod
    def min_plating_mm(*, panel_short_m: float, panel_long_m: float, draught_m: float, force_n: float,
                       area_m2: float, k: float) -> float:
        """S10.5.2: t = 5.5 s beta sqrt((T + C_R 1e-4 / A) k) + 2.5."""
        ratio = panel_short_m / panel_long_m
        beta = 1.0 if panel_long_m / panel_short_m >= 2.5 else min(math.sqrt(1.1 - 0.5 * ratio**2), 1.0)
        return 5.5 * panel_short_m * beta * math.sqrt((draught_m + force_n * 1e-4 / area_m2) * k) + 2.5


# S10.8.2 Table 3: allowable bearing surface pressure q_a (N/mm^2), and S10.8.1 least liner or bush thickness (mm).
BEARING_MATERIALS = {
    "lignum": {"name": "Lignum vitae", "pressure_mpa": 2.5, "liner_mm": 22.0, "metallic": False},
    "white_metal": {"name": "White metal, oil lubricated", "pressure_mpa": 4.5, "liner_mm": 8.0, "metallic": True},
    "synthetic": {"name": "Synthetic material, harder than 60 Shore D", "pressure_mpa": 5.5, "liner_mm": 8.0, "metallic": False},
    "bronze": {"name": "Steel or bronze, or hot-pressed bronze-graphite", "pressure_mpa": 7.0, "liner_mm": 8.0, "metallic": True},
}
BEARING_MAX_LENGTH_RATIO = 1.2  # S10.8.3: bearing length / diameter not greater than 1.2


def bearing_clearance_mm(diameter_mm: float, metallic: bool) -> float:
    """S10.8.4: metal bearings at least d/1000 + 1.0 mm on the diameter; non-metallic not less than 1.5 mm."""
    return diameter_mm / 1000.0 + 1.0 if metallic else 1.5
