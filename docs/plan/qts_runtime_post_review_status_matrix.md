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
| Milestone 3 - Multi-account, recovery, reporting | Partial | Some account isolation, signal aggregation, and event envelope work exists, but topology unification, durable recovery, and reporting contracts are incomplete. |
| Milestone 4 - Replay realism and reproducibility | Partial | Replay no-future tests are partially present, but simulated execution assumptions are not fully manifest-backed. |

## Task Matrix

| Task | Status | Evidence Found | Blocking Gaps | Next Gate |
|---|---:|---|---|---|
| T00 baseline and protection net | Complete | Inventory/import graph tools and before/after snapshots exist; smoke tests are covered by `make test-unit` in CI. | None for Milestone 1. | Keep snapshots refreshed after later architecture changes. |
| T01 fake/placeholder/beta cleanup | Complete | Fakes live under `qts.testing.fakes`; `ProductionNoFakeClassRule`, placeholder/runtime wording rules, and architecture HTML checks pass. | None for Milestone 1. | Future cleanup can remove compatibility fake aliases after release window. |
| T02 RuntimeSession rename | Complete | Canonical `qts.runtime.session`, `dependencies`, `state`, and `safety` modules exist; old `live_runtime_session`/`live_runtime_dependencies` delegate as deprecated shims; focused runtime tests pass. | Compatibility aliases remain for one release. | Remove aliases after downstream migration. |
| T03 RuntimeMode vs live order permission | Complete | `RuntimeMode.LIVE_OBSERVATION` and `qts.runtime.permissions.LiveOrderPermission` exist; startup decisions expose `order_permission`; session order gate rejects `OBSERVATION_ONLY`. | `LivePermissionMode` remains only as a compatibility alias, not a class definition. | Remove alias after release window. |
| T04 paper broker vs paper simulated config | Complete | `PaperBrokerRuntimeConfig`, `PaperSimulatedRuntimeConfig`, `configs/paper_broker.yaml`, and `configs/paper_simulated.yaml` are covered by acceptance tests. | `PaperRuntimeConfig` remains as deprecated compatibility config. | Remove compatibility config after migration. |
| T05 shared market-data contracts out of `qts.data.live` | Complete | Shared contracts are canonical in `qts.data.interfaces`, `events`, `capabilities`, and `subscriptions`; `qts.data.live.*` files are deprecation shims; default guardrail rejects shared contract definitions under `qts.data.live`. | Compatibility shims remain for one release. | Remove shims after downstream migration. |
| T06 fake vs simulated boundary | Complete | Production fake classes are rejected outside `qts.testing`; production imports from `qts.testing` are rejected; paper simulated config is explicitly separated from paper broker config. | Compatibility alias `FakeLiveFeedAdapter` remains under `qts.testing`, not production runtime/data packages. | Remove alias after release window. |
| T07 data transport migration | Complete | Canonical data transports live in `qts.data.transports`; old adapter transport paths are classless compatibility shims; focused transport tests and default `TransportCanonicalPathRule` pass. | None for canonical path migration. | Continue with T10/T11 transport internals; remove compatibility shims after release window. |
| T08 execution transport migration | Complete | Canonical execution transports and `IbkrOrderIdAllocator` live in `qts.execution.transports`; old adapter paths are classless compatibility shims; focused transport/order-id tests and `make guardrails` pass. | None for canonical path migration. | Continue with T10 order transport split; remove compatibility shims after release window. |
| T09 RuntimeSession coordinator split | Complete | `RuntimeSession` delegates market-data, broker lifecycle, safety, rollback, and recovery to dedicated coordinators; method-surface and coordinator tests pass; architecture HTML and snapshots were refreshed. | Event writing remains centralized on the session facade for shared envelope sequencing. | Continue with T12/T13 safety gates on top of `RuntimeSafetyController`. |
| T10 IBKR order transport split | Complete | `IbkrTwsOrderExecutionTransport` is a facade over `IbkrTwsConnection`, `IbkrTwsOrderClient`, `IbkrTwsReconciliationClient`, `IbkrTwsCallbackDispatcher`, and `IbkrTwsExecutionEventEmitter`; component and facade tests pass. | None for T10 split. T11 still owns callback quarantine/idempotency hardening. | Continue with T11 composite idempotency and quarantine tests. |
| T11 IBKR callback idempotency/quarantine | Complete | `BrokerCallbackQuarantine` exists; duplicate status/execution/commission callbacks are idempotent; composite execution key covers account/broker order/execution id; execution-before-openOrder can resolve; wrong-account execution is quarantined; unresolved callbacks block new order requests. | Broader reconnect command semantics move to T13/T24. | Continue with RuntimeSession coordinator split and startup/reconnect gates. |
| T12 market-data permission/freshness risk gate | Complete | `MarketDataRiskContext`, market-data permission/freshness risk rules, RiskDecision evidence, runtime risk-rejection events, and risk-rule registry wiring are implemented and tested. | Runtime source events still degrade the session before subsequent orders, by design. | Continue with startup/reconnect safety gates. |
| T13 broker runtime startup gate enforcement | Complete | Canonical broker-runtime startup classes exist with compatibility aliases; `BrokerRuntimeStartupGate` is wired into `RuntimeSafetyController`; live and paper-broker order paths fail closed without startup decisions; startup/reconnect evidence tests pass. | Reconnect resume command authorization remains in T24. | Continue with runtime command permission/audit/idempotency. |
| T14 replay no-future contract tests | Partial | Replay sequencer and subscription tests cover visible-at, mid-run subscribe, duplicates, and gaps. | Missing explicit unsubscribe delivery test, out-of-order rejected event coverage, and RuntimeEventSink anomaly integration for all cases. | Add remaining replay contract tests with RuntimeEventSink evidence. |
| T15 simulated execution assumptions manifest | Not started | Cost model and brokerage model are written. | Missing required execution-assumption fields such as fill/slippage/commission model names and versions, partial-fill policy, volume limit, capability model, unsupported-order policy, and latency model. | Add manifest assertion for complete `execution_assumptions`, then implement adapter/report payload. |
| T16 RuntimeEvent envelope contract | Partial | `RuntimeEvent` has envelope fields and context applies run/mode/sequence. | Required fields are optional on raw event; sinks can accept events before canonical envelope; event store still persists `BaseEvent`. | Add sink contract tests requiring canonical envelope before append and recovery replay by sequence. |
| T17 topology builder unification | Not started | Public `RuntimeTopologyBuilder` exists. | `_LiveRuntimeTopologyBuilder`, `_ResolvedLiveRuntimeTopology`, and `_StrategyRuntimeBinding` remain primary implementation details. | Add inventory test that live-only topology builder is absent from canonical inventory. |
| T18 durable event/snapshot recovery | Partial | Sequence validation and recovery gate helpers exist. | `FileEventStore.append()` is not atomic/fsync; `FileSnapshotStore` is append-only JSONL, not temp-file atomic rename; recovery does not rebuild runtime state plus broker reconciliation as one flow. | Add interruption/gap/reconciliation recovery tests before changing stores. |
| T19 multi-account runtime isolation | Partial | `AccountActor` validates fill account id; route metadata exists; some tests exist. | Missing full runtime tests for cancel isolation, wrong-account broker callback quarantine, route restore after recovery, and account-scoped risk config. | Add integration tests for fill/cancel/order/recovery/account-risk isolation. |
| T20 signal aggregation audit loop | Partial | `SignalPolicyEngine`, `SignalAggregatorActor`, and signal conflict runtime events exist. | `AggregatedSignalBatch` lacks several required fields; report/ledger traceability from final order plan back to aggregation decision is incomplete. | Add tests for deterministic policies and RiskDecision/OrderPlan back-reference to aggregation decision. |
| T21 reporting base contract and manifest completeness | Not started | `BacktestReportWriter` and `LiveReportWriter` exist. | `ReportWriter` and `RuntimeArtifactWriter` are empty classes, not protocols with required methods; no shared `RuntimeManifest`; live writer does not finalize artifacts through the base contract. | Write protocol/contract tests for backtest/live writers and manifest required fields. |
| T22 config path unification | Complete | `qts.runtime.config` is a package with canonical mode-specific modules; `PaperBrokerRuntimeConfig`/`PaperSimulatedRuntimeConfig` are exported from `qts.runtime.config.paper` and package `__init__`. | None for Milestone 1. | Later work can introduce stricter import-style checks if needed. |
| T23 StartRuntime command unification | Partial | `OperationsService.start_runtime` exists. | `qts.application.commands.start_paper` remains an implementation, not a shim; no `StartRuntimeCommand` with runtime_mode/config_ref/operator/idempotency/reason. | Add tests for `StartRuntimeCommand` starting backtest/paper/live-observation and old path shim-only behavior. |
| T24 runtime command permission/audit/idempotency | Complete | `RuntimeCommand` carries operator role/scope, requested/approved metadata, reason codes, scoped idempotency, dual-control live enablement checks, reconnect-resume reconciliation checks, and audit event payloads; application/API DTOs expose command result reason codes. Focused runtime/application/API tests and final `make check` pass. | None for T24. | Continue with Milestone 3 backlog. |
| T25 docs, inventory, architecture snapshot | Complete | `docs/architecture/backtest_live_parallel_sequence.html` is updated for M1 canonical names; HTML sync tests pass; after inventory/import graph snapshots were regenerated. | Transport path documentation remains a Milestone 2 concern. | Refresh again after transport migration. |
| T26 CI architecture guardrail strict mode | Complete for M1 | `make guardrails` is in CI and passes; default suite rejects production fake classes, production `qts.testing` imports, deprecated imports outside shims, and shared contracts under `qts.data.live`; transport canonical rule exists for warning/future strict use. | Transport path strict default waits for T07/T08 in Milestone 2 because current transports are not yet migrated. | Enable `TransportCanonicalPathRule` by default after T07/T08. |

## Milestone 1 Execution Order

Milestone 1 should be completed before runtime safety work. The goal is to stabilize names, paths, and automated boundaries so later changes do not chase moving targets.

1. **M1-G1 guardrail gap tests**
   - Status: `Complete` on 2026-05-15.
   - Evidence:
     - Added focused tests for shared contracts in `qts.data.live`, transport classes under adapters, deprecated import usage, production `qts.testing` imports, and fake classes outside `qts.testing`.
     - Added corresponding rule classes in `qts.quality.guardrails`.
     - Fixed targeted `GuardrailSuite(rules=...)` execution so single-rule tests actually exercise the supplied rule list.
   - Add failing tests under `tests/unit/scripts/test_verify_guardrails.py` for:
     - `DataLiveNoSharedContractRule`
     - `TransportCanonicalPathRule`
     - `DeprecatedImportNoNewUsageRule`
     - production no-fake outside `qts.testing`
     - production no `qts.testing` imports
   - Verification command: `uv run pytest tests/unit/scripts/test_verify_guardrails.py -q`
   - Observed result: `44 passed`.

2. **M1-G2 shared data/fake boundary**
   - Status: `Complete` on 2026-05-15.
   - Evidence:
     - `DataLiveNoSharedContractRule` is now in the default guardrail suite.
     - `qts.data.live.adapter.LiveFeedAdapter` is an alias compatibility shim, not a canonical class definition.
     - Production `qts.testing` imports are rejected by the default guardrail suite.
     - Focused data compatibility tests pass.
   - Complete T01, T05, and T06 after G1 fails correctly.
   - Canonical shared contracts must live outside `qts.data.live`.
   - Only explicit compatibility tests may import deprecated live contract paths.
   - Verification commands:
     - `uv run pytest tests/unit/data tests/unit/scripts/test_verify_guardrails.py -q`
     - `make guardrails`

3. **M1-G3 runtime canonical rename**
   - Status: `Complete` on 2026-05-15.
   - Evidence:
     - Added `qts.runtime.session`, `qts.runtime.dependencies`, `qts.runtime.state`, `qts.runtime.safety`, and `qts.runtime.permissions`.
     - Deprecated runtime modules delegate to canonical modules.
     - `RuntimeMode.LIVE_OBSERVATION` and `LiveOrderPermission` are covered by startup/session tests.
   - Complete T02 and T03 together because session state and live order permission share imports.
   - New canonical modules:
     - `qts.runtime.session`
     - `qts.runtime.dependencies`
     - `qts.runtime.state`
     - `qts.runtime.safety`
     - `qts.runtime.permissions`
   - Deprecated modules must delegate immediately and emit `DeprecationWarning`.
   - Verification commands:
     - `uv run pytest tests/unit/runtime tests/integration/test_live_kill_switch_flow.py -q`
     - `rg -n "from qts\\.runtime\\.live_runtime_session import LiveRuntimeSession|from qts\\.runtime\\.live import LivePermissionMode" backend/src/qts tests`

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
     - `rg -n "paper without real broker credentials|PaperRuntimeConfig" backend/src/qts/application backend/src/qts/runtime docs`

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
     - deprecated imports outside compatibility tests
   - Transport class path enforcement remains warning/future strict until T07/T08 move the transport classes.
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
