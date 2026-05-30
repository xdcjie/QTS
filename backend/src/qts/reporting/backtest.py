"""Backtest report artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

from qts.core.hashing import stable_json_default, stable_json_hash
from qts.core.ids import RuntimeRunId
from qts.data.provenance import DatasetMetadata
from qts.reporting.base import (
    NON_BROKER_HASH_SENTINEL,
    NON_BROKER_SOURCE_COMMIT,
    PLATFORM_BASELINE_VERSION,
    RUNTIME_ARTIFACT_SCHEMA_VERSION,
    RuntimeManifest,
)
from qts.reporting.statistics import StatisticsBuilder

RUNTIME_EVENT_SCHEMA_VERSION = "1"
_REQUIRED_M1_MANIFEST_FIELDS = (
    "runtime_mode",
    "config_hash",
    "topology_hash",
    "event_schema_version",
    "artifact_schema_version",
    "risk_config_hash",
)
_REQUIRED_M1_DATASET_FIELDS = (
    "dataset_id",
    "file_hash",
    "row_count",
    "first_ts",
    "last_ts",
    "timezone",
    "adjustment_mode",
)
_REQUIRED_M1_EXECUTION_FIELDS = (
    "fill_model_name",
    "fill_model_version",
    "slippage_model",
    "commission_model",
    "partial_fill_policy",
    "broker_capability_model",
)


def is_broker_capability_reject(exc: ValueError) -> bool:
    """Return whether a broker rejection came from the capability model."""
    return "not supported by broker capabilities" in str(exc)


def broker_capability_payload(execution_adapter: object) -> dict[str, object]:
    """Return broker capability evidence for a runtime rejection event."""
    payload = getattr(execution_adapter, "broker_capability_payload", None)
    if payload is None:
        return {}
    return cast(dict[str, object], payload())


def dataset_metadata_payload(item: DatasetMetadata) -> dict[str, str | int | None]:
    """Serialize one dataset provenance row for reporting."""
    return {
        "dataset_id": item.dataset_id,
        "source": item.source,
        "instrument_id": item.instrument_id.value,
        "timeframe": item.timeframe,
        "timezone_policy": item.timezone_policy,
        "timezone": item.timezone_policy,
        "adjustment_policy": item.adjustment_policy,
        "adjustment_mode": item.adjustment_policy,
        "normalization_version": item.normalization_version,
        "created_at": item.created_at.isoformat(),
        "content_hash": item.content_hash,
        "file_hash": item.content_hash,
        "row_count": item.row_count,
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


class StreamingEquityMetrics:
    """Incremental metrics for a streamed equity curve."""

    def __init__(self) -> None:
        """Initialize empty streaming equity metrics state."""
        self._points = 0
        self._first: Decimal | None = None
        self._last: Decimal | None = None
        self._peak: Decimal | None = None
        self._max_drawdown = Decimal("0")

    def update(self, equity: Decimal) -> None:
        """Fold one equity observation into running peak and max-drawdown."""
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
        """Return point count, total return, and max drawdown as a payload."""
        if self._first is None or self._last is None:
            raise ValueError("equity curve must not be empty")
        return {
            "points": self._points,
            "total_return": (self._last - self._first) / self._first,
            "max_drawdown": self._max_drawdown,
        }


@dataclass(frozen=True, slots=True)
class BacktestArtifacts:
    """Final paths and row counts for streamed backtest artifacts."""

    manifest_path: Path
    artifact_paths: dict[str, Path]
    artifact_rows: dict[str, int]
    artifact_hashes: dict[str, str]


class _NdjsonArtifact:
    """_NdjsonArtifact."""

    def __init__(self, path: Path) -> None:
        """Open an NDJSON artifact file at ``path`` for hashed writing."""
        self.path = path
        self.rows = 0
        self._hasher = hashlib.sha256()
        self._handle = path.open("w", encoding="utf-8")

    def write(self, payload: dict[str, Any]) -> None:
        """Append one JSON line, updating the row count and content hash."""
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
        """Close the underlying file handle."""
        self._handle.close()

    @property
    def content_hash(self) -> str:
        """Return the sha256 content hash of all written lines."""
        return f"sha256:{self._hasher.hexdigest()}"


class BacktestArtifactWriter:
    """Write large backtest outputs as line-delimited artifacts."""

    _KINDS = ("events", "orders", "fills", "trade_ledger", "equity_curve", "statistics")
    _COMPACT_EXCLUDED_KINDS = frozenset({"runtime.market_data", "runtime.account_snapshot"})

    def __init__(
        self,
        output_dir: Path,
        *,
        run_id: RuntimeRunId | None = None,
        compact_events: bool = False,
    ) -> None:
        """Create a writer for partitioned backtest artifacts.

        ``compact_events`` opt-in suppresses per-bar event kinds
        (``runtime.market_data`` + ``runtime.account_snapshot``) from
        the events artifact. The equity curve and holdings snapshot
        artifacts already capture per-bar account state, so for a
        long-running backtest this drops 30x+ from events.ndjson.
        All other event kinds (trading lifecycle, kill switch,
        snapshot, position_closed) are always persisted.
        """
        self._output_dir = output_dir
        self._run_id = run_id
        self._compact_events = compact_events
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._artifacts = {
            kind: _NdjsonArtifact(self._output_dir / f".{kind}.partial.ndjson")
            for kind in self._KINDS
        }
        self._equity_metrics = StreamingEquityMetrics()
        self._statistics = StatisticsBuilder()

    def write_order(self, payload: dict[str, Any]) -> None:
        """Append one order payload to the orders artifact."""
        self._artifacts["orders"].write(payload)

    def write_runtime_event(self, payload: dict[str, Any]) -> None:
        """Write one normalized runtime event envelope."""
        if self._compact_events and payload.get("kind") in self._COMPACT_EXCLUDED_KINDS:
            return
        self._artifacts["events"].write(payload)

    def write_event(self, payload: dict[str, Any]) -> None:
        """Write one normalized runtime event through the artifact contract."""
        self.write_runtime_event(dict(payload))

    def write_snapshot(self, payload: dict[str, Any]) -> None:
        """Write one runtime snapshot evidence row through the event artifact."""
        self.write_runtime_event({"kind": "runtime.snapshot", "payload": dict(payload)})

    def write_position_closed(self, payload: dict[str, Any]) -> None:
        """Route an ``account.position_closed`` event payload into statistics.

        ``HoldingBook`` is the single source of trade-level realized PnL;
        this method translates one event payload into a
        ``StatisticsBuilder.on_position_close`` call so the builder no
        longer maintains a parallel fill aggregator.
        """
        instrument_id = str(payload["instrument_id"])
        realized_pnl = Decimal(str(payload["realized_pnl"]))
        opened_at = payload.get("opened_at")
        closed_at = payload.get("closed_at")
        holding_bars = self._holding_bars_from_payload(opened_at, closed_at)
        self._statistics.on_position_close(
            realized_pnl=realized_pnl,
            holding_bars=holding_bars,
            instrument_id=instrument_id,
        )

    def _holding_bars_from_payload(self, opened_at: object, closed_at: object) -> int:
        """Compute the holding period in bars from event timestamps.

        Falls back to ``0`` when the event lacks an open timestamp (e.g. a
        position opened before the artifact writer started). The conversion
        uses a one-minute baseline; downstream callers can override via a
        future ``bar_duration_seconds`` configuration.
        """
        if not isinstance(opened_at, str) or not isinstance(closed_at, str):
            return 0
        try:
            opened = datetime.fromisoformat(opened_at)
            closed = datetime.fromisoformat(closed_at)
        except ValueError:
            return 0
        seconds = (closed - opened).total_seconds()
        return max(int(seconds // 60), 0)

    def write_manifest(self, manifest: RuntimeManifest | dict[str, Any]) -> Path:
        """Write a shared manifest payload for contract-level callers."""
        payload = manifest.to_payload() if isinstance(manifest, RuntimeManifest) else dict(manifest)
        payload.setdefault("manifest_hash", RuntimeManifest.hash_payload(payload))
        RuntimeManifest.from_payload(payload)
        manifest_path = self._output_dir / f"{payload['run_id']}.manifest.json"
        manifest_path.write_text(
            json.dumps(payload, default=stable_json_default, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return manifest_path

    def write_fill(self, payload: dict[str, Any]) -> None:
        """Append one fill payload to the fills artifact."""
        self._artifacts["fills"].write(payload)

    def write_trade_ledger(self, row: TradeLedgerEntry) -> None:
        """Record one ledger row in statistics and the trade-ledger artifact."""
        payload = {
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
        self._statistics.on_fill(
            order_id=row.order_id,
            instrument_id=row.instrument_id,
            side=row.side,
            quantity=row.quantity,
            price=row.fill_price,
            commission=row.commission,
            slippage=row.slippage,
            fill_time=row.fill_time,
        )
        self._artifacts["trade_ledger"].write(payload)

    def write_equity_point(self, point: EquityCurvePoint) -> None:
        """Fold one equity point into metrics, statistics, and the artifact."""
        self._equity_metrics.update(point.equity)
        self._statistics.on_equity_point(time=point.time, equity=point.equity)
        self._artifacts["equity_curve"].write({"time": point.time, "equity": point.equity})

    def write_holdings_snapshot(
        self,
        *,
        gross_notional: Decimal,
        net_notional: Decimal,
    ) -> None:
        """Record one per-bar holdings notional snapshot.

        Feeds the statistics builder so ``avg_gross_exposure`` and
        ``avg_net_exposure`` appear in the finalized payload.
        """
        self._statistics.on_holdings_snapshot(
            gross_notional=gross_notional,
            net_notional=net_notional,
        )

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
        runtime_topology_payload: dict[str, Any] | None = None,
        brokerage_model: str | None = None,
        execution_assumptions: dict[str, Any] | None = None,
        risk_config_hash: str | None = None,
    ) -> tuple[str, str, dict[str, Any], BacktestArtifacts]:
        """Close artifacts, write the manifest, and return run id, hash, and paths."""
        finalized_at = datetime.now(UTC)
        statistics_payload = self._statistics.finalize(
            trading_bars=trading_bars,
        ).to_payload()
        self._artifacts["statistics"].write(statistics_payload)
        for artifact in self._artifacts.values():
            artifact.close()

        metrics = self._equity_metrics.to_payload()
        metrics.update(statistics_payload)
        normalized_dataset_metadata = tuple(
            _normalize_dataset_metadata_payload(item) for item in dataset_metadata
        )
        normalized_execution_assumptions = _normalize_execution_assumptions_payload(
            execution_assumptions
        )
        artifact_rows = {kind: artifact.rows for kind, artifact in self._artifacts.items()}
        artifact_hashes = {
            kind: artifact.content_hash for kind, artifact in self._artifacts.items()
        }
        report_payload: dict[str, Any] = {
            "config_hash": config_hash,
            "cost_model": cost_model,
            "dataset_metadata": normalized_dataset_metadata,
            "final_cash": str(final_cash),
            "processed_bars": processed_bars,
            "warmup_bars": warmup_bars,
            "trading_bars": trading_bars,
            "strategy_version": strategy_version,
            "brokerage_model": brokerage_model,
            "execution_assumptions": normalized_execution_assumptions,
            "risk_config_hash": risk_config_hash,
            "metrics": metrics,
            "statistics": statistics_payload,
            "artifacts": {
                kind: {
                    "rows": artifact_rows[kind],
                    "sha256": artifact_hashes[kind],
                }
                for kind in self._KINDS
            },
        }
        report_payload["statistics_hash"] = stable_json_hash(statistics_payload)
        if runtime_topology_payload is not None:
            report_payload["runtime_topology"] = runtime_topology_payload
        report_hash = stable_json_hash(report_payload)
        run_id = (
            self._run_id.value
            if self._run_id is not None
            else f"bt-{report_hash.removeprefix('sha256:')[:12]}"
        )
        artifact_paths: dict[str, Path] = {}
        for kind, artifact in self._artifacts.items():
            final_path = self._output_dir / f"{run_id}.{kind}.ndjson"
            artifact.path.replace(final_path)
            artifact_paths[kind] = final_path

        manifest_payload: dict[str, Any] = {
            "run_id": run_id,
            "runtime_instance_id": run_id,
            "runtime_mode": "backtest",
            "market_data_environment": "historical_replay",
            "execution_environment": "simulated",
            "account_environment": "simulated",
            "order_submission_permission": False,
            "event_schema_version": RUNTIME_EVENT_SCHEMA_VERSION,
            "artifact_schema_version": RUNTIME_ARTIFACT_SCHEMA_VERSION,
            "config_hash": config_hash,
            "topology_hash": (
                str(runtime_topology_payload["topology_hash"])
                if runtime_topology_payload is not None
                and runtime_topology_payload.get("topology_hash") is not None
                else None
            ),
            "startup_checklist_hash": NON_BROKER_HASH_SENTINEL,
            "platform_baseline_version": PLATFORM_BASELINE_VERSION,
            "created_at": finalized_at.isoformat(),
            "finalized_at": finalized_at.isoformat(),
            "source_commit": NON_BROKER_SOURCE_COMMIT,
            "operator_identity_hash": NON_BROKER_HASH_SENTINEL,
            "report_hash": report_hash,
            "dataset_metadata": normalized_dataset_metadata,
            "cost_model": cost_model,
            "processed_bars": processed_bars,
            "warmup_bars": warmup_bars,
            "trading_bars": trading_bars,
            "brokerage_model": brokerage_model,
            "execution_assumptions": normalized_execution_assumptions,
            "risk_config_hash": risk_config_hash,
            "metrics": metrics,
            "statistics": statistics_payload,
            "statistics_hash": report_payload["statistics_hash"],
            "artifacts": {
                kind: {
                    "path": str(artifact_paths[kind]),
                    "rows": artifact_rows[kind],
                    "sha256": artifact_hashes[kind],
                }
                for kind in self._KINDS
            },
        }
        if runtime_topology_payload is not None:
            manifest_payload["runtime_topology"] = runtime_topology_payload
        _validate_m1_backtest_manifest(manifest_payload)
        manifest_payload["manifest_hash"] = RuntimeManifest.hash_payload(manifest_payload)
        RuntimeManifest.from_payload(manifest_payload)
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
            BacktestArtifacts(
                manifest_path=manifest_path,
                artifact_paths=artifact_paths,
                artifact_rows=artifact_rows,
                artifact_hashes=artifact_hashes,
            ),
        )


class BacktestReportWriter(BacktestArtifactWriter):
    """Backtest report writer for partitioned artifacts."""


def _normalize_dataset_metadata_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    if "file_hash" not in normalized and "content_hash" in normalized:
        normalized["file_hash"] = normalized["content_hash"]
    if "timezone" not in normalized and "timezone_policy" in normalized:
        normalized["timezone"] = normalized["timezone_policy"]
    if "adjustment_mode" not in normalized and "adjustment_policy" in normalized:
        normalized["adjustment_mode"] = normalized["adjustment_policy"]
    return normalized


def _normalize_execution_assumptions_payload(
    payload: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if payload is None:
        return None
    normalized = dict(payload)
    if "slippage_model" not in normalized and "slippage_model_name" in normalized:
        normalized["slippage_model"] = normalized.pop("slippage_model_name")
    if "commission_model" not in normalized and "commission_model_name" in normalized:
        normalized["commission_model"] = normalized.pop("commission_model_name")
    return normalized


def _validate_m1_backtest_manifest(payload: dict[str, Any]) -> None:
    for key in _REQUIRED_M1_MANIFEST_FIELDS:
        _require_manifest_value(payload, key)

    dataset_metadata = payload.get("dataset_metadata")
    if not isinstance(dataset_metadata, tuple) or not dataset_metadata:
        raise ValueError("missing required backtest manifest field: dataset_metadata")
    for index, dataset in enumerate(dataset_metadata):
        if not isinstance(dataset, dict):
            raise ValueError(f"missing required backtest manifest field: dataset_metadata[{index}]")
        for key in _REQUIRED_M1_DATASET_FIELDS:
            _require_manifest_value(dataset, key, label=f"dataset_metadata[{index}].{key}")

    execution_assumptions = payload.get("execution_assumptions")
    if not isinstance(execution_assumptions, dict):
        raise ValueError("missing required backtest manifest field: execution_assumptions")
    for key in _REQUIRED_M1_EXECUTION_FIELDS:
        _require_manifest_value(execution_assumptions, key, label=f"execution_assumptions.{key}")


def _require_manifest_value(payload: dict[str, Any], key: str, *, label: str | None = None) -> None:
    value: Any = payload
    for part in key.split("."):
        if not isinstance(value, dict) or part not in value:
            raise ValueError(f"missing required backtest manifest field: {label or key}")
        value = value[part]
    if value is None or value == "":
        raise ValueError(f"missing required backtest manifest field: {label or key}")


__all__ = [
    "BacktestArtifactWriter",
    "BacktestArtifacts",
    "BacktestReportWriter",
    "EquityCurvePoint",
    "StreamingEquityMetrics",
    "TradeLedgerEntry",
    "dataset_metadata_payload",
    "zero_time",
]
