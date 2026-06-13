"""Community-level exposure and vulnerability data."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass(frozen=True)
class Community:
    id: str
    name: str
    division: str
    lat: float
    lon: float
    population: int
    older_adults: int
    children_under5: int
    disability_count: int
    shelter_capacity: int
    health_facility: bool
    access_score: float  # 0 easy, 1 very hard
    poverty_score: float  # 0 low, 1 high
    cyclone_exposure: float  # 0 low, 1 high
    flood_exposure: float  # 0 low, 1 high


class CommunityError(ValueError):
    """Raised when community data is missing or malformed."""


def load_communities(path="data/fiji_communities.csv") -> List[Community]:
    path = Path(path)
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
    except FileNotFoundError:
        raise CommunityError(f"community file not found: {path}")
    if not rows:
        raise CommunityError(f"{path}: no communities found")
    communities = [_parse_row(row, path, index + 2) for index, row in enumerate(rows)]
    ids = [c.id for c in communities]
    if len(ids) != len(set(ids)):
        raise CommunityError(f"{path}: duplicate community id")
    return communities


def _parse_row(row: dict, path: Path, line_no: int) -> Community:
    try:
        community = Community(
            id=str(row["id"]).strip(),
            name=str(row["name"]).strip(),
            division=str(row["division"]).strip(),
            lat=float(row["lat"]),
            lon=float(row["lon"]),
            population=int(row["population"]),
            older_adults=int(row["older_adults"]),
            children_under5=int(row["children_under5"]),
            disability_count=int(row["disability_count"]),
            shelter_capacity=int(row["shelter_capacity"]),
            health_facility=_bool(row["health_facility"]),
            access_score=float(row["access_score"]),
            poverty_score=float(row["poverty_score"]),
            cyclone_exposure=float(row["cyclone_exposure"]),
            flood_exposure=float(row["flood_exposure"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise CommunityError(f"{path}:{line_no}: bad community row: {exc}")

    if not community.id or not community.name or not community.division:
        raise CommunityError(f"{path}:{line_no}: id, name and division are required")
    if community.population <= 0:
        raise CommunityError(f"{path}:{line_no}: population must be positive")
    if any(value < 0 for value in (community.older_adults, community.children_under5,
                                  community.disability_count, community.shelter_capacity)):
        raise CommunityError(f"{path}:{line_no}: counts must be non-negative")
    for field in ("access_score", "poverty_score", "cyclone_exposure", "flood_exposure"):
        value = getattr(community, field)
        if not 0 <= value <= 1:
            raise CommunityError(f"{path}:{line_no}: {field} must be between 0 and 1")
    return community


def _bool(value) -> bool:
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y"}:
        return True
    if text in {"0", "false", "no", "n"}:
        return False
    raise ValueError(f"not a boolean: {value!r}")
