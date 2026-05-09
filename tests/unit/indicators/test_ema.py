from __future__ import annotations

from decimal import Decimal


def test_ema_warms_up_with_sma_then_updates_incrementally() -> None:
    from qts.indicators.price.ema import EMA

    ema = EMA(window=3)

    assert ema.update(Decimal("1")) is None
    assert ema.update(Decimal("2")) is None
    assert ema.update(Decimal("3")) == Decimal("2")
    assert ema.ready
    assert ema.update(Decimal("5")) == Decimal("3.5")
