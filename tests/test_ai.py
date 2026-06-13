"""AI layer: provider resolution, safe fallback, note enrichment, brief narrative.

All offline — no network, no API keys. The point is that the AI is real but
optional: with no backend the deterministic scorer and template brief run
exactly as before.
"""

from datetime import datetime

import pytest

from foreact import llm
from foreact.brief import render_brief
from foreact.community import load_communities
from foreact.config import load_config
from foreact.enrich import NoteSignal, enrich_communities, generate_brief_narrative, load_notes
from foreact.event import load_event
from foreact.rank import rank_communities

from .conftest import path

GEN = datetime(2026, 6, 13, 9, 0)


def _ranked():
    config = load_config(path("config/fiji.yaml"))
    event = load_event(path("examples/cyclone_trigger.json"))
    communities = load_communities(path("data/fiji_communities.csv"))
    return rank_communities(communities, event, config), event, config


def test_active_provider_none(monkeypatch):
    monkeypatch.setenv("HEATLINE_LLM_PROVIDER", "none")
    assert llm.active_provider() == "none"
    assert llm.available() is False


def test_active_provider_unknown_raises_but_available_is_safe(monkeypatch):
    monkeypatch.setenv("HEATLINE_LLM_PROVIDER", "wizard")
    with pytest.raises(llm.LLMError):
        llm.active_provider()
    assert llm.available() is False  # available() must never raise


def test_load_notes(tmp_path):
    assert load_notes(None) == {}
    assert load_notes(tmp_path / "missing.json") == {}
    good = tmp_path / "n.json"
    good.write_text('{"fji-ba-001": "bridge out"}', encoding="utf-8")
    assert load_notes(good) == {"fji-ba-001": "bridge out"}
    bad = tmp_path / "bad.json"
    bad.write_text('["not", "a", "map"]', encoding="utf-8")
    with pytest.raises(ValueError):
        load_notes(bad)


def test_enrich_without_llm_returns_unchanged():
    communities = load_communities(path("data/fiji_communities.csv"))
    out, signals = enrich_communities(communities, {"fji-ba-001": "bridge washed out"}, use_llm=False)
    assert out == communities
    assert signals == {}


def test_enrich_provider_none_ignores_notes(monkeypatch):
    monkeypatch.setenv("HEATLINE_LLM_PROVIDER", "none")
    communities = load_communities(path("data/fiji_communities.csv"))
    out, signals = enrich_communities(communities, {"fji-ba-001": "bridge washed out"}, use_llm=True)
    assert out == communities  # no backend -> safe fallback, scorer sees original data
    assert signals == {}


def test_narrative_none_without_llm():
    ranked, event, config = _ranked()
    assert generate_brief_narrative(ranked, event, config, use_llm=False) is None


def test_render_brief_includes_ai_sections_when_provided():
    ranked, event, config = _ranked()
    signal = NoteSignal("fji-ba-001", "bridge washed out; clinic closed", 0.95, False, ["access", "health"], "llm:test")
    out = render_brief(
        ranked, event, config, GEN,
        narrative="Authorities should prioritise the eastern islands first.",
        note_signals={"fji-ba-001": signal},
    )
    assert "## AI summary (for human review)" in out
    assert "Authorities should prioritise the eastern islands" in out
    assert "## AI field-note signals applied" in out
    assert "bridge washed out" in out


def test_render_brief_has_no_ai_sections_by_default():
    ranked, event, config = _ranked()
    out = render_brief(ranked, event, config, GEN)
    assert "AI summary" not in out
    assert "field-note signals" not in out


def test_apply_signal_overrides_fields():
    from dataclasses import replace
    from foreact.enrich import _apply_signal
    communities = load_communities(path("data/fiji_communities.csv"))
    target = next(c for c in communities if c.id == "fji-ba-001")
    signal = NoteSignal("fji-ba-001", "harder to reach, clinic closed", 0.9, False, [], "llm:test")
    adjusted = _apply_signal(target, signal)
    assert adjusted.access_score == 0.9
    assert adjusted.health_facility is False
    assert adjusted.name == target.name  # other fields untouched
