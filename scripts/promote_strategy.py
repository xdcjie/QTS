"""Evaluate research promotion gates for a completed research run."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from qts.research.promotion import ResearchPromotionPolicy


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True, help="Research artifact directory")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/promotion/default.yaml"),
        help="Promotion gate policy YAML",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    manifest = _read_json(args.run_dir / "resolved_manifest.json")
    metrics = _read_json(args.run_dir / "metrics.json")
    reproducibility = _read_json(args.run_dir / "reproducibility.json")
    run = _mapping(manifest, "run")
    strategy = _mapping(manifest, "strategy")
    decision = ResearchPromotionPolicy.from_yaml(args.config).evaluate(
        run_id=_required_text(run, "id"),
        strategy_id=_required_text(strategy, "id"),
        metrics=metrics,
        reproducibility=reproducibility,
    )
    output = args.run_dir / "promotion_decision.json"
    output.write_text(
        json.dumps(decision.to_payload(), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(str(output))
    return 0 if decision.status == "research_passed" else 1


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _mapping(payload: dict[str, Any], field_name: str) -> dict[str, Any]:
    value = payload.get(field_name)
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return value


def _required_text(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required")
    return value.strip()


if __name__ == "__main__":
    raise SystemExit(main())
