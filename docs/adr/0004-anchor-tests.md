# ADR 0004: Anchor Tests

## Decision

Use anchor tests for financial/domain correctness invariants.

## Rationale

Trading systems can run without throwing errors while being financially wrong. Anchor tests lock domain facts that must survive refactors.
