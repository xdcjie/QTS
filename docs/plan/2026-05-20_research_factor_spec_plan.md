# Research FactorSpec Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a structured `FactorSpec` draft workflow that turns source-backed `FactorIdea` records into human-reviewable factor hypotheses without generating executable trading behavior.

**Architecture:** `qts.research.factor_spec` owns the draft schema and deterministic drafting policy. `ResearchSession` exposes convenience methods that delegate to the drafter; executable factor implementation remains in `qts.factors`, and validation remains in `FactorEvaluation` plus the existing backtest pipeline.

**Tech Stack:** Python dataclasses, deterministic JSON payloads, heuristic tag-to-field mapping, optional pandas only through existing idea/result frame paths, pytest.

---

## Domain Gates

Domain fact / invariant:
`FactorSpec` is a reviewed research hypothesis draft, not executable factor code and not strategy behavior.

Correct owner or abstraction boundary:
`qts.research.factor_spec` owns the schema and draft heuristics. `qts.factors` owns versioned factor implementations. `qts.research.factor_evaluation` owns factor evidence metrics. `ResearchSession` only delegates.

Forbidden shortcut:
Do not generate Python factor code, orders, target intents, fills, account state, or backtest-specific behavior from `FactorIdea` or `FactorSpec`.

Required gates / verification:
Unit tests for schema validation, deterministic payloads, tag mapping, source references, session delegation, public exports, docs, `make guardrails`, `make typecheck`, and focused research tests.

## File Structure

- Create `backend/src/qts/research/factor_spec.py`: `FactorSpecSourceRef`, `FactorSpec`, `FactorSpecDrafter`.
- Modify `backend/src/qts/research/session.py`: add `draft_factor_spec(...)` and `draft_factor_specs(...)`.
- Modify `backend/src/qts/research/__init__.py`: export public spec types.
- Add `docs/research/factor_spec_v1.md`: durable boundary and promotion path.
- Modify `docs/research/factor_discovery_v1.md`: link FactorIdea promotion to FactorSpec.
- Modify `docs/architecture/platform_freeze_exceptions.yaml`: register new classes.
- Add `tests/unit/research/test_factor_spec.py`: spec/drafter/session tests.
- Regenerate source inventory HTML if tests require it.

## Task 1: FactorSpec Schema and Drafter

- [x] **Step 1: Write failing unit tests**

Add `tests/unit/research/test_factor_spec.py` with tests for:

```python
def test_factor_spec_drafter_maps_momentum_carry_idea_to_reviewable_spec() -> None: ...
def test_factor_spec_to_payload_is_deterministic() -> None: ...
def test_factor_spec_rejects_empty_required_fields() -> None: ...
def test_factor_spec_drafter_preserves_source_reference() -> None: ...
```

Run:

```bash
uv run pytest tests/unit/research/test_factor_spec.py -q
```

Expected: fail because `qts.research.factor_spec` does not exist.

- [x] **Step 2: Implement schema and drafter**

Create `FactorSpecSourceRef`, `FactorSpec`, and `FactorSpecDrafter`.

The drafter must produce:

- `review_status="draft"`
- `promotion_gate="human_review_required"`
- deterministic `name`
- `hypothesis`
- `inputs`
- `lookback`
- `universe`
- `rebalance`
- `expected_direction`
- `data_requirements`
- `source_refs`
- `candidate_tags`
- `notes`

- [x] **Step 3: Rerun unit tests**

```bash
uv run pytest tests/unit/research/test_factor_spec.py -q
```

Expected: pass.

## Task 2: ResearchSession Facade

- [x] **Step 1: Write failing session/public tests**

Add tests in `tests/unit/research/test_factor_spec.py` for:

```python
def test_research_session_drafts_single_factor_spec() -> None: ...
def test_research_session_drafts_specs_from_discovery_result() -> None: ...
def test_factor_spec_public_exports_are_available() -> None: ...
```

Run:

```bash
uv run pytest tests/unit/research/test_factor_spec.py -q
```

Expected: fail because session methods and public exports do not exist.

- [x] **Step 2: Implement session methods and exports**

Add:

```python
ResearchSession.draft_factor_spec(idea: FactorIdea) -> FactorSpec
ResearchSession.draft_factor_specs(ideas: FactorDiscoveryResult | Sequence[FactorIdea]) -> tuple[FactorSpec, ...]
```

These methods must not call backtest, optimizer, runtime, paper, or live adapters.

- [x] **Step 3: Rerun tests**

```bash
uv run pytest tests/unit/research/test_factor_spec.py tests/unit/research/test_research_session.py -q
```

Expected: pass.

## Task 3: Docs and Verification

- [x] **Step 1: Add docs and freeze exceptions**

Add `docs/research/factor_spec_v1.md`, update `docs/research/factor_discovery_v1.md`, and register new classes in `docs/architecture/platform_freeze_exceptions.yaml`.

- [x] **Step 2: Run focused checks**

```bash
uv run pytest tests/unit/research -q
make guardrails
make typecheck
```

Expected: all pass.

- [x] **Step 3: Run normal checks**

```bash
make format
make lint
make test-unit
make test-integration
make test-anchor
git diff --check
```

Expected: all pass or report exact blockers.
