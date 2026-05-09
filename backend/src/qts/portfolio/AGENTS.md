# Portfolio Rules

This module owns portfolio/accounting logic, not runtime state ownership.

Rules:

- Account state is ultimately mutated only by AccountActor.
- Broker callbacks must not directly mutate portfolio state.
- Fill accounting must be explicit and tested.
- Add anchor tests for financial accounting formulas.
