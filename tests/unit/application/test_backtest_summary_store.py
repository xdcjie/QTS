from __future__ import annotations

import json
from pathlib import Path


def test_backtest_summary_store_lists_schema_v1_summaries_newest_first(tmp_path: Path) -> None:
    from qts.application.services.backtest_summary_store import BacktestSummaryStore

    older = tmp_path / "bt-older.summary.json"
    older.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "run_id": "bt-older",
                "config_path": "configs/older.yaml",
                "status": "completed",
                "manifest_path": "runs/backtests/bt-older.manifest.json",
                "report_hash": "sha256:older",
            }
        ),
        encoding="utf-8",
    )
    newer = tmp_path / "bt-newer.summary.json"
    newer.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "run_id": "bt-newer",
                "config_path": "configs/newer.yaml",
                "status": "failed",
                "manifest_path": "runs/backtests/bt-newer.manifest.json",
                "report_hash": "sha256:newer",
            }
        ),
        encoding="utf-8",
    )
    older.touch()
    newer.touch()

    runs = BacktestSummaryStore(tmp_path).list_runs()

    assert [run.run_id for run in runs] == ["bt-newer", "bt-older"]
    assert runs[0].config_path == "configs/newer.yaml"
    assert runs[0].status == "failed"
    assert runs[0].summary_path == str(newer)
    assert runs[0].manifest_path == "runs/backtests/bt-newer.manifest.json"
    assert runs[0].report_hash == "sha256:newer"


def test_backtest_summary_store_marks_missing_config_path_as_invalid_summary(
    tmp_path: Path,
) -> None:
    from qts.application.services.backtest_summary_store import BacktestSummaryStore

    path = tmp_path / "bt-compat.summary.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "run_id": "bt-compat",
                "status": "completed",
            }
        ),
        encoding="utf-8",
    )

    runs = BacktestSummaryStore(tmp_path).list_runs()

    assert len(runs) == 1
    assert runs[0].run_id == "bt-compat"
    assert runs[0].config_path == ""
    assert runs[0].status == "invalid_summary"


def test_backtest_summary_store_marks_invalid_json_as_invalid_summary(tmp_path: Path) -> None:
    from qts.application.services.backtest_summary_store import BacktestSummaryStore

    path = tmp_path / "bt-broken.summary.json"
    path.write_text("{", encoding="utf-8")

    runs = BacktestSummaryStore(tmp_path).list_runs()

    assert len(runs) == 1
    assert runs[0].run_id == "bt-broken"
    assert runs[0].config_path == ""
    assert runs[0].status == "invalid_summary"
