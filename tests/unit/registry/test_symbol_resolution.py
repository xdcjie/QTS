from __future__ import annotations

import pytest
from qts.core.ids import InstrumentId
from qts.registry.symbol_resolution import StaticSymbolResolver


def test_static_symbol_resolver_maps_source_symbols_to_instrument_ids() -> None:
    resolver = StaticSymbolResolver({"aapl": InstrumentId("EQUITY.US.NASDAQ.AAPL")})

    assert resolver.is_supported_symbol("AAPL") is True
    assert resolver.instrument_id_for_symbol("AAPL") == InstrumentId("EQUITY.US.NASDAQ.AAPL")


def test_static_symbol_resolver_rejects_unknown_symbols() -> None:
    resolver = StaticSymbolResolver({"AAPL": InstrumentId("EQUITY.US.NASDAQ.AAPL")})

    assert resolver.is_supported_symbol("MSFT") is False
    with pytest.raises(ValueError, match="unsupported source symbol"):
        resolver.instrument_id_for_symbol("MSFT")


def test_static_symbol_resolver_rejects_ambiguous_normalized_symbols() -> None:
    with pytest.raises(ValueError, match="duplicate source symbol"):
        StaticSymbolResolver(
            {
                "aapl": InstrumentId("EQUITY.US.NASDAQ.AAPL"),
                "AAPL": InstrumentId("EQUITY.US.NYSE.AAPL"),
            }
        )
