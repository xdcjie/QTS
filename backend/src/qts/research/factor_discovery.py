"""Research-only factor idea discovery from scholarly metadata sources."""

from __future__ import annotations

import hashlib
import html
import importlib
import json
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

DEFAULT_FACTOR_DISCOVERY_SOURCES = (
    "semantic_scholar",
    "openalex",
    "crossref",
    "arxiv",
)

_FACTOR_TAG_TERMS: dict[str, tuple[str, ...]] = {
    "momentum": ("momentum", "trend", "trend-following", "moving average"),
    "reversal": ("reversal", "mean reversion", "contrarian"),
    "volatility": ("volatility", "variance", "realized vol", "vix"),
    "carry": ("carry", "term structure", "roll yield", "basis"),
    "value": ("value", "valuation", "book-to-market"),
    "quality": ("quality", "profitability", "earnings quality"),
    "sentiment": ("sentiment", "news", "tone", "attention"),
    "liquidity": ("liquidity", "turnover", "bid-ask", "spread"),
    "seasonality": ("seasonality", "calendar", "month-of-year", "day-of-week"),
    "macro": ("macro", "inflation", "interest rate", "yield curve"),
}


@dataclass(frozen=True, slots=True)
class FactorDiscoveryQuery:
    """Validated scholarly search query for factor idea discovery."""

    text: str
    sources: tuple[str, ...] = DEFAULT_FACTOR_DISCOVERY_SOURCES
    max_results: int = 10
    from_year: int | None = None
    to_year: int | None = None

    def __post_init__(self) -> None:
        text = self.text.strip()
        if not text:
            raise ValueError("query text is required")
        sources = tuple(source.strip().lower() for source in self.sources if source.strip())
        if not sources:
            raise ValueError("sources must not be empty")
        if self.max_results <= 0:
            raise ValueError("max_results must be positive")
        if (
            self.from_year is not None
            and self.to_year is not None
            and self.from_year > self.to_year
        ):
            raise ValueError("from_year must be <= to_year")
        object.__setattr__(self, "text", text)
        object.__setattr__(self, "sources", sources)

    @property
    def query_id(self) -> str:
        """Return a deterministic cache key for this query."""

        payload = {
            "from_year": self.from_year,
            "max_results": self.max_results,
            "sources": list(self.sources),
            "text": self.text,
            "to_year": self.to_year,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()[:16]

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready query payload."""

        return {
            "from_year": self.from_year,
            "max_results": self.max_results,
            "sources": list(self.sources),
            "text": self.text,
            "to_year": self.to_year,
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> FactorDiscoveryQuery:
        """Rehydrate a query from cache JSON."""

        return cls(
            text=str(payload.get("text", "")),
            sources=tuple(str(item) for item in payload.get("sources", ())),
            max_results=int(payload.get("max_results", 10)),
            from_year=_optional_int(payload.get("from_year")),
            to_year=_optional_int(payload.get("to_year")),
        )


@dataclass(frozen=True, slots=True)
class FactorIdea:
    """One source-backed factor idea candidate."""

    idea_id: str
    source: str
    external_id: str
    title: str
    abstract: str
    url: str
    year: int | None
    authors: tuple[str, ...]
    citation_count: int | None
    candidate_tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.idea_id.strip():
            raise ValueError("idea_id is required")
        if not self.source.strip():
            raise ValueError("source is required")
        if not self.title.strip():
            raise ValueError("title is required")
        object.__setattr__(self, "idea_id", self.idea_id.strip())
        object.__setattr__(self, "source", self.source.strip().lower())
        object.__setattr__(self, "external_id", self.external_id.strip())
        object.__setattr__(self, "title", self.title.strip())
        object.__setattr__(self, "abstract", self.abstract.strip())
        object.__setattr__(self, "url", self.url.strip())
        object.__setattr__(
            self, "authors", tuple(author.strip() for author in self.authors if author.strip())
        )
        if not self.candidate_tags:
            object.__setattr__(
                self,
                "candidate_tags",
                _infer_candidate_tags(f"{self.title}\n{self.abstract}"),
            )

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready idea payload."""

        return {
            "abstract": self.abstract,
            "authors": list(self.authors),
            "candidate_tags": list(self.candidate_tags),
            "citation_count": self.citation_count,
            "external_id": self.external_id,
            "idea_id": self.idea_id,
            "source": self.source,
            "title": self.title,
            "url": self.url,
            "year": self.year,
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> FactorIdea:
        """Rehydrate a factor idea from cache JSON."""

        return cls(
            idea_id=str(payload.get("idea_id", "")),
            source=str(payload.get("source", "")),
            external_id=str(payload.get("external_id", "")),
            title=str(payload.get("title", "")),
            abstract=str(payload.get("abstract", "")),
            url=str(payload.get("url", "")),
            year=_optional_int(payload.get("year")),
            authors=tuple(str(item) for item in payload.get("authors", ())),
            citation_count=_optional_int(payload.get("citation_count")),
            candidate_tags=tuple(str(item) for item in payload.get("candidate_tags", ())),
        )


@dataclass(frozen=True, slots=True)
class FactorDiscoveryError:
    """Non-fatal source search failure."""

    source: str
    message: str

    def to_payload(self) -> dict[str, str]:
        """Return a deterministic JSON-ready error payload."""

        return {"message": self.message, "source": self.source}

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> FactorDiscoveryError:
        """Rehydrate a source error from cache JSON."""

        return cls(source=str(payload.get("source", "")), message=str(payload.get("message", "")))


@dataclass(frozen=True, slots=True)
class FactorDiscoveryResult:
    """Result of one factor idea discovery query."""

    query: FactorDiscoveryQuery
    ideas: tuple[FactorIdea, ...]
    errors: tuple[FactorDiscoveryError, ...] = ()
    cached: bool = False
    cache_path: Path | None = None

    def with_cache_state(self, *, cached: bool, cache_path: Path) -> FactorDiscoveryResult:
        """Return this result with cache metadata set."""

        return FactorDiscoveryResult(
            query=self.query,
            ideas=self.ideas,
            errors=self.errors,
            cached=cached,
            cache_path=cache_path,
        )

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready result payload."""

        return {
            "errors": [error.to_payload() for error in self.errors],
            "ideas": [idea.to_payload() for idea in self.ideas],
            "query": self.query.to_payload(),
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> FactorDiscoveryResult:
        """Rehydrate a result from cache JSON."""

        return cls(
            query=FactorDiscoveryQuery.from_payload(cls._mapping(payload, "query")),
            ideas=tuple(FactorIdea.from_payload(item) for item in cls._sequence(payload, "ideas")),
            errors=tuple(
                FactorDiscoveryError.from_payload(item) for item in cls._sequence(payload, "errors")
            ),
        )

    @staticmethod
    def _mapping(payload: Mapping[str, Any], field_name: str) -> Mapping[str, Any]:
        value = payload.get(field_name)
        if not isinstance(value, dict):
            raise ValueError(f"{field_name} must be a JSON object")
        return value

    @staticmethod
    def _sequence(payload: Mapping[str, Any], field_name: str) -> Sequence[Mapping[str, Any]]:
        value = payload.get(field_name, ())
        if not isinstance(value, list):
            raise ValueError(f"{field_name} must be a JSON list")
        if not all(isinstance(item, dict) for item in value):
            raise ValueError(f"{field_name} must contain JSON objects")
        return value

    def rows(self) -> tuple[dict[str, object], ...]:
        """Return notebook-friendly rows for discovered ideas."""

        return tuple(
            {
                "abstract": idea.abstract,
                "authors": ", ".join(idea.authors),
                "candidate_tags": ", ".join(idea.candidate_tags),
                "citation_count": idea.citation_count,
                "external_id": idea.external_id,
                "idea_id": idea.idea_id,
                "source": idea.source,
                "title": idea.title,
                "url": idea.url,
                "year": idea.year,
            }
            for idea in self.ideas
        )

    def to_pandas(self) -> Any:
        """Return discovered ideas as a pandas DataFrame."""

        pandas_module: Any = importlib.import_module("pandas")
        return pandas_module.DataFrame(self.rows())


class FactorIdeaSource(Protocol):
    """Provider boundary for scholarly factor idea searches."""

    name: str

    def search(self, query: FactorDiscoveryQuery) -> tuple[FactorIdea, ...]:
        """Return source-backed ideas for a query."""


class FactorDiscoveryHttpClient(Protocol):
    """Small HTTP boundary for source adapters."""

    def get_text(
        self,
        url: str,
        *,
        params: dict[str, str],
        headers: dict[str, str] | None = None,
    ) -> str:
        """Return text for an HTTP GET request."""


class UrllibFactorDiscoveryHttpClient:
    """Stdlib HTTP client used by factor discovery source adapters."""

    def __init__(self, *, timeout_seconds: float = 10.0) -> None:
        self._timeout_seconds = timeout_seconds

    def get_text(
        self,
        url: str,
        *,
        params: dict[str, str],
        headers: dict[str, str] | None = None,
    ) -> str:
        """Return UTF-8 response text for an HTTP GET request."""

        encoded = urllib.parse.urlencode(params)
        request = urllib.request.Request(
            f"{url}?{encoded}",
            headers={} if headers is None else headers,
        )
        with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
            data = response.read()
        if isinstance(data, bytes):
            return data.decode("utf-8")
        return str(data)


class SemanticScholarFactorIdeaSource:
    """Owns Semantic Scholar Graph API factor research paper searches."""

    name = "semantic_scholar"
    _url = "https://api.semanticscholar.org/graph/v1/paper/search"

    def __init__(self, *, http_client: FactorDiscoveryHttpClient | None = None) -> None:
        self._http_client = (
            http_client if http_client is not None else UrllibFactorDiscoveryHttpClient()
        )

    def search(self, query: FactorDiscoveryQuery) -> tuple[FactorIdea, ...]:
        """Return Semantic Scholar-backed factor ideas."""

        params = {
            "fields": "paperId,title,abstract,year,url,citationCount,authors,externalIds",
            "limit": str(query.max_results),
            "query": query.text,
        }
        year_range = _year_range(query)
        if year_range:
            params["year"] = year_range
        headers: dict[str, str] = {}
        api_key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
        if api_key:
            headers["x-api-key"] = api_key
        payload = json.loads(self._http_client.get_text(self._url, params=params, headers=headers))
        return tuple(
            self._idea_from_item(item) for item in payload.get("data", ()) if isinstance(item, dict)
        )

    def _idea_from_item(self, item: Mapping[str, Any]) -> FactorIdea:
        paper_id = str(item.get("paperId") or item.get("url") or _stable_text_id(item))
        return FactorIdea(
            idea_id=f"{self.name}:{paper_id}",
            source=self.name,
            external_id=paper_id,
            title=str(item.get("title") or ""),
            abstract=str(item.get("abstract") or ""),
            url=str(item.get("url") or ""),
            year=_optional_int(item.get("year")),
            authors=tuple(
                str(author.get("name", ""))
                for author in item.get("authors", ())
                if isinstance(author, dict)
            ),
            citation_count=_optional_int(item.get("citationCount")),
        )


class OpenAlexFactorIdeaSource:
    """Owns OpenAlex works factor research paper searches."""

    name = "openalex"
    _url = "https://api.openalex.org/works"

    def __init__(self, *, http_client: FactorDiscoveryHttpClient | None = None) -> None:
        self._http_client = (
            http_client if http_client is not None else UrllibFactorDiscoveryHttpClient()
        )

    def search(self, query: FactorDiscoveryQuery) -> tuple[FactorIdea, ...]:
        """Return OpenAlex-backed factor ideas."""

        params = {
            "per-page": str(query.max_results),
            "search": query.text,
            "sort": "cited_by_count:desc",
        }
        filters = _openalex_filters(query)
        if filters:
            params["filter"] = filters
        mailto = os.environ.get("OPENALEX_MAILTO")
        if mailto:
            params["mailto"] = mailto
        payload = json.loads(self._http_client.get_text(self._url, params=params))
        return tuple(
            self._idea_from_item(item)
            for item in payload.get("results", ())
            if isinstance(item, dict)
        )

    def _idea_from_item(self, item: Mapping[str, Any]) -> FactorIdea:
        external_id = str(item.get("id") or _stable_text_id(item)).rstrip("/").rsplit("/", 1)[-1]
        return FactorIdea(
            idea_id=f"{self.name}:{external_id}",
            source=self.name,
            external_id=external_id,
            title=str(item.get("display_name") or ""),
            abstract=_openalex_abstract(item.get("abstract_inverted_index")),
            url=str(item.get("doi") or item.get("id") or ""),
            year=_optional_int(item.get("publication_year")),
            authors=tuple(_openalex_authors(item.get("authorships"))),
            citation_count=_optional_int(item.get("cited_by_count")),
        )


class CrossrefFactorIdeaSource:
    """Owns Crossref works factor research paper searches."""

    name = "crossref"
    _url = "https://api.crossref.org/works"

    def __init__(self, *, http_client: FactorDiscoveryHttpClient | None = None) -> None:
        self._http_client = (
            http_client if http_client is not None else UrllibFactorDiscoveryHttpClient()
        )

    def search(self, query: FactorDiscoveryQuery) -> tuple[FactorIdea, ...]:
        """Return Crossref-backed factor ideas."""

        params = {
            "order": "desc",
            "query.bibliographic": query.text,
            "rows": str(query.max_results),
            "sort": "is-referenced-by-count",
        }
        filters = _crossref_filters(query)
        if filters:
            params["filter"] = filters
        mailto = os.environ.get("CROSSREF_MAILTO")
        if mailto:
            params["mailto"] = mailto
        payload = json.loads(self._http_client.get_text(self._url, params=params))
        message = payload.get("message", {})
        if not isinstance(message, dict):
            return ()
        return tuple(
            self._idea_from_item(item)
            for item in message.get("items", ())
            if isinstance(item, dict)
        )

    def _idea_from_item(self, item: Mapping[str, Any]) -> FactorIdea:
        doi = str(item.get("DOI") or _stable_text_id(item))
        return FactorIdea(
            idea_id=f"{self.name}:{doi}",
            source=self.name,
            external_id=doi,
            title=_first_text(item.get("title")),
            abstract=_strip_markup(str(item.get("abstract") or "")),
            url=str(item.get("URL") or f"https://doi.org/{doi}"),
            year=_crossref_year(item),
            authors=tuple(_crossref_authors(item.get("author"))),
            citation_count=_optional_int(item.get("is-referenced-by-count")),
        )


class ArxivFactorIdeaSource:
    """Owns arXiv Atom API factor research paper searches."""

    name = "arxiv"
    _url = "https://export.arxiv.org/api/query"

    def __init__(self, *, http_client: FactorDiscoveryHttpClient | None = None) -> None:
        self._http_client = (
            http_client if http_client is not None else UrllibFactorDiscoveryHttpClient()
        )

    def search(self, query: FactorDiscoveryQuery) -> tuple[FactorIdea, ...]:
        """Return arXiv-backed factor ideas."""

        params = {
            "max_results": str(query.max_results),
            "search_query": f"all:{query.text}",
            "sortBy": "relevance",
            "start": "0",
        }
        payload = self._http_client.get_text(self._url, params=params)
        root = ET.fromstring(payload)
        namespace = {"atom": "http://www.w3.org/2005/Atom"}
        return tuple(
            self._idea_from_entry(entry, namespace)
            for entry in root.findall("atom:entry", namespace)
        )

    def _idea_from_entry(self, entry: ET.Element, namespace: dict[str, str]) -> FactorIdea:
        raw_id = _xml_text(entry, "atom:id", namespace)
        external_id = re.sub(r"v\d+$", "", raw_id.rstrip("/").rsplit("/", 1)[-1])
        return FactorIdea(
            idea_id=f"{self.name}:{external_id}",
            source=self.name,
            external_id=external_id,
            title=_collapse_whitespace(_xml_text(entry, "atom:title", namespace)),
            abstract=_collapse_whitespace(_xml_text(entry, "atom:summary", namespace)),
            url=_arxiv_url(entry, namespace) or raw_id,
            year=_arxiv_year(_xml_text(entry, "atom:published", namespace)),
            authors=tuple(
                _xml_text(author, "atom:name", namespace)
                for author in entry.findall("atom:author", namespace)
            ),
            citation_count=None,
        )


class FactorIdeaStore:
    """Owns deterministic local cache files for factor idea discovery."""

    def __init__(self, root_dir: Path) -> None:
        self._root_dir = root_dir

    @property
    def cache_dir(self) -> Path:
        """Return the cache directory for factor idea searches."""

        return self._root_dir / "factor-ideas"

    def cache_path(self, query: FactorDiscoveryQuery) -> Path:
        """Return the deterministic cache path for a query."""

        return self.cache_dir / f"{query.query_id}.json"

    def load_search(self, query: FactorDiscoveryQuery) -> FactorDiscoveryResult | None:
        """Load a cached search result if present."""

        path = self.cache_path(query)
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("factor idea cache must contain a JSON object")
        result = FactorDiscoveryResult.from_payload(payload)
        return result.with_cache_state(cached=True, cache_path=path)

    def save_search(self, result: FactorDiscoveryResult) -> FactorDiscoveryResult:
        """Write a search result to deterministic JSON cache."""

        path = self.cache_path(result.query)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(result.to_payload(), sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        return result.with_cache_state(cached=result.cached, cache_path=path)


class FactorDiscovery:
    """Coordinates scholarly source searches and local factor idea cache."""

    @classmethod
    def with_default_sources(cls, store: FactorIdeaStore) -> FactorDiscovery:
        """Return discovery service wired to supported scholarly sources."""

        return cls(
            store=store,
            sources={
                "arxiv": ArxivFactorIdeaSource(),
                "crossref": CrossrefFactorIdeaSource(),
                "openalex": OpenAlexFactorIdeaSource(),
                "semantic_scholar": SemanticScholarFactorIdeaSource(),
            },
        )

    def __init__(
        self,
        *,
        store: FactorIdeaStore,
        sources: Mapping[str, FactorIdeaSource],
    ) -> None:
        self._store = store
        self._sources = {name.strip().lower(): source for name, source in sources.items()}

    def search(
        self,
        text: str,
        *,
        sources: Sequence[str] = DEFAULT_FACTOR_DISCOVERY_SOURCES,
        max_results: int = 10,
        from_year: int | None = None,
        to_year: int | None = None,
        refresh: bool = False,
    ) -> FactorDiscoveryResult:
        """Search configured sources for source-backed factor ideas."""

        query = FactorDiscoveryQuery(
            text=text,
            sources=tuple(sources),
            max_results=max_results,
            from_year=from_year,
            to_year=to_year,
        )
        if not refresh:
            cached = self._store.load_search(query)
            if cached is not None:
                return cached

        ideas: list[FactorIdea] = []
        errors: list[FactorDiscoveryError] = []
        seen: set[str] = set()
        for source_name in query.sources:
            source = self._sources.get(source_name)
            if source is None:
                errors.append(
                    FactorDiscoveryError(
                        source=source_name,
                        message=f"unknown factor discovery source: {source_name}",
                    )
                )
                continue
            try:
                source_ideas = source.search(query)
            except Exception as exc:  # pragma: no cover - exact source failures vary
                errors.append(FactorDiscoveryError(source=source_name, message=str(exc)))
                continue
            for idea in source_ideas:
                if idea.idea_id in seen:
                    continue
                ideas.append(idea)
                seen.add(idea.idea_id)

        result = FactorDiscoveryResult(query=query, ideas=tuple(ideas), errors=tuple(errors))
        if result.ideas:
            return self._store.save_search(result)
        return result


def _infer_candidate_tags(text: str) -> tuple[str, ...]:
    lowered = text.lower()
    return tuple(
        tag for tag, terms in _FACTOR_TAG_TERMS.items() if any(term in lowered for term in terms)
    )


def _stable_text_id(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def _year_range(query: FactorDiscoveryQuery) -> str:
    if query.from_year is None and query.to_year is None:
        return ""
    start = "" if query.from_year is None else str(query.from_year)
    end = "" if query.to_year is None else str(query.to_year)
    return f"{start}-{end}"


def _openalex_filters(query: FactorDiscoveryQuery) -> str:
    filters: list[str] = []
    if query.from_year is not None:
        filters.append(f"from_publication_date:{query.from_year}-01-01")
    if query.to_year is not None:
        filters.append(f"to_publication_date:{query.to_year}-12-31")
    return ",".join(filters)


def _crossref_filters(query: FactorDiscoveryQuery) -> str:
    filters: list[str] = []
    if query.from_year is not None:
        filters.append(f"from-pub-date:{query.from_year}-01-01")
    if query.to_year is not None:
        filters.append(f"until-pub-date:{query.to_year}-12-31")
    return ",".join(filters)


def _openalex_abstract(value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    positions: list[tuple[int, str]] = []
    for term, indexes in value.items():
        if not isinstance(term, str) or not isinstance(indexes, list):
            continue
        for index in indexes:
            if isinstance(index, int):
                positions.append((index, term))
    return " ".join(term for _index, term in sorted(positions))


def _openalex_authors(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    authors: list[str] = []
    for authorship in value:
        if not isinstance(authorship, dict):
            continue
        author = authorship.get("author")
        if isinstance(author, dict):
            display_name = str(author.get("display_name") or "").strip()
            if display_name:
                authors.append(display_name)
    return tuple(authors)


def _first_text(value: Any) -> str:
    if isinstance(value, list) and value:
        return str(value[0])
    if isinstance(value, str):
        return value
    return ""


def _strip_markup(value: str) -> str:
    return _collapse_whitespace(html.unescape(re.sub(r"<[^>]+>", " ", value)))


def _crossref_year(item: Mapping[str, Any]) -> int | None:
    for field_name in ("published-print", "published-online", "issued", "published"):
        year = _year_from_date_parts(item.get(field_name))
        if year is not None:
            return year
    return None


def _year_from_date_parts(value: Any) -> int | None:
    if not isinstance(value, dict):
        return None
    date_parts = value.get("date-parts")
    if not isinstance(date_parts, list) or not date_parts:
        return None
    first = date_parts[0]
    if not isinstance(first, list) or not first:
        return None
    return _optional_int(first[0])


def _crossref_authors(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    authors: list[str] = []
    for author in value:
        if not isinstance(author, dict):
            continue
        name = " ".join(
            part
            for part in (
                str(author.get("given") or "").strip(),
                str(author.get("family") or "").strip(),
            )
            if part
        )
        if name:
            authors.append(name)
    return tuple(authors)


def _xml_text(element: ET.Element, path: str, namespace: dict[str, str]) -> str:
    match = element.find(path, namespace)
    if match is None or match.text is None:
        return ""
    return match.text.strip()


def _arxiv_url(entry: ET.Element, namespace: dict[str, str]) -> str:
    for link in entry.findall("atom:link", namespace):
        if link.attrib.get("rel") == "alternate" and link.attrib.get("href"):
            return link.attrib["href"]
    return ""


def _arxiv_year(value: str) -> int | None:
    if len(value) < 4:
        return None
    return _optional_int(value[:4])


def _collapse_whitespace(value: str) -> str:
    return " ".join(value.split())


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


__all__ = [
    "ArxivFactorIdeaSource",
    "CrossrefFactorIdeaSource",
    "DEFAULT_FACTOR_DISCOVERY_SOURCES",
    "FactorDiscovery",
    "FactorDiscoveryError",
    "FactorDiscoveryHttpClient",
    "FactorDiscoveryQuery",
    "FactorDiscoveryResult",
    "FactorIdea",
    "FactorIdeaSource",
    "FactorIdeaStore",
    "OpenAlexFactorIdeaSource",
    "SemanticScholarFactorIdeaSource",
    "UrllibFactorDiscoveryHttpClient",
]
