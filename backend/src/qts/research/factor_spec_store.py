"""Deterministic persistence for human-reviewable factor specs."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from qts.research.factor_spec import FactorSpec

_ALLOWED_REVIEW_DECISIONS = frozenset({"draft", "accepted", "rejected", "needs_work"})


@dataclass(frozen=True, slots=True)
class FactorSpecReview:
    """Persisted research evidence for one human review decision."""

    spec_name: str
    decision: str
    reviewer: str
    reviewed_at: datetime
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        spec_name = self.spec_name.strip()
        decision = _validate_review_decision(self.decision)
        reviewer = self.reviewer.strip()
        notes = self._normalized_string_tuple(self.notes)

        if not spec_name:
            raise ValueError("spec_name is required")
        if not reviewer:
            raise ValueError("reviewer is required")
        if (
            self.reviewed_at.tzinfo is None
            or self.reviewed_at.tzinfo.utcoffset(self.reviewed_at) is None
        ):
            raise ValueError("reviewed_at must be timezone-aware")

        object.__setattr__(self, "spec_name", spec_name)
        object.__setattr__(self, "decision", decision)
        object.__setattr__(self, "reviewer", reviewer)
        object.__setattr__(self, "notes", notes)

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready review evidence record."""

        return {
            "decision": self.decision,
            "notes": list(self.notes),
            "reviewed_at": self.reviewed_at.isoformat(),
            "reviewer": self.reviewer,
            "spec_name": self.spec_name,
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> FactorSpecReview:
        """Rehydrate a persisted review evidence record."""

        return cls(
            spec_name=str(payload.get("spec_name", "")),
            decision=str(payload.get("decision", "")),
            reviewer=str(payload.get("reviewer", "")),
            reviewed_at=cls._datetime_from_payload(payload.get("reviewed_at")),
            notes=cls._normalized_string_tuple(payload.get("notes", ())),
        )

    @staticmethod
    def _normalized_string_tuple(value: Sequence[Any] | Any) -> tuple[str, ...]:
        if isinstance(value, str) or not isinstance(value, Sequence):
            return ()
        return tuple(
            dict.fromkeys(normalized for item in value if (normalized := str(item).strip()))
        )

    @staticmethod
    def _datetime_from_payload(value: Any) -> datetime:
        if not isinstance(value, str):
            raise ValueError("reviewed_at must be an ISO datetime string")
        return datetime.fromisoformat(value)


class FactorSpecStore:
    """Owns deterministic storage for non-executable factor spec drafts."""

    def __init__(self, root_dir: Path) -> None:
        self._store_root = root_dir
        self._root_dir = root_dir / "factor-specs"

    @property
    def reviews_path(self) -> Path:
        """Return the JSONL path for persisted review evidence."""

        return self._store_root / "factor-spec-reviews.jsonl"

    def path_for(self, name: str) -> Path:
        """Return the JSON path for a raw spec name."""

        normalized = name.strip()
        if (
            not normalized
            or "/" in normalized
            or "\\" in normalized
            or ".." in normalized
            or normalized.endswith(".json")
        ):
            raise ValueError("factor spec name must be a plain name without .json suffix")
        return self._root_dir / f"{normalized}.json"

    def save(self, spec: FactorSpec) -> Path:
        """Persist a spec as deterministic JSON and return its path."""

        path = self.path_for(spec.name)
        path.parent.mkdir(parents=True, exist_ok=True)
        content = json.dumps(spec.to_payload(), sort_keys=True, indent=2) + "\n"
        path.write_text(content, encoding="utf-8")
        return path

    def load(self, name: str) -> FactorSpec:
        """Load one persisted spec by raw spec name."""

        payload = json.loads(self.path_for(name).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("factor spec payload must be a JSON object")
        return FactorSpec.from_payload(self._string_key_mapping(payload))

    def list_specs(self) -> tuple[FactorSpec, ...]:
        """Return all persisted specs sorted lexicographically by filename."""

        return tuple(self.load(path.stem) for path in sorted(self._root_dir.glob("*.json")))

    def record_review(
        self,
        name: str,
        *,
        decision: str,
        reviewer: str,
        notes: Sequence[str] = (),
        reviewed_at: datetime | None = None,
    ) -> FactorSpecReview:
        """Persist one review decision and update the spec's research status."""

        spec = self.load(name)
        review = FactorSpecReview(
            spec_name=spec.name,
            decision=decision,
            reviewer=reviewer,
            reviewed_at=reviewed_at or datetime.now(UTC),
            notes=tuple(notes),
        )
        self.save(replace(spec, review_status=review.decision))
        self._append_review(review)
        return review

    def list_reviews(self, *, decision: str | None = None) -> tuple[FactorSpecReview, ...]:
        """Return persisted review decisions newest-first."""

        normalized_decision = None if decision is None else _validate_review_decision(decision)
        reviews = self._load_reviews()
        if normalized_decision is not None:
            reviews = tuple(review for review in reviews if review.decision == normalized_decision)
        return tuple(
            sorted(
                reviews,
                key=lambda review: (-review.reviewed_at.timestamp(), review.spec_name),
            )
        )

    def list_specs_by_status(self, status: str) -> tuple[FactorSpec, ...]:
        """Return persisted specs whose research review status matches status."""

        normalized_status = _validate_review_decision(status)
        return tuple(
            spec
            for spec in sorted(self.list_specs(), key=lambda item: item.name)
            if spec.review_status == normalized_status
        )

    def _append_review(self, review: FactorSpecReview) -> None:
        self.reviews_path.parent.mkdir(parents=True, exist_ok=True)
        content = json.dumps(review.to_payload(), sort_keys=True) + "\n"
        with self.reviews_path.open("a", encoding="utf-8") as review_file:
            review_file.write(content)

    def _load_reviews(self) -> tuple[FactorSpecReview, ...]:
        if not self.reviews_path.exists():
            return ()
        reviews: list[FactorSpecReview] = []
        for line in self.reviews_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError("factor spec review payload must be a JSON object")
            reviews.append(FactorSpecReview.from_payload(self._string_key_mapping(payload)))
        return tuple(reviews)

    @staticmethod
    def _string_key_mapping(payload: dict[Any, Any]) -> dict[str, Any]:
        return {str(key): value for key, value in payload.items()}


def _validate_review_decision(decision: str) -> str:
    normalized = decision.strip()
    if normalized not in _ALLOWED_REVIEW_DECISIONS:
        allowed = ", ".join(sorted(_ALLOWED_REVIEW_DECISIONS))
        raise ValueError(f"review decision must be one of: {allowed}")
    return normalized
