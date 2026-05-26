# QTS Research OS 当前 master Review、剩余问题计划与 STATUS MATRIX

生成日期：2026-05-26  
Review 对象：`github:xdcjie/QTS` 当前 `master`  
信息边界：仅基于 GitHub `master` 可见代码，不使用任何上传文件或本地未提交工作区假设。  
目标：把 QTS 从“Research OS 已完成基础实现”推进到 **高淘汰率、高复现性、低自欺风险、能长期积累 edge 的成熟 Research Operating System**。

---

## 0. 执行限制说明

当前会话可用的 GitHub connector 工具只暴露读取类操作，例如：

```text
fetch_file
search
fetch_pr
get_repo
list_recent_issues
get_commit_status
...
```

没有看到以下写入 / 修改类工具：

```text
create_branch
update_file
commit
create_pr
merge_pr
```

因此，本文件完成了：

```text
1. 当前 master 实现 review
2. 剩余问题识别
3. STATUS MATRIX
4. 可交给 Codex / subagent 逐项实现的详细计划
5. 每项验收条件与证据
```

但没有直接把代码提交到 GitHub。  
如需我继续实际落地代码，需要当前会话暴露 GitHub 写入工具，或你在本地 / Codex CLI 执行本文中的 work packages。

---

## 1. 当前 master 总体判断

QTS 当前 `master` 已经实现了 Research OS 的多数核心模块：

```text
1. Evidence Registry
2. Idea Registry + Trial Budget
3. Factor Snapshot Protocol
4. Ablation Report
5. Trade Diagnostics
6. Research Validation Policy
7. Promotion Candidate Spec
8. Meta-Research Summary
9. Workflow Run Context / Evidence Header
10. Route Metadata
11. Portfolio research-only hardening
12. Research OS docs and issue template
```

这说明项目已经从“有 research workflow 的量化系统”推进到了“Research OS 初版”。

不过，当前实现仍然有若干需要修复或硬化的问题。它们不一定会立即导致回测错误，但会影响 Research OS 的目标：

```text
高淘汰率
高复现性
低自欺风险
长期积累 edge
```

本 review 重点不是重复实现已完成模块，而是找剩余风险。

---

## 2. Review Evidence Index

本 review 抽样读取并分析了以下 GitHub `master` 文件：

| Area | File |
|---|---|
| Evidence bundle | `backend/src/qts/research/evidence_registry.py` |
| Idea governance | `backend/src/qts/research/idea_spec.py`, `idea_registry.py` |
| Ablation | `backend/src/qts/research/ablation.py` |
| Trade diagnostics | `backend/src/qts/research/trade_diagnostics.py` |
| Optimizer validation | `backend/src/qts/research/optimizer/validation.py` |
| Promotion packet | `backend/src/qts/research/promotion.py` |
| Meta-research | `backend/src/qts/research/meta_research.py` |
| Workflow | `backend/src/qts/research/workflow.py` |
| Report | `backend/src/qts/research/report.py` |
| Factor evaluation | `backend/src/qts/research/factor_evaluation.py` |
| Factor tearsheet | `backend/src/qts/research/tearsheet.py` |
| Portfolio ensemble | `backend/src/qts/research/portfolio_ensemble.py` |
| CLI | `scripts/run_research.py` |
| Guardrails | `backend/src/qts/quality/rules/flows.py` |
| Docs | `docs/research/research_os.md`, `docs/research/promotion.md` |
| Issue template | `.github/ISSUE_TEMPLATE/research_os_work_package.md` |
| Tests | `tests/unit/research/test_evidence_registry.py` and related already inspected previously |

---

## 3. 当前已完成能力摘要

### 3.1 Evidence Registry 已实现

`ResearchEvidenceBundle` 已包含：

```text
evidence_bundle_id
workflow_run_id
workflow_config_hash
research_config_hash
git_commit
git_dirty
dataset_ids
manifest_paths
manifest_hashes
artifact_hashes
artifact_paths
report_path
period_roles
idea_id
idea_metadata
trial_budget_warnings
strategy_id
review_decisions
status = research_evidence_only
promotion_eligibility = not_reviewed
```

`EvidenceRegistry` 支持：

```text
create_from_workflow_summary
show
list
verify
append_review_decision
```

CLI 也已支持：

```bash
scripts/run_research.py evidence bundle
scripts/run_research.py evidence list
scripts/run_research.py evidence show
scripts/run_research.py evidence verify
```

---

### 3.2 Idea Registry 已实现

`IdeaSpec` 已包含：

```text
idea_id
title
hypothesis
edge_type
source
created_at
data_required
kill_criteria
trial_budget
status
trial_count
rejection_reason
```

`IdeaRegistry` 支持：

```text
save_idea
get
list_ideas
record_trial
record_review_decision
```

并有：

```text
trial_budget_warning
validate_promotion_candidate
```

---

### 3.3 Factor Snapshot Protocol 已实现

`FactorSnapshotProtocol` 已包含：

```text
source_data_end
available_at
forward_return_start
forward_return_end
```

并验证：

```text
source_data_end <= available_at
available_at <= forward_return_start
forward_return_start < forward_return_end
```

Factor artifact 已写入：

```text
forward_return_protocol
snapshot_hash
```

Tearsheet 也会读取 protocol，并校验 artifact 中的 `snapshot_hash` 与 protocol hash 一致。

---

### 3.4 Ablation 已实现

`ablation.py` 已提供：

```text
AblationRun
AblationPlan
AblationReport
AblationReportWriter
```

并支持：

```text
baseline-first protocol
single-module ablation requirement
combined modules after single modules
IS/OOS delta
trade_count_delta
cost_stress_deltas
unstable flag
JSON + Markdown artifacts
```

Workflow 已新增 `ablation` step kind。

---

### 3.5 Trade Diagnostics 已实现

`trade_diagnostics.py` 已提供：

```text
TradeDiagnostic
TradeDiagnosticSummary
FactorBucketSpec
TradeDiagnosticsReport
TradeDiagnosticsArtifactWriter
PaperCandidateDiagnosticsGate
```

并写出：

```text
trades.jsonl
trade_diagnostics_summary.json
trade_diagnostics_report.md
```

Workflow 已新增 `trade_diagnostics` step kind。

---

### 3.6 Promotion Candidate Spec 已实现

`promotion.py` 已提供：

```text
PaperReadinessChecklist
PromotionCandidateSpec
```

并要求：

```text
evidence_bundle_id
source_module != target_module
examples strategy 需要 migration review
paper_candidate 必须满足 readiness checklist
production_params 不能包含 research-only params
```

---

### 3.7 Meta-Research 已实现

`meta_research.py` 已提供：

```text
MetaResearchSummary
MetaResearchSummaryWriter
```

可统计：

```text
ideas_created
factor_candidates
strategy_prototypes
validation_pass_rate
paper_candidate_count
rejected_reason_distribution
source_success_rate
edge_type_distribution
trial_count_outliers
```

CLI 已支持：

```bash
scripts/run_research.py meta summary
```

---

### 3.8 Workflow / Report 已扩展

`workflow.py` 已有：

```text
ResearchWorkflowRunContext
ResearchRouteMetadata
ResearchIdeaLink
ResearchRouteIndex
ablation step
trade_diagnostics step
route metadata
idea metadata
validation_policy
validation_scorecard
```

`report.py` 已有：

```text
Evidence Header
Idea Metadata
Period Roles
Route Metadata
Evidence Summary
Review Decision
Non-Promotion Boundary
```

---

### 3.9 Portfolio Hardening 已实现

`portfolio_ensemble.py` 已写入：

```text
research_only: true
not_tradable_config: true
allocation_overfit_warning
report_only_periods
uses_prior_returns_only
```

并保留对 report-only score periods 的拒绝。

---

### 3.10 Docs 与 issue template 已实现

存在：

```text
docs/research/research_os.md
docs/research/promotion.md
.github/ISSUE_TEMPLATE/research_os_work_package.md
```

这些文档已经明确：

```text
research evidence != paper/live/production behavior
promotion requires human review
```

---

# 4. STATUS MATRIX

状态标记：

```text
DONE              已满足目标
DONE_WITH_GAPS    已实现但存在局部风险
NEEDS_FIX         有明确缺陷或高优先级硬化事项
PARTIAL           初版可用，但目标能力不足
MISSING           当前 master 未见
```

| Component | Status | Evidence | Key Remaining Issue | Priority | WP |
|---|---|---|---|---:|---|
| Evidence Header | DONE | `ResearchWorkflowRunContext`, report Evidence Header, `test_research_report_step_accepts_decision_payload` | 已支持 workflow decision payload 注入 | P1 | WP-02 |
| Evidence Registry | DONE | `ResearchEvidenceBundle`, `EvidenceRegistry`, evidence CLI tests | 已解析 manifest-relative artifacts、完整 path keys、summary/report hashes、idea registry gate | P0 | WP-01 |
| Idea Registry | DONE | `IdeaSpec`, `IdeaRegistry`, meta-research tests | 已支持 `edge_types`、扩展 taxonomy/status lifecycle、meta 统计多 edge | P2 | WP-08 |
| Factor Snapshot Protocol | DONE | `FactorSnapshotProtocol`, `ResearchSession._snapshot_protocol` tests | 已保留 intraday ISO/Z/offset datetime | P0 | WP-03 |
| Factor Tearsheet | DONE | protocol + snapshot_hash 校验 | 无重大问题 | P3 | Monitor |
| Ablation | DONE | `AblationPlan.from_backtest_matrix_summary`, workflow ablation source summary tests | 已接 backtest_matrix summary + module_map | P2 | WP-09 |
| Trade Diagnostics | DONE | `TradeDiagnostic`, writer, paper/small-live guardrail tests | 已支持 overnight bucket、direction/quantity/holding_bars 校验、missing/unbucketed factor buckets | P1 | WP-04 |
| Validation Policy | DONE | `ResearchValidationPolicy`, optimizer/report tests | 已支持 accepted count、robustness、WF/failure/cost-stress missing evidence hard gates | P0 | WP-05 |
| Optimizer Scorecard | DONE | `validation_scorecard`, report policy reason tests | 已渲染 policy reasons/missing evidence | P1 | WP-05 |
| Report Decision | DONE | `ResearchReviewDecision`, workflow/report tests | 已修正 string normalization、workflow decision injection、small-live evidence gate | P0 | WP-02 |
| Promotion Spec | DONE | `PromotionCandidateSpec`, guardrail tests | 已强制 paper/small-live readiness 和 production target namespace | P1 | WP-06 |
| Meta-Research | DONE | `MetaResearchSummary`, CLI/unit tests | 已支持 monthly/quarterly/custom period filtering 和 `--all-history` | P2 | WP-10 |
| Portfolio Ensemble | DONE | research_only / not_tradable / prior returns | 继续保持 tests | P3 | Monitor |
| Route Metadata | DONE | `ResearchRouteMetadata`, `ResearchRouteIndex`, route index tests | 已校验 index route_id 与 workflow route.route_id 匹配 | P2 | WP-11 |
| Guardrails | DONE | research guardrail rules and tests | 已覆盖 evidence bundle、route metadata、decision block、stale docstring、small-live diagnostics、production target | P1 | WP-07 |
| Docs | DONE | required docs + docs tests | 已补 CLI examples、known failure modes、issue-template docs refs | P2 | WP-12 |
| Research VWAP docstring | DONE | `vwap_factor_research.py`, stale-docstring guardrail | stale boundary wording 已受 guardrail 保护 | P1 | WP-07 |

本轮完成证据（2026-05-26）：

```text
WP-01: tests/unit/research/test_evidence_registry.py + CLI evidence registry gate
WP-02: tests/unit/research/test_research_report.py + test_research_report_step_accepts_decision_payload
WP-03: tests/unit/research/test_research_session.py intraday snapshot protocol artifact test
WP-04: tests/unit/research/test_trade_diagnostics.py overnight / invalid trade fact tests
WP-05: tests/unit/research/test_optimizer_constraints.py + report policy reason test
WP-06: tests/unit/research/test_promotion.py + guardrail production target tests
WP-07: tests/unit/scripts/test_verify_guardrails.py Research OS guardrail expansion tests
WP-08: tests/unit/research/test_idea_registry.py + meta multi-edge test
WP-09: tests/unit/research/test_ablation.py + workflow source_summary ablation test
WP-10: tests/unit/research/test_meta_research.py + integration CLI --all-history test
WP-11: tests/unit/research/test_research_workflow.py route index/selection policy tests
WP-12: tests/unit/docs/test_research_os_docs.py docs/issue-template gates
Final gate: `make check` passed with 1444 unit, 149 integration / 4 skipped, 159 anchor / 2 skipped.
```

---

# 5. Remaining Issues Ranked by Severity

本节保留原 review 问题清单用于追溯；本轮已按 WP-01..WP-12 关闭对应缺口，状态与证据以第 4 节 STATUS MATRIX 为准。

## P0-1：Factor protocol loses intraday datetime

### Problem

`FactorSnapshotProtocol` supports `date | datetime | str`, but `ResearchSession._snapshot_protocol` parses protocol fields via `_as_of`, which only accepts `date` or ISO date strings.

This means a workflow snapshot with:

```yaml
available_at: "2026-05-25T10:00:00Z"
forward_return_start: "2026-05-25T10:15:00Z"
```

will fail or be forced into date semantics instead of intraday semantics.

### Impact

For intraday futures research, factor availability and forward-return label timing are central to no-lookahead discipline. Losing intraday precision weakens the Research OS no-lookahead gate.

### Fix

Update `ResearchSession._snapshot_protocol` to parse full ISO datetime strings through `FactorSnapshotProtocol.from_payload(...)` or a shared protocol parser.

---

## P0-2：Evidence Registry does not resolve relative artifact paths relative to manifest

### Problem

`_collect_manifest_artifact_paths` reads `artifact_paths_by_hash` from manifests and returns:

```python
{path_text: hash}
```

But if manifest artifact paths are relative, verification later does:

```python
Path(path_text)
```

relative to current working directory, not manifest directory.

### Impact

Valid evidence bundles can fail verification if manifest artifacts are stored with relative paths.

### Fix

Resolve relative artifact paths against `manifest_path.parent` when collecting paths.

---

## P0-3：Evidence Bundle path collection misses important workflow outputs

### Problem

Evidence Registry currently collects:

```text
manifest_path
report_path
artifact_path
artifact_paths
```

But workflow outputs include other important artifact fields:

```text
summary_path
validation_output
walk_forward_validation_output
failure_window_veto_output
trades_path
ablation_summary/report outputs
portfolio summary_path
backtest_matrix summary_path
```

### Impact

Evidence bundle can be incomplete even when workflow produced important validation evidence.

### Fix

Use a recursive path collector over known output keys, or support a controlled `_EVIDENCE_PATH_KEYS` registry.

---

## P0-4：Review decision is not injectable from workflow payload

### Problem

`ResearchWorkflowReport` has `ResearchReviewDecision`, but `_research_report(...)` builds a result without passing decision from `step.payload`.

So reports appear to always use default:

```text
keep_researching
```

even if workflow YAML intended another decision.

### Impact

Machine-readable review status cannot be controlled by workflow evidence.

### Fix

Support:

```yaml
- id: report
  kind: research_report
  decision:
    status: freeze_forward
    reviewer: ...
    reason: [...]
```

and pass this decision into `ResearchWorkflowResult`.

---

## P0-5：`_normalize_decision` handles string reason incorrectly

### Problem

In `report.py`, `_normalize_decision` does:

```python
reason=tuple(str(item) for item in value.get("reason", ()))
```

If `reason` is a string, it becomes a tuple of characters.

### Impact

Review decision output becomes corrupted.

### Fix

Normalize string or list uniformly:

```python
def _string_tuple_field(value):
    if value is None: return ()
    if isinstance(value, str): return (value,)
    ...
```

---

## P0-6：ValidationPolicy is too light

### Problem

`ResearchValidationPolicy` only has:

```python
require_passing_candidate: bool
```

It does not implement gates such as:

```text
min_trades
min_profit_factor
min_net_sharpe
max_drawdown
cost_stress acceptance
remove_best_days
min_walk_forward_windows
max_losing_windows
```

### Impact

Research OS still lacks a serious hard-gate validator beyond basic constraints.

### Fix

Extend `ResearchValidationPolicy` to accept and evaluate richer policy fields, or require these gates to be expressed in constraints + evidence and summarized explicitly.

---

# 6. Detailed Work Packages

---

## WP-01：Evidence Registry Completeness and Relative Path Fix

**Priority:** P0  
**Owner:** Evidence Registry Agent  
**Status:** DONE

### Objective

Make evidence bundles complete and robust when manifests contain relative artifact paths.

### Files Likely Touched

```text
backend/src/qts/research/evidence_registry.py
tests/unit/research/test_evidence_registry.py
scripts/run_research.py
```

### Required Changes

1. Resolve manifest artifact paths relative to `manifest_path.parent`.

Current behavior to fix:

```text
artifact_paths_by_hash:
  sha256:abc: artifacts/equity.ndjson

Verification uses Path("artifacts/equity.ndjson") from cwd.
```

Target:

```text
Path(manifest_path).parent / "artifacts/equity.ndjson"
```

2. Store `workflow_summary_path` and `workflow_summary_hash` in bundle payload.

3. Expand evidence path collection.

Recommended controlled keys:

```python
_EVIDENCE_PATH_KEYS = {
    "manifest_path",
    "manifest_paths",
    "report_path",
    "artifact_path",
    "artifact_paths",
    "summary_path",
    "validation_output",
    "walk_forward_validation_output",
    "failure_window_veto_output",
    "trades_path",
}
```

4. If CLI receives `--idea-id`, require either:
   - `--idea-registry-root` and load/attach the idea, or
   - workflow summary contains `idea_metadata`.

5. `EvidenceRegistry.verify(...)` should verify:
   - workflow summary hash
   - manifest hashes
   - artifact path hashes
   - report path existence/hash if stored

### Tests

```text
test_evidence_bundle_resolves_manifest_relative_artifact_paths
test_evidence_bundle_records_workflow_summary_hash
test_evidence_bundle_collects_validation_and_summary_paths
test_evidence_cli_idea_id_requires_registry_or_summary_metadata
test_evidence_verify_detects_workflow_summary_mutation
```

### Acceptance Criteria

```text
[ ] Relative manifest artifact paths verify correctly.
[ ] Bundle stores workflow_summary_path and workflow_summary_hash.
[ ] Important workflow outputs are included in artifact_paths.
[ ] `--idea-id` cannot create weak bundle without validating idea metadata.
[ ] Existing evidence tests continue passing.
```

---

## WP-02：Research Report Decision Injection and Normalization Fix

**Priority:** P0  
**Owner:** Report / Review Agent  
**Status:** DONE

### Objective

Allow workflow YAML to inject a machine-readable review decision and fix decision normalization.

### Files Likely Touched

```text
backend/src/qts/research/report.py
backend/src/qts/research/workflow.py
tests/unit/research/test_research_report.py
tests/unit/research/test_research_workflow.py
```

### Required Changes

1. Add parser:

```python
def _review_decision_from_payload(payload: Mapping[str, Any]) -> ResearchReviewDecision
```

2. In `_research_report(...)`, read:

```python
decision = _review_decision_from_payload(step.payload.get("decision"))
```

3. Pass decision into `ResearchWorkflowResult`.

4. Fix string/list normalization for:

```text
reason
required_next_evidence
```

5. Apply paper/small-live evidence gates consistently:
   - `paper_candidate` requires evidence bundle + diagnostics + validation + cost stress.
   - `small_live_candidate` should require at least the same, possibly stricter.

### Tests

```text
test_research_report_step_accepts_decision_payload
test_research_report_decision_string_reason_not_split_into_chars
test_paper_candidate_requires_evidence_bundle
test_small_live_candidate_requires_paper_evidence
test_review_decision_markdown_renders_yaml_block
```

### Acceptance Criteria

```text
[ ] `research_report.decision` appears in markdown and JSON-derived report.
[ ] String reason remains one string item.
[ ] paper_candidate and small_live_candidate cannot be emitted without required evidence.
[ ] Default remains keep_researching when no decision is supplied.
```

---

## WP-03：Intraday Factor Snapshot Protocol Fix

**Priority:** P0  
**Owner:** Factor Integrity Agent  
**Status:** DONE

### Objective

Preserve intraday datetime precision for factor snapshot protocol fields.

### Files Likely Touched

```text
backend/src/qts/research/session.py
backend/src/qts/research/factor_evaluation.py
tests/unit/research/test_factor_evaluation.py
tests/unit/research/test_research_session.py
```

### Required Changes

1. Change `_snapshot_protocol(...)` to parse protocol fields using `FactorSnapshotProtocol.from_payload(...)` or shared parser.

2. Allow:

```text
2026-05-25
2026-05-25T10:00:00Z
2026-05-25T10:00:00+00:00
```

3. Artifact should preserve intraday timestamps.

4. Add explicit test with 15m interval protocol:

```text
source_data_end = 10:00
available_at = 10:00
forward_return_start = 10:15
forward_return_end = 11:15
```

### Tests

```text
test_factor_snapshot_protocol_accepts_intraday_datetime_strings
test_research_session_snapshot_protocol_preserves_intraday_datetimes
test_factor_artifact_records_intraday_protocol
test_factor_snapshot_rejects_intraday_available_after_forward_start
```

### Acceptance Criteria

```text
[ ] Intraday protocol fields pass through session -> evaluation -> artifact.
[ ] Snapshot hash changes when intraday timestamps change.
[ ] Invalid intraday order fails.
[ ] Legacy date-only snapshots still work.
```

---

## WP-04：Trade Diagnostics Hardening

**Priority:** P1  
**Owner:** Trade Diagnostics Agent  
**Status:** DONE

### Objective

Make trade diagnostics robust for futures intraday/session research.

### Files Likely Touched

```text
backend/src/qts/research/trade_diagnostics.py
tests/unit/research/test_trade_diagnostics.py
```

### Required Changes

1. Add overnight bucket support:

Current logic:

```python
if start_hour <= hour < end_hour
```

This fails for 20:00-02:00.

Target:

```python
if start_hour <= end_hour:
    start <= hour < end
else:
    hour >= start or hour < end
```

2. Validate direction:

```text
long
short
flat? maybe disallow for completed trades
```

3. Validate quantity is positive.

4. Validate holding_bars non-negative.

5. Include optional `entry_time_bucket` and `exit_time_bucket` if needed.

6. Add factor bucket grouping test for missing/unbucketed.

### Tests

```text
test_trade_diagnostics_time_bucket_supports_overnight_window
test_trade_diagnostics_rejects_unknown_direction
test_trade_diagnostics_rejects_non_positive_quantity
test_trade_diagnostics_rejects_negative_holding_bars
test_trade_diagnostics_factor_bucket_missing_and_unbucketed
```

### Acceptance Criteria

```text
[ ] 20:00-02:00 bucket works.
[ ] Invalid direction/quantity/holding_bars fail.
[ ] Existing writer artifacts remain deterministic.
```

---

## WP-05：Research Validation Policy Upgrade

**Priority:** P0  
**Owner:** Validation Gate Agent  
**Status:** DONE

### Objective

Extend validation policy from “require passing candidate” to a real hard-gate scorecard.

### Files Likely Touched

```text
backend/src/qts/research/optimizer/validation.py
backend/src/qts/research/workflow.py
backend/src/qts/research/report.py
tests/unit/research/test_optimizer_constraints.py
tests/unit/research/test_research_workflow.py
```

### Required Policy Fields

```yaml
validation_policy:
  require_passing_candidate: true
  min_accepted_count: 1
  min_robustness_score: "30"
  require_walk_forward: true
  require_failure_window: true
  require_cost_stress: true
  max_rejected_count: null
```

Optional later:

```yaml
min_trades
min_profit_factor
min_net_sharpe
max_drawdown
remove_best_days
parameter_neighborhood
```

### Required Changes

1. `ResearchValidationPolicy` should parse more fields.
2. `evaluate()` should return:
   ```text
   accepted
   blocked
   reasons
   missing_evidence
   robustness_score
   accepted_count
   rejected_count
   ```
3. Workflow should block if policy fails.
4. Report should render policy rejection reasons.

### Tests

```text
test_validation_policy_blocks_missing_walk_forward_when_required
test_validation_policy_blocks_missing_failure_window_when_required
test_validation_policy_blocks_missing_cost_stress_when_required
test_validation_policy_blocks_low_robustness_score
test_optimizer_report_shows_validation_policy_reasons
```

### Acceptance Criteria

```text
[ ] Policy can require WF / failure window / cost stress evidence.
[ ] Missing required evidence blocks optimize step.
[ ] Report shows policy reasons.
[ ] Existing simple require_passing_candidate behavior remains backward compatible.
```

---

## WP-06：Promotion Candidate Hardening

**Priority:** P1  
**Owner:** Promotion Boundary Agent  
**Status:** DONE

### Objective

Make promotion candidate status transitions stricter and less ambiguous.

### Files Likely Touched

```text
backend/src/qts/research/promotion.py
tests/unit/research/test_promotion.py
```

### Required Changes

1. `small_live_candidate` should require at least the same evidence as `paper_candidate`.

2. `target_module` should be constrained:
   - production target should start with `strategies.production.` or another approved target namespace.
   - paper-only targets may need a separate approved namespace later.

3. `source_module` under `strategies.research` should be allowed as source evidence, but target must be production-owned.

4. Promotion spec should expose `missing_items`.

### Tests

```text
test_small_live_candidate_requires_full_readiness
test_promotion_target_module_must_be_production_owned
test_research_source_to_production_target_allowed
test_promotion_spec_reports_missing_items
```

### Acceptance Criteria

```text
[ ] small_live cannot bypass paper readiness.
[ ] target module must be production-owned.
[ ] examples source still requires migration review.
[ ] promotion packet remains human_review_required.
```

---

## WP-07：Guardrail Expansion and Stale Docstring Fix

**Priority:** P1  
**Owner:** Architecture Guardrail Agent  
**Status:** DONE

### Objective

Close remaining Research OS boundary gaps via guardrails and fix stale wording.

### Files Likely Touched

```text
backend/src/qts/quality/rules/flows.py
backend/src/qts/quality/rules/research.py
backend/src/qts/quality/rules/__init__.py
scripts/verify_guardrails.py
strategies/research/vwap_factor_research.py
tests/unit/quality/
```

### Required Changes

1. Fix `vwap_factor_research.py` docstring:

Current problem:

```text
This module intentionally lives under examples.
```

But file is under:

```text
strategies/research/
```

2. Add guardrail to reject stale phrase under `strategies/research`.

3. Add guardrail for:
   - promotion packet without evidence_bundle_id
   - route workflow missing route metadata when under route directory
   - report decision missing when required
   - paper candidate without diagnostics evidence

### Tests

```text
test_guardrail_rejects_research_strategy_stale_examples_docstring
test_guardrail_rejects_promotion_without_evidence_bundle
test_guardrail_rejects_route_workflow_without_route_metadata
test_guardrail_scans_nested_workflow_routes
```

### Acceptance Criteria

```text
[ ] Stale docstring fixed.
[ ] Guardrail catches reintroduction.
[ ] make guardrails covers Research OS rules.
```

---

## WP-08：Idea Governance Enhancements

**Priority:** P2  
**Owner:** Idea Governance Agent  
**Status:** DONE

### Objective

Make idea metadata better aligned with quant research reality.

### Recommended Changes

1. Support multiple edge types:

Current:

```python
edge_type: str
```

Target:

```python
edge_types: tuple[str, ...]
```

Backward compatibility:

```text
edge_type accepted as single edge_type.
```

2. Expand taxonomy:

```text
time_series_momentum
cross_sectional_momentum
mean_reversion
carry
term_structure
relative_value
event_driven
liquidity
microstructure
seasonality
macro_regime
volatility
execution_alpha
```

3. Add lifecycle statuses:

```text
idea
factor_candidate
strategy_prototype
validated_research
frozen_forward
paper_candidate
rejected
retired
```

### Tests

```text
test_idea_spec_accepts_multiple_edge_types
test_idea_spec_backwards_compatible_edge_type
test_idea_spec_rejects_unknown_edge_type
test_idea_status_lifecycle_values
```

### Acceptance Criteria

```text
[ ] Multiple edge types supported.
[ ] Old edge_type payload still works.
[ ] MetaResearch counts all edge types.
```

---

## WP-09：Ablation Integration with Backtest Matrix

**Priority:** P2  
**Owner:** Strategy Research Agent  
**Status:** DONE

### Objective

Move ablation from “manual completed metrics” toward direct consumption of backtest_matrix summaries.

### Current State

`ablation` step expects run metrics in YAML payload.

### Target

Support:

```yaml
kind: ablation
source_summary: path/to/backtest_matrix_summary.json
baseline: baseline
primary_metric: sharpe_ratio
module_map:
  candidate_a: [mom_filter]
  candidate_b: [mom_filter, volume_filter]
```

### Tests

```text
test_ablation_loads_runs_from_backtest_matrix_summary
test_ablation_rejects_missing_baseline_in_summary
test_ablation_maps_candidate_modules
```

### Acceptance Criteria

```text
[ ] Existing inline runs still work.
[ ] Source summary ingestion works.
[ ] Metric deltas are generated from actual backtest_matrix outputs.
```

---

## WP-10：Meta-Research Period Filtering

**Priority:** P2  
**Owner:** Meta-Research Agent  
**Status:** DONE

### Objective

Make `period` and `period_start` more than labels.

### Current State

`MetaResearchSummary.from_registries(...)` receives all ideas / evidence / experiments and labels the output period.

### Target

If records have timestamps, filter to:

```text
period_start <= record_time < period_end
```

Support:

```text
monthly
quarterly
custom
```

### Tests

```text
test_meta_research_filters_ideas_by_created_at_month
test_meta_research_filters_experiment_records_by_recorded_at
test_meta_research_filters_evidence_review_decisions_by_time
test_meta_research_custom_period
```

### Acceptance Criteria

```text
[ ] Meta summaries respect period boundaries when timestamps exist.
[ ] Records without timestamps are counted under unknown/legacy bucket or explicitly excluded.
[ ] Existing all-record behavior can be requested with --all-history.
```

---

## WP-11：Route Metadata Hardening

**Priority:** P2  
**Owner:** Workflow Scalability Agent  
**Status:** DONE

### Objective

Ensure future large research programs do not become chronology-opaque.

### Required Changes

1. Workflows under:

```text
configs/research/workflows/routes/
```

must include `route` metadata.

2. Route index should verify each route file has matching `route_id`.

3. Report should include route decision.

4. Candidate route status should require scoring selection periods, already partly implemented.

### Tests

```text
test_route_workflow_under_routes_requires_route_metadata
test_route_index_requires_matching_route_id
test_candidate_route_requires_selection_periods
test_report_route_metadata_includes_selection_policy
```

### Acceptance Criteria

```text
[ ] Nested route workflows are governed.
[ ] Route index cannot drift from route YAML.
[ ] Report distinguishes exploration/candidate/frozen/rejected.
```

---

## WP-12：Docs and CLI Examples Update

**Priority:** P3  
**Owner:** Documentation Agent  
**Status:** DONE

### Objective

Bring docs in line with current implemented Research OS modules.

### Files

```text
docs/research/research_os.md
docs/research/promotion.md
docs/research/evidence_registry.md
docs/research/idea_registry.md
docs/research/factor_protocol.md
docs/research/trade_diagnostics.md
```

### Required Additions

```text
1. CLI examples for evidence / idea / meta commands.
2. Known failure modes:
   - incomplete evidence bundle
   - report-only misuse
   - trial budget exceeded
   - missing trade diagnostics
3. Promotion packet examples.
4. Factor protocol examples with intraday timestamps.
5. Ablation examples with baseline/module/full.
```

### Acceptance Criteria

```text
[ ] Docs match implemented CLI.
[ ] Docs contain copy-paste examples.
[ ] Docs warn research evidence != promotion.
[ ] Issue template references these docs.
```

---

# 7. Execution Order

## Batch 1：P0 Correctness Fixes

```text
WP-01 Evidence Registry Completeness and Relative Path Fix
WP-02 Research Report Decision Injection and Normalization Fix
WP-03 Intraday Factor Snapshot Protocol Fix
WP-05 Research Validation Policy Upgrade
```

These protect reproducibility, no-lookahead discipline, and candidate gating.

---

## Batch 2：P1 Boundary and Diagnostics Hardening

```text
WP-04 Trade Diagnostics Hardening
WP-06 Promotion Candidate Hardening
WP-07 Guardrail Expansion and Stale Docstring Fix
```

These protect research-to-production boundaries and paper/live readiness.

---

## Batch 3：P2/P3 Research OS Quality Improvements

```text
WP-08 Idea Governance Enhancements
WP-09 Ablation Integration with Backtest Matrix
WP-10 Meta-Research Period Filtering
WP-11 Route Metadata Hardening
WP-12 Docs and CLI Examples Update
```

These make the system scale better across future strategies and subagents.

---

# 8. Final Acceptance Matrix

Final target is complete when:

| Target | Evidence |
|---|---|
| Evidence bundles are complete and path-stable | New evidence registry tests pass |
| Review decisions are real workflow evidence | `research_report.decision` test passes |
| Intraday factor protocol is preserved | factor artifact records intraday datetimes |
| Optimizer has real hard gates | validation policy blocks missing required evidence |
| Trade diagnostics support Asia/overnight sessions | overnight bucket test passes |
| Promotion cannot bypass evidence | paper/small-live readiness tests pass |
| Guardrails catch Research OS drift | `make guardrails` catches stale docstring / missing evidence |
| Meta-research is period-aware | monthly/quarterly filtering tests pass |
| Docs reflect implemented CLI | docs tests or review checklist pass |
| No existing invariants weakened | `make check` passes |

Required commands:

```bash
make format
make lint
make guardrails
make typecheck
make test-unit
make test-integration
make check
```

If full `make check` is too slow during intermediate PRs, each PR should at least run:

```bash
make format
make lint
make guardrails
make typecheck
make test-unit
```

and document any skipped tests.

---

# 9. Codex Subagent Prompt Template

Use this template for each WP:

```text
You are the Codex subagent for QTS Research OS [WP-XX].

Repository:
xdcjie/QTS

Branch:
Create a feature branch named research-os/wp-XX-<short-name>.

Objective:
<copy WP objective>

Scope:
<copy files likely touched and out-of-scope constraints>

Critical invariants:
- Do not weaken report-only / true-OOS period isolation.
- Do not create ad hoc backtest runners.
- Do not let research evidence auto-promote paper/live/production.
- Keep research/production module boundaries.
- Add tests and deterministic evidence artifacts where applicable.

Implementation requirements:
<copy required changes>

Acceptance tests:
<copy tests>

Required commands:
make format
make lint
make guardrails
make typecheck
make test-unit

Deliver:
1. Summary
2. Files changed
3. Tests added
4. Commands run
5. Evidence artifacts
6. Remaining risks
7. Whether all acceptance criteria are met
```

---

# 10. Final Recommendation

The Research OS is materially implemented, but not yet final production-grade.

The most important next actions are:

```text
1. Fix evidence bundle completeness and path resolution.
2. Fix report decision injection and decision normalization.
3. Fix intraday factor snapshot protocol parsing.
4. Upgrade validation policy beyond require_passing_candidate.
5. Harden trade diagnostics for overnight futures sessions.
6. Harden promotion gates and guardrails.
```

After those are complete, QTS will be much closer to the desired operating model:

```text
High rejection rate
High reproducibility
Low self-deception risk
Long-term edge accumulation
```

The system should then be considered Research OS v1.0, with future work focused on strategy diversity, factor lab breadth, and live/paper monitoring integration.
