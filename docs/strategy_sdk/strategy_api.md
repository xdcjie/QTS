# Strategy API

User strategies should focus on research and trading intent.

## User-facing objects

- `Strategy`
- `StrategyContext`
- `AssetRef`
- `DataView`
- `PortfolioView`
- `IndicatorFactory`
- `FactorFactory`
- `Universe`
- `OrderSpec`
- `OrderType`
- target APIs

## Preferred methods

```python
ctx.target_percent(asset, 0.5)
ctx.target_quantity(asset, 100)
ctx.target_value(asset, 50_000)
ctx.rebalance(weights)
ctx.close(asset)
```

These methods emit intents. They do not mutate portfolio state directly.

## Advanced order specs

Strategies that need a non-market order may pass an `OrderSpec` with the
neutral domain `OrderType`. Broker-specific support remains an execution and
risk boundary concern.

```python
ctx.target_quantity(
    asset,
    100,
    spec=OrderSpec(order_type=OrderType.LIMIT, limit_price=Decimal("101.25")),
)
```

## Optional signal path

Strategies may separate forecasts from target construction by emitting
`Signal` values and then running a `PortfolioConstructionModel`.

```python
ctx.emit_signal(
    Signal(
        asset=asset,
        direction=SignalDirection.UP,
        generated_at=bar.end_time,
        horizon=timedelta(days=1),
        source_model="momentum-v1",
    )
)
ctx.construct_targets(EqualWeightSignalPortfolioConstruction())
```

Signals are forecasts, not orders. Portfolio construction emits existing
`TargetIntent` objects, so risk, order management, execution, and account
mutation keep the same ownership path used by direct target APIs. Each
`construct_targets(...)` call consumes the pending signal batch, so strategies
can safely emit and construct once per bar without re-emitting prior signals.

## Strategy callbacks

`Strategy` callback signatures use public SDK and domain value objects:

```python
def initialize(ctx: StrategyContext) -> None: ...
def on_bar(ctx: StrategyContext, bar: Bar) -> None: ...
def on_tick(ctx: StrategyContext, tick: Tick) -> None: ...
def on_timer(ctx: StrategyContext, timer: TimerEvent) -> None: ...
def on_order_update(ctx: StrategyContext, update: OrderUpdate) -> None: ...
def on_fill(ctx: StrategyContext, fill: Fill) -> None: ...
def finalize(ctx: StrategyContext) -> None: ...
```

`TimerEvent`, `OrderUpdate`, and `Fill` are Strategy SDK event types. Strategy
code should not import runtime actors, execution adapters, broker adapters, or
OrderManager internals for callback payloads.

## Indicators

Indicators are created through `ctx.indicator` and are updated by the runtime
from completed strategy-facing bars. Strategy code should read indicator values
inside `on_bar`; it should not call indicator update methods manually.

```python
MA_20 = ctx.indicator.ema(asset, window=20)
ATR_7 = ctx.indicator.atr(asset, window=7)
RSI_14 = ctx.indicator.rsi(asset, window=14)
VWAP = ctx.indicator.session_vwap(asset)
VOL_20 = ctx.indicator.volume_ratio(asset, window=20)
```

Supertrend accepts a Decimal multiplier, for example
`ST_10_3 = ctx.indicator.supertrend(asset, window=10, multiplier=Decimal("3"))`.

## Hidden internals

User strategies must not access:

- Actor runtime
- Order execution adapters
- Market data adapters
- RiskEngine internals
- OrderManager internals
- ContractSpec
- BrokerSymbolMapping
