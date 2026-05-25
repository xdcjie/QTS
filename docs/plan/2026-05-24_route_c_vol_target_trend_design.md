# Route C Volatility-Targeted Trend Research Design

## Objective

Continue strategy research beyond VWAP and dual-supertrend with a production-review
candidate family that can plausibly satisfy:

- SI and OOS evidence after 2020
- annualized return above 10%
- Sharpe at or above 0.70 in every required window, target above 1.00
- max drawdown below 20%
- no holdout tuning and no paper/live promotion from research alone

## External Evidence

The next lane is based on time-series momentum and volatility scaling:

- Moskowitz, Ooi, and Pedersen document own-past-return predictability across
  equity index, currency, commodity, and bond futures, with one-to-12-month
  persistence and later reversal. Source:
  https://pages.stern.nyu.edu/~lpederse/papers/TimeSeriesMomentum.pdf
- Hurst, Ooi, and Pedersen extend trend-following evidence over a much longer
  history and report positive average returns across decades and macro regimes.
  Source: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2993026
- Moreira and Muir show that reducing exposure when realized volatility is high
  can improve Sharpe ratios because expected returns do not rise proportionally
  with volatility. Source: https://www.nber.org/papers/w22208
- Commodity term structure and basis-momentum papers are relevant but require
  reliable curve/spread exposure. Source:
  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2587784

## Current Local Evidence

Route B rejected all tested candidates:

- GC VWAP still failed 2020-2022 and/or 2022-2024 windows.
- SI VWAP slope/acceptance was closest but missed 10% annualized return and
  Sharpe 0.70 in both 2020-2022 and 2022-2024.
- Dual-supertrend GC/SI failed pre-holdout gates, with SI showing unacceptable
  holdout/anchor drawdowns.

The next strategy must not be another high-turnover 15m trend variant. It should
reduce turnover and use a slower signal that is less likely to overfit intraday
noise.

## Flow Gate

Flow ID: `FLOW-RESEARCH`
Canonical entry: `PYTHONPATH=backend/src uv run python scripts/run_research.py --config configs/research/vwap.yaml workflow configs/research/workflows/vwap_factor_search.yaml`
Config owner: `configs/research/vwap.yaml` and `configs/research/workflows/vwap_factor_search.yaml`
Allowed owner: research workflow YAML, research-only example strategy, and tests
Iteration point: Route C `backtest_matrix` candidate params and predeclared windows
Future-data risk: yes; holdout windows and reports must not tune candidates
Required verification: workflow tests, config parse tests, canonical workflow run

Flow ID: `FLOW-BACKTEST`
Canonical entry: `ResearchSession.run_backtest(...)` from the research workflow
Config owner: `configs/backtest.route_c_vol_target_trend_*.yaml`
Allowed owner: backtest config and Strategy SDK example strategy
Iteration point: strategy params, timeframe, cost model, warmup, and date windows
Future-data risk: yes; strategy must use only completed daily bars visible at callback time
Required verification: unit tests for strategy behavior, config parsing, integration tests, and costed backtest matrix artifacts

Domain fact / invariant: daily bars are session-aligned `1d` bars, not 24-hour clock buckets.
Correct owner or abstraction boundary: `qts.data.bars` and existing backtest aggregation produce daily bars; the strategy only consumes Strategy SDK `DataView` history.
Forbidden shortcut: reading CSVs, spread rows, or future bars directly from strategy code.
Required gates / verification: unit tests for completed-bar strategy behavior, `make guardrails`, and backtest integration evidence.

## Recommended Lane

Implement `examples.strategies.vol_target_trend:VolTargetTrendStrategy`.

Signal:

- Subscribe to one futures root on `1d`.
- Use completed daily closes only.
- Compute simple return over a momentum lookback.
- Compute realized daily volatility over a volatility lookback.
- Go long when momentum return is above `min_signal_return`.
- Go short when momentum return is below `-min_signal_return` and shorting is enabled.
- Otherwise close.
- Size target percent as `target_annual_vol / realized_annual_vol`, capped by
  `max_target_percent`.
- Suppress duplicate target emissions unless the new target changes by at least
  `rebalance_threshold`.

Research matrix:

- SI and GC separate configs, both using local historical research futures data.
- Windows:
  - `is_2020_2022`: 2020-01-01 to 2022-01-01
  - `validation_2022_2024`: 2022-01-01 to 2024-01-01
  - `holdout_2024_2026`: 2024-01-01 to 2026-04-10, report-only
  - `anchor_2010_2020`: 2010-06-06 to 2020-01-01
- Candidate grid kept small:
  - `tsm_63_vol20_target20`
  - `tsm_126_vol40_target20`
  - `tsm_252_vol60_target15`

## Rejected For This Iteration

Term-structure and basis-momentum are promising but not first for Route C:

- The local CSVs contain spread rows, but the current historical backtest stream
  excludes spreads by design for tradable-bar replay.
- A correct curve lane needs a dedicated data/research boundary that models
  spreads and curve signals without passing non-tradable spread symbols into
  core strategy/risk/order logic.

Intraday opening-range strategies are also deferred:

- They are more exposed to session microstructure and parameter overfit.
- Route B already showed that 15m intraday variants can look good in holdout
  while failing pre-holdout robustness.
