"""Integration tests for ResearchSession factor discovery facade."""

from __future__ import annotations

from pathlib import Path

from qts.research import ResearchSession
from qts.research.factor_discovery import (
    FactorDiscovery,
    FactorDiscoveryQuery,
    FactorIdea,
    FactorIdeaStore,
)


class _CountingSource:
    name = "fixture"

    def __init__(self, ideas: tuple[FactorIdea, ...]) -> None:
        self.calls = 0
        self._ideas = ideas

    def search(self, query: FactorDiscoveryQuery) -> tuple[FactorIdea, ...]:
        self.calls += 1
        return self._ideas


def _write_research_session_config(tmp_path: Path) -> Path:
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
objective_metric: total_return
discovery:
  sources: [fixture]
  max_results: 3
""",
        encoding="utf-8",
    )
    return config_path


def _idea() -> FactorIdea:
    return FactorIdea(
        idea_id="fixture:momentum-carry",
        source="fixture",
        external_id="momentum-carry",
        title="Momentum and carry signals in commodity futures",
        abstract="A carry factor combined with trend-following momentum.",
        url="https://example.test/momentum-carry",
        year=2026,
        authors=("Researcher",),
        citation_count=10,
    )


def test_research_session_discover_factors_delegates_to_discovery_service(
    tmp_path: Path,
) -> None:
    source = _CountingSource((_idea(),))
    discovery = FactorDiscovery(
        store=FactorIdeaStore(tmp_path / "research-store"),
        sources={"fixture": source},
    )
    session = ResearchSession.from_yaml(_write_research_session_config(tmp_path))
    session = ResearchSession(session.config, discovery=discovery)

    result = session.discover_factors("commodity futures alpha")
    cached = session.discover_factors("commodity futures alpha")

    assert source.calls == 1
    assert result.cached is False
    assert cached.cached is True
    assert result.ideas == (_idea(),)
    assert (
        result.cache_path
        == tmp_path / "research-store" / "factor-ideas" / f"{result.query.query_id}.json"
    )


def test_research_session_discover_factors_frame_returns_dataframe(tmp_path: Path) -> None:
    discovery = FactorDiscovery(
        store=FactorIdeaStore(tmp_path / "research-store"),
        sources={"fixture": _CountingSource((_idea(),))},
    )
    session = ResearchSession.from_yaml(_write_research_session_config(tmp_path))
    session = ResearchSession(session.config, discovery=discovery)

    frame = session.discover_factors_frame("commodity futures alpha")

    assert list(frame["idea_id"]) == ["fixture:momentum-carry"]
    assert list(frame["candidate_tags"]) == ["momentum, carry"]


def test_research_session_find_factor_candidates_persists_specs(
    tmp_path: Path,
) -> None:
    discovery = FactorDiscovery(
        store=FactorIdeaStore(tmp_path / "research-store"),
        sources={"fixture": _CountingSource((_idea(),))},
    )
    session = ResearchSession.from_yaml(_write_research_session_config(tmp_path))
    session = ResearchSession(session.config, discovery=discovery)

    batch = session.find_factor_candidates("commodity futures alpha")

    assert [spec.name for spec in batch.specs] == ["momentum-carry-signals-in-commodity-futures"]
    assert (
        session.load_factor_spec("momentum-carry-signals-in-commodity-futures").review_status
        == "draft"
    )
