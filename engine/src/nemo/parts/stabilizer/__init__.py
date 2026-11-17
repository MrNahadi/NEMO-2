"""Roll-stabilizer fin: foil loads, internal structure (skin, spars, ribs) and stock, checked with IACS UR S10."""

from .checks import check_fin
from .geometry import FinDesign
from .job import FinJob, fin_loads

__all__ = ["FinDesign", "FinJob", "check_fin", "fin_loads"]
