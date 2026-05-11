# 2026-05-10 S3-02 Live Beta Fine-Grained Backlog

## Purpose

This backlog starts after `next_stage_fine_grained_backlog.md` is complete.

It is designed for one task per worker run.

## Naming

Task ID format:

```text
S3-<milestone>-T<task>
```

Plan file format:

```text
YYYY-MM-DD_<STAGE-ID>-<DOC-ID>_<name>.md
```

## How to execute

```text
Read AGENTS.md and docs/plan/2026-05-10_S3-02_live_beta_fine_grained_backlog.md.
Implement S3-00-T01 only. Add tests and run required checks.
```

## Verification rules

| Change type | Required checks |
|---|---|
| Local code only | `make format && make lint && make typecheck && make test-unit` |
| Runtime / API / broker / reconciliation / multi-module | add `make test-integration` |
| Financial correctness / accounting / order lifecycle / recovery / risk | add `make test-anchor` |
| Milestone completion | `make check` |


## S3-00 — Planning and baseline verification

| Task ID | Name | Goal | Deliverable | Verification | Acceptance |
|---|---|---|---|---|---|
| S3-00-T01 | Verify S2 baseline | Confirm repo health before S3 | Baseline report/checklist | `make check` | Passes or failures classified |
| S3-00-T02 | Create S3 status tracker | Track S3 tasks | Status table in docs/plan | `make format` | Tasks are trackable |
| S3-00-T03 | Review architecture boundaries | Find dependency/AGENTS violations | Review notes | `make lint` | Violations documented or absent |

## S3-01 — Broker adapter contracts

| Task ID | Name | Goal | Deliverable | Verification | Acceptance |
|---|---|---|---|---|---|
| S3-01-T01 | Broker capability model | Represent broker-supported features | Capability model | `make test-unit` | Capabilities typed and tested |
| S3-01-T02 | Broker adapter interface | Stable broker boundary | Interface and fake adapter | `make test-unit` | Fake adapter implements interface |
| S3-01-T03 | Execution report normalization | Normalize broker callbacks | Normalizer and tests | `make test-unit` | Vendor objects do not leak |
| S3-01-T04 | Broker contract tests | Reusable adapter tests | Contract test suite | `make test-unit` | Submit/cancel/fill cases covered |
| S3-01-T05 | Broker boundary docs | Document adapter rules | Execution docs update | `make format` | Boundary documented |

## S3-02 — Live market data adapters

| Task ID | Name | Goal | Deliverable | Verification | Acceptance |
|---|---|---|---|---|---|
| S3-02-T01 | Feed capability model | Represent feed features/limits | Capability model | `make test-unit` | Typed and tested |
| S3-02-T02 | Live feed interface | Stable feed boundary | Interface and fake feed | `make test-unit` | Fake feed implements interface |
| S3-02-T03 | Reconnect policy | Deterministic retry behavior | Policy object | `make test-unit` | Backoff tested |
| S3-02-T04 | Feed to aggregation pipeline | Route live feed through session/bar pipeline | Integration flow | `make test-integration` | Timeframe-aware BarEvents emitted |
| S3-02-T05 | Feed contract tests | Reusable feed adapter tests | Contract tests | `make test-unit` | Subscribe/emit/failure covered |

## S3-03 — Reconciliation engine

| Task ID | Name | Goal | Deliverable | Verification | Acceptance |
|---|---|---|---|---|---|
| S3-03-T01 | Snapshot models | Model internal/broker snapshots | Snapshot dataclasses | `make test-unit` | Typed and immutable where practical |
| S3-03-T02 | Order reconciliation | Detect order drift | Comparator and report | `make test-unit` | Missing/extra/divergent orders classified |
| S3-03-T03 | Position/cash reconciliation | Detect account drift | Comparator and report | `make test-unit` | Drift classified with tolerance |
| S3-03-T04 | Reconciliation report | Structured audit output | Report model | `make test-unit` | Serializable and deterministic |
| S3-03-T05 | Reconciliation integration | Validate runtime reconciliation flow | Integration test | `make test-integration` | Drift event emitted without direct mutation |

## S3-04 — Live runtime orchestration

| Task ID | Name | Goal | Deliverable | Verification | Acceptance |
|---|---|---|---|---|---|
| S3-04-T01 | Runtime lifecycle states | Model live runtime states | Lifecycle state machine | `make test-unit` | Illegal transitions fail |
| S3-04-T02 | Live runtime skeleton | Wire fake feed/broker/strategy flow | LiveRuntime service | `make test-integration` | Start/stop with fakes |
| S3-04-T03 | Pause/resume | Block new order flow when paused | Runtime controls | `make test-integration` | Pause/resume behavior tested |
| S3-04-T04 | Degraded mode | Enter degraded on health failure | Health transition | `make test-integration` | Degraded state observable |
| S3-04-T05 | Runtime startup docs | Document startup/recovery order | Docs update | `make format` | Startup flow documented |

## S3-05 — Risk controls and kill-switches

| Task ID | Name | Goal | Deliverable | Verification | Acceptance |
|---|---|---|---|---|---|
| S3-05-T01 | Kill-switch model | Model global/account/strategy/broker halts | Domain model | `make test-unit` | Auditable states tested |
| S3-05-T02 | Global halt enforcement | Block all new live orders | Risk enforcement | `make test-unit` | Rejection reason explicit |
| S3-05-T03 | Account halt enforcement | Block one account only | Account-level enforcement | `make test-integration` | Other accounts unaffected |
| S3-05-T04 | Strategy halt enforcement | Block one strategy only | Strategy-level enforcement | `make test-integration` | Other strategies unaffected |
| S3-05-T05 | Kill-switch API | Operational command API | API endpoints | `make test-integration` | Activate/deactivate/read tested |
| S3-05-T06 | Kill-switch UI stub | Operational control surface | UI stub/docs | `make lint` | Uses backend API only |

## S3-06 — Multi-account live partitioning

| Task ID | Name | Goal | Deliverable | Verification | Acceptance |
|---|---|---|---|---|---|
| S3-06-T01 | Account partition policy | Route by account_id | Router rule/tests | `make test-unit` | Correct partitioning |
| S3-06-T02 | Account broker mapping | Map internal account to broker account | Mapping model | `make test-unit` | Broker IDs boundary-only |
| S3-06-T03 | Account risk config | Per-account risk config | Config model/load | `make test-unit` | Different limits enforced |
| S3-06-T04 | Multi-account flow | Prove account isolation | Integration test | `make test-integration` | No state leakage |
| S3-06-T05 | Per-account reconciliation | Reconcile by account partition | Integration test | `make test-integration` | Drift isolated by account |

## S3-07 — Event-store recovery and restart safety

| Task ID | Name | Goal | Deliverable | Verification | Acceptance |
|---|---|---|---|---|---|
| S3-07-T01 | Recovery source-of-truth doc | Define replay/snapshot/broker precedence | Docs update | `make format` | Recovery order documented |
| S3-07-T02 | Order snapshot/restore | Restore OrderManager state | Snapshot logic | `make test-unit` | Idempotency state restored |
| S3-07-T03 | Account snapshot/restore | Restore account/portfolio state | Snapshot logic | `make test-unit` | State restores accurately |
| S3-07-T04 | Replay bootstrap | Snapshot + replay + reconcile | Bootstrap flow | `make test-integration` | No duplicate fills |
| S3-07-T05 | Pending order recovery | Gate trading until broker reconciliation | Recovery gate | `make test-integration` | Unknown pending orders block/resolved |

## S3-08 — API and WebSocket hardening

| Task ID | Name | Goal | Deliverable | Verification | Acceptance |
|---|---|---|---|---|---|
| S3-08-T01 | API error model | Stable operational errors | Error schema | `make test-unit` | No internal leaks |
| S3-08-T02 | Command idempotency | Prevent duplicate commands | Idempotency key support | `make test-integration` | Duplicate command deterministic |
| S3-08-T03 | WebSocket metadata | Add event/order metadata | Stream schema | `make test-integration` | Metadata present |
| S3-08-T04 | Permission hooks | Add auth/permission hook layer | Dependency/hooks | `make test-integration` | Sensitive endpoints guarded |
| S3-08-T05 | Operational API docs | Document status/risk/reconcile/control APIs | Docs update | `make format` | Schemas documented |

## S3-09 — Frontend operational console

| Task ID | Name | Goal | Deliverable | Verification | Acceptance |
|---|---|---|---|---|---|
| S3-09-T01 | Frontend IA | Define operational screens | Docs update | `make format` | Screens and data sources clear |
| S3-09-T02 | Runtime status view | Show runtime/health | UI view | `make lint` | API/WS-only state |
| S3-09-T03 | Order blotter view | Show orders/fills | UI view | `make lint` | No frontend state machine |
| S3-09-T04 | Risk events view | Show risk/kill-switch | UI view | `make lint` | Backend-derived data |
| S3-09-T05 | Operational controls view | Pause/resume/kill-switch controls | UI view | `make lint` | Calls explicit APIs |

## S3-10 — Observability, audit, and incident workflows

| Task ID | Name | Goal | Deliverable | Verification | Acceptance |
|---|---|---|---|---|---|
| S3-10-T01 | Structured logging fields | Standard log metadata | Logging helper | `make test-unit` | No secrets logged |
| S3-10-T02 | Core metrics | Queue/feed/broker/risk metrics | Metrics helper | `make test-unit` | Metrics registered/tested |
| S3-10-T03 | Audit event model | Immutable audit events | Audit model | `make test-unit` | Serializable |
| S3-10-T04 | Incident runbook | Operational triage docs | Runbook | `make format` | Covers key incidents |
| S3-10-T05 | End-to-end trace | Trace order lifecycle | Integration test | `make test-integration` | correlation_id preserved |

## S3-11 — Performance, load, and soak testing

| Task ID | Name | Goal | Deliverable | Verification | Acceptance |
|---|---|---|---|---|---|
| S3-11-T01 | Load test scenarios | Define throughput targets | Docs update | `make format` | Scenarios documented |
| S3-11-T02 | Synthetic market data generator | Deterministic load input | Generator | `make test-unit` | Deterministic output |
| S3-11-T03 | Queue health instrumentation | Measure depth/lag | Metrics | `make test-unit` | Queue health exposed |
| S3-11-T04 | Load test command | Runnable small load test | Script/Make target | `make test-unit` | Small scenario runs |
| S3-11-T05 | Soak test command | Long-run stability scenario | Script/docs | `make format` | Manual/slow target documented |

## S3-12 — Deployment, CI/CD, and secrets baseline

| Task ID | Name | Goal | Deliverable | Verification | Acceptance |
|---|---|---|---|---|---|
| S3-12-T01 | CI workflow plan | Define CI checks | Workflow/docs | `make format` | CI includes required checks |
| S3-12-T02 | Safe config examples | Ensure no secrets committed | .env.example/configs | `make lint` | No real credentials |
| S3-12-T03 | Docker local baseline | Run API/worker locally | Docker docs/config | `make format` | Local path documented |
| S3-12-T04 | Bootstrap scripts | Idempotent local bootstrap | Script/tests | `make test-unit` | Safe repeated runs |
| S3-12-T05 | Deployment profiles | Document local/backtest/paper/live-beta | Docs update | `make format` | Safety gates documented |

## S3-13 — Live beta readiness review

| Task ID | Name | Goal | Deliverable | Verification | Acceptance |
|---|---|---|---|---|---|
| S3-13-T01 | Readiness checklist | Define go/no-go checklist | Checklist doc | `make format` | Explicit criteria |
| S3-13-T02 | Test evidence collection | Record latest evidence | Evidence doc | `make check` | Results recorded honestly |
| S3-13-T03 | Paper soak gate | Require paper soak before live beta | Gate doc/result | `make format` | Missing soak blocks live beta |
| S3-13-T04 | Risk exception log | Track accepted deviations | Exception log | `make format` | Owner/mitigation/expiry included |
| S3-13-T05 | Go/no-go document | Final live beta decision artifact | Decision doc/template | `make format` | Approval required |
