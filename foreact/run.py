"""Orchestrate a ForeAct anticipatory-action run."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from .brief import write_outputs
from .community import load_communities
from .config import load_config
from .event import load_event
from .rank import RankedCommunity, rank_communities


@dataclass(frozen=True)
class RunResult:
    ranked: List[RankedCommunity]
    outputs: Dict[str, Path]

    def summary(self) -> str:
        top = self.ranked[0].community.name if self.ranked else "none"
        people = sum(item.exposed_people for item in self.ranked)
        cost = sum(item.total_cost for item in self.ranked)
        return (
            f"ranked {len(self.ranked)} communit(ies); top={top}; "
            f"people_exposed={people}; estimated_cost={cost:.0f}; "
            f"outputs={', '.join(str(p) for p in self.outputs.values())}"
        )


def run_pipeline(
    config_path="config/fiji.yaml",
    *,
    communities_path="data/fiji_communities.csv",
    event_path="examples/cyclone_trigger.json",
    out_dir="outputs/foreact-run",
) -> RunResult:
    config = load_config(config_path)
    event = load_event(event_path)
    communities = load_communities(communities_path)
    ranked = rank_communities(communities, event, config)
    outputs = write_outputs(ranked, event, config, out_dir)
    return RunResult(ranked=ranked, outputs=outputs)
