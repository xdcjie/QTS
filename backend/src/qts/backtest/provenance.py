"""Backtest dataset manifest + market-data provenance serialization.

Owns turning a run's dataset metadata (or inline bars) into the manifest's
dataset-provenance rows and per-bar market-data provenance payloads, so the
engine does not own dataset/provenance serialization.
"""

from __future__ import annotations

from typing import Any

from qts.core.hashing import stable_json_hash
from qts.data.provenance import DatasetMetadata
from qts.domain.market_data import Bar
from qts.reporting.backtest import dataset_metadata_payload, zero_time


class BacktestDatasetManifestBuilder:
    """Build dataset manifest rows and market-data provenance for a backtest run."""

    def __init__(
        self,
        *,
        dataset_metadata: tuple[DatasetMetadata, ...],
        registry_bars: tuple[Bar, ...],
        config_hash_payload: dict[str, Any],
        target_timeframe: str | None,
    ) -> None:
        self._dataset_metadata = dataset_metadata
        self._registry_bars = registry_bars
        self._config_hash_payload = config_hash_payload
        self._target_timeframe = target_timeframe

    def manifest_dataset_metadata_payloads(self) -> tuple[dict[str, Any], ...]:
        """Return dataset provenance rows with the M1 manifest aliases."""
        first_ts, last_ts = self._dataset_time_bounds()
        if self._dataset_metadata:
            return tuple(
                self._enrich(dataset_metadata_payload(item), first_ts=first_ts, last_ts=last_ts)
                for item in self._dataset_metadata
            )
        return (self._inline_payload(first_ts=first_ts, last_ts=last_ts),)

    def market_data_provenance_for(self, bar: Bar) -> dict[str, str | int | None]:
        """Return replay provenance for a market-data runtime event."""
        candidates = [
            metadata for metadata in self._dataset_metadata if metadata.timeframe == bar.timeframe
        ]
        for metadata in candidates:
            if metadata.instrument_id == bar.instrument_id and metadata.timeframe == bar.timeframe:
                return self._provenance_payload(metadata)
        if len(candidates) == 1:
            return self._provenance_payload(candidates[0])
        return {}

    def _dataset_time_bounds(self) -> tuple[str | None, str | None]:
        start = self._config_hash_payload.get("start")
        end = self._config_hash_payload.get("end")
        if isinstance(start, str) and isinstance(end, str):
            return start, end
        if self._registry_bars:
            return (
                min(bar.start_time for bar in self._registry_bars).isoformat(),
                max(bar.end_time for bar in self._registry_bars).isoformat(),
            )
        return None, None

    @staticmethod
    def _enrich(
        payload: dict[str, Any], *, first_ts: str | None, last_ts: str | None
    ) -> dict[str, Any]:
        enriched = dict(payload)
        if first_ts is not None:
            enriched.setdefault("first_ts", first_ts)
        if last_ts is not None:
            enriched.setdefault("last_ts", last_ts)
        return enriched

    def _inline_payload(self, *, first_ts: str | None, last_ts: str | None) -> dict[str, Any]:
        source_payload = [
            {
                "instrument_id": bar.instrument_id.value,
                "timeframe": bar.timeframe,
                "start_time": bar.start_time.isoformat(),
                "end_time": bar.end_time.isoformat(),
                "open": str(bar.open),
                "high": str(bar.high),
                "low": str(bar.low),
                "close": str(bar.close),
                "volume": str(bar.volume) if bar.volume is not None else None,
            }
            for bar in self._registry_bars
        ]
        file_hash = stable_json_hash(source_payload)
        return {
            "dataset_id": "inline-bars",
            "source": "inline",
            "instrument_id": "MULTI",
            "timeframe": self._target_timeframe or "source",
            "timezone": "UTC",
            "timezone_policy": "UTC",
            "adjustment_mode": "none",
            "adjustment_policy": "none",
            "normalization_version": "inline-bars-v1",
            "created_at": first_ts or zero_time().isoformat(),
            "content_hash": file_hash,
            "file_hash": file_hash,
            "row_count": len(self._registry_bars),
            "first_ts": first_ts or zero_time().isoformat(),
            "last_ts": last_ts or zero_time().isoformat(),
        }

    @staticmethod
    def _provenance_payload(metadata: DatasetMetadata) -> dict[str, str | int | None]:
        return {
            "source_id": metadata.source,
            "dataset_id": metadata.dataset_id,
            "provider": metadata.source,
            "permission_state": None,
            "adjustment_mode": metadata.adjustment_policy,
            "content_hash": metadata.content_hash,
            "row_count": metadata.row_count,
        }


__all__ = ["BacktestDatasetManifestBuilder"]
