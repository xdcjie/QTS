from __future__ import annotations

import json
from pathlib import Path

from qts.research.artifact_graph import ResearchArtifactGraph

from tests.integration.research._autonomous_engine_plan_helpers import read_jsonl, run_engine


def test_engine_records_strategy_variant_hash_in_artifact_graph(tmp_path: Path) -> None:
    _, result = run_engine(
        tmp_path,
        families=("momentum",),
        max_trials_per_generation=3,
        max_total_trials=3,
    )

    selected = read_jsonl(result.selected_candidates_path)[0]
    graph = ResearchArtifactGraph.from_payload(
        json.loads(result.artifact_graph_path.read_text(encoding="utf-8"))
    )

    variant_nodes = [
        node
        for node in graph.nodes
        if node.node_type == "strategy_variant" and node.node_id == selected["strategy_variant_id"]
    ]
    assert variant_nodes
    assert variant_nodes[0].payload_hash == selected["strategy_variant_hash"]
    assert any(
        edge.source_id == selected["promotion_candidate_id"]
        and edge.target_id == selected["strategy_variant_id"]
        for edge in graph.edges
    )
