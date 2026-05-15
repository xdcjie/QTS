# QTS Runtime M2 Review Status Matrix

> Source backlog: `docs/plan/qts_runtime_post_review_improvement_tasks.md`
> Scope: Milestone 2 - Broker runtime safety
> M2 task set: T07, T08, T09, T10, T11, T12, T13, T24
> Baseline date: 2026-05-15
> Baseline verification: `make check` passed after M1 closure.

## Completion Rules

A Milestone 2 task is `Complete` only when every acceptance condition has at least one hard gate:

- focused unit, integration, anchor, or architecture test
- strict guardrail rule that fails on violation
- generated inventory/import graph evidence
- runtime event/audit evidence for safety-sensitive behavior
- fresh verification command output

Passing broad tests is not enough if the specific M2 safety rule has no failing test or guardrail.

## M2 Correctness Invariants

| Invariant | Correct Owner / Boundary | Forbidden Shortcut | Required Gate |
|---|---|---|---|
| Transport owns socket/SDK lifecycle; adapter owns provider-to-domain mapping. | `qts.data.transports`, `qts.execution.transports`; adapters remain under `qts.*.adapters`. | Leaving canonical `*Transport` classes in adapters and only renaming imports. | Inventory/import tests plus `TransportCanonicalPathRule` default enforcement after T07/T08. |
| RuntimeSession is a thin orchestrator. | `RuntimeMarketDataCoordinator`, `RuntimeBrokerLifecycleCoordinator`, `RuntimeSafetyController`, `RuntimeRollbackCoordinator`. | Moving code without reducing `RuntimeSession` responsibility. | Class/method-surface test and coordinator behavior tests. |
| IBKR callbacks are idempotent and quarantined until resolvable. | IBKR callback dispatcher/quarantine/order map boundaries. | Dropping unknown callbacks silently or relying only on fill id string. | Duplicate/out-of-order/wrong-account callback tests with runtime event evidence. |
| Market-data permission and freshness block unsafe live orders. | `RiskEngine` via explicit market-data context and risk rules. | Degrading runtime only through events while still allowing order submission. | Risk rejection tests for delayed/frozen/stale/unavailable data. |
| Broker startup checklist is an enforced order gate. | Broker runtime startup decision plus safety controller. | Writing checklist only to manifest while paper/live broker orders continue. | Paper broker and live order-path tests for each blocking checklist item. |
| Runtime commands are authorized, auditable, and scoped-idempotent. | `RuntimeCommand`, `RuntimeCommandBus`, application/API command boundaries. | Idempotency keyed only by command type + idempotency key; no operator scope. | Duplicate scope, authorization, audit event, and reconnect-resume rejection tests. |

## Current Summary

| Area | Status | Review Finding |
|---|---:|---|
| M2 overall | Complete | T07/T08/T09/T10/T11/T12/T13/T24 are implemented; architecture HTML/inventory/import snapshots are refreshed; `make check` passes. |
| Transport paths | Complete for T07/T08 | Canonical transport classes now live under `qts.data.transports` and `qts.execution.transports`; old adapter paths are compatibility shims. |
| RuntimeSession split | Complete | `RuntimeSession` delegates market-data, broker lifecycle, safety, rollback, and recovery to dedicated coordinators. |
| IBKR callback safety | Complete | `BrokerCallbackQuarantine` covers unresolved callbacks; duplicate, out-of-order, and wrong-account callbacks are gated by focused tests. |
| Market-data risk gate | Complete | `OrderRiskRequest` carries `MarketDataRiskContext`; risk rules reject unsafe permission/freshness contexts and emit evidence. |
| Startup enforcement | Complete | Canonical broker-runtime startup names and `BrokerRuntimeStartupGate` block live/paper-broker orders without valid startup decisions. |
| Runtime command safety | Complete | `RuntimeCommand` carries role/scope/approval/reason metadata, scoped idempotency, dual-control live enablement, audit events, and reconnect-resume reconciliation checks. |

## Task Matrix

| Task | Status | Evidence Found | Blocking Gaps | First Required Red Gate |
|---|---:|---|---|---|
| T07 data transport migration | Complete | `test_transport_canonical_modules_are_under_transports`, `test_transport_adapter_paths_are_compatibility_shims`, data transport unit tests, and `make guardrails` pass. | None for canonical path migration. | Complete: architecture test asserts data transport modules are under `qts.data.transports`; default guardrail rejects adapter `*Transport` definitions. |
| T08 execution transport migration | Complete | `test_transport_canonical_modules_are_under_transports`, `test_transport_adapter_paths_are_compatibility_shims`, execution transport/order-id unit tests, and `make guardrails` pass. | None for canonical path migration. | Complete: architecture test asserts execution transport modules are under `qts.execution.transports`; adapter paths are classless compatibility shims. |
| T09 RuntimeSession coordinator split | Complete | `RuntimeMarketDataCoordinator`, `RuntimeBrokerLifecycleCoordinator`, `RuntimeSafetyController`, `RuntimeRollbackCoordinator`, and `RuntimeRecoveryCoordinator` exist; `RuntimeSession` public market-data, broker lifecycle, kill-switch, rollback, and recovery entrypoints delegate; focused runtime/integration tests, architecture HTML smoke, and `make guardrails` pass. | Event envelope writing remains on `RuntimeSession` as shared facade plumbing for all coordinators. | Complete: method-surface tests assert delegation and public surface <= 15; coordinator behavior tests cover subscribed/unsubscribed bars and safety reason codes. |
| T10 IBKR order transport split | Complete | `IbkrTwsConnection`, `IbkrTwsOrderClient`, `IbkrTwsReconciliationClient`, `IbkrTwsCallbackDispatcher`, and `IbkrTwsExecutionEventEmitter` exist under `qts.execution.transports`; facade delegation and component unit tests pass; IBKR paper flow passes. | None for T10 split. T11 still owns deeper quarantine/idempotency semantics. | Complete: inventory/module test, facade delegation test, dispatcher/order-client/reconciliation unit tests, and T10 execution tests pass. |
| T11 IBKR callback idempotency/quarantine | Complete | `BrokerCallbackQuarantine` owns unresolved callbacks; duplicate orderStatus is dropped; execution idempotency uses account/broker-order/execution identity; execution-before-openOrder resolves after mapping; wrong-account execution is quarantined; unresolved callbacks block new order requests. | Runtime sink publication is still represented as adapter callback audit events; broader reconnect orchestration is covered by T13/T24 gates. | Complete for adapter/transport safety: `test_ibkr_order_execution_adapter.py`, `test_ibkr_order_execution_transport.py`, `test_live_execution_report_flow.py` pass. |
| T12 market-data permission/freshness risk gate | Complete | `MarketDataRiskContext` is carried on `OrderRiskRequest`; `RiskDecision` has evidence payloads; `MarketDataPermissionRiskRule` and `MarketDataFreshnessRiskRule` reject delayed/frozen/unavailable/unknown/stale contexts; `MarketDataFlow` exposes latest risk context; runtime writes `runtime.risk_rejected` with evidence; registry can build both rules. | Runtime still also degrades on provider permission/stale source events, preserving the existing fail-closed behavior. | Complete: risk rule tests cover delayed/frozen/unavailable/unknown/stale reason codes and evidence; runtime test asserts risk rejection event evidence. |
| T13 broker runtime startup gate enforcement | Complete | Canonical `BrokerRuntimeStartupCheck`, `BrokerRuntimeStartupChecklist`, `BrokerRuntimeStartupDecision`, and `BrokerRuntimeStartupDecisionStatus` exist with `LiveStartup*` compatibility aliases; `BrokerRuntimeStartupGate` blocks `LIVE` and `PAPER_BROKER` order submission without startup decisions; checklist evidence/remediation and reconnect reconciliation gates are covered by runtime/startup tests. | Reconnect command authorization is covered by T24 runtime command safety. | Complete: canonical type test, paper-broker startup-decision order-path test, startup checklist evidence tests, reconnect blocking test, and focused T13 suite pass. |
| T24 runtime command permission/audit/idempotency | Complete | `RuntimeCommand` has `operator_role`, `authorization_scope`, `reason_code`, `idempotency_scope`, `requested_at`, `approved_by`, and `approval_required`; idempotency is scoped by runtime/operator/type/key; kill-switch deactivation requires safety scope; live enablement requires a distinct approver; pause/resume/kill-switch/reconcile/snapshot commands emit audit events; resume after reconnect without reconciliation is rejected. | None for T24. | Complete: runtime/application/API command tests pass. |

## Dependency Order

| Gate | Tasks | Why This Order |
|---|---|---|
| M2-G1 transport canonical paths | T07, T08 | T10 should split execution transport after canonical modules exist. This also lets `TransportCanonicalPathRule` become default. |
| M2-G2 IBKR order transport split | T10 | Dispatcher/emitter/client boundaries are needed before robust callback quarantine implementation. |
| M2-G3 callback idempotency/quarantine | T11 | Depends on clean callback ownership; must protect account/order state before runtime safety gates rely on broker callbacks. |
| M2-G4 RuntimeSession coordinator split | T09 | Should happen before deeper startup/reconnect behavior so new safety logic goes into the right owner. |
| M2-G5 market-data risk gate | T12 | Can proceed after/alongside T09; must update risk request/decision contracts and runtime event evidence. |
| M2-G6 startup gate enforcement | T13 | Builds on M1 permission split and T09 safety controller. Paper broker/live orders must fail closed. |
| M2-G7 runtime command security | T24 | Can run after T13 so resume/live enablement semantics use the enforced startup/reconnect model. |
| M2-G8 docs/snapshots/final guardrails | T07-T13, T24 | Regenerate architecture docs and snapshots only after code paths are stable. |

## Execution Gates

### M2-G1 - Transport Canonical Paths

**Goal:** Move data/execution transport canonical classes out of adapters.

**Files to touch:**

- Create: `backend/src/qts/data/transports/__init__.py`
- Create: `backend/src/qts/data/transports/ibkr_tws_market_data_transport.py`
- Create: `backend/src/qts/data/transports/ib_async_market_data_transport.py`
- Create: `backend/src/qts/execution/transports/__init__.py`
- Create: `backend/src/qts/execution/transports/ibkr_tws_order_execution_transport.py`
- Create: `backend/src/qts/execution/transports/ib_async_order_execution_transport.py`
- Modify: `backend/src/qts/data/adapters/ibkr_transport.py`
- Modify: `backend/src/qts/data/adapters/ibkr_async_transport.py`
- Modify: `backend/src/qts/execution/adapters/ibkr_transport.py`
- Modify: `backend/src/qts/execution/adapters/ibkr_async_transport.py`
- Modify: `backend/src/qts/quality/guardrails.py`
- Test: `tests/unit/scripts/test_verify_guardrails.py`
- Test: `tests/unit/data/test_ibkr_market_data_transport.py`
- Test: `tests/unit/data/test_ibkr_async_market_data_transport.py`
- Test: `tests/unit/execution/test_ibkr_order_execution_transport.py`
- Test: `tests/unit/execution/test_ibkr_async_order_execution_transport.py`

**Required first tests:**

- `test_transport_canonical_modules_are_under_transports`
- `test_default_guardrails_reject_transport_classes_under_adapters_after_migration`
- compatibility import tests for old adapter paths.

**Verification:**

```bash
uv run pytest tests/unit/scripts/test_verify_guardrails.py \
  tests/unit/data/test_ibkr_market_data_transport.py \
  tests/unit/data/test_ibkr_async_market_data_transport.py \
  tests/unit/execution/test_ibkr_order_execution_transport.py \
  tests/unit/execution/test_ibkr_async_order_execution_transport.py -q
make guardrails
```

### M2-G2 - IBKR Order Transport Split

**Goal:** Keep `IbkrTwsOrderExecutionTransport` as facade and move responsibilities into small owners.

**Files to touch:**

- Create: `backend/src/qts/execution/transports/ibkr_tws_connection.py`
- Create: `backend/src/qts/execution/transports/ibkr_tws_order_client.py`
- Create: `backend/src/qts/execution/transports/ibkr_tws_reconciliation_client.py`
- Create: `backend/src/qts/execution/transports/ibkr_tws_callback_dispatcher.py`
- Create: `backend/src/qts/execution/transports/ibkr_tws_execution_event_emitter.py`
- Modify: `backend/src/qts/execution/transports/ibkr_tws_order_execution_transport.py`
- Test: `tests/unit/execution/test_ibkr_order_execution_transport.py`

**Required first tests:**

- facade has no direct `handle_*` implementation beyond delegation
- dispatcher unit test handles `orderStatus`, `openOrder`, `execution`, `commission`, and error callbacks
- order client unit test builds submit/cancel payloads without dispatcher state
- reconciliation client unit test issues open-order/position/account/execution requests.

**Verification:**

```bash
uv run pytest tests/unit/execution/test_ibkr_order_execution_transport.py \
  tests/unit/execution/test_ibkr_order_execution_adapter.py \
  tests/integration/test_ibkr_paper_flow.py -q
```

### M2-G3 - IBKR Callback Quarantine

**Goal:** Duplicate/out-of-order/wrong-account callbacks cannot mutate local order/account state incorrectly.

**Files to touch:**

- Create: `backend/src/qts/execution/adapters/broker_callback_quarantine.py`
- Modify: `backend/src/qts/execution/adapters/ibkr_order_map.py`
- Modify: `backend/src/qts/execution/adapters/ibkr_order_execution.py`
- Modify: `backend/src/qts/execution/transports/ibkr_tws_callback_dispatcher.py`
- Test: `tests/unit/execution/test_ibkr_order_map.py`
- Test: `tests/unit/execution/test_ibkr_order_execution_adapter.py`
- Test: `tests/unit/execution/test_ibkr_order_execution_transport.py`

**Required first tests:**

- duplicate execution with same account/instrument/broker execution id is applied once
- same broker execution id on a different account is not treated as the same fill
- execution before openOrder is quarantined and later resolved when mapping arrives
- wrong-account callback produces quarantine event and does not update local account
- reconnect with pending unresolved callbacks blocks new orders until reconciliation resolves.

**Verification:**

```bash
uv run pytest tests/unit/execution/test_ibkr_order_map.py \
  tests/unit/execution/test_ibkr_order_execution_adapter.py \
  tests/unit/execution/test_ibkr_order_execution_transport.py \
  tests/integration/test_live_execution_report_flow.py -q
```

### M2-G4 - RuntimeSession Coordinator Split

**Goal:** `RuntimeSession` delegates market-data, broker lifecycle, safety, rollback, and recovery responsibilities.

**Files to touch:**

- Create: `backend/src/qts/runtime/market_data_coordinator.py`
- Create: `backend/src/qts/runtime/broker_lifecycle.py`
- Create: `backend/src/qts/runtime/safety_controller.py`
- Create: `backend/src/qts/runtime/rollback.py`
- Create: `backend/src/qts/runtime/recovery.py`
- Modify: `backend/src/qts/runtime/session.py`
- Test: `tests/unit/runtime/test_live_runtime_session.py`
- Test: `tests/unit/runtime/test_runtime_market_data_coordinator.py`
- Test: `tests/unit/runtime/test_runtime_safety_controller.py`

**Required first tests:**

- `RuntimeMarketDataCoordinator` returns the same `RuntimeSessionResult` for subscribed/unsubscribed bars as current session behavior
- `RuntimeSafetyController` blocks paused/degraded/not-running/kill-switch/observation-only states with existing reason codes
- architecture test asserts `RuntimeSession` no longer directly owns the full `on_market_data` implementation.

**Verification:**

```bash
uv run pytest tests/unit/runtime/test_live_runtime_session.py \
  tests/unit/runtime/test_runtime_market_data_coordinator.py \
  tests/unit/runtime/test_runtime_safety_controller.py \
  tests/integration/test_paper_runtime_full_chain.py \
  tests/integration/test_live_kill_switch_flow.py -q
```

### M2-G5 - Market-Data Risk Gate

**Goal:** Market-data permission/freshness becomes a risk input, not only runtime degradation.

**Files to touch:**

- Create: `backend/src/qts/domain/risk/market_data_context.py`
- Create: `backend/src/qts/risk/rules/market_data_permission.py`
- Create: `backend/src/qts/risk/rules/market_data_freshness.py`
- Modify: `backend/src/qts/domain/risk/request.py`
- Modify: `backend/src/qts/domain/risk/decision.py`
- Modify: `backend/src/qts/runtime/intent_processing.py`
- Modify: `backend/src/qts/runtime/market_data_flow.py`
- Test: `tests/unit/risk/test_market_data_permission.py`
- Test: `tests/unit/runtime/test_live_runtime_session.py`

**Required first tests:**

- LIVE delayed data rejects with `MARKET_DATA_DELAYED_FOR_LIVE_ORDER`
- LIVE frozen data rejects with `MARKET_DATA_FROZEN_FOR_LIVE_ORDER`
- stale data rejects with `MARKET_DATA_STALE`
- unavailable/unknown permission rejects with `MARKET_DATA_UNAVAILABLE` or `MARKET_DATA_PERMISSION_UNKNOWN`
- `RiskDecision` contains market-data evidence payload and runtime event records reason code.

**Verification:**

```bash
uv run pytest tests/unit/risk/test_market_data_permission.py \
  tests/unit/runtime/test_live_runtime_session.py \
  tests/unit/runtime/test_market_data_flow.py -q
make guardrails
```

### M2-G6 - Broker Startup Gate Enforcement

**Goal:** Broker startup checklist blocks paper broker and live order submission until safety evidence is valid.

**Files to touch:**

- Create: `backend/src/qts/runtime/startup_gate.py`
- Modify: `backend/src/qts/runtime/live.py`
- Modify: `backend/src/qts/runtime/safety_controller.py`
- Modify: `backend/src/qts/runtime/dependencies.py`
- Test: `tests/unit/runtime/test_live_startup_guard.py`
- Test: `tests/unit/runtime/test_live_runtime_session.py`

**Required first tests:**

- missing operator signoff blocks live orders
- reconciliation drift blocks live and paper-broker orders
- event sink not writable blocks live and paper-broker orders
- snapshot store not writable blocks live and paper-broker orders
- reconnect downgrades broker runtime to observation/block until reconciliation passes
- checklist failure includes `check_name`, `status`, `severity`, `evidence`, and `remediation`.

**Verification:**

```bash
uv run pytest tests/unit/runtime/test_live_startup_guard.py \
  tests/unit/runtime/test_live_runtime_session.py \
  tests/integration/test_live_kill_switch_flow.py -q
```

### M2-G7 - Runtime Command Permission, Audit, Idempotency

**Goal:** Runtime commands carry operator authorization and scoped idempotency, and write audit events.

**Files to touch:**

- Modify: `backend/src/qts/runtime/commands.py`
- Modify: `backend/src/qts/application/services/operations.py`
- Modify: `backend/src/qts/application/dto/operations.py`
- Modify: `backend/src/qts/api/schemas/operations.py`
- Test: `tests/unit/runtime/test_runtime_commands.py`
- Test: `tests/unit/application/test_services.py`
- Test: `tests/unit/api/test_operational_api_models.py`

**Required first tests:**

- duplicate command with same `runtime_instance_id`, `operator_id`, `command_type`, and `idempotency_key` returns same result
- same key with different operator/runtime scope is not treated as duplicate
- kill-switch deactivate without elevated scope is rejected
- live order enablement without `approved_by` is rejected
- pause/resume/kill-switch/reconcile/snapshot emit audit events
- resume after reconnect without reconciliation is rejected.

**Verification:**

```bash
uv run pytest tests/unit/runtime/test_runtime_commands.py \
  tests/unit/application/test_services.py \
  tests/unit/api/test_operational_api_models.py -q
```

### M2-G8 - Final M2 Closure

**Goal:** Turn M2 safety architecture into durable gates and refreshed docs.

**Files to touch:**

- Modify: `backend/src/qts/quality/guardrails.py`
- Modify: `docs/architecture/backtest_live_parallel_sequence.html`
- Modify: `tests/architecture/snapshots/class_inventory_after_post_review.json`
- Modify: `tests/architecture/snapshots/import_graph_after_post_review.json`
- Modify: `docs/plan/qts_runtime_post_review_status_matrix.md`
- Modify: `docs/plan/qts_runtime_m2_review_status_matrix.md`

**Required first tests:**

- architecture HTML no longer lists transport canonical classes under adapters
- after inventory shows transport classes under `qts.data.transports` and `qts.execution.transports`
- default guardrail rejects new `*Transport` classes under adapters
- status matrices list M2 tasks as complete only after focused gates pass.

**Verification:**

```bash
uv run pytest tests/unit/test_backtest_live_parallel_sequence_html.py \
  tests/unit/test_architecture_baseline_smokes.py \
  tests/unit/scripts/test_verify_guardrails.py -q
uv run python tools/architecture/export_inventory.py --source backend/src --output tests/architecture/snapshots/class_inventory_after_post_review.json
uv run python tools/architecture/export_import_graph.py --source backend/src --output tests/architecture/snapshots/import_graph_after_post_review.json
make check
```

## M2 No-Go Criteria

Do not mark M2 complete if any of these remain true:

- canonical `*Transport` classes still live under `qts.data.adapters` or `qts.execution.adapters`
- `TransportCanonicalPathRule` is not in the default guardrail suite after T07/T08
- `RuntimeSession` still owns full market-data processing and safety/rollback logic directly
- market-data permission/freshness can degrade runtime but cannot reject through `RiskEngine`
- paper broker can submit orders without a valid broker startup decision
- duplicate/out-of-order IBKR callbacks lack quarantine/resolve runtime events

## M2 Baseline Verification

Commands already passed before opening M2:

```bash
make check
```

Observed result:

- `ruff format`: passed
- `ruff check`: passed
- `make guardrails`: passed
- `mypy backend tests`: passed
- unit: `602 passed, 1 warning`
- integration: `58 passed, 4 skipped`
- anchor: `39 passed, 1 skipped`

This is only the M1-closed baseline. It does not prove any M2 task is complete.

## M2 Final Verification

Commands passed after T07/T08/T09/T10/T11/T12/T13/T24 and final snapshot refresh:

```bash
uv run pytest tests/unit/test_backtest_live_parallel_sequence_html.py \
  tests/unit/test_architecture_baseline_smokes.py \
  tests/unit/scripts/test_verify_guardrails.py -q
make check
```

Observed result:

- architecture/guardrail closure tests: `59 passed`
- `ruff format`: `493 files left unchanged`
- `ruff check`: passed
- `scripts/verify_guardrails.py`: passed
- `mypy backend tests`: passed
- unit: `646 passed, 1 warning`
- integration: `58 passed, 4 skipped`
- anchor: `39 passed, 1 skipped`
