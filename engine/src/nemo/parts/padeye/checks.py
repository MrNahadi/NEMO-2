"""Padeye design checks.

The padeye head (hole region) is checked as a pin-connected plate. Because the
head is a circle centred on the hole, the head checks do not depend on the sling
direction in the plate's plane, so the full sling force is used.

The base section and the base weld are checked for the sling force split into
its components: pulling (perpendicular to the base), in-plane shear and
bending, and sideways (out-of-plane) shear and bending.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from ...checks import CheckResult
from ...data import Material, Shackle
from ...loads import PadeyeLoads
from ...rules import ASMEBTH1
from .geometry import PadeyeDesign

DEFAULT_ELECTRODE_STRENGTH_MPA = 482.0  # E70XX / E7018 class electrodes (70 ksi)
SHACKLE_JAW_CLEARANCE_MM = 2.0
SHACKLE_MIN_FILL_FRACTION = 0.60
PIN_TO_HOLE_MIN_RATIO = 0.90
MIN_HOLE_CLEARANCE_MM = 1.0


@dataclass(frozen=True)
class PadeyeCheckReport:
    design: PadeyeDesign
    material: Material
    shackle: Shackle
    loads: PadeyeLoads
    rule_set: ASMEBTH1
    checks: tuple[CheckResult, ...]
    mass_kg: float
    values: dict[str, float] = field(default_factory=dict)

    @property
    def required_checks(self) -> tuple[CheckResult, ...]:
        return tuple(c for c in self.checks if c.severity == "required")

    @property
    def advice(self) -> tuple[CheckResult, ...]:
        return tuple(c for c in self.checks if c.severity == "advice")

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.required_checks)

    @property
    def governing(self) -> CheckResult:
        """The required strength check closest to (or furthest past) its limit."""
        strength = [c for c in self.required_checks if c.category == "strength"]
        return max(strength, key=lambda c: c.utilization)

    def check(self, check_id: str) -> CheckResult:
        for c in self.checks:
            if c.id == check_id:
                return c
        raise KeyError(check_id)

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "governing": self.governing.id,
            "mass_kg": self.mass_kg,
            "design": self.design.to_dict(),
            "material": self.material.id,
            "shackle": {
                "label": self.shackle.label,
                "wll_t": self.shackle.wll_t,
                "jaw_width_mm": self.shackle.jaw_width_mm,
                "pin_diameter_mm": self.shackle.pin_diameter_mm,
            },
            "loads": self.loads.to_dict(),
            "rule_set": self.rule_set.describe(),
            "checks": [c.to_dict() for c in self.checks],
            "values": dict(self.values),
        }


def check_padeye(
    design: PadeyeDesign,
    *,
    material: Material,
    shackle: Shackle,
    loads: PadeyeLoads,
    rule_set: ASMEBTH1,
    electrode_strength_mpa: float = DEFAULT_ELECTRODE_STRENGTH_MPA,
) -> PadeyeCheckReport:
    issues = design.problems()
    if issues:
        raise ValueError(" ".join(issues))

    rs = rule_set
    src = rs.name
    checks: list[CheckResult] = []
    values: dict[str, float] = {}

    t_main = design.main_thickness_mm
    t_tot = design.total_thickness_mm
    fu = material.tensile_strength_mpa
    fy_main = material.yield_strength_mpa(t_main)
    fy_head = fy_main
    if design.has_cheeks:
        fy_head = min(fy_main, material.yield_strength_mpa(design.cheek_thickness_mm))
    e_mod = material.elastic_modulus_mpa
    dh = design.hole_diameter_mm
    dp = shackle.pin_diameter_mm
    r_head = design.head_radius_at_hole_mm
    be = r_head - dh / 2.0

    values.update(
        yield_main_mpa=fy_main,
        yield_head_mpa=fy_head,
        tensile_mpa=fu,
        total_thickness_mm=t_tot,
        net_width_mm=be,
        design_factor=rs.nd,
    )

    sling = loads.sling_force_n

    # ------------------------------------------------------------ head
    if dp > dh:
        checks.append(
            CheckResult(
                id="hole_fits_pin",
                title="Shackle pin fits through the hole",
                demand=dp + MIN_HOLE_CLEARANCE_MM,
                capacity=dh,
                unit="mm",
                source="NEMO practice",
                basis="practice",
                category="fit",
                explanation="The hole must be at least 1 mm larger than the shackle pin.",
            )
        )
        head = None
    else:
        head = rs.pin_plate_strength(
            yield_mpa=fy_head,
            tensile_mpa=fu,
            thickness_mm=t_tot,
            hole_diameter_mm=dh,
            pin_diameter_mm=dp,
            edge_distance_mm=r_head,
            net_width_mm=be,
            end_radius_mm=r_head,
        )
        values.update(
            strength_reduction_factor_cr=head.cr,
            effective_width_mm=head.effective_width_mm,
            shear_plane_angle_deg=head.shear_plane_angle_deg,
            curvature_loss_mm=head.curvature_loss_mm,
            shear_area_mm2=head.shear_area_mm2,
        )
        pin_src = f"{src}, pin-connected plates"
        checks += [
            CheckResult(
                id="head_tension",
                title="Tearing across the sides of the hole",
                demand=sling,
                capacity=head.tension_n,
                unit="N",
                source=f"{pin_src}: tensile strength through the pinhole",
                explanation=(
                    "The pin pulls on the plate either side of the hole. Too little "
                    "material there and the padeye tears straight across."
                ),
                details={"Cr": head.cr, "beff_mm": head.effective_width_mm},
            ),
            CheckResult(
                id="head_fracture",
                title="Splitting above the hole",
                demand=sling,
                capacity=head.fracture_n,
                unit="N",
                source=f"{pin_src}: fracture strength beyond the pinhole",
                explanation=(
                    "The material between the hole and the top edge can split along "
                    "the line of the sling."
                ),
            ),
            CheckResult(
                id="head_shear_out",
                title="Shearing out above the hole",
                demand=sling,
                capacity=head.double_shear_n,
                unit="N",
                source=f"{pin_src}: double plane shear strength",
                explanation=(
                    "The pin can push a plug of material out of the top of the head "
                    "along two shear lines."
                ),
                details={"phi_deg": head.shear_plane_angle_deg, "Av_mm2": head.shear_area_mm2},
            ),
            CheckResult(
                id="head_bearing",
                title="Crushing under the shackle pin",
                demand=sling,
                capacity=head.bearing_n,
                unit="N",
                source=f"{pin_src}: bearing strength",
                explanation="The pin presses on the hole surface. Too thin a plate and it dents.",
            ),
            CheckResult(
                id="pin_hole_fit",
                title="Pin fits the hole closely",
                demand=PIN_TO_HOLE_MIN_RATIO,
                capacity=dp / dh,
                unit="ratio",
                source=f"{src} commentary on pin-to-hole clearance",
                basis="practice",
                category="fit",
                severity="advice",
                explanation=(
                    "A loose pin concentrates the load and weakens the head. Keep the "
                    "pin at least 90% of the hole diameter."
                ),
            ),
            CheckResult(
                id="hole_clearance",
                title="Hole is big enough for the pin",
                demand=dp + MIN_HOLE_CLEARANCE_MM,
                capacity=dh,
                unit="mm",
                source="NEMO practice",
                basis="practice",
                category="fit",
                explanation="The hole must be at least 1 mm larger than the shackle pin so it fits.",
            ),
        ]

    # --------------------------------------------------------- cheek welds
    if design.has_cheeks:
        cheek_share = sling * (2.0 * design.cheek_thickness_mm / t_tot) / 2.0
        throat = 0.7071 * design.cheek_weld_leg_mm
        weld_len = 2.0 * math.pi * design.cheek_radius_mm
        stress = cheek_share / (weld_len * throat)
        checks.append(
            CheckResult(
                id="cheek_weld",
                title="Cheek plate welds",
                demand=stress,
                capacity=rs.allowable_weld_shear_mpa(electrode_strength_mpa),
                unit="MPa",
                source=f"{src}, welded connections: fillet weld allowable shear",
                explanation=(
                    "Each cheek plate carries its share of the pin load into the main "
                    "plate through the weld around its edge."
                ),
                details={"load_per_cheek_n": cheek_share},
            )
        )
        checks.append(_weld_size_check("cheek_weld_size", "Cheek weld size", design.cheek_weld_leg_mm,
                                       max(design.cheek_thickness_mm, t_main)))

    # ------------------------------------------------------ base section
    length = design.base_length_mm
    h = design.hole_height_mm
    area = length * t_main
    s_major = t_main * length**2 / 6.0
    s_minor = length * t_main**2 / 6.0
    f_axial = loads.vertical_n / area
    f_bend_in = loads.horizontal_n * h / s_major
    f_bend_side = loads.side_n * h / s_minor
    ft = rs.allowable_tension_mpa(fy_main)
    fb_major = rs.allowable_bending_rectangular_major_mpa(
        yield_mpa=fy_main,
        elastic_modulus_mpa=e_mod,
        unbraced_length_mm=h,
        depth_mm=length,
        thickness_mm=t_main,
    )
    fb_minor = rs.allowable_bending_weak_axis_mpa(fy_main)
    interaction = f_axial / ft + f_bend_in / fb_major + f_bend_side / fb_minor
    values.update(
        base_axial_mpa=f_axial,
        base_bending_in_plane_mpa=f_bend_in,
        base_bending_side_mpa=f_bend_side,
        allowable_bending_in_plane_mpa=fb_major,
    )
    checks.append(
        CheckResult(
            id="base_combined",
            title="Pulling and bending at the base",
            demand=interaction,
            capacity=1.0,
            unit="ratio",
            source=f"{src}, members: combined axial tension and bending",
            explanation=(
                "At the base the padeye is pulled upward and bent by the sloping and "
                "sideways parts of the sling force. The three effects are added."
            ),
            details={
                "axial_mpa": f_axial,
                "bending_in_plane_mpa": f_bend_in,
                "bending_side_mpa": f_bend_side,
                "allow_tension_mpa": ft,
                "allow_bending_in_plane_mpa": fb_major,
                "allow_bending_side_mpa": fb_minor,
            },
        )
    )
    f_shear = math.hypot(loads.horizontal_n, loads.side_n) / area
    checks.append(
        CheckResult(
            id="base_shear",
            title="Shear at the base",
            demand=f_shear,
            capacity=rs.allowable_shear_mpa(fy_main),
            unit="MPa",
            source=f"{src}, members: allowable shear stress",
            explanation="The sloping and sideways parts of the sling force try to slide the padeye along its base.",
        )
    )

    # --------------------------------------------------------- base weld
    leg = design.weld_leg_mm
    throat = 0.7071 * leg
    weld_area = 2.0 * length * throat
    weld_s_major = 2.0 * throat * length**2 / 6.0
    separation = t_main + throat  # distance between the two weld throat centrelines
    weld_s_minor = length * throat * separation
    w_normal = (
        loads.vertical_n / weld_area
        + loads.horizontal_n * h / weld_s_major
        + loads.side_n * h / weld_s_minor
    )
    w_shear = math.hypot(loads.horizontal_n, loads.side_n) / weld_area
    w_resultant = math.hypot(w_normal, w_shear)
    checks.append(
        CheckResult(
            id="base_weld",
            title="Base weld strength",
            demand=w_resultant,
            capacity=rs.allowable_weld_shear_mpa(electrode_strength_mpa),
            unit="MPa",
            source=f"{src}, welded connections: fillet weld allowable shear",
            explanation=(
                "Two fillet welds, one on each face, join the padeye to the deck or "
                "structure. All forces on the weld are combined on its throat."
            ),
            details={"normal_mpa": w_normal, "shear_mpa": w_shear, "throat_mm": throat},
        )
    )
    checks.append(_weld_size_check("base_weld_size", "Base weld size", leg, t_main))

    # ------------------------------------------------------------ shackle
    checks += [
        CheckResult(
            id="shackle_rating",
            title="Shackle is rated for the load",
            demand=loads.sling_force_t,
            capacity=shackle.wll_t,
            unit="t",
            source=f"{shackle.series} working load limit",
            basis="practice",
            explanation="The sling force on this padeye must not exceed the shackle's working load limit.",
        ),
        CheckResult(
            id="shackle_fit",
            title="Padeye fits inside the shackle",
            demand=t_tot + SHACKLE_JAW_CLEARANCE_MM,
            capacity=shackle.jaw_width_mm,
            unit="mm",
            source="NEMO practice",
            basis="practice",
            category="fit",
            explanation="The padeye plus cheek plates must slide into the shackle jaw with a little room.",
        ),
        CheckResult(
            id="shackle_fill",
            title="Padeye fills the shackle jaw",
            demand=SHACKLE_MIN_FILL_FRACTION * shackle.jaw_width_mm,
            capacity=t_tot,
            unit="mm",
            source="NEMO practice (rigging guidance)",
            basis="practice",
            category="fit",
            severity="advice",
            explanation=(
                "A padeye much thinner than the shackle jaw lets the shackle tilt and "
                "bends its pin. Aim to fill at least 60% of the jaw, or add spacers."
            ),
        ),
    ]

    return PadeyeCheckReport(
        design=design,
        material=material,
        shackle=shackle,
        loads=loads,
        rule_set=rule_set,
        checks=tuple(checks),
        mass_kg=design.steel_mass_kg(material),
        values=values,
    )


def minimum_fillet_size_mm(thicker_part_mm: float) -> float:
    """Minimum fillet weld leg by thickness of the thicker part joined.

    Follows the AWS D1.1 minimum fillet weld size table (converted to mm).
    """
    if thicker_part_mm <= 6.0:
        return 3.0
    if thicker_part_mm <= 12.0:
        return 5.0
    if thicker_part_mm <= 19.0:
        return 6.0
    return 8.0


def _weld_size_check(check_id: str, title: str, leg_mm: float, thickness_mm: float) -> CheckResult:
    return CheckResult(
        id=check_id,
        title=title,
        demand=minimum_fillet_size_mm(thickness_mm),
        capacity=leg_mm,
        unit="mm",
        source="AWS D1.1 minimum fillet weld size",
        basis="practice",
        category="fit",
        severity="advice",
        explanation=(
            "Very small welds on thick plate cool too fast and can crack. This is "
            "the smallest weld size normally allowed for this plate thickness."
        ),
    )
