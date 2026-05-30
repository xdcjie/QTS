# Kill Switch Incident

## ⚠️ Current wiring limitation (until M8/M10 live runtime)

The operator HTTP endpoint `POST /operations/kill-switches` records the
kill-switch state in the control-plane `OperationsService` and returns
`200 OK`, **but it does not yet stop order submission.** In the current build
the control plane (`OperationsService` / `RuntimeLifecycleService`) holds no
reference to a running `RuntimeSession`, so the operator command only mutates an
isolated `KillSwitchRegistry` that no order path consults
(`KillSwitchRegistry.check_order` has no production caller).

The runtime order gate (`RuntimeSafetyController.blocked_reason`) blocks new
orders only on `RuntimeSession._kill_switch_active`, which is set by
`RuntimeSession.activate_kill_switch`. Today that path is reached **only** by:

- the automated reconciliation persistent-drift trigger
  (`PersistentDriftCoordinator` → `activate_kill_switch_via_persistent_drift`),
  which also cancels active orders; and
- the rollback path (`runtime/rollback.py`).

There is therefore **no operator-facing HTTP kill switch that halts a running
runtime yet.** Binding the operator API to the live session is part of the
live-runtime wiring (M8 paper / M10 live; same milestone as the unwired runtime
components in `docs/plan/wiring_deferrals.md`).

### Interim emergency stop

Until the API↔runtime binding lands, an operator emergency stop is:

1. Halt the runtime process directly (process / supervisor stop); and
2. Rely on the automated persistent-drift kill switch for reconciliation-driven
   halts.

Do **not** rely on the HTTP kill switch alone to stop trading until this
limitation is removed. The sections below describe the intended incident flow
once the operator path is bound to the runtime gate.

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
