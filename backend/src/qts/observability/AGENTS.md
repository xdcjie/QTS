# Observability Rules

This module owns logging, metrics, tracing, and audit helpers.

Rules:

- Use structured logs.
- Preserve event_id, correlation_id, causation_id, account_id, strategy_id, instrument_id, and order_id where available.
- Do not log secrets.
