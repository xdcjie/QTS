# FactorSpec V1

`qts.research.factor_spec` defines human-reviewable factor hypothesis drafts.
It bridges discovered paper/web ideas and versioned factor implementation, but
it is not executable trading behavior.

It may:

- convert a source-backed `FactorIdea` into a structured research hypothesis;
- preserve source references;
- infer draft inputs and data requirements from candidate tags;
- produce deterministic JSON-ready payloads for review and storage.
- persist and reload reviewed draft payloads through `FactorSpecStore`.

It must not:

- generate Python factor code;
- create orders, targets, fills, portfolio state, or account state;
- call broker, execution, risk, runtime actor, paper, or live adapters;
- bypass `qts.factors`, `FactorEvaluation`, `BacktestPipeline`, or
  `BacktestPipelineRunner`.

## Fields

`FactorSpec` contains:

- `name`: stable slug for the draft factor idea;
- `hypothesis`: text statement to be reviewed before implementation;
- `inputs`: draft data inputs such as `close`, `roll_yield`, or
  `news_sentiment`;
- `lookback`, `universe`, and `rebalance`: placeholders requiring researcher
  review;
- `expected_direction`: default scoring convention;
- `data_requirements`: source data needed before evaluation;
- `source_refs`: source-backed references from discovery;
- `candidate_tags`: heuristic tags copied from `FactorIdea`;
- `review_status="draft"`;
- `promotion_gate="human_review_required"`.

## Usage

```python
from qts.research import ResearchSession

session = ResearchSession.from_yaml("configs/research/quickstart.yaml")
ideas = session.discover_factors("commodity futures momentum carry", max_results=5)

spec = session.draft_factor_spec(ideas.ideas[0])
specs = session.draft_factor_specs(ideas)

session.save_factor_spec(spec)
persisted_specs = session.list_factor_specs()
loaded = session.load_factor_spec(spec.name)
```

## Persistence

`FactorSpecStore` writes deterministic JSON under:

```text
<research store>/factor-specs/<spec name>.json
```

The store is a research artifact boundary. It preserves source-backed drafts for
review and follow-up implementation, but it does not promote the draft, generate
factor code, or make the factor available to strategy runtime paths.

## Promotion Path

The allowed path is:

```text
FactorIdea
  -> FactorSpec draft
  -> human review
  -> versioned qts.factors implementation
  -> FactorEvaluation artifact
  -> ExperimentManifest / ExperimentStore
  -> ResearchSession.run_backtest(...) or ResearchSession.optimize(...)
```

Paper/live modes may use only reviewed and versioned strategy/factor code that
has passed the same validation path. They must not consume `FactorSpec` drafts
directly.
