# QTS Runtime M3 Review Status Matrix

> Source backlog: `docs/plan/qts_runtime_post_review_improvement_tasks.md`
> Scope: Milestone 3 - Multi-account, recovery, reporting
> M3 task set: T16, T17, T18, T19, T20, T21
> Baseline date: 2026-05-15

## Completion Rules

A task is `Complete` only when every acceptance condition in the source backlog has direct evidence from at least one of:

- a focused unit, integration, anchor, architecture, or regression test
- a strict guardrail rule that fails on violation
- generated inventory/import-graph evidence
- updated durable documentation for intentionally changed contracts
- fresh verification command output

Passing existing tests is not sufficient when a plan acceptance item has no gate.

## M3 Goal

M3 turns the runtime from "broker-safe single-flow execution" into auditable multi-account and multi-strategy operation with durable recovery and shared artifact contracts.

Required durable invariants:

- runtime events must be canonical envelopes before they reach sinks, stores, reports, or recovery
- event sequence gaps must block paper-broker/live resume
- account route metadata must survive order, cancel, fill, broker callback, and recovery paths
- signal aggregation decisions must be traceable into risk and final order planning
- backtest/live reporting must share one manifest and artifact writer contract

## Current Summary

| Area | Status | Review Finding |
|---|---:|---|
| M3 overall | Complete | All six M3 tasks have direct code, test, and document evidence; final milestone verification is tracked in the closure section. |
| RuntimeEvent envelope | Complete | Runtime events crossing sinks and stores use one canonical envelope with `run_id`, `runtime_mode`, `sequence_no`, `event_id`, and schema version. |
| Topology builder | Complete | `RuntimeSession` uses the public `BrokerRuntimeTopologyResolver` boundary; live-private builder names are compatibility aliases only. |
| Durable recovery | Complete | Event/snapshot stores are hardened against missing sequence and partial snapshot writes; recovery decisions emit manifest/runtime-event evidence. |
| Multi-account isolation | Complete | Account, order, cancel, broker callback, risk-engine, and route metadata checks are covered by focused runtime tests. |
| Signal aggregation audit | Complete | Aggregated signal batches, risk decisions, order plans, and route metadata carry aggregation-decision traceability. |
| Reporting contract | Complete | Backtest/live manifests validate through shared `RuntimeManifest`; reporting writer boundaries are explicit protocols. |

## Task Matrix

| Task | Status | Evidence Found | Blocking Gaps | First Required Red Gate |
|---|---:|---|---|---|
| T16 RuntimeEvent envelope contract | Complete | `RuntimeEvent.require_canonical_envelope`, backtest/live sinks, and `FileEventStore` enforce/replay canonical runtime envelopes. | None for M3. | Keep canonical envelope tests when adding event kinds. |
| T17 RuntimeTopology builder unification | Complete | Public resolver/topology binding names are primary; architecture smoke tests reject live-private canonical builder classes. | Compatibility aliases remain. | Remove aliases after compatibility window. |
| T18 Durable event/snapshot recovery | Complete | Event appends fsync; snapshot save uses temp-file atomic replace; partial snapshots are ignored; recovery decisions serialize to manifest/runtime events. | None for M3. | Preserve gap/reconciliation recovery tests. |
| T19 Multi-account runtime isolation | Complete | Fill/cancel/wrong-account callback/route restore/account-risk tests cover account isolation gates. | None for M3. | Broaden as new broker callback flows are added. |
| T20 Signal aggregation audit loop | Complete | Batch, risk decision, order plan, route metadata, and runtime event payloads include aggregation-decision traceability. | None for M3. | Extend report presentation later if needed. |
| T21 Reporting base contract and manifest completeness | Complete | `RuntimeManifest`, `ReportWriter`, and `RuntimeArtifactWriter` are enforced by focused tests; live/backtest manifests share required fields. | None for M3. | Keep manifest anchors in sync with schema versions. |

## Dependency Order

| Gate | Tasks | Why This Order |
|---|---|---|
| M3-G1 canonical runtime event envelope | T16 | Recovery, reporting, signal audit, and account traceability all depend on one canonical event schema. |
| M3-G2 durable recovery stores and decisions | T18 | Requires T16 envelope so event replay and manifest evidence use the same sequence model. |
| M3-G3 topology builder/resolver unification | T17 | Multi-account isolation needs one topology source of truth for account, strategy, broker, and market-data routes. |
| M3-G4 multi-account runtime isolation | T19 | Depends on topology routes and recovery metadata; protects account-owned state before broader signal/reporting claims. |
| M3-G5 signal aggregation auditability | T20 | Can start with policy tests, but final traceability should use canonical events and account route metadata. |
| M3-G6 reporting/artifact contract | T21 | Can start in parallel, but final manifest should include T16/T18/T17 evidence fields. |
| M3-G7 docs/snapshots/final guardrails | T16-T21 | Refresh architecture docs and snapshots only after contracts and class boundaries are stable. |

## Execution Gates

### M3-G1 - RuntimeEvent Envelope Contract

**Goal:** All runtime events crossing sinks/stores/reports/recovery use one canonical immutable envelope.

**Files likely to touch:**

- Modify: `backend/src/qts/runtime/sinks/base.py`
- Modify: `backend/src/qts/runtime/sinks/backtest.py`
- Modify: `backend/src/qts/runtime/sinks/live.py`
- Modify: `backend/src/qts/runtime/event_store.py`
- Modify: `backend/src/qts/runtime/session.py`
- Test: `tests/unit/runtime/test_live_runtime_event_sink.py`
- Test: `tests/unit/backtest/test_backtest_streaming_sink.py`
- Test: `tests/unit/runtime/test_event_store.py`
- Test: `tests/integration/test_runtime_recovery_from_events.py`

**Required first tests:**

- sink write rejects events without canonical `run_id`, `runtime_mode`, `sequence_no`, and `event_id`
- `RuntimeEventContext` writes `runtime_mode`, not only `mode`
- order/fill/risk/account events require `correlation_id`
- fill events require a `causation_id` pointing to an order or broker callback event
- event store appends/replays canonical `RuntimeEvent` envelopes by sequence

**Verification:**

```bash
uv run pytest tests/unit/runtime/test_live_runtime_event_sink.py \
  tests/unit/backtest/test_backtest_streaming_sink.py \
  tests/unit/runtime/test_event_store.py \
  tests/integration/test_runtime_recovery_from_events.py -q
```

### M3-G2 - Durable Event/Snapshot Recovery

**Goal:** Recovery is safe against partial writes, sequence gaps, and unreconciled broker state.

**Files likely to touch:**

- Modify: `backend/src/qts/runtime/event_store.py`
- Modify: `backend/src/qts/runtime/state_recovery.py`
- Modify: `backend/src/qts/runtime/recovery.py`
- Modify: `backend/src/qts/runtime/safety_controller.py`
- Test: `tests/unit/runtime/test_event_store.py`
- Test: `tests/unit/runtime/test_state_recovery.py`
- Test: `tests/integration/test_runtime_recovery_from_events.py`

**Required first tests:**

- interrupted snapshot write is ignored and cannot become latest snapshot
- event sequence gap returns recovery decision `BLOCK`
- replay after latest snapshot uses `last_event_sequence_no`
- recovery decision remains observation-only until broker reconciliation passes
- recovery decision is emitted to `RuntimeEventSink` and manifest evidence

**Verification:**

```bash
uv run pytest tests/unit/runtime/test_event_store.py \
  tests/unit/runtime/test_state_recovery.py \
  tests/integration/test_runtime_recovery_from_events.py -q
```

### M3-G3 - RuntimeTopology Builder Unification

**Goal:** Public topology/resolver boundaries replace live-private topology builders.

**Files likely to touch:**

- Modify: `backend/src/qts/runtime/topology.py`
- Modify: `backend/src/qts/runtime/live_runtime_topology.py`
- Modify: `backend/src/qts/runtime/session.py`
- Modify: `docs/architecture/backtest_live_parallel_sequence.html`
- Test: `tests/unit/runtime/test_runtime_topology.py`
- Test: `tests/unit/runtime/test_live_runtime_topology.py`
- Test: `tests/unit/test_architecture_baseline_smokes.py`

**Required first tests:**

- class inventory does not list `_LiveRuntimeTopologyBuilder`, `_ResolvedLiveRuntimeTopology`, or `_StrategyRuntimeBinding` as canonical classes
- `RuntimeSession` does not import live-private topology classes
- paper/live/backtest topologies all produce `RuntimeTopologyManifest`
- duplicate strategy id fails
- missing account route and missing broker route fail

**Verification:**

```bash
uv run pytest tests/unit/runtime/test_runtime_topology.py \
  tests/unit/runtime/test_live_runtime_topology.py \
  tests/unit/test_architecture_baseline_smokes.py -q
```

### M3-G4 - Multi-Account Runtime Isolation

**Goal:** Account state, order state, broker callbacks, risk config, and route metadata cannot cross account partitions.

**Files likely to touch:**

- Modify: `backend/src/qts/runtime/actors/account_actor.py`
- Modify: `backend/src/qts/runtime/actors/order_manager_actor.py`
- Modify: `backend/src/qts/runtime/market_data_coordinator.py`
- Modify: `backend/src/qts/execution/adapters/ibkr_order_execution.py`
- Modify: `backend/src/qts/runtime/state_recovery.py`
- Test: `tests/unit/runtime/test_account_actor.py`
- Test: `tests/unit/runtime/test_order_manager_actor.py`
- Test: `tests/unit/execution/test_ibkr_order_execution_adapter.py`
- Test: `tests/integration/test_live_kill_switch_flow.py`
- Test: `tests/integration/test_live_execution_report_flow.py`

**Required first tests:**

- fill for account A never updates account B
- cancel for account A cannot cancel account B order
- wrong-account broker callback enters quarantine
- missing account route fails fast
- order route metadata is restored after recovery
- account-specific risk config is applied by account route

**Verification:**

```bash
uv run pytest tests/unit/runtime/test_account_actor.py \
  tests/unit/runtime/test_order_manager_actor.py \
  tests/unit/execution/test_ibkr_order_execution_adapter.py \
  tests/integration/test_live_kill_switch_flow.py \
  tests/integration/test_live_execution_report_flow.py -q
```

### M3-G5 - Signal Aggregation Audit Loop

**Goal:** Multi-strategy aggregation decisions are deterministic and traceable into risk, orders, reports, and runtime events.

**Files likely to touch:**

- Modify: `backend/src/qts/runtime/signal_policy.py`
- Modify: `backend/src/qts/runtime/actors/signal_aggregator_actor.py`
- Modify: `backend/src/qts/runtime/intent_processing.py`
- Modify: `backend/src/qts/runtime/market_data_coordinator.py`
- Modify: `backend/src/qts/runtime/actors/order_manager_actor.py`
- Test: `tests/unit/runtime/test_signal_aggregator_actor.py`
- Test: `tests/unit/runtime/test_live_runtime_session.py`
- Test: `tests/unit/backtest/test_backtest_actor_loop.py`

**Required first tests:**

- REJECT_CONFLICT records conflict reason and rejected strategy ids
- PRIORITY_WINS records winner and rejected strategy ids
- SUM_TARGETS and WEIGHTED_NET record each strategy contribution
- aggregated batch carries `account_id`, `instrument_id`, `correlation_id`, and aggregation decision id
- `RiskDecision` and final order route metadata reference aggregation decision id

**Verification:**

```bash
uv run pytest tests/unit/runtime/test_signal_aggregator_actor.py \
  tests/unit/runtime/test_live_runtime_session.py \
  tests/unit/backtest/test_backtest_actor_loop.py -q
```

### M3-G6 - Reporting Base Contract And Manifest

**Goal:** Backtest and live artifact/report writers implement one explicit contract and one manifest schema.

**Files likely to touch:**

- Modify: `backend/src/qts/reporting/base.py`
- Modify: `backend/src/qts/reporting/backtest.py`
- Modify: `backend/src/qts/reporting/live.py`
- Modify: `backend/src/qts/runtime/sinks/backtest.py`
- Modify: `backend/src/qts/runtime/sinks/live.py`
- Test: `tests/unit/reporting/test_live_report_writer.py`
- Test: `tests/unit/backtest/test_backtest_streaming_sink.py`
- Test: `tests/anchor/test_backtest_chain_acceptance_anchors.py`

**Required first tests:**

- `ReportWriter` has `write_manifest()` and `finalize()` protocol methods
- `RuntimeArtifactWriter` has `write_event()`, `write_snapshot()`, `write_manifest()`, and `finalize()` protocol methods
- backtest/live writers both emit `RuntimeManifest`
- manifest includes `run_id`, `runtime_mode`, `event_schema_version`, `artifact_schema_version`, `config_hash`, `topology_hash`, `created_at`, and `finalized_at`
- live writer finalizes runtime artifacts through the base contract

**Verification:**

```bash
uv run pytest tests/unit/reporting/test_live_report_writer.py \
  tests/unit/backtest/test_backtest_streaming_sink.py \
  tests/anchor/test_backtest_chain_acceptance_anchors.py -q
```

### M3-G7 - Final M3 Closure

**Goal:** Turn M3 multi-account/recovery/reporting contracts into durable gates and refreshed docs.

**Files likely to touch:**

- Modify: `docs/architecture/backtest_live_parallel_sequence.html`
- Modify: `tests/architecture/snapshots/class_inventory_after_post_review.json`
- Modify: `tests/architecture/snapshots/import_graph_after_post_review.json`
- Modify: `docs/plan/qts_runtime_post_review_status_matrix.md`
- Modify: `docs/plan/qts_runtime_m3_review_status_matrix.md`

**Required first tests:**

- architecture HTML lists the final canonical topology/recovery/reporting classes
- inventory no longer lists removed live-private topology implementation classes
- status matrices list M3 tasks as complete only after focused gates pass

**Verification:**

```bash
uv run pytest tests/unit/test_backtest_live_parallel_sequence_html.py \
  tests/unit/test_architecture_baseline_smokes.py \
  tests/unit/scripts/test_verify_guardrails.py -q
uv run python tools/architecture/export_inventory.py --source backend/src --output tests/architecture/snapshots/class_inventory_after_post_review.json
uv run python tools/architecture/export_import_graph.py --source backend/src --output tests/architecture/snapshots/import_graph_after_post_review.json
make check
```

## M3 No-Go Criteria

Do not mark M3 complete if any of these remain true:

- sinks/stores/reports can accept events without canonical envelope identity and sequence fields
- `FileEventStore` persists `BaseEvent` instead of canonical runtime events for recovery paths
- snapshot writes can leave a half-written latest snapshot
- event sequence gaps do not block paper-broker/live resume
- `RuntimeSession` still depends on `_LiveRuntimeTopologyBuilder` as the primary topology implementation
- account route metadata cannot be snapshotted and restored
- wrong-account broker callbacks can affect the wrong internal account path
- signal aggregation decisions cannot be traced into risk and final order planning
- `ReportWriter` and `RuntimeArtifactWriter` are not explicit protocols
- backtest/live manifests do not share one required `RuntimeManifest` schema

## M3 Baseline Verification

M2 closure was committed in `9e2ed33` with:

```bash
make check
```

Observed result:

- `ruff format`: passed
- `ruff check`: passed
- `scripts/verify_guardrails.py`: passed
- `mypy backend tests`: passed
- unit: `646 passed, 1 warning`
- integration: `58 passed, 4 skipped`
- anchor: `39 passed, 1 skipped`

This is only the M2-closed baseline. It does not prove any M3 task is complete.

## M3 Closure Verification

Fresh closure verification on 2026-05-15:

```bash
make check
```

Observed result:

- `ruff format`: passed
- `ruff check`: passed
- `scripts/verify_guardrails.py`: passed
- `mypy backend tests`: passed
- unit: `663 passed, 1 warning`
- integration: `58 passed, 4 skipped`
- anchor: `39 passed, 1 skipped`

Additional closure gates:

- architecture HTML and class/method index regenerated after final formatting
- class inventory and import graph snapshots regenerated
- code-review graph refreshed incrementally with minimal post-processing
