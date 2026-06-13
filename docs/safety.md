# Safety And Do-No-Harm

ForeAct is advisory decision support. It should only be used after an official
anticipatory-action trigger has fired or in planning/simulation mode.

## Safeguards

- **Official trigger first**: the event file carries `official_trigger`.
- **Human authority decides**: every output repeats that deployment requires
  human review.
- **No personal data**: the MVP uses aggregate community-level fields only.
- **Auditable reasoning**: every ranked community includes component scores and
  human-readable reasons.
- **Conservative action catalogue**: all pre-positioning actions come from the
  country config, not from free-form generation.
- **Decision log**: each run emits `decision_log.json` with weights, thresholds,
  trigger details and ranked outputs.

## Operational Caveat

The sample data and trigger files in this repository are illustrative. They are
for demonstration, testing and grant review. They are not operational Fiji
government data and must not be used for real-world deployment.

