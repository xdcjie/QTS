from __future__ import annotations

import pytest


def test_future_chain_resolves_tradable_contract_to_concrete_instrument_id() -> None:
    from qts.core.ids import InstrumentId
    from qts.registry.future_chain_registry import FutureChain, FutureChainRegistry

    registry = FutureChainRegistry()
    front = InstrumentId("FUTURE.COMEX.GC.202606")
    second = InstrumentId("FUTURE.COMEX.GC.202608")
    registry.register(FutureChain(root_symbol="GC", contracts=(front, second)))

    assert registry.resolve_contract("GC", offset=0) == front
    assert registry.resolve_contract("GC", offset=1) == second


def test_continuous_future_reference_is_rejected_for_direct_trading() -> None:
    from qts.registry.future_chain_registry import ContinuousFutureRef, FutureChainRegistry

    registry = FutureChainRegistry()

    with pytest.raises(ValueError, match="continuous future references are not directly tradable"):
        registry.require_tradable(ContinuousFutureRef(root_symbol="GC", offset=0))
