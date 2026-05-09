# Actor Model

## Rule

Use Actor as the architectural abstraction and Queue as the mailbox implementation.

## Principles

- Actor owns its state.
- Actor processes mailbox messages sequentially.
- Actors communicate only by messages.
- Do not directly call another actor's business methods.
- Preserve per-key ordering, not global ordering.

## Recommended actors

- `MarketDataActor`
- `StrategyActor`
- `SignalAggregatorActor`
- `AccountActor(account_id)`
- `RiskActor`
- `OrderManagerActor(account_id)`
- `ExecutionActor(broker_id, account_id)`

## Key partitioning

- account_id -> AccountActor
- order_id / account_id -> OrderManagerActor
- strategy_id -> StrategyActor
- market_data_source_id / instrument_id -> MarketDataActor
- broker_id / account_id -> ExecutionActor

## External adapter boundaries

Market data and order execution must be separate actor-facing boundaries. Even
when both use IBKR, market data subscriptions, quotes, ticks, and bars flow
through `MarketDataActor`, while order submission, cancel/replace, execution
reports, and fills flow through `ExecutionActor` and `OrderManagerActor`.

Neither actor may directly mutate account state. Account changes happen only
after normalized execution reports are accepted by the order/account flow.
