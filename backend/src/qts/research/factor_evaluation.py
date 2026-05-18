"""Deterministic factor evaluation metrics and artifact writing."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from pathlib import Path
from typing import Any

from qts.factors import FactorResult


@dataclass(frozen=True, slots=True)
class FactorEvaluationInput:
    """Owns one dated factor evaluation input snapshot."""

    as_of: date
    factor_name: str
    factor_version: str
    factor_result: FactorResult
    forward_returns: dict[str, Decimal]
    bucket_count: int = 5
    previous_factor_result: FactorResult | None = None

    def __post_init__(self) -> None:
        if not self.factor_name:
            raise ValueError("factor_name is required")
        if not self.factor_version:
            raise ValueError("factor_version is required")
        if self.bucket_count <= 0:
            raise ValueError("bucket_count must be positive")


@dataclass(frozen=True, slots=True)
class FactorEvaluationMetrics:
    """Owns deterministic factor evaluation metric values."""

    rank_ic: Decimal
    long_short_spread: Decimal
    coverage: Decimal
    turnover: Decimal | None
    scored_count: int
    return_count: int
    missing_symbols: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FactorEvaluationResult:
    """Owns the dated result of evaluating one factor snapshot."""

    as_of: date
    factor_name: str
    factor_version: str
    metrics: FactorEvaluationMetrics


class FactorEvaluation:
    """Owns deterministic factor evaluation metric calculations."""

    @classmethod
    def evaluate(cls, evaluation_input: FactorEvaluationInput) -> FactorEvaluationResult:
        """Evaluate a scored factor snapshot against aligned forward returns."""

        scored = cls._scored_returns(evaluation_input)
        if len(scored) < 2:
            raise ValueError("at least two scored assets with forward returns are required")

        missing_symbols = tuple(
            item.asset.symbol
            for item in evaluation_input.factor_result.ranked
            if item.asset.symbol not in evaluation_input.forward_returns
        )
        scored_count = len(evaluation_input.factor_result.ranked)
        return_count = len(scored)
        coverage = _METRIC_CONTEXT.divide(Decimal(return_count), Decimal(scored_count))
        coverage = coverage.quantize(_METRIC_QUANTUM, context=_METRIC_CONTEXT)
        coverage = coverage.normalize(context=_METRIC_CONTEXT)
        metrics = FactorEvaluationMetrics(
            rank_ic=cls._spearman([item[0] for item in scored], [item[1] for item in scored]),
            long_short_spread=_METRIC_CONTEXT.subtract(scored[0][1], scored[-1][1]),
            coverage=coverage,
            turnover=cls._turnover(
                evaluation_input.factor_result,
                evaluation_input.previous_factor_result,
                evaluation_input.bucket_count,
            ),
            scored_count=scored_count,
            return_count=return_count,
            missing_symbols=missing_symbols,
        )
        return FactorEvaluationResult(
            as_of=evaluation_input.as_of,
            factor_name=evaluation_input.factor_name,
            factor_version=evaluation_input.factor_version,
            metrics=metrics,
        )

    @staticmethod
    def _scored_returns(evaluation_input: FactorEvaluationInput) -> list[tuple[Decimal, Decimal]]:
        return [
            (item.value, evaluation_input.forward_returns[item.asset.symbol])
            for item in evaluation_input.factor_result.ranked
            if item.asset.symbol in evaluation_input.forward_returns
        ]

    @classmethod
    def _spearman(cls, left: list[Decimal], right: list[Decimal]) -> Decimal:
        with localcontext(_METRIC_CONTEXT):
            left_ranks = cls._average_ranks(left)
            right_ranks = cls._average_ranks(right)
            left_mean = sum(left_ranks, Decimal("0")) / Decimal(len(left_ranks))
            right_mean = sum(right_ranks, Decimal("0")) / Decimal(len(right_ranks))
            left_variance = sum((rank - left_mean) ** 2 for rank in left_ranks)
            right_variance = sum((rank - right_mean) ** 2 for rank in right_ranks)
            if left_variance == 0 or right_variance == 0:
                raise ValueError("rank IC is undefined for constant ranks")
            covariance = sum(
                (left_rank - left_mean) * (right_rank - right_mean)
                for left_rank, right_rank in zip(left_ranks, right_ranks, strict=True)
            )
            rank_ic = covariance / (left_variance.sqrt() * right_variance.sqrt())
            return rank_ic.quantize(_METRIC_QUANTUM).normalize()

    @staticmethod
    def _average_ranks(values: list[Decimal]) -> list[Decimal]:
        ordered = sorted((value, index) for index, value in enumerate(values))
        ranks = [Decimal("0")] * len(values)
        position = 0
        while position < len(ordered):
            next_position = position + 1
            while (
                next_position < len(ordered) and ordered[next_position][0] == ordered[position][0]
            ):
                next_position += 1
            average_rank = (Decimal(position + 1) + Decimal(next_position)) / Decimal("2")
            for _value, index in ordered[position:next_position]:
                ranks[index] = average_rank
            position = next_position
        return ranks

    @classmethod
    def _turnover(
        cls,
        current: FactorResult,
        previous: FactorResult | None,
        bucket_count: int,
    ) -> Decimal | None:
        if previous is None:
            return None
        current_top = cls._top_bucket_symbols(current, bucket_count)
        previous_top = cls._top_bucket_symbols(previous, bucket_count)
        retained = len(current_top.intersection(previous_top))
        with localcontext(_METRIC_CONTEXT):
            turnover = Decimal("1") - (Decimal(retained) / Decimal(len(current_top)))
            return turnover.quantize(_METRIC_QUANTUM).normalize()

    @staticmethod
    def _top_bucket_symbols(factor_result: FactorResult, bucket_count: int) -> set[str]:
        if not factor_result.ranked:
            return set()
        bucket_size = max(1, -(-len(factor_result.ranked) // bucket_count))
        return {item.asset.symbol for item in factor_result.ranked[:bucket_size]}


class FactorEvaluationArtifactWriter:
    """Owns deterministic factor evaluation artifact serialization."""

    def __init__(self, root_dir: Path) -> None:
        self._root_dir = root_dir

    def write(self, result: FactorEvaluationResult) -> Path:
        """Write a deterministic JSON artifact and return its path."""

        self._root_dir.mkdir(parents=True, exist_ok=True)
        path = self._root_dir / (
            f"{result.as_of.isoformat()}-{result.factor_name}-{result.factor_version}.json"
        )
        payload = {
            "as_of": result.as_of.isoformat(),
            "factor_name": result.factor_name,
            "factor_version": result.factor_version,
            "metrics": self._metrics_payload(result.metrics),
        }
        path.write_text(
            json.dumps(payload, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        return path

    @staticmethod
    def _metrics_payload(metrics: FactorEvaluationMetrics) -> dict[str, object]:
        payload: dict[str, object] = {}
        for key, value in asdict(metrics).items():
            payload[key] = FactorEvaluationArtifactWriter._json_value(value)
        return payload

    @staticmethod
    def _json_value(value: Any) -> object:
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


__all__ = [
    "FactorEvaluation",
    "FactorEvaluationArtifactWriter",
    "FactorEvaluationInput",
    "FactorEvaluationMetrics",
    "FactorEvaluationResult",
]

_METRIC_CONTEXT = Context(prec=50, rounding=ROUND_HALF_EVEN)
_METRIC_QUANTUM = Decimal("0.0000000001")
