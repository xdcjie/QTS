from __future__ import annotations

from pathlib import Path

from qts.research.data_quality import DataQualityRunner


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
