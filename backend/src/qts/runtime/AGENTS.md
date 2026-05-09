# Runtime Rules

This module contains actor, event routing, clock, and event-store infrastructure.

Rules:

- Actor-to-actor coordination must use message passing.
- Do not directly call another actor's business methods.
- Actor-owned state must only be mutated by the owning actor.
- Preserve per-key ordering for account, order, strategy, market data, and execution flows.
- Use correlation_id and causation_id for traceable event chains.
- Add integration tests for cross-actor flows.
