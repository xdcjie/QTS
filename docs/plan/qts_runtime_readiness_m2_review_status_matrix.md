# QTS Runtime Readiness M2 Review Status Matrix

Source backlog: `docs/plan/qts_runtime_readiness_deep_review_tasks.md`

Scope: Milestone 2 - Live Capital safety gates

Baseline: 2026-05-16, `HEAD 5cc2fe6`

## Completion Rules

M2 is complete only when live-capital order enablement is fail-closed across permission, startup, broker lifecycle, market-data risk, and operator emergency controls.

No direct bypass, compatibility wrapper, shadow submit path, or "record-only" checklist item may satisfy an acceptance condition. Every safety decision must produce structured evidence and, where runtime-visible, a runtime event.

## Correctness Invariants

| Invariant | Correct owner or boundary | Forbidden shortcut | Required gate |
| --- | --- | --- | --- |
| Live order submission requires explicit live permission and a passing startup/safety state. | `RuntimeSession` order path plus `RuntimeSafetyController` and `LiveOrderPermission`. | Allowing any alternate live submit API to bypass `RuntimeSession`. | Unit/integration tests for permission-off, observation, paper-vs-live account, and bypass prevention. |
| Live startup blockers are hard blockers, not manifest notes. | `BrokerRuntimeStartupGate`, startup checklist, `RuntimeSession.start()`. | Writing checklist evidence while still entering order-enabled live state. | Per-blocker tests and manifest/event evidence for every blocker. |
| Reconnect cannot resume orders until broker state is reconciled. | Broker lifecycle callbacks, `LiveReconciliation`, `RuntimeSession` degraded/recover flow. | Treating reconnect as healthy before open orders, positions, executions, and account summary are refreshed. | Disconnect/reconnect/reconcile tests and event stream assertions. |
| Delayed, frozen, stale, or unavailable market data must reach `RiskEngine` as a rejection reason for live capital. | `MarketDataFlow`, market-data risk context, risk rules. | Checking feed state only in UI/manifest while live risk accepts the order. | Risk rule tests and runtime rejection-event tests with strategy/account/instrument evidence. |
| Kill switch and rollback block new orders while preserving observability and audit evidence. | `RuntimeSafetyController`, `RuntimeSession`, order/execution actors, rollback evidence. | Stopping all event/snapshot recording or allowing unaudited kill-switch deactivation. | Kill switch, cancel-active-orders, rollback evidence, and unauthorized deactivate tests. |

## Status Matrix

| Task | Status | Current Evidence Candidates | Blocking Gaps | First Red Gate |
| --- | --- | --- | --- | --- |
| M2-1 LiveOrderPermission forced into order path | Implemented - simulated/runtime gates passed | `RuntimeSessionResult.order_results` now carries `RuntimeOrderResult` evidence. `order_blocked_by_permission` includes reason, permission, and startup checklist hash. Direct `LiveRuntime.submit_order()` returns `DIRECT_ORDER_PATH_DISABLED` instead of submitting to the broker. | No real broker live order drill was run in this workspace. | `tests/unit/runtime/test_runtime_session.py::{test_runtime_session_permission_block_writes_runtime_order_result_evidence,test_runtime_session_paper_permission_does_not_permit_live_account_order}` and `tests/unit/runtime/test_live_runtime.py::test_live_runtime_direct_submit_path_is_disabled_when_running`. |
| M2-2 Live startup gate hard-fail matrix | Implemented - simulated/runtime gates passed | Startup checks use severity `BLOCKER`/`WARNING`/`INFO`; failed `BLOCKER` checks make checklist `passed=False`. `RuntimeSession.start()` emits startup gate evidence and enters degraded state instead of order-enabled live when startup is blocked. | Real event-sink and snapshot-store writability are represented by config gates; no external storage failure drill was run. | `tests/unit/runtime/test_live_startup_guard.py::test_startup_checklist_blocks_only_blocker_severity_failures` and startup session gate tests. |
| M2-3 Broker reconnect requires reconciliation before resume | Implemented - simulated/runtime gates passed | Reconnect uses `BrokerReconnectReconciliation` boundary, refreshes open orders/positions/executions/account summary, emits `runtime.reconciliation_passed` or `runtime.reconciliation_failed`, and stays degraded without a passing result. | Broker transport callbacks were simulated through the reconciliation boundary; no live IBKR reconnect drill was run. | `tests/unit/runtime/test_runtime_session.py::{test_runtime_session_reconnect_blocks_orders_until_reconciled,test_runtime_session_reconnect_requires_configured_reconciliation_boundary,test_runtime_session_reconnect_keeps_degraded_for_unresolved_callbacks}`. |
| M2-4 Market-data permission/freshness forced risk gate | Implemented - simulated/runtime gates passed | Live broker sessions wrap risk engines with mandatory `MarketDataPermissionRiskRule` and `MarketDataFreshnessRiskRule`; `MarketDataFlow.risk_context_for()` preserves permission and stale evidence. | High-risk delayed-data override and dual signoff remain intentionally unsupported for live capital. | `tests/unit/risk/test_market_data_permission.py::test_risk_engine_forces_market_data_permission_and_freshness_rules` and market-data runtime rejection tests. |
| M2-5 Kill switch / rollback drill | Implemented - simulated/runtime gates passed | Kill switch evidence now includes run ID and snapshot refs; rollback evidence includes run ID, active order IDs, event-store paths, and snapshot refs. Unauthorized deactivate raises `PermissionError`; market data and account snapshots continue after kill switch blocks orders. | No real broker cancel drill was run; integration coverage uses runtime actors and fake execution adapters. | `tests/integration/test_live_kill_switch_flow.py` kill switch, cancel-active-orders, rollback, observability, and unauthorized deactivate tests. |

## Parallel Execution Lanes

| Lane | Owner | Write Scope | Exit Evidence |
| --- | --- | --- | --- |
| A | Main agent | Matrix, integration, final review, commit. | This matrix updated with actual pass/fail evidence and verification commands. |
| B | Worker | Live permission and startup hard-fail gates. | Tests and implementation for M2-1/M2-2 without direct submit compatibility. |
| C | Worker | Broker disconnect/reconnect/reconciliation recovery. | Tests and implementation for M2-3 degraded/recover behavior and events. |
| D | Worker | Market-data risk and kill switch/rollback controls. | Tests and implementation for M2-4/M2-5 risk, evidence, and emergency controls. |

## Verification Plan

Run narrow tests first, then required repository gates:

```bash
uv run pytest tests/unit/runtime tests/unit/risk tests/integration/test_live_kill_switch_flow.py tests/integration/test_live_beta_flows.py tests/unit/test_architecture_baseline_smokes.py -q
make format
make lint
make guardrails
make typecheck
make test-unit
make test-integration
make check
```

If real IBKR/live broker evidence is not available in this workspace, M2 can only claim simulated/runtime safety coverage, not production broker drill completion.
