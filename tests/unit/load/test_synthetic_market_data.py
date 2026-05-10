from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.load.synthetic_market_data import SyntheticMarketDataConfig, generate_bars


def test_synthetic_market_data_generator_is_deterministic() -> None:
    config = SyntheticMarketDataConfig(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        start=datetime(2026, 5, 10, 9, 30, tzinfo=UTC),
        count=3,
        timeframe="1m",
        start_price=Decimal("100"),
        step=Decimal("0.25"),
        session_id="2026-05-10",
    )

    first = generate_bars(config)
    second = generate_bars(config)

    assert first == second
    assert [bar.close for bar in first] == [Decimal("100.25"), Decimal("100.50"), Decimal("100.75")]
