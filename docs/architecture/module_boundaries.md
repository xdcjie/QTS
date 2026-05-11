# Module Boundaries

This document defines ownership boundaries for `backend/src/qts`. When a concept
could be used by both backtest and live, place it in a shared boundary rather
than in a mode-specific or source-specific package.

## Boundary Rule

Ask this before creating or moving a module:

```text
Who owns the domain rule?
Which modes need it: backtest, paper, live?
Is this source-specific, adapter-specific, mode-specific, or shared runtime/domain behavior?
```

If both backtest and live need the rule, it must not live in `qts.backtest` or
`qts.data.historical`. Those packages may call shared services, but they do not
own shared financial semantics.

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

When a new module boundary is introduced, update this document and the guardrail
tests in the same change.
