# Quant Trading System Fine-Grained Milestones and Implementation Plan

This document decomposes the quantitative trading system roadmap into small, concrete, verifiable implementation units.

The goal is to make each task suitable for Codex CLI or a human engineer:

- Small enough to implement and review independently.
- Clear enough to avoid ambiguous architecture choices.
- Testable through unit, integration, or anchor tests.
- Aligned with the project architecture and module boundaries.

---

## 0. Planning Principles

### 0.1 Task Size

Each implementation task should be:

- **Small**: preferably 0.5 to 2 engineering days.
- **Concrete**: names exact modules/files to create or modify.
- **Verifiable**: includes tests and commands.
- **Non-speculative**: does not introduce future-only abstractions.
- **Architecture-safe**: respects module dependency rules.

Avoid tasks like:

```text
Implement the trading system.
Implement the backtest engine.
Implement risk management.
Implement frontend.
```

Prefer tasks like:

```text
Implement `InstrumentId`, `AccountId`, and `OrderId` as immutable value objects with tests.
Implement `Timeframe` parsing for `5s`, `1m`, `5m`, `1d`, including unit tests.
Implement anchor test proving `1d` is session-based and not equal to `24h`.
```

---

## 1. Definition of Done

A task is done only when:

1. The requested behavior is implemented.
2. Relevant tests are added or updated.
3. The narrowest required checks pass.
4. Architecture boundaries are not violated.
5. Documentation is updated if public behavior or design changes.
6. The final summary lists changed files, tests run, and known limitations.

### 1.1 Required Checks by Change Type

For simple local changes:

```bash
make format
make lint
make typecheck
make test-unit
```

For cross-module flow changes:

```bash
make test-integration
```

For financial correctness, sessions, calendars, bars, instruments, order lifecycle, portfolio accounting:

```bash
make test-anchor
```

For milestone completion:

```bash
make check
```

---

## 2. Recommended Plan Structure

Update the project plan area to this structure:

```text
docs/plan/
├── implementation_plan.md              # High-level phase roadmap
├── milestones_and_acceptance.md         # Milestone-level acceptance criteria
├── fine_grained_backlog.md              # This document
└── task_template.md                     # Reusable task template for Codex/humans
```

The existing `implementation_plan.md` should stay high-level.  
This file should become the task backlog used for daily implementation.

---

## 3. Task Template

Use this template for each Codex task:

```md
## Task ID: P{phase}-T{number}

### Goal

One-sentence goal.

### Read First

- `AGENTS.md`
- Relevant module `AGENTS.md`
- Relevant docs

### Scope

Create or modify:

- `path/to/file.py`
- `tests/path/test_file.py`

### Requirements

- Requirement 1
- Requirement 2
- Requirement 3

### Out of Scope

- Anything not needed for this task
- Future features
- Broker-specific integrations unless explicitly requested

### Verification

Run:

```bash
make format
make lint
make typecheck
make test-unit
```

Also run `make test-integration` or `make test-anchor` when relevant.

### Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Tests pass
- [ ] No architecture boundary violations
```

---

# Phase 0 — Repository Bootstrap

Goal: make the repository installable, testable, and Codex-ready.

## P0-T01 — Verify Project Skeleton

### Goal

Ensure the repository layout matches the target architecture.

### Scope

- `README.md`
- `MANIFEST.md`
- `docs/README.md`
- `backend/src/qts/__init__.py`
- Empty module `__init__.py` files

### Requirements

- Ensure all intended top-level directories exist.
- Ensure Python package import path is valid.
- Ensure no temporary planning files remain in final project.

### Verification

```bash
make lint
make typecheck
```

### Acceptance Criteria

- [√] `backend/src/qts` is importable.
- [√] `docs/README.md` describes reading order.
- [√] `MANIFEST.md` reflects actual project structure.

---

## P0-T02 — Stabilize Tooling

### Goal

Make format, lint, typecheck, and test commands reliable.

### Scope

- `Makefile`
- `pyproject.toml`
- `tests/`

### Requirements

- Configure `ruff`.
- Configure `mypy`.
- Configure `pytest` markers: `unit`, `integration`, `anchor`, `slow`.
- Create smoke tests if no tests exist.

### Verification

```bash
make format
make lint
make typecheck
make test-unit
```

### Acceptance Criteria

- [√] `make format` passes.
- [√] `make lint` passes.
- [√] `make typecheck` passes.
- [√] `make test-unit` passes.

---

## P0-T03 — Add Test Directory Contracts

### Goal

Define test layout and marker expectations.

### Scope

- `tests/AGENTS.md`
- `tests/unit/test_smoke.py`
- `tests/integration/test_smoke.py`
- `tests/anchor/test_smoke.py`

### Requirements

- Unit tests must be fast and local.
- Integration tests validate multi-module flow.
- Anchor tests validate financial/domain invariants.

### Verification

```bash
make test-unit
make test-integration
make test-anchor
```

### Acceptance Criteria

- [√] All three test categories run independently.
- [√] Pytest markers work.
- [√] Smoke tests do not depend on external services.

---

# Phase 1 — Core Types and Domain Foundations

Goal: create stable domain primitives without infrastructure dependencies.

## P1-T01 — Implement Immutable ID Types

### Scope

- `backend/src/qts/core/ids.py`
- `tests/unit/core/test_ids.py`

### Requirements

Implement immutable value objects:

- `InstrumentId`
- `AccountId`
- `StrategyId`
- `OrderId`
- `BrokerId`
- `EventId`
- `CorrelationId`
- `CausationId`

### Acceptance Criteria

- [√] IDs are immutable.
- [√] IDs compare by value.
- [√] Empty IDs are rejected or explicitly allowed by documented factory behavior.
- [√] Tests cover equality, hashing, and string conversion.

---

## P1-T02 — Implement Time Interval Types

### Scope

- `backend/src/qts/core/time.py`
- `tests/unit/core/test_time.py`
- `tests/anchor/test_time_interval_anchors.py`

### Requirements

- Implement half-open interval type `[start, end)`.
- Reject `end <= start`.
- Provide `contains(timestamp)`.
- Provide overlap/intersection helpers only if needed.

### Acceptance Criteria

- [√] Timestamp exactly equal to `start` is included.
- [√] Timestamp exactly equal to `end` is excluded.
- [√] Anchor test documents half-open semantics.

---

## P1-T03 — Implement Instrument Domain Model

### Scope

- `backend/src/qts/domain/instruments/instrument.py`
- `backend/src/qts/domain/instruments/contract_spec.py`
- `backend/src/qts/domain/instruments/derivative_spec.py`
- `tests/unit/domain/test_instruments.py`
- `tests/anchor/test_instrument_identity_anchors.py`

### Requirements

- Implement `AssetClass`.
- Implement `Instrument`.
- Implement `ContractSpec`.
- Implement option/future derivative metadata.
- Internal identity must be `InstrumentId`.

### Acceptance Criteria

- [√] Stocks, futures, and options can be represented.
- [√] Option requires underlying, expiry, strike, and right.
- [√] Future requires expiry/root metadata where relevant.
- [√] Broker symbols are not part of core identity.

---

## P1-T04 — Implement Bar Domain Model

### Scope

- `backend/src/qts/domain/market_data/bar.py`
- `tests/unit/domain/test_bar.py`
- `tests/anchor/test_bar_interval_anchors.py`

### Requirements

- `Bar` must include `start_time` and `end_time`.
- `Bar` must include `timeframe`.
- Bar interval uses `[start, end)`.
- Support OHLCV fields.
- Include `session_id`, `is_complete`, `is_partial`.

### Acceptance Criteria

- [√] No ambiguous single `timestamp` model.
- [√] Invalid OHLC interval is rejected if domain validation is implemented.
- [√] Anchor tests document start/end semantics.

---

## P1-T05 — Implement Base Event Model

### Scope

- `backend/src/qts/domain/events/event.py`
- `tests/unit/domain/test_events.py`

### Requirements

Events must support:

- `event_id`
- `event_type`
- `event_time`
- `source`
- `partition_key`
- `correlation_id`
- `causation_id`

### Acceptance Criteria

- [√] Events are immutable.
- [√] Correlation/causation can trace event chains.
- [√] Partition key is explicit.

---

# Phase 2 — Timeframe, Calendar, and Bar Aggregation

Goal: define correct market session and bar aggregation semantics before strategy/backtest work.

## P2-T01 — Implement Timeframe Model

### Scope

- `backend/src/qts/data/bars/timeframe.py`
- `tests/unit/data/test_timeframe.py`
- `tests/anchor/test_timeframe_anchors.py`

### Requirements

Support:

- `5s`
- `1m`
- `5m`
- `15m`
- `30m`
- `1h`
- `4h`
- `1d`

Rules:

- `<1d` is clock-aligned.
- `1d` is session-aligned.
- `1d` must not equal `24h`.

### Acceptance Criteria

- [√] `Timeframe.parse("1d")` is session-based.
- [√] `Timeframe.parse("4h")` is clock-based.
- [√] Anchor test asserts `1d != 24h`.

---

## P2-T02 — Implement Bar Alignment Helpers

### Scope

- `backend/src/qts/data/bars/alignment.py`
- `tests/unit/data/test_bar_alignment.py`
- `tests/anchor/test_bar_alignment_anchors.py`

### Requirements

- Implement clock bucket alignment in exchange timezone.
- Use `[start, end)`.
- For `1m -> 5m`, buckets are `[00m, 05m)`, `[05m, 10m)`, etc.
- Timestamp exactly at bucket end belongs to next bucket.

### Acceptance Criteria

- [√] `09:30` belongs to `[09:30, 09:35)`.
- [√] `09:35` belongs to `[09:35, 09:40)`.
- [√] Cross-hour bucket is `[09:55, 10:00)`.

---

## P2-T03 — Wrap Exchange Calendar Library

### Scope

- `backend/src/qts/registry/calendar_registry.py`
- `backend/src/qts/registry/providers/exchange_calendar_provider.py`
- `tests/unit/registry/test_calendar_registry.py`

### Requirements

- Use `exchange-calendars` as preferred base calendar engine.
- Wrap it behind internal interfaces.
- Do not expose third-party calendar objects through domain/strategy SDK.

### Acceptance Criteria

- [√] Calendar lookup returns internal session objects.
- [√] Third-party types do not leak into domain models.
- [√] Tests use deterministic dates.

---

## P2-T04 — Implement Session Filter

### Scope

- `backend/src/qts/data/sessions/filter.py`
- `tests/unit/data/test_session_filter.py`

### Requirements

- Filter out bars outside valid sessions.
- Respect holidays, early closes, late opens where calendar service provides them.
- Use exchange timezone.

### Acceptance Criteria

- [√] Session-outside bar is excluded.
- [√] Session-inside bar is included.
- [√] Boundary `session_close` is excluded.

---

## P2-T05 — Implement Bar Aggregator

### Scope

- `backend/src/qts/data/bars/aggregator.py`
- `tests/unit/data/test_bar_aggregator.py`
- `tests/anchor/test_bar_aggregation_anchors.py`

### Requirements

- Implement `BarAggregator` as the core stateful streaming API.
- Implement `AggregationState` for the current bucket.
- Implement `AggregationResult` as the return value from `update` / `finish`.
- Aggregate lower timeframe bars into higher timeframe bars.
- Support OHLCV aggregation.
- Support `vwap`, `trade_count`, `open_interest` if present.
- `open` = first open.
- `high` = max high.
- `low` = min low.
- `close` = last close.
- `volume` = sum volume.
- Mark partial bars explicitly.
- Keep `aggregate_bars(...)` only as a batch convenience wrapper over `BarAggregator`.

### Acceptance Criteria

- [√] 5 one-minute bars aggregate into one 5-minute bar.
- [√] OHLCV is correct.
- [√] Partial intraday session bars are marked.
- [√] Aggregator does not aggregate session-outside bars.
- [√] Incremental `update(bar)` returns completed bars through `AggregationResult`.
- [√] Current bucket state is represented by `AggregationState`.
- [√] Aggregator state is keyed by `(instrument_id, timeframe, session_id)` at runtime.
- [√] `AggregationState` is not exposed to Strategy SDK or `DataView`.

---

## P2-T06 — Add COMEX Gold Session Anchor

### Scope

- `docs/domain/market_calendar_and_sessions.md`
- `tests/anchor/test_market_calendar_anchors.py`

### Requirements

Document and test:

- COMEX Gold regular session `[ET 18:00, ET 17:00)`.
- Timezone representation does not change session semantics.
- Normal full 1-minute session has `23 * 60 = 1380` bars.
- Exclude holidays, early closes, late opens.

### Acceptance Criteria

- [√] Anchor test documents the expected `1380` count.
- [√] The test is deterministic.
- [√] Any library mismatch is handled by an adapter/override, not silently accepted.

---

# Phase 3 — Registry and Symbol Mapping

Goal: ensure internal identity is stable and broker/data-source symbols stay at boundaries.

## P3-T01 — Implement Instrument Registry Interface

### Scope

- `backend/src/qts/registry/instrument_registry.py`
- `tests/unit/registry/test_instrument_registry.py`

### Requirements

- Resolve user symbol to `InstrumentId`.
- Retrieve `Instrument`.
- Retrieve `ContractSpec`.

### Acceptance Criteria

- [√] Registry returns internal IDs.
- [√] Registry has no broker-specific dependency.
- [√] Tests cover stock, future, option.

---

## P3-T02 — Implement Broker Symbol Mapping

### Scope

- `backend/src/qts/registry/broker_symbol_mapping.py`
- `tests/unit/registry/test_broker_symbol_mapping.py`

### Requirements

- Map `InstrumentId -> broker_symbol`.
- Map broker report symbol back to `InstrumentId`.
- Keep mapping out of domain models.

### Acceptance Criteria

- [√] Domain model does not contain broker symbol.
- [√] Mapping errors are explicit.
- [√] Tests cover round-trip mapping.

---

## P3-T03 — Implement Future Chain and Continuous Future References

### Scope

- `backend/src/qts/registry/future_chain_registry.py`
- `tests/unit/registry/test_future_chain_registry.py`
- `tests/anchor/test_continuous_future_anchors.py`

### Requirements

- Represent future chains.
- Represent continuous future references for research.
- Continuous future must not be directly tradable.

### Acceptance Criteria

- [√] Tradable future contract resolves to concrete `InstrumentId`.
- [√] Continuous future is rejected for direct order submission.
- [√] Anchor test protects this rule.

---

## P3-T04 — Implement Option Chain Registry

### Scope

- `backend/src/qts/registry/option_chain_registry.py`
- `tests/unit/registry/test_option_chain_registry.py`

### Requirements

- Retrieve options by underlying.
- Filter by expiry, strike, right.
- Support selection helpers later, but keep MVP small.

### Acceptance Criteria

- [√] Option chain returns option instruments.
- [√] Missing underlying is explicit error.
- [√] Tests cover call/put selection.

---

# Phase 4 — Strategy SDK MVP

Goal: let users write strategies without seeing internal trading complexity.

## P4-T01 — Implement AssetRef

### Scope

- `backend/src/qts/strategy_sdk/asset_ref.py`
- `tests/unit/strategy_sdk/test_asset_ref.py`

### Requirements

- Lightweight user-facing asset reference.
- Contains internal `InstrumentId`.
- Does not expose `ContractSpec` or broker symbol.

### Acceptance Criteria

- [√] `AssetRef` is safe for user strategies.
- [√] It can represent stock/future/option references.
- [√] It does not leak internal registry objects.

---

## P4-T02 — Implement Strategy Base Class

### Scope

- `backend/src/qts/strategy_sdk/strategy.py`
- `tests/unit/strategy_sdk/test_strategy_base.py`

### Requirements

Define lifecycle hooks:

- `initialize`
- `on_bar`
- `on_tick`
- `on_timer`
- `on_order_update`
- `on_fill`

### Acceptance Criteria

- [√] Strategy can override hooks.
- [√] Default hooks are no-op.
- [√] No dependency on runtime actors.

---

## P4-T03 — Implement StrategyContext Symbol Resolution

### Scope

- `backend/src/qts/strategy_sdk/context.py`
- `tests/unit/strategy_sdk/test_context_symbol.py`

### Requirements

- `ctx.symbol("AAPL")`.
- `ctx.future("ES", contract="front")`.
- `ctx.option(...)` or minimal placeholder if option selection is not yet implemented.
- Calls registry behind the scenes.

### Acceptance Criteria

- [√] User receives `AssetRef`.
- [√] Registry details are hidden.
- [√] Invalid symbol errors are clear.

---

## P4-T04 — Implement Target Intent API

### Scope

- `backend/src/qts/strategy_sdk/target.py`
- `backend/src/qts/strategy_sdk/context.py`
- `tests/unit/strategy_sdk/test_target_api.py`
- `tests/anchor/test_strategy_sdk_boundaries.py`

### Requirements

Implement:

- `ctx.target_percent(asset, weight)`
- `ctx.target_quantity(asset, quantity)`
- `ctx.target_value(asset, value)`
- `ctx.close(asset)`
- `ctx.rebalance(weights)`

### Acceptance Criteria

- [√] Calls produce intents.
- [√] Calls do not mutate portfolio directly.
- [√] Calls do not bypass risk/order manager.
- [√] Anchor test protects SDK boundary.

---

## P4-T05 — Implement DataView MVP

### Scope

- `backend/src/qts/strategy_sdk/data_view.py`
- `tests/unit/strategy_sdk/test_data_view.py`

### Requirements

- `data.close(asset)`.
- `data.bar(asset)`.
- `ctx.data.history(asset, bars, timeframe)`.
- Must be time-sliced by `as_of`.
- Must consume finalized bars, not `BarAggregator` or `AggregationState`.

### Acceptance Criteria

- [√] No future data can be read.
- [√] DataView returns user-safe data objects.
- [√] Tests cover `as_of` behavior.
- [√] DataView does not expose in-progress aggregation state.

---

## P4-T06 — Implement PortfolioView MVP

### Scope

- `backend/src/qts/strategy_sdk/portfolio_view.py`
- `tests/unit/strategy_sdk/test_portfolio_view.py`

### Requirements

- Read-only view of cash, equity, position, exposure, weight.
- No direct mutation.

### Acceptance Criteria

- [√] PortfolioView is immutable/read-only.
- [√] Attempts to mutate state are impossible or blocked.
- [√] Tests cover position lookup.

---

# Phase 5 — Indicators and Factors MVP

Goal: support user research and strategy writing.

## P5-T01 — Implement Rolling Window

### Scope

- `backend/src/qts/indicators/rolling.py`
- `tests/unit/indicators/test_rolling_window.py`

### Requirements

- Fixed-size rolling buffer.
- `ready` once full.
- Snapshot/restore if simple.

### Acceptance Criteria

- [√] Window maintains max length.
- [√] `ready` semantics are correct.
- [√] Tests cover append and restore.

---

## P5-T02 — Implement SMA Indicator

### Scope

- `backend/src/qts/indicators/price/sma.py`
- `backend/src/qts/strategy_sdk/indicators.py`
- `tests/unit/indicators/test_sma.py`

### Requirements

- Incremental SMA.
- User creates via `ctx.indicator.sma(asset, window)`.

### Acceptance Criteria

- [√] SMA is not ready before warmup.
- [√] SMA value is correct after warmup.
- [√] Strategy SDK wrapper hides implementation.

---

## P5-T03 — Implement RSI or EMA as Second Indicator

### Scope

- `backend/src/qts/indicators/price/ema.py` or `rsi.py`
- `tests/unit/indicators/test_ema.py` or `test_rsi.py`

### Requirements

- Add one non-trivial indicator to validate abstraction.

### Acceptance Criteria

- [√] Indicator follows common interface.
- [√] Warmup behavior is documented.
- [√] Tests cover incremental updates.

---

## P5-T04 — Implement Momentum Factor MVP

### Scope

- `backend/src/qts/factors/momentum.py`
- `backend/src/qts/strategy_sdk/factors.py`
- `tests/unit/factors/test_momentum.py`

### Requirements

- Multi-asset momentum calculation.
- Return ranked factor result.

### Acceptance Criteria

- [√] Factor supports a universe of assets.
- [√] Ranking is deterministic.
- [√] Strategy SDK wrapper is simple.

---

# Phase 6 — Portfolio and Accounting

Goal: make account state updates deterministic and financially correct.

## P6-T01 — Implement PositionBook

### Scope

- `backend/src/qts/portfolio/position_book.py`
- `tests/unit/portfolio/test_position_book.py`

### Requirements

- Track positions by `InstrumentId`.
- Apply position deltas.
- Return immutable snapshots.

### Acceptance Criteria

- [√] Position quantity updates correctly.
- [√] Unknown position returns zero/empty view.
- [√] Tests cover long and short positions.

---

## P6-T02 — Implement CashBook and ReservationBook

### Scope

- `backend/src/qts/portfolio/cash_book.py`
- `backend/src/qts/portfolio/reservation_book.py`
- `tests/unit/portfolio/test_cash_and_reservation.py`

### Requirements

- Track cash.
- Track reserved/frozen cash.
- Release reservation on rejection/cancel/fill.

### Acceptance Criteria

- [√] Available cash = cash - reserved.
- [√] Reservations are idempotent by ID.
- [√] Releasing unknown reservation is explicit behavior.

---

## P6-T03 — Implement Fill Accounting

### Scope

- `backend/src/qts/portfolio/accounting/fill_accounting.py`
- `tests/unit/portfolio/test_fill_accounting.py`

### Requirements

- Apply fills to position/cash.
- Support buy/sell.
- Support multiplier.

### Acceptance Criteria

- [√] Equity cash/position update is correct.
- [√] Future PnL formula uses multiplier.
- [√] Option premium value uses multiplier.
- [√] Anchor tests cover accounting invariants.

---

## P6-T04 — Implement Valuation Models

### Scope

- `backend/src/qts/portfolio/valuation/`
- `tests/unit/portfolio/test_valuation_models.py`
- `tests/anchor/test_portfolio_accounting_anchors.py`

### Requirements

- Equity valuation.
- Future exposure/PnL valuation.
- Option premium valuation.

### Acceptance Criteria

- [√] Equity notional = qty * price.
- [√] Future PnL = contracts * price_diff * multiplier.
- [√] Option value = contracts * option_price * multiplier.
- [√] Anchor tests pass.

---

# Phase 7 — Risk MVP

Goal: create explicit pre-trade risk decisions.

## P7-T01 — Implement RiskDecision and RiskRule Interfaces

### Scope

- `backend/src/qts/domain/risk/`
- `backend/src/qts/risk/rule.py`
- `backend/src/qts/risk/risk_engine.py`
- `tests/unit/risk/test_risk_decision.py`

### Requirements

- `Approved`, `Rejected`, maybe `Modified`.
- Include reasons.
- No silent rejection.

### Acceptance Criteria

- [√] Every check returns explicit decision.
- [√] Rejections contain reason codes.
- [√] Tests cover approved/rejected paths.

---

## P7-T02 — Implement Max Order Quantity Rule

### Scope

- `backend/src/qts/risk/rules/max_order_qty.py`
- `tests/unit/risk/test_max_order_qty.py`

### Acceptance Criteria

- [√] Orders within limit pass.
- [√] Orders above limit reject.
- [√] Decision reason is explicit.

---

## P7-T03 — Implement Max Notional Rule

### Scope

- `backend/src/qts/risk/rules/max_notional.py`
- `tests/unit/risk/test_max_notional.py`

### Acceptance Criteria

- [√] Uses instrument multiplier.
- [√] Rejects excessive notional.
- [√] Tests cover stock/future/option examples.

---

## P7-T04 — Implement Trading Session Rule

### Scope

- `backend/src/qts/risk/rules/trading_session_rule.py`
- `tests/unit/risk/test_trading_session_rule.py`
- `tests/anchor/test_market_calendar_anchors.py`

### Acceptance Criteria

- [√] Orders outside session reject.
- [√] Orders inside session pass.
- [√] Uses calendar service, not local machine time.

---

# Phase 8 — Execution and Order Lifecycle

Goal: make orders explicit, stateful, idempotent, and broker-safe.

## P8-T01 — Implement Order State Machine

### Scope

- `backend/src/qts/execution/order_state_machine.py`
- `tests/unit/execution/test_order_state_machine.py`
- `tests/anchor/test_order_state_machine_anchors.py`

### Requirements

States:

- Created
- Sent
- Accepted
- PartiallyFilled
- Filled
- CancelRequested
- Cancelled
- Rejected

### Acceptance Criteria

- [√] Valid transitions pass.
- [√] Invalid transitions reject.
- [√] Late/duplicate broker reports do not corrupt state.
- [√] Anchor tests cover core lifecycle.

---

## P8-T02 — Implement Idempotency for Fills

### Scope

- `backend/src/qts/execution/idempotency.py`
- `tests/unit/execution/test_fill_idempotency.py`

### Acceptance Criteria

- [√] Duplicate fill ID is ignored.
- [√] Distinct fill IDs apply once.
- [√] Behavior is deterministic.

---

## P8-T03 — Implement OrderManager MVP

### Scope

- `backend/src/qts/execution/order_manager.py`
- `tests/unit/execution/test_order_manager.py`

### Requirements

- Create orders from approved order intents.
- Track local order ID and broker order ID.
- Process normalized execution reports.
- Emit accepted fill/update events.

### Acceptance Criteria

- [√] Broker report does not directly mutate portfolio.
- [√] Fill must pass through OrderManager.
- [√] Order state is queryable.

---

## P8-T04 — Implement Simulated Broker

### Scope

- `backend/src/qts/execution/simulator/simulated_broker.py`
- `backend/src/qts/execution/simulator/fill_model.py`
- `tests/unit/execution/test_simulated_broker.py`

### Requirements

- Fill market orders deterministically.
- Return normalized execution reports.
- No real broker dependency.

### Acceptance Criteria

- [√] Simulated fill event is valid.
- [√] Fill price comes from provided market data.
- [√] Tests are deterministic.

---

# Phase 9 — Runtime Actors

Goal: wire modules through Actor + Queue while preserving state ownership.

## P9-T01 — Implement Actor Base and Mailbox

### Scope

- `backend/src/qts/runtime/actor.py`
- `backend/src/qts/runtime/actor_ref.py`
- `backend/src/qts/runtime/mailbox.py`
- `tests/unit/runtime/test_actor.py`

### Acceptance Criteria

- [√] Actor processes mailbox serially.
- [√] `tell` enqueues messages.
- [√] No direct business method cross-call required.

---

## P9-T02 — Implement Event Router

### Scope

- `backend/src/qts/runtime/router.py`
- `backend/src/qts/runtime/partitioning.py`
- `tests/unit/runtime/test_router.py`

### Acceptance Criteria

- [√] Routes by `account_id`, `strategy_id`, `broker_id`, `market_data_source_id`, or configured key.
- [√] Unknown route is explicit error.
- [√] Per-key routing is deterministic.
- [√] Market data messages and order execution messages route to different actor types.

---

## P9-T03 — Implement AccountActor MVP

### Scope

- `backend/src/qts/runtime/actors/account_actor.py`
- `tests/unit/runtime/test_account_actor.py`

### Requirements

- Own account state.
- Process targets/fills serially.
- Use portfolio accounting.

### Acceptance Criteria

- [√] Account state mutated only inside AccountActor.
- [√] Fill updates position/cash once.
- [√] Duplicate fill remains idempotent.

---

## P9-T04 — Implement OrderManagerActor MVP

### Scope

- `backend/src/qts/runtime/actors/order_manager_actor.py`
- `tests/unit/runtime/test_order_manager_actor.py`

### Acceptance Criteria

- [√] Owns order state.
- [√] Sends order execution requests.
- [√] Receives execution reports and emits validated fills.

---

## P9-T05 — Implement ExecutionActor MVP

### Scope

- `backend/src/qts/runtime/actors/execution_actor.py`
- `tests/unit/runtime/test_execution_actor.py`

### Acceptance Criteria

- [√] Wraps order execution adapter or simulator.
- [√] Emits normalized execution reports.
- [√] Does not mutate account/portfolio.
- [√] Does not handle ticks, quotes, bars, or market data subscriptions.

---

## P9-T06 — Implement MarketDataActor MVP

### Scope

- `backend/src/qts/runtime/actors/market_data_actor.py`
- `tests/unit/runtime/test_market_data_actor.py`

### Acceptance Criteria

- [√] Owns market data subscription and aggregation stream state.
- [√] Emits normalized ticks, quotes, and finalized bars.
- [√] Does not submit, cancel, replace, or reconcile orders.
- [√] Does not mutate account/portfolio.

---

## P9-T07 — Implement End-to-End Integration Flow

### Scope

- `tests/integration/test_bar_to_fill_flow.py`

### Requirements

Test:

```text
Bar
→ Strategy
→ TargetIntent
→ AccountActor
→ Risk
→ OrderManagerActor
→ ExecutionActor
→ SimulatedBroker
→ Fill
→ AccountActor
→ Portfolio snapshot
```

### Acceptance Criteria

- [√] Full flow completes.
- [√] Account position updates.
- [√] Order state is final.
- [√] Risk path is exercised.

---

# Phase 10 — Backtest MVP

Goal: run a simple user strategy on historical bars.

## P10-T01 — Implement Replay Clock

### Scope

- `backend/src/qts/backtest/replay_clock.py`
- `tests/unit/backtest/test_replay_clock.py`

### Acceptance Criteria

- [√] Clock advances deterministically.
- [√] No wall-clock dependency.
- [√] Tests cover ordered time events.

---

## P10-T02 — Implement Historical Data Portal

### Scope

- `backend/src/qts/backtest/historical_data_portal.py`
- `tests/unit/backtest/test_historical_data_portal.py`

### Acceptance Criteria

- [√] Returns bars as of current time only.
- [√] Does not expose future bars.
- [√] Supports basic history request.

---

## P10-T03 — Implement Backtest Engine MVP

### Scope

- `backend/src/qts/backtest/engine.py`
- `tests/integration/test_backtest_engine_flow.py`

### Requirements

- Load strategy.
- Replay bars.
- Run strategy callbacks.
- Process intents through trading flow.
- Produce basic result.

### Acceptance Criteria

- [√] Example moving average strategy runs.
- [√] No future data is visible.
- [√] Orders/fills go through execution flow.
- [√] Integration test passes.

---

## P10-T04 — Add Example Moving Average Strategy

### Scope

- `examples/strategies/moving_average_cross.py`
- `examples/configs/backtest.yaml`
- `tests/integration/test_example_strategy_backtest.py`

### Acceptance Criteria

- [√] Strategy imports only from Strategy SDK.
- [√] Strategy does not import runtime/risk/execution internals.
- [√] Example can run in backtest mode.

---

# Phase 11 — Application and API MVP

Goal: expose backend use cases safely to frontend and external clients.

## P11-T01 — Implement Application Service Skeletons

### Scope

- `backend/src/qts/application/services/`
- `tests/unit/application/test_services.py`

### Acceptance Criteria

- [√] Services wrap use cases.
- [√] API can call services.
- [√] Services do not leak actor internals.

---

## P11-T02 — Implement FastAPI App Skeleton

### Scope

- `backend/src/qts/api/app.py`
- `backend/src/qts/api/routes/`
- `backend/src/qts/api/schemas/`
- `tests/integration/test_api_smoke.py`

### Acceptance Criteria

- [√] App starts in test mode.
- [√] Health endpoint works.
- [√] Schemas do not expose actor internals.

---

## P11-T03 — Implement Backtest API Endpoint

### Scope

- `backend/src/qts/api/routes/backtests.py`
- `backend/src/qts/api/schemas/backtest_schema.py`
- `tests/integration/test_api_backtest_flow.py`

### Acceptance Criteria

- [√] Can submit backtest request.
- [√] Request maps to application service.
- [√] Response is stable DTO.

---

## P11-T04 — Implement WebSocket Event Stream Skeleton

### Scope

- `backend/src/qts/api/websocket/`
- `tests/integration/test_websocket_smoke.py`

### Acceptance Criteria

- [√] Can connect in test.
- [√] Can stream synthetic event.
- [√] Does not expose raw actor mailboxes.

---

# Phase 12 — Frontend Skeleton

Goal: create a frontend shell that consumes backend APIs without duplicating trading logic.

## P12-T01 — Initialize Frontend Project

### Scope

- `frontend/package.json`
- `frontend/src/`

### Acceptance Criteria

- [√] Project installs.
- [ ] Basic app renders.
- [√] No trading logic duplicated.

---

## P12-T02 — Add API Client Layer

### Scope

- `frontend/src/api/`
- `frontend/src/types/`

### Acceptance Criteria

- [ ] API client calls backend health endpoint.
- [ ] Shared DTO types are explicit.
- [√] No direct backend internals.

---

## P12-T03 — Add Basic Dashboard Shell

### Scope

- `frontend/src/features/`

### Acceptance Criteria

- [ ] Shows placeholder account/strategy/order/risk panels.
- [ ] Data comes from API client or mocks.
- [ ] Components are separated by feature.

---

# Phase 13 — IBKR Paper Trading MVP

Goal: run strategy against IBKR paper market data and an IBKR paper account while preserving separate market data and order execution boundaries.

## P13-T01 — Implement IBKR Paper Runtime Config

### Scope

- `configs/paper.ibkr.example.yaml`
- `backend/src/qts/config/`
- `scripts/run_paper_ibkr.py`

### Acceptance Criteria

- [√] Paper config loads without committing real credentials.
- [√] Config has separate market data and order execution connection sections.
- [√] Config requires paper account identity and paper permissions.
- [√] Runtime fails safely if required IBKR paper settings are missing.

---

## P13-T02 — Implement IBKR Market Data Adapter Skeleton

### Scope

- `backend/src/qts/data/adapters/ibkr_market_data.py`
- `tests/unit/data/test_ibkr_market_data_adapter.py`

### Acceptance Criteria

- [√] Adapter maps configured IBKR market data connection settings to internal subscription requests.
- [√] Adapter emits normalized tick, quote, and bar events.
- [√] Adapter uses `InstrumentId` and boundary symbol mapping rather than broker symbols as internal IDs.
- [√] Adapter has no submit, cancel, replace, or order reconciliation methods.

---

## P13-T03 — Implement IBKR Paper Order Execution Adapter Skeleton

### Scope

- `backend/src/qts/execution/adapters/ibkr_order_execution.py`
- `tests/unit/execution/test_ibkr_order_execution_adapter.py`

### Acceptance Criteria

- [√] Adapter maps internal orders to IBKR paper order requests at the boundary.
- [√] Adapter emits normalized execution reports and fills.
- [√] Adapter has no market data subscription or bar aggregation methods.
- [√] Adapter cannot directly mutate account or portfolio state.

---

## P13-T04 — Connect IBKR Paper Flow with Fake Transport Tests

### Scope

- `tests/integration/test_ibkr_paper_flow.py`

### Acceptance Criteria

- [√] Fake IBKR market data transport emits ticks/quotes/bars through MarketDataActor.
- [√] Fake IBKR order transport receives approved orders from ExecutionActor only.
- [√] Orders flow through Risk and OrderManager before reaching IBKR paper execution.
- [√] Paper fills return through OrderManager before affecting AccountActor.
- [√] Market data and order execution tests can run without network access.

---

# Phase 14 — Hardening and Observability

Goal: make runtime debuggable, auditable, and recoverable.

## P14-T01 — Implement Structured Logging

### Scope

- `backend/src/qts/observability/logging.py`

### Acceptance Criteria

- [√] Logs include correlation_id where available.
- [√] Logs are structured.
- [√] No secrets in logs.

---

## P14-T02 — Implement Event Store Interface

### Scope

- `backend/src/qts/runtime/event_store.py`
- `tests/unit/runtime/test_event_store.py`

### Acceptance Criteria

- [√] Event append API exists.
- [√] Event replay API exists.
- [√] In-memory implementation is deterministic.

---

## P14-T03 — Implement State Snapshot Interfaces

### Scope

- `backend/src/qts/runtime/state_recovery.py`
- `tests/unit/runtime/test_state_recovery.py`

### Acceptance Criteria

- [√] Actor state can snapshot.
- [√] Actor state can restore.
- [√] Indicator state can be included later.

---

# Phase 15 — IBKR Live Trading Preparation

Goal: promote the tested IBKR paper path to live trading readiness with explicit environment separation, reconciliation, and operational controls.

## P15-T01 — Add IBKR Live Configuration Shape

### Scope

- `.env.example`
- `configs/live.ibkr.example.yaml`
- `backend/src/qts/config/secrets.py`

### Acceptance Criteria

- [√] Real secrets are not committed.
- [√] Example config documents separate market data and order execution connection settings.
- [√] Example config documents live account identity and permissions.
- [√] Runtime fails safely if required IBKR live settings are missing.

---

## P15-T02 — Add Paper/Live Environment Guardrails

### Scope

- `backend/src/qts/config/`
- `tests/unit/config/test_ibkr_environment_guards.py`

### Acceptance Criteria

- [√] Live mode cannot load paper account IDs by accident.
- [√] Live mode cannot reuse paper client IDs or credentials by accident.
- [√] Paper and live risk limit profiles are explicitly selected.
- [√] Error messages identify the misconfigured environment without printing secrets.

---

## P15-T03 — Add Reconnect and Reconciliation Plan

### Scope

- `docs/operations/ibkr_live_readiness.md`
- `tests/integration/test_ibkr_reconciliation_flow.py`

### Acceptance Criteria

- [√] Reconnect behavior preserves pending order state.
- [√] Broker order IDs reconcile to internal order IDs.
- [√] Duplicate or late execution reports remain idempotent.
- [√] Manual cutover and rollback checklist is documented.

---

# Phase 16 — Documentation and Review Gates

Goal: keep implementation aligned with design.

## P16-T01 — Add Architecture Review Checklist

### Scope

- `docs/architecture/review_checklist.md`

### Acceptance Criteria

- [√] Checklist covers dependency rules.
- [√] Checklist covers actor boundaries.
- [√] Checklist covers Strategy SDK boundaries.
- [√] Checklist covers anchor tests.

---

## P16-T02 — Add Milestone Review Template

### Scope

- `docs/plan/milestone_review_template.md`

### Acceptance Criteria

- [√] Captures completed tasks.
- [√] Captures checks run.
- [√] Captures known limitations.
- [√] Captures next milestone.

---

# 4. Recommended Implementation Order

Recommended strict order:

```text
P0  Repository bootstrap
P1  Core + domain foundations
P2  Timeframe + calendar + bar aggregation
P3  Registry + symbol mapping
P4  Strategy SDK MVP
P5  Indicators/factors MVP
P6  Portfolio/accounting
P7  Risk MVP
P8  Execution/order lifecycle
P9  Runtime actors
P10 Backtest MVP
P11 Application/API MVP
P12 Frontend skeleton
P13 IBKR paper trading MVP
P14 Hardening/observability
P15 IBKR live preparation
P16 Documentation/review gates
```

Do not start API/frontend before Strategy SDK, portfolio, risk, execution, and runtime integration are reasonably stable.

---

# 5. Codex CLI Usage Pattern

For each task:

```bash
codex "Read AGENTS.md, the relevant module AGENTS.md, and docs/plan/fine_grained_backlog.md. Implement P2-T02 only. Add tests and run the required checks."
```

For milestone review:

```bash
codex "Review completed work for Phase 2 against docs/plan/fine_grained_backlog.md, docs/testing/anchor_tests.md, and module AGENTS files. Report gaps before changing code."
```

For architecture review:

```bash
codex "Review the repository against docs/architecture/dependency_rules.md and all AGENTS.md files. Identify dependency violations and risky abstractions."
```

---

# 6. Notes

This plan is intentionally conservative. It favors correctness, testability, and reviewability over speed.

In financial systems, the most dangerous failure mode is not a crash. It is code that runs successfully while implementing the wrong market semantics.

Anchor tests are therefore mandatory for:

- Calendars and sessions
- Bar boundaries
- Instrument identity
- Order lifecycle
- Portfolio accounting
- Strategy SDK boundaries
