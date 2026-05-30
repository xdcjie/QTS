"""Gate tests for continuous-futures offset resolution and missing-price handling (DR-027)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from qts.core.ids import InstrumentId
from qts.registry.future_roll import (
    FutureRollRegistry,
    FutureRollSelection,
    MissingExecutionPriceError,
)

_FIRST = InstrumentId("FUTURE.CME.GC.GCM0")
_SECOND = InstrumentId("FUTURE.CME.GC.GCN0")
_THIRD = InstrumentId("FUTURE.CME.GC.GCQ0")
_AS_OF = datetime(2010, 5, 1, tzinfo=UTC)


def _registry() -> tuple[FutureRollRegistry, InstrumentId]:
    registry = FutureRollRegistry()
    continuous_id = registry.register_root(
        root_symbol="GC", exchange="CME", contracts=(_FIRST, _SECOND, _THIRD)
    )
    registry.record_selection(
        FutureRollSelection(
            continuous_instrument_id=continuous_id,
            root_symbol="GC",
            as_of=_AS_OF,
            concrete_instrument_id=_FIRST,
            source_symbol="GCM0",
            prices_by_instrument={
                _FIRST: Decimal("1200"),
                _SECOND: Decimal("1205"),
                _THIRD: Decimal("1210"),
            },
        )
    )
    return registry, continuous_id


def test_offset_resolves_successive_deferred_contracts() -> None:
    registry, _ = _registry()
    assert registry.resolve_contract("GC", as_of=_AS_OF, offset=0) == _FIRST
    assert registry.resolve_contract("GC", as_of=_AS_OF, offset=1) == _SECOND
    assert registry.resolve_contract("GC", as_of=_AS_OF, offset=2) == _THIRD


def test_offset_beyond_available_contracts_raises() -> None:
    registry, _ = _registry()
    with pytest.raises(ValueError, match="exceeds available contracts"):
        registry.resolve_contract("GC", as_of=_AS_OF, offset=3)


def test_deferred_continuous_reference_resolves_next_active_contract() -> None:
    registry, continuous_id = _registry()
    deferred = registry.continuous_instrument_id("GC", offset=1)
    assert deferred != continuous_id
    assert registry.is_continuous(deferred)
    # The deferred reference carries its own implicit offset of 1.
    assert registry.resolve_contract(deferred, as_of=_AS_OF) == _SECOND


def test_missing_execution_price_raises_structured_error_not_bare_keyerror() -> None:
    registry, continuous_id = _registry()
    unknown = InstrumentId("FUTURE.CME.GC.GCZ9")
    with pytest.raises(MissingExecutionPriceError):
        registry.execution_price(continuous_id, unknown, as_of=_AS_OF)
