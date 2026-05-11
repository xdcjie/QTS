# Instrument Model

## Principles

- Use `InstrumentId` internally.
- Do not use broker symbols as internal identifiers.
- Separate instrument identity from broker/data-source mappings.
- Keep source-symbol resolution at adapter/data-source boundaries; do not make
  historical, broker, or live-specific symbols part of internal identity.
- Use composition over deep inheritance.

## Main concepts

- `InstrumentId`: stable internal identity.
- `Instrument`: tradable contract or asset reference.
- `ContractSpec`: tick size, lot size, multiplier, settlement, calendar.
- `DerivativeSpec`: expiry, strike, option right, underlying, exercise style.
- `BrokerSymbolMapping`: boundary mapping only.
- `SourceSymbolResolver`: boundary contract for data-source symbols that resolve
  to `InstrumentId`; historical CSV loaders, broker market data adapters, and
  future live data adapters can share this contract without depending on each
  other.

## Examples

```text
EQUITY.US.NASDAQ.AAPL
FUTURE.CME.ES.202606
OPTION.US.AAPL.20260619.C.200
```

## Continuous futures

Continuous futures are research/data references, not directly tradable instruments. They must resolve to a concrete tradable future contract before order creation.

The shared futures roll boundary is `FutureRollRegistry`. Backtest and live
adapters should both use it, or an equivalent implementation of the same
contract, to resolve a continuous root such as `GC` to the concrete contract
selected at a specific time. Historical CSV loading may build the selection from
same-timestamp candidates, while live adapters may build it from live market
data or a precomputed schedule. In both cases, the order path must receive a
concrete `InstrumentId`.
