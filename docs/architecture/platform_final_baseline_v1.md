# Platform Final Baseline v1

## 平台基线版本

```text
PLATFORM_BASELINE_VERSION = "qts-platform-v1"
```

该版本常量定义了 M0.1 目标的唯一平台基线版本；运行时清单、事件、与启动证据必须在可追溯位置携带这一值。

## 支持与限制的运行模式

- `backtest`
- `paper_simulated`
- `paper_broker`
- `live_observation`
- `observation`
- `live`

## 交易权限边界

- **允许下单模式**：`paper_simulated`、`paper_broker`
- **允许观察-only 模式**：`observation`、`live_observation`
- **允许实盘下单模式**：`live`（需允许实盘订单权限与运行时开关）
- **`live_capital` 默认禁用**：`observation`、`live_observation` 使用禁用实盘执行环境；实盘下单只在 `live` 且策略配置允许时开放。

## 向外部暴露的基线字段（本轮要求）

以下字段必须同时出现在每次运行产物中：

- `platform_baseline_version`（清单）
- `platform_baseline_version`（运行时事件 envelope）
- `platform_baseline_version`（启动清单证据 `startup_checklist`）

清单/事件在运行时由平台共用边界构建，避免按模式重复实现或分支。

## 冻结边界（M0.1 范围）

- 不再新增“历史兼容”分支路径作为默认运行时行为。
- 基线版本以 `PLATFORM_BASELINE_VERSION` 为唯一真值来源；不为单一模式定义独立基线常量。
- 未来若需扩展基线字段或冻结边界，需同步更新：
  - `docs/architecture/platform_final_baseline_v1.md`
  - 共享写入方（`qts.reporting.base`, `qts.runtime.sinks.base`, `qts.runtime.broker_startup`）并重跑对应 gate 测试。
