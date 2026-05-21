# Optimizer Validation V1

## Scope

`qts.research.optimizer` validation evaluates completed optimizer results after
each run has produced a QTS backtest manifest.

It may:

- apply metric constraints to `OptimizationResult` manifests;
- record accepted and rejected optimizer runs with reasons;
- describe deterministic walk-forward train/test windows;
- rerun selected backtest-pipeline candidates across those train/test windows;
- derive research-only capital metrics from completed backtest manifests;
- write deterministic JSON validation summaries.

It must not:

- run a vectorized optimizer path;
- bypass `BacktestPipelineRunner` for backtest-config optimization;
- redefine strategy behavior, market data semantics, sessions, instrument
  identity, risk, execution, or account mutation;
- silently drop failed or rejected runs.

## Constraints

`MetricConstraint(metric_name, operator, threshold)` reads the named metric from
derived capital metrics first, then from the run manifest `statistics` or
`metrics` block, and compares it with a `Decimal` threshold. Supported
operators are `>`, `>=`, `<`, `<=`, and `==`.

Each evaluation returns a `ConstraintDecision` containing:

- `accepted`: whether the result passed the constraint;
- `reason`: a human-readable acceptance or rejection reason.

Missing, non-Decimal-parseable, and non-finite metrics reject the run with
distinct explicit reasons. `NaN`, `Infinity`, and `-Infinity` are not valid
constraint inputs, even when a comparison such as `>=` would otherwise accept
the value. The rejected `OptimizationResult` remains part of the validation
summary.

## Walk-Forward Validation

`WalkForwardSplit` records one ordered, non-overlapping train/test window:

```text
train_start < train_end <= test_start < test_end
```

`WalkForwardPlan` requires at least one split, unique split names, and an
ordered non-overlapping sequence across splits. A later split must not start
before the prior split's `test_end`.

`BacktestWalkForwardValidationRunner` takes selected optimizer candidate
parameters and reruns them through `BacktestPipeline` for each split phase. It
changes only the backtest date range and strategy parameters; market data,
instrument resolution, risk, execution, account state, and reporting still come
from the same backtest pipeline as normal optimizer runs.

`WalkForwardValidationSummary` groups the rerun evidence by split and phase,
then applies the same validation constraints and optional capital metrics used
by `OptimizerValidationSummary`.

## Validation Summary

`OptimizerValidationSummary.from_results(...)` records:

- total run count;
- accepted run count;
- rejected run count;
- accepted run evidence;
- rejected run evidence and reasons;
- optional walk-forward split metadata.

Without constraints, V1 records every result as accepted. With constraints, any
failed constraint rejects the run and stores every rejection reason.

When `capital_metric_config` is supplied, the summary may include research-only
capital metrics derived from completed manifests:

- `initial_cash`
- `pnl_usd`
- `net_pnl_usd`
- `gross_pnl_before_recorded_cost`
- `pnl_per_trade`
- `return_on_avg_gross_exposure`
- `return_on_margin_proxy`

These metrics are evidence and validation helpers only. They do not change
backtest account state, fill simulation, risk checks, order handling, or
portfolio accounting.

`OptimizerValidationSummaryWriter` writes JSON with:

- `sort_keys=True`;
- two-space indentation;
- trailing newline.

Optimizer parameter evidence is made JSON-safe before writing. `Decimal`
parameters serialize as strings. Strings, booleans, integers, finite floats,
`null`, lists, and tuples of those values are allowed. Unsupported parameter
values and non-finite numeric parameters raise `ValueError` instead of being
stringified implicitly.

## CLI

`scripts/run_optimizer.py --validation-output path/to/summary.json` writes the
validation summary after the existing optimizer runner returns ranked results.
The flag does not change factory resolution, `BacktestPipelineRunner`, manifest
generation, result ranking, or the human-readable ranked table.

Configs may include optional validation evidence:

```yaml
capital_metrics:
  margin_proxy: "12000"
validation:
  constraints:
    - metric: pnl_usd
      operator: ">"
      threshold: "0"
  walk_forward:
    splits:
      - name: split-1
        train_start: "2026-01-01"
        train_end: "2026-01-15"
        test_start: "2026-01-15"
        test_end: "2026-01-31"
```

When present, the CLI applies constraints to the validation summary and records
walk-forward split metadata. The research workflow runner additionally uses
`validation.walk_forward` to rerun the selected top candidates and can write a
separate walk-forward summary artifact. When `capital_metrics.margin_proxy` or
`capital_metrics.margin_proxy_usd` is present, the summary also records
`return_on_margin_proxy`. Without `validation`, the summary remains
unconstrained and accepts every completed optimizer result.
