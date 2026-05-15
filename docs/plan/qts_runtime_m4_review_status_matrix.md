# QTS Runtime M4 Review Status Matrix

> Source backlog: `docs/plan/qts_runtime_post_review_improvement_tasks.md`
> Scope: Milestone 4 - Replay realism and reproducibility
> M4 task set: T14, T15, plus full regression
> Baseline date: 2026-05-15

## Completion Rules

A task is `Complete` only when every acceptance condition in the source backlog has direct evidence from at least one of:

- a focused unit, integration, replay, anchor, or regression test
- a runtime event or manifest contract test that fails on violation
- updated durable documentation for intentionally changed contracts
- fresh verification command output

Passing broad tests is not sufficient when a M4 acceptance item has no focused gate.

## M4 Goal

M4 makes replay and simulation reproducible enough for strategy comparison:

- replay data must behave like a broker-like subscription source, not like full-history direct access
- strategies must never see a bar close before the bar is complete and visible
- replay anomalies must be explicit runtime evidence, not silent data repair
- simulated fills, slippage, commission, capability limits, partial-fill policy, and latency assumptions must be manifest-backed
- backtest, paper-simulated, paper-broker, and live artifacts must remain parseable through the shared runtime event/reporting contracts completed in M3

## Current Summary

| Area | Status | Review Finding |
|---|---:|---|
| M4 overall | Complete | T14/T15 implementation gates are covered by focused tests, architecture snapshots/docs are refreshed, and final `make check` passed after M4 implementation. |
| Replay no-future contract | Complete | `ReplayClock`, `ReplaySequencedEvent.visible_at`, `ReplayEventSequencer`, and `SubscriptionReplayMarketDataSource` enforce source-order validation, deterministic visible-at emission, and active subscription delivery. |
| Replay subscription lifecycle | Complete | Subscribe, mid-run subscribe, and unsubscribe delivery-stop behavior are covered by focused replay source tests. |
| Replay anomaly evidence | Complete | Duplicate, out-of-order, and gap diagnostics enter canonical runtime event artifacts through `MarketDataFlow` and `BacktestRuntimeEventSink`; deterministic event timestamps preserve replay report hashes. |
| Simulated execution assumptions | Complete | Backtest and paper-simulated manifests include `execution_assumptions` with fill/slippage/commission versions, partial/volume policy, broker capability payload, unsupported-order policy, and latency assumptions. |
| Artifact parseability | Complete | Runtime events and manifests use shared schema contracts, and the backtest artifact anchor now includes `execution_assumptions`. |

## Task Matrix

| Task | Status | Evidence Found | Blocking Gaps | First Required Red Gate |
|---|---:|---|---|---|
| T14 replay no-future contract tests | Complete | `tests/unit/data/test_replay_market_data_source.py`, `tests/unit/runtime/test_market_data_flow.py`, `tests/unit/backtest/test_backtest_streaming_sink.py`, and `tests/replay/test_backtest_determinism.py` cover unsubscribe, out-of-order rejection, duplicate/gap/out-of-order runtime evidence, and deterministic report hash. | None. | Keep these tests in M4 final regression. |
| T15 simulated execution assumptions manifest | Complete | `tests/unit/backtest/test_report_metadata.py`, `tests/unit/reporting/test_live_report_writer.py`, `tests/unit/backtest/test_backtest_actor_loop.py`, `tests/unit/runtime/test_runtime_evolution_plan_acceptance.py`, and `tests/anchor/test_backtest_chain_acceptance_anchors.py` cover manifest assumptions, paper-simulated parity, fill model payloads, capability reject events, and artifact contract parseability. | None. | Keep these tests in M4 final regression. |
| M4 full regression | Complete | M4 focused replay/simulation suite passed with 32 tests; final `make check` passed with format, lint, guardrails, typecheck, unit, integration, and anchor gates. | None. | Keep M4 focused replay tests alongside default check because `tests/replay` is outside the normal unit/integration/anchor targets. |

## Dependency Order

| Gate | Tasks | Why This Order |
|---|---|---|
| M4-G1 replay visibility and subscription contract | T14 | No-future behavior is a domain invariant; it must be locked before broader replay artifact claims. |
| M4-G2 replay anomaly runtime evidence | T14 | Diagnostic events must enter the same runtime event contract completed in M3. |
| M4-G3 simulated execution assumptions manifest | T15 | Manifest schema should be enforced before filling in cost/fill/capability payload details. |
| M4-G4 simulated broker capability rejection evidence | T15 | Unsupported orders must become auditable runtime events, not just local exceptions. |
| M4-G5 full regression and docs | T14-T15 | M4 is complete only after replay, simulation, manifest, architecture/docs, and `make check` evidence are fresh. |

## Execution Gates

### M4-G1 - Replay Visibility And Subscription Contract

**Goal:** Replay bars are visible only at `[start, end)` completion and only for active subscriptions.

**Files likely to touch:**

- Modify: `backend/src/qts/data/sources/replay_market_data_source.py`
- Modify: `backend/src/qts/runtime/market_data_flow.py`
- Test: `tests/unit/data/test_replay_market_data_source.py`
- Test: `tests/unit/runtime/test_market_data_flow.py`
- Test: `tests/integration/test_backtest_engine_flow.py`

**Required first tests:**

- bar close for `[10:00, 10:01)` is not strategy-visible before `10:01`
- mid-run subscribe only receives bars whose `end_time >= subscribed_at`
- unsubscribe before the next bar prevents delivery of that later bar
- same-timestamp multi-instrument ordering is deterministic

**Verification:**

```bash
uv run pytest tests/unit/data/test_replay_market_data_source.py \
  tests/unit/runtime/test_market_data_flow.py \
  tests/integration/test_backtest_engine_flow.py -q
```

### M4-G2 - Replay Anomaly Runtime Evidence

**Goal:** Replay gaps, duplicates, and out-of-order bars are explicit runtime evidence.

**Files likely to touch:**

- Modify: `backend/src/qts/data/sources/replay_market_data_source.py`
- Modify: `backend/src/qts/runtime/market_data_flow.py`
- Modify: `backend/src/qts/backtest/actor_loop.py`
- Modify: `backend/src/qts/backtest/engine.py`
- Test: `tests/unit/data/test_replay_market_data_source.py`
- Test: `tests/unit/backtest/test_backtest_streaming_sink.py`
- Test: `tests/replay/test_backtest_determinism.py`

**Required first tests:**

- duplicate bars are dropped and emit `replay_duplicate_dropped`
- out-of-order bars are rejected and emit `replay_out_of_order_rejected`
- gaps emit `replay_gap_detected` without silent fill
- each anomaly can be written as a canonical runtime event envelope through the backtest sink

**Verification:**

```bash
uv run pytest tests/unit/data/test_replay_market_data_source.py \
  tests/unit/backtest/test_backtest_streaming_sink.py \
  tests/replay/test_backtest_determinism.py -q
```

### M4-G3 - Simulated Execution Assumptions Manifest

**Goal:** Backtest and paper-simulated reports state every execution assumption needed for audit and comparison.

**Files likely to touch:**

- Modify: `backend/src/qts/execution/simulator/fill_model.py`
- Modify: `backend/src/qts/execution/adapters/simulated_execution_adapter.py`
- Modify: `backend/src/qts/execution/broker.py`
- Modify: `backend/src/qts/reporting/backtest.py`
- Modify: `backend/src/qts/reporting/live.py`
- Modify: `backend/src/qts/backtest/engine.py`
- Test: `tests/unit/backtest/test_report_metadata.py`
- Test: `tests/unit/reporting/test_live_report_writer.py`
- Test: `tests/anchor/test_backtest_chain_acceptance_anchors.py`

**Required first tests:**

- backtest manifest contains `execution_assumptions`
- `execution_assumptions` includes:
  - `fill_model_name`
  - `fill_model_version`
  - `slippage_model_name`
  - `slippage_model_version`
  - `commission_model_name`
  - `commission_model_version`
  - `volume_participation_limit`
  - `partial_fill_policy`
  - `broker_capability_model`
  - `unsupported_order_rejection_policy`
  - `market_data_latency_model`
- changing fill/slippage/commission model assumptions changes manifest/report hash
- paper-simulated live manifest includes the same assumptions block

**Verification:**

```bash
uv run pytest tests/unit/backtest/test_report_metadata.py \
  tests/unit/reporting/test_live_report_writer.py \
  tests/anchor/test_backtest_chain_acceptance_anchors.py -q
```

### M4-G4 - Simulated Broker Capability Rejection Evidence

**Goal:** Backtest unsupported orders are rejected according to broker capability assumptions and leave runtime evidence.

**Files likely to touch:**

- Modify: `backend/src/qts/execution/adapters/simulated_execution_adapter.py`
- Modify: `backend/src/qts/runtime/intent_processing.py`
- Modify: `backend/src/qts/backtest/actor_loop.py`
- Test: `tests/unit/runtime/test_runtime_evolution_plan_named_gates.py`
- Test: `tests/unit/backtest/test_backtest_actor_loop.py`
- Test: `tests/integration/test_backtest_engine_flow.py`

**Required first tests:**

- unsupported order type is rejected by simulated broker capabilities
- rejection produces a runtime event with reason code and capability payload
- rejected unsupported order does not create a fill or mutate account state

**Verification:**

```bash
uv run pytest tests/unit/backtest/test_backtest_actor_loop.py \
  tests/unit/runtime/test_runtime_evolution_plan_named_gates.py \
  tests/integration/test_backtest_engine_flow.py -q
```

### M4-G5 - Final M4 Closure

**Goal:** M4 behavior and docs are durable after implementation.

**Files likely to touch:**

- Modify: `docs/plan/qts_runtime_post_review_status_matrix.md`
- Modify: `docs/plan/qts_runtime_m4_review_status_matrix.md`
- Modify: `docs/plan/qts_runtime_post_review_improvement_tasks.md`
- Optional modify: `docs/architecture/backtest_live_parallel_sequence.html`
- Optional modify: `tests/architecture/snapshots/class_inventory_after_post_review.json`
- Optional modify: `tests/architecture/snapshots/import_graph_after_post_review.json`

**Closure gates:**

```bash
uv run pytest tests/unit/data/test_replay_market_data_source.py \
  tests/unit/runtime/test_market_data_flow.py \
  tests/unit/backtest/test_report_metadata.py \
  tests/unit/reporting/test_live_report_writer.py \
  tests/replay/test_backtest_determinism.py -q
make check
```

If production class/method locations change, also run:

```bash
uv run python tools/architecture/export_inventory.py --source backend/src --output tests/architecture/snapshots/class_inventory_after_post_review.json
uv run python tools/architecture/export_import_graph.py --source backend/src --output tests/architecture/snapshots/import_graph_after_post_review.json
uv run pytest tests/unit/test_backtest_live_parallel_sequence_html.py \
  tests/unit/test_architecture_baseline_smokes.py -q
```

## M4 No-Go Criteria

Do not mark M4 complete if any of these remain true:

- strategy code can observe a bar close before that bar's `end_time`
- unsubscribe does not prevent later replay delivery
- out-of-order replay bars are not rejected with explicit diagnostics
- replay anomalies do not enter canonical runtime event artifacts
- backtest manifest lacks a complete `execution_assumptions` block
- paper-simulated manifest lacks the same execution assumptions contract
- unsupported simulated broker capability rejects are not auditable runtime events
- `make check` has not passed after the M4 implementation

## M4 Final Verification

M4 closure completed with:

```bash
uv run pytest tests/unit/data/test_replay_market_data_source.py \
  tests/unit/runtime/test_market_data_flow.py \
  tests/unit/backtest/test_report_metadata.py \
  tests/unit/reporting/test_live_report_writer.py \
  tests/unit/backtest/test_backtest_actor_loop.py \
  tests/unit/backtest/test_backtest_streaming_sink.py \
  tests/replay/test_backtest_determinism.py -q
make check
```

Observed result:

```text
M4 focused replay/simulation: 32 passed
make check:
- ruff format: unchanged
- ruff check: all checks passed
- guardrails: Architecture guardrails passed
- mypy: Success, 476 source files
- unit: 671 passed, 1 warning
- integration: 58 passed, 4 skipped
- anchor: 39 passed, 1 skipped
```

## M4 Baseline Verification

M3 closure completed with:

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

This is only the M3-closed baseline. It does not prove M4 is complete.
