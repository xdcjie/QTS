from __future__ import annotations

from pathlib import Path

import pytest
from qts.research.engine.autonomous_research_engine import (
    AutonomousResearchEngine,
    AutonomousResearchRun,
)

from tests.integration.research._autonomous_engine_plan_helpers import (
    read_jsonl,
    write_campaign,
    write_data_paths,
)


def test_engine_uses_search_space_candidates_and_writes_parameters(
    tmp_path: Path,
) -> None:
    campaign_path = write_campaign(
        tmp_path,
        families=("momentum",),
        max_trials_per_generation=4,
        max_total_trials=4,
    )
    search_path = tmp_path / "campaign_inputs" / "momentum_search.yaml"
    search_path.write_text(
        "\n".join(
            [
                "parameters:",
                "  - name: root",
                "    parameter_type: categorical",
                "    values: [GC]",
                "  - name: lookback",
                "    parameter_type: categorical",
                "    values: [5, 10]",
                "  - name: use_regime",
                "    parameter_type: boolean",
                "  - name: regime_threshold",
                "    parameter_type: categorical",
                "    values: [0.1, 0.2]",
                "constraints:",
                "  - constraint_type: conditional",
                "    parameter: regime_threshold",
                "    when:",
                "      use_regime: true",
                "  - constraint_type: forbidden_combination",
                "    values:",
                "      use_regime: true",
                "      regime_threshold: 0.2",
                "",
            ]
        ),
        encoding="utf-8",
    )
    data_paths = write_data_paths(tmp_path)
    first_run = AutonomousResearchRun.from_yaml(
        campaign_path,
        data_paths=data_paths,
        output_root=tmp_path / "run-a",
    )
    second_run = AutonomousResearchRun.from_yaml(
        campaign_path,
        data_paths=data_paths,
        output_root=tmp_path / "run-b",
    )

    first = AutonomousResearchEngine(repo_root=Path.cwd()).run(first_run)
    second = AutonomousResearchEngine(repo_root=Path.cwd()).run(second_run)

    first_rows = read_jsonl(first.output_root / "candidate_parameters.jsonl")
    second_rows = read_jsonl(second.output_root / "candidate_parameters.jsonl")
    assert first_rows == second_rows
    parameter_rows = [row["parameters"] for row in first_rows]
    assert any(
        row["use_regime"] is False and "regime_threshold" not in row for row in parameter_rows
    )
    assert not any(
        row["use_regime"] is True and row.get("regime_threshold") == 0.2 for row in parameter_rows
    )
    assert read_jsonl(first.output_root / "generation-000" / "candidate_parameters.jsonl")


def test_engine_fails_when_campaign_search_space_is_missing(tmp_path: Path) -> None:
    campaign_path = write_campaign(tmp_path, families=("momentum",))
    (tmp_path / "campaign_inputs" / "momentum_search.yaml").unlink()
    run = AutonomousResearchRun.from_yaml(
        campaign_path,
        data_paths=write_data_paths(tmp_path),
        output_root=tmp_path / "run",
    )

    with pytest.raises(FileNotFoundError, match="search-space config not found"):
        AutonomousResearchEngine(repo_root=Path.cwd()).run(run)
