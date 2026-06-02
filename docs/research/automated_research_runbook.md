# Automated Research OS Runbook

This runbook defines the canonical research automation path. The invariant is:
research automation produces evidence for human review; it must not launch
paper or live trading.

## Quickstart smoke

Run the fixture-backed quickstart workflow from the repository root:

```bash
PYTHONPATH=backend/src uv run python scripts/run_research.py --config configs/research/quickstart.yaml workflow configs/research/workflows/quickstart.yaml --manifest configs/research/manifests/quickstart.yaml
```

The workflow is expected to produce a backtest summary, optimizer summary,
validation summary, artifact hashes, `research_index.json`, and
`research_dashboard.md` under the configured research output root.

## Canonical path

1. Data: use fixture, sample, or approved historical data configured by
   `ResearchSessionConfig`.
2. Manifest: declare the data roots, output root, required artifacts, and hash
   policy in `ResearchManifestV2`.
3. Workflow: execute through `scripts/run_research.py --config ... workflow ...`
   with `--manifest`.
4. Backtest: route through `BacktestPipeline`; do not add a research-only
   trading path.
5. Optimize: consume the backtest config and record ranked candidates.
6. Validation: write validation and walk-forward verdict artifacts through their
   owning validation objects.
7. Evidence bundle: write stable hashes, summary JSON, `research_index.json`,
   and dashboard links.
8. Promotion review: prepare review evidence only. Paper/live launch remains a
   separate manual decision outside this workflow.

## Template workflows

Factor-only review workflow:

```bash
PYTHONPATH=backend/src uv run python scripts/run_research.py --config configs/research/quickstart.yaml workflow configs/research/workflows/factor_only_template.yaml --manifest configs/research/manifests/quickstart.yaml
```

Strategy-parameter workflow:

```bash
PYTHONPATH=backend/src uv run python scripts/run_research.py --config configs/research/quickstart.yaml workflow configs/research/workflows/strategy_parameter_template.yaml --manifest configs/research/manifests/quickstart.yaml
```

## AI review checklist

Before accepting an automated research run, verify:

1. The command entered through `scripts/run_research.py --config ... workflow ... --manifest ...`.
2. Data roots and output roots came from `ResearchSessionConfig` and `ResearchManifestV2`.
3. The workflow produced backtest, optimizer, validation, artifact hash, index, and dashboard evidence.
4. No paper/live launch, broker order, account mutation, or deployment side effect occurred.
5. Reviewed factors were converted only into implementation tasks, not executable modules.
6. Required readiness gates include the quickstart workflow smoke and research workflow smoke tests.
