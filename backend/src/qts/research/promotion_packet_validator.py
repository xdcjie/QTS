"""Promotion packet machine-validation engine.

Owns the machine-validation of a :class:`PromotionPacketV2` extracted from the
packet schema (QTS-FINAL-011): it runs every evidence/metrics/reproducibility/
data-quality/runtime/safety/timing check and produces the
:class:`PromotionPacketValidationResult`. ``PromotionPacketV2`` keeps the schema
(fields, payload (de)serialization, human review) and delegates ``validate_machine``
here so no single class owns both the record shape and the ~450-line validation engine.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

from qts.core.hashing import stable_json_hash
from qts.research.artifact_graph import ResearchArtifactGraphWriter
from qts.research.audit_log import ResearchAuditLog
from qts.research.data_quality import DataQualityArtifact
from qts.research.evidence_policy import EvidenceCompletenessPolicy, PromotionEvidenceSpec
from qts.research.evidence_registry import EvidenceRegistry
from qts.research.metrics_schema import ResearchMetricsSchema
from qts.research.promotion_metrics_integrity import append_research_safety_metric_reasons
from qts.research.promotion_packet import PromotionPacketValidationResult
from qts.research.reproducibility import ReproducibilitySnapshotV2

if TYPE_CHECKING:
    from qts.research.promotion_packet import PromotionPacketV2


class PromotionPacketValidator:
    """Owns machine-validation of a promotion packet and its decision reasons."""

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
    _LIVE_ARTIFACT_REF_FIELDS: ClassVar[tuple[tuple[str, str], ...]] = (
        ("runtime", "risk_profile_id"),
        ("runtime", "kill_switch_profile"),
        ("operations", "rollback_plan"),
        ("operations", "monitoring_plan"),
    )
    _LIVE_EVIDENCE_ARTIFACT_REF_FIELDS: ClassVar[tuple[str, ...]] = (
        "paper_soak_evidence",
        "reconciliation_evidence",
        "kill_switch_drill_evidence",
        "capital_signoff",
    )
    _METRICS_SCHEMA_PATH: ClassVar[Path] = (
        Path(__file__).resolve().parents[4] / "configs/research/metrics/schema_v2.yaml"
    )

    def __init__(self, packet: PromotionPacketV2) -> None:
        """Bind the validator to the packet whose evidence it machine-validates."""
        self._packet = packet

    def validate_machine(
        self,
        *,
        evidence_registry: EvidenceRegistry,
        audit_log: ResearchAuditLog,
        metrics_schema: ResearchMetricsSchema | None = None,
        artifact_graph_writer: ResearchArtifactGraphWriter | None = None,
    ) -> PromotionPacketValidationResult:
        """Validate machine-checkable packet evidence without human approval."""

        packet_hash = stable_json_hash(self._packet.to_payload())
        audit_chain_reasons = audit_log.verify_hash_chain()
        if audit_chain_reasons:
            return PromotionPacketValidationResult(
                accepted=False,
                status="rejected",
                packet_hash=packet_hash,
                audit_record_id="",
                reasons=tuple(
                    f"audit hash chain invalid: {reason}" for reason in audit_chain_reasons
                ),
            )

        reasons: list[str] = []
        warnings: list[str] = []
        self._append_packet_structure_reasons(reasons)
        self._append_evidence_reasons(evidence_registry, audit_log, reasons, warnings)
        metrics_reasons: list[str] = []
        metrics_warnings: list[str] = []
        reproducibility_reasons: list[str] = []
        data_quality_reasons: list[str] = []
        self._append_metrics_reasons(metrics_schema, metrics_reasons, metrics_warnings)
        self._append_reproducibility_reasons(reproducibility_reasons)
        self._append_data_quality_reasons(data_quality_reasons)
        reasons.extend(metrics_reasons)
        reasons.extend(reproducibility_reasons)
        reasons.extend(data_quality_reasons)
        warnings.extend(metrics_warnings)
        self._append_runtime_operations_reasons(reasons)

        metrics_record = audit_log.append(
            "metrics_validated",
            {
                "accepted": not metrics_reasons,
                "metrics_schema_id": self._packet.metrics.get("metrics_schema_id"),
                "payload_hash": self._packet.metrics.get("payload_hash"),
                "promotion_candidate_id": self._packet.promotion_candidate_id,
                "reasons": metrics_reasons,
                "status": "accepted" if not metrics_reasons else "rejected",
                "warnings": metrics_warnings,
            },
        )
        data_quality_record = audit_log.append(
            "data_quality_validated",
            {
                "accepted": not data_quality_reasons,
                "artifact_id": self._packet.data_quality.get("artifact_id"),
                "payload_hash": self._packet.data_quality.get("payload_hash"),
                "promotion_candidate_id": self._packet.promotion_candidate_id,
                "reasons": data_quality_reasons,
                "status": "accepted" if not data_quality_reasons else "rejected",
            },
        )
        reproducibility_record = audit_log.append(
            "reproducibility_validated",
            {
                "accepted": not reproducibility_reasons,
                "payload_hash": self._packet.reproducibility.get("payload_hash"),
                "promotion_candidate_id": self._packet.promotion_candidate_id,
                "reasons": reproducibility_reasons,
                "snapshot_id": self._packet.reproducibility.get("snapshot_id"),
                "status": "accepted" if not reproducibility_reasons else "rejected",
            },
        )
        accepted = not reasons
        status = "human_pending" if accepted else "rejected"
        validation_payload: dict[str, Any] = {
            "accepted": accepted,
            "evidence_bundle_id": self._packet.evidence_bundle_id,
            "human_approval_required": accepted,
            "packet_hash": packet_hash,
            "promotion_candidate_id": self._packet.promotion_candidate_id,
            "reasons": reasons,
            "status": status,
            "strategy_id": self._packet.strategy_id,
            "target_mode": self._packet.target_mode,
            "warnings": warnings,
        }
        record = audit_log.append(
            "promotion_packet_validated",
            validation_payload,
        )
        if accepted and artifact_graph_writer is not None:
            audit_records = [
                metrics_record.to_payload(),
                data_quality_record.to_payload(),
                reproducibility_record.to_payload(),
                record.to_payload(),
            ]
            artifact_graph_writer.write_from_payloads(
                evidence_bundles=(
                    evidence_registry.show(self._packet.evidence_bundle_id).to_payload(),
                ),
                promotion_packets=(
                    {
                        **self._packet.to_payload(),
                        "audit_record_id": record.record_id,
                        "promotion_packet_id": self._packet.promotion_candidate_id,
                        "packet_hash": packet_hash,
                    },
                ),
                audit_records=tuple(audit_records),
                output_path=(
                    f"promotion-packet-{self._packet.promotion_candidate_id}-artifact-graph.json"
                ),
                audit_log=audit_log,
            )
        return PromotionPacketValidationResult(
            accepted=accepted,
            status=status,
            packet_hash=packet_hash,
            audit_record_id=record.record_id,
            reasons=tuple(reasons),
            warnings=tuple(warnings),
        )

    def _append_packet_structure_reasons(self, reasons: list[str]) -> None:
        if self._packet.schema_version != 2:
            reasons.append("schema_version must be 2")
        if self._packet.target_mode not in self._TARGET_MODES:
            reasons.append(f"target_mode is unsupported: {self._packet.target_mode}")
        for field_name, value in (
            ("promotion_candidate_id", self._packet.promotion_candidate_id),
            ("strategy_id", self._packet.strategy_id),
            ("source_module", self._packet.source_module),
            ("target_module", self._packet.target_module),
            ("idea_id", self._packet.idea_id),
            ("evidence_bundle_id", self._packet.evidence_bundle_id),
        ):
            if not self._has_value(value):
                reasons.append(f"{field_name} is required")
        if self._packet.source_module == self._packet.target_module:
            reasons.append("source_module and target_module must differ")
        if not self._packet.target_module.startswith("strategies.production."):
            reasons.append("target_module must start with strategies.production.")

    def _append_review_reasons(self, reasons: list[str]) -> None:
        decision = self._packet.review.get("decision")
        if self._has_value(decision) and str(decision).strip().lower() not in {
            "approved",
            "rejected",
        }:
            reasons.append("review.decision must be approved or rejected")
        reviewed_at = self._packet.review.get("reviewed_at")
        if not self._has_value(reviewed_at):
            return
        try:
            parsed = datetime.fromisoformat(str(reviewed_at))
        except ValueError:
            reasons.append("review.reviewed_at must be an ISO 8601 datetime")
            return
        if parsed.tzinfo is None or parsed.tzinfo.utcoffset(parsed) is None:
            reasons.append("review.reviewed_at must be timezone-aware")

    def _append_evidence_reasons(
        self,
        evidence_registry: EvidenceRegistry,
        audit_log: ResearchAuditLog,
        reasons: list[str],
        warnings: list[str],
    ) -> None:
        status = (
            "paper_candidate" if self._packet.target_mode in self._PAPER_MODES else "live_candidate"
        )
        try:
            result = EvidenceCompletenessPolicy.promotion_candidate().validate_candidate(
                PromotionEvidenceSpec(
                    promotion_candidate_id=self._packet.promotion_candidate_id,
                    strategy_id=self._packet.strategy_id,
                    evidence_bundle_id=self._packet.evidence_bundle_id,
                    status=status,
                    idea_id=self._packet.idea_id,
                ),
                evidence_registry=evidence_registry,
                audit_log=audit_log,
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
        payload = self._payload_section("metrics", self._packet.metrics, reasons)
        if payload is None:
            return
        self._append_payload_hash_reason("metrics", self._packet.metrics, payload, reasons)
        try:
            schema = metrics_schema or ResearchMetricsSchema.from_yaml(self._METRICS_SCHEMA_PATH)
            self._append_metrics_schema_id_reason(schema, payload, reasons)
            result = schema.validate(payload, purpose="promotion")
        except (OSError, ValueError) as exc:
            reasons.append(f"metrics validation failed: {exc}")
            return
        reasons.extend(result.reasons)
        warnings.extend(result.warnings)
        append_research_safety_metric_reasons(payload, reasons)

    def _append_reproducibility_reasons(self, reasons: list[str]) -> None:
        payload = self._payload_section("reproducibility", self._packet.reproducibility, reasons)
        if payload is None:
            return
        self._append_payload_hash_reason(
            "reproducibility", self._packet.reproducibility, payload, reasons
        )
        try:
            snapshot = ReproducibilitySnapshotV2.from_payload(payload)
        except ValueError as exc:
            reasons.append(f"reproducibility validation failed: {exc}")
            return
        reasons.extend(snapshot.promotion_blockers())

    def _append_data_quality_reasons(self, reasons: list[str]) -> None:
        payload = self._payload_section("data_quality", self._packet.data_quality, reasons)
        if payload is None:
            return
        self._append_payload_hash_reason(
            "data_quality", self._packet.data_quality, payload, reasons
        )
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
        if self._packet.target_mode not in self._LIVE_MODES:
            return
        for field_name in self._LIVE_RUNTIME_FIELDS:
            if not self._has_value(self._packet.runtime.get(field_name)):
                reasons.append(f"runtime.{field_name} is required for {self._packet.target_mode}")
        for field_name in self._LIVE_OPERATIONS_FIELDS:
            if not self._has_value(self._packet.operations.get(field_name)):
                reasons.append(
                    f"operations.{field_name} is required for {self._packet.target_mode}"
                )
        for section_name, field_name in self._LIVE_ARTIFACT_REF_FIELDS:
            section = self._packet.runtime if section_name == "runtime" else self._packet.operations
            if not self._has_value(section.get(field_name)):
                continue
            self._append_artifact_ref_reason(
                f"{section_name}.{field_name}",
                section.get(field_name),
                reasons,
            )
        for field_name in self._LIVE_EVIDENCE_ARTIFACT_REF_FIELDS:
            if not self._has_value(self._packet.operations.get(field_name)):
                reasons.append(
                    f"operations.{field_name} is required for {self._packet.target_mode}"
                )
                continue
            self._append_artifact_ref_reason(
                f"operations.{field_name}",
                self._packet.operations.get(field_name),
                reasons,
            )

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
        if not cls._has_value(expected_hash):
            reasons.append(f"{section_name}.payload_hash is required")
            return
        actual_hash = stable_json_hash(payload)
        if expected_hash != actual_hash:
            reasons.append(
                f"{section_name}.payload_hash mismatch: {actual_hash} != {expected_hash}"
            )

    def _append_artifact_ref_reason(
        self,
        field_path: str,
        value: Any,
        reasons: list[str],
    ) -> None:
        if not isinstance(value, Mapping):
            reasons.append(f"{field_path} must be an artifact ref for {self._packet.target_mode}")
            return
        missing_required_field = False
        for ref_field_name in ("artifact_id", "payload_hash", "payload"):
            if ref_field_name not in value or not self._has_value(value.get(ref_field_name)):
                reasons.append(f"{field_path}.{ref_field_name} is required")
                missing_required_field = True
        path_value = value.get("path")
        if not isinstance(path_value, str) or not path_value.strip():
            reasons.append(f"{field_path}.path is required")
            missing_required_field = True
        elif not Path(path_value).exists():
            reasons.append(f"{field_path}.path does not exist")
            missing_required_field = True
        if missing_required_field:
            return
        actual_hash = stable_json_hash(value["payload"])
        expected_hash = value["payload_hash"]
        if expected_hash != actual_hash:
            reasons.append(f"{field_path}.payload_hash mismatch: {actual_hash} != {expected_hash}")

    def _append_metrics_schema_id_reason(
        self,
        schema: ResearchMetricsSchema,
        payload: Mapping[str, Any],
        reasons: list[str],
    ) -> None:
        for field_path, observed in (
            ("metrics.metrics_schema_id", self._packet.metrics.get("metrics_schema_id")),
            ("metrics.payload.metrics_schema_id", payload.get("metrics_schema_id")),
            (
                "metrics.payload._metadata.metrics_schema_id",
                self._metadata_metrics_schema_id(payload),
            ),
        ):
            if observed is None:
                continue
            if observed != schema.schema_id:
                reasons.append(f"{field_path} mismatch: {observed} != {schema.schema_id}")

    @staticmethod
    def _metadata_metrics_schema_id(payload: Mapping[str, Any]) -> Any:
        metadata = payload.get("_metadata")
        if not isinstance(metadata, Mapping):
            return None
        return metadata.get("metrics_schema_id")

    @staticmethod
    def _has_value(value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        return True


__all__ = ["PromotionPacketValidator"]
