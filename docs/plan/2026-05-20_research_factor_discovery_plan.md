# Research Factor Discovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a ResearchSession facade workflow that searches scholarly web sources for factor ideas, caches the evidence locally, and returns notebook-friendly idea cards without creating a research-only trading path.

**Architecture:** `qts.research.factor_discovery` owns web-search adapters, factor idea records, query/result validation, and local cache storage. `ResearchSession` delegates to this service through convenience methods; executable validation remains in existing `qts.factors`, `FactorEvaluation`, `BacktestPipeline`, and `BacktestPipelineRunner` boundaries.

**Tech Stack:** Python dataclasses, stdlib `urllib`, `json`, `xml.etree.ElementTree`, optional pandas via local import, pytest with fake HTTP clients, existing `ResearchSession` and `ExperimentStore` patterns.

---

## Domain Gates

Domain fact / invariant:
Web factor discovery is idea discovery only. It may collect metadata, abstracts, citations, links, and heuristic tags. It must not generate orders, targets, fills, account state, or executable strategy behavior.

Correct owner or abstraction boundary:
`qts.research.factor_discovery` owns candidate idea discovery and cache artifacts. Versioned factor implementation stays in `qts.factors`. Factor validation stays in `qts.research.factor_evaluation`. Executable evidence stays in the existing `ResearchSession.run_backtest(...)` and `ResearchSession.optimize(...)` facade methods.

Forbidden shortcut:
Do not let web search results bypass `qts.factors`, `FactorEvaluation`, `BacktestPipeline`, `RiskEngine`, `OrderManagerActor`, `ExecutionActor`, or `AccountActor`. Do not add production dependencies for HTTP.

Required gates / verification:
Unit tests for query validation, store cache determinism, source parsing, deduplication, and ResearchSession delegation. Integration test proving `ResearchSession.discover_factors(...)` returns cached idea evidence without invoking backtest/paper/live runtime. `make guardrails`, `make typecheck`, focused research tests, and normal project checks.

## File Structure

- Create `backend/src/qts/research/factor_discovery.py`: factor idea models, source adapters, cache store, and discovery service.
- Modify `backend/src/qts/research/session.py`: add lazy factor discovery facade methods.
- Modify `backend/src/qts/research/__init__.py`: export public discovery types.
- Modify `configs/research/quickstart.yaml`: add optional `discovery` defaults.
- Add `docs/research/factor_discovery_v1.md`: durable boundary and usage doc.
- Modify `docs/architecture/platform_freeze_exceptions.yaml`: register new platform-owned discovery classes.
- Add `tests/unit/research/test_factor_discovery.py`: model/store/source/service tests.
- Add `tests/integration/test_research_session_factor_discovery.py`: session facade and cache workflow.
- Regenerate `project_panorama.html` and `docs/architecture/backtest_live_parallel_sequence.html` if source inventory tests require it.

## Task 1: Models, Store, and Service

- [x] **Step 1: Write failing unit tests**

Add tests in `tests/unit/research/test_factor_discovery.py` for:

```python
def test_factor_discovery_query_validates_inputs() -> None: ...
def test_factor_idea_infers_candidate_tags_from_title_and_abstract() -> None: ...
def test_factor_idea_store_round_trips_cached_search(tmp_path: Path) -> None: ...
def test_factor_discovery_uses_cache_without_calling_sources(tmp_path: Path) -> None: ...
def test_factor_discovery_deduplicates_ideas_across_sources(tmp_path: Path) -> None: ...
```

Run:

```bash
uv run pytest tests/unit/research/test_factor_discovery.py -q
```

Expected: fail because `qts.research.factor_discovery` does not exist.

- [x] **Step 2: Implement minimal models/store/service**

Create `FactorIdea`, `FactorDiscoveryQuery`, `FactorDiscoveryError`, `FactorDiscoveryResult`, `FactorIdeaStore`, `FactorIdeaSource`, and `FactorDiscovery`.

Keep JSON cache deterministic with sorted keys and query-hash paths under `store_root/factor-ideas/`.

- [x] **Step 3: Rerun unit tests**

```bash
uv run pytest tests/unit/research/test_factor_discovery.py -q
```

Expected: pass.

## Task 2: Scholarly Source Adapters

- [x] **Step 1: Write failing adapter tests**

In `tests/unit/research/test_factor_discovery.py`, add tests with a fake HTTP client for:

```python
def test_semantic_scholar_source_parses_paper_results() -> None: ...
def test_openalex_source_parses_abstract_inverted_index() -> None: ...
def test_crossref_source_parses_work_items() -> None: ...
def test_arxiv_source_parses_atom_entries() -> None: ...
```

Run:

```bash
uv run pytest tests/unit/research/test_factor_discovery.py -q
```

Expected: fail because source adapter classes do not exist.

- [x] **Step 2: Implement source adapters**

Implement `SemanticScholarFactorIdeaSource`, `OpenAlexFactorIdeaSource`, `CrossrefFactorIdeaSource`, and `ArxivFactorIdeaSource`.

Use stdlib HTTP through `UrllibFactorDiscoveryHttpClient`; tests must use fake HTTP and never call the network.

- [x] **Step 3: Rerun adapter tests**

```bash
uv run pytest tests/unit/research/test_factor_discovery.py -q
```

Expected: pass.

## Task 3: ResearchSession Facade and Docs

- [x] **Step 1: Write failing session tests**

Add unit/integration tests:

```python
def test_research_session_config_loads_discovery_defaults(tmp_path: Path) -> None: ...
def test_research_session_discover_factors_delegates_to_discovery_service(tmp_path: Path) -> None: ...
def test_research_session_discover_factors_frame_returns_dataframe(tmp_path: Path) -> None: ...
```

Run:

```bash
uv run pytest tests/unit/research/test_research_session.py tests/integration/test_research_session_factor_discovery.py -q
```

Expected: fail because session facade methods do not exist.

- [x] **Step 2: Implement session facade**

Add `discovery_sources` and `discovery_max_results` to `ResearchSessionConfig`, and add:

```python
ResearchSession.discover_factors(...)
ResearchSession.discover_factors_frame(...)
```

These methods must delegate to `FactorDiscovery`; they must not import or invoke backtest runtime unless the user separately calls `run_backtest(...)` or `optimize(...)`.

- [x] **Step 3: Add docs/config exports**

Update public exports, quickstart YAML, `docs/research/factor_discovery_v1.md`, and platform freeze exceptions.

## Task 4: Verification and Cleanup

- [x] **Step 1: Inspect private helpers**

```bash
rg -n "^def _|^class _" backend/src/qts/research/factor_discovery.py backend/src/qts/research/session.py
```

Expected: private helpers are class-owned validation/conversion helpers or pure module algorithms serving source parsing.

- [x] **Step 2: Run focused checks**

```bash
uv run pytest tests/unit/research tests/integration/test_research_session_factor_discovery.py tests/integration/test_research_session_facade.py -q
make guardrails
make typecheck
```

Expected: all pass.

- [x] **Step 3: Run normal-code checks**

```bash
make format
make lint
make test-unit
make test-integration
make test-anchor
git diff --check
```

Expected: all pass or report exact blockers.
