# QTS Research System Brief for ChatGPT 5.5 Pro

生成时间: 2026-05-25  
仓库: `/Users/bjhl/Projects/QTS`  
分支/基线提交: `master` / `232c9b1`  
状态说明: 当前工作区存在大量未提交修改和未跟踪 research/route 配置、策略、测试与 graphify 产物。本文件按当前工作区内容整理，而不是只按已提交版本整理。

## 1. 给 ChatGPT 5.5 Pro 的分析目标

请把本文件当作 QTS 项目 research 体系的压缩上下文，重点分析:

- research 架构是否保持了“研究证据”和“可交易执行”边界。
- VWAP 与 Route B-R 多路线研究是否有未来数据泄露、选择偏差、重复调参、报告窗口误用的风险。
- `ResearchSession`、`ResearchWorkflowRunner`、optimizer、portfolio ensemble、production strategy 之间的职责是否清晰。
- 当前证据门禁是否足以支持从 research 到 backtest/paper/live promotion 的人工评审。
- 哪些测试/守卫/文档还不足，哪些配置或流程最容易漂移。

## 2. 项目 research 总原则

QTS 是 Python-first 量化交易系统。research 体系的核心设计不是绕过 runtime/backtest，而是为研究人员提供更易用的 facade 和 workflow:

```text
Research YAML / Workflow YAML
  -> ResearchSession
  -> ResearchWorkflowRunner
  -> BacktestPipeline / BacktestPipelineRunner
  -> shared backtest/runtime/data boundaries
  -> deterministic manifests / JSON summaries / markdown reports
```

关键不变量:

- research 产物只是证据，不自动生成 trading code，不自动进入 paper/live。
- 新 VWAP research 的规范入口只有:

```bash
PYTHONPATH=backend/src uv run python scripts/run_research.py \
  --config configs/research/vwap.yaml \
  workflow configs/research/workflows/vwap_factor_search.yaml
```

- VWAP ad hoc runner 不允许保留或重引入，例如 `scripts/research/run_vwap_*.py`。
- VWAP-specific `configs/optimizer` YAML 不允许作为新研究入口；VWAP sweeps 必须进入 canonical workflow YAML。
- optimizer/backtest matrix 必须走 `BacktestPipeline`，不能手写 vectorized backtest 或直接调用 strategy internals。
- 研究、优化、报告窗口必须预声明且时间有序；report-only/OOS 窗口不能反向调参，除非开启新的研究记录。
- research workflow 禁止配置包含 `broker`、`live`、`paper`、`orders`、`runtime`、`trade`、`promote` 等会模糊边界的 key。

## 3. 规范 Flow

来自 `docs/architecture/system_flows.md` 的相关 Flow:

### FLOW-RESEARCH

- Canonical entrypoint: `scripts/run_research.py --config <research-config> workflow <workflow-config>`。
- Config owner: `ResearchSessionConfig` 管 research session YAML；`ResearchWorkflowConfig` 管 workflow YAML。
- Allowed owners: `qts.research`、`qts.factors`、`qts.indicators`、reviewed strategy boundaries、thin CLI、`qts.backtest` public path。
- Future-data risk: datasets、factor snapshots、forward labels、train/test/OOS windows、validation windows 均可能泄漏未来信息，必须预声明、时间有序。
- Required verification: research session/workflow/factor/tearsheet unit tests，`scripts/run_research.py` integration tests，optimizer/backtest tests，人工确认 research artifact 未被 paper/live 直接消费。

### FLOW-OPTIMIZER

- Canonical entrypoint: 从 FLOW-RESEARCH 的 `optimize` step 调 `ResearchSession.optimize(...)`，或 generic `scripts/run_optimizer.py <config>`。
- Config owner: `qts.research.optimizer` 管 parameter grid、objective metric、constraints、walk-forward、failure-window veto、validation summary。
- Future-data risk: candidate selection 只能使用本 step 声明的训练/验证证据；report-only/OOS 只能验证或拒绝，不能用于早期选择。
- Forbidden shortcuts: 手写 optimizer backtest path、直接调 strategy internals、改 market/session/risk/execution/account semantics、静默丢弃失败 run。

### FLOW-BACKTEST

- Research 中的 backtest 入口允许是 `ResearchSession.run_backtest(...)` 或 `BacktestPipelineRunner`。
- 回测结果可作为 research/promotion evidence，但本身不启用 paper/live。

### FLOW-PROMOTION

- research/optimizer/backtest/paper evidence 只能进入人工 promotion review。
- research acceptance、optimizer ranking、backtest PnL、paper success 都不是自动 promotion。

## 4. 主要源码结构

| 区域 | 路径 | 角色 |
| --- | --- | --- |
| Research facade | `backend/src/qts/research/session.py` | Notebook/CLI friendly facade。加载 research config，提供 history、backtest、optimizer、factor discovery/evaluation、experiment store API。 |
| Research data book | `backend/src/qts/research/research_book.py` | 只读历史数据 facade。基于 `HistoricalCatalog`、CSV dataset、bar aggregation。`HistoryRequest` 使用 `[start, end)`。 |
| Workflow engine | `backend/src/qts/research/workflow.py` | Gate-based orchestration。解析 workflow YAML，执行 step，阻断 failed/blocked gates。 |
| Optimizer | `backend/src/qts/research/optimizer/` | Parameter grid、pipeline runner、constraints、validation summary、walk-forward、failure-window veto。 |
| Factor discovery | `backend/src/qts/research/factor_discovery.py` | 从 Semantic Scholar/OpenAlex/Crossref/arXiv 抽取 source-backed factor ideas，缓存、去重、过滤非交易主题和撤稿。 |
| Factor specs | `backend/src/qts/research/factor_spec.py`, `factor_spec_store.py` | 把 factor idea 转为非执行、人工评审的 factor hypothesis draft。 |
| Factor evaluation | `backend/src/qts/research/factor_evaluation.py`, `tearsheet.py` | 对 factor scores 和 forward returns 计算 rank IC、long-short spread、coverage、turnover，写 deterministic artifacts/tearsheets。 |
| Experiment evidence | `experiment_manifest.py`, `experiment_store.py`, `experiment_recorder.py` | 生成 hashable manifest，JSONL index，记录 metrics/config/artifact hashes。 |
| Portfolio research | `portfolio_ensemble.py` | 基于已完成 equity curves 做 research-only static allocation scan 和 volatility-managed allocation scan。 |
| Report writer | `report.py` | 从 workflow results 生成 deterministic markdown research report，并声明 non-promotion boundary。 |
| Thin CLI | `scripts/run_research.py` | CLI: `factor-tearsheet`、`runs`、`workflow`。 |
| Optimizer CLI | `scripts/run_optimizer.py` | 支持旧 factory-driven 和新 pipeline-driven optimizer；pipeline path 走 shared `BacktestPipelineRunner`。 |

## 5. ResearchSession API 摘要

`ResearchSessionConfig.from_yaml(path)` 读取配置:

- `data.config`: historical data config。
- `data.catalog`: catalog name。
- `data.roots`: roots，例如 `GC`, `SI`。
- `data.timeframe`: research 默认 timeframe。
- `data.instrument_ids`: symbol 到 `InstrumentId` 的可选映射。
- `backtest_config`: 默认 backtest config。
- `store`: experiment store root。
- `output_root`: backtest/evaluation/experiment output root。
- `objective_metric`: 默认 `sharpe_ratio`。
- `discovery.sources`, `discovery.max_results`。

主要 public methods:

- `history(...)`, `history_frame(...)`: 通过 `ResearchBook` 取历史 bars。
- `parameter_grid(...)`: notebook-friendly parameter grid。
- `run_backtest(...)`: 通过 `BacktestPipeline.from_yaml(...)` 构造 engine 并 `run_streaming(...)`。
- `run_backtest_matrix(...)`: 对 period/candidate matrix 运行同一个 cached `BacktestPipeline`，输出 per-run manifest metrics。
- `optimize(...)`: 交给 `BacktestPipelineRunner` 做 parameter sweep。
- `validate_optimizer_walk_forward(...)`: 对 selected candidates 做 train/test window rerun。
- `validate_optimizer_failure_window_veto(...)`: 对 selected candidates 做 failure/adverse windows rerun，支持 report-only windows。
- `record_manifest(...)`, `list_runs(...)`, `compare_runs(...)`, `compare_frame(...)`: 管 experiment store。
- `discover_factors(...)`, `find_factor_candidates(...)`: 文献/metadata 驱动的 source-backed idea discovery，生成非执行 factor specs。
- `review_factor_spec(...)`, `review_queue_frame(...)`: 人工评审队列。
- `evaluate_factor(...)`, `factor_tearsheet(...)`, `record_factor_tearsheet(...)`: deterministic factor evaluation 和 manifest 记录。
- `start_experiment(...)`: context-managed experiment recorder。

设计意图: `ResearchSession` 可以方便 notebooks/scripts，但任何 executable evidence 仍通过 backtest pipeline 或 factor evaluation deterministic artifacts。

## 6. ResearchWorkflow step kinds

`ResearchWorkflowConfig` 只允许以下 step kind:

- `factor_candidates`: 搜索 factor ideas，draft non-executable factor specs 并持久化。
- `factor_review_gate`: 要求 store 中有足够数量的指定 review status spec，失败时 hard stop。
- `implementation_gate`: 要求模块或 strategy 可 import/resolve。只允许检查 `qts.factors`、`qts.indicators`、strategy boundary，禁止 internal runtime imports。
- `factor_evaluation`: 从 factor score/forward return snapshots 生成 evaluation JSON artifacts。
- `factor_tearsheet`: 汇总 factor evaluation artifacts，可记录 experiment manifest。
- `backtest`: 单次 shared backtest pipeline run。
- `backtest_matrix`: candidate x period matrix，写 summary JSON。
- `optimize`: parameter sweep，支持 validation constraints、walk-forward、failure-window veto、capital metrics。
- `portfolio_ensemble`: research-only completed equity curve allocation evaluation。
- `portfolio_ensemble_scan`: static weight grid scan。
- `portfolio_volatility_managed_scan`: no-lookahead volatility-managed allocation scan。
- `research_report`: 写 deterministic markdown report。

Hard stop step kinds:

- `factor_review_gate`
- `implementation_gate`

workflow 选择参数:

- `--step <id>`: 只跑一个 step。
- `--from-step <id>` / `--to-step <id>`: 选定 step range。
- 互斥或未知 selection 会被 CLI/integration tests 拦截。

## 7. Optimizer 体系

核心类:

- `ParameterSpace`: 一个 parameter 维度，必须有非空 name 和 values。
- `ParameterGrid`: 多维 cartesian product，按声明顺序稳定迭代，leftmost varies slowest。
- `BacktestPipelineJob`: 用 backtest config + parameter grid + output root + objective metric 描述 sweep。
- `BacktestPipelineRunner`: 每个 combination 使用 `base_pipeline.with_strategy_params(...)`，然后 `build_engine().run_streaming(...)`，从 manifest 读 objective，按 objective 降序排序。
- `OptimizationResult`: `parameters`, `manifest_path`, `manifest_hash`, `objective_value`。

Validation:

- `MetricConstraint`: 从 manifest 的 `statistics` 或 `metrics` 读取 Decimal metric，支持 `>`, `>=`, `<`, `<=`, `==`。
- `OptimizerValidationSummary`: 汇总 accepted/rejected runs 和 rejection reasons。
- `derive_capital_metrics(...)`: 从 manifest 派生 `pnl_usd`, `pnl_per_trade`, `return_on_margin_proxy`, `gross_pnl_before_recorded_cost` 等，用于 margin/capital-aware constraints。

Walk-forward:

- `WalkForwardSplit`: `train_start/train_end/test_start/test_end`，要求窗口有序且 train/test 不重叠。
- `BacktestWalkForwardValidationRunner`: 对 selected candidates 在每个 split 的 train/test 两个 phase rerun。
- `WalkForwardRobustnessPolicy`: 可要求 min windows、max losing windows、min pnl 等聚合条件。

Failure-window veto:

- `FailureWindow`: adverse window，name 是 safe path segment，`start < end`。
- `FailureWindowVetoRunner`: selected candidates 在 veto windows 和 report-only windows 上 rerun。
- `FailureWindowVetoSummary`: candidate-level accepted/rejected decision；report-only window 单独记录，不应参与 selection。
- `require_passing_candidate: true` 时，如果没有 candidate 通过 failure-window constraints，workflow step 会 `blocked`。

## 8. Portfolio ensemble research

`backend/src/qts/research/portfolio_ensemble.py` 明确是 research-only:

- 输入是已完成 backtest manifest 的 equity curve artifact。
- `evaluate_portfolio_ensemble(...)` 对多条 equity curves 按权重合成，输出 full curve metrics 和 reporting-grid metrics。
- `scan_portfolio_ensemble_allocations(...)` 扫 static weight grid，按 constraints 和 score 排序。
- `scan_volatility_managed_allocations(...)` 扫 volatility-managed parameter grid；测试声明其权重使用 prior returns，避免未来数据。
- 输出 payload 包含 `research_only: true`。

需要 ChatGPT 特别审查:

- allocation scan 的 baseline/post periods 是否会把 holdout 反馈到选择。
- volatility-managed weights 的历史窗口是否严格只用 prior observations。
- summary JSON 是否足以防止后续人工误读为可交易 portfolio config。

## 9. 配置入口和文件族

Research session configs:

- `configs/research/quickstart.yaml`: 单 `GC` quickstart。
- `configs/research/vwap.yaml`: canonical VWAP research session，`roots: [GC, SI]`，`timeframe: 1m`，`backtest_config: ../backtest.vwap_factor_research.yaml`，store/output root 在 `runs/research/vwap`。
- `configs/research/vwap_gc_*.yaml`, `configs/research/vwap_si_*.yaml`: symbol/timeframe-specific long research configs。

Workflow configs:

- `configs/research/workflows/quickstart.yaml`
- `configs/research/workflows/vwap_factor_search.yaml`: canonical all-route VWAP workflow。
- 多个 GC 15m round workflows: feature ablation、long search、round01-round27、sigma transfer。
- 多个 SI 15m round workflows: feature ablation、long search、round01-round21。
- GC/SI 5m、long search variants。

Backtest configs:

- VWAP research: `configs/backtest.vwap_factor_research*.yaml`
- VWAP production pullback: `configs/backtest.vwap_production_pullback_gc.yaml`, `configs/backtest.vwap_production_pullback_si.yaml`
- Route B-R research configs: `configs/backtest.route_*.yaml`

Strategy configs:

- `configs/strategies/vwap_factor_research.yaml`
- `configs/strategies/vwap_production_pullback_gc.yaml`
- `configs/strategies/vwap_production_pullback_si.yaml`
- general examples: `gc_momentum`, `gc_si_momentum`, `vwap_pullback`

## 10. Canonical VWAP workflow map

主 workflow: `configs/research/workflows/vwap_factor_search.yaml`

Early/core steps:

- `discover`: `factor_candidates`，查询 VWAP、intraday futures、regime filter、trend strength、volatility timing、ATR/VWAP slope、order-flow、opening drive、volume curve、liquidity、commodity futures/gold。
- `implementation`: 确认 `strategies.research.vwap_factor_research:VwapFactorResearchStrategy`。
- `baseline`: 使用 `backtest.vwap_production_pullback_gc.yaml` 运行 production baseline。
- `structural-candidates`: `optimize`，目标 `sharpe_ratio`，使用 risk-budget sizing、quality filters、partial runner，包含 validation constraints 和 failure-window veto。
- `gc-15m-stable-annualized-scale`: `backtest_matrix`，验证 GC 15m stable annualized scale / quantity variants。
- `report`: 输出 `runs/research/vwap/reports/vwap-factor-search-report.md`。

Route lanes:

| Route | 主题 | 代表策略/步骤 |
| --- | --- | --- |
| B | VWAP rolling + dual supertrend comparison | `route-b-vwap-gc-rolling`, `route-b-vwap-si-rolling`, `route-b-dual-supertrend-gc/si` |
| C | Vol target trend | `examples.strategies.vol_target_trend:VolTargetTrendStrategy` |
| D | GC/SI ratio mean reversion | `examples.strategies.gc_si_ratio_mean_reversion:GcSiRatioMeanReversionStrategy` |
| E | Carry trend overlay | `examples.strategies.carry_trend_overlay:CarryTrendOverlayStrategy` |
| F | Dual momentum rotation | `examples.strategies.dual_momentum_rotation:DualMomentumRotationStrategy` |
| G | Risk-managed dual momentum | same dual momentum strategy with risk-management params |
| H | Drawdown-gated dual momentum | same strategy with drawdown/cooldown gate |
| I | Threshold-confirmation dual momentum | same strategy with confirmation thresholds |
| J | Research-only portfolio ensembles | multiple `portfolio_ensemble` steps over completed manifests |
| K | Allocation scan | `portfolio_ensemble_scan` |
| L | Volatility-managed allocation scan | `portfolio_volatility_managed_scan` |
| M | Multi-horizon dual momentum | `route-m-multi-horizon-dual-momentum` |
| N | Carry momentum rotation | `examples.strategies.carry_momentum_rotation:CarryMomentumRotationStrategy` |
| O | Opening range breakout | `examples.strategies.opening_range_breakout:OpeningRangeBreakoutStrategy` |
| P | Intraday ratio mean reversion | GC/SI ratio strategy on intraday config |
| Q | Opening range risk refinement | opening range breakout with refined risk params |
| R | Vol-managed allocation refinement | volatility-managed scan variant |

Common period protocol used by many routes:

- `is_2020_2022`: in-sample selection window.
- `validation_2022_2024`: validation window.
- `holdout_2024_2026`: report-only holdout, not tuning.
- `anchor_2010_2020`: older anchor/stability window.
- Some VWAP structural validation also uses `failure-2022`, `failure-2023`, `failure-2024`, plus report-only `report-known-2025` and `true-oos-after-2026-01-01`.

Critical analysis point: the workflow file encodes many route experiments in one canonical workflow. This is good for central governance, but it also creates risk that later route observations influence earlier candidate selection unless reports preserve selection chronology and report-only semantics.

## 11. Strategy research/production boundary

Research strategy:

- `strategies/research/vwap_factor_research.py`
- Main class: `VwapFactorResearchStrategy`
- Purpose: rich parameter/factor-filter research harness for VWAP pullback logic.
- Feature/filter themes from tests and config:
  - VWAP slope strength
  - ATR percent range
  - session sigma range
  - moving-average alignment
  - technical score filters
  - VWAP acceptance
  - trend efficiency / trend age
  - range expansion
  - bad-regime conditional tightening
  - RTH drive strength
  - rejection quality
  - session entry limit
  - risk budget sizing
  - partial runner exits
  - early no-progress exits/reductions
  - detailed factor diagnostics in intent metadata

Production strategy:

- `strategies/production/vwap_production_pullback.py`
- Main classes:
  - `VwapProductionPullbackStrategy`
  - `GcVwapProductionPullbackStrategy`
  - `SiVwapProductionPullbackStrategy`
- Production configs point to GC/SI wrappers, not the research strategy.
- Tests assert production does not depend on research strategy and formal config rejects research-blocked-session shortcuts.

Example route strategies:

- `examples/strategies/dual_supertrend.py`
- `examples/strategies/vol_target_trend.py`
- `examples/strategies/gc_si_ratio_mean_reversion.py`
- `examples/strategies/carry_trend_overlay.py`
- `examples/strategies/dual_momentum_rotation.py`
- `examples/strategies/carry_momentum_rotation.py`
- `examples/strategies/opening_range_breakout.py`

Potential concern: route strategies live under `examples/strategies` but are used in serious research matrices. If they become promotion candidates, they likely need explicit promotion review and possibly relocation or stronger ownership documentation.

## 12. Data and calendar boundaries

Research history:

- `ResearchBook` loads `HistoricalCatalog` from configured data YAML.
- `HistoryRequest` validates `TimeInterval(start, end)` and uses `[start, end)` inclusion.
- CSV bars are read via `iter_historical_bars(...)`.
- If source timeframe differs from request timeframe, aggregation uses `BarAggregationPipeline` with exchange timezone and session window.

Domain facts from docs/tests:

- Market sessions are domain facts; timezones are representations.
- All bars use half-open intervals `[start, end)`.
- `<1d` bars are clock-aligned in exchange timezone.
- `1d` bars are session-aligned, not 24h bars.
- Exchange/session behavior needs anchor tests.

Materialized replay cache:

- Research/workflow/optimizer can pass `materialized_replay_cache`.
- Integration tests assert materialized replay cache preserves backtest metrics.
- This is performance/caching infrastructure; it must not change strategy/data semantics.

## 13. Artifacts and evidence model

Expected outputs:

- Backtest run dirs under `runs/research/...`
- Backtest `manifest.json` files and equity curve artifacts from shared reporting/backtest pipeline.
- Optimizer per-combination run dirs: `run-0000`, `run-0001`, ...
- Validation summaries: JSON files, e.g. `runs/research/vwap/validation/*.json`
- Backtest matrix summaries: `*-summary.json`
- Portfolio ensemble summaries: route-specific JSON files with `research_only: true`
- Workflow markdown reports: `runs/research/.../reports/*.md`
- Experiment store index: `<store>/experiments.jsonl`
- Experiment manifests: deterministic JSON with:
  - `experiment_id`
  - `platform_baseline_version`
  - `strategy_name`, `strategy_version`
  - `factor_versions`
  - `dataset_ids`
  - `config_hash`
  - `artifact_hashes`
  - `artifact_paths_by_hash`
  - `metrics`

Important evidence invariant: metrics should be linked to exact config/artifacts/manifests. Any promotion decision should cite hashes and paths, not just copied PnL values.

## 14. CLI usage

Canonical VWAP:

```bash
PYTHONPATH=backend/src uv run python scripts/run_research.py \
  --config configs/research/vwap.yaml \
  workflow configs/research/workflows/vwap_factor_search.yaml
```

Run one workflow step:

```bash
PYTHONPATH=backend/src uv run python scripts/run_research.py \
  --config configs/research/vwap.yaml \
  workflow configs/research/workflows/vwap_factor_search.yaml \
  --step structural-candidates
```

Run a step range:

```bash
PYTHONPATH=backend/src uv run python scripts/run_research.py \
  --config configs/research/vwap.yaml \
  workflow configs/research/workflows/vwap_factor_search.yaml \
  --from-step route-b-implementation \
  --to-step route-b-report
```

List recorded runs:

```bash
PYTHONPATH=backend/src uv run python scripts/run_research.py \
  --config configs/research/vwap.yaml \
  runs --sort-by sharpe_ratio --limit 20
```

Generic optimizer CLI:

```bash
PYTHONPATH=backend/src uv run python scripts/run_optimizer.py <optimizer-config.yaml> \
  --output-root runs/optimizer \
  --validation-output runs/optimizer/validation.json \
  --experiment-store runs/research/optimizer-store
```

Note: generic optimizer supports factory-driven legacy shape and pipeline-driven backtest-config shape. VWAP optimizer work should be inside canonical research workflow, not separate VWAP optimizer YAML.

## 15. 测试和守卫覆盖

Research unit tests:

- `tests/unit/research/test_research_session.py`
- `tests/unit/research/test_research_workflow.py`
- `tests/unit/research/test_research_book.py`
- `tests/unit/research/test_parameter_grid.py`
- `tests/unit/research/test_optimizer_constraints.py`
- `tests/unit/research/test_optimizer_walk_forward.py`
- `tests/unit/research/test_optimizer_failure_veto.py`
- `tests/unit/research/test_factor_discovery.py`
- `tests/unit/research/test_factor_spec.py`
- `tests/unit/research/test_factor_spec_store.py`
- `tests/unit/research/test_factor_evaluation.py`
- `tests/unit/research/test_tearsheet.py`
- `tests/unit/research/test_experiment_manifest.py`
- `tests/unit/research/test_experiment_store.py`
- `tests/unit/research/test_experiment_recorder.py`
- `tests/unit/research/test_portfolio_ensemble.py`
- `tests/unit/research/test_research_report.py`

Integration tests:

- `tests/integration/test_run_research_cli.py`
  - CLI records factor tearsheet/list runs.
  - workflow blocks on review gate.
  - selected step/range behavior.
  - backtest and optimize after gates.
  - canonical VWAP optimize matches direct session metrics.
  - implementation gate blocks missing code.
- `tests/integration/test_optimizer_consumes_backtest_config.py`
  - optimizer CLI consumes backtest config.
  - pipeline sweeps params from strategy config.
  - materialized replay cache preserves metrics.

Strategy tests:

- `tests/unit/strategies/test_vwap_factor_research.py`: extensive factor filter, sizing, exit, diagnostics coverage.
- `tests/unit/strategies/test_vwap_regime_pullback.py`: production VWAP wrappers/configs, no research dependency, regime gate behavior.
- `tests/unit/strategies/test_dual_supertrend.py`
- `tests/unit/strategies/test_dual_momentum_rotation.py`
- `tests/unit/strategies/test_vol_target_trend.py`
- `tests/unit/strategies/test_opening_range_breakout.py`
- route-specific tests for carry/ratio/momentum variants.

Architecture/guardrails:

- `scripts/verify_guardrails.py`
- `make guardrails`
- Required normal code checks per repo instructions:

```bash
make format
make lint
make guardrails
make typecheck
make test-unit
```

For research/runtime interaction changes, also run integration/anchor tests as applicable.

## 16. 已知强点

- Research facade delegates executable evidence to shared `BacktestPipeline` instead of creating an independent research backtest path.
- Workflow schema has explicit allowed step kinds and forbidden trading/promotion keys.
- Implementation gate checks importability without generating code.
- Optimizer validation produces explicit accepted/rejected evidence and reasons.
- Walk-forward and failure-window structures model temporal validation rather than a single global score.
- Production VWAP strategy is separated from research strategy, with tests asserting no dependency.
- Portfolio ensemble outputs carry `research_only: true`.
- Tests encode many research invariants, especially canonical VWAP workflow structure and no legacy VWAP optimizer configs.

## 17. 主要风险点

1. Canonical workflow is very large.
   - Pros: one governed place.
   - Risk: many routes and reports in one file can obscure chronology and selection policy.

2. Report-only semantics are policy-driven.
   - YAML marks holdout/OOS/report-only windows, but downstream human interpretation can still misuse them unless reports clearly separate selection vs validation vs report-only.

3. Route strategies under `examples/strategies`.
   - They are used for serious research; promotion path should require review, possibly stronger module ownership, and docs updates.

4. Factor discovery depends on external scholarly metadata.
   - Discovery is source-backed and cached, but relevance/tag heuristics are not equivalent to financial validity.

5. Factor evaluation snapshots can leak future returns if snapshots/forward returns are prepared incorrectly.
   - The evaluation code is deterministic, but correctness depends on the input construction protocol.

6. Portfolio ensemble can overfit allocations.
   - Static and volatility-managed scans need strict selection-period discipline and explicit holdout treatment.

7. Materialized replay cache must remain semantics-preserving.
   - Existing tests cover metric preservation, but any data/schema/session change should rerun integration/anchor tests.

8. Experiment manifests are strong evidence containers, but not a complete promotion gate.
   - Promotion still needs human approval, exact config/capital/account context, and paper/live readiness evidence.

## 18. 建议 ChatGPT 重点审查的问题

### A. Future-data / OOS discipline

- `vwap_factor_search.yaml` 中每个 route 的 `is_2020_2022`、`validation_2022_2024`、`holdout_2024_2026`、`anchor_2010_2020` 是否被一致使用？
- `holdout_2024_2026` 是否只用于 report-only，不影响 candidates？
- `true-oos-after-2026-01-01` 是否永远是 report-only？
- 是否需要在 report writer 中强制输出 selection/validation/report-only 分类？

### B. Optimizer gate sufficiency

- `structural-candidates` 的 constraints 是否过松或过度依赖少数 trades？
- `failure_window_veto.require_passing_candidate: false` 是否合理，还是会让失败窗口只作为 evidence 而不阻断？
- Walk-forward robustness policy 是否应该成为 canonical VWAP workflow 的硬门禁？

### C. Route proliferation

- Route B-R 是否已经超过单一 workflow 的可维护范围？
- 是否应该拆成 route sub-workflows，同时保留一个 canonical index/manifest？
- 当前 route report 是否能让审查者知道哪些 route 是探索、哪些是候选、哪些已经被拒绝？

### D. Research to production boundary

- `VwapProductionPullbackStrategy` 是否完整复制/固化了 research-selected logic，还是仍有配置漂移风险？
- GC/SI production wrappers 是否足够防止 accidental research params leak？
- 如果某个 `examples/strategies` route 进入 promotion，哪些文件必须移动、测试、文档化？

### E. Evidence artifacts

- 当前 manifest/summary/report 是否足以重建一次研究结论？
- 是否应该把 workflow config hash、git commit、dirty status、dataset identity、backtest config hash 写入每个 workflow report？
- 是否应该为 route-level report 增加 explicit “selection basis” 与 “not used for tuning” section？

### F. Tests and guardrails

- 是否有 guardrail 防止 `configs/research/workflows/vwap_factor_search.yaml` 中新增 step 使用 forbidden future windows？
- 是否有测试确保 route J/K/L/R portfolio scans 不把 holdout 纳入 score？
- 是否有 architecture test 防止 research workflow import runtime/broker/order/risk internals？
- 是否需要 snapshot tests 锁定 canonical workflow step order？

## 19. 推荐的下一步改进

短期:

- 在 research report 中显示每个 period/window 的 role: `selection`, `validation`, `holdout_report_only`, `anchor`, `true_oos_report_only`。
- 在 workflow summary JSON 中写入 `workflow_config_path`, workflow config hash, git commit, dirty status。
- 给 canonical VWAP workflow 增加 machine-readable route metadata，避免 route policy 只在 step id/report metadata 中体现。

中期:

- 把 Route B-R 拆成 route-specific workflow files，并用一个 canonical meta-workflow 或 manifest 索引。
- 为 `portfolio_ensemble_scan` 和 `portfolio_volatility_managed_scan` 增加更强的 period-role checks。
- 将 promotion 候选从 `examples/strategies` 迁移到正式 strategy boundary，并补充 docs/guardrails。

长期:

- 建立 research evidence registry，把 workflow run、config hash、dataset hash、backtest manifest、report、review decision 统一成 promotion-ready evidence bundle。
- 引入 architecture guardrail，防止 research code 直接依赖 broker/runtime/order/risk internals。
- 对 factor snapshot/forward-return generation 建立专门的 no-lookahead anchor tests。

## 20. Source map

核心源码:

- `backend/src/qts/research/session.py`
- `backend/src/qts/research/workflow.py`
- `backend/src/qts/research/research_book.py`
- `backend/src/qts/research/optimizer/pipeline.py`
- `backend/src/qts/research/optimizer/walk_forward.py`
- `backend/src/qts/research/optimizer/failure_veto.py`
- `backend/src/qts/research/optimizer/validation.py`
- `backend/src/qts/research/factor_discovery.py`
- `backend/src/qts/research/factor_spec.py`
- `backend/src/qts/research/factor_spec_store.py`
- `backend/src/qts/research/factor_evaluation.py`
- `backend/src/qts/research/tearsheet.py`
- `backend/src/qts/research/portfolio_ensemble.py`
- `backend/src/qts/research/report.py`

入口:

- `scripts/run_research.py`
- `scripts/run_optimizer.py`
- `scripts/run_backtest.py`

关键配置:

- `configs/research/vwap.yaml`
- `configs/research/workflows/vwap_factor_search.yaml`
- `configs/backtest.vwap_factor_research*.yaml`
- `configs/backtest.vwap_production_pullback_gc.yaml`
- `configs/backtest.vwap_production_pullback_si.yaml`
- `configs/backtest.route_*.yaml`
- `configs/strategies/vwap_factor_research.yaml`
- `configs/strategies/vwap_production_pullback_gc.yaml`
- `configs/strategies/vwap_production_pullback_si.yaml`

关键策略:

- `strategies/research/vwap_factor_research.py`
- `strategies/production/vwap_production_pullback.py`
- `examples/strategies/dual_supertrend.py`
- `examples/strategies/vol_target_trend.py`
- `examples/strategies/gc_si_ratio_mean_reversion.py`
- `examples/strategies/carry_trend_overlay.py`
- `examples/strategies/dual_momentum_rotation.py`
- `examples/strategies/carry_momentum_rotation.py`
- `examples/strategies/opening_range_breakout.py`

关键测试:

- `tests/unit/research/test_research_workflow.py`
- `tests/unit/research/test_research_session.py`
- `tests/integration/test_run_research_cli.py`
- `tests/integration/test_optimizer_consumes_backtest_config.py`
- `tests/unit/strategies/test_vwap_factor_research.py`
- `tests/unit/strategies/test_vwap_regime_pullback.py`
- `tests/unit/research/test_portfolio_ensemble.py`
