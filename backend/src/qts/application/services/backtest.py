"""Backtest application service skeleton."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qts.application.dto import BacktestRequestDTO, BacktestRunDTO, BacktestRunResultDTO
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
        """Initialize the service with its output directory and summary store."""
        self._output_dir = output_dir if output_dir is not None else Path("runs/backtests")
        self._summary_store = (
            summary_store if summary_store is not None else BacktestSummaryStore(self._output_dir)
        )

    def submit(self, request: BacktestRequestDTO) -> BacktestRunResultDTO:
        """Submit a backtest request and return the research artifact contract."""
        run = run_backtest(Path(request.config_path), output_dir=self._output_dir)
        return self._result_from_manifest(Path(run.manifest_path))

    def submit_batch(self, requests: list[BacktestRequestDTO]) -> tuple[BacktestRunResultDTO, ...]:
        """Submit multiple backtest requests in caller-provided order."""
        return tuple(self.submit(request) for request in requests)

    def list_runs(self, *, limit: int | None = None) -> tuple[BacktestRunDTO, ...]:
        """List completed or failed backtests from persisted summaries."""
        summaries = self._summary_store.list_runs()
        if limit is None:
            return summaries
        if limit < 0:
            raise ValueError("limit must be non-negative")
        return summaries[:limit]

    @classmethod
    def _result_from_manifest(cls, manifest_path: Path) -> BacktestRunResultDTO:
        """Map a persisted manifest into the stable research result DTO."""
        payload = cls._manifest_payload(manifest_path)
        artifacts = cls._mapping_field(payload, "artifacts")
        return BacktestRunResultDTO(
            run_id=cls._required_string(payload, "run_id"),
            manifest_path=str(manifest_path),
            equity_curve_path=cls._artifact_path(artifacts, "equity_curve"),
            orders_path=cls._artifact_path(artifacts, "orders"),
            fills_path=cls._artifact_path(artifacts, "fills"),
            metrics=dict(cls._mapping_field(payload, "metrics")),
            artifact_hashes={
                kind: cls._artifact_hash(artifacts, kind)
                for kind in ("equity_curve", "orders", "fills")
            },
        )

    @staticmethod
    def _manifest_payload(manifest_path: Path) -> dict[str, Any]:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"backtest manifest must be a JSON object: {manifest_path}")
        return payload

    @classmethod
    def _artifact_path(cls, artifacts: dict[str, Any], kind: str) -> str:
        artifact = cls._mapping_field(artifacts, kind)
        return cls._required_string(artifact, "path")

    @classmethod
    def _artifact_hash(cls, artifacts: dict[str, Any], kind: str) -> str:
        artifact = cls._mapping_field(artifacts, kind)
        return cls._required_string(artifact, "sha256")

    @staticmethod
    def _mapping_field(payload: dict[str, Any], name: str) -> dict[str, Any]:
        value = payload.get(name)
        if not isinstance(value, dict):
            raise ValueError(f"backtest manifest field must be an object: {name}")
        return value

    @staticmethod
    def _required_string(payload: dict[str, Any], name: str) -> str:
        value = payload.get(name)
        if not isinstance(value, str) or not value:
            raise ValueError(f"backtest manifest field must be a non-empty string: {name}")
        return value


__all__ = ["BacktestService"]
