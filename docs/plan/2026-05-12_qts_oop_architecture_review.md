# QTS Python OOP / Abstraction / Naming Review

Date: 2026-05-12
Input: `CODE_INVENTORY(1).md`
Scope: non-test Python classes, functions, methods, and static call relationships.

## Executive summary

The project has improved significantly compared with the earlier inventory: backtest responsibilities have already been split into modules such as `actor_loop`, `intent_processor`, `portfolio_projection`, `inputs`, `sinks`, and `report`; the project now also has a central `qts.quality.guardrails` module instead of relying only on textual rules. However, the current inventory still shows several OOP and abstraction issues that should be resolved before growing the system further.

The most important remaining theme is not “make everything a class.” The right rule is:

> Use classes for stable concepts with state, configuration, lifecycle, invariants, dependencies, or a coherent public interface. Use module functions for stateless algorithms, framework entrypoints, thin compatibility wrappers, or pure transformations.

That matches the project rules: construction and validation of stable concepts should be owned by the concept itself or by a focused `<Concept>Config`, while runners/CLI/services should orchestrate rather than own data construction, registry resolution, session semantics, or artifact formats.

## Evidence from inventory

The uploaded inventory reports a large Python codebase: `1075` total symbols, `311` classes, `764` functions/methods, `138` module-level functions, and `626` methods/properties. The highest-density files include `qts.quality.guardrails`, `qts.reconciliation`, `qts.data.historical.config`, `qts.execution.broker`, `qts.backtest.config`, `qts.data.live_feed`, `qts.data.historical.csv_dataset`, and `qts.backtest.report`.

The important findings are:

1. `BacktestEngine` is smaller than before, but still accepts a long primitive-heavy constructor and creates several collaborators directly. This violates the project’s construction-config preference and makes test/backtest/live parity harder to reason about.
2. `BacktestActorLoop` has been extracted, which is good, but it accepts many injected collaborators and callbacks. It should have a `BacktestActorLoopConfig` and `BacktestActorLoopDependencies` or `BacktestActorLoopContext` object so the loop owns one coherent runtime concept rather than a long parameter list.
3. `_BacktestExecutionAdapter` still lives inside `qts.backtest.engine`. It is an execution adapter concept and should move to a backtest execution adapter boundary, preferably `qts.execution.simulator` or a dedicated `qts.backtest.execution_adapter` if it remains backtest-specific.
4. `StrategyContext` is correctly acting as the user-facing facade, but its `option(...)` API accepts `InstrumentId` for the underlying. Since the Strategy SDK should hide internal trading complexity, this should be adjusted to accept `AssetRef` or user-level symbols, while the internal resolver may still use `InstrumentId`.
5. `qts.api.routes.operations` contains Pydantic schemas and route handlers in one route module. API routes should be thin entrypoints; request/response schemas should move to `qts.api.schemas.operations` and application DTOs should remain in `qts.application.dto`.
6. `qts.reconciliation` is a single large module containing snapshots, reports, decisions, engine, and helper comparisons. Reconciliation is a stable production concept and should become a package with cohesive files.
7. `qts.data.live_feed` contains capabilities, subscription requests, event DTOs, reconnect policy, adapter protocol, and fake adapter in one file. That is still coherent as “live feed,” but it is now too dense and mixes protocol, DTO, policy, and fake adapter. It should become a package or at least split into concept modules.
8. `qts.quality.guardrails` is large but conceptually acceptable because it is the architecture-gate owner. It should not be deleted; however, its helper algorithms should be reviewed for ownership and eventually split by stable rule families if it grows further.
9. Several scripts are now thin or empty wrappers. Empty non-`__init__` files should not remain ambiguous. They must either be implemented as thin CLI entrypoints delegating to application commands or removed if no documented entrypoint depends on them.
10. Many public classes and methods have no docstring, causing the inventory generator to infer generic descriptions like “Perform x.” Public APIs should have concise docstrings; private methods do not need ceremonial docstrings.

## OOP evaluation by layer

### Core and domain

Current shape appears mostly appropriate: IDs, time ranges, instrument models, bar models, risk decisions, and request/response value objects are stable domain objects and should remain dataclasses or simple value objects. Do not over-classify stateless helpers.

Recommended rule: keep domain models free of API, runtime, broker, and storage dependencies.

### Data and historical data

`qts.data.historical.config` is large but mostly conceptually coherent: historical store defaults, store config, catalog config, dataset config, and resolution behavior belong together if they form a stable historical-data configuration model. However, source parsing should remain in `HistoricalMarketDataConfigLoader`, and runtime iteration should remain outside config objects.

`qts.data.live_feed` needs concept splits because it combines protocol, DTOs, reconnect policy, and fake adapter.

### Bars

`qts.data.bars.aggregator`, `alignment`, `pipeline`, and `timeframe` are conceptually well placed. Bar aggregation should remain in data, not runtime or strategy. The streaming aggregator should be a class; alignment helpers can be stateless functions.

### Backtest

Backtest is the area most in need of disciplined OOP ownership. The project rules already say runners may wire a run together but must not own reusable data construction or roll/session semantics. The inventory shows improvement, but the remaining long constructors and inner adapter show that construction still needs to be moved into cohesive config/dependency objects.

### Runtime and actors

The runtime modules are appropriately actor-oriented. The main review point is to keep actors owning state, while avoiding direct cross-actor business method calls. Actor loops can orchestrate but should not reconstruct registries, load datasets, or own broker/data adapter semantics.

### Execution

`qts.execution.order_manager` looks like an appropriate stateful OOP owner. `qts.execution.broker` contains several related value objects and protocols. It can remain a single module for now, but if it grows further split by capability/request/report/adapter.

### Strategy SDK

`StrategyContext` should remain a user-facing facade. The facade is allowed to have several small methods because usability matters. But it must not expose internal `InstrumentId`, `ContractSpec`, broker symbols, actor types, or order manager internals. Its job is to delegate to `StrategyAssetResolver`, `TargetEmitter`, subscription registry, `DataView`, and `PortfolioView`.

### API

Routes should be thin. Pydantic schemas should live under `qts.api.schemas`. Application commands and DTOs should live in `qts.application`. The route layer should not own business decisions.

### Quality/guardrails

The guardrails module is important and should be treated as an architecture gate. Its presence is a positive sign. The next step is to prevent it from becoming a giant script-like file by introducing rule-family modules only when that improves cohesion.

## Priority problems

### P0 — Fix before adding major features

1. Backtest construction overload.
2. Backtest execution adapter living inside `engine.py`.
3. Strategy SDK option API exposing internal `InstrumentId` at user boundary.
4. Empty or ambiguous script wrappers.
5. Ensure `make guardrails` remains a required gate.

### P1 — Fix during next refactor milestone

1. Split `qts.reconciliation` into a package.
2. Split `qts.data.live_feed` into cohesive concepts.
3. Move API operation schemas out of route module.
4. Add public docstrings for stable public APIs.
5. Strengthen guardrails for Strategy SDK and backtest/live parity boundaries.

### P2 — Monitor and only refactor when pressure appears

1. Split `qts.execution.broker` only if it grows beyond the current cohesive boundary.
2. Split `qts.quality.guardrails` by rule family only after adding tests and preserving its CLI/API.
3. Split historical config only if it starts opening datasets or constructing runtime iterators.

## Do not do

- Do not turn all functions into classes.
- Do not split every helper into its own file.
- Do not delete static no-caller symbols without checking dynamic entrypoints, protocols, framework route registration, package exports, docs, and CLI references.
- Do not move backtest-only behavior into live/runtime modules unless the behavior truly belongs in the shared path.
- Do not make Strategy SDK users handle `InstrumentId`, broker symbols, or internal actor objects.

## Target architecture after cleanup

```text
qts.backtest
  config.py                  # BacktestRunConfig, cost model, run options
  engine.py                  # BacktestEngine facade/orchestrator only
  actor_loop.py              # BacktestActorLoop + config/dependencies/context
  inputs.py                  # BacktestInputBuilder and input assembly
  execution_adapter.py       # only if adapter remains backtest-specific
  report.py / sinks.py       # artifact/report ownership

qts.execution.simulator
  fill_model.py
  simulated_broker.py
  backtest_execution_adapter.py   # preferred if shared with simulation semantics

qts.strategy_sdk
  context.py                 # user-facing facade
  asset_resolver.py           # internal resolver
  target_emitter.py           # target intent emission
  subscription_registry.py    # subscriptions

qts.reconciliation
  snapshots.py
  drift.py
  report.py
  engine.py
  startup_gate.py

qts.data.live
  capabilities.py
  subscriptions.py
  events.py
  reconnect.py
  adapter.py
  fake_adapter.py
```

## Review conclusion

The project is moving in the right direction: actor/runtime, backtest components, data/bars, Strategy SDK, and quality guardrails are now recognizable layers. The remaining work is mainly to reduce constructor overloads, keep user-facing APIs clean, split dense production concepts, and delete or convert ambiguous wrappers.
