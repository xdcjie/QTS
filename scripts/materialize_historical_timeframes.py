"""Materialize derived historical OHLCV timeframes under per-root directories.

The script derives higher timeframes from the existing 1m CSV source while
preserving project timeframe semantics:

- clock-aligned `<1d` bars in exchange timezone;
- session-aligned `1d` bars using futures chain trading hours;
- daily sidecar indexes for every generated CSV.

The source CSV is treated as the trusted market-data tape. Missing 1m slots are
not synthesized by this script.

Run from the repository root with `PYTHONPATH=backend/src`.
"""

from __future__ import annotations

import argparse
import csv
import heapq
import json
import shutil
import sys
from collections.abc import Iterable, Sequence
from concurrent.futures import ProcessPoolExecutor, as_completed
from contextlib import ExitStack
from dataclasses import dataclass, replace
from datetime import UTC
from decimal import Decimal
from pathlib import Path
from time import monotonic
from typing import Any

import yaml
from qts.core.ids import InstrumentId
from qts.data.bars.aggregator import BarAggregator
from qts.data.bars.timeframe import AlignmentMode, Timeframe
from qts.data.historical.chains import HistoricalChain
from qts.data.historical.csv_dataset import iter_historical_bars
from qts.data.historical.csv_format import EXPECTED_HISTORICAL_COLUMNS
from qts.data.historical.csv_index import write_historical_csv_index
from qts.domain.market_data import Bar

DEFAULT_ROOTS = ("GC", "SI")
DEFAULT_TIMEFRAMES = ("1m", "5m", "10m", "15m", "30m", "1h", "4h", "1d")
DEFAULT_DATA_CONFIG = Path("configs/data/historical.local.yaml")
DEFAULT_SOURCE_DIR = Path("historical/data")
DEFAULT_OUTPUT_DIR = Path("historical/data")
DEFAULT_CHAINS_DIR = Path("historical/chains")
SOURCE_TIMEFRAME = "1m"
SORT_CHUNK_ROWS = 500_000
COPY_CHUNK_BYTES = 16 * 1024 * 1024


class ProgressReporter:
    """Small stderr progress reporter for long-running materialization jobs."""

    def __init__(
        self,
        *,
        quiet: bool,
        progress_every: int,
        line_mode: bool = False,
    ) -> None:
        self._quiet = quiet
        self._progress_every = max(1, progress_every)
        self._is_tty = sys.stderr.isatty() and not line_mode
        self._stage_starts: dict[str, float] = {}

    def event(self, message: str) -> None:
        if self._quiet:
            return
        print(message, file=sys.stderr)

    def bar(
        self,
        label: str,
        *,
        current: int,
        total: int,
        unit: str,
        extra: str = "",
        force: bool = False,
    ) -> None:
        if self._quiet:
            return
        if not force and unit == "rows" and current % self._progress_every != 0:
            return
        start = self._stage_starts.setdefault(label, monotonic())
        elapsed = max(monotonic() - start, 0.0)
        rate = current / elapsed if elapsed > 0 else 0.0
        if total <= 0:
            line = f"{label}: {current:,} {unit}"
        else:
            ratio = min(max(current / total, 0.0), 1.0)
            filled = int(ratio * 30)
            bar = "#" * filled + "." * (30 - filled)
            line = (
                f"{label}: [{bar}] {ratio * 100:6.2f}% "
                f"({_progress_value(current, unit)}/{_progress_value(total, unit)})"
            )
        line = (
            f"{line} elapsed={_format_duration(elapsed)} "
            f"rate={_rate_text(rate, unit)} eta={_eta_text(current, total, rate)}"
        )
        if extra:
            line = f"{line} {extra}"
        if self._is_tty:
            sys.stderr.write("\r" + line)
            if force:
                sys.stderr.write("\n")
            sys.stderr.flush()
            if force:
                self._stage_starts.pop(label, None)
            return
        print(line, file=sys.stderr)
        if force:
            self._stage_starts.pop(label, None)


def _progress_value(value: int, unit: str) -> str:
    if unit == "bytes":
        mib = value / (1024 * 1024)
        if mib >= 1024:
            return f"{mib / 1024:.2f}GB"
        return f"{mib:.1f}MB"
    return f"{value:,}"


def _rate_text(rate: float, unit: str) -> str:
    if rate <= 0:
        return "0/s"
    if unit == "bytes":
        return f"{_progress_value(int(rate), unit)}/s"
    return f"{rate:,.0f}/s"


def _eta_text(current: int, total: int, rate: float) -> str:
    if total <= 0:
        return "n/a"
    if current >= total:
        return "0s"
    if rate <= 0:
        return "n/a"
    return _format_duration((total - current) / rate)


def _format_duration(seconds: float) -> str:
    rounded = int(max(seconds, 0.0))
    if rounded < 60:
        return f"{rounded}s"
    minutes, seconds_part = divmod(rounded, 60)
    if minutes < 60:
        return f"{minutes}m{seconds_part:02d}s"
    hours, minutes_part = divmod(minutes, 60)
    return f"{hours}h{minutes_part:02d}m"


@dataclass(frozen=True, slots=True)
class RootMaterializationResult:
    """Files materialized for one futures root."""

    root: str
    outputs: tuple[Path, ...]


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint."""

    args = _parse_args(argv)
    roots = tuple(_normalize_root(root) for root in args.roots)
    timeframes = tuple(_normalize_timeframe(value) for value in args.timeframes)
    _validate_timeframes(timeframes)
    if args.jobs < 1:
        raise ValueError("--jobs must be positive")
    reporter = ProgressReporter(
        quiet=args.quiet,
        progress_every=args.progress_every,
        line_mode=args.jobs > 1,
    )

    if args.jobs == 1 or len(roots) == 1:
        results = [
            materialize_root(
                root=root,
                timeframes=timeframes,
                source_dir=args.source_dir,
                output_dir=args.output_dir,
                chains_dir=args.chains_dir,
                overwrite=args.overwrite,
                reporter=reporter,
            )
            for root in roots
        ]
    else:
        results = _materialize_roots_parallel(
            roots=roots,
            timeframes=timeframes,
            source_dir=args.source_dir,
            output_dir=args.output_dir,
            chains_dir=args.chains_dir,
            overwrite=args.overwrite,
            quiet=args.quiet,
            progress_every=args.progress_every,
            jobs=args.jobs,
        )

    if args.update_config:
        update_historical_data_config(
            args.data_config,
            roots=roots,
            timeframes=timeframes,
            output_dir=args.output_dir,
        )

    for result in results:
        print(f"{result.root}: {len(result.outputs)} files")
        for path in result.outputs:
            print(f"  {path}")
    return 0


def _materialize_roots_parallel(
    *,
    roots: Sequence[str],
    timeframes: Sequence[str],
    source_dir: Path,
    output_dir: Path,
    chains_dir: Path,
    overwrite: bool,
    quiet: bool,
    progress_every: int,
    jobs: int,
) -> list[RootMaterializationResult]:
    """Materialize independent roots concurrently."""

    results_by_root: dict[str, RootMaterializationResult] = {}
    with ProcessPoolExecutor(max_workers=min(jobs, len(roots))) as executor:
        futures = {
            executor.submit(
                materialize_root,
                root=root,
                timeframes=tuple(timeframes),
                source_dir=source_dir,
                output_dir=output_dir,
                chains_dir=chains_dir,
                overwrite=overwrite,
                reporter=ProgressReporter(
                    quiet=quiet,
                    progress_every=progress_every,
                    line_mode=True,
                ),
            ): root
            for root in roots
        }
        for future in as_completed(futures):
            root = futures[future]
            results_by_root[root] = future.result()
    return [results_by_root[root] for root in roots]


def materialize_root(
    *,
    root: str,
    timeframes: Sequence[str],
    source_dir: Path,
    output_dir: Path,
    chains_dir: Path,
    overwrite: bool,
    reporter: ProgressReporter,
) -> RootMaterializationResult:
    """Materialize all requested timeframes for one futures root."""

    source_path = source_dir / f"{root.lower()}.csv"
    if not source_path.exists():
        raise FileNotFoundError(f"source CSV not found for {root}: {source_path}")
    chain_path = chains_dir / f"{root}.json"
    if not chain_path.exists():
        raise FileNotFoundError(f"chain metadata not found for {root}: {chain_path}")

    root_output_dir = output_dir / root
    root_output_dir.mkdir(parents=True, exist_ok=True)
    chain = HistoricalChain.load(chain_path)
    output_paths = {timeframe: root_output_dir / f"{timeframe}.csv" for timeframe in timeframes}
    for output_path in output_paths.values():
        if output_path.exists() and not overwrite:
            raise FileExistsError(f"output exists: {output_path}; pass --overwrite to replace it")

    completed_outputs: dict[str, Path] = {}
    source_row_count = (
        _source_row_count(source_path, reporter=reporter)
        if any(timeframe != SOURCE_TIMEFRAME for timeframe in timeframes)
        else 0
    )

    if SOURCE_TIMEFRAME in timeframes:
        label = f"{root} {SOURCE_TIMEFRAME}"
        output_path = output_paths[SOURCE_TIMEFRAME]
        _copy_source_timeframe(
            source_path=source_path,
            output_path=output_path,
            reporter=reporter,
            label=label,
        )
        _write_historical_index(output_path, reporter=reporter, label=label)
        completed_outputs[SOURCE_TIMEFRAME] = output_path

    derived_timeframes = tuple(
        timeframe for timeframe in timeframes if timeframe != SOURCE_TIMEFRAME
    )
    if derived_timeframes:
        _write_derived_timeframes_single_scan(
            root=root,
            source_path=source_path,
            output_paths={timeframe: output_paths[timeframe] for timeframe in derived_timeframes},
            chain=chain,
            target_timeframes=tuple(Timeframe.parse(timeframe) for timeframe in derived_timeframes),
            source_row_count=source_row_count,
            reporter=reporter,
        )
        for timeframe in derived_timeframes:
            label = f"{root} {timeframe}"
            output_path = output_paths[timeframe]
            _write_historical_index(output_path, reporter=reporter, label=label)
            completed_outputs[timeframe] = output_path

    return RootMaterializationResult(
        root=root,
        outputs=tuple(completed_outputs[timeframe] for timeframe in timeframes),
    )


def _copy_source_timeframe(
    *,
    source_path: Path,
    output_path: Path,
    reporter: ProgressReporter,
    label: str,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    total_bytes = source_path.stat().st_size
    copied_bytes = 0
    with source_path.open("rb") as source, output_path.open("wb") as target:
        for chunk in iter(lambda: source.read(COPY_CHUNK_BYTES), b""):
            target.write(chunk)
            copied_bytes += len(chunk)
            reporter.bar(
                f"{label} copy",
                current=copied_bytes,
                total=total_bytes,
                unit="bytes",
            )
    shutil.copystat(source_path, output_path)
    reporter.bar(
        f"{label} copy",
        current=total_bytes,
        total=total_bytes,
        unit="bytes",
        force=True,
    )


def _write_historical_index(
    path: Path,
    *,
    reporter: ProgressReporter,
    label: str,
) -> None:
    started_at = monotonic()
    reporter.event(f"{label}: writing index")
    write_historical_csv_index(path)
    reporter.event(f"{label}: index done elapsed={_format_duration(monotonic() - started_at)}")


def _write_derived_timeframes_single_scan(
    *,
    root: str,
    source_path: Path,
    output_paths: dict[str, Path],
    chain: HistoricalChain,
    target_timeframes: Sequence[Timeframe],
    source_row_count: int,
    reporter: ProgressReporter,
) -> None:
    for output_path in output_paths.values():
        output_path.parent.mkdir(parents=True, exist_ok=True)

    session_window = chain.session_window()
    stream: Iterable[Bar] = iter_historical_bars(
        source_path,
        chain,
        timeframe=SOURCE_TIMEFRAME,
        session_window=session_window,
    )
    written_rows = {str(timeframe): 0 for timeframe in target_timeframes}
    clock_aggregators: dict[str, dict[InstrumentId, BarAggregator]] = {
        str(timeframe): {}
        for timeframe in target_timeframes
        if timeframe.alignment is AlignmentMode.CLOCK
    }
    daily_states: dict[str, dict[InstrumentId, _DailyAggregationState]] = {
        str(timeframe): {}
        for timeframe in target_timeframes
        if timeframe.alignment is AlignmentMode.SESSION
    }
    processed_source_bars = 0

    def progress_extra() -> str:
        return "written=" + ",".join(
            f"{timeframe}={count:,}" for timeframe, count in written_rows.items()
        )

    with ExitStack() as stack:
        writers: dict[str, Any] = {}
        for timeframe in target_timeframes:
            timeframe_value = str(timeframe)
            handle = stack.enter_context(
                output_paths[timeframe_value].open("w", encoding="utf-8", newline="")
            )
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(EXPECTED_HISTORICAL_COLUMNS)
            writers[timeframe_value] = writer

        for bar in stream:
            processed_source_bars += 1
            for target_timeframe in target_timeframes:
                timeframe_value = str(target_timeframe)
                if target_timeframe.alignment is AlignmentMode.SESSION:
                    completed_bars = _update_daily_aggregation_state(
                        daily_states[timeframe_value],
                        bar,
                        target_timeframe=target_timeframe,
                        session_window=session_window,
                    )
                else:
                    completed_bars = _update_clock_aggregation_state(
                        clock_aggregators[timeframe_value],
                        bar,
                        target_timeframe=target_timeframe,
                        exchange_timezone=chain.timezone,
                    )
                for completed in completed_bars:
                    writers[timeframe_value].writerow(_bar_csv_row(root=root, bar=completed))
                    written_rows[timeframe_value] += 1
            reporter.bar(
                f"{root} multi-aggregate",
                current=processed_source_bars,
                total=source_row_count,
                unit="rows",
                extra=progress_extra(),
            )

        for target_timeframe in target_timeframes:
            timeframe_value = str(target_timeframe)
            if target_timeframe.alignment is AlignmentMode.SESSION:
                for state in daily_states[timeframe_value].values():
                    writers[timeframe_value].writerow(
                        _bar_csv_row(
                            root=root,
                            bar=state.to_bar(
                                timeframe=timeframe_value,
                                session_window=session_window,
                            ),
                        )
                    )
                    written_rows[timeframe_value] += 1
                continue
            for aggregator in clock_aggregators[timeframe_value].values():
                for completed in aggregator.finish().completed:
                    writers[timeframe_value].writerow(_bar_csv_row(root=root, bar=completed))
                    written_rows[timeframe_value] += 1

    reporter.bar(
        f"{root} multi-aggregate",
        current=processed_source_bars,
        total=source_row_count,
        unit="rows",
        extra=f"source_bars={processed_source_bars:,} {progress_extra()}",
        force=True,
    )

    for timeframe in target_timeframes:
        timeframe_value = str(timeframe)
        _sort_csv_file_in_place(
            output_paths[timeframe_value],
            reporter=reporter,
            label=f"{root} {timeframe_value}",
            total_rows=written_rows[timeframe_value],
        )


def _update_clock_aggregation_state(
    aggregators: dict[InstrumentId, BarAggregator],
    bar: Bar,
    *,
    target_timeframe: Timeframe,
    exchange_timezone: str,
) -> tuple[Bar, ...]:
    aggregator = aggregators.get(bar.instrument_id)
    if aggregator is None:
        aggregator = BarAggregator(
            target_timeframe=target_timeframe,
            exchange_timezone=exchange_timezone,
        )
        aggregators[bar.instrument_id] = aggregator
    return aggregator.update(bar).completed


def _update_daily_aggregation_state(
    states: dict[InstrumentId, _DailyAggregationState],
    bar: Bar,
    *,
    target_timeframe: Timeframe,
    session_window: Any,
) -> tuple[Bar, ...]:
    if bar.session_id is None:
        return ()
    completed: list[Bar] = []
    state = states.get(bar.instrument_id)
    if state is not None and state.session_id != bar.session_id:
        completed.append(
            state.to_bar(
                timeframe=str(target_timeframe),
                session_window=session_window,
            )
        )
        state = None
    if state is None:
        states[bar.instrument_id] = _DailyAggregationState.from_bar(bar)
    else:
        states[bar.instrument_id] = state.updated(bar)
    return tuple(completed)


@dataclass(frozen=True, slots=True)
class _DailyAggregationState:
    instrument_id: InstrumentId
    session_id: str
    start_time: Any
    end_time: Any
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    is_complete: bool
    is_partial: bool

    @classmethod
    def from_bar(cls, bar: Bar) -> _DailyAggregationState:
        return cls(
            instrument_id=bar.instrument_id,
            session_id=bar.session_id,
            start_time=bar.start_time,
            end_time=bar.end_time,
            open=bar.open,
            high=bar.high,
            low=bar.low,
            close=bar.close,
            volume=bar.volume,
            is_complete=bar.is_complete,
            is_partial=bar.is_partial,
        )

    def updated(self, bar: Bar) -> _DailyAggregationState:
        if bar.instrument_id != self.instrument_id:
            raise ValueError("cannot aggregate daily bars for different instruments")
        if bar.session_id != self.session_id:
            raise ValueError("cannot aggregate daily bars for different sessions")
        return replace(
            self,
            end_time=bar.end_time,
            high=max(self.high, bar.high),
            low=min(self.low, bar.low),
            close=bar.close,
            volume=self.volume + bar.volume,
            is_complete=self.is_complete and bar.is_complete,
            is_partial=self.is_partial or bar.is_partial,
        )

    def to_bar(self, *, timeframe: str, session_window: Any) -> Bar:
        interval = session_window.interval_for_session_id(self.session_id)
        is_partial = (
            self.is_partial
            or not self.is_complete
            or self.start_time != interval.start
            or self.end_time != interval.end
        )
        return Bar(
            instrument_id=self.instrument_id,
            start_time=interval.start,
            end_time=interval.end,
            timeframe=timeframe,
            session_id=self.session_id,
            open=self.open,
            high=self.high,
            low=self.low,
            close=self.close,
            volume=self.volume,
            is_complete=not is_partial,
            is_partial=is_partial,
        )


def _bar_csv_row(
    *,
    root: str,
    bar: Bar,
) -> tuple[str, str, str, str, str, str, str, str, str, str]:
    return (
        _timestamp_text(bar.start_time),
        "",
        "",
        bar.instrument_id.value,
        _decimal_text(bar.open),
        _decimal_text(bar.high),
        _decimal_text(bar.low),
        _decimal_text(bar.close),
        _decimal_text(bar.volume),
        _symbol_from_instrument_id(root=root, instrument_id=bar.instrument_id),
    )


def _timestamp_text(value: Any) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _decimal_text(value: Decimal) -> str:
    return format(value, "f")


def _symbol_from_instrument_id(*, root: str, instrument_id: InstrumentId) -> str:
    parts = instrument_id.value.split(".")
    if len(parts) >= 4 and parts[0] == "FUTURE" and parts[2] == root:
        return parts[-1]
    return root


def _sort_csv_file_in_place(
    path: Path,
    *,
    reporter: ProgressReporter,
    label: str,
    total_rows: int,
) -> None:
    """Sort generated rows by timestamp and symbol without loading the file at once."""

    chunk_paths: list[Path] = []
    rows_seen = 0
    reporter.event(f"{label}: sorting chunks")
    with path.open("r", encoding="utf-8", newline="") as source:
        header = source.readline()
        chunk: list[str] = []
        for line in source:
            if not line.strip():
                continue
            rows_seen += 1
            chunk.append(line)
            reporter.bar(
                f"{label} sort-read",
                current=rows_seen,
                total=total_rows,
                unit="rows",
            )
            if len(chunk) >= SORT_CHUNK_ROWS:
                chunk_paths.append(_write_sorted_chunk(path, chunk, len(chunk_paths)))
                chunk = []
        if chunk:
            chunk_paths.append(_write_sorted_chunk(path, chunk, len(chunk_paths)))
    reporter.bar(
        f"{label} sort-read",
        current=total_rows,
        total=total_rows,
        unit="rows",
        force=True,
    )

    sorted_path = path.with_suffix(path.suffix + ".sorted")
    reporter.event(f"{label}: merging sorted chunks")
    with sorted_path.open("w", encoding="utf-8", newline="") as target:
        target.write(header)
        _merge_sorted_chunks(
            chunk_paths,
            target,
            reporter=reporter,
            label=label,
            total_rows=total_rows,
        )
    sorted_path.replace(path)
    for chunk_path in chunk_paths:
        chunk_path.unlink(missing_ok=True)


def _write_sorted_chunk(source_path: Path, rows: list[str], index: int) -> Path:
    rows.sort(key=_csv_sort_key)
    chunk_path = source_path.with_suffix(source_path.suffix + f".chunk-{index:04d}")
    chunk_path.write_text("".join(rows), encoding="utf-8")
    return chunk_path


def _merge_sorted_chunks(
    chunk_paths: Sequence[Path],
    target: Any,
    *,
    reporter: ProgressReporter,
    label: str,
    total_rows: int,
) -> None:
    handles = [path.open("r", encoding="utf-8", newline="") for path in chunk_paths]
    try:
        heap: list[tuple[tuple[str, str, str], int, str]] = []
        for index, handle in enumerate(handles):
            line = handle.readline()
            if line:
                heapq.heappush(heap, (_csv_sort_key(line), index, line))
        rows_written = 0
        while heap:
            _key, index, line = heapq.heappop(heap)
            target.write(line)
            rows_written += 1
            reporter.bar(
                f"{label} sort-merge",
                current=rows_written,
                total=total_rows,
                unit="rows",
            )
            next_line = handles[index].readline()
            if next_line:
                heapq.heappush(heap, (_csv_sort_key(next_line), index, next_line))
        reporter.bar(
            f"{label} sort-merge",
            current=total_rows,
            total=total_rows,
            unit="rows",
            force=True,
        )
    finally:
        for handle in handles:
            handle.close()


def _csv_sort_key(line: str) -> tuple[str, str, str]:
    fields = line.rstrip("\r\n").split(",")
    timestamp = fields[0]
    instrument_id = fields[3] if len(fields) > 3 else ""
    symbol = fields[9] if len(fields) > 9 else ""
    return (timestamp, instrument_id, symbol)


def _source_row_count(source_path: Path, *, reporter: ProgressReporter) -> int:
    row_count = _source_row_count_from_index(source_path)
    if row_count is not None:
        return row_count
    return _count_csv_data_rows(source_path, reporter=reporter)


def _source_row_count_from_index(source_path: Path) -> int | None:
    index_paths = (
        source_path.with_suffix(source_path.suffix + ".index.json"),
        source_path.with_suffix(".index.json"),
    )
    for index_path in index_paths:
        if not index_path.exists():
            continue
        payload = json.loads(index_path.read_text(encoding="utf-8"))
        row_count = _find_row_count(payload)
        if row_count is not None:
            return row_count
    return None


def _find_row_count(payload: Any) -> int | None:
    if not isinstance(payload, dict):
        return None
    for key in ("row_count", "rows", "total_rows"):
        value = payload.get(key)
        if isinstance(value, int):
            return value
    for key in ("summary", "metadata", "stats"):
        row_count = _find_row_count(payload.get(key))
        if row_count is not None:
            return row_count
    return None


def _count_csv_data_rows(source_path: Path, *, reporter: ProgressReporter) -> int:
    reporter.event(f"{source_path}: counting rows because no index row_count was found")
    total_bytes = source_path.stat().st_size
    read_bytes = 0
    row_count = 0
    last_byte = b"\n"
    with source_path.open("rb") as handle:
        header = handle.readline()
        read_bytes += len(header)
        for chunk in iter(lambda: handle.read(COPY_CHUNK_BYTES), b""):
            read_bytes += len(chunk)
            row_count += chunk.count(b"\n")
            last_byte = chunk[-1:]
            reporter.bar(
                f"{source_path.name} count",
                current=read_bytes,
                total=total_bytes,
                unit="bytes",
            )
    if total_bytes > len(header) and last_byte not in {b"\n", b"\r"}:
        row_count += 1
    reporter.bar(
        f"{source_path.name} count",
        current=total_bytes,
        total=total_bytes,
        unit="bytes",
        force=True,
    )
    return row_count


def update_historical_data_config(
    config_path: Path,
    *,
    roots: Sequence[str],
    timeframes: Sequence[str],
    output_dir: Path,
) -> None:
    """Update historical.local.yaml to point roots at generated files."""

    bars_root = Path("historical/data").resolve()
    try:
        output_relative_root = output_dir.resolve().relative_to(bars_root)
    except ValueError as exc:
        raise ValueError(
            "--update-config requires --output-dir to be inside historical/data"
        ) from exc

    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"historical data config must be a mapping: {config_path}")
    datasets = payload["historical_data"]["catalogs"]["research_futures"]["datasets"]
    for root in roots:
        root_dir = output_relative_root / root
        datasets[root]["bars"] = [
            {
                "file": str(root_dir / f"{timeframe}.csv"),
                "timeframe": timeframe,
            }
            for timeframe in timeframes
        ]
    config_path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Materialize derived GC/SI historical timeframes and sidecar indexes."
    )
    parser.add_argument("--roots", nargs="+", default=list(DEFAULT_ROOTS))
    parser.add_argument("--timeframes", nargs="+", default=list(DEFAULT_TIMEFRAMES))
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--chains-dir", type=Path, default=DEFAULT_CHAINS_DIR)
    parser.add_argument("--data-config", type=Path, default=DEFAULT_DATA_CONFIG)
    parser.add_argument(
        "--progress-every",
        type=int,
        default=100_000,
        help="Refresh row-based progress every N source rows.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Disable progress output.",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=1,
        help="Number of independent roots to materialize concurrently.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing generated CSV and index files.",
    )
    parser.add_argument(
        "--update-config",
        action="store_true",
        help="Rewrite configs/data/historical.local.yaml to use generated files.",
    )
    return parser.parse_args(argv)


def _normalize_root(value: str) -> str:
    root = value.strip().upper()
    if not root:
        raise ValueError("root must not be empty")
    return root


def _normalize_timeframe(value: str) -> str:
    return str(Timeframe.parse(value.strip().lower()))


def _validate_timeframes(timeframes: Sequence[str]) -> None:
    if not timeframes:
        raise ValueError("at least one timeframe is required")
    if len(set(timeframes)) != len(timeframes):
        raise ValueError("timeframes must be unique")
    if SOURCE_TIMEFRAME not in timeframes:
        raise ValueError("timeframes must include 1m so per-root directories are complete")


if __name__ == "__main__":
    raise SystemExit(main())
