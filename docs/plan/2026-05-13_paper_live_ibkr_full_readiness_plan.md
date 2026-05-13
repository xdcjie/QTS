# Paper / Live IBKR Full Readiness Plan

**Date:** 2026-05-13

**Goal:** Make paper trading fully usable against the local IB Gateway paper
account at `127.0.0.1:4002`, and make live trading code-path-ready behind
explicit operational gates, using the same strategy, risk, order, execution,
fill, account, reporting, and reconciliation path.

**Architecture:** Backtest, paper, and live are execution modes of one runtime.
Only market data source, execution adapter, clock, connectivity, persistence,
latency, and external broker capabilities may differ. Paper/live must reuse:

```text
Strategy SDK
-> StrategyExecutionPipeline
-> TargetIntentProcessor / OrderPlanBuilder
-> RiskEngine
-> OrderManagerActor
-> ExecutionActor
-> BrokerExecutionAdapter
-> normalized ExecutionReport
-> ExecutionReportHandler
-> AccountActor
-> runtime sink / report / reconciliation
```

**Tech stack:** Python 3.13, actor + mailbox runtime, IBKR TWS API via an
adapter boundary, pytest, ruff, mypy, architecture guardrails, real IB Gateway
paper endpoint `127.0.0.1:4002`.

---

## Domain Facts And Gates

**Domain fact / invariant:** A broker callback is not a fill until it has been
normalized into an internal `ExecutionReport`, accepted by `OrderManager`, and
converted to `ApplyFill` by `ExecutionReportHandler`.

**Correct owner or abstraction boundary:**

- `qts.data.adapters`: IBKR market-data normalization.
- `qts.execution.adapters`: IBKR order request/report normalization.
- `qts.runtime`: actor wiring, lifecycle, event routing, runtime state.
- `qts.risk`: pre-trade risk decisions.
- `qts.portfolio` / `AccountActor`: cash and position mutation.
- `qts.reconciliation`: broker/internal snapshot comparison.

**Forbidden shortcuts:**

- Strategy directly calling IBKR, broker adapters, order manager, risk, or
  account state.
- Live or paper runtime mutating account cash/positions outside `AccountActor`.
- Broker symbols entering domain, risk, portfolio, Strategy SDK, or runtime
  actor-owned state.
- Combining IBKR market data and order execution into one adapter.
- Treating paper Gateway evidence as approval for live capital.

**Required gates / verification:**

- `make format`
- `make lint`
- `make guardrails`
- `make typecheck`
- `make test-unit`
- `make test-integration`
- `make test-anchor`
- `git diff --check`
- Real IBKR paper evidence from `127.0.0.1:4002`
- Paper soak evidence
- Reconciliation evidence
- Kill-switch evidence
- Rollback evidence
- Engineering, operations, and risk signoff before live capital

---

## Current State Snapshot

Implemented foundations:

- Shared `StrategyExecutionPipeline` exists in
  `backend/src/qts/runtime/strategy_execution_pipeline.py`.
- Shared `MarketDataFlow` exists in
  `backend/src/qts/runtime/market_data_flow.py`.
- Shared `TargetIntentProcessor` and `OrderPlanBuilder` exist in
  `backend/src/qts/runtime/intent_processing.py`.
- Shared `ExecutionReportHandler` exists in
  `backend/src/qts/runtime/execution_report_handler.py`.
- Backtest sink/reporting have concrete implementations under
  `qts.runtime.sinks.backtest` and `qts.reporting.backtest`.
- `BrokerExecutionAdapter` can bridge a broker adapter into `ExecutionActor`.
- Fake IBKR market-data and order-execution integration tests exist.

Known gaps:

- `LiveRuntime` is still a small beta wrapper and does not yet own the full
  strategy-to-account actor chain.
- `StreamingMarketDataSource` is still an empty live/paper source boundary.
- `LiveRuntimeEventSink` and `LiveReportWriter` are still empty boundaries.
- `IbkrMarketDataAdapter` and `IbkrOrderExecutionAdapter` normalize shapes, but
  they do not yet own a real TWS API transport.
- Real paper Gateway anchors do not yet prove connection, subscription, order
  ack/cancel/fill, account update, reconciliation, kill switch, reconnect, or
  soak behavior.

---

## Milestone P0: Paper Gateway Baseline And Safety Preconditions

**Goal:** Prove the local IB Gateway paper endpoint is reachable and that local
configuration is safe before any market-data or order action.

**Files:**

- Create local only: `configs/paper.ibkr.local.yaml`
- Modify: `backend/src/qts/application/commands/ibkr_environment_evidence.py`
- Modify: `backend/src/qts/config/ibkr.py`
- Test: `tests/unit/scripts/test_ibkr_collect_environment_evidence.py`
- Test: `tests/unit/config/test_ibkr_environment_guards.py`
- Evidence: `evidence/ibkr/*.json`

**Tasks:**

- [ ] Create `configs/paper.ibkr.local.yaml` from
  `configs/paper.ibkr.example.yaml`.
- [ ] Set both paper connections to `host: 127.0.0.1`, `port: 4002`.
- [ ] Keep market data and order execution on distinct client IDs.
- [ ] Keep paper account ID in `DU...` form.
- [ ] Ensure the local config is ignored by git if it contains local account
  details.
- [ ] Extend `collect_environment_evidence` to record separate market-data and
  order-execution TCP probe results for `127.0.0.1:4002`.
- [ ] Extend evidence output with Gateway target, client IDs, mode, account
  classification, and secret reference status.
- [ ] Add a test that paper config on `4002` is accepted and live config on
  `4002` is rejected unless explicitly marked observation-only.

**Commands:**

```bash
PYTHONPATH=backend/src uv run python scripts/ibkr_collect_environment_evidence.py \
  --config configs/paper.ibkr.local.yaml \
  --output-dir evidence/ibkr \
  --label paper-gateway-4002 \
  --timeout-seconds 2

make guardrails
pytest tests/unit/scripts/test_ibkr_collect_environment_evidence.py tests/unit/config/test_ibkr_environment_guards.py -q
```

**Acceptance:**

- TCP probe to `127.0.0.1:4002` succeeds for the configured paper boundaries.
- Evidence JSON has `orders_enabled: false` and `observe_only: true`.
- Evidence JSON contains no password, token, or credential value.
- Invalid paper/live separation fails before any network or order action.
- No IBKR order API is called in P0.

---

## Milestone P1: Real IBKR Transport Boundary

**Goal:** Add real IBKR TWS API connectivity behind narrow transport interfaces
without leaking IBKR objects outside adapter modules.

**Files:**

- Create: `backend/src/qts/data/adapters/ibkr_transport.py`
- Create: `backend/src/qts/execution/adapters/ibkr_transport.py`
- Modify: `backend/src/qts/data/adapters/ibkr_market_data.py`
- Modify: `backend/src/qts/execution/adapters/ibkr_order_execution.py`
- Modify: `pyproject.toml` and lockfile only if an approved dependency is added
- Test: `tests/unit/data/test_ibkr_market_data_transport.py`
- Test: `tests/unit/execution/test_ibkr_order_execution_transport.py`
- Test: `tests/unit/scripts/test_verify_guardrails.py`

**Tasks:**

- [ ] Select the TWS API Python client implementation and record the decision
  in `docs/broker/ibkr_adapter_decision.md`.
- [ ] Define a market-data transport protocol that emits raw IBKR tick, quote,
  and bar callback payloads only to `IbkrMarketDataAdapter`.
- [ ] Define an order-execution transport protocol that accepts normalized
  order requests and emits raw IBKR order status, execution, commission, error,
  disconnect, and reconnect callback payloads only to
  `IbkrOrderExecutionAdapter`.
- [ ] Add guardrail tests proving `qts.data.adapters` still does not import
  execution/risk/portfolio/runtime and `qts.execution.adapters` still does not
  import data.
- [ ] Add unit tests using fake transport objects for connect, disconnect,
  callback dispatch, and callback normalization.

**Commands:**

```bash
pytest tests/unit/data/test_ibkr_market_data_transport.py tests/unit/execution/test_ibkr_order_execution_transport.py -q
make guardrails
make typecheck
```

**Acceptance:**

- IBKR-specific client objects are only referenced inside IBKR adapter/transport
  modules.
- Core domain, runtime, Strategy SDK, risk, portfolio, and reconciliation do not
  import IBKR client types.
- Market-data and order-execution transports are distinct classes with distinct
  client IDs.
- Transport unit tests pass without connecting to IB Gateway.

---

## Milestone P2: Streaming Market Data Source

**Goal:** Turn IBKR market data callbacks into internal market-data events that
enter the shared `MarketDataFlow` and strategy pipeline.

**Files:**

- Modify: `backend/src/qts/data/sources/streaming_market_data_source.py`
- Modify: `backend/src/qts/data/adapters/ibkr_market_data.py`
- Modify: `backend/src/qts/runtime/market_data_flow.py` only if a public source
  API is needed
- Test: `tests/unit/data/test_streaming_market_data_source.py`
- Test: `tests/integration/test_ibkr_gateway_market_data_anchor.py`
- Test: `tests/anchor/test_market_data_subscription_anchors.py`

**Tasks:**

- [ ] Implement `StreamingMarketDataSource` as the owner of live/paper source
  subscriptions.
- [ ] Expose explicit methods for `subscribe`, `unsubscribe`, `on_tick`,
  `on_quote`, `on_bar`, and `drain`.
- [ ] Convert callback payloads to `Tick`, `Quote`, or `Bar` through
  `IbkrMarketDataAdapter`.
- [ ] Feed complete bars through `MarketDataFlow`.
- [ ] Add stale-data detection based on configured max age per subscription.
- [ ] Emit a runtime degradation event when stale data exceeds threshold.

**Commands:**

```bash
pytest tests/unit/data/test_streaming_market_data_source.py -q
pytest tests/anchor/test_market_data_subscription_anchors.py -q
PYTHONPATH=backend/src uv run pytest tests/integration/test_ibkr_gateway_market_data_anchor.py \
  --ibkr-paper-gateway 127.0.0.1:4002
```

**Acceptance:**

- Fake transport callback produces normalized internal market-data objects.
- Real paper Gateway subscription receives at least one normalized tick, quote,
  or bar for a configured instrument.
- All internal market-data events carry `InstrumentId`, not IBKR broker symbol.
- Requested timeframe semantics are preserved by shared aggregation.
- Stale market data blocks new orders through runtime degradation.

---

## Milestone P3: IBKR Order Execution And Callback Normalization

**Goal:** Submit and cancel paper orders through IBKR paper Gateway and process
ack/cancel/fill callbacks through the shared order and account chain.

**Files:**

- Modify: `backend/src/qts/execution/adapters/ibkr_order_execution.py`
- Modify: `backend/src/qts/execution/adapters/broker_execution_adapter.py`
- Modify: `backend/src/qts/runtime/actors/execution_actor.py` only if cancel
  messages are added
- Modify: `backend/src/qts/runtime/actors/order_manager_actor.py` only if cancel
  messages are added
- Test: `tests/unit/execution/test_ibkr_order_execution_adapter.py`
- Test: `tests/unit/execution/test_broker_execution_adapter.py`
- Test: `tests/integration/test_ibkr_gateway_order_lifecycle_anchor.py`
- Test: `tests/integration/test_live_execution_report_flow.py`

**Tasks:**

- [ ] Add explicit capability checks for market orders, limit orders, cancel,
  replace, fractional quantity, shorting, and supported asset classes.
- [ ] Submit paper orders only after receiving an approved `RiskDecision`.
- [ ] Normalize IBKR order status callback into internal `ExecutionReport`.
- [ ] Normalize IBKR execution callback into internal `ExecutionReport`.
- [ ] Normalize IBKR commission callback and attach commission to fill reports
  before account mutation.
- [ ] Preserve broker order ID to runtime broker order ID mapping in
  `BrokerExecutionAdapter`.
- [ ] Reject unknown broker order IDs with a fail-closed runtime event.
- [ ] Add cancel flow through `OrderManagerActor -> ExecutionActor ->
  BrokerExecutionAdapter`.

**Commands:**

```bash
pytest tests/unit/execution/test_ibkr_order_execution_adapter.py tests/unit/execution/test_broker_execution_adapter.py -q
pytest tests/integration/test_live_execution_report_flow.py -q
PYTHONPATH=backend/src uv run pytest tests/integration/test_ibkr_gateway_order_lifecycle_anchor.py \
  --ibkr-paper-gateway 127.0.0.1:4002 \
  --paper-only \
  --non-marketable-limit
```

**Acceptance:**

- Risk-rejected order never reaches IBKR transport.
- Accepted broker ack changes order state but does not mutate account.
- Cancel request follows the approved actor path and receives a broker callback.
- Fill callback mutates account only through `ExecutionReportHandler` and
  `AccountActor`.
- Duplicate fill ID is idempotent.
- Unknown broker order ID does not mutate order or account state.

---

## Milestone P4: Shared Paper / Live Runtime Session

**Goal:** Replace beta `LiveRuntime.submit_order` direct broker behavior with a
shared actor runtime session that can run a strategy end-to-end in paper mode.

**Files:**

- Create: `backend/src/qts/runtime/live_runtime_session.py`
- Create: `backend/src/qts/runtime/live_runtime_dependencies.py`
- Modify: `backend/src/qts/runtime/live.py`
- Modify: `backend/src/qts/application/commands/start_paper.py`
- Modify: `scripts/run_paper.py`
- Test: `tests/unit/runtime/test_live_runtime_session.py`
- Test: `tests/integration/test_paper_runtime_full_chain.py`
- Test: `tests/anchor/test_backtest_live_parity.py`

**Tasks:**

- [ ] Introduce `LiveRuntimeDependencies` with market-data source, strategy,
  risk engine, instrument context, execution adapter, sink, account actor, and
  registries.
- [ ] Introduce `LiveRuntimeSession` with `start`, `stop`, `pause`, `resume`,
  `degrade`, `recover`, and `on_market_data`.
- [ ] Wire `on_market_data` to:

  ```text
  StreamingMarketDataSource
  -> MarketDataFlow
  -> StrategyExecutionPipeline
  -> TargetIntentProcessor
  -> OrderManagerActor
  -> ExecutionActor
  -> BrokerExecutionAdapter
  -> ExecutionReportHandler
  -> AccountActor
  ```

- [ ] Remove direct broker submission from the runtime execution path.
- [ ] Keep observation mode capable of market data and reconciliation without
  order submission.
- [ ] Keep live mode fail-closed unless explicit startup decision permits real
  order submission.

**Commands:**

```bash
pytest tests/unit/runtime/test_live_runtime_session.py -q
pytest tests/integration/test_paper_runtime_full_chain.py -q
pytest tests/anchor/test_backtest_live_parity.py -q
```

**Acceptance:**

- Same reference strategy source runs in backtest and paper runtime.
- Paper runtime emits an order only through `RiskEngine` and actor path.
- `pause` rejects new intents before order submission.
- `degrade` rejects new intents but keeps market data and reconciliation
  observability alive.
- Live runtime defaults to observation-only unless all startup guards pass.

---

## Milestone P5: Runtime Event Sink And Live Report Writer

**Goal:** Make paper/live runs auditable, replayable, and comparable to broker
state.

**Files:**

- Modify: `backend/src/qts/runtime/sinks/base.py`
- Modify: `backend/src/qts/runtime/sinks/live.py`
- Modify: `backend/src/qts/reporting/live.py`
- Test: `tests/unit/runtime/test_live_runtime_event_sink.py`
- Test: `tests/unit/reporting/test_live_report_writer.py`
- Test: `tests/integration/test_live_runtime_evidence_output.py`

**Tasks:**

- [ ] Define normalized `RuntimeEvent` kinds for state transition, market data,
  strategy intent, risk decision, order submitted, broker request, broker
  report, fill, account snapshot, reconciliation report, kill switch, and
  runtime error.
- [ ] Implement `LiveRuntimeEventSink` as a writer of append-only NDJSON event
  streams.
- [ ] Implement `LiveReportWriter` to produce a manifest with config hash,
  event hashes, artifact paths, row counts, runtime mode, account ID, and
  redacted connection metadata.
- [ ] Add per-order trace fields that connect intent, risk, order, broker
  request, broker report, fill, and account snapshot.

**Commands:**

```bash
pytest tests/unit/runtime/test_live_runtime_event_sink.py tests/unit/reporting/test_live_report_writer.py -q
pytest tests/integration/test_live_runtime_evidence_output.py -q
```

**Acceptance:**

- Every submitted order has a complete trace from intent to account snapshot.
- Runtime artifacts contain no secret values.
- Event hashes are stable for identical event payloads.
- Live report manifest names all artifacts and row counts.
- Evidence is enough to replay final internal account state.

---

## Milestone P6: Reconciliation, Startup Gate, And Recovery

**Goal:** Block trading when broker and internal state disagree, and recover
order mappings safely after reconnect.

**Files:**

- Modify: `backend/src/qts/reconciliation/*`
- Create: `backend/src/qts/runtime/live_reconciliation.py`
- Modify: `backend/src/qts/execution/adapters/broker_execution_adapter.py`
- Test: `tests/unit/runtime/test_live_reconciliation.py`
- Test: `tests/integration/test_ibkr_gateway_reconciliation_anchor.py`
- Test: `tests/integration/test_runtime_recovery_from_events.py`

**Tasks:**

- [ ] Build broker `ReconciliationSnapshot` from IBKR open orders, fills,
  positions, and cash.
- [ ] Build internal `ReconciliationSnapshot` from `OrderManager` snapshot and
  `AccountActor` snapshot.
- [ ] Run reconciliation before enabling paper/live order submission.
- [ ] Run periodic reconciliation while runtime is active.
- [ ] Degrade runtime on unclassified drift.
- [ ] Rebuild broker order ID mapping from `OrderManagerSnapshot` after
  reconnect.
- [ ] Verify duplicate post-reconnect callbacks remain idempotent.

**Commands:**

```bash
pytest tests/unit/runtime/test_live_reconciliation.py -q
pytest tests/integration/test_runtime_recovery_from_events.py -q
PYTHONPATH=backend/src uv run pytest tests/integration/test_ibkr_gateway_reconciliation_anchor.py \
  --ibkr-paper-gateway 127.0.0.1:4002 \
  --paper-only
```

**Acceptance:**

- Startup reconciliation drift blocks order submission.
- Matched broker/internal snapshots allow paper trading.
- Unknown broker open order produces actionable drift and degraded runtime.
- Reconnect restores broker order ID mapping without duplicate account mutation.
- Reconciliation evidence is written to live report artifacts.

---

## Milestone P7: Kill Switch And Rollback Drill

**Goal:** Prove operators can stop new orders, cancel active orders through the
approved path, preserve evidence, and recover safely.

**Files:**

- Modify: `backend/src/qts/risk/kill_switch.py`
- Modify: `backend/src/qts/runtime/live_runtime_session.py`
- Modify: `backend/src/qts/runtime/sinks/live.py`
- Modify: `docs/operations/production_rollout_checklist.md`
- Modify: `docs/infra/rollback_procedure.md`
- Test: `tests/unit/risk/test_kill_switch.py`
- Test: `tests/integration/test_live_kill_switch_flow.py`
- Test: `tests/integration/test_ibkr_gateway_kill_switch_anchor.py`

**Tasks:**

- [ ] Add a runtime kill-switch command that blocks new strategy intents before
  `SubmitOrder`.
- [ ] Add cancel-all-active-orders through `OrderManagerActor ->
  ExecutionActor -> BrokerExecutionAdapter`.
- [ ] Emit kill-switch evidence with runtime state, active order IDs, broker
  cancel reports, account snapshots, and reconciliation report.
- [ ] Add rollback command that stops new orders, persists snapshots, preserves
  event store paths, and records operator action.

**Commands:**

```bash
pytest tests/unit/risk/test_kill_switch.py -q
pytest tests/integration/test_live_kill_switch_flow.py -q
PYTHONPATH=backend/src uv run pytest tests/integration/test_ibkr_gateway_kill_switch_anchor.py \
  --ibkr-paper-gateway 127.0.0.1:4002 \
  --paper-only
```

**Acceptance:**

- Kill switch blocks new broker submissions.
- Active order cancellation uses only the approved actor path.
- Broker cancel callbacks update internal order state.
- Rollback evidence contains event store path, snapshots, broker reports, and
  final reconciliation status.

---

## Milestone P8: Real Paper Full-Chain Anchors

**Goal:** Prove the complete paper system works against `127.0.0.1:4002` with
real IB Gateway behavior.

**Files:**

- Create: `tests/integration/test_ibkr_gateway_full_chain_anchor.py`
- Create: `tests/anchor/test_ibkr_gateway_paper_readiness.py`
- Modify: `docs/operations/production_soak_plan.md`
- Modify: `docs/operations/live_beta_go_no_go.md`
- Evidence: `evidence/ibkr/paper-full-chain-*.json`

**Tasks:**

- [ ] Run observe-only connection evidence.
- [ ] Run real market-data subscription evidence.
- [ ] Submit a non-marketable paper limit order and cancel it.
- [ ] Submit a marketable tiny paper order only after manual operator
  confirmation in the test command.
- [ ] Run a reference strategy that emits one controlled paper order.
- [ ] Compare internal final account state against broker state.
- [ ] Record queue depth, event latency, stale data, errors, reconnects, memory,
  order count, fill count, and reconciliation result.

**Commands:**

```bash
PYTHONPATH=backend/src uv run pytest tests/integration/test_ibkr_gateway_full_chain_anchor.py \
  --ibkr-paper-gateway 127.0.0.1:4002 \
  --paper-only \
  --operator-confirm-paper-order

PYTHONPATH=backend/src uv run pytest tests/anchor/test_ibkr_gateway_paper_readiness.py \
  --evidence-dir evidence/ibkr
```

**Acceptance:**

- Observe-only evidence passes.
- Market-data evidence passes.
- Non-marketable limit submit/cancel evidence passes.
- Tiny paper fill evidence passes with internal and broker account state
  reconciled.
- Reference strategy source is unchanged across backtest and paper.
- No unexplained drift exists at run end.
- Evidence artifacts are committed or archived according to operations policy.

---

## Milestone P9: Paper Soak

**Goal:** Demonstrate paper runtime stability over a full regular trading
session for the target strategy and instrument set.

**Files:**

- Modify: `docs/operations/load_and_soak.md`
- Modify: `docs/operations/production_soak_plan.md`
- Create: `tests/soak/test_ibkr_paper_session_soak.py`
- Evidence: `evidence/ibkr/paper-soak-*.json`

**Tasks:**

- [ ] Run one full regular trading session in paper or observation mode.
- [ ] Record event lag, queue depth, runtime state transitions, stale-data
  events, broker status, rejected orders, memory growth, reconnects, and
  reconciliation results.
- [ ] Run end-of-session reconciliation.
- [ ] Record operator notes for any manual interventions.

**Commands:**

```bash
PYTHONPATH=backend/src uv run pytest tests/soak/test_ibkr_paper_session_soak.py \
  --ibkr-paper-gateway 127.0.0.1:4002 \
  --paper-only \
  --duration full-session
```

**Acceptance:**

- Full-session evidence has no unexplained reconciliation drift.
- No order bypasses risk or actor order path.
- No stale-data event remains unresolved at session end.
- No duplicate fill mutates account twice.
- Runtime memory and queue depth remain within documented thresholds.

---

## Milestone P10: Live Observation And Readiness Gate

**Goal:** Verify live environment readiness without submitting live orders.

**Files:**

- Modify: `docs/operations/ibkr_live_readiness.md`
- Modify: `docs/operations/paper_vs_live_comparison.md`
- Modify: `docs/operations/production_rollout_checklist.md`
- Test: `tests/integration/test_ibkr_live_observation_anchor.py`
- Evidence: `evidence/ibkr/live-observation-*.json`

**Tasks:**

- [ ] Validate live config cannot use paper account ID, paper client IDs, paper
  secret references, or paper risk profile.
- [ ] Connect live Gateway/TWS in observation mode only.
- [ ] Verify live market data subscription normalization.
- [ ] Verify account, permissions, and broker capabilities without order
  submission.
- [ ] Compare paper decisions against live market and broker state.
- [ ] Require engineering, operations, and risk signoff before enabling any live
  capital path.

**Commands:**

```bash
PYTHONPATH=backend/src uv run pytest tests/integration/test_ibkr_live_observation_anchor.py \
  --live-observation-only \
  --config configs/live.ibkr.local.yaml
```

**Acceptance:**

- Live observation submits no orders.
- Live config validation passes only with live account and live client IDs.
- Paper-vs-live comparison has no unexplained differences.
- Production rollout checklist has engineering, operations, and risk signoff.
- Live order submission remains disabled until signoff evidence exists.

---

## Final Acceptance Matrix

| Area | Paper acceptance | Live acceptance |
| --- | --- | --- |
| Config | `configs/paper.ibkr.local.yaml` validates for `127.0.0.1:4002` | live config rejects paper account/client/secret/risk profile |
| Market data | real paper Gateway normalized events enter `MarketDataFlow` | live observation normalized events enter `MarketDataFlow` |
| Strategy | unchanged strategy emits intents in paper | unchanged strategy can run in observation mode without order submission |
| Risk | rejected intent never reaches broker | rejected intent never reaches broker |
| Orders | submit, ack, cancel, fill pass through actor path | submit path remains disabled until signoff |
| Account | fills mutate only via `ExecutionReportHandler` and `AccountActor` | same invariant protected before live capital |
| Reporting | paper run writes event/report artifacts | live observation writes event/report artifacts |
| Reconciliation | paper internal and broker snapshots match | live observation snapshots reviewed |
| Kill switch | blocks new orders and cancels active orders through approved path | same drill required before live capital |
| Rollback | evidence preserved and restart-safe | evidence preserved and operator-approved |

---

## Completion Definitions

Paper is fully usable when:

- P0 through P9 are complete.
- `make check` passes.
- Real paper Gateway evidence exists for connection, market data, order
  lifecycle, strategy-driven runtime submission, account-config match,
  reconciliation, kill switch, rollback, and full-session soak.
- The final paper readiness report has no unexplained drift or unresolved stale
  data.

Live is code-path-ready when:

- P0 through P10 are complete.
- Live observation evidence exists.
- Paper-vs-live comparison is reviewed.
- Reconciliation, kill switch, rollback, and operational runbooks are reviewed.
- Engineering, operations, and risk owners sign off.

Live capital is approved only when:

- The live rollout checklist is complete.
- Capital limits are documented.
- Real order submission is explicitly enabled by configuration and manual
  approval.
- Any missing, stale, or conflicting evidence keeps the system in No-Go.

---

## Mandatory Verification Before Claiming Readiness

Run these commands on the final branch:

```bash
make format
make lint
make guardrails
make typecheck
make test-unit
make test-integration
make test-anchor
git diff --check
```

Run these environment-gated checks against paper Gateway:

```bash
PYTHONPATH=backend/src uv run python scripts/ibkr_collect_environment_evidence.py \
  --config configs/paper.ibkr.local.yaml \
  --output-dir evidence/ibkr \
  --label paper-gateway-4002

PYTHONPATH=backend/src uv run pytest tests/integration/test_ibkr_gateway_full_chain_anchor.py \
  --ibkr-paper-gateway 127.0.0.1:4002 \
  --paper-only \
  --operator-confirm-paper-order

PYTHONPATH=backend/src uv run pytest tests/soak/test_ibkr_paper_session_soak.py \
  --ibkr-paper-gateway 127.0.0.1:4002 \
  --paper-only \
  --duration full-session
```

Readiness cannot be claimed from fake transport tests alone.
