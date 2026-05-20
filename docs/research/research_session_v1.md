# ResearchSession Facade v1

`ResearchSession` is the notebook/script-friendly entrypoint for research
workflows. It reduces user ceremony but does not create a separate research
runtime.

It may:

- load one YAML config that points at historical data, a base backtest config,
  a research store, and a default optimizer objective;
- expose `ResearchBook` history as bars or pandas `DataFrame` objects;
- discover source-backed factor ideas through `FactorDiscovery`;
- persist and reload human-reviewable `FactorSpec` drafts;
- record notebook/script experiments through manifest-backed
  `ResearchExperimentRecorder`;
- run one backtest by merging notebook-supplied `strategy_params` into the base
  backtest config;
- run a parameter grid through `BacktestPipelineRunner`;
- record and compare existing `ExperimentManifest` records through
  `ExperimentStore`.

It must not:

- parse historical CSV rows directly;
- synthesize bars outside `ResearchBook` / `BarAggregationPipeline`;
- turn web search results into executable factors or strategy behavior;
- turn persisted `FactorSpec` drafts into executable factors or strategy
  behavior;
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

ideas = session.discover_factors(
    "commodity futures momentum carry volatility",
    from_year=2015,
)

spec = session.draft_factor_spec(ideas.ideas[0])
session.save_factor_spec(spec)
saved_specs = session.list_factor_specs()

with session.start_experiment(
    "manual-factor-review",
    strategy_name="manual-review",
    strategy_version="1",
) as recorder:
    recorder.log_params({"lookback": 63})
    recorder.log_metric("rank_ic", "0.08")
    recorder.log_factor_version("momentum", "1")
    recorder.log_dataset_id("research-bars-v1")
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

## Factor Specs

`save_factor_spec(...)`, `save_factor_specs(...)`, `list_factor_specs(...)`,
and `load_factor_spec(...)` operate through `FactorSpecStore` under the research
store:

```text
<research store>/factor-specs/<spec name>.json
```

These files are review artifacts. They do not generate Python factor code and
they are not read by paper/live runtime paths.

## Experiment Recorder

`start_experiment(...)` returns `ResearchExperimentRecorder`, a context manager
for logging manual or notebook research evidence. On successful exit it writes
an `ExperimentManifest` under:

```text
<output root>/experiments/<experiment id>/manifest.json
```

and indexes the manifest in `ExperimentStore`. If the context exits with an
exception, no manifest is recorded. This mirrors Qlib-style recorder ergonomics
while keeping QTS evidence tied to existing manifest/store boundaries.

## Discovery

`discover_factors(...)` delegates to `qts.research.factor_discovery`. It returns
source-backed idea cards and uses the research store for deterministic query
caching. Discovery results are not executable. A candidate must be promoted into
human-reviewed `FactorSpec`, then versioned `qts.factors` code, and evaluated
through the normal research/backtest path before paper or live use.
