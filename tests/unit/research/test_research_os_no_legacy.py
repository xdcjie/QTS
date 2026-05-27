from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml  # type: ignore[import-untyped]
from qts.research.audit_log import ResearchAuditLog, ResearchAuditRecord
from qts.research.evidence_registry import EvidenceRegistry, ResearchEvidenceBundle
from qts.research.manifest import ResearchManifest, ResearchManifestV2
from qts.research.system_run import ResearchDryRunRunner

from scripts import run_research


def test_promotion_validate_rejects_candidate_argument(
    tmp_path: Path,
) -> None:
    candidate_path = tmp_path / "candidate.yaml"
    candidate_path.write_text(
        """
promotion_candidate_id: pc-legacy
strategy_id: legacy
evidence_bundle_id: evb_legacy
""",
        encoding="utf-8",
    )

    with pytest.raises(SystemExit) as excinfo:
        run_research.main(
            [
                "promotion",
                "validate",
                "--candidate",
                str(candidate_path),
                "--evidence-registry-root",
                str(tmp_path / "evidence"),
            ]
        )

    assert excinfo.value.code == 2


def test_dry_run_rejects_manifest_v1_for_canonical_research_os(tmp_path: Path) -> None:
    manifest = ResearchManifest.from_yaml("configs/research/backtest_gc_si_smoke.yaml")
    manifest_path = _write_manifest_v1(tmp_path, manifest)

    with pytest.raises(ValueError, match="Research OS v1.0 requires schema_version=2"):
        ResearchDryRunRunner(repo_root=Path.cwd()).run(
            manifest_path,
            argv=["--config", str(manifest_path), "--dry-run"],
        )


def test_manifest_validate_cli_rejects_v1_manifest(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manifest = ResearchManifest.from_yaml("configs/research/backtest_gc_si_smoke.yaml")
    manifest_path = _write_manifest_v1(tmp_path, manifest)

    exit_code = run_research.main(["manifest", "validate", "--manifest", str(manifest_path)])

    assert exit_code == 2
    assert "schema_version=2" in capsys.readouterr().err


def test_manifest_validate_cli_accepts_v2_manifest(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manifest_path = _write_manifest_v2(tmp_path)

    exit_code = run_research.main(["manifest", "validate", "--manifest", str(manifest_path)])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["accepted"] is True
    assert payload["audit_record_id"]
    assert payload["schema_version"] == 2
    assert payload["manifest_hash"] == ResearchManifestV2.from_yaml(manifest_path).manifest_hash


def test_manifest_validate_graph_write_records_audit_with_default_root(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manifest_path = _write_manifest_v2(tmp_path)

    exit_code = run_research.main(
        [
            "manifest",
            "validate",
            "--manifest",
            str(manifest_path),
            "--artifact-graph-root",
            str(tmp_path / "graphs"),
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["audit_record_id"]
    assert payload["artifact_graph_hash"]


def test_promotion_candidate_spec_is_not_public_canonical_boundary() -> None:
    import qts.research as research
    import qts.research.promotion as promotion

    assert not hasattr(research, "PromotionCandidateSpec")
    assert not hasattr(research, "PaperReadinessChecklist")
    assert "PromotionCandidateSpec" not in promotion.__all__
    assert "PaperReadinessChecklist" not in promotion.__all__


def test_evidence_bundle_rejects_legacy_review_decisions_payload() -> None:
    with pytest.raises(ValueError, match="review_decisions moved to ResearchAuditLog"):
        ResearchEvidenceBundle.from_payload(
            {
                "evidence_bundle_id": "evb_legacy",
                "workflow_run_id": "run-legacy",
                "review_decisions": [{"decision": "go"}],
            }
        )


def test_evidence_bundle_payload_omits_review_decisions(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text('{"artifact_hashes": {}}\n', encoding="utf-8")
    report_path = tmp_path / "workflow-report.md"
    report_path.write_text("# Report\n", encoding="utf-8")
    summary_path = _write_workflow_summary(tmp_path, manifest_path, report_path)

    bundle = EvidenceRegistry(tmp_path / "evidence").create_from_workflow_summary(summary_path)

    assert "review_decisions" not in bundle.to_payload()


def test_append_review_decision_hard_fails_in_favor_of_audit_log(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text('{"artifact_hashes": {}}\n', encoding="utf-8")
    report_path = tmp_path / "workflow-report.md"
    report_path.write_text("# Report\n", encoding="utf-8")
    summary_path = _write_workflow_summary(tmp_path, manifest_path, report_path)
    registry = EvidenceRegistry(tmp_path / "evidence")
    bundle = registry.create_from_workflow_summary(summary_path)

    with pytest.raises(
        ValueError, match="human review decisions must be written to ResearchAuditLog"
    ):
        registry.append_review_decision(bundle.evidence_bundle_id, {"decision": "go"})


@pytest.mark.parametrize(
    "record_type",
    [
        "manifest_loaded",
        "research_run_completed",
        "evidence_bundle_created",
        "evidence_validated",
        "metrics_validated",
        "data_quality_validated",
        "reproducibility_validated",
        "promotion_packet_validated",
        "artifact_graph_verified",
        "human_review_decided",
        "artifact_graph_written",
        "report_projected",
    ],
)
def test_audit_log_accepts_all_research_os_v1_record_types(record_type: str) -> None:
    record = ResearchAuditRecord.create(record_type, {"status": "recorded"})

    assert record.record_type == record_type


def test_audit_log_can_record_full_v1_lifecycle(tmp_path: Path) -> None:
    audit_log = ResearchAuditLog(tmp_path / "audit")

    for record_type in (
        "manifest_loaded",
        "research_run_completed",
        "evidence_bundle_created",
        "evidence_validated",
        "metrics_validated",
        "data_quality_validated",
        "reproducibility_validated",
        "promotion_packet_validated",
        "artifact_graph_verified",
        "human_review_decided",
        "artifact_graph_written",
        "report_projected",
    ):
        audit_log.append(record_type, {"record_type": record_type})

    assert audit_log.verify_hash_chain() == ()
    assert [record.record_type for record in audit_log.list()] == [
        "manifest_loaded",
        "research_run_completed",
        "evidence_bundle_created",
        "evidence_validated",
        "metrics_validated",
        "data_quality_validated",
        "reproducibility_validated",
        "promotion_packet_validated",
        "artifact_graph_verified",
        "human_review_decided",
        "artifact_graph_written",
        "report_projected",
    ]


def _write_manifest_v1(tmp_path: Path, manifest: ResearchManifest) -> Path:
    path = tmp_path / "research_v1.yaml"
    payload = manifest.to_payload()
    payload["output_root"] = str(tmp_path / "artifacts" / "research")
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
                "  short_window: [1]",
                "  long_window: [2]",
                f"promotion_config: {payload['promotion_config']}",
                f"output_root: {payload['output_root']}",
                "splits:",
                "  windows:",
                "    - {name: train, role: in_sample, start: '2010-06-06', end: '2010-06-07'}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _write_manifest_v2(tmp_path: Path) -> Path:
    payload = {
        "schema_version": 2,
        "run": {
            "id": "research-os-v1",
            "question": "Can v1.0 validate canonical manifest?",
            "owner": "research",
            "created_at": "2026-05-27T00:00:00+00:00",
        },
        "strategy": {
            "id": "gc_si_momentum",
            "source_module": "examples.strategies.gc_si_momentum",
            "entrypoint": "GcSiMomentumStrategy",
            "default_config": "configs/strategies/gc_si_momentum.yaml",
            "hypothesis": "GC/SI momentum persists after costs.",
        },
        "data": {
            "dataset_id": "research_futures_gc_si_1m",
            "config": "configs/data/historical.local.yaml",
            "catalog": "research_futures",
            "roots": ["GC", "SI"],
            "timeframe": "1m",
            "start": "2010-06-06T22:00:00+00:00",
            "end": "2010-06-06T22:05:00+00:00",
            "calendar": "CME",
        },
        "splits": {
            "windows": [
                {
                    "name": "train",
                    "role": "in_sample",
                    "start": "2010-06-06",
                    "end": "2010-06-07",
                }
            ]
        },
        "metrics_schema": {
            "id": "schema_v2",
            "version": 2,
            "path": "configs/research/metrics/schema_v2.yaml",
        },
        "promotion_policy": {
            "id": "default_research_policy",
            "version": 1,
            "path": "configs/promotion/default.yaml",
        },
        "artifacts": {
            "required": [
                "metrics",
                "data_quality",
                "reproducibility",
                "evidence_bundle",
                "artifact_graph",
            ]
        },
        "reproducibility": {
            "require_clean_git": True,
            "required_hash_groups": ["dependency_hashes", "config_hashes", "data_hashes"],
        },
        "parameter_grid": {"short_window": [1], "long_window": [2]},
        "output_root": str(tmp_path / "artifacts" / "research"),
    }
    path = tmp_path / "research_v2.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=True), encoding="utf-8")
    return path


def _write_workflow_summary(tmp_path: Path, manifest_path: Path, report_path: Path) -> Path:
    summary_path = tmp_path / "workflow-summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "run_context": {
                    "dataset_ids": ["fixture:GC:1m"],
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
                "steps": [
                    {
                        "id": "manifest",
                        "kind": "manifest",
                        "outputs": {"manifest_path": str(manifest_path)},
                        "status": "passed",
                    },
                    {
                        "id": "report",
                        "kind": "report",
                        "outputs": {"report_path": str(report_path)},
                        "status": "passed",
                    },
                ],
                "workflow_id": "canonical-flow",
            },
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return summary_path
