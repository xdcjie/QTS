from __future__ import annotations

import json
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

import pytest
from qts.research.artifact_graph import (
    ResearchArtifactEdge,
    ResearchArtifactGraph,
    ResearchArtifactNode,
)
from qts.research.audit_log import ResearchAuditLog
from qts.research.evidence_registry import EvidenceRegistry

from scripts import run_research


def test_run_research_audit_verify_accepts_valid_chain(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    audit_log = ResearchAuditLog(tmp_path / "audit")
    audit_log.append_human_review_decision(
        reviewer="risk",
        decision="go",
        reviewed_at=datetime(2026, 5, 26, tzinfo=UTC),
        evidence_bundle_id="evb_001",
    )

    exit_code = run_research.main(["audit", "verify", "--audit-log-root", str(tmp_path / "audit")])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload == {"accepted": True, "reasons": []}


def test_run_research_audit_verify_rejects_tampered_chain(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    audit_log = ResearchAuditLog(tmp_path / "audit")
    audit_log.append_human_review_decision(
        reviewer="risk",
        decision="go",
        reviewed_at=datetime(2026, 5, 26, tzinfo=UTC),
        evidence_bundle_id="evb_001",
    )
    audit_log.path.write_text(
        audit_log.path.read_text(encoding="utf-8").replace("go", "no_go"),
        encoding="utf-8",
    )

    exit_code = run_research.main(["audit", "verify", "--audit-log-root", str(tmp_path / "audit")])

    assert exit_code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["accepted"] is False
    assert payload["reasons"]


def test_run_research_graph_verify_accepts_valid_graph(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    graph_path = tmp_path / "graph.json"
    graph = _valid_graph()
    graph_path.write_text(json.dumps(graph.to_payload(), sort_keys=True), encoding="utf-8")

    exit_code = run_research.main(["graph", "verify", "--graph", str(graph_path)])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["accepted"] is True
    assert payload["artifact_graph_hash"] == graph.stable_hash()


def test_run_research_graph_verify_rejects_missing_edge(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    graph = _valid_graph()
    graph_path = tmp_path / "graph.json"
    graph_path.write_text(
        json.dumps(
            ResearchArtifactGraph(
                nodes=graph.nodes,
                edges=tuple(
                    edge
                    for edge in graph.edges
                    if not (edge.source_id == "report-1" and edge.target_id == "audit-1")
                ),
            ).to_payload(),
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    exit_code = run_research.main(["graph", "verify", "--graph", str(graph_path)])

    assert exit_code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["accepted"] is False
    assert "report must reference audit_record" in payload["reasons"]


def test_run_research_data_quality_run_writes_artifact(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    bars_path = tmp_path / "bars.csv"
    bars_path.write_text(
        "timestamp,close\n2026-01-02T14:30:00Z,100\n",
        encoding="utf-8",
    )
    snapshot_path = tmp_path / "snapshot.json"
    snapshot_path.write_text(
        json.dumps(
            {
                "dataset_id": "dataset-001",
                "timeframe": "1m",
                "start": "2026-01-02T14:30:00Z",
                "end": "2026-01-02T14:31:00Z",
                "calendar": "TEST",
                "dataset_files": [{"path": str(bars_path), "exists": True}],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    exit_code = run_research.main(
        [
            "data-quality",
            "run",
            "--snapshot",
            str(snapshot_path),
            "--output-dir",
            str(tmp_path / "dq"),
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["artifact"]["accepted"] is True
    assert Path(payload["path"]).exists()
    assert payload["artifact_hash"].startswith("sha256:")


def test_run_research_evidence_reproduce_rejects_bundle_hash_mismatch(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    registry_root, bundle_id, artifact_path = _write_evidence_bundle(tmp_path)
    artifact_path.write_text('{"sharpe": "99.0"}\n', encoding="utf-8")

    exit_code = run_research.main(
        [
            "evidence",
            "--registry-root",
            str(registry_root),
            "reproduce",
            "--bundle-id",
            bundle_id,
        ]
    )

    assert exit_code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["accepted"] is False
    assert any("hash mismatch" in reason for reason in payload["reasons"])


def _valid_graph() -> ResearchArtifactGraph:
    return ResearchArtifactGraph(
        nodes=(
            ResearchArtifactNode("manifest-1", "manifest", "sha256:manifest"),
            ResearchArtifactNode("evidence-1", "evidence_bundle", "sha256:evidence"),
            ResearchArtifactNode("promotion-1", "promotion_packet", "sha256:promotion"),
            ResearchArtifactNode("audit-1", "audit_record", "sha256:audit"),
            ResearchArtifactNode("report-1", "report", "sha256:report"),
        ),
        edges=(
            ResearchArtifactEdge("evidence-1", "manifest-1", "references"),
            ResearchArtifactEdge("promotion-1", "evidence-1", "references"),
            ResearchArtifactEdge("report-1", "promotion-1", "references"),
            ResearchArtifactEdge("report-1", "audit-1", "references"),
        ),
    )


def _write_evidence_bundle(tmp_path: Path) -> tuple[Path, str, Path]:
    artifact_path = tmp_path / "metrics.json"
    artifact_path.write_text('{"sharpe": "1.2"}\n', encoding="utf-8")
    artifact_hash = f"sha256:{sha256(artifact_path.read_bytes()).hexdigest()}"
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
    report_path.write_text("# Research Workflow Report\n", encoding="utf-8")
    summary_path = tmp_path / "workflow-summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "run_context": {
                    "dataset_ids": ["fixture:GC:15m"],
                    "git_commit": "abc123",
                    "git_dirty": False,
                    "research_config_hash": "sha256:research",
                    "workflow_config_hash": "sha256:workflow",
                },
                "steps": [
                    {
                        "id": "manifest",
                        "kind": "manifest",
                        "outputs": {"manifest_path": str(manifest_path)},
                        "status": "passed",
                    },
                    {
                        "id": "report",
                        "kind": "report",
                        "outputs": {"report_path": str(report_path)},
                        "status": "passed",
                    },
                ],
                "workflow_id": "repro-flow",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    registry_root = tmp_path / "evidence"
    bundle = EvidenceRegistry(registry_root).create_from_workflow_summary(summary_path)
    return registry_root, bundle.evidence_bundle_id, artifact_path
