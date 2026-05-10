# Live Beta Incident Runbook

## Runtime Paused

1. Confirm operator and idempotency key from audit logs.
2. Check queue depth, broker health, feed health, and latest reconciliation report.
3. Resume only after the blocking condition is resolved.

## Broker Disconnect

1. Enter degraded mode.
2. Stop new order submission for affected broker/account partitions.
3. Reconnect using configured backoff.
4. Reconcile before clearing the gate.

## Reconciliation Drift

1. Classify missing, extra, divergent, matched, and tolerance-only items.
2. Do not mutate actor state directly from the report.
3. Apply corrective commands through owning actors after review.
