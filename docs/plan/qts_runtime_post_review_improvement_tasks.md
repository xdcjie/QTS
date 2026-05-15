# QTS 统一运行时二次 Review 后改进计划 / Task Backlog

> 生成日期：2026-05-14
> 适用范围：`backend/src/qts` 统一 backtest / paper / live runtime。
> 目标：将上一轮 review 中发现的剩余问题拆成可并行推进、验收条件明确的工程 task。
> 原则：**建议改类名的项必须纳入改名计划**；task 尽量独立，只有必须存在的依赖才显式标注。

---

## 0. 当前状态摘要

当前系统已经具备统一职责链：

```text
Strategy SDK
 -> StrategyContext
 -> TargetIntent
 -> RiskEngine
 -> OrderManagerActor
 -> ExecutionActor
 -> AccountActor
 -> RuntimeEventSink / ReportWriter
```

Backtest 使用 `ReplayMarketDataSource + SimulatedExecutionAdapter`，paper/live 使用 `StreamingMarketDataSource + BrokerExecutionAdapter / IbkrOrderExecutionAdapter`。方向是正确的。

本轮剩余主要问题不是“统一流程是否成立”，而是：

```text
1. 命名和实际语义仍有 live/paper/backtest 混用。
2. guardrail 和当前 class inventory 之间仍有冲突，例如 Fake* / placeholder / live-beta wording。
3. LiveRuntimeSession、IbkrTwsOrderExecutionTransport 已过重，需要拆分。
4. market-data permission / stale 状态需要进入 RiskEngine gate，而不是只进入观测事件。
5. IBKR callback 幂等、乱序、quarantine、reconnect 后恢复仍需强测。
6. 多账户、多策略、signal aggregation 已有类，但还需运行时隔离和审计测试。
7. EventStore / Snapshot / Reporting contract 需要从“存在”推进到“生产级 contract”。
```

---

## 1. 改名总表

以下改名作为本计划的强制目标。允许短期保留 backward-compatible import shim，但 production inventory 和新代码必须使用新名。

| 当前名称 | 新名称 | 新位置 | 处理方式 | 理由 |
|---|---|---|---|---|
| `LiveRuntimeSession` | `RuntimeSession` | `qts/runtime/session.py` | 改名 + 保留 deprecated alias 1 个 release | session 实际承载 paper/live broker-capable runtime，不应暗示 live capital。 |
| `LiveRuntimeSessionResult` | `RuntimeSessionResult` | `qts/runtime/session.py` | 改名 | 结果对象模式无关。 |
| `LiveRuntimeDependencies` | `RuntimeSessionDependencies` | `qts/runtime/dependencies.py` | 改名 | 依赖集合属于 runtime session，不属于 live 专属。 |
| `LiveRuntimeState` | `RuntimeSessionState` | `qts/runtime/state.py` | 改名 | 状态机应跨 paper/live/observation 共用。 |
| `LiveRuntimeStateMachine` | `RuntimeStateMachine` | `qts/runtime/state.py` | 改名 | 去掉 live-only wording。 |
| `LivePermissionMode` | `LiveOrderPermission` | `qts/runtime/permissions.py` | 改名 | 避免和 `RuntimeMode` 混用；该类表达的是 live order permission，不是 runtime mode。 |
| `LiveKillSwitchEvidence` | `RuntimeKillSwitchEvidence` | `qts/runtime/safety.py` | 改名 | kill switch 是 runtime safety 事件，不是 live 专属。 |
| `LiveReconciliation` | `BrokerRuntimeReconciliation` | `qts/runtime/reconciliation.py` 或 `qts/reconciliation/broker_runtime.py` | 改名 | 它实际 gate paper/live broker runtime，不是只 gate live。 |
| `LiveReconciliationResult` | `BrokerRuntimeReconciliationResult` | 同上 | 改名 | 与上保持一致。 |
| `LiveStartupChecklist` | `BrokerRuntimeStartupChecklist` | `qts/runtime/startup_gate.py` | 改名 | paper broker 和 live capital 都需要 broker startup gate。 |
| `LiveStartupCheck` | `BrokerRuntimeStartupCheck` | 同上 | 改名 | 与 checklist 一致。 |
| `LiveStartupDecision` | `BrokerRuntimeStartupDecision` | 同上 | 改名 | 与 checklist 一致。 |
| `LiveStartupDecisionStatus` | `BrokerRuntimeStartupDecisionStatus` | 同上 | 改名 | 与 checklist 一致。 |
| `LiveRuntime` | `RuntimeFacade` 或删除 | `qts/runtime/facade.py` | 若仅测试使用则移到 `qts/testing`；若 public API 仍需则改名 | 当前名称和 beta/fake wording 容易误导。 |
| `_LiveRuntimeTopologyBuilder` | 删除或 `BrokerRuntimeTopologyResolver` | `qts/runtime/topology.py` | 合并到 public `RuntimeTopologyBuilder` | 避免第二套 topology builder。 |
| `_ResolvedLiveRuntimeTopology` | `ResolvedRuntimeTopology` | `qts/runtime/topology.py` | 改名/合并 | topology 不应 live-only。 |
| `LiveFeedAdapter` | `StreamingFeedAdapter` | `qts/data/interfaces.py` | 改名/迁移 | feed 是 streaming 边界，不等于 live capital。 |
| `MarketDataAdapter` in `qts.data.live.adapter` | `MarketDataAdapter` | `qts/data/interfaces.py` | 迁移，不一定改名 | 共享 contract 不能放在 `data.live` 包。 |
| `FeedCapabilities` | `MarketDataFeedCapabilities` | `qts/data/capabilities.py` | 改名/迁移 | 名称表达 market-data feed，而不是 generic feed。 |
| `FeedSubscription` | `MarketDataSubscription` | `qts/data/subscriptions.py` | 改名/迁移 | subscription 是 data source contract。 |
| `LiveFeedEvent` | `MarketDataSourceEvent` | `qts/data/events.py` | 改名/迁移 | replay/streaming 都可产生 source event。 |
| `LiveFeedFailure` | `MarketDataSourceFailure` | `qts/data/events.py` | 改名/迁移 | replay/streaming failure 使用同一语义。 |
| `FakeLiveFeedAdapter` | `FakeStreamingMarketDataAdapter` | `qts/testing/fakes/market_data.py` | 改名/迁移 | fake 只能在 testing 中出现。 |
| `FakeMarketDataAdapter` | `FakeMarketDataAdapter` | `qts/testing/fakes/market_data.py` | 迁移 | 保留名称但移出 production data package。 |
| `FakeBrokerAdapter` | `FakeBrokerAdapter` 或 `SimulatedBrokerAdapter` | `qts/testing/fakes/broker.py` 或 `qts/simulation/broker.py` | 按用途迁移 | 测试 fake 与生产 simulation 要分开。 |
| `IbkrTwsOrderExecutionTransport` | 拆成 5 个类 | `qts/execution/transports/` | 拆分 | 当前类职责过重。 |
| `IbkrTwsMarketDataTransport` | 保持名称但移动 | `qts/data/transports/` | 迁移 | Transport 不应放在 adapters 目录。 |
| `IbAsyncMarketDataTransport` | 保持名称但移动 | `qts/data/transports/` | 迁移 | 同上。 |
| `IbkrTwsOrderExecutionTransport` | 保持 facade 名称，内部委托新类 | `qts/execution/transports/` | 迁移 + 拆分 | 兼容现有调用，同时拆职责。 |

---

## 2. 并行推进建议

| Lane | 可并行 task | 说明 |
|---|---|---|
| A. 命名与边界 | T01, T02, T03, T04, T05, T06, T22, T25 | 多数是 import / docstring / package 清理，可独立推进。 |
| B. Runtime safety | T07, T12, T13, T18, T21, T24 | 以 live capital block 为核心，可与 IBKR 拆分并行。 |
| C. IBKR 稳定性 | T08, T09, T10, T11 | 可以独立于 runtime 改名推进，但最终需接入 T12/T13。 |
| D. Data / replay / simulation | T14, T15, T16 | 与 IBKR 低耦合，可由数据/回测方向并行推进。 |
| E. 多账户/多策略 | T17, T19, T20 | 依赖 topology 名称稳定，但可先写 contract tests。 |
| F. Observability / reporting / recovery | T18, T21, T23 | 可独立补 contract 和测试。 |
| G. CI guardrail | T00, T01, T26 | 先建立 baseline，再逐步收紧。 |

---

# Task Backlog

---

## T00 — 建立改造基线与任务保护网

**优先级**：P0
**可并行性**：可立即开始
**依赖**：无

### 目标

在改名、迁移、拆分前建立可回归基线，避免大规模重构后无法确认行为是否改变。

### 范围

```text
1. 生成当前 class inventory snapshot。
2. 生成当前 import graph snapshot。
3. 生成当前关键链路 smoke test baseline。
4. 明确哪些测试是 regression gate。
```

### 实施步骤

1. 新增 `tools/architecture/export_inventory.py`，输出：
   - class name
   - module path
   - public/private
   - docstring first line
   - direct imports
   - method count
2. 新增 `tools/architecture/export_import_graph.py`，输出 module dependency graph。
3. 在 `tests/architecture/snapshots/` 保存 baseline：
   - `class_inventory_before_post_review.json`
   - `import_graph_before_post_review.json`
4. 新增 smoke tests：
   - `test_backtest_core_chain_smoke`
   - `test_paper_runtime_chain_smoke_with_fake_boundary`
   - `test_runtime_event_sink_smoke`
5. 在 CI 中把 smoke tests 作为每个 PR 必跑项。

### 验收条件

```text
[ ] 可以通过一条命令生成 class inventory。
[ ] 可以通过一条命令生成 import graph。
[ ] 当前 backtest smoke test 通过。
[ ] 当前 paper/runtime fake-boundary smoke test 通过。
[ ] 后续 task 的 PR 都能和 baseline 做 diff。
```

---

## T01 — 启用 guardrail 并清理 Fake / placeholder / beta / later wording

**优先级**：P0
**可并行性**：可立即开始
**依赖**：T00 建议先完成，但不是硬依赖

### 目标

消除当前 guardrail 与实际 inventory 的冲突。生产目录中不再出现 fake class、placeholder docstring、beta wording、`intended later` wording。

### 范围

重点清理：

```text
FakeLiveFeedAdapter
FakeMarketDataAdapter
FakeBrokerAdapter
LiveRuntime docstring 中的 fake / beta wording
ReportWriter placeholder wording
RuntimeArtifactWriter placeholder wording
CashBook intended later wording
PositionBook intended later wording
```

### 实施步骤

1. 将测试 fake 迁移到：

```text
qts/testing/fakes/market_data.py
qts/testing/fakes/broker.py
```

2. 如果某个 fake 实际用于本地模拟 paper，则改为 production simulation 名称：

```text
FakeBrokerAdapter -> SimulatedBrokerAdapter
FakeLiveFeedAdapter -> SimulatedStreamingMarketDataAdapter
```

3. 修改生产 docstring：

```text
ReportWriter
  Boundary contract for generating auditable runtime reports.

RuntimeArtifactWriter
  Boundary contract for persisting runtime artifacts.

CashBook
  AccountActor-owned mutable cash balance book.

PositionBook
  AccountActor-owned mutable position book.
```

4. 在 `qts/quality/guardrails.py` 中启用或新增：
   - `ProductionNoFakeClassRule`
   - `ProductionPlaceholderDocstringRule`
   - `ProductionNoBetaWordingRule`
   - `ProductionNoIntendedLaterWordingRule`
5. CI 中执行：

```bash
pytest tests/quality/test_guardrails.py
```

### 验收条件

```text
[ ] `grep -R "class Fake" backend/src/qts` 无结果，除非路径在 `qts/testing`。
[ ] `grep -R "placeholder" backend/src/qts` 无 production docstring 结果。
[ ] `grep -R "beta" backend/src/qts` 无 production docstring 结果。
[ ] `grep -R "intended to be owned" backend/src/qts` 无结果。
[ ] guardrail 在 CI 中必跑且违规会 fail。
[ ] 所有 moved fake 的 import 已迁移或有 deprecated shim。
```

---

## T02 — Runtime session 类统一改名

**优先级**：P0
**可并行性**：可与 T03/T04 并行
**依赖**：无

### 目标

将 broker-capable runtime session 从 `LiveRuntimeSession` 改为模式无关的 `RuntimeSession`，避免 paper/live/observation 语义混淆。

### 改名列表

```text
LiveRuntimeSession         -> RuntimeSession
LiveRuntimeSessionResult   -> RuntimeSessionResult
LiveRuntimeDependencies    -> RuntimeSessionDependencies
LiveRuntimeState           -> RuntimeSessionState
LiveRuntimeStateMachine    -> RuntimeStateMachine
LiveKillSwitchEvidence     -> RuntimeKillSwitchEvidence
```

### 新目录建议

```text
qts/runtime/session.py
qts/runtime/dependencies.py
qts/runtime/state.py
qts/runtime/safety.py
```

### 实施步骤

1. 新增新模块并迁移类定义。
2. 原模块保留兼容 alias：

```python
# qts/runtime/live_runtime_session.py
from qts.runtime.session import RuntimeSession as LiveRuntimeSession
```

3. alias 上加 deprecation warning，期限 1 个 release。
4. 更新所有 production import，测试 import，文档 import。
5. 更新 runtime event payload 字段：
   - `session_type` 不再写 live-only。
   - `runtime_mode` 必须来自 `RuntimeMode`。
6. 更新 class inventory generator，不再把 alias 当 production canonical class。

### 验收条件

```text
[ ] production code 不再 import `qts.runtime.live_runtime_session.LiveRuntimeSession`。
[ ] class inventory canonical name 显示 `RuntimeSession`。
[ ] 旧 import shim 可用，但测试中只有 compatibility test 使用。
[ ] `RuntimeSession` docstring 明确：broker-capable runtime session，不代表 live capital enabled。
[ ] backtest smoke、paper smoke、runtime command smoke 全部通过。
```

---

## T03 — 拆分 `RuntimeMode` 与 live order permission

**优先级**：P0
**可并行性**：可与 T02/T04 并行
**依赖**：无

### 目标

消除 `RuntimeMode` 与 `LivePermissionMode` 两套“模式”语义并存的问题。

### 改名

```text
LivePermissionMode -> LiveOrderPermission
```

### 推荐枚举

```python
class RuntimeMode(Enum):
    BACKTEST = "backtest"
    PAPER_BROKER = "paper_broker"
    PAPER_SIMULATED = "paper_simulated"
    LIVE_OBSERVATION = "live_observation"
    LIVE = "live"

class LiveOrderPermission(Enum):
    OBSERVATION_ONLY = "observation_only"
    PAPER_ORDERS_ALLOWED = "paper_orders_allowed"
    LIVE_ORDERS_ALLOWED = "live_orders_allowed"
```

### 实施步骤

1. 新增 `qts/runtime/permissions.py`。
2. `RuntimeMode` 只表达 runtime 类型，不表达是否允许 live 下单。
3. `LiveOrderPermission` 只表达 order enablement。
4. `BrokerRuntimeStartupDecision` 输出必须包含：

```text
runtime_mode
market_data_environment
execution_environment
account_environment
live_order_permission
```

5. order submission gate 使用 `LiveOrderPermission`，而不是直接判断 `RuntimeMode`。
6. 更新配置校验：
   - `RuntimeMode.LIVE` + `LiveOrderPermission.LIVE_ORDERS_ALLOWED` 才能真实资金下单。
   - `RuntimeMode.LIVE_OBSERVATION` 必须强制 `OBSERVATION_ONLY`。
   - `RuntimeMode.PAPER_BROKER` 只能 `PAPER_ORDERS_ALLOWED` 或 `OBSERVATION_ONLY`。

### 验收条件

```text
[ ] `LivePermissionMode` 不再是 canonical class。
[ ] live order path 不再直接用 RuntimeMode 判断是否可下单。
[ ] `LIVE_OBSERVATION` 模式下所有 submit order 被拒绝，并记录 reason_code。
[ ] `PAPER_BROKER` 模式不能获得 `LIVE_ORDERS_ALLOWED`。
[ ] `LIVE` 模式没有显式 `LIVE_ORDERS_ALLOWED` 时不能下单。
```

---

## T04 — 明确 paper broker 与 paper simulated 配置语义

**优先级**：P0
**可并行性**：可与 T02/T03 并行
**依赖**：T03 最好先完成枚举，但可并行开发

### 目标

拆清 `paper_broker` 与 `paper_simulated`。不允许 `PaperRuntimeConfig` 同时表达“IBKR paper broker”和“本地模拟 broker”。

### 推荐配置类

```text
PaperBrokerRuntimeConfig
PaperSimulatedRuntimeConfig
```

或统一用：

```text
TradingRuntimeConfig(runtime_mode=RuntimeMode.PAPER_BROKER)
TradingRuntimeConfig(runtime_mode=RuntimeMode.PAPER_SIMULATED)
```

但无论哪种方式，docstring 必须明确区分。

### 实施步骤

1. 搜索 `PaperRuntimeConfig` 所有用法。
2. 如果它连接 IBKR paper account：改为 `PaperBrokerRuntimeConfig`。
3. 如果它不需要真实 broker credentials：改为 `PaperSimulatedRuntimeConfig`。
4. 修改配置校验：

```text
PAPER_BROKER:
  - broker_account_kind == paper
  - account code 必须匹配 DU...
  - 默认 port 4002
  - 必须构造 broker execution transport

PAPER_SIMULATED:
  - broker_account_kind == simulated
  - 禁止构造 IBKR order transport
  - 可以使用 replay 或 streaming market data
```

5. 更新 manifest：
   - `runtime_mode`
   - `market_data_environment`
   - `execution_environment`
   - `account_environment`
   - `broker_account_kind`

### 验收条件

```text
[ ] production docstring 不再出现 “paper without real broker credentials” 这种模糊描述。
[ ] PAPER_BROKER 使用 DU account + 4002 默认端口。
[ ] PAPER_SIMULATED 永远不会构造 IBKR order transport。
[ ] manifest 能一眼区分 paper broker 和 paper simulated。
[ ] 至少有 2 个配置样例：paper_broker.yaml、paper_simulated.yaml。
```

---

## T05 — 将共享 market-data contract 移出 `qts.data.live`

**优先级**：P0
**可并行性**：可与 T06/T07 并行
**依赖**：无

### 目标

`qts.data.live` 只保留 streaming/live-specific provider 内容；共享接口、subscription、event 必须迁出。

### 改名与迁移

```text
qts.data.live.adapter.MarketDataAdapter -> qts.data.interfaces.MarketDataAdapter
qts.data.live.adapter.LiveFeedAdapter    -> qts.data.interfaces.StreamingFeedAdapter
qts.data.live.capabilities.FeedCapabilities -> qts.data.capabilities.MarketDataFeedCapabilities
qts.data.live.events.FeedSubscription    -> qts.data.subscriptions.MarketDataSubscription
qts.data.live.events.LiveFeedEvent       -> qts.data.events.MarketDataSourceEvent
qts.data.live.events.LiveFeedFailure     -> qts.data.events.MarketDataSourceFailure
qts.data.live.events.MarketDataSubscribed -> qts.data.events.MarketDataSubscribed
```

### 新目录

```text
qts/data/interfaces.py
qts/data/events.py
qts/data/subscriptions.py
qts/data/capabilities.py
qts/data/live/reconnect.py
qts/data/live/ibkr_specific.py   # 如确实有 provider-specific 内容
```

### 实施步骤

1. 新增共享 modules。
2. 迁移类定义和 import。
3. 原 `qts.data.live.*` 保留 deprecation shim 1 个 release。
4. 更新 `StreamingMarketDataSource` 和 `ReplayMarketDataSource`，统一引用新 contract。
5. 更新 guardrail：
   - shared market-data contract 不能位于 `qts.data.live`。
   - replay/source event 不能 import `qts.data.live.events`。

### 验收条件

```text
[ ] `MarketDataAdapter` canonical path 是 `qts.data.interfaces`。
[ ] `ReplayMarketDataSource` 不依赖 `qts.data.live`。
[ ] `StreamingMarketDataSource` 可通过新 shared contract 运行。
[ ] `qts.data.live` 中不再有 shared contract class。
[ ] architecture test 禁止 replay 依赖 live package。
```

---

## T06 — Fake 与 simulated 边界重新归位

**优先级**：P0
**可并行性**：可与 T05 并行
**依赖**：无

### 目标

测试 fake 与生产 simulation 分离。fake 只能用于测试，simulation 才能用于 paper simulated / backtest。

### 实施步骤

1. 新建：

```text
qts/testing/fakes/market_data.py
qts/testing/fakes/broker.py
qts/simulation/market_data.py
qts/simulation/broker.py
```

2. 按用途迁移：

```text
测试替身：FakeStreamingMarketDataAdapter, FakeMarketDataAdapter, FakeBrokerAdapter
生产模拟：SimulatedStreamingMarketDataAdapter, SimulatedBrokerAdapter
```

3. `PAPER_SIMULATED` 只能使用 simulation class，不能使用 testing fake。
4. 单元测试可以使用 testing fake，但必须从 `qts.testing.fakes` import。
5. guardrail：
   - production path 禁止 `Fake*`。
   - production config 禁止引用 `qts.testing`。

### 验收条件

```text
[ ] `backend/src/qts/data/live/fake_adapter.py` 删除或仅作为 deprecated test shim。
[ ] production package 不再含 `Fake*` class。
[ ] tests 中 fake import 全部来自 `qts.testing.fakes`。
[ ] paper_simulated runtime 使用 `Simulated*`，不是 `Fake*`。
[ ] CI guardrail 覆盖 production no-fake rule。
```

---

## T07 — Transport 目录迁移：data side

**优先级**：P1
**可并行性**：可与 T08 并行
**依赖**：T05 建议先完成接口迁移，但不是硬依赖

### 目标

将 market-data transport 从 adapters 目录迁移到 transports 目录，符合词典：

```text
Adapter = provider shape -> internal domain model
Transport = SDK / socket / callback / network lifecycle
```

### 迁移

```text
qts/data/adapters/ibkr_transport.py
  -> qts/data/transports/ibkr_tws_market_data_transport.py

qts/data/adapters/ib_async_transport.py
  -> qts/data/transports/ib_async_market_data_transport.py
```

### 实施步骤

1. 新建 `qts/data/transports/__init__.py`。
2. 移动 transport class。
3. `IbkrMarketDataAdapter` 保留在 `qts/data/adapters/ibkr_market_data_adapter.py`。
4. 原路径保留 deprecation shim。
5. import graph guardrail：`*Transport` class 不允许 canonical path 在 `adapters` 目录。

### 验收条件

```text
[x] `IbkrTwsMarketDataTransport` canonical path 是 `qts.data.transports`。
[x] `IbAsyncMarketDataTransport` canonical path 是 `qts.data.transports`。
[x] `IbkrMarketDataAdapter` 不拥有 network reconnect lifecycle。
[x] source -> adapter -> transport 依赖方向清晰。
[x] 旧 import 有 compatibility test，但新代码不再使用旧路径。
```

---

## T08 — Transport 目录迁移：execution side

**优先级**：P1
**可并行性**：可与 T07/T09 并行
**依赖**：无

### 目标

将 order execution transport 从 adapters 目录迁移到 transports 目录。

### 迁移

```text
qts/execution/adapters/ibkr_transport.py
  -> qts/execution/transports/ibkr_tws_order_execution_transport.py

qts/execution/adapters/ibkr_async_transport.py
  -> qts/execution/transports/ib_async_order_execution_transport.py
```

### 实施步骤

1. 新建 `qts/execution/transports/`。
2. 移动 `IbkrOrderExecutionTransport`、`IbkrTwsOrderExecutionTransport`、`IbkrConnectionEvent` 等 transport/callback payload。
3. 保留 `IbkrOrderExecutionAdapter` 在 `qts/execution/adapters/ibkr_order_execution_adapter.py`。
4. `BrokerExecutionAdapter` 只依赖 order execution adapter interface，不直接依赖 provider transport。
5. guardrail：`qts.execution.adapters` 不允许定义 `*Transport` canonical class。

### 验收条件

```text
[x] order transport canonical path 是 `qts.execution.transports`。
[x] adapter 只负责 provider shape mapping，不负责 socket lifecycle。
[x] existing IBKR submit/cancel paper tests 通过。
[x] old import path 仅作为 deprecated shim。
[x] architecture import graph 通过。
```

---

## T09 — 拆分 `RuntimeSession`，避免 God Object

**优先级**：P1
**可并行性**：可与 T10/T12 并行
**依赖**：T02 完成后实施最顺畅

### 目标

将 `RuntimeSession` 降级为 thin orchestrator，拆出 market data、broker lifecycle、safety、rollback、recovery 等 coordinator。

### 新类

```text
RuntimeSession
RuntimeMarketDataCoordinator
RuntimeBrokerLifecycleCoordinator
RuntimeSafetyController
RuntimeRollbackCoordinator
RuntimeRecoveryCoordinator
```

### 责任拆分

```text
RuntimeSession:
  start / stop / pause / resume
  dependency wiring
  expose state and topology

RuntimeMarketDataCoordinator:
  on_market_data_source_event
  on_market_data
  route to MarketDataFlow / StrategyExecutionPipeline

RuntimeBrokerLifecycleCoordinator:
  on_broker_disconnect
  on_broker_reconnect
  broker degraded / recovered event

RuntimeSafetyController:
  activate_kill_switch
  startup decision
  order enablement gate

RuntimeRollbackCoordinator:
  rollback command
  rollback evidence
  preserve state and stop new orders

RuntimeRecoveryCoordinator:
  snapshot load
  event replay
  broker reconciliation
  recovery decision
```

### 实施步骤

1. 先抽 `RuntimeMarketDataCoordinator`，因为它最容易通过 paper market-data smoke 验证。
2. 再抽 `RuntimeSafetyController`，连接 kill switch 与 startup gate。
3. 再抽 `RuntimeBrokerLifecycleCoordinator`。
4. 最后抽 rollback/recovery。
5. `RuntimeSession` 保留 public API，但方法内部委托 coordinator。

### 验收条件

```text
[x] `RuntimeSession` 不直接实现 `on_market_data` 的全部业务逻辑，只委托 coordinator。
[x] `RuntimeSession` 不直接实现 IBKR reconnect 细节。
[x] `RuntimeSession` 单类方法数明显下降，目标不超过 15 个 public methods。
[x] market-data coordinator 有独立 unit tests。
[x] safety controller 有独立 unit tests。
[x] 原 paper/live 链路 smoke test 通过。
```

---

## T10 — 拆分 `IbkrTwsOrderExecutionTransport`

**优先级**：P1
**可并行性**：可与 T09/T11 并行
**依赖**：T08 建议先完成目录迁移

### 目标

将过重的 IBKR order transport 拆成 connection、order client、reconciliation client、callback dispatcher、event emitter，便于测试 callback 乱序、重复、reconnect。

### 新类

```text
IbkrTwsConnection
IbkrTwsOrderClient
IbkrTwsReconciliationClient
IbkrTwsCallbackDispatcher
IbkrTwsExecutionEventEmitter
IbkrTwsOrderExecutionTransport  # 保留为 facade
```

### 责任拆分

```text
IbkrTwsConnection:
  connect / disconnect
  managed_accounts
  nextValidId / reqIds
  connection state

IbkrTwsOrderClient:
  submit_order
  submit_order_with_broker_id
  cancel_order

IbkrTwsReconciliationClient:
  request_startup_reconciliation
  request_open_orders
  request_positions
  request_account_summary
  request_executions

IbkrTwsCallbackDispatcher:
  handle_order_status
  handle_open_order
  handle_position
  handle_account_summary
  handle_execution
  handle_commission_report
  handle_error
  handle_disconnect
  handle_reconnect

IbkrTwsExecutionEventEmitter:
  emit_order_status
  emit_open_order
  emit_execution
  emit_commission
  emit_error
  emit_disconnect
  emit_reconnect
```

### 实施步骤

1. 将原 transport 的 callback handling 方法搬到 dispatcher。
2. 将 emit 方法搬到 emitter。
3. 将 `request_startup_reconciliation` 搬到 reconciliation client。
4. 将 `submit_order/cancel_order` 搬到 order client。
5. facade `IbkrTwsOrderExecutionTransport` 保持旧 public API，内部组合这些类。

### 验收条件

```text
[x] `IbkrTwsOrderExecutionTransport` 不直接包含所有 handle_* 和 emit_* 业务。
[x] callback dispatcher 可独立注入 fake sink 做单测。
[x] reconciliation client 可独立单测。
[x] order client 可独立单测 submit/cancel payload。
[x] 原 IBKR paper submit/cancel/tiny-fill 测试通过。
```

---

## T11 — IBKR callback 幂等、乱序与 quarantine 测试

**优先级**：P0
**可并行性**：可与 T10 并行先写测试，T10 后接实现
**依赖**：无

### 目标

确保 IBKR callback 重复、乱序、延迟、缺失 account/permId 时不会重复入账、错误归属或污染其他账户。

### 范围

覆盖：

```text
orderStatus duplicate
openOrder before local submitted record
execution before openOrder
partial fill duplicate
commission report after fill
commission report duplicate
permId missing
wrong account callback
reconnect after pending order
cancel after reconnect
```

### 实施步骤

1. 扩展 `FillIdempotencyStore` key：

```text
broker_account
instrument_id
broker_exec_id
perm_id optional
ibkr_order_id optional
```

2. 新增 `BrokerCallbackQuarantine`：
   - unknown order
   - wrong account
   - missing critical id
   - execution before order mapping
3. `BrokerOrderMap` 支持 pending/unresolved callback attach。
4. 所有 quarantine event 写入 `RuntimeEventSink`。
5. reconnect 后执行：
   - request open orders
   - request positions
   - request executions since last checkpoint
   - resolve quarantine

### 验收条件

```text
[x] duplicate orderStatus 不推进两次状态。
[x] duplicate execution 不重复 apply fill。
[x] commission 晚到只更新费用，不二次 apply fill。
[x] execution before openOrder 会进入 quarantine 并在 mapping 到达后 resolve。
[x] wrong account callback 不会更新本地账户。
[x] reconnect 前 pending order 在 reconciliation 通过前不能继续新单。
[x] 所有 quarantine / resolve 都有 callback audit event；runtime sink 编排在 T13/T24 继续收口。
```

---

## T12 — Market-data permission / stale 状态接入 RiskEngine gate

**优先级**：P0
**可并行性**：可与 T13/T14 并行
**依赖**：无

### 目标

market data 的 `LIVE / DELAYED / FROZEN / STALE / UNAVAILABLE` 状态必须影响下单权限，不能只作为观测事件。

### 新规则

```text
MarketDataPermissionRiskRule
MarketDataFreshnessRiskRule
```

### 实施步骤

1. `StreamingMarketDataSource` 输出 permission state snapshot：

```text
subscription_id
instrument_id
market_data_type
permission_state
last_event_ts
stale_after
source_degraded
```

2. `StrategyExecutionPipeline` 或 `TargetIntentProcessor` 将产生 intent 时的数据 freshness context 传入 risk。
3. `RiskEngine` 增加 market-data context 参数。
4. 新增风险拒绝 reason code：

```text
MARKET_DATA_DELAYED_FOR_LIVE_ORDER
MARKET_DATA_FROZEN_FOR_LIVE_ORDER
MARKET_DATA_STALE
MARKET_DATA_UNAVAILABLE
MARKET_DATA_PERMISSION_UNKNOWN
```

5. live order path 默认规则：

```text
LIVE capital:
  only LIVE market data can trigger order

PAPER_BROKER:
  delayed data allowed only if config explicitly allows

PAPER_SIMULATED:
  delayed/replay allowed but manifest must record
```

### 验收条件

```text
[x] LIVE 模式下 delayed data 触发的 intent 被 risk reject。
[x] LIVE 模式下 stale data 触发的 intent 被 risk reject。
[x] frozen data 不允许触发 live order。
[x] RiskDecision payload 包含 market-data permission/freshness evidence。
[x] RuntimeEventSink 记录 risk rejection reason code。
[ ] paper_simulated 如果使用 delayed/replay，manifest 必须写明。
```

---

## T13 — Broker runtime startup gate 强制化

**优先级**：P0
**可并行性**：可与 T12/T18/T24 并行
**依赖**：T03/T04 完成后语义更清晰

### 目标

`BrokerRuntimeStartupChecklist` 不只是输出 manifest，而是 live/paper broker order path 的强制 gate。

### 改名

```text
LiveStartupChecklist       -> BrokerRuntimeStartupChecklist
LiveStartupCheck           -> BrokerRuntimeStartupCheck
LiveStartupDecision        -> BrokerRuntimeStartupDecision
LiveStartupDecisionStatus  -> BrokerRuntimeStartupDecisionStatus
```

### 必须检查项

```text
runtime_mode_check
account_code_check
port_check
client_id_check
api_order_enablement_check
api_read_only_check
market_data_permission_check
broker_clock_drift_check
open_order_reconciliation_check
position_reconciliation_check
cash_reconciliation_check
risk_config_check
kill_switch_initial_state_check
event_sink_writable_check
snapshot_store_writable_check
operator_signoff_check
```

### 实施步骤

1. checklist 每项输出：

```text
check_name
status
severity
evidence
remediation
```

2. decision 输出：

```text
ALLOW_OBSERVATION
ALLOW_PAPER_ORDERS
ALLOW_LIVE_ORDERS
BLOCK
```

3. `RuntimeSafetyController` 在每次 submit order 前检查当前 decision。
4. reconnect 后 decision 自动降级为 `ALLOW_OBSERVATION` 或 `BLOCK`，直到 reconciliation 重新通过。
5. manifest 写入 checklist hash 和 decision evidence。

### 验收条件

```text
[x] 没有 operator_signoff 时，LIVE 不能下单。
[x] reconciliation drift 存在时，LIVE/PAPER_BROKER 不能下单。
[x] event sink 不可写时，LIVE/PAPER_BROKER 不能下单。
[x] snapshot store 不可写时，LIVE/PAPER_BROKER 不能下单。
[x] reconnect 后未重新 reconcile 前不能恢复 order submission。
[x] checklist 每个 block 都有 evidence 和 remediation。
```

---

## T14 — Backtest replay 防未来函数 contract tests

**优先级**：P1
**可并行性**：可独立推进
**依赖**：无

### 目标

确保 replay source 是 broker-like subscription-driven source，而不是直接读全量历史数据喂策略；策略不能读取未来 bar close。

### 测试清单

```text
test_bar_close_visible_only_at_bar_end
test_multi_instrument_same_timestamp_deterministic_order
test_subscription_mid_run_only_receives_after_subscribe
test_unsubscribe_stops_delivery
test_replay_gap_emits_anomaly_and_does_not_silent_fill
test_no_future_bar_available_to_strategy_context
test_replay_duplicate_dropped_with_event
test_replay_out_of_order_rejected_with_event
```

### 实施步骤

1. 明确 `ReplaySequencedEvent.visible_at` 语义。
2. bar event 只在 `bar.end` 或之后 visible。
3. 多 instrument 同 timestamp 使用 deterministic tie-breaker：

```text
1. ts_event
2. visible_at
3. event_type priority: quote -> tick -> bar 或项目固定规则
4. instrument_id
5. sequence_no
```

4. subscription book 只发送 active subscriptions。
5. replay gap/anomaly 必须输出 `ReplayDataAnomalyEvent`。
6. manifest 写入 replay provenance。

### 验收条件

```text
[ ] 策略在 10:00 不能看到 [10:00, 10:01) bar close。
[ ] 中途 subscribe 前的数据不会被发送。
[ ] unsubscribe 后不再发送该 subscription 数据。
[ ] 多标的同 timestamp 的 replay 顺序可重复。
[ ] 数据 gap 不会静默补齐。
[ ] ReplayDataAnomalyEvent 进入 RuntimeEventSink。
```

---

## T15 — Simulated execution 假设写入 manifest

**优先级**：P2
**可并行性**：可独立推进
**依赖**：无

### 目标

让 backtest/paper_simulated 的成交假设可审计、可复现、可比较。

### manifest 必填字段

```text
fill_model_name
fill_model_version
slippage_model_name
slippage_model_version
commission_model_name
commission_model_version
volume_participation_limit
partial_fill_policy
broker_capability_model
unsupported_order_rejection_policy
market_data_latency_model
```

### 实施步骤

1. 为 fill model 增加 `model_name`、`model_version`、`to_manifest_payload()`。
2. `SimulatedExecutionAdapter` 输出 execution assumptions payload。
3. `BacktestReportWriter` 写入 assumptions。
4. `LiveReportWriter` 如果运行在 `PAPER_SIMULATED`，同样写入 assumptions。
5. `BrokerCapabilities` 写入 manifest。

### 验收条件

```text
[ ] 任意 backtest manifest 都能看到 fill/slippage/commission/capability 假设。
[ ] 不同 fill model 的报告可通过 manifest 区分。
[ ] unsupported order 在 backtest 中按 broker capability reject。
[ ] broker capability reject 会进入 RuntimeEventSink。
```

---

## T16 — RuntimeEvent envelope contract 化

**优先级**：P1
**可并行性**：可与 T18/T21 并行
**依赖**：无

### 目标

backtest / paper / live 统一事件 envelope，支持审计、恢复、trace 和跨模式分析。

### 必填字段

```text
event_id
run_id
runtime_mode
sequence_no
event_type
ts_event
ts_ingest
account_id optional
strategy_id optional
instrument_id optional
order_id optional
client_order_id optional
correlation_id
causation_id optional
parent_event_id optional
payload_schema_version
payload
```

### 实施步骤

1. 将 `RuntimeEvent` 定义为 frozen dataclass 或 pydantic immutable model。
2. 所有 sink 只接受 canonical `RuntimeEvent`。
3. 新增 event builder，集中生成 sequence/correlation/causation。
4. `FileEventStore.append()` 必须校验 sequence monotonic。
5. `RuntimeEventSink` contract test 覆盖 backtest/live sink。

### 验收条件

```text
[ ] 所有 runtime event 都有 run_id、runtime_mode、sequence_no。
[ ] order/fill/risk/account event 都有 correlation_id。
[ ] fill event 的 causation_id 指向 order event 或 broker callback event。
[ ] recovery replay 能按 sequence_no 重建顺序。
[ ] backtest sink 和 live sink 使用同一 envelope schema。
```

---

## T17 — RuntimeTopology builder 统一，删除 live 专属 topology builder

**优先级**：P1
**可并行性**：可与 T19/T20 并行
**依赖**：T02/T03 最好先完成

### 目标

消除 public `RuntimeTopologyBuilder` 与 `_LiveRuntimeTopologyBuilder` 的重复职责。

### 改名 / 合并

```text
_LiveRuntimeTopologyBuilder -> 删除或 BrokerRuntimeTopologyResolver
_ResolvedLiveRuntimeTopology -> ResolvedRuntimeTopology
_StrategyRuntimeBinding -> StrategyRuntimeBinding 或删除并入 StrategyRuntimeSpec
```

### 实施步骤

1. 梳理 `_LiveRuntimeTopologyBuilder` 的特殊逻辑。
2. 将通用部分合并到 `RuntimeTopologyBuilder`。
3. 将 broker-specific resolution 抽成 `BrokerRuntimeTopologyResolver`，仅处理：
   - account broker route
   - execution route
   - market data route
4. topology manifest 写入：

```text
strategy_id
account_id
broker_route_id
market_data_route_id
risk_profile_id
signal_aggregation_policy
```

5. 删除 live-only topology 私有类或只保留非 canonical shim。

### 验收条件

```text
[ ] 只有一个 public topology builder。
[ ] paper/live/backtest topology 都能生成 RuntimeTopologyManifest。
[ ] duplicate strategy_id 会 fail。
[ ] missing account route 会 fail。
[ ] missing broker route 会 fail。
[ ] class inventory 不再把 `_LiveRuntimeTopologyBuilder` 作为主要实现。
```

---

## T18 — Durable event/snapshot recovery 加固

**优先级**：P1
**可并行性**：可与 T16/T21 并行
**依赖**：T16 完成后实现更稳

### 目标

从“本地 deterministic recovery tests”推进到 live/paper broker runtime 可用的 durable recovery。

### 实施步骤

1. `FileEventStore.append()` 使用 atomic append 策略，明确 flush/fsync policy。
2. `FileSnapshotStore.write()` 使用 temp file + atomic rename。
3. snapshot 增加：

```text
snapshot_id
run_id
schema_version
created_at
last_event_sequence_no
topology_hash
config_hash
```

4. recovery 流程：

```text
load latest snapshot
validate snapshot schema
replay events after snapshot
validate sequence gap
build internal state
run broker reconciliation
produce BrokerRuntimeRecoveryDecision
```

5. event sequence gap 必须 block live/paper broker resume。
6. recovery 后默认 observation-only，直到 reconciliation 通过。

### 验收条件

```text
[ ] snapshot 写入中断不会留下被误读的半文件。
[ ] event sequence gap 会导致 recovery decision = BLOCK。
[ ] recovery replay 后必须执行 broker reconciliation。
[ ] reconciliation 未通过不能恢复 order submission。
[ ] recovery decision 写入 RuntimeEventSink 和 manifest。
```

---

## T19 — 多账户运行时隔离测试

**优先级**：P0
**可并行性**：可独立先写测试
**依赖**：T17 完成后更容易实现

### 目标

证明多账户并行不是仅有 topology class，而是在 order/fill/cancel/reconcile 运行时完全隔离。

### 测试清单

```text
test_fill_for_account_a_never_updates_account_b
test_cancel_for_account_a_cannot_cancel_account_b_order
test_broker_callback_with_wrong_account_is_quarantined
test_order_for_account_a_routes_to_account_a_execution_actor
test_missing_account_route_raises_route_not_found
test_order_route_metadata_restored_after_recovery
test_account_risk_config_is_account_scoped
```

### 实施步骤

1. `SubmitOrder`、`CancelOrder`、`ReplaceOrder`、`ApplyFill` 必须包含：

```text
account_id
strategy_id
route_metadata
correlation_id
```

2. `AccountActor` apply fill 前校验 `account_id`。
3. `ExecutionReportHandler` 对 wrong account callback 进入 quarantine。
4. `EventRouter` 不允许默认账户 fallback。
5. `OrderRouteMetadata` 支持 snapshot/restore。

### 验收条件

```text
[ ] 任意 fill 都不能跨账户 apply。
[ ] 任意 cancel 都不能跨账户 cancel。
[ ] wrong-account broker callback 进入 quarantine。
[ ] 缺失 account route fail-fast。
[ ] recovery 后 route metadata 仍能恢复。
```

---

## T20 — Signal aggregation 审计闭环

**优先级**：P1
**可并行性**：可独立推进
**依赖**：无

### 目标

多策略共用账户时，信号冲突、聚合、拒绝和最终 order plan 可追溯。

### 必填字段

`AggregatedSignalBatch` 必须包含：

```text
aggregation_policy
contributing_strategy_ids
rejected_strategy_ids
conflicts
target_before_risk
target_after_aggregation
account_id
instrument_id
correlation_id
```

`RiskDecision` 必须包含：

```text
aggregation_decision_id optional
contributing_strategy_ids optional
conflict_reason optional
```

### 实施步骤

1. 完成 `SignalAggregationPolicy` 到 runtime config 的接入。
2. `SignalAggregatorActor` 输出：
   - `signal_received`
   - `signal_conflict_detected`
   - `signal_aggregated`
   - `signal_rejected`
3. `OrderRouteMetadata` 记录 contributing strategy ids。
4. report manifest/ledger 可展示 order 来自哪些策略。

### 验收条件

```text
[ ] 两个策略同账户同标的反向 target 时行为 deterministic。
[ ] REJECT_CONFLICT 策略会拒绝冲突并记录原因。
[ ] PRIORITY_WINS 策略会记录 winner 和 rejected strategy。
[ ] SUM_TARGETS / WEIGHTED_NET 能记录每个策略贡献。
[ ] RiskDecision 和最终 OrderPlan 能反查 aggregation decision。
```

---

## T21 — Reporting base contract 与 manifest 完整性

**优先级**：P1
**可并行性**：可与 T16/T18 并行
**依赖**：无

### 目标

`ReportWriter` 和 `RuntimeArtifactWriter` 不再只是 placeholder，而是稳定 contract。

### 推荐 contract

```python
class RuntimeArtifactWriter(Protocol):
    def write_event(self, event: RuntimeEvent) -> ArtifactRef: ...
    def write_snapshot(self, snapshot: StateSnapshot) -> ArtifactRef: ...
    def write_manifest(self, manifest: RuntimeManifest) -> ArtifactRef: ...
    def finalize(self) -> RuntimeArtifacts: ...

class ReportWriter(Protocol):
    def write_manifest(self, manifest: RuntimeManifest) -> ArtifactRef: ...
    def finalize(self) -> RuntimeReport: ...
```

### manifest 必填字段

```text
run_id
runtime_mode
event_schema_version
artifact_schema_version
config_hash
topology_hash
startup_checklist_hash optional
dataset_provenance optional
broker_route_mapping_hash optional
reconciliation_report_id optional
execution_assumptions optional
created_at
finalized_at
```

### 实施步骤

1. 修改 base protocol。
2. `BacktestReportWriter` 和 `LiveReportWriter` 实现同一 contract。
3. `LiveReportWriter` 不只写 manifest，还要能 finalize runtime artifacts。
4. 所有 writer 输出 artifact refs。
5. 删除 placeholder docstring。

### 验收条件

```text
[ ] `ReportWriter` 有显式核心方法。
[ ] `RuntimeArtifactWriter` 有显式核心方法。
[ ] backtest/live manifest 使用同一 RuntimeManifest contract。
[ ] manifest 包含 config_hash、topology_hash、event_schema_version。
[ ] writer contract tests 对 backtest/live writer 都通过。
```

---

## T22 — 配置路径统一：`config.py` vs `config/models.py`

**优先级**：P1
**可并行性**：可与 T02/T04 并行
**依赖**：无

### 目标

清理文档和 class inventory 中同时出现 `qts/runtime/config.py` 与 `qts/runtime/config/models.py` 的不一致。

### 推荐结构

```text
qts/runtime/config/
  __init__.py
  models.py
  backtest.py
  paper.py
  live.py
  risk.py
  cost.py
  ibkr.py
```

### 实施步骤

1. 将 canonical config classes 移到 package。
2. `qts/runtime/config.py` 只保留 deprecated shim，或彻底删除。
3. 更新所有 import：

```python
from qts.runtime.config.models import TradingRuntimeConfig
from qts.runtime.config.backtest import BacktestRuntimeConfig
from qts.runtime.config.live import BrokerRuntimeConfig
```

4. inventory generator 忽略 deprecated shim。
5. docs 中只出现 canonical path。

### 验收条件

```text
[ ] class inventory 中 canonical config path 只显示 config package。
[ ] production code 不再 import `qts.runtime.config` 旧 flat module。
[ ] 旧路径 compatibility test 单独覆盖。
[ ] 文档中的推荐目录和实际目录一致。
[ ] config hash 生成不受 import path 影响。
```

---

## T23 — Application 层统一 StartRuntime command

**优先级**：P2
**可并行性**：可独立推进
**依赖**：T03/T04 完成后语义更清楚

### 目标

application 层不再有第二套 paper runtime 概念，统一通过 `StartRuntimeCommand` + `RuntimeMode` 启动。

### 改造范围

```text
qts/application/commands/start_paper.py
qts/application/services/operations.py
qts/api/schemas/operations.py
```

### 推荐命令

```text
StartRuntimeCommand
StopRuntimeCommand
PauseRuntimeCommand
ResumeRuntimeCommand
ReconcileRuntimeCommand
SnapshotRuntimeCommand
ActivateKillSwitchCommand
DeactivateKillSwitchCommand
```

### 实施步骤

1. 将 `start_paper.py` 迁移为 `start_runtime.py`。
2. DTO 中显式携带：

```text
runtime_mode
config_ref
operator_id
idempotency_key
reason_code
```

3. paper broker / paper simulated 由 runtime config 决定，不由 application command 名称决定。
4. 旧 `StartPaperCommand` 保留 deprecated alias。

### 验收条件

```text
[ ] application 层没有独立 paper runtime implementation。
[ ] StartRuntimeCommand 可启动 BACKTEST/PAPER_BROKER/PAPER_SIMULATED/LIVE_OBSERVATION。
[ ] LIVE 模式必须通过 safety gate 才能 order enabled。
[ ] old start_paper path 仅作为 compatibility shim。
```

---

## T24 — Runtime command 权限、审计和幂等 scope

**优先级**：P1
**可并行性**：可与 T13/T23 并行
**依赖**：无

### 目标

runtime 操作命令具备 operator identity、authorization、reason code、audit event 和幂等 scope。

### 新字段

```text
operator_id
operator_role
authorization_scope
reason_code
idempotency_key
idempotency_scope
requested_at
approved_by optional
approval_required
```

### 实施步骤

1. `RuntimeCommand` 增加 operator metadata。
2. `CommandIdempotencyStore` key 改为：

```text
command_type
runtime_instance_id
operator_id
idempotency_key
```

3. kill switch deactivate 需要 elevated permission。
4. live order enablement 需要 dual-control：
   - requester
   - approver
5. 所有 runtime command 写入 audit event。
6. `resume` 在 live/paper broker reconnect 后必须要求 reconciliation。

### 验收条件

```text
[x] duplicate command 返回同一 RuntimeCommandResult。
[x] kill switch deactivate 没有权限会被拒绝。
[x] LIVE order enablement 没有 approver 会被拒绝。
[x] pause/resume/kill-switch/reconcile/snapshot 都写 audit event。
[x] reconnect 后 resume 不做 reconciliation 会被拒绝。
```

---

## T25 — 文档、class inventory 与 architecture snapshot 更新

**优先级**：P1
**可并行性**：可与各 task 并行，每个 milestone 后更新
**依赖**：无

### 目标

确保 HTML 职责链、推荐目录、class inventory 不再展示旧路径、旧类名和旧缓存。

### 实施步骤

1. 更新职责链文档：
   - `LiveRuntimeSession` 改为 `RuntimeSession`。
   - paper/live 会话编排改为 broker-capable runtime session。
   - `qts.runtime` 是共享 runtime，不是 live 专属。
2. 更新推荐目录：
   - `qts/runtime/config/models.py` 与实际一致。
   - transport canonical path 使用 `transports`。
3. class inventory generator 忽略 deprecated alias。
4. 增加 architecture snapshot：

```text
class_inventory_after_post_review.json
import_graph_after_post_review.json
```

5. 每个 milestone 生成 diff report。

### 验收条件

```text
[ ] 文档不再把 `LiveRuntimeSession` 作为 canonical session。
[ ] 文档不再把 `MarketDataAdapter` 放在 `qts.data.live`。
[ ] 文档不再显示 production Fake* class。
[ ] 推荐目录和实际 source path 一致。
[ ] inventory 中 deprecated alias 被标记为 compatibility，不作为主类。
```

---

## T26 — CI architecture guardrail 升级为必过项

**优先级**：P0
**可并行性**：可与所有 task 并行，逐步收紧
**依赖**：T01/T05/T07/T08 完成后可开启 strict mode

### 目标

把命名、目录、依赖、共享边界、provider SDK 泄漏、fake 泄漏都变成自动化检查。

### Guardrail 规则

```text
ProductionNoFakeClassRule
ProductionPlaceholderDocstringRule
ProductionNoBetaWordingRule
SharedRuntimeNoBacktestOnlyWordingRule
LivePackageNoReplayClassRule
DataLiveNoSharedContractRule
TransportCanonicalPathRule
RuntimeNoProviderSdkImportRule
DomainNoRuntimeImportRule
StrategySdkNoBrokerImportRule
PipelineNoActorImportRule
AdapterNoActorMutationRule
BrokerSymbolBoundaryRule
DeprecatedImportNoNewUsageRule
```

### 实施步骤

1. `tests/quality/test_architecture_guardrails.py` 覆盖所有规则。
2. CI 分两阶段：
   - warning mode：输出违规列表。
   - strict mode：违规直接 fail。
3. 对 deprecated shim 添加白名单：

```text
qts.runtime.live_runtime_session
qts.runtime.config
qts.data.live.adapter
```

白名单必须带 expiry release。
4. 新增 pre-commit hook：

```bash
python -m qts.quality.guardrails --strict
```

### 验收条件

```text
[ ] CI strict mode 下所有 guardrail 通过。
[ ] 新增 Fake* 到 production package 会 fail。
[ ] 新增 *Transport 到 adapters 目录会 fail。
[ ] strategy_sdk import broker/execution internals 会 fail。
[ ] domain import runtime 会 fail。
[ ] deprecated shim 过期后仍被 import 会 fail。
```

---

# 3. 里程碑建议

## Milestone 1 — 名称与边界收敛

包含：T00, T01, T02, T03, T04, T05, T06, T22, T25, T26 warning mode。

### 验收

```text
[ ] canonical class names 和目录语义一致。
[ ] production no fake / no placeholder / no beta。
[ ] paper broker / paper simulated / live observation / live 语义清晰。
[ ] 文档和 inventory 不再显示旧 canonical path。
```

## Milestone 2 — Broker runtime safety

包含：T07, T08, T09, T10, T11, T12, T13, T24。

### 验收

```text
[x] IBKR transport 拆分完成。
[x] callback 幂等、乱序、quarantine 测试通过。
[x] market-data permission/freshness 进入 RiskEngine gate。
[x] startup checklist 强制 block live/paper broker order。
[x] runtime command 有 operator audit 和 idempotency。
```

## Milestone 3 — 多账户、多策略、恢复与报告

包含：T16, T17, T18, T19, T20, T21。

### 验收

```text
[ ] RuntimeEvent envelope 统一。
[ ] topology builder 单一化。
[ ] 多账户隔离测试通过。
[ ] signal aggregation 可审计。
[ ] recovery 必须经过 event replay + broker reconciliation。
[ ] report/manifest contract 完整。
```

## Milestone 4 — 回测真实性与生产可复现

包含：T14, T15，并补跑全量 regression。

### 验收

```text
[ ] replay 无未来函数 contract tests 通过。
[ ] simulated execution 假设写入 manifest。
[ ] backtest/paper/live event artifact 可统一解析。
```

---

# 4. 最终全局验收清单

当所有 task 完成后，系统需要满足：

```text
[ ] Backtest / PAPER_SIMULATED / PAPER_BROKER / LIVE_OBSERVATION / LIVE 使用同一核心 runtime contract。
[ ] LIVE capital 只有在 startup checklist、reconciliation、market-data permission、operator signoff、kill switch、event/snapshot store 都通过后才能下单。
[ ] paper broker 与 paper simulated 语义完全分离。
[ ] production package 中没有 Fake*、placeholder、beta、intended later wording。
[ ] Source / Adapter / Transport / Flow / Actor / Sink / ReportWriter 目录和命名一致。
[ ] IBKR callback 重复、乱序、延迟、wrong account 都有 deterministic behavior。
[ ] 多账户 fill/cancel/order route 不串账户。
[ ] 多策略 signal conflict 可审计。
[ ] Replay source 服从 subscription 和 visible_at，不允许未来函数。
[ ] RuntimeEvent envelope 统一，event store 可恢复，snapshot 可验证。
[ ] Report manifest 含 config_hash、topology_hash、event_schema_version、execution assumptions、startup/reconciliation evidence。
[ ] CI guardrail strict mode 必过。
```

---

# 5. 建议 PR 切分

为了减少单个 PR 风险，建议按如下 PR 提交：

```text
PR-01 baseline inventory + smoke tests
PR-02 fake/placeholder/beta cleanup + guardrail warning mode
PR-03 RuntimeSession rename with compatibility shims
PR-04 RuntimeMode / LiveOrderPermission / paper split
PR-05 data shared contracts migration
PR-06 transport package migration
PR-07 RuntimeSession coordinator split
PR-08 IBKR order transport split
PR-09 IBKR callback idempotency + quarantine
PR-10 market-data permission/freshness risk rules
PR-11 broker startup gate hard enforcement
PR-12 runtime event envelope + event store sequence validation
PR-13 topology builder unification + account isolation tests
PR-14 signal aggregation auditability
PR-15 reporting contract + manifest completeness
PR-16 durable recovery hardening
PR-17 replay no-future tests + simulated execution manifest
PR-18 application runtime commands + authorization audit
PR-19 docs/inventory refresh + guardrail strict mode
```

---

# 6. Live capital enablement gate

完成上述 task 仍不代表自动启用 live capital。启用 live capital 需要额外的运营签核：

```text
[ ] 工程签核：CI strict mode 通过，所有 P0/P1 task 完成。
[ ] 风控签核：risk config、market data freshness gate、kill switch、operator permission 全部验证。
[ ] 运维签核：IB Gateway、clientId、account code、reconnect、snapshot/event store、alerting 全部验证。
[ ] 交易签核：live account、产品权限、订单类型、TIF、margin/short/futures/options 权限验证。
[ ] 试运行签核：LIVE_OBSERVATION 至少完成指定窗口观测，且 reconciliation 无重大 drift。
```
