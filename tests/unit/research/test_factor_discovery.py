from __future__ import annotations

from pathlib import Path

import pytest
from qts.research.factor_discovery import (
    ArxivFactorIdeaSource,
    CrossrefFactorIdeaSource,
    FactorDiscovery,
    FactorDiscoveryQuery,
    FactorDiscoveryResult,
    FactorIdea,
    FactorIdeaStore,
    OpenAlexFactorIdeaSource,
    SemanticScholarFactorIdeaSource,
)


class _CountingSource:
    name = "fixture"

    def __init__(self, ideas: tuple[FactorIdea, ...]) -> None:
        self.calls = 0
        self._ideas = ideas

    def search(self, query: FactorDiscoveryQuery) -> tuple[FactorIdea, ...]:
        self.calls += 1
        return self._ideas


def _idea(
    *,
    idea_id: str = "fixture:momentum",
    source: str = "fixture",
    title: str = "Momentum and reversal effects in futures",
    abstract: str = "A momentum signal with volatility controls and reversal filters.",
) -> FactorIdea:
    return FactorIdea(
        idea_id=idea_id,
        source=source,
        external_id=idea_id,
        title=title,
        abstract=abstract,
        url="https://example.test/paper",
        year=2026,
        authors=("A. Researcher",),
        citation_count=12,
    )


def test_factor_discovery_query_validates_inputs() -> None:
    query = FactorDiscoveryQuery(
        text=" futures momentum ",
        sources=("OpenAlex", "semantic_scholar"),
        max_results=5,
        from_year=2020,
        to_year=2026,
    )

    assert query.text == "futures momentum"
    assert query.sources == ("openalex", "semantic_scholar")
    assert query.max_results == 5

    with pytest.raises(ValueError, match="query text is required"):
        FactorDiscoveryQuery(text=" ")
    with pytest.raises(ValueError, match="max_results must be positive"):
        FactorDiscoveryQuery(text="momentum", max_results=0)
    with pytest.raises(ValueError, match="from_year must be <= to_year"):
        FactorDiscoveryQuery(text="momentum", from_year=2026, to_year=2020)


def test_factor_discovery_public_exports_are_available() -> None:
    from qts.research import FactorDiscovery as ExportedFactorDiscovery
    from qts.research import FactorIdea as ExportedFactorIdea

    assert ExportedFactorDiscovery is FactorDiscovery
    assert ExportedFactorIdea is FactorIdea


def test_factor_idea_infers_candidate_tags_from_title_and_abstract() -> None:
    idea = _idea()

    assert idea.candidate_tags == ("momentum", "reversal", "volatility")


def test_factor_idea_infers_regime_volume_and_order_flow_tags() -> None:
    idea = _idea(
        title="Regime switching VWAP strategy from order flow imbalance",
        abstract="A volume curve filter separates high volatility market states.",
    )

    assert idea.candidate_tags == (
        "volatility",
        "liquidity",
        "volume",
        "order_flow",
        "regime",
    )


def test_factor_idea_store_round_trips_cached_search(tmp_path: Path) -> None:
    store = FactorIdeaStore(tmp_path / "research-store")
    query = FactorDiscoveryQuery(text="intraday futures momentum", max_results=3)
    result = FactorDiscoveryResult(query=query, ideas=(_idea(),))

    stored = store.save_search(result)
    loaded = store.load_search(query)

    assert stored.cache_path == store.cache_path(query)
    assert loaded is not None
    assert loaded.cached is True
    assert loaded.cache_path == store.cache_path(query)
    assert loaded.ideas == (_idea(),)


def test_factor_discovery_uses_cache_without_calling_sources(tmp_path: Path) -> None:
    query = FactorDiscoveryQuery(text="intraday futures momentum", sources=("fixture",))
    store = FactorIdeaStore(tmp_path / "research-store")
    store.save_search(FactorDiscoveryResult(query=query, ideas=(_idea(),)))
    source = _CountingSource((_idea(idea_id="fixture:new"),))
    discovery = FactorDiscovery(store=store, sources={"fixture": source})

    result = discovery.search(query.text, sources=("fixture",))

    assert result.cached is True
    assert source.calls == 0
    assert result.ideas == (_idea(),)


def test_factor_discovery_deduplicates_ideas_across_sources(tmp_path: Path) -> None:
    duplicate = _idea(idea_id="shared:paper", source="source_a")
    duplicate_from_other_source = _idea(idea_id="shared:paper", source="source_b")
    unique = _idea(idea_id="source_b:unique", source="source_b")
    discovery = FactorDiscovery(
        store=FactorIdeaStore(tmp_path / "research-store"),
        sources={
            "source_a": _CountingSource((duplicate,)),
            "source_b": _CountingSource((duplicate_from_other_source, unique)),
        },
    )

    result = discovery.search("futures momentum", sources=("source_a", "source_b"))

    assert [idea.idea_id for idea in result.ideas] == ["shared:paper", "source_b:unique"]
    assert result.cached is False


def test_factor_discovery_filters_non_trading_results_for_market_queries(
    tmp_path: Path,
) -> None:
    relevant = _idea(
        idea_id="fixture:vwap",
        title="VWAP execution with order flow imbalance in futures markets",
    )
    irrelevant = _idea(
        idea_id="fixture:lung-screening",
        title="Reduced lung cancer mortality with volume CT screening",
    )
    discovery = FactorDiscovery(
        store=FactorIdeaStore(tmp_path / "research-store"),
        sources={"fixture": _CountingSource((irrelevant, relevant))},
    )

    result = discovery.search(
        "VWAP intraday futures market microstructure order flow",
        sources=("fixture",),
        max_results=5,
    )

    assert [idea.idea_id for idea in result.ideas] == ["fixture:vwap"]


def test_factor_discovery_caps_results_after_relevance_ranking(tmp_path: Path) -> None:
    precise = _idea(
        idea_id="fixture:vwap",
        title="VWAP intraday futures alpha from order flow imbalance",
    )
    broad = _idea(
        idea_id="fixture:volume",
        title="Volume curve seasonality in commodity futures",
    )
    weak = _idea(
        idea_id="fixture:momentum",
        title="Momentum and volatility timing in futures",
    )
    discovery = FactorDiscovery(
        store=FactorIdeaStore(tmp_path / "research-store"),
        sources={"fixture": _CountingSource((weak, broad, precise))},
    )

    result = discovery.search(
        "VWAP intraday futures order flow",
        sources=("fixture",),
        max_results=2,
    )

    assert [idea.idea_id for idea in result.ideas] == ["fixture:vwap", "fixture:volume"]


def test_factor_discovery_excludes_retracted_market_papers(tmp_path: Path) -> None:
    retracted = _idea(
        idea_id="fixture:retracted",
        title="RETRACTED: Trading volume and predictability in commodity futures",
    )
    active = _idea(
        idea_id="fixture:active",
        title="Order flow imbalance and intraday futures returns",
    )
    discovery = FactorDiscovery(
        store=FactorIdeaStore(tmp_path / "research-store"),
        sources={"fixture": _CountingSource((retracted, active))},
    )

    result = discovery.search(
        "VWAP intraday futures order flow",
        sources=("fixture",),
        max_results=5,
    )

    assert [idea.idea_id for idea in result.ideas] == ["fixture:active"]


class _FakeHttpClient:
    def __init__(self, text: str) -> None:
        self.text = text
        self.calls: list[tuple[str, dict[str, str], dict[str, str]]] = []

    def get_text(
        self,
        url: str,
        *,
        params: dict[str, str],
        headers: dict[str, str] | None = None,
    ) -> str:
        self.calls.append((url, params, {} if headers is None else headers))
        return self.text


def test_semantic_scholar_source_parses_paper_results() -> None:
    http = _FakeHttpClient(
        """
        {
          "data": [
            {
              "paperId": "S2-1",
              "title": "Momentum and volatility timing in futures",
              "abstract": "A trend-following factor with volatility controls.",
              "year": 2024,
              "url": "https://semanticscholar.org/paper/S2-1",
              "citationCount": 42,
              "authors": [{"name": "Jane Researcher"}],
              "externalIds": {"DOI": "10.1000/ssrn.1"}
            }
          ]
        }
        """
    )
    source = SemanticScholarFactorIdeaSource(http_client=http)

    ideas = source.search(FactorDiscoveryQuery(text="futures momentum", max_results=2))

    assert http.calls[0][0] == "https://api.semanticscholar.org/graph/v1/paper/search"
    assert http.calls[0][1]["query"] == "futures momentum"
    assert http.calls[0][1]["limit"] == "2"
    assert ideas == (
        FactorIdea(
            idea_id="semantic_scholar:S2-1",
            source="semantic_scholar",
            external_id="S2-1",
            title="Momentum and volatility timing in futures",
            abstract="A trend-following factor with volatility controls.",
            url="https://semanticscholar.org/paper/S2-1",
            year=2024,
            authors=("Jane Researcher",),
            citation_count=42,
        ),
    )


def test_openalex_source_parses_abstract_inverted_index() -> None:
    http = _FakeHttpClient(
        """
        {
          "results": [
            {
              "id": "https://openalex.org/W123",
              "display_name": "Carry signals in commodity futures",
              "abstract_inverted_index": {"Carry": [0], "term": [1], "structure": [2]},
              "publication_year": 2023,
              "cited_by_count": 7,
              "doi": "https://doi.org/10.1000/openalex.1",
              "authorships": [{"author": {"display_name": "Alex Author"}}]
            }
          ]
        }
        """
    )
    source = OpenAlexFactorIdeaSource(http_client=http)

    ideas = source.search(FactorDiscoveryQuery(text="commodity carry", max_results=1))

    assert http.calls[0][0] == "https://api.openalex.org/works"
    assert http.calls[0][1]["search"] == "commodity carry"
    assert ideas[0].idea_id == "openalex:W123"
    assert ideas[0].abstract == "Carry term structure"
    assert ideas[0].candidate_tags == ("carry",)


def test_crossref_source_parses_work_items() -> None:
    http = _FakeHttpClient(
        """
        {
          "message": {
            "items": [
              {
                "DOI": "10.1000/crossref.1",
                "title": ["Mean reversion after liquidity shocks"],
                "abstract": "<jats:p>A reversal factor using bid-ask spread pressure.</jats:p>",
                "published-print": {"date-parts": [[2022]]},
                "is-referenced-by-count": 5,
                "URL": "https://doi.org/10.1000/crossref.1",
                "author": [{"given": "Casey", "family": "Scholar"}]
              }
            ]
          }
        }
        """
    )
    source = CrossrefFactorIdeaSource(http_client=http)

    ideas = source.search(FactorDiscoveryQuery(text="liquidity reversal", max_results=1))

    assert http.calls[0][0] == "https://api.crossref.org/works"
    assert http.calls[0][1]["query.bibliographic"] == "liquidity reversal"
    assert ideas[0].idea_id == "crossref:10.1000/crossref.1"
    assert ideas[0].authors == ("Casey Scholar",)
    assert ideas[0].candidate_tags == ("reversal", "liquidity")


def test_arxiv_source_parses_atom_entries() -> None:
    http = _FakeHttpClient(
        """
        <feed xmlns="http://www.w3.org/2005/Atom">
          <entry>
            <id>http://arxiv.org/abs/2308.00016v1</id>
            <title>Alpha mining with sentiment and momentum factors</title>
            <summary>News sentiment improves momentum factor discovery.</summary>
            <published>2023-08-01T00:00:00Z</published>
            <author><name>Aria Quant</name></author>
            <link rel="alternate" href="http://arxiv.org/abs/2308.00016v1" />
          </entry>
        </feed>
        """
    )
    source = ArxivFactorIdeaSource(http_client=http)

    ideas = source.search(FactorDiscoveryQuery(text="alpha mining", max_results=1))

    assert http.calls[0][0] == "https://export.arxiv.org/api/query"
    assert http.calls[0][1]["search_query"] == "all:alpha mining"
    assert ideas[0].idea_id == "arxiv:2308.00016"
    assert ideas[0].year == 2023
    assert ideas[0].candidate_tags == ("momentum", "sentiment")
