# Domain Invariants

Anchor tests should protect these invariants.

## Calendar/session

- Sessions use `[start, end)`.
- Timezones do not redefine sessions.
- COMEX Gold normal `[ET 18:00, ET 17:00)` 1m session has 1380 bars.

## Bar aggregation

- `<1d` bars are clock-aligned.
- `1d` bars are session-aligned.
- 1m -> 5m uses `[00m, 05m)`, `[05m, 10m)`, ..., `[55m, next hour 00m)`.
- `1d != 24h`.

## Instrument identity

- Domain uses `InstrumentId`.
- Broker symbols do not leak into domain models.
- Continuous futures are not directly tradable.

## Order lifecycle

- Fill does not directly mutate account state.
- Duplicate fills are idempotent.
- Out-of-order broker reports do not corrupt state.
- Market data adapters do not submit or reconcile orders.
- Order execution adapters do not own market data subscriptions or bar aggregation.

## Portfolio accounting

- Equity notional = quantity * price.
- Future PnL = contracts * price_diff * multiplier.
- Option premium value = contracts * option_price * multiplier.
