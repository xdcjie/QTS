"""Materialized replay cache for deterministic backtest/research inputs."""

from __future__ import annotations

import dataclasses
import json
from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from qts.core.hashing import stable_json_hash
from qts.core.ids import InstrumentId
from qts.data.bars.pipeline import BarAggregationPipeline
from qts.data.bars.timeframe import Timeframe
from qts.data.historical.catalog import HistoricalCatalog
from qts.data.provenance import DatasetMetadata
from qts.data.sessions import RegularSessionWindow
from qts.data.sources.replay_market_data_source import (
    ReplayMarketDataBundle,
    ReplayMarketDataSource,
)
from qts.domain.market_data import Bar
from qts.registry.future_roll import FutureRollRegistry, FutureRollSelection


def materialized_replay_inputs(
    *,
    config: Any,
    catalog: HistoricalCatalog,
    inputs: ReplayMarketDataBundle,
    cache_dir: Path,
) -> ReplayMarketDataBundle:
    """Return replay inputs backed by cached strategy-facing bars when available."""

    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path, manifest_path, identity = _materialized_replay_cache_paths(
        config=config,
        catalog=catalog,
        cache_dir=cache_dir,
        inputs=inputs,
    )
    if cache_path.exists() and manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        _restore_roll_selections(
            inputs.future_roll_registry,
            manifest.get("roll_selections", ()),
        )
        return dataclasses.replace(inputs, bars=iter(_read_materialized_bars(cache_path)))

    bars = _materialize_strategy_bars(config=config, inputs=inputs)
    _write_materialized_bars(cache_path, bars)
    _write_materialized_manifest(
        manifest_path,
        identity=identity,
        bars=bars,
        roll_registry=inputs.future_roll_registry,
    )
    return dataclasses.replace(inputs, bars=iter(bars))


def _materialized_replay_cache_paths(
    *,
    config: Any,
    catalog: HistoricalCatalog,
    cache_dir: Path,
    inputs: ReplayMarketDataBundle,
) -> tuple[Path, Path, dict[str, Any]]:
    identity = _materialized_replay_identity(config=config, catalog=catalog, inputs=inputs)
    digest = stable_json_hash(identity).removeprefix("sha256:")
    return cache_dir / f"{digest}.jsonl", cache_dir / f"{digest}.manifest.json", identity


def _materialized_replay_identity(
    *,
    config: Any,
    catalog: HistoricalCatalog,
    inputs: ReplayMarketDataBundle,
) -> dict[str, Any]:
    return {
        "version": "materialized-replay-v1",
        "start": config.start.isoformat(),
        "end": config.end.isoformat(),
        "timeframe": config.timeframe,
        "roots": list(config.roots),
        "symbols": list(config.symbols),
        "instrument_ids": {
            symbol: instrument_id.value
            for symbol, instrument_id in sorted(config.instrument_ids.items())
        },
        "market_data": config.market_data.to_payload(),
        "roll_policy": config.roll_policy.to_payload(),
        "datasets": _catalog_dataset_identity(catalog),
        "dataset_metadata": [
            _dataset_metadata_identity(metadata)
            for metadata in sorted(
                inputs.dataset_metadata,
                key=lambda item: (item.dataset_id, item.instrument_id.value),
            )
        ],
    }


def _catalog_dataset_identity(catalog: HistoricalCatalog) -> list[dict[str, Any]]:
    datasets = catalog.datasets
    entries: list[dict[str, Any]] = []
    for root, dataset in sorted(datasets.items(), key=lambda item: str(item[0])):
        entry: dict[str, Any] = {
            "root": str(root),
            "source_timeframe": dataset.source_timeframe,
            "exchange_timezone": dataset.exchange_timezone,
            "schema_name": dataset.schema_name,
            "timezone_policy": dataset.timezone_policy,
            "normalization": dataset.normalization,
        }
        csv_path = dataset.csv_path
        if csv_path.exists():
            entry["csv_path"] = str(csv_path.resolve())
            entry["csv_hash"] = ReplayMarketDataSource._file_content_hash(csv_path)
        chain_path = dataset.chain_path
        if chain_path is not None and chain_path.exists():
            entry["chain_path"] = str(chain_path.resolve())
            entry["chain_hash"] = ReplayMarketDataSource._file_content_hash(chain_path)
        entries.append(entry)
    return entries


def _dataset_metadata_identity(metadata: DatasetMetadata) -> dict[str, Any]:
    return {
        "dataset_id": metadata.dataset_id,
        "source": metadata.source,
        "instrument_id": metadata.instrument_id.value,
        "timeframe": metadata.timeframe,
        "timezone_policy": metadata.timezone_policy,
        "adjustment_policy": metadata.adjustment_policy,
        "normalization_version": metadata.normalization_version,
        "created_at": metadata.created_at.isoformat(),
        "content_hash": metadata.content_hash,
        "row_count": metadata.row_count,
    }


def _materialize_strategy_bars(
    *,
    config: Any,
    inputs: ReplayMarketDataBundle,
) -> tuple[Bar, ...]:
    target_timeframe = Timeframe.parse(config.timeframe)
    aggregators: dict[tuple[str | object, RegularSessionWindow | None], BarAggregationPipeline] = {}
    bars: list[Bar] = []
    for source_bar in inputs.bars:
        if source_bar.timeframe == config.timeframe:
            bars.append(source_bar)
            continue
        try:
            exchange_timezone = inputs.exchange_timezone_by_instrument[source_bar.instrument_id]
        except KeyError as exc:
            raise RuntimeError(
                f"exchange timezone is required to aggregate {source_bar.instrument_id} "
                f"from {source_bar.timeframe} to {config.timeframe}"
            ) from exc
        session_window = inputs.session_window_by_instrument.get(source_bar.instrument_id)
        key = (exchange_timezone, session_window)
        aggregator = aggregators.get(key)
        if aggregator is None:
            aggregator = BarAggregationPipeline(
                exchange_timezone,
                session_window=session_window,
            )
            aggregators[key] = aggregator
        bars.extend(aggregator.aggregate(source_bar, target_timeframe))
    return tuple(bars)


def _read_materialized_bars(cache_path: Path) -> tuple[Bar, ...]:
    return tuple(
        _bar_from_payload(json.loads(line))
        for line in cache_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )


def _write_materialized_bars(cache_path: Path, bars: tuple[Bar, ...]) -> None:
    tmp_path = cache_path.with_suffix(cache_path.suffix + ".tmp")
    tmp_path.write_text(
        "".join(json.dumps(_bar_payload(bar), sort_keys=True) + "\n" for bar in bars),
        encoding="utf-8",
    )
    tmp_path.replace(cache_path)


def _write_materialized_manifest(
    manifest_path: Path,
    *,
    identity: dict[str, Any],
    bars: tuple[Bar, ...],
    roll_registry: FutureRollRegistry | None,
) -> None:
    tmp_path = manifest_path.with_suffix(manifest_path.suffix + ".tmp")
    tmp_path.write_text(
        json.dumps(
            {
                "bar_count": len(bars),
                "cache_identity": identity,
                "first_bar_end": None if not bars else bars[0].end_time.isoformat(),
                "last_bar_end": None if not bars else bars[-1].end_time.isoformat(),
                "roll_selections": _roll_selection_payloads(roll_registry, bars=bars),
                "version": "materialized-replay-v1",
            },
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    tmp_path.replace(manifest_path)


def _bar_payload(bar: Bar) -> dict[str, Any]:
    return {
        "instrument_id": bar.instrument_id.value,
        "start_time": bar.start_time.isoformat(),
        "end_time": bar.end_time.isoformat(),
        "timeframe": bar.timeframe,
        "session_id": bar.session_id,
        "open": str(bar.open),
        "high": str(bar.high),
        "low": str(bar.low),
        "close": str(bar.close),
        "volume": str(bar.volume),
        "vwap": None if bar.vwap is None else str(bar.vwap),
        "open_interest": None if bar.open_interest is None else str(bar.open_interest),
        "trade_count": bar.trade_count,
        "is_complete": bar.is_complete,
        "is_partial": bar.is_partial,
        "is_synthetic": bar.is_synthetic,
    }


def _bar_from_payload(payload: Mapping[str, Any]) -> Bar:
    return Bar(
        instrument_id=InstrumentId(str(payload["instrument_id"])),
        start_time=datetime.fromisoformat(str(payload["start_time"])),
        end_time=datetime.fromisoformat(str(payload["end_time"])),
        timeframe=str(payload["timeframe"]),
        session_id=str(payload["session_id"]),
        open=Decimal(str(payload["open"])),
        high=Decimal(str(payload["high"])),
        low=Decimal(str(payload["low"])),
        close=Decimal(str(payload["close"])),
        volume=Decimal(str(payload.get("volume", "0"))),
        vwap=None if payload.get("vwap") is None else Decimal(str(payload["vwap"])),
        open_interest=(
            None if payload.get("open_interest") is None else Decimal(str(payload["open_interest"]))
        ),
        trade_count=None if payload.get("trade_count") is None else int(payload["trade_count"]),
        is_complete=bool(payload.get("is_complete", False)),
        is_partial=bool(payload.get("is_partial", False)),
        is_synthetic=bool(payload.get("is_synthetic", False)),
    )


def _roll_selection_payloads(
    roll_registry: FutureRollRegistry | None,
    *,
    bars: tuple[Bar, ...],
) -> list[dict[str, Any]]:
    if roll_registry is None:
        return []
    cache_times = tuple(sorted({bar.end_time for bar in bars}))
    if not cache_times:
        return []
    payloads: list[dict[str, Any]] = []
    histories: dict[InstrumentId, list[FutureRollSelection]] = {}
    for selection in roll_registry.selection_history():
        histories.setdefault(selection.continuous_instrument_id, []).append(selection)
    for history in histories.values():
        history.sort(key=lambda selection: selection.as_of)
        cursor = 0
        latest: FutureRollSelection | None = None
        last_payload_key: tuple[InstrumentId, datetime] | None = None
        for cache_time in cache_times:
            while cursor < len(history) and history[cursor].as_of <= cache_time:
                latest = history[cursor]
                cursor += 1
            if latest is None:
                continue
            payload_key = (latest.continuous_instrument_id, latest.as_of)
            if payload_key == last_payload_key:
                continue
            payloads.append(_roll_selection_payload(latest))
            last_payload_key = payload_key
    return payloads


def _roll_selection_payload(selection: FutureRollSelection) -> dict[str, Any]:
    return {
        "continuous_instrument_id": selection.continuous_instrument_id.value,
        "root_symbol": selection.root_symbol,
        "as_of": selection.as_of.isoformat(),
        "concrete_instrument_id": selection.concrete_instrument_id.value,
        "source_symbol": selection.source_symbol,
        "prices_by_instrument": {
            instrument_id.value: str(price)
            for instrument_id, price in sorted(
                selection.prices_by_instrument.items(),
                key=lambda item: item[0].value,
            )
        },
    }


def _restore_roll_selections(
    roll_registry: FutureRollRegistry | None,
    payloads: object,
) -> None:
    if roll_registry is None:
        return
    if not isinstance(payloads, list):
        raise ValueError("materialized replay manifest roll_selections must be a list")
    for payload in payloads:
        if not isinstance(payload, dict):
            raise ValueError("materialized replay roll selection must be a mapping")
        roll_registry.record_selection(_roll_selection_from_payload(payload))


def _roll_selection_from_payload(payload: Mapping[str, Any]) -> FutureRollSelection:
    raw_prices = payload.get("prices_by_instrument", {})
    if not isinstance(raw_prices, Mapping):
        raise ValueError("roll selection prices_by_instrument must be a mapping")
    return FutureRollSelection(
        continuous_instrument_id=InstrumentId(str(payload["continuous_instrument_id"])),
        root_symbol=str(payload["root_symbol"]),
        as_of=datetime.fromisoformat(str(payload["as_of"])),
        concrete_instrument_id=InstrumentId(str(payload["concrete_instrument_id"])),
        source_symbol=str(payload["source_symbol"]),
        prices_by_instrument={
            InstrumentId(str(instrument_id)): Decimal(str(price))
            for instrument_id, price in raw_prices.items()
        },
    )


__all__ = ["materialized_replay_inputs"]
