"""Historical data catalog configuration."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from qts.data.capabilities import MarketDataFeedCapabilities
from qts.data.historical.csv_format import DEFAULT_HISTORICAL_CSV_SCHEMA, HistoricalCsvSchema
from qts.data.sessions import RegularSessionWindow


@dataclass(frozen=True, slots=True)
class HistoricalDataStoreDefaults:
    """Default metadata applied to datasets and bars in one historical store."""

    schema: str | None = None
    exchange_timezone: str | None = None
    timezone_policy: str = "source_utc_exchange_sessions"
    normalization: str = "raw"

    def __post_init__(self) -> None:
        """Validate that all non-None default metadata fields are non-empty."""
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
        """Validate that store name, type, root_dir, and file templates are non-empty."""
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
        """Return the absolute path to the bar file for a root, honoring any override."""
        filename = override or self._render_template(self.bars_file_template, root)
        return self._join(self.bars_dir) / filename

    def chain_path(self, root: str, *, override: str | None = None) -> Path:
        """Return the absolute path to the chain file for a root, honoring any override."""
        filename = override or self._render_template(self.chain_file_template, root)
        return self._join(self.chains_dir) / filename

    def _join(self, path: Path) -> Path:
        """Return the path as-is if absolute, else resolve it relative to root_dir."""
        return path if path.is_absolute() else self.root_dir / path

    @staticmethod
    def _render_template(template: str, root: str) -> str:
        """Render a filename template with the normalized root and its lowercase form."""
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
    session_window: RegularSessionWindow | None = None

    def __post_init__(self) -> None:
        """Validate that all provided bar-file metadata fields are non-empty."""
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
        """Validate dataset root, asset_class, optional fields, and a non-empty bars list."""
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
        """Return True when the dataset is a future or declares an explicit chain file."""
        return self.asset_class.strip().lower() == "future" or self.chain_file is not None

    @staticmethod
    def normalize_root(root: str) -> str:
        """Return the root trimmed and uppercased, raising if it is empty."""
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
        """Validate that catalog name, store, and datasets mapping are non-empty."""
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
    session_window: RegularSessionWindow | None
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
        """Validate non-empty stores/catalogs and that each catalog references a known store."""
        if not self.stores:
            raise ValueError("historical_data.stores must not be empty")
        if not self.catalogs:
            raise ValueError("historical_data.catalogs must not be empty")
        for catalog in self.catalogs.values():
            if catalog.store not in self.stores:
                raise ValueError(f"unknown historical data store: {catalog.store}")

    @classmethod
    def from_yaml(cls, path: Path) -> HistoricalMarketDataConfig:
        """Build a HistoricalMarketDataConfig by loading and parsing a YAML file."""
        from qts.data.historical.config_loader import HistoricalMarketDataConfigLoader

        return HistoricalMarketDataConfigLoader.from_path(path)

    @classmethod
    def from_payload(cls, payload: object) -> HistoricalMarketDataConfig:
        """Build a HistoricalMarketDataConfig from an already-parsed mapping payload."""
        from qts.data.historical.config_loader import HistoricalMarketDataConfigLoader

        if not isinstance(payload, dict):
            raise ValueError("historical_data must be a mapping")
        return HistoricalMarketDataConfigLoader.from_payload(payload)

    def catalog(self, name: str) -> HistoricalDataCatalogConfig:
        """Return the named catalog config, raising KeyError if it is unknown."""
        try:
            return self.catalogs[name]
        except KeyError as exc:
            raise KeyError(f"unknown historical data catalog: {name}") from exc

    def store(self, name: str) -> HistoricalDataStoreConfig:
        """Return the named store config, raising KeyError if it is unknown."""
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
        """Resolve a catalog root to file paths and metadata for the requested timeframe."""
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
            session_window=bar.session_window,
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
        """Return the named CSV schema, or the default when name is None."""
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
        """Select the dataset bar file matching the requested timeframe, or the sole entry."""
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
    "HistoricalBarFileConfig",
    "HistoricalDataCatalogConfig",
    "HistoricalDataStoreConfig",
    "HistoricalDataStoreDefaults",
    "HistoricalDatasetConfig",
    "HistoricalDatasetLocation",
    "HistoricalMarketDataConfig",
]
