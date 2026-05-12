"""Historical dataset identity and provenance models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from qts.core.ids import InstrumentId
from qts.core.time import require_aware_datetime


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


__all__ = ["DatasetMetadata"]
