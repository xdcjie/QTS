"""Validate a research promotion candidate against an evidence registry."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from qts.research.evidence_policy import (
    EvidenceCompletenessPolicy,
    PromotionEvidenceSpec,
)
from qts.research.evidence_registry import EvidenceRegistry


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path, help="Promotion candidate YAML/JSON file")
    parser.add_argument(
        "--evidence-registry-root",
        type=Path,
        default=Path("runs/research/evidence"),
        help="Evidence registry root directory",
    )
    return parser


def _load_mapping(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
    else:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"{path} must contain a mapping")
    return dict(payload)


def main(argv: Sequence[str] | None = None) -> int:
    """Validate a promotion candidate and emit a machine-readable result."""

    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        candidate = PromotionEvidenceSpec.from_payload(_load_mapping(args.candidate))
        result = EvidenceCompletenessPolicy.promotion_candidate().validate_candidate(
            candidate,
            evidence_registry=EvidenceRegistry(args.evidence_registry_root),
        )
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result.to_payload(), sort_keys=True, indent=2))
    return 0 if result.accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
