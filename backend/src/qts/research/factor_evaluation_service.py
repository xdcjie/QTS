"""Deterministic factor-evaluation service.

Owns the factor-evaluation workflow extracted from ``ResearchSession``
(QTS-FINAL-011): evaluating deterministic factor-snapshot inputs into
content-addressed evaluation artifacts, building factor tearsheets, recording
them as indexed experiment artifacts, and the symbol/value input loaders that
back them. ``ResearchSession`` keeps a thin facade that delegates here.
"""

from __future__ import annotations

import csv
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from qts.factors import FactorResult, FactorScore
from qts.research.experiment_manifest import ExperimentManifestConfig, ExperimentManifestWriter
from qts.research.experiment_store import ExperimentStore, ExperimentStoreRecord
from qts.research.factor_evaluation import (
    FactorEvaluation,
    FactorEvaluationArtifactWriter,
    FactorEvaluationInput,
    FactorEvaluationResult,
    FactorSnapshotProtocol,
)
from qts.research.tearsheet import (
    FactorEvaluationTearsheet,
    FactorEvaluationTearsheetArtifactWriter,
)

_FILENAME_SAFE_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
)


@dataclass(frozen=True, slots=True)
class _FactorScoreAsset:
    """Tiny symbol adapter for factor-result rank rows."""

    symbol: str


@dataclass(frozen=True, slots=True)
class EvaluatedFactorSnapshot:
    """Owns one evaluated factor snapshot artifact and its evaluation result."""

    artifact_path: Path
    result: FactorEvaluationResult


class FactorEvaluationService:
    """Evaluates factor snapshots and records factor-evaluation artifacts."""

    def __init__(self, *, output_root: Path, store: ExperimentStore) -> None:
        """Create the service bound to an output root and experiment store."""
        self._output_root = output_root
        self._store = store

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

        if bucket_count <= 0:
            raise ValueError("bucket_count must be positive")
        if not snapshots:
            raise ValueError("factor_evaluation requires non-empty snapshots")
        writer = FactorEvaluationArtifactWriter(output_dir or self._output_root / "evaluations")
        runs: list[EvaluatedFactorSnapshot] = []
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
                    forward_return_protocol=self._snapshot_protocol(snapshot, as_of),
                    bucket_count=bucket_count,
                    previous_factor_result=previous_factor_result,
                )
            )
            runs.append(
                EvaluatedFactorSnapshot(
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
        experiment_root = self._output_root / "experiments" / experiment_id
        tearsheet_path = FactorEvaluationTearsheetArtifactWriter(
            experiment_root / "artifacts"
        ).write(tearsheet)
        manifest = ExperimentManifestWriter(self._output_root / "experiments").write_manifest(
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

    def _snapshot_protocol(
        self,
        snapshot: Mapping[str, Any],
        as_of: date,
    ) -> FactorSnapshotProtocol:
        required_fields = (
            "source_data_end",
            "available_at",
            "forward_return_start",
            "forward_return_end",
        )
        if not any(field in snapshot for field in required_fields):
            return FactorSnapshotProtocol.from_as_of(as_of)
        missing = [field for field in required_fields if field not in snapshot]
        if missing:
            raise ValueError(f"factor snapshot protocol missing fields: {', '.join(missing)}")
        return FactorSnapshotProtocol.from_payload(
            {field: snapshot[field] for field in required_fields}
        )

    @staticmethod
    def _load_symbol_decimal_map(path: Path, *, value_column: str = "value") -> dict[str, Decimal]:
        if not path.exists():
            raise ValueError(f"missing input path: {path}")
        if path.suffix.lower() == ".json":
            return FactorEvaluationService._load_json_map(path, value_column=value_column)
        return FactorEvaluationService._load_csv_map(path, value_column=value_column)

    @staticmethod
    def _load_json_map(path: Path, *, value_column: str) -> dict[str, Decimal]:
        payload = path.read_text(encoding="utf-8")
        # lightweight parser for simple mapping-style inputs only.
        raw = yaml.safe_load(payload)
        if not isinstance(raw, dict):
            raise ValueError("symbol-value input must be a JSON object")
        values: dict[str, Decimal] = {}
        for symbol, item in raw.items():
            values[FactorEvaluationService._normalize_symbol(symbol)] = (
                FactorEvaluationService._load_decimal(item, f"{path}: {symbol}")
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
                symbol_text = FactorEvaluationService._normalize_symbol(symbol)
                rows[symbol_text] = FactorEvaluationService._load_decimal(
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


__all__ = ["EvaluatedFactorSnapshot", "FactorEvaluationService"]
