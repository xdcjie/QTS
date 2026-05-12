# QTS OOP Refactor Backlog

This backlog is designed for GoalAgent/Codex execution. Execute one task at a time. Each task must preserve behavior and pass the listed verification gates.

## Global gates for every task

```bash
make format
make lint
make guardrails
make typecheck
make test-unit
```

Add when relevant:

```bash
make test-integration
make test-anchor
```

Never delete a symbol only because the static inventory says “no internal callers.” First check imports, package exports, routes, CLI entrypoints, framework registration, Protocol methods, dependency injection, docs, examples, and tests.

---

## OOP-00 — Baseline and safety gates

### OOP-00-T01 — Establish current baseline

Goal: record the current passing/failing status before refactor work.

Scope:
- Run the required checks.
- Record baseline failures separately from new refactor failures.

Expected files:
- `docs/plan/2026-05-12_oop_refactor_execution_log.md`

Acceptance:
- Baseline commands and results are recorded.
- Existing failures are not confused with refactor regressions.
- No production code changed.

Verification:
```bash
make format
make lint
make guardrails
make typecheck
make test-unit
```

### OOP-00-T02 — Generate dependency and export map for deletion safety

Goal: produce a deletion safety map before removing wrappers or zero-symbol files.

Scope:
- Identify imports and docs references for deletion candidates.
- Include dynamic and CLI entrypoints in the check.

Expected files:
- `docs/plan/2026-05-12_oop_deletion_safety_map.md`

Acceptance:
- Every deletion candidate has reference status: imported / CLI / docs / tests / package export / no reference.
- No file is deleted in this task.

Verification:
```bash
make guardrails
make test-unit
```

---

## OOP-01 — Remove or normalize redundant wrappers

### OOP-01-T01 — Resolve empty IBKR evidence scripts

Goal: remove ambiguity for `scripts/ibkr_collect_environment_evidence.py` and `scripts/ibkr_paper_order_lifecycle_drill.py`, which appear as zero-symbol scripts while reusable command modules exist under `qts.application.commands`.

Scope:
- If scripts are documented CLI entrypoints, implement a narrow `main()` delegating to the corresponding `qts.application.commands.*` command.
- If they are not documented or referenced, delete them.
- Do not duplicate application command logic in scripts.

Expected files:
- `scripts/ibkr_collect_environment_evidence.py`
- `scripts/ibkr_paper_order_lifecycle_drill.py`
- possibly docs or examples referencing these scripts

Acceptance:
- Each script is either deleted or becomes a thin CLI wrapper.
- No business logic lives in script wrappers.
- Existing evidence/drill commands remain available through one canonical path.

Verification:
```bash
make guardrails
make test-unit
```

### OOP-01-T02 — Verify guardrails script is only a thin wrapper

Goal: ensure `scripts/verify_guardrails.py` delegates to `qts.quality.guardrails.main` and does not duplicate rule implementations.

Scope:
- Inspect script implementation.
- If duplicate rule logic exists, delete it and delegate to `qts.quality.guardrails.main`.
- If already thin, document that no change is required.

Expected files:
- `scripts/verify_guardrails.py`
- `tests/unit/scripts/test_verify_guardrails.py`

Acceptance:
- Exactly one implementation owner for guardrail rules: `qts.quality.guardrails`.
- Script wrapper contains no duplicate `GuardrailViolation`, `Rule`, or `_check_*` logic.
- `make guardrails` still works.

Verification:
```bash
make guardrails
make test-unit
```

---

## OOP-02 — Backtest construction and engine cleanup

### OOP-02-T01 — Introduce `BacktestEngineConfig`

Goal: reduce `BacktestEngine.__init__` primitive-heavy parameter list.

Scope:
- Create a focused config value object containing run-level immutable inputs: `initial_cash`, `warmup_bars`, `target_timeframe`, `strategy_version`, optional config payload, cost model configuration, and other stable construction inputs.
- Keep strategy and bars as runtime inputs if that is clearer, but group repeated primitive parameters.

Expected files:
- `backend/src/qts/backtest/config.py`
- `backend/src/qts/backtest/engine.py`
- tests for config validation

Acceptance:
- `BacktestEngine` constructor takes fewer primitive parameters.
- Config object owns validation/normalization.
- Backward-compatible constructor or `from_config` is preserved if existing callers require it.
- No runtime behavior changes.

Verification:
```bash
make guardrails
make typecheck
make test-unit
make test-integration
```

### OOP-02-T02 — Introduce `BacktestEngineDependencies`

Goal: separate runtime dependencies from immutable config.

Scope:
- Group dependencies such as `risk_engine`, `instrument_registry`, `future_roll_registry`, contract multipliers, and timezone mappings into a dependency/context object.
- Ensure default construction is explicit and testable.

Expected files:
- `backend/src/qts/backtest/engine.py`
- possibly `backend/src/qts/backtest/dependencies.py`

Acceptance:
- `BacktestEngine` no longer constructs unrelated dependencies through scattered conditionals.
- Defaults are owned by dependency construction and tested.
- Existing `BacktestEngine.from_config` remains a named constructor delegating to the new path.

Verification:
```bash
make guardrails
make typecheck
make test-unit
make test-integration
```

### OOP-02-T03 — Move `_BacktestExecutionAdapter` out of `engine.py`

Goal: put execution adapter behavior at the correct boundary.

Scope:
- Move `_BacktestExecutionAdapter` to `qts.execution.simulator.backtest_execution_adapter` if it represents simulated execution semantics.
- Alternatively move to `qts.backtest.execution_adapter` if it is strictly backtest-local.
- `BacktestEngine` should receive or create the adapter through a dependency object, not define it inline.

Expected files:
- `backend/src/qts/backtest/engine.py`
- `backend/src/qts/execution/simulator/backtest_execution_adapter.py` or `backend/src/qts/backtest/execution_adapter.py`
- tests for execution report normalization / fill cost behavior

Acceptance:
- `engine.py` no longer defines execution adapter classes.
- Adapter has a concise public class docstring.
- Behavior remains unchanged.
- Order/execution integration tests still pass.

Verification:
```bash
make guardrails
make typecheck
make test-unit
make test-integration
```

### OOP-02-T04 — Move dataset payload and zero-time helpers to owning concepts

Goal: remove report/artifact formatting helpers from `BacktestEngine`.

Scope:
- Move `_dataset_payload` to a dataset metadata serializer or report artifact writer.
- Move `_zero_time` to a clock/report utility if it is not engine-specific.

Expected files:
- `backend/src/qts/backtest/engine.py`
- `backend/src/qts/backtest/report.py`
- possibly `backend/src/qts/data/provenance.py`

Acceptance:
- `BacktestEngine` is an orchestrator facade, not an artifact serializer.
- Artifact payload format remains identical.
- Existing report tests pass or characterization tests are added.

Verification:
```bash
make guardrails
make test-unit
make test-integration
```

### OOP-02-T05 — Add `BacktestActorLoopConfig` and dependency object

Goal: reduce `BacktestActorLoop.__init__` long parameter list.

Scope:
- Group static loop settings in `BacktestActorLoopConfig`.
- Group collaborators/callbacks in `BacktestActorLoopDependencies` or `BacktestActorLoopContext`.

Expected files:
- `backend/src/qts/backtest/actor_loop.py`
- tests for actor loop construction and a minimal run

Acceptance:
- `BacktestActorLoop` constructor is readable and has concept-owned inputs.
- No behavior changes to actor message flow.
- Integration test covering strategy -> intent -> order -> fill still passes.

Verification:
```bash
make guardrails
make typecheck
make test-unit
make test-integration
```

---

## OOP-03 — Strategy SDK facade cleanup

### OOP-03-T01 — Change user-facing `StrategyContext.option` API away from raw `InstrumentId`

Goal: keep the Strategy SDK user-facing and hide internal instrument complexity.

Scope:
- Add an overload or replacement accepting `AssetRef` or user symbol for the underlying.
- Internally resolve to `InstrumentId` through `StrategyAssetResolver`.
- Keep backward-compatible API only if required, and mark it as internal/advanced if retained.

Expected files:
- `backend/src/qts/strategy_sdk/context.py`
- `backend/src/qts/strategy_sdk/asset_resolver.py`
- strategy SDK tests and examples

Acceptance:
- Normal strategy authors can select options without directly passing `InstrumentId`.
- Existing examples remain simple.
- No actor, broker, risk engine, order manager, or contract spec internals leak into Strategy SDK.

Verification:
```bash
make guardrails
make typecheck
make test-unit
make test-integration
```

### OOP-03-T02 — Add concise public docstrings to Strategy SDK facade

Goal: make public user-facing API semantics explicit.

Scope:
- Add short docstrings to `StrategyContext`, `symbol`, `future`, `option`, `target_percent`, `target_quantity`, `target_value`, `rebalance`, and subscription APIs.
- Do not add verbose private method docstrings.

Expected files:
- `backend/src/qts/strategy_sdk/context.py`
- possibly `docs/strategy_sdk/strategy_api.md`

Acceptance:
- Inventory no longer needs to infer public Strategy SDK intent as “Perform x.”
- Documentation remains concise.

Verification:
```bash
make lint
make typecheck
make test-unit
```

---

## OOP-04 — API schema/route boundary cleanup

### OOP-04-T01 — Move operations route schemas to `qts.api.schemas.operations`

Goal: keep route modules thin and move DTO/schema ownership to schemas.

Scope:
- Move `RuntimeCommandResponse`, `KillSwitchScopeSchema`, `KillSwitchCommand`, `KillSwitchResponse` from `qts.api.routes.operations` to `qts.api.schemas.operations`.
- Update route imports.

Expected files:
- `backend/src/qts/api/routes/operations.py`
- `backend/src/qts/api/schemas/operations.py`
- API tests

Acceptance:
- Route module contains route handlers and thin dependency wiring only.
- Schema classes live under `qts.api.schemas`.
- API response behavior unchanged.

Verification:
```bash
make guardrails
make typecheck
make test-unit
make test-integration
```

---

## OOP-05 — Reconciliation package split

### OOP-05-T01 — Split reconciliation value objects and engine

Goal: turn `qts.reconciliation` from a dense module into a package with cohesive owners.

Scope:
- Move snapshots to `qts.reconciliation.snapshots`.
- Move drift kinds/items to `qts.reconciliation.drift`.
- Move report object to `qts.reconciliation.report`.
- Move engine to `qts.reconciliation.engine`.
- Move startup decision/gate to `qts.reconciliation.startup_gate`.
- Preserve `qts.reconciliation` imports via compatibility re-exports if external callers use them.

Expected files:
- `backend/src/qts/reconciliation.py` or package replacement
- new `backend/src/qts/reconciliation/*.py`
- reconciliation tests

Acceptance:
- Public imports remain compatible or migration is documented.
- Reconciliation behavior unchanged.
- Startup fail-closed behavior remains test-covered.

Verification:
```bash
make guardrails
make typecheck
make test-unit
make test-integration
```

---

## OOP-06 — Live feed package split

### OOP-06-T01 — Split live feed protocol, DTOs, policy, and fake adapter

Goal: reduce density in `qts.data.live_feed` while preserving the live feed boundary.

Scope:
- Move `FeedCapabilities` to `qts.data.live.capabilities`.
- Move `FeedSubscription`, `LiveFeedSubscribed`, `LiveFeedEvent`, `LiveFeedFailure` to `qts.data.live.events` or `subscriptions`.
- Move `ReconnectPolicy` to `qts.data.live.reconnect`.
- Move `LiveFeedAdapter` Protocol to `qts.data.live.adapter`.
- Move `FakeLiveFeedAdapter` to `qts.data.live.fake_adapter` or `qts.data.live.testing` depending on production use.
- Provide re-exports if required.

Expected files:
- `backend/src/qts/data/live_feed.py`
- new `backend/src/qts/data/live/*.py`
- live feed tests and market data actor tests

Acceptance:
- Live feed behavior unchanged.
- MarketDataActor still receives the same events.
- Fake adapter remains clearly separated from production adapter protocols.

Verification:
```bash
make guardrails
make typecheck
make test-unit
make test-integration
```

---

## OOP-07 — Execution broker boundary review

### OOP-07-T01 — Decide whether `qts.execution.broker` should remain one module

Goal: avoid premature splitting while documenting the boundary.

Scope:
- Inspect whether `BrokerCapabilities`, order requests, execution reports, adapter protocol, and fake adapter are still one cohesive execution boundary.
- If cohesive, add docstrings and keep module.
- If too dense, split into `capabilities.py`, `requests.py`, `reports.py`, `adapter.py`, `fake_adapter.py` with compatibility exports.

Expected files:
- `backend/src/qts/execution/broker.py`
- possibly new execution broker submodules

Acceptance:
- Decision is documented.
- Public imports remain compatible.
- No broker behavior leaks into portfolio/accounting.

Verification:
```bash
make guardrails
make typecheck
make test-unit
make test-integration
```

---

## OOP-08 — Public docstrings and naming cleanup

### OOP-08-T01 — Add docstrings to public stable concepts

Goal: reduce inferred “Perform x” descriptions and make public APIs self-explanatory.

Scope:
- Add concise docstrings to public classes/methods in high-touch modules only.
- Do not add noise to private helpers.

Priority modules:
- `qts.backtest.engine`
- `qts.backtest.actor_loop`
- `qts.strategy_sdk.context`
- `qts.execution.order_manager`
- `qts.data.live_feed` or new live package
- `qts.reconciliation` or new reconciliation package

Acceptance:
- Public API intent is clear.
- No behavior change.

Verification:
```bash
make lint
make typecheck
make test-unit
```

### OOP-08-T02 — Normalize API naming to avoid command/schema ambiguity

Goal: avoid names like `KillSwitchCommand` being confused with application commands when it is an API schema.

Scope:
- Rename API schema classes with `Schema` or place in `schemas` module where context makes it clear.
- Preserve backwards compatibility where required.

Expected files:
- `backend/src/qts/api/schemas/operations.py`
- `backend/src/qts/api/routes/operations.py`

Acceptance:
- API schema names are unambiguous.
- Application command names remain separate.

Verification:
```bash
make typecheck
make test-unit
make test-integration
```

---

## OOP-09 — Strengthen guardrails for the next cycle

### OOP-09-T01 — Add guardrail for Strategy SDK internal leakage

Goal: automatically catch user-facing API leaks.

Scope:
- Add rule rejecting `qts.runtime`, `qts.execution.adapters`, `qts.risk.risk_engine`, `BrokerActor`, `OrderManagerActor`, `ContractSpec`, and `BrokerSymbolMapping` in Strategy SDK public modules unless explicitly allowed.

Expected files:
- `backend/src/qts/quality/guardrails.py`
- `tests/unit/quality/test_guardrails.py` or existing guardrail tests

Acceptance:
- Violating fixture fails guardrail test.
- Valid Strategy SDK modules pass.

Verification:
```bash
make guardrails
make test-unit
```

### OOP-09-T02 — Add guardrail for empty non-entrypoint source files

Goal: prevent ambiguous empty files outside package markers.

Scope:
- Flag non-`__init__.py` files with zero classes/functions unless listed as allowed framework entrypoint or generated placeholder.

Expected files:
- `backend/src/qts/quality/guardrails.py`
- guardrail tests

Acceptance:
- Empty non-entrypoint scripts are caught.
- Empty `__init__.py` package markers are allowed.

Verification:
```bash
make guardrails
make test-unit
```

---

## OOP-10 — Final deletion pass

### OOP-10-T01 — Delete verified redundant files/symbols

Goal: remove code only after safety map, compatibility decision, and tests.

Scope:
- Delete only files/symbols that have no imports, docs references, package exports, CLI use, dynamic entrypoint use, tests, or public compatibility requirement.
- For public compatibility wrappers, keep them until a deprecation decision is documented.

Expected files:
- only verified redundant candidates
- `docs/plan/2026-05-12_oop_deletion_report.md`

Acceptance:
- Deletion report lists each removed item and proof.
- Full check passes.
- No public entrypoint is removed accidentally.

Verification:
```bash
make check
```
