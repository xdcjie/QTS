# Runtime Flow

## Backtest

```text
HistoricalDataStore
  -> BacktestClock
  -> MarketDataActor
     -> BarAggregator per (instrument_id, timeframe, session_id)
     -> BarClosedEvent / completed Bar
  -> StrategyActor
  -> SignalAggregatorActor
  -> AccountActor
  -> RiskEngine
  -> OrderManagerActor
  -> ExecutionActor
  -> BrokerSimulator
  -> OrderManagerActor
  -> AccountActor
  -> StreamingBacktestArtifacts
```

## Paper / Live

```text
IBKR MarketDataAdapter / LiveMarketDataFeed
  -> MarketDataActor
     -> BarAggregator per (instrument_id, timeframe, session_id)
     -> BarClosedEvent / completed Bar
  -> StrategyActor
  -> SignalAggregatorActor
  -> AccountActor
  -> RiskActor / RiskEngine
  -> OrderManagerActor
  -> ExecutionActor
  -> OrderExecutionAdapter
  -> IBKR paper/live account
  -> ExecutionActor
  -> OrderManagerActor
  -> AccountActor
```

Market data and order execution are separate flows. IBKR can back both in paper
and live modes, but subscriptions and market data events stay in the market data
flow while order requests and execution reports stay in the execution flow.

### Adapter naming map

- `LiveFeedAdapter` / `MarketDataAdapter`:
  live-mode feed contract used by `qts.runtime.actors.MarketDataActor`.
- `ReplayMarketDataAdapter`:
  historical/replay contract in `qts.data.historical.service`.
- `LiveMarketDataAdapter`:
  compatibility alias to `IbkrMarketDataAdapter` in `qts.data.adapters.ibkr_market_data`.

## Ordering rule

Do not require global order. Preserve order by business key:

- account_id
- order_id
- strategy_id
- broker_id
- market_data_source_id
- instrument_id when needed

For bar aggregation, ordering is stricter within each aggregation stream:

- stream key: `(instrument_id, timeframe, session_id)`
- `MarketDataActor` owns the `BarAggregator` instance for that stream.
- Incoming lower-timeframe bars update `AggregationState`.
- Only `AggregationResult.completed` bars are emitted downstream.
- `AggregationState` is actor-owned runtime state and must not be exposed to `StrategyActor`,
  `DataView`, or user strategies.
