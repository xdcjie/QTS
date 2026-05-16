# IBKR Live Readiness

This checklist must be completed before enabling live order execution.

## Environment Separation

- Use `configs/live.ibkr.example.yaml` as the shape for live configuration.
- Do not reuse paper account IDs, paper client IDs, paper credentials, or paper risk profiles.
- Keep market data and order execution in separate config sections.
- Keep market data and order execution on distinct IBKR client IDs.
- Load credentials from environment variables or a secret manager, never from committed config.
- Live observation config must reject `DUP...` paper accounts and paper-only
  client IDs or secret references.
- Live observation mode must keep `orders_enabled: false` until signoff evidence exists.

## Cutover

1. Confirm `make check` passes.
2. Confirm paper flow passes with fake IBKR transports.
3. Confirm live configuration passes IBKR environment guardrails.
4. Confirm account ID, permissions, and risk profile with the broker account owner.
5. Start market data worker first and verify normalized ticks/quotes/bars.
6. Start order execution worker in observe-only mode if available.
7. Compare paper decisions against live market and broker state.
8. Submit a minimal test order only after engineering, operations, and risk signoff.

## Reconnect

- Preserve internal pending orders before reconnect.
- Rebuild broker order ID to internal order ID mapping from the latest `OrderManager` snapshot.
- Normalize all post-reconnect broker reports before processing them.
- Treat duplicate execution reports as idempotent.

## Reconciliation

- Compare open broker orders against internal non-terminal orders.
- Compare broker fills against accepted internal fills by fill ID.
- Investigate any broker order ID that cannot be mapped to an internal order ID.
- Do not mutate account state directly from broker reports; route through OrderManager and AccountActor.

## Rollback

- Disable live order submission.
- Leave market data running if needed for observability.
- Cancel or flatten only through the approved order path.
- Save the event store, snapshots, logs, and broker reports for review.
