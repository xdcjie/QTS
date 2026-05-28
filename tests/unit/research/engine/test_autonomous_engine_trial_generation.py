from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]
from qts.research.engine.autonomous_research_engine import (
    AutonomousResearchEngine,
    AutonomousResearchRun,
)


def test_engine_generates_trials_from_campaign_search_space_and_strategy_factory(
    tmp_path: Path,
) -> None:
    campaign_path = write_campaign(tmp_path, families=("momentum",))
    run = AutonomousResearchRun.from_yaml(
        campaign_path,
        data_paths=write_data_paths(tmp_path),
        output_root=tmp_path / "run",
    )

    result = AutonomousResearchEngine(repo_root=Path.cwd()).run(run)

    rows = read_jsonl(result.fitness_landscape_path)
    assert len(rows) == 3
    assert {row["strategy_family"] for row in rows} == {"momentum"}
    assert {row["metrics"]["performance"]["oos_sharpe"] for row in rows}
    assert all(row["parameter_hash"].startswith("sha256:") for row in rows)
    generation_candidate_rows = read_jsonl(
        result.output_root / "generation-000" / "candidate_parameters.jsonl"
    )
    assert {row["parameters"]["lookback"] for row in generation_candidate_rows} <= {5, 10, 15}
    assert all(
        row["candidate_space_hash"].startswith("sha256:") for row in generation_candidate_rows
    )
    assert all(
        row["strategy_variant_hash"].startswith("sha256:") for row in generation_candidate_rows
    )
    assert all(row["trial_id"].startswith("generation-000-trial-") for row in rows)


def test_backtest_data_materialization_mode_controls_truncation(tmp_path: Path) -> None:
    source = tmp_path / "source.csv"
    source.write_text(
        "\n".join(
            ["timestamp,close"]
            + [f"2026-01-02T00:{minute:02d}:00+00:00,{100 + minute:.1f}" for minute in range(60)]
            + [""]
        ),
        encoding="utf-8",
    )
    engine = AutonomousResearchEngine(repo_root=Path.cwd())

    fixture_target = tmp_path / "fixture.csv"
    engine._materialize_backtest_csv(source, fixture_target, symbol="GC", max_rows=10)
    assert len(fixture_target.read_text(encoding="utf-8").splitlines()) == 11

    full_target = tmp_path / "full.csv"
    engine._materialize_backtest_csv(source, full_target, symbol="GC", max_rows=None)
    assert len(full_target.read_text(encoding="utf-8").splitlines()) == 61

    window_target = tmp_path / "window.csv"
    engine._materialize_backtest_csv(
        source,
        window_target,
        symbol="GC",
        max_rows=None,
        window=("2026-01-02T00:10:00+00:00", "2026-01-02T00:20:00+00:00"),
    )
    assert len(window_target.read_text(encoding="utf-8").splitlines()) == 11


def test_full_backtest_data_materialization_reuses_shared_csv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    campaign_path = write_campaign(tmp_path, data_mode="full", max_rows=None)
    data_paths = write_data_paths(tmp_path)
    run = AutonomousResearchRun.from_yaml(
        campaign_path,
        data_paths=data_paths,
        output_root=tmp_path / "run",
    )
    engine = AutonomousResearchEngine(repo_root=Path.cwd())
    calls: list[Path] = []
    original = engine._materialize_backtest_csv

    def counted_materialize(
        source_path: Path,
        target_path: Path,
        *,
        symbol: str,
        max_rows: int | None,
        window: tuple[str, str] | None = None,
        windows: tuple[tuple[str, str], ...] = (),
    ) -> None:
        calls.append(target_path)
        original(
            source_path,
            target_path,
            symbol=symbol,
            max_rows=max_rows,
            window=window,
            windows=windows,
        )

    monkeypatch.setattr(engine, "_materialize_backtest_csv", counted_materialize)

    _first_config, first_csv = engine._write_backtest_data_config(
        run=run,
        trial_id="generation-000-trial-000",
        root="GC",
        data_path=data_paths["GC"],
    )
    _second_config, second_csv = engine._write_backtest_data_config(
        run=run,
        trial_id="generation-000-trial-001",
        root="GC",
        data_path=data_paths["GC"],
    )

    assert first_csv == second_csv
    assert first_csv == tmp_path / "run" / "backtest_data" / "full" / "GC" / "data" / "GC.csv"
    assert len(calls) == 1
    metadata = json.loads(first_csv.with_suffix(".materialization.json").read_text())
    assert metadata["max_rows"] is None


def test_backtest_pipeline_template_maps_research_parameters_to_strategy_config(
    tmp_path: Path,
) -> None:
    campaign_path = write_campaign(tmp_path, families=("momentum",))
    run = AutonomousResearchRun.from_yaml(
        campaign_path,
        data_paths=write_data_paths(tmp_path),
        output_root=tmp_path / "run",
    )
    engine = AutonomousResearchEngine(repo_root=Path.cwd())

    payload = engine._backtest_pipeline_payload(
        run=run,
        trial_id="generation-000-trial-000",
        root="GC",
        parameters={
            "root": "GC",
            "time_window": "evening_18_22",
            "vwap_slope_lookback": 5,
        },
        strategy_entrypoint="strategies.research.vwap_factor_research:VwapFactorResearchStrategy",
        manifest_patch={
            "backtest_pipeline": {
                "root_strategy_parameter": "symbol",
                "strategy_parameter_defaults": {"target_quantity": "1"},
                "strategy_parameter_names": ["time_window", "vwap_slope_lookback"],
            }
        },
    )

    config_payload = yaml.safe_load(
        Path(payload["backtest_config_path"]).read_text(encoding="utf-8")
    )
    assert config_payload["strategy_params"] == {"symbol": "GC", "target_quantity": "1"}
    assert payload["strategy_parameter_defaults"] == {
        "symbol": "GC",
        "target_quantity": "1",
    }
    assert payload["strategy_parameter_names"] == ("time_window", "vwap_slope_lookback")
    assert "strategy_parameter_map" not in payload


def test_generated_trials_use_template_backtest_pipeline_mapping(tmp_path: Path) -> None:
    campaign_path = write_campaign(
        tmp_path,
        families=("momentum",),
        template_extra_lines=(
            "backtest_pipeline:",
            "  root_strategy_parameter: symbol",
            "  strategy_parameter_defaults:",
            "    target_quantity: \"1\"",
            "  strategy_parameter_map:",
            "    lookback: vwap_slope_lookback",
        ),
    )
    run = AutonomousResearchRun.from_yaml(
        campaign_path,
        data_paths=write_data_paths(tmp_path),
        output_root=tmp_path / "run",
    )
    engine = AutonomousResearchEngine(repo_root=Path.cwd())

    trials = engine._generated_trials(
        run,
        "generation-000",
        0,
        proposal=None,
    )

    pipeline = dict(trials[0]["backtest_pipeline"])
    assert pipeline["strategy_parameter_defaults"] == {
        "symbol": "GC",
        "target_quantity": "1",
    }
    assert pipeline["strategy_parameter_map"] == {"lookback": "vwap_slope_lookback"}
    config_payload = yaml.safe_load(
        Path(pipeline["backtest_config_path"]).read_text(encoding="utf-8")
    )
    assert config_payload["strategy_params"] == {"symbol": "GC", "target_quantity": "1"}


def write_campaign(
    tmp_path: Path,
    *,
    families: tuple[str, ...] = ("momentum", "breakout"),
    max_generations: int = 1,
    max_trials_per_generation: int = 3,
    max_total_trials: int = 6,
    max_family_trials: int | None = None,
    compute_budget_limit: int | None = None,
    active_correlation: float = 0.30,
    data_mode: str = "fixture",
    max_rows: int | None = 50,
    template_extra_lines: tuple[str, ...] = (),
) -> Path:
    config_dir = tmp_path / "campaign_inputs"
    config_dir.mkdir(parents=True, exist_ok=True)
    resolved_max_family_trials = (
        max_total_trials if max_family_trials is None else max_family_trials
    )
    family_rows: list[str] = []
    for family in families:
        search_path = config_dir / f"{family}_search.yaml"
        template_path = config_dir / f"{family}_template.yaml"
        search_path.write_text(
            "\n".join(
                [
                    "parameters:",
                    "  - name: root",
                    "    parameter_type: categorical",
                    "    values: [GC]",
                    "  - name: lookback",
                    "    parameter_type: int_range",
                    "    minimum: 5",
                    "    maximum: 15",
                    "    step: 5",
                    "  - name: threshold",
                    "    parameter_type: categorical",
                    "    values: [0.1]",
                    "  - name: active_correlation",
                    "    parameter_type: categorical",
                    f"    values: [{active_correlation}]",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        template_path.write_text(
            "\n".join(
                [
                    f"template_id: {family}_template",
                    f"family: {family}",
                    "strategy_entrypoint: examples.strategies.gc_si_momentum:GcSiMomentumStrategy",
                    "allowed_imports: [qts.strategy_sdk]",
                    "risk_assumptions:",
                    "  max_position_notional: 100000",
                    "execution_assumptions:",
                    "  slippage_bps: 1",
                    *template_extra_lines,
                    "factor_definition:",
                    f"  factor_id: {family}_factor",
                    "  family: momentum",
                    "  inputs:",
                    "    - root: GC",
                    "      field: close",
                    "  transforms:",
                    "    - type: returns",
                    "      lookback: 5",
                    "  label_policy:",
                    "    horizon_bars: 5",
                    "    visible_after: bar_close",
                    "    no_lookahead: true",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        family_rows.extend(
            [
                f"  - id: {family}",
                f"    template: {family}",
                f"    manifest_template: {template_path}",
                f"    search_space: {search_path}",
            ]
        )
    campaign_path = config_dir / "campaign.yaml"
    campaign_path.write_text(
        "\n".join(
            [
                "campaign_id: engine_campaign",
                "owner: research",
                'created_at: "2026-05-27T00:00:00+00:00"',
                "universe:",
                "  roots: [GC]",
                "  asset_class: futures",
                "  calendar: CME",
                "  timeframe: 1m",
                "  dataset_id: research_gc",
                "families:",
                *family_rows,
                "execution:",
                "  default_mode: backtest_pipeline",
                "  metrics_source: backtest_artifacts",
                f"  data_mode: {data_mode}",
                *([] if max_rows is None else [f"  max_rows: {max_rows}"]),
                "objective:",
                "  primary: composite_score",
                "  components:",
                "    sharpe: 1.0",
                "constraints:",
                "  min_oos_months: 12",
                "  min_oos_trade_count: 1",
                "  min_profit_factor: 1.15",
                "  max_drawdown: 0.25",
                "  max_cost_impact: 0.25",
                "  max_correlation_to_active: 0.50",
                "budget:",
                f"  max_generations: {max_generations}",
                f"  max_trials_per_generation: {max_trials_per_generation}",
                f"  max_total_trials: {max_total_trials}",
                f"  max_family_trials: {resolved_max_family_trials}",
                "  wall_clock_limit_minutes: 30",
                *(
                    []
                    if compute_budget_limit is None
                    else [f"  compute_budget_limit: {compute_budget_limit}"]
                ),
                "",
            ]
        ),
        encoding="utf-8",
    )
    return campaign_path


def write_data_paths(tmp_path: Path) -> dict[str, Path]:
    data_path = tmp_path / "gc.csv"
    data_path.write_text(
        "\n".join(
            ["timestamp,close"]
            + [
                f"2026-01-02T00:{minute:02d}:00+00:00,{100 + (minute * 0.5):.1f}"
                for minute in range(20)
            ]
            + [""]
        ),
        encoding="utf-8",
    )
    return {"GC": data_path}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
