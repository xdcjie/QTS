# Broker Adapter Canonical Paths

## Canonical IBKR stack

Production IBKR paper/live wiring uses the official TWS/Gateway API transport
stack only:

| Boundary | Production owner |
|---|---|
| Market-data adapter | `qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter` |
| Market-data transport | `qts.data.transports.ibkr_tws_market_data_transport.IbkrTwsMarketDataTransport` |
| Order-execution adapter | `qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionAdapter` |
| Order-execution transport | `qts.execution.transports.ibkr_tws_order_execution_transport.IbkrTwsOrderExecutionTransport` |

Market data and order execution stay separate adapters, transports, client IDs,
configuration sections, and event streams. Broker SDK objects and broker symbols
remain at adapter/transport boundaries; core runtime, strategy, risk, portfolio,
and domain code use `InstrumentId` and normalized execution/market-data events.

The `ib_async` implementations are experimental validation transports under
`qts.experimental.ibkr`. They are not exported by production transport packages
and are not approved production launch wiring.
