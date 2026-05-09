from __future__ import annotations

import pytest


def test_broker_symbol_mapping_round_trips_at_boundary() -> None:
    from qts.core.ids import BrokerId, InstrumentId
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

    mapping = BrokerSymbolMapping(BrokerId("ibkr"))
    instrument_id = InstrumentId("FUTURE.COMEX.GC.202606")

    mapping.register(instrument_id, "GCM6")

    assert mapping.to_broker_symbol(instrument_id) == "GCM6"
    assert mapping.to_instrument_id("GCM6") == instrument_id


def test_broker_symbol_mapping_errors_are_explicit() -> None:
    from qts.core.ids import BrokerId, InstrumentId
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

    mapping = BrokerSymbolMapping(BrokerId("ibkr"))

    with pytest.raises(KeyError, match="missing broker symbol"):
        mapping.to_broker_symbol(InstrumentId("FUTURE.COMEX.GC.202606"))
    with pytest.raises(KeyError, match="missing instrument mapping"):
        mapping.to_instrument_id("GCM6")
