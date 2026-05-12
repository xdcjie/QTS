# 2026-05-12 — Fine-Grained OOP Refactor Backlog

This backlog turns the OOP architecture review into small tasks suitable for GoalAgent/Codex execution. Each task is intentionally scoped to one behavior or ownership boundary.

## OOP-00 — Baseline and gates

### OOP-00-T01 — Capture baseline test and guardrail status

- Goal: record current project health before refactoring.
- Scope: no production code changes.
- Expected files:
  - `docs/review/2026-05-12_oop_baseline.md`
- Tests/checks:
  - `make format`
  - `make lint`
  - `make typecheck`
  - `make test-unit`
  - `make test-integration`
  - `make test-anchor`
- Acceptance:
  - baseline exists
  - known failures documented
  - no code changed

### OOP-00-T02 — Create OOP component map

- Goal: document class ownership and refactor targets.
- Expected files:
  - `docs/architecture/oop_component_map.md`
- Acceptance:
  - top-level packages classified
  - high-risk classes listed
  - no production code changed

### OOP-00-T03 — Add OOP architecture gate rules

- Goal: prevent future spec/architecture drift.
- Expected files:
  - `scripts/verify_guardrails.py` or `.goalagent/rules/oop_rules.json`
  - `tests/unit/quality/test_oop_guardrails.py`
- Acceptance:
  - domain/import boundary violations are detected
  - strategy SDK internal exposure is detected
  - broker adapter → portfolio mutation import is detected

## OOP-01 — Placeholder modules

### OOP-01-T01 — Remove or implement `data/bars/builder.py`

- Goal: eliminate empty placeholder.
- Expected files:
  - `backend/src/qts/data/bars/builder.py` or deletion
  - tests if implemented
- Acceptance:
  - file is either deleted or contains cohesive `BarBuilder`
  - no import failures
  - bar tests pass

### OOP-01-T02 — Remove or implement `data/bars/validation.py`

- Goal: eliminate empty placeholder.
- Expected files:
  - `backend/src/qts/data/bars/validation.py` or deletion
  - tests if implemented
- Acceptance:
  - file is either deleted or contains cohesive validation functions
  - anchor tests for bar invariants pass

### OOP-01-T03 — Resolve empty script entrypoints

- Goal: implement or remove empty CLI scripts.
- Expected files:
  - `scripts/run_api.py`
  - `scripts/run_paper_ibkr.py`
  - `scripts/run_worker.py`
- Acceptance:
  - documented scripts have `main()` and CLI smoke test
  - undocumented empty scripts removed

## OOP-02 — BacktestEngine split

### OOP-02-T01 — Add characterization tests for streaming backtest output

- Goal: lock current behavior before refactor.
- Expected files:
  - `tests/integration/backtest/test_backtest_engine_characterization.py`
- Acceptance:
  - captures processed bars, fills, equity output structure
  - fails if behavior changes unexpectedly

### OOP-02-T02 — Extract `BacktestStreamingSink`

- Goal: move sink responsibility out of engine.
- Expected files:
  - `backend/src/qts/backtest/sinks.py`
  - `backend/src/qts/backtest/engine.py`
  - `tests/unit/backtest/test_backtest_streaming_sink.py`
- Acceptance:
  - nested `_StreamingBacktestSink` removed
  - streaming output unchanged

### OOP-02-T03 — Extract `BacktestActorLoop`

- Goal: move actor loop orchestration out of engine.
- Expected files:
  - `backend/src/qts/backtest/actor_loop.py`
  - `backend/src/qts/backtest/engine.py`
  - `tests/unit/backtest/test_backtest_actor_loop.py`
- Acceptance:
  - `_run_actor_loop` removed from engine
  - actor loop object has explicit dependencies
  - integration test passes

### OOP-02-T04 — Extract `BacktestIntentProcessor`

- Goal: separate target/order processing from engine orchestration.
- Expected files:
  - `backend/src/qts/backtest/intent_processor.py`
  - `backend/src/qts/backtest/engine.py`
  - `tests/unit/backtest/test_backtest_intent_processor.py`
- Acceptance:
  - `_process_intent`, `_process_order_delta`, `_desired_quantity` moved
  - risk/order flow unchanged

### OOP-02-T05 — Extract `BacktestPortfolioProjector`

- Goal: isolate PortfolioView/equity calculations.
- Expected files:
  - `backend/src/qts/backtest/portfolio_projection.py`
  - tests
- Acceptance:
  - `_portfolio_view`, `_equity_point`, multiplier lookup moved
  - equity curve unchanged

### OOP-02-T06 — Extract `BacktestInstrumentContext`

- Goal: remove instrument registry/future-roll handling from engine.
- Expected files:
  - `backend/src/qts/backtest/instrument_context.py`
  - tests
- Acceptance:
  - `_symbol_for` and `_exchange_for` removed from engine
  - no string parsing of `InstrumentId.value` in engine

### OOP-02-T07 — Make `BacktestEngine` facade-only

- Goal: leave `BacktestEngine` as public coordinator.
- Acceptance:
  - public API stable
  - method count materially reduced
  - all backtest tests pass

## OOP-03 — Config responsibilities

### OOP-03-T01 — Consolidate stable hashing

- Goal: one stable JSON hash utility.
- Expected files:
  - `backend/src/qts/core/hashing.py`
  - affected config/report/engine files
  - tests
- Acceptance:
  - duplicate `_stable_hash` helpers removed
  - hash outputs unchanged

### OOP-03-T02 — Extract `BacktestConfigLoader`

- Goal: move YAML parsing out of config dataclasses.
- Expected files:
  - `backend/src/qts/backtest/config_loader.py`
  - tests
- Acceptance:
  - YAML parsing behavior unchanged
  - dataclasses no longer own file I/O

### OOP-03-T03 — Extract `HistoricalDataConfigLoader`

- Goal: move historical config parsing out of data config classes.
- Expected files:
  - `backend/src/qts/data/historical/config_loader.py`
  - tests
- Acceptance:
  - historical config behavior unchanged
  - parser helpers no longer crowd data model classes

## OOP-04 — Historical data responsibility split

### OOP-04-T01 — Extract CSV row mapper

- Goal: make row-to-bar conversion testable.
- Expected files:
  - `backend/src/qts/data/historical/csv_row_mapper.py`
  - tests
- Acceptance:
  - row mapper tests cover required fields and timezones

### OOP-04-T02 — Extract historical dataset validator

- Goal: move sample validation into validator object/service.
- Expected files:
  - `backend/src/qts/data/historical/validation.py`
  - tests
- Acceptance:
  - validation report unchanged

## OOP-05 — Order domain boundary

### OOP-05-T01 — Move stable order value objects to domain

- Goal: align domain/execution boundary.
- Expected files:
  - `backend/src/qts/domain/orders/*.py`
  - `backend/src/qts/execution/order_manager.py`
  - tests
- Acceptance:
  - order/fill/report value objects available from domain
  - order manager imports them
  - compatibility imports maintained temporarily if needed

### OOP-05-T02 — Keep OrderManager focused on lifecycle

- Goal: reduce manager to state transitions and report processing.
- Acceptance:
  - no stable domain class definitions remain in order manager
  - order lifecycle tests pass

## OOP-06 — Strategy SDK facade cleanup

### OOP-06-T01 — Extract asset resolver

- Goal: delegate symbol/future/option resolution.
- Expected files:
  - `backend/src/qts/strategy_sdk/asset_resolver.py`
  - tests
- Acceptance:
  - `StrategyContext` public API unchanged

### OOP-06-T02 — Extract target intent emitter

- Goal: delegate target intent creation and storage.
- Expected files:
  - `backend/src/qts/strategy_sdk/target_emitter.py`
  - tests
- Acceptance:
  - target APIs produce intents only
  - no portfolio mutation

### OOP-06-T03 — Extract subscription registry

- Goal: delegate subscription collection.
- Expected files:
  - `backend/src/qts/strategy_sdk/subscriptions.py`
  - tests
- Acceptance:
  - subscription API behavior unchanged

## OOP-07 — Runtime actors

### OOP-07-T01 — Actor ownership audit

- Goal: prove actor state ownership.
- Expected files:
  - `docs/review/2026-05-12_actor_ownership_audit.md`
  - tests/guardrails if needed
- Acceptance:
  - no direct cross-actor business method call found
  - account/order state ownership documented

### OOP-07-T02 — Extract market data aggregation pipeline if needed

- Goal: keep aggregation semantics in data layer, actor state in runtime.
- Acceptance:
  - MarketDataActor owns aggregator instance state
  - data layer owns aggregation semantics

## OOP-08 — Reconciliation and live workflow

### OOP-08-T01 — Introduce ReconciliationEngine

- Goal: cohesive reconciliation service.
- Expected files:
  - `backend/src/qts/reconciliation.py` or `backend/src/qts/reconciliation/engine.py`
  - tests
- Acceptance:
  - report output unchanged
  - startup gate behavior unchanged

## OOP-09 — Scripts to application services

### OOP-09-T01 — Extract IBKR environment evidence command

- Goal: make evidence collection reusable.
- Expected files:
  - `backend/src/qts/application/commands/ibkr_environment_evidence.py`
  - `scripts/ibkr_collect_environment_evidence.py`
  - tests
- Acceptance:
  - script is thin wrapper
  - evidence output unchanged

### OOP-09-T02 — Extract IBKR paper order lifecycle drill command

- Goal: make paper drill reusable and safe.
- Acceptance:
  - script remains paper-only
  - no live order path enabled

## OOP-10 — API DTO/schema boundary

### OOP-10-T01 — Add API mapper layer

- Goal: explicit schema ↔ DTO mapping.
- Expected files:
  - `backend/src/qts/api/mappers.py`
  - tests
- Acceptance:
  - API schemas do not leak actor internals
  - application DTOs remain stable

### OOP-10-T02 — Delete verified orphan schemas/DTOs only

- Goal: remove real duplicates safely.
- Acceptance:
  - OpenAPI/routes tests pass
  - no dynamic route schema removed incorrectly

## OOP-11 — Guardrail engine

### OOP-11-T01 — Convert guardrail checks into rule objects

- Goal: make architecture checks extensible and testable.
- Expected files:
  - `backend/src/qts/quality/guardrails.py` or `scripts/verify_guardrails.py`
  - tests
- Acceptance:
  - current guardrail behavior preserved
  - each rule independently testable

## OOP-12 — Documentation and docstrings

### OOP-12-T01 — Add public API docstrings

- Goal: clarify public responsibilities.
- Acceptance:
  - public classes/protocols/services/adapters have concise docstrings
  - no boilerplate docstrings for obvious private helpers

## OOP-13 — Final deletion pass

### OOP-13-T01 — Generate updated code inventory and delete approved redundancies

- Goal: delete only proven redundant code.
- Acceptance:
  - updated inventory exists
  - approved deletion list exists
  - all checks pass after deletion
