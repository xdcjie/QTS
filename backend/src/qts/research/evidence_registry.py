"""Research evidence bundle registry.

Evidence bundles are research-only references to completed artifacts. They are
allowed to support human promotion review, but they never enable paper/live
runtime behavior by themselves.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from qts.core.hashing import stable_json_hash
from qts.research.idea_registry import trial_budget_warning
from qts.research.idea_spec import IdeaSpec


@dataclass(frozen=True, slots=True)
class EvidenceVerificationResult:
    """Result of verifying one evidence bundle's referenced artifacts."""

    accepted: bool
    checked_paths: tuple[str, ...]
    reasons: tuple[str, ...] = ()

    def to_payload(self) -> dict[str, Any]:
        """Return a JSON-ready verification payload."""

        return {
            "accepted": self.accepted,
            "checked_paths": list(self.checked_paths),
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True, slots=True)
class ResearchEvidenceBundle:
    """Workflow-level research evidence object used by promotion review."""

    evidence_bundle_id: str
    workflow_run_id: str
    workflow_config_hash: str = "unknown"
    research_config_hash: str = "unknown"
    git_commit: str = "unknown"
    git_dirty: bool | str = "unknown"
    dataset_ids: tuple[str, ...] = ()
    manifest_paths: tuple[str, ...] = ()
    manifest_hashes: Mapping[str, str] | None = None
    artifact_hashes: Mapping[str, str] | None = None
    artifact_paths: Mapping[str, str] | None = None
    report_path: str | None = None
    period_roles: Mapping[str, str] | None = None
    idea_id: str | None = None
    idea_metadata: Mapping[str, Any] | None = None
    trial_budget_warnings: tuple[Mapping[str, Any], ...] = ()
    strategy_id: str | None = None
    review_decisions: tuple[Mapping[str, Any], ...] = ()
    status: str = "research_evidence_only"
    promotion_eligibility: str = "not_reviewed"

    def __post_init__(self) -> None:
        if self.status != "research_evidence_only":
            raise ValueError("status must be research_evidence_only")
        if self.promotion_eligibility != "not_reviewed":
            raise ValueError("promotion_eligibility must be not_reviewed")

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> ResearchEvidenceBundle:
        """Rehydrate a bundle from deterministic JSON payload."""

        return cls(
            evidence_bundle_id=cls._required_text(payload, "evidence_bundle_id"),
            workflow_run_id=cls._required_text(payload, "workflow_run_id"),
            workflow_config_hash=str(payload.get("workflow_config_hash", "unknown")),
            research_config_hash=str(payload.get("research_config_hash", "unknown")),
            git_commit=str(payload.get("git_commit", "unknown")),
            git_dirty=payload.get("git_dirty", "unknown"),
            dataset_ids=_string_tuple(payload.get("dataset_ids", ())),
            manifest_paths=_string_tuple(payload.get("manifest_paths", ())),
            manifest_hashes=_string_mapping(payload.get("manifest_hashes", {})),
            artifact_hashes=_string_mapping(payload.get("artifact_hashes", {})),
            artifact_paths=_string_mapping(payload.get("artifact_paths", {})),
            report_path=None if payload.get("report_path") is None else str(payload["report_path"]),
            period_roles=_string_mapping(payload.get("period_roles", {})),
            idea_id=None if payload.get("idea_id") is None else str(payload["idea_id"]),
            idea_metadata=_optional_mapping(payload.get("idea_metadata")),
            trial_budget_warnings=cls._mapping_tuple(payload.get("trial_budget_warnings", ())),
            strategy_id=None if payload.get("strategy_id") is None else str(payload["strategy_id"]),
            review_decisions=cls._mapping_tuple(payload.get("review_decisions", ())),
            status=str(payload.get("status", "research_evidence_only")),
            promotion_eligibility=str(payload.get("promotion_eligibility", "not_reviewed")),
        )

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON payload."""

        return {
            "artifact_hashes": dict(self.artifact_hashes or {}),
            "artifact_paths": dict(self.artifact_paths or {}),
            "dataset_ids": list(self.dataset_ids),
            "evidence_bundle_id": self.evidence_bundle_id,
            "git_commit": self.git_commit,
            "git_dirty": self.git_dirty,
            "idea_id": self.idea_id,
            "idea_metadata": dict(self.idea_metadata or {}),
            "manifest_hashes": dict(self.manifest_hashes or {}),
            "manifest_paths": list(self.manifest_paths),
            "period_roles": dict(self.period_roles or {}),
            "promotion_eligibility": self.promotion_eligibility,
            "report_path": self.report_path,
            "research_config_hash": self.research_config_hash,
            "review_decisions": [dict(decision) for decision in self.review_decisions],
            "status": self.status,
            "strategy_id": self.strategy_id,
            "trial_budget_warnings": [dict(warning) for warning in self.trial_budget_warnings],
            "workflow_config_hash": self.workflow_config_hash,
            "workflow_run_id": self.workflow_run_id,
        }

    def with_review_decision(self, decision: Mapping[str, Any]) -> ResearchEvidenceBundle:
        """Return a new bundle with an appended review decision."""

        return ResearchEvidenceBundle.from_payload(
            {
                **self.to_payload(),
                "review_decisions": [*self.review_decisions, dict(decision)],
            }
        )

    @staticmethod
    def _required_text(payload: Mapping[str, Any], field_name: str) -> str:
        value = payload.get(field_name)
        if not isinstance(value, str) or not value:
            raise ValueError(f"{field_name} is required")
        return value

    @staticmethod
    def _mapping_tuple(value: Any) -> tuple[Mapping[str, Any], ...]:
        if value is None:
            return ()
        if not isinstance(value, Sequence) or isinstance(value, str):
            raise ValueError("expected JSON object list")
        result: list[Mapping[str, Any]] = []
        for item in value:
            if not isinstance(item, Mapping):
                raise ValueError("expected JSON object list")
            result.append(dict(item))
        return tuple(result)


class EvidenceRegistry:
    """Owns research evidence bundle files and a JSONL index."""

    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir

    @property
    def index_path(self) -> Path:
        """Return the JSONL evidence index path."""

        return self.root_dir / "index.jsonl"

    def create_from_workflow_summary(
        self,
        workflow_summary_path: Path,
        *,
        idea: IdeaSpec | None = None,
        idea_id: str | None = None,
        strategy_id: str | None = None,
    ) -> ResearchEvidenceBundle:
        """Create and persist an evidence bundle from a workflow JSON payload."""

        payload = _load_json_mapping(workflow_summary_path)
        run_context = self._mapping(payload.get("run_context", {}))
        manifest_paths = _collect_output_paths(payload, "manifest_path")
        report_paths = _collect_output_paths(payload, "report_path")
        period_roles = {
            str(period["name"]): str(period["role"])
            for period in payload.get("periods", ())
            if isinstance(period, Mapping) and "name" in period and "role" in period
        }
        manifest_hashes = {path: _sha256_path(Path(path)) for path in manifest_paths}
        manifest_artifact_hashes = _collect_manifest_artifact_hashes(manifest_paths)
        artifact_path_hashes = _collect_manifest_artifact_paths(manifest_paths)
        artifact_path_hashes.update(
            _hash_existing_paths(_collect_output_paths(payload, "artifact_path"))
        )
        artifact_path_hashes.update(
            _hash_existing_paths(_collect_output_paths(payload, "artifact_paths"))
        )
        report_path = report_paths[-1] if report_paths else None
        summary_idea = _idea_from_payload(payload.get("idea_metadata"))
        if idea is None:
            idea = summary_idea
        resolved_idea_id = idea_id
        idea_metadata: Mapping[str, Any] | None = None
        trial_budget_warnings: tuple[Mapping[str, Any], ...] = ()
        if idea is not None:
            if idea_id is not None and idea_id != idea.idea_id:
                raise ValueError("idea_id must match idea.idea_id")
            resolved_idea_id = idea.idea_id
            idea_metadata = idea.to_payload()
            trial_budget_warnings = _trial_budget_warning_payloads(idea)
        bundle_seed = {
            "artifact_paths": artifact_path_hashes,
            "idea_id": resolved_idea_id,
            "manifest_hashes": manifest_hashes,
            "report_path": report_path,
            "summary_hash": _sha256_path(workflow_summary_path),
            "workflow_run_id": payload.get("workflow_id"),
        }
        bundle = ResearchEvidenceBundle(
            evidence_bundle_id=_bundle_id(bundle_seed),
            workflow_run_id=str(payload.get("workflow_id", "")),
            workflow_config_hash=str(run_context.get("workflow_config_hash", "unknown")),
            research_config_hash=str(run_context.get("research_config_hash", "unknown")),
            git_commit=str(run_context.get("git_commit", "unknown")),
            git_dirty=run_context.get("git_dirty", "unknown"),
            dataset_ids=_string_tuple(run_context.get("dataset_ids", ())),
            manifest_paths=manifest_paths,
            manifest_hashes=manifest_hashes,
            artifact_hashes={
                **manifest_artifact_hashes,
                **artifact_path_hashes,
            },
            artifact_paths=artifact_path_hashes,
            report_path=report_path,
            period_roles=period_roles,
            idea_id=resolved_idea_id,
            idea_metadata=idea_metadata,
            trial_budget_warnings=trial_budget_warnings,
            strategy_id=strategy_id,
        )
        self._write_bundle(bundle)
        self._write_index(self._upsert(bundle))
        return bundle

    def show(self, evidence_bundle_id: str) -> ResearchEvidenceBundle:
        """Load one evidence bundle by id."""

        path = self.root_dir / f"evidence-bundle-{evidence_bundle_id}.json"
        return ResearchEvidenceBundle.from_payload(_load_json_mapping(path))

    def list(self) -> tuple[ResearchEvidenceBundle, ...]:
        """Return indexed evidence bundles sorted by id."""

        if not self.index_path.exists():
            return ()
        bundles: list[ResearchEvidenceBundle] = []
        for line in self.index_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                bundles.append(ResearchEvidenceBundle.from_payload(json.loads(line)))
        return tuple(sorted(bundles, key=lambda bundle: bundle.evidence_bundle_id))

    def verify(self, evidence_bundle_id: str) -> EvidenceVerificationResult:
        """Verify referenced manifests/reports still exist and match stored hashes."""

        bundle = self.show(evidence_bundle_id)
        checked: list[str] = []
        reasons: list[str] = []
        for path_text, expected_hash in (bundle.manifest_hashes or {}).items():
            checked.append(path_text)
            path = Path(path_text)
            if not path.exists():
                reasons.append(f"missing referenced path: {path_text}")
                continue
            actual_hash = _sha256_path(path)
            if actual_hash != expected_hash:
                reasons.append(f"hash mismatch for {path_text}: {actual_hash} != {expected_hash}")
        for path_text, expected_hash in (bundle.artifact_paths or {}).items():
            checked.append(path_text)
            path = Path(path_text)
            if not path.exists():
                reasons.append(f"missing referenced path: {path_text}")
                continue
            actual_hash = _sha256_path(path)
            if actual_hash != expected_hash:
                reasons.append(f"hash mismatch for {path_text}: {actual_hash} != {expected_hash}")
        verified_artifact_hashes = set((bundle.artifact_paths or {}).values())
        for artifact_name, expected_hash in (bundle.artifact_hashes or {}).items():
            if expected_hash not in verified_artifact_hashes:
                reasons.append(f"artifact hash has no path for recomputation: {artifact_name}")
        if bundle.report_path is not None:
            checked.append(bundle.report_path)
            if not Path(bundle.report_path).exists():
                reasons.append(f"missing referenced path: {bundle.report_path}")
        return EvidenceVerificationResult(
            accepted=not reasons,
            checked_paths=tuple(checked),
            reasons=tuple(reasons),
        )

    def append_review_decision(
        self,
        evidence_bundle_id: str,
        decision: Mapping[str, Any],
    ) -> ResearchEvidenceBundle:
        """Append a reviewer decision without rewriting hashes or prior decisions."""

        bundle = self.show(evidence_bundle_id).with_review_decision(decision)
        self._write_bundle(bundle)
        self._write_index(self._upsert(bundle))
        return bundle

    def _write_bundle(self, bundle: ResearchEvidenceBundle) -> None:
        self.root_dir.mkdir(parents=True, exist_ok=True)
        path = self.root_dir / f"evidence-bundle-{bundle.evidence_bundle_id}.json"
        path.write_text(
            json.dumps(bundle.to_payload(), sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )

    def _upsert(self, bundle: ResearchEvidenceBundle) -> tuple[ResearchEvidenceBundle, ...]:
        by_id = {item.evidence_bundle_id: item for item in self.list()}
        by_id[bundle.evidence_bundle_id] = bundle
        return tuple(by_id.values())

    def _write_index(self, bundles: Sequence[ResearchEvidenceBundle]) -> None:
        self.root_dir.mkdir(parents=True, exist_ok=True)
        lines = [
            json.dumps(bundle.to_payload(), sort_keys=True)
            for bundle in sorted(bundles, key=lambda item: item.evidence_bundle_id)
        ]
        self.index_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

    @staticmethod
    def _mapping(value: Any) -> Mapping[str, Any]:
        if isinstance(value, Mapping):
            return value
        return {}


def _load_json_mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"evidence input not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _collect_output_paths(payload: Mapping[str, Any], key: str) -> tuple[str, ...]:
    paths: list[str] = []
    for step in payload.get("steps", ()):
        if not isinstance(step, Mapping):
            continue
        outputs = step.get("outputs", {})
        if not isinstance(outputs, Mapping):
            continue
        value = outputs.get(key)
        if isinstance(value, str):
            paths.append(value)
        elif isinstance(value, Sequence) and not isinstance(value, str):
            paths.extend(str(item) for item in value if isinstance(item, (str, Path)))
    return tuple(paths)


def _collect_manifest_artifact_hashes(manifest_paths: Sequence[str]) -> dict[str, str]:
    artifact_hashes: dict[str, str] = {}
    for manifest_path in manifest_paths:
        path = Path(manifest_path)
        if not path.exists():
            continue
        payload = _load_json_mapping(path)
        raw_hashes = payload.get("artifact_hashes", {})
        if isinstance(raw_hashes, Mapping):
            artifact_hashes.update({str(key): str(value) for key, value in raw_hashes.items()})
    return artifact_hashes


def _collect_manifest_artifact_paths(manifest_paths: Sequence[str]) -> dict[str, str]:
    artifact_paths: dict[str, str] = {}
    for manifest_path in manifest_paths:
        path = Path(manifest_path)
        if not path.exists():
            continue
        payload = _load_json_mapping(path)
        raw_paths = payload.get("artifact_paths_by_hash", {})
        if isinstance(raw_paths, Mapping):
            artifact_paths.update({str(item): str(key) for key, item in raw_paths.items()})
    return artifact_paths


def _hash_existing_paths(paths: Sequence[str]) -> dict[str, str]:
    return {path: _sha256_path(Path(path)) for path in paths}


def _string_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, Sequence) or isinstance(value, str):
        raise ValueError("expected JSON string list")
    if not all(isinstance(item, str) for item in value):
        raise ValueError("expected JSON string list")
    return tuple(value)


def _string_mapping(value: Any) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError("expected JSON string object")
    return {str(key): str(item) for key, item in value.items()}


def _optional_mapping(value: Any) -> Mapping[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ValueError("expected JSON object")
    return dict(value)


def _idea_from_payload(value: Any) -> IdeaSpec | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ValueError("idea_metadata must be a JSON object")
    return IdeaSpec.from_payload(value)


def _trial_budget_warning_payloads(idea: IdeaSpec) -> tuple[Mapping[str, Any], ...]:
    warning = trial_budget_warning(idea)
    if warning is None:
        return ()
    return (
        {
            "budget": warning.budget,
            "idea_id": warning.idea_id,
            "message": warning.message,
            "trial_count": warning.trial_count,
        },
    )


def _sha256_path(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return f"sha256:{hasher.hexdigest()}"


def _bundle_id(seed: Mapping[str, Any]) -> str:
    return f"evb_{stable_json_hash(seed).removeprefix('sha256:')[:16]}"


__all__ = [
    "EvidenceRegistry",
    "EvidenceVerificationResult",
    "ResearchEvidenceBundle",
]
