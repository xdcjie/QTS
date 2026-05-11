from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.registry.future_roll import (
    FutureContractCandidate,
    FutureRollRegistry,
    FutureRollSelection,
    HighestVolumeFutureContractSelector,
)


def test_highest_volume_selector_picks_one_contract_per_root_timestamp() -> None:
    as_of = datetime(2010, 6, 6, 22, 1, tzinfo=UTC)
    low_volume = FutureContractCandidate(
        root_symbol="GC",
        symbol="GCN0",
        instrument_id=InstrumentId("FUTURE.CME.GC.GCN0"),
        as_of=as_of,
        close=Decimal("1220.2"),
        volume=Decimal("4"),
    )
    high_volume = FutureContractCandidate(
        root_symbol="GC",
        symbol="GCQ0",
        instrument_id=InstrumentId("FUTURE.CME.GC.GCQ0"),
        as_of=as_of,
        close=Decimal("1221.6"),
        volume=Decimal("74"),
    )

    selected = HighestVolumeFutureContractSelector().select((low_volume, high_volume))

    assert selected == high_volume


def test_future_roll_registry_resolves_continuous_id_to_selected_contract() -> None:
    first = InstrumentId("FUTURE.CME.GC.GCN0")
    second = InstrumentId("FUTURE.CME.GC.GCQ0")
    t0 = datetime(2010, 6, 6, 22, 1, tzinfo=UTC)
    t1 = datetime(2010, 6, 6, 22, 2, tzinfo=UTC)
    registry = FutureRollRegistry()
    continuous_id = registry.register_root(
        root_symbol="GC",
        exchange="CME",
        contracts=(first, second),
    )

    registry.record_selection(
        FutureRollSelection(
            continuous_instrument_id=continuous_id,
            root_symbol="GC",
            as_of=t0,
            concrete_instrument_id=first,
            source_symbol="GCN0",
            prices_by_instrument={first: Decimal("1220.2"), second: Decimal("1221.6")},
        )
    )
    registry.record_selection(
        FutureRollSelection(
            continuous_instrument_id=continuous_id,
            root_symbol="GC",
            as_of=t1,
            concrete_instrument_id=second,
            source_symbol="GCQ0",
            prices_by_instrument={first: Decimal("1220.3"), second: Decimal("1221.7")},
        )
    )

    assert continuous_id == InstrumentId("CONTINUOUS_FUTURE.CME.GC")
    assert registry.is_continuous(continuous_id) is True
    assert registry.resolve_contract("GC", as_of=t0) == first
    assert registry.resolve_contract(continuous_id, as_of=t1) == second
    assert registry.related_contracts(continuous_id) == (first, second)
    assert registry.execution_price(continuous_id, first, as_of=t1) == Decimal("1220.3")
