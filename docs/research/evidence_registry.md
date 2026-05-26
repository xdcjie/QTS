# Research Evidence Registry

Evidence bundles are immutable research-only references to completed workflow
artifacts. They support human review; they do not enable paper, live, or
production behavior.

Create and verify a bundle:

```bash
PYTHONPATH=backend/src uv run python scripts/run_research.py \
  evidence --registry-root runs/research/evidence bundle \
  --workflow-summary runs/research/workflows/example/summary.json \
  --idea-registry-root runs/research/idea_registry \
  --idea-id idea-momentum \
  --strategy-id strategy-prototype

PYTHONPATH=backend/src uv run python scripts/run_research.py \
  evidence --registry-root runs/research/evidence verify evb_example
```

The bundle records workflow summary, manifest, report, validation, walk-forward,
failure-window, trade diagnostics, and artifact paths with hashes where
available. `--idea-id` requires either `--idea-registry-root` or embedded
workflow `idea_metadata`.

Known failure modes: incomplete evidence bundle, changed artifact hash, missing
manifest-relative artifact path, report-only misuse, and citing research
evidence as promotion approval.
