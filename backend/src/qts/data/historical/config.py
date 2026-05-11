"""Historical data catalog configuration."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

import yaml  # type: ignore[import-untyped]

from qts.data.historical.csv_format import DEFAULT_HISTORICAL_CSV_SCHEMA, HistoricalCsvSchema
from qts.data.live_feed import FeedCapabilities

_DATASET_STORAGE_PATH_KEYS = frozenset(
    {
        "root_dir",
        "data_dir",
        "chain_dir",
        "bars_dir",
        "chains_dir",
    }
)


@dataclass(frozen=True, slots=True)
class HistoricalDataStoreDefaults:
    """Default metadata applied to datasets and bars in one historical store."""

    schema: str | None = None
    exchange_timezone: str | None = None
    timezone_policy: str = "source_utc_exchange_sessions"
    normalization: str = "raw"

    def __post_init__(self) -> None:
        if self.schema is not None and not self.schema.strip():
            raise ValueError("historical data store default schema must not be empty")
        if self.exchange_timezone is not None and not self.exchange_timezone.strip():
            raise ValueError("historical data store default exchange_timezone must not be empty")
        if not self.timezone_policy.strip():
            raise ValueError("historical data store default timezone_policy must not be empty")
        if not self.normalization.strip():
            raise ValueError("historical data store default normalization must not be empty")


@dataclass(frozen=True, slots=True)
class HistoricalDataStoreConfig:
    """Project-level physical layout for a historical data store."""

    name: str
    type: str
    root_dir: Path
    bars_dir: Path = Path("data")
    chains_dir: Path = Path("chains")
    bars_file_template: str = "{root_lower}.csv"
    chain_file_template: str = "{root}.json"
    source_timeframe: str | None = None
    exchange_timezone: str | None = None
    timezone_policy: str = "source_utc_exchange_sessions"
    normalization: str = "raw"
    defaults: HistoricalDataStoreDefaults = field(default_factory=HistoricalDataStoreDefaults)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("historical data store name must not be empty")
        if not self.type.strip():
            raise ValueError("historical data store type must not be empty")
        if not str(self.root_dir).strip():
            raise ValueError("historical data store root_dir must not be empty")
        if not self.bars_file_template.strip():
            raise ValueError("bars_file_template must not be empty")
        if not self.chain_file_template.strip():
            raise ValueError("chain_file_template must not be empty")
        if self.source_timeframe is not None and not self.source_timeframe.strip():
            raise ValueError("source_timeframe must not be empty")
        if self.exchange_timezone is not None and not self.exchange_timezone.strip():
            raise ValueError("exchange_timezone must not be empty")
        if not self.timezone_policy.strip():
            raise ValueError("timezone_policy must not be empty")
        if not self.normalization.strip():
            raise ValueError("normalization must not be empty")

    def bars_path(self, root: str, *, override: str | None = None) -> Path:
        filename = override or _render_template(self.bars_file_template, root)
        return self._join(self.bars_dir) / filename

    def chain_path(self, root: str, *, override: str | None = None) -> Path:
        filename = override or _render_template(self.chain_file_template, root)
        return self._join(self.chains_dir) / filename

    def _join(self, path: Path) -> Path:
        return path if path.is_absolute() else self.root_dir / path


@dataclass(frozen=True, slots=True)
class HistoricalBarFileConfig:
    """One physical bar file for a dataset."""

    file: str | None = None
    timeframe: str | None = None
    schema: str | None = None
    exchange_timezone: str | None = None
    timezone_policy: str | None = None
    normalization: str | None = None

    def __post_init__(self) -> None:
        if self.file is not None and not self.file.strip():
            raise ValueError("historical bars file must not be empty")
        if self.timeframe is not None and not self.timeframe.strip():
            raise ValueError("historical bars timeframe must not be empty")
        if self.schema is not None and not self.schema.strip():
            raise ValueError("historical bars schema must not be empty")
        if self.exchange_timezone is not None and not self.exchange_timezone.strip():
            raise ValueError("historical bars exchange_timezone must not be empty")
        if self.timezone_policy is not None and not self.timezone_policy.strip():
            raise ValueError("historical bars timezone_policy must not be empty")
        if self.normalization is not None and not self.normalization.strip():
            raise ValueError("historical bars normalization must not be empty")


@dataclass(frozen=True, slots=True)
class HistoricalDatasetConfig:
    """One product/data entry inside a historical data catalog."""

    root: str
    asset_class: str
    exchange: str | None = None
    bars_file: str | None = None
    chain_file: str | None = None
    source_timeframe: str | None = None
    schema: str | None = None
    exchange_timezone: str | None = None
    bars: tuple[HistoricalBarFileConfig, ...] = ()

    def __post_init__(self) -> None:
        if not self.root.strip():
            raise ValueError("historical dataset root must not be empty")
        if not self.asset_class.strip():
            raise ValueError("historical dataset asset_class must not be empty")
        if self.exchange is not None and not self.exchange.strip():
            raise ValueError("historical dataset exchange must not be empty")
        if self.bars_file is not None and not self.bars_file.strip():
            raise ValueError("historical dataset bars_file must not be empty")
        if self.chain_file is not None and not self.chain_file.strip():
            raise ValueError("historical dataset chain_file must not be empty")
        if self.source_timeframe is not None and not self.source_timeframe.strip():
            raise ValueError("historical dataset source_timeframe must not be empty")
        if self.schema is not None and not self.schema.strip():
            raise ValueError("historical dataset schema must not be empty")
        if self.exchange_timezone is not None and not self.exchange_timezone.strip():
            raise ValueError("historical dataset exchange_timezone must not be empty")

    @property
    def requires_chain(self) -> bool:
        return self.asset_class.strip().lower() == "future" or self.chain_file is not None


@dataclass(frozen=True, slots=True)
class HistoricalDataCatalogConfig:
    """Logical catalog of historical datasets backed by one store."""

    name: str
    store: str
    datasets: Mapping[str, HistoricalDatasetConfig]

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("historical data catalog name must not be empty")
        if not self.store.strip():
            raise ValueError("historical data catalog store must not be empty")
        if not self.datasets:
            raise ValueError("historical data catalog datasets must not be empty")


@dataclass(frozen=True, slots=True)
class HistoricalDatasetLocation:
    """Resolved physical file paths for one catalog dataset."""

    root: str
    csv_path: Path
    chain_path: Path | None
    source_timeframe: str | None
    exchange_timezone: str | None
    schema_name: str | None
    csv_schema: HistoricalCsvSchema
    bar: HistoricalBarFileConfig
    dataset: HistoricalDatasetConfig
    store: HistoricalDataStoreConfig


@dataclass(frozen=True, slots=True)
class HistoricalDataConfig:
    """Project-level historical data stores and catalogs."""

    stores: Mapping[str, HistoricalDataStoreConfig]
    catalogs: Mapping[str, HistoricalDataCatalogConfig]
    schemas: Mapping[str, HistoricalCsvSchema] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.stores:
            raise ValueError("historical_data.stores must not be empty")
        if not self.catalogs:
            raise ValueError("historical_data.catalogs must not be empty")
        for catalog in self.catalogs.values():
            if catalog.store not in self.stores:
                raise ValueError(f"unknown historical data store: {catalog.store}")

    @classmethod
    def from_yaml(cls, path: Path) -> HistoricalDataConfig:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("historical data config must be a mapping")
        raw_config = payload.get("historical_data")
        if not isinstance(raw_config, dict):
            raise ValueError("historical_data must be a mapping")
        return cls(
            stores=_parse_stores(raw_config.get("stores")),
            catalogs=_parse_catalogs(raw_config.get("catalogs")),
            schemas=_parse_schemas(raw_config.get("schemas")),
        )

    def catalog(self, name: str) -> HistoricalDataCatalogConfig:
        try:
            return self.catalogs[name]
        except KeyError as exc:
            raise KeyError(f"unknown historical data catalog: {name}") from exc

    def store(self, name: str) -> HistoricalDataStoreConfig:
        try:
            return self.stores[name]
        except KeyError as exc:
            raise KeyError(f"unknown historical data store: {name}") from exc

    def resolve_dataset(
        self,
        catalog_name: str,
        root: str,
        *,
        requested_timeframe: str | None = None,
    ) -> HistoricalDatasetLocation:
        normalized_root = _normalize_root(root)
        catalog = self.catalog(catalog_name)
        try:
            dataset = catalog.datasets[normalized_root]
        except KeyError as exc:
            raise KeyError(
                f"unknown historical dataset root {normalized_root} in catalog {catalog_name}"
            ) from exc
        store = self.store(catalog.store)
        bar = _select_bar_file(
            catalog_name=catalog_name,
            root=normalized_root,
            dataset=dataset,
            store=store,
            requested_timeframe=requested_timeframe,
        )
        schema_name = bar.schema or dataset.schema or store.defaults.schema
        return HistoricalDatasetLocation(
            root=normalized_root,
            csv_path=store.bars_path(normalized_root, override=bar.file),
            chain_path=(
                store.chain_path(normalized_root, override=dataset.chain_file)
                if dataset.requires_chain
                else None
            ),
            source_timeframe=bar.timeframe,
            exchange_timezone=(
                bar.exchange_timezone
                or dataset.exchange_timezone
                or store.defaults.exchange_timezone
                or store.exchange_timezone
            ),
            schema_name=schema_name,
            csv_schema=self._csv_schema(schema_name),
            bar=bar,
            dataset=dataset,
            store=store,
        )

    def _csv_schema(self, name: str | None) -> HistoricalCsvSchema:
        if name is None:
            return DEFAULT_HISTORICAL_CSV_SCHEMA
        try:
            return self.schemas[name]
        except KeyError as exc:
            raise KeyError(f"unknown historical CSV schema: {name}") from exc


def _parse_stores(payload: object) -> dict[str, HistoricalDataStoreConfig]:
    if not isinstance(payload, dict):
        raise ValueError("historical_data.stores must be a mapping")
    stores: dict[str, HistoricalDataStoreConfig] = {}
    for name, raw_store in payload.items():
        if not isinstance(name, str):
            raise ValueError("historical data store names must be strings")
        if not isinstance(raw_store, dict):
            raise ValueError(f"historical data store {name} must be a mapping")
        defaults = _parse_store_defaults(raw_store)
        stores[name] = HistoricalDataStoreConfig(
            name=name,
            type=str(raw_store.get("type", "local_csv")),
            root_dir=Path(str(raw_store["root_dir"])),
            bars_dir=Path(str(raw_store.get("bars_dir", "data"))),
            chains_dir=Path(str(raw_store.get("chains_dir", "chains"))),
            bars_file_template=str(raw_store.get("bars_file_template", "{root_lower}.csv")),
            chain_file_template=str(raw_store.get("chain_file_template", "{root}.json")),
            source_timeframe=(
                str(raw_store["source_timeframe"])
                if raw_store.get("source_timeframe") is not None
                else None
            ),
            exchange_timezone=(
                str(raw_store["exchange_timezone"])
                if raw_store.get("exchange_timezone") is not None
                else None
            ),
            timezone_policy=str(raw_store.get("timezone_policy", "source_utc_exchange_sessions")),
            normalization=str(raw_store.get("normalization", "raw")),
            defaults=defaults,
        )
    return stores


def _parse_store_defaults(raw_store: Mapping[str, object]) -> HistoricalDataStoreDefaults:
    raw_defaults = raw_store.get("defaults", {})
    if raw_defaults is None:
        raw_defaults = {}
    if not isinstance(raw_defaults, dict):
        raise ValueError("historical data store defaults must be a mapping")
    return HistoricalDataStoreDefaults(
        schema=(str(raw_defaults["schema"]) if raw_defaults.get("schema") is not None else None),
        exchange_timezone=(
            str(raw_defaults["exchange_timezone"])
            if raw_defaults.get("exchange_timezone") is not None
            else (
                str(raw_store["exchange_timezone"])
                if raw_store.get("exchange_timezone") is not None
                else None
            )
        ),
        timezone_policy=str(
            raw_defaults.get(
                "timezone_policy",
                raw_store.get("timezone_policy", "source_utc_exchange_sessions"),
            )
        ),
        normalization=str(raw_defaults.get("normalization", raw_store.get("normalization", "raw"))),
    )


def _parse_catalogs(payload: object) -> dict[str, HistoricalDataCatalogConfig]:
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
            datasets=_parse_datasets(raw_datasets),
        )
    return catalogs


def _parse_datasets(payload: Mapping[object, object]) -> dict[str, HistoricalDatasetConfig]:
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
        normalized_root = _normalize_root(root)
        datasets[normalized_root] = HistoricalDatasetConfig(
            root=normalized_root,
            asset_class=str(raw_dataset["asset_class"]),
            exchange=(
                str(raw_dataset["exchange"]) if raw_dataset.get("exchange") is not None else None
            ),
            bars_file=(
                str(raw_dataset["bars_file"]) if raw_dataset.get("bars_file") is not None else None
            ),
            chain_file=(
                str(raw_dataset["chain_file"])
                if raw_dataset.get("chain_file") is not None
                else None
            ),
            source_timeframe=(
                str(raw_dataset["source_timeframe"])
                if raw_dataset.get("source_timeframe") is not None
                else None
            ),
            schema=(str(raw_dataset["schema"]) if raw_dataset.get("schema") is not None else None),
            exchange_timezone=(
                str(raw_dataset["exchange_timezone"])
                if raw_dataset.get("exchange_timezone") is not None
                else None
            ),
            bars=_parse_bar_files(raw_dataset.get("bars")),
        )
    return datasets


def _parse_bar_files(payload: object) -> tuple[HistoricalBarFileConfig, ...]:
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


def _parse_schemas(payload: object) -> dict[str, HistoricalCsvSchema]:
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


def _select_bar_file(
    *,
    catalog_name: str,
    root: str,
    dataset: HistoricalDatasetConfig,
    store: HistoricalDataStoreConfig,
    requested_timeframe: str | None,
) -> HistoricalBarFileConfig:
    bars = dataset.bars or (
        HistoricalBarFileConfig(
            file=dataset.bars_file,
            timeframe=dataset.source_timeframe or store.source_timeframe,
            schema=dataset.schema,
            exchange_timezone=dataset.exchange_timezone,
        ),
    )
    if requested_timeframe is None:
        if len(bars) > 1:
            raise ValueError(
                "requested_timeframe is required to choose historical bars for "
                f"{catalog_name}:{root}"
            )
        return bars[0]
    timeframes = frozenset(bar.timeframe for bar in bars if bar.timeframe is not None)
    if not timeframes:
        return bars[0]
    source_timeframe = FeedCapabilities(
        source_id=f"{catalog_name}:{root}",
        supports_ticks=False,
        supports_quotes=False,
        supports_bars=True,
        supported_timeframes=timeframes,
    ).source_timeframe_for(requested_timeframe)
    for bar in bars:
        if bar.timeframe == source_timeframe:
            return bar
    raise RuntimeError("selected historical timeframe was not present in bars")


def _normalize_root(root: str) -> str:
    normalized = root.strip().upper()
    if not normalized:
        raise ValueError("historical dataset root must not be empty")
    return normalized


def _render_template(template: str, root: str) -> str:
    normalized_root = _normalize_root(root)
    return template.format(root=normalized_root, root_lower=normalized_root.lower())


__all__ = [
    "HistoricalDataCatalogConfig",
    "HistoricalDataConfig",
    "HistoricalDataStoreDefaults",
    "HistoricalBarFileConfig",
    "HistoricalDatasetConfig",
    "HistoricalDatasetLocation",
    "HistoricalDataStoreConfig",
]
