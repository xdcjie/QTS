# Strategy API

User strategies should focus on research and trading intent.

## User-facing objects

- `Strategy`
- `StrategyContext`
- `AssetRef`
- `DataView`
- `PortfolioView`
- `IndicatorFactory`
- `FactorFactory`
- `Universe`
- target APIs

## Preferred methods

```python
ctx.target_percent(asset, 0.5)
ctx.target_quantity(asset, 100)
ctx.target_value(asset, 50_000)
ctx.rebalance(weights)
ctx.close(asset)
```

These methods emit intents. They do not mutate portfolio state directly.

## Hidden internals

User strategies must not access:

- Actor runtime
- Order execution adapters
- Market data adapters
- RiskEngine internals
- OrderManager internals
- ContractSpec
- BrokerSymbolMapping
