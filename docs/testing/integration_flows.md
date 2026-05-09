# Integration Flows

Initial integration tests should cover:

- Bar -> Strategy -> TargetIntent -> AccountActor -> Risk -> OrderManager -> BrokerSimulator -> Fill -> AccountActor
- Multi-strategy signal aggregation
- Order lifecycle with partial fill and cancel
- Broker report normalization
- API starts a backtest and returns status/results
- IBKR paper market data flow with fake transport: subscription -> normalized tick/quote/bar -> MarketDataActor -> StrategyActor
- IBKR paper order flow with fake transport: OrderManager -> ExecutionActor -> order execution adapter -> normalized execution report -> AccountActor

IBKR market data and order execution tests must use separate fake transports so
tests can prove the two boundaries do not call into each other.
