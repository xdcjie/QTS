from __future__ import annotations

import pytest


def test_continuous_future_is_research_reference_not_orderable_instrument() -> None:
    from qts.registry.future_chain_registry import ContinuousFutureRef, FutureChainRegistry

    with pytest.raises(ValueError, match="not directly tradable"):
        FutureChainRegistry().require_tradable(ContinuousFutureRef(root_symbol="GC", offset=0))
