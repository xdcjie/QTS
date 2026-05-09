from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from qts.domain.instruments import Instrument


def _option(strike: str, right_name: str) -> Instrument:
    from qts.core.ids import InstrumentId
    from qts.domain.instruments import (
        AssetClass,
        ContractSpec,
        OptionRight,
        OptionSpec,
        SettlementType,
    )

    right = OptionRight.CALL if right_name == "call" else OptionRight.PUT
    return Instrument(
        instrument_id=InstrumentId(f"OPTION.US.AAPL.20260619.{right.value}.{strike}"),
        asset_class=AssetClass.OPTION,
        exchange="OPRA",
        currency="USD",
        contract_spec=ContractSpec(
            tick_size=Decimal("0.01"),
            lot_size=Decimal("1"),
            multiplier=Decimal("100"),
            settlement=SettlementType.CASH,
            calendar_id="XNYS",
        ),
        derivative=OptionSpec(
            expiry=date(2026, 6, 19),
            underlying=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
            strike=Decimal(strike),
            right=right,
        ),
    )


def test_option_chain_filters_by_underlying_expiry_strike_and_right() -> None:
    from qts.core.ids import InstrumentId
    from qts.domain.instruments import OptionRight
    from qts.registry.option_chain_registry import OptionChainRegistry

    registry = OptionChainRegistry()
    call_200 = _option("200", "call")
    put_200 = _option("200", "put")
    registry.register(call_200)
    registry.register(put_200)

    matches = registry.find(
        underlying=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        expiry=date(2026, 6, 19),
        strike=Decimal("200"),
        right=OptionRight.CALL,
    )

    assert matches == [call_200]


def test_option_chain_missing_underlying_is_explicit() -> None:
    from qts.core.ids import InstrumentId
    from qts.registry.option_chain_registry import OptionChainRegistry

    with pytest.raises(KeyError, match="missing option chain"):
        OptionChainRegistry().options_for(InstrumentId("EQUITY.US.NASDAQ.MSFT"))
