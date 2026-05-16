# QTS Runtime Readiness M4 Review Status Matrix

Source backlog: `docs/plan/qts_runtime_readiness_deep_review_tasks.md`

Scope: Milestone 4 - Multi-strategy and multi-account parallel correctness

Baseline: 2026-05-16, `HEAD 55177b4`

## Completion Rules

M4 is complete only when order route metadata, account state mutation, broker route lookup, report topology, and signal aggregation decisions are account/strategy explicit and covered by enforceable tests.

No default account, implicit strategy ownership, route reconstruction, silent signal netting, or record-only audit event may satisfy an acceptance condition. Every route-sensitive runtime decision must either preserve the original metadata or fail closed.

## Correctness Invariants

| Invariant | Correct owner or boundary | Forbidden shortcut | Required gate |
| --- | --- | --- | --- |
| Submit/cancel/replace/fill must preserve account, strategy, broker route, and correlation identity. | `OrderRouteMetadata`, order manager/runtime routing, execution adapter, event writer. | Rebuilding route metadata from a symbol, broker ID, or current default account. | Route metadata invariant tests for submit, cancel, replace, fill, mismatch, and event correlation. |
| Account state is partitioned by `AccountId`; only matching-account fills and snapshots may mutate a partition. | `AccountActor`, account event routing, reconciliation snapshots, report manifest. | Applying fill/cash/position updates to the first or only configured account. | Account isolation suite covering fill, reservation, position snapshot, reconciliation snapshot, missing route, and report topology. |
| Broker route lookup must fail closed when the route is absent. | Event router / broker route registry boundary. | Falling back to a default broker route or account. | Missing route test expecting `RouteNotFoundError` or the local route lookup exception. |
| Signal aggregation must be deterministic and auditable by strategy contribution. | `SignalAggregatorActor` / runtime aggregation policy boundary. | Silently netting conflicting strategies without an explicit policy decision. | Policy tests for `SUM_TARGETS`, `PRIORITY_WINS`, `WEIGHTED_NET`, `REJECT_CONFLICT`, rejected strategies, contribution IDs, and deterministic decision hash. |
| Risk/order/report events must retain aggregation provenance. | `SignalAggregationDecision`, risk decision, order route metadata, runtime/report event payloads. | Losing contributing strategy IDs after aggregation. | Tests asserting `aggregation_decision_id` and `contributing_strategy_ids` on downstream risk/order/report evidence. |

## Status Matrix

| Task | Status | Current Evidence | Remaining Boundary | First Red Gate |
| --- | --- | --- | --- | --- |
| M4-1 OrderRouteMetadata invariant tests | Implemented | `tests/unit/runtime/test_order_manager_actor.py`, `tests/unit/runtime/test_execution_actor.py`, and route-flow integration tests cover explicit `OrderRouteMetadata` on submit/cancel/replace/fill, broker ID preservation, mismatch fail-fast, and correlation identity forwarding. `SubmitOrder`, `CancelOrder`, `ReplaceOrder`, and execution requests now carry route metadata instead of reconstructing route fields. | None for local route metadata invariants. Real broker-side correlation tracing remains external. | Replacing or cancelling Account A order retains Account A route metadata and never touches Account B. |
| M4-2 Account isolation suite | Implemented | `tests/unit/runtime/test_account_actor.py`, `tests/unit/runtime/test_runtime_session.py`, `tests/unit/runtime/test_broker_runtime_topology.py`, and `tests/unit/reporting/test_live_report_writer.py` cover account-scoped fill mutation, partitioned cash/position snapshots, partitioned recovery snapshots, missing broker route fail-fast under broker execution, and manifest account partition topology. | None for local runtime partition behavior. Real managed-account broker evidence remains external. | Account A fill does not update Account B cash, positions, or snapshots. |
| M4-3 Signal aggregation audit suite | Implemented | `tests/unit/runtime/test_signal_aggregator_actor.py` covers all aggregation policies and deterministic decision IDs. `tests/unit/runtime/test_runtime_session.py` asserts rejected strategy audit and downstream risk/order/report provenance via `aggregation_decision_id` and `contributing_strategy_ids`. | None for local policy/provenance behavior. | Conflicting strategy contributions are rejected unless the configured policy explicitly permits aggregation. |

## Parallel Execution Lanes

| Lane | Owner | Write Scope | Exit Evidence |
| --- | --- | --- | --- |
| A | Main agent | Matrix, cross-lane integration, graph refresh, full verification, final commit. | Status matrix updated with actual evidence, repository gates passing, and clean worktree after commit. |
| B | Worker | M4-1 route metadata invariants at runtime/order/execution boundaries. | Tests and implementation proving submit/cancel/replace/fill route metadata preservation and mismatch fail-fast behavior. |
| C | Worker | M4-2 account isolation and report partition topology. | Tests and implementation proving no account cross-mutation and route-missing fail-fast behavior. |
| D | Worker | M4-3 signal aggregation policy and audit provenance. | Tests and implementation proving deterministic aggregation decisions, rejection audit, and downstream provenance. |

## Verification Plan

Run focused tests first, then repository gates:

```bash
uv run pytest tests/unit/runtime tests/unit/execution tests/unit/reporting -q
make format
make lint
make guardrails
make typecheck
make test-unit
make test-integration
make test-anchor
make check
```

If real multi-account broker evidence is unavailable, M4 can only claim local runtime/account/signal correctness, not a live managed-account drill.

## Verification Evidence

Completed on 2026-05-16:

```bash
uv run pytest tests/unit/runtime tests/unit/execution tests/unit/reporting/test_live_report_writer.py tests/unit/backtest/test_backtest_actor_loop.py tests/unit/backtest/test_backtest_intent_processor.py tests/integration/test_bar_to_fill_flow.py tests/integration/test_backtest_live_parity_flow.py tests/integration/test_live_execution_report_flow.py tests/integration/test_ibkr_paper_flow.py -q
make format
make lint
make guardrails
make typecheck
make test-unit
make test-integration
make test-anchor
make check
```

Observed results:

- Focused M4 and nearby flow suite: 359 passed.
- Unit suite: 721 passed.
- Integration suite: 61 passed, 4 skipped.
- Anchor suite: 39 passed, 1 skipped.
- `make check`: passed.

External multi-account broker drills were not run in this workspace.
