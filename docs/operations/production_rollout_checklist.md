# Production Rollout Checklist

- Live config validates broker, account, risk, calendar, kill-switch, market-data, order-execution, and secret references.
- Observation mode completed without real order submission.
- Paper-vs-live comparison report reviewed.
- Reconciliation status is clean or formally accepted.
- Risk limits are production-specific and approved.
- Kill switch drill completed and audited.
- Rollback procedure reviewed by operator.
- Small-capital limit and maximum loss threshold are documented.
- Final readiness report records Go / No-Go.
