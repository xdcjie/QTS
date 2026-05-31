"""Notebook-friendly research session facade over existing QTS boundaries."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from qts.backtest.engine import BacktestStreamResult
from qts.backtest.pipeline import BacktestPipeline
from qts.core.ids import InstrumentId
from qts.research.experiment_recorder import (
    ResearchExperimentRecorder,
    ResearchExperimentRecorderConfig,
)
from qts.research.experiment_run_service import ExperimentRunService
from qts.research.experiment_store import ExperimentStore, ExperimentStoreRecord
from qts.research.factor_candidate import FactorCandidateBatch
from qts.research.factor_discovery import (
    DEFAULT_FACTOR_DISCOVERY_SOURCES,
    FactorDiscovery,
    FactorDiscoveryResult,
    FactorIdea,
    FactorIdeaStore,
)
from qts.research.factor_evaluation_service import EvaluatedFactorSnapshot, FactorEvaluationService
from qts.research.factor_spec import FactorSpec
from qts.research.factor_spec_store import FactorSpecReview, FactorSpecStore
from qts.research.factor_workbench_service import FactorWorkbenchService
from qts.research.optimizer.constraints import OptimizationConstraint
from qts.research.optimizer.failure_veto import (
    FailureWindow,
    FailureWindowVetoJob,
    FailureWindowVetoRunner,
    FailureWindowVetoSummary,
)
from qts.research.optimizer.parameter_space import ParameterGrid, ParameterSpace
from qts.research.optimizer.pipeline import BacktestPipelineJob, BacktestPipelineRunner
from qts.research.optimizer.result import OptimizationResult
from qts.research.optimizer.walk_forward import (
    BacktestWalkForwardValidationJob,
    BacktestWalkForwardValidationRunner,
    WalkForwardPlan,
    WalkForwardValidationSummary,
)
from qts.research.research_book import (
    HistoryRequest,
    ResearchBook,
    ResearchBookConfig,
    ResearchHistoryFrame,
)
from qts.research.tearsheet import (
    FactorEvaluationTearsheet,
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
        factor_specs: FactorSpecStore | None = None,
    ) -> None:
        self._config = config
        self._book = book
        self._store = store if store is not None else ExperimentStore(config.store_root)
        self._discovery = discovery
        self._factor_specs = factor_specs
        self._factor_evaluation = FactorEvaluationService(
            output_root=config.output_root, store=self._store
        )
        self._factor_workbench = FactorWorkbenchService(
            discovery_factory=lambda: self.discovery,
            spec_store_factory=lambda: self.factor_specs,
            discovery_sources=config.discovery_sources,
            discovery_max_results=config.discovery_max_results,
        )
        self._experiment_runs = ExperimentRunService(store=self._store)

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

    @property
    def factor_specs(self) -> FactorSpecStore:
        """Return the factor spec persistence facade."""

        if self._factor_specs is None:
            self._factor_specs = FactorSpecStore(self._config.store_root)
        return self._factor_specs

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
        backtest_config_path: str | Path | None = None,
        end: datetime | None = None,
        materialized_replay_cache_dir: Path | None = None,
        start: datetime | None = None,
        strategy_params: Mapping[str, Any] | None = None,
        output_dir: Path | None = None,
    ) -> BacktestStreamResult:
        """Run one backtest through the shared ``BacktestPipeline``."""

        if (start is None) != (end is None):
            raise ValueError("start and end must be provided together")
        pipeline = BacktestPipeline.from_yaml(
            Path(backtest_config_path)
            if backtest_config_path is not None
            else self._config.backtest_config_path
        )
        if materialized_replay_cache_dir is not None:
            pipeline = pipeline.with_materialized_replay_cache(materialized_replay_cache_dir)
        if start is not None and end is not None:
            pipeline = pipeline.with_date_range(start=start, end=end)
        if strategy_params:
            pipeline = pipeline.with_strategy_params(strategy_params)
        engine, _bundle = pipeline.build_engine()
        return engine.run_streaming(
            output_dir or self._config.output_root / "single-run",
            compact_events=True,
        )

    def run_backtest_matrix(
        self,
        *,
        base_strategy_params: Mapping[str, Any],
        candidates: Sequence[Mapping[str, Any]],
        metrics: Sequence[str],
        output_root: Path,
        periods: Sequence[Mapping[str, Any]],
        backtest_config_path: str | Path | None = None,
        materialized_replay_cache_dir: Path | None = None,
    ) -> tuple[dict[str, Any], ...]:
        """Run a candidate/period backtest matrix through one cached pipeline."""

        base_pipeline = BacktestPipeline.from_yaml(
            Path(backtest_config_path)
            if backtest_config_path is not None
            else self._config.backtest_config_path
        )
        if materialized_replay_cache_dir is not None:
            base_pipeline = base_pipeline.with_materialized_replay_cache(
                materialized_replay_cache_dir
            )
        base_pipeline.catalog()
        rows: list[dict[str, Any]] = []
        for period in periods:
            period_name = str(period["name"])
            start = period["start"]
            end = period["end"]
            if not isinstance(start, datetime) or not isinstance(end, datetime):
                raise TypeError("backtest matrix periods must contain datetime start/end")
            period_pipeline = base_pipeline.with_date_range(start=start, end=end)
            for candidate in candidates:
                candidate_name = str(candidate["name"])
                candidate_params = candidate.get("strategy_params", {})
                if not isinstance(candidate_params, Mapping):
                    raise TypeError("backtest matrix candidate strategy_params must be a mapping")
                strategy_params = {**dict(base_strategy_params), **dict(candidate_params)}
                run_pipeline = period_pipeline.with_strategy_params(strategy_params)
                engine, _bundle = run_pipeline.build_engine()
                result = engine.run_streaming(
                    output_root / period_name / candidate_name,
                    compact_events=True,
                )
                manifest_path = Path(result.manifest_path)
                manifest_metrics = self._manifest_metrics(manifest_path)
                row = {
                    "candidate": candidate_name,
                    "manifest_path": str(manifest_path),
                    "period": period_name,
                    "processed_bars": result.processed_bars,
                    "strategy_params": strategy_params,
                    "trading_bars": result.trading_bars,
                }
                row.update({metric: manifest_metrics.get(metric) for metric in metrics})
                rows.append(row)
        return tuple(rows)

    @staticmethod
    def _manifest_metrics(manifest_path: Path) -> dict[str, str]:
        if not manifest_path.exists():
            return {}
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        metrics = payload.get("metrics", {})
        if not isinstance(metrics, Mapping):
            return {}
        return {str(key): str(value) for key, value in metrics.items()}

    def optimize(
        self,
        *,
        parameters: Mapping[str, Sequence[Any]],
        objective_metric: str | None = None,
        output_root: Path | None = None,
        materialized_replay_cache_dir: Path | None = None,
    ) -> tuple[OptimizationResult, ...]:
        """Run a parameter sweep through ``BacktestPipelineRunner``."""

        return BacktestPipelineRunner().run(
            BacktestPipelineJob(
                base_config_path=self._config.backtest_config_path,
                parameter_grid=self.parameter_grid(parameters),
                output_root=output_root or self._config.output_root / "optimizer",
                objective_metric=objective_metric or self._config.objective_metric,
                materialized_replay_cache_dir=materialized_replay_cache_dir,
            )
        )

    def validate_optimizer_walk_forward(
        self,
        *,
        candidate_parameters: Sequence[Mapping[str, Any]],
        plan: WalkForwardPlan,
        constraints: Iterable[OptimizationConstraint] = (),
        capital_metric_config: Mapping[str, Any] | None = None,
        objective_metric: str | None = None,
        output_root: Path | None = None,
        materialized_replay_cache_dir: Path | None = None,
    ) -> WalkForwardValidationSummary:
        """Rerun selected optimizer candidates across walk-forward windows."""
        results = BacktestWalkForwardValidationRunner().run(
            BacktestWalkForwardValidationJob(
                base_config_path=self._config.backtest_config_path,
                candidate_parameters=tuple(dict(parameters) for parameters in candidate_parameters),
                objective_metric=objective_metric or self._config.objective_metric,
                output_root=output_root or self._config.output_root / "walk-forward",
                plan=plan,
                materialized_replay_cache_dir=materialized_replay_cache_dir,
            )
        )
        return WalkForwardValidationSummary.from_results(
            results,
            constraints=constraints,
            capital_metric_config=(
                None if capital_metric_config is None else dict(capital_metric_config)
            ),
        )

    def validate_optimizer_failure_window_veto(
        self,
        *,
        candidate_parameters: Sequence[Mapping[str, Any]],
        windows: Sequence[FailureWindow],
        report_only_windows: Sequence[FailureWindow] = (),
        constraints: Iterable[OptimizationConstraint] = (),
        capital_metric_config: Mapping[str, Any] | None = None,
        objective_metric: str | None = None,
        output_root: Path | None = None,
        materialized_replay_cache_dir: Path | None = None,
    ) -> FailureWindowVetoSummary:
        """Rerun selected optimizer candidates across failure-veto windows."""
        results = FailureWindowVetoRunner().run(
            FailureWindowVetoJob(
                base_config_path=self._config.backtest_config_path,
                candidate_parameters=tuple(dict(parameters) for parameters in candidate_parameters),
                objective_metric=objective_metric or self._config.objective_metric,
                output_root=output_root or self._config.output_root / "failure-veto",
                windows=tuple(windows),
                report_only_windows=tuple(report_only_windows),
                materialized_replay_cache_dir=materialized_replay_cache_dir,
            )
        )
        return FailureWindowVetoSummary.from_results(
            results,
            constraints=constraints,
            capital_metric_config=(
                None if capital_metric_config is None else dict(capital_metric_config)
            ),
        )

    def record_manifest(
        self,
        manifest_path: Path,
        *,
        recorded_at: datetime | None = None,
    ) -> ExperimentStoreRecord:
        """Record a completed experiment manifest in the session store."""

        return self._experiment_runs.record_manifest(manifest_path, recorded_at=recorded_at)

    def list_runs(self, *, limit: int | None = None) -> tuple[ExperimentStoreRecord, ...]:
        """Return indexed experiment records, newest first."""

        return self._experiment_runs.list_runs(limit=limit)

    def compare_runs(self, metric: str) -> tuple[ExperimentStoreRecord, ...]:
        """Return records sorted descending by a Decimal-parseable metric."""

        return self._experiment_runs.compare_runs(metric)

    def compare_frame(self, metric: str) -> Any:
        """Return a pandas DataFrame comparing stored experiment runs."""

        return self._experiment_runs.compare_frame(metric)

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
        return self._factor_workbench.discover_factors(
            query,
            sources=sources,
            max_results=max_results,
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
        return self._factor_workbench.discover_factors_frame(
            query,
            sources=sources,
            max_results=max_results,
            from_year=from_year,
            to_year=to_year,
            refresh=refresh,
        )

    def draft_factor_spec(self, idea: FactorIdea) -> FactorSpec:
        """Draft a non-executable factor hypothesis from one discovered idea."""
        return self._factor_workbench.draft_factor_spec(idea)

    def draft_factor_specs(
        self,
        ideas: FactorDiscoveryResult | Sequence[FactorIdea],
    ) -> tuple[FactorSpec, ...]:
        """Draft non-executable factor hypotheses from discovered ideas."""
        return self._factor_workbench.draft_factor_specs(ideas)

    def save_factor_spec(self, spec: FactorSpec) -> Path:
        """Persist one non-executable factor hypothesis draft."""
        return self._factor_workbench.save_factor_spec(spec)

    def save_factor_specs(self, specs: Sequence[FactorSpec]) -> tuple[Path, ...]:
        """Persist multiple non-executable factor hypothesis drafts."""
        return self._factor_workbench.save_factor_specs(specs)

    def list_factor_specs(self) -> tuple[FactorSpec, ...]:
        """Return persisted factor hypothesis drafts sorted by name."""
        return self._factor_workbench.list_factor_specs()

    def load_factor_spec(self, name: str) -> FactorSpec:
        """Load one persisted factor hypothesis draft by name."""
        return self._factor_workbench.load_factor_spec(name)

    def find_factor_candidates(
        self,
        query: str,
        *,
        sources: Sequence[str] | None = None,
        max_results: int | None = None,
        from_year: int | None = None,
        to_year: int | None = None,
        refresh: bool = False,
    ) -> FactorCandidateBatch:
        """Discover, draft, and persist non-executable factor candidates."""
        return self._factor_workbench.find_factor_candidates(
            query,
            sources=sources,
            max_results=max_results,
            from_year=from_year,
            to_year=to_year,
            refresh=refresh,
        )

    def find_factor_candidates_frame(
        self,
        query: str,
        *,
        sources: Sequence[str] | None = None,
        max_results: int | None = None,
        from_year: int | None = None,
        to_year: int | None = None,
        refresh: bool = False,
    ) -> Any:
        """Return discovered factor candidates as a pandas DataFrame."""
        return self._factor_workbench.find_factor_candidates_frame(
            query,
            sources=sources,
            max_results=max_results,
            from_year=from_year,
            to_year=to_year,
            refresh=refresh,
        )

    def review_factor_spec(
        self,
        name: str,
        *,
        decision: str,
        reviewer: str,
        notes: Sequence[str] = (),
        reviewed_at: datetime | None = None,
    ) -> FactorSpecReview:
        """Record a research review decision for a persisted factor spec."""
        return self._factor_workbench.review_factor_spec(
            name,
            decision=decision,
            reviewer=reviewer,
            notes=notes,
            reviewed_at=reviewed_at,
        )

    def list_factor_reviews(
        self,
        *,
        decision: str | None = None,
    ) -> tuple[FactorSpecReview, ...]:
        """Return persisted factor spec review decisions."""
        return self._factor_workbench.list_factor_reviews(decision=decision)

    def list_factor_specs_by_status(self, status: str) -> tuple[FactorSpec, ...]:
        """Return persisted factor specs filtered by review status."""
        return self._factor_workbench.list_factor_specs_by_status(status)

    def review_queue_frame(self, *, status: str = "draft") -> Any:
        """Return factor specs awaiting review as a pandas DataFrame."""
        return self._factor_workbench.review_queue_frame(status=status)

    def evaluate_factor(
        self,
        *,
        factor_name: str,
        factor_version: str,
        snapshots: Sequence[Mapping[str, Any]],
        bucket_count: int = 5,
        output_dir: Path | None = None,
    ) -> tuple[EvaluatedFactorSnapshot, ...]:
        """Evaluate deterministic factor snapshot inputs and write artifacts."""
        return self._factor_evaluation.evaluate_factor(
            factor_name=factor_name,
            factor_version=factor_version,
            snapshots=snapshots,
            bucket_count=bucket_count,
            output_dir=output_dir,
        )

    def factor_tearsheet(self, artifact_paths: Sequence[Path]) -> FactorEvaluationTearsheet:
        """Build a factor-evaluation tearsheet from existing research artifacts."""
        return self._factor_evaluation.factor_tearsheet(artifact_paths)

    def factor_tearsheet_frame(self, artifact_paths: Sequence[Path]) -> Any:
        """Return a factor-evaluation tearsheet as a pandas DataFrame."""
        return self._factor_evaluation.factor_tearsheet_frame(artifact_paths)

    def record_factor_tearsheet(
        self,
        artifact_paths: Sequence[Path],
        *,
        experiment_id: str,
        strategy_name: str = "factor-tearsheet",
        strategy_version: str = "1",
        dataset_ids: Sequence[str] = (),
        recorded_at: datetime | None = None,
    ) -> ExperimentStoreRecord:
        """Write and index a deterministic factor-evaluation tearsheet artifact."""
        return self._factor_evaluation.record_factor_tearsheet(
            artifact_paths,
            experiment_id=experiment_id,
            strategy_name=strategy_name,
            strategy_version=strategy_version,
            dataset_ids=dataset_ids,
            recorded_at=recorded_at,
        )

    def start_experiment(
        self,
        experiment_id: str,
        *,
        strategy_name: str,
        strategy_version: str = "1",
    ) -> ResearchExperimentRecorder:
        """Start a manifest-backed research experiment recorder."""

        return ResearchExperimentRecorder(
            ResearchExperimentRecorderConfig(
                experiment_id=experiment_id,
                strategy_name=strategy_name,
                strategy_version=strategy_version,
                manifest_root=self._config.output_root / "experiments",
                store=self._store,
            )
        )


__all__ = ["ResearchSession", "ResearchSessionConfig"]
