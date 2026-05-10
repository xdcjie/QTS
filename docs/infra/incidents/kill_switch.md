# Kill Switch Incident

## Detection

- Operator activates global, account, strategy, or instrument kill switch.
- Risk gate rejects new orders with active kill-switch reason codes.

## Immediate Action

- Confirm activation is audited with operator, reason, scope, and timestamp.
- Cancel active orders when configured for the incident scope.
- Notify operators that new orders are blocked.

## Recovery

- Verify pending cancels and fills through broker reconciliation.
- Deactivate only after approval and documented cause resolution.
- Run a small no-order observation period before restoring trading.

## Postmortem

- Record trigger, operator actions, affected orders, cancellation results, and follow-up controls.
