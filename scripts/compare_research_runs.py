"""Compare registered manifest-driven research runs."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from qts.research.registry import ResearchRunRegistry, latest_record


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("artifacts/research/index.jsonl"),
        help="Research-system JSONL registry",
    )
    parser.add_argument("--output", type=Path, default=None, help="Markdown comparison path")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    records = ResearchRunRegistry(args.registry).list()
    if not records:
        parser.error(f"research registry is empty: {args.registry}")
    output_path = args.output or latest_record(records).artifact_dir / "comparison.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_comparison_markdown(records), encoding="utf-8")
    print(str(output_path))
    return 0


def _comparison_markdown(records: tuple[Any, ...]) -> str:
    lines = [
        "# Research Run Comparison",
        "",
        "| Run ID | Status | Promotion | Candidate count | Sharpe | Manifest hash |",
        "| --- | --- | --- | ---: | ---: | --- |",
    ]
    for record in records:
        metrics = _read_json(record.artifact_dir / "metrics.json")
        lines.append(
            "| {run_id} | {status} | {promotion} | {candidate_count} | {sharpe} | {hash} |".format(
                candidate_count=_nested(metrics, "research", "candidate_count"),
                hash=record.manifest_hash,
                promotion=record.promotion_status,
                run_id=record.run_id,
                sharpe=_nested(metrics, "quality", "sharpe"),
                status=record.status,
            )
        )
    return "\n".join(lines) + "\n"


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _nested(payload: dict[str, Any], group: str, field_name: str) -> Any:
    group_value = payload.get(group)
    if not isinstance(group_value, dict):
        return None
    return group_value.get(field_name)


if __name__ == "__main__":
    raise SystemExit(main())
