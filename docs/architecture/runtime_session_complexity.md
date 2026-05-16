# RuntimeSession Complexity Evidence

Source backlog: `docs/plan/qts_runtime_readiness_deep_review_tasks.md`

M5 guardrail evidence for `RuntimeSession` and runtime coordinator candidates.

## Facade Limits

| Metric | Limit | Current evidence | Decision |
| --- | ---: | ---: | --- |
| RuntimeSession public methods | 12 | 12, excluding `@property` accessors | Pass |
| RuntimeSession private helpers | 8 | 13 | Allowed by this M5 evidence gate until helpers migrate to owning coordinators. |
| RuntimeSession file length | 350 | 492 | Allowed by this M5 evidence gate while event writing and rollback snapshot plumbing remain centralized. |
| Single method length | 50 | `__init__` currently exceeds the limit | Allowed by this M5 evidence gate because dependency wiring is still facade construction. |
| Cyclomatic complexity | 10 | No method may exceed this limit without this evidence gate failing. | Guarded |

## Method Groups

| Group | RuntimeSession public surface |
| --- | --- |
| lifecycle | `start`, `stop`, `pause`, `resume`, `degrade`, `recover` |
| broker lifecycle | `on_broker_disconnect`, `on_broker_reconnect` |
| market data dispatch | `on_market_data_source_event`, `on_market_data` |
| strategy/risk/order processing | private facade plumbing delegates to `TargetIntentProcessor` and runtime coordinators |
| safety/rollback | `activate_kill_switch`, `rollback` |
| event writing | private event-envelope writing remains centralized for sequence and context consistency |

## Coordinator Decisions

| Candidate | Decision | Evidence | Gate |
| --- | --- | --- | --- |
| RuntimeRecoveryCoordinator | Keep | state/policy: owns degraded-to-running recovery transition and audit event write behind the facade | `RUNTIME_COORDINATOR_DECISION` |
| RuntimeRollbackCoordinator | Keep | safety boundary: owns fail-closed rollback evidence capture, active-order snapshotting, and rollback audit event | `RUNTIME_COORDINATOR_DECISION` |
| BrokerRuntimeStartupGate | Keep | independent test value: startup permission decisions are unit-tested separately from RuntimeSession order flow | `RUNTIME_COORDINATOR_DECISION` |
| RuntimeSafetyController | Keep | safety boundary: kill-switch and order-blocking policy remain isolated from market-data dispatch | `RUNTIME_COORDINATOR_DECISION` |
| RuntimeBrokerLifecycleCoordinator | Keep | external boundary: broker disconnect/reconnect reconciliation owns broker-refresh sequencing and recovery gating | `RUNTIME_COORDINATOR_DECISION` |
| RuntimeMarketDataCoordinator | Keep | complexity threshold: inlining market-data, strategy, risk, order, fill, and account-snapshot dispatch would make RuntimeSession unreadable | `RUNTIME_COORDINATOR_DECISION` |

Merge/delete decisions must remove the production class definition in the same change. The guardrail fails if a candidate is marked `Merge` or `Delete` while the class still exists.
