# P0 Wiring Follow-up + Structural Baseline Plan

- Document type: plan + status matrix
- Owner: TBD
- Created: 2026-05-17
- Predecessor: `docs/plan/2026-05-17_opt_25_to_29_platform_readiness_plan.md`
- Scope: ten items split across three independent lanes — close the wiring
  residue left by OPT-25.1/26.1/27.1/29.1, plus six structural baselines that
  unblock production observability, reliability, and capacity planning.

## 0. Why this batch, why now

After OPT-25.1/26.1/27.1/29.1 landed, four narrow wiring gaps remain and six
structural items have been promoted from P2 to P0/P1 because every additional
production-facing commit makes them costlier. They split cleanly into three
lanes that share no source files, so they can land in parallel without
serialized review.

| Lane | Theme | Items |
|---|---|---|
| A — Wiring residue | finish OPT-25/26/27/29 plumbing | OPT-25.2 / 26.2 / 27.2 / 29.2 |
| B — Observability | metrics + audit + schema | OPT-15 / 17 / 18 |
| C — Reliability | reconciliation + recovery + perf | OPT-47 / 48 / 50 |

## 1. Non-negotiable platform invariants

Every item must preserve the durable invariants from
`docs/architecture/backtest_live_parity.md` and `CLAUDE.md`:

| # | Invariant | Anchor |
|---|---|---|
| 1 | Strategies emit intents only; no direct order creation. | `qts.strategy_sdk.context.StrategyContext` |
| 2 | Risk runs before order submission in every mode. | `qts.risk.RiskEngine` |
| 3 | `OrderManagerActor` owns order state in every mode. | `qts.execution.order_manager` |
| 4 | `AccountActor` owns cash and positions in every mode. | `qts.runtime.actors.account_actor` |
| 5 | Broker symbols stay at adapter boundaries; core uses `InstrumentId`. | guardrails |
| 6 | Decimal end-to-end for monetary and price math. | guardrails |
| 7 | Backtest cannot use a shortcut that live cannot use. | parity doc |
| 8 | Every spec touched needs a first failing test before production edits. | matrix style |

These supersede any item-level acceptance below.

## 2. Status matrix (updated as items land)

| Item | Status | First red gate | Verified green | Commit |
|---|---|---|---|---|
| OPT-25.2 Wire `on_holdings_snapshot` | ✅ DONE | `test_exposure_in_finalized_backtest.py` | ✓ | `de18b66` |
| OPT-26.2 Consume `account.position_closed` in stats | ✅ DONE | `test_statistics_consumes_position_closed.py` | ✓ | `55dc935` |
| OPT-27.2 Risk rule rejects sim-unsupported types | ✅ DONE | `test_order_spec_validity_rejects_unsupported.py` | ✓ | `e4f2b72` |
| OPT-29.2 `api.auth_decision` audit events | ✅ DONE | `test_api_audit_emission.py` | ✓ | `eef4ad2` |
| OPT-15 Prometheus exporter + queue depth | ✅ DONE | `test_prometheus_metrics_endpoint.py` | ✓ | `145a089` |
| OPT-17 Event schema migration registry | ✅ DONE | `test_event_schema_migration.py` | ✓ | `d28e33f` |
| OPT-18 Freeze exceptions cleanup + `expires_on` | ✅ DONE | `test_freeze_exception_schema.py` | ✓ | `d60ff82` |
| OPT-47 Reconciliation kill-switch | ✅ DONE | `test_persistent_drift_kill_switch.py` | ✓ | `71dd959` |
| OPT-48 Crash-mid-fill recovery anchor | ✅ DONE | `test_recovery_byte_identical_state.py` | ✓ | `6c3d421` |
| OPT-50 Performance benchmark baseline | ✅ DONE | `tests/benchmarks/` suite green | ✓ | `6cfc399` |

Marking an item DONE requires: first red gate recorded, focused green
recorded, `make check` recorded, commit linked, this matrix updated.

---

# Lane A — Wiring residue

## OPT-25.2 — Wire `on_holdings_snapshot`

**Goal**: every backtest equity point emits a holdings notional snapshot so
`avg_gross_exposure` / `avg_net_exposure` appear in the finalized payload.

**Domain fact / invariant**: at every equity-point sample, exposure is the
absolute (gross) and signed (net) sum of `quantity × mark_price × multiplier`
for the account's holdings at the same instant.

**Correct owner / boundary**: `BacktestArtifactWriter.write_equity_point` is
the one place that snapshots equity; it should also snapshot holdings notional
through the same call. Mark prices already live in `state.latest_prices` of
the backtest actor loop.

**Forbidden shortcut**: computing exposure from fills alone; emitting a
synthetic zero when no positions exist (current behaviour silently elides the
field — that is correct **only** when the writer has never been informed,
not when it has been informed with zero exposure).

**Scope**:
- Add `BacktestArtifactWriter.write_holdings_snapshot(*, gross_notional, net_notional)`.
- Call it from `BacktestActorLoop.write_equity_point_phase` right after the
  equity point write, sourcing notional from the latest mark prices and the
  account snapshot.
- Drop the existing test assertion `"avg_gross_exposure" not in payload` and
  replace with a real value.

**Required gates**:
- `tests/integration/test_exposure_in_finalized_backtest.py`: one open
  position over 5 bars → `avg_gross_exposure` > 0 in the statistics payload.
- existing `tests/unit/reporting/test_statistics_payload_shape.py` flips to
  expect the keys present.

**ETA**: 0.5 day.

---

## OPT-26.2 — Statistics consumes `account.position_closed`

**Goal**: `StatisticsBuilder` no longer keeps its private `_OpenTrade`
aggregator; trade-level counters (`total_trades`, `win_rate`, `profit_factor`,
`expectancy`, `largest_win/loss`) come from `account.position_closed` events.

**Domain fact / invariant**: realized PnL per trade is computed exactly once
by `HoldingBook` when a holding crosses through flat; downstream consumers
read it, they do not recompute it.

**Correct owner / boundary**: `BacktestArtifactWriter` routes `account.position_closed`
events to `_statistics.on_position_close(realized_pnl, holding_bars)`;
`_OpenTrade` is deleted; `on_fill` shrinks to cost-only (commission,
slippage, total_orders).

**Forbidden shortcut**: keeping `_OpenTrade` around as a fallback; computing
holding_bars from a private per-instrument tracker rather than from event
timestamps versus the writer's bar counter.

**Scope**:
- Delete `_OpenTrade` and the trade-cross logic in `StatisticsBuilder.on_fill`.
- Add `BacktestArtifactWriter.write_position_closed(payload)` that decodes
  the event and calls `_statistics.on_position_close(realized_pnl, holding_bars)`.
- Plumb the call from `BacktestRuntimeSink.write` whenever
  `event.kind == "account.position_closed"`.
- `holding_bars` derived from `(payload.closed_at - payload.opened_at) /
  bar_duration` where `bar_duration` is the configured target timeframe.

**Required gates**:
- `tests/anchor/test_statistics_consumes_position_closed.py`: builder fed
  three `on_position_close` events; payload `total_trades == 3`,
  `win_rate / profit_factor / expectancy` match offline values.
- existing OPT-25.1 numerical anchors stay green.
- `_OpenTrade` deleted (guardrail-like grep assertion: zero occurrences).

**ETA**: 1 day.

---

## OPT-27.2 — Risk rule rejects sim-unsupported types

**Goal**: an intent carrying an `OrderSpec.order_type` outside the active
brokerage's `supported_order_types` is rejected by `OrderSpecValidityRule`
at risk-time, before it can crash in the adapter.

**Domain fact / invariant**: an intent that cannot execute under the active
brokerage must be rejected at risk-time, not crashed inside the adapter.
Backtest and live cannot use different acceptance sets.

**Correct owner / boundary**: `qts.risk.rules.order_spec_validity` consults
the active `BrokerageRiskPolicy.supported_order_types` (new Protocol field)
and rejects unsupported types with reason `UNSUPPORTED_ORDER_TYPE`.

**Forbidden shortcut**: letting the adapter raise `NotImplementedError`; that
is a runtime crash, not a risk decision.

**Scope**:
- Extend `BrokerageRiskPolicy` Protocol with
  `supported_order_types: frozenset[BrokerOrderType]`.
- Existing `BrokerageModel.simulated/custom/ibkr_*` already expose
  `capabilities.supported_order_types`; surface that through a thin adapter.
- `OrderSpecValidityRule` accepts an optional brokerage policy; when present,
  rejects intents whose `order_spec.order_type` is not supported.
- `SimulatedExecutionAdapter` strips the `_UNSUPPORTED_SIM_ORDER_TYPES` set
  from its default `BrokerCapabilities.supported_order_types` so the rule
  can see the truth at config time.

**Required gates**:
- `tests/anchor/test_order_spec_validity_rejects_unsupported.py`:
  intent with `TRAILING_STOP` against simulated brokerage →
  `RiskDecision.approved == False`, `reason_code == "UNSUPPORTED_ORDER_TYPE"`.
- same intent against an IBKR brokerage policy that supports trailing stop →
  approved.
- adapter `NotImplementedError` path remains as a defence-in-depth gate but
  is unreachable in normal flow.

**ETA**: 0.5 day.

---

## OPT-29.2 — `api.auth_decision` audit events

**Goal**: every authentication and authorization outcome (200/401/403/429)
through `ApiSecurityMiddleware` emits exactly one `api.auth_decision` audit
event with `(principal_id, method, path, status_code, latency_ms,
correlation_id)`. A pluggable sink writes the events; default sink is
stderr JSON.

**Domain fact / invariant**: auth decisions are an audit trail; their
absence is itself a compliance failure.

**Correct owner / boundary**: new `qts.observability.audit_sink.AuditSink`
Protocol owned by the observability layer; `ApiSecurityMiddleware` accepts
an optional sink in its constructor; default = stderr JSON writer.

**Forbidden shortcut**: routing the events through the FastAPI logger and
calling that "audit"; mixing audit semantics into the existing
`RuntimeEventSink` (different lifecycle, different retention).

**Scope**:
- New `qts.observability.audit_sink` module with `AuditSink` Protocol,
  `InMemoryAuditSink` (test helper), and `StderrJsonAuditSink` (default).
- `ApiSecurityMiddleware` takes `audit_sink: AuditSink | None = None`;
  emits one `AuditEvent` per request.
- `AuditEvent` already exists; reuse it with `event_type="api.auth_decision"`,
  `actor=<principal_id-or-anonymous>`, `message=f"{method} {path} {status}"`,
  `correlation_id` from request state.

**Required gates**:
- `tests/integration/api/test_api_audit_emission.py`:
  - bad token → 1 audit event with status 401
  - good token → 1 event with status 200
  - missing scope → 1 event with status 403
- audit sink size grows by exactly 1 per request.

**ETA**: 0.5 day.

---

# Lane B — Observability

## OPT-15 — Prometheus exporter + queue depth + per-stage latency

**Goal**: a `/metrics` endpoint serves Prometheus text format with counters
for the 12 `RuntimeCounterMetric` enums, gauges for actor mailbox depth, and
histograms for the 8 `RuntimeLatencyMetric` enums. CI assertion catches
silent metric drop.

**Domain fact / invariant**: production SLI/SLO require wire-format metrics
that an external Prometheus can scrape.

**Correct owner / boundary**: new `qts.observability.prometheus` module
hosts a `PrometheusMetricsRegistry` that implements the existing
`MetricsRegistry` Protocol. FastAPI app mounts `/metrics` outside the auth
middleware (Prometheus convention).

**Forbidden shortcut**: scraping the in-memory dict via JSON over the auth-
protected API; mixing metric collection into the trading hot path
synchronously (use the existing async tap pattern).

**Scope**:
- Add `prometheus_client` dependency.
- `PrometheusMetricsRegistry` wraps `prometheus_client.CollectorRegistry`,
  exposes the existing counter/histogram/gauge API used by `metrics.py`.
- `/metrics` GET endpoint on FastAPI app, **bypassed by auth middleware**
  (path whitelist alongside `/health`).
- Mailbox depth gauge sampled per dispatch in `MarketDataCoordinator`.
- Histogram instrumentation hooks in
  `RuntimeMarketDataCoordinator.trigger_strategy_for_bar` (one observation
  per stage from a `time.perf_counter()` delta).

**Required gates**:
- `tests/integration/test_prometheus_metrics_endpoint.py`:
  - GET `/metrics` returns 200 + `text/plain; version=0.0.4; charset=utf-8`
  - body contains `market_data_events_total`, `strategy_eval_latency_bucket`,
    `actor_mailbox_depth`
  - bypass of auth: no token required for `/metrics`
- one anchor that a counter increments after one backtest bar.

**ETA**: 1 day.

---

## OPT-17 — Event schema migration registry

**Goal**: replaying an event store that contains older `payload_schema_version`
values goes through a `SchemaMigrationRegistry`; readers always see the
current schema. New event kinds can ship without breaking historical replays.

**Domain fact / invariant**: once a `RuntimeEvent` is persisted, its
payload is durable; schema evolution must preserve replay determinism.

**Correct owner / boundary**: `qts.runtime.event_store.SchemaMigrationRegistry`
keyed by `(kind, from_version)`; `InMemoryEventStore.replay` and
`FileEventStore.replay` run each event through the registry before yielding.

**Forbidden shortcut**: ad-hoc `if event["kind"] == X and payload.get("v") == "0":`
branches in readers; silent passthrough of unknown versions.

**Scope**:
- `SchemaMigrationRegistry.register(kind: str, from_version: str,
  to_version: str, migrate: Callable[[dict], dict])`.
- `EventStore.replay()` applies registry; on unknown version, raises
  `SchemaMigrationMissing`.
- One concrete migration shipped: `account.position_closed v0→v1` adding
  a synthetic `schema_audit` field (proof-of-life).

**Required gates**:
- `tests/anchor/test_event_schema_migration.py`:
  - register `(account.position_closed, "0")` migration that adds a field;
    persist a v0 event; replay yields a v1 event with the new field.
  - unregistered v0 event for a kind without migration → `SchemaMigrationMissing`.
  - already-current event passes through unchanged.

**ETA**: 1 day.

---

## OPT-18 — Freeze exceptions cleanup + `expires_on`

**Goal**: every entry in `docs/architecture/platform_freeze_exceptions.yaml`
carries `expires_on: YYYY-MM-DD` (ISO date) and `re_evaluate_reason:
<non-empty>`; CI fails on expired exceptions.

**Domain fact / invariant**: a freeze exception without an expiry becomes
permanent dead weight; the file growth rate proves the lack of enforcement
is real.

**Correct owner / boundary**: `qts.quality.platform_freeze` (existing
loader in `guardrails.py` — extracted in this item to its own module).
`scripts/verify_guardrails.py` enforces the schema.

**Forbidden shortcut**: bulk-setting `expires_on: never`; a placeholder
date that nobody owns.

**Scope**:
- Loader requires `expires_on` (ISO date) and `re_evaluate_reason`.
- Bulk-fill existing entries with `expires_on: 2026-08-17` (3 months) and
  `re_evaluate_reason: "auto-filled during OPT-18 — refresh by expiry"`.
- Guardrail check: any expiry < today's date → fail with list.

**Required gates**:
- `tests/quality/test_freeze_exception_schema.py`:
  - missing `expires_on` rejected.
  - missing `re_evaluate_reason` rejected.
  - expired entry rejected.
- `make guardrails` continues to pass with the bulk-filled file.

**ETA**: 1 day.

---

# Lane C — Reliability

## OPT-47 — Reconciliation kill-switch

**Goal**: after N (configurable, default 3) consecutive reconciliation
cycles with the same DIVERGENT drift key, the runtime transitions to
observation-only and activates the kill-switch.

**Domain fact / invariant**: persistent broker/internal drift is a
financial-correctness emergency; further orders compound the discrepancy.

**Correct owner / boundary**: `qts.reconciliation.persistent_drift.
PersistentDriftKillSwitch`. The reconciliation engine feeds it each cycle's
report; the existing kill-switch path receives the activation.

**Forbidden shortcut**: counting cycles in `ReconciliationEngine` itself
(it should remain a stateless diff producer); reaching directly into the
runtime state machine (use the existing kill-switch contract).

**Scope**:
- `PersistentDriftConfig(consecutive_threshold: int = 3)`.
- `PersistentDriftKillSwitch.observe(report) -> KillSwitchDecision` keyed
  by drift identifier.
- Test that single-cycle drift does not trip; same key for `threshold`
  cycles does; alternating keys never trip.

**Required gates**:
- `tests/anchor/test_persistent_drift_kill_switch.py`:
  - threshold=3; feed two DIVERGENT cycles on key A → no kill; third → kill.
  - feed A, B, A → no kill (alternation breaks streak).
  - MATCHED report resets the streak.

**ETA**: 1 day.

---

## OPT-48 — Crash-mid-fill recovery anchor

**Goal**: a documented end-to-end anchor proves that crashing after sequence
number N and replaying events 1..N + applying the latest snapshot reproduces
the byte-identical AccountSnapshot / OrderManagerSnapshot the run would have
had at the same point.

**Domain fact / invariant**: deterministic replay underpins backtest/live
parity; if a crash mid-run cannot be recovered byte-for-byte, parity is
hypothetical.

**Correct owner / boundary**: existing `state_recovery.py` is the
implementation; this item adds the gate.

**Forbidden shortcut**: comparing string representations rather than
structural snapshots; allowing any difference under "rounding".

**Scope**:
- New anchor: run a 10-bar backtest, snapshot at bar 5, replay events
  1..5 from a fresh state via `state_recovery`, compare to the bar-5
  snapshot of the live run.
- If divergence found: file as a bug under OPT-48 and fix in the same
  PR (or split out).

**Required gates**:
- `tests/anchor/test_recovery_byte_identical_state.py` passes for
  `AccountSnapshot.cash`, `AccountSnapshot.holdings`,
  `OrderManagerSnapshot.orders`, `OrderManagerSnapshot.broker_to_order`,
  `OrderManagerSnapshot.seen_fill_ids`.

**ETA**: 1-2 days (depends on what divergence is found).

---

## OPT-50 — Performance benchmark baseline

**Goal**: `tests/benchmarks/` runs five micro-benchmarks under
`pytest-benchmark` and records per-path latency (μs) into
`evidence/benchmarks/baseline.json`. CI runs the suite as informational
(non-gating) until a regression policy is set in a later item.

**Domain fact / invariant**: capacity planning needs measured numbers.

**Correct owner / boundary**: `tests/benchmarks/` is the location;
`evidence/benchmarks/` is the durable storage of baselines.

**Forbidden shortcut**: a single end-to-end timing without per-stage
breakdown; storing raw timings in the test file itself.

**Scope**:
- Add `pytest-benchmark` dev dependency.
- Five benchmarks:
  - `bench_account_actor_apply_fill`
  - `bench_holding_book_apply_fill`
  - `bench_risk_engine_check`
  - `bench_market_data_dispatch_one_bar`
  - `bench_order_manager_process_report`
- Each benchmark stores result via `benchmark.extra_info` so JSON output is
  readable.
- Baseline file `evidence/benchmarks/baseline.json` checked in.

**Required gates**:
- `tests/benchmarks/` runs and produces output without errors.
- Each path has a μs-level number recorded in the baseline.
- `make check` does not run benchmarks (they live behind their own marker).

**ETA**: 1 day.

---

## 3. Execution lanes (parallel)

| Lane | Owner | Files | Exit evidence |
|---|---|---|---|
| A | Main session | `qts.reporting`, `qts.risk`, `qts.api` | OPT-25.2..29.2 green |
| B | Main session | `qts.observability`, `qts.runtime.event_store`, `qts.quality` | OPT-15/17/18 green |
| C | Main session | `qts.reconciliation`, recovery anchors, benchmarks | OPT-47/48/50 green |

The three lanes touch disjoint module roots and can land in any order;
within Lane A, OPT-26.2 lands before OPT-25.2 because both edit
`statistics.py` and 26.2 is the bigger refactor.

## 4. Verification commands

```bash
PYTHONPATH=backend/src uv run pytest tests/anchor tests/integration tests/unit -q
make guardrails
make typecheck
make lint
make check
PYTHONPATH=backend/src uv run pytest tests/benchmarks -m benchmark --benchmark-only
```

## 5. How this plan is used

- Each item is referenced by ID in PR titles.
- Status flips to `IN-PROGRESS` when work starts and to `DONE` with commit
  hash when verified green.
- This matrix is the single place that tracks completion; backlog updates
  follow.
- Items discovered during this work go to the source backlog with the next
  free OPT-NN; no renumbering.
