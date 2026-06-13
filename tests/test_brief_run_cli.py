import json

from foreact.brief import render_brief
from foreact.cli import main
from foreact.community import load_communities
from foreact.config import load_config
from foreact.event import load_event
from foreact.rank import rank_communities
from foreact.run import run_pipeline

from .conftest import path


def test_render_brief_contains_decision_support_warning():
    config = load_config(path("config/fiji.yaml"))
    event = load_event(path("examples/cyclone_trigger.json"))
    ranked = rank_communities(load_communities(path("data/fiji_communities.csv")), event, config)

    text = render_brief(ranked, event, config, event.issued_at)

    assert "human authority must review" in text
    assert "Top Priorities" in text
    assert "Estimated early-action package cost" in text


def test_run_pipeline_writes_outputs(tmp_path):
    result = run_pipeline(
        path("config/fiji.yaml"),
        communities_path=path("data/fiji_communities.csv"),
        event_path=path("examples/cyclone_trigger.json"),
        out_dir=tmp_path,
    )

    assert result.ranked
    assert (tmp_path / "brief.md").exists()
    assert (tmp_path / "ranked_communities.csv").exists()
    log = json.loads((tmp_path / "decision_log.json").read_text(encoding="utf-8"))
    assert log["event"]["id"] == "TC-DEMO-2026-01"
    assert log["ranked"][0]["score"] >= log["ranked"][-1]["score"]


def test_cli_check_and_run(tmp_path, capsys):
    check_code = main([
        "--config", str(path("config/fiji.yaml")),
        "--communities", str(path("data/fiji_communities.csv")),
        "--event", str(path("examples/cyclone_trigger.json")),
        "check",
    ])
    assert check_code == 0
    assert "OK: Fiji config valid" in capsys.readouterr().out

    run_code = main([
        "--config", str(path("config/fiji.yaml")),
        "--communities", str(path("data/fiji_communities.csv")),
        "--event", str(path("examples/cyclone_trigger.json")),
        "run",
        "--out", str(tmp_path),
    ])
    assert run_code == 0
    assert "ranked" in capsys.readouterr().out
    assert (tmp_path / "brief.md").exists()
