from __future__ import annotations

import ast
from datetime import date
from decimal import Decimal
from pathlib import Path

from qts.domain.instruments import ContractSpec, SettlementType


def _contract_spec() -> ContractSpec:
    return ContractSpec(
        tick_size=Decimal("0.01"),
        lot_size=Decimal("1"),
        multiplier=Decimal("1"),
        settlement=SettlementType.CASH,
        calendar_id="XNYS",
    )


def test_instrument_registry_resolves_symbols_and_metadata_for_supported_assets() -> None:
    from qts.core.ids import InstrumentId
    from qts.domain.instruments import AssetClass, FutureSpec, Instrument, OptionRight, OptionSpec
    from qts.registry.instrument_registry import InstrumentRegistry

    registry = InstrumentRegistry()
    equity = Instrument(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        asset_class=AssetClass.EQUITY,
        exchange="NASDAQ",
        currency="USD",
        contract_spec=_contract_spec(),
    )
    future = Instrument(
        instrument_id=InstrumentId("FUTURE.CME.ES.202606"),
        asset_class=AssetClass.FUTURE,
        exchange="CME",
        currency="USD",
        contract_spec=_contract_spec(),
        derivative=FutureSpec(
            expiry=date(2026, 6, 19),
            underlying=InstrumentId("FUTURE_ROOT.CME.ES"),
            root_symbol="ES",
        ),
    )
    option = Instrument(
        instrument_id=InstrumentId("OPTION.US.AAPL.20260619.C.200"),
        asset_class=AssetClass.OPTION,
        exchange="OPRA",
        currency="USD",
        contract_spec=_contract_spec(),
        derivative=OptionSpec(
            expiry=date(2026, 6, 19),
            underlying=equity.instrument_id,
            strike=Decimal("200"),
            right=OptionRight.CALL,
        ),
    )

    registry.register("AAPL", equity)
    registry.register("ESM6", future)
    registry.register("AAPL 20260619 C 200", option)

    assert registry.resolve("AAPL") == equity.instrument_id
    assert registry.get_instrument(future.instrument_id) == future
    assert registry.get_contract_spec(option.instrument_id) == option.contract_spec


def test_instrument_registry_keeps_symbol_normalization_inside_the_registry() -> None:
    tree = ast.parse(
        Path("backend/src/qts/registry/instrument_registry.py").read_text(encoding="utf-8")
    )

    private_functions = {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("_")
    }

    assert "_normalize_symbol" not in private_functions
