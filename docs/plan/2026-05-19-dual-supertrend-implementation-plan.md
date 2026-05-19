# Dual Supertrend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a reusable Supertrend indicator, expose it through the Strategy SDK, and implement a single-asset `GC` default dual Supertrend research strategy with ADX, volume, time, ATR sizing, and software close controls.

**Architecture:** `qts.indicators.technical.Supertrend` owns the ATR-band calculation and incremental state. `IndicatorFactory.supertrend(...)` exposes it to strategy authors without changing indicator lifecycle ownership. `examples.strategies.dual_supertrend.DualSupertrendStrategy` owns strategy-specific signal filters and emits only `ctx.target_percent(...)` / `ctx.close(...)` target intents.

**Tech Stack:** Python dataclasses, `Decimal`, existing Strategy SDK, existing indicator factory, pytest, ruff, mypy, guardrail checks.

---

## File Structure

- Modify: `backend/src/qts/indicators/technical.py`
  Add `SupertrendValue` and `Supertrend` near `AverageTrueRange`; export both in `__all__`.
- Modify: `backend/src/qts/indicators/__init__.py`
  Re-export `Supertrend` and `SupertrendValue`.
- Modify: `backend/src/qts/strategy_sdk/indicators.py`
  Add `SupertrendValue` to `IndicatorValue`; add `IndicatorFactory.supertrend(...)`; include `Supertrend` in bar-indicator binding.
- Modify: `backend/src/qts/strategy_sdk/__init__.py`
  Re-export `DirectionalMovementValue` and `SupertrendValue` as user-facing indicator output schemas used by the example strategy.
- Modify: `docs/strategy_sdk/strategy_api.md`
  Add the Supertrend factory call to the indicators list.
- Modify: `docs/research/strategy_factor_api_v1.md`
  Add immutable indicator output schemas exported by `qts.strategy_sdk`.
- Modify: `tests/unit/indicators/test_technical.py`
  Add Supertrend numerical anchor and validation tests.
- Modify: `tests/unit/strategy_sdk/test_indicator_factory.py`
  Add SDK factory coverage for Supertrend.
- Create: `examples/strategies/dual_supertrend.py`
  Add `DualSupertrendConfig`, `DualSupertrendIndicators`, and `DualSupertrendStrategy`.
- Create: `tests/unit/strategies/test_dual_supertrend.py`
  Add behavior and boundary tests for the example strategy.

---

### Task 1: Supertrend Indicator Tests

**Files:**
- Modify: `tests/unit/indicators/test_technical.py`
- Source under test: `backend/src/qts/indicators/technical.py`

- [ ] **Step 1: Add failing Supertrend tests**

Append these tests to `tests/unit/indicators/test_technical.py`:

```python
import pytest


def test_supertrend_uses_atr_bands_and_flips_direction_anchor() -> None:
    from qts.indicators.technical import Supertrend, SupertrendValue

    supertrend = Supertrend(window=3, multiplier=Decimal("2"))

    bars = (
        _bar(0, high="10", low="8", close="9"),
        _bar(1, high="11", low="9", close="10"),
        _bar(2, high="14", low="9", close="13"),
        _bar(3, high="17", low="13", close="16"),
        _bar(4, high="20", low="15", close="19"),
        _bar(5, high="12", low="8", close="9"),
    )
    values = [supertrend.update_bar(bar) for bar in bars]

    assert values[0] is None
    assert values[1] is None

    first = values[2]
    assert isinstance(first, SupertrendValue)
    assert first.direction == -1
    assert first.upper_band == Decimal("17.5")
    assert first.lower_band == Decimal("5.5")
    assert first.value == Decimal("17.5")

    bullish = values[4]
    assert isinstance(bullish, SupertrendValue)
    assert bullish.direction == 1
    assert bullish.value.quantize(Decimal("0.00000001")) == Decimal("9.72222222")

    bearish = values[5]
    assert isinstance(bearish, SupertrendValue)
    assert bearish.direction == -1
    assert bearish.value.quantize(Decimal("0.00000001")) == Decimal("22.51851852")
    assert supertrend.ready is True


def test_supertrend_rejects_invalid_configuration() -> None:
    from qts.indicators.technical import Supertrend

    with pytest.raises(ValueError, match="window must be positive"):
        Supertrend(window=0)

    with pytest.raises(ValueError, match="multiplier must be non-negative"):
        Supertrend(window=3, multiplier=Decimal("-1"))
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
pytest tests/unit/indicators/test_technical.py::test_supertrend_uses_atr_bands_and_flips_direction_anchor tests/unit/indicators/test_technical.py::test_supertrend_rejects_invalid_configuration -q
```

Expected: FAIL because `qts.indicators.technical.Supertrend` does not exist.

- [ ] **Step 3: Commit only the failing tests if using strict TDD commits**

Run:

```bash
git add tests/unit/indicators/test_technical.py
git commit -m "test: define supertrend indicator anchors"
```

Skip this commit only if executing in a batch without intermediate commits; keep the RED output in the implementation notes.

---

### Task 2: Supertrend Indicator Implementation

**Files:**
- Modify: `backend/src/qts/indicators/technical.py`
- Modify: `backend/src/qts/indicators/__init__.py`
- Test: `tests/unit/indicators/test_technical.py`

- [ ] **Step 1: Add Supertrend implementation**

In `backend/src/qts/indicators/technical.py`, insert this code after `AverageTrueRange`:

```python
@dataclass(frozen=True, slots=True)
class SupertrendValue:
    """Supertrend output for a completed bar update."""

    value: Decimal
    direction: int
    upper_band: Decimal
    lower_band: Decimal


@dataclass(slots=True)
class Supertrend:
    """ATR-band trend indicator with bullish/bearish direction state."""

    window: int
    multiplier: Decimal = Decimal("3")
    _atr: AverageTrueRange = field(init=False, repr=False)
    _previous_close: Decimal | None = field(default=None, init=False, repr=False)
    _final_upper_band: Decimal | None = field(default=None, init=False, repr=False)
    _final_lower_band: Decimal | None = field(default=None, init=False, repr=False)
    _direction: int | None = field(default=None, init=False, repr=False)
    value: SupertrendValue | None = None

    def __post_init__(self) -> None:
        """Validate and initialize Supertrend state."""
        if self.window <= 0:
            raise ValueError("window must be positive")
        if not isinstance(self.multiplier, Decimal):
            self.multiplier = Decimal(str(self.multiplier))
        if self.multiplier < Decimal("0"):
            raise ValueError("multiplier must be non-negative")
        self._atr = AverageTrueRange(window=self.window)

    @property
    def ready(self) -> bool:
        """Return whether Supertrend has warmed up."""
        return self.value is not None

    def update_bar(self, bar: Bar) -> SupertrendValue | None:
        """Update Supertrend from a completed OHLC bar."""
        return self.update(high=bar.high, low=bar.low, close=bar.close)

    def update(self, *, high: Decimal, low: Decimal, close: Decimal) -> SupertrendValue | None:
        """Update Supertrend from OHLC values."""
        previous_close = self._previous_close
        atr = self._atr.update(high=high, low=low, close=close)
        if atr is None:
            self._previous_close = close
            self.value = None
            return None

        midpoint = (high + low) / Decimal("2")
        basic_upper = midpoint + self.multiplier * atr
        basic_lower = midpoint - self.multiplier * atr
        final_upper = self._final_upper(basic_upper, previous_close)
        final_lower = self._final_lower(basic_lower, previous_close)
        direction = self._next_direction(close, final_upper, final_lower)
        active_value = final_lower if direction == 1 else final_upper

        self._final_upper_band = final_upper
        self._final_lower_band = final_lower
        self._direction = direction
        self._previous_close = close
        self.value = SupertrendValue(
            value=active_value,
            direction=direction,
            upper_band=final_upper,
            lower_band=final_lower,
        )
        return self.value

    def _final_upper(self, basic_upper: Decimal, previous_close: Decimal | None) -> Decimal:
        """Return the carried or reset final upper band."""
        current = self._final_upper_band
        if current is None:
            return basic_upper
        if basic_upper < current:
            return basic_upper
        if previous_close is not None and previous_close > current:
            return basic_upper
        return current

    def _final_lower(self, basic_lower: Decimal, previous_close: Decimal | None) -> Decimal:
        """Return the carried or reset final lower band."""
        current = self._final_lower_band
        if current is None:
            return basic_lower
        if basic_lower > current:
            return basic_lower
        if previous_close is not None and previous_close < current:
            return basic_lower
        return current

    def _next_direction(
        self,
        close: Decimal,
        final_upper: Decimal,
        final_lower: Decimal,
    ) -> int:
        """Return next direction using close crosses of the active band."""
        if self._direction is None or self._direction == -1:
            return 1 if close > final_upper else -1
        return -1 if close < final_lower else 1
```

- [ ] **Step 2: Export Supertrend from the indicator package**

In `backend/src/qts/indicators/technical.py`, add `"Supertrend"` and `"SupertrendValue"` to `__all__`.

In `backend/src/qts/indicators/__init__.py`, import and export both symbols:

```python
from qts.indicators.technical import (
    ADX,
    MACD,
    RSI,
    AccumulationDistribution,
    AverageTrueRange,
    BollingerBands,
    ChaikinMoneyFlow,
    CommodityChannelIndex,
    DonchianChannel,
    HistoricalVolatility,
    KeltnerChannel,
    MoneyFlowIndex,
    OnBalanceVolume,
    RateOfChange,
    SessionVWAP,
    StandardDeviation,
    StochasticOscillator,
    Supertrend,
    SupertrendValue,
    VolumeRatio,
    WilliamsR,
)
```

Also add `"Supertrend"` and `"SupertrendValue"` to that file's `__all__`.

- [ ] **Step 3: Run tests to verify GREEN**

Run:

```bash
pytest tests/unit/indicators/test_technical.py::test_supertrend_uses_atr_bands_and_flips_direction_anchor tests/unit/indicators/test_technical.py::test_supertrend_rejects_invalid_configuration -q
```

Expected: PASS.

- [ ] **Step 4: Commit indicator implementation**

Run:

```bash
git add backend/src/qts/indicators/technical.py backend/src/qts/indicators/__init__.py tests/unit/indicators/test_technical.py
git commit -m "feat: add supertrend indicator"
```

---

### Task 3: Strategy SDK Indicator Factory

**Files:**
- Modify: `tests/unit/strategy_sdk/test_indicator_factory.py`
- Modify: `backend/src/qts/strategy_sdk/indicators.py`
- Modify: `backend/src/qts/strategy_sdk/__init__.py`
- Modify: `docs/strategy_sdk/strategy_api.md`
- Modify: `docs/research/strategy_factor_api_v1.md`

- [ ] **Step 1: Add failing SDK factory test**

Append this test to `tests/unit/strategy_sdk/test_indicator_factory.py`:

```python
def test_indicator_factory_registers_supertrend_indicator() -> None:
    from qts.strategy_sdk.indicators import IndicatorFactory
    from qts.indicators.technical import SupertrendValue

    asset = AssetRef(InstrumentId("EQUITY.US.NASDAQ.AAPL"), "AAPL")
    indicators = IndicatorFactory()
    trend = indicators.supertrend(asset, window=3, multiplier=Decimal("2"))

    for index, close in enumerate(("9", "10", "13", "16", "19")):
        base = _bar(index, close=close)
        high = Decimal(close) + Decimal("1")
        low = Decimal(close) - Decimal("1")
        indicators.update_from_bar(
            Bar(
                instrument_id=asset.instrument_id,
                start_time=base.start_time,
                end_time=base.end_time,
                timeframe="1m",
                session_id="2026-01-02",
                open=Decimal(close),
                high=high,
                low=low,
                close=Decimal(close),
                volume=Decimal("10"),
                is_complete=True,
            )
        )

    assert trend.ready is True
    assert isinstance(trend.value, SupertrendValue)
    assert trend.value.direction in {-1, 1}
```

- [ ] **Step 2: Run SDK test to verify RED**

Run:

```bash
pytest tests/unit/strategy_sdk/test_indicator_factory.py::test_indicator_factory_registers_supertrend_indicator -q
```

Expected: FAIL because `IndicatorFactory.supertrend` does not exist.

- [ ] **Step 3: Implement SDK factory method and public value exports**

In `backend/src/qts/strategy_sdk/indicators.py`:

1. Import `Supertrend` and `SupertrendValue` from `qts.indicators.technical`.
2. Add `SupertrendValue` to `IndicatorValue`.
3. Add this method to `IndicatorFactory`:

```python
def supertrend(
    self,
    asset: AssetRef,
    window: int,
    multiplier: Decimal = Decimal("3"),
) -> AssetIndicator:
    """Create a Supertrend indicator for OHLC bars."""
    indicator = Supertrend(window=window, multiplier=multiplier)
    return self._bind_bar_indicator(asset, indicator.update_bar, indicator)
```

4. Add `Supertrend` to the indicator type union accepted by `_bind_bar_indicator`.
5. Add `DirectionalMovementValue` and `SupertrendValue` to `__all__` so strategy examples can type-check indicator output through the SDK module.

In `backend/src/qts/strategy_sdk/__init__.py`, re-export the value schemas:

```python
from qts.strategy_sdk.indicators import (
    AssetIndicator,
    DirectionalMovementValue,
    IndicatorFactory,
    SupertrendValue,
)
```

Add `"DirectionalMovementValue"` and `"SupertrendValue"` to `__all__`.

In `docs/research/strategy_factor_api_v1.md`, add these under the
`qts.strategy_sdk` public entry list:

```markdown
  - `DirectionalMovementValue`
  - `SupertrendValue`
```

- [ ] **Step 4: Update user-facing indicator docs**

In `docs/strategy_sdk/strategy_api.md`, add this line to the Indicators example block:

```python
ST_10_3 = ctx.indicator.supertrend(asset, window=10, multiplier=Decimal("3"))
```

If the docs block does not import `Decimal`, write the literal as text in the surrounding paragraph instead of changing all examples.

- [ ] **Step 5: Run SDK test to verify GREEN**

Run:

```bash
pytest tests/unit/strategy_sdk/test_indicator_factory.py::test_indicator_factory_registers_supertrend_indicator tests/unit/strategy_sdk/test_indicator_factory.py::test_indicator_factory_updates_only_matching_asset -q
```

Expected: PASS.

- [ ] **Step 6: Commit SDK factory changes**

Run:

```bash
git add backend/src/qts/strategy_sdk/indicators.py backend/src/qts/strategy_sdk/__init__.py docs/strategy_sdk/strategy_api.md docs/research/strategy_factor_api_v1.md tests/unit/strategy_sdk/test_indicator_factory.py
git commit -m "feat: expose supertrend through strategy sdk"
```

---

### Task 4: Dual Supertrend Strategy Tests

**Files:**
- Create: `tests/unit/strategies/test_dual_supertrend.py`
- Source under test: `examples/strategies/dual_supertrend.py`

- [ ] **Step 1: Create failing strategy test file**

Create `tests/unit/strategies/test_dual_supertrend.py` with these tests and fixtures:

```python
from __future__ import annotations

import ast
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import cast

import pytest
from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar
from qts.strategy_sdk import DirectionalMovementValue, Strategy, StrategyContext, SupertrendValue


@dataclass(frozen=True)
class FakeAsset:
    instrument_id: InstrumentId
    symbol: str


@dataclass
class FakeIndicator:
    ready: bool = True
    value: object | None = None


class FakeIndicatorFactory:
    def __init__(self, *, ready: bool = True) -> None:
        self.ready = ready
        self.created: dict[tuple[str, int | None], FakeIndicator] = {}

    def supertrend(
        self,
        asset: FakeAsset,
        window: int,
        multiplier: Decimal = Decimal("3"),
    ) -> FakeIndicator:
        _ = asset, multiplier
        return self._indicator("supertrend", window)

    def atr(self, asset: FakeAsset, window: int) -> FakeIndicator:
        _ = asset
        return self._indicator("atr", window)

    def adx(self, asset: FakeAsset, window: int) -> FakeIndicator:
        _ = asset
        return self._indicator("adx", window)

    def volume_ratio(self, asset: FakeAsset, window: int) -> FakeIndicator:
        _ = asset
        return self._indicator("volume_ratio", window)

    def _indicator(self, name: str, window: int | None) -> FakeIndicator:
        indicator = FakeIndicator(ready=self.ready)
        self.created[(name, window)] = indicator
        return indicator


class FakeContext:
    def __init__(self, *, ready: bool = True) -> None:
        self.asset = FakeAsset(InstrumentId("FUTURE.CME.GC.GCG6"), "GC")
        self.indicator = FakeIndicatorFactory(ready=ready)
        self.intents: list[tuple[str, FakeAsset, Decimal | None]] = []
        self.subscriptions: list[tuple[FakeAsset, str, int]] = []

    def symbol(self, symbol: str) -> FakeAsset:
        return FakeAsset(self.asset.instrument_id, symbol)

    def subscribe(self, asset: FakeAsset, *, timeframe: str, warmup: int = 1) -> None:
        self.subscriptions.append((asset, timeframe, warmup))

    def target_percent(self, asset: FakeAsset, weight: Decimal) -> None:
        self.intents.append(("target_percent", asset, weight))

    def close(self, asset: FakeAsset) -> None:
        self.intents.append(("close", asset, None))


def _ctx(ctx: FakeContext) -> StrategyContext:
    return cast(StrategyContext, ctx)


def _bar(index: int, *, close: str = "2000", start_hour: int = 14) -> Bar:
    start = datetime(2026, 1, 2, start_hour, 30, tzinfo=UTC) + timedelta(minutes=index)
    close_value = Decimal(close)
    return Bar(
        instrument_id=InstrumentId("FUTURE.CME.GC.GCG6"),
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=close_value,
        high=close_value + Decimal("5"),
        low=close_value - Decimal("5"),
        close=close_value,
        volume=Decimal("100"),
        is_complete=True,
    )


def _supertrend(direction: int) -> SupertrendValue:
    if direction == 1:
        return SupertrendValue(
            value=Decimal("1990"),
            direction=1,
            upper_band=Decimal("2010"),
            lower_band=Decimal("1990"),
        )
    return SupertrendValue(
        value=Decimal("2010"),
        direction=-1,
        upper_band=Decimal("2010"),
        lower_band=Decimal("1990"),
    )


def _adx(value: str = "25") -> DirectionalMovementValue:
    return DirectionalMovementValue(
        plus_di=Decimal("30"),
        minus_di=Decimal("10"),
        dx=Decimal(value),
        adx=Decimal(value),
    )


def _set_indicators(
    ctx: FakeContext,
    *,
    fast_direction: int,
    slow_direction: int,
    adx: str = "25",
    atr: str = "20",
    volume_ratio: str = "2",
) -> None:
    ctx.indicator.created[("supertrend", 10)].value = _supertrend(fast_direction)
    ctx.indicator.created[("supertrend", 20)].value = _supertrend(slow_direction)
    ctx.indicator.created[("adx", 14)].value = _adx(adx)
    ctx.indicator.created[("atr", 14)].value = Decimal(atr)
    volume = ctx.indicator.created.get(("volume_ratio", 20))
    if volume is not None:
        volume.value = Decimal(volume_ratio)


def test_dual_supertrend_is_strategy_subclass() -> None:
    from examples.strategies.dual_supertrend import DualSupertrendStrategy

    assert issubclass(DualSupertrendStrategy, Strategy)


def test_initialize_subscribes_and_creates_required_indicators() -> None:
    from examples.strategies.dual_supertrend import DualSupertrendStrategy

    ctx = FakeContext()
    strategy = DualSupertrendStrategy()

    strategy.initialize(_ctx(ctx))

    assert ctx.subscriptions[0][1] == "1m"
    assert ("supertrend", 10) in ctx.indicator.created
    assert ("supertrend", 20) in ctx.indicator.created
    assert ("adx", 14) in ctx.indicator.created
    assert ("atr", 14) in ctx.indicator.created


def test_no_entry_before_indicators_are_ready() -> None:
    from examples.strategies.dual_supertrend import DualSupertrendStrategy

    ctx = FakeContext(ready=False)
    strategy = DualSupertrendStrategy()
    strategy.initialize(_ctx(ctx))

    strategy.on_bar(_ctx(ctx), _bar(0))

    assert ctx.intents == []


def test_enters_long_when_fast_and_slow_supertrend_align_and_filters_pass() -> None:
    from examples.strategies.dual_supertrend import (
        DualSupertrendConfig,
        DualSupertrendStrategy,
    )

    ctx = FakeContext()
    strategy = DualSupertrendStrategy(
        DualSupertrendConfig(use_atr_position_sizing=False)
    )
    strategy.initialize(_ctx(ctx))
    _set_indicators(ctx, fast_direction=1, slow_direction=1)

    strategy.on_bar(_ctx(ctx), _bar(0))

    assert ctx.intents == [("target_percent", ctx.asset, Decimal("0.30"))]


def test_enters_short_when_allowed_and_trends_align() -> None:
    from examples.strategies.dual_supertrend import (
        DualSupertrendConfig,
        DualSupertrendStrategy,
    )

    ctx = FakeContext()
    strategy = DualSupertrendStrategy(
        DualSupertrendConfig(use_atr_position_sizing=False)
    )
    strategy.initialize(_ctx(ctx))
    _set_indicators(ctx, fast_direction=-1, slow_direction=-1)

    strategy.on_bar(_ctx(ctx), _bar(0))

    assert ctx.intents == [("target_percent", ctx.asset, Decimal("-0.30"))]


def test_does_not_short_when_shorting_is_disabled() -> None:
    from examples.strategies.dual_supertrend import (
        DualSupertrendConfig,
        DualSupertrendStrategy,
    )

    ctx = FakeContext()
    strategy = DualSupertrendStrategy(
        DualSupertrendConfig(allow_short=False, use_atr_position_sizing=False)
    )
    strategy.initialize(_ctx(ctx))
    _set_indicators(ctx, fast_direction=-1, slow_direction=-1)

    strategy.on_bar(_ctx(ctx), _bar(0))

    assert ctx.intents == []


def test_closes_long_on_fast_bearish_flip() -> None:
    from examples.strategies.dual_supertrend import (
        DualSupertrendConfig,
        DualSupertrendStrategy,
    )

    ctx = FakeContext()
    strategy = DualSupertrendStrategy(
        DualSupertrendConfig(use_atr_position_sizing=False)
    )
    strategy.initialize(_ctx(ctx))
    _set_indicators(ctx, fast_direction=1, slow_direction=1)
    strategy.on_bar(_ctx(ctx), _bar(0))
    _set_indicators(ctx, fast_direction=-1, slow_direction=1)

    strategy.on_bar(_ctx(ctx), _bar(1))

    assert ctx.intents[-1] == ("close", ctx.asset, None)


@pytest.mark.parametrize(
    ("adx", "volume_ratio"),
    [
        ("10", "2"),
        ("25", "0.5"),
    ],
)
def test_entry_filters_block_new_positions(adx: str, volume_ratio: str) -> None:
    from examples.strategies.dual_supertrend import (
        DualSupertrendConfig,
        DualSupertrendStrategy,
    )

    ctx = FakeContext()
    strategy = DualSupertrendStrategy(
        DualSupertrendConfig(
            use_volume_filter=True,
            min_volume_ratio=Decimal("1.0"),
            use_atr_position_sizing=False,
        )
    )
    strategy.initialize(_ctx(ctx))
    _set_indicators(
        ctx,
        fast_direction=1,
        slow_direction=1,
        adx=adx,
        volume_ratio=volume_ratio,
    )

    strategy.on_bar(_ctx(ctx), _bar(0))

    assert ctx.intents == []


def test_atr_position_sizing_caps_target_percent() -> None:
    from examples.strategies.dual_supertrend import DualSupertrendStrategy

    ctx = FakeContext()
    strategy = DualSupertrendStrategy()
    strategy.initialize(_ctx(ctx))
    _set_indicators(ctx, fast_direction=1, slow_direction=1, atr="20")

    strategy.on_bar(_ctx(ctx), _bar(0, close="2000"))

    assert ctx.intents == [("target_percent", ctx.asset, Decimal("0.50"))]


def test_trading_hours_filter_uses_half_open_window() -> None:
    from examples.strategies.dual_supertrend import (
        DualSupertrendConfig,
        DualSupertrendStrategy,
    )

    config = DualSupertrendConfig(
        use_trading_hours_filter=True,
        trading_hours_timezone="UTC",
        trading_hours_start="14:30",
        trading_hours_end="15:30",
    )
    strategy = DualSupertrendStrategy(config)

    assert strategy.in_trading_hours(_bar(0, start_hour=14))
    assert not strategy.in_trading_hours(_bar(0, start_hour=15))


def test_strategy_imports_only_strategy_sdk_and_domain_bar_boundary() -> None:
    source = Path("examples/strategies/dual_supertrend.py").read_text()
    tree = ast.parse(source)
    allowed_qts_modules = {"qts.strategy_sdk", "qts.domain.market_data"}
    bad: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("qts."):
            if node.module not in allowed_qts_modules:
                bad.append(node.module)
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("qts.") and alias.name not in allowed_qts_modules:
                    bad.append(alias.name)
    assert bad == []
    assert ".update(" not in source
    assert ".update_from_bar(" not in source
```

- [ ] **Step 2: Run strategy tests to verify RED**

Run:

```bash
pytest tests/unit/strategies/test_dual_supertrend.py -q
```

Expected: FAIL because `examples.strategies.dual_supertrend` does not exist.

- [ ] **Step 3: Commit failing strategy tests if using strict TDD commits**

Run:

```bash
git add tests/unit/strategies/test_dual_supertrend.py
git commit -m "test: define dual supertrend strategy behavior"
```

Skip this commit only if executing in a batch without intermediate commits; keep RED output in the implementation notes.

---

### Task 5: Dual Supertrend Strategy Implementation

**Files:**
- Create: `examples/strategies/dual_supertrend.py`
- Test: `tests/unit/strategies/test_dual_supertrend.py`

- [ ] **Step 1: Implement the strategy file**

Create `examples/strategies/dual_supertrend.py` with this structure:

```python
"""Dual Supertrend trend-following strategy using the public Strategy SDK."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from decimal import Decimal
from zoneinfo import ZoneInfo

from qts.domain.market_data import Bar
from qts.strategy_sdk import (
    AssetIndicator,
    AssetRef,
    DirectionalMovementValue,
    Strategy,
    StrategyContext,
    SupertrendValue,
)


@dataclass(frozen=True, slots=True)
class DualSupertrendConfig:
    """Configuration for the single-asset dual Supertrend strategy."""

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

    def __post_init__(self) -> None:
        """Validate configuration values."""
        for name in (
            "fast_window",
            "slow_window",
            "adx_window",
            "volume_ratio_window",
            "atr_window",
        ):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")
        for name in (
            "fast_multiplier",
            "slow_multiplier",
            "base_target_percent",
            "max_target_percent",
            "min_adx",
            "min_volume_ratio",
            "target_atr_fraction",
            "stop_atr_multiple",
            "trail_atr_multiple",
        ):
            value = getattr(self, name)
            if not isinstance(value, Decimal):
                object.__setattr__(self, name, Decimal(str(value)))
        if self.fast_multiplier < Decimal("0"):
            raise ValueError("fast_multiplier must be non-negative")
        if self.slow_multiplier < Decimal("0"):
            raise ValueError("slow_multiplier must be non-negative")
        if self.base_target_percent <= Decimal("0"):
            raise ValueError("base_target_percent must be positive")
        if self.max_target_percent <= Decimal("0"):
            raise ValueError("max_target_percent must be positive")
        if self.min_adx < Decimal("0"):
            raise ValueError("min_adx must be non-negative")
        if self.min_volume_ratio < Decimal("0"):
            raise ValueError("min_volume_ratio must be non-negative")
        if self.target_atr_fraction <= Decimal("0"):
            raise ValueError("target_atr_fraction must be positive")
        if self.stop_atr_multiple < Decimal("0"):
            raise ValueError("stop_atr_multiple must be non-negative")
        if self.trail_atr_multiple < Decimal("0"):
            raise ValueError("trail_atr_multiple must be non-negative")
        if not self.symbol.strip():
            raise ValueError("symbol must not be empty")
        if not self.timeframe.strip():
            raise ValueError("timeframe must not be empty")
        if not isinstance(self.allow_short, bool):
            raise ValueError("allow_short must be a bool")
        if not isinstance(self.use_adx_filter, bool):
            raise ValueError("use_adx_filter must be a bool")
        if not isinstance(self.use_volume_filter, bool):
            raise ValueError("use_volume_filter must be a bool")
        if not isinstance(self.use_atr_position_sizing, bool):
            raise ValueError("use_atr_position_sizing must be a bool")
        if not isinstance(self.use_trading_hours_filter, bool):
            raise ValueError("use_trading_hours_filter must be a bool")
        self._parse_time(self.trading_hours_start, "trading_hours_start")
        self._parse_time(self.trading_hours_end, "trading_hours_end")
        ZoneInfo(self.trading_hours_timezone)

    @staticmethod
    def _parse_time(value: str, name: str) -> time:
        """Parse HH:MM into a time value."""
        parts = value.split(":")
        if len(parts) != 2:
            raise ValueError(f"{name} must use HH:MM")
        hour = int(parts[0])
        minute = int(parts[1])
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError(f"{name} must use HH:MM")
        return time(hour=hour, minute=minute)

    @property
    def trading_start_time(self) -> time:
        """Return the parsed start of the strategy trading window."""
        return self._parse_time(self.trading_hours_start, "trading_hours_start")

    @property
    def trading_end_time(self) -> time:
        """Return the parsed end of the strategy trading window."""
        return self._parse_time(self.trading_hours_end, "trading_hours_end")


@dataclass(frozen=True, slots=True)
class DualSupertrendIndicators:
    """Indicator bundle owned by the strategy lifecycle."""

    fast: AssetIndicator
    slow: AssetIndicator
    adx: AssetIndicator
    atr: AssetIndicator
    volume_ratio: AssetIndicator | None = None

    @property
    def ready(self) -> bool:
        """Return whether all configured indicators have values."""
        indicators = (self.fast, self.slow, self.adx, self.atr)
        if any(not indicator.ready or indicator.value is None for indicator in indicators):
            return False
        if self.volume_ratio is None:
            return True
        return self.volume_ratio.ready and self.volume_ratio.value is not None
```

Then add `DualSupertrendStrategy`:

```python
class DualSupertrendStrategy(Strategy):
    """Dual Supertrend trend-following strategy with optional regime filters."""

    def __init__(self, config: DualSupertrendConfig | None = None) -> None:
        self._config = config or DualSupertrendConfig()
        self._asset: AssetRef | None = None
        self._indicators: DualSupertrendIndicators | None = None
        self._previous_fast_direction: int | None = None
        self._position_side: int = 0
        self._entry_price: Decimal | None = None
        self._stop_price: Decimal | None = None
        self._trailing_stop: Decimal | None = None
        self._tz = ZoneInfo(self._config.trading_hours_timezone)
        self._trading_start = self._config.trading_start_time
        self._trading_end = self._config.trading_end_time

    def initialize(self, ctx: StrategyContext) -> None:
        """Initialize subscriptions and indicators."""
        asset = ctx.symbol(self._config.symbol)
        self._asset = asset
        warmup = max(
            self._config.fast_window,
            self._config.slow_window,
            self._config.adx_window,
            self._config.atr_window,
            self._config.volume_ratio_window if self._config.use_volume_filter else 1,
        )
        ctx.subscribe(asset, timeframe=self._config.timeframe, warmup=warmup)
        volume_ratio = (
            ctx.indicator.volume_ratio(asset, self._config.volume_ratio_window)
            if self._config.use_volume_filter
            else None
        )
        self._indicators = DualSupertrendIndicators(
            fast=ctx.indicator.supertrend(
                asset,
                window=self._config.fast_window,
                multiplier=self._config.fast_multiplier,
            ),
            slow=ctx.indicator.supertrend(
                asset,
                window=self._config.slow_window,
                multiplier=self._config.slow_multiplier,
            ),
            adx=ctx.indicator.adx(asset, self._config.adx_window),
            atr=ctx.indicator.atr(asset, self._config.atr_window),
            volume_ratio=volume_ratio,
        )

    def on_bar(self, ctx: StrategyContext, bar: Bar) -> None:
        """Handle a completed strategy-facing bar."""
        if self._asset is None or self._indicators is None:
            raise RuntimeError("strategy must be initialized before on_bar")
        if bar.instrument_id != self._asset.instrument_id:
            return
        indicators = self._indicators
        if not indicators.ready:
            return

        fast = self._supertrend_value(indicators.fast)
        slow = self._supertrend_value(indicators.slow)
        atr = self._decimal_value(indicators.atr)
        if fast is None or slow is None or atr is None:
            return

        self._previous_fast_direction = fast.direction

        if self._close_on_software_risk(ctx, bar, atr):
            return
        if self._close_on_trend_flip(ctx, fast.direction):
            return
        if self._position_side != 0:
            return
        if not self.in_trading_hours(bar):
            return
        if not self._entry_filters_pass():
            return

        side = self._entry_side(fast.direction, slow.direction)
        if side == 0:
            return
        self._enter_position(ctx, bar, side, atr)

    def in_trading_hours(self, bar: Bar) -> bool:
        """Return whether a bar is inside the configured half-open time window."""
        if not self._config.use_trading_hours_filter:
            return True
        local_time = bar.start_time.astimezone(self._tz).time()
        if self._trading_start <= self._trading_end:
            return self._trading_start <= local_time < self._trading_end
        return local_time >= self._trading_start or local_time < self._trading_end
```

Complete the class with these methods:

```python
    def _entry_filters_pass(self) -> bool:
        if self._indicators is None:
            return False
        if self._config.use_adx_filter:
            adx = self._adx_value(self._indicators.adx)
            if adx is None or adx < self._config.min_adx:
                return False
        if self._config.use_volume_filter:
            if self._indicators.volume_ratio is None:
                return False
            volume_ratio = self._decimal_value(self._indicators.volume_ratio)
            if volume_ratio is None or volume_ratio < self._config.min_volume_ratio:
                return False
        return True

    def _entry_side(self, fast_direction: int, slow_direction: int) -> int:
        if fast_direction == 1 and slow_direction == 1:
            return 1
        if fast_direction == -1 and slow_direction == -1 and self._config.allow_short:
            return -1
        return 0

    def _enter_position(self, ctx: StrategyContext, bar: Bar, side: int, atr: Decimal) -> None:
        if self._asset is None:
            return
        target = self._target_percent(bar.close, atr)
        if side < 0:
            target = -target
        self._position_side = side
        self._entry_price = bar.close
        self._stop_price = self._initial_stop(bar.close, atr, side)
        self._trailing_stop = None
        ctx.target_percent(self._asset, target)

    def _target_percent(self, close: Decimal, atr: Decimal) -> Decimal:
        target = self._config.base_target_percent
        if self._config.use_atr_position_sizing and atr > Decimal("0") and close > Decimal("0"):
            atr_fraction = atr / close
            target = self._config.base_target_percent * (
                self._config.target_atr_fraction / atr_fraction
            )
        return min(target, self._config.max_target_percent)

    def _initial_stop(self, close: Decimal, atr: Decimal, side: int) -> Decimal | None:
        if self._config.stop_atr_multiple <= Decimal("0") or atr <= Decimal("0"):
            return None
        if side > 0:
            return close - atr * self._config.stop_atr_multiple
        return close + atr * self._config.stop_atr_multiple

    def _close_on_trend_flip(self, ctx: StrategyContext, fast_direction: int) -> bool:
        if self._position_side > 0 and fast_direction == -1:
            self._close(ctx)
            return True
        if self._position_side < 0 and fast_direction == 1:
            self._close(ctx)
            return True
        return False

    def _close_on_software_risk(self, ctx: StrategyContext, bar: Bar, atr: Decimal) -> bool:
        if self._position_side == 0:
            return False
        self._update_trailing_stop(bar, atr)
        if self._position_side > 0:
            stop = self._max_stop(self._stop_price, self._trailing_stop)
            if stop is not None and bar.low <= stop:
                self._close(ctx)
                return True
        else:
            stop = self._min_stop(self._stop_price, self._trailing_stop)
            if stop is not None and bar.high >= stop:
                self._close(ctx)
                return True
        return False

    def _update_trailing_stop(self, bar: Bar, atr: Decimal) -> None:
        if self._config.trail_atr_multiple <= Decimal("0") or atr <= Decimal("0"):
            return
        offset = atr * self._config.trail_atr_multiple
        if self._position_side > 0:
            candidate = bar.close - offset
            self._trailing_stop = self._max_stop(self._trailing_stop, candidate)
        elif self._position_side < 0:
            candidate = bar.close + offset
            self._trailing_stop = self._min_stop(self._trailing_stop, candidate)

    def _close(self, ctx: StrategyContext) -> None:
        if self._asset is not None:
            ctx.close(self._asset)
        self._position_side = 0
        self._entry_price = None
        self._stop_price = None
        self._trailing_stop = None

    @staticmethod
    def _supertrend_value(indicator: AssetIndicator) -> SupertrendValue | None:
        value = indicator.value
        return value if isinstance(value, SupertrendValue) else None

    @staticmethod
    def _adx_value(indicator: AssetIndicator) -> Decimal | None:
        value = indicator.value
        if isinstance(value, DirectionalMovementValue):
            return value.adx
        return None

    @staticmethod
    def _decimal_value(indicator: AssetIndicator) -> Decimal | None:
        value = indicator.value
        return value if isinstance(value, Decimal) else None

    @staticmethod
    def _max_stop(left: Decimal | None, right: Decimal | None) -> Decimal | None:
        if left is None:
            return right
        if right is None:
            return left
        return max(left, right)

    @staticmethod
    def _min_stop(left: Decimal | None, right: Decimal | None) -> Decimal | None:
        if left is None:
            return right
        if right is None:
            return left
        return min(left, right)


__all__ = ["DualSupertrendConfig", "DualSupertrendIndicators", "DualSupertrendStrategy"]
```

- [ ] **Step 2: Run strategy tests to verify GREEN**

Run:

```bash
pytest tests/unit/strategies/test_dual_supertrend.py -q
```

Expected: PASS.

- [ ] **Step 3: Commit strategy implementation**

Run:

```bash
git add examples/strategies/dual_supertrend.py tests/unit/strategies/test_dual_supertrend.py
git commit -m "feat: add dual supertrend strategy example"
```

---

### Task 6: Integration Checks, Guardrails, and Cleanup

**Files:**
- Inspect changed Python files from Tasks 1-5.
- No planned source changes unless checks identify concrete issues.

- [ ] **Step 1: Inspect new private helpers**

Run:

```bash
rg -n "^def _|^class _" backend/src/qts/indicators/technical.py backend/src/qts/strategy_sdk/indicators.py examples/strategies/dual_supertrend.py tests/unit/strategies/test_dual_supertrend.py tests/unit/indicators/test_technical.py tests/unit/strategy_sdk/test_indicator_factory.py
```

Expected: private methods in class-centric modules are owned by their classes. If a new module-private helper appears in production code, move it onto the owning class or make the concept explicit.

- [ ] **Step 2: Run narrow tests**

Run:

```bash
pytest tests/unit/indicators/test_technical.py tests/unit/strategy_sdk/test_indicator_factory.py tests/unit/strategies/test_dual_supertrend.py -q
```

Expected: PASS.

- [ ] **Step 3: Run required normal code-task checks**

Run:

```bash
make format
make lint
make guardrails
make typecheck
make test-unit
```

Expected: all PASS. If a command fails, apply the smallest scoped fix and re-run the failing command.

- [ ] **Step 4: Refresh the code-review graph**

Run the graph update tool after successful source changes:

```text
build_or_update_graph_tool(full_rebuild=False, repo_root="/Users/bjhl/Projects/QTS")
```

Expected: graph update succeeds.

- [ ] **Step 5: Review final diff**

Run:

```bash
git diff --check
git status --short
git diff -- backend/src/qts/indicators/technical.py backend/src/qts/indicators/__init__.py backend/src/qts/strategy_sdk/indicators.py backend/src/qts/strategy_sdk/__init__.py docs/strategy_sdk/strategy_api.md examples/strategies/dual_supertrend.py tests/unit/indicators/test_technical.py tests/unit/strategy_sdk/test_indicator_factory.py tests/unit/strategies/test_dual_supertrend.py
```

Expected: no whitespace errors; diff contains only the requested Supertrend indicator, SDK exposure, docs, strategy example, and tests.

- [ ] **Step 6: Final commit**

If previous task commits were skipped, create one implementation commit:

```bash
git add backend/src/qts/indicators/technical.py backend/src/qts/indicators/__init__.py backend/src/qts/strategy_sdk/indicators.py backend/src/qts/strategy_sdk/__init__.py docs/strategy_sdk/strategy_api.md examples/strategies/dual_supertrend.py tests/unit/indicators/test_technical.py tests/unit/strategy_sdk/test_indicator_factory.py tests/unit/strategies/test_dual_supertrend.py
git commit -m "feat: add dual supertrend strategy"
```

Expected: commit succeeds without staging unrelated VWAP files or analysis artifacts.
