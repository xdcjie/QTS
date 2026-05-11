"""Backtest report artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from qts.core.ids import BacktestRunId


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


@dataclass(frozen=True, slots=True)
class BacktestReport:
    """Stable backtest report containing inputs, outputs, metrics, and hashes."""

    run_id: BacktestRunId
    config_hash: str
    dataset_metadata: tuple[Any, ...]
    cost_model: dict[str, Any]
    processed_bars: int
    warmup_bars: int
    trading_bars: int
    orders: tuple[dict[str, Any], ...]
    fills: tuple[dict[str, Any], ...]
    trade_ledger: tuple[TradeLedgerEntry, ...]
    equity_curve: tuple[EquityCurvePoint, ...]
    metrics: dict[str, Any]
    report_hash: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "report_hash",
            self._stable_hash(self._payload(include_hash=False)),
        )

    def to_json(self) -> str:
        return json.dumps(
            self._payload(include_hash=True),
            default=self._json_default,
            sort_keys=True,
            separators=(",", ":"),
        )

    def to_dict(self) -> dict[str, Any]:
        return self._payload(include_hash=True)

    def _payload(self, *, include_hash: bool) -> dict[str, Any]:
        payload = {
            "run_id": self.run_id.value,
            "config_hash": self.config_hash,
            "dataset_metadata": self.dataset_metadata,
            "cost_model": self.cost_model,
            "processed_bars": self.processed_bars,
            "warmup_bars": self.warmup_bars,
            "trading_bars": self.trading_bars,
            "orders": self.orders,
            "fills": self.fills,
            "trade_ledger": [
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
                for row in self.trade_ledger
            ],
            "equity_curve": [
                {"time": point.time, "equity": point.equity} for point in self.equity_curve
            ],
            "metrics": self.metrics,
        }
        if include_hash:
            payload["report_hash"] = self.report_hash
        return payload

    @classmethod
    def _stable_hash(cls, payload: Any) -> str:
        encoded = json.dumps(
            payload,
            default=cls._json_default,
            sort_keys=True,
            separators=(",", ":"),
        )
        return f"sha256:{hashlib.sha256(encoded.encode()).hexdigest()}"

    @staticmethod
    def _json_default(value: object) -> object:
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, datetime):
            return value.isoformat()
        if hasattr(value, "value") and isinstance(value.value, str):
            return value.value
        raise TypeError(f"object of type {type(value).__name__} is not JSON serializable")


class StreamingEquityMetrics:
    """Incremental metrics for a streamed equity curve."""

    def __init__(self) -> None:
        self._points = 0
        self._first: Decimal | None = None
        self._last: Decimal | None = None
        self._peak: Decimal | None = None
        self._max_drawdown = Decimal("0")

    def update(self, equity: Decimal) -> None:
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
    def __init__(self, path: Path) -> None:
        self.path = path
        self.rows = 0
        self._hasher = hashlib.sha256()
        self._handle = path.open("w", encoding="utf-8")

    def write(self, payload: dict[str, Any]) -> None:
        line = (
            json.dumps(
                payload,
                default=BacktestReport._json_default,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        )
        self._handle.write(line)
        self._hasher.update(line.encode())
        self.rows += 1

    def close(self) -> None:
        self._handle.close()

    @property
    def content_hash(self) -> str:
        return f"sha256:{self._hasher.hexdigest()}"


class StreamingBacktestArtifactWriter:
    """Write large backtest outputs as line-delimited artifacts."""

    _KINDS = ("orders", "fills", "trade_ledger", "equity_curve")

    def __init__(self, output_dir: Path) -> None:
        self._output_dir = output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._artifacts = {
            kind: _NdjsonArtifact(self._output_dir / f".{kind}.partial.ndjson")
            for kind in self._KINDS
        }
        self._equity_metrics = StreamingEquityMetrics()

    def write_order(self, payload: dict[str, Any]) -> None:
        self._artifacts["orders"].write(payload)

    def write_fill(self, payload: dict[str, Any]) -> None:
        self._artifacts["fills"].write(payload)

    def write_trade_ledger(self, row: TradeLedgerEntry) -> None:
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
        for artifact in self._artifacts.values():
            artifact.close()

        metrics = self._equity_metrics.to_payload()
        artifact_rows = {kind: artifact.rows for kind, artifact in self._artifacts.items()}
        artifact_hashes = {
            kind: artifact.content_hash for kind, artifact in self._artifacts.items()
        }
        report_hash = BacktestReport._stable_hash(
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
                default=BacktestReport._json_default,
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
    "BacktestReport",
    "EquityCurvePoint",
    "StreamingBacktestArtifactWriter",
    "StreamingBacktestArtifacts",
    "StreamingEquityMetrics",
    "TradeLedgerEntry",
]
