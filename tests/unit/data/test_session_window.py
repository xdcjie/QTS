from __future__ import annotations

from datetime import UTC, datetime, time

import pytest
from qts.data.sessions import RegularSessionWindow


def test_regular_session_window_maps_overnight_session_to_close_date() -> None:
    window = RegularSessionWindow(
        exchange_timezone="US/Eastern",
        open_time=time(18, 0),
        close_time=time(17, 0),
    )

    assert window.session_id_for_timestamp(datetime(2010, 6, 6, 22, 0, tzinfo=UTC)) == (
        "2010-06-07"
    )
    assert window.session_id_for_timestamp(datetime(2010, 6, 7, 20, 59, tzinfo=UTC)) == (
        "2010-06-07"
    )
    assert window.session_id_for_timestamp(datetime(2010, 6, 7, 21, 0, tzinfo=UTC)) is None


def test_regular_session_window_maps_same_day_session_to_local_date() -> None:
    window = RegularSessionWindow(
        exchange_timezone="US/Eastern",
        open_time=time(9, 30),
        close_time=time(16, 0),
    )

    assert window.session_id_for_timestamp(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)) == (
        "2026-01-02"
    )
    assert window.session_id_for_timestamp(datetime(2026, 1, 2, 20, 59, tzinfo=UTC)) == (
        "2026-01-02"
    )
    assert window.session_id_for_timestamp(datetime(2026, 1, 2, 21, 0, tzinfo=UTC)) is None


def test_regular_session_window_rejects_empty_and_zero_length_definitions() -> None:
    with pytest.raises(ValueError, match="exchange_timezone"):
        RegularSessionWindow(exchange_timezone="", open_time=time(9, 30), close_time=time(16, 0))

    with pytest.raises(ValueError, match="must differ"):
        RegularSessionWindow(
            exchange_timezone="US/Eastern",
            open_time=time(9, 30),
            close_time=time(9, 30),
        )
