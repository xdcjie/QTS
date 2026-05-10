# Broker Disconnect Incident

## Detection

- Broker status changes to disconnected or degraded.
- New order submissions are rejected with broker connectivity reason codes.
- Pending orders lack fresh broker reports past the configured threshold.

## Immediate Action

- Pause live order submission.
- Activate the kill switch if order state is uncertain.
- Preserve logs, audit events, broker timestamps, and reconciliation snapshots.

## Recovery

- Reconnect with the configured execution client ID.
- Replay broker open orders and executions into normalized internal reports.
- Run startup reconciliation. Trading remains disabled while critical drift exists.

## Postmortem

- Record disconnect duration, affected orders, reconciliation result, operator actions, and prevention work.
