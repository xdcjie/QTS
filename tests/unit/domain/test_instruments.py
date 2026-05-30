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


def test_contract_spec_initial_margin_rate_defaults_to_none() -> None:
    assert _contract_spec().initial_margin_rate is None


def test_contract_spec_accepts_configured_initial_margin_rate() -> None:
    spec = ContractSpec(
        tick_size=Decimal("0.1"),
        lot_size=Decimal("1"),
        multiplier=Decimal("100"),
        settlement=SettlementType.PHYSICAL,
        calendar_id="CMES",
        initial_margin_rate=Decimal("0.05"),
    )
    assert spec.initial_margin_rate == Decimal("0.05")


@pytest.mark.parametrize("bad_rate", [Decimal("0"), Decimal("-0.01")])
def test_contract_spec_rejects_non_positive_margin_rate(bad_rate: Decimal) -> None:
    with pytest.raises(ValueError, match="initial_margin_rate must be positive"):
        ContractSpec(
            tick_size=Decimal("0.1"),
            lot_size=Decimal("1"),
            multiplier=Decimal("100"),
            settlement=SettlementType.PHYSICAL,
            calendar_id="CMES",
            initial_margin_rate=bad_rate,
        )


def test_contract_spec_rejects_margin_rate_above_one() -> None:
    with pytest.raises(ValueError, match="initial_margin_rate must not exceed 1"):
        ContractSpec(
            tick_size=Decimal("0.1"),
            lot_size=Decimal("1"),
            multiplier=Decimal("100"),
            settlement=SettlementType.PHYSICAL,
            calendar_id="CMES",
            initial_margin_rate=Decimal("1.5"),
        )


def test_contract_spec_margin_rate_drives_calculator_projection() -> None:
    """The per-contract rate is the product fact a MarginCalculator consumes.

    A 10-lot at price 100 with multiplier 100 has notional 100,000; at the
    contract's 0.05 rate the projected initial margin is 5,000.
    """
    from qts.risk.margin.calculator import MarginCalculator

    spec = _contract_spec_with_margin(Decimal("0.05"))
    assert spec.initial_margin_rate is not None
    calculator = MarginCalculator(
        initial_margin_rate=spec.initial_margin_rate,
        maintenance_margin_rate=spec.initial_margin_rate,
    )
    notional = Decimal("10") * Decimal("100") * Decimal("100")
    assert calculator.order_initial_margin(notional) == Decimal("5000")


def _contract_spec_with_margin(rate: Decimal) -> ContractSpec:
    return ContractSpec(
        tick_size=Decimal("0.1"),
        lot_size=Decimal("1"),
        multiplier=Decimal("100"),
        settlement=SettlementType.PHYSICAL,
        calendar_id="CMES",
        initial_margin_rate=rate,
    )


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
