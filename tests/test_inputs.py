from foreact.community import load_communities
from foreact.event import load_event

from .conftest import path


def test_load_communities():
    communities = load_communities(path("data/fiji_communities.csv"))
    assert len(communities) == 12
    assert communities[0].division == "Western"
    assert all(0 <= c.access_score <= 1 for c in communities)


def test_load_cyclone_event():
    event = load_event(path("examples/cyclone_trigger.json"))
    assert event.official_trigger is True
    assert event.hazard == "cyclone"
    assert event.zone_for("Western").wind_kmh == 150
    assert event.zone_for("Northern") is None


def test_load_flood_event():
    event = load_event(path("examples/flood_trigger.json"))
    assert event.hazard == "flood"
    assert event.zone_for("Central").flood_probability == 0.93
