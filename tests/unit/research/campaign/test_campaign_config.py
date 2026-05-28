from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]
from qts.core.hashing import stable_json_hash
from qts.research.campaign.config import ResearchCampaignConfig
from qts.research.search import CandidateGenerator, SearchSpaceSpec


def test_campaign_config_accepts_valid_contract_and_serializes_payload(
    tmp_path: Path,
) -> None:
    campaign_path = _write_campaign(tmp_path)

    config = ResearchCampaignConfig.from_yaml(campaign_path)
    payload = config.to_payload()

    assert config.campaign_id == "gc_si_auto_alpha_v1"
    assert config.owner == "research"
    assert config.universe.roots == ("GC", "SI")
    assert config.universe.dataset_id == "research_futures_gc_si_1m"
    assert [family.id for family in config.families] == [
        "gc_si_momentum",
        "gc_si_spread_zscore",
    ]
    assert config.objective.components["drawdown_penalty"] == -0.2
    assert config.budget.max_total_trials == 500
    assert config.execution.data_mode == "fixture"
    assert config.execution.max_rows == 50
    assert config.execution.start == "2026-01-02T00:00:00+00:00"
    assert config.execution.end == "2026-02-02T00:00:00+00:00"
    assert config.execution.windows == ()
    assert payload["campaign_hash"] == config.campaign_hash
    assert payload["universe"]["roots"] == ["GC", "SI"]
    assert payload["families"][0]["manifest_template"] == (
        "configs/research/manifests/templates/gc_si_momentum.yaml"
    )
    assert json.loads(json.dumps(payload, sort_keys=True)) == payload


def test_campaign_hash_is_deterministic_from_normalized_payload(tmp_path: Path) -> None:
    campaign_path = _write_campaign(tmp_path)

    first = ResearchCampaignConfig.from_yaml(campaign_path)
    second = ResearchCampaignConfig.from_yaml(campaign_path)

    assert first.campaign_hash == second.campaign_hash
    assert first.campaign_hash == stable_json_hash(first.to_payload(include_hash=False))
    assert first.to_payload() == second.to_payload()


def test_campaign_config_is_public_package_export() -> None:
    import qts.research as research

    assert research.ResearchCampaignConfig is ResearchCampaignConfig
    assert research.ResearchCampaignExecution is not None


def test_gc_si_momentum_alpha_research_config_uses_executable_parameters() -> None:
    campaign = ResearchCampaignConfig.from_yaml(
        "configs/research/campaigns/gc_si_momentum_alpha_research_v1.yaml"
    )
    assert [family.id for family in campaign.families] == ["momentum"]

    search_space = SearchSpaceSpec.from_yaml(campaign.families[0].search_space)
    parameter_names = tuple(parameter.name for parameter in search_space.parameters)
    assert parameter_names == ("root", "short_window", "long_window")

    candidates = CandidateGenerator(search_space).grid()
    assert len(candidates) == 32
    assert {candidate.parameters["root"] for candidate in candidates} == {"GC", "SI"}
    assert all(
        candidate.parameters["short_window"] < candidate.parameters["long_window"]
        for candidate in candidates
    )
    assert campaign.budget.max_trials_per_generation >= len(candidates)
    assert campaign.budget.max_total_trials >= len(candidates) * campaign.budget.max_generations


def test_gc_si_vwap_trend_alpha_research_config_declares_campaign_mapping() -> None:
    campaign = ResearchCampaignConfig.from_yaml(
        "configs/research/campaigns/gc_si_vwap_trend_alpha_research_v1.yaml"
    )
    assert [family.id for family in campaign.families] == ["vwap_trend"]

    search_space = SearchSpaceSpec.from_yaml(campaign.families[0].search_space)
    candidates = CandidateGenerator(search_space).grid()
    assert len(candidates) == 32
    assert {candidate.parameters["root"] for candidate in candidates} == {"GC", "SI"}

    template = yaml.safe_load(
        Path(campaign.families[0].manifest_template).read_text(encoding="utf-8")
    )
    assert template["strategy_entrypoint"] == (
        "strategies.research.vwap_factor_research:VwapFactorResearchStrategy"
    )
    pipeline = template["backtest_pipeline"]
    assert pipeline["root_strategy_parameter"] == "symbol"
    assert set(pipeline["strategy_parameter_names"]) == {
        "min_volume_ratio",
        "target_r_multiple",
        "time_window",
        "vwap_slope_lookback",
    }
    assert campaign.budget.max_trials_per_generation >= len(candidates)


def test_gc_si_vwap_trend_holdout_config_replays_selected_candidate_only() -> None:
    campaign = ResearchCampaignConfig.from_yaml(
        "configs/research/campaigns/gc_si_vwap_trend_holdout_v1.yaml"
    )
    assert campaign.campaign_id == "gc_si_vwap_trend_holdout_v1"
    assert campaign.universe.roots == ("GC", "SI")
    assert [family.id for family in campaign.families] == ["vwap_trend_holdout"]
    assert campaign.execution.data_mode == "full"
    assert campaign.execution.default_mode == "backtest_pipeline"
    assert campaign.execution.metrics_source == "backtest_artifacts"
    assert list(campaign.execution.windows) == [
        {
            "start": "2026-02-03T23:00:00+00:00",
            "end": "2026-02-04T22:00:00+00:00",
        },
        {
            "start": "2026-02-04T23:00:00+00:00",
            "end": "2026-02-05T22:00:00+00:00",
        },
        {
            "start": "2026-02-05T23:00:00+00:00",
            "end": "2026-02-06T22:00:00+00:00",
        },
        {
            "start": "2026-02-23T23:00:00+00:00",
            "end": "2026-02-24T22:00:00+00:00",
        },
        {
            "start": "2026-03-02T23:00:00+00:00",
            "end": "2026-03-03T22:00:00+00:00",
        },
        {
            "start": "2026-03-03T23:00:00+00:00",
            "end": "2026-03-04T22:00:00+00:00",
        },
    ]
    assert all(
        window["start"] >= "2026-02-01T00:00:00+00:00" for window in campaign.execution.windows
    )
    assert not any(window["start"].startswith("2026-01-") for window in campaign.execution.windows)
    assert campaign.budget.max_generations == 1
    assert campaign.budget.max_trials_per_generation == 1
    assert campaign.budget.max_total_trials == 1

    search_space = SearchSpaceSpec.from_yaml(campaign.families[0].search_space)
    candidates = CandidateGenerator(search_space).grid()
    assert len(candidates) == 1
    assert candidates[0].parameters == {
        "root": "GC",
        "time_window": "current_08_16",
        "vwap_slope_lookback": 3,
        "min_volume_ratio": "1.2",
        "target_r_multiple": "1.0",
    }

    template = yaml.safe_load(
        Path(campaign.families[0].manifest_template).read_text(encoding="utf-8")
    )
    pipeline = template["backtest_pipeline"]
    assert pipeline["root_strategy_parameter"] == "symbol"
    assert set(candidates[0].parameters) - {"root"} == set(pipeline["strategy_parameter_names"])


def test_gc_si_vwap_trend_clean_scan_config_searches_full_grid_on_clean_windows() -> None:
    campaign = ResearchCampaignConfig.from_yaml(
        "configs/research/campaigns/gc_si_vwap_trend_clean_scan_v1.yaml"
    )
    assert campaign.campaign_id == "gc_si_vwap_trend_clean_scan_v1"
    assert campaign.universe.roots == ("GC", "SI")
    assert [family.id for family in campaign.families] == ["vwap_trend_clean_scan"]
    assert campaign.execution.data_mode == "full"
    assert list(campaign.execution.windows) == list(
        ResearchCampaignConfig.from_yaml(
            "configs/research/campaigns/gc_si_vwap_trend_holdout_v1.yaml"
        ).execution.windows
    )

    search_space = SearchSpaceSpec.from_yaml(campaign.families[0].search_space)
    candidates = CandidateGenerator(search_space).grid()
    assert len(candidates) == 32
    assert {candidate.parameters["root"] for candidate in candidates} == {"GC", "SI"}
    assert campaign.budget.max_generations == 1
    assert campaign.budget.max_trials_per_generation >= len(candidates)
    assert campaign.budget.max_total_trials >= len(candidates)


def test_gc_si_vwap_trend_post_dst_holdout_replays_clean_scan_winner() -> None:
    campaign = ResearchCampaignConfig.from_yaml(
        "configs/research/campaigns/gc_si_vwap_trend_post_dst_holdout_v1.yaml"
    )
    assert campaign.campaign_id == "gc_si_vwap_trend_post_dst_holdout_v1"
    assert campaign.universe.roots == ("GC", "SI")
    assert [family.id for family in campaign.families] == ["vwap_trend_post_dst_holdout"]
    assert campaign.execution.data_mode == "full"
    assert list(campaign.execution.windows) == [
        {
            "start": "2026-03-12T22:00:00+00:00",
            "end": "2026-03-13T21:00:00+00:00",
        },
        {
            "start": "2026-03-18T22:00:00+00:00",
            "end": "2026-03-19T21:00:00+00:00",
        },
        {
            "start": "2026-03-19T22:00:00+00:00",
            "end": "2026-03-20T21:00:00+00:00",
        },
        {
            "start": "2026-03-23T22:00:00+00:00",
            "end": "2026-03-24T21:00:00+00:00",
        },
        {
            "start": "2026-03-24T22:00:00+00:00",
            "end": "2026-03-25T21:00:00+00:00",
        },
        {
            "start": "2026-03-25T22:00:00+00:00",
            "end": "2026-03-26T21:00:00+00:00",
        },
        {
            "start": "2026-03-30T22:00:00+00:00",
            "end": "2026-03-31T21:00:00+00:00",
        },
    ]

    search_space = SearchSpaceSpec.from_yaml(campaign.families[0].search_space)
    candidates = CandidateGenerator(search_space).grid()
    assert len(candidates) == 1
    assert candidates[0].parameters == {
        "root": "GC",
        "time_window": "evening_18_22",
        "vwap_slope_lookback": 3,
        "min_volume_ratio": "0",
        "target_r_multiple": "2.0",
    }
    assert campaign.budget.max_generations == 1
    assert campaign.budget.max_total_trials == 1


def test_gc_si_vwap_trend_late_holdout_replays_clean_scan_winner() -> None:
    campaign = ResearchCampaignConfig.from_yaml(
        "configs/research/campaigns/gc_si_vwap_trend_late_holdout_v1.yaml"
    )
    assert campaign.campaign_id == "gc_si_vwap_trend_late_holdout_v1"
    assert campaign.universe.roots == ("GC", "SI")
    assert [family.id for family in campaign.families] == ["vwap_trend_late_holdout"]
    assert campaign.families[0].search_space == (
        "configs/research/search/gc_si_vwap_trend_clean_scan_winner_space.yaml"
    )
    assert campaign.execution.data_mode == "full"
    assert len(campaign.execution.windows) == 12
    assert campaign.execution.windows[0] == {
        "start": "2026-04-01T22:00:00+00:00",
        "end": "2026-04-02T21:00:00+00:00",
    }
    assert campaign.execution.windows[-1] == {
        "start": "2026-05-18T22:00:00+00:00",
        "end": "2026-05-19T21:00:00+00:00",
    }

    search_space = SearchSpaceSpec.from_yaml(campaign.families[0].search_space)
    candidates = CandidateGenerator(search_space).grid()
    assert len(candidates) == 1
    assert candidates[0].parameters["root"] == "GC"
    assert candidates[0].parameters["time_window"] == "evening_18_22"
    assert candidates[0].parameters["target_r_multiple"] == "2.0"
    assert campaign.budget.max_generations == 1
    assert campaign.budget.max_total_trials == 1


def test_gc_vwap_trend_robust_scan_searches_gc_grid_across_clean_windows() -> None:
    campaign = ResearchCampaignConfig.from_yaml(
        "configs/research/campaigns/gc_vwap_trend_robust_scan_v1.yaml"
    )
    assert campaign.campaign_id == "gc_vwap_trend_robust_scan_v1"
    assert campaign.universe.roots == ("GC", "SI")
    assert [family.id for family in campaign.families] == ["gc_vwap_trend_robust_scan"]
    assert campaign.execution.data_mode == "full"
    assert len(campaign.execution.windows) == 25
    assert campaign.execution.windows[0] == {
        "start": "2026-02-03T23:00:00+00:00",
        "end": "2026-02-04T22:00:00+00:00",
    }
    assert campaign.execution.windows[-1] == {
        "start": "2026-05-18T22:00:00+00:00",
        "end": "2026-05-19T21:00:00+00:00",
    }

    search_space = SearchSpaceSpec.from_yaml(campaign.families[0].search_space)
    candidates = CandidateGenerator(search_space).grid()
    assert len(candidates) == 16
    assert {candidate.parameters["root"] for candidate in candidates} == {"GC"}
    assert {candidate.parameters["time_window"] for candidate in candidates} == {
        "current_08_16",
        "evening_18_22",
    }
    assert campaign.budget.max_generations == 1
    assert campaign.budget.max_trials_per_generation >= len(candidates)


def test_campaign_config_rejects_invalid_budget(tmp_path: Path) -> None:
    campaign_path = _write_campaign(tmp_path, {"budget": {"max_total_trials": 0}})

    with pytest.raises(ValueError, match="budget.max_total_trials"):
        ResearchCampaignConfig.from_yaml(campaign_path)


def test_campaign_config_requires_explicit_data_mode(tmp_path: Path) -> None:
    campaign_path = _write_campaign(tmp_path, {"execution": {"data_mode": None}})

    with pytest.raises(ValueError, match="execution.data_mode"):
        ResearchCampaignConfig.from_yaml(campaign_path)


def test_campaign_config_rejects_full_mode_truncation(tmp_path: Path) -> None:
    campaign_path = _write_campaign(
        tmp_path,
        {"execution": {"data_mode": "full", "max_rows": 50}},
    )

    with pytest.raises(ValueError, match="execution.max_rows"):
        ResearchCampaignConfig.from_yaml(campaign_path)


def test_campaign_config_requires_fixture_max_rows(tmp_path: Path) -> None:
    payload = _valid_campaign_payload()
    del payload["execution"]["max_rows"]
    campaign_path = tmp_path / "campaign.yaml"
    campaign_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    with pytest.raises(ValueError, match="execution.max_rows"):
        ResearchCampaignConfig.from_yaml(campaign_path)


def test_campaign_config_rejects_partial_execution_window(tmp_path: Path) -> None:
    campaign_path = _write_campaign(tmp_path, {"execution": {"end": None}})

    with pytest.raises(ValueError, match="execution.start and execution.end"):
        ResearchCampaignConfig.from_yaml(campaign_path)


def test_campaign_config_rejects_reversed_execution_window(tmp_path: Path) -> None:
    campaign_path = _write_campaign(
        tmp_path,
        {
            "execution": {
                "start": "2026-02-02T00:00:00+00:00",
                "end": "2026-01-02T00:00:00+00:00",
            }
        },
    )

    with pytest.raises(ValueError, match="execution.start must be before execution.end"):
        ResearchCampaignConfig.from_yaml(campaign_path)


def test_campaign_config_accepts_multi_execution_windows(tmp_path: Path) -> None:
    campaign_path = _write_campaign(
        tmp_path,
        {
            "execution": {
                "end": None,
                "start": None,
                "windows": [
                    {
                        "start": "2026-01-06T23:00:00+00:00",
                        "end": "2026-01-07T22:00:00+00:00",
                    },
                    {
                        "start": "2026-01-07T23:00:00+00:00",
                        "end": "2026-01-08T22:00:00+00:00",
                    },
                ],
            }
        },
    )

    config = ResearchCampaignConfig.from_yaml(campaign_path)

    assert config.execution.start is None
    assert config.execution.end is None
    assert [dict(window) for window in config.execution.windows] == [
        {
            "end": "2026-01-07T22:00:00+00:00",
            "start": "2026-01-06T23:00:00+00:00",
        },
        {
            "end": "2026-01-08T22:00:00+00:00",
            "start": "2026-01-07T23:00:00+00:00",
        },
    ]


def test_campaign_config_rejects_window_and_start_end_mix(tmp_path: Path) -> None:
    campaign_path = _write_campaign(
        tmp_path,
        {
            "execution": {
                "windows": [
                    {
                        "start": "2026-01-06T23:00:00+00:00",
                        "end": "2026-01-07T22:00:00+00:00",
                    }
                ]
            }
        },
    )

    with pytest.raises(ValueError, match="execution.windows cannot be combined"):
        ResearchCampaignConfig.from_yaml(campaign_path)


def test_campaign_config_rejects_invalid_objective_weights(tmp_path: Path) -> None:
    campaign_path = _write_campaign(
        tmp_path,
        {"objective": {"components": {"sharpe": float("nan")}}},
    )

    with pytest.raises(ValueError, match="objective.components.sharpe"):
        ResearchCampaignConfig.from_yaml(campaign_path)


def test_campaign_config_rejects_invalid_constraints(tmp_path: Path) -> None:
    campaign_path = _write_campaign(tmp_path, {"constraints": {"max_drawdown": 1.5}})

    with pytest.raises(ValueError, match="constraints.max_drawdown"):
        ResearchCampaignConfig.from_yaml(campaign_path)


def test_campaign_config_rejects_duplicate_family_ids(tmp_path: Path) -> None:
    campaign_path = _write_campaign(
        tmp_path,
        {
            "families": [
                {
                    "id": "gc_si_momentum",
                    "template": "momentum",
                    "manifest_template": (
                        "configs/research/manifests/templates/gc_si_momentum.yaml"
                    ),
                    "search_space": "configs/research/search/gc_si_momentum_space.yaml",
                },
                {
                    "id": "gc_si_momentum",
                    "template": "pair_spread",
                    "manifest_template": "configs/research/manifests/templates/gc_si_spread.yaml",
                    "search_space": "configs/research/search/gc_si_spread_space.yaml",
                },
            ]
        },
    )

    with pytest.raises(ValueError, match="duplicate campaign family id"):
        ResearchCampaignConfig.from_yaml(campaign_path)


def test_campaign_config_rejects_empty_roots(tmp_path: Path) -> None:
    campaign_path = _write_campaign(tmp_path, {"universe": {"roots": []}})

    with pytest.raises(ValueError, match="universe.roots must not be empty"):
        ResearchCampaignConfig.from_yaml(campaign_path)


def _write_campaign(tmp_path: Path, overrides: dict[str, Any] | None = None) -> Path:
    payload = _valid_campaign_payload()
    if overrides:
        _merge(payload, overrides)
    path = tmp_path / "campaign.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def _valid_campaign_payload() -> dict[str, Any]:
    return {
        "campaign_id": "gc_si_auto_alpha_v1",
        "owner": "research",
        "created_at": "2026-05-27T00:00:00+00:00",
        "universe": {
            "roots": ["GC", "SI"],
            "asset_class": "futures",
            "calendar": "CME",
            "timeframe": "1m",
            "dataset_id": "research_futures_gc_si_1m",
        },
        "families": [
            {
                "id": "gc_si_momentum",
                "template": "momentum",
                "manifest_template": "configs/research/manifests/templates/gc_si_momentum.yaml",
                "search_space": "configs/research/search/gc_si_momentum_space.yaml",
            },
            {
                "id": "gc_si_spread_zscore",
                "template": "pair_spread",
                "manifest_template": "configs/research/manifests/templates/gc_si_spread.yaml",
                "search_space": "configs/research/search/gc_si_spread_space.yaml",
            },
        ],
        "execution": {
            "default_mode": "backtest_pipeline",
            "metrics_source": "backtest_artifacts",
            "data_mode": "fixture",
            "max_rows": 50,
            "start": "2026-01-02T00:00:00+00:00",
            "end": "2026-02-02T00:00:00+00:00",
        },
        "objective": {
            "primary": "composite_score",
            "components": {
                "sharpe": 0.30,
                "annualized_return": 0.20,
                "calmar": 0.20,
                "walk_forward_consistency": 0.15,
                "low_correlation_bonus": 0.10,
                "drawdown_penalty": -0.20,
                "turnover_cost_penalty": -0.10,
            },
        },
        "constraints": {
            "min_oos_months": 24,
            "min_oos_trade_count": 200,
            "min_profit_factor": 1.15,
            "max_drawdown": 0.15,
            "max_cost_impact": 0.25,
            "max_correlation_to_active": 0.50,
        },
        "budget": {
            "max_generations": 3,
            "max_trials_per_generation": 200,
            "max_total_trials": 500,
            "max_family_trials": 150,
            "wall_clock_limit_minutes": 240,
        },
    }


def _merge(target: dict[str, Any], overrides: dict[str, Any]) -> None:
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _merge(target[key], value)
            continue
        target[key] = value
