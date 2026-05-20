# ResearchSession Facade v1

`ResearchSession` is the notebook/script-friendly entrypoint for research
workflows. It reduces user ceremony but does not create a separate research
runtime.

It may:

- load one YAML config that points at historical data, a base backtest config,
  a research store, and a default optimizer objective;
- expose `ResearchBook` history as bars or pandas `DataFrame` objects;
- discover source-backed factor ideas through `FactorDiscovery`;
- run one backtest by merging notebook-supplied `strategy_params` into the base
  backtest config;
- run a parameter grid through `BacktestPipelineRunner`;
- record and compare existing `ExperimentManifest` records through
  `ExperimentStore`.

It must not:

- parse historical CSV rows directly;
- synthesize bars outside `ResearchBook` / `BarAggregationPipeline`;
- turn web search results into executable factors or strategy behavior;
- simulate fills, mutate account state, or compute portfolio state itself;
- create orders or target intents from research code;
- bypass `BacktestPipeline`, `RiskEngine`, `OrderManagerActor`,
  `ExecutionActor`, or `AccountActor` for executable strategy evidence.

## Config

```yaml
data:
  config: ../data/historical.local.yaml
  catalog: research_futures
  roots: [GC]
  timeframe: 1m
  instrument_ids:
    AAPL: EQUITY.US.NASDAQ.AAPL
backtest_config: ../backtest.gc_si.example.yaml
store: ../../runs/research/quickstart
output_root: ../../runs/research/quickstart/backtests
objective_metric: sharpe_ratio
discovery:
  sources: [semantic_scholar, openalex, crossref, arxiv]
  max_results: 10
```

`data.instrument_ids` is optional. It is needed for static symbol datasets that
do not have a futures chain file. Continuous futures and chain-backed datasets
continue to use the existing historical catalog resolver.

Relative `data.config` and `backtest_config` paths are resolved from the
research config directory when the sibling path exists, otherwise they remain
relative to the process working directory. Relative `store` and `output_root`
paths are always resolved from the research config directory.

## Usage

```python
from datetime import UTC, datetime

from qts.research import HistoryRequest, ResearchSession

session = ResearchSession.from_yaml("configs/research/quickstart.yaml")

bars = session.history_frame(
    HistoryRequest(
        root="GC",
        start=datetime(2010, 6, 6, 22, 0, tzinfo=UTC),
        end=datetime(2010, 6, 6, 22, 5, tzinfo=UTC),
        timeframe="1m",
    )
)

single = session.run_backtest(strategy_params={"quantity": "2"})

results = session.optimize(
    parameters={
        "entry_bar": [1, 2],
        "quantity": ["1", "2"],
    }
)

ideas = session.discover_factors_frame(
    "commodity futures momentum carry volatility",
    from_year=2015,
)
```

`run_backtest(...)` delegates to:

```text
BacktestPipeline.from_yaml(...)
  -> BacktestPipeline.with_strategy_params(...)
  -> BacktestPipeline.build_engine()
  -> BacktestEngine.run_streaming(...)
```

`optimize(...)` delegates to:

```text
ParameterGrid
  -> BacktestPipelineJob
  -> BacktestPipelineRunner.run(...)
```

Therefore the user-facing facade stays aligned with the same backtest path used
by normal CLI and API workflows.

## Compare

`record_manifest(...)`, `list_runs(...)`, `compare_runs(metric)`, and
`compare_frame(metric)` operate on `ExperimentStore` records. They compare
published research evidence only; they do not inspect runtime internals or
derive trading state.

## Discovery

`discover_factors(...)` delegates to `qts.research.factor_discovery`. It returns
source-backed idea cards and uses the research store for deterministic query
caching. Discovery results are not executable. A candidate must be promoted into
versioned `qts.factors` code and evaluated through the normal research/backtest
path before paper or live use.
