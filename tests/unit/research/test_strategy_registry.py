from __future__ import annotations

import json
from pathlib import Path

import pytest
from qts.research.strategy_registry import (
    LifecycleStatus,
    PromotionDecision,
    StrategyRegistry,
)


def test_registry_requires_complete_strategy_records(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.yaml"
    registry_path.write_text(
        """
strategies:
  - id: vwap_pullback
    owner: research
    status: candidate
    hypothesis: ""
    entrypoint: strategies.production.vwap_production_pullback:VWAPPullbackStrategy
    default_config: configs/research/quickstart.yaml
    failure_conditions:
      - max drawdown breach
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="hypothesis is required"):
        StrategyRegistry.from_yaml(registry_path)


def test_registry_rejects_unknown_lifecycle_status(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.yaml"
    registry_path.write_text(
        """
strategies:
  - id: vwap_pullback
    owner: research
    status: live
    hypothesis: Intraday pullbacks revert after liquidity shocks.
    entrypoint: strategies.production.vwap_production_pullback:VWAPPullbackStrategy
    default_config: configs/research/quickstart.yaml
    failure_conditions:
      - max drawdown breach
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unsupported lifecycle status"):
        StrategyRegistry.from_yaml(registry_path)


def test_strategy_card_must_match_registry_record(tmp_path: Path) -> None:
    registry = StrategyRegistry.from_yaml(_write_registry(tmp_path, status="candidate"))
    card_path = tmp_path / "strategies" / "vwap_pullback" / "card.md"
    card_path.parent.mkdir(parents=True)
    card_path.write_text(
        """
---
id: vwap_pullback
owner: research
status: candidate
hypothesis: Intraday pullbacks revert after liquidity shocks.
entrypoint: strategies.production.vwap_production_pullback:VWAPPullbackStrategy
default_config: configs/research/quickstart.yaml
failure_conditions:
  - max drawdown breach
---
""",
        encoding="utf-8",
    )

    assert registry.require_card(card_path).strategy_id == "vwap_pullback"


def test_strategy_card_rejects_mismatched_status(tmp_path: Path) -> None:
    registry = StrategyRegistry.from_yaml(_write_registry(tmp_path, status="candidate"))
    card_path = tmp_path / "strategies" / "vwap_pullback" / "card.md"
    card_path.parent.mkdir(parents=True)
    card_path.write_text(
        """
---
id: vwap_pullback
owner: research
status: paper_candidate
hypothesis: Intraday pullbacks revert after liquidity shocks.
entrypoint: strategies.production.vwap_production_pullback:VWAPPullbackStrategy
default_config: configs/research/quickstart.yaml
failure_conditions:
  - max drawdown breach
---
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="card status does not match registry"):
        registry.require_card(card_path)


def test_promotion_decision_updates_status_only_with_required_gate(tmp_path: Path) -> None:
    registry = StrategyRegistry.from_yaml(_write_registry(tmp_path, status="research_passed"))
    decision = PromotionDecision(
        decision_id="pd_001",
        run_id="run_001",
        strategy_id="vwap_pullback",
        from_status=LifecycleStatus.RESEARCH_PASSED,
        to_status=LifecycleStatus.PAPER_CANDIDATE,
        gate="paper_candidate_review",
        approved_by="research-lead",
        evidence_refs=("artifacts/research/run_001/report.json",),
    )

    updated = registry.apply_decision(decision)

    assert updated.get("vwap_pullback").status is LifecycleStatus.PAPER_CANDIDATE
    assert decision.to_payload()["strategy_id"] == "vwap_pullback"


def test_promotion_decision_rejects_missing_or_wrong_gate(tmp_path: Path) -> None:
    registry = StrategyRegistry.from_yaml(_write_registry(tmp_path, status="research_passed"))
    decision = PromotionDecision(
        decision_id="pd_001",
        run_id="run_001",
        strategy_id="vwap_pullback",
        from_status=LifecycleStatus.RESEARCH_PASSED,
        to_status=LifecycleStatus.PAPER_CANDIDATE,
        gate="manual_note",
        approved_by="research-lead",
        evidence_refs=("artifacts/research/run_001/report.json",),
    )

    with pytest.raises(ValueError, match="requires gate paper_candidate_review"):
        registry.apply_decision(decision)


def test_promotion_decision_payload_matches_artifact_contract() -> None:
    decision = PromotionDecision(
        decision_id="pd_001",
        run_id="run_001",
        strategy_id="vwap_pullback",
        from_status=LifecycleStatus.CANDIDATE,
        to_status=LifecycleStatus.RESEARCH_PASSED,
        gate="research_passed_review",
        approved_by="research-lead",
        evidence_refs=("artifacts/research/run_001/report.json",),
    )

    payload = decision.to_payload()

    assert json.dumps(payload, sort_keys=True)
    assert payload["artifact"] == "artifacts/research/run_001/promotion_decision.json"
    assert payload["status_transition"] == {
        "from": "candidate",
        "to": "research_passed",
        "gate": "research_passed_review",
    }


def test_checked_in_strategy_registry_and_card_are_valid() -> None:
    registry = StrategyRegistry.from_yaml(Path("strategies/registry.yaml"))

    cards = {
        strategy_id: registry.require_card(Path("strategies") / strategy_id / "card.md")
        for strategy_id in registry.records
    }

    assert set(cards) == {"gc_si_momentum", "vwap_pullback"}


def _write_registry(tmp_path: Path, *, status: str) -> Path:
    registry_path = tmp_path / "registry.yaml"
    registry_path.write_text(
        f"""
strategies:
  - id: vwap_pullback
    owner: research
    status: {status}
    hypothesis: Intraday pullbacks revert after liquidity shocks.
    entrypoint: strategies.production.vwap_production_pullback:VWAPPullbackStrategy
    default_config: configs/research/quickstart.yaml
    failure_conditions:
      - max drawdown breach
""",
        encoding="utf-8",
    )
    return registry_path
