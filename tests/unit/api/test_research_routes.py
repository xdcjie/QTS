from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from qts.research.registry import ResearchRunRecord, ResearchRunRegistry


def _auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer dev-token"}


def test_research_dashboard_routes_list_filter_and_compare_runs(tmp_path: Path) -> None:
    from fastapi.testclient import TestClient
    from qts.api.app import create_app

    experiment_root = tmp_path / "experiments"
    manifest_a = _write_manifest(
        experiment_root / "exp-a.json",
        experiment_id="exp-a",
        strategy_name="VWAP Pullback",
        idea_id="idea-vwap",
        metrics={"total_return": 0.12, "sharpe": 1.4},
    )
    manifest_b = _write_manifest(
        experiment_root / "exp-b.json",
        experiment_id="exp-b",
        strategy_name="Mean Reversion",
        idea_id="idea-mean",
        metrics={"total_return": 0.05, "sharpe": 0.8},
    )
    _write_experiment_index(
        experiment_root,
        [
            {
                "experiment_id": "exp-a",
                "manifest_path": str(manifest_a),
                "recorded_at": datetime(2026, 5, 26, 10, tzinfo=UTC).isoformat(),
                "platform_baseline_version": "baseline",
                "strategy_name": "VWAP Pullback",
                "strategy_version": "1",
                "factor_versions": {"vwap": "1"},
                "dataset_ids": ["gc-rth"],
                "config_hash": "cfg-a",
                "artifact_hashes": {"report": "hash-a"},
                "metrics": {"total_return": 0.12, "sharpe": 1.4},
                "idea_id": "idea-vwap",
            },
            {
                "experiment_id": "exp-b",
                "manifest_path": str(manifest_b),
                "recorded_at": datetime(2026, 5, 25, 10, tzinfo=UTC).isoformat(),
                "platform_baseline_version": "baseline",
                "strategy_name": "Mean Reversion",
                "strategy_version": "1",
                "factor_versions": {},
                "dataset_ids": ["spy-daily"],
                "config_hash": "cfg-b",
                "artifact_hashes": {},
                "metrics": {"total_return": 0.05, "sharpe": 0.8},
                "idea_id": "idea-mean",
            },
        ],
    )

    app = create_app()
    app.state.research_experiment_store_root = experiment_root
    client = TestClient(app)

    runs = client.get(
        "/backtests/research/runs?strategy_name=VWAP",
        headers=_auth_headers(),
    )
    comparison = client.get(
        "/backtests/research/compare",
        params={"left_run_id": "exp-a", "right_run_id": "exp-b", "metric": "total_return"},
        headers=_auth_headers(),
    )

    assert runs.status_code == 200
    assert [run["run_id"] for run in runs.json()] == ["exp-a"]
    assert runs.json()[0]["metrics"]["sharpe"] == 1.4
    assert comparison.status_code == 200
    assert comparison.json() == {
        "left_run_id": "exp-a",
        "right_run_id": "exp-b",
        "metric": "total_return",
        "left_value": 0.12,
        "right_value": 0.05,
        "delta": 0.06999999999999999,
    }


def test_research_dashboard_routes_list_and_compare_manifest_registry_runs(
    tmp_path: Path,
) -> None:
    from fastapi.testclient import TestClient
    from qts.api.app import create_app

    artifact_root = tmp_path / "research"
    run_dir = artifact_root / "gc-si-smoke-dry-run"
    run_dir.mkdir(parents=True)
    (run_dir / "manifest.yaml").write_text("run:\n  id: gc-si-smoke-dry-run\n", encoding="utf-8")
    (run_dir / "resolved_manifest.json").write_text(
        json.dumps(
            {
                "data": {"dataset_id": "research_futures_gc_si_1m"},
                "run": {
                    "id": "gc-si-smoke-dry-run",
                    "question": "Does GC/SI momentum have enough evidence?",
                },
                "strategy": {
                    "entrypoint": "examples.strategies.gc_si_momentum:GcSiMomentumStrategy",
                    "id": "gc_si_momentum",
                },
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    (run_dir / "metrics.json").write_text(
        json.dumps(
            {
                "quality": {"sharpe": 1.25},
                "research": {"candidate_count": 4},
                "return": {"total_return": 0.08},
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    ResearchRunRegistry.from_root(artifact_root).append(
        ResearchRunRecord(
            run_id="gc-si-smoke-dry-run",
            manifest_hash="sha256:manifest",
            artifact_dir=run_dir,
            status="dry_run",
            promotion_status="rejected",
            recorded_at=datetime(2026, 5, 26, 11, tzinfo=UTC),
        )
    )

    app = create_app()
    app.state.research_artifact_root = artifact_root
    client = TestClient(app)

    runs = client.get(
        "/backtests/research/runs?strategy_name=gc_si&status=rejected",
        headers=_auth_headers(),
    )
    comparison = client.get(
        "/backtests/research/compare",
        params={
            "left_run_id": "gc-si-smoke-dry-run",
            "right_run_id": "gc-si-smoke-dry-run",
            "metric": "candidate_count",
        },
        headers=_auth_headers(),
    )

    assert runs.status_code == 200
    assert runs.json()[0]["run_id"] == "gc-si-smoke-dry-run"
    assert runs.json()[0]["metrics"]["quality.sharpe"] == 1.25
    assert runs.json()[0]["metrics"]["sharpe"] == 1.25
    assert runs.json()[0]["metrics"]["promotion_status"] == "rejected"
    assert comparison.status_code == 200
    assert comparison.json()["left_value"] == 4.0
    assert comparison.json()["delta"] == 0.0


def test_research_dashboard_routes_expose_reports_decisions_and_lifecycle(
    tmp_path: Path,
) -> None:
    from fastapi.testclient import TestClient
    from qts.api.app import create_app

    evidence_root = tmp_path / "evidence"
    report_path = tmp_path / "reports" / "workflow.md"
    report_path.parent.mkdir(parents=True)
    report_path.write_text("# Research Workflow Report\n\nAccepted evidence.\n", encoding="utf-8")
    bundle = {
        "artifact_hashes": {},
        "artifact_paths": {},
        "dataset_ids": ["gc-rth"],
        "evidence_bundle_id": "bundle-a",
        "git_commit": "abc123",
        "git_dirty": False,
        "idea_id": "idea-vwap",
        "idea_metadata": {},
        "manifest_hashes": {},
        "manifest_paths": [],
        "period_roles": {"selection": "in_sample"},
        "promotion_eligibility": "not_reviewed",
        "report_hash": "report-hash",
        "report_path": str(report_path),
        "research_config_hash": "research-cfg",
        "status": "research_evidence_only",
        "strategy_id": "vwap_pullback",
        "trial_budget_warnings": [],
        "workflow_config_hash": "workflow-cfg",
        "workflow_run_id": "workflow-a",
        "workflow_summary_hash": "summary-hash",
        "workflow_summary_path": str(tmp_path / "summary.json"),
    }
    evidence_root.mkdir(parents=True)
    (evidence_root / "index.jsonl").write_text(json.dumps(bundle) + "\n", encoding="utf-8")

    idea_root = tmp_path / "ideas"
    idea_root.mkdir()
    (idea_root / "ideas.yaml").write_text(
        """
ideas:
  - idea_id: idea-vwap
    title: VWAP Pullback
    hypothesis: intraday pullback
    status: validated_research
    edge_types: [mean_reversion]
    source: research
    created_at: "2026-05-26T00:00:00+00:00"
""",
        encoding="utf-8",
    )

    promotion_root = tmp_path / "promotion"
    promotion_root.mkdir()
    (promotion_root / "vwap.yaml").write_text(
        """
promotion_candidate_id: pc-vwap
strategy_id: vwap_pullback
source_module: strategies.research.vwap
target_module: strategies.production.vwap
evidence_bundle_id: bundle-a
status: review_required
paper_readiness:
  evidence_bundle_verified: true
""",
        encoding="utf-8",
    )

    readiness_root = tmp_path / "readiness"
    readiness_path = (
        readiness_root / "vwap_pullback" / "2026-05-26" / "paper_live_gate_decision.json"
    )
    readiness_path.parent.mkdir(parents=True)
    readiness_path.write_text(
        json.dumps(
            {
                "strategy_id": "vwap_pullback",
                "decision_date": "2026-05-26",
                "target_status": "paper_candidate",
                "paper_live_readiness_gate": "needs_more_evidence",
            }
        ),
        encoding="utf-8",
    )

    app = create_app()
    app.state.research_evidence_root = evidence_root
    app.state.research_idea_registry_root = idea_root
    app.state.research_promotion_root = promotion_root
    app.state.research_readiness_root = readiness_root
    client = TestClient(app)

    report = client.get("/backtests/research/reports/bundle-a", headers=_auth_headers())
    decisions = client.get("/backtests/research/promotion-decisions", headers=_auth_headers())
    lifecycle = client.get("/backtests/research/lifecycle", headers=_auth_headers())

    assert report.status_code == 200
    assert report.json()["report_preview"].startswith("# Research Workflow Report")
    assert "review_decisions" not in report.json()
    assert decisions.status_code == 200
    assert {item["source"] for item in decisions.json()} == {
        "promotion_candidate",
        "readiness_gate",
    }
    assert all(item["source"] != "evidence_review" for item in decisions.json())
    assert lifecycle.status_code == 200
    assert lifecycle.json() == [
        {
            "strategy_id": "vwap_pullback",
            "idea_id": "idea-vwap",
            "lifecycle_status": "validated_research",
            "promotion_status": "review_required",
            "latest_readiness_status": "paper_candidate",
        }
    ]


def _write_manifest(
    path: Path,
    *,
    experiment_id: str,
    strategy_name: str,
    idea_id: str,
    metrics: dict[str, float],
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "experiment_id": experiment_id,
                "strategy_name": strategy_name,
                "idea_id": idea_id,
                "metrics": metrics,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return path


def _write_experiment_index(root: Path, records: list[dict[str, object]]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    root.joinpath("experiments.jsonl").write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )
