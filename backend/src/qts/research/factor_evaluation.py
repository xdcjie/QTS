"""Deterministic factor evaluation metrics and artifact writing."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, time, timedelta
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from hashlib import sha256
from pathlib import Path
from typing import Any, cast

from qts.factors import FactorResult


@dataclass(frozen=True, slots=True)
class FactorSnapshotProtocol:
    """No-lookahead timing contract for factor snapshots and forward returns."""

    source_data_end: date | datetime
    available_at: date | datetime
    forward_return_start: date | datetime
    forward_return_end: date | datetime

    def __post_init__(self) -> None:
        source_data_end = self._protocol_datetime(self.source_data_end)
        available_at = self._protocol_datetime(self.available_at)
        forward_return_start = self._protocol_datetime(self.forward_return_start)
        forward_return_end = self._protocol_datetime(self.forward_return_end)
        object.__setattr__(self, "source_data_end", source_data_end)
        object.__setattr__(self, "available_at", available_at)
        object.__setattr__(self, "forward_return_start", forward_return_start)
        object.__setattr__(self, "forward_return_end", forward_return_end)
        if source_data_end > available_at:
            raise ValueError("source_data_end must be <= available_at")
        if available_at > forward_return_start:
            raise ValueError("available_at must be <= forward_return_start")
        if forward_return_start >= forward_return_end:
            raise ValueError("forward_return_start must be < forward_return_end")

    @classmethod
    def from_as_of(cls, as_of: date) -> FactorSnapshotProtocol:
        """Return a conservative compatibility protocol for legacy dated inputs."""

        return cls(
            source_data_end=as_of,
            available_at=as_of,
            forward_return_start=as_of + timedelta(days=1),
            forward_return_end=as_of + timedelta(days=2),
        )

    @classmethod
    def from_payload(cls, payload: Mapping[str, object]) -> FactorSnapshotProtocol:
        """Load protocol metadata from a JSON artifact payload."""

        return cls(
            source_data_end=cls._required_protocol_date(payload, "source_data_end"),
            available_at=cls._required_protocol_date(payload, "available_at"),
            forward_return_start=cls._required_protocol_date(payload, "forward_return_start"),
            forward_return_end=cls._required_protocol_date(payload, "forward_return_end"),
        )

    @property
    def snapshot_hash(self) -> str:
        """Return a stable hash of the timing contract."""

        canonical_payload = json.dumps(
            self.to_payload(),
            sort_keys=True,
            separators=(",", ":"),
        )
        return f"sha256:{sha256(canonical_payload.encode('utf-8')).hexdigest()}"

    def to_payload(self) -> dict[str, str]:
        """Return JSON-ready protocol metadata."""

        return {
            "available_at": self._format_protocol_datetime(
                self._protocol_datetime(self.available_at)
            ),
            "forward_return_end": self._format_protocol_datetime(
                self._protocol_datetime(self.forward_return_end)
            ),
            "forward_return_start": self._format_protocol_datetime(
                self._protocol_datetime(self.forward_return_start)
            ),
            "source_data_end": self._format_protocol_datetime(
                self._protocol_datetime(self.source_data_end)
            ),
        }

    @staticmethod
    def _required_protocol_date(payload: Mapping[str, object], field_name: str) -> datetime:
        value = payload.get(field_name)
        if not isinstance(value, str) or not value:
            raise ValueError(f"{field_name} is required")
        return FactorSnapshotProtocol._protocol_datetime(value)

    @staticmethod
    def _protocol_datetime(value: date | datetime | str) -> datetime:
        if isinstance(value, datetime):
            return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
        if isinstance(value, date):
            return datetime.combine(value, time.min, tzinfo=UTC)
        text = value
        if text.endswith("Z"):
            text = f"{text[:-1]}+00:00"
        if "T" not in text:
            return datetime.combine(date.fromisoformat(text), time.min, tzinfo=UTC)
        parsed = datetime.fromisoformat(text)
        return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)

    @staticmethod
    def _format_protocol_datetime(value: datetime) -> str:
        if value.time() == time.min and value.utcoffset() == timedelta(0):
            return value.date().isoformat()
        return value.isoformat()


def _validate_factor_snapshot_protocol(protocol: FactorSnapshotProtocol) -> None:
    """Force protocol construction/validation at call sites that accept Any."""

    source_data_end = FactorSnapshotProtocol._protocol_datetime(protocol.source_data_end)
    available_at = FactorSnapshotProtocol._protocol_datetime(protocol.available_at)
    forward_return_start = FactorSnapshotProtocol._protocol_datetime(protocol.forward_return_start)
    forward_return_end = FactorSnapshotProtocol._protocol_datetime(protocol.forward_return_end)
    if source_data_end > available_at:
        raise ValueError("source_data_end must be <= available_at")
    if available_at > forward_return_start:
        raise ValueError("available_at must be <= forward_return_start")
    if forward_return_start >= forward_return_end:
        raise ValueError("forward_return_start must be < forward_return_end")


@dataclass(frozen=True, slots=True)
class FactorEvaluationInput:
    """Owns one dated factor evaluation input snapshot."""

    as_of: date
    factor_name: str
    factor_version: str
    factor_result: FactorResult
    forward_returns: dict[str, Decimal]
    forward_return_protocol: Any | None = None
    bucket_count: int = 5
    previous_factor_result: FactorResult | None = None

    def __post_init__(self) -> None:
        if not self.factor_name:
            raise ValueError("factor_name is required")
        if not self.factor_version:
            raise ValueError("factor_version is required")
        _require_filename_safe_token(self.factor_name, "factor_name")
        _require_filename_safe_token(self.factor_version, "factor_version")
        if self.bucket_count <= 0:
            raise ValueError("bucket_count must be positive")
        if self.forward_return_protocol is None:
            object.__setattr__(
                self,
                "forward_return_protocol",
                FactorSnapshotProtocol.from_as_of(self.as_of),
            )
        else:
            _validate_factor_snapshot_protocol(self.forward_return_protocol)


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
    forward_return_protocol: Any | None = None

    def __post_init__(self) -> None:
        if self.forward_return_protocol is None:
            object.__setattr__(
                self,
                "forward_return_protocol",
                FactorSnapshotProtocol.from_as_of(self.as_of),
            )
        else:
            _validate_factor_snapshot_protocol(self.forward_return_protocol)

    @property
    def snapshot_hash(self) -> str:
        """Return the deterministic no-lookahead snapshot protocol hash."""

        return self.protocol.snapshot_hash

    @property
    def protocol(self) -> FactorSnapshotProtocol:
        """Return validated no-lookahead timing protocol metadata."""

        if self.forward_return_protocol is None:
            raise ValueError("forward_return_protocol is required")
        return cast(FactorSnapshotProtocol, self.forward_return_protocol)


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
            long_short_spread=cls._long_short_spread(scored, evaluation_input.bucket_count),
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
            forward_return_protocol=evaluation_input.forward_return_protocol,
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
    def _long_short_spread(
        cls,
        scored: list[tuple[Decimal, Decimal]],
        bucket_count: int,
    ) -> Decimal:
        bucket_size = cls._bucket_size(len(scored), bucket_count)
        top_returns = [forward_return for _score, forward_return in scored[:bucket_size]]
        bottom_returns = [forward_return for _score, forward_return in scored[-bucket_size:]]
        with localcontext(_METRIC_CONTEXT):
            top_average = sum(top_returns, Decimal("0")) / Decimal(len(top_returns))
            bottom_average = sum(bottom_returns, Decimal("0")) / Decimal(len(bottom_returns))
            spread = top_average - bottom_average
            return spread.quantize(_METRIC_QUANTUM).normalize()

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
        bucket_size = FactorEvaluation._bucket_size(len(factor_result.ranked), bucket_count)
        return {item.asset.symbol for item in factor_result.ranked[:bucket_size]}

    @staticmethod
    def _bucket_size(item_count: int, bucket_count: int) -> int:
        return max(1, -(-item_count // bucket_count))


class FactorEvaluationArtifactWriter:
    """Owns deterministic factor evaluation artifact serialization."""

    def __init__(self, root_dir: Path) -> None:
        self._root_dir = root_dir

    def write(self, result: FactorEvaluationResult) -> Path:
        """Write a deterministic JSON artifact and return its path."""

        _require_filename_safe_token(result.factor_name, "factor_name")
        _require_filename_safe_token(result.factor_version, "factor_version")
        self._root_dir.mkdir(parents=True, exist_ok=True)
        path = self._root_dir / (
            f"{result.as_of.isoformat()}-{result.factor_name}-{result.factor_version}.json"
        )
        payload = {
            "as_of": result.as_of.isoformat(),
            "factor_name": result.factor_name,
            "factor_version": result.factor_version,
            "forward_return_protocol": result.protocol.to_payload(),
            "metrics": self._metrics_payload(result.metrics),
            "snapshot_hash": result.snapshot_hash,
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


def _require_filename_safe_token(value: str, name: str) -> None:
    if not value or any(character not in _FILENAME_SAFE_CHARS for character in value):
        raise ValueError(f"{name} must be filename-safe")


__all__ = [
    "FactorEvaluation",
    "FactorEvaluationArtifactWriter",
    "FactorEvaluationInput",
    "FactorEvaluationMetrics",
    "FactorEvaluationResult",
    "FactorSnapshotProtocol",
]

_METRIC_CONTEXT = Context(prec=50, rounding=ROUND_HALF_EVEN)
_METRIC_QUANTUM = Decimal("0.0000000001")
_FILENAME_SAFE_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
)
