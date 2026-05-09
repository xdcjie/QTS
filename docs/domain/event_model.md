# Event Model

Events should be immutable and traceable.

Recommended metadata:

- event_id
- event_type
- source_actor
- target_actor
- account_id
- strategy_id
- instrument_id
- order_id
- event_time
- bar_time
- seq
- partition_key
- correlation_id
- causation_id
- market_data_source_id
- broker_id

Use `correlation_id` to group a business workflow and `causation_id` to trace which event triggered the next event.

## Market data aggregation events

Stateful bar aggregation produces events at the actor boundary, not direct method calls into
strategies.

Recommended event types:

- `market_data.bar.input`: normalized lower-timeframe bar accepted by `MarketDataActor`.
- `market_data.bar.closed`: finalized bar emitted from `AggregationResult.completed`.
- `market_data.bar.dropped`: source bar rejected because it is outside the active session.

Rules:

- `MarketDataActor` owns `BarAggregator` and `AggregationState`.
- `AggregationState` is not an event payload for strategies; it is internal actor state.
- `market_data.bar.closed` carries the finalized `Bar` with explicit `start_time`,
  `end_time`, `timeframe`, and `session_id`.
- Event `partition_key` for aggregation should include `instrument_id`, `timeframe`, and
  `session_id` so ordering is preserved per bar stream.
- `causation_id` should link `market_data.bar.closed` to the input bar event that completed
  or flushed the bucket.

## Execution events

Order execution events are separate from market data events.

Recommended event types:

- `execution.order.submitted`: internal order accepted for adapter submission.
- `execution.report.received`: normalized broker report received from an order execution adapter.
- `execution.fill.accepted`: fill accepted by OrderManager after idempotency checks.

Rules:

- Execution reports originate from order execution adapters, not market data adapters.
- Market data events must not mutate order, account, or portfolio state directly.
- Execution events must preserve `broker_id`, `account_id`, `order_id`, `correlation_id`,
  and `causation_id` when available.
