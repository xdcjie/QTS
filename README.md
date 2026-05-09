# Quant Trading System

Python-first quantitative trading system scaffold.

## Final target

The system is designed for:

- Multi-strategy and multi-account trading
- Stock, futures, and options
- Backtest, paper trading, and live trading
- Actor + Queue runtime
- User-facing Strategy SDK
- REST/WebSocket API and frontend console
- Financial correctness verified by anchor tests

## Structure

```text
backend/src/qts/
  core/          foundational IDs, time, money, errors
  domain/        pure trading domain models
  registry/      instruments, calendars, symbol mappings
  data/          feed adapters, stores, bar building and aggregation
  indicators/    internal indicator engine
  factors/       cross-sectional factor engine
  portfolio/     positions, accounting, valuation, PnL
  risk/          rules, margin, risk decisions
  execution/     order manager, state machine, order execution adapters
  runtime/       actors, router, clock, event store
  backtest/      historical simulation runtime
  strategy_sdk/  user-facing strategy API
  application/   use-case orchestration
  api/           REST/WebSocket API
  workers/       runtime process entrypoints
  config/        settings and config loading
  observability/ logs, metrics, tracing, audit
```

## Setup

```bash
uv sync
make check
```

## Recommended implementation flow

1. Domain value objects and events
2. Instrument registry and market calendar anchors
3. Bar timeframe and aggregation model
4. Strategy SDK minimal API
5. Single-threaded backtest loop
6. Actor runtime and account/order state machines
7. API and frontend
8. IBKR paper runtime with separate market data and order execution adapters
9. IBKR live readiness with reconciliation and operational controls

See `docs/plan/implementation_plan.md`, `docs/plan/milestones_and_acceptance.md`, `docs/architecture/system_overview.md`, and `docs/architecture/dependency_rules.md`.
