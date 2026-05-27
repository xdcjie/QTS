from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from qts.research.artifact_graph import ResearchArtifactGraph, ResearchArtifactGraphWriter
from qts.research.audit_log import ResearchAuditLog
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


def test_evidence_bundle_creation_writes_audit_record(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text('{"metrics": {"sharpe": "1.0"}}\n', encoding="utf-8")
    report_path = tmp_path / "workflow-report.md"
    report_path.write_text("# Report\n", encoding="utf-8")
    summary_path = _write_workflow_summary(tmp_path, manifest_path, report_path)
    registry = EvidenceRegistry(tmp_path / "evidence")
    audit_log = ResearchAuditLog(tmp_path / "audit.jsonl")

    bundle = registry.create_from_workflow_summary(summary_path, audit_log=audit_log)

    records = audit_log.list()
    assert len(records) == 1
    assert records[0].record_type == "evidence_bundle_created"
    assert records[0].payload["evidence_bundle_id"] == bundle.evidence_bundle_id
    assert records[0].payload["workflow_run_id"] == "evidence-flow"
    assert records[0].payload["workflow_summary_hash"] == bundle.workflow_summary_hash
    assert records[0].payload["bundle_hash"].startswith("sha256:")
    assert audit_log.verify_hash_chain() == ()


def test_evidence_bundle_creation_writes_artifact_graph(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text('{"metrics": {"sharpe": "1.0"}}\n', encoding="utf-8")
    report_path = tmp_path / "workflow-report.md"
    report_path.write_text("# Report\n", encoding="utf-8")
    summary_path = _write_workflow_summary(tmp_path, manifest_path, report_path)
    registry = EvidenceRegistry(tmp_path / "evidence")
    audit_log = ResearchAuditLog(tmp_path / "audit.jsonl")
    graph_writer = ResearchArtifactGraphWriter(tmp_path / "graphs")

    bundle = registry.create_from_workflow_summary(
        summary_path,
        audit_log=audit_log,
        artifact_graph_writer=graph_writer,
    )

    assert [record.record_type for record in audit_log.list()] == [
        "evidence_bundle_created",
        "artifact_graph_written",
    ]
    graph_path = (
        tmp_path / "graphs" / f"evidence-bundle-{bundle.evidence_bundle_id}-artifact-graph.json"
    )
    graph = ResearchArtifactGraph.from_payload(json.loads(graph_path.read_text(encoding="utf-8")))
    graph.validate()
    assert {node.node_type for node in graph.nodes} == {
        "audit_record",
        "evidence_bundle",
        "manifest",
    }
    assert (bundle.evidence_bundle_id, str(manifest_path), "references") in {
        (edge.source_id, edge.target_id, edge.relation) for edge in graph.edges
    }


def test_evidence_bundle_creation_graph_includes_created_audit_record(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text('{"metrics": {"sharpe": "1.0"}}\n', encoding="utf-8")
    report_path = tmp_path / "workflow-report.md"
    report_path.write_text("# Report\n", encoding="utf-8")
    summary_path = _write_workflow_summary(tmp_path, manifest_path, report_path)
    registry = EvidenceRegistry(tmp_path / "evidence")
    audit_log = ResearchAuditLog(tmp_path / "audit.jsonl")
    graph_writer = ResearchArtifactGraphWriter(tmp_path / "graphs")

    bundle = registry.create_from_workflow_summary(
        summary_path,
        audit_log=audit_log,
        artifact_graph_writer=graph_writer,
    )

    record = audit_log.list()[0]
    graph_path = (
        tmp_path / "graphs" / f"evidence-bundle-{bundle.evidence_bundle_id}-artifact-graph.json"
    )
    graph = ResearchArtifactGraph.from_payload(json.loads(graph_path.read_text(encoding="utf-8")))
    graph.validate()
    assert record.record_id in {node.node_id for node in graph.nodes}
    assert {node.node_type for node in graph.nodes} == {
        "audit_record",
        "evidence_bundle",
        "manifest",
    }


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
            "edge_types": ["momentum"],
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
        "edge_types": ["momentum"],
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
    assert verification.checked_paths == (str(summary_path), str(manifest_path), str(report_path))


def test_evidence_bundle_verify_writes_accepted_audit_record(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text('{"metrics": {"sharpe": "1.0"}}\n', encoding="utf-8")
    report_path = tmp_path / "workflow-report.md"
    report_path.write_text("# Report\n", encoding="utf-8")
    summary_path = _write_workflow_summary(tmp_path, manifest_path, report_path)
    registry = EvidenceRegistry(tmp_path / "evidence")
    audit_log = ResearchAuditLog(tmp_path / "audit.jsonl")
    bundle = registry.create_from_workflow_summary(summary_path, audit_log=audit_log)

    verification = registry.verify(bundle.evidence_bundle_id, audit_log=audit_log)

    assert verification.accepted
    records = audit_log.list()
    assert [record.record_type for record in records] == [
        "evidence_bundle_created",
        "evidence_validated",
    ]
    validation_record = records[-1]
    assert validation_record.payload["evidence_bundle_id"] == bundle.evidence_bundle_id
    assert validation_record.payload["accepted"] is True
    assert validation_record.payload["status"] == "accepted"
    assert validation_record.payload["reasons"] == []
    assert validation_record.payload["checked_paths"] == [
        str(summary_path),
        str(manifest_path),
        str(report_path),
    ]
    assert audit_log.verify_hash_chain() == ()


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


def test_evidence_bundle_verify_writes_rejected_audit_record(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps({"artifact_hashes": {"metrics.json": "sha256:abc"}}, sort_keys=True),
        encoding="utf-8",
    )
    report_path = tmp_path / "workflow-report.md"
    report_path.write_text("# Report\n", encoding="utf-8")
    summary_path = _write_workflow_summary(tmp_path, manifest_path, report_path)
    registry = EvidenceRegistry(tmp_path / "evidence")
    audit_log = ResearchAuditLog(tmp_path / "audit.jsonl")
    bundle = registry.create_from_workflow_summary(summary_path, audit_log=audit_log)

    verification = registry.verify(bundle.evidence_bundle_id, audit_log=audit_log)

    assert not verification.accepted
    validation_record = audit_log.list()[-1]
    assert validation_record.record_type == "evidence_validated"
    assert validation_record.payload["evidence_bundle_id"] == bundle.evidence_bundle_id
    assert validation_record.payload["accepted"] is False
    assert validation_record.payload["status"] == "rejected"
    assert validation_record.payload["reasons"] == list(verification.reasons)
    assert audit_log.verify_hash_chain() == ()


def test_evidence_create_verify_and_human_review_audit_chain_verifies(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text('{"metrics": {"sharpe": "1.0"}}\n', encoding="utf-8")
    report_path = tmp_path / "workflow-report.md"
    report_path.write_text("# Report\n", encoding="utf-8")
    summary_path = _write_workflow_summary(tmp_path, manifest_path, report_path)
    registry = EvidenceRegistry(tmp_path / "evidence")
    audit_log = ResearchAuditLog(tmp_path / "audit.jsonl")
    bundle = registry.create_from_workflow_summary(summary_path, audit_log=audit_log)

    registry.verify(bundle.evidence_bundle_id, audit_log=audit_log)
    audit_log.append_human_review_decision(
        reviewer="risk",
        decision="go",
        reviewed_at=datetime(2026, 5, 26, 16, 0, tzinfo=UTC),
        evidence_bundle_id=bundle.evidence_bundle_id,
    )

    assert [record.record_type for record in audit_log.list()] == [
        "evidence_bundle_created",
        "evidence_validated",
        "human_review_decided",
    ]
    assert audit_log.verify_hash_chain() == ()


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


def test_evidence_bundle_resolves_manifest_relative_artifact_paths(tmp_path: Path) -> None:
    artifact_path = tmp_path / "artifacts" / "metrics.json"
    artifact_path.parent.mkdir()
    artifact_path.write_text('{"sharpe": "1.0"}\n', encoding="utf-8")
    artifact_hash = f"sha256:{hashlib.sha256(artifact_path.read_bytes()).hexdigest()}"
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "artifact_hashes": {artifact_path.name: artifact_hash},
                "artifact_paths_by_hash": {artifact_hash: "artifacts/metrics.json"},
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

    assert bundle.artifact_paths == {str(artifact_path): artifact_hash}
    assert registry.verify(bundle.evidence_bundle_id).accepted


def test_evidence_bundle_records_workflow_summary_hash(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text('{"metrics": {}}\n', encoding="utf-8")
    report_path = tmp_path / "workflow-report.md"
    report_path.write_text("# Report\n", encoding="utf-8")
    summary_path = _write_workflow_summary(tmp_path, manifest_path, report_path)
    registry = EvidenceRegistry(tmp_path / "evidence")

    bundle = registry.create_from_workflow_summary(summary_path)

    assert bundle.workflow_summary_path == str(summary_path)
    assert bundle.workflow_summary_hash == (
        f"sha256:{hashlib.sha256(summary_path.read_bytes()).hexdigest()}"
    )
    assert ResearchEvidenceBundle.from_payload(bundle.to_payload()).workflow_summary_hash


def test_evidence_bundle_collects_validation_and_summary_paths(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text('{"metrics": {}}\n', encoding="utf-8")
    report_path = tmp_path / "workflow-report.md"
    report_path.write_text("# Report\n", encoding="utf-8")
    extra_paths = {
        "summary_path": tmp_path / "trade-summary.json",
        "validation_output": tmp_path / "validation.json",
        "walk_forward_validation_output": tmp_path / "walk-forward.json",
        "failure_window_veto_output": tmp_path / "failure-window.json",
        "trades_path": tmp_path / "trades.jsonl",
    }
    for path in extra_paths.values():
        path.write_text("{}\n", encoding="utf-8")
    summary_path = _write_workflow_summary(tmp_path, manifest_path, report_path)
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    payload["steps"].append(
        {
            "id": "validate",
            "kind": "optimize",
            "message": "done",
            "outputs": {key: str(path) for key, path in extra_paths.items()},
            "status": "passed",
        }
    )
    summary_path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    registry = EvidenceRegistry(tmp_path / "evidence")

    bundle = registry.create_from_workflow_summary(summary_path)

    for path in extra_paths.values():
        assert str(path) in (bundle.artifact_paths or {})


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


def test_evidence_verify_detects_workflow_summary_mutation(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text('{"metrics": {}}\n', encoding="utf-8")
    report_path = tmp_path / "workflow-report.md"
    report_path.write_text("# Report\n", encoding="utf-8")
    summary_path = _write_workflow_summary(tmp_path, manifest_path, report_path)
    registry = EvidenceRegistry(tmp_path / "evidence")
    bundle = registry.create_from_workflow_summary(summary_path)

    summary_path.write_text(summary_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    verification = registry.verify(bundle.evidence_bundle_id)

    assert not verification.accepted
    assert any(
        "hash mismatch" in reason and str(summary_path) in reason for reason in verification.reasons
    )


def test_evidence_bundle_never_sets_paper_live_production_status() -> None:
    payload = {
        "evidence_bundle_id": "evb_bad",
        "status": "paper",
        "promotion_eligibility": "not_reviewed",
        "workflow_run_id": "flow",
    }

    with pytest.raises(ValueError, match="status must be research_evidence_only"):
        ResearchEvidenceBundle.from_payload(payload)


def test_evidence_review_decision_hard_fails_in_favor_of_audit_log(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text('{"metrics": {}}\n', encoding="utf-8")
    report_path = tmp_path / "workflow-report.md"
    report_path.write_text("# Report\n", encoding="utf-8")
    summary_path = _write_workflow_summary(tmp_path, manifest_path, report_path)
    registry = EvidenceRegistry(tmp_path / "evidence")
    bundle = registry.create_from_workflow_summary(summary_path)

    with pytest.raises(
        ValueError, match="human review decisions must be written to ResearchAuditLog"
    ):
        registry.append_review_decision(
            bundle.evidence_bundle_id,
            {"status": "keep_researching", "reviewer": "alice"},
        )
