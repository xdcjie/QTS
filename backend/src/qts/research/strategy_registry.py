"""Strategy lifecycle registry and promotion decision evidence."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from enum import StrEnum
from pathlib import Path
from typing import Any, Self, cast

import yaml  # type: ignore[import-untyped]


class LifecycleStatus(StrEnum):
    """Allowed lifecycle statuses for reviewed strategies."""

    CANDIDATE = "candidate"
    RESEARCH_PASSED = "research_passed"
    PAPER_CANDIDATE = "paper_candidate"
    PAPER_PASSED = "paper_passed"
    LIVE_CANDIDATE = "live_candidate"
    LIVE_APPROVED = "live_approved"
    QUARANTINED = "quarantined"
    RETIRED = "retired"


@dataclass(frozen=True, slots=True)
class StrategyRecord:
    """Complete strategy registry entry."""

    strategy_id: str
    owner: str
    status: LifecycleStatus
    hypothesis: str
    entrypoint: str
    default_config: str
    failure_conditions: tuple[str, ...]

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> Self:
        """Parse and validate a strategy record from YAML/front matter data."""

        status_value = cls._required_text(data, "status")
        try:
            status = LifecycleStatus(status_value)
        except ValueError as exc:
            raise ValueError(f"unsupported lifecycle status: {status_value}") from exc

        failure_conditions = data.get("failure_conditions")
        if not isinstance(failure_conditions, Sequence) or isinstance(failure_conditions, str):
            raise ValueError("failure_conditions must be a non-empty list")
        normalized_failure_conditions = tuple(str(item).strip() for item in failure_conditions)
        if not normalized_failure_conditions or any(
            not item for item in normalized_failure_conditions
        ):
            raise ValueError("failure_conditions must be a non-empty list")

        return cls(
            strategy_id=cls._required_text(data, "id"),
            owner=cls._required_text(data, "owner"),
            status=status,
            hypothesis=cls._required_text(data, "hypothesis"),
            entrypoint=cls._required_text(data, "entrypoint"),
            default_config=cls._required_text(data, "default_config"),
            failure_conditions=normalized_failure_conditions,
        )

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready strategy record."""

        return {
            "default_config": self.default_config,
            "entrypoint": self.entrypoint,
            "failure_conditions": list(self.failure_conditions),
            "hypothesis": self.hypothesis,
            "id": self.strategy_id,
            "owner": self.owner,
            "status": self.status.value,
        }

    @staticmethod
    def _required_text(data: Mapping[str, Any], field_name: str) -> str:
        value = data.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} is required")
        return value.strip()


@dataclass(frozen=True, slots=True)
class StrategyCard:
    """Markdown card front matter for a registered strategy."""

    record: StrategyRecord

    @classmethod
    def from_markdown(cls, path: str | Path) -> Self:
        """Parse a strategy card from a Markdown file with YAML front matter."""

        card_path = Path(path)
        text = card_path.read_text(encoding="utf-8")
        front_matter = cls._front_matter(text, card_path)
        return cls(record=StrategyRecord.from_mapping(front_matter))

    @property
    def strategy_id(self) -> str:
        """Return the strategy ID named by the card."""

        return self.record.strategy_id

    @staticmethod
    def _front_matter(text: str, path: Path) -> Mapping[str, Any]:
        text = text.lstrip()
        if not text.startswith("---\n"):
            raise ValueError(f"{path} must start with YAML front matter")
        try:
            _, front_matter, _body = text.split("---", 2)
        except ValueError as exc:
            raise ValueError(f"{path} must contain closing YAML front matter") from exc
        payload = yaml.safe_load(front_matter) or {}
        if not isinstance(payload, Mapping):
            raise ValueError(f"{path} front matter must be a mapping")
        return cast(Mapping[str, Any], payload)


@dataclass(frozen=True, slots=True)
class PromotionDecision:
    """Explicit lifecycle status transition evidence."""

    decision_id: str
    run_id: str
    strategy_id: str
    from_status: LifecycleStatus
    to_status: LifecycleStatus
    gate: str
    approved_by: str
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        for field_name, value in (
            ("decision_id", self.decision_id),
            ("run_id", self.run_id),
            ("strategy_id", self.strategy_id),
            ("gate", self.gate),
            ("approved_by", self.approved_by),
        ):
            if not str(value).strip():
                raise ValueError(f"{field_name} is required")
        if not self.evidence_refs or any(not str(ref).strip() for ref in self.evidence_refs):
            raise ValueError("evidence_refs must be a non-empty list")

    def required_gate(self) -> str:
        """Return the exact gate required for this transition."""

        try:
            return _REQUIRED_TRANSITION_GATES[(self.from_status, self.to_status)]
        except KeyError as exc:
            raise ValueError(
                "unsupported lifecycle transition: "
                f"{self.from_status.value} -> {self.to_status.value}"
            ) from exc

    def to_payload(self) -> dict[str, Any]:
        """Return a JSON-ready promotion decision artifact payload."""

        return {
            "approved_by": self.approved_by,
            "artifact": f"artifacts/research/{self.run_id}/promotion_decision.json",
            "decision_id": self.decision_id,
            "evidence_refs": list(self.evidence_refs),
            "run_id": self.run_id,
            "status_transition": {
                "from": self.from_status.value,
                "gate": self.gate,
                "to": self.to_status.value,
            },
            "strategy_id": self.strategy_id,
        }


@dataclass(frozen=True, slots=True)
class StrategyRegistry:
    """Validated registry of strategies by stable strategy ID."""

    records: Mapping[str, StrategyRecord]

    @classmethod
    def from_yaml(cls, path: str | Path) -> Self:
        """Parse a strategy registry YAML file."""

        registry_path = Path(path)
        payload = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
        if not isinstance(payload, Mapping):
            raise ValueError("strategy registry must be a mapping")
        strategies = payload.get("strategies")
        if not isinstance(strategies, Sequence) or isinstance(strategies, str):
            raise ValueError("strategies must be a non-empty list")
        records: dict[str, StrategyRecord] = {}
        for item in strategies:
            if not isinstance(item, Mapping):
                raise ValueError("strategy registry entries must be mappings")
            record = StrategyRecord.from_mapping(cast(Mapping[str, Any], item))
            if record.strategy_id in records:
                raise ValueError(f"duplicate strategy id: {record.strategy_id}")
            records[record.strategy_id] = record
        if not records:
            raise ValueError("strategies must be a non-empty list")
        return cls(records=records)

    def get(self, strategy_id: str) -> StrategyRecord:
        """Return a strategy record by ID."""

        try:
            return self.records[strategy_id]
        except KeyError as exc:
            raise ValueError(f"unknown strategy id: {strategy_id}") from exc

    def require_card(self, path: str | Path) -> StrategyCard:
        """Load a strategy card and verify it agrees with the registry."""

        card = StrategyCard.from_markdown(path)
        record = self.get(card.strategy_id)
        if card.record.to_payload() != record.to_payload():
            if card.record.status is not record.status:
                raise ValueError("card status does not match registry")
            raise ValueError("card metadata does not match registry")
        return card

    def apply_decision(self, decision: PromotionDecision) -> Self:
        """Return an updated registry after validating an explicit transition gate."""

        record = self.get(decision.strategy_id)
        if record.status is not decision.from_status:
            raise ValueError(
                f"strategy {decision.strategy_id} is {record.status.value}, "
                f"not {decision.from_status.value}"
            )
        required_gate = decision.required_gate()
        if decision.gate != required_gate:
            raise ValueError(
                f"{decision.from_status.value} -> {decision.to_status.value} "
                f"requires gate {required_gate}"
            )
        updated_records = dict(self.records)
        updated_records[record.strategy_id] = replace(record, status=decision.to_status)
        return type(self)(records=updated_records)


_REQUIRED_TRANSITION_GATES = {
    (LifecycleStatus.CANDIDATE, LifecycleStatus.RESEARCH_PASSED): "research_passed_review",
    (LifecycleStatus.RESEARCH_PASSED, LifecycleStatus.PAPER_CANDIDATE): "paper_candidate_review",
    (LifecycleStatus.PAPER_CANDIDATE, LifecycleStatus.PAPER_PASSED): "paper_passed_review",
    (LifecycleStatus.PAPER_PASSED, LifecycleStatus.LIVE_CANDIDATE): "live_candidate_review",
    (LifecycleStatus.LIVE_CANDIDATE, LifecycleStatus.LIVE_APPROVED): "live_approval_review",
    (LifecycleStatus.CANDIDATE, LifecycleStatus.QUARANTINED): "quarantine_review",
    (LifecycleStatus.RESEARCH_PASSED, LifecycleStatus.QUARANTINED): "quarantine_review",
    (LifecycleStatus.PAPER_CANDIDATE, LifecycleStatus.QUARANTINED): "quarantine_review",
    (LifecycleStatus.PAPER_PASSED, LifecycleStatus.QUARANTINED): "quarantine_review",
    (LifecycleStatus.LIVE_CANDIDATE, LifecycleStatus.QUARANTINED): "quarantine_review",
    (LifecycleStatus.LIVE_APPROVED, LifecycleStatus.QUARANTINED): "quarantine_review",
    (LifecycleStatus.CANDIDATE, LifecycleStatus.RETIRED): "retirement_review",
    (LifecycleStatus.RESEARCH_PASSED, LifecycleStatus.RETIRED): "retirement_review",
    (LifecycleStatus.PAPER_CANDIDATE, LifecycleStatus.RETIRED): "retirement_review",
    (LifecycleStatus.PAPER_PASSED, LifecycleStatus.RETIRED): "retirement_review",
    (LifecycleStatus.LIVE_CANDIDATE, LifecycleStatus.RETIRED): "retirement_review",
    (LifecycleStatus.LIVE_APPROVED, LifecycleStatus.RETIRED): "retirement_review",
    (LifecycleStatus.QUARANTINED, LifecycleStatus.RETIRED): "retirement_review",
}


__all__ = [
    "LifecycleStatus",
    "PromotionDecision",
    "StrategyCard",
    "StrategyRecord",
    "StrategyRegistry",
]
