"""Hand-calculation style working for every number NEMO reports.

Each ``Step`` holds the formula in symbols, the same formula with the numbers
put in, and the result, so anyone can repeat the calculation with a
calculator.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Step:
    label: str
    symbol: str
    formula: str
    substituted: str
    value: float
    unit: str
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "symbol": self.symbol,
            "formula": self.formula,
            "substituted": self.substituted,
            "value": self.value,
            "unit": self.unit,
            "result": f"{num(self.value)} {self.unit}".strip(),
            "note": self.note,
        }


def num(value: float, digits: int | None = None) -> str:
    """Format a number the way it would be written in a hand calculation."""
    if value != value:  # NaN
        return "-"
    magnitude = abs(value)
    if digits is None:
        if magnitude >= 1000:
            digits = 0
        elif magnitude >= 100:
            digits = 1
        elif magnitude >= 10:
            digits = 2
        elif magnitude >= 1:
            digits = 3
        elif magnitude == 0:
            digits = 0
        else:
            digits = 4
    text = f"{value:,.{digits}f}"
    return text.replace(",", "\u2009")  # thin space as thousands separator


def kn(newtons: float) -> str:
    return f"{num(newtons / 1000.0)} kN"
