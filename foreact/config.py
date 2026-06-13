"""Load and validate a country configuration for ForeAct.

Everything country-specific lives in one YAML file: scoring weights, action
catalogue, currency and operating assumptions. Adapting ForeAct to another
country should mean replacing data and config, not rewriting the ranking engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import yaml


class ConfigError(ValueError):
    """Raised when a configuration file is missing, malformed or unsafe."""


@dataclass(frozen=True)
class ActionItem:
    name: str
    unit: str
    unit_cost: float
    per_people: int
    hazards: List[str]
    description: str


@dataclass(frozen=True)
class CountryConfig:
    country: str
    currency: str
    lead_time_hours: int
    max_ranked_communities: int
    weights: Dict[str, float]
    priority_thresholds: Dict[str, float]
    actions: List[ActionItem]
    institutions: List[str]
    data_sources: List[str]


REQUIRED_WEIGHTS = ("hazard", "vulnerability", "capacity_gap", "access")


def load_config(path="config/fiji.yaml") -> CountryConfig:
    path = Path(path)
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ConfigError(f"config file not found: {path}")
    except yaml.YAMLError as exc:
        raise ConfigError(f"{path}: invalid YAML: {exc}")
    if not isinstance(raw, dict):
        raise ConfigError(f"{path}: config root must be a mapping")

    for key in ("country", "currency", "weights", "priority_thresholds", "actions"):
        if key not in raw:
            raise ConfigError(f"{path}: missing required key: {key}")

    weights = _parse_float_map(raw["weights"], path, "weights")
    missing = [key for key in REQUIRED_WEIGHTS if key not in weights]
    if missing:
        raise ConfigError(f"{path}: missing weight(s): {', '.join(missing)}")
    total = sum(weights[key] for key in REQUIRED_WEIGHTS)
    if not 0.95 <= total <= 1.05:
        raise ConfigError(f"{path}: core weights must sum to ~1.0, got {total:.2f}")

    thresholds = _parse_float_map(raw["priority_thresholds"], path, "priority_thresholds")
    for key in ("high", "medium"):
        if key not in thresholds:
            raise ConfigError(f"{path}: missing priority threshold: {key}")
    if not thresholds["high"] > thresholds["medium"] > 0:
        raise ConfigError(f"{path}: thresholds must satisfy high > medium > 0")

    actions = _parse_actions(raw["actions"], path)
    lead_time_hours = int(raw.get("lead_time_hours", 72))
    if not 6 <= lead_time_hours <= 168:
        raise ConfigError(f"{path}: lead_time_hours must be between 6 and 168")
    max_ranked = int(raw.get("max_ranked_communities", 10))
    if not 1 <= max_ranked <= 100:
        raise ConfigError(f"{path}: max_ranked_communities must be 1-100")

    return CountryConfig(
        country=str(raw["country"]),
        currency=str(raw["currency"]),
        lead_time_hours=lead_time_hours,
        max_ranked_communities=max_ranked,
        weights=weights,
        priority_thresholds=thresholds,
        actions=actions,
        institutions=[str(x) for x in raw.get("institutions", [])],
        data_sources=[str(x) for x in raw.get("data_sources", [])],
    )


def _parse_float_map(value, path: Path, name: str) -> Dict[str, float]:
    if not isinstance(value, dict) or not value:
        raise ConfigError(f"{path}: {name} must be a non-empty mapping")
    result = {}
    for key, raw in value.items():
        try:
            result[str(key)] = float(raw)
        except (TypeError, ValueError):
            raise ConfigError(f"{path}: {name}.{key} must be numeric")
    return result


def _parse_actions(entries, path: Path) -> List[ActionItem]:
    if not isinstance(entries, list) or not entries:
        raise ConfigError(f"{path}: actions must be a non-empty list")
    actions = []
    for item in entries:
        if not isinstance(item, dict):
            raise ConfigError(f"{path}: bad action entry: {item!r}")
        try:
            action = ActionItem(
                name=str(item["name"]),
                unit=str(item.get("unit", "kit")),
                unit_cost=float(item["unit_cost"]),
                per_people=int(item.get("per_people", 100)),
                hazards=[str(h) for h in item.get("hazards", ["cyclone", "flood"])],
                description=str(item.get("description", "")),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ConfigError(f"{path}: bad action entry {item!r}: {exc}")
        if action.unit_cost < 0 or action.per_people <= 0:
            raise ConfigError(f"{path}: action {action.name!r} has unsafe cost/per_people")
        actions.append(action)
    return actions
