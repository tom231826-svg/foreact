"""Official anticipatory-action trigger events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class EventError(ValueError):
    """Raised when a trigger event is missing, malformed or unsafe."""


@dataclass(frozen=True)
class ImpactZone:
    division: str
    wind_kmh: float
    rainfall_mm: float
    flood_probability: float
    lead_time_hours: int


@dataclass(frozen=True)
class TriggerEvent:
    id: str
    hazard: str
    issued_at: datetime
    source: str
    official_trigger: bool
    confidence: float
    notes: str
    zones: List[ImpactZone]

    def zone_for(self, division: str) -> Optional[ImpactZone]:
        division_key = division.strip().lower()
        for zone in self.zones:
            if zone.division.strip().lower() == division_key:
                return zone
        return None


def load_event(path="examples/cyclone_trigger.json") -> TriggerEvent:
    path = Path(path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise EventError(f"event file not found: {path}")
    except json.JSONDecodeError as exc:
        raise EventError(f"{path}: invalid JSON: {exc}")
    if not isinstance(raw, dict):
        raise EventError(f"{path}: event root must be a mapping")
    return parse_event(raw, source_path=path)


def parse_event(raw: Dict, *, source_path: Path | str = "<event>") -> TriggerEvent:
    path = Path(source_path)
    try:
        event = TriggerEvent(
            id=str(raw["id"]),
            hazard=str(raw["hazard"]).lower(),
            issued_at=datetime.fromisoformat(str(raw["issued_at"])),
            source=str(raw.get("source", "unknown")),
            official_trigger=bool(raw.get("official_trigger", False)),
            confidence=float(raw.get("confidence", 0.5)),
            notes=str(raw.get("notes", "")),
            zones=[_parse_zone(item, path) for item in raw["impact_zones"]],
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise EventError(f"{path}: bad trigger event: {exc}")
    if event.hazard not in {"cyclone", "flood", "storm"}:
        raise EventError(f"{path}: unsupported hazard {event.hazard!r}")
    if not 0 <= event.confidence <= 1:
        raise EventError(f"{path}: confidence must be between 0 and 1")
    if not event.zones:
        raise EventError(f"{path}: at least one impact zone is required")
    return event


def _parse_zone(item: dict, path: Path) -> ImpactZone:
    try:
        zone = ImpactZone(
            division=str(item["division"]),
            wind_kmh=float(item.get("wind_kmh", 0)),
            rainfall_mm=float(item.get("rainfall_mm", 0)),
            flood_probability=float(item.get("flood_probability", 0)),
            lead_time_hours=int(item.get("lead_time_hours", 72)),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise EventError(f"{path}: bad impact zone {item!r}: {exc}")
    if not zone.division:
        raise EventError(f"{path}: zone division is required")
    if not 0 <= zone.flood_probability <= 1:
        raise EventError(f"{path}: flood_probability must be 0-1")
    if zone.wind_kmh < 0 or zone.rainfall_mm < 0 or zone.lead_time_hours <= 0:
        raise EventError(f"{path}: zone values must be non-negative")
    return zone
