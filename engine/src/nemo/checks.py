"""Common result record for every design check NEMO reports."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Severity = Literal["required", "advice"]
Basis = Literal["rule", "practice"]
Category = Literal["strength", "fit", "stiffness", "span"]


@dataclass(frozen=True)
class CheckResult:
    """One check: a demand compared with a capacity.

    ``utilization`` is demand / capacity. A value of 1.0 means the design is
    exactly at its limit. ``severity="advice"`` checks never fail a design on
    their own; they appear as warnings. ``category="fit"`` marks size and
    fit-up checks (does the pin go through the hole) as opposed to strength.
    `"stiffness"` limits deflection; `"span"` checks the pipe between supports,
    which the bracket's own size cannot change.
    """

    id: str
    title: str
    demand: float
    capacity: float
    unit: str
    source: str
    explanation: str
    basis: Basis = "rule"
    severity: Severity = "required"
    category: Category = "strength"
    details: dict[str, float] = field(default_factory=dict)
    working: tuple = ()  # tuple[nemo.working.Step, ...]

    @property
    def utilization(self) -> float:
        if self.capacity <= 0:
            return float("inf")
        return self.demand / self.capacity

    @property
    def passed(self) -> bool:
        return bool(self.utilization <= 1.0 + 1e-12)

    @property
    def margin_percent(self) -> float:
        """Spare capacity as a percentage of capacity (negative when failing)."""
        return (1.0 - self.utilization) * 100.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "demand": self.demand,
            "capacity": self.capacity,
            "unit": self.unit,
            "utilization": self.utilization,
            "passed": self.passed,
            "margin_percent": self.margin_percent,
            "source": self.source,
            "explanation": self.explanation,
            "basis": self.basis,
            "severity": self.severity,
            "category": self.category,
            "details": dict(self.details),
            "working": [step.to_dict() for step in self.working],
        }


@dataclass(frozen=True)
class PartCheckReport:
    """Every check on one design of a part, with its mass. Used by the bracket and the fin."""

    design: object
    material: object
    loads: object
    rule_set: object
    checks: tuple[CheckResult, ...]
    mass_kg: float
    values: dict[str, float] = field(default_factory=dict)
    extra: dict = field(default_factory=dict)

    @property
    def required_checks(self) -> tuple[CheckResult, ...]:
        return tuple(c for c in self.checks if c.severity == "required")

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.required_checks)

    @property
    def governing(self) -> CheckResult:
        strength = [c for c in self.required_checks if c.category == "strength"] or list(self.required_checks)
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
            "loads": self.loads.to_dict(),
            "rule_set": self.rule_set.describe(),
            "checks": [c.to_dict() for c in self.checks],
            "values": dict(self.values),
            **self.extra,
        }
