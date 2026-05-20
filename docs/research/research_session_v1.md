# ResearchSession Facade v1

`ResearchSession` is the notebook/script-friendly entrypoint for research
workflows. It reduces user ceremony but does not create a separate research
runtime.

It may:

- load one YAML config that points at historical data, a base backtest config,
  a research store, and a default optimizer objective;
- expose `ResearchBook` history as bars or pandas `DataFrame` objects;
- discover source-backed factor ideas through `FactorDiscovery`;
- turn a discovery query into persisted, reviewable factor candidates;
- persist and reload human-reviewable `FactorSpec` drafts;
- record review decisions for persisted factor specs;
- record notebook/script experiments through manifest-backed
  `ResearchExperimentRecorder`;
- aggregate existing factor-evaluation artifacts into a deterministic
  research tearsheet and record it through `ExperimentStore`;
- run one backtest by merging notebook-supplied `strategy_params` into the base
  backtest config;
- run a parameter grid through `BacktestPipelineRunner`;
- record and compare existing `ExperimentManifest` records through
  `ExperimentStore`.

It must not:

- parse historical CSV rows directly;
- synthesize bars outside `ResearchBook` / `BarAggregationPipeline`;
- turn web search results into executable factors or strategy behavior;
- turn factor candidates or accepted review decisions into executable factors
  or strategy behavior;
- turn persisted `FactorSpec` drafts into executable factors or strategy
  behavior;
- turn a factor-evaluation tearsheet into executable factors or strategy
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
from pathlib import Path

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

candidates = session.find_factor_candidates(
    "commodity futures momentum carry volatility",
    from_year=2015,
)
candidate_frame = candidates.to_pandas()

session.review_factor_spec(
    candidates.specs[0].name,
    decision="accepted",
    reviewer="researcher@example.com",
    notes=("source reviewed",),
)
review_queue = session.review_queue_frame()

with session.start_experiment(
    "manual-factor-review",
    strategy_name="manual-review",
    strategy_version="1",
) as recorder:
    recorder.log_params({"lookback": 63})
    recorder.log_metric("rank_ic", "0.08")
    recorder.log_factor_version("momentum", "1")
    recorder.log_dataset_id("research-bars-v1")

record = session.record_factor_tearsheet(
    [
        Path("runs/research/evaluations/2026-01-02-momentum-1.json"),
        Path("runs/research/evaluations/2026-01-03-momentum-1.json"),
    ],
    experiment_id="momentum-v1-tearsheet",
    dataset_ids=("research-bars-v1",),
)
ranked = session.compare_frame("mean_rank_ic")
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

## CLI

`scripts/run_research.py` is a thin CLI over `ResearchSession`.

```bash
uv run python scripts/run_research.py \
  --config configs/research/quickstart.yaml \
  factor-tearsheet \
  runs/research/evaluations/2026-01-02-momentum-1.json \
  runs/research/evaluations/2026-01-03-momentum-1.json \
  --experiment-id momentum-v1-tearsheet \
  --dataset-id research-bars-v1

uv run python scripts/run_research.py \
  --config configs/research/quickstart.yaml \
  runs --sort-by mean_rank_ic
```

The `factor-tearsheet` command only consumes existing factor-evaluation JSON
artifacts. It writes:

```text
<output root>/experiments/<experiment id>/artifacts/<factor>-<version>-tearsheet.json
<output root>/experiments/<experiment id>/manifest.json
<research store>/experiments.jsonl
```

It does not compute factors, read historical CSV files, run a backtest, create
target intents, or touch runtime/account/order state.

## Compare

`record_manifest(...)`, `list_runs(...)`, `compare_runs(metric)`, and
`compare_frame(metric)` operate on `ExperimentStore` records. They compare
published research evidence only; they do not inspect runtime internals or
derive trading state.

## Factor Tearsheets

`factor_tearsheet(...)` and `factor_tearsheet_frame(...)` aggregate existing
`FactorEvaluationArtifactWriter` JSON files into deterministic per-snapshot rows.
`record_factor_tearsheet(...)` writes a tearsheet artifact, writes an experiment
manifest, and records that manifest in `ExperimentStore`.

Tearsheets are evidence summaries. They can support human review and experiment
comparison, but they are not a promotion mechanism. Paper/live can only use
reviewed factor code through strategies that execute on the normal shared path.

## Factor Specs

`save_factor_spec(...)`, `save_factor_specs(...)`, `list_factor_specs(...)`,
and `load_factor_spec(...)` operate through `FactorSpecStore` under the research
store:

```text
<research store>/factor-specs/<spec name>.json
```

These files are review artifacts. They do not generate Python factor code and
they are not read by paper/live runtime paths.

## Candidate Review Workflow

`find_factor_candidates(...)` composes existing owners:

```text
FactorDiscovery.search(...)
  -> FactorSpecDrafter.draft(...)
  -> FactorSpecStore.save(...)
  -> FactorCandidateBatch
```

The returned batch preserves query metadata, idea metadata, drafted specs,
spec paths, and review status for notebook triage. `find_factor_candidates_frame(...)`
returns the same rows as a pandas `DataFrame`.

`review_factor_spec(...)` records review evidence in `FactorSpecStore` and
updates the persisted spec `review_status`. `list_factor_reviews(...)`,
`list_factor_specs_by_status(...)`, and `review_queue_frame(...)` help users
work through candidates without needing to inspect JSON files.

The allowed promotion path remains:

```text
web-backed FactorIdea
  -> persisted FactorCandidateBatch
  -> FactorSpec review decision
  -> human implementation as versioned qts.factors code
  -> FactorEvaluation / ExperimentManifest evidence
  -> shared BacktestPipeline
  -> paper/live only after reviewed code is used by strategies
```

An `accepted` review decision is not runtime promotion. It does not generate
factor code, does not create target intents or orders, and is not consumed by
paper/live adapters.

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
