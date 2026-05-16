# QTS Runtime Readiness M3 Review Status Matrix

Source backlog: `docs/plan/qts_runtime_readiness_deep_review_tasks.md`

Scope: Milestone 3 - IBKR Robustness and Broker Failure Drill

Baseline: 2026-05-16, `HEAD bf2622c`

## Completion Rules

M3 is complete only when IBKR callback duplication, ordering variance, durable order-map restore, transport responsibility boundaries, and managed-account mismatches are fail-closed and covered by explicit tests.

No compatibility wrapper, shadow callback path, direct state mutation bypass, or record-only quarantine may satisfy an acceptance condition. Every broker callback safety decision must either update the owned broker/order boundary exactly once or enter quarantine with structured evidence.

## Correctness Invariants

| Invariant | Correct owner or boundary | Forbidden shortcut | Required gate |
| --- | --- | --- | --- |
| IBKR callbacks are at-least-once and may be duplicated, late, or out of order; fills and commissions must be idempotent. | IBKR execution adapter, callback dispatcher, fill idempotency store, broker order map. | Applying a fill twice because callbacks arrive twice or commission arrives late. | Callback ordering/idempotency tests for duplicate orderStatus, execution, commission, late cancel, missing permId, and wrong account. |
| Broker order identity must survive process restart. | `BrokerOrderMap` snapshot/restore boundary. | Reconstructing indexes from incomplete payloads or silently accepting missing client order identity. | Durable restore tests for client order ID, internal order ID, IBKR order ID, permId, deterministic snapshot hash, and fail-fast invalid payload. |
| IBKR transport split must keep responsibilities separated. | Transport connection/client/dispatcher/emitter/facade classes and guardrails. | Letting connection produce domain reports, order client handle callbacks, dispatcher submit orders, or facade hold duplicate business state. | Contract tests plus guardrail checks for transport/adapters path mixing. |
| Managed account mismatch must never mutate local account state. | IBKR order execution adapter, route metadata, callback quarantine, runtime event boundary. | Updating `BrokerOrderMap`, account snapshots, or fills before validating callback account ownership. | Wrong-account execution/position/account summary tests and live resume blocker for unresolved quarantine. |
| Account evidence must be audit-useful but non-sensitive. | Quarantine and runtime event payload serialization. | Emitting full sensitive account identifiers in event payloads. | Masked account-code assertion in mismatch event tests. |

## Status Matrix

| Task | Status | Current Evidence | Remaining Boundary | First Red Gate |
| --- | --- | --- | --- | --- |
| M3-1 IBKR callback idempotency / ordering suite | Implemented with simulated callback coverage | `tests/unit/execution/test_ibkr_order_execution_adapter.py` covers duplicate execution, duplicate/late commission, partial fills, late cancel after fill, out-of-order `openOrder` / `execDetails`, unresolved quarantine replay, and resume blocking through unresolved callback validation. | Real TWS callback timing drill remains external and is not claimed by this matrix. | Duplicate execution and late commission apply one fill and update fees only once. |
| M3-2 BrokerOrderMap durable restore suite | Implemented | `tests/unit/execution/test_ibkr_order_map.py` covers pending/submitted/filled/cancelled restore records, client/internal/IBKR/permId lookup indexes, deterministic `snapshot_hash()`, post-restore callback ownership, missing `client_order_id`, and ambiguous broker identity fail-fast behavior. | None for local durable restore semantics. External persistence media is outside this milestone. | Restored map resolves by client/internal/IBKR/permId with identical ownership. |
| M3-3 IBKR transport split contract tests | Implemented | `tests/unit/execution/test_ibkr_order_execution_transport.py`, `tests/unit/execution/test_ibkr_async_order_execution_transport.py`, and `tests/unit/scripts/test_verify_guardrails.py` cover connection/client/dispatcher/emitter/facade responsibility split plus the transport-to-adapter import guardrail. | None for static/source contract coverage. Real TWS socket behavior remains covered by existing opt-in anchors when credentials are present. | Static/source tests fail if connection creates domain reports, order client handles callbacks, dispatcher submits orders, or transport modules import adapter paths. |
| M3-4 Managed account mismatch quarantine | Implemented with simulated callback coverage | `tests/unit/execution/test_ibkr_order_execution_adapter.py` covers wrong-account execution, position, and account summary quarantine; no order map/fill/account snapshot mutation; masked runtime-event evidence; and unresolved quarantine blocking live resume. | Real managed-account mismatch drill requires broker/TWS environment and is not claimed here. | Wrong-account execution does not update order map or fills and blocks live resume while unresolved. |

## Parallel Execution Lanes

| Lane | Owner | Write Scope | Exit Evidence |
| --- | --- | --- | --- |
| A | Main agent | Matrix, integration, cross-lane review, graph refresh, final commit. | Matrix updated with actual evidence, full repo gates passing, and no direct bypass left open. |
| B | Worker | M3-1 and M3-4 callback idempotency/quarantine at adapter boundary. | Tests and implementation for duplicate/out-of-order/wrong-account callbacks and live resume quarantine blocking. |
| C | Worker | M3-2 `BrokerOrderMap` durable restore. | Tests and implementation for snapshot/restore, indexes, deterministic hash, and fail-fast payload validation. |
| D | Worker | M3-3 transport split contracts and guardrails. | Tests and guardrails proving connection/client/dispatcher/emitter/facade responsibilities remain separated. |

## Verification Plan

Focused tests first, then repository gates:

```bash
uv run pytest tests/unit/execution/test_ibkr_order_execution_adapter.py tests/unit/execution/test_ibkr_order_execution_transport.py tests/unit/execution/test_ibkr_order_map.py tests/unit/scripts/test_verify_guardrails.py -q
make format
make lint
make guardrails
make typecheck
make test-unit
make test-integration
make test-anchor
make check
```

If live IBKR/TWS evidence is unavailable, M3 can only claim simulated callback and transport-contract coverage, not a real broker failure drill.

## Verification Evidence

Completed on 2026-05-16:

```bash
uv run pytest tests/unit/execution/test_ibkr_order_execution_adapter.py tests/unit/execution/test_ibkr_order_execution_transport.py tests/unit/execution/test_ibkr_async_order_execution_transport.py tests/unit/execution/test_ibkr_order_map.py tests/unit/scripts/test_verify_guardrails.py -q
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

- Focused M3 suite: 103 passed.
- Unit suite: 713 passed.
- Integration suite: 61 passed, 4 skipped.
- Anchor suite: 39 passed, 1 skipped.
- `make check`: passed.

External IBKR/TWS broker failure drills were not run in this workspace.
