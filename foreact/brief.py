"""Generate auditable anticipatory-action briefs."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .config import CountryConfig
from .event import TriggerEvent
from .rank import RankedCommunity


def write_outputs(
    ranked: List[RankedCommunity],
    event: TriggerEvent,
    config: CountryConfig,
    out_dir="outputs/foreact-run",
    *,
    generated_at: Optional[datetime] = None,
) -> Dict[str, Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    now = generated_at or datetime.now()
    paths = {
        "brief": out / "brief.md",
        "ranked_csv": out / "ranked_communities.csv",
        "decision_log": out / "decision_log.json",
    }
    paths["brief"].write_text(render_brief(ranked, event, config, now), encoding="utf-8")
    _write_csv(paths["ranked_csv"], ranked)
    paths["decision_log"].write_text(json.dumps(decision_log(ranked, event, config, now), indent=2), encoding="utf-8")
    return paths


def render_brief(
    ranked: List[RankedCommunity],
    event: TriggerEvent,
    config: CountryConfig,
    generated_at: datetime,
) -> str:
    title = f"# ForeAct anticipatory-action brief: {event.id}"
    trigger = "YES" if event.official_trigger else "NO - planning mode only"
    total_people = sum(item.exposed_people for item in ranked)
    total_cost = sum(item.total_cost for item in ranked)
    lines = [
        title,
        "",
        f"- Generated: {generated_at.isoformat(timespec='minutes')}",
        f"- Country: {config.country}",
        f"- Hazard: {event.hazard}",
        f"- Official trigger active: {trigger}",
        f"- Source: {event.source}",
        f"- Confidence: {event.confidence:.2f}",
        f"- Ranked communities: {len(ranked)}",
        f"- Estimated people exposed in ranked list: {total_people:,}",
        f"- Estimated early-action package cost: {config.currency} {total_cost:,.0f}",
        "",
        "> Advisory decision support only. A human authority must review assumptions, local access and stock availability before deployment.",
        "",
        "## Top Priorities",
        "",
    ]
    if not ranked:
        lines.append("No communities matched the current trigger zones.")
    for index, item in enumerate(ranked, start=1):
        c = item.community
        lines.extend([
            f"### {index}. {c.name} ({c.division}) - {item.priority.upper()}",
            "",
            f"- Score: {item.score:.3f} | confidence: {item.confidence:.2f}",
            f"- Exposed people estimate: {item.exposed_people:,} of {c.population:,}",
            f"- Components: hazard {item.hazard_score:.2f}, vulnerability {item.vulnerability_score:.2f}, capacity gap {item.capacity_gap_score:.2f}, access {item.access_score:.2f}",
            f"- Why: {'; '.join(item.reasons)}",
        ])
        if item.actions:
            lines.append("- Recommended early actions:")
            for action in item.actions:
                lines.append(
                    f"  - {action.name}: {action.units} {action.unit}(s), "
                    f"{config.currency} {action.estimated_cost:,.0f} - {action.rationale}"
                )
        else:
            lines.append("- Recommended early actions: monitor; no package generated below medium threshold.")
        lines.append("")

    lines.extend([
        "## Trigger Zones",
        "",
        "| Division | Wind km/h | Rainfall mm | Flood probability | Lead time h |",
        "|---|---:|---:|---:|---:|",
    ])
    for zone in event.zones:
        lines.append(
            f"| {zone.division} | {zone.wind_kmh:.0f} | {zone.rainfall_mm:.0f} | {zone.flood_probability:.2f} | {zone.lead_time_hours} |"
        )
    lines.extend([
        "",
        "## Data Sources",
        "",
    ])
    for source in config.data_sources:
        lines.append(f"- {source}")
    if event.notes:
        lines.extend(["", "## Notes", "", event.notes])
    return "\n".join(lines) + "\n"


def decision_log(
    ranked: List[RankedCommunity],
    event: TriggerEvent,
    config: CountryConfig,
    generated_at: datetime,
) -> dict:
    return {
        "generated_at": generated_at.isoformat(),
        "event": {
            "id": event.id,
            "hazard": event.hazard,
            "issued_at": event.issued_at.isoformat(),
            "source": event.source,
            "official_trigger": event.official_trigger,
            "confidence": event.confidence,
            "zones": [asdict(zone) for zone in event.zones],
        },
        "config": {
            "country": config.country,
            "weights": config.weights,
            "priority_thresholds": config.priority_thresholds,
            "currency": config.currency,
        },
        "ranked": [
            {
                "community_id": item.community.id,
                "community": item.community.name,
                "division": item.community.division,
                "score": item.score,
                "priority": item.priority,
                "exposed_people": item.exposed_people,
                "confidence": item.confidence,
                "reasons": item.reasons,
                "actions": [asdict(action) for action in item.actions],
                "total_cost": item.total_cost,
            }
            for item in ranked
        ],
    }


def _write_csv(path: Path, ranked: List[RankedCommunity]) -> None:
    fields = [
        "rank", "community_id", "community", "division", "priority", "score",
        "exposed_people", "confidence", "total_cost", "reasons",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for index, item in enumerate(ranked, start=1):
            writer.writerow({
                "rank": index,
                "community_id": item.community.id,
                "community": item.community.name,
                "division": item.community.division,
                "priority": item.priority,
                "score": item.score,
                "exposed_people": item.exposed_people,
                "confidence": item.confidence,
                "total_cost": item.total_cost,
                "reasons": "; ".join(item.reasons),
            })
