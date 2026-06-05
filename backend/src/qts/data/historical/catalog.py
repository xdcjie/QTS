"""Generic catalog for local historical datasets."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from qts.core.ids import InstrumentId
from qts.data.historical.chains import HistoricalChain
from qts.data.historical.config import (
    HistoricalDatasetConfig,
    HistoricalDatasetLocation,
    HistoricalMarketDataConfig,
)
from qts.data.historical.csv_dataset import CsvDatasetDescription, describe_csv_dataset
from qts.data.historical.csv_format import DEFAULT_HISTORICAL_CSV_SCHEMA, HistoricalCsvSchema
from qts.data.historical.symbols import HistoricalFutureChainSymbolResolver
from qts.data.historical.validation import (
    find_futures_outright_symbols,
    is_futures_outright_symbol,
)
from qts.data.sessions import RegularSessionWindow
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
    session_window: RegularSessionWindow | None = None
    timezone_policy: str = "source_utc_exchange_sessions"
    normalization: str = "raw"
    csv_schema: HistoricalCsvSchema = DEFAULT_HISTORICAL_CSV_SCHEMA
    schema_name: str | None = None


@dataclass(frozen=True, slots=True)
class HistoricalCatalog:
    """Explicit catalog for a local historical data layout."""

    root_path: Path
    roots: tuple[str, ...]
    datasets: dict[str, HistoricalDataset]

    @classmethod
    def load(cls, config: HistoricalCatalogLoadConfig) -> HistoricalCatalog:
        """Load a catalog from one cohesive construction config."""

        historical_data_config = HistoricalMarketDataConfig.from_yaml(config.data_config_path)
        symbol_resolvers = cls._symbol_resolvers_for_load_config(
            config,
            historical_data_config=historical_data_config,
        )
        return cls.from_historical_market_data_config(
            historical_data_config,
            catalog=config.catalog_name,
            roots=config.roots,
            symbol_resolvers=symbol_resolvers,
            requested_timeframe=config.requested_timeframe,
        )

    @classmethod
    def from_historical_market_data_config(
        cls,
        config: HistoricalMarketDataConfig,
        *,
        catalog: str,
        roots: tuple[str, ...],
        symbol_resolvers: Mapping[str, SourceSymbolResolver] | None = None,
        count_rows: bool = False,
        requested_timeframe: str | None = None,
    ) -> HistoricalCatalog:
        """Load requested roots from a project-level historical data catalog."""

        normalized_roots = tuple(HistoricalDatasetConfig.normalize_root(root) for root in roots)
        if not normalized_roots:
            raise ValueError("roots must not be empty")
        catalog_config = config.catalog(catalog)
        store = config.store(catalog_config.store)
        resolvers = {
            HistoricalDatasetConfig.normalize_root(root): resolver
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
            if location.dataset.requires_chain:
                if chain_path is None:
                    raise FileNotFoundError(f"required historical chain file is missing: {root}")
                cls._require_file(chain_path, store.root_dir)
                chain = HistoricalChain.load(chain_path)
                resolver = HistoricalFutureChainSymbolResolver(chain)
            elif resolver is None:
                raise FileNotFoundError(f"required historical symbol resolver is missing: {root}")
            else:
                cls._reject_undeclared_futures_outright_symbols(
                    location.csv_path,
                    location,
                    resolver,
                )
            dataset = describe_csv_dataset(
                location.csv_path,
                root=root,
                timeframe=location.source_timeframe or "1m",
                count_rows=count_rows,
                schema=location.csv_schema,
                timezone_policy=location.timezone_policy,
                normalization_policy=location.normalization,
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
                session_window=location.session_window,
                timezone_policy=location.timezone_policy,
                normalization=location.normalization,
                csv_schema=location.csv_schema,
                schema_name=location.schema_name,
            )
        return cls(root_path=store.root_dir, roots=normalized_roots, datasets=datasets)

    @classmethod
    def _symbol_resolvers_for_load_config(
        cls,
        config: HistoricalCatalogLoadConfig,
        *,
        historical_data_config: HistoricalMarketDataConfig,
    ) -> dict[str, StaticSymbolResolver]:
        """Build static symbol resolvers for non-chain roots from explicit instrument ids."""
        if not config.instrument_ids:
            return {}
        return {
            root: StaticSymbolResolver(config.instrument_ids)
            for root in config.roots
            if not cls._dataset_requires_chain(
                config,
                root,
                historical_data_config=historical_data_config,
            )
            and not cls._chain_path_exists(
                config,
                root,
                historical_data_config=historical_data_config,
            )
        }

    @staticmethod
    def _dataset_requires_chain(
        config: HistoricalCatalogLoadConfig,
        root: str,
        *,
        historical_data_config: HistoricalMarketDataConfig,
    ) -> bool:
        normalized_root = HistoricalDatasetConfig.normalize_root(root)
        return (
            historical_data_config.catalog(config.catalog_name)
            .datasets[normalized_root]
            .requires_chain
        )

    @staticmethod
    def _chain_path_exists(
        config: HistoricalCatalogLoadConfig,
        root: str,
        *,
        historical_data_config: HistoricalMarketDataConfig,
    ) -> bool:
        """Return True if a chain file is configured and present on disk for the root."""
        chain_path = historical_data_config.resolve_chain_path(config.catalog_name, root)
        return chain_path is not None and chain_path.exists()

    @staticmethod
    def _require_file(path: Path, root_path: Path) -> None:
        """Raise FileNotFoundError if a required historical file is missing."""
        if not path.exists():
            try:
                display = Path("historical") / path.relative_to(root_path)
            except ValueError:
                display = path
            raise FileNotFoundError(f"required historical file is missing: {display}")

    @staticmethod
    def _reject_undeclared_futures_outright_symbols(
        csv_path: Path,
        location: HistoricalDatasetLocation,
        resolver: SourceSymbolResolver,
    ) -> None:
        symbols = (
            tuple(
                sorted(
                    symbol.strip().upper()
                    for symbol, instrument_id in resolver.instrument_ids.items()
                    if is_futures_outright_symbol(symbol)
                    or str(instrument_id).upper().startswith("FUTURE.")
                )
            )
            if isinstance(resolver, StaticSymbolResolver)
            else find_futures_outright_symbols(csv_path, schema=location.csv_schema)
        )
        if not symbols:
            return
        examples = ", ".join(symbols)
        raise ValueError(
            "historical dataset contains futures outright symbols or futures "
            "instrument identities but asset_class is "
            f"{location.dataset.asset_class!r} and no chain metadata is configured: {examples}"
        )


@dataclass(frozen=True, slots=True)
class HistoricalCatalogLoadConfig:
    """Construction inputs for a configured historical catalog."""

    roots: tuple[str, ...]
    data_config_path: Path
    catalog_name: str
    instrument_ids: Mapping[str, InstrumentId] = field(default_factory=dict)
    requested_timeframe: str | None = None

    def __post_init__(self) -> None:
        """Normalize roots, instrument ids, paths, and validate required fields."""
        object.__setattr__(
            self,
            "roots",
            tuple(HistoricalDatasetConfig.normalize_root(root) for root in self.roots),
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
        object.__setattr__(self, "data_config_path", Path(self.data_config_path))
        catalog_name = self.catalog_name.strip()
        if not catalog_name:
            raise ValueError("catalog_name must not be empty")
        object.__setattr__(self, "catalog_name", catalog_name)

    @classmethod
    def from_historical_market_data_config(
        cls,
        config_path: Path,
        *,
        catalog: str,
        roots: tuple[str, ...],
        instrument_ids: Mapping[str, InstrumentId] | None = None,
        requested_timeframe: str | None = None,
    ) -> HistoricalCatalogLoadConfig:
        """Build a load config from a config path, catalog name, roots, and instrument ids."""
        return cls(
            roots=roots,
            instrument_ids=instrument_ids or {},
            requested_timeframe=requested_timeframe or "1m",
            data_config_path=config_path,
            catalog_name=catalog,
        )

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        """Return the symbol uppercased and trimmed, raising if empty."""
        normalized = symbol.strip().upper()
        if not normalized:
            raise ValueError("instrument_ids must not contain empty symbols")
        return normalized


__all__ = [
    "HistoricalCatalog",
    "HistoricalCatalogLoadConfig",
    "HistoricalDataset",
]
