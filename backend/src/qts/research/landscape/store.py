"""Persistent fitness landscape for autonomous research trials."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from qts.core.hashing import stable_json_dumps, stable_json_hash


@dataclass(frozen=True, slots=True)
class FitnessLandscapePoint:
    """One immutable trial point in the autonomous research fitness landscape."""

    trial_id: str
    retry_id: str | None
    campaign_id: str
    generation_id: str
    strategy_family: str
    factor_family: str
    universe: tuple[str, ...]
    root: str
    timeframe: str
    regime: str
    session: str
    parameter_hash: str
    metrics: Mapping[str, Any]
    constraints: Mapping[str, Any]
    accepted: bool
    rejected_reasons: tuple[str, ...]
    evidence_bundle_id: str | None
    promotion_packet_id: str | None
    artifact_graph_hash: str | None
    lifecycle_status: str = "selected"
    rejection_stage: str | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "trial_id",
            "campaign_id",
            "generation_id",
            "strategy_family",
            "factor_family",
            "root",
            "timeframe",
            "regime",
            "session",
            "parameter_hash",
            "lifecycle_status",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} is required")
        if self.retry_id is not None and not self.retry_id.strip():
            raise ValueError("retry_id must be non-empty when provided")
        if self.evidence_bundle_id is not None and not self.evidence_bundle_id.strip():
            raise ValueError("evidence_bundle_id must be non-empty when provided")
        if self.artifact_graph_hash is not None and not self.artifact_graph_hash.strip():
            raise ValueError("artifact_graph_hash must be non-empty when provided")
        if self.rejection_stage is not None and not self.rejection_stage.strip():
            raise ValueError("rejection_stage must be non-empty when provided")
        if not self.universe:
            raise ValueError("universe must not be empty")
        object.__setattr__(self, "universe", tuple(str(item) for item in self.universe))
        object.__setattr__(
            self,
            "metrics",
            self._json_object(self.metrics, "metrics"),
        )
        object.__setattr__(
            self,
            "constraints",
            self._json_object(self.constraints, "constraints"),
        )
        object.__setattr__(
            self,
            "rejected_reasons",
            tuple(str(reason) for reason in self.rejected_reasons),
        )

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> FitnessLandscapePoint:
        """Restore a fitness point from a persisted JSON object."""

        universe = payload.get("universe")
        rejected_reasons = payload.get("rejected_reasons", ())
        if not isinstance(universe, list):
            raise ValueError("universe must be a list")
        if not isinstance(rejected_reasons, list):
            raise ValueError("rejected_reasons must be a list")
        metrics = payload.get("metrics")
        constraints = payload.get("constraints")
        if not isinstance(metrics, Mapping):
            raise ValueError("metrics must be a JSON object")
        if not isinstance(constraints, Mapping):
            raise ValueError("constraints must be a JSON object")
        return cls(
            trial_id=cls._required_text(payload, "trial_id"),
            retry_id=cls._optional_text(payload, "retry_id"),
            campaign_id=cls._required_text(payload, "campaign_id"),
            generation_id=cls._required_text(payload, "generation_id"),
            strategy_family=cls._required_text(payload, "strategy_family"),
            factor_family=cls._required_text(payload, "factor_family"),
            universe=tuple(str(item) for item in universe),
            root=cls._required_text(payload, "root"),
            timeframe=cls._required_text(payload, "timeframe"),
            regime=cls._required_text(payload, "regime"),
            session=cls._required_text(payload, "session"),
            parameter_hash=cls._required_text(payload, "parameter_hash"),
            metrics=metrics,
            constraints=constraints,
            accepted=bool(payload.get("accepted")),
            rejected_reasons=tuple(str(reason) for reason in rejected_reasons),
            evidence_bundle_id=cls._optional_text(payload, "evidence_bundle_id"),
            promotion_packet_id=cls._optional_text(payload, "promotion_packet_id"),
            artifact_graph_hash=cls._optional_text(payload, "artifact_graph_hash"),
            lifecycle_status=str(
                payload.get(
                    "lifecycle_status",
                    "selected" if payload.get("accepted") else "rejected",
                )
            ),
            rejection_stage=cls._optional_text(payload, "rejection_stage"),
        )

    @property
    def point_hash(self) -> str:
        """Return the deterministic hash of this landscape point."""

        return stable_json_hash(self._payload_without_hash())

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready point payload."""

        payload = self._payload_without_hash()
        payload["point_hash"] = self.point_hash
        return payload

    def metric(self, path: str, *, default: float = 0.0) -> float:
        """Return a numeric metric by dotted path for analytics."""

        current: Any = self.metrics
        for part in path.split("."):
            if not isinstance(current, Mapping):
                return default
            current = current.get(part)
        if isinstance(current, bool) or current is None:
            return default
        if isinstance(current, int | float):
            return float(current)
        try:
            return float(str(current))
        except ValueError:
            return default

    @property
    def identity_key(self) -> tuple[str, str]:
        """Return the duplicate-detection key for trial/retry identity."""

        return (self.trial_id, self.retry_id or "")

    @property
    def sort_key(self) -> tuple[str, str, str, str]:
        """Return a deterministic ordering key."""

        return (self.campaign_id, self.generation_id, self.trial_id, self.retry_id or "")

    def _payload_without_hash(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "artifact_graph_hash": self.artifact_graph_hash,
            "campaign_id": self.campaign_id,
            "constraints": dict(self.constraints),
            "evidence_bundle_id": self.evidence_bundle_id,
            "factor_family": self.factor_family,
            "generation_id": self.generation_id,
            "metrics": dict(self.metrics),
            "parameter_hash": self.parameter_hash,
            "promotion_packet_id": self.promotion_packet_id,
            "regime": self.regime,
            "rejection_stage": self.rejection_stage,
            "rejected_reasons": list(self.rejected_reasons),
            "retry_id": self.retry_id,
            "root": self.root,
            "session": self.session,
            "strategy_family": self.strategy_family,
            "timeframe": self.timeframe,
            "trial_id": self.trial_id,
            "universe": list(self.universe),
            "lifecycle_status": self.lifecycle_status,
        }

    @staticmethod
    def _json_object(payload: Mapping[str, Any], field_name: str) -> dict[str, Any]:
        loaded = json.loads(stable_json_dumps(dict(payload)))
        if not isinstance(loaded, dict):
            raise ValueError(f"{field_name} must be a JSON object")
        return loaded

    @staticmethod
    def _required_text(payload: Mapping[str, Any], field_name: str) -> str:
        value = payload.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} is required")
        return value.strip()

    @staticmethod
    def _optional_text(payload: Mapping[str, Any], field_name: str) -> str | None:
        value = payload.get(field_name)
        if value is None:
            return None
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be non-empty when provided")
        return value.strip()


@dataclass(frozen=True, slots=True)
class FitnessQuery:
    """Filters for querying persisted fitness landscape points."""

    campaign_id: str | None = None
    generation_id: str | None = None
    trial_id: str | None = None
    strategy_family: str | None = None
    factor_family: str | None = None
    root: str | None = None
    regime: str | None = None
    session: str | None = None

    def matches(self, point: FitnessLandscapePoint) -> bool:
        """Return whether a point satisfies every non-empty filter."""

        return all(
            expected is None or getattr(point, field_name) == expected
            for field_name, expected in (
                ("campaign_id", self.campaign_id),
                ("generation_id", self.generation_id),
                ("trial_id", self.trial_id),
                ("strategy_family", self.strategy_family),
                ("factor_family", self.factor_family),
                ("root", self.root),
                ("regime", self.regime),
                ("session", self.session),
            )
        )


@dataclass(frozen=True, slots=True)
class FitnessLandscape:
    """In-memory view over completed trial fitness points."""

    points: tuple[FitnessLandscapePoint, ...]

    @property
    def landscape_hash(self) -> str:
        """Return a deterministic hash over the landscape contents."""

        return stable_json_hash(
            {
                "points": [
                    point.to_payload()
                    for point in sorted(self.points, key=lambda item: item.sort_key)
                ]
            }
        )

    def query(self, query: FitnessQuery) -> tuple[FitnessLandscapePoint, ...]:
        """Return points matching the query in stored order."""

        return tuple(point for point in self.points if query.matches(point))

    def rejection_reason_counts(self) -> dict[str, int]:
        """Return deterministic rejection reason counts."""

        counts: dict[str, int] = {}
        for point in self.points:
            for reason in point.rejected_reasons:
                counts[reason] = counts.get(reason, 0) + 1
        return dict(sorted(counts.items(), key=lambda item: item[0]))

    def to_payload(self) -> dict[str, Any]:
        """Return JSON-ready landscape payload."""

        return {
            "fitness_landscape_hash": self.landscape_hash,
            "points": [point.to_payload() for point in self.points],
            "trial_count": len(self.points),
        }


class FitnessLandscapeStore:
    """Append-only JSONL store for autonomous research fitness points."""

    def __init__(self, root_or_path: str | Path) -> None:
        path = Path(root_or_path)
        self.path = path if path.suffix == ".jsonl" else path / "fitness_landscape.jsonl"

    def append(self, point: FitnessLandscapePoint) -> None:
        """Append a completed trial point, rejecting accidental duplicates."""

        existing = self.read().points
        for current in existing:
            if current.trial_id != point.trial_id:
                continue
            if current.retry_id is None and point.retry_id is None:
                raise ValueError(f"duplicate trial_id without retry_id: {point.trial_id}")
            if current.retry_id == point.retry_id:
                raise ValueError(f"duplicate trial_id/retry_id: {point.trial_id}/{point.retry_id}")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(point.to_payload(), sort_keys=True) + "\n")

    def read(self) -> FitnessLandscape:
        """Return the current persisted fitness landscape."""

        if not self.path.exists():
            return FitnessLandscape(())
        points: list[FitnessLandscapePoint] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                payload = json.loads(line)
                if not isinstance(payload, Mapping):
                    raise ValueError("fitness landscape rows must be JSON objects")
                point = FitnessLandscapePoint.from_payload(payload)
                expected_hash = point.point_hash
                if payload.get("point_hash") != expected_hash:
                    raise ValueError("fitness landscape point_hash mismatch")
                points.append(point)
        return FitnessLandscape(tuple(points))

    def query(self, query: FitnessQuery) -> tuple[FitnessLandscapePoint, ...]:
        """Query persisted points."""

        return self.read().query(query)

    @property
    def landscape_hash(self) -> str:
        """Return the current deterministic landscape hash."""

        return self.read().landscape_hash


__all__ = [
    "FitnessLandscape",
    "FitnessLandscapePoint",
    "FitnessLandscapeStore",
    "FitnessQuery",
]
