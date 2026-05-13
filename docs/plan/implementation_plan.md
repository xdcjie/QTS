# Implementation Plan

This document defines the recommended implementation path for the quantitative trading system.

The project should be implemented in small, verifiable increments. Each phase must preserve the architecture boundaries defined in `docs/architecture/dependency_rules.md` and the module-local `AGENTS.md` files.

## Guiding principles

- Implement correctness-critical domain models before runtime orchestration.
- Prefer simple, deterministic implementations before distributed or highly concurrent implementations.
- Do not expose internal trading complexity to user strategies.
- Keep Strategy SDK, domain models, risk, order execution, and market data boundaries strict.
- Use anchor tests to protect financial correctness invariants.
- Run the narrowest relevant checks during development and `make check` before finishing a milestone.

## Phase 0: Project skeleton and verification baseline

### Goal

The project installs, imports, and runs all baseline checks.

### Scope

- Confirm `pyproject.toml` dependency groups.
- Confirm `Makefile` targets.
- Confirm package import path under `backend/src/qts`.
- Confirm test directories exist:
  - `tests/unit`
  - `tests/integration`
  - `tests/anchor`
- Confirm agent guidance exists:
  - root `AGENTS.md`
  - module-level `AGENTS.md`

### Out of scope

- Real broker integration, including IBKR paper/live connectivity.
- Frontend implementation.
- Distributed runtime.

### Verification

```bash
uv sync
make format
make lint
make typecheck
make test-unit
make test-integration
make test-anchor
```

Milestone is complete when `make check` passes.

---

## Phase 1: Core and pure domain models

### Goal

Establish stable domain primitives and immutable trading value objects.

### Scope

Implement the minimal model set:

- `qts/core/ids.py`
  - `AccountId`
  - `StrategyId`
  - `InstrumentId`
  - `OrderId`
  - `BrokerId`
  - `EventId`
  - `CorrelationId`
- `qts/core/time.py`
  - half-open time intervals
  - exchange-time aware helpers
- `qts/domain/instruments/`
  - `Instrument`
  - `ContractSpec`
  - `AssetClass`
  - derivative specs for future and option contracts
- `qts/domain/market_data/`
  - `Bar`
  - `Quote`
  - `Tick`
- `qts/domain/events/`
  - base event metadata
  - correlation and causation IDs

### Design rules

- Domain models may depend on `qts/core` only.
- Domain models must not depend on API, runtime, order execution adapters, market data adapters, database, or frontend code.
- Internal identifiers must use `InstrumentId`; broker symbols must not leak into domain models.
- `Bar` must use explicit `[start_time, end_time)` semantics.

### Verification

```bash
make test-unit
make test-anchor
make typecheck
```

---

## Phase 2: Registry, calendars, sessions, and bar aggregation

### Goal

Implement instrument metadata, exchange calendar abstraction, session handling, and deterministic bar aggregation.

### Scope

Implement:

- `qts/registry/instrument_registry.py`
- `qts/registry/calendar_registry.py`
- `qts/registry/broker_symbol_mapping.py`
- `qts/data/bars/timeframe.py`
- `qts/data/bars/alignment.py`
- `qts/data/bars/aggregator.py`
- `qts/data/bars/validation.py`

### Design rules

- Use `exchange-calendars` as the preferred base implementation for exchange calendars.
- Wrap third-party calendar behavior behind project interfaces.
- Do not expose `exchange_calendars` objects through domain models or Strategy SDK.
- All bar intervals use `[start, end)`.
- Intraday bars, including `5s`, `1m`, `5m`, `15m`, `30m`, `1h`, and `4h`, are clock-aligned in exchange time.
- `1d` bars are session-aligned, not `24h` bars.
- Session-outside data must not enter aggregated bars.

### Required anchor tests

- `1m -> 5m` aligns to `[00m, 05m)`, `[05m, 10m)`, ..., `[55m, next_hour 00m)`.
- A timestamp exactly at the boundary belongs to the next interval.
- `1d` uses session boundaries.
- COMEX Gold normal session `[ET 18:00, ET 17:00)` produces `23 * 60 = 1380` one-minute bars, excluding holidays and special sessions.

### Verification

```bash
make test-unit
make test-anchor
```

---

## Phase 3: Strategy SDK minimal API

### Goal

Allow users to write strategies without knowing internal trading-system concepts.

### Scope

Implement:

- `qts/strategy_sdk/strategy.py`
- `qts/strategy_sdk/context.py`
- `qts/strategy_sdk/asset_ref.py`
- `qts/strategy_sdk/data_view.py`
- `qts/strategy_sdk/portfolio_view.py`
- `qts/strategy_sdk/target.py`
- basic indicator/factor facade stubs

### User-facing goal

A user should be able to write:

```python
class MovingAverageStrategy(Strategy):
    def initialize(self, ctx):
        self.asset = ctx.symbol("AAPL")
        self.fast = ctx.indicator.sma(self.asset, 20)
        self.slow = ctx.indicator.sma(self.asset, 60)

    def on_bar(self, ctx, data):
        if self.fast.value > self.slow.value:
            ctx.target_percent(self.asset, 1.0)
        else:
            ctx.close(self.asset)
```

### Design rules

- Strategies must not access Actor, Broker, RiskEngine, OrderManager, ContractSpec, or BrokerSymbolMapping directly.
- Target APIs produce intents; they must not mutate portfolio state directly.
- Strategy SDK must be usable in backtest, paper, and live modes.

### Verification

```bash
make test-unit
make test-anchor
```

---

## Phase 4: Portfolio, accounting, risk, and execution state machines

### Goal

Implement the minimal trading decision and accounting chain before introducing actor concurrency.

### Scope

Implement:

- `qts/portfolio/position_book.py`
- `qts/portfolio/account_book.py`
- `qts/portfolio/reservation_book.py`
- valuation and PnL basics
- `qts/risk/risk_engine.py`
- basic risk rules
- `qts/execution/order_manager.py`
- `qts/execution/order_state_machine.py`
- `qts/execution/idempotency.py`

### Minimal flow

```text
TargetIntent
  -> OrderIntent
  -> RiskDecision
  -> Order
  -> Fill
  -> Position/Cash update
```

### Design rules

- Risk checks must not be bypassed.
- Fill processing must be idempotent.
- Broker reports must not directly mutate account state.
- Order state transitions must be explicit and testable.

### Verification

```bash
make test-unit
make test-anchor
```

---

## Phase 5: Runtime Actor integration

### Goal

Introduce Actor + Queue orchestration while preserving deterministic state ownership.

### Scope

Implement:

- `qts/runtime/actor.py`
- `qts/runtime/actor_ref.py`
- `qts/runtime/mailbox.py`
- `qts/runtime/router.py`
- `qts/runtime/partitioning.py`
- `qts/runtime/actors/account_actor.py`
- `qts/runtime/actors/order_manager_actor.py`
- `qts/runtime/actors/execution_actor.py`
- `qts/runtime/actors/market_data_actor.py`
- `qts/runtime/actors/strategy_actor.py`

### Design rules

- Actor-to-actor communication must use messages, not direct business method calls.
- `AccountActor` owns and mutates account state.
- `OrderManagerActor` owns and mutates order state.
- Preserve per-key ordering for account, order, strategy, market data, and execution flows.
- Market data adapters and order execution adapters must use separate actor boundaries, even when both connect to IBKR.

### Required integration flow

```text
Bar
  -> Strategy
  -> TargetIntent
  -> AccountActor
  -> Risk
  -> OrderManagerActor
  -> ExecutionActor
  -> BrokerSimulator
  -> Fill
  -> OrderManagerActor
  -> AccountActor
```

### Verification

```bash
make test-unit
make test-integration
make test-anchor
```

---

## Phase 6: Backtest MVP

### Goal

Run a complete historical strategy simulation with the same Strategy SDK used by paper/live modes.

### Scope

Implement:

- `qts/backtest/engine.py`
- `qts/backtest/backtest_runtime.py`
- `qts/backtest/replay_clock.py`
- `qts/strategy_sdk/data_view.py` (`DataView`)
- `qts/backtest/broker_simulator.py`
- `qts/backtest/fill_model.py`
- `scripts/run_backtest.py`

### Design rules

- Backtest `DataView` must be time-sliced.
- No future data may be visible to user strategy code.
- Simulated fills should pass through the same execution/accounting path where practical.

### Verification

```bash
python scripts/run_backtest.py
make test-integration
make test-anchor
```

---

## Phase 7: API and application service layer

### Goal

Expose backend capabilities through stable application services and APIs.

### Scope

Implement:

- `qts/application/services/`
- `qts/application/dto/`
- `qts/api/app.py`
- `qts/api/routes/`
- `qts/api/schemas/`
- `qts/api/websocket/`

### Design rules

- API calls application services, not actor internals directly.
- Public API schemas must not leak internal actor objects.
- WebSocket streams publish state/log/order/risk updates, not raw internal control channels.

### Verification

```bash
make test-unit
make test-integration
```

---

## Phase 8: Paper trading runtime

### Goal

Run strategies against IBKR paper market data and an IBKR paper trading account without using live capital.

### Scope

- IBKR paper order execution adapter.
- IBKR market data adapter and worker.
- Separate runtime configuration for market data and order execution connections.
- Order/fill event stream.

### Design rules

- Paper trading uses the same IBKR adapter boundary as live trading, with paper account credentials and paper account permissions.
- Market data subscriptions, ticks, quotes, and bars must not pass through the order execution adapter.
- Order submit/cancel/replace and execution reports must not pass through the market data adapter.
- Orders still flow through Risk and OrderManager before reaching IBKR paper execution.

### Verification

```bash
make test-integration
make test-anchor
```

---

## Phase 9: Frontend console

### Goal

Provide a UI for monitoring and controlling strategies, accounts, risk, orders, and system status.

### Scope

- Account view.
- Strategy view.
- Order view.
- Risk view.
- Market data view.
- System status view.

### Design rules

- Frontend consumes backend APIs.
- Frontend must not duplicate trading logic.
- Trading actions must call explicit backend APIs.

### Verification

Use frontend test/lint commands once frontend tooling is added, plus backend API integration tests.

---

## Phase 10: IBKR live trading readiness

### Goal

Promote the tested IBKR paper adapter path to live trading readiness after paper behavior, reconciliation, and operational controls are stable.

### Scope

- IBKR live configuration profile.
- Live account permission and environment separation.
- Credential/config handling.
- Reconnect behavior.
- Broker report normalization.
- Order reconciliation.
- Manual cutover and rollback checklist.

### Design rules

- IBKR market data and order execution remain separate adapter boundaries.
- Order execution adapters must not mutate account or portfolio state directly.
- All broker reports must be converted to internal events.
- Secrets must not be committed.
- Live mode must not reuse paper account IDs, client IDs, credentials, or risk limits by accident.

### Verification

- Adapter contract tests.
- Integration tests with fake broker transport.
- Manual paper/live readiness checklist.
