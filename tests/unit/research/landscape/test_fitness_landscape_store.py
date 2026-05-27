"""Unit tests for autonomous research fitness landscape persistence."""

from __future__ import annotations

from pathlib import Path

import pytest
from qts.research.landscape import FitnessLandscapePoint, FitnessLandscapeStore, FitnessQuery


def test_fitness_landscape_store_appends_queries_and_hashes_trials(tmp_path: Path) -> None:
    store = FitnessLandscapeStore(tmp_path / "fitness_landscape.jsonl")
    first = _point("trial-001", accepted=True, strategy_family="momentum", root="GC")
    second = _point(
        "trial-002",
        accepted=False,
        strategy_family="breakout",
        root="SI",
        rejected_reasons=("max_drawdown: 0.31 exceeds 0.2",),
    )

    store.append(first)
    store.append(second)

    landscape = store.read()
    assert landscape.points == (first, second)
    assert store.query(FitnessQuery(campaign_id="campaign-001", root="GC")) == (first,)
    assert store.query(FitnessQuery(strategy_family="breakout", session="rth")) == (second,)
    assert landscape.rejection_reason_counts() == {
        "max_drawdown: 0.31 exceeds 0.2": 1,
    }
    assert landscape.landscape_hash == store.read().landscape_hash


def test_fitness_landscape_store_rejects_duplicate_trial_without_retry_id(
    tmp_path: Path,
) -> None:
    store = FitnessLandscapeStore(tmp_path / "fitness_landscape.jsonl")
    store.append(_point("trial-001", accepted=False))

    with pytest.raises(ValueError, match="duplicate trial_id without retry_id"):
        store.append(_point("trial-001", accepted=True))

    retry = _point("trial-001", accepted=True, retry_id="retry-001")
    store.append(retry)

    assert store.query(FitnessQuery(trial_id="trial-001")) == (
        _point("trial-001", accepted=False),
        retry,
    )


def test_fitness_landscape_point_payload_is_deterministic_json() -> None:
    point = _point("trial-001", accepted=True)

    assert point.point_hash == FitnessLandscapePoint.from_payload(point.to_payload()).point_hash
    assert point.to_payload()["point_hash"] == point.point_hash


def _point(
    trial_id: str,
    *,
    accepted: bool,
    strategy_family: str = "momentum",
    factor_family: str = "carry",
    root: str = "GC",
    regime: str = "trend",
    session: str = "rth",
    rejected_reasons: tuple[str, ...] = (),
    retry_id: str | None = None,
) -> FitnessLandscapePoint:
    return FitnessLandscapePoint(
        trial_id=trial_id,
        retry_id=retry_id,
        campaign_id="campaign-001",
        generation_id="generation-000",
        strategy_family=strategy_family,
        factor_family=factor_family,
        universe=("metals",),
        root=root,
        timeframe="1h",
        regime=regime,
        session=session,
        parameter_hash=f"sha256:{trial_id}",
        metrics={
            "performance": {
                "oos_sharpe": 1.2 if accepted else 0.2,
                "train_sharpe": 1.3,
                "max_drawdown": 0.08 if accepted else 0.31,
            },
            "costs": {"cost_sensitivity": 0.04},
        },
        constraints={"max_drawdown": 0.20},
        accepted=accepted,
        rejected_reasons=rejected_reasons,
        evidence_bundle_id=f"evidence-{trial_id}",
        promotion_packet_id=f"packet-{trial_id}" if accepted else None,
        artifact_graph_hash=f"sha256:artifact-{trial_id}",
    )
