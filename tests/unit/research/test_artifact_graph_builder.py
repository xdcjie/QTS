from __future__ import annotations

import json
from pathlib import Path

from qts.research.artifact_graph import (
    ResearchArtifactGraph,
    ResearchArtifactGraphBuilder,
    ResearchArtifactGraphWriter,
)
from qts.research.audit_log import ResearchAuditLog


def test_builder_constructs_required_references_from_minimal_payloads() -> None:
    graph = ResearchArtifactGraphBuilder().build(
        manifests=(
            {
                "manifest_id": "manifest-001",
                "payload_hash": "sha256:manifest",
            },
        ),
        workflow_runs=(
            {
                "workflow_run_id": "workflow-001",
                "manifest_id": "manifest-001",
                "payload_hash": "sha256:workflow",
            },
        ),
        evidence_bundles=(
            {
                "evidence_bundle_id": "evb-001",
                "workflow_run_id": "workflow-001",
                "manifest_ids": ("manifest-001",),
                "payload_hash": "sha256:evidence",
            },
        ),
        promotion_packets=(
            {
                "promotion_packet_id": "packet-001",
                "evidence_bundle_id": "evb-001",
                "metrics": {
                    "metrics_id": "metrics-001",
                    "payload_hash": "sha256:metrics",
                },
                "data_quality": {
                    "data_quality_id": "quality-001",
                    "payload_hash": "sha256:quality",
                },
                "reproducibility": {
                    "reproducibility_id": "repro-001",
                    "payload_hash": "sha256:repro",
                },
                "audit_record_id": "audit-001",
                "payload_hash": "sha256:packet",
            },
        ),
        audit_records=(
            {
                "record_id": "audit-001",
                "payload_hash": "sha256:audit",
            },
        ),
        reports=(
            {
                "report_id": "report-001",
                "promotion_packet_id": "packet-001",
                "audit_record_id": "audit-001",
                "artifact_graph_id": "graph-001",
                "artifact_graph_hash": "sha256:graph",
                "payload_hash": "sha256:report",
            },
        ),
    )

    graph.validate_full_chain()

    assert {node.node_id: node.node_type for node in graph.nodes} == {
        "audit-001": "audit_record",
        "evb-001": "evidence_bundle",
        "graph-001": "artifact_graph",
        "manifest-001": "manifest",
        "metrics-001": "metrics",
        "packet-001": "promotion_packet",
        "quality-001": "data_quality",
        "report-001": "report",
        "repro-001": "reproducibility",
        "workflow-001": "workflow_run",
    }
    assert {(edge.source_id, edge.target_id, edge.relation) for edge in graph.edges} == {
        ("evb-001", "manifest-001", "references"),
        ("evb-001", "metrics-001", "references"),
        ("evb-001", "quality-001", "references"),
        ("evb-001", "repro-001", "references"),
        ("packet-001", "evb-001", "references"),
        ("packet-001", "metrics-001", "references"),
        ("packet-001", "quality-001", "references"),
        ("packet-001", "repro-001", "references"),
        ("packet-001", "audit-001", "references"),
        ("report-001", "audit-001", "references"),
        ("report-001", "graph-001", "references"),
        ("report-001", "packet-001", "references"),
        ("workflow-001", "manifest-001", "references"),
    }


def test_builder_reads_report_projection_refs() -> None:
    graph = ResearchArtifactGraphBuilder().build(
        manifests=({"manifest_id": "manifest-001"},),
        workflow_runs=({"workflow_run_id": "workflow-001", "manifest_id": "manifest-001"},),
        evidence_bundles=(
            {
                "evidence_bundle_id": "evb-001",
                "workflow_run_id": "workflow-001",
                "manifest_ids": ("manifest-001",),
            },
        ),
        promotion_packets=(
            {
                "promotion_packet_id": "packet-001",
                "evidence_bundle_id": "evb-001",
                "metrics": {"metrics_id": "metrics-001"},
                "data_quality": {"data_quality_id": "quality-001"},
                "reproducibility": {"reproducibility_id": "repro-001"},
                "audit_record_id": "audit-001",
            },
        ),
        audit_records=({"record_id": "audit-001"},),
        reports=(
            {
                "report_id": "report-001",
                "projection_refs": {
                    "promotion_packet_id": "packet-001",
                    "audit_record_id": "audit-001",
                    "artifact_graph_hash": "sha256:graph",
                },
            },
        ),
    )

    graph.validate_full_chain()

    assert ("report-001", "packet-001", "references") in {
        (edge.source_id, edge.target_id, edge.relation) for edge in graph.edges
    }
    artifact_graph_nodes = [node for node in graph.nodes if node.node_type == "artifact_graph"]
    assert artifact_graph_nodes[0].node_id == "sha256:graph"
    assert artifact_graph_nodes[0].payload_hash == "sha256:graph"


def test_builder_uses_artifact_graph_path_and_hash_for_graph_artifact() -> None:
    graph = ResearchArtifactGraphBuilder().build(
        manifests=({"manifest_id": "manifest-001"},),
        workflow_runs=({"workflow_run_id": "workflow-001", "manifest_id": "manifest-001"},),
        evidence_bundles=(
            {
                "evidence_bundle_id": "evb-001",
                "workflow_run_id": "workflow-001",
                "manifest_ids": ("manifest-001",),
            },
        ),
        promotion_packets=(
            {
                "promotion_packet_id": "packet-001",
                "evidence_bundle_id": "evb-001",
                "metrics": {"metrics_id": "metrics-001"},
                "data_quality": {"data_quality_id": "quality-001"},
                "reproducibility": {"reproducibility_id": "repro-001"},
                "audit_record_id": "audit-001",
            },
        ),
        audit_records=({"record_id": "audit-001"},),
        reports=(
            {
                "report_id": "report-001",
                "projection_refs": {
                    "promotion_packet_id": "packet-001",
                    "audit_record_id": "audit-001",
                    "artifact_graph_path": "artifact_graph.json",
                    "artifact_graph_hash": "sha256:graph",
                },
            },
        ),
    )

    graph.validate_full_chain()

    artifact_graph_nodes = [node for node in graph.nodes if node.node_type == "artifact_graph"]
    assert artifact_graph_nodes[0].node_id == "artifact_graph.json"
    assert artifact_graph_nodes[0].payload_hash == "sha256:graph"


def test_writer_persists_deterministic_json_and_preserves_stable_hash(tmp_path: Path) -> None:
    graph = ResearchArtifactGraphBuilder().build(
        manifests=({"manifest_id": "manifest-001"},),
        workflow_runs=({"workflow_run_id": "workflow-001", "manifest_id": "manifest-001"},),
        evidence_bundles=(
            {
                "evidence_bundle_id": "evb-001",
                "workflow_run_id": "workflow-001",
                "manifest_ids": ("manifest-001",),
            },
        ),
        promotion_packets=(
            {
                "promotion_packet_id": "packet-001",
                "evidence_bundle_id": "evb-001",
                "metrics": {"metrics_id": "metrics-001"},
                "data_quality": {"data_quality_id": "quality-001"},
                "reproducibility": {"reproducibility_id": "repro-001"},
                "audit_record_id": "audit-001",
            },
        ),
        audit_records=({"record_id": "audit-001"},),
        reports=(
            {
                "report_id": "report-001",
                "promotion_packet_id": "packet-001",
                "audit_record_id": "audit-001",
                "artifact_graph_id": "graph-001",
                "artifact_graph_hash": "sha256:graph",
            },
        ),
    )

    result = ResearchArtifactGraphWriter(tmp_path).write(
        graph,
        output_path="artifact-graph.json",
        audit_log=ResearchAuditLog(tmp_path / "audit"),
    )

    assert result.path == tmp_path / "artifact-graph.json"
    assert result.artifact_graph_hash == graph.stable_hash()
    assert result.graph == graph
    assert result.path.read_text(encoding="utf-8").endswith("\n")

    round_tripped = ResearchArtifactGraph.from_payload(
        json.loads(result.path.read_text(encoding="utf-8"))
    )
    assert round_tripped.stable_hash() == graph.stable_hash()
    assert round_tripped.to_payload() == graph.to_payload()


def test_writer_records_artifact_graph_written_audit_event(tmp_path: Path) -> None:
    graph = ResearchArtifactGraphBuilder().build(
        manifests=({"manifest_id": "manifest-001"},),
        workflow_runs=({"workflow_run_id": "workflow-001", "manifest_id": "manifest-001"},),
        evidence_bundles=(
            {
                "evidence_bundle_id": "evb-001",
                "workflow_run_id": "workflow-001",
                "manifest_ids": ("manifest-001",),
            },
        ),
        promotion_packets=(
            {
                "promotion_packet_id": "packet-001",
                "evidence_bundle_id": "evb-001",
                "metrics": {"metrics_id": "metrics-001"},
                "data_quality": {"data_quality_id": "quality-001"},
                "reproducibility": {"reproducibility_id": "repro-001"},
                "audit_record_id": "audit-001",
            },
        ),
        audit_records=({"record_id": "audit-001"},),
        reports=(
            {
                "report_id": "report-001",
                "promotion_packet_id": "packet-001",
                "audit_record_id": "audit-001",
                "artifact_graph_id": "graph-001",
                "artifact_graph_hash": "sha256:graph",
            },
        ),
    )
    audit_log = ResearchAuditLog(tmp_path / "audit")

    result = ResearchArtifactGraphWriter(tmp_path).write(
        graph,
        output_path="artifact-graph.json",
        audit_log=audit_log,
    )

    records = audit_log.list()
    assert [record.record_type for record in records] == ["artifact_graph_written"]
    assert records[0].payload["artifact_graph_hash"] == result.artifact_graph_hash
    assert records[0].payload["artifact_graph_path"] == str(result.path)
    assert records[0].payload["node_count"] == len(graph.nodes)
    assert records[0].payload["edge_count"] == len(graph.edges)
    assert audit_log.verify_hash_chain() == ()


def test_writer_rejects_unaudited_artifact_graph_write(tmp_path: Path) -> None:
    graph = ResearchArtifactGraphBuilder().build(
        manifests=({"manifest_id": "manifest-001"},),
        workflow_runs=({"workflow_run_id": "workflow-001", "manifest_id": "manifest-001"},),
    )

    try:
        ResearchArtifactGraphWriter(tmp_path).write(graph, output_path="artifact-graph.json")
    except ValueError as exc:
        assert str(exc) == "artifact graph writes require ResearchAuditLog"
    else:
        raise AssertionError("expected unaudited artifact graph write to fail")
