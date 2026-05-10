# 2026-05-10 S3-01 Live Beta Milestones and Acceptance

## Acceptance model

Each milestone must satisfy:

1. **Local acceptance** — its own task tests pass.
2. **Flow acceptance** — the milestone integrates into existing runtime flow.
3. **Operational acceptance** — behavior is observable and documented.

## Milestones

### S3-00 — Planning and baseline verification

**Goal:** Confirm the project is ready for live-beta hardening.

**Acceptance:**

- `S3-00-T01` complete: Passes or failures classified.
- `S3-00-T02` complete: Tasks are trackable.
- `S3-00-T03` complete: Violations documented or absent.

### S3-01 — Broker adapter contracts

**Goal:** Create stable broker-facing contracts before real broker integrations.

**Acceptance:**

- `S3-01-T01` complete: Capabilities typed and tested.
- `S3-01-T02` complete: Fake adapter implements interface.
- `S3-01-T03` complete: Vendor objects do not leak.
- `S3-01-T04` complete: Submit/cancel/fill cases covered.
- `S3-01-T05` complete: Boundary documented.

### S3-02 — Live market data adapters

**Goal:** Add stable live feed boundaries.

**Acceptance:**

- `S3-02-T01` complete: Typed and tested.
- `S3-02-T02` complete: Fake feed implements interface.
- `S3-02-T03` complete: Backoff tested.
- `S3-02-T04` complete: Timeframe-aware BarEvents emitted.
- `S3-02-T05` complete: Subscribe/emit/failure covered.

### S3-03 — Reconciliation engine

**Goal:** Detect drift between internal state and broker state.

**Acceptance:**

- `S3-03-T01` complete: Typed and immutable where practical.
- `S3-03-T02` complete: Missing/extra/divergent orders classified.
- `S3-03-T03` complete: Drift classified with tolerance.
- `S3-03-T04` complete: Serializable and deterministic.
- `S3-03-T05` complete: Drift event emitted without direct mutation.

### S3-04 — Live runtime orchestration

**Goal:** Wire live runtime with explicit lifecycle states.

**Acceptance:**

- `S3-04-T01` complete: Illegal transitions fail.
- `S3-04-T02` complete: Start/stop with fakes.
- `S3-04-T03` complete: Pause/resume behavior tested.
- `S3-04-T04` complete: Degraded state observable.
- `S3-04-T05` complete: Startup flow documented.

### S3-05 — Risk controls and kill-switches

**Goal:** Make live operation bounded and stoppable.

**Acceptance:**

- `S3-05-T01` complete: Auditable states tested.
- `S3-05-T02` complete: Rejection reason explicit.
- `S3-05-T03` complete: Other accounts unaffected.
- `S3-05-T04` complete: Other strategies unaffected.
- `S3-05-T05` complete: Activate/deactivate/read tested.
- `S3-05-T06` complete: Uses backend API only.

### S3-06 — Multi-account live partitioning

**Goal:** Safely support multiple live accounts.

**Acceptance:**

- `S3-06-T01` complete: Correct partitioning.
- `S3-06-T02` complete: Broker IDs boundary-only.
- `S3-06-T03` complete: Different limits enforced.
- `S3-06-T04` complete: No state leakage.
- `S3-06-T05` complete: Drift isolated by account.

### S3-07 — Event-store recovery and restart safety

**Goal:** Restart safely without losing or duplicating critical state.

**Acceptance:**

- `S3-07-T01` complete: Recovery order documented.
- `S3-07-T02` complete: Idempotency state restored.
- `S3-07-T03` complete: State restores accurately.
- `S3-07-T04` complete: No duplicate fills.
- `S3-07-T05` complete: Unknown pending orders block/resolved.

### S3-08 — API and WebSocket hardening

**Goal:** Provide safe operational APIs.

**Acceptance:**

- `S3-08-T01` complete: No internal leaks.
- `S3-08-T02` complete: Duplicate command deterministic.
- `S3-08-T03` complete: Metadata present.
- `S3-08-T04` complete: Sensitive endpoints guarded.
- `S3-08-T05` complete: Schemas documented.

### S3-09 — Frontend operational console

**Goal:** Make operations visible and controllable.

**Acceptance:**

- `S3-09-T01` complete: Screens and data sources clear.
- `S3-09-T02` complete: API/WS-only state.
- `S3-09-T03` complete: No frontend state machine.
- `S3-09-T04` complete: Backend-derived data.
- `S3-09-T05` complete: Calls explicit APIs.

### S3-10 — Observability, audit, and incident workflows

**Goal:** Make live behavior traceable.

**Acceptance:**

- `S3-10-T01` complete: No secrets logged.
- `S3-10-T02` complete: Metrics registered/tested.
- `S3-10-T03` complete: Serializable.
- `S3-10-T04` complete: Covers key incidents.
- `S3-10-T05` complete: correlation_id preserved.

### S3-11 — Performance, load, and soak testing

**Goal:** Identify stability and throughput risks.

**Acceptance:**

- `S3-11-T01` complete: Scenarios documented.
- `S3-11-T02` complete: Deterministic output.
- `S3-11-T03` complete: Queue health exposed.
- `S3-11-T04` complete: Small scenario runs.
- `S3-11-T05` complete: Manual/slow target documented.

### S3-12 — Deployment, CI/CD, and secrets baseline

**Goal:** Make deployment repeatable and secrets safe.

**Acceptance:**

- `S3-12-T01` complete: CI includes required checks.
- `S3-12-T02` complete: No real credentials.
- `S3-12-T03` complete: Local path documented.
- `S3-12-T04` complete: Safe repeated runs.
- `S3-12-T05` complete: Safety gates documented.

### S3-13 — Live beta readiness review

**Goal:** Decide go/no-go for live beta.

**Acceptance:**

- `S3-13-T01` complete: Explicit criteria.
- `S3-13-T02` complete: Results recorded honestly.
- `S3-13-T03` complete: Missing soak blocks live beta.
- `S3-13-T04` complete: Owner/mitigation/expiry included.
- `S3-13-T05` complete: Approval required.
