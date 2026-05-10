# Live Runtime Startup

## Order

1. Load safe configuration and account-to-broker mappings.
2. Initialize event store and latest actor snapshots.
3. Restore `OrderManagerActor` and `AccountActor` state from snapshots.
4. Connect live feed and broker execution adapters.
5. Reconcile broker snapshots against internal snapshots.
6. Keep new order flow gated until unknown pending orders are classified or resolved.
7. Start strategies only after runtime state is `running`.

## Controls

Runtime states are `stopped`, `starting`, `running`, `paused`, and `degraded`.

`paused` blocks new live order submission. `degraded` is observable and must trigger operator review.
Recovery returns to `running` only after health and reconciliation checks pass.
