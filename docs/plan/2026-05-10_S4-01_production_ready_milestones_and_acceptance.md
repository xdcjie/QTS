# 2026-05-10 S4-01 Production-Ready Milestones and Acceptance

## Acceptance philosophy

Each milestone must satisfy:

1. **Domain correctness** — first-principles financial truth is preserved.
2. **Engineering correctness** — code is simple, typed, tested, and maintainable.
3. **Operational correctness** — behavior is observable, recoverable, and safe under failure.
4. **Verification evidence** — relevant unit, integration, anchor, replay, reconciliation, or soak tests pass.

---

## S4-00 Baseline Freeze and Readiness Audit

### Acceptance

- `make check` passes or failures are explicitly classified.
- S3 completion is documented.
- Known defects are listed by severity.
- No unreviewed architecture violations exist.
- Docs and module AGENTS match actual code.

## S4-01 Historical Data Correctness and Provenance

### Acceptance

- Historical data source, symbol mapping, timezone, session, and adjustment policy are explicit.
- Dataset provenance is persisted with every backtest report.
- Raw data and normalized data are distinguishable.
- Missing bars, duplicate bars, out-of-session bars, non-monotonic timestamps, and invalid OHLC values are detectable.
- Historical data load is reproducible.
- Domain-sensitive data rules have anchor tests.

## S4-02 Calendar, Session, and Bar Correctness Hardening

### Acceptance

- `<1d` bars are exchange-time clock-aligned.
- `1d` bars are session-aligned and never treated as 24h.
- All intervals use `[start, end)`.
- Holidays, early closes, and late opens are respected.
- COMEX Gold normal session 1m count is `1380`.
- Bar aggregation tests cover `5s -> 1m -> 5m -> 15m -> 30m -> 1h -> 4h -> 1d`.
- Partial intraday bars are explicitly marked.
- No out-of-session bars enter aggregation.

## S4-03 Real Backtest Engine Validation

### Acceptance

- Backtest DataView cannot access future data.
- Strategy lifecycle matches paper/live where applicable.
- Backtest uses the same Strategy SDK as live.
- Fill, commission, slippage, and latency assumptions are explicit.
- Backtest reports include input dataset metadata.
- Same inputs produce same outputs.
- Replay tests prove deterministic event order.

## S4-04 Strategy SDK Parity and Research/Live Equivalence

### Acceptance

- Strategy code cannot import runtime, broker, risk internals, or order manager internals.
- Strategy APIs produce intents, not direct portfolio mutation.
- DataView behavior is consistent across backtest/paper/live.
- Indicator warmup is deterministic.
- Strategy state snapshot/restore works.
- A reference strategy runs unchanged in backtest and paper/live simulation.

## S4-05 Portfolio Accounting and PnL Correctness

### Acceptance

- Stock accounting uses quantity and price correctly.
- Futures PnL uses `contracts * price_diff * multiplier`.
- Options premium value uses `contracts * option_price * multiplier`.
- Realized and unrealized PnL are separated.
- Cash, buying power, reservations, and frozen funds are consistent.
- Duplicate fills are idempotent.
- Anchor tests cover accounting invariants.

## S4-06 Risk Correctness and Fail-Closed Controls

### Acceptance

- Risk decisions are explicit: approved, rejected, or blocked.
- Missing safety-critical data fails closed.
- Max notional, max position, max order quantity, leverage, session, stale data, and kill-switch rules work.
- Product-specific risk rules are isolated.
- Rejected orders include reason codes.
- Risk bypass is impossible through public APIs and Strategy SDK.
- Anchor/integration tests prove risk runs before broker submission.

## S4-07 Broker and Live Execution Correctness

### Acceptance

- Broker capabilities are modeled explicitly.
- Order submit/cancel/replace is supported or explicitly unsupported per broker.
- Execution reports are normalized.
- Broker symbol mapping is isolated at adapter boundaries.
- Order state machine tolerates duplicate and out-of-order reports.
- Broker callbacks never mutate account state directly.
- Order lifecycle is testable without live credentials.

## S4-08 Reconciliation and Recovery Correctness

### Acceptance

- Startup reconciliation compares internal account/order/position state with broker state.
- Mismatches are classified and reported.
- Recovery from event store is deterministic.
- Pending orders are reconciled after restart.
- Unknown external fills are detected.
- Recovery does not create duplicate fills or double-count PnL.

## S4-09 Live Runtime Operational Safety

### Acceptance

- Runtime starts and stops cleanly.
- Kill switch blocks new orders and cancels active orders when configured.
- Actor partitions preserve account/order state ordering.
- Market data disconnects, broker disconnects, and stale data are detected.
- Live mode cannot start without required config and risk controls.
- Runtime health is operator-visible.

## S4-10 API and Frontend Operator Workflows

### Acceptance

- UI/API can view accounts, strategies, orders, fills, risk, runtime health, and logs.
- Trading actions require explicit backend commands.
- UI never invents trading state locally.
- Dangerous actions require confirmation and are audited.
- API schemas do not expose actor internals.

## S4-11 Observability, Audit, and Incident Response

### Acceptance

- Every order can be traced from strategy signal to fill.
- Logs include correlation_id and causation_id.
- Audit events are immutable.
- Metrics include event lag, queue depth, stale data, rejected orders, broker status, and reconciliation status.
- Incident runbooks exist for broker disconnect, data outage, reconciliation mismatch, and kill switch activation.

## S4-12 Performance, Load, and Soak Testing

### Acceptance

- Load tests cover realistic market data and strategy counts.
- Soak test runs for defined duration without memory growth or state drift.
- Queue depth and event lag stay within limits.
- Backpressure behavior is defined.
- Slow strategies are isolated.

## S4-13 Deployment, Secrets, and Production Environments

### Acceptance

- Config profiles exist for local, backtest, paper, staging, and live.
- Secrets are not committed.
- Live startup validates required secrets and risk config.
- CI runs format, lint, typecheck, unit, integration, and anchor tests.
- Deployment rollback path exists.

## S4-14 Controlled Live Rollout

### Acceptance

- Live rollout starts with observation mode.
- Paper/sandbox comparison is run before real capital.
- Small-capital live uses strict risk limits.
- Kill switch drill is performed before capital is enabled.
- Reconciliation is clean before, during, and after session.

## S4-15 Final Production Readiness Review

### Acceptance

- All S4 milestones are complete.
- All critical tests pass.
- Known issues are classified and accepted or fixed.
- Risk limits, broker limitations, data limitations, and incident procedures are documented.
- Go/no-go decision is recorded in ADR or readiness report.
