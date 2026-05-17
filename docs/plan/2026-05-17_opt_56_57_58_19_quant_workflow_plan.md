# OPT-56 / 57 / 58 / 19 — Wiring, Operational Baseline, and Optimizer

- Document type: plan + status matrix
- Owner: TBD
- Created: 2026-05-17
- Predecessor: `docs/plan/2026-05-17_p0_followup_and_structural_baseline_plan.md`
- Scope: close the two remaining anchor-only setups (OPT-15 metrics +
  OPT-17 migration registry), ship a focused operational baseline (health
  probes + alert rules + observability doc), and land the first usable
  walk-forward optimizer slice.

## 0. Why this batch, why now

Five rounds of project review converged on three structural gaps:

1. **"Shipped but unwired"** — `MetricsRegistry` and `SchemaMigrationRegistry`
   have anchor tests but no production caller. `/metrics` serves an empty body
   and the migration registry is empty. Until a non-test caller exists, both
   are dead assets.
2. **Operational readiness** — anchor-tested code does not equal "live with
   money". The project lacks Prometheus alert rules, differentiated health
   probes, and a documented observability setup. Live-beta runbooks exist but
   point at metrics nobody is recording.
3. **Optimizer is the basic quant workflow** — "tweak parameter, rerun, compare
   Sharpe" is the day-1 quant loop. Without a sweep runner, OPT-25.1 statistics
   are decorative.

Four items, ~5 days end-to-end, can land independently in three lanes.

| Lane | Theme | Items |
|---|---|---|
| A — Wire existing facilities | turn anchor-only assets into production assets | OPT-56 / 57 |
| B — Operational baseline | health probes + alert rules + doc | OPT-58 (focused slice) |
| C — Optimizer | first usable parameter-sweep runner | OPT-19 (first slice) |

## 1. Non-negotiable platform invariants

Items below must preserve the durable invariants from
`docs/architecture/backtest_live_parity.md` and CLAUDE.md / AGENTS.md:

| # | Invariant | Anchor |
|---|---|---|
| 1 | Backtest cannot use a shortcut that live cannot use. | parity doc |
| 2 | Strategy emits intents only. | SDK |
| 3 | Risk runs before order submission in every mode. | RiskEngine |
| 4 | Metrics / audit / migration must run alongside the real flow, not as a parallel pollers. | observability boundary |
| 5 | Every new gate must be backed by a first failing test before production edits. | matrix style |
| 6 | Smallest correct solution (§5 Simplicity). | senior-engineer test |

## 2. Status matrix (updated as items land)

| Item | Status | First red gate | Verified green | Commit |
|---|---|---|---|---|
| OPT-56 wire `SchemaMigrationRegistry` | ✅ DONE | `test_canonical_event_migration_registry.py` | ✓ | `702a4bb` |
| OPT-57 wire `MetricsRegistry` into hot path | ✅ DONE | `test_metrics_populated_by_backtest_run.py` | ✓ | `b7a3f61` |
| OPT-58.A health probe split | ✅ DONE | `test_health_probes_differentiated.py` | ✓ | `ed5ff47` |
| OPT-58.B Prometheus alert rules | ✅ DONE | `test_alert_rules_yaml_schema.py` | ✓ | `ed5ff47` |
| OPT-58.C observability setup doc | ✅ DONE | `test_observability_setup_doc.py` | ✓ | `ed5ff47` |
| OPT-19 ParameterSpace + grid runner | ✅ DONE | `test_optimization_runner_grid_sweep.py` | ✓ | `18a4e09` |

Marking an item DONE requires: first red gate recorded, focused green
recorded, `make check` recorded, commit linked, this matrix updated.

---

# Lane A — Wire existing facilities

## OPT-56 — Wire `SchemaMigrationRegistry` into production

### Goal
A non-test caller assembles a canonical `SchemaMigrationRegistry` containing
at least one real migration for a real event kind. `InMemoryEventStore`
default-constructs against this registry so a fresh production event store
gets schema-aware replay.

### Domain fact / invariant
Once an event is persisted, its payload version is durable. Schema evolution
must preserve replay determinism. A migration registry that ships empty is
dead weight that gives a false sense of safety.

### Correct owner / boundary
`qts.runtime.event_migrations` (new module) owns the canonical migration set.
`qts.runtime.event_store.InMemoryEventStore` and `FileEventStore` consume it.

### Forbidden shortcut
Returning an empty `SchemaMigrationRegistry()` from production code; treating
the registry as test-only infrastructure.

### Scope
- New `backend/src/qts/runtime/event_migrations.py` exporting
  `canonical_runtime_event_migrations() -> SchemaMigrationRegistry`.
- At least one **real** migration: `account.position_closed` v0 → v1 that
  back-fills a `schema_audit` field documenting the schema version transition
  (we don't yet have a real shape change, but this proves the wiring
  end-to-end and documents the version contract).
- `InMemoryEventStore.__init__` default `migration_registry` falls back to the
  canonical registry when none supplied.
- `FileEventStore` (read path) similarly uses the canonical registry.

### Required gates
- `tests/anchor/test_canonical_event_migration_registry.py`:
  - canonical registry has at least one registered migration.
  - replaying a v0 `account.position_closed` event through a default
    `InMemoryEventStore()` advances it to v1.
  - the registered migration carries the documented audit field.

### ETA
0.5 day.

---

## OPT-57 — Wire `MetricsRegistry` into runtime hot path

### Goal
After running one backtest tick or one live tick, the `/metrics` endpoint
serves non-empty Prometheus text with at least:
- `market_data_events_total`
- `strategy_eval_latency`
- `actor_mailbox_depth{name=...}`

### Domain fact / invariant
Metric observation is a side-effect of the actual event flow. The recorder
runs in the same path as the event sink, sees the same events, and records
deterministically.

### Correct owner / boundary
- `BacktestRuntimeEventSink` accepts an optional `metrics: MetricsRegistry`
  and calls `metrics.record_runtime_event(event)` for every event it writes.
- `RuntimeMarketDataCoordinator` accepts an injected `MetricsRegistry` and
  calls `metrics.record_runtime_event(event)` per stage emission.
- `time.perf_counter()` instruments `trigger_strategy_for_bar` and emits
  `record_latency(RuntimeLatencyMetric.STRATEGY_EVAL_LATENCY, elapsed)`.
- `create_app()` accepts the same registry so the HTTP `/metrics` exporter
  sees the populated counters.

### Forbidden shortcut
Polling actor state externally; emitting instrumentation that doesn't share
the bar timestamp; passing the metrics registry as a global singleton.

### Scope
- `BacktestRuntimeEventSink.__init__` takes `metrics: MetricsRegistry | None`.
- `BacktestRuntimeEventSink.write()` invokes
  `self._metrics.record_runtime_event(event)` after persisting.
- `BacktestEngine.run_streaming(output_dir, metrics=...)` plumbs the registry
  to the sink.
- One latency probe in `BacktestActorLoop.process_market_data_phase` around
  the `trigger_strategy_for_bar` block; emits to the supplied registry.
- Mailbox depth gauge: sample `mailbox.size` for each account partition once
  per dispatch tick.

### Required gates
- `tests/integration/test_metrics_populated_by_backtest_run.py`:
  - run a 3-bar backtest with a known strategy.
  - assert `market_data_events_total > 0` in the registry snapshot.
  - assert `strategy_eval_latency` has at least one observation.
  - assert `queue.depth` was sampled at least once.
- `tests/anchor/test_runtime_metrics_recorded_per_event.py`:
  - direct sink test — write one RuntimeEvent; counter increments.

### ETA
1 day.

---

# Lane B — Operational baseline (OPT-58 focused slice)

This item's full scope (alerts + Grafana + per-strategy labels + dashboards)
is one week. The slice landed in this PR covers the minimum that unblocks
external Prometheus integration and gives ops a checklist:

## OPT-58.A — Health probe split

### Goal
`/health/liveness`, `/health/readiness`, `/health/startup` carry distinct
semantics that an orchestrator (k8s) can use for restart vs traffic-cut
vs initial-rollout decisions.

### Domain fact / invariant
Liveness fail → restart the pod. Readiness fail → remove from load balancer
but do not restart. Startup fail → grace period during boot. Single `/health`
conflates these and makes orchestrators choose poorly.

### Correct owner / boundary
`qts.api.routes.health` owns the three endpoints. Existing `/health` is kept
as a documented alias of `/health/liveness` so existing callers do not break.

### Forbidden shortcut
Making the three probes return identical state; gating any probe behind auth.

### Scope
- `GET /health/liveness` → 200 if the process is responsive (pure smoke).
- `GET /health/readiness` → 200 if the runtime is in a ready state
  (`RuntimeSessionState.READY`); 503 otherwise.
- `GET /health/startup` → 200 if `startup_checklist.passed` (when available)
  or simply 200 in modes that don't have a startup checklist.
- All three bypass `ApiSecurityMiddleware` (already true for `/health`).
- The existing `GET /health` keeps current behaviour.

### Required gates
- `tests/integration/api/test_health_probes_differentiated.py`:
  - `/health/liveness` returns 200.
  - `/health/readiness` returns 503 when runtime not ready, 200 when ready.
  - `/health/startup` returns 200 in backtest mode.
  - all three bypass auth.

### ETA
0.5 day.

---

## OPT-58.B — Prometheus alert rules

### Goal
`configs/alerts/qts_alerts.yaml` ships 8 alert rules that an external
Prometheus server can scrape and route. Each rule references a metric that
OPT-57 actually populates, plus an annotation pointing at the relevant
runbook section.

### Domain fact / invariant
Alerts are durable specifications. They live in version control with the
code so a metric rename or removal forces matching alert update.

### Correct owner / boundary
`configs/alerts/qts_alerts.yaml` (new file). A quality test parses it and
verifies each rule references a real metric name from
`RuntimeCounterMetric` / `RuntimeLatencyMetric` / declared gauge names.

### Forbidden shortcut
Hard-coded thresholds without justification in the doc; alerts referencing
metrics that aren't recorded.

### Scope — 8 rules:
1. **`KillSwitchActive`** — `kill_switch_activations_total` increased > 0 in last 5m → page
2. **`ReconciliationDrift`** — `reconciliation_drifts_total` > 0 for 1m → page
3. **`MarketDataStale`** — `market_data_stale_total` > 0 for 30s → page
4. **`MarketDataSubscriptionFailure`** — `market_data_subscription_failures_total` > 0 in 5m → warn
5. **`BrokerRejectionRate`** — `broker_rejections_total` rate > 0.01/s for 1m → warn
6. **`RiskRejectionRate`** — `risk_rejections_total` rate > 0.1/s for 1m → warn (could be legitimate)
7. **`RuntimeRecoveryBlocked`** — `runtime_recovery_blocks_total` > 0 for 1m → page
8. **`HighStrategyEvalLatency`** — `strategy_eval_latency` p95 > 0.2s for 5m → warn

### Required gates
- `tests/quality/test_alert_rules_yaml_schema.py`:
  - YAML parses; structure matches Prometheus alert format.
  - 8 rules; each has `alert`, `expr`, `for`, `labels.severity`, `annotations.summary`, `annotations.runbook_url`.
  - every metric name referenced is in `RuntimeCounterMetric` ∪ `RuntimeLatencyMetric` ∪ allowed gauge names.

### ETA
0.5 day.

---

## OPT-58.C — Observability setup doc

### Goal
`docs/operations/observability_setup.md` documents:
- how to point an external Prometheus at `/metrics`
- the 8 alert rules and their runbook references
- which metrics are populated by which actor

### Owner / boundary
`docs/operations/observability_setup.md` is the durable doc; a quality test
ensures every alert in `qts_alerts.yaml` is referenced in the doc.

### Required gates
- `tests/quality/test_observability_setup_doc.py`:
  - doc exists; references every alert by name.
  - lists every metric in `RuntimeCounterMetric` / `RuntimeLatencyMetric`.

### ETA
0.25 day.

---

# Lane C — OPT-19 first slice: parameter-sweep optimizer

## OPT-19 — Sequential grid optimizer (first slice)

### Goal
A `qts.research.optimizer` subpackage runs a strategy through `BacktestEngine`
against a grid of parameter combinations. Each run produces a backtest
manifest and a captured Sharpe ratio. Results are ranked by the configured
objective and returned to the caller.

### Domain fact / invariant
The optimizer is a thin orchestrator over `BacktestEngine`. It must use the
same engine + same risk + same execution adapter the user gets in normal
backtests. No parallel "fast path".

### Correct owner / boundary
- `qts.research.optimizer.parameter_space` — `ParameterSpace` (single dim)
  and `ParameterGrid` (cartesian product over multiple spaces).
- `qts.research.optimizer.job` — `OptimizationJob` (strategy factory +
  bars factory + parameter grid + objective metric name).
- `qts.research.optimizer.runner` — `OptimizationRunner.run(job)` returns
  `tuple[OptimizationResult, ...]` sorted by objective descending.
- `qts.research.optimizer.result` — `OptimizationResult` (parameter values,
  manifest_path, objective_value, manifest_hash).

### Forbidden shortcut
Bypassing `BacktestEngine`; building a "fast" backtest mode for the optimizer;
in-memory sharing of strategy state across runs.

### Scope (first slice — sequential, single dim)
- `ParameterSpace(name: str, values: tuple[T, ...])`
- `ParameterGrid(*spaces: ParameterSpace)` yields `dict[str, Any]` combinations
- `StrategyFactory = Callable[[Mapping[str, Any]], Strategy]`
- `OptimizationJob`:
  - `strategy_factory: StrategyFactory`
  - `bars_factory: Callable[[], Iterable[Bar]]`
  - `initial_cash: Decimal`
  - `parameter_grid: ParameterGrid`
  - `objective_metric: str` (default `"sharpe_ratio"`)
  - `output_root: Path`
- `OptimizationRunner.run(job)`:
  - iterates combinations sequentially
  - per combination: build strategy via factory, build fresh bars via factory,
    run `BacktestEngine.run_streaming(output_root / f"run-{i}")`,
    parse manifest.json for objective metric
  - returns results sorted by objective descending
- No concurrency, no walk-forward, no Bayesian — those are follow-up slices.

### Required gates
- `tests/integration/test_optimization_runner_grid_sweep.py`:
  - 2-parameter grid (e.g. 2 windows × 2 thresholds = 4 combinations)
  - run produces 4 `OptimizationResult` rows
  - each has distinct `manifest_hash`
  - results are sorted by objective descending
  - the highest-objective result matches by hand-computed Sharpe direction
- `tests/unit/research/test_parameter_grid.py`:
  - grid yields cartesian product in stable order
  - empty space rejected
  - duplicate parameter names across spaces rejected

### ETA
1.5-2 days.

---

## 3. Execution lanes (parallel)

| Lane | Owner | Files | Exit evidence |
|---|---|---|---|
| A | Main session | `qts.runtime.event_migrations`, `qts.runtime.event_store`, `qts.observability.metrics`, runtime coordinator, backtest sink | OPT-56 + 57 green |
| B | Main session | `qts.api.routes.health`, `configs/alerts/`, `docs/operations/` | OPT-58.A + B + C green |
| C | Main session | `qts.research.optimizer/*`, `scripts/run_optimizer.py` (optional) | OPT-19 first-slice green |

The three lanes touch disjoint roots and can land in any order. Within Lane A
OPT-56 lands before OPT-57 (both use `InMemoryEventStore` defaults; 56's
canonical registry simplifies 57's wiring).

## 4. Verification commands

```bash
PYTHONPATH=backend/src uv run pytest tests/anchor tests/integration tests/unit tests/quality -q
make guardrails
make typecheck
make lint
make check
```

## 5. Out of scope (explicit defer)

- **OPT-58.D** — Grafana JSON dashboard (requires hands-on tuning against
  real ops Grafana; pure-config artifact is brittle without that).
- **OPT-58.E** — `strategy_id` / `account_id` metric labels (touches every
  `record_runtime_event` call site; do as OPT-58 follow-up).
- **OPT-19.B** — Concurrency (concurrent.futures parallelism for grid).
- **OPT-19.C** — Walk-forward window protocol.
- **OPT-19.D** — Random search / Bayesian optimization.
- **OPT-19.E** — CLI wrapper script.

These follow-ups stay in the backlog and land after the first slice ships.

## 6. How this plan is used

- Each item is referenced by ID in PR titles.
- Status flips to `IN-PROGRESS` when work starts and to `DONE` with commit
  hash when verified green.
- New gaps discovered during this work go to the source backlog with the next
  free OPT-NN; no renumbering.
