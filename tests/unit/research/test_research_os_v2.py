from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from qts.research.audit_log import ResearchAuditLog
from qts.research.data_check import ResearchDataCheck
from qts.research.evidence_policy import validate_review_packet_payload
from qts.research.evidence_registry import EvidenceRegistry
from qts.research.idea_spec import IdeaSpec
from qts.research.metrics_schema import ResearchMetricsSchema
from qts.research.reproducibility import ReproducibilitySnapshotV2


def _sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _metrics() -> dict[str, object]:
    return {
        "execution": {"cost_impact": 0.01, "slippage_sensitivity": 0.02},
        "portfolio": {"correlation_to_active": 0.1},
        "quality": {"profit_factor": 1.3, "sharpe": 1.2},
        "research": {"deterministic_replay_passed": True, "no_lookahead_passed": True},
        "risk": {"max_drawdown": 0.1},
        "stability": {"parameter_sensitivity": 0.8, "walk_forward_consistency": 0.7},
        "trading": {"oos_months": 12, "oos_trade_count": 40},
    }


def _repro() -> dict[str, object]:
    return {
        "command_argv": ["run_research"],
        "config_hashes": {"research.yaml": "sha256:cfg"},
        "data_hashes": {"data.csv": "sha256:data"},
        "dependency_hashes": {"pyproject.toml": "sha256:dep"},
        "git_dirty": False,
        "git_sha": "abc123",
        "manifest_hash": "sha256:manifest",
        "platform": "test",
        "python_version": "3.13.0",
        "random_seeds": {"search": 7},
        "schema_version": 2,
    }


def _write_bundle(tmp_path: Path) -> tuple[EvidenceRegistry, str]:
    artifact_path = tmp_path / "metrics.json"
    artifact_path.write_text('{"sharpe": "1.2"}\n', encoding="utf-8")
    artifact_hash = _sha256(artifact_path)
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "artifact_hashes": {"metrics.json": artifact_hash},
                "artifact_paths_by_hash": {artifact_hash: str(artifact_path)},
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    report_path = tmp_path / "workflow-report.md"
    report_path.write_text("# Report\n", encoding="utf-8")
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
                    {"name": "selection", "role": "selection", "start": "2020", "end": "2021"}
                ],
                "steps": [
                    {"outputs": {"manifest_path": str(manifest_path)}},
                    {"outputs": {"report_path": str(report_path)}},
                ],
                "workflow_id": "wf",
            },
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    idea = IdeaSpec(
        idea_id="idea-vwap",
        title="VWAP",
        hypothesis="VWAP pullback persists.",
        edge_type="mean_reversion",
        source="fixture",
        created_at=datetime(2026, 5, 25, tzinfo=UTC),
    )
    registry = EvidenceRegistry(tmp_path / "evidence")
    bundle = registry.create_from_workflow_summary(summary_path, idea=idea, strategy_id="vwap")
    return registry, bundle.evidence_bundle_id


def test_audit_log_appends_and_verifies_hash_chain(tmp_path: Path) -> None:
    log = ResearchAuditLog(tmp_path / "audit")
    first = log.append(record_type="evidence_validated", payload={"accepted": True})
    second = log.append(record_type="promotion_validated", payload={"accepted": False})

    assert second.previous_payload_hash == first.payload_hash
    assert log.verify() == ()


def test_metrics_schema_v2_rejects_missing_required_metric() -> None:
    metrics = _metrics()
    del metrics["quality"]

    assert "quality.profit_factor is required" in ResearchMetricsSchema.default_v2().validate(metrics)


def test_reproducibility_v2_blocks_dirty_git() -> None:
    payload = _repro()
    payload["git_dirty"] = True

    blockers = ReproducibilitySnapshotV2.from_payload(payload).promotion_blockers()

    assert "git_dirty must be false, got True" in blockers


def test_data_check_blocks_missing_dataset_file() -> None:
    check = ResearchDataCheck.from_dataset_files(
        dataset_id="fixture",
        dataset_files=[{"exists": False, "path": "missing.csv", "reason": "missing"}],
    )

    assert not check.accepted
    assert check.blockers() == ("missing_file: missing",)


def test_review_packet_payload_validates_and_writes_audit_record(tmp_path: Path) -> None:
    registry, bundle_id = _write_bundle(tmp_path)
    data_check = ResearchDataCheck.from_dataset_files(
        dataset_id="fixture",
        dataset_files=[{"exists": True, "path": "data.csv"}],
    )
    packet = {
        "schema_version": 2,
        "promotion_candidate_id": "pc-vwap",
        "target_mode": "paper_simulated",
        "strategy_id": "vwap",
        "source_module": "strategies.research.vwap",
        "target_module": "strategies.production.vwap",
        "evidence_bundle_id": bundle_id,
        "idea_id": "idea-vwap",
        "metrics": _metrics(),
        "reproducibility": _repro(),
        "data_check": data_check.to_payload(),
    }

    result = validate_review_packet_payload(
        packet,
        evidence_registry=registry,
        audit_log=ResearchAuditLog(tmp_path / "audit"),
    )

    assert result["accepted"] is True
    assert result["audit_record_id"]
