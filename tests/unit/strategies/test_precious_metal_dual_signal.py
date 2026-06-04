from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import cast

from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar
from qts.strategy_sdk import AssetRef, PortfolioView, StrategyContext

GC_ID = InstrumentId("CONTINUOUS_FUTURE.CME.GC")
VIX_ID = InstrumentId("RESEARCH.TEST.VIX")
REAL_YIELD_ID = InstrumentId("RESEARCH.TEST.REALYIELD10Y")


class FakeDataView:
    def __init__(self, closes_by_symbol: dict[str, tuple[str, ...]]) -> None:
        self._closes_by_symbol = closes_by_symbol

    def history(
        self,
        asset: AssetRef,
        *,
        bars: int,
        timeframe: str | None = None,
    ) -> tuple[Bar, ...]:
        _ = timeframe
        if asset.instrument_id == GC_ID:
            return _bars(GC_ID, self._closes_by_symbol["GC"][-bars:])
        if asset.instrument_id == VIX_ID:
            return _bars(VIX_ID, self._closes_by_symbol["VIX"][-bars:])
        if asset.instrument_id == REAL_YIELD_ID:
            return _bars(REAL_YIELD_ID, self._closes_by_symbol["REALYIELD10Y"][-bars:])
        return ()


@dataclass
class FakeContext:
    data: FakeDataView
    portfolio: PortfolioView | None = None

    def __post_init__(self) -> None:
        self.gc_asset = AssetRef(GC_ID, "GC")
        self.vix_asset = AssetRef(VIX_ID, "VIX")
        self.real_yield_asset = AssetRef(REAL_YIELD_ID, "REALYIELD10Y")
        self.intents: list[tuple[str, AssetRef, Decimal | None]] = []
        self.subscriptions: list[tuple[AssetRef, str, int]] = []

    def future(self, symbol: str) -> AssetRef:
        if symbol == "GC":
            return self.gc_asset
        raise KeyError(symbol)

    def symbol(self, symbol: str) -> AssetRef:
        if symbol == "VIX":
            return self.vix_asset
        if symbol == "REALYIELD10Y":
            return self.real_yield_asset
        raise KeyError(symbol)

    def subscribe(self, asset: AssetRef, *, timeframe: str, warmup: int = 1) -> None:
        self.subscriptions.append((asset, timeframe, warmup))

    def target_quantity(self, asset: AssetRef, quantity: Decimal) -> None:
        self.intents.append(("target_quantity", asset, quantity))

    def close(self, asset: AssetRef) -> None:
        self.intents.append(("close", asset, None))


def _ctx(ctx: FakeContext) -> StrategyContext:
    return cast(StrategyContext, ctx)


def _bars(instrument_id: InstrumentId, closes: tuple[str, ...]) -> tuple[Bar, ...]:
    start = datetime(2020, 1, 1, tzinfo=UTC)
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


def _bar() -> Bar:
    return _bars(GC_ID, ("100", "101", "102"))[-1]


def test_dual_signal_confirm_policy_requires_secondary_agreement() -> None:
    from strategies.research.precious_metal_dual_signal import PreciousMetalDualSignalStrategy

    ctx = FakeContext(
        FakeDataView(
            {
                "GC": ("100", "101", "102"),
                "VIX": ("100", "101", "103", "106"),
                "REALYIELD10Y": ("10", "10", "10", "10"),
            }
        )
    )
    strategy = PreciousMetalDualSignalStrategy(
        trade_symbol="GC",
        primary_symbol="VIX",
        secondary_symbol="REALYIELD10Y",
        primary_lookback_bars=3,
        secondary_lookback_bars=3,
        primary_direction="follow",
        secondary_direction="fade",
        primary_entry_z=Decimal("1"),
        secondary_entry_z=Decimal("1"),
        secondary_policy="confirm",
        history_buffer_bars=0,
    )
    strategy.initialize(_ctx(ctx))

    strategy.on_bar(_ctx(ctx), _bar())

    assert ctx.intents == []


def test_dual_signal_veto_policy_allows_neutral_secondary_signal() -> None:
    from strategies.research.precious_metal_dual_signal import PreciousMetalDualSignalStrategy

    ctx = FakeContext(
        FakeDataView(
            {
                "GC": ("100", "101", "102"),
                "VIX": ("100", "101", "103", "106"),
                "REALYIELD10Y": ("10", "10", "10", "10"),
            }
        )
    )
    strategy = PreciousMetalDualSignalStrategy(
        trade_symbol="GC",
        primary_symbol="VIX",
        secondary_symbol="REALYIELD10Y",
        primary_lookback_bars=3,
        secondary_lookback_bars=3,
        primary_direction="follow",
        secondary_direction="fade",
        primary_entry_z=Decimal("1"),
        secondary_entry_z=Decimal("1"),
        secondary_policy="veto",
        history_buffer_bars=0,
    )
    strategy.initialize(_ctx(ctx))

    strategy.on_bar(_ctx(ctx), _bar())

    assert ctx.intents == [("target_quantity", ctx.gc_asset, Decimal("1"))]


def test_dual_signal_veto_policy_blocks_opposed_secondary_signal() -> None:
    from strategies.research.precious_metal_dual_signal import PreciousMetalDualSignalStrategy

    ctx = FakeContext(
        FakeDataView(
            {
                "GC": ("100", "101", "102"),
                "VIX": ("100", "101", "103", "106"),
                "REALYIELD10Y": ("10", "11", "13", "16"),
            }
        )
    )
    strategy = PreciousMetalDualSignalStrategy(
        trade_symbol="GC",
        primary_symbol="VIX",
        secondary_symbol="REALYIELD10Y",
        primary_lookback_bars=3,
        secondary_lookback_bars=3,
        primary_direction="follow",
        secondary_direction="fade",
        primary_entry_z=Decimal("1"),
        secondary_entry_z=Decimal("1"),
        secondary_policy="veto",
        history_buffer_bars=0,
    )
    strategy.initialize(_ctx(ctx))

    strategy.on_bar(_ctx(ctx), _bar())

    assert ctx.intents == []
