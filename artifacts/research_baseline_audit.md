# WP-00 Research Baseline Audit

Generated UTC: `2026-05-25T07:31:43+00:00`

This Markdown report is the reviewer-facing companion to `artifacts/research_baseline_audit.json`.
The JSON is the authoritative machine-readable audit output for this WP.

## Status Snapshot

- Repository root: `/Users/bjhl/Projects/QTS`
- Branch: `master`
- Commit: `166ec47b46cd0f1fce785605780563f087b77666`
- Dirty before audit artifacts: `true`
- Modified files before audit artifacts: `1`
- Untracked files before audit artifacts: `0`
- Current untracked files after audit artifact generation: `2`

### Dirty State Before Audit Artifacts

| Status | Path | Classification |
| --- | --- | --- |
| ` M` | `AGENTS.md` | `non_research_instructions` |

Research-related dirty/untracked files before audit artifact generation: `0`.

### Current WP-00 Generated Artifacts

| Status | Path | Classification |
| --- | --- | --- |
| `??` | `artifacts/research_baseline_audit.json` | `graphify_report_artifacts` |
| `??` | `artifacts/research_baseline_audit.md` | `graphify_report_artifacts` |

## Flow And Domain Contract

- Flow IDs: `FLOW-RESEARCH`, `FLOW-REPORTING`
- Boundary: audit evidence only under `artifacts/research_baseline_audit.*`
- Behavior contract: this WP does not create trading, paper, live, order, risk, or runtime behavior.
- Forbidden shortcut preserved: ad hoc VWAP paths are not treated as valid research entrypoints.

## Canonical VWAP Entrypoint

```bash
PYTHONPATH=backend/src uv run python scripts/run_research.py --config configs/research/vwap.yaml workflow configs/research/workflows/vwap_factor_search.yaml
```

Canonical configs:

- `configs/research/vwap.yaml`
- `configs/backtest.vwap_factor_research.yaml`
- `configs/strategies/vwap_factor_research.yaml`
- `configs/research/workflows/vwap_factor_search.yaml`

## Research Surface Counts

- Research session configs: `8`
- Research workflow configs: `55`
- Generic optimizer configs: `1`
- `qts.research` modules: `25`
- `qts.factors` modules: `4`
- Durable research docs: `9`
- Route / Research OS plan docs: `9`
- Research/report/VWAP-related tests: `45`
- Tracked report/artifact paths matching research terms: `4`

## Classification Summary

- `canonical_research_infrastructure`: `48`
- `vwap_specific_research`: `68`
- `route_b_r_research`: `10`
- `production_strategy`: `14`
- `tests`: `45`
- `graphify_report_artifacts`: `5`
- `obsolete_ad_hoc_scripts`: `0`
- `non_research_instructions_dirty_state`: `1`

### Canonical Research Infrastructure

- `backend/src/qts/factors/AGENTS.md`
- `backend/src/qts/factors/__init__.py`
- `backend/src/qts/factors/contract.py`
- `backend/src/qts/factors/momentum.py`
- `backend/src/qts/research/__init__.py`
- `backend/src/qts/research/experiment_manifest.py`
- `backend/src/qts/research/experiment_recorder.py`
- `backend/src/qts/research/experiment_store.py`
- `backend/src/qts/research/factor_candidate.py`
- `backend/src/qts/research/factor_discovery.py`
- `backend/src/qts/research/factor_evaluation.py`
- `backend/src/qts/research/factor_spec.py`
- `backend/src/qts/research/factor_spec_store.py`
- `backend/src/qts/research/optimizer/__init__.py`
- `backend/src/qts/research/optimizer/constraints.py`
- `backend/src/qts/research/optimizer/failure_veto.py`
- `backend/src/qts/research/optimizer/job.py`
- `backend/src/qts/research/optimizer/parameter_space.py`
- `backend/src/qts/research/optimizer/pipeline.py`
- `backend/src/qts/research/optimizer/result.py`
- `backend/src/qts/research/optimizer/runner.py`
- `backend/src/qts/research/optimizer/validation.py`
- `backend/src/qts/research/optimizer/walk_forward.py`
- `backend/src/qts/research/portfolio_ensemble.py`
- `backend/src/qts/research/report.py`
- `backend/src/qts/research/research_book.py`
- `backend/src/qts/research/session.py`
- `backend/src/qts/research/tearsheet.py`
- `backend/src/qts/research/workflow.py`
- `configs/research/quickstart.yaml`
- `configs/research/workflows/quickstart.yaml`
- `docs/architecture/backtest_live_parity.md`
- `docs/architecture/module_boundaries.md`
- `docs/architecture/system_flows.md`
- `docs/research/factor_contract_v1.md`
- `docs/research/factor_discovery_v1.md`
- `docs/research/factor_evaluation_v1.md`
- `docs/research/factor_spec_v1.md`
- `docs/research/optimizer_validation_v1.md`
- `docs/research/research_book_v1.md`
- `docs/research/research_session_v1.md`
- `docs/research/signal_model_v1.md`
- `docs/research/strategy_factor_api_v1.md`
- `docs/testing/domain_invariants.md`
- `docs/testing/testing_strategy.md`
- `scripts/generate_backtest_report.py`
- `scripts/run_optimizer.py`
- `scripts/run_research.py`

### VWAP-Specific Research Surface

- `configs/backtest.vwap_factor_research.yaml`
- `configs/research/vwap.yaml`
- `configs/research/vwap_gc_15m_long.yaml`
- `configs/research/vwap_gc_5m_long.yaml`
- `configs/research/vwap_gc_long.yaml`
- `configs/research/vwap_si_15m_long.yaml`
- `configs/research/vwap_si_5m_long.yaml`
- `configs/research/vwap_si_long.yaml`
- `configs/research/workflows/vwap_factor_gc_15m_feature_ablation.yaml`
- `configs/research/workflows/vwap_factor_gc_15m_long_search.yaml`
- `configs/research/workflows/vwap_factor_gc_15m_round01_escape_matrix.yaml`
- `configs/research/workflows/vwap_factor_gc_15m_round02_conditional_acceptance_matrix.yaml`
- `configs/research/workflows/vwap_factor_gc_15m_round03_bad_acceptance_threshold_matrix.yaml`
- `configs/research/workflows/vwap_factor_gc_15m_round04_exit_target_matrix.yaml`
- `configs/research/workflows/vwap_factor_gc_15m_round05_bad_regime_target_matrix.yaml`
- `configs/research/workflows/vwap_factor_gc_15m_round09_momentum_strength_matrix.yaml`
- `configs/research/workflows/vwap_factor_gc_15m_round10_old_year_anchor_matrix.yaml`
- `configs/research/workflows/vwap_factor_gc_15m_round11_conditional_momentum_anchor_matrix.yaml`
- `configs/research/workflows/vwap_factor_gc_15m_round12_slope_strength_anchor_matrix.yaml`
- `configs/research/workflows/vwap_factor_gc_15m_round13_structure_anchor_matrix.yaml`
- `configs/research/workflows/vwap_factor_gc_15m_round14_exit_anchor_matrix.yaml`
- `configs/research/workflows/vwap_factor_gc_15m_round15_target_anchor_matrix.yaml`
- `configs/research/workflows/vwap_factor_gc_15m_round16_target175_vwap_exit_check.yaml`
- `configs/research/workflows/vwap_factor_gc_15m_round17_early_no_progress_exit.yaml`
- `configs/research/workflows/vwap_factor_gc_15m_round18_target175_no_progress_exit.yaml`
- `configs/research/workflows/vwap_factor_gc_15m_round19_dynamic_sizing.yaml`
- `configs/research/workflows/vwap_factor_gc_15m_round20_oos_degradation_repair.yaml`
- `configs/research/workflows/vwap_factor_gc_15m_round21_entry_sizing.yaml`
- `configs/research/workflows/vwap_factor_gc_15m_round22_rejection_quality.yaml`
- `configs/research/workflows/vwap_factor_gc_15m_round23_range_cap.yaml`
- `configs/research/workflows/vwap_factor_gc_15m_round24_session_entry_risk.yaml`
- `configs/research/workflows/vwap_factor_gc_15m_round25_combined_risk_controls.yaml`
- `configs/research/workflows/vwap_factor_gc_15m_round26_trend_confirmation.yaml`
- `configs/research/workflows/vwap_factor_gc_15m_round27_oos_validation.yaml`
- `configs/research/workflows/vwap_factor_gc_15m_sigma115_ma027_transfer.yaml`
- `configs/research/workflows/vwap_factor_gc_5m_long_search.yaml`
- `configs/research/workflows/vwap_factor_gc_long_search.yaml`
- `configs/research/workflows/vwap_factor_search.yaml`
- `configs/research/workflows/vwap_factor_si_15m_feature_ablation.yaml`
- `configs/research/workflows/vwap_factor_si_15m_long_search.yaml`
- `configs/research/workflows/vwap_factor_si_15m_round01_escape_matrix.yaml`
- `configs/research/workflows/vwap_factor_si_15m_round02_conditional_acceptance_matrix.yaml`
- `configs/research/workflows/vwap_factor_si_15m_round03_bad_acceptance_threshold_matrix.yaml`
- `configs/research/workflows/vwap_factor_si_15m_round04_exit_target_matrix.yaml`
- `configs/research/workflows/vwap_factor_si_15m_round05_bad_regime_target_matrix.yaml`
- `configs/research/workflows/vwap_factor_si_15m_round06_late_asia_matrix.yaml`
- `configs/research/workflows/vwap_factor_si_15m_round07_momentum_strength_matrix.yaml`
- `configs/research/workflows/vwap_factor_si_15m_round08_momentum_exit_refine_matrix.yaml`
- `configs/research/workflows/vwap_factor_si_15m_round10_old_year_anchor_matrix.yaml`
- `configs/research/workflows/vwap_factor_si_15m_round11_conditional_momentum_anchor_matrix.yaml`
- `configs/research/workflows/vwap_factor_si_15m_round12_slope_strength_anchor_matrix.yaml`
- `configs/research/workflows/vwap_factor_si_15m_round13_slope020_old_year_sweep.yaml`
- `configs/research/workflows/vwap_factor_si_15m_round14_slope_threshold_refine.yaml`
- `configs/research/workflows/vwap_factor_si_15m_round15_conditional_slope_refine.yaml`
- `configs/research/workflows/vwap_factor_si_15m_round16_slope020_exit_refine.yaml`
- `configs/research/workflows/vwap_factor_si_15m_round17_slope020_volume_curve.yaml`
- `configs/research/workflows/vwap_factor_si_15m_round18_slope020_feature_attribution.yaml`
- `configs/research/workflows/vwap_factor_si_15m_round19_sigma_escape.yaml`
- `configs/research/workflows/vwap_factor_si_15m_round20_sigma_escape_refine.yaml`
- `configs/research/workflows/vwap_factor_si_15m_round21_sigma_escape_anchor_validation.yaml`
- `configs/research/workflows/vwap_factor_si_5m_long_search.yaml`
- `configs/research/workflows/vwap_factor_si_long_search.yaml`
- `configs/strategies/vwap_factor_research.yaml`
- `strategies/research/vwap_factor_research.py`
- `tests/anchor/test_vwap_pullback_v2_state_machine.py`
- `tests/unit/strategies/test_vwap_factor_research.py`
- `tests/unit/strategies/test_vwap_pullback.py`
- `tests/unit/strategies/test_vwap_regime_pullback.py`

### Route B-R / Route Governance Surface

- `configs/research/workflows/vwap_factor_search.yaml`
- `docs/plan/2026-05-23_route_b_strategy_research_design.md`
- `docs/plan/2026-05-23_route_b_strategy_research_implementation_plan.md`
- `docs/plan/2026-05-24_route_c_vol_target_trend_design.md`
- `docs/plan/2026-05-24_route_c_vol_target_trend_implementation_plan.md`
- `docs/plan/2026-05-24_route_d_gc_si_relative_value_design.md`
- `docs/plan/2026-05-24_route_d_gc_si_relative_value_implementation_plan.md`
- `docs/plan/2026-05-24_route_e_carry_trend_design.md`
- `docs/plan/2026-05-24_route_e_carry_trend_implementation_plan.md`
- `docs/plan/qts_quant_research_os_subagent_plan.md`

### Production Strategy / Runtime Config Surface

- `configs/backtest.vwap_production_pullback_gc.yaml`
- `configs/backtest.vwap_production_pullback_si.yaml`
- `configs/live.example.yaml`
- `configs/live.ibkr.example.yaml`
- `configs/paper.ibkr.example.yaml`
- `configs/paper.vwap_production_pullback_gc.example.yaml`
- `configs/paper.vwap_production_pullback_si.example.yaml`
- `configs/paper.yaml`
- `configs/paper_broker.yaml`
- `configs/paper_simulated.yaml`
- `configs/strategies/vwap_production_pullback_gc.yaml`
- `configs/strategies/vwap_production_pullback_si.yaml`
- `strategies/production/__init__.py`
- `strategies/production/vwap_production_pullback.py`

### Test Coverage Map

- `research_session`: `3` path(s)
  - `tests/integration/test_research_session_facade.py`
  - `tests/integration/test_research_session_factor_discovery.py`
  - `tests/unit/research/test_research_session.py`
- `research_workflow`: `2` path(s)
  - `tests/unit/research/test_research_workflow.py`
  - `tests/integration/test_run_research_cli.py`
- `factor_discovery_and_specs`: `10` path(s)
  - `tests/integration/test_research_session_factor_discovery.py`
  - `tests/unit/factors/test_momentum.py`
  - `tests/unit/research/test_factor_candidate.py`
  - `tests/unit/research/test_factor_discovery.py`
  - `tests/unit/research/test_factor_evaluation.py`
  - `tests/unit/research/test_factor_evaluation_manifest.py`
  - `tests/unit/research/test_factor_spec.py`
  - `tests/unit/research/test_factor_spec_store.py`
  - `tests/unit/strategies/test_vwap_factor_research.py`
  - `tests/unit/strategy_sdk/test_indicator_factory.py`
- `optimizer_validation`: `6` path(s)
  - `tests/integration/test_optimizer_consumes_backtest_config.py`
  - `tests/integration/test_optimizer_validation_cli.py`
  - `tests/integration/test_run_optimizer_cli_outputs_ranked_results.py`
  - `tests/unit/research/test_optimizer_constraints.py`
  - `tests/unit/research/test_optimizer_failure_veto.py`
  - `tests/unit/research/test_optimizer_walk_forward.py`
- `experiment_manifest_store`: `3` path(s)
  - `tests/unit/research/test_experiment_manifest.py`
  - `tests/unit/research/test_experiment_recorder.py`
  - `tests/unit/research/test_experiment_store.py`
- `tearsheet_and_reports`: `14` path(s)
  - `tests/anchor/test_broker_execution_report_fill_time.py`
  - `tests/integration/test_backtest_analyst_report_generation.py`
  - `tests/integration/test_live_execution_report_flow.py`
  - `tests/replay/test_backtest_report_hash.py`
  - `tests/unit/backtest/test_backtest_report_metrics.py`
  - `tests/unit/backtest/test_report_metadata.py`
  - `tests/unit/data/test_validation_report.py`
  - `tests/unit/reporting/test_backtest_analyst_report.py`
  - `tests/unit/reporting/test_broker_runtime_report_writer.py`
  - `tests/unit/reporting/test_reporting_contracts.py`
  - `tests/unit/reporting/test_statistics_payload_shape.py`
  - `tests/unit/research/test_research_report.py`
  - `tests/unit/research/test_tearsheet.py`
  - `tests/unit/runtime/test_execution_report_handler.py`
- `vwap_strategy_research`: `4` path(s)
  - `tests/anchor/test_vwap_pullback_v2_state_machine.py`
  - `tests/unit/strategies/test_vwap_factor_research.py`
  - `tests/unit/strategies/test_vwap_pullback.py`
  - `tests/unit/strategies/test_vwap_regime_pullback.py`
- `canonical_vwap_workflow_tests`: `2` path(s)
  - `tests/integration/test_run_research_cli.py`
  - `tests/unit/research/test_research_workflow.py`

### Graphify / Report Artifacts

- `graphify-out/graph.json` exists: `true`
- `graphify-out/wiki/index.md` exists: `false`
- `graphify-out/GRAPH_REPORT.md` exists: `true`
- Top tracked report/artifact directories:
  - `artifacts/analysis/backend_class_role_review_2026-05-18.md`: `1` path(s)
  - `artifacts/research_system_for_chatgpt55_pro.md`: `1` path(s)
  - `artifacts/verification/gc_strategy_data_2025`: `1` path(s)
  - `artifacts/verification/gc_strategy_data_2026-05-18`: `1` path(s)

## Deprecated Or Ad Hoc Candidates

No `scripts/research/run_vwap_*.py` or `configs/optimizer/*vwap*.yaml` candidates were present at the observation point.

## Baseline Conclusion

- The current research baseline continues from the canonical `scripts/run_research.py` workflow path.
- The workspace was dirty before this audit only because `AGENTS.md` was modified; it is recorded as non-research/instructions.
- No untracked research/workflow/route files were present before the audit artifacts were generated.
- The current untracked files are the two WP-00 audit artifacts generated by this task.
- The audit files are evidence artifacts only and do not bless any ad hoc VWAP path.
