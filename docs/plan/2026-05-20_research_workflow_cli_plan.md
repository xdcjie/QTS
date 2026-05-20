# Research Workflow CLI Plan

## Goal

Add a gate-based `research workflow` command that lets users advance common
research work from discovery to candidate review, implementation checks,
backtest, optimization, and evidence comparison without creating a separate
research runtime.

## Architecture

`qts.research.workflow` owns workflow YAML validation, step result payloads, and
the runner. `scripts/run_research.py` remains a thin CLI over `ResearchSession`.
Executable evidence continues through `ResearchSession.run_backtest(...)` and
`ResearchSession.optimize(...)`, which delegate to `BacktestPipeline` and
`BacktestPipelineRunner`.

## Domain Boundary

```text
Domain fact / invariant:
Research workflows may collect evidence and stop/pass gates, but must not
create strategy code, create orders, start paper/live runtime, or promote
factors into tradable behavior.

Correct owner or abstraction boundary:
Workflow config and gate orchestration belong in qts.research.workflow.
Backtest/optimization execution remains owned by BacktestPipeline and
BacktestPipelineRunner via ResearchSession.

Forbidden shortcut:
Do not parse workflow YAML or encode gate semantics in scripts/run_research.py.
Do not add paper/live/trade/promote/generate_code workflow steps.
Do not import runtime actors, broker adapters, risk, order, or account modules
into workflow artifacts.

Required gates / verification:
Unit tests for config/gate validation, CLI integration tests for blocked and
passing workflows, make guardrails, lint, typecheck, unit, and integration tests.
```

## Work Items

1. Add `ResearchWorkflowConfig`, `ResearchWorkflowStepConfig`,
   `ResearchWorkflowResult`, `ResearchWorkflowStepResult`, and
   `ResearchWorkflowRunner`.
2. Support step kinds: `factor_candidates`, `factor_review_gate`,
   `implementation_gate`, `factor_tearsheet`, `backtest`, and `optimize`.
3. Add `workflow` subcommand to `scripts/run_research.py`.
4. Add `configs/research/workflows/quickstart.yaml`.
5. Update research documentation and platform-freeze exceptions.

## Acceptance Criteria

- Workflow YAML with forbidden keys such as `generate_code`, `promote`, `paper`,
  `live`, `broker`, `orders`, `runtime`, or `trade` is rejected.
- A failing `factor_review_gate` returns CLI exit code `1`, emits JSON status
  `blocked`, and does not run later `backtest` steps, even if YAML sets
  `on_fail: continue`.
- `implementation_gate` rejects non-research internal `qts.*` modules before
  importing them, while allowing user strategy modules and research-facing
  `qts.factors.*` / `qts.indicators.*` checks.
- A passing review and implementation gate can run `backtest` and `optimize`,
  returning manifest paths and ranked optimizer results.
- Backtest and optimize steps delegate through `ResearchSession`, not direct
  engine construction.
- `make guardrails` proves research workflow code does not violate architecture
  boundaries.

## Verification Evidence

Record these command results before merging:

```bash
uv run pytest tests/unit/research/test_research_workflow.py -q
uv run pytest tests/integration/test_run_research_cli.py -q
uv run pytest tests/unit/research tests/integration/test_research_session_facade.py tests/integration/test_research_session_factor_discovery.py tests/integration/test_run_research_cli.py -q
make lint
make guardrails
make typecheck
make test-unit
make test-integration
git diff --check
```
