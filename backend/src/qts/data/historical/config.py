"""Historical data catalog configuration."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from qts.data.capabilities import MarketDataFeedCapabilities
from qts.data.historical.csv_format import DEFAULT_HISTORICAL_CSV_SCHEMA, HistoricalCsvSchema


@dataclass(frozen=True, slots=True)
class HistoricalDataStoreDefaults:
    """Default metadata applied to datasets and bars in one historical store."""

    schema: str | None = None
    exchange_timezone: str | None = None
    timezone_policy: str = "source_utc_exchange_sessions"
    normalization: str = "raw"

    def __post_init__(self) -> None:
        """Perform __post_init__."""
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
    defaults: HistoricalDataStoreDefaults = field(default_factory=HistoricalDataStoreDefaults)

    def __post_init__(self) -> None:
        """Perform __post_init__."""
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

    def bars_path(self, root: str, *, override: str | None = None) -> Path:
        """Perform bars_path."""
        filename = override or self._render_template(self.bars_file_template, root)
        return self._join(self.bars_dir) / filename

    def chain_path(self, root: str, *, override: str | None = None) -> Path:
        """Perform chain_path."""
        filename = override or self._render_template(self.chain_file_template, root)
        return self._join(self.chains_dir) / filename

    def _join(self, path: Path) -> Path:
        """Perform _join."""
        return path if path.is_absolute() else self.root_dir / path

    @staticmethod
    def _render_template(template: str, root: str) -> str:
        """Perform _render_template."""
        normalized_root = HistoricalDatasetConfig.normalize_root(root)
        return template.format(root=normalized_root, root_lower=normalized_root.lower())


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
        """Perform __post_init__."""
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
    chain_file: str | None = None
    bars: tuple[HistoricalBarFileConfig, ...] = ()

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if not self.root.strip():
            raise ValueError("historical dataset root must not be empty")
        if not self.asset_class.strip():
            raise ValueError("historical dataset asset_class must not be empty")
        if self.exchange is not None and not self.exchange.strip():
            raise ValueError("historical dataset exchange must not be empty")
        if self.chain_file is not None and not self.chain_file.strip():
            raise ValueError("historical dataset chain_file must not be empty")
        if not self.bars:
            raise ValueError("historical dataset bars must not be empty")

    @property
    def requires_chain(self) -> bool:
        """Perform requires_chain."""
        return self.asset_class.strip().lower() == "future" or self.chain_file is not None

    @staticmethod
    def normalize_root(root: str) -> str:
        """Perform normalize_root."""
        normalized = root.strip().upper()
        if not normalized:
            raise ValueError("historical dataset root must not be empty")
        return normalized


@dataclass(frozen=True, slots=True)
class HistoricalDataCatalogConfig:
    """Logical catalog of historical datasets backed by one store."""

    name: str
    store: str
    datasets: Mapping[str, HistoricalDatasetConfig]

    def __post_init__(self) -> None:
        """Perform __post_init__."""
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
    timezone_policy: str
    normalization: str
    schema_name: str | None
    csv_schema: HistoricalCsvSchema
    bar: HistoricalBarFileConfig
    dataset: HistoricalDatasetConfig
    store: HistoricalDataStoreConfig


@dataclass(frozen=True, slots=True)
class HistoricalMarketDataConfig:
    """Project-level historical market data stores, catalogs, and metadata."""

    stores: Mapping[str, HistoricalDataStoreConfig]
    catalogs: Mapping[str, HistoricalDataCatalogConfig]
    schemas: Mapping[str, HistoricalCsvSchema] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if not self.stores:
            raise ValueError("historical_data.stores must not be empty")
        if not self.catalogs:
            raise ValueError("historical_data.catalogs must not be empty")
        for catalog in self.catalogs.values():
            if catalog.store not in self.stores:
                raise ValueError(f"unknown historical data store: {catalog.store}")

    @classmethod
    def from_yaml(cls, path: Path) -> HistoricalMarketDataConfig:
        """Perform from_yaml."""
        from qts.data.historical.config_loader import HistoricalMarketDataConfigLoader

        return HistoricalMarketDataConfigLoader.from_path(path)

    @classmethod
    def from_payload(cls, payload: object) -> HistoricalMarketDataConfig:
        """Perform from_payload."""
        from qts.data.historical.config_loader import HistoricalMarketDataConfigLoader

        if not isinstance(payload, dict):
            raise ValueError("historical_data must be a mapping")
        return HistoricalMarketDataConfigLoader.from_payload(payload)

    def catalog(self, name: str) -> HistoricalDataCatalogConfig:
        """Perform catalog."""
        try:
            return self.catalogs[name]
        except KeyError as exc:
            raise KeyError(f"unknown historical data catalog: {name}") from exc

    def store(self, name: str) -> HistoricalDataStoreConfig:
        """Perform store."""
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
        """Perform resolve_dataset."""
        normalized_root = HistoricalDatasetConfig.normalize_root(root)
        catalog = self.catalog(catalog_name)
        try:
            dataset = catalog.datasets[normalized_root]
        except KeyError as exc:
            raise KeyError(
                f"unknown historical dataset root {normalized_root} in catalog {catalog_name}"
            ) from exc
        store = self.store(catalog.store)
        bar = self._select_bar_file(
            catalog_name=catalog_name,
            root=normalized_root,
            dataset=dataset,
            store=store,
            requested_timeframe=requested_timeframe,
        )
        schema_name = bar.schema or store.defaults.schema
        return HistoricalDatasetLocation(
            root=normalized_root,
            csv_path=store.bars_path(normalized_root, override=bar.file),
            chain_path=(
                store.chain_path(normalized_root, override=dataset.chain_file)
                if dataset.requires_chain
                else None
            ),
            source_timeframe=bar.timeframe,
            exchange_timezone=bar.exchange_timezone or store.defaults.exchange_timezone,
            timezone_policy=bar.timezone_policy or store.defaults.timezone_policy,
            normalization=bar.normalization or store.defaults.normalization,
            schema_name=schema_name,
            csv_schema=self._csv_schema(schema_name),
            bar=bar,
            dataset=dataset,
            store=store,
        )

    def resolve_chain_path(self, catalog_name: str, root: str) -> Path | None:
        """Resolve chain metadata path without selecting a concrete bar file."""

        normalized_root = HistoricalDatasetConfig.normalize_root(root)
        catalog = self.catalog(catalog_name)
        try:
            dataset = catalog.datasets[normalized_root]
        except KeyError as exc:
            raise KeyError(
                f"unknown historical dataset root {normalized_root} in catalog {catalog_name}"
            ) from exc
        store = self.store(catalog.store)
        if not dataset.requires_chain:
            return None
        return store.chain_path(normalized_root, override=dataset.chain_file)

    def _csv_schema(self, name: str | None) -> HistoricalCsvSchema:
        """Perform _csv_schema."""
        if name is None:
            return DEFAULT_HISTORICAL_CSV_SCHEMA
        try:
            return self.schemas[name]
        except KeyError as exc:
            raise KeyError(f"unknown historical CSV schema: {name}") from exc

    @staticmethod
    def _select_bar_file(
        *,
        catalog_name: str,
        root: str,
        dataset: HistoricalDatasetConfig,
        store: HistoricalDataStoreConfig,
        requested_timeframe: str | None,
    ) -> HistoricalBarFileConfig:
        """Perform _select_bar_file."""
        bars = dataset.bars
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
        source_timeframe = MarketDataFeedCapabilities(
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


__all__ = [
    "HistoricalDataCatalogConfig",
    "HistoricalMarketDataConfig",
    "HistoricalDataStoreDefaults",
    "HistoricalBarFileConfig",
    "HistoricalDatasetConfig",
    "HistoricalDatasetLocation",
    "HistoricalDataStoreConfig",
]
