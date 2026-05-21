"""Notebook-friendly research session facade over existing QTS boundaries."""

from __future__ import annotations

import csv
import importlib
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from qts.backtest.engine import BacktestStreamResult
from qts.backtest.pipeline import BacktestPipeline
from qts.core.ids import InstrumentId
from qts.factors import FactorResult, FactorScore
from qts.research.experiment_manifest import ExperimentManifestConfig, ExperimentManifestWriter
from qts.research.experiment_recorder import (
    ResearchExperimentRecorder,
    ResearchExperimentRecorderConfig,
)
from qts.research.experiment_store import ExperimentStore, ExperimentStoreRecord
from qts.research.factor_candidate import FactorCandidateBatch, FactorCandidateWorkflow
from qts.research.factor_discovery import (
    DEFAULT_FACTOR_DISCOVERY_SOURCES,
    FactorDiscovery,
    FactorDiscoveryResult,
    FactorIdea,
    FactorIdeaStore,
)
from qts.research.factor_evaluation import (
    FactorEvaluation,
    FactorEvaluationArtifactWriter,
    FactorEvaluationInput,
    FactorEvaluationResult,
)
from qts.research.factor_spec import FactorSpec, FactorSpecDrafter
from qts.research.factor_spec_store import FactorSpecReview, FactorSpecStore
from qts.research.optimizer.constraints import OptimizationConstraint
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
    FactorEvaluationTearsheetArtifactWriter,
)


@dataclass(frozen=True, slots=True)
class _EvaluatedFactorSnapshot:
    """Owns one evaluated factor snapshot artifact and its evaluation result."""

    artifact_path: Path
    result: FactorEvaluationResult


@dataclass(frozen=True, slots=True)
class _FactorScoreAsset:
    """Tiny symbol adapter for factor-result rank rows."""

    symbol: str


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

    def validate_optimizer_walk_forward(
        self,
        *,
        candidate_parameters: Sequence[Mapping[str, Any]],
        plan: WalkForwardPlan,
        constraints: Iterable[OptimizationConstraint] = (),
        capital_metric_config: Mapping[str, Any] | None = None,
        objective_metric: str | None = None,
        output_root: Path | None = None,
    ) -> WalkForwardValidationSummary:
        """Rerun selected optimizer candidates across walk-forward windows."""
        results = BacktestWalkForwardValidationRunner().run(
            BacktestWalkForwardValidationJob(
                base_config_path=self._config.backtest_config_path,
                candidate_parameters=tuple(dict(parameters) for parameters in candidate_parameters),
                objective_metric=objective_metric or self._config.objective_metric,
                output_root=output_root or self._config.output_root / "walk-forward",
                plan=plan,
            )
        )
        return WalkForwardValidationSummary.from_results(
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

    def save_factor_spec(self, spec: FactorSpec) -> Path:
        """Persist one non-executable factor hypothesis draft."""

        return self.factor_specs.save(spec)

    def save_factor_specs(self, specs: Sequence[FactorSpec]) -> tuple[Path, ...]:
        """Persist multiple non-executable factor hypothesis drafts."""

        return tuple(self.factor_specs.save(spec) for spec in specs)

    def list_factor_specs(self) -> tuple[FactorSpec, ...]:
        """Return persisted factor hypothesis drafts sorted by name."""

        return self.factor_specs.list_specs()

    def load_factor_spec(self, name: str) -> FactorSpec:
        """Load one persisted factor hypothesis draft by name."""

        return self.factor_specs.load(name)

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

        return FactorCandidateWorkflow(
            discovery=self.discovery,
            spec_store=self.factor_specs,
        ).find(
            query,
            sources=self._config.discovery_sources if sources is None else sources,
            max_results=(
                self._config.discovery_max_results if max_results is None else max_results
            ),
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

        return self.find_factor_candidates(
            query,
            sources=sources,
            max_results=max_results,
            from_year=from_year,
            to_year=to_year,
            refresh=refresh,
        ).to_pandas()

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

        return self.factor_specs.record_review(
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

        return self.factor_specs.list_reviews(decision=decision)

    def list_factor_specs_by_status(self, status: str) -> tuple[FactorSpec, ...]:
        """Return persisted factor specs filtered by review status."""

        return self.factor_specs.list_specs_by_status(status)

    def review_queue_frame(self, *, status: str = "draft") -> Any:
        """Return factor specs awaiting review as a pandas DataFrame."""

        pandas_module: Any = importlib.import_module("pandas")
        return pandas_module.DataFrame(
            [
                {
                    "candidate_tags": ", ".join(spec.candidate_tags),
                    "hypothesis": spec.hypothesis,
                    "promotion_gate": spec.promotion_gate,
                    "review_status": spec.review_status,
                    "source_refs": ", ".join(
                        f"{source_ref.source}:{source_ref.external_id}"
                        for source_ref in spec.source_refs
                    ),
                    "spec_name": spec.name,
                }
                for spec in self.list_factor_specs_by_status(status)
            ]
        )

    def evaluate_factor(
        self,
        *,
        factor_name: str,
        factor_version: str,
        snapshots: Sequence[Mapping[str, Any]],
        bucket_count: int = 5,
        output_dir: Path | None = None,
    ) -> tuple[_EvaluatedFactorSnapshot, ...]:
        """Evaluate deterministic factor snapshot inputs and write artifacts."""

        if bucket_count <= 0:
            raise ValueError("bucket_count must be positive")
        if not snapshots:
            raise ValueError("factor_evaluation requires non-empty snapshots")
        writer = FactorEvaluationArtifactWriter(
            output_dir or self._config.output_root / "evaluations"
        )
        runs: list[_EvaluatedFactorSnapshot] = []
        previous_factor_result: FactorResult | None = None
        observed_as_of: set[date] = set()
        for snapshot in snapshots:
            as_of = self._as_of(snapshot.get("as_of"))
            if as_of in observed_as_of:
                raise ValueError("snapshot as_of values must be unique")
            observed_as_of.add(as_of)
            factor_scores = self._load_symbol_decimal_map(
                self._resolve_input_path(snapshot, "factor_scores")
            )
            forward_returns = self._load_symbol_decimal_map(
                self._resolve_input_path(snapshot, "forward_returns"),
                value_column="forward_return",
            )
            factor_result = self._factor_result(
                factor_scores,
                bucket_count=bucket_count,
            )
            evaluation = FactorEvaluation.evaluate(
                FactorEvaluationInput(
                    as_of=as_of,
                    factor_name=factor_name,
                    factor_version=factor_version,
                    factor_result=factor_result,
                    forward_returns=forward_returns,
                    bucket_count=bucket_count,
                    previous_factor_result=previous_factor_result,
                )
            )
            runs.append(
                _EvaluatedFactorSnapshot(
                    artifact_path=writer.write(evaluation),
                    result=evaluation,
                )
            )
            previous_factor_result = factor_result
        return tuple(runs)

    def factor_tearsheet(
        self,
        artifact_paths: Sequence[Path],
    ) -> FactorEvaluationTearsheet:
        """Build a factor-evaluation tearsheet from existing research artifacts."""

        return FactorEvaluationTearsheet.from_artifact_paths(tuple(artifact_paths))

    def factor_tearsheet_frame(self, artifact_paths: Sequence[Path]) -> Any:
        """Return a factor-evaluation tearsheet as a pandas DataFrame."""

        return self.factor_tearsheet(artifact_paths).to_pandas()

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

        self._require_filename_safe_token(experiment_id, "experiment_id")
        tearsheet = self.factor_tearsheet(artifact_paths)
        experiment_root = self._config.output_root / "experiments" / experiment_id
        tearsheet_path = FactorEvaluationTearsheetArtifactWriter(
            experiment_root / "artifacts"
        ).write(tearsheet)
        manifest = ExperimentManifestWriter(
            self._config.output_root / "experiments"
        ).write_manifest(
            ExperimentManifestConfig(
                experiment_id=experiment_id,
                strategy_name=strategy_name,
                strategy_version=strategy_version,
                factor_versions={tearsheet.factor_name: tearsheet.factor_version},
                dataset_ids=dataset_ids,
                config={
                    "factor_name": tearsheet.factor_name,
                    "factor_version": tearsheet.factor_version,
                    "source_artifacts": sorted(str(path) for path in artifact_paths),
                },
                artifact_paths=(tearsheet_path,),
                metrics=tearsheet.manifest_metrics(),
            )
        )
        return self._store.record_manifest(manifest.manifest_path, recorded_at=recorded_at)

    @staticmethod
    def _require_filename_safe_token(value: str, name: str) -> None:
        if not value or any(character not in _FILENAME_SAFE_CHARS for character in value):
            raise ValueError(f"{name} must be filename-safe")

    def _resolve_input_path(self, payload: Mapping[str, Any], key: str) -> Path:
        value = payload.get(key)
        if not isinstance(value, (str, Path)):
            raise ValueError(f"{key} must be a path")
        return Path(value)

    def _as_of(self, value: object) -> date:
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except ValueError as exc:
                raise ValueError("as_of must be an ISO date") from exc
        raise ValueError("as_of must be an ISO date")

    @staticmethod
    def _load_symbol_decimal_map(path: Path, *, value_column: str = "value") -> dict[str, Decimal]:
        if not path.exists():
            raise ValueError(f"missing input path: {path}")
        if path.suffix.lower() == ".json":
            return ResearchSession._load_json_map(path, value_column=value_column)
        return ResearchSession._load_csv_map(path, value_column=value_column)

    @staticmethod
    def _load_json_map(path: Path, *, value_column: str) -> dict[str, Decimal]:
        payload = path.read_text(encoding="utf-8")
        # lightweight parser for simple mapping-style inputs only.
        raw = yaml.safe_load(payload)
        if not isinstance(raw, dict):
            raise ValueError("symbol-value input must be a JSON object")
        values: dict[str, Decimal] = {}
        for symbol, item in raw.items():
            values[ResearchSession._normalize_symbol(symbol)] = ResearchSession._load_decimal(
                item,
                f"{path}: {symbol}",
            )
        if not values:
            raise ValueError(f"{path} contains no rows")
        _ = value_column
        return values

    @staticmethod
    def _load_csv_map(path: Path, *, value_column: str) -> dict[str, Decimal]:
        rows: dict[str, Decimal] = {}
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            headers = tuple(reader.fieldnames or ())
            header_lookup = {item.lower(): item for item in headers}
            symbol_key = header_lookup.get("symbol")
            if symbol_key is None:
                raise ValueError(f"{path} must include symbol header")
            value_key = header_lookup.get(value_column.lower())
            if value_key is None:
                raise ValueError(f"{path} must include {value_column} header")
            for row in reader:
                symbol = row.get(symbol_key)
                raw_value = row.get(value_key)
                if symbol is None or raw_value is None:
                    raise ValueError(f"{path}: invalid row {row}")
                symbol_text = ResearchSession._normalize_symbol(symbol)
                rows[symbol_text] = ResearchSession._load_decimal(
                    raw_value,
                    f"{path}: {symbol_text}",
                )
        if not rows:
            raise ValueError(f"{path} contains no rows")
        return rows

    @staticmethod
    def _factor_result(
        score_map: Mapping[str, Decimal],
        *,
        bucket_count: int,
    ) -> FactorResult:
        if not score_map:
            raise ValueError("factor scores must contain at least one symbol")
        ranked = tuple(
            FactorScore(
                asset=_FactorScoreAsset(symbol=symbol),
                value=score,
            )
            for symbol, score in sorted(
                score_map.items(),
                key=lambda item: (-item[1], item[0]),
            )
        )
        if len(ranked) < 2:
            raise ValueError("at least two ranked factor scores are required")
        return FactorResult(
            ranked=ranked,
        )

    @staticmethod
    def _normalize_symbol(value: object) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("symbol must be a non-empty string")
        return value.strip().upper()

    @staticmethod
    def _load_decimal(value: object, field_name: str) -> Decimal:
        if isinstance(value, Decimal):
            return value
        if isinstance(value, int):
            return Decimal(value)
        if isinstance(value, float):
            return Decimal(str(value))
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                raise ValueError(f"{field_name} must be a decimal")
            try:
                return Decimal(stripped)
            except InvalidOperation as exc:
                raise ValueError(f"{field_name} must be a decimal") from exc
        raise ValueError(f"{field_name} must be a decimal")

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

_FILENAME_SAFE_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
)
