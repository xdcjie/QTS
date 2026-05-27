# Research Idea Registry

The idea registry tracks hypotheses, economic mechanisms, edge taxonomy, trial
budgets, and lifecycle status. `edge_types` is the canonical edge taxonomy field.

Copy-paste examples:

```bash
PYTHONPATH=backend/src uv run python scripts/run_research.py \
  idea --registry-root runs/research/idea_registry add \
  --idea-payload docs/examples/research/idea.json

PYTHONPATH=backend/src uv run python scripts/run_research.py \
  idea --registry-root runs/research/idea_registry record-trial \
  --idea-id idea-momentum \
  --experiment-id exp-001
```

Use lifecycle statuses such as `idea`, `factor_candidate`,
`strategy_prototype`, `validated_research`, `frozen_forward`, `paper_candidate`,
`rejected`, and `retired`. Trial budget exceeded warnings are evidence for
review; they are not promotion approval.
