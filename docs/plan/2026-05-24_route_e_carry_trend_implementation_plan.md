# Route E Carry/Trend Implementation Plan

## Objective

Add a reproducible carry/trend research lane for GC/SI without introducing a
backtest-only trading path or making synthetic signal assets tradable.

## Steps

1. Add historical data support for non-chain session-window signal datasets.
2. Add a carry-signal dataset builder and CLI that derive `historical/data/carry.csv`
   from observed GC/SI calendar-spread rows.
3. Add `CarryTrendOverlayStrategy` using Strategy SDK subscriptions and target
   APIs only.
4. Add Route E backtest config and canonical workflow steps.
5. Add regression tests for session-aligned signal bars, carry generation,
   strategy behavior, workflow declaration, and target sizing from signal bars.
6. Generate Route E evidence and reject or promote based on IS/validation first;
   holdout remains report-only.

## Verification Gates

- Focused unit tests for historical config, daily signal bar mapping, carry
  dataset generation, strategy behavior, backtest config, workflow declaration,
  and order-plan sizing.
- Route E workflow subset through `ResearchWorkflowRunner` using the Route E
  steps declared in `configs/research/workflows/vwap_factor_search.yaml`.
- Standard repository checks: `make format`, `make lint`, `make guardrails`,
  `make typecheck`, `make test-unit`, `make test-integration`.
- `make test-anchor` because session-aligned `1d` source handling changed.

## Evidence Summary

The Route E matrix wrote
`runs/research/vwap/route-e/carry-trend-overlay-summary.json` with 16 runs.
No candidate passed the production objective because validation performance was
negative for the candidates that looked strongest in IS or holdout.
