# Architecture

ForeAct is a decision-support pipeline for official anticipatory-action triggers.

```text
official trigger event
        +
community exposure/vulnerability CSV
        +
country config and early-action catalogue
        ↓
risk scoring and priority ranking
        ↓
recommended early-action package
        ↓
brief.md + ranked_communities.csv + decision_log.json
```

## Modules

- `foreact.config`: country-level weights, thresholds and action items.
- `foreact.community`: aggregate community exposure and vulnerability records.
- `foreact.event`: official trigger fixture and impact zones.
- `foreact.rank`: transparent scoring, priority tiers and recommended packages.
- `foreact.brief`: auditable markdown, CSV and JSON outputs.
- `foreact.cli`: `foreact check` and `foreact run`.

## What The AI Layer Represents

The current MVP uses deterministic scoring so results are testable and auditable.
The intended AI layer is the structured-data and brief-generation layer around
that core: reading messy public documents or field notes, filling explicit
reviewable assumptions, and drafting a decision brief that a human authority can
approve or edit. The scoring formula remains transparent.

## Non-Goals

- ForeAct does not decide whether a trigger fires.
- ForeAct does not message the public.
- ForeAct does not use personal data.
- ForeAct does not replace a national disaster authority.

