"""Generate a human-readable analyst report for a completed backtest run."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from qts.reporting.backtest_analyst import AnalystBacktestReportGenerator


def main(argv: Sequence[str] | None = None) -> int:
    """Generate HTML and optionally PDF analyst report artifacts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "source",
        type=Path,
        help="Completed run directory or *.summary.json path.",
    )
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument(
        "--no-pdf",
        action="store_true",
        help="Write HTML only and skip Chrome PDF export.",
    )
    args = parser.parse_args(argv)

    generated = AnalystBacktestReportGenerator().generate(
        args.source,
        output_dir=args.output_dir,
        write_pdf=not args.no_pdf,
    )
    print(generated.html_path)
    if not args.no_pdf:
        print(generated.pdf_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
