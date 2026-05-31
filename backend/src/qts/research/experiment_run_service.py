"""Experiment-run recording and comparison service.

Owns recording completed experiment manifests into the session store and
comparing indexed runs by a metric (QTS-FINAL-011 extraction from
``ResearchSession`` so the facade keeps no experiment-persistence logic).
"""

from __future__ import annotations

import importlib
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from qts.research.experiment_store import ExperimentStore, ExperimentStoreRecord


class ExperimentRunService:
    """Owns recording and metric-comparison of indexed experiment runs."""

    def __init__(self, *, store: ExperimentStore) -> None:
        """Create the service bound to an experiment store."""
        self._store = store

    def record_manifest(
        self,
        manifest_path: Path,
        *,
        recorded_at: datetime | None = None,
    ) -> ExperimentStoreRecord:
        """Record a completed experiment manifest in the session store."""

        return self._store.record_manifest(manifest_path, recorded_at=recorded_at)

    def list_runs(self, *, limit: int | None = None) -> tuple[ExperimentStoreRecord, ...]:
        """Return indexed experiment records, newest first."""

        return self._store.list_runs(limit=limit)

    def compare_runs(self, metric: str) -> tuple[ExperimentStoreRecord, ...]:
        """Return records sorted descending by a Decimal-parseable metric."""

        scored: list[tuple[Decimal, ExperimentStoreRecord]] = []
        for record in self._store.list_runs():
            raw_metric = record.metrics.get(metric)
            if raw_metric is None:
                continue
            try:
                scored.append((Decimal(str(raw_metric)), record))
            except (InvalidOperation, ValueError):
                continue
        return tuple(
            record for _score, record in sorted(scored, key=lambda item: item[0], reverse=True)
        )

    def compare_frame(self, metric: str) -> Any:
        """Return a pandas DataFrame comparing stored experiment runs."""

        pandas_module: Any = importlib.import_module("pandas")
        return pandas_module.DataFrame(
            [
                {
                    "experiment_id": record.experiment_id,
                    "manifest_path": str(record.manifest_path),
                    "metric": metric,
                    "metric_value": Decimal(str(record.metrics[metric])),
                    "recorded_at": record.recorded_at,
                    "strategy_name": record.strategy_name,
                    "strategy_version": record.strategy_version,
                }
                for record in self.compare_runs(metric)
            ]
        )


__all__ = ["ExperimentRunService"]
