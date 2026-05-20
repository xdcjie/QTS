"""Notebook-friendly research session facade over existing QTS boundaries."""

from __future__ import annotations

import importlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from qts.backtest.engine import BacktestStreamResult
from qts.backtest.pipeline import BacktestPipeline
from qts.core.ids import InstrumentId
from qts.research.experiment_store import ExperimentStore, ExperimentStoreRecord
from qts.research.factor_discovery import (
    DEFAULT_FACTOR_DISCOVERY_SOURCES,
    FactorDiscovery,
    FactorDiscoveryResult,
    FactorIdea,
    FactorIdeaStore,
)
from qts.research.factor_spec import FactorSpec, FactorSpecDrafter
from qts.research.optimizer.parameter_space import ParameterGrid, ParameterSpace
from qts.research.optimizer.pipeline import BacktestPipelineJob, BacktestPipelineRunner
from qts.research.optimizer.result import OptimizationResult
from qts.research.research_book import (
    HistoryRequest,
    ResearchBook,
    ResearchBookConfig,
    ResearchHistoryFrame,
)


@dataclass(frozen=True, slots=True)
class ResearchSessionConfig:
    """Owns configuration for a notebook-friendly research session."""

    research_config_path: Path
    data_config_path: Path
    catalog_name: str
    roots: tuple[str, ...]
    timeframe: str
    instrument_ids: Mapping[str, InstrumentId]
    backtest_config_path: Path
    store_root: Path
    output_root: Path
    objective_metric: str = "sharpe_ratio"
    discovery_sources: tuple[str, ...] = DEFAULT_FACTOR_DISCOVERY_SOURCES
    discovery_max_results: int = 10

    @classmethod
    def from_yaml(cls, path: str | Path) -> ResearchSessionConfig:
        """Load and validate a research session YAML config."""

        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"research config not found: {path}")
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("research config must be a YAML mapping")
        data = cls._required_mapping(raw, "data")
        discovery = cls._optional_mapping(raw, "discovery")
        roots = cls._string_tuple(data.get("roots"), "data.roots")
        data_config_path = cls._resolve_path(path, cls._required_text(data, "config"))
        backtest_config_path = cls._resolve_path(path, cls._required_text(raw, "backtest_config"))
        if not backtest_config_path.exists():
            raise FileNotFoundError(f"backtest config not found: {backtest_config_path}")
        return cls(
            research_config_path=path,
            data_config_path=data_config_path,
            catalog_name=cls._required_text(data, "catalog"),
            roots=roots,
            timeframe=cls._required_text(data, "timeframe"),
            instrument_ids=cls._instrument_ids(data.get("instrument_ids", {})),
            backtest_config_path=backtest_config_path,
            store_root=cls._resolve_output_path(path, str(raw.get("store", "runs/research"))),
            output_root=cls._resolve_output_path(
                path,
                str(raw.get("output_root", "runs/research/backtests")),
            ),
            objective_metric=str(raw.get("objective_metric", "sharpe_ratio")),
            discovery_sources=cls._source_tuple(
                discovery.get("sources", list(DEFAULT_FACTOR_DISCOVERY_SOURCES)),
                "discovery.sources",
            ),
            discovery_max_results=cls._positive_int(
                discovery.get("max_results", 10),
                "discovery.max_results",
            ),
        )

    def research_book_config(self) -> ResearchBookConfig:
        """Return the read-only history facade config."""

        return ResearchBookConfig(
            data_config_path=self.data_config_path,
            catalog_name=self.catalog_name,
            roots=self.roots,
            timeframe=self.timeframe,
            instrument_ids=dict(self.instrument_ids),
        )

    @staticmethod
    def _required_mapping(payload: Mapping[str, Any], field_name: str) -> dict[str, Any]:
        value = payload.get(field_name)
        if not isinstance(value, dict):
            raise ValueError(f"{field_name} must be a mapping")
        return value

    @staticmethod
    def _optional_mapping(payload: Mapping[str, Any], field_name: str) -> dict[str, Any]:
        value = payload.get(field_name, {})
        if not isinstance(value, dict):
            raise ValueError(f"{field_name} must be a mapping")
        return value

    @staticmethod
    def _required_text(payload: Mapping[str, Any], field_name: str) -> str:
        value = payload.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} is required")
        return value

    @staticmethod
    def _string_tuple(value: Any, field_name: str) -> tuple[str, ...]:
        if not isinstance(value, list) or not value:
            raise ValueError(f"{field_name} must not be empty")
        if not all(isinstance(item, str) and item.strip() for item in value):
            raise ValueError(f"{field_name} must contain non-empty strings")
        return tuple(item.strip() for item in value)

    @staticmethod
    def _source_tuple(value: Any, field_name: str) -> tuple[str, ...]:
        return tuple(
            item.lower() for item in ResearchSessionConfig._string_tuple(value, field_name)
        )

    @staticmethod
    def _positive_int(value: Any, field_name: str) -> int:
        parsed = int(value)
        if parsed <= 0:
            raise ValueError(f"{field_name} must be positive")
        return parsed

    @staticmethod
    def _instrument_ids(value: Any) -> dict[str, InstrumentId]:
        if not isinstance(value, dict):
            raise ValueError("data.instrument_ids must be a mapping")
        result: dict[str, InstrumentId] = {}
        for symbol, instrument_id in value.items():
            if not isinstance(symbol, str) or not symbol.strip():
                raise ValueError("data.instrument_ids must contain non-empty symbols")
            result[symbol.strip().upper()] = InstrumentId(str(instrument_id))
        return result

    @staticmethod
    def _resolve_path(config_path: Path, value: str) -> Path:
        raw_path = Path(value)
        if raw_path.is_absolute():
            return raw_path
        sibling = config_path.parent / raw_path
        if sibling.exists():
            return sibling
        return raw_path

    @staticmethod
    def _resolve_output_path(config_path: Path, value: str) -> Path:
        raw_path = Path(value)
        if raw_path.is_absolute():
            return raw_path
        return config_path.parent / raw_path


class ResearchSession:
    """Orchestrates user-friendly research actions through QTS boundaries."""

    def __init__(
        self,
        config: ResearchSessionConfig,
        *,
        book: ResearchBook | None = None,
        store: ExperimentStore | None = None,
        discovery: FactorDiscovery | None = None,
    ) -> None:
        self._config = config
        self._book = book
        self._store = store if store is not None else ExperimentStore(config.store_root)
        self._discovery = discovery

    @classmethod
    def from_yaml(cls, path: str | Path) -> ResearchSession:
        """Load a research session from YAML."""

        return cls(ResearchSessionConfig.from_yaml(path))

    @property
    def config(self) -> ResearchSessionConfig:
        """Return the validated research session config."""

        return self._config

    @property
    def book(self) -> ResearchBook:
        """Return the read-only research history facade."""

        if self._book is None:
            self._book = ResearchBook.from_config(self._config.research_book_config())
        return self._book

    @property
    def store(self) -> ExperimentStore:
        """Return the experiment store facade."""

        return self._store

    @property
    def discovery(self) -> FactorDiscovery:
        """Return the factor idea discovery facade."""

        if self._discovery is None:
            self._discovery = FactorDiscovery.with_default_sources(
                FactorIdeaStore(self._config.store_root)
            )
        return self._discovery

    def history(self, request: HistoryRequest) -> ResearchHistoryFrame:
        """Return historical bars through ``ResearchBook``."""

        return self.book.history(request)

    def history_frame(self, request: HistoryRequest) -> Any:
        """Return historical bars as a pandas DataFrame."""

        return self.book.history_frame(request)

    def parameter_grid(self, parameters: Mapping[str, Sequence[Any]]) -> ParameterGrid:
        """Return a stable optimizer parameter grid from notebook inputs."""

        spaces: list[ParameterSpace] = []
        for name, values in parameters.items():
            value_tuple = tuple(values)
            if not value_tuple:
                raise ValueError("parameter values must not be empty")
            spaces.append(ParameterSpace(name=str(name), values=value_tuple))
        return ParameterGrid(*spaces)

    def run_backtest(
        self,
        *,
        strategy_params: Mapping[str, Any] | None = None,
        output_dir: Path | None = None,
    ) -> BacktestStreamResult:
        """Run one backtest through the shared ``BacktestPipeline``."""

        pipeline = BacktestPipeline.from_yaml(self._config.backtest_config_path)
        if strategy_params:
            pipeline = pipeline.with_strategy_params(strategy_params)
        engine, _bundle = pipeline.build_engine()
        return engine.run_streaming(
            output_dir or self._config.output_root / "single-run",
            compact_events=True,
        )

    def optimize(
        self,
        *,
        parameters: Mapping[str, Sequence[Any]],
        objective_metric: str | None = None,
        output_root: Path | None = None,
    ) -> tuple[OptimizationResult, ...]:
        """Run a parameter sweep through ``BacktestPipelineRunner``."""

        return BacktestPipelineRunner().run(
            BacktestPipelineJob(
                base_config_path=self._config.backtest_config_path,
                parameter_grid=self.parameter_grid(parameters),
                output_root=output_root or self._config.output_root / "optimizer",
                objective_metric=objective_metric or self._config.objective_metric,
            )
        )

    def record_manifest(
        self,
        manifest_path: Path,
        *,
        recorded_at: datetime | None = None,
    ) -> ExperimentStoreRecord:
        """Record a completed experiment manifest in the session store."""

        return self._store.record_manifest(manifest_path, recorded_at=recorded_at)

    def list_runs(self, *, limit: int | None = None) -> tuple[ExperimentStoreRecord, ...]:
        """Return indexed experiment records, newest first."""

        return self._store.list_runs(limit=limit)

    def compare_runs(self, metric: str) -> tuple[ExperimentStoreRecord, ...]:
        """Return records sorted descending by a Decimal-parseable metric."""

        scored: list[tuple[Decimal, ExperimentStoreRecord]] = []
        for record in self._store.list_runs():
            raw_metric = record.metrics.get(metric)
            if raw_metric is None:
                continue
            try:
                scored.append((Decimal(str(raw_metric)), record))
            except (InvalidOperation, ValueError):
                continue
        return tuple(
            record for _score, record in sorted(scored, key=lambda item: item[0], reverse=True)
        )

    def compare_frame(self, metric: str) -> Any:
        """Return a pandas DataFrame comparing stored experiment runs."""

        pandas_module: Any = importlib.import_module("pandas")
        return pandas_module.DataFrame(
            [
                {
                    "experiment_id": record.experiment_id,
                    "manifest_path": str(record.manifest_path),
                    "metric": metric,
                    "metric_value": Decimal(str(record.metrics[metric])),
                    "recorded_at": record.recorded_at,
                    "strategy_name": record.strategy_name,
                    "strategy_version": record.strategy_version,
                }
                for record in self.compare_runs(metric)
            ]
        )

    def discover_factors(
        self,
        query: str,
        *,
        sources: Sequence[str] | None = None,
        max_results: int | None = None,
        from_year: int | None = None,
        to_year: int | None = None,
        refresh: bool = False,
    ) -> FactorDiscoveryResult:
        """Discover source-backed factor ideas without creating executable behavior."""

        return self.discovery.search(
            query,
            sources=self._config.discovery_sources if sources is None else sources,
            max_results=(
                self._config.discovery_max_results if max_results is None else max_results
            ),
            from_year=from_year,
            to_year=to_year,
            refresh=refresh,
        )

    def discover_factors_frame(
        self,
        query: str,
        *,
        sources: Sequence[str] | None = None,
        max_results: int | None = None,
        from_year: int | None = None,
        to_year: int | None = None,
        refresh: bool = False,
    ) -> Any:
        """Return discovered factor ideas as a pandas DataFrame."""

        return self.discover_factors(
            query,
            sources=sources,
            max_results=max_results,
            from_year=from_year,
            to_year=to_year,
            refresh=refresh,
        ).to_pandas()

    def draft_factor_spec(self, idea: FactorIdea) -> FactorSpec:
        """Draft a non-executable factor hypothesis from one discovered idea."""

        return FactorSpecDrafter().draft(idea)

    def draft_factor_specs(
        self,
        ideas: FactorDiscoveryResult | Sequence[FactorIdea],
    ) -> tuple[FactorSpec, ...]:
        """Draft non-executable factor hypotheses from discovered ideas."""

        source_ideas = ideas.ideas if isinstance(ideas, FactorDiscoveryResult) else ideas
        drafter = FactorSpecDrafter()
        return tuple(drafter.draft(idea) for idea in source_ideas)


__all__ = ["ResearchSession", "ResearchSessionConfig"]
