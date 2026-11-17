"""Turn a lifting job description into the forces on one padeye."""

from __future__ import annotations

import math
from dataclasses import dataclass

STANDARD_GRAVITY = 9.80665  # m/s^2


@dataclass(frozen=True)
class LiftScenario:
    """What the user tells NEMO about the lift.

    ``sling_angle_deg``: angle of each sling leg measured from the horizontal
    (90 = straight up).
    ``points_carrying``: how many lifting points are assumed to share the load.
    With four points and no spreader beam, rigging practice often assumes only
    two carry it. Defaults to all points.
    ``dynamic_factor``: extra factor for dynamic effects, if the lift procedure
    or standard asks for one. 1.0 adds nothing.
    ``side_load_fraction``: sideways (out-of-plane) force on the padeye as a
    fraction of the sling force, to allow for the sling not lining up perfectly.
    ``out_of_plane_angle_deg``: the second angle of an oblique sling. Seen from
    above, it is the angle between the sling and the plane of the padeye plate
    (0 = the padeye is lined up with its sling, the usual case). The sling
    then pulls sideways on the plate and on the shackle, and the sideways force
    is the larger of this real component and the allowance above.
    """

    lifted_mass_kg: float
    lift_points: int = 2
    sling_angle_deg: float = 60.0
    dynamic_factor: float = 1.0
    points_carrying: int | None = None
    side_load_fraction: float = 0.05
    out_of_plane_angle_deg: float = 0.0

    def problems(self) -> list[str]:
        issues: list[str] = []
        if self.lifted_mass_kg <= 0:
            issues.append("The load must weigh more than 0 kg.")
        if self.lift_points < 1:
            issues.append("There must be at least 1 lifting point.")
        carrying = self.carrying_points
        if carrying < 1 or carrying > self.lift_points:
            issues.append(
                "The number of points carrying the load must be between 1 and the number of lifting points."
            )
        if not (15.0 <= self.sling_angle_deg <= 90.0):
            issues.append("Sling angle must be between 15 and 90 degrees from horizontal.")
        if self.dynamic_factor < 1.0:
            issues.append("The dynamic factor cannot be less than 1.0.")
        if not (0.0 <= self.side_load_fraction <= 0.5):
            issues.append("The sideways load must be between 0% and 50% of the sling force.")
        if not (0.0 <= self.out_of_plane_angle_deg <= 90.0):
            issues.append("The angle between the sling and the padeye plate must be between 0 and 90 degrees.")
        return issues

    @property
    def carrying_points(self) -> int:
        return self.points_carrying if self.points_carrying is not None else self.lift_points


@dataclass(frozen=True)
class PadeyeLoads:
    """Forces on one padeye, in newtons.

    ``sling_force_n`` acts along the sling, in the plane of the padeye.
    ``vertical_n`` and ``horizontal_n`` are its components perpendicular and
    parallel to the base. ``side_n`` acts perpendicular to the padeye plate.
    """

    sling_force_n: float
    vertical_n: float
    horizontal_n: float
    side_n: float
    sling_angle_deg: float
    static_sling_force_n: float
    out_of_plane_angle_deg: float = 0.0
    side_angle_deg: float = 0.0  # angle between the sling and the plane of the plate: the shackle's side-load angle
    side_from_angle_n: float = 0.0  # sideways component from the oblique sling alone, before the allowance

    @property
    def sling_force_t(self) -> float:
        """Sling force expressed in tonnes-force, for comparing with shackle WLL."""
        return self.sling_force_n / STANDARD_GRAVITY / 1000.0

    def to_dict(self) -> dict:
        return {
            "sling_force_n": self.sling_force_n,
            "sling_force_t": self.sling_force_t,
            "vertical_n": self.vertical_n,
            "horizontal_n": self.horizontal_n,
            "side_n": self.side_n,
            "sling_angle_deg": self.sling_angle_deg,
            "static_sling_force_n": self.static_sling_force_n,
            "out_of_plane_angle_deg": self.out_of_plane_angle_deg,
            "side_angle_deg": self.side_angle_deg,
            "side_from_angle_n": self.side_from_angle_n,
        }


def padeye_loads(scenario: LiftScenario) -> PadeyeLoads:
    issues = scenario.problems()
    if issues:
        raise ValueError(" ".join(issues))
    weight_n = scenario.lifted_mass_kg * STANDARD_GRAVITY
    static_vertical = weight_n / scenario.carrying_points
    vertical = static_vertical * scenario.dynamic_factor
    angle = math.radians(scenario.sling_angle_deg)
    plan = math.radians(scenario.out_of_plane_angle_deg)
    sling = vertical / math.sin(angle)
    across = math.cos(angle) * math.sin(plan)  # sideways share of the sling force, from the two angles
    side_geometric = sling * across
    return PadeyeLoads(
        sling_force_n=sling,
        vertical_n=vertical,
        horizontal_n=sling * math.cos(angle) * math.cos(plan),
        side_n=max(side_geometric, sling * scenario.side_load_fraction),
        sling_angle_deg=scenario.sling_angle_deg,
        static_sling_force_n=static_vertical / math.sin(angle),
        out_of_plane_angle_deg=scenario.out_of_plane_angle_deg,
        side_angle_deg=math.degrees(math.asin(min(across, 1.0))),
        side_from_angle_n=side_geometric,
    )
