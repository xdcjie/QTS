"""Backtest application service skeleton."""

from __future__ import annotations

from pathlib import Path

from qts.application.dto import BacktestRequestDTO, BacktestRunDTO
from qts.application.services.backtest_summary_store import BacktestSummaryStore
from qts.backtest.runner import run_backtest


class BacktestService:
    """Application boundary for backtest use cases."""

    def __init__(
        self,
        *,
        output_dir: Path | None = None,
        summary_store: BacktestSummaryStore | None = None,
    ) -> None:
        """Perform __init__."""
        self._output_dir = output_dir if output_dir is not None else Path("runs/backtests")
        self._summary_store = (
            summary_store if summary_store is not None else BacktestSummaryStore(self._output_dir)
        )

    def submit(self, request: BacktestRequestDTO) -> BacktestRunDTO:
        """Perform submit."""
        run = run_backtest(Path(request.config_path), output_dir=self._output_dir)
        return BacktestRunDTO(
            run_id=run.result.run_id.value,
            config_path=str(request.config_path),
            status="accepted",
            summary_path=str(run.summary_path),
            manifest_path=str(run.manifest_path),
            report_hash=run.result.report_hash,
        )

    def list_runs(self, *, limit: int | None = None) -> tuple[BacktestRunDTO, ...]:
        """List completed or failed backtests from persisted summaries."""
        summaries = self._summary_store.list_runs()
        if limit is None:
            return summaries
        if limit < 0:
            raise ValueError("limit must be non-negative")
        return summaries[:limit]


__all__ = ["BacktestService"]
