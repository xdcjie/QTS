"""Anchor: compact_events=True drops noisy per-bar event kinds from events.ndjson.

Domain fact: the 2.25-year VWAP run produced a 2.4 GB events.ndjson
file because ``runtime.market_data`` and ``runtime.account_snapshot``
get emitted per bar (~1.6M events for 800k bars). Equity curve and
holdings snapshot already capture per-bar account state — so the
events.ndjson copies are redundant for backtest forensics.

Owner: ``qts.reporting.backtest.BacktestArtifactWriter`` carries a
``compact_events`` flag. When True, the two noisy per-bar event
kinds are silently dropped from events.ndjson. All other event
kinds (trading lifecycle, kill switch, signal, risk, fill,
position_closed, snapshot, etc.) ALWAYS reach the artifact.

Forbidden shortcut: dropping any non-noisy event kind; silently
dropping events in metrics / position-closed routing paths
(those run before the artifact filter); changing the public
``BacktestRuntimeEventSink.write`` return value when filtered.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from qts.core.ids import RuntimeRunId
from qts.reporting.backtest import BacktestArtifactWriter
from qts.runtime.sinks.backtest import BacktestRuntimeEventSink
from qts.runtime.sinks.base import RuntimeEvent, RuntimeEventContext

_NOISY_KINDS = frozenset({"runtime.market_data", "runtime.account_snapshot"})


def _drive_sink(writer: BacktestArtifactWriter) -> BacktestRuntimeEventSink:
    """Build a sink + push a mixed set of events through it."""
    sink = BacktestRuntimeEventSink(
        writer,
        context=RuntimeEventContext(
            run_id=RuntimeRunId("run-1"),
            mode="backtest",
            execution_environment="simulated",
        ),
    )
    base = datetime(2024, 1, 2, 14, 30, tzinfo=UTC)
    for index, kind in enumerate(
        [
            "runtime.market_data",
            "runtime.account_snapshot",
            "runtime.snapshot",
            "runtime.market_data",
            "runtime.account_snapshot",
            "runtime.kill_switch",
            "runtime.market_data",
            "runtime.account_snapshot",
        ]
    ):
        sink.write(
            RuntimeEvent(
                kind=kind,
                payload={"i": index, "t": (base + timedelta(minutes=index)).isoformat()},
            )
        )
    return sink


def _read_event_kinds(events_path: Path) -> list[str]:
    return [
        json.loads(line)["kind"]
        for line in events_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_compact_events_false_keeps_all_event_kinds(tmp_path: Path) -> None:
    """Default verbose mode persists every event written through the sink."""
    writer = BacktestArtifactWriter(tmp_path, compact_events=False)
    _drive_sink(writer)
    for artifact in writer._artifacts.values():
        artifact.close()

    events_path = next(tmp_path.glob(".events.partial.ndjson"))
    kinds = _read_event_kinds(events_path)
    # 8 events sent, all preserved.
    assert len(kinds) == 8
    assert kinds.count("runtime.market_data") == 3
    assert kinds.count("runtime.account_snapshot") == 3
    assert kinds.count("runtime.snapshot") == 1
    assert kinds.count("runtime.kill_switch") == 1


def test_compact_events_true_drops_noisy_per_bar_kinds(tmp_path: Path) -> None:
    """Compact mode silently filters runtime.market_data + runtime.account_snapshot."""
    writer = BacktestArtifactWriter(tmp_path, compact_events=True)
    _drive_sink(writer)
    for artifact in writer._artifacts.values():
        artifact.close()

    events_path = next(tmp_path.glob(".events.partial.ndjson"))
    kinds = _read_event_kinds(events_path)
    # Trading events preserved, noisy kinds dropped.
    assert "runtime.market_data" not in kinds
    assert "runtime.account_snapshot" not in kinds
    assert kinds == [
        "runtime.snapshot",
        "runtime.kill_switch",
    ]


def test_compact_events_default_is_false() -> None:
    """Default behavior must be verbose to avoid breaking forensic callers."""
    import inspect

    sig = inspect.signature(BacktestArtifactWriter.__init__)
    assert sig.parameters["compact_events"].default is False


def test_compact_events_filter_set_pins_known_noisy_kinds() -> None:
    """The filter set is part of the contract — pin it so additions are explicit."""
    assert BacktestArtifactWriter._COMPACT_EXCLUDED_KINDS == _NOISY_KINDS


def test_compact_events_does_not_disable_position_close_routing(tmp_path: Path) -> None:
    """``account.position_closed`` events route into statistics even in compact mode.

    The filter only suppresses persistence of *noisy* event kinds; it
    must NOT interfere with the sink's responsibility to translate
    position-close events into ``StatisticsBuilder.on_position_close``
    via ``BacktestArtifactWriter.write_position_closed``.
    """
    writer = BacktestArtifactWriter(tmp_path, compact_events=True)
    sink = BacktestRuntimeEventSink(
        writer,
        context=RuntimeEventContext(
            run_id=RuntimeRunId("run-1"),
            mode="backtest",
            execution_environment="simulated",
        ),
    )
    sink.write(
        RuntimeEvent(
            kind="account.position_closed",
            payload={
                "instrument_id": "FUTURE.CME.GC.GCG4",
                "realized_pnl": "10.0",
                "opened_at": "2024-01-02T14:30:00+00:00",
                "closed_at": "2024-01-02T14:35:00+00:00",
            },
        )
    )
    # The statistics builder must have received the position close — verify
    # via the builder's internal trade list (an indirect contract because the
    # builder doesn't expose a public iterator).
    assert writer._statistics._closed_pnls == [Decimal("10.0")]
