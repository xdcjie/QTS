#!/usr/bin/env python3
"""Release gate for the Rust core migration parity path."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Protocol, TypedDict, cast

from qts.core.ids import InstrumentId
from qts.data.historical.csv_format import EXPECTED_HISTORICAL_COLUMNS
from qts.registry.future_roll import (
    FirstNoticeDateFutureContractSelector,
    FutureContractCandidate,
    FutureContractRollSpec,
    FutureRollRegistry,
    FutureRollSelection,
)
from qts.reporting.backtest_analyst import BacktestRunReportLoader


class RunResearchModule(Protocol):
    def engine_parity_evidence_criterion(self, path: Path) -> dict[str, object]: ...


class FixtureRow(TypedDict):
    ts_event: datetime
    rtype: str
    publisher_id: str
    instrument_id: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    symbol: str


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
run_research = cast(
    RunResearchModule,
    importlib.import_module("scripts.run_research"),
)

ROOTS = ("GC", "SI")
GC_INSTRUMENT_ID = "FUTURE.CME.GC.GCM26"
GC_SYMBOL = "GCM26"
SI_INSTRUMENT_ID = "FUTURE.CME.SI.SIN26"
SI_SYMBOL = "SIN26"
TIMEFRAME = "5m"
ROLL_POLICY = "front"
ROLL_SESSION_DATE = date(2026, 6, 17)
ROLL_AS_OF = datetime(2026, 6, 17, 14, 30, tzinfo=UTC)
ROLL_CONTRACTS = (
    (
        "GCM26",
        "FUTURE.CME.GC.GCM26",
        date(2026, 6, 22),
        datetime(2026, 6, 26, 21, 0, tzinfo=UTC),
        Decimal("2001"),
        Decimal("100"),
    ),
    (
        "GCQ26",
        "FUTURE.CME.GC.GCQ26",
        date(2026, 8, 21),
        datetime(2026, 8, 26, 21, 0, tzinfo=UTC),
        Decimal("2012"),
        Decimal("90"),
    ),
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path for clean engine-parity evidence JSON",
    )
    parser.add_argument(
        "--diff-artifact-dir",
        type=Path,
        default=None,
        help="Optional directory for Python/Rust parity diff artifacts",
    )
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    cargo = shutil.which("cargo")
    if cargo is None:
        print("cargo not found", file=sys.stderr)
        return 1

    subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "verify_rust_materialize_golden.py"),
        ],
        cwd=repo_root,
        check=True,
    )
    _run_rust_unit_tests(repo_root=repo_root, cargo=cargo)

    diff_artifact_dir = args.diff_artifact_dir
    if diff_artifact_dir is None and args.output is not None:
        diff_artifact_dir = args.output.parent / f"{args.output.stem}.diffs"

    diff_artifacts: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="qts-rs-core-gate-") as tmp:
        work = Path(tmp)
        source_csv = work / "source.csv"
        replay_json = work / "replay.json"
        replay_json_2 = work / "replay-2.json"
        roll_json = work / "roll-selection.json"
        backtest_json = work / "backtest.json"
        rust_artifact_dir = work / "rust-backtest-artifacts"
        rows = _fixture_rows()
        _write_source_csv(source_csv, rows)
        dataset_hash = hashlib.sha256(source_csv.read_bytes()).hexdigest()

        replay_command = [
            cargo,
            "run",
            "-q",
            "-p",
            "qts-cli",
            "--",
            "replay",
            *_identity_args(),
            "--source-csv",
            str(source_csv),
            "--timeframe",
            TIMEFRAME,
            "--dataset-hash",
            dataset_hash,
            "--roll-policy",
            ROLL_POLICY,
            "--start",
            _timestamp_text(rows[0]["ts_event"]),
            "--end",
            _timestamp_text(rows[-1]["ts_event"] + timedelta(minutes=5)),
            "--output-json",
        ]
        subprocess.run([*replay_command, str(replay_json)], cwd=repo_root / "rust", check=True)
        subprocess.run([*replay_command, str(replay_json_2)], cwd=repo_root / "rust", check=True)

        rust_replay = _read_json(replay_json)
        rust_replay_2 = _read_json(replay_json_2)
        rust_cache_identity = _string_field(rust_replay, "cache_identity", "rust replay")
        rust_cache_identity_2 = _string_field(
            rust_replay_2,
            "cache_identity",
            "second rust replay",
        )
        expected_replay = _expected_replay(
            rows,
            dataset_hash,
            source_csv,
            cache_identity=str(rust_replay["cache_identity"]),
        )
        replay_differences = _replay_differences(expected_replay, rust_replay)
        if diff_artifact_dir is not None:
            diff_artifacts.append(
                _write_parity_diff_artifact(
                    diff_artifact_dir,
                    "phase2_replay_sequence_diff",
                    expected_replay,
                    rust_replay,
                    replay_differences,
                )
            )
        _assert_no_differences("replay", replay_differences)
        if rust_cache_identity != rust_cache_identity_2:
            raise AssertionError("replay cache identity is not stable")

        subprocess.run(
            [
                cargo,
                "run",
                "-q",
                "-p",
                "qts-cli",
                "--",
                "roll-select",
                "--root",
                "GC",
                "--exchange",
                "CME",
                "--session-date",
                ROLL_SESSION_DATE.isoformat(),
                "--roll-sessions-before-first-notice",
                "3",
                *[
                    value
                    for contract in ROLL_CONTRACTS
                    for value in ("--contract", _roll_contract_arg(contract))
                ],
                "--output-json",
                str(roll_json),
            ],
            cwd=repo_root / "rust",
            check=True,
        )
        rust_roll = _read_json(roll_json)
        expected_roll = _expected_roll_selection()
        roll_differences = _subset_differences("roll", expected_roll, rust_roll)
        if diff_artifact_dir is not None:
            diff_artifacts.append(
                _write_parity_diff_artifact(
                    diff_artifact_dir,
                    "phase3_continuous_future_roll_diff",
                    expected_roll,
                    rust_roll,
                    roll_differences,
                )
            )
        _assert_no_differences("roll", roll_differences)

        subprocess.run(
            [
                cargo,
                "run",
                "-q",
                "-p",
                "qts-cli",
                "--",
                "backtest",
                "--shadow",
                *_identity_args(),
                "--source-csv",
                str(source_csv),
                "--timeframe",
                TIMEFRAME,
                "--dataset-hash",
                dataset_hash,
                "--roll-policy",
                ROLL_POLICY,
                "--start",
                _timestamp_text(rows[0]["ts_event"]),
                "--end",
                _timestamp_text(rows[-1]["ts_event"] + timedelta(minutes=5)),
                "--initial-cash",
                "100000",
                "--quantity",
                "1",
                "--output-json",
                str(backtest_json),
                "--output-dir",
                str(rust_artifact_dir),
            ],
            cwd=repo_root / "rust",
            check=True,
        )
        rust_backtest = _read_json(backtest_json)
        expected_backtest = _expected_backtest(expected_replay, rust_cache_identity)
        backtest_differences = _subset_differences(
            "backtest",
            expected_backtest,
            rust_backtest,
        )
        if diff_artifact_dir is not None:
            diff_artifacts.append(
                _write_parity_diff_artifact(
                    diff_artifact_dir,
                    "phase3_engine_backtest_diff",
                    expected_backtest,
                    rust_backtest,
                    backtest_differences,
                )
            )
        _assert_no_differences("backtest", backtest_differences)
        _assert_engine_parity_state_flow(rust_backtest)
        dataset = BacktestRunReportLoader.from_run_directory(rust_artifact_dir)
        if dataset.manifest["runtime_mode"] != "backtest":
            raise AssertionError("Rust artifact manifest runtime_mode is not backtest")
        if dataset.manifest["execution_environment"] != "simulated":
            raise AssertionError("Rust artifact execution environment is not simulated")
        if len(dataset.artifacts.equity_curve) != len(
            _object_list_field(expected_replay, "events", "expected replay")
        ):
            raise AssertionError("Rust artifact equity_curve row count mismatch")
        if dataset.summary["report_hash"] != dataset.manifest["report_hash"]:
            raise AssertionError("Rust summary/manifest report_hash mismatch")
        if [event["kind"] for event in dataset.artifacts.events] != [
            "risk.accepted",
            "order.accepted",
            "execution.filled",
            "account.updated",
        ]:
            raise AssertionError("Rust artifact event chain mismatch")
        if dataset.artifacts.orders[0]["status"] != "filled":
            raise AssertionError("Rust artifact order state did not reach filled")
        if dataset.artifacts.fills[0]["account_id"] != "simulated-engine-account":
            raise AssertionError("Rust artifact fill missing account id")
        _assert_replacement_evidence_rejected(work, diff_artifacts)

    payload = {
        "status": "ok",
        "checked": [
            "phase1_materialize_golden",
            "phase1_rust_unit_tests",
            "phase2_replay_sequence_diff",
            "phase2_cache_identity_stability",
            "phase2_visible_at_no_lookahead",
            "phase3_engine_backtest_diff",
            "phase3_continuous_future_roll_diff",
            "phase3_risk_order_execution_account_state_flow",
            "phase3_manifest_compatible_artifacts",
            "phase4_release_gate_rejects_unclean_by_default",
        ],
        "engine_id": "rust",
        "engine_mode": "shadow",
        "reference_engine": "python",
        "candidate_replaces_reference": False,
        "diff_artifacts": diff_artifacts,
    }
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(payload, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(payload, sort_keys=True))
    return 0


def _run_rust_unit_tests(*, repo_root: Path, cargo: str) -> None:
    subprocess.run(
        [
            cargo,
            "test",
            "-q",
            "--workspace",
        ],
        cwd=repo_root / "rust",
        check=True,
    )


def _fixture_rows() -> list[FixtureRow]:
    start = datetime(2026, 1, 6, 14, 30, tzinfo=UTC)
    rows: list[FixtureRow] = [
        {
            "ts_event": start,
            "rtype": "",
            "publisher_id": "",
            "instrument_id": GC_INSTRUMENT_ID,
            "open": Decimal("2000"),
            "high": Decimal("2002"),
            "low": Decimal("1999"),
            "close": Decimal("2001"),
            "volume": Decimal("10"),
            "symbol": GC_SYMBOL,
        },
        {
            "ts_event": start,
            "rtype": "",
            "publisher_id": "",
            "instrument_id": SI_INSTRUMENT_ID,
            "open": Decimal("25"),
            "high": Decimal("25.2"),
            "low": Decimal("24.9"),
            "close": Decimal("25.1"),
            "volume": Decimal("20"),
            "symbol": SI_SYMBOL,
        },
        {
            "ts_event": start + timedelta(minutes=5),
            "rtype": "",
            "publisher_id": "",
            "instrument_id": GC_INSTRUMENT_ID,
            "open": Decimal("2002"),
            "high": Decimal("2004"),
            "low": Decimal("2001"),
            "close": Decimal("2003"),
            "volume": Decimal("12"),
            "symbol": GC_SYMBOL,
        },
        {
            "ts_event": start + timedelta(minutes=5),
            "rtype": "",
            "publisher_id": "",
            "instrument_id": SI_INSTRUMENT_ID,
            "open": Decimal("25.2"),
            "high": Decimal("25.4"),
            "low": Decimal("25.1"),
            "close": Decimal("25.3"),
            "volume": Decimal("22"),
            "symbol": SI_SYMBOL,
        },
    ]
    return sorted(rows, key=lambda row: (row["ts_event"], row["instrument_id"]))


def _write_source_csv(path: Path, rows: list[FixtureRow]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(EXPECTED_HISTORICAL_COLUMNS)
        for row in rows:
            writer.writerow(
                [
                    _timestamp_text(row["ts_event"]),
                    row["rtype"],
                    row["publisher_id"],
                    row["instrument_id"],
                    _decimal_text(row["open"]),
                    _decimal_text(row["high"]),
                    _decimal_text(row["low"]),
                    _decimal_text(row["close"]),
                    _decimal_text(row["volume"]),
                    row["symbol"],
                ]
            )


def _expected_replay(
    rows: list[FixtureRow],
    dataset_hash: str,
    source_csv: Path,
    *,
    cache_identity: str,
) -> dict[str, object]:
    return {
        "config": {
            "dataset_hash": dataset_hash,
            "timeframe": TIMEFRAME,
            "start": _timestamp_text(rows[0]["ts_event"]),
            "end": _timestamp_text(rows[-1]["ts_event"] + timedelta(minutes=5)),
            "roots": list(ROOTS),
            "symbols": [GC_SYMBOL, SI_SYMBOL],
            "instrument_ids": [GC_INSTRUMENT_ID, SI_INSTRUMENT_ID],
            "roll_policy": ROLL_POLICY,
            "source_path": str(source_csv),
        },
        "events": [
            {
                "sequence": index,
                "visible_at": _timestamp_text(row["ts_event"] + timedelta(minutes=5)),
                "bar": {
                    "instrument_id": row["instrument_id"],
                    "timeframe": TIMEFRAME,
                    "start_time": _timestamp_text(row["ts_event"]),
                    "end_time": _timestamp_text(row["ts_event"] + timedelta(minutes=5)),
                    "open": _decimal_text(row["open"]),
                    "high": _decimal_text(row["high"]),
                    "low": _decimal_text(row["low"]),
                    "close": _decimal_text(row["close"]),
                    "volume": _decimal_text(row["volume"]),
                    "session_id": "2026-01-06",
                    "is_complete": True,
                    "is_partial": False,
                    "is_synthetic": False,
                },
                "provenance": {
                    "cache_identity": cache_identity,
                    "dataset_hash": dataset_hash,
                    "timeframe": TIMEFRAME,
                    "roots": list(ROOTS),
                    "symbols": [GC_SYMBOL, SI_SYMBOL],
                    "instrument_ids": [GC_INSTRUMENT_ID, SI_INSTRUMENT_ID],
                    "roll_policy": ROLL_POLICY,
                    "source_path": str(source_csv),
                },
            }
            for index, row in enumerate(_replay_ordered_rows(rows))
        ],
    }


def _expected_backtest(
    expected_replay: dict[str, object],
    cache_identity: str,
) -> dict[str, object]:
    events = _object_list_field(expected_replay, "events", "expected replay")
    first = events[0]
    first_bar = _object_field(first, "bar", "first event")
    first_instrument_id = _string_field(first_bar, "instrument_id", "first bar")
    first_visible_at = _string_field(first, "visible_at", "first event")
    first_sequence = _int_field(first, "sequence", "first event")
    fill = next(
        event
        for event in events
        if _string_field(
            _object_field(event, "bar", "candidate event"),
            "instrument_id",
            "candidate bar",
        )
        == first_instrument_id
        and _string_field(
            _object_field(event, "bar", "candidate event"),
            "start_time",
            "candidate bar",
        )
        >= first_visible_at
        and _int_field(event, "sequence", "candidate event") > first_sequence
    )
    fill_bar = _object_field(fill, "bar", "fill event")
    fill_start_time = _string_field(fill_bar, "start_time", "fill bar")
    fill_sequence = _int_field(fill, "sequence", "fill event")
    fill_price = Decimal(_string_field(fill_bar, "open", "fill bar"))
    close = Decimal(_string_field(fill_bar, "close", "fill bar"))
    cash = Decimal("100000") - fill_price
    final_equity = cash + close
    processed_bars = len(events)
    equity_curve: list[dict[str, object]] = []
    running_equity = Decimal("100000")
    for event in events:
        event_sequence = _int_field(event, "sequence", "replay event")
        event_visible_at = _string_field(event, "visible_at", "replay event")
        event_bar = _object_field(event, "bar", "replay event")
        if event_sequence < fill_sequence:
            equity_curve.append(
                {
                    "timestamp": event_visible_at,
                    "cash": "100000",
                    "position_quantity": "0",
                    "positions": {},
                    "equity": _decimal_text(running_equity),
                }
            )
            continue
        if _string_field(event_bar, "instrument_id", "replay bar") == first_instrument_id:
            running_equity = cash + Decimal(_string_field(event_bar, "close", "replay bar"))
        equity_curve.append(
            {
                "timestamp": event_visible_at,
                "cash": _decimal_text(cash),
                "position_quantity": "1",
                "positions": {first_instrument_id: "1"},
                "equity": _decimal_text(running_equity),
            }
        )
    return {
        "manifest": {
            "mode": "shadow",
            "fill_timing": "next_bar_open",
            "replay_cache_identity": cache_identity,
            "processed_bars": processed_bars,
        },
        "events": [
            {
                "sequence_no": 0,
                "kind": "risk.accepted",
                "timestamp": first_visible_at,
                "order_id": "engine-order-1",
                "account_id": "simulated-engine-account",
                "instrument_id": first_instrument_id,
                "payload": {"quantity": "1"},
            },
            {
                "sequence_no": 1,
                "kind": "order.accepted",
                "timestamp": first_visible_at,
                "order_id": "engine-order-1",
                "account_id": "simulated-engine-account",
                "instrument_id": first_instrument_id,
                "payload": {"status": "accepted"},
            },
            {
                "sequence_no": 2,
                "kind": "execution.filled",
                "timestamp": fill_start_time,
                "order_id": "engine-order-1",
                "account_id": "simulated-engine-account",
                "instrument_id": first_instrument_id,
                "payload": {"price": _decimal_text(fill_price)},
            },
            {
                "sequence_no": 3,
                "kind": "account.updated",
                "timestamp": fill_start_time,
                "order_id": "engine-order-1",
                "account_id": "simulated-engine-account",
                "instrument_id": first_instrument_id,
                "payload": {
                    "cash": _decimal_text(cash),
                    "position_quantity": "1",
                },
            },
        ],
        "orders": [
            {
                "order_id": "engine-order-1",
                "submitted_at": first_visible_at,
                "instrument_id": first_instrument_id,
                "quantity": "1",
                "risk_status": "accepted",
                "status": "filled",
            }
        ],
        "fills": [
            {
                "order_id": "engine-order-1",
                "filled_at": fill_start_time,
                "instrument_id": first_instrument_id,
                "quantity": "1",
                "price": _decimal_text(fill_price),
                "account_id": "simulated-engine-account",
            }
        ],
        "equity_curve": equity_curve,
        "metrics": {
            "processed_bars": processed_bars,
            "orders": 1,
            "fills": 1,
            "final_cash": _decimal_text(cash),
            "final_equity": _decimal_text(final_equity),
        },
    }


def _expected_roll_selection() -> dict[str, object]:
    contracts = tuple(
        FutureContractRollSpec(
            symbol=symbol,
            instrument_id=InstrumentId(instrument_id),
            first_notice_day=first_notice_day,
            expiry=expiry,
        )
        for symbol, instrument_id, first_notice_day, expiry, _close, _volume in ROLL_CONTRACTS
    )
    candidates = tuple(
        FutureContractCandidate(
            root_symbol="GC",
            symbol=symbol,
            instrument_id=InstrumentId(instrument_id),
            as_of=ROLL_AS_OF,
            close=close,
            volume=volume,
            session_date=ROLL_SESSION_DATE,
        )
        for symbol, instrument_id, _first_notice_day, _expiry, close, volume in ROLL_CONTRACTS
    )
    selector = FirstNoticeDateFutureContractSelector(
        contracts=contracts,
        session_offset=_business_session_offset,
        roll_sessions_before_first_notice=3,
    )
    selected = selector.select(candidates)
    registry = FutureRollRegistry()
    continuous_id = registry.register_root(
        root_symbol="GC",
        exchange="CME",
        contracts=tuple(contract.instrument_id for contract in contracts),
    )
    registry.record_selection(
        FutureRollSelection(
            continuous_instrument_id=continuous_id,
            root_symbol="GC",
            as_of=ROLL_AS_OF,
            concrete_instrument_id=selected.instrument_id,
            source_symbol=selected.symbol,
            prices_by_instrument={
                candidate.instrument_id: candidate.close for candidate in candidates
            },
        )
    )
    resolved = registry.resolve_contract("GC", as_of=ROLL_AS_OF)
    if resolved != selected.instrument_id:
        raise AssertionError("Python roll registry and selector disagree")
    return {
        "continuous_instrument_id": continuous_id.value,
        "root_symbol": "GC",
        "exchange": "CME",
        "session_date": ROLL_SESSION_DATE.isoformat(),
        "concrete_instrument_id": selected.instrument_id.value,
        "source_symbol": selected.symbol,
        "roll_policy": "first_notice",
        "offset": 0,
    }


def _assert_engine_parity_state_flow(payload: dict[str, object]) -> None:
    events = payload.get("events")
    if not isinstance(events, list):
        raise AssertionError("Rust backtest payload missing events")
    kinds = [event.get("kind") for event in events if isinstance(event, dict)]
    if kinds != ["risk.accepted", "order.accepted", "execution.filled", "account.updated"]:
        raise AssertionError(f"Rust backtest state flow mismatch: {kinds}")
    equity_curve = payload.get("equity_curve")
    if not isinstance(equity_curve, list) or not equity_curve:
        raise AssertionError("Rust backtest payload missing equity curve")
    last = equity_curve[-1]
    if not isinstance(last, dict):
        raise AssertionError("Rust final equity point is not an object")
    positions = last.get("positions")
    if not isinstance(positions, dict):
        raise AssertionError("Rust final equity point missing positions")
    if positions.get(GC_INSTRUMENT_ID) != "1":
        raise AssertionError("Rust final position quantity mismatch")


def _assert_replacement_evidence_rejected(
    work_dir: Path,
    diff_artifacts: list[dict[str, object]],
) -> None:
    path = work_dir / "replacement-attempt-evidence.json"
    path.write_text(
        json.dumps(
            {
                "candidate_replaces_reference": True,
                "checked": [
                    "phase1_materialize_golden",
                    "phase1_rust_unit_tests",
                    "phase2_replay_sequence_diff",
                    "phase2_cache_identity_stability",
                    "phase2_visible_at_no_lookahead",
                    "phase3_engine_backtest_diff",
                    "phase3_continuous_future_roll_diff",
                    "phase3_risk_order_execution_account_state_flow",
                    "phase3_manifest_compatible_artifacts",
                    "phase4_release_gate_rejects_unclean_by_default",
                ],
                "diff_artifacts": diff_artifacts,
                "engine_id": "rust",
                "engine_mode": "shadow",
                "reference_engine": "python",
                "status": "ok",
            },
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    criterion = run_research.engine_parity_evidence_criterion(path)
    if criterion["accepted"] is not False:
        raise AssertionError("replacement evidence was not rejected")
    reasons = criterion.get("reasons")
    if not isinstance(reasons, list) or not any(
        "candidate_replaces_reference=false" in str(reason) for reason in reasons
    ):
        raise AssertionError("replacement evidence rejection reason is missing")


def _identity_args() -> list[str]:
    return [
        "--root",
        "GC",
        "--root",
        "SI",
        "--symbol",
        GC_SYMBOL,
        "--symbol",
        SI_SYMBOL,
        "--instrument-id",
        GC_INSTRUMENT_ID,
        "--instrument-id",
        SI_INSTRUMENT_ID,
    ]


def _replay_ordered_rows(rows: list[FixtureRow]) -> list[FixtureRow]:
    return sorted(
        rows,
        key=lambda row: (
            row["ts_event"] + timedelta(minutes=5),
            row["instrument_id"],
            TIMEFRAME,
            row["ts_event"],
        ),
    )


def _roll_contract_arg(
    contract: tuple[str, str, date, datetime, Decimal, Decimal],
) -> str:
    symbol, instrument_id, first_notice_day, expiry, _close, _volume = contract
    return "|".join(
        (
            symbol,
            instrument_id,
            first_notice_day.isoformat(),
            expiry.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
    )


def _business_session_offset(session_date: date, offset: int) -> date:
    step = 1 if offset >= 0 else -1
    remaining = abs(offset)
    current = session_date
    while remaining > 0:
        current += timedelta(days=step)
        if current.weekday() < 5:
            remaining -= 1
    return current


def _replay_differences(expected: dict[str, object], actual: dict[str, object]) -> list[str]:
    differences = []
    if not str(actual.get("cache_identity", "")).startswith("qts-replay-v1-"):
        differences.append("replay.cache_identity: missing stable qts-replay-v1 prefix")
    differences.extend(_subset_differences("replay", expected, actual))
    for event in _object_list_field(actual, "events", "actual replay"):
        bar = _object_field(event, "bar", "actual replay event")
        if _string_field(event, "visible_at", "actual replay event") != _string_field(
            bar,
            "end_time",
            "actual replay bar",
        ):
            differences.append("replay.events: bar is visible before completion")
    return differences


def _subset_differences(label: str, expected: object, actual: object) -> list[str]:
    differences: list[str] = []
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return [f"{label}: actual is not an object"]
        for key, value in expected.items():
            if key not in actual:
                differences.append(f"{label}: missing key {key}")
                continue
            differences.extend(_subset_differences(f"{label}.{key}", value, actual[key]))
        return differences
    if isinstance(expected, list):
        if not isinstance(actual, list):
            return [f"{label}: actual is not a list"]
        if len(expected) != len(actual):
            return [f"{label}: list length mismatch expected={len(expected)} actual={len(actual)}"]
        for index, value in enumerate(expected):
            differences.extend(_subset_differences(f"{label}[{index}]", value, actual[index]))
        return differences
    if expected != actual:
        differences.append(f"{label}: expected {expected!r}, got {actual!r}")
    return differences


def _assert_no_differences(label: str, differences: list[str]) -> None:
    if differences:
        raise AssertionError(f"{label}: parity diff is not clean: {differences}")


def _write_parity_diff_artifact(
    output_dir: Path,
    phase: str,
    reference: dict[str, object],
    candidate: dict[str, object],
    differences: list[str],
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{phase}.json"
    payload = {
        "artifact_type": "python_rust_parity_diff",
        "candidate_engine": "rust",
        "candidate_payload": candidate,
        "differences": differences,
        "phase": phase,
        "reference_engine": "python",
        "reference_payload": reference,
        "status": "clean" if not differences else "failed",
    }
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return {
        "phase": phase,
        "path": str(path),
        "sha256": _file_sha256(path),
        "status": payload["status"],
    }


def _file_sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _read_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected object JSON: {path}")
    return payload


def _object_field(payload: dict[str, object], key: str, label: str) -> dict[str, object]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise AssertionError(f"{label} missing object field: {key}")
    return cast(dict[str, object], value)


def _object_list_field(
    payload: dict[str, object],
    key: str,
    label: str,
) -> list[dict[str, object]]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise AssertionError(f"{label} missing list field: {key}")
    result: list[dict[str, object]] = []
    for item in value:
        if not isinstance(item, dict):
            raise AssertionError(f"{label}.{key} contains non-object item")
        result.append(cast(dict[str, object], item))
    return result


def _string_field(payload: dict[str, object], key: str, label: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise AssertionError(f"{label} missing string field: {key}")
    return value


def _int_field(payload: dict[str, object], key: str, label: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int):
        raise AssertionError(f"{label} missing int field: {key}")
    return value


def _timestamp_text(value: object) -> str:
    if not isinstance(value, datetime):
        raise TypeError(f"expected datetime, got {type(value)!r}")
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S") + ".000000000Z"


def _decimal_text(value: object) -> str:
    if not isinstance(value, Decimal):
        raise TypeError(f"expected Decimal, got {type(value)!r}")
    return format(value.normalize(), "f")


if __name__ == "__main__":
    raise SystemExit(main())
