# 2026-05-10 S4-00 Production-Ready Implementation Plan

## Context

This stage starts after S3 live beta work is complete.

S3 should already have produced:

- Broker adapter contracts
- Live market data adapters
- Reconciliation baseline
- Live runtime orchestration
- Risk controls and kill switches
- Multi-account partitioning
- Event-store recovery baseline
- API/WebSocket hardening
- Operational console
- Observability and deployment baseline

S4 turns the system into a production-ready alpha capable of realistic historical backtesting and controlled live trading.

## Final S4 objective

By the end of S4, the system must support:

1. **Real backtesting**
   - Historical data ingestion
   - Dataset provenance
   - Exchange calendar correctness
   - Bar aggregation correctness
   - Strategy SDK parity with paper/live
   - Reproducible reports

2. **Real live trading**
   - Broker lifecycle management
   - Submit/cancel/replace order workflows
   - Normalized execution reports
   - Broker reconciliation
   - Restart-safe recovery
   - Risk controls and kill switches
   - Operator-visible audit trail

3. **First-principles correctness**
   - Domain invariants are documented.
   - Anchor tests protect financial semantics.
   - Integration tests prove workflow correctness.
   - Replay tests prove determinism.
   - Reconciliation tests prove internal/external consistency.
   - Soak tests prove operational stability.

## First-principles method

Every S4 task must answer before coding:

1. What is the domain truth?
2. What invariant must never be broken?
3. What implementation representation is allowed?
4. What tests prove the invariant?
5. What operational evidence proves it is safe?

Example:

- Domain truth: COMEX Gold session is `[ET 18:00, ET 17:00)`.
- Representation: timestamps may be stored in UTC.
- Invariant: a normal full 1-minute session has `23 * 60 = 1380` bars, excluding holidays and special sessions.
- Acceptance: an implementation returning `1440`, `1379`, or timezone-dependent counts is incorrect.

## Milestone map

```text
S4-00 Baseline freeze and readiness audit
S4-01 Historical data correctness and provenance
S4-02 Calendar, session, and bar correctness hardening
S4-03 Real backtest engine validation
S4-04 Strategy SDK parity and research/live equivalence
S4-05 Portfolio accounting and PnL correctness
S4-06 Risk correctness and fail-closed controls
S4-07 Broker/live execution correctness
S4-08 Reconciliation and recovery correctness
S4-09 Live runtime operational safety
S4-10 API/frontend operator workflows
S4-11 Observability, audit, and incident response
S4-12 Performance, load, and soak testing
S4-13 Deployment, secrets, and production environments
S4-14 Controlled live rollout
S4-15 Final production readiness review
```

## Verification model

Required existing checks:

```bash
make format
make lint
make typecheck
make test-unit
make test-integration
make test-anchor
make check
```

S4 should add these targets when the corresponding capability is implemented:

```bash
make test-replay
make test-reconciliation
make test-soak
make readiness-check
```

## S4 Definition of Done

S4 is complete only when:

1. A realistic backtest runs end-to-end from historical data to report.
2. A strategy runs unchanged in backtest, paper, and live.
3. Live execution can submit/cancel/replace through at least one real broker adapter or broker sandbox adapter.
4. Restart recovery reconstructs account/order/position state deterministically.
5. Broker reconciliation detects and reports mismatches.
6. Risk controls fail closed.
7. Kill switch cancels active orders and blocks new orders.
8. Operator console exposes strategy/account/order/risk/runtime health.
9. Audit trail reconstructs why an order happened.
10. All anchor tests pass.
11. Production readiness review is signed off.
