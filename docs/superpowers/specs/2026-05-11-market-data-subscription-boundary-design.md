# Market Data Subscription Boundary Design

## Goal

Establish a shared market data subscription boundary that works the same way for
backtest, paper, and live modes:

- Strategies declare logical market data subscriptions by `InstrumentId` and
  requested timeframe.
- The runtime deduplicates physical provider subscriptions based on provider
  capabilities.
- `MarketDataActor` owns bar aggregation state and fan-out state.
- Historical data, IBKR, and future data providers behave as source adapters
  that push normalized events into the same actor-facing contract.

This design sets the boundary first. It does not require a full rewrite of the
single-strategy `BacktestEngine` in the first implementation increment.

## Domain Rule

Requested timeframe is strategy intent. Source timeframe is provider capability.

Provider limitations must not redefine strategy-facing bar semantics. If IBKR
can provide only `5s` realtime bars for a symbol, a strategy request for `1m`,
`5m`, or `15m` still means internally aggregated bars with the existing
half-open interval semantics. The physical subscription should be one `5s`
subscription for that symbol, and the runtime should derive requested bars from
that stream.

Historical data follows the same rule. If a historical source has `5s` data, it
can satisfy `1m` and larger requests through internal aggregation. If it has
only `1m` data, it can satisfy `1m` and larger compatible requests, but it must
reject `5s` requests explicitly rather than fabricating finer bars.

## Keys And Ownership

Use separate keys for the three separate concepts:

```text
LogicalSubscriptionKey = (instrument_id, requested_timeframe)
PhysicalSubscriptionKey = (source_id, instrument_id, source_stream_type, source_timeframe)
AggregationKey = (instrument_id, source_timeframe, target_timeframe, session_id)
```

Ownership:

- Strategy SDK records logical subscriptions only.
- Market data source adapters expose capabilities and accept physical
  subscriptions only.
- `MarketDataActor` owns logical subscribers, physical subscription dedup state,
  aggregation state, and fan-out state.
- Adapter code normalizes provider symbols to `InstrumentId` before events enter
  runtime actors.

## Market Data Flow

```text
StrategyContext.subscribe(asset, timeframe)
  -> logical subscription request
  -> MarketDataActor resolves provider capability
  -> one physical source subscription per PhysicalSubscriptionKey
  -> provider emits normalized Bar / Tick / Quote
  -> MarketDataActor aggregation chain
  -> fan-out requested timeframe events to subscriber ActorRef mailboxes
```

For IBKR-style providers:

```text
Strategy A requests GC 1m
Strategy B requests GC 5m
Strategy C requests GC 1m

Physical source subscription:
  IBKR GC 5s, once

Derived streams:
  5s -> 1m, fan-out to A and C
  1m -> 5m, fan-out to B
```

The design keeps market data and execution separate. Market data adapters do not
submit, cancel, reconcile, or mutate orders or account state.

## Historical Data Service Boundary

Historical data should be represented as a source service with the same
actor-facing behavior as live data:

- It reads configured historical CSV and chain metadata.
- It resolves source symbols at the data-source boundary.
- It exposes source capabilities, including the minimum available timeframe.
- It accepts physical subscriptions and pushes normalized bars in deterministic
  replay order.
- It records futures roll selections when continuous futures are requested.

The service may reuse existing `HistoricalCatalog`, `HistoricalBarStream`, and
`FutureRollRegistry` code. It should not expose provider/source symbols to
`MarketDataActor`, Strategy SDK, portfolio, risk, order, or execution code.

## Architecture Documents To Update

The implementation should update these long-lived docs so future work follows
the boundary:

- `docs/architecture/system_overview.md`: add logical subscription, physical
  source subscription, aggregation, and fan-out to the market data runtime flow.
- `docs/architecture/backtest_live_parity.md`: state that backtest, paper, and
  live market data differ only by source adapter, not by subscription,
  aggregation, fan-out, or strategy-facing bar semantics.
- `docs/runtime/actor_model.md`: state that `MarketDataActor` owns subscription
  deduplication, aggregation state, and subscriber fan-out state.
- `docs/domain/bar_timeframe_model.md`: state that source timeframe is provider
  capability and requested timeframe is strategy intent; provider capability
  cannot redefine bar interval semantics.
- `docs/testing/domain_invariants.md`: add testable invariants for physical
  subscription deduplication, canonical aggregation, and source capability
  rejection.

## Tests To Add

Anchor tests:

- Add `tests/anchor/test_market_data_subscription_anchors.py`.
- Assert multiple logical subscriptions for the same `InstrumentId` and derived
  timeframe can map to one provider `5s` physical subscription.
- Assert one `5s` source stream can derive `1m` and `5m` logical streams without
  duplicate provider subscriptions.
- Assert requested `1m` bars preserve `[start, end)` semantics even when source
  bars are `5s`.
- Assert a historical source with only `1m` data rejects `5s` requests.
- Assert provider/source symbols do not cross into runtime actor messages or
  Strategy SDK data objects.

Regression and unit tests:

- Extend `tests/unit/runtime/test_market_data_actor.py` for subscription dedup,
  aggregation, and fan-out state.
- Extend `tests/unit/data/test_live_feed_contract.py` for feed capability and
  physical timeframe selection.
- Add `tests/unit/data/test_historical_market_data_service.py` for historical
  source subscriptions and deterministic push behavior.
- Extend `tests/integration/test_backtest_live_parity_flow.py` to prove
  historical and live/fake feeds use the same actor-facing message contract.

## Non-Goals For First Increment

- Do not rewrite the full backtest loop into a multi-strategy runtime.
- Do not add a new production dependency.
- Do not expose provider-specific symbols or IBKR objects to strategy code.
- Do not create a separate backtest-only aggregation path.
- Do not support downsampling from coarse historical data to finer requested
  timeframes.

## Verification

The first implementation increment should run:

```bash
make format
make lint
make typecheck
make test-unit
make test-integration
make test-anchor
```

Because the change affects market data subscription semantics, bar aggregation,
backtest/live parity, and financial domain correctness, the anchor and
integration checks are required.
