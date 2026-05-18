"""Read-only research facade for configured historical bars."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from qts.core.time import TimeInterval, require_aware_datetime
from qts.data.historical.catalog import HistoricalCatalog, HistoricalCatalogLoadConfig
from qts.data.historical.csv_dataset import iter_historical_bars
from qts.domain.market_data import Bar

if TYPE_CHECKING:
    from qts.runtime.config import BacktestRuntimeConfig


@dataclass(frozen=True, slots=True)
class ResearchBookConfig:
    """Construction inputs for a configured research history facade."""

    data_config_path: Path
    catalog_name: str
    roots: tuple[str, ...]
    timeframe: str

    def __post_init__(self) -> None:
        """Validate and normalize config inputs."""

        if not self.catalog_name.strip():
            raise ValueError("catalog_name is required")
        if not self.roots:
            raise ValueError("roots must not be empty")
        if not self.timeframe.strip():
            raise ValueError("timeframe is required")
        object.__setattr__(self, "data_config_path", Path(self.data_config_path))


@dataclass(frozen=True, slots=True)
class HistoryRequest:
    """One bounded historical bar request using `[start, end)` semantics."""

    root: str
    start: datetime
    end: datetime
    timeframe: str

    def __post_init__(self) -> None:
        """Validate request identity and interval bounds."""

        TimeInterval(start=self.start, end=self.end)
        if not self.root.strip():
            raise ValueError("root is required")
        if not self.timeframe.strip():
            raise ValueError("timeframe is required")

    def includes(self, timestamp: datetime) -> bool:
        """Return whether ``timestamp`` belongs to this half-open request."""

        require_aware_datetime(timestamp, name="timestamp")
        return self.start <= timestamp < self.end


@dataclass(frozen=True, slots=True)
class ResearchHistoryFrame:
    """Deterministic row-like collection of historical bars."""

    bars: tuple[Bar, ...]

    def __iter__(self) -> Iterator[Bar]:
        """Iterate over frame bars in source order."""

        return iter(self.bars)

    def __len__(self) -> int:
        """Return the number of bars in the frame."""

        return len(self.bars)


class ResearchBook:
    """Read-only research facade over configured historical data."""

    def __init__(self, config: ResearchBookConfig, catalog: HistoricalCatalog) -> None:
        self._config = config
        self._catalog = catalog

    @classmethod
    def from_config(cls, config: ResearchBookConfig) -> ResearchBook:
        """Load a configured historical catalog for research queries."""

        catalog = HistoricalCatalog.load(
            HistoricalCatalogLoadConfig.from_historical_market_data_config(
                config.data_config_path,
                catalog=config.catalog_name,
                roots=config.roots,
                requested_timeframe=config.timeframe,
            )
        )
        return cls(config=config, catalog=catalog)

    @classmethod
    def from_backtest_config(cls, config: BacktestRuntimeConfig) -> ResearchBook:
        """Build from a backtest config's read-only market data reference."""

        market_data = config.market_data
        if market_data.config_path is None or market_data.catalog is None:
            raise RuntimeError("market data reference is partially configured")
        return cls.from_config(
            ResearchBookConfig(
                data_config_path=market_data.config_path,
                catalog_name=market_data.catalog,
                roots=config.roots,
                timeframe=config.timeframe,
            )
        )

    @property
    def dataset_ids(self) -> tuple[str, ...]:
        """Return deterministic dataset identifiers for experiment manifests."""

        return tuple(
            f"{dataset.root}:{dataset.dataset.timeframe}:{dataset.dataset.path}"
            for dataset in self._catalog.datasets.values()
        )

    def history(self, request: HistoryRequest) -> ResearchHistoryFrame:
        """Return bars from the configured catalog within ``request`` bounds."""

        root = request.root.strip().upper()
        dataset = self._catalog.datasets[root]
        stream = iter_historical_bars(
            dataset.csv_path,
            dataset.symbol_resolver,
            timeframe=request.timeframe,
            start=request.start,
            end=request.end,
            session_window=dataset.chain.session_window() if dataset.chain is not None else None,
            schema=dataset.csv_schema,
        )
        return ResearchHistoryFrame(bars=tuple(stream))


__all__ = [
    "HistoryRequest",
    "ResearchBook",
    "ResearchBookConfig",
    "ResearchHistoryFrame",
]
