from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import cast

from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar
from qts.strategy_sdk import AssetRef, StrategyContext

GC_ID = InstrumentId("CONTINUOUS_FUTURE.CME.GC")
GC_CARRY_ID = InstrumentId("RESEARCH.CARRY.GC")


class FakeDataView:
    def __init__(
        self,
        price_closes: tuple[str, ...],
        carry_closes: tuple[str, ...],
    ) -> None:
        self._price_closes = price_closes
        self._carry_closes = carry_closes
        self._start_offset_days = 0

    def set_closes(self, price_closes: tuple[str, ...], carry_closes: tuple[str, ...]) -> None:
        self._price_closes = price_closes
        self._carry_closes = carry_closes
        self._start_offset_days += 1

    def history(
        self,
        asset: AssetRef,
        *,
        bars: int,
        timeframe: str | None = None,
    ) -> tuple[Bar, ...]:
        _ = timeframe
        if asset.instrument_id == GC_ID:
            return _bars(
                GC_ID,
                self._price_closes[-bars:],
                start_offset_days=self._start_offset_days,
            )
        if asset.instrument_id == GC_CARRY_ID:
            offset = self._start_offset_days + max(
                len(self._price_closes) - len(self._carry_closes),
                0,
            )
            return _bars(
                GC_CARRY_ID,
                self._carry_closes[-bars:],
                start_offset_days=offset,
            )
        return ()


@dataclass
class FakeContext:
    data: FakeDataView

    def __post_init__(self) -> None:
        self.gc_asset = AssetRef(GC_ID, "GC")
        self.carry_asset = AssetRef(GC_CARRY_ID, "GC_CARRY")
        self.intents: list[tuple[str, AssetRef, Decimal | None]] = []
        self.subscriptions: list[tuple[AssetRef, str, int]] = []

    def future(self, symbol: str) -> AssetRef:
        if symbol == "GC":
            return self.gc_asset
        raise KeyError(symbol)

    def symbol(self, symbol: str) -> AssetRef:
        if symbol == "GC_CARRY":
            return self.carry_asset
        return AssetRef(InstrumentId(f"RESEARCH.TEST.{symbol}"), symbol)

    def subscribe(self, asset: AssetRef, *, timeframe: str, warmup: int = 1) -> None:
        self.subscriptions.append((asset, timeframe, warmup))

    def target_percent(self, asset: AssetRef, weight: Decimal) -> None:
        self.intents.append(("target_percent", asset, weight))

    def close(self, asset: AssetRef) -> None:
        self.intents.append(("close", asset, None))


def _ctx(ctx: FakeContext) -> StrategyContext:
    return cast(StrategyContext, ctx)


def _bars(
    instrument_id: InstrumentId,
    closes: tuple[str, ...],
    *,
    start_offset_days: int = 0,
) -> tuple[Bar, ...]:
    start = datetime(2020, 1, 1, tzinfo=UTC) + timedelta(days=start_offset_days)
    output: list[Bar] = []
    for index, close_text in enumerate(closes):
        close = Decimal(close_text)
        output.append(
            Bar(
                instrument_id=instrument_id,
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


def _bar(instrument_id: InstrumentId = GC_CARRY_ID) -> Bar:
    return Bar(
        instrument_id=instrument_id,
        start_time=datetime(2020, 1, 4, tzinfo=UTC),
        end_time=datetime(2020, 1, 5, tzinfo=UTC),
        timeframe="1d",
        session_id="2020-01-04",
        open=Decimal("1"),
        high=Decimal("1"),
        low=Decimal("1"),
        close=Decimal("1"),
        volume=Decimal("1"),
        is_complete=True,
    )


def test_carry_trend_overlay_subscribes_to_trade_and_signal_assets() -> None:
    from examples.strategies.carry_trend_overlay import CarryTrendOverlayStrategy

    ctx = FakeContext(FakeDataView(("100", "101", "102", "103"), ("0.01", "0.01")))
    strategy = CarryTrendOverlayStrategy(
        symbols=("GC",),
        carry_symbols={"GC": "GC_CARRY"},
        momentum_lookback_bars=3,
        volatility_lookback_bars=3,
        carry_lookback_bars=2,
        history_buffer_bars=0,
    )

    strategy.initialize(_ctx(ctx))

    assert ctx.subscriptions == [
        (ctx.gc_asset, "1d", 4),
        (ctx.carry_asset, "1d", 2),
    ]


def test_carry_trend_overlay_targets_trade_asset_when_trend_and_carry_agree() -> None:
    from examples.strategies.carry_trend_overlay import CarryTrendOverlayStrategy

    ctx = FakeContext(FakeDataView(("100", "101", "102", "103"), ("0.01", "0.02")))
    strategy = CarryTrendOverlayStrategy(
        symbols=("GC",),
        carry_symbols={"GC": "GC_CARRY"},
        momentum_lookback_bars=3,
        volatility_lookback_bars=3,
        carry_lookback_bars=2,
        min_momentum_return=Decimal("0.02"),
        min_carry=Decimal("0.005"),
        max_target_percent=Decimal("0.50"),
        target_annual_vol=Decimal("0.20"),
        history_buffer_bars=0,
    )
    strategy.initialize(_ctx(ctx))

    strategy.on_bar(_ctx(ctx), _bar(GC_CARRY_ID))

    assert ctx.intents == [("target_percent", ctx.gc_asset, Decimal("0.50"))]
    assert all(intent[1] != ctx.carry_asset for intent in ctx.intents)


def test_carry_trend_overlay_closes_when_carry_disagrees() -> None:
    from examples.strategies.carry_trend_overlay import CarryTrendOverlayStrategy

    data = FakeDataView(("100", "101", "102", "103"), ("0.01", "0.02"))
    ctx = FakeContext(data)
    strategy = CarryTrendOverlayStrategy(
        symbols=("GC",),
        carry_symbols={"GC": "GC_CARRY"},
        momentum_lookback_bars=3,
        volatility_lookback_bars=3,
        carry_lookback_bars=2,
        min_momentum_return=Decimal("0.02"),
        min_carry=Decimal("0.005"),
        max_target_percent=Decimal("0.50"),
        target_annual_vol=Decimal("0.20"),
        history_buffer_bars=0,
    )
    strategy.initialize(_ctx(ctx))
    strategy.on_bar(_ctx(ctx), _bar(GC_CARRY_ID))

    data.set_closes(("100", "101", "102", "103"), ("-0.01", "-0.02"))
    strategy.on_bar(_ctx(ctx), _bar(GC_CARRY_ID))

    assert ctx.intents == [
        ("target_percent", ctx.gc_asset, Decimal("0.50")),
        ("close", ctx.gc_asset, None),
    ]


def test_backtest_loader_can_instantiate_carry_trend_overlay_with_yaml_params() -> None:
    from qts.backtest.pipeline import BacktestPipeline

    from examples.strategies.carry_trend_overlay import CarryTrendOverlayStrategy

    strategy = BacktestPipeline.load_strategy(
        "examples.strategies.carry_trend_overlay:CarryTrendOverlayStrategy",
        {
            "symbols": ["GC"],
            "carry_symbols": {"GC": "GC_CARRY"},
            "timeframe": "1d",
            "momentum_lookback_bars": 3,
            "volatility_lookback_bars": 3,
            "carry_lookback_bars": 2,
            "min_momentum_return": "0.02",
            "min_carry": "0.005",
            "target_annual_vol": "0.20",
            "max_target_percent": "0.50",
            "history_buffer_bars": 0,
            "allow_short": True,
        },
    )
    ctx = FakeContext(FakeDataView(("100", "101", "102", "103"), ("0.01", "0.02")))

    strategy.initialize(_ctx(ctx))

    assert isinstance(strategy, CarryTrendOverlayStrategy)
    assert ctx.subscriptions == [
        (ctx.gc_asset, "1d", 4),
        (ctx.carry_asset, "1d", 2),
    ]
