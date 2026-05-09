# Deployment Topology

## Local MVP

- One Python process
- In-memory event router
- In-memory broker simulator
- Local data store
- No frontend required initially

## Paper trading

- API process
- Runtime worker process
- IBKR market data worker
- IBKR paper order execution worker
- Persistent event/audit store
- Separate market data and order execution configuration

## Live trading

- API process
- Runtime workers partitioned by account/broker
- IBKR market data workers
- IBKR live order execution workers
- Observability pipeline
- Persistent event store
- Strict secrets management
- Reconnect and reconciliation controls

Do not start with distributed complexity. Preserve architecture boundaries so components can later be split into processes.
