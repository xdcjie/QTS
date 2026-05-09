from __future__ import annotations

from decimal import Decimal


def test_target_apis_emit_intents_without_mutating_portfolio() -> None:
    from qts.core.ids import InstrumentId
    from qts.strategy_sdk import AssetRef, StrategyContext
    from qts.strategy_sdk.target import TargetIntent, TargetIntentType

    ctx = StrategyContext()
    asset = AssetRef(InstrumentId("EQUITY.US.NASDAQ.AAPL"), "AAPL")

    intents = [
        ctx.target_percent(asset, Decimal("0.5")),
        ctx.target_quantity(asset, Decimal("100")),
        ctx.target_value(asset, Decimal("50000")),
        ctx.close(asset),
    ]

    assert all(isinstance(intent, TargetIntent) for intent in intents)
    assert [intent.intent_type for intent in intents] == [
        TargetIntentType.PERCENT,
        TargetIntentType.QUANTITY,
        TargetIntentType.VALUE,
        TargetIntentType.CLOSE,
    ]
    assert ctx.intents == tuple(intents)


def test_rebalance_emits_one_percent_intent_per_asset() -> None:
    from qts.core.ids import InstrumentId
    from qts.strategy_sdk import AssetRef, StrategyContext
    from qts.strategy_sdk.target import TargetIntentType

    ctx = StrategyContext()
    aapl = AssetRef(InstrumentId("EQUITY.US.NASDAQ.AAPL"), "AAPL")
    msft = AssetRef(InstrumentId("EQUITY.US.NASDAQ.MSFT"), "MSFT")

    intents = ctx.rebalance({aapl: Decimal("0.6"), msft: Decimal("0.4")})

    assert len(intents) == 2
    assert {intent.intent_type for intent in intents} == {TargetIntentType.PERCENT}
    assert ctx.intents == tuple(intents)
