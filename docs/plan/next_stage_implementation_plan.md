# Next Stage Implementation Plan

## Purpose

This document defines the next stage after the initial fine-grained backlog is complete.

The assumed current state is:

- Project skeleton exists.
- Core/domain models exist.
- Timeframe, session, bar aggregation, and anchor tests exist.
- Strategy SDK MVP exists.
- Portfolio, risk, execution, runtime, and backtest MVPs exist.
- `make check` can run with unit, integration, and anchor tests.

The next stage moves the system from a working MVP to a reliable research, backtest, paper-trading, and live-readiness platform.

## Stage Goal

Build a **paper/live-ready alpha system** with:

- reliable data persistence and replay,
- stable event storage and recovery,
- production-grade order lifecycle handling,
- robust risk configuration,
- strategy lifecycle management,
- API surfaces for frontend and automation,
- observability and audit trails,
- deployment-ready local environment,
- stronger validation through integration and anchor tests.

## Guiding Principles

1. Preserve financial correctness invariants before optimizing throughput.
2. Keep domain models independent from infrastructure.
3. Keep user strategy API simple and stable.
4. Route all trading actions through Risk and OrderManager.
5. Do not expose actor internals through API or frontend.
6. Prefer mature libraries, but wrap domain-critical behavior behind internal interfaces.
7. Every milestone must have executable verification.

## Next Stage Roadmap

| Stage | Name | Outcome |
|---|---|---|
| S2-00 | Baseline audit | Confirm the current project is ready for next-stage work |
| S2-01 | Data persistence and replay | Store, retrieve, validate, and replay market data deterministically |
| S2-02 | Event store and recovery | Persist critical events and restore runtime state |
| S2-03 | Strategy lifecycle | Register, configure, start, stop, and inspect strategy instances |
| S2-04 | Order lifecycle hardening | Handle duplicate, delayed, and out-of-order broker reports safely |
| S2-05 | Risk configuration | Make risk rules configurable and testable per account/strategy/product |
| S2-06 | Paper trading runtime | Run strategies against live/replayed data with simulated broker execution |
| S2-07 | API layer MVP | Expose accounts, strategies, orders, risk, data, and backtest endpoints |
| S2-08 | WebSocket streams | Stream market data, strategy status, orders, fills, risk, and logs |
| S2-09 | Frontend console MVP | Provide basic operational UI over the API |
| S2-10 | Observability and audit | Add structured logs, metrics, trace IDs, and audit trail |
| S2-11 | Deployment baseline | Provide local Docker Compose and config profiles |
| S2-12 | Production readiness review | Validate boundaries, invariants, recovery, and operational workflow |

## Recommended Execution Model

Run only one fine-grained task at a time.

For each task:

1. Read root `AGENTS.md` and relevant module `AGENTS.md` files.
2. Read the relevant design documents.
3. Implement the smallest coherent change.
4. Add or update tests.
5. Run required checks.
6. Update documentation if public behavior changes.

Default verification:

```bash
make format
make lint
make typecheck
make test-unit
```

When runtime or cross-module behavior changes:

```bash
make test-integration
```

When financial correctness, calendar/session semantics, bar aggregation, portfolio accounting, order state machines, or risk semantics change:

```bash
make test-anchor
```

Milestone-level verification:

```bash
make check
```

## Non-goals for This Stage

These are intentionally deferred unless explicitly pulled forward:

- Real-money broker integration.
- Complex multi-node distributed deployment.
- Full portfolio margin for complex option books.
- Advanced frontend analytics dashboards.
- Strategy marketplace or multi-tenant SaaS features.
- High-frequency microstructure execution engine.

## Exit Criteria

This stage is complete when:

- A strategy can be registered and configured.
- A backtest can be run through the API or CLI.
- A paper-trading runtime can consume replay/live-like data and simulated fills.
- Critical events are persisted and replay/recovery paths are tested.
- Order lifecycle handles realistic duplicate/out-of-order broker reports.
- Risk rules are configurable and cannot be bypassed.
- Frontend can inspect strategies, accounts, orders, risk status, and system health.
- `make check` passes.
