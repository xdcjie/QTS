from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from qts.core.ids import InstrumentId
from qts.strategy_sdk.asset_ref import AssetRef
from qts.strategy_sdk.signals import Signal, SignalDirection


def _asset(symbol: str) -> AssetRef:
    return AssetRef(
        instrument_id=InstrumentId(f"EQUITY.US.NASDAQ.{symbol}"),
        symbol=symbol,
    )


def test_signal_requires_direction_and_source_model() -> None:
    asset = _asset("AAPL")

    with pytest.raises(ValueError, match="direction"):
        Signal(
            asset=asset,
            direction="sideways",  # type: ignore[arg-type]
            generated_at=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
            horizon=timedelta(days=1),
            source_model="momentum-v1",
        )

    with pytest.raises(ValueError, match="source_model is required"):
        Signal(
            asset=asset,
            direction=SignalDirection.UP,
            generated_at=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
            horizon=timedelta(days=1),
            source_model="",
        )


def test_signal_confidence_is_normalized_decimal() -> None:
    signal = Signal(
        asset=_asset("AAPL"),
        direction=SignalDirection.UP,
        generated_at=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
        horizon=timedelta(days=1),
        source_model="momentum-v1",
        confidence="0.75",  # type: ignore[arg-type]
    )

    assert signal.confidence == Decimal("0.75")


def test_signal_requires_aware_generated_at_and_positive_horizon() -> None:
    asset = _asset("AAPL")

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        Signal(
            asset=asset,
            direction=SignalDirection.UP,
            generated_at=datetime(2026, 1, 2, 14, 30),
            horizon=timedelta(days=1),
            source_model="momentum-v1",
        )

    with pytest.raises(ValueError, match="horizon must be positive"):
        Signal(
            asset=asset,
            direction=SignalDirection.UP,
            generated_at=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
            horizon=timedelta(0),
            source_model="momentum-v1",
        )


def test_signal_rejects_confidence_outside_unit_interval() -> None:
    with pytest.raises(ValueError, match=r"confidence must be in \[0, 1\]"):
        Signal(
            asset=_asset("AAPL"),
            direction=SignalDirection.UP,
            generated_at=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
            horizon=timedelta(days=1),
            source_model="momentum-v1",
            confidence=Decimal("1.01"),
        )
