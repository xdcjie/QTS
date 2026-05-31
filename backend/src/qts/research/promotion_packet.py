"""Promotion packet validation for Research OS.

Promotion packets aggregate reviewed evidence for a requested paper/live target
mode. They are validation records only; this module does not create runtime
configuration or start paper/live behavior.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from qts.core.hashing import stable_json_hash
from qts.research.artifact_graph import ResearchArtifactGraphWriter
from qts.research.audit_log import ResearchAuditLog
from qts.research.evidence_registry import EvidenceRegistry
from qts.research.metrics_schema import ResearchMetricsSchema


@dataclass(frozen=True, slots=True)
class PromotionPacketValidationResult:
    """Machine-readable outcome of machine-validating a promotion packet.

    Evidence produced with the optimistic ``same_bar_close`` fill policy is
    never promotion-grade, so such a packet is always rejected here regardless
    of any research waiver; only next-obtainable (``next_bar_open``) evidence
    can reach ``human_pending``.
    """

    accepted: bool
    status: str
    packet_hash: str
    audit_record_id: str
    reasons: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready validation result payload."""

        return {
            "accepted": self.accepted,
            "audit_record_id": self.audit_record_id,
            "packet_hash": self.packet_hash,
            "reasons": list(self.reasons),
            "status": self.status,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True, slots=True)
class PromotionPacketV2:
    """Promotion packet validation object for schema version 2."""

    schema_version: int
    promotion_candidate_id: str
    target_mode: str
    strategy_id: str
    source_module: str
    target_module: str
    idea_id: str
    evidence_bundle_id: str
    metrics: Mapping[str, Any]
    data_quality: Mapping[str, Any]
    reproducibility: Mapping[str, Any]
    runtime: Mapping[str, Any]
    operations: Mapping[str, Any]
    review: Mapping[str, Any]

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> PromotionPacketV2:
        """Build a v2 packet from a JSON/YAML payload mapping."""

        return cls(
            schema_version=cls._int_field(payload, "schema_version"),
            promotion_candidate_id=str(payload.get("promotion_candidate_id", "")),
            target_mode=str(payload.get("target_mode", "")),
            strategy_id=str(payload.get("strategy_id", "")),
            source_module=str(payload.get("source_module", "")),
            target_module=str(payload.get("target_module", "")),
            idea_id=str(payload.get("idea_id", "")),
            evidence_bundle_id=str(payload.get("evidence_bundle_id", "")),
            metrics=cls._mapping_field(payload, "metrics"),
            data_quality=cls._mapping_field(payload, "data_quality"),
            reproducibility=cls._mapping_field(payload, "reproducibility"),
            runtime=cls._mapping_field(payload, "runtime"),
            operations=cls._mapping_field(payload, "operations"),
            review=cls._mapping_field(payload, "review"),
        )

    def validate(
        self,
        *,
        evidence_registry: EvidenceRegistry,
        audit_log: ResearchAuditLog,
        metrics_schema: ResearchMetricsSchema | None = None,
        artifact_graph_writer: ResearchArtifactGraphWriter | None = None,
    ) -> PromotionPacketValidationResult:
        """Machine-validate this packet and append an audit-log record."""

        return self.validate_machine(
            evidence_registry=evidence_registry,
            audit_log=audit_log,
            metrics_schema=metrics_schema,
            artifact_graph_writer=artifact_graph_writer,
        )

    def validate_machine(
        self,
        *,
        evidence_registry: EvidenceRegistry,
        audit_log: ResearchAuditLog,
        metrics_schema: ResearchMetricsSchema | None = None,
        artifact_graph_writer: ResearchArtifactGraphWriter | None = None,
    ) -> PromotionPacketValidationResult:
        """Validate machine-checkable packet evidence without human approval."""
        from qts.research.promotion_packet_validator import PromotionPacketValidator

        return PromotionPacketValidator(self).validate_machine(
            evidence_registry=evidence_registry,
            audit_log=audit_log,
            metrics_schema=metrics_schema,
            artifact_graph_writer=artifact_graph_writer,
        )

    def human_review(
        self,
        *,
        audit_log: ResearchAuditLog,
        decision: str,
        reviewer: str,
        reviewed_at: datetime,
        expected_packet_hash: str | None = None,
        notes: str | None = None,
    ) -> PromotionPacketValidationResult:
        """Append an explicit human review decision for this packet."""

        packet_hash = stable_json_hash(self.to_payload())
        if expected_packet_hash is not None and expected_packet_hash != packet_hash:
            raise ValueError(f"packet hash mismatch: {packet_hash} != {expected_packet_hash}")
        normalized_decision = decision.strip().lower()
        if normalized_decision not in {"approved", "rejected"}:
            raise ValueError("human review decision must be approved or rejected")
        accepted = normalized_decision == "approved"
        record = audit_log.append_human_review_decision(
            reviewer=reviewer,
            decision=normalized_decision,
            reviewed_at=reviewed_at,
            evidence_bundle_id=self.evidence_bundle_id,
            promotion_candidate_id=self.promotion_candidate_id,
            packet_hash=packet_hash,
            notes=notes,
        )
        return PromotionPacketValidationResult(
            accepted=accepted,
            status="human_approved" if accepted else "human_rejected",
            packet_hash=packet_hash,
            audit_record_id=record.record_id,
            reasons=() if accepted else (f"human review decision is {normalized_decision}",),
            warnings=(),
        )

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready packet payload."""

        return {
            "schema_version": self.schema_version,
            "promotion_candidate_id": self.promotion_candidate_id,
            "target_mode": self.target_mode,
            "strategy_id": self.strategy_id,
            "source_module": self.source_module,
            "target_module": self.target_module,
            "idea_id": self.idea_id,
            "evidence_bundle_id": self.evidence_bundle_id,
            "metrics": dict(self.metrics),
            "data_quality": dict(self.data_quality),
            "reproducibility": dict(self.reproducibility),
            "runtime": dict(self.runtime),
            "operations": dict(self.operations),
            "review": dict(self.review),
        }

    @staticmethod
    def _mapping_field(payload: Mapping[str, Any], field_name: str) -> Mapping[str, Any]:
        value = payload.get(field_name, {})
        return dict(value) if isinstance(value, Mapping) else {}

    @staticmethod
    def _int_field(payload: Mapping[str, Any], field_name: str) -> int:
        value = payload.get(field_name)
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{field_name} must be an integer")
        return value


__all__ = [
    "PromotionPacketV2",
    "PromotionPacketValidationResult",
]
