from __future__ import annotations

import json

import pytest
from qts.research.artifact_graph import (
    ResearchArtifactEdge,
    ResearchArtifactGraph,
    ResearchArtifactNode,
)


def _node(node_id: str, node_type: str, payload_hash: str | None = None) -> ResearchArtifactNode:
    return ResearchArtifactNode(
        node_id=node_id,
        node_type=node_type,
        payload_hash=payload_hash,
        metadata={"label": node_id},
    )


def _valid_graph() -> ResearchArtifactGraph:
    return ResearchArtifactGraph(
        nodes=(
            _node("manifest-1", "manifest", "sha256:manifest"),
            _node("evidence-1", "evidence_bundle", "sha256:evidence"),
            _node("promotion-1", "promotion_packet", "sha256:promotion"),
            _node("audit-1", "audit_record", "sha256:audit"),
            _node("report-1", "report", "sha256:report"),
        ),
        edges=(
            ResearchArtifactEdge(
                source_id="evidence-1",
                target_id="manifest-1",
                relation="references",
            ),
            ResearchArtifactEdge(
                source_id="promotion-1",
                target_id="evidence-1",
                relation="references",
            ),
            ResearchArtifactEdge(
                source_id="report-1",
                target_id="promotion-1",
                relation="references",
            ),
            ResearchArtifactEdge(
                source_id="report-1",
                target_id="audit-1",
                relation="references",
            ),
        ),
    )


def test_graph_validates_required_artifact_relationships() -> None:
    graph = _valid_graph()

    graph.validate()


@pytest.mark.parametrize(
    ("missing_source", "missing_target", "expected_message"),
    (
        ("promotion-1", "evidence-1", "promotion_packet must reference evidence_bundle"),
        ("evidence-1", "manifest-1", "evidence_bundle must reference manifest"),
        ("report-1", "promotion-1", "report must reference promotion_packet"),
        ("report-1", "audit-1", "report must reference audit_record"),
    ),
)
def test_graph_rejects_missing_required_artifact_relationships(
    missing_source: str,
    missing_target: str,
    expected_message: str,
) -> None:
    graph = _valid_graph()
    graph = ResearchArtifactGraph(
        nodes=graph.nodes,
        edges=tuple(
            edge
            for edge in graph.edges
            if not (edge.source_id == missing_source and edge.target_id == missing_target)
        ),
    )

    with pytest.raises(ValueError, match=expected_message):
        graph.validate()


def test_graph_rejects_missing_node_references() -> None:
    graph = ResearchArtifactGraph(
        nodes=(_node("manifest-1", "manifest"),),
        edges=(
            ResearchArtifactEdge(
                source_id="evidence-1",
                target_id="manifest-1",
                relation="references",
            ),
        ),
    )

    with pytest.raises(ValueError, match="edge source_id is not a node: evidence-1"):
        graph.validate()


def test_graph_rejects_cycles() -> None:
    graph = ResearchArtifactGraph(
        nodes=(
            _node("metrics-1", "metrics"),
            _node("manifest-1", "manifest"),
        ),
        edges=(
            ResearchArtifactEdge(
                source_id="metrics-1",
                target_id="manifest-1",
                relation="references",
            ),
            ResearchArtifactEdge(
                source_id="manifest-1",
                target_id="metrics-1",
                relation="references",
            ),
        ),
    )

    with pytest.raises(ValueError, match="artifact graph contains a cycle"):
        graph.validate()


def test_stable_hash_is_independent_of_input_order() -> None:
    graph = _valid_graph()
    reordered = ResearchArtifactGraph(
        nodes=tuple(reversed(graph.nodes)),
        edges=tuple(reversed(graph.edges)),
    )

    assert graph.to_payload() == reordered.to_payload()
    assert graph.stable_hash() == reordered.stable_hash()


def test_payload_round_trips_json_safe_values() -> None:
    graph = _valid_graph()
    payload = graph.to_payload()
    encoded = json.dumps(payload, sort_keys=True)

    round_tripped = ResearchArtifactGraph.from_payload(json.loads(encoded))

    assert round_tripped == graph
    assert round_tripped.to_payload() == payload
