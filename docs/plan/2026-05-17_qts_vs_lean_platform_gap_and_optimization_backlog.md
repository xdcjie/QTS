# QTS vs Lean — Platform Gap Analysis and Optimization Backlog

- Document type: review + backlog
- Owner: TBD
- Created: 2026-05-17
- Source analysis: code graph (4378 nodes / 530 files / 210 test files), architecture docs under `docs/architecture/`, `docs/strategy_sdk/`, `backend/src/qts/strategy_sdk/`, `backend/src/qts/runtime/`, `backend/src/qts/quality/guardrails.py`
- Reference: QuantConnect / Lean (`IAlgorithm`, `Slice`, `IDataConsolidator`, Universe Selection, Risk Management Model, Brokerage Model, Indicators library, LEAN Optimizer)

This document is the single entry point for the next round of platform optimization. Each item carries a stable ID (`OPT-XX`) so it can be referenced from PRs, ADRs, and follow-up plans without renumbering.

---

## 1. Scorecard

| Dimension | Status | Notes |
|---|---|---|
| Layering / DDD | Strong | 12-layer split documented in `docs/architecture/system_overview.md` |
| Backtest / Paper / Live parity | Strong | `docs/architecture/backtest_live_parity.md` is more explicit than Lean's equivalent |
| Architecture guardrails as code | Strong | `quality/guardrails.py` enforces 30+ AST rules |
| Actor runtime + multi-account partitioning | Strong | ADR-0001; partitioning by `AccountId` |
| Numeric correctness | Strong | `Decimal` end-to-end |
| Symbol discipline | Strong | `InstrumentId` enforced at core boundary |
| Test infrastructure | Strong | anchor / replay / soak / reconciliation tiers; 9408 TESTED_BY edges |
| Strategy SDK type ergonomics | Weak | Callbacks typed as `object`; example strategies fall back to `Any` |
| Indicator coverage | Weak | 6 indicators (SMA, EMA, ATR, RSI, SessionVWAP, VolumeRatio) vs Lean 100+ |
| Cross-timeframe consolidator | Missing | Only provider->strategy two-axis aggregation; no chained consolidator primitive |
| Universe Selection | Missing | Mentioned in docs, not present in code |
| Brokerage Model breadth | Partial | `broker_capabilities_for_model` exists; cost/margin model thin |
| Risk rule breadth | Weak | Only `MaxNotionalRule` wired into the backtest engine |
| Frontend depth | Weak | 13 .ts/tsx files, 0 frontend tests, hand-written DTOs |
| Observability / SLI | Partial | `metrics.py` 6.4KB; no OTel; latency per stage not tracked |
| Optimizer / walk-forward | Missing | No parameter-sweep or WFO framework |
| Research notebook lib | Partial | `research/` placeholder; no `QuantBook`-style API |
| Options pricing / Greeks | Missing | `OptionContractRef` exists, no pricing model |
| Historical data format | Partial | CSV + single Parquet store; no Arrow/Polars/DuckDB path |
| Freeze-exception debt | Watch item | `platform_freeze_exceptions.yaml` is 36 KB and growing |

---

## 2. Lean Comparison Matrix

| Lean capability | QTS current state | Gap |
|---|---|---|
| `IAlgorithm` + strongly-typed `Slice` callback | `Strategy` with `object` callbacks | Large |
| `Securities[symbol]` unified portfolio/price view | `PortfolioView` skeleton | Medium |
| `IDataConsolidator` for cross-timeframe synthesis | Provider->strategy only | Large |
| 100+ built-in indicators | 6 | Large |
| Universe Selection framework | Doc-only | Large |
| Brokerage Model (fees, margin, capabilities) | `broker_capabilities_for_model` only | Medium |
| Risk Management Model framework | `RiskEngine` + 1 rule | Medium |
| Options Greeks / pricing model | Not present | Large |
| LEAN Optimizer (sweep + walk-forward) | Not present | Large |
| QuantBook research API | `research/` placeholder | Medium |
| Charting API | Not present | Medium |
| Actor runtime + multi-account partitioning | Present, stronger than Lean | QTS leads |
| Backtest/Live parity formalized | Present, stronger than Lean | QTS leads |
| Guardrails as code | Present, stronger than Lean | QTS leads |

---

## 3. Optimization Backlog

Status legend: `TODO` / `IN-PROGRESS` / `BLOCKED` / `DONE`
Priority: P0 (next sprint) > P1 (next quarter) > P2 (when capacity) > P3 (watch)

### P0 — SDK ergonomics and hot-path correctness

#### OPT-01 — Strongly-type the Strategy SDK callbacks
- Status: DONE
- Review status matrix: `docs/plan/qts_vs_lean_p0_review_status_matrix.md`
- Files: `backend/src/qts/strategy_sdk/strategy.py:9-31`, `examples/strategies/vwap_pullback.py` (uses `Any`)
- Problem: `Strategy.initialize/on_bar/on_tick/on_timer/on_order_update/on_fill/finalize` declare every parameter as `object`. Strategy authors lose IDE completion and mypy coverage. The example strategy works around this with `Any`.
- Proposal: switch to typed signatures using `StrategyContext`, `Bar`, `Tick`, `Timer`, `OrderUpdate`, `Fill`. Consider a `Protocol` to keep the SDK open for testing fakes. Bump example strategies to drop `Any`.
- Acceptance: `examples/strategies/vwap_pullback.py` mypy-clean without `Any`; `strategy_api.md` updated.
- ETA: 1 week
- Depends on: nothing
- Risk: low

#### OPT-02 — Decompose `RuntimeMarketDataCoordinator.on_market_data` (282 lines, hot path)
- Status: DONE
- Review status matrix: `docs/plan/qts_vs_lean_p0_review_status_matrix.md`
- Files: `backend/src/qts/runtime/market_data_coordinator.py:61`
- Problem: every market data event traverses this monolithic function. Hard to profile, hard to test individual stages, currently flagged as untested hotspot (degree 57).
- Proposal: split into composable stages (normalize -> route -> derive-bar -> trigger-strategy). Each stage gets its own unit tests.
- Acceptance: function under 80 lines; each stage covered by unit tests; replay anchor tests unchanged.
- ETA: 1-2 weeks
- Depends on: nothing
- Risk: medium (hot path; regression risk in event ordering)

#### OPT-03 — Decompose `BacktestActorLoop.run` (308 lines)
- Status: DONE
- Review status matrix: `docs/plan/qts_vs_lean_p0_review_status_matrix.md`
- Files: `backend/src/qts/backtest/actor_loop.py:129`
- Problem: longest function in backend; untested hotspot (degree 67).
- Proposal: extract phases (warmup -> trading -> finalize) and per-bar tick into separate methods; introduce a `BacktestPhase` enum if useful.
- Acceptance: `run` under 80 lines; no behavioral change anchored by existing `tests/anchor/` and `tests/integration/test_paper_runtime_full_chain.py`.
- ETA: 1 week
- Depends on: nothing
- Risk: medium

### P1 — Module health and breadth

#### OPT-04 — Split `quality/guardrails.py` (2873 lines)
- Status: DONE
- Review status matrix: `docs/plan/qts_vs_lean_p1_module_health_review_status_matrix.md`
- Files: `backend/src/qts/quality/guardrails.py`
- Problem: single file holds 30+ rule classes; violates its own complexity-budget philosophy; review cost high; change concurrency low.
- Proposal: split into `qts/quality/rules/{imports,oop,naming,inventory,boundary,placeholder,...}.py` + `qts/quality/suite.py` registry. Keep public entrypoint `run_guardrails` stable for `scripts/verify_guardrails.py`.
- Acceptance: every rule lives in a sub-module; `run_guardrails` unchanged externally; tests in `tests/unit/scripts/test_verify_guardrails.py` still green.
- ETA: 2 weeks
- Depends on: nothing
- Risk: low (mechanical refactor, but large)

#### OPT-05 — Decompose `BrokerRuntimeStartupChecklist.from_config` (172 lines)
- Status: DONE
- Review status matrix: `docs/plan/qts_vs_lean_p1_module_health_review_status_matrix.md`
- Files: `backend/src/qts/runtime/broker_startup.py:56`
- Proposal: turn `from_config` into a Builder; each broker subsystem (data, execution, capital, reconciliation) gets its own builder section.
- ETA: 1 week
- Risk: medium

#### OPT-06 — Decompose `RuntimeTopologyBuilder.from_live_config` (101 lines)
- Status: DONE
- Review status matrix: `docs/plan/qts_vs_lean_p1_module_health_review_status_matrix.md`
- Files: `backend/src/qts/runtime/topology.py:346`
- ETA: 0.5 week

#### OPT-07 — Add core indicators to reach an industrial baseline
- Status: DONE
- Review status matrix: `docs/plan/qts_vs_lean_p1_module_health_review_status_matrix.md`
- Files: `backend/src/qts/indicators/`, `backend/src/qts/strategy_sdk/indicators.py`
- Proposal — add these 12, grouped:
  - Trend: MACD, Bollinger Bands, ADX, Keltner Channel, Donchian Channel
  - Momentum: Stochastic, CCI, Williams %R, Rate of Change
  - Volatility: Standard Deviation, Historical Volatility
  - Volume: OBV, MFI, A/D, Chaikin Money Flow
- Acceptance: each indicator has a numerical anchor test vs a known-good reference (TA-Lib or Lean fixture); registered in `IndicatorFactory`; documented in `docs/strategy_sdk/indicator_model.md`.
- ETA: 2-3 weeks
- Depends on: nothing

#### OPT-08 — Introduce a Consolidator primitive for cross-timeframe synthesis
- Status: DONE
- Review status matrix: `docs/plan/qts_vs_lean_p1_module_health_review_status_matrix.md`
- Files: new `backend/src/qts/data/bars/consolidator.py`, integrate with `runtime/market_data_coordinator.py`
- Problem: currently only the provider physical / strategy logical two-axis exists. Strategies that want 1m + 5m + 1h cannot chain consolidators.
- Proposal: `Consolidator` protocol (input bar/tick -> emit derived bar). Compose: `TickConsolidator -> 1mBar -> NMinuteConsolidator -> 5mBar`. Backed by `RuntimeMarketDataCoordinator`.
- Acceptance: a multi-timeframe example strategy exists; anchor test verifies derived 5m bars equal the historical 5m fixture from 1m source.
- ETA: 2-3 weeks
- Depends on: OPT-02 helps but not required

#### OPT-09 — Pluginize risk rules and add the standard 5
- Status: DONE
- Review status matrix: `docs/plan/qts_vs_lean_p1_module_health_review_status_matrix.md`
- Files: `backend/src/qts/risk/rules/`, `backend/src/qts/risk/risk_engine.py`
- Problem: only `MaxNotionalRule` is wired into the backtest engine; production live needs more.
- Proposal — 5 anchor rules with config:
  1. PositionLimit (per instrument and per asset class)
  2. LeverageLimit (gross + net)
  3. IntradayLossLimit (rolling drawdown -> trip kill switch)
  4. ConcentrationLimit (sector / single-issuer)
  5. VolatilityAdjustedSizing (ATR-based notional cap)
- Acceptance: each rule has an anchor test proving it rejects a violating intent; `RuleRegistry` loads from YAML; `RiskEngine` runs all in the order declared by config.
- ETA: 2 weeks
- Depends on: nothing

#### OPT-10 — Brokerage Model: fees, margin, capabilities matrix
- Status: DONE
- Review status matrix: `docs/plan/qts_vs_lean_p1_module_health_review_status_matrix.md`
- Files: `backend/src/qts/execution/adapters/`, new `qts/execution/brokerage_model.py`
- Proposal: `BrokerageModel` aggregates `FeeModel`, `MarginModel`, `SlippageModel`, `CapabilityMatrix`. IBKR ships first; backtest sim uses a default. Capabilities table feeds `RiskEngine.requires_live_market_data` and order capability checks already in place.
- ETA: 2 weeks
- Depends on: OPT-09 helps with margin rule integration

#### OPT-11 — Universe Selection framework
- Status: DONE
- Review status matrix: `docs/plan/qts_vs_lean_p1_module_health_review_status_matrix.md`
- Files: new `backend/src/qts/strategy_sdk/universe.py`, integrate with `MarketDataCoordinator`
- Problem: `Universe` is named in `docs/strategy_sdk/strategy_api.md` but absent from code.
- Proposal: `UniverseSelector` protocol returning a set of `InstrumentId` at scheduled intervals; the runtime materializes the subscription delta.
- Acceptance: one fundamental and one technical (top-N volume) selector ship with anchor tests; strategy can declare `ctx.set_universe(...)`.
- ETA: 2-3 weeks
- Depends on: OPT-08 (Consolidator) helps but not required

### P1 — Frontend and DX

#### OPT-12 — OpenAPI -> TS types pipeline
- Status: DONE
- Review status matrix: `docs/plan/qts_vs_lean_p1_frontend_dx_review_status_matrix.md`
- Files: `backend/src/qts/api/`, `backend/scripts/generate_openapi_json.py`, `frontend/src/api/`, `frontend/package.json`
- Problem: FastAPI emits OpenAPI; frontend types are hand-written; DTO drift is inevitable.
- Proposal: build step running `openapi-typescript` against `/openapi.json`; replace hand-written DTOs in `frontend/src/api/`.
- ETA: 3 days

#### OPT-13 — Frontend test baseline (vitest + Playwright smoke)
- Status: DONE
- Review status matrix: `docs/plan/qts_vs_lean_p1_frontend_dx_review_status_matrix.md`
- Problem: 0 frontend tests; high-degree `App` component is untested.
- Proposal: vitest for component logic, Playwright headless for one smoke test per route (Dashboard, BacktestLab, StrategyManagement, Operations).
- ETA: 1 week

#### OPT-14 — WebSocket client robustness
- Status: DONE
- Review status matrix: `docs/plan/qts_vs_lean_p1_frontend_dx_review_status_matrix.md`
- Files: `frontend/src/` (find/create ws client), `backend/src/qts/api/websocket/manager.py`
- Proposal: standardize a client wrapper with reconnect, sequence-number gap detection, and buffered replay. Document the wire contract.
- ETA: 1 week

### P2 — Observability and ops

#### OPT-15 — Latency and queue-depth SLI metrics
- Status: TODO
- Files: `backend/src/qts/observability/metrics.py`, runtime actors
- Proposal: instrument actor mailbox depth, event-to-order latency, reconciliation lag. Expose as Prometheus counters/histograms.
- ETA: 1.5 weeks

#### OPT-16 — OpenTelemetry tracing on the order lifecycle
- Status: TODO
- Proposal: span per `RuntimeEvent` traversal (market data -> strategy -> intent -> risk -> order -> exec -> fill). Sampled in live; deterministic in backtest.
- ETA: 2 weeks
- Depends on: OPT-15

#### OPT-17 — Runtime event schema versioning
- Status: TODO
- Files: `backend/src/qts/runtime/event_store.py`, `runtime/sinks/base.py`
- Problem: events are written without an explicit `schema_version`. Future schema changes will be hard to replay.
- Proposal: embed `schema_version` in every `RuntimeEvent` envelope; add a migration registry on the reader path.
- ETA: 1 week

#### OPT-18 — Reap `platform_freeze_exceptions.yaml`
- Status: TODO
- Files: `docs/architecture/platform_freeze_exceptions.yaml` (currently 36 KB)
- Problem: exception list is monotonically growing; some entries are likely stale.
- Proposal: each exception gets an `expires_on` and a `re-evaluate` reason; CI fails on expired exceptions.
- ETA: 1 week
- Risk: low

### P2 — Research and quant tooling

#### OPT-19 — Walk-forward / parameter-sweep optimizer
- Status: TODO
- Files: new `backend/src/qts/research/optimizer/`
- Proposal: grid + random + Bayesian search runners; walk-forward window protocol; CLI to launch parallel backtests; output artifacts indexed by parameter hash.
- ETA: 3-4 weeks
- Depends on: stable backtest engine entrypoints

#### OPT-20 — QuantBook-style research API
- Status: TODO
- Files: `backend/src/qts/research/`
- Proposal: Jupyter-friendly API exposing `History(symbol, n, timeframe)`, indicator factory in research mode, fast Parquet/Arrow path on top of `data/historical/`.
- ETA: 2-3 weeks
- Depends on: OPT-22 (Arrow path) is a strong enabler

#### OPT-21 — Options pricing and Greeks
- Status: TODO
- Files: new `backend/src/qts/domain/options/pricing.py`
- Proposal: Black-Scholes + binomial fallback; Greeks computed from market data; integrate with `OptionContractRef`. Risk rules can then operate on delta/gamma exposure.
- ETA: 3 weeks
- Risk: medium (correctness-critical; needs reference fixtures)

### P2 — Data layer

#### OPT-22 — Arrow/Polars/DuckDB historical path
- Status: TODO
- Files: `backend/src/qts/data/historical/`, `backend/src/qts/data/stores/parquet_store.py`
- Problem: `csv_dataset.py` (462 lines) + `replay_market_data_source.py` (678 lines) — read path is heavy on pandas/manual CSV.
- Proposal: introduce an Arrow-backed read path; CSV becomes an ingestion-only format. Polars or DuckDB for scan/filter; lazy.
- ETA: 3 weeks
- Risk: medium (replay determinism must be preserved; anchor tests will catch regressions)

### P3 — Graph and dev tools

#### OPT-23 — Run `embed_graph_tool` to enable semantic search
- Status: TODO
- Proposal: pick a small local model (e.g. `all-MiniLM-L6-v2`); re-embed weekly via existing hook.
- ETA: 1 day

#### OPT-24 — Tune community detection in `code-review-graph`
- Status: TODO
- Problem: 7 communities cover only 53 of 4378 nodes; 0 cross-community edges. The graph isn't reflecting actual module coupling.
- Proposal: adjust Leiden resolution or switch to file-based grouping; re-evaluate `get_surprising_connections` afterwards.
- ETA: 0.5 day

---

## 4. What we explicitly want to keep (do NOT regress)

Anchored in `docs/architecture/backtest_live_parity.md` and the guardrails:

1. Strategies emit intents only; no direct order creation.
2. Risk runs before order submission in every mode.
3. `OrderManagerActor` owns order state in every mode.
4. `AccountActor` owns cash and positions in every mode.
5. Broker symbols stay at adapter boundaries; core uses `InstrumentId`.
6. Continuous futures resolve to concrete contracts before order creation.
7. Backtest cannot use a shortcut that live cannot use.
8. Decimal end-to-end for monetary and price math.

Any optimization in this backlog that touches the shared core flow must be accompanied by anchor-test evidence that these invariants still hold.

---

## 5. Suggested sequencing (first two months)

| Week | Items | Theme |
|---|---|---|
| 1 | OPT-01, OPT-23, OPT-24 | SDK ergonomics + dev tools warm-up |
| 2-3 | OPT-03, OPT-06, OPT-12 | Hot-path decomposition + frontend type pipeline |
| 4-5 | OPT-02, OPT-13 | Coordinator decomposition + frontend test baseline |
| 6-8 | OPT-04, OPT-09 | Guardrails split + risk rule pluginization |
| 8-10 | OPT-07, OPT-08 | Indicator breadth + Consolidator primitive |
| 10-12 | OPT-10, OPT-17 | Brokerage Model + event schema versioning |

OPT-11, OPT-19, OPT-20, OPT-21, OPT-22 follow once the above lands.

---

## 6. How this document is used

- Each item is referenced by ID in PR titles, e.g. `OPT-01: type Strategy callbacks`.
- When an item kicks off, change its `Status:` to `IN-PROGRESS` and add a link to the implementing plan under `docs/plan/`.
- When an item completes, change to `DONE` and link the merged PR.
- New optimization items go to the end with the next free `OPT-NN`. Do not renumber.
- This document is not a roadmap; it is a backlog. The roadmap lives in `docs/plan/implementation_plan.md` and the freeze/readiness matrices.
