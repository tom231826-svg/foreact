# ForeAct

**Open-source AI anticipatory-action decision support — built for Fiji, designed for replication across Pacific SIDS and other LDCs/SIDS.**

[![CI](https://github.com/tom231826-svg/foreact/actions/workflows/ci.yml/badge.svg)](https://github.com/tom231826-svg/foreact/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](pyproject.toml)

> **Status: working prototype.** ForeAct generates ranked, auditable
> anticipatory-action briefs from illustrative Fiji data. It is **not** an
> operational disaster-management system and must not be used for real deployment
> without review by Fiji's disaster, meteorological and sector authorities.

---

## The problem

Fiji already has an anticipatory-action foundation for tropical cyclones: an
official framework and a Red Cross Simplified Early Action Protocol. The remaining
operational gap is the last mile of decision support. When a trigger fires, staff
must quickly decide which communities to prioritize, what to pre-position and how
to explain the decision.

ForeAct fills that operational layer.

## What it does

```text
official trigger event + community vulnerability data + early-action catalogue
        → ranked communities
        → recommended pre-positioning package
        → brief.md + ranked_communities.csv + decision_log.json
```

1. **Accepts** an official trigger fixture for cyclone or flood events.
2. **Fuses** open, aggregate community data: population, older adults, young
   children, disability, shelter capacity, health facilities, access difficulty,
   poverty proxy and hazard exposure.
3. **Ranks** communities by transparent hazard, vulnerability, capacity-gap and
   access components.
4. **Recommends** early-action packages from a configurable catalogue: WASH kits,
   shelter reinforcement, outreach team-days and transport voucher blocks.
5. **Publishes** an auditable decision pack for human review.

## Quickstart

```bash
git clone https://github.com/tom231826-svg/foreact.git
cd foreact
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Validate config, sample trigger and community data
foreact check

# Generate a ranked anticipatory-action brief
foreact run --out outputs/demo

# Try the flood trigger path (global --event goes before the subcommand)
foreact --event examples/flood_trigger.json run --out outputs/flood-demo
```

Open `outputs/demo/brief.md` after running the sample.

## Why AI is essential

The scoring formula is deliberately transparent, testable and deterministic — the
auditable core. The AI is the operational layer around it, and it is **optional and
degrades safely**: with no API key the formula and template brief run exactly as
shown above. Enable it with `--llm` and `OPENAI_API_KEY` to use `gpt-6-luna`
(`reasoning_effort=none`, bounded `max_completion_tokens`). The model does two
things a formula cannot:

1. **Messy field notes → structured assumptions.** Pass `--notes examples/field_notes.json`
   (free text a community officer might radio in after a trigger) and the model
   extracts bounded, reviewable signals — e.g. "access bridge washed out" → harder
   to reach; "clinic flooded and closed" → no health facility — which feed the
   ranking. Conservative do-no-harm rule: AI can automatically escalate risk
   flags, but de-escalating signals remain review-only. Every override is logged
   and printed in the brief for human review.
2. **Plain-language decision brief.** It writes the executive summary for the
   authorities from the structured ranking, using only those facts.

On any error or missing key it falls back to the deterministic path, so a run is
never blocked (do-no-harm). Try it:

```bash
export OPENAI_API_KEY=sk-...
foreact --event examples/cyclone_trigger.json run --llm --notes examples/field_notes.json --out outputs/demo
```

`FOREACT_LLM_PROVIDER=openai|anthropic|none` and `FOREACT_LLM_MODEL` remain
explicit overrides, with legacy `HEATLINE_LLM_*` fallbacks. Anthropic requires
an explicit provider selection plus `ANTHROPIC_API_KEY`; it is never selected
automatically. Without an OpenAI key, the default stays deterministic. Clear old
provider/model overrides under both prefixes to use Luna. See the
[Luna API documentation](https://developers.openai.com/api/docs/models/gpt-6-luna).

## Documentation

- [Architecture](docs/architecture.md)
- [Safety / do-no-harm](docs/safety.md)
- [Digital Public Goods alignment](docs/DPG-compliance.md)
- [Deployment](docs/deployment.md)

## Development

```bash
pytest --cov=foreact
```

## License & Data

Code is under the [MIT License](LICENSE). Sample community and trigger files are
illustrative synthetic fixtures for demonstration only.

## Acknowledgements

Built as an entry candidate for the **UNFCCC AI for Climate Action Award (AICA)
2026**, inspired by Fiji's anticipatory-action work and global forecast-based
action practice.
