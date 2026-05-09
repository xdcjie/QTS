# Instrument Model

## Principles

- Use `InstrumentId` internally.
- Do not use broker symbols as internal identifiers.
- Separate instrument identity from broker/data-source mappings.
- Use composition over deep inheritance.

## Main concepts

- `InstrumentId`: stable internal identity.
- `Instrument`: tradable contract or asset reference.
- `ContractSpec`: tick size, lot size, multiplier, settlement, calendar.
- `DerivativeSpec`: expiry, strike, option right, underlying, exercise style.
- `BrokerSymbolMapping`: boundary mapping only.

## Examples

```text
EQUITY.US.NASDAQ.AAPL
FUTURE.CME.ES.202606
OPTION.US.AAPL.20260619.C.200
```

## Continuous futures

Continuous futures are research/data references, not directly tradable instruments. They must resolve to a concrete tradable future contract before order creation.
