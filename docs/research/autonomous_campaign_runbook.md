# Autonomous Research Campaign Runbook

Campaign automation is a research-only loop. It may generate candidates,
backtests, optimizer evidence, validation packets, and review artifacts, but it
must not launch paper or live trading.

## Quickstart campaign

The checked-in fixture campaign is:

```text
configs/research/campaigns/quickstart_fixture.yaml
```

Validate it before running:

```bash
PYTHONPATH=backend/src uv run python scripts/run_research.py --config configs/research/quickstart.yaml campaign validate configs/research/campaigns/quickstart_fixture.yaml
```

Run the campaign:

```bash
PYTHONPATH=backend/src uv run python scripts/run_research.py --config configs/research/quickstart.yaml campaign run configs/research/campaigns/quickstart_fixture.yaml
```

Inspect and control an active campaign with:

```bash
PYTHONPATH=backend/src uv run python scripts/run_research.py --config configs/research/quickstart.yaml campaign status configs/research/campaigns/quickstart_fixture.yaml
PYTHONPATH=backend/src uv run python scripts/run_research.py --config configs/research/quickstart.yaml campaign verify configs/research/campaigns/quickstart_fixture.yaml
PYTHONPATH=backend/src uv run python scripts/run_research.py --config configs/research/quickstart.yaml campaign approve-next-generation configs/research/campaigns/quickstart_fixture.yaml
PYTHONPATH=backend/src uv run python scripts/run_research.py --config configs/research/quickstart.yaml campaign stop configs/research/campaigns/quickstart_fixture.yaml
PYTHONPATH=backend/src uv run python scripts/run_research.py --config configs/research/quickstart.yaml campaign resume configs/research/campaigns/quickstart_fixture.yaml
```

## Operator checklist

1. Budgets: confirm max generations, max trials, and wall-clock limits before run.
2. Approval mode: confirm review gates before moving to the next generation.
3. Data-path mapping: confirm fixture or historical roots match the manifest.
4. Selector replay: preserve selector decisions and reviewed candidate records.
5. Verification: require validation summaries and artifact hashes for each
   candidate promoted to review.
6. Paper/live disabled: confirm campaign output is evidence-only and does not
   enter broker, execution, account, or live runtime paths.
