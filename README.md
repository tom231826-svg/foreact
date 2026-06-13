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

# Try the flood trigger path
foreact run --event examples/flood_trigger.json --out outputs/flood-demo
```

Open `outputs/demo/brief.md` after running the sample.

## Why AI is essential

The core scoring formula is intentionally transparent and testable. The AI value
is the operational layer around it: converting scattered public documents,
messy facility/community notes and hazard products into structured assumptions,
ranked recommendations and a plain-language decision brief in minutes. Every
assumption remains visible for human review.

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
