# Architecture Review Checklist

Use this checklist before closing a milestone or approving a cross-module change.

## Dependency Rules

- Domain code depends only on `qts.core`.
- Strategy SDK does not import runtime, risk internals, order execution adapters, or market data adapters.
- API routes call application services instead of actor internals.
- Frontend consumes API DTOs and does not implement trading logic.
- Provider-specific code stays behind data or execution adapter boundaries.

## Actor Boundaries

- Actors communicate through messages, not direct business method calls.
- `AccountActor` owns account state.
- `OrderManagerActor` owns order state.
- `MarketDataActor` owns market data subscription and aggregation stream state.
- `ExecutionActor` owns order execution adapter interaction.
- Market data events do not flow through `ExecutionActor`.
- Order submit/cancel/replace and execution reports do not flow through `MarketDataActor`.

## Strategy SDK Boundaries

- User strategies import only Strategy SDK-facing APIs.
- Target APIs produce intents and do not mutate portfolio state.
- `DataView` exposes finalized, time-sliced data only.
- Strategy code cannot access `ContractSpec`, `BrokerSymbolMapping`, RiskEngine, OrderManager, or adapters.

## Financial Correctness

- Market sessions are defined by exchange rules, not storage timezone.
- Bars use `[start, end)` intervals.
- Intraday bars are clock-aligned in exchange time.
- Daily bars are session-aligned, not 24-hour bars.
- Orders pass through risk checks before execution.
- Broker reports are normalized before affecting internal state.

## Verification

- Run focused tests for the changed modules.
- Run `make test-integration` for actor, API, order, portfolio, or adapter flow changes.
- Run `make test-anchor` for financial/domain invariant changes.
- Run `make check` before milestone completion.
