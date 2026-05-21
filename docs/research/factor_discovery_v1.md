# Factor Discovery V1

`qts.research.factor_discovery` is the research-only boundary for discovering
source-backed factor ideas from scholarly metadata. It is designed for
notebooks and scripts through `ResearchSession.discover_factors(...)`.

It may:

- search Semantic Scholar, OpenAlex, Crossref, and arXiv metadata APIs;
- cache query results under the research store for reproducibility;
- return idea cards with title, abstract, year, authors, citations, source URL,
  and heuristic candidate tags;
- rank and cap source results by market-research relevance before drafting
  candidates;
- expose notebook-friendly pandas `DataFrame` output.

It must not:

- generate executable factor code;
- create orders, targets, fills, portfolio state, or account state;
- call broker, execution, risk, runtime actor, paper, or live adapters;
- bypass `qts.factors`, `FactorEvaluation`, `BacktestPipeline`, or
  `BacktestPipelineRunner`.

## Query

```python
from qts.research import ResearchSession

session = ResearchSession.from_yaml("configs/research/quickstart.yaml")

ideas = session.discover_factors(
    "commodity futures momentum carry volatility",
    sources=("semantic_scholar", "openalex", "crossref", "arxiv"),
    max_results=10,
    from_year=2015,
)

frame = ideas.to_pandas()
```

`ResearchSession.discover_factors_frame(...)` is a convenience wrapper around
`discover_factors(...).to_pandas()`.

`ResearchSession.find_factor_candidates(...)` is the one-call workflow for
turning a discovery query into persisted review artifacts:

```python
batch = session.find_factor_candidates(
    "commodity futures momentum carry volatility",
    from_year=2015,
)

candidate_frame = batch.to_pandas()
```

This delegates to `FactorDiscovery`, drafts each idea through
`FactorSpecDrafter`, and persists each draft through `FactorSpecStore`.
The returned `FactorCandidateBatch` is a research queue, not executable factor
logic.

## Cache

`FactorIdeaStore` writes deterministic JSON cache files under:

```text
<research store>/factor-ideas/<query hash>.json
```

The query hash includes query text, source list, max result count, and optional
year bounds. Repeating the same query returns the cached result unless
`refresh=True` is passed.

## Relevance Ranking

Discovery combines results from the configured sources, deduplicates by
`idea_id`, and then applies a deterministic market-research relevance score.
For queries that include trading terms such as `VWAP`, `futures`, `market
microstructure`, `order flow`, `returns`, or `commodity`, the result set keeps
ideas with finance/trading context and drops obvious off-topic metadata matches
such as medical or generic NLP papers that only matched a broad word like
`volume`.

The final result is capped after relevance ranking by `max_results`. This keeps
notebook review queues small and makes workflow output deterministic. Ranking is
for triage only; it does not imply that an idea is implemented, reviewed, or
promoted.

## Idea Cards

Each `FactorIdea` contains:

- `idea_id`: stable source-prefixed id;
- `source`: scholarly metadata source;
- `external_id`: provider paper/work id or DOI;
- `title`, `abstract`, `url`, `year`, `authors`, `citation_count`;
- `candidate_tags`: heuristic tags such as `momentum`, `reversal`,
  `volatility`, `carry`, `value`, `quality`, `sentiment`, `liquidity`,
  `volume`, `order_flow`, `regime`, `seasonality`, or `macro`.

Candidate tags are hints for triage only. They do not define a factor contract.

## Candidate Workflow

The candidate workflow preserves the source query, idea metadata, drafted spec,
spec path, and review status in notebook-friendly rows. It is intended to make
paper-backed research triage fast while keeping promotion explicit.

The allowed path is:

```text
web-backed FactorIdea
  -> persisted FactorCandidateBatch
  -> FactorSpec review decision
  -> human implementation as versioned qts.factors code
  -> FactorEvaluation / ExperimentManifest evidence
  -> shared BacktestPipeline
  -> paper/live only after reviewed code is used by strategies
```

An `accepted` review decision means the hypothesis is worth implementation or
further testing. It is not runtime promotion, does not generate Python factor
code, and is not read by paper/live execution paths.

## Promotion Path

The allowed promotion path is:

```text
FactorIdea
  -> FactorSpec draft
  -> human review
  -> versioned qts.factors implementation
  -> FactorEvaluation artifact
  -> ExperimentManifest / ExperimentStore
  -> ResearchSession.run_backtest(...) or ResearchSession.optimize(...)
```

Paper/live modes may consume only versioned strategy/factor code that has
already passed the same validation path. They must not query the web or derive
runtime behavior directly from `FactorIdea` records.
