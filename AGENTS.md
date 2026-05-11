# Quant Trading System Project Instructions

This repository implements a Python-first quantitative trading system.

The system must support:

- Multi-strategy execution
- Multi-account portfolio management
- Actor + Queue orchestration
- Stock, future, and option instruments
- Backtest, paper trading, and live trading modes
- Frontend and API extensibility
- A user-facing Strategy SDK that hides internal trading complexity
- Unit, integration, and anchor verification

## Quant system abstraction rules

- Instrument-specific behavior belongs in `InstrumentRegistry`, `ContractSpec`, calendar/session definitions, or product-specific risk/valuation models.
- Broker-specific behavior belongs in broker adapters.
- Strategy-specific behavior belongs in user strategy code, not in runtime, portfolio, risk, or execution core.
- Timeframe/session-specific behavior belongs in `qts/data/bars` and calendar/session services.
- Financial correctness rules must be expressed as reusable domain rules and protected by tests.

## Domain-sensitive implementation gate

Before changing sessions, bar generation, instrument identity, broker/data
adapters, strategy SDK boundaries, risk, order flow, portfolio/accounting, or
backtest/live parity, state this gate before editing code:

```text
Domain fact:
Correct abstraction boundary:
Forbidden shortcut:
Verification:
```

If the correct abstraction boundary is unclear, stop and clarify the design
before implementation.

Rules:

- Product-specific facts such as `GC`, `SI`, trading hours, roll behavior, margin,
  or valuation overrides must not enter shared implementation as product-named
  functions, constants, or `if root == "..."` branches. Put them in registry,
  contract spec, calendar/session provider, configuration/data, or documented
  product-specific risk/valuation boundaries.
- Broker-specific facts such as IBKR host/port/client IDs, broker symbols, order
  capabilities, and protocol behavior must stay in config or adapter boundaries.
- Passing behavioral tests does not prove the abstraction boundary is correct.
  Run `make guardrails` and inspect any intentional exception before claiming
  the change is ready.

## Required design documents

Before implementing or modifying core behavior, read the relevant documents under `docs/`, especially:

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

If implementation conflicts with these documents, stop and propose a design update first.

Before creating a new module, check `docs/architecture/module_boundaries.md`.
Allowed import direction is not enough; the module must live in the package that
owns the concept. Shared roll/session/resolution behavior used by both backtest
and live must not be placed under `qts.backtest` or `qts.data.historical`.

## Documentation governance

Before adding or moving project documentation, read `docs/README.md` and use
the existing documentation directory boundaries.

Rules:

- Do not add a new top-level `docs/` directory unless the content represents a
  stable project concept, does not fit an existing directory, is expected to
  hold more than one document over time, and is documented in `docs/README.md`.
- Do not add agent/tool/workflow-specific directories under `docs/`.
- Architecture, runtime, domain, strategy SDK, testing, operations, API,
  infrastructure, and plan material must live in the corresponding existing
  `docs/` directory.
- Temporary agent plans, scratch specs, and tool-specific execution notes must
  not be committed under `docs/` unless they are rewritten as project-level
  long-lived documentation.
- When changing a durable rule, update the authoritative long-lived document
  instead of creating a parallel spec.

## Architecture rules

- Use Actor + Queue as the orchestration model.
- Actor-to-actor communication must use message passing, not direct business method calls.
- Actor-owned state must only be mutated by the owning actor.
- Account state must be owned and mutated only by `AccountActor`.
- Order state must be owned and mutated only by `OrderManagerActor`.
- Broker callbacks must become normalized internal events before affecting system state.
- Paper and live trading must use IBKR adapter boundaries unless a later design document explicitly changes the broker target.
- Market data and order execution must be separated into different adapters, actor boundaries, configuration sections, and event streams, even when both use IBKR.
- Risk checks must never be bypassed.
- User strategies must not directly access Broker, RiskEngine, OrderManager, AccountActor, ContractSpec, or BrokerSymbolMapping.

## Backtest and live parity rules

Backtest, paper, and live are execution modes of the same trading system. They
must share the same core domain and runtime path unless a documented adapter
boundary requires different behavior.

Required shared path:

Strategy SDK -> StrategyContext -> AssetRef/TargetIntent -> Instrument/Symbol/Roll
resolution -> RiskEngine -> OrderManagerActor -> ExecutionActor -> AccountActor
-> Portfolio/account state -> reporting/observability.

Allowed differences are limited to boundary adapters:

- Market data source: historical CSV/replay, paper feed, live market data adapter.
- Execution adapter: simulated/backtest fill adapter, paper broker adapter, live broker adapter.
- Clock/source timing: replay clock, paper clock, live runtime clock.
- Environment concerns: credentials, broker connectivity, persistence, latency model,
  and external broker capabilities.

Rules:

- Do not create a backtest-only business path that bypasses RiskEngine,
  OrderManagerActor, ExecutionActor, or AccountActor.
- Do not create a live-only business path for behavior that should be testable in
  backtest.
- Symbol, instrument, and continuous-future roll resolution must use shared
  registry-level abstractions where possible.
- Broker/data-source symbols must stay at adapter boundaries and resolve to
  InstrumentId before entering core runtime logic.
- Continuous futures are research/data references and must resolve to concrete
  tradable contracts before order creation in both backtest and live.
- Strategy code must not branch on execution mode except through documented
  Strategy SDK capabilities.
- If a feature touches one mode, the implementation must either reuse the shared
  path for all modes or document why it is adapter-specific.
- Any intentional divergence between backtest and live must be documented in
  `docs/architecture/backtest_live_parity.md` and covered by a test.


## Instrument and market data rules

- Use `InstrumentId` internally.
- Do not use broker symbols as internal identifiers.
- Use `InstrumentRegistry` for symbol resolution and contract metadata.
- Use `BrokerSymbolMapping` only at broker/data-source boundaries.
- IBKR market data adapters may resolve broker/data-source symbols only at the adapter boundary.
- IBKR order execution adapters may translate internal orders to broker order requests only at the adapter boundary.
- Support stock, future, and option through unified Instrument abstractions.
- Market sessions are domain facts; timezones are representations.
- All bar intervals use `[start, end)` semantics.
- `<1d` bars are clock-aligned in exchange timezone.
- `1d` bars are session-aligned and must not be treated as 24h bars.

## Approved components and dependency policy

Prefer mature, maintained, domain-standard Python packages for common infrastructure.

Approved default components:

- `exchange-calendars`
  - Use for exchange sessions, holidays, opens/closes, and trading calendar queries where supported.
  - Wrap behind `qts.registry` / `qts.data.sessions` interfaces.
  - Do not expose `exchange_calendars` objects directly through domain models or Strategy SDK.
  - Validate important exchange/session behavior with anchor tests.
- `pandas`
  - Use for research-facing tabular/time-series data and batch calculations.
  - Do not require domain models to depend on pandas objects.
- `pydantic`
  - Use for API schemas, external configuration, and validation at system boundaries.
  - Do not use Pydantic models as core domain entities unless explicitly justified.
- `fastapi`
  - Use for backend HTTP/WebSocket APIs when API implementation begins.
- `ruff`, `mypy`, `pytest`
  - Use for formatting, linting, static type checking, and tests.

Dependency rules:

- Prefer standard or approved components over custom implementations.
- Wrap domain-critical third-party behavior behind internal interfaces.
- Add or update anchor tests when adopting a library for financial correctness.
- Do not leak third-party API types into core domain models unless approved.
- Do not add new production dependencies without explaining why existing dependencies are insufficient.

## Strategy SDK rules

User-facing strategies should use:

- `Strategy`
- `StrategyContext`
- `AssetRef`
- `DataView`
- `PortfolioView`
- `IndicatorFactory`
- `FactorFactory`
- target APIs

Prefer:

- `ctx.target_percent(...)`
- `ctx.target_quantity(...)`
- `ctx.target_value(...)`
- `ctx.rebalance(...)`
- `ctx.close(...)`

Direct order APIs are advanced APIs and must still produce intents that pass through Risk and OrderManager.

## Verification

Run the narrowest relevant checks first, then full checks when shared behavior changes.

Required for normal code tasks:

```bash
make format
make lint
make guardrails
make typecheck
make test-unit
```

For changes that affect module interaction, actor flow, order flow, portfolio flow, broker simulation, IBKR adapter behavior, API behavior, or runtime orchestration, also run:

```bash
make test-integration
```

For changes that affect market calendars, sessions, bar generation, instrument identity, portfolio accounting, order state machines, risk semantics, or financial domain correctness, also run:

```bash
make test-anchor
```

Before milestone-level completion, run:

```bash
make check
```

If a check cannot be run, explain why and do not claim full verification.


## File and module granularity

Organize code by cohesive concepts, not by one function per file and not by forcing every helper into a class.

Rules:

- A file should represent a stable concept, component, adapter, model, policy, algorithm, command, or framework entrypoint.
- Do not create a new file for every small helper function.
- Group tightly related helper functions in the same module when they belong to the same concept.
- Keep files small enough to understand, but not so small that navigation becomes fragmented.
- Prefer names like `timeframe.py`, `alignment.py`, `aggregator.py`, `validation.py`, and `order_state_machine.py` over names like `get_x.py`, `calculate_y.py`, or `handle_z.py`.
- A single-function file is acceptable only when the function is a standalone command, adapter entrypoint, algorithm, framework route/handler entrypoint, or clearly reusable public API.
- Do not create artificial abstractions just to avoid putting related functions in the same file.
- Do not introduce a class just to wrap a stateless function. Prefer a class only when the object owns state, configuration, strategy, lifecycle, dependencies, or a coherent public interface.
- In class-centric modules, private helpers that only serve one class should live on that class as private instance, class, or static methods.
- Do not leave a module-level private helper next to a class when the helper only implements that class's validation, normalization, mapping, serialization, or state transition logic.
- Keep module-level functions when they are public convenience APIs, function-oriented framework entrypoints, shared algorithm steps, or pure transformations that are not owned by one class.
- For paired APIs, it is acceptable to expose both a stateful class and a stateless convenience function when they serve different workflows. For example, a streaming `BarAggregator` can coexist with an
`aggregate_bars(...)` batch helper.

### Private helper ownership review

Before finalizing code changes, inspect changed Python files for newly added
module-private helpers:

```bash
rg -n "^def _|^class _" <changed-python-files>
```

For each new private helper, explicitly decide its owner:

- If it only serves one class in a class-centric module, move it onto that class
  as a private instance, class, or static method.
- If it is a shared algorithm step, pure transformation, function-oriented
  framework entrypoint, or stable module concept, keep it module-private.
- If it is meant to be used by other modules, make it an explicit public API
  instead of relying on a leading underscore.

Do not rely on nearby legacy style to override this ownership check.

Tests must not depend on module-private helpers as stable integration points.
When testing architecture or flow, prefer public behavior, public classes, or the
owning class boundary. If a test must inspect source for an architectural anchor,
inspect the owning public class or module-level public API instead of importing
or referencing private helper functions directly.

<!-- code-review-graph MCP tools -->
## MCP Tools: code-review-graph

**IMPORTANT: This project has a knowledge graph. ALWAYS use the
code-review-graph MCP tools BEFORE using Grep/Glob/Read to explore
the codebase.** The graph is faster, cheaper (fewer tokens), and gives
you structural context (callers, dependents, test coverage) that file
scanning cannot.

### When to use graph tools FIRST

- **Exploring code**: `semantic_search_nodes` or `query_graph` instead of Grep
- **Understanding impact**: `get_impact_radius` instead of manually tracing imports
- **Code review**: `detect_changes` + `get_review_context` instead of reading entire files
- **Finding relationships**: `query_graph` with callers_of/callees_of/imports_of/tests_for
- **Architecture questions**: `get_architecture_overview` + `list_communities`

Fall back to Grep/Glob/Read **only** when the graph doesn't cover what you need.

### Key Tools

| Tool | Use when |
|------|----------|
| `detect_changes` | Reviewing code changes — gives risk-scored analysis |
| `get_review_context` | Need source snippets for review — token-efficient |
| `get_impact_radius` | Understanding blast radius of a change |
| `get_affected_flows` | Finding which execution paths are impacted |
| `query_graph` | Tracing callers, callees, imports, tests, dependencies |
| `semantic_search_nodes` | Finding functions/classes by name or keyword |
| `get_architecture_overview` | Understanding high-level codebase structure |
| `refactor_tool` | Planning renames, finding dead code |

### Workflow

1. Treat graph refresh as a hard tool-use hook: after any successful file
   modification (`apply_patch`, refactor tools, formatters, generated outputs,
   or test fixture rewrites), immediately call
   `build_or_update_graph_tool(repo_root=<repo>, full_rebuild=False,
   postprocess="minimal")` before further code exploration, impact analysis, or
   final review.
2. If a batch operation modifies many files, refresh once after the batch
   completes. Use `full_rebuild=True` only after broad file moves/deletes,
   parser-impacting changes, or when incremental update reports errors.
3. Do not expose graph refresh as a user-facing Make target or checklist item;
   it is an internal maintenance hook that keeps subsequent graph queries
   trustworthy.
4. Use `detect_changes` for code review.
5. Use `get_affected_flows` to understand impact.
6. Use `query_graph` pattern="tests_for" to check coverage.
