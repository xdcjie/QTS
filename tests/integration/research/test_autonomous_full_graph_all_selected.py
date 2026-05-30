from __future__ import annotations

import json
from pathlib import Path

from qts.research.artifact_graph import ResearchArtifactGraph

from tests.integration.research._autonomous_engine_plan_helpers import read_jsonl, run_engine


def test_final_artifact_graph_covers_every_candidate(tmp_path: Path) -> None:
    # WIRING: the final artifact graph is structurally valid and its
    # reproducibility nodes point at on-disk artifacts. HONESTY: the toy fixture
    # clears no candidate, so the graph carries no promotion_packet nodes (the
    # rejected campaign has no release sub-chain) rather than faking promotion.
    _campaign_path, result = run_engine(tmp_path)

    selected_rows = read_jsonl(result.selected_candidates_path)
    rejected_rows = read_jsonl(result.rejected_candidates_path)
    graph = ResearchArtifactGraph.from_payload(
        json.loads(result.artifact_graph_path.read_text(encoding="utf-8"))
    )
    graph.validate()
    promotion_packet_nodes = {
        node.node_id for node in graph.nodes if node.node_type == "promotion_packet"
    }
    reproducibility_nodes = [
        node.node_id for node in graph.nodes if node.node_type == "reproducibility"
    ]

    assert selected_rows == []
    assert promotion_packet_nodes == set()
    assert rejected_rows
    assert all(row["reasons"] for row in rejected_rows)
    assert all(Path(node_id).exists() for node_id in reproducibility_nodes)
