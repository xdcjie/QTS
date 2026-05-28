from __future__ import annotations

import json
from pathlib import Path

from qts.research.artifact_graph import ResearchArtifactGraph

from tests.integration.research._autonomous_engine_plan_helpers import read_jsonl, run_engine


def test_final_artifact_graph_covers_all_selected_candidates(tmp_path: Path) -> None:
    _campaign_path, result = run_engine(tmp_path)

    selected_rows = read_jsonl(result.selected_candidates_path)
    graph = ResearchArtifactGraph.from_payload(
        json.loads(result.artifact_graph_path.read_text(encoding="utf-8"))
    )
    graph.validate_full_chain()
    promotion_packet_nodes = {
        node.node_id for node in graph.nodes if node.node_type == "promotion_packet"
    }
    audit_record_nodes = {node.node_id for node in graph.nodes if node.node_type == "audit_record"}
    reproducibility_nodes = [
        node.node_id for node in graph.nodes if node.node_type == "reproducibility"
    ]
    audit_records = [
        json.loads(line) for line in result.audit_log_path.read_text(encoding="utf-8").splitlines()
    ]

    assert selected_rows
    assert {row["promotion_candidate_id"] for row in selected_rows} <= promotion_packet_nodes
    for selected in selected_rows:
        packet = json.loads(Path(str(selected["promotion_packet_path"])).read_text())
        related_audit_record_ids = {
            row["record_id"]
            for row in audit_records
            if row["record_id"]
            in {selected["validation_audit_record_id"], packet["audit_record_id"]}
            or row["payload"].get("evidence_bundle_id") == selected["evidence_bundle_id"]
            or row["payload"].get("promotion_candidate_id") == selected["promotion_candidate_id"]
        }
        assert related_audit_record_ids <= audit_record_nodes
    assert all(Path(node_id).exists() for node_id in reproducibility_nodes)
