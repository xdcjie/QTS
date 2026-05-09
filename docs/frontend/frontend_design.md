# Frontend Design

The frontend is a console, not a trading logic engine.

Views:

- Dashboard
- Accounts
- Strategies
- Orders
- Risk
- Market data
- Backtests
- Logs / system health

Rules:

- Consume backend APIs.
- Do not duplicate trading logic.
- Do not hardcode broker-specific assumptions.
- Trading actions must call explicit backend endpoints.
