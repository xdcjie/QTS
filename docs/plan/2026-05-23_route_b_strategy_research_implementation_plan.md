# Route B Strategy Research Implementation Plan

Status: implemented, with the GC/SI momentum lane retired during execution.

## Goal

Build reproducible Route B research evidence through the canonical VWAP research
workflow:

- repair/test VWAP candidates across GC and SI rolling windows
- compare against a structurally different non-VWAP dual-supertrend lane
- keep the 2024-2026 window report-only
- make no paper/live promotion without a separate promotion packet

## Flow Gate

Flow ID: `FLOW-RESEARCH`
Canonical entry: `scripts/run_research.py --config configs/research/vwap.yaml workflow configs/research/workflows/vwap_factor_search.yaml`
Config owner: `configs/research/vwap.yaml` and `configs/research/workflows/vwap_factor_search.yaml`
Allowed owner: `qts.research.workflow`, `ResearchSession`, and strategy/config files referenced by workflow steps
Iteration point: research workflow steps and backtest matrices only
Future-data risk: yes; holdout metrics and reports must not feed parameter selection
Required verification: workflow config unit tests, config parse tests, guardrails, and a canonical workflow run

Flow ID: `FLOW-BACKTEST`
Canonical entry: `ResearchSession` delegating executable evidence to `BacktestPipeline`
Config owner: backtest YAML files under `configs/`
Allowed owner: backtest config and Strategy SDK example strategy configuration surfaces
Iteration point: candidate periods and parameter grids in `backtest_matrix` steps
Future-data risk: yes; replay bars and reports must remain bounded by each matrix period
Required verification: backtest config parse tests and costed matrix artifacts

## Files

- Modified: `configs/research/vwap.yaml`
  Include both `GC` and `SI` roots for Route B evidence.
- Modified: `configs/research/workflows/vwap_factor_search.yaml`
  Add Route B implementation gate, VWAP GC/SI rolling matrices, dual-supertrend GC/SI matrices, and report-only holdout metadata.
- Created: `configs/backtest.route_b_dual_supertrend_gc.yaml`
  Backtest config for `DualSupertrendStrategy` on GC.
- Created: `configs/backtest.route_b_dual_supertrend_si.yaml`
  Backtest config for `DualSupertrendStrategy` on SI.
- Modified: `examples/strategies/dual_supertrend.py`
  Accept YAML strategy parameter overrides through the Strategy SDK loader.
- Modified: `examples/strategies/gc_si_momentum.py`
  Suppress duplicate unchanged target intents. The lane remains out of the canonical Route B workflow because its costed matrix generated oversized artifacts and remained pathologically high-turnover.
- Modified: `tests/unit/research/test_research_workflow.py`
  Gate Route B workflow windows, lane declarations, report-only holdout policy, and absence of the retired momentum lane.
- Modified: `tests/unit/backtest/test_backtest_config.py`
  Gate Route B dual-supertrend config parsing.
- Modified/created strategy tests under `tests/unit/strategies/`
  Gate dual-supertrend loader overrides and GC/SI momentum duplicate-intent suppression.

## Research Windows

| Name | Start | End | Role |
| --- | --- | --- | --- |
| `is_2020_2022` | `2020-01-01` | `2022-01-01` | Candidate selection |
| `validation_2022_2024` | `2022-01-01` | `2024-01-01` | Failure-window veto |
| `holdout_2024_2026` | `2024-01-01` | `2026-04-10` | Report-only holdout |
| `anchor_2010_2020` | `2010-06-06` | `2020-01-01` | Generalization stress |

Passing evidence requires costed runs with annualized return above 10%, Sharpe
at least 0.70 in every required window, target Sharpe at least 1.00, drawdown no
greater than 20%, at least 50 trades per major two-year window, positive PnL in
failure windows, and explicit no-promotion reporting.

## Canonical Execution

```bash
PYTHONPATH=backend/src uv run python scripts/run_research.py \
  --config configs/research/vwap.yaml \
  workflow configs/research/workflows/vwap_factor_search.yaml
```

Generated artifacts go under `runs/research/vwap/route-b/` and should not be
committed unless explicitly requested.

## Verification

Narrow tests:

```bash
PYTHONPATH=backend/src:. uv run pytest \
  tests/unit/research/test_research_workflow.py \
  tests/unit/backtest/test_backtest_config.py \
  tests/unit/strategies/test_dual_supertrend.py \
  tests/unit/strategies/test_gc_si_momentum.py \
  tests/integration/test_run_research_cli.py -q
```

Repository checks:

```bash
make format
make lint
make guardrails
make typecheck
make test-unit
```

## Execution Verdict

Canonical Route B workflow execution completed and produced these summaries:

- `runs/research/vwap/route-b/vwap-gc-rolling-summary.json`
- `runs/research/vwap/route-b/vwap-si-rolling-summary.json`
- `runs/research/vwap/route-b/dual-supertrend-gc-summary.json`
- `runs/research/vwap/route-b/dual-supertrend-si-summary.json`
- `runs/research/vwap/route-b/reports/route-b-strategy-research-report.md`

Execution note: the long workflow run was started before the final cleanup that
removed the retired momentum module from the Route B implementation gate. The
matrix outputs and candidate verdict are unaffected; the current workflow config
is separately gated by unit tests and no longer references the retired momentum
lane.

Result: no candidate is production-review eligible in this iteration.

Key rejects:

- GC VWAP candidates all fail the 2020-2022 and/or 2022-2024 gates. The best
  holdout returns are strong, but required pre-holdout windows include negative
  annualized returns and Sharpe below 0.70.
- SI VWAP candidates are the closest lane. `vwap_si_trend_sigma_slope_accept`
  has positive 2020-2024 behavior and strong report-only holdout, but still
  misses the required 10% annualized return and Sharpe 0.70 gates in both
  2020-2022 and 2022-2024.
- Dual-supertrend GC/SI variants fail pre-holdout profitability and Sharpe
  gates, with SI also showing severe holdout and anchor drawdowns.

Promotion decision: rejected. No paper/live configuration should be changed
from this Route B run.
