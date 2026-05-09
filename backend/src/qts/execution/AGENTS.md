# Execution Rules

This module owns order lifecycle and broker-facing order execution abstractions.

Rules:

- Order state must be updated only through OrderManager logic.
- Broker reports must be normalized before affecting internal state.
- Fills must be idempotent.
- Broker callbacks must not directly mutate portfolio/account state.
- Order lifecycle transitions must be tested with unit and anchor tests.
- Broker-specific order behavior belongs in execution adapters, not domain models.
- Market data subscriptions, ticks, quotes, and bars belong in data adapters, not execution adapters.
