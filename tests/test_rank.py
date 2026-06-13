from foreact.community import load_communities
from foreact.config import load_config
from foreact.event import load_event
from foreact.rank import rank_communities

from .conftest import path


def test_rank_cyclone_prioritises_high_exposure_communities():
    config = load_config(path("config/fiji.yaml"))
    event = load_event(path("examples/cyclone_trigger.json"))
    communities = load_communities(path("data/fiji_communities.csv"))

    ranked = rank_communities(communities, event, config)

    assert ranked
    assert ranked[0].community.name in {"Kadavu coastal villages", "Nakorotubu", "Lau outer islands"}
    assert ranked[0].priority in {"critical", "high"}
    assert ranked[0].actions
    assert ranked[0].total_cost > 0
    assert "forecast exposure" in " ".join(ranked[0].reasons)


def test_flood_event_uses_flood_path():
    config = load_config(path("config/fiji.yaml"))
    event = load_event(path("examples/flood_trigger.json"))
    communities = load_communities(path("data/fiji_communities.csv"))

    ranked = rank_communities(communities, event, config)

    names = [item.community.name for item in ranked[:3]]
    assert "Rewa delta villages" in names or "Navua river settlements" in names
    assert all("Shelter reinforcement kit" not in [a.name for a in item.actions] for item in ranked)


def test_unaffected_divisions_are_not_ranked():
    config = load_config(path("config/fiji.yaml"))
    event = load_event(path("examples/flood_trigger.json"))
    communities = load_communities(path("data/fiji_communities.csv"))

    ranked = rank_communities(communities, event, config)

    assert all(item.community.division in {"Central", "Western"} for item in ranked)
