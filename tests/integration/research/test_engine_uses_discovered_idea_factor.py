from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import qts.research.engine.autonomous_engine_orchestration as engine_orchestration
from qts.research.engine.autonomous_research_engine import (
    AutonomousResearchEngine,
    AutonomousResearchRun,
)
from qts.research.factory.discovery_mapper import (
    FactorDefinitionDraftConstraints,
    FactorDiscoveryDraftMapper,
)
from qts.research.idea_spec import IdeaSpec

from tests.integration.research._autonomous_engine_plan_helpers import (
    read_jsonl,
    write_campaign,
    write_data_paths,
)

_IDEA_SPEC_TEMPLATE_LINES: tuple[str, ...] = (
    "factor_discovery:",
    "  idea_spec:",
    "    idea_id: paper:carry-term-structure",
    "    title: Term structure carry in futures markets",
    "    hypothesis: Roll yield and basis contain a carry premium.",
    "    edge_types: [carry]",
    "    source: semantic_scholar",
    '    created_at: "2026-05-27T00:00:00+00:00"',
)

_IDEA_SPEC = IdeaSpec(
    idea_id="paper:carry-term-structure",
    title="Term structure carry in futures markets",
    hypothesis="Roll yield and basis contain a carry premium.",
    edge_type="carry",
    edge_types=("carry",),
    source="semantic_scholar",
    created_at=datetime(2026, 5, 27, tzinfo=UTC),
)


def test_discovered_idea_drives_generated_candidate_factor_definition(tmp_path: Path) -> None:
    campaign_path = write_campaign(
        tmp_path,
        families=("momentum",),
        template_extra_lines=_IDEA_SPEC_TEMPLATE_LINES,
    )
    run = AutonomousResearchRun.from_yaml(
        campaign_path,
        data_paths=write_data_paths(tmp_path),
        output_root=tmp_path / "run",
    )

    trials = engine_orchestration._generated_trials(
        AutonomousResearchEngine(repo_root=Path.cwd())._support,
        run,
        "generation-000",
        0,
        proposal=None,
    )

    expected_draft = FactorDiscoveryDraftMapper(
        constraints=FactorDefinitionDraftConstraints(roots=run.universe)
    ).draft_from_idea_spec(_IDEA_SPEC)
    assert expected_draft.factor_definition is not None
    expected_factor_hash = expected_draft.factor_definition.factor_hash

    assert trials
    assert {trial["factor_hash"] for trial in trials} == {expected_factor_hash}
    assert all(
        trial["manifest_patch"]["research_factory"]["factor_hash"] == expected_factor_hash
        for trial in trials
    )


def test_unmappable_idea_falls_back_to_static_template_factor(tmp_path: Path) -> None:
    campaign_path = write_campaign(
        tmp_path,
        families=("momentum",),
        template_extra_lines=(
            "factor_discovery:",
            "  idea_spec:",
            "    idea_id: paper:sentiment-tone",
            "    title: News sentiment tone in commodity markets",
            "    hypothesis: Text embeddings may predict return dispersion.",
            "    edge_types: [sentiment]",
            "    source: arxiv",
            '    created_at: "2026-05-27T00:00:00+00:00"',
        ),
    )
    run = AutonomousResearchRun.from_yaml(
        campaign_path,
        data_paths=write_data_paths(tmp_path),
        output_root=tmp_path / "run",
    )
    engine = AutonomousResearchEngine(repo_root=Path.cwd())

    trials = engine_orchestration._generated_trials(
        engine._support, run, "generation-000", 0, proposal=None
    )

    no_discovery_campaign = write_campaign(tmp_path / "static", families=("momentum",))
    static_run = AutonomousResearchRun.from_yaml(
        no_discovery_campaign,
        data_paths=write_data_paths(tmp_path / "static"),
        output_root=tmp_path / "static" / "run",
    )
    static_trials = engine_orchestration._generated_trials(
        engine._support, static_run, "generation-000", 0, proposal=None
    )

    assert {trial["factor_hash"] for trial in trials} == {
        trial["factor_hash"] for trial in static_trials
    }


def test_full_campaign_run_records_discovered_idea_factor(tmp_path: Path) -> None:
    campaign_path = write_campaign(
        tmp_path,
        families=("momentum",),
        template_extra_lines=_IDEA_SPEC_TEMPLATE_LINES,
    )
    run = AutonomousResearchRun.from_yaml(
        campaign_path,
        data_paths=write_data_paths(tmp_path),
        output_root=tmp_path / "run",
    )

    result = AutonomousResearchEngine(repo_root=Path.cwd()).run(run)

    expected_draft = FactorDiscoveryDraftMapper(
        constraints=FactorDefinitionDraftConstraints(roots=run.universe)
    ).draft_from_idea_spec(_IDEA_SPEC)
    assert expected_draft.factor_definition is not None
    expected_factor_hash = expected_draft.factor_definition.factor_hash

    candidate_rows = read_jsonl(
        result.output_root / "generation-000" / "candidate_parameters.jsonl"
    )
    assert candidate_rows
    variant_payloads = read_jsonl(
        result.output_root / "generation-000" / "selection" / "candidate_results.jsonl"
    )
    assert variant_payloads
    landscape_rows = read_jsonl(result.fitness_landscape_path)
    assert {row["factor_family"] for row in landscape_rows} == {"momentum"}
    assert any(
        trial["factor_hash"] == expected_factor_hash
        for trial in engine_orchestration._generated_trials(
            AutonomousResearchEngine(repo_root=Path.cwd())._support,
            run,
            "generation-000",
            0,
            proposal=None,
        )
    )
