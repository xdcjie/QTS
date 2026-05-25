"""Run notebook-friendly research workflows from a small CLI."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path
from typing import Any

from qts.research import ResearchSession
from qts.research.evidence_registry import EvidenceRegistry
from qts.research.idea_registry import IdeaRegistry
from qts.research.idea_spec import IdeaSpec
from qts.research.meta_research import MetaResearchSummary, MetaResearchSummaryWriter
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
    evidence_subparsers = parser.add_subparsers(dest="evidence_command", required=True)

    bundle = evidence_subparsers.add_parser(
        "bundle",
        help="Create an evidence bundle from a workflow JSON summary",
    )
    bundle.add_argument("--workflow-summary", type=Path, required=True)
    bundle.add_argument("--idea-id", default=None)
    bundle.add_argument("--strategy-id", default=None)

    evidence_subparsers.add_parser("list", help="List evidence bundles")

    show = evidence_subparsers.add_parser("show", help="Show one evidence bundle")
    show.add_argument("bundle_id")

    verify = evidence_subparsers.add_parser("verify", help="Verify one evidence bundle")
    verify.add_argument("bundle_id")


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
    summary.add_argument("--evidence-records", type=Path, default=None)
    summary.add_argument("--experiment-records", type=Path, default=None)
    summary.add_argument("--period", required=True)
    summary.add_argument("--period-start", required=True)
    summary.add_argument("--trial-count-outlier-threshold", type=int, default=10)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/research/quickstart.yaml"),
        help="Research session YAML config",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    _add_factor_tearsheet_parser(subparsers)
    _add_runs_parser(subparsers)
    _add_workflow_parser(subparsers)
    _add_evidence_parser(subparsers)
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
    if args.evidence_command == "bundle":
        bundle = registry.create_from_workflow_summary(
            args.workflow_summary,
            idea_id=args.idea_id,
            strategy_id=args.strategy_id,
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
        verification = registry.verify(args.bundle_id)
        print(json.dumps(verification.to_payload(), sort_keys=True, indent=2))
        return 0 if verification.accepted else 1
    raise ValueError(f"unsupported evidence command: {args.evidence_command}")


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
        evidence_records = _load_json_records(args.evidence_records)
        experiment_records = _load_json_records(args.experiment_records)
        summary = MetaResearchSummary.from_registries(
            ideas=ideas,
            evidence_records=evidence_records,
            experiment_records=experiment_records,
            period=args.period,
            period_start=date.fromisoformat(args.period_start),
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


def _ensure_repo_root_on_path() -> None:
    repo_root = str(_REPO_ROOT)
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)


def main(argv: Sequence[str] | None = None) -> int:
    """Perform main."""

    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "evidence":
        return _run_evidence(args)
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
