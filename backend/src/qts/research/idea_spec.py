"""Research idea schema and controlled edge taxonomy."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from qts.core.time import require_aware_datetime

ALLOWED_EDGE_TYPES = frozenset(
    {
        "carry",
        "cross_sectional_momentum",
        "event_driven",
        "execution_alpha",
        "liquidity",
        "macro",
        "macro_regime",
        "mean_reversion",
        "microstructure",
        "momentum",
        "quality",
        "relative_value",
        "reversal",
        "seasonality",
        "sentiment",
        "term_structure",
        "time_series_momentum",
        "value",
        "volatility",
    }
)

ALLOWED_IDEA_STATUSES = frozenset(
    {
        "accepted",
        "draft",
        "factor_candidate",
        "frozen_forward",
        "idea",
        "needs_work",
        "paper_candidate",
        "promotion_review",
        "rejected",
        "retired",
        "strategy_prototype",
        "validated_research",
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
    data_required: tuple[str, ...] = ()
    kill_criteria: tuple[str, ...] = ()
    trial_budget: Mapping[str, int] | None = None
    status: str = "draft"
    trial_count: int = 0
    rejection_reason: str | None = None
    edge_types: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        idea_id = self.idea_id.strip()
        title = self.title.strip()
        hypothesis = self.hypothesis.strip()
        edge_types = self._edge_types()
        edge_type = edge_types[0]
        source = self.source.strip().lower()
        data_required = self._string_tuple(self.data_required, field_name="data_required")
        kill_criteria = self._string_tuple(self.kill_criteria, field_name="kill_criteria")
        trial_budget = self._int_mapping(self.trial_budget or {}, field_name="trial_budget")
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
        unknown_edge_types = sorted(edge for edge in edge_types if edge not in ALLOWED_EDGE_TYPES)
        if unknown_edge_types:
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
        object.__setattr__(self, "edge_types", edge_types)
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "data_required", data_required)
        object.__setattr__(self, "kill_criteria", kill_criteria)
        object.__setattr__(self, "trial_budget", trial_budget)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "rejection_reason", rejection_reason)

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> IdeaSpec:
        """Rehydrate an idea spec from YAML/JSON payload data."""

        created_at = datetime.fromisoformat(cls._required_text(payload, "created_at"))
        raw_edge_types = cls._string_tuple(payload.get("edge_types"), field_name="edge_types")
        if not raw_edge_types:
            raise ValueError("edge_types is required")
        return cls(
            idea_id=cls._required_text(payload, "idea_id"),
            title=cls._required_text(payload, "title"),
            hypothesis=cls._required_text(payload, "hypothesis"),
            edge_type=raw_edge_types[0],
            source=cls._required_text(payload, "source"),
            created_at=created_at,
            data_required=cls._string_tuple(
                payload.get("data_required", ()), field_name="data_required"
            ),
            kill_criteria=cls._string_tuple(
                payload.get("kill_criteria", ()), field_name="kill_criteria"
            ),
            trial_budget=cls._int_mapping(
                payload.get("trial_budget", {}),
                field_name="trial_budget",
            ),
            status=str(payload.get("status", "draft")),
            trial_count=int(payload.get("trial_count", 0)),
            rejection_reason=cls._optional_text(payload.get("rejection_reason")),
            edge_types=raw_edge_types,
        )

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic YAML/JSON-ready payload."""

        return {
            "created_at": self.created_at.isoformat(),
            "data_required": list(self.data_required),
            "edge_type": self.edge_type,
            "edge_types": list(self.edge_types),
            "hypothesis": self.hypothesis,
            "idea_id": self.idea_id,
            "kill_criteria": list(self.kill_criteria),
            "rejection_reason": self.rejection_reason,
            "source": self.source,
            "status": self.status,
            "title": self.title,
            "trial_budget": dict(self.trial_budget or {}),
            "trial_count": self.trial_count,
        }

    @staticmethod
    def _required_text(payload: Mapping[str, Any], field_name: str) -> str:
        value = payload.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} is required")
        return value

    def _edge_types(self) -> tuple[str, ...]:
        raw_edge_types = self.edge_types or (self.edge_type,)
        normalized: list[str] = []
        seen: set[str] = set()
        for raw_edge_type in raw_edge_types:
            edge_type = str(raw_edge_type).strip().lower()
            if not edge_type:
                raise ValueError("edge_type is required")
            if edge_type in seen:
                continue
            seen.add(edge_type)
            normalized.append(edge_type)
        return tuple(normalized)

    @staticmethod
    def _optional_text(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _string_tuple(value: Any, *, field_name: str) -> tuple[str, ...]:
        if value is None:
            return ()
        if not isinstance(value, Sequence) or isinstance(value, str):
            raise ValueError(f"{field_name} must be a string sequence")
        result: list[str] = []
        for item in value:
            if not isinstance(item, str) or not item.strip():
                raise ValueError(f"{field_name} must be a string sequence")
            result.append(item.strip())
        return tuple(result)

    @staticmethod
    def _int_mapping(value: Any, *, field_name: str) -> dict[str, int]:
        if value is None:
            return {}
        if not isinstance(value, Mapping):
            raise ValueError(f"{field_name} must be an integer mapping")
        result: dict[str, int] = {}
        for key, item in value.items():
            key_text = str(key).strip()
            if not key_text:
                raise ValueError(f"{field_name} keys must not be empty")
            item_int = int(item)
            if item_int < 0:
                raise ValueError(f"{field_name}.{key_text} must be non-negative")
            result[key_text] = item_int
        return result


__all__ = ["ALLOWED_EDGE_TYPES", "ALLOWED_IDEA_STATUSES", "IdeaSpec"]
