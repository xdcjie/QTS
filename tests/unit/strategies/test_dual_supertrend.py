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


def _bar(
    index: int,
    *,
    close: str = "2000",
    start_hour: int = 14,
    high: str | None = None,
    low: str | None = None,
) -> Bar:
    start = datetime(2026, 1, 2, start_hour, 30, tzinfo=UTC) + timedelta(minutes=index)
    close_value = Decimal(close)
    return Bar(
        instrument_id=InstrumentId("FUTURE.CME.GC.GCG6"),
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=close_value,
        high=Decimal(high) if high is not None else close_value + Decimal("5"),
        low=Decimal(low) if low is not None else close_value - Decimal("5"),
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


def test_backtest_loader_can_instantiate_dual_supertrend_with_yaml_params() -> None:
    from qts.backtest.pipeline import BacktestPipeline

    strategy = BacktestPipeline.load_strategy(
        "examples.strategies.dual_supertrend:DualSupertrendStrategy",
        {
            "symbol": "SI",
            "timeframe": "15m",
            "base_target_percent": "0.20",
            "use_trading_hours_filter": True,
            "trading_hours_timezone": "US/Eastern",
            "trading_hours_start": "18:00",
            "trading_hours_end": "17:00",
        },
    )
    ctx = FakeContext()

    strategy.initialize(_ctx(ctx))

    assert ctx.subscriptions[0][0].symbol == "SI"
    assert ctx.subscriptions[0][1] == "15m"


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
    strategy = DualSupertrendStrategy(DualSupertrendConfig(use_atr_position_sizing=False))
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
    strategy = DualSupertrendStrategy(DualSupertrendConfig(use_atr_position_sizing=False))
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
    strategy = DualSupertrendStrategy(DualSupertrendConfig(use_atr_position_sizing=False))
    strategy.initialize(_ctx(ctx))
    _set_indicators(ctx, fast_direction=1, slow_direction=1)
    strategy.on_bar(_ctx(ctx), _bar(0))
    _set_indicators(ctx, fast_direction=-1, slow_direction=1)

    strategy.on_bar(_ctx(ctx), _bar(1))

    assert ctx.intents[-1] == ("close", ctx.asset, None)


def test_closes_short_on_fast_bullish_flip() -> None:
    from examples.strategies.dual_supertrend import (
        DualSupertrendConfig,
        DualSupertrendStrategy,
    )

    ctx = FakeContext()
    strategy = DualSupertrendStrategy(DualSupertrendConfig(use_atr_position_sizing=False))
    strategy.initialize(_ctx(ctx))
    _set_indicators(ctx, fast_direction=-1, slow_direction=-1)
    strategy.on_bar(_ctx(ctx), _bar(0))
    _set_indicators(ctx, fast_direction=1, slow_direction=-1)

    strategy.on_bar(_ctx(ctx), _bar(1))

    assert ctx.intents[-1] == ("close", ctx.asset, None)


def test_long_fixed_stop_closes_position() -> None:
    from examples.strategies.dual_supertrend import (
        DualSupertrendConfig,
        DualSupertrendStrategy,
    )

    ctx = FakeContext()
    strategy = DualSupertrendStrategy(
        DualSupertrendConfig(
            stop_atr_multiple=Decimal("1"),
            use_atr_position_sizing=False,
        )
    )
    strategy.initialize(_ctx(ctx))
    _set_indicators(ctx, fast_direction=1, slow_direction=1, atr="20")
    strategy.on_bar(_ctx(ctx), _bar(0, close="2000"))

    strategy.on_bar(_ctx(ctx), _bar(1, close="1990", low="1979"))

    assert ctx.intents[-1] == ("close", ctx.asset, None)


def test_long_trailing_stop_updates_after_current_bar_stop_check() -> None:
    from examples.strategies.dual_supertrend import (
        DualSupertrendConfig,
        DualSupertrendStrategy,
    )

    ctx = FakeContext()
    strategy = DualSupertrendStrategy(
        DualSupertrendConfig(
            trail_atr_multiple=Decimal("1"),
            use_atr_position_sizing=False,
        )
    )
    strategy.initialize(_ctx(ctx))
    _set_indicators(ctx, fast_direction=1, slow_direction=1, atr="20")
    strategy.on_bar(_ctx(ctx), _bar(0, close="2000"))

    strategy.on_bar(_ctx(ctx), _bar(1, close="2020", low="1995"))
    strategy.on_bar(_ctx(ctx), _bar(2, close="2040", low="2005"))

    assert ctx.intents == [("target_percent", ctx.asset, Decimal("0.30"))]

    strategy.on_bar(_ctx(ctx), _bar(3, close="2040", low="2019"))

    assert ctx.intents[-1] == ("close", ctx.asset, None)


def test_short_trailing_stop_updates_after_current_bar_stop_check() -> None:
    from examples.strategies.dual_supertrend import (
        DualSupertrendConfig,
        DualSupertrendStrategy,
    )

    ctx = FakeContext()
    strategy = DualSupertrendStrategy(
        DualSupertrendConfig(
            trail_atr_multiple=Decimal("1"),
            use_atr_position_sizing=False,
        )
    )
    strategy.initialize(_ctx(ctx))
    _set_indicators(ctx, fast_direction=-1, slow_direction=-1, atr="20")
    strategy.on_bar(_ctx(ctx), _bar(0, close="2000"))

    strategy.on_bar(_ctx(ctx), _bar(1, close="1980", high="2005"))
    strategy.on_bar(_ctx(ctx), _bar(2, close="1960", high="1995"))

    assert ctx.intents == [("target_percent", ctx.asset, Decimal("-0.30"))]

    strategy.on_bar(_ctx(ctx), _bar(3, close="1960", high="1981"))

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
    _set_indicators(ctx, fast_direction=1, slow_direction=1, atr="10")

    strategy.on_bar(_ctx(ctx), _bar(0, close="2000"))

    assert ctx.intents == [("target_percent", ctx.asset, Decimal("0.50"))]


def test_atr_position_sizing_scales_base_target_percent() -> None:
    from examples.strategies.dual_supertrend import DualSupertrendStrategy

    ctx = FakeContext()
    strategy = DualSupertrendStrategy()
    strategy.initialize(_ctx(ctx))
    _set_indicators(ctx, fast_direction=1, slow_direction=1, atr="40")

    strategy.on_bar(_ctx(ctx), _bar(0, close="2000"))

    assert ctx.intents == [("target_percent", ctx.asset, Decimal("0.15"))]


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


def test_disabled_trading_hours_filter_ignores_invalid_window_config() -> None:
    from examples.strategies.dual_supertrend import (
        DualSupertrendConfig,
        DualSupertrendStrategy,
    )

    config = DualSupertrendConfig(
        use_trading_hours_filter=False,
        trading_hours_timezone="Not/AZone",
        trading_hours_start="bad",
        trading_hours_end="also-bad",
    )
    strategy = DualSupertrendStrategy(config)

    assert strategy.in_trading_hours(_bar(0))


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
