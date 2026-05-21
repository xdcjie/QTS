"""Unit tests for optimizer validation constraints."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest
from qts.research.optimizer import (
    MetricConstraint,
    OptimizationResult,
    OptimizerValidationSummary,
    OptimizerValidationSummaryWriter,
)


def _result_with_manifest(tmp_path: Path, metrics: dict[str, str]) -> OptimizationResult:
    tmp_path.mkdir(parents=True, exist_ok=True)
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "run_id": "run-0001",
                "manifest_hash": "abcdef123456",
                "metrics": metrics,
                "runtime_topology": {
                    "accounts": [
                        {
                            "account_id": "acct-backtest",
                            "initial_cash": "100000",
                        }
                    ]
                },
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return OptimizationResult(
        parameters={"window": 20},
        manifest_path=manifest_path,
        manifest_hash="abcdef123456",
        objective_value=Decimal(metrics.get("total_return", "0")),
    )


def test_constraint_rejects_result_below_minimum_metric(tmp_path: Path) -> None:
    result = _result_with_manifest(tmp_path, {"total_return": "0.049"})
    constraint = MetricConstraint("total_return", ">=", Decimal("0.05"))

    decision = constraint.evaluate(result)

    assert not decision.accepted
    assert "total_return" in decision.reason
    assert "0.049" in decision.reason
    assert ">= 0.05" in decision.reason


def test_constraint_accepts_result_that_meets_metric_threshold(tmp_path: Path) -> None:
    result = _result_with_manifest(tmp_path, {"sharpe_ratio": "1.25"})
    constraint = MetricConstraint("sharpe_ratio", ">", Decimal("1.0"))

    decision = constraint.evaluate(result)

    assert decision.accepted
    assert "sharpe_ratio" in decision.reason


def test_constraint_rejects_missing_metric_with_reason(tmp_path: Path) -> None:
    result = _result_with_manifest(tmp_path, {"total_return": "0.1"})
    constraint = MetricConstraint("max_drawdown", "<=", Decimal("0.2"))

    decision = constraint.evaluate(result)

    assert not decision.accepted
    assert "max_drawdown" in decision.reason
    assert "missing" in decision.reason


def test_constraint_rejects_non_parseable_metric_with_distinct_reason(tmp_path: Path) -> None:
    result = _result_with_manifest(tmp_path, {"sharpe_ratio": "abc"})
    constraint = MetricConstraint("sharpe_ratio", ">=", Decimal("1.0"))

    decision = constraint.evaluate(result)

    assert not decision.accepted
    assert decision.reason == "sharpe_ratio value 'abc' is not Decimal-parseable"


def test_constraint_rejects_nan_metric_without_decimal_signal(tmp_path: Path) -> None:
    result = _result_with_manifest(tmp_path, {"sharpe_ratio": "NaN"})
    constraint = MetricConstraint("sharpe_ratio", ">=", Decimal("1.0"))

    decision = constraint.evaluate(result)

    assert not decision.accepted
    assert decision.reason == "sharpe_ratio value 'NaN' is not finite"


def test_constraint_rejects_infinite_metric_even_when_comparison_would_pass(
    tmp_path: Path,
) -> None:
    result = _result_with_manifest(tmp_path, {"sharpe_ratio": "Infinity"})
    constraint = MetricConstraint("sharpe_ratio", ">=", Decimal("1.0"))

    decision = constraint.evaluate(result)

    assert not decision.accepted
    assert decision.reason == "sharpe_ratio value 'Infinity' is not finite"


def test_invalid_metric_constraint_operator_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported constraint operator"):
        MetricConstraint("total_return", "!=", Decimal("0"))


def test_validation_summary_counts_rejected_results(tmp_path: Path) -> None:
    accepted = _result_with_manifest(tmp_path / "accepted", {"total_return": "0.08"})
    rejected = _result_with_manifest(tmp_path / "rejected", {"total_return": "0.01"})
    constraint = MetricConstraint("total_return", ">=", Decimal("0.05"))

    summary = OptimizerValidationSummary.from_results((accepted, rejected), (constraint,))

    assert summary.run_count == 2
    assert summary.accepted_count == 1
    assert summary.rejected_count == 1
    assert summary.rejections[0]["manifest_hash"] == rejected.manifest_hash
    assert "total_return" in summary.rejections[0]["reasons"][0]


def test_validation_summary_accepts_all_results_without_constraints(tmp_path: Path) -> None:
    result = _result_with_manifest(tmp_path, {"total_return": "0.01"})

    summary = OptimizerValidationSummary.from_results((result,))

    assert summary.run_count == 1
    assert summary.accepted_count == 1
    assert summary.rejected_count == 0
    assert summary.rejections == ()


def test_validation_summary_writer_serializes_decimal_parameters(tmp_path: Path) -> None:
    result = _result_with_manifest(tmp_path, {"total_return": "0.01"})
    result.parameters["threshold"] = Decimal("0.25")
    summary = OptimizerValidationSummary.from_results((result,))
    output_path = tmp_path / "validation.json"

    OptimizerValidationSummaryWriter().write(output_path, summary)

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["accepted_runs"][0]["parameters"]["threshold"] == "0.25"


def test_validation_summary_rejects_unsupported_parameter_values(tmp_path: Path) -> None:
    result = _result_with_manifest(tmp_path, {"total_return": "0.01"})
    result.parameters["callback"] = object()

    with pytest.raises(ValueError, match="unsupported optimizer parameter value"):
        OptimizerValidationSummary.from_results((result,))


def test_validation_summary_includes_capital_metrics_and_constraints(
    tmp_path: Path,
) -> None:
    accepted = _result_with_manifest(
        tmp_path / "accepted",
        {
            "avg_gross_exposure": "0.5",
            "total_return": "0.02",
            "total_trades": "4",
        },
    )
    rejected = _result_with_manifest(
        tmp_path / "rejected",
        {
            "avg_gross_exposure": "0.5",
            "total_return": "0.001",
            "total_trades": "2",
        },
    )

    summary = OptimizerValidationSummary.from_results(
        (accepted, rejected),
        (MetricConstraint("pnl_usd", ">=", Decimal("1000")),),
        capital_metric_config={"margin_proxy": "1000"},
    )

    assert summary.accepted_count == 1
    assert summary.rejected_count == 1
    accepted_metrics = summary.accepted_runs[0]["capital_metrics"]
    assert accepted_metrics["initial_cash"] == "100000"
    assert accepted_metrics["pnl_usd"] == "2000.00"
    assert accepted_metrics["pnl_per_trade"] == "500.00"
    assert accepted_metrics["return_on_margin_proxy"] == "2.00"
    assert accepted_metrics["return_on_avg_gross_exposure"] == "0.04"
    assert "pnl_usd=100.000" in summary.rejections[0]["reasons"][0]
