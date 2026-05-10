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

## Required design documents

Before implementing or modifying core behavior, read the relevant documents under `docs/`, especially:

- `docs/architecture/system_overview.md`
- `docs/architecture/dependency_rules.md`
- `docs/runtime/actor_model.md`
- `docs/domain/instrument_model.md`
- `docs/domain/market_calendar_and_sessions.md`
- `docs/domain/bar_timeframe_model.md`
- `docs/strategy_sdk/strategy_api.md`
- `docs/testing/testing_strategy.md`
- `docs/testing/domain_invariants.md`

If implementation conflicts with these documents, stop and propose a design update first.

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

Organize code by cohesive concepts, not by one function per file.

Rules:

- Do not create a new file for every small helper function.
- A file should represent a stable concept, component, adapter, model, policy, or algorithm.
- Group tightly related helper functions in the same module.
- Keep files small enough to understand, but not so small that navigation becomes fragmented.
- Prefer names like `timeframe.py`, `alignment.py`, `aggregator.py`, `validation.py`, and `order_state_machine.py` over names like `get_x.py`, `calculate_y.py`, or `handle_z.py`.
- A single-function file is acceptable only when that function is a standalone command, adapter entrypoint, algorithm, or clearly reusable public API.
- Do not create artificial abstractions just to avoid putting related functions in the same file.

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

1. The graph auto-updates on file changes (via hooks).
2. Use `detect_changes` for code review.
3. Use `get_affected_flows` to understand impact.
4. Use `query_graph` pattern="tests_for" to check coverage.
