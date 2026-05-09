# Indicator Model

Indicators are time-series transformations.

## Indicator types

- Single-asset indicators: SMA, EMA, RSI, MACD, ATR, realized vol
- Futures indicators: basis, roll yield, term structure
- Options indicators: IV rank, IV percentile, skew, Greeks

## Requirements

- Incremental update support
- Warmup support
- `ready` state
- Snapshot/restore support for live restart

User-facing access should be through `ctx.indicator`.
