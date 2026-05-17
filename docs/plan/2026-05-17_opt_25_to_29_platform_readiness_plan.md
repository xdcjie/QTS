# OPT-25 / 26 / 27 / 29 — Platform Readiness Plan

- Document type: plan (detailed)
- Owner: TBD
- Created: 2026-05-17
- Backlog: `docs/plan/2026-05-17_qts_vs_lean_platform_gap_and_optimization_backlog.md`
- Prior milestone: P0 (OPT-01..03) + P1 module health (OPT-04..11) — both DONE
- Scope: the four items that block QTS from being usable as a real internal trading platform — backtest statistics, holdings PnL, order types/TIF, API security baseline.

## 0. Why these four, why now

OPT-01..11 made the SDK ergonomic and the runtime modular. They did **not** make
the platform usable end-to-end:

1. `reporting/backtest.py` only produces `total_return` and `max_drawdown` — there
   is no Sharpe, Sortino, win-rate, profit factor, exposure, or trade-level
   statistic. Without a target function, the Optimizer (OPT-19) cannot ship.
2. Portfolio holdings now require average cost, realized/unrealized PnL, and
   holding-period semantics as first-class account state.
   Strategies that exit on PnL or rebalance by equity can't be expressed.
3. `BrokerOrderType` is `{MARKET, LIMIT, STOP}` and `TimeInForce` is `{DAY, GTC, IOC}`
   (`backend/src/qts/execution/broker.py:134-148`). Worse, `BrokerOrderRequest`
   has no `order_type` / `time_in_force` / `limit_price` / `stop_price` fields at
   all (`broker.py:150-167`) — so the IBKR adapter takes them as method
   parameters with a `MARKET / DAY` default. Internal order intent
   (`domain/orders/value_objects.py:33-46`) also has no order type.
4. `api/app.py` (`backend/src/qts/api/app.py:18-28`) wires routers with **no auth
   middleware, no CORS, no rate limit**. The only "auth" is a literal string
   comparison on the `Authorization` header in `operations.py:36-40`. The API
   cannot be exposed to anything beyond loopback today.

Together these four are the minimum readiness bar. Estimated wall clock: 5-6
weeks if run sequentially in the order in this document.

## 1. Non-negotiable platform invariants

Any OPT-25..29 work that touches the shared runtime must keep these alive
(anchored in `docs/architecture/backtest_live_parity.md`):

| # | Invariant | Anchor |
|---|---|---|
| 1 | Strategies emit intents only; no direct order creation. | `qts.strategy_sdk.context.StrategyContext` |
| 2 | Risk runs before order submission in every mode. | `qts.risk.RiskEngine` |
| 3 | `OrderManagerActor` owns order state in every mode. | `qts.execution.order_manager` |
| 4 | `AccountActor` owns cash and positions in every mode. | `qts.runtime.actors.account_actor` |
| 5 | Broker symbols stay at adapter boundaries; core uses `InstrumentId`. | `qts.execution.adapters.*` |
| 6 | Decimal end-to-end for monetary and price math. | guardrails |
| 7 | Backtest cannot use a shortcut that live cannot use. | parity doc |
| 8 | Every cross-cutting change needs a first failing test or guardrail. | matrix style |

These supersede any item-level acceptance below.

---

# OPT-25 — Backtest statistics expansion

## Goal

When a backtest finishes, the manifest and `BacktestArtifacts` expose the
**standard quantitative performance statistics** that an internal team would
use to compare strategies and that the future Optimizer (OPT-19) can use as a
target function. Streaming computation; no second pass over the equity curve;
no breakage of existing `manifest_hash` / `report_hash` semantics.

## Scope

In:

- A new `qts.reporting.statistics` module that computes the metrics below
  incrementally from the equity curve, trade ledger, and fill stream.
- Wire `BacktestArtifactWriter` to feed the new computer alongside the existing
  `StreamingEquityMetrics` (`backend/src/qts/reporting/backtest.py:114-150`).
- Manifest gains a `statistics:` section (additive, behind the existing
  `report_hash`).
- New artifact `<run_id>.statistics.json` next to existing ones.
- `BacktestArtifactReader` / `backtest_analyst.py` reads and renders the new
  payload (HTML report and CLI summary).

Out:

- WFO / parameter-sweep search (that's OPT-19; this is its prerequisite).
- Per-symbol attribution beyond simple position-side breakdown (defer).
- Benchmark-relative metrics (alpha/beta/IR) — included only if a benchmark
  series is provided in config; otherwise omitted, not faked.

## Metric set (frozen)

Return / equity curve metrics:

- `total_return` (already present)
- `compounding_annual_return` — using actual trading session count from manifest
- `volatility_annual` — std of period returns × √annualization_factor
- `max_drawdown` (already present)
- `max_drawdown_duration_bars`
- `calmar_ratio` = CAR / |MDD|

Risk-adjusted metrics:

- `sharpe_ratio` = (mean_excess_return / std) × √annualization_factor
- `sortino_ratio` = (mean_excess_return / downside_std) × √annualization_factor
- `probabilistic_sharpe_ratio` (López de Prado formulation)

Trade-level metrics (computed from `trade_ledger` + `fills` + close-outs):

- `total_trades`, `total_orders`
- `win_rate`, `loss_rate`
- `avg_win`, `avg_loss`, `largest_win`, `largest_loss`
- `profit_factor` = Σwins / |Σlosses|
- `expectancy` = win_rate × avg_win − loss_rate × |avg_loss|
- `avg_holding_period_bars`

Exposure metrics:

- `time_in_market` = fraction of bars with at least one open position
- `avg_gross_exposure`, `avg_net_exposure` (notional / equity)

Cost metrics (audit):

- `total_commission`, `total_slippage`
- `commission_per_trade`, `slippage_per_trade`

Benchmark metrics (only if `benchmark_series` is supplied):

- `alpha_annual`, `beta`, `information_ratio`, `tracking_error_annual`

Annualization factor comes from manifest fields `trading_bars` and
`bars_per_year` (computed from the dataset's session calendar). Default
fallback: 252 days × bars_per_day inferred from `target_timeframe`.

## Design

```
backend/src/qts/reporting/statistics/
    __init__.py
    streaming_returns.py        # incremental return + variance + downside variance
    streaming_drawdown.py       # max drawdown, duration
    trade_aggregator.py         # converts fills -> closed trades, accumulates win/loss
    exposure_tracker.py         # time-in-market, gross/net notional
    cost_aggregator.py          # commission + slippage
    benchmark_aligner.py        # optional benchmark series, computes alpha/beta/IR
    statistics_builder.py       # the only public type — pulls the above together
    payload.py                  # frozen dataclass + serialization
```

`StatisticsBuilder` is fed incrementally by `BacktestArtifactWriter`:

- `on_equity_point(point)` — returns + drawdown
- `on_fill(order_id, fill, instrument, multiplier)` — costs + trade aggregator
- `on_position_close(closed_trade)` — fired by Holdings (depends on **OPT-26**)
- `finalize(manifest_fields, benchmark_series=None) -> StatisticsPayload`

Decimal-clean: every accumulator is `Decimal`. `to_payload()` serializes via
`stable_json_default` so the result is hashable for `report_hash`.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Trade-level metrics need a "closed trade" notion that does not exist yet. | OPT-25 trade aggregator depends on **OPT-26** Holdings emitting `PositionClosed` events. Sequence OPT-26 → OPT-25 trade-level part. Risk-adjusted return metrics ship before trade-level metrics if needed. |
| Sharpe/Sortino on coarse bars (e.g. 1d) is noisy. | Always emit `points` and `annualization_factor` in the payload so downstream knows the sample. Anchor against scipy on a fixture. |
| Float vs Decimal in std/variance. | Use Welford's algorithm with Decimal — numerically stable, no float intermediates. |
| Benchmark calendar mismatch. | `benchmark_aligner.py` aligns on `(session_id, bar_start)` and refuses to align if coverage <90% of strategy bars. |

## Acceptance / Evidence

The following must be true before OPT-25 is marked DONE:

1. **First red gate** (write before any production edits) —
   `tests/unit/reporting/test_statistics_payload_shape.py` asserts every key in
   the metric set above is present in `StatisticsPayload`. This **must** fail
   first.

2. **Streaming-vs-batch anchor** —
   `tests/unit/reporting/test_streaming_statistics_anchor.py` builds a known
   equity curve fixture (`tests/fixtures/statistics/known_equity.json`) where
   the expected Sharpe / Sortino / Calmar / MDD were independently computed
   with NumPy + scipy. Streaming output must match to `Decimal('1e-10')`.

3. **Trade-level anchor** —
   `tests/unit/reporting/test_trade_level_statistics.py` runs a fixture of 20
   round-trip trades with known win/loss/expectancy and asserts every
   trade-level metric.

4. **Benchmark optional path** — when benchmark omitted, payload omits
   `alpha_annual` / `beta` / `information_ratio` / `tracking_error_annual`
   (the keys must be absent, not `null`). Asserted in
   `test_statistics_payload_shape.py`.

5. **Manifest hash stability** — adding the `statistics` section under a new
   sub-key keeps the manifest validator green
   (`_validate_m1_backtest_manifest` in `backend/src/qts/reporting/backtest.py:432`).
   New invariant test: replaying a fixture run with `statistics` removed must
   still pass schema validation; with `statistics` present must include
   `statistics_hash` in the report payload.

6. **Backtest end-to-end** —
   `tests/integration/test_backtest_engine_flow.py` rerun must include
   non-empty `statistics_hash` for any run with `processed_bars > 0`.

7. **Reporter integration** — `backtest_analyst.py` HTML render shows at least
   Sharpe, Sortino, Calmar, max drawdown, win rate, profit factor as metric
   cards. New anchor: `test_backtest_analyst_renders_extended_statistics.py`.

8. **Determinism** — `tests/replay/test_backtest_determinism.py` extended to
   cover the new statistics payload. Bit-for-bit equal across two replays.

9. **Guardrails / mypy / lint clean**; `make check` green.

### Verification commands

```bash
PYTHONPATH=backend/src uv run pytest tests/unit/reporting -q
PYTHONPATH=backend/src uv run pytest tests/unit/reporting/test_streaming_statistics_anchor.py -q
PYTHONPATH=backend/src uv run pytest tests/integration/test_backtest_engine_flow.py -q
PYTHONPATH=backend/src uv run pytest tests/replay/test_backtest_determinism.py -q
make check
```

### ETA

1.5 weeks calendar time. Equity-curve metrics ship in week 1; trade-level
metrics ship as a second slice once OPT-26 lands.

---

# OPT-26 — Holdings / SecurityHolding model

## Goal

Use the `Holdings` model as the account-owned position state that tracks
**average cost, market value, realized PnL, unrealized PnL, and emits a
`PositionClosed` event** when a position flips through flat. Strategies and
risk rules can read this without re-deriving it from fill streams. Backtest
parity holds (the same Holdings is consumed live).

## Scope

In:

- New `qts.portfolio.holdings.Holding` (immutable snapshot) and
  `qts.portfolio.holdings.HoldingBook` (mutable, owned by AccountActor).
- `FillAccounting.apply` (`backend/src/qts/portfolio/accounting/fill_accounting.py:45-54`)
  becomes a thin dispatcher that updates `HoldingBook` + `CashBook` in lock-step.
- `AccountSnapshot` (`backend/src/qts/runtime/actors/account_actor.py:27-35`)
  exposes `holdings: Mapping[InstrumentId, Holding]`; the `positions` accessor
  is a quantity view derived from holdings for current account state only.
- `qts.strategy_sdk.portfolio_view.PortfolioView` gains
  `unrealized_pnl(asset) / realized_pnl(asset) / avg_cost(asset) / holding_period(asset)`.
- `PositionClosed` runtime event emitted by AccountActor when a holding goes
  from non-flat to flat. Sink writers persist it next to fills.

Out:

- Multi-leg basis tracking (combos / options spreads) — defer until OPT-21.
- Tax-lot accounting (FIFO/LIFO/SpecificID) — defer; add a single
  `cost_basis_method` enum stub so the field can be added later without a
  schema break.
- Cross-currency holding consolidation — defer.

## Holding shape (frozen)

```python
@dataclass(frozen=True, slots=True)
class Holding:
    instrument_id: InstrumentId
    quantity: Decimal                # signed
    average_cost: Decimal            # in instrument currency, weighted by signed quantity
    realized_pnl: Decimal            # cumulative, never resets
    cost_basis_method: CostBasisMethod = CostBasisMethod.AVERAGE
    opened_at: datetime | None = None  # set when going from flat to non-flat
    last_fill_at: datetime | None = None

    # Read-only views computed from a market price:
    def market_value(self, mark_price: Decimal, multiplier: Decimal) -> Decimal: ...
    def unrealized_pnl(self, mark_price: Decimal, multiplier: Decimal) -> Decimal: ...
    def holding_period(self, now: datetime) -> timedelta: ...
```

`HoldingBook.apply_fill(fill, instrument)` implements the **weighted average
cost convention**:

- Increase in same direction: `avg_cost = (old_qty*old_avg + fill_qty*fill_price) / new_qty`
  (signed quantity).
- Decrease (closing portion): no change to `avg_cost`; `realized_pnl +=
  closed_qty * (fill_price - avg_cost) * sign * multiplier`.
- Crossing through flat: split into close (realize on whole prior position) and
  open (new direction, `avg_cost = fill_price`); emit `PositionClosed`.

All math is `Decimal`. Cost includes commission? — **No**. Commission lands in
`CashBook` directly (preserving current behavior). This is documented in the
Holding docstring as a deliberate convention.

## Strategy SDK exposure

`StrategyContext` gains (idempotent — read-only proxies into PortfolioView):

```python
def holding(self, asset: AssetRef) -> Holding | None: ...
def unrealized_pnl(self, asset: AssetRef) -> Decimal: ...
def realized_pnl(self, asset: AssetRef) -> Decimal: ...
def avg_cost(self, asset: AssetRef) -> Decimal | None: ...
```

These resolve through `PortfolioView`. They are sticky-typed; no `Any`.

## Sequencing inside OPT-26

1. Slice A: `Holding` + `HoldingBook` + unit anchors (no actor wiring).
2. Slice B: `FillAccounting` rewrite + `AccountActor` snapshot field swap +
   `PortfolioView` accessors.
3. Slice C: `PositionClosed` runtime event + sink wiring + replay determinism
   gate.
4. Slice D: removed position-book module path is blocked by guardrails and all
   callers use holdings.

Each slice is a separate commit. Slice D must not land until anchors for
slices A-C are green.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Average-cost rule errors on direction flips. | Crossing-through-flat is the highest-bug-density branch. Dedicated anchor test with 8 scenarios (long-add, long-reduce, long-close-exact, long-flip-to-short, mirror for short). |
| Existing snapshots in `tests/anchor` carry only `positions:`; tests assume that shape. | Snapshot fixture migration is part of slice B; replay-anchor gate must stay green. |
| Mark price for `unrealized_pnl` must come from somewhere; sourcing it from `PortfolioView` adds coupling. | Mark price is supplied explicitly by the caller (`PortfolioView.mark_price(asset)`); no implicit lookup inside `Holding`. |
| Realized PnL accumulating across an entire run can grow large in long-running live sessions. | Stored as `Decimal`, no precision loss; no compression scheme yet. Document expected magnitude (per-instrument <= 1e12 USD lifetime). |

## Acceptance / Evidence

1. **First red gate** — `tests/unit/portfolio/test_holding_avg_cost_anchor.py`
   covering 8 fill scenarios; must fail before the production module exists.

2. **Crossing-through-flat anchor** —
   `tests/unit/portfolio/test_holding_cross_through_flat.py` asserts the
   `PositionClosed` event is emitted exactly once, the realized PnL is
   correct, and the new position has `avg_cost == fill_price`.

3. **Fill accounting parity** —
   `tests/unit/portfolio/test_fill_accounting.py` asserts cash and holdings
   move in lock-step for fills, commissions, and direction changes.

4. **Account actor snapshot/restore** —
   `tests/unit/runtime/test_account_actor_holdings_snapshot_roundtrip.py`
   asserts `AccountActor.restore(actor.snapshot())` reproduces holdings
   bit-for-bit including `realized_pnl`, `average_cost`, `opened_at`.

5. **Strategy SDK accessor types** — anchor in
   `tests/anchor/test_strategy_sdk_boundaries.py` asserts `ctx.holding`,
   `ctx.unrealized_pnl`, `ctx.realized_pnl`, `ctx.avg_cost` exist with the
   stated signatures (no `Any`, no `object`).

6. **Runtime event schema** — `PositionClosed` registered in the runtime event
   sink with a stable kind constant; replay-anchor confirms event order is
   stable.

7. **No removed import path** — guardrail rule `qts.quality.rules.imports`
   forbids any import of `qts.portfolio.position_book` after slice D.

8. **Backtest determinism** — `tests/replay/test_backtest_determinism.py`
   green with holdings replacing positions (manifest hash will change — that's
   expected; the test reseeds the recorded hash in the same PR).

9. `make check` green; mypy clean; guardrails clean.

### Verification commands

```bash
PYTHONPATH=backend/src uv run pytest tests/unit/portfolio -q
PYTHONPATH=backend/src uv run pytest tests/unit/runtime/test_account_actor_holdings_snapshot_roundtrip.py -q
PYTHONPATH=backend/src uv run pytest tests/anchor tests/replay -q
make check
```

### ETA

2 weeks. Slices A-B in week 1, slices C-D in week 2.

### Dependencies

- **Blocks OPT-25** trade-level metrics (`win_rate`, `profit_factor`, etc.).
- Blocks future risk rule `MaxRealizedDailyLossRule` and `MaxHoldingPeriodRule`.

---

# OPT-27 — Order type and TIF expansion

## Goal

Strategies can express the order shapes a real trader uses (limit, stop, stop-limit,
trailing stop, market-on-open, market-on-close, bracket), through typed SDK
intents that flow as a single piece of metadata from `TargetIntent` → risk →
`OrderManager` → broker adapter — without bypassing existing actor boundaries
and without each strategy reinventing stop/trailing-stop logic locally.

## Current state (verified)

- `BrokerOrderType = {MARKET, LIMIT, STOP}` (`backend/src/qts/execution/broker.py:134-139`).
- `TimeInForce = {DAY, GTC, IOC}` (`broker.py:142-147`).
- `BrokerOrderRequest` has no `order_type`, no TIF, no `limit_price`, no `stop_price`
  fields (`broker.py:150-167`). They are passed through the IBKR adapter as
  method arguments only, defaulting to `MARKET / DAY`
  (`backend/src/qts/execution/adapters/ibkr_order_execution.py:188-189`).
- `OrderIntent` carries only `order_id, instrument_id, side, quantity, account_id`
  (`backend/src/qts/domain/orders/value_objects.py:33-46`).
- `TargetIntent` carries only `asset, intent_type ∈ {PERCENT, QUANTITY, VALUE,
  CLOSE}, value` (`backend/src/qts/strategy_sdk/target.py:12-27`).

So today, **the platform is effectively market-orders-only** despite the LIMIT
and STOP enum constants existing — there is no path from strategy intent to a
limit price.

## Scope

In:

- New types added end-to-end (SDK → intent → risk → broker adapter):
  - `BrokerOrderType`: add `STOP_LIMIT, TRAILING_STOP, MARKET_ON_OPEN,
    MARKET_ON_CLOSE, BRACKET`.
  - `TimeInForce`: add `FOK, GTD, OPG, ATC`.
  - `BrokerOrderRequest` gains:
    `order_type: BrokerOrderType`, `time_in_force: TimeInForce`,
    `limit_price: Decimal | None`, `stop_price: Decimal | None`,
    `trail_amount: Decimal | None`, `trail_percent: Decimal | None`,
    `good_til_date: datetime | None`, `bracket_legs: tuple[BracketLeg, ...] | None`.
  - `OrderIntent` gains the same fields (single source of truth in the domain).
- `TargetIntent` gains an `order_spec: OrderSpec` describing execution shape:
  ```python
  @dataclass(frozen=True, slots=True)
  class OrderSpec:
      order_type: BrokerOrderType = BrokerOrderType.MARKET
      time_in_force: TimeInForce = TimeInForce.DAY
      limit_price: Decimal | None = None
      stop_price: Decimal | None = None
      trail_amount: Decimal | None = None
      trail_percent: Decimal | None = None
      good_til_date: datetime | None = None
      bracket: BracketSpec | None = None
  ```
  Default value = `OrderSpec()` (market / day), preserving current behavior.
  `ctx.target_quantity(...)`, etc. gain a `spec: OrderSpec | None = None`
  keyword argument.
- `BrokerCapabilities.supports_order_type` already exists; extend
  `supported_order_types` defaults for each adapter:
  - `simulated`: all order types (deterministic fill model implemented in OPT-27 itself, see Slice C).
  - IBKR adapter: every type IBKR TWS natively supports.
- Bracket orders modeled as a parent + OCO children. Owned by `OrderManager`
  (no strategy-side OCO bookkeeping).
- Trailing stop tracked by `OrderManager` against last fill / last quote; never
  recomputed in the strategy.

Out:

- Iceberg / hidden / pegged / combo (multi-leg) orders. Combo legs require
  OPT-21 (Options Greeks) to make sense; add an `ICEBERG` enum stub but raise
  `NotImplementedError` in the adapter.
- Smart-order routing / venue selection. QTS today is single-broker per order;
  not part of this item.

## Slicing

1. **Slice A** — types only. Extend `BrokerOrderType` / `TimeInForce` /
   `BrokerOrderRequest` / `OrderIntent` / `OrderSpec`. Wire SDK kwargs through
   `TargetIntent`. No adapter logic. Guardrail-friendly anchor test:
   `tests/anchor/test_order_intent_carries_order_spec.py`.
2. **Slice B** — risk pass-through. `RiskEngine` reads `order_spec` from intent
   without rejecting (existing rules continue to work); add one new rule
   `OrderSpecValidityRule` that rejects combinations the simulated capability
   matrix forbids.
3. **Slice C** — simulated execution adapter implements deterministic fills
   for LIMIT, STOP, STOP_LIMIT, TRAILING_STOP using the bar's
   `[open, high, low, close]`. Fill semantics documented in
   `docs/architecture/execution_simulation.md` (new). Bracket = parent + OCO
   children handled inside `OrderManager`.
4. **Slice D** — IBKR adapter maps every new order type/TIF to the official
   IB enum. Lookup table lives in `qts.execution.adapters.ibkr_order_map`
   (already exists, extended). MOO/MOC require routing flags; documented.
5. **Slice E** — Strategy SDK helpers: `ctx.limit(...)`, `ctx.stop(...)`,
   `ctx.bracket(...)` — thin wrappers that build the right `OrderSpec`.
   Example strategy uses one limit-on-pullback to keep mypy honest.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| `BrokerOrderRequest` schema change ripples through every test fixture. | Default values keep market/day callers untouched; fixtures updated in slice A. |
| Simulated fill semantics for STOP / TRAILING_STOP are tricky on bars. | Anchor doc + 12 bar-fill anchor tests covering touched/not-touched/gap/inside-bar; baselines locked to a Lean reference where possible (their `BackTestingBrokerage.Stop`). |
| Bracket OCO state changes (one child cancels the other) cross actor boundaries. | OCO managed inside `OrderManager` via existing state machine; new state `CANCEL_REQUESTED_OCO`; sibling cancel scheduled via `tell` not direct call. |
| IBKR MOO/MOC requires explicit `tif=OPG` + market-data permissions on certain venues. | `OrderSpec(time_in_force=OPG)` + capability check; readiness gate flags missing permissions before live submit. |
| Broker capability matrix drift between simulated and IBKR. | Each adapter snapshot is recorded in the manifest under `brokerage_model.supported_order_types` — already in `to_manifest_payload`. New replay-anchor refuses to replay if capability matrix doesn't match. |

## Acceptance / Evidence

1. **First red gate** —
   `tests/anchor/test_order_intent_carries_order_spec.py` asserts every
   `OrderIntent` carries a non-None `order_spec` field; must fail today.

2. **Capability matrix anchors** —
   `tests/unit/execution/test_brokerage_capability_full_matrix.py` asserts the
   simulated brokerage supports the full enum set and IBKR brokerage supports
   the documented IBKR subset.

3. **Simulated fill semantics anchors** —
   `tests/anchor/test_simulated_fill_anchors.py` with 12 bar-fill scenarios
   (4 per order type × LIMIT / STOP / STOP_LIMIT) and 8 trailing-stop
   scenarios. Each fill price compared to the documented rule.

4. **Bracket OCO anchor** —
   `tests/anchor/test_bracket_order_oco_anchor.py`. Parent fills → both
   children become live. Profit-target fills → stop-loss cancels (and vice
   versa). Either child rejected → other stays live.

5. **IBKR mapping snapshot** —
   `tests/unit/execution/test_ibkr_order_map_snapshot.py` JSON snapshot of
   every supported `(BrokerOrderType, TimeInForce)` → `ib.Order(...)` mapping.
   Snapshot diffed in CI.

6. **End-to-end SDK** — `examples/strategies/vwap_pullback.py` updated to use
   one bracket entry on long signals; mypy clean; integration test
   `tests/integration/test_backtest_engine_flow.py` produces bracket fill
   stream.

7. **Risk integration** — `OrderSpecValidityRule` rejects an intent with
   `STOP_LIMIT` but no `stop_price`; anchor test
   `tests/unit/risk/test_order_spec_validity_rule.py`.

8. **No legacy path** — guardrail forbids method-parameter passing of
   `order_type` / `time_in_force` in adapter signatures; the only source is
   `OrderIntent.order_spec`. Anchor:
   `tests/quality/test_order_spec_single_source.py`.

9. **Backtest live parity anchor extended** —
   `tests/integration/test_backtest_live_parity_flow.py` includes one limit and
   one stop intent and asserts the same `OrderSpec` ends up in both
   `BrokerOrderRequest` payloads.

10. `make check` green; mypy clean; guardrails clean.

### Verification commands

```bash
PYTHONPATH=backend/src uv run pytest tests/unit/execution tests/unit/strategy_sdk tests/unit/risk -q
PYTHONPATH=backend/src uv run pytest tests/anchor/test_order_intent_carries_order_spec.py tests/anchor/test_simulated_fill_anchors.py tests/anchor/test_bracket_order_oco_anchor.py -q
PYTHONPATH=backend/src uv run pytest tests/integration/test_backtest_live_parity_flow.py -q
make check
```

### ETA

2.5 weeks. Slices A-B week 1; Slice C week 2; Slices D-E half-week each.

### Dependencies

- Blocks any strategy that needs stops, brackets, MOC, or limits — i.e.
  realistic intraday strategies. OPT-25's `slippage_per_trade` and
  `commission_per_trade` are unaffected by this item.

---

# OPT-29 — API security baseline

## Goal

Make the FastAPI surface safe to expose beyond loopback. Every state-changing
endpoint (backtest submit, strategy enable, runtime start/stop/kill, order
submit/cancel) requires an authenticated principal with an explicit scope.
Read-only endpoints require authentication but no scope check. CORS is
explicit, not permissive. Per-principal rate limits exist. The existing
`X-QTS-Operator` header convention is preserved as a *defense-in-depth*
operator-identity audit trail, not as auth.

## Current state (verified)

- `api/app.py:18-28` — `create_app` mounts routers with no middleware, no
  dependency injection of an auth principal.
- `api/routes/operations.py:36-40` — `_require_safety_scope(authorization_scope)`
  checks for the literal string `"runtime:safety:write"` on the
  `Authorization` header. Anyone who knows the header value passes.
- No CORS configuration, no rate limiter, no audit log of unauthenticated calls.

## Scope

In:

- New `qts.api.security` module:
  - `Principal` value object: `id, kind ∈ {service, human}, scopes:
    frozenset[str], session_id, issued_at, expires_at`.
  - `AuthBackend` protocol: `verify(authorization_header) -> Principal`.
  - Two backends:
    - `BearerJWTAuthBackend` — verifies a signed JWT (HS256 by default; RS256
      optional). Keys/secret loaded from env (`QTS_API_JWT_SECRET` /
      `QTS_API_JWT_PUBKEY_PATH`).
    - `StaticTokenAuthBackend` — for CI / local dev only; reads a YAML map of
      `token_hash → Principal` from `configs/api_static_tokens.yaml`.
- FastAPI dependency `get_principal(authorization) -> Principal` mounted on
  every router via `app.dependency_overrides` and `Depends`.
- Scope decorator: `Depends(require_scope("orders:write"))` returns 403 with
  audit log entry if missing.
- Existing `X-QTS-Operator` header stays as an audit attribute on the
  `Principal` (validated to be present + matching for sensitive endpoints).
- CORS via FastAPI `CORSMiddleware`, configured from
  `qts.config.api.ApiSecurityConfig.allowed_origins`. Default = `[]` (no CORS).
- Rate limiting via `slowapi`. Default per-principal limits:
  - reads: 60 req/min
  - writes: 30 req/min
  - safety (kill switch, runtime start/stop): 6 req/min
  - configurable in `ApiSecurityConfig`.
- Audit log: every authenticated call emits a `qts.api.auth_event` runtime
  event with `(principal_id, scope, route, status_code, latency_ms,
  correlation_id)`. Logged through existing `observability/audit.py`.
- One default scope vocabulary:
  - `backtests:read`, `backtests:write`
  - `strategies:read`, `strategies:write`
  - `accounts:read`, `orders:read`, `orders:write`, `orders:cancel`
  - `runtime:read`, `runtime:safety:write`
- `configs/local.yaml` example shows a development static-token setup;
  `configs/api_static_tokens.example.yaml` shipped, real tokens gitignored.

Out:

- OAuth / OIDC / SSO (defer to OPT-29b when an identity provider exists).
- Per-IP allowlist beyond what CORS provides.
- Mutual TLS (defer; reverse proxy concern).
- WebSocket auth handshake — covered in slice E (in scope, but acknowledged
  separately because WS doesn't use the FastAPI `Depends` chain the same way).

## Slicing

1. **Slice A** — `qts.api.security` module + `Principal` + `BearerJWTAuthBackend`
   + `StaticTokenAuthBackend` + unit anchors. No FastAPI integration yet.
2. **Slice B** — `get_principal` dependency + `require_scope` decorator;
   wired into the existing `health` route only as proof; integration tests for
   401 / 403 / 200 paths.
3. **Slice C** — every route mounts the dependency; scope vocabulary applied.
   `operations.py` `_require_safety_scope` replaced by `Depends(require_scope("runtime:safety:write"))`.
4. **Slice D** — CORS middleware + rate limiter wired in `create_app()`.
5. **Slice E** — WebSocket auth in `api/websocket/manager.py`: token in
   `Sec-WebSocket-Protocol` subprotocol header or first JSON message;
   identical scope check.
6. **Slice F** — Audit logging emitted to existing observability pipeline.

## Threat model (explicit)

| Threat | Mitigation in this item | Out of scope |
|---|---|---|
| Unauthenticated trader places live orders | Bearer JWT on `/orders/*`; scope `orders:write`. | n/a |
| Replay of intercepted JWT | Short expiry (default 15 min); `jti` claim deduped via Redis-or-memory replay cache. | Refresh tokens (manual reissue for now). |
| CSRF on browser-issued POST | JWT in `Authorization` header (not cookie); CORS restrictive. | Cookie-based auth. |
| Privilege escalation via altered JWT | HS256 with secret rotation procedure documented; or RS256 with public key pinning. | Hardware key signing. |
| Operator collusion (audit gap) | `X-QTS-Operator` mandatory + recorded in audit; `Principal` recorded in audit; both must match a registry. | Tamper-evident audit log. |
| DoS via flood | Rate limit per principal; static budgets in config. | Network-layer protection. |
| Key leakage in env | Document key rotation; secrets loaded only at startup; never logged. | HSM. |

This threat model lives in `docs/architecture/api_security.md` (new doc).

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Breaking existing local-dev workflows. | Static token backend with one default dev token in `configs/api_static_tokens.example.yaml`; `QTS_PROFILE=local` auto-loads it; documented in README. |
| Rate limiter in single-process FastAPI doesn't share state with future replicas. | Backend = in-memory by default; pluggable Redis backend for prod (configured but not required for OPT-29). |
| Some routes legitimately need to be open (e.g. `/health` for k8s liveness). | Whitelist explicit, documented, audited. Default = closed. |
| `X-QTS-Operator` becoming redundant. | Document that operator is **identity context**, principal is **auth context**; both required for safety routes. |

## Acceptance / Evidence

1. **First red gate** —
   `tests/integration/api/test_api_requires_authentication.py` issues a
   request to every route without auth and asserts 401; must fail today.

2. **Per-route scope anchor** —
   `tests/integration/api/test_api_scope_matrix.py` JSON fixture lists every
   route + required scope; runtime test asserts the same matrix is enforced.
   This file is also the documented spec.

3. **JWT verification anchors** —
   `tests/unit/api/security/test_bearer_jwt_backend.py`:
   - good token → Principal with claims
   - expired token → 401
   - bad signature → 401
   - missing scopes claim → Principal with empty scopes
   - `jti` replay → 401

4. **Static token backend anchor** —
   `tests/unit/api/security/test_static_token_backend.py`:
   - good token → Principal
   - unknown token hash → 401
   - tokens loaded from YAML

5. **CORS contract** —
   `tests/integration/api/test_cors_contract.py`:
   - default config (no origins) → preflight 403
   - configured origin → preflight 200 + correct headers

6. **Rate limit contract** —
   `tests/integration/api/test_rate_limit_contract.py`:
   - exceeding read budget → 429
   - safety budget enforced separately

7. **WebSocket auth** —
   `tests/integration/api/test_ws_auth.py`:
   - missing auth → 4401 close code
   - bad scope on `events.subscribe` → 4403
   - good scope → message flow proceeds

8. **Audit log emission** —
   `tests/unit/observability/test_api_auth_audit_event.py`: every authenticated
   call (and every rejection) produces exactly one audit event with required
   fields.

9. **Threat model doc anchor** —
   `tests/quality/test_api_security_threat_model_doc.py` asserts every threat
   in `docs/architecture/api_security.md` lists a mitigation that exists in
   code; reverse direction checked too.

10. **Configuration anchor** —
    `tests/unit/config/test_api_security_config.py`: rejects empty JWT secret
    in non-local profiles; rejects permissive CORS in non-local profiles.

11. **No legacy path** — `_require_safety_scope` string-comparison helper
    removed; guardrail rule forbids any new HTTPException with `"runtime
    safety scope required"` literal except inside the security module.

12. `make check` green; mypy clean; guardrails clean; integration suite
    green.

### Verification commands

```bash
PYTHONPATH=backend/src uv run pytest tests/unit/api -q
PYTHONPATH=backend/src uv run pytest tests/integration/api -q
PYTHONPATH=backend/src uv run pytest tests/quality/test_api_security_threat_model_doc.py -q
make check
```

### ETA

1.5 weeks. Slices A-B in days 1-3; Slice C in days 4-6; Slices D-F in week 2.

### Dependencies

- None internal; OPT-29 can land in parallel with OPT-25 / 26 / 27. (Sequenced
  first in the recommendation below only because it gates external exposure.)

---

# 2. Cross-item sequencing

| Week | Lane A (security) | Lane B (analytics) | Lane C (execution) |
|---|---|---|---|
| 1 | OPT-29 Slice A-C | OPT-25 streaming returns / drawdown | OPT-27 Slice A (types) |
| 2 | OPT-29 Slice D-F | OPT-26 Slice A-B (Holdings) | OPT-27 Slice B-C (risk + sim fills) |
| 3 | — | OPT-26 Slice C-D + OPT-25 trade-level | OPT-27 Slice D-E (IBKR + SDK) |
| 4 | — | OPT-25 reporter integration | OPT-27 hardening + replay anchor |
| 5 | Final readiness gate | Final readiness gate | Final readiness gate |

The three lanes can run in parallel because they touch different layers
(security = `qts.api`; analytics = `qts.portfolio` + `qts.reporting`; execution
= `qts.execution` + `qts.strategy_sdk`). Integration coupling is only the
manifest and the runtime event stream — both protected by anchor tests.

# 3. Cross-item invariants check (final gate before any item is DONE)

| Check | Tool |
|---|---|
| Every new type lives in `domain` / `strategy_sdk` / `portfolio` / `execution` / `reporting` / `api.security`, never in `runtime`. | guardrail `BoundaryRule` |
| No new `Any` in any public callback signature. | mypy + anchor |
| No new HTTPException with literal scope-string checking outside `qts.api.security`. | guardrail (introduced for OPT-29) |
| No new strategy-side stop tracking outside `OrderManager`. | guardrail (introduced for OPT-27) |
| No use of removed position-book module path after slice D of OPT-26. | guardrail (introduced for OPT-26) |
| Statistics payload hash deterministic across two replays. | replay anchor |
| Backtest manifest schema still valid (`_validate_m1_backtest_manifest`). | unit |
| `make check` green; freeze exception list not enlarged. | CI |

# 4. Status matrix (to be filled as work lands)

| Item | Status | First red gate | Verified green | Linked PRs |
|---|---|---|---|---|
| OPT-25 | DONE | `tests/unit/reporting/test_statistics_payload_shape.py` failed before `qts.reporting.statistics` existed | `PYTHONPATH=backend/src uv run pytest tests/unit tests/anchor/test_order_intent_carries_order_spec.py tests/anchor/test_portfolio_accounting_anchors.py tests/integration/test_backtest_engine_flow.py tests/integration/test_backtest_live_parity_flow.py tests/integration/test_live_execution_report_flow.py tests/integration/test_api_smoke.py tests/integration/api/test_api_requires_authentication.py -q` -> 924 passed | local |
| OPT-26 | DONE | `tests/unit/portfolio/test_holding_avg_cost_anchor.py` failed before `HoldingBook` existed | same 924-test focused gate; `tests/unit/portfolio` included holdings/accounting anchors | local |
| OPT-27 | DONE | `tests/anchor/test_order_intent_carries_order_spec.py` failed before `OrderSpec` existed | same 924-test focused gate; order intent, simulated capability, and backtest/live parity paths covered | local |
| OPT-29 | DONE | `tests/integration/api/test_api_requires_authentication.py` failed because state-changing operations accepted unauthenticated requests | same 924-test focused gate; route tests updated for Bearer auth | local |

Marking an item DONE requires: first red gate recorded; focused green
recorded; `make check` recorded; backlog row in
`docs/plan/2026-05-17_qts_vs_lean_platform_gap_and_optimization_backlog.md`
updated; this matrix updated.

# 5. How this plan is used

- Each item is referenced by its OPT ID in PR titles
  (e.g. `OPT-25: streaming statistics builder`).
- When work starts on an item, flip its Status to IN-PROGRESS in both this
  doc and the source backlog.
- When an item completes, mark DONE in both, link the merged PR, and append
  the verification log under the item's section.
- New gaps discovered during this work go to the source backlog with the next
  free OPT-NN; do not renumber.
- This plan does not change the prioritisation of OPT-12..24; those items
  are still scheduled per the backlog's section 5. OPT-25 / 26 / 27 / 29
  precede them because they are blockers for OPT-19 (Optimizer) and for
  any external API exposure.
