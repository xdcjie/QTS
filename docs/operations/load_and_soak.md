# Load And Soak

## Load Scenario

`make load-test` runs a deterministic small market-data generation scenario. It is intended for a
quick local path check, not capacity certification.

## Soak Scenario

`make soak-test` documents the manual gate. Live beta requires a paper-trading soak with:

- Runtime running continuously for the agreed window.
- No unclassified reconciliation drift.
- No unknown pending orders.
- Queue lag and broker/feed reconnects recorded.

Missing or failed paper soak blocks live beta.
