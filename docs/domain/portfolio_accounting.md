# Portfolio Accounting

## Main responsibilities

- Position book
- Cash balances
- Reservation/frozen cash
- Market value
- Notional exposure
- Realized and unrealized PnL

## Cross-product formulas

- Equity notional: `quantity * price`
- Future exposure: `contracts * price * multiplier`
- Future PnL: `contracts * price_diff * multiplier`
- Option premium value: `contracts * option_price * multiplier`

## State ownership

Account state is mutated only by `AccountActor`. Broker or strategy code must never directly mutate portfolio state.
