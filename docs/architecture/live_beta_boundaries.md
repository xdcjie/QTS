# Live Beta Boundaries

## Broker Execution

`qts.execution.broker` defines `BrokerCapabilities`, `BrokerAdapter`, `BrokerOrderRequest`,
`BrokerExecutionReport`, and `FakeBrokerAdapter`.

Broker and vendor identifiers stay at the adapter boundary. Internal flows keep using
`InstrumentId`, `AccountId`, `StrategyId`, and `OrderId`. Broker reports are normalized before they
can affect `OrderManager`.

## Live Market Data

`qts.data.live` defines `FeedCapabilities`, `LiveFeedAdapter`, `FeedSubscription`,
`ReconnectPolicy`, and `FakeLiveFeedAdapter`.

Feed events carry normalized `Tick`, `Quote`, or `Bar` payloads. Bar aggregation remains owned by
the data/runtime path through `MarketDataActor` and existing timeframe/session semantics.

## Reconciliation

`qts.reconciliation` compares internal and broker snapshots and emits deterministic
`ReconciliationReport` data. It does not directly change account, order, or portfolio state.
