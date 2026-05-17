# Indicator Model

Indicators are time-series transformations.

## Indicator types

- Single-asset indicators: SMA, EMA, RSI, ATR, Session VWAP, Volume Ratio,
  Bollinger Bands, MACD, ADX, Keltner Channel, Donchian Channel, Stochastic,
  CCI, Williams %R, Rate of Change, Standard Deviation, Historical Volatility,
  OBV, MFI, Accumulation/Distribution, Chaikin Money Flow
- Futures indicators: basis, roll yield, term structure
- Options indicators: IV rank, IV percentile, skew, Greeks

## Anchored core group

The first OPT-07 anchored group exposes these strategy-facing factory methods:

- `ctx.indicator.bollinger_bands(asset, window, standard_deviations=Decimal("2"))`
- `ctx.indicator.macd(asset, fast_window, slow_window, signal_window)`
- `ctx.indicator.rate_of_change(asset, window)`
- `ctx.indicator.adx(asset, window)`
- `ctx.indicator.keltner_channel(asset, window, multiplier=Decimal("2"))`
- `ctx.indicator.donchian_channel(asset, window)`
- `ctx.indicator.stochastic(asset, window, signal_window=3)`
- `ctx.indicator.cci(asset, window)`
- `ctx.indicator.williams_r(asset, window)`
- `ctx.indicator.standard_deviation(asset, window)`
- `ctx.indicator.historical_volatility(asset, window, periods_per_year=Decimal("252"))`
- `ctx.indicator.on_balance_volume(asset)`
- `ctx.indicator.money_flow_index(asset, window)`
- `ctx.indicator.accumulation_distribution(asset)`
- `ctx.indicator.chaikin_money_flow(asset, window)`

Bollinger Bands and MACD return structured values because they produce multiple
series from one price update. ADX, Keltner Channel, Donchian Channel, and
Stochastic also return structured values. Single-series indicators return a
`Decimal`. Each registered indicator must have a deterministic numerical anchor
test before being added to the Strategy SDK factory.

## Requirements

- Incremental update support
- Warmup support
- `ready` state
- Snapshot/restore support for live restart

User-facing access should be through `ctx.indicator`.
