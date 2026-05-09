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
