# 2026-05-10 S4-02 Production-Ready Fine-Grained Backlog

## Usage

Implement exactly one task at a time. Each task must preserve the first-principles acceptance matrix.

For each task:

1. Read `AGENTS.md` and relevant module `AGENTS.md`.
2. Read this backlog and `2026-05-10_S4-03_first_principles_acceptance_matrix.md`.
3. State the domain truth and invariant before coding.
4. Add or update tests.
5. Run required checks.

---

# S4-00 Baseline Freeze and Readiness Audit

## S4-00-T01 — Run Baseline Verification

Goal: Establish a clean baseline before S4 changes.

Verification:

```bash
make check
```

Acceptance:

- Check results are recorded.
- Failures are classified.
- No implementation changes are made unless required to make baseline runnable.

## S4-00-T02 — Create S4 Readiness Report Template

Deliverable:

- `docs/plan/2026-05-10_S4_readiness_report_template.md`

Acceptance:

- Template includes completed tasks, failed checks, known risks, accepted limitations, and go/no-go decision.

## S4-00-T03 — Align Docs With Current Code

Acceptance:

- Docs reflect actual directories.
- Outdated references are removed.
- Architecture rules are not weakened.

---

# S4-01 Historical Data Correctness and Provenance

## S4-01-T01 — Define Dataset Metadata Model

Goal: Model historical dataset identity and provenance.

Deliverables:

- Dataset metadata model
- Unit tests

Acceptance:

- Metadata includes dataset_id, source, instrument_id, timeframe, timezone policy, adjustment policy, normalization version, created_at, and checksum/content hash when practical.
- Backtest reports can reference dataset metadata.
- Required provenance fields are validated.

## S4-01-T02 — Implement Historical Data Validation Report

Goal: Detect data quality issues before backtesting.

Detect:

- missing bars
- duplicate bars
- out-of-session bars
- non-monotonic timestamps
- invalid OHLC values
- unexpected gaps

Verification:

```bash
make test-unit
make test-anchor
```

Acceptance:

- Issues are classified by severity.
- Out-of-session bars are never silently accepted.
- Domain-sensitive validation has anchor tests.

## S4-01-T03 — Add Dataset Provenance to Backtest Report

Verification:

```bash
make test-integration
```

Acceptance:

- Report includes dataset metadata.
- Different dataset IDs produce distinguishable reports.
- Data validation warnings are visible.

---

# S4-02 Calendar, Session, and Bar Correctness Hardening

## S4-02-T01 — Add Exchange Calendar Adapter Contract

Acceptance:

- Calendar interface returns project domain types.
- `exchange-calendars` objects do not leak into domain or Strategy SDK.
- Adapter answers session open/close, holidays, early closes, and late opens.
- Calendar can be faked in tests.

## S4-02-T02 — Add COMEX Gold Calendar Anchors

Verification:

```bash
make test-anchor
```

Acceptance:

- Normal session `[ET 18:00, ET 17:00)` has 1380 one-minute bars.
- Test excludes holidays and special sessions.
- UTC/ET conversion does not change count.

## S4-02-T03 — Harden BarAggregator Boundary Tests

Acceptance:

- `1m -> 5m` uses `[00m, 05m)`, `[05m, 10m)`.
- Exact boundary belongs to next bucket.
- `<1d` is clock-aligned.
- `1d` is session-aligned.
- Partial intraday bars are explicitly marked.

## S4-02-T04 — Add Bar Aggregation Gap Policy

Acceptance:

- Gap policy is explicit.
- Aggregated bars include completeness metadata.
- Missing lower-timeframe bars do not silently produce complete bars.

---

# S4-03 Real Backtest Engine Validation

## S4-03-T01 — Add Backtest Run Identity

Acceptance:

- BacktestRunId exists.
- Report includes strategy version, config hash, and dataset metadata.

## S4-03-T02 — Enforce Time-Sliced DataView

Verification:

```bash
make test-anchor
make test-integration
```

Acceptance:

- DataView cannot return data after runtime clock.
- Attempts to access future data fail.

## S4-03-T03 — Add Deterministic Replay Test

Verification:

```bash
make test-replay
```

Acceptance:

- Same data/config/strategy produces same report hash.
- Clock and random seeds are controlled.

## S4-03-T04 — Add Explicit Slippage/Commission Models

Acceptance:

- Fill, slippage, and commission assumptions are explicit in config and report.

---

# S4-04 Strategy SDK Parity and Research/Live Equivalence

## S4-04-T01 — Add Strategy Import Boundary Test

Acceptance:

- Example strategies import only Strategy SDK and approved public types.
- Test fails if strategies import runtime/execution/risk internals.

## S4-04-T02 — Add Reference Strategy Parity Test

Verification:

```bash
make test-integration
```

Acceptance:

- Same strategy source runs in backtest and paper simulation.
- Target intents are semantically equivalent.

## S4-04-T03 — Add Strategy State Snapshot/Restore

Acceptance:

- Strategy and indicator state can be snapshotted and restored deterministically.

---

# S4-05 Portfolio Accounting and PnL Correctness

## S4-05-T01 — Add Stock Accounting Anchors

Acceptance:

- Market value = quantity * price.
- Buy/sell fill updates quantity/cash correctly.

## S4-05-T02 — Add Futures Accounting Anchors

Acceptance:

- PnL = contracts * price_diff * multiplier.
- Margin and notional are separate.

## S4-05-T03 — Add Option Accounting Anchors

Acceptance:

- Premium value = contracts * option_price * multiplier.
- Long/short option cash effects are correct.

## S4-05-T04 — Add Fill Idempotency Tests

Acceptance:

- Duplicate fill does not double count.
- Recovery replay does not double count.

---

# S4-06 Risk Correctness and Fail-Closed Controls

## S4-06-T01 — Add Fail-Closed Risk Policy

Acceptance:

- Missing critical price, calendar, or ContractSpec blocks order.
- Rejected decisions include reason codes.

## S4-06-T02 — Add Kill Switch Integration Test

Acceptance:

- Kill switch blocks new orders.
- Active orders are cancelled if configured.
- Event is audited.

## S4-06-T03 — Add Stale Market Data Risk Rule

Acceptance:

- Stale threshold is configurable.
- Orders relying on stale data are blocked.

---

# S4-07 Broker and Live Execution Correctness

## S4-07-T01 — Harden Broker Capability Model

Acceptance:

- Capabilities include market/limit/stop support, cancel, replace, TIF, fractional, and short support.
- Unsupported orders are rejected before broker submission.

## S4-07-T02 — Add Execution Report Normalization Tests

Acceptance:

- Raw broker reports normalize into internal execution reports.
- Unknown statuses are not silently accepted.

## S4-07-T03 — Add Order State Race Tests

Acceptance:

- Partial fill after cancel request is handled.
- Fill before accepted report is handled.
- Duplicate reports are idempotent.

---

# S4-08 Reconciliation and Recovery Correctness

## S4-08-T01 — Implement Reconciliation Snapshot Model

Acceptance:

- Internal and external snapshots can be compared.
- Differences are classified.

## S4-08-T02 — Add Startup Reconciliation Flow

Acceptance:

- Trading remains disabled if critical mismatches exist.
- Operator-visible reconciliation report is produced.

## S4-08-T03 — Add Deterministic Event Replay Recovery

Acceptance:

- Replay reconstructs account/order state.
- Replay result equals expected snapshot.
- Duplicate fills do not double count after replay.

---

# S4-09 Live Runtime Operational Safety

## S4-09-T01 — Add Live Startup Guard

Acceptance:

- Live mode refuses to start without broker, account, risk, calendar, and kill-switch config.

## S4-09-T02 — Add Market Data Disconnect Handling

Acceptance:

- Disconnect is detected.
- Dependent strategies are paused or blocked.
- Risk gate treats stale/missing data safely.

## S4-09-T03 — Add Broker Disconnect Handling

Acceptance:

- Broker disconnect blocks new orders.
- Pending orders are reconciled after reconnect.

---

# S4-10 API and Frontend Operator Workflows

## S4-10-T01 — Add Read-Only Operational Status API

Acceptance:

- API exposes runtime health, risk state, broker status, and reconciliation status.
- API schemas do not expose actor internals.

## S4-10-T02 — Add Kill Switch API Workflow

Acceptance:

- Kill switch endpoint requires explicit action.
- Action is audited.
- New orders are blocked after activation.

## S4-10-T03 — Add Order Trace API

Acceptance:

- Operator can trace an order from signal to risk decision to broker report to fill.

---

# S4-11 Observability, Audit, and Incident Response

## S4-11-T01 — Add Correlated Audit Trail

Acceptance:

- Signal, target, risk, order, broker report, and fill share trace identifiers.
- Audit records are append-only.

## S4-11-T02 — Add Runtime Health Metrics

Acceptance:

- Metrics include queue depth, event lag, stale data age, broker status, rejected orders.
- Secrets are not logged.

## S4-11-T03 — Write Incident Runbooks

Deliverables:

- `docs/infra/incidents/broker_disconnect.md`
- `docs/infra/incidents/market_data_outage.md`
- `docs/infra/incidents/reconciliation_mismatch.md`
- `docs/infra/incidents/kill_switch.md`

Acceptance:

- Each runbook includes detection, immediate action, recovery, and postmortem notes.

---

# S4-12 Performance, Load, and Soak Testing

## S4-12-T01 — Add Load Test Harness

Acceptance:

- Harness replays representative market data rate.
- Measures throughput, latency, queue depth.

## S4-12-T02 — Add Soak Test Plan

Acceptance:

- Soak duration and success metrics are defined.
- Memory growth, event lag, and state drift are monitored.

## S4-12-T03 — Add Slow Strategy Isolation Test

Acceptance:

- One slow strategy does not block unrelated accounts/strategies beyond defined limits.

---

# S4-13 Deployment, Secrets, and Production Environments

## S4-13-T01 — Add Live Config Validation

Acceptance:

- Live config requires explicit broker, account, risk, calendar, and kill-switch settings.
- Secrets are referenced, not committed.

## S4-13-T02 — Add CI Verification Plan

Acceptance:

- CI runs format, lint, typecheck, unit, integration, and anchor tests.
- Slow tests are separated.

## S4-13-T03 — Add Rollback Procedure

Acceptance:

- Deployment rollback path is documented.
- Operator can stop trading safely before rollback.

---

# S4-14 Controlled Live Rollout

## S4-14-T01 — Add Observation Mode

Acceptance:

- System can connect to live data/broker without trading.
- Strategy signals and hypothetical orders are recorded.
- Real orders cannot be submitted.

## S4-14-T02 — Add Paper-vs-Live Comparison Report

Acceptance:

- Compares paper decisions against live market/broker state.
- Differences are classified.

## S4-14-T03 — Add Small-Capital Rollout Checklist

Acceptance:

- Checklist includes risk limits, kill switch drill, reconciliation status, operator readiness, and rollback plan.

---

# S4-15 Final Production Readiness Review

## S4-15-T01 — Generate Production Readiness Report

Acceptance:

- Report includes milestone completion, test results, known risks, accepted limitations, and go/no-go decision.
- Unresolved critical issues block production readiness.

## S4-15-T02 — Record Final ADR

Deliverable:

- `docs/adr/0007-production-readiness-decision.md`

Acceptance:

- ADR records decision, rationale, limitations, and rollback criteria.
