# QTS vs Lean P1 Frontend and DX Review Status Matrix

Source backlog: `docs/plan/2026-05-17_qts_vs_lean_platform_gap_and_optimization_backlog.md`

Scope: P1 — Frontend and DX, OPT-12 through OPT-14.

Baseline: 2026-05-17, `HEAD $(git rev-parse --short HEAD)`

## Completion Rules

P1 Frontend and DX is complete only when `OPT-12` through `OPT-14` are closed with hard evidence in this repository:

- all public API/WS DTOs are generated or mapped from backend contracts, and hand-written interface drift is removed;
- WebSocket runtime is resumable and observable under reorder/drop conditions;
- high-value UI paths have unit logic tests and a Playwright smoke baseline per route.

No legacy schema path, no compatibility wrapper, and no historical debt may be used to satisfy any acceptance condition.

## P1 Frontend and DX Correctness Invariants

| Invariant | Correct owner or boundary | Forbidden shortcut | Required gate |
| --- | --- | --- | --- |
| HTTP DTO contracts come from the live backend OpenAPI contract, not duplicated local interfaces. | Backend `qts.api` schema/mappers and frontend generated SDK boundary. | Maintaining hand-written DTOs in `frontend/src/api/` and using `axios.get<T>` casts without generated types. | `tests/unit/docs/test_qts_vs_lean_p1_frontend_dx_review_status_matrix.py`, OpenAPI diff checks, and runtime compile gate. |
| WebSocket consumer must detect gaps and support bounded replay semantics under reconnect. | Frontend WS client wrapper and backend `/ws/events` event envelope contract. | Reconnect loop without sequence checks, silent message drops, or ad-hoc local buffering. | Unit test for sequence gap handling plus WS smoke tests with synthetic stream assertions. |
| Frontend route/state behavior remains backend-driven and test-covered. | Frontend hooks/services/components. | Mocking backend responses with synthetic static strings while ignoring backend contract. | `vitest` suite for critical components + Playwright smoke for each main route (`Dashboard`, `BacktestLab`, `StrategyManagement`, `Operations`). |

## Status Matrix

| Task | Status | Evidence Candidates | Blocking Gaps | First Red Gate |
| --- | --- | --- | --- | --- |
| OPT-12 OpenAPI -> TS types pipeline | DONE | `backend/scripts/generate_openapi_json.py`, `frontend/openapi.json`, `frontend/src/api/types.gen.ts`, `frontend/src/api/http.ts`, `frontend/src/models/index.ts`, `frontend/package.json` build scripts. | None. | OpenAPI generation test expects generated `types.gen.ts` to expose `components.schemas.StrategyStatusSchema` and route response aliases. |
| OPT-13 Frontend test baseline (vitest + Playwright smoke) | DONE | `frontend/vitest.config.ts`, `frontend/playwright.config.ts`, `frontend/tests/components/BacktestLab.spec.tsx`, `frontend/tests/e2e/smoke.spec.ts`, `frontend/tests/ws/stream-client.spec.ts`. | None currently. | `frontend/tests/components/BacktestLab.spec.tsx` and `frontend/tests/e2e/smoke.spec.ts` first-pass compile. |
| OPT-14 WebSocket client robustness | DONE | `backend/src/qts/api/websocket/events.py`, `frontend/src/hooks/useMetricsWS.ts`, `frontend/src/ws/stream-client.ts`, `frontend/tests/ws/stream-client.spec.ts`, `tests/integration/test_websocket_smoke.py`. | Existing `/ws/events` emits only synthetic connect event was replaced by envelope-based bootstrap + replay. | Unit test where sequence gap is detected and replay request is sent. |

## Execution Lanes

| Lane | Write Scope | Exit Evidence |
| --- | --- | --- |
| A | Matrix + backlog links, evidence mapping, verification gates, docs updates | Matrix and backlog keep only current source-of-truth paths. |
| B | Frontend API type generation and public API client service ownership | OpenAPI generation can run without hand-coded DTOs and all callers compile with generated types. |
| C | WebSocket robustness and stream client abstraction | Reconnect/replay behavior proven by unit tests and backend envelope support. |
| D | Frontend baseline tests + Playwright smoke | At least one smoke spec per route in matrix, plus component-level unit coverage on key UI logic. |

## Verification Plan

Run matrix gate first:

```bash
PYTHONPATH=backend/src uv run pytest tests/unit/docs/test_qts_vs_lean_p1_frontend_dx_review_status_matrix.py -q
```

Focused gates for implementation:

```bash
cd frontend
npm install
npm run gen:openapi
cd /Users/bjhl/Projects/QTS
PYTHONPATH=backend/src uv run python scripts/generate_openapi_json.py --output frontend/openapi.json
cd frontend
npm run test:unit
npm run test:e2e
```

Optional frontend static/type gate:

```bash
cd frontend
npm run build
```

## Verification Log

Initial matrix setup:

```bash
PYTHONPATH=backend/src uv run pytest tests/unit/docs/test_qts_vs_lean_p1_frontend_dx_review_status_matrix.py -q
# initial run (before completion) expected fail while matrix did not exist
```

Post-completion hard evidence:

```bash
cd /Users/bjhl/Projects/QTS
PYTHONPATH=backend/src uv run pytest tests/unit/docs/test_qts_vs_lean_p1_frontend_dx_review_status_matrix.py -q
# 1 passed
PYTHONPATH=backend/src uv run pytest tests/integration/test_websocket_smoke.py -q
# 2 passed
cd frontend
PYTHONPATH=backend/src uv run python scripts/generate_openapi_json.py --output frontend/openapi.json
npm run gen:openapi
test -f frontend/src/api/types.gen.ts
npm run test:unit
# 3 passed (2 vitest suites, 3 tests total)
npm run test:e2e
# 4 passed (Dashboard, Strategies, BacktestLab, Operations smoke routes)
```
