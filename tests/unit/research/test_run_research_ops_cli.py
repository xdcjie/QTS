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
        decision="approved",
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
        decision="approved",
        reviewed_at=datetime(2026, 5, 26, tzinfo=UTC),
        evidence_bundle_id="evb_001",
    )
    audit_log.path.write_text(
        audit_log.path.read_text(encoding="utf-8").replace("approved", "tampered"),
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

    exit_code = run_research.main(
        [
            "graph",
            "verify",
            "--graph",
            str(graph_path),
            "--audit-log-root",
            str(tmp_path / "audit"),
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["accepted"] is True
    assert payload["artifact_graph_hash"] == graph.stable_hash()
    assert payload["audit_record_id"]


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


def test_run_research_graph_verify_rejects_hash_mismatch(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    graph_path = tmp_path / "graph.json"
    graph_path.write_text(json.dumps(_valid_graph().to_payload(), sort_keys=True), encoding="utf-8")

    exit_code = run_research.main(
        [
            "graph",
            "verify",
            "--graph",
            str(graph_path),
            "--expected-hash",
            "sha256:not-the-graph",
        ]
    )

    assert exit_code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["accepted"] is False
    assert "artifact graph hash mismatch" in payload["reasons"][0]


def test_run_research_workflow_writes_summary_audit_and_graph(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    research_config = _write_research_config(tmp_path)
    workflow_path = tmp_path / "workflow.yaml"
    workflow_path.write_text(
        """
version: 1
workflow_id: cli-workflow
steps:
  - id: report
    kind: research_report
    output_root: reports
""",
        encoding="utf-8",
    )
    summary_path = tmp_path / "workflow_summary.json"

    exit_code = run_research.main(
        [
            "--config",
            str(research_config),
            "workflow",
            str(workflow_path),
            "--manifest",
            "configs/research/manifests/gc_si_smoke_v2.yaml",
            "--output",
            str(summary_path),
            "--audit-log-root",
            str(tmp_path / "audit"),
            "--artifact-graph-root",
            str(tmp_path / "graphs"),
        ]
    )

    assert exit_code == 0
    stdout_payload = json.loads(capsys.readouterr().out)
    summary_payload = json.loads(summary_path.read_text(encoding="utf-8"))
    assert stdout_payload == summary_payload
    assert summary_payload["workflow_id"] == "cli-workflow"
    assert summary_payload["manifest_hash"].startswith("sha256:")
    records = ResearchAuditLog(tmp_path / "audit").list()
    assert [record.record_type for record in records] == [
        "research_run_completed",
        "artifact_graph_written",
    ]
    assert records[0].payload["workflow_summary_path"] == str(summary_path)
    assert (
        records[1]
        .payload["artifact_graph_path"]
        .endswith("workflow-cli-workflow-artifact-graph.json")
    )
    graph_path = tmp_path / "graphs" / "workflow-cli-workflow-artifact-graph.json"
    graph = ResearchArtifactGraph.from_payload(json.loads(graph_path.read_text(encoding="utf-8")))
    graph.validate()
    assert {node.node_type for node in graph.nodes} == {"manifest", "workflow_run"}


def test_run_research_workflow_rejects_unclean_engine_parity_evidence(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    research_config = _write_research_config(tmp_path)
    workflow_path = tmp_path / "workflow.yaml"
    workflow_path.write_text(
        """
version: 1
workflow_id: cli-workflow
steps:
  - id: report
    kind: research_report
    output_root: reports
""",
        encoding="utf-8",
    )
    evidence_path = _write_engine_parity_evidence(tmp_path, status="failed")
    summary_path = tmp_path / "workflow_summary.json"

    exit_code = run_research.main(
        [
            "--config",
            str(research_config),
            "workflow",
            str(workflow_path),
            "--manifest",
            "configs/research/manifests/gc_si_smoke_v2.yaml",
            "--output",
            str(summary_path),
            "--engine-parity-evidence",
            str(evidence_path),
        ]
    )

    assert exit_code == 1
    stdout_payload = json.loads(capsys.readouterr().out)
    summary_payload = json.loads(summary_path.read_text(encoding="utf-8"))
    assert stdout_payload == summary_payload
    assert summary_payload["status"] == "failed"
    assert summary_payload["engine_parity_blocked"] is True
    assert summary_payload["engine_parity_evidence"]["accepted"] is False
    assert summary_payload["engine_parity_evidence"]["path"] == str(evidence_path)


def test_run_research_workflow_rejects_graph_without_audit_log(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    research_config = _write_research_config(tmp_path)
    workflow_path = tmp_path / "workflow.yaml"
    workflow_path.write_text(
        """
version: 1
workflow_id: cli-workflow
steps:
  - id: report
    kind: research_report
    output_root: reports
""",
        encoding="utf-8",
    )

    exit_code = run_research.main(
        [
            "--config",
            str(research_config),
            "workflow",
            str(workflow_path),
            "--manifest",
            "configs/research/manifests/gc_si_smoke_v2.yaml",
            "--artifact-graph-root",
            str(tmp_path / "graphs"),
        ]
    )

    assert exit_code == 2
    assert "artifact graph writes require --audit-log-root" in capsys.readouterr().err


def test_run_research_workflow_requires_manifest_v2(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    research_config = _write_research_config(tmp_path)
    workflow_path = tmp_path / "workflow.yaml"
    workflow_path.write_text(
        """
version: 1
workflow_id: cli-workflow
steps:
  - id: report
    kind: research_report
    output_root: reports
""",
        encoding="utf-8",
    )

    exit_code = run_research.main(
        [
            "--config",
            str(research_config),
            "workflow",
            str(workflow_path),
        ]
    )

    assert exit_code == 2
    assert "workflow requires --manifest schema_version=2" in capsys.readouterr().err


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
            "--audit-log-root",
            str(tmp_path / "audit"),
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["artifact"]["accepted"] is True
    assert Path(payload["path"]).exists()
    assert payload["artifact_hash"].startswith("sha256:")
    assert payload["audit_record_id"]


def test_run_research_data_quality_run_can_write_exact_output_path(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    bars_path = tmp_path / "bars.csv"
    bars_path.write_text(
        "timestamp,close\n2026-01-02T14:30:00Z,100\n",
        encoding="utf-8",
    )
    snapshot_path = tmp_path / "snapshot.json"
    output_path = tmp_path / "data_quality.json"
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
            "--output",
            str(output_path),
            "--audit-log-root",
            str(tmp_path / "audit"),
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert Path(payload["path"]) == output_path
    assert payload["audit_record_id"]
    assert (
        json.loads(output_path.read_text(encoding="utf-8"))["artifact_hash"]
        == payload["artifact_hash"]
    )


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


def test_run_research_evidence_bundle_and_verify_write_audit_and_graph(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    summary_path = _write_workflow_summary(tmp_path)
    registry_root = tmp_path / "evidence"
    audit_root = tmp_path / "audit"
    graph_root = tmp_path / "graphs"

    bundle_exit_code = run_research.main(
        [
            "evidence",
            "--registry-root",
            str(registry_root),
            "--audit-log-root",
            str(audit_root),
            "--artifact-graph-root",
            str(graph_root),
            "bundle",
            "--workflow-summary",
            str(summary_path),
            "--strategy-id",
            "vwap",
        ]
    )

    assert bundle_exit_code == 0
    bundle_payload = json.loads(capsys.readouterr().out)
    bundle_id = bundle_payload["evidence_bundle_id"]
    audit_log = ResearchAuditLog(audit_root)
    assert [record.record_type for record in audit_log.list()] == [
        "evidence_bundle_created",
        "artifact_graph_written",
    ]
    graph_path = graph_root / f"evidence-bundle-{bundle_id}-artifact-graph.json"
    assert graph_path.exists()
    ResearchArtifactGraph.from_payload(
        json.loads(graph_path.read_text(encoding="utf-8"))
    ).validate()

    verify_exit_code = run_research.main(
        [
            "evidence",
            "--registry-root",
            str(registry_root),
            "--audit-log-root",
            str(audit_root),
            "verify",
            bundle_id,
        ]
    )

    assert verify_exit_code == 0
    verify_payload = json.loads(capsys.readouterr().out)
    assert verify_payload["accepted"] is True
    assert [record.record_type for record in audit_log.list()] == [
        "evidence_bundle_created",
        "artifact_graph_written",
        "evidence_validated",
    ]
    assert audit_log.verify_hash_chain() == ()


def test_run_research_evidence_bundle_defaults_to_audit_and_graph_roots(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    summary_path = _write_workflow_summary(tmp_path)
    registry_root = tmp_path / "evidence"
    monkeypatch.chdir(tmp_path)

    exit_code = run_research.main(
        [
            "evidence",
            "--registry-root",
            str(registry_root),
            "bundle",
            "--workflow-summary",
            str(summary_path),
            "--strategy-id",
            "vwap",
        ]
    )

    assert exit_code == 0
    bundle_payload = json.loads(capsys.readouterr().out)
    bundle_id = bundle_payload["evidence_bundle_id"]
    assert (tmp_path / "runs" / "research" / "audit" / "audit_log.jsonl").exists()
    assert (
        tmp_path
        / "runs"
        / "research"
        / "artifact_graph"
        / f"evidence-bundle-{bundle_id}-artifact-graph.json"
    ).exists()


def test_run_research_evidence_reproduce_accepts_verified_bundle(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    registry_root, bundle_id, _artifact_path = _write_evidence_bundle(tmp_path)

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

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["accepted"] is True
    assert payload["evidence_bundle_id"] == bundle_id


def test_run_research_evidence_reproduce_rejects_missing_reproducibility_v2_artifact(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    registry_root, bundle_id, _artifact_path = _write_evidence_bundle(
        tmp_path,
        include_reproducibility_v2=False,
    )

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
    assert payload["reproducibility_path"] is None
    assert any(
        reason.startswith("missing reproducibility_v2 artifact path")
        for reason in payload["reasons"]
    )


def test_run_research_evidence_reproduce_rejects_invalid_reproducibility_v2(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    registry_root, bundle_id, reproducibility_path = _write_evidence_bundle(
        tmp_path,
        return_reproducibility=True,
    )
    reproducibility_path.write_text("{", encoding="utf-8")

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
    assert payload["reproducibility_path"] == str(reproducibility_path)
    assert any(
        "reproducibility validation blocker: reproducibility_v2 is not readable or invalid JSON"
        in reason
        for reason in payload["reasons"]
    )


def _valid_graph() -> ResearchArtifactGraph:
    return ResearchArtifactGraph(
        nodes=(
            ResearchArtifactNode("manifest-1", "manifest", "sha256:manifest"),
            ResearchArtifactNode("workflow-1", "workflow_run", "sha256:workflow"),
            ResearchArtifactNode("evidence-1", "evidence_bundle", "sha256:evidence"),
            ResearchArtifactNode("metrics-1", "metrics", "sha256:metrics"),
            ResearchArtifactNode("quality-1", "data_quality", "sha256:quality"),
            ResearchArtifactNode("repro-1", "reproducibility", "sha256:repro"),
            ResearchArtifactNode("promotion-1", "promotion_packet", "sha256:promotion"),
            ResearchArtifactNode("audit-1", "audit_record", "sha256:audit"),
            ResearchArtifactNode("report-1", "report", "sha256:report"),
            ResearchArtifactNode("graph-1", "artifact_graph", "sha256:graph"),
        ),
        edges=(
            ResearchArtifactEdge("workflow-1", "manifest-1", "references"),
            ResearchArtifactEdge("evidence-1", "manifest-1", "references"),
            ResearchArtifactEdge("evidence-1", "metrics-1", "references"),
            ResearchArtifactEdge("evidence-1", "quality-1", "references"),
            ResearchArtifactEdge("evidence-1", "repro-1", "references"),
            ResearchArtifactEdge("promotion-1", "evidence-1", "references"),
            ResearchArtifactEdge("promotion-1", "metrics-1", "references"),
            ResearchArtifactEdge("promotion-1", "quality-1", "references"),
            ResearchArtifactEdge("promotion-1", "repro-1", "references"),
            ResearchArtifactEdge("promotion-1", "audit-1", "references"),
            ResearchArtifactEdge("report-1", "promotion-1", "references"),
            ResearchArtifactEdge("report-1", "audit-1", "references"),
            ResearchArtifactEdge("report-1", "graph-1", "references"),
        ),
    )


def _write_evidence_bundle(
    tmp_path: Path,
    *,
    include_reproducibility_v2: bool = True,
    return_reproducibility: bool = False,
) -> tuple[Path, str, Path]:
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
    steps: list[dict[str, object]] = [
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
    ]
    reproducibility_path: Path | None = None
    if include_reproducibility_v2:
        reproducibility_path = tmp_path / "reproducibility_v2.json"
        reproducibility_path.write_text(
            json.dumps(_reproducibility_v2_payload(), sort_keys=True) + "\n",
            encoding="utf-8",
        )
        steps.append(
            {
                "id": "reproducibility",
                "kind": "reproducibility",
                "outputs": {"reproducibility_v2_path": str(reproducibility_path)},
                "status": "passed",
            }
        )
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
                "steps": steps,
                "workflow_id": "repro-flow",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    registry_root = tmp_path / "evidence"
    bundle = EvidenceRegistry(registry_root).create_from_workflow_summary(summary_path)
    return_path = artifact_path
    if return_reproducibility:
        assert reproducibility_path is not None
        return_path = reproducibility_path
    return registry_root, bundle.evidence_bundle_id, return_path


def _reproducibility_v2_payload() -> dict[str, object]:
    return {
        "calendar_version": "trade_calendar/v1",
        "command_argv": ["run_research", "workflow"],
        "config_hashes": {"configs/research/quickstart.yaml": "sha256:config"},
        "container_digest": None,
        "data_hashes": {"fixtures/data/gc.csv": "sha256:data"},
        "dependency_hashes": {"pyproject.toml": "sha256:deps"},
        "git_dirty": False,
        "git_sha": "f".ljust(40, "1"),
        "manifest_hash": "sha256:manifest",
        "platform": "Linux-6.5.0",
        "python_version": "3.13.0",
        "random_seeds": {"seed": 42},
        "schema_version": 2,
        "stochastic_search_required": False,
    }


def _write_workflow_summary(tmp_path: Path) -> Path:
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
                "periods": [
                    {
                        "end": "2022-01-01T00:00:00+00:00",
                        "name": "selection",
                        "role": "selection",
                        "start": "2020-01-01T00:00:00+00:00",
                    }
                ],
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
                "workflow_id": "evidence-cli-flow",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return summary_path


def _write_engine_parity_evidence(tmp_path: Path, *, status: str = "ok") -> Path:
    path = tmp_path / f"engine-parity-{status}.json"
    diff_artifacts = _write_engine_parity_diff_artifacts(tmp_path)
    path.write_text(
        json.dumps(
            {
                "checked": ["phase1", "phase2", "phase3", "phase4"],
                "candidate_replaces_reference": False,
                "diff_artifacts": diff_artifacts,
                "engine_id": "rust",
                "engine_mode": "shadow",
                "reference_engine": "python",
                "status": status,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _write_engine_parity_diff_artifacts(tmp_path: Path) -> list[dict[str, object]]:
    artifacts: list[dict[str, object]] = []
    for phase in (
        "phase2_replay_sequence_diff",
        "phase3_engine_backtest_diff",
        "phase3_continuous_future_roll_diff",
    ):
        path = tmp_path / f"{phase}.json"
        path.write_text(
            json.dumps(
                {
                    "artifact_type": "python_rust_parity_diff",
                    "candidate_engine": "rust",
                    "differences": [],
                    "phase": phase,
                    "reference_engine": "python",
                    "status": "clean",
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        artifacts.append(
            {
                "phase": phase,
                "path": str(path),
                "sha256": f"sha256:{sha256(path.read_bytes()).hexdigest()}",
                "status": "clean",
            }
        )
    return artifacts


def _write_research_config(tmp_path: Path) -> Path:
    path = tmp_path / "research.yaml"
    path.write_text(
        "\n".join(
            [
                "data:",
                f"  config: {Path('configs/data/historical.local.yaml').resolve()}",
                "  catalog: research_futures",
                "  roots: [GC]",
                "  timeframe: 1m",
                f"backtest_config: {Path('configs/backtest.gc_si.example.yaml').resolve()}",
                f"store: {tmp_path / 'store'}",
                f"output_root: {tmp_path / 'backtests'}",
                "objective_metric: sharpe_ratio",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return path
