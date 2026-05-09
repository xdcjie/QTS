from __future__ import annotations

from decimal import Decimal


def test_momentum_factor_ranks_assets_deterministically() -> None:
    from qts.core.ids import InstrumentId
    from qts.factors.momentum import MomentumFactor
    from qts.strategy_sdk import AssetRef

    aapl = AssetRef(InstrumentId("EQUITY.US.NASDAQ.AAPL"), "AAPL")
    msft = AssetRef(InstrumentId("EQUITY.US.NASDAQ.MSFT"), "MSFT")
    goog = AssetRef(InstrumentId("EQUITY.US.NASDAQ.GOOG"), "GOOG")
    factor = MomentumFactor(window=3)

    result = factor.compute(
        {
            aapl: (Decimal("10"), Decimal("12"), Decimal("15")),
            msft: (Decimal("20"), Decimal("21"), Decimal("22")),
            goog: (Decimal("30"), Decimal("30"), Decimal("30")),
        }
    )

    assert [score.asset.symbol for score in result.ranked] == ["AAPL", "MSFT", "GOOG"]
    assert result.score(aapl) == Decimal("0.5")
    assert result.score(msft) == Decimal("0.1")
    assert result.score(goog) == Decimal("0")


def test_factor_factory_creates_momentum_factor() -> None:
    from qts.strategy_sdk.factors import FactorFactory

    factor = FactorFactory().momentum(window=3)

    assert factor.window == 3
