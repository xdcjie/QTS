from __future__ import annotations

import json
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]
from qts.core.hashing import stable_json_hash
from qts.research.artifact_graph import ResearchArtifactGraph
from qts.research.audit_log import ResearchAuditLog
from qts.research.evidence_registry import EvidenceRegistry
from qts.research.idea_spec import IdeaSpec

from scripts import run_research


def _sha256(path: Path) -> str:
    return f"sha256:{sha256(path.read_bytes()).hexdigest()}"


def _write_bundle(tmp_path: Path, *, git_dirty: bool = False) -> tuple[Path, str]:
    artifact_path = tmp_path / "metrics.json"
    artifact_path.write_text('{"sharpe": "1.2"}\n', encoding="utf-8")
    artifact_hash = _sha256(artifact_path)

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "artifact_hashes": {artifact_path.name: artifact_hash},
                "artifact_paths_by_hash": {artifact_hash: str(artifact_path)},
                "metrics": {"sharpe": "1.2"},
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
                    "backtest_config_hash": "sha256:backtest",
                    "dataset_ids": ["fixture:GC:15m"],
                    "generated_at": "2026-05-25T00:00:00+00:00",
                    "git_branch": "master",
                    "git_commit": "abc123",
                    "git_dirty": git_dirty,
                    "promotion_status": "research_only",
                    "research_config_hash": "sha256:research",
                    "research_config_path": "configs/research/quickstart.yaml",
                    "workflow_config_hash": "sha256:workflow",
                    "workflow_config_path": "configs/research/workflows/quickstart.yaml",
                },
                "periods": [
                    {
                        "end": "2022-01-01T00:00:00+00:00",
                        "name": "selection",
                        "role": "selection",
                        "start": "2020-01-01T00:00:00+00:00",
                    }
                ],
                "status": "completed",
                "steps": [
                    {
                        "id": "tearsheet",
                        "kind": "factor_tearsheet",
                        "message": "done",
                        "outputs": {"manifest_path": str(manifest_path)},
                        "status": "passed",
                    },
                    {
                        "id": "report",
                        "kind": "research_report",
                        "message": "done",
                        "outputs": {"report_path": str(report_path)},
                        "status": "passed",
                    },
                ],
                "workflow_id": "promotion-flow",
            },
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    idea = IdeaSpec(
        idea_id="idea-vwap",
        title="VWAP pullback",
        hypothesis="VWAP pullback persists after costs.",
        edge_type="mean_reversion",
        source="fixture",
        created_at=datetime(2026, 5, 25, tzinfo=UTC),
    )
    registry_root = tmp_path / "evidence"
    bundle = EvidenceRegistry(registry_root).create_from_workflow_summary(
        summary_path,
        idea=idea,
        strategy_id="vwap",
    )
    return registry_root, bundle.evidence_bundle_id


def _write_candidate(tmp_path: Path, bundle_id: str) -> Path:
    candidate_path = tmp_path / "candidate.yaml"
    candidate_path.write_text(
        f"""
promotion_candidate_id: pc-vwap
strategy_id: vwap
evidence_bundle_id: {bundle_id}
status: paper_candidate
idea_id: idea-vwap
""",
        encoding="utf-8",
    )
    return candidate_path


def _packet_payload(bundle_id: str) -> dict[str, Any]:
    metrics = {
        "execution": {
            "cost_impact": 0.01,
            "slippage_sensitivity": 0.02,
        },
        "portfolio": {"correlation_to_active": 0.3},
        "quality": {
            "profit_factor": 1.4,
            "sharpe": 1.1,
        },
        "research": {
            "deterministic_replay_passed": True,
            "no_lookahead_passed": True,
            "promotion_eligible": True,
        },
        "risk": {"max_drawdown": 0.2},
        "stability": {
            "parameter_sensitivity": 0.8,
            "walk_forward_consistency": 0.75,
        },
        "trading": {
            "oos_months": 12.0,
            "oos_trade_count": 40,
        },
    }
    data_quality = {
        "schema_version": 2,
        "dataset_id": "dataset-001",
        "accepted": True,
        "checked_paths": [],
        "issues": [],
        "duplicate_timestamps": 0,
        "missing_bars": 0,
        "session_alignment": True,
        "stale_prices": 0,
        "halted_sessions": 0,
        "label_visibility": True,
    }
    reproducibility = {
        "schema_version": 2,
        "git_sha": "abc123",
        "git_dirty": False,
        "python_version": "3.13.0",
        "platform": "macOS",
        "manifest_hash": "sha256:manifest",
        "dependency_hashes": {"uv.lock": "sha256:deps"},
        "config_hashes": {"research.yaml": "sha256:config"},
        "data_hashes": {"dataset.parquet": "sha256:data"},
        "command_argv": ["--config", "research.yaml"],
        "random_seeds": {"python": 7},
        "calendar_version": "XNYS-2026a",
        "container_digest": None,
    }
    return {
        "schema_version": 2,
        "promotion_candidate_id": "pc-vwap",
        "target_mode": "paper_simulated",
        "strategy_id": "vwap",
        "source_module": "strategies.research.vwap",
        "target_module": "strategies.production.vwap",
        "idea_id": "idea-vwap",
        "evidence_bundle_id": bundle_id,
        "metrics": {
            "metrics_schema_id": "schema_v2",
            "payload_hash": stable_json_hash(metrics),
            "payload": metrics,
        },
        "data_quality": {
            "artifact_id": "dq-dataset-001",
            "payload_hash": stable_json_hash(data_quality),
            "payload": data_quality,
        },
        "reproducibility": {
            "snapshot_id": "repro-001",
            "payload_hash": stable_json_hash(reproducibility),
            "payload": reproducibility,
        },
        "runtime": {
            "account_id": "paper-account",
            "risk_profile_id": "risk-paper",
            "capital_limit": 100000,
            "runtime_mode": "paper_simulated",
            "kill_switch_profile": "paper-kill-switch",
        },
        "operations": {
            "rollback_plan": "disable promoted strategy module",
            "monitoring_plan": "watch fills and reconciliation",
            "alert_policy": "page operator on kill-switch trigger",
        },
        "review": {
            "reviewer": "risk",
            "decision": "go",
            "reviewed_at": "2026-05-26T00:00:00+00:00",
        },
    }


def _write_packet(tmp_path: Path, bundle_id: str, *, valid: bool = True) -> tuple[Path, str]:
    payload = _packet_payload(bundle_id)
    if not valid:
        payload["target_module"] = "strategies.production_evil.vwap"
    packet_path = tmp_path / "packet.yaml"
    packet_path.write_text(yaml.safe_dump(payload, sort_keys=True), encoding="utf-8")
    return packet_path, stable_json_hash(payload)


def test_run_research_promotion_validate_accepts_complete_bundle(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    registry_root, bundle_id = _write_bundle(tmp_path)
    candidate_path = _write_candidate(tmp_path, bundle_id)

    exit_code = run_research.main(
        [
            "promotion",
            "validate",
            "--candidate",
            str(candidate_path),
            "--evidence-registry-root",
            str(registry_root),
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["accepted"] is True
    assert payload["status"] == "accepted"
    assert payload["reasons"] == []


def test_run_research_promotion_validate_rejects_dirty_bundle(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    registry_root, bundle_id = _write_bundle(tmp_path, git_dirty=True)
    candidate_path = _write_candidate(tmp_path, bundle_id)

    exit_code = run_research.main(
        [
            "promotion",
            "validate",
            "--candidate",
            str(candidate_path),
            "--evidence-registry-root",
            str(registry_root),
        ]
    )

    assert exit_code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["accepted"] is False
    assert "git_dirty must be false, got True" in payload["reasons"]


def test_run_research_promotion_validate_accepts_packet_and_writes_audit_log(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    registry_root, bundle_id = _write_bundle(tmp_path)
    packet_path, packet_hash = _write_packet(tmp_path, bundle_id)
    audit_log_root = tmp_path / "audit"

    exit_code = run_research.main(
        [
            "promotion",
            "validate",
            "--packet",
            str(packet_path),
            "--evidence-registry-root",
            str(registry_root),
            "--audit-log-root",
            str(audit_log_root),
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["accepted"] is True
    assert payload["status"] == "accepted"
    assert payload["packet_hash"] == packet_hash
    assert payload["audit_record_id"]
    assert payload["reasons"] == []
    assert payload["warnings"] == []
    audit_log = ResearchAuditLog(audit_log_root)
    assert audit_log.path.exists()
    assert audit_log.verify_hash_chain() == ()


def test_run_research_promotion_validate_packet_writes_artifact_graph(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    registry_root, bundle_id = _write_bundle(tmp_path)
    packet_path, _packet_hash = _write_packet(tmp_path, bundle_id)
    graph_root = tmp_path / "graphs"

    exit_code = run_research.main(
        [
            "promotion",
            "validate",
            "--packet",
            str(packet_path),
            "--evidence-registry-root",
            str(registry_root),
            "--audit-log-root",
            str(tmp_path / "audit"),
            "--artifact-graph-root",
            str(graph_root),
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    graph_path = graph_root / "promotion-packet-pc-vwap-artifact-graph.json"
    assert graph_path.exists()
    graph = ResearchArtifactGraph.from_payload(json.loads(graph_path.read_text(encoding="utf-8")))
    graph.validate()
    assert payload["audit_record_id"] in {node.node_id for node in graph.nodes}


def test_run_research_promotion_validate_rejects_invalid_packet(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    registry_root, bundle_id = _write_bundle(tmp_path)
    packet_path, _packet_hash = _write_packet(tmp_path, bundle_id, valid=False)

    exit_code = run_research.main(
        [
            "promotion",
            "validate",
            "--packet",
            str(packet_path),
            "--evidence-registry-root",
            str(registry_root),
            "--audit-log-root",
            str(tmp_path / "audit"),
        ]
    )

    assert exit_code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["accepted"] is False
    assert "target_module must start with strategies.production." in payload["reasons"]


def test_run_research_promotion_validate_requires_candidate_or_packet() -> None:
    with pytest.raises(SystemExit) as excinfo:
        run_research.main(["promotion", "validate"])

    assert excinfo.value.code == 2


def test_run_research_promotion_validate_rejects_candidate_and_packet(
    tmp_path: Path,
) -> None:
    registry_root, bundle_id = _write_bundle(tmp_path)
    candidate_path = _write_candidate(tmp_path, bundle_id)
    packet_path, _packet_hash = _write_packet(tmp_path, bundle_id)

    with pytest.raises(SystemExit) as excinfo:
        run_research.main(
            [
                "promotion",
                "validate",
                "--candidate",
                str(candidate_path),
                "--packet",
                str(packet_path),
                "--evidence-registry-root",
                str(registry_root),
            ]
        )

    assert excinfo.value.code == 2
