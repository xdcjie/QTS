# Research Dashboard Acceptance

Phase 8 exposes completed research evidence through read-only API and frontend
surfaces. The dashboard does not start research workflows, approve promotion, or
mutate trading/runtime state.

## Flow Gates

| Flow | Dashboard behavior | Gate |
| --- | --- | --- |
| `FLOW-RESEARCH` | Lists indexed experiment runs from `ExperimentStore` and manifest-driven artifact runs from `artifacts/research/index.jsonl`, then filters by strategy, idea, and status. | API tests create both registry types and verify filtered results. |
| `FLOW-REPORTING` | Shows evidence reports from `EvidenceRegistry` and reads bounded markdown previews from completed report files. | API tests verify report metadata and preview rendering. |
| `FLOW-PROMOTION` | Displays review decisions, promotion candidate specs, readiness gate records, and lifecycle status. | API tests verify all decision sources are visible and remain read-only. |

## Acceptance Coverage

- Research runs can be listed and filtered through
  `GET /backtests/research/runs`.
- Reports are viewable through `GET /backtests/research/reports` and
  `GET /backtests/research/reports/{evidence_bundle_id}`.
- Promotion decisions are viewable through
  `GET /backtests/research/promotion-decisions`.
- Strategy lifecycle status is visible through
  `GET /backtests/research/lifecycle`.
- Run comparison is available through `GET /backtests/research/compare`.

## Evidence

Focused backend acceptance:

```bash
PYTHONPATH=backend/src QTS_API_DEV_TOKENS=1 uv run pytest tests/unit/api/test_research_routes.py
```

Frontend acceptance target:

```bash
cd frontend
npm run test:unit -- ResearchDashboard.spec.tsx
```

The frontend test covers the dashboard loading runs, reports, lifecycle status,
promotion decisions, strategy filtering, report preview, and run comparison.
