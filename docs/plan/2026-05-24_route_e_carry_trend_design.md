# Route E Carry/Trend Design

## Goal

Explore a production-shaped precious-metals futures strategy that combines a
calendar-spread carry signal with time-series trend confirmation.

## Flow Gate

Flow ID:
- `FLOW-DATA`
- `FLOW-RESEARCH`
- `FLOW-BACKTEST`

Canonical entry:
`PYTHONPATH=backend/src uv run python scripts/run_research.py --config configs/research/vwap.yaml workflow configs/research/workflows/vwap_factor_search.yaml`

Config owner:
Historical data config owns the derived signal dataset; backtest config owns
strategy parameters and replay settings; research workflow config owns windows
and candidate declarations.

Allowed owner:
`qts.data.historical` owns reproducible carry-signal construction,
`examples.strategies` owns Strategy SDK strategy code, and `qts.research`
owns workflow evidence execution.

Iteration point:
Derived signal generation, strategy parameters, candidate grids, and declared
research windows.

Future-data risk:
Carry rows are computed from observed calendar-spread rows and exposed as
session-aligned `1d` signal bars visible at the exchange session close. The
2024-2026 window is report-only and must not tune candidate selection.

## Domain Invariant

Calendar-spread carry is a research signal in this route, not a tradable
instrument. Orders may target only GC/SI continuous futures through Strategy
SDK target APIs. The strategy must not read CSV files, inspect broker symbols,
or trade `GC_CARRY` / `SI_CARRY`.

## Evidence Basis

The route follows durable academic priors:

- commodity futures term structure/carry can contain expected-return
  information;
- trend following has long-horizon evidence across asset classes;
- carry is treated here as a relative own-history signal because GC/SI carry is
  usually negative in the available data.

## Design

`CalendarSpreadCarrySignalDataset` builds one latest observed normalized carry
value per root and exchange session:

```text
carry = observed_calendar_spread_close / front_contract_close
```

The output dataset uses static research instrument IDs:

```text
GC_CARRY -> RESEARCH.CARRY.GC
SI_CARRY -> RESEARCH.CARRY.SI
```

`CarryTrendOverlayStrategy` subscribes to GC/SI tradable assets and the carry
signal assets. It emits `target_percent` only for GC/SI when:

- price momentum exceeds the configured threshold;
- current carry is above or below its own carry lookback mean in the same
  direction;
- volatility-targeted sizing is non-zero.

## Result

Route E does not produce a production-review candidate. The best IS candidate,
`carry_trend_126_20_min0_target15`, reaches 10.54% annualized return and Sharpe
0.92 in 2020-2022, but fails validation in 2022-2024 with -7.56% annualized
return and Sharpe -0.77. Strong 2024-2026 holdout results are report-only and
cannot be used to tune or accept the candidate.
