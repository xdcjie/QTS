"""Stable research-system metrics schema."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from qts.research.metrics_schema import ResearchMetricsSchema

REQUIRED_METRIC_GROUPS = (
    "return",
    "risk",
    "quality",
    "trading",
    "stability",
    "execution",
    "portfolio",
)


@dataclass(frozen=True, slots=True)
class ResearchMetrics:
    """Stable comparable metric payload for research reports and promotion gates."""

    payload: Mapping[str, Any]

    @classmethod
    def dry_run(cls, *, candidate_count: int) -> ResearchMetrics:
        """Return a complete schema with missing real-performance values."""

        return cls(
            {
                "execution": {
                    "capacity_constraints": None,
                    "cost_impact": None,
                    "slippage_sensitivity": None,
                },
                "portfolio": {
                    "correlation_to_active": None,
                    "marginal_contribution": None,
                },
                "quality": {
                    "calmar": None,
                    "expectancy": None,
                    "profit_factor": None,
                    "sharpe": None,
                    "sortino": None,
                    "win_rate": None,
                },
                "research": {
                    "candidate_count": candidate_count,
                    "mode": "dry_run",
                    "promotion_eligible": False,
                },
                "return": {
                    "cagr": None,
                    "monthly_returns": {},
                    "total_return": None,
                    "yearly_returns": {},
                },
                "risk": {
                    "cvar": None,
                    "drawdown_duration": None,
                    "max_drawdown": None,
                    "var": None,
                    "volatility": None,
                },
                "stability": {
                    "parameter_sensitivity": None,
                    "regime_split": {},
                    "rolling_sharpe": [],
                    "walk_forward_consistency": None,
                },
                "trading": {
                    "average_trade": None,
                    "exposure": None,
                    "median_trade": None,
                    "oos_months": None,
                    "oos_trade_count": None,
                    "trade_count": None,
                    "turnover": None,
                },
            }
        )

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, Any],
        *,
        metrics_schema: ResearchMetricsSchema | None = None,
        purpose: str | None = None,
    ) -> ResearchMetrics:
        """Validate and return a metrics object."""

        missing = [group for group in REQUIRED_METRIC_GROUPS if group not in payload]
        if missing:
            raise ValueError(f"metrics missing group: {missing[0]}")
        resolved_payload = dict(payload)
        if metrics_schema is not None:
            if purpose is None:
                raise ValueError("purpose is required when metrics_schema is provided")
            result = metrics_schema.validate(resolved_payload, purpose=purpose)
            if not result.accepted:
                raise ValueError("; ".join(result.reasons))
        return cls(resolved_payload)

    def to_payload(self) -> dict[str, Any]:
        """Return a JSON-ready metrics payload."""

        return {str(key): value for key, value in self.payload.items()}


def metric_value(metrics: Mapping[str, Any], group: str, name: str) -> Any:
    """Return a nested metric value or ``None`` when absent."""

    group_value = metrics.get(group)
    if not isinstance(group_value, Mapping):
        return None
    return group_value.get(name)


__all__ = ["REQUIRED_METRIC_GROUPS", "ResearchMetrics", "metric_value"]
