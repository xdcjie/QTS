"""Persisted backtest summary access."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qts.application.dto import BacktestRunDTO


class BacktestSummaryStore:
    """Read persisted backtest summary files with schema compatibility checks."""

    _SCHEMA_VERSION = "1"

    def __init__(self, output_dir: Path) -> None:
        """Perform __init__."""
        self._output_dir = output_dir

    def list_runs(self) -> tuple[BacktestRunDTO, ...]:
        """List summary-backed backtest runs newest first."""
        if not self._output_dir.exists():
            return ()
        return tuple(
            self._read_summary(path)
            for path in sorted(
                self._output_dir.glob("bt-*.summary.json"),
                key=lambda item: item.stat().st_mtime,
                reverse=True,
            )
        )

    def _read_summary(self, path: Path) -> BacktestRunDTO:
        """Read one summary file into the public application DTO."""
        payload = self._summary_payload(path)
        if payload is None:
            return self._invalid_summary(path)

        run_id = self._string_field(payload, "run_id")
        if run_id is None:
            run_id = self._run_id_from_summary_path(path)

        schema_version = self._string_field(payload, "schema_version")
        config_path = self._string_field(payload, "config_path")
        status = self._string_field(payload, "status")
        if schema_version != self._SCHEMA_VERSION or config_path is None:
            return BacktestRunDTO(
                run_id=run_id,
                config_path="",
                status="legacy_summary",
                summary_path=str(path),
                manifest_path=self._string_field(payload, "manifest_path"),
                report_hash=self._string_field(payload, "report_hash"),
            )

        return BacktestRunDTO(
            run_id=run_id,
            config_path=config_path,
            status=status if status is not None else "completed",
            summary_path=str(path),
            manifest_path=self._string_field(payload, "manifest_path"),
            report_hash=self._string_field(payload, "report_hash"),
        )

    def _summary_payload(self, path: Path) -> dict[str, Any] | None:
        """Load a summary payload if it is readable JSON object."""
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if not isinstance(payload, dict):
            return None
        return payload

    def _invalid_summary(self, path: Path) -> BacktestRunDTO:
        """Return a deterministic DTO for unreadable summary files."""
        return BacktestRunDTO(
            run_id=self._run_id_from_summary_path(path),
            config_path="",
            status="invalid_summary",
            summary_path=str(path),
        )

    @staticmethod
    def _run_id_from_summary_path(path: Path) -> str:
        """Derive run id from a canonical summary file name."""
        return path.name.removesuffix(".summary.json")

    @staticmethod
    def _string_field(payload: dict[str, Any], name: str) -> str | None:
        """Return a non-empty string field from a summary payload."""
        value = payload.get(name)
        if isinstance(value, str) and value:
            return value
        return None


__all__ = ["BacktestSummaryStore"]
