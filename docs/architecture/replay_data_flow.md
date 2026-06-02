# Replay Data Flow

## Canonical replay flow

Replay-backed research, optimizer, and backtest work enters through the catalog
and replay bundle boundary:

```text
HistoricalCatalog.load(...)
  -> ReplayMarketDataBundleBuilder
  -> ReplayMarketDataSource / SubscriptionReplayMarketDataSource
  -> MarketDataActor / MarketDataFlow
  -> Strategy SDK data views
```

`ReplayFeed` is the small store-backed library surface for deterministic stored
bar replay. `HistoricalMarketDataAdapter` owns historical source adaptation.
`InMemoryMarketDataStore` and `ParquetMarketDataStore` own persistence choices.
None of these are paper/live launch shortcuts; promotion must still materialize
a `RuntimeLaunchPlan` before runtime start.
