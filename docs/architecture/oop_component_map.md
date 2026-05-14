# OOP Component Map (2026-05-12)

## Top-level package ownership map

### `qts.core`
Owner: stable primitives and helper services.

- Value/object classes: IDs (`AccountId`, `BrokerId`, `OrderId`, `StrategyId`, `InstrumentId`), time types, hashing helpers.
- Should stay free of runtime, API, broker, and persistence behavior.
- Current split: mostly clean.

### `qts.domain`
Owner: pure trading invariants and data models used by multiple modes.

- Domain entities/value objects: instruments, market-data value types, portfolio/account snapshots, orders/fills/decisions where stable.
- Must stay independent from actor internals, broker protocols, and API DTOs.
- Includes stable rules consumed by backtest and live modes.

### `qts.registry`
Owner: instrument metadata and trading metadata resolution.

- `InstrumentRegistry`, futures chain/roll, broker-symbol mappings, calendar providers.
- Shared for backtest/live/paper; should not include mode-specific orchestration.

### `qts.data`
Owner: market data ingestion and session/bar semantics.

- Historical source parsing/config (`data.historical`), bars aggregation/alignment, sessions.
- Should stay clear of order lifecycle, risk decisions, and actor ownership state.

### `qts.portfolio`
Owner: portfolio accounting and position/cash modeling.

- Position books, valuation models, accounting utilities.
- Must remain decoupled from `AccountActor` and broker callback handling.

### `qts.risk`
Owner: pre-trade risk policy and decision objects.

- Limits, guards, kill-switch rules, risk decisions.
- Should consume domain primitives only; should not mutate order/account state directly.

### `qts.execution`
Owner: execution lifecycle and broker abstraction boundaries.

- `OrderManager` lifecycle logic, broker adapters, simulated/live broker implementations.
- Domain order/fill/status concepts should be imported from domain modules, not defined ad hoc.

### `qts.runtime`
Owner: Actor + Queue orchestration.

- Actors, routers, event store, startup/runtime lifecycle, actor clocks.
- Each actor owns its mutable state and communicates via messages.

### `qts.strategy_sdk`
Owner: user-facing strategy API facade.

- Strategy lifecycle, strategy context, data/portfolio views, target APIs.
- Must delegate heavy logic to collaborators and avoid direct runtime/execution internals.

### `qts.backtest`
Owner: backtest composition and replay orchestration.

- Configured backtest composition, deterministic replay, report entrypoint.
- Should not own shared domain semantics that apply to live/paper; those belong in shared packages.

### `qts.application`
Owner: use-case orchestration for API/CLI flows.

- Command handlers and workflow composition.
- Thin wrappers around domain/runtime services; should not own reusable business logic.

### `qts.api`
Owner: external contract exposure.

- FastAPI app, schemas, routes, websocket surfaces.
- Must remain API-shaped DTO boundaries and not expose domain mutable internals.

### `qts.load`
Owner: bootstrap/replay data generation helpers.

- Deterministic test/data generation utilities; no ownership of trading domain rules.

## Current high-risk split candidates

- `qts.backtest.engine.BacktestEngine`: mixes actor loop orchestration, intent handling, instrument resolution, artifact sink, and projection.
- `qts.backtest.config.BacktestRunConfig`: mixes config values with parsing/validation/hashing.
- `qts.strategy_sdk.context.StrategyContext`: facade does resolution + target + subscription internals in one class.
- `qts.execution.order_manager.OrderManager`: imports/defines domain-like order artifacts in mixed layers.

## Immediate placeholders to resolve

- None currently tracked in production code.

## Next validation checkpoints

1. Run `make format`, `make lint`, `make typecheck`, `make test-unit`, `make test-integration`, `make test-anchor`.
2. Confirm component ownership against `docs/architecture/module_boundaries.md`.
3. Run guardrail checks before larger refactors (`BacktestEngine`, `StrategyContext`, config loaders).
