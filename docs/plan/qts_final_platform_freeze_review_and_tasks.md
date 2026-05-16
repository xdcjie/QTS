# QTS 最终平台冻结 Review 与收尾任务计划

> 目标：判断上一轮演进完成后是否可以把交易系统工程视为“平台最终状态”，并把后续时间主要投入策略 / 因子研究。  
> 结论：可以进入“最终平台冻结冲刺”，但还不应直接宣称最终完成。剩余工作不应继续扩展架构，而应只做：命名冻结、验收证据、live-capital 硬门禁、IBKR failure drill、复杂度收敛和策略研究交接。

---

## 0. 总体判断

### 0.1 当前状态判断

当前架构已经具备成为最终平台基线的条件：

- Backtest / Paper / Live 共用核心职责链。
- Backtest 使用 `ReplayMarketDataSource` + `SimulatedExecutionAdapter`。
- Paper / Live 使用 `StreamingMarketDataSource` + `BrokerExecutionAdapter`。
- 策略、风控、订单、账户、reporting 已经走统一 runtime path。
- IBKR market-data / order execution 边界已经拆出 transport、adapter、callback、order id 等结构。
- Paper broker 已有外部证据覆盖 market-data、submit/cancel、tiny fill、manifest、账户对账。
- Guardrail、RuntimeSession complexity rule、RuntimeCoordinator decision rule 已经出现，说明架构退化防线已经有雏形。

但它还不是严格意义上的“工程最终状态”，原因是：

1. 仍存在少量 `Live*` 命名残留，和 broker-capable runtime 的实际语义不完全一致。
2. `LiveRuntimeConfig` / `PaperBrokerRuntimeConfig` / `PaperSimulatedRuntimeConfig` 的配置边界还有最后一次简化空间。
3. `LiveRuntimeEventSink`、`LiveOrderPermission`、`LiveReconciliation`、`LiveRecoveryDecision` 这类名称会在 paper broker、live observation、live capital 三种场景中持续制造语义噪音。
4. Live capital 仍然需要硬门禁、operator signoff、reconnect 后 reconciliation、market-data freshness/permission risk rule、IBKR callback 幂等和乱序测试全部通过。
5. 当前类数量和 coordinator 数量已经不低，必须做一次复杂度预算和 keep / merge / delete 审计，防止后续策略开发时平台继续膨胀。

### 0.2 最终状态定义

完成本计划后，可以把系统定义为：

```text
QTS Platform Final Baseline v1

支持范围：
- Backtest：可正式用于策略评估。
- Paper simulated：可用于 CI、本地 smoke test、策略链路验证。
- IBKR Paper broker：可受控运行，用于 broker-path 验证。
- Live observation：可运行，不允许真实资金下单。
- Live capital：默认禁用；只有通过 live-capital enablement checklist 后才允许开启。

后续重心：
- 策略研究
- 因子研究
- 数据质量
- 组合构建
- 回测实验管理

平台工程只允许：
- bug fix
- broker failure drill 补证据
- guardrail 维护
- 新策略需要的最小公共接口扩展
```

### 0.3 不应再继续做的架构扩展

除非有真实生产需求，不建议再做：

- 分布式 actor / 多进程 runtime。
- Kafka / event bus 外部化。
- 多 broker 大规模抽象。
- 复杂 OMS / EMS 独立服务拆分。
- 在 runtime 内加入复杂 portfolio optimizer。
- 为未来未知需求继续增加 DTO / Protocol / Coordinator。
- 重新设计 backtest / paper / live 统一链路。

---

## 1. 最终可用性结论

| 模式 | 当前是否可用 | 这轮完成后状态 | 说明 |
|---|---:|---:|---|
| Backtest | 可以 | 最终可用 | 需补齐 deterministic / no-lookahead / golden regression suite。 |
| Paper simulated | 可以 | 最终可用 | 作为 CI 和本地策略 smoke test。 |
| IBKR Paper broker | 可以受控运行 | 最终可用 | 需补齐 paper acceptance suite 和 IBKR failure drill。 |
| Live observation | 可以 | 最终可用 | 只观察行情、账户、事件、reconciliation，不允许真实下单。 |
| Live capital | 不建议直接开启 | 条件性可开启 | 必须完成 M3 / M4 的全部 hard gate 和人工签核。 |

---

# Milestone M0：最终平台冻结与范围声明

## Task M0.1：定义 `QTS Platform Final Baseline v1`

### 目标

把“最终状态”写成可执行、可验收的边界，而不是继续开放式演进。

### 实施步骤

1. 新增文档：

```text
docs/architecture/platform_final_baseline_v1.md
```

2. 文档必须明确：

```text
- 支持哪些 RuntimeMode。
- 哪些模式允许下单。
- 哪些模式只允许 observation。
- live capital 默认禁用。
- 平台工程冻结后，哪些修改允许，哪些修改禁止。
- 策略 / 因子研究允许依赖的稳定 API。
```

3. 明确 platform final baseline 的版本字段：

```python
PLATFORM_BASELINE_VERSION = "qts-platform-v1"
```

4. 将该版本写入：

```text
- Backtest report manifest
- Broker runtime report manifest
- RuntimeEvent envelope
- Startup checklist evidence
```

### 验收条件

- `docs/architecture/platform_final_baseline_v1.md` 存在。
- 每次 backtest / paper / live-observation run 的 manifest 都包含 `platform_baseline_version`。
- 新增测试：

```text
test_backtest_manifest_contains_platform_baseline_version
test_broker_runtime_manifest_contains_platform_baseline_version
test_runtime_event_contains_platform_baseline_version
```

---

## Task M0.2：建立“平台冻结后禁止新增架构层”的 guardrail

### 目标

防止后续策略研究过程中，平台代码继续因为临时需求膨胀。

### 实施步骤

1. 新增 guardrail：

```python
PlatformFreezeRule
```

2. 默认禁止在以下包中新增 production class，除非提交 exception file：

```text
qts.runtime
qts.execution.adapters
qts.execution.transports
qts.data.sources
qts.data.adapters
qts.data.transports
qts.reconciliation
```

3. 新增例外文件：

```text
docs/architecture/platform_freeze_exceptions.yaml
```

格式：

```yaml
exceptions:
  - class_name: NewClassName
    module: qts.runtime.xxx
    reason: "why this is required"
    owner: "engineering"
    expiry: "2026-06-30"
```

4. CI 中运行：

```bash
pytest tests/quality/test_platform_freeze.py
```

### 验收条件

- 无 exception 时，在核心平台包新增 class 会导致 CI fail。
- exception 过期会导致 CI fail。
- 策略 / 因子包不受该规则限制。

---

## Task M0.3：冻结 strategy / factor 研究可依赖 API

### 目标

让后续策略和因子研究不需要理解 runtime、broker、actor、risk internals。

### 实施步骤

1. 新增文档：

```text
docs/research/strategy_factor_api_v1.md
```

2. 明确稳定 API：

```text
qts.strategy_sdk.Strategy
qts.strategy_sdk.StrategyContext
qts.strategy_sdk.TargetIntentEmitter
qts.factors.*
BacktestService.submit()
StartRuntimeCommand for paper/live observation
Report manifest schema
Backtest artifact schema
```

3. 明确禁止策略直接 import：

```text
qts.runtime.*
qts.execution.*
qts.reconciliation.*
qts.portfolio.account_actor internals
qts.data.transports.*
qts.execution.transports.*
```

4. 扩展已有 `StrategySdkPublicSurfaceRule`，确保策略示例和策略包不能触达 internal runtime/broker/risk symbols。

### 验收条件

- 策略代码只依赖 SDK / factors / domain view。
- 新增测试：

```text
test_strategy_package_cannot_import_runtime_internals
test_strategy_package_cannot_import_broker_transports
test_factor_package_has_no_runtime_dependency
```

---

# Milestone M1：最终命名冻结与配置收敛

## Task M1.1：将 `LiveRuntimeConfig` 改为 `BrokerRuntimeConfig`

### 当前问题

`LiveRuntimeConfig` 实际描述的是 broker-capable runtime 的启动和安全配置，不只适用于 live capital。它也服务于 IBKR paper broker 和 live observation。

### 目标

消除 live / paper broker / live observation 的语义混淆。

### 实施步骤

1. 重命名：

```text
LiveRuntimeConfig -> BrokerRuntimeConfig
```

2. 更新文件：

```text
qts/runtime/config/models.py
```

3. 修改 docstring：

```text
Startup and safety configuration for broker-capable runtime modes.
```

4. 替换字段和方法中的 wording：

```text
live runtime config -> broker runtime config
validate live runtime mode label -> validate broker runtime mode contract
live runtime config hash -> broker runtime config hash
```

5. 如果现有 YAML / API 仍使用旧字段，提供一次性 migration：

```python
ConfigMigration(v_old="live_runtime", v_new="broker_runtime")
```

6. 删除旧 alias，或者仅保留一个 release 的 deprecated alias，并由 guardrail 禁止新增引用。

### 验收条件

- production code 中不再出现 `LiveRuntimeConfig`。
- `BrokerRuntimeConfig` 同时支持：

```text
RuntimeMode.PAPER_BROKER
RuntimeMode.LIVE_OBSERVATION
RuntimeMode.LIVE
```

- 新增测试：

```text
test_broker_runtime_config_accepts_paper_broker_mode
test_broker_runtime_config_accepts_live_observation_mode
test_broker_runtime_config_requires_live_order_permission_for_live_mode
test_no_new_import_of_live_runtime_config
```

---

## Task M1.2：合并或降级 `PaperBrokerRuntimeConfig`

### 当前问题

当前同时存在：

```text
Broker-capable config：LiveRuntimeConfig / 待改 BrokerRuntimeConfig
Paper-specific config：PaperBrokerRuntimeConfig
Paper simulated config：PaperSimulatedRuntimeConfig
```

其中 `PaperBrokerRuntimeConfig` 如果只是 mode default / account default，会成为重复配置层。

### 目标

把 paper broker 表达为 `BrokerRuntimeConfig(mode=PAPER_BROKER)`，而不是第二套 broker 配置。

### 实施步骤

1. 审计 `PaperBrokerRuntimeConfig` 字段。

2. 如果只包含 paper 默认值，删除 class，改为：

```python
BrokerRuntimeConfig.for_paper_broker(...)
```

3. 如果确实需要保留 paper-specific policy，则改名为：

```text
PaperBrokerRuntimeProfile
```

并确保它不是完整 config，只是 profile / defaults。

4. 保留：

```text
PaperSimulatedRuntimeConfig
```

因为它走本地 simulated execution，不是 broker-capable config。

### 验收条件

- paper broker 不再有独立完整 runtime config。
- paper simulated 仍然有独立 config。
- 新增测试：

```text
test_paper_broker_uses_broker_runtime_config
test_paper_simulated_does_not_construct_broker_transport
test_paper_broker_profile_cannot_enable_live_orders
```

---

## Task M1.3：将 `LiveRuntimeEventSink` 改为 `BrokerRuntimeEventSink`

### 当前问题

`LiveRuntimeEventSink` 的职责是写 paper/live broker runtime 事件，不只 live。

### 目标

命名和实际用途一致。

### 实施步骤

1. 重命名 class：

```text
LiveRuntimeEventSink -> BrokerRuntimeEventSink
```

2. 重命名文件：

```text
qts/runtime/sinks/live.py -> qts/runtime/sinks/broker_runtime.py
```

3. 更新调用链：

```text
RuntimeSession -> RuntimeEventContext -> BrokerRuntimeEventSink
```

4. 更新 reporting：

```text
BrokerRuntimeEventSink -> BrokerRuntimeReportWriter
```

5. 增加 compatibility import guard：旧路径只允许在 migration 测试中使用。

### 验收条件

- production code 不再引用 `LiveRuntimeEventSink`。
- 文件路径不再是 `qts/runtime/sinks/live.py`。
- 新增测试：

```text
test_broker_runtime_event_sink_writes_paper_events
test_broker_runtime_event_sink_writes_live_observation_events
test_removed_live_event_sink_import_fails_guardrail
```

---

## Task M1.4：将 `LiveOrderPermission` 改为 `OrderSubmissionPermission`

### 当前问题

`LiveOrderPermission` 实际表达的是 broker-capable runtime 的下单权限，包括 observation、paper order、live order。

### 目标

将权限命名从 live-specific 改成 order-submission-specific。

### 实施步骤

1. 重命名：

```text
LiveOrderPermission -> OrderSubmissionPermission
```

2. 推荐枚举值：

```python
class OrderSubmissionPermission(Enum):
    OBSERVATION_ONLY = "observation_only"
    PAPER_ORDERS_ALLOWED = "paper_orders_allowed"
    LIVE_ORDERS_ALLOWED = "live_orders_allowed"
```

3. 保留方法：

```python
allows_order_submission
allows_live_orders
```

4. 修改所有 risk gate / startup gate / manifest 字段名：

```text
live_order_permission -> order_submission_permission
```

### 验收条件

- production code 不再引用 `LiveOrderPermission`。
- `OBSERVATION_ONLY` 必须阻断 broker order submission。
- `PAPER_ORDERS_ALLOWED` 不允许 live capital。
- `LIVE_ORDERS_ALLOWED` 只在 live signoff 后允许。
- 新增测试：

```text
test_observation_only_blocks_all_broker_orders
test_paper_orders_allowed_blocks_live_capital
test_live_orders_allowed_requires_operator_signoff
test_order_submission_permission_serialized_in_manifest
```

---

## Task M1.5：将 `LiveReconciliation` / `LiveRecoveryDecision` 改为 broker/runtime 通用命名

### 当前问题

当前 reconciliation 和 recovery 实际用于 paper/live broker runtime，但 class 名仍带 `Live`。

### 目标

减少 paper broker / live observation / live capital 的概念混淆。

### 实施步骤

重命名：

```text
LiveReconciliation -> BrokerRuntimeReconciliation
LiveReconciliationResult -> BrokerRuntimeReconciliationResult
qts/runtime/live_reconciliation.py -> qts/runtime/broker_runtime_reconciliation.py

LiveRecoveryDecisionStatus -> RuntimeRecoveryDecisionStatus
LiveRecoveryDecision -> RuntimeRecoveryDecision
```

同步更新：

```text
Startup checklist
RuntimeRecoveryCoordinator
BrokerRuntimeStartupGate
Manifest payload
RuntimeEvent payload
```

### 验收条件

- production code 中不再出现 `LiveReconciliation` / `LiveRecoveryDecision`。
- recovery decision 可用于 paper broker、live observation、live capital 三种模式。
- 新增测试：

```text
test_broker_runtime_reconciliation_blocks_order_submission_on_drift
test_runtime_recovery_decision_serializes_to_manifest
test_runtime_recovery_decision_emits_runtime_event
test_removed_live_reconciliation_names_fail_guardrail
```

---

## Task M1.6：处理 `RiskConfig` 重名 / 重复概念

### 当前问题

`qts/runtime/config/models.py` 中存在 `RiskConfig`，风险模块也可能有自己的 risk config。最终平台状态不应有两个同名、边界不同的配置概念。

### 目标

让 risk config 的归属清楚：runtime config 负责引用，risk package 负责风险规则定义。

### 实施步骤

方案 A：如果 runtime 中的 `RiskConfig` 只服务 backtest：

```text
RiskConfig -> BacktestRiskConfig
```

方案 B：如果它是全模式共享：

```text
迁移到 qts/risk/config.py
runtime/config/models.py 只引用 RiskProfileRef 或 RiskConfigRef
```

推荐最终结构：

```text
qts/risk/config.py
  RiskProfileConfig
  RiskRuleConfig

qts/runtime/config/models.py
  risk_profile_id: str
  risk_profile_ref: RiskProfileRef
```

### 验收条件

- 不再存在两个含义不同的 `RiskConfig`。
- backtest / paper / live 使用同一 risk profile schema。
- 新增测试：

```text
test_backtest_runtime_config_references_risk_profile
test_broker_runtime_config_references_risk_profile
test_risk_profile_builds_market_data_permission_rule
test_risk_profile_builds_market_data_freshness_rule
```

---

# Milestone M2：Backtest / Paper / Live Observation 最终验收套件

## Task M2.1：Backtest deterministic golden suite

### 目标

让 backtest 成为策略研究可信入口。

### 实施步骤

1. 准备最小 deterministic dataset：

```text
tests/fixtures/market_data/golden_bars/*.parquet or *.csv
```

2. 固定策略：

```text
ReferenceMomentumStrategy
ReferenceMeanReversionStrategy
NoTradeStrategy
```

3. 固定 expected outputs：

```text
expected_orders.ndjson
expected_fills.ndjson
expected_equity_curve.ndjson
expected_manifest.json
```

4. 验证：

```text
- 相同输入重复运行，artifact hash 一致。
- bar close 只能在 bar.end 后可见。
- strategy context 不可访问未来数据。
- 多 instrument 同 timestamp 排序确定。
- subscription mid-run 只收到 subscribe 后的数据。
- replay gap 会进入 diagnostic event，不可静默跳过。
```

### 验收条件

新增测试：

```text
test_backtest_golden_run_is_deterministic
test_bar_close_visible_only_at_bar_end
test_strategy_context_cannot_see_future_bar
test_multi_instrument_same_timestamp_order_is_stable
test_replay_gap_emits_diagnostic_event
test_backtest_manifest_contains_dataset_provenance_and_config_hash
```

全部通过后，Backtest 标记为：

```text
BACKTEST_RESEARCH_READY = true
```

---

## Task M2.2：Paper simulated final smoke suite

### 目标

让本地模拟 paper 成为 CI 中最便宜的完整链路测试。

### 实施步骤

1. 使用 `PaperSimulatedRuntimeConfig` 启动完整链路。
2. 使用 fake market data，但 fake 必须位于：

```text
qts.testing.fakes
```

3. 验证：

```text
- market data -> strategy -> intent -> risk -> order -> simulated fill -> account -> event sink -> report
- 禁止构造 IBKR transport
- 禁止真实 broker credential
- event envelope 和 broker runtime sink schema 一致
```

### 验收条件

新增测试：

```text
test_paper_simulated_full_chain_generates_fill_and_account_update
test_paper_simulated_never_constructs_ibkr_transport
test_paper_simulated_runtime_event_schema_matches_broker_runtime_schema
test_paper_simulated_manifest_contains_platform_baseline_version
```

全部通过后，Paper simulated 标记为：

```text
PAPER_SIMULATED_READY = true
```

---

## Task M2.3：IBKR Paper broker acceptance suite

### 目标

证明 IBKR paper broker 链路可以受控运行。

### 实施步骤

1. 准备最小 paper acceptance script：

```text
scripts/acceptance/ibkr_paper_smoke.py
```

2. 覆盖：

```text
- connect paper gateway
- verify DU account
- subscribe market data
- receive normalized event
- place tiny order or dry-run order if instrument not tradable
- cancel order
- receive orderStatus / openOrder / execDetails if filled
- reconcile account / position / open orders
- write broker runtime manifest
```

3. 所有 broker identifiers 写入 evidence，不泄漏到 strategy SDK。

### 验收条件

输出：

```text
artifacts/acceptance/ibkr_paper/<run_id>/manifest.json
artifacts/acceptance/ibkr_paper/<run_id>/events.ndjson
artifacts/acceptance/ibkr_paper/<run_id>/reconciliation.json
```

新增测试或 acceptance check：

```text
test_ibkr_paper_acceptance_manifest_has_market_data_anchor
test_ibkr_paper_acceptance_manifest_has_submit_cancel_evidence
test_ibkr_paper_acceptance_manifest_has_reconciliation_evidence
test_ibkr_paper_rejects_live_account_code
test_ibkr_paper_requires_paper_order_permission
```

全部通过后，IBKR Paper broker 标记为：

```text
IBKR_PAPER_BROKER_READY = true
```

---

## Task M2.4：Live observation acceptance suite

### 目标

允许连接 live broker / live market data，但确保无法真实下单。

### 实施步骤

1. 启动：

```text
RuntimeMode.LIVE_OBSERVATION
OrderSubmissionPermission.OBSERVATION_ONLY
```

2. 验证：

```text
- 可连接 live market data。
- 可读取 account / position snapshot。
- 可运行 reconciliation。
- 可写 event sink / manifest。
- 任何 order submission 都被 RuntimeSafetyController 或 RiskEngine 阻断。
```

3. live observation manifest 必须明确：

```json
{
  "runtime_mode": "live_observation",
  "order_submission_permission": "observation_only",
  "live_orders_allowed": false
}
```

### 验收条件

新增测试：

```text
test_live_observation_accepts_market_data
test_live_observation_writes_account_snapshot
test_live_observation_blocks_submit_order
test_live_observation_manifest_marks_live_orders_allowed_false
```

全部通过后，Live observation 标记为：

```text
LIVE_OBSERVATION_READY = true
```

---

# Milestone M3：Live Capital 硬门禁

> 该里程碑不是为了马上开启 live capital，而是为了保证未来开启时不需要再重构平台。

## Task M3.1：在最靠近执行边界的位置强制 live order gate

### 目标

即使 RuntimeSession、API 或上游风控出现漏检，真实下单也必须在执行边界前被阻断。

### 实施步骤

在以下位置全部检查：

```text
RuntimeSafetyController
TargetIntentProcessor / RiskEngine
OrderManagerActor
ExecutionActor
BrokerExecutionAdapter
IbkrOrderExecutionAdapter
```

最小强制条件：

```text
runtime_mode == LIVE
order_submission_permission == LIVE_ORDERS_ALLOWED
startup_decision == ALLOW_LIVE
operator_signoff.valid == true
market_data_permission == LIVE
market_data_freshness == FRESH
reconciliation_status == CLEAN
kill_switch == INACTIVE
broker_account_kind == LIVE
ibkr_account_code startswith U
ibkr_port == 4001 unless explicit approved override
```

### 验收条件

新增测试：

```text
test_live_order_blocked_without_live_order_permission
test_live_order_blocked_without_operator_signoff
test_live_order_blocked_when_reconciliation_not_clean
test_live_order_blocked_when_market_data_delayed
test_live_order_blocked_when_market_data_stale
test_live_order_blocked_when_kill_switch_active
test_live_order_blocked_when_account_code_is_du
test_live_order_blocked_when_gateway_port_is_paper
```

---

## Task M3.2：Operator signoff 和 dual-control

### 目标

live capital 不能由配置文件或单个 API call 静默打开。

### 实施步骤

1. 新增：

```python
OperatorSignoff
LiveCapitalEnablementRequest
LiveCapitalEnablementDecision
```

2. 最低字段：

```text
operator_id
reason
risk_approver_id
engineering_approver_id
expires_at
strategy_ids
account_ids
max_notional_limit
allowed_instruments
```

3. signoff 写入：

```text
RuntimeEvent
BrokerRuntimeReportManifest
Startup checklist evidence
```

4. signoff 过期后自动降级到 observation-only。

### 验收条件

新增测试：

```text
test_live_capital_requires_operator_and_risk_signoff
test_expired_signoff_blocks_live_orders
test_signoff_scope_blocks_unapproved_strategy
test_signoff_scope_blocks_unapproved_account
test_signoff_evidence_written_to_manifest_and_runtime_event
```

---

## Task M3.3：Kill switch drill 必须成为 live-capital 前置条件

### 目标

证明 kill switch 可以在运行中阻断新单，并且不可被低权限恢复。

### 实施步骤

1. 新增 live-capital readiness drill：

```text
scripts/drills/kill_switch_drill.py
```

2. Drill 步骤：

```text
- start broker runtime in paper broker mode
- submit allowed paper order or dry-run order
- activate kill switch
- attempt new order -> must reject
- attempt cancel open order -> should be allowed if cancellation is safety action
- attempt deactivate with low privilege -> reject
- deactivate with authorized signoff -> allow
- write evidence
```

### 验收条件

输出：

```text
artifacts/drills/kill_switch/<run_id>/evidence.json
```

新增测试：

```text
test_kill_switch_blocks_new_orders
test_kill_switch_allows_safety_cancel
test_kill_switch_deactivation_requires_authorized_signoff
test_kill_switch_drill_evidence_required_for_live_capital
```

---

# Milestone M4：IBKR failure drill 与订单可靠性最终验收

## Task M4.1：IBKR callback 幂等和乱序验收

### 目标

IBKR 的 `orderStatus`、`openOrder`、`execDetails`、`commissionReport` 乱序或重复时不会造成重复入账、错误状态推进或跨账户污染。

### 实施步骤

构造 callback 序列：

```text
1. duplicate orderStatus
2. execDetails before openOrder
3. commissionReport after fill
4. partial fills with same exec_id duplicated
5. openOrder for unknown internal order
6. callback account code mismatches route account
7. callback permId missing
8. reconnect produces old openOrder again
```

期望行为：

```text
- duplicate -> idempotent drop
- unknown -> quarantine
- account mismatch -> quarantine
- late commission -> update cost, no second fill apply
- reconnect replay -> reconcile, no duplicate order creation
```

### 验收条件

新增测试：

```text
test_duplicate_order_status_is_idempotent
test_execution_before_open_order_is_quarantined_or_later_resolved
test_late_commission_updates_cost_without_duplicate_fill
test_duplicate_exec_id_applied_once
test_open_order_unknown_internal_order_quarantined
test_callback_account_mismatch_quarantined
test_reconnect_open_order_replay_is_idempotent
```

---

## Task M4.2：Reconnect 后必须重新 reconciliation 才能恢复下单

### 目标

断线恢复后不能直接继续下单。

### 实施步骤

1. 在 broker disconnect：

```text
runtime_state = DEGRADED
order_submission_permission_effective = OBSERVATION_ONLY
```

2. 在 reconnect：

```text
- resubscribe market data
- reqOpenOrders
- reqPositions
- reqAccountSummary
- reqExecutions since last watermark
- run BrokerRuntimeReconciliation
```

3. 只有 reconciliation clean 才允许恢复 paper/live order submission。

### 验收条件

新增测试：

```text
test_disconnect_degrades_runtime_and_blocks_new_orders
test_reconnect_does_not_resume_orders_before_reconciliation
test_reconnect_resubscribes_market_data
test_reconnect_reconciles_open_orders_positions_cash
test_reconnect_with_drift_stays_degraded
```

---

## Task M4.3：Market-data permission / freshness risk rule 最终验收

### 目标

已存在的 `MarketDataPermissionRiskRule` 和 `MarketDataFreshnessRiskRule` 必须证明会阻断 live-capable orders。

### 实施步骤

1. 构造 market-data states：

```text
LIVE
DELAYED
FROZEN
DELAYED_FROZEN
UNAVAILABLE
STALE
```

2. 在每个状态下生成 strategy intent。
3. 验证 risk decision 和 runtime event。

### 验收条件

新增测试：

```text
test_live_market_data_permission_allows_order_when_fresh
test_delayed_market_data_rejects_live_order
test_frozen_market_data_rejects_live_order
test_unavailable_market_data_rejects_order
test_stale_market_data_rejects_order
test_market_data_rejection_emits_runtime_event_with_reason_code
```

---

# Milestone M5：复杂度收敛、去冗余、避免过度设计

## Task M5.1：RuntimeSession facade 复杂度预算

### 目标

`RuntimeSession` 保持 facade，不变成 God Object。

### 实施步骤

1. 明确预算：

```text
RuntimeSession public methods <= 14
RuntimeSession non-dunder private methods <= 8
RuntimeSession direct business decision branches <= 10
RuntimeSession file length <= 350 lines
RuntimeSession 不直接实现 broker callback / reconciliation / risk rule / order state transition
```

2. `RuntimeSession` 只允许：

```text
start
stop
pause
resume
degrade
recover
on_broker_disconnect
on_broker_reconnect
on_market_data_source_event
on_market_data
activate_kill_switch
deactivate_kill_switch
rollback
snapshot/status properties
```

3. 超过预算时，不新增 coordinator，优先把逻辑移到已有 owner：

```text
RuntimeMarketDataCoordinator
RuntimeBrokerLifecycleCoordinator
RuntimeSafetyController
RuntimeRecoveryCoordinator
RuntimeRollbackCoordinator
RiskEngine
OrderManagerActor
ExecutionActor
```

### 验收条件

- `RuntimeSessionComplexityRule` 在 CI hard gate 中运行。
- CI 输出 RuntimeSession complexity report。
- 新增测试：

```text
test_runtime_session_complexity_budget_passes
test_runtime_session_does_not_import_ibkr_transport
test_runtime_session_does_not_apply_account_mutation_directly
```

---

## Task M5.2：Coordinator keep / merge / delete 审计

### 目标

避免薄 coordinator 变成 ceremony。

### 实施步骤

对以下类建立决策表：

```text
RuntimeRecoveryCoordinator
RuntimeRollbackCoordinator
RuntimeBrokerLifecycleCoordinator
RuntimeMarketDataCoordinator
RuntimeSafetyController
BrokerRuntimeStartupGate
BrokerRuntimeTopologyResolver
```

每个类必须有结论：

```text
KEEP：拥有状态、策略或证据生成。
MERGE：只是 1-2 行透传，合并回 caller 或 owner。
DELETE：没有生产引用。
```

文档：

```text
docs/architecture/runtime_coordinator_decisions.md
```

### 验收条件

- 每个 coordinator 有 keep / merge / delete 决策。
- `RuntimeCoordinatorDecisionRule` 在 CI 中强制检查。
- 新增测试：

```text
test_every_runtime_coordinator_has_decision_record
test_deleted_coordinator_has_no_production_import
test_kept_coordinator_has_state_policy_or_evidence_responsibility
```

---

## Task M5.3：类数量和 DTO / ValueObject 预算

### 目标

让平台不再继续类膨胀。

### 实施步骤

1. 生成 class inventory：

```bash
python scripts/update_project_panorama_source_index.py
```

2. 建立预算：

```text
production class count baseline = 当前最终冻结时数量
新增 production class 必须有 freeze exception
DTO / ValueObject 只允许在跨边界时存在
单文件 class 数量超过 12 需要拆分或解释
```

3. 找出只包装一个字段、没有边界价值的 DTO / ValueObject。
4. 合并纯 pass-through 类型。

### 验收条件

- 生成 `artifacts/quality/class_inventory_baseline.json`。
- 新增测试：

```text
test_class_inventory_does_not_exceed_platform_baseline_without_exception
test_single_field_dto_requires_boundary_justification
test_no_duplicate_dto_names_across_application_and_runtime
```

---

## Task M5.4：删除旧 alias、旧路径和过期文档缓存

### 目标

避免 reviewer 看到旧名称或旧路径，从而怀疑当前实现状态。

### 实施步骤

1. 删除或 fail guardrail：

```text
LiveRuntimeConfig alias
LiveRuntimeEventSink alias
LiveOrderPermission alias
LiveReconciliation alias
LiveRecoveryDecision alias
qts/runtime/sinks/live.py old path
qts/reporting/live.py old path if broker_runtime.py has replaced it
```

2. 更新 panorama/source index 生成器，只读取当前源码路径。
3. 删除旧 HTML / 旧 source inventory 缓存，或标记为 archived。

### 验收条件

- 最新 panorama 中不再出现旧 alias。
- 旧路径 import 会 fail。
- 新增测试：

```text
test_removed_live_alias_imports_fail
test_panorama_source_index_uses_current_paths_only
test_archived_docs_are_not_used_as_current_inventory
```

---

# Milestone M6：策略 / 因子研究交接

## Task M6.1：建立 research run API

### 目标

让策略研究只需要提交配置和策略，不需要理解 runtime internals。

### 实施步骤

1. 提供统一入口：

```python
BacktestService.submit(config: BacktestRuntimeConfig) -> BacktestRunResult
```

2. 输出：

```text
run_id
manifest_path
equity_curve_path
orders_path
fills_path
metrics
artifact_hashes
```

3. 支持批量实验：

```python
BacktestService.submit_batch(configs: list[BacktestRuntimeConfig]) -> list[BacktestRunResult]
```

4. 只允许从 manifest/artifact 读取结果，不允许研究代码读取 runtime internals。

### 验收条件

新增测试：

```text
test_research_backtest_submit_returns_manifest_and_artifacts
test_research_batch_submit_is_deterministic
test_research_code_cannot_access_runtime_actor_internals
```

---

## Task M6.2：建立 factor research contract

### 目标

把后续研发重心切到因子，而不是交易平台架构。

### 实施步骤

1. 新增文档：

```text
docs/research/factor_contract_v1.md
```

2. 统一 factor interface：

```python
class Factor(Protocol):
    name: str
    version: str
    def compute(self, window: FactorWindow) -> FactorResult: ...
```

3. 每个 factor 必须有：

```text
- deterministic unit test
- missing data behavior
- universe filtering behavior
- output ranking convention
- lookback window definition
```

4. Factor 不得 import runtime/execution/broker。

### 验收条件

新增测试：

```text
test_factor_has_name_and_version
test_factor_is_deterministic
test_factor_handles_missing_data_explicitly
test_factor_package_has_no_runtime_execution_broker_imports
```

---

## Task M6.3：建立 experiment manifest

### 目标

让策略/因子研究结果可复现、可比较。

### 实施步骤

每个实验输出：

```json
{
  "experiment_id": "...",
  "platform_baseline_version": "qts-platform-v1",
  "strategy_name": "...",
  "strategy_version": "...",
  "factor_versions": {},
  "dataset_ids": [],
  "config_hash": "...",
  "artifact_hashes": {},
  "metrics": {}
}
```

新增目录：

```text
artifacts/research/<experiment_id>/
```

### 验收条件

新增测试：

```text
test_experiment_manifest_contains_strategy_factor_dataset_versions
test_experiment_manifest_contains_platform_baseline_version
test_same_experiment_input_produces_same_config_hash
test_experiment_artifacts_are_addressable_by_hash
```

---

# 最终退出条件

完成下列条件后，平台工程可以标记为最终状态，后续主要投入策略 / 因子研究：

```text
[ ] M0：Platform Final Baseline v1 文档、manifest 字段、freeze guardrail 完成。
[ ] M1：Live* 残留命名完成替换或明确保留豁免；配置概念收敛完成。
[ ] M2：Backtest / Paper simulated / IBKR Paper broker / Live observation 验收套件通过。
[ ] M3：Live capital hard gate 全部通过；live capital 默认仍 disabled。
[ ] M4：IBKR callback / reconnect / market-data permission failure drill 全部通过。
[ ] M5：RuntimeSession、coordinator、class inventory 复杂度预算通过。
[ ] M6：Strategy / Factor research API 和 experiment manifest 完成。
[ ] CI 包含 guardrail、readiness suite、golden backtest、paper smoke、quality budget。
[ ] 最新架构 panorama 不再显示过期路径或旧 alias。
```

---

# 最终建议

这不是再做一轮“大架构演进”。这是最后一轮“平台冻结冲刺”。

完成后建议明确宣布：

```text
QTS trading platform runtime is frozen at Platform Final Baseline v1.
Future work is strategy, factor, dataset, and research workflow first.
Runtime / broker / architecture changes require explicit platform freeze exception.
```

这样才能避免系统继续在工程架构上无限打磨，而真正转向策略和因子产出。
