# Optimizer Validation V1

## Scope

`qts.research.optimizer` validation evaluates completed optimizer results after
each run has produced a QTS backtest manifest.

It may:

- apply metric constraints to `OptimizationResult` manifests;
- record accepted and rejected optimizer runs with reasons;
- describe deterministic walk-forward train/test windows;
- rerun selected backtest-pipeline candidates across those train/test windows;
- apply predeclared failure-window veto gates to selected candidates;
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

## Failure-Window Veto

Failure-window veto validation is a research-only gate for rejecting optimizer
candidates that fail in predeclared adverse market environments. It is designed
for cases where a later favorable period would otherwise offset an earlier
common-failure period in aggregate OOS evidence.

The domain invariant is:

```text
A candidate that fails any predeclared veto window is rejected for promotion.
Later report-only windows must not compensate for, override, or tune away that
failure decision.
```

The correct owner is `qts.research.optimizer` validation. The gate reruns
completed optimizer candidate parameters through the normal `BacktestPipeline`
date-range override path, applies validation constraints to each veto window,
and writes deterministic evidence. It must not change strategy behavior, add
strategy factor filters, create orders or target intents, bypass the normal
backtest pipeline, or alter runtime/risk/execution/account semantics.

The first VWAP research use case treats `[2022-01-01, 2025-01-01)` as the
failure-veto period and `[2025-01-01, 2026-04-10)` as report-only evidence.
This keeps all of calendar year 2024 inside veto evidence and prevents
2025-2026 performance from rescuing candidates that fail in 2022-2024.

Workflow validation may declare:

```yaml
validation:
  failure_window_veto:
    top_n: 3
    require_passing_candidate: true
    output_root: ../../../runs/research/vwap/gc-long/failure-veto
    summary_output: ../../../runs/research/vwap/gc-long/validation/failure-veto.json
    windows:
      - name: failure-2022
        start: 2022-01-01
        end: 2023-01-01
      - name: failure-2023
        start: 2023-01-01
        end: 2024-01-01
      - name: failure-2024
        start: 2024-01-01
        end: 2025-01-01
    constraints:
      - metric: pnl_usd
        operator: ">"
        threshold: "0"
      - metric: max_drawdown
        operator: "<="
        threshold: "0.05"
    report_only_windows:
      - name: report-2025-2026
        start: 2025-01-01
        end: 2026-04-10
```

`windows` are hard veto windows. Each selected candidate is evaluated
independently against every veto window. Any failed veto-window constraint
rejects that candidate. Veto-window PnL, objective value, and drawdown are not
aggregated across windows for the accept/reject decision.

`report_only_windows` are optional evidence windows. They may be rerun and
written to the summary for context, but they are excluded from the veto decision
and must be marked as report-only in the output artifact.

The summary artifact records:

- deterministic candidate identity;
- candidate parameters;
- per-window manifest path and hash;
- per-window accepted/rejected status and reasons;
- accepted and rejected candidate lists;
- aggregate decision status and reasons;
- explicit separation between veto windows and report-only windows.

When `require_passing_candidate` is true and every selected candidate is
rejected by the veto gate, the workflow `optimize` step is blocked. Otherwise
the gate writes evidence without changing optimizer ranking or strategy
behavior.

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
  failure_window_veto:
    top_n: 3
    require_passing_candidate: true
    windows:
      - name: failure-2024
        start: "2024-01-01"
        end: "2025-01-01"
    constraints:
      - metric: pnl_usd
        operator: ">"
        threshold: "0"
```

When present, the CLI applies constraints to the validation summary and records
walk-forward split metadata. The research workflow runner additionally uses
`validation.walk_forward` to rerun the selected top candidates and can write a
separate walk-forward summary artifact. The research workflow runner also uses
`validation.failure_window_veto` to rerun selected top candidates on
predeclared veto windows and can block the workflow when no selected candidate
survives. When `capital_metrics.margin_proxy` or
`capital_metrics.margin_proxy_usd` is present, the summary also records
`return_on_margin_proxy`. Without `validation`, the summary remains
unconstrained and accepts every completed optimizer result.
