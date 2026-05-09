# State Recovery

Runtime state should be recoverable from snapshots and events.

Persist when relevant:

- Strategy state
- Indicator state
- Account snapshot
- Position book
- Pending orders
- Order state machine
- Event log / audit trail

Recovery must be deterministic for the same event sequence.
