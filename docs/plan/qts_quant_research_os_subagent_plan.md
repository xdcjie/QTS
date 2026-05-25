# QTS Quant Research Operating System：Subagent 推进计划

生成日期：2026-05-25  
目标：把 QTS 从“能运行 research workflow 的项目”升级为一套真正专业的量化 Research Operating System。  
核心原则：**高淘汰率、高复现性、低自欺风险、长期积累 edge**。

---

## 0. 项目背景与当前判断

根据当前 QTS Research System Brief，项目已经具备较好的 research 基础，包括：

- `ResearchSession`
- `ResearchWorkflowRunner`
- `BacktestPipeline / BacktestPipelineRunner`
- optimizer
- factor discovery / evaluation
- experiment manifest / experiment store
- portfolio ensemble
- deterministic report writer
- CLI
- 较完整的 unit / integration tests

当前架构的核心路径是：

```text
Research YAML / Workflow YAML
  -> ResearchSession
  -> ResearchWorkflowRunner
  -> BacktestPipeline / BacktestPipelineRunner
  -> shared backtest/runtime/data boundaries
  -> deterministic manifests / JSON summaries / markdown reports
```

这是正确方向，因为它没有绕过正式 backtest/runtime/data boundary，而是把 research 产物固化为可审计 evidence。

当前最重要的不变量：

```text
1. research 产物只是证据，不自动生成 trading code，不自动进入 paper/live。
2. 新 VWAP research 只能走 canonical workflow。
3. 不允许保留 ad hoc VWAP runner。
4. VWAP-specific optimizer YAML 不应成为新研究入口。
5. optimizer / backtest matrix 必须走 BacktestPipeline。
6. report-only / OOS 窗口不能反向调参。
7. research workflow 禁止 broker/live/paper/orders/runtime/trade/promote 等模糊边界 key。
```

---

## 1. 当前项目的主要优势

### 1.1 Research 和 Production 边界已经有雏形

当前项目中：

```text
strategies/research/vwap_factor_research.py
```

是 research harness。

```text
strategies/production/vwap_production_pullback.py
```

是 production strategy boundary。

这说明 QTS 已经意识到：

```text
research logic != production logic
research evidence != executable trading system
```

这是专业量化研究系统非常重要的基础。

---

### 1.2 Optimizer 和 backtest 已经接入共享 pipeline

当前 optimizer / backtest matrix 已经要求走：

```text
BacktestPipeline
BacktestPipelineRunner
```

而不是手写 vectorized backtest 或直接调用 strategy internals。

这是降低 research/runtime divergence 的关键。

---

### 1.3 Workflow 已经有 gate-based orchestration

当前 `ResearchWorkflowRunner` 已经支持：

```text
factor_candidates
factor_review_gate
implementation_gate
factor_evaluation
factor_tearsheet
backtest
backtest_matrix
optimize
portfolio_ensemble
portfolio_ensemble_scan
portfolio_volatility_managed_scan
research_report
```

并且有 hard-stop gates：

```text
factor_review_gate
implementation_gate
```

这为后续加入更强的 evidence gate、OOS gate、promotion gate 提供了基础。

---

### 1.4 Artifact / Manifest 思路正确

当前已经有：

```text
experiment_manifest.py
experiment_store.py
experiment_recorder.py
```

并能记录：

```text
experiment_id
platform_baseline_version
strategy_name
strategy_version
factor_versions
dataset_ids
config_hash
artifact_hashes
artifact_paths_by_hash
metrics
```

这是 Research OS 的核心资产。

---

## 2. 当前最大风险

当前 QTS 最大的问题不是“没有 research 框架”，而是：

```text
1. canonical VWAP workflow 太大，Route B-R 太多，容易模糊选择顺序。
2. report-only / holdout 语义主要靠政策约定，人工读报告时仍可能误用。
3. examples/strategies 已被用于严肃 research，但 promotion boundary 不够硬。
4. factor snapshot / forward return 构造仍可能发生未来数据泄露。
5. portfolio allocation scan 有 overfit 风险。
6. manifest 很强，但还不是完整 promotion-ready evidence bundle。
7. round27 这类反复研究容易产生 trial-count / data-snooping 风险。
```

因此，下一阶段的重点不是继续寻找更多策略，而是建立一套能不断产生、淘汰、迭代策略的 Research Operating System。

---

## 3. Research OS 目标架构

最终目标架构：

```text
Idea Registry
  -> Factor Lab
    -> Minimal Strategy Lab
      -> Validation Lab
        -> Portfolio Lab
          -> Evidence Registry
            -> Human Promotion Review
              -> Paper / Small Live / Production
                -> Monitoring / Drift / Kill Switch
                  -> Meta-Research Review
```

这套架构的目的不是让更多策略通过，而是让更多弱策略更快死亡，让少数强策略以可审计、可复现、可解释的方式留下来。

---

## 4. QTS 当前组件与 Research OS 的映射

| Research OS 层 | QTS 当前已有基础 | 需要补强 |
|---|---|---|
| Idea Registry | `factor_candidates`, `factor_spec_store` | 非论文类 idea、trial budget、edge taxonomy |
| Factor Lab | `factor_evaluation`, `tearsheet` | no-lookahead snapshot protocol、factor report 标准化 |
| Strategy Lab | `backtest`, `backtest_matrix`, `optimize` | minimal strategy / ablation 标准流程 |
| Validation Lab | constraints、walk-forward、failure-window veto | hard gates、period role enforcement、robustness scorecard |
| Portfolio Lab | portfolio ensemble / allocation scan | holdout 不参与 score 的强测试 |
| Evidence Registry | experiment manifest / store | promotion-ready evidence bundle |
| Promotion | policy exists | machine-readable review gate |
| Production Monitoring | 暂未充分展开 | live drift / kill switch 后续接入 |
| Meta-Research | 暂缺 | idea/source/pass-rate/false-positive 统计 |

---

## 5. Subagent 工作通用规则

每个 subagent 不应该只是“改代码”，而应该提交一个可审计工作包。

### 5.1 每个 Subagent 必须输出

```text
1. Scope
   - 本次解决什么问题
   - 不解决什么问题

2. Files Changed
   - 修改了哪些源码、配置、测试、文档

3. Behavior Contract
   - 新增或固化了哪些不变量

4. Evidence
   - 新增测试
   - 运行命令
   - 生成 artifact path
   - JSON/Markdown 示例片段
   - 失败用例是否被覆盖

5. Risk / Follow-up
   - 仍未覆盖的边界
   - 后续工作包依赖
```

### 5.2 代码类工作包最低检查

```bash
make format
make lint
make guardrails
make typecheck
make test-unit
```

### 5.3 Workflow / CLI / Optimizer / Portfolio 类工作包额外检查

```bash
tests/integration/test_run_research_cli.py
tests/integration/test_optimizer_consumes_backtest_config.py
relevant unit tests
```

### 5.4 Production Boundary 类工作包额外检查

```bash
strategy tests
guardrail tests
promotion spec tests
```

---

## 6. 推进阶段

建议分五个阶段推进。

```text
Phase 0：冻结与审计当前状态
Phase 1：补齐 evidence / period-role / guardrail
Phase 2：建立 Idea -> Factor -> Strategy 的标准漏斗
Phase 3：建立 Portfolio / Promotion / Paper-ready evidence
Phase 4：建立 Meta-Research 和长期运营机制
```

---

# Phase 0：冻结与审计当前状态

---

## WP-00：Research Baseline Freeze & Dirty State Audit

**Subagent：Research Baseline Auditor**

### 目标

把当前 `/Users/bjhl/Projects/QTS` 的 research 状态冻结成一个可审计 baseline。

当前 brief 明确指出：当前工作区存在大量未提交修改和未跟踪 research / route 配置、策略、测试与 graphify 产物。因此第一步必须确认：

```text
我们到底在什么代码、什么配置、什么 artifact 状态上继续研究？
```

### 工作内容

1. 记录当前 git commit、branch、dirty status。
2. 输出所有未提交 / 未跟踪 research 相关文件列表。
3. 将文件分类为：
   ```text
   canonical research infrastructure
   VWAP-specific research
   Route B-R research
   production strategy
   tests
   graphify/report artifacts
   obsolete/ad hoc scripts
   ```
4. 建立 `research_baseline_audit.json`。
5. 建立 `research_baseline_audit.md`。

### 可能涉及文件

```text
scripts/
configs/research/
configs/backtest.*
configs/strategies/
backend/src/qts/research/
strategies/research/
strategies/production/
examples/strategies/
tests/
runs/research/
```

### 验收证据

必须生成：

```text
artifacts/research_baseline_audit.json
artifacts/research_baseline_audit.md
```

JSON 示例：

```json
{
  "git_commit": "232c9b1",
  "branch": "master",
  "dirty": true,
  "untracked_files": [],
  "modified_files": [],
  "research_entrypoints": [],
  "deprecated_or_ad_hoc_candidates": [],
  "canonical_configs": [],
  "production_configs": [],
  "test_coverage_map": {}
}
```

### 验收条件

```text
1. audit 文件能明确复现当前研究基线。
2. 所有未跟踪 research/workflow/route 文件都有分类。
3. ad hoc VWAP runner 如存在，必须被列入 deprecated_or_ad_hoc_candidates。
4. 输出中包含 canonical VWAP entrypoint。
5. 人工 reviewer 能仅凭 audit 文件知道当前 project research surface。
```

---

# Phase 1：补齐 Evidence、Period Role、Guardrail

---

## WP-01：Period Role Contract & No-Tuning Enforcement

**Subagent：OOS Discipline Agent**

### 目标

把以下 period role 从“报告约定”升级成 schema 级别的机器约束：

```text
selection
validation
anchor
holdout_report_only
true_oos_report_only
```

当前项目已经意识到：

```text
holdout_2024_2026 应只用于 report-only
true-oos-after-2026-01-01 应永远是 report-only
```

但还需要让 workflow / optimizer / report / portfolio scan 都强制遵守。

### 工作内容

1. 为 workflow period 定义统一 schema：

```yaml
periods:
  is_2020_2022:
    start: "2020-01-01"
    end: "2022-01-01"
    role: selection

  validation_2022_2024:
    start: "2022-01-01"
    end: "2024-01-01"
    role: validation

  holdout_2024_2026:
    start: "2024-01-01"
    end: "2026-01-01"
    role: holdout_report_only

  true_oos_after_2026_01_01:
    start: "2026-01-01"
    end: null
    role: true_oos_report_only
```

2. 在 `ResearchWorkflowConfig` 解析时验证：
   ```text
   start < end
   windows 时间有序
   report_only windows 不允许进入 optimize objective
   true_oos_report_only 不允许进入 candidate selection
   ```

3. Optimizer / backtest_matrix / portfolio_scan 读取 period role。

4. 如果某 step 把 holdout 作为 score / objective / ranking basis，直接 fail。

5. Report 中强制输出每个 period 的 role。

### 可能涉及文件

```text
backend/src/qts/research/workflow.py
backend/src/qts/research/report.py
backend/src/qts/research/optimizer/
backend/src/qts/research/portfolio_ensemble.py
tests/unit/research/test_research_workflow.py
tests/unit/research/test_research_report.py
tests/unit/research/test_portfolio_ensemble.py
tests/integration/test_run_research_cli.py
configs/research/workflows/*.yaml
```

### 新增测试

```text
test_workflow_rejects_holdout_in_optimizer_objective
test_workflow_rejects_true_oos_in_candidate_selection
test_research_report_prints_period_roles
test_backtest_matrix_records_period_roles
test_portfolio_scan_rejects_holdout_score_period
```

### 验收证据

Workflow summary JSON 示例：

```json
{
  "periods": {
    "is_2020_2022": {"role": "selection"},
    "validation_2022_2024": {"role": "validation"},
    "holdout_2024_2026": {"role": "holdout_report_only"},
    "true_oos_after_2026_01_01": {"role": "true_oos_report_only"}
  },
  "selection_basis": ["is_2020_2022", "validation_2022_2024"],
  "report_only_periods": ["holdout_2024_2026", "true_oos_after_2026_01_01"]
}
```

### 验收条件

```text
1. 故意把 holdout_report_only 配进 optimizer objective 时，workflow 必须失败。
2. report markdown 中必须出现 period role 表。
3. summary JSON 中必须有 machine-readable period roles。
4. Route J/K/L/R portfolio scans 不能把 holdout 纳入 score。
5. make test-unit + relevant integration tests pass。
```

---

## WP-02：Workflow Report Evidence Header

**Subagent：Evidence Report Agent**

### 目标

每份 research report 必须能回答：

```text
这次研究跑的是哪个 workflow？
基于哪个 git commit？
工作区是否 dirty？
数据集是什么？
backtest config hash 是什么？
workflow config hash 是什么？
每个结果对应哪个 manifest？
哪些窗口用于选择，哪些只是 report-only？
```

### 工作内容

1. 在 workflow run summary 中加入：
   ```text
   workflow_config_path
   workflow_config_hash
   research_config_path
   research_config_hash
   git_commit
   git_branch
   git_dirty
   dataset_ids
   backtest_config_hash
   generated_at
   ```

2. Report header 强制显示这些字段。

3. Report 每个 route/step 显示：
   ```text
   step_id
   step_kind
   selection_basis
   validation_basis
   report_only_windows
   artifact_paths
   manifest_hashes
   ```

4. Report 加入硬声明：
   ```text
   This report is research evidence only and is not a paper/live/production promotion.
   ```

### 可能涉及文件

```text
backend/src/qts/research/report.py
backend/src/qts/research/workflow.py
backend/src/qts/research/experiment_manifest.py
tests/unit/research/test_research_report.py
tests/integration/test_run_research_cli.py
```

### 新增测试

```text
test_research_report_contains_evidence_header
test_workflow_summary_contains_config_and_git_hashes
test_report_marks_research_only_boundary
```

### Report Header 示例

```markdown
## Evidence Header

- Workflow config: `configs/research/workflows/vwap_factor_search.yaml`
- Workflow config hash: `...`
- Research config: `configs/research/vwap.yaml`
- Git commit: `...`
- Dirty workspace: `true/false`
- Dataset IDs: `[...]`
- Backtest config hash: `...`
- Promotion status: `research_only`
```

### 验收条件

```text
1. 任一 workflow report 缺少 evidence header，测试失败。
2. dirty workspace 必须显式显示，不允许隐藏。
3. report-only windows 必须独立列出。
4. report 明确声明不能直接用于 paper/live。
```

---

## WP-03：Research Evidence Registry

**Subagent：Evidence Registry Agent**

### 目标

把 workflow run、config hash、dataset hash、backtest manifest、report、review decision 统一成一个 promotion-ready evidence bundle。

当前 manifest 已经很强，但它不是完整 promotion gate。还需要一个更高层 evidence bundle。

### 工作内容

1. 新增 `ResearchEvidenceBundle`。
2. 每个 bundle 包含：
   ```text
   evidence_bundle_id
   idea_id
   strategy_id
   workflow_run_id
   experiment_manifest_paths
   workflow_summary_path
   report_path
   config_hashes
   dataset_ids
   artifact_hashes
   period_roles
   trial_count
   review_status
   review_decision
   reviewer
   review_timestamp
   promotion_eligibility
   ```

3. 增加 CLI：

```bash
scripts/run_research.py evidence bundle --workflow-run <path>
scripts/run_research.py evidence list
scripts/run_research.py evidence show <bundle_id>
```

4. Evidence bundle 只能作为 promotion review input，不触发 promotion。

### 可能涉及文件

```text
backend/src/qts/research/evidence_registry.py
backend/src/qts/research/experiment_store.py
backend/src/qts/research/experiment_manifest.py
scripts/run_research.py
tests/unit/research/test_evidence_registry.py
tests/integration/test_run_research_cli.py
```

### 验收证据

生成：

```text
runs/research/evidence/evidence-bundle-<id>.json
runs/research/evidence/index.jsonl
```

Bundle 示例：

```json
{
  "evidence_bundle_id": "evb_...",
  "strategy_id": "gc_asia_vwap_pullback_q1_np4_range150_mom075",
  "status": "research_evidence_only",
  "promotion_eligibility": "not_reviewed",
  "workflow_config_hash": "...",
  "dataset_ids": ["..."],
  "manifest_hashes": ["..."],
  "report_path": "...",
  "period_roles": {},
  "review_decision": null
}
```

### 验收条件

```text
1. bundle 可从 workflow summary + manifests 重建。
2. bundle 中所有 artifact path 必须存在。
3. bundle 中所有 hash 可重新计算匹配。
4. bundle status 不能是 paper/live/production。
5. promotion review 必须引用 bundle_id，而不是复制 PnL 文本。
```

---

## WP-04：Architecture Import Guardrail

**Subagent：Architecture Guardrail Agent**

### 目标

防止 research workflow 直接依赖 broker / runtime / order / risk internals。

当前 workflow 禁止配置中包含：

```text
broker
live
paper
orders
runtime
trade
promote
```

但还需要源码级 architecture guardrail。

### 工作内容

1. 扩展 `scripts/verify_guardrails.py`。
2. 扫描：
   ```text
   backend/src/qts/research/
   scripts/run_research.py
   configs/research/
   configs/research/workflows/
   ```
3. 禁止 import / config key：
   ```text
   broker
   live
   paper
   orders
   runtime
   promote
   trading
   ```
4. 输出 machine-readable guardrail report。

### 可能涉及文件

```text
scripts/verify_guardrails.py
tests/unit or tests/integration for guardrails
configs/research/workflows/*.yaml
backend/src/qts/research/*
```

### 新增测试

```text
test_guardrail_rejects_research_importing_broker
test_guardrail_rejects_workflow_live_key
test_guardrail_allows_report_text_boundary_statement
```

### 验收证据

Guardrail report 示例：

```json
{
  "status": "passed",
  "checked_paths": [],
  "forbidden_imports_found": [],
  "forbidden_config_keys_found": []
}
```

### 验收条件

```text
1. 故意在 research workflow 加 `paper:` key 时 make guardrails fail。
2. 故意在 qts.research import broker/runtime 时 fail。
3. 正常 report 中出现 “not paper/live” 文本不误杀。
4. make guardrails 通过。
```

---

# Phase 2：建立 Idea -> Factor -> Strategy 标准漏斗

---

## WP-05：Idea Registry + Trial Budget

**Subagent：Idea Governance Agent**

### 目标

建立真正的 idea registry，让每个策略研究都有：

```text
来源
机制
假设
edge taxonomy
trial count
kill criteria
```

当前 QTS 已有 factor discovery / factor spec，但它偏论文 / metadata 驱动。Research OS 需要覆盖：

```text
内部诊断
交易员观察
失败路径
外部搜索
宏观机制
portfolio gap
```

### 工作内容

1. 新增 `IdeaSpec`。
2. 支持 idea source：
   ```text
   internal_diagnostic
   external_paper
   exchange_data
   public_strategy
   trader_observation
   macro_event
   post_trade_failure_analysis
   portfolio_gap
   ```

3. 支持 edge taxonomy：
   ```text
   time_series_momentum
   mean_reversion
   carry
   term_structure
   event_driven
   seasonality
   liquidity
   microstructure
   relative_value
   volatility
   macro_regime
   execution_alpha
   ```

4. 每次 experiment 可关联 `idea_id`。
5. 每个 `idea_id` 自动累计 trial count。
6. 超过 trial budget 时，workflow report 显示 warning；promotion score 降权。

### 可能涉及文件

```text
backend/src/qts/research/idea_spec.py
backend/src/qts/research/idea_registry.py
backend/src/qts/research/experiment_recorder.py
backend/src/qts/research/report.py
scripts/run_research.py
tests/unit/research/test_idea_registry.py
tests/unit/research/test_experiment_recorder.py
```

### 验收证据

新增：

```text
registry/idea_registry.yaml
```

示例：

```yaml
idea_id: gc_asia_session_continuation_v1
status: active_research
source: internal_diagnostic
edge_type:
  - session_effect
  - time_series_momentum
  - liquidity
hypothesis: >
  Asia session 内，如果价格接受 session VWAP 趋势侧并出现成交确认回踩，
  后续 1-8 根 15m bar 延续概率高于随机。
trial_budget:
  max_strategy_trials: 30
  max_validation_variants: 5
current_trial_count: 17
kill_criteria:
  - no_parameter_neighborhood
  - oos_net_sharpe_below_0_8
  - cost_2x_negative
```

### 验收条件

```text
1. 每个 recorded experiment 可以关联 idea_id。
2. idea_id 的 trial_count 会随 experiment 增长。
3. 超过 trial_budget 时 report 出 warning。
4. strategy report 中显示 idea source 和 edge taxonomy。
5. 没有 hypothesis 的 idea 不能进入 promotion review。
```

---

## WP-06：Factor Snapshot No-Lookahead Protocol

**Subagent：Factor Integrity Agent**

### 目标

建立 factor score 和 forward return snapshot 的 no-lookahead anchor tests。

当前 factor evaluation 代码 deterministic，但 correctness 依赖输入 snapshot / forward return 构造协议。错误构造会泄漏未来。

### 工作内容

1. 定义标准 factor snapshot schema：
   ```text
   timestamp
   instrument
   factor_name
   factor_version
   factor_value
   available_at
   source_data_end
   horizon
   forward_return_start
   forward_return_end
   ```

2. 约束：
   ```text
   available_at <= forward_return_start
   source_data_end <= available_at
   factor timestamp 使用 [start, end) bar boundary
   ```

3. 对 factor evaluation 增加 preflight validation。

4. 增加 synthetic leak tests：
   ```text
   future_return 被错误塞进 factor_value -> test fails
   source_data_end 晚于 available_at -> test fails
   available_at 晚于 forward_return_start -> test fails
   ```

5. factor tearsheet 记录 snapshot hash 和 forward horizon。

### 可能涉及文件

```text
backend/src/qts/research/factor_evaluation.py
backend/src/qts/research/tearsheet.py
backend/src/qts/research/factor_spec.py
tests/unit/research/test_factor_evaluation.py
tests/unit/research/test_tearsheet.py
```

### 新增测试

```text
test_factor_snapshot_rejects_future_available_at
test_factor_snapshot_rejects_source_data_after_available_at
test_factor_snapshot_rejects_forward_return_overlap
test_factor_tearsheet_records_snapshot_hash
```

### 验收证据

Factor evaluation artifact 示例：

```json
{
  "snapshot_hash": "...",
  "factor_versions": {},
  "forward_return_protocol": {
    "horizon": "4bar",
    "label_start": "next_bar_open_or_close",
    "no_overlap_verified": true
  }
}
```

### 验收条件

```text
1. 人工构造未来泄漏 snapshot 时 evaluation fail。
2. factor tearsheet 中可追踪 snapshot hash。
3. snapshot protocol 写入 deterministic artifact。
4. factor evaluation 结果不能只给 IC/long-short，不给数据协议。
```

---

## WP-07：Strategy Lab Ablation Protocol

**Subagent：Strategy Research Agent**

### 目标

把策略开发标准化为：

```text
minimal baseline
+ single-module ablation
+ combined modules
+ robustness validation
```

避免 round27 之后继续无约束调参。

### 工作内容

1. 定义 `AblationPlan` schema：

```yaml
base_config: ...
modules:
  - name: momentum_filter
    params: ...
  - name: range_filter
    params: ...
  - name: sizing_rule
    params: ...
ablation_order:
  - baseline
  - baseline+momentum
  - baseline+momentum+range
```

2. 支持 workflow step kind 或 config convention。

3. 每个 ablation 输出：
   ```text
   metric_delta_vs_baseline
   trade_count_delta
   dd_delta
   oos_delta
   cost_stress_delta
   ```

4. 对当前 GC VWAP q1 候选输出 ablation template：
   ```text
   baseline
   + mom120
   + volume_ratio
   + range_expansion
   + early_no_progress
   + size_reduction
   + vwap_acceptance
   ```

### 可能涉及文件

```text
backend/src/qts/research/workflow.py
backend/src/qts/research/report.py
configs/research/workflows/*ablation*.yaml
tests/unit/research/test_research_workflow.py
tests/unit/research/test_research_report.py
```

### 验收证据

生成：

```text
runs/research/<strategy>/ablation/summary.json
runs/research/<strategy>/ablation/report.md
```

Summary 示例：

```json
{
  "baseline": {
    "net_sharpe": 0.82,
    "max_dd": 0.12
  },
  "baseline_plus_mom120": {
    "net_sharpe": 1.05,
    "delta_sharpe": 0.23,
    "delta_max_dd": -0.03,
    "trade_count_delta": -42
  }
}
```

### 验收条件

```text
1. 每个 filter/module 的增量贡献可见。
2. 如果某模块只提升 IS，不提升 OOS，report 标记为 unstable。
3. ablation report 不允许只展示最终组合。
4. 当前 VWAP q1 至少有一份 ablation plan artifact。
```

---

## WP-08：Trade-Level Diagnostics Standard

**Subagent：Trade Diagnostics Agent**

### 目标

所有 strategy research 必须输出 trade-level diagnostics，而不只是 equity curve 和 Sharpe。

这对当前 q1 VWAP 候选尤其关键，因为收益/DD 可能来自：

```text
固定 4 手
特定时间段
特定 exit reason
特定 momentum bucket
特定 range bucket
```

### 工作内容

1. 定义标准 trade diagnostics schema：
   ```text
   trade_id
   strategy_id
   idea_id
   entry_time
   exit_time
   symbol
   direction
   quantity
   entry_price
   exit_price
   R_pnl
   MAE_R
   MFE_R
   holding_bars
   exit_reason
   time_bucket
   regime
   factor_snapshot
   ```

2. 对 strategy intent metadata 中已有 factor diagnostics 做标准化。

3. Report 输出：
   ```text
   PnL by time bucket
   PnL by direction
   PnL by exit reason
   PnL by quantity
   PnL by factor bucket
   MAE/MFE distribution
   ```

4. 支持 JSON + Markdown summary。

### 可能涉及文件

```text
backend/src/qts/research/report.py
backend/src/qts/research/experiment_manifest.py
strategies/research/vwap_factor_research.py
tests/unit/strategies/test_vwap_factor_research.py
tests/unit/research/test_research_report.py
```

### 验收证据

生成：

```text
runs/research/<strategy>/diagnostics/trades.parquet
# 或
runs/research/<strategy>/diagnostics/trades.jsonl

runs/research/<strategy>/diagnostics/trade_diagnostics_summary.json
runs/research/<strategy>/diagnostics/trade_diagnostics_report.md
```

### 验收条件

```text
1. 每笔交易有 R_pnl、MAE_R、MFE_R、exit_reason。
2. VWAP q1 candidate 能按 qty=4 / qty=1 拆分。
3. 能按 20:00-22:00、22:00-00:00、00:00-02:00 拆分。
4. 能按 mom/range/volume bucket 拆分。
5. 缺少 trade-level diagnostics 的策略不能进入 Paper candidate。
```

---

# Phase 3：建立 Validation、Portfolio、Promotion Gate

---

## WP-09：Optimizer Hard Gates & Robustness Scorecard

**Subagent：Validation Gate Agent**

### 目标

把 optimizer 从“按 objective 排名”推进到“必须通过 validation gate 才能进入候选”。

当前 optimizer 已经支持：

```text
constraints
validation summary
walk-forward
failure-window veto
capital metrics
```

但还需要统一 hard gate 和 robustness scorecard。

### 工作内容

1. 定义 `ResearchValidationPolicy`：

```yaml
min_trades: 50
min_profit_factor: 1.15
min_net_sharpe: 0.8
max_drawdown: 0.12
min_walk_forward_windows: 3
max_losing_windows: 1
cost_stress:
  slippage_multiplier: [1, 2, 3]
remove_best_days:
  n: [5, 10]
failure_windows:
  require_passing_candidate: true
```

2. Optimizer summary 输出：
   ```text
   raw_rank
   accepted_rank
   rejection_reasons
   robustness_score
   cost_stress_status
   walk_forward_status
   failure_window_status
   ```

3. 如果没有 candidate 通过 hard gate，workflow step 必须 blocked。

4. Report 不能只显示 top Sharpe，必须显示 rejected candidates 和原因。

### 可能涉及文件

```text
backend/src/qts/research/optimizer/validation.py
backend/src/qts/research/optimizer/walk_forward.py
backend/src/qts/research/optimizer/failure_veto.py
backend/src/qts/research/report.py
tests/unit/research/test_optimizer_constraints.py
tests/unit/research/test_optimizer_walk_forward.py
tests/unit/research/test_optimizer_failure_veto.py
```

### 新增测试

```text
test_optimizer_blocks_when_no_candidate_passes_hard_gates
test_optimizer_reports_rejection_reasons
test_walk_forward_policy_required_for_candidate_promotion
test_failure_window_require_passing_candidate_blocks_step
test_optimizer_scorecard_includes_cost_stress
```

### Validation Summary 示例

```json
{
  "candidate_id": "run-0017",
  "raw_objective_rank": 2,
  "accepted": false,
  "rejection_reasons": [
    "max_drawdown > 0.12",
    "cost_stress_2x_net_pnl < 0",
    "failure_window_2024_failed"
  ],
  "robustness_score": 61.5
}
```

### 验收条件

```text
1. 没有通过 hard gates 的 optimizer step 必须 blocked。
2. accepted candidates 必须少于或等于 raw candidates。
3. report 显示 accepted/rejected，不允许只展示 winners。
4. failure-window veto 可配置为 hard gate，并有测试覆盖。
5. 2x/3x cost stress 结果进入 summary。
```

---

## WP-10：Portfolio Lab Guardrails

**Subagent：Portfolio Research Agent**

### 目标

防止 portfolio ensemble / allocation scan 把 holdout 反馈进选择，并确保 portfolio artifacts 不被误读为可交易 portfolio config。

当前 `portfolio_ensemble.py` 已明确是 research-only，但还需要更强 period-role checks。

### 工作内容

1. 所有 portfolio scan 必须声明：
   ```text
   selection_periods
   validation_periods
   holdout_report_only_periods
   ```

2. score 只能使用 selection / validation，不得使用 holdout_report_only。

3. vol-managed allocation 权重计算必须只用 prior returns。

4. Artifact 显示：
   ```text
   research_only: true
   not_tradable_config: true
   ```

5. Report 中加入 allocation overfit warning。

### 可能涉及文件

```text
backend/src/qts/research/portfolio_ensemble.py
backend/src/qts/research/workflow.py
backend/src/qts/research/report.py
tests/unit/research/test_portfolio_ensemble.py
tests/unit/research/test_research_workflow.py
```

### 新增测试

```text
test_portfolio_scan_rejects_holdout_in_score
test_vol_managed_weights_use_prior_returns_only
test_portfolio_artifact_marks_research_only
test_portfolio_report_shows_selection_and_holdout_separately
```

### Artifact 示例

```json
{
  "research_only": true,
  "not_tradable_config": true,
  "score_periods": ["is_2020_2022", "validation_2022_2024"],
  "report_only_periods": ["holdout_2024_2026"],
  "uses_prior_returns_only": true
}
```

### 验收条件

```text
1. Route J/K/L/R 不能把 holdout 纳入 score。
2. vol-managed 权重使用未来收益时测试失败。
3. portfolio artifact 永远 research_only。
4. report 明确 allocation scan 不是 production allocation。
```

---

## WP-11：Research-to-Production Boundary Gate

**Subagent：Promotion Boundary Agent**

### 目标

确保 research strategy、examples strategy 和 production strategy 的边界不能漂移。

当前项目已区分：

```text
research strategy:
  strategies/research/vwap_factor_research.py

production strategy:
  strategies/production/vwap_production_pullback.py

examples route strategies:
  examples/strategies/*.py
```

但如果 examples route 策略变成 promotion candidate，需要明确迁移 / 审查路径。

### 工作内容

1. 建立 `PromotionCandidateSpec`：
   ```text
   strategy_id
   source_module
   target_module
   evidence_bundle_id
   production_owner
   allowed_config_surface
   prohibited_research_params
   paper_readiness_checklist
   ```

2. Guardrail：
   ```text
   production strategy 不得 import strategies.research.*
   production config 不得引用 research-only params
   promotion candidate 不得直接来自 examples/strategies，除非有 migration review
   ```

3. 为 examples strategy promotion 定义路径：

```text
examples/strategies/foo.py
  -> strategies/research/foo_research.py
  -> strategies/production/foo.py
```

或明确标记：

```text
research_only: true
not_promotion_eligible: true
```

### 可能涉及文件

```text
scripts/verify_guardrails.py
strategies/production/
strategies/research/
examples/strategies/
configs/strategies/
configs/backtest.*
tests/unit/strategies/
tests/unit/research/
docs/research/promotion.md
```

### 新增测试

```text
test_production_strategy_does_not_import_research_strategy
test_production_config_rejects_research_only_params
test_examples_strategy_cannot_be_promotion_candidate_without_review
test_promotion_candidate_requires_evidence_bundle
```

### 验收条件

```text
1. production 不能 import research strategy。
2. production config 出现 research-only key 时 fail。
3. examples strategy 不能直接 promotion。
4. promotion spec 必须引用 evidence_bundle_id。
5. promotion 仍是人工 review，不由 backtest 自动触发。
```

---

## WP-12：Research Report Decision Template

**Subagent：Review Process Agent**

### 目标

每份 report 最后都必须给出明确决策，而不是“看起来不错”。

决策只能是：

```text
reject
keep_researching
freeze_forward
paper_candidate
small_live_candidate
retire
```

### 工作内容

1. Report writer 支持 decision block：

```yaml
decision:
  status: keep_researching
  reviewer: null
  required_next_evidence:
    - trade_level_diagnostics
    - parameter_neighborhood
    - cost_stress_2x
```

2. 每个 decision 必须引用 evidence bundle 或 manifest。

3. `paper_candidate` 之前必须满足：
   ```text
   evidence_bundle exists
   period roles exist
   no research-only strategy boundary violation
   validation scorecard exists
   cost stress exists
   trade diagnostics exists
   ```

4. 缺失 evidence 时，report 不能输出 paper_candidate。

### 可能涉及文件

```text
backend/src/qts/research/report.py
backend/src/qts/research/evidence_registry.py
tests/unit/research/test_research_report.py
docs/research/review_process.md
```

### 新增测试

```text
test_report_decision_requires_evidence_bundle
test_paper_candidate_requires_validation_artifacts
test_report_decision_status_enum
```

### Markdown 示例

```markdown
## Review Decision

Status: keep_researching

Reason:
- Candidate is promising but OOS is not clean.
- Trade-level diagnostics missing.
- 2x cost stress not yet available.

Required next evidence:
- Dynamic sizing comparison
- Period-role validated report
- True forward run after frozen date
```

### 验收条件

```text
1. report 不允许无状态结束。
2. paper_candidate 缺 evidence 时测试失败。
3. decision block machine-readable。
4. 人工 reviewer 可以追加 decision，但不能覆盖原始 artifact hash。
```

---

# Phase 4：Route 治理与当前 VWAP Candidate 纳入系统

---

## WP-13：Workflow Route Metadata & Route B-R Decomposition

**Subagent：Workflow Scalability Agent**

### 目标

解决 canonical workflow 太大、Route B-R 在同一个文件中容易模糊探索 / 候选 / 拒绝状态的问题。

当前 `vwap_factor_search.yaml` 是 canonical all-route VWAP workflow，包含 B-R 多路线。中心治理有好处，但也带来后续 route 观察影响 earlier selection 的风险。

### 工作内容

1. 为每个 route 增加 machine-readable metadata：

```yaml
route_id: B
route_name: vwap_rolling_dual_supertrend
status: exploration
owner: research
selection_policy: ...
allowed_period_roles:
  - selection
  - validation
  - holdout_report_only
```

2. 将 Route B-R 拆成 route-specific workflow files：

```text
configs/research/workflows/routes/route_b_vwap_rolling.yaml
configs/research/workflows/routes/route_c_vol_target_trend.yaml
...
```

3. 建立 canonical meta-workflow/index：

```text
configs/research/workflows/vwap_routes_index.yaml
```

4. Report 按 route 输出：
   ```text
   route status
   selection basis
   validation basis
   report-only periods
   decision
   ```

### 可能涉及文件

```text
configs/research/workflows/vwap_factor_search.yaml
configs/research/workflows/routes/*.yaml
backend/src/qts/research/workflow.py
backend/src/qts/research/report.py
tests/unit/research/test_research_workflow.py
tests/integration/test_run_research_cli.py
```

### 新增测试

```text
test_route_metadata_required_for_route_workflows
test_route_status_appears_in_report
test_route_index_resolves_all_routes
test_canonical_route_order_snapshot
```

### 验收证据

必须生成：

```text
configs/research/workflows/vwap_routes_index.yaml
configs/research/workflows/routes/route_*.yaml
```

### 验收条件

```text
1. 每个 route 有 route_id、status、selection_policy。
2. report 能区分 exploration / candidate / rejected / frozen。
3. holdout_report_only route 结果不能改变 route status 为 candidate。
4. route index 中缺失 route file 时测试失败。
5. workflow step order 有 snapshot test，防止无意漂移。
```

---

## WP-14：Current VWAP q1 Candidate Onboarding into Research OS

**Subagent：VWAP Candidate Steward**

### 目标

把当前 `q1_np4_range150_mom075` 从“当前最优 research 候选”正式纳入 Research OS，而不是继续口头追踪。

### 工作内容

1. 创建 strategy registry entry：

```yaml
strategy_id: gc_asia_vwap_pullback_q1_np4_range150_mom075
status: research_candidate
source_workflow: round27
implementation: strategies/research/vwap_factor_research.py
production_eligible: false
reason: research harness only
oos_clean: false
reason_oos_not_clean: post-cut period used for repair/selection
```

2. 创建 idea entry：

```text
GC Asia VWAP trend-pullback continuation
```

3. 生成 evidence bundle。
4. 生成 trade-level diagnostics。
5. 定义 freeze date：

```text
true_forward_start: 2026-05-23 或人工确认后的实际冻结日
```

6. 添加 next experiments：

```text
same_signal_dynsize
global_acceptance
trend_efficiency
partial_runner
v2_full
```

7. 标记这些都是 frozen candidates，不允许根据 forward period 继续调参。

### 可能涉及文件

```text
registry/idea_registry.yaml
registry/strategy_registry.yaml
configs/research/workflows/vwap_*.yaml
runs/research/vwap/
strategies/research/vwap_factor_research.py
```

### 验收证据

必须生成：

```text
registry/strategies/gc_asia_vwap_pullback_q1_np4_range150_mom075.yaml
runs/research/vwap/evidence/<bundle>.json
runs/research/vwap/diagnostics/<candidate>/trade_diagnostics_summary.json
```

### 验收条件

```text
1. q1 candidate 状态是 research_candidate，不是 paper/live/production。
2. registry 明确 oos_clean = false。
3. true_forward_start 明确写入。
4. diagnostics 能拆分 qty、time bucket、exit reason、factor bucket。
5. 后续变体必须作为新 candidate_id，不覆盖原 q1。
```

---

# Phase 5：Meta-Research 和长期运营

---

## WP-15：Meta-Research Dashboard

**Subagent：Meta-Research Agent**

### 目标

让系统每月 / 每季度能回答：

```text
我们产生了多少 idea？
多少进入 factor lab？
多少进入 strategy prototype？
多少通过 validation？
多少 paper？
多少 small live？
哪些 idea source 成功率高？
哪些 edge type 最容易过拟合？
哪些 strategy 被淘汰，原因是什么？
```

这是 Research OS 长期积累能力的核心。

### 工作内容

1. 从 idea registry、experiment registry、evidence registry 汇总。
2. 输出：
   ```text
   idea pass rate
   factor pass rate
   strategy pass rate
   validation pass rate
   paper pass rate
   production survival rate
   false positive count
   average trials per accepted candidate
   rejected reasons distribution
   edge type distribution
   source success rate
   ```

3. 生成 monthly / quarterly report。
4. 用于调整 research roadmap。

### 可能涉及文件

```text
backend/src/qts/research/meta_research.py
scripts/run_research.py
registry/
runs/research/
tests/unit/research/test_meta_research.py
```

### 验收证据

生成：

```text
runs/research/meta/monthly_summary_YYYY_MM.json
runs/research/meta/monthly_summary_YYYY_MM.md
```

示例：

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

### 验收条件

```text
1. 能从 registry 和 experiment store 自动生成 summary。
2. 每个 rejected strategy 有 reason。
3. 能按 source 和 edge_type 统计成功率。
4. 能暴露 trial_count 过高的策略。
```

---

## 7. 推荐执行顺序

### 第一批：保护研究诚信

```text
WP-00 Research Baseline Freeze
WP-01 Period Role Contract
WP-02 Workflow Report Evidence Header
WP-04 Architecture Import Guardrail
```

目的：

```text
阻断 OOS 误用、未来函数、report-only 误读和 research/production 边界漂移。
```

---

### 第二批：建立证据系统

```text
WP-03 Research Evidence Registry
WP-05 Idea Registry + Trial Budget
WP-12 Research Report Decision Template
```

目的：

```text
让每次研究变成可审计、可追踪、可复盘的 evidence。
```

---

### 第三批：建立研究漏斗

```text
WP-06 Factor Snapshot No-Lookahead
WP-07 Strategy Lab Ablation Protocol
WP-08 Trade-Level Diagnostics Standard
WP-09 Optimizer Hard Gates
```

目的：

```text
提高淘汰率，降低自欺风险。
```

---

### 第四批：治理 route 和 portfolio

```text
WP-10 Portfolio Lab Guardrails
WP-11 Research-to-Production Boundary Gate
WP-13 Workflow Route Metadata & Decomposition
```

目的：

```text
解决 Route B-R 扩散、allocation overfit 和 examples/production 边界问题。
```

---

### 第五批：当前候选纳入与长期运营

```text
WP-14 Current VWAP q1 Candidate Onboarding
WP-15 Meta-Research Dashboard
```

目的：

```text
把当前 q1 候选纳入新体系，并建立长期 research feedback loop。
```

---

## 8. Subagent 分工矩阵

| Work Package | Subagent | 优先级 | 依赖 | 验收核心 |
|---|---|---:|---|---|
| WP-00 | Research Baseline Auditor | P0 | 无 | baseline audit JSON/MD |
| WP-01 | OOS Discipline Agent | P0 | WP-00 | holdout 不能进 objective |
| WP-02 | Evidence Report Agent | P0 | WP-00 | report header + config/git hash |
| WP-04 | Architecture Guardrail Agent | P0 | WP-00 | research 不依赖 broker/runtime |
| WP-03 | Evidence Registry Agent | P1 | WP-02 | evidence bundle 可重建 |
| WP-05 | Idea Governance Agent | P1 | WP-03 | idea_id + trial_count |
| WP-12 | Review Process Agent | P1 | WP-03 | report decision + evidence gate |
| WP-06 | Factor Integrity Agent | P2 | WP-01 | no-lookahead snapshot tests |
| WP-07 | Strategy Research Agent | P2 | WP-05 | ablation report |
| WP-08 | Trade Diagnostics Agent | P2 | WP-07 | trade-level diagnostics |
| WP-09 | Validation Gate Agent | P2 | WP-01, WP-08 | accepted/rejected hard gates |
| WP-10 | Portfolio Research Agent | P3 | WP-01 | no holdout allocation scoring |
| WP-11 | Promotion Boundary Agent | P3 | WP-03 | promotion requires evidence bundle |
| WP-13 | Workflow Scalability Agent | P3 | WP-01, WP-02 | route metadata + route index |
| WP-14 | VWAP Candidate Steward | P4 | WP-03, WP-08 | q1 candidate frozen + diagnostics |
| WP-15 | Meta-Research Agent | P4 | WP-03, WP-05 | monthly meta report |

---

## 9. 全局 Definition of Done

任何 work package 完成，都必须满足：

```text
1. 有对应测试或 artifact 证明。
2. 有明确的 before/after 行为变化。
3. 不降低现有 canonical research boundary。
4. 不引入新的 ad hoc backtest path。
5. 不允许 research artifact 自动 promotion。
6. 不把 report-only / holdout 用于 selection。
7. 所有新增 artifact 都有 hash 或可复现路径。
8. 所有新增状态都 machine-readable。
```

代码类 work package：

```bash
make format
make lint
make guardrails
make typecheck
make test-unit
```

workflow / CLI / optimizer / portfolio 类 work package：

```bash
tests/integration/test_run_research_cli.py
tests/integration/test_optimizer_consumes_backtest_config.py
relevant unit tests
```

production boundary 类 work package：

```bash
strategy tests
guardrail tests
promotion spec tests
```

---

## 10. 为什么这套计划能避免“继续找神奇策略”

这套计划会强制每个策略经过：

```text
Idea hypothesis
  -> Factor evidence
    -> Minimal strategy
      -> Ablation
        -> Robustness
          -> Evidence bundle
            -> Human review
              -> Paper/small live
```

它解决的核心问题是：

### 10.1 高淘汰率

通过：

```text
hard gates
trial budget
rejected reasons
ablation
cost stress
failure-window veto
```

让弱策略尽早死亡。

### 10.2 高复现性

通过：

```text
config hash
git dirty status
dataset IDs
artifact hashes
evidence bundle
manifest paths
```

让每个研究结论都能追溯。

### 10.3 低自欺风险

通过：

```text
period role contract
report-only enforcement
no-lookahead factor snapshots
holdout 不参与 allocation score
route chronology
trial-count warning
```

防止把验证集、holdout、true-OOS 反复用于调参。

### 10.4 长期积累 edge

通过：

```text
idea registry
edge taxonomy
meta-research dashboard
source success rate
strategy lifecycle
```

让 QTS 逐渐积累真正的研究资产，而不是堆积无法复盘的回测结果。

---

## 11. 最先建议启动的 5 个 Subagent 任务

第一轮不要并行太多。最先开这 5 个：

```text
1. WP-00 Research Baseline Freeze
2. WP-01 Period Role Contract
3. WP-02 Workflow Report Evidence Header
4. WP-03 Research Evidence Registry
5. WP-08 Trade-Level Diagnostics Standard
```

原因：

```text
WP-00 确认当前项目状态。
WP-01 防止 OOS / report-only 被误用。
WP-02 让所有 report 可审计。
WP-03 把研究结果变成 evidence bundle。
WP-08 让当前 q1 VWAP 和后续策略都能被拆解诊断。
```

这 5 个完成后，QTS 会从：

```text
能跑 research workflow
```

升级为：

```text
每次 research 都能被追踪、验收、质疑和复盘的研究系统。
```

---

## 12. 建议 GitHub Issue 模板

每个 WP 可以拆成一个 GitHub issue，使用以下模板。

```markdown
# [WP-XX] <Title>

## Subagent
<Subagent name>

## Objective
<本工作包解决什么问题>

## Scope
### In Scope
- ...

### Out of Scope
- ...

## Files Likely Touched
- ...

## Behavior Contract
- ...

## Required Evidence
- Tests:
  - ...
- Artifacts:
  - ...
- CLI output:
  - ...

## Acceptance Criteria
- [ ] ...
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
- ...
```

---

## 13. 最终目标

这套计划的最终结果不是“又多了几个策略”，而是让 QTS 具备一个真正专业的 Quant Research Operating System：

```text
一个能持续把市场观察转化为假设，
把假设转化为因子证据，
把因子转化为最小策略，
把策略放进严格验证漏斗，
把少数幸存者送入 paper / live，
再用真实表现反哺研究方向的闭环系统。
```

外部搜索、内部诊断、市场机制、回测验证、paper/live 反馈都只是输入。  
真正的护城河是：

```text
高淘汰率
高复现性
低自欺风险
强 evidence discipline
清晰 research-to-production boundary
长期 meta-research feedback loop
```
