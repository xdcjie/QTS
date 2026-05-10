# Production Soak Plan

Production readiness requires a paper or observation-mode soak before any live capital rollout.

## Duration

- Run at least one full regular trading session for the target instruments.
- For futures with overnight sessions, include the exchange-defined open, maintenance break if any, and close.
- Record the exact start and end timestamps, mode, account, broker environment, strategy set, and dataset/feed source.

## Metrics

- Queue depth and event lag for market data, strategy, risk, order, execution, and account flows.
- Stale data age by instrument.
- Broker connection and market-data connection status.
- Rejected orders by risk reason code.
- Memory growth and process restarts.
- Internal versus broker state drift at startup, periodic checks, and shutdown.

## Success Gate

- No unexplained state drift.
- No unbounded event lag.
- No dropped broker callbacks.
- Kill switch drill completed and audited.
- Reconciliation report is operator-visible and blocks trading on critical drift.
