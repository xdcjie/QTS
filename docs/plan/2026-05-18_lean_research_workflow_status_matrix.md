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
| RB-1 ResearchBook V1 | Complete | `docs/plan/2026-05-18_researchbook_v1_plan.md` | `uv run pytest tests/unit/research/test_research_book.py::test_research_book_config_rejects_missing_catalog_reference -q` -> red: `ImportError: cannot import name 'HistoryRequest' from 'qts.research'`. | `uv run pytest tests/unit/research/test_research_book.py -q` -> 2 passed; `uv run pytest tests/integration/test_research_book_historical_catalog.py -q` -> 2 passed; `uv run pytest tests/unit/research/test_research_book.py tests/integration/test_research_book_historical_catalog.py -q` -> 4 passed; quality bundle `uv run pytest tests/unit/test_backtest_live_parallel_sequence_html.py tests/unit/test_project_panorama_html.py tests/quality/test_freeze_exception_schema.py tests/quality/test_platform_freeze.py tests/quality/test_class_inventory_guardrails.py -q` -> 21 passed. | `make guardrails` -> passed; `make format` -> 627 files unchanged; `make lint` -> passed; `make typecheck` -> success; `make test-unit` -> 941 passed; `make test-integration` -> 110 passed, 4 skipped. | `413553b` |
| SIG-1 Signal + Portfolio Construction V1 | Complete | `docs/plan/2026-05-18_signal_portfolio_construction_v1_plan.md` | `uv run pytest tests/unit/strategy_sdk/test_signals.py::test_signal_requires_direction_and_source_model -q` -> red: `ModuleNotFoundError: No module named 'qts.strategy_sdk.signals'`; review regressions `uv run pytest tests/unit/strategy_sdk/test_signals.py tests/unit/strategy_sdk/test_portfolio_construction.py -q` -> red: stale pending signals re-emitted and non-finite decimals leaked/accepted. | `uv run pytest tests/unit/strategy_sdk/test_signals.py tests/unit/strategy_sdk/test_portfolio_construction.py tests/integration/test_signal_portfolio_target_flow.py -q` -> 19 passed; inventory regression `uv run pytest tests/unit/test_backtest_live_parallel_sequence_html.py tests/unit/test_project_panorama_html.py -q` -> 12 passed. | `make format && make lint && make guardrails && make typecheck && make test-unit && make test-integration` -> initial completion: format unchanged; lint passed; guardrails passed; typecheck success; 964 unit tests passed; 111 integration tests passed, 4 skipped. Review fix verification: `make format && make lint && ... && make test-unit` -> format unchanged; lint passed; guardrails passed; typecheck success; 974 unit tests passed. | `acbb82e`; review fix `759bc75` |
| FE-1 Factor Evaluation Artifacts V1 | Complete | `docs/plan/2026-05-18_factor_evaluation_artifacts_v1_plan.md` | `uv run pytest tests/unit/research/test_factor_evaluation.py::test_factor_evaluation_computes_rank_ic_and_bucket_spread -q` -> red: `ModuleNotFoundError: No module named 'qts.research.factor_evaluation'`; review regression `uv run pytest tests/unit/research/test_factor_evaluation.py::test_factor_evaluation_rejects_constant_factor_and_return_ranks -q` -> red: did not raise `ValueError`; decimal-context regression `uv run pytest tests/unit/research/test_factor_evaluation.py::test_factor_evaluation_canonicalizes_non_perfect_rank_ic_across_decimal_contexts -q` -> red: artifact rank IC serialized as `0.4000000000` instead of canonical `0.4`; residual decimal-context regressions `uv run pytest tests/unit/research/test_factor_evaluation.py::test_factor_evaluation_formats_rank_ic_independent_of_decimal_context tests/unit/research/test_factor_evaluation.py::test_factor_evaluation_computes_coverage_independent_of_decimal_context tests/unit/research/test_factor_evaluation.py::test_factor_evaluation_computes_turnover_independent_of_decimal_context -q` -> red: low precision serialized rank IC as `-0.14286` and computed coverage/turnover as `0.66667`. | `uv run pytest tests/unit/research/test_factor_evaluation.py::test_factor_evaluation_formats_rank_ic_independent_of_decimal_context tests/unit/research/test_factor_evaluation.py::test_factor_evaluation_computes_coverage_independent_of_decimal_context tests/unit/research/test_factor_evaluation.py::test_factor_evaluation_computes_turnover_independent_of_decimal_context -q` -> 3 passed; `uv run pytest tests/unit/research/test_factor_evaluation.py tests/unit/research/test_factor_evaluation_manifest.py -q` -> 15 passed; inventory bundle `uv run pytest tests/unit/test_backtest_live_parallel_sequence_html.py tests/unit/test_project_panorama_html.py -q` -> 12 passed. | `make format && make lint && make guardrails && make typecheck && make test-unit` -> format 630 files unchanged; lint passed; guardrails passed; typecheck success; 956 unit tests passed. | `429f2f1`; fixes `ed9cb40`, `c639e02`, `8e0c803` |
| OPTV-1 Optimizer Validation V1 | Complete | `docs/plan/2026-05-18_optimizer_validation_v1_plan.md` | `uv run pytest tests/unit/research/test_optimizer_constraints.py::test_constraint_rejects_result_below_minimum_metric -q` -> red: `ImportError: cannot import name 'MetricConstraint' from 'qts.research.optimizer'`; review fix red `uv run pytest tests/unit/research/test_optimizer_constraints.py tests/unit/research/test_optimizer_walk_forward.py -q` -> 7 failed for non-finite metrics, non-parseable metric reason, Decimal parameter serialization, unsupported parameter rejection, and cross-split overlap/order. | Initial: `uv run pytest tests/unit/research/test_optimizer_constraints.py tests/unit/research/test_optimizer_walk_forward.py -q` -> 10 passed; `uv run pytest tests/integration/test_optimizer_validation_cli.py tests/integration/test_run_optimizer_cli_outputs_ranked_results.py -q` -> 2 passed; inventory regeneration check `uv run pytest tests/unit/test_backtest_live_parallel_sequence_html.py tests/unit/test_project_panorama_html.py -q` -> 12 passed. Review fix: `uv run pytest tests/unit/research/test_optimizer_constraints.py tests/unit/research/test_optimizer_walk_forward.py tests/integration/test_optimizer_validation_cli.py tests/integration/test_run_optimizer_cli_outputs_ranked_results.py -q` -> 20 passed. | Initial: `make format && make lint && make guardrails && make typecheck && make test-unit && make test-integration` -> format 641 files unchanged; lint passed; guardrails passed; typecheck success; 984 unit tests passed; 112 integration tests passed, 4 skipped. Review fix: `make format && make lint && make guardrails && make typecheck && make test-unit && make test-integration` -> format 641 files unchanged; lint passed; guardrails passed; typecheck success; 992 unit tests passed; 112 integration tests passed, 4 skipped. | `74160a1`; review fix `2fc5ba4` |

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
