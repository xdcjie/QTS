# Optimizer Validation V1

## Scope

`qts.research.optimizer` validation evaluates completed optimizer results after
each run has produced a QTS backtest manifest.

It may:

- apply metric constraints to `OptimizationResult` manifests;
- record accepted and rejected optimizer runs with reasons;
- describe deterministic walk-forward train/test windows;
- write deterministic JSON validation summaries.

It must not:

- run a vectorized optimizer path;
- bypass `BacktestPipelineRunner` for backtest-config optimization;
- redefine strategy behavior, market data semantics, sessions, instrument
  identity, risk, execution, or account mutation;
- silently drop failed or rejected runs.

## Constraints

`MetricConstraint(metric_name, operator, threshold)` reads the named metric from
the run manifest `statistics` or `metrics` block and compares it with a
`Decimal` threshold. Supported operators are `>`, `>=`, `<`, `<=`, and `==`.

Each evaluation returns a `ConstraintDecision` containing:

- `accepted`: whether the result passed the constraint;
- `reason`: a human-readable acceptance or rejection reason.

Missing or non-Decimal-parseable metrics reject the run with an explicit reason.
The rejected `OptimizationResult` remains part of the validation summary.

## Walk-Forward Metadata

`WalkForwardSplit` records one ordered, non-overlapping train/test window:

```text
train_start < train_end <= test_start < test_end
```

`WalkForwardPlan` requires at least one split and serializes the windows as
ISO-8601 dates. V1 does not alter the optimizer execution path from split
metadata; it provides deterministic validation evidence for workflows that
separate in-sample and out-of-sample evaluation.

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

`OptimizerValidationSummaryWriter` writes JSON with:

- `sort_keys=True`;
- two-space indentation;
- trailing newline.

## CLI

`scripts/run_optimizer.py --validation-output path/to/summary.json` writes the
validation summary after the existing optimizer runner returns ranked results.
The flag does not change factory resolution, `BacktestPipelineRunner`, manifest
generation, result ranking, or the human-readable ranked table.
