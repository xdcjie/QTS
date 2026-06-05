from __future__ import annotations

import subprocess
from collections.abc import Sequence
from pathlib import Path

import pytest

from scripts import verify_rust_core_migration


def test_rust_core_gate_runs_workspace_unit_tests(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_run(command: Sequence[object], *, cwd: Path, check: bool) -> None:
        assert cwd == tmp_path / "rust"
        assert check is True
        calls.append(tuple(str(part) for part in command))

    monkeypatch.setattr(subprocess, "run", fake_run)

    verify_rust_core_migration._run_rust_unit_tests(
        repo_root=tmp_path,
        cargo="cargo",
    )

    assert calls == [
        (
            "cargo",
            "test",
            "-q",
            "--workspace",
        )
    ]


def test_phase3_expected_backtest_includes_events_and_equity_curve() -> None:
    expected_replay: dict[str, object] = {
        "events": [
            {
                "sequence": 0,
                "visible_at": "2026-01-06T14:35:00.000000000Z",
                "bar": {
                    "instrument_id": "FUTURE.CME.GC.GCM26",
                    "start_time": "2026-01-06T14:30:00.000000000Z",
                    "open": "2000",
                    "close": "2001",
                },
            },
            {
                "sequence": 1,
                "visible_at": "2026-01-06T14:40:00.000000000Z",
                "bar": {
                    "instrument_id": "FUTURE.CME.GC.GCM26",
                    "start_time": "2026-01-06T14:35:00.000000000Z",
                    "open": "2002",
                    "close": "2003",
                },
            },
        ]
    }

    payload = verify_rust_core_migration._expected_backtest(
        expected_replay,
        "qts-replay-v1-test",
    )
    events = verify_rust_core_migration._object_list_field(payload, "events", "payload")
    equity_curve = verify_rust_core_migration._object_list_field(
        payload,
        "equity_curve",
        "payload",
    )

    assert [event["kind"] for event in events] == [
        "risk.accepted",
        "order.accepted",
        "execution.filled",
        "account.updated",
    ]
    assert equity_curve == [
        {
            "timestamp": "2026-01-06T14:35:00.000000000Z",
            "cash": "100000",
            "position_quantity": "0",
            "positions": {},
            "equity": "100000",
        },
        {
            "timestamp": "2026-01-06T14:40:00.000000000Z",
            "cash": "97998",
            "position_quantity": "1",
            "positions": {"FUTURE.CME.GC.GCM26": "1"},
            "equity": "100001",
        },
    ]


def test_phase3_expected_equity_ignores_non_position_instrument_bars() -> None:
    expected_replay: dict[str, object] = {
        "events": [
            {
                "sequence": 0,
                "visible_at": "2026-01-06T14:35:00.000000000Z",
                "bar": {
                    "instrument_id": "FUTURE.CME.GC.GCM26",
                    "start_time": "2026-01-06T14:30:00.000000000Z",
                    "open": "2000",
                    "close": "2001",
                },
            },
            {
                "sequence": 1,
                "visible_at": "2026-01-06T14:35:00.000000000Z",
                "bar": {
                    "instrument_id": "FUTURE.CME.SI.SIN26",
                    "start_time": "2026-01-06T14:30:00.000000000Z",
                    "open": "25",
                    "close": "25.1",
                },
            },
            {
                "sequence": 2,
                "visible_at": "2026-01-06T14:40:00.000000000Z",
                "bar": {
                    "instrument_id": "FUTURE.CME.GC.GCM26",
                    "start_time": "2026-01-06T14:35:00.000000000Z",
                    "open": "2002",
                    "close": "2003",
                },
            },
            {
                "sequence": 3,
                "visible_at": "2026-01-06T14:40:00.000000000Z",
                "bar": {
                    "instrument_id": "FUTURE.CME.SI.SIN26",
                    "start_time": "2026-01-06T14:35:00.000000000Z",
                    "open": "25.2",
                    "close": "25.3",
                },
            },
        ]
    }

    payload = verify_rust_core_migration._expected_backtest(
        expected_replay,
        "qts-replay-v1-test",
    )
    equity_curve = verify_rust_core_migration._object_list_field(
        payload,
        "equity_curve",
        "payload",
    )

    assert [point["equity"] for point in equity_curve] == [
        "100000",
        "100000",
        "100001",
        "100001",
    ]


def test_phase2_expected_replay_provenance_includes_cache_identity(tmp_path: Path) -> None:
    payload = verify_rust_core_migration._expected_replay(
        verify_rust_core_migration._fixture_rows(),
        "fixture-dataset-hash",
        tmp_path / "source.csv",
        cache_identity="qts-replay-v1-fixture",
    )
    events = verify_rust_core_migration._object_list_field(payload, "events", "payload")

    assert {
        verify_rust_core_migration._string_field(
            verify_rust_core_migration._object_field(event, "provenance", "event"),
            "cache_identity",
            "provenance",
        )
        for event in events
    } == {"qts-replay-v1-fixture"}
