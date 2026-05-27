from __future__ import annotations

import json
from pathlib import Path

from qts.research import (
    ReproducibilitySnapshot,
    ResearchArtifactGraph,
    ResearchDryRunRunner,
    ResearchManifest,
    ResearchMetrics,
    ResearchPromotionPolicy,
    ResearchRunRegistry,
)
from qts.research.registry import new_record


def test_manifest_loads_and_expands_deterministic_candidate_ids() -> None:
    manifest = ResearchManifest.from_yaml("configs/research/backtest_gc_si_smoke.yaml")

    candidates = manifest.candidates()
    second_load = ResearchManifest.from_yaml("configs/research/backtest_gc_si_smoke.yaml")

    assert manifest.run_id == "gc-si-smoke-dry-run"
    assert len(candidates) == 6
    assert [candidate.candidate_id for candidate in candidates] == [
        candidate.candidate_id for candidate in second_load.candidates()
    ]
    assert candidates[0].parameters == {"long_window": 2, "short_window": 1}
    assert [candidate.search_type for candidate in candidates].count("grid") == 4
    assert [candidate.search_type for candidate in candidates].count("random") == 2


def test_manifest_random_search_is_deterministic() -> None:
    manifest = ResearchManifest.from_yaml("configs/research/backtest_gc_si_smoke.yaml")

    random_candidates = [
        candidate for candidate in manifest.candidates() if candidate.search_type == "random"
    ]

    assert [candidate.parameters for candidate in random_candidates] == [
        {"long_window": 4, "short_window": 2},
        {"long_window": 3, "short_window": 2},
    ]


def test_research_registry_appends_jsonl_records(tmp_path: Path) -> None:
    registry = ResearchRunRegistry(tmp_path / "index.jsonl")
    record = new_record(
        run_id="run-001",
        manifest_hash="sha256:abc",
        artifact_dir=tmp_path / "run-001",
        status="dry_run",
        promotion_status="rejected",
    )

    registry.append(record)

    rows = registry.list()
    assert len(rows) == 1
    assert rows[0].run_id == "run-001"
    assert rows[0].promotion_status == "rejected"


def test_promotion_policy_rejects_missing_oos_metrics_and_warns_dirty() -> None:
    policy = ResearchPromotionPolicy.from_yaml(Path("configs/promotion/default.yaml"))
    metrics = ResearchMetrics.dry_run(candidate_count=2).to_payload()

    decision = policy.evaluate(
        run_id="run-001",
        strategy_id="gc_si_momentum",
        metrics=metrics,
        reproducibility={"git_dirty": True},
    )

    assert decision.status == "rejected"
    assert "git worktree was dirty during research run" in decision.warnings
    assert any(gate.status == "missing" for gate in decision.gates)


def test_promotion_policy_accepts_complete_research_metrics() -> None:
    policy = ResearchPromotionPolicy.from_yaml(Path("configs/promotion/default.yaml"))
    metrics = ResearchMetrics.dry_run(candidate_count=2).to_payload()
    metrics["trading"]["oos_months"] = 12
    metrics["trading"]["oos_trade_count"] = 40
    metrics["quality"]["sharpe"] = 1.2
    metrics["quality"]["profit_factor"] = 1.3
    metrics["risk"]["max_drawdown"] = 0.1
    metrics["execution"]["cost_impact"] = 0.01
    metrics["execution"]["slippage_sensitivity"] = 0.02
    metrics["stability"]["parameter_sensitivity"] = 0.8
    metrics["stability"]["walk_forward_consistency"] = 0.75
    metrics["portfolio"]["correlation_to_active"] = 0.3
    metrics["research"]["deterministic_replay_passed"] = True
    metrics["research"]["no_lookahead_passed"] = True
    metrics["research"]["promotion_eligible"] = True

    decision = policy.evaluate(
        run_id="run-001",
        strategy_id="gc_si_momentum",
        metrics=metrics,
        reproducibility={"git_dirty": False},
    )

    assert decision.status == "research_passed"
    assert all(gate.status == "passed" for gate in decision.gates)


def test_reproducibility_snapshot_round_trips_manifest_hash() -> None:
    snapshot = ReproducibilitySnapshot(
        git_sha="abc",
        git_dirty=True,
        python_version="3.13.0",
        platform="test",
        manifest_hash="sha256:manifest",
    )

    assert ReproducibilitySnapshot.from_payload(snapshot.to_payload()) == snapshot


def test_dry_run_writes_complete_plan_artifacts(tmp_path: Path) -> None:
    config = ResearchManifest.from_yaml("configs/research/backtest_gc_si_smoke.yaml")
    rewritten = _write_tmp_manifest(tmp_path, config)

    result = ResearchDryRunRunner(repo_root=Path.cwd()).run(
        rewritten,
        argv=["--config", str(rewritten), "--dry-run"],
    )

    artifact_dir = result.artifact_dir
    expected_files = {
        "candidate_parameters.jsonl",
        "candidate_results.jsonl",
        "command_log.jsonl",
        "data_quality.json",
        "data_quality_report.md",
        "data_snapshot.json",
        "artifact_graph.json",
        "failures.jsonl",
        "manifest.yaml",
        "metrics.json",
        "promotion_decision.json",
        "ranking.csv",
        "report.md",
        "reproducibility.json",
        "reproducibility_v2.json",
        "resolved_manifest.json",
        "splits.json",
    }
    assert expected_files <= {path.name for path in artifact_dir.iterdir()}
    metrics = json.loads((artifact_dir / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["research"]["promotion_eligible"] is False
    reproducibility_v2 = json.loads(
        (artifact_dir / "reproducibility_v2.json").read_text(encoding="utf-8")
    )
    assert reproducibility_v2["schema_version"] == 2
    assert "pyproject.toml" in reproducibility_v2["dependency_hashes"]
    assert "uv.lock" in reproducibility_v2["dependency_hashes"]
    assert str(rewritten) in reproducibility_v2["config_hashes"]
    data_quality = json.loads((artifact_dir / "data_quality.json").read_text(encoding="utf-8"))
    assert data_quality["schema_version"] == 2
    assert data_quality["dataset_id"] == config.dataset_id
    graph = ResearchArtifactGraph.from_payload(
        json.loads((artifact_dir / "artifact_graph.json").read_text(encoding="utf-8"))
    )
    graph.validate()
    node_types = {node.node_type for node in graph.nodes}
    assert {"manifest", "metrics", "data_quality", "reproducibility"} <= node_types
    decision = json.loads((artifact_dir / "promotion_decision.json").read_text(encoding="utf-8"))
    assert decision["status"] == "rejected"
    assert ResearchRunRegistry(result.registry_path).list()[0].run_id == result.run_id


def _write_tmp_manifest(tmp_path: Path, config: ResearchManifest) -> Path:
    path = tmp_path / "research.yaml"
    payload = config.to_payload()
    payload["output_root"] = str(tmp_path / "artifacts" / "research")
    # Keep a fixed, valid split plan but isolate generated artifacts under tmp_path.
    path.write_text(
        "\n".join(
            [
                "run:",
                f"  id: {payload['run']['id']}",
                f"  question: {payload['run']['question']}",
                "strategy:",
                f"  id: {payload['strategy']['id']}",
                f"  entrypoint: {payload['strategy']['entrypoint']}",
                f"  hypothesis: {payload['strategy']['hypothesis']}",
                f"  default_config: {payload['strategy']['default_config']}",
                "data:",
                f"  dataset_id: {payload['data']['dataset_id']}",
                f"  config: {payload['data']['config']}",
                f"  catalog: {payload['data']['catalog']}",
                "  roots: [GC, SI]",
                f"  timeframe: {payload['data']['timeframe']}",
                f'  start: "{payload["data"]["start"]}"',
                f'  end: "{payload["data"]["end"]}"',
                "parameter_grid:",
                "  short_window: [1, 2]",
                "  long_window: [2, 3]",
                f"promotion_config: {payload['promotion_config']}",
                f"output_root: {payload['output_root']}",
                "splits:",
                "  windows:",
                "    - {name: train, role: in_sample, start: '2010-06-06', end: '2010-06-07'}",
                "    - name: validation",
                "      role: validation",
                "      start: '2010-06-07'",
                "      end: '2010-06-08'",
                "    - {name: oos, role: out_of_sample, start: '2010-06-08', end: '2010-06-09'}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path
