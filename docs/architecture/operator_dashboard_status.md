# Operator Dashboard Status

The operator dashboard status surface is owned by application DTOs and the
operations application service. API routes may map those DTOs into HTTP
payloads, but they must not expose actor objects, mutable runtime stores,
WebSocket stream DTOs, or runtime event envelopes directly.

Each dashboard status slot is represented as a timestamped field. The minimal
operator status includes runtime state and mode, order permission state, broker
connection state, market data permission state, stale subscriptions, open
orders, positions, cash, kill-switch state, last reconciliation result,
unresolved broker callbacks, event sink evidence, and latest manifest evidence.

Stale subscriptions, reconciliation drift, and unresolved broker callbacks are
operator-visible problem states. They must produce explicit timestamped alerts
in the application DTO before API mapping.
