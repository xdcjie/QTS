"""Generic catalog for local historical datasets."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from qts.core.ids import InstrumentId
from qts.data.historical.chains import HistoricalChain
from qts.data.historical.config import HistoricalDataConfig
from qts.data.historical.csv_dataset import CsvDatasetDescription, describe_csv_dataset
from qts.data.historical.csv_format import DEFAULT_HISTORICAL_CSV_SCHEMA, HistoricalCsvSchema
from qts.data.historical.symbols import HistoricalFutureChainSymbolResolver
from qts.registry.symbol_resolution import SourceSymbolResolver, StaticSymbolResolver


@dataclass(frozen=True, slots=True)
class HistoricalDataset:
    """One local historical dataset entry."""

    root: str
    chain_path: Path | None
    csv_path: Path
    chain: HistoricalChain | None
    symbol_resolver: SourceSymbolResolver
    dataset: CsvDatasetDescription
    source_timeframe: str | None = None
    exchange_timezone: str | None = None
    csv_schema: HistoricalCsvSchema = DEFAULT_HISTORICAL_CSV_SCHEMA
    schema_name: str | None = None

    @staticmethod
    def normalize_root(root: str) -> str:
        """Perform normalize_root."""
        normalized = root.strip().upper()
        if not normalized:
            raise ValueError("roots must not contain empty values")
        return normalized


@dataclass(frozen=True, slots=True)
class HistoricalCatalog:
    """Explicit catalog for a local historical data layout."""

    root_path: Path
    roots: tuple[str, ...]
    datasets: dict[str, HistoricalDataset]

    @classmethod
    def load(cls, config: HistoricalCatalogLoadConfig) -> HistoricalCatalog:
        """Load a catalog from one cohesive construction config."""

        historical_data_config: HistoricalDataConfig | None = None
        if config.data_config_path is not None:
            historical_data_config = HistoricalDataConfig.from_yaml(config.data_config_path)
        symbol_resolvers = cls._symbol_resolvers_for_load_config(
            config,
            historical_data_config=historical_data_config,
        )
        if historical_data_config is not None:
            if config.catalog_name is None:
                raise RuntimeError("historical catalog name is not configured")
            return cls.from_historical_data_config(
                historical_data_config,
                catalog=config.catalog_name,
                roots=config.roots,
                symbol_resolvers=symbol_resolvers,
                requested_timeframe=config.requested_timeframe,
            )
        if config.legacy_root_path is None:
            raise RuntimeError("legacy historical root is not configured")
        return cls.from_legacy_root(
            config.legacy_root_path,
            roots=config.roots,
            symbol_resolvers=symbol_resolvers,
        )

    @classmethod
    def from_legacy_root(
        cls,
        root_path: Path,
        *,
        roots: tuple[str, ...],
        symbol_resolvers: Mapping[str, SourceSymbolResolver] | None = None,
        count_rows: bool = False,
    ) -> HistoricalCatalog:
        """Load requested roots from a local historical data directory."""

        normalized_roots = tuple(HistoricalDataset.normalize_root(root) for root in roots)
        if not normalized_roots:
            raise ValueError("roots must not be empty")
        resolvers = {
            HistoricalDataset.normalize_root(root): resolver
            for root, resolver in (symbol_resolvers or {}).items()
        }

        datasets: dict[str, HistoricalDataset] = {}
        for root in normalized_roots:
            csv_path = root_path / "data" / f"{root.lower()}.csv"
            cls._require_file(csv_path, root_path)
            chain_path: Path | None = None
            chain: HistoricalChain | None = None
            resolver = resolvers.get(root)
            if resolver is None:
                chain_path = root_path / "chains" / f"{root}.json"
                cls._require_file(chain_path, root_path)
                chain = HistoricalChain.load(chain_path)
                resolver = HistoricalFutureChainSymbolResolver(chain)
            dataset = describe_csv_dataset(csv_path, root=root, count_rows=count_rows)
            datasets[root] = HistoricalDataset(
                root=root,
                chain_path=chain_path,
                csv_path=csv_path,
                chain=chain,
                symbol_resolver=resolver,
                dataset=dataset,
                source_timeframe=None,
                exchange_timezone=chain.timezone if chain is not None else None,
            )
        return cls(root_path=root_path, roots=normalized_roots, datasets=datasets)

    @classmethod
    def from_historical_data_config(
        cls,
        config: HistoricalDataConfig,
        *,
        catalog: str,
        roots: tuple[str, ...],
        symbol_resolvers: Mapping[str, SourceSymbolResolver] | None = None,
        count_rows: bool = False,
        requested_timeframe: str | None = None,
    ) -> HistoricalCatalog:
        """Load requested roots from a project-level historical data catalog."""

        normalized_roots = tuple(HistoricalDataset.normalize_root(root) for root in roots)
        if not normalized_roots:
            raise ValueError("roots must not be empty")
        catalog_config = config.catalog(catalog)
        store = config.store(catalog_config.store)
        resolvers = {
            HistoricalDataset.normalize_root(root): resolver
            for root, resolver in (symbol_resolvers or {}).items()
        }

        datasets: dict[str, HistoricalDataset] = {}
        for root in normalized_roots:
            location = config.resolve_dataset(
                catalog,
                root,
                requested_timeframe=requested_timeframe,
            )
            cls._require_file(location.csv_path, store.root_dir)
            chain_path = location.chain_path
            chain: HistoricalChain | None = None
            resolver = resolvers.get(root)
            if resolver is None:
                if chain_path is None:
                    raise FileNotFoundError(f"required historical chain file is missing: {root}")
                cls._require_file(chain_path, store.root_dir)
                chain = HistoricalChain.load(chain_path)
                resolver = HistoricalFutureChainSymbolResolver(chain)
            dataset = describe_csv_dataset(
                location.csv_path,
                root=root,
                timeframe=location.source_timeframe or "1m",
                count_rows=count_rows,
                schema=location.csv_schema,
            )
            datasets[root] = HistoricalDataset(
                root=root,
                chain_path=chain_path,
                csv_path=location.csv_path,
                chain=chain,
                symbol_resolver=resolver,
                dataset=dataset,
                source_timeframe=location.source_timeframe,
                exchange_timezone=location.exchange_timezone
                or (chain.timezone if chain is not None else None),
                csv_schema=location.csv_schema,
                schema_name=location.schema_name,
            )
        return cls(root_path=store.root_dir, roots=normalized_roots, datasets=datasets)

    @classmethod
    def _symbol_resolvers_for_load_config(
        cls,
        config: HistoricalCatalogLoadConfig,
        *,
        historical_data_config: HistoricalDataConfig | None,
    ) -> dict[str, StaticSymbolResolver]:
        """Perform _symbol_resolvers_for_load_config."""
        if not config.instrument_ids:
            return {}
        return {
            root: StaticSymbolResolver(config.instrument_ids)
            for root in config.roots
            if not cls._chain_path_exists(
                config,
                root,
                historical_data_config=historical_data_config,
            )
        }

    @staticmethod
    def _chain_path_exists(
        config: HistoricalCatalogLoadConfig,
        root: str,
        *,
        historical_data_config: HistoricalDataConfig | None,
    ) -> bool:
        """Perform _chain_path_exists."""
        if historical_data_config is not None:
            if config.catalog_name is None:
                raise RuntimeError("historical catalog name is not configured")
            chain_path = historical_data_config.resolve_chain_path(config.catalog_name, root)
            return chain_path is not None and chain_path.exists()
        if config.legacy_root_path is None:
            return False
        return (config.legacy_root_path / "chains" / f"{root}.json").exists()

    @staticmethod
    def _require_file(path: Path, root_path: Path) -> None:
        """Perform _require_file."""
        if not path.exists():
            try:
                display = Path("historical") / path.relative_to(root_path)
            except ValueError:
                display = path
            raise FileNotFoundError(f"required historical file is missing: {display}")


@dataclass(frozen=True, slots=True)
class HistoricalCatalogLoadConfig:
    """Construction inputs for a configured historical catalog."""

    roots: tuple[str, ...]
    instrument_ids: Mapping[str, InstrumentId] = field(default_factory=dict)
    requested_timeframe: str | None = None
    legacy_root_path: Path | None = None
    data_config_path: Path | None = None
    catalog_name: str | None = None

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        object.__setattr__(
            self,
            "roots",
            tuple(HistoricalDataset.normalize_root(root) for root in self.roots),
        )
        if not self.roots:
            raise ValueError("roots must not be empty")
        object.__setattr__(
            self,
            "instrument_ids",
            {
                self._normalize_symbol(symbol): (
                    instrument_id
                    if isinstance(instrument_id, InstrumentId)
                    else InstrumentId(str(instrument_id))
                )
                for symbol, instrument_id in self.instrument_ids.items()
            },
        )
        if self.requested_timeframe is not None:
            requested_timeframe = self.requested_timeframe.strip()
            if not requested_timeframe:
                raise ValueError("requested_timeframe must not be empty")
            object.__setattr__(self, "requested_timeframe", requested_timeframe)
        if self.legacy_root_path is not None:
            object.__setattr__(self, "legacy_root_path", Path(self.legacy_root_path))
        if self.data_config_path is not None:
            object.__setattr__(self, "data_config_path", Path(self.data_config_path))
        if self.catalog_name is not None:
            catalog_name = self.catalog_name.strip()
            if not catalog_name:
                raise ValueError("catalog_name must not be empty")
            object.__setattr__(self, "catalog_name", catalog_name)
        data_configured = self.data_config_path is not None or self.catalog_name is not None
        if data_configured and (self.data_config_path is None or self.catalog_name is None):
            raise ValueError("data_config_path and catalog_name must be provided together")
        if data_configured == (self.legacy_root_path is not None):
            raise ValueError("configure exactly one historical catalog source")

    @classmethod
    def from_legacy_root(
        cls,
        root_path: Path,
        *,
        roots: tuple[str, ...],
        instrument_ids: Mapping[str, InstrumentId] | None = None,
        requested_timeframe: str | None = None,
    ) -> HistoricalCatalogLoadConfig:
        """Perform from_legacy_root."""
        return cls(
            roots=roots,
            instrument_ids=instrument_ids or {},
            requested_timeframe=requested_timeframe,
            legacy_root_path=root_path,
        )

    @classmethod
    def from_historical_data_config(
        cls,
        config_path: Path,
        *,
        catalog: str,
        roots: tuple[str, ...],
        instrument_ids: Mapping[str, InstrumentId] | None = None,
        requested_timeframe: str | None = None,
    ) -> HistoricalCatalogLoadConfig:
        """Perform from_historical_data_config."""
        return cls(
            roots=roots,
            instrument_ids=instrument_ids or {},
            requested_timeframe=requested_timeframe,
            data_config_path=config_path,
            catalog_name=catalog,
        )

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        """Perform _normalize_symbol."""
        normalized = symbol.strip().upper()
        if not normalized:
            raise ValueError("instrument_ids must not contain empty symbols")
        return normalized


__all__ = [
    "HistoricalCatalog",
    "HistoricalDataset",
    "HistoricalCatalogLoadConfig",
]
