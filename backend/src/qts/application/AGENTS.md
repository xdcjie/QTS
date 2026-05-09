# Application Rules

This module orchestrates use cases for API, CLI, and workers.

Rules:

- Application services may coordinate runtime, backtest, registry, and persistence boundaries.
- Keep DTO conversion here or in api schemas, not inside domain models.
- Do not put domain invariants in application services if they belong in domain modules.
