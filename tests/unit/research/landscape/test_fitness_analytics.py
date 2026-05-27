"""Unit tests for autonomous research fitness analytics."""

from __future__ import annotations

from qts.research.landscape import FitnessAnalytics, FitnessLandscape, FitnessLandscapePoint


def test_fitness_analytics_identifies_best_family_and_rejection_clusters() -> None:
    analytics = FitnessAnalytics.from_landscape(
        FitnessLandscape(
            (
                _point(
                    "trial-001",
                    strategy_family="momentum",
                    accepted=True,
                    oos_sharpe=1.4,
                    max_drawdown=0.06,
                    cost_sensitivity=0.02,
                ),
                _point(
                    "trial-002",
                    strategy_family="momentum",
                    accepted=True,
                    oos_sharpe=1.0,
                    max_drawdown=0.10,
                    cost_sensitivity=0.04,
                ),
                _point(
                    "trial-003",
                    strategy_family="breakout",
                    accepted=False,
                    oos_sharpe=0.2,
                    max_drawdown=0.32,
                    rejected_reasons=("max_drawdown",),
                ),
                _point(
                    "trial-004",
                    strategy_family="breakout",
                    accepted=False,
                    oos_sharpe=0.3,
                    max_drawdown=0.28,
                    rejected_reasons=("max_drawdown",),
                ),
            )
        )
    )

    payload = analytics.to_payload()

    assert payload["best_family"]["strategy_family"] == "momentum"
    assert payload["best_family"]["risk_adjusted_score"] > 0
    assert payload["rejection_clusters"][0]["reason"] == "max_drawdown"
    assert payload["rejection_clusters"][0]["count"] == 2
    assert payload["analytics_hash"] == analytics.analytics_hash


def test_fitness_analytics_identifies_overfit_parameter_regions_and_regime_stability() -> None:
    analytics = FitnessAnalytics.from_landscape(
        FitnessLandscape(
            (
                _point(
                    "trial-001",
                    parameter_hash="sha256:stable",
                    regime="trend",
                    accepted=True,
                    train_sharpe=1.1,
                    oos_sharpe=1.0,
                ),
                _point(
                    "trial-002",
                    parameter_hash="sha256:overfit",
                    regime="chop",
                    accepted=False,
                    train_sharpe=2.5,
                    oos_sharpe=0.1,
                    rejected_reasons=("walk_forward",),
                ),
            )
        )
    )

    payload = analytics.to_payload()
    overfit = {
        summary["parameter_hash"]: summary["overfit"] for summary in payload["parameter_regions"]
    }
    regimes = {
        summary["regime"]: summary["regime_stability"] for summary in payload["regime_summaries"]
    }

    assert overfit["sha256:overfit"] is True
    assert overfit["sha256:stable"] is False
    assert regimes["trend"] > regimes["chop"]
    assert (
        FitnessAnalytics.from_landscape(
            FitnessLandscape(tuple(reversed(analytics.points)))
        ).to_payload()
        == payload
    )


def _point(
    trial_id: str,
    *,
    strategy_family: str = "momentum",
    factor_family: str = "carry",
    parameter_hash: str = "sha256:param",
    regime: str = "trend",
    accepted: bool,
    train_sharpe: float = 1.2,
    oos_sharpe: float,
    max_drawdown: float = 0.08,
    cost_sensitivity: float = 0.03,
    rejected_reasons: tuple[str, ...] = (),
) -> FitnessLandscapePoint:
    return FitnessLandscapePoint(
        trial_id=trial_id,
        retry_id=None,
        campaign_id="campaign-001",
        generation_id="generation-000",
        strategy_family=strategy_family,
        factor_family=factor_family,
        universe=("metals",),
        root="GC",
        timeframe="1h",
        regime=regime,
        session="rth",
        parameter_hash=parameter_hash,
        metrics={
            "performance": {
                "max_drawdown": max_drawdown,
                "oos_sharpe": oos_sharpe,
                "train_sharpe": train_sharpe,
            },
            "costs": {"cost_sensitivity": cost_sensitivity},
        },
        constraints={"max_drawdown": 0.2},
        accepted=accepted,
        rejected_reasons=rejected_reasons,
        evidence_bundle_id=f"evidence-{trial_id}",
        promotion_packet_id=f"packet-{trial_id}" if accepted else None,
        artifact_graph_hash=f"sha256:artifact-{trial_id}",
    )
