# Architecture Boundary Review

Date: 2026-05-09

Reviewed boundaries:

- Strategy SDK does not depend on runtime, risk, execution adapters, or actor internals.
- API routes call application services or return public DTO schemas; actor refs and mailboxes are not exposed.
- Data adapters use `InstrumentId` internally and broker symbols only at adapter boundaries.
- Order execution and market data adapters remain separate modules.

Known limitations mapped to this backlog:

- File-backed market data store is a local JSONL-backed skeleton behind the `ParquetMarketDataStore` boundary.
- Paper runtime is a construction/flow skeleton and does not connect to live broker transports.
- Frontend console is an MVP skeleton consuming DTO-shaped data only.

## S3 Boundary Review

Date: 2026-05-10

S3 implementation rules:

- Broker execution contracts live under `qts.execution` and normalize reports before `OrderManager`.
- Live feed contracts live under `qts.data` and emit normalized market data payloads for `MarketDataActor`.
- Reconciliation compares immutable snapshots and returns reports; it does not mutate actor-owned account or order state.
- Operational API routes return DTOs and use a permission hook header; they do not expose actor refs or mailboxes.
- Frontend operational controls call backend APIs only and do not implement trading state machines.
