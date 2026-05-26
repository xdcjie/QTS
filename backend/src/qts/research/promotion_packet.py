"""Promotion packet validation for Research OS.

Promotion packets aggregate reviewed evidence for a requested paper/live target
mode. They are validation records only; this module does not create runtime
configuration or start paper/live behavior.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

from qts.core.hashing import stable_json_hash
from qts.research.audit_log import ResearchAuditLog
from qts.research.data_quality import DataQualityArtifact
from qts.research.evidence_policy import EvidenceCompletenessPolicy, PromotionEvidenceSpec
from qts.research.evidence_registry import EvidenceRegistry
from qts.research.metrics_schema import ResearchMetricsSchema
from qts.research.reproducibility import ReproducibilitySnapshotV2


@dataclass(frozen=True, slots=True)
class PromotionPacketValidationResult:
    """Machine-readable outcome of validating a promotion packet."""

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

    _TARGET_MODES: ClassVar[frozenset[str]] = frozenset(
        {
            "paper_simulated",
            "paper_broker",
            "live_observation",
            "live_canary",
            "live",
        }
    )
    _PAPER_MODES: ClassVar[frozenset[str]] = frozenset({"paper_simulated", "paper_broker"})
    _LIVE_MODES: ClassVar[frozenset[str]] = frozenset({"live_observation", "live_canary", "live"})
    _LIVE_RUNTIME_FIELDS: ClassVar[tuple[str, ...]] = (
        "account_id",
        "risk_profile_id",
        "capital_limit",
        "runtime_mode",
        "kill_switch_profile",
    )
    _LIVE_OPERATIONS_FIELDS: ClassVar[tuple[str, ...]] = (
        "rollback_plan",
        "monitoring_plan",
        "alert_policy",
    )
    _METRICS_SCHEMA_PATH: ClassVar[Path] = (
        Path(__file__).resolve().parents[4] / "configs/research/metrics/schema_v2.yaml"
    )

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
    ) -> PromotionPacketValidationResult:
        """Validate this packet and append an audit-log record."""

        reasons: list[str] = []
        warnings: list[str] = []
        self._append_packet_structure_reasons(reasons)
        self._append_evidence_reasons(evidence_registry, reasons, warnings)
        self._append_metrics_reasons(metrics_schema, reasons, warnings)
        self._append_reproducibility_reasons(reasons)
        self._append_data_quality_reasons(reasons)
        self._append_runtime_operations_reasons(reasons)

        accepted = not reasons
        status = "accepted" if accepted else "rejected"
        packet_hash = stable_json_hash(self.to_payload())
        record = audit_log.append(
            "promotion_packet_validated",
            {
                "accepted": accepted,
                "evidence_bundle_id": self.evidence_bundle_id,
                "packet_hash": packet_hash,
                "promotion_candidate_id": self.promotion_candidate_id,
                "reasons": reasons,
                "status": status,
                "strategy_id": self.strategy_id,
                "target_mode": self.target_mode,
                "warnings": warnings,
            },
        )
        return PromotionPacketValidationResult(
            accepted=accepted,
            status=status,
            packet_hash=packet_hash,
            audit_record_id=record.record_id,
            reasons=tuple(reasons),
            warnings=tuple(warnings),
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

    def _append_packet_structure_reasons(self, reasons: list[str]) -> None:
        if self.schema_version != 2:
            reasons.append("schema_version must be 2")
        if self.target_mode not in self._TARGET_MODES:
            reasons.append(f"target_mode is unsupported: {self.target_mode}")
        for field_name in (
            "promotion_candidate_id",
            "strategy_id",
            "source_module",
            "target_module",
            "idea_id",
            "evidence_bundle_id",
        ):
            if not self._has_value(getattr(self, field_name)):
                reasons.append(f"{field_name} is required")
        if self.source_module == self.target_module:
            reasons.append("source_module and target_module must differ")
        if not self.target_module.startswith("strategies.production."):
            reasons.append("target_module must start with strategies.production.")
        for field_name in ("reviewer", "decision", "reviewed_at"):
            if not self._has_value(self.review.get(field_name)):
                reasons.append(f"review.{field_name} is required")

    def _append_evidence_reasons(
        self,
        evidence_registry: EvidenceRegistry,
        reasons: list[str],
        warnings: list[str],
    ) -> None:
        status = "paper_candidate" if self.target_mode in self._PAPER_MODES else "live_candidate"
        try:
            result = EvidenceCompletenessPolicy.promotion_candidate().validate_candidate(
                PromotionEvidenceSpec(
                    promotion_candidate_id=self.promotion_candidate_id,
                    strategy_id=self.strategy_id,
                    evidence_bundle_id=self.evidence_bundle_id,
                    status=status,
                    idea_id=self.idea_id,
                ),
                evidence_registry=evidence_registry,
            )
        except (FileNotFoundError, ValueError) as exc:
            reasons.append(f"evidence validation failed: {exc}")
            return
        reasons.extend(result.reasons)
        warnings.extend(result.warnings)

    def _append_metrics_reasons(
        self,
        metrics_schema: ResearchMetricsSchema | None,
        reasons: list[str],
        warnings: list[str],
    ) -> None:
        payload = self._payload_section("metrics", self.metrics, reasons)
        if payload is None:
            return
        self._append_payload_hash_reason("metrics", self.metrics, payload, reasons)
        try:
            schema = metrics_schema or ResearchMetricsSchema.from_yaml(self._METRICS_SCHEMA_PATH)
            result = schema.validate(payload, purpose="promotion")
        except (OSError, ValueError) as exc:
            reasons.append(f"metrics validation failed: {exc}")
            return
        reasons.extend(result.reasons)
        warnings.extend(result.warnings)
        self._append_research_safety_metric_reasons(payload, reasons)

    def _append_reproducibility_reasons(self, reasons: list[str]) -> None:
        payload = self._payload_section("reproducibility", self.reproducibility, reasons)
        if payload is None:
            return
        self._append_payload_hash_reason("reproducibility", self.reproducibility, payload, reasons)
        try:
            snapshot = ReproducibilitySnapshotV2.from_payload(payload)
        except ValueError as exc:
            reasons.append(f"reproducibility validation failed: {exc}")
            return
        reasons.extend(snapshot.promotion_blockers())

    def _append_data_quality_reasons(self, reasons: list[str]) -> None:
        payload = self._payload_section("data_quality", self.data_quality, reasons)
        if payload is None:
            return
        self._append_payload_hash_reason("data_quality", self.data_quality, payload, reasons)
        try:
            artifact = DataQualityArtifact.from_payload(payload)
        except ValueError as exc:
            reasons.append(f"data_quality validation failed: {exc}")
            return
        if not artifact.accepted:
            reasons.append("data_quality.accepted must be true")
        for blocker in artifact.blockers():
            reasons.append(f"data_quality blocker {blocker['code']}: {blocker['message']}")

    def _append_runtime_operations_reasons(self, reasons: list[str]) -> None:
        if self.target_mode not in self._LIVE_MODES:
            return
        for field_name in self._LIVE_RUNTIME_FIELDS:
            if not self._has_value(self.runtime.get(field_name)):
                reasons.append(f"runtime.{field_name} is required for {self.target_mode}")
        for field_name in self._LIVE_OPERATIONS_FIELDS:
            if not self._has_value(self.operations.get(field_name)):
                reasons.append(f"operations.{field_name} is required for {self.target_mode}")

    @classmethod
    def _append_research_safety_metric_reasons(
        cls,
        metrics_payload: Mapping[str, Any],
        reasons: list[str],
    ) -> None:
        research = metrics_payload.get("research")
        if not isinstance(research, Mapping):
            return
        for field_name in ("deterministic_replay_passed", "no_lookahead_passed"):
            if research.get(field_name) is not True:
                reasons.append(f"research.{field_name} must be true")

    @classmethod
    def _payload_section(
        cls,
        section_name: str,
        section: Mapping[str, Any],
        reasons: list[str],
    ) -> Mapping[str, Any] | None:
        payload = section.get("payload")
        if not isinstance(payload, Mapping):
            reasons.append(f"{section_name}.payload must be a JSON object")
            return None
        return payload

    @classmethod
    def _append_payload_hash_reason(
        cls,
        section_name: str,
        section: Mapping[str, Any],
        payload: Mapping[str, Any],
        reasons: list[str],
    ) -> None:
        expected_hash = section.get("payload_hash")
        if expected_hash is None:
            return
        actual_hash = stable_json_hash(payload)
        if expected_hash != actual_hash:
            reasons.append(
                f"{section_name}.payload_hash mismatch: {actual_hash} != {expected_hash}"
            )

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

    @staticmethod
    def _has_value(value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        return True


__all__ = ["PromotionPacketV2", "PromotionPacketValidationResult"]
