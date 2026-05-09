# Risk Rules

This module owns pre-trade and trading risk logic.

Rules:

- Risk checks must never be bypassed.
- Risk logic must operate on explicit snapshots or actor-owned state.
- Account-level risk should remain consistent with AccountActor state.
- Product-specific risk should be isolated in rules or models.
- Add anchor tests for financial correctness invariants.
- Do not hide rejected decisions; return explicit RiskDecision results.
