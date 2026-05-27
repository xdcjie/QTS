# Module Boundaries

This document defines ownership boundaries for `backend/src/qts`. When a concept
could be used by both backtest and live, place it in a shared boundary rather
than in a mode-specific or source-specific package.

## Boundary Rule

Ask this before creating or moving a module:

```text
What is the unit's single reason to change?
Who owns the domain rule?
Which modes need it: backtest, paper, live?
Is this source-specific, adapter-specific, mode-specific, or shared runtime/domain behavior?
Does the module only orchestrate other owners, or does it own reusable behavior?
```

Also choose the applicable Flow ID from `docs/architecture/system_flows.md` and
state the canonical entrypoint, config owner, allowed implementation owner,
iteration point, future-data risk, and verification gate before editing
non-trivial behavior. Module placement is not sufficient if the change enters
through the wrong flow.

If both backtest and live need the rule, it must not live in `qts.backtest` or
`qts.data.historical`. Those packages may call shared services, but they do not
own shared financial semantics.

High cohesion means a module groups responsibilities that change for the same
reason and can be described as one stable concept. Low coupling means callers
depend on that concept's narrow public API, not on its file layout, private
helpers, source format details, or unrelated runtime wiring.

Keep these responsibilities separate unless a documented module boundary owns
the combined concept:

- configuration parsing and validation;
- source/data loading and file-format parsing;
- domain invariants and financial rules;
- registry, symbol, and roll/session resolution;
- runtime or use-case orchestration;
- artifact/report serialization.

Runners, CLIs, workers, and application services are orchestration boundaries.
They may connect cohesive components, but they must not accumulate reusable data
construction, domain resolution, source parsing, registry construction, or
artifact format logic as private helpers.

For backtests, configured historical bar streams, dataset metadata, instrument
registry construction, and roll-aware replay input assembly belong in cohesive
data/backtest input boundaries. The runner should invoke those boundaries and
then call the engine.

For research and optimizer work, `qts.research` and `qts.research.optimizer`
own evidence, workflow gates, parameter grids, validation constraints,
walk-forward splits, failure-window vetoes, and research reports. They may call
`BacktestPipeline` through public session/runner APIs, but they must not own
runtime, broker, risk, order, execution, account, registry, session, or market
data semantics. Research outputs become paper/live behavior only through the
promotion flow.

Research workflow runs must use:

```bash
PYTHONPATH=backend/src uv run python scripts/run_research.py \
  --config <research-config> \
  workflow <workflow-config>
```

Deprecated VWAP ad hoc runners under `scripts/research/run_vwap_*.py` and
VWAP-specific optimizer configs under `configs/optimizer` are forbidden
shortcuts. They are not compatibility boundaries and must not remain or be
reintroduced. Deleted VWAP workflow files are not valid workflow dependencies.

Do not use backtest package placement to describe the source's time model.
`historical` versus `realtime` is a market data source property;
`backtest`/`paper`/`live` is an execution-mode property. A source-agnostic
strategy data view or market data portal belongs in a shared Strategy SDK or
runtime-facing boundary, not in `qts.backtest` solely because backtests replay
historical bars.

## Repository OOP Standard

This project uses object-oriented ownership for stable system concepts. Choose
the shape that keeps a concept closed over its own rules and keeps callers
coupled to a narrow public API.

Use a class when a concept has state, configuration, lifecycle, invariants,
validation/normalization, or a coherent public interface. Its construction path
belongs with the concept: constructors and classmethod constructors should
parse, validate, normalize, and assemble the object without requiring callers to
know its internals.

For stable concepts, prefer a construction-config pattern:

```python
catalog_config = HistoricalCatalogLoadConfig(
    source=source,
    roots=roots,
    symbol_resolvers=symbol_resolvers,
    requested_timeframe=requested_timeframe,
)
catalog = HistoricalCatalog.load(catalog_config)
```

The `<Concept>Config` value object owns the complete construction input shape.
The `<Concept>` object owns validation, normalization, internal branching, and
invariant checks. Callers should pass one cohesive config object instead of long
primitive parameter lists, and they should not reproduce the concept's assembly
decisions outside the concept owner.

Do not add new module-level public factory functions such as `load_<concept>`,
`build_<concept>`, `create_<concept>`, or `make_<concept>` for stable concepts.
Use class-owned constructors such as `Concept.load(config)` or
`Concept.from_yaml(...)`.

Use module-level functions only for stateless algorithms, pure transformations,
framework entrypoints, protocol callbacks, and explicit compatibility wrappers.
Compatibility wrappers must be narrow, delegate immediately to the owning object
API, avoid new behavior, and stay out of package `__all__` unless backward
compatibility explicitly requires export.

In class-centric modules, private helpers that only serve the public class must
live on that class as private instance, class, or static methods. Keep
module-private helpers only when they are shared algorithm steps, pure
transformations, function-oriented framework entrypoints, or stable module
concepts rather than one class's construction, validation, mapping,
serialization, or state transition logic.

Do not move object construction decisions into runners, CLIs, workers, or
unrelated builders. For example, a historical catalog boundary should close over
historical catalog configuration, path resolution, dataset validation, and
`HistoricalCatalog` construction. A backtest input builder should consume the
catalog object; it should not decide how to construct the catalog.

Automated guardrails block new public module-level factory functions and
class-centric module-private helpers except for documented compatibility or
framework exceptions. New exceptions must update this document, the guardrail
script, and the guardrail tests in the same change.

## Top-Level Modules

| Path | Owns | Must Not Own |
| --- | --- | --- |
| `qts.core` | Stable IDs, time primitives, base value helpers. | Domain, broker, runtime, API, or persistence behavior. |
| `qts.domain` | Pure trading domain objects and invariants. | Broker protocols, actors, storage, API schemas, source file formats. |
| `qts.registry` | Instrument metadata, symbol mappings, calendar providers, futures chain and roll resolution shared by modes. | Historical CSV parsing, broker transport, strategy execution. |
| `qts.data` | Market data ingestion contracts, source adapters, sessions, bar generation, storage access. | Order execution, risk decisions, portfolio mutation. |
| `qts.portfolio` | Portfolio/accounting calculations and position/cash books. | Actor ownership or broker callbacks. |
| `qts.risk` | Pre-trade risk rules and risk decisions. | Broker transport, market data ingestion, strategy APIs. |
| `qts.execution` | Order lifecycle, broker-order abstractions, execution adapters. | Market data subscriptions, bar aggregation, portfolio mutation. |
| `qts.runtime` | Actor/message orchestration, routing, clocks, event store, runtime lifecycle. | Financial domain rules that should be tested outside actors. |
| `qts.strategy_sdk` | User-facing strategy API and read-only views. | Actor internals, broker adapters, risk engine, order manager internals. |
| `qts.backtest` | Backtest mode composition, replay clock use, historical simulation orchestration, report generation. | Shared roll/session/instrument semantics or backtest-only business paths that live/paper also need. |
| `qts.application` | Use-case orchestration for API/CLI/workers. | Domain invariants or adapter protocol behavior. |
| `qts.api` | Public HTTP/WebSocket schemas and routes. | Actor internals or direct domain state mutation. |
| `qts.workers` | Process entrypoints and dependency wiring. | Business logic. |

## Data Subpackages

| Path | Owns | Must Not Own |
| --- | --- | --- |
| `qts.data.historical` | Historical source configuration, catalog resolution, CSV schema/parsing, historical source replay service. | Futures roll resolution, exchange session rules, live/backtest-shared market semantics. |
| `qts.data.sessions` | Session window definitions, session filtering, exchange-time session membership helpers. | Product-specific hardcoded behavior outside provider/config data. |
| `qts.data.bars` | Timeframe model, bucket alignment, bar aggregation and validation. | Source-specific file parsing or order execution. |
| `qts.data.adapters` | Market data provider adapters such as IBKR market data normalization. | Order submission, order reconciliation, account mutation. |
| `qts.data.feeds` | Feed abstractions and replay/live source contracts. | Strategy decisions or portfolio mutation. |
| `qts.data.stores` | Market data persistence access. | Domain rules or broker behavior. |

## Shared Versus Source-Specific Examples

| Concept | Correct Boundary | Incorrect Boundary |
| --- | --- | --- |
| GC `[ET 18:00, ET 17:00)` product session provider | `qts.registry.providers` or `qts.data.sessions` through configuration/provider data | `qts.backtest`, `qts.data.historical` shared helper |
| Generic session window membership | `qts.data.sessions` | `qts.backtest`, `qts.data.historical` |
| Continuous future roll selection and contract resolution | `qts.registry.future_roll` | `qts.backtest`, `qts.data.historical` |
| Historical CSV timestamp parsing | `qts.data.historical` | `qts.registry`, `qts.runtime` |
| IBKR market data normalization | `qts.data.adapters` | `qts.execution`, `qts.domain` |
| IBKR order request mapping | `qts.execution.adapters` | `qts.data.adapters`, `qts.domain` |
| Backtest replay orchestration | `qts.backtest` | `qts.registry`, `qts.domain` |

## Guardrails

`make guardrails` enforces the highest-risk parts of this document. It cannot
prove every design decision, but it should block obvious placement mistakes:

- shared roll/session/resolution modules under `qts.backtest` or
  `qts.data.historical`;
- test or anchor helpers under `backend/src/qts`;
- product-specific implementation in shared core packages;
- broker-specific implementation outside config/adapters;
- forbidden imports across core, domain, strategy SDK, API, and adapter
  boundaries.
- production classes over 300 lines must be present in
  `docs/plan/backend_class_boundary_review_status_matrix.md`;
- production classes over 500 lines must have a split/retain decision and
  evidence in that matrix.

When a new module boundary is introduced, update this document and the guardrail
tests in the same change.
