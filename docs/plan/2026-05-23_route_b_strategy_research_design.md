# Route B Strategy Research Design

- Owner: QTS platform engineering
- Created: 2026-05-23
- Status: Approved route, implementation plan pending
- Scope: VWAP failure-window repair plus a parallel non-VWAP trend/momentum comparison for GC/SI futures

## Goal

Find or reject a production-eligible GC/SI futures strategy candidate with strong
IS/OOS evidence, post-2020 annualized return above 10%, positive Sharpe,
controlled drawdown, low overfit risk, and a clear path through paper/live
promotion gates.

The current best VWAP candidates are not production-ready. Existing costed
rolling robustness evidence under
`runs/research/vwap/costed-rolling-robustness-2010-2026-15m` shows:

| Candidate | Window | Annual Return | Sharpe | Max DD | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| GC VWAP sigma/mom120 vol13 qty4 | 2020-2022 | -9.54% | -0.81 | 32.51% | Fail |
| GC VWAP sigma/mom120 vol13 qty4 | 2022-2024 | -4.92% | -0.42 | 23.86% | Fail |
| GC VWAP sigma/mom120 vol13 qty4 | 2024-2026 | 31.15% | 1.39 | 16.66% | Pass |
| SI VWAP trend/sigma vol15 qty3 | 2020-2022 | 11.46% | 1.15 | 7.87% | Pass |
| SI VWAP trend/sigma vol15 qty3 | 2022-2024 | -4.54% | -0.59 | 12.33% | Fail |
| SI VWAP trend/sigma vol15 qty3 | 2024-2026 | 36.48% | 1.31 | 14.34% | Pass |

## Flow Gates

### FLOW-RESEARCH

Flow ID: `FLOW-RESEARCH`

Canonical entry:

```bash
PYTHONPATH=backend/src uv run python scripts/run_research.py \
  --config configs/research/vwap.yaml \
  workflow configs/research/workflows/vwap_factor_search.yaml
```

Config owner: `ResearchSession` owns `configs/research/vwap.yaml`;
`ResearchWorkflowConfig` owns workflow YAML.

Allowed owner: `qts.research`, `qts.factors`, `qts.indicators`, reviewed
strategy code under `strategies/research`, `strategies/production`, and
`examples/strategies`, with `scripts/run_research.py` as a thin CLI.

Iteration point: research queries, workflow gate thresholds, strategy
parameters, backtest matrix periods, optimizer grids, report contents.

Future-data risk: high. Window definitions, failure vetoes, OOS summaries, and
candidate selection can expose future data if the workflow allows OOS results to
tune earlier choices.

Required verification: workflow config tests when workflow behavior changes,
`scripts/run_research.py` integration coverage, and manual review that research
artifacts do not promote paper/live behavior.

### FLOW-OPTIMIZER

Flow ID: `FLOW-OPTIMIZER`

Canonical entry: optimizer steps inside the canonical VWAP research workflow or
generic optimizer paths for non-VWAP comparison configs.

Config owner: `qts.research.optimizer` owns parameter grids, constraints,
failure-window vetoes, and walk-forward validation.

Allowed owner: `qts.research.optimizer`, `qts.research.session`, and
`qts.backtest` through `BacktestPipelineRunner`.

Iteration point: candidate parameter space, objective metric, selected top-N,
failure windows, walk-forward splits, capital metrics.

Future-data risk: high. Candidate ranking must use only declared training and
validation windows; true holdout windows are report-only and cannot feed back
into candidate selection.

Required verification: optimizer unit tests if validation logic changes,
integration evidence that candidates run through `BacktestPipelineRunner`, and
deterministic validation artifacts.

### FLOW-BACKTEST

Flow ID: `FLOW-BACKTEST`

Canonical entry: `ResearchSession.run_backtest(...)`,
`BacktestPipelineRunner`, or:

```bash
PYTHONPATH=backend/src uv run python scripts/run_backtest.py \
  --config <backtest-config> --output-dir <runs-dir>
```

Config owner: backtest config, `BacktestPipeline`, and runner owners.

Allowed owner: `qts.backtest`, `qts.runtime`, `qts.strategy_sdk`, `qts.data`,
`qts.registry`, `qts.risk`, `qts.execution`, `qts.portfolio`, `qts.reporting`.

Iteration point: strategy params, historical date range, cost model, replay
clock, warmup, report outputs.

Future-data risk: medium to high. Strategy callbacks must see only completed
bars at visible time; backtest reports must not feed strategy decisions.

Required verification: relevant unit tests, integration tests for backtest flow,
replay determinism/report hash checks when output contracts change, and anchor
tests for sessions/bar intervals if touched.

### FLOW-PROMOTION

Flow ID: `FLOW-PROMOTION`

Canonical entry: human review over recorded research, optimizer, backtest,
paper, and operations evidence.

Config owner: promotion packet, runtime config owners, risk policy owners.

Allowed owner: durable docs/checklists, runtime config owners, risk policy
owners, reviewed strategy code owners, evidence writers.

Iteration point: review status, evidence links, config hashes, capital/risk
limits, account/mode target, rollout/rollback criteria.

Future-data risk: medium. Promotion may use only evidence that existed at review
time; later outcomes require a new review.

Required verification: evidence manifest/hash review, `make check` before
milestone/live readiness when code changed, paper/full-chain/soak evidence
before live, operations/risk signoff.

## Domain Invariants

Domain fact / invariant:
Research and optimizer artifacts are evidence only. They must not create or
enable paper/live trading behavior. Strategy performance claims must come from
the shared backtest path with completed bars, realistic costs, declared windows,
and immutable manifests.

Correct owner or abstraction boundary:
Window declarations and research gates belong in workflow YAML and
`qts.research` owners. Executable runs belong to `BacktestPipeline`. Production
strategy code belongs under reviewed strategy boundaries. Promotion belongs to
`FLOW-PROMOTION`, not research output.

Forbidden shortcut:
Do not tune on 2025-2026 holdout results. Do not use ad hoc VWAP runners. Do
not add VWAP-specific optimizer configs under `configs/optimizer`. Do not
promote research YAML or report output directly into paper/live config.

Required gates / verification:
Use predeclared IS/OOS windows, failure-window vetoes, walk-forward validation,
costed backtests, manifest evidence, guardrails for boundary changes, and
promotion review before paper/live use.

## Research Design

### Lane 1: VWAP Repair

Purpose: repair known VWAP failures without sacrificing 2024-2026 strength.

Starting evidence:

- GC fails 2020-2022 and 2022-2024 in rolling robustness.
- SI passes 2020-2022 but fails 2022-2024.
- Both are strong in 2024-2026, so 2024-2026 must be treated as true holdout.

Allowed changes:

- Research workflow candidate grids.
- Existing `VwapFactorResearchStrategy` parameters.
- Failure-window veto and walk-forward thresholds.
- Cost and sizing assumptions at documented config boundaries.

Not allowed initially:

- New VWAP strategy code before a workflow-only repair attempt.
- Production config changes before promotion evidence exists.

### Lane 2: Non-VWAP Parallel Comparison

Purpose: avoid overfitting one strategy family by testing a structurally
different trend family under the same gates.

Starting candidates:

- `examples.strategies.dual_supertrend:DualSupertrendStrategy`

Execution note: `examples.strategies.gc_si_momentum:GcSiMomentumStrategy` was
audited and fixed to suppress duplicate unchanged targets, but its Route B
matrix was retired from the canonical workflow because the costed run generated
oversized artifacts and remained pathologically high-turnover. It is not an
active comparison lane for this iteration.

Allowed changes:

- Backtest/research configs that run existing example strategies through the
shared backtest path.
- Parameter grids for timeframe, trend windows, ATR sizing, ADX/volume filters,
and costed risk budgets.

Not allowed initially:

- New non-VWAP strategy behavior until baseline comparison evidence shows
existing examples cannot express the needed structure.

## Window Protocol

Candidate selection and repair use only these windows:

| Window | Dates | Role |
| --- | --- | --- |
| IS | 2020-01-01 to 2022-01-01 | Parameter selection and initial filter repair |
| Validation | 2022-01-01 to 2024-01-01 | Failure-window veto and robustness validation |
| Holdout | 2024-01-01 to 2026-04-10 | Report-only true holdout |
| Legacy anchors | 2010-06-06 to 2020-01-01 | Generalization stress tests only |

The holdout cannot change candidate selection. If holdout failure triggers new
research, the workflow must record a new research iteration and re-freeze a new
future holdout.

## Acceptance Gates

A candidate is production-review eligible only if all required gates pass:

| Gate | Minimum |
| --- | --- |
| 2020+ annualized return | Greater than 10% after commission and slippage |
| Holdout annualized return | Greater than 10% after commission and slippage |
| Sharpe | At least 0.70 in each required window; target at least 1.00 |
| Max drawdown | No required window above 20% |
| Trade count | At least 50 trades in each major two-year window |
| Profit factor | Greater than 1.20 in required windows |
| Failure windows | No required failure window with negative PnL |
| Overfit control | Candidate must pass at least one structurally different comparison or cross-symbol transfer check |
| Promotion boundary | No paper/live change without promotion packet |

## Outputs

The implementation should produce:

1. Updated canonical VWAP workflow evidence for route B.
2. Costed backtest matrix artifacts for both lanes.
3. A rolling 2-year robustness summary for 2020-2026 and legacy anchors.
4. A pass/fail research report that explicitly names rejected and accepted
   candidates.
5. If a candidate passes, a promotion packet draft that remains non-executable
   until reviewed.

## Verification Commands

Narrow checks should run first:

```bash
PYTHONPATH=backend/src uv run python scripts/run_research.py \
  --config configs/research/vwap.yaml \
  workflow configs/research/workflows/vwap_factor_search.yaml
```

If workflow/config code changes:

```bash
uv run pytest tests/unit/research/test_research_workflow.py \
  tests/integration/test_run_research_cli.py -q
make guardrails
```

If strategy behavior changes:

```bash
uv run pytest tests/unit/strategies/test_vwap_factor_research.py \
  tests/unit/strategies/test_vwap_regime_pullback.py \
  tests/unit/strategies/test_dual_supertrend.py -q
make guardrails
```

Before claiming production readiness:

```bash
make format
make lint
make guardrails
make typecheck
make test-unit
make test-integration
make test-anchor
```

Before live readiness:

```bash
make check
```

## Self-Review

- No placeholders remain.
- The design preserves the approved route B scope.
- The design does not add forbidden docs directories.
- The design treats 2024-2026 as report-only holdout.
- The design does not promote any strategy to paper/live.
- The design uses existing workflow/backtest owners before proposing new code.
