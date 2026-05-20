from __future__ import annotations

import json
from pathlib import Path

import pytest
from qts.research import ResearchSession, ResearchSessionConfig
from qts.research.factor_discovery import FactorDiscoveryQuery, FactorDiscoveryResult, FactorIdea
from qts.research.factor_spec import FactorSpec, FactorSpecDrafter, FactorSpecSourceRef


def _idea() -> FactorIdea:
    return FactorIdea(
        idea_id="openalex:W123",
        source="openalex",
        external_id="W123",
        title="Momentum and carry signals in commodity futures",
        abstract="A term structure carry factor combined with trend-following momentum.",
        url="https://openalex.org/W123",
        year=2026,
        authors=("A. Researcher",),
        citation_count=42,
    )


def test_factor_spec_drafter_maps_momentum_carry_idea_to_reviewable_spec() -> None:
    spec = FactorSpecDrafter().draft(_idea())

    assert spec.name == "momentum-carry-signals-in-commodity-futures"
    assert spec.review_status == "draft"
    assert spec.promotion_gate == "human_review_required"
    assert spec.candidate_tags == ("momentum", "carry")
    assert spec.inputs == ("close", "contract_chain", "roll_yield")
    assert spec.expected_direction == "higher_score_higher_expected_return"
    assert spec.lookback == "researcher_defined"
    assert spec.universe == "research_session_universe"
    assert spec.rebalance == "researcher_defined"
    assert "human review required" in spec.notes
    assert "Momentum and carry signals" in spec.hypothesis


def test_factor_spec_to_payload_is_deterministic() -> None:
    spec = FactorSpecDrafter().draft(_idea())

    payload = spec.to_payload()

    assert json.dumps(payload, sort_keys=True)
    assert payload["source_refs"] == [
        {
            "external_id": "W123",
            "source": "openalex",
            "title": "Momentum and carry signals in commodity futures",
            "url": "https://openalex.org/W123",
            "year": 2026,
        }
    ]


def test_factor_spec_rejects_empty_required_fields() -> None:
    with pytest.raises(ValueError, match="name is required"):
        FactorSpec(
            name=" ",
            hypothesis="hypothesis",
            inputs=("close",),
            lookback="researcher_defined",
            universe="research_session_universe",
            rebalance="researcher_defined",
            expected_direction="unknown",
            data_requirements=("historical bars",),
            source_refs=(
                FactorSpecSourceRef(
                    source="openalex",
                    external_id="W123",
                    title="Paper",
                    url="https://openalex.org/W123",
                    year=2026,
                ),
            ),
            candidate_tags=("momentum",),
            notes=("human review required",),
        )


def test_factor_spec_rejects_blank_inputs_after_normalization() -> None:
    with pytest.raises(ValueError, match="inputs must not be empty"):
        FactorSpec(
            name="momentum",
            hypothesis="hypothesis",
            inputs=(" ",),
            lookback="researcher_defined",
            universe="research_session_universe",
            rebalance="researcher_defined",
            expected_direction="unknown",
            data_requirements=("historical bars",),
            source_refs=(
                FactorSpecSourceRef(
                    source="openalex",
                    external_id="W123",
                    title="Paper",
                    url="https://openalex.org/W123",
                    year=2026,
                ),
            ),
            candidate_tags=("momentum",),
            notes=("human review required",),
        )


def test_factor_spec_drafter_preserves_source_reference() -> None:
    spec = FactorSpecDrafter().draft(_idea())

    assert spec.source_refs == (
        FactorSpecSourceRef(
            source="openalex",
            external_id="W123",
            title="Momentum and carry signals in commodity futures",
            url="https://openalex.org/W123",
            year=2026,
        ),
    )


def _session(tmp_path: Path) -> ResearchSession:
    data_config = tmp_path / "historical.local.yaml"
    data_config.write_text("historical_data: {}\n", encoding="utf-8")
    backtest_config = tmp_path / "backtest.yaml"
    backtest_config.write_text("mode: backtest\n", encoding="utf-8")
    config_path = tmp_path / "research.yaml"
    config_path.write_text(
        f"""
data:
  config: {data_config}
  catalog: research_futures
  roots: [GC]
  timeframe: 1m
backtest_config: {backtest_config}
store: research-store
output_root: research-runs
""",
        encoding="utf-8",
    )
    return ResearchSession(ResearchSessionConfig.from_yaml(config_path))


def test_research_session_drafts_single_factor_spec(tmp_path: Path) -> None:
    spec = _session(tmp_path).draft_factor_spec(_idea())

    assert spec.name == "momentum-carry-signals-in-commodity-futures"
    assert spec.source_refs[0].source == "openalex"


def test_research_session_drafts_specs_from_discovery_result(tmp_path: Path) -> None:
    result = FactorDiscoveryResult(
        query=FactorDiscoveryQuery(text="commodity futures momentum"),
        ideas=(_idea(),),
    )

    specs = _session(tmp_path).draft_factor_specs(result)

    assert [spec.name for spec in specs] == ["momentum-carry-signals-in-commodity-futures"]


def test_factor_spec_public_exports_are_available() -> None:
    from qts.research import FactorSpec as ExportedFactorSpec
    from qts.research import FactorSpecDrafter as ExportedFactorSpecDrafter

    assert ExportedFactorSpec is FactorSpec
    assert ExportedFactorSpecDrafter is FactorSpecDrafter
