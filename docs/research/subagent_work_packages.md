# Research OS Subagent Work Packages

Use this document to create issue-ready work packages for Research OS workers.
Each package must remain inside its stated scope, avoid reverting other agents'
edits, and report evidence before completion claims.

Every issue should include:

- objective;
- allowed write scope;
- first-principles behavior contract;
- required evidence;
- acceptance criteria;
- required commands;
- risks and follow-up.

## Common Worker Contract

Required Evidence:

- changed files list;
- command output summary with exit status;
- relevant artifact paths, manifest paths, or documentation anchors;
- unresolved risks and follow-up items;
- confirmation that paper/live/production behavior was not enabled unless the
  package is explicitly a promotion package.

Acceptance Criteria:

- the package objective is satisfied within the allowed scope;
- durable rules touched by the package have a gate: test, guardrail, checklist,
  or documented manual review;
- no-lookahead and promotion boundaries are preserved where relevant;
- the final response uses `DONE`, `DONE_WITH_CONCERNS`, `BLOCKED`, or
  `NEEDS_CONTEXT`.

Required Commands:

```bash
git status --short
```

Run the package-specific commands below. For code changes, also run the
repository-required checks named by `AGENTS.md` unless the issue narrows the
verification scope and explains why.

## WP-01: Research OS Workflow Contract

Objective: define the end-to-end Research OS workflow contract for idea intake,
evidence production, validation, and promotion handoff.

Scope: durable research docs and workflow config docs. Do not edit runtime,
broker, risk, order, account, or execution code.

First-principles behavior contract: research artifacts are evidence only; they
must not create trading behavior or paper/live configuration.

Required Evidence:

- documented workflow states and transitions;
- owner for each gate;
- command examples for the canonical research entrypoint;
- promotion boundary reference.

Acceptance Criteria:

- idea, evidence, validation, and promotion handoff are all represented;
- workflow entrypoint matches `FLOW-RESEARCH`;
- forbidden shortcuts are explicit.

Required Commands:

```bash
rg -n "FLOW-RESEARCH|FLOW-PROMOTION|research evidence" docs/research docs/architecture/system_flows.md
```

## WP-02: Idea Governance and Factor Spec Review

Objective: make factor idea intake reviewable before implementation.

Scope: factor spec docs, review docs, research docs, and tests only if the issue
explicitly allows code changes.

First-principles behavior contract: an accepted idea is permission to continue
research, not permission to create executable strategy behavior.

Required Evidence:

- fields required for idea rationale, source, timing, universe, owner, and
  reviewer;
- examples of accepted, rejected, and needs-more-evidence decisions;
- review gate command output or documentation anchor.

Acceptance Criteria:

- generated text and source summaries remain non-executable;
- accepted specs require human review before implementation;
- status vocabulary is deterministic.

Required Commands:

```bash
rg -n "FactorSpec|review|accepted|rejected|needs" docs/research backend/src tests
```

## WP-03: No-Lookahead Factor Protocol

Objective: document and enforce the no-lookahead protocol for factor snapshots,
labels, and evaluation windows.

Scope: factor evaluation docs/tests and research docs. Do not change broker,
runtime, or live paths.

First-principles behavior contract: values unavailable at the factor `as_of`
time cannot influence the score for that time.

Required Evidence:

- declared IS/OOS/report windows;
- feature/label separation;
- visibility time rules for bars and labels;
- regression or anchor evidence where code changes occur.

Acceptance Criteria:

- forward returns are labels only;
- `[start, end)` interval visibility is explicit;
- report-only windows cannot tune earlier choices.

Required Commands:

```bash
rg -n "forward returns|lookahead|\\[start, end\\)|visible" docs/research docs/domain tests
```

## WP-04: Factor Evaluation Artifacts

Objective: ensure factor evaluation artifacts are deterministic, reviewable, and
manifest-friendly.

Scope: factor evaluation docs, artifact writer behavior, and related tests when
code changes are authorized.

First-principles behavior contract: identical factor inputs produce identical
artifact bytes and hashes regardless of caller environment.

Required Evidence:

- sample artifact path and manifest path;
- metric definitions for rank IC, spread, coverage, and turnover;
- deterministic serialization command output.

Acceptance Criteria:

- artifact identity is filename-safe;
- decimals and sorting are deterministic;
- missing symbols are recorded.

Required Commands:

```bash
rg -n "FactorEvaluation|rank IC|coverage|turnover|manifest" docs/research backend/src tests
```

## WP-05: Research Session CLI

Objective: keep `ResearchSession` and `scripts/run_research.py` as thin,
canonical research entrypoints.

Scope: research session docs, CLI docs, and allowed research/session tests.

First-principles behavior contract: the facade may orchestrate research but
must not own reusable data construction, trading behavior, or runtime state.

Required Evidence:

- canonical command examples;
- proof that backtests delegate through the shared backtest pipeline;
- workflow exit-code behavior.

Acceptance Criteria:

- no ad hoc VWAP runner is introduced;
- paper/live runtime is not started;
- CLI remains a thin wrapper over research owners.

Required Commands:

```bash
rg -n "run_research.py|ResearchSession|workflow|BacktestPipeline" docs/research scripts backend/src tests
```

## WP-06: Research Workflow Gates

Objective: make gate-based workflow YAML behavior explicit and reproducible.

Scope: research workflow docs/config docs and workflow tests when code changes
are authorized.

First-principles behavior contract: gates block advancement when required
evidence is absent; they do not silently pass incomplete evidence.

Required Evidence:

- gate list and owner;
- pass/fail behavior;
- blocked-step output examples or tests.

Acceptance Criteria:

- gate thresholds are declared in workflow YAML;
- failed gates exit non-zero where applicable;
- skipped evidence is visible in the report.

Required Commands:

```bash
rg -n "gate|workflow|threshold|blocked|exit" docs/research configs/research backend/src tests
```

## WP-07: Optimizer Validation

Objective: ensure optimizer candidates are validated through completed backtest
manifests and declared windows.

Scope: optimizer validation docs/config docs and optimizer tests when code
changes are authorized.

First-principles behavior contract: optimizer ranking is evidence only and must
not promote candidates automatically.

Required Evidence:

- parameter grid and objective metric;
- train/test or walk-forward windows;
- failure-window veto decisions;
- accepted/rejected candidate summaries.

Acceptance Criteria:

- candidates run through `BacktestPipelineRunner`;
- failed runs are not hidden;
- accepted candidates remain promotion evidence only.

Required Commands:

```bash
rg -n "optimizer|walk-forward|failure|BacktestPipelineRunner|candidate" docs/research configs backend/src tests
```

## WP-08: Backtest Evidence and Trade Diagnostics

Objective: require trade-level diagnostics for executable research evidence.

Scope: backtest evidence docs/report docs and tests when code changes are
authorized.

First-principles behavior contract: aggregate PnL is insufficient; evidence
must explain whether results come from signal, execution assumptions, risk, or
accounting.

Required Evidence:

- order/fill/reject counts;
- exposure and turnover;
- cost/slippage assumptions;
- drawdown and failure-window diagnostics;
- risk and account-state reconciliation.

Acceptance Criteria:

- diagnostics are linked to manifest/report artifacts;
- shared backtest path is preserved;
- known accounting or execution assumptions are stated.

Required Commands:

```bash
rg -n "diagnostic|orders|fills|slippage|drawdown|RiskEngine|AccountActor" docs backend/src tests
```

## WP-09: Ablation Protocol

Objective: make ablation evidence mandatory for durable factor or strategy
claims.

Scope: research docs, report docs, and ablation tests/tools when authorized.

First-principles behavior contract: a candidate is fragile until core
assumptions survive removal or stress.

Required Evidence:

- neutral or no-factor baseline;
- component-removal results;
- cost/slippage stress;
- parameter sensitivity;
- adverse-regime or failure-window slices.

Acceptance Criteria:

- ablation results can reject or qualify a candidate;
- narrow parameter dependence is called out;
- missing ablations are listed as risks.

Required Commands:

```bash
rg -n "ablation|baseline|stress|sensitivity|failure-window" docs/research backend/src tests
```

## WP-10: Experiment Store and Manifest Evidence

Objective: keep research artifacts reproducible through manifests and experiment
records.

Scope: experiment-store docs, manifest docs/tests, and research evidence docs.

First-principles behavior contract: claims must point to immutable evidence, not
ambient notebook state.

Required Evidence:

- experiment ID;
- artifact paths and hashes;
- dataset and factor versions;
- command used to create the record.

Acceptance Criteria:

- records are deterministic and append-only where designed;
- artifact paths resolve from documented roots;
- failed or incomplete records are not reported as accepted evidence.

Required Commands:

```bash
rg -n "ExperimentStore|manifest|artifact|hash|experiment_id" docs/research backend/src tests
```

## WP-11: Research Reporting and Tearsheets

Objective: define deterministic research reports and tearsheets as read-only
evidence.

Scope: research report docs, tearsheet docs/tests, and reporting docs when
authorized.

First-principles behavior contract: reports aggregate completed artifacts; they
must not mutate runtime state or alter completed run behavior.

Required Evidence:

- input artifact list;
- summary metric definitions;
- deterministic output path;
- manifest linkage.

Acceptance Criteria:

- report code is read-only with respect to trading state;
- report-only windows cannot tune the run being reported;
- missing symbols and coverage are visible.

Required Commands:

```bash
rg -n "tearsheet|report|read-only|coverage|missing" docs/research backend/src tests
```

## WP-12: Promotion Packet

Objective: define the packet required before research can be considered for
paper/live operation.

Scope: promotion docs, operations checklist references, and issue templates.

First-principles behavior contract: research evidence != paper/live/production;
promotion requires human review of exact build/config/account/risk/mode.

Required Evidence:

- exact target mode;
- code version and config hashes;
- account, risk profile, and capital limits;
- evidence links and reviewers;
- rollback criteria.

Acceptance Criteria:

- promotion language forbids automatic approval from research, optimizer,
  backtest, or paper evidence;
- human review is explicit;
- Go approval is scoped to exact reviewed inputs.

Required Commands:

```bash
rg -n "research evidence !=|paper/live/production|human review|Go|No-Go" docs/research docs/architecture docs/operations
```

## WP-13: Meta-Research Feedback Loop

Objective: capture process feedback that improves future Research OS gates.

Scope: research docs, decision docs references, and issue templates.

First-principles behavior contract: feedback may improve future gates but must
not rewrite completed evidence or backdate approval.

Required Evidence:

- false-positive or false-negative examples;
- recurring data or workflow gaps;
- proposed gate updates;
- owner and follow-up issue.

Acceptance Criteria:

- feedback is linked to a completed work package or decision;
- gate updates are explicit and reviewable;
- earlier outcomes remain historically accurate.

Required Commands:

```bash
rg -n "meta-research|feedback|false positive|false negative|follow-up" docs/research .github/ISSUE_TEMPLATE
```

## WP-14: Documentation Navigation and Boundaries

Objective: make Research OS documentation discoverable from the repository docs
index without creating tool-specific docs directories.

Scope: `docs/README.md` and `docs/research/*`.

First-principles behavior contract: durable research process documentation
belongs under `docs/research`; agent scratch material does not belong in
committed docs.

Required Evidence:

- updated docs directory boundary;
- links or references to Research OS, work packages, and promotion docs;
- confirmation no unrelated docs were edited.

Acceptance Criteria:

- `docs/README.md` names the `research/` boundary;
- research docs are durable project docs, not temporary agent notes;
- no existing docs outside the allowed scope are modified.

Required Commands:

```bash
rg -n "research/|Research OS|promotion" docs/README.md docs/research
```

## WP-15: Documentation and GitHub Issue Templates

Objective: solidify the Research OS process in durable repository docs and a
GitHub issue template.

Scope: `docs/README.md`, `docs/research/research_os.md`,
`docs/research/subagent_work_packages.md`, `docs/research/promotion.md`, and
`.github/ISSUE_TEMPLATE/research_os_work_package.md`.

First-principles behavior contract: documentation must make evidence gates and
promotion limits enforceable through issue acceptance criteria and required
commands.

Required Evidence:

- Research OS doc covering evidence discipline, idea governance, no-lookahead
  factor protocol, ablation, trade diagnostics, validation gates, promotion
  boundary, and meta-research feedback;
- WP-01..WP-15 work-package entries with objective, scope, required evidence,
  acceptance criteria, and required commands;
- promotion doc stating research evidence is not paper/live/production and
  human review is required;
- issue template requiring evidence, acceptance criteria, behavior contract,
  required commands, and risks/follow-up.

Acceptance Criteria:

- all required strings are discoverable by the verification command;
- no Python code, tests, workflow configs, or out-of-scope docs are edited;
- final status reports files changed, command output summary, and remaining
  risks.

Required Commands:

```bash
rg -n "research evidence !=|research evidence is not|paper/live/production|Acceptance Criteria|Required Evidence" docs/research .github/ISSUE_TEMPLATE docs/README.md
```
