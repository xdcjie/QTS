# Runtime Durability Recovery

Runtime durability recovery is a shared runtime boundary. It proves that a
crash/restart can recover from durable actor snapshots plus the append-only
runtime event store before live order submission resumes.

## Invariants

- Event-store recovery requires contiguous persisted sequence numbers. Missing
  or duplicate sequences block recovery.
- Snapshot payloads must use the expected schema version. Unsupported versions
  block recovery unless a future explicit migration owner is added.
- The recovered named runtime state must equal the pre-crash state after loading
  the latest snapshots and replaying events after the latest snapshot sequence.
- Live order submission must stay disabled after durable recovery until the
  observation/reconciliation gate returns `ALLOW_LIVE`.

## Boundary

`qts.runtime.durability.RuntimeDurabilityDrill` owns the durability drill. It
uses existing event-store, snapshot-store, and live recovery decision contracts;
it does not own actor business state or broker reconciliation semantics.

The drill writes runtime events, saves named actor/state snapshots, recreates
store instances to simulate restart, validates event sequence continuity, loads
latest snapshots, replays post-snapshot events, compares recovered state against
crash-time state, and returns recovery/live gate evidence.

## Gates

Integration coverage in `tests/integration/test_runtime_durability_recovery.py`
protects:

- snapshot plus post-snapshot event replay equality;
- event sequence gap blocking recovery;
- snapshot schema mismatch blocking recovery;
- reconciliation-required live order submission blocking;
- recovered state mismatch detection.
