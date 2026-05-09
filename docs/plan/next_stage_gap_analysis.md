# Next Stage Gap Analysis

## Ranked Follow-Up Backlog

1. Replace local JSONL market data skeleton with a true parquet engine behind `MarketDataStore`.
2. Add real broker-specific paper/live adapter orchestration for IBKR market data and execution.
3. Expand PaperRuntime from construction skeleton to a long-running actor supervisor.
4. Add persistent API job storage for backtests and runtime sessions.
5. Harden frontend with generated API clients, authentication, and live WebSocket subscriptions.
6. Add advanced risk: leverage, product/instrument limits, and option-specific exposure.
7. Add production deployment secrets handling and environment-specific observability exporters.

## Accepted Current Limitations

- No real-money broker integration is started in this stage.
- Docker files are a local baseline, not production images.
- Frontend is an operational skeleton and intentionally contains no trading logic.
