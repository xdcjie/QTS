from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from qts.backtest.engine import BacktestEngine, BacktestStreamResult


@dataclass(frozen=True, slots=True)
class CapturedBacktestStream:
    result: BacktestStreamResult
    manifest: dict[str, Any]
    orders: tuple[dict[str, Any], ...]
    fills: tuple[dict[str, Any], ...]
    trade_ledger: tuple[dict[str, Any], ...]
    equity_curve: tuple[dict[str, Any], ...]


def run_engine_streaming(
    engine: BacktestEngine,
    output_dir: Path,
) -> CapturedBacktestStream:
    result = engine.run_streaming(output_dir)
    return capture_stream_result(result)


def capture_stream_result(result: BacktestStreamResult) -> CapturedBacktestStream:
    return CapturedBacktestStream(
        result=result,
        manifest=json.loads(Path(result.manifest_path).read_text(encoding="utf-8")),
        orders=_read_ndjson(Path(result.artifact_paths["orders"])),
        fills=_read_ndjson(Path(result.artifact_paths["fills"])),
        trade_ledger=_read_ndjson(Path(result.artifact_paths["trade_ledger"])),
        equity_curve=_read_ndjson(Path(result.artifact_paths["equity_curve"])),
    )


def _read_ndjson(path: Path) -> tuple[dict[str, Any], ...]:
    return tuple(
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    )
