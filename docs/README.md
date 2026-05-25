# Documentation Guide

Recommended reading order:

1. `../README.md`
2. `../AGENTS.md`
3. `plan/implementation_plan.md`
4. `plan/milestones_and_acceptance.md`
5. `architecture/system_overview.md`
6. `architecture/dependency_rules.md`
7. `architecture/module_boundaries.md`
8. `architecture/naming.md`
9. `domain/instrument_model.md`
10. `domain/market_calendar_and_sessions.md`
11. `domain/bar_timeframe_model.md`
12. `runtime/actor_model.md`
13. `strategy_sdk/strategy_api.md`
14. `testing/testing_strategy.md`
15. `testing/domain_invariants.md`
16. ADRs under `adr/`

## Planning documents

- `plan/implementation_plan.md` defines the phase-by-phase build order.
- `plan/milestones_and_acceptance.md` defines deliverables, checks, and acceptance criteria for each milestone.

Legacy monolithic docs are intentionally not used. This folder is organized by architecture layer.

## Directory boundaries

Use existing documentation directories before adding new ones:

- `adr/`: accepted architecture decisions with durable rationale. Add a new ADR only for a
  decision that changes architecture direction or constrains future choices.
- `api/`: external API contracts, auth, REST, WebSocket, and request/response behavior.
- `architecture/`: cross-cutting system structure, dependency rules, mode parity, runtime
  flows, deployment topology, and review checklists.
- `broker/`: broker-specific adapter decisions and broker capability notes.
- `decision/`: dated go/no-go decisions, project decisions, and operational decision records
  that are not durable ADRs.
- `domain/`: financial domain models and correctness rules such as instruments, sessions,
  bars, orders, portfolio accounting, and risk semantics.
- `frontend/`: frontend product and console design.
- `infra/`: CI, deployment, configuration, database, observability, rollback, and
  infrastructure incident material.
- `operations/`: runbooks, readiness checklists, live/paper operating procedures, evidence,
  and rollout/soak plans.
- `plan/`: implementation plans, milestone plans, acceptance matrices, backlogs, gap
  analyses, and status reports.
- `research/`: Research OS contracts, factor discovery/evaluation protocols,
  experiment evidence rules, subagent work-package templates, and promotion
  boundaries for moving reviewed evidence toward paper/live consideration.
- `runtime/`: actor model, router, scheduler, clock, recovery, and runtime lifecycle rules.
- `strategy_sdk/`: user-facing strategy API, data views, indicators, factors, and examples.
- `testing/`: testing strategy, anchor-test policy, domain invariants, and integration-flow
  expectations.

## Adding documentation directories

Add a new top-level docs directory only when all of these are true:

- The content has a stable project concept not covered by an existing directory.
- More than one document is expected to live there over time.
- The directory boundary can be described in one sentence and added to this file.
- The name is domain or project specific, not tool or workflow specific.

Do not add agent/tool/process directories such as `superpowers`, `codex`,
`claude`, or temporary scratch/spec folders under `docs/`. Agent-generated
plans or specs must either update the relevant long-lived docs above or remain
outside committed project documentation.
