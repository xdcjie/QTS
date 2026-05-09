from __future__ import annotations


def test_asset_ref_exposes_only_user_safe_identity() -> None:
    from qts.core.ids import InstrumentId
    from qts.strategy_sdk.asset_ref import AssetRef

    asset = AssetRef(instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"), symbol="AAPL")

    assert asset.instrument_id == InstrumentId("EQUITY.US.NASDAQ.AAPL")
    assert asset.symbol == "AAPL"
    assert not hasattr(asset, "contract_spec")
    assert not hasattr(asset, "broker_symbol")
