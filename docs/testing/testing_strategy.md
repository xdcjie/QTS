# Testing Strategy

Testing has three levels:

```text
Unit Tests
  Validate functions, value objects, state machines.

Integration Tests
  Validate module collaboration and runtime flows.

Anchor Tests
  Validate financial/domain correctness invariants.
```

## Commands

```bash
make test-unit
make test-integration
make test-anchor
make check
```

## Rules

- Bug fixes should include regression tests when practical.
- Actor/order/account flows require integration tests.
- IBKR paper/live adapter flows require fake-transport integration tests.
- Market sessions, bar aggregation, portfolio accounting, and order state invariants require anchor tests.

## Bar aggregation test expectations

Because `BarAggregator` is a stateful streaming component, test coverage must include:

- Unit tests for `BarAggregator.update`, `AggregationState`, `AggregationResult`, and `finish`.
- Unit tests for bucket rollover, partial session-close buckets, OHLCV aggregation, and
  session-outside input rejection.
- Integration tests for `MarketDataActor -> BarAggregator -> market_data.bar.closed ->
  DataView -> StrategyActor` once actors are implemented.
- Anchor tests for half-open intervals, exchange-time clock buckets, `1d != 24h`, and COMEX
  Gold `1380` one-minute session count.
- Boundary tests proving `DataView` exposes finalized bars only and does not expose
  `AggregationState`.

## IBKR adapter boundary expectations

- Unit tests cover market data adapter normalization without order methods.
- Unit tests cover order execution adapter normalization without market data methods.
- Integration tests use separate fake transports for IBKR market data and IBKR order execution.
- Anchor tests protect the rule that market data events cannot mutate order/account state directly.
