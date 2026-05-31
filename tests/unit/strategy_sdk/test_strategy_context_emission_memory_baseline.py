"""Emission buffers are drainable and bounded (QTS-FINAL-005 memory baseline).

The pre-split context retained every emitted intent for the session lifetime, so
a live strategy emitting each bar leaked memory without bound. The drainable
``TargetIntentEmitter`` / ``TargetContext`` reset to empty on every drain, so the
retained buffer is bounded by a single event's emissions regardless of how many
events have been processed. These tests lock that drain-and-clear contract.
"""

from __future__ import annotations

from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.strategy_sdk import AssetRef
from qts.strategy_sdk.subcontexts import TargetContext
from qts.strategy_sdk.target_emitter import TargetIntentEmitter


def _asset() -> AssetRef:
    return AssetRef(InstrumentId("EQUITY.US.NASDAQ.AAPL"), "AAPL")


def test_emitter_drain_returns_then_clears() -> None:
    emitter = TargetIntentEmitter()
    from qts.strategy_sdk.target import TargetIntent, TargetIntentType

    intent = TargetIntent(
        asset=_asset(),
        intent_type=TargetIntentType.QUANTITY,
        value=Decimal("1"),
    )
    emitter.emit(intent)
    assert emitter.drain() == (intent,)
    # Drained: a second drain yields nothing -- the buffer was cleared, not sliced.
    assert emitter.drain() == ()
    assert emitter.intents == ()


def test_target_context_buffer_stays_bounded_across_many_cycles() -> None:
    target = TargetContext()
    asset = _asset()
    cycles = 500
    per_cycle = 3
    for _ in range(cycles):
        for _ in range(per_cycle):
            target.target_quantity(asset, Decimal("1"))
        drained = target.drain_intents()
        # Each cycle drains exactly what it emitted -- no carryover from prior cycles.
        assert len(drained) == per_cycle
        # The retained buffer is empty immediately after the drain.
        assert target.pending_intents == ()
    # After 500 cycles the buffer holds nothing: retention is O(1), not O(cycles).
    assert target.pending_intents == ()


def test_target_context_cancels_drain_independently() -> None:
    target = TargetContext()
    target.cancel_order("ORD-1")
    target.cancel_order("ORD-2")
    assert len(target.drain_cancels()) == 2
    assert target.pending_cancels == ()
    assert target.drain_cancels() == ()
