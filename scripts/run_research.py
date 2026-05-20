"""Run notebook-friendly research workflows from a small CLI."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from qts.research import ResearchSession
from qts.research.workflow import ResearchWorkflowConfig, ResearchWorkflowRunner

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
        "--format",
        choices=("json", "text"),
        default="json",
        help="Workflow result output format",
    )


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
    result = ResearchWorkflowRunner().run(
        session,
        ResearchWorkflowConfig.from_yaml(args.workflow_config),
    )
    if args.format == "json":
        print(json.dumps(result.to_payload(), sort_keys=True, indent=2))
    else:
        print(f"workflow_id={result.workflow_id}")
        print(f"status={result.status}")
        for step in result.steps:
            print(f"{step.step_id}={step.status}")
    return 0 if result.succeeded else 1


def _ensure_repo_root_on_path() -> None:
    repo_root = str(_REPO_ROOT)
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)


def main(argv: Sequence[str] | None = None) -> int:
    """Perform main."""

    parser = _build_parser()
    args = parser.parse_args(argv)
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
