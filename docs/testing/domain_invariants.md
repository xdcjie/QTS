# Domain Invariants

Anchor tests should protect these invariants.

Implementation guardrails should protect the abstraction boundaries that anchor
tests cannot prove from output alone. Domain-sensitive changes must define:

```text
Domain fact:
Correct abstraction boundary:
Forbidden shortcut:
Verification:
```

`make guardrails` must pass before claiming a domain-sensitive change is ready.

## Calendar/session

- Sessions use `[start, end)`.
- Timezones do not redefine sessions.
- COMEX Gold normal `[ET 18:00, ET 17:00)` 1m session has 1380 bars.

## Bar aggregation

- `<1d` bars are clock-aligned.
- `1d` bars are session-aligned.
- 1m -> 5m uses `[00m, 05m)`, `[05m, 10m)`, ..., `[55m, next hour 00m)`.
- `1d != 24h`.
- Requested timeframe is strategy intent; source timeframe is provider capability.
- A provider that supplies `5s` bars must not redefine `1m` or `5m` requested bar semantics.
- A coarse historical source must reject requests for finer bars instead of fabricating them.

## Market data subscriptions

- Multiple logical subscribers for the same instrument and derived timeframe share one derived stream.
- Multiple derived timeframes for the same instrument share one physical source subscription when provider capability permits.
- `MarketDataActor` owns subscription deduplication, aggregation state, and fan-out state.
- Market data source adapters do not own strategy subscriber lists.

## Instrument identity

- Domain uses `InstrumentId`.
- Broker symbols do not leak into domain models.
- Continuous futures are not directly tradable.
- Product-specific facts do not appear as shared implementation branches such as
  `if root == "GC"` or `gc_*` helpers. They belong in registry/spec/session data
  boundaries, product-specific providers, or documented risk/valuation models.

## Order lifecycle

- Fill does not directly mutate account state.
- Duplicate fills are idempotent.
- Out-of-order broker reports do not corrupt state.
- Market data adapters do not submit or reconcile orders.
- Order execution adapters do not own market data subscriptions or bar aggregation.
- Broker-specific behavior belongs in config or broker/data-source adapters, not
  shared runtime, domain, portfolio, risk, or strategy SDK code.

## Portfolio accounting

- Equity notional = quantity * price.
- Future PnL = contracts * price_diff * multiplier.
- Option premium value = contracts * option_price * multiplier.
