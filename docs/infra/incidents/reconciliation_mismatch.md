# Reconciliation Mismatch Incident

## Detection

- Startup or periodic reconciliation reports divergent orders, positions, or cash.
- Internal snapshot and broker snapshot disagree beyond tolerance.

## Immediate Action

- Keep trading disabled.
- Export the operator-visible reconciliation report.
- Preserve internal event-store checkpoint and broker statements.

## Recovery

- Classify each drift item as missing at broker, extra at broker, divergent, or tolerance-only.
- Replay events only through idempotent order/account flows.
- Resume trading only after critical drift is resolved or formally accepted.

## Postmortem

- Record root cause, drift amount, affected account, replay evidence, and controls added.
