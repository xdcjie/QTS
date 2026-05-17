"""Unit tests for Strategy SDK universe selection."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar
from qts.strategy_sdk import AssetRef, StrategyContext
from qts.strategy_sdk.universe import Universe


def test_universe_set_add_remove_uses_internal_instrument_ids() -> None:
    ctx = StrategyContext()
    aapl = AssetRef(InstrumentId("EQUITY.US.NASDAQ.AAPL"), "AAPL")
    msft = AssetRef(InstrumentId("EQUITY.US.NASDAQ.MSFT"), "MSFT")
    gc = InstrumentId("FUTURE.CME.GC.202606")

    universe = ctx.set_universe([msft, aapl, aapl])

    assert isinstance(universe, Universe)
    assert ctx.universe.instrument_ids == (
        InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        InstrumentId("EQUITY.US.NASDAQ.MSFT"),
    )

    ctx.add_to_universe([gc, msft])
    expected_after_add: tuple[InstrumentId, ...] = (
        InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        InstrumentId("EQUITY.US.NASDAQ.MSFT"),
        InstrumentId("FUTURE.CME.GC.202606"),
    )
    assert ctx.universe.instrument_ids == expected_after_add

    ctx.remove_from_universe([aapl])
    expected_after_remove: tuple[InstrumentId, ...] = (
        InstrumentId("EQUITY.US.NASDAQ.MSFT"),
        InstrumentId("FUTURE.CME.GC.202606"),
    )
    assert ctx.universe.instrument_ids == expected_after_remove


def test_universe_rejects_empty_selection_items() -> None:
    import pytest

    with pytest.raises(ValueError, match="at least one instrument"):
        Universe.from_members([])


def test_fundamental_top_n_selector_orders_by_metric_and_tie_breaks_by_instrument() -> None:
    from qts.strategy_sdk.universe import FundamentalTopNSelector, FundamentalUniverseRow

    selector = FundamentalTopNSelector(
        rows=(
            FundamentalUniverseRow(
                instrument_id=InstrumentId("EQUITY.US.NASDAQ.MSFT"),
                market_cap=Decimal("300"),
                dollar_volume=Decimal("900"),
            ),
            FundamentalUniverseRow(
                instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
                market_cap=Decimal("500"),
                dollar_volume=Decimal("900"),
            ),
            FundamentalUniverseRow(
                instrument_id=InstrumentId("EQUITY.US.NASDAQ.NVDA"),
                market_cap=Decimal("500"),
                dollar_volume=Decimal("800"),
            ),
        ),
        top_n=2,
        metric="market_cap",
    )

    assert tuple(selector.select_universe()) == (
        InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        InstrumentId("EQUITY.US.NASDAQ.NVDA"),
    )


def test_top_n_volume_selector_uses_latest_total_volume_anchor() -> None:
    from qts.strategy_sdk.universe import TopNVolumeSelector

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)

    def bar(instrument_id: str, index: int, volume: str) -> Bar:
        close = Decimal("100")
        return Bar(
            instrument_id=InstrumentId(instrument_id),
            start_time=start + timedelta(minutes=index),
            end_time=start + timedelta(minutes=index + 1),
            timeframe="1m",
            session_id="2026-01-02",
            open=close,
            high=close,
            low=close,
            close=close,
            volume=Decimal(volume),
            is_complete=True,
        )

    selector = TopNVolumeSelector(
        bars=(
            bar("EQUITY.US.NASDAQ.MSFT", 0, "100"),
            bar("EQUITY.US.NASDAQ.AAPL", 0, "100"),
            bar("EQUITY.US.NASDAQ.NVDA", 0, "250"),
            bar("EQUITY.US.NASDAQ.AAPL", 1, "200"),
        ),
        top_n=2,
    )

    assert tuple(selector.select_universe()) == (
        InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        InstrumentId("EQUITY.US.NASDAQ.NVDA"),
    )


def test_strategy_context_sets_universe_from_selector() -> None:
    from qts.strategy_sdk.universe import FundamentalTopNSelector, FundamentalUniverseRow

    ctx = StrategyContext()
    selector = FundamentalTopNSelector(
        rows=(
            FundamentalUniverseRow(
                instrument_id=InstrumentId("EQUITY.US.NASDAQ.MSFT"),
                market_cap=Decimal("300"),
            ),
            FundamentalUniverseRow(
                instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
                market_cap=Decimal("500"),
            ),
        ),
        top_n=1,
        metric="market_cap",
    )

    universe = ctx.set_universe_from_selector(selector)

    assert universe.instrument_ids == (InstrumentId("EQUITY.US.NASDAQ.AAPL"),)
