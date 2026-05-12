"""Load and parse historical data configuration files."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import yaml  # type: ignore[import-untyped]

from qts.data.historical.config import (
    HistoricalBarFileConfig,
    HistoricalDataCatalogConfig,
    HistoricalDatasetConfig,
    HistoricalDataStoreConfig,
    HistoricalDataStoreDefaults,
    HistoricalMarketDataConfig,
)
from qts.data.historical.csv_format import HistoricalCsvSchema

_DATASET_STORAGE_PATH_KEYS = frozenset(
    {
        "root_dir",
        "data_dir",
        "chain_dir",
        "bars_dir",
        "chains_dir",
    }
)
_UNSUPPORTED_STORE_KEYS = frozenset(
    {
        "source_timeframe",
        "exchange_timezone",
        "timezone_policy",
        "normalization",
    }
)
_UNSUPPORTED_DATASET_KEYS = frozenset(
    {
        "bars_file",
        "source_timeframe",
        "schema",
        "exchange_timezone",
    }
)


class HistoricalMarketDataConfigLoader:
    """Load historical data configuration from files or payload dictionaries."""

    @classmethod
    def from_path(cls, path: Path) -> HistoricalMarketDataConfig:
        """Perform from_path."""
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("historical data config must be a mapping")
        return cls.from_payload(payload)

    @classmethod
    def from_payload(cls, payload: object) -> HistoricalMarketDataConfig:
        """Perform from_payload."""
        if not isinstance(payload, Mapping):
            raise ValueError("historical_data must be a mapping")
        raw_config = payload.get("historical_data")
        if not isinstance(raw_config, Mapping):
            raise ValueError("historical_data must be a mapping")
        return HistoricalMarketDataConfig(
            stores=cls._parse_stores(raw_config.get("stores")),
            catalogs=cls._parse_catalogs(raw_config.get("catalogs")),
            schemas=cls._parse_schemas(raw_config.get("schemas")),
        )

    @classmethod
    def _parse_stores(cls, payload: object) -> dict[str, HistoricalDataStoreConfig]:
        """Perform _parse_stores."""
        if not isinstance(payload, dict):
            raise ValueError("historical_data.stores must be a mapping")
        stores: dict[str, HistoricalDataStoreConfig] = {}
        for name, raw_store in payload.items():
            if not isinstance(name, str):
                raise ValueError("historical data store names must be strings")
            if not isinstance(raw_store, dict):
                raise ValueError(f"historical data store {name} must be a mapping")
            unsupported_keys = _UNSUPPORTED_STORE_KEYS.intersection(raw_store)
            if unsupported_keys:
                names = ", ".join(sorted(unsupported_keys))
                raise ValueError(f"unsupported historical store keys: {names}")
            defaults = cls._parse_store_defaults(raw_store)
            stores[name] = HistoricalDataStoreConfig(
                name=name,
                type=str(raw_store.get("type", "local_csv")),
                root_dir=Path(str(raw_store["root_dir"])),
                bars_dir=Path(str(raw_store.get("bars_dir", "data"))),
                chains_dir=Path(str(raw_store.get("chains_dir", "chains"))),
                bars_file_template=str(raw_store.get("bars_file_template", "{root_lower}.csv")),
                chain_file_template=str(raw_store.get("chain_file_template", "{root}.json")),
                defaults=defaults,
            )
        return stores

    @staticmethod
    def _parse_store_defaults(raw_store: Mapping[str, object]) -> HistoricalDataStoreDefaults:
        """Perform _parse_store_defaults."""
        raw_defaults = raw_store.get("defaults", {})
        if raw_defaults is None:
            raw_defaults = {}
        if not isinstance(raw_defaults, dict):
            raise ValueError("historical data store defaults must be a mapping")
        return HistoricalDataStoreDefaults(
            schema=(
                str(raw_defaults["schema"]) if raw_defaults.get("schema") is not None else None
            ),
            exchange_timezone=(
                str(raw_defaults["exchange_timezone"])
                if raw_defaults.get("exchange_timezone") is not None
                else None
            ),
            timezone_policy=str(
                raw_defaults.get("timezone_policy", "source_utc_exchange_sessions")
            ),
            normalization=str(raw_defaults.get("normalization", "raw")),
        )

    @classmethod
    def _parse_catalogs(cls, payload: object) -> dict[str, HistoricalDataCatalogConfig]:
        """Perform _parse_catalogs."""
        if not isinstance(payload, dict):
            raise ValueError("historical_data.catalogs must be a mapping")
        catalogs: dict[str, HistoricalDataCatalogConfig] = {}
        for name, raw_catalog in payload.items():
            if not isinstance(name, str):
                raise ValueError("historical data catalog names must be strings")
            if not isinstance(raw_catalog, dict):
                raise ValueError(f"historical data catalog {name} must be a mapping")
            raw_datasets = raw_catalog.get("datasets")
            if not isinstance(raw_datasets, dict):
                raise ValueError(f"historical data catalog {name} datasets must be a mapping")
            catalogs[name] = HistoricalDataCatalogConfig(
                name=name,
                store=str(raw_catalog["store"]),
                datasets=cls._parse_datasets(raw_datasets),
            )
        return catalogs

    @classmethod
    def _parse_datasets(
        cls, payload: Mapping[object, object]
    ) -> dict[str, HistoricalDatasetConfig]:
        """Perform _parse_datasets."""
        datasets: dict[str, HistoricalDatasetConfig] = {}
        for root, raw_dataset in payload.items():
            if not isinstance(root, str):
                raise ValueError("historical dataset roots must be strings")
            if not isinstance(raw_dataset, dict):
                raise ValueError(f"historical dataset {root} must be a mapping")
            forbidden = _DATASET_STORAGE_PATH_KEYS.intersection(raw_dataset)
            if forbidden:
                names = ", ".join(sorted(forbidden))
                raise ValueError(f"storage paths belong to stores, not dataset entries: {names}")
            unsupported_keys = _UNSUPPORTED_DATASET_KEYS.intersection(raw_dataset)
            if unsupported_keys:
                names = ", ".join(sorted(unsupported_keys))
                raise ValueError(f"unsupported historical dataset keys: {names}")
            normalized_root = HistoricalDatasetConfig.normalize_root(root)
            datasets[normalized_root] = HistoricalDatasetConfig(
                root=normalized_root,
                asset_class=str(raw_dataset["asset_class"]),
                exchange=(
                    str(raw_dataset["exchange"])
                    if raw_dataset.get("exchange") is not None
                    else None
                ),
                chain_file=(
                    str(raw_dataset["chain_file"])
                    if raw_dataset.get("chain_file") is not None
                    else None
                ),
                bars=cls._parse_bar_files(raw_dataset.get("bars")),
            )
        return datasets

    @staticmethod
    def _parse_bar_files(payload: object) -> tuple[HistoricalBarFileConfig, ...]:
        """Perform _parse_bar_files."""
        if payload is None:
            return ()
        if not isinstance(payload, list):
            raise ValueError("historical dataset bars must be a list")
        bars: list[HistoricalBarFileConfig] = []
        for raw_bar in payload:
            if not isinstance(raw_bar, dict):
                raise ValueError("historical dataset bars entries must be mappings")
            bars.append(
                HistoricalBarFileConfig(
                    file=str(raw_bar["file"]) if raw_bar.get("file") is not None else None,
                    timeframe=(
                        str(raw_bar["timeframe"]) if raw_bar.get("timeframe") is not None else None
                    ),
                    schema=str(raw_bar["schema"]) if raw_bar.get("schema") is not None else None,
                    exchange_timezone=(
                        str(raw_bar["exchange_timezone"])
                        if raw_bar.get("exchange_timezone") is not None
                        else None
                    ),
                    timezone_policy=(
                        str(raw_bar["timezone_policy"])
                        if raw_bar.get("timezone_policy") is not None
                        else None
                    ),
                    normalization=(
                        str(raw_bar["normalization"])
                        if raw_bar.get("normalization") is not None
                        else None
                    ),
                )
            )
        return tuple(bars)

    @staticmethod
    def _parse_schemas(payload: object) -> dict[str, HistoricalCsvSchema]:
        """Perform _parse_schemas."""
        if payload is None:
            return {}
        if not isinstance(payload, dict):
            raise ValueError("historical_data.schemas must be a mapping")
        schemas: dict[str, HistoricalCsvSchema] = {}
        for name, raw_schema in payload.items():
            if not isinstance(name, str):
                raise ValueError("historical CSV schema names must be strings")
            if not isinstance(raw_schema, dict):
                raise ValueError(f"historical CSV schema {name} must be a mapping")
            schemas[name] = HistoricalCsvSchema(
                timestamp=str(raw_schema["timestamp"]),
                symbol=str(raw_schema["symbol"]),
                instrument_id=(
                    str(raw_schema["instrument_id"])
                    if raw_schema.get("instrument_id") is not None
                    else None
                ),
                open=str(raw_schema["open"]),
                high=str(raw_schema["high"]),
                low=str(raw_schema["low"]),
                close=str(raw_schema["close"]),
                volume=str(raw_schema["volume"]),
            )
        return schemas


__all__ = ["HistoricalMarketDataConfigLoader"]
