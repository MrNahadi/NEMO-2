"""AISC 360-16 "Specification for Structural Steel Buildings", allowable strength design (ASD).

Used for ship structural details that are not lifting devices, such as pipe
support brackets. Each allowable is the nominal strength divided by the
safety factor Omega given in the clause named:

* tension yield on the gross section: F_y / 1.67 (Chapter D);
* flexure of a compact or plate section: M_n / 1.67 (Chapter F). For plates
  bent about their weak axis M_n = F_y Z <= 1.6 F_y S (F11);
* shear yield of plate webs: 0.6 F_y / 1.67 (Chapter G, C_v = 1);
* fillet welds: 0.60 F_EXX / 2.00 on the effective throat (J2.4);
* bolts in tension: 0.75 F_u / 2.00 on the nominal bolt area (J3.6). NEMO
  applies it to the threaded tensile stress area, which is conservative.

Units: N, mm, MPa.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AISC360:
    id = "aisc-360-asd"
    name = "AISC 360-16 (ASD)"
    full_name = "AISC 360-16, Specification for Structural Steel Buildings, allowable strength design"

    omega_tension: float = 1.67
    omega_flexure: float = 1.67
    omega_shear: float = 1.67
    omega_weld: float = 2.00
    omega_bolt: float = 2.00

    def describe(self) -> dict:
        return {
            "id": self.id,
            "name": self.full_name,
            "design_factor": self.omega_flexure,
            "omega_tension": self.omega_tension,
            "omega_flexure": self.omega_flexure,
            "omega_shear": self.omega_shear,
            "omega_weld": self.omega_weld,
            "omega_bolt": self.omega_bolt,
        }

    def allowable_tension_mpa(self, yield_mpa: float) -> float:
        return yield_mpa / self.omega_tension

    def allowable_bending_mpa(self, yield_mpa: float, shape_factor: float = 1.0) -> float:
        """Allowable bending stress on the elastic section modulus.

        ``shape_factor`` is Z / S, capped at 1.6 as AISC F11 does for plates. 1.0
        (first yield) is used for built-up sections whose plates are not all
        compact.
        """
        return min(shape_factor, 1.6) * yield_mpa / self.omega_flexure

    def allowable_shear_mpa(self, yield_mpa: float) -> float:
        return 0.6 * yield_mpa / self.omega_shear

    def allowable_weld_shear_mpa(self, electrode_strength_mpa: float) -> float:
        return 0.60 * electrode_strength_mpa / self.omega_weld

    def allowable_bolt_tension_mpa(self, tensile_mpa: float) -> float:
        return 0.75 * tensile_mpa / self.omega_bolt
