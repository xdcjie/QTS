"""Phase 3 trial-budget governance tests."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from qts.research.search import TrialBudgetLedger, TrialBudgetManager, TrialBudgetRecord


def _request(
    manager: TrialBudgetManager,
    trial_id: str,
    *,
    campaign_id: str = "campaign-a",
    strategy_family: str = "breakout",
    factor_family: str = "momentum",
    idea_id: str = "idea-a",
    minute: int = 0,
) -> bool:
    return manager.request_trial(
        trial_id=trial_id,
        campaign_id=campaign_id,
        generation_id="generation-1",
        strategy_family=strategy_family,
        factor_family=factor_family,
        idea_id=idea_id,
        time_window="2020-01/2021-01",
        compute_cost=1,
        created_at=datetime(2026, 5, 27, 9, minute, tzinfo=UTC),
    ).accepted


def test_campaign_budget_is_enforced_and_every_decision_is_written(tmp_path: Path) -> None:
    ledger = TrialBudgetLedger(tmp_path)
    manager = TrialBudgetManager(ledger=ledger, campaign_trial_limit=2)

    assert _request(manager, "trial-1")
    assert _request(manager, "trial-2")
    third = manager.request_trial(
        trial_id="trial-3",
        campaign_id="campaign-a",
        generation_id="generation-1",
        strategy_family="breakout",
        factor_family="momentum",
        idea_id="idea-a",
        time_window="2020-01/2021-01",
        compute_cost=1,
        created_at=datetime(2026, 5, 27, 9, 3, tzinfo=UTC),
    )

    assert not third.accepted
    assert third.reason == "campaign trial budget exceeded: 2/2 accepted"
    records = ledger.list()
    assert [record.payload["trial_id"] for record in records] == [
        "trial-1",
        "trial-2",
        "trial-3",
    ]
    assert records[-1].payload["accepted"] is False
    assert records[-1].payload["decision_reason"] == third.reason
    assert ledger.path == tmp_path / "trial_budget_ledger.jsonl"
    assert ledger.verify_hash_chain() == ()


def test_strategy_factor_and_idea_budgets_are_enforced_independently(tmp_path: Path) -> None:
    manager = TrialBudgetManager(
        ledger=TrialBudgetLedger(tmp_path / "trial_budget_ledger.jsonl"),
        campaign_trial_limit=10,
        strategy_family_trial_limit=1,
        factor_family_trial_limit=2,
        idea_trial_limit=1,
    )

    assert _request(manager, "trial-1", strategy_family="breakout", idea_id="idea-a")
    strategy_reject = manager.request_trial(
        trial_id="trial-2",
        campaign_id="campaign-a",
        generation_id="generation-1",
        strategy_family="breakout",
        factor_family="carry",
        idea_id="idea-b",
        created_at=datetime(2026, 5, 27, 9, 2, tzinfo=UTC),
    )
    idea_reject = manager.request_trial(
        trial_id="trial-3",
        campaign_id="campaign-a",
        generation_id="generation-1",
        strategy_family="mean_reversion",
        factor_family="carry",
        idea_id="idea-a",
        created_at=datetime(2026, 5, 27, 9, 3, tzinfo=UTC),
    )
    assert _request(
        manager,
        "trial-4",
        strategy_family="trend",
        factor_family="momentum",
        idea_id="idea-c",
        minute=4,
    )
    factor_reject = manager.request_trial(
        trial_id="trial-5",
        campaign_id="campaign-a",
        generation_id="generation-1",
        strategy_family="seasonal",
        factor_family="momentum",
        idea_id="idea-d",
        created_at=datetime(2026, 5, 27, 9, 5, tzinfo=UTC),
    )

    assert not strategy_reject.accepted
    assert strategy_reject.reason == "strategy family trial budget exceeded: 1/1 accepted"
    assert not idea_reject.accepted
    assert idea_reject.reason == "idea trial budget exceeded: 1/1 accepted"
    assert not factor_reject.accepted
    assert factor_reject.reason == "factor family trial budget exceeded: 2/2 accepted"
    assert manager.ledger.verify_hash_chain() == ()


def test_budget_ledger_hash_chain_detects_tampering(tmp_path: Path) -> None:
    ledger = TrialBudgetLedger(tmp_path / "trial_budget_ledger.jsonl")
    manager = TrialBudgetManager(ledger=ledger, campaign_trial_limit=2)
    assert _request(manager, "trial-1")
    assert _request(manager, "trial-2")

    rows = [json.loads(line) for line in ledger.path.read_text(encoding="utf-8").splitlines()]
    rows[1]["payload"]["trial_id"] = "tampered"
    ledger.path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )

    reasons = ledger.verify_hash_chain()
    assert reasons
    assert "payload_hash mismatch at line 2" in reasons[0]


def test_trial_budget_record_round_trips_with_deterministic_hash() -> None:
    created_at = datetime(2026, 5, 27, 10, 0, tzinfo=UTC)
    payload = {
        "accepted": True,
        "campaign_id": "campaign-a",
        "trial_id": "trial-1",
    }

    record = TrialBudgetRecord.create(
        payload,
        previous_record_hash="sha256:previous",
        created_at=created_at,
    )
    same_record = TrialBudgetRecord.create(
        {"trial_id": "trial-1", "campaign_id": "campaign-a", "accepted": True},
        previous_record_hash="sha256:previous",
        created_at=created_at,
    )

    assert record.record_type == "trial_budget_decision"
    assert record.payload_hash == same_record.payload_hash
    assert record.record_hash == same_record.record_hash
    assert TrialBudgetRecord.from_payload(record.to_payload()) == record


def test_budget_validation_rejects_bad_inputs(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="campaign_trial_limit must be non-negative"):
        TrialBudgetManager(ledger=TrialBudgetLedger(tmp_path), campaign_trial_limit=-1)

    manager = TrialBudgetManager(ledger=TrialBudgetLedger(tmp_path), campaign_trial_limit=1)
    with pytest.raises(ValueError, match="created_at must be timezone-aware"):
        manager.request_trial(
            trial_id="trial-1",
            campaign_id="campaign-a",
            generation_id="generation-1",
            strategy_family="breakout",
            factor_family="momentum",
            idea_id="idea-a",
            created_at=datetime(2026, 5, 27, 10, 0),
        )
