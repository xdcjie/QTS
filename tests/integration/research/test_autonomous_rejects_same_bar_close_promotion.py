"""End-to-end gate: same_bar_close evidence cannot be promoted (C1).

A promotion attempt backed by an OOS backtest that filled at the decision bar's
own close (``same_bar_close``) is optimistic look-ahead. Without an explicit
optimistic waiver it must be rejected by the promotion path.

These tests drive the REAL producer chain rather than hand-authoring the
rejection: the OOS backtest manifest carries the genuine
``execution_assumptions`` payload emitted by ``ExecutionTimingModel`` for each
policy, ``ResearchMetricsFromValidationArtifacts`` derives the research metrics
(including ``promotion_eligible`` and the fill-timing facts) from real artifacts
+ that manifest, and the assembled ``PromotionPacketV2`` is validated through
the same ``validate_machine`` call the promotion path uses. The accept/reject
outcome is therefore driven by the production fill-timing model and derivation,
not by a synthetic ``promotion_eligible`` flag.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from qts.backtest.execution_timing import ExecutionTimingModel
from qts.core.hashing import stable_json_hash
from qts.research.audit_log import ResearchAuditLog
from qts.research.evidence_registry import EvidenceRegistry
from qts.research.idea_spec import IdeaSpec
from qts.research.orchestrator.validation_artifact_reader import (
    ResearchMetricsFromValidationArtifacts,
    ValidationArtifactReader,
)
from qts.research.promotion_packet import PromotionPacketV2


def test_same_bar_close_evidence_promotion_rejected(tmp_path: Path) -> None:
    """A promotion packet backed by unwaived same_bar_close fills is rejected."""
    result = _validate_promotion_for_policy(tmp_path, ExecutionTimingModel.research_only())

    assert result.accepted is False
    assert result.optimistic is False
    # The rejection is driven by the fill-timing fact, not a synthetic flag.
    assert any(
        "fill_timing_promotion_grade is False" in reason for reason in result.reasons
    ) or any("promotion_eligible must be true" in reason for reason in result.reasons)


def test_next_bar_open_evidence_promotion_accepted(tmp_path: Path) -> None:
    """The same evidence is promotable when the OOS fills are next_bar_open."""
    result = _validate_promotion_for_policy(tmp_path, ExecutionTimingModel.promotion_grade())

    assert result.accepted is True
    assert result.optimistic is False


def test_waived_same_bar_close_promotion_accepted_but_optimistic(tmp_path: Path) -> None:
    """An explicit optimistic waiver allows promotion but the packet stays optimistic."""
    result = _validate_promotion_for_policy(
        tmp_path,
        ExecutionTimingModel.research_only(optimistic_waiver=True),
    )

    assert result.accepted is True
    assert result.optimistic is True
    assert result.to_payload()["optimistic"] is True


# ---------------------------------------------------------------------------
# Real-producer evidence assembly
# ---------------------------------------------------------------------------


def _validate_promotion_for_policy(
    tmp_path: Path,
    timing: ExecutionTimingModel,
) -> Any:
    """Derive metrics from real artifacts + the policy's manifest, then validate.

    The only thing that varies between the three cases is the OOS manifest's
    ``execution_assumptions`` payload, which is taken verbatim from the
    production ``ExecutionTimingModel.to_manifest_payload()``.
    """
    artifact_dir = tmp_path / "trial"
    _write_all_passing_artifacts(artifact_dir)
    reader = ValidationArtifactReader(artifact_dir)

    oos_manifest = {
        "manifest_hash": "sha256:oos-manifest",
        "statistics": {"sharpe_ratio": 1.0},
        "execution_assumptions": timing.to_manifest_payload(),
    }
    train_manifest = {
        "manifest_hash": "sha256:train-manifest",
        "statistics": {"sharpe_ratio": 1.2},
        "execution_assumptions": timing.to_manifest_payload(),
    }
    twelve_month_oos = {
        "periods": [
            {
                "start": "2021-01-01T00:00:00+00:00",
                "end": "2022-01-01T00:00:00+00:00",
                "name": "oos",
                "role": "oos",
            }
        ]
    }
    derivation = ResearchMetricsFromValidationArtifacts().derive(
        reader,
        twelve_month_oos,
        train_manifest=train_manifest,
        test_manifest=oos_manifest,
    )

    metrics = _metrics_from_derivation(derivation)
    registry, bundle_id = _write_verifiable_bundle(tmp_path)
    return PromotionPacketV2.from_payload(
        _packet_payload(bundle_id, metrics_payload=metrics)
    ).validate_machine(
        evidence_registry=registry,
        audit_log=ResearchAuditLog(tmp_path / "audit.jsonl"),
    )


def _metrics_from_derivation(derivation: Any) -> dict[str, dict[str, object]]:
    """Build a v2 metrics payload from honestly-derived research metrics."""
    return {
        "execution": {"cost_impact": 0.01, "slippage_sensitivity": 0.02},
        "performance": {
            "max_drawdown": 0.2,
            "oos_manifest_hash": "sha256:oos-manifest",
            "oos_sharpe": derivation.sharpe_sources.oos_sharpe,
            "total_return": 0.15,
            "train_manifest_hash": "sha256:train-manifest",
            "train_sharpe": derivation.sharpe_sources.train_sharpe,
        },
        "portfolio": {"correlation_to_active": 0.3},
        "quality": {"profit_factor": 1.4, "sharpe": 1.1},
        "research": {
            "deterministic_replay_passed": derivation.deterministic_replay_passed,
            "fill_timing_optimistic": derivation.fill_timing_optimistic,
            "fill_timing_promotion_grade": derivation.fill_timing_promotion_grade,
            "no_lookahead_passed": derivation.no_lookahead_passed,
            "promotion_eligible": derivation.promotion_eligible,
        },
        "risk": {"max_drawdown": 0.2},
        "stability": {
            "parameter_sensitivity": derivation.parameter_sensitivity,
            "walk_forward_consistency": derivation.walk_forward_consistency,
        },
        "trading": {"oos_months": derivation.oos_months, "oos_trade_count": 40},
    }


def _write_artifact(artifact_dir: Path, artifact_name: str, payload: dict[str, Any]) -> None:
    validation_dir = artifact_dir / "validation"
    validation_dir.mkdir(parents=True, exist_ok=True)
    wrapper = {
        "artifact_id": artifact_name,
        "artifact_type": artifact_name,
        "evidence_source": "backtest_pipeline_artifact",
        "payload": payload,
        "payload_hash": stable_json_hash(payload),
    }
    (validation_dir / f"{artifact_name}.json").write_text(
        json.dumps(wrapper, sort_keys=True), encoding="utf-8"
    )


def _write_all_passing_artifacts(artifact_dir: Path) -> None:
    _write_artifact(artifact_dir, "deterministic_replay", {"passed": True})
    _write_artifact(artifact_dir, "no_lookahead", {"passed": True})
    _write_artifact(
        artifact_dir,
        "walk_forward_validation",
        {
            "consistent": True,
            "test_windows": [
                {
                    "accepted": True,
                    "train_score": 1.2,
                    "score": 1.0,
                    "train_manifest_hash": "sha256:train-hash",
                    "manifest_hash": "sha256:test-hash",
                }
            ],
        },
    )
    _write_artifact(artifact_dir, "cost_stress", {"degradation": 0.1})


def _packet_payload(
    bundle_id: str,
    *,
    target_mode: str = "paper_simulated",
    metrics_payload: dict[str, dict[str, object]],
) -> dict[str, Any]:
    return {
        "schema_version": 2,
        "promotion_candidate_id": "pc-test",
        "target_mode": target_mode,
        "strategy_id": "test",
        "source_module": "strategies.research.test",
        "target_module": "strategies.production.test",
        "idea_id": "idea-test",
        "evidence_bundle_id": bundle_id,
        "metrics": {
            "metrics_schema_id": "schema_v2",
            "payload_hash": stable_json_hash(metrics_payload),
            "payload": metrics_payload,
        },
        "data_quality": {
            "artifact_id": "dq-dataset-001",
            "payload_hash": stable_json_hash(_data_quality_payload()),
            "payload": _data_quality_payload(),
        },
        "reproducibility": {
            "snapshot_id": "repro-001",
            "payload_hash": stable_json_hash(_repro_payload()),
            "payload": _repro_payload(),
        },
        "runtime": {
            "account_id": "paper-account",
            "risk_profile_id": "risk-paper",
            "capital_limit": 100000,
            "runtime_mode": target_mode,
            "kill_switch_profile": "paper-kill-switch",
        },
        "operations": {
            "rollback_plan": "disable promoted strategy module",
            "monitoring_plan": "watch fills",
            "alert_policy": "page operator",
        },
        "review": {},
    }


def _data_quality_payload() -> dict[str, Any]:
    return {
        "schema_version": 2,
        "dataset_id": "dataset-001",
        "accepted": True,
        "checked_paths": ["datasets/dataset-001/bars.csv"],
        "issues": [],
        "duplicate_timestamps": 0,
        "missing_bars": 0,
        "session_alignment": True,
        "stale_prices": 0,
        "halted_sessions": 0,
        "label_visibility": True,
    }


def _repro_payload() -> dict[str, Any]:
    return {
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


def _write_verifiable_bundle(tmp_path: Path) -> tuple[EvidenceRegistry, str]:
    artifact_path = tmp_path / "metrics.json"
    artifact_path.write_text('{"sharpe": "1.2"}\n', encoding="utf-8")
    artifact_hash = f"sha256:{hashlib.sha256(artifact_path.read_bytes()).hexdigest()}"

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
                    "dataset_ids": ["fixture:GC:15m"],
                    "git_commit": "abc123",
                    "git_dirty": False,
                    "research_config_hash": "sha256:research",
                    "workflow_config_hash": "sha256:workflow",
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
                        "outputs": {"manifest_path": str(manifest_path)},
                        "status": "passed",
                    },
                    {
                        "id": "report",
                        "kind": "research_report",
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
        idea_id="idea-test",
        title="Test strategy",
        hypothesis="Test hypothesis.",
        edge_type="mean_reversion",
        source="fixture",
        created_at=datetime(2026, 5, 25, tzinfo=UTC),
    )
    registry = EvidenceRegistry(tmp_path / "evidence")
    bundle = registry.create_from_workflow_summary(
        summary_path,
        idea=idea,
        strategy_id="test",
    )
    return registry, bundle.evidence_bundle_id
