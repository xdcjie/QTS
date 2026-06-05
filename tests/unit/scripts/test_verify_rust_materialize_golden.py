from __future__ import annotations

from scripts import verify_rust_materialize_golden


def test_phase1_golden_diff_covers_all_documented_timeframes() -> None:
    assert verify_rust_materialize_golden.CHECKED_TIMEFRAMES == (
        "1m",
        "2m",
        "3m",
        "5m",
        "10m",
        "15m",
        "30m",
        "1h",
        "4h",
        "1d",
    )
