"""Reference data shipped with NEMO: materials, plate stock and shackles."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources


@dataclass(frozen=True)
class YieldBand:
    max_thickness_mm: float
    yield_strength_mpa: float


@dataclass(frozen=True)
class Material:
    id: str
    name: str
    family: str
    source: str
    density_kg_m3: float
    elastic_modulus_gpa: float
    poisson_ratio: float
    tensile_strength_mpa: float
    yield_bands: tuple[YieldBand, ...]

    @property
    def elastic_modulus_mpa(self) -> float:
        return self.elastic_modulus_gpa * 1000.0

    @property
    def max_thickness_mm(self) -> float:
        return self.yield_bands[-1].max_thickness_mm

    def yield_strength_mpa(self, thickness_mm: float) -> float:
        """Minimum yield strength for a plate of the given thickness."""
        if thickness_mm <= 0:
            raise ValueError("Plate thickness must be greater than 0 mm.")
        for band in self.yield_bands:
            if thickness_mm <= band.max_thickness_mm:
                return band.yield_strength_mpa
        raise ValueError(
            f"{self.name} data covers plate up to {self.max_thickness_mm:g} mm; "
            f"{thickness_mm:g} mm is outside it."
        )


@dataclass(frozen=True)
class Shackle:
    size_in: str
    wll_t: float
    jaw_width_mm: float
    pin_diameter_mm: float
    series: str

    @property
    def label(self) -> str:
        return f"{self.wll_t:g} t ({self.size_in} in) {self.series}"


# Crosby side-loading reduction for screw pin and bolt type shackles (Crosby catalogue, "Angular loading of
# Crosby screw pin and bolt type shackles"): (largest side angle in whole degrees, share of the rated WLL).
SIDE_LOAD_BANDS = ((10, 1.00), (20, 0.85), (30, 0.75), (45, 0.70), (55, 0.60), (70, 0.55), (90, 0.50))
# Shackles larger than 3 in: full rating up to 5 degrees, 85% up to 10 degrees, beyond that analysis is required.
LARGE_SIDE_LOAD_BANDS = ((5, 1.00), (10, 0.85))


def shackle_size_inches(size_in: str) -> float:
    """'1 1/4' or '1-1/4' -> 1.25, '5/8' -> 0.625, '3' -> 3.0."""
    total = 0.0
    for part in size_in.replace("-", " ").split():
        if "/" in part:
            top, bottom = part.split("/")
            total += float(top) / float(bottom)
        else:
            total += float(part)
    return total


def shackle_side_load_factor(shackle: "Shackle", side_angle_deg: float) -> float:
    """Share of the working load limit usable when the sling pulls at an angle to the shackle's in-line axis.

    0.0 means the maker does not allow that angle without a separate analysis.
    """
    bands = LARGE_SIDE_LOAD_BANDS if shackle_size_inches(shackle.size_in) > 3.0 else SIDE_LOAD_BANDS
    angle = round(abs(side_angle_deg))
    for limit, factor in bands:
        if angle <= limit:
            return factor
    return 0.0


def _load_json(name: str) -> dict:
    with resources.files(__package__).joinpath(name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=1)
def materials() -> dict[str, Material]:
    raw = _load_json("materials.json")["materials"]
    result: dict[str, Material] = {}
    for item in raw:
        bands = tuple(
            YieldBand(float(b["max_thickness_mm"]), float(b["yield_strength_mpa"]))
            for b in sorted(item["yield_bands"], key=lambda b: b["max_thickness_mm"])
        )
        result[item["id"]] = Material(
            id=item["id"],
            name=item["name"],
            family=item["family"],
            source=item["source"],
            density_kg_m3=float(item["density_kg_m3"]),
            elastic_modulus_gpa=float(item["elastic_modulus_gpa"]),
            poisson_ratio=float(item["poisson_ratio"]),
            tensile_strength_mpa=float(item["tensile_strength_mpa"]),
            yield_bands=bands,
        )
    return result


def get_material(material_id: str) -> Material:
    try:
        return materials()[material_id]
    except KeyError as exc:
        known = ", ".join(materials())
        raise KeyError(f"Unknown material '{material_id}'. Known: {known}") from exc


@lru_cache(maxsize=1)
def shackles() -> tuple[Shackle, ...]:
    raw = _load_json("shackles.json")
    series = raw["series"]
    return tuple(
        Shackle(
            size_in=s["size_in"],
            wll_t=float(s["wll_t"]),
            jaw_width_mm=float(s["jaw_width_mm"]),
            pin_diameter_mm=float(s["pin_diameter_mm"]),
            series=series,
        )
        for s in sorted(raw["shackles"], key=lambda s: s["wll_t"])
    )


def smallest_shackle_for(load_t: float) -> Shackle:
    """Smallest catalogued shackle whose working load limit covers ``load_t``."""
    for shackle in shackles():
        if shackle.wll_t >= load_t:
            return shackle
    largest = shackles()[-1]
    raise ValueError(
        f"No catalogued shackle covers {load_t:.1f} t. The largest is {largest.wll_t:g} t."
    )


@lru_cache(maxsize=1)
def plate_stock() -> dict:
    return _load_json("plates.json")


@lru_cache(maxsize=1)
def piping() -> dict:
    """Pipe sizes, pipe materials, fluids, insulation and U-bolts for pipe supports."""
    return _load_json("piping.json")


def find_by_id(items: list[dict], item_id: str, what: str) -> dict:
    for item in items:
        if item["id"] == item_id:
            return item
    known = ", ".join(i["id"] for i in items)
    raise KeyError(f"Unknown {what} '{item_id}'. Known: {known}")
