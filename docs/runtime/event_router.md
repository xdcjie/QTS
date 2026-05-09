# Event Router

The router maps events to actor mailboxes by partition key.

Rules:

- Do not let senders call receiver handlers directly.
- Use `ActorRef.tell(event)` semantics.
- Routing decisions should be explicit and testable.
- Events should preserve correlation_id and causation_id.

Example routes:

- `MarketDataSubscriptionRequest` -> `MarketDataActor(market_data_source_id)`
- `TickEvent` / `QuoteEvent` / `BarEvent` -> `StrategyActor(strategy_id)` and market data stores
- `SignalEvent` -> `SignalAggregatorActor`
- `TargetPositionEvent` -> `AccountActor(account_id)`
- `OrderRequest` -> `OrderManagerActor(account_id)`
- `SendOrderRequest` -> `ExecutionActor(broker_id, account_id)`
- `ExecutionReport` -> `OrderManagerActor(account_id)`
- accepted fill/account delta -> `AccountActor(account_id)`

Market data events must not be routed through the order execution actor. Order
execution reports must not be routed through the market data actor. Providers
such as IBKR can back both adapters, but router keys and message types remain
separate.
