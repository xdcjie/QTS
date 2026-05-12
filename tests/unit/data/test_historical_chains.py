from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from qts.core.ids import InstrumentId
from qts.data.historical.chains import HistoricalChain


def test_historical_chain_load_parses_gc_contract_metadata() -> None:
    chain = HistoricalChain.load(Path("historical/chains/GC.json"))

    assert chain.root == "GC"
    assert chain.timezone == "US/Eastern"
    assert chain.tick_size == Decimal("0.1")
    assert chain.multiplier == Decimal("100.0")
    assert len(chain.contracts) == 224

    contract = chain.contract_for_symbol("GCM0")
    assert contract.symbol == "GCM0"
    assert contract.expiry == datetime(2010, 6, 28, 22, tzinfo=UTC)
    assert contract.first_notice_day == date(2010, 5, 31)
    assert contract.currency == "USD"
    assert contract.exchange == "CME"
    assert contract.tick_size == Decimal("0.1")
    assert contract.multiplier == Decimal("100.0")


def test_historical_chain_maps_outright_symbols_to_internal_instrument_ids() -> None:
    chain = HistoricalChain.load(Path("historical/chains/GC.json"))

    assert chain.is_outright_symbol("GCQ0") is True
    assert chain.instrument_id_for_symbol("GCQ0") == InstrumentId("FUTURE.CME.GC.GCQ0")


def test_historical_chain_rejects_spread_symbols() -> None:
    chain = HistoricalChain.load(Path("historical/chains/GC.json"))

    assert chain.is_outright_symbol("GCN0-GCQ0") is False
    with pytest.raises(ValueError, match="not an outright"):
        chain.instrument_id_for_symbol("GCN0-GCQ0")


def test_historical_chain_missing_required_fields_raise_value_error(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text(
        (
            '{"root": "GC", "market": "CME_FUT", "currency": "USD", '
            '"timezone_id": "US/Eastern", "tick_size": "0.1", '
            '"trading_calendar": "CMES", "contracts": []}'
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="multiplier"):
        HistoricalChain.load(bad)
