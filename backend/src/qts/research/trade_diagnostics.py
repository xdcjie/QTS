"""Trade-level diagnostics evidence for research promotion review."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class TradeDiagnostic:
    """Required R-multiple diagnostics for one completed trade."""

    r_pnl: float | None = None
    mae_r: float | None = None
    mfe_r: float | None = None
    exit_reason: str | None = None
    direction: str | None = None
    quantity: float | int | None = None
    exited_at: datetime | None = None
    factor_values: Mapping[str, float] | None = None
    diagnostics_complete: bool = True

    def __post_init__(self) -> None:
        if self.r_pnl is None:
            raise ValueError("Trade diagnostics require R_pnl")
        if self.mae_r is None:
            raise ValueError("Trade diagnostics require MAE_R")
        if self.mfe_r is None:
            raise ValueError("Trade diagnostics require MFE_R")
        if not self.exit_reason:
            raise ValueError("Trade diagnostics require exit_reason")
        object.__setattr__(self, "factor_values", dict(self.factor_values or {}))


@dataclass(frozen=True, slots=True)
class TradeDiagnosticSummary:
    """Aggregate diagnostics for one trade group."""

    trade_count: int
    average_r_pnl: float
    average_mae_r: float
    average_mfe_r: float

    @classmethod
    def from_trades(cls, trades: Sequence[TradeDiagnostic]) -> TradeDiagnosticSummary:
        """Summarize required R diagnostics for a deterministic trade group."""

        if not trades:
            return cls(
                trade_count=0,
                average_r_pnl=0.0,
                average_mae_r=0.0,
                average_mfe_r=0.0,
            )
        count = len(trades)
        return cls(
            trade_count=count,
            average_r_pnl=sum(trade.r_pnl or 0.0 for trade in trades) / count,
            average_mae_r=sum(trade.mae_r or 0.0 for trade in trades) / count,
            average_mfe_r=sum(trade.mfe_r or 0.0 for trade in trades) / count,
        )


@dataclass(frozen=True, slots=True)
class FactorBucketSpec:
    """Bucket rule for grouping trades by a factor value."""

    factor_name: str
    buckets: tuple[tuple[str, float | None, float | None], ...]

    def __init__(
        self,
        *,
        factor_name: str,
        buckets: Sequence[tuple[str, float | None, float | None]],
    ) -> None:
        if not factor_name:
            raise ValueError("factor_name is required")
        if not buckets:
            raise ValueError("factor buckets are required")
        object.__setattr__(self, "factor_name", factor_name)
        object.__setattr__(self, "buckets", tuple(buckets))

    def bucket_for(self, value: float) -> str | None:
        """Return the first bucket containing the factor value."""

        for label, lower, upper in self.buckets:
            if lower is not None and value < lower:
                continue
            if upper is not None and value >= upper:
                continue
            return label
        return None


@dataclass(frozen=True, slots=True)
class TradeDiagnosticsReport:
    """Research artifact summarizing complete trade-level diagnostics."""

    trades: tuple[TradeDiagnostic, ...]

    def __init__(self, *, trades: Sequence[TradeDiagnostic]) -> None:
        object.__setattr__(self, "trades", tuple(trades))

    @property
    def has_complete_diagnostics(self) -> bool:
        """Return whether every trade has complete diagnostics and at least one trade exists."""

        return bool(self.trades) and all(trade.diagnostics_complete for trade in self.trades)

    def group_by_direction(self) -> dict[str, TradeDiagnosticSummary]:
        """Summarize trades by direction."""

        return self._group_by(lambda trade: trade.direction or "<missing>")

    def group_by_exit_reason(self) -> dict[str, TradeDiagnosticSummary]:
        """Summarize trades by exit reason."""

        return self._group_by(lambda trade: trade.exit_reason or "<missing>")

    def group_by_quantity(self) -> dict[str, TradeDiagnosticSummary]:
        """Summarize trades by executed quantity."""

        return self._group_by(
            lambda trade: str(trade.quantity) if trade.quantity is not None else "<missing>"
        )

    def group_by_time_bucket(
        self,
        buckets: Mapping[str, tuple[int, int]],
    ) -> dict[str, TradeDiagnosticSummary]:
        """Summarize trades by hour-of-day buckets in each trade timestamp timezone."""

        def key_for(trade: TradeDiagnostic) -> str:
            if trade.exited_at is None:
                return "<missing>"
            hour = trade.exited_at.hour
            for label, (start_hour, end_hour) in buckets.items():
                if start_hour <= hour < end_hour:
                    return label
            return "<unbucketed>"

        return self._group_by(key_for)

    def group_by_factor_buckets(
        self,
        bucket_spec: FactorBucketSpec,
    ) -> dict[str, TradeDiagnosticSummary]:
        """Summarize trades by configured factor-value buckets."""

        def key_for(trade: TradeDiagnostic) -> str:
            value = (trade.factor_values or {}).get(bucket_spec.factor_name)
            if value is None:
                return "<missing>"
            return bucket_spec.bucket_for(value) or "<unbucketed>"

        return self._group_by(key_for)

    def _group_by(
        self,
        key_for: Callable[[TradeDiagnostic], str],
    ) -> dict[str, TradeDiagnosticSummary]:
        groups: defaultdict[str, list[TradeDiagnostic]] = defaultdict(list)
        for trade in self.trades:
            groups[key_for(trade)].append(trade)
        return {key: TradeDiagnosticSummary.from_trades(groups[key]) for key in sorted(groups)}


@dataclass(frozen=True, slots=True)
class PaperCandidateDiagnosticsValidation:
    """Promotion gate result for trade diagnostics evidence."""

    blocks_paper_candidate: bool
    missing_fields: tuple[str, ...]


class PaperCandidateDiagnosticsGate:
    """Validates that paper-candidate evidence includes trade diagnostics."""

    def validate(
        self,
        report: TradeDiagnosticsReport | None,
    ) -> PaperCandidateDiagnosticsValidation:
        """Return whether missing or incomplete diagnostics block paper candidacy."""

        if report is None or not report.has_complete_diagnostics:
            return PaperCandidateDiagnosticsValidation(
                blocks_paper_candidate=True,
                missing_fields=("trade_diagnostics",),
            )
        return PaperCandidateDiagnosticsValidation(
            blocks_paper_candidate=False,
            missing_fields=(),
        )
