"""Unit tests for strategy target intent emitter."""

from __future__ import annotations

from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.strategy_sdk.asset_ref import AssetRef
from qts.strategy_sdk.target import TargetIntent, TargetIntentType
from qts.strategy_sdk.target_emitter import TargetIntentEmitter


def test_target_emitter_records_and_returns_intents() -> None:
    asset = AssetRef(InstrumentId("EQUITY.US.NASDAQ.AAPL"), "AAPL")
    emitter = TargetIntentEmitter()

    intent = emitter.emit(TargetIntent(asset=asset, intent_type=TargetIntentType.CLOSE, value=None))
    another = emitter.emit(
        TargetIntent(asset=asset, intent_type=TargetIntentType.QUANTITY, value=Decimal("3"))
    )

    assert emitter.intents == (intent, another)
