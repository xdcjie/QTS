# Quant Trading System Project Instructions

This repository is a Python-first quantitative trading system supporting multi-strategy, multi-account trading; stock/future/option instruments; backtest, paper, and live modes; API/frontend extensibility; and a Strategy SDK that hides internal trading complexity.

The global `~/.codex/AGENTS.md` still applies. This file adds project-specific architecture, domain, OOP, and verification rules.

## 1. Source of truth and spec gates

Before implementing or modifying core behavior, read the relevant durable docs under `docs/`, especially:

- `docs/architecture/system_overview.md`
- `docs/architecture/dependency_rules.md`
- `docs/architecture/module_boundaries.md`
- `docs/architecture/backtest_live_parity.md`
- `docs/runtime/actor_model.md`
- `docs/domain/instrument_model.md`
- `docs/domain/market_calendar_and_sessions.md`
- `docs/domain/bar_timeframe_model.md`
- `docs/strategy_sdk/strategy_api.md`
- `docs/testing/testing_strategy.md`
- `docs/testing/domain_invariants.md`

If implementation conflicts with docs, stop and propose either a design update or a code change. Do not create parallel scratch specs for durable rules.

Important specs must become gates. For every durable boundary, invariant, or architecture rule touched by a task, identify at least one enforcement mechanism: `make guardrails`, unit/integration/anchor/regression tests, static checks, review checklist, or manual approval. Passing behavior tests alone is not enough if a boundary gate applies.

## 1.1 Plan-execution closure gate

For any task that asks to execute, complete, review against, or fix findings from
a plan/spec/status matrix/work package document, the plan is the acceptance
contract. Scale the process to the size of the plan, but do not replace the
plan's target outcome with a partial implementation detail.

Before editing, extract the relevant plan items into a short checklist:

```text
Plan item:
Target behavior:
Canonical entrypoint:
Correct owner or boundary:
Required evidence:
Status: pending
```

Rules:

- Account for each relevant requirement, acceptance criterion, and required
  evidence item, or explicitly mark it out of scope with a reason.
- "Implemented" means the behavior is reachable through the plan's intended
  entrypoint, owner, artifact, or user-facing path. Sidecar modules, private
  helpers, fixtures, and one-off scripts do not count unless the plan asks only
  for that layer.
- Turn durable requirements into gates: tests, guardrails, artifact/hash checks,
  snapshots, anchor tests, or documented manual review gates.
- Subagent output is advisory. Inspect the diff, verify behavior, run relevant
  checks, and compare the result back to the plan before marking work complete.
- Do not claim completion while generated-artifact residue, deleted-config
  dependencies, stale references, or unverified acceptance gates remain.

Before final response on plan work, re-open the plan and verify the checklist
against fresh evidence. If a required item cannot be backed by evidence, say it
is incomplete and keep working unless blocked. For milestone-level completion,
run `make check` unless impossible and explain skipped checks.

## 1.2 Flow-first implementation gate

For every non-trivial implementation, choose the applicable Flow ID from
`docs/architecture/system_flows.md` before editing code or configs. If multiple
flows are touched, state one gate per flow:

```text
Flow ID:
Canonical entry:
Config owner:
Allowed owner:
Iteration point:
Future-data risk:
Required verification:
```

The answer must be concrete, not generic. `Allowed owner` must name the package,
module, config owner, or documentation owner that is allowed to change.
`Future-data risk` must state whether the change can expose data, labels,
optimizer windows, replay bars, broker/account events, or reports before they
are actually available.

The change should not proceed if the requested implementation would enter
through a non-canonical entrypoint, use the wrong config owner, or iterate at a
point forbidden by `system_flows.md`.

Research workflow runs must enter through:

```bash
PYTHONPATH=backend/src uv run python scripts/run_research.py \
  --config <research-config> \
  workflow <workflow-config>
```

Legacy VWAP ad hoc runners under `scripts/research/run_vwap_*.py` and
VWAP-specific optimizer configs under `configs/optimizer` are not allowed to
remain or be reintroduced. Do not depend on deleted VWAP workflow files; create
or review an existing workflow YAML under `configs/research/workflows/` before
running workflow research.

For domain-sensitive changes, state this before editing code:

```text
Domain fact / invariant:
Correct owner or abstraction boundary:
Forbidden shortcut:
Required gates / verification:
```

If the correct boundary is unclear, stop and clarify.

## 2. Ownership, cohesion, and OOP

Use object-oriented ownership for stable system concepts. Functions are allowed, but stable concept construction, validation, normalization, lifecycle, state, and cohesive behavior should be owned by the concept.

Rules:

- Every new or changed module/class/function must have one clear reason to change.
- Keep configuration parsing, data loading, source parsing, domain rules, registry/resolution, runtime orchestration, and artifact/report writing in separate owners unless one cohesive concept explicitly owns them.
- Runners, CLIs, workers, and application services may orchestrate; they must not own reusable data construction, source parsing, domain resolution, roll/session semantics, registry construction, or artifact formats.
- Stable concepts should prefer `<Concept>Config` plus `<Concept>` construction. The concept owns validation, normalization, internal branching, and invariant checks.
- Do not add public module-level factories such as `load_<concept>`, `build_<concept>`, `create_<concept>`, or `make_<concept>` for stable concepts. Use the owning class/config, named constructors, or narrow compatibility wrappers.
- Compatibility wrappers must delegate immediately, add no new behavior, and should not be exported unless required for backward compatibility.
- Use a class when the concept has state, configuration, lifecycle, dependencies, invariants, or a coherent public API. Use module functions for pure stateless algorithms, framework/CLI entrypoints, protocol callbacks, or thin convenience APIs.
- Private helpers that only serve one class in a class-centric module belong on that class. Module-private helpers are acceptable only for shared algorithm steps, pure transformations, framework entrypoints, or module-owned concepts.
- Large god objects are not acceptable just because tests pass. Split by ownership after characterization tests are in place.

Backtest runners may wire a run together, but configured historical bar streams, dataset metadata, instrument registry construction, and roll-aware replay input assembly must live in cohesive data/backtest input boundaries, not private runner helpers.

New exceptions to ownership/OOP rules require updating `docs/architecture/module_boundaries.md`, `scripts/verify_guardrails.py`, and `tests/unit/scripts/test_verify_guardrails.py` in the same change.

## 3. File and module granularity

Organize code by cohesive concept, not by one function per file and not by forcing every helper into a class.

- A file should represent a stable concept, component, adapter, model, policy, algorithm, command, or framework entrypoint.
- Do not create a new file for every small helper.
- Group tightly related helpers in the same module.
- Keep files readable but not fragmented.
- Prefer concept names such as `timeframe.py`, `alignment.py`, `aggregator.py`, `validation.py`, `order_state_machine.py`.
- A single-function file is acceptable for a standalone command, route/handler, adapter entrypoint, algorithm, or public API.
- A streaming class and a batch helper may coexist when they serve different workflows, e.g. `BarAggregator` and `aggregate_bars(...)`.

Before finalizing changed Python files, inspect new private helpers:

```bash
rg -n "^def _|^class _" <changed-python-files>
```

Decide whether each belongs on an owning class, remains a module-private shared algorithm, or should become an explicit public API. Tests should prefer public behavior and owning boundaries, not private helpers.

## 4. Quant domain boundaries

- Instrument-specific behavior belongs in `InstrumentRegistry`, `ContractSpec`, calendar/session definitions, or product-specific risk/valuation models.
- Broker-specific behavior belongs in broker adapters and config.
- Strategy-specific behavior belongs in user strategy code, not runtime, portfolio, risk, or execution core.
- Timeframe/session-specific behavior belongs in `qts.data.bars`, `qts.data.sessions`, and registry/calendar services.
- Financial correctness rules must be reusable domain rules protected by unit, integration, anchor, or regression tests.
- Product facts such as `GC`, `SI`, trading hours, roll behavior, margin, or valuation overrides must not appear in shared implementation as product-named functions/constants or `if root == ...` branches.
- Broker facts such as IBKR host/port/client IDs, symbols, capabilities, and protocol behavior must not leak outside config or adapter boundaries.

## 5. Architecture and runtime rules

- Use Actor + Queue orchestration.
- Actor-to-actor coordination uses message passing, not direct business method calls.
- Actor-owned state is mutated only by the owning actor.
- Account state belongs to `AccountActor`.
- Order state belongs to `OrderManagerActor`.
- Broker callbacks become normalized internal events before affecting system state.
- Market data and order execution are separate adapters, actor boundaries, config sections, and event streams, even when both use IBKR.
- Risk checks are never bypassed.
- User strategies must not directly access Broker, RiskEngine, OrderManager, AccountActor, ContractSpec, or BrokerSymbolMapping.

## 6. Backtest, paper, and live parity

Backtest, paper, and live are execution modes of the same system. They must share the same core domain and runtime path unless a documented adapter boundary requires different behavior.

Required shared path:

```text
Strategy SDK -> StrategyContext -> AssetRef/TargetIntent -> Instrument/Symbol/Roll resolution -> RiskEngine -> OrderManagerActor -> ExecutionActor -> AccountActor -> Portfolio/account state -> reporting/observability
```

Allowed differences are boundary adapters only:

- market data source: historical/replay, paper feed, live adapter
- execution adapter: simulated fill, paper broker, live broker
- clock/source timing: replay, paper, live
- environment: credentials, connectivity, persistence, latency model, external capabilities

Rules:

- Do not create a backtest-only business path that bypasses RiskEngine, OrderManagerActor, ExecutionActor, or AccountActor.
- Do not create a live-only business path for behavior that should be testable in backtest.
- Symbol, instrument, and continuous-future roll resolution must use shared registry abstractions where possible.
- Broker/data-source symbols stay at adapter boundaries and resolve to `InstrumentId` before core runtime logic.
- Continuous futures are research/data references and must resolve to concrete tradable contracts before order creation in both backtest and live.
- Strategy code must not branch on execution mode except through documented Strategy SDK capabilities.
- Intentional divergence must be documented in `docs/architecture/backtest_live_parity.md` and covered by tests.

## 7. Instrument, calendar, and market data rules

- Use `InstrumentId` internally; never use broker/data-source symbols as internal identifiers.
- Use `InstrumentRegistry` for symbol resolution and contract metadata.
- Use `BrokerSymbolMapping` only at broker/data-source boundaries.
- Support stock, future, and option through unified Instrument abstractions.
- Market sessions are domain facts; timezones are representations.
- All bar intervals use `[start, end)` semantics.
- `<1d` bars are clock-aligned in exchange timezone.
- `1d` bars are session-aligned and must not be treated as 24h bars.
- Domain-critical calendar/library behavior must be wrapped behind internal interfaces and protected by anchor tests.

Approved default components:

- `exchange-calendars` for exchange sessions where supported, wrapped behind `qts.registry` / `qts.data.sessions`.
- `pandas` for research-facing tabular/time-series and batch calculations; domain models must not require pandas.
- `pydantic` for API schemas, external config, and boundary validation; not as core domain entities unless justified.
- `fastapi` for backend HTTP/WebSocket APIs when API implementation begins.
- `ruff`, `mypy`, `pytest` for formatting, typing, and tests.

Do not add production dependencies without explaining why existing or approved components are insufficient.

## 8. Strategy SDK rules

User-facing strategies should use only:

- `Strategy`
- `StrategyContext`
- `AssetRef`
- `DataView`
- `PortfolioView`
- `IndicatorFactory` / `FactorFactory`
- target APIs such as `ctx.target_percent`, `ctx.target_quantity`, `ctx.target_value`, `ctx.rebalance`, and `ctx.close`

Direct order APIs are advanced APIs and must still emit intents that pass through Risk and OrderManager. Strategy SDK APIs must not expose actors, broker internals, ContractSpec, BrokerSymbolMapping, or internal event routing.

## 9. Documentation governance

Before adding or moving docs, read `docs/README.md` and use existing documentation boundaries.

- Architecture, runtime, domain, strategy SDK, testing, operations, API, infrastructure, and plan material belong in their existing `docs/` areas.
- Do not add agent/tool/workflow-specific directories under `docs/`.
- Temporary plans, scratch specs, and tool execution notes should not be committed under `docs/` unless rewritten as project-level durable documentation.
- When changing a durable rule, update the authoritative long-lived document instead of creating a parallel spec.

## 10. Verification

Run the narrowest relevant checks first, then broader checks when shared behavior changes.

Required for normal code tasks:

```bash
make format
make lint
make guardrails
make typecheck
make test-unit
```

Also run `make test-integration` for module interaction, actor flow, order flow, portfolio flow, broker simulation, IBKR adapter behavior, API behavior, or runtime orchestration.

Also run `make test-anchor` for calendars, sessions, bar generation, instrument identity, portfolio accounting, order state machines, risk semantics, or financial domain correctness.

Before milestone-level completion, run:

```bash
make check
```

If checks cannot be run, explain why and do not claim full verification.

Deletion/refactor safety:

- Do not delete code solely because a static search finds no caller. Check graph/impact when available, dynamic entrypoints, routes, scripts, protocols, package exports, tests, and docs.
- Characterize existing behavior before splitting large classes or moving responsibilities.
- Remove verified redundant placeholders only after import/reference checks and relevant tests pass.

## MCP Tools: codegraph

This project uses the `codegraph` MCP knowledge graph for code exploration,
impact analysis, and architecture questions. Prefer it before raw text search
when looking up symbols, callers, callees, flows, or ownership boundaries.

### When to use codegraph first

- **Task/area context**: `codegraph_context`
- **Symbol lookup**: `codegraph_search`
- **Several related source snippets**: `codegraph_explore`
- **One symbol body or signature**: `codegraph_node`
- **Flow/path tracing**: `codegraph_trace`
- **Blast radius**: `codegraph_impact`
- **Index health**: `codegraph_status`

Fall back to `rg` or file reads when `codegraph` does not cover the needed
detail. The `codegraph` index refreshes automatically through its watcher.
