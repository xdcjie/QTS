# QTS Runtime Readiness M5 Review Status Matrix

Source backlog: `docs/plan/qts_runtime_readiness_deep_review_tasks.md`

Scope: Milestone 5 - Simplicity, redundancy removal, and over-design control

Baseline: 2026-05-16, `HEAD 78a4e23`

## Completion Rules

M5 is complete only when runtime/backtest orchestration remains thin, coordinator classes have explicit retention value, duplicate runtime state models have boundary reasons, report naming matches broker-capable runtime semantics, and complexity evidence is enforced by tests or guardrails.

No alias, transitional import path, shadow report writer, or passive audit note may satisfy an acceptance condition. Any renamed or removed production API must be updated at call sites directly, with guardrails blocking reintroduction.

## Correctness Invariants

| Invariant | Correct owner or boundary | Forbidden shortcut | Required gate |
| --- | --- | --- | --- |
| `RuntimeSession` is an orchestrator facade, not a business-rule owner. | Runtime coordinators, actors, risk/order/safety owners, and complexity report gate. | Moving business decisions back into session just to reduce class count. | Complexity report plus unit guard for public methods, private helpers, file length, and method length. |
| Coordinators must earn their boundary. | Runtime lifecycle, market-data, safety, rollback, recovery, startup-gate owners. | Keeping pass-through classes with no state, boundary, or test value. | Candidate decision table and guard/test evidence for keep/merge/delete decisions. |
| Runtime/domain/API/reporting DTOs model distinct boundaries only. | Domain models, runtime results, adapter payloads, API/reporting schemas. | Maintaining two interchangeable production classes for the same runtime state. | Concept-map audit and focused tests/guardrails for centralized conversions. |
| Broker-capable runtime reports must not use live-capital wording for paper/broker modes. | Reporting package and manifest schema boundary. | Keeping live-only names or adding aliases to avoid updating imports. | Direct rename tests, import guard, and manifest assertions for runtime/account/execution environments. |
| `BacktestActorLoop` only drives replay/actor/event flow. | Backtest engine/dependencies, replay source, runtime event sink, artifact writer, capability/report boundaries. | Letting actor loop load catalogs, parse config, build datasets, or own report formats. | Cohesion guardrails, complexity report, and actor-loop tests with fakes only. |

## Status Matrix

| Task | Status | Current Evidence Candidates | Blocking Gaps | First Red Gate |
| --- | --- | --- | --- | --- |
| M5-1 RuntimeSession complexity audit and convergence | Implemented | `RuntimeSessionComplexityRule` measures facade size and method complexity. `docs/architecture/runtime_session_complexity.md` records the current report and method grouping. | None. | `tests/unit/scripts/test_verify_guardrails.py` fails when `RuntimeSession` exceeds thresholds without updated evidence. |
| M5-2 Thin coordinator delete/merge audit | Implemented | `RuntimeCoordinatorDecisionRule` requires an explicit decision table for recovery, rollback, startup gate, safety controller, broker lifecycle, and market data coordinator boundaries. | None. | Guardrail fails when a candidate coordinator lacks keep/merge/delete evidence or lacks a retained-boundary reason. |
| M5-3 Protocol / DTO / ValueObject duplicate modeling audit | Implemented | `docs/architecture/runtime_value_model_boundaries.md` maps runtime/reporting/API concepts. `WrittenRuntimeEvent` was removed; `LiveRuntimeEventSink.write()` returns shared `RuntimeEventWriteResult`. | None. | `tests/unit/architecture/test_runtime_value_model_boundaries.py` fails if a listed value object lacks owner, direction, conversion owner, and mirror decision. |
| M5-4 Report naming convergence | Implemented | `qts.reporting.broker_runtime` owns `BrokerRuntimeReportWriter` and `BrokerRuntimeReportManifest`; old report import/export names are blocked by guardrails and negative import tests. | None. | Report writer tests fail if broker-capable reports expose live-only naming or omit runtime/account/execution environment metadata. |
| M5-5 BacktestActorLoop complexity convergence | Implemented | `BacktestActorLoop` delegates broker-capability payload decisions to `qts.reporting.backtest`; `BACKTEST_ACTOR_LOOP_COHESION` blocks catalog/config/report ownership imports and private-helper growth. | None. | Guardrail fails if actor loop imports catalog/config parsing, report-writer ownership, or grows private helpers past the allowed boundary. |

## Parallel Execution Lanes

| Lane | Owner | Write Scope | Exit Evidence |
| --- | --- | --- | --- |
| A | Main agent | Matrix, cross-lane integration, graph refresh, full verification, final commit. | Matrix updated with actual evidence, repository gates passing, and clean worktree after commit. |
| B | Worker | M5-1 and M5-2 RuntimeSession/coordinator complexity and retention decisions. | Complexity report/gate and coordinator keep/merge/delete evidence with any scoped code changes. |
| C | Worker | M5-3 DTO/ValueObject concept map and conversion boundary cleanup. | Concept map, tests/guardrails for retained boundaries, and removal/merge of any unjustified mirror. |
| D | Worker | M5-4 report naming convergence. | Direct production rename, import guard, updated tests/docs, no alias. |
| E | Worker | M5-5 BacktestActorLoop complexity and cohesion. | Complexity/cohesion gate and scoped actor-loop boundary cleanup. |

## Verification Plan

Run focused checks first, then repository gates.

Focused evidence from this milestone:

```bash
uv run pytest tests/unit/scripts/test_verify_guardrails.py tests/unit/architecture/test_runtime_value_model_boundaries.py tests/unit/runtime/test_live_runtime_event_sink.py tests/unit/reporting/test_broker_runtime_report_writer.py tests/unit/reporting/test_reporting_contracts.py tests/unit/architecture/test_runtime_file_layout.py tests/unit/runtime/test_runtime_evolution_plan_acceptance.py tests/unit/backtest/test_backtest_actor_loop.py tests/integration/test_live_runtime_evidence_output.py tests/integration/test_ibkr_gateway_full_chain_anchor.py -q
# 113 passed, 1 skipped

uv run pytest tests/unit/test_backtest_live_parallel_sequence_html.py tests/unit/test_project_panorama_html.py -q
# 8 passed
```

Repository evidence:

```bash
make format
# 487 files left unchanged

make lint
# All checks passed

make guardrails
# Architecture guardrails passed

make typecheck
# Success: no issues found in 468 source files

make test-unit
# 730 passed

make test-integration
# 61 passed, 4 skipped

make test-anchor
# 39 passed, 1 skipped

make check
# format, lint, guardrails, typecheck, unit, integration, and anchor all passed
```

If a complexity threshold cannot be fully automated, M5 must include a generated review artifact and an explicit guard that fails on regression-prone imports or class reintroduction.
