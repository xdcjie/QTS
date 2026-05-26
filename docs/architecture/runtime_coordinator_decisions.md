# Runtime Coordinator Decisions

Authoritative M5.2 keep / merge / delete audit for runtime coordinator candidates.

Source backlog: `docs/architecture/runtime_session_complexity.md`

Guardrail: `RUNTIME_COORDINATOR_DECISION`

## Decision Criteria

| Decision | Meaning |
| --- | --- |
| Keep | Owns state, policy, evidence generation, an external boundary, safety boundary, independent test value, or complexity that would otherwise make the facade unreadable. |
| Merge | Only forwards one or two calls and should move back to its caller or owning concept. |
| Delete | Has no production responsibility and no production imports. |

## Coordinator Decisions

| Candidate | Decision | Evidence | Gate |
| --- | --- | --- | --- |
| RuntimeRecoveryCoordinator | Keep | state/policy: owns degraded-to-running recovery transition and audit event write behind the facade | `RUNTIME_COORDINATOR_DECISION` |
| RuntimeRollbackCoordinator | Keep | safety boundary: owns fail-closed rollback evidence capture, active-order snapshotting, and rollback audit event | `RUNTIME_COORDINATOR_DECISION` |
| RuntimeBrokerLifecycleCoordinator | Keep | external boundary: broker disconnect/reconnect reconciliation owns broker-refresh sequencing and recovery gating | `RUNTIME_COORDINATOR_DECISION` |
| RuntimeMarketDataCoordinator | Keep | complexity threshold: inlining market-data, strategy, risk, order, fill, and account-snapshot dispatch would make RuntimeSession unreadable | `RUNTIME_COORDINATOR_DECISION` |
| RuntimeSafetyController | Keep | safety boundary: kill-switch and order-blocking policy remain isolated from market-data dispatch | `RUNTIME_COORDINATOR_DECISION` |
| BrokerRuntimeStartupGate | Keep | independent test value: startup permission decisions are unit-tested separately from RuntimeSession order flow | `RUNTIME_COORDINATOR_DECISION` |
| BrokerRuntimeTopologyResolver | Keep | external boundary: resolves broker runtime topology dependencies and evidence separately from RuntimeSession construction | `RUNTIME_COORDINATOR_DECISION` |

Merge/delete decisions must remove the production class definition in the same change. Delete decisions must also leave no production import of the deleted coordinator.
