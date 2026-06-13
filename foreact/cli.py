"""Command-line interface: `foreact check | run`."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from .community import CommunityError, load_communities
from .config import ConfigError, load_config
from .event import EventError, load_event
from .rank import rank_communities
from .run import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="foreact",
        description="AI anticipatory-action decision support for official disaster triggers.",
    )
    parser.add_argument("--config", default="config/fiji.yaml", help="country config file")
    parser.add_argument("--communities", default="data/fiji_communities.csv", help="community vulnerability CSV")
    parser.add_argument("--event", default="examples/cyclone_trigger.json", help="official trigger event JSON")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("check", help="validate config, event and community inputs")

    run = sub.add_parser("run", help="rank communities and generate a decision brief")
    run.add_argument("--out", default="outputs/foreact-run", help="output directory")
    run.add_argument("--llm", action="store_true",
                     help="use an AI backend to read field notes and write the brief (falls back to templates)")
    run.add_argument("--notes", default=None, help="optional field-notes JSON (community_id -> free text)")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "check":
            return _cmd_check(args)
        if args.command == "run":
            return _cmd_run(args)
    except (ConfigError, CommunityError, EventError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 1


def _cmd_check(args) -> int:
    config = load_config(args.config)
    event = load_event(args.event)
    communities = load_communities(args.communities)
    ranked = rank_communities(communities, event, config)
    trigger = "active" if event.official_trigger else "planning-mode"
    print(
        f"OK: {config.country} config valid; {len(communities)} communities; "
        f"{len(event.zones)} trigger zone(s); trigger={trigger}; "
        f"{len(ranked)} ranked community candidate(s)."
    )
    return 0


def _cmd_run(args) -> int:
    result = run_pipeline(
        args.config,
        communities_path=args.communities,
        event_path=args.event,
        out_dir=args.out,
        use_llm=args.llm,
        notes_path=args.notes,
    )
    print(result.summary())
    return 0
