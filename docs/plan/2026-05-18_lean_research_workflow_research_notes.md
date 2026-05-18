# Lean-Inspired Research Workflow Deep Research Notes

- Document type: research notes + design decomposition
- Owner: QTS platform engineering
- Created: 2026-05-18
- Scope: research workflow, factor evaluation, signal/portfolio-construction boundary, optimizer validation
- Status: Planned input for the focused implementation plans listed below

## External References

Official QuantConnect / Lean references reviewed on 2026-05-18:

- Research Environment: `QuantBook`, notebook-first hypothesis testing, history, indicator history, ML model training, and backtest-result analysis.
  <https://www.quantconnect.com/docs/v2/research-environment/key-concepts/getting-started>
- Research universes: `UniverseHistory`, dynamic baskets, top-minus-bottom mini-backtest examples, and futures/options universe history.
  <https://www.quantconnect.com/docs/v2/research-environment/universes>
- Algorithm Framework alpha concepts: `Insight` objects carry direction, magnitude, confidence, suggested weight, and model identity; active insight semantics matter when risk changes targets.
  <https://www.quantconnect.com/docs/v2/writing-algorithms/algorithm-framework/alpha/key-concepts>
- Lean CLI optimizer: parameter grid, objective target, constraints, output directories, and local optimizer execution.
  <https://www.quantconnect.com/docs/v2/lean-cli/api-reference/lean-optimize>
- US Futures research: `FutureHistory`, continuous future history, data mapping, normalization mode, and contract history access.
  <https://www.quantconnect.com/docs/v2/writing-algorithms/datasets/algoseek/us-futures>

## QTS Current State

QTS already has the important production boundaries that Lean's classic `QCAlgorithm`
API does not force as strictly:

- Strategy authors use `qts.strategy_sdk.StrategyContext` and emit target intents through `ctx.target_percent`, `ctx.target_quantity`, `ctx.target_value`, `ctx.rebalance`, and `ctx.close`.
- Runtime path is actor + queue based and must preserve the documented parity chain:
  `Strategy SDK -> TargetIntent -> RiskEngine -> OrderManagerActor -> ExecutionActor -> AccountActor`.
- Historical local data already has cohesive owners:
  `HistoricalCatalog`, `HistoricalBarStream`, `ReplayMarketDataSource`, `BacktestPipeline`, and `BacktestPipelineRunner`.
- Research currently has:
  `ExperimentManifestWriter`, `ParameterGrid`, `OptimizationRunner`, `BacktestPipelineRunner`, `qts.factors` with `FactorWindow` / `FactorResult`, and a `MomentumFactor`.
- Existing docs already freeze the factor public surface under `docs/research/factor_contract_v1.md`.

## What To Borrow From Lean

### Borrow

1. **QuantBook-style read-only research facade**
   Give notebook users one stable entrypoint for historical bars, research windows,
   factor windows, and mini summaries without exposing runtime actors or broker
   internals.

2. **Insight-like signal boundary**
   Keep direct target APIs for simple strategies, but add an optional signal layer
   for multi-alpha workflows:
   `Factor/Alpha -> Signal -> PortfolioConstruction -> TargetIntent`.

3. **Research artifacts as first-class outputs**
   Every factor evaluation and optimizer validation run should write deterministic
   artifacts and an experiment manifest with dataset IDs, factor versions, config
   hash, metrics, and artifact hashes.

4. **Optimizer target + constraint model**
   Keep QTS's stronger parity guarantee by continuing to route optimizer runs through
   `BacktestPipeline`, while adding objective constraints, validation summaries,
   and walk-forward split evidence.

### Do Not Borrow

1. **Do not add a `QCAlgorithm`-style god object**
   QTS must not expose actor, broker, order-manager, risk-engine, or contract-spec
   internals through research or strategy APIs.

2. **Do not allow notebook-owned business rules**
   Notebooks may call production research APIs; they must not define roll rules,
   bar semantics, instrument identity, or portfolio/risk correctness rules.

3. **Do not create a research-only backtest shortcut**
   Mini research summaries can be vectorized, but any claim about executable strategy
   performance must go through the same backtest path used by `scripts/run_backtest.py`
   and `BacktestPipelineRunner`.

## Domain Invariants

| Invariant | Owner | Gate |
|---|---|---|
| Research reads market data; it does not mutate runtime/account/order state. | `qts.research` facade boundaries | Unit tests + import guardrail |
| Continuous futures remain research/data references and resolve to concrete contracts before trading. | `qts.registry.future_roll`, historical/live adapters | Anchor tests for roll/session behavior |
| Factor windows are trailing `[start, end)` slices with explicit missing-data policy. | `qts.factors` and `qts.research.factor_evaluation` | Unit tests for no lookahead and missing-data behavior |
| Signals are not orders. Portfolio construction turns signals into `TargetIntent`; risk/order/execution still own trading. | `qts.strategy_sdk.signals`, `qts.strategy_sdk.portfolio_construction` | SDK tests + integration test for target path |
| Optimizer validation cannot bypass the shared backtest pipeline. | `qts.research.optimizer` | Integration tests around `BacktestPipelineRunner` |
| No new storage dependency is added without benchmark evidence. | `docs/decision/2026-05-10_research_storage_decision.md` | Review gate + storage benchmark if proposed |

## Focused Plan Decomposition

| Plan | Output | Independent Write Scope | Why It Is Subagent-Friendly |
|---|---|---|---|
| RB-1 ResearchBook V1 | Read-only QuantBook-style facade over QTS historical data | `qts.research.research_book`, research docs, tests | Does not modify strategy runtime or optimizer |
| SIG-1 Signal + Portfolio Construction V1 | Optional signal boundary and equal-weight portfolio construction | `qts.strategy_sdk.signals`, `qts.strategy_sdk.portfolio_construction`, SDK docs/tests | Builds on existing `TargetIntent`; independent of factor evaluation |
| FE-1 Factor Evaluation Artifacts V1 | IC, bucket spread, coverage, turnover metrics and manifest artifacts | `qts.research.factor_evaluation`, artifact tests/docs | Uses current `FactorResult`; independent of optimizer runner |
| OPTV-1 Optimizer Validation V1 | Constraints, walk-forward split plan, validation summary artifacts | `qts.research.optimizer.constraints`, `qts.research.optimizer.walk_forward`, CLI tests | Extends optimizer only; no Strategy SDK changes required |

## Recommended Execution Order

1. RB-1 first, because factor evaluation and notebooks need a stable read-only data
   access facade.
2. FE-1 second, because it creates research evidence before signal-to-target
   production wiring.
3. SIG-1 third, because it introduces a new user-facing SDK surface and should be
   informed by the factor-result shape.
4. OPTV-1 fourth, because optimizer validation consumes experiment artifacts and
   should remain downstream of the research contracts.

Each plan has its own file, status entries, and acceptance-evidence requirements.
