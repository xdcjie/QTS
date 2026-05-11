"""Generic catalog for local historical datasets."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from qts.data.historical.chains import HistoricalChain, load_historical_chain
from qts.data.historical.config import HistoricalDataConfig
from qts.data.historical.csv_dataset import CsvDatasetDescription, describe_csv_dataset
from qts.data.historical.symbols import HistoricalFutureChainSymbolResolver
from qts.registry.symbol_resolution import SourceSymbolResolver


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


@dataclass(frozen=True, slots=True)
class HistoricalCatalog:
    """Explicit catalog for a local historical data layout."""

    root_path: Path
    roots: tuple[str, ...]
    datasets: dict[str, HistoricalDataset]


def load_historical_catalog(
    root_path: Path,
    *,
    roots: tuple[str, ...],
    symbol_resolvers: Mapping[str, SourceSymbolResolver] | None = None,
    count_rows: bool = False,
) -> HistoricalCatalog:
    """Load requested roots from a local historical data directory."""

    normalized_roots = tuple(_normalize_root(root) for root in roots)
    if not normalized_roots:
        raise ValueError("roots must not be empty")
    resolvers = {
        _normalize_root(root): resolver for root, resolver in (symbol_resolvers or {}).items()
    }

    datasets: dict[str, HistoricalDataset] = {}
    for root in normalized_roots:
        csv_path = root_path / "data" / f"{root.lower()}.csv"
        _require_file(csv_path, root_path)
        chain_path: Path | None = None
        chain: HistoricalChain | None = None
        resolver = resolvers.get(root)
        if resolver is None:
            chain_path = root_path / "chains" / f"{root}.json"
            _require_file(chain_path, root_path)
            chain = load_historical_chain(chain_path)
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
    return HistoricalCatalog(root_path=root_path, roots=normalized_roots, datasets=datasets)


def load_historical_catalog_from_config(
    config: HistoricalDataConfig,
    *,
    catalog: str,
    roots: tuple[str, ...],
    symbol_resolvers: Mapping[str, SourceSymbolResolver] | None = None,
    count_rows: bool = False,
) -> HistoricalCatalog:
    """Load requested roots from a project-level historical data catalog."""

    normalized_roots = tuple(_normalize_root(root) for root in roots)
    if not normalized_roots:
        raise ValueError("roots must not be empty")
    catalog_config = config.catalog(catalog)
    store = config.store(catalog_config.store)
    resolvers = {
        _normalize_root(root): resolver for root, resolver in (symbol_resolvers or {}).items()
    }

    datasets: dict[str, HistoricalDataset] = {}
    for root in normalized_roots:
        location = config.resolve_dataset(catalog, root)
        _require_file(location.csv_path, store.root_dir)
        chain_path = location.chain_path
        chain: HistoricalChain | None = None
        resolver = resolvers.get(root)
        if resolver is None:
            if chain_path is None:
                raise FileNotFoundError(f"required historical chain file is missing: {root}")
            _require_file(chain_path, store.root_dir)
            chain = load_historical_chain(chain_path)
            resolver = HistoricalFutureChainSymbolResolver(chain)
        dataset = describe_csv_dataset(location.csv_path, root=root, count_rows=count_rows)
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
        )
    return HistoricalCatalog(root_path=store.root_dir, roots=normalized_roots, datasets=datasets)


def _normalize_root(root: str) -> str:
    normalized = root.strip().upper()
    if not normalized:
        raise ValueError("roots must not contain empty values")
    return normalized


def _require_file(path: Path, root_path: Path) -> None:
    if not path.exists():
        try:
            display = Path("historical") / path.relative_to(root_path)
        except ValueError:
            display = path
        raise FileNotFoundError(f"required historical file is missing: {display}")


__all__ = [
    "HistoricalCatalog",
    "HistoricalDataset",
    "load_historical_catalog",
    "load_historical_catalog_from_config",
]
