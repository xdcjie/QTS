# Research Workflow Report

workflow_id: orb-vwap-trend-gc-target3-single
workflow_status: completed

## Evidence Header
- Workflow config: configs/research/workflows/orb_vwap_trend_gc_target3_single.yaml
- Workflow config hash: sha256:b41016a1fb38b08042278a8d5257d53914e5f11a997131dfcfb26d693fc64d64
- Research config: configs/research/orb_vwap_trend_gc_si_long.yaml
- Research config hash: sha256:3a1404759731161a2a3c054bc146fd19c76097ab7f9b9a537cd8e39f91e93973
- Git branch: master
- Git commit: 5df35d2c7e82a0a3ed53cc04bdb7bf5b18fe54a5
- Dirty workspace: True
- Dataset IDs: ['research_futures:GC:1m', 'research_futures:SI:1m']
- Backtest config hash: sha256:5bd571d2adc40db312cea2d5c996a00854c61e7d82ff80ba81833db0b4ac7cf8
- Generated at: 2026-06-04T05:38:21.206458+00:00
- Promotion status: research_only

## Execution Summary
- step_count: 2
- passed: 2
- blocked: 0
- failed: 0

## Step Results
### 1. implementation (implementation_gate)
- status: passed
- message: implementation gate passed
- outputs:
  - missing_modules: []
  - missing_strategies: []
  - required_modules: ['strategies.research.orb_vwap_trend_filter']
  - required_strategy: strategies.research.orb_vwap_trend_filter:OrbVwapTrendFilterStrategy
### 2. gc_target3_single (backtest_matrix)
- status: passed
- message: backtest matrix completed
- outputs:
  - candidate_count: 1
  - period_count: 2
  - periods: [{'end': '2026-01-01T00:00:00+00:00', 'name': 'train_2024_2025', 'role': 'selection', 'start': '2024-01-01T00:00:00+00:00'}, {'end': '2026-05-22T20:20:00+00:00', 'name': 'oos_2026', 'role': 'validation', 'start': '2026-01-01T00:00:00+00:00'}]
  - report_only_periods: []
  - run_count: 2
  - selection_basis: ['train_2024_2025', 'oos_2026']
  - summary_path: configs/research/workflows/../../../runs/research/orb_vwap_trend_gc_si_long/gc_target3_single/summary.json

## Period Roles
| Period | Start | End | Role | Usage |
| --- | --- | --- | --- | --- |
| train_2024_2025 | 2024-01-01T00:00:00+00:00 | 2026-01-01T00:00:00+00:00 | selection | selection_basis |
| oos_2026 | 2026-01-01T00:00:00+00:00 | 2026-05-22T20:20:00+00:00 | validation | selection_basis |

## Evidence Summary
### Implementation Gate
- required_modules: ['strategies.research.orb_vwap_trend_filter']
- required_strategy: strategies.research.orb_vwap_trend_filter:OrbVwapTrendFilterStrategy
- missing_modules: []
- missing_strategies: []

## Review Decision
This projection block is not source of truth for promotion; source-of-truth is audit/packet/evidence/graph.
```yaml
decision:
  cost_stress_available: false
  evidence_bundle_id: null
  reason:
    []
  required_next_evidence:
    []
  reviewer: null
  status: keep_researching
  trade_diagnostics_available: false
  validation_scorecard_available: false
```

## Non-Promotion Boundary
This workflow report is research evidence only. It does not promote strategy code into paper/live execution.
