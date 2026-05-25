# Route D GC/SI Relative Value Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a reproducible Route D research lane for GC/SI daily ratio mean reversion.

**Architecture:** The lane stays in `FLOW-RESEARCH` and `FLOW-BACKTEST`. A new Strategy SDK example strategy consumes only completed `1d` GC and SI bars, computes a rolling ratio z-score, and emits separate target quantity intents for both tradable legs. The canonical research workflow owns Route D matrices and report-only holdout metadata.

**Tech Stack:** Python, YAML, Strategy SDK, `ResearchWorkflowConfig`, `BacktestRuntimeConfig`, pytest, ruff, mypy, guardrails.

---

## Files

- Create: `examples/strategies/gc_si_ratio_mean_reversion.py`
  Research-only Strategy SDK strategy for GC/SI ratio mean reversion.
- Create: `tests/unit/strategies/test_gc_si_ratio_mean_reversion.py`
  Unit tests for warmup subscriptions, long-ratio entry, short-ratio entry,
  exit behavior, duplicate suppression, and YAML string parameter loading.
- Create: `configs/backtest.route_d_gc_si_ratio_mean_reversion.yaml`
  Costed GC/SI combined backtest config for Route D.
- Modify: `configs/research/workflows/vwap_factor_search.yaml`
  Add Route D implementation gate, GC/SI ratio backtest matrix, and report step.
- Modify: `tests/unit/backtest/test_backtest_config.py`
  Parse-test the new Route D backtest config.
- Modify: `tests/unit/research/test_research_workflow.py`
  Gate Route D windows, candidates, holdout policy, and implementation entry.

## TDD Tasks

### Task 1: Strategy Unit Tests

- [x] Write failing tests in `tests/unit/strategies/test_gc_si_ratio_mean_reversion.py`.
- [x] Run the focused strategy tests and verify they fail because `GcSiRatioMeanReversionStrategy` does not exist.
- [x] Implement `examples/strategies/gc_si_ratio_mean_reversion.py`.
- [x] Re-run focused strategy tests and verify they pass.
- [x] Add aligned-leg regression coverage so GC/SI ratio decisions wait for matching completed bar end times.

### Task 2: Backtest Config Tests

- [x] Add a failing config parse test for `configs/backtest.route_d_gc_si_ratio_mean_reversion.yaml`.
- [x] Run the focused test and verify it fails because the config does not exist.
- [x] Add the Route D backtest config.
- [x] Re-run the focused config test and verify it passes.

### Task 3: Workflow Gate Tests

- [x] Add failing research workflow tests for Route D steps and report-only holdout policy.
- [x] Run the focused tests and verify they fail because Route D workflow steps do not exist.
- [x] Add Route D steps to `configs/research/workflows/vwap_factor_search.yaml`.
- [x] Re-run focused workflow tests and verify they pass.

### Task 4: Canonical Evidence

- [x] Run focused related tests:

```bash
PYTHONPATH=backend/src:. uv run pytest \
  tests/unit/strategies/test_gc_si_ratio_mean_reversion.py \
  tests/unit/backtest/test_backtest_config.py::test_route_d_gc_si_ratio_mean_reversion_backtest_config_parses \
  tests/unit/research/test_research_workflow.py::test_canonical_vwap_workflow_declares_route_d_relative_value_lane \
  tests/unit/research/test_research_workflow.py::test_route_d_workflow_records_holdout_as_report_only_policy -q
```

- [x] Run the canonical research workflow:

```bash
PYTHONPATH=backend/src uv run python scripts/run_research.py \
  --config configs/research/vwap.yaml \
  workflow configs/research/workflows/vwap_factor_search.yaml
```

- [x] Extract Route D summaries and apply promotion gates.

## Execution Verdict

Canonical workflow completed successfully and produced:

- Summary: `runs/research/vwap/route-d/gc-si-ratio-mean-reversion-summary.json`
- Report: `runs/research/vwap/route-d/reports/route-d-gc-si-relative-value-report.md`

Promotion decision: **rejected; no production-review candidate**.

Required pre-holdout gates were annualized return > 10%, Sharpe >= 0.70, max
drawdown <= 20%, and enough trades to avoid a sparse-signal result. No Route D
candidate passed those gates across both `is_2020_2022` and
`validation_2022_2024`.

Key evidence:

| Period | Best/Relevant Candidate | Ann. Return % | Sharpe | Max DD % | Trades | Gate Result |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| is_2020_2022 | ratio_20_entry15_exit025_1x2 | 0.22 | 0.36 | 36.20 | 36 | Fails return, Sharpe, DD, trades |
| validation_2022_2024 | ratio_60_entry20_exit050_1x2 | 4.39 | 0.30 | 26.06 | 10 | Fails return, Sharpe, DD, trades |
| anchor_2010_2020 | ratio_20_entry15_exit025_1x2 | 10.11 | 0.42 | 32.45 | 104 | Fails Sharpe and DD |
| holdout_2024_2026 | ratio_20_entry15_exit025_1x2 | -30.93 | 0.50 | 422.16 | 50 | Report-only; poor drawdown |

The holdout window was not used for tuning or promotion. The result suggests a
plain GC/SI rolling ratio z-score is too sparse and unstable for production
promotion in this implementation.

### Task 5: Required Checks

- [x] Inspect private helpers in changed Python files:

```bash
rg -n "^def _|^class _" examples/strategies/gc_si_ratio_mean_reversion.py tests/unit/strategies/test_gc_si_ratio_mean_reversion.py tests/unit/research/test_research_workflow.py tests/unit/backtest/test_backtest_config.py
```

- [x] Run:

```bash
uv run ruff format examples/strategies/gc_si_ratio_mean_reversion.py tests/unit/strategies/test_gc_si_ratio_mean_reversion.py tests/unit/research/test_research_workflow.py tests/unit/backtest/test_backtest_config.py
uv run ruff format --check .
make format
make lint
make guardrails
make typecheck
make test-unit
make test-integration
```

Run `make test-anchor` only if implementation changes bar/session/calendar/instrument domain behavior.

Verification evidence:

- `PYTHONPATH=backend/src:. uv run pytest tests/unit/strategies/test_gc_si_ratio_mean_reversion.py tests/unit/backtest/test_backtest_config.py::test_route_d_gc_si_ratio_mean_reversion_backtest_config_parses tests/unit/research/test_research_workflow.py::test_canonical_vwap_workflow_declares_route_d_relative_value_lane tests/unit/research/test_research_workflow.py::test_route_d_workflow_records_holdout_as_report_only_policy -q` passed: 10 tests.
- `uv run ruff format --check .` passed: 692 files already formatted.
- `make format` passed: 692 files left unchanged.
- `make lint` passed.
- `make guardrails` passed.
- `make typecheck` passed: 668 source files.
- `make test-unit` passed: 1299 tests.
- `make test-integration` passed: 144 tests, 4 skipped.
- `make test-anchor` was not run because Route D did not change bar/session/calendar/instrument domain behavior.
