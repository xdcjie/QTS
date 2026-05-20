# Factor Discovery V1

`qts.research.factor_discovery` is the research-only boundary for discovering
source-backed factor ideas from scholarly metadata. It is designed for
notebooks and scripts through `ResearchSession.discover_factors(...)`.

It may:

- search Semantic Scholar, OpenAlex, Crossref, and arXiv metadata APIs;
- cache query results under the research store for reproducibility;
- return idea cards with title, abstract, year, authors, citations, source URL,
  and heuristic candidate tags;
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

## Cache

`FactorIdeaStore` writes deterministic JSON cache files under:

```text
<research store>/factor-ideas/<query hash>.json
```

The query hash includes query text, source list, max result count, and optional
year bounds. Repeating the same query returns the cached result unless
`refresh=True` is passed.

## Idea Cards

Each `FactorIdea` contains:

- `idea_id`: stable source-prefixed id;
- `source`: scholarly metadata source;
- `external_id`: provider paper/work id or DOI;
- `title`, `abstract`, `url`, `year`, `authors`, `citation_count`;
- `candidate_tags`: heuristic tags such as `momentum`, `reversal`,
  `volatility`, `carry`, `value`, `quality`, `sentiment`, `liquidity`,
  `seasonality`, or `macro`.

Candidate tags are hints for triage only. They do not define a factor contract.

## Promotion Path

The allowed promotion path is:

```text
FactorIdea
  -> human-reviewed FactorSpec / implementation plan
  -> versioned qts.factors implementation
  -> FactorEvaluation artifact
  -> ExperimentManifest / ExperimentStore
  -> ResearchSession.run_backtest(...) or ResearchSession.optimize(...)
```

Paper/live modes may consume only versioned strategy/factor code that has
already passed the same validation path. They must not query the web or derive
runtime behavior directly from `FactorIdea` records.
