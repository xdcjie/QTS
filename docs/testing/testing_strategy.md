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
make guardrails
make check
```

## Rules

- Bug fixes should include regression tests when practical.
- Actor/order/account flows require integration tests.
- IBKR paper/live adapter flows require fake-transport integration tests.
- Market sessions, bar aggregation, portfolio accounting, and order state invariants require anchor tests.
- Market data subscription deduplication and provider source timeframe semantics require anchor tests.
- Domain-sensitive implementation must pass `make guardrails`; these checks
  enforce architecture boundaries that tests alone do not prove.

## Domain-sensitive change gate

Before changing sessions, bar generation, instrument identity, broker adapters,
strategy SDK boundaries, risk, order flow, portfolio/accounting, or backtest/live
runtime parity, write down the gate in the implementation notes or PR:

```text
Domain fact:
Correct abstraction boundary:
Forbidden shortcut:
Verification:
```

The change should not proceed until the abstraction boundary is explicit. If a
rule is product-, broker-, strategy-, or environment-specific, it must enter the
system through the right boundary: registry/spec/session data, broker adapters,
strategy code, configuration, or documented policy objects.

## Guardrail checks

`make guardrails` runs `scripts/verify_guardrails.py`. It blocks common cases
where written standards are otherwise easy to miss:

- product-specific symbols such as `GC` or `SI` in shared core implementation
  instead of registry/provider/session/risk data boundaries;
- broker-specific identifiers such as `IBKR` outside config or adapter
  boundaries;
- `domain` importing runtime, execution, data, API, or other upper layers;
- `strategy_sdk` importing runtime, execution, risk, registry, data, backtest,
  application, API, or workers;
- market-data adapters importing execution/risk/portfolio/runtime;
- order-execution adapters importing data;
- shared roll/session/resolution modules placed under source-specific
  boundaries such as `qts.backtest` or `qts.data.historical`;
- new module-level public factory functions for stable concepts instead of
  class-owned construction APIs;
- module-private helpers beside a single public class when the helper should be
  owned by that class.

Guardrail exceptions must be narrow and expressed in `scripts/verify_guardrails.py`
with tests that prove both the allowed boundary and the forbidden shortcut.

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

## Market data subscription test expectations

- Unit tests cover logical-to-physical subscription planning and fan-out bookkeeping.
- Unit tests cover historical data source capability checks and deterministic replay events.
- Integration tests prove historical and live/fake market data sources use the same
  actor-facing message contract.
- Anchor tests protect the rule that provider source timeframe capability cannot
  redefine requested bar semantics.
