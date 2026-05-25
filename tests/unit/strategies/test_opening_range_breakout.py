from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, cast
from zoneinfo import ZoneInfo

from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar
from qts.strategy_sdk import AssetRef, StrategyContext

GC_ID = InstrumentId("CONTINUOUS_FUTURE.CME.GC")
SI_ID = InstrumentId("CONTINUOUS_FUTURE.CME.SI")
ET = ZoneInfo("US/Eastern")


@dataclass
class FakeContext:
    def __post_init__(self) -> None:
        self.gc_asset = AssetRef(GC_ID, "GC")
        self.si_asset = AssetRef(SI_ID, "SI")
        self.subscriptions: list[tuple[AssetRef, str, int]] = []
        self.intents: list[tuple[str, AssetRef, Decimal | None, dict[str, str]]] = []

    def future(self, symbol: str) -> AssetRef:
        if symbol == "GC":
            return self.gc_asset
        if symbol == "SI":
            return self.si_asset
        raise KeyError(symbol)

    def subscribe(self, asset: AssetRef, *, timeframe: str, warmup: int = 1) -> None:
        self.subscriptions.append((asset, timeframe, warmup))

    def target_quantity(
        self,
        asset: AssetRef,
        quantity: Decimal,
        *,
        metadata: Mapping[str, str] | None = None,
    ) -> None:
        self.intents.append(("target_quantity", asset, quantity, dict(metadata or {})))

    def close(
        self,
        asset: AssetRef,
        *,
        metadata: Mapping[str, str] | None = None,
    ) -> None:
        self.intents.append(("close", asset, None, dict(metadata or {})))


def _ctx(ctx: FakeContext) -> StrategyContext:
    return cast(StrategyContext, ctx)


def _bar(
    *,
    minute: int,
    session_id: str = "2020-01-02",
    open_: str = "100",
    high: str = "100",
    low: str = "100",
    close: str = "100",
    instrument_id: InstrumentId = GC_ID,
) -> Bar:
    hour, minute_of_hour = divmod(minute, 60)
    start = datetime(2020, 1, 1, hour, minute_of_hour, tzinfo=ET)
    if minute < 17 * 60:
        start = datetime(2020, 1, 2, hour, minute_of_hour, tzinfo=ET)
    return Bar(
        instrument_id=instrument_id,
        start_time=start,
        end_time=start + timedelta(minutes=15),
        timeframe="15m",
        session_id=session_id,
        open=Decimal(open_),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(close),
        volume=Decimal("100"),
        is_complete=True,
    )


def _feed_opening_range(strategy: Any, ctx: FakeContext, *, session_id: str) -> None:
    for index, close in enumerate(("100.0", "100.2", "99.8", "100.4")):
        strategy.on_bar(
            _ctx(ctx),
            _bar(
                minute=18 * 60 + index * 15,
                session_id=session_id,
                open_=close,
                high="101",
                low="99",
                close=close,
            ),
        )


def test_opening_range_strategy_subscribes_to_selected_future_timeframe() -> None:
    from examples.strategies.opening_range_breakout import OpeningRangeBreakoutStrategy

    ctx = FakeContext()
    strategy = OpeningRangeBreakoutStrategy(symbol="SI", timeframe="15m")

    strategy.initialize(_ctx(ctx))

    assert ctx.subscriptions == [(ctx.si_asset, "15m", 1)]


def test_opening_range_strategy_does_not_trade_before_range_is_complete() -> None:
    from examples.strategies.opening_range_breakout import OpeningRangeBreakoutStrategy

    ctx = FakeContext()
    strategy = OpeningRangeBreakoutStrategy(
        symbol="GC",
        opening_range_minutes=60,
        range_start_et="18:00",
        range_width_min_history_sessions=0,
    )
    strategy.initialize(_ctx(ctx))

    strategy.on_bar(
        _ctx(ctx),
        _bar(minute=18 * 60, high="103", low="99", close="102"),
    )

    assert ctx.intents == []


def test_opening_range_breakout_enters_after_completed_range_breaks_higher() -> None:
    from examples.strategies.opening_range_breakout import OpeningRangeBreakoutStrategy

    ctx = FakeContext()
    strategy = OpeningRangeBreakoutStrategy(
        symbol="GC",
        mode="breakout",
        opening_range_minutes=60,
        range_start_et="18:00",
        range_width_min_history_sessions=0,
        target_quantity=Decimal("2"),
    )
    strategy.initialize(_ctx(ctx))

    _feed_opening_range(strategy, ctx, session_id="2020-01-02")
    strategy.on_bar(
        _ctx(ctx),
        _bar(minute=19 * 60, high="102", low="100", close="101.5"),
    )

    assert ctx.intents == [
        (
            "target_quantity",
            ctx.gc_asset,
            Decimal("2"),
            {"entry_reason": "opening_range_breakout_long", "session_id": "2020-01-02"},
        )
    ]


def test_opening_range_failure_fades_false_high_break() -> None:
    from examples.strategies.opening_range_breakout import OpeningRangeBreakoutStrategy

    ctx = FakeContext()
    strategy = OpeningRangeBreakoutStrategy(
        symbol="GC",
        mode="failure",
        opening_range_minutes=60,
        range_start_et="18:00",
        range_width_min_history_sessions=0,
        target_quantity=Decimal("1"),
    )
    strategy.initialize(_ctx(ctx))

    _feed_opening_range(strategy, ctx, session_id="2020-01-02")
    strategy.on_bar(
        _ctx(ctx),
        _bar(minute=19 * 60, high="102", low="100", close="100.5"),
    )

    assert ctx.intents == [
        (
            "target_quantity",
            ctx.gc_asset,
            Decimal("-1"),
            {"entry_reason": "opening_range_failure_short", "session_id": "2020-01-02"},
        )
    ]


def test_opening_range_width_filter_uses_prior_completed_sessions_only() -> None:
    from examples.strategies.opening_range_breakout import OpeningRangeBreakoutStrategy

    ctx = FakeContext()
    strategy = OpeningRangeBreakoutStrategy(
        symbol="GC",
        mode="breakout",
        opening_range_minutes=60,
        range_start_et="18:00",
        range_width_lookback_sessions=5,
        range_width_min_history_sessions=1,
        max_range_width_ratio=Decimal("1.5"),
    )
    strategy.initialize(_ctx(ctx))

    _feed_opening_range(strategy, ctx, session_id="2020-01-02")
    strategy.on_bar(_ctx(ctx), _bar(minute=16 * 60, session_id="2020-01-02"))
    for index in range(4):
        strategy.on_bar(
            _ctx(ctx),
            _bar(
                minute=18 * 60 + index * 15,
                session_id="2020-01-03",
                high="104",
                low="100",
                close="103",
            ),
        )
    strategy.on_bar(
        _ctx(ctx),
        _bar(
            minute=19 * 60,
            session_id="2020-01-03",
            open_="104.5",
            high="106",
            low="104",
            close="105",
        ),
    )

    assert ctx.intents == []


def test_opening_range_strategy_flattens_before_session_close() -> None:
    from examples.strategies.opening_range_breakout import OpeningRangeBreakoutStrategy

    ctx = FakeContext()
    strategy = OpeningRangeBreakoutStrategy(
        symbol="GC",
        mode="breakout",
        opening_range_minutes=60,
        range_start_et="18:00",
        range_width_min_history_sessions=0,
        minutes_before_close_flat=60,
    )
    strategy.initialize(_ctx(ctx))
    _feed_opening_range(strategy, ctx, session_id="2020-01-02")
    strategy.on_bar(
        _ctx(ctx),
        _bar(minute=19 * 60, high="102", low="100", close="101.5"),
    )

    strategy.on_bar(
        _ctx(ctx),
        _bar(
            minute=16 * 60,
            session_id="2020-01-02",
            open_="101.1",
            high="102",
            low="101",
            close="101.2",
        ),
    )

    assert ctx.intents[-1] == (
        "close",
        ctx.gc_asset,
        None,
        {"exit_reason": "session_close_flat", "session_id": "2020-01-02"},
    )


def test_backtest_loader_can_instantiate_opening_range_strategy_with_yaml_params() -> None:
    from qts.backtest.pipeline import BacktestPipeline

    from examples.strategies.opening_range_breakout import OpeningRangeBreakoutStrategy

    strategy = BacktestPipeline.load_strategy(
        "examples.strategies.opening_range_breakout:OpeningRangeBreakoutStrategy",
        {
            "symbol": "GC",
            "timeframe": "15m",
            "mode": "failure",
            "range_start_et": "08:30",
            "opening_range_minutes": 60,
            "target_quantity": "1",
            "breakout_buffer_ratio": "0.05",
            "stop_range_multiple": "0.75",
            "target_range_multiple": "1.25",
            "minutes_before_close_flat": 60,
            "range_width_lookback_sessions": 20,
            "range_width_min_history_sessions": 10,
            "max_range_width_ratio": "2.0",
        },
    )

    assert isinstance(strategy, OpeningRangeBreakoutStrategy)
