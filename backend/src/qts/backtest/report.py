"""Backtest report artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from qts.core.hashing import stable_json_default, stable_json_hash
from qts.data.provenance import DatasetMetadata


def dataset_metadata_payload(item: DatasetMetadata) -> dict[str, str | None]:
    """Serialize one dataset provenance row for reporting."""
    return {
        "dataset_id": item.dataset_id,
        "source": item.source,
        "instrument_id": item.instrument_id.value,
        "timeframe": item.timeframe,
        "timezone_policy": item.timezone_policy,
        "adjustment_policy": item.adjustment_policy,
        "normalization_version": item.normalization_version,
        "created_at": item.created_at.isoformat(),
        "content_hash": item.content_hash,
    }


def zero_time() -> datetime:
    """Return the epoch boundary used for empty-equity bootstrap."""
    from datetime import UTC

    return datetime(1970, 1, 1, tzinfo=UTC)


@dataclass(frozen=True, slots=True)
class EquityCurvePoint:
    """One timestamped equity observation."""

    time: datetime
    equity: Decimal


@dataclass(frozen=True, slots=True)
class TradeLedgerEntry:
    """Auditable row for a simulated fill."""

    order_id: str
    instrument_id: str
    side: str
    quantity: Decimal
    fill_price: Decimal
    commission: Decimal
    slippage: Decimal
    fill_time: datetime
    source_bar_time: datetime


def _stable_hash(payload: Any) -> str:
    """Perform _stable_hash."""
    return stable_json_hash(payload)


class StreamingEquityMetrics:
    """Incremental metrics for a streamed equity curve."""

    def __init__(self) -> None:
        """Perform __init__."""
        self._points = 0
        self._first: Decimal | None = None
        self._last: Decimal | None = None
        self._peak: Decimal | None = None
        self._max_drawdown = Decimal("0")

    def update(self, equity: Decimal) -> None:
        """Perform update."""
        if self._first is None:
            if equity == Decimal("0"):
                raise ValueError("first equity value must not be zero")
            self._first = equity
            self._peak = equity
        assert self._peak is not None
        if equity > self._peak:
            self._peak = equity
        if self._peak != Decimal("0"):
            drawdown = (self._peak - equity) / self._peak
            if drawdown > self._max_drawdown:
                self._max_drawdown = drawdown
        self._last = equity
        self._points += 1

    def to_payload(self) -> dict[str, Decimal | int]:
        """Perform to_payload."""
        if self._first is None or self._last is None:
            raise ValueError("equity curve must not be empty")
        return {
            "points": self._points,
            "total_return": (self._last - self._first) / self._first,
            "max_drawdown": self._max_drawdown,
        }


@dataclass(frozen=True, slots=True)
class StreamingBacktestArtifacts:
    """Final paths and row counts for streamed backtest artifacts."""

    manifest_path: Path
    artifact_paths: dict[str, Path]
    artifact_rows: dict[str, int]
    artifact_hashes: dict[str, str]


class _NdjsonArtifact:
    """_NdjsonArtifact."""

    def __init__(self, path: Path) -> None:
        """Perform __init__."""
        self.path = path
        self.rows = 0
        self._hasher = hashlib.sha256()
        self._handle = path.open("w", encoding="utf-8")

    def write(self, payload: dict[str, Any]) -> None:
        """Perform write."""
        line = (
            json.dumps(
                payload,
                default=stable_json_default,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        )
        self._handle.write(line)
        self._hasher.update(line.encode())
        self.rows += 1

    def close(self) -> None:
        """Perform close."""
        self._handle.close()

    @property
    def content_hash(self) -> str:
        """Perform content_hash."""
        return f"sha256:{self._hasher.hexdigest()}"


class StreamingBacktestArtifactWriter:
    """Write large backtest outputs as line-delimited artifacts."""

    _KINDS = ("orders", "fills", "trade_ledger", "equity_curve")

    def __init__(self, output_dir: Path) -> None:
        """Perform __init__."""
        self._output_dir = output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._artifacts = {
            kind: _NdjsonArtifact(self._output_dir / f".{kind}.partial.ndjson")
            for kind in self._KINDS
        }
        self._equity_metrics = StreamingEquityMetrics()

    def write_order(self, payload: dict[str, Any]) -> None:
        """Perform write_order."""
        self._artifacts["orders"].write(payload)

    def write_fill(self, payload: dict[str, Any]) -> None:
        """Perform write_fill."""
        self._artifacts["fills"].write(payload)

    def write_trade_ledger(self, row: TradeLedgerEntry) -> None:
        """Perform write_trade_ledger."""
        self._artifacts["trade_ledger"].write(
            {
                "order_id": row.order_id,
                "instrument_id": row.instrument_id,
                "side": row.side,
                "quantity": row.quantity,
                "fill_price": row.fill_price,
                "commission": row.commission,
                "slippage": row.slippage,
                "fill_time": row.fill_time,
                "source_bar_time": row.source_bar_time,
            }
        )

    def write_equity_point(self, point: EquityCurvePoint) -> None:
        """Perform write_equity_point."""
        self._equity_metrics.update(point.equity)
        self._artifacts["equity_curve"].write({"time": point.time, "equity": point.equity})

    def finalize(
        self,
        *,
        config_hash: str,
        dataset_metadata: tuple[dict[str, Any], ...],
        cost_model: dict[str, Any],
        processed_bars: int,
        warmup_bars: int,
        trading_bars: int,
        final_cash: Decimal,
        strategy_version: str,
    ) -> tuple[str, str, dict[str, Any], StreamingBacktestArtifacts]:
        """Perform finalize."""
        for artifact in self._artifacts.values():
            artifact.close()

        metrics = self._equity_metrics.to_payload()
        artifact_rows = {kind: artifact.rows for kind, artifact in self._artifacts.items()}
        artifact_hashes = {
            kind: artifact.content_hash for kind, artifact in self._artifacts.items()
        }
        report_hash = _stable_hash(
            {
                "config_hash": config_hash,
                "cost_model": cost_model,
                "dataset_metadata": dataset_metadata,
                "final_cash": str(final_cash),
                "processed_bars": processed_bars,
                "warmup_bars": warmup_bars,
                "trading_bars": trading_bars,
                "strategy_version": strategy_version,
                "metrics": metrics,
                "artifacts": {
                    kind: {
                        "rows": artifact_rows[kind],
                        "sha256": artifact_hashes[kind],
                    }
                    for kind in self._KINDS
                },
            }
        )
        run_id = f"bt-{report_hash.removeprefix('sha256:')[:12]}"
        artifact_paths: dict[str, Path] = {}
        for kind, artifact in self._artifacts.items():
            final_path = self._output_dir / f"{run_id}.{kind}.ndjson"
            artifact.path.replace(final_path)
            artifact_paths[kind] = final_path

        manifest_payload: dict[str, Any] = {
            "run_id": run_id,
            "config_hash": config_hash,
            "report_hash": report_hash,
            "dataset_metadata": dataset_metadata,
            "cost_model": cost_model,
            "processed_bars": processed_bars,
            "warmup_bars": warmup_bars,
            "trading_bars": trading_bars,
            "metrics": metrics,
            "artifacts": {
                kind: {
                    "path": str(artifact_paths[kind]),
                    "rows": artifact_rows[kind],
                    "sha256": artifact_hashes[kind],
                }
                for kind in self._KINDS
            },
        }
        manifest_path = self._output_dir / f"{run_id}.manifest.json"
        manifest_path.write_text(
            json.dumps(
                manifest_payload,
                default=stable_json_default,
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        return (
            run_id,
            report_hash,
            manifest_payload,
            StreamingBacktestArtifacts(
                manifest_path=manifest_path,
                artifact_paths=artifact_paths,
                artifact_rows=artifact_rows,
                artifact_hashes=artifact_hashes,
            ),
        )


__all__ = [
    "dataset_metadata_payload",
    "EquityCurvePoint",
    "StreamingBacktestArtifactWriter",
    "StreamingBacktestArtifacts",
    "StreamingEquityMetrics",
    "zero_time",
    "TradeLedgerEntry",
]
