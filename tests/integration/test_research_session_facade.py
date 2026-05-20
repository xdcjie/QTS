"""Integration tests for the notebook-friendly ResearchSession facade."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from qts.research import HistoryRequest, ResearchSession

from tests.integration.test_optimizer_consumes_backtest_config import _write_fixtures


def _write_research_session_config(tmp_path: Path) -> Path:
    backtest_config, data_config = _write_fixtures(tmp_path)
    config_path = tmp_path / "research.yaml"
    config_path.write_text(
        f"""
data:
  config: {data_config}
  catalog: research
  roots: [EQUITY]
  timeframe: 1m
  instrument_ids:
    AAPL: EQUITY.US.NASDAQ.AAPL
backtest_config: {backtest_config}
store: research-store
output_root: research-runs
objective_metric: total_return
""",
        encoding="utf-8",
    )
    return config_path


def test_research_session_reads_history_through_research_book(tmp_path: Path) -> None:
    session = ResearchSession.from_yaml(_write_research_session_config(tmp_path))

    frame = session.history_frame(
        HistoryRequest(
            root="EQUITY",
            start=datetime(2010, 6, 6, 22, 0, tzinfo=UTC),
            end=datetime(2010, 6, 6, 22, 5, tzinfo=UTC),
            timeframe="1m",
        )
    )

    assert len(frame) == 5
    assert list(frame["instrument_id"]) == ["EQUITY.US.NASDAQ.AAPL"] * 5


def test_research_session_run_backtest_uses_shared_backtest_pipeline(tmp_path: Path) -> None:
    session = ResearchSession.from_yaml(_write_research_session_config(tmp_path))

    result = session.run_backtest(strategy_params={"quantity": "2"})

    assert result.manifest_path.exists()
    assert result.trading_bars == 5
    assert result.processed_bars == 5
    assert result.manifest_path.parent == tmp_path / "research-runs" / "single-run"


def test_research_session_optimize_uses_backtest_pipeline_runner(tmp_path: Path) -> None:
    session = ResearchSession.from_yaml(_write_research_session_config(tmp_path))

    results = session.optimize(
        parameters={
            "entry_bar": [1, 2],
            "quantity": ["1", "2"],
        }
    )

    assert len(results) == 4
    assert all(result.manifest_path.exists() for result in results)
    assert all(
        result.manifest_path.parent.parent == tmp_path / "research-runs" / "optimizer"
        for result in results
    )
