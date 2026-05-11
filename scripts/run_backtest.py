"""Run a config-driven backtest."""

from __future__ import annotations

import argparse
import json
import time
from collections.abc import Sequence
from pathlib import Path

from qts.backtest.runner import run_backtest, run_streaming_backtest


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("runs/backtests"))
    parser.add_argument("--streaming", action="store_true")
    args = parser.parse_args(argv)

    started = time.perf_counter()
    if args.streaming:
        run = run_streaming_backtest(args.config, output_dir=args.output_dir)
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

    run = run_backtest(args.config, output_dir=args.output_dir)
    elapsed_seconds = time.perf_counter() - started
    summary_path = args.output_dir / f"{run.result.run_id.value}.summary.json"
    processed_rows = sum(item["rows_seen"] for item in run.dataset_stats.values())
    emitted_bars = sum(item["bars_emitted"] for item in run.dataset_stats.values())
    excluded_spreads = sum(item["spreads_excluded"] for item in run.dataset_stats.values())
    contracts_excluded = sum(
        item.get("contracts_excluded", 0) for item in run.dataset_stats.values()
    )
    summary_path.write_text(
        json.dumps(
            {
                "contracts_excluded": contracts_excluded,
                "elapsed_seconds": elapsed_seconds,
                "processed_rows": processed_rows,
                "emitted_bars": emitted_bars,
                "excluded_spreads": excluded_spreads,
                "report_path": str(run.report_path),
                "report_hash": run.result.report_hash,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    print(run.report_path)
    print(summary_path)
    print(f"elapsed_seconds={elapsed_seconds:.6f}")
    print(f"processed_rows={processed_rows}")
    print(f"emitted_bars={emitted_bars}")
    print(f"excluded_spreads={excluded_spreads}")
    print(f"contracts_excluded={contracts_excluded}")
    print(f"processed_bars={run.result.processed_bars}")
    print(f"warmup_bars={run.result.warmup_bars}")
    print(f"trading_bars={run.result.trading_bars}")
    print(f"report_hash={run.result.report_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
