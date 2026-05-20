# Research Candidate Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make research users able to go from web-backed factor discovery to persisted, reviewable factor candidates with one facade call, without creating executable trading behavior.

**Architecture:** `qts.research.factor_candidate` owns the candidate batch produced by discovery plus spec drafting and persistence. `FactorSpecStore` owns review decisions for persisted specs. `ResearchSession` remains a thin facade over those owners and still delegates executable evidence to `BacktestPipeline` / `BacktestPipelineRunner`.

**Tech Stack:** Python dataclasses, deterministic JSON/JSONL, pathlib, pandas via lazy import, existing `FactorDiscovery`, `FactorSpecDrafter`, `FactorSpecStore`, pytest, guardrails, mypy.

---

## Domain Gates

Domain fact / invariant:
Research candidates are evidence and review inputs only. An accepted candidate is still not executable trading behavior.

Correct owner or abstraction boundary:
`FactorDiscovery` owns source-backed idea search and cache. `FactorSpecDrafter` owns deterministic idea-to-spec draft heuristics. `FactorCandidateWorkflow` owns the user-friendly combination of discovery, drafting, and persistence. `FactorSpecStore` owns persisted specs and review decisions. `ResearchSession` delegates and does not implement source parsing, spec mutation, runtime behavior, or artifact formats.

Forbidden shortcut:
Do not generate factor Python code, target intents, orders, fills, account state, portfolio state, or paper/live behavior from `FactorIdea`, `FactorSpec`, `FactorCandidateBatch`, or review decisions.

Required gates / verification:
Focused red-green unit tests, focused integration tests for the facade path, docs updates, platform-freeze class exceptions, source inventory regeneration, `make format`, `make lint`, `make guardrails`, `make typecheck`, `make test-unit`, `make test-integration`, `make test-anchor`, `git diff --check`, and code-review-graph refresh/review.

## Scope

In scope for this branch:

- Add a one-call candidate workflow: `session.find_factor_candidates(...)`.
- Persist drafted specs produced by the candidate workflow.
- Return notebook-friendly candidate rows and pandas frames.
- Persist factor spec review decisions with reviewer, decision, notes, and timestamp.
- Update the stored spec `review_status` when a review decision is recorded.
- Add `session.review_factor_spec(...)`, `list_factor_reviews(...)`, `list_factor_specs_by_status(...)`, and `review_queue_frame(...)`.
- Update docs and generated source inventory.

Out of scope for this branch:

- Factor implementation generation.
- Evaluating candidate specs as factor signals.
- Paper/live use of candidate specs or review decisions.
- Ranking model, LLM summarization, or provider-specific relevance scoring.
- New production dependencies.

## Acceptance Criteria

- `FactorCandidateWorkflow.find(...)` calls existing `FactorDiscovery`, drafts specs with `FactorSpecDrafter`, saves them with `FactorSpecStore`, and returns a `FactorCandidateBatch`.
- `FactorCandidateBatch.specs` returns the drafted specs in discovery order.
- `FactorCandidateBatch.rows()` includes query id, idea id, source, title, candidate tags, spec name, spec path, and review status.
- `FactorCandidateBatch.to_pandas()` returns a DataFrame using the existing lazy pandas pattern.
- `FactorSpecStore.record_review(...)` validates decisions in `draft`, `accepted`, `rejected`, and `needs_work`; writes deterministic JSONL review evidence; updates the persisted spec `review_status`; and returns a `FactorSpecReview`.
- Review listing can filter by decision and returns newest-first records.
- `ResearchSession` exposes candidate and review workflow methods without changing `run_backtest(...)` or `optimize(...)`.
- No new API imports runtime, execution, risk, paper/live broker adapters, account actors, portfolio mutation, or order boundaries.
- Docs explain that accepted review status is still research evidence, not a runtime promotion.

## Verification Evidence

Record exact outputs before completion:

- [ ] `uv run pytest tests/unit/research/test_factor_candidate.py -q`
- [ ] `uv run pytest tests/unit/research/test_factor_spec_store.py -q`
- [ ] `uv run pytest tests/unit/research/test_research_session.py -q`
- [ ] `uv run pytest tests/integration/test_research_session_factor_discovery.py tests/integration/test_research_session_facade.py -q`
- [ ] `uv run pytest tests/unit/test_backtest_live_parallel_sequence_html.py tests/unit/test_project_panorama_html.py -q`
- [ ] `make format`
- [ ] `make lint`
- [ ] `make guardrails`
- [ ] `make typecheck`
- [ ] `make test-unit`
- [ ] `make test-integration`
- [ ] `make test-anchor`
- [ ] `git diff --check`
- [ ] code-review-graph `build_or_update_graph_tool`
- [ ] code-review-graph `detect_changes_tool`
- [ ] code-review-graph `get_affected_flows_tool`
- [ ] independent read-only code review

## File Structure

- Create `backend/src/qts/research/factor_candidate.py`
  - Owns candidate batch rows and the discovery/draft/save workflow.
  - Public classes: `FactorCandidate`, `FactorCandidateBatch`, `FactorCandidateWorkflow`.
- Modify `backend/src/qts/research/factor_spec_store.py`
  - Add review record ownership and status-filtered spec listing.
  - Public class: `FactorSpecReview`.
- Modify `backend/src/qts/research/session.py`
  - Add candidate and review facade methods.
- Modify `backend/src/qts/research/__init__.py`
  - Export new public research types.
- Modify `docs/architecture/platform_freeze_exceptions.yaml`
  - Register new public classes.
- Modify `docs/research/factor_discovery_v1.md`
  - Document candidate workflow.
- Modify `docs/research/factor_spec_v1.md`
  - Document review decisions.
- Modify `docs/research/research_session_v1.md`
  - Add one-call candidate usage and review queue usage.
- Regenerate `project_panorama.html` and `docs/architecture/backtest_live_parallel_sequence.html`.
- Add `tests/unit/research/test_factor_candidate.py`.
- Modify `tests/unit/research/test_factor_spec_store.py`.
- Modify `tests/unit/research/test_research_session.py`.
- Modify `tests/integration/test_research_session_factor_discovery.py`.
- Modify `tests/integration/test_research_session_facade.py`.

## Parallelization Plan

- Task 1 and Task 2 are independent and can be implemented in parallel with disjoint production files.
- Task 3 depends on Task 1 and Task 2 because it wires both owners into `ResearchSession`.
- Task 4 depends on public API names from Tasks 1-3.
- Task 5 is final verification and review.

## Task 1: Factor Candidate Workflow

**Files:**

- Create: `backend/src/qts/research/factor_candidate.py`
- Test: `tests/unit/research/test_factor_candidate.py`

- [ ] **Step 1: Write failing candidate workflow tests**

Add tests for:

```python
def test_factor_candidate_workflow_discovers_drafts_saves_and_returns_batch(tmp_path: Path) -> None: ...
def test_factor_candidate_batch_rows_are_notebook_friendly(tmp_path: Path) -> None: ...
def test_factor_candidate_batch_to_pandas_returns_dataframe(tmp_path: Path) -> None: ...
```

Run:

```bash
uv run pytest tests/unit/research/test_factor_candidate.py -q
```

Expected red:

```text
ModuleNotFoundError: No module named 'qts.research.factor_candidate'
```

- [ ] **Step 2: Implement candidate types**

Implement:

```python
@dataclass(frozen=True, slots=True)
class FactorCandidate:
    idea: FactorIdea
    spec: FactorSpec
    spec_path: Path

@dataclass(frozen=True, slots=True)
class FactorCandidateBatch:
    result: FactorDiscoveryResult
    candidates: tuple[FactorCandidate, ...]

    @property
    def specs(self) -> tuple[FactorSpec, ...]: ...
    def rows(self) -> tuple[dict[str, object], ...]: ...
    def to_pandas(self) -> Any: ...
```

Rows must include:

```text
query_id, query_text, idea_id, source, external_id, title, url, year,
candidate_tags, spec_name, spec_path, review_status
```

- [ ] **Step 3: Implement workflow owner**

Implement:

```python
class FactorCandidateWorkflow:
    def __init__(self, *, discovery: FactorDiscovery, spec_store: FactorSpecStore) -> None: ...

    def find(
        self,
        query: str,
        *,
        sources: Sequence[str],
        max_results: int,
        from_year: int | None = None,
        to_year: int | None = None,
        refresh: bool = False,
    ) -> FactorCandidateBatch: ...
```

`find(...)` must call `discovery.search(...)`, draft each idea with `FactorSpecDrafter`, save each spec with `spec_store.save(...)`, and return a batch preserving discovery order.

- [ ] **Step 4: Verify Task 1**

Run:

```bash
uv run pytest tests/unit/research/test_factor_candidate.py -q
```

Expected green:

```text
3 passed
```

## Task 2: Factor Spec Review Store

**Files:**

- Modify: `backend/src/qts/research/factor_spec_store.py`
- Test: `tests/unit/research/test_factor_spec_store.py`

- [ ] **Step 1: Write failing review tests**

Add tests for:

```python
def test_factor_spec_store_records_review_and_updates_spec_status(tmp_path: Path) -> None: ...
def test_factor_spec_store_lists_reviews_newest_first_and_filters_decision(tmp_path: Path) -> None: ...
def test_factor_spec_store_rejects_unknown_review_decision(tmp_path: Path) -> None: ...
def test_factor_spec_store_lists_specs_by_status(tmp_path: Path) -> None: ...
```

Run:

```bash
uv run pytest tests/unit/research/test_factor_spec_store.py -q
```

Expected red:

```text
AttributeError: 'FactorSpecStore' object has no attribute 'record_review'
```

- [ ] **Step 2: Implement `FactorSpecReview`**

Implement a frozen dataclass with fields:

```python
spec_name: str
decision: str
reviewer: str
reviewed_at: datetime
notes: tuple[str, ...] = ()
```

Allowed decisions:

```python
("draft", "accepted", "rejected", "needs_work")
```

The review must require non-empty `spec_name`, `decision`, and `reviewer`, require timezone-aware `reviewed_at`, normalize notes, and support deterministic `to_payload()` / `from_payload(...)`.

- [ ] **Step 3: Add review methods to `FactorSpecStore`**

Implement:

```python
def record_review(
    self,
    name: str,
    *,
    decision: str,
    reviewer: str,
    notes: Sequence[str] = (),
    reviewed_at: datetime | None = None,
) -> FactorSpecReview: ...

def list_reviews(self, *, decision: str | None = None) -> tuple[FactorSpecReview, ...]: ...
def list_specs_by_status(self, status: str) -> tuple[FactorSpec, ...]: ...
```

`record_review(...)` must load the existing spec, write it back with `review_status=decision`, append review evidence to `<research store>/factor-spec-reviews.jsonl`, and return the review. `list_reviews(...)` must return newest-first records sorted by `reviewed_at` descending, then `spec_name`.

- [ ] **Step 4: Verify Task 2**

Run:

```bash
uv run pytest tests/unit/research/test_factor_spec_store.py -q
```

Expected green:

```text
15 passed
```

## Task 3: ResearchSession Facade Wiring

**Files:**

- Modify: `backend/src/qts/research/session.py`
- Modify: `backend/src/qts/research/__init__.py`
- Test: `tests/unit/research/test_research_session.py`
- Test: `tests/integration/test_research_session_factor_discovery.py`
- Test: `tests/integration/test_research_session_facade.py`

- [ ] **Step 1: Write failing facade tests**

Add unit tests for:

```python
def test_research_session_find_factor_candidates_saves_specs(tmp_path: Path) -> None: ...
def test_research_session_review_factor_spec_records_decision(tmp_path: Path) -> None: ...
def test_research_session_review_queue_frame_filters_drafts(tmp_path: Path) -> None: ...
```

Add integration tests proving candidate workflow does not change backtest:

```python
def test_research_session_candidate_workflow_keeps_backtest_path_unchanged(tmp_path: Path) -> None: ...
```

Run:

```bash
uv run pytest tests/unit/research/test_research_session.py tests/integration/test_research_session_factor_discovery.py tests/integration/test_research_session_facade.py -q
```

Expected red:

```text
AttributeError: 'ResearchSession' object has no attribute 'find_factor_candidates'
```

- [ ] **Step 2: Add facade methods**

Add to `ResearchSession`:

```python
def find_factor_candidates(...) -> FactorCandidateBatch: ...
def find_factor_candidates_frame(...) -> Any: ...
def review_factor_spec(...) -> FactorSpecReview: ...
def list_factor_reviews(...) -> tuple[FactorSpecReview, ...]: ...
def list_factor_specs_by_status(...) -> tuple[FactorSpec, ...]: ...
def review_queue_frame(...) -> Any: ...
```

Use configured discovery defaults when call-site values are omitted. Do not modify `run_backtest(...)` or `optimize(...)`.

- [ ] **Step 3: Export public classes**

Export `FactorCandidate`, `FactorCandidateBatch`, `FactorCandidateWorkflow`, and `FactorSpecReview` from `qts.research`.

- [ ] **Step 4: Verify Task 3**

Run:

```bash
uv run pytest tests/unit/research/test_research_session.py tests/integration/test_research_session_factor_discovery.py tests/integration/test_research_session_facade.py -q
```

Expected green.

## Task 4: Docs, Guardrails, and Inventory

**Files:**

- Modify: `docs/architecture/platform_freeze_exceptions.yaml`
- Modify: `docs/research/factor_discovery_v1.md`
- Modify: `docs/research/factor_spec_v1.md`
- Modify: `docs/research/research_session_v1.md`
- Modify: `project_panorama.html`
- Modify: `docs/architecture/backtest_live_parallel_sequence.html`

- [ ] **Step 1: Register new public classes**

Add platform-freeze exceptions for:

```text
FactorCandidate
FactorCandidateBatch
FactorCandidateWorkflow
FactorSpecReview
```

Use owner `platform` and expiry `2027-05-20`.

- [ ] **Step 2: Update research docs**

Document the allowed path:

```text
web-backed FactorIdea
  -> persisted FactorCandidateBatch
  -> FactorSpec review decision
  -> human implementation as versioned qts.factors code
  -> FactorEvaluation / ExperimentManifest evidence
  -> shared BacktestPipeline
  -> paper/live only after reviewed code is used by strategies
```

State explicitly that `accepted` review status is not runtime promotion.

- [ ] **Step 3: Regenerate inventory docs**

Run the existing inventory generation command used by this repo for `project_panorama.html` and `docs/architecture/backtest_live_parallel_sequence.html`. If no single command exists, update them with the existing test-supported generation path.

- [ ] **Step 4: Verify docs and guardrails**

Run:

```bash
uv run pytest tests/unit/test_backtest_live_parallel_sequence_html.py tests/unit/test_project_panorama_html.py -q
make guardrails
```

Expected green.

## Task 5: Final Verification, Graph Review, and Commit

**Files:**

- All changed files.

- [ ] **Step 1: Run focused tests**

Run:

```bash
uv run pytest tests/unit/research/test_factor_candidate.py -q
uv run pytest tests/unit/research/test_factor_spec_store.py -q
uv run pytest tests/unit/research/test_research_session.py -q
uv run pytest tests/integration/test_research_session_factor_discovery.py tests/integration/test_research_session_facade.py -q
```

- [ ] **Step 2: Run full required checks**

Run:

```bash
make format
make lint
make guardrails
make typecheck
make test-unit
make test-integration
make test-anchor
git diff --check
```

- [ ] **Step 3: Refresh and review graph**

Run code-review-graph:

```text
build_or_update_graph_tool(full_rebuild=False, postprocess="minimal")
detect_changes_tool(base="research-workbench", detail_level="minimal")
get_affected_flows_tool(base="research-workbench")
```

Review any affected flows touching `ResearchSession`, `run_backtest`, or `optimize`.

- [ ] **Step 4: Independent read-only review**

Request read-only review of the diff against `research-workbench`, focused on:

- forbidden runtime/execution/risk/broker/account/portfolio imports;
- candidate/review artifacts accidentally becoming executable behavior;
- missing tests for acceptance criteria;
- docs contradicting architecture.

- [ ] **Step 5: Commit**

Commit with:

```bash
git commit -m "Add research candidate workflow"
```
