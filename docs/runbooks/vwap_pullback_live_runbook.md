# vwap_pullback Live Runbook

## Scope

This runbook applies only to the reviewed `vwap_pullback` strategy ID, exact promoted code version, runtime config, broker account, and capital limits named by the readiness and promotion decisions.

## Pre-Open Checks

- Confirm the strategy status has passed the required promotion gate for the target mode.
- Confirm risk limits match the reviewed readiness decision.
- Confirm paper reconciliation evidence has no unexplained cash, position, order, or fill drift.
- Confirm alert routing and monitoring checks were recorded for the same strategy/config.
- Confirm the operator on duty has access to broker, runtime logs, metrics, and rollback controls.

## Kill Switch

- Disable new strategy intents for `vwap_pullback`.
- Cancel open orders through the approved order-management path.
- Verify order cancellation events and broker state reconciliation.
- Flatten positions only under the approved risk/operations instruction for the affected account.
- Record the time, operator, reason, account state, order state, and follow-up ticket.

## Reconciliation

- Compare broker fills, open orders, cash, and positions against runtime account/order state.
- Treat unexplained drift as a no-go for live approval or continued live operation.
- Attach reconciliation evidence to `artifacts/readiness/vwap_pullback/<date>/paper_live_gate_decision.json`.

## Rollback

- Return the strategy to observation or paper mode through a new promotion/readiness decision.
- Preserve original logs and artifacts; do not rewrite historical runtime evidence.
- Quarantine the strategy when the failure condition indicates possible model, implementation, or operations risk.
