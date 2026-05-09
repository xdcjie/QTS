# Deployment

Start local-first.

Phases:

1. Local backtest process
2. Local API + IBKR paper runtime
3. Docker Compose for API/runtime/frontend
4. Split workers by account/broker and market data source when needed
5. Production deployment with strict secrets management

Paper and live deployments keep IBKR market data workers separate from IBKR
order execution workers. Backtest and local simulation may use an in-memory
broker simulator, but paper trading targets an IBKR paper account.
