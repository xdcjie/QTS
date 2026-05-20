# Research Workbench Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Make research workflows easier by adding persistent factor-spec management and a notebook-friendly experiment recorder while preserving the shared backtest/paper/live architecture.

**Architecture:** `qts.research` remains a facade over existing owners. `FactorSpecStore` owns review-draft persistence; `ResearchExperimentRecorder` owns manifest-backed experiment recording; `ResearchSession` delegates to those owners. No research API may generate executable factors, create orders, mutate portfolio/account state, or bypass `BacktestPipeline`.

**Tech Stack:** Python dataclasses, deterministic JSON, pathlib, existing `ExperimentManifestWriter`, existing `ExperimentStore`, pytest, guardrails, mypy.

---

## Domain Gates

Domain fact / invariant:
Research artifacts are evidence and review inputs, not executable trading behavior.

Correct owner or abstraction boundary:
`qts.research.factor_spec` owns the `FactorSpec` schema. `qts.research.factor_spec_store` owns deterministic spec persistence. `qts.research.experiment_recorder` owns manifest-backed run recording. `ResearchSession` only delegates. Backtest evidence continues through `BacktestPipeline` / `BacktestPipelineRunner`; paper/live may only use reviewed strategy/factor code.

Forbidden shortcut:
Do not generate factor Python code, target intents, orders, fills, account state, portfolio state, or a research-only execution path from `FactorIdea`, `FactorSpec`, or recorder inputs.

Required gates / verification:
Focused unit tests, focused integration tests for facade ergonomics, docs updates, platform-freeze class exceptions, source inventory regeneration, `make format`, `make lint`, `make guardrails`, `make typecheck`, `make test-unit`, `make test-integration`, `make test-anchor`, `git diff --check`, and code-review-graph refresh/review.

## Scope

In scope for this branch:

- Persist, list, load, and round-trip `FactorSpec` drafts under the research store.
- Add `ResearchSession.save_factor_spec(...)`, `save_factor_specs(...)`, `list_factor_specs(...)`, and `load_factor_spec(...)`.
- Add `ResearchExperimentRecorder` with deterministic manifest writing and store indexing.
- Add `ResearchSession.start_experiment(...)`.
- Update docs and generated source inventory.

Out of scope for this branch:

- Factor implementation generation.
- Factor scoring from `FactorSpec`.
- Lookahead, walk-forward, cost/capacity, or liquidity audit gates.
- A vectorized research-only backtest engine.

## Acceptance Criteria

- `FactorSpecStore.save(...)` writes deterministic JSON to `<research store>/factor-specs/<spec name>.json`.
- `FactorSpecStore.list_specs()` returns persisted specs sorted by name.
- `FactorSpecStore.load(name)` round-trips through `FactorSpec.from_payload(...)`.
- `ResearchSession` exposes the store operations without changing the existing backtest/optimizer path.
- `ResearchExperimentRecorder.finalize(...)` writes an `ExperimentManifest` and indexes it in `ExperimentStore`.
- Recorder context manager finalizes on clean exit and does not record failed experiments on exception.
- Recorder metrics, params/config, artifact hashes, dataset ids, and factor versions appear in the manifest/store record.
- No new API imports runtime, execution, risk, paper/live broker adapters, or account/portfolio mutation boundaries.
- Docs explain that persisted specs and recorder manifests are research evidence only.

## Verification Evidence

Record exact outputs before completion:

- [x] `uv run pytest tests/unit/research/test_factor_spec_store.py -q`
- [x] `uv run pytest tests/unit/research/test_experiment_recorder.py -q`
- [x] `uv run pytest tests/unit/research/test_research_session.py tests/unit/research/test_factor_spec.py -q`
- [x] `uv run pytest tests/integration/test_research_session_facade.py -q`
- [x] `uv run pytest tests/unit/test_backtest_live_parallel_sequence_html.py tests/unit/test_project_panorama_html.py -q`
- [x] `make format`
- [x] `make lint`
- [x] `make guardrails`
- [x] `make typecheck`
- [x] `make test-unit`
- [x] `make test-integration`
- [x] `make test-anchor`
- [x] `git diff --check`
- [x] code-review-graph `build_or_update_graph_tool`
- [x] code-review-graph `detect_changes_tool`
- [x] code-review-graph `get_affected_flows_tool`

## File Structure

- Create `backend/src/qts/research/factor_spec_store.py`
  - Owns deterministic `FactorSpec` persistence.
  - Public classes: `FactorSpecStore`.
- Create `backend/src/qts/research/experiment_recorder.py`
  - Owns notebook-friendly manifest-backed experiment recording.
  - Public classes: `ResearchExperimentRecorderConfig`, `ResearchExperimentRecorder`.
- Modify `backend/src/qts/research/session.py`
  - Add lazy `factor_specs` owner.
  - Add spec store and recorder facade methods.
- Modify `backend/src/qts/research/__init__.py`
  - Export new public research types.
- Modify `docs/research/factor_spec_v1.md`
  - Document persistence boundary.
- Modify `docs/research/research_session_v1.md`
  - Document session ergonomics and recorder.
- Modify `docs/architecture/platform_freeze_exceptions.yaml`
  - Register new public classes.
- Regenerate `project_panorama.html` and `docs/architecture/backtest_live_parallel_sequence.html`.
- Add `tests/unit/research/test_factor_spec_store.py`.
- Add `tests/unit/research/test_experiment_recorder.py`.
- Modify `tests/unit/research/test_research_session.py`.
- Modify `tests/integration/test_research_session_facade.py`.

## Task 1: FactorSpecStore

**Files:**

- Create: `backend/src/qts/research/factor_spec_store.py`
- Test: `tests/unit/research/test_factor_spec_store.py`
- Modify: `backend/src/qts/research/__init__.py`
- Modify: `docs/architecture/platform_freeze_exceptions.yaml`

- [x] **Step 1: Write failing store tests**

Add tests for:

```python
def test_factor_spec_store_saves_deterministic_json(tmp_path: Path) -> None: ...
def test_factor_spec_store_lists_specs_sorted_by_name(tmp_path: Path) -> None: ...
def test_factor_spec_store_load_round_trips_spec(tmp_path: Path) -> None: ...
def test_factor_spec_store_rejects_path_like_names(tmp_path: Path) -> None: ...
def test_factor_spec_store_public_export_is_available() -> None: ...
```

Run:

```bash
uv run pytest tests/unit/research/test_factor_spec_store.py -q
```

Expected red:

```text
ModuleNotFoundError: No module named 'qts.research.factor_spec_store'
```

- [x] **Step 2: Implement `FactorSpecStore`**

Behavior:

- `FactorSpecStore(root_dir: Path)` stores specs in `root_dir / "factor-specs"`.
- `path_for(name: str) -> Path` rejects `/`, `\`, `..`, empty strings, and names ending with `.json` only by normalizing through the raw spec name.
- `save(spec: FactorSpec) -> Path` writes `json.dumps(spec.to_payload(), sort_keys=True, indent=2) + "\n"`.
- `load(name: str) -> FactorSpec` reads the deterministic JSON and calls `FactorSpec.from_payload(...)`.
- `list_specs() -> tuple[FactorSpec, ...]` loads `*.json` sorted lexicographically by filename.

- [x] **Step 3: Export and register**

Export `FactorSpecStore` from `qts.research` and register it in `docs/architecture/platform_freeze_exceptions.yaml` with owner `platform` and expiry `2027-05-20`.

- [x] **Step 4: Verify Task 1**

Run:

```bash
uv run pytest tests/unit/research/test_factor_spec_store.py -q
make guardrails
```

Expected green:

```text
5 passed
Architecture guardrails passed.
```

## Task 2: ResearchExperimentRecorder

**Files:**

- Create: `backend/src/qts/research/experiment_recorder.py`
- Test: `tests/unit/research/test_experiment_recorder.py`
- Modify: `backend/src/qts/research/__init__.py`
- Modify: `docs/architecture/platform_freeze_exceptions.yaml`

- [x] **Step 1: Write failing recorder tests**

Add tests for:

```python
def test_experiment_recorder_finalizes_manifest_and_store_record(tmp_path: Path) -> None: ...
def test_experiment_recorder_context_manager_finalizes_on_clean_exit(tmp_path: Path) -> None: ...
def test_experiment_recorder_does_not_record_failed_context(tmp_path: Path) -> None: ...
def test_experiment_recorder_rejects_empty_required_identity(tmp_path: Path) -> None: ...
def test_experiment_recorder_public_exports_are_available() -> None: ...
```

Run:

```bash
uv run pytest tests/unit/research/test_experiment_recorder.py -q
```

Expected red:

```text
ModuleNotFoundError: No module named 'qts.research.experiment_recorder'
```

- [x] **Step 2: Implement recorder config and recorder**

`ResearchExperimentRecorderConfig` fields:

- `experiment_id: str`
- `strategy_name: str`
- `strategy_version: str`
- `manifest_root: Path`
- `store: ExperimentStore`

`ResearchExperimentRecorder` behavior:

- Constructor accepts config and starts with empty params/config, metrics, factor_versions, dataset_ids, artifact_paths.
- `log_params(params: Mapping[str, Any]) -> None` merges into config payload.
- `log_metrics(metrics: Mapping[str, Any]) -> None` merges metrics.
- `log_metric(name: str, value: Any) -> None` records one metric.
- `log_factor_version(name: str, version: str) -> None` records a factor version.
- `log_dataset_id(dataset_id: str) -> None` appends a unique dataset id.
- `log_artifact(path: Path) -> None` appends an existing artifact path.
- `finalize(recorded_at: datetime | None = None) -> ExperimentStoreRecord` writes an `ExperimentManifest` and records it.
- `__enter__` returns self.
- `__exit__` finalizes only when `exc_type is None`; failed contexts are not recorded.

- [x] **Step 3: Export and register**

Export `ResearchExperimentRecorder` and `ResearchExperimentRecorderConfig`; register both classes in `docs/architecture/platform_freeze_exceptions.yaml`.

- [x] **Step 4: Verify Task 2**

Run:

```bash
uv run pytest tests/unit/research/test_experiment_recorder.py -q
make guardrails
```

Expected green:

```text
5 passed
Architecture guardrails passed.
```

## Task 3: ResearchSession Facade Integration

**Files:**

- Modify: `backend/src/qts/research/session.py`
- Modify: `tests/unit/research/test_research_session.py`
- Modify: `tests/integration/test_research_session_facade.py`

- [x] **Step 1: Write failing session tests**

Add unit tests:

```python
def test_research_session_saves_lists_and_loads_factor_specs(tmp_path: Path) -> None: ...
def test_research_session_start_experiment_records_manifest(tmp_path: Path) -> None: ...
```

Add integration assertion that `session.start_experiment(...)` stores a manifest without changing `run_backtest(...)` behavior.

Run:

```bash
uv run pytest tests/unit/research/test_research_session.py tests/integration/test_research_session_facade.py -q
```

Expected red:

```text
AttributeError: 'ResearchSession' object has no attribute 'save_factor_spec'
```

- [x] **Step 2: Implement session methods**

Add:

- `factor_specs` property returning `FactorSpecStore(self._config.store_root)`.
- `save_factor_spec(spec: FactorSpec) -> Path`.
- `save_factor_specs(specs: Sequence[FactorSpec]) -> tuple[Path, ...]`.
- `list_factor_specs() -> tuple[FactorSpec, ...]`.
- `load_factor_spec(name: str) -> FactorSpec`.
- `start_experiment(experiment_id: str, *, strategy_name: str, strategy_version: str = "1") -> ResearchExperimentRecorder`.

The recorder manifest root must be `self._config.output_root / "experiments"`, and the recorder must use `self._store`.

- [x] **Step 3: Verify Task 3**

Run:

```bash
uv run pytest tests/unit/research/test_research_session.py tests/integration/test_research_session_facade.py -q
```

Expected green.

## Task 4: Docs, Inventory, and Normal Checks

**Files:**

- Modify: `docs/research/factor_spec_v1.md`
- Modify: `docs/research/research_session_v1.md`
- Modify: `project_panorama.html`
- Modify: `docs/architecture/backtest_live_parallel_sequence.html`

- [x] **Step 1: Update docs**

Document:

- factor spec persistence path;
- recorder usage;
- explicit statement that persisted specs and recorder manifests do not create executable behavior;
- official promotion path remains `FactorSpec -> qts.factors -> FactorEvaluation -> ExperimentManifest -> shared backtest path`.

- [x] **Step 2: Regenerate source inventory**

Run:

```bash
uv run python scripts/update_project_panorama_source_index.py --html project_panorama.html
uv run python scripts/update_project_panorama_source_index.py --html docs/architecture/backtest_live_parallel_sequence.html
```

- [x] **Step 3: Verify docs and focused research suite**

Run:

```bash
uv run pytest tests/unit/research -q
uv run pytest tests/unit/test_backtest_live_parallel_sequence_html.py tests/unit/test_project_panorama_html.py -q
```

Expected green.

## Task 5: Final Verification and Evidence

- [x] **Step 1: Run normal checks**

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

Expected green, or exact blocker recorded in this plan.

- [x] **Step 2: Refresh and review code graph**

Run:

```text
build_or_update_graph_tool(full_rebuild=True, postprocess="full")
detect_changes_tool(base="master", detail_level="minimal")
get_affected_flows_tool(base="master")
```

Expected:

- Changed files are restricted to `qts.research`, research tests, docs, and generated inventory.
- Affected flows remain research/backtest facade related.
- No new paper/live/runtime actor path is introduced.

- [x] **Step 3: Commit**

Commit message:

```bash
git commit -m "Add research workbench persistence"
```

## Parallelization Plan

Parallel-capable after the plan is committed:

- Task 1 and Task 2 are independent if workers use disjoint files:
  - Worker A owns `factor_spec_store.py`, `test_factor_spec_store.py`, export additions for `FactorSpecStore`, and its freeze exception entry.
  - Worker B owns `experiment_recorder.py`, `test_experiment_recorder.py`, export additions for recorder types, and their freeze exception entries.

Sequential dependencies:

- Task 3 depends on Task 1 and Task 2.
- Task 4 depends on final public class line numbers and exports.
- Task 5 depends on all implementation and docs changes.

