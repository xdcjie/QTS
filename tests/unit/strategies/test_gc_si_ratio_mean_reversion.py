from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import cast

from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar
from qts.strategy_sdk import AssetRef, StrategyContext

GC_ID = InstrumentId("FUTURE.CME.GC.GCG0")
SI_ID = InstrumentId("FUTURE.CME.SI.SIH0")


class FakeDataView:
    def __init__(
        self,
        gc_closes: tuple[str, ...],
        si_closes: tuple[str, ...],
        *,
        gc_start_offset_days: int = 0,
        si_start_offset_days: int = 0,
    ) -> None:
        self.as_of = datetime(2020, 1, 10, tzinfo=UTC)
        self._gc_closes = gc_closes
        self._si_closes = si_closes
        self._gc_start_offset_days = gc_start_offset_days
        self._si_start_offset_days = si_start_offset_days

    def set_closes(self, gc_closes: tuple[str, ...], si_closes: tuple[str, ...]) -> None:
        self.as_of += timedelta(days=1)
        self._gc_closes = gc_closes
        self._si_closes = si_closes
        self._gc_start_offset_days += 1
        self._si_start_offset_days += 1

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
                GC_ID, self._gc_closes[-bars:], start_offset_days=self._gc_start_offset_days
            )
        if asset.instrument_id == SI_ID:
            return _bars(
                SI_ID, self._si_closes[-bars:], start_offset_days=self._si_start_offset_days
            )
        return ()


@dataclass
class FakeContext:
    data: FakeDataView

    def __post_init__(self) -> None:
        self.gc_asset = AssetRef(GC_ID, "GC")
        self.si_asset = AssetRef(SI_ID, "SI")
        self.intents: list[tuple[str, AssetRef, Decimal | None]] = []
        self.subscriptions: list[tuple[AssetRef, str, int]] = []

    def future(self, symbol: str) -> AssetRef:
        if symbol == "GC":
            return self.gc_asset
        if symbol == "SI":
            return self.si_asset
        raise KeyError(symbol)

    def symbol(self, symbol: str) -> AssetRef:
        return AssetRef(InstrumentId(f"EQUITY.TEST.{symbol}"), symbol)

    def subscribe(self, asset: AssetRef, *, timeframe: str, warmup: int = 1) -> None:
        self.subscriptions.append((asset, timeframe, warmup))

    def target_quantity(self, asset: AssetRef, quantity: Decimal) -> None:
        self.intents.append(("target_quantity", asset, quantity))

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
        start_time=datetime(2020, 1, 10, tzinfo=UTC),
        end_time=datetime(2020, 1, 11, tzinfo=UTC),
        timeframe="1d",
        session_id="2020-01-10",
        open=Decimal("100"),
        high=Decimal("100"),
        low=Decimal("100"),
        close=Decimal("100"),
        volume=Decimal("100"),
        is_complete=True,
    )


def test_gc_si_ratio_strategy_subscribes_to_both_daily_legs() -> None:
    from examples.strategies.gc_si_ratio_mean_reversion import GcSiRatioMeanReversionStrategy

    ctx = FakeContext(FakeDataView(("100", "101", "102"), ("10", "10", "10")))
    strategy = GcSiRatioMeanReversionStrategy(lookback_bars=3)

    strategy.initialize(_ctx(ctx))

    assert ctx.subscriptions == [
        (ctx.gc_asset, "1d", 3),
        (ctx.si_asset, "1d", 3),
    ]


def test_gc_si_ratio_strategy_shorts_ratio_when_zscore_is_high() -> None:
    from examples.strategies.gc_si_ratio_mean_reversion import GcSiRatioMeanReversionStrategy

    ctx = FakeContext(FakeDataView(("100", "100", "130"), ("10", "10", "10")))
    strategy = GcSiRatioMeanReversionStrategy(
        lookback_bars=3,
        entry_z=Decimal("0.70"),
        exit_z=Decimal("0.10"),
        gc_contracts=Decimal("1"),
        si_contracts=Decimal("2"),
    )
    strategy.initialize(_ctx(ctx))

    strategy.on_bar(_ctx(ctx), _bar(GC_ID))

    assert ctx.intents == [
        ("target_quantity", ctx.gc_asset, Decimal("-1")),
        ("target_quantity", ctx.si_asset, Decimal("2")),
    ]


def test_gc_si_ratio_strategy_longs_ratio_when_zscore_is_low() -> None:
    from examples.strategies.gc_si_ratio_mean_reversion import GcSiRatioMeanReversionStrategy

    ctx = FakeContext(FakeDataView(("100", "100", "70"), ("10", "10", "10")))
    strategy = GcSiRatioMeanReversionStrategy(
        lookback_bars=3,
        entry_z=Decimal("0.70"),
        exit_z=Decimal("0.10"),
        gc_contracts=Decimal("1"),
        si_contracts=Decimal("2"),
    )
    strategy.initialize(_ctx(ctx))

    strategy.on_bar(_ctx(ctx), _bar(SI_ID))

    assert ctx.intents == [
        ("target_quantity", ctx.gc_asset, Decimal("1")),
        ("target_quantity", ctx.si_asset, Decimal("-2")),
    ]


def test_gc_si_ratio_strategy_closes_both_legs_when_ratio_reverts() -> None:
    from examples.strategies.gc_si_ratio_mean_reversion import GcSiRatioMeanReversionStrategy

    data = FakeDataView(("100", "100", "130"), ("10", "10", "10"))
    ctx = FakeContext(data)
    strategy = GcSiRatioMeanReversionStrategy(
        lookback_bars=3,
        entry_z=Decimal("0.70"),
        exit_z=Decimal("0.10"),
        gc_contracts=Decimal("1"),
        si_contracts=Decimal("2"),
    )
    strategy.initialize(_ctx(ctx))
    strategy.on_bar(_ctx(ctx), _bar(GC_ID))

    data.set_closes(("100", "100", "100"), ("10", "10", "10"))
    strategy.on_bar(_ctx(ctx), _bar(GC_ID))

    assert ctx.intents == [
        ("target_quantity", ctx.gc_asset, Decimal("-1")),
        ("target_quantity", ctx.si_asset, Decimal("2")),
        ("close", ctx.gc_asset, None),
        ("close", ctx.si_asset, None),
    ]


def test_gc_si_ratio_strategy_suppresses_duplicate_targets_for_same_bar() -> None:
    from examples.strategies.gc_si_ratio_mean_reversion import GcSiRatioMeanReversionStrategy

    ctx = FakeContext(FakeDataView(("100", "100", "130"), ("10", "10", "10")))
    strategy = GcSiRatioMeanReversionStrategy(
        lookback_bars=3,
        entry_z=Decimal("0.70"),
        exit_z=Decimal("0.10"),
        gc_contracts=Decimal("1"),
        si_contracts=Decimal("2"),
    )
    strategy.initialize(_ctx(ctx))

    strategy.on_bar(_ctx(ctx), _bar(GC_ID))
    strategy.on_bar(_ctx(ctx), _bar(SI_ID))

    assert ctx.intents == [
        ("target_quantity", ctx.gc_asset, Decimal("-1")),
        ("target_quantity", ctx.si_asset, Decimal("2")),
    ]


def test_gc_si_ratio_strategy_waits_for_aligned_leg_history() -> None:
    from examples.strategies.gc_si_ratio_mean_reversion import GcSiRatioMeanReversionStrategy

    ctx = FakeContext(
        FakeDataView(
            ("100", "100", "130"),
            ("10", "10", "10"),
            si_start_offset_days=-1,
        )
    )
    strategy = GcSiRatioMeanReversionStrategy(
        lookback_bars=3,
        entry_z=Decimal("0.70"),
        exit_z=Decimal("0.10"),
        gc_contracts=Decimal("1"),
        si_contracts=Decimal("2"),
    )
    strategy.initialize(_ctx(ctx))

    strategy.on_bar(_ctx(ctx), _bar(GC_ID))

    assert ctx.intents == []


def test_backtest_loader_can_instantiate_gc_si_ratio_strategy_with_yaml_params() -> None:
    from qts.backtest.pipeline import BacktestPipeline

    strategy = BacktestPipeline.load_strategy(
        "examples.strategies.gc_si_ratio_mean_reversion:GcSiRatioMeanReversionStrategy",
        {
            "gc_symbol": "GC",
            "si_symbol": "SI",
            "timeframe": "1d",
            "lookback_bars": 3,
            "entry_z": "0.70",
            "exit_z": "0.10",
            "gc_contracts": "1",
            "si_contracts": "2",
            "min_ratio_std": "0.0001",
        },
    )
    ctx = FakeContext(FakeDataView(("100", "100", "130"), ("10", "10", "10")))

    strategy.initialize(_ctx(ctx))

    assert ctx.subscriptions == [
        (ctx.gc_asset, "1d", 3),
        (ctx.si_asset, "1d", 3),
    ]
