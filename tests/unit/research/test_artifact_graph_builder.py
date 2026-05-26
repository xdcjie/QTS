from __future__ import annotations

import json
from pathlib import Path

from qts.research.artifact_graph import (
    ResearchArtifactGraph,
    ResearchArtifactGraphBuilder,
    ResearchArtifactGraphWriter,
)


def test_builder_constructs_required_references_from_minimal_payloads() -> None:
    graph = ResearchArtifactGraphBuilder().build(
        manifests=(
            {
                "manifest_id": "manifest-001",
                "payload_hash": "sha256:manifest",
            },
        ),
        evidence_bundles=(
            {
                "evidence_bundle_id": "evb-001",
                "manifest_ids": ("manifest-001",),
                "payload_hash": "sha256:evidence",
            },
        ),
        promotion_packets=(
            {
                "promotion_packet_id": "packet-001",
                "evidence_bundle_id": "evb-001",
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
                "payload_hash": "sha256:report",
            },
        ),
    )

    graph.validate()

    assert {node.node_id: node.node_type for node in graph.nodes} == {
        "audit-001": "audit_record",
        "evb-001": "evidence_bundle",
        "manifest-001": "manifest",
        "packet-001": "promotion_packet",
        "report-001": "report",
    }
    assert {(edge.source_id, edge.target_id, edge.relation) for edge in graph.edges} == {
        ("evb-001", "manifest-001", "references"),
        ("packet-001", "evb-001", "references"),
        ("report-001", "audit-001", "references"),
        ("report-001", "packet-001", "references"),
    }


def test_builder_reads_report_projection_refs() -> None:
    graph = ResearchArtifactGraphBuilder().build(
        manifests=({"manifest_id": "manifest-001"},),
        evidence_bundles=(
            {
                "evidence_bundle_id": "evb-001",
                "manifest_ids": ("manifest-001",),
            },
        ),
        promotion_packets=(
            {
                "promotion_packet_id": "packet-001",
                "evidence_bundle_id": "evb-001",
            },
        ),
        audit_records=({"record_id": "audit-001"},),
        reports=(
            {
                "report_id": "report-001",
                "projection_refs": {
                    "promotion_packet_id": "packet-001",
                    "audit_record_id": "audit-001",
                },
            },
        ),
    )

    graph.validate()

    assert ("report-001", "packet-001", "references") in {
        (edge.source_id, edge.target_id, edge.relation) for edge in graph.edges
    }


def test_writer_persists_deterministic_json_and_preserves_stable_hash(tmp_path: Path) -> None:
    graph = ResearchArtifactGraphBuilder().build(
        manifests=({"manifest_id": "manifest-001"},),
        evidence_bundles=(
            {
                "evidence_bundle_id": "evb-001",
                "manifest_ids": ("manifest-001",),
            },
        ),
    )

    result = ResearchArtifactGraphWriter(tmp_path).write(graph, output_path="artifact-graph.json")

    assert result.path == tmp_path / "artifact-graph.json"
    assert result.artifact_graph_hash == graph.stable_hash()
    assert result.graph == graph
    assert result.path.read_text(encoding="utf-8").endswith("\n")

    round_tripped = ResearchArtifactGraph.from_payload(
        json.loads(result.path.read_text(encoding="utf-8"))
    )
    assert round_tripped.stable_hash() == graph.stable_hash()
    assert round_tripped.to_payload() == graph.to_payload()
