"""Research idea schema and controlled edge taxonomy."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from qts.core.time import require_aware_datetime

ALLOWED_EDGE_TYPES = frozenset(
    {
        "carry",
        "liquidity",
        "macro",
        "momentum",
        "quality",
        "reversal",
        "seasonality",
        "sentiment",
        "value",
        "volatility",
    }
)

ALLOWED_IDEA_STATUSES = frozenset(
    {
        "accepted",
        "draft",
        "needs_work",
        "paper_candidate",
        "promotion_review",
        "rejected",
    }
)


@dataclass(frozen=True, slots=True)
class IdeaSpec:
    """Owns one research idea and its process-governance metadata."""

    idea_id: str
    title: str
    hypothesis: str
    edge_type: str
    source: str
    created_at: datetime
    status: str = "draft"
    trial_count: int = 0
    rejection_reason: str | None = None

    def __post_init__(self) -> None:
        idea_id = self.idea_id.strip()
        title = self.title.strip()
        hypothesis = self.hypothesis.strip()
        edge_type = self.edge_type.strip().lower()
        source = self.source.strip().lower()
        status = self.status.strip()
        rejection_reason = (
            None if self.rejection_reason is None else self.rejection_reason.strip() or None
        )

        if not idea_id:
            raise ValueError("idea_id is required")
        if not title:
            raise ValueError("title is required")
        if not hypothesis:
            raise ValueError("hypothesis is required")
        if edge_type not in ALLOWED_EDGE_TYPES:
            allowed = ", ".join(sorted(ALLOWED_EDGE_TYPES))
            raise ValueError(f"edge_type must be one of: {allowed}")
        if not source:
            raise ValueError("source is required")
        require_aware_datetime(self.created_at, name="created_at")
        if status not in ALLOWED_IDEA_STATUSES:
            allowed = ", ".join(sorted(ALLOWED_IDEA_STATUSES))
            raise ValueError(f"status must be one of: {allowed}")
        if self.trial_count < 0:
            raise ValueError("trial_count must be non-negative")
        if status == "promotion_review" and not hypothesis:
            raise ValueError("hypothesis is required for promotion_review")

        object.__setattr__(self, "idea_id", idea_id)
        object.__setattr__(self, "title", title)
        object.__setattr__(self, "hypothesis", hypothesis)
        object.__setattr__(self, "edge_type", edge_type)
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "rejection_reason", rejection_reason)

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> IdeaSpec:
        """Rehydrate an idea spec from YAML/JSON payload data."""

        created_at = datetime.fromisoformat(cls._required_text(payload, "created_at"))
        return cls(
            idea_id=cls._required_text(payload, "idea_id"),
            title=cls._required_text(payload, "title"),
            hypothesis=cls._required_text(payload, "hypothesis"),
            edge_type=cls._required_text(payload, "edge_type"),
            source=cls._required_text(payload, "source"),
            created_at=created_at,
            status=str(payload.get("status", "draft")),
            trial_count=int(payload.get("trial_count", 0)),
            rejection_reason=cls._optional_text(payload.get("rejection_reason")),
        )

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic YAML/JSON-ready payload."""

        return {
            "created_at": self.created_at.isoformat(),
            "edge_type": self.edge_type,
            "hypothesis": self.hypothesis,
            "idea_id": self.idea_id,
            "rejection_reason": self.rejection_reason,
            "source": self.source,
            "status": self.status,
            "title": self.title,
            "trial_count": self.trial_count,
        }

    @staticmethod
    def _required_text(payload: Mapping[str, Any], field_name: str) -> str:
        value = payload.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} is required")
        return value

    @staticmethod
    def _optional_text(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None


__all__ = ["ALLOWED_EDGE_TYPES", "ALLOWED_IDEA_STATUSES", "IdeaSpec"]
