from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(slots=True)
class _FixedClock:
    instant: datetime

    def now(self) -> datetime:
        return self.instant


def test_snapshot_event_stamps_event_time_with_injected_clock() -> None:
    from qts.api.websocket import events

    fixed = datetime(2026, 5, 30, 12, 0, tzinfo=UTC)
    events.set_stream_clock(_FixedClock(fixed))
    try:
        event = events._snapshot_event()
    finally:
        events.set_stream_clock(None)

    assert event["event_time_utc"] == fixed.isoformat()


def test_default_stream_clock_uses_wall_clock_utc() -> None:
    from qts.api.websocket import events

    before = datetime.now(tz=UTC)
    event = events._snapshot_event()
    after = datetime.now(tz=UTC)

    stamped = datetime.fromisoformat(event["event_time_utc"])
    assert before <= stamped <= after


def test_broadcast_stream_event_envelope_uses_injected_clock() -> None:
    import asyncio

    from qts.api.websocket import events

    fixed = datetime(2026, 5, 30, 13, 30, tzinfo=UTC)
    events.set_stream_clock(_FixedClock(fixed))
    try:
        event = asyncio.run(events.broadcast_stream_event("snapshot", {"samples": []}))
    finally:
        events.set_stream_clock(None)

    assert event["event_time_utc"] == fixed.isoformat()
