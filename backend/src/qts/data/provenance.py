"""Historical dataset identity and provenance models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from qts.core.ids import InstrumentId
from qts.core.time import require_aware_datetime


class ReplayDataAnomalyType(StrEnum):
    """Replay data quality events emitted by historical sources."""

    GAP_DETECTED = "replay_gap_detected"
    OUT_OF_ORDER_REJECTED = "replay_out_of_order_rejected"
    DUPLICATE_DROPPED = "replay_duplicate_dropped"
    SESSION_FILTERED = "replay_session_filtered"
    DATA_SCHEMA_ERROR = "replay_data_schema_error"


@dataclass(frozen=True, slots=True)
class ReplayDataAnomalyEvent:
    """Replay source diagnostic event for deterministic data-quality handling."""

    anomaly_type: ReplayDataAnomalyType
    source_id: str
    instrument_id: InstrumentId
    timeframe: str
    bar_start: datetime
    bar_end: datetime
    observed_at: datetime
    previous_end: datetime | None = None
    reason: str | None = None

    def __post_init__(self) -> None:
        """Validate replay data anomaly event fields."""
        if not self.source_id.strip():
            raise ValueError("source_id must not be empty")
        if not self.timeframe.strip():
            raise ValueError("timeframe must not be empty")
        require_aware_datetime(self.bar_start, name="bar_start")
        require_aware_datetime(self.bar_end, name="bar_end")
        require_aware_datetime(self.observed_at, name="observed_at")
        if self.previous_end is not None:
            require_aware_datetime(self.previous_end, name="previous_end")
        if self.bar_start >= self.bar_end:
            raise ValueError("bar_start must be before bar_end")
        if self.reason is not None and not self.reason.strip():
            raise ValueError("reason must not be empty")


@dataclass(frozen=True, slots=True)
class DatasetMetadata:
    """Stable reference to historical data used by simulation or research."""

    dataset_id: str
    source: str
    instrument_id: InstrumentId
    timeframe: str
    timezone_policy: str
    adjustment_policy: str
    normalization_version: str
    created_at: datetime
    content_hash: str | None = None
    row_count: int | None = None

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        self._require_text(self.dataset_id, "dataset_id")
        self._require_text(self.source, "source")
        self._require_text(self.timeframe, "timeframe")
        self._require_text(self.timezone_policy, "timezone_policy")
        self._require_text(self.adjustment_policy, "adjustment_policy")
        self._require_text(self.normalization_version, "normalization_version")
        require_aware_datetime(self.created_at, name="created_at")
        if self.content_hash is not None:
            self._require_text(self.content_hash, "content_hash")
        if self.row_count is not None and self.row_count < 0:
            raise ValueError("row_count must be non-negative")

    @property
    def reference(self) -> str:
        """Perform reference."""
        suffix = self.content_hash if self.content_hash is not None else "unhashed"
        return f"{self.source}:{self.dataset_id}:{suffix}"

    @staticmethod
    def _require_text(value: str, name: str) -> None:
        """Perform _require_text."""
        if not value.strip():
            raise ValueError(f"{name} must not be empty")


__all__ = ["DatasetMetadata", "ReplayDataAnomalyEvent", "ReplayDataAnomalyType"]
