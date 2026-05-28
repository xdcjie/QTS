"""Unit tests for autonomous research validation gauntlets."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from qts.research.audit_log import ResearchAuditLog
from qts.research.selector import (
    CapacityGate,
    CorrelationGate,
    CostStressGate,
    FailureWindowVetoGate,
    ValidationGauntlet,
    WalkForwardGate,
)


def test_validation_gauntlet_accepts_candidate_and_writes_audit_record(tmp_path: Path) -> None:
    audit_log = ResearchAuditLog(tmp_path / "audit")
    result = _gauntlet().validate(
        _candidate(),
        audit_log=audit_log,
        created_at=datetime(2026, 5, 1, tzinfo=UTC),
    )

    assert result.accepted is True
    assert result.reasons == ()
    assert result.deterministic_replay_status == "passed"
    assert result.no_lookahead_status == "passed"
    assert [decision.gate_name for decision in result.gate_decisions] == [
        "walk_forward",
        "failure_window_veto",
        "cost_stress",
        "correlation",
        "capacity",
    ]

    records = audit_log.list()
    assert len(records) == 1
    assert records[0].record_type == "evidence_validated"
    assert records[0].payload["candidate_id"] == "candidate-001"
    assert result.audit_record_id == records[0].record_id
    assert result.to_payload()["validation_hash"] == result.validation_hash


@pytest.mark.parametrize(
    ("path", "value", "reason"),
    (
        (
            ("validation", "walk_forward", "consistent"),
            False,
            "walk_forward: consistency check failed",
        ),
        (
            ("validation", "failure_windows", 0, "max_drawdown"),
            0.35,
            "failure_window_veto: crisis max_drawdown 0.35 exceeds 0.2",
        ),
        (
            ("validation", "cost_stress", "degradation"),
            0.55,
            "cost_stress: degradation 0.55 exceeds 0.25",
        ),
        (
            ("validation", "correlation", "max_active_correlation"),
            0.93,
            "correlation: max_active_correlation 0.93 exceeds 0.8",
        ),
        (
            ("validation", "capacity", "required_capital"),
            3_000_000,
            "capacity: required_capital 3000000 exceeds estimated_capacity 1000000",
        ),
    ),
)
def test_validation_gauntlet_rejects_gate_breaches(
    path: tuple[str | int, ...],
    value: object,
    reason: str,
) -> None:
    candidate = _candidate()
    _set_path(candidate, path, value)

    result = _gauntlet().validate(candidate)

    assert result.accepted is False
    assert reason in result.reasons


def test_validation_gauntlet_rejects_failed_replay_or_lookahead_status() -> None:
    replay_failure = _candidate()
    _set_path(replay_failure, ("validation", "deterministic_replay", "passed"), False)

    replay_result = _gauntlet().validate(replay_failure)

    assert replay_result.accepted is False
    assert replay_result.deterministic_replay_status == "failed"
    assert "deterministic_replay: replay evidence failed" in replay_result.reasons

    lookahead_failure = _candidate()
    _set_path(lookahead_failure, ("validation", "no_lookahead", "passed"), False)

    lookahead_result = _gauntlet().validate(lookahead_failure)

    assert lookahead_result.accepted is False
    assert lookahead_result.no_lookahead_status == "failed"
    assert "no_lookahead: validation evidence failed" in lookahead_result.reasons


def _gauntlet() -> ValidationGauntlet:
    return ValidationGauntlet(
        walk_forward_gate=WalkForwardGate(min_test_windows=2, max_train_test_gap=0.40),
        failure_window_gate=FailureWindowVetoGate(max_drawdown=0.20),
        cost_stress_gate=CostStressGate(
            max_degradation=0.25,
            max_slippage_sensitivity=0.15,
        ),
        correlation_gate=CorrelationGate(max_active_correlation=0.80),
        capacity_gate=CapacityGate(max_turnover=4.0),
    )


def _candidate() -> dict[str, Any]:
    return {
        "candidate_id": "candidate-001",
        "validation": {
            "walk_forward": {
                "consistent": True,
                "test_windows": (
                    {"name": "split-001", "accepted": True, "score": 1.10},
                    {"name": "split-002", "accepted": True, "score": 0.90},
                ),
                "max_train_test_gap": 0.30,
            },
            "failure_windows": (
                {"name": "crisis", "max_drawdown": 0.12},
                {"name": "rebound", "max_drawdown": 0.08, "report_only": True},
            ),
            "cost_stress": {
                "degradation": 0.12,
                "slippage_sensitivity": 0.05,
                "stressed_score": 0.84,
            },
            "correlation": {
                "active_portfolio_snapshot": {
                    "active_candidate_count": 1,
                    "active_portfolio_status": "computed",
                    "candidate_return_count": 2,
                },
                "max_active_correlation": 0.42,
            },
            "capacity": {
                "estimated_capacity": 1_000_000,
                "required_capital": 500_000,
                "turnover": 1.8,
            },
            "deterministic_replay": {"passed": True, "evidence_id": "replay-001"},
            "no_lookahead": {"passed": True, "evidence_id": "lookahead-001"},
        },
    }


def _set_path(payload: dict[str, Any], path: tuple[str | int, ...], value: object) -> None:
    current: Any = payload
    for part in path[:-1]:
        if isinstance(part, int):
            current = current[part]
        else:
            current = current[part]
    last = path[-1]
    if isinstance(last, int):
        current[last] = value
    else:
        current[last] = value
