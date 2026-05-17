"""Unit tests for Strategy SDK universe selection."""

from __future__ import annotations

from qts.core.ids import InstrumentId
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
