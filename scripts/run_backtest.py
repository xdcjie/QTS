"""Run a config-driven backtest."""

from __future__ import annotations

import argparse
import json
import time
from collections.abc import Sequence
from pathlib import Path

from qts.backtest.runner import run_backtest


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("runs/backtests"))
    args = parser.parse_args(argv)

    started = time.perf_counter()
    run = run_backtest(args.config, output_dir=args.output_dir)
    elapsed_seconds = time.perf_counter() - started
    summary = json.loads(run.summary_path.read_text(encoding="utf-8"))
    summary["elapsed_seconds"] = elapsed_seconds
    run.summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(run.manifest_path)
    print(run.summary_path)
    print(f"elapsed_seconds={elapsed_seconds:.6f}")
    print(f"processed_rows={summary['processed_rows']}")
    print(f"emitted_bars={summary['emitted_bars']}")
    print(f"excluded_spreads={summary['excluded_spreads']}")
    print(f"contracts_excluded={summary['contracts_excluded']}")
    print(f"processed_bars={summary['processed_bars']}")
    print(f"warmup_bars={summary['warmup_bars']}")
    print(f"trading_bars={summary['trading_bars']}")
    print(f"report_hash={summary['report_hash']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
