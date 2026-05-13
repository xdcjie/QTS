# Production Rollback Procedure

1. Activate the global kill switch.
2. Pause runtime order submission.
3. Cancel active orders when broker connectivity is healthy.
4. Reconcile open orders, fills, positions, and cash against broker truth.
5. Stop live workers after reconciliation artifacts are written.
6. Deploy the previous approved version.
7. Start in observation mode and verify no real orders can be submitted.
8. Resume paper or live trading only after operator approval.

Rollback evidence must preserve:

- Operator ID, timestamp, and reason.
- Runtime state and event store paths.
- Active order IDs and broker cancel reports.
- Internal account snapshot and broker snapshot.
- Final reconciliation report and any accepted drift classification.
