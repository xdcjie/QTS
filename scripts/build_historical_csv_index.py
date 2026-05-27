"""Build daily byte-offset indexes for ordered historical CSV files."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from qts.data.historical.csv_index import DEFAULT_TIMESTAMP_COLUMN, write_historical_csv_index


def main(argv: Sequence[str] | None = None) -> int:
    """Build sidecar indexes for one or more CSV files."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_paths", nargs="+", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        help="Index output path. Only valid when indexing one CSV file.",
    )
    parser.add_argument("--timestamp-column", default=DEFAULT_TIMESTAMP_COLUMN)
    args = parser.parse_args(argv)

    if args.output is not None and len(args.csv_paths) != 1:
        parser.error("--output can only be used with one CSV path")

    for csv_path in args.csv_paths:
        index_path = write_historical_csv_index(
            csv_path,
            output_path=args.output,
            timestamp_column=args.timestamp_column,
        )
        print(index_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
