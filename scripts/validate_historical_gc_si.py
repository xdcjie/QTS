"""Validate local GC/SI historical datasets and write JSON evidence."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from qts.data.historical.csv_dataset import validate_historical_sample
from qts.data.historical.gc_si import load_gc_si_catalog


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("historical"))
    parser.add_argument("--sample-rows", type=int, default=1000)
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=Path("evidence/historical"))
    args = parser.parse_args(argv)

    sample_rows = None if args.full else args.sample_rows
    catalog = load_gc_si_catalog(args.root)
    payload: dict[str, object] = {
        "root": str(args.root),
        "sample_rows": sample_rows,
        "full": bool(args.full),
        "created_at": datetime.now(tz=UTC).isoformat(),
        "datasets": {},
    }
    datasets: dict[str, object] = {}
    for root, dataset in catalog.datasets.items():
        sample = validate_historical_sample(
            dataset.csv_path,
            dataset.chain,
            sample_rows=sample_rows,
        )
        datasets[root] = {
            "csv_path": str(dataset.csv_path),
            "chain_path": str(dataset.chain_path),
            "stats": sample.stats.as_dict(),
            "valid": sample.report.valid,
            "max_severity": (
                None if sample.report.max_severity is None else sample.report.max_severity.value
            ),
            "issues": [
                {
                    "code": issue.code.value,
                    "message": issue.message,
                    "severity": issue.severity.value,
                }
                for issue in sample.report.issues
            ],
        }
    payload["datasets"] = datasets

    args.output_dir.mkdir(parents=True, exist_ok=True)
    mode = "full" if args.full else f"sample_{args.sample_rows}"
    output_path = args.output_dir / f"gc_si_validation_{mode}.json"
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
