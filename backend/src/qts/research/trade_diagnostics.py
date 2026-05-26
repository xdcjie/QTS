"""Trade-level diagnostics evidence for research promotion review."""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class TradeDiagnostic:
    """Required R-multiple diagnostics for one completed trade."""

    trade_id: str | None = None
    strategy_id: str | None = None
    idea_id: str | None = None
    symbol: str | None = None
    entry_time: datetime | None = None
    exit_time: datetime | None = None
    entry_price: float | None = None
    exit_price: float | None = None
    r_pnl: float | None = None
    mae_r: float | None = None
    mfe_r: float | None = None
    holding_bars: int | None = None
    exit_reason: str | None = None
    direction: str | None = None
    quantity: float | int | None = None
    exited_at: datetime | None = None
    time_bucket: str | None = None
    factor_values: Mapping[str, float] | None = None
    factor_snapshot: Mapping[str, float] | None = None
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
        exit_time = self.exit_time or self.exited_at
        factor_snapshot = dict(self.factor_snapshot or self.factor_values or {})
        object.__setattr__(self, "exit_time", exit_time)
        object.__setattr__(self, "exited_at", exit_time)
        object.__setattr__(self, "factor_values", factor_snapshot)
        object.__setattr__(self, "factor_snapshot", factor_snapshot)

    def to_payload(self) -> dict[str, Any]:
        """Return a JSON-ready trade diagnostics row."""

        return {
            "diagnostics_complete": self.diagnostics_complete,
            "direction": self.direction,
            "entry_price": self.entry_price,
            "entry_time": _json_ready(self.entry_time),
            "exit_price": self.exit_price,
            "exit_reason": self.exit_reason,
            "exit_time": _json_ready(self.exit_time),
            "exited_at": _json_ready(self.exited_at),
            "factor_snapshot": dict(self.factor_snapshot or {}),
            "factor_values": dict(self.factor_values or {}),
            "holding_bars": self.holding_bars,
            "idea_id": self.idea_id,
            "mae_r": self.mae_r,
            "mfe_r": self.mfe_r,
            "quantity": self.quantity,
            "r_pnl": self.r_pnl,
            "strategy_id": self.strategy_id,
            "symbol": self.symbol,
            "time_bucket": self.time_bucket,
            "trade_id": self.trade_id,
        }

    def missing_standard_artifact_fields(self) -> tuple[str, ...]:
        """Return fields required for standard research diagnostics artifacts."""

        missing: list[str] = []
        for field_name in _STANDARD_TRADE_DIAGNOSTIC_FIELDS:
            value = getattr(self, field_name)
            if isinstance(value, str):
                if not value.strip():
                    missing.append(field_name)
            elif value is None:
                missing.append(field_name)
        if not self.factor_snapshot:
            missing.append("factor_snapshot")
        return tuple(missing)


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

    def to_payload(self) -> dict[str, Any]:
        """Return a JSON-ready aggregate diagnostics payload."""

        return {
            "average_mae_r": self.average_mae_r,
            "average_mfe_r": self.average_mfe_r,
            "average_r_pnl": self.average_r_pnl,
            "trade_count": self.trade_count,
        }


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

    def group_by_time_bucket_label(self) -> dict[str, TradeDiagnosticSummary]:
        """Summarize trades by precomputed time-bucket label."""

        return self._group_by(lambda trade: trade.time_bucket or "<missing>")

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

    def to_summary_payload(self) -> dict[str, Any]:
        """Return the standard trade diagnostics artifact summary payload."""

        return {
            "groups": {
                "direction": _summary_group_payload(self.group_by_direction()),
                "exit_reason": _summary_group_payload(self.group_by_exit_reason()),
                "quantity": _summary_group_payload(self.group_by_quantity()),
                "time_bucket": _summary_group_payload(self.group_by_time_bucket_label()),
            },
            "promotion_boundary": (
                "Trade diagnostics are research evidence only and do not auto-promote "
                "paper/live runtime configuration."
            ),
            "trade_count": len(self.trades),
        }


@dataclass(frozen=True, slots=True)
class TradeDiagnosticsArtifacts:
    """Paths written by the trade diagnostics artifact writer."""

    trades_path: Path
    summary_path: Path
    markdown_path: Path


class TradeDiagnosticsArtifactWriter:
    """Owns deterministic trade diagnostics JSONL, summary, and markdown artifacts."""

    def write(
        self,
        output_dir: str | Path,
        report: TradeDiagnosticsReport,
    ) -> TradeDiagnosticsArtifacts:
        """Write standard trade diagnostics artifacts under an output directory."""

        output_dir = Path(output_dir)
        self._validate_standard_trade_artifacts(report.trades)
        output_dir.mkdir(parents=True, exist_ok=True)
        trades_path = output_dir / "trades.jsonl"
        summary_path = output_dir / "trade_diagnostics_summary.json"
        markdown_path = output_dir / "trade_diagnostics_report.md"
        trade_lines = [json.dumps(trade.to_payload(), sort_keys=True) for trade in report.trades]
        trades_path.write_text(
            "\n".join(trade_lines) + ("\n" if trade_lines else ""),
            encoding="utf-8",
        )
        summary_payload = report.to_summary_payload()
        summary_path.write_text(
            json.dumps(summary_payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        markdown_path.write_text(
            _trade_diagnostics_markdown(summary_payload) + "\n",
            encoding="utf-8",
        )
        return TradeDiagnosticsArtifacts(
            trades_path=trades_path,
            summary_path=summary_path,
            markdown_path=markdown_path,
        )

    @staticmethod
    def _validate_standard_trade_artifacts(trades: Sequence[TradeDiagnostic]) -> None:
        for index, trade in enumerate(trades):
            missing = trade.missing_standard_artifact_fields()
            if missing:
                raise ValueError(
                    "standard trade diagnostics fields missing "
                    f"for trade[{index}]: {', '.join(missing)}"
                )


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
        missing_fields = tuple(
            sorted(
                {
                    field
                    for trade in report.trades
                    for field in trade.missing_standard_artifact_fields()
                }
            )
        )
        if missing_fields:
            return PaperCandidateDiagnosticsValidation(
                blocks_paper_candidate=True,
                missing_fields=missing_fields,
            )
        return PaperCandidateDiagnosticsValidation(
            blocks_paper_candidate=False,
            missing_fields=(),
        )


def _summary_group_payload(
    group: Mapping[str, TradeDiagnosticSummary],
) -> dict[str, dict[str, Any]]:
    return {key: summary.to_payload() for key, summary in group.items()}


def _trade_diagnostics_markdown(summary_payload: Mapping[str, Any]) -> str:
    lines = [
        "# Trade Diagnostics Report",
        "",
        f"trade_count: {summary_payload['trade_count']}",
        "",
        "## Exit Reasons",
        "| Exit reason | Trades | Average R | Average MAE_R | Average MFE_R |",
        "| --- | --- | --- | --- | --- |",
    ]
    exit_reasons = summary_payload["groups"]["exit_reason"]
    for reason, summary in exit_reasons.items():
        lines.append(
            "| "
            f"{reason} | "
            f"{summary['trade_count']} | "
            f"{summary['average_r_pnl']:.12g} | "
            f"{summary['average_mae_r']:.12g} | "
            f"{summary['average_mfe_r']:.12g} |"
        )
    lines.extend(
        [
            "",
            "## Non-Promotion Boundary",
            str(summary_payload["promotion_boundary"]),
        ]
    )
    return "\n".join(lines)


def _json_ready(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    return value


_STANDARD_TRADE_DIAGNOSTIC_FIELDS = (
    "trade_id",
    "strategy_id",
    "idea_id",
    "symbol",
    "direction",
    "quantity",
    "entry_time",
    "exit_time",
    "entry_price",
    "exit_price",
    "holding_bars",
    "time_bucket",
)


__all__ = [
    "FactorBucketSpec",
    "PaperCandidateDiagnosticsGate",
    "PaperCandidateDiagnosticsValidation",
    "TradeDiagnostic",
    "TradeDiagnosticSummary",
    "TradeDiagnosticsArtifactWriter",
    "TradeDiagnosticsArtifacts",
    "TradeDiagnosticsReport",
]
