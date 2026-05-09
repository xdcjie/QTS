# Anchor Tests

Anchor tests protect correctness invariants that must not change due to implementation convenience.

Examples:

- Market session count invariants
- Bar bucket boundaries
- Instrument identity rules
- Order state machine legal transitions
- Portfolio accounting formulas
- Strategy SDK boundary rules
- IBKR adapter boundary rules for separating market data from order execution

Anchor tests are expected to be stable, explicit, and tied to domain facts.
