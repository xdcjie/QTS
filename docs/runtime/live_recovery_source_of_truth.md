# Live Recovery Source Of Truth

## Precedence

1. Event store replay is the durable internal history.
2. Actor snapshots speed recovery but do not replace replay for missing events.
3. Broker snapshots are external truth for broker-accepted open orders, fills, cash, and positions.
4. Reconciliation reports classify differences before actors receive corrective commands.

## Pending Orders

If a pending internal order has unknown broker state, the runtime must gate new live order flow for
that account until reconciliation resolves it.

## Duplicate Fills

Order and account recovery must preserve fill idempotency state. Replayed or broker-reported
duplicate fills are ignored by the owning actor flow.
