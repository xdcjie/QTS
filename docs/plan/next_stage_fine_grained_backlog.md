# Next Stage Fine-Grained Backlog

## How to Use This Backlog

Run one task at a time.

Each task includes:

- Goal
- Scope
- Deliverables
- Verification
- Acceptance Criteria

Suggested Codex command pattern:

```bash
codex "Read AGENTS.md, relevant module AGENTS.md files, and docs/plan/next_stage_fine_grained_backlog.md. Implement TASK_ID only. Add tests and run required checks."
```

---

# S2-00 — Baseline Audit

## S2-00-T01 — Run Baseline Verification

### Goal
Verify the current repository state before next-stage implementation.

### Scope
- No product code changes unless checks cannot run due to missing test/config scaffolding.

### Deliverables
- Baseline verification note in `docs/plan/status/baseline_verification.md`.

### Verification
```bash
make check
```

### Acceptance Criteria
- [√] `make check` passes, or failures are documented with follow-up tasks.

## S2-00-T02 — Review Architecture Boundaries

### Goal
Confirm current code follows dependency rules.

### Scope
- Review imports and module boundaries.
- Do not refactor unless a violation blocks next-stage work.

### Deliverables
- `docs/plan/status/architecture_boundary_review.md`.

### Verification
```bash
make lint
make typecheck
```

### Acceptance Criteria
- [√] Known boundary violations are listed and mapped to backlog tasks.

---

# S2-01 — Data Persistence and Replay

## S2-01-T01 — Define MarketDataStore Interface

### Goal
Create a stable interface for storing and reading bars.

### Scope
- `qts/data/stores/base.py`
- Bar read/write protocol.
- No database-specific implementation yet.

### Deliverables
- `MarketDataStore` protocol or abstract base.
- Unit tests for interface expectations using a fake implementation.

### Verification
```bash
make test-unit
make typecheck
```

### Acceptance Criteria
- [√] Interface supports writing bars and reading by instrument, timeframe, and time range.
- [√] Interface uses internal domain types, not vendor symbols.

## S2-01-T02 — Implement InMemoryMarketDataStore

### Goal
Provide deterministic in-memory data storage for tests and local runs.

### Scope
- `qts/data/stores/memory_store.py`

### Deliverables
- In-memory implementation.
- Unit tests for ordering, filtering, and empty ranges.

### Verification
```bash
make test-unit
```

### Acceptance Criteria
- [√] Reads return bars sorted by `[start_time, end_time)`.
- [√] Read ranges use half-open semantics.

## S2-01-T03 — Implement ParquetMarketDataStore Skeleton

### Goal
Add a file-backed store for local historical data.

### Scope
- `qts/data/stores/parquet_store.py`
- Minimal partitioning by instrument/timeframe/date.

### Deliverables
- Parquet store skeleton.
- Unit tests using temporary directory.

### Verification
```bash
make test-unit
```

### Acceptance Criteria
- [√] Written bars can be read back exactly for a test dataset.
- [√] Store does not require broker/data vendor symbols.

## S2-01-T04 — Implement ReplayFeed from MarketDataStore

### Goal
Replay stored bars as deterministic market data events.

### Scope
- `qts/data/feeds/replay_feed.py`

### Deliverables
- Replay feed iterator or async producer.
- Unit tests for deterministic order.

### Verification
```bash
make test-unit
make test-integration
```

### Acceptance Criteria
- [√] Same stored input produces identical replay sequence.
- [√] Timeframe-aware BarEvents are preserved.

## S2-01-T05 — Add Data Validation Report

### Goal
Detect obvious data integrity problems before backtest/paper runs.

### Scope
- Missing bars.
- Overlapping bars.
- Bars outside session.
- Non-monotonic time ranges.

### Deliverables
- `qts/data/validation_report.py` or equivalent.
- Unit and anchor tests.

### Verification
```bash
make test-unit
make test-anchor
```

### Acceptance Criteria
- [√] Invalid bar intervals are detected.
- [√] Session-outside bars are detected for configured calendars.

---

# S2-02 — Event Store and Recovery

## S2-02-T01 — Define EventStore Interface

### Goal
Create a stable interface for persisting and reading events.

### Scope
- `qts/runtime/event_store.py`

### Deliverables
- EventStore protocol/ABC.
- Append and read APIs.
- Unit tests with fake store.

### Verification
```bash
make test-unit
make typecheck
```

### Acceptance Criteria
- [√] Events preserve ordering by append sequence.
- [√] Events retain event metadata.

## S2-02-T02 — Implement InMemoryEventStore

### Goal
Support deterministic event recording in tests.

### Scope
- In-memory event store implementation.

### Deliverables
- Append/read by stream or correlation ID.
- Unit tests.

### Verification
```bash
make test-unit
```

### Acceptance Criteria
- [√] Events can be queried by correlation ID.

## S2-02-T03 — Implement FileEventStore Skeleton

### Goal
Add a simple persistent event store for local runs.

### Scope
- JSONL or SQLite skeleton.
- No production database complexity yet.

### Deliverables
- File-backed append/read.
- Serialization tests.

### Verification
```bash
make test-unit
```

### Acceptance Criteria
- [√] Events survive process restart in tests.

## S2-02-T04 — Add Runtime Recovery Integration Test

### Goal
Verify state can be reconstructed from events.

### Scope
- Minimal order/account reconstruction path.

### Deliverables
- Integration test.

### Verification
```bash
make test-integration
```

### Acceptance Criteria
- [ ] Replayed events reconstruct expected order and position state.

---

# S2-03 — Strategy Lifecycle

## S2-03-T01 — Define StrategyInstance Model

### Goal
Separate strategy class from configured runtime instance.

### Scope
- `qts/application` or `qts/strategy_sdk` boundary.

### Deliverables
- StrategyInstance model.
- Config fields: strategy_id, class path, account_id, params, allocation, enabled.

### Verification
```bash
make test-unit
make typecheck
```

### Acceptance Criteria
- [√] Same Strategy class can produce multiple instances.

## S2-03-T02 — Implement StrategyRegistry

### Goal
Register and resolve strategy classes safely.

### Scope
- Strategy class registry.
- No dynamic untrusted code loading yet.

### Deliverables
- Registry implementation.
- Unit tests.

### Verification
```bash
make test-unit
```

### Acceptance Criteria
- [√] Duplicate registration is handled explicitly.
- [√] Missing strategy returns explicit error.

## S2-03-T03 — Implement StrategyLifecycleService

### Goal
Create application service for start/stop/status.

### Scope
- `qts/application/services/strategy_service.py`

### Deliverables
- Start/stop/status APIs.
- Unit tests.

### Verification
```bash
make test-unit
make test-integration
```

### Acceptance Criteria
- [√] Strategy instance status changes are explicit and deterministic.

## S2-03-T04 — Add Strategy Config Examples

### Goal
Make strategy execution configurable.

### Scope
- `examples/configs/`
- `configs/backtest.yaml`

### Deliverables
- Example config for at least two strategy instances.

### Verification
```bash
make test-unit
```

### Acceptance Criteria
- [√] Config can be parsed into StrategyInstance models.

---

# S2-04 — Order Lifecycle Hardening

## S2-04-T01 — Expand Order State Machine Tests

### Goal
Cover realistic broker order lifecycle paths.

### Scope
- `tests/unit/execution/`
- `tests/anchor/test_order_state_machine_anchors.py`

### Deliverables
- Tests for accepted, partial fill, full fill, cancel, reject, replace.

### Verification
```bash
make test-unit
make test-anchor
```

### Acceptance Criteria
- [√] Illegal transitions are rejected explicitly.

## S2-04-T02 — Implement Duplicate Fill Idempotency

### Goal
Ensure duplicate fill reports do not alter state twice.

### Scope
- OrderManager / idempotency helper.

### Deliverables
- Fill deduplication by broker fill id or internal event id.
- Anchor test.

### Verification
```bash
make test-unit
make test-anchor
```

### Acceptance Criteria
- [√] Duplicate fill does not double-count position/cash.

## S2-04-T03 — Handle Out-of-Order Broker Reports

### Goal
Support realistic broker report ordering.

### Scope
- Partial fill before accepted.
- Cancel accepted followed by late fill.

### Deliverables
- State-machine logic and tests.

### Verification
```bash
make test-unit
make test-anchor
```

### Acceptance Criteria
- [√] Out-of-order reports do not corrupt order/account state.

## S2-04-T04 — Add Cancel/Replace Intent Flow

### Goal
Represent cancel and replace through OrderManager.

### Scope
- CancelIntent.
- ReplaceIntent.
- State transitions.

### Deliverables
- Domain models and tests.

### Verification
```bash
make test-unit
make test-integration
```

### Acceptance Criteria
- [√] Cancel/replace does not bypass Risk/OrderManager policies.

---

# S2-05 — Risk Configuration

## S2-05-T01 — Define RiskConfig Schema

### Goal
Represent account, strategy, and product risk rules in configuration.

### Scope
- `qts/risk` and config schema.

### Deliverables
- RiskConfig model.
- Unit tests.

### Verification
```bash
make test-unit
make typecheck
```

### Acceptance Criteria
- [√] Config supports account-level max notional, max leverage, and product-specific rules.

## S2-05-T02 — Implement RiskRuleRegistry

### Goal
Map configured rules to executable risk checks.

### Scope
- `qts/risk/rule_registry.py`

### Deliverables
- Rule lookup and construction.
- Unit tests.

### Verification
```bash
make test-unit
```

### Acceptance Criteria
- [√] Unknown rule names fail explicitly.

## S2-05-T03 — Add Risk Decision Audit Fields

### Goal
Make risk outcomes traceable.

### Scope
- RiskDecision model.

### Deliverables
- reason_code, reason_text, rule_id, checked_at.
- Unit tests.

### Verification
```bash
make test-unit
```

### Acceptance Criteria
- [√] Rejections always include a reason code.

## S2-05-T04 — Add Rejected Order Integration Test

### Goal
Verify risk rejections stop the trading flow safely.

### Scope
- Strategy target over limit.
- Risk rejection.
- No order sent to broker.

### Deliverables
- Integration test.

### Verification
```bash
make test-integration
```

### Acceptance Criteria
- [√] Rejected intent does not reach BrokerActor.

---

# S2-06 — Paper Trading Runtime

## S2-06-T01 — Define PaperRuntime Configuration

### Goal
Configure paper runtime using data feed, strategies, account, and simulated broker.

### Scope
- `qts/backtest` or `qts/application` runtime config.

### Deliverables
- Config schema and example.

### Verification
```bash
make test-unit
```

### Acceptance Criteria
- [√] Example paper config validates.

## S2-06-T02 — Implement Paper Runtime Entrypoint

### Goal
Start a paper runtime from config.

### Scope
- `scripts/run_paper.py`
- `qts/application/commands/start_paper.py`

### Deliverables
- CLI entrypoint skeleton.
- Smoke test.

### Verification
```bash
make test-unit
make test-integration
```

### Acceptance Criteria
- [√] Paper runtime can be constructed without real broker credentials.

## S2-06-T03 — Connect Simulated Broker Through BrokerActor

### Goal
Ensure paper flow uses the same broker abstraction as live design.

### Scope
- Simulated broker adapter.
- BrokerActor integration.

### Deliverables
- Integration test for order to simulated fill.

### Verification
```bash
make test-integration
```

### Acceptance Criteria
- [√] Simulated fills enter through OrderManager before account update.

## S2-06-T04 — Run Example Strategy in Paper Runtime

### Goal
Prove strategy-to-fill loop works.

### Scope
- Moving average example.
- Replay feed or generated bars.

### Deliverables
- Integration test.

### Verification
```bash
make test-integration
```

### Acceptance Criteria
- [√] Strategy emits target, risk approves, order fills, portfolio updates.

---

# S2-07 — API Layer MVP

## S2-07-T01 — Add Application Service Interfaces

### Goal
Create API-facing use-case boundaries.

### Scope
- `qts/application/services/`

### Deliverables
- AccountService, StrategyService, OrderService, RiskService, BacktestService interfaces.

### Verification
```bash
make test-unit
make typecheck
```

### Acceptance Criteria
- [√] API routes will depend on application services, not actors directly.

## S2-07-T02 — Implement API App Skeleton

### Goal
Create backend API app entrypoint.

### Scope
- `qts/api/app.py`

### Deliverables
- Health endpoint.
- Test client smoke test.

### Verification
```bash
make test-unit
```

### Acceptance Criteria
- [√] Health endpoint returns expected status.

## S2-07-T03 — Implement Strategy API Routes

### Goal
Expose strategy listing, config, start, stop, and status.

### Scope
- `qts/api/routes/strategies.py`
- schemas.

### Deliverables
- Route handlers calling StrategyService.
- API tests.

### Verification
```bash
make test-unit
make test-integration
```

### Acceptance Criteria
- [√] Routes do not expose actor internals.

## S2-07-T04 — Implement Account and Order API Routes

### Goal
Expose account snapshots and order lifecycle state.

### Scope
- account routes.
- order routes.

### Deliverables
- DTOs and route tests.

### Verification
```bash
make test-unit
make test-integration
```

### Acceptance Criteria
- [√] API responses use schema models, not raw domain objects.

## S2-07-T05 — Implement Backtest API Skeleton

### Goal
Allow starting and inspecting backtest jobs.

### Scope
- backtest route skeleton.
- no distributed job system yet.

### Deliverables
- Start/status endpoints.
- Tests.

### Verification
```bash
make test-unit
```

### Acceptance Criteria
- [√] Backtest endpoint returns explicit job/status DTOs.

---

# S2-08 — WebSocket Streams

## S2-08-T01 — Implement WebSocket Connection Manager

### Goal
Manage client connections safely.

### Scope
- `qts/api/websocket/manager.py`

### Deliverables
- Connect/disconnect/broadcast basics.
- Unit tests.

### Verification
```bash
make test-unit
```

### Acceptance Criteria
- [√] Disconnected client does not fail broadcasts to others.

## S2-08-T02 — Define Stream Event DTOs

### Goal
Create public streaming event schemas.

### Scope
- order update, fill, risk alert, strategy status, log event.

### Deliverables
- DTOs and tests.

### Verification
```bash
make test-unit
```

### Acceptance Criteria
- [√] No raw actor objects are exposed.

## S2-08-T03 — Add Order/Fills Stream Integration Test

### Goal
Verify runtime events can be streamed to clients.

### Scope
- simulated order update stream.

### Deliverables
- Integration test.

### Verification
```bash
make test-integration
```

### Acceptance Criteria
- [ ] A fill event can be transformed into stream DTO and delivered.

---

# S2-09 — Frontend Console MVP

## S2-09-T01 — Initialize Frontend App Skeleton

### Goal
Create frontend project skeleton without trading logic.

### Scope
- `frontend/`

### Deliverables
- package skeleton.
- API client placeholder.

### Verification
```bash
# if frontend tooling exists
npm test
```

### Acceptance Criteria
- [√] Frontend does not duplicate backend trading logic.

## S2-09-T02 — Implement API Client Types

### Goal
Consume backend schemas in a typed way.

### Scope
- `frontend/src/api/`
- `frontend/src/types/`

### Deliverables
- Account, strategy, order, risk DTO types.

### Verification
```bash
npm test
```

### Acceptance Criteria
- [√] Types mirror public API responses, not internal domain/actor objects.

## S2-09-T03 — Implement Strategy Status View

### Goal
Show configured strategies and status.

### Scope
- `frontend/src/features/strategies/`

### Deliverables
- Strategy table or cards.

### Verification
```bash
npm test
```

### Acceptance Criteria
- [√] View reads API state and does not create local trading state.

## S2-09-T04 — Implement Orders and Fills View

### Goal
Inspect order lifecycle and fills.

### Scope
- `frontend/src/features/orders/`

### Deliverables
- Orders/fills table.

### Verification
```bash
npm test
```

### Acceptance Criteria
- [√] Order state display follows backend DTO state.

---

# S2-10 — Observability and Audit

## S2-10-T01 — Add Structured Logging Helpers

### Goal
Standardize logs with event/correlation IDs.

### Scope
- `qts/observability/logging.py`

### Deliverables
- Logger helper.
- Unit tests.

### Verification
```bash
make test-unit
```

### Acceptance Criteria
- [√] Logs can include event_id, correlation_id, causation_id.

## S2-10-T02 — Add Audit Event Model

### Goal
Represent important operational and trading audit events.

### Scope
- `qts/observability/audit.py`

### Deliverables
- Audit event model.
- Tests.

### Verification
```bash
make test-unit
```

### Acceptance Criteria
- [√] Risk rejection and order transition can be represented as audit events.

## S2-10-T03 — Add Correlation Trace Integration Test

### Goal
Trace a bar-to-fill flow by correlation ID.

### Scope
- Integration test over runtime flow.

### Deliverables
- Test verifying correlation propagation.

### Verification
```bash
make test-integration
```

### Acceptance Criteria
- [√] Bar, target, order, fill, and portfolio update share traceable correlation.

---

# S2-11 — Deployment Baseline

## S2-11-T01 — Add Config Profiles

### Goal
Make local/backtest/paper/live configs explicit.

### Scope
- `configs/`
- `.env.example`

### Deliverables
- local.yaml, backtest.yaml, paper.yaml, live.example.yaml.

### Verification
```bash
make test-unit
```

### Acceptance Criteria
- [√] Configs contain no real credentials.

## S2-11-T02 — Add Backend Dockerfile

### Goal
Provide reproducible backend container build.

### Scope
- `docker/Dockerfile.backend`

### Deliverables
- Dockerfile.
- Build instructions.

### Verification
```bash
docker build -f docker/Dockerfile.backend .
```

### Acceptance Criteria
- [ ] Build succeeds in local environment.

## S2-11-T03 — Add Docker Compose Local Environment

### Goal
Provide local orchestration skeleton.

### Scope
- `docker/docker-compose.local.yml`

### Deliverables
- backend service.
- optional frontend placeholder.

### Verification
```bash
docker compose -f docker/docker-compose.local.yml config
```

### Acceptance Criteria
- [ ] Compose config validates without secrets.

---

# S2-12 — Production Readiness Review

## S2-12-T01 — Run Full Verification

### Goal
Confirm next-stage system health.

### Scope
- No product code changes unless verification commands are broken.

### Deliverables
- `docs/plan/status/next_stage_verification.md`

### Verification
```bash
make check
```

### Acceptance Criteria
- [√] `make check` passes or every failure is documented.

## S2-12-T02 — Create Operational Runbook Draft

### Goal
Document how to run, stop, inspect, and recover the system.

### Scope
- `docs/infra/operational_runbook.md`

### Deliverables
- Startup, shutdown, paper run, backtest run, recovery, troubleshooting sections.

### Verification
Manual documentation review.

### Acceptance Criteria
- [√] A new developer can run the paper runtime from the runbook.

## S2-12-T03 — Create Next-Stage Gap Analysis

### Goal
Define the following stage after this one.

### Scope
- Broker-specific adapters.
- Live operations.
- Frontend hardening.
- Advanced risk.

### Deliverables
- `docs/plan/next_stage_gap_analysis.md`

### Verification
Manual review.

### Acceptance Criteria
- [√] Follow-up backlog is actionable and ranked.
