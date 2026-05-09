from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest


def test_all_phase1_ids_are_immutable_non_empty_value_objects() -> None:
    from qts.core.ids import (
        AccountId,
        BrokerId,
        CausationId,
        CorrelationId,
        EventId,
        InstrumentId,
        OrderId,
        StrategyId,
    )

    id_types = (
        AccountId,
        InstrumentId,
        StrategyId,
        OrderId,
        BrokerId,
        EventId,
        CorrelationId,
        CausationId,
    )

    for id_type in id_types:
        value = id_type("id-001")

        assert value == id_type("id-001")
        assert hash(value) == hash(id_type("id-001"))
        assert str(value) == "id-001"
        with pytest.raises(FrozenInstanceError):
            value.value = "id-002"  # type: ignore[misc]
        with pytest.raises(ValueError, match=f"{id_type.__name__} must not be empty"):
            id_type("")


def test_ids_are_typed_even_when_values_match() -> None:
    from qts.core.ids import AccountId, InstrumentId

    instrument_id: object = InstrumentId("same")

    assert AccountId("same") != instrument_id
