# QTS Runtime Post-Review Execution Status Matrix

> Source backlog: `docs/plan/qts_runtime_post_review_improvement_tasks.md`
> Review baseline: 2026-05-15 working tree review
> Purpose: convert the post-review backlog into executable, gate-driven work.

## Completion Rules

A task is `Complete` only when every acceptance condition in the source backlog has direct evidence from at least one of:

- a focused unit, integration, anchor, architecture, or regression test
- a strict guardrail rule that fails on violation
- generated inventory/import-graph evidence
- updated durable documentation for intentionally changed contracts
- fresh verification command output

Passing existing tests is not sufficient when a plan acceptance item has no gate.

## Current Summary

| Milestone | Status | Reason |
|---|---:|---|
| Milestone 1 - Names and boundaries | Complete | T00/T01/T02/T03/T04/T05/T06/T22/T25 are implemented with focused tests, refreshed inventory/import snapshots, architecture HTML checks, and guardrail coverage; T26 is enabled for the Milestone 1 warning/strict subset. |
| Milestone 2 - Broker runtime safety | Complete | T07/T08/T09/T10/T11/T12/T13/T24 are implemented with focused tests, refreshed architecture HTML/inventory/import snapshots, graph refresh, and `make check` verification. Dedicated execution matrix: `docs/plan/qts_runtime_m2_review_status_matrix.md`. |
| Milestone 3 - Multi-account, recovery, reporting | Complete | RuntimeEvent envelope, topology resolver, durable recovery evidence, account isolation, signal aggregation auditability, and shared reporting manifest contracts are implemented and covered by focused tests. Dedicated execution matrix: `docs/plan/qts_runtime_m3_review_status_matrix.md`. |
| Milestone 4 - Replay realism and reproducibility | Complete | Replay no-future/source-subscription contracts, replay anomaly runtime evidence, simulated execution assumptions, paper-simulated manifest parity, broker capability reject events, architecture snapshots, and final `make check` are complete. Dedicated execution matrix: `docs/plan/qts_runtime_m4_review_status_matrix.md`. |

## Task Matrix

| Task | Status | Evidence Found | Blocking Gaps | Next Gate |
|---|---:|---|---|---|
| T00 baseline and protection net | Complete | Inventory/import graph tools and before/after snapshots exist; smoke tests are covered by `make test-unit` in CI. | None for Milestone 1. | Keep snapshots refreshed after later architecture changes. |
| T01 fake/placeholder/beta cleanup | Complete | Fakes live under `qts.testing.fakes`; `ProductionNoFakeClassRule`, placeholder/runtime wording rules, and architecture HTML checks pass. | None. | Keep fake/simulated boundary checks active. |
| T02 RuntimeSession rename | Complete | Canonical `qts.runtime.session`, `dependencies`, `state`, and `safety` modules exist; `live_runtime_session` and `live_runtime_dependencies` were removed. | None. | `RemovedImportNoNewUsageRule` rejects reintroducing removed paths. |
| T03 RuntimeMode vs live order permission | Complete | `RuntimeMode.LIVE_OBSERVATION` and `qts.runtime.permissions.LiveOrderPermission` exist; startup decisions expose `order_permission`; session order gate rejects `OBSERVATION_ONLY`. | None. | Keep permission/runtime-mode naming tests active. |
| T04 paper broker vs paper simulated config | Complete | `PaperBrokerRuntimeConfig`, `PaperSimulatedRuntimeConfig`, `configs/paper_broker.yaml`, and `configs/paper_simulated.yaml` are covered by acceptance tests; `PaperRuntimeConfig` was removed. | None. | Keep mode-specific config tests active. |
| T05 shared market-data contracts out of `qts.data.live` | Complete | Shared contracts are canonical in `qts.data.interfaces`, `events`, `capabilities`, and `subscriptions`; `qts.data.live` only exposes live utilities such as reconnect policy. | None. | Guardrails reject shared contract definitions under `qts.data.live`. |
| T06 fake vs simulated boundary | Complete | Production fake classes are rejected outside `qts.testing`; production imports from `qts.testing` are rejected; test-only callers use `FakeStreamingMarketDataAdapter`. | None. | Keep fake/simulated import guardrails active. |
| T07 data transport migration | Complete | Canonical data transports live in `qts.data.transports`; removed adapter transport paths are blocked by guardrails. | None. | Continue with T10/T11 transport internals. |
| T08 execution transport migration | Complete | Canonical execution transports and `IbkrOrderIdAllocator` live in `qts.execution.transports`; removed adapter paths are blocked by guardrails. | None. | Continue with T10 order transport split. |
| T09 RuntimeSession coordinator split | Complete | `RuntimeSession` delegates market-data, broker lifecycle, safety, rollback, and recovery to dedicated coordinators; method-surface and coordinator tests pass; architecture HTML and snapshots were refreshed. | Event writing remains centralized on the session facade for shared envelope sequencing. | Continue with T12/T13 safety gates on top of `RuntimeSafetyController`. |
| T10 IBKR order transport split | Complete | `IbkrTwsOrderExecutionTransport` is a facade over `IbkrTwsConnection`, `IbkrTwsOrderClient`, `IbkrTwsReconciliationClient`, `IbkrTwsCallbackDispatcher`, and `IbkrTwsExecutionEventEmitter`; component and facade tests pass. | None for T10 split. T11 still owns callback quarantine/idempotency hardening. | Continue with T11 composite idempotency and quarantine tests. |
| T11 IBKR callback idempotency/quarantine | Complete | `BrokerCallbackQuarantine` exists; duplicate status/execution/commission callbacks are idempotent; composite execution key covers account/broker order/execution id; execution-before-openOrder can resolve; wrong-account execution is quarantined; unresolved callbacks block new order requests. | Broader reconnect command semantics move to T13/T24. | Continue with RuntimeSession coordinator split and startup/reconnect gates. |
| T12 market-data permission/freshness risk gate | Complete | `MarketDataRiskContext`, market-data permission/freshness risk rules, RiskDecision evidence, runtime risk-rejection events, and risk-rule registry wiring are implemented and tested. | Runtime source events still degrade the session before subsequent orders, by design. | Continue with startup/reconnect safety gates. |
| T13 broker runtime startup gate enforcement | Complete | Canonical broker-runtime startup classes exist; `BrokerRuntimeStartupGate` is wired into `RuntimeSafetyController`; live and paper-broker order paths fail closed without startup decisions; startup/reconnect evidence tests pass. | Reconnect resume command authorization remains in T24. | Continue with runtime command permission/audit/idempotency. |
| T14 replay no-future contract tests | Complete | Replay sequencer/source tests cover visible-at, active subscribe, mid-run subscribe, unsubscribe delivery-stop, deterministic same-timestamp ordering, duplicate drop, gap diagnostics, out-of-order rejection, anomaly runtime-event sink evidence, and replay report determinism. | None. | Keep replay determinism in M4 focused checks because it is outside default unit/integration/anchor targets. |
| T15 simulated execution assumptions manifest | Complete | Backtest and paper-simulated manifests include complete `execution_assumptions`; fill models and broker capabilities expose manifest payloads; simulated capability rejects emit canonical runtime artifacts without fills/account mutation. | None. | Keep manifest and capability reject tests with reporting/backtest actor suites. |
| T16 RuntimeEvent envelope contract | Complete | `RuntimeEvent.require_canonical_envelope`, backtest/live sinks, and `FileEventStore` enforce and replay canonical runtime envelopes with `run_id`, `runtime_mode`, `sequence_no`, `event_id`, and schema version. | None for M3. | Maintain sink/store contract tests when adding event kinds. |
| T17 topology builder unification | Complete | `BrokerRuntimeTopologyResolver`, `ResolvedRuntimeTopology`, and `StrategyRuntimeBinding` are public boundaries under `qts.runtime.broker_runtime_topology`; `RuntimeSession` uses the public resolver; architecture smoke tests reject private builder classes. | None. | Keep topology resolver tests active. |
| T18 durable event/snapshot recovery | Complete | `FileEventStore` fsyncs canonical events; `FileSnapshotStore` uses temp-file atomic replace and ignores trailing partial records; snapshot metadata and recovery decision manifest/runtime-event payloads are tested. | Full broker reconciliation remains owned by existing recovery gate flow. | Keep gap/block/reconciliation evidence tests in the recovery suite. |
| T19 multi-account runtime isolation | Complete | Fill/cancel/account route tests, account-scoped risk topology tests, wrong-account callback quarantine, and route metadata snapshot/restore coverage are in place. | None for M3. | Add broader integration coverage as new broker callback flows are introduced. |
| T20 signal aggregation audit loop | Complete | `AggregatedSignalBatch` carries account/instrument/correlation/conflict/decision-id metadata; `RiskDecision`, `OrderPlan`, and `OrderRouteMetadata` reference aggregation decisions; runtime signal/order events include audit linkage. | None for M3. | Extend ledger/report views when adding user-facing strategy contribution reports. |
| T21 reporting base contract and manifest completeness | Complete | `ReportWriter` and `RuntimeArtifactWriter` are protocols; `RuntimeManifest` validates shared live/backtest manifest fields; backtest/live manifests include schema, topology, config, created, and finalized fields. | None for M3. | Keep manifest anchor tests updated when artifact schema evolves. |
| T22 config path unification | Complete | `qts.runtime.config` is a package with canonical mode-specific modules; `PaperBrokerRuntimeConfig`/`PaperSimulatedRuntimeConfig` are exported from `qts.runtime.config.paper` and package `__init__`. | None for Milestone 1. | Later work can introduce stricter import-style checks if needed. |
| T23 StartRuntime command unification | Complete | `qts.application.commands.start_runtime.StartRuntimeCommand` carries `runtime_mode`, `config_ref`, `operator_id`, `idempotency_key`, and `reason`; required start modes are covered; live order enablement requires startup decision evidence. | None. | `RemovedImportNoNewUsageRule` rejects reintroducing `start_paper`. |
| T24 runtime command permission/audit/idempotency | Complete | `RuntimeCommand` carries operator role/scope, requested/approved metadata, reason codes, scoped idempotency, dual-control live enablement checks, reconnect-resume reconciliation checks, and audit event payloads; application/API DTOs expose command result reason codes. Focused runtime/application/API tests and final `make check` pass. | None for T24. | Continue with Milestone 3 backlog. |
| T25 docs, inventory, architecture snapshot | Complete | `docs/architecture/backtest_live_parallel_sequence.html` is updated for M1 canonical names; HTML sync tests pass; after inventory/import graph snapshots were regenerated. | Transport path documentation remains a Milestone 2 concern. | Refresh again after transport migration. |
| T26 CI architecture guardrail strict mode | Complete | `make guardrails` is in CI and passes; default suite rejects production fake classes, production `qts.testing` imports, removed imports, shared contracts under `qts.data.live`, and transport classes under adapter paths. | None. | Keep strict guardrails in `make check`. |

## Milestone 1 Execution Order

Milestone 1 should be completed before runtime safety work. The goal is to stabilize names, paths, and automated boundaries so later changes do not chase moving targets.

1. **M1-G1 guardrail gap tests**
   - Status: `Complete` on 2026-05-15.
   - Evidence:
     - Added focused tests for shared contracts in `qts.data.live`, transport classes under adapters, removed import usage, production `qts.testing` imports, and fake classes outside `qts.testing`.
     - Added corresponding rule classes in `qts.quality.guardrails`.
     - Fixed targeted `GuardrailSuite(rules=...)` execution so single-rule tests actually exercise the supplied rule list.
   - Add failing tests under `tests/unit/scripts/test_verify_guardrails.py` for:
     - `DataLiveNoSharedContractRule`
     - `TransportCanonicalPathRule`
     - `RemovedImportNoNewUsageRule`
     - production no-fake outside `qts.testing`
     - production no `qts.testing` imports
   - Verification command: `uv run pytest tests/unit/scripts/test_verify_guardrails.py -q`
   - Observed result: `44 passed`.

2. **M1-G2 shared data/fake boundary**
   - Status: `Complete` on 2026-05-15.
   - Evidence:
     - `DataLiveNoSharedContractRule` is now in the default guardrail suite.
     - Shared market-data contracts are canonical outside `qts.data.live`.
     - Production `qts.testing` imports are rejected by the default guardrail suite.
     - Focused data boundary tests pass.
   - Complete T01, T05, and T06 after G1 fails correctly.
   - Canonical shared contracts must live outside `qts.data.live`.
   - Removed live contract paths are rejected by guardrails.
   - Verification commands:
     - `uv run pytest tests/unit/data tests/unit/scripts/test_verify_guardrails.py -q`
     - `make guardrails`

3. **M1-G3 runtime canonical rename**
   - Status: `Complete` on 2026-05-15.
   - Evidence:
     - Added `qts.runtime.session`, `qts.runtime.dependencies`, `qts.runtime.state`, `qts.runtime.safety`, and `qts.runtime.permissions`.
     - Removed runtime module names are blocked by guardrails.
     - `RuntimeMode.LIVE_OBSERVATION` and `LiveOrderPermission` are covered by startup/session tests.
   - Complete T02 and T03 together because session state and live order permission share imports.
   - New canonical modules:
     - `qts.runtime.session`
     - `qts.runtime.dependencies`
     - `qts.runtime.state`
     - `qts.runtime.safety`
     - `qts.runtime.permissions`
   - Removed modules must not be reintroduced.
   - Verification commands:
     - `uv run pytest tests/unit/runtime tests/integration/test_live_kill_switch_flow.py -q`
     - `rg -n "from qts\\.runtime\\.live_runtime_session|from qts\\.runtime\\.live import LivePermissionMode" backend/src/qts tests`

4. **M1-G4 paper broker/simulated config split**
   - Status: `Complete` on 2026-05-15.
   - Evidence:
     - Added `PaperBrokerRuntimeConfig` and `PaperSimulatedRuntimeConfig`.
     - Added `configs/paper_broker.yaml` and `configs/paper_simulated.yaml`.
     - Acceptance tests assert broker/simulated environments, account kind, and default port semantics.
   - Complete T04 after T03.
   - Add config samples:
     - `configs/paper_broker.yaml`
     - `configs/paper_simulated.yaml`
   - Verification commands:
     - `uv run pytest tests/unit/runtime/test_live_startup_guard.py tests/unit/runtime/test_runtime_evolution_plan_acceptance.py -q`
     - `rg -n "paper without real broker credentials|PaperBrokerRuntimeConfig|PaperSimulatedRuntimeConfig" backend/src/qts/application backend/src/qts/runtime docs`

5. **M1-G5 config/docs/inventory closure**
   - Status: `Complete` on 2026-05-15.
   - Evidence:
     - Regenerated `tests/architecture/snapshots/class_inventory_after_post_review.json`.
     - Regenerated `tests/architecture/snapshots/import_graph_after_post_review.json`.
     - Updated architecture HTML and verified with `tests/unit/test_backtest_live_parallel_sequence_html.py`.
   - Complete T22 and T25.
   - Regenerate class inventory/import graph after canonical renames.
   - Update architecture HTML only after code paths are stable.
   - Verification commands:
     - `uv run pytest tests/unit/test_architecture_baseline_smokes.py tests/unit/test_backtest_live_parallel_sequence_html.py -q`
     - `python tools/architecture/export_inventory.py --source backend/src --output /tmp/qts_class_inventory.json`
     - `python tools/architecture/export_import_graph.py --source backend/src --output /tmp/qts_import_graph.json`

6. **M1-G6 strict guardrail subset**
   - Status: `Complete for M1` on 2026-05-15.
   - Complete the Milestone 1 portion of T26.
   - `make guardrails` must fail on newly introduced:
     - production `Fake*`
     - shared contracts under `qts.data.live`
     - removed import paths
   - Transport class path enforcement is strict after T07/T08 moved the transport classes.
   - Verification commands:
     - `make guardrails`
     - `make lint`
     - `make typecheck`
     - `make test-unit`

## Codex Execution Protocol

For each gate above:

1. Start with a clean checkpoint or clearly documented dirty baseline.
2. Write the failing test or guardrail first.
3. Run the narrow command and confirm the failure is the intended failure.
4. Implement the smallest code change that satisfies the gate.
5. Run the narrow command again and confirm it passes.
6. Run `make guardrails` after every architecture-boundary change.
7. Update inventory/docs only after code and guardrails pass.
8. Record evidence in this matrix by changing the task row from `Partial` or `Not started` to `Complete`.

## Verification Commands Used For This Matrix

```bash
make guardrails
uv run pytest tests/unit/runtime/test_runtime_evolution_plan_named_gates.py tests/unit/data/test_replay_market_data_source.py tests/unit/reporting/test_live_report_writer.py tests/unit/backtest/test_backtest_streaming_sink.py
```

Observed result during review:

- `make guardrails`: passed
- selected tests: `74 passed`

These results prove only the current implemented gates pass. They do not prove the full backlog is complete.
