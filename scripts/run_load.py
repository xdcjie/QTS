#!/usr/bin/env python
"""Run a small deterministic synthetic market-data load scenario."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.load.synthetic_market_data import SyntheticMarketDataConfig, generate_bars


def main() -> None:
    bars = generate_bars(
        SyntheticMarketDataConfig(
            instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
            start=datetime(2026, 5, 10, 9, 30, tzinfo=UTC),
            count=100,
            timeframe="1m",
            start_price=Decimal("100"),
            step=Decimal("0.01"),
            session_id="load-test",
        )
    )
    print(f"generated_bars={len(bars)}")


if __name__ == "__main__":
    main()
