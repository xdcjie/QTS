# QTS Runtime Readiness M6 Review Status Matrix

Source backlog: `docs/plan/qts_runtime_readiness_deep_review_tasks.md`

Scope: Milestone 6 - Manifest, durability, and operator observability

Baseline: 2026-05-16, `HEAD 43b74b6`

## Completion Rules

M6 is complete only when runtime artifacts have one canonical manifest contract,
recovery evidence proves durable replay gates, operator state is available
through application DTOs, and readiness smokes are executable gates.

No alias, transitional import path, shadow schema, or passive checklist may
satisfy an acceptance condition. Removed or renamed production APIs must be
updated at call sites directly, with tests or guardrails blocking reintroduction.

## Correctness Invariants

| Invariant | Correct owner or boundary | Forbidden shortcut | Required gate |
| --- | --- | --- | --- |
| Backtest, paper, and broker runtime reports share one manifest base contract. | `qts.reporting.base.RuntimeManifest` plus report writers. | Adding mode-specific required-field mirrors or optionalizing required evidence. | Missing-field failure tests, deterministic hash tests, and query tests. |
| Recovery cannot resume order submission from durable state alone. | Event store, snapshot store, recovery decision, and reconciliation boundary. | Treating a snapshot load as permission to trade before reconciliation. | Gap, schema-version, state equality, and reconciliation-block tests. |
| Operator state is a public application DTO, not actor internals. | Application service DTOs and API/WebSocket boundary. | Returning actor objects, mutable stores, or runtime event envelopes directly. | DTO field/timestamp tests and alert-state tests. |
| Readiness smokes are executable gates with run identity evidence. | Test matrix, local CI target, and external/nightly boundary docs. | Keeping a smoke list as plain text or mixing external broker tests into local CI. | Local smoke tests, external marker coverage, and artifact/run id assertions. |

## Status Matrix

| Task | Status | Current Evidence Candidates | Blocking Gaps | First Red Gate |
| --- | --- | --- | --- | --- |
| M6-1 RuntimeManifest canonical schema | Implemented | `RuntimeManifest` now owns canonical required fields, deterministic `manifest_hash`, and `RuntimeManifestRecord.load/query`. Backtest and broker runtime writers validate through the same base. | None. | Reporting tests fail when required fields are missing or `manifest_hash` does not match canonical payload. |
| M6-2 Event store / snapshot store durability drill | Implemented | `RuntimeDurabilityDrill` writes events/snapshots, simulates restart, validates sequence continuity, loads latest snapshots, replays post-snapshot events, compares state, and requires reconciliation before live order submission. | None. | Durability tests fail on event sequence gaps, snapshot schema mismatch, recovered-state mismatch, or missing reconciliation. |
| M6-3 Operator dashboard minimal state panel | Implemented | `OperatorDashboardStatusDTO` and `GET /operations/operator-status` expose timestamped application-owned fields and explicit stale data, reconciliation drift, and unresolved callback alerts. | None. | Service/API tests fail if fields lack timestamps, actor internals leak, or alert states are not surfaced. |
| M6-4 Readiness smoke matrix | Implemented | `docs/testing/readiness_smoke_matrix.md`, `readiness-smoke-local`, `readiness-smoke-external`, local smoke tests, and external marker coverage encode the named matrix. | None. | Local smoke tests fail if manifest/event artifacts, `run_id`, or required `correlation_id` evidence is missing. |

## Parallel Execution Lanes

| Lane | Owner | Write Scope | Exit Evidence |
| --- | --- | --- | --- |
| A | Main agent | Matrix, cross-lane integration, graph refresh, full verification, final commit. | Matrix updated with actual evidence, repository gates passing, and clean worktree after commit. |
| B | Worker | M6-1 manifest schema/report query path. | Shared manifest base, writer tests, deterministic hash tests, and direct query tests. |
| C | Worker | M6-2 durability and recovery drill. | Recovery drill tests proving gap/schema blockers, state restoration, and reconciliation-required order gate. |
| D | Worker | M6-3 operator DTO/dashboard state. | Application DTO/service tests with timestamped fields and explicit alerts. |
| E | Worker | M6-4 readiness smoke matrix. | Local smoke tests, external marker documentation/tests, and artifact identity assertions. |

## Verification Plan

Run focused checks first, then repository gates.

Focused evidence from this milestone:

```bash
uv run pytest tests/unit/reporting tests/unit/application/test_services.py tests/unit/api/test_routes.py tests/integration/test_runtime_durability_recovery.py tests/integration/test_readiness_smoke_matrix.py tests/anchor/test_readiness_smoke_matrix_external.py -q
# 46 passed, 1 skipped

make readiness-smoke-local
# 9 passed

uv run pytest tests/anchor/test_readiness_smoke_matrix_external.py -q -m external
# 1 skipped without external evidence
```

Repository evidence:

```bash
make format
# 1 file reformatted, then clean on final run

make lint
# All checks passed

make guardrails
# Architecture guardrails passed

make typecheck
# Success: no issues found in 472 source files

make test-unit
# 736 passed

make test-integration
# 75 passed, 4 skipped

make test-anchor
# 39 passed, 2 skipped

make check
```

If a live or external broker smoke cannot run locally, M6 must include an
explicit marker and a local test proving it is excluded from CI but present in
the nightly/external matrix.
