# System Overview

The final architecture is split into twelve layers:

1. Product / UX Layer: frontend console and user interaction
2. API Layer: REST, WebSocket, Admin API
3. Application Layer: use-case orchestration and service entrypoints
4. Strategy SDK Layer: user-facing strategy API
5. Runtime Layer: Actor, event router, clock, scheduler
6. Domain Layer: trading domain models and invariants
7. Market Data Layer: feed adapters, subscriptions, bars, quotes, data stores
8. Registry Layer: instruments, calendars, symbol mappings
9. Portfolio / Accounting Layer: positions, cash, valuation, PnL
10. Risk Layer: pre-trade, intraday, and post-trade risk
11. Execution Layer: OrderManager, order/execution adapters, execution reports
12. Infrastructure Layer: config, DB, logging, metrics, deployment

## Primary runtime flow

```text
MarketDataAdapter
  -> MarketDataActor
  -> StrategyActor
  -> SignalAggregatorActor
  -> AccountActor
  -> RiskActor / RiskEngine
  -> OrderManagerActor
  -> ExecutionActor
  -> OrderExecutionAdapter
  -> External Broker / Simulated Broker
  -> ExecutionActor
  -> OrderManagerActor
  -> AccountActor
```

Market data and order execution are separate external-boundary concerns. A
provider such as IBKR may supply both, but the system models them as separate
adapters, workers, actor mailboxes, configuration, and event streams.

```text
StrategyContext.subscribe(asset, timeframe)
  -> logical market data subscription
  -> MarketDataActor
  -> one physical source subscription per provider capability
  -> MarketDataAdapter / HistoricalDataService
  -> normalized Tick / Quote / Bar events
  -> MarketDataActor aggregation and fan-out
  -> StrategyActor subscribers

IBKR / Historical Data Source
  -> MarketDataAdapter
  -> normalized Tick / Quote / Bar events
  -> MarketDataActor

OrderManagerActor
  -> ExecutionActor
  -> OrderExecutionAdapter
  -> IBKR paper/live account
  -> normalized ExecutionReport / Fill events
```

## User strategy flow

```text
User Strategy
  -> StrategyContext
  -> TargetIntent / OrderIntent
  -> platform-owned portfolio, risk, order, and execution flow
```

Users express desired exposure. The platform decides how to trade safely.
