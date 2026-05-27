"""Run notebook-friendly research workflows from a small CLI."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from datetime import date
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from qts.research import ResearchSession
from qts.research.artifact_graph import ResearchArtifactGraph, ResearchArtifactGraphWriter
from qts.research.audit_log import ResearchAuditLog
from qts.research.data_quality import DataQualityArtifactWriter, DataQualityRunner
from qts.research.evidence_policy import (
    EvidenceCompletenessPolicy,
    PromotionEvidenceSpec,
)
from qts.research.evidence_registry import EvidenceRegistry
from qts.research.experiment_store import ExperimentStore
from qts.research.idea_registry import IdeaRegistry
from qts.research.idea_spec import IdeaSpec
from qts.research.meta_research import MetaResearchSummary, MetaResearchSummaryWriter
from qts.research.promotion_packet import PromotionPacketV2
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
        default=None,
        help="Optional Research OS audit log root for evidence lifecycle records",
    )
    parser.add_argument(
        "--artifact-graph-root",
        type=Path,
        default=None,
        help="Optional artifact graph output root for evidence lifecycle records",
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
        help="Verify evidence bundle hashes before attempting reproduction",
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
        help="Validate a promotion candidate against a research evidence bundle",
    )
    validate_source = validate.add_mutually_exclusive_group(required=True)
    validate_source.add_argument("--candidate", type=Path)
    validate_source.add_argument("--packet", type=Path)
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


def _add_graph_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("graph", help="Verify Research OS artifact graphs")
    graph_subparsers = parser.add_subparsers(dest="graph_command", required=True)
    verify = graph_subparsers.add_parser("verify", help="Verify one artifact graph JSON file")
    verify.add_argument("--graph", type=Path, required=True)


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
    _add_audit_parser(subparsers)
    _add_graph_parser(subparsers)
    _add_data_quality_parser(subparsers)
    _add_idea_parser(subparsers)
    _add_meta_parser(subparsers)
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
        result = ResearchWorkflowRunner().run(
            session,
            ResearchWorkflowConfig.from_yaml(args.workflow_config),
            step_id=args.step_id,
            from_step_id=args.from_step_id,
            to_step_id=args.to_step_id,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(result.to_payload(), sort_keys=True, indent=2))
    else:
        print(f"workflow_id={result.workflow_id}")
        print(f"status={result.status}")
        for step in result.steps:
            print(f"{step.step_id}={step.status}")
    return 0 if result.succeeded else 1


def _run_evidence(args: argparse.Namespace) -> int:
    registry = EvidenceRegistry(args.registry_root)
    audit_log = None if args.audit_log_root is None else ResearchAuditLog(args.audit_log_root)
    artifact_graph_writer = (
        None
        if args.artifact_graph_root is None
        else ResearchArtifactGraphWriter(args.artifact_graph_root)
    )
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
        payload = {
            **verification.to_payload(),
            "evidence_bundle_id": args.bundle_id,
            "reproduction_boundary": "verify_hashes_before_reproduce",
        }
        print(json.dumps(payload, sort_keys=True, indent=2))
        return 0 if verification.accepted else 1
    raise ValueError(f"unsupported evidence command: {args.evidence_command}")


def _run_promotion(args: argparse.Namespace) -> int:
    if args.promotion_command == "validate":
        try:
            evidence_registry = EvidenceRegistry(args.evidence_registry_root)
            if args.packet is not None:
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
            else:
                candidate = PromotionEvidenceSpec.from_payload(_load_mapping(args.candidate))
                candidate_result = (
                    EvidenceCompletenessPolicy.promotion_candidate().validate_candidate(
                        candidate,
                        evidence_registry=evidence_registry,
                        audit_log=ResearchAuditLog(args.audit_log_root),
                    )
                )
                print(json.dumps(candidate_result.to_payload(), sort_keys=True, indent=2))
                return 0 if candidate_result.accepted else 1
        except (FileNotFoundError, ValueError) as exc:
            print(str(exc), file=sys.stderr)
            return 2
    raise ValueError(f"unsupported promotion command: {args.promotion_command}")


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
            graph.validate()
        except (FileNotFoundError, ValueError) as exc:
            print(json.dumps({"accepted": False, "reasons": [str(exc)]}, sort_keys=True, indent=2))
            return 1
        print(
            json.dumps(
                {
                    "accepted": True,
                    "artifact_graph_hash": graph.stable_hash(),
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
            result = DataQualityArtifactWriter(args.output_dir).write(artifact)
        except (FileNotFoundError, ValueError) as exc:
            print(json.dumps({"accepted": False, "reasons": [str(exc)]}, sort_keys=True, indent=2))
            return 1
        print(
            json.dumps(
                {
                    "accepted": artifact.accepted,
                    "artifact": artifact.to_payload(),
                    "artifact_hash": result.artifact_hash,
                    "path": str(result.path),
                    "reasons": [
                        f"{item['code']}: {item['message']}" for item in artifact.blockers()
                    ],
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


def _load_json_mapping(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


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


def _required_mapping_text(payload: Mapping[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required")
    return value.strip()


def _optional_mapping_text(payload: Mapping[str, Any], field_name: str) -> str | None:
    value = payload.get(field_name)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be text")
    return value.strip() or None


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
