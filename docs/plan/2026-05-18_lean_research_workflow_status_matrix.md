# Lean-Inspired Research Workflow Status Matrix

- Document type: execution status matrix
- Owner: QTS platform engineering
- Created: 2026-05-18
- Source notes: `docs/plan/2026-05-18_lean_research_workflow_research_notes.md`
- Status legend: `Planned`, `In Progress`, `Blocked`, `Complete`

## Completion Rules

A plan is `Complete` only when every row below has direct evidence from:

- a first red unit, integration, anchor, architecture, or regression gate;
- a focused green command after implementation;
- durable docs updated for any public contract;
- `make guardrails` for boundary-sensitive changes;
- `make format`, `make lint`, `make typecheck`, and relevant tests;
- a commit hash recorded in this matrix.

Existing tests passing without a new gate does not close a plan.

## Plan Matrix

| Plan | Status | Plan File | First Red Gate | Acceptance Evidence To Record | Broad Verification | Commit |
|---|---:|---|---|---|---|---|
| RB-1 ResearchBook V1 | Planned | `docs/plan/2026-05-18_researchbook_v1_plan.md` | `tests/unit/research/test_research_book.py::test_research_book_config_rejects_missing_catalog_reference` | Unit + integration tests prove bounded history uses `HistoricalCatalog` and returns deterministic `[start, end)` rows. | `make guardrails && make test-unit && make test-integration` | No implementation commit |
| SIG-1 Signal + Portfolio Construction V1 | Planned | `docs/plan/2026-05-18_signal_portfolio_construction_v1_plan.md` | `tests/unit/strategy_sdk/test_signals.py::test_signal_requires_direction_and_source_model` | SDK tests prove signals are not orders; portfolio construction emits `TargetIntent`; integration test preserves risk path. | `make guardrails && make test-unit && make test-integration` | No implementation commit |
| FE-1 Factor Evaluation Artifacts V1 | Planned | `docs/plan/2026-05-18_factor_evaluation_artifacts_v1_plan.md` | `tests/unit/research/test_factor_evaluation.py::test_factor_evaluation_computes_rank_ic_and_bucket_spread` | Unit tests cover IC, bucket spread, coverage, turnover; manifest tests cover artifact hashes. | `make guardrails && make test-unit` | No implementation commit |
| OPTV-1 Optimizer Validation V1 | Planned | `docs/plan/2026-05-18_optimizer_validation_v1_plan.md` | `tests/unit/research/test_optimizer_constraints.py::test_constraint_rejects_result_below_minimum_metric` | Unit + integration tests prove constraints, walk-forward splits, and validation artifacts without bypassing `BacktestPipelineRunner`. | `make guardrails && make test-unit && make test-integration` | No implementation commit |

## Subagent Allocation Matrix

| Subagent Lane | Owns | Must Not Touch | Integration Point |
|---|---|---|---|
| RB worker | `backend/src/qts/research/research_book.py`, `tests/unit/research/test_research_book.py`, `tests/integration/test_research_book_historical_catalog.py`, `docs/research/research_book_v1.md` | Strategy SDK signal files; optimizer constraint files | Exports `ResearchBook`, `ResearchBookConfig`, and `HistoryRequest` from `qts.research` |
| SIG worker | `backend/src/qts/strategy_sdk/signals.py`, `backend/src/qts/strategy_sdk/portfolio_construction.py`, SDK tests/docs | `qts.research.factor_evaluation`; optimizer runner | Consumes `AssetRef`; emits existing `TargetIntent` objects |
| FE worker | `backend/src/qts/research/factor_evaluation.py`, factor-evaluation tests/docs | StrategyContext; optimizer CLI | Consumes current `qts.factors` contract and `ExperimentManifestWriter` |
| OPTV worker | `backend/src/qts/research/optimizer/constraints.py`, `backend/src/qts/research/optimizer/walk_forward.py`, optimizer CLI/docs/tests | ResearchBook internals; Strategy SDK signal files | Consumes `OptimizationResult` and `BacktestPipelineRunner` |

## Cross-Plan Gates

| Gate | Command | Expected Evidence |
|---|---|---|
| Docs have no passive-only contract | `rg -n "ResearchBook|Signal|FactorEvaluation|WalkForward" docs/research docs/plan` | Each public contract appears in a plan and a durable research/SDK doc. |
| No internal runtime leakage into research/factors | `make guardrails` | Guardrails pass; add a new rule only if an implementation introduces a new import boundary. |
| Required checks for normal code tasks | `make format && make lint && make guardrails && make typecheck && make test-unit` | All commands exit 0. |
| Module-interaction checks | `make test-integration` | Required for RB-1, SIG-1, and OPTV-1. |

## Matrix Update Protocol

1. Keep status `Planned` until the first red gate has been observed.
2. Change to `In Progress` after the red gate is committed or documented in the worker's log.
3. Change to `Complete` only after focused checks and broad checks are recorded.
4. Record the final commit hash in the `Commit` column.
