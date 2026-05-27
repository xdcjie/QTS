# Operational Runbook

## Start Backend

Run the local API:

```bash
uv run uvicorn qts.api.app:create_app --factory --host 127.0.0.1 --port 8000
```

## Run Paper Runtime

Construct the paper runtime without broker credentials:

```bash
PYTHONPATH=backend/src uv run python scripts/run_paper.py
```

## Run Backtests

Submit through the API:

```bash
curl -X POST http://127.0.0.1:8000/backtests \
  -H 'content-type: application/json' \
  -d '{"strategy_name":"smoke"}'
```

## Stop

Stop the foreground process with `Ctrl-C`.

## Inspect

Use `/health/liveness`, `/health/readiness`, `/health/startup`, `/strategies`,
`/accounts/{account_id}`, `/orders/{order_id}`, and `/ws/events`.

## Recovery

Use `FileEventStore` JSONL files for local event replay and `InMemorySnapshotStore` for deterministic tests.

## Troubleshooting

- If imports fail, confirm `PYTHONPATH=backend/src`.
- If risk rejects an order, inspect `reason_code`, `reason_text`, `rule_id`, and `checked_at`.
- Do not place real broker credentials in config files.
