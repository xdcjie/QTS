# Milestones and Acceptance Criteria

This document converts the implementation plan into milestone-level acceptance criteria.

A milestone is complete only when its deliverables are implemented, documented where necessary, and verified with the required checks.

## Verification command tiers

### Fast local verification

Use for small local changes that do not affect integration behavior.

```bash
make format
make lint
make typecheck
make test-unit
```

### Integration verification

Use when changing runtime flow, actor coordination, order flow, portfolio flow, broker simulation, IBKR adapter behavior, API behavior, or cross-module behavior.

```bash
make test-integration
```

### Anchor verification

Use when changing financial domain semantics, market calendars, sessions, bar generation, instrument identity, order state machines, portfolio accounting, risk semantics, or Strategy SDK boundaries.

```bash
make test-anchor
```

### Full milestone verification

Run before considering a milestone complete.

```bash
make check
```

---

## Milestone 0: Repository readiness

### Deliverables

- Python package imports correctly.
- `uv sync` succeeds.
- `Makefile` targets exist.
- `pyproject.toml` contains ruff, mypy, pytest configuration.
- Test directories exist.
- Agent instructions exist at root and module levels.

### Acceptance criteria

- `make check` passes.
- `docs/README.md` explains reading order.
- `MANIFEST.md` accurately describes repository contents.

---

## Milestone 1: Core and domain model foundation

### Deliverables

- Stable ID/value-object model.
- Time interval model using `[start, end)`.
- Instrument and ContractSpec model.
- Bar model with explicit start/end times.
- Base event metadata model.

### Acceptance criteria

- Domain models do not import runtime, API, order execution adapters, market data adapters, storage, or frontend modules.
- Domain identifiers use `InstrumentId`, not broker symbols.
- Unit tests cover ID/value-object creation and equality.
- Anchor tests cover instrument identity and bar interval semantics.

### Required checks

```bash
make test-unit
make test-anchor
make typecheck
```

---

## Milestone 2: Calendar, session, and bar aggregation correctness

### Deliverables

- Calendar registry interface.
- `exchange-calendars` wrapped behind project interfaces.
- Timeframe model distinguishing `CLOCK` and `SESSION` timeframes.
- Bar alignment helpers.
- Stateful `BarAggregator` for supported timeframe chain:
  - `5s -> 1m -> 5m -> 15m -> 30m -> 1h -> 4h -> 1d`
- `AggregationState` for current bucket state.
- `AggregationResult` returned by incremental `update` / `finish`.

### Acceptance criteria

- Intraday bars are clock-aligned in exchange time.
- `1d` bars are session-aligned and are not treated as 24-hour bars.
- Aggregation uses `[start, end)` intervals.
- Session-outside data does not enter aggregated bars.
- Aggregation state is owned per `(instrument_id, timeframe, session_id)` stream.
- Only finalized `AggregationResult.completed` bars flow to events, `DataView`, and strategies.
- `AggregationState` does not leak through Strategy SDK APIs.
- COMEX Gold normal session anchor test expects `1380` one-minute bars for `[ET 18:00, ET 17:00)` excluding holidays and special sessions.

### Required checks

```bash
make test-unit
make test-anchor
```

---

## Milestone 3: Strategy SDK minimal user experience

### Deliverables

- `Strategy` base class.
- `StrategyContext`.
- `AssetRef`.
- `DataView`.
- `PortfolioView`.
- Target APIs:
  - `target_percent`
  - `target_quantity`
  - `target_value`
  - `rebalance`
  - `close`
- Example moving-average strategy.

### Acceptance criteria

- User strategies can express trading intent without importing internal modules.
- Strategy target APIs generate intents rather than mutating portfolio state.
- Strategy SDK does not expose Actor, Broker, RiskEngine, OrderManager, ContractSpec, or BrokerSymbolMapping.
- `DataView` exposes time-sliced finalized bars and does not expose `BarAggregator` or `AggregationState`.
- Example strategy imports only from Strategy SDK.

### Required checks

```bash
make test-unit
make test-anchor
```

---

## Milestone 4: Portfolio, risk, and execution primitives

### Deliverables

- Position and account books.
- Cash/reservation model.
- Basic valuation and PnL calculators.
- Risk engine with explicit decisions.
- Order manager and order state machine.
- Fill idempotency logic.

### Acceptance criteria

- Risk checks cannot be bypassed in the order path.
- Order state transitions are explicit and tested.
- Duplicate fills are idempotent.
- Broker reports do not directly mutate portfolio/account state.
- Portfolio accounting anchor tests cover stock, future, and option notional/PnL semantics as implemented.

### Required checks

```bash
make test-unit
make test-anchor
```

---

## Milestone 5: Actor runtime integration

### Deliverables

- Actor base implementation.
- Mailbox and actor references.
- Event router and partitioning.
- MarketDataActor-owned `BarAggregator` state per aggregation stream.
- AccountActor.
- OrderManagerActor.
- MarketDataActor.
- ExecutionActor.
- StrategyActor.
- Minimal integration flow test.

### Acceptance criteria

- Actor-to-actor coordination uses messages.
- MarketDataActor emits finalized bar events from `AggregationResult.completed`.
- StrategyActor receives finalized bars through messages/DataView, not direct aggregator state.
- Actors do not directly call each other's business methods.
- Account state is owned and mutated only by AccountActor.
- Order state is owned and mutated only by OrderManagerActor.
- Market data and order execution use separate actor boundaries.
- End-to-end integration test covers Bar -> Strategy -> Target -> Risk -> Order -> ExecutionActor -> BrokerSimulator -> Fill -> Portfolio.

### Required checks

```bash
make test-unit
make test-integration
make test-anchor
```

---

## Milestone 6: Backtest MVP

### Deliverables

- Backtest engine.
- Replay clock.
- Historical DataView/DataPortal.
- Broker simulator.
- Fill model.
- Basic report output.
- Runnable example script.

### Acceptance criteria

- A sample strategy can run end-to-end over historical/replayed bars.
- Backtest DataView is time-sliced.
- User strategy cannot access future data.
- Simulated fills pass through execution and accounting path.

### Required checks

```bash
python scripts/run_backtest.py
make test-integration
make test-anchor
```

---

## Milestone 7: Application services and API MVP

### Deliverables

- Application service layer.
- DTOs.
- API app.
- Account, strategy, order, risk, market data, and backtest routes.
- WebSocket stream skeleton.

### Acceptance criteria

- API calls application services rather than internal actor objects directly.
- Public API schemas do not leak actor internals.
- Integration tests cover the main API use cases added in this milestone.

### Required checks

```bash
make test-unit
make test-integration
```

---

## Milestone 8: Paper trading runtime

### Deliverables

- IBKR paper order execution adapter.
- IBKR market data adapter.
- Paper profile config with separate market data and order execution connection settings.
- Market data worker skeleton.
- Order execution worker skeleton.
- Runtime event stream for orders/fills/account state.
- Fake IBKR transport tests for paper order and market data flows.

### Acceptance criteria

- Orders flow through Risk and OrderManager before reaching the IBKR paper order adapter.
- Paper fills return through OrderManager before affecting AccountActor.
- Market data subscriptions, ticks, quotes, and bars do not pass through the order execution adapter.
- Order submit/cancel/replace requests and execution reports do not pass through the market data adapter.
- Live broker credentials are not required; paper credentials and paper account permissions are required.

### Required checks

```bash
make test-integration
make test-anchor
```

---

## Milestone 9: Frontend console

### Deliverables

- Frontend app shell.
- Account status view.
- Strategy status view.
- Order status view.
- Risk status view.
- Market data/status view.

### Acceptance criteria

- Frontend consumes backend APIs.
- Frontend does not implement trading logic.
- Trading actions map to explicit backend API calls.
- UI state reflects backend state.

### Required checks

- Frontend lint/test commands once configured.
- Backend API integration tests.

---

## Milestone 10: IBKR live trading readiness

### Deliverables

- IBKR live configuration profile.
- Paper/live environment separation checks.
- Credential/config handling for IBKR live.
- Reconnect and reconciliation plan.
- Operational cutover, rollback, and manual readiness checklist.

### Acceptance criteria

- Broker reports are normalized into internal events.
- IBKR market data and order execution remain separate adapter boundaries.
- Order execution adapters cannot directly modify portfolio/account state.
- Secrets are not committed.
- Risk, OrderManager, and AccountActor boundaries remain intact.
- Live mode cannot accidentally reuse paper account IDs, client IDs, credentials, or risk limits.
- Manual readiness checklist is completed before live trading.

### Required checks

```bash
make check
```
