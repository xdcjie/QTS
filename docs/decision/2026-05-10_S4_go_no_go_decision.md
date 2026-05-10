# 2026-05-10 S4 Go/No-Go Decision

## Current Status

Decision: No-Go

S4 is not approved for real production capital. Local readiness evidence exists, but production approval requires recorded external evidence from the target broker environment, operator signoff, paper or observation soak, reconciliation review, and rollback drill completion.

## Decision Levels

| Level | Meaning | Required evidence | Current status |
|---|---|---|---|
| G0 | No-Go | Missing or incomplete local verification, readiness evidence, or safety controls | Active decision |
| G1 | Local readiness candidate | `make check` passes and S4 readiness lanes are defined | Partially satisfied |
| G2 | Paper or observation readiness candidate | Full-session paper or observation soak with metrics, no unexplained drift, and operator-visible reconciliation | Not satisfied |
| G3 | Live environment readiness candidate | Target IBKR TWS/Gateway connectivity, permissions, market data, order execution boundaries, and startup guards validated without live capital | Not satisfied |
| G4 | Small-capital rollout candidate | Risk owner approval, production-specific limits, rollback readiness, and accepted reconciliation state | Not satisfied |
| G5 | Production Go | Engineering, operations, and risk signoff with complete rollout checklist and no open live-blocking items | Not satisfied |

## Evidence Table

| Area | Evidence recorded | Source | Decision impact |
|---|---|---|---|
| Baseline verification | `make check` passed on 2026-05-10 with 133 unit, 20 integration, and 19 anchor tests after format, lint, and mypy | `docs/plan/status/S4_production_ready_status.md` | Supports G1 only |
| Replay lane | S4 replay verification lane exists as `make test-replay` | `docs/plan/S4_final_readiness_report.md` | Supports local determinism evidence |
| Reconciliation lane | S4 reconciliation verification lane exists as `make test-reconciliation` | `docs/plan/S4_final_readiness_report.md` | Necessary, but live broker reconciliation evidence is still required |
| Soak lane | S4 soak documentation lane exists as `make test-soak` | `docs/plan/S4_final_readiness_report.md` | Necessary, but real paper or observation soak evidence is still required |
| Live startup safety | Live startup guard and observation-mode order-submission block are recorded | `docs/plan/status/S4_production_ready_status.md` | Supports safety posture but does not approve live capital |
| Broker capability modeling | Order type, time-in-force, fractional, and short capability model are recorded | `docs/plan/status/S4_production_ready_status.md` | Supports broker-boundary readiness |
| Rollout checklist | Production rollout requires observation mode, paper-vs-live review, reconciliation review, risk approval, kill-switch drill, rollback review, and capital limits | `docs/operations/production_rollout_checklist.md` | Blocks G4 and G5 until complete |
| Soak requirements | Production soak requires at least one full regular trading session and success metrics for event lag, stale data, broker status, rejected orders, memory growth, and drift | `docs/operations/production_soak_plan.md` | Blocks G2 until recorded |
| Paper-vs-live comparison | Unexplained differences block production readiness | `docs/operations/paper_vs_live_comparison.md` | Blocks G4 and G5 until reviewed |
| ADR decision | S4 records No-Go until external live-readiness evidence is complete | `docs/adr/0007-production-readiness-decision.md` | Confirms current No-Go |

## Required To Change Decision

The decision may move out of No-Go only after all of the following are recorded:

- Target IBKR environment validation, including TWS/Gateway connectivity, account permissions, market data behavior, and adapter boundary behavior.
- Paper or observation-mode soak evidence for the target instrument set and strategy set.
- Clean or formally accepted reconciliation status.
- Completed rollback and kill-switch drill evidence.
- Engineering owner, operations owner, and risk owner signoff.
- Completed production rollout checklist with no open live-blocking items.

Until those records exist, the S4 decision remains No-Go.
