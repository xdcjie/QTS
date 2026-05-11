# Next Stage Milestones and Acceptance Criteria

## S2-00 — Baseline Audit

### Goal
Confirm that the completed initial backlog is stable enough for next-stage work.

### Deliverables
- Current architecture review.
- Current test result summary.
- List of known gaps and accepted limitations.
- Updated `MANIFEST.md` if files were added or moved.

### Acceptance Criteria
- `make check` passes or every failure is documented with an owner task.
- No known dependency-rule violation is left undocumented.
- An implementation worker can identify the next task from `next_stage_fine_grained_backlog.md`.

---

## S2-01 — Data Persistence and Replay

### Goal
Make market data storage and deterministic replay reliable enough for repeatable backtests and paper simulations.

### Deliverables
- Data store interface.
- In-memory store.
- File-backed store, preferably Parquet.
- Replay feed using stored bars.
- Data validation utilities.
- Tests for replay determinism.

### Acceptance Criteria
- Same input data replay produces the same BarEvent sequence.
- Bar intervals remain `[start, end)`.
- Session-outside bars are rejected or marked according to the design.
- `make test-unit` and relevant anchor tests pass.

---

## S2-02 — Event Store and Runtime Recovery

### Goal
Persist critical system events and support state reconstruction.

### Deliverables
- Event store interface.
- In-memory event store.
- File-backed event store.
- Event serialization/deserialization.
- Runtime recovery design validation.

### Acceptance Criteria
- Events preserve `event_id`, `correlation_id`, and `causation_id`.
- Replayed events reconstruct expected account/order state in integration tests.
- Duplicate event handling is deterministic.

---

## S2-03 — Strategy Lifecycle

### Goal
Support strategy registration, configuration, instantiation, start, stop, and inspection.

### Deliverables
- Strategy registry.
- Strategy instance model.
- Strategy config schema.
- Strategy lifecycle service.
- Example configured strategies.

### Acceptance Criteria
- One Strategy class can run multiple configured instances.
- Strategy instances cannot directly access broker/risk/order internals.
- Starting/stopping strategy instances is deterministic and tested.

---

## S2-04 — Order Lifecycle Hardening

### Goal
Make order state transitions robust against realistic broker behavior.

### Deliverables
- Explicit order state machine tests.
- Duplicate report handling.
- Out-of-order report handling.
- Cancel/replace lifecycle handling.
- Fill idempotency tests.

### Acceptance Criteria
- Duplicate fills do not double-count positions or cash.
- Partial fill before accepted status does not corrupt state.
- Cancel accepted followed by late fill is handled according to the documented state machine.
- Anchor tests cover state-machine invariants.

---

## S2-05 — Risk Configuration

### Goal
Make risk rules configurable per account, strategy, product, and instrument class.

### Deliverables
- Risk config schema.
- Rule registry.
- Account-level risk profile.
- Product-specific rule configuration.
- Risk decision audit fields.

### Acceptance Criteria
- Risk checks return explicit `RiskDecision`.
- Rejected decisions include reason codes.
- Risk config cannot be bypassed by Strategy SDK or direct order APIs.
- Integration tests cover a rejected order path.

---

## S2-06 — Paper Trading Runtime

### Goal
Run the full flow without real broker connectivity.

### Deliverables
- Paper runtime entrypoint.
- Simulated broker connected through BrokerActor/BrokerAdapter interface.
- Strategy-to-fill loop using actor runtime.
- Paper account state reporting.

### Acceptance Criteria
- A sample strategy produces target intents, orders, fills, and portfolio updates.
- Flow uses the same Risk and OrderManager path as backtest/live design.
- `make test-integration` passes.

---

## S2-07 — API Layer MVP

### Goal
Expose core operations through stable HTTP APIs.

### Deliverables
- Application services.
- API schemas.
- Routes for accounts, strategies, orders, risk, market data, and backtests.
- API tests.

### Acceptance Criteria
- API does not expose actor internals.
- API does not mutate domain state directly.
- API calls application services.
- Public schemas are explicit and typed.

---

## S2-08 — WebSocket Streams

### Goal
Stream runtime state to frontend and operators.

### Deliverables
- WebSocket manager.
- Streams for order updates, fills, strategy status, market data, risk alerts, and logs.
- Subscription model.

### Acceptance Criteria
- Streams use DTOs, not raw domain/actor objects.
- Disconnected clients do not break runtime actors.
- Integration tests cover subscription and event delivery basics.

---

## S2-09 — Frontend Console MVP

### Goal
Provide operational visibility and safe controls.

### Deliverables
- Account view.
- Strategy view.
- Orders/fills view.
- Risk status view.
- System health view.

### Acceptance Criteria
- Frontend consumes backend APIs only.
- Frontend does not duplicate trading logic.
- Trading controls call explicit backend actions.
- UI can inspect paper runtime status.

---

## S2-10 — Observability and Audit

### Goal
Make the system debuggable and auditable.

### Deliverables
- Structured logging.
- Correlation ID propagation.
- Audit event schema.
- Metrics placeholders.
- Runtime health endpoint.

### Acceptance Criteria
- A bar-to-fill flow can be traced by correlation ID.
- Risk rejections and order transitions are auditable.
- Logs avoid leaking secrets.

---

## S2-11 — Deployment Baseline

### Goal
Make local deployment reproducible.

### Deliverables
- Docker Compose local environment.
- Backend Dockerfile.
- Frontend Dockerfile placeholder or MVP.
- `.env.example` and config profiles.
- Startup scripts.

### Acceptance Criteria
- Local environment starts from documented commands.
- No real credentials are required.
- Config profile selection is explicit.

---

## S2-12 — Production Readiness Review

### Goal
Confirm readiness for broker-specific paper/live adapter work.

### Deliverables
- Architecture review report.
- Risk review report.
- Data/session correctness review.
- Operational runbook draft.
- Known limitations list.

### Acceptance Criteria
- `make check` passes.
- Domain invariants are covered by anchor tests.
- Cross-module flows are covered by integration tests.
- The next stage can safely focus on broker-specific adapters and live operations.
