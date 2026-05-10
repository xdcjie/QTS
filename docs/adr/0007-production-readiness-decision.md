# ADR 0007: Production Readiness Decision

## Status

Accepted

## Decision

S4 records a No-Go decision for real production capital until external live-readiness evidence is complete.

## Rationale

The system has explicit dataset provenance, deterministic backtest report hashes, replay and reconciliation verification lanes, live startup guards, observation mode semantics, broker capability modeling, incident runbooks, and rollout/rollback documentation. These are necessary for production readiness but not sufficient without real broker, operator, and soak evidence.

## Limitations

- Real IBKR TWS/Gateway behavior must be validated in the target environment.
- Production secrets are referenced by environment and are not stored in the repository.
- Critical reconciliation drift blocks trading.

## Rollback Criteria

Rollback is required if broker connectivity is unstable, market data becomes stale beyond configured thresholds, reconciliation drift is critical, kill switch cancellation does not complete, or unexplained paper-vs-live differences occur.
