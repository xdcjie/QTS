from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from qts.domain.instruments import ContractSpec, SettlementType


def _contract_spec() -> ContractSpec:
    return ContractSpec(
        tick_size=Decimal("0.01"),
        lot_size=Decimal("1"),
        multiplier=Decimal("1"),
        settlement=SettlementType.CASH,
        calendar_id="XNYS",
    )


def test_option_instrument_requires_option_metadata() -> None:
    from qts.core.ids import InstrumentId
    from qts.domain.instruments import AssetClass, Instrument

    with pytest.raises(ValueError, match="option instruments require OptionSpec"):
        Instrument(
            instrument_id=InstrumentId("OPTION.US.AAPL.20260619.C.200"),
            asset_class=AssetClass.OPTION,
            exchange="OPRA",
            currency="USD",
            contract_spec=_contract_spec(),
        )


def test_future_instrument_requires_future_metadata_with_root_symbol() -> None:
    from qts.core.ids import InstrumentId
    from qts.domain.instruments import AssetClass, FutureSpec, Instrument

    with pytest.raises(ValueError, match="future instruments require FutureSpec"):
        Instrument(
            instrument_id=InstrumentId("FUTURE.COMEX.GC.202606"),
            asset_class=AssetClass.FUTURE,
            exchange="COMEX",
            currency="USD",
            contract_spec=_contract_spec(),
        )

    future = Instrument(
        instrument_id=InstrumentId("FUTURE.COMEX.GC.202606"),
        asset_class=AssetClass.FUTURE,
        exchange="COMEX",
        currency="USD",
        contract_spec=_contract_spec(),
        derivative=FutureSpec(
            expiry=date(2026, 6, 26),
            underlying=InstrumentId("FUTURE_ROOT.COMEX.GC"),
            root_symbol="GC",
        ),
    )

    assert isinstance(future.derivative, FutureSpec)
    assert future.derivative.root_symbol == "GC"


def test_equity_instrument_rejects_derivative_metadata() -> None:
    from qts.core.ids import InstrumentId
    from qts.domain.instruments import AssetClass, FutureSpec, Instrument

    with pytest.raises(ValueError, match="equity instruments must not have derivative metadata"):
        Instrument(
            instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
            asset_class=AssetClass.EQUITY,
            exchange="NASDAQ",
            currency="USD",
            contract_spec=_contract_spec(),
            derivative=FutureSpec(
                expiry=date(2026, 6, 26),
                underlying=InstrumentId("FUTURE_ROOT.COMEX.GC"),
                root_symbol="GC",
            ),
        )
