from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest


def test_continuous_future_is_research_reference_not_orderable_instrument() -> None:
    from qts.registry.future_chain_registry import ContinuousFutureRef, FutureChainRegistry

    with pytest.raises(ValueError, match="not directly tradable"):
        FutureChainRegistry().require_tradable(ContinuousFutureRef(root_symbol="GC", offset=0))


def test_continuous_future_roll_resolves_to_concrete_contract_at_time() -> None:
    from qts.core.ids import InstrumentId
    from qts.registry.future_roll import FutureRollRegistry, FutureRollSelection

    first = InstrumentId("FUTURE.CME.GC.GCN0")
    second = InstrumentId("FUTURE.CME.GC.GCQ0")
    as_of = datetime(2010, 6, 6, 22, 1, tzinfo=UTC)
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
            as_of=as_of,
            concrete_instrument_id=second,
            source_symbol="GCQ0",
            prices_by_instrument={first: Decimal("1220.2"), second: Decimal("1221.6")},
        )
    )

    assert registry.resolve_contract("GC", as_of=as_of) == second
