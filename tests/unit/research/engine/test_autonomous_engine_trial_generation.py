from __future__ import annotations

import json
from collections.abc import Callable
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
import qts.research.engine.autonomous_engine_helpers as engine_helpers
import qts.research.engine.autonomous_engine_orchestration as engine_orchestration
import yaml  # type: ignore[import-untyped]
from qts.backtest.pipeline import BacktestPipeline
from qts.core.ids import InstrumentId
from qts.data.historical.csv_index import write_historical_csv_index
from qts.research.engine.autonomous_research_engine import (
    AutonomousResearchEngine,
    AutonomousResearchRun,
)

from tests.support.research_provenance import (
    force_clean_reproducibility as force_clean_reproducibility,
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


def test_engine_selection_policy_uses_campaign_profit_factor_constraint(tmp_path: Path) -> None:
    campaign_path = write_campaign(tmp_path)
    run = AutonomousResearchRun.from_yaml(
        campaign_path,
        data_paths=write_data_paths(tmp_path),
        output_root=tmp_path / "run",
    )
    engine = AutonomousResearchEngine(repo_root=Path.cwd())

    policy = engine._support._selection_policy(run)

    assert policy.min_profit_factor == 1.15
    assert policy.profit_factor_metric == "quality.profit_factor"


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

    fixture_target = tmp_path / "fixture.csv"
    engine_helpers._materialize_backtest_csv(source, fixture_target, symbol="GC", max_rows=10)
    assert len(fixture_target.read_text(encoding="utf-8").splitlines()) == 11

    full_target = tmp_path / "full.csv"
    engine_helpers._materialize_backtest_csv(source, full_target, symbol="GC", max_rows=None)
    assert len(full_target.read_text(encoding="utf-8").splitlines()) == 61

    window_target = tmp_path / "window.csv"
    engine_helpers._materialize_backtest_csv(
        source,
        window_target,
        symbol="GC",
        max_rows=None,
        window=("2026-01-02T00:10:00+00:00", "2026-01-02T00:20:00+00:00"),
    )
    assert len(window_target.read_text(encoding="utf-8").splitlines()) == 11


def test_full_backtest_data_materialization_uses_daily_index_for_window_start(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source.csv"
    source.write_text(
        "\n".join(
            ["timestamp,close"]
            + [f"2026-01-02T00:{minute:02d}:00+00:00,{100 + minute:.1f}" for minute in range(60)]
            + [
                "2026-01-03T00:00:00+00:00,200.0",
                "2026-01-03T00:01:00+00:00,201.0",
                "2026-01-03T00:02:00+00:00,202.0",
                "",
            ]
        ),
        encoding="utf-8",
    )
    write_historical_csv_index(source, timestamp_column="timestamp")
    parsed_timestamps: list[str] = []
    original_parse_timestamp = engine_helpers._parse_timestamp

    def counted_parse_timestamp(value: str) -> datetime:
        parsed_timestamps.append(value)
        return original_parse_timestamp(value)

    monkeypatch.setattr(engine_helpers, "_parse_timestamp", counted_parse_timestamp)

    target = tmp_path / "window.csv"
    engine_helpers._materialize_backtest_csv(
        source,
        target,
        symbol="SI",
        max_rows=None,
        window=("2026-01-03T00:01:00+00:00", "2026-01-03T00:03:00+00:00"),
    )

    assert len(target.read_text(encoding="utf-8").splitlines()) == 3
    assert all(not timestamp.startswith("2026-01-02") for timestamp in parsed_timestamps)


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
    original = engine_helpers._materialize_backtest_csv

    def counted_materialize(
        source_path: Path,
        target_path: Path,
        *,
        symbol: str,
        max_rows: int | None,
        window: tuple[str, str] | None = None,
        windows: tuple[tuple[str, str], ...] = (),
        contract_symbol_for: Callable[[datetime], str] | None = None,
    ) -> None:
        calls.append(target_path)
        original(
            source_path,
            target_path,
            symbol=symbol,
            max_rows=max_rows,
            window=window,
            windows=windows,
            contract_symbol_for=contract_symbol_for,
        )

    monkeypatch.setattr(engine_orchestration, "_materialize_backtest_csv", counted_materialize)
    monkeypatch.setattr(engine_helpers, "_materialize_backtest_csv", counted_materialize)

    _first_config, first_csv = engine_orchestration._write_backtest_data_config(
        engine._support,
        run=run,
        trial_id="generation-000-trial-000",
        root="GC",
        data_path=data_paths["GC"],
    )
    _second_config, second_csv = engine_orchestration._write_backtest_data_config(
        engine._support,
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

    payload = engine_orchestration._backtest_pipeline_payload(
        engine._support,
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


def test_backtest_pipeline_template_can_reuse_base_config_path(tmp_path: Path) -> None:
    campaign_path = write_campaign(tmp_path, families=("momentum",))
    run = AutonomousResearchRun.from_yaml(
        campaign_path,
        data_paths=write_data_paths(tmp_path),
        output_root=tmp_path / "run",
    )
    engine = AutonomousResearchEngine(repo_root=Path.cwd())

    payload = engine_orchestration._backtest_pipeline_payload(
        engine._support,
        run=run,
        trial_id="generation-000-trial-000",
        root="GC",
        parameters={
            "root": "GC",
            "cot_lookback_bars": 20,
            "entry_z": "0.75",
        },
        strategy_entrypoint=(
            "strategies.research.precious_metal_cot_positioning:PreciousMetalCotPositioningStrategy"
        ),
        manifest_patch={
            "backtest_pipeline": {
                "base_config_path": "configs/backtest.precious_metal_vix_risk_gc.yaml",
                "data_quality_paths": ["historical/data/vix.csv"],
                "strategy_parameter_defaults": {
                    "allow_short": False,
                    "cot_symbol": "VIX",
                    "positioning_direction": "follow",
                    "signal_mode": "change",
                    "target_quantity": "1",
                    "trade_symbol": "GC",
                },
                "strategy_parameter_names": ["cot_lookback_bars", "entry_z"],
            }
        },
    )

    assert payload["base_config_path"] == "configs/backtest.precious_metal_vix_risk_gc.yaml"
    assert "backtest_config_path" not in payload
    assert payload["data_quality_paths"] == ("historical/data/vix.csv",)
    assert payload["strategy_parameter_defaults"]["cot_symbol"] == "VIX"
    assert payload["strategy_parameter_names"] == ("cot_lookback_bars", "entry_z")


def test_generated_trials_use_template_backtest_pipeline_mapping(tmp_path: Path) -> None:
    campaign_path = write_campaign(
        tmp_path,
        families=("momentum",),
        template_extra_lines=(
            "backtest_pipeline:",
            "  root_strategy_parameter: symbol",
            "  strategy_parameter_defaults:",
            '    target_quantity: "1"',
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

    trials = engine_orchestration._generated_trials(
        engine._support,
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


def test_autonomous_future_backtest_config_preserves_chain_and_contract_symbols(
    tmp_path: Path,
) -> None:
    campaign_path = write_campaign(
        tmp_path,
        data_mode="full",
        max_rows=None,
        template_extra_lines=(
            "backtest_pipeline:",
            "  root_strategy_parameter: symbol",
            "  strategy_parameter_defaults:",
            '    target_quantity: "1"',
            "  strategy_parameter_map:",
            "    lookback: vwap_slope_lookback",
        ),
    )
    data_paths = write_future_ohlcv_data_paths(tmp_path)
    run = AutonomousResearchRun.from_yaml(
        campaign_path,
        data_paths=data_paths,
        output_root=tmp_path / "run",
    )
    engine = AutonomousResearchEngine(repo_root=Path.cwd())

    payload = engine_orchestration._backtest_pipeline_payload(
        engine._support,
        run=run,
        trial_id="generation-000-trial-000",
        root="GC",
        parameters={"root": "GC", "lookback": 5},
        strategy_entrypoint="strategies.research.vwap_factor_research:VwapFactorResearchStrategy",
        manifest_patch={
            "backtest_pipeline": {
                "root_strategy_parameter": "symbol",
                "strategy_parameter_defaults": {"target_quantity": "1"},
                "strategy_parameter_map": {"lookback": "vwap_slope_lookback"},
            }
        },
    )

    backtest_config = yaml.safe_load(
        Path(payload["backtest_config_path"]).read_text(encoding="utf-8")
    )
    data_config_path = Path(backtest_config["market_data"]["config"])
    data_config = yaml.safe_load(data_config_path.read_text(encoding="utf-8"))
    materialized_csv = data_config_path.parent / "data" / "GC.csv"
    first_data_row = materialized_csv.read_text(encoding="utf-8").splitlines()[1]
    _first_timestamp, *_fields, materialized_symbol = first_data_row.split(",")

    assert "instrument_ids" not in backtest_config
    assert backtest_config["roll_policy"] == {"enabled": True}
    assert (
        data_config["historical_data"]["catalogs"]["research"]["datasets"]["GC"]["chain_file"]
        == "GC.json"
    )
    assert (data_config_path.parent / "chains" / "GC.json").is_file()
    assert materialized_symbol == "GCQ0"

    pipeline = BacktestPipeline.from_yaml(Path(payload["backtest_config_path"]))
    _engine, inputs = pipeline.build_engine()
    assert inputs.contract_multipliers[InstrumentId("FUTURE.CME.GC.GCQ0")] == Decimal("100.0")


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
    min_oos_months: int = 1,
    template_extra_lines: tuple[str, ...] = (),
    fill_policy: str = "next_bar_open",
    optimistic_fill_waiver: bool = False,
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
                f"  fill_policy: {fill_policy}",
                # same_bar_close is optimistic look-ahead and requires an
                # explicit waiver; toy fixtures opt into it for their economics.
                *(
                    ["  optimistic_fill_waiver: true"]
                    if optimistic_fill_waiver or fill_policy == "same_bar_close"
                    else []
                ),
                f"  data_mode: {data_mode}",
                *([] if max_rows is None else [f"  max_rows: {max_rows}"]),
                "objective:",
                "  primary: composite_score",
                "  components:",
                "    sharpe: 1.0",
                "constraints:",
                f"  min_oos_months: {min_oos_months}",
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
                f"2026-01-02T00:{minute:02d}:00+00:00,{price:.1f}"
                for minute, price in enumerate(_profit_factor_fixture_prices(100))
            ]
            + [""]
        ),
        encoding="utf-8",
    )
    return {"GC": data_path}


def _multi_month_fixture_csv(*, base: int, minutes: int = 92000) -> str:
    """Build a multi-month 1m fixture as a contiguous repeating profitable cycle.

    The bars are emitted as an unbroken 1-minute series so the data-quality gap
    check sees no missing bars, while the ~2.1-month span crosses a futures
    contract roll. Repeating the same profitable cycle gives the walk-forward
    train and out-of-sample halves matching profitable cycles, so the
    honestly-derived oos_months clears the 1-month intraday promotion bar and
    walk-forward consistency stays positive.
    """
    from datetime import UTC, datetime, timedelta

    cycle = _profit_factor_fixture_prices(base)
    start = datetime(2026, 1, 5, tzinfo=UTC)
    rows = ["timestamp,close"]
    rows.extend(
        f"{(start + timedelta(minutes=offset)).isoformat()},{cycle[offset % len(cycle)]:.1f}"
        for offset in range(minutes)
    )
    rows.append("")
    return "\n".join(rows)


def write_future_ohlcv_data_paths(tmp_path: Path) -> dict[str, Path]:
    data_path = tmp_path / "gc_ohlcv.csv"
    data_path.write_text(
        "\n".join(
            [
                "ts_event,rtype,publisher_id,instrument_id,open,high,low,close,volume,symbol",
                "2010-06-06T22:00:00.000000000Z,33,1,104313,1221.1,1221.8,1221.1,1221.6,74,GCQ0",
                "2010-06-06T22:01:00.000000000Z,33,1,104314,1221.6,1221.9,1221.4,1221.7,80,GCQ0",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return {"GC": data_path}


def _profit_factor_fixture_prices(base: int) -> tuple[int, ...]:
    return (
        *((base,) * 15),
        base + 1,
        base,
        base - 1,
        *((base - 1,) * 15),
        base,
        base + 3,
        base + 6,
        base + 9,
        base + 12,
        base + 8,
        base + 4,
        *((base + 4,) * 10),
    )


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
