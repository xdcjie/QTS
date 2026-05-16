# Readiness Smoke Matrix

M6-4 fixes readiness as executable smoke gates, not a passive checklist.

## Local CI Gate

Run:

```bash
make readiness-smoke-local
```

Local smokes use deterministic in-process data, simulated execution, and runtime fakes. They must not require a real broker.

| Smoke | Boundary | Required evidence |
| --- | --- | --- |
| `backtest_minimal_single_strategy_single_account` | Backtest engine, single strategy, single account | Backtest manifest, events artifact, `run_id`, order/fill `correlation_id` |
| `backtest_multi_strategy_one_account_conflict_reject` | Deterministic shared runtime topology covering the backtest readiness invariant | Smoke manifest, events artifact, `run_id`, conflict `correlation_id` |
| `backtest_two_accounts_isolation` | Deterministic shared runtime topology covering the backtest readiness invariant | Smoke manifest, events artifact, `run_id`, account-scoped order `correlation_id` |
| `paper_simulated_market_data_to_fill` | Paper simulated market data through fill/account path | Smoke manifest, events artifact, `run_id`, fill `correlation_id` |
| `live_observation_market_data_no_orders` | Live observation mode with disabled execution | Smoke manifest, events artifact, `run_id`, blocked-order `correlation_id` |
| `live_permission_off_blocks_order` | Live mode with order permission withheld | Smoke manifest, events artifact, `run_id`, blocked-order `correlation_id` |
| `broker_disconnect_blocks_order` | Broker disconnect lifecycle gate | Smoke manifest, events artifact, `run_id`, blocked-order `correlation_id` |
| `reconnect_requires_reconciliation` | Reconnect lifecycle and reconciliation gate | Smoke manifest, events artifact, `run_id`, reconciliation failure and blocked-order `correlation_id` |

## External IBKR Paper Gate

Run only from an operator-controlled paper broker environment:

```bash
QTS_RUN_EXTERNAL_READINESS_SMOKES=1 make readiness-smoke-external
```

The external matrix is marked `external` and skipped unless `QTS_RUN_EXTERNAL_READINESS_SMOKES=1` is set. Local CI must not require these broker smokes.

| Smoke | Boundary | Required evidence |
| --- | --- | --- |
| `paper_broker_gateway_market_data_anchor` | IBKR paper Gateway market-data observation | Manifest path, events artifact, `run_id`, market-data `correlation_id` |
| `paper_broker_submit_cancel_drill` | IBKR paper non-marketable submit/cancel drill | Manifest path, events artifact, `run_id`, order lifecycle `correlation_id` |

External evidence files are read from `--evidence-dir` and must be named `readiness-smoke-*.json`.
