"""Design rule sets.

Each rule set supplies capacities and allowable stresses. Parts call the rule
set; they never hard-code a code's factors. Adding DNV, BV, Lloyd's Register or
ABS means adding a module here with the same methods.

Which rule set fits depends on the part: ASME BTH-1 for lifting devices
(padeyes), AISC 360 for general steel details (pipe support brackets), IACS
UR S10 for all-movable foils on a stock (stabilizer fins).
"""

from __future__ import annotations

from .aisc360 import AISC360
from .asme_bth1 import ASMEBTH1
from .iacs_s10 import IACSS10

RULE_SETS = {
    ASMEBTH1.id: ASMEBTH1,
    AISC360.id: AISC360,
    IACSS10.id: IACSS10,
}

PART_RULE_SETS = {
    "padeye": (ASMEBTH1.id,),
    "pipe-bracket": (AISC360.id,),
    "stabilizer": (IACSS10.id,),
}


def get_rule_set(rule_set_id: str, **options):
    try:
        cls = RULE_SETS[rule_set_id]
    except KeyError as exc:
        known = ", ".join(RULE_SETS)
        raise KeyError(f"Unknown rule set '{rule_set_id}'. Known: {known}") from exc
    return cls(**options)


__all__ = ["AISC360", "ASMEBTH1", "IACSS10", "PART_RULE_SETS", "RULE_SETS", "get_rule_set"]
