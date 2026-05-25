"""Deterministic research factor tearsheet artifacts."""

from __future__ import annotations

import importlib
import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import date
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from pathlib import Path
from typing import Any

from qts.research.factor_evaluation import (
    FactorEvaluationMetrics,
    FactorEvaluationResult,
    FactorSnapshotProtocol,
)


@dataclass(frozen=True, slots=True)
class FactorEvaluationTearsheetMetrics:
    """Owns aggregate factor-evaluation tearsheet metrics."""

    snapshot_count: int
    first_as_of: date
    last_as_of: date
    mean_rank_ic: Decimal
    positive_rank_ic_rate: Decimal
    mean_long_short_spread: Decimal
    mean_coverage: Decimal
    min_coverage: Decimal
    mean_turnover: Decimal | None
    turnover_count: int
    missing_symbols: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FactorEvaluationTearsheet:
    """Owns a deterministic notebook-friendly factor-evaluation tearsheet."""

    factor_name: str
    factor_version: str
    evaluations: tuple[FactorEvaluationResult, ...]
    metrics: FactorEvaluationTearsheetMetrics

    @classmethod
    def from_evaluations(
        cls,
        evaluations: Sequence[FactorEvaluationResult],
    ) -> FactorEvaluationTearsheet:
        """Build a deterministic tearsheet from per-snapshot evaluation results."""

        if not evaluations:
            raise ValueError("at least one factor evaluation is required")
        sorted_evaluations = tuple(sorted(evaluations, key=lambda item: item.as_of))
        factor_name = sorted_evaluations[0].factor_name
        factor_version = sorted_evaluations[0].factor_version
        if any(
            item.factor_name != factor_name or item.factor_version != factor_version
            for item in sorted_evaluations
        ):
            raise ValueError("factor evaluations must share one identity")
        metrics = cls._aggregate_metrics(sorted_evaluations)
        return cls(
            factor_name=factor_name,
            factor_version=factor_version,
            evaluations=sorted_evaluations,
            metrics=metrics,
        )

    @classmethod
    def from_artifact_paths(
        cls,
        artifact_paths: Sequence[Path],
    ) -> FactorEvaluationTearsheet:
        """Build a tearsheet from JSON artifacts written by ``FactorEvaluationArtifactWriter``."""

        return cls.from_evaluations(
            tuple(cls._evaluation_from_artifact(path) for path in artifact_paths)
        )

    def rows(self) -> tuple[dict[str, object], ...]:
        """Return notebook-friendly per-snapshot rows sorted by evaluation date."""

        return tuple(
            {
                "as_of": evaluation.as_of.isoformat(),
                "coverage": evaluation.metrics.coverage,
                "forward_return_protocol": evaluation.protocol.to_payload(),
                "long_short_spread": evaluation.metrics.long_short_spread,
                "missing_symbols": evaluation.metrics.missing_symbols,
                "rank_ic": evaluation.metrics.rank_ic,
                "return_count": evaluation.metrics.return_count,
                "snapshot_hash": evaluation.snapshot_hash,
                "scored_count": evaluation.metrics.scored_count,
                "turnover": evaluation.metrics.turnover,
            }
            for evaluation in self.evaluations
        )

    def to_pandas(self) -> Any:
        """Return per-snapshot rows as a pandas DataFrame."""

        pandas_module: Any = importlib.import_module("pandas")
        return pandas_module.DataFrame(list(self.rows()))

    def manifest_metrics(self) -> dict[str, object]:
        """Return stable summary metrics suitable for an experiment manifest."""

        return {
            "mean_coverage": self._json_value(self.metrics.mean_coverage),
            "mean_long_short_spread": self._json_value(self.metrics.mean_long_short_spread),
            "mean_rank_ic": self._json_value(self.metrics.mean_rank_ic),
            "mean_turnover": self._json_value(self.metrics.mean_turnover),
            "min_coverage": self._json_value(self.metrics.min_coverage),
            "positive_rank_ic_rate": self._json_value(self.metrics.positive_rank_ic_rate),
            "snapshot_count": self.metrics.snapshot_count,
            "turnover_count": self.metrics.turnover_count,
        }

    def to_payload(self) -> dict[str, object]:
        """Return a deterministic JSON-ready tearsheet payload."""

        return {
            "factor_name": self.factor_name,
            "factor_version": self.factor_version,
            "metrics": self._metrics_payload(self.metrics),
            "snapshots": tuple(self._row_payload(row) for row in self.rows()),
        }

    @classmethod
    def _aggregate_metrics(
        cls,
        evaluations: tuple[FactorEvaluationResult, ...],
    ) -> FactorEvaluationTearsheetMetrics:
        rank_ics = tuple(item.metrics.rank_ic for item in evaluations)
        spreads = tuple(item.metrics.long_short_spread for item in evaluations)
        coverages = tuple(item.metrics.coverage for item in evaluations)
        turnovers = tuple(
            item.metrics.turnover for item in evaluations if item.metrics.turnover is not None
        )
        positive_count = sum(1 for item in rank_ics if item > 0)
        missing_symbols = tuple(
            sorted({symbol for item in evaluations for symbol in item.metrics.missing_symbols})
        )
        return FactorEvaluationTearsheetMetrics(
            snapshot_count=len(evaluations),
            first_as_of=evaluations[0].as_of,
            last_as_of=evaluations[-1].as_of,
            mean_rank_ic=cls._mean(rank_ics),
            positive_rank_ic_rate=cls._ratio(positive_count, len(rank_ics)),
            mean_long_short_spread=cls._mean(spreads),
            mean_coverage=cls._mean(coverages),
            min_coverage=min(coverages),
            mean_turnover=cls._mean(turnovers) if turnovers else None,
            turnover_count=len(turnovers),
            missing_symbols=missing_symbols,
        )

    @staticmethod
    def _evaluation_from_artifact(path: Path) -> FactorEvaluationResult:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("factor evaluation artifact must contain a JSON object")
        raw_metrics = payload.get("metrics")
        if not isinstance(raw_metrics, dict):
            raise ValueError("factor evaluation artifact metrics must be a JSON object")
        missing_symbols = raw_metrics.get("missing_symbols", ())
        if not isinstance(missing_symbols, list) or not all(
            isinstance(item, str) for item in missing_symbols
        ):
            raise ValueError("factor evaluation artifact missing_symbols must be a string list")
        turnover = raw_metrics.get("turnover")
        protocol = FactorEvaluationTearsheet._protocol_from_artifact(payload)
        return FactorEvaluationResult(
            as_of=date.fromisoformat(FactorEvaluationTearsheet._required_text(payload, "as_of")),
            factor_name=FactorEvaluationTearsheet._required_text(payload, "factor_name"),
            factor_version=FactorEvaluationTearsheet._required_text(payload, "factor_version"),
            metrics=FactorEvaluationMetrics(
                rank_ic=FactorEvaluationTearsheet._required_decimal(raw_metrics, "rank_ic"),
                long_short_spread=FactorEvaluationTearsheet._required_decimal(
                    raw_metrics,
                    "long_short_spread",
                ),
                coverage=FactorEvaluationTearsheet._required_decimal(raw_metrics, "coverage"),
                turnover=None if turnover is None else Decimal(str(turnover)),
                scored_count=FactorEvaluationTearsheet._required_int(
                    raw_metrics,
                    "scored_count",
                ),
                return_count=FactorEvaluationTearsheet._required_int(
                    raw_metrics,
                    "return_count",
                ),
                missing_symbols=tuple(missing_symbols),
            ),
            forward_return_protocol=protocol,
        )

    @staticmethod
    def _protocol_from_artifact(payload: dict[str, object]) -> Any | None:
        raw_protocol = payload.get("forward_return_protocol")
        if raw_protocol is None:
            return None
        if not isinstance(raw_protocol, dict):
            raise ValueError("factor evaluation artifact forward_return_protocol must be an object")
        protocol = FactorSnapshotProtocol.from_payload(raw_protocol)
        snapshot_hash = payload.get("snapshot_hash")
        if snapshot_hash is not None and snapshot_hash != protocol.snapshot_hash:
            raise ValueError("factor evaluation artifact snapshot_hash does not match protocol")
        return protocol

    @classmethod
    def _metrics_payload(cls, metrics: FactorEvaluationTearsheetMetrics) -> dict[str, object]:
        payload: dict[str, object] = {}
        for key, value in asdict(metrics).items():
            if isinstance(value, date):
                payload[key] = value.isoformat()
            else:
                payload[key] = cls._json_value(value)
        return payload

    @classmethod
    def _row_payload(cls, row: dict[str, object]) -> dict[str, object]:
        return {key: cls._json_value(value) for key, value in row.items()}

    @classmethod
    def _mean(cls, values: Sequence[Decimal]) -> Decimal:
        with localcontext(_METRIC_CONTEXT):
            value = sum(values, Decimal("0")) / Decimal(len(values))
            return cls._canonical_decimal(value)

    @classmethod
    def _ratio(cls, numerator: int, denominator: int) -> Decimal:
        with localcontext(_METRIC_CONTEXT):
            return cls._canonical_decimal(Decimal(numerator) / Decimal(denominator))

    @staticmethod
    def _canonical_decimal(value: Decimal) -> Decimal:
        return value.quantize(_METRIC_QUANTUM, context=_METRIC_CONTEXT).normalize(
            context=_METRIC_CONTEXT
        )

    @staticmethod
    def _json_value(value: object) -> object:
        if isinstance(value, Decimal):
            with localcontext(_METRIC_CONTEXT):
                canonical = value.quantize(_METRIC_QUANTUM)
                text = format(canonical.normalize(), "f")
            if canonical == 0:
                return "0"
            if "." in text:
                return text.rstrip("0").rstrip(".")
            return text
        if isinstance(value, tuple):
            return list(value)
        return value

    @staticmethod
    def _required_text(payload: dict[str, object], field_name: str) -> str:
        value = payload.get(field_name)
        if not isinstance(value, str) or not value:
            raise ValueError(f"{field_name} is required")
        return value

    @staticmethod
    def _required_decimal(payload: dict[str, object], field_name: str) -> Decimal:
        value = payload.get(field_name)
        if value is None:
            raise ValueError(f"{field_name} is required")
        return Decimal(str(value))

    @staticmethod
    def _required_int(payload: dict[str, object], field_name: str) -> int:
        value = payload.get(field_name)
        if not isinstance(value, int):
            raise ValueError(f"{field_name} is required")
        return value


class FactorEvaluationTearsheetArtifactWriter:
    """Owns deterministic factor-evaluation tearsheet artifact serialization."""

    def __init__(self, root_dir: Path) -> None:
        self._root_dir = root_dir

    def write(self, tearsheet: FactorEvaluationTearsheet) -> Path:
        """Write a deterministic factor-evaluation tearsheet JSON artifact."""

        self._require_filename_safe_token(tearsheet.factor_name, "factor_name")
        self._require_filename_safe_token(tearsheet.factor_version, "factor_version")
        self._root_dir.mkdir(parents=True, exist_ok=True)
        path = self._root_dir / f"{tearsheet.factor_name}-{tearsheet.factor_version}-tearsheet.json"
        path.write_text(
            json.dumps(tearsheet.to_payload(), sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        return path

    @staticmethod
    def _require_filename_safe_token(value: str, name: str) -> None:
        if not value or any(character not in _FILENAME_SAFE_CHARS for character in value):
            raise ValueError(f"{name} must be filename-safe")


__all__ = [
    "FactorEvaluationTearsheet",
    "FactorEvaluationTearsheetArtifactWriter",
    "FactorEvaluationTearsheetMetrics",
]

_METRIC_CONTEXT = Context(prec=50, rounding=ROUND_HALF_EVEN)
_METRIC_QUANTUM = Decimal("0.0000000001")
_FILENAME_SAFE_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
)
