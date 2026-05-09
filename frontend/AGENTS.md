# Frontend Rules

This module implements the web console.

Rules:

- Frontend consumes backend APIs; it must not duplicate trading logic.
- UI state must reflect backend state rather than inventing trade/account state locally.
- Trading actions must call explicit backend APIs.
- Do not hardcode broker-specific assumptions in components.
- Keep account, strategy, order, risk, and system status views separate.
