# 2026-05-10 S3-00 Live Beta Implementation Plan

## Purpose

S3 moves the system from a completed paper/live-ready alpha into **live beta / production-hardening**.

The focus is safety, correctness, operability, recovery, observability, and controlled live execution.

## Assumptions

S3 assumes these are complete:

- Core domain models and event model
- Timeframe-aware bar model and stateful `BarAggregator`
- Backtest and paper runtime
- Strategy SDK
- Portfolio/Risk/Execution flow
- Actor runtime MVP
- Event store MVP
- API/WebSocket MVP
- Frontend MVP
- Unit, integration, and anchor test foundations
- `next_stage_fine_grained_backlog.md`

If any of these are incomplete, finish them before S3.

## S3 stage goals

1. Stable broker adapter contracts.
2. Stable live market data adapter contracts.
3. Reconciliation engine for broker/account/order/position drift.
4. Live runtime orchestration with explicit lifecycle states.
5. Kill-switches and operational risk controls.
6. Multi-account live partitioning.
7. Restart recovery and pending order safety.
8. Hardened API/WebSocket operational surfaces.
9. Operational frontend console.
10. Observability, audit, and incident workflows.
11. Load/soak testing.
12. Deployment, CI/CD, and secrets baseline.
13. Live beta readiness review.

## Milestones

- S3-00 — Planning and baseline verification
- S3-01 — Broker adapter contracts
- S3-02 — Live market data adapters
- S3-03 — Reconciliation engine
- S3-04 — Live runtime orchestration
- S3-05 — Risk controls and kill-switches
- S3-06 — Multi-account live partitioning
- S3-07 — Event-store recovery and restart safety
- S3-08 — API and WebSocket hardening
- S3-09 — Frontend operational console
- S3-10 — Observability, audit, and incident workflows
- S3-11 — Performance, load, and soak testing
- S3-12 — Deployment, CI/CD, and secrets baseline
- S3-13 — Live beta readiness review

## Non-goals

Out of scope unless explicitly approved:

- HFT-grade latency optimization
- Full multi-region production deployment
- Complex option portfolio margin beyond current risk model
- Strategy marketplace
- Multi-tenant SaaS behavior
- Real broker SDK adoption before adapter contracts and fake adapters are tested

## Execution rules

- Implement one task at a time from `2026-05-10_S3-02_live_beta_fine_grained_backlog.md`.
- Prefer fake adapters before real adapters.
- Keep broker/vendor objects out of domain models.
- Do not bypass `Risk`, `AccountActor`, `OrderManager`, or broker normalization.
- Add integration tests for runtime flows.
- Add anchor tests for financial correctness and recovery invariants.
- Update documentation when behavior changes.

## Verification

Minimum:

```bash
make format
make lint
make typecheck
make test-unit
```

If the task affects runtime, broker, order, API, reconciliation, or cross-module behavior:

```bash
make test-integration
```

If the task affects financial correctness, order lifecycle, recovery, accounting, calendars/sessions, or risk semantics:

```bash
make test-anchor
```

For milestone completion:

```bash
make check
```

Optional targets introduced as needed:

```bash
make test-contract
make test-e2e
make test-load
make test-soak
```
