# Operational Console

## Screens

- Runtime status and controls: backend state from `/operations/runtime/*`.
- Order blotter: backend order endpoints and WebSocket order updates.
- Risk events: backend risk and kill-switch events.
- Operational controls: pause, resume, and kill-switch commands.

## Rules

The console renders backend state and calls explicit APIs. It must not duplicate order, risk,
accounting, reconciliation, or runtime state machines in browser code.
