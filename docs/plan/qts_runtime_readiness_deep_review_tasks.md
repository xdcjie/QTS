# QTS Runtime 架构最终 Readiness Review 与可执行改进任务

基于最新上传的 `parallel_sequence.html`，本次 review 聚焦三件事：

1. 当前架构是否可以进行 **Backtest / Paper / Live**。
2. 当前实现是否足够简洁，是否仍有冗余、旧入口、过度设计或文档/代码不一致。
3. 如果还存在优化点，将其拆成可并行推进的里程碑和具体 task，每个 task 都有明确目标、实施步骤和验收条件。

> 说明：本 review 基于职责链图、class inventory、方法索引和阶段说明，不等同于逐行源码审计或测试结果审计。因此下面的 readiness 判断是“架构与实现清单层面”的判断；涉及 live capital 的结论必须以自动化测试、paper 外部证据、broker drill、operator signoff 和风控签核共同确认。

---

## 1. 总体结论

### 1.1 是否可以 Backtest

**可以。**

当前 backtest 链路已经形成完整闭环：

```text
BacktestEngine
 -> ReplayMarketDataSource
 -> BacktestActorLoop
 -> MarketDataFlow
 -> StrategyExecutionPipeline
 -> TargetIntentProcessor
 -> OrderPlanBuilder
 -> OrderManagerActor
 -> ExecutionActor
 -> AccountActor
 -> BacktestRuntimeEventSink
 -> BacktestReportWriter
```

从最新 inventory 看，`ReplayClock`、`ReplaySequencedEvent`、`ReplayEventSequencer`、`SubscriptionReplayMarketDataSource`、`ReplayMarketDataBundle`、`ReplayMarketDataSource` 已经存在；`BacktestEngine.run_streaming()`、`BacktestArtifactWriter`、`RuntimeManifest`、`RuntimeEvent`、`RuntimeEventContext`、`require_canonical_envelope()` 也已经出现。说明当前 backtest 已经不是简单 batch 读文件，而是接近 subscription-driven / event-driven replay 的实现。

**可用于：**

```text
1. 策略研究回测。
2. deterministic replay 验证。
3. shared runtime chain 的 dry run。
4. 多策略、多账户拓扑的模拟验证。
5. fill model / risk / account accounting 的回归测试。
```

**但正式使用前仍需补足：**

```text
1. no-lookahead contract tests。
2. bar visible_at / bar end emission tests。
3. 多 instrument 同 timestamp deterministic ordering tests。
4. replay provenance / dataset hash / fill assumptions manifest 校验。
5. BacktestActorLoop 复杂度收敛与职责边界检查。
```

### 1.2 是否可以 Paper

**可以进入受控 Paper 阶段。**

这里要区分两类 paper：

```text
PaperSimulatedRuntimeConfig
  live/replay data + local simulated execution，不连接真实 broker 下单。

PaperBrokerRuntimeConfig
  IBKR paper account + broker API + broker paper order lifecycle。
```

最新实现已经有 `PaperBrokerRuntimeConfig`、`PaperSimulatedRuntimeConfig`、`RuntimeSession`、`RuntimeMarketDataCoordinator`、`StreamingMarketDataSource`、`BrokerExecutionAdapter`、`IbkrOrderExecutionAdapter`、`LiveRuntimeEventSink`、`LiveReportWriter`，并且文档脚注说明 paper 外部证据已经覆盖 market-data、submit/cancel、runtime tiny fill、report manifest 和账户对账。

**可用于：**

```text
1. Paper simulated CI / local verification。
2. IBKR paper Gateway market-data anchor。
3. IBKR paper submit/cancel/tiny fill drill。
4. paper reconciliation drill。
5. operator workflow drill。
```

**但 PaperBroker 仍应带限制：**

```text
1. 只允许白名单账户 DU...。
2. 只允许 paper Gateway 端口 4002，除非显式 override 并记录 evidence。
3. 每次启动必须输出 startup checklist、topology hash、config hash、event schema version。
4. 所有 paper broker callback 乱序、重复、late commission、reconnect 都必须进入测试矩阵。
```

### 1.3 是否可以 Live

需要拆成两档：

| 模式 | 当前判断 | 原因 |
|---|---:|---|
| Live observation | 可以 | 已有 `RuntimeSession`、`StreamingMarketDataSource`、IBKR market-data boundary、runtime sink、manifest、safety/reconciliation 组件。 |
| Live code-path ready | 基本可以 | shared runtime chain 已完成，live/paper 通过 broker boundary 接入。 |
| Live capital | 暂不建议开启 | 最新文档脚注仍明确 live capital 必须保持 disabled，直到运维、工程、风控签核完成。 |

**Live capital 启用前必须满足：**

```text
1. operator signoff 是强制 gate，不是 manifest 字段。
2. allow_live_orders 必须显式开启，默认 false。
3. U... live account、4001 live port、broker account kind、RuntimeMode、LiveOrderPermission 必须一致。
4. IBKR read-only / order permission / market-data permission 必须检查。
5. startup reconciliation 必须通过。
6. broker reconnect 后必须重新 reconciliation 才能恢复 order submission。
7. stale/delayed/frozen market data 必须进入 RiskEngine reject。
8. kill switch / rollback / cancel active orders drill 必须通过。
9. event store / snapshot store 必须具备 durable write evidence。
10. unresolved broker callback quarantine 必须阻断 live resume。
```

---

## 2. 当前架构简洁性与冗余 Review

### 2.1 已经明显改善的点

```text
1. 主 runtime 已经从 LiveRuntimeSession 语义迁移到 RuntimeSession。
2. paper 语义拆成 PaperBrokerRuntimeConfig 与 PaperSimulatedRuntimeConfig。
3. Broker 测试替身已收敛到 production-adjacent 的 SimulatedBrokerAdapter；FakeStreamingMarketDataAdapter 仍位于 qts.testing.fakes。
4. IBKR order transport 已拆出 connection、order client、callback dispatcher、event emitter、order id allocator。
5. RuntimeEventContext 已经负责 run-scoped defaults 和 monotonic sequence number。
6. MarketDataFreshnessRiskRule / MarketDataPermissionRiskRule 已经出现，说明 market-data 状态开始进入 risk gate。
7. SignalPolicyEngine / SignalAggregationDecision / SignalConflict 已经出现，多策略冲突不再只是隐式 aggregate。
8. ReportWriter / RuntimeArtifactWriter 源码 inventory 已经显示为稳定 boundary contract，不再是 placeholder contract。
```

这些变化说明当前架构已经从“概念型统一流程”推进到“可运行统一流程”。

### 2.2 仍然存在的简洁性 / 冗余问题

#### 问题 A：文档/索引存在旧信息残留

同一个最新 HTML 中同时出现了：

```text
1. 当前实现清单指向 qts/runtime/config/models.py。
2. 阶段卡仍写 backend/src/qts/runtime/config.py。
3. source inventory 中 ReportWriter 是稳定 boundary。
4. 分组 inventory 中仍出现 ReportWriter / RuntimeArtifactWriter 的 placeholder wording。
```

这更像是 panorama / source index 生成器混入了旧缓存或旧静态卡片，而不是源码一定仍旧。但对 review 来说，这是高风险问题：架构文档是 code review 的入口，旧信息会误导评审，也会让 guardrail 结果不可置信。

#### 问题 B：`LiveRuntime` 仍然存在

最新主链路已经使用 `RuntimeSession`，但 inventory 仍有：

```text
backend/src/qts/runtime/live.py:309 LiveRuntime
```

并且 `LiveRuntime` 仍有：

```text
degrade()
recover()
apply_runtime_event()
submit_order()
```

这说明系统中仍有第二个 runtime-like 入口。即使它只是 legacy wrapper，也需要明确 deprecate / remove / alias-only。否则后续可能出现：

```text
1. application/API 调 RuntimeSession。
2. test/helper 调 LiveRuntime。
3. 两边行为不一致。
4. live safety gate 只覆盖其中一边。
```

#### 问题 C：`qts/runtime/live.py` 文件名仍偏历史语义

`runtime/live.py` 里现在承载的是 `BrokerRuntimeStartupChecklist`、`BrokerRuntimeStartupDecision`、`RuntimeOrderResult`、`LiveRuntime` 等 broker runtime / startup gate 概念。既然主目录原则已经明确 `qts/runtime` 是 backtest/paper/live 共用运行时，那么 `live.py` 这个文件名会持续制造语义债。

建议迁移为：

```text
qts/runtime/broker_startup.py
qts/runtime/broker_runtime.py
qts/runtime/runtime_order_result.py
```

如果 `LiveRuntime` 必须保留，则放入：

```text
qts/runtime/legacy/live_runtime.py
```

并禁止新代码 import。

#### 问题 D：`RuntimeSession` 仍偏重

`RuntimeSession` 当前至少承担：

```text
start / stop / pause / resume
state / topology / account_snapshot
degrade / recover
broker disconnect / reconnect
market-data source event handling
market-data bar handling
kill switch
rollback
intent processing helper
signal aggregation helper
event writing helper
active order lookup
```

这不一定已经过度设计，但它是目前最大的复杂度聚合点。当前已有 `RuntimeMarketDataCoordinator`、`RuntimeSafetyController`、`RuntimeBrokerLifecycleCoordinator`、`RuntimeRecoveryCoordinator`，因此需要确认 `RuntimeSession` 是否只是 facade，还是仍在承担内部业务细节。

#### 问题 E：部分 coordinator 可能是“薄封装 ceremony”

以下类需要做 usage audit：

```text
RuntimeRecoveryCoordinator
RuntimeRollbackCoordinator
BrokerRuntimeStartupGate
RuntimeSafetyController
RuntimeBrokerLifecycleCoordinator
RuntimeMarketDataCoordinator
```

这些类本身不是坏事。交易系统里安全门禁、恢复、rollback 拆开是合理的。但如果某个类只有 1 个方法、1 个调用点、没有状态、没有独立测试价值，就可能是过度设计。

#### 问题 F：493 个 class 说明系统已经进入高复杂度区间

493 个 production classes 对量化交易系统不一定过多，因为里面包含 DTO、Schema、Protocol、ValueObject、ActorMessage、Broker payload、Manifest、测试边界等。但这已经足够高，必须开始用“复杂度预算”管理：

```text
1. 单文件 class 数量预算。
2. 单类 public method 数量预算。
3. 单类私有 helper 数量预算。
4. 单类单调用点 coordinator 是否保留的规则。
5. Protocol 是否有多个实现。
6. DTO / domain / runtime event 是否重复建模。
```

---

## 3. Readiness 分级结论

| 能力 | 当前状态 | 是否可运行 | 附加条件 |
|---|---:|---:|---|
| Backtest research | 架构已完成 | 可以 | 先跑 M1 的 deterministic / no-lookahead / manifest suite。 |
| Backtest production-like validation | 接近 ready | 可以受控使用 | 需要 M1-1 到 M1-4。 |
| Paper simulated | ready | 可以 | 需要纳入 CI smoke。 |
| IBKR paper broker | paper-ready | 可以受控运行 | 需要 paper account allowlist、tiny order drill、reconciliation drill。 |
| Live observation | observation-ready | 可以 | 禁止 order submission。 |
| Live capital | not ready | 不建议 | 必须完成 M0、M2、M3、M6 的 gate。 |

---

## 4. 后续里程碑总览

| Milestone | 目标 | 是否阻断 live capital | 是否可并行 |
|---|---|---:|---:|
| M0 | 清理旧入口、旧文档、guardrail 可信度 | 是 | 高 |
| M1 | Backtest / Paper readiness 验收套件 | 否，但强烈建议 | 高 |
| M2 | Live capital 安全门禁 | 是 | 中 |
| M3 | IBKR robustness 与 failure drill | 是 | 高 |
| M4 | 多策略、多账户隔离正确性 | 是 | 高 |
| M5 | 简洁性、去冗余、反过度设计 | 否，但影响维护性 | 高 |
| M6 | Manifest、event store、operator observability | 是 | 中 |

---

# Milestone 0：旧入口、旧文档与 Guardrail 可信度修复

## Task M0-1：修复 panorama / source inventory 的旧信息残留

### 目标

让架构文档、阶段卡、source inventory 和源码实际路径完全一致，避免 reviewer 看到互相冲突的信息。

### 范围

```text
scripts/update_project_panorama_source_index.py
parallel_sequence.html 生成模板
docs/architecture/backtest_live_parity.md
docs/architecture/runtime_flow.md
```

### 实施步骤

```text
1. 找出阶段卡中仍写 backend/src/qts/runtime/config.py 的模板来源。
2. 统一替换为 backend/src/qts/runtime/config/models.py。
3. 找出分组 inventory 中 ReportWriter / RuntimeArtifactWriter 仍显示 placeholder 的来源。
4. 如果来源是旧静态 HTML 卡片，删除静态卡片，改为从源码 docstring 自动生成。
5. 如果来源是旧缓存，清理缓存并强制每次生成前重建 source index。
6. 在生成脚本中增加 stale text detector：
   - `Boundary placeholder`
   - `live-beta`
   - `backend/src/qts/runtime/config.py`
   - `LiveRuntimeSession`
   - `fake or real boundary adapters`
7. 生成后的 HTML 如果包含上述旧文本，脚本退出码必须非 0。
```

### 验收条件

```text
1. `grep -R "Boundary placeholder" docs/ generated/` 无结果，除非在测试 fixture 中。
2. `grep -R "backend/src/qts/runtime/config.py" docs/ generated/` 无结果，除非明确标注 deprecated。
3. `parallel_sequence.html` 中 ReportWriter 只出现稳定 contract wording。
4. CI 中新增 `test_panorama_has_no_stale_architecture_text`。
5. README 或 docs 中明确：source inventory 以源码为唯一事实来源。
```

---

## Task M0-2：Retire `LiveRuntime`，消除第二 runtime 入口

### 目标

确保生产路径只有一个 broker-capable runtime entrypoint：`RuntimeSession`。

### 范围

```text
backend/src/qts/runtime/live.py
backend/src/qts/runtime/session.py
application/API/CLI/test imports
```

### 实施步骤

```text
1. 搜索所有 LiveRuntime import：
   ripgrep "LiveRuntime" backend/src backend/tests
2. 将生产 import 全部迁移到 RuntimeSession。
3. 如果 LiveRuntime 仅用于历史兼容：
   - 移到 qts/runtime/legacy/live_runtime.py。
   - class docstring 写明 deprecated and test-only compatibility wrapper。
   - 运行时初始化时发 DeprecationWarning。
4. 如果无必要，直接删除 LiveRuntime。
5. 在 qts/runtime/live.py 删除 runtime-like submit_order/degrade/recover 入口。
6. 新增 guardrail：生产代码禁止 import qts.runtime.legacy.live_runtime。
7. 新增测试：RuntimeSession 是唯一可提交 broker order 的 runtime boundary。
```

### 验收条件

```text
1. backend/src 中不存在 `from qts.runtime.live import LiveRuntime`。
2. backend/src 中不存在 `LiveRuntime(` 调用。
3. `RuntimeSession` 是唯一有 broker-capable order submission 的 runtime session entrypoint。
4. guardrail 失败用例能捕获新增的 LiveRuntime 生产 import。
5. 如果保留 legacy wrapper，只有 tests 或 migration fixture 可以 import。
```

---

## Task M0-3：拆分 / 重命名 `qts/runtime/live.py`

### 目标

把 live-specific 文件名改成 broker-runtime / startup-gate 语义，减少 paper/live 混淆。

### 建议命名

```text
qts/runtime/broker_startup.py
  BrokerRuntimeStartupCheck
  BrokerRuntimeStartupChecklist
  BrokerRuntimeStartupDecision
  BrokerRuntimeStartupDecisionStatus

qts/runtime/order_result.py
  RuntimeOrderResult

qts/runtime/legacy/live_runtime.py
  LiveRuntime  # 仅当必须保留
```

### 实施步骤

```text
1. 创建新文件 broker_startup.py，迁移 startup check/decision 类型。
2. 创建 order_result.py，迁移 RuntimeOrderResult。
3. 更新 imports。
4. 在旧 qts/runtime/live.py 中只保留 deprecated re-export，或删除该文件。
5. 添加 RemovedImportNoNewUsageRule：禁止新代码 import qts.runtime.live。
6. 更新 docs、panorama、阶段卡。
```

### 验收条件

```text
1. 新生产代码中不存在 qts.runtime.live import。
2. `BrokerRuntimeStartupChecklist` 的 canonical path 是 qts.runtime.broker_startup。
3. panorama 中不再把 broker startup 类型展示在 runtime/live.py。
4. 旧 import 若保留，必须触发 deprecation warning，并在 docs 中标注 removal date。
```

---

## Task M0-4：GuardrailSuite 进入 CI hard gate

### 目标

确保 guardrail 不是文档说明，而是 CI 必过项。

### 实施步骤

```text
1. 在 CI 中新增命令：
   python -m qts.quality.guardrails backend/src/qts
2. 确认以下 rule 全部运行：
   - ImportBoundaryRule
   - LivePackageNoReplayClassRule
   - ProductionNoFakeClassRule
   - DataLiveNoSharedContractRule
   - TransportCanonicalPathRule
   - RemovedImportNoNewUsageRule
   - ProductionNoTestingImportRule
   - SharedRuntimeWordingRule
   - ProductionPlaceholderDocstringRule
   - BrokerSymbolBoundaryRule
   - ProviderSdkImportRule
   - StrategySdkPublicSurfaceRule
3. 为每条 rule 加一个 positive fixture 和一个 negative fixture。
4. 失败输出必须包含 file path、symbol、rule name、修复建议。
```

### 验收条件

```text
1. CI 中 guardrail 失败会阻断 merge。
2. 每条 rule 至少有一个 violation fixture test。
3. guardrail 输出可被 reviewer 直接定位。
4. 生产代码无 fake/replay/live-package/shared-contract/path 违规。
```

---

# Milestone 1：Backtest / Paper Readiness 验收套件

## Task M1-1：Backtest deterministic replay suite

### 目标

证明相同 config + 相同 dataset + 相同 seed 会生成完全相同的 event stream 和 artifacts。

### 实施步骤

```text
1. 构造最小 dataset：2 个 instrument、2 个 session、多个相同 timestamp bar。
2. 固定 BacktestRuntimeConfig、fill model、risk config、topology。
3. 连续运行 BacktestEngine.run_streaming() 两次。
4. 比较：
   - event NDJSON hash
   - manifest hash
   - order ledger hash
   - fill ledger hash
   - equity curve hash
5. 如果存在 run_id 不同导致 hash 不同，则比较 normalized hash，排除 run_id、created_at。
```

### 验收条件

```text
1. 相同输入的 normalized artifacts hash 完全一致。
2. event sequence_no 单调递增且无 gap。
3. RuntimeEventContext.apply() 生成的 sequence 可复现。
4. 该 suite 纳入 CI。
```

---

## Task M1-2：No-lookahead / bar visible_at contract tests

### 目标

证明策略在 backtest 中无法读取未来 bar。

### 实施步骤

```text
1. 构造 bar：start=10:00, end=10:01, close=100。
2. 策略在 10:00 尝试读取该 bar close，必须不可见。
3. 策略在 10:01 或 visible_at 之后读取，该 bar 才可见。
4. 对 tick/quote/bar 混合数据增加 deterministic priority。
5. 对 resample/aggregation 增加 close 不能提前使用的测试。
6. 对 session boundary 增加 next-open bar 不提前可见的测试。
```

### 验收条件

```text
1. `test_bar_close_visible_only_at_bar_end` 通过。
2. `test_resampled_bar_close_not_visible_before_bucket_end` 通过。
3. `test_multi_instrument_same_timestamp_order_is_deterministic` 通过。
4. 策略 SDK 没有 API 可以绕过 ReplayMarketDataSource 直接读取全量 dataframe。
```

---

## Task M1-3：Backtest manifest 完整性校验

### 目标

让每个 backtest 结果都能解释数据来源和执行假设。

### Manifest 必须包含

```text
runtime_mode
config_hash
topology_hash
event_schema_version
artifact_schema_version
dataset_id
file_hash
row_count
first_ts / last_ts
timezone
adjustment_mode
fill_model_name
fill_model_version
slippage_model
commission_model
partial_fill_policy
broker_capability_model
risk_config_hash
```

### 实施步骤

```text
1. 扩展 RuntimeManifest 或 BacktestReportWriter manifest payload。
2. BacktestEngine._execution_assumptions_payload() 必须输出 fill/cost/capability。
3. ReplayMarketDataBundle.provenance_payload_for() 输出 dataset provenance。
4. 新增 manifest validator。
5. report writer finalize 前执行 validator。
```

### 验收条件

```text
1. 缺少任一必填 manifest 字段时 backtest finalize 失败。
2. report manifest 能反查 dataset file hash。
3. report manifest 能反查 fill model 假设。
4. manifest validator 有 positive/negative tests。
```

---

## Task M1-4：Paper simulated CI smoke

### 目标

证明 PaperSimulatedRuntimeConfig 可在无 broker 的 CI 中完整跑通 live-like runtime chain。

### 实施步骤

```text
1. 使用 FakeStreamingMarketDataAdapter from qts.testing.fakes。
2. 显式注入 SimulatedExecutionAdapter。
3. 构造 RuntimeSession + RuntimeMarketDataCoordinator。
4. 注入一条 market data event。
5. 策略 emit TargetIntent。
6. RiskEngine approve。
7. OrderManagerActor submit。
8. ExecutionActor execute。
9. AccountActor apply fill。
10. LiveRuntimeEventSink 写出 NDJSON。
```

### 验收条件

```text
1. CI 无 IBKR 环境即可通过。
2. 事件链包含 market_data_received、strategy_intent、risk_decision、order_submitted、fill_applied、account_snapshot。
3. event envelope 全部有 run_id、mode、sequence_no、correlation_id。
4. qts.testing.fakes 不被 production code import。
```

---

## Task M1-5：IBKR paper broker lifecycle drill

### 目标

证明 IBKR paper account 能完整完成 submit/cancel/tiny fill/reconciliation/report manifest。

### 实施步骤

```text
1. 新增或完善 application command：ibkr_paper_order_lifecycle_drill。
2. 强制 account code DU...。
3. 强制 paper port 4002，除非 explicit override。
4. submit tiny market/limit order，记录 client_order_id、ibkr_order_id、perm_id。
5. cancel active order 或等待 tiny fill。
6. 收集 orderStatus/openOrder/execDetails/commissionReport。
7. 运行 LiveReconciliation.startup_decision() 与 periodic_check()。
8. 写入 event stream 和 manifest。
```

### 验收条件

```text
1. paper drill artifact 包含 submit/cancel/fill/reconciliation evidence。
2. BrokerOrderMap snapshot 可恢复。
3. commission late arrival 能更新 cost evidence，但不重复 apply fill。
4. paper drill 不允许 live account 或 live port。
```

---

# Milestone 2：Live Capital 安全门禁

## Task M2-1：LiveOrderPermission 强制接入 order path

### 目标

保证 live order submission 不能靠配置遗漏或旧入口绕过。

### 实施步骤

```text
1. 在 RuntimeSession order submission 前检查 LiveOrderPermission。
2. 在 BrokerRuntimeStartupGate.blocked_reason() 中返回 live order permission 状态。
3. 在 RuntimeSafetyController.blocked_reason() 合并：
   - startup decision
   - kill switch
   - market data stale/permission
   - broker degraded
   - unresolved callbacks
   - reconciliation drift
4. 删除或阻断所有绕过 RuntimeSession 的 submit_order path。
5. 新增 tests：
   - live permission OFF blocks order
   - observation mode blocks order
   - paper permission does not allow live account order
```

### 验收条件

```text
1. allow_live_orders=false 时任何 live order 都被拒绝。
2. RuntimeOrderResult 包含 blocked reason 和 evidence。
3. event stream 写出 order_blocked_by_permission。
4. 旧 LiveRuntime 不能绕过该检查。
```

---

## Task M2-2：Live startup gate hard-fail matrix

### 目标

把 live startup checklist 从“记录项”变成“强制阻断项”。

### 必测条件

```text
1. account code 非 U... 时阻断 LIVE。
2. port 非 4001 且无 explicit override 时阻断 LIVE。
3. operator signoff 缺失时阻断 LIVE。
4. market data permission 非 LIVE 时阻断 LIVE orders。
5. event sink 不可写时阻断 LIVE。
6. snapshot store 不可写时阻断 LIVE。
7. reconciliation drift 非空时阻断 LIVE。
8. read-only / broker permission 未确认时阻断 LIVE。
```

### 实施步骤

```text
1. 为 BrokerRuntimeStartupChecklist 增加 check severity：BLOCKER / WARNING / INFO。
2. BrokerRuntimeStartupDecision 根据 BLOCKER 生成 BLOCK。
3. RuntimeSession.start() 读取 decision，未通过则进入 observation/degraded，而不是 active trading。
4. 所有 BLOCKER 写入 manifest 和 RuntimeEventSink。
```

### 验收条件

```text
1. 每个 blocker 都有单测。
2. LIVE mode 下任何 blocker 都不能进入 order-enabled state。
3. PaperBroker mode 下 paper-specific gate 仍生效。
4. manifest 中有 checklist_hash 和每个 check evidence。
```

---

## Task M2-3：Broker reconnect 必须 reconciliation 才能恢复

### 目标

防止断线重连后在未知 broker state 下继续下单。

### 实施步骤

```text
1. RuntimeSession.on_broker_disconnect() 进入 DEGRADED。
2. DEGRADED 状态允许 market data 和 event writing，但禁止新订单。
3. RuntimeSession.on_broker_reconnect() 触发：
   - reqOpenOrders
   - reqPositions
   - reqExecutions since last snapshot
   - reqAccountSummary
4. LiveReconciliation.startup_decision() 通过后才 RuntimeSession.recover()。
5. 若有 drift 或 unresolved callbacks，保持 DEGRADED。
```

### 验收条件

```text
1. reconnect 前新订单全部被拒。
2. reconnect 后 reconciliation 未通过仍拒单。
3. reconciliation 通过后恢复 order submission。
4. event stream 包含 broker_disconnected、broker_reconnected、reconciliation_passed/failed。
```

---

## Task M2-4：Market-data permission / freshness 强制 risk gate

### 目标

确保 delayed/frozen/stale data 不会触发 live capital order。

### 实施步骤

```text
1. MarketDataFlow.risk_context_for() 必须输出 MarketDataRiskContext。
2. MarketDataFreshnessRiskRule 检查 last_event_age。
3. MarketDataPermissionRiskRule 检查 LIVE / DELAYED / FROZEN / UNAVAILABLE。
4. RiskEngine.check() 必须执行这两条 rule。
5. RuntimeSession.on_market_data_source_event() 遇到 permission downgrade 时写 event 并标记 degraded/risk context。
6. 如果配置允许 delayed data，只能用于 observation 或 paper simulated，不能用于 live capital，除非显式 high-risk override 并二次签核。
```

### 验收条件

```text
1. stale data 会产生 risk rejection。
2. delayed data 在 LIVE capital 下会产生 risk rejection。
3. frozen data 在 LIVE capital 下会产生 risk rejection。
4. rejection event 含 strategy_id、account_id、instrument_id、permission_state、last_event_ts。
```

---

## Task M2-5：Kill switch / rollback drill

### 目标

证明 operator 可以在 live/paper runtime 中安全停止新订单，并可选择取消活跃订单。

### 实施步骤

```text
1. RuntimeSafetyController.activate_kill_switch() 输出 RuntimeKillSwitchEvidence。
2. RuntimeSession.activate_kill_switch(cancel_active_orders=True) 路由到 OrderManagerActor / ExecutionActor。
3. RuntimeSession.rollback() 输出 RuntimeRollbackEvidence。
4. kill switch 激活后：
   - market data 继续记录
   - account snapshot 继续记录
   - 新 strategy intent 不进入 order submission
5. kill switch 解除必须有 operator identity、reason code、权限校验。
```

### 验收条件

```text
1. kill switch 激活后新订单被拒。
2. cancel_active_orders=True 时所有 active order 都发出 cancel request。
3. rollback evidence 包含 run_id、state、active_order_ids、snapshot refs。
4. kill switch deactivate 无权限时失败。
```

---

# Milestone 3：IBKR Robustness 与 Broker Failure Drill

## Task M3-1：IBKR callback idempotency / ordering suite

### 目标

证明 IBKR callback 重复、乱序、迟到不会造成重复入账或错误状态推进。

### 测试场景

```text
1. duplicate orderStatus。
2. execDetails 先于 openOrder。
3. openOrder 先于 record_submitted_order。
4. commissionReport 晚于 execution。
5. commissionReport 重复。
6. execution 重复。
7. partial fill 多次到达。
8. cancel status 迟到。
9. permId 缺失。
10. wrong account callback。
```

### 验收条件

```text
1. FillIdempotencyStore 或等价机制只 apply 一次 fill。
2. late commission 更新费用，不重复 apply fill。
3. unresolved callbacks 进入 BrokerCallbackQuarantine。
4. validate_no_unresolved_callbacks() 在 live resume 前强制通过。
5. wrong account callback 被 quarantine，不能更新 AccountActor。
```

---

## Task M3-2：BrokerOrderMap durable restore suite

### 目标

证明 pending / submitted / filled / cancelled order mapping 可从 snapshot 恢复。

### 实施步骤

```text
1. 创建 BrokerOrderMap，record_pending_submission。
2. attach_ibkr_order_id。
3. attach_perm_id。
4. mark_status。
5. snapshot。
6. restore 到新 BrokerOrderMap。
7. 分别用 client_order_id/internal_order_id/ibkr_order_id/perm_id 查询。
8. restore 后继续处理 openOrder/execution/commission。
```

### 验收条件

```text
1. 四种 lookup index restore 后一致。
2. snapshot hash deterministic。
3. restore 后 callback 不丢失归属。
4. 缺少 client_order_id 的 restore payload 会 fail-fast。
```

---

## Task M3-3：IBKR transport split contract tests

### 目标

验证 transport split 后职责没有重新混杂。

### 范围

```text
IbkrTwsConnection
IbkrTwsOrderClient
IbkrTwsCallbackDispatcher
IbkrTwsExecutionEventEmitter
IbkrTwsOrderExecutionTransport
IbAsyncOrderExecutionTransport
```

### 验收条件

```text
1. Connection 不生成 domain ExecutionReport。
2. OrderClient 不处理 callback。
3. CallbackDispatcher 不提交订单。
4. EventEmitter 只做 normalized event publish。
5. OrderExecutionTransport 只做 wiring/facade，不持有重复业务状态。
6. guardrail 能识别 transport/adapters path 混用。
```

---

## Task M3-4：Managed account mismatch quarantine

### 目标

防止 IBKR 多账户环境中错误 account callback 修改本地账户。

### 实施步骤

```text
1. 在 IbkrOrderExecutionAdapter.on_execution/on_position/on_account_summary 中校验 account code。
2. 如果 broker callback account 与 route metadata account 不一致：
   - 不更新 BrokerOrderMap status。
   - 不生成 fill applied。
   - 写入 quarantine。
   - 写 RuntimeEvent。
3. LiveReconciliation 遇到 account mismatch drift 直接 BLOCK。
```

### 验收条件

```text
1. wrong-account execution 不会更新 AccountActor。
2. wrong-account position 不会覆盖 local snapshot。
3. unresolved wrong-account callbacks 阻断 live resume。
4. event payload 不泄漏 sensitive account secret，只保留 masked account code。
```

---

# Milestone 4：多策略、多账户并行正确性

## Task M4-1：OrderRouteMetadata invariant tests

### 目标

保证 submit/cancel/replace/fill 全程保留 account/strategy/broker route。

### 实施步骤

```text
1. 创建两个 account、两个 strategy、一个 broker route。
2. Strategy A on Account A submit order。
3. Strategy B on Account B submit order。
4. cancel Account A order，确认不会 cancel Account B。
5. replace Account A order，确认 route metadata 不变。
6. fill Account A order，确认 only Account A updated。
```

### 验收条件

```text
1. SubmitOrder 必须有 account_id、strategy_id、OrderRouteMetadata。
2. CancelOrder 必须引用原始 route metadata。
3. ReplaceOrder 必须引用原始 route metadata。
4. route mismatch fail-fast。
5. 所有 order events 可按 correlation_id 追踪。
```

---

## Task M4-2：Account isolation suite

### 目标

证明多账户并行不会串账户状态。

### 测试

```text
test_fill_for_account_a_never_updates_account_b
test_cash_reservation_for_account_a_never_blocks_account_b
test_position_snapshot_partitioned_by_account
test_reconciliation_snapshot_partitioned_by_account
test_broker_route_missing_fails_fast
```

### 验收条件

```text
1. AccountActor state 只能由对应 account_id 的 fill/update 修改。
2. EventRouter 找不到 route 时抛 RouteNotFoundError。
3. 不存在默认 fallback account。
4. report manifest 包含 account partition topology。
```

---

## Task M4-3：Signal aggregation audit suite

### 目标

证明多策略信号合并 deterministic 且可审计。

### 实施步骤

```text
1. 对同一 account/instrument 创建两个 strategy contribution。
2. 覆盖 policy：SUM_TARGETS、PRIORITY_WINS、WEIGHTED_NET、REJECT_CONFLICT。
3. 每个 policy 输出 SignalAggregationDecision。
4. RuntimeSession._aggregate_signal_batches 或 SignalAggregatorActor 输出 AggregatedSignalBatch。
5. RiskDecision 引用 aggregation_decision_id。
6. OrderRouteMetadata 可反查 contributing_strategy_ids。
```

### 验收条件

```text
1. 冲突信号不会静默 net 掉，除非 policy 明确允许。
2. rejected_strategy_ids 写入 event。
3. contributing_strategy_ids 写入 order/risk/report event。
4. 相同输入 aggregation decision hash deterministic。
```

---

# Milestone 5：简洁性、去冗余、反过度设计

## Task M5-1：RuntimeSession 复杂度审计与收敛

### 目标

判断 `RuntimeSession` 是否保持 facade，还是已经成为 God Object；基于指标决定保留、抽取或删除 helper。

### 指标阈值建议

```text
public methods <= 12
private helpers <= 8
file length <= 350 lines
单个方法 <= 50 lines
cyclomatic complexity <= 10
```

### 实施步骤

```text
1. 使用 radon 或自定义 AST script 生成 RuntimeSession complexity report。
2. 将 RuntimeSession 方法分组：
   - lifecycle
   - broker lifecycle
   - market data dispatch
   - strategy/risk/order processing
   - safety/rollback
   - event writing
3. 如果某组有独立 coordinator 且 session 仍有细节逻辑，迁移到 coordinator。
4. 如果 coordinator 只是单方法 pass-through，则反向 inline。
5. 更新 tests，只测 public behavior，不测私有 helper。
```

### 验收条件

```text
1. RuntimeSession 只负责 orchestration，不承载 business decision。
2. RuntimeSession 私有 helper 数量低于阈值，或有明确 ADR 说明。
3. 每个 coordinator 至少满足以下之一：
   - 多调用点
   - 有状态
   - 有独立测试价值
   - 隔离外部边界
4. 复杂度 report 进入 CI artifact。
```

---

## Task M5-2：Thin coordinator 删除 / 合并审计

### 目标

删除没有实际隔离价值的 ceremony 类。

### 候选类

```text
RuntimeRecoveryCoordinator
RuntimeRollbackCoordinator
BrokerRuntimeStartupGate
RuntimeSafetyController
RuntimeBrokerLifecycleCoordinator
RuntimeMarketDataCoordinator
```

### 审计规则

保留条件至少满足一个：

```text
1. 有两个以上调用点。
2. 持有状态或策略对象。
3. 有独立 mock/fake 价值。
4. 隔离外部边界或安全门禁。
5. 方法复杂度高于 inline 后可读性阈值。
```

删除/合并条件：

```text
1. 只有一个方法。
2. 只有一个调用点。
3. 无状态。
4. 方法只是转发。
5. 没有独立测试。
```

### 验收条件

```text
1. 每个候选类都有 keep/merge/delete 决策。
2. keep 的类有 ADR 或注释说明保留原因。
3. delete 的类无生产 import 残留。
4. class count 减少或复杂度报告说明为何不减少。
```

---

## Task M5-3：Protocol / DTO / ValueObject 重复建模审计

### 目标

避免同一概念在 domain、runtime、API、reporting 中无必要重复。

### 审计对象

```text
RuntimeOrderResult
OrderManagerResult
ExecutionReport
IbkrExecutionReport
RuntimeEventWriteResult
WrittenRuntimeEvent
RuntimeManifest
LiveReportManifest
BacktestArtifacts
```

### 实施步骤

```text
1. 建立 concept map：概念 -> classes -> package -> direction。
2. 标记重复但必要的 boundary translation：API DTO、broker adapter payload、domain model。
3. 标记重复且不必要的 mirror class。
4. 对 mirror class 进行合并或删除。
5. 对保留的 DTO 添加 from_domain / to_payload，不允许散落字典转换。
```

### 验收条件

```text
1. 每个同名/近义类都有明确 boundary reason。
2. 不存在两个 production class 表达同一 runtime state 且可互相替代。
3. domain model 不依赖 API/reporting/broker payload。
4. 转换函数集中在 adapter/application/reporting boundary。
```

---

## Task M5-4：Report 命名收敛：`LiveReport*` 是否改成 broker/runtime 语义

### 目标

减少 paper/live 共享报告使用 `LiveReport*` 的语义不一致。

### 方案选择

```text
方案 A：保留 LiveReportWriter
  条件：明确 live 表示 broker-capable runtime，不表示 live capital。

方案 B：重命名为 BrokerRuntimeReportWriter / BrokerRuntimeReportManifest
  条件：希望 paper broker、live observation、live capital 都使用更准确命名。
```

### 推荐

采用方案 B，但可以分两步：

```text
1. 新增 BrokerRuntimeReportWriter，LiveReportWriter 作为 deprecated alias。
2. 一轮 release 后移除 LiveReportWriter。
```

### 验收条件

```text
1. paper report 不再显示 live-only 语义。
2. manifest 中明确 runtime_mode、account_environment、execution_environment。
3. 旧 LiveReportWriter import 被 RemovedImportNoNewUsageRule 阻断。
```

---

## Task M5-5：BacktestActorLoop 复杂度收敛

### 目标

确认 BacktestActorLoop 没有承担 replay assembly、catalog loading、report writing 之外的过多职责。

### 实施步骤

```text
1. 统计 BacktestActorLoop 文件长度、public methods、private helpers。
2. 确认 replay input assembly 由 BacktestEngine / dependencies / ReplayMarketDataSource 完成。
3. 确认 report writing 由 BacktestRuntimeEventSink / BacktestArtifactWriter 完成。
4. BacktestActorLoop 只保留：
   - poll/replay event
   - call MarketDataFlow
   - call StrategyExecutionPipeline
   - call TargetIntentProcessor
   - process actors
   - emit normalized events
5. 将 broker capability payload helper 下沉到 capability/reporting boundary。
```

### 验收条件

```text
1. BacktestRunnerCohesionRule / BacktestInputCohesionRule / BacktestEngineCohesionRule 全部通过。
2. BacktestActorLoop 不直接 load catalog，不直接 parse config，不直接 build dataset。
3. private helper 数量低于阈值，或有 ADR。
4. actor loop tests 只依赖 fakes，不依赖真实 file catalog。
```

---

# Milestone 6：Manifest、Durability、Operator Observability

## Task M6-1：统一 RuntimeManifest canonical schema

### 目标

backtest、paper、live 都输出同一 shared manifest 基础字段。

### 必填字段

```text
run_id
runtime_instance_id
runtime_mode
market_data_environment
execution_environment
account_environment
live_order_permission
config_hash
topology_hash
startup_checklist_hash
event_schema_version
artifact_schema_version
created_at
source_commit
operator_identity_hash  # live/paper broker required
```

### 验收条件

```text
1. BacktestReportWriter 和 BrokerRuntimeReportWriter 使用同一 RuntimeManifest base。
2. 缺字段 finalize 失败。
3. manifest hash deterministic。
4. manifest 可被 API/CLI 查询。
```

---

## Task M6-2：Event store / snapshot store durability drill

### 目标

证明 crash/restart 后可以从 snapshot + event store 恢复，并且 live 恢复前必须 broker reconciliation。

### 实施步骤

```text
1. 写入 N 个 runtime events。
2. 保存 AccountActor / OrderManagerActor / BrokerOrderMap snapshot。
3. 模拟进程 crash。
4. 加载 latest snapshot。
5. replay snapshot 后 events。
6. 执行 LiveReconciliation。
7. 只有 LiveRecoveryDecision=ALLOW 时恢复 order submission。
```

### 验收条件

```text
1. event sequence gap 会阻断 recovery。
2. snapshot schema version mismatch 会阻断 recovery 或执行 migration。
3. recovered account/order state 与 crash 前一致。
4. live recovery 未 reconciliation 不允许恢复下单。
```

---

## Task M6-3：Operator dashboard 最小状态面板

### 目标

为 paper/live observation/live capital 提供可排障的最小可视化状态。

### 必须展示

```text
runtime state
runtime mode
order permission state
broker connection state
market data permission state
stale subscriptions
open orders
positions
cash snapshot
kill switch state
last reconciliation result
unresolved broker callbacks
event sink path/hash/row count
latest manifest path/hash
```

### 验收条件

```text
1. Dashboard 数据来自 application service DTO，不直接暴露 actor internals。
2. 每个状态字段都有 timestamp。
3. unresolved callbacks / reconciliation drift / stale data 有显著告警。
4. WebSocket event DTO 与 RuntimeEvent schema 不混用。
```

---

## Task M6-4：Readiness smoke matrix

### 目标

在 CI 或 nightly 中固定运行一组 smoke，防止 backtest/paper/live 统一链路退化。

### Smoke matrix

```text
1. backtest_minimal_single_strategy_single_account
2. backtest_multi_strategy_one_account_conflict_reject
3. backtest_two_accounts_isolation
4. paper_simulated_market_data_to_fill
5. paper_broker_gateway_market_data_anchor  # 可 nightly / external only
6. paper_broker_submit_cancel_drill          # 可 nightly / external only
7. live_observation_market_data_no_orders
8. live_permission_off_blocks_order
9. broker_disconnect_blocks_order
10. reconnect_requires_reconciliation
```

### 验收条件

```text
1. CI 跑 local smoke。
2. Nightly 跑 external IBKR paper smoke。
3. 每个 smoke 输出 manifest 和 event artifact。
4. smoke failure 能直接定位到 run_id / correlation_id。
```

---

## 5. 并行推进建议

### Lane A：文档与 guardrail

```text
M0-1
M0-3
M0-4
M6-1
```

### Lane B：Backtest readiness

```text
M1-1
M1-2
M1-3
M5-5
```

### Lane C：Paper / live safety

```text
M1-4
M1-5
M2-1
M2-2
M2-5
```

### Lane D：IBKR robustness

```text
M3-1
M3-2
M3-3
M3-4
```

### Lane E：多策略 / 多账户

```text
M4-1
M4-2
M4-3
```

### Lane F：简洁性 / 去冗余

```text
M0-2
M5-1
M5-2
M5-3
M5-4
```

---

## 6. Live capital go / no-go checklist

只有全部满足后，才建议从 live observation 进入 live capital：

```text
[ ] RuntimeSession 是唯一 broker-capable runtime entrypoint。
[ ] LiveRuntime 已删除或仅 test-only deprecated wrapper。
[ ] qts.runtime.live 不再是生产 canonical import。
[ ] GuardrailSuite 是 CI hard gate。
[ ] Backtest deterministic / no-lookahead tests 通过。
[ ] Paper simulated CI smoke 通过。
[ ] IBKR paper lifecycle drill 通过。
[ ] Startup gate blocker matrix 通过。
[ ] MarketDataFreshnessRiskRule / MarketDataPermissionRiskRule 在 live order path 生效。
[ ] Broker disconnect/reconnect/reconciliation drill 通过。
[ ] IBKR callback idempotency / quarantine suite 通过。
[ ] Account isolation suite 通过。
[ ] Signal aggregation audit suite 通过。
[ ] Event store / snapshot recovery drill 通过。
[ ] Operator dashboard 可见 kill switch、stale data、reconciliation drift、unresolved callbacks。
[ ] operator signoff、risk signoff、engineering signoff 全部写入 manifest。
```

---

## 7. 最终判断

当前系统已经具备清晰的统一 runtime 形态：

```text
Backtest = replay market data + simulated execution + shared strategy/risk/order/account/reporting
Paper simulated = streaming/replay-like data + simulated execution + shared runtime
Paper broker = streaming IBKR paper data + IBKR paper execution + shared runtime
Live observation = streaming live data + no order submission + shared runtime
Live capital = streaming live data + broker execution + additional hard gates
```

当前建议状态：

```text
Backtest：可以使用，但必须补 deterministic/no-lookahead/manifest 验收。
Paper simulated：可以进入 CI 和日常验证。
IBKR paper：可以受控运行 drill 和小规模 paper 验证。
Live observation：可以运行。
Live capital：暂不建议开启，直到 M0、M2、M3、M4、M6 的阻断项完成。
```

从“简洁性/不过度设计”角度看，当前架构大方向合理，不属于明显过度设计，因为交易系统 live safety、reconciliation、broker callback、event sourcing、multi-account isolation 本身就需要显式边界。但系统已经进入较高复杂度区间，必须开始用复杂度预算、guardrail、thin coordinator audit 和 deprecated import 清理来控制演进速度。最值得立即做的是：

```text
1. 删除或隔离 LiveRuntime。
2. 迁移 qts/runtime/live.py 的 broker startup 内容。
3. 修复 panorama stale text。
4. 让 GuardrailSuite 进入 CI hard gate。
5. 补齐 Backtest/Paper/Live readiness smoke matrix。
```
