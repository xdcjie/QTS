# Order Model

Orders are internal instructions produced after portfolio sizing and risk checks.

## Concepts

- `OrderIntent`: desired order before final approval.
- `Order`: internal order tracked by OrderManager.
- `ExecutionReport`: normalized broker status update.
- `Fill`: execution quantity/price report.

## Rules

- Strategy SDK produces intents, not direct broker orders.
- OrderManager owns order lifecycle.
- Broker callbacks must be normalized before state mutation.
- Fills must be idempotent.
- Fill should not directly mutate account/portfolio state.
- Order execution adapters submit, cancel, replace, and reconcile orders only.
- Market data adapters do not create or mutate order state.
