from __future__ import annotations

from pathlib import Path

import pytest
from qts.research.promotion import ResearchPromotionPolicy


def test_promotion_gate_payload_includes_metric_metadata() -> None:
    policy = ResearchPromotionPolicy(
        min_oos_months=6,
        min_oos_trade_count=30,
        min_oos_sharpe=1.0,
        min_profit_factor=1.2,
        max_drawdown=0.25,
        max_cost_impact=0.02,
        max_slippage_sensitivity=0.03,
        min_parameter_stability=0.7,
        min_walk_forward_consistency=0.7,
        max_correlation_to_active=0.5,
    )

    decision = policy.evaluate(
        run_id="run-001",
        strategy_id="vwap",
        metrics={
            "execution": {
                "cost_impact": 0.01,
                "slippage_sensitivity": 0.02,
            },
            "portfolio": {"correlation_to_active": 0.4},
            "quality": {"profit_factor": 1.3, "sharpe": 1.1},
            "research": {
                "deterministic_replay_passed": True,
                "no_lookahead_passed": True,
                "promotion_eligible": True,
            },
            "risk": {"max_drawdown": 0.1},
            "stability": {
                "parameter_sensitivity": 0.8,
                "walk_forward_consistency": 0.75,
            },
            "trading": {
                "oos_months": 12,
                "oos_trade_count": 40,
            },
        },
        reproducibility={},
    )

    payloads = {gate["name"]: gate for gate in decision.to_payload()["gates"]}

    assert payloads["max_drawdown"] == {
        "direction": "lower_is_better",
        "metric_path": "risk.max_drawdown",
        "name": "max_drawdown",
        "observed": 0.1,
        "reason": "risk.max_drawdown must be <= 0.25",
        "status": "passed",
        "threshold": 0.25,
        "unit": "ratio",
    }


def test_promotion_policy_from_yaml_requires_explicit_metrics_schema_binding(
    tmp_path: Path,
) -> None:
    policy_path = tmp_path / "policy.yaml"
    policy_path.write_text(
        """
research_gates:
  min_oos_months: 6
  min_oos_trade_count: 30
  min_oos_sharpe: 1.0
  min_profit_factor: 1.2
  max_drawdown: 0.25
  max_cost_impact: 0.02
  max_slippage_sensitivity: 0.03
  min_parameter_stability: 0.7
  min_walk_forward_consistency: 0.7
  max_correlation_to_active: 0.5
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="metrics_schema_id is required"):
        ResearchPromotionPolicy.from_yaml(policy_path)


def test_promotion_policy_from_yaml_binds_metrics_schema_identity(tmp_path: Path) -> None:
    policy_path = tmp_path / "policy.yaml"
    schema_path = Path("configs/research/metrics/schema_v2.yaml").resolve()
    policy_path.write_text(
        f"""
metrics_schema_id: schema_v2
metrics_schema_path: {schema_path}
research_gates:
  min_oos_months: 6
  min_oos_trade_count: 30
  min_oos_sharpe: 1.0
  min_profit_factor: 1.2
  max_drawdown: 0.25
  max_cost_impact: 0.02
  max_slippage_sensitivity: 0.03
  min_parameter_stability: 0.7
  min_walk_forward_consistency: 0.7
  max_correlation_to_active: 0.5
""",
        encoding="utf-8",
    )

    policy = ResearchPromotionPolicy.from_yaml(policy_path)

    assert policy.metrics_schema_id == "schema_v2"
    assert Path(policy.metrics_schema_path).name == "schema_v2.yaml"


def test_promotion_policy_rejects_metric_schema_id_mismatch() -> None:
    policy = ResearchPromotionPolicy(
        min_oos_months=6,
        min_oos_trade_count=30,
        min_oos_sharpe=1.0,
        min_profit_factor=1.2,
        max_drawdown=0.25,
        max_cost_impact=0.02,
        max_slippage_sensitivity=0.03,
        min_parameter_stability=0.7,
        min_walk_forward_consistency=0.7,
        max_correlation_to_active=0.5,
        metrics_schema_id="schema_v2",
    )
    metrics = _passing_metrics()
    metrics["_metadata"] = {"metrics_schema_id": "schema_v1"}

    decision = policy.evaluate(
        run_id="run-001",
        strategy_id="vwap",
        metrics=metrics,
        reproducibility={},
    )

    assert decision.status == "rejected"
    assert decision.gates[0].name == "metrics_schema"
    assert "metrics schema id mismatch" in decision.gates[0].reason


def test_promotion_policy_rejects_metrics_schema_failures_before_gates() -> None:
    policy = ResearchPromotionPolicy(
        min_oos_months=6,
        min_oos_trade_count=30,
        min_oos_sharpe=1.0,
        min_profit_factor=1.2,
        max_drawdown=0.25,
        max_cost_impact=0.02,
        max_slippage_sensitivity=0.03,
        min_parameter_stability=0.7,
        min_walk_forward_consistency=0.7,
        max_correlation_to_active=0.5,
    )
    metrics = _passing_metrics()
    metrics["quality"]["sharpe"] = "1.1"

    decision = policy.evaluate(
        run_id="run-001",
        strategy_id="vwap",
        metrics=metrics,
        reproducibility={},
    )

    assert decision.status == "rejected"
    assert len(decision.gates) == 1
    assert decision.gates[0].name == "metrics_schema"
    assert decision.gates[0].status == "failed"
    assert "quality.sharpe expected float" in decision.gates[0].reason


def test_promotion_gate_payload_uses_schema_and_metric_source_metadata() -> None:
    policy = ResearchPromotionPolicy(
        min_oos_months=6,
        min_oos_trade_count=30,
        min_oos_sharpe=1.0,
        min_profit_factor=1.2,
        max_drawdown=0.25,
        max_cost_impact=0.02,
        max_slippage_sensitivity=0.03,
        min_parameter_stability=0.7,
        min_walk_forward_consistency=0.7,
        max_correlation_to_active=0.5,
    )
    metrics = _passing_metrics()
    metrics["_metadata"] = {
        "metric_sources": {
            "risk.max_drawdown": {
                "period_role": "out_of_sample",
                "source_artifact_id": "artifact-risk-oos",
            }
        }
    }

    decision = policy.evaluate(
        run_id="run-001",
        strategy_id="vwap",
        metrics=metrics,
        reproducibility={},
    )

    payloads = {gate["name"]: gate for gate in decision.to_payload()["gates"]}

    assert payloads["max_drawdown"]["direction"] == "lower_is_better"
    assert payloads["max_drawdown"]["unit"] == "ratio"
    assert payloads["max_drawdown"]["period_role"] == "out_of_sample"
    assert payloads["max_drawdown"]["source_artifact_id"] == "artifact-risk-oos"


def test_promotion_policy_rejects_promotion_eligible_false() -> None:
    policy = ResearchPromotionPolicy(
        min_oos_months=6,
        min_oos_trade_count=30,
        min_oos_sharpe=1.0,
        min_profit_factor=1.2,
        max_drawdown=0.25,
        max_cost_impact=0.02,
        max_slippage_sensitivity=0.03,
        min_parameter_stability=0.7,
        min_walk_forward_consistency=0.7,
        max_correlation_to_active=0.5,
    )
    metrics = _passing_metrics()
    metrics["research"]["promotion_eligible"] = False

    decision = policy.evaluate(
        run_id="run-001",
        strategy_id="vwap",
        metrics=metrics,
        reproducibility={},
    )

    payloads = {gate["name"]: gate for gate in decision.to_payload()["gates"]}

    assert decision.status == "rejected"
    assert payloads["promotion_eligible"]["status"] == "failed"
    assert payloads["promotion_eligible"]["reason"] == "research.promotion_eligible must be true"


def _passing_metrics() -> dict[str, dict[str, object]]:
    return {
        "execution": {
            "cost_impact": 0.01,
            "slippage_sensitivity": 0.02,
        },
        "portfolio": {"correlation_to_active": 0.4},
        "quality": {"profit_factor": 1.3, "sharpe": 1.1},
        "research": {
            "deterministic_replay_passed": True,
            "no_lookahead_passed": True,
            "promotion_eligible": True,
        },
        "risk": {"max_drawdown": 0.1},
        "stability": {
            "parameter_sensitivity": 0.8,
            "walk_forward_consistency": 0.75,
        },
        "trading": {
            "oos_months": 12,
            "oos_trade_count": 40,
        },
    }
