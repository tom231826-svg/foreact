"""Risk ranking and early-action recommendations."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Iterable, List

from .community import Community
from .config import ActionItem, CountryConfig
from .event import ImpactZone, TriggerEvent


@dataclass(frozen=True)
class RecommendedAction:
    name: str
    units: int
    unit: str
    estimated_cost: float
    rationale: str


@dataclass(frozen=True)
class RankedCommunity:
    community: Community
    score: float
    priority: str
    hazard_score: float
    vulnerability_score: float
    capacity_gap_score: float
    access_score: float
    exposed_people: int
    confidence: float
    reasons: List[str]
    actions: List[RecommendedAction]

    @property
    def total_cost(self) -> float:
        return round(sum(action.estimated_cost for action in self.actions), 2)


def rank_communities(
    communities: Iterable[Community],
    event: TriggerEvent,
    config: CountryConfig,
) -> List[RankedCommunity]:
    """Rank communities affected by the trigger event.

    ForeAct never decides whether an official trigger should fire. It only ranks
    communities after a human-authorised trigger is present.
    """
    ranked = []
    for community in communities:
        zone = event.zone_for(community.division)
        if zone is None:
            continue
        ranked.append(score_community(community, zone, event, config))
    ranked.sort(key=lambda item: (item.score, item.exposed_people), reverse=True)
    return ranked[: config.max_ranked_communities]


def score_community(
    community: Community,
    zone: ImpactZone,
    event: TriggerEvent,
    config: CountryConfig,
) -> RankedCommunity:
    hazard = _hazard_score(community, zone, event.hazard)
    vulnerability = _vulnerability_score(community)
    capacity_gap = _capacity_gap_score(community)
    access = community.access_score
    weights = config.weights
    score = (
        hazard * weights["hazard"]
        + vulnerability * weights["vulnerability"]
        + capacity_gap * weights["capacity_gap"]
        + access * weights["access"]
    )
    score = round(min(score, 1.0), 3)
    priority = _priority(score, config.priority_thresholds)
    exposed_people = int(round(community.population * min(1.0, 0.45 + hazard * 0.55)))
    confidence = round(min(event.confidence, 0.95) * (0.8 + 0.2 * hazard), 2)
    reasons = _reasons(community, zone, hazard, vulnerability, capacity_gap, access)
    actions = recommend_actions(community, event.hazard, priority, config.actions, exposed_people, reasons)
    return RankedCommunity(
        community=community,
        score=score,
        priority=priority,
        hazard_score=round(hazard, 3),
        vulnerability_score=round(vulnerability, 3),
        capacity_gap_score=round(capacity_gap, 3),
        access_score=round(access, 3),
        exposed_people=exposed_people,
        confidence=confidence,
        reasons=reasons,
        actions=actions,
    )


def recommend_actions(
    community: Community,
    hazard: str,
    priority: str,
    actions: List[ActionItem],
    exposed_people: int,
    reasons: List[str],
) -> List[RecommendedAction]:
    if priority == "watch":
        return []
    multiplier = {"critical": 1.2, "high": 1.0, "medium": 0.55}.get(priority, 0.0)
    recommended = []
    for item in actions:
        if hazard not in item.hazards and "all" not in item.hazards:
            continue
        units = max(1, math.ceil((exposed_people / item.per_people) * multiplier))
        rationale = _action_rationale(item, community, reasons)
        recommended.append(
            RecommendedAction(
                name=item.name,
                units=units,
                unit=item.unit,
                estimated_cost=round(units * item.unit_cost, 2),
                rationale=rationale,
            )
        )
    return recommended


def _hazard_score(community: Community, zone: ImpactZone, hazard: str) -> float:
    wind = min(zone.wind_kmh / 180.0, 1.0)
    rain = min(zone.rainfall_mm / 300.0, 1.0)
    flood = zone.flood_probability
    base_exposure = community.flood_exposure if hazard == "flood" else community.cyclone_exposure
    if hazard == "flood":
        score = 0.45 * rain + 0.35 * flood + 0.20 * base_exposure
    else:
        score = 0.50 * wind + 0.25 * rain + 0.25 * base_exposure
    return min(max(score, 0.0), 1.0)


def _vulnerability_score(community: Community) -> float:
    older = community.older_adults / community.population
    young = community.children_under5 / community.population
    disability = community.disability_count / community.population
    score = (older * 1.8) + (young * 1.5) + (disability * 2.0) + (community.poverty_score * 0.35)
    return min(score, 1.0)


def _capacity_gap_score(community: Community) -> float:
    shelter_gap = max(0, community.population - community.shelter_capacity) / community.population
    health_gap = 0.35 if not community.health_facility else 0.0
    return min((shelter_gap * 0.65) + health_gap, 1.0)


def _priority(score: float, thresholds: Dict[str, float]) -> str:
    if score >= thresholds.get("critical", 0.78):
        return "critical"
    if score >= thresholds["high"]:
        return "high"
    if score >= thresholds["medium"]:
        return "medium"
    return "watch"


def _reasons(
    community: Community,
    zone: ImpactZone,
    hazard: float,
    vulnerability: float,
    capacity_gap: float,
    access: float,
) -> List[str]:
    reasons = []
    if hazard >= 0.7:
        reasons.append(f"high forecast exposure in {community.division} ({zone.wind_kmh:.0f} km/h wind, {zone.rainfall_mm:.0f} mm rain)")
    elif hazard >= 0.45:
        reasons.append(f"moderate forecast exposure in {community.division}")
    if vulnerability >= 0.35:
        reasons.append("large vulnerable population share")
    if capacity_gap >= 0.65:
        reasons.append("shelter and health-service capacity gap")
    elif capacity_gap >= 0.4:
        reasons.append("limited shelter capacity")
    if access >= 0.7:
        reasons.append("hard-to-reach community")
    if not reasons:
        reasons.append("inside official trigger zone")
    return reasons


def _action_rationale(item: ActionItem, community: Community, reasons: List[str]) -> str:
    if "health" in item.name.lower():
        return "prioritise outreach because " + reasons[0]
    if "wash" in item.name.lower() or "water" in item.name.lower():
        return "pre-position WASH support ahead of cyclone/flood disruption"
    if "shelter" in item.name.lower():
        return f"cover expected shelter gap for {community.name}"
    return item.description or "recommended by configured early-action playbook"
