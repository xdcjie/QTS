from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import cast

from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar
from qts.strategy_sdk import AssetRef, StrategyContext


class FakeDataView:
    def __init__(self, closes: tuple[str, ...]) -> None:
        self._closes = closes

    def set_closes(self, closes: tuple[str, ...]) -> None:
        self._closes = closes

    def history(
        self,
        asset: AssetRef,
        *,
        bars: int,
        timeframe: str | None = None,
    ) -> tuple[Bar, ...]:
        _ = asset, timeframe
        start = datetime(2020, 1, 2, tzinfo=UTC)
        output: list[Bar] = []
        for index, close_text in enumerate(self._closes[-bars:]):
            close = Decimal(close_text)
            output.append(
                Bar(
                    instrument_id=InstrumentId("FUTURE.CME.SI.SIH0"),
                    start_time=start + timedelta(days=index),
                    end_time=start + timedelta(days=index + 1),
                    timeframe="1d",
                    session_id=(start + timedelta(days=index)).date().isoformat(),
                    open=close,
                    high=close,
                    low=close,
                    close=close,
                    volume=Decimal("100"),
                    is_complete=True,
                )
            )
        return tuple(output)


@dataclass
class FakeContext:
    data: FakeDataView

    def __post_init__(self) -> None:
        self.asset = AssetRef(InstrumentId("FUTURE.CME.SI.SIH0"), "SI")
        self.intents: list[tuple[str, AssetRef, Decimal | None]] = []
        self.subscriptions: list[tuple[AssetRef, str, int]] = []

    def future(self, symbol: str) -> AssetRef:
        if symbol != "SI":
            raise KeyError(symbol)
        return self.asset

    def symbol(self, symbol: str) -> AssetRef:
        return AssetRef(self.asset.instrument_id, symbol)

    def subscribe(self, asset: AssetRef, *, timeframe: str, warmup: int = 1) -> None:
        self.subscriptions.append((asset, timeframe, warmup))

    def target_percent(self, asset: AssetRef, weight: Decimal) -> None:
        self.intents.append(("target_percent", asset, weight))

    def close(self, asset: AssetRef) -> None:
        self.intents.append(("close", asset, None))


def _ctx(ctx: FakeContext) -> StrategyContext:
    return cast(StrategyContext, ctx)


def _bar() -> Bar:
    return Bar(
        instrument_id=InstrumentId("FUTURE.CME.SI.SIH0"),
        start_time=datetime(2020, 1, 5, tzinfo=UTC),
        end_time=datetime(2020, 1, 6, tzinfo=UTC),
        timeframe="1d",
        session_id="2020-01-05",
        open=Decimal("100"),
        high=Decimal("100"),
        low=Decimal("100"),
        close=Decimal("100"),
        volume=Decimal("100"),
        is_complete=True,
    )


def test_vol_target_trend_subscribes_to_daily_warmup() -> None:
    from examples.strategies.vol_target_trend import VolTargetTrendStrategy

    ctx = FakeContext(FakeDataView(("100", "101", "102", "103")))
    strategy = VolTargetTrendStrategy(
        symbol="SI",
        momentum_lookback_bars=3,
        volatility_lookback_bars=5,
    )

    strategy.initialize(_ctx(ctx))

    assert ctx.subscriptions == [(ctx.asset, "1d", 6)]


def test_vol_target_trend_caps_long_target_when_momentum_is_positive() -> None:
    from examples.strategies.vol_target_trend import VolTargetTrendStrategy

    ctx = FakeContext(FakeDataView(("100", "101", "102", "103")))
    strategy = VolTargetTrendStrategy(
        symbol="SI",
        momentum_lookback_bars=3,
        volatility_lookback_bars=3,
        target_annual_vol=Decimal("0.20"),
        max_target_percent=Decimal("0.50"),
        min_signal_return=Decimal("0.02"),
    )
    strategy.initialize(_ctx(ctx))

    strategy.on_bar(_ctx(ctx), _bar())

    assert ctx.intents == [("target_percent", ctx.asset, Decimal("0.50"))]


def test_vol_target_trend_caps_short_target_when_momentum_is_negative() -> None:
    from examples.strategies.vol_target_trend import VolTargetTrendStrategy

    ctx = FakeContext(FakeDataView(("100", "99", "98", "97")))
    strategy = VolTargetTrendStrategy(
        symbol="SI",
        momentum_lookback_bars=3,
        volatility_lookback_bars=3,
        target_annual_vol=Decimal("0.20"),
        max_target_percent=Decimal("0.50"),
        min_signal_return=Decimal("0.02"),
        allow_short=True,
    )
    strategy.initialize(_ctx(ctx))

    strategy.on_bar(_ctx(ctx), _bar())

    assert ctx.intents == [("target_percent", ctx.asset, Decimal("-0.50"))]


def test_vol_target_trend_closes_when_signal_returns_to_flat() -> None:
    from examples.strategies.vol_target_trend import VolTargetTrendStrategy

    data = FakeDataView(("100", "101", "102", "103"))
    ctx = FakeContext(data)
    strategy = VolTargetTrendStrategy(
        symbol="SI",
        momentum_lookback_bars=3,
        volatility_lookback_bars=3,
        target_annual_vol=Decimal("0.20"),
        max_target_percent=Decimal("0.50"),
        min_signal_return=Decimal("0.02"),
    )
    strategy.initialize(_ctx(ctx))
    strategy.on_bar(_ctx(ctx), _bar())

    data.set_closes(("100", "100.2", "100.1", "100.3"))
    strategy.on_bar(_ctx(ctx), _bar())
    strategy.on_bar(_ctx(ctx), _bar())

    assert ctx.intents == [
        ("target_percent", ctx.asset, Decimal("0.50")),
        ("close", ctx.asset, None),
    ]


def test_vol_target_trend_suppresses_duplicate_targets_inside_threshold() -> None:
    from examples.strategies.vol_target_trend import VolTargetTrendStrategy

    ctx = FakeContext(FakeDataView(("100", "101", "102", "103")))
    strategy = VolTargetTrendStrategy(
        symbol="SI",
        momentum_lookback_bars=3,
        volatility_lookback_bars=3,
        target_annual_vol=Decimal("0.20"),
        max_target_percent=Decimal("0.50"),
        min_signal_return=Decimal("0.02"),
        rebalance_threshold=Decimal("0.05"),
    )
    strategy.initialize(_ctx(ctx))

    strategy.on_bar(_ctx(ctx), _bar())
    strategy.on_bar(_ctx(ctx), _bar())

    assert ctx.intents == [("target_percent", ctx.asset, Decimal("0.50"))]


def test_backtest_loader_can_instantiate_vol_target_trend_with_yaml_params() -> None:
    from qts.backtest.pipeline import BacktestPipeline

    strategy = BacktestPipeline.load_strategy(
        "examples.strategies.vol_target_trend:VolTargetTrendStrategy",
        {
            "symbol": "SI",
            "timeframe": "1d",
            "momentum_lookback_bars": 3,
            "volatility_lookback_bars": 3,
            "target_annual_vol": "0.20",
            "max_target_percent": "0.50",
            "min_signal_return": "0.02",
            "rebalance_threshold": "0.05",
            "allow_short": True,
        },
    )
    ctx = FakeContext(FakeDataView(("100", "101", "102", "103")))

    strategy.initialize(_ctx(ctx))

    assert ctx.subscriptions == [(ctx.asset, "1d", 4)]
