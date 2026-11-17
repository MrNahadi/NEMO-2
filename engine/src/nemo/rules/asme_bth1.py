"""ASME BTH-1 "Design of Below-the-Hook Lifting Devices" rule set.

Implements the allowable-strength (ASD) expressions NEMO uses:

* design factor Nd by design category (A = 2.00, B = 3.00);
* pin-connected plate strengths: tension through the pinhole, fracture on a
  single plane beyond the pinhole, double-plane shear, and pin bearing;
* member allowable stresses: tension, shear, bending (weak axis and strong-axis
  bending of solid rectangular sections with lateral-torsional buckling);
* fillet weld allowable shear on the effective throat.

Pin-connected plate strengths use 1.20 Nd, as BTH-1 requires for that clause.
Section names are quoted in results. Equation numbers are not, because they
change between editions; check against the edition named in the project.

Units: N, mm, MPa.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class PinPlateStrength:
    """Allowable loads (N) for a pin-connected plate and the values behind them."""

    tension_n: float
    fracture_n: float
    double_shear_n: float
    bearing_n: float
    cr: float
    effective_width_mm: float
    shear_plane_angle_deg: float
    curvature_loss_mm: float
    shear_area_mm2: float


@dataclass(frozen=True)
class ASMEBTH1:
    """ASME BTH-1 allowable strengths.

    ``design_category``: "A" for predictable loads and non-severe conditions,
    "B" for uncertain loads or severe conditions (the usual choice at sea).
    ``service_class``: 0 for up to 20,000 load cycles; 1 to 4 for more.
    """

    design_category: str = "B"
    service_class: int = 0

    id = "asme-bth-1"
    name = "ASME BTH-1"
    full_name = "ASME BTH-1, Design of Below-the-Hook Lifting Devices"

    def __post_init__(self) -> None:
        if self.design_category not in ("A", "B"):
            raise ValueError("Design category must be 'A' or 'B'.")
        if self.service_class not in (0, 1, 2, 3, 4):
            raise ValueError("Service class must be 0, 1, 2, 3 or 4.")

    # ----------------------------------------------------------- factors
    @property
    def nd(self) -> float:
        """Design factor Nd."""
        return 2.00 if self.design_category == "A" else 3.00

    @property
    def nd_pin_connection(self) -> float:
        """Design factor for pin-connected plate strengths (1.20 Nd)."""
        return 1.20 * self.nd

    def describe(self) -> dict:
        return {
            "id": self.id,
            "name": self.full_name,
            "design_category": self.design_category,
            "service_class": self.service_class,
            "design_factor": self.nd,
            "pin_connection_design_factor": self.nd_pin_connection,
        }

    # ----------------------------------------------------- pin-connected plate
    def pin_plate_strength(
        self,
        *,
        yield_mpa: float,
        tensile_mpa: float,
        thickness_mm: float,
        hole_diameter_mm: float,
        pin_diameter_mm: float,
        edge_distance_mm: float,
        net_width_mm: float,
        end_radius_mm: float,
        pin_yield_mpa: float | None = None,
    ) -> PinPlateStrength:
        """Allowable loads for a pin-connected plate.

        ``edge_distance_mm`` (R): hole centre to plate edge along the load.
        ``net_width_mm`` (be): hole edge to plate edge across the load, each side.
        ``end_radius_mm`` (r): radius of the plate edge beyond the hole.
        ``pin_yield_mpa``: pin yield strength for bearing; the lower of plate and
        pin governs. Defaults to the plate yield.
        """
        t, dh, dp = thickness_mm, hole_diameter_mm, pin_diameter_mm
        big_r, be, r = edge_distance_mm, net_width_mm, end_radius_mm
        fy, fu = yield_mpa, tensile_mpa
        if not (0 < dp <= dh):
            raise ValueError("Pin diameter must be positive and no larger than the hole.")
        if be <= 0 or big_r <= dh / 2 or t <= 0:
            raise ValueError("Plate must extend beyond the hole on every side.")

        cr = 1.0 - 0.275 * math.sqrt(1.0 - (dp / dh) ** 2)

        beff = min(
            be,
            4.0 * t,
            be * 0.6 * (fu / fy) * math.sqrt(dh / be),
        )
        tension = cr * fu * 2.0 * t * beff / self.nd_pin_connection

        fracture = (
            cr
            * fu
            * (1.13 * (big_r - dh / 2.0) + 0.92 * be / (1.0 + be / dh))
            * t
            / self.nd_pin_connection
        )

        phi_deg = 55.0 * dp / dh
        phi = math.radians(phi_deg)
        a = big_r - dh / 2.0
        half_chord = dp / 2.0 * math.sin(phi)
        z = r - math.sqrt(max(r * r - half_chord * half_chord, 0.0)) if math.isfinite(r) else 0.0
        av = 2.0 * (a + dp / 2.0 * (1.0 - math.cos(phi)) - z) * t
        double_shear = 0.70 * fu * av / self.nd_pin_connection

        bearing_fy = min(fy, pin_yield_mpa) if pin_yield_mpa else fy
        bearing_coeff = 1.25 if self.service_class == 0 else 0.63
        bearing = bearing_coeff * bearing_fy * dp * t / self.nd

        return PinPlateStrength(
            tension_n=tension,
            fracture_n=fracture,
            double_shear_n=double_shear,
            bearing_n=bearing,
            cr=cr,
            effective_width_mm=beff,
            shear_plane_angle_deg=phi_deg,
            curvature_loss_mm=z,
            shear_area_mm2=av,
        )

    # --------------------------------------------------------- member stresses
    def allowable_tension_mpa(self, yield_mpa: float) -> float:
        return yield_mpa / self.nd

    def allowable_shear_mpa(self, yield_mpa: float) -> float:
        return yield_mpa / (math.sqrt(3.0) * self.nd)

    def allowable_bending_weak_axis_mpa(self, yield_mpa: float) -> float:
        """Solid rectangular section bent about its minor (weak) axis."""
        return 1.25 * yield_mpa / self.nd

    def allowable_bending_rectangular_major_mpa(
        self,
        *,
        yield_mpa: float,
        elastic_modulus_mpa: float,
        unbraced_length_mm: float,
        depth_mm: float,
        thickness_mm: float,
        cb: float = 1.0,
    ) -> float:
        """Solid rectangular section bent about its major (strong) axis.

        Allows for lateral-torsional buckling through the slenderness
        Lb * d / t^2. Returned as an allowable stress on the elastic section
        modulus.
        """
        fy, e = yield_mpa, elastic_modulus_mpa
        slenderness = unbraced_length_mm * depth_mm / thickness_mm**2
        if slenderness <= 0.08 * e / fy:
            factor = 1.25
        elif slenderness <= 1.9 * e / fy:
            factor = min(cb * (1.52 - 0.274 * slenderness * fy / e), 1.25)
        else:
            factor = min(1.9 * e * cb / (slenderness * fy), 1.25)
        return factor * fy / self.nd

    def allowable_weld_shear_mpa(self, electrode_strength_mpa: float) -> float:
        """Fillet weld shear on the effective throat."""
        return 0.60 * electrode_strength_mpa / (1.20 * self.nd)
