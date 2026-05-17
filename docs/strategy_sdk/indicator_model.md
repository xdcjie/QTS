# Indicator Model

Indicators are time-series transformations.

## Indicator types

- Single-asset indicators: SMA, EMA, RSI, ATR, Session VWAP, Volume Ratio,
  Bollinger Bands, MACD, Rate of Change
- Futures indicators: basis, roll yield, term structure
- Options indicators: IV rank, IV percentile, skew, Greeks

## Anchored core group

The first OPT-07 anchored group exposes these strategy-facing factory methods:

- `ctx.indicator.bollinger_bands(asset, window, standard_deviations=Decimal("2"))`
- `ctx.indicator.macd(asset, fast_window, slow_window, signal_window)`
- `ctx.indicator.rate_of_change(asset, window)`

Bollinger Bands and MACD return structured values because they produce multiple
series from one price update. Rate of Change returns a `Decimal` percentage.
Each registered indicator must have a deterministic numerical anchor test before
being added to the Strategy SDK factory.

## Requirements

- Incremental update support
- Warmup support
- `ready` state
- Snapshot/restore support for live restart

User-facing access should be through `ctx.indicator`.
