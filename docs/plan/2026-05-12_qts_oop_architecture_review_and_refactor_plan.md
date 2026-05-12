# 2026-05-12 — Quant Trading System OOP Architecture Review and Refactor Plan

## 0. Scope and source of truth

This review is based on `CODE_INVENTORY.md`, a static inventory of non-test Python symbols and call relationships. It covers all repository `.py` files except tests, virtual environments, cache, and build directories.

Important limitation: static call extraction does not reliably detect framework entrypoints, dependency injection, dynamic dispatch, CLI entrypoints, FastAPI route discovery, callbacks, runtime reflection, or external imports. Therefore, this plan does **not** treat “no static caller” as proof that a symbol is unused. Deletion tasks below require import checks, runtime tests, and owner approval before removal.

## 1. Executive summary

The project has a clear layered intent and many good building blocks for a Python-first quant trading system, but the current class/function inventory shows several OOP and maintainability risks:

1. **God-object risk in `BacktestEngine`**: `backend/src/qts/backtest/engine.py` has 46 symbols, and `BacktestEngine` spans `121-877`. It mixes actor-loop orchestration, intent processing, order delta handling, instrument registry construction, portfolio view projection, payload serialization, rolling price updates, future-roll handling, artifact sink management, and stable hashing.
2. **Configuration classes mix data model, parsing, serialization, validation, and hashing**: `BacktestRunConfig` and historical data config modules show high method counts and high call complexity.
3. **Some modules are placeholders or empty**: non-`__init__` empty modules such as `backend/src/qts/data/bars/builder.py` and `backend/src/qts/data/bars/validation.py` should either be implemented according to the design or removed if unused.
4. **Domain models are not fully separated from execution/application concerns**: order-related domain objects appear inside `qts.execution.order_manager`, while design rules require domain objects for orders, fills, positions, portfolio state, and risk decisions to live in domain/core boundaries.
5. **Strategy SDK facade is doing too much**: `StrategyContext` has multiple resolver protocols, symbol/future/option resolution, target emission, subscription capture, and context state in one file. It should remain the user-facing facade but delegate internally.
6. **Scripts contain reusable business logic**: IBKR evidence and drill scripts contain validation and workflow logic that should be extracted to application command/services, leaving scripts as thin CLI wrappers.
7. **Guardrail code exists but is itself procedural and should become reusable rule objects if it grows**: `scripts/verify_guardrails.py` has 25 symbols and many AST checks. It is valuable, but should become an OOP guardrail suite if retained as a core quality gate.
8. **Docstring/public API clarity is low**: the inventory reports 697 symbols inferred as “未写 docstring”. Not every private helper needs a docstring, but public classes, protocols, services, adapters, and engines should document intent and ownership.

This plan is intentionally incremental. It protects behavior with tests before refactoring and uses strict deletion gates before removing files or symbols.

## 2. OOP target model for this quant trading system

A healthy Python OOP design for this system should use classes where they model stable responsibilities and keep pure helpers as cohesive module functions where appropriate. The goal is not “class everything”; the goal is **clear ownership, low coupling, and testable collaborators**.

### 2.1 Class categories

| Category | Purpose | Examples | Rules |
|---|---|---|---|
| Value Object | immutable identity or small data concept | `InstrumentId`, `OrderId`, `TimeInterval`, `Timeframe` | Prefer `dataclass(frozen=True)` or immutable style. No infrastructure dependencies. |
| Domain Entity / Snapshot | core trading state or state snapshot | `Instrument`, `Bar`, `Position`, `ExecutionReport`, `RiskDecision` | Keep in `qts.domain` or core domain modules. No API/broker/persistence leakage. |
| Service / Engine | owns a cohesive use case | `BacktestActorLoop`, `RiskEngine`, `OrderManager` | Small public surface; dependencies injected; no unrelated parsing/serialization. |
| Actor | owns serialized mutable runtime state | `AccountActor`, `OrderManagerActor`, `MarketDataActor` | Communicate by messages; state mutated only by owner. |
| Adapter | translates external provider/broker/data-source formats | `IbkrMarketDataAdapter`, `BrokerAdapter` | Normalize at boundary; never mutate domain/account state directly. |
| Repository / Store | persistence boundary | `EventStore`, `MarketDataStore` | Explicit interfaces/protocols; persistence concerns stay here. |
| DTO / Schema | API/application boundary shape | Application DTOs, Pydantic schemas | API schemas must not leak domain internals or actors. |
| Pure Function Module | deterministic utility group | bar alignment, hashing, validation helpers | Keep cohesive, not one-function-per-file. |

### 2.2 File granularity rule

Do not create one file per helper function. A file should represent one cohesive concept, such as `alignment.py`, `aggregator.py`, `order_state_machine.py`, `config_loader.py`, or `artifact_writer.py`.

Do not collapse unrelated concepts into a single large file. A file/class is a split candidate when it mixes several categories above.

## 3. High-risk areas by inventory evidence

| Area | Evidence from inventory | Risk | Target action |
|---|---|---|---|
| `qts.backtest.engine` | 46 symbols; `BacktestEngine` `121-877`; `_run_actor_loop` has 67 raw calls and 24 internal calls; `_process_intent` and `_process_order_delta` also large | God object, low testability, hard to reason about OOP ownership | Split into collaborator classes while keeping `BacktestEngine` as facade |
| `qts.backtest.config` | 28 symbols; `BacktestRunConfig` has parsing, validation, hashing, payload conversion | Config model mixed with parser/serializer | Extract loader/parser, serializer, stable hash utility |
| `qts.data.historical.config` | 32 symbols; multiple parse helpers | Same as above | Extract `HistoricalDataConfigLoader`, section parsers, and validation services |
| `qts.data.historical.csv_dataset` | 26 symbols; stream iteration and validation helpers | Reader, validator, stream, row conversion mixed | Split reader/stream/validator/row mapper |
| `qts.strategy_sdk.context` | 25 symbols; resolver protocols + context + target + subscription | Facade doing too much | Keep facade; extract internal resolver and target emitter collaborators |
| `qts.execution.order_manager` | 27 symbols; contains order domain classes plus manager | Domain/execution boundary blurred | Move stable order/fill/report value objects to `qts.domain.orders` |
| `scripts/ibkr_*` | many functions and high call counts | CLI scripts own reusable workflows | Extract application command/services; scripts become wrappers |
| `scripts/verify_guardrails.py` | 25 symbols, many AST checks | Valuable but procedural quality system | Convert to rule-object architecture if reused as core guardrail |
| Empty modules | `data/bars/builder.py`, `data/bars/validation.py` have 0 symbols | Placeholder noise or unfinished design | Implement or delete after import/test checks |

## 4. Deletion policy

Deletion is allowed only after these gates pass:

1. `rg` / import graph shows no direct imports.
2. The symbol/file is not a framework route, CLI entrypoint, plugin hook, dynamic callback, public API, or documented extension point.
3. Relevant unit/integration/anchor/regression tests pass before and after deletion.
4. If public API, first deprecate or provide migration unless the symbol is demonstrably unused internal scaffolding.
5. Diff gate confirms no unrelated files changed.

Static “no caller” is a signal, not proof.

## 5. Immediate deletion / consolidation candidates

These are candidates, not automatic deletions.

| Candidate | Current signal | Recommendation | Required verification |
|---|---|---|---|
| `backend/src/qts/data/bars/builder.py` | non-`__init__` file with 0 symbols | Delete if unimported, or implement `BarBuilder` if still part of bar design | `rg "data\.bars\.builder|BarBuilder"`; unit tests; import smoke |
| `backend/src/qts/data/bars/validation.py` | non-`__init__` file with 0 symbols | Delete if unimported, or implement cohesive bar validation module | `rg "data\.bars\.validation|validate_bar"`; anchor tests for bar invariants |
| `scripts/run_api.py`, `scripts/run_paper_ibkr.py`, `scripts/run_worker.py` | 0 symbols in inventory | If intentionally empty entrypoints, implement thin `main()`; otherwise delete | CLI smoke tests or `rg` references |
| `BacktestEngine._stable_hash`, `BacktestRunConfig._stable_hash`, `backtest.report._stable_hash` | duplicate stable hashing concept | Consolidate to `qts.core.hashing.stable_json_hash` | Hash regression tests; reports/config hashes unchanged |
| IBKR config validation in scripts vs `qts.config.ibkr` | scripts contain large validation helpers | Reuse `qts.config.ibkr.validate_ibkr_environment`; remove duplicate script helpers | Script tests and evidence generation tests |
| `BacktestEngine._symbol_for`, `_exchange_for` | parse `InstrumentId.value` strings | Move to `InstrumentRegistry`/metadata access; remove string parsing helpers | Backtest and registry tests |
| Nested `BacktestEngine._StreamingBacktestSink` | sink/artifact responsibility in engine | Move to `qts.backtest.sinks` or report layer | Streaming backtest artifact tests |
| Reconciliation module helper functions | many related pure functions in one module | Prefer `ReconciliationEngine` plus pure comparison helpers | Existing reconciliation behavior tests |

## 6. Refactor roadmap

### Phase OOP-00 — Baseline, safety net, and ownership map

**Goal:** establish a safe refactor baseline and explicit ownership rules.

**Tasks:**

#### OOP-00-T01 — Capture baseline checks

- Scope:
  - run current tests/checks
  - record failing baseline if any
  - no production code changes
- Commands:
  - `make format`
  - `make lint`
  - `make typecheck`
  - `make test-unit`
  - `make test-integration`
  - `make test-anchor`
- Acceptance:
  - baseline result recorded in `docs/review/2026-05-12_oop_baseline.md`
  - known failures are not confused with refactor regressions

#### OOP-00-T02 — Create OOP component map

- Scope:
  - `docs/architecture/oop_component_map.md`
  - classify classes into Value Object / Domain Entity / Service / Actor / Adapter / Store / DTO / Utility
- Acceptance:
  - every top-level package has a responsibility statement
  - large files are classified as split candidates
  - no code changes

#### OOP-00-T03 — Add architecture refactor gates

- Scope:
  - `scripts/verify_guardrails.py` or GoalAgent rule registry
  - architecture gate rules for import boundaries
- Acceptance:
  - domain cannot import runtime/api/broker adapters
  - strategy SDK cannot import runtime/execution adapters/risk engine internals
  - broker adapters cannot import portfolio/account mutation code
  - guardrail tests exist

---

### Phase OOP-01 — Remove or complete placeholder modules

**Goal:** eliminate dead scaffolding without changing behavior.

#### OOP-01-T01 — Resolve empty bar modules

- Scope:
  - `backend/src/qts/data/bars/builder.py`
  - `backend/src/qts/data/bars/validation.py`
- Plan:
  1. Search imports and documentation references.
  2. If unused, delete both files.
  3. If design still requires them, implement cohesive `BarBuilder`/validation functions with tests.
- Acceptance:
  - no import failure
  - bar unit/anchor tests pass
  - no unrelated data module change

#### OOP-01-T02 — Resolve empty script entrypoints

- Scope:
  - `scripts/run_api.py`
  - `scripts/run_paper_ibkr.py`
  - `scripts/run_worker.py`
- Plan:
  - either implement thin `main()` wrappers or delete if not used
- Acceptance:
  - documented CLI entrypoints are executable
  - unused placeholders removed
  - no shell/import errors

---

### Phase OOP-02 — Split `BacktestEngine` god object

**Goal:** make backtest execution object-oriented and collaborator-driven without changing public behavior.

#### OOP-02-T01 — Add characterization tests for current `BacktestEngine`

- Scope:
  - integration tests around `run_streaming`
  - report artifact hash where deterministic
  - order/fill/equity output structure
- Acceptance:
  - tests capture current behavior before refactor
  - tests fail if output shape changes unexpectedly

#### OOP-02-T02 — Extract streaming sink from `BacktestEngine`

- Move:
  - `BacktestEngine._StreamingBacktestSink`
  - related order/fill/ledger serialization calls
- Target:
  - `qts.backtest.sinks.BacktestStreamingSink`
- Keep:
  - `StreamingBacktestArtifactWriter` remains in report layer unless further split needed
- Acceptance:
  - `BacktestEngine` no longer defines `_StreamingBacktestSink`
  - streaming backtest outputs unchanged
  - unit tests for sink exist

#### OOP-02-T03 — Extract actor replay loop

- Move:
  - `_run_actor_loop`
  - `_take_strategy_bar_result`
  - `_take_signal_batch`
  - `_take_strategy_finalized`
  - `_market_data_ref_for`
- Target:
  - `qts.backtest.actor_loop.BacktestActorLoop`
- Acceptance:
  - `BacktestEngine.run_streaming` delegates to `BacktestActorLoop.run`
  - actor loop has explicit dependencies
  - integration test still passes

#### OOP-02-T04 — Extract intent and order delta processing

- Move:
  - `_process_intent`
  - `_process_order_delta`
  - `_desired_quantity`
- Target:
  - `qts.backtest.intent_processor.BacktestIntentProcessor`
- Acceptance:
  - risk/order/fill behavior unchanged
  - processor unit tests cover target percent/quantity/value
  - no direct broker/portfolio mutation bypass

#### OOP-02-T05 — Extract portfolio projection and equity point generation

- Move:
  - `_portfolio_view`
  - `_equity_point`
  - `_multiplier_for`
- Target:
  - `qts.backtest.portfolio_projection.BacktestPortfolioProjector`
- Acceptance:
  - no change to equity curve semantics
  - projector unit tests cover cash/position/multiplier

#### OOP-02-T06 — Extract instrument context and future-roll resolution

- Move:
  - `_instrument_registry_for`
  - `_order_instrument_for_intent`
  - `_market_price_for_intent`
  - `_update_rolling_prices`
  - `_related_contracts_for`
  - `_symbol_for`, `_exchange_for`
- Target:
  - `qts.backtest.instrument_context.BacktestInstrumentContext`
- Acceptance:
  - no string parsing of `InstrumentId.value` remains inside `BacktestEngine`
  - continuous future behavior preserved by tests

#### OOP-02-T07 — Make `BacktestEngine` a facade

- Target public surface:
  - `from_config`
  - `run_streaming`
- Acceptance:
  - `BacktestEngine` delegates to collaborators
  - class length/method count reduced materially
  - all backtest integration tests pass

---

### Phase OOP-03 — Separate config data models from parsing and serialization

**Goal:** config dataclasses should represent validated configuration, not own all parsing/serialization/hashing logic.

#### OOP-03-T01 — Extract stable JSON hashing

- Target:
  - `qts.core.hashing.stable_json_hash`
- Remove duplicates from:
  - `qts.backtest.report._stable_hash`
  - `BacktestRunConfig._stable_hash`
  - `BacktestEngine._stable_hash`
- Acceptance:
  - config/report hash regression tests pass
  - exactly one stable JSON hash implementation remains

#### OOP-03-T02 — Extract `BacktestConfigLoader`

- Move YAML parsing from `BacktestRunConfig.from_yaml` into:
  - `qts.backtest.config_loader.BacktestConfigLoader`
- Keep dataclasses for normalized config.
- Acceptance:
  - existing YAML files parse identically
  - config class no longer owns file I/O
  - backward-compatible factory may remain temporarily with deprecation

#### OOP-03-T03 — Extract historical data config loader

- Move parsing helpers from `qts.data.historical.config.HistoricalDataConfig`
- Target:
  - `qts.data.historical.config_loader.HistoricalDataConfigLoader`
  - optional section parsers
- Acceptance:
  - historical config tests pass
  - data config classes become mostly data/validation objects

---

### Phase OOP-04 — Historical data module responsibility split

**Goal:** make historical data ingestion testable and cohesive.

#### OOP-04-T01 — Split CSV row mapping from stream iteration

- Target:
  - `qts.data.historical.csv_row_mapper`
  - `qts.data.historical.csv_bar_stream`
- Acceptance:
  - row-to-bar mapping independently testable
  - stream iteration tests unchanged

#### OOP-04-T02 — Extract historical sample validator

- Move:
  - `validate_historical_sample`
  - related validation helpers
- Target:
  - `qts.data.historical.validation.HistoricalDatasetValidator`
- Acceptance:
  - validation report unchanged
  - validator can be used by CLI and services

#### OOP-04-T03 — Review catalog/chain responsibilities

- Scope:
  - `catalog.py`
  - `chains.py`
  - `future_roll.py`
- Acceptance:
  - chain resolution and future roll selection have explicit collaborators
  - no duplicated root/symbol normalization logic

---

### Phase OOP-05 — Move order domain objects out of execution manager

**Goal:** align domain/execution boundary with architecture rules.

#### OOP-05-T01 — Create `qts.domain.orders` value objects

- Move or re-export:
  - `OrderIntent`
  - `CancelIntent`
  - `ReplaceIntent`
  - `ExecutionReport`
  - `OrderFill`
  - order/status enums where domain-level
- Acceptance:
  - `OrderManager` imports domain objects
  - public imports remain backward-compatible during transition
  - no circular imports

#### OOP-05-T02 — Keep `OrderManager` as lifecycle service only

- Scope:
  - `qts.execution.order_manager.OrderManager`
- Acceptance:
  - creates/tracks state machines
  - processes normalized reports
  - emits fills/updates
  - does not define stable domain value objects internally

#### OOP-05-T03 — Normalize broker/domain status mapping

- Scope:
  - `qts.execution.broker`
  - `qts.execution.order_manager`
- Acceptance:
  - broker-specific statuses stay in broker boundary
  - normalized statuses live in domain/execution-neutral layer
  - mapping is explicit and tested

---

### Phase OOP-06 — Strategy SDK facade cleanup

**Goal:** keep `StrategyContext` user-friendly while delegating internal responsibilities.

#### OOP-06-T01 — Extract asset resolution collaborator

- Target:
  - `qts.strategy_sdk.asset_resolver.StrategyAssetResolver`
- Move:
  - symbol/future/option resolution details
- Acceptance:
  - `ctx.symbol`, `ctx.future`, `ctx.option` behavior unchanged
  - registry internals remain hidden from user strategies

#### OOP-06-T02 — Extract target intent emitter

- Target:
  - `qts.strategy_sdk.target_emitter.TargetIntentEmitter`
- Move:
  - `_emit`, target methods implementation detail
- Acceptance:
  - target APIs produce intents only
  - no portfolio mutation
  - strategy SDK boundary anchor tests pass

#### OOP-06-T03 — Extract subscription registry

- Target:
  - `qts.strategy_sdk.subscription_registry.StrategySubscriptionRegistry`
- Acceptance:
  - subscriptions remain immutable/read-only to user
  - strategy actor/runtime can consume subscriptions safely

---

### Phase OOP-07 — Runtime actor boundary review

**Goal:** ensure Actor + Queue OOP ownership is explicit.

#### OOP-07-T01 — Actor dependency and state ownership audit

- Scope:
  - `qts.runtime.actors.*`
- Acceptance:
  - AccountActor owns account state
  - OrderManagerActor owns order state
  - MarketDataActor owns aggregation state for its partition
  - no cross-actor business method calls

#### OOP-07-T02 — Extract MarketDataActor aggregation pipeline if needed

- Target:
  - `qts.data.bars.pipeline.BarAggregationPipeline` or runtime-owned wrapper
- Acceptance:
  - data aggregation remains data-layer concept
  - runtime actor owns state instance, not aggregation semantics
  - integration test covers bar event routing

---

### Phase OOP-08 — Reconciliation and live workflow cleanup

**Goal:** make reconciliation and live runtime services explicit, not just bags of functions.

#### OOP-08-T01 — Introduce `ReconciliationEngine`

- Scope:
  - `qts.reconciliation`
- Plan:
  - keep snapshot dataclasses
  - move `reconcile_snapshots` and startup gate into engine/gate classes
  - keep pure comparison helpers private
- Acceptance:
  - reconciliation report unchanged
  - critical drift still fails closed

#### OOP-08-T02 — Live runtime command model cleanup

- Scope:
  - `qts.runtime.live`
  - `qts.application.commands.start_paper`
- Acceptance:
  - runtime state transitions tested
  - live/paper command configs separated from execution adapters

---

### Phase OOP-09 — Scripts become thin wrappers

**Goal:** no reusable business logic should live only in scripts.

#### OOP-09-T01 — Extract IBKR environment evidence service

- Move reusable logic from:
  - `scripts/ibkr_collect_environment_evidence.py`
- Target:
  - `qts.application.commands.ibkr_environment_evidence`
  - or `qts.execution.adapters.ibkr.evidence`
- Acceptance:
  - script only parses args and calls service
  - no live orders placed
  - evidence output unchanged

#### OOP-09-T02 — Extract paper order lifecycle drill service

- Move reusable logic from:
  - `scripts/ibkr_paper_order_lifecycle_drill.py`
- Target:
  - application command/service
- Acceptance:
  - script remains paper-only
  - no live order path enabled
  - drill evidence unchanged

#### OOP-09-T03 — Consolidate script config validation

- Target:
  - reuse `qts.config.ibkr.validate_ibkr_environment`
- Acceptance:
  - duplicate validation helpers removed
  - scripts and services share validation behavior

---

### Phase OOP-10 — DTO/schema boundary cleanup

**Goal:** preserve boundaries without pointless duplication.

#### OOP-10-T01 — Add explicit mapping layer

- Scope:
  - application DTOs
  - API schemas
- Target:
  - `qts.api.mappers`
- Acceptance:
  - API schemas remain Pydantic
  - application DTOs remain stable dataclasses
  - no direct actor/domain internals exposed by API

#### OOP-10-T02 — Identify orphan DTO/schema classes

- Plan:
  - do not delete based on no static caller alone because FastAPI and Pydantic use dynamic discovery
  - verify route/schema imports and OpenAPI generation
- Acceptance:
  - unused schemas removed only after API tests pass
  - public API compatibility documented

---

### Phase OOP-11 — Guardrail engine cleanup

**Goal:** turn guardrails into reusable, testable rule objects if they are core to the project.

#### OOP-11-T01 — Convert `scripts/verify_guardrails.py` to rule suite

- Target:
  - `qts.quality.guardrails.Rule`
  - `qts.quality.guardrails.GuardrailSuite`
  - script becomes wrapper
- Acceptance:
  - existing guardrail outputs unchanged
  - each rule is individually testable
  - no loss of architecture enforcement

#### OOP-11-T02 — Add OOP-specific guardrails

- Rules:
  - max symbols per engine file unless approved
  - no nested service classes in engine facades
  - no one-off factory functions where class ownership is clearer
  - no one-function-per-file utility fragmentation
- Acceptance:
  - guardrails fail on known anti-pattern fixtures
  - guardrails pass current accepted modules after refactor

---

### Phase OOP-12 — Public docs and docstring cleanup

**Goal:** improve readability without bloating private helper docs.

#### OOP-12-T01 — Public API docstrings

- Scope:
  - public classes, protocols, services, adapters, engines
- Acceptance:
  - public classes have one-sentence responsibility docstrings
  - private helpers are documented only when non-obvious

#### OOP-12-T02 — Update architecture docs

- Docs:
  - `docs/architecture/oop_component_map.md`
  - `docs/architecture/dependency_rules.md`
  - ADRs for major extraction decisions
- Acceptance:
  - docs match actual module ownership
  - GoalAgent/guardrail rules reference docs by ID

---

### Phase OOP-13 — Final redundancy deletion pass

**Goal:** remove remaining code proven redundant.

#### OOP-13-T01 — Run dead symbol review

- Inputs:
  - updated code inventory
  - import graph
  - route/CLI/plugin entrypoint list
  - public API list
- Acceptance:
  - candidates classified as delete/deprecate/keep
  - no dynamic entrypoint deleted accidentally

#### OOP-13-T02 — Delete approved redundant files/symbols

- Scope:
  - only approved delete list
- Acceptance:
  - all tests/checks pass
  - import smoke passes
  - release notes mention deleted public symbols if any

## 7. Recommended order

Use this strict order:

```text
OOP-00 Baseline and gates
OOP-01 Placeholder modules
OOP-02 BacktestEngine split
OOP-03 Config loader split
OOP-04 Historical data split
OOP-05 Order domain boundary
OOP-06 Strategy SDK facade cleanup
OOP-07 Runtime actor boundary review
OOP-08 Reconciliation/live workflow cleanup
OOP-09 Script extraction
OOP-10 DTO/schema cleanup
OOP-11 Guardrail engine cleanup
OOP-12 Public docstrings/docs
OOP-13 Final deletion pass
```

Do not start OOP-02 before OOP-00 tests exist. Do not delete public-looking symbols until OOP-13 unless they are placeholder files with verified no references.

## 8. How to run this with GoalAgent

Recommended initial goal:

```bash
make goalagent-goal GOAL="Refactor the quant trading system to align with Python OOP ownership boundaries, reduce god objects, remove verified redundant placeholders, and preserve behavior through tests and architecture gates."
```

Recommended first task:

```bash
make goalagent-next GOALAGENT_NEXT_ARGS="--task OOP-00-T01"
```

Required GoalAgent gates:

- Traceability gate: every refactor task maps to a concrete OOP criterion.
- Architecture gate: import and dependency boundaries must pass.
- Integration gate: cross-module refactors require integration tests.
- Regression gate: bugfix or behavior-preserving refactor requires regression/characterization tests.
- Diff gate: changed files must match task expected files.
- Verification evidence: task cannot finish on “tests probably pass”.

## 9. Review checklist before each refactor task

1. Does the class have one clear responsibility?
2. Does the class own state, coordinate collaborators, or model a domain concept?
3. Is a module function preferable because the logic is pure and cohesive?
4. Is this code in the right layer?
5. Does the refactor preserve public behavior?
6. Are there characterization tests before moving code?
7. Is deletion backed by import/API/entrypoint checks?
8. Is there any broker/product/strategy-specific special case in the wrong layer?
9. Are Strategy SDK and API boundaries still user-safe?
10. Does the final diff reduce complexity rather than just move it?

## 10. Non-goals

- Do not rewrite the whole project.
- Do not convert every function into a class.
- Do not remove API schemas or DTOs merely because they look duplicative; they may enforce boundary separation.
- Do not delete symbols only because static caller analysis misses framework/dynamic usage.
- Do not introduce distributed infrastructure or new dependencies as part of OOP cleanup.
- Do not change trading semantics while refactoring object structure.
