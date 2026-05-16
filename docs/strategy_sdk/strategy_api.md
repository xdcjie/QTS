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

## Indicators

Indicators are created through `ctx.indicator` and are updated by the runtime
from completed strategy-facing bars. Strategy code should read indicator values
inside `on_bar`; it should not call indicator update methods manually.

```python
MA_20 = ctx.indicator.ema(asset, window=20)
ATR_7 = ctx.indicator.atr(asset, window=7)
RSI_14 = ctx.indicator.rsi(asset, window=14)
VWAP = ctx.indicator.session_vwap(asset)
VOL_20 = ctx.indicator.volume_ratio(asset, window=20)
```

## Hidden internals

User strategies must not access:

- Actor runtime
- Order execution adapters
- Market data adapters
- RiskEngine internals
- OrderManager internals
- ContractSpec
- BrokerSymbolMapping
