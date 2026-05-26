# QTS Quant Research Operating System：GitHub-Only Review 与多 Subagent 推进计划

生成日期：2026-05-25  
Review 对象：`github:xdcjie/QTS`，默认分支：`master`  
信息边界：**本文件仅基于 GitHub `xdcjie/QTS` 当前 `master` 可见实现生成，不使用任何上传的 QTS Research System Brief 或本地未提交工作区假设。**

---

## 1. Executive Summary

基于 GitHub `master` 的 review，QTS 已经具备一个专业量化 Research Operating System 的重要基础：

```text
1. Research workflow 有 schema 化 step kind 和 period role。
2. Workflow config 会拒绝 report-only / true-OOS period 进入 scoring / selection fields。
3. Optimizer 已经支持 validation summary、walk-forward、failure-window veto。
4. Portfolio ensemble 明确是 research-only，并对 holdout score period 做拒绝。
5. Report writer 已经输出 Period Roles 和 Non-Promotion Boundary。
6. Experiment manifest 已经记录 config hash、dataset ids、artifact hashes、metrics。
7. Guardrails 已经覆盖 ad hoc research runner、VWAP optimizer shortcut、production import research/examples、research workflow runtime keys。
8. Production VWAP strategy 与 research VWAP strategy 有代码边界，production 不继承 research strategy。
9. Makefile 已经提供 format / lint / guardrails / typecheck / test-unit / test-integration / check 等标准命令。
```

但要把 QTS 建设成一个 **高淘汰率、高复现性、低自欺风险、能长期积累 edge 的研究操作系统**，还缺以下系统能力：

```text
A. Evidence Bundle Registry
   当前有 experiment manifest，但没有 workflow/candidate 层级 evidence bundle。

B. Idea Registry + Trial Budget
   当前看不到 idea-level source、hypothesis、edge taxonomy、trial_count、kill criteria。

C. Factor Snapshot No-Lookahead Protocol
   FactorEvaluation 有 rank IC / long-short / coverage / turnover，但 snapshot/forward return 时间协议不够完整。

D. Strategy Ablation Protocol
   当前没有标准化 baseline + module ablation + delta report。

E. Trade-Level Diagnostics Standard
   当前没有全局强制的 trades.jsonl/parquet、R_pnl、MAE/MFE、exit_reason、factor bucket 诊断协议。

F. Promotion Candidate Spec
   当前 report 有 non-promotion boundary，guardrail 也防止 production import research/examples；但没有 machine-readable promotion review spec。

G. Meta-Research Dashboard
   当前没有 idea/source/edge-type/pass-rate/rejection-reason/trial-count 的长期复盘系统。

H. Route Metadata / Research Program Structure
   GitHub master 中没有看到 route-level workflow index；若未来 research workflow 增大，需要 route_id/status/selection_policy。
```

因此，推荐的推进方向不是继续扩展策略数量，而是优先建立：

```text
Evidence discipline
Idea governance
No-lookahead factor protocol
Ablation discipline
Trade-level diagnostics
Validation hard gates
Promotion boundary
Meta-research feedback loop
```

---

## 2. GitHub Master Evidence Index

以下是本 review 使用的 GitHub `master` 可见证据。

| Evidence Area | GitHub Path | Observed Capability |
|---|---|---|
| Workflow orchestration | `backend/src/qts/research/workflow.py` | `ResearchWorkflowConfig`、`ResearchWorkflowRunner`、allowed step kinds、period roles、report-only rejection、optimizer / backtest_matrix / portfolio workflow steps |
| Report writer | `backend/src/qts/research/report.py` | deterministic markdown report、Evidence Summary、Period Roles、Non-Promotion Boundary |
| Experiment manifest | `backend/src/qts/research/experiment_manifest.py` | experiment_id、strategy_name、strategy_version、factor_versions、dataset_ids、config_hash、artifact_hashes、metrics |
| Factor evaluation | `backend/src/qts/research/factor_evaluation.py` | FactorEvaluationInput、rank IC、long-short spread、coverage、turnover、deterministic artifact writer |
| Portfolio ensemble | `backend/src/qts/research/portfolio_ensemble.py` | research-only static allocation scan、volatility-managed allocation scan、holdout score rejection、prior returns weighting logic |
| Research CLI | `scripts/run_research.py` | `factor-tearsheet`、`runs`、`workflow` commands |
| Guardrails | `scripts/verify_guardrails.py`, `backend/src/qts/quality/rules/flows.py` | ResearchRunScriptRule、VwapOptimizerConfigRule、ProductionStrategyImportRule、ResearchWorkflowRuntimeKeyRule |
| Research VWAP strategy | `strategies/research/vwap_factor_research.py` | research-only VWAP pullback harness with broad parameter/filter surface |
| Production VWAP strategy | `strategies/production/vwap_production_pullback.py` | production-facing stable VWAP pullback classes/configs, independent of research strategy |
| Workflow tests | `tests/unit/research/test_research_workflow.py` | period-role, report-only, walk-forward, failure-window, matrix validation tests |
| Report tests | `tests/unit/research/test_research_report.py` | report stability, optimizer capital metrics, period roles rendering |
| Portfolio tests | `tests/unit/research/test_portfolio_ensemble.py` | research-only portfolio, holdout rejection, vol-managed prior returns behavior |
| Production strategy tests | `tests/unit/strategies/test_vwap_regime_pullback.py` | production config checks and no subclass dependency on research strategy |
| Make targets | `Makefile` | `format`, `lint`, `guardrails`, `typecheck`, `test-unit`, `test-integration`, `check`, etc. |

---

## 3. Research OS Target Architecture

目标架构：

```text
Idea Registry
  -> Factor Lab
    -> Minimal Strategy Lab
      -> Strategy Ablation
        -> Validation Lab
          -> Portfolio Lab
            -> Evidence Bundle Registry
              -> Human Promotion Review
                -> Paper / Small Live / Production
                  -> Monitoring / Drift / Kill Switch
                    -> Meta-Research Feedback
```

核心机制：

```text
1. Idea 层：
   每个研究必须有来源、机制假设、edge taxonomy、data requirement、kill criteria、trial budget。

2. Factor 层：
   先 cheap test：bucket、forward return、MAE/MFE、decay、interaction，再进入 strategy。

3. Strategy 层：
   先 minimal baseline，再 ablation。每个 filter / sizing / exit 必须证明增量贡献。

4. Validation 层：
   OOS、walk-forward、failure windows、cost stress、remove-best-days、parameter neighborhood。

5. Portfolio 层：
   只看 portfolio contribution，不允许 holdout / true-OOS 反向参与 allocation selection。

6. Evidence 层：
   所有结论必须引用 evidence_bundle_id，而不是复制 PnL 数字。

7. Promotion 层：
   research artifact 只进入人工 review，不自动 paper/live/production。

8. Meta 层：
   每月/季度统计 idea pass rate、trial count、false positive、rejection reason。
```

---

## 4. STATUS MATRIX

状态标记：

```text
DONE / STRONG       已实现且有清晰测试或代码证据
PARTIAL             已有基础，但不够完整
MISSING             GitHub master 未看到实现
NEEDS HARDENING     有实现，但 Research OS 化需要加强
REVIEW REQUIRED     需要结合更多 repo 文件或未来 PR 再确认
```

| Area | Current Status | Evidence from GitHub Master | Gap / Risk | Target State | Work Package |
|---|---|---|---|---|---|
| Workflow allowed step kinds | DONE / STRONG | `_ALLOWED_STEP_KINDS` 限定 research step kinds | 新增 step 需持续受控 | 所有新增 step 必须 schema + tests | WP-13 |
| Forbidden workflow runtime keys | DONE / STRONG | `_FORBIDDEN_WORKFLOW_KEYS` + `ResearchWorkflowRuntimeKeyRule` | 需要确保未来 nested workflow dirs 也扫描 | 递归扫描 all workflow dirs | WP-13 |
| Period role schema | DONE / STRONG | `anchor / selection / validation / holdout_report_only / true_oos_report_only` | 无 frozen_forward / repair_selection 等细分 role | 先保持精简，在 evidence bundle 记录 freeze boundary | WP-01 / WP-02 |
| Report-only 不进 scoring | DONE / STRONG | `_reject_report_only_period_names` 与 workflow tests | 新增 scoring fields 可能漏注册 | 统一 decision-bearing fields registry | WP-13 |
| Backtest matrix period validation | DONE / STRONG | `backtest_matrix.periods` 需要声明 role，且不可覆盖声明边界 | summary 仍需进入 evidence bundle | matrix summary 作为 bundle artifact | WP-02 |
| Optimizer walk-forward overlap guard | DONE / STRONG | report-only overlap validation tests | 还需进入 validation scorecard | hard-gate scorecard | WP-07 |
| Failure-window veto | PARTIAL / STRONG | `require_passing_candidate` 可 block workflow | workflow 可能选择仅 report-only evidence，不形成 hard gate | ResearchValidationPolicy 标准化 | WP-07 |
| Report Period Roles | DONE | report 输出 Period Roles 表 | 缺 git/config/data/hash evidence header | Evidence Header | WP-01 |
| Report Non-Promotion Boundary | DONE / PARTIAL | report footer 声明 research evidence only | 缺 machine-readable decision block | Review Decision Template | WP-14 |
| Workflow result metadata | PARTIAL | `to_payload` 输出 periods、report_only_periods、selection_basis | 缺 workflow_config_hash、research_config_hash、git context | Run context metadata | WP-01 |
| Experiment manifest | PARTIAL / STRONG | 记录 config_hash、artifact_hashes、dataset_ids、metrics | 缺 workflow run / period roles / review decision / promotion eligibility | Evidence Bundle Registry | WP-02 |
| Evidence registry | MISSING | 未见 `ResearchEvidenceBundle` 或 evidence CLI | evidence 分散，promotion review 无统一引用对象 | bundle + index + verify CLI | WP-02 |
| Idea registry | MISSING | 未见 idea_id / hypothesis / edge taxonomy / trial budget | round-based research 容易 data-snooping | IdeaSpec + TrialBudget | WP-03 |
| Trial budget | MISSING | 未见 per-idea trial count | 参数搜索越多，自欺风险越高 | trial warning / promotion penalty | WP-03 |
| Factor evaluation metrics | DONE / PARTIAL | rank IC、long-short、coverage、turnover | 缺 snapshot timing protocol | no-lookahead protocol | WP-04 |
| Factor artifact metadata | PARTIAL | deterministic JSON artifact | 缺 snapshot_hash / forward_return_protocol | factor protocol metadata | WP-04 |
| Strategy research harness | DONE / NEEDS GOVERNANCE | VWAP research config parameter surface 很广 | 参数多，必须 ablation + trial budget | ablation discipline | WP-05 |
| Research strategy docstring | NEEDS HARDENING | `vwap_factor_research.py` docstring 说 lives under examples，但路径是 strategies/research | 文档漂移 | 修正文档，强化 research-only 声明 | WP-10 / WP-13 |
| Trade-level diagnostics | MISSING / PARTIAL | 未见统一 trade diagnostics schema | 无法系统定位 DD 来源 | trades artifact + report | WP-06 |
| Strategy ablation | MISSING | 未见 AblationPlan / delta report | filter 堆叠不可审计 | baseline + module ablation | WP-05 |
| Optimizer hard gates | PARTIAL | constraints / validation summary / WF / veto 已有 | 缺统一 ResearchValidationPolicy、accepted_rank/rejected reasons report | robustness scorecard | WP-07 |
| Portfolio static allocation scan | DONE / NEEDS HARDENING | `research_only: true`，reject report-only score periods | artifact 缺 not_tradable_config / overfit warning | stronger portfolio artifact | WP-09 |
| Vol-managed no-lookahead | DONE / NEEDS HARDENING | weights use history before return_index，tests cover prior returns | artifact 未显式写 `uses_prior_returns_only` | explicit artifact flag | WP-09 |
| Research-to-production boundary | DONE / PARTIAL | production strategy independent, guardrail rejects production imports from research/examples | 缺 PromotionCandidateSpec + evidence_bundle requirement | formal promotion gate | WP-10 |
| Examples promotion boundary | PARTIAL | production import examples 被 guardrail 禁止 | examples strategy 若成为 candidate 需迁移/review | examples cannot directly promote | WP-10 |
| Guardrail suite | DONE / PARTIAL | `verify_guardrails.py` integrates flow guardrails | 缺 evidence/idea/promotion/route metadata specific guards | expand guardrails | WP-13 |
| CLI | PARTIAL | supports `factor-tearsheet`, `runs`, `workflow` | 缺 evidence / idea / meta commands | CLI extension | WP-02 / WP-03 / WP-12 |
| Route metadata | MISSING | GitHub master 未见 route index / route metadata | future workflow expansion may obscure chronology | route_id/status/selection_policy | WP-08 |
| Meta-research | MISSING | 未见 monthly/quarterly research statistics | 无法长期学习 research process quality | Meta dashboard | WP-12 |
| Make targets | DONE / STRONG | Makefile has format/lint/guardrails/typecheck/test-unit/test-integration/check | Work packages 应统一使用 | global DoD commands | All WPs |

---

# 5. Subagent Work Packages

---

## WP-01：Workflow Run Context & Evidence Header

**Subagent**：Evidence Report Agent  
**Priority**：P0  
**Current Status**：PARTIAL  
**Depends On**：None

### Objective

在 workflow result 和 markdown report 中加入完整 evidence header：

```text
workflow_config_path
workflow_config_hash
research_config_path
research_config_hash
git_branch
git_commit
git_dirty
dataset_ids
backtest_config_hash
generated_at
```

当前 report 已有 Period Roles 和 Non-Promotion Boundary，但缺少 run context。

### Scope

In scope：

```text
- deterministic config hashing
- git metadata capture
- workflow result run_context
- markdown Evidence Header
- CLI JSON 输出 run_context
```

Out of scope：

```text
- 不实现 evidence bundle registry
- 不改变策略回测逻辑
```

### Likely Files

```text
backend/src/qts/research/workflow.py
backend/src/qts/research/report.py
backend/src/qts/research/session.py
scripts/run_research.py
tests/unit/research/test_research_workflow.py
tests/unit/research/test_research_report.py
tests/integration/test_run_research_cli.py
```

### Implementation Tasks

```text
1. 新增 ResearchWorkflowRunContext dataclass。
2. ResearchWorkflowRunner.run 构造或接收 run_context。
3. ResearchWorkflowResult.to_payload 输出 run_context。
4. ResearchWorkflowReport 接收 run_context 并渲染 Evidence Header。
5. CLI workflow JSON 输出 run_context。
6. 缺少 git command 或非 git 环境时记录 unknown，而不是静默省略。
```

### Required Evidence

Report 示例：

```markdown
## Evidence Header

- Repository: xdcjie/QTS
- Workflow config: configs/research/workflows/...
- Workflow config hash: sha256:...
- Research config: configs/research/...
- Research config hash: sha256:...
- Git branch: master
- Git commit: ...
- Dirty workspace: true/false/unknown
- Dataset IDs: [...]
- Backtest config hash: sha256:...
- Promotion status: research_only
```

Tests：

```text
test_workflow_summary_contains_run_context
test_research_report_contains_evidence_header
test_report_marks_dirty_workspace_explicitly
test_run_context_config_hash_is_deterministic
test_run_context_survives_missing_git_metadata
```

### Acceptance Criteria

```text
[ ] Workflow JSON payload includes run_context.
[ ] Markdown report includes Evidence Header.
[ ] Dirty workspace state is explicit.
[ ] Config hash is deterministic.
[ ] Existing report tests still pass with updated snapshot expectations.
```

---

## WP-02：Research Evidence Bundle Registry

**Subagent**：Evidence Registry Agent  
**Priority**：P0  
**Current Status**：MISSING  
**Depends On**：WP-01

### Objective

建立 candidate/workflow 层级 evidence bundle，作为 promotion review 的唯一引用对象。

当前 `ExperimentManifestWriter` 是单 experiment 层级；Research OS 需要更高层聚合：

```text
workflow summary
manifest paths
report path
period roles
config hashes
dataset ids
artifact hashes
review decision
promotion eligibility
```

### Scope

In scope：

```text
- ResearchEvidenceBundle
- EvidenceRegistry
- evidence index JSONL
- evidence verify
- CLI create/list/show/verify
```

Out of scope：

```text
- 不自动 promotion
- 不创建 paper/live config
```

### Likely Files

```text
backend/src/qts/research/evidence_registry.py
backend/src/qts/research/experiment_store.py
backend/src/qts/research/experiment_manifest.py
scripts/run_research.py
tests/unit/research/test_evidence_registry.py
tests/integration/test_run_research_cli.py
```

### Bundle Schema

```json
{
  "evidence_bundle_id": "evb_...",
  "status": "research_evidence_only",
  "promotion_eligibility": "not_reviewed",
  "idea_id": null,
  "strategy_id": null,
  "workflow_run_id": "...",
  "workflow_config_hash": "sha256:...",
  "research_config_hash": "sha256:...",
  "git_commit": "...",
  "git_dirty": false,
  "dataset_ids": [],
  "manifest_paths": [],
  "manifest_hashes": [],
  "artifact_hashes": {},
  "report_path": "...",
  "period_roles": {},
  "review_decision": null
}
```

### CLI

```bash
PYTHONPATH=backend/src uv run python scripts/run_research.py \
  --config configs/research/quickstart.yaml \
  evidence bundle --workflow-summary <path>

PYTHONPATH=backend/src uv run python scripts/run_research.py evidence list
PYTHONPATH=backend/src uv run python scripts/run_research.py evidence show <bundle_id>
PYTHONPATH=backend/src uv run python scripts/run_research.py evidence verify <bundle_id>
```

### Required Evidence

Artifacts：

```text
runs/research/evidence/index.jsonl
runs/research/evidence/evidence-bundle-<id>.json
```

Tests：

```text
test_evidence_bundle_created_from_workflow_summary
test_evidence_bundle_verifies_manifest_hashes
test_evidence_bundle_missing_artifact_fails
test_evidence_cli_list_show_verify
test_evidence_bundle_never_sets_paper_live_production_status
```

### Acceptance Criteria

```text
[ ] Evidence bundle can be created from workflow summary.
[ ] All referenced artifact/manifest paths exist or verification fails.
[ ] All hashes can be recomputed.
[ ] Bundle status cannot be paper/live/production.
[ ] Promotion review must cite evidence_bundle_id.
```

---

## WP-03：Idea Registry + Trial Budget

**Subagent**：Idea Governance Agent  
**Priority**：P1  
**Current Status**：MISSING  
**Depends On**：WP-02

### Objective

建立 idea-level governance，让每个 research candidate 都有机制假设、来源、edge taxonomy、trial count 和 kill criteria。

### Scope

In scope：

```text
- IdeaSpec schema
- idea registry YAML / JSONL
- experiment -> idea_id linkage
- trial_count update
- trial_budget warning
- report/evidence bundle display idea metadata
```

Out of scope：

```text
- 不评价策略好坏
- 不自动 reject
```

### Likely Files

```text
backend/src/qts/research/idea_spec.py
backend/src/qts/research/idea_registry.py
backend/src/qts/research/experiment_recorder.py
backend/src/qts/research/report.py
scripts/run_research.py
tests/unit/research/test_idea_registry.py
tests/unit/research/test_experiment_recorder.py
```

### IdeaSpec Example

```yaml
idea_id: gc_asia_vwap_continuation_v1
status: active_research
source: internal_diagnostic
edge_type:
  - session_effect
  - time_series_momentum
  - liquidity
hypothesis: >
  If GC accepts one side of session VWAP during Asia session and rejects a VWAP pullback with volume confirmation,
  short-horizon continuation probability is higher than random.
mechanism:
  - session liquidity transfer
  - VWAP as session cost anchor
  - trend continuation after pullback
data_required:
  - GC 15m OHLCV
  - session VWAP
  - ATR
  - volume ratio
kill_criteria:
  - no_parameter_neighborhood
  - oos_net_sharpe_below_0_8
  - cost_2x_negative
trial_budget:
  max_strategy_trials: 30
  max_validation_variants: 5
current_trial_count: 0
```

### Required Evidence

Artifacts：

```text
registry/idea_registry.yaml
runs/research/idea_registry/index.jsonl
```

Tests：

```text
test_idea_registry_requires_hypothesis
test_idea_registry_rejects_unknown_edge_type
test_experiment_increments_idea_trial_count
test_report_warns_when_trial_budget_exceeded
test_promotion_candidate_requires_idea_id
```

### Acceptance Criteria

```text
[ ] Every strategy research run can optionally link to idea_id.
[ ] Trial count increments deterministically.
[ ] Exceeding trial budget emits warning in report/evidence.
[ ] Idea without hypothesis cannot enter promotion review.
[ ] Edge taxonomy is a controlled enum.
```

---

## WP-04：Factor Snapshot No-Lookahead Protocol

**Subagent**：Factor Integrity Agent  
**Priority**：P1  
**Current Status**：PARTIAL  
**Depends On**：WP-01

### Objective

给 factor score / forward return snapshot 建立明确的 no-lookahead protocol。

当前 FactorEvaluationInput 有 `as_of`、factor_result、forward_returns，但不足以证明：

```text
source_data_end <= available_at <= forward_return_start < forward_return_end
```

### Scope

In scope：

```text
- FactorSnapshotProtocol
- available_at
- source_data_end
- forward_return_start
- forward_return_end
- snapshot_hash
- artifact protocol metadata
- preflight validation
```

Out of scope：

```text
- 不改 factor discovery economics
- 不要求所有历史 artifact 回填
```

### Likely Files

```text
backend/src/qts/research/factor_evaluation.py
backend/src/qts/research/tearsheet.py
backend/src/qts/research/factor_spec.py
tests/unit/research/test_factor_evaluation.py
tests/unit/research/test_tearsheet.py
```

### Required Protocol

```text
source_data_end <= available_at
available_at <= forward_return_start
forward_return_start < forward_return_end
factor values do not use forward_return window
```

### Artifact Example

```json
{
  "as_of": "2026-05-25",
  "factor_name": "mom120",
  "factor_version": "v1",
  "snapshot_hash": "sha256:...",
  "forward_return_protocol": {
    "horizon": "4bar",
    "source_data_end": "2026-05-25T10:00:00Z",
    "available_at": "2026-05-25T10:00:00Z",
    "forward_return_start": "2026-05-25T10:15:00Z",
    "forward_return_end": "2026-05-25T11:15:00Z",
    "no_overlap_verified": true
  },
  "metrics": {}
}
```

### Required Evidence

Tests：

```text
test_factor_snapshot_rejects_source_data_after_available_at
test_factor_snapshot_rejects_available_at_after_forward_start
test_factor_snapshot_rejects_forward_window_overlap
test_factor_artifact_records_snapshot_hash
test_factor_tearsheet_preserves_forward_protocol
```

### Acceptance Criteria

```text
[ ] Future-leaked snapshot fails validation.
[ ] Factor artifact includes snapshot_hash.
[ ] Factor artifact includes forward_return_protocol.
[ ] Tearsheets preserve protocol metadata.
[ ] Factor evaluation output cannot omit timing protocol for new artifacts.
```

---

## WP-05：Strategy Lab Ablation Protocol

**Subagent**：Strategy Research Agent  
**Priority**：P1  
**Current Status**：MISSING  
**Depends On**：WP-03

### Objective

把 strategy research 标准化为：

```text
minimal baseline
+ individual module ablation
+ combined modules
+ delta report
```

### Scope

In scope：

```text
- AblationPlan schema
- baseline + module variants
- metric delta vs baseline
- IS/OOS delta
- trade count delta
- cost stress delta
- report section
```

Out of scope：

```text
- 不保证策略通过
- 不自动选择 production
```

### Likely Files

```text
backend/src/qts/research/ablation.py
backend/src/qts/research/workflow.py
backend/src/qts/research/report.py
configs/research/workflows/*ablation*.yaml
tests/unit/research/test_ablation.py
tests/unit/research/test_research_workflow.py
```

### AblationPlan Example

```yaml
ablation_id: vwap_pullback_research_ablation
base_candidate: baseline
modules:
  - name: momentum_filter
    strategy_params:
      factor_filters: [mom120_aligned]
  - name: volume_confirmation
    strategy_params:
      min_volume_ratio: "1.3"
  - name: range_filter
    strategy_params:
      range_expansion_max: "1.50"
order:
  - baseline
  - baseline+momentum_filter
  - baseline+momentum_filter+volume_confirmation
  - full
```

### Required Evidence

Artifacts：

```text
runs/research/<strategy>/ablation/summary.json
runs/research/<strategy>/ablation/report.md
```

Summary Example：

```json
{
  "baseline": {
    "net_sharpe": "0.82",
    "max_drawdown": "0.12",
    "trade_count": 118
  },
  "baseline_plus_momentum_filter": {
    "net_sharpe": "1.05",
    "delta_net_sharpe": "0.23",
    "delta_max_drawdown": "-0.03",
    "trade_count_delta": -42
  }
}
```

Tests：

```text
test_ablation_plan_requires_baseline
test_ablation_report_shows_metric_deltas
test_ablation_flags_is_only_improvement
test_ablation_summary_records_trade_count_delta
```

### Acceptance Criteria

```text
[ ] Each module has visible incremental contribution.
[ ] Report cannot show only final full combo.
[ ] IS-only improvement is marked unstable.
[ ] Ablation summary can enter evidence bundle.
```

---

## WP-06：Trade-Level Diagnostics Standard

**Subagent**：Trade Diagnostics Agent  
**Priority**：P1  
**Current Status**：MISSING / PARTIAL  
**Depends On**：WP-05

### Objective

所有 strategy research 必须输出标准交易级诊断，而不是只看 aggregate Sharpe / DD。

### Scope

In scope：

```text
- trades.jsonl or trades.parquet schema
- R_pnl
- MAE_R
- MFE_R
- exit_reason
- holding_bars
- time_bucket
- quantity bucket
- factor snapshot at entry
- diagnostics report
```

Out of scope：

```text
- 不重写 backtest engine
- 不依赖 live fills
```

### Likely Files

```text
backend/src/qts/research/trade_diagnostics.py
backend/src/qts/research/report.py
backend/src/qts/reporting/
strategies/research/vwap_factor_research.py
tests/unit/research/test_trade_diagnostics.py
tests/unit/strategies/test_vwap_factor_research.py
```

### Trade Schema Example

```json
{
  "trade_id": "...",
  "strategy_id": "...",
  "idea_id": "...",
  "symbol": "GC",
  "direction": "long",
  "quantity": "4",
  "entry_time": "...",
  "exit_time": "...",
  "entry_price": "...",
  "exit_price": "...",
  "R_pnl": "...",
  "MAE_R": "...",
  "MFE_R": "...",
  "holding_bars": 4,
  "exit_reason": "target_r_touched",
  "time_bucket": "20:00-22:00",
  "factor_snapshot": {
    "mom120": "...",
    "range_expansion": "...",
    "volume_ratio": "...",
    "session_sigma_atr": "..."
  }
}
```

### Required Evidence

Artifacts：

```text
runs/research/<strategy>/diagnostics/trades.jsonl
runs/research/<strategy>/diagnostics/trade_diagnostics_summary.json
runs/research/<strategy>/diagnostics/trade_diagnostics_report.md
```

Tests：

```text
test_trade_diagnostics_requires_r_pnl_mae_mfe
test_trade_diagnostics_groups_by_exit_reason
test_trade_diagnostics_groups_by_time_bucket
test_trade_diagnostics_groups_by_quantity
test_missing_trade_diagnostics_blocks_paper_candidate
```

### Acceptance Criteria

```text
[ ] Every trade has R_pnl, MAE_R, MFE_R, exit_reason.
[ ] Diagnostics can group by direction, quantity, time bucket, exit reason.
[ ] Diagnostics can group by factor buckets.
[ ] Missing trade diagnostics blocks paper_candidate.
```

---

## WP-07：Optimizer Hard Gates & Robustness Scorecard

**Subagent**：Validation Gate Agent  
**Priority**：P1  
**Current Status**：PARTIAL  
**Depends On**：WP-01, WP-06

### Objective

把 optimizer 从 ranking tool 升级为 candidate gating system。

### Scope

In scope：

```text
- ResearchValidationPolicy
- accepted_rank vs raw_rank
- rejection_reasons
- robustness_score
- cost stress status
- walk-forward status
- failure-window status
```

Out of scope：

```text
- 不自动 paper/live
```

### Likely Files

```text
backend/src/qts/research/optimizer/validation.py
backend/src/qts/research/optimizer/walk_forward.py
backend/src/qts/research/optimizer/failure_veto.py
backend/src/qts/research/report.py
tests/unit/research/test_optimizer_constraints.py
tests/unit/research/test_optimizer_walk_forward.py
tests/unit/research/test_optimizer_failure_veto.py
```

### Policy Example

```yaml
validation_policy:
  min_trades: 50
  min_profit_factor: "1.15"
  min_net_sharpe: "0.80"
  max_drawdown: "0.12"
  min_walk_forward_windows: 3
  max_losing_windows: 1
  cost_stress:
    slippage_multiplier: [1, 2, 3]
  failure_windows:
    require_passing_candidate: true
```

### Required Evidence

Validation Summary Example：

```json
{
  "candidate_id": "run-0017",
  "raw_objective_rank": 2,
  "accepted": false,
  "accepted_rank": null,
  "robustness_score": "61.5",
  "rejection_reasons": [
    "max_drawdown > 0.12",
    "cost_stress_2x_net_pnl < 0",
    "failure_window_2024_failed"
  ]
}
```

Tests：

```text
test_optimizer_blocks_when_no_candidate_passes_hard_gates
test_optimizer_reports_rejection_reasons
test_optimizer_reports_accepted_rank_separate_from_raw_rank
test_cost_stress_failure_rejects_candidate
test_walk_forward_policy_required_for_candidate_status
```

### Acceptance Criteria

```text
[ ] No passing candidate -> workflow step blocked.
[ ] Raw ranking and accepted ranking are separate.
[ ] Report includes rejected candidates and rejection reasons.
[ ] Cost stress status appears in summary.
[ ] Failure-window veto can be configured as hard gate.
```

---

## WP-08：Route Metadata & Research Program Structure

**Subagent**：Workflow Scalability Agent  
**Priority**：P2  
**Current Status**：MISSING  
**Depends On**：WP-01, WP-02

### Objective

为未来大型 research workflow 提供 route-level governance。

GitHub master 没有观察到 route index / route metadata。若未来出现多路线 strategy research，需要避免：

```text
- later route observation influence earlier candidate selection
- exploration/candidate/rejected/frozen status mixed in one huge workflow
- reviewer cannot tell selection chronology
```

### Scope

In scope：

```text
- route_id
- route_name
- route_status
- route_owner
- selection_policy
- allowed_period_roles
- route index
- route report section
```

Out of scope：

```text
- 不要求当前所有 workflow 立刻拆分
```

### Likely Files

```text
backend/src/qts/research/workflow.py
backend/src/qts/research/report.py
configs/research/workflows/routes/*.yaml
configs/research/workflows/research_routes_index.yaml
tests/unit/research/test_research_workflow.py
tests/integration/test_run_research_cli.py
```

### Route Metadata Example

```yaml
route_id: B
route_name: vwap_rolling_dual_supertrend
status: exploration
owner: research
selection_policy:
  selection_periods: [selection_2020_2022]
  validation_periods: [validation_2022_2024]
  report_only_periods: [holdout_2024_2026]
allowed_period_roles:
  - selection
  - validation
  - holdout_report_only
```

### Required Evidence

Tests：

```text
test_route_metadata_required_for_route_workflows
test_route_status_appears_in_report
test_route_index_resolves_all_routes
test_route_report_only_result_cannot_promote_candidate
test_route_order_snapshot
```

### Acceptance Criteria

```text
[ ] Route workflows can declare route metadata.
[ ] Report distinguishes exploration / candidate / rejected / frozen.
[ ] Report-only result cannot change route status to candidate.
[ ] Route index missing file fails.
[ ] Route order has snapshot test.
```

---

## WP-09：Portfolio Lab Hardening

**Subagent**：Portfolio Research Agent  
**Priority**：P2  
**Current Status**：PARTIAL / NEEDS HARDENING  
**Depends On**：WP-01, WP-02

### Objective

加强 portfolio ensemble / allocation scan 的 research-only 语义，防止 allocation research 被误认为 production config。

### Scope

In scope：

```text
- not_tradable_config flag
- explicit score_periods vs report_only_periods
- uses_prior_returns_only flag
- allocation_overfit_warning
- evidence bundle integration
```

Out of scope：

```text
- 不做 live portfolio allocator
```

### Likely Files

```text
backend/src/qts/research/portfolio_ensemble.py
backend/src/qts/research/workflow.py
backend/src/qts/research/report.py
tests/unit/research/test_portfolio_ensemble.py
```

### Artifact Example

```json
{
  "research_only": true,
  "not_tradable_config": true,
  "score_periods": ["anchor", "validation"],
  "report_only_periods": ["holdout_2024_2026"],
  "uses_prior_returns_only": true,
  "allocation_overfit_warning": true
}
```

### Required Evidence

Tests：

```text
test_portfolio_artifact_marks_not_tradable_config
test_portfolio_scan_rejects_holdout_in_all_score_fields
test_vol_managed_artifact_records_prior_returns_only
test_portfolio_report_contains_allocation_overfit_warning
```

### Acceptance Criteria

```text
[ ] Portfolio artifacts always include research_only and not_tradable_config.
[ ] Selection/report-only periods are explicit in artifact.
[ ] Vol-managed scan artifact records uses_prior_returns_only.
[ ] Report clearly states allocation scan is not production allocation.
```

---

## WP-10：Promotion Candidate Spec & Boundary Gate

**Subagent**：Promotion Boundary Agent  
**Priority**：P2  
**Current Status**：PARTIAL  
**Depends On**：WP-02, WP-06, WP-07

### Objective

把 research evidence 到 paper/live/production 的路径固化为 machine-readable PromotionCandidateSpec。

当前 production strategy 与 research strategy 有边界，但缺 formal promotion gate。

### Scope

In scope：

```text
- PromotionCandidateSpec
- evidence_bundle_id requirement
- paper_readiness checklist
- research-only params forbidden
- examples direct promotion forbidden
```

Out of scope：

```text
- 不自动生成 production code
- 不自动创建 broker/live config
```

### Likely Files

```text
backend/src/qts/research/promotion.py
scripts/verify_guardrails.py
strategies/production/
strategies/research/
examples/strategies/
configs/strategies/
docs/research/promotion.md
tests/unit/research/test_promotion.py
tests/unit/strategies/
```

### PromotionCandidateSpec Example

```yaml
promotion_candidate_id: pc_...
strategy_id: ...
source_module: strategies.research.vwap_factor_research
target_module: strategies.production.vwap_production_pullback
evidence_bundle_id: evb_...
status: review_required
paper_readiness:
  evidence_bundle_verified: true
  trade_diagnostics_available: true
  validation_scorecard_available: true
  cost_stress_available: true
  no_research_import_in_production: true
  no_examples_direct_promotion: true
```

### Required Evidence

Tests：

```text
test_promotion_candidate_requires_evidence_bundle
test_promotion_candidate_requires_trade_diagnostics
test_paper_candidate_requires_validation_scorecard
test_production_config_rejects_research_only_params
test_examples_strategy_cannot_be_promotion_candidate_without_migration_review
```

### Acceptance Criteria

```text
[ ] Research artifact cannot auto-promote.
[ ] Promotion spec must cite evidence_bundle_id.
[ ] Paper candidate requires diagnostics / validation / cost stress.
[ ] Production strategy cannot import strategies.research or examples.
[ ] Examples strategy requires migration or explicit review before promotion.
```

---

## WP-11：Research Strategy Documentation Hardening

**Subagent**：Research Boundary Documentation Agent  
**Priority**：P2  
**Current Status**：NEEDS HARDENING  
**Depends On**：WP-10

### Objective

修正 research strategy documentation drift，并让 strategy files 自带边界声明。

GitHub master 中 `strategies/research/vwap_factor_research.py` 位于 `strategies/research`，但模块 docstring 说 intentionally lives under `examples`。这会降低 research/production boundary 的可信度。

### Scope

In scope：

```text
- Correct stale docstring
- Add explicit research-only statement
- Add tests preventing stale wording
- Add docs on research vs production strategy boundary
```

### Likely Files

```text
strategies/research/vwap_factor_research.py
docs/research/strategy_boundaries.md
tests/unit/strategies/test_vwap_factor_research.py
tests/unit/quality/
```

### Acceptance Criteria

```text
[ ] Research strategy docstring no longer says it lives under examples.
[ ] Research strategy explicitly declares research-only / not paper-live.
[ ] Test or guardrail catches stale "lives under examples" wording in strategies/research.
[ ] Docs explain migration path from research to production.
```

---

## WP-12：Meta-Research Dashboard

**Subagent**：Meta-Research Agent  
**Priority**：P3  
**Current Status**：MISSING  
**Depends On**：WP-02, WP-03

### Objective

建立 monthly / quarterly meta-research summary，让系统能长期学习 research process quality。

### Scope

In scope：

```text
- idea pass rate
- factor pass rate
- strategy prototype count
- validation pass rate
- paper candidate count
- rejected reason distribution
- source success rate
- edge type distribution
- trial count outliers
```

Out of scope：

```text
- 不接 live PnL monitoring，未来可扩展
```

### Likely Files

```text
backend/src/qts/research/meta_research.py
scripts/run_research.py
registry/
runs/research/
tests/unit/research/test_meta_research.py
```

### Required Evidence

Artifacts：

```text
runs/research/meta/monthly_summary_YYYY_MM.json
runs/research/meta/monthly_summary_YYYY_MM.md
```

Summary Example：

```json
{
  "period": "2026-05",
  "ideas_created": 18,
  "factor_candidates": 9,
  "strategy_prototypes": 4,
  "validated_research": 1,
  "paper_candidates": 0,
  "rejected": 11,
  "top_rejection_reasons": [
    "no_oos_stability",
    "cost_stress_failed",
    "single_period_dependence"
  ],
  "avg_trials_per_active_candidate": 23.5
}
```

### Acceptance Criteria

```text
[ ] Can generate summary from idea/evidence/experiment registry.
[ ] Rejected strategies have reasons.
[ ] Can group by source and edge_type.
[ ] Can flag high trial_count candidates.
```

---

## WP-13：Research OS Guardrail Expansion

**Subagent**：Architecture Guardrail Agent  
**Priority**：P2  
**Current Status**：PARTIAL  
**Depends On**：WP-02, WP-03, WP-10

### Objective

在已有 guardrails 基础上增加 Research OS 专属规则。

### Existing Guardrails

```text
ResearchRunScriptRule
VwapOptimizerConfigRule
ProductionStrategyImportRule
ResearchWorkflowRuntimeKeyRule
```

### New Guardrails

```text
EvidenceBundleRequiredForPromotionRule
IdeaRegistryRequiredForCandidateRule
TradeDiagnosticsRequiredForPaperRule
RouteMetadataRequiredRule
ResearchReportDecisionRequiredRule
ResearchStrategyStaleDocstringRule
```

### Likely Files

```text
backend/src/qts/quality/rules/flows.py
backend/src/qts/quality/rules/research.py
backend/src/qts/quality/rules/__init__.py
scripts/verify_guardrails.py
tests/unit/quality/
```

### Tests

```text
test_guardrail_rejects_promotion_without_evidence_bundle
test_guardrail_rejects_candidate_without_idea_id
test_guardrail_rejects_route_workflow_without_route_metadata
test_guardrail_rejects_report_without_decision_block
test_guardrail_rejects_research_strategy_stale_examples_docstring
test_guardrail_scans_nested_workflow_routes
```

### Acceptance Criteria

```text
[ ] make guardrails includes new Research OS rules.
[ ] Promotion candidate without evidence_bundle_id fails.
[ ] Paper candidate without diagnostics fails.
[ ] Route workflow without metadata fails.
[ ] Stale research strategy docstring fails.
```

---

## WP-14：Research Review Decision Template

**Subagent**：Review Process Agent  
**Priority**：P1  
**Current Status**：MISSING  
**Depends On**：WP-02

### Objective

每份 research report 都必须有 machine-readable decision block，避免“看起来不错”。

### Allowed Decisions

```text
reject
keep_researching
freeze_forward
paper_candidate
small_live_candidate
retire
```

### Scope

In scope：

```text
- Decision schema
- Markdown rendering
- Evidence requirement per decision
- Append-only reviewer decision
```

### Likely Files

```text
backend/src/qts/research/report.py
backend/src/qts/research/evidence_registry.py
docs/research/review_process.md
tests/unit/research/test_research_report.py
```

### Decision Block Example

```yaml
decision:
  status: keep_researching
  reviewer: null
  reason:
    - Candidate is promising but trade diagnostics are missing.
    - Cost stress has not been run.
  required_next_evidence:
    - trade_level_diagnostics
    - cost_stress_2x_3x
    - parameter_neighborhood
```

### Tests

```text
test_report_decision_status_enum
test_report_decision_requires_evidence_bundle_for_paper_candidate
test_report_decision_blocks_paper_without_trade_diagnostics
test_report_decision_append_only_review
```

### Acceptance Criteria

```text
[ ] Report cannot end without decision block.
[ ] paper_candidate requires evidence_bundle.
[ ] paper_candidate requires diagnostics / validation / cost stress.
[ ] Reviewer can append decision but cannot overwrite artifact hashes.
```

---

## WP-15：Documentation and GitHub Issue Templates

**Subagent**：Research Program Manager Agent  
**Priority**：P3  
**Current Status**：MISSING  
**Depends On**：WP-01 to WP-14

### Objective

把 Research OS process 固化到 repo docs 和 issue templates，方便多个 Codex/subagents 并行推进。

### Likely Files

```text
docs/research/research_os.md
docs/research/subagent_work_packages.md
docs/research/promotion.md
.github/ISSUE_TEMPLATE/research_os_work_package.md
```

### Issue Template

```markdown
# [WP-XX] <Title>

## Subagent
...

## Objective
...

## Scope
### In Scope
...
### Out of Scope
...

## Files Likely Touched
...

## Behavior Contract
...

## Required Evidence
### Tests
...
### Artifacts
...
### CLI
...

## Acceptance Criteria
- [ ] ...
- [ ] ...

## Required Commands
```bash
make format
make lint
make guardrails
make typecheck
make test-unit
```

## Risks / Follow-up
...
```

### Acceptance Criteria

```text
[ ] Research OS docs exist.
[ ] All WP descriptions are issue-ready.
[ ] Issue template requires evidence and acceptance criteria.
[ ] Docs explicitly state research evidence != paper/live/production.
```

---

# 6. Recommended Execution Order

## Batch 1：Evidence Discipline First

```text
1. WP-01 Workflow Run Context & Evidence Header
2. WP-02 Research Evidence Bundle Registry
3. WP-14 Research Review Decision Template
```

Reason：

```text
先让每次 research 可审计、可引用、可判定。
```

## Batch 2：Research Funnel

```text
4. WP-03 Idea Registry + Trial Budget
5. WP-04 Factor Snapshot No-Lookahead Protocol
6. WP-05 Strategy Lab Ablation Protocol
7. WP-06 Trade-Level Diagnostics Standard
```

Reason：

```text
让 idea -> factor -> strategy 每一步都有证据和淘汰机制。
```

## Batch 3：Validation and Portfolio Hardening

```text
8. WP-07 Optimizer Hard Gates & Robustness Scorecard
9. WP-09 Portfolio Lab Hardening
```

Reason：

```text
防止 optimizer 和 portfolio scan 成为新的 overfit surface。
```

## Batch 4：Boundary and Scalability

```text
10. WP-10 Promotion Candidate Spec & Boundary Gate
11. WP-13 Research OS Guardrail Expansion
12. WP-08 Route Metadata & Research Program Structure
13. WP-11 Research Strategy Documentation Hardening
```

Reason：

```text
强化 research-to-production boundary，并为未来多路线研究做治理。
```

## Batch 5：Long-Term Operating System

```text
14. WP-12 Meta-Research Dashboard
15. WP-15 Documentation and GitHub Issue Templates
```

Reason：

```text
让系统长期学习，形成可持续 research process。
```

---

# 7. Global Definition of Done

每个 work package 必须满足：

```text
1. 有测试或 artifact 证明。
2. 有明确 before/after 行为变化。
3. 不降低已有 research/production boundary。
4. 不引入新的 ad hoc backtest path。
5. 不允许 research artifact 自动 promotion。
6. 不把 report-only / holdout / true-OOS 用于 selection。
7. 新增 artifact 有 hash 或可复现路径。
8. 新增状态 machine-readable。
```

代码类 work package：

```bash
make format
make lint
make guardrails
make typecheck
make test-unit
```

Workflow / CLI / optimizer / portfolio 类 work package：

```bash
make test-integration
```

更严格检查：

```bash
make check
```

---

# 8. Codex Subagent Prompt Template

```text
You are the subagent for [WP-XX: Title] in the QTS Quant Research Operating System project.

Repository:
github:xdcjie/QTS

Important:
Use only the GitHub repository implementation as source of truth.
Do not assume local uncommitted files.
Do not weaken existing period-role, report-only, guardrail, or research/production boundaries.

Goal:
<copy Objective>

Scope:
<copy Scope>

Required behavior:
- Do not create a new ad hoc backtest path.
- Do not allow report-only / holdout / true-OOS periods to influence selection.
- Do not promote research evidence into paper/live/production.
- Add tests and artifacts as acceptance evidence.
- Keep changes small and reviewable.

Required evidence:
<copy Required Evidence>

Acceptance criteria:
<copy Acceptance Criteria>

Required commands:
make format
make lint
make guardrails
make typecheck
make test-unit

Deliver:
1. Scope summary
2. Files changed
3. Behavior contract
4. Evidence produced
5. Commands run
6. Remaining risks
```

---

# 9. Final Recommendation

基于 GitHub `master`，QTS 的基础已经不错。最不应该做的是继续堆策略和参数 round。最应该做的是把现有能力升级为一套完整 Research OS：

```text
1. 先补 evidence header 和 evidence bundle。
2. 再补 idea/trial governance。
3. 再补 factor no-lookahead protocol。
4. 再补 ablation 和 trade-level diagnostics。
5. 再把 optimizer / portfolio 变成严格 validation labs。
6. 最后补 promotion spec、guardrail、meta-research dashboard。
```

这样 QTS 会从：

```text
有研究 workflow 的量化项目
```

升级为：

```text
能持续产生、验证、淘汰、迭代和生产化 edge 的研究操作系统。
```

真正的护城河不是某一个策略，而是：

```text
高淘汰率
高复现性
低自欺风险
强 evidence discipline
清晰 research-to-production boundary
长期 meta-research feedback loop
```
