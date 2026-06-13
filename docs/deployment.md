# Deployment Notes

## Minimum Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
foreact check
foreact run --out outputs/demo
```

## Adapting To Another Country

1. Copy `config/fiji.yaml`.
2. Replace the action catalogue, currency, weights and data sources.
3. Replace `data/fiji_communities.csv` with an aggregate community dataset.
4. Replace `examples/cyclone_trigger.json` with the official trigger format.
5. Run `foreact check` and review component scores with local officials.

## Operational Integration

ForeAct should sit behind an official anticipatory-action framework. It can be
run manually by NDMO or Red Cross staff, or scheduled when a trigger service
publishes an endorsed event.

