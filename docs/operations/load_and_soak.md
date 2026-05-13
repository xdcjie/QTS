# Load And Soak

## Load Scenario

`make load-test` runs a deterministic small market-data generation scenario. It is intended for a
quick local path check, not capacity certification.

## Soak Scenario

`make soak-test` documents the manual gate. Live beta requires a paper-trading soak with:

- Runtime running continuously for the agreed window.
- One full regular trading session when claiming paper readiness for live code-path use.
- No unclassified reconciliation drift.
- No unknown pending orders.
- Queue lag and broker/feed reconnects recorded.
- Event lag, queue depth, runtime state transitions, stale-data events, broker status,
  rejected orders, memory growth, reconnects, and end-of-session reconciliation
  recorded in `evidence/ibkr/paper-soak-*.json`.
- Operator notes recorded for every manual intervention.

Missing or failed paper soak blocks live beta.
