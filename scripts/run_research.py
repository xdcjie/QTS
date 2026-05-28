"""Run notebook-friendly research workflows from a small CLI."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from qts.core.hashing import stable_json_hash
from qts.research import ResearchSession
from qts.research.artifact_graph import (
    ResearchArtifactGraph,
    ResearchArtifactGraphWriter,
    ResearchArtifactNode,
)
from qts.research.audit_log import ResearchAuditLog
from qts.research.campaign import ResearchCampaignConfig
from qts.research.data_quality import DataQualityArtifactWriter, DataQualityRunner
from qts.research.engine import AutonomousResearchEngine, AutonomousResearchRun
from qts.research.evidence_registry import EvidenceRegistry, ResearchEvidenceBundle
from qts.research.experiment_store import ExperimentStore
from qts.research.idea_registry import IdeaRegistry
from qts.research.idea_spec import IdeaSpec
from qts.research.landscape import FitnessAnalytics, FitnessLandscapeStore, FitnessQuery
from qts.research.manifest import ResearchManifestV2
from qts.research.meta_research import MetaResearchSummary, MetaResearchSummaryWriter
from qts.research.planner import GenerationApprovalRecord
from qts.research.promotion_packet import PromotionPacketV2
from qts.research.reproducibility import ReproducibilitySnapshotV2
from qts.research.selector import CandidateSelector, SelectionPolicy
from qts.research.system_run import ResearchDryRunRunner
from qts.research.workflow import (
    ResearchWorkflowConfig,
    ResearchWorkflowRunner,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _add_factor_tearsheet_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "factor-tearsheet",
        help="Record a factor-evaluation tearsheet from existing evaluation artifacts",
    )
    parser.add_argument("artifacts", type=Path, nargs="+", help="Factor evaluation JSON artifacts")
    parser.add_argument("--experiment-id", required=True, help="Experiment id for the store record")
    parser.add_argument(
        "--strategy-name",
        default="factor-tearsheet",
        help="Research manifest strategy name",
    )
    parser.add_argument(
        "--strategy-version", default="1", help="Research manifest strategy version"
    )
    parser.add_argument(
        "--dataset-id",
        action="append",
        default=[],
        help="Dataset identity to include in the research manifest; may be repeated",
    )


def _add_runs_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("runs", help="List indexed research experiment runs")
    parser.add_argument("--sort-by", default=None, help="Metric name to sort by descending")
    parser.add_argument("--limit", type=int, default=None, help="Maximum rows to print")


def _add_workflow_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("workflow", help="Run a gate-based research workflow")
    parser.add_argument("workflow_config", type=Path, help="Research workflow YAML config")
    parser.add_argument(
        "--step",
        dest="step_id",
        default=None,
        help="Run only the workflow step with this id",
    )
    parser.add_argument(
        "--from-step",
        dest="from_step_id",
        default=None,
        help="Run from this workflow step id, inclusive",
    )
    parser.add_argument(
        "--to-step",
        dest="to_step_id",
        default=None,
        help="Run through this workflow step id, inclusive",
    )
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Workflow result output format",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Canonical ResearchManifestV2 that owns this workflow run",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write workflow_summary.json to this path",
    )
    parser.add_argument(
        "--audit-log-root",
        type=Path,
        default=None,
        help="Research OS audit log root for workflow lifecycle records",
    )
    parser.add_argument(
        "--artifact-graph-root",
        type=Path,
        default=None,
        help="Artifact graph output root for workflow lifecycle records",
    )


def _add_evidence_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("evidence", help="Manage research evidence bundles")
    parser.add_argument(
        "--registry-root",
        type=Path,
        default=Path("runs/research/evidence"),
        help="Evidence registry root directory",
    )
    parser.add_argument(
        "--audit-log-root",
        type=Path,
        default=Path("runs/research/audit"),
        help="Research OS audit log root for evidence lifecycle records",
    )
    parser.add_argument(
        "--artifact-graph-root",
        type=Path,
        default=Path("runs/research/artifact_graph"),
        help="Artifact graph output root for evidence lifecycle records",
    )
    evidence_subparsers = parser.add_subparsers(dest="evidence_command", required=True)

    bundle = evidence_subparsers.add_parser(
        "bundle",
        help="Create an evidence bundle from a workflow JSON summary",
    )
    bundle.add_argument("--workflow-summary", type=Path, required=True)
    bundle.add_argument("--idea-id", default=None)
    bundle.add_argument("--idea-registry-root", type=Path, default=None)
    bundle.add_argument("--strategy-id", default=None)

    evidence_subparsers.add_parser("list", help="List evidence bundles")

    show = evidence_subparsers.add_parser("show", help="Show one evidence bundle")
    show.add_argument("bundle_id")

    verify = evidence_subparsers.add_parser("verify", help="Verify one evidence bundle")
    verify.add_argument("bundle_id")

    reproduce = evidence_subparsers.add_parser(
        "reproduce",
        help="Verify evidence bundle hashes and reproducibility_v2 blockers",
    )
    reproduce.add_argument("--bundle-id", required=True)


def _add_promotion_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "promotion",
        help="Validate research-to-promotion review evidence",
    )
    promotion_subparsers = parser.add_subparsers(dest="promotion_command", required=True)

    validate = promotion_subparsers.add_parser(
        "validate",
        help="Validate a PromotionPacketV2 against a research evidence bundle",
    )
    validate.add_argument("--packet", type=Path, required=True)
    validate.add_argument(
        "--evidence-registry-root",
        type=Path,
        default=Path("runs/research/evidence"),
        help="Evidence registry root directory",
    )
    validate.add_argument(
        "--audit-log-root",
        type=Path,
        default=Path("runs/research/audit"),
        help="Research audit log root directory",
    )
    validate.add_argument(
        "--artifact-graph-root",
        type=Path,
        default=None,
        help="Optional artifact graph output root for packet validation records",
    )
    approve = promotion_subparsers.add_parser(
        "approve",
        help="Record an explicit human approval decision for a machine-valid packet",
    )
    approve.add_argument("--packet", type=Path, required=True)
    approve.add_argument("--expected-packet-hash", required=True)
    approve.add_argument(
        "--decision",
        choices=("approved", "rejected"),
        required=True,
    )
    approve.add_argument("--reviewer", required=True)
    approve.add_argument("--reason", required=True)
    approve.add_argument(
        "--audit-log-root",
        type=Path,
        default=Path("runs/research/audit"),
        help="Research audit log root directory",
    )


def _add_audit_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("audit", help="Verify Research OS audit logs")
    audit_subparsers = parser.add_subparsers(dest="audit_command", required=True)
    verify = audit_subparsers.add_parser("verify", help="Verify an audit-log hash chain")
    verify.add_argument(
        "--audit-log-root",
        type=Path,
        default=Path("runs/research/audit"),
        help="Research audit log root directory",
    )


def _add_manifest_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("manifest", help="Validate Research OS manifests")
    manifest_subparsers = parser.add_subparsers(dest="manifest_command", required=True)
    validate = manifest_subparsers.add_parser(
        "validate",
        help="Validate a canonical ResearchManifestV2 YAML file",
    )
    validate.add_argument("--manifest", type=Path, required=True)
    validate.add_argument(
        "--audit-log-root",
        type=Path,
        default=Path("runs/research/audit"),
        help="Research OS audit log root for manifest_loaded records",
    )
    validate.add_argument(
        "--artifact-graph-root",
        type=Path,
        default=None,
        help="Optional artifact graph output root for manifest records",
    )


def _add_graph_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("graph", help="Verify Research OS artifact graphs")
    graph_subparsers = parser.add_subparsers(dest="graph_command", required=True)
    verify = graph_subparsers.add_parser("verify", help="Verify one artifact graph JSON file")
    verify.add_argument("--graph", type=Path, required=True)
    verify.add_argument("--expected-hash", default=None)
    verify.add_argument(
        "--audit-log-root",
        type=Path,
        default=Path("runs/research/audit"),
        help="Research OS audit log root for artifact_graph_verified records",
    )


def _add_data_quality_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("data-quality", help="Generate data-quality artifacts")
    data_quality_subparsers = parser.add_subparsers(
        dest="data_quality_command",
        required=True,
    )
    run = data_quality_subparsers.add_parser(
        "run",
        help="Run data-quality checks from a dataset snapshot JSON",
    )
    run.add_argument("--snapshot", type=Path, required=True)
    run.add_argument(
        "--output-dir",
        type=Path,
        default=Path("runs/research/data_quality"),
    )
    run.add_argument("--output", type=Path, default=None)
    run.add_argument(
        "--audit-log-root",
        type=Path,
        default=Path("runs/research/audit"),
        help="Research OS audit log root for data_quality_validated records",
    )


def _add_idea_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("idea", help="Manage research idea registry records")
    parser.add_argument(
        "--registry-root",
        type=Path,
        default=Path("runs/research/idea_registry"),
        help="Idea registry root directory",
    )
    idea_subparsers = parser.add_subparsers(dest="idea_command", required=True)

    add = idea_subparsers.add_parser("add", help="Add or update an idea from JSON")
    add.add_argument("--idea-payload", type=Path, required=True)

    idea_subparsers.add_parser("list", help="List ideas")

    trial = idea_subparsers.add_parser("record-trial", help="Record one experiment trial")
    trial.add_argument("--idea-id", required=True)
    trial.add_argument("--experiment-id", required=True)


def _add_meta_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("meta", help="Generate meta-research summaries")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("runs/research/meta"),
        help="Meta-research artifact output directory",
    )
    meta_subparsers = parser.add_subparsers(dest="meta_command", required=True)

    summary = meta_subparsers.add_parser("summary", help="Write a meta-research summary")
    summary.add_argument("--idea-registry-root", type=Path, required=True)
    summary.add_argument("--evidence-registry-root", type=Path, default=None)
    summary.add_argument("--experiment-store-root", type=Path, default=None)
    summary.add_argument("--evidence-records", type=Path, default=None)
    summary.add_argument("--experiment-records", type=Path, default=None)
    summary.add_argument("--period", required=True)
    summary.add_argument("--period-start", required=True)
    summary.add_argument("--period-end", default=None)
    summary.add_argument(
        "--all-history",
        action="store_true",
        help="Include timestamped records outside the requested period",
    )
    summary.add_argument("--trial-count-outlier-threshold", type=int, default=10)


def _add_campaign_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("campaign", help="Operate autonomous research campaigns")
    campaign_subparsers = parser.add_subparsers(dest="campaign_command", required=True)

    validate = campaign_subparsers.add_parser(
        "validate",
        help="Validate a ResearchCampaignConfig YAML file",
    )
    validate.add_argument("--campaign", type=Path, required=True)
    validate.add_argument(
        "--audit-log-root",
        type=Path,
        default=Path("runs/research/audit"),
        help="Research OS audit log root for campaign_loaded records",
    )
    validate.add_argument(
        "--artifact-graph-root",
        type=Path,
        default=None,
        help="Optional artifact graph output root for the campaign node",
    )

    run = campaign_subparsers.add_parser(
        "run",
        help="Run a bounded autonomous research campaign",
    )
    run.add_argument("--campaign", type=Path, required=True)
    run.add_argument("--output-root", type=Path, required=True)
    run.add_argument(
        "--approval-mode",
        choices=("manual", "none"),
        default="manual",
        help="Use manual to stop after generation 0 when later generations require approval",
    )
    run.add_argument(
        "--data-path",
        action="append",
        default=[],
        metavar="ROOT=PATH",
        help="CSV data contract path for one universe root; may be repeated",
    )

    status = campaign_subparsers.add_parser(
        "status",
        help="Return machine-readable campaign status",
    )
    status.add_argument("--output-root", type=Path, required=True)

    verify = campaign_subparsers.add_parser(
        "verify",
        help="Verify an autonomous research campaign release bundle",
    )
    verify.add_argument("--output-root", type=Path, required=True)

    approval = campaign_subparsers.add_parser(
        "approve-next-generation",
        help="Record a human decision for a next-generation proposal",
    )
    approval.add_argument("--proposal", type=Path, required=True)
    approval.add_argument("--expected-proposal-hash", required=True)
    approval.add_argument("--output-root", type=Path, default=None)
    approval.add_argument(
        "--decision",
        choices=("approved", "rejected"),
        required=True,
    )
    approval.add_argument("--reviewer", required=True)
    approval.add_argument("--reason", required=True)
    approval.add_argument(
        "--audit-log-root",
        type=Path,
        default=Path("runs/research/audit"),
        help="Research OS audit log root for generation approval records",
    )

    stop = campaign_subparsers.add_parser("stop", help="Persist a stopped campaign state")
    stop.add_argument("--output-root", type=Path, required=True)
    stop.add_argument("--reason", default="operator requested stop")
    stop.add_argument(
        "--audit-log-root",
        type=Path,
        default=Path("runs/research/audit"),
    )

    resume = campaign_subparsers.add_parser("resume", help="Clear a stopped campaign state")
    resume.add_argument("--output-root", type=Path, required=True)
    resume.add_argument(
        "--audit-log-root",
        type=Path,
        default=Path("runs/research/audit"),
    )


def _add_landscape_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("landscape", help="Query fitness landscape artifacts")
    parser.add_argument(
        "--landscape",
        type=Path,
        default=Path("runs/research/fitness_landscape.jsonl"),
        help="Fitness landscape JSONL path or containing directory",
    )
    landscape_subparsers = parser.add_subparsers(dest="landscape_command", required=True)

    landscape_subparsers.add_parser(
        "summarize",
        help="Summarize family performance and rejection clusters",
    )

    query = landscape_subparsers.add_parser("query", help="Query landscape points")
    query.add_argument("--campaign-id", default=None)
    query.add_argument("--generation-id", default=None)
    query.add_argument("--trial-id", default=None)
    query.add_argument("--strategy-family", default=None)
    query.add_argument("--factor-family", default=None)
    query.add_argument("--root", default=None)
    query.add_argument("--regime", default=None)
    query.add_argument("--session", default=None)

    export = landscape_subparsers.add_parser("export", help="Export landscape rows as JSON")
    export.add_argument("--output", type=Path, default=None)


def _add_selector_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("selector", help="Replay selector decisions")
    selector_subparsers = parser.add_subparsers(dest="selector_command", required=True)
    replay = selector_subparsers.add_parser("replay", help="Reproduce a selector artifact")
    replay.add_argument("--selection-result", type=Path, required=True)
    replay.add_argument("--campaign", type=Path, required=True)
    replay.add_argument(
        "--candidate-results",
        type=Path,
        required=True,
        help="Candidate result JSON array, JSON object, or JSONL rows used by the selector",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/research/quickstart.yaml"),
        help="Research session YAML config",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Produce manifest-driven research artifacts without executing backtests",
    )
    subparsers = parser.add_subparsers(dest="command")
    _add_factor_tearsheet_parser(subparsers)
    _add_runs_parser(subparsers)
    _add_workflow_parser(subparsers)
    _add_evidence_parser(subparsers)
    _add_promotion_parser(subparsers)
    _add_manifest_parser(subparsers)
    _add_audit_parser(subparsers)
    _add_graph_parser(subparsers)
    _add_data_quality_parser(subparsers)
    _add_idea_parser(subparsers)
    _add_meta_parser(subparsers)
    _add_campaign_parser(subparsers)
    _add_landscape_parser(subparsers)
    _add_selector_parser(subparsers)
    return parser


def _record_factor_tearsheet(args: argparse.Namespace, session: ResearchSession) -> int:
    record = session.record_factor_tearsheet(
        tuple(args.artifacts),
        experiment_id=args.experiment_id,
        strategy_name=args.strategy_name,
        strategy_version=args.strategy_version,
        dataset_ids=tuple(args.dataset_id),
    )
    manifest_payload = json.loads(record.manifest_path.read_text(encoding="utf-8"))
    artifact_paths = _artifact_paths_by_name(manifest_payload)
    print(f"manifest_path={record.manifest_path}")
    print(f"store_index={session.store.index_path}")
    if artifact_paths:
        first_name = sorted(artifact_paths)[0]
        print(f"tearsheet_artifact={first_name}")
        print(f"tearsheet_path={artifact_paths[first_name]}")
    return 0


def _artifact_paths_by_name(manifest_payload: dict[str, object]) -> dict[str, str]:
    artifact_hashes = manifest_payload.get("artifact_hashes")
    artifact_paths_by_hash = manifest_payload.get("artifact_paths_by_hash")
    if not isinstance(artifact_hashes, dict) or not isinstance(artifact_paths_by_hash, dict):
        return {}
    result: dict[str, str] = {}
    for artifact_name, digest in artifact_hashes.items():
        if isinstance(artifact_name, str) and isinstance(digest, str):
            path = artifact_paths_by_hash.get(digest)
            if isinstance(path, str):
                result[artifact_name] = path
    return result


def _list_runs(args: argparse.Namespace, session: ResearchSession) -> int:
    records = (
        session.compare_runs(args.sort_by)
        if args.sort_by is not None
        else session.list_runs(limit=args.limit)
    )
    if args.sort_by is not None and args.limit is not None:
        records = records[: args.limit]
    rows = [
        {
            "experiment_id": record.experiment_id,
            "manifest_path": str(record.manifest_path),
            "metrics": dict(record.metrics),
            "recorded_at": record.recorded_at.isoformat(),
            "strategy_name": record.strategy_name,
            "strategy_version": record.strategy_version,
        }
        for record in records
    ]
    print(json.dumps(rows, sort_keys=True, indent=2))
    return 0


def _run_workflow(args: argparse.Namespace, session: ResearchSession) -> int:
    _ensure_repo_root_on_path()
    try:
        if args.manifest is None:
            raise ValueError("workflow requires --manifest schema_version=2")
        if args.artifact_graph_root is not None and args.audit_log_root is None:
            raise ValueError("artifact graph writes require --audit-log-root")
        manifest = ResearchManifestV2.from_yaml(args.manifest)
        result = ResearchWorkflowRunner().run(
            session,
            ResearchWorkflowConfig.from_yaml(args.workflow_config),
            step_id=args.step_id,
            from_step_id=args.from_step_id,
            to_step_id=args.to_step_id,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    payload = result.to_payload()
    payload["manifest_hash"] = manifest.manifest_hash
    payload["manifest_path"] = str(args.manifest)
    payload["schema_version"] = manifest.schema_version
    workflow_summary_hash = stable_json_hash(payload)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
    audit_log = None
    if args.audit_log_root is not None:
        audit_log = ResearchAuditLog(args.audit_log_root)
        audit_log.append(
            "research_run_completed",
            {
                "accepted": result.succeeded,
                "manifest_hash": manifest.manifest_hash,
                "manifest_path": str(args.manifest),
                "status": result.status,
                "workflow_id": result.workflow_id,
                "workflow_summary_hash": workflow_summary_hash,
                "workflow_summary_path": None if args.output is None else str(args.output),
            },
        )
    if args.artifact_graph_root is not None:
        ResearchArtifactGraphWriter(args.artifact_graph_root).write_from_payloads(
            manifests=(
                {
                    "manifest_id": str(args.manifest),
                    "manifest_hash": manifest.manifest_hash,
                    "path": str(args.manifest),
                },
            ),
            workflow_runs=(
                {
                    "manifest_id": str(args.manifest),
                    "payload_hash": workflow_summary_hash,
                    "workflow_run_id": result.workflow_id,
                },
            ),
            output_path=f"workflow-{_artifact_safe_name(result.workflow_id)}-artifact-graph.json",
            audit_log=audit_log,
        )
    if args.format == "json":
        print(json.dumps(payload, sort_keys=True, indent=2))
    else:
        print(f"workflow_id={result.workflow_id}")
        print(f"status={result.status}")
        for step in result.steps:
            print(f"{step.step_id}={step.status}")
    return 0 if result.succeeded else 1


def _run_evidence(args: argparse.Namespace) -> int:
    registry = EvidenceRegistry(args.registry_root)
    audit_log = ResearchAuditLog(args.audit_log_root)
    artifact_graph_writer = ResearchArtifactGraphWriter(args.artifact_graph_root)
    if args.evidence_command == "bundle":
        idea = (
            None
            if args.idea_id is None or args.idea_registry_root is None
            else IdeaRegistry(args.idea_registry_root).get(args.idea_id)
        )
        bundle = registry.create_from_workflow_summary(
            args.workflow_summary,
            idea=idea,
            idea_id=args.idea_id,
            strategy_id=args.strategy_id,
            audit_log=audit_log,
            artifact_graph_writer=artifact_graph_writer,
        )
        print(json.dumps(bundle.to_payload(), sort_keys=True, indent=2))
        return 0
    if args.evidence_command == "list":
        print(
            json.dumps(
                [bundle.to_payload() for bundle in registry.list()],
                sort_keys=True,
                indent=2,
            )
        )
        return 0
    if args.evidence_command == "show":
        print(json.dumps(registry.show(args.bundle_id).to_payload(), sort_keys=True, indent=2))
        return 0
    if args.evidence_command == "verify":
        verification = registry.verify(args.bundle_id, audit_log=audit_log)
        print(json.dumps(verification.to_payload(), sort_keys=True, indent=2))
        return 0 if verification.accepted else 1
    if args.evidence_command == "reproduce":
        verification = registry.verify(args.bundle_id)
        reproduce_reasons: list[str] = list(verification.reasons)
        checked_paths = list(verification.checked_paths)
        reproducibility_blockers: list[str] = []
        reproducibility_path = _find_reproducibility_v2_path(registry.show(args.bundle_id))
        if reproducibility_path is None:
            reproduce_reasons.append("missing reproducibility_v2 artifact path in evidence bundle")
        else:
            checked_paths.append(reproducibility_path)
            reproducibility_blockers = list(
                _reproducibility_v2_blockers(Path(reproducibility_path))
            )
            reproduce_reasons.extend(
                f"reproducibility validation blocker: {reason}"
                for reason in reproducibility_blockers
            )

        accepted = verification.accepted and len(reproduce_reasons) == 0
        payload = {
            "accepted": accepted,
            "checked_paths": list(dict.fromkeys(checked_paths)),
            "evidence_bundle_id": args.bundle_id,
            "reproducibility_blockers": reproducibility_blockers,
            "reproducibility_path": reproducibility_path,
            "reasons": reproduce_reasons,
            "reproduction_boundary": "verify_hashes_and_reproducibility_v2_before_reproduce",
        }
        print(json.dumps(payload, sort_keys=True, indent=2))
        return 0 if accepted else 1
    raise ValueError(f"unsupported evidence command: {args.evidence_command}")


def _run_promotion(args: argparse.Namespace) -> int:
    if args.promotion_command == "validate":
        try:
            evidence_registry = EvidenceRegistry(args.evidence_registry_root)
            packet_result = PromotionPacketV2.from_payload(_load_mapping(args.packet)).validate(
                evidence_registry=evidence_registry,
                audit_log=ResearchAuditLog(args.audit_log_root),
                artifact_graph_writer=(
                    None
                    if args.artifact_graph_root is None
                    else ResearchArtifactGraphWriter(args.artifact_graph_root)
                ),
            )
            print(json.dumps(packet_result.to_payload(), sort_keys=True, indent=2))
            return 0 if packet_result.accepted else 1
        except (FileNotFoundError, ValueError) as exc:
            print(str(exc), file=sys.stderr)
            return 2
    if args.promotion_command == "approve":
        try:
            packet = PromotionPacketV2.from_payload(_load_mapping(args.packet))
            result = packet.human_review(
                audit_log=ResearchAuditLog(args.audit_log_root),
                decision=args.decision,
                reviewer=args.reviewer,
                reviewed_at=datetime.now(UTC),
                expected_packet_hash=args.expected_packet_hash,
                notes=args.reason,
            )
            print(json.dumps(result.to_payload(), sort_keys=True, indent=2))
            return 0 if result.accepted else 1
        except (FileNotFoundError, ValueError) as exc:
            print(str(exc), file=sys.stderr)
            return 2
    raise ValueError(f"unsupported promotion command: {args.promotion_command}")


def _run_manifest(args: argparse.Namespace) -> int:
    if args.manifest_command == "validate":
        try:
            _ensure_repo_root_on_path()
            if args.artifact_graph_root is not None and args.audit_log_root is None:
                raise ValueError("artifact graph writes require --audit-log-root")
            manifest = ResearchManifestV2.from_yaml(args.manifest)
        except (FileNotFoundError, ValueError) as exc:
            message = str(exc)
            if message != "artifact graph writes require --audit-log-root":
                message = f"canonical Research OS v1.0 manifest requires schema_version=2: {exc}"
            print(message, file=sys.stderr)
            return 2
        manifest_hash = manifest.manifest_hash
        audit_record_id = None
        audit_log = None
        if args.audit_log_root is not None:
            audit_log = ResearchAuditLog(args.audit_log_root)
            record = audit_log.append(
                "manifest_loaded",
                {
                    "manifest_hash": manifest_hash,
                    "manifest_path": str(args.manifest),
                    "run_id": manifest.run_id,
                    "schema_version": manifest.schema_version,
                },
            )
            audit_record_id = record.record_id
        artifact_graph_hash = None
        if args.artifact_graph_root is not None:
            result = ResearchArtifactGraphWriter(args.artifact_graph_root).write_from_payloads(
                manifests=(
                    {
                        "manifest_id": str(args.manifest),
                        "manifest_hash": manifest_hash,
                        "path": str(args.manifest),
                    },
                ),
                output_path=f"manifest-{manifest.run_id}-artifact-graph.json",
                audit_log=audit_log,
            )
            artifact_graph_hash = result.artifact_graph_hash
        print(
            json.dumps(
                {
                    "accepted": True,
                    "audit_record_id": audit_record_id,
                    "artifact_graph_hash": artifact_graph_hash,
                    "manifest_hash": manifest_hash,
                    "run_id": manifest.run_id,
                    "schema_version": manifest.schema_version,
                },
                sort_keys=True,
                indent=2,
            )
        )
        return 0
    raise ValueError(f"unsupported manifest command: {args.manifest_command}")


def _run_audit(args: argparse.Namespace) -> int:
    if args.audit_command == "verify":
        reasons = ResearchAuditLog(args.audit_log_root).verify_hash_chain()
        payload = {"accepted": not reasons, "reasons": list(reasons)}
        print(json.dumps(payload, sort_keys=True, indent=2))
        return 0 if not reasons else 1
    raise ValueError(f"unsupported audit command: {args.audit_command}")


def _run_graph(args: argparse.Namespace) -> int:
    if args.graph_command == "verify":
        try:
            graph = ResearchArtifactGraph.from_payload(_load_json_mapping(args.graph))
            graph.validate_full_chain()
            artifact_graph_hash = graph.stable_hash()
            if args.expected_hash is not None and args.expected_hash != artifact_graph_hash:
                raise ValueError(
                    f"artifact graph hash mismatch: {artifact_graph_hash} != {args.expected_hash}"
                )
        except (FileNotFoundError, ValueError) as exc:
            print(json.dumps({"accepted": False, "reasons": [str(exc)]}, sort_keys=True, indent=2))
            return 1
        audit_record = ResearchAuditLog(args.audit_log_root).append(
            "artifact_graph_verified",
            {
                "accepted": True,
                "artifact_graph_hash": artifact_graph_hash,
                "artifact_graph_path": str(args.graph),
            },
        )
        print(
            json.dumps(
                {
                    "accepted": True,
                    "artifact_graph_hash": artifact_graph_hash,
                    "audit_record_id": audit_record.record_id,
                    "reasons": [],
                },
                sort_keys=True,
                indent=2,
            )
        )
        return 0
    raise ValueError(f"unsupported graph command: {args.graph_command}")


def _run_data_quality(args: argparse.Namespace) -> int:
    if args.data_quality_command == "run":
        try:
            snapshot = _load_json_mapping(args.snapshot)
            artifact = DataQualityRunner(
                dataset_id=_required_mapping_text(snapshot, "dataset_id"),
                timeframe=_required_mapping_text(snapshot, "timeframe"),
                start=_optional_mapping_text(snapshot, "start"),
                end=_optional_mapping_text(snapshot, "end"),
                calendar=_optional_mapping_text(snapshot, "calendar"),
            ).run(snapshot)
            output_root = args.output.parent if args.output is not None else args.output_dir
            result = DataQualityArtifactWriter(output_root).write(artifact)
            output_path = result.path
            if args.output is not None and result.path != args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(result.path.read_text(encoding="utf-8"), encoding="utf-8")
                result.path.unlink()
                output_path = args.output
        except (FileNotFoundError, ValueError) as exc:
            print(json.dumps({"accepted": False, "reasons": [str(exc)]}, sort_keys=True, indent=2))
            return 1
        blockers = [f"{item['code']}: {item['message']}" for item in artifact.blockers()]
        audit_record = ResearchAuditLog(args.audit_log_root).append(
            "data_quality_validated",
            {
                "accepted": artifact.accepted,
                "artifact_hash": result.artifact_hash,
                "dataset_id": artifact.dataset_id,
                "data_quality_path": str(output_path),
                "reasons": blockers,
            },
        )
        print(
            json.dumps(
                {
                    "accepted": artifact.accepted,
                    "artifact": artifact.to_payload(),
                    "artifact_hash": result.artifact_hash,
                    "audit_record_id": audit_record.record_id,
                    "path": str(output_path),
                    "reasons": blockers,
                },
                sort_keys=True,
                indent=2,
            )
        )
        return 0 if artifact.accepted else 1
    raise ValueError(f"unsupported data-quality command: {args.data_quality_command}")


def _run_idea(args: argparse.Namespace) -> int:
    registry = IdeaRegistry(args.registry_root)
    if args.idea_command == "add":
        idea = IdeaSpec.from_payload(_load_json_mapping(args.idea_payload))
        registry.save_idea(idea)
        print(json.dumps(idea.to_payload(), sort_keys=True, indent=2))
        return 0
    if args.idea_command == "list":
        print(
            json.dumps(
                [idea.to_payload() for idea in registry.list_ideas()],
                sort_keys=True,
                indent=2,
            )
        )
        return 0
    if args.idea_command == "record-trial":
        idea = registry.record_trial(args.idea_id, experiment_id=args.experiment_id)
        print(json.dumps(idea.to_payload(), sort_keys=True, indent=2))
        return 0
    raise ValueError(f"unsupported idea command: {args.idea_command}")


def _run_meta(args: argparse.Namespace) -> int:
    if args.meta_command == "summary":
        ideas = IdeaRegistry(args.idea_registry_root).list_ideas()
        evidence_records = list(_load_json_records(args.evidence_records))
        if args.evidence_registry_root is not None:
            evidence_records.extend(
                MetaResearchSummary.evidence_records_from_registry(
                    EvidenceRegistry(args.evidence_registry_root)
                )
            )
        experiment_records = list(_load_json_records(args.experiment_records))
        if args.experiment_store_root is not None:
            experiment_records.extend(
                MetaResearchSummary.experiment_records_from_store(
                    ExperimentStore(args.experiment_store_root)
                )
            )
        summary = MetaResearchSummary.from_registries(
            ideas=ideas,
            evidence_records=evidence_records,
            experiment_records=experiment_records,
            period=args.period,
            period_start=date.fromisoformat(args.period_start),
            period_end=(None if args.period_end is None else date.fromisoformat(args.period_end)),
            all_history=args.all_history,
            trial_count_outlier_threshold=args.trial_count_outlier_threshold,
        )
        artifacts = MetaResearchSummaryWriter().write(args.output_dir, summary)
        print(
            json.dumps(
                {
                    "json_path": str(artifacts.json_path),
                    "markdown_path": str(artifacts.markdown_path),
                    "summary": summary.to_payload(),
                },
                sort_keys=True,
                indent=2,
            )
        )
        return 0
    raise ValueError(f"unsupported meta command: {args.meta_command}")


def _run_campaign(args: argparse.Namespace) -> int:
    if args.campaign_command == "validate":
        try:
            if args.artifact_graph_root is not None and args.audit_log_root is None:
                raise ValueError("artifact graph writes require --audit-log-root")
            campaign = ResearchCampaignConfig.from_yaml(args.campaign)
        except (FileNotFoundError, ValueError) as exc:
            print(str(exc), file=sys.stderr)
            return 2

        audit_log = ResearchAuditLog(args.audit_log_root)
        audit_record = audit_log.append(
            "campaign_loaded",
            {
                "campaign_hash": campaign.campaign_hash,
                "campaign_id": campaign.campaign_id,
                "campaign_path": str(args.campaign),
                "universe_roots": list(campaign.universe.roots),
            },
        )
        artifact_graph_hash = None
        artifact_graph_path = None
        if args.artifact_graph_root is not None:
            graph_result = ResearchArtifactGraphWriter(args.artifact_graph_root).write(
                ResearchArtifactGraph(
                    nodes=(
                        ResearchArtifactNode(
                            node_id=campaign.campaign_id,
                            node_type="campaign",
                            payload_hash=campaign.campaign_hash,
                            metadata={"path": str(args.campaign)},
                        ),
                    )
                ),
                output_path=f"campaign-{_artifact_safe_name(campaign.campaign_id)}.json",
                audit_log=audit_log,
            )
            artifact_graph_hash = graph_result.artifact_graph_hash
            artifact_graph_path = str(graph_result.path)
        print(
            json.dumps(
                {
                    "accepted": True,
                    "artifact_graph_hash": artifact_graph_hash,
                    "artifact_graph_path": artifact_graph_path,
                    "audit_record_id": audit_record.record_id,
                    "campaign_hash": campaign.campaign_hash,
                    "campaign_id": campaign.campaign_id,
                },
                sort_keys=True,
                indent=2,
            )
        )
        return 0

    if args.campaign_command == "run":
        try:
            data_paths = _data_paths_from_args(args.data_path)
            run = AutonomousResearchRun.from_yaml(
                args.campaign,
                data_paths=data_paths,
                output_root=args.output_root,
            )
            requested_generations = run.max_generations
            if args.approval_mode == "manual" and requested_generations > 1:
                run = replace(run, max_generations=1)
            result = _run_campaign_engine(run)
            acceptance_markers = _acceptance_markers_from_campaign(args.campaign)
            _annotate_operator_acceptance_artifacts(result.output_root, acceptance_markers)
        except (FileNotFoundError, ValueError) as exc:
            print(str(exc), file=sys.stderr)
            return 2
        payload = result.to_payload()
        payload["accepted"] = result.status == "accepted"
        payload["acceptance_markers"] = acceptance_markers
        if (
            args.approval_mode == "manual"
            and requested_generations > 1
            and result.status == "accepted"
        ):
            proposal = _load_json_mapping(result.next_generation_proposal_path)
            state = _write_campaign_state(
                args.output_root,
                "pending_human_approval",
                "next generation requires human approval",
                extra={
                    "campaign_path": str(args.campaign),
                    "completed_generation_count": len(result.generations),
                    "data_paths": {root: str(path) for root, path in sorted(data_paths.items())},
                    "pending_generation_id": str(proposal.get("generation_id")),
                    "proposal_hash": str(proposal.get("proposal_hash")),
                    "requested_max_generations": requested_generations,
                },
            )
            payload.update(
                {
                    "accepted": True,
                    "completed_generation_count": len(result.generations),
                    "pending_generation_id": state["pending_generation_id"],
                    "proposal_hash": state["proposal_hash"],
                    "status": "pending_human_approval",
                }
            )
        print(json.dumps(payload, sort_keys=True, indent=2))
        return 0 if result.status == "accepted" else 1

    if args.campaign_command == "status":
        output_root = Path(args.output_root)
        summary_path = output_root / "validation_summary.json"
        state_path = output_root / "campaign_state.json"
        status_payload: dict[str, Any] = {
            "accepted": summary_path.exists(),
            "output_root": str(output_root),
            "state": _load_json_mapping(state_path) if state_path.exists() else {},
            "status": "not_started",
            "validation_summary_path": str(summary_path),
        }
        if summary_path.exists():
            status_payload.update(_load_json_mapping(summary_path))
        if status_payload["state"].get("status"):
            status_payload["status"] = status_payload["state"]["status"]
        print(json.dumps(status_payload, sort_keys=True, indent=2))
        return 0 if summary_path.exists() else 1

    if args.campaign_command == "verify":
        payload = _verify_campaign_release_bundle(args.output_root)
        print(json.dumps(payload, sort_keys=True, indent=2))
        return 0 if payload["accepted"] else 1

    if args.campaign_command == "approve-next-generation":
        try:
            proposal = _load_json_mapping(args.proposal)
            proposal_hash = str(proposal.get("proposal_hash") or stable_json_hash(proposal))
            if proposal_hash != args.expected_proposal_hash:
                raise ValueError(
                    f"proposal hash mismatch: {proposal_hash} != {args.expected_proposal_hash}"
                )
            output_root = args.output_root or args.proposal.parent
            audit_record = ResearchAuditLog(args.audit_log_root).append(
                "generation_approval_decided",
                {
                    "decision": args.decision,
                    "proposal_hash": proposal_hash,
                    "proposal_id": proposal.get("proposal_id"),
                    "proposal_path": str(args.proposal),
                    "reason": args.reason,
                    "reviewed_at": datetime.now(UTC).isoformat(),
                    "reviewer": args.reviewer,
                },
            )
            state_payload = _load_optional_campaign_state(output_root)
            state_extra = {
                **{
                    key: value
                    for key, value in state_payload.items()
                    if key
                    in {
                        "campaign_path",
                        "completed_generation_count",
                        "data_paths",
                        "pending_generation_id",
                        "requested_max_generations",
                    }
                },
                "decision": args.decision,
                "proposal_hash": proposal_hash,
                "proposal_id": proposal.get("proposal_id"),
                "reviewer": args.reviewer,
            }
            _write_campaign_state(
                output_root,
                "approved_next_generation" if args.decision == "approved" else "rejected",
                args.reason,
                extra=state_extra,
            )
        except (FileNotFoundError, ValueError) as exc:
            print(str(exc), file=sys.stderr)
            return 2
        print(
            json.dumps(
                {
                    "accepted": args.decision == "approved",
                    "audit_record_id": audit_record.record_id,
                    "decision": args.decision,
                    "proposal_hash": proposal_hash,
                    "proposal_id": proposal.get("proposal_id"),
                    "status": (
                        "approved_next_generation" if args.decision == "approved" else "rejected"
                    ),
                },
                sort_keys=True,
                indent=2,
            )
        )
        return 0 if args.decision == "approved" else 1

    if args.campaign_command == "stop":
        payload = _write_campaign_state(args.output_root, "stopped", args.reason)
        audit_record = ResearchAuditLog(args.audit_log_root).append(
            "campaign_stopped",
            payload,
        )
        print(
            json.dumps(
                {**payload, "accepted": True, "audit_record_id": audit_record.record_id},
                sort_keys=True,
                indent=2,
            )
        )
        return 0

    if args.campaign_command == "resume":
        try:
            state = _load_optional_campaign_state(args.output_root)
            if state.get("status") != "approved_next_generation":
                raise ValueError("campaign resume requires an approved next-generation state")
            campaign_path = _required_state_path(state, "campaign_path")
            data_paths = _state_data_paths(state)
            requested_generations = _state_positive_int(state, "requested_max_generations")
            approval = _approval_record_from_state(state)
            run = AutonomousResearchRun.from_yaml(
                campaign_path,
                data_paths=data_paths,
                output_root=args.output_root,
                approval_records=(approval,),
            )
            run = replace(run, max_generations=requested_generations)
            result = _run_campaign_engine(run)
            acceptance_markers = _acceptance_markers_from_campaign(campaign_path)
            _annotate_operator_acceptance_artifacts(result.output_root, acceptance_markers)
            state_payload = _write_campaign_state(
                args.output_root,
                "accepted" if result.status == "accepted" else result.status,
                "operator resumed approved generation",
                extra={
                    "campaign_path": str(campaign_path),
                    "resumed_from_generation_id": state.get("pending_generation_id"),
                    "requested_max_generations": requested_generations,
                },
            )
            audit_record = ResearchAuditLog(args.audit_log_root).append(
                "campaign_resumed",
                state_payload,
            )
        except (FileNotFoundError, ValueError) as exc:
            print(str(exc), file=sys.stderr)
            return 2
        payload = result.to_payload()
        payload.update(
            {
                "accepted": result.status == "accepted",
                "acceptance_markers": acceptance_markers,
                "audit_record_id": audit_record.record_id,
                "resumed_from_generation_id": state.get("pending_generation_id"),
            }
        )
        print(json.dumps(payload, sort_keys=True, indent=2))
        return 0

    raise ValueError(f"unsupported campaign command: {args.campaign_command}")


def _verify_campaign_release_bundle(output_root: Path) -> dict[str, Any]:
    output_root = Path(output_root)
    criteria: dict[str, dict[str, Any]] = {}

    state_path = output_root / "campaign_state.json"
    state = _load_json_mapping(state_path) if state_path.exists() else {}
    state_status = state.get("status")
    state_reasons = (
        []
        if state_status in {None, "accepted"}
        else [f"campaign state is not accepted: {state_status}"]
    )
    criteria["campaign_state"] = {
        "accepted": not state_reasons,
        "path": str(state_path),
        "reasons": state_reasons,
        "status": state_status,
    }

    summary_path = output_root / "validation_summary.json"
    summary = _load_json_mapping(summary_path) if summary_path.exists() else {}
    criteria["validation_summary"] = {
        "accepted": summary.get("status") == "accepted",
        "path": str(summary_path),
        "status": summary.get("status"),
    }

    audit_log = ResearchAuditLog(output_root / "audit" / "audit_log.jsonl")
    audit_reasons = list(audit_log.verify_hash_chain())
    criteria["audit_hash_chain"] = {
        "accepted": not audit_reasons and audit_log.path.exists(),
        "path": str(audit_log.path),
        "reasons": audit_reasons,
    }

    graph_path = output_root / "artifact_graph" / "artifact_graph.json"
    graph_reasons: list[str] = []
    if graph_path.exists():
        try:
            ResearchArtifactGraph.from_payload(_load_json_mapping(graph_path)).validate_full_chain()
        except ValueError as exc:
            graph_reasons.append(str(exc))
    else:
        graph_reasons.append(f"missing artifact graph: {graph_path}")
    criteria["artifact_graph"] = {
        "accepted": not graph_reasons,
        "path": str(graph_path),
        "reasons": graph_reasons,
    }

    selected_rows = _read_jsonl(output_root / "selected_candidates.jsonl")
    rejected_rows = _read_jsonl(output_root / "rejected_candidates.jsonl")
    generated_count = len(selected_rows) + len(rejected_rows)
    try:
        landscape = FitnessLandscapeStore(output_root).read()
        landscape_count = len(landscape.points)
        landscape_reasons = (
            []
            if landscape_count == generated_count
            else [f"landscape count {landscape_count} != generated candidates {generated_count}"]
        )
    except (FileNotFoundError, ValueError) as exc:
        landscape_count = 0
        landscape_reasons = [str(exc)]
    criteria["fitness_landscape"] = {
        "accepted": not landscape_reasons,
        "generated_candidate_count": generated_count,
        "landscape_trial_count": landscape_count,
        "reasons": landscape_reasons,
    }

    packet_reasons = _selected_candidate_packet_reasons(selected_rows)
    criteria["selected_candidate_packets"] = {
        "accepted": bool(selected_rows) and not packet_reasons,
        "reasons": packet_reasons,
        "selected_count": len(selected_rows),
    }

    paper_live_launches = summary.get("paper_live_launches", [])
    criteria["paper_live_launches"] = {
        "accepted": paper_live_launches == [],
        "paper_live_launches": paper_live_launches,
    }

    proposal_path = output_root / "next_generation_proposal.json"
    proposal_reasons = _proposal_evidence_reasons(proposal_path)
    criteria["next_generation_proposal"] = {
        "accepted": not proposal_reasons,
        "path": str(proposal_path),
        "reasons": proposal_reasons,
    }

    report_path = output_root / "report.md"
    criteria["report_projection"] = {
        "accepted": report_path.exists(),
        "path": str(report_path),
    }

    accepted = all(item["accepted"] for item in criteria.values())
    payload = {
        "accepted": accepted,
        "criteria": criteria,
        "output_root": str(output_root),
        "release_verification_path": str(output_root / "release_verification.json"),
    }
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "release_verification.json").write_text(
        json.dumps(payload, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def _selected_candidate_packet_reasons(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    reasons: list[str] = []
    for row in rows:
        bundle_id = row.get("evidence_bundle_id")
        packet_path = row.get("promotion_packet_path")
        packet_hash = row.get("packet_hash")
        if not isinstance(bundle_id, str) or not bundle_id.strip():
            reasons.append(f"selected candidate missing evidence_bundle_id: {row.get('trial_id')}")
        if not isinstance(packet_path, str) or not Path(packet_path).exists():
            reasons.append(f"selected candidate missing packet: {row.get('trial_id')}")
            continue
        packet = _load_json_mapping(Path(packet_path))
        validation = packet.get("validation")
        if not isinstance(validation, Mapping):
            reasons.append(f"packet missing validation payload: {packet_path}")
            continue
        if validation.get("status") not in {"human_pending", "human_approved"}:
            reasons.append(f"packet is not machine-valid human-gated: {packet_path}")
        if packet_hash != packet.get("packet_hash"):
            reasons.append(f"packet hash mismatch in selected row: {packet_path}")
    return reasons


def _proposal_evidence_reasons(path: Path) -> list[str]:
    if not path.exists():
        return [f"missing next generation proposal: {path}"]
    proposal = _load_json_mapping(path)
    if not proposal:
        return []
    reasons: list[str] = []
    evidence_refs = proposal.get("evidence_refs")
    if not isinstance(evidence_refs, list) or not evidence_refs:
        reasons.append("next_generation_proposal.evidence_refs must not be empty")
    mutations = proposal.get("mutations", [])
    if isinstance(mutations, Sequence) and not isinstance(mutations, str):
        for index, mutation in enumerate(mutations):
            if not isinstance(mutation, Mapping):
                reasons.append(f"next_generation_proposal.mutations[{index}] must be a mapping")
                continue
            refs = mutation.get("evidence_refs")
            if not isinstance(refs, list) or not refs:
                reasons.append(
                    f"next_generation_proposal.mutations[{index}].evidence_refs must not be empty"
                )
    return reasons


def _run_landscape(args: argparse.Namespace) -> int:
    try:
        landscape = FitnessLandscapeStore(args.landscape).read()
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.landscape_command == "summarize":
        analytics = FitnessAnalytics.from_landscape(landscape)
        rejection_counts = landscape.rejection_reason_counts()
        payload = {
            "analytics": analytics.to_payload(),
            "family_success_rate": _family_success_rates(analytics),
            "fitness_landscape_hash": landscape.landscape_hash,
            "rejection_distribution": rejection_counts,
            "rejection_reason_counts": rejection_counts,
        }
        print(json.dumps(payload, sort_keys=True, indent=2))
        return 0

    if args.landscape_command == "query":
        points = landscape.query(
            FitnessQuery(
                campaign_id=args.campaign_id,
                generation_id=args.generation_id,
                trial_id=args.trial_id,
                strategy_family=args.strategy_family,
                factor_family=args.factor_family,
                root=args.root,
                regime=args.regime,
                session=args.session,
            )
        )
        print(
            json.dumps(
                {
                    "fitness_landscape_hash": landscape.landscape_hash,
                    "points": [point.to_payload() for point in points],
                    "query_count": len(points),
                },
                sort_keys=True,
                indent=2,
            )
        )
        return 0

    if args.landscape_command == "export":
        analytics = FitnessAnalytics.from_landscape(landscape)
        payload = {
            **landscape.to_payload(),
            "analytics": analytics.to_payload(),
            "family_success_rate": _family_success_rates(analytics),
            "rejection_distribution": landscape.rejection_reason_counts(),
        }
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                json.dumps(payload, sort_keys=True, indent=2) + "\n",
                encoding="utf-8",
            )
        print(json.dumps(payload, sort_keys=True, indent=2))
        return 0

    raise ValueError(f"unsupported landscape command: {args.landscape_command}")


def _run_selector(args: argparse.Namespace) -> int:
    if args.selector_command == "replay":
        try:
            campaign = ResearchCampaignConfig.from_yaml(args.campaign)
            expected = _load_selection_result(args.selection_result)
            candidates = _load_json_or_jsonl_records(args.candidate_results)
            result = CandidateSelector(_selection_policy_from_campaign(campaign)).select(candidates)
        except (FileNotFoundError, ValueError) as exc:
            print(str(exc), file=sys.stderr)
            return 2
        replayed = result.to_payload()
        reasons = _selector_replay_reasons(expected, replayed)
        payload = {
            "accepted": not reasons,
            "expected_selection_hash": expected.get("selection_hash"),
            "rejected_candidates": replayed["rejected_candidates"],
            "replayed_selection_hash": replayed["selection_hash"],
            "reasons": reasons,
            "replayed": replayed,
            "selected_candidates": replayed["selected_candidates"],
        }
        print(json.dumps(payload, sort_keys=True, indent=2))
        return 0 if not reasons else 1
    raise ValueError(f"unsupported selector command: {args.selector_command}")


def _load_json_mapping(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _load_selection_result(path: Path) -> dict[str, Any]:
    if path.suffix.lower() != ".jsonl":
        return _load_json_mapping(path)
    sibling = path.with_name("selection_result.json")
    if not sibling.exists():
        raise ValueError(
            "selector replay requires selection_result.json when "
            f"--selection-result points at JSONL rows: {path}"
        )
    return _load_json_mapping(sibling)


def _load_mapping(path: Path) -> dict[str, Any]:
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
    else:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"{path} must contain a mapping")
    return dict(payload)


def _load_json_records(path: Path | None) -> tuple[dict[str, Any], ...]:
    if path is None:
        return ()
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"{path} must contain a JSON array")
    records: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError(f"{path} must contain only JSON objects")
        records.append(dict(item))
    return tuple(records)


def _load_json_or_jsonl_records(path: Path) -> tuple[dict[str, Any], ...]:
    text = path.read_text(encoding="utf-8")
    rows: Any
    if path.suffix.lower() == ".jsonl":
        rows = [json.loads(line) for line in text.splitlines() if line.strip()]
    else:
        payload = json.loads(text)
        if isinstance(payload, Mapping):
            rows = payload.get("candidate_results", payload.get("candidates", ()))
            if not rows and "candidate_id" in payload:
                rows = (payload,)
        else:
            rows = payload
    if not isinstance(rows, Sequence) or isinstance(rows, str):
        raise ValueError(f"{path} must contain candidate result rows")
    records: list[dict[str, Any]] = []
    for item in rows:
        if not isinstance(item, Mapping):
            raise ValueError(f"{path} must contain only candidate result objects")
        records.append(dict(item))
    return tuple(records)


def _data_paths_from_args(values: Sequence[str]) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"--data-path must use ROOT=PATH: {value}")
        root, path_text = value.split("=", 1)
        root = root.strip()
        if not root:
            raise ValueError("--data-path root must not be empty")
        if root in result:
            raise ValueError(f"duplicate --data-path root: {root}")
        path = Path(path_text).expanduser()
        if not path.exists():
            raise ValueError(f"data path does not exist for {root}: {path}")
        result[root] = path
    return result


def _write_campaign_state(
    output_root: Path,
    status: str,
    reason: str,
    *,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    payload = {
        "reason": reason,
        "status": status,
        "updated_at": datetime.now(UTC).isoformat(),
    }
    if extra is not None:
        payload.update(dict(extra))
    (output_root / "campaign_state.json").write_text(
        json.dumps(payload, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def _load_optional_campaign_state(output_root: Path) -> dict[str, Any]:
    state_path = output_root / "campaign_state.json"
    if not state_path.exists():
        return {}
    return _load_json_mapping(state_path)


def _run_campaign_engine(run: AutonomousResearchRun) -> Any:
    return AutonomousResearchEngine(repo_root=_REPO_ROOT).run(run)


def _required_state_path(state: Mapping[str, Any], field_name: str) -> Path:
    value = state.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"campaign state missing {field_name}")
    return Path(value)


def _state_positive_int(state: Mapping[str, Any], field_name: str) -> int:
    value = state.get(field_name)
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"campaign state missing positive integer {field_name}")
    return value


def _state_data_paths(state: Mapping[str, Any]) -> dict[str, Path]:
    value = state.get("data_paths")
    if not isinstance(value, Mapping) or not value:
        raise ValueError("campaign state missing data_paths")
    paths: dict[str, Path] = {}
    for root, path_text in value.items():
        if not isinstance(root, str) or not isinstance(path_text, str):
            raise ValueError("campaign state data_paths must map text roots to text paths")
        paths[root] = Path(path_text)
    return paths


def _approval_record_from_state(state: Mapping[str, Any]) -> GenerationApprovalRecord:
    proposal_id = state.get("proposal_id")
    proposal_hash = state.get("proposal_hash")
    decision = state.get("decision")
    reviewer = state.get("reviewer")
    reason = state.get("reason")
    if not isinstance(proposal_id, str) or not proposal_id.strip():
        raise ValueError("campaign state missing proposal_id")
    if not isinstance(proposal_hash, str) or not proposal_hash.strip():
        raise ValueError("campaign state missing proposal_hash")
    if decision != "approved":
        raise ValueError("campaign state decision must be approved")
    if not isinstance(reviewer, str) or not reviewer.strip():
        raise ValueError("campaign state missing reviewer")
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("campaign state missing approval reason")
    return GenerationApprovalRecord(
        proposal_id=proposal_id,
        proposal_hash=proposal_hash,
        decision=decision,
        reviewer=reviewer,
        decided_at=datetime.now(UTC),
        reason=reason,
        evidence_refs=(proposal_hash,),
    )


def _acceptance_markers_from_campaign(campaign_path: Path) -> dict[str, Any]:
    raw = _load_mapping(campaign_path)
    execution = raw.get("execution", {})
    selection = raw.get("selection", {})
    launch_controls = raw.get("launch_controls", {})
    if not isinstance(execution, Mapping):
        execution = {}
    if not isinstance(selection, Mapping):
        selection = {}
    if not isinstance(launch_controls, Mapping):
        launch_controls = {}
    paper_live_disabled = launch_controls.get("paper_live_launches") == "disabled"
    return {
        "execution_mode": execution.get("default_mode"),
        "gauntlet": selection.get("gauntlet"),
        "metrics_source": execution.get("metrics_source"),
        "paper_live_launches": [] if paper_live_disabled else ["not_disabled"],
        "selector": selection.get("selector"),
    }


def _annotate_operator_acceptance_artifacts(
    output_root: Path,
    acceptance_markers: Mapping[str, Any],
) -> None:
    rejected_path = output_root / "rejected_candidates.jsonl"
    rejected_rows = _read_jsonl(rejected_path)
    if rejected_rows:
        _write_jsonl(
            rejected_path,
            [_annotated_rejected_candidate(row) for row in rejected_rows],
        )
    summary_path = output_root / "validation_summary.json"
    if summary_path.exists():
        summary = _load_json_mapping(summary_path)
        summary["paper_live_launches"] = list(acceptance_markers.get("paper_live_launches", []))
        summary["real_path_markers"] = {
            "execution_mode": acceptance_markers.get("execution_mode"),
            "gauntlet": acceptance_markers.get("gauntlet"),
            "metrics_source": acceptance_markers.get("metrics_source"),
            "selector": acceptance_markers.get("selector"),
        }
        summary_path.write_text(
            json.dumps(summary, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )


def _annotated_rejected_candidate(row: Mapping[str, Any]) -> dict[str, Any]:
    reasons = _reason_list(row.get("reasons"))
    selector_reasons = _reason_list(row.get("selector_reasons"))
    gauntlet_reasons = _reason_list(row.get("gauntlet_reasons"))
    stage = str(row.get("rejection_stage") or row.get("stage") or "")
    if not selector_reasons and stage == "selector":
        selector_reasons = reasons
    if not gauntlet_reasons and stage == "gauntlet":
        gauntlet_reasons = reasons
    return {
        **dict(row),
        "gauntlet_reasons": gauntlet_reasons,
        "selector_reasons": selector_reasons,
    }


def _reason_list(value: Any) -> list[str]:
    if isinstance(value, Sequence) and not isinstance(value, str):
        return [str(reason) for reason in value]
    return []


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, Mapping):
            raise ValueError(f"{path} must contain JSON object rows")
        rows.append(dict(payload))
    return rows


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(dict(row), sort_keys=True) + "\n")


def _family_success_rates(analytics: FitnessAnalytics) -> dict[str, float]:
    return {
        f"{summary.strategy_family}/{summary.factor_family}": summary.family_success_rate
        for summary in analytics.family_summaries
    }


def _selection_policy_from_campaign(campaign: ResearchCampaignConfig) -> SelectionPolicy:
    constraints = {constraint.name: constraint.value for constraint in campaign.constraints}
    return SelectionPolicy(
        max_drawdown=constraints.get("max_drawdown", 0.25),
        min_oos_trade_count=int(constraints.get("min_oos_trade_count", 30)),
        max_selected=1,
        purpose="promotion",
        total_return_metric="performance.total_return",
        oos_sharpe_metric="performance.oos_sharpe",
        max_drawdown_metric="performance.max_drawdown",
        oos_trade_count_metric="trading.oos_trade_count",
        cost_sensitivity_metric="costs.cost_sensitivity",
    )


def _selector_replay_reasons(
    expected: Mapping[str, Any],
    replayed: Mapping[str, Any],
) -> list[str]:
    reasons: list[str] = []
    if expected.get("selection_hash") != replayed.get("selection_hash"):
        reasons.append("selector replay mismatch: selection_hash changed")
    if expected.get("policy") != replayed.get("policy"):
        reasons.append("selector replay mismatch: constraints changed")
    expected_selected = expected.get("selected_candidates")
    replayed_selected = replayed.get("selected_candidates")
    if expected_selected != replayed_selected:
        reasons.append("selector replay mismatch: selected candidates changed")
    expected_rejected = expected.get("rejected_candidates")
    replayed_rejected = replayed.get("rejected_candidates")
    if expected_rejected != replayed_rejected:
        reasons.append("selector replay mismatch: rejected candidates changed")
    return reasons


def _required_mapping_text(payload: Mapping[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required")
    return value.strip()


def _find_reproducibility_v2_path(bundle: ResearchEvidenceBundle) -> str | None:
    if bundle.artifact_paths:
        for path_text in bundle.artifact_paths.keys():
            if path_text.endswith("reproducibility_v2.json"):
                return path_text
    return None


def _reproducibility_v2_blockers(path: Path) -> tuple[str, ...]:
    try:
        payload = _load_json_mapping(path)
    except (OSError, ValueError) as exc:
        return (f"reproducibility_v2 is not readable or invalid JSON: {exc}",)
    try:
        snapshot = ReproducibilitySnapshotV2.from_payload(payload)
    except (TypeError, ValueError) as exc:
        return (f"reproducibility_v2 is invalid: {exc}",)
    return snapshot.promotion_blockers()


def _optional_mapping_text(payload: Mapping[str, Any], field_name: str) -> str | None:
    value = payload.get(field_name)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be text")
    return value.strip() or None


def _artifact_safe_name(value: str) -> str:
    safe = "".join(char if char.isalnum() or char in "._-" else "_" for char in value)
    return safe.strip("._-") or "artifact"


def _ensure_repo_root_on_path() -> None:
    repo_root = str(_REPO_ROOT)
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)


def main(argv: Sequence[str] | None = None) -> int:
    """Perform main."""

    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.dry_run:
        if args.command is not None:
            parser.error("--dry-run cannot be combined with a subcommand")
        _ensure_repo_root_on_path()
        result = ResearchDryRunRunner(repo_root=_REPO_ROOT).run(
            args.config,
            argv=sys.argv[1:] if argv is None else list(argv),
        )
        print(json.dumps(result.to_payload(), sort_keys=True, indent=2))
        return 0
    if args.command is None:
        parser.error("a subcommand or --dry-run is required")
    if args.command == "evidence":
        return _run_evidence(args)
    if args.command == "promotion":
        return _run_promotion(args)
    if args.command == "manifest":
        return _run_manifest(args)
    if args.command == "audit":
        return _run_audit(args)
    if args.command == "graph":
        return _run_graph(args)
    if args.command == "data-quality":
        return _run_data_quality(args)
    if args.command == "idea":
        return _run_idea(args)
    if args.command == "meta":
        return _run_meta(args)
    if args.command == "campaign":
        return _run_campaign(args)
    if args.command == "landscape":
        return _run_landscape(args)
    if args.command == "selector":
        return _run_selector(args)
    session = ResearchSession.from_yaml(args.config)
    if args.command == "factor-tearsheet":
        return _record_factor_tearsheet(args, session)
    if args.command == "runs":
        return _list_runs(args, session)
    if args.command == "workflow":
        return _run_workflow(args, session)
    parser.error(f"unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
