"""Read-only research facade for configured historical bars."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from qts.core.time import TimeInterval, require_aware_datetime
from qts.data.bars.pipeline import BarAggregationPipeline
from qts.data.historical.catalog import (
    HistoricalCatalog,
    HistoricalCatalogLoadConfig,
    HistoricalDataset,
)
from qts.data.historical.csv_dataset import HistoricalBarStream, iter_historical_bars
from qts.domain.market_data import Bar


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
        source_timeframe = dataset.source_timeframe or dataset.dataset.timeframe
        stream = iter_historical_bars(
            dataset.csv_path,
            dataset.symbol_resolver,
            timeframe=source_timeframe,
            start=request.start,
            end=request.end,
            session_window=dataset.chain.session_window() if dataset.chain is not None else None,
            schema=dataset.csv_schema,
        )
        if source_timeframe == request.timeframe:
            return ResearchHistoryFrame(bars=tuple(stream))
        return ResearchHistoryFrame(
            bars=self._aggregate_stream(
                stream,
                dataset=dataset,
                source_timeframe=source_timeframe,
                target_timeframe=request.timeframe,
            )
        )

    @classmethod
    def _aggregate_stream(
        cls,
        stream: HistoricalBarStream,
        *,
        dataset: HistoricalDataset,
        source_timeframe: str,
        target_timeframe: str,
    ) -> tuple[Bar, ...]:
        exchange_timezone = cls._exchange_timezone_for(dataset)
        if exchange_timezone is None:
            raise RuntimeError("exchange timezone is required to aggregate research history")
        pipeline = BarAggregationPipeline(exchange_timezone)
        aggregated: list[Bar] = []
        for bar in stream:
            aggregated.extend(
                pipeline.aggregate_logical(
                    bar,
                    source_timeframe=source_timeframe,
                    target_timeframe=target_timeframe,
                )
            )
        return tuple(aggregated)

    @staticmethod
    def _exchange_timezone_for(dataset: HistoricalDataset) -> str | None:
        if dataset.exchange_timezone is not None:
            return dataset.exchange_timezone
        if dataset.chain is not None:
            return dataset.chain.timezone
        return None


__all__ = [
    "HistoryRequest",
    "ResearchBook",
    "ResearchBookConfig",
    "ResearchHistoryFrame",
]
