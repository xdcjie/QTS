# Backtest / Paper / Live Parity

## Goal

Backtest, paper, and live are execution modes of the same trading system.
They must share core domain rules, resolver boundaries, actor flow, order state
ownership, risk checks, and account mutation semantics.

Only external boundaries may differ: data source, broker adapter, clock, latency,
credentials, connectivity, persistence, and external broker capabilities.

## Shared Core Flow

```mermaid
flowchart LR
  Strategy["Strategy SDK"] --> Context["StrategyContext"]
  Context --> Intent["TargetIntent / AssetRef"]
  Intent --> Resolver["Instrument / Symbol / Roll Resolution"]
  Resolver --> Risk["RiskEngine"]
  Risk --> OM["OrderManagerActor"]
  OM --> Exec["ExecutionActor"]
  Exec --> Adapter["ExecutionAdapter"]
  Adapter --> Report["ExecutionReport"]
  Report --> OM
  OM --> Account["AccountActor"]
  Account["AccountActor"] --> Portfolio["Portfolio / Account Snapshot"]
```

## Mode-Specific Boundaries

`historical`/`realtime` and `backtest`/`paper`/`live` are separate concepts.
The first axis describes the market data source's temporal delivery model. The
second axis describes the execution mode and adapter set. Backtests normally
consume historical replay, but historical market data configuration belongs to
the data source boundary, not to the backtest mode boundary.

| Concern | Shared Core | Backtest | Paper | Live |
| --- | --- | --- | --- | --- |
| Strategy API | `Strategy`, `StrategyContext`, `TargetIntent` | same | same | same |
| Symbol identity | `InstrumentId`, `InstrumentRegistry` | same | same | same |
| Roll resolution | `FutureRollRegistry` or compatible contract | historical-derived selections | adapter/precomputed selections | live/precomputed selections |
| Risk | `RiskEngine` + rules | same | same | same |
| Order lifecycle | `OrderManagerActor` | same | same | same |
| Execution actor | `ExecutionActor` | same | same | same |
| Execution adapter | `ExecutionAdapter` protocol | simulated/backtest adapter | paper broker adapter | live broker adapter |
| Account mutation | `AccountActor` only | same | same | same |
| Market data | logical subscriptions, physical source subscriptions, `Bar`/`Tick`/`Quote`, aggregation, fan-out | historical/replay source | paper source | live source |
| Clock | runtime time source | replay clock | paper clock | live clock |

## Required Invariants

- Strategy code emits intents only; it must not create orders directly.
- Risk checks must run before order submission in every mode.
- Order state is owned by `OrderManagerActor` in every mode.
- Account cash and positions are owned by `AccountActor` in every mode.
- Broker/data-source symbols stay at adapter boundaries.
- Core runtime uses `InstrumentId`, never broker symbols.
- Strategy-requested market data timeframes are logical subscriptions.
- Provider-supported source timeframes are physical subscription capabilities and must not redefine strategy-facing bar semantics.
- Market data aggregation and fan-out semantics are shared across backtest, paper, and live modes.
- Continuous futures are not directly tradable.
- Continuous futures must resolve to concrete contracts before order creation.
- Backtest cannot use a shortcut path that live cannot use.
- Live cannot implement business behavior that cannot be exercised in backtest.

## Allowed Divergence

Divergence is allowed only at these adapter boundaries:

- Market data source.
- Broker execution adapter.
- Clock and scheduling source.
- Latency/fill simulation model.
- Broker connectivity and credentials.
- External broker capability handling.
- Persistence backend, when the domain contract is unchanged.

Every divergence must name the boundary and explain why it is external I/O or
environment-specific.

## Forbidden Patterns

- Calling broker adapters directly from strategy code.
- Mutating account state outside `AccountActor`.
- Creating fills outside normalized `ExecutionReport` handling.
- Having a `BacktestOrderManager` with different lifecycle semantics.
- Having live-only risk logic that backtest skips.
- Creating a backtest-only or live-only market data aggregation path.
- Letting provider bar limitations change requested timeframe semantics.
- Resolving futures roll in `qts.data.historical` only.
- Passing broker symbols through portfolio, risk, order, or strategy internals.
- Using concrete historical fixtures to hardcode product behavior.

## Review Checklist

A PR touching backtest, paper, live, market data, order flow, or symbol resolution
must answer:

- Does this reuse the shared Strategy SDK -> Risk -> OrderManagerActor ->
  ExecutionActor -> AccountActor path?
- If not, is the difference strictly at an adapter boundary?
- Does every external symbol become InstrumentId before entering core logic?
- Do logical market data subscriptions map to deduplicated physical source subscriptions?
- Are requested bars produced through shared aggregation semantics rather than provider-specific shortcuts?
- Are continuous futures resolved to concrete contracts before order creation?
- Are risk and order-state transitions covered by tests?
- Is there an integration or anchor test protecting parity?

## Required Tests

Anchor tests protect domain invariants:

- Continuous futures are not directly tradable.
- Continuous futures resolve to concrete contracts before order creation.
- Risk cannot be bypassed.
- Account state only changes from validated fills.
- Provider source timeframe capability cannot redefine requested bar semantics.

Integration tests protect flow parity:

- Backtest order flow goes through `RiskEngine`, `OrderManagerActor`,
  `ExecutionActor`, and `AccountActor`.
- Paper/live adapter tests use the same message contracts.
- Historical and live market data sources use the same actor-facing subscription and event contracts.
- Futures roll changes concrete contracts without changing strategy API.
