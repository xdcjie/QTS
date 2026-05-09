# WebSocket API Design

WebSocket streams are for frontend/external subscribers.

Candidate streams:

- Account snapshots
- Position updates
- Order updates
- Fill updates
- Risk alerts
- Strategy logs
- Market data snapshots
- System health

Do not expose raw internal control channels.
