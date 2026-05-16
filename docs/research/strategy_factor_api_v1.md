# Strategy / Factor SDK Public Surface v1（冻结）

## 适用范围

- 目标：冻结 `qts.strategy_sdk` 与 `qts.factors` 的用户可见依赖面，防止策略/因子直接依赖运行时/执行/对账/账户 Actor 内核能力。
- 适用版本：v1
- 守护规则：`StrategySdkPublicSurfaceRule`

## 公共入口（允许直接导入）

- `qts.strategy_sdk`
  - `Strategy`
  - `StrategyContext`
  - `AssetRef`
  - `DataSubscription`
  - `DataView`
  - `FactorFactory`
  - `IndicatorFactory`
  - `PortfolioPosition`
  - `PortfolioView`
  - `TargetIntent`
  - `TargetIntentType`
- `qts.factors`
  - `FactorResult`
  - `FactorScore`
  - `MomentumFactor`

## 禁止策略层/因子层直接引用的模块

- `qts.runtime`（含 `qts.runtime.*`）
- `qts.execution.adapters`
- `qts.reconciliation`
- `qts.portfolio.account_actor`
- `qts.risk.risk_engine`

## 禁止直接引用的符号（即使通过上游模块间接引入）

- `BrokerActor`
- `OrderManagerActor`
- `ContractSpec`
- `BrokerSymbolMapping`
- `AccountActor`

## 验收与治理

- 统一由 `StrategySdkPublicSurfaceRule` 在 `scripts/verify_guardrails.py` 中触发报错码：
  - `STRATEGY_SDK_INTERNAL_LEAK`
- 与此规则联动的单测：
  - `tests/unit/scripts/test_verify_guardrails.py`
    - `test_strategy_package_cannot_import_runtime_internals`
    - `test_factor_package_has_no_runtime_dependency`
    - `test_factor_package_has_no_runtime_execution_broker_imports`
    - 以及既有的策略/因子/域边界测试（如 `test_guardrails_reject_strategy_sdk_internal_domain_symbols` 等）
