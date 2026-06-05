from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.domain.market_data.bar import Bar
from qts.strategy_sdk.asset_ref import AssetRef

from strategies.research.precious_metal_microtrend_acd_switch import (
    PreciousMetalMicrotrendAcdSwitchStrategy,
)


class _Data:
    def __init__(self) -> None:
        self._history: dict[str, tuple[Bar, ...]] = {}

    def set_history(self, timeframe: str, bars: tuple[Bar, ...]) -> None:
        self._history[timeframe] = bars

    def history(self, _asset: AssetRef, *, bars: int, timeframe: str) -> tuple[Bar, ...]:
        return self._history.get(timeframe, ())[-bars:]


class _Ctx:
    def __init__(self) -> None:
        self.asset = AssetRef(InstrumentId("FUT.CME.SI"), "SI")
        self.data = _Data()
        self.subscriptions: list[tuple[AssetRef, str, int]] = []
        self.targets: list[tuple[AssetRef, Decimal, dict[str, str] | None]] = []

    def future(self, root_symbol: str, *, contract: str = "front") -> AssetRef:
        assert root_symbol == "SI"
        assert contract == "front"
        return self.asset

    def subscribe(self, asset: AssetRef, *, timeframe: str, warmup: int) -> None:
        self.subscriptions.append((asset, timeframe, warmup))

    def target_quantity(
        self,
        asset: AssetRef,
        quantity: Decimal,
        *,
        metadata: dict[str, str] | None = None,
    ) -> None:
        self.targets.append((asset, quantity, metadata))

    def close(self, asset: AssetRef, *, metadata: dict[str, str] | None = None) -> None:
        self.targets.append((asset, Decimal("0"), metadata))


def _bar(
    *,
    minute: int,
    timeframe: str,
    open_: str,
    high: str,
    low: str,
    close: str,
    volume: str = "100",
    session_id: str = "2026-01-02",
) -> Bar:
    start = datetime(2026, 1, 2, 23, 0, tzinfo=UTC) + timedelta(minutes=minute)
    minutes = int(timeframe.removesuffix("m"))
    return Bar(
        instrument_id=InstrumentId("FUT.CME.SI"),
        start_time=start,
        end_time=start + timedelta(minutes=minutes),
        timeframe=timeframe,
        session_id=session_id,
        open=Decimal(open_),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(close),
        volume=Decimal(volume),
        is_complete=True,
    )


def test_initializes_single_timeframe_once() -> None:
    strategy = PreciousMetalMicrotrendAcdSwitchStrategy(
        symbol="SI",
        timeframe="3m",
    )
    ctx = _Ctx()

    strategy.initialize(ctx)

    assert [item[1] for item in ctx.subscriptions] == ["3m"]
    assert all(item[2] > 0 for item in ctx.subscriptions)


def test_microtrend_entry_suppresses_acd_breakout_entry() -> None:
    strategy = PreciousMetalMicrotrendAcdSwitchStrategy(
        symbol="SI",
        timeframe="3m",
        micro_fast_bars=2,
        micro_slow_bars=4,
        micro_vwap_lookback_bars=4,
        micro_volume_lookback_bars=3,
        micro_atr_lookback_bars=3,
        micro_entry_return_threshold=Decimal("0"),
        micro_min_volume_ratio=Decimal("0"),
        micro_min_vwap_distance_bps=Decimal("0"),
        micro_max_vwap_distance_bps=Decimal("10000"),
        micro_signal_confirm_bars=1,
        acd_opening_range_bars=2,
        acd_max_entry_bars=5,
        target_quantity=Decimal("1"),
    )
    ctx = _Ctx()
    strategy.initialize(ctx)
    micro_history = (
        _bar(minute=0, timeframe="3m", open_="20", high="20.2", low="19.9", close="20.0"),
        _bar(minute=3, timeframe="3m", open_="20.0", high="20.3", low="19.9", close="20.1"),
        _bar(minute=6, timeframe="3m", open_="20.1", high="20.5", low="20.0", close="20.3"),
        _bar(minute=9, timeframe="3m", open_="20.3", high="20.8", low="20.2", close="20.7"),
    )
    acd_range_a = _bar(minute=0, timeframe="3m", open_="20", high="20.2", low="19.9", close="20.1")
    acd_range_b = _bar(minute=3, timeframe="3m", open_="20.1", high="20.3", low="20.0", close="20.2")
    strategy.on_bar(ctx, acd_range_a)
    strategy.on_bar(ctx, acd_range_b)
    ctx.data.set_history("3m", micro_history)

    strategy.on_bar(ctx, micro_history[-1])

    assert ctx.targets == [(ctx.asset, Decimal("1"), {"source": "microtrend", "reason": "entry"})]


def test_acd_enters_when_microtrend_is_flat() -> None:
    strategy = PreciousMetalMicrotrendAcdSwitchStrategy(
        symbol="SI",
        timeframe="3m",
        acd_opening_range_bars=2,
        acd_max_entry_bars=5,
        acd_entry_buffer_ratio=Decimal("0"),
        target_quantity=Decimal("1"),
    )
    ctx = _Ctx()
    strategy.initialize(ctx)

    strategy.on_bar(
        ctx,
        _bar(minute=0, timeframe="3m", open_="20", high="20.2", low="19.9", close="20.1"),
    )
    strategy.on_bar(
        ctx,
        _bar(minute=3, timeframe="3m", open_="20.1", high="20.3", low="20.0", close="20.2"),
    )
    strategy.on_bar(
        ctx,
        _bar(minute=6, timeframe="3m", open_="20.2", high="20.8", low="20.2", close="20.7"),
    )

    assert ctx.targets[-1][1] == Decimal("1")
    assert ctx.targets[-1][2] == {"source": "acd", "reason": "entry"}


def test_microtrend_respects_session_entry_limit() -> None:
    strategy = PreciousMetalMicrotrendAcdSwitchStrategy(
        symbol="SI",
        timeframe="3m",
        micro_fast_bars=2,
        micro_slow_bars=4,
        micro_vwap_lookback_bars=4,
        micro_volume_lookback_bars=3,
        micro_atr_lookback_bars=3,
        micro_entry_return_threshold=Decimal("0"),
        micro_min_volume_ratio=Decimal("0"),
        micro_min_vwap_distance_bps=Decimal("0"),
        micro_max_vwap_distance_bps=Decimal("10000"),
        micro_max_entries_per_session=1,
        micro_min_bars_between_entries=1,
        micro_post_exit_cooldown_bars=1,
        target_quantity=Decimal("1"),
    )
    ctx = _Ctx()
    strategy.initialize(ctx)
    first_history = (
        _bar(minute=0, timeframe="3m", open_="20", high="20.2", low="19.9", close="20.0"),
        _bar(minute=3, timeframe="3m", open_="20.0", high="20.3", low="19.9", close="20.1"),
        _bar(minute=6, timeframe="3m", open_="20.1", high="20.5", low="20.0", close="20.3"),
        _bar(minute=9, timeframe="3m", open_="20.3", high="20.8", low="20.2", close="20.7"),
    )
    ctx.data.set_history("3m", first_history)

    strategy.on_bar(ctx, first_history[-1])
    strategy.on_bar(
        ctx,
        _bar(minute=12, timeframe="3m", open_="20.7", high="25.0", low="20.7", close="24.8"),
    )
    ctx.targets.clear()
    second_history = (
        _bar(minute=15, timeframe="3m", open_="20", high="20.2", low="19.9", close="20.0"),
        _bar(minute=18, timeframe="3m", open_="20.0", high="20.3", low="19.9", close="20.1"),
        _bar(minute=21, timeframe="3m", open_="20.1", high="20.5", low="20.0", close="20.3"),
        _bar(minute=24, timeframe="3m", open_="20.3", high="20.8", low="20.2", close="20.7"),
    )
    ctx.data.set_history("3m", second_history)

    strategy.on_bar(ctx, second_history[-1])

    assert ctx.targets == []


def test_microtrend_quality_gate_blocks_narrow_opening_range() -> None:
    strategy = PreciousMetalMicrotrendAcdSwitchStrategy(
        symbol="SI",
        timeframe="3m",
        micro_fast_bars=2,
        micro_slow_bars=4,
        micro_vwap_lookback_bars=4,
        micro_volume_lookback_bars=3,
        micro_atr_lookback_bars=3,
        micro_entry_return_threshold=Decimal("0"),
        micro_min_volume_ratio=Decimal("0"),
        micro_min_vwap_distance_bps=Decimal("0"),
        micro_max_vwap_distance_bps=Decimal("10000"),
        micro_require_acd_opening_range=True,
        micro_min_opening_range_bps=Decimal("100"),
        acd_opening_range_bars=2,
        acd_max_entry_bars=5,
        acd_entry_buffer_ratio=Decimal("100"),
        target_quantity=Decimal("1"),
    )
    ctx = _Ctx()
    strategy.initialize(ctx)
    strategy.on_bar(
        ctx,
        _bar(minute=0, timeframe="3m", open_="20", high="20.02", low="20.00", close="20.01"),
    )
    strategy.on_bar(
        ctx,
        _bar(minute=3, timeframe="3m", open_="20.01", high="20.05", low="20.01", close="20.04"),
    )
    micro_history = (
        _bar(minute=0, timeframe="3m", open_="20", high="20.2", low="19.9", close="20.0"),
        _bar(minute=3, timeframe="3m", open_="20.0", high="20.3", low="19.9", close="20.1"),
        _bar(minute=6, timeframe="3m", open_="20.1", high="20.5", low="20.0", close="20.3"),
        _bar(minute=9, timeframe="3m", open_="20.3", high="20.8", low="20.2", close="20.7"),
    )
    ctx.data.set_history("3m", micro_history)

    strategy.on_bar(ctx, micro_history[-1])

    assert ctx.targets == []
