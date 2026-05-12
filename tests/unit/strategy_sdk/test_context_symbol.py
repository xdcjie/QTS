from __future__ import annotations

from datetime import date
from decimal import Decimal


def test_context_resolves_user_symbols_to_asset_refs() -> None:
    from qts.core.ids import InstrumentId
    from qts.domain.instruments import AssetClass, ContractSpec, Instrument, SettlementType
    from qts.registry.instrument_registry import InstrumentRegistry
    from qts.strategy_sdk import AssetRef, StrategyContext

    registry = InstrumentRegistry()
    registry.register(
        "AAPL",
        Instrument(
            instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
            asset_class=AssetClass.EQUITY,
            exchange="NASDAQ",
            currency="USD",
            contract_spec=ContractSpec(
                tick_size=Decimal("0.01"),
                lot_size=Decimal("1"),
                multiplier=Decimal("1"),
                settlement=SettlementType.CASH,
                calendar_id="XNYS",
            ),
        ),
    )
    ctx = StrategyContext(instrument_registry=registry)

    asset = ctx.symbol("AAPL")

    assert isinstance(asset, AssetRef)
    assert asset.instrument_id == InstrumentId("EQUITY.US.NASDAQ.AAPL")
    assert asset.symbol == "AAPL"


def test_context_resolves_future_contracts_through_future_chain() -> None:
    from qts.core.ids import InstrumentId
    from qts.registry.future_chain_registry import FutureChain, FutureChainRegistry
    from qts.registry.instrument_registry import InstrumentRegistry
    from qts.strategy_sdk import StrategyContext

    chain_registry = FutureChainRegistry()
    chain_registry.register(
        FutureChain(root_symbol="ES", contracts=(InstrumentId("FUTURE.CME.ES.202606"),))
    )
    ctx = StrategyContext(
        instrument_registry=InstrumentRegistry(),
        future_chain_registry=chain_registry,
    )

    asset = ctx.future("ES", contract="front")

    assert asset.instrument_id == InstrumentId("FUTURE.CME.ES.202606")
    assert asset.symbol == "ES"
    assert asset.metadata["contract"] == "front"


def test_context_resolves_option_selection_when_registry_is_available() -> None:
    from qts.core.ids import InstrumentId
    from qts.domain.instruments import (
        AssetClass,
        ContractSpec,
        Instrument,
        OptionRight,
        OptionSpec,
        SettlementType,
    )
    from qts.registry.instrument_registry import InstrumentRegistry
    from qts.registry.option_chain_registry import OptionChainRegistry
    from qts.strategy_sdk import StrategyContext

    option = Instrument(
        instrument_id=InstrumentId("OPTION.US.AAPL.20260619.C.200"),
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
            strike=Decimal("200"),
            right=OptionRight.CALL,
        ),
    )
    option_registry = OptionChainRegistry()
    option_registry.register(option)
    instrument_registry = InstrumentRegistry()
    instrument_registry.register(
        "AAPL",
        Instrument(
            instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
            asset_class=AssetClass.EQUITY,
            exchange="NASDAQ",
            currency="USD",
            contract_spec=ContractSpec(
                tick_size=Decimal("0.01"),
                lot_size=Decimal("1"),
                multiplier=Decimal("1"),
                settlement=SettlementType.CASH,
                calendar_id="XNYS",
            ),
        ),
    )
    ctx = StrategyContext(
        instrument_registry=instrument_registry,
        option_chain_registry=option_registry,
    )

    asset = ctx.option(
        underlying="AAPL",
        expiry=date(2026, 6, 19),
        strike=Decimal("200"),
        right=OptionRight.CALL,
    )

    assert asset.instrument_id == option.instrument_id


def test_context_records_data_subscriptions() -> None:
    import pytest
    from qts.core.ids import InstrumentId
    from qts.strategy_sdk import AssetRef, StrategyContext

    ctx = StrategyContext()
    asset = AssetRef(InstrumentId("FUTURE.CME.GC.GCQ0"), "GCQ0")

    subscription = ctx.subscribe(asset, timeframe="1m", warmup=60)

    assert subscription.asset == asset
    assert subscription.timeframe == "1m"
    assert subscription.warmup == 60
    assert ctx.subscriptions == (subscription,)
    with pytest.raises(ValueError, match="warmup"):
        ctx.subscribe(asset, timeframe="1m", warmup=0)
    with pytest.raises(ValueError, match="timeframe"):
        ctx.subscribe(asset, timeframe=" ", warmup=1)
