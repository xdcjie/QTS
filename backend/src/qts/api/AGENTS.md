# API Rules

This module exposes backend APIs for frontend and external clients.

Rules:

- Do not leak actor internals through public API schemas.
- Use request/response DTOs or schema models.
- API routes should call application services, not mutate domain state directly.
- WebSocket endpoints are for streaming state, logs, market data, order updates, and risk events.
- Never expose secrets, broker credentials, or raw internal control channels.
