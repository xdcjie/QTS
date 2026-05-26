from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from qts.research.evidence_registry import EvidenceRegistry, ResearchEvidenceBundle
from qts.research.idea_spec import IdeaSpec


def _write_workflow_summary(tmp_path: Path, manifest_path: Path, report_path: Path) -> Path:
    summary_path = tmp_path / "workflow-summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "run_context": {
                    "backtest_config_hash": "sha256:backtest",
                    "dataset_ids": ["fixture:GC:15m"],
                    "generated_at": "2026-05-25T00:00:00+00:00",
                    "git_branch": "master",
                    "git_commit": "abc123",
                    "git_dirty": False,
                    "promotion_status": "research_only",
                    "research_config_hash": "sha256:research",
                    "research_config_path": "configs/research/quickstart.yaml",
                    "workflow_config_hash": "sha256:workflow",
                    "workflow_config_path": "configs/research/workflows/quickstart.yaml",
                },
                "periods": [
                    {
                        "end": "2022-01-01T00:00:00+00:00",
                        "name": "selection_2020_2022",
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
                "workflow_id": "evidence-flow",
            },
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return summary_path


def test_evidence_bundle_created_from_workflow_summary(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps({"artifact_hashes": {"metrics.json": "sha256:abc"}}, sort_keys=True),
        encoding="utf-8",
    )
    report_path = tmp_path / "workflow-report.md"
    report_path.write_text("# Report\n", encoding="utf-8")
    summary_path = _write_workflow_summary(tmp_path, manifest_path, report_path)
    registry = EvidenceRegistry(tmp_path / "runs" / "research" / "evidence")

    bundle = registry.create_from_workflow_summary(summary_path)

    assert bundle.status == "research_evidence_only"
    assert bundle.promotion_eligibility == "not_reviewed"
    assert bundle.workflow_run_id == "evidence-flow"
    assert bundle.workflow_config_hash == "sha256:workflow"
    assert bundle.dataset_ids == ("fixture:GC:15m",)
    assert bundle.manifest_paths == (str(manifest_path),)
    assert bundle.report_path == str(report_path)
    assert registry.index_path.exists()
    assert (registry.root_dir / f"evidence-bundle-{bundle.evidence_bundle_id}.json").exists()


def test_evidence_bundle_persists_idea_metadata_and_trial_budget_warning(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text('{"metrics": {}}\n', encoding="utf-8")
    report_path = tmp_path / "workflow-report.md"
    report_path.write_text("# Report\n", encoding="utf-8")
    summary_path = _write_workflow_summary(tmp_path, manifest_path, report_path)
    registry = EvidenceRegistry(tmp_path / "evidence")
    idea = IdeaSpec.from_payload(
        {
            "created_at": "2026-05-25T00:00:00+00:00",
            "data_required": ["GC 15m OHLCV"],
            "edge_type": "momentum",
            "hypothesis": "Momentum persists after costs.",
            "idea_id": "idea-momentum",
            "kill_criteria": ["oos_net_sharpe_below_0_8"],
            "source": "fixture",
            "status": "draft",
            "title": "Momentum",
            "trial_budget": {"max_strategy_trials": 3},
            "trial_count": 4,
        }
    )

    bundle = registry.create_from_workflow_summary(summary_path, idea=idea)
    payload = bundle.to_payload()

    assert payload["idea_id"] == "idea-momentum"
    assert payload["idea_metadata"]["kill_criteria"] == ["oos_net_sharpe_below_0_8"]
    assert payload["trial_budget_warnings"] == [
        {
            "budget": 3,
            "idea_id": "idea-momentum",
            "message": "idea-momentum trial_count 4 exceeds budget 3",
            "trial_count": 4,
        }
    ]


def test_evidence_bundle_uses_workflow_summary_idea_metadata(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text('{"metrics": {}}\n', encoding="utf-8")
    report_path = tmp_path / "workflow-report.md"
    report_path.write_text("# Report\n", encoding="utf-8")
    summary_path = _write_workflow_summary(tmp_path, manifest_path, report_path)
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    payload["idea_metadata"] = {
        "created_at": "2026-05-25T00:00:00+00:00",
        "data_required": ["GC 15m OHLCV"],
        "edge_type": "momentum",
        "hypothesis": "Momentum persists after costs.",
        "idea_id": "idea-momentum",
        "kill_criteria": ["oos_net_sharpe_below_0_8"],
        "source": "fixture",
        "status": "draft",
        "title": "Momentum",
        "trial_budget": {"max_strategy_trials": 3},
        "trial_count": 4,
    }
    summary_path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    registry = EvidenceRegistry(tmp_path / "evidence")

    bundle = registry.create_from_workflow_summary(summary_path)

    assert bundle.idea_id == "idea-momentum"
    assert bundle.idea_metadata is not None
    assert bundle.idea_metadata["edge_type"] == "momentum"
    assert bundle.trial_budget_warnings == (
        {
            "budget": 3,
            "idea_id": "idea-momentum",
            "message": "idea-momentum trial_count 4 exceeds budget 3",
            "trial_count": 4,
        },
    )


def test_evidence_bundle_verifies_manifest_hashes(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text('{"metrics": {"sharpe": "1.0"}}\n', encoding="utf-8")
    report_path = tmp_path / "workflow-report.md"
    report_path.write_text("# Report\n", encoding="utf-8")
    summary_path = _write_workflow_summary(tmp_path, manifest_path, report_path)
    registry = EvidenceRegistry(tmp_path / "evidence")
    bundle = registry.create_from_workflow_summary(summary_path)

    verification = registry.verify(bundle.evidence_bundle_id)

    assert verification.accepted
    assert verification.checked_paths == (str(manifest_path), str(report_path))


def test_evidence_bundle_rejects_unverifiable_manifest_artifact_hash(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps({"artifact_hashes": {"metrics.json": "sha256:abc"}}, sort_keys=True),
        encoding="utf-8",
    )
    report_path = tmp_path / "workflow-report.md"
    report_path.write_text("# Report\n", encoding="utf-8")
    summary_path = _write_workflow_summary(tmp_path, manifest_path, report_path)
    registry = EvidenceRegistry(tmp_path / "evidence")
    bundle = registry.create_from_workflow_summary(summary_path)

    verification = registry.verify(bundle.evidence_bundle_id)

    assert not verification.accepted
    assert any(
        "artifact hash has no path for recomputation: metrics.json" in reason
        for reason in verification.reasons
    )


def test_evidence_bundle_verifies_artifact_hashes(tmp_path: Path) -> None:
    artifact_path = tmp_path / "metrics.json"
    artifact_path.write_text('{"sharpe": "1.0"}\n', encoding="utf-8")
    artifact_hash = f"sha256:{hashlib.sha256(artifact_path.read_bytes()).hexdigest()}"
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "artifact_hashes": {artifact_path.name: artifact_hash},
                "artifact_paths_by_hash": {artifact_hash: str(artifact_path)},
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    report_path = tmp_path / "workflow-report.md"
    report_path.write_text("# Report\n", encoding="utf-8")
    summary_path = _write_workflow_summary(tmp_path, manifest_path, report_path)
    registry = EvidenceRegistry(tmp_path / "evidence")
    bundle = registry.create_from_workflow_summary(summary_path)

    artifact_path.write_text('{"sharpe": "99.0"}\n', encoding="utf-8")
    verification = registry.verify(bundle.evidence_bundle_id)

    assert not verification.accepted
    assert any(
        "hash mismatch" in reason and str(artifact_path) in reason
        for reason in verification.reasons
    )


def test_evidence_bundle_missing_artifact_fails(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text('{"metrics": {}}\n', encoding="utf-8")
    report_path = tmp_path / "workflow-report.md"
    report_path.write_text("# Report\n", encoding="utf-8")
    summary_path = _write_workflow_summary(tmp_path, manifest_path, report_path)
    registry = EvidenceRegistry(tmp_path / "evidence")
    bundle = registry.create_from_workflow_summary(summary_path)
    manifest_path.unlink()

    verification = registry.verify(bundle.evidence_bundle_id)

    assert not verification.accepted
    assert any("missing referenced path" in reason for reason in verification.reasons)


def test_evidence_bundle_never_sets_paper_live_production_status() -> None:
    payload = {
        "evidence_bundle_id": "evb_bad",
        "status": "paper",
        "promotion_eligibility": "not_reviewed",
        "workflow_run_id": "flow",
    }

    with pytest.raises(ValueError, match="status must be research_evidence_only"):
        ResearchEvidenceBundle.from_payload(payload)


def test_evidence_review_decision_is_append_only(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text('{"metrics": {}}\n', encoding="utf-8")
    report_path = tmp_path / "workflow-report.md"
    report_path.write_text("# Report\n", encoding="utf-8")
    summary_path = _write_workflow_summary(tmp_path, manifest_path, report_path)
    registry = EvidenceRegistry(tmp_path / "evidence")
    bundle = registry.create_from_workflow_summary(summary_path)

    first = registry.append_review_decision(
        bundle.evidence_bundle_id,
        {"status": "keep_researching", "reviewer": "alice"},
    )
    second = registry.append_review_decision(
        bundle.evidence_bundle_id,
        {"status": "reject", "reviewer": "bob"},
    )

    assert [decision["status"] for decision in second.review_decisions] == [
        "keep_researching",
        "reject",
    ]
    assert first.manifest_hashes == second.manifest_hashes
