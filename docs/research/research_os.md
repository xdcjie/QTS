# Research OS

Research OS is the durable process for turning research ideas into reviewable
evidence without creating trading behavior by accident. It belongs to
`FLOW-RESEARCH` until a human promotion review explicitly moves an exact build,
configuration, account, and risk profile through `FLOW-PROMOTION`.

Research may produce ideas, factor specifications, factor evaluations,
optimizer summaries, backtest evidence, reports, and promotion packets. Research
must not start paper/live runtimes, submit orders, change account state, bypass
risk/order/execution/account actors, or let report artifacts become executable
strategy behavior.

## Evidence Discipline

Every research claim needs reproducible evidence. A research record should name:

- the question or hypothesis;
- datasets, symbols, instrument identifiers, sessions, and date windows;
- factor versions, strategy versions, parameter grids, and config hashes;
- the command that produced the artifact;
- artifact paths, manifest paths, and relevant hashes;
- acceptance criteria and rejection criteria known before evaluation;
- failures, exclusions, manual interventions, and follow-up questions.

Evidence must be recorded before claims are made. Later evidence may invalidate
or qualify an earlier result, but it must not be backdated into the earlier
decision. Report-only windows and out-of-sample windows may validate or reject a
candidate; they must not tune the same candidate unless a new workflow record is
opened.

CLI examples:

```bash
PYTHONPATH=backend/src uv run python scripts/run_research.py \
  evidence --registry-root runs/research/evidence bundle \
  --workflow-summary runs/research/workflows/example/summary.json

PYTHONPATH=backend/src uv run python scripts/run_research.py \
  idea --registry-root runs/research/idea_registry list

PYTHONPATH=backend/src uv run python scripts/run_research.py \
  meta --output-dir runs/research/meta summary \
  --idea-registry-root runs/research/idea_registry \
  --evidence-registry-root runs/research/evidence \
  --period monthly \
  --period-start 2026-05-01
```

## Idea Governance

Ideas enter Research OS as non-executable `FactorSpec` drafts or research notes.
Accepted ideas are permission to continue research, not permission to trade.

Idea records should identify:

- source material or rationale;
- expected economic mechanism;
- observable inputs available at decision time;
- target universe and asset class;
- expected holding horizon and rebalance cadence;
- known crowding, capacity, transaction-cost, or regime risks;
- owner and reviewer.

Generated text, web search results, notebooks, and factor drafts must not become
executable factor or strategy code without human review of the code boundary,
data timing, and risk implications.

## No-Lookahead Factor Protocol

Factor work must separate feature construction from labels. Factor scores are
computed from data available at the factor `as_of` time. Forward returns,
future volatility, post-close values, later membership, and report statistics are
labels or diagnostics only.

Required behavior contract:

- bars use `[start, end)` intervals and become strategy-visible only at `end`;
- intraday bars are clock-aligned in exchange timezone;
- daily bars are session-aligned, not fixed 24-hour windows;
- train, validation, OOS, and report-only windows are declared before use;
- universe membership and survivorship rules are stated explicitly;
- missing returns, stale prices, and halted sessions are recorded as evidence;
- factor ties, ranking, bucket sizing, and turnover rules are deterministic.

The forbidden shortcut is allowing easier dataframe availability to redefine
truth. If a value would not have been known at decision time, it cannot
contribute to a factor score for that time.

## Ablation

Ablation is required before treating a factor or strategy result as durable
evidence. At minimum, research should compare the full candidate against:

- no-factor or neutral baseline;
- single-component removals for composite factors;
- transaction-cost and slippage stress;
- universe and session variants where relevant;
- parameter sensitivity around the selected value;
- stale-data and missing-data behavior;
- failure-window or adverse-regime slices.

An ablation result should explain what part of the result survives when the
favored assumption is removed. If performance depends on one narrow setting,
that is evidence of fragility unless the mechanism explains why the setting is
stable.

Backtest-matrix summaries can feed ablation without rewriting completed runs:

```yaml
kind: ablation
source_summary: matrix-summary.json
baseline: baseline
primary_metric: sharpe_ratio
module_map:
  candidate_a: [mom_filter]
```

## Trade Diagnostics

Backtest evidence should include trade-level diagnostics, not only aggregate
PnL. Diagnostics should cover:

- order count, fill count, cancels, rejects, and unfilled intents;
- exposure by instrument, sector/root, side, and session;
- turnover, holding period, and rebalance timing;
- realized costs, slippage assumptions, and sensitivity;
- drawdown path, loss clusters, and tail days;
- risk-limit interactions and kill-switch behavior when applicable;
- reconciliation between strategy intents, orders, fills, account state, and
  reported portfolio state.

Diagnostics must identify whether a result comes from signal quality,
implementation assumptions, execution assumptions, or accounting effects.

## Validation Gates

Research OS gates are explicit checkpoints. A candidate should not advance when
required evidence is missing.

Required gates:

- **Idea review:** mechanism, inputs, universe, timing, and owner are recorded.
- **Data gate:** datasets, sessions, `[start, end)` semantics, gaps, and
  instrument resolution are documented.
- **No-lookahead gate:** features, labels, windows, and visibility times are
  separated and testable.
- **Factor evaluation gate:** rank IC, spread, coverage, turnover, missing
  symbols, and deterministic artifacts are recorded where applicable.
- **Ablation gate:** baseline, component removal, cost stress, and sensitivity
  evidence are recorded.
- **Backtest gate:** executable evidence runs through the shared backtest path,
  not a research-only trading path.
- **Diagnostics gate:** trade, exposure, cost, risk, and failure-window evidence
  are available.
- **Promotion gate:** a human review decides whether evidence may support paper
  or live consideration.

## Promotion Boundary

Research evidence is not paper/live/production approval. Research evidence !=
paper/live/production behavior.

Promotion requires the `FLOW-PROMOTION` review described in
`docs/research/promotion.md`. A Go decision authorizes only the exact reviewed
build, config hash, account, strategy set, capital limits, and runtime mode. Any
code change, config change, account change, risk-limit change, or target-mode
change requires a new review.

## Meta-Research Feedback Loop

Research OS also tracks the quality of the research process. After each work
package or promotion decision, record feedback on:

- hypotheses that repeatedly fail and why;
- factors that looked strong before costs, ablation, or diagnostics;
- data-quality issues that consumed research time;
- review comments that should become future gates;
- false positives, false negatives, and stale assumptions;
- commands or artifacts that were hard to reproduce.

Meta-research feedback should tighten future work-package acceptance criteria,
required evidence, and validation commands. It should not retroactively change
the result of a completed research workflow.
