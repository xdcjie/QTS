from __future__ import annotations

import json
from pathlib import Path
from typing import Any

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
    generation_rows = read_jsonl(result.generations[0].landscape_path)
    assert {row["parameters"]["lookback"] for row in generation_rows} <= {5, 10, 15}
    assert all(row["candidate_space_hash"].startswith("sha256:") for row in generation_rows)
    assert all(row["strategy_variant_hash"].startswith("sha256:") for row in generation_rows)
    assert all(row["factor_hash"].startswith("sha256:") for row in generation_rows)
    assert all(row["trial_id"].startswith("generation-000-trial-") for row in generation_rows)


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
