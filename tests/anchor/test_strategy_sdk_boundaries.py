from __future__ import annotations


def test_strategy_sdk_target_api_does_not_expose_risk_order_or_broker_internals() -> None:
    from qts.core.ids import InstrumentId
    from qts.strategy_sdk import AssetRef, StrategyContext

    ctx = StrategyContext()
    asset = AssetRef(InstrumentId("EQUITY.US.NASDAQ.AAPL"), "AAPL")
    intent = ctx.close(asset)

    assert not hasattr(ctx, "broker")
    assert not hasattr(ctx, "order_manager")
    assert not hasattr(ctx, "risk_engine")
    assert not hasattr(intent, "broker_symbol")
    assert not hasattr(intent, "contract_spec")
