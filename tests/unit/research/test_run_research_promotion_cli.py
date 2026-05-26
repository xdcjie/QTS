from __future__ import annotations

import json
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

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


def test_run_research_promotion_validate_accepts_complete_bundle(
    tmp_path: Path,
    capsys,
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
    capsys,
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
