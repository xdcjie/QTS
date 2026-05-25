# Route C Volatility-Targeted Trend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a reproducible Route C research lane for daily volatility-targeted time-series momentum on GC and SI.

**Architecture:** The lane stays in `FLOW-RESEARCH` and `FLOW-BACKTEST`. A new Strategy SDK example strategy consumes only completed `1d` bars and emits target intents through the shared backtest path. The canonical VWAP research workflow owns Route C matrices and report-only holdout metadata.

**Tech Stack:** Python, YAML, Strategy SDK, `ResearchWorkflowConfig`, `BacktestRuntimeConfig`, pytest, ruff, mypy, guardrails.

---

## Files

- Create: `examples/strategies/vol_target_trend.py`
  Research-only Strategy SDK strategy for daily time-series momentum with volatility target sizing.
- Create: `tests/unit/strategies/test_vol_target_trend.py`
  Unit tests for long, short, flat, volatility cap, and duplicate-intent suppression behavior.
- Create: `configs/backtest.route_c_vol_target_trend_gc.yaml`
  Costed GC backtest config for Route C.
- Create: `configs/backtest.route_c_vol_target_trend_si.yaml`
  Costed SI backtest config for Route C.
- Modify: `configs/research/workflows/vwap_factor_search.yaml`
  Add Route C implementation gate, GC/SI backtest matrices, and report step.
- Modify: `tests/unit/backtest/test_backtest_config.py`
  Parse-test the new Route C backtest configs.
- Modify: `tests/unit/research/test_research_workflow.py`
  Gate Route C windows, candidates, holdout policy, and implementation entry.

## TDD Tasks

### Task 1: Strategy Unit Tests

- [x] Write failing tests in `tests/unit/strategies/test_vol_target_trend.py`.
- [x] Run the focused test and verify it fails because `VolTargetTrendStrategy` does not exist.
- [x] Implement `examples/strategies/vol_target_trend.py`.
- [x] Re-run focused strategy tests and verify they pass.

### Task 2: Backtest Config Tests

- [x] Add failing config parse test for `configs/backtest.route_c_vol_target_trend_gc.yaml` and `configs/backtest.route_c_vol_target_trend_si.yaml`.
- [x] Run the focused test and verify it fails because configs do not exist.
- [x] Add both Route C backtest configs.
- [x] Re-run focused config tests and verify they pass.

### Task 3: Workflow Gate Tests

- [x] Add failing research workflow tests for Route C steps and report-only holdout policy.
- [x] Run the focused test and verify it fails because Route C workflow steps do not exist.
- [x] Add Route C steps to `configs/research/workflows/vwap_factor_search.yaml`.
- [x] Re-run focused workflow tests and verify they pass.

### Task 4: Canonical Evidence

- [x] Run focused related tests:

```bash
PYTHONPATH=backend/src:. uv run pytest \
  tests/unit/strategies/test_vol_target_trend.py \
  tests/unit/backtest/test_backtest_config.py::test_route_c_vol_target_trend_backtest_configs_parse \
  tests/unit/research/test_research_workflow.py::test_canonical_vwap_workflow_declares_route_c_lanes_and_windows \
  tests/unit/research/test_research_workflow.py::test_route_c_workflow_records_holdout_as_report_only_policy -q
```

- [x] Run the canonical research workflow:

```bash
PYTHONPATH=backend/src uv run python scripts/run_research.py \
  --config configs/research/vwap.yaml \
  workflow configs/research/workflows/vwap_factor_search.yaml
```

- [x] Extract Route C summaries and apply promotion gates.

### Task 5: Required Checks

- [x] Inspect private helpers in changed Python files:

```bash
rg -n "^def _|^class _" examples/strategies/vol_target_trend.py tests/unit/strategies/test_vol_target_trend.py tests/unit/research/test_research_workflow.py tests/unit/backtest/test_backtest_config.py
```

- [x] Run:

```bash
uv run ruff format examples/strategies/vol_target_trend.py tests/unit/strategies/test_vol_target_trend.py tests/unit/research/test_research_workflow.py tests/unit/backtest/test_backtest_config.py
uv run ruff format --check .
make lint
make guardrails
make typecheck
make test-unit
make test-integration
```

Run `make test-anchor` only if implementation changes bar/session/calendar/instrument domain behavior.

Executed checks:

- `uv run ruff format examples/strategies/vol_target_trend.py tests/unit/strategies/test_vol_target_trend.py tests/unit/research/test_research_workflow.py tests/unit/backtest/test_backtest_config.py`
- `uv run ruff format --check .`
- `make format`
- `make lint`
- `make guardrails`
- `make typecheck`
- `make test-unit`
- `make test-integration`

`make test-anchor` was not run because Route C did not change bar generation,
session/calendar logic, instrument identity, portfolio accounting, order state
machines, or risk semantics.

## Execution Verdict

Canonical workflow:

```bash
PYTHONPATH=backend/src uv run python scripts/run_research.py \
  --config configs/research/vwap.yaml \
  workflow configs/research/workflows/vwap_factor_search.yaml
```

Result: completed, 14 passed steps, including Route C GC and SI matrices plus
Route C report.

Promotion verdict: no Route C candidate is production-review eligible.

GC failures:

- 2020-2022 annualized return ranged from -3.27% to 0.09%; Sharpe ranged from
  -0.71 to 0.04; trades ranged from 4 to 12.
- 2022-2024 annualized return ranged from -3.89% to -0.35%; Sharpe ranged from
  -0.99 to -0.02; trades ranged from 5 to 11.
- 2024-2026 holdout had one positive annualized result, 11.56% with Sharpe
  0.62, but max drawdown was 30.40% and holdout is report-only.

SI failures:

- 2020-2022 best annualized return was 4.20% with Sharpe 0.65; trades ranged
  from 7 to 20.
- 2022-2024 all candidates lost money, with annualized return from -11.92% to
  -4.23% and Sharpe from -1.55 to -0.68.
- 2024-2026 holdout was positive for all candidates, but drawdown ranged from
  27.90% to 41.04%, and holdout is report-only.

The lane is retained as reproducible negative evidence. It should not be tuned
against the 2024-2026 holdout. The next research lane should change the signal
family or data boundary rather than only retuning these three daily TSM
parameters.
