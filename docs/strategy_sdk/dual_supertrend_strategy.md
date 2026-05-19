# Dual Supertrend Strategy Design

## Status

Approved for implementation planning on 2026-05-19.

## Goal

Add a single-asset Strategy SDK example that implements a configurable dual
Supertrend trend-following template with regime filters and volatility-aware
position sizing, while adding a reusable Supertrend indicator to the internal
indicator library and Strategy SDK indicator factory.

The default example symbol is `GC`. This is a strategy default only; no
Gold-specific product facts, sessions, margin, rolls, or valuation rules belong
in the indicator, Strategy SDK, or shared runtime implementation.

## Research Basis

Supertrend is an ATR-based trend-following indicator. TradingView's published
calculation uses `hl2 +/- multiplier * ATR`, final upper/lower bands, and a
direction switch when close crosses the active band.

Academic and industry trend-following research supports the broader design
choice: trend filters can be represented in many equivalent or related forms,
including time-series momentum and moving-average style filters; robust
implementation depends heavily on costs, risk management, diversification,
position sizing, and volatility control. The first implementation should
therefore separate the reusable indicator from the strategy-specific research
template, and keep all order expression on the Strategy SDK target-intent path.

References:

- TradingView Supertrend formula:
  https://www.tradingview.com/support/solutions/43000634738-supertrend/
- Moskowitz, Ooi, and Pedersen, "Time Series Momentum", Journal of Financial
  Economics 104 (2012):
  https://pages.stern.nyu.edu/~lpederse/papers/TimeSeriesMomentum.pdf
- Hurst, Ooi, and Pedersen, "A Century of Evidence on Trend-Following
  Investing":
  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2993026
- Levine and Pedersen, "Which Trend Is Your Friend?":
  https://www.aqr.com/Insights/Research/Journal-Article/Which-Trend-Is-Your-Friend

## Domain Gate

Domain fact / invariant:

Supertrend is computed only from completed OHLC bars and prior indicator state.
It must not use future bars. Strategy signals may combine several filters, but
orders must be expressed as Strategy SDK target intents so every execution mode
keeps the shared Strategy SDK -> RiskEngine -> OrderManagerActor ->
ExecutionActor -> AccountActor path.

Correct owner or abstraction boundary:

- `qts.indicators.technical.Supertrend` owns the formula, ATR smoothing
  dependency, warmup, direction state, and output value.
- `qts.strategy_sdk.indicators.IndicatorFactory.supertrend(...)` owns only
  strategy-facing construction and runtime-managed update binding.
- `examples.strategies.dual_supertrend.DualSupertrendStrategy` owns the
  research template: fast/slow confirmation, ADX and volume filters, optional
  trading-hours filter, volatility sizing, and software close conditions.

Forbidden shortcut:

- Do not access broker adapters, actors, `RiskEngine`, `OrderManager`,
  `AccountActor`, `ContractSpec`, or `BrokerSymbolMapping` from the strategy.
- Do not update indicators manually inside strategy code; runtime-owned
  `IndicatorFactory.update_from_bar(...)` remains the lifecycle boundary.
- Do not place single-asset time-series signal logic in `qts.factors`, whose
  current boundary is cross-sectional factor computation.
- Do not hardcode product-specific facts such as GC sessions, active months,
  margin, or valuation into the generic indicator or Strategy SDK.

Required gates / verification:

- Unit tests for Supertrend warmup, band calculation, direction flips, and
  deterministic Decimal output.
- Unit tests for `IndicatorFactory.supertrend(...)`, including matching-asset
  update behavior.
- Unit tests for `DualSupertrendStrategy` entries, exits, filters, and target
  sizing.
- A boundary test proving the example strategy imports only allowed SDK/domain
  read-only types and does not call indicator update methods.
- `make guardrails`, plus normal format, lint, typecheck, and unit-test gates.

## Indicator Design

Add these public indicator objects under `qts.indicators.technical`:

```python
@dataclass(frozen=True, slots=True)
class SupertrendValue:
    value: Decimal
    direction: int
    upper_band: Decimal
    lower_band: Decimal


@dataclass(slots=True)
class Supertrend:
    window: int
    multiplier: Decimal = Decimal("3")
```

`direction` is `1` for bullish and `-1` for bearish. The value is the lower
band in bullish state and upper band in bearish state.

Calculation:

```text
hl2 = (high + low) / 2
basic_upper = hl2 + multiplier * ATR
basic_lower = hl2 - multiplier * ATR

final_upper = basic_upper
    if prior final upper is absent
    or basic_upper < prior final upper
    or previous close > prior final upper
    else prior final upper

final_lower = basic_lower
    if prior final lower is absent
    or basic_lower > prior final lower
    or previous close < prior final lower
    else prior final lower

if prior direction is bearish:
    direction = bullish if close > final_upper else bearish
else:
    direction = bearish if close < final_lower else bullish
```

The first value after ATR warmup starts bearish unless the implementation has a
prior direction from restored state in a later snapshot/restore extension. This
matches the common Supertrend convention and avoids inventing a bullish signal
before the first close-cross event.

Validation:

- `window` must be positive.
- `multiplier` must be non-negative.
- All state uses `Decimal`.
- `ready` is true only after a `SupertrendValue` exists.

## Strategy SDK API

Add:

```python
ctx.indicator.supertrend(asset, window=10, multiplier=Decimal("3"))
```

The method returns `AssetIndicator`. `IndicatorValue` must include
`SupertrendValue`.

The factory uses the existing bar-indicator binding. Strategy code reads
`indicator.ready` and `indicator.value`; it does not call `update(...)` or
`update_from_bar(...)`.

## Strategy Design

Add `examples/strategies/dual_supertrend.py` with:

```python
@dataclass(frozen=True, slots=True)
class DualSupertrendConfig:
    symbol: str = "GC"
    timeframe: str = "1m"
    fast_window: int = 10
    fast_multiplier: Decimal = Decimal("2")
    slow_window: int = 20
    slow_multiplier: Decimal = Decimal("4")
    allow_short: bool = True
    base_target_percent: Decimal = Decimal("0.30")
    max_target_percent: Decimal = Decimal("0.50")
    use_adx_filter: bool = True
    adx_window: int = 14
    min_adx: Decimal = Decimal("20")
    use_volume_filter: bool = False
    volume_ratio_window: int = 20
    min_volume_ratio: Decimal = Decimal("1.0")
    use_atr_position_sizing: bool = True
    atr_window: int = 14
    target_atr_fraction: Decimal = Decimal("0.01")
    use_trading_hours_filter: bool = False
    trading_hours_timezone: str = "US/Eastern"
    trading_hours_start: str = "08:00"
    trading_hours_end: str = "16:00"
    stop_atr_multiple: Decimal = Decimal("0")
    trail_atr_multiple: Decimal = Decimal("0")
```

Construction validates positive windows, non-negative thresholds, target caps,
booleans, and half-open time window strings. If `use_trading_hours_filter` is
false, the start/end values are ignored and full session-managed bars are
allowed through.

`DualSupertrendStrategy` owns one asset and the following state:

- previous fast Supertrend direction
- current position side: `0`, `1`, or `-1`
- entry price
- fixed stop price
- trailing stop price

The strategy initializes by resolving `ctx.symbol(config.symbol)`, subscribing
to `config.timeframe`, and creating fast Supertrend, slow Supertrend, ADX, ATR,
and optional volume-ratio indicators.

Entry rules:

- All required indicators must be ready.
- If the trading-hours filter is enabled, `bar.start_time` must be inside the
  configured half-open local time interval `[start, end)`.
- ADX must be at or above `min_adx` when the ADX filter is enabled.
- Volume ratio must be at or above `min_volume_ratio` when the volume filter is
  enabled.
- A long entry requires fast and slow Supertrend direction `1`.
- A short entry requires fast and slow Supertrend direction `-1` and
  `allow_short=True`.
- A new entry is emitted when the fast Supertrend just flipped into the aligned
  direction, or when the strategy is flat and alignment is already present.

Exit rules:

- Long exits on fast Supertrend direction `-1`.
- Short exits on fast Supertrend direction `1`.
- Optional software stop and trailing stop conditions emit `ctx.close(asset)`.
  They do not create broker-native stop orders and do not bypass platform risk.
- If filters later fail while a position is open, the strategy does not close
  solely because a filter failed; filters gate entries, while exits are trend
  failure or optional software risk conditions.

Sizing:

```text
target = base_target_percent
if use_atr_position_sizing and ATR > 0 and close > 0:
    atr_fraction = ATR / close
    target = base_target_percent * target_atr_fraction / atr_fraction
target = min(target, max_target_percent)
```

Long target is `target`; short target is `-target`. This is a single-asset
volatility-targeting approximation for research. Portfolio-level volatility
budgeting remains a later portfolio/risk-layer capability.

## Tests

Unit indicator tests:

- `Supertrend` returns `None` before ATR warmup and a `SupertrendValue` after
  warmup.
- `Supertrend` computes final bands from basic bands and previous close.
- `Supertrend` flips bullish when close crosses the final upper band.
- `Supertrend` flips bearish when close crosses the final lower band.
- Invalid `window` or negative `multiplier` raises `ValueError`.

Strategy SDK tests:

- `IndicatorFactory.supertrend(...)` creates an `AssetIndicator` whose value is
  `SupertrendValue`.
- `IndicatorFactory.update_from_bar(...)` updates only matching assets.

Strategy tests:

- The example class subclasses `Strategy`.
- It does not emit entries before indicators are ready.
- It enters long when fast and slow Supertrend are bullish and filters pass.
- It enters short when fast and slow Supertrend are bearish, filters pass, and
  shorting is allowed.
- It does not short when `allow_short=False`.
- It closes long on fast bearish flip and closes short on fast bullish flip.
- ADX and volume filters block new entries when configured thresholds fail.
- ATR position sizing caps exposure at `max_target_percent`.
- Trading-hours filtering uses `[start, end)` semantics.
- The strategy does not import runtime, execution, broker, risk, registry, or
  actor internals, and the source does not call indicator update methods.

## Non-Goals

- No expansion of `qts.factors` in this iteration.
- No multi-asset portfolio construction.
- No broker-native stop order placement from the example strategy.
- No GC-specific calendar/session/roll/margin implementation.
- No performance claim or parameter optimization.

