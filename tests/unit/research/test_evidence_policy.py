from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from qts.research.evidence_policy import EvidenceCompletenessPolicy, PromotionEvidenceSpec
from qts.research.evidence_registry import EvidenceRegistry
from qts.research.idea_spec import IdeaSpec


def _sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _write_verifiable_bundle(
    tmp_path: Path,
    *,
    git_dirty: bool = False,
    git_commit: str = "abc123",
    strategy_id: str = "vwap",
    idea_id: str = "idea-vwap",
) -> tuple[EvidenceRegistry, str]:
    artifact_path = tmp_path / "metrics.json"
    artifact_path.write_text('{"sharpe": "1.2"}\n', encoding="utf-8")
    artifact_hash = _sha256(artifact_path)

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "artifact_hashes": {artifact_path.name: artifact_hash},
                "artifact_paths_by_hash": {artifact_hash: str(artifact_path)},
                "metrics": {"sharpe": "1.2"},
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    report_path = tmp_path / "workflow-report.md"
    report_path.write_text("# Research Workflow Report\n", encoding="utf-8")
    summary_path = tmp_path / "workflow-summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "run_context": {
                    "backtest_config_hash": "sha256:backtest",
                    "dataset_ids": ["fixture:GC:15m"],
                    "generated_at": "2026-05-25T00:00:00+00:00",
                    "git_branch": "master",
                    "git_commit": git_commit,
                    "git_dirty": git_dirty,
                    "promotion_status": "research_only",
                    "research_config_hash": "sha256:research",
                    "research_config_path": "configs/research/quickstart.yaml",
                    "workflow_config_hash": "sha256:workflow",
                    "workflow_config_path": "configs/research/workflows/quickstart.yaml",
                },
                "periods": [
                    {
                        "end": "2022-01-01T00:00:00+00:00",
                        "name": "selection",
                        "role": "selection",
                        "start": "2020-01-01T00:00:00+00:00",
                    }
                ],
                "status": "completed",
                "steps": [
                    {
                        "id": "tearsheet",
                        "kind": "factor_tearsheet",
                        "message": "done",
                        "outputs": {"manifest_path": str(manifest_path)},
                        "status": "passed",
                    },
                    {
                        "id": "report",
                        "kind": "research_report",
                        "message": "done",
                        "outputs": {"report_path": str(report_path)},
                        "status": "passed",
                    },
                ],
                "workflow_id": "promotion-flow",
            },
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    idea = IdeaSpec(
        idea_id=idea_id,
        title="VWAP pullback",
        hypothesis="VWAP pullback persists after costs.",
        edge_type="mean_reversion",
        source="fixture",
        created_at=datetime(2026, 5, 25, tzinfo=UTC),
    )
    registry = EvidenceRegistry(tmp_path / "evidence")
    bundle = registry.create_from_workflow_summary(
        summary_path,
        idea=idea,
        strategy_id=strategy_id,
    )
    return registry, bundle.evidence_bundle_id


def test_promotion_evidence_policy_accepts_verified_complete_bundle(tmp_path: Path) -> None:
    registry, bundle_id = _write_verifiable_bundle(tmp_path)

    result = EvidenceCompletenessPolicy.promotion_candidate().validate_candidate(
        PromotionEvidenceSpec(
            promotion_candidate_id="pc-vwap",
            strategy_id="vwap",
            evidence_bundle_id=bundle_id,
            status="paper_candidate",
            idea_id="idea-vwap",
        ),
        evidence_registry=registry,
    )

    assert result.accepted
    assert result.reasons == ()
    assert result.checked_paths


def test_promotion_evidence_spec_from_payload_requires_id_fields() -> None:
    try:
        PromotionEvidenceSpec.from_payload(
            {
                "promotion_candidate_id": "",
                "strategy_id": "vwap",
                "evidence_bundle_id": "evb-001",
            }
        )
    except ValueError as exc:
        assert str(exc) == "promotion_candidate_id is required"
    else:
        raise AssertionError("expected promotion_candidate_id validation failure")


def test_promotion_evidence_policy_rejects_dirty_git(tmp_path: Path) -> None:
    registry, bundle_id = _write_verifiable_bundle(tmp_path, git_dirty=True)

    result = EvidenceCompletenessPolicy.promotion_candidate().validate_candidate(
        PromotionEvidenceSpec(
            promotion_candidate_id="pc-vwap",
            strategy_id="vwap",
            evidence_bundle_id=bundle_id,
            status="paper_candidate",
            idea_id="idea-vwap",
        ),
        evidence_registry=registry,
    )

    assert not result.accepted
    assert "git_dirty must be false, got True" in result.reasons


def test_promotion_evidence_policy_rejects_unknown_git_commit(tmp_path: Path) -> None:
    registry, bundle_id = _write_verifiable_bundle(tmp_path, git_commit="unknown")

    result = EvidenceCompletenessPolicy.promotion_candidate().validate_candidate(
        PromotionEvidenceSpec(
            promotion_candidate_id="pc-vwap",
            strategy_id="vwap",
            evidence_bundle_id=bundle_id,
            status="paper_candidate",
            idea_id="idea-vwap",
        ),
        evidence_registry=registry,
    )

    assert not result.accepted
    assert "git_commit must be known" in result.reasons


def test_promotion_evidence_policy_rejects_strategy_mismatch(tmp_path: Path) -> None:
    registry, bundle_id = _write_verifiable_bundle(tmp_path, strategy_id="other")

    result = EvidenceCompletenessPolicy.promotion_candidate().validate_candidate(
        PromotionEvidenceSpec(
            promotion_candidate_id="pc-vwap",
            strategy_id="vwap",
            evidence_bundle_id=bundle_id,
            status="paper_candidate",
            idea_id="idea-vwap",
        ),
        evidence_registry=registry,
    )

    assert not result.accepted
    assert "candidate strategy_id does not match evidence bundle: vwap != other" in result.reasons


def test_promotion_evidence_policy_requires_idea_for_candidates(tmp_path: Path) -> None:
    registry, bundle_id = _write_verifiable_bundle(tmp_path)

    result = EvidenceCompletenessPolicy.promotion_candidate().validate_candidate(
        PromotionEvidenceSpec(
            promotion_candidate_id="pc-vwap",
            strategy_id="vwap",
            evidence_bundle_id=bundle_id,
            status="paper_candidate",
        ),
        evidence_registry=registry,
    )

    assert not result.accepted
    assert "paper_candidate requires idea_id" in result.reasons


def test_promotion_evidence_policy_rejects_mutated_artifact(tmp_path: Path) -> None:
    registry, bundle_id = _write_verifiable_bundle(tmp_path)
    (tmp_path / "metrics.json").write_text('{"sharpe": "99.0"}\n', encoding="utf-8")

    result = EvidenceCompletenessPolicy.promotion_candidate().validate_candidate(
        PromotionEvidenceSpec(
            promotion_candidate_id="pc-vwap",
            strategy_id="vwap",
            evidence_bundle_id=bundle_id,
            status="paper_candidate",
            idea_id="idea-vwap",
        ),
        evidence_registry=registry,
    )

    assert not result.accepted
    assert any("hash mismatch" in reason for reason in result.reasons)
