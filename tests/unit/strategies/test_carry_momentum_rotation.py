from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import cast

from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar
from qts.strategy_sdk import AssetRef, StrategyContext

GC_ID = InstrumentId("CONTINUOUS_FUTURE.CME.GC")
SI_ID = InstrumentId("CONTINUOUS_FUTURE.CME.SI")
GC_CARRY_ID = InstrumentId("RESEARCH.CARRY.GC")
SI_CARRY_ID = InstrumentId("RESEARCH.CARRY.SI")


class FakeDataView:
    def __init__(self, closes_by_symbol: dict[str, tuple[str, ...]]) -> None:
        self._closes_by_symbol = closes_by_symbol
        self._start_offset_days = 0

    def set_closes(self, closes_by_symbol: dict[str, tuple[str, ...]]) -> None:
        self._closes_by_symbol = closes_by_symbol
        self._start_offset_days += 1

    def history(
        self,
        asset: AssetRef,
        *,
        bars: int,
        timeframe: str | None = None,
    ) -> tuple[Bar, ...]:
        _ = timeframe
        symbol = asset.symbol
        closes = self._closes_by_symbol.get(symbol, ())[-bars:]
        max_length = max((len(values) for values in self._closes_by_symbol.values()), default=0)
        return _bars(
            asset.instrument_id,
            closes,
            start_offset_days=self._start_offset_days + max(max_length - len(closes), 0),
        )


@dataclass
class FakeContext:
    data: FakeDataView

    def __post_init__(self) -> None:
        self.gc_asset = AssetRef(GC_ID, "GC")
        self.si_asset = AssetRef(SI_ID, "SI")
        self.gc_carry_asset = AssetRef(GC_CARRY_ID, "GC_CARRY")
        self.si_carry_asset = AssetRef(SI_CARRY_ID, "SI_CARRY")
        self.subscriptions: list[tuple[AssetRef, str, int]] = []
        self.intents: list[tuple[str, AssetRef, Decimal | None]] = []

    def future(self, symbol: str) -> AssetRef:
        if symbol == "GC":
            return self.gc_asset
        if symbol == "SI":
            return self.si_asset
        raise KeyError(symbol)

    def symbol(self, symbol: str) -> AssetRef:
        if symbol == "GC_CARRY":
            return self.gc_carry_asset
        if symbol == "SI_CARRY":
            return self.si_carry_asset
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


def _bar(instrument_id: InstrumentId = GC_ID) -> Bar:
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


def test_carry_momentum_rotation_subscribes_to_trade_and_carry_assets() -> None:
    from examples.strategies.carry_momentum_rotation import CarryMomentumRotationStrategy

    ctx = FakeContext(
        FakeDataView(
            {
                "GC": ("100", "101", "102", "103", "104"),
                "SI": ("20", "21", "22", "23", "24"),
                "GC_CARRY": ("0.01", "0.02", "0.03"),
                "SI_CARRY": ("0.01", "0.02", "0.03"),
            }
        )
    )
    strategy = CarryMomentumRotationStrategy(
        symbols=("GC", "SI"),
        carry_symbols={"GC": "GC_CARRY", "SI": "SI_CARRY"},
        momentum_lookback_bars=(2, 4),
        volatility_lookback_bars=3,
        carry_zscore_lookback_bars=3,
        history_buffer_bars=0,
    )

    strategy.initialize(_ctx(ctx))

    assert ctx.subscriptions == [
        (ctx.gc_asset, "1d", 5),
        (ctx.gc_carry_asset, "1d", 3),
        (ctx.si_asset, "1d", 5),
        (ctx.si_carry_asset, "1d", 3),
    ]


def test_carry_momentum_rotation_can_select_carry_confirmed_asset() -> None:
    from examples.strategies.carry_momentum_rotation import CarryMomentumRotationStrategy

    ctx = FakeContext(
        FakeDataView(
            {
                "GC": ("100", "110", "120", "130", "140"),
                "SI": ("100", "104", "108", "112", "116"),
                "GC_CARRY": ("0", "0.02", "-0.02"),
                "SI_CARRY": ("0", "-0.02", "0.02"),
            }
        )
    )
    strategy = CarryMomentumRotationStrategy(
        symbols=("GC", "SI"),
        carry_symbols={"GC": "GC_CARRY", "SI": "SI_CARRY"},
        momentum_lookback_bars=(2, 4),
        volatility_lookback_bars=3,
        carry_zscore_lookback_bars=3,
        carry_zscore_weight=Decimal("0.20"),
        min_score=Decimal("0"),
        min_relative_score=Decimal("0.02"),
        target_annual_vol=Decimal("1"),
        max_target_percent=Decimal("0.50"),
        history_buffer_bars=0,
    )
    strategy.initialize(_ctx(ctx))

    strategy.on_bar(_ctx(ctx), _bar(GC_ID))

    assert ctx.intents == [("target_percent", ctx.si_asset, Decimal("0.50"))]


def test_carry_momentum_rotation_stays_flat_when_relative_score_is_too_small() -> None:
    from examples.strategies.carry_momentum_rotation import CarryMomentumRotationStrategy

    ctx = FakeContext(
        FakeDataView(
            {
                "GC": ("100", "101", "102", "103", "104"),
                "SI": ("100", "101", "102", "103", "104"),
                "GC_CARRY": ("0", "0.01", "0.02"),
                "SI_CARRY": ("0", "0.01", "0.02"),
            }
        )
    )
    strategy = CarryMomentumRotationStrategy(
        symbols=("GC", "SI"),
        carry_symbols={"GC": "GC_CARRY", "SI": "SI_CARRY"},
        momentum_lookback_bars=(2, 4),
        volatility_lookback_bars=3,
        carry_zscore_lookback_bars=3,
        min_score=Decimal("0"),
        min_relative_score=Decimal("0.05"),
        history_buffer_bars=0,
    )
    strategy.initialize(_ctx(ctx))

    strategy.on_bar(_ctx(ctx), _bar(GC_ID))

    assert ctx.intents == []


def test_backtest_loader_can_instantiate_carry_momentum_rotation_with_yaml_params() -> None:
    from qts.backtest.pipeline import BacktestPipeline

    from examples.strategies.carry_momentum_rotation import CarryMomentumRotationStrategy

    strategy = BacktestPipeline.load_strategy(
        "examples.strategies.carry_momentum_rotation:CarryMomentumRotationStrategy",
        {
            "symbols": ["GC", "SI"],
            "carry_symbols": {"GC": "GC_CARRY", "SI": "SI_CARRY"},
            "timeframe": "1d",
            "momentum_lookback_bars": [21, 63, 126],
            "volatility_lookback_bars": 40,
            "carry_zscore_lookback_bars": 20,
            "carry_zscore_weight": "0.02",
            "min_score": "0",
            "min_relative_score": "0.02",
            "target_annual_vol": "0.20",
            "max_target_percent": "0.50",
            "rebalance_threshold": "0.01",
            "history_buffer_bars": 20,
        },
    )

    assert isinstance(strategy, CarryMomentumRotationStrategy)
