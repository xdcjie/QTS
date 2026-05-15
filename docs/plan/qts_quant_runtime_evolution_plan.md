# 量化交易系统 Backtest / Paper / Live 统一运行时演进计划

生成日期：2026-05-14
适用范围：`backtest / paper / live` 统一交易流程、模块边界、命名规范、多策略多账户并行、IBKR 市场数据与下单、backtest replay market data、可观测性与运行安全。

---

## 0. 总体结论

当前系统把 `backtest / paper / live` 作为同一条统一交易流程在不同边界上的实现，这个方向是合理的，也符合成熟事件驱动交易系统的主流架构理念。

建议将目标明确为：

```text
共享核心交易内核
+ 共享策略 API
+ 共享风控 / 订单 / 账户状态机
+ 不同 market data source
+ 不同 execution adapter
+ 不同 clock / reconciliation / startup gate / reporting
```

也就是说：

```text
Backtest:
  ReplayMarketDataSource + SimulatedExecutionAdapter + ReplayClock + SimulatedAccount

Paper Broker:
  StreamingMarketDataSource + BrokerExecutionAdapter + BrokerClock + IBKR Paper Account

Paper Simulated:
  StreamingMarketDataSource 或 ReplayMarketDataSource + SimulatedExecutionAdapter + SimulatedAccount

Live:
  StreamingMarketDataSource + BrokerExecutionAdapter + BrokerClock + Real Broker Account
```

当前架构已经具备较好的基础，但仍需重点强化：

```text
1. RuntimeMode 与 paper 语义拆分。
2. Source / Adapter / Transport / Flow / Pipeline / Actor / Sink 术语固化。
3. RuntimeRunId 与统一 RuntimeEvent envelope。
4. RuntimeTopology，显式支持多策略、多账户并行。
5. SignalAggregatorActor 的冲突策略产品化。
6. IBKR order id、callback idempotency、reconnect、reconciliation。
7. IBKR market data permission、stale data、resubscribe、pacing。
8. Backtest replay 做成真正 subscription-driven broker-like market data source。
9. live startup safety checklist 产品化。
10. guardrail 进入 CI，自动阻止边界退化。
```

---

## 1. 架构原则

### 1.1 统一流程原则

```text
Config
 -> MarketDataSource
 -> MarketDataPipeline / MarketDataFlow
 -> StrategyExecutionPipeline
 -> TargetIntentProcessor / OrderPlanBuilder
 -> RiskEngine
 -> OrderManagerActor
 -> ExecutionActor
 -> ExecutionAdapter
 -> ExecutionReportHandler
 -> AccountActor
 -> RuntimeEventSink / ReportWriter
```

上述链路应在 backtest、paper、live 三种模式下保持一致。模式差异只允许出现在：

```text
1. market data source
2. execution adapter
3. broker transport
4. runtime clock
5. reconciliation policy
6. startup safety gate
7. reporting artifact
8. account environment
```

策略层、风控层、订单状态机、账户记账和 event sink envelope 不应因为模式不同而发生结构性变化。

### 1.2 模块边界原则

| 层级 | 允许职责 | 禁止职责 |
|---|---|---|
| `qts.core` | ID、时间区间、基础值对象 | broker/provider/runtime 依赖 |
| `qts.domain` | Bar、Quote、Tick、Order、ExecutionReport、RiskDecision | actor、adapter、I/O |
| `qts.registry` | instrument、symbol、calendar、roll、chain | 订单执行、账户记账 |
| `qts.data` | data source、subscription、adapter、pipeline、aggregation | 下单、账户 mutation |
| `qts.strategy_sdk` | 策略 API、只读视图、intent API | broker、risk 内部实现、actor 引用 |
| `qts.runtime` | actor、flow、session、event store、recovery | provider SDK 直接依赖 |
| `qts.risk` | pre-trade risk、kill switch、rules | broker transport |
| `qts.execution` | order lifecycle、execution adapter、simulator、idempotency | 策略逻辑 |
| `qts.portfolio` | cash、position、reservation、fill accounting | broker callback 解析 |
| `qts.reconciliation` | broker/internal snapshot 对账 | 策略执行 |
| `qts.reporting` | report、manifest、artifact | 核心状态 mutation |
| `qts.quality` | 架构 guardrail | 业务执行逻辑 |

### 1.3 命名术语原则

| 术语 | 定义 | 示例 |
|---|---|---|
| `Source` | runtime 看到的数据源生命周期，负责 subscribe/unsubscribe、degradation、callback delivery | `ReplayMarketDataSource`, `StreamingMarketDataSource` |
| `Adapter` | provider/broker shape 到内部 domain model 的映射 | `IbkrMarketDataAdapter`, `IbkrOrderExecutionAdapter` |
| `Transport` | 外部 SDK/网络连接和 callback 接入 | `IbkrTwsMarketDataTransport`, `IbAsyncOrderExecutionTransport` |
| `Pipeline` | 纯数据处理，不拥有 actor/queue/runtime mutable state | `MarketDataPipeline`, `BarAggregationPipeline` |
| `Flow` | runtime 编排，把 source event 接入 actor/queue | `MarketDataFlow` |
| `Actor` | 拥有 mutable state，通过 message 串行处理 | `AccountActor`, `OrderManagerActor` |
| `Sink` | runtime event 出口 | `LiveRuntimeEventSink`, `BacktestRuntimeEventSink` |
| `ReportWriter` | 生成最终 artifact 或 manifest | `BacktestReportWriter`, `LiveReportWriter` |

---

# P0 计划

P0 是必须优先处理的结构性事项。这些事项不解决，后续 live 安全、多账户并行、IBKR 稳定性和 backtest/live parity 都会继续被模糊语义拖累。

---

## P0-1：统一 `RuntimeMode` 与 paper 语义

### Review 项

当前 `paper` 可能同时表示：

```text
1. 使用 IBKR paper account。
2. 使用本地 simulated broker。
3. 使用实时行情但模拟撮合。
4. 使用历史 replay 但按 paper 路径跑。
```

这会影响配置、安全门禁、reporting、reconciliation 和测试命名。尤其是 live/paper 的资金风险不同，如果没有显式区分，可能导致错误环境下提交订单。

### 目标

新增清晰的运行模式：

```python
class RuntimeMode(Enum):
    BACKTEST = "backtest"
    PAPER_BROKER = "paper_broker"
    PAPER_SIMULATED = "paper_simulated"
    LIVE = "live"
    OBSERVATION = "observation"
```

模式含义：

```text
BACKTEST:
  历史数据 replay + simulated execution + simulated account。

PAPER_BROKER:
  实时 broker market data + broker paper account execution。

PAPER_SIMULATED:
  实时或 replay market data + local simulated execution。

LIVE:
  实时 market data + real broker account execution。

OBSERVATION:
  允许订阅行情和运行策略观测，但禁止提交订单。
```

### 实施清单

```text
1. 新增 qts/runtime/mode.py
   - RuntimeMode
   - MarketDataEnvironment
   - ExecutionEnvironment
   - AccountEnvironment

2. 修改 LiveMode
   - 如果 LiveMode 只用于 live 权限，改名为 LivePermissionMode。
   - 如果 LiveMode 表示运行模式，则迁移到 RuntimeMode。

3. 修改 LiveRuntimeConfig
   - 添加 mode: RuntimeMode。
   - 添加 allow_live_orders: bool。
   - 添加 observation_only: bool。
   - 添加 broker_account_kind: paper/live/simulated。
   - 添加 execution_environment。
   - 添加 market_data_environment。

4. 修改 BacktestRuntimeConfig
   - 添加 mode: RuntimeMode = BACKTEST。
   - 添加 execution_environment = SIMULATED。
   - 添加 market_data_environment = REPLAY。

5. 新增 mode/account/port 校验
   - mode == LIVE:
     - broker account code 必须匹配 live account 规则。
     - IBKR port 默认必须是 4001，除非显式 override 并记录原因。
     - allow_live_orders 必须为 true。
     - operator signoff 必须存在。
   - mode == PAPER_BROKER:
     - broker account code 必须匹配 paper account 规则，例如 DU...。
     - IBKR port 默认必须是 4002。
   - mode == PAPER_SIMULATED:
     - 禁止构造真实 broker order transport。
     - 可以允许真实或 replay market data。
   - mode == OBSERVATION:
     - 允许 market data。
     - 禁止 submit order、cancel order、replace order。

6. 修改 reporting manifest
   - 写入 runtime_mode。
   - 写入 market_data_environment。
   - 写入 execution_environment。
   - 写入 account_environment。
   - 写入 broker_account_kind。
   - 写入 allow_live_orders。
   - 写入 operator_signoff_id。

7. 修改 runtime event envelope
   - 每条事件写入 mode。
   - 每条 order/risk/fill 事件写入 execution_environment。

8. 新增测试
   - test_live_rejects_paper_account_code
   - test_paper_broker_rejects_live_account_code
   - test_observation_mode_blocks_submit_order
   - test_paper_simulated_never_constructs_ibkr_order_transport
   - test_live_requires_operator_signoff
   - test_mode_written_to_report_manifest
```

### 完成标准

```text
1. 每个 run 都能明确说明资金风险级别。
2. paper_broker 和 paper_simulated 不再共享模糊命名。
3. live 下单必须经过 mode/account/port/signoff 校验。
4. observation mode 可以运行策略和行情订阅，但无法提交订单。
```

---

## P0-2：定义 MarketData Source / Adapter / Transport / Flow 词典并落 guardrail

### Review 项

当前存在 `ReplayMarketDataAdapter`、`FakeMarketDataAdapter` 等容易和 live/source/transport 混用的命名。`qts.data.live` 中如果出现 replay/fake 概念，会让 reviewer 难以判断这个类到底是生产 live、测试 fake，还是 backtest replay。

### 目标

让名字直接表达边界职责，并通过 guardrail 自动检查。

推荐结构：

```text
qts/data/
  interfaces.py
  subscriptions.py
  provenance.py
  sources/
    replay_market_data_source.py
    streaming_market_data_source.py
  adapters/
    ibkr_market_data_adapter.py
    simulated_market_data_adapter.py
  transports/
    ibkr_tws_market_data_transport.py
    ib_async_market_data_transport.py
  pipelines/
    market_data_pipeline.py
    bar_aggregation_pipeline.py
```

### 实施清单

```text
1. 新增 docs/architecture/naming.md
   - Source 定义。
   - Adapter 定义。
   - Transport 定义。
   - Pipeline 定义。
   - Flow 定义。
   - Actor 定义。
   - Sink 定义。
   - ReportWriter 定义。

2. 整理 qts.data.live.adapter
   当前可能存在：
     qts/data/live/adapter.py
   建议迁移为：
     qts/data/interfaces.py
     qts/data/sources/base.py
     qts/data/adapters/base.py

3. 迁移 ReplayMarketDataAdapter
   推荐：
     qts.data.sources.replay_market_data_source.ReplayMarketDataSource
   或：
     qts.data.adapters.replay_market_data_adapter.ReplayMarketDataAdapter
   但不应放在 qts.data.live。

4. 迁移 FakeMarketDataAdapter
   如果用于测试：
     qts.testing.fakes.market_data.FakeMarketDataAdapter
   如果用于 paper_simulated：
     qts.data.adapters.simulated_market_data_adapter.SimulatedMarketDataAdapter

5. 调整 StreamingMarketDataSource
   - Source 负责 subscription lifecycle。
   - Adapter 负责 provider message -> internal event。
   - Transport 负责外部 SDK callbacks。
   - Source 不直接解析 provider 原始对象。

6. 调整 MarketDataFlow
   - Flow 负责把 market data event 接入 actor/queue。
   - Flow 不负责 provider message 解析。
   - Flow 不负责 broker connection。

7. 新增 guardrail
   - 禁止 `Replay*` 出现在 `qts.data.live`。
   - 禁止 `Fake*` 出现在 production package，除非在 `qts.testing` 或 `qts.simulation`。
   - 禁止 `Transport` 依赖 runtime actors。
   - 禁止 `Pipeline` 依赖 actor/ref/mailbox。
   - 禁止 `Adapter` 直接修改 AccountActor 或 OrderManagerActor。

8. 新增 import graph 测试
   - test_data_pipeline_has_no_runtime_imports
   - test_transport_has_no_strategy_imports
   - test_strategy_sdk_has_no_broker_imports
   - test_runtime_has_no_provider_sdk_imports
```

### 完成标准

```text
1. 任何 reviewer 看到类名就能判断其边界层级。
2. replay/fake/live 不再混在 live 包里。
3. qts.quality 能自动阻止命名和依赖边界退化。
```

---

## P0-3：建立统一 `RuntimeRunId` 和事件 envelope

### Review 项

当前 `BacktestRunId` 能表达 backtest run，但统一 runtime 需要跨 backtest/paper/live 的 run identity。否则 event store、report、reconciliation 和排查工具会按模式割裂。

### 目标

所有模式统一使用：

```text
RuntimeRunId
RuntimeInstanceId
RuntimeEvent
CorrelationId
CausationId
```

推荐事件 envelope：

```python
@dataclass(frozen=True)
class RuntimeEvent:
    event_id: EventId
    run_id: RuntimeRunId
    mode: RuntimeMode
    sequence_no: int
    ts_event: datetime
    ts_ingest: datetime
    account_id: AccountId | None
    strategy_id: StrategyId | None
    instrument_id: InstrumentId | None
    correlation_id: CorrelationId
    causation_id: CausationId | None
    event_type: RuntimeEventType
    payload: Mapping[str, Any]
```

### 实施清单

```text
1. 在 qts/core/ids.py 增加
   - RuntimeRunId
   - RuntimeInstanceId

2. 保留 BacktestRunId
   - 作为历史兼容 alias。
   - 或仅作为 BacktestRuntimeConfig 内部字段。
   - reporting/runtime event 使用 RuntimeRunId。

3. 修改 RuntimeEvent
   - 添加 run_id。
   - 添加 mode。
   - 添加 sequence_no。
   - 添加 account_id。
   - 添加 strategy_id。
   - 添加 instrument_id。
   - 添加 correlation_id。
   - 添加 causation_id。
   - 添加 payload schema version。

4. 修改 RuntimeEventSink
   - BacktestRuntimeEventSink 与 LiveRuntimeEventSink 输出同一 envelope。
   - sink 可以不同，但 event envelope 不能不同。

5. 修改 ReportWriter
   - manifest 写入 run_id。
   - manifest 写入 event schema version。
   - manifest 写入 input data provenance。
   - manifest 写入 broker/account mapping hash。
   - manifest 写入 runtime topology hash。

6. 修改 OrderManagerActor / ExecutionActor / AccountActor
   - 关键状态事件携带 correlation_id。
   - fill/account 事件通过 causation_id 链接到 execution report。

7. 新增测试
   - test_backtest_and_live_events_share_envelope
   - test_correlation_id_flows_from_market_data_to_order
   - test_fill_event_has_causation_order_event
   - test_event_sequence_no_monotonic_per_run
   - test_manifest_contains_runtime_run_id
```

### 完成标准

```text
1. 任意订单、成交、账户变化都能追溯到策略、行情事件和风控决策。
2. backtest/paper/live 的 event artifact 可以用同一个分析工具读取。
3. event store 能按 run_id + sequence_no 做恢复与缺口检测。
```

---

## P0-4：修正共享类中的 backtest-only wording

### Review 项

部分共享 runtime 类的说明仍有 backtest-only 表述。例如 `TargetIntentProcessor` 如果说明为 “Translate strategy target intents into validated, executed backtest orders”，会误导维护者以为它只服务 backtest。

### 目标

所有共享类的命名和 docstring 模式无关。

### 实施清单

```text
1. 扫描 qts/runtime 下所有 docstring 和注释
   grep:
     - backtest orders
     - live-beta
     - fake or real
     - intended to be owned later
     - placeholder
     - temporary
     - TODO production

2. 修改 TargetIntentProcessor docstring
   从：
     Translate strategy target intents into validated, executed backtest orders.
   改为：
     Translate strategy target intents into validated runtime order submissions.

3. 修改 LiveRuntime docstring
   如果保留：
     明确它是 facade、legacy wrapper 还是 beta test runtime。
   如果不用：
     删除或迁移到 tests/support。

4. 修改 LiveRuntimeSession 命名候选
   如果它是模式无关 session：
     LiveRuntimeSession -> RuntimeSession。
   如果它只服务 live/paper：
     保留 LiveRuntimeSession，但明确 backtest 不通过它。

5. 修改 CashBook / PositionBook docstring
   从：
     intended to be owned by AccountActor later
   改为：
     Owned by AccountActor for account-state mutation.

6. 修改 ReportWriter / RuntimeArtifactWriter docstring
   - 去掉 placeholder。
   - 写清楚 artifact contract。

7. 新增 guardrail
   - shared runtime class docstring 不允许出现 “backtest orders”。
   - production code 不允许出现 “placeholder” docstring。
   - qts.runtime 中 shared 类不允许出现 “beta only” 文案。

8. 新增测试
   - test_shared_runtime_docstrings_are_mode_neutral
   - test_no_placeholder_docstrings_in_production
```

### 完成标准

```text
1. 类说明和实际边界一致。
2. 新人 review 时不会误以为共享处理器只支持 backtest。
3. 架构文档、docstring、命名形成一致语言。
```

---

# P1 计划

P1 是在 P0 基础上建立生产级多策略、多账户、IBKR、backtest replay 和执行能力模型的核心计划。

---

## P1-1：建立 `RuntimeTopology`，产品化多策略/多账户

### Review 项

当前系统已经具备 `StrategyActor`、`SignalAggregatorActor`、`AccountPartitionPolicy`、`AccountBrokerMapping`、`EventRouter` 等基础，但仍需要一个显式 topology 来证明多策略、多账户并行不是隐式拼装。

### 目标

一个 runtime session 启动前可以输出完整拓扑：

```text
which strategy
runs on which account
uses which market data
routes to which execution adapter
uses which risk config
writes to which event sink
```

推荐对象：

```python
@dataclass(frozen=True)
class RuntimeTopology:
    run_id: RuntimeRunId
    mode: RuntimeMode
    accounts: list[AccountRuntimeSpec]
    strategies: list[StrategyRuntimeSpec]
    broker_routes: list[BrokerRouteSpec]
    market_data_routes: list[MarketDataRouteSpec]
```

### 实施清单

```text
1. 新增 qts/runtime/topology.py
   - RuntimeTopology
   - StrategyRuntimeSpec
   - AccountRuntimeSpec
   - BrokerRouteSpec
   - MarketDataRouteSpec
   - RuntimePartitionKey

2. StrategyRuntimeSpec 字段
   - strategy_id
   - strategy_class
   - account_id
   - subscriptions
   - capital_allocation
   - risk_profile_id
   - signal_aggregation_policy
   - enabled

3. AccountRuntimeSpec 字段
   - account_id
   - broker_id
   - base_currency
   - risk_config
   - initial_cash
   - live_account_mapping
   - broker_account_code
   - account_environment

4. BrokerRouteSpec 字段
   - broker_id
   - account_id
   - execution_adapter_type
   - order_transport_type
   - broker_capabilities
   - idempotency_store_ref

5. MarketDataRouteSpec 字段
   - source_id
   - source_type
   - provider
   - subscriptions
   - permission_policy
   - stale_data_policy

6. RuntimeTopologyBuilder
   - 从 BacktestRuntimeConfig / LiveRuntimeConfig 构建 topology。
   - 校验 strategy_id 唯一。
   - 校验 account_id 存在。
   - 校验 broker route 存在。
   - 校验 subscription 可解析。
   - 校验 instrument_id 已注册。
   - 校验同一 account 下 risk config 存在。

7. RuntimeTopologyManifest
   - 每次启动写入 manifest。
   - 包含 strategy/account/broker/data route。
   - 生成 topology_hash。
   - report manifest 引用 topology_hash。

8. 修改 RuntimeSessionDependencies
   - 改为从 RuntimeTopology 构造 actor graph。
   - 不允许手工散落拼接多账户 route。

9. 新增测试
   - test_two_strategies_one_account_topology
   - test_two_accounts_one_strategy_each_topology
   - test_strategy_referencing_missing_account_fails
   - test_duplicate_strategy_id_fails
   - test_missing_broker_route_fails
   - test_topology_hash_stable
```

### 完成标准

```text
1. 多策略、多账户启动前可审计。
2. 每条 order 都能反查 strategy/account/broker/data route。
3. 拓扑变化会反映到 manifest 和 topology_hash。
```

---

## P1-2：产品化 `SignalAggregatorActor` 的冲突处理

### Review 项

多策略共用账户时，信号合并是最容易出事故的地方。仅仅 “aggregate signals” 不够，需要明确策略冲突规则。

典型冲突：

```text
Strategy A -> target long 10 GC
Strategy B -> target short 5 GC
```

系统必须确定地决定：加总、净额、优先级胜出，还是拒绝冲突。

### 目标

实现可配置、可测试、可审计的 signal aggregation。

### 实施清单

```text
1. 新增 qts/runtime/signal_policy.py
   - SignalAggregationPolicy
   - SignalConflict
   - SignalAggregationDecision
   - AggregatedSignalBatch

2. 支持策略
   - SUM_TARGETS：同账户同标的 target 加总。
   - PRIORITY_WINS：高优先级策略覆盖低优先级策略。
   - WEIGHTED_NET：按策略权重净额。
   - REJECT_CONFLICT：发现方向冲突直接拒绝。

3. StrategyRuntimeSpec 增加
   - signal_priority
   - signal_weight
   - conflict_group

4. AggregatedSignalBatch 增加
   - contributing_strategy_ids
   - rejected_strategy_ids
   - conflict_reason
   - aggregation_policy
   - target_before_risk
   - target_after_aggregation

5. RiskEngine 输入增加 aggregation metadata
   - 方便排查订单来自哪些策略。
   - risk decision 输出保留 contributing_strategy_ids。

6. RuntimeEventSink 输出
   - signal_received
   - signal_conflict_detected
   - signal_aggregated
   - signal_rejected

7. 修改 StrategyExecutionPipeline
   - 策略 intent 不直接进入 OrderPlanBuilder。
   - 必须先进入 SignalAggregatorActor。
   - 聚合结果再进入 TargetIntentProcessor。

8. 新增测试
   - test_sum_targets_same_direction
   - test_reject_conflicting_targets
   - test_priority_wins_conflicting_targets
   - test_weighted_net_targets
   - test_signal_conflict_event_emitted
   - test_aggregation_metadata_reaches_risk_engine
```

### 完成标准

```text
1. 两个策略对同一账户同一标的发相反 intent 时，系统行为确定且可审计。
2. 风控看到的是 aggregation 后的 order plan，但仍可追溯每个策略贡献。
3. 聚合策略变化会写入 RuntimeTopologyManifest。
```

---

## P1-3：完善 account partition 和 per-account actor graph

### Review 项

`AccountPartitionPolicy`、`AccountBrokerMapping`、`AccountRiskConfig` 已存在，但需要把 actor graph 明确成 per-account partition，防止状态串账户。

### 目标

每个账户拥有独立状态和风险边界：

```text
AccountActor(account_id)
OrderManagerActor(account_id)
RiskEngine(account_id)
ExecutionActor(account_id)
BrokerRoute(account_id -> broker/account)
```

### 实施清单

```text
1. 新增 AccountRuntimePartition
   - account_id
   - account_actor_ref
   - order_manager_actor_ref
   - execution_actor_ref
   - risk_engine
   - broker_route
   - snapshot_store

2. 修改 EventRouter
   - order/risk/account/fill message 默认按 account_id route。
   - market data 按 subscription fan-out。
   - strategy event 按 strategy_id route。
   - route 缺失必须 fail-fast。

3. 修改 OrderPlanBuilder
   - 输入必须包含 account_id。
   - 输出 OrderPlan 必须包含 account_id。
   - 不允许默认账户。

4. 修改 SubmitOrder / CancelOrder / ReplaceOrder
   - 必须包含 account_id。
   - 必须包含 strategy_id。
   - 必须包含 client_order_id。
   - 必须包含 correlation_id。

5. 修改 AccountActor
   - snapshot 按 account_id 输出。
   - apply fill 时校验 fill.account_id。
   - 禁止跨 account apply fill。

6. 修改 ExecutionReportHandler
   - broker execution report 必须 resolve 到 account_id。
   - 无法 resolve 的 fill 进入 quarantine，不得入账。

7. 新增 per-account metrics
   - orders_submitted_total{account_id}
   - fills_total{account_id}
   - risk_rejections_total{account_id}
   - account_reconciliation_drift_total{account_id}

8. 新增测试
   - test_fill_for_account_a_does_not_change_account_b
   - test_order_for_account_a_routes_to_account_a_execution_actor
   - test_missing_account_route_raises_route_not_found
   - test_unresolved_execution_report_is_quarantined
   - test_no_default_account_allowed
```

### 完成标准

```text
1. 多账户并行时状态不串。
2. route 错误会 fail-fast，而不是落到默认账户。
3. fill 入账前必须确认 account_id。
```

---

## P1-4：IBKR order execution 可靠性升级

### Review 项

IBKR adapter 和 transport 边界已经具备，但生产级 live/paper 的关键在 order id、callback、reconnect、reconciliation、idempotency。

IBKR 回调可能重复、乱序、延迟；partial fill、commissionReport、orderStatus、openOrder、execDetails 之间不一定按理想顺序出现。

### 目标

IBKR order path 变成可恢复、可审计、可重复处理的状态机。

### 实施清单

```text
1. 新增 IbkrOrderIdAllocator
   - 持久化 nextValidId。
   - reconnect 后 reconcile nextValidId。
   - clientId 维度隔离。
   - 防止重启后复用 order id。

2. 新增 BrokerOrderMap
   - internal_order_id
   - client_order_id
   - ibkr_order_id
   - perm_id
   - account_id
   - strategy_id
   - status
   - submitted_at
   - last_broker_status_at

3. 修改 IbkrOrderExecutionAdapter
   - submit 前生成 client_order_id。
   - placeOrder 后记录 pending submission。
   - openOrder/orderStatus/execDetails 映射到同一 internal order。
   - cancel/replace 也通过 client_order_id 和 ibkr_order_id 映射。

4. 完善 callback 去重
   - FillIdempotencyStore 支持 broker_exec_id。
   - orderStatus 重复不得重复改变状态。
   - execDetails 重复不得重复入账。
   - commissionReport 可以晚于 fill 到达。
   - partial fill 按 exec_id 去重。

5. 增加 startup reconciliation
   - reqOpenOrders。
   - reqAllOpenOrders，按配置决定是否允许。
   - reqPositions。
   - reqExecutions since last snapshot。
   - reqAccountSummary。

6. 增加 reconnect 流程
   - disconnect -> runtime degraded。
   - 暂停新单。
   - reconnect -> request open orders/positions/executions。
   - reconcile drift。
   - drift 通过后恢复。
   - drift 未通过进入 observation 或 kill switch。

7. 新增 broker callback event
   - ibkr_open_order_received
   - ibkr_order_status_received
   - ibkr_execution_details_received
   - ibkr_commission_report_received
   - ibkr_order_callback_duplicate_dropped
   - ibkr_order_callback_unresolved_quarantined

8. 修改 ExecutionReportHandler
   - 对 duplicate fill 做幂等处理。
   - 对 unresolved fill 进入 quarantine。
   - 对 late commission 更新成本，不重复更新 position quantity。

9. 新增测试
   - test_duplicate_order_status_is_idempotent
   - test_partial_fill_applied_once
   - test_commission_report_after_fill_updates_trade_cost
   - test_reconnect_blocks_new_orders_until_reconciled
   - test_unknown_exec_id_is_quarantined
   - test_order_id_allocator_survives_restart
   - test_perm_id_maps_to_internal_order
```

### 完成标准

```text
1. IBKR callback 重复、乱序、延迟不会导致重复入账。
2. Gateway 重启后可以恢复 open orders 和 position 状态。
3. live/paper order path 有完整审计证据。
4. reconnect 期间不会继续提交新单。
```

---

## P1-5：IBKR market data 订阅可靠性升级

### Review 项

IBKR market data 的核心风险是 permission、delayed data、stale data、subscription restore、pacing 和 error classification。

如果没有显式 permission state，系统可能把 delayed/frozen data 当 live data 使用，从而触发错误下单。

### 目标

IBKR market data source 可检测、可降级、可恢复，并且 permission state 对策略、risk 和 event sink 可见。

### 实施清单

```text
1. 新增 MarketDataPermissionState
   - LIVE
   - DELAYED
   - FROZEN
   - DELAYED_FROZEN
   - UNAVAILABLE

2. IbkrMarketDataAdapter 输出 market_data_type event
   - 记录 reqMarketDataType callback。
   - 记录是否使用 delayed。
   - 记录 provider permission status。

3. StreamingMarketDataSource 增加 SubscriptionBook
   - logical subscription。
   - physical subscription。
   - ibkr reqId。
   - contract spec。
   - current status。
   - last_event_ts。

4. 增加 stale data detector
   - 每个 subscription 记录 last_event_ts。
   - 超过 threshold 输出 StreamingMarketDataDegradation。
   - stale 时 risk gate 可拒绝新单。

5. 增加 reconnect resubscribe
   - reconnect 后恢复 active subscriptions。
   - subscription ack 写入 RuntimeEventSink。
   - resubscribe 失败进入 degraded。

6. 增加 pacing/backoff
   - throttle subscription requests。
   - 按 IBKR error code 做分类。
   - transient error 自动重试。
   - permission error fail-fast。
   - pacing violation 进入 backoff。

7. 增加 market data risk gate
   - live mode 下 delayed/frozen data 默认禁止触发新单。
   - 可配置 allow_delayed_data_for_observation_only。
   - stale data 时拒绝新单。

8. RuntimeEventSink 输出
   - market_data_subscribed
   - market_data_unsubscribed
   - market_data_permission_changed
   - market_data_stale_detected
   - market_data_resubscribed
   - market_data_subscription_failed

9. 新增测试
   - test_delayed_market_data_sets_permission_state
   - test_stale_data_blocks_live_orders
   - test_reconnect_resubscribes_active_subscriptions
   - test_permission_error_does_not_retry_forever
   - test_pacing_violation_enters_backoff
   - test_market_data_permission_written_to_event
```

### 完成标准

```text
1. 策略和风控永远知道自己收到的是 live、delayed 还是 frozen data。
2. stale data 不会继续触发 live 下单。
3. IBKR 断线恢复后订阅自动恢复并可审计。
```

---

## P1-6：Backtest replay source 做成真正的 broker-like market data source

### Review 项

当前 backtest 从本地文件 replay 的方向正确，但要确保它不是“读文件喂策略”，而是“按 subscription 和 time frontier 生成 market data event”。

尤其要避免 look-ahead bias：bar `[10:00, 10:01)` 的 close 只能在 `10:01` 或之后被策略看到。

### 目标

backtest replay 与 live streaming 在下游完全同构。

### 实施清单

```text
1. ReplayMarketDataSource 实现统一接口
   - subscribe(subscription)
   - unsubscribe(subscription)
   - poll_next()
   - on_event(callback)
   - close()

2. 新增 ReplayClock
   - current_time。
   - advance_to_next_event()。
   - emit_at_end_time。
   - 支持 deterministic replay。

3. 新增 ReplayEventSequencer
   - 多 instrument 多 timeframe 排序。
   - 相同 timestamp 的 deterministic tie-breaker。
   - tick/quote/bar priority。
   - 防止 out-of-order event。

4. 新增 ReplaySubscriptionBook
   - 只发送 active subscriptions。
   - 支持中途 subscribe/unsubscribe。
   - 输出 MarketDataSubscribed event。
   - 输出 MarketDataUnsubscribed event。

5. Bar emission 规则
   - bar.start/end 使用 half-open interval。
   - 策略只能在 bar.end 后收到 bar。
   - close 不可提前可见。
   - 多 timeframe bar 按可见时间排序。

6. 数据异常事件
   - replay_gap_detected。
   - replay_out_of_order_rejected。
   - replay_duplicate_dropped。
   - replay_session_filtered。
   - replay_data_schema_error。

7. provenance
   - dataset_id。
   - file path。
   - file hash。
   - row count。
   - schema version。
   - timezone。
   - adjustment mode。
   - vendor/source。

8. MarketDataFlow 统一接入
   - ReplayMarketDataSource 和 StreamingMarketDataSource 输出同一 MarketDataEvent schema。
   - 下游 StrategyExecutionPipeline 不感知模式。

9. 新增测试
   - test_bar_close_emitted_at_bar_end
   - test_unsubscribed_instrument_not_emitted
   - test_multi_instrument_deterministic_ordering
   - test_replay_gap_emits_degradation_event
   - test_backtest_and_live_market_data_event_schema_match
   - test_strategy_cannot_access_future_bar_close
   - test_mid_run_subscribe_only_emits_after_subscription
```

### 完成标准

```text
1. backtest market data 和 live market data 使用同一 event schema。
2. 策略无法读取未来数据。
3. replay 结果可复现，可定位到具体数据文件和行。
4. backtest replay 服从 subscription，而不是全量推送。
```

---

## P1-7：统一 simulated execution 和 broker execution 的能力模型

### Review 项

`SimulatedExecutionAdapter` 与 `BrokerExecutionAdapter` 分离是正确的，但 backtest 要尽可能使用和 live 相同的 brokerage capability model，否则 backtest/live 偏差会变大。

例如 live broker 不支持某个 order type，backtest 也不应该允许这个 order type 静默通过。

### 目标

backtest simulated execution 也经过 broker capability gate。

### 实施清单

```text
1. 扩展 BrokerCapabilities
   - supported_order_types
   - supported_tif
   - supports_fractional
   - supports_short
   - supports_options
   - supports_futures
   - min_tick
   - min_order_qty
   - lot_size
   - max_order_qty
   - supported_asset_classes

2. BacktestRuntimeConfig 增加 brokerage_model
   - IBKR_EQUITY
   - IBKR_FUTURES
   - IBKR_OPTIONS
   - CUSTOM

3. OrderPlanBuilder 输出前校验 instrument constraints
   - lot size。
   - min tick。
   - quantity precision。
   - price precision。
   - supported order type。
   - supported TIF。

4. SimulatedExecutionAdapter 使用 BrokerCapabilities
   - 不支持的 order type 在 backtest 也 reject。
   - TIF 不支持也 reject。
   - 数量/价格精度按 broker capability 处理。

5. Fill model 配置化
   - ImmediateFillModel。
   - NextBarOpenFillModel。
   - QuoteAwareFillModel。
   - VolumeParticipationFillModel。
   - PartialFillModel。

6. 成本模型与能力模型分离
   - capability 决定能不能下。
   - cost model 决定费用/滑点假设。
   - fill model 决定如何成交。

7. 新增测试
   - test_backtest_rejects_order_type_not_supported_by_live_broker
   - test_min_tick_rounding
   - test_lot_size_rounding
   - test_limit_order_fill_model_differs_from_market_order
   - test_fractional_quantity_rejected_when_not_supported
   - test_brokerage_model_written_to_manifest
```

### 完成标准

```text
1. backtest 不会通过 live broker 无法执行的订单。
2. broker-specific constraints 在 adapter 边界前已经可见。
3. backtest/live 偏差可以通过 capability/cost/fill model 拆解分析。
```

---

# P2 计划

P2 关注 live 安全、状态恢复、可观测性、配置版本化和数据 provenance。

---

## P2-1：live 启动安全门禁产品化

### Review 项

已有 `validate_live_startup`、`LiveStartupDecision`、`LiveReconciliation`、`KillSwitch` 等基础，但需要形成完整 checklist。live 下单前必须可证明：账户、端口、行情权限、对账、event sink、snapshot store、风控配置、operator signoff 全部通过。

### 目标

live 下单前必须满足所有安全条件；未满足时可以进入 observation，但不能提交订单。

### 实施清单

```text
1. 新增 LiveStartupChecklist
   - account_mode_check
   - port_check
   - api_read_only_check
   - market_data_permission_check
   - broker_time_check
   - open_order_reconciliation_check
   - position_reconciliation_check
   - cash_reconciliation_check
   - risk_config_check
   - kill_switch_check
   - event_sink_check
   - snapshot_store_check
   - operator_signoff_check

2. 每个 check 输出
   - check_name
   - status: PASS/WARN/FAIL
   - severity: INFO/WARN/BLOCKER
   - evidence
   - remediation

3. LiveStartupDecision 扩展
   - ALLOW_OBSERVATION
   - ALLOW_PAPER
   - ALLOW_LIVE
   - BLOCK

4. live order path 强制检查
   - startup decision 必须 ALLOW_LIVE。
   - kill switch inactive。
   - account not degraded。
   - market data not stale。
   - broker connected。
   - reconciliation valid。

5. checklist manifest
   - 每次 live/paper 启动写入 startup checklist artifact。
   - report manifest 引用 checklist hash。

6. 新增测试
   - test_live_blocks_without_operator_signoff
   - test_live_blocks_with_reconciliation_drift
   - test_live_blocks_when_event_sink_not_writable
   - test_observation_allowed_when_order_blocked
   - test_live_blocks_when_market_data_stale
   - test_checklist_written_to_manifest
```

### 完成标准

```text
1. live capital 无法绕过 checklist。
2. 每个 block 都有明确 evidence 和 remediation。
3. observation 和 live order enabled 是两个不同状态。
```

---

## P2-2：状态恢复与事件溯源增强

### Review 项

已有 `EventStore`、`FileEventStore`、`StateSnapshot`、`InMemorySnapshotStore`，但 live 需要 durable recovery，而不是仅本地测试恢复。

### 目标

runtime 可从 event store + snapshot 恢复，并在恢复后与 broker state 对账。

### 实施清单

```text
1. SnapshotStore 抽象
   - InMemorySnapshotStore
   - FileSnapshotStore
   - DurableSnapshotStore

2. Actor snapshot
   - AccountActor.snapshot()
   - OrderManagerActor.snapshot()
   - StrategyActor.snapshot() 可选
   - MarketDataSource.subscription_snapshot()
   - RiskEngine.snapshot() 可选

3. Recovery flow
   - load latest snapshot。
   - replay events after snapshot。
   - detect missing event sequence。
   - reconstruct actor state。
   - reconcile broker state。
   - mark runtime recovered。

4. EventStore 增加 sequence_no
   - 每个 run_id 单调递增。
   - detect missing sequence。
   - detect duplicate sequence。

5. Snapshot frequency policy
   - by event count。
   - by time interval。
   - on order/fill boundary。
   - on graceful shutdown。

6. Live recovery safety
   - 恢复后必须先进入 observation。
   - reconciliation 通过后才能恢复下单。
   - 恢复失败进入 BLOCK。

7. 新增测试
   - test_recover_account_from_snapshot_and_events
   - test_recover_open_orders_then_reconcile_broker
   - test_missing_event_sequence_blocks_live
   - test_duplicate_event_sequence_blocks_recovery
   - test_recovery_enters_observation_before_live
```

### 完成标准

```text
1. runtime 崩溃后能恢复内部状态。
2. 恢复后必须与 broker reconciliation 通过才能继续下单。
3. event sequence 缺口会阻止 live 下单。
```

---

## P2-3：可观测性与排障标准化

### Review 项

已有 `MetricsRegistry` 和 `AuditEvent`，但交易系统排障需要统一指标、日志、事件和 trace ID。核心要求是从 market data event 追到 strategy intent、risk decision、order、broker ack、fill 和 account mutation。

### 目标

每条链路都能按 run_id/order_id/correlation_id 直接定位。

### 实施清单

```text
1. 定义核心 metrics
   - market_data_events_total
   - market_data_stale_total
   - strategy_intents_total
   - signal_conflicts_total
   - risk_rejections_total
   - orders_submitted_total
   - broker_rejections_total
   - fills_total
   - reconciliation_drifts_total
   - kill_switch_activations_total

2. 定义 latency metrics
   - market_data_ingest_latency
   - strategy_eval_latency
   - signal_aggregation_latency
   - risk_eval_latency
   - order_manager_latency
   - broker_submit_latency
   - broker_ack_latency
   - fill_to_account_apply_latency

3. RuntimeEventSink 增加 trace 字段
   - correlation_id
   - causation_id
   - parent_event_id
   - sequence_no

4. 增加 structured log
   - no free-form critical event。
   - all logs include run_id/mode/account_id/strategy_id/order_id where applicable。
   - broker callbacks include provider callback type。

5. 新增 operational dashboard schema
   - runtime state。
   - subscriptions。
   - open orders。
   - positions。
   - cash。
   - risk status。
   - broker connection state。
   - reconciliation status。

6. error taxonomy
   - MARKET_DATA_PERMISSION_ERROR
   - MARKET_DATA_STALE
   - BROKER_DISCONNECTED
   - ORDER_REJECTED_BY_RISK
   - ORDER_REJECTED_BY_BROKER
   - EXECUTION_REPORT_UNRESOLVED
   - RECONCILIATION_DRIFT
   - EVENT_STORE_WRITE_FAILED

7. 新增测试
   - test_every_order_event_has_correlation_id
   - test_metrics_increment_on_risk_rejection
   - test_stale_market_data_event_visible_in_sink
   - test_broker_reject_has_reason_code
   - test_fill_to_account_event_linked_by_causation_id
```

### 完成标准

```text
1. 出问题时能按 run_id/order_id/correlation_id 直接定位。
2. live/paper/backtest 输出事件可以统一分析。
3. 核心异常都有标准 reason_code。
```

---

## P2-4：配置拆分与版本化

### Review 项

`qts/runtime/config.py` 如果同时承载 backtest、paper、live、risk、cost、roll、market data reference 等配置，长期会继续膨胀，并导致模式字段互相污染。

### 目标

配置模块分层、版本化、可 migration。

### 实施清单

```text
1. 拆分配置包
   qts/runtime/config/
     base.py
     backtest.py
     paper.py
     live.py
     risk.py
     cost.py
     ibkr.py
     market_data.py

2. 所有配置增加 schema_version
   - BacktestRuntimeConfig.schema_version
   - LiveRuntimeConfig.schema_version
   - PaperRuntimeConfig.schema_version
   - RiskConfig.schema_version

3. 新增 ConfigMigration
   - v1 -> v2。
   - v2 -> v3。
   - migration 输出 change log。

4. 配置 validate 分层
   - syntax validation。
   - semantic validation。
   - environment validation。
   - startup validation。

5. 输出 config hash
   - report manifest。
   - runtime event。
   - topology manifest。
   - startup checklist。

6. 禁止字段污染
   - live config 不允许出现 backtest-only dataset file path，除非是 paper_simulated replay。
   - backtest config 不允许出现 live broker credentials。
   - observation mode 不允许 allow_live_orders。

7. 新增测试
   - test_config_version_required
   - test_config_hash_stable
   - test_live_config_rejects_backtest_only_fields
   - test_backtest_config_rejects_live_broker_credentials
   - test_config_migration_v1_to_v2
```

### 完成标准

```text
1. 配置变化可审计。
2. live/backtest/paper 字段不再互相污染。
3. 历史配置可以通过 migration 明确升级。
```

---

## P2-5：数据 provenance 与 validation 强化

### Review 项

已有 `DataValidationReport`、`HistoricalDatasetValidator`、`DatasetMetadata` 等方向，但需要让每次回测和 replay 都能复现到数据版本，并把数据质量问题显式写入 report manifest。

### 目标

每个 backtest/paper/live run 都能说明数据来源、质量、权限和可见性。

### 实施清单

```text
1. Historical dataset 增加
   - dataset_id
   - vendor
   - asset_class
   - adjustment_mode
   - timezone
   - schema_version
   - file_hash
   - row_count
   - first_ts
   - last_ts
   - data_quality_score

2. ReplayMarketDataBundle 增加 provenance list
   - 支持多文件、多标的、多 timeframe。
   - 每个文件记录 hash 和 row count。

3. RuntimeEvent 中 market data event 增加
   - source_id
   - dataset_id
   - provider
   - permission_state
   - latency
   - adjustment_mode

4. DataValidationReport 增加 hard gate
   - ERROR 阻止 backtest。
   - WARNING 写 manifest。
   - INFO 仅记录。

5. 数据异常分类
   - MISSING_BAR
   - DUPLICATE_BAR
   - OUT_OF_ORDER_ROW
   - SESSION_MISMATCH
   - TIMEZONE_MISMATCH
   - PRICE_OUTLIER
   - VOLUME_OUTLIER

6. live data provenance
   - provider。
   - market data type。
   - account permission state。
   - subscription id。
   - first event timestamp。
   - last event timestamp。

7. 新增测试
   - test_backtest_manifest_contains_dataset_hash
   - test_invalid_csv_blocks_replay_when_error
   - test_warning_validation_issue_does_not_block
   - test_live_market_data_permission_written_to_manifest
   - test_replay_event_contains_dataset_id
```

### 完成标准

```text
1. 回测结果可用同一数据版本复现。
2. 数据质量问题不会静默进入策略。
3. live/paper/backtest 的 market data provenance 都可追踪。
```

---

# P3 计划

P3 是外部操作、API、CI guardrail 和长期演进治理。

---

## P3-1：统一 API / CLI runtime 操作模型

### Review 项

已有 `OperationsService`、`KillSwitchCommandDTO`、`RuntimeStateDTO`、WebSocket DTO，但需要把 runtime 控制动作规范化。外部 API/CLI 不应直接碰 actor 或 broker 细节。

### 目标

API/CLI 只发 runtime command，所有 command 都具备幂等性和审计证据。

### 实施清单

```text
1. 新增 RuntimeCommand
   - START
   - STOP
   - PAUSE
   - RESUME
   - ACTIVATE_KILL_SWITCH
   - DEACTIVATE_KILL_SWITCH
   - RECONCILE
   - SNAPSHOT
   - ENTER_OBSERVATION
   - EXIT_OBSERVATION

2. RuntimeCommandResult
   - command_id
   - idempotency_key
   - accepted_at
   - completed_at
   - result_status
   - evidence
   - failure_reason

3. CommandIdempotencyStore 扩展
   - 支持 runtime command。
   - 支持 order command。
   - 支持 cancel command。
   - 支持 reconcile command。

4. WebSocket stream 统一
   - runtime_state_changed
   - command_accepted
   - command_completed
   - risk_event
   - order_event
   - account_event
   - reconciliation_event
   - market_data_status_event

5. OperationsService 不直接触达 internals
   - 只调用 RuntimeCommandBus。
   - RuntimeCommandBus 再 route 到 runtime session。

6. 新增测试
   - test_duplicate_kill_switch_command_returns_same_result
   - test_pause_blocks_new_order_but_keeps_market_data
   - test_resume_requires_reconciliation_when_live
   - test_snapshot_command_writes_snapshot
   - test_reconcile_command_emits_result_event
```

### 完成标准

```text
1. 外部入口只依赖 application/API DTO。
2. runtime 操作具备幂等性和审计证据。
3. pause/resume/kill switch/reconcile 的语义稳定。
```

---

## P3-2：架构 guardrail 升级为 CI 必过项

### Review 项

`qts.quality.guardrails` 是很好的基础，但边界退化不能只靠人工 review。命名、依赖、共享边界、broker symbol 泄漏都应该自动化检查。

### 目标

架构退化在 CI 阶段失败。

### 实施清单

```text
1. 增加 guardrail 规则
   - StrategySdkNoRuntimeImportRule
   - RuntimeNoProviderSdkImportRule
   - DomainNoRuntimeImportRule
   - AdapterMayImportProviderSdkRule
   - TransportNoDomainMutationRule
   - SharedRuntimeNoBacktestOnlyWordingRule
   - LivePackageNoReplayClassRule
   - BrokerSymbolBoundaryRule
   - PipelineNoActorImportRule
   - ProductionNoFakeClassRule

2. 增加 import graph 测试
   - qts.domain 只能依赖 qts.core。
   - qts.strategy_sdk 不依赖 qts.execution/qts.risk internals。
   - qts.data.pipeline 不依赖 runtime actors。
   - qts.execution.adapters 可依赖 provider SDK，但 domain 不可。
   - qts.runtime 不直接依赖 IBKR SDK。

3. 增加 naming convention 测试
   - *Transport 只能在 transports/adapters boundary。
   - *Source 必须拥有 lifecycle/subscription。
   - *Pipeline 不允许拥有 mailbox。
   - *Actor 必须只通过 message mutation。
   - *Sink 不允许修改 domain state。

4. CI 集成
   - pre-commit。
   - pytest quality。
   - fail on violation。
   - 输出 violation report。

5. 新增 architecture snapshot
   - 每次 release 生成 module dependency graph。
   - graph 写入 artifact。
   - 与上次 release 对比新增依赖。

6. 新增测试
   - test_no_replay_classes_in_live_package
   - test_no_provider_sdk_import_in_domain
   - test_strategy_sdk_has_no_execution_adapter_import
   - test_pipeline_has_no_actor_import
   - test_guardrail_report_contains_remediation
```

### 完成标准

```text
1. 边界不是靠人记忆维护，而是自动检查。
2. 新增模块时能及时发现架构污染。
3. CI 能输出可操作的 remediation。
```

---

# 2. 推荐最终目录结构

```text
qts/
  core/
    ids.py
    time.py

  domain/
    market_data/
    orders/
    instruments/
    risk/

  registry/
    instruments.py
    calendars.py
    broker_symbol_mapping.py
    future_roll.py
    option_chain_registry.py

  data/
    interfaces.py
    subscriptions.py
    provenance.py
    sources/
      replay_market_data_source.py
      streaming_market_data_source.py
    adapters/
      ibkr_market_data_adapter.py
      simulated_market_data_adapter.py
    transports/
      ibkr_tws_market_data_transport.py
      ib_async_market_data_transport.py
    pipelines/
      market_data_pipeline.py
      bar_aggregation_pipeline.py
    historical/

  strategy_sdk/
    strategy.py
    context.py
    target.py
    portfolio_view.py
    data_view.py

  runtime/
    mode.py
    topology.py
    session.py
    signal_policy.py
    market_data_flow.py
    strategy_execution_pipeline.py
    intent_processing.py
    execution_report_handler.py
    event_store.py
    state_recovery.py
    actors/
    sinks/
    config/
      base.py
      backtest.py
      paper.py
      live.py
      risk.py
      cost.py
      ibkr.py
      market_data.py

  risk/
    risk_engine.py
    rules/
    kill_switch.py

  execution/
    broker.py
    order_manager.py
    order_state_machine.py
    idempotency.py
    adapters/
      broker_execution_adapter.py
      ibkr_order_execution_adapter.py
      simulated_execution_adapter.py
    transports/
      ibkr_tws_order_execution_transport.py
      ib_async_order_execution_transport.py
    simulator/

  portfolio/
    accounting/
    cash_book.py
    position_book.py
    reservation_book.py

  reconciliation/
    engine.py
    snapshots.py
    startup_gate.py

  reporting/
    base.py
    backtest.py
    live.py

  application/
  api/
  quality/
  testing/
```

---

# 3. 建议里程碑

## Milestone 1：语义与事件合同稳定

包含：

```text
P0-1 RuntimeMode
P0-2 naming guardrail
P0-3 RuntimeRunId / RuntimeEvent
P0-4 docstring wording cleanup
```

验收：

```text
1. backtest/paper/live 都能输出同一 RuntimeEvent envelope。
2. paper_broker 和 paper_simulated 语义明确。
3. CI 能阻止 replay/fake/live 命名混用。
```

## Milestone 2：多策略多账户与 signal aggregation

包含：

```text
P1-1 RuntimeTopology
P1-2 SignalAggregatorActor policy
P1-3 AccountRuntimePartition
```

验收：

```text
1. 两策略一账户、一策略两账户、两策略两账户均可启动并有 topology manifest。
2. 冲突信号行为确定并有 runtime event。
3. fill 不会跨账户入账。
```

## Milestone 3：IBKR paper/live 可靠性

包含：

```text
P1-4 IBKR order execution reliability
P1-5 IBKR market data reliability
P2-1 live startup checklist
```

验收：

```text
1. IBKR reconnect 后能恢复订阅、open orders、positions。
2. duplicate callbacks 不重复入账。
3. delayed/stale data 不会触发 live order。
4. live order path 必须通过 startup checklist。
```

## Milestone 4：Backtest/live parity 与复现

包含：

```text
P1-6 broker-like replay source
P1-7 broker capability model
P2-5 data provenance
```

验收：

```text
1. replay 服从 subscription。
2. bar close 不可提前可见。
3. backtest 也应用 live broker capability constraints。
4. report manifest 含 dataset hash 和 brokerage model。
```

## Milestone 5：生产运维闭环

包含：

```text
P2-2 recovery
P2-3 observability
P2-4 config versioning
P3-1 runtime command model
P3-2 CI guardrail
```

验收：

```text
1. runtime 崩溃后可从 snapshot + event store 恢复。
2. 任何 order/fill/account mutation 可按 correlation_id 追踪。
3. API/CLI runtime command 幂等。
4. 架构边界退化会在 CI 失败。
```

---

# 4. 优先级建议

建议按下面顺序执行：

```text
1. P0-1 RuntimeMode 与 paper 语义拆分。
2. P0-2 命名词典与 guardrail。
3. P0-3 RuntimeRunId 与 RuntimeEvent envelope。
4. P1-1 RuntimeTopology。
5. P1-3 AccountRuntimePartition。
6. P1-2 SignalAggregatorActor policy。
7. P1-6 Backtest replay broker-like source。
8. P1-4 IBKR order execution reliability。
9. P1-5 IBKR market data reliability。
10. P2-1 live startup checklist。
11. P1-7 broker capability model。
12. P2-2 recovery。
13. P2-3 observability。
14. P2-4 config versioning。
15. P2-5 data provenance。
16. P3-1 runtime command model。
17. P3-2 CI guardrail 升级。
```

---

# 5. 最小可落地版本

如果希望尽快落一个 MVP，建议先实现以下 6 个 PR：

```text
PR-1: RuntimeMode + mode/account/port/signoff validation
PR-2: RuntimeRunId + RuntimeEvent envelope unification
PR-3: data naming cleanup + qts.quality guardrail
PR-4: RuntimeTopology + account/strategy route validation
PR-5: ReplayMarketDataSource subscription-driven replay
PR-6: IBKR order callback idempotency + startup reconciliation skeleton
```

MVP 完成后，系统至少可以达到：

```text
1. backtest/paper/live 共享核心路径。
2. paper/live 不会因 paper 语义模糊造成安全问题。
3. 多策略、多账户 route 显式可审计。
4. backtest replay 不再绕过 market data subscription。
5. IBKR paper/live callback 不会重复入账。
6. 每个 run 的事件和 report 可被统一分析。
```
