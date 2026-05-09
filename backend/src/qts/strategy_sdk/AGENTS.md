# Strategy SDK Rules

This module defines the user-facing strategy API.

Rules:

- Keep the user strategy API simple.
- Do not expose Actor, Broker, RiskEngine, OrderManager, ContractSpec, BrokerSymbolMapping, or internal event routing.
- User strategies should use `Strategy`, `StrategyContext`, `AssetRef`, `DataView`, `PortfolioView`, indicators, factors, universe, schedule, and target APIs.
- Prefer target APIs such as `ctx.target_percent`, `ctx.target_quantity`, `ctx.target_value`, `ctx.rebalance`, and `ctx.close`.
- Direct order APIs are advanced APIs and must still produce intents that pass through Risk and OrderManager.
- Strategy code must not mutate portfolio state directly.
