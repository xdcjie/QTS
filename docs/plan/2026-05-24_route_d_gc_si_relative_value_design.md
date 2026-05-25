# Route D GC/SI Relative Value Research Design

## Objective

Continue the strategy search after Route B and Route C rejected all production
review candidates. Route D tests a structurally different family: GC/SI
relative value mean reversion using the gold/silver price ratio.

The production-review bar remains unchanged:

- post-2020 IS/OOS evidence
- annualized return above 10%
- Sharpe at least 0.70 in every required pre-holdout window, target above 1.00
- max drawdown below 20%
- enough trades to avoid single-event fit
- no tuning on the 2024-2026 report-only holdout
- no paper/live promotion from research alone

## External Evidence

Relative-value pairs trading has a durable academic basis:

- Gatev, Goetzmann, and Rouwenhorst document the historical performance of a
  simple distance-based pairs trading rule. Source:
  https://www.nber.org/papers/w7032
- Recent gold/silver literature emphasizes long-run linkage and parameter
  instability in the relationship, which supports testing a rolling-window
  signal instead of a fixed static hedge. Source:
  https://www.ifo.de/en/cesifo/publications/2026/working-paper/long-run-linkages-and-parameter-instability-gold-silver

This lane deliberately does not model term structure, carry, or calendar-spread
signals yet. Those remain promising, but require a separate curve data boundary.

## Current Local Evidence

Route B rejected VWAP repair and dual-supertrend comparison lanes. Route C
rejected single-market daily volatility-targeted time-series momentum:

- GC failed both 2020-2022 and 2022-2024 pre-holdout return/Sharpe gates.
- SI had positive 2024-2026 holdout behavior but failed 2022-2024 and had
  unacceptable drawdown in holdout.
- Both lanes depended on single-market direction. Route D instead tests whether
  cross-market relative value is more stable across regimes.

## Flow Gate

Flow ID: `FLOW-RESEARCH`
Canonical entry: `PYTHONPATH=backend/src uv run python scripts/run_research.py --config configs/research/vwap.yaml workflow configs/research/workflows/vwap_factor_search.yaml`
Config owner: `configs/research/vwap.yaml` and `configs/research/workflows/vwap_factor_search.yaml`
Allowed owner: research workflow YAML, research-only example strategy, backtest config, and tests
Iteration point: Route D `backtest_matrix` candidate params and predeclared windows
Future-data risk: high; holdout and anchor evidence must not tune candidates
Required verification: workflow tests, config parse tests, canonical workflow run

Flow ID: `FLOW-BACKTEST`
Canonical entry: `ResearchSession.run_backtest_matrix(...)` from the research workflow
Config owner: `configs/backtest.route_d_gc_si_ratio_mean_reversion.yaml`
Allowed owner: backtest config and Strategy SDK example strategy
Iteration point: strategy params, timeframe, cost model, warmup, and date windows
Future-data risk: yes; strategy must use only completed daily bars visible at callback time
Required verification: unit tests for strategy behavior, config parsing, integration tests, and costed backtest matrix artifacts

Domain fact / invariant: the GC/SI ratio is a research signal, not a tradable instrument.
Correct owner or abstraction boundary: strategy code emits separate GC and SI target intents through `StrategyContext`; roll and `InstrumentId` resolution stay in registry/backtest boundaries.
Forbidden shortcut: trading a spread symbol, reading CSVs directly, accessing broker internals, or accessing `ContractSpec` from strategy code.
Required gates / verification: Strategy SDK unit tests, workflow holdout gate, `make guardrails`, and costed backtest evidence.

## Strategy Design

Implement `examples.strategies.gc_si_ratio_mean_reversion:GcSiRatioMeanReversionStrategy`.

Signal:

- Subscribe to GC and SI futures roots on `1d`.
- Use completed daily closes from `DataView.history(...)`.
- Compute `ratio = GC close / SI close` for a rolling lookback.
- Compute rolling z-score using the current ratio, rolling mean, and rolling
  standard deviation.
- If z-score is above `entry_z`, short the ratio: short GC and long SI.
- If z-score is below `-entry_z`, long the ratio: long GC and short SI.
- If a position is open and absolute z-score falls below `exit_z`, close both
  legs.
- Suppress duplicate target emissions while the side is unchanged.

Sizing:

- Use explicit integer contract quantities, not a synthetic spread symbol.
- Default pair is `1` GC contract against `2` SI contracts. The ratio reflects
  approximate futures notional balance under recent price levels while keeping
  behavior simple and inspectable.
- Candidate parameters may vary the contract ratio, but the first Route D grid
  keeps sizing fixed and varies only signal windows/thresholds.

## Research Matrix

Backtest config:

- roots: `GC`, `SI`
- symbols: `GC`, `SI`
- timeframe: `1d`
- initial cash: `100000`
- costs: `2.50` fixed commission per contract plus `0.25` bps slippage
- roll policy: first notice date, three sessions before first notice

Windows:

- `is_2020_2022`: 2020-01-01 to 2022-01-01
- `validation_2022_2024`: 2022-01-01 to 2024-01-01
- `holdout_2024_2026`: 2024-01-01 to 2026-04-10, report-only
- `anchor_2010_2020`: 2010-06-06 to 2020-01-01

Candidate grid:

- `ratio_20_entry15_exit025_1x2`
- `ratio_60_entry15_exit025_1x2`
- `ratio_60_entry20_exit050_1x2`
- `ratio_120_entry20_exit050_1x2`

## Promotion Boundary

Route D can only produce research/backtest evidence. A passing candidate would
still require:

- exact promotion packet
- paper runtime config review
- risk/capital limits
- paper full-chain and soak evidence
- operations and risk signoff

No paper/live config changes are part of this design.
