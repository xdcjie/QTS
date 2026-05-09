# REST API Design

The API layer exposes use cases through schemas and application services.

Initial resources:

- Accounts
- Strategies
- Backtests
- Orders
- Risk
- Market data
- System health

Rules:

- API must not expose actor internals.
- API should call application services.
- Public schemas should be explicit DTOs.
