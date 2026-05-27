"""Promotion-grade evidence completeness policy.

The policy keeps promotion evidence as research-only artifacts while making the
promotion review boundary machine-checkable. It validates that a promotion
candidate cites a verifiable evidence bundle with known provenance before human
review can treat it as paper/live-ready evidence.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from qts.research.audit_log import ResearchAuditLog
from qts.research.evidence_registry import EvidenceRegistry

_UNKNOWN_TEXT_VALUES = frozenset({"", "none", "null", "unknown"})
_IDEA_REQUIRED_STATUSES = frozenset(
    {
        "candidate",
        "live_approved",
        "live_candidate",
        "paper_candidate",
        "paper_passed",
        "small_live_candidate",
    }
)


@dataclass(frozen=True, slots=True)
class PromotionEvidenceSpec:
    """Minimal candidate fields needed to validate evidence completeness."""

    promotion_candidate_id: str
    strategy_id: str
    evidence_bundle_id: str
    status: str = "review_required"
    idea_id: str | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "promotion_candidate_id",
            "strategy_id",
            "evidence_bundle_id",
            "status",
        ):
            value = str(getattr(self, field_name)).strip()
            if not value:
                raise ValueError(f"{field_name} is required")
            object.__setattr__(self, field_name, value)
        if self.idea_id is not None:
            idea_id = self.idea_id.strip()
            object.__setattr__(self, "idea_id", idea_id or None)

    def with_idea_id(self, idea_id: str | None) -> PromotionEvidenceSpec:
        """Return a copy carrying an explicit idea id."""

        return PromotionEvidenceSpec(
            promotion_candidate_id=self.promotion_candidate_id,
            strategy_id=self.strategy_id,
            evidence_bundle_id=self.evidence_bundle_id,
            status=self.status,
            idea_id=idea_id,
        )

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> PromotionEvidenceSpec:
        """Build an evidence spec from a YAML/JSON promotion candidate payload."""

        return cls(
            promotion_candidate_id=cls._required_text(payload, "promotion_candidate_id"),
            strategy_id=cls._required_text(payload, "strategy_id"),
            evidence_bundle_id=cls._required_text(payload, "evidence_bundle_id"),
            status=str(payload.get("status", "review_required")),
            idea_id=_optional_text(payload.get("idea_id")),
        )

    @staticmethod
    def _required_text(payload: Mapping[str, Any], field_name: str) -> str:
        value = payload.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} is required")
        return value.strip()


@dataclass(frozen=True, slots=True)
class EvidenceCompletenessResult:
    """Machine-readable result for a promotion evidence completeness check."""

    promotion_candidate_id: str
    evidence_bundle_id: str
    accepted: bool
    checked_paths: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def status(self) -> str:
        """Return the promotion-validation status label."""

        return "accepted" if self.accepted else "rejected"

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready validation payload."""

        return {
            "accepted": self.accepted,
            "checked_paths": list(self.checked_paths),
            "evidence_bundle_id": self.evidence_bundle_id,
            "promotion_candidate_id": self.promotion_candidate_id,
            "reasons": list(self.reasons),
            "status": self.status,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True, slots=True)
class EvidenceCompletenessPolicy:
    """Validate that a promotion candidate cites complete, reproducible evidence."""

    require_verified_bundle: bool = True
    reject_unknown_provenance: bool = True
    reject_dirty_git: bool = True
    require_dataset_ids: bool = True
    require_manifest_paths: bool = True
    require_report_hash: bool = True
    require_period_roles: bool = True
    require_strategy_id: bool = True
    require_matching_idea_id: bool = True

    @classmethod
    def promotion_candidate(cls) -> EvidenceCompletenessPolicy:
        """Return the default strict policy for paper/live promotion review."""

        return cls()

    def validate_candidate(
        self,
        candidate: PromotionEvidenceSpec,
        *,
        evidence_registry: EvidenceRegistry,
        idea_id: str | None = None,
        audit_log: ResearchAuditLog | None = None,
    ) -> EvidenceCompletenessResult:
        """Validate one promotion candidate against its cited evidence bundle."""

        if not isinstance(candidate, PromotionEvidenceSpec):
            raise TypeError("promotion evidence validation requires PromotionEvidenceSpec")
        spec = candidate if idea_id is None else candidate.with_idea_id(idea_id)
        reasons: list[str] = []
        warnings: list[str] = []
        checked_paths: list[str] = []

        try:
            bundle = evidence_registry.show(spec.evidence_bundle_id)
        except FileNotFoundError:
            return self._result(
                spec,
                checked_paths=(),
                reasons=(f"evidence bundle not found: {spec.evidence_bundle_id}",),
                warnings=(),
            )
        except ValueError as exc:
            return self._result(
                spec,
                checked_paths=(),
                reasons=(f"invalid evidence bundle: {exc}",),
                warnings=(),
            )

        if self.require_verified_bundle:
            verification = evidence_registry.verify(spec.evidence_bundle_id, audit_log=audit_log)
            checked_paths.extend(verification.checked_paths)
            if not verification.accepted:
                reasons.extend(verification.reasons)

        self._append_provenance_reasons(bundle.to_payload(), reasons)
        self._append_structure_reasons(bundle.to_payload(), reasons)
        self._append_candidate_linkage_reasons(spec, bundle.to_payload(), reasons)

        for warning in bundle.trial_budget_warnings:
            message = warning.get("message")
            if message is not None:
                warnings.append(str(message))

        return self._result(
            spec,
            checked_paths=tuple(checked_paths),
            reasons=tuple(reasons),
            warnings=tuple(warnings),
        )

    def _append_provenance_reasons(
        self,
        bundle_payload: Mapping[str, Any],
        reasons: list[str],
    ) -> None:
        if self.reject_unknown_provenance:
            for field_name in (
                "workflow_run_id",
                "workflow_config_hash",
                "research_config_hash",
                "git_commit",
                "workflow_summary_hash",
            ):
                self._reject_unknown_field(bundle_payload, field_name, reasons)
        if self.reject_dirty_git and bundle_payload.get("git_dirty") is not False:
            reasons.append(f"git_dirty must be false, got {bundle_payload.get('git_dirty')}")

    def _append_structure_reasons(
        self,
        bundle_payload: Mapping[str, Any],
        reasons: list[str],
    ) -> None:
        if self.require_dataset_ids and not bundle_payload.get("dataset_ids"):
            reasons.append("dataset_ids are required")
        if self.require_manifest_paths and not bundle_payload.get("manifest_paths"):
            reasons.append("manifest_paths are required")
        if self.require_report_hash:
            if not bundle_payload.get("report_path"):
                reasons.append("report_path is required")
            self._reject_unknown_field(bundle_payload, "report_hash", reasons)
        if self.require_period_roles and not bundle_payload.get("period_roles"):
            reasons.append("period_roles are required")

    def _append_candidate_linkage_reasons(
        self,
        spec: PromotionEvidenceSpec,
        bundle_payload: Mapping[str, Any],
        reasons: list[str],
    ) -> None:
        bundle_strategy_id = _optional_text(bundle_payload.get("strategy_id"))
        if self.require_strategy_id and bundle_strategy_id is None:
            reasons.append("evidence bundle strategy_id is required")
        elif bundle_strategy_id is not None and bundle_strategy_id != spec.strategy_id:
            reasons.append(
                "candidate strategy_id does not match evidence bundle: "
                f"{spec.strategy_id} != {bundle_strategy_id}"
            )

        if not self.require_matching_idea_id:
            return
        bundle_idea_id = _optional_text(bundle_payload.get("idea_id"))
        if spec.status in _IDEA_REQUIRED_STATUSES and spec.idea_id is None:
            reasons.append(f"{spec.status} requires idea_id")
            return
        if spec.idea_id is None:
            return
        if bundle_idea_id is None:
            reasons.append("evidence bundle idea_id is required")
            return
        if bundle_idea_id != spec.idea_id:
            reasons.append(
                "candidate idea_id does not match evidence bundle: "
                f"{spec.idea_id} != {bundle_idea_id}"
            )

    @staticmethod
    def _reject_unknown_field(
        payload: Mapping[str, Any],
        field_name: str,
        reasons: list[str],
    ) -> None:
        value = payload.get(field_name)
        if _is_unknown_text(value):
            reasons.append(f"{field_name} must be known")

    @staticmethod
    def _result(
        spec: PromotionEvidenceSpec,
        *,
        checked_paths: tuple[str, ...],
        reasons: tuple[str, ...],
        warnings: tuple[str, ...],
    ) -> EvidenceCompletenessResult:
        return EvidenceCompletenessResult(
            promotion_candidate_id=spec.promotion_candidate_id,
            evidence_bundle_id=spec.evidence_bundle_id,
            accepted=not reasons,
            checked_paths=checked_paths,
            reasons=reasons,
            warnings=warnings,
        )


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _is_unknown_text(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in _UNKNOWN_TEXT_VALUES
    return False


__all__ = [
    "EvidenceCompletenessPolicy",
    "EvidenceCompletenessResult",
    "PromotionEvidenceSpec",
]
