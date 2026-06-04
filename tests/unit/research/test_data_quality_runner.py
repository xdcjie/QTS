from __future__ import annotations

from pathlib import Path

from qts.research.data_quality import DataQualityRunner


def _write_gc_chain(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """
{
  "root": "GC",
  "market": "CME_FUT",
  "currency": "USD",
  "timezone_id": "US/Eastern",
  "tick_size": "0.1",
  "multiplier": "100",
  "trading_calendar": "CMES",
  "trading_hours": "20260104:1800-20260105:1700",
  "contracts": [
    {
      "local_symbol": "GCG6",
      "expiry": "2026-02-25T00:00:00+00:00",
      "first_notice_day": "2026-01-30"
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )


def test_data_quality_runner_is_public_package_export() -> None:
    import qts.research as research

    assert research.DataQualityRunner is DataQualityRunner


def test_data_quality_runner_accepts_clean_bar_fixture(tmp_path: Path) -> None:
    bars_path = tmp_path / "bars.csv"
    bars_path.write_text(
        "timestamp,close\n"
        "2026-01-02T14:30:00Z,100\n"
        "2026-01-02T14:31:00Z,101\n"
        "2026-01-02T14:32:00Z,102\n",
        encoding="utf-8",
    )

    artifact = DataQualityRunner(
        dataset_id="dataset-001",
        timeframe="1m",
        start="2026-01-02T14:30:00Z",
        end="2026-01-02T14:33:00Z",
        calendar="TEST",
    ).run({"dataset_files": [{"path": str(bars_path), "exists": True}]})

    assert artifact.accepted is True
    assert artifact.checked_paths == (str(bars_path),)
    assert artifact.blockers() == ()


def test_data_quality_runner_detects_duplicate_and_missing_bars(tmp_path: Path) -> None:
    bars_path = tmp_path / "bars.csv"
    bars_path.write_text(
        "timestamp,close\n"
        "2026-01-02T14:30:00Z,100\n"
        "2026-01-02T14:31:00Z,101\n"
        "2026-01-02T14:31:00Z,102\n"
        "2026-01-02T14:34:00Z,103\n",
        encoding="utf-8",
    )

    artifact = DataQualityRunner(
        dataset_id="dataset-001",
        timeframe="1m",
        start="2026-01-02T14:30:00Z",
        end="2026-01-02T14:35:00Z",
        calendar="TEST",
    ).run({"dataset_files": [{"path": str(bars_path), "exists": True}]})

    assert artifact.accepted is False
    assert artifact.duplicate_timestamps == 1
    assert artifact.missing_bars == 2
    assert {"code": "duplicate_timestamps", "message": "duplicate timestamps detected: 1"} in (
        artifact.blockers()
    )
    assert {"code": "missing_bars", "message": "missing bars detected: 2"} in artifact.blockers()


def test_data_quality_runner_records_trusted_sparse_missing_bars(tmp_path: Path) -> None:
    bars_path = tmp_path / "bars.csv"
    bars_path.write_text(
        "timestamp,close\n"
        "2026-01-02T14:30:00Z,100\n"
        "2026-01-02T14:31:00Z,101\n"
        "2026-01-02T14:34:00Z,103\n",
        encoding="utf-8",
    )

    artifact = DataQualityRunner(
        dataset_id="dataset-001",
        timeframe="1m",
        start="2026-01-02T14:30:00Z",
        end="2026-01-02T14:35:00Z",
        calendar="TEST",
        missing_bar_policy="record_only",
    ).run({"dataset_files": [{"path": str(bars_path), "exists": True}]})

    assert artifact.accepted is True
    assert artifact.missing_bars == 2
    assert artifact.missing_bar_policy == "record_only"
    assert artifact.blockers() == ()


def test_data_quality_runner_counts_missing_start_and_end_boundary_bars(
    tmp_path: Path,
) -> None:
    bars_path = tmp_path / "bars.csv"
    bars_path.write_text(
        "timestamp,close\n2026-01-02T14:31:00Z,101\n2026-01-02T14:32:00Z,102\n",
        encoding="utf-8",
    )

    artifact = DataQualityRunner(
        dataset_id="dataset-001",
        timeframe="1m",
        start="2026-01-02T14:30:00Z",
        end="2026-01-02T14:34:00Z",
        calendar="TEST",
    ).run({"dataset_files": [{"path": str(bars_path), "exists": True}]})

    assert artifact.accepted is False
    assert artifact.missing_bars == 2
    assert {"code": "missing_bars", "message": "missing bars detected: 2"} in artifact.blockers()


def test_data_quality_runner_counts_missing_bars_per_declared_window(tmp_path: Path) -> None:
    bars_path = tmp_path / "bars.csv"
    bars_path.write_text(
        "timestamp,close\n"
        "2026-01-02T14:30:00Z,100\n"
        "2026-01-02T14:31:00Z,101\n"
        "2026-01-03T14:30:00Z,102\n"
        "2026-01-03T14:31:00Z,103\n",
        encoding="utf-8",
    )

    artifact = DataQualityRunner(
        dataset_id="dataset-001",
        timeframe="1m",
        calendar="TEST",
        windows=(
            {"start": "2026-01-02T14:30:00Z", "end": "2026-01-02T14:32:00Z"},
            {"start": "2026-01-03T14:30:00Z", "end": "2026-01-03T14:32:00Z"},
        ),
    ).run({"dataset_files": [{"path": str(bars_path), "exists": True}]})

    assert artifact.accepted is True
    assert artifact.missing_bars == 0


def test_data_quality_runner_ignores_closed_periods_from_historical_chain(
    tmp_path: Path,
) -> None:
    root = tmp_path / "historical"
    bars_path = root / "data" / "GC.csv"
    bars_path.parent.mkdir(parents=True, exist_ok=True)
    bars_path.write_text(
        "timestamp,close\n"
        "2026-01-02T21:59:00Z,100\n"
        "2026-01-04T23:00:00Z,101\n"
        "2026-01-04T23:01:00Z,102\n",
        encoding="utf-8",
    )
    _write_gc_chain(root / "chains" / "GC.json")

    artifact = DataQualityRunner(
        dataset_id="dataset-001",
        timeframe="1m",
        start="2026-01-02T21:59:00Z",
        end="2026-01-04T23:02:00Z",
        calendar="CMES",
    ).run({"dataset_files": [{"path": str(bars_path), "exists": True}]})

    assert artifact.accepted is True
    assert artifact.missing_bars == 0


def test_data_quality_runner_counts_in_session_missing_bars_from_historical_chain(
    tmp_path: Path,
) -> None:
    root = tmp_path / "historical"
    bars_path = root / "data" / "GC.csv"
    bars_path.parent.mkdir(parents=True, exist_ok=True)
    bars_path.write_text(
        "timestamp,close\n2026-01-04T23:00:00Z,100\n2026-01-04T23:02:00Z,102\n",
        encoding="utf-8",
    )
    _write_gc_chain(root / "chains" / "GC.json")

    artifact = DataQualityRunner(
        dataset_id="dataset-001",
        timeframe="1m",
        start="2026-01-04T23:00:00Z",
        end="2026-01-04T23:03:00Z",
        calendar="CMES",
        missing_bar_policy="record_only",
    ).run({"dataset_files": [{"path": str(bars_path), "exists": True}]})

    assert artifact.accepted is True
    assert artifact.missing_bars == 1


def test_data_quality_runner_detects_session_alignment_and_stale_prices(
    tmp_path: Path,
) -> None:
    bars_path = tmp_path / "bars.csv"
    bars_path.write_text(
        "timestamp,close\n"
        "2026-01-02T14:29:00Z,100\n"
        "2026-01-02T14:30:00Z,100\n"
        "2026-01-02T14:31:00Z,100\n"
        "2026-01-02T14:32:00Z,100\n",
        encoding="utf-8",
    )

    artifact = DataQualityRunner(
        dataset_id="dataset-001",
        timeframe="1m",
        start="2026-01-02T14:30:00Z",
        end="2026-01-02T14:33:00Z",
        calendar="TEST",
        stale_price_max_repeats=2,
    ).run({"dataset_files": [{"path": str(bars_path), "exists": True}]})

    assert artifact.accepted is False
    assert artifact.session_alignment is False
    assert artifact.stale_prices == 2
    assert {"code": "session_alignment", "message": "session alignment check failed"} in (
        artifact.blockers()
    )
    assert {"code": "stale_prices", "message": "stale prices detected: 2"} in artifact.blockers()


def test_data_quality_runner_detects_label_visibility_failure(tmp_path: Path) -> None:
    bars_path = tmp_path / "bars.csv"
    bars_path.write_text(
        "timestamp,close\n2026-01-02T14:30:00Z,100\n",
        encoding="utf-8",
    )
    labels_path = tmp_path / "labels.csv"
    labels_path.write_text(
        "timestamp,label_timestamp,visible_at\n"
        "2026-01-02T14:30:00Z,2026-01-02T14:35:00Z,2026-01-02T14:34:00Z\n",
        encoding="utf-8",
    )

    artifact = DataQualityRunner(
        dataset_id="dataset-001",
        timeframe="1m",
        start="2026-01-02T14:30:00Z",
        end="2026-01-02T14:31:00Z",
        calendar="TEST",
    ).run(
        {
            "dataset_files": [{"path": str(bars_path), "exists": True}],
            "label_paths": [str(labels_path)],
        }
    )

    assert artifact.accepted is False
    assert artifact.label_visibility is False
    assert {"code": "label_visibility", "message": "label visibility check failed"} in (
        artifact.blockers()
    )


def test_data_quality_runner_rejects_missing_dataset_file(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing-bars.csv"

    artifact = DataQualityRunner(
        dataset_id="dataset-001",
        timeframe="1m",
        start="2026-01-02T14:30:00Z",
        end="2026-01-02T14:31:00Z",
        calendar="TEST",
    ).run({"dataset_files": [{"path": str(missing_path), "exists": False}]})

    assert artifact.accepted is False
    assert artifact.checked_paths == (str(missing_path),)
    assert {
        "code": "missing_checked_path",
        "message": f"checked path does not exist: {missing_path}",
    } in artifact.blockers()
