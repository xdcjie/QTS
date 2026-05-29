from __future__ import annotations

import math
from pathlib import Path

import pytest
from qts.research.metrics import ResearchMetrics
from qts.research.metrics_schema import ResearchMetricsSchema


def test_schema_v2_declares_schema_identity() -> None:
    schema = ResearchMetricsSchema.from_yaml(Path("configs/research/metrics/schema_v2.yaml"))
    promotion_eligible = schema.definition_for("research.promotion_eligible")

    assert schema.schema_id == "schema_v2"
    assert promotion_eligible is not None
    assert promotion_eligible.type == "bool"
    assert promotion_eligible.unit == "boolean"
    assert promotion_eligible.direction == "neutral"
    assert "promotion" in promotion_eligible.required_for


def test_schema_v2_accepts_valid_promotion_metrics() -> None:
    schema = ResearchMetricsSchema.from_yaml(Path("configs/research/metrics/schema_v2.yaml"))

    result = schema.validate(
        _valid_metrics(),
        purpose="promotion",
    )

    assert result.accepted is True
    assert result.passed is True
    assert result.reasons == ()
    assert result.to_payload() == {
        "accepted": True,
        "passed": True,
        "reasons": [],
        "warnings": [],
    }


def test_schema_v2_fails_when_purpose_required_metric_is_missing() -> None:
    schema = ResearchMetricsSchema.from_yaml(Path("configs/research/metrics/schema_v2.yaml"))
    metrics = _valid_metrics()
    del metrics["quality"]["sharpe"]

    result = schema.validate(metrics, purpose="promotion")

    assert result.accepted is False
    assert result.passed is False
    assert "quality.sharpe missing for promotion" in result.reasons


def test_schema_v2_fails_wrong_type_and_rejects_bool_as_number() -> None:
    schema = ResearchMetricsSchema.from_payload(
        {
            "schema_id": "schema_v2",
            "schema_version": 2,
            "metrics": [
                {
                    "path": "quality.sharpe",
                    "type": "float",
                    "unit": "ratio",
                    "direction": "higher_is_better",
                    "required_for": ["promotion"],
                },
                {
                    "path": "trading.oos_trade_count",
                    "type": "int",
                    "unit": "count",
                    "direction": "higher_is_better",
                    "required_for": ["promotion"],
                },
            ],
        }
    )

    result = schema.validate(
        {
            "quality": {"sharpe": True},
            "trading": {"oos_trade_count": False},
        },
        purpose="promotion",
    )

    assert result.accepted is False
    assert result.passed is False
    assert "quality.sharpe expected float" in result.reasons
    assert "trading.oos_trade_count expected int" in result.reasons


def test_research_metrics_from_payload_preserves_group_only_validation() -> None:
    metrics = ResearchMetrics.from_payload(ResearchMetrics.dry_run(candidate_count=3).to_payload())

    assert metrics.to_payload()["research"]["candidate_count"] == 3


def test_research_metrics_from_payload_can_validate_with_schema_for_purpose() -> None:
    schema = ResearchMetricsSchema.from_yaml(Path("configs/research/metrics/schema_v2.yaml"))
    payload = ResearchMetrics.dry_run(candidate_count=3).to_payload()

    with pytest.raises(ValueError, match="trading.oos_months missing for promotion"):
        ResearchMetrics.from_payload(payload, metrics_schema=schema, purpose="promotion")


def test_schema_v2_fails_max_drawdown_outside_unit_interval() -> None:
    schema = ResearchMetricsSchema.from_yaml(Path("configs/research/metrics/schema_v2.yaml"))
    metrics = _valid_metrics()
    metrics["risk"]["max_drawdown"] = 1.2

    result = schema.validate(metrics, purpose="promotion")

    assert result.accepted is False
    assert result.passed is False
    assert "risk.max_drawdown above maximum 1.0" in result.reasons


def test_schema_v2_rejects_non_finite_numeric_metrics() -> None:
    schema = ResearchMetricsSchema.from_yaml(Path("configs/research/metrics/schema_v2.yaml"))
    metrics = _valid_metrics()
    metrics["quality"]["sharpe"] = math.nan
    metrics["quality"]["profit_factor"] = math.inf
    metrics["risk"]["max_drawdown"] = -math.inf

    result = schema.validate(metrics, purpose="promotion")

    assert result.accepted is False
    assert "quality.sharpe must be finite" in result.reasons
    assert "quality.profit_factor must be finite" in result.reasons
    assert "risk.max_drawdown must be finite" in result.reasons


def test_schema_v2_exposes_metric_definition_metadata() -> None:
    schema = ResearchMetricsSchema.from_yaml(Path("configs/research/metrics/schema_v2.yaml"))

    definition = schema.definition_for("risk.max_drawdown")

    assert definition is not None
    assert definition.unit == "ratio"
    assert definition.direction == "lower_is_better"
    assert definition.minimum == 0.0
    assert definition.maximum == 1.0


def _valid_metrics() -> dict[str, dict[str, object]]:
    return {
        "execution": {
            "cost_impact": 0.01,
            "slippage_sensitivity": 0.02,
        },
        "performance": {
            "oos_sharpe": 1.0,
            "train_sharpe": 1.2,
        },
        "portfolio": {"correlation_to_active": 0.3},
        "quality": {
            "profit_factor": 1.4,
            "sharpe": 1.1,
        },
        "research": {
            "deterministic_replay_passed": True,
            "no_lookahead_passed": True,
            "promotion_eligible": True,
        },
        "risk": {"max_drawdown": 0.2},
        "stability": {
            "parameter_sensitivity": 0.8,
            "walk_forward_consistency": 0.75,
        },
        "trading": {
            "oos_months": 12.0,
            "oos_trade_count": 40,
        },
    }
