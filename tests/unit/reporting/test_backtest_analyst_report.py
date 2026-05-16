from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from subprocess import CompletedProcess

import pytest


def test_loader_reads_summary_manifest_and_artifact_rows(tmp_path: Path) -> None:
    from qts.reporting.backtest_analyst import BacktestRunReportLoader

    summary_path = _write_completed_run(tmp_path)

    dataset = BacktestRunReportLoader.from_summary(summary_path)

    assert dataset.run_id == "bt-analyst"
    assert dataset.summary["status"] == "completed"
    assert dataset.manifest["report_hash"] == "sha256:report"
    assert len(dataset.artifacts.equity_curve) == 2
    assert len(dataset.artifacts.orders) == 1
    assert len(dataset.artifacts.fills) == 1
    assert len(dataset.artifacts.trade_ledger) == 1
    assert len(dataset.artifacts.events) == 1


def test_loader_rejects_missing_required_artifact(tmp_path: Path) -> None:
    from qts.reporting.backtest_analyst import BacktestReportError, BacktestRunReportLoader

    summary_path = _write_completed_run(tmp_path)
    (tmp_path / "bt-analyst.fills.ndjson").unlink()

    with pytest.raises(BacktestReportError, match="fills"):
        BacktestRunReportLoader.from_summary(summary_path)


def test_dataset_derives_analyst_metrics_from_finalized_artifacts(tmp_path: Path) -> None:
    from qts.reporting.backtest_analyst import BacktestRunReportLoader

    dataset = BacktestRunReportLoader.from_summary(_write_completed_run(tmp_path))
    metrics = dataset.metrics

    assert metrics.total_return == "0.50%"
    assert metrics.max_drawdown == "0.00%"
    assert metrics.final_equity == "100500"
    assert metrics.trade_count == 1
    assert metrics.fill_count == 1
    assert metrics.order_count == 1


def test_html_renderer_includes_metrics_chart_and_artifact_links(tmp_path: Path) -> None:
    from qts.reporting.backtest_analyst import (
        AnalystBacktestReportRenderer,
        BacktestRunReportLoader,
    )

    dataset = BacktestRunReportLoader.from_summary(_write_completed_run(tmp_path))

    html = AnalystBacktestReportRenderer().render(dataset)

    assert "VWAP Backtest Analyst Report" in html
    assert "bt-analyst" in html
    assert "sha256:report" in html
    assert "Total Return" in html
    assert "Max Drawdown" in html
    assert "Trade Count" in html
    assert "<svg" in html
    assert "bt-analyst.equity_curve.ndjson" in html
    assert "bt-analyst.manifest.json" in html


def test_pdf_exporter_invokes_configured_chrome(tmp_path: Path) -> None:
    from qts.reporting.backtest_analyst import BacktestPdfExporter

    calls: list[Sequence[str]] = []
    html_path = tmp_path / "report.html"
    pdf_path = tmp_path / "report.pdf"
    html_path.write_text("<html><body>report</body></html>", encoding="utf-8")

    def fake_run(command: Sequence[str], **kwargs: object) -> CompletedProcess[str]:
        calls.append(command)
        pdf_path.write_bytes(b"%PDF-1.4\n")
        return CompletedProcess(args=command, returncode=0, stdout="", stderr="")

    BacktestPdfExporter(chrome_path=Path("/tmp/chrome"), run_command=fake_run).export(
        html_path,
        pdf_path,
    )

    assert calls
    assert calls[0][0] == "/tmp/chrome"
    assert "--headless" in calls[0]
    assert "--disable-gpu" in calls[0]
    assert f"--print-to-pdf={pdf_path}" in calls[0]
    assert str(html_path.resolve().as_uri()) in calls[0]


def test_pdf_exporter_rejects_missing_chrome(tmp_path: Path) -> None:
    from qts.reporting.backtest_analyst import BacktestPdfExporter, BacktestReportError

    html_path = tmp_path / "report.html"
    html_path.write_text("<html><body>report</body></html>", encoding="utf-8")

    with pytest.raises(BacktestReportError, match="Chrome"):
        BacktestPdfExporter(chrome_path=None).export(html_path, tmp_path / "report.pdf")


def _write_completed_run(tmp_path: Path) -> Path:
    run_id = "bt-analyst"
    artifact_paths = {
        "events": tmp_path / f"{run_id}.events.ndjson",
        "orders": tmp_path / f"{run_id}.orders.ndjson",
        "fills": tmp_path / f"{run_id}.fills.ndjson",
        "trade_ledger": tmp_path / f"{run_id}.trade_ledger.ndjson",
        "equity_curve": tmp_path / f"{run_id}.equity_curve.ndjson",
    }
    _write_ndjson(
        artifact_paths["events"],
        ({"kind": "runtime.market_data", "payload": {"instrument_id": "EQUITY.AAPL"}},),
    )
    _write_ndjson(
        artifact_paths["orders"],
        ({"order_id": "order-1", "instrument_id": "EQUITY.AAPL", "side": "BUY"},),
    )
    _write_ndjson(
        artifact_paths["fills"],
        ({"order_id": "order-1", "fill_price": "100", "quantity": "1"},),
    )
    _write_ndjson(
        artifact_paths["trade_ledger"],
        (
            {
                "order_id": "order-1",
                "instrument_id": "EQUITY.AAPL",
                "side": "BUY",
                "quantity": "1",
                "fill_price": "100",
                "commission": "0",
                "slippage": "0",
            },
        ),
    )
    _write_ndjson(
        artifact_paths["equity_curve"],
        (
            {"time": "2026-01-02T14:30:00+00:00", "equity": "100000"},
            {"time": "2026-01-02T14:31:00+00:00", "equity": "100500"},
        ),
    )
    manifest_path = tmp_path / f"{run_id}.manifest.json"
    manifest = {
        "run_id": run_id,
        "runtime_mode": "backtest",
        "report_hash": "sha256:report",
        "config_hash": "sha256:config",
        "topology_hash": "sha256:topology",
        "processed_bars": 2,
        "warmup_bars": 0,
        "trading_bars": 2,
        "metrics": {"total_return": "0.005", "max_drawdown": "0", "points": 2},
        "dataset_metadata": [
            {
                "dataset_id": "dataset-a",
                "source": "historical/data/aapl.csv",
                "instrument_id": "EQUITY.AAPL",
                "timeframe": "1m",
                "file_hash": "sha256:data",
                "row_count": 2,
                "first_ts": "2026-01-02T14:30:00+00:00",
                "last_ts": "2026-01-02T14:31:00+00:00",
                "timezone": "UTC",
                "adjustment_mode": "raw",
            }
        ],
        "cost_model": {"fixed_commission_per_contract": "0", "slippage_bps": "0"},
        "execution_assumptions": {"fill_model_name": "immediate_market_fill"},
        "artifacts": {
            name: {"path": str(path), "rows": _line_count(path), "sha256": "sha256:artifact"}
            for name, path in artifact_paths.items()
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    summary_path = tmp_path / f"{run_id}.summary.json"
    summary = {
        "schema_version": "1",
        "run_id": run_id,
        "status": "completed",
        "manifest_path": str(manifest_path),
        "processed_bars": 2,
        "warmup_bars": 0,
        "trading_bars": 2,
        "report_hash": "sha256:report",
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary_path


def _write_ndjson(path: Path, rows: tuple[dict[str, object], ...]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())
