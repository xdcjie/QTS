# Backend Rules

Backend source code lives under `backend/src/qts`.

Rules:

- Keep domain logic independent from API, frontend, broker-specific order execution adapters, market data adapters, and storage details.
- Use explicit typed interfaces at module boundaries.
- Do not introduce infrastructure dependencies into pure domain modules.
- Public backend APIs must use DTO/schema objects, not raw internal actor objects.
- Add or update tests under `tests/unit`, `tests/integration`, or `tests/anchor` depending on the change.
