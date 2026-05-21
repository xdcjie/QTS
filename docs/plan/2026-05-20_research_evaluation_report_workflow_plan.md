# Research Evaluation + Report Workflow Plan

## Goal

Make research usable as a daily strategy research pipeline by adding a
workflow-native factor evaluation step and a deterministic research report step,
without creating a separate research runtime or promotion path.

The target user flow is:

```text
discover candidates
  -> review accepted FactorSpec
  -> implementation gate
  -> evaluate factor evidence
  -> factor tearsheet
  -> backtest
  -> optimize
  -> write research report
```

## Domain Fact / Invariant

Research may produce evidence, manifests, reports, and gate decisions. It must
not generate executable trading behavior, create target intents or orders,
start paper/live runtime, mutate account state, or promote a FactorSpec directly
into paper/live behavior.

## Correct Owner / Boundary

- `qts.research.workflow` owns workflow YAML validation, step orchestration, and
  deterministic step results.
- `qts.research.factor_evaluation` owns per-snapshot factor metrics and JSON
  artifacts.
- `qts.research.tearsheet` owns aggregate factor-evaluation evidence.
- A new research report owner should own deterministic Markdown/JSON report
  serialization.
- `ResearchSession` remains the notebook/CLI facade. It may orchestrate existing
  research owners, but it must not compute bars, factor scores, fills, account
  state, or runtime behavior itself.
- Backtest and optimization continue through `BacktestPipeline` and
  `BacktestPipelineRunner`.

## Forbidden Shortcuts

- Do not add `paper`, `live`, `trade`, `orders`, `broker`, `runtime`, `promote`,
  or `generate_code` workflow behavior.
- Do not make workflow YAML import backtest/runtime/risk/order/account internals.
- Do not compute factor scores from forward returns.
- Do not make reports scrape runtime internals or infer account state.
- Do not make `accepted` FactorSpec mean deployable strategy.

## Target Shape

### New Workflow Steps

Add two workflow step kinds:

```yaml
- id: evaluate
  kind: factor_evaluation
  factor_name: momentum
  factor_version: "1"
  snapshots:
    - as_of: "2026-01-02"
      factor_scores: path/to/scores-2026-01-02.csv
      forward_returns: path/to/returns-2026-01-02.csv
  output_dir: runs/research/evaluations

- id: report
  kind: research_report
  output_path: runs/research/reports/quickstart.md
```

`factor_evaluation` writes one deterministic JSON artifact per snapshot through
`FactorEvaluationArtifactWriter`. `research_report` writes a deterministic
Markdown report summarizing all prior workflow step outputs.

### Report Sections

The first report version should include:

- workflow id and final status;
- candidate discovery count and spec names;
- review gate status and accepted spec names;
- implementation gate status and required modules/strategy;
- factor evaluation artifact paths and core metrics;
- factor tearsheet metrics when present;
- backtest manifest path, processed bars, and trading bars;
- optimizer run count and top ranked results;
- explicit "not promoted to paper/live" note.

## Parallel Execution Plan

### Phase 0: Characterization And Spec Gates

This phase is sequential and should run before parallel implementation.

**Files to inspect**

- `backend/src/qts/research/workflow.py`
- `backend/src/qts/research/session.py`
- `backend/src/qts/research/factor_evaluation.py`
- `backend/src/qts/research/tearsheet.py`
- `docs/research/research_session_v1.md`
- `docs/research/factor_evaluation_v1.md`
- `tests/unit/research/test_research_workflow.py`
- `tests/integration/test_run_research_cli.py`

**Tasks**

1. Confirm existing `FactorEvaluationInput` expects a `FactorResult` plus
   forward returns.
2. Confirm how `FactorResult` and assets are built in existing tests.
3. Confirm current workflow result payload shape.
4. Add failing tests before implementation for both new steps.

**Acceptance**

- A failing unit test demonstrates `factor_evaluation` is currently unsupported.
- A failing unit test demonstrates `research_report` is currently unsupported.
- The tests assert no paper/live/runtime/promotion keys are accepted.

**Evidence**

```bash
uv run pytest tests/unit/research/test_research_workflow.py::test_workflow_runs_factor_evaluation_step -q
uv run pytest tests/unit/research/test_research_workflow.py::test_workflow_writes_research_report_from_prior_steps -q
```

Expected before implementation: both fail because the step kinds are unsupported
or not implemented.

### Phase 1A: Factor Evaluation Workflow Step

This work can run in parallel with Phase 1B after Phase 0 tests are in place.

**Owner**

Subagent A.

**Files**

- Modify: `backend/src/qts/research/workflow.py`
- Modify: `backend/src/qts/research/session.py` only if a facade method is
  needed to keep workflow thin
- Test: `tests/unit/research/test_research_workflow.py`
- Test: `tests/integration/test_run_research_cli.py`
- Docs: `docs/research/research_session_v1.md`

**Design**

Add a `factor_evaluation` workflow step that converts explicit snapshot inputs
into `FactorEvaluationInput`, calls `FactorEvaluation.evaluate(...)`, and writes
artifacts through `FactorEvaluationArtifactWriter`.

The step should support only simple, deterministic CSV/JSON score and return
inputs in v1. Input parsing belongs to a cohesive research-owned adapter or
config helper if the parsing is non-trivial. Workflow orchestration must not
become a general file parser.

**Suggested minimal input contract**

CSV files:

```text
symbol,value
GC,0.8
SI,0.2
```

Forward returns:

```text
symbol,forward_return
GC,0.01
SI,-0.02
```

**Acceptance**

- Step writes one artifact per snapshot.
- Result payload includes artifact paths and metric summaries.
- Multiple snapshots preserve previous factor result for turnover.
- Missing forward returns are recorded in metrics, not silently dropped.
- Step rejects empty snapshots and non-filename-safe factor identities.
- Step remains research-only and imports no runtime/execution/broker/risk/order
  modules.

**Evidence**

```bash
uv run pytest tests/unit/research/test_research_workflow.py::test_workflow_runs_factor_evaluation_step -q
uv run pytest tests/unit/research/test_research_workflow.py::test_factor_evaluation_step_records_turnover_across_snapshots -q
uv run pytest tests/integration/test_run_research_cli.py::test_research_cli_workflow_runs_factor_evaluation_and_tearsheet -q
make guardrails
```

### Phase 1B: Research Report Artifact

This work can run in parallel with Phase 1A. It should consume generic workflow
step results and not depend on the internal implementation of factor evaluation.

**Owner**

Subagent B.

**Files**

- Create: `backend/src/qts/research/report.py`
- Modify: `backend/src/qts/research/__init__.py`
- Modify: `backend/src/qts/research/workflow.py`
- Test: `tests/unit/research/test_research_report.py`
- Test: `tests/unit/research/test_research_workflow.py`
- Docs: `docs/research/research_session_v1.md`
- Architecture exception: `docs/architecture/platform_freeze_exceptions.yaml`

**Design**

Add a deterministic report owner:

```python
ResearchWorkflowReport
ResearchWorkflowReportWriter
```

The writer takes a completed `ResearchWorkflowResult` plus optional output path
and writes Markdown. It should not inspect runtime internals, read manifests
unless paths are already present in step outputs, or recompute metrics.

**Acceptance**

- Report output is byte-stable for the same workflow result.
- Report contains workflow status, step statuses, core outputs, and the
  non-promotion note.
- Report can be invoked as a workflow step after prior steps.
- Report step output includes `report_path`.
- Report writer validates filename/path behavior without creating paths outside
  the configured report location.

**Evidence**

```bash
uv run pytest tests/unit/research/test_research_report.py -q
uv run pytest tests/unit/research/test_research_workflow.py::test_workflow_writes_research_report_from_prior_steps -q
make guardrails
```

### Phase 1C: Workflow CLI Integration

This depends on Phase 1A and Phase 1B and should run after both land.

**Owner**

Subagent C.

**Files**

- Modify: `configs/research/workflows/quickstart.yaml`
- Modify: `tests/integration/test_run_research_cli.py`
- Modify: `docs/research/research_session_v1.md`
- Optional docs: `docs/research/factor_evaluation_v1.md`

**Design**

Extend the quickstart workflow to show the full research evidence path. The
integration test should use temporary fixture score/return files and a temporary
research config so it does not depend on external network calls or persistent
local state.

**Acceptance**

- CLI workflow can run:

```text
review gate passed
implementation gate passed
factor_evaluation passed
factor_tearsheet passed
backtest passed
optimize passed
research_report passed
```

- CLI JSON includes artifact paths for factor evaluation, manifest path for
  backtest, optimizer ranked results, and report path.
- A blocked review or implementation gate still prevents evaluation, backtest,
  optimize, and report steps from running.

**Evidence**

```bash
uv run pytest tests/integration/test_run_research_cli.py::test_research_cli_workflow_runs_full_research_evidence_pipeline -q
uv run pytest tests/integration/test_run_research_cli.py::test_research_cli_workflow_blocks_evidence_steps_after_failed_gate -q
```

### Phase 1D: Architecture And Documentation Gates

This can run partly in parallel with implementation but should be finalized
after Phase 1A-1C.

**Owner**

Subagent D.

**Files**

- Modify: `docs/research/research_session_v1.md`
- Modify: `docs/research/factor_evaluation_v1.md`
- Modify: `docs/architecture/platform_freeze_exceptions.yaml`
- Regenerate if needed:
  - `project_panorama.html`
  - `docs/architecture/backtest_live_parallel_sequence.html`

**Acceptance**

- Docs state the new steps and their non-promotion boundary.
- Platform freeze exceptions include any new report owner classes.
- Generated HTML source inventory is current.
- Guardrails pass.

**Evidence**

```bash
PYTHONPATH=backend/src uv run python scripts/update_project_panorama_source_index.py --html project_panorama.html
PYTHONPATH=backend/src uv run python scripts/update_project_panorama_source_index.py --html docs/architecture/backtest_live_parallel_sequence.html
uv run pytest tests/unit/test_project_panorama_html.py tests/unit/test_backtest_live_parallel_sequence_html.py -q
make guardrails
```

## Dependency Graph

```text
Phase 0
  -> Phase 1A factor_evaluation
  -> Phase 1B research_report

Phase 1A + Phase 1B
  -> Phase 1C CLI integration
  -> Phase 1D docs/architecture finalization

All phases
  -> final verification
  -> commit
  -> merge to master if requested
```

## Subagent Assignment

- Subagent A: factor evaluation workflow step and focused unit tests.
- Subagent B: deterministic research report owner and report workflow step.
- Subagent C: CLI integration and quickstart workflow update.
- Subagent D: documentation, generated HTML inventory, and architecture gates.

Subagents must work on disjoint write sets where possible. `workflow.py` is a
shared file between A and B; avoid simultaneous edits there unless changes are
split by clearly isolated methods and integrated by the parent agent.

## Final Acceptance Criteria

- `workflow` supports `factor_evaluation` and `research_report`.
- The full CLI workflow can run from review/implementation gates through
  evaluation, tearsheet, backtest, optimize, and report.
- Evidence artifacts are deterministic and path-safe.
- Failed review or implementation gates hard-stop all downstream evidence steps.
- No research code imports runtime/execution/broker/risk/order/account internals.
- Docs explain the final user flow and the non-promotion boundary.
- Generated architecture/source inventory docs are current.

## Final Verification Evidence

Run and record:

```bash
uv run pytest tests/unit/research/test_research_workflow.py -q
uv run pytest tests/unit/research/test_research_report.py -q
uv run pytest tests/integration/test_run_research_cli.py -q
uv run pytest tests/unit/research tests/integration/test_research_session_facade.py tests/integration/test_research_session_factor_discovery.py tests/integration/test_run_research_cli.py -q
make format
make lint
make guardrails
make typecheck
make test-unit
make test-integration
make check
git diff --check
```

Before final review, refresh the code graph:

```text
build_or_update_graph_tool(full_rebuild=False, postprocess="minimal")
detect_changes_tool(base="HEAD", changed_files=<changed files>, detail_level="minimal")
```

## Implementation Notes

- Keep TDD strict: write failing tests for each new step before implementation.
- Prefer public behavior tests over private helper tests.
- Use `ResearchSession` only as a facade over research/backtest owners.
- If CSV/JSON input parsing grows beyond a few lines, create a cohesive
  research-owned input adapter instead of putting parsing logic in the runner.
- Do not update paper/live docs unless a research-to-paper checklist is added in
  a later phase.
