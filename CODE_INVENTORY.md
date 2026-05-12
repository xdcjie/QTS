# 非 Test Python 类、函数、方法与调用关系全量清单

生成时间：2026-05-12T06:18:04+00:00 UTC

## 范围与口径

- 源范围：仓库内所有 `.py` 文件，排除 `tests/`、任意 `*/tests/`、`test_*.py`、`*_test.py`、虚拟环境、缓存和构建目录。
- 包含：模块级函数、异步函数、类、实例方法、类方法、静态方法、属性方法、嵌套函数。
- 调用关系：基于 Python AST 提取每个类体/函数体/方法体中的所有直接 `Call` 表达式；同时尽量解析到仓库内部符号。动态分派、依赖注入、反射、回调注册和运行时生成的调用会保留为原始调用名。
- 作用说明：优先使用源码 docstring 首句；无 docstring 时根据名称、签名、继承和装饰器做静态推断，并标注为推断。

## 汇总

- 非 test Python 文件数：190
- 成功解析文件数：190
- 解析失败文件数：0
- 符号总数：987
- 类：285
- 函数/方法总数：702
- 模块级函数：125
- 方法/属性：575
- 嵌套函数：2

### 按类型统计

| 类型 | 数量 |
|---|---:|
| `class` | 285 |
| `module_function` | 124 |
| `nested_function` | 2 |
| `method` | 437 |
| `classmethod` | 26 |
| `staticmethod` | 60 |
| `property` | 48 |
| `async_module_function` | 1 |
| `async_method` | 4 |

## 文件清单

| 文件 | 模块 | 符号数 |
|---|---|---:|
| `backend/src/qts/__init__.py` | `qts` | 0 |
| `backend/src/qts/api/__init__.py` | `qts.api` | 0 |
| `backend/src/qts/api/app.py` | `qts.api.app` | 1 |
| `backend/src/qts/api/routes/__init__.py` | `qts.api.routes` | 0 |
| `backend/src/qts/api/routes/accounts.py` | `qts.api.routes.accounts` | 1 |
| `backend/src/qts/api/routes/backtests.py` | `qts.api.routes.backtests` | 1 |
| `backend/src/qts/api/routes/health.py` | `qts.api.routes.health` | 1 |
| `backend/src/qts/api/routes/operations.py` | `qts.api.routes.operations` | 11 |
| `backend/src/qts/api/routes/orders.py` | `qts.api.routes.orders` | 1 |
| `backend/src/qts/api/routes/strategies.py` | `qts.api.routes.strategies` | 3 |
| `backend/src/qts/api/schemas/__init__.py` | `qts.api.schemas` | 0 |
| `backend/src/qts/api/schemas/backtest_schema.py` | `qts.api.schemas.backtest_schema` | 2 |
| `backend/src/qts/api/schemas/common.py` | `qts.api.schemas.common` | 6 |
| `backend/src/qts/api/services/__init__.py` | `qts.api.services` | 0 |
| `backend/src/qts/api/services/command_idempotency.py` | `qts.api.services.command_idempotency` | 3 |
| `backend/src/qts/api/websocket/__init__.py` | `qts.api.websocket` | 0 |
| `backend/src/qts/api/websocket/dtos.py` | `qts.api.websocket.dtos` | 2 |
| `backend/src/qts/api/websocket/events.py` | `qts.api.websocket.events` | 1 |
| `backend/src/qts/api/websocket/fill_adapter.py` | `qts.api.websocket.fill_adapter` | 1 |
| `backend/src/qts/api/websocket/manager.py` | `qts.api.websocket.manager` | 9 |
| `backend/src/qts/application/__init__.py` | `qts.application` | 0 |
| `backend/src/qts/application/commands/__init__.py` | `qts.application.commands` | 0 |
| `backend/src/qts/application/commands/start_paper.py` | `qts.application.commands.start_paper` | 4 |
| `backend/src/qts/application/dto/__init__.py` | `qts.application.dto` | 0 |
| `backend/src/qts/application/dto/backtest.py` | `qts.application.dto.backtest` | 3 |
| `backend/src/qts/application/dto/health.py` | `qts.application.dto.health` | 1 |
| `backend/src/qts/application/dto/operations.py` | `qts.application.dto.operations` | 4 |
| `backend/src/qts/application/dto/order_events.py` | `qts.application.dto.order_events` | 2 |
| `backend/src/qts/application/services/__init__.py` | `qts.application.services` | 0 |
| `backend/src/qts/application/services/backtest.py` | `qts.application.services.backtest` | 3 |
| `backend/src/qts/application/services/health.py` | `qts.application.services.health` | 2 |
| `backend/src/qts/application/services/interfaces.py` | `qts.application.services.interfaces` | 6 |
| `backend/src/qts/application/services/operations.py` | `qts.application.services.operations` | 6 |
| `backend/src/qts/application/services/strategy_service.py` | `qts.application.services.strategy_service` | 8 |
| `backend/src/qts/application/strategy_lifecycle.py` | `qts.application.strategy_lifecycle` | 7 |
| `backend/src/qts/backtest/__init__.py` | `qts.backtest` | 0 |
| `backend/src/qts/backtest/config.py` | `qts.backtest.config` | 28 |
| `backend/src/qts/backtest/engine.py` | `qts.backtest.engine` | 46 |
| `backend/src/qts/backtest/historical_data_portal.py` | `qts.backtest.historical_data_portal` | 4 |
| `backend/src/qts/backtest/inputs.py` | `qts.backtest.inputs` | 15 |
| `backend/src/qts/backtest/report.py` | `qts.backtest.report` | 21 |
| `backend/src/qts/backtest/runner.py` | `qts.backtest.runner` | 7 |
| `backend/src/qts/config/__init__.py` | `qts.config` | 0 |
| `backend/src/qts/config/ibkr.py` | `qts.config.ibkr` | 9 |
| `backend/src/qts/core/__init__.py` | `qts.core` | 0 |
| `backend/src/qts/core/ids.py` | `qts.core.ids` | 12 |
| `backend/src/qts/core/time.py` | `qts.core.time` | 6 |
| `backend/src/qts/data/__init__.py` | `qts.data` | 0 |
| `backend/src/qts/data/adapters/__init__.py` | `qts.data.adapters` | 0 |
| `backend/src/qts/data/adapters/ibkr_market_data.py` | `qts.data.adapters.ibkr_market_data` | 9 |
| `backend/src/qts/data/bars/__init__.py` | `qts.data.bars` | 0 |
| `backend/src/qts/data/bars/aggregator.py` | `qts.data.bars.aggregator` | 15 |
| `backend/src/qts/data/bars/alignment.py` | `qts.data.bars.alignment` | 2 |
| `backend/src/qts/data/bars/builder.py` | `qts.data.bars.builder` | 0 |
| `backend/src/qts/data/bars/timeframe.py` | `qts.data.bars.timeframe` | 4 |
| `backend/src/qts/data/bars/validation.py` | `qts.data.bars.validation` | 0 |
| `backend/src/qts/data/feeds/__init__.py` | `qts.data.feeds` | 0 |
| `backend/src/qts/data/feeds/replay_feed.py` | `qts.data.feeds.replay_feed` | 3 |
| `backend/src/qts/data/historical/__init__.py` | `qts.data.historical` | 0 |
| `backend/src/qts/data/historical/catalog.py` | `qts.data.historical.catalog` | 14 |
| `backend/src/qts/data/historical/chains.py` | `qts.data.historical.chains` | 11 |
| `backend/src/qts/data/historical/config.py` | `qts.data.historical.config` | 32 |
| `backend/src/qts/data/historical/csv_dataset.py` | `qts.data.historical.csv_dataset` | 26 |
| `backend/src/qts/data/historical/csv_format.py` | `qts.data.historical.csv_format` | 8 |
| `backend/src/qts/data/historical/service.py` | `qts.data.historical.service` | 5 |
| `backend/src/qts/data/historical/symbols.py` | `qts.data.historical.symbols` | 4 |
| `backend/src/qts/data/live_feed.py` | `qts.data.live_feed` | 23 |
| `backend/src/qts/data/normalization/__init__.py` | `qts.data.normalization` | 0 |
| `backend/src/qts/data/provenance.py` | `qts.data.provenance` | 4 |
| `backend/src/qts/data/sessions/__init__.py` | `qts.data.sessions` | 0 |
| `backend/src/qts/data/sessions/filter.py` | `qts.data.sessions.filter` | 4 |
| `backend/src/qts/data/sessions/window.py` | `qts.data.sessions.window` | 5 |
| `backend/src/qts/data/stores/__init__.py` | `qts.data.stores` | 0 |
| `backend/src/qts/data/stores/base.py` | `qts.data.stores.base` | 3 |
| `backend/src/qts/data/stores/memory_store.py` | `qts.data.stores.memory_store` | 4 |
| `backend/src/qts/data/stores/parquet_store.py` | `qts.data.stores.parquet_store` | 8 |
| `backend/src/qts/data/subscriptions.py` | `qts.data.subscriptions` | 8 |
| `backend/src/qts/data/validation_report.py` | `qts.data.validation_report` | 8 |
| `backend/src/qts/domain/__init__.py` | `qts.domain` | 0 |
| `backend/src/qts/domain/events/__init__.py` | `qts.domain.events` | 0 |
| `backend/src/qts/domain/events/event.py` | `qts.domain.events.event` | 2 |
| `backend/src/qts/domain/events/metadata.py` | `qts.domain.events.metadata` | 2 |
| `backend/src/qts/domain/instruments/__init__.py` | `qts.domain.instruments` | 0 |
| `backend/src/qts/domain/instruments/contract_spec.py` | `qts.domain.instruments.contract_spec` | 4 |
| `backend/src/qts/domain/instruments/derivative_spec.py` | `qts.domain.instruments.derivative_spec` | 7 |
| `backend/src/qts/domain/instruments/instrument.py` | `qts.domain.instruments.instrument` | 3 |
| `backend/src/qts/domain/market_data/__init__.py` | `qts.domain.market_data` | 0 |
| `backend/src/qts/domain/market_data/bar.py` | `qts.domain.market_data.bar` | 9 |
| `backend/src/qts/domain/orders/__init__.py` | `qts.domain.orders` | 0 |
| `backend/src/qts/domain/portfolio/__init__.py` | `qts.domain.portfolio` | 0 |
| `backend/src/qts/domain/risk/__init__.py` | `qts.domain.risk` | 0 |
| `backend/src/qts/domain/risk/decision.py` | `qts.domain.risk.decision` | 6 |
| `backend/src/qts/domain/risk/request.py` | `qts.domain.risk.request` | 3 |
| `backend/src/qts/execution/__init__.py` | `qts.execution` | 0 |
| `backend/src/qts/execution/adapters/__init__.py` | `qts.execution.adapters` | 0 |
| `backend/src/qts/execution/adapters/ibkr_order_execution.py` | `qts.execution.adapters.ibkr_order_execution` | 8 |
| `backend/src/qts/execution/broker.py` | `qts.execution.broker` | 24 |
| `backend/src/qts/execution/idempotency.py` | `qts.execution.idempotency` | 6 |
| `backend/src/qts/execution/order_manager.py` | `qts.execution.order_manager` | 27 |
| `backend/src/qts/execution/order_state_machine.py` | `qts.execution.order_state_machine` | 5 |
| `backend/src/qts/execution/simulator/__init__.py` | `qts.execution.simulator` | 0 |
| `backend/src/qts/execution/simulator/fill_model.py` | `qts.execution.simulator.fill_model` | 2 |
| `backend/src/qts/execution/simulator/simulated_broker.py` | `qts.execution.simulator.simulated_broker` | 3 |
| `backend/src/qts/factors/__init__.py` | `qts.factors` | 0 |
| `backend/src/qts/factors/momentum.py` | `qts.factors.momentum` | 9 |
| `backend/src/qts/indicators/__init__.py` | `qts.indicators` | 0 |
| `backend/src/qts/indicators/price/__init__.py` | `qts.indicators.price` | 0 |
| `backend/src/qts/indicators/price/ema.py` | `qts.indicators.price.ema` | 4 |
| `backend/src/qts/indicators/price/sma.py` | `qts.indicators.price.sma` | 4 |
| `backend/src/qts/indicators/rolling.py` | `qts.indicators.rolling` | 8 |
| `backend/src/qts/load/__init__.py` | `qts.load` | 0 |
| `backend/src/qts/load/bootstrap.py` | `qts.load.bootstrap` | 1 |
| `backend/src/qts/load/synthetic_market_data.py` | `qts.load.synthetic_market_data` | 3 |
| `backend/src/qts/observability/__init__.py` | `qts.observability` | 0 |
| `backend/src/qts/observability/audit.py` | `qts.observability.audit` | 2 |
| `backend/src/qts/observability/logging.py` | `qts.observability.logging` | 3 |
| `backend/src/qts/observability/metrics.py` | `qts.observability.metrics` | 7 |
| `backend/src/qts/portfolio/__init__.py` | `qts.portfolio` | 0 |
| `backend/src/qts/portfolio/accounting/__init__.py` | `qts.portfolio.accounting` | 0 |
| `backend/src/qts/portfolio/accounting/fill_accounting.py` | `qts.portfolio.accounting.fill_accounting` | 5 |
| `backend/src/qts/portfolio/cash_book.py` | `qts.portfolio.cash_book` | 6 |
| `backend/src/qts/portfolio/position_book.py` | `qts.portfolio.position_book` | 6 |
| `backend/src/qts/portfolio/reservation_book.py` | `qts.portfolio.reservation_book` | 7 |
| `backend/src/qts/portfolio/valuation/__init__.py` | `qts.portfolio.valuation` | 0 |
| `backend/src/qts/portfolio/valuation/models.py` | `qts.portfolio.valuation.models` | 3 |
| `backend/src/qts/reconciliation.py` | `qts.reconciliation` | 23 |
| `backend/src/qts/registry/__init__.py` | `qts.registry` | 0 |
| `backend/src/qts/registry/broker_symbol_mapping.py` | `qts.registry.broker_symbol_mapping` | 8 |
| `backend/src/qts/registry/calendar_registry.py` | `qts.registry.calendar_registry` | 10 |
| `backend/src/qts/registry/future_chain_registry.py` | `qts.registry.future_chain_registry` | 11 |
| `backend/src/qts/registry/future_roll.py` | `qts.registry.future_roll` | 19 |
| `backend/src/qts/registry/instrument_registry.py` | `qts.registry.instrument_registry` | 7 |
| `backend/src/qts/registry/option_chain_registry.py` | `qts.registry.option_chain_registry` | 5 |
| `backend/src/qts/registry/providers/__init__.py` | `qts.registry.providers` | 0 |
| `backend/src/qts/registry/providers/comex_gold_calendar_provider.py` | `qts.registry.providers.comex_gold_calendar_provider` | 2 |
| `backend/src/qts/registry/providers/exchange_calendar_provider.py` | `qts.registry.providers.exchange_calendar_provider` | 4 |
| `backend/src/qts/registry/symbol_resolution.py` | `qts.registry.symbol_resolution` | 8 |
| `backend/src/qts/risk/__init__.py` | `qts.risk` | 0 |
| `backend/src/qts/risk/config.py` | `qts.risk.config` | 4 |
| `backend/src/qts/risk/kill_switch.py` | `qts.risk.kill_switch` | 14 |
| `backend/src/qts/risk/margin/__init__.py` | `qts.risk.margin` | 0 |
| `backend/src/qts/risk/risk_engine.py` | `qts.risk.risk_engine` | 3 |
| `backend/src/qts/risk/rule.py` | `qts.risk.rule` | 2 |
| `backend/src/qts/risk/rule_registry.py` | `qts.risk.rule_registry` | 3 |
| `backend/src/qts/risk/rules/__init__.py` | `qts.risk.rules` | 0 |
| `backend/src/qts/risk/rules/max_notional.py` | `qts.risk.rules.max_notional` | 3 |
| `backend/src/qts/risk/rules/max_order_qty.py` | `qts.risk.rules.max_order_qty` | 3 |
| `backend/src/qts/risk/rules/trading_session_rule.py` | `qts.risk.rules.trading_session_rule` | 4 |
| `backend/src/qts/runtime/__init__.py` | `qts.runtime` | 0 |
| `backend/src/qts/runtime/actor.py` | `qts.runtime.actor` | 2 |
| `backend/src/qts/runtime/actor_ref.py` | `qts.runtime.actor_ref` | 4 |
| `backend/src/qts/runtime/actors/__init__.py` | `qts.runtime.actors` | 0 |
| `backend/src/qts/runtime/actors/account_actor.py` | `qts.runtime.actors.account_actor` | 7 |
| `backend/src/qts/runtime/actors/execution_actor.py` | `qts.runtime.actors.execution_actor` | 6 |
| `backend/src/qts/runtime/actors/market_data_actor.py` | `qts.runtime.actors.market_data_actor` | 15 |
| `backend/src/qts/runtime/actors/order_manager_actor.py` | `qts.runtime.actors.order_manager_actor` | 11 |
| `backend/src/qts/runtime/actors/signal_aggregator_actor.py` | `qts.runtime.actors.signal_aggregator_actor` | 5 |
| `backend/src/qts/runtime/actors/strategy_actor.py` | `qts.runtime.actors.strategy_actor` | 9 |
| `backend/src/qts/runtime/event_store.py` | `qts.runtime.event_store` | 17 |
| `backend/src/qts/runtime/live.py` | `qts.runtime.live` | 19 |
| `backend/src/qts/runtime/mailbox.py` | `qts.runtime.mailbox` | 6 |
| `backend/src/qts/runtime/partitioning.py` | `qts.runtime.partitioning` | 8 |
| `backend/src/qts/runtime/router.py` | `qts.runtime.router` | 5 |
| `backend/src/qts/runtime/state_recovery.py` | `qts.runtime.state_recovery` | 6 |
| `backend/src/qts/strategy_sdk/__init__.py` | `qts.strategy_sdk` | 0 |
| `backend/src/qts/strategy_sdk/asset_ref.py` | `qts.strategy_sdk.asset_ref` | 3 |
| `backend/src/qts/strategy_sdk/context.py` | `qts.strategy_sdk.context` | 25 |
| `backend/src/qts/strategy_sdk/data_view.py` | `qts.strategy_sdk.data_view` | 4 |
| `backend/src/qts/strategy_sdk/factors.py` | `qts.strategy_sdk.factors` | 2 |
| `backend/src/qts/strategy_sdk/indicators.py` | `qts.strategy_sdk.indicators` | 7 |
| `backend/src/qts/strategy_sdk/portfolio_view.py` | `qts.strategy_sdk.portfolio_view` | 6 |
| `backend/src/qts/strategy_sdk/strategy.py` | `qts.strategy_sdk.strategy` | 8 |
| `backend/src/qts/strategy_sdk/target.py` | `qts.strategy_sdk.target` | 2 |
| `backend/src/qts/workers/__init__.py` | `qts.workers` | 0 |
| `examples/__init__.py` | `examples` | 0 |
| `examples/strategies/__init__.py` | `examples.strategies` | 0 |
| `examples/strategies/gc_si_momentum.py` | `examples.strategies.gc_si_momentum` | 6 |
| `examples/strategies/moving_average_cross.py` | `examples.strategies.moving_average_cross` | 3 |
| `scripts/__init__.py` | `scripts` | 0 |
| `scripts/bootstrap.py` | `scripts.bootstrap` | 1 |
| `scripts/ibkr_collect_environment_evidence.py` | `scripts.ibkr_collect_environment_evidence` | 12 |
| `scripts/ibkr_paper_order_lifecycle_drill.py` | `scripts.ibkr_paper_order_lifecycle_drill` | 10 |
| `scripts/run_api.py` | `scripts.run_api` | 0 |
| `scripts/run_backtest.py` | `scripts.run_backtest` | 1 |
| `scripts/run_load.py` | `scripts.run_load` | 1 |
| `scripts/run_paper.py` | `scripts.run_paper` | 1 |
| `scripts/run_paper_ibkr.py` | `scripts.run_paper_ibkr` | 0 |
| `scripts/run_worker.py` | `scripts.run_worker` | 0 |
| `scripts/validate_historical.py` | `scripts.validate_historical` | 1 |
| `scripts/verify_guardrails.py` | `scripts.verify_guardrails` | 25 |

## 全量符号索引

| 文件:行 | 类型 | 符号 | 作用 | 内部调用数 | 原始调用数 |
|---|---|---|---|---:|---:|
| `backend/src/qts/api/app.py:18` | `module_function` | `qts.api.app.create_app` | 未写 docstring；静态推断为创建对象或资源（名称：create app）。 | 0 | 8 |
| `backend/src/qts/api/routes/accounts.py:13` | `module_function` | `qts.api.routes.accounts.account_snapshot` | 未写 docstring；静态推断为 `account snapshot` 函数，具体语义以实现为准。 | 1 | 1 |
| `backend/src/qts/api/routes/backtests.py:15` | `module_function` | `qts.api.routes.backtests.submit_backtest` | 未写 docstring；静态推断为 `submit backtest` 函数，具体语义以实现为准。 | 2 | 4 |
| `backend/src/qts/api/routes/health.py:13` | `module_function` | `qts.api.routes.health.health` | 未写 docstring；静态推断为 `health` 函数，具体语义以实现为准。 | 1 | 2 |
| `backend/src/qts/api/routes/operations.py:20` | `class` | `qts.api.routes.operations.RuntimeCommandResponse` | 未写 docstring；静态推断为定义 Runtime Command Response 概念，继承/实现 BaseModel。 | 0 | 0 |
| `backend/src/qts/api/routes/operations.py:24` | `class` | `qts.api.routes.operations.KillSwitchScopeSchema` | 未写 docstring；静态推断为定义 Kill Switch Scope Schema 概念，继承/实现 StrEnum。 | 0 | 0 |
| `backend/src/qts/api/routes/operations.py:31` | `class` | `qts.api.routes.operations.KillSwitchCommand` | 未写 docstring；静态推断为定义 Kill Switch Command 概念，继承/实现 BaseModel。 | 0 | 0 |
| `backend/src/qts/api/routes/operations.py:37` | `method` | `qts.api.routes.operations.KillSwitchCommand.validate_scope` | 未写 docstring；静态推断为校验输入、状态或领域约束（名称：validate scope）。 | 0 | 4 |
| `backend/src/qts/api/routes/operations.py:47` | `class` | `qts.api.routes.operations.KillSwitchResponse` | 未写 docstring；静态推断为定义 Kill Switch Response 概念，继承/实现 BaseModel。 | 0 | 0 |
| `backend/src/qts/api/routes/operations.py:54` | `module_function` | `qts.api.routes.operations._require_operator` | 未写 docstring；静态推断为 `require operator` 函数，具体语义以实现为准。 | 0 | 2 |
| `backend/src/qts/api/routes/operations.py:60` | `module_function` | `qts.api.routes.operations.pause_runtime` | 未写 docstring；静态推断为 `pause runtime` 函数，具体语义以实现为准。 | 1 | 3 |
| `backend/src/qts/api/routes/operations.py:66` | `nested_function` | `qts.api.routes.operations.pause_runtime.<locals>.command` | 未写 docstring；静态推断为 `command` 函数，具体语义以实现为准。 | 1 | 2 |
| `backend/src/qts/api/routes/operations.py:76` | `module_function` | `qts.api.routes.operations.resume_runtime` | 未写 docstring；静态推断为 `resume runtime` 函数，具体语义以实现为准。 | 1 | 3 |
| `backend/src/qts/api/routes/operations.py:82` | `nested_function` | `qts.api.routes.operations.resume_runtime.<locals>.command` | 未写 docstring；静态推断为 `command` 函数，具体语义以实现为准。 | 1 | 2 |
| `backend/src/qts/api/routes/operations.py:92` | `module_function` | `qts.api.routes.operations.activate_kill_switch` | 未写 docstring；静态推断为 `activate kill switch` 函数，具体语义以实现为准。 | 3 | 4 |
| `backend/src/qts/api/routes/orders.py:13` | `module_function` | `qts.api.routes.orders.order_status` | 未写 docstring；静态推断为 `order status` 函数，具体语义以实现为准。 | 1 | 1 |
| `backend/src/qts/api/routes/strategies.py:13` | `module_function` | `qts.api.routes.strategies.list_strategies` | 未写 docstring；静态推断为 `list strategies` 函数，具体语义以实现为准。 | 1 | 1 |
| `backend/src/qts/api/routes/strategies.py:18` | `module_function` | `qts.api.routes.strategies.start_strategy` | 未写 docstring；静态推断为启动流程或服务（名称：start strategy）。 | 1 | 1 |
| `backend/src/qts/api/routes/strategies.py:23` | `module_function` | `qts.api.routes.strategies.stop_strategy` | 未写 docstring；静态推断为停止流程或服务（名称：stop strategy）。 | 1 | 1 |
| `backend/src/qts/api/schemas/backtest_schema.py:8` | `class` | `qts.api.schemas.backtest_schema.BacktestRequestSchema` | HTTP request for submitting a backtest. | 0 | 1 |
| `backend/src/qts/api/schemas/backtest_schema.py:14` | `class` | `qts.api.schemas.backtest_schema.BacktestRunSchema` | HTTP response for a submitted backtest. | 0 | 1 |
| `backend/src/qts/api/schemas/common.py:8` | `class` | `qts.api.schemas.common.StrategyStatusSchema` | 未写 docstring；静态推断为定义 Strategy Status Schema 概念，继承/实现 BaseModel。 | 0 | 0 |
| `backend/src/qts/api/schemas/common.py:13` | `class` | `qts.api.schemas.common.AccountSnapshotSchema` | 未写 docstring；静态推断为定义 Account Snapshot Schema 概念，继承/实现 BaseModel。 | 0 | 0 |
| `backend/src/qts/api/schemas/common.py:18` | `class` | `qts.api.schemas.common.OrderStatusSchema` | 未写 docstring；静态推断为定义 Order Status Schema 概念，继承/实现 BaseModel。 | 0 | 0 |
| `backend/src/qts/api/schemas/common.py:23` | `class` | `qts.api.schemas.common.RiskRuleSchema` | 未写 docstring；静态推断为定义 Risk Rule Schema 概念，继承/实现 BaseModel。 | 0 | 0 |
| `backend/src/qts/api/schemas/common.py:28` | `class` | `qts.api.schemas.common.OperationalErrorSchema` | 未写 docstring；静态推断为定义 Operational Error Schema 概念，继承/实现 BaseModel。 | 0 | 0 |
| `backend/src/qts/api/schemas/common.py:34` | `classmethod` | `qts.api.schemas.common.OperationalErrorSchema.from_exception` | 未写 docstring；静态推断为从指定来源构造或转换对象（名称：from exception）。 | 0 | 1 |
| `backend/src/qts/api/services/command_idempotency.py:11` | `class` | `qts.api.services.command_idempotency.CommandIdempotencyStore` | Remember the first result for each command idempotency key. | 0 | 0 |
| `backend/src/qts/api/services/command_idempotency.py:14` | `method` | `qts.api.services.command_idempotency.CommandIdempotencyStore.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 0 | 0 |
| `backend/src/qts/api/services/command_idempotency.py:17` | `method` | `qts.api.services.command_idempotency.CommandIdempotencyStore.run` | 未写 docstring；静态推断为运行流程或命令（名称：run）。 | 0 | 3 |
| `backend/src/qts/api/websocket/dtos.py:10` | `class` | `qts.api.websocket.dtos.StreamEventDTO` | 未写 docstring；静态推断为定义 Stream Event D T O 概念或数据结构。 | 0 | 1 |
| `backend/src/qts/api/websocket/dtos.py:16` | `method` | `qts.api.websocket.dtos.StreamEventDTO.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 2 |
| `backend/src/qts/api/websocket/events.py:11` | `async_module_function` | `qts.api.websocket.events.event_stream` | 未写 docstring；静态推断为 `event stream` 函数，具体语义以实现为准。 | 0 | 3 |
| `backend/src/qts/api/websocket/fill_adapter.py:11` | `module_function` | `qts.api.websocket.fill_adapter.order_fill_to_stream_dto` | Convert an OrderManager-validated fill into a public stream event DTO. | 1 | 4 |
| `backend/src/qts/api/websocket/manager.py:8` | `class` | `qts.api.websocket.manager.JsonWebSocket` | 未写 docstring；静态推断为定义 Json Web Socket 概念，继承/实现 Protocol。 | 0 | 0 |
| `backend/src/qts/api/websocket/manager.py:9` | `async_method` | `qts.api.websocket.manager.JsonWebSocket.accept` | 未写 docstring；静态推断为所属类上的 `accept` 行为。 | 0 | 0 |
| `backend/src/qts/api/websocket/manager.py:11` | `async_method` | `qts.api.websocket.manager.JsonWebSocket.send_json` | 未写 docstring；静态推断为所属类上的 `send json` 行为。 | 0 | 0 |
| `backend/src/qts/api/websocket/manager.py:14` | `class` | `qts.api.websocket.manager.WebSocketConnectionManager` | Track WebSocket clients and broadcast JSON payloads. | 0 | 0 |
| `backend/src/qts/api/websocket/manager.py:17` | `method` | `qts.api.websocket.manager.WebSocketConnectionManager.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 0 | 0 |
| `backend/src/qts/api/websocket/manager.py:21` | `property` | `qts.api.websocket.manager.WebSocketConnectionManager.count` | 未写 docstring；静态推断为所属类上的 `count` 行为。 | 0 | 1 |
| `backend/src/qts/api/websocket/manager.py:24` | `async_method` | `qts.api.websocket.manager.WebSocketConnectionManager.connect` | 未写 docstring；静态推断为所属类上的 `connect` 行为。 | 0 | 2 |
| `backend/src/qts/api/websocket/manager.py:28` | `method` | `qts.api.websocket.manager.WebSocketConnectionManager.disconnect` | 未写 docstring；静态推断为所属类上的 `disconnect` 行为。 | 0 | 1 |
| `backend/src/qts/api/websocket/manager.py:32` | `async_method` | `qts.api.websocket.manager.WebSocketConnectionManager.broadcast` | 未写 docstring；静态推断为所属类上的 `broadcast` 行为。 | 1 | 4 |
| `backend/src/qts/application/commands/start_paper.py:10` | `class` | `qts.application.commands.start_paper.PaperRuntimeConfig` | Paper runtime configuration without real broker credentials. | 0 | 1 |
| `backend/src/qts/application/commands/start_paper.py:18` | `method` | `qts.application.commands.start_paper.PaperRuntimeConfig.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 6 |
| `backend/src/qts/application/commands/start_paper.py:28` | `class` | `qts.application.commands.start_paper.PaperRuntime` | Constructed paper runtime descriptor. | 0 | 1 |
| `backend/src/qts/application/commands/start_paper.py:35` | `module_function` | `qts.application.commands.start_paper.start_paper` | Construct the paper runtime boundary without connecting to a real broker. | 1 | 1 |
| `backend/src/qts/application/dto/backtest.py:9` | `class` | `qts.application.dto.backtest.BacktestRequestDTO` | Stable application request for starting a backtest. | 0 | 1 |
| `backend/src/qts/application/dto/backtest.py:14` | `method` | `qts.application.dto.backtest.BacktestRequestDTO.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 2 |
| `backend/src/qts/application/dto/backtest.py:20` | `class` | `qts.application.dto.backtest.BacktestRunDTO` | Stable application response for a submitted backtest. | 0 | 1 |
| `backend/src/qts/application/dto/health.py:9` | `class` | `qts.application.dto.health.HealthStatusDTO` | Stable health status response. | 0 | 1 |
| `backend/src/qts/application/dto/operations.py:9` | `class` | `qts.application.dto.operations.RuntimeStateDTO` | Stable runtime state response. | 0 | 1 |
| `backend/src/qts/application/dto/operations.py:16` | `class` | `qts.application.dto.operations.KillSwitchCommandDTO` | Stable kill-switch activation request. | 0 | 1 |
| `backend/src/qts/application/dto/operations.py:23` | `method` | `qts.application.dto.operations.KillSwitchCommandDTO.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 6 |
| `backend/src/qts/application/dto/operations.py:33` | `class` | `qts.application.dto.operations.KillSwitchStateDTO` | Stable kill-switch state response. | 0 | 1 |
| `backend/src/qts/application/dto/order_events.py:10` | `class` | `qts.application.dto.order_events.OrderFillDTO` | Stable fill event shape for public streams. | 0 | 1 |
| `backend/src/qts/application/dto/order_events.py:20` | `method` | `qts.application.dto.order_events.OrderFillDTO.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 8 |
| `backend/src/qts/application/services/backtest.py:10` | `class` | `qts.application.services.backtest.BacktestService` | Application boundary for backtest use cases. | 0 | 0 |
| `backend/src/qts/application/services/backtest.py:13` | `method` | `qts.application.services.backtest.BacktestService.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 1 | 1 |
| `backend/src/qts/application/services/backtest.py:16` | `method` | `qts.application.services.backtest.BacktestService.submit` | 未写 docstring；静态推断为所属类上的 `submit` 行为。 | 1 | 2 |
| `backend/src/qts/application/services/health.py:8` | `class` | `qts.application.services.health.HealthService` | Returns platform health without exposing internals. | 0 | 0 |
| `backend/src/qts/application/services/health.py:11` | `method` | `qts.application.services.health.HealthService.status` | 未写 docstring；静态推断为所属类上的 `status` 行为。 | 1 | 1 |
| `backend/src/qts/application/services/interfaces.py:8` | `class` | `qts.application.services.interfaces.AccountService` | 未写 docstring；静态推断为定义 Account Service 概念，继承/实现 Protocol。 | 0 | 0 |
| `backend/src/qts/application/services/interfaces.py:9` | `method` | `qts.application.services.interfaces.AccountService.snapshot` | 未写 docstring；静态推断为所属类上的 `snapshot` 行为。 | 0 | 0 |
| `backend/src/qts/application/services/interfaces.py:12` | `class` | `qts.application.services.interfaces.OrderService` | 未写 docstring；静态推断为定义 Order Service 概念，继承/实现 Protocol。 | 0 | 0 |
| `backend/src/qts/application/services/interfaces.py:13` | `method` | `qts.application.services.interfaces.OrderService.status` | 未写 docstring；静态推断为所属类上的 `status` 行为。 | 0 | 0 |
| `backend/src/qts/application/services/interfaces.py:16` | `class` | `qts.application.services.interfaces.RiskService` | 未写 docstring；静态推断为定义 Risk Service 概念，继承/实现 Protocol。 | 0 | 0 |
| `backend/src/qts/application/services/interfaces.py:17` | `method` | `qts.application.services.interfaces.RiskService.rules` | 未写 docstring；静态推断为所属类上的 `rules` 行为。 | 0 | 0 |
| `backend/src/qts/application/services/operations.py:9` | `class` | `qts.application.services.operations.OperationsService` | Owns operational state without leaking runtime internals into API routes. | 0 | 0 |
| `backend/src/qts/application/services/operations.py:12` | `method` | `qts.application.services.operations.OperationsService.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 1 | 1 |
| `backend/src/qts/application/services/operations.py:16` | `method` | `qts.application.services.operations.OperationsService.pause_runtime` | 未写 docstring；静态推断为所属类上的 `pause runtime` 行为。 | 1 | 1 |
| `backend/src/qts/application/services/operations.py:20` | `method` | `qts.application.services.operations.OperationsService.resume_runtime` | 未写 docstring；静态推断为所属类上的 `resume runtime` 行为。 | 1 | 1 |
| `backend/src/qts/application/services/operations.py:24` | `method` | `qts.application.services.operations.OperationsService.activate_kill_switch` | 未写 docstring；静态推断为所属类上的 `activate kill switch` 行为。 | 2 | 3 |
| `backend/src/qts/application/services/operations.py:35` | `staticmethod` | `qts.application.services.operations.OperationsService._scope_from_command` | 未写 docstring；静态推断为所属类上的 `scope from command` 行为。 | 3 | 3 |
| `backend/src/qts/application/services/strategy_service.py:9` | `class` | `qts.application.services.strategy_service.StrategyLifecycleService` | Start, stop, and inspect configured strategy instances. | 0 | 0 |
| `backend/src/qts/application/services/strategy_service.py:12` | `method` | `qts.application.services.strategy_service.StrategyLifecycleService.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 0 | 0 |
| `backend/src/qts/application/services/strategy_service.py:20` | `method` | `qts.application.services.strategy_service.StrategyLifecycleService.add` | 未写 docstring；静态推断为所属类上的 `add` 行为。 | 0 | 1 |
| `backend/src/qts/application/services/strategy_service.py:27` | `method` | `qts.application.services.strategy_service.StrategyLifecycleService.start` | 未写 docstring；静态推断为启动流程或服务（名称：start）。 | 1 | 1 |
| `backend/src/qts/application/services/strategy_service.py:32` | `method` | `qts.application.services.strategy_service.StrategyLifecycleService.stop` | 未写 docstring；静态推断为停止流程或服务（名称：stop）。 | 1 | 1 |
| `backend/src/qts/application/services/strategy_service.py:37` | `method` | `qts.application.services.strategy_service.StrategyLifecycleService.status` | 未写 docstring；静态推断为所属类上的 `status` 行为。 | 1 | 1 |
| `backend/src/qts/application/services/strategy_service.py:41` | `method` | `qts.application.services.strategy_service.StrategyLifecycleService.list_instances` | 未写 docstring；静态推断为所属类上的 `list instances` 行为。 | 0 | 2 |
| `backend/src/qts/application/services/strategy_service.py:44` | `method` | `qts.application.services.strategy_service.StrategyLifecycleService._require_enabled` | 未写 docstring；静态推断为所属类上的 `require enabled` 行为。 | 0 | 1 |
| `backend/src/qts/application/strategy_lifecycle.py:14` | `class` | `qts.application.strategy_lifecycle.StrategyStatus` | Configured strategy instance lifecycle status. | 0 | 0 |
| `backend/src/qts/application/strategy_lifecycle.py:22` | `class` | `qts.application.strategy_lifecycle.StrategyInstance` | Configured runtime instance of a Strategy class. | 0 | 3 |
| `backend/src/qts/application/strategy_lifecycle.py:32` | `method` | `qts.application.strategy_lifecycle.StrategyInstance.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 4 |
| `backend/src/qts/application/strategy_lifecycle.py:39` | `class` | `qts.application.strategy_lifecycle.StrategyRegistry` | Safe registry for explicitly approved strategy classes. | 0 | 0 |
| `backend/src/qts/application/strategy_lifecycle.py:42` | `method` | `qts.application.strategy_lifecycle.StrategyRegistry.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 0 | 0 |
| `backend/src/qts/application/strategy_lifecycle.py:45` | `method` | `qts.application.strategy_lifecycle.StrategyRegistry.register` | 未写 docstring；静态推断为所属类上的 `register` 行为。 | 0 | 3 |
| `backend/src/qts/application/strategy_lifecycle.py:52` | `method` | `qts.application.strategy_lifecycle.StrategyRegistry.resolve` | 未写 docstring；静态推断为解析标识、引用或配置到目标对象（名称：resolve）。 | 0 | 1 |
| `backend/src/qts/backtest/config.py:21` | `class` | `qts.backtest.config.CostModelConfig` | Explicit backtest cost model settings. | 0 | 3 |
| `backend/src/qts/backtest/config.py:27` | `method` | `qts.backtest.config.CostModelConfig.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 10 |
| `backend/src/qts/backtest/config.py:39` | `method` | `qts.backtest.config.CostModelConfig.to_payload` | 未写 docstring；静态推断为转换或序列化为指定目标表示（名称：to payload）。 | 0 | 2 |
| `backend/src/qts/backtest/config.py:47` | `class` | `qts.backtest.config.RiskConfig` | Backtest risk settings. | 0 | 1 |
| `backend/src/qts/backtest/config.py:52` | `method` | `qts.backtest.config.RiskConfig.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 5 |
| `backend/src/qts/backtest/config.py:57` | `method` | `qts.backtest.config.RiskConfig.to_payload` | 未写 docstring；静态推断为转换或序列化为指定目标表示（名称：to payload）。 | 0 | 1 |
| `backend/src/qts/backtest/config.py:62` | `class` | `qts.backtest.config.RollPolicyConfig` | Continuous futures roll policy for config-driven backtest runs. | 0 | 1 |
| `backend/src/qts/backtest/config.py:68` | `method` | `qts.backtest.config.RollPolicyConfig.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 4 |
| `backend/src/qts/backtest/config.py:74` | `method` | `qts.backtest.config.RollPolicyConfig.to_payload` | 未写 docstring；静态推断为转换或序列化为指定目标表示（名称：to payload）。 | 0 | 0 |
| `backend/src/qts/backtest/config.py:79` | `class` | `qts.backtest.config.BacktestMarketDataReference` | Market data source reference for one backtest run. | 0 | 1 |
| `backend/src/qts/backtest/config.py:86` | `method` | `qts.backtest.config.BacktestMarketDataReference.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 11 |
| `backend/src/qts/backtest/config.py:104` | `property` | `qts.backtest.config.BacktestMarketDataReference.is_configured` | 未写 docstring；静态推断为判断布尔条件（名称：is configured）。 | 0 | 0 |
| `backend/src/qts/backtest/config.py:107` | `method` | `qts.backtest.config.BacktestMarketDataReference.to_payload` | 未写 docstring；静态推断为转换或序列化为指定目标表示（名称：to payload）。 | 0 | 2 |
| `backend/src/qts/backtest/config.py:119` | `class` | `qts.backtest.config.BacktestStrategyConfig` | Configured strategy instance referenced by a backtest run. | 0 | 3 |
| `backend/src/qts/backtest/config.py:129` | `method` | `qts.backtest.config.BacktestStrategyConfig.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 13 |
| `backend/src/qts/backtest/config.py:142` | `classmethod` | `qts.backtest.config.BacktestStrategyConfig.from_yaml` | 未写 docstring；静态推断为从指定来源构造或转换对象（名称：from yaml）。 | 1 | 5 |
| `backend/src/qts/backtest/config.py:148` | `method` | `qts.backtest.config.BacktestStrategyConfig.to_payload` | 未写 docstring；静态推断为转换或序列化为指定目标表示（名称：to payload）。 | 0 | 1 |
| `backend/src/qts/backtest/config.py:159` | `classmethod` | `qts.backtest.config.BacktestStrategyConfig._parse_payload` | 未写 docstring；静态推断为所属类上的 `parse payload` 行为。 | 0 | 14 |
| `backend/src/qts/backtest/config.py:178` | `class` | `qts.backtest.config.BacktestRunConfig` | Complete identity for a backtest run. | 1 | 10 |
| `backend/src/qts/backtest/config.py:202` | `method` | `qts.backtest.config.BacktestRunConfig.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 4 | 50 |
| `backend/src/qts/backtest/config.py:267` | `classmethod` | `qts.backtest.config.BacktestRunConfig.from_yaml` | 未写 docstring；静态推断为从指定来源构造或转换对象（名称：from yaml）。 | 7 | 64 |
| `backend/src/qts/backtest/config.py:340` | `property` | `qts.backtest.config.BacktestRunConfig.config_hash` | 未写 docstring；静态推断为所属类上的 `config hash` 行为。 | 2 | 2 |
| `backend/src/qts/backtest/config.py:343` | `method` | `qts.backtest.config.BacktestRunConfig.to_payload` | 未写 docstring；静态推断为转换或序列化为指定目标表示（名称：to payload）。 | 0 | 14 |
| `backend/src/qts/backtest/config.py:374` | `staticmethod` | `qts.backtest.config.BacktestRunConfig._parse_datetime` | 未写 docstring；静态推断为所属类上的 `parse datetime` 行为。 | 0 | 5 |
| `backend/src/qts/backtest/config.py:384` | `staticmethod` | `qts.backtest.config.BacktestRunConfig._normalize_symbol` | 未写 docstring；静态推断为所属类上的 `normalize symbol` 行为。 | 0 | 3 |
| `backend/src/qts/backtest/config.py:391` | `staticmethod` | `qts.backtest.config.BacktestRunConfig._parse_market_data_reference` | 未写 docstring；静态推断为所属类上的 `parse market data reference` 行为。 | 1 | 9 |
| `backend/src/qts/backtest/config.py:403` | `staticmethod` | `qts.backtest.config.BacktestRunConfig._parse_historical_data_reference` | 未写 docstring；静态推断为所属类上的 `parse historical data reference` 行为。 | 1 | 9 |
| `backend/src/qts/backtest/config.py:415` | `staticmethod` | `qts.backtest.config.BacktestRunConfig._stable_hash` | 未写 docstring；静态推断为所属类上的 `stable hash` 行为。 | 0 | 4 |
| `backend/src/qts/backtest/engine.py:68` | `class` | `qts.backtest.engine.BacktestCostModel` | Explicit simulation cost assumptions included in reports. | 0 | 3 |
| `backend/src/qts/backtest/engine.py:75` | `method` | `qts.backtest.engine.BacktestCostModel.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 6 |
| `backend/src/qts/backtest/engine.py:83` | `method` | `qts.backtest.engine.BacktestCostModel.to_payload` | 未写 docstring；静态推断为转换或序列化为指定目标表示（名称：to payload）。 | 0 | 2 |
| `backend/src/qts/backtest/engine.py:91` | `property` | `qts.backtest.engine.BacktestCostModel.slippage_model` | 未写 docstring；静态推断为所属类上的 `slippage model` 行为。 | 0 | 1 |
| `backend/src/qts/backtest/engine.py:95` | `property` | `qts.backtest.engine.BacktestCostModel.commission_model` | 未写 docstring；静态推断为所属类上的 `commission model` 行为。 | 0 | 1 |
| `backend/src/qts/backtest/engine.py:102` | `class` | `qts.backtest.engine.BacktestStreamResult` | Backtest result written to partitioned streaming artifacts. | 0 | 1 |
| `backend/src/qts/backtest/engine.py:121` | `class` | `qts.backtest.engine.BacktestEngine` | Single-process backtest engine using the Strategy SDK and actor order flow. | 0 | 0 |
| `backend/src/qts/backtest/engine.py:125` | `class` | `qts.backtest.engine.BacktestEngine._ProcessedIntent` | 未写 docstring；静态推断为定义 Processed Intent 概念或数据结构。 | 0 | 1 |
| `backend/src/qts/backtest/engine.py:130` | `class` | `qts.backtest.engine.BacktestEngine._RuntimeRunResult` | 未写 docstring；静态推断为定义 Runtime Run Result 概念或数据结构。 | 0 | 1 |
| `backend/src/qts/backtest/engine.py:137` | `property` | `qts.backtest.engine.BacktestEngine._RuntimeRunResult.processed_bars` | 未写 docstring；静态推断为所属类上的 `processed bars` 行为。 | 0 | 0 |
| `backend/src/qts/backtest/engine.py:140` | `class` | `qts.backtest.engine.BacktestEngine._StreamingBacktestSink` | 未写 docstring；静态推断为定义 Streaming Backtest Sink 概念或数据结构。 | 0 | 0 |
| `backend/src/qts/backtest/engine.py:141` | `method` | `qts.backtest.engine.BacktestEngine._StreamingBacktestSink.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 0 | 0 |
| `backend/src/qts/backtest/engine.py:146` | `property` | `qts.backtest.engine.BacktestEngine._StreamingBacktestSink.order_count` | 未写 docstring；静态推断为所属类上的 `order count` 行为。 | 0 | 0 |
| `backend/src/qts/backtest/engine.py:149` | `method` | `qts.backtest.engine.BacktestEngine._StreamingBacktestSink.write_processed` | 未写 docstring；静态推断为写入数据（名称：write processed）。 | 0 | 7 |
| `backend/src/qts/backtest/engine.py:164` | `method` | `qts.backtest.engine.BacktestEngine._StreamingBacktestSink.write_equity_point` | 未写 docstring；静态推断为写入数据（名称：write equity point）。 | 0 | 1 |
| `backend/src/qts/backtest/engine.py:167` | `method` | `qts.backtest.engine.BacktestEngine.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 3 | 11 |
| `backend/src/qts/backtest/engine.py:209` | `classmethod` | `qts.backtest.engine.BacktestEngine.from_config` | 未写 docstring；静态推断为从指定来源构造或转换对象（名称：from config）。 | 3 | 5 |
| `backend/src/qts/backtest/engine.py:244` | `staticmethod` | `qts.backtest.engine.BacktestEngine._take_strategy_bar_result` | 未写 docstring；静态推断为所属类上的 `take strategy bar result` 行为。 | 0 | 8 |
| `backend/src/qts/backtest/engine.py:255` | `staticmethod` | `qts.backtest.engine.BacktestEngine._take_signal_batch` | 未写 docstring；静态推断为所属类上的 `take signal batch` 行为。 | 0 | 8 |
| `backend/src/qts/backtest/engine.py:266` | `staticmethod` | `qts.backtest.engine.BacktestEngine._take_strategy_finalized` | 未写 docstring；静态推断为所属类上的 `take strategy finalized` 行为。 | 0 | 8 |
| `backend/src/qts/backtest/engine.py:276` | `method` | `qts.backtest.engine.BacktestEngine._market_data_ref_for` | 未写 docstring；静态推断为所属类上的 `market data ref for` 行为。 | 3 | 5 |
| `backend/src/qts/backtest/engine.py:308` | `method` | `qts.backtest.engine.BacktestEngine._run_actor_loop` | 未写 docstring；静态推断为所属类上的 `run actor loop` 行为。 | 24 | 67 |
| `backend/src/qts/backtest/engine.py:457` | `method` | `qts.backtest.engine.BacktestEngine.run_streaming` | 未写 docstring；静态推断为运行流程或命令（名称：run streaming）。 | 8 | 13 |
| `backend/src/qts/backtest/engine.py:504` | `method` | `qts.backtest.engine.BacktestEngine._process_intent` | 未写 docstring；静态推断为所属类上的 `process intent` 行为。 | 7 | 24 |
| `backend/src/qts/backtest/engine.py:584` | `method` | `qts.backtest.engine.BacktestEngine._process_order_delta` | 未写 docstring；静态推断为所属类上的 `process order delta` 行为。 | 4 | 18 |
| `backend/src/qts/backtest/engine.py:638` | `method` | `qts.backtest.engine.BacktestEngine._order_instrument_for_intent` | 未写 docstring；静态推断为所属类上的 `order instrument for intent` 行为。 | 0 | 2 |
| `backend/src/qts/backtest/engine.py:648` | `method` | `qts.backtest.engine.BacktestEngine._market_price_for_intent` | 未写 docstring；静态推断为所属类上的 `market price for intent` 行为。 | 0 | 2 |
| `backend/src/qts/backtest/engine.py:666` | `staticmethod` | `qts.backtest.engine.BacktestEngine._desired_quantity` | 未写 docstring；静态推断为所属类上的 `desired quantity` 行为。 | 0 | 4 |
| `backend/src/qts/backtest/engine.py:686` | `method` | `qts.backtest.engine.BacktestEngine._update_rolling_prices` | 未写 docstring；静态推断为所属类上的 `update rolling prices` 行为。 | 0 | 3 |
| `backend/src/qts/backtest/engine.py:709` | `method` | `qts.backtest.engine.BacktestEngine._related_contracts_for` | 未写 docstring；静态推断为所属类上的 `related contracts for` 行为。 | 0 | 4 |
| `backend/src/qts/backtest/engine.py:722` | `method` | `qts.backtest.engine.BacktestEngine._portfolio_view` | 未写 docstring；静态推断为所属类上的 `portfolio view` 行为。 | 3 | 9 |
| `backend/src/qts/backtest/engine.py:745` | `method` | `qts.backtest.engine.BacktestEngine._equity_point` | 未写 docstring；静态推断为所属类上的 `equity point` 行为。 | 2 | 2 |
| `backend/src/qts/backtest/engine.py:760` | `method` | `qts.backtest.engine.BacktestEngine._instrument_registry_for` | 未写 docstring；静态推断为所属类上的 `instrument registry for` 行为。 | 6 | 12 |
| `backend/src/qts/backtest/engine.py:794` | `staticmethod` | `qts.backtest.engine.BacktestEngine._history_limit_from_subscriptions` | 未写 docstring；静态推断为所属类上的 `history limit from subscriptions` 行为。 | 0 | 1 |
| `backend/src/qts/backtest/engine.py:799` | `method` | `qts.backtest.engine.BacktestEngine._multiplier_for` | 未写 docstring；静态推断为所属类上的 `multiplier for` 行为。 | 0 | 2 |
| `backend/src/qts/backtest/engine.py:803` | `staticmethod` | `qts.backtest.engine.BacktestEngine._symbol_for` | 未写 docstring；静态推断为所属类上的 `symbol for` 行为。 | 0 | 1 |
| `backend/src/qts/backtest/engine.py:807` | `staticmethod` | `qts.backtest.engine.BacktestEngine._exchange_for` | 未写 docstring；静态推断为所属类上的 `exchange for` 行为。 | 0 | 2 |
| `backend/src/qts/backtest/engine.py:814` | `staticmethod` | `qts.backtest.engine.BacktestEngine._ledger_rows` | 未写 docstring；静态推断为所属类上的 `ledger rows` 行为。 | 1 | 2 |
| `backend/src/qts/backtest/engine.py:831` | `staticmethod` | `qts.backtest.engine.BacktestEngine._order_payload` | 未写 docstring；静态推断为所属类上的 `order payload` 行为。 | 0 | 1 |
| `backend/src/qts/backtest/engine.py:842` | `staticmethod` | `qts.backtest.engine.BacktestEngine._fill_payload` | 未写 docstring；静态推断为所属类上的 `fill payload` 行为。 | 0 | 4 |
| `backend/src/qts/backtest/engine.py:855` | `staticmethod` | `qts.backtest.engine.BacktestEngine._dataset_payload` | 未写 docstring；静态推断为所属类上的 `dataset payload` 行为。 | 0 | 1 |
| `backend/src/qts/backtest/engine.py:869` | `staticmethod` | `qts.backtest.engine.BacktestEngine._stable_hash` | 未写 docstring；静态推断为所属类上的 `stable hash` 行为。 | 0 | 4 |
| `backend/src/qts/backtest/engine.py:874` | `staticmethod` | `qts.backtest.engine.BacktestEngine._zero_time` | 未写 docstring；静态推断为所属类上的 `zero time` 行为。 | 0 | 1 |
| `backend/src/qts/backtest/engine.py:880` | `class` | `qts.backtest.engine._BacktestExecutionAdapter` | 未写 docstring；静态推断为定义 Backtest Execution Adapter 概念或数据结构。 | 0 | 0 |
| `backend/src/qts/backtest/engine.py:881` | `method` | `qts.backtest.engine._BacktestExecutionAdapter.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 0 | 0 |
| `backend/src/qts/backtest/engine.py:884` | `method` | `qts.backtest.engine._BacktestExecutionAdapter.execute_market_order` | 未写 docstring；静态推断为所属类上的 `execute market order` 行为。 | 1 | 5 |
| `backend/src/qts/backtest/historical_data_portal.py:13` | `class` | `qts.backtest.historical_data_portal.HistoricalDataPortal` | Returns finalized bars visible as of a replay timestamp. | 0 | 0 |
| `backend/src/qts/backtest/historical_data_portal.py:16` | `method` | `qts.backtest.historical_data_portal.HistoricalDataPortal.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 0 | 3 |
| `backend/src/qts/backtest/historical_data_portal.py:22` | `method` | `qts.backtest.historical_data_portal.HistoricalDataPortal.data_view` | 未写 docstring；静态推断为所属类上的 `data view` 行为。 | 1 | 1 |
| `backend/src/qts/backtest/historical_data_portal.py:25` | `method` | `qts.backtest.historical_data_portal.HistoricalDataPortal.history` | 未写 docstring；静态推断为所属类上的 `history` 行为。 | 1 | 2 |
| `backend/src/qts/backtest/inputs.py:22` | `class` | `qts.backtest.inputs.BacktestInputBundle` | Streaming inputs and side-channel metadata required by a backtest run. | 0 | 1 |
| `backend/src/qts/backtest/inputs.py:34` | `class` | `qts.backtest.inputs.BacktestInputBuilder` | Build replay-ready market data, registry, and provenance inputs. | 0 | 0 |
| `backend/src/qts/backtest/inputs.py:37` | `method` | `qts.backtest.inputs.BacktestInputBuilder.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 0 | 0 |
| `backend/src/qts/backtest/inputs.py:41` | `method` | `qts.backtest.inputs.BacktestInputBuilder.build` | 未写 docstring；静态推断为组装对象、请求或运行上下文（名称：build）。 | 6 | 6 |
| `backend/src/qts/backtest/inputs.py:60` | `method` | `qts.backtest.inputs.BacktestInputBuilder._roll_registry` | 未写 docstring；静态推断为所属类上的 `roll registry` 行为。 | 1 | 2 |
| `backend/src/qts/backtest/inputs.py:65` | `method` | `qts.backtest.inputs.BacktestInputBuilder._stream_configured_bars` | 未写 docstring；静态推断为所属类上的 `stream configured bars` 行为。 | 5 | 16 |
| `backend/src/qts/backtest/inputs.py:131` | `method` | `qts.backtest.inputs.BacktestInputBuilder._iter_root_bars` | 未写 docstring；静态推断为所属类上的 `iter root bars` 行为。 | 1 | 7 |
| `backend/src/qts/backtest/inputs.py:170` | `staticmethod` | `qts.backtest.inputs.BacktestInputBuilder._merge_ordered_bar_streams` | 未写 docstring；静态推断为所属类上的 `merge ordered bar streams` 行为。 | 0 | 5 |
| `backend/src/qts/backtest/inputs.py:193` | `staticmethod` | `qts.backtest.inputs.BacktestInputBuilder._record_exchange_timezone` | 未写 docstring；静态推断为所属类上的 `record exchange timezone` 行为。 | 0 | 1 |
| `backend/src/qts/backtest/inputs.py:203` | `staticmethod` | `qts.backtest.inputs.BacktestInputBuilder._exchange_timezone_for` | 未写 docstring；静态推断为所属类上的 `exchange timezone for` 行为。 | 0 | 0 |
| `backend/src/qts/backtest/inputs.py:210` | `method` | `qts.backtest.inputs.BacktestInputBuilder._instrument_registry_for` | 未写 docstring；静态推断为所属类上的 `instrument registry for` 行为。 | 2 | 14 |
| `backend/src/qts/backtest/inputs.py:264` | `staticmethod` | `qts.backtest.inputs.BacktestInputBuilder._instrument_for` | 未写 docstring；静态推断为所属类上的 `instrument for` 行为。 | 2 | 3 |
| `backend/src/qts/backtest/inputs.py:288` | `method` | `qts.backtest.inputs.BacktestInputBuilder._dataset_metadata` | 未写 docstring；静态推断为所属类上的 `dataset metadata` 行为。 | 2 | 6 |
| `backend/src/qts/backtest/inputs.py:311` | `staticmethod` | `qts.backtest.inputs.BacktestInputBuilder._dataset_instrument_id` | 未写 docstring；静态推断为所属类上的 `dataset instrument id` 行为。 | 1 | 2 |
| `backend/src/qts/backtest/inputs.py:316` | `method` | `qts.backtest.inputs.BacktestInputBuilder._contract_multipliers_for` | 未写 docstring；静态推断为所属类上的 `contract multipliers for` 行为。 | 0 | 1 |
| `backend/src/qts/backtest/report.py:15` | `class` | `qts.backtest.report.EquityCurvePoint` | One timestamped equity observation. | 0 | 1 |
| `backend/src/qts/backtest/report.py:23` | `class` | `qts.backtest.report.TradeLedgerEntry` | Auditable row for a simulated fill. | 0 | 1 |
| `backend/src/qts/backtest/report.py:37` | `module_function` | `qts.backtest.report._stable_hash` | 未写 docstring；静态推断为 `stable hash` 函数，具体语义以实现为准。 | 0 | 4 |
| `backend/src/qts/backtest/report.py:47` | `module_function` | `qts.backtest.report._json_default` | 未写 docstring；静态推断为 `json default` 函数，具体语义以实现为准。 | 0 | 8 |
| `backend/src/qts/backtest/report.py:57` | `class` | `qts.backtest.report.StreamingEquityMetrics` | Incremental metrics for a streamed equity curve. | 0 | 0 |
| `backend/src/qts/backtest/report.py:60` | `method` | `qts.backtest.report.StreamingEquityMetrics.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 0 | 1 |
| `backend/src/qts/backtest/report.py:67` | `method` | `qts.backtest.report.StreamingEquityMetrics.update` | 未写 docstring；静态推断为所属类上的 `update` 行为。 | 0 | 3 |
| `backend/src/qts/backtest/report.py:83` | `method` | `qts.backtest.report.StreamingEquityMetrics.to_payload` | 未写 docstring；静态推断为转换或序列化为指定目标表示（名称：to payload）。 | 0 | 1 |
| `backend/src/qts/backtest/report.py:94` | `class` | `qts.backtest.report.StreamingBacktestArtifacts` | Final paths and row counts for streamed backtest artifacts. | 0 | 1 |
| `backend/src/qts/backtest/report.py:103` | `class` | `qts.backtest.report._NdjsonArtifact` | 未写 docstring；静态推断为定义 Ndjson Artifact 概念或数据结构。 | 0 | 0 |
| `backend/src/qts/backtest/report.py:104` | `method` | `qts.backtest.report._NdjsonArtifact.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 0 | 2 |
| `backend/src/qts/backtest/report.py:110` | `method` | `qts.backtest.report._NdjsonArtifact.write` | 未写 docstring；静态推断为写入数据（名称：write）。 | 0 | 4 |
| `backend/src/qts/backtest/report.py:124` | `method` | `qts.backtest.report._NdjsonArtifact.close` | 未写 docstring；静态推断为关闭资源或头寸（名称：close）。 | 0 | 1 |
| `backend/src/qts/backtest/report.py:128` | `property` | `qts.backtest.report._NdjsonArtifact.content_hash` | 未写 docstring；静态推断为所属类上的 `content hash` 行为。 | 0 | 1 |
| `backend/src/qts/backtest/report.py:132` | `class` | `qts.backtest.report.StreamingBacktestArtifactWriter` | Write large backtest outputs as line-delimited artifacts. | 0 | 0 |
| `backend/src/qts/backtest/report.py:137` | `method` | `qts.backtest.report.StreamingBacktestArtifactWriter.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 2 | 3 |
| `backend/src/qts/backtest/report.py:146` | `method` | `qts.backtest.report.StreamingBacktestArtifactWriter.write_order` | 未写 docstring；静态推断为写入数据（名称：write order）。 | 0 | 1 |
| `backend/src/qts/backtest/report.py:149` | `method` | `qts.backtest.report.StreamingBacktestArtifactWriter.write_fill` | 未写 docstring；静态推断为写入数据（名称：write fill）。 | 0 | 1 |
| `backend/src/qts/backtest/report.py:152` | `method` | `qts.backtest.report.StreamingBacktestArtifactWriter.write_trade_ledger` | 未写 docstring；静态推断为写入数据（名称：write trade ledger）。 | 0 | 1 |
| `backend/src/qts/backtest/report.py:167` | `method` | `qts.backtest.report.StreamingBacktestArtifactWriter.write_equity_point` | 未写 docstring；静态推断为写入数据（名称：write equity point）。 | 0 | 2 |
| `backend/src/qts/backtest/report.py:171` | `method` | `qts.backtest.report.StreamingBacktestArtifactWriter.finalize` | 未写 docstring；静态推断为所属类上的 `finalize` 行为。 | 2 | 14 |
| `backend/src/qts/backtest/runner.py:23` | `class` | `qts.backtest.runner.BacktestRun` | Output of a backtest runner invocation. | 0 | 1 |
| `backend/src/qts/backtest/runner.py:33` | `property` | `qts.backtest.runner.BacktestRun.processed_bars` | 未写 docstring；静态推断为所属类上的 `processed bars` 行为。 | 0 | 0 |
| `backend/src/qts/backtest/runner.py:37` | `property` | `qts.backtest.runner.BacktestRun.report_hash` | 未写 docstring；静态推断为所属类上的 `report hash` 行为。 | 0 | 0 |
| `backend/src/qts/backtest/runner.py:41` | `module_function` | `qts.backtest.runner.run_backtest` | Run a backtest and write partitioned streaming artifacts. | 9 | 14 |
| `backend/src/qts/backtest/runner.py:84` | `module_function` | `qts.backtest.runner._catalog_load_config` | 未写 docstring；静态推断为 `catalog load config` 函数，具体语义以实现为准。 | 2 | 4 |
| `backend/src/qts/backtest/runner.py:105` | `module_function` | `qts.backtest.runner._load_strategy` | 未写 docstring；静态推断为 `load strategy` 函数，具体语义以实现为准。 | 0 | 14 |
| `backend/src/qts/backtest/runner.py:126` | `module_function` | `qts.backtest.runner._streaming_summary_payload` | 未写 docstring；静态推断为 `streaming summary payload` 函数，具体语义以实现为准。 | 0 | 10 |
| `backend/src/qts/config/ibkr.py:13` | `class` | `qts.config.ibkr.IbkrConnectionConfig` | IBKR connection settings for one boundary. | 0 | 1 |
| `backend/src/qts/config/ibkr.py:20` | `method` | `qts.config.ibkr.IbkrConnectionConfig.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 4 |
| `backend/src/qts/config/ibkr.py:30` | `class` | `qts.config.ibkr.IbkrOrderExecutionConfig` | IBKR order execution settings. | 0 | 1 |
| `backend/src/qts/config/ibkr.py:36` | `method` | `qts.config.ibkr.IbkrOrderExecutionConfig.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 5 |
| `backend/src/qts/config/ibkr.py:45` | `class` | `qts.config.ibkr.IbkrSecretRefs` | Environment variable names for IBKR credentials. | 0 | 1 |
| `backend/src/qts/config/ibkr.py:51` | `method` | `qts.config.ibkr.IbkrSecretRefs.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 4 |
| `backend/src/qts/config/ibkr.py:59` | `class` | `qts.config.ibkr.IbkrEnvironmentConfig` | IBKR runtime configuration split by external boundary. | 0 | 1 |
| `backend/src/qts/config/ibkr.py:68` | `module_function` | `qts.config.ibkr.validate_ibkr_environment` | Validate paper/live separation without exposing secret values. | 1 | 14 |
| `backend/src/qts/config/ibkr.py:100` | `module_function` | `qts.config.ibkr._contains_paper_reference` | 未写 docstring；静态推断为 `contains paper reference` 函数，具体语义以实现为准。 | 0 | 1 |
| `backend/src/qts/core/ids.py:9` | `class` | `qts.core.ids._StringId` | Base class for typed string identifiers. | 0 | 1 |
| `backend/src/qts/core/ids.py:14` | `method` | `qts.core.ids._StringId.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 4 |
| `backend/src/qts/core/ids.py:21` | `method` | `qts.core.ids._StringId.__str__` | 未写 docstring；实现 Python 协议方法 `__str__`。 | 0 | 0 |
| `backend/src/qts/core/ids.py:25` | `class` | `qts.core.ids.AccountId` | Stable internal account identifier. | 0 | 0 |
| `backend/src/qts/core/ids.py:29` | `class` | `qts.core.ids.StrategyId` | Stable internal strategy identifier. | 0 | 0 |
| `backend/src/qts/core/ids.py:33` | `class` | `qts.core.ids.InstrumentId` | Stable internal instrument identifier. | 0 | 0 |
| `backend/src/qts/core/ids.py:37` | `class` | `qts.core.ids.OrderId` | Stable internal order identifier. | 0 | 0 |
| `backend/src/qts/core/ids.py:41` | `class` | `qts.core.ids.BrokerId` | Stable internal broker identifier. | 0 | 0 |
| `backend/src/qts/core/ids.py:45` | `class` | `qts.core.ids.EventId` | Stable internal event identifier. | 0 | 0 |
| `backend/src/qts/core/ids.py:49` | `class` | `qts.core.ids.BacktestRunId` | Stable identifier for a backtest run. | 0 | 0 |
| `backend/src/qts/core/ids.py:53` | `class` | `qts.core.ids.CorrelationId` | Identifier grouping events in one business workflow. | 0 | 0 |
| `backend/src/qts/core/ids.py:57` | `class` | `qts.core.ids.CausationId` | Identifier linking an event to the event that caused it. | 0 | 0 |
| `backend/src/qts/core/time.py:10` | `module_function` | `qts.core.time.require_aware_datetime` | Validate that a datetime has an effective timezone. | 0 | 2 |
| `backend/src/qts/core/time.py:17` | `module_function` | `qts.core.time.to_exchange_time` | Convert a timestamp representation into an exchange timezone. | 1 | 4 |
| `backend/src/qts/core/time.py:28` | `class` | `qts.core.time.TimeInterval` | A half-open time interval with `[start, end)` membership. | 0 | 1 |
| `backend/src/qts/core/time.py:34` | `method` | `qts.core.time.TimeInterval.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 1 | 3 |
| `backend/src/qts/core/time.py:41` | `property` | `qts.core.time.TimeInterval.duration` | 未写 docstring；静态推断为所属类上的 `duration` 行为。 | 0 | 0 |
| `backend/src/qts/core/time.py:44` | `method` | `qts.core.time.TimeInterval.contains` | 未写 docstring；静态推断为所属类上的 `contains` 行为。 | 1 | 1 |
| `backend/src/qts/data/adapters/ibkr_market_data.py:15` | `class` | `qts.data.adapters.ibkr_market_data.IbkrMarketDataConnection` | IBKR market data connection settings. | 0 | 1 |
| `backend/src/qts/data/adapters/ibkr_market_data.py:23` | `method` | `qts.data.adapters.ibkr_market_data.IbkrMarketDataConnection.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 6 |
| `backend/src/qts/data/adapters/ibkr_market_data.py:35` | `class` | `qts.data.adapters.ibkr_market_data.IbkrMarketDataSubscription` | IBKR market data subscription request at the adapter boundary. | 0 | 1 |
| `backend/src/qts/data/adapters/ibkr_market_data.py:43` | `class` | `qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter` | Normalizes IBKR market data without owning order execution. | 0 | 0 |
| `backend/src/qts/data/adapters/ibkr_market_data.py:46` | `method` | `qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 0 | 0 |
| `backend/src/qts/data/adapters/ibkr_market_data.py:55` | `method` | `qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter.subscription_for` | 未写 docstring；静态推断为所属类上的 `subscription for` 行为。 | 1 | 2 |
| `backend/src/qts/data/adapters/ibkr_market_data.py:62` | `method` | `qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter.normalize_tick` | 未写 docstring；静态推断为所属类上的 `normalize tick` 行为。 | 1 | 2 |
| `backend/src/qts/data/adapters/ibkr_market_data.py:77` | `method` | `qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter.normalize_quote` | 未写 docstring；静态推断为所属类上的 `normalize quote` 行为。 | 1 | 2 |
| `backend/src/qts/data/adapters/ibkr_market_data.py:96` | `method` | `qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter.normalize_bar` | 未写 docstring；静态推断为所属类上的 `normalize bar` 行为。 | 1 | 2 |
| `backend/src/qts/data/bars/aggregator.py:18` | `class` | `qts.data.bars.aggregator.AggregationState` | Current in-progress aggregation bucket. | 0 | 1 |
| `backend/src/qts/data/bars/aggregator.py:27` | `property` | `qts.data.bars.aggregator.AggregationState.aggregate_end` | 未写 docstring；静态推断为所属类上的 `aggregate end` 行为。 | 0 | 0 |
| `backend/src/qts/data/bars/aggregator.py:32` | `class` | `qts.data.bars.aggregator.AggregationResult` | Result returned by one incremental aggregator update. | 0 | 1 |
| `backend/src/qts/data/bars/aggregator.py:39` | `class` | `qts.data.bars.aggregator.BarAggregator` | Stateful incremental bar aggregator for one ordered bar stream. | 0 | 0 |
| `backend/src/qts/data/bars/aggregator.py:42` | `method` | `qts.data.bars.aggregator.BarAggregator.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 0 | 1 |
| `backend/src/qts/data/bars/aggregator.py:56` | `method` | `qts.data.bars.aggregator.BarAggregator.update` | Add a lower-timeframe bar and return any completed aggregate bars. | 6 | 11 |
| `backend/src/qts/data/bars/aggregator.py:85` | `method` | `qts.data.bars.aggregator.BarAggregator.finish` | Flush the current bucket as a partial aggregate when present. | 2 | 3 |
| `backend/src/qts/data/bars/aggregator.py:94` | `method` | `qts.data.bars.aggregator.BarAggregator._new_state_for` | 未写 docstring；静态推断为所属类上的 `new state for` 行为。 | 3 | 3 |
| `backend/src/qts/data/bars/aggregator.py:107` | `module_function` | `qts.data.bars.aggregator.aggregate_bars` | Aggregate bars into a higher clock-aligned timeframe. | 1 | 9 |
| `backend/src/qts/data/bars/aggregator.py:136` | `module_function` | `qts.data.bars.aggregator._bar_inside_session` | 未写 docstring；静态推断为 `bar inside session` 函数，具体语义以实现为准。 | 0 | 1 |
| `backend/src/qts/data/bars/aggregator.py:140` | `module_function` | `qts.data.bars.aggregator._same_stream_bucket` | 未写 docstring；静态推断为 `same stream bucket` 函数，具体语义以实现为准。 | 0 | 0 |
| `backend/src/qts/data/bars/aggregator.py:148` | `module_function` | `qts.data.bars.aggregator._aggregate_state` | 未写 docstring；静态推断为 `aggregate state` 函数，具体语义以实现为准。 | 4 | 13 |
| `backend/src/qts/data/bars/aggregator.py:188` | `module_function` | `qts.data.bars.aggregator._aggregate_vwap` | 未写 docstring；静态推断为 `aggregate vwap` 函数，具体语义以实现为准。 | 0 | 4 |
| `backend/src/qts/data/bars/aggregator.py:197` | `module_function` | `qts.data.bars.aggregator._last_open_interest` | 未写 docstring；静态推断为 `last open interest` 函数，具体语义以实现为准。 | 0 | 1 |
| `backend/src/qts/data/bars/aggregator.py:204` | `module_function` | `qts.data.bars.aggregator._sum_trade_count` | 未写 docstring；静态推断为 `sum trade count` 函数，具体语义以实现为准。 | 0 | 1 |
| `backend/src/qts/data/bars/alignment.py:11` | `module_function` | `qts.data.bars.alignment.clock_bucket_for` | Return the exchange-clock bucket containing ``timestamp``. | 3 | 7 |
| `backend/src/qts/data/bars/alignment.py:36` | `module_function` | `qts.data.bars.alignment._duration_seconds` | 未写 docstring；静态推断为 `duration seconds` 函数，具体语义以实现为准。 | 0 | 4 |
| `backend/src/qts/data/bars/timeframe.py:10` | `class` | `qts.data.bars.timeframe.AlignmentMode` | How bars for a timeframe align to time. | 0 | 0 |
| `backend/src/qts/data/bars/timeframe.py:29` | `class` | `qts.data.bars.timeframe.Timeframe` | Bar timeframe with explicit alignment semantics. | 0 | 1 |
| `backend/src/qts/data/bars/timeframe.py:37` | `classmethod` | `qts.data.bars.timeframe.Timeframe.parse` | 未写 docstring；静态推断为解析外部表示（名称：parse）。 | 0 | 5 |
| `backend/src/qts/data/bars/timeframe.py:49` | `method` | `qts.data.bars.timeframe.Timeframe.__str__` | 未写 docstring；实现 Python 协议方法 `__str__`。 | 0 | 0 |
| `backend/src/qts/data/feeds/replay_feed.py:12` | `class` | `qts.data.feeds.replay_feed.ReplayFeed` | Deterministic replay feed over stored bars. | 0 | 0 |
| `backend/src/qts/data/feeds/replay_feed.py:15` | `method` | `qts.data.feeds.replay_feed.ReplayFeed.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 0 | 0 |
| `backend/src/qts/data/feeds/replay_feed.py:18` | `method` | `qts.data.feeds.replay_feed.ReplayFeed.events` | 未写 docstring；静态推断为所属类上的 `events` 行为。 | 0 | 1 |
| `backend/src/qts/data/historical/catalog.py:19` | `class` | `qts.data.historical.catalog.HistoricalDataset` | One local historical dataset entry. | 0 | 1 |
| `backend/src/qts/data/historical/catalog.py:34` | `staticmethod` | `qts.data.historical.catalog.HistoricalDataset.normalize_root` | 未写 docstring；静态推断为所属类上的 `normalize root` 行为。 | 0 | 3 |
| `backend/src/qts/data/historical/catalog.py:42` | `class` | `qts.data.historical.catalog.HistoricalCatalog` | Explicit catalog for a local historical data layout. | 0 | 1 |
| `backend/src/qts/data/historical/catalog.py:50` | `classmethod` | `qts.data.historical.catalog.HistoricalCatalog.load` | Load a catalog from one cohesive construction config. | 4 | 6 |
| `backend/src/qts/data/historical/catalog.py:79` | `classmethod` | `qts.data.historical.catalog.HistoricalCatalog.from_legacy_root` | Load requested roots from a local historical data directory. | 5 | 14 |
| `backend/src/qts/data/historical/catalog.py:123` | `classmethod` | `qts.data.historical.catalog.HistoricalCatalog.from_historical_data_config` | Load requested roots from a project-level historical data catalog. | 5 | 17 |
| `backend/src/qts/data/historical/catalog.py:185` | `classmethod` | `qts.data.historical.catalog.HistoricalCatalog._symbol_resolvers_for_load_config` | 未写 docstring；静态推断为所属类上的 `symbol resolvers for load config` 行为。 | 2 | 2 |
| `backend/src/qts/data/historical/catalog.py:204` | `staticmethod` | `qts.data.historical.catalog.HistoricalCatalog._chain_path_exists` | 未写 docstring；静态推断为所属类上的 `chain path exists` 行为。 | 0 | 4 |
| `backend/src/qts/data/historical/catalog.py:220` | `staticmethod` | `qts.data.historical.catalog.HistoricalCatalog._require_file` | 未写 docstring；静态推断为所属类上的 `require file` 行为。 | 0 | 4 |
| `backend/src/qts/data/historical/catalog.py:230` | `class` | `qts.data.historical.catalog.HistoricalCatalogLoadConfig` | Construction inputs for a configured historical catalog. | 0 | 2 |
| `backend/src/qts/data/historical/catalog.py:240` | `method` | `qts.data.historical.catalog.HistoricalCatalogLoadConfig.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 2 | 22 |
| `backend/src/qts/data/historical/catalog.py:281` | `classmethod` | `qts.data.historical.catalog.HistoricalCatalogLoadConfig.from_legacy_root` | 未写 docstring；静态推断为从指定来源构造或转换对象（名称：from legacy root）。 | 0 | 1 |
| `backend/src/qts/data/historical/catalog.py:297` | `classmethod` | `qts.data.historical.catalog.HistoricalCatalogLoadConfig.from_historical_data_config` | 未写 docstring；静态推断为从指定来源构造或转换对象（名称：from historical data config）。 | 0 | 1 |
| `backend/src/qts/data/historical/catalog.py:315` | `staticmethod` | `qts.data.historical.catalog.HistoricalCatalogLoadConfig._normalize_symbol` | 未写 docstring；静态推断为所属类上的 `normalize symbol` 行为。 | 0 | 3 |
| `backend/src/qts/data/historical/chains.py:16` | `class` | `qts.data.historical.chains.HistoricalContract` | One outright contract from a historical chain file. | 0 | 1 |
| `backend/src/qts/data/historical/chains.py:31` | `class` | `qts.data.historical.chains.HistoricalChain` | Parsed historical futures chain. | 0 | 2 |
| `backend/src/qts/data/historical/chains.py:44` | `method` | `qts.data.historical.chains.HistoricalChain.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 2 |
| `backend/src/qts/data/historical/chains.py:54` | `method` | `qts.data.historical.chains.HistoricalChain.contract_for_symbol` | 未写 docstring；静态推断为所属类上的 `contract for symbol` 行为。 | 0 | 1 |
| `backend/src/qts/data/historical/chains.py:60` | `method` | `qts.data.historical.chains.HistoricalChain.is_outright_symbol` | 未写 docstring；静态推断为判断布尔条件（名称：is outright symbol）。 | 0 | 0 |
| `backend/src/qts/data/historical/chains.py:63` | `method` | `qts.data.historical.chains.HistoricalChain.instrument_id_for_symbol` | 未写 docstring；静态推断为所属类上的 `instrument id for symbol` 行为。 | 2 | 3 |
| `backend/src/qts/data/historical/chains.py:69` | `classmethod` | `qts.data.historical.chains.HistoricalChain.load` | Load a historical futures chain JSON file into typed metadata. | 4 | 16 |
| `backend/src/qts/data/historical/chains.py:108` | `classmethod` | `qts.data.historical.chains.HistoricalChain._parse_contract` | 未写 docstring；静态推断为所属类上的 `parse contract` 行为。 | 2 | 13 |
| `backend/src/qts/data/historical/chains.py:138` | `staticmethod` | `qts.data.historical.chains.HistoricalChain._required_text` | 未写 docstring；静态推断为所属类上的 `required text` 行为。 | 0 | 4 |
| `backend/src/qts/data/historical/chains.py:145` | `staticmethod` | `qts.data.historical.chains.HistoricalChain._required_decimal` | 未写 docstring；静态推断为所属类上的 `required decimal` 行为。 | 0 | 5 |
| `backend/src/qts/data/historical/chains.py:154` | `staticmethod` | `qts.data.historical.chains.HistoricalChain._exchange_code` | 未写 docstring；静态推断为所属类上的 `exchange code` 行为。 | 0 | 2 |
| `backend/src/qts/data/historical/config.py:26` | `class` | `qts.data.historical.config.HistoricalDataStoreDefaults` | Default metadata applied to datasets and bars in one historical store. | 0 | 1 |
| `backend/src/qts/data/historical/config.py:34` | `method` | `qts.data.historical.config.HistoricalDataStoreDefaults.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 8 |
| `backend/src/qts/data/historical/config.py:46` | `class` | `qts.data.historical.config.HistoricalDataStoreConfig` | Project-level physical layout for a historical data store. | 0 | 4 |
| `backend/src/qts/data/historical/config.py:62` | `method` | `qts.data.historical.config.HistoricalDataStoreConfig.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 19 |
| `backend/src/qts/data/historical/config.py:82` | `method` | `qts.data.historical.config.HistoricalDataStoreConfig.bars_path` | 未写 docstring；静态推断为所属类上的 `bars path` 行为。 | 2 | 2 |
| `backend/src/qts/data/historical/config.py:86` | `method` | `qts.data.historical.config.HistoricalDataStoreConfig.chain_path` | 未写 docstring；静态推断为所属类上的 `chain path` 行为。 | 2 | 2 |
| `backend/src/qts/data/historical/config.py:90` | `method` | `qts.data.historical.config.HistoricalDataStoreConfig._join` | 未写 docstring；静态推断为所属类上的 `join` 行为。 | 0 | 1 |
| `backend/src/qts/data/historical/config.py:94` | `staticmethod` | `qts.data.historical.config.HistoricalDataStoreConfig._render_template` | 未写 docstring；静态推断为所属类上的 `render template` 行为。 | 0 | 3 |
| `backend/src/qts/data/historical/config.py:100` | `class` | `qts.data.historical.config.HistoricalBarFileConfig` | One physical bar file for a dataset. | 0 | 1 |
| `backend/src/qts/data/historical/config.py:110` | `method` | `qts.data.historical.config.HistoricalBarFileConfig.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 12 |
| `backend/src/qts/data/historical/config.py:126` | `class` | `qts.data.historical.config.HistoricalDatasetConfig` | One product/data entry inside a historical data catalog. | 0 | 1 |
| `backend/src/qts/data/historical/config.py:139` | `method` | `qts.data.historical.config.HistoricalDatasetConfig.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 16 |
| `backend/src/qts/data/historical/config.py:158` | `property` | `qts.data.historical.config.HistoricalDatasetConfig.requires_chain` | 未写 docstring；静态推断为所属类上的 `requires chain` 行为。 | 0 | 2 |
| `backend/src/qts/data/historical/config.py:162` | `staticmethod` | `qts.data.historical.config.HistoricalDatasetConfig.normalize_root` | 未写 docstring；静态推断为所属类上的 `normalize root` 行为。 | 0 | 3 |
| `backend/src/qts/data/historical/config.py:170` | `class` | `qts.data.historical.config.HistoricalDataCatalogConfig` | Logical catalog of historical datasets backed by one store. | 0 | 1 |
| `backend/src/qts/data/historical/config.py:177` | `method` | `qts.data.historical.config.HistoricalDataCatalogConfig.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 5 |
| `backend/src/qts/data/historical/config.py:187` | `class` | `qts.data.historical.config.HistoricalDatasetLocation` | Resolved physical file paths for one catalog dataset. | 0 | 1 |
| `backend/src/qts/data/historical/config.py:203` | `class` | `qts.data.historical.config.HistoricalDataConfig` | Project-level historical data stores and catalogs. | 0 | 2 |
| `backend/src/qts/data/historical/config.py:210` | `method` | `qts.data.historical.config.HistoricalDataConfig.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 4 |
| `backend/src/qts/data/historical/config.py:220` | `classmethod` | `qts.data.historical.config.HistoricalDataConfig.from_yaml` | 未写 docstring；静态推断为从指定来源构造或转换对象（名称：from yaml）。 | 3 | 14 |
| `backend/src/qts/data/historical/config.py:233` | `method` | `qts.data.historical.config.HistoricalDataConfig.catalog` | 未写 docstring；静态推断为所属类上的 `catalog` 行为。 | 0 | 1 |
| `backend/src/qts/data/historical/config.py:239` | `method` | `qts.data.historical.config.HistoricalDataConfig.store` | 未写 docstring；静态推断为所属类上的 `store` 行为。 | 0 | 1 |
| `backend/src/qts/data/historical/config.py:245` | `method` | `qts.data.historical.config.HistoricalDataConfig.resolve_dataset` | 未写 docstring；静态推断为解析标识、引用或配置到目标对象（名称：resolve dataset）。 | 5 | 9 |
| `backend/src/qts/data/historical/config.py:291` | `method` | `qts.data.historical.config.HistoricalDataConfig.resolve_chain_path` | Resolve chain metadata path without selecting a concrete bar file. | 2 | 5 |
| `backend/src/qts/data/historical/config.py:307` | `method` | `qts.data.historical.config.HistoricalDataConfig._csv_schema` | 未写 docstring；静态推断为所属类上的 `csv schema` 行为。 | 0 | 1 |
| `backend/src/qts/data/historical/config.py:316` | `classmethod` | `qts.data.historical.config.HistoricalDataConfig._parse_stores` | 未写 docstring；静态推断为所属类上的 `parse stores` 行为。 | 2 | 31 |
| `backend/src/qts/data/historical/config.py:353` | `staticmethod` | `qts.data.historical.config.HistoricalDataConfig._parse_store_defaults` | 未写 docstring；静态推断为所属类上的 `parse store defaults` 行为。 | 1 | 16 |
| `backend/src/qts/data/historical/config.py:384` | `classmethod` | `qts.data.historical.config.HistoricalDataConfig._parse_catalogs` | 未写 docstring；静态推断为所属类上的 `parse catalogs` 行为。 | 2 | 13 |
| `backend/src/qts/data/historical/config.py:404` | `classmethod` | `qts.data.historical.config.HistoricalDataConfig._parse_datasets` | 未写 docstring；静态推断为所属类上的 `parse datasets` 行为。 | 2 | 26 |
| `backend/src/qts/data/historical/config.py:454` | `staticmethod` | `qts.data.historical.config.HistoricalDataConfig._parse_bar_files` | 未写 docstring；静态推断为所属类上的 `parse bar files` 行为。 | 1 | 19 |
| `backend/src/qts/data/historical/config.py:490` | `staticmethod` | `qts.data.historical.config.HistoricalDataConfig._parse_schemas` | 未写 docstring；静态推断为所属类上的 `parse schemas` 行为。 | 1 | 17 |
| `backend/src/qts/data/historical/config.py:518` | `staticmethod` | `qts.data.historical.config.HistoricalDataConfig._select_bar_file` | 未写 docstring；静态推断为所属类上的 `select bar file` 行为。 | 2 | 7 |
| `backend/src/qts/data/historical/csv_dataset.py:42` | `class` | `qts.data.historical.csv_dataset.CsvDatasetDescription` | Cheap metadata description for a historical CSV dataset. | 0 | 1 |
| `backend/src/qts/data/historical/csv_dataset.py:56` | `class` | `qts.data.historical.csv_dataset.HistoricalCsvStats` | Streaming reader counters. | 0 | 1 |
| `backend/src/qts/data/historical/csv_dataset.py:66` | `method` | `qts.data.historical.csv_dataset.HistoricalCsvStats.as_dict` | 未写 docstring；静态推断为所属类上的 `as dict` 行为。 | 0 | 0 |
| `backend/src/qts/data/historical/csv_dataset.py:78` | `class` | `qts.data.historical.csv_dataset.HistoricalValidationSample` | Validation report plus counters for a sampled historical CSV. | 0 | 1 |
| `backend/src/qts/data/historical/csv_dataset.py:86` | `class` | `qts.data.historical.csv_dataset.HistoricalBarStream` | Lazy iterable over historical bars with side-channel reader stats. | 0 | 0 |
| `backend/src/qts/data/historical/csv_dataset.py:89` | `method` | `qts.data.historical.csv_dataset.HistoricalBarStream.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 1 | 1 |
| `backend/src/qts/data/historical/csv_dataset.py:115` | `method` | `qts.data.historical.csv_dataset.HistoricalBarStream.__iter__` | 未写 docstring；实现 Python 协议方法 `__iter__`。 | 4 | 7 |
| `backend/src/qts/data/historical/csv_dataset.py:129` | `method` | `qts.data.historical.csv_dataset.HistoricalBarStream._iter_all_supported_rows` | 未写 docstring；静态推断为所属类上的 `iter all supported rows` 行为。 | 4 | 5 |
| `backend/src/qts/data/historical/csv_dataset.py:154` | `method` | `qts.data.historical.csv_dataset.HistoricalBarStream._iter_selected_contract_rows` | 未写 docstring；静态推断为所属类上的 `iter selected contract rows` 行为。 | 7 | 15 |
| `backend/src/qts/data/historical/csv_dataset.py:217` | `method` | `qts.data.historical.csv_dataset.HistoricalBarStream._iter_session_selected_contract_rows` | 未写 docstring；静态推断为所属类上的 `iter session selected contract rows` 行为。 | 2 | 8 |
| `backend/src/qts/data/historical/csv_dataset.py:263` | `method` | `qts.data.historical.csv_dataset.HistoricalBarStream._emit_selected_session_rows` | 未写 docstring；静态推断为所属类上的 `emit selected session rows` 行为。 | 8 | 22 |
| `backend/src/qts/data/historical/csv_dataset.py:352` | `method` | `qts.data.historical.csv_dataset.HistoricalBarStream._timestamp_groups` | 未写 docstring；静态推断为所属类上的 `timestamp groups` 行为。 | 2 | 4 |
| `backend/src/qts/data/historical/csv_dataset.py:369` | `method` | `qts.data.historical.csv_dataset.HistoricalBarStream._count_excluded_symbol` | 未写 docstring；静态推断为所属类上的 `count excluded symbol` 行为。 | 1 | 1 |
| `backend/src/qts/data/historical/csv_dataset.py:374` | `method` | `qts.data.historical.csv_dataset.HistoricalBarStream._resolver_root` | 未写 docstring；静态推断为所属类上的 `resolver root` 行为。 | 1 | 1 |
| `backend/src/qts/data/historical/csv_dataset.py:377` | `method` | `qts.data.historical.csv_dataset.HistoricalBarStream._field` | 未写 docstring；静态推断为所属类上的 `field` 行为。 | 0 | 1 |
| `backend/src/qts/data/historical/csv_dataset.py:380` | `method` | `qts.data.historical.csv_dataset.HistoricalBarStream._timestamp` | 未写 docstring；静态推断为所属类上的 `timestamp` 行为。 | 2 | 2 |
| `backend/src/qts/data/historical/csv_dataset.py:384` | `module_function` | `qts.data.historical.csv_dataset.describe_csv_dataset` | Read historical CSV identity metadata without materializing row data. | 2 | 7 |
| `backend/src/qts/data/historical/csv_dataset.py:411` | `module_function` | `qts.data.historical.csv_dataset.iter_historical_bars` | Return a lazy stream of outright historical bars. | 2 | 2 |
| `backend/src/qts/data/historical/csv_dataset.py:438` | `module_function` | `qts.data.historical.csv_dataset.validate_historical_sample` | Validate a bounded sample or full CSV when `sample_rows` is None. | 11 | 25 |
| `backend/src/qts/data/historical/csv_dataset.py:514` | `module_function` | `qts.data.historical.csv_dataset._row_to_bar` | 未写 docstring；静态推断为 `row to bar` 函数，具体语义以实现为准。 | 4 | 8 |
| `backend/src/qts/data/historical/csv_dataset.py:540` | `module_function` | `qts.data.historical.csv_dataset._row_ohlcv` | 未写 docstring；静态推断为 `row ohlcv` 函数，具体语义以实现为准。 | 1 | 1 |
| `backend/src/qts/data/historical/csv_dataset.py:554` | `module_function` | `qts.data.historical.csv_dataset._parse_ohlcv_values` | 未写 docstring；静态推断为 `parse ohlcv values` 函数，具体语义以实现为准。 | 0 | 12 |
| `backend/src/qts/data/historical/csv_dataset.py:578` | `module_function` | `qts.data.historical.csv_dataset._resolver_root` | 未写 docstring；静态推断为 `resolver root` 函数，具体语义以实现为准。 | 0 | 4 |
| `backend/src/qts/data/historical/csv_dataset.py:585` | `module_function` | `qts.data.historical.csv_dataset._group_bars` | 未写 docstring；静态推断为 `group bars` 函数，具体语义以实现为准。 | 0 | 2 |
| `backend/src/qts/data/historical/csv_dataset.py:592` | `module_function` | `qts.data.historical.csv_dataset._as_symbol_resolver` | 未写 docstring；静态推断为 `as symbol resolver` 函数，具体语义以实现为准。 | 1 | 2 |
| `backend/src/qts/data/historical/csv_dataset.py:600` | `module_function` | `qts.data.historical.csv_dataset._is_spread_symbol` | 未写 docstring；静态推断为 `is spread symbol` 函数，具体语义以实现为准。 | 0 | 0 |
| `backend/src/qts/data/historical/csv_format.py:24` | `class` | `qts.data.historical.csv_format.HistoricalCsvSchema` | Mapping from framework OHLCV semantics to concrete CSV columns. | 0 | 1 |
| `backend/src/qts/data/historical/csv_format.py:36` | `method` | `qts.data.historical.csv_format.HistoricalCsvSchema.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 5 |
| `backend/src/qts/data/historical/csv_format.py:52` | `property` | `qts.data.historical.csv_format.HistoricalCsvSchema.required_columns` | 未写 docstring；静态推断为所属类上的 `required columns` 行为。 | 0 | 0 |
| `backend/src/qts/data/historical/csv_format.py:63` | `method` | `qts.data.historical.csv_format.HistoricalCsvSchema.validate_columns` | 未写 docstring；静态推断为校验输入、状态或领域约束（名称：validate columns）。 | 0 | 4 |
| `backend/src/qts/data/historical/csv_format.py:70` | `method` | `qts.data.historical.csv_format.HistoricalCsvSchema.column_indices` | 未写 docstring；静态推断为所属类上的 `column indices` 行为。 | 1 | 2 |
| `backend/src/qts/data/historical/csv_format.py:87` | `module_function` | `qts.data.historical.csv_format.validate_historical_csv_columns` | Validate historical CSV columns against the configured schema. | 0 | 4 |
| `backend/src/qts/data/historical/csv_format.py:104` | `module_function` | `qts.data.historical.csv_format.parse_historical_ts_event` | Parse a historical CSV UTC timestamp, accepting nanosecond text input. | 0 | 7 |
| `backend/src/qts/data/historical/csv_format.py:119` | `module_function` | `qts.data.historical.csv_format.historical_timeframe_delta` | Return the duration represented by a supported historical timeframe. | 0 | 11 |
| `backend/src/qts/data/historical/service.py:16` | `class` | `qts.data.historical.service.HistoricalMarketDataService` | Deterministic historical market data source with feed-like contracts. | 0 | 2 |
| `backend/src/qts/data/historical/service.py:27` | `method` | `qts.data.historical.service.HistoricalMarketDataService.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 4 |
| `backend/src/qts/data/historical/service.py:34` | `property` | `qts.data.historical.service.HistoricalMarketDataService.capabilities` | 未写 docstring；静态推断为所属类上的 `capabilities` 行为。 | 1 | 2 |
| `backend/src/qts/data/historical/service.py:43` | `method` | `qts.data.historical.service.HistoricalMarketDataService.subscribe` | 未写 docstring；静态推断为所属类上的 `subscribe` 行为。 | 2 | 2 |
| `backend/src/qts/data/historical/service.py:48` | `method` | `qts.data.historical.service.HistoricalMarketDataService.events` | 未写 docstring；静态推断为所属类上的 `events` 行为。 | 2 | 5 |
| `backend/src/qts/data/historical/symbols.py:12` | `class` | `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver` | Resolve historical futures outright symbols through chain metadata. | 0 | 1 |
| `backend/src/qts/data/historical/symbols.py:18` | `property` | `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver.root` | 未写 docstring；静态推断为所属类上的 `root` 行为。 | 0 | 0 |
| `backend/src/qts/data/historical/symbols.py:21` | `method` | `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver.is_supported_symbol` | 未写 docstring；静态推断为判断布尔条件（名称：is supported symbol）。 | 0 | 1 |
| `backend/src/qts/data/historical/symbols.py:24` | `method` | `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver.instrument_id_for_symbol` | 未写 docstring；静态推断为所属类上的 `instrument id for symbol` 行为。 | 0 | 1 |
| `backend/src/qts/data/live_feed.py:17` | `class` | `qts.data.live_feed.FeedCapabilities` | Feed-supported live market data features. | 0 | 2 |
| `backend/src/qts/data/live_feed.py:27` | `method` | `qts.data.live_feed.FeedCapabilities.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 6 |
| `backend/src/qts/data/live_feed.py:35` | `method` | `qts.data.live_feed.FeedCapabilities.supports_timeframe` | 未写 docstring；静态推断为所属类上的 `supports timeframe` 行为。 | 0 | 2 |
| `backend/src/qts/data/live_feed.py:40` | `method` | `qts.data.live_feed.FeedCapabilities.source_timeframe_for` | Return the provider timeframe needed to satisfy a requested bar stream. | 1 | 5 |
| `backend/src/qts/data/live_feed.py:73` | `class` | `qts.data.live_feed.FeedSubscription` | Internal live feed subscription request. | 0 | 1 |
| `backend/src/qts/data/live_feed.py:80` | `method` | `qts.data.live_feed.FeedSubscription.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 4 |
| `backend/src/qts/data/live_feed.py:88` | `class` | `qts.data.live_feed.LiveFeedSubscribed` | 未写 docstring；静态推断为定义 Live Feed Subscribed 概念或数据结构。 | 0 | 1 |
| `backend/src/qts/data/live_feed.py:94` | `class` | `qts.data.live_feed.LiveFeedEvent` | 未写 docstring；静态推断为定义 Live Feed Event 概念或数据结构。 | 0 | 1 |
| `backend/src/qts/data/live_feed.py:100` | `class` | `qts.data.live_feed.LiveFeedFailure` | 未写 docstring；静态推断为定义 Live Feed Failure 概念或数据结构。 | 0 | 1 |
| `backend/src/qts/data/live_feed.py:105` | `method` | `qts.data.live_feed.LiveFeedFailure.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 2 |
| `backend/src/qts/data/live_feed.py:111` | `class` | `qts.data.live_feed.ReconnectPolicy` | Deterministic reconnect backoff policy. | 0 | 1 |
| `backend/src/qts/data/live_feed.py:119` | `method` | `qts.data.live_feed.ReconnectPolicy.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 6 |
| `backend/src/qts/data/live_feed.py:129` | `method` | `qts.data.live_feed.ReconnectPolicy.delay_for_attempt` | 未写 docstring；静态推断为所属类上的 `delay for attempt` 行为。 | 0 | 5 |
| `backend/src/qts/data/live_feed.py:138` | `class` | `qts.data.live_feed.LiveFeedAdapter` | 未写 docstring；静态推断为定义 Live Feed Adapter 概念，继承/实现 Protocol。 | 0 | 0 |
| `backend/src/qts/data/live_feed.py:140` | `property` | `qts.data.live_feed.LiveFeedAdapter.capabilities` | 未写 docstring；静态推断为所属类上的 `capabilities` 行为。 | 0 | 0 |
| `backend/src/qts/data/live_feed.py:142` | `method` | `qts.data.live_feed.LiveFeedAdapter.subscribe` | 未写 docstring；静态推断为所属类上的 `subscribe` 行为。 | 0 | 0 |
| `backend/src/qts/data/live_feed.py:145` | `class` | `qts.data.live_feed.FakeLiveFeedAdapter` | Deterministic fake live market data feed. | 0 | 0 |
| `backend/src/qts/data/live_feed.py:148` | `method` | `qts.data.live_feed.FakeLiveFeedAdapter.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 0 | 3 |
| `backend/src/qts/data/live_feed.py:163` | `property` | `qts.data.live_feed.FakeLiveFeedAdapter.capabilities` | 未写 docstring；静态推断为所属类上的 `capabilities` 行为。 | 1 | 1 |
| `backend/src/qts/data/live_feed.py:167` | `property` | `qts.data.live_feed.FakeLiveFeedAdapter.subscription_count` | 未写 docstring；静态推断为所属类上的 `subscription count` 行为。 | 0 | 1 |
| `backend/src/qts/data/live_feed.py:170` | `method` | `qts.data.live_feed.FakeLiveFeedAdapter.subscribe` | 未写 docstring；静态推断为所属类上的 `subscribe` 行为。 | 1 | 1 |
| `backend/src/qts/data/live_feed.py:174` | `method` | `qts.data.live_feed.FakeLiveFeedAdapter.emit` | 未写 docstring；静态推断为所属类上的 `emit` 行为。 | 1 | 1 |
| `backend/src/qts/data/live_feed.py:177` | `method` | `qts.data.live_feed.FakeLiveFeedAdapter.fail` | 未写 docstring；静态推断为所属类上的 `fail` 行为。 | 1 | 2 |
| `backend/src/qts/data/provenance.py:13` | `class` | `qts.data.provenance.DatasetMetadata` | Stable reference to historical data used by simulation or research. | 0 | 1 |
| `backend/src/qts/data/provenance.py:26` | `method` | `qts.data.provenance.DatasetMetadata.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 2 | 8 |
| `backend/src/qts/data/provenance.py:38` | `property` | `qts.data.provenance.DatasetMetadata.reference` | 未写 docstring；静态推断为所属类上的 `reference` 行为。 | 0 | 0 |
| `backend/src/qts/data/provenance.py:43` | `staticmethod` | `qts.data.provenance.DatasetMetadata._require_text` | 未写 docstring；静态推断为所属类上的 `require text` 行为。 | 0 | 2 |
| `backend/src/qts/data/sessions/filter.py:13` | `class` | `qts.data.sessions.filter.SessionLookup` | Calendar session lookup required by session filters. | 0 | 0 |
| `backend/src/qts/data/sessions/filter.py:16` | `method` | `qts.data.sessions.filter.SessionLookup.session_for` | Return the internal market session for the date. | 0 | 0 |
| `backend/src/qts/data/sessions/filter.py:20` | `module_function` | `qts.data.sessions.filter.filter_session_bars` | Return bars whose start and end fall inside the half-open session. | 1 | 2 |
| `backend/src/qts/data/sessions/filter.py:33` | `module_function` | `qts.data.sessions.filter._bar_inside_session` | 未写 docstring；静态推断为 `bar inside session` 函数，具体语义以实现为准。 | 0 | 1 |
| `backend/src/qts/data/sessions/window.py:12` | `class` | `qts.data.sessions.window.RegularSessionWindow` | A recurring half-open exchange session window. The session id is the exchange-local close date. For overnight sessions this means a bar at or after the open belongs to the next local date's session. | 0 | 1 |
| `backend/src/qts/data/sessions/window.py:23` | `method` | `qts.data.sessions.window.RegularSessionWindow.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 3 |
| `backend/src/qts/data/sessions/window.py:29` | `method` | `qts.data.sessions.window.RegularSessionWindow.session_id_for_timestamp` | Return the exchange-local close-date session id containing timestamp. | 1 | 2 |
| `backend/src/qts/data/sessions/window.py:35` | `method` | `qts.data.sessions.window.RegularSessionWindow.session_date_for_timestamp` | Return the exchange-local close date for timestamp, or None if outside. | 1 | 6 |
| `backend/src/qts/data/sessions/window.py:50` | `method` | `qts.data.sessions.window.RegularSessionWindow.to_payload` | Return a stable JSON-serializable description of the session rule. | 0 | 0 |
| `backend/src/qts/data/stores/base.py:13` | `class` | `qts.data.stores.base.MarketDataStore` | Store and read bars by internal instrument identity. | 0 | 0 |
| `backend/src/qts/data/stores/base.py:16` | `method` | `qts.data.stores.base.MarketDataStore.write_bars` | 未写 docstring；静态推断为写入数据（名称：write bars）。 | 0 | 0 |
| `backend/src/qts/data/stores/base.py:18` | `method` | `qts.data.stores.base.MarketDataStore.read_bars` | 未写 docstring；静态推断为读取数据（名称：read bars）。 | 0 | 0 |
| `backend/src/qts/data/stores/memory_store.py:13` | `class` | `qts.data.stores.memory_store.InMemoryMarketDataStore` | In-memory bar store for tests and local runs. | 0 | 0 |
| `backend/src/qts/data/stores/memory_store.py:16` | `method` | `qts.data.stores.memory_store.InMemoryMarketDataStore.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 0 | 1 |
| `backend/src/qts/data/stores/memory_store.py:19` | `method` | `qts.data.stores.memory_store.InMemoryMarketDataStore.write_bars` | 未写 docstring；静态推断为写入数据（名称：write bars）。 | 0 | 2 |
| `backend/src/qts/data/stores/memory_store.py:25` | `method` | `qts.data.stores.memory_store.InMemoryMarketDataStore.read_bars` | 未写 docstring；静态推断为读取数据（名称：read bars）。 | 0 | 2 |
| `backend/src/qts/data/stores/parquet_store.py:21` | `class` | `qts.data.stores.parquet_store.ParquetMarketDataStore` | File-backed bar store partitioned by instrument, timeframe, and date. | 0 | 0 |
| `backend/src/qts/data/stores/parquet_store.py:24` | `method` | `qts.data.stores.parquet_store.ParquetMarketDataStore.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 0 | 0 |
| `backend/src/qts/data/stores/parquet_store.py:27` | `method` | `qts.data.stores.parquet_store.ParquetMarketDataStore.write_bars` | 未写 docstring；静态推断为写入数据（名称：write bars）。 | 3 | 14 |
| `backend/src/qts/data/stores/parquet_store.py:43` | `method` | `qts.data.stores.parquet_store.ParquetMarketDataStore.read_bars` | 未写 docstring；静态推断为读取数据（名称：read bars）。 | 1 | 7 |
| `backend/src/qts/data/stores/parquet_store.py:63` | `method` | `qts.data.stores.parquet_store.ParquetMarketDataStore._path_for` | 未写 docstring；静态推断为所属类上的 `path for` 行为。 | 0 | 2 |
| `backend/src/qts/data/stores/parquet_store.py:71` | `method` | `qts.data.stores.parquet_store.ParquetMarketDataStore._read_file` | 未写 docstring；静态推断为所属类上的 `read file` 行为。 | 1 | 5 |
| `backend/src/qts/data/stores/parquet_store.py:76` | `staticmethod` | `qts.data.stores.parquet_store.ParquetMarketDataStore._bar_to_json` | 未写 docstring；静态推断为所属类上的 `bar to json` 行为。 | 0 | 9 |
| `backend/src/qts/data/stores/parquet_store.py:96` | `staticmethod` | `qts.data.stores.parquet_store.ParquetMarketDataStore._bar_from_json` | 未写 docstring；静态推断为所属类上的 `bar from json` 行为。 | 2 | 26 |
| `backend/src/qts/data/subscriptions.py:12` | `class` | `qts.data.subscriptions.SourceStreamType` | Physical market data stream type. | 0 | 0 |
| `backend/src/qts/data/subscriptions.py:21` | `class` | `qts.data.subscriptions.LogicalSubscription` | Strategy-requested market data stream. | 0 | 1 |
| `backend/src/qts/data/subscriptions.py:29` | `method` | `qts.data.subscriptions.LogicalSubscription.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 4 |
| `backend/src/qts/data/subscriptions.py:37` | `class` | `qts.data.subscriptions.LogicalSubscriptionKey` | Deduplication key for strategy-facing subscribers. | 0 | 1 |
| `backend/src/qts/data/subscriptions.py:46` | `class` | `qts.data.subscriptions.PhysicalSubscriptionKey` | Deduplication key for provider-facing subscriptions. | 0 | 1 |
| `backend/src/qts/data/subscriptions.py:54` | `method` | `qts.data.subscriptions.PhysicalSubscriptionKey.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 4 |
| `backend/src/qts/data/subscriptions.py:61` | `module_function` | `qts.data.subscriptions.logical_key` | Return the logical fan-out key for a subscription. | 1 | 1 |
| `backend/src/qts/data/subscriptions.py:71` | `module_function` | `qts.data.subscriptions.plan_physical_subscription` | Map one logical subscription to its provider source subscription. | 1 | 3 |
| `backend/src/qts/data/validation_report.py:13` | `class` | `qts.data.validation_report.DataValidationIssueCode` | Known market data validation issue codes. | 0 | 0 |
| `backend/src/qts/data/validation_report.py:27` | `class` | `qts.data.validation_report.DataValidationSeverity` | Severity for data validation issues. | 0 | 0 |
| `backend/src/qts/data/validation_report.py:36` | `class` | `qts.data.validation_report.DataValidationIssue` | One validation issue for a bar sequence. | 0 | 1 |
| `backend/src/qts/data/validation_report.py:45` | `class` | `qts.data.validation_report.DataValidationReport` | Validation result for a bar sequence. | 0 | 1 |
| `backend/src/qts/data/validation_report.py:51` | `property` | `qts.data.validation_report.DataValidationReport.valid` | 未写 docstring；静态推断为所属类上的 `valid` 行为。 | 0 | 1 |
| `backend/src/qts/data/validation_report.py:55` | `property` | `qts.data.validation_report.DataValidationReport.max_severity` | 未写 docstring；静态推断为所属类上的 `max severity` 行为。 | 0 | 1 |
| `backend/src/qts/data/validation_report.py:66` | `module_function` | `qts.data.validation_report.validate_bars` | Validate bar ordering, overlap, and optional session containment. | 3 | 27 |
| `backend/src/qts/data/validation_report.py:143` | `module_function` | `qts.data.validation_report._append_ohlc_issue` | 未写 docstring；静态推断为 `append ohlc issue` 函数，具体语义以实现为准。 | 1 | 5 |
| `backend/src/qts/domain/events/event.py:13` | `class` | `qts.domain.events.event.BaseEvent` | Minimal event envelope used for traceable internal messages. | 0 | 1 |
| `backend/src/qts/domain/events/event.py:24` | `method` | `qts.domain.events.event.BaseEvent.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 1 | 7 |
| `backend/src/qts/domain/events/metadata.py:21` | `class` | `qts.domain.events.metadata.EventMetadata` | Trace metadata carried by platform events. | 0 | 1 |
| `backend/src/qts/domain/events/metadata.py:39` | `method` | `qts.domain.events.metadata.EventMetadata.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 1 | 7 |
| `backend/src/qts/domain/instruments/contract_spec.py:10` | `class` | `qts.domain.instruments.contract_spec.SettlementType` | How a contract settles. | 0 | 0 |
| `backend/src/qts/domain/instruments/contract_spec.py:18` | `class` | `qts.domain.instruments.contract_spec.ContractSpec` | Trading contract metadata required for valuation and order sizing. | 0 | 1 |
| `backend/src/qts/domain/instruments/contract_spec.py:27` | `method` | `qts.domain.instruments.contract_spec.ContractSpec.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 1 | 5 |
| `backend/src/qts/domain/instruments/contract_spec.py:35` | `staticmethod` | `qts.domain.instruments.contract_spec.ContractSpec._require_positive` | 未写 docstring；静态推断为所属类上的 `require positive` 行为。 | 0 | 2 |
| `backend/src/qts/domain/instruments/derivative_spec.py:13` | `class` | `qts.domain.instruments.derivative_spec.OptionRight` | Option payoff direction. | 0 | 0 |
| `backend/src/qts/domain/instruments/derivative_spec.py:20` | `class` | `qts.domain.instruments.derivative_spec.ExerciseStyle` | Option exercise style. | 0 | 0 |
| `backend/src/qts/domain/instruments/derivative_spec.py:28` | `class` | `qts.domain.instruments.derivative_spec.DerivativeSpec` | Common derivative metadata. | 0 | 1 |
| `backend/src/qts/domain/instruments/derivative_spec.py:36` | `class` | `qts.domain.instruments.derivative_spec.FutureSpec` | Future contract metadata. | 0 | 1 |
| `backend/src/qts/domain/instruments/derivative_spec.py:41` | `method` | `qts.domain.instruments.derivative_spec.FutureSpec.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 2 |
| `backend/src/qts/domain/instruments/derivative_spec.py:47` | `class` | `qts.domain.instruments.derivative_spec.OptionSpec` | Option contract metadata. | 0 | 1 |
| `backend/src/qts/domain/instruments/derivative_spec.py:54` | `method` | `qts.domain.instruments.derivative_spec.OptionSpec.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 2 |
| `backend/src/qts/domain/instruments/instrument.py:19` | `class` | `qts.domain.instruments.instrument.AssetClass` | Supported instrument asset classes. | 0 | 0 |
| `backend/src/qts/domain/instruments/instrument.py:28` | `class` | `qts.domain.instruments.instrument.Instrument` | Tradable instrument identified by a stable internal InstrumentId. | 0 | 1 |
| `backend/src/qts/domain/instruments/instrument.py:39` | `method` | `qts.domain.instruments.instrument.Instrument.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 9 |
| `backend/src/qts/domain/market_data/bar.py:14` | `class` | `qts.domain.market_data.bar.Bar` | OHLCV bar over a half-open interval. | 0 | 2 |
| `backend/src/qts/domain/market_data/bar.py:33` | `method` | `qts.domain.market_data.bar.Bar.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 2 | 14 |
| `backend/src/qts/domain/market_data/bar.py:54` | `property` | `qts.domain.market_data.bar.Bar.interval` | 未写 docstring；静态推断为所属类上的 `interval` 行为。 | 1 | 1 |
| `backend/src/qts/domain/market_data/bar.py:58` | `staticmethod` | `qts.domain.market_data.bar.Bar._require_non_negative` | 未写 docstring；静态推断为所属类上的 `require non negative` 行为。 | 0 | 2 |
| `backend/src/qts/domain/market_data/bar.py:64` | `class` | `qts.domain.market_data.bar.Quote` | Top-of-book quote. | 0 | 3 |
| `backend/src/qts/domain/market_data/bar.py:74` | `method` | `qts.domain.market_data.bar.Quote.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 1 | 4 |
| `backend/src/qts/domain/market_data/bar.py:82` | `property` | `qts.domain.market_data.bar.Quote.spread` | 未写 docstring；静态推断为所属类上的 `spread` 行为。 | 0 | 0 |
| `backend/src/qts/domain/market_data/bar.py:87` | `class` | `qts.domain.market_data.bar.Tick` | Trade tick. | 0 | 2 |
| `backend/src/qts/domain/market_data/bar.py:95` | `method` | `qts.domain.market_data.bar.Tick.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 1 | 2 |
| `backend/src/qts/domain/risk/decision.py:10` | `class` | `qts.domain.risk.decision.RiskDecisionStatus` | Risk check outcome. | 0 | 0 |
| `backend/src/qts/domain/risk/decision.py:19` | `class` | `qts.domain.risk.decision.RiskDecision` | Explicit result of a risk check. | 0 | 1 |
| `backend/src/qts/domain/risk/decision.py:29` | `classmethod` | `qts.domain.risk.decision.RiskDecision.approve` | 未写 docstring；静态推断为所属类上的 `approve` 行为。 | 0 | 1 |
| `backend/src/qts/domain/risk/decision.py:38` | `classmethod` | `qts.domain.risk.decision.RiskDecision.rejected` | 未写 docstring；静态推断为所属类上的 `rejected` 行为。 | 0 | 5 |
| `backend/src/qts/domain/risk/decision.py:59` | `property` | `qts.domain.risk.decision.RiskDecision.approved` | 未写 docstring；静态推断为所属类上的 `approved` 行为。 | 0 | 0 |
| `backend/src/qts/domain/risk/decision.py:63` | `property` | `qts.domain.risk.decision.RiskDecision.reason_text` | 未写 docstring；静态推断为所属类上的 `reason text` 行为。 | 0 | 0 |
| `backend/src/qts/domain/risk/request.py:14` | `class` | `qts.domain.risk.request.OrderRiskRequest` | Pre-trade risk input for a proposed order. | 0 | 1 |
| `backend/src/qts/domain/risk/request.py:23` | `method` | `qts.domain.risk.request.OrderRiskRequest.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 1 | 7 |
| `backend/src/qts/domain/risk/request.py:34` | `property` | `qts.domain.risk.request.OrderRiskRequest.notional` | 未写 docstring；静态推断为所属类上的 `notional` 行为。 | 0 | 0 |
| `backend/src/qts/execution/adapters/ibkr_order_execution.py:14` | `class` | `qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionConnection` | IBKR order execution connection settings. | 0 | 1 |
| `backend/src/qts/execution/adapters/ibkr_order_execution.py:23` | `method` | `qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionConnection.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 6 |
| `backend/src/qts/execution/adapters/ibkr_order_execution.py:35` | `class` | `qts.execution.adapters.ibkr_order_execution.IbkrOrderRequest` | IBKR order request produced at the adapter boundary. | 0 | 1 |
| `backend/src/qts/execution/adapters/ibkr_order_execution.py:46` | `class` | `qts.execution.adapters.ibkr_order_execution.IbkrExecutionReport` | IBKR execution report shape before normalization. | 0 | 2 |
| `backend/src/qts/execution/adapters/ibkr_order_execution.py:57` | `class` | `qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionAdapter` | Maps internal orders to IBKR order requests and normalizes reports. | 0 | 0 |
| `backend/src/qts/execution/adapters/ibkr_order_execution.py:60` | `method` | `qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionAdapter.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 0 | 0 |
| `backend/src/qts/execution/adapters/ibkr_order_execution.py:69` | `method` | `qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionAdapter.to_order_request` | 未写 docstring；静态推断为转换或序列化为指定目标表示（名称：to order request）。 | 1 | 2 |
| `backend/src/qts/execution/adapters/ibkr_order_execution.py:78` | `method` | `qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionAdapter.normalize_execution_report` | 未写 docstring；静态推断为所属类上的 `normalize execution report` 行为。 | 1 | 1 |
| `backend/src/qts/execution/broker.py:15` | `class` | `qts.execution.broker.BrokerCapabilities` | Broker-supported live execution features. | 0 | 4 |
| `backend/src/qts/execution/broker.py:31` | `method` | `qts.execution.broker.BrokerCapabilities.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 5 |
| `backend/src/qts/execution/broker.py:37` | `method` | `qts.execution.broker.BrokerCapabilities.supports_asset_class` | 未写 docstring；静态推断为所属类上的 `supports asset class` 行为。 | 0 | 2 |
| `backend/src/qts/execution/broker.py:42` | `method` | `qts.execution.broker.BrokerCapabilities.supports_order_type` | 未写 docstring；静态推断为所属类上的 `supports order type` 行为。 | 0 | 0 |
| `backend/src/qts/execution/broker.py:51` | `method` | `qts.execution.broker.BrokerCapabilities.supports_tif` | 未写 docstring；静态推断为所属类上的 `supports tif` 行为。 | 0 | 0 |
| `backend/src/qts/execution/broker.py:55` | `class` | `qts.execution.broker.BrokerOrderType` | Order types modeled before broker submission. | 0 | 0 |
| `backend/src/qts/execution/broker.py:63` | `class` | `qts.execution.broker.TimeInForce` | Time-in-force values modeled at the execution boundary. | 0 | 0 |
| `backend/src/qts/execution/broker.py:72` | `class` | `qts.execution.broker.BrokerOrderRequest` | Internal order request sent to the broker adapter boundary. | 0 | 1 |
| `backend/src/qts/execution/broker.py:82` | `method` | `qts.execution.broker.BrokerOrderRequest.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 2 |
| `backend/src/qts/execution/broker.py:87` | `class` | `qts.execution.broker.BrokerExecutionReportStatus` | Broker-boundary execution report status. | 0 | 0 |
| `backend/src/qts/execution/broker.py:98` | `class` | `qts.execution.broker.BrokerExecutionReport` | Normalized broker callback before it reaches OrderManager. | 0 | 2 |
| `backend/src/qts/execution/broker.py:113` | `method` | `qts.execution.broker.BrokerExecutionReport.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 8 |
| `backend/src/qts/execution/broker.py:124` | `class` | `qts.execution.broker.BrokerAdapter` | Stable broker execution boundary. | 0 | 0 |
| `backend/src/qts/execution/broker.py:128` | `property` | `qts.execution.broker.BrokerAdapter.capabilities` | 未写 docstring；静态推断为所属类上的 `capabilities` 行为。 | 0 | 0 |
| `backend/src/qts/execution/broker.py:130` | `method` | `qts.execution.broker.BrokerAdapter.submit_order` | 未写 docstring；静态推断为所属类上的 `submit order` 行为。 | 0 | 0 |
| `backend/src/qts/execution/broker.py:132` | `method` | `qts.execution.broker.BrokerAdapter.cancel_order` | 未写 docstring；静态推断为所属类上的 `cancel order` 行为。 | 0 | 0 |
| `backend/src/qts/execution/broker.py:135` | `class` | `qts.execution.broker.FakeBrokerAdapter` | Deterministic fake broker for live-beta tests and local runs. | 0 | 0 |
| `backend/src/qts/execution/broker.py:138` | `method` | `qts.execution.broker.FakeBrokerAdapter.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 0 | 0 |
| `backend/src/qts/execution/broker.py:145` | `property` | `qts.execution.broker.FakeBrokerAdapter.capabilities` | 未写 docstring；静态推断为所属类上的 `capabilities` 行为。 | 1 | 1 |
| `backend/src/qts/execution/broker.py:148` | `method` | `qts.execution.broker.FakeBrokerAdapter.submit_order` | 未写 docstring；静态推断为所属类上的 `submit order` 行为。 | 1 | 3 |
| `backend/src/qts/execution/broker.py:159` | `method` | `qts.execution.broker.FakeBrokerAdapter.cancel_order` | 未写 docstring；静态推断为所属类上的 `cancel order` 行为。 | 1 | 1 |
| `backend/src/qts/execution/broker.py:167` | `method` | `qts.execution.broker.FakeBrokerAdapter.emit_fill` | 未写 docstring；静态推断为所属类上的 `emit fill` 行为。 | 1 | 7 |
| `backend/src/qts/execution/broker.py:196` | `method` | `qts.execution.broker.FakeBrokerAdapter._report` | 未写 docstring；静态推断为所属类上的 `report` 行为。 | 1 | 1 |
| `backend/src/qts/execution/broker.py:222` | `module_function` | `qts.execution.broker.normalize_broker_execution_report` | Convert broker-boundary report into the OrderManager report type. | 2 | 2 |
| `backend/src/qts/execution/idempotency.py:6` | `class` | `qts.execution.idempotency.FillIdempotencyStore` | Tracks fill IDs that have already been applied. | 0 | 0 |
| `backend/src/qts/execution/idempotency.py:9` | `method` | `qts.execution.idempotency.FillIdempotencyStore.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 0 | 2 |
| `backend/src/qts/execution/idempotency.py:12` | `method` | `qts.execution.idempotency.FillIdempotencyStore.mark_seen` | 未写 docstring；静态推断为所属类上的 `mark seen` 行为。 | 0 | 3 |
| `backend/src/qts/execution/idempotency.py:20` | `method` | `qts.execution.idempotency.FillIdempotencyStore.discard` | 未写 docstring；静态推断为所属类上的 `discard` 行为。 | 0 | 1 |
| `backend/src/qts/execution/idempotency.py:23` | `method` | `qts.execution.idempotency.FillIdempotencyStore.snapshot` | 未写 docstring；静态推断为所属类上的 `snapshot` 行为。 | 0 | 2 |
| `backend/src/qts/execution/idempotency.py:27` | `classmethod` | `qts.execution.idempotency.FillIdempotencyStore.restore` | 未写 docstring；静态推断为所属类上的 `restore` 行为。 | 0 | 2 |
| `backend/src/qts/execution/order_manager.py:15` | `class` | `qts.execution.order_manager.OrderSide` | Order side. | 0 | 0 |
| `backend/src/qts/execution/order_manager.py:23` | `class` | `qts.execution.order_manager.OrderIntent` | Approved order instruction before broker submission. | 0 | 1 |
| `backend/src/qts/execution/order_manager.py:31` | `method` | `qts.execution.order_manager.OrderIntent.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 2 |
| `backend/src/qts/execution/order_manager.py:37` | `class` | `qts.execution.order_manager.CancelIntent` | Intent to cancel an order through OrderManager. | 0 | 1 |
| `backend/src/qts/execution/order_manager.py:45` | `class` | `qts.execution.order_manager.ReplaceIntent` | Intent to replace an order through OrderManager. | 0 | 1 |
| `backend/src/qts/execution/order_manager.py:51` | `method` | `qts.execution.order_manager.ReplaceIntent.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 2 |
| `backend/src/qts/execution/order_manager.py:57` | `class` | `qts.execution.order_manager.Order` | Order snapshot owned by OrderManager. | 0 | 1 |
| `backend/src/qts/execution/order_manager.py:66` | `class` | `qts.execution.order_manager.ExecutionReportStatus` | Normalized broker report status. | 0 | 0 |
| `backend/src/qts/execution/order_manager.py:80` | `class` | `qts.execution.order_manager.ExecutionReport` | Normalized broker execution report. | 0 | 4 |
| `backend/src/qts/execution/order_manager.py:92` | `method` | `qts.execution.order_manager.ExecutionReport.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 10 |
| `backend/src/qts/execution/order_manager.py:106` | `class` | `qts.execution.order_manager.OrderFill` | OrderManager-validated fill event. | 0 | 3 |
| `backend/src/qts/execution/order_manager.py:120` | `class` | `qts.execution.order_manager.OrderManagerResult` | Events emitted by processing an execution report. | 0 | 1 |
| `backend/src/qts/execution/order_manager.py:128` | `class` | `qts.execution.order_manager.OrderManagerSnapshot` | Serializable OrderManager state for reconnect/recovery. | 0 | 1 |
| `backend/src/qts/execution/order_manager.py:136` | `class` | `qts.execution.order_manager.OrderManager` | Owns order lifecycle and normalized execution reports. | 0 | 0 |
| `backend/src/qts/execution/order_manager.py:139` | `method` | `qts.execution.order_manager.OrderManager.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 1 | 1 |
| `backend/src/qts/execution/order_manager.py:146` | `method` | `qts.execution.order_manager.OrderManager.create_order` | 未写 docstring；静态推断为创建对象或资源（名称：create order）。 | 2 | 3 |
| `backend/src/qts/execution/order_manager.py:155` | `method` | `qts.execution.order_manager.OrderManager.mark_sent` | 未写 docstring；静态推断为所属类上的 `mark sent` 行为。 | 1 | 4 |
| `backend/src/qts/execution/order_manager.py:164` | `method` | `qts.execution.order_manager.OrderManager.request_cancel` | 未写 docstring；静态推断为所属类上的 `request cancel` 行为。 | 1 | 2 |
| `backend/src/qts/execution/order_manager.py:168` | `method` | `qts.execution.order_manager.OrderManager.request_replace` | 未写 docstring；静态推断为所属类上的 `request replace` 行为。 | 2 | 4 |
| `backend/src/qts/execution/order_manager.py:188` | `method` | `qts.execution.order_manager.OrderManager.process_report` | 未写 docstring；静态推断为所属类上的 `process report` 行为。 | 4 | 5 |
| `backend/src/qts/execution/order_manager.py:195` | `method` | `qts.execution.order_manager.OrderManager.get_order` | 未写 docstring；静态推断为读取或返回值（名称：get order）。 | 0 | 0 |
| `backend/src/qts/execution/order_manager.py:198` | `method` | `qts.execution.order_manager.OrderManager.discard_terminal_order` | 未写 docstring；静态推断为所属类上的 `discard terminal order` 行为。 | 0 | 7 |
| `backend/src/qts/execution/order_manager.py:209` | `method` | `qts.execution.order_manager.OrderManager.snapshot` | 未写 docstring；静态推断为所属类上的 `snapshot` 行为。 | 1 | 6 |
| `backend/src/qts/execution/order_manager.py:217` | `classmethod` | `qts.execution.order_manager.OrderManager.restore` | 未写 docstring；静态推断为所属类上的 `restore` 行为。 | 2 | 4 |
| `backend/src/qts/execution/order_manager.py:228` | `method` | `qts.execution.order_manager.OrderManager._replace_order` | 未写 docstring；静态推断为所属类上的 `replace order` 行为。 | 1 | 1 |
| `backend/src/qts/execution/order_manager.py:247` | `method` | `qts.execution.order_manager.OrderManager._fills_for_report` | 未写 docstring；静态推断为所属类上的 `fills for report` 行为。 | 1 | 7 |
| `backend/src/qts/execution/order_manager.py:269` | `staticmethod` | `qts.execution.order_manager.OrderManager._event_for_report` | 未写 docstring；静态推断为所属类上的 `event for report` 行为。 | 0 | 0 |
| `backend/src/qts/execution/order_state_machine.py:9` | `class` | `qts.execution.order_state_machine.OrderState` | Internal order lifecycle states. | 0 | 0 |
| `backend/src/qts/execution/order_state_machine.py:23` | `class` | `qts.execution.order_state_machine.OrderEvent` | Order lifecycle transition inputs. | 0 | 0 |
| `backend/src/qts/execution/order_state_machine.py:36` | `class` | `qts.execution.order_state_machine.OrderTransitionError` | Raised when an order transition is invalid. | 0 | 0 |
| `backend/src/qts/execution/order_state_machine.py:93` | `class` | `qts.execution.order_state_machine.OrderStateMachine` | Validate and apply order lifecycle transitions. | 0 | 1 |
| `backend/src/qts/execution/order_state_machine.py:98` | `method` | `qts.execution.order_state_machine.OrderStateMachine.apply` | 未写 docstring；静态推断为应用状态变更、规则或计算结果（名称：apply）。 | 1 | 4 |
| `backend/src/qts/execution/simulator/fill_model.py:10` | `class` | `qts.execution.simulator.fill_model.ImmediateFillModel` | Fills market orders at the provided market price. | 0 | 0 |
| `backend/src/qts/execution/simulator/fill_model.py:13` | `method` | `qts.execution.simulator.fill_model.ImmediateFillModel.fill` | 未写 docstring；静态推断为所属类上的 `fill` 行为。 | 1 | 3 |
| `backend/src/qts/execution/simulator/simulated_broker.py:11` | `class` | `qts.execution.simulator.simulated_broker.SimulatedBroker` | Broker simulator with no external dependency. | 0 | 0 |
| `backend/src/qts/execution/simulator/simulated_broker.py:14` | `method` | `qts.execution.simulator.simulated_broker.SimulatedBroker.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 1 | 1 |
| `backend/src/qts/execution/simulator/simulated_broker.py:17` | `method` | `qts.execution.simulator.simulated_broker.SimulatedBroker.execute_market_order` | 未写 docstring；静态推断为所属类上的 `execute market order` 行为。 | 0 | 1 |
| `backend/src/qts/factors/momentum.py:10` | `class` | `qts.factors.momentum.FactorAsset` | Minimal asset shape required by factor ranking. | 0 | 0 |
| `backend/src/qts/factors/momentum.py:14` | `property` | `qts.factors.momentum.FactorAsset.symbol` | Stable display symbol used for deterministic tie-breaking. | 0 | 0 |
| `backend/src/qts/factors/momentum.py:19` | `class` | `qts.factors.momentum.FactorScore` | Single asset factor score. | 0 | 1 |
| `backend/src/qts/factors/momentum.py:27` | `class` | `qts.factors.momentum.FactorResult` | Ranked cross-sectional factor result. | 0 | 1 |
| `backend/src/qts/factors/momentum.py:32` | `method` | `qts.factors.momentum.FactorResult.score` | 未写 docstring；静态推断为所属类上的 `score` 行为。 | 0 | 1 |
| `backend/src/qts/factors/momentum.py:40` | `class` | `qts.factors.momentum.MomentumFactor` | Compute simple period momentum as last / first - 1. | 0 | 1 |
| `backend/src/qts/factors/momentum.py:45` | `method` | `qts.factors.momentum.MomentumFactor.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 1 |
| `backend/src/qts/factors/momentum.py:49` | `method` | `qts.factors.momentum.MomentumFactor.compute` | 未写 docstring；静态推断为计算派生值（名称：compute）。 | 3 | 7 |
| `backend/src/qts/factors/momentum.py:58` | `staticmethod` | `qts.factors.momentum.MomentumFactor._momentum` | 未写 docstring；静态推断为所属类上的 `momentum` 行为。 | 0 | 5 |
| `backend/src/qts/indicators/price/ema.py:12` | `class` | `qts.indicators.price.ema.EMA` | Incremental EMA using SMA as the warmup seed. | 0 | 2 |
| `backend/src/qts/indicators/price/ema.py:19` | `method` | `qts.indicators.price.ema.EMA.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 1 | 1 |
| `backend/src/qts/indicators/price/ema.py:23` | `property` | `qts.indicators.price.ema.EMA.ready` | 未写 docstring；静态推断为读取数据（名称：ready）。 | 0 | 0 |
| `backend/src/qts/indicators/price/ema.py:26` | `method` | `qts.indicators.price.ema.EMA.update` | 未写 docstring；静态推断为所属类上的 `update` 行为。 | 0 | 6 |
| `backend/src/qts/indicators/price/sma.py:12` | `class` | `qts.indicators.price.sma.SMA` | Incremental simple moving average. | 0 | 2 |
| `backend/src/qts/indicators/price/sma.py:19` | `method` | `qts.indicators.price.sma.SMA.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 1 | 1 |
| `backend/src/qts/indicators/price/sma.py:23` | `property` | `qts.indicators.price.sma.SMA.ready` | 未写 docstring；静态推断为读取数据（名称：ready）。 | 0 | 0 |
| `backend/src/qts/indicators/price/sma.py:26` | `method` | `qts.indicators.price.sma.SMA.update` | 未写 docstring；静态推断为所属类上的 `update` 行为。 | 0 | 4 |
| `backend/src/qts/indicators/rolling.py:14` | `class` | `qts.indicators.rolling.RollingWindow` | Bounded FIFO buffer with warmup state. | 0 | 2 |
| `backend/src/qts/indicators/rolling.py:20` | `method` | `qts.indicators.rolling.RollingWindow.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 2 |
| `backend/src/qts/indicators/rolling.py:26` | `property` | `qts.indicators.rolling.RollingWindow.ready` | 未写 docstring；静态推断为读取数据（名称：ready）。 | 0 | 1 |
| `backend/src/qts/indicators/rolling.py:29` | `method` | `qts.indicators.rolling.RollingWindow.append` | 未写 docstring；静态推断为所属类上的 `append` 行为。 | 0 | 1 |
| `backend/src/qts/indicators/rolling.py:32` | `method` | `qts.indicators.rolling.RollingWindow.snapshot` | 未写 docstring；静态推断为所属类上的 `snapshot` 行为。 | 0 | 1 |
| `backend/src/qts/indicators/rolling.py:35` | `method` | `qts.indicators.rolling.RollingWindow.restore` | 未写 docstring；静态推断为所属类上的 `restore` 行为。 | 1 | 2 |
| `backend/src/qts/indicators/rolling.py:41` | `method` | `qts.indicators.rolling.RollingWindow.__iter__` | 未写 docstring；实现 Python 协议方法 `__iter__`。 | 0 | 1 |
| `backend/src/qts/indicators/rolling.py:44` | `method` | `qts.indicators.rolling.RollingWindow.__len__` | 未写 docstring；实现 Python 协议方法 `__len__`。 | 0 | 1 |
| `backend/src/qts/load/bootstrap.py:8` | `module_function` | `qts.load.bootstrap.bootstrap_local` | Create local runtime directories and marker files safely. | 0 | 8 |
| `backend/src/qts/load/synthetic_market_data.py:14` | `class` | `qts.load.synthetic_market_data.SyntheticMarketDataConfig` | 未写 docstring；静态推断为定义 Synthetic Market Data Config 概念或数据结构。 | 0 | 1 |
| `backend/src/qts/load/synthetic_market_data.py:23` | `method` | `qts.load.synthetic_market_data.SyntheticMarketDataConfig.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 5 |
| `backend/src/qts/load/synthetic_market_data.py:32` | `module_function` | `qts.load.synthetic_market_data.generate_bars` | 未写 docstring；静态推断为 `generate bars` 函数，具体语义以实现为准。 | 1 | 9 |
| `backend/src/qts/observability/audit.py:10` | `class` | `qts.observability.audit.AuditEvent` | Operational or trading audit event. | 0 | 1 |
| `backend/src/qts/observability/audit.py:19` | `method` | `qts.observability.audit.AuditEvent.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 6 |
| `backend/src/qts/observability/logging.py:14` | `module_function` | `qts.observability.logging.build_log_record` | Build a structured log record without exposing secret values. | 2 | 10 |
| `backend/src/qts/observability/logging.py:42` | `module_function` | `qts.observability.logging._metadata_fields` | 未写 docstring；静态推断为 `metadata fields` 函数，具体语义以实现为准。 | 0 | 5 |
| `backend/src/qts/observability/logging.py:67` | `module_function` | `qts.observability.logging._is_secret_key` | 未写 docstring；静态推断为 `is secret key` 函数，具体语义以实现为准。 | 0 | 2 |
| `backend/src/qts/observability/metrics.py:10` | `class` | `qts.observability.metrics.MetricsRegistry` | Record counters and gauges with deterministic key formatting. | 0 | 0 |
| `backend/src/qts/observability/metrics.py:13` | `method` | `qts.observability.metrics.MetricsRegistry.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 0 | 0 |
| `backend/src/qts/observability/metrics.py:16` | `method` | `qts.observability.metrics.MetricsRegistry.increment` | 未写 docstring；静态推断为所属类上的 `increment` 行为。 | 1 | 3 |
| `backend/src/qts/observability/metrics.py:26` | `method` | `qts.observability.metrics.MetricsRegistry.gauge` | 未写 docstring；静态推断为所属类上的 `gauge` 行为。 | 1 | 1 |
| `backend/src/qts/observability/metrics.py:31` | `method` | `qts.observability.metrics.MetricsRegistry.observe_queue` | 未写 docstring；静态推断为所属类上的 `observe queue` 行为。 | 1 | 2 |
| `backend/src/qts/observability/metrics.py:45` | `method` | `qts.observability.metrics.MetricsRegistry.snapshot` | 未写 docstring；静态推断为所属类上的 `snapshot` 行为。 | 0 | 3 |
| `backend/src/qts/observability/metrics.py:49` | `staticmethod` | `qts.observability.metrics.MetricsRegistry._metric_key` | 未写 docstring；静态推断为所属类上的 `metric key` 行为。 | 0 | 4 |
| `backend/src/qts/portfolio/accounting/fill_accounting.py:14` | `class` | `qts.portfolio.accounting.fill_accounting.TradeSide` | Fill side. | 0 | 0 |
| `backend/src/qts/portfolio/accounting/fill_accounting.py:22` | `class` | `qts.portfolio.accounting.fill_accounting.Fill` | Executed fill used by accounting. | 0 | 1 |
| `backend/src/qts/portfolio/accounting/fill_accounting.py:33` | `method` | `qts.portfolio.accounting.fill_accounting.Fill.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 8 |
| `backend/src/qts/portfolio/accounting/fill_accounting.py:44` | `class` | `qts.portfolio.accounting.fill_accounting.FillAccounting` | Fill accounting operations. | 0 | 0 |
| `backend/src/qts/portfolio/accounting/fill_accounting.py:48` | `staticmethod` | `qts.portfolio.accounting.fill_accounting.FillAccounting.apply` | 未写 docstring；静态推断为应用状态变更、规则或计算结果（名称：apply）。 | 0 | 2 |
| `backend/src/qts/portfolio/cash_book.py:11` | `class` | `qts.portfolio.cash_book.CashBook` | Mutable cash balance book intended to be owned by AccountActor later. | 0 | 0 |
| `backend/src/qts/portfolio/cash_book.py:14` | `method` | `qts.portfolio.cash_book.CashBook.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 0 | 1 |
| `backend/src/qts/portfolio/cash_book.py:17` | `method` | `qts.portfolio.cash_book.CashBook.apply_delta` | 未写 docstring；静态推断为应用状态变更、规则或计算结果（名称：apply delta）。 | 2 | 2 |
| `backend/src/qts/portfolio/cash_book.py:21` | `method` | `qts.portfolio.cash_book.CashBook.balance` | 未写 docstring；静态推断为所属类上的 `balance` 行为。 | 1 | 3 |
| `backend/src/qts/portfolio/cash_book.py:24` | `method` | `qts.portfolio.cash_book.CashBook.available` | 未写 docstring；静态推断为所属类上的 `available` 行为。 | 2 | 3 |
| `backend/src/qts/portfolio/cash_book.py:29` | `staticmethod` | `qts.portfolio.cash_book.CashBook._normalize_currency` | 未写 docstring；静态推断为所属类上的 `normalize currency` 行为。 | 0 | 3 |
| `backend/src/qts/portfolio/position_book.py:14` | `class` | `qts.portfolio.position_book.Position` | Immutable position snapshot. | 0 | 1 |
| `backend/src/qts/portfolio/position_book.py:21` | `class` | `qts.portfolio.position_book.PositionBook` | Mutable position book intended to be owned by AccountActor later. | 0 | 0 |
| `backend/src/qts/portfolio/position_book.py:24` | `method` | `qts.portfolio.position_book.PositionBook.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 0 | 1 |
| `backend/src/qts/portfolio/position_book.py:27` | `method` | `qts.portfolio.position_book.PositionBook.apply_delta` | 未写 docstring；静态推断为应用状态变更、规则或计算结果（名称：apply delta）。 | 1 | 1 |
| `backend/src/qts/portfolio/position_book.py:30` | `method` | `qts.portfolio.position_book.PositionBook.quantity` | 未写 docstring；静态推断为所属类上的 `quantity` 行为。 | 0 | 2 |
| `backend/src/qts/portfolio/position_book.py:33` | `method` | `qts.portfolio.position_book.PositionBook.snapshot` | 未写 docstring；静态推断为所属类上的 `snapshot` 行为。 | 1 | 3 |
| `backend/src/qts/portfolio/reservation_book.py:12` | `class` | `qts.portfolio.reservation_book.Reservation` | Cash reservation by order ID. | 0 | 1 |
| `backend/src/qts/portfolio/reservation_book.py:20` | `class` | `qts.portfolio.reservation_book.ReservationBook` | Idempotent cash reservations keyed by order ID. | 0 | 0 |
| `backend/src/qts/portfolio/reservation_book.py:23` | `method` | `qts.portfolio.reservation_book.ReservationBook.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 0 | 0 |
| `backend/src/qts/portfolio/reservation_book.py:26` | `method` | `qts.portfolio.reservation_book.ReservationBook.reserve` | 未写 docstring；静态推断为所属类上的 `reserve` 行为。 | 2 | 4 |
| `backend/src/qts/portfolio/reservation_book.py:38` | `method` | `qts.portfolio.reservation_book.ReservationBook.release` | 未写 docstring；静态推断为所属类上的 `release` 行为。 | 0 | 1 |
| `backend/src/qts/portfolio/reservation_book.py:41` | `method` | `qts.portfolio.reservation_book.ReservationBook.reserved` | 未写 docstring；静态推断为所属类上的 `reserved` 行为。 | 1 | 4 |
| `backend/src/qts/portfolio/reservation_book.py:53` | `staticmethod` | `qts.portfolio.reservation_book.ReservationBook._normalize_currency` | 未写 docstring；静态推断为所属类上的 `normalize currency` 行为。 | 0 | 3 |
| `backend/src/qts/portfolio/valuation/models.py:8` | `module_function` | `qts.portfolio.valuation.models.equity_notional` | 未写 docstring；静态推断为 `equity notional` 函数，具体语义以实现为准。 | 0 | 0 |
| `backend/src/qts/portfolio/valuation/models.py:12` | `module_function` | `qts.portfolio.valuation.models.future_pnl` | 未写 docstring；静态推断为 `future pnl` 函数，具体语义以实现为准。 | 0 | 0 |
| `backend/src/qts/portfolio/valuation/models.py:22` | `module_function` | `qts.portfolio.valuation.models.option_premium_value` | 未写 docstring；静态推断为 `option premium value` 函数，具体语义以实现为准。 | 0 | 0 |
| `backend/src/qts/reconciliation.py:14` | `class` | `qts.reconciliation.DriftKind` | 未写 docstring；静态推断为定义 Drift Kind 概念，继承/实现 StrEnum。 | 0 | 0 |
| `backend/src/qts/reconciliation.py:23` | `class` | `qts.reconciliation.OrderSnapshot` | 未写 docstring；静态推断为定义 Order Snapshot 概念或数据结构。 | 0 | 1 |
| `backend/src/qts/reconciliation.py:30` | `method` | `qts.reconciliation.OrderSnapshot.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 4 |
| `backend/src/qts/reconciliation.py:38` | `class` | `qts.reconciliation.PositionSnapshot` | 未写 docstring；静态推断为定义 Position Snapshot 概念或数据结构。 | 0 | 1 |
| `backend/src/qts/reconciliation.py:44` | `class` | `qts.reconciliation.CashSnapshot` | 未写 docstring；静态推断为定义 Cash Snapshot 概念或数据结构。 | 0 | 1 |
| `backend/src/qts/reconciliation.py:48` | `method` | `qts.reconciliation.CashSnapshot.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 2 |
| `backend/src/qts/reconciliation.py:54` | `class` | `qts.reconciliation.ReconciliationSnapshot` | 未写 docstring；静态推断为定义 Reconciliation Snapshot 概念或数据结构。 | 0 | 1 |
| `backend/src/qts/reconciliation.py:62` | `class` | `qts.reconciliation.DriftItem` | 未写 docstring；静态推断为定义 Drift Item 概念或数据结构。 | 0 | 1 |
| `backend/src/qts/reconciliation.py:68` | `method` | `qts.reconciliation.DriftItem.to_dict` | 未写 docstring；静态推断为转换或序列化为指定目标表示（名称：to dict）。 | 0 | 0 |
| `backend/src/qts/reconciliation.py:78` | `class` | `qts.reconciliation.ReconciliationReport` | 未写 docstring；静态推断为定义 Reconciliation Report 概念或数据结构。 | 0 | 1 |
| `backend/src/qts/reconciliation.py:83` | `property` | `qts.reconciliation.ReconciliationReport.has_drift` | 未写 docstring；静态推断为判断是否存在指定状态或能力（名称：has drift）。 | 0 | 1 |
| `backend/src/qts/reconciliation.py:88` | `method` | `qts.reconciliation.ReconciliationReport.to_dict` | 未写 docstring；静态推断为转换或序列化为指定目标表示（名称：to dict）。 | 0 | 1 |
| `backend/src/qts/reconciliation.py:97` | `class` | `qts.reconciliation.StartupReconciliationDecision` | Startup gate result derived from reconciliation drift. | 0 | 1 |
| `backend/src/qts/reconciliation.py:105` | `module_function` | `qts.reconciliation.startup_reconciliation_gate` | Block trading on startup when reconciliation contains critical drift. | 1 | 2 |
| `backend/src/qts/reconciliation.py:117` | `module_function` | `qts.reconciliation.reconcile_snapshots` | 未写 docstring；静态推断为 `reconcile snapshots` 函数，具体语义以实现为准。 | 5 | 10 |
| `backend/src/qts/reconciliation.py:139` | `module_function` | `qts.reconciliation._compare_orders` | 未写 docstring；静态推断为 `compare orders` 函数，具体语义以实现为准。 | 2 | 19 |
| `backend/src/qts/reconciliation.py:170` | `module_function` | `qts.reconciliation._compare_positions` | 未写 docstring；静态推断为 `compare positions` 函数，具体语义以实现为准。 | 1 | 7 |
| `backend/src/qts/reconciliation.py:186` | `module_function` | `qts.reconciliation._compare_cash` | 未写 docstring；静态推断为 `compare cash` 函数，具体语义以实现为准。 | 1 | 7 |
| `backend/src/qts/reconciliation.py:202` | `module_function` | `qts.reconciliation._quantity_item` | 未写 docstring；静态推断为 `quantity item` 函数，具体语义以实现为准。 | 3 | 10 |
| `backend/src/qts/reconciliation.py:223` | `module_function` | `qts.reconciliation._order_repr` | 未写 docstring；静态推断为 `order repr` 函数，具体语义以实现为准。 | 0 | 0 |
| `backend/src/qts/reconciliation.py:229` | `module_function` | `qts.reconciliation._amount` | 未写 docstring；静态推断为 `amount` 函数，具体语义以实现为准。 | 0 | 1 |
| `backend/src/qts/reconciliation.py:235` | `module_function` | `qts.reconciliation._amount_repr` | 未写 docstring；静态推断为 `amount repr` 函数，具体语义以实现为准。 | 1 | 2 |
| `backend/src/qts/reconciliation.py:241` | `module_function` | `qts.reconciliation._drift_sort_key` | 未写 docstring；静态推断为 `drift sort key` 函数，具体语义以实现为准。 | 0 | 1 |
| `backend/src/qts/registry/broker_symbol_mapping.py:8` | `class` | `qts.registry.broker_symbol_mapping.BrokerSymbolMapping` | Bidirectional mapping between internal IDs and one broker's symbols. | 0 | 0 |
| `backend/src/qts/registry/broker_symbol_mapping.py:11` | `method` | `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 0 | 0 |
| `backend/src/qts/registry/broker_symbol_mapping.py:16` | `method` | `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.register` | 未写 docstring；静态推断为所属类上的 `register` 行为。 | 1 | 3 |
| `backend/src/qts/registry/broker_symbol_mapping.py:24` | `method` | `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.to_broker_symbol` | 未写 docstring；静态推断为转换或序列化为指定目标表示（名称：to broker symbol）。 | 0 | 1 |
| `backend/src/qts/registry/broker_symbol_mapping.py:30` | `method` | `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.to_instrument_id` | 未写 docstring；静态推断为转换或序列化为指定目标表示（名称：to instrument id）。 | 1 | 2 |
| `backend/src/qts/registry/broker_symbol_mapping.py:39` | `method` | `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.is_supported_symbol` | 未写 docstring；静态推断为判断布尔条件（名称：is supported symbol）。 | 1 | 1 |
| `backend/src/qts/registry/broker_symbol_mapping.py:42` | `method` | `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.instrument_id_for_symbol` | 未写 docstring；静态推断为所属类上的 `instrument id for symbol` 行为。 | 1 | 1 |
| `backend/src/qts/registry/broker_symbol_mapping.py:46` | `staticmethod` | `qts.registry.broker_symbol_mapping.BrokerSymbolMapping._normalize_broker_symbol` | 未写 docstring；静态推断为所属类上的 `normalize broker symbol` 行为。 | 0 | 2 |
| `backend/src/qts/registry/calendar_registry.py:13` | `class` | `qts.registry.calendar_registry.MarketSession` | Internal half-open exchange session. | 0 | 1 |
| `backend/src/qts/registry/calendar_registry.py:20` | `method` | `qts.registry.calendar_registry.MarketSession.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 4 |
| `backend/src/qts/registry/calendar_registry.py:27` | `property` | `qts.registry.calendar_registry.MarketSession.open_time` | 未写 docstring；静态推断为打开资源或建立状态（名称：open time）。 | 0 | 0 |
| `backend/src/qts/registry/calendar_registry.py:31` | `property` | `qts.registry.calendar_registry.MarketSession.close_time` | 未写 docstring；静态推断为关闭资源或头寸（名称：close time）。 | 0 | 0 |
| `backend/src/qts/registry/calendar_registry.py:35` | `class` | `qts.registry.calendar_registry.CalendarProvider` | Provider interface for internal calendar session lookup. | 0 | 0 |
| `backend/src/qts/registry/calendar_registry.py:38` | `method` | `qts.registry.calendar_registry.CalendarProvider.session_for` | Return the exchange session for a date. | 0 | 0 |
| `backend/src/qts/registry/calendar_registry.py:42` | `class` | `qts.registry.calendar_registry.CalendarRegistry` | Lookup table for calendar providers. | 0 | 0 |
| `backend/src/qts/registry/calendar_registry.py:45` | `method` | `qts.registry.calendar_registry.CalendarRegistry.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 0 | 0 |
| `backend/src/qts/registry/calendar_registry.py:48` | `method` | `qts.registry.calendar_registry.CalendarRegistry.register` | 未写 docstring；静态推断为所属类上的 `register` 行为。 | 0 | 2 |
| `backend/src/qts/registry/calendar_registry.py:53` | `method` | `qts.registry.calendar_registry.CalendarRegistry.session_for` | 未写 docstring；静态推断为所属类上的 `session for` 行为。 | 0 | 2 |
| `backend/src/qts/registry/future_chain_registry.py:11` | `class` | `qts.registry.future_chain_registry.FutureChain` | Ordered concrete future contracts for a root symbol. | 0 | 1 |
| `backend/src/qts/registry/future_chain_registry.py:17` | `method` | `qts.registry.future_chain_registry.FutureChain.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 3 |
| `backend/src/qts/registry/future_chain_registry.py:25` | `class` | `qts.registry.future_chain_registry.ContinuousFutureRef` | Research/data reference to a rolling future contract. | 0 | 1 |
| `backend/src/qts/registry/future_chain_registry.py:31` | `method` | `qts.registry.future_chain_registry.ContinuousFutureRef.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 3 |
| `backend/src/qts/registry/future_chain_registry.py:38` | `class` | `qts.registry.future_chain_registry.FutureChainRegistry` | Resolve future roots to concrete tradable contracts. | 0 | 0 |
| `backend/src/qts/registry/future_chain_registry.py:41` | `method` | `qts.registry.future_chain_registry.FutureChainRegistry.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 0 | 0 |
| `backend/src/qts/registry/future_chain_registry.py:44` | `method` | `qts.registry.future_chain_registry.FutureChainRegistry.register` | 未写 docstring；静态推断为所属类上的 `register` 行为。 | 1 | 1 |
| `backend/src/qts/registry/future_chain_registry.py:47` | `method` | `qts.registry.future_chain_registry.FutureChainRegistry.resolve_contract` | 未写 docstring；静态推断为解析标识、引用或配置到目标对象（名称：resolve contract）。 | 1 | 2 |
| `backend/src/qts/registry/future_chain_registry.py:56` | `method` | `qts.registry.future_chain_registry.FutureChainRegistry.require_tradable` | 未写 docstring；静态推断为所属类上的 `require tradable` 行为。 | 0 | 2 |
| `backend/src/qts/registry/future_chain_registry.py:61` | `method` | `qts.registry.future_chain_registry.FutureChainRegistry._get_chain` | 未写 docstring；静态推断为所属类上的 `get chain` 行为。 | 1 | 2 |
| `backend/src/qts/registry/future_chain_registry.py:69` | `staticmethod` | `qts.registry.future_chain_registry.FutureChainRegistry._normalize_root` | 未写 docstring；静态推断为所属类上的 `normalize root` 行为。 | 0 | 3 |
| `backend/src/qts/registry/future_roll.py:16` | `class` | `qts.registry.future_roll.FutureContractCandidate` | One concrete futures contract candidate at a decision timestamp. | 0 | 1 |
| `backend/src/qts/registry/future_roll.py:26` | `method` | `qts.registry.future_roll.FutureContractCandidate.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 6 |
| `backend/src/qts/registry/future_roll.py:35` | `class` | `qts.registry.future_roll.FutureContractSelector` | Select one concrete future from same-root same-time candidates. | 0 | 0 |
| `backend/src/qts/registry/future_roll.py:38` | `method` | `qts.registry.future_roll.FutureContractSelector.select` | 未写 docstring；静态推断为所属类上的 `select` 行为。 | 0 | 0 |
| `backend/src/qts/registry/future_roll.py:44` | `class` | `qts.registry.future_roll.HighestVolumeFutureContractSelector` | Select the most liquid candidate for one root at one timestamp. | 0 | 0 |
| `backend/src/qts/registry/future_roll.py:47` | `method` | `qts.registry.future_roll.HighestVolumeFutureContractSelector.select` | 未写 docstring；静态推断为所属类上的 `select` 行为。 | 0 | 2 |
| `backend/src/qts/registry/future_roll.py:64` | `class` | `qts.registry.future_roll.FutureRollSelection` | Resolved concrete contract for a continuous future at one timestamp. | 0 | 1 |
| `backend/src/qts/registry/future_roll.py:74` | `method` | `qts.registry.future_roll.FutureRollSelection.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 4 |
| `backend/src/qts/registry/future_roll.py:81` | `class` | `qts.registry.future_roll.FutureRollRegistry` | Resolve continuous futures to concrete contracts over time. | 0 | 0 |
| `backend/src/qts/registry/future_roll.py:84` | `method` | `qts.registry.future_roll.FutureRollRegistry.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 0 | 0 |
| `backend/src/qts/registry/future_roll.py:93` | `method` | `qts.registry.future_roll.FutureRollRegistry.register_root` | 未写 docstring；静态推断为所属类上的 `register root` 行为。 | 2 | 12 |
| `backend/src/qts/registry/future_roll.py:115` | `method` | `qts.registry.future_roll.FutureRollRegistry.continuous_instrument_id` | 未写 docstring；静态推断为所属类上的 `continuous instrument id` 行为。 | 1 | 3 |
| `backend/src/qts/registry/future_roll.py:124` | `method` | `qts.registry.future_roll.FutureRollRegistry.record_selection` | 未写 docstring；静态推断为所属类上的 `record selection` 行为。 | 0 | 7 |
| `backend/src/qts/registry/future_roll.py:141` | `method` | `qts.registry.future_roll.FutureRollRegistry.is_continuous` | 未写 docstring；静态推断为判断布尔条件（名称：is continuous）。 | 0 | 0 |
| `backend/src/qts/registry/future_roll.py:144` | `method` | `qts.registry.future_roll.FutureRollRegistry.resolve_contract` | 未写 docstring；静态推断为解析标识、引用或配置到目标对象（名称：resolve contract）。 | 2 | 4 |
| `backend/src/qts/registry/future_roll.py:161` | `method` | `qts.registry.future_roll.FutureRollRegistry.related_contracts` | 未写 docstring；静态推断为所属类上的 `related contracts` 行为。 | 0 | 1 |
| `backend/src/qts/registry/future_roll.py:167` | `method` | `qts.registry.future_roll.FutureRollRegistry.execution_price` | 未写 docstring；静态推断为所属类上的 `execution price` 行为。 | 1 | 3 |
| `backend/src/qts/registry/future_roll.py:182` | `method` | `qts.registry.future_roll.FutureRollRegistry._selection_at` | 未写 docstring；静态推断为所属类上的 `selection at` 行为。 | 0 | 4 |
| `backend/src/qts/registry/future_roll.py:202` | `staticmethod` | `qts.registry.future_roll.FutureRollRegistry._normalize_root` | 未写 docstring；静态推断为所属类上的 `normalize root` 行为。 | 0 | 3 |
| `backend/src/qts/registry/instrument_registry.py:9` | `class` | `qts.registry.instrument_registry.InstrumentRegistry` | Resolve user-facing symbols to internal instruments. | 0 | 0 |
| `backend/src/qts/registry/instrument_registry.py:12` | `method` | `qts.registry.instrument_registry.InstrumentRegistry.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 0 | 0 |
| `backend/src/qts/registry/instrument_registry.py:16` | `method` | `qts.registry.instrument_registry.InstrumentRegistry.register` | 未写 docstring；静态推断为所属类上的 `register` 行为。 | 1 | 1 |
| `backend/src/qts/registry/instrument_registry.py:21` | `method` | `qts.registry.instrument_registry.InstrumentRegistry.resolve` | 未写 docstring；静态推断为解析标识、引用或配置到目标对象（名称：resolve）。 | 1 | 2 |
| `backend/src/qts/registry/instrument_registry.py:28` | `method` | `qts.registry.instrument_registry.InstrumentRegistry.get_instrument` | 未写 docstring；静态推断为读取或返回值（名称：get instrument）。 | 0 | 1 |
| `backend/src/qts/registry/instrument_registry.py:34` | `method` | `qts.registry.instrument_registry.InstrumentRegistry.get_contract_spec` | 未写 docstring；静态推断为读取或返回值（名称：get contract spec）。 | 1 | 1 |
| `backend/src/qts/registry/instrument_registry.py:38` | `staticmethod` | `qts.registry.instrument_registry.InstrumentRegistry._normalize_symbol` | 未写 docstring；静态推断为所属类上的 `normalize symbol` 行为。 | 0 | 3 |
| `backend/src/qts/registry/option_chain_registry.py:12` | `class` | `qts.registry.option_chain_registry.OptionChainRegistry` | Lookup option instruments by underlying and simple filters. | 0 | 0 |
| `backend/src/qts/registry/option_chain_registry.py:15` | `method` | `qts.registry.option_chain_registry.OptionChainRegistry.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 0 | 0 |
| `backend/src/qts/registry/option_chain_registry.py:18` | `method` | `qts.registry.option_chain_registry.OptionChainRegistry.register` | 未写 docstring；静态推断为所属类上的 `register` 行为。 | 0 | 4 |
| `backend/src/qts/registry/option_chain_registry.py:25` | `method` | `qts.registry.option_chain_registry.OptionChainRegistry.options_for` | 未写 docstring；静态推断为所属类上的 `options for` 行为。 | 0 | 2 |
| `backend/src/qts/registry/option_chain_registry.py:31` | `method` | `qts.registry.option_chain_registry.OptionChainRegistry.find` | 未写 docstring；静态推断为所属类上的 `find` 行为。 | 1 | 4 |
| `backend/src/qts/registry/providers/comex_gold_calendar_provider.py:12` | `class` | `qts.registry.providers.comex_gold_calendar_provider.ComexGoldCalendarProvider` | Regular COMEX Gold session provider for anchor-verified semantics. | 0 | 1 |
| `backend/src/qts/registry/providers/comex_gold_calendar_provider.py:18` | `method` | `qts.registry.providers.comex_gold_calendar_provider.ComexGoldCalendarProvider.session_for` | 未写 docstring；静态推断为所属类上的 `session for` 行为。 | 2 | 12 |
| `backend/src/qts/registry/providers/exchange_calendar_provider.py:14` | `class` | `qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider` | Calendar provider backed by ``exchange-calendars``. | 0 | 0 |
| `backend/src/qts/registry/providers/exchange_calendar_provider.py:17` | `method` | `qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 0 | 3 |
| `backend/src/qts/registry/providers/exchange_calendar_provider.py:23` | `method` | `qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider.session_for` | 未写 docstring；静态推断为所属类上的 `session for` 行为。 | 3 | 7 |
| `backend/src/qts/registry/providers/exchange_calendar_provider.py:34` | `staticmethod` | `qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider._to_datetime` | 未写 docstring；静态推断为所属类上的 `to datetime` 行为。 | 0 | 6 |
| `backend/src/qts/registry/symbol_resolution.py:12` | `class` | `qts.registry.symbol_resolution.SourceSymbolResolver` | Resolve external source symbols into internal instrument IDs. | 0 | 0 |
| `backend/src/qts/registry/symbol_resolution.py:15` | `method` | `qts.registry.symbol_resolution.SourceSymbolResolver.is_supported_symbol` | 未写 docstring；静态推断为判断布尔条件（名称：is supported symbol）。 | 0 | 0 |
| `backend/src/qts/registry/symbol_resolution.py:17` | `method` | `qts.registry.symbol_resolution.SourceSymbolResolver.instrument_id_for_symbol` | 未写 docstring；静态推断为所属类上的 `instrument id for symbol` 行为。 | 0 | 0 |
| `backend/src/qts/registry/symbol_resolution.py:21` | `class` | `qts.registry.symbol_resolution.StaticSymbolResolver` | Resolve source symbols from an explicit symbol-to-instrument mapping. | 0 | 2 |
| `backend/src/qts/registry/symbol_resolution.py:27` | `method` | `qts.registry.symbol_resolution.StaticSymbolResolver.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 1 | 5 |
| `backend/src/qts/registry/symbol_resolution.py:38` | `method` | `qts.registry.symbol_resolution.StaticSymbolResolver.is_supported_symbol` | 未写 docstring；静态推断为判断布尔条件（名称：is supported symbol）。 | 1 | 1 |
| `backend/src/qts/registry/symbol_resolution.py:41` | `method` | `qts.registry.symbol_resolution.StaticSymbolResolver.instrument_id_for_symbol` | 未写 docstring；静态推断为所属类上的 `instrument id for symbol` 行为。 | 1 | 2 |
| `backend/src/qts/registry/symbol_resolution.py:49` | `staticmethod` | `qts.registry.symbol_resolution.StaticSymbolResolver._normalize_symbol` | 未写 docstring；静态推断为所属类上的 `normalize symbol` 行为。 | 0 | 3 |
| `backend/src/qts/risk/config.py:10` | `class` | `qts.risk.config.RiskRuleConfig` | One configured risk rule. | 0 | 1 |
| `backend/src/qts/risk/config.py:17` | `method` | `qts.risk.config.RiskRuleConfig.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 4 |
| `backend/src/qts/risk/config.py:25` | `class` | `qts.risk.config.RiskConfig` | Account/strategy/product risk configuration. | 0 | 2 |
| `backend/src/qts/risk/config.py:34` | `method` | `qts.risk.config.RiskConfig.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 6 |
| `backend/src/qts/risk/kill_switch.py:12` | `class` | `qts.risk.kill_switch.KillSwitchScopeType` | 未写 docstring；静态推断为定义 Kill Switch Scope Type 概念，继承/实现 StrEnum。 | 0 | 0 |
| `backend/src/qts/risk/kill_switch.py:20` | `class` | `qts.risk.kill_switch.KillSwitchScope` | 未写 docstring；静态推断为定义 Kill Switch Scope 概念或数据结构。 | 0 | 1 |
| `backend/src/qts/risk/kill_switch.py:25` | `classmethod` | `qts.risk.kill_switch.KillSwitchScope.global_scope` | 未写 docstring；静态推断为所属类上的 `global scope` 行为。 | 0 | 1 |
| `backend/src/qts/risk/kill_switch.py:29` | `classmethod` | `qts.risk.kill_switch.KillSwitchScope.account` | 未写 docstring；静态推断为所属类上的 `account` 行为。 | 0 | 1 |
| `backend/src/qts/risk/kill_switch.py:33` | `classmethod` | `qts.risk.kill_switch.KillSwitchScope.strategy` | 未写 docstring；静态推断为所属类上的 `strategy` 行为。 | 0 | 1 |
| `backend/src/qts/risk/kill_switch.py:37` | `classmethod` | `qts.risk.kill_switch.KillSwitchScope.broker` | 未写 docstring；静态推断为所属类上的 `broker` 行为。 | 0 | 1 |
| `backend/src/qts/risk/kill_switch.py:40` | `method` | `qts.risk.kill_switch.KillSwitchScope.reason_code` | 未写 docstring；静态推断为所属类上的 `reason code` 行为。 | 0 | 1 |
| `backend/src/qts/risk/kill_switch.py:45` | `class` | `qts.risk.kill_switch.KillSwitchState` | 未写 docstring；静态推断为定义 Kill Switch State 概念或数据结构。 | 0 | 1 |
| `backend/src/qts/risk/kill_switch.py:51` | `class` | `qts.risk.kill_switch.KillSwitchRegistry` | Auditable in-memory kill-switch registry. | 0 | 0 |
| `backend/src/qts/risk/kill_switch.py:54` | `method` | `qts.risk.kill_switch.KillSwitchRegistry.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 0 | 0 |
| `backend/src/qts/risk/kill_switch.py:57` | `method` | `qts.risk.kill_switch.KillSwitchRegistry.activate` | 未写 docstring；静态推断为所属类上的 `activate` 行为。 | 1 | 3 |
| `backend/src/qts/risk/kill_switch.py:64` | `method` | `qts.risk.kill_switch.KillSwitchRegistry.deactivate` | 未写 docstring；静态推断为所属类上的 `deactivate` 行为。 | 1 | 3 |
| `backend/src/qts/risk/kill_switch.py:71` | `method` | `qts.risk.kill_switch.KillSwitchRegistry.check_order` | 未写 docstring；静态推断为所属类上的 `check order` 行为。 | 1 | 5 |
| `backend/src/qts/risk/kill_switch.py:91` | `staticmethod` | `qts.risk.kill_switch.KillSwitchRegistry._matching_scopes` | 未写 docstring；静态推断为所属类上的 `matching scopes` 行为。 | 0 | 6 |
| `backend/src/qts/risk/risk_engine.py:11` | `class` | `qts.risk.risk_engine.RiskEngine` | Apply risk rules in order and return the first rejection. | 0 | 0 |
| `backend/src/qts/risk/risk_engine.py:14` | `method` | `qts.risk.risk_engine.RiskEngine.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 0 | 1 |
| `backend/src/qts/risk/risk_engine.py:17` | `method` | `qts.risk.risk_engine.RiskEngine.check` | 未写 docstring；静态推断为所属类上的 `check` 行为。 | 0 | 2 |
| `backend/src/qts/risk/rule.py:10` | `class` | `qts.risk.rule.RiskRule` | A pre-trade risk rule. | 0 | 0 |
| `backend/src/qts/risk/rule.py:13` | `method` | `qts.risk.rule.RiskRule.check` | Return an explicit risk decision. | 0 | 0 |
| `backend/src/qts/risk/rule_registry.py:13` | `class` | `qts.risk.rule_registry.RiskRuleRegistry` | Map configured rule names to executable risk rules. | 0 | 0 |
| `backend/src/qts/risk/rule_registry.py:16` | `method` | `qts.risk.rule_registry.RiskRuleRegistry.build` | 未写 docstring；静态推断为组装对象、请求或运行上下文（名称：build）。 | 3 | 5 |
| `backend/src/qts/risk/rule_registry.py:24` | `staticmethod` | `qts.risk.rule_registry.RiskRuleRegistry._param` | 未写 docstring；静态推断为所属类上的 `param` 行为。 | 0 | 1 |
| `backend/src/qts/risk/rules/max_notional.py:12` | `class` | `qts.risk.rules.max_notional.MaxNotionalRule` | Reject orders whose notional exceeds a fixed limit. | 0 | 1 |
| `backend/src/qts/risk/rules/max_notional.py:17` | `method` | `qts.risk.rules.max_notional.MaxNotionalRule.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 2 |
| `backend/src/qts/risk/rules/max_notional.py:21` | `method` | `qts.risk.rules.max_notional.MaxNotionalRule.check` | 未写 docstring；静态推断为所属类上的 `check` 行为。 | 0 | 2 |
| `backend/src/qts/risk/rules/max_order_qty.py:12` | `class` | `qts.risk.rules.max_order_qty.MaxOrderQuantityRule` | Reject orders whose absolute quantity exceeds a fixed limit. | 0 | 1 |
| `backend/src/qts/risk/rules/max_order_qty.py:17` | `method` | `qts.risk.rules.max_order_qty.MaxOrderQuantityRule.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 2 |
| `backend/src/qts/risk/rules/max_order_qty.py:21` | `method` | `qts.risk.rules.max_order_qty.MaxOrderQuantityRule.check` | 未写 docstring；静态推断为所属类上的 `check` 行为。 | 0 | 2 |
| `backend/src/qts/risk/rules/trading_session_rule.py:13` | `class` | `qts.risk.rules.trading_session_rule.SessionLookup` | Calendar session lookup required by the rule. | 0 | 0 |
| `backend/src/qts/risk/rules/trading_session_rule.py:16` | `method` | `qts.risk.rules.trading_session_rule.SessionLookup.session_for` | Return the internal market session for the date. | 0 | 0 |
| `backend/src/qts/risk/rules/trading_session_rule.py:21` | `class` | `qts.risk.rules.trading_session_rule.TradingSessionRule` | Reject orders whose order time is outside the configured session. | 0 | 1 |
| `backend/src/qts/risk/rules/trading_session_rule.py:28` | `method` | `qts.risk.rules.trading_session_rule.TradingSessionRule.check` | 未写 docstring；静态推断为所属类上的 `check` 行为。 | 0 | 5 |
| `backend/src/qts/runtime/actor.py:8` | `class` | `qts.runtime.actor.Actor` | Base actor that handles messages serially through an ActorRef. | 0 | 0 |
| `backend/src/qts/runtime/actor.py:12` | `method` | `qts.runtime.actor.Actor.handle` | Handle one message. | 0 | 0 |
| `backend/src/qts/runtime/actor_ref.py:12` | `class` | `qts.runtime.actor_ref.ActorRef` | Message-only reference to an actor mailbox. | 0 | 1 |
| `backend/src/qts/runtime/actor_ref.py:18` | `method` | `qts.runtime.actor_ref.ActorRef.tell` | 未写 docstring；静态推断为所属类上的 `tell` 行为。 | 0 | 1 |
| `backend/src/qts/runtime/actor_ref.py:21` | `method` | `qts.runtime.actor_ref.ActorRef.process_one` | 未写 docstring；静态推断为所属类上的 `process one` 行为。 | 0 | 3 |
| `backend/src/qts/runtime/actor_ref.py:27` | `method` | `qts.runtime.actor_ref.ActorRef.process_all` | 未写 docstring；静态推断为所属类上的 `process all` 行为。 | 1 | 1 |
| `backend/src/qts/runtime/actors/account_actor.py:19` | `class` | `qts.runtime.actors.account_actor.ApplyFill` | Message instructing AccountActor to apply a validated fill. | 0 | 1 |
| `backend/src/qts/runtime/actors/account_actor.py:28` | `class` | `qts.runtime.actors.account_actor.AccountSnapshot` | Read-only account snapshot. | 0 | 1 |
| `backend/src/qts/runtime/actors/account_actor.py:35` | `class` | `qts.runtime.actors.account_actor.AccountActor` | Owns account cash and position state. | 0 | 0 |
| `backend/src/qts/runtime/actors/account_actor.py:38` | `method` | `qts.runtime.actors.account_actor.AccountActor.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 3 | 3 |
| `backend/src/qts/runtime/actors/account_actor.py:43` | `method` | `qts.runtime.actors.account_actor.AccountActor.handle` | 未写 docstring；静态推断为处理事件、命令或请求（名称：handle）。 | 1 | 4 |
| `backend/src/qts/runtime/actors/account_actor.py:49` | `method` | `qts.runtime.actors.account_actor.AccountActor.snapshot` | 未写 docstring；静态推断为所属类上的 `snapshot` 行为。 | 1 | 4 |
| `backend/src/qts/runtime/actors/account_actor.py:55` | `method` | `qts.runtime.actors.account_actor.AccountActor._apply_fill` | 未写 docstring；静态推断为所属类上的 `apply fill` 行为。 | 0 | 3 |
| `backend/src/qts/runtime/actors/execution_actor.py:15` | `class` | `qts.runtime.actors.execution_actor.ExecutionAdapter` | Execution boundary contract used by the actor. | 0 | 0 |
| `backend/src/qts/runtime/actors/execution_actor.py:18` | `method` | `qts.runtime.actors.execution_actor.ExecutionAdapter.execute_market_order` | 未写 docstring；静态推断为所属类上的 `execute market order` 行为。 | 0 | 0 |
| `backend/src/qts/runtime/actors/execution_actor.py:28` | `class` | `qts.runtime.actors.execution_actor.OrderExecutionRequest` | Message requesting order execution. | 0 | 1 |
| `backend/src/qts/runtime/actors/execution_actor.py:36` | `class` | `qts.runtime.actors.execution_actor.ExecutionActor` | Actor wrapper for an order execution adapter or simulator. | 0 | 0 |
| `backend/src/qts/runtime/actors/execution_actor.py:39` | `method` | `qts.runtime.actors.execution_actor.ExecutionActor.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 1 | 1 |
| `backend/src/qts/runtime/actors/execution_actor.py:48` | `method` | `qts.runtime.actors.execution_actor.ExecutionActor.handle` | 未写 docstring；静态推断为处理事件、命令或请求（名称：handle）。 | 0 | 5 |
| `backend/src/qts/runtime/actors/market_data_actor.py:29` | `class` | `qts.runtime.actors.market_data_actor.MarketDataEvent` | Normalized market data payload accepted by MarketDataActor. | 0 | 1 |
| `backend/src/qts/runtime/actors/market_data_actor.py:36` | `class` | `qts.runtime.actors.market_data_actor.SubscribeMarketData` | Message requesting strategy market data fan-out. | 0 | 1 |
| `backend/src/qts/runtime/actors/market_data_actor.py:44` | `method` | `qts.runtime.actors.market_data_actor.SubscribeMarketData.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 4 |
| `backend/src/qts/runtime/actors/market_data_actor.py:51` | `class` | `qts.runtime.actors.market_data_actor.MarketDataActor` | Actor boundary for normalized market data events. | 0 | 0 |
| `backend/src/qts/runtime/actors/market_data_actor.py:54` | `method` | `qts.runtime.actors.market_data_actor.MarketDataActor.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 1 | 4 |
| `backend/src/qts/runtime/actors/market_data_actor.py:75` | `method` | `qts.runtime.actors.market_data_actor.MarketDataActor.handle` | 未写 docstring；静态推断为处理事件、命令或请求（名称：handle）。 | 4 | 11 |
| `backend/src/qts/runtime/actors/market_data_actor.py:94` | `property` | `qts.runtime.actors.market_data_actor.MarketDataActor.logical_subscription_count` | 未写 docstring；静态推断为所属类上的 `logical subscription count` 行为。 | 0 | 1 |
| `backend/src/qts/runtime/actors/market_data_actor.py:98` | `property` | `qts.runtime.actors.market_data_actor.MarketDataActor.physical_subscription_count` | 未写 docstring；静态推断为所属类上的 `physical subscription count` 行为。 | 0 | 1 |
| `backend/src/qts/runtime/actors/market_data_actor.py:101` | `method` | `qts.runtime.actors.market_data_actor.MarketDataActor._subscribe` | 未写 docstring；静态推断为所属类上的 `subscribe` 行为。 | 5 | 9 |
| `backend/src/qts/runtime/actors/market_data_actor.py:131` | `method` | `qts.runtime.actors.market_data_actor.MarketDataActor._publish_to_logical_subscribers` | 未写 docstring；静态推断为所属类上的 `publish to logical subscribers` 行为。 | 3 | 9 |
| `backend/src/qts/runtime/actors/market_data_actor.py:156` | `method` | `qts.runtime.actors.market_data_actor.MarketDataActor._aggregator_for` | 未写 docstring；静态推断为所属类上的 `aggregator for` 行为。 | 1 | 4 |
| `backend/src/qts/runtime/actors/market_data_actor.py:169` | `method` | `qts.runtime.actors.market_data_actor.MarketDataActor._logical_aggregator_for` | 未写 docstring；静态推断为所属类上的 `logical aggregator for` 行为。 | 2 | 4 |
| `backend/src/qts/runtime/actors/market_data_actor.py:188` | `method` | `qts.runtime.actors.market_data_actor.MarketDataActor._publish` | 未写 docstring；静态推断为所属类上的 `publish` 行为。 | 0 | 1 |
| `backend/src/qts/runtime/actors/market_data_actor.py:193` | `staticmethod` | `qts.runtime.actors.market_data_actor.MarketDataActor._publish_to` | 未写 docstring；静态推断为所属类上的 `publish to` 行为。 | 0 | 1 |
| `backend/src/qts/runtime/actors/market_data_actor.py:198` | `staticmethod` | `qts.runtime.actors.market_data_actor.MarketDataActor._subscription_id` | 未写 docstring；静态推断为所属类上的 `subscription id` 行为。 | 0 | 1 |
| `backend/src/qts/runtime/actors/order_manager_actor.py:19` | `class` | `qts.runtime.actors.order_manager_actor.SubmitOrder` | Message to submit an approved order to an execution actor. | 0 | 1 |
| `backend/src/qts/runtime/actors/order_manager_actor.py:28` | `class` | `qts.runtime.actors.order_manager_actor.OrderManagerActor` | Actor-owned OrderManager wrapper. | 0 | 0 |
| `backend/src/qts/runtime/actors/order_manager_actor.py:31` | `method` | `qts.runtime.actors.order_manager_actor.OrderManagerActor.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 1 | 2 |
| `backend/src/qts/runtime/actors/order_manager_actor.py:44` | `method` | `qts.runtime.actors.order_manager_actor.OrderManagerActor.handle` | 未写 docstring；静态推断为处理事件、命令或请求（名称：handle）。 | 2 | 6 |
| `backend/src/qts/runtime/actors/order_manager_actor.py:53` | `method` | `qts.runtime.actors.order_manager_actor.OrderManagerActor.get_order` | 未写 docstring；静态推断为读取或返回值（名称：get order）。 | 0 | 1 |
| `backend/src/qts/runtime/actors/order_manager_actor.py:57` | `property` | `qts.runtime.actors.order_manager_actor.OrderManagerActor.fills` | 未写 docstring；静态推断为所属类上的 `fills` 行为。 | 0 | 1 |
| `backend/src/qts/runtime/actors/order_manager_actor.py:61` | `property` | `qts.runtime.actors.order_manager_actor.OrderManagerActor.fill_count` | 未写 docstring；静态推断为所属类上的 `fill count` 行为。 | 0 | 1 |
| `backend/src/qts/runtime/actors/order_manager_actor.py:64` | `method` | `qts.runtime.actors.order_manager_actor.OrderManagerActor.fills_since` | 未写 docstring；静态推断为所属类上的 `fills since` 行为。 | 0 | 1 |
| `backend/src/qts/runtime/actors/order_manager_actor.py:67` | `method` | `qts.runtime.actors.order_manager_actor.OrderManagerActor.compact_for_streaming` | 未写 docstring；静态推断为所属类上的 `compact for streaming` 行为。 | 0 | 2 |
| `backend/src/qts/runtime/actors/order_manager_actor.py:72` | `method` | `qts.runtime.actors.order_manager_actor.OrderManagerActor._handle_submit` | 未写 docstring；静态推断为所属类上的 `handle submit` 行为。 | 1 | 4 |
| `backend/src/qts/runtime/actors/order_manager_actor.py:83` | `method` | `qts.runtime.actors.order_manager_actor.OrderManagerActor._handle_report` | 未写 docstring；静态推断为所属类上的 `handle report` 行为。 | 1 | 6 |
| `backend/src/qts/runtime/actors/signal_aggregator_actor.py:14` | `class` | `qts.runtime.actors.signal_aggregator_actor.StrategySignalEvent` | Strategy intents emitted for one completed bar. | 0 | 1 |
| `backend/src/qts/runtime/actors/signal_aggregator_actor.py:22` | `class` | `qts.runtime.actors.signal_aggregator_actor.AggregatedSignalBatch` | Aggregated intents ready for portfolio/risk/order flow. | 0 | 1 |
| `backend/src/qts/runtime/actors/signal_aggregator_actor.py:29` | `class` | `qts.runtime.actors.signal_aggregator_actor.SignalAggregatorActor` | Boundary for combining strategy signals before order flow. | 0 | 0 |
| `backend/src/qts/runtime/actors/signal_aggregator_actor.py:32` | `method` | `qts.runtime.actors.signal_aggregator_actor.SignalAggregatorActor.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 0 | 0 |
| `backend/src/qts/runtime/actors/signal_aggregator_actor.py:35` | `method` | `qts.runtime.actors.signal_aggregator_actor.SignalAggregatorActor.handle` | 未写 docstring；静态推断为处理事件、命令或请求（名称：handle）。 | 1 | 5 |
| `backend/src/qts/runtime/actors/strategy_actor.py:14` | `class` | `qts.runtime.actors.strategy_actor.StrategyBarEvent` | Completed strategy-facing bar delivered to a strategy actor. | 0 | 1 |
| `backend/src/qts/runtime/actors/strategy_actor.py:23` | `class` | `qts.runtime.actors.strategy_actor.StrategyBarResult` | New strategy intents emitted while handling one bar. | 0 | 1 |
| `backend/src/qts/runtime/actors/strategy_actor.py:31` | `class` | `qts.runtime.actors.strategy_actor.StrategyFinalize` | Request strategy finalization. | 0 | 1 |
| `backend/src/qts/runtime/actors/strategy_actor.py:36` | `class` | `qts.runtime.actors.strategy_actor.StrategyFinalized` | Strategy finalization completed. | 0 | 1 |
| `backend/src/qts/runtime/actors/strategy_actor.py:42` | `class` | `qts.runtime.actors.strategy_actor.StrategyActor` | Actor-owned strategy instance and user-facing context. | 0 | 0 |
| `backend/src/qts/runtime/actors/strategy_actor.py:45` | `method` | `qts.runtime.actors.strategy_actor.StrategyActor.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 0 | 1 |
| `backend/src/qts/runtime/actors/strategy_actor.py:57` | `method` | `qts.runtime.actors.strategy_actor.StrategyActor.handle` | 未写 docstring；静态推断为处理事件、命令或请求（名称：handle）。 | 2 | 6 |
| `backend/src/qts/runtime/actors/strategy_actor.py:66` | `method` | `qts.runtime.actors.strategy_actor.StrategyActor._handle_bar` | 未写 docstring；静态推断为所属类上的 `handle bar` 行为。 | 1 | 5 |
| `backend/src/qts/runtime/actors/strategy_actor.py:79` | `method` | `qts.runtime.actors.strategy_actor.StrategyActor._handle_finalize` | 未写 docstring；静态推断为所属类上的 `handle finalize` 行为。 | 1 | 5 |
| `backend/src/qts/runtime/event_store.py:15` | `class` | `qts.runtime.event_store.EventStore` | Append-only event store contract. | 0 | 0 |
| `backend/src/qts/runtime/event_store.py:18` | `method` | `qts.runtime.event_store.EventStore.append` | 未写 docstring；静态推断为所属类上的 `append` 行为。 | 0 | 0 |
| `backend/src/qts/runtime/event_store.py:20` | `method` | `qts.runtime.event_store.EventStore.replay` | 未写 docstring；静态推断为所属类上的 `replay` 行为。 | 0 | 0 |
| `backend/src/qts/runtime/event_store.py:22` | `method` | `qts.runtime.event_store.EventStore.by_correlation_id` | 未写 docstring；静态推断为所属类上的 `by correlation id` 行为。 | 0 | 0 |
| `backend/src/qts/runtime/event_store.py:25` | `class` | `qts.runtime.event_store.InMemoryEventStore` | Deterministic append-only in-memory event store. | 0 | 0 |
| `backend/src/qts/runtime/event_store.py:28` | `method` | `qts.runtime.event_store.InMemoryEventStore.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 0 | 0 |
| `backend/src/qts/runtime/event_store.py:31` | `method` | `qts.runtime.event_store.InMemoryEventStore.append` | 未写 docstring；静态推断为所属类上的 `append` 行为。 | 0 | 2 |
| `backend/src/qts/runtime/event_store.py:35` | `method` | `qts.runtime.event_store.InMemoryEventStore.append_many` | 未写 docstring；静态推断为所属类上的 `append many` 行为。 | 1 | 1 |
| `backend/src/qts/runtime/event_store.py:39` | `method` | `qts.runtime.event_store.InMemoryEventStore.replay` | 未写 docstring；静态推断为所属类上的 `replay` 行为。 | 0 | 2 |
| `backend/src/qts/runtime/event_store.py:44` | `method` | `qts.runtime.event_store.InMemoryEventStore.by_correlation_id` | 未写 docstring；静态推断为所属类上的 `by correlation id` 行为。 | 0 | 1 |
| `backend/src/qts/runtime/event_store.py:48` | `class` | `qts.runtime.event_store.FileEventStore` | JSONL event store for local deterministic recovery tests. | 0 | 0 |
| `backend/src/qts/runtime/event_store.py:51` | `method` | `qts.runtime.event_store.FileEventStore.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 0 | 0 |
| `backend/src/qts/runtime/event_store.py:54` | `method` | `qts.runtime.event_store.FileEventStore.append` | 未写 docstring；静态推断为所属类上的 `append` 行为。 | 2 | 8 |
| `backend/src/qts/runtime/event_store.py:63` | `method` | `qts.runtime.event_store.FileEventStore.replay` | 未写 docstring；静态推断为所属类上的 `replay` 行为。 | 1 | 7 |
| `backend/src/qts/runtime/event_store.py:76` | `method` | `qts.runtime.event_store.FileEventStore.by_correlation_id` | 未写 docstring；静态推断为所属类上的 `by correlation id` 行为。 | 1 | 2 |
| `backend/src/qts/runtime/event_store.py:80` | `staticmethod` | `qts.runtime.event_store.FileEventStore._event_to_json` | 未写 docstring；静态推断为所属类上的 `event to json` 行为。 | 0 | 1 |
| `backend/src/qts/runtime/event_store.py:92` | `staticmethod` | `qts.runtime.event_store.FileEventStore._event_from_json` | 未写 docstring；静态推断为所属类上的 `event from json` 行为。 | 4 | 12 |
| `backend/src/qts/runtime/live.py:12` | `class` | `qts.runtime.live.LiveRuntimeState` | 未写 docstring；静态推断为定义 Live Runtime State 概念，继承/实现 StrEnum。 | 0 | 0 |
| `backend/src/qts/runtime/live.py:20` | `class` | `qts.runtime.live.LiveMode` | Runtime mode with explicit live-trading permissions. | 0 | 0 |
| `backend/src/qts/runtime/live.py:29` | `class` | `qts.runtime.live.LiveStartupConfig` | Startup guard inputs for live-capable runtime. | 0 | 1 |
| `backend/src/qts/runtime/live.py:41` | `class` | `qts.runtime.live.LiveStartupDecision` | Result of startup guard validation. | 0 | 1 |
| `backend/src/qts/runtime/live.py:48` | `module_function` | `qts.runtime.live.validate_live_startup` | Fail closed unless all live safety prerequisites are explicit. | 1 | 3 |
| `backend/src/qts/runtime/live.py:95` | `class` | `qts.runtime.live.LiveRuntimeStateMachine` | 未写 docstring；静态推断为定义 Live Runtime State Machine 概念或数据结构。 | 0 | 1 |
| `backend/src/qts/runtime/live.py:98` | `method` | `qts.runtime.live.LiveRuntimeStateMachine.apply` | 未写 docstring；静态推断为应用状态变更、规则或计算结果（名称：apply）。 | 0 | 3 |
| `backend/src/qts/runtime/live.py:107` | `class` | `qts.runtime.live.RuntimeOrderResult` | 未写 docstring；静态推断为定义 Runtime Order Result 概念或数据结构。 | 0 | 1 |
| `backend/src/qts/runtime/live.py:114` | `class` | `qts.runtime.live.LiveRuntime` | Small live-beta runtime wrapper over fake or real boundary adapters. | 0 | 0 |
| `backend/src/qts/runtime/live.py:117` | `method` | `qts.runtime.live.LiveRuntime.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 1 | 1 |
| `backend/src/qts/runtime/live.py:123` | `property` | `qts.runtime.live.LiveRuntime.state` | 未写 docstring；静态推断为所属类上的 `state` 行为。 | 0 | 0 |
| `backend/src/qts/runtime/live.py:127` | `property` | `qts.runtime.live.LiveRuntime.feed` | 未写 docstring；静态推断为所属类上的 `feed` 行为。 | 0 | 0 |
| `backend/src/qts/runtime/live.py:130` | `method` | `qts.runtime.live.LiveRuntime.start` | 未写 docstring；静态推断为启动流程或服务（名称：start）。 | 0 | 2 |
| `backend/src/qts/runtime/live.py:134` | `method` | `qts.runtime.live.LiveRuntime.stop` | 未写 docstring；静态推断为停止流程或服务（名称：stop）。 | 0 | 1 |
| `backend/src/qts/runtime/live.py:137` | `method` | `qts.runtime.live.LiveRuntime.pause` | 未写 docstring；静态推断为所属类上的 `pause` 行为。 | 0 | 1 |
| `backend/src/qts/runtime/live.py:140` | `method` | `qts.runtime.live.LiveRuntime.resume` | 未写 docstring；静态推断为所属类上的 `resume` 行为。 | 0 | 1 |
| `backend/src/qts/runtime/live.py:143` | `method` | `qts.runtime.live.LiveRuntime.degrade` | 未写 docstring；静态推断为所属类上的 `degrade` 行为。 | 0 | 1 |
| `backend/src/qts/runtime/live.py:146` | `method` | `qts.runtime.live.LiveRuntime.recover` | 未写 docstring；静态推断为所属类上的 `recover` 行为。 | 0 | 1 |
| `backend/src/qts/runtime/live.py:149` | `method` | `qts.runtime.live.LiveRuntime.submit_order` | 未写 docstring；静态推断为所属类上的 `submit order` 行为。 | 1 | 4 |
| `backend/src/qts/runtime/mailbox.py:8` | `class` | `qts.runtime.mailbox.Mailbox` | Simple in-memory FIFO mailbox. | 0 | 0 |
| `backend/src/qts/runtime/mailbox.py:11` | `method` | `qts.runtime.mailbox.Mailbox.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 0 | 1 |
| `backend/src/qts/runtime/mailbox.py:15` | `property` | `qts.runtime.mailbox.Mailbox.size` | 未写 docstring；静态推断为所属类上的 `size` 行为。 | 0 | 1 |
| `backend/src/qts/runtime/mailbox.py:18` | `method` | `qts.runtime.mailbox.Mailbox.put` | 未写 docstring；静态推断为所属类上的 `put` 行为。 | 0 | 1 |
| `backend/src/qts/runtime/mailbox.py:21` | `method` | `qts.runtime.mailbox.Mailbox.get` | 未写 docstring；静态推断为读取或返回值（名称：get）。 | 0 | 1 |
| `backend/src/qts/runtime/mailbox.py:24` | `method` | `qts.runtime.mailbox.Mailbox.empty` | 未写 docstring；静态推断为所属类上的 `empty` 行为。 | 0 | 0 |
| `backend/src/qts/runtime/partitioning.py:11` | `class` | `qts.runtime.partitioning.AccountPartitionPolicy` | Partition live state and messages by internal account id. | 0 | 0 |
| `backend/src/qts/runtime/partitioning.py:14` | `method` | `qts.runtime.partitioning.AccountPartitionPolicy.partition_for` | 未写 docstring；静态推断为所属类上的 `partition for` 行为。 | 0 | 0 |
| `backend/src/qts/runtime/partitioning.py:19` | `class` | `qts.runtime.partitioning.AccountBrokerMapping` | Boundary-only broker account mapping. | 0 | 1 |
| `backend/src/qts/runtime/partitioning.py:26` | `method` | `qts.runtime.partitioning.AccountBrokerMapping.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 2 |
| `backend/src/qts/runtime/partitioning.py:30` | `method` | `qts.runtime.partitioning.AccountBrokerMapping.boundary_payload` | 未写 docstring；静态推断为所属类上的 `boundary payload` 行为。 | 0 | 0 |
| `backend/src/qts/runtime/partitioning.py:38` | `class` | `qts.runtime.partitioning.AccountRiskConfig` | Per-account live risk limits. | 0 | 2 |
| `backend/src/qts/runtime/partitioning.py:45` | `method` | `qts.runtime.partitioning.AccountRiskConfig.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 6 |
| `backend/src/qts/runtime/partitioning.py:51` | `method` | `qts.runtime.partitioning.AccountRiskConfig.limit_for` | 未写 docstring；静态推断为所属类上的 `limit for` 行为。 | 0 | 1 |
| `backend/src/qts/runtime/router.py:8` | `class` | `qts.runtime.router.RouteNotFoundError` | Raised when no actor route exists for a partition key. | 0 | 0 |
| `backend/src/qts/runtime/router.py:12` | `class` | `qts.runtime.router.EventRouter` | Route messages to actor refs by a configured message attribute. | 0 | 0 |
| `backend/src/qts/runtime/router.py:15` | `method` | `qts.runtime.router.EventRouter.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 0 | 2 |
| `backend/src/qts/runtime/router.py:21` | `method` | `qts.runtime.router.EventRouter.register` | 未写 docstring；静态推断为所属类上的 `register` 行为。 | 0 | 0 |
| `backend/src/qts/runtime/router.py:24` | `method` | `qts.runtime.router.EventRouter.route` | 未写 docstring；静态推断为所属类上的 `route` 行为。 | 1 | 3 |
| `backend/src/qts/runtime/state_recovery.py:10` | `class` | `qts.runtime.state_recovery.StateSnapshot` | Serialized actor state snapshot envelope. | 0 | 1 |
| `backend/src/qts/runtime/state_recovery.py:17` | `method` | `qts.runtime.state_recovery.StateSnapshot.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 3 |
| `backend/src/qts/runtime/state_recovery.py:24` | `class` | `qts.runtime.state_recovery.InMemorySnapshotStore` | In-memory snapshot store for deterministic tests and local recovery. | 0 | 0 |
| `backend/src/qts/runtime/state_recovery.py:27` | `method` | `qts.runtime.state_recovery.InMemorySnapshotStore.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 0 | 0 |
| `backend/src/qts/runtime/state_recovery.py:30` | `method` | `qts.runtime.state_recovery.InMemorySnapshotStore.save` | 未写 docstring；静态推断为保存数据或状态（名称：save）。 | 0 | 0 |
| `backend/src/qts/runtime/state_recovery.py:33` | `method` | `qts.runtime.state_recovery.InMemorySnapshotStore.load` | 未写 docstring；静态推断为加载数据或配置（名称：load）。 | 0 | 3 |
| `backend/src/qts/strategy_sdk/asset_ref.py:13` | `class` | `qts.strategy_sdk.asset_ref.AssetRef` | Lightweight strategy-facing reference to an internal instrument. | 0 | 2 |
| `backend/src/qts/strategy_sdk/asset_ref.py:20` | `method` | `qts.strategy_sdk.asset_ref.AssetRef.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 5 |
| `backend/src/qts/strategy_sdk/asset_ref.py:25` | `method` | `qts.strategy_sdk.asset_ref.AssetRef.__hash__` | 未写 docstring；实现 Python 协议方法 `__hash__`。 | 0 | 1 |
| `backend/src/qts/strategy_sdk/context.py:21` | `class` | `qts.strategy_sdk.context.SymbolResolver` | Platform-provided symbol resolution boundary. | 0 | 0 |
| `backend/src/qts/strategy_sdk/context.py:24` | `method` | `qts.strategy_sdk.context.SymbolResolver.resolve` | 未写 docstring；静态推断为解析标识、引用或配置到目标对象（名称：resolve）。 | 0 | 0 |
| `backend/src/qts/strategy_sdk/context.py:27` | `class` | `qts.strategy_sdk.context.FutureContractResolver` | Platform-provided future chain resolution boundary. | 0 | 0 |
| `backend/src/qts/strategy_sdk/context.py:30` | `method` | `qts.strategy_sdk.context.FutureContractResolver.resolve_contract` | 未写 docstring；静态推断为解析标识、引用或配置到目标对象（名称：resolve contract）。 | 0 | 0 |
| `backend/src/qts/strategy_sdk/context.py:33` | `class` | `qts.strategy_sdk.context.ContinuousFutureResolver` | Platform-provided rolling future reference boundary. | 0 | 0 |
| `backend/src/qts/strategy_sdk/context.py:36` | `method` | `qts.strategy_sdk.context.ContinuousFutureResolver.continuous_instrument_id` | 未写 docstring；静态推断为所属类上的 `continuous instrument id` 行为。 | 0 | 0 |
| `backend/src/qts/strategy_sdk/context.py:39` | `class` | `qts.strategy_sdk.context.OptionContractRef` | Read-only option contract reference returned by the platform. | 0 | 0 |
| `backend/src/qts/strategy_sdk/context.py:43` | `property` | `qts.strategy_sdk.context.OptionContractRef.instrument_id` | 未写 docstring；静态推断为所属类上的 `instrument id` 行为。 | 0 | 0 |
| `backend/src/qts/strategy_sdk/context.py:46` | `class` | `qts.strategy_sdk.context.OptionContractResolver` | Platform-provided option chain resolution boundary. | 0 | 0 |
| `backend/src/qts/strategy_sdk/context.py:49` | `method` | `qts.strategy_sdk.context.OptionContractResolver.find` | 未写 docstring；静态推断为所属类上的 `find` 行为。 | 0 | 0 |
| `backend/src/qts/strategy_sdk/context.py:60` | `class` | `qts.strategy_sdk.context.DataSubscription` | Strategy-declared market data requirement. | 0 | 1 |
| `backend/src/qts/strategy_sdk/context.py:67` | `method` | `qts.strategy_sdk.context.DataSubscription.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 3 |
| `backend/src/qts/strategy_sdk/context.py:75` | `class` | `qts.strategy_sdk.context.StrategyContext` | User-facing strategy context. | 0 | 5 |
| `backend/src/qts/strategy_sdk/context.py:89` | `property` | `qts.strategy_sdk.context.StrategyContext.intents` | 未写 docstring；静态推断为所属类上的 `intents` 行为。 | 0 | 1 |
| `backend/src/qts/strategy_sdk/context.py:93` | `property` | `qts.strategy_sdk.context.StrategyContext.subscriptions` | 未写 docstring；静态推断为所属类上的 `subscriptions` 行为。 | 0 | 1 |
| `backend/src/qts/strategy_sdk/context.py:96` | `method` | `qts.strategy_sdk.context.StrategyContext.symbol` | 未写 docstring；静态推断为所属类上的 `symbol` 行为。 | 1 | 3 |
| `backend/src/qts/strategy_sdk/context.py:102` | `method` | `qts.strategy_sdk.context.StrategyContext.future` | 未写 docstring；静态推断为所属类上的 `future` 行为。 | 1 | 8 |
| `backend/src/qts/strategy_sdk/context.py:122` | `method` | `qts.strategy_sdk.context.StrategyContext.option` | 未写 docstring；静态推断为所属类上的 `option` 行为。 | 1 | 5 |
| `backend/src/qts/strategy_sdk/context.py:143` | `method` | `qts.strategy_sdk.context.StrategyContext.target_percent` | 未写 docstring；静态推断为所属类上的 `target percent` 行为。 | 2 | 2 |
| `backend/src/qts/strategy_sdk/context.py:148` | `method` | `qts.strategy_sdk.context.StrategyContext.target_quantity` | 未写 docstring；静态推断为所属类上的 `target quantity` 行为。 | 2 | 2 |
| `backend/src/qts/strategy_sdk/context.py:153` | `method` | `qts.strategy_sdk.context.StrategyContext.target_value` | 未写 docstring；静态推断为所属类上的 `target value` 行为。 | 2 | 2 |
| `backend/src/qts/strategy_sdk/context.py:158` | `method` | `qts.strategy_sdk.context.StrategyContext.close` | 未写 docstring；静态推断为关闭资源或头寸（名称：close）。 | 2 | 2 |
| `backend/src/qts/strategy_sdk/context.py:161` | `method` | `qts.strategy_sdk.context.StrategyContext.rebalance` | 未写 docstring；静态推断为所属类上的 `rebalance` 行为。 | 1 | 3 |
| `backend/src/qts/strategy_sdk/context.py:164` | `method` | `qts.strategy_sdk.context.StrategyContext.subscribe` | 未写 docstring；静态推断为所属类上的 `subscribe` 行为。 | 1 | 2 |
| `backend/src/qts/strategy_sdk/context.py:169` | `method` | `qts.strategy_sdk.context.StrategyContext._emit` | 未写 docstring；静态推断为所属类上的 `emit` 行为。 | 0 | 1 |
| `backend/src/qts/strategy_sdk/data_view.py:16` | `class` | `qts.strategy_sdk.data_view.DataView` | Time-sliced market data exposed to strategies. | 0 | 1 |
| `backend/src/qts/strategy_sdk/data_view.py:22` | `method` | `qts.strategy_sdk.data_view.DataView.close` | 未写 docstring；静态推断为关闭资源或头寸（名称：close）。 | 1 | 1 |
| `backend/src/qts/strategy_sdk/data_view.py:25` | `method` | `qts.strategy_sdk.data_view.DataView.bar` | 未写 docstring；静态推断为所属类上的 `bar` 行为。 | 1 | 2 |
| `backend/src/qts/strategy_sdk/data_view.py:31` | `method` | `qts.strategy_sdk.data_view.DataView.history` | 未写 docstring；静态推断为所属类上的 `history` 行为。 | 0 | 3 |
| `backend/src/qts/strategy_sdk/factors.py:11` | `class` | `qts.strategy_sdk.factors.FactorFactory` | Factory for user-created factors. | 0 | 1 |
| `backend/src/qts/strategy_sdk/factors.py:14` | `method` | `qts.strategy_sdk.factors.FactorFactory.momentum` | 未写 docstring；静态推断为所属类上的 `momentum` 行为。 | 1 | 1 |
| `backend/src/qts/strategy_sdk/indicators.py:14` | `class` | `qts.strategy_sdk.indicators.AssetIndicator` | Indicator bound to a strategy asset reference. | 0 | 1 |
| `backend/src/qts/strategy_sdk/indicators.py:21` | `property` | `qts.strategy_sdk.indicators.AssetIndicator.ready` | 未写 docstring；静态推断为读取数据（名称：ready）。 | 0 | 0 |
| `backend/src/qts/strategy_sdk/indicators.py:25` | `property` | `qts.strategy_sdk.indicators.AssetIndicator.value` | 未写 docstring；静态推断为所属类上的 `value` 行为。 | 0 | 0 |
| `backend/src/qts/strategy_sdk/indicators.py:28` | `method` | `qts.strategy_sdk.indicators.AssetIndicator.update` | 未写 docstring；静态推断为所属类上的 `update` 行为。 | 0 | 1 |
| `backend/src/qts/strategy_sdk/indicators.py:33` | `class` | `qts.strategy_sdk.indicators.IndicatorFactory` | Factory for user-created indicators. | 0 | 2 |
| `backend/src/qts/strategy_sdk/indicators.py:38` | `method` | `qts.strategy_sdk.indicators.IndicatorFactory.sma` | 未写 docstring；静态推断为所属类上的 `sma` 行为。 | 2 | 3 |
| `backend/src/qts/strategy_sdk/indicators.py:43` | `method` | `qts.strategy_sdk.indicators.IndicatorFactory.update_from_bar` | 未写 docstring；静态推断为所属类上的 `update from bar` 行为。 | 0 | 1 |
| `backend/src/qts/strategy_sdk/portfolio_view.py:15` | `class` | `qts.strategy_sdk.portfolio_view.PortfolioPosition` | Read-only position snapshot. | 0 | 3 |
| `backend/src/qts/strategy_sdk/portfolio_view.py:23` | `class` | `qts.strategy_sdk.portfolio_view.PortfolioView` | Immutable user-facing portfolio snapshot. | 0 | 2 |
| `backend/src/qts/strategy_sdk/portfolio_view.py:30` | `method` | `qts.strategy_sdk.portfolio_view.PortfolioView.__post_init__` | 未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。 | 0 | 3 |
| `backend/src/qts/strategy_sdk/portfolio_view.py:33` | `method` | `qts.strategy_sdk.portfolio_view.PortfolioView.position` | 未写 docstring；静态推断为所属类上的 `position` 行为。 | 1 | 2 |
| `backend/src/qts/strategy_sdk/portfolio_view.py:36` | `method` | `qts.strategy_sdk.portfolio_view.PortfolioView.exposure` | 未写 docstring；静态推断为所属类上的 `exposure` 行为。 | 1 | 1 |
| `backend/src/qts/strategy_sdk/portfolio_view.py:39` | `method` | `qts.strategy_sdk.portfolio_view.PortfolioView.weight` | 未写 docstring；静态推断为所属类上的 `weight` 行为。 | 1 | 3 |
| `backend/src/qts/strategy_sdk/strategy.py:6` | `class` | `qts.strategy_sdk.strategy.Strategy` | Base class for user strategies. | 0 | 0 |
| `backend/src/qts/strategy_sdk/strategy.py:9` | `method` | `qts.strategy_sdk.strategy.Strategy.initialize` | 未写 docstring；静态推断为所属类上的 `initialize` 行为。 | 0 | 0 |
| `backend/src/qts/strategy_sdk/strategy.py:12` | `method` | `qts.strategy_sdk.strategy.Strategy.on_bar` | 未写 docstring；静态推断为响应事件或回调（名称：on bar）。 | 0 | 0 |
| `backend/src/qts/strategy_sdk/strategy.py:15` | `method` | `qts.strategy_sdk.strategy.Strategy.on_tick` | 未写 docstring；静态推断为响应事件或回调（名称：on tick）。 | 0 | 0 |
| `backend/src/qts/strategy_sdk/strategy.py:18` | `method` | `qts.strategy_sdk.strategy.Strategy.on_timer` | 未写 docstring；静态推断为响应事件或回调（名称：on timer）。 | 0 | 0 |
| `backend/src/qts/strategy_sdk/strategy.py:21` | `method` | `qts.strategy_sdk.strategy.Strategy.on_order_update` | 未写 docstring；静态推断为响应事件或回调（名称：on order update）。 | 0 | 0 |
| `backend/src/qts/strategy_sdk/strategy.py:24` | `method` | `qts.strategy_sdk.strategy.Strategy.on_fill` | 未写 docstring；静态推断为响应事件或回调（名称：on fill）。 | 0 | 0 |
| `backend/src/qts/strategy_sdk/strategy.py:27` | `method` | `qts.strategy_sdk.strategy.Strategy.finalize` | 未写 docstring；静态推断为所属类上的 `finalize` 行为。 | 0 | 0 |
| `backend/src/qts/strategy_sdk/target.py:12` | `class` | `qts.strategy_sdk.target.TargetIntentType` | Supported target intent kinds. | 0 | 0 |
| `backend/src/qts/strategy_sdk/target.py:22` | `class` | `qts.strategy_sdk.target.TargetIntent` | Strategy-emitted intent, later handled by platform risk/order flow. | 0 | 1 |
| `examples/strategies/gc_si_momentum.py:12` | `class` | `examples.strategies.gc_si_momentum.GcSiMomentumStrategy` | Simple moving-average momentum strategy for configured GC/SI symbols. | 0 | 0 |
| `examples/strategies/gc_si_momentum.py:15` | `method` | `examples.strategies.gc_si_momentum.GcSiMomentumStrategy.__init__` | 未写 docstring；初始化所属类实例并保存/校验构造参数。 | 0 | 4 |
| `examples/strategies/gc_si_momentum.py:33` | `method` | `examples.strategies.gc_si_momentum.GcSiMomentumStrategy.initialize` | 未写 docstring；静态推断为所属类上的 `initialize` 行为。 | 1 | 3 |
| `examples/strategies/gc_si_momentum.py:38` | `method` | `examples.strategies.gc_si_momentum.GcSiMomentumStrategy.on_bar` | 未写 docstring；静态推断为响应事件或回调（名称：on bar）。 | 1 | 7 |
| `examples/strategies/gc_si_momentum.py:55` | `module_function` | `examples.strategies.gc_si_momentum._average` | 未写 docstring；静态推断为 `average` 函数，具体语义以实现为准。 | 0 | 5 |
| `examples/strategies/gc_si_momentum.py:60` | `module_function` | `examples.strategies.gc_si_momentum._asset_for_symbol` | 未写 docstring；静态推断为 `asset for symbol` 函数，具体语义以实现为准。 | 0 | 2 |
| `examples/strategies/moving_average_cross.py:8` | `class` | `examples.strategies.moving_average_cross.MovingAverageCross` | 未写 docstring；静态推断为定义 Moving Average Cross 概念，继承/实现 Strategy。 | 0 | 0 |
| `examples/strategies/moving_average_cross.py:9` | `method` | `examples.strategies.moving_average_cross.MovingAverageCross.initialize` | 未写 docstring；静态推断为所属类上的 `initialize` 行为。 | 0 | 3 |
| `examples/strategies/moving_average_cross.py:14` | `method` | `examples.strategies.moving_average_cross.MovingAverageCross.on_bar` | 未写 docstring；静态推断为响应事件或回调（名称：on bar）。 | 0 | 6 |
| `scripts/bootstrap.py:11` | `module_function` | `scripts.bootstrap.main` | 未写 docstring；静态推断为 `main` 函数，具体语义以实现为准。 | 1 | 2 |
| `scripts/ibkr_collect_environment_evidence.py:28` | `module_function` | `scripts.ibkr_collect_environment_evidence.collect_environment_evidence` | Write a JSON evidence file and return its path. | 5 | 11 |
| `scripts/ibkr_collect_environment_evidence.py:81` | `module_function` | `scripts.ibkr_collect_environment_evidence.main` | 未写 docstring；静态推断为 `main` 函数，具体语义以实现为准。 | 1 | 9 |
| `scripts/ibkr_collect_environment_evidence.py:122` | `module_function` | `scripts.ibkr_collect_environment_evidence._read_config` | 未写 docstring；静态推断为 `read config` 函数，具体语义以实现为准。 | 0 | 4 |
| `scripts/ibkr_collect_environment_evidence.py:130` | `module_function` | `scripts.ibkr_collect_environment_evidence._summarize_config` | 未写 docstring；静态推断为 `summarize config` 函数，具体语义以实现为准。 | 2 | 28 |
| `scripts/ibkr_collect_environment_evidence.py:167` | `module_function` | `scripts.ibkr_collect_environment_evidence._validate_ibkr_config` | 未写 docstring；静态推断为 `validate ibkr config` 函数，具体语义以实现为准。 | 2 | 44 |
| `scripts/ibkr_collect_environment_evidence.py:211` | `module_function` | `scripts.ibkr_collect_environment_evidence._validate_connection` | 未写 docstring；静态推断为 `validate connection` 函数，具体语义以实现为准。 | 0 | 10 |
| `scripts/ibkr_collect_environment_evidence.py:224` | `module_function` | `scripts.ibkr_collect_environment_evidence._collect_network_evidence` | 未写 docstring；静态推断为 `collect network evidence` 函数，具体语义以实现为准。 | 2 | 8 |
| `scripts/ibkr_collect_environment_evidence.py:249` | `module_function` | `scripts.ibkr_collect_environment_evidence._tcp_probe` | 未写 docstring；静态推断为 `tcp probe` 函数，具体语义以实现为准。 | 0 | 5 |
| `scripts/ibkr_collect_environment_evidence.py:271` | `module_function` | `scripts.ibkr_collect_environment_evidence._env_ref_status` | 未写 docstring；静态推断为 `env ref status` 函数，具体语义以实现为准。 | 0 | 1 |
| `scripts/ibkr_collect_environment_evidence.py:278` | `module_function` | `scripts.ibkr_collect_environment_evidence._mapping` | 未写 docstring；静态推断为 `mapping` 函数，具体语义以实现为准。 | 0 | 1 |
| `scripts/ibkr_collect_environment_evidence.py:284` | `module_function` | `scripts.ibkr_collect_environment_evidence._evidence_filename` | 未写 docstring；静态推断为 `evidence filename` 函数，具体语义以实现为准。 | 1 | 2 |
| `scripts/ibkr_collect_environment_evidence.py:290` | `module_function` | `scripts.ibkr_collect_environment_evidence._safe_label` | 未写 docstring；静态推断为 `safe label` 函数，具体语义以实现为准。 | 0 | 3 |
| `scripts/ibkr_paper_order_lifecycle_drill.py:35` | `module_function` | `scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill` | Run a paper-only limit-order lifecycle drill and write JSON evidence. | 18 | 41 |
| `scripts/ibkr_paper_order_lifecycle_drill.py:145` | `module_function` | `scripts.ibkr_paper_order_lifecycle_drill.main` | 未写 docstring；静态推断为 `main` 函数，具体语义以实现为准。 | 1 | 14 |
| `scripts/ibkr_paper_order_lifecycle_drill.py:188` | `module_function` | `scripts.ibkr_paper_order_lifecycle_drill._read_config` | 未写 docstring；静态推断为 `read config` 函数，具体语义以实现为准。 | 0 | 4 |
| `scripts/ibkr_paper_order_lifecycle_drill.py:196` | `module_function` | `scripts.ibkr_paper_order_lifecycle_drill._validate_paper_only_ibkr_config` | 未写 docstring；静态推断为 `validate paper only ibkr config` 函数，具体语义以实现为准。 | 2 | 19 |
| `scripts/ibkr_paper_order_lifecycle_drill.py:215` | `module_function` | `scripts.ibkr_paper_order_lifecycle_drill._summarize_config` | 未写 docstring；静态推断为 `summarize config` 函数，具体语义以实现为准。 | 2 | 11 |
| `scripts/ibkr_paper_order_lifecycle_drill.py:231` | `module_function` | `scripts.ibkr_paper_order_lifecycle_drill._execution_report_evidence` | 未写 docstring；静态推断为 `execution report evidence` 函数，具体语义以实现为准。 | 0 | 4 |
| `scripts/ibkr_paper_order_lifecycle_drill.py:246` | `module_function` | `scripts.ibkr_paper_order_lifecycle_drill._account_id` | 未写 docstring；静态推断为 `account id` 函数，具体语义以实现为准。 | 1 | 4 |
| `scripts/ibkr_paper_order_lifecycle_drill.py:250` | `module_function` | `scripts.ibkr_paper_order_lifecycle_drill._mapping` | 未写 docstring；静态推断为 `mapping` 函数，具体语义以实现为准。 | 0 | 1 |
| `scripts/ibkr_paper_order_lifecycle_drill.py:256` | `module_function` | `scripts.ibkr_paper_order_lifecycle_drill._evidence_filename` | 未写 docstring；静态推断为 `evidence filename` 函数，具体语义以实现为准。 | 1 | 2 |
| `scripts/ibkr_paper_order_lifecycle_drill.py:262` | `module_function` | `scripts.ibkr_paper_order_lifecycle_drill._safe_label` | 未写 docstring；静态推断为 `safe label` 函数，具体语义以实现为准。 | 0 | 3 |
| `scripts/run_backtest.py:14` | `module_function` | `scripts.run_backtest.main` | 未写 docstring；静态推断为 `main` 函数，具体语义以实现为准。 | 1 | 23 |
| `scripts/run_load.py:13` | `module_function` | `scripts.run_load.main` | 未写 docstring；静态推断为 `main` 函数，具体语义以实现为准。 | 3 | 8 |
| `scripts/run_paper.py:8` | `module_function` | `scripts.run_paper.main` | 未写 docstring；静态推断为 `main` 函数，具体语义以实现为准。 | 2 | 4 |
| `scripts/validate_historical.py:15` | `module_function` | `scripts.validate_historical.main` | 未写 docstring；静态推断为 `main` 函数，具体语义以实现为准。 | 2 | 25 |
| `scripts/verify_guardrails.py:104` | `class` | `scripts.verify_guardrails.GuardrailViolation` | One architecture or domain-boundary guardrail violation. | 0 | 1 |
| `scripts/verify_guardrails.py:112` | `method` | `scripts.verify_guardrails.GuardrailViolation.format` | 未写 docstring；静态推断为格式化输出表示（名称：format）。 | 0 | 0 |
| `scripts/verify_guardrails.py:116` | `module_function` | `scripts.verify_guardrails.run_guardrails` | Return all guardrail violations under the repository root. | 1 | 6 |
| `scripts/verify_guardrails.py:130` | `module_function` | `scripts.verify_guardrails._check_python_file` | 未写 docstring；静态推断为 `check python file` 函数，具体语义以实现为准。 | 12 | 28 |
| `scripts/verify_guardrails.py:157` | `module_function` | `scripts.verify_guardrails._check_import` | 未写 docstring；静态推断为 `check import` 函数，具体语义以实现为准。 | 3 | 9 |
| `scripts/verify_guardrails.py:192` | `module_function` | `scripts.verify_guardrails._is_forbidden_dependency` | 未写 docstring；静态推断为 `is forbidden dependency` 函数，具体语义以实现为准。 | 0 | 2 |
| `scripts/verify_guardrails.py:220` | `module_function` | `scripts.verify_guardrails._is_forbidden_adapter_dependency` | 未写 docstring；静态推断为 `is forbidden adapter dependency` 函数，具体语义以实现为准。 | 0 | 2 |
| `scripts/verify_guardrails.py:231` | `module_function` | `scripts.verify_guardrails._check_product_specific_code` | 未写 docstring；静态推断为 `check product specific code` 函数，具体语义以实现为准。 | 1 | 1 |
| `scripts/verify_guardrails.py:244` | `module_function` | `scripts.verify_guardrails._check_broker_specific_code` | 未写 docstring；静态推断为 `check broker specific code` 函数，具体语义以实现为准。 | 1 | 1 |
| `scripts/verify_guardrails.py:257` | `module_function` | `scripts.verify_guardrails._check_test_support_code` | 未写 docstring；静态推断为 `check test support code` 函数，具体语义以实现为准。 | 4 | 12 |
| `scripts/verify_guardrails.py:288` | `module_function` | `scripts.verify_guardrails._check_shared_capability_placement` | 未写 docstring；静态推断为 `check shared capability placement` 函数，具体语义以实现为准。 | 3 | 5 |
| `scripts/verify_guardrails.py:310` | `module_function` | `scripts.verify_guardrails._check_oop_public_factory_functions` | 未写 docstring；静态推断为 `check oop public factory functions` 函数，具体语义以实现为准。 | 1 | 7 |
| `scripts/verify_guardrails.py:340` | `module_function` | `scripts.verify_guardrails._check_oop_helper_ownership` | 未写 docstring；静态推断为 `check oop helper ownership` 函数，具体语义以实现为准。 | 2 | 17 |
| `scripts/verify_guardrails.py:406` | `module_function` | `scripts.verify_guardrails._check_backtest_runner_cohesion` | 未写 docstring；静态推断为 `check backtest runner cohesion` 函数，具体语义以实现为准。 | 3 | 14 |
| `scripts/verify_guardrails.py:462` | `module_function` | `scripts.verify_guardrails._check_backtest_input_cohesion` | 未写 docstring；静态推断为 `check backtest input cohesion` 函数，具体语义以实现为准。 | 3 | 13 |
| `scripts/verify_guardrails.py:518` | `module_function` | `scripts.verify_guardrails._check_backtest_engine_cohesion` | 未写 docstring；静态推断为 `check backtest engine cohesion` 函数，具体语义以实现为准。 | 2 | 10 |
| `scripts/verify_guardrails.py:558` | `module_function` | `scripts.verify_guardrails._check_forbidden_tokens` | 未写 docstring；静态推断为 `check forbidden tokens` 函数，具体语义以实现为准。 | 3 | 14 |
| `scripts/verify_guardrails.py:591` | `module_function` | `scripts.verify_guardrails._node_identifier_name` | 未写 docstring；静态推断为 `node identifier name` 函数，具体语义以实现为准。 | 0 | 5 |
| `scripts/verify_guardrails.py:601` | `module_function` | `scripts.verify_guardrails._contains_forbidden_token` | 未写 docstring；静态推断为 `contains forbidden token` 函数，具体语义以实现为准。 | 1 | 2 |
| `scripts/verify_guardrails.py:605` | `module_function` | `scripts.verify_guardrails._node_references_name` | 未写 docstring；静态推断为 `node references name` 函数，具体语义以实现为准。 | 0 | 4 |
| `scripts/verify_guardrails.py:612` | `module_function` | `scripts.verify_guardrails._identifier_tokens` | 未写 docstring；静态推断为 `identifier tokens` 函数，具体语义以实现为准。 | 0 | 7 |
| `scripts/verify_guardrails.py:624` | `module_function` | `scripts.verify_guardrails._iter_imports` | 未写 docstring；静态推断为 `iter imports` 函数，具体语义以实现为准。 | 0 | 5 |
| `scripts/verify_guardrails.py:634` | `module_function` | `scripts.verify_guardrails._iter_imported_names` | 未写 docstring；静态推断为 `iter imported names` 函数，具体语义以实现为准。 | 0 | 3 |
| `scripts/verify_guardrails.py:642` | `module_function` | `scripts.verify_guardrails._has_allowed_prefix` | 未写 docstring；静态推断为 `has allowed prefix` 函数，具体语义以实现为准。 | 0 | 2 |
| `scripts/verify_guardrails.py:646` | `module_function` | `scripts.verify_guardrails.main` | 未写 docstring；静态推断为 `main` 函数，具体语义以实现为准。 | 1 | 6 |

## 详细清单

### `backend/src/qts/__init__.py`

模块：`qts`

无类或函数定义。

### `backend/src/qts/api/__init__.py`

模块：`qts.api`

无类或函数定义。

### `backend/src/qts/api/app.py`

模块：`qts.api.app`

#### `qts.api.app.create_app`

- 位置：`backend/src/qts/api/app.py:18-27`
- 类型：`module_function`
- 签名：`def create_app() -> FastAPI`
- 作用：未写 docstring；静态推断为创建对象或资源（名称：create app）。
- 直接原始调用：`app.include_router` x7, `FastAPI`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/api/routes/__init__.py`

模块：`qts.api.routes`

无类或函数定义。

### `backend/src/qts/api/routes/accounts.py`

模块：`qts.api.routes.accounts`

#### `qts.api.routes.accounts.account_snapshot`

- 位置：`backend/src/qts/api/routes/accounts.py:13-14`
- 类型：`module_function`
- 签名：`def account_snapshot(account_id: str) -> AccountSnapshotSchema`
- 装饰器：`router.get()`
- 作用：未写 docstring；静态推断为 `account snapshot` 函数，具体语义以实现为准。
- 直接原始调用：`AccountSnapshotSchema`
- 已解析到仓库内部的调用：`qts.api.schemas.common.AccountSnapshotSchema`
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/api/routes/backtests.py`

模块：`qts.api.routes.backtests`

#### `qts.api.routes.backtests.submit_backtest`

- 位置：`backend/src/qts/api/routes/backtests.py:15-17`
- 类型：`module_function`
- 签名：`def submit_backtest(request: BacktestRequestSchema) -> BacktestRunSchema`
- 装饰器：`router.post()`
- 作用：未写 docstring；静态推断为 `submit backtest` 函数，具体语义以实现为准。
- 直接原始调用：`BacktestRequestDTO`, `BacktestRunSchema.model_validate`, `BacktestService`, `BacktestService().submit`
- 已解析到仓库内部的调用：`qts.application.dto.backtest.BacktestRequestDTO`, `qts.application.services.backtest.BacktestService`
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/api/routes/health.py`

模块：`qts.api.routes.health`

#### `qts.api.routes.health.health`

- 位置：`backend/src/qts/api/routes/health.py:13-15`
- 类型：`module_function`
- 签名：`def health() -> dict`
- 装饰器：`router.get()`
- 作用：未写 docstring；静态推断为 `health` 函数，具体语义以实现为准。
- 直接原始调用：`HealthService`, `HealthService().status`
- 已解析到仓库内部的调用：`qts.application.services.health.HealthService`
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/api/routes/operations.py`

模块：`qts.api.routes.operations`

#### `qts.api.routes.operations.RuntimeCommandResponse`

- 位置：`backend/src/qts/api/routes/operations.py:20-21`
- 类型：`class`
- 签名：`class RuntimeCommandResponse(BaseModel)`
- 继承/基类：`BaseModel`
- 作用：未写 docstring；静态推断为定义 Runtime Command Response 概念，继承/实现 BaseModel。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.api.routes.operations.pause_runtime.<locals>.command`, `qts.api.routes.operations.resume_runtime.<locals>.command`

#### `qts.api.routes.operations.KillSwitchScopeSchema`

- 位置：`backend/src/qts/api/routes/operations.py:24-28`
- 类型：`class`
- 签名：`class KillSwitchScopeSchema(StrEnum)`
- 继承/基类：`StrEnum`
- 作用：未写 docstring；静态推断为定义 Kill Switch Scope Schema 概念，继承/实现 StrEnum。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.api.routes.operations.KillSwitchCommand`

- 位置：`backend/src/qts/api/routes/operations.py:31-44`
- 类型：`class`
- 签名：`class KillSwitchCommand(BaseModel)`
- 继承/基类：`BaseModel`
- 作用：未写 docstring；静态推断为定义 Kill Switch Command 概念，继承/实现 BaseModel。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.api.routes.operations.KillSwitchCommand.validate_scope`

- 位置：`backend/src/qts/api/routes/operations.py:37-44`
- 类型：`method`
- 签名：`def validate_scope(self) -> KillSwitchCommand`
- 所属：`qts.api.routes.operations.KillSwitchCommand`
- 装饰器：`model_validator()`
- 作用：未写 docstring；静态推断为校验输入、状态或领域约束（名称：validate scope）。
- 直接原始调用：`ValueError` x2, `self.reason.strip`, `self.scope_id.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.api.routes.operations.KillSwitchResponse`

- 位置：`backend/src/qts/api/routes/operations.py:47-51`
- 类型：`class`
- 签名：`class KillSwitchResponse(BaseModel)`
- 继承/基类：`BaseModel`
- 作用：未写 docstring；静态推断为定义 Kill Switch Response 概念，继承/实现 BaseModel。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.api.routes.operations.activate_kill_switch`

#### `qts.api.routes.operations._require_operator`

- 位置：`backend/src/qts/api/routes/operations.py:54-56`
- 类型：`module_function`
- 签名：`def _require_operator(operator: str | None) -> None`
- 作用：未写 docstring；静态推断为 `require operator` 函数，具体语义以实现为准。
- 直接原始调用：`HTTPException`, `operator.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.api.routes.operations.activate_kill_switch`, `qts.api.routes.operations.pause_runtime`, `qts.api.routes.operations.resume_runtime`

#### `qts.api.routes.operations.pause_runtime`

- 位置：`backend/src/qts/api/routes/operations.py:60-72`
- 类型：`module_function`
- 签名：`def pause_runtime(idempotency_key: Annotated = None, operator: Annotated = None) -> RuntimeCommandResponse`
- 装饰器：`router.post()`
- 作用：未写 docstring；静态推断为 `pause runtime` 函数，具体语义以实现为准。
- 直接原始调用：`_idempotency.run`, `_require_operator`, `command`
- 已解析到仓库内部的调用：`qts.api.routes.operations._require_operator`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.api.routes.operations.pause_runtime.<locals>.command`

- 位置：`backend/src/qts/api/routes/operations.py:66-68`
- 类型：`nested_function`
- 签名：`def command() -> RuntimeCommandResponse`
- 所属：`qts.api.routes.operations.pause_runtime`
- 作用：未写 docstring；静态推断为 `command` 函数，具体语义以实现为准。
- 直接原始调用：`RuntimeCommandResponse`, `_operations.pause_runtime`
- 已解析到仓库内部的调用：`qts.api.routes.operations.RuntimeCommandResponse`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.api.routes.operations.resume_runtime`

- 位置：`backend/src/qts/api/routes/operations.py:76-88`
- 类型：`module_function`
- 签名：`def resume_runtime(idempotency_key: Annotated = None, operator: Annotated = None) -> RuntimeCommandResponse`
- 装饰器：`router.post()`
- 作用：未写 docstring；静态推断为 `resume runtime` 函数，具体语义以实现为准。
- 直接原始调用：`_idempotency.run`, `_require_operator`, `command`
- 已解析到仓库内部的调用：`qts.api.routes.operations._require_operator`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.api.routes.operations.resume_runtime.<locals>.command`

- 位置：`backend/src/qts/api/routes/operations.py:82-84`
- 类型：`nested_function`
- 签名：`def command() -> RuntimeCommandResponse`
- 所属：`qts.api.routes.operations.resume_runtime`
- 作用：未写 docstring；静态推断为 `command` 函数，具体语义以实现为准。
- 直接原始调用：`RuntimeCommandResponse`, `_operations.resume_runtime`
- 已解析到仓库内部的调用：`qts.api.routes.operations.RuntimeCommandResponse`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.api.routes.operations.activate_kill_switch`

- 位置：`backend/src/qts/api/routes/operations.py:92-109`
- 类型：`module_function`
- 签名：`def activate_kill_switch(command: KillSwitchCommand, operator: Annotated = None) -> KillSwitchResponse`
- 装饰器：`router.post()`
- 作用：未写 docstring；静态推断为 `activate kill switch` 函数，具体语义以实现为准。
- 直接原始调用：`KillSwitchCommandDTO`, `KillSwitchResponse`, `_operations.activate_kill_switch`, `_require_operator`
- 已解析到仓库内部的调用：`qts.api.routes.operations.KillSwitchResponse`, `qts.api.routes.operations._require_operator`, `qts.application.dto.operations.KillSwitchCommandDTO`
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/api/routes/orders.py`

模块：`qts.api.routes.orders`

#### `qts.api.routes.orders.order_status`

- 位置：`backend/src/qts/api/routes/orders.py:13-14`
- 类型：`module_function`
- 签名：`def order_status(order_id: str) -> OrderStatusSchema`
- 装饰器：`router.get()`
- 作用：未写 docstring；静态推断为 `order status` 函数，具体语义以实现为准。
- 直接原始调用：`OrderStatusSchema`
- 已解析到仓库内部的调用：`qts.api.schemas.common.OrderStatusSchema`
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/api/routes/strategies.py`

模块：`qts.api.routes.strategies`

#### `qts.api.routes.strategies.list_strategies`

- 位置：`backend/src/qts/api/routes/strategies.py:13-14`
- 类型：`module_function`
- 签名：`def list_strategies() -> list`
- 装饰器：`router.get()`
- 作用：未写 docstring；静态推断为 `list strategies` 函数，具体语义以实现为准。
- 直接原始调用：`StrategyStatusSchema`
- 已解析到仓库内部的调用：`qts.api.schemas.common.StrategyStatusSchema`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.api.routes.strategies.start_strategy`

- 位置：`backend/src/qts/api/routes/strategies.py:18-19`
- 类型：`module_function`
- 签名：`def start_strategy(strategy_id: str) -> StrategyStatusSchema`
- 装饰器：`router.post()`
- 作用：未写 docstring；静态推断为启动流程或服务（名称：start strategy）。
- 直接原始调用：`StrategyStatusSchema`
- 已解析到仓库内部的调用：`qts.api.schemas.common.StrategyStatusSchema`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.api.routes.strategies.stop_strategy`

- 位置：`backend/src/qts/api/routes/strategies.py:23-24`
- 类型：`module_function`
- 签名：`def stop_strategy(strategy_id: str) -> StrategyStatusSchema`
- 装饰器：`router.post()`
- 作用：未写 docstring；静态推断为停止流程或服务（名称：stop strategy）。
- 直接原始调用：`StrategyStatusSchema`
- 已解析到仓库内部的调用：`qts.api.schemas.common.StrategyStatusSchema`
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/api/schemas/__init__.py`

模块：`qts.api.schemas`

无类或函数定义。

### `backend/src/qts/api/schemas/backtest_schema.py`

模块：`qts.api.schemas.backtest_schema`

#### `qts.api.schemas.backtest_schema.BacktestRequestSchema`

- 位置：`backend/src/qts/api/schemas/backtest_schema.py:8-11`
- 类型：`class`
- 签名：`class BacktestRequestSchema(BaseModel)`
- 继承/基类：`BaseModel`
- 作用：HTTP request for submitting a backtest.
- 直接原始调用：`Field`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.api.schemas.backtest_schema.BacktestRunSchema`

- 位置：`backend/src/qts/api/schemas/backtest_schema.py:14-21`
- 类型：`class`
- 签名：`class BacktestRunSchema(BaseModel)`
- 继承/基类：`BaseModel`
- 作用：HTTP response for a submitted backtest.
- 直接原始调用：`ConfigDict`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/api/schemas/common.py`

模块：`qts.api.schemas.common`

#### `qts.api.schemas.common.StrategyStatusSchema`

- 位置：`backend/src/qts/api/schemas/common.py:8-10`
- 类型：`class`
- 签名：`class StrategyStatusSchema(BaseModel)`
- 继承/基类：`BaseModel`
- 作用：未写 docstring；静态推断为定义 Strategy Status Schema 概念，继承/实现 BaseModel。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.api.routes.strategies.list_strategies`, `qts.api.routes.strategies.start_strategy`, `qts.api.routes.strategies.stop_strategy`

#### `qts.api.schemas.common.AccountSnapshotSchema`

- 位置：`backend/src/qts/api/schemas/common.py:13-15`
- 类型：`class`
- 签名：`class AccountSnapshotSchema(BaseModel)`
- 继承/基类：`BaseModel`
- 作用：未写 docstring；静态推断为定义 Account Snapshot Schema 概念，继承/实现 BaseModel。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.api.routes.accounts.account_snapshot`

#### `qts.api.schemas.common.OrderStatusSchema`

- 位置：`backend/src/qts/api/schemas/common.py:18-20`
- 类型：`class`
- 签名：`class OrderStatusSchema(BaseModel)`
- 继承/基类：`BaseModel`
- 作用：未写 docstring；静态推断为定义 Order Status Schema 概念，继承/实现 BaseModel。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.api.routes.orders.order_status`

#### `qts.api.schemas.common.RiskRuleSchema`

- 位置：`backend/src/qts/api/schemas/common.py:23-25`
- 类型：`class`
- 签名：`class RiskRuleSchema(BaseModel)`
- 继承/基类：`BaseModel`
- 作用：未写 docstring；静态推断为定义 Risk Rule Schema 概念，继承/实现 BaseModel。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.api.schemas.common.OperationalErrorSchema`

- 位置：`backend/src/qts/api/schemas/common.py:28-42`
- 类型：`class`
- 签名：`class OperationalErrorSchema(BaseModel)`
- 继承/基类：`BaseModel`
- 作用：未写 docstring；静态推断为定义 Operational Error Schema 概念，继承/实现 BaseModel。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.api.schemas.common.OperationalErrorSchema.from_exception`

- 位置：`backend/src/qts/api/schemas/common.py:34-42`
- 类型：`classmethod`
- 签名：`def from_exception(cls, *, code: str, message: str, exc: Exception) -> OperationalErrorSchema`
- 所属：`qts.api.schemas.common.OperationalErrorSchema`
- 装饰器：`classmethod`
- 作用：未写 docstring；静态推断为从指定来源构造或转换对象（名称：from exception）。
- 直接原始调用：`cls`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/api/services/__init__.py`

模块：`qts.api.services`

无类或函数定义。

### `backend/src/qts/api/services/command_idempotency.py`

模块：`qts.api.services.command_idempotency`

#### `qts.api.services.command_idempotency.CommandIdempotencyStore`

- 位置：`backend/src/qts/api/services/command_idempotency.py:11-24`
- 类型：`class`
- 签名：`class CommandIdempotencyStore`
- 作用：Remember the first result for each command idempotency key.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.api.services.command_idempotency.CommandIdempotencyStore.__init__`

- 位置：`backend/src/qts/api/services/command_idempotency.py:14-15`
- 类型：`method`
- 签名：`def __init__(self) -> None`
- 所属：`qts.api.services.command_idempotency.CommandIdempotencyStore`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.api.services.command_idempotency.CommandIdempotencyStore.run`

- 位置：`backend/src/qts/api/services/command_idempotency.py:17-24`
- 类型：`method`
- 签名：`def run(self, key: str, command: Callable) -> T`
- 所属：`qts.api.services.command_idempotency.CommandIdempotencyStore`
- 作用：未写 docstring；静态推断为运行流程或命令（名称：run）。
- 直接原始调用：`ValueError`, `command`, `key.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/api/websocket/__init__.py`

模块：`qts.api.websocket`

无类或函数定义。

### `backend/src/qts/api/websocket/dtos.py`

模块：`qts.api.websocket.dtos`

#### `qts.api.websocket.dtos.StreamEventDTO`

- 位置：`backend/src/qts/api/websocket/dtos.py:10-18`
- 类型：`class`
- 签名：`class StreamEventDTO`
- 装饰器：`dataclass()`
- 作用：未写 docstring；静态推断为定义 Stream Event D T O 概念或数据结构。
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.api.websocket.fill_adapter.order_fill_to_stream_dto`

#### `qts.api.websocket.dtos.StreamEventDTO.__post_init__`

- 位置：`backend/src/qts/api/websocket/dtos.py:16-18`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.api.websocket.dtos.StreamEventDTO`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError`, `self.event_type.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/api/websocket/events.py`

模块：`qts.api.websocket.events`

#### `qts.api.websocket.events.event_stream`

- 位置：`backend/src/qts/api/websocket/events.py:11-19`
- 类型：`async_module_function`
- 签名：`async def event_stream(websocket: WebSocket) -> None`
- 装饰器：`router.websocket()`
- 作用：未写 docstring；静态推断为 `event stream` 函数，具体语义以实现为准。
- 直接原始调用：`websocket.accept`, `websocket.close`, `websocket.send_json`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/api/websocket/fill_adapter.py`

模块：`qts.api.websocket.fill_adapter`

#### `qts.api.websocket.fill_adapter.order_fill_to_stream_dto`

- 位置：`backend/src/qts/api/websocket/fill_adapter.py:11-29`
- 类型：`module_function`
- 签名：`def order_fill_to_stream_dto(fill: OrderFillDTO, *, correlation_id: str | None = None) -> StreamEventDTO`
- 作用：Convert an OrderManager-validated fill into a public stream event DTO.
- 直接原始调用：`str` x2, `StreamEventDTO`, `datetime.now`
- 已解析到仓库内部的调用：`qts.api.websocket.dtos.StreamEventDTO`
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/api/websocket/manager.py`

模块：`qts.api.websocket.manager`

#### `qts.api.websocket.manager.JsonWebSocket`

- 位置：`backend/src/qts/api/websocket/manager.py:8-11`
- 类型：`class`
- 签名：`class JsonWebSocket(Protocol)`
- 继承/基类：`Protocol`
- 作用：未写 docstring；静态推断为定义 Json Web Socket 概念，继承/实现 Protocol。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.api.websocket.manager.JsonWebSocket.accept`

- 位置：`backend/src/qts/api/websocket/manager.py:9-9`
- 类型：`async_method`
- 签名：`async def accept(self) -> None`
- 所属：`qts.api.websocket.manager.JsonWebSocket`
- 作用：未写 docstring；静态推断为所属类上的 `accept` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.api.websocket.manager.JsonWebSocket.send_json`

- 位置：`backend/src/qts/api/websocket/manager.py:11-11`
- 类型：`async_method`
- 签名：`async def send_json(self, data: object) -> None`
- 所属：`qts.api.websocket.manager.JsonWebSocket`
- 作用：未写 docstring；静态推断为所属类上的 `send json` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.api.websocket.manager.WebSocketConnectionManager`

- 位置：`backend/src/qts/api/websocket/manager.py:14-40`
- 类型：`class`
- 签名：`class WebSocketConnectionManager`
- 作用：Track WebSocket clients and broadcast JSON payloads.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.api.websocket.manager.WebSocketConnectionManager.__init__`

- 位置：`backend/src/qts/api/websocket/manager.py:17-18`
- 类型：`method`
- 签名：`def __init__(self) -> None`
- 所属：`qts.api.websocket.manager.WebSocketConnectionManager`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.api.websocket.manager.WebSocketConnectionManager.count`

- 位置：`backend/src/qts/api/websocket/manager.py:21-22`
- 类型：`property`
- 签名：`def count(self) -> int`
- 所属：`qts.api.websocket.manager.WebSocketConnectionManager`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为所属类上的 `count` 行为。
- 直接原始调用：`len`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.application.services.backtest.BacktestService.__init__`

#### `qts.api.websocket.manager.WebSocketConnectionManager.connect`

- 位置：`backend/src/qts/api/websocket/manager.py:24-26`
- 类型：`async_method`
- 签名：`async def connect(self, websocket: JsonWebSocket) -> None`
- 所属：`qts.api.websocket.manager.WebSocketConnectionManager`
- 作用：未写 docstring；静态推断为所属类上的 `connect` 行为。
- 直接原始调用：`self._connections.append`, `websocket.accept`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.api.websocket.manager.WebSocketConnectionManager.disconnect`

- 位置：`backend/src/qts/api/websocket/manager.py:28-30`
- 类型：`method`
- 签名：`def disconnect(self, websocket: JsonWebSocket) -> None`
- 所属：`qts.api.websocket.manager.WebSocketConnectionManager`
- 作用：未写 docstring；静态推断为所属类上的 `disconnect` 行为。
- 直接原始调用：`self._connections.remove`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.api.websocket.manager.WebSocketConnectionManager.broadcast`

#### `qts.api.websocket.manager.WebSocketConnectionManager.broadcast`

- 位置：`backend/src/qts/api/websocket/manager.py:32-40`
- 类型：`async_method`
- 签名：`async def broadcast(self, payload: object) -> None`
- 所属：`qts.api.websocket.manager.WebSocketConnectionManager`
- 作用：未写 docstring；静态推断为所属类上的 `broadcast` 行为。
- 直接原始调用：`self.disconnect`, `stale.append`, `tuple`, `websocket.send_json`
- 已解析到仓库内部的调用：`qts.api.websocket.manager.WebSocketConnectionManager.disconnect`
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/application/__init__.py`

模块：`qts.application`

无类或函数定义。

### `backend/src/qts/application/commands/__init__.py`

模块：`qts.application.commands`

无类或函数定义。

### `backend/src/qts/application/commands/start_paper.py`

模块：`qts.application.commands.start_paper`

#### `qts.application.commands.start_paper.PaperRuntimeConfig`

- 位置：`backend/src/qts/application/commands/start_paper.py:10-24`
- 类型：`class`
- 签名：`class PaperRuntimeConfig`
- 装饰器：`dataclass()`
- 作用：Paper runtime configuration without real broker credentials.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`scripts.run_paper.main`

#### `qts.application.commands.start_paper.PaperRuntimeConfig.__post_init__`

- 位置：`backend/src/qts/application/commands/start_paper.py:18-24`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.application.commands.start_paper.PaperRuntimeConfig`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x3, `Decimal`, `self.account_id.strip`, `self.data_source.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.application.commands.start_paper.PaperRuntime`

- 位置：`backend/src/qts/application/commands/start_paper.py:28-32`
- 类型：`class`
- 签名：`class PaperRuntime`
- 装饰器：`dataclass()`
- 作用：Constructed paper runtime descriptor.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.application.commands.start_paper.start_paper`

#### `qts.application.commands.start_paper.start_paper`

- 位置：`backend/src/qts/application/commands/start_paper.py:35-38`
- 类型：`module_function`
- 签名：`def start_paper(config: PaperRuntimeConfig) -> PaperRuntime`
- 作用：Construct the paper runtime boundary without connecting to a real broker.
- 直接原始调用：`PaperRuntime`
- 已解析到仓库内部的调用：`qts.application.commands.start_paper.PaperRuntime`
- 被以下仓库内部符号调用：`scripts.run_paper.main`

### `backend/src/qts/application/dto/__init__.py`

模块：`qts.application.dto`

无类或函数定义。

### `backend/src/qts/application/dto/backtest.py`

模块：`qts.application.dto.backtest`

#### `qts.application.dto.backtest.BacktestRequestDTO`

- 位置：`backend/src/qts/application/dto/backtest.py:9-16`
- 类型：`class`
- 签名：`class BacktestRequestDTO`
- 装饰器：`dataclass()`
- 作用：Stable application request for starting a backtest.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.api.routes.backtests.submit_backtest`

#### `qts.application.dto.backtest.BacktestRequestDTO.__post_init__`

- 位置：`backend/src/qts/application/dto/backtest.py:14-16`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.application.dto.backtest.BacktestRequestDTO`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError`, `self.strategy_name.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.application.dto.backtest.BacktestRunDTO`

- 位置：`backend/src/qts/application/dto/backtest.py:20-25`
- 类型：`class`
- 签名：`class BacktestRunDTO`
- 装饰器：`dataclass()`
- 作用：Stable application response for a submitted backtest.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.application.services.backtest.BacktestService.submit`

### `backend/src/qts/application/dto/health.py`

模块：`qts.application.dto.health`

#### `qts.application.dto.health.HealthStatusDTO`

- 位置：`backend/src/qts/application/dto/health.py:9-12`
- 类型：`class`
- 签名：`class HealthStatusDTO`
- 装饰器：`dataclass()`
- 作用：Stable health status response.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.application.services.health.HealthService.status`

### `backend/src/qts/application/dto/operations.py`

模块：`qts.application.dto.operations`

#### `qts.application.dto.operations.RuntimeStateDTO`

- 位置：`backend/src/qts/application/dto/operations.py:9-12`
- 类型：`class`
- 签名：`class RuntimeStateDTO`
- 装饰器：`dataclass()`
- 作用：Stable runtime state response.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.application.services.operations.OperationsService.pause_runtime`, `qts.application.services.operations.OperationsService.resume_runtime`

#### `qts.application.dto.operations.KillSwitchCommandDTO`

- 位置：`backend/src/qts/application/dto/operations.py:16-29`
- 类型：`class`
- 签名：`class KillSwitchCommandDTO`
- 装饰器：`dataclass()`
- 作用：Stable kill-switch activation request.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.api.routes.operations.activate_kill_switch`

#### `qts.application.dto.operations.KillSwitchCommandDTO.__post_init__`

- 位置：`backend/src/qts/application/dto/operations.py:23-29`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.application.dto.operations.KillSwitchCommandDTO`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x3, `self.reason.strip`, `self.scope.strip`, `self.scope_id.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.application.dto.operations.KillSwitchStateDTO`

- 位置：`backend/src/qts/application/dto/operations.py:33-39`
- 类型：`class`
- 签名：`class KillSwitchStateDTO`
- 装饰器：`dataclass()`
- 作用：Stable kill-switch state response.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.application.services.operations.OperationsService.activate_kill_switch`

### `backend/src/qts/application/dto/order_events.py`

模块：`qts.application.dto.order_events`

#### `qts.application.dto.order_events.OrderFillDTO`

- 位置：`backend/src/qts/application/dto/order_events.py:10-28`
- 类型：`class`
- 签名：`class OrderFillDTO`
- 装饰器：`dataclass()`
- 作用：Stable fill event shape for public streams.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.application.dto.order_events.OrderFillDTO.__post_init__`

- 位置：`backend/src/qts/application/dto/order_events.py:20-28`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.application.dto.order_events.OrderFillDTO`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x4, `self.fill_id.strip`, `self.instrument_id.strip`, `self.order_id.strip`, `self.side.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/application/services/__init__.py`

模块：`qts.application.services`

无类或函数定义。

### `backend/src/qts/application/services/backtest.py`

模块：`qts.application.services.backtest`

#### `qts.application.services.backtest.BacktestService`

- 位置：`backend/src/qts/application/services/backtest.py:10-21`
- 类型：`class`
- 签名：`class BacktestService`
- 作用：Application boundary for backtest use cases.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.api.routes.backtests.submit_backtest`

#### `qts.application.services.backtest.BacktestService.__init__`

- 位置：`backend/src/qts/application/services/backtest.py:13-14`
- 类型：`method`
- 签名：`def __init__(self) -> None`
- 所属：`qts.application.services.backtest.BacktestService`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：`count`
- 已解析到仓库内部的调用：`qts.api.websocket.manager.WebSocketConnectionManager.count`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.application.services.backtest.BacktestService.submit`

- 位置：`backend/src/qts/application/services/backtest.py:16-21`
- 类型：`method`
- 签名：`def submit(self, request: BacktestRequestDTO) -> BacktestRunDTO`
- 所属：`qts.application.services.backtest.BacktestService`
- 作用：未写 docstring；静态推断为所属类上的 `submit` 行为。
- 直接原始调用：`BacktestRunDTO`, `next`
- 已解析到仓库内部的调用：`qts.application.dto.backtest.BacktestRunDTO`
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/application/services/health.py`

模块：`qts.application.services.health`

#### `qts.application.services.health.HealthService`

- 位置：`backend/src/qts/application/services/health.py:8-12`
- 类型：`class`
- 签名：`class HealthService`
- 作用：Returns platform health without exposing internals.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.api.routes.health.health`

#### `qts.application.services.health.HealthService.status`

- 位置：`backend/src/qts/application/services/health.py:11-12`
- 类型：`method`
- 签名：`def status(self) -> HealthStatusDTO`
- 所属：`qts.application.services.health.HealthService`
- 作用：未写 docstring；静态推断为所属类上的 `status` 行为。
- 直接原始调用：`HealthStatusDTO`
- 已解析到仓库内部的调用：`qts.application.dto.health.HealthStatusDTO`
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/application/services/interfaces.py`

模块：`qts.application.services.interfaces`

#### `qts.application.services.interfaces.AccountService`

- 位置：`backend/src/qts/application/services/interfaces.py:8-9`
- 类型：`class`
- 签名：`class AccountService(Protocol)`
- 继承/基类：`Protocol`
- 作用：未写 docstring；静态推断为定义 Account Service 概念，继承/实现 Protocol。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.application.services.interfaces.AccountService.snapshot`

- 位置：`backend/src/qts/application/services/interfaces.py:9-9`
- 类型：`method`
- 签名：`def snapshot(self, account_id: str) -> object`
- 所属：`qts.application.services.interfaces.AccountService`
- 作用：未写 docstring；静态推断为所属类上的 `snapshot` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.application.services.interfaces.OrderService`

- 位置：`backend/src/qts/application/services/interfaces.py:12-13`
- 类型：`class`
- 签名：`class OrderService(Protocol)`
- 继承/基类：`Protocol`
- 作用：未写 docstring；静态推断为定义 Order Service 概念，继承/实现 Protocol。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.application.services.interfaces.OrderService.status`

- 位置：`backend/src/qts/application/services/interfaces.py:13-13`
- 类型：`method`
- 签名：`def status(self, order_id: str) -> object`
- 所属：`qts.application.services.interfaces.OrderService`
- 作用：未写 docstring；静态推断为所属类上的 `status` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.application.services.interfaces.RiskService`

- 位置：`backend/src/qts/application/services/interfaces.py:16-17`
- 类型：`class`
- 签名：`class RiskService(Protocol)`
- 继承/基类：`Protocol`
- 作用：未写 docstring；静态推断为定义 Risk Service 概念，继承/实现 Protocol。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.application.services.interfaces.RiskService.rules`

- 位置：`backend/src/qts/application/services/interfaces.py:17-17`
- 类型：`method`
- 签名：`def rules(self, account_id: str) -> object`
- 所属：`qts.application.services.interfaces.RiskService`
- 作用：未写 docstring；静态推断为所属类上的 `rules` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/application/services/operations.py`

模块：`qts.application.services.operations`

#### `qts.application.services.operations.OperationsService`

- 位置：`backend/src/qts/application/services/operations.py:9-39`
- 类型：`class`
- 签名：`class OperationsService`
- 作用：Owns operational state without leaking runtime internals into API routes.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.application.services.operations.OperationsService.__init__`

- 位置：`backend/src/qts/application/services/operations.py:12-14`
- 类型：`method`
- 签名：`def __init__(self, *, kill_switches: KillSwitchRegistry | None = None) -> None`
- 所属：`qts.application.services.operations.OperationsService`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：`KillSwitchRegistry`
- 已解析到仓库内部的调用：`qts.risk.kill_switch.KillSwitchRegistry`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.application.services.operations.OperationsService.pause_runtime`

- 位置：`backend/src/qts/application/services/operations.py:16-18`
- 类型：`method`
- 签名：`def pause_runtime(self) -> RuntimeStateDTO`
- 所属：`qts.application.services.operations.OperationsService`
- 作用：未写 docstring；静态推断为所属类上的 `pause runtime` 行为。
- 直接原始调用：`RuntimeStateDTO`
- 已解析到仓库内部的调用：`qts.application.dto.operations.RuntimeStateDTO`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.application.services.operations.OperationsService.resume_runtime`

- 位置：`backend/src/qts/application/services/operations.py:20-22`
- 类型：`method`
- 签名：`def resume_runtime(self) -> RuntimeStateDTO`
- 所属：`qts.application.services.operations.OperationsService`
- 作用：未写 docstring；静态推断为所属类上的 `resume runtime` 行为。
- 直接原始调用：`RuntimeStateDTO`
- 已解析到仓库内部的调用：`qts.application.dto.operations.RuntimeStateDTO`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.application.services.operations.OperationsService.activate_kill_switch`

- 位置：`backend/src/qts/application/services/operations.py:24-32`
- 类型：`method`
- 签名：`def activate_kill_switch(self, command: KillSwitchCommandDTO) -> KillSwitchStateDTO`
- 所属：`qts.application.services.operations.OperationsService`
- 作用：未写 docstring；静态推断为所属类上的 `activate kill switch` 行为。
- 直接原始调用：`KillSwitchStateDTO`, `self._kill_switches.activate`, `self._scope_from_command`
- 已解析到仓库内部的调用：`qts.application.dto.operations.KillSwitchStateDTO`, `qts.application.services.operations.OperationsService._scope_from_command`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.application.services.operations.OperationsService._scope_from_command`

- 位置：`backend/src/qts/application/services/operations.py:35-39`
- 类型：`staticmethod`
- 签名：`def _scope_from_command(command: KillSwitchCommandDTO) -> KillSwitchScope`
- 所属：`qts.application.services.operations.OperationsService`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `scope from command` 行为。
- 直接原始调用：`KillSwitchScope`, `KillSwitchScope.global_scope`, `KillSwitchScopeType`
- 已解析到仓库内部的调用：`qts.risk.kill_switch.KillSwitchScope`, `qts.risk.kill_switch.KillSwitchScope.global_scope`, `qts.risk.kill_switch.KillSwitchScopeType`
- 被以下仓库内部符号调用：`qts.application.services.operations.OperationsService.activate_kill_switch`

### `backend/src/qts/application/services/strategy_service.py`

模块：`qts.application.services.strategy_service`

#### `qts.application.services.strategy_service.StrategyLifecycleService`

- 位置：`backend/src/qts/application/services/strategy_service.py:9-47`
- 类型：`class`
- 签名：`class StrategyLifecycleService`
- 作用：Start, stop, and inspect configured strategy instances.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.application.services.strategy_service.StrategyLifecycleService.__init__`

- 位置：`backend/src/qts/application/services/strategy_service.py:12-18`
- 类型：`method`
- 签名：`def __init__(self, instances: tuple = ()) -> None`
- 所属：`qts.application.services.strategy_service.StrategyLifecycleService`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.application.services.strategy_service.StrategyLifecycleService.add`

- 位置：`backend/src/qts/application/services/strategy_service.py:20-25`
- 类型：`method`
- 签名：`def add(self, instance: StrategyInstance) -> None`
- 所属：`qts.application.services.strategy_service.StrategyLifecycleService`
- 作用：未写 docstring；静态推断为所属类上的 `add` 行为。
- 直接原始调用：`ValueError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.application.services.strategy_service.StrategyLifecycleService.start`

- 位置：`backend/src/qts/application/services/strategy_service.py:27-30`
- 类型：`method`
- 签名：`def start(self, strategy_id: StrategyId) -> StrategyStatus`
- 所属：`qts.application.services.strategy_service.StrategyLifecycleService`
- 作用：未写 docstring；静态推断为启动流程或服务（名称：start）。
- 直接原始调用：`self._require_enabled`
- 已解析到仓库内部的调用：`qts.application.services.strategy_service.StrategyLifecycleService._require_enabled`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.application.services.strategy_service.StrategyLifecycleService.stop`

- 位置：`backend/src/qts/application/services/strategy_service.py:32-35`
- 类型：`method`
- 签名：`def stop(self, strategy_id: StrategyId) -> StrategyStatus`
- 所属：`qts.application.services.strategy_service.StrategyLifecycleService`
- 作用：未写 docstring；静态推断为停止流程或服务（名称：stop）。
- 直接原始调用：`self._require_enabled`
- 已解析到仓库内部的调用：`qts.application.services.strategy_service.StrategyLifecycleService._require_enabled`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.application.services.strategy_service.StrategyLifecycleService.status`

- 位置：`backend/src/qts/application/services/strategy_service.py:37-39`
- 类型：`method`
- 签名：`def status(self, strategy_id: StrategyId) -> StrategyStatus`
- 所属：`qts.application.services.strategy_service.StrategyLifecycleService`
- 作用：未写 docstring；静态推断为所属类上的 `status` 行为。
- 直接原始调用：`self._require_enabled`
- 已解析到仓库内部的调用：`qts.application.services.strategy_service.StrategyLifecycleService._require_enabled`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.application.services.strategy_service.StrategyLifecycleService.list_instances`

- 位置：`backend/src/qts/application/services/strategy_service.py:41-42`
- 类型：`method`
- 签名：`def list_instances(self) -> tuple`
- 所属：`qts.application.services.strategy_service.StrategyLifecycleService`
- 作用：未写 docstring；静态推断为所属类上的 `list instances` 行为。
- 直接原始调用：`self._instances.values`, `tuple`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.application.services.strategy_service.StrategyLifecycleService._require_enabled`

- 位置：`backend/src/qts/application/services/strategy_service.py:44-47`
- 类型：`method`
- 签名：`def _require_enabled(self, strategy_id: StrategyId) -> None`
- 所属：`qts.application.services.strategy_service.StrategyLifecycleService`
- 作用：未写 docstring；静态推断为所属类上的 `require enabled` 行为。
- 直接原始调用：`ValueError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.application.services.strategy_service.StrategyLifecycleService.start`, `qts.application.services.strategy_service.StrategyLifecycleService.status`, `qts.application.services.strategy_service.StrategyLifecycleService.stop`

### `backend/src/qts/application/strategy_lifecycle.py`

模块：`qts.application.strategy_lifecycle`

#### `qts.application.strategy_lifecycle.StrategyStatus`

- 位置：`backend/src/qts/application/strategy_lifecycle.py:14-18`
- 类型：`class`
- 签名：`class StrategyStatus(StrEnum)`
- 继承/基类：`StrEnum`
- 作用：Configured strategy instance lifecycle status.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.application.strategy_lifecycle.StrategyInstance`

- 位置：`backend/src/qts/application/strategy_lifecycle.py:22-36`
- 类型：`class`
- 签名：`class StrategyInstance`
- 装饰器：`dataclass()`
- 作用：Configured runtime instance of a Strategy class.
- 直接原始调用：`Decimal`, `dataclass`, `field`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.application.strategy_lifecycle.StrategyInstance.__post_init__`

- 位置：`backend/src/qts/application/strategy_lifecycle.py:32-36`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.application.strategy_lifecycle.StrategyInstance`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x2, `Decimal`, `self.class_path.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.application.strategy_lifecycle.StrategyRegistry`

- 位置：`backend/src/qts/application/strategy_lifecycle.py:39-56`
- 类型：`class`
- 签名：`class StrategyRegistry`
- 作用：Safe registry for explicitly approved strategy classes.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.application.strategy_lifecycle.StrategyRegistry.__init__`

- 位置：`backend/src/qts/application/strategy_lifecycle.py:42-43`
- 类型：`method`
- 签名：`def __init__(self) -> None`
- 所属：`qts.application.strategy_lifecycle.StrategyRegistry`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.application.strategy_lifecycle.StrategyRegistry.register`

- 位置：`backend/src/qts/application/strategy_lifecycle.py:45-50`
- 类型：`method`
- 签名：`def register(self, class_path: str, strategy_cls: type) -> None`
- 所属：`qts.application.strategy_lifecycle.StrategyRegistry`
- 作用：未写 docstring；静态推断为所属类上的 `register` 行为。
- 直接原始调用：`ValueError` x2, `class_path.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.application.strategy_lifecycle.StrategyRegistry.resolve`

- 位置：`backend/src/qts/application/strategy_lifecycle.py:52-56`
- 类型：`method`
- 签名：`def resolve(self, class_path: str) -> type`
- 所属：`qts.application.strategy_lifecycle.StrategyRegistry`
- 作用：未写 docstring；静态推断为解析标识、引用或配置到目标对象（名称：resolve）。
- 直接原始调用：`KeyError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/backtest/__init__.py`

模块：`qts.backtest`

无类或函数定义。

### `backend/src/qts/backtest/config.py`

模块：`qts.backtest.config`

#### `qts.backtest.config.CostModelConfig`

- 位置：`backend/src/qts/backtest/config.py:21-43`
- 类型：`class`
- 签名：`class CostModelConfig`
- 装饰器：`dataclass()`
- 作用：Explicit backtest cost model settings.
- 直接原始调用：`Decimal` x2, `dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.config.BacktestRunConfig.from_yaml`

#### `qts.backtest.config.CostModelConfig.__post_init__`

- 位置：`backend/src/qts/backtest/config.py:27-37`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.backtest.config.CostModelConfig`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`Decimal` x4, `ValueError` x2, `object.__setattr__` x2, `str` x2
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.config.CostModelConfig.to_payload`

- 位置：`backend/src/qts/backtest/config.py:39-43`
- 类型：`method`
- 签名：`def to_payload(self) -> dict`
- 所属：`qts.backtest.config.CostModelConfig`
- 作用：未写 docstring；静态推断为转换或序列化为指定目标表示（名称：to payload）。
- 直接原始调用：`str` x2
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.config.RiskConfig`

- 位置：`backend/src/qts/backtest/config.py:47-58`
- 类型：`class`
- 签名：`class RiskConfig`
- 装饰器：`dataclass()`
- 作用：Backtest risk settings.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.config.BacktestRunConfig`, `qts.backtest.config.BacktestRunConfig.from_yaml`

#### `qts.backtest.config.RiskConfig.__post_init__`

- 位置：`backend/src/qts/backtest/config.py:52-55`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.backtest.config.RiskConfig`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`Decimal` x2, `ValueError`, `object.__setattr__`, `str`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.config.RiskConfig.to_payload`

- 位置：`backend/src/qts/backtest/config.py:57-58`
- 类型：`method`
- 签名：`def to_payload(self) -> dict`
- 所属：`qts.backtest.config.RiskConfig`
- 作用：未写 docstring；静态推断为转换或序列化为指定目标表示（名称：to payload）。
- 直接原始调用：`str`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.config.RollPolicyConfig`

- 位置：`backend/src/qts/backtest/config.py:62-75`
- 类型：`class`
- 签名：`class RollPolicyConfig`
- 装饰器：`dataclass()`
- 作用：Continuous futures roll policy for config-driven backtest runs.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.config.BacktestRunConfig.from_yaml`

#### `qts.backtest.config.RollPolicyConfig.__post_init__`

- 位置：`backend/src/qts/backtest/config.py:68-72`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.backtest.config.RollPolicyConfig`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError`, `object.__setattr__`, `self.method.strip`, `self.method.strip().lower`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.config.RollPolicyConfig.to_payload`

- 位置：`backend/src/qts/backtest/config.py:74-75`
- 类型：`method`
- 签名：`def to_payload(self) -> dict`
- 所属：`qts.backtest.config.RollPolicyConfig`
- 作用：未写 docstring；静态推断为转换或序列化为指定目标表示（名称：to payload）。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.config.BacktestMarketDataReference`

- 位置：`backend/src/qts/backtest/config.py:79-112`
- 类型：`class`
- 签名：`class BacktestMarketDataReference`
- 装饰器：`dataclass()`
- 作用：Market data source reference for one backtest run.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.config.BacktestRunConfig.__post_init__`, `qts.backtest.config.BacktestRunConfig._parse_historical_data_reference`, `qts.backtest.config.BacktestRunConfig._parse_market_data_reference`

#### `qts.backtest.config.BacktestMarketDataReference.__post_init__`

- 位置：`backend/src/qts/backtest/config.py:86-101`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.backtest.config.BacktestMarketDataReference`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x4, `object.__setattr__` x3, `Path`, `self.catalog.strip`, `self.source.strip`, `self.source.strip().lower`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.config.BacktestMarketDataReference.is_configured`

- 位置：`backend/src/qts/backtest/config.py:104-105`
- 类型：`property`
- 签名：`def is_configured(self) -> bool`
- 所属：`qts.backtest.config.BacktestMarketDataReference`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为判断布尔条件（名称：is configured）。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.config.BacktestMarketDataReference.to_payload`

- 位置：`backend/src/qts/backtest/config.py:107-112`
- 类型：`method`
- 签名：`def to_payload(self) -> dict[str, str] | None`
- 所属：`qts.backtest.config.BacktestMarketDataReference`
- 作用：未写 docstring；静态推断为转换或序列化为指定目标表示（名称：to payload）。
- 直接原始调用：`RuntimeError`, `str`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.config.BacktestStrategyConfig`

- 位置：`backend/src/qts/backtest/config.py:119-174`
- 类型：`class`
- 签名：`class BacktestStrategyConfig`
- 装饰器：`dataclass()`
- 作用：Configured strategy instance referenced by a backtest run.
- 直接原始调用：`Decimal`, `dataclass`, `field`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.config.BacktestRunConfig.__post_init__`

#### `qts.backtest.config.BacktestStrategyConfig.__post_init__`

- 位置：`backend/src/qts/backtest/config.py:129-139`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.backtest.config.BacktestStrategyConfig`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x4, `Decimal` x2, `object.__setattr__` x2, `dict`, `self.account_id.strip`, `self.class_path.strip`, `self.strategy_id.strip`, `str`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.config.BacktestStrategyConfig.from_yaml`

- 位置：`backend/src/qts/backtest/config.py:142-146`
- 类型：`classmethod`
- 签名：`def from_yaml(cls, path: Path) -> BacktestStrategyConfig`
- 所属：`qts.backtest.config.BacktestStrategyConfig`
- 装饰器：`classmethod`
- 作用：未写 docstring；静态推断为从指定来源构造或转换对象（名称：from yaml）。
- 直接原始调用：`ValueError`, `cls._parse_payload`, `isinstance`, `path.read_text`, `yaml.safe_load`
- 已解析到仓库内部的调用：`qts.backtest.config.BacktestStrategyConfig._parse_payload`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.config.BacktestStrategyConfig.to_payload`

- 位置：`backend/src/qts/backtest/config.py:148-156`
- 类型：`method`
- 签名：`def to_payload(self) -> dict`
- 所属：`qts.backtest.config.BacktestStrategyConfig`
- 作用：未写 docstring；静态推断为转换或序列化为指定目标表示（名称：to payload）。
- 直接原始调用：`str`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.config.BacktestStrategyConfig._parse_payload`

- 位置：`backend/src/qts/backtest/config.py:159-174`
- 类型：`classmethod`
- 签名：`def _parse_payload(cls, payload: dict) -> BacktestStrategyConfig`
- 所属：`qts.backtest.config.BacktestStrategyConfig`
- 装饰器：`classmethod`
- 作用：未写 docstring；静态推断为所属类上的 `parse payload` 行为。
- 直接原始调用：`payload.get` x5, `str` x4, `Decimal`, `ValueError`, `bool`, `cls`, `isinstance`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.config.BacktestStrategyConfig.from_yaml`

#### `qts.backtest.config.BacktestRunConfig`

- 位置：`backend/src/qts/backtest/config.py:178-417`
- 类型：`class`
- 签名：`class BacktestRunConfig`
- 装饰器：`dataclass()`
- 作用：Complete identity for a backtest run.
- 直接原始调用：`field` x7, `Decimal`, `RiskConfig`, `dataclass`
- 已解析到仓库内部的调用：`qts.backtest.config.RiskConfig`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.config.BacktestRunConfig.__post_init__`

- 位置：`backend/src/qts/backtest/config.py:202-264`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.backtest.config.BacktestRunConfig`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`object.__setattr__` x14, `ValueError` x10, `isinstance` x4, `BacktestMarketDataReference` x2, `Decimal` x2, `Path` x2, `dict` x2, `str` x2, `tuple` x2, `BacktestStrategyConfig`, `InstrumentId`, `all`, `root.strip`, `self._normalize_symbol`, `self.historical_data.to_payload`, `self.instrument_ids.items`, `self.market_data.to_payload`, `self.strategy_class.strip`, `self.timeframe.strip`
- 已解析到仓库内部的调用：`qts.backtest.config.BacktestMarketDataReference`, `qts.backtest.config.BacktestRunConfig._normalize_symbol`, `qts.backtest.config.BacktestStrategyConfig`, `qts.core.ids.InstrumentId`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.config.BacktestRunConfig.from_yaml`

- 位置：`backend/src/qts/backtest/config.py:267-337`
- 类型：`classmethod`
- 签名：`def from_yaml(cls, path: Path) -> BacktestRunConfig`
- 所属：`qts.backtest.config.BacktestRunConfig`
- 装饰器：`classmethod`
- 作用：未写 docstring；静态推断为从指定来源构造或转换对象（名称：from yaml）。
- 直接原始调用：`str` x12, `payload.get` x10, `ValueError` x7, `isinstance` x6, `Decimal` x4, `Path` x2, `cls._parse_datetime` x2, `cost_payload.get` x2, `roll_payload.get` x2, `tuple` x2, `BacktestStrategyConfig.from_yaml`, `CostModelConfig`, `InstrumentId`, `RiskConfig`, `RollPolicyConfig`, `bool`, `cls`, `cls._parse_historical_data_reference`, `cls._parse_market_data_reference`, `dict`, `instrument_ids_payload.items`, `int`, `path.read_text`, `risk_payload.get`, `yaml.safe_load`
- 已解析到仓库内部的调用：`qts.backtest.config.BacktestRunConfig._parse_datetime`, `qts.backtest.config.BacktestRunConfig._parse_historical_data_reference`, `qts.backtest.config.BacktestRunConfig._parse_market_data_reference`, `qts.backtest.config.CostModelConfig`, `qts.backtest.config.RiskConfig`, `qts.backtest.config.RollPolicyConfig`, `qts.core.ids.InstrumentId`
- 被以下仓库内部符号调用：`qts.backtest.runner.run_backtest`

#### `qts.backtest.config.BacktestRunConfig.config_hash`

- 位置：`backend/src/qts/backtest/config.py:340-341`
- 类型：`property`
- 签名：`def config_hash(self) -> str`
- 所属：`qts.backtest.config.BacktestRunConfig`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为所属类上的 `config hash` 行为。
- 直接原始调用：`self._stable_hash`, `self.to_payload`
- 已解析到仓库内部的调用：`qts.backtest.config.BacktestRunConfig._stable_hash`, `qts.backtest.config.BacktestRunConfig.to_payload`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.config.BacktestRunConfig.to_payload`

- 位置：`backend/src/qts/backtest/config.py:343-371`
- 类型：`method`
- 签名：`def to_payload(self) -> dict`
- 所属：`qts.backtest.config.BacktestRunConfig`
- 作用：未写 docstring；静态推断为转换或序列化为指定目标表示（名称：to payload）。
- 直接原始调用：`str` x3, `list` x2, `self.cost_model.to_payload`, `self.end.isoformat`, `self.instrument_ids.items`, `self.market_data.to_payload`, `self.risk_config.to_payload`, `self.roll_policy.to_payload`, `self.start.isoformat`, `self.strategy.to_payload`, `sorted`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.config.BacktestRunConfig.config_hash`

#### `qts.backtest.config.BacktestRunConfig._parse_datetime`

- 位置：`backend/src/qts/backtest/config.py:374-381`
- 类型：`staticmethod`
- 签名：`def _parse_datetime(value: datetime | str) -> datetime`
- 所属：`qts.backtest.config.BacktestRunConfig`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `parse datetime` 行为。
- 直接原始调用：`ValueError`, `datetime.fromisoformat`, `isinstance`, `parsed.astimezone`, `value.replace`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.config.BacktestRunConfig.from_yaml`

#### `qts.backtest.config.BacktestRunConfig._normalize_symbol`

- 位置：`backend/src/qts/backtest/config.py:384-388`
- 类型：`staticmethod`
- 签名：`def _normalize_symbol(symbol: str) -> str`
- 所属：`qts.backtest.config.BacktestRunConfig`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `normalize symbol` 行为。
- 直接原始调用：`ValueError`, `symbol.strip`, `symbol.strip().upper`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.config.BacktestRunConfig.__post_init__`

#### `qts.backtest.config.BacktestRunConfig._parse_market_data_reference`

- 位置：`backend/src/qts/backtest/config.py:391-400`
- 类型：`staticmethod`
- 签名：`def _parse_market_data_reference(payload: object) -> BacktestMarketDataReference`
- 所属：`qts.backtest.config.BacktestRunConfig`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `parse market data reference` 行为。
- 直接原始调用：`str` x3, `BacktestMarketDataReference` x2, `Path`, `ValueError`, `isinstance`, `payload.get`
- 已解析到仓库内部的调用：`qts.backtest.config.BacktestMarketDataReference`
- 被以下仓库内部符号调用：`qts.backtest.config.BacktestRunConfig.from_yaml`

#### `qts.backtest.config.BacktestRunConfig._parse_historical_data_reference`

- 位置：`backend/src/qts/backtest/config.py:403-412`
- 类型：`staticmethod`
- 签名：`def _parse_historical_data_reference(payload: object) -> BacktestMarketDataReference`
- 所属：`qts.backtest.config.BacktestRunConfig`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `parse historical data reference` 行为。
- 直接原始调用：`str` x3, `BacktestMarketDataReference` x2, `Path`, `ValueError`, `isinstance`, `payload.get`
- 已解析到仓库内部的调用：`qts.backtest.config.BacktestMarketDataReference`
- 被以下仓库内部符号调用：`qts.backtest.config.BacktestRunConfig.from_yaml`

#### `qts.backtest.config.BacktestRunConfig._stable_hash`

- 位置：`backend/src/qts/backtest/config.py:415-417`
- 类型：`staticmethod`
- 签名：`def _stable_hash(payload: Any) -> str`
- 所属：`qts.backtest.config.BacktestRunConfig`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `stable hash` 行为。
- 直接原始调用：`hashlib.sha256`, `hashlib.sha256().hexdigest`, `json.dumps`, `json.dumps().encode`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.config.BacktestRunConfig.config_hash`

### `backend/src/qts/backtest/engine.py`

模块：`qts.backtest.engine`

#### `qts.backtest.engine.BacktestCostModel`

- 位置：`backend/src/qts/backtest/engine.py:68-98`
- 类型：`class`
- 签名：`class BacktestCostModel`
- 装饰器：`dataclass()`
- 作用：Explicit simulation cost assumptions included in reports.
- 直接原始调用：`Decimal` x2, `dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine.__init__`, `qts.backtest.engine.BacktestEngine.from_config`

#### `qts.backtest.engine.BacktestCostModel.__post_init__`

- 位置：`backend/src/qts/backtest/engine.py:75-81`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.backtest.engine.BacktestCostModel`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x3, `Decimal` x2, `self.latency_model.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.engine.BacktestCostModel.to_payload`

- 位置：`backend/src/qts/backtest/engine.py:83-88`
- 类型：`method`
- 签名：`def to_payload(self) -> dict`
- 所属：`qts.backtest.engine.BacktestCostModel`
- 作用：未写 docstring；静态推断为转换或序列化为指定目标表示（名称：to payload）。
- 直接原始调用：`str` x2
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.engine.BacktestCostModel.slippage_model`

- 位置：`backend/src/qts/backtest/engine.py:91-92`
- 类型：`property`
- 签名：`def slippage_model(self) -> str`
- 所属：`qts.backtest.engine.BacktestCostModel`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为所属类上的 `slippage model` 行为。
- 直接原始调用：`Decimal`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.engine.BacktestCostModel.commission_model`

- 位置：`backend/src/qts/backtest/engine.py:95-98`
- 类型：`property`
- 签名：`def commission_model(self) -> str`
- 所属：`qts.backtest.engine.BacktestCostModel`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为所属类上的 `commission model` 行为。
- 直接原始调用：`Decimal`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.engine.BacktestStreamResult`

- 位置：`backend/src/qts/backtest/engine.py:102-118`
- 类型：`class`
- 签名：`class BacktestStreamResult`
- 装饰器：`dataclass()`
- 作用：Backtest result written to partitioned streaming artifacts.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine.run_streaming`

#### `qts.backtest.engine.BacktestEngine`

- 位置：`backend/src/qts/backtest/engine.py:121-877`
- 类型：`class`
- 签名：`class BacktestEngine`
- 作用：Single-process backtest engine using the Strategy SDK and actor order flow.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.engine.BacktestEngine._ProcessedIntent`

- 位置：`backend/src/qts/backtest/engine.py:125-127`
- 类型：`class`
- 签名：`class _ProcessedIntent`
- 所属：`BacktestEngine`
- 装饰器：`dataclass()`
- 作用：未写 docstring；静态推断为定义 Processed Intent 概念或数据结构。
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.engine.BacktestEngine._RuntimeRunResult`

- 位置：`backend/src/qts/backtest/engine.py:130-138`
- 类型：`class`
- 签名：`class _RuntimeRunResult`
- 所属：`BacktestEngine`
- 装饰器：`dataclass()`
- 作用：未写 docstring；静态推断为定义 Runtime Run Result 概念或数据结构。
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.engine.BacktestEngine._RuntimeRunResult.processed_bars`

- 位置：`backend/src/qts/backtest/engine.py:137-138`
- 类型：`property`
- 签名：`def processed_bars(self) -> int`
- 所属：`qts.backtest.engine.BacktestEngine._RuntimeRunResult`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为所属类上的 `processed bars` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.engine.BacktestEngine._StreamingBacktestSink`

- 位置：`backend/src/qts/backtest/engine.py:140-165`
- 类型：`class`
- 签名：`class _StreamingBacktestSink`
- 所属：`BacktestEngine`
- 作用：未写 docstring；静态推断为定义 Streaming Backtest Sink 概念或数据结构。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.engine.BacktestEngine._StreamingBacktestSink.__init__`

- 位置：`backend/src/qts/backtest/engine.py:141-143`
- 类型：`method`
- 签名：`def __init__(self, writer: StreamingBacktestArtifactWriter) -> None`
- 所属：`qts.backtest.engine.BacktestEngine._StreamingBacktestSink`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.engine.BacktestEngine._StreamingBacktestSink.order_count`

- 位置：`backend/src/qts/backtest/engine.py:146-147`
- 类型：`property`
- 签名：`def order_count(self) -> int`
- 所属：`qts.backtest.engine.BacktestEngine._StreamingBacktestSink`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为所属类上的 `order count` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.engine.BacktestEngine._StreamingBacktestSink.write_processed`

- 位置：`backend/src/qts/backtest/engine.py:149-162`
- 类型：`method`
- 签名：`def write_processed(self, engine: BacktestEngine, processed: BacktestEngine._ProcessedIntent, *, bar: Bar) -> None`
- 所属：`qts.backtest.engine.BacktestEngine._StreamingBacktestSink`
- 作用：未写 docstring；静态推断为写入数据（名称：write processed）。
- 直接原始调用：`engine._fill_payload`, `engine._ledger_rows`, `engine._order_payload`, `len`, `self._writer.write_fill`, `self._writer.write_order`, `self._writer.write_trade_ledger`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.engine.BacktestEngine._StreamingBacktestSink.write_equity_point`

- 位置：`backend/src/qts/backtest/engine.py:164-165`
- 类型：`method`
- 签名：`def write_equity_point(self, point: EquityCurvePoint) -> None`
- 所属：`qts.backtest.engine.BacktestEngine._StreamingBacktestSink`
- 作用：未写 docstring；静态推断为写入数据（名称：write equity point）。
- 直接原始调用：`self._writer.write_equity_point`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.engine.BacktestEngine.__init__`

- 位置：`backend/src/qts/backtest/engine.py:167-206`
- 类型：`method`
- 签名：`def __init__(self, *, strategy: Strategy, bars: Iterable, initial_cash: Decimal, risk_engine: RiskEngine | None = None, dataset_metadata: Iterable = (), config: dict[str, Any] | None = None, strategy_version: str | None = None, cost_model: BacktestCostModel | None = None, contract_multipliers: Mapping[InstrumentId, Decimal] | None = None, future_roll_registry: FutureRollRegistry | None = None, warmup_bars: int = 0, target_timeframe: str | None = None, exchange_timezone_by_instrument: Mapping[InstrumentId, str | tzinfo] | None = None, instrument_registry: InstrumentRegistry | None = None) -> None`
- 所属：`qts.backtest.engine.BacktestEngine`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：`dict` x2, `iter` x2, `tuple` x2, `BacktestCostModel`, `Decimal`, `MaxNotionalRule`, `RiskEngine`, `isinstance`
- 已解析到仓库内部的调用：`qts.backtest.engine.BacktestCostModel`, `qts.risk.risk_engine.RiskEngine`, `qts.risk.rules.max_notional.MaxNotionalRule`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.engine.BacktestEngine.from_config`

- 位置：`backend/src/qts/backtest/engine.py:209-241`
- 类型：`classmethod`
- 签名：`def from_config(cls, config: BacktestRunConfig, *, bars: Iterable, strategy: Strategy, instrument_registry: InstrumentRegistry | None = None, dataset_metadata: Iterable = (), future_roll_registry: FutureRollRegistry | None = None, exchange_timezone_by_instrument: Mapping[InstrumentId, str | tzinfo] | None = None, contract_multipliers: Mapping[InstrumentId, Decimal] | None = None) -> BacktestEngine`
- 所属：`qts.backtest.engine.BacktestEngine`
- 装饰器：`classmethod`
- 作用：未写 docstring；静态推断为从指定来源构造或转换对象（名称：from config）。
- 直接原始调用：`BacktestCostModel`, `MaxNotionalRule`, `RiskEngine`, `cls`, `config.to_payload`
- 已解析到仓库内部的调用：`qts.backtest.engine.BacktestCostModel`, `qts.risk.risk_engine.RiskEngine`, `qts.risk.rules.max_notional.MaxNotionalRule`
- 被以下仓库内部符号调用：`qts.backtest.runner.run_backtest`

#### `qts.backtest.engine.BacktestEngine._take_strategy_bar_result`

- 位置：`backend/src/qts/backtest/engine.py:244-252`
- 类型：`staticmethod`
- 签名：`def _take_strategy_bar_result(mailbox: Mailbox) -> StrategyBarResult`
- 所属：`qts.backtest.engine.BacktestEngine`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `take strategy bar result` 行为。
- 直接原始调用：`RuntimeError` x2, `mailbox.empty` x2, `TypeError`, `isinstance`, `mailbox.get`, `type`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._run_actor_loop`

#### `qts.backtest.engine.BacktestEngine._take_signal_batch`

- 位置：`backend/src/qts/backtest/engine.py:255-263`
- 类型：`staticmethod`
- 签名：`def _take_signal_batch(mailbox: Mailbox) -> AggregatedSignalBatch`
- 所属：`qts.backtest.engine.BacktestEngine`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `take signal batch` 行为。
- 直接原始调用：`RuntimeError` x2, `mailbox.empty` x2, `TypeError`, `isinstance`, `mailbox.get`, `type`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._run_actor_loop`

#### `qts.backtest.engine.BacktestEngine._take_strategy_finalized`

- 位置：`backend/src/qts/backtest/engine.py:266-274`
- 类型：`staticmethod`
- 签名：`def _take_strategy_finalized(mailbox: Mailbox) -> StrategyFinalized`
- 所属：`qts.backtest.engine.BacktestEngine`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `take strategy finalized` 行为。
- 直接原始调用：`RuntimeError` x2, `mailbox.empty` x2, `TypeError`, `isinstance`, `mailbox.get`, `type`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._run_actor_loop`

#### `qts.backtest.engine.BacktestEngine._market_data_ref_for`

- 位置：`backend/src/qts/backtest/engine.py:276-306`
- 类型：`method`
- 签名：`def _market_data_ref_for(self, bar: Bar, *, refs: dict, subscriber: ActorRef) -> ActorRef`
- 所属：`qts.backtest.engine.BacktestEngine`
- 作用：未写 docstring；静态推断为所属类上的 `market data ref for` 行为。
- 直接原始调用：`ActorRef`, `Mailbox`, `MarketDataActor`, `RuntimeError`, `refs.get`
- 已解析到仓库内部的调用：`qts.runtime.actor_ref.ActorRef`, `qts.runtime.actors.market_data_actor.MarketDataActor`, `qts.runtime.mailbox.Mailbox`
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._run_actor_loop`

#### `qts.backtest.engine.BacktestEngine._run_actor_loop`

- 位置：`backend/src/qts/backtest/engine.py:308-455`
- 类型：`method`
- 签名：`def _run_actor_loop(self, *, sink: BacktestEngine._StreamingBacktestSink, prune_history: bool, compact_orders: bool) -> BacktestEngine._RuntimeRunResult`
- 所属：`qts.backtest.engine.BacktestEngine`
- 作用：未写 docstring；静态推断为所属类上的 `run actor loop` 行为。
- 直接原始调用：`ActorRef` x9, `Mailbox` x8, `account_actor.snapshot` x4, `len` x2, `self._equity_point` x2, `sink.write_equity_point` x2, `strategy_ref.process_all` x2, `strategy_ref.tell` x2, `AccountActor`, `BacktestEngine._RuntimeRunResult`, `ExecutionActor`, `HistoricalDataPortal`, `MarketDataEvent`, `OrderManagerActor`, `SignalAggregatorActor`, `StrategyActor`, `StrategyBarEvent`, `StrategyContext`, `StrategyFinalize`, `StrategySignalEvent`, `TypeError`, `_BacktestExecutionAdapter`, `defaultdict`, `history.append`, `isinstance`, `market_data_mailbox.empty`, `market_data_mailbox.get`, `market_data_ref.process_all`, `market_data_ref.tell`, `order_manager_actor.compact_for_streaming`, `portal.data_view`, `self._history_limit_from_subscriptions`, `self._instrument_registry_for`, `self._market_data_ref_for`, `self._portfolio_view`, `self._process_intent`, `self._take_signal_batch`, `self._take_strategy_bar_result`, `self._take_strategy_finalized`, `self._update_rolling_prices`, `signal_ref.process_all`, `signal_ref.tell`, `sink.write_processed`, `type`
- 已解析到仓库内部的调用：`qts.backtest.engine.BacktestEngine._equity_point`, `qts.backtest.engine.BacktestEngine._history_limit_from_subscriptions`, `qts.backtest.engine.BacktestEngine._instrument_registry_for`, `qts.backtest.engine.BacktestEngine._market_data_ref_for`, `qts.backtest.engine.BacktestEngine._portfolio_view`, `qts.backtest.engine.BacktestEngine._process_intent`, `qts.backtest.engine.BacktestEngine._take_signal_batch`, `qts.backtest.engine.BacktestEngine._take_strategy_bar_result`, `qts.backtest.engine.BacktestEngine._take_strategy_finalized`, `qts.backtest.engine.BacktestEngine._update_rolling_prices`, `qts.backtest.engine._BacktestExecutionAdapter`, `qts.backtest.historical_data_portal.HistoricalDataPortal`, `qts.runtime.actor_ref.ActorRef`, `qts.runtime.actors.account_actor.AccountActor`, `qts.runtime.actors.execution_actor.ExecutionActor`, `qts.runtime.actors.market_data_actor.MarketDataEvent`, `qts.runtime.actors.order_manager_actor.OrderManagerActor`, `qts.runtime.actors.signal_aggregator_actor.SignalAggregatorActor`, `qts.runtime.actors.signal_aggregator_actor.StrategySignalEvent`, `qts.runtime.actors.strategy_actor.StrategyActor`, `qts.runtime.actors.strategy_actor.StrategyBarEvent`, `qts.runtime.actors.strategy_actor.StrategyFinalize`, `qts.runtime.mailbox.Mailbox`, `qts.strategy_sdk.context.StrategyContext`
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine.run_streaming`

#### `qts.backtest.engine.BacktestEngine.run_streaming`

- 位置：`backend/src/qts/backtest/engine.py:457-502`
- 类型：`method`
- 签名：`def run_streaming(self, output_dir: Any) -> BacktestStreamResult`
- 所属：`qts.backtest.engine.BacktestEngine`
- 作用：未写 docstring；静态推断为运行流程或命令（名称：run streaming）。
- 直接原始调用：`BacktestEngine._StreamingBacktestSink`, `BacktestRunId`, `BacktestStreamResult`, `EquityCurvePoint`, `StreamingBacktestArtifactWriter`, `self._cost_model.to_payload`, `self._dataset_payload`, `self._run_actor_loop`, `self._stable_hash`, `self._zero_time`, `sink.write_equity_point`, `tuple`, `writer.finalize`
- 已解析到仓库内部的调用：`qts.backtest.engine.BacktestEngine._dataset_payload`, `qts.backtest.engine.BacktestEngine._run_actor_loop`, `qts.backtest.engine.BacktestEngine._stable_hash`, `qts.backtest.engine.BacktestEngine._zero_time`, `qts.backtest.engine.BacktestStreamResult`, `qts.backtest.report.EquityCurvePoint`, `qts.backtest.report.StreamingBacktestArtifactWriter`, `qts.core.ids.BacktestRunId`
- 被以下仓库内部符号调用：`qts.backtest.runner.run_backtest`

#### `qts.backtest.engine.BacktestEngine._process_intent`

- 位置：`backend/src/qts/backtest/engine.py:504-582`
- 类型：`method`
- 签名：`def _process_intent(self, intent: TargetIntent, *, bar: Bar, account_actor: AccountActor, order_manager_actor: OrderManagerActor, order_manager_ref: ActorRef, execution_ref: ActorRef, account_ref: ActorRef, order_number: int) -> BacktestEngine._ProcessedIntent`
- 所属：`qts.backtest.engine.BacktestEngine`
- 作用：未写 docstring；静态推断为所属类上的 `process intent` 行为。
- 直接原始调用：`Decimal` x3, `order_requests.append` x2, `self._ProcessedIntent` x2, `tuple` x2, `Position`, `account_actor.snapshot`, `enumerate`, `fills.extend`, `orders.extend`, `self._desired_quantity`, `self._future_roll_registry.execution_price`, `self._future_roll_registry.is_continuous`, `self._market_price_for_intent`, `self._multiplier_for`, `self._order_instrument_for_intent`, `self._process_order_delta`, `self._related_contracts_for`, `snapshot.positions.get`, `snapshot.positions.items`
- 已解析到仓库内部的调用：`qts.backtest.engine.BacktestEngine._desired_quantity`, `qts.backtest.engine.BacktestEngine._market_price_for_intent`, `qts.backtest.engine.BacktestEngine._multiplier_for`, `qts.backtest.engine.BacktestEngine._order_instrument_for_intent`, `qts.backtest.engine.BacktestEngine._process_order_delta`, `qts.backtest.engine.BacktestEngine._related_contracts_for`, `qts.portfolio.position_book.Position`
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._run_actor_loop`

#### `qts.backtest.engine.BacktestEngine._process_order_delta`

- 位置：`backend/src/qts/backtest/engine.py:584-636`
- 类型：`method`
- 签名：`def _process_order_delta(self, *, instrument_id: InstrumentId, quantity_delta: Decimal, market_price: Decimal, order_time: Any, order_manager_actor: OrderManagerActor, order_manager_ref: ActorRef, execution_ref: ActorRef, account_ref: ActorRef, order_number: int, multiplier: Decimal) -> BacktestEngine._ProcessedIntent`
- 所属：`qts.backtest.engine.BacktestEngine`
- 作用：未写 docstring；静态推断为所属类上的 `process order delta` 行为。
- 直接原始调用：`self._ProcessedIntent` x3, `Decimal` x2, `order_manager_ref.process_all` x2, `OrderId`, `OrderIntent`, `OrderRiskRequest`, `SubmitOrder`, `abs`, `account_ref.process_all`, `execution_ref.process_all`, `order_manager_actor.fills_since`, `order_manager_actor.get_order`, `order_manager_ref.tell`, `self._risk_engine.check`
- 已解析到仓库内部的调用：`qts.core.ids.OrderId`, `qts.domain.risk.request.OrderRiskRequest`, `qts.execution.order_manager.OrderIntent`, `qts.runtime.actors.order_manager_actor.SubmitOrder`
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._process_intent`

#### `qts.backtest.engine.BacktestEngine._order_instrument_for_intent`

- 位置：`backend/src/qts/backtest/engine.py:638-646`
- 类型：`method`
- 签名：`def _order_instrument_for_intent(self, intent: TargetIntent, *, bar: Bar) -> InstrumentId`
- 所属：`qts.backtest.engine.BacktestEngine`
- 作用：未写 docstring；静态推断为所属类上的 `order instrument for intent` 行为。
- 直接原始调用：`self._future_roll_registry.is_continuous`, `self._future_roll_registry.resolve_contract`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._process_intent`

#### `qts.backtest.engine.BacktestEngine._market_price_for_intent`

- 位置：`backend/src/qts/backtest/engine.py:648-663`
- 类型：`method`
- 签名：`def _market_price_for_intent(self, intent: TargetIntent, *, instrument_id: InstrumentId, bar: Bar) -> Decimal`
- 所属：`qts.backtest.engine.BacktestEngine`
- 作用：未写 docstring；静态推断为所属类上的 `market price for intent` 行为。
- 直接原始调用：`self._future_roll_registry.execution_price`, `self._future_roll_registry.is_continuous`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._process_intent`

#### `qts.backtest.engine.BacktestEngine._desired_quantity`

- 位置：`backend/src/qts/backtest/engine.py:666-684`
- 类型：`staticmethod`
- 签名：`def _desired_quantity(intent: TargetIntent, *, current_quantity: Decimal, bar: Bar) -> Decimal`
- 所属：`qts.backtest.engine.BacktestEngine`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `desired quantity` 行为。
- 直接原始调用：`ValueError` x2, `Decimal`, `max`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._process_intent`

#### `qts.backtest.engine.BacktestEngine._update_rolling_prices`

- 位置：`backend/src/qts/backtest/engine.py:686-707`
- 类型：`method`
- 签名：`def _update_rolling_prices(self, bar: Bar, *, latest_prices: dict) -> None`
- 所属：`qts.backtest.engine.BacktestEngine`
- 作用：未写 docstring；静态推断为所属类上的 `update rolling prices` 行为。
- 直接原始调用：`self._future_roll_registry.execution_price`, `self._future_roll_registry.is_continuous`, `self._future_roll_registry.resolve_contract`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._run_actor_loop`

#### `qts.backtest.engine.BacktestEngine._related_contracts_for`

- 位置：`backend/src/qts/backtest/engine.py:709-720`
- 类型：`method`
- 签名：`def _related_contracts_for(self, continuous_instrument_id: InstrumentId) -> frozenset`
- 所属：`qts.backtest.engine.BacktestEngine`
- 作用：未写 docstring；静态推断为所属类上的 `related contracts for` 行为。
- 直接原始调用：`RuntimeError`, `frozenset`, `self._future_roll_registry.related_contracts`, `self._related_contracts_by_continuous.get`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._process_intent`

#### `qts.backtest.engine.BacktestEngine._portfolio_view`

- 位置：`backend/src/qts/backtest/engine.py:722-743`
- 类型：`method`
- 签名：`def _portfolio_view(self, snapshot: AccountSnapshot, *, latest_prices: Mapping) -> PortfolioView`
- 所属：`qts.backtest.engine.BacktestEngine`
- 作用：未写 docstring；静态推断为所属类上的 `portfolio view` 行为。
- 直接原始调用：`Decimal` x2, `PortfolioPosition`, `PortfolioView`, `latest_prices.get`, `positions.values`, `self._multiplier_for`, `snapshot.positions.items`, `sum`
- 已解析到仓库内部的调用：`qts.backtest.engine.BacktestEngine._multiplier_for`, `qts.strategy_sdk.portfolio_view.PortfolioPosition`, `qts.strategy_sdk.portfolio_view.PortfolioView`
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._equity_point`, `qts.backtest.engine.BacktestEngine._run_actor_loop`

#### `qts.backtest.engine.BacktestEngine._equity_point`

- 位置：`backend/src/qts/backtest/engine.py:745-758`
- 类型：`method`
- 签名：`def _equity_point(self, bar: Bar, snapshot: AccountSnapshot, *, latest_prices: Mapping) -> EquityCurvePoint`
- 所属：`qts.backtest.engine.BacktestEngine`
- 作用：未写 docstring；静态推断为所属类上的 `equity point` 行为。
- 直接原始调用：`EquityCurvePoint`, `self._portfolio_view`
- 已解析到仓库内部的调用：`qts.backtest.engine.BacktestEngine._portfolio_view`, `qts.backtest.report.EquityCurvePoint`
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._run_actor_loop`

#### `qts.backtest.engine.BacktestEngine._instrument_registry_for`

- 位置：`backend/src/qts/backtest/engine.py:760-791`
- 类型：`method`
- 签名：`def _instrument_registry_for(self) -> InstrumentRegistry`
- 所属：`qts.backtest.engine.BacktestEngine`
- 作用：未写 docstring；静态推断为所属类上的 `instrument registry for` 行为。
- 直接原始调用：`Decimal` x2, `ContractSpec`, `Instrument`, `InstrumentRegistry`, `RuntimeError`, `registry.register`, `seen.add`, `self._exchange_for`, `self._multiplier_for`, `self._symbol_for`, `set`
- 已解析到仓库内部的调用：`qts.backtest.engine.BacktestEngine._exchange_for`, `qts.backtest.engine.BacktestEngine._multiplier_for`, `qts.backtest.engine.BacktestEngine._symbol_for`, `qts.domain.instruments.contract_spec.ContractSpec`, `qts.domain.instruments.instrument.Instrument`, `qts.registry.instrument_registry.InstrumentRegistry`
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._run_actor_loop`

#### `qts.backtest.engine.BacktestEngine._history_limit_from_subscriptions`

- 位置：`backend/src/qts/backtest/engine.py:794-797`
- 类型：`staticmethod`
- 签名：`def _history_limit_from_subscriptions(ctx: StrategyContext) -> int | None`
- 所属：`qts.backtest.engine.BacktestEngine`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `history limit from subscriptions` 行为。
- 直接原始调用：`max`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._run_actor_loop`

#### `qts.backtest.engine.BacktestEngine._multiplier_for`

- 位置：`backend/src/qts/backtest/engine.py:799-800`
- 类型：`method`
- 签名：`def _multiplier_for(self, instrument_id: InstrumentId) -> Decimal`
- 所属：`qts.backtest.engine.BacktestEngine`
- 作用：未写 docstring；静态推断为所属类上的 `multiplier for` 行为。
- 直接原始调用：`Decimal`, `self._contract_multipliers.get`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._instrument_registry_for`, `qts.backtest.engine.BacktestEngine._portfolio_view`, `qts.backtest.engine.BacktestEngine._process_intent`

#### `qts.backtest.engine.BacktestEngine._symbol_for`

- 位置：`backend/src/qts/backtest/engine.py:803-804`
- 类型：`staticmethod`
- 签名：`def _symbol_for(instrument_id: InstrumentId) -> str`
- 所属：`qts.backtest.engine.BacktestEngine`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `symbol for` 行为。
- 直接原始调用：`instrument_id.value.rsplit`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._instrument_registry_for`

#### `qts.backtest.engine.BacktestEngine._exchange_for`

- 位置：`backend/src/qts/backtest/engine.py:807-811`
- 类型：`staticmethod`
- 签名：`def _exchange_for(instrument_id: InstrumentId) -> str`
- 所属：`qts.backtest.engine.BacktestEngine`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `exchange for` 行为。
- 直接原始调用：`instrument_id.value.split`, `len`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._instrument_registry_for`

#### `qts.backtest.engine.BacktestEngine._ledger_rows`

- 位置：`backend/src/qts/backtest/engine.py:814-828`
- 类型：`staticmethod`
- 签名：`def _ledger_rows(fills: Iterable, *, bar: Bar) -> tuple`
- 所属：`qts.backtest.engine.BacktestEngine`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `ledger rows` 行为。
- 直接原始调用：`TradeLedgerEntry`, `tuple`
- 已解析到仓库内部的调用：`qts.backtest.report.TradeLedgerEntry`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.engine.BacktestEngine._order_payload`

- 位置：`backend/src/qts/backtest/engine.py:831-839`
- 类型：`staticmethod`
- 签名：`def _order_payload(order: Order) -> dict`
- 所属：`qts.backtest.engine.BacktestEngine`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `order payload` 行为。
- 直接原始调用：`str`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.engine.BacktestEngine._fill_payload`

- 位置：`backend/src/qts/backtest/engine.py:842-852`
- 类型：`staticmethod`
- 签名：`def _fill_payload(fill: OrderFill) -> dict`
- 所属：`qts.backtest.engine.BacktestEngine`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `fill payload` 行为。
- 直接原始调用：`str` x4
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.engine.BacktestEngine._dataset_payload`

- 位置：`backend/src/qts/backtest/engine.py:855-866`
- 类型：`staticmethod`
- 签名：`def _dataset_payload(item: DatasetMetadata) -> dict`
- 所属：`qts.backtest.engine.BacktestEngine`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `dataset payload` 行为。
- 直接原始调用：`item.created_at.isoformat`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine.run_streaming`

#### `qts.backtest.engine.BacktestEngine._stable_hash`

- 位置：`backend/src/qts/backtest/engine.py:869-871`
- 类型：`staticmethod`
- 签名：`def _stable_hash(payload: Any) -> str`
- 所属：`qts.backtest.engine.BacktestEngine`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `stable hash` 行为。
- 直接原始调用：`hashlib.sha256`, `hashlib.sha256().hexdigest`, `json.dumps`, `json.dumps().encode`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine.run_streaming`

#### `qts.backtest.engine.BacktestEngine._zero_time`

- 位置：`backend/src/qts/backtest/engine.py:874-877`
- 类型：`staticmethod`
- 签名：`def _zero_time() -> Any`
- 所属：`qts.backtest.engine.BacktestEngine`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `zero time` 行为。
- 直接原始调用：`datetime`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine.run_streaming`

#### `qts.backtest.engine._BacktestExecutionAdapter`

- 位置：`backend/src/qts/backtest/engine.py:880-907`
- 类型：`class`
- 签名：`class _BacktestExecutionAdapter`
- 作用：未写 docstring；静态推断为定义 Backtest Execution Adapter 概念或数据结构。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._run_actor_loop`

#### `qts.backtest.engine._BacktestExecutionAdapter.__init__`

- 位置：`backend/src/qts/backtest/engine.py:881-882`
- 类型：`method`
- 签名：`def __init__(self, cost_model: BacktestCostModel) -> None`
- 所属：`qts.backtest.engine._BacktestExecutionAdapter`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.engine._BacktestExecutionAdapter.execute_market_order`

- 位置：`backend/src/qts/backtest/engine.py:884-907`
- 类型：`method`
- 签名：`def execute_market_order(self, intent: OrderIntent, *, broker_order_id: str, market_price: Decimal) -> ExecutionReport`
- 所属：`qts.backtest.engine._BacktestExecutionAdapter`
- 作用：未写 docstring；静态推断为所属类上的 `execute market order` 行为。
- 直接原始调用：`Decimal` x2, `ExecutionReport`, `ValueError`, `abs`
- 已解析到仓库内部的调用：`qts.execution.order_manager.ExecutionReport`
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/backtest/historical_data_portal.py`

模块：`qts.backtest.historical_data_portal`

#### `qts.backtest.historical_data_portal.HistoricalDataPortal`

- 位置：`backend/src/qts/backtest/historical_data_portal.py:13-33`
- 类型：`class`
- 签名：`class HistoricalDataPortal`
- 作用：Returns finalized bars visible as of a replay timestamp.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._run_actor_loop`

#### `qts.backtest.historical_data_portal.HistoricalDataPortal.__init__`

- 位置：`backend/src/qts/backtest/historical_data_portal.py:16-20`
- 类型：`method`
- 签名：`def __init__(self, bars: Mapping) -> None`
- 所属：`qts.backtest.historical_data_portal.HistoricalDataPortal`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：`bars.items`, `sorted`, `tuple`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.historical_data_portal.HistoricalDataPortal.data_view`

- 位置：`backend/src/qts/backtest/historical_data_portal.py:22-23`
- 类型：`method`
- 签名：`def data_view(self, *, as_of: datetime) -> DataView`
- 所属：`qts.backtest.historical_data_portal.HistoricalDataPortal`
- 作用：未写 docstring；静态推断为所属类上的 `data view` 行为。
- 直接原始调用：`DataView`
- 已解析到仓库内部的调用：`qts.strategy_sdk.data_view.DataView`
- 被以下仓库内部符号调用：`qts.backtest.historical_data_portal.HistoricalDataPortal.history`

#### `qts.backtest.historical_data_portal.HistoricalDataPortal.history`

- 位置：`backend/src/qts/backtest/historical_data_portal.py:25-33`
- 类型：`method`
- 签名：`def history(self, asset: AssetRef, *, as_of: datetime, bars: int, timeframe: str | None = None) -> tuple`
- 所属：`qts.backtest.historical_data_portal.HistoricalDataPortal`
- 作用：未写 docstring；静态推断为所属类上的 `history` 行为。
- 直接原始调用：`self.data_view`, `self.data_view().history`
- 已解析到仓库内部的调用：`qts.backtest.historical_data_portal.HistoricalDataPortal.data_view`
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/backtest/inputs.py`

模块：`qts.backtest.inputs`

#### `qts.backtest.inputs.BacktestInputBundle`

- 位置：`backend/src/qts/backtest/inputs.py:22-31`
- 类型：`class`
- 签名：`class BacktestInputBundle`
- 装饰器：`dataclass()`
- 作用：Streaming inputs and side-channel metadata required by a backtest run.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.inputs.BacktestInputBuilder.build`

#### `qts.backtest.inputs.BacktestInputBuilder`

- 位置：`backend/src/qts/backtest/inputs.py:34-327`
- 类型：`class`
- 签名：`class BacktestInputBuilder`
- 作用：Build replay-ready market data, registry, and provenance inputs.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.runner.run_backtest`

#### `qts.backtest.inputs.BacktestInputBuilder.__init__`

- 位置：`backend/src/qts/backtest/inputs.py:37-39`
- 类型：`method`
- 签名：`def __init__(self, config: BacktestRunConfig, catalog: HistoricalCatalog) -> None`
- 所属：`qts.backtest.inputs.BacktestInputBuilder`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.inputs.BacktestInputBuilder.build`

- 位置：`backend/src/qts/backtest/inputs.py:41-58`
- 类型：`method`
- 签名：`def build(self) -> BacktestInputBundle`
- 所属：`qts.backtest.inputs.BacktestInputBuilder`
- 作用：未写 docstring；静态推断为组装对象、请求或运行上下文（名称：build）。
- 直接原始调用：`BacktestInputBundle`, `self._contract_multipliers_for`, `self._dataset_metadata`, `self._instrument_registry_for`, `self._roll_registry`, `self._stream_configured_bars`
- 已解析到仓库内部的调用：`qts.backtest.inputs.BacktestInputBuilder._contract_multipliers_for`, `qts.backtest.inputs.BacktestInputBuilder._dataset_metadata`, `qts.backtest.inputs.BacktestInputBuilder._instrument_registry_for`, `qts.backtest.inputs.BacktestInputBuilder._roll_registry`, `qts.backtest.inputs.BacktestInputBuilder._stream_configured_bars`, `qts.backtest.inputs.BacktestInputBundle`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.inputs.BacktestInputBuilder._roll_registry`

- 位置：`backend/src/qts/backtest/inputs.py:60-63`
- 类型：`method`
- 签名：`def _roll_registry(self) -> FutureRollRegistry | None`
- 所属：`qts.backtest.inputs.BacktestInputBuilder`
- 作用：未写 docstring；静态推断为所属类上的 `roll registry` 行为。
- 直接原始调用：`FutureRollRegistry`, `len`
- 已解析到仓库内部的调用：`qts.registry.future_roll.FutureRollRegistry`
- 被以下仓库内部符号调用：`qts.backtest.inputs.BacktestInputBuilder.build`

#### `qts.backtest.inputs.BacktestInputBuilder._stream_configured_bars`

- 位置：`backend/src/qts/backtest/inputs.py:65-129`
- 类型：`method`
- 签名：`def _stream_configured_bars(self, catalog: HistoricalCatalog, *, roll_registry: FutureRollRegistry | None) -> tuple`
- 所属：`qts.backtest.inputs.BacktestInputBuilder`
- 作用：未写 docstring；静态推断为所属类上的 `stream configured bars` 行为。
- 直接原始调用：`dataset.chain.instrument_id_for_symbol` x2, `exchange_timezones.setdefault` x2, `HighestVolumeFutureContractSelector`, `RuntimeError`, `ValueError`, `enumerate`, `iter_historical_bars`, `roll_registry.register_root`, `self._exchange_timezone_for`, `self._iter_root_bars`, `self._merge_ordered_bar_streams`, `set`, `streams.append`, `tuple`
- 已解析到仓库内部的调用：`qts.backtest.inputs.BacktestInputBuilder._exchange_timezone_for`, `qts.backtest.inputs.BacktestInputBuilder._iter_root_bars`, `qts.backtest.inputs.BacktestInputBuilder._merge_ordered_bar_streams`, `qts.data.historical.csv_dataset.iter_historical_bars`, `qts.registry.future_roll.HighestVolumeFutureContractSelector`
- 被以下仓库内部符号调用：`qts.backtest.inputs.BacktestInputBuilder.build`

#### `qts.backtest.inputs.BacktestInputBuilder._iter_root_bars`

- 位置：`backend/src/qts/backtest/inputs.py:131-167`
- 类型：`method`
- 签名：`def _iter_root_bars(self, root: str, stream: HistoricalBarStream, *, requested: set, rolling_root: bool, roll_registry: FutureRollRegistry | None, stats: dict, exchange_timezones: dict, exchange_timezone: str | None) -> Iterator`
- 所属：`qts.backtest.inputs.BacktestInputBuilder`
- 作用：未写 docstring；静态推断为所属类上的 `iter root bars` 行为。
- 直接原始调用：`self._record_exchange_timezone` x2, `RuntimeError`, `bar.instrument_id.value.rsplit`, `len`, `roll_registry.record_selection`, `stream.stats.as_dict`
- 已解析到仓库内部的调用：`qts.backtest.inputs.BacktestInputBuilder._record_exchange_timezone`
- 被以下仓库内部符号调用：`qts.backtest.inputs.BacktestInputBuilder._stream_configured_bars`

#### `qts.backtest.inputs.BacktestInputBuilder._merge_ordered_bar_streams`

- 位置：`backend/src/qts/backtest/inputs.py:170-190`
- 类型：`staticmethod`
- 签名：`def _merge_ordered_bar_streams(streams: list) -> Iterator`
- 所属：`qts.backtest.inputs.BacktestInputBuilder`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `merge ordered bar streams` 行为。
- 直接原始调用：`heapq.heappush` x2, `next` x2, `heapq.heappop`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.inputs.BacktestInputBuilder._stream_configured_bars`

#### `qts.backtest.inputs.BacktestInputBuilder._record_exchange_timezone`

- 位置：`backend/src/qts/backtest/inputs.py:193-200`
- 类型：`staticmethod`
- 签名：`def _record_exchange_timezone(bar: Bar, *, exchange_timezones: dict, exchange_timezone: str | None) -> None`
- 所属：`qts.backtest.inputs.BacktestInputBuilder`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `record exchange timezone` 行为。
- 直接原始调用：`exchange_timezones.setdefault`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.inputs.BacktestInputBuilder._iter_root_bars`

#### `qts.backtest.inputs.BacktestInputBuilder._exchange_timezone_for`

- 位置：`backend/src/qts/backtest/inputs.py:203-208`
- 类型：`staticmethod`
- 签名：`def _exchange_timezone_for(dataset: HistoricalDataset) -> str | None`
- 所属：`qts.backtest.inputs.BacktestInputBuilder`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `exchange timezone for` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.inputs.BacktestInputBuilder._stream_configured_bars`

#### `qts.backtest.inputs.BacktestInputBuilder._instrument_registry_for`

- 位置：`backend/src/qts/backtest/inputs.py:210-261`
- 类型：`method`
- 签名：`def _instrument_registry_for(self, catalog: HistoricalCatalog, *, roll_registry: FutureRollRegistry | None) -> InstrumentRegistry`
- 所属：`qts.backtest.inputs.BacktestInputBuilder`
- 作用：未写 docstring；静态推断为所属类上的 `instrument registry for` 行为。
- 直接原始调用：`registry.register` x3, `self._instrument_for` x3, `Decimal` x2, `InstrumentRegistry`, `RuntimeError`, `chain.instrument_id_for_symbol`, `roll_registry.continuous_instrument_id`, `self._config.instrument_ids.items`, `set`
- 已解析到仓库内部的调用：`qts.backtest.inputs.BacktestInputBuilder._instrument_for`, `qts.registry.instrument_registry.InstrumentRegistry`
- 被以下仓库内部符号调用：`qts.backtest.inputs.BacktestInputBuilder.build`

#### `qts.backtest.inputs.BacktestInputBuilder._instrument_for`

- 位置：`backend/src/qts/backtest/inputs.py:264-286`
- 类型：`staticmethod`
- 签名：`def _instrument_for(instrument_id: InstrumentId, *, exchange: str, currency: str, tick_size: Decimal, multiplier: Decimal, calendar_id: str, asset_class: AssetClass = AssetClass.EQUITY) -> Instrument`
- 所属：`qts.backtest.inputs.BacktestInputBuilder`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `instrument for` 行为。
- 直接原始调用：`ContractSpec`, `Decimal`, `Instrument`
- 已解析到仓库内部的调用：`qts.domain.instruments.contract_spec.ContractSpec`, `qts.domain.instruments.instrument.Instrument`
- 被以下仓库内部符号调用：`qts.backtest.inputs.BacktestInputBuilder._instrument_registry_for`

#### `qts.backtest.inputs.BacktestInputBuilder._dataset_metadata`

- 位置：`backend/src/qts/backtest/inputs.py:288-308`
- 类型：`method`
- 签名：`def _dataset_metadata(self, catalog: HistoricalCatalog) -> tuple`
- 所属：`qts.backtest.inputs.BacktestInputBuilder`
- 作用：未写 docstring；静态推断为所属类上的 `dataset metadata` 行为。
- 直接原始调用：`DatasetMetadata`, `self._config.end.isoformat`, `self._config.start.isoformat`, `self._dataset_instrument_id`, `str`, `tuple`
- 已解析到仓库内部的调用：`qts.backtest.inputs.BacktestInputBuilder._dataset_instrument_id`, `qts.data.provenance.DatasetMetadata`
- 被以下仓库内部符号调用：`qts.backtest.inputs.BacktestInputBuilder.build`

#### `qts.backtest.inputs.BacktestInputBuilder._dataset_instrument_id`

- 位置：`backend/src/qts/backtest/inputs.py:311-314`
- 类型：`staticmethod`
- 签名：`def _dataset_instrument_id(root: str, dataset: HistoricalDataset) -> InstrumentId`
- 所属：`qts.backtest.inputs.BacktestInputBuilder`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `dataset instrument id` 行为。
- 直接原始调用：`InstrumentId` x2
- 已解析到仓库内部的调用：`qts.core.ids.InstrumentId`
- 被以下仓库内部符号调用：`qts.backtest.inputs.BacktestInputBuilder._dataset_metadata`

#### `qts.backtest.inputs.BacktestInputBuilder._contract_multipliers_for`

- 位置：`backend/src/qts/backtest/inputs.py:316-327`
- 类型：`method`
- 签名：`def _contract_multipliers_for(self, catalog: HistoricalCatalog) -> dict`
- 所属：`qts.backtest.inputs.BacktestInputBuilder`
- 作用：未写 docstring；静态推断为所属类上的 `contract multipliers for` 行为。
- 直接原始调用：`chain.instrument_id_for_symbol`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.inputs.BacktestInputBuilder.build`

### `backend/src/qts/backtest/report.py`

模块：`qts.backtest.report`

#### `qts.backtest.report.EquityCurvePoint`

- 位置：`backend/src/qts/backtest/report.py:15-19`
- 类型：`class`
- 签名：`class EquityCurvePoint`
- 装饰器：`dataclass()`
- 作用：One timestamped equity observation.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._equity_point`, `qts.backtest.engine.BacktestEngine.run_streaming`

#### `qts.backtest.report.TradeLedgerEntry`

- 位置：`backend/src/qts/backtest/report.py:23-34`
- 类型：`class`
- 签名：`class TradeLedgerEntry`
- 装饰器：`dataclass()`
- 作用：Auditable row for a simulated fill.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._ledger_rows`

#### `qts.backtest.report._stable_hash`

- 位置：`backend/src/qts/backtest/report.py:37-44`
- 类型：`module_function`
- 签名：`def _stable_hash(payload: Any) -> str`
- 作用：未写 docstring；静态推断为 `stable hash` 函数，具体语义以实现为准。
- 直接原始调用：`encoded.encode`, `hashlib.sha256`, `hashlib.sha256().hexdigest`, `json.dumps`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.report.StreamingBacktestArtifactWriter.finalize`

#### `qts.backtest.report._json_default`

- 位置：`backend/src/qts/backtest/report.py:47-54`
- 类型：`module_function`
- 签名：`def _json_default(value: object) -> object`
- 作用：未写 docstring；静态推断为 `json default` 函数，具体语义以实现为准。
- 直接原始调用：`isinstance` x3, `TypeError`, `hasattr`, `str`, `type`, `value.isoformat`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.report.StreamingEquityMetrics`

- 位置：`backend/src/qts/backtest/report.py:57-90`
- 类型：`class`
- 签名：`class StreamingEquityMetrics`
- 作用：Incremental metrics for a streamed equity curve.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.report.StreamingBacktestArtifactWriter.__init__`

#### `qts.backtest.report.StreamingEquityMetrics.__init__`

- 位置：`backend/src/qts/backtest/report.py:60-65`
- 类型：`method`
- 签名：`def __init__(self) -> None`
- 所属：`qts.backtest.report.StreamingEquityMetrics`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：`Decimal`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.report.StreamingEquityMetrics.update`

- 位置：`backend/src/qts/backtest/report.py:67-81`
- 类型：`method`
- 签名：`def update(self, equity: Decimal) -> None`
- 所属：`qts.backtest.report.StreamingEquityMetrics`
- 作用：未写 docstring；静态推断为所属类上的 `update` 行为。
- 直接原始调用：`Decimal` x2, `ValueError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.report.StreamingEquityMetrics.to_payload`

- 位置：`backend/src/qts/backtest/report.py:83-90`
- 类型：`method`
- 签名：`def to_payload(self) -> dict`
- 所属：`qts.backtest.report.StreamingEquityMetrics`
- 作用：未写 docstring；静态推断为转换或序列化为指定目标表示（名称：to payload）。
- 直接原始调用：`ValueError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.report.StreamingBacktestArtifacts`

- 位置：`backend/src/qts/backtest/report.py:94-100`
- 类型：`class`
- 签名：`class StreamingBacktestArtifacts`
- 装饰器：`dataclass()`
- 作用：Final paths and row counts for streamed backtest artifacts.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.report.StreamingBacktestArtifactWriter.finalize`

#### `qts.backtest.report._NdjsonArtifact`

- 位置：`backend/src/qts/backtest/report.py:103-129`
- 类型：`class`
- 签名：`class _NdjsonArtifact`
- 作用：未写 docstring；静态推断为定义 Ndjson Artifact 概念或数据结构。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.report.StreamingBacktestArtifactWriter.__init__`

#### `qts.backtest.report._NdjsonArtifact.__init__`

- 位置：`backend/src/qts/backtest/report.py:104-108`
- 类型：`method`
- 签名：`def __init__(self, path: Path) -> None`
- 所属：`qts.backtest.report._NdjsonArtifact`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：`hashlib.sha256`, `path.open`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.report._NdjsonArtifact.write`

- 位置：`backend/src/qts/backtest/report.py:110-122`
- 类型：`method`
- 签名：`def write(self, payload: dict) -> None`
- 所属：`qts.backtest.report._NdjsonArtifact`
- 作用：未写 docstring；静态推断为写入数据（名称：write）。
- 直接原始调用：`json.dumps`, `line.encode`, `self._handle.write`, `self._hasher.update`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.report._NdjsonArtifact.close`

- 位置：`backend/src/qts/backtest/report.py:124-125`
- 类型：`method`
- 签名：`def close(self) -> None`
- 所属：`qts.backtest.report._NdjsonArtifact`
- 作用：未写 docstring；静态推断为关闭资源或头寸（名称：close）。
- 直接原始调用：`self._handle.close`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.report._NdjsonArtifact.content_hash`

- 位置：`backend/src/qts/backtest/report.py:128-129`
- 类型：`property`
- 签名：`def content_hash(self) -> str`
- 所属：`qts.backtest.report._NdjsonArtifact`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为所属类上的 `content hash` 行为。
- 直接原始调用：`self._hasher.hexdigest`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.report.StreamingBacktestArtifactWriter`

- 位置：`backend/src/qts/backtest/report.py:132-257`
- 类型：`class`
- 签名：`class StreamingBacktestArtifactWriter`
- 作用：Write large backtest outputs as line-delimited artifacts.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine.run_streaming`

#### `qts.backtest.report.StreamingBacktestArtifactWriter.__init__`

- 位置：`backend/src/qts/backtest/report.py:137-144`
- 类型：`method`
- 签名：`def __init__(self, output_dir: Path) -> None`
- 所属：`qts.backtest.report.StreamingBacktestArtifactWriter`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：`StreamingEquityMetrics`, `_NdjsonArtifact`, `self._output_dir.mkdir`
- 已解析到仓库内部的调用：`qts.backtest.report.StreamingEquityMetrics`, `qts.backtest.report._NdjsonArtifact`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.report.StreamingBacktestArtifactWriter.write_order`

- 位置：`backend/src/qts/backtest/report.py:146-147`
- 类型：`method`
- 签名：`def write_order(self, payload: dict) -> None`
- 所属：`qts.backtest.report.StreamingBacktestArtifactWriter`
- 作用：未写 docstring；静态推断为写入数据（名称：write order）。
- 直接原始调用：`self._artifacts.write`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.report.StreamingBacktestArtifactWriter.write_fill`

- 位置：`backend/src/qts/backtest/report.py:149-150`
- 类型：`method`
- 签名：`def write_fill(self, payload: dict) -> None`
- 所属：`qts.backtest.report.StreamingBacktestArtifactWriter`
- 作用：未写 docstring；静态推断为写入数据（名称：write fill）。
- 直接原始调用：`self._artifacts.write`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.report.StreamingBacktestArtifactWriter.write_trade_ledger`

- 位置：`backend/src/qts/backtest/report.py:152-165`
- 类型：`method`
- 签名：`def write_trade_ledger(self, row: TradeLedgerEntry) -> None`
- 所属：`qts.backtest.report.StreamingBacktestArtifactWriter`
- 作用：未写 docstring；静态推断为写入数据（名称：write trade ledger）。
- 直接原始调用：`self._artifacts.write`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.report.StreamingBacktestArtifactWriter.write_equity_point`

- 位置：`backend/src/qts/backtest/report.py:167-169`
- 类型：`method`
- 签名：`def write_equity_point(self, point: EquityCurvePoint) -> None`
- 所属：`qts.backtest.report.StreamingBacktestArtifactWriter`
- 作用：未写 docstring；静态推断为写入数据（名称：write equity point）。
- 直接原始调用：`self._artifacts.write`, `self._equity_metrics.update`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.report.StreamingBacktestArtifactWriter.finalize`

- 位置：`backend/src/qts/backtest/report.py:171-257`
- 类型：`method`
- 签名：`def finalize(self, *, config_hash: str, dataset_metadata: tuple, cost_model: dict, processed_bars: int, warmup_bars: int, trading_bars: int, final_cash: Decimal, strategy_version: str) -> tuple`
- 所属：`qts.backtest.report.StreamingBacktestArtifactWriter`
- 作用：未写 docstring；静态推断为所属类上的 `finalize` 行为。
- 直接原始调用：`self._artifacts.items` x3, `str` x2, `StreamingBacktestArtifacts`, `_stable_hash`, `artifact.close`, `artifact.path.replace`, `json.dumps`, `manifest_path.write_text`, `report_hash.removeprefix`, `self._artifacts.values`, `self._equity_metrics.to_payload`
- 已解析到仓库内部的调用：`qts.backtest.report.StreamingBacktestArtifacts`, `qts.backtest.report._stable_hash`
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/backtest/runner.py`

模块：`qts.backtest.runner`

#### `qts.backtest.runner.BacktestRun`

- 位置：`backend/src/qts/backtest/runner.py:23-38`
- 类型：`class`
- 签名：`class BacktestRun`
- 装饰器：`dataclass()`
- 作用：Output of a backtest runner invocation.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.runner.run_backtest`

#### `qts.backtest.runner.BacktestRun.processed_bars`

- 位置：`backend/src/qts/backtest/runner.py:33-34`
- 类型：`property`
- 签名：`def processed_bars(self) -> int`
- 所属：`qts.backtest.runner.BacktestRun`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为所属类上的 `processed bars` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.runner.BacktestRun.report_hash`

- 位置：`backend/src/qts/backtest/runner.py:37-38`
- 类型：`property`
- 签名：`def report_hash(self) -> str`
- 所属：`qts.backtest.runner.BacktestRun`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为所属类上的 `report hash` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.backtest.runner.run_backtest`

- 位置：`backend/src/qts/backtest/runner.py:41-81`
- 类型：`module_function`
- 签名：`def run_backtest(config_path: Path, *, output_dir: Path = Path()) -> BacktestRun`
- 作用：Run a backtest and write partitioned streaming artifacts.
- 直接原始调用：`BacktestEngine.from_config`, `BacktestEngine.from_config().run_streaming`, `BacktestInputBuilder`, `BacktestInputBuilder().build`, `BacktestRun`, `BacktestRunConfig.from_yaml`, `HistoricalCatalog.load`, `Path`, `_catalog_load_config`, `_load_strategy`, `_streaming_summary_payload`, `json.dumps`, `result.artifact_paths.items`, `summary_path.write_text`
- 已解析到仓库内部的调用：`qts.backtest.config.BacktestRunConfig.from_yaml`, `qts.backtest.engine.BacktestEngine.from_config`, `qts.backtest.engine.BacktestEngine.run_streaming`, `qts.backtest.inputs.BacktestInputBuilder`, `qts.backtest.runner.BacktestRun`, `qts.backtest.runner._catalog_load_config`, `qts.backtest.runner._load_strategy`, `qts.backtest.runner._streaming_summary_payload`, `qts.data.historical.catalog.HistoricalCatalog.load`
- 被以下仓库内部符号调用：`scripts.run_backtest.main`

#### `qts.backtest.runner._catalog_load_config`

- 位置：`backend/src/qts/backtest/runner.py:84-102`
- 类型：`module_function`
- 签名：`def _catalog_load_config(config: BacktestRunConfig) -> HistoricalCatalogLoadConfig`
- 作用：未写 docstring；静态推断为 `catalog load config` 函数，具体语义以实现为准。
- 直接原始调用：`RuntimeError` x2, `HistoricalCatalogLoadConfig.from_historical_data_config`, `HistoricalCatalogLoadConfig.from_legacy_root`
- 已解析到仓库内部的调用：`qts.data.historical.catalog.HistoricalCatalogLoadConfig.from_historical_data_config`, `qts.data.historical.catalog.HistoricalCatalogLoadConfig.from_legacy_root`
- 被以下仓库内部符号调用：`qts.backtest.runner.run_backtest`

#### `qts.backtest.runner._load_strategy`

- 位置：`backend/src/qts/backtest/runner.py:105-123`
- 类型：`module_function`
- 签名：`def _load_strategy(strategy_class: str, params: dict) -> Strategy`
- 作用：未写 docstring；静态推断为 `load strategy` 函数，具体语义以实现为准。
- 直接原始调用：`Path`, `Path().with_suffix`, `ValueError`, `cast`, `getattr`, `importlib.import_module`, `importlib.util.module_from_spec`, `importlib.util.spec_from_file_location`, `module_name.split`, `module_path.exists`, `spec.loader.exec_module`, `strategy_class.partition`, `strategy_class.rpartition`, `strategy_type`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.runner.run_backtest`

#### `qts.backtest.runner._streaming_summary_payload`

- 位置：`backend/src/qts/backtest/runner.py:126-146`
- 类型：`module_function`
- 签名：`def _streaming_summary_payload(result: BacktestStreamResult, *, manifest_path: Path, dataset_stats: dict) -> dict`
- 作用：未写 docstring；静态推断为 `streaming summary payload` 函数，具体语义以实现为准。
- 直接原始调用：`dataset_stats.values` x4, `sum` x4, `item.get`, `str`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.runner.run_backtest`

### `backend/src/qts/config/__init__.py`

模块：`qts.config`

无类或函数定义。

### `backend/src/qts/config/ibkr.py`

模块：`qts.config.ibkr`

#### `qts.config.ibkr.IbkrConnectionConfig`

- 位置：`backend/src/qts/config/ibkr.py:13-26`
- 类型：`class`
- 签名：`class IbkrConnectionConfig`
- 装饰器：`dataclass()`
- 作用：IBKR connection settings for one boundary.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.config.ibkr.IbkrConnectionConfig.__post_init__`

- 位置：`backend/src/qts/config/ibkr.py:20-26`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.config.ibkr.IbkrConnectionConfig`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x3, `self.host.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.config.ibkr.IbkrOrderExecutionConfig`

- 位置：`backend/src/qts/config/ibkr.py:30-41`
- 类型：`class`
- 签名：`class IbkrOrderExecutionConfig(IbkrConnectionConfig)`
- 继承/基类：`IbkrConnectionConfig`
- 装饰器：`dataclass()`
- 作用：IBKR order execution settings.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.config.ibkr.IbkrOrderExecutionConfig.__post_init__`

- 位置：`backend/src/qts/config/ibkr.py:36-41`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.config.ibkr.IbkrOrderExecutionConfig`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x2, `IbkrConnectionConfig.__post_init__`, `self.account_id.strip`, `self.risk_profile.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.config.ibkr.IbkrSecretRefs`

- 位置：`backend/src/qts/config/ibkr.py:45-55`
- 类型：`class`
- 签名：`class IbkrSecretRefs`
- 装饰器：`dataclass()`
- 作用：Environment variable names for IBKR credentials.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.config.ibkr.IbkrSecretRefs.__post_init__`

- 位置：`backend/src/qts/config/ibkr.py:51-55`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.config.ibkr.IbkrSecretRefs`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x2, `self.password_env.strip`, `self.username_env.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.config.ibkr.IbkrEnvironmentConfig`

- 位置：`backend/src/qts/config/ibkr.py:59-65`
- 类型：`class`
- 签名：`class IbkrEnvironmentConfig`
- 装饰器：`dataclass()`
- 作用：IBKR runtime configuration split by external boundary.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.config.ibkr.validate_ibkr_environment`

- 位置：`backend/src/qts/config/ibkr.py:68-97`
- 类型：`module_function`
- 签名：`def validate_ibkr_environment(config: IbkrEnvironmentConfig, *, paper_client_ids: Set[int] | None = None) -> None`
- 作用：Validate paper/live separation without exposing secret values.
- 直接原始调用：`errors.append` x5, `_contains_paper_reference` x2, `'; '.join`, `ValueError`, `config.order_execution.account_id.upper`, `config.order_execution.account_id.upper().startswith`, `config.order_execution.risk_profile.lower`, `live_client_ids.intersection`, `set`
- 已解析到仓库内部的调用：`qts.config.ibkr._contains_paper_reference`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.config.ibkr._contains_paper_reference`

- 位置：`backend/src/qts/config/ibkr.py:100-101`
- 类型：`module_function`
- 签名：`def _contains_paper_reference(secret_env_name: str) -> bool`
- 作用：未写 docstring；静态推断为 `contains paper reference` 函数，具体语义以实现为准。
- 直接原始调用：`secret_env_name.upper`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.config.ibkr.validate_ibkr_environment`

### `backend/src/qts/core/__init__.py`

模块：`qts.core`

无类或函数定义。

### `backend/src/qts/core/ids.py`

模块：`qts.core.ids`

#### `qts.core.ids._StringId`

- 位置：`backend/src/qts/core/ids.py:9-22`
- 类型：`class`
- 签名：`class _StringId`
- 装饰器：`dataclass()`
- 作用：Base class for typed string identifiers.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.core.ids._StringId.__post_init__`

- 位置：`backend/src/qts/core/ids.py:14-19`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.core.ids._StringId`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`TypeError`, `ValueError`, `isinstance`, `self.value.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.core.ids._StringId.__str__`

- 位置：`backend/src/qts/core/ids.py:21-22`
- 类型：`method`
- 签名：`def __str__(self) -> str`
- 所属：`qts.core.ids._StringId`
- 作用：未写 docstring；实现 Python 协议方法 `__str__`。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.core.ids.AccountId`

- 位置：`backend/src/qts/core/ids.py:25-26`
- 类型：`class`
- 签名：`class AccountId(_StringId)`
- 继承/基类：`_StringId`
- 作用：Stable internal account identifier.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill`

#### `qts.core.ids.StrategyId`

- 位置：`backend/src/qts/core/ids.py:29-30`
- 类型：`class`
- 签名：`class StrategyId(_StringId)`
- 继承/基类：`_StringId`
- 作用：Stable internal strategy identifier.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill`

#### `qts.core.ids.InstrumentId`

- 位置：`backend/src/qts/core/ids.py:33-34`
- 类型：`class`
- 签名：`class InstrumentId(_StringId)`
- 继承/基类：`_StringId`
- 作用：Stable internal instrument identifier.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.config.BacktestRunConfig.__post_init__`, `qts.backtest.config.BacktestRunConfig.from_yaml`, `qts.backtest.inputs.BacktestInputBuilder._dataset_instrument_id`, `qts.data.historical.catalog.HistoricalCatalogLoadConfig.__post_init__`, `qts.data.historical.chains.HistoricalChain.instrument_id_for_symbol`, `qts.data.stores.parquet_store.ParquetMarketDataStore._bar_from_json`, `qts.registry.future_roll.FutureRollRegistry.register_root`, `scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill`, `scripts.run_load.main`

#### `qts.core.ids.OrderId`

- 位置：`backend/src/qts/core/ids.py:37-38`
- 类型：`class`
- 签名：`class OrderId(_StringId)`
- 继承/基类：`_StringId`
- 作用：Stable internal order identifier.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._process_order_delta`, `scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill`

#### `qts.core.ids.BrokerId`

- 位置：`backend/src/qts/core/ids.py:41-42`
- 类型：`class`
- 签名：`class BrokerId(_StringId)`
- 继承/基类：`_StringId`
- 作用：Stable internal broker identifier.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill`

#### `qts.core.ids.EventId`

- 位置：`backend/src/qts/core/ids.py:45-46`
- 类型：`class`
- 签名：`class EventId(_StringId)`
- 继承/基类：`_StringId`
- 作用：Stable internal event identifier.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.event_store.FileEventStore._event_from_json`

#### `qts.core.ids.BacktestRunId`

- 位置：`backend/src/qts/core/ids.py:49-50`
- 类型：`class`
- 签名：`class BacktestRunId(_StringId)`
- 继承/基类：`_StringId`
- 作用：Stable identifier for a backtest run.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine.run_streaming`

#### `qts.core.ids.CorrelationId`

- 位置：`backend/src/qts/core/ids.py:53-54`
- 类型：`class`
- 签名：`class CorrelationId(_StringId)`
- 继承/基类：`_StringId`
- 作用：Identifier grouping events in one business workflow.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.event_store.FileEventStore._event_from_json`

#### `qts.core.ids.CausationId`

- 位置：`backend/src/qts/core/ids.py:57-58`
- 类型：`class`
- 签名：`class CausationId(_StringId)`
- 继承/基类：`_StringId`
- 作用：Identifier linking an event to the event that caused it.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.event_store.FileEventStore._event_from_json`

### `backend/src/qts/core/time.py`

模块：`qts.core.time`

#### `qts.core.time.require_aware_datetime`

- 位置：`backend/src/qts/core/time.py:10-14`
- 类型：`module_function`
- 签名：`def require_aware_datetime(value: datetime, *, name: str) -> None`
- 作用：Validate that a datetime has an effective timezone.
- 直接原始调用：`ValueError`, `value.utcoffset`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.core.time.TimeInterval.__post_init__`, `qts.core.time.TimeInterval.contains`, `qts.core.time.to_exchange_time`, `qts.data.provenance.DatasetMetadata.__post_init__`, `qts.domain.events.event.BaseEvent.__post_init__`, `qts.domain.events.metadata.EventMetadata.__post_init__`, `qts.domain.market_data.bar.Quote.__post_init__`, `qts.domain.market_data.bar.Tick.__post_init__`, `qts.domain.risk.request.OrderRiskRequest.__post_init__`

#### `qts.core.time.to_exchange_time`

- 位置：`backend/src/qts/core/time.py:17-24`
- 类型：`module_function`
- 签名：`def to_exchange_time(value: datetime, exchange_timezone: str | tzinfo) -> datetime`
- 作用：Convert a timestamp representation into an exchange timezone.
- 直接原始调用：`ZoneInfo`, `isinstance`, `require_aware_datetime`, `value.astimezone`
- 已解析到仓库内部的调用：`qts.core.time.require_aware_datetime`
- 被以下仓库内部符号调用：`qts.data.bars.alignment.clock_bucket_for`, `qts.data.sessions.window.RegularSessionWindow.session_date_for_timestamp`

#### `qts.core.time.TimeInterval`

- 位置：`backend/src/qts/core/time.py:28-46`
- 类型：`class`
- 签名：`class TimeInterval`
- 装饰器：`dataclass()`
- 作用：A half-open time interval with `[start, end)` membership.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.bars.aggregator.BarAggregator._new_state_for`, `qts.data.bars.alignment.clock_bucket_for`, `qts.domain.market_data.bar.Bar.__post_init__`, `qts.domain.market_data.bar.Bar.interval`, `qts.registry.providers.comex_gold_calendar_provider.ComexGoldCalendarProvider.session_for`, `qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider.session_for`

#### `qts.core.time.TimeInterval.__post_init__`

- 位置：`backend/src/qts/core/time.py:34-38`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.core.time.TimeInterval`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`require_aware_datetime` x2, `ValueError`
- 已解析到仓库内部的调用：`qts.core.time.require_aware_datetime`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.core.time.TimeInterval.duration`

- 位置：`backend/src/qts/core/time.py:41-42`
- 类型：`property`
- 签名：`def duration(self) -> timedelta`
- 所属：`qts.core.time.TimeInterval`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为所属类上的 `duration` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.core.time.TimeInterval.contains`

- 位置：`backend/src/qts/core/time.py:44-46`
- 类型：`method`
- 签名：`def contains(self, value: datetime) -> bool`
- 所属：`qts.core.time.TimeInterval`
- 作用：未写 docstring；静态推断为所属类上的 `contains` 行为。
- 直接原始调用：`require_aware_datetime`
- 已解析到仓库内部的调用：`qts.core.time.require_aware_datetime`
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/data/__init__.py`

模块：`qts.data`

无类或函数定义。

### `backend/src/qts/data/adapters/__init__.py`

模块：`qts.data.adapters`

无类或函数定义。

### `backend/src/qts/data/adapters/ibkr_market_data.py`

模块：`qts.data.adapters.ibkr_market_data`

#### `qts.data.adapters.ibkr_market_data.IbkrMarketDataConnection`

- 位置：`backend/src/qts/data/adapters/ibkr_market_data.py:15-31`
- 类型：`class`
- 签名：`class IbkrMarketDataConnection`
- 装饰器：`dataclass()`
- 作用：IBKR market data connection settings.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.adapters.ibkr_market_data.IbkrMarketDataConnection.__post_init__`

- 位置：`backend/src/qts/data/adapters/ibkr_market_data.py:23-31`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.data.adapters.ibkr_market_data.IbkrMarketDataConnection`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x4, `self.host.strip`, `self.source_id.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.adapters.ibkr_market_data.IbkrMarketDataSubscription`

- 位置：`backend/src/qts/data/adapters/ibkr_market_data.py:35-40`
- 类型：`class`
- 签名：`class IbkrMarketDataSubscription`
- 装饰器：`dataclass()`
- 作用：IBKR market data subscription request at the adapter boundary.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter.subscription_for`

#### `qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter`

- 位置：`backend/src/qts/data/adapters/ibkr_market_data.py:43-131`
- 类型：`class`
- 签名：`class IbkrMarketDataAdapter`
- 作用：Normalizes IBKR market data without owning order execution.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter.__init__`

- 位置：`backend/src/qts/data/adapters/ibkr_market_data.py:46-53`
- 类型：`method`
- 签名：`def __init__(self, *, connection: IbkrMarketDataConnection, symbol_mapping: BrokerSymbolMapping) -> None`
- 所属：`qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter.subscription_for`

- 位置：`backend/src/qts/data/adapters/ibkr_market_data.py:55-60`
- 类型：`method`
- 签名：`def subscription_for(self, instrument_id: InstrumentId) -> IbkrMarketDataSubscription`
- 所属：`qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter`
- 作用：未写 docstring；静态推断为所属类上的 `subscription for` 行为。
- 直接原始调用：`IbkrMarketDataSubscription`, `self._symbol_mapping.to_broker_symbol`
- 已解析到仓库内部的调用：`qts.data.adapters.ibkr_market_data.IbkrMarketDataSubscription`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter.normalize_tick`

- 位置：`backend/src/qts/data/adapters/ibkr_market_data.py:62-75`
- 类型：`method`
- 签名：`def normalize_tick(self, *, broker_symbol: str, time: datetime, price: Decimal, size: Decimal = Decimal()) -> Tick`
- 所属：`qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter`
- 作用：未写 docstring；静态推断为所属类上的 `normalize tick` 行为。
- 直接原始调用：`Tick`, `self._symbol_mapping.to_instrument_id`
- 已解析到仓库内部的调用：`qts.domain.market_data.bar.Tick`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter.normalize_quote`

- 位置：`backend/src/qts/data/adapters/ibkr_market_data.py:77-94`
- 类型：`method`
- 签名：`def normalize_quote(self, *, broker_symbol: str, time: datetime, bid_price: Decimal, ask_price: Decimal, bid_size: Decimal = Decimal(), ask_size: Decimal = Decimal()) -> Quote`
- 所属：`qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter`
- 作用：未写 docstring；静态推断为所属类上的 `normalize quote` 行为。
- 直接原始调用：`Quote`, `self._symbol_mapping.to_instrument_id`
- 已解析到仓库内部的调用：`qts.domain.market_data.bar.Quote`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter.normalize_bar`

- 位置：`backend/src/qts/data/adapters/ibkr_market_data.py:96-131`
- 类型：`method`
- 签名：`def normalize_bar(self, *, broker_symbol: str, start_time: datetime, end_time: datetime, timeframe: str, session_id: str, open: Decimal, high: Decimal, low: Decimal, close: Decimal, volume: Decimal = Decimal(), vwap: Decimal | None = None, open_interest: Decimal | None = None, trade_count: int | None = None, is_complete: bool = False, is_partial: bool = False) -> Bar`
- 所属：`qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter`
- 作用：未写 docstring；静态推断为所属类上的 `normalize bar` 行为。
- 直接原始调用：`Bar`, `self._symbol_mapping.to_instrument_id`
- 已解析到仓库内部的调用：`qts.domain.market_data.bar.Bar`
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/data/bars/__init__.py`

模块：`qts.data.bars`

无类或函数定义。

### `backend/src/qts/data/bars/aggregator.py`

模块：`qts.data.bars.aggregator`

#### `qts.data.bars.aggregator.AggregationState`

- 位置：`backend/src/qts/data/bars/aggregator.py:18-28`
- 类型：`class`
- 签名：`class AggregationState`
- 装饰器：`dataclass()`
- 作用：Current in-progress aggregation bucket.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.bars.aggregator.BarAggregator._new_state_for`, `qts.data.bars.aggregator.BarAggregator.update`

#### `qts.data.bars.aggregator.AggregationState.aggregate_end`

- 位置：`backend/src/qts/data/bars/aggregator.py:27-28`
- 类型：`property`
- 签名：`def aggregate_end(self) -> datetime`
- 所属：`qts.data.bars.aggregator.AggregationState`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为所属类上的 `aggregate end` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.bars.aggregator.AggregationResult`

- 位置：`backend/src/qts/data/bars/aggregator.py:32-36`
- 类型：`class`
- 签名：`class AggregationResult`
- 装饰器：`dataclass()`
- 作用：Result returned by one incremental aggregator update.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.bars.aggregator.BarAggregator.finish`, `qts.data.bars.aggregator.BarAggregator.update`

#### `qts.data.bars.aggregator.BarAggregator`

- 位置：`backend/src/qts/data/bars/aggregator.py:39-104`
- 类型：`class`
- 签名：`class BarAggregator`
- 作用：Stateful incremental bar aggregator for one ordered bar stream.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.bars.aggregator.aggregate_bars`, `qts.runtime.actors.market_data_actor.MarketDataActor._aggregator_for`, `qts.runtime.actors.market_data_actor.MarketDataActor._logical_aggregator_for`

#### `qts.data.bars.aggregator.BarAggregator.__init__`

- 位置：`backend/src/qts/data/bars/aggregator.py:42-54`
- 类型：`method`
- 签名：`def __init__(self, *, target_timeframe: Timeframe, exchange_timezone: str | tzinfo, session: MarketSession | None = None) -> None`
- 所属：`qts.data.bars.aggregator.BarAggregator`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：`ValueError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.bars.aggregator.BarAggregator.update`

- 位置：`backend/src/qts/data/bars/aggregator.py:56-83`
- 类型：`method`
- 签名：`def update(self, bar: Bar) -> AggregationResult`
- 所属：`qts.data.bars.aggregator.BarAggregator`
- 作用：Add a lower-timeframe bar and return any completed aggregate bars.
- 直接原始调用：`AggregationResult` x2, `_aggregate_state` x2, `completed.append` x2, `AggregationState`, `_bar_inside_session`, `_same_stream_bucket`, `self._new_state_for`, `tuple`
- 已解析到仓库内部的调用：`qts.data.bars.aggregator.AggregationResult`, `qts.data.bars.aggregator.AggregationState`, `qts.data.bars.aggregator.BarAggregator._new_state_for`, `qts.data.bars.aggregator._aggregate_state`, `qts.data.bars.aggregator._bar_inside_session`, `qts.data.bars.aggregator._same_stream_bucket`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.bars.aggregator.BarAggregator.finish`

- 位置：`backend/src/qts/data/bars/aggregator.py:85-92`
- 类型：`method`
- 签名：`def finish(self) -> AggregationResult`
- 所属：`qts.data.bars.aggregator.BarAggregator`
- 作用：Flush the current bucket as a partial aggregate when present.
- 直接原始调用：`AggregationResult` x2, `_aggregate_state`
- 已解析到仓库内部的调用：`qts.data.bars.aggregator.AggregationResult`, `qts.data.bars.aggregator._aggregate_state`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.bars.aggregator.BarAggregator._new_state_for`

- 位置：`backend/src/qts/data/bars/aggregator.py:94-104`
- 类型：`method`
- 签名：`def _new_state_for(self, bar: Bar) -> AggregationState`
- 所属：`qts.data.bars.aggregator.BarAggregator`
- 作用：未写 docstring；静态推断为所属类上的 `new state for` 行为。
- 直接原始调用：`AggregationState`, `TimeInterval`, `clock_bucket_for`
- 已解析到仓库内部的调用：`qts.core.time.TimeInterval`, `qts.data.bars.aggregator.AggregationState`, `qts.data.bars.alignment.clock_bucket_for`
- 被以下仓库内部符号调用：`qts.data.bars.aggregator.BarAggregator.update`

#### `qts.data.bars.aggregator.aggregate_bars`

- 位置：`backend/src/qts/data/bars/aggregator.py:107-133`
- 类型：`module_function`
- 签名：`def aggregate_bars(bars: Iterable, *, target_timeframe: Timeframe, exchange_timezone: str | tzinfo, session: MarketSession | None = None) -> list`
- 作用：Aggregate bars into a higher clock-aligned timeframe.
- 直接原始调用：`aggregated.extend` x2, `sorted` x2, `BarAggregator`, `aggregator.finish`, `aggregator.update`, `aggregators.setdefault`, `aggregators.values`
- 已解析到仓库内部的调用：`qts.data.bars.aggregator.BarAggregator`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.bars.aggregator._bar_inside_session`

- 位置：`backend/src/qts/data/bars/aggregator.py:136-137`
- 类型：`module_function`
- 签名：`def _bar_inside_session(bar: Bar, session: MarketSession) -> bool`
- 作用：未写 docstring；静态推断为 `bar inside session` 函数，具体语义以实现为准。
- 直接原始调用：`session.interval.contains`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.bars.aggregator.BarAggregator.update`

#### `qts.data.bars.aggregator._same_stream_bucket`

- 位置：`backend/src/qts/data/bars/aggregator.py:140-145`
- 类型：`module_function`
- 签名：`def _same_stream_bucket(left: AggregationState, right: AggregationState) -> bool`
- 作用：未写 docstring；静态推断为 `same stream bucket` 函数，具体语义以实现为准。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.bars.aggregator.BarAggregator.update`

#### `qts.data.bars.aggregator._aggregate_state`

- 位置：`backend/src/qts/data/bars/aggregator.py:148-185`
- 类型：`module_function`
- 签名：`def _aggregate_state(state: AggregationState) -> Bar`
- 作用：未写 docstring；静态推断为 `aggregate state` 函数，具体语义以实现为准。
- 直接原始调用：`ValueError` x3, `Bar`, `Decimal`, `_aggregate_vwap`, `_last_open_interest`, `_sum_trade_count`, `all`, `max`, `min`, `str`, `sum`
- 已解析到仓库内部的调用：`qts.data.bars.aggregator._aggregate_vwap`, `qts.data.bars.aggregator._last_open_interest`, `qts.data.bars.aggregator._sum_trade_count`, `qts.domain.market_data.bar.Bar`
- 被以下仓库内部符号调用：`qts.data.bars.aggregator.BarAggregator.finish`, `qts.data.bars.aggregator.BarAggregator.update`

#### `qts.data.bars.aggregator._aggregate_vwap`

- 位置：`backend/src/qts/data/bars/aggregator.py:188-194`
- 类型：`module_function`
- 签名：`def _aggregate_vwap(bars: tuple, total_volume: Decimal) -> Decimal | None`
- 作用：未写 docstring；静态推断为 `aggregate vwap` 函数，具体语义以实现为准。
- 直接原始调用：`Decimal` x3, `sum`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.bars.aggregator._aggregate_state`

#### `qts.data.bars.aggregator._last_open_interest`

- 位置：`backend/src/qts/data/bars/aggregator.py:197-201`
- 类型：`module_function`
- 签名：`def _last_open_interest(bars: tuple) -> Decimal | None`
- 作用：未写 docstring；静态推断为 `last open interest` 函数，具体语义以实现为准。
- 直接原始调用：`reversed`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.bars.aggregator._aggregate_state`

#### `qts.data.bars.aggregator._sum_trade_count`

- 位置：`backend/src/qts/data/bars/aggregator.py:204-208`
- 类型：`module_function`
- 签名：`def _sum_trade_count(bars: tuple) -> int | None`
- 作用：未写 docstring；静态推断为 `sum trade count` 函数，具体语义以实现为准。
- 直接原始调用：`sum`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.bars.aggregator._aggregate_state`

### `backend/src/qts/data/bars/alignment.py`

模块：`qts.data.bars.alignment`

#### `qts.data.bars.alignment.clock_bucket_for`

- 位置：`backend/src/qts/data/bars/alignment.py:11-33`
- 类型：`module_function`
- 签名：`def clock_bucket_for(timestamp: datetime, timeframe: Timeframe, exchange_timezone: str | tzinfo) -> TimeInterval`
- 作用：Return the exchange-clock bucket containing ``timestamp``.
- 直接原始调用：`TimeInterval`, `ValueError`, `_duration_seconds`, `exchange_time.replace`, `int`, `timedelta`, `to_exchange_time`
- 已解析到仓库内部的调用：`qts.core.time.TimeInterval`, `qts.core.time.to_exchange_time`, `qts.data.bars.alignment._duration_seconds`
- 被以下仓库内部符号调用：`qts.data.bars.aggregator.BarAggregator._new_state_for`

#### `qts.data.bars.alignment._duration_seconds`

- 位置：`backend/src/qts/data/bars/alignment.py:36-42`
- 类型：`module_function`
- 签名：`def _duration_seconds(duration: timedelta) -> int`
- 作用：未写 docstring；静态推断为 `duration seconds` 函数，具体语义以实现为准。
- 直接原始调用：`ValueError` x2, `duration.total_seconds`, `int`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.bars.alignment.clock_bucket_for`

### `backend/src/qts/data/bars/builder.py`

模块：`qts.data.bars.builder`

无类或函数定义。

### `backend/src/qts/data/bars/timeframe.py`

模块：`qts.data.bars.timeframe`

#### `qts.data.bars.timeframe.AlignmentMode`

- 位置：`backend/src/qts/data/bars/timeframe.py:10-14`
- 类型：`class`
- 签名：`class AlignmentMode(StrEnum)`
- 继承/基类：`StrEnum`
- 作用：How bars for a timeframe align to time.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.bars.timeframe.Timeframe`

- 位置：`backend/src/qts/data/bars/timeframe.py:29-50`
- 类型：`class`
- 签名：`class Timeframe`
- 装饰器：`dataclass()`
- 作用：Bar timeframe with explicit alignment semantics.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.bars.timeframe.Timeframe.parse`

- 位置：`backend/src/qts/data/bars/timeframe.py:37-47`
- 类型：`classmethod`
- 签名：`def parse(cls, value: str) -> Timeframe`
- 所属：`qts.data.bars.timeframe.Timeframe`
- 装饰器：`classmethod`
- 作用：未写 docstring；静态推断为解析外部表示（名称：parse）。
- 直接原始调用：`cls` x2, `ValueError`, `value.strip`, `value.strip().lower`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.actors.market_data_actor.MarketDataActor.__init__`, `qts.runtime.actors.market_data_actor.MarketDataActor._logical_aggregator_for`

#### `qts.data.bars.timeframe.Timeframe.__str__`

- 位置：`backend/src/qts/data/bars/timeframe.py:49-50`
- 类型：`method`
- 签名：`def __str__(self) -> str`
- 所属：`qts.data.bars.timeframe.Timeframe`
- 作用：未写 docstring；实现 Python 协议方法 `__str__`。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/data/bars/validation.py`

模块：`qts.data.bars.validation`

无类或函数定义。

### `backend/src/qts/data/feeds/__init__.py`

模块：`qts.data.feeds`

无类或函数定义。

### `backend/src/qts/data/feeds/replay_feed.py`

模块：`qts.data.feeds.replay_feed`

#### `qts.data.feeds.replay_feed.ReplayFeed`

- 位置：`backend/src/qts/data/feeds/replay_feed.py:12-31`
- 类型：`class`
- 签名：`class ReplayFeed`
- 作用：Deterministic replay feed over stored bars.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.feeds.replay_feed.ReplayFeed.__init__`

- 位置：`backend/src/qts/data/feeds/replay_feed.py:15-16`
- 类型：`method`
- 签名：`def __init__(self, store: MarketDataStore) -> None`
- 所属：`qts.data.feeds.replay_feed.ReplayFeed`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.feeds.replay_feed.ReplayFeed.events`

- 位置：`backend/src/qts/data/feeds/replay_feed.py:18-31`
- 类型：`method`
- 签名：`def events(self, *, instrument_id: InstrumentId, timeframe: str, start: datetime, end: datetime) -> tuple`
- 所属：`qts.data.feeds.replay_feed.ReplayFeed`
- 作用：未写 docstring；静态推断为所属类上的 `events` 行为。
- 直接原始调用：`self._store.read_bars`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/data/historical/__init__.py`

模块：`qts.data.historical`

无类或函数定义。

### `backend/src/qts/data/historical/catalog.py`

模块：`qts.data.historical.catalog`

#### `qts.data.historical.catalog.HistoricalDataset`

- 位置：`backend/src/qts/data/historical/catalog.py:19-38`
- 类型：`class`
- 签名：`class HistoricalDataset`
- 装饰器：`dataclass()`
- 作用：One local historical dataset entry.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.catalog.HistoricalCatalog.from_historical_data_config`, `qts.data.historical.catalog.HistoricalCatalog.from_legacy_root`

#### `qts.data.historical.catalog.HistoricalDataset.normalize_root`

- 位置：`backend/src/qts/data/historical/catalog.py:34-38`
- 类型：`staticmethod`
- 签名：`def normalize_root(root: str) -> str`
- 所属：`qts.data.historical.catalog.HistoricalDataset`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `normalize root` 行为。
- 直接原始调用：`ValueError`, `root.strip`, `root.strip().upper`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.historical.catalog.HistoricalCatalog`

- 位置：`backend/src/qts/data/historical/catalog.py:42-226`
- 类型：`class`
- 签名：`class HistoricalCatalog`
- 装饰器：`dataclass()`
- 作用：Explicit catalog for a local historical data layout.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.historical.catalog.HistoricalCatalog.load`

- 位置：`backend/src/qts/data/historical/catalog.py:50-76`
- 类型：`classmethod`
- 签名：`def load(cls, config: HistoricalCatalogLoadConfig) -> HistoricalCatalog`
- 所属：`qts.data.historical.catalog.HistoricalCatalog`
- 装饰器：`classmethod`
- 作用：Load a catalog from one cohesive construction config.
- 直接原始调用：`RuntimeError` x2, `HistoricalDataConfig.from_yaml`, `cls._symbol_resolvers_for_load_config`, `cls.from_historical_data_config`, `cls.from_legacy_root`
- 已解析到仓库内部的调用：`qts.data.historical.catalog.HistoricalCatalog._symbol_resolvers_for_load_config`, `qts.data.historical.catalog.HistoricalCatalog.from_historical_data_config`, `qts.data.historical.catalog.HistoricalCatalog.from_legacy_root`, `qts.data.historical.config.HistoricalDataConfig.from_yaml`
- 被以下仓库内部符号调用：`qts.backtest.runner.run_backtest`

#### `qts.data.historical.catalog.HistoricalCatalog.from_legacy_root`

- 位置：`backend/src/qts/data/historical/catalog.py:79-120`
- 类型：`classmethod`
- 签名：`def from_legacy_root(cls, root_path: Path, *, roots: tuple, symbol_resolvers: Mapping[str, SourceSymbolResolver] | None = None, count_rows: bool = False) -> HistoricalCatalog`
- 所属：`qts.data.historical.catalog.HistoricalCatalog`
- 装饰器：`classmethod`
- 作用：Load requested roots from a local historical data directory.
- 直接原始调用：`HistoricalDataset.normalize_root` x2, `cls._require_file` x2, `HistoricalChain.load`, `HistoricalDataset`, `HistoricalFutureChainSymbolResolver`, `ValueError`, `cls`, `describe_csv_dataset`, `resolvers.get`, `root.lower`, `symbol_resolvers or {}.items`, `tuple`
- 已解析到仓库内部的调用：`qts.data.historical.catalog.HistoricalCatalog._require_file`, `qts.data.historical.catalog.HistoricalDataset`, `qts.data.historical.chains.HistoricalChain.load`, `qts.data.historical.csv_dataset.describe_csv_dataset`, `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver`
- 被以下仓库内部符号调用：`qts.data.historical.catalog.HistoricalCatalog.load`, `scripts.validate_historical.main`

#### `qts.data.historical.catalog.HistoricalCatalog.from_historical_data_config`

- 位置：`backend/src/qts/data/historical/catalog.py:123-182`
- 类型：`classmethod`
- 签名：`def from_historical_data_config(cls, config: HistoricalDataConfig, *, catalog: str, roots: tuple, symbol_resolvers: Mapping[str, SourceSymbolResolver] | None = None, count_rows: bool = False, requested_timeframe: str | None = None) -> HistoricalCatalog`
- 所属：`qts.data.historical.catalog.HistoricalCatalog`
- 装饰器：`classmethod`
- 作用：Load requested roots from a project-level historical data catalog.
- 直接原始调用：`HistoricalDataset.normalize_root` x2, `cls._require_file` x2, `FileNotFoundError`, `HistoricalChain.load`, `HistoricalDataset`, `HistoricalFutureChainSymbolResolver`, `ValueError`, `cls`, `config.catalog`, `config.resolve_dataset`, `config.store`, `describe_csv_dataset`, `resolvers.get`, `symbol_resolvers or {}.items`, `tuple`
- 已解析到仓库内部的调用：`qts.data.historical.catalog.HistoricalCatalog._require_file`, `qts.data.historical.catalog.HistoricalDataset`, `qts.data.historical.chains.HistoricalChain.load`, `qts.data.historical.csv_dataset.describe_csv_dataset`, `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver`
- 被以下仓库内部符号调用：`qts.data.historical.catalog.HistoricalCatalog.load`

#### `qts.data.historical.catalog.HistoricalCatalog._symbol_resolvers_for_load_config`

- 位置：`backend/src/qts/data/historical/catalog.py:185-201`
- 类型：`classmethod`
- 签名：`def _symbol_resolvers_for_load_config(cls, config: HistoricalCatalogLoadConfig, *, historical_data_config: HistoricalDataConfig | None) -> dict`
- 所属：`qts.data.historical.catalog.HistoricalCatalog`
- 装饰器：`classmethod`
- 作用：未写 docstring；静态推断为所属类上的 `symbol resolvers for load config` 行为。
- 直接原始调用：`StaticSymbolResolver`, `cls._chain_path_exists`
- 已解析到仓库内部的调用：`qts.data.historical.catalog.HistoricalCatalog._chain_path_exists`, `qts.registry.symbol_resolution.StaticSymbolResolver`
- 被以下仓库内部符号调用：`qts.data.historical.catalog.HistoricalCatalog.load`

#### `qts.data.historical.catalog.HistoricalCatalog._chain_path_exists`

- 位置：`backend/src/qts/data/historical/catalog.py:204-217`
- 类型：`staticmethod`
- 签名：`def _chain_path_exists(config: HistoricalCatalogLoadConfig, root: str, *, historical_data_config: HistoricalDataConfig | None) -> bool`
- 所属：`qts.data.historical.catalog.HistoricalCatalog`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `chain path exists` 行为。
- 直接原始调用：`RuntimeError`, `chain_path.exists`, `config.legacy_root_path / 'chains' / f'{root}.json'.exists`, `historical_data_config.resolve_chain_path`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.catalog.HistoricalCatalog._symbol_resolvers_for_load_config`

#### `qts.data.historical.catalog.HistoricalCatalog._require_file`

- 位置：`backend/src/qts/data/historical/catalog.py:220-226`
- 类型：`staticmethod`
- 签名：`def _require_file(path: Path, root_path: Path) -> None`
- 所属：`qts.data.historical.catalog.HistoricalCatalog`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `require file` 行为。
- 直接原始调用：`FileNotFoundError`, `Path`, `path.exists`, `path.relative_to`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.catalog.HistoricalCatalog.from_historical_data_config`, `qts.data.historical.catalog.HistoricalCatalog.from_legacy_root`

#### `qts.data.historical.catalog.HistoricalCatalogLoadConfig`

- 位置：`backend/src/qts/data/historical/catalog.py:230-319`
- 类型：`class`
- 签名：`class HistoricalCatalogLoadConfig`
- 装饰器：`dataclass()`
- 作用：Construction inputs for a configured historical catalog.
- 直接原始调用：`dataclass`, `field`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.historical.catalog.HistoricalCatalogLoadConfig.__post_init__`

- 位置：`backend/src/qts/data/historical/catalog.py:240-278`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.data.historical.catalog.HistoricalCatalogLoadConfig`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`object.__setattr__` x6, `ValueError` x5, `Path` x2, `HistoricalDataset.normalize_root`, `InstrumentId`, `isinstance`, `self._normalize_symbol`, `self.catalog_name.strip`, `self.instrument_ids.items`, `self.requested_timeframe.strip`, `str`, `tuple`
- 已解析到仓库内部的调用：`qts.core.ids.InstrumentId`, `qts.data.historical.catalog.HistoricalCatalogLoadConfig._normalize_symbol`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.historical.catalog.HistoricalCatalogLoadConfig.from_legacy_root`

- 位置：`backend/src/qts/data/historical/catalog.py:281-294`
- 类型：`classmethod`
- 签名：`def from_legacy_root(cls, root_path: Path, *, roots: tuple, instrument_ids: Mapping[str, InstrumentId] | None = None, requested_timeframe: str | None = None) -> HistoricalCatalogLoadConfig`
- 所属：`qts.data.historical.catalog.HistoricalCatalogLoadConfig`
- 装饰器：`classmethod`
- 作用：未写 docstring；静态推断为从指定来源构造或转换对象（名称：from legacy root）。
- 直接原始调用：`cls`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.runner._catalog_load_config`

#### `qts.data.historical.catalog.HistoricalCatalogLoadConfig.from_historical_data_config`

- 位置：`backend/src/qts/data/historical/catalog.py:297-312`
- 类型：`classmethod`
- 签名：`def from_historical_data_config(cls, config_path: Path, *, catalog: str, roots: tuple, instrument_ids: Mapping[str, InstrumentId] | None = None, requested_timeframe: str | None = None) -> HistoricalCatalogLoadConfig`
- 所属：`qts.data.historical.catalog.HistoricalCatalogLoadConfig`
- 装饰器：`classmethod`
- 作用：未写 docstring；静态推断为从指定来源构造或转换对象（名称：from historical data config）。
- 直接原始调用：`cls`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.runner._catalog_load_config`

#### `qts.data.historical.catalog.HistoricalCatalogLoadConfig._normalize_symbol`

- 位置：`backend/src/qts/data/historical/catalog.py:315-319`
- 类型：`staticmethod`
- 签名：`def _normalize_symbol(symbol: str) -> str`
- 所属：`qts.data.historical.catalog.HistoricalCatalogLoadConfig`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `normalize symbol` 行为。
- 直接原始调用：`ValueError`, `symbol.strip`, `symbol.strip().upper`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.catalog.HistoricalCatalogLoadConfig.__post_init__`

### `backend/src/qts/data/historical/chains.py`

模块：`qts.data.historical.chains`

#### `qts.data.historical.chains.HistoricalContract`

- 位置：`backend/src/qts/data/historical/chains.py:16-27`
- 类型：`class`
- 签名：`class HistoricalContract`
- 装饰器：`dataclass()`
- 作用：One outright contract from a historical chain file.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.chains.HistoricalChain._parse_contract`

#### `qts.data.historical.chains.HistoricalChain`

- 位置：`backend/src/qts/data/historical/chains.py:31-157`
- 类型：`class`
- 签名：`class HistoricalChain`
- 装饰器：`dataclass()`
- 作用：Parsed historical futures chain.
- 直接原始调用：`dataclass`, `field`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.historical.chains.HistoricalChain.__post_init__`

- 位置：`backend/src/qts/data/historical/chains.py:44-52`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.data.historical.chains.HistoricalChain`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`contracts_by_symbol.setdefault`, `object.__setattr__`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.historical.chains.HistoricalChain.contract_for_symbol`

- 位置：`backend/src/qts/data/historical/chains.py:54-58`
- 类型：`method`
- 签名：`def contract_for_symbol(self, symbol: str) -> HistoricalContract`
- 所属：`qts.data.historical.chains.HistoricalChain`
- 作用：未写 docstring；静态推断为所属类上的 `contract for symbol` 行为。
- 直接原始调用：`KeyError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.historical.chains.HistoricalChain.is_outright_symbol`

- 位置：`backend/src/qts/data/historical/chains.py:60-61`
- 类型：`method`
- 签名：`def is_outright_symbol(self, symbol: str) -> bool`
- 所属：`qts.data.historical.chains.HistoricalChain`
- 作用：未写 docstring；静态推断为判断布尔条件（名称：is outright symbol）。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.chains.HistoricalChain.instrument_id_for_symbol`

#### `qts.data.historical.chains.HistoricalChain.instrument_id_for_symbol`

- 位置：`backend/src/qts/data/historical/chains.py:63-66`
- 类型：`method`
- 签名：`def instrument_id_for_symbol(self, symbol: str) -> InstrumentId`
- 所属：`qts.data.historical.chains.HistoricalChain`
- 作用：未写 docstring；静态推断为所属类上的 `instrument id for symbol` 行为。
- 直接原始调用：`InstrumentId`, `ValueError`, `self.is_outright_symbol`
- 已解析到仓库内部的调用：`qts.core.ids.InstrumentId`, `qts.data.historical.chains.HistoricalChain.is_outright_symbol`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.historical.chains.HistoricalChain.load`

- 位置：`backend/src/qts/data/historical/chains.py:69-105`
- 类型：`classmethod`
- 签名：`def load(cls, path: Path) -> HistoricalChain`
- 所属：`qts.data.historical.chains.HistoricalChain`
- 装饰器：`classmethod`
- 作用：Load a historical futures chain JSON file into typed metadata.
- 直接原始调用：`cls._required_text` x5, `cls._required_decimal` x2, `ValueError`, `cls`, `cls._exchange_code`, `cls._parse_contract`, `isinstance`, `json.loads`, `path.read_text`, `payload.get`, `tuple`
- 已解析到仓库内部的调用：`qts.data.historical.chains.HistoricalChain._exchange_code`, `qts.data.historical.chains.HistoricalChain._parse_contract`, `qts.data.historical.chains.HistoricalChain._required_decimal`, `qts.data.historical.chains.HistoricalChain._required_text`
- 被以下仓库内部符号调用：`qts.data.historical.catalog.HistoricalCatalog.from_historical_data_config`, `qts.data.historical.catalog.HistoricalCatalog.from_legacy_root`

#### `qts.data.historical.chains.HistoricalChain._parse_contract`

- 位置：`backend/src/qts/data/historical/chains.py:108-135`
- 类型：`classmethod`
- 签名：`def _parse_contract(cls, payload: object, *, root: str, exchange: str, chain_currency: str, chain_tick_size: Decimal, chain_multiplier: Decimal, chain_calendar: str) -> HistoricalContract`
- 所属：`qts.data.historical.chains.HistoricalChain`
- 装饰器：`classmethod`
- 作用：未写 docstring；静态推断为所属类上的 `parse contract` 行为。
- 直接原始调用：`cls._required_text` x3, `item.get` x2, `str` x2, `HistoricalContract`, `ValueError`, `date.fromisoformat`, `datetime.fromisoformat`, `datetime.fromisoformat().astimezone`, `isinstance`
- 已解析到仓库内部的调用：`qts.data.historical.chains.HistoricalChain._required_text`, `qts.data.historical.chains.HistoricalContract`
- 被以下仓库内部符号调用：`qts.data.historical.chains.HistoricalChain.load`

#### `qts.data.historical.chains.HistoricalChain._required_text`

- 位置：`backend/src/qts/data/historical/chains.py:138-142`
- 类型：`staticmethod`
- 签名：`def _required_text(payload: dict, field: str) -> str`
- 所属：`qts.data.historical.chains.HistoricalChain`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `required text` 行为。
- 直接原始调用：`ValueError`, `isinstance`, `payload.get`, `value.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.chains.HistoricalChain._parse_contract`, `qts.data.historical.chains.HistoricalChain.load`

#### `qts.data.historical.chains.HistoricalChain._required_decimal`

- 位置：`backend/src/qts/data/historical/chains.py:145-151`
- 类型：`staticmethod`
- 签名：`def _required_decimal(payload: dict, field: str) -> Decimal`
- 所属：`qts.data.historical.chains.HistoricalChain`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `required decimal` 行为。
- 直接原始调用：`Decimal` x2, `ValueError` x2, `str`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.chains.HistoricalChain.load`

#### `qts.data.historical.chains.HistoricalChain._exchange_code`

- 位置：`backend/src/qts/data/historical/chains.py:154-157`
- 类型：`staticmethod`
- 签名：`def _exchange_code(market: str) -> str`
- 所属：`qts.data.historical.chains.HistoricalChain`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `exchange code` 行为。
- 直接原始调用：`market.endswith`, `market.removesuffix`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.chains.HistoricalChain.load`

### `backend/src/qts/data/historical/config.py`

模块：`qts.data.historical.config`

#### `qts.data.historical.config.HistoricalDataStoreDefaults`

- 位置：`backend/src/qts/data/historical/config.py:26-42`
- 类型：`class`
- 签名：`class HistoricalDataStoreDefaults`
- 装饰器：`dataclass()`
- 作用：Default metadata applied to datasets and bars in one historical store.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.config.HistoricalDataConfig._parse_store_defaults`

#### `qts.data.historical.config.HistoricalDataStoreDefaults.__post_init__`

- 位置：`backend/src/qts/data/historical/config.py:34-42`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.data.historical.config.HistoricalDataStoreDefaults`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x4, `self.exchange_timezone.strip`, `self.normalization.strip`, `self.schema.strip`, `self.timezone_policy.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.historical.config.HistoricalDataStoreConfig`

- 位置：`backend/src/qts/data/historical/config.py:46-96`
- 类型：`class`
- 签名：`class HistoricalDataStoreConfig`
- 装饰器：`dataclass()`
- 作用：Project-level physical layout for a historical data store.
- 直接原始调用：`Path` x2, `dataclass`, `field`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.config.HistoricalDataConfig._parse_stores`

#### `qts.data.historical.config.HistoricalDataStoreConfig.__post_init__`

- 位置：`backend/src/qts/data/historical/config.py:62-80`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.data.historical.config.HistoricalDataStoreConfig`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x9, `self.bars_file_template.strip`, `self.chain_file_template.strip`, `self.exchange_timezone.strip`, `self.name.strip`, `self.normalization.strip`, `self.source_timeframe.strip`, `self.timezone_policy.strip`, `self.type.strip`, `str`, `str().strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.historical.config.HistoricalDataStoreConfig.bars_path`

- 位置：`backend/src/qts/data/historical/config.py:82-84`
- 类型：`method`
- 签名：`def bars_path(self, root: str, *, override: str | None = None) -> Path`
- 所属：`qts.data.historical.config.HistoricalDataStoreConfig`
- 作用：未写 docstring；静态推断为所属类上的 `bars path` 行为。
- 直接原始调用：`self._join`, `self._render_template`
- 已解析到仓库内部的调用：`qts.data.historical.config.HistoricalDataStoreConfig._join`, `qts.data.historical.config.HistoricalDataStoreConfig._render_template`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.historical.config.HistoricalDataStoreConfig.chain_path`

- 位置：`backend/src/qts/data/historical/config.py:86-88`
- 类型：`method`
- 签名：`def chain_path(self, root: str, *, override: str | None = None) -> Path`
- 所属：`qts.data.historical.config.HistoricalDataStoreConfig`
- 作用：未写 docstring；静态推断为所属类上的 `chain path` 行为。
- 直接原始调用：`self._join`, `self._render_template`
- 已解析到仓库内部的调用：`qts.data.historical.config.HistoricalDataStoreConfig._join`, `qts.data.historical.config.HistoricalDataStoreConfig._render_template`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.historical.config.HistoricalDataStoreConfig._join`

- 位置：`backend/src/qts/data/historical/config.py:90-91`
- 类型：`method`
- 签名：`def _join(self, path: Path) -> Path`
- 所属：`qts.data.historical.config.HistoricalDataStoreConfig`
- 作用：未写 docstring；静态推断为所属类上的 `join` 行为。
- 直接原始调用：`path.is_absolute`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.config.HistoricalDataStoreConfig.bars_path`, `qts.data.historical.config.HistoricalDataStoreConfig.chain_path`

#### `qts.data.historical.config.HistoricalDataStoreConfig._render_template`

- 位置：`backend/src/qts/data/historical/config.py:94-96`
- 类型：`staticmethod`
- 签名：`def _render_template(template: str, root: str) -> str`
- 所属：`qts.data.historical.config.HistoricalDataStoreConfig`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `render template` 行为。
- 直接原始调用：`HistoricalDatasetConfig.normalize_root`, `normalized_root.lower`, `template.format`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.config.HistoricalDataStoreConfig.bars_path`, `qts.data.historical.config.HistoricalDataStoreConfig.chain_path`

#### `qts.data.historical.config.HistoricalBarFileConfig`

- 位置：`backend/src/qts/data/historical/config.py:100-122`
- 类型：`class`
- 签名：`class HistoricalBarFileConfig`
- 装饰器：`dataclass()`
- 作用：One physical bar file for a dataset.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.config.HistoricalDataConfig._parse_bar_files`, `qts.data.historical.config.HistoricalDataConfig._select_bar_file`

#### `qts.data.historical.config.HistoricalBarFileConfig.__post_init__`

- 位置：`backend/src/qts/data/historical/config.py:110-122`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.data.historical.config.HistoricalBarFileConfig`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x6, `self.exchange_timezone.strip`, `self.file.strip`, `self.normalization.strip`, `self.schema.strip`, `self.timeframe.strip`, `self.timezone_policy.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.historical.config.HistoricalDatasetConfig`

- 位置：`backend/src/qts/data/historical/config.py:126-166`
- 类型：`class`
- 签名：`class HistoricalDatasetConfig`
- 装饰器：`dataclass()`
- 作用：One product/data entry inside a historical data catalog.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.config.HistoricalDataConfig._parse_datasets`

#### `qts.data.historical.config.HistoricalDatasetConfig.__post_init__`

- 位置：`backend/src/qts/data/historical/config.py:139-155`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.data.historical.config.HistoricalDatasetConfig`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x8, `self.asset_class.strip`, `self.bars_file.strip`, `self.chain_file.strip`, `self.exchange.strip`, `self.exchange_timezone.strip`, `self.root.strip`, `self.schema.strip`, `self.source_timeframe.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.historical.config.HistoricalDatasetConfig.requires_chain`

- 位置：`backend/src/qts/data/historical/config.py:158-159`
- 类型：`property`
- 签名：`def requires_chain(self) -> bool`
- 所属：`qts.data.historical.config.HistoricalDatasetConfig`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为所属类上的 `requires chain` 行为。
- 直接原始调用：`self.asset_class.strip`, `self.asset_class.strip().lower`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.historical.config.HistoricalDatasetConfig.normalize_root`

- 位置：`backend/src/qts/data/historical/config.py:162-166`
- 类型：`staticmethod`
- 签名：`def normalize_root(root: str) -> str`
- 所属：`qts.data.historical.config.HistoricalDatasetConfig`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `normalize root` 行为。
- 直接原始调用：`ValueError`, `root.strip`, `root.strip().upper`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.historical.config.HistoricalDataCatalogConfig`

- 位置：`backend/src/qts/data/historical/config.py:170-183`
- 类型：`class`
- 签名：`class HistoricalDataCatalogConfig`
- 装饰器：`dataclass()`
- 作用：Logical catalog of historical datasets backed by one store.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.config.HistoricalDataConfig._parse_catalogs`

#### `qts.data.historical.config.HistoricalDataCatalogConfig.__post_init__`

- 位置：`backend/src/qts/data/historical/config.py:177-183`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.data.historical.config.HistoricalDataCatalogConfig`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x3, `self.name.strip`, `self.store.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.historical.config.HistoricalDatasetLocation`

- 位置：`backend/src/qts/data/historical/config.py:187-199`
- 类型：`class`
- 签名：`class HistoricalDatasetLocation`
- 装饰器：`dataclass()`
- 作用：Resolved physical file paths for one catalog dataset.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.config.HistoricalDataConfig.resolve_dataset`

#### `qts.data.historical.config.HistoricalDataConfig`

- 位置：`backend/src/qts/data/historical/config.py:203-554`
- 类型：`class`
- 签名：`class HistoricalDataConfig`
- 装饰器：`dataclass()`
- 作用：Project-level historical data stores and catalogs.
- 直接原始调用：`dataclass`, `field`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.historical.config.HistoricalDataConfig.__post_init__`

- 位置：`backend/src/qts/data/historical/config.py:210-217`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.data.historical.config.HistoricalDataConfig`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x3, `self.catalogs.values`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.historical.config.HistoricalDataConfig.from_yaml`

- 位置：`backend/src/qts/data/historical/config.py:220-231`
- 类型：`classmethod`
- 签名：`def from_yaml(cls, path: Path) -> HistoricalDataConfig`
- 所属：`qts.data.historical.config.HistoricalDataConfig`
- 装饰器：`classmethod`
- 作用：未写 docstring；静态推断为从指定来源构造或转换对象（名称：from yaml）。
- 直接原始调用：`raw_config.get` x3, `ValueError` x2, `isinstance` x2, `cls`, `cls._parse_catalogs`, `cls._parse_schemas`, `cls._parse_stores`, `path.read_text`, `payload.get`, `yaml.safe_load`
- 已解析到仓库内部的调用：`qts.data.historical.config.HistoricalDataConfig._parse_catalogs`, `qts.data.historical.config.HistoricalDataConfig._parse_schemas`, `qts.data.historical.config.HistoricalDataConfig._parse_stores`
- 被以下仓库内部符号调用：`qts.data.historical.catalog.HistoricalCatalog.load`

#### `qts.data.historical.config.HistoricalDataConfig.catalog`

- 位置：`backend/src/qts/data/historical/config.py:233-237`
- 类型：`method`
- 签名：`def catalog(self, name: str) -> HistoricalDataCatalogConfig`
- 所属：`qts.data.historical.config.HistoricalDataConfig`
- 作用：未写 docstring；静态推断为所属类上的 `catalog` 行为。
- 直接原始调用：`KeyError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.config.HistoricalDataConfig.resolve_chain_path`, `qts.data.historical.config.HistoricalDataConfig.resolve_dataset`

#### `qts.data.historical.config.HistoricalDataConfig.store`

- 位置：`backend/src/qts/data/historical/config.py:239-243`
- 类型：`method`
- 签名：`def store(self, name: str) -> HistoricalDataStoreConfig`
- 所属：`qts.data.historical.config.HistoricalDataConfig`
- 作用：未写 docstring；静态推断为所属类上的 `store` 行为。
- 直接原始调用：`KeyError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.config.HistoricalDataConfig.resolve_chain_path`, `qts.data.historical.config.HistoricalDataConfig.resolve_dataset`

#### `qts.data.historical.config.HistoricalDataConfig.resolve_dataset`

- 位置：`backend/src/qts/data/historical/config.py:245-289`
- 类型：`method`
- 签名：`def resolve_dataset(self, catalog_name: str, root: str, *, requested_timeframe: str | None = None) -> HistoricalDatasetLocation`
- 所属：`qts.data.historical.config.HistoricalDataConfig`
- 作用：未写 docstring；静态推断为解析标识、引用或配置到目标对象（名称：resolve dataset）。
- 直接原始调用：`HistoricalDatasetConfig.normalize_root`, `HistoricalDatasetLocation`, `KeyError`, `self._csv_schema`, `self._select_bar_file`, `self.catalog`, `self.store`, `store.bars_path`, `store.chain_path`
- 已解析到仓库内部的调用：`qts.data.historical.config.HistoricalDataConfig._csv_schema`, `qts.data.historical.config.HistoricalDataConfig._select_bar_file`, `qts.data.historical.config.HistoricalDataConfig.catalog`, `qts.data.historical.config.HistoricalDataConfig.store`, `qts.data.historical.config.HistoricalDatasetLocation`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.historical.config.HistoricalDataConfig.resolve_chain_path`

- 位置：`backend/src/qts/data/historical/config.py:291-305`
- 类型：`method`
- 签名：`def resolve_chain_path(self, catalog_name: str, root: str) -> Path | None`
- 所属：`qts.data.historical.config.HistoricalDataConfig`
- 作用：Resolve chain metadata path without selecting a concrete bar file.
- 直接原始调用：`HistoricalDatasetConfig.normalize_root`, `KeyError`, `self.catalog`, `self.store`, `store.chain_path`
- 已解析到仓库内部的调用：`qts.data.historical.config.HistoricalDataConfig.catalog`, `qts.data.historical.config.HistoricalDataConfig.store`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.historical.config.HistoricalDataConfig._csv_schema`

- 位置：`backend/src/qts/data/historical/config.py:307-313`
- 类型：`method`
- 签名：`def _csv_schema(self, name: str | None) -> HistoricalCsvSchema`
- 所属：`qts.data.historical.config.HistoricalDataConfig`
- 作用：未写 docstring；静态推断为所属类上的 `csv schema` 行为。
- 直接原始调用：`KeyError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.config.HistoricalDataConfig.resolve_dataset`

#### `qts.data.historical.config.HistoricalDataConfig._parse_stores`

- 位置：`backend/src/qts/data/historical/config.py:316-350`
- 类型：`classmethod`
- 签名：`def _parse_stores(cls, payload: object) -> dict`
- 所属：`qts.data.historical.config.HistoricalDataConfig`
- 装饰器：`classmethod`
- 作用：未写 docstring；静态推断为所属类上的 `parse stores` 行为。
- 直接原始调用：`str` x10, `raw_store.get` x9, `Path` x3, `ValueError` x3, `isinstance` x3, `HistoricalDataStoreConfig`, `cls._parse_store_defaults`, `payload.items`
- 已解析到仓库内部的调用：`qts.data.historical.config.HistoricalDataConfig._parse_store_defaults`, `qts.data.historical.config.HistoricalDataStoreConfig`
- 被以下仓库内部符号调用：`qts.data.historical.config.HistoricalDataConfig.from_yaml`

#### `qts.data.historical.config.HistoricalDataConfig._parse_store_defaults`

- 位置：`backend/src/qts/data/historical/config.py:353-381`
- 类型：`staticmethod`
- 签名：`def _parse_store_defaults(raw_store: Mapping) -> HistoricalDataStoreDefaults`
- 所属：`qts.data.historical.config.HistoricalDataConfig`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `parse store defaults` 行为。
- 直接原始调用：`str` x5, `raw_defaults.get` x4, `raw_store.get` x4, `HistoricalDataStoreDefaults`, `ValueError`, `isinstance`
- 已解析到仓库内部的调用：`qts.data.historical.config.HistoricalDataStoreDefaults`
- 被以下仓库内部符号调用：`qts.data.historical.config.HistoricalDataConfig._parse_stores`

#### `qts.data.historical.config.HistoricalDataConfig._parse_catalogs`

- 位置：`backend/src/qts/data/historical/config.py:384-401`
- 类型：`classmethod`
- 签名：`def _parse_catalogs(cls, payload: object) -> dict`
- 所属：`qts.data.historical.config.HistoricalDataConfig`
- 装饰器：`classmethod`
- 作用：未写 docstring；静态推断为所属类上的 `parse catalogs` 行为。
- 直接原始调用：`ValueError` x4, `isinstance` x4, `HistoricalDataCatalogConfig`, `cls._parse_datasets`, `payload.items`, `raw_catalog.get`, `str`
- 已解析到仓库内部的调用：`qts.data.historical.config.HistoricalDataCatalogConfig`, `qts.data.historical.config.HistoricalDataConfig._parse_datasets`
- 被以下仓库内部符号调用：`qts.data.historical.config.HistoricalDataConfig.from_yaml`

#### `qts.data.historical.config.HistoricalDataConfig._parse_datasets`

- 位置：`backend/src/qts/data/historical/config.py:404-451`
- 类型：`classmethod`
- 签名：`def _parse_datasets(cls, payload: Mapping) -> dict`
- 所属：`qts.data.historical.config.HistoricalDataConfig`
- 装饰器：`classmethod`
- 作用：未写 docstring；静态推断为所属类上的 `parse datasets` 行为。
- 直接原始调用：`raw_dataset.get` x7, `str` x7, `ValueError` x3, `isinstance` x2, `', '.join`, `HistoricalDatasetConfig`, `HistoricalDatasetConfig.normalize_root`, `_DATASET_STORAGE_PATH_KEYS.intersection`, `cls._parse_bar_files`, `payload.items`, `sorted`
- 已解析到仓库内部的调用：`qts.data.historical.config.HistoricalDataConfig._parse_bar_files`, `qts.data.historical.config.HistoricalDatasetConfig`
- 被以下仓库内部符号调用：`qts.data.historical.config.HistoricalDataConfig._parse_catalogs`

#### `qts.data.historical.config.HistoricalDataConfig._parse_bar_files`

- 位置：`backend/src/qts/data/historical/config.py:454-487`
- 类型：`staticmethod`
- 签名：`def _parse_bar_files(payload: object) -> tuple`
- 所属：`qts.data.historical.config.HistoricalDataConfig`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `parse bar files` 行为。
- 直接原始调用：`raw_bar.get` x6, `str` x6, `ValueError` x2, `isinstance` x2, `HistoricalBarFileConfig`, `bars.append`, `tuple`
- 已解析到仓库内部的调用：`qts.data.historical.config.HistoricalBarFileConfig`
- 被以下仓库内部符号调用：`qts.data.historical.config.HistoricalDataConfig._parse_datasets`

#### `qts.data.historical.config.HistoricalDataConfig._parse_schemas`

- 位置：`backend/src/qts/data/historical/config.py:490-515`
- 类型：`staticmethod`
- 签名：`def _parse_schemas(payload: object) -> dict`
- 所属：`qts.data.historical.config.HistoricalDataConfig`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `parse schemas` 行为。
- 直接原始调用：`str` x8, `ValueError` x3, `isinstance` x3, `HistoricalCsvSchema`, `payload.items`, `raw_schema.get`
- 已解析到仓库内部的调用：`qts.data.historical.csv_format.HistoricalCsvSchema`
- 被以下仓库内部符号调用：`qts.data.historical.config.HistoricalDataConfig.from_yaml`

#### `qts.data.historical.config.HistoricalDataConfig._select_bar_file`

- 位置：`backend/src/qts/data/historical/config.py:518-554`
- 类型：`staticmethod`
- 签名：`def _select_bar_file(*, catalog_name: str, root: str, dataset: HistoricalDatasetConfig, store: HistoricalDataStoreConfig, requested_timeframe: str | None) -> HistoricalBarFileConfig`
- 所属：`qts.data.historical.config.HistoricalDataConfig`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `select bar file` 行为。
- 直接原始调用：`FeedCapabilities`, `FeedCapabilities().source_timeframe_for`, `HistoricalBarFileConfig`, `RuntimeError`, `ValueError`, `frozenset`, `len`
- 已解析到仓库内部的调用：`qts.data.historical.config.HistoricalBarFileConfig`, `qts.data.live_feed.FeedCapabilities`
- 被以下仓库内部符号调用：`qts.data.historical.config.HistoricalDataConfig.resolve_dataset`

### `backend/src/qts/data/historical/csv_dataset.py`

模块：`qts.data.historical.csv_dataset`

#### `qts.data.historical.csv_dataset.CsvDatasetDescription`

- 位置：`backend/src/qts/data/historical/csv_dataset.py:42-52`
- 类型：`class`
- 签名：`class CsvDatasetDescription`
- 装饰器：`dataclass()`
- 作用：Cheap metadata description for a historical CSV dataset.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.describe_csv_dataset`

#### `qts.data.historical.csv_dataset.HistoricalCsvStats`

- 位置：`backend/src/qts/data/historical/csv_dataset.py:56-74`
- 类型：`class`
- 签名：`class HistoricalCsvStats`
- 装饰器：`dataclass()`
- 作用：Streaming reader counters.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.HistoricalBarStream.__init__`, `qts.data.historical.csv_dataset.validate_historical_sample`

#### `qts.data.historical.csv_dataset.HistoricalCsvStats.as_dict`

- 位置：`backend/src/qts/data/historical/csv_dataset.py:66-74`
- 类型：`method`
- 签名：`def as_dict(self) -> dict`
- 所属：`qts.data.historical.csv_dataset.HistoricalCsvStats`
- 作用：未写 docstring；静态推断为所属类上的 `as dict` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.historical.csv_dataset.HistoricalValidationSample`

- 位置：`backend/src/qts/data/historical/csv_dataset.py:78-83`
- 类型：`class`
- 签名：`class HistoricalValidationSample`
- 装饰器：`dataclass()`
- 作用：Validation report plus counters for a sampled historical CSV.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.validate_historical_sample`

#### `qts.data.historical.csv_dataset.HistoricalBarStream`

- 位置：`backend/src/qts/data/historical/csv_dataset.py:86-381`
- 类型：`class`
- 签名：`class HistoricalBarStream`
- 作用：Lazy iterable over historical bars with side-channel reader stats.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.iter_historical_bars`

#### `qts.data.historical.csv_dataset.HistoricalBarStream.__init__`

- 位置：`backend/src/qts/data/historical/csv_dataset.py:89-113`
- 类型：`method`
- 签名：`def __init__(self, *, csv_path: Path, symbol_resolver: SourceSymbolResolver, timeframe: str, start: datetime | None = None, end: datetime | None = None, contract_selector: FutureContractSelector | None = None, continuous_instrument_id: InstrumentId | None = None, session_window: RegularSessionWindow | None = None, schema: HistoricalCsvSchema | None = None) -> None`
- 所属：`qts.data.historical.csv_dataset.HistoricalBarStream`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：`HistoricalCsvStats`
- 已解析到仓库内部的调用：`qts.data.historical.csv_dataset.HistoricalCsvStats`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.historical.csv_dataset.HistoricalBarStream.__iter__`

- 位置：`backend/src/qts/data/historical/csv_dataset.py:115-127`
- 类型：`method`
- 签名：`def __iter__(self) -> Iterator`
- 所属：`qts.data.historical.csv_dataset.HistoricalBarStream`
- 作用：未写 docstring；实现 Python 协议方法 `__iter__`。
- 直接原始调用：`csv.DictReader`, `self._csv_path.open`, `self._iter_all_supported_rows`, `self._iter_selected_contract_rows`, `self._iter_session_selected_contract_rows`, `tuple`, `validate_historical_csv_columns`
- 已解析到仓库内部的调用：`qts.data.historical.csv_dataset.HistoricalBarStream._iter_all_supported_rows`, `qts.data.historical.csv_dataset.HistoricalBarStream._iter_selected_contract_rows`, `qts.data.historical.csv_dataset.HistoricalBarStream._iter_session_selected_contract_rows`, `qts.data.historical.csv_format.validate_historical_csv_columns`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.historical.csv_dataset.HistoricalBarStream._iter_all_supported_rows`

- 位置：`backend/src/qts/data/historical/csv_dataset.py:129-152`
- 类型：`method`
- 签名：`def _iter_all_supported_rows(self, reader: csv.DictReader) -> Iterator`
- 所属：`qts.data.historical.csv_dataset.HistoricalBarStream`
- 作用：未写 docstring；静态推断为所属类上的 `iter all supported rows` 行为。
- 直接原始调用：`_row_to_bar`, `self._count_excluded_symbol`, `self._field`, `self._symbol_resolver.is_supported_symbol`, `self._timestamp`
- 已解析到仓库内部的调用：`qts.data.historical.csv_dataset.HistoricalBarStream._count_excluded_symbol`, `qts.data.historical.csv_dataset.HistoricalBarStream._field`, `qts.data.historical.csv_dataset.HistoricalBarStream._timestamp`, `qts.data.historical.csv_dataset._row_to_bar`
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.HistoricalBarStream.__iter__`

#### `qts.data.historical.csv_dataset.HistoricalBarStream._iter_selected_contract_rows`

- 位置：`backend/src/qts/data/historical/csv_dataset.py:154-215`
- 类型：`method`
- 签名：`def _iter_selected_contract_rows(self, reader: csv.DictReader) -> Iterator`
- 所属：`qts.data.historical.csv_dataset.HistoricalBarStream`
- 作用：未写 docstring；静态推断为所属类上的 `iter selected contract rows` 行为。
- 直接原始调用：`FutureContractCandidate`, `FutureRollSelection`, `RuntimeError`, `_row_to_bar`, `candidates.append`, `contract_selector.select`, `len`, `replace`, `self._count_excluded_symbol`, `self._field`, `self._resolver_root`, `self._symbol_resolver.is_supported_symbol`, `self._timestamp_groups`, `self.roll_selections.append`, `tuple`
- 已解析到仓库内部的调用：`qts.data.historical.csv_dataset.HistoricalBarStream._count_excluded_symbol`, `qts.data.historical.csv_dataset.HistoricalBarStream._field`, `qts.data.historical.csv_dataset.HistoricalBarStream._resolver_root`, `qts.data.historical.csv_dataset.HistoricalBarStream._timestamp_groups`, `qts.data.historical.csv_dataset._row_to_bar`, `qts.registry.future_roll.FutureContractCandidate`, `qts.registry.future_roll.FutureRollSelection`
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.HistoricalBarStream.__iter__`

#### `qts.data.historical.csv_dataset.HistoricalBarStream._iter_session_selected_contract_rows`

- 位置：`backend/src/qts/data/historical/csv_dataset.py:217-261`
- 类型：`method`
- 签名：`def _iter_session_selected_contract_rows(self, reader: csv.DictReader) -> Iterator`
- 所属：`qts.data.historical.csv_dataset.HistoricalBarStream`
- 作用：未写 docstring；静态推断为所属类上的 `iter session selected contract rows` 行为。
- 直接原始调用：`self._emit_selected_session_rows` x3, `RuntimeError` x2, `current_groups.append`, `self._timestamp_groups`, `session_window.session_id_for_timestamp`
- 已解析到仓库内部的调用：`qts.data.historical.csv_dataset.HistoricalBarStream._emit_selected_session_rows`, `qts.data.historical.csv_dataset.HistoricalBarStream._timestamp_groups`
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.HistoricalBarStream.__iter__`

#### `qts.data.historical.csv_dataset.HistoricalBarStream._emit_selected_session_rows`

- 位置：`backend/src/qts/data/historical/csv_dataset.py:263-350`
- 类型：`method`
- 签名：`def _emit_selected_session_rows(self, session_id: str, groups: list, *, contract_selector: FutureContractSelector) -> Iterator`
- 所属：`qts.data.historical.csv_dataset.HistoricalBarStream`
- 作用：未写 docstring；静态推断为所属类上的 `emit selected session rows` 行为。
- 直接原始调用：`Decimal`, `FutureContractCandidate`, `FutureRollSelection`, `_row_ohlcv`, `_row_to_bar`, `closes_by_timestamp.append`, `contract_selector.select`, `defaultdict`, `historical_timeframe_delta`, `len`, `replace`, `rows_by_instrument.get`, `rows_by_timestamp.append`, `self._count_excluded_symbol`, `self._field`, `self._resolver_root`, `self._symbol_resolver.instrument_id_for_symbol`, `self._symbol_resolver.is_supported_symbol`, `self.roll_selections.append`, `total_volume_by_instrument.items`, `tuple`, `zip`
- 已解析到仓库内部的调用：`qts.data.historical.csv_dataset.HistoricalBarStream._count_excluded_symbol`, `qts.data.historical.csv_dataset.HistoricalBarStream._field`, `qts.data.historical.csv_dataset.HistoricalBarStream._resolver_root`, `qts.data.historical.csv_dataset._row_ohlcv`, `qts.data.historical.csv_dataset._row_to_bar`, `qts.data.historical.csv_format.historical_timeframe_delta`, `qts.registry.future_roll.FutureContractCandidate`, `qts.registry.future_roll.FutureRollSelection`
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.HistoricalBarStream._iter_session_selected_contract_rows`

#### `qts.data.historical.csv_dataset.HistoricalBarStream._timestamp_groups`

- 位置：`backend/src/qts/data/historical/csv_dataset.py:352-367`
- 类型：`method`
- 签名：`def _timestamp_groups(self, reader: csv.DictReader) -> Iterator`
- 所属：`qts.data.historical.csv_dataset.HistoricalBarStream`
- 作用：未写 docstring；静态推断为所属类上的 `timestamp groups` 行为。
- 直接原始调用：`parse_historical_ts_event` x2, `current_rows.append`, `self._field`
- 已解析到仓库内部的调用：`qts.data.historical.csv_dataset.HistoricalBarStream._field`, `qts.data.historical.csv_format.parse_historical_ts_event`
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.HistoricalBarStream._iter_selected_contract_rows`, `qts.data.historical.csv_dataset.HistoricalBarStream._iter_session_selected_contract_rows`

#### `qts.data.historical.csv_dataset.HistoricalBarStream._count_excluded_symbol`

- 位置：`backend/src/qts/data/historical/csv_dataset.py:369-372`
- 类型：`method`
- 签名：`def _count_excluded_symbol(self, symbol: str) -> None`
- 所属：`qts.data.historical.csv_dataset.HistoricalBarStream`
- 作用：未写 docstring；静态推断为所属类上的 `count excluded symbol` 行为。
- 直接原始调用：`_is_spread_symbol`
- 已解析到仓库内部的调用：`qts.data.historical.csv_dataset._is_spread_symbol`
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.HistoricalBarStream._emit_selected_session_rows`, `qts.data.historical.csv_dataset.HistoricalBarStream._iter_all_supported_rows`, `qts.data.historical.csv_dataset.HistoricalBarStream._iter_selected_contract_rows`

#### `qts.data.historical.csv_dataset.HistoricalBarStream._resolver_root`

- 位置：`backend/src/qts/data/historical/csv_dataset.py:374-375`
- 类型：`method`
- 签名：`def _resolver_root(self) -> str`
- 所属：`qts.data.historical.csv_dataset.HistoricalBarStream`
- 作用：未写 docstring；静态推断为所属类上的 `resolver root` 行为。
- 直接原始调用：`_resolver_root`
- 已解析到仓库内部的调用：`qts.data.historical.csv_dataset._resolver_root`
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.HistoricalBarStream._emit_selected_session_rows`, `qts.data.historical.csv_dataset.HistoricalBarStream._iter_selected_contract_rows`

#### `qts.data.historical.csv_dataset.HistoricalBarStream._field`

- 位置：`backend/src/qts/data/historical/csv_dataset.py:377-378`
- 类型：`method`
- 签名：`def _field(self, row: dict, semantic_name: str) -> str`
- 所属：`qts.data.historical.csv_dataset.HistoricalBarStream`
- 作用：未写 docstring；静态推断为所属类上的 `field` 行为。
- 直接原始调用：`getattr`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.HistoricalBarStream._emit_selected_session_rows`, `qts.data.historical.csv_dataset.HistoricalBarStream._iter_all_supported_rows`, `qts.data.historical.csv_dataset.HistoricalBarStream._iter_selected_contract_rows`, `qts.data.historical.csv_dataset.HistoricalBarStream._timestamp`, `qts.data.historical.csv_dataset.HistoricalBarStream._timestamp_groups`

#### `qts.data.historical.csv_dataset.HistoricalBarStream._timestamp`

- 位置：`backend/src/qts/data/historical/csv_dataset.py:380-381`
- 类型：`method`
- 签名：`def _timestamp(self, row: dict) -> datetime`
- 所属：`qts.data.historical.csv_dataset.HistoricalBarStream`
- 作用：未写 docstring；静态推断为所属类上的 `timestamp` 行为。
- 直接原始调用：`parse_historical_ts_event`, `self._field`
- 已解析到仓库内部的调用：`qts.data.historical.csv_dataset.HistoricalBarStream._field`, `qts.data.historical.csv_format.parse_historical_ts_event`
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.HistoricalBarStream._iter_all_supported_rows`

#### `qts.data.historical.csv_dataset.describe_csv_dataset`

- 位置：`backend/src/qts/data/historical/csv_dataset.py:384-408`
- 类型：`module_function`
- 签名：`def describe_csv_dataset(path: Path, *, root: str, timeframe: str = '1m', count_rows: bool = False, schema: HistoricalCsvSchema | None = None) -> CsvDatasetDescription`
- 作用：Read historical CSV identity metadata without materializing row data.
- 直接原始调用：`CsvDatasetDescription`, `csv.reader`, `next`, `path.open`, `sum`, `tuple`, `validate_historical_csv_columns`
- 已解析到仓库内部的调用：`qts.data.historical.csv_dataset.CsvDatasetDescription`, `qts.data.historical.csv_format.validate_historical_csv_columns`
- 被以下仓库内部符号调用：`qts.data.historical.catalog.HistoricalCatalog.from_historical_data_config`, `qts.data.historical.catalog.HistoricalCatalog.from_legacy_root`

#### `qts.data.historical.csv_dataset.iter_historical_bars`

- 位置：`backend/src/qts/data/historical/csv_dataset.py:411-435`
- 类型：`module_function`
- 签名：`def iter_historical_bars(csv_path: Path, symbol_resolver: SourceSymbolResolver | HistoricalChain, *, timeframe: str = '1m', start: datetime | None = None, end: datetime | None = None, contract_selector: FutureContractSelector | None = None, continuous_instrument_id: InstrumentId | None = None, session_window: RegularSessionWindow | None = None, schema: HistoricalCsvSchema | None = None) -> HistoricalBarStream`
- 作用：Return a lazy stream of outright historical bars.
- 直接原始调用：`HistoricalBarStream`, `_as_symbol_resolver`
- 已解析到仓库内部的调用：`qts.data.historical.csv_dataset.HistoricalBarStream`, `qts.data.historical.csv_dataset._as_symbol_resolver`
- 被以下仓库内部符号调用：`qts.backtest.inputs.BacktestInputBuilder._stream_configured_bars`, `qts.data.historical.service.HistoricalMarketDataService.events`

#### `qts.data.historical.csv_dataset.validate_historical_sample`

- 位置：`backend/src/qts/data/historical/csv_dataset.py:438-511`
- 类型：`module_function`
- 签名：`def validate_historical_sample(csv_path: Path, symbol_resolver: SourceSymbolResolver | HistoricalChain, *, sample_rows: int | None, timeframe: str = '1m', schema: HistoricalCsvSchema | None = None) -> HistoricalValidationSample`
- 作用：Validate a bounded sample or full CSV when `sample_rows` is None.
- 直接原始调用：`tuple` x4, `DataValidationIssue` x2, `issues.append` x2, `DataValidationReport`, `HistoricalCsvStats`, `HistoricalValidationSample`, `ValueError`, `_as_symbol_resolver`, `_group_bars`, `_group_bars().values`, `_is_spread_symbol`, `_row_to_bar`, `bars.append`, `csv.DictReader`, `csv_path.open`, `historical_timeframe_delta`, `issues.extend`, `resolver.is_supported_symbol`, `validate_bars`, `validate_historical_csv_columns`
- 已解析到仓库内部的调用：`qts.data.historical.csv_dataset.HistoricalCsvStats`, `qts.data.historical.csv_dataset.HistoricalValidationSample`, `qts.data.historical.csv_dataset._as_symbol_resolver`, `qts.data.historical.csv_dataset._group_bars`, `qts.data.historical.csv_dataset._is_spread_symbol`, `qts.data.historical.csv_dataset._row_to_bar`, `qts.data.historical.csv_format.historical_timeframe_delta`, `qts.data.historical.csv_format.validate_historical_csv_columns`, `qts.data.validation_report.DataValidationIssue`, `qts.data.validation_report.DataValidationReport`, `qts.data.validation_report.validate_bars`
- 被以下仓库内部符号调用：`scripts.validate_historical.main`

#### `qts.data.historical.csv_dataset._row_to_bar`

- 位置：`backend/src/qts/data/historical/csv_dataset.py:514-537`
- 类型：`module_function`
- 签名：`def _row_to_bar(row: dict, *, symbol_resolver: SourceSymbolResolver, timeframe: str, schema: HistoricalCsvSchema = DEFAULT_HISTORICAL_CSV_SCHEMA) -> Bar`
- 作用：未写 docstring；静态推断为 `row to bar` 函数，具体语义以实现为准。
- 直接原始调用：`Bar`, `_row_ohlcv`, `historical_timeframe_delta`, `parse_historical_ts_event`, `start_time.astimezone`, `start_time.astimezone().date`, `start_time.astimezone().date().isoformat`, `symbol_resolver.instrument_id_for_symbol`
- 已解析到仓库内部的调用：`qts.data.historical.csv_dataset._row_ohlcv`, `qts.data.historical.csv_format.historical_timeframe_delta`, `qts.data.historical.csv_format.parse_historical_ts_event`, `qts.domain.market_data.bar.Bar`
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.HistoricalBarStream._emit_selected_session_rows`, `qts.data.historical.csv_dataset.HistoricalBarStream._iter_all_supported_rows`, `qts.data.historical.csv_dataset.HistoricalBarStream._iter_selected_contract_rows`, `qts.data.historical.csv_dataset.validate_historical_sample`

#### `qts.data.historical.csv_dataset._row_ohlcv`

- 位置：`backend/src/qts/data/historical/csv_dataset.py:540-551`
- 类型：`module_function`
- 签名：`def _row_ohlcv(row: dict, *, schema: HistoricalCsvSchema = DEFAULT_HISTORICAL_CSV_SCHEMA) -> tuple`
- 作用：未写 docstring；静态推断为 `row ohlcv` 函数，具体语义以实现为准。
- 直接原始调用：`_parse_ohlcv_values`
- 已解析到仓库内部的调用：`qts.data.historical.csv_dataset._parse_ohlcv_values`
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.HistoricalBarStream._emit_selected_session_rows`, `qts.data.historical.csv_dataset._row_to_bar`

#### `qts.data.historical.csv_dataset._parse_ohlcv_values`

- 位置：`backend/src/qts/data/historical/csv_dataset.py:554-575`
- 类型：`module_function`
- 签名：`def _parse_ohlcv_values(*, open_value: str, high_value: str, low_value: str, close_value: str, volume_value: str) -> tuple`
- 作用：未写 docstring；静态推断为 `parse ohlcv values` 函数，具体语义以实现为准。
- 直接原始调用：`Decimal` x6, `ValueError` x4, `max`, `min`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset._row_ohlcv`

#### `qts.data.historical.csv_dataset._resolver_root`

- 位置：`backend/src/qts/data/historical/csv_dataset.py:578-582`
- 类型：`module_function`
- 签名：`def _resolver_root(symbol_resolver: SourceSymbolResolver) -> str`
- 作用：未写 docstring；静态推断为 `resolver root` 函数，具体语义以实现为准。
- 直接原始调用：`ValueError`, `getattr`, `isinstance`, `root.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.HistoricalBarStream._resolver_root`

#### `qts.data.historical.csv_dataset._group_bars`

- 位置：`backend/src/qts/data/historical/csv_dataset.py:585-589`
- 类型：`module_function`
- 签名：`def _group_bars(bars: list) -> dict`
- 作用：未写 docstring；静态推断为 `group bars` 函数，具体语义以实现为准。
- 直接原始调用：`defaultdict`, `grouped.append`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.validate_historical_sample`

#### `qts.data.historical.csv_dataset._as_symbol_resolver`

- 位置：`backend/src/qts/data/historical/csv_dataset.py:592-597`
- 类型：`module_function`
- 签名：`def _as_symbol_resolver(value: SourceSymbolResolver | HistoricalChain) -> SourceSymbolResolver`
- 作用：未写 docstring；静态推断为 `as symbol resolver` 函数，具体语义以实现为准。
- 直接原始调用：`HistoricalFutureChainSymbolResolver`, `isinstance`
- 已解析到仓库内部的调用：`qts.data.historical.symbols.HistoricalFutureChainSymbolResolver`
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.iter_historical_bars`, `qts.data.historical.csv_dataset.validate_historical_sample`

#### `qts.data.historical.csv_dataset._is_spread_symbol`

- 位置：`backend/src/qts/data/historical/csv_dataset.py:600-601`
- 类型：`module_function`
- 签名：`def _is_spread_symbol(symbol: str) -> bool`
- 作用：未写 docstring；静态推断为 `is spread symbol` 函数，具体语义以实现为准。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.HistoricalBarStream._count_excluded_symbol`, `qts.data.historical.csv_dataset.validate_historical_sample`

### `backend/src/qts/data/historical/csv_format.py`

模块：`qts.data.historical.csv_format`

#### `qts.data.historical.csv_format.HistoricalCsvSchema`

- 位置：`backend/src/qts/data/historical/csv_format.py:24-81`
- 类型：`class`
- 签名：`class HistoricalCsvSchema`
- 装饰器：`dataclass()`
- 作用：Mapping from framework OHLCV semantics to concrete CSV columns.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.config.HistoricalDataConfig._parse_schemas`

#### `qts.data.historical.csv_format.HistoricalCsvSchema.__post_init__`

- 位置：`backend/src/qts/data/historical/csv_format.py:36-49`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.data.historical.csv_format.HistoricalCsvSchema`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x2, `any`, `item.strip`, `self.instrument_id.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.historical.csv_format.HistoricalCsvSchema.required_columns`

- 位置：`backend/src/qts/data/historical/csv_format.py:52-61`
- 类型：`property`
- 签名：`def required_columns(self) -> tuple`
- 所属：`qts.data.historical.csv_format.HistoricalCsvSchema`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为所属类上的 `required columns` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.historical.csv_format.HistoricalCsvSchema.validate_columns`

- 位置：`backend/src/qts/data/historical/csv_format.py:63-68`
- 类型：`method`
- 签名：`def validate_columns(self, columns: Iterable) -> tuple`
- 所属：`qts.data.historical.csv_format.HistoricalCsvSchema`
- 作用：未写 docstring；静态推断为校验输入、状态或领域约束（名称：validate columns）。
- 直接原始调用：`tuple` x2, `','.join`, `ValueError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.csv_format.HistoricalCsvSchema.column_indices`

#### `qts.data.historical.csv_format.HistoricalCsvSchema.column_indices`

- 位置：`backend/src/qts/data/historical/csv_format.py:70-81`
- 类型：`method`
- 签名：`def column_indices(self, columns: Iterable) -> dict`
- 所属：`qts.data.historical.csv_format.HistoricalCsvSchema`
- 作用：未写 docstring；静态推断为所属类上的 `column indices` 行为。
- 直接原始调用：`enumerate`, `self.validate_columns`
- 已解析到仓库内部的调用：`qts.data.historical.csv_format.HistoricalCsvSchema.validate_columns`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.historical.csv_format.validate_historical_csv_columns`

- 位置：`backend/src/qts/data/historical/csv_format.py:87-101`
- 类型：`module_function`
- 签名：`def validate_historical_csv_columns(columns: tuple, *, schema: HistoricalCsvSchema | None = None) -> None`
- 作用：Validate historical CSV columns against the configured schema.
- 直接原始调用：`','.join` x2, `ValueError`, `schema.validate_columns`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.HistoricalBarStream.__iter__`, `qts.data.historical.csv_dataset.describe_csv_dataset`, `qts.data.historical.csv_dataset.validate_historical_sample`

#### `qts.data.historical.csv_format.parse_historical_ts_event`

- 位置：`backend/src/qts/data/historical/csv_format.py:104-116`
- 类型：`module_function`
- 签名：`def parse_historical_ts_event(value: str) -> datetime`
- 作用：Parse a historical CSV UTC timestamp, accepting nanosecond text input.
- 直接原始调用：`ValueError`, `datetime.fromisoformat`, `parsed.astimezone`, `rest.ljust`, `text.split`, `value.endswith`, `value.removesuffix`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.HistoricalBarStream._timestamp`, `qts.data.historical.csv_dataset.HistoricalBarStream._timestamp_groups`, `qts.data.historical.csv_dataset._row_to_bar`

#### `qts.data.historical.csv_format.historical_timeframe_delta`

- 位置：`backend/src/qts/data/historical/csv_format.py:119-130`
- 类型：`module_function`
- 签名：`def historical_timeframe_delta(timeframe: str) -> timedelta`
- 作用：Return the duration represented by a supported historical timeframe.
- 直接原始调用：`timedelta` x4, `int` x3, `timeframe.endswith` x3, `ValueError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.HistoricalBarStream._emit_selected_session_rows`, `qts.data.historical.csv_dataset._row_to_bar`, `qts.data.historical.csv_dataset.validate_historical_sample`

### `backend/src/qts/data/historical/service.py`

模块：`qts.data.historical.service`

#### `qts.data.historical.service.HistoricalMarketDataService`

- 位置：`backend/src/qts/data/historical/service.py:16-64`
- 类型：`class`
- 签名：`class HistoricalMarketDataService`
- 装饰器：`dataclass()`
- 作用：Deterministic historical market data source with feed-like contracts.
- 直接原始调用：`dataclass`, `field`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.historical.service.HistoricalMarketDataService.__post_init__`

- 位置：`backend/src/qts/data/historical/service.py:27-31`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.data.historical.service.HistoricalMarketDataService`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x2, `self.source_id.strip`, `self.source_timeframe.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.historical.service.HistoricalMarketDataService.capabilities`

- 位置：`backend/src/qts/data/historical/service.py:34-41`
- 类型：`property`
- 签名：`def capabilities(self) -> FeedCapabilities`
- 所属：`qts.data.historical.service.HistoricalMarketDataService`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为所属类上的 `capabilities` 行为。
- 直接原始调用：`FeedCapabilities`, `frozenset`
- 已解析到仓库内部的调用：`qts.data.live_feed.FeedCapabilities`
- 被以下仓库内部符号调用：`qts.data.historical.service.HistoricalMarketDataService.subscribe`

#### `qts.data.historical.service.HistoricalMarketDataService.subscribe`

- 位置：`backend/src/qts/data/historical/service.py:43-46`
- 类型：`method`
- 签名：`def subscribe(self, subscription: FeedSubscription) -> LiveFeedSubscribed`
- 所属：`qts.data.historical.service.HistoricalMarketDataService`
- 作用：未写 docstring；静态推断为所属类上的 `subscribe` 行为。
- 直接原始调用：`LiveFeedSubscribed`, `self.capabilities.source_timeframe_for`
- 已解析到仓库内部的调用：`qts.data.historical.service.HistoricalMarketDataService.capabilities`, `qts.data.live_feed.LiveFeedSubscribed`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.historical.service.HistoricalMarketDataService.events`

- 位置：`backend/src/qts/data/historical/service.py:48-64`
- 类型：`method`
- 签名：`def events(self, subscription_id: str) -> Iterator`
- 所属：`qts.data.historical.service.HistoricalMarketDataService`
- 作用：未写 docstring；静态推断为所属类上的 `events` 行为。
- 直接原始调用：`KeyError`, `LiveFeedEvent`, `ValueError`, `iter_historical_bars`, `subscription_id.strip`
- 已解析到仓库内部的调用：`qts.data.historical.csv_dataset.iter_historical_bars`, `qts.data.live_feed.LiveFeedEvent`
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/data/historical/symbols.py`

模块：`qts.data.historical.symbols`

#### `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver`

- 位置：`backend/src/qts/data/historical/symbols.py:12-25`
- 类型：`class`
- 签名：`class HistoricalFutureChainSymbolResolver`
- 装饰器：`dataclass()`
- 作用：Resolve historical futures outright symbols through chain metadata.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.catalog.HistoricalCatalog.from_historical_data_config`, `qts.data.historical.catalog.HistoricalCatalog.from_legacy_root`, `qts.data.historical.csv_dataset._as_symbol_resolver`

#### `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver.root`

- 位置：`backend/src/qts/data/historical/symbols.py:18-19`
- 类型：`property`
- 签名：`def root(self) -> str`
- 所属：`qts.data.historical.symbols.HistoricalFutureChainSymbolResolver`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为所属类上的 `root` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver.is_supported_symbol`

- 位置：`backend/src/qts/data/historical/symbols.py:21-22`
- 类型：`method`
- 签名：`def is_supported_symbol(self, symbol: str) -> bool`
- 所属：`qts.data.historical.symbols.HistoricalFutureChainSymbolResolver`
- 作用：未写 docstring；静态推断为判断布尔条件（名称：is supported symbol）。
- 直接原始调用：`self.chain.is_outright_symbol`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver.instrument_id_for_symbol`

- 位置：`backend/src/qts/data/historical/symbols.py:24-25`
- 类型：`method`
- 签名：`def instrument_id_for_symbol(self, symbol: str) -> InstrumentId`
- 所属：`qts.data.historical.symbols.HistoricalFutureChainSymbolResolver`
- 作用：未写 docstring；静态推断为所属类上的 `instrument id for symbol` 行为。
- 直接原始调用：`self.chain.instrument_id_for_symbol`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/data/live_feed.py`

模块：`qts.data.live_feed`

#### `qts.data.live_feed.FeedCapabilities`

- 位置：`backend/src/qts/data/live_feed.py:17-69`
- 类型：`class`
- 签名：`class FeedCapabilities`
- 装饰器：`dataclass()`
- 作用：Feed-supported live market data features.
- 直接原始调用：`dataclass`, `frozenset`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.config.HistoricalDataConfig._select_bar_file`, `qts.data.historical.service.HistoricalMarketDataService.capabilities`, `qts.data.live_feed.FakeLiveFeedAdapter.capabilities`

#### `qts.data.live_feed.FeedCapabilities.__post_init__`

- 位置：`backend/src/qts/data/live_feed.py:27-33`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.data.live_feed.FeedCapabilities`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x3, `any`, `item.strip`, `self.source_id.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.live_feed.FeedCapabilities.supports_timeframe`

- 位置：`backend/src/qts/data/live_feed.py:35-38`
- 类型：`method`
- 签名：`def supports_timeframe(self, timeframe: str) -> bool`
- 所属：`qts.data.live_feed.FeedCapabilities`
- 作用：未写 docstring；静态推断为所属类上的 `supports timeframe` 行为。
- 直接原始调用：`ValueError`, `timeframe.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.live_feed.FeedCapabilities.source_timeframe_for`

#### `qts.data.live_feed.FeedCapabilities.source_timeframe_for`

- 位置：`backend/src/qts/data/live_feed.py:40-69`
- 类型：`method`
- 签名：`def source_timeframe_for(self, requested_timeframe: str) -> str`
- 所属：`qts.data.live_feed.FeedCapabilities`
- 作用：Return the provider timeframe needed to satisfy a requested bar stream.
- 直接原始调用：`ValueError` x3, `requested_timeframe.strip`, `self.supports_timeframe`
- 已解析到仓库内部的调用：`qts.data.live_feed.FeedCapabilities.supports_timeframe`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.live_feed.FeedSubscription`

- 位置：`backend/src/qts/data/live_feed.py:73-84`
- 类型：`class`
- 签名：`class FeedSubscription`
- 装饰器：`dataclass()`
- 作用：Internal live feed subscription request.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.actors.market_data_actor.MarketDataActor._subscribe`

#### `qts.data.live_feed.FeedSubscription.__post_init__`

- 位置：`backend/src/qts/data/live_feed.py:80-84`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.data.live_feed.FeedSubscription`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x2, `self.subscription_id.strip`, `self.timeframe.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.live_feed.LiveFeedSubscribed`

- 位置：`backend/src/qts/data/live_feed.py:88-90`
- 类型：`class`
- 签名：`class LiveFeedSubscribed`
- 装饰器：`dataclass()`
- 作用：未写 docstring；静态推断为定义 Live Feed Subscribed 概念或数据结构。
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.service.HistoricalMarketDataService.subscribe`, `qts.data.live_feed.FakeLiveFeedAdapter.subscribe`

#### `qts.data.live_feed.LiveFeedEvent`

- 位置：`backend/src/qts/data/live_feed.py:94-96`
- 类型：`class`
- 签名：`class LiveFeedEvent`
- 装饰器：`dataclass()`
- 作用：未写 docstring；静态推断为定义 Live Feed Event 概念或数据结构。
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.service.HistoricalMarketDataService.events`, `qts.data.live_feed.FakeLiveFeedAdapter.emit`

#### `qts.data.live_feed.LiveFeedFailure`

- 位置：`backend/src/qts/data/live_feed.py:100-107`
- 类型：`class`
- 签名：`class LiveFeedFailure`
- 装饰器：`dataclass()`
- 作用：未写 docstring；静态推断为定义 Live Feed Failure 概念或数据结构。
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.live_feed.FakeLiveFeedAdapter.fail`

#### `qts.data.live_feed.LiveFeedFailure.__post_init__`

- 位置：`backend/src/qts/data/live_feed.py:105-107`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.data.live_feed.LiveFeedFailure`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError`, `self.reason.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.live_feed.ReconnectPolicy`

- 位置：`backend/src/qts/data/live_feed.py:111-135`
- 类型：`class`
- 签名：`class ReconnectPolicy`
- 装饰器：`dataclass()`
- 作用：Deterministic reconnect backoff policy.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.live_feed.ReconnectPolicy.__post_init__`

- 位置：`backend/src/qts/data/live_feed.py:119-127`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.data.live_feed.ReconnectPolicy`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x4, `Decimal`, `timedelta`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.live_feed.ReconnectPolicy.delay_for_attempt`

- 位置：`backend/src/qts/data/live_feed.py:129-135`
- 类型：`method`
- 签名：`def delay_for_attempt(self, attempt: int) -> timedelta | None`
- 所属：`qts.data.live_feed.ReconnectPolicy`
- 作用：未写 docstring；静态推断为所属类上的 `delay for attempt` 行为。
- 直接原始调用：`ValueError`, `float`, `min`, `self.initial_delay.total_seconds`, `timedelta`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.live_feed.LiveFeedAdapter`

- 位置：`backend/src/qts/data/live_feed.py:138-142`
- 类型：`class`
- 签名：`class LiveFeedAdapter(Protocol)`
- 继承/基类：`Protocol`
- 作用：未写 docstring；静态推断为定义 Live Feed Adapter 概念，继承/实现 Protocol。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.live_feed.LiveFeedAdapter.capabilities`

- 位置：`backend/src/qts/data/live_feed.py:140-140`
- 类型：`property`
- 签名：`def capabilities(self) -> FeedCapabilities`
- 所属：`qts.data.live_feed.LiveFeedAdapter`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为所属类上的 `capabilities` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.live_feed.LiveFeedAdapter.subscribe`

- 位置：`backend/src/qts/data/live_feed.py:142-142`
- 类型：`method`
- 签名：`def subscribe(self, subscription: FeedSubscription) -> LiveFeedSubscribed`
- 所属：`qts.data.live_feed.LiveFeedAdapter`
- 作用：未写 docstring；静态推断为所属类上的 `subscribe` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.live_feed.FakeLiveFeedAdapter`

- 位置：`backend/src/qts/data/live_feed.py:145-184`
- 类型：`class`
- 签名：`class FakeLiveFeedAdapter`
- 作用：Deterministic fake live market data feed.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.live_feed.FakeLiveFeedAdapter.__init__`

- 位置：`backend/src/qts/data/live_feed.py:148-160`
- 类型：`method`
- 签名：`def __init__(self, *, source_id: str, capabilities: FeedCapabilities | None = None) -> None`
- 所属：`qts.data.live_feed.FakeLiveFeedAdapter`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：`ValueError` x2, `source_id.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.live_feed.FakeLiveFeedAdapter.capabilities`

- 位置：`backend/src/qts/data/live_feed.py:163-164`
- 类型：`property`
- 签名：`def capabilities(self) -> FeedCapabilities`
- 所属：`qts.data.live_feed.FakeLiveFeedAdapter`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为所属类上的 `capabilities` 行为。
- 直接原始调用：`FeedCapabilities`
- 已解析到仓库内部的调用：`qts.data.live_feed.FeedCapabilities`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.live_feed.FakeLiveFeedAdapter.subscription_count`

- 位置：`backend/src/qts/data/live_feed.py:167-168`
- 类型：`property`
- 签名：`def subscription_count(self) -> int`
- 所属：`qts.data.live_feed.FakeLiveFeedAdapter`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为所属类上的 `subscription count` 行为。
- 直接原始调用：`len`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.live_feed.FakeLiveFeedAdapter.subscribe`

- 位置：`backend/src/qts/data/live_feed.py:170-172`
- 类型：`method`
- 签名：`def subscribe(self, subscription: FeedSubscription) -> LiveFeedSubscribed`
- 所属：`qts.data.live_feed.FakeLiveFeedAdapter`
- 作用：未写 docstring；静态推断为所属类上的 `subscribe` 行为。
- 直接原始调用：`LiveFeedSubscribed`
- 已解析到仓库内部的调用：`qts.data.live_feed.LiveFeedSubscribed`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.live_feed.FakeLiveFeedAdapter.emit`

- 位置：`backend/src/qts/data/live_feed.py:174-175`
- 类型：`method`
- 签名：`def emit(self, payload: LiveFeedPayload) -> LiveFeedEvent`
- 所属：`qts.data.live_feed.FakeLiveFeedAdapter`
- 作用：未写 docstring；静态推断为所属类上的 `emit` 行为。
- 直接原始调用：`LiveFeedEvent`
- 已解析到仓库内部的调用：`qts.data.live_feed.LiveFeedEvent`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.live_feed.FakeLiveFeedAdapter.fail`

- 位置：`backend/src/qts/data/live_feed.py:177-184`
- 类型：`method`
- 签名：`def fail(self, subscription_id: str, *, reason: str) -> LiveFeedFailure`
- 所属：`qts.data.live_feed.FakeLiveFeedAdapter`
- 作用：未写 docstring；静态推断为所属类上的 `fail` 行为。
- 直接原始调用：`KeyError`, `LiveFeedFailure`
- 已解析到仓库内部的调用：`qts.data.live_feed.LiveFeedFailure`
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/data/normalization/__init__.py`

模块：`qts.data.normalization`

无类或函数定义。

### `backend/src/qts/data/provenance.py`

模块：`qts.data.provenance`

#### `qts.data.provenance.DatasetMetadata`

- 位置：`backend/src/qts/data/provenance.py:13-45`
- 类型：`class`
- 签名：`class DatasetMetadata`
- 装饰器：`dataclass()`
- 作用：Stable reference to historical data used by simulation or research.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.inputs.BacktestInputBuilder._dataset_metadata`

#### `qts.data.provenance.DatasetMetadata.__post_init__`

- 位置：`backend/src/qts/data/provenance.py:26-35`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.data.provenance.DatasetMetadata`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`self._require_text` x7, `require_aware_datetime`
- 已解析到仓库内部的调用：`qts.core.time.require_aware_datetime`, `qts.data.provenance.DatasetMetadata._require_text`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.provenance.DatasetMetadata.reference`

- 位置：`backend/src/qts/data/provenance.py:38-40`
- 类型：`property`
- 签名：`def reference(self) -> str`
- 所属：`qts.data.provenance.DatasetMetadata`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为所属类上的 `reference` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.provenance.DatasetMetadata._require_text`

- 位置：`backend/src/qts/data/provenance.py:43-45`
- 类型：`staticmethod`
- 签名：`def _require_text(value: str, name: str) -> None`
- 所属：`qts.data.provenance.DatasetMetadata`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `require text` 行为。
- 直接原始调用：`ValueError`, `value.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.provenance.DatasetMetadata.__post_init__`

### `backend/src/qts/data/sessions/__init__.py`

模块：`qts.data.sessions`

无类或函数定义。

### `backend/src/qts/data/sessions/filter.py`

模块：`qts.data.sessions.filter`

#### `qts.data.sessions.filter.SessionLookup`

- 位置：`backend/src/qts/data/sessions/filter.py:13-17`
- 类型：`class`
- 签名：`class SessionLookup(Protocol)`
- 继承/基类：`Protocol`
- 作用：Calendar session lookup required by session filters.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.sessions.filter.SessionLookup.session_for`

- 位置：`backend/src/qts/data/sessions/filter.py:16-17`
- 类型：`method`
- 签名：`def session_for(self, calendar_id: str, session_date: date) -> MarketSession`
- 所属：`qts.data.sessions.filter.SessionLookup`
- 作用：Return the internal market session for the date.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.sessions.filter.filter_session_bars`

- 位置：`backend/src/qts/data/sessions/filter.py:20-30`
- 类型：`module_function`
- 签名：`def filter_session_bars(bars: Iterable, *, calendar_registry: SessionLookup, calendar_id: str, session_date: date) -> list`
- 作用：Return bars whose start and end fall inside the half-open session.
- 直接原始调用：`_bar_inside_session`, `calendar_registry.session_for`
- 已解析到仓库内部的调用：`qts.data.sessions.filter._bar_inside_session`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.sessions.filter._bar_inside_session`

- 位置：`backend/src/qts/data/sessions/filter.py:33-38`
- 类型：`module_function`
- 签名：`def _bar_inside_session(bar: Bar, session: MarketSession) -> bool`
- 作用：未写 docstring；静态推断为 `bar inside session` 函数，具体语义以实现为准。
- 直接原始调用：`session.interval.contains`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.sessions.filter.filter_session_bars`

### `backend/src/qts/data/sessions/window.py`

模块：`qts.data.sessions.window`

#### `qts.data.sessions.window.RegularSessionWindow`

- 位置：`backend/src/qts/data/sessions/window.py:12-57`
- 类型：`class`
- 签名：`class RegularSessionWindow`
- 装饰器：`dataclass()`
- 作用：A recurring half-open exchange session window. The session id is the exchange-local close date. For overnight sessions this means a bar at or after the open belongs to the next local date's session.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.sessions.window.RegularSessionWindow.__post_init__`

- 位置：`backend/src/qts/data/sessions/window.py:23-27`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.data.sessions.window.RegularSessionWindow`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x2, `self.exchange_timezone.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.sessions.window.RegularSessionWindow.session_id_for_timestamp`

- 位置：`backend/src/qts/data/sessions/window.py:29-33`
- 类型：`method`
- 签名：`def session_id_for_timestamp(self, timestamp: datetime) -> str | None`
- 所属：`qts.data.sessions.window.RegularSessionWindow`
- 作用：Return the exchange-local close-date session id containing timestamp.
- 直接原始调用：`self.session_date_for_timestamp`, `session_date.isoformat`
- 已解析到仓库内部的调用：`qts.data.sessions.window.RegularSessionWindow.session_date_for_timestamp`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.sessions.window.RegularSessionWindow.session_date_for_timestamp`

- 位置：`backend/src/qts/data/sessions/window.py:35-48`
- 类型：`method`
- 签名：`def session_date_for_timestamp(self, timestamp: datetime) -> date | None`
- 所属：`qts.data.sessions.window.RegularSessionWindow`
- 作用：Return the exchange-local close date for timestamp, or None if outside.
- 直接原始调用：`local_timestamp.date` x3, `local_timestamp.time`, `timedelta`, `to_exchange_time`
- 已解析到仓库内部的调用：`qts.core.time.to_exchange_time`
- 被以下仓库内部符号调用：`qts.data.sessions.window.RegularSessionWindow.session_id_for_timestamp`

#### `qts.data.sessions.window.RegularSessionWindow.to_payload`

- 位置：`backend/src/qts/data/sessions/window.py:50-57`
- 类型：`method`
- 签名：`def to_payload(self) -> dict`
- 所属：`qts.data.sessions.window.RegularSessionWindow`
- 作用：Return a stable JSON-serializable description of the session rule.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/data/stores/__init__.py`

模块：`qts.data.stores`

无类或函数定义。

### `backend/src/qts/data/stores/base.py`

模块：`qts.data.stores.base`

#### `qts.data.stores.base.MarketDataStore`

- 位置：`backend/src/qts/data/stores/base.py:13-25`
- 类型：`class`
- 签名：`class MarketDataStore(Protocol)`
- 继承/基类：`Protocol`
- 作用：Store and read bars by internal instrument identity.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.stores.base.MarketDataStore.write_bars`

- 位置：`backend/src/qts/data/stores/base.py:16-16`
- 类型：`method`
- 签名：`def write_bars(self, bars: Iterable) -> None`
- 所属：`qts.data.stores.base.MarketDataStore`
- 作用：未写 docstring；静态推断为写入数据（名称：write bars）。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.stores.base.MarketDataStore.read_bars`

- 位置：`backend/src/qts/data/stores/base.py:18-25`
- 类型：`method`
- 签名：`def read_bars(self, *, instrument_id: InstrumentId, timeframe: str, start: datetime, end: datetime) -> tuple`
- 所属：`qts.data.stores.base.MarketDataStore`
- 作用：未写 docstring；静态推断为读取数据（名称：read bars）。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/data/stores/memory_store.py`

模块：`qts.data.stores.memory_store`

#### `qts.data.stores.memory_store.InMemoryMarketDataStore`

- 位置：`backend/src/qts/data/stores/memory_store.py:13-37`
- 类型：`class`
- 签名：`class InMemoryMarketDataStore`
- 作用：In-memory bar store for tests and local runs.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.stores.memory_store.InMemoryMarketDataStore.__init__`

- 位置：`backend/src/qts/data/stores/memory_store.py:16-17`
- 类型：`method`
- 签名：`def __init__(self) -> None`
- 所属：`qts.data.stores.memory_store.InMemoryMarketDataStore`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：`defaultdict`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.stores.memory_store.InMemoryMarketDataStore.write_bars`

- 位置：`backend/src/qts/data/stores/memory_store.py:19-23`
- 类型：`method`
- 签名：`def write_bars(self, bars: Iterable) -> None`
- 所属：`qts.data.stores.memory_store.InMemoryMarketDataStore`
- 作用：未写 docstring；静态推断为写入数据（名称：write bars）。
- 直接原始调用：`self._bars.append`, `self._bars.sort`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.stores.memory_store.InMemoryMarketDataStore.read_bars`

- 位置：`backend/src/qts/data/stores/memory_store.py:25-37`
- 类型：`method`
- 签名：`def read_bars(self, *, instrument_id: InstrumentId, timeframe: str, start: datetime, end: datetime) -> tuple`
- 所属：`qts.data.stores.memory_store.InMemoryMarketDataStore`
- 作用：未写 docstring；静态推断为读取数据（名称：read bars）。
- 直接原始调用：`self._bars.get`, `tuple`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/data/stores/parquet_store.py`

模块：`qts.data.stores.parquet_store`

#### `qts.data.stores.parquet_store.ParquetMarketDataStore`

- 位置：`backend/src/qts/data/stores/parquet_store.py:21-115`
- 类型：`class`
- 签名：`class ParquetMarketDataStore`
- 作用：File-backed bar store partitioned by instrument, timeframe, and date.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.stores.parquet_store.ParquetMarketDataStore.__init__`

- 位置：`backend/src/qts/data/stores/parquet_store.py:24-25`
- 类型：`method`
- 签名：`def __init__(self, root: Path) -> None`
- 所属：`qts.data.stores.parquet_store.ParquetMarketDataStore`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.stores.parquet_store.ParquetMarketDataStore.write_bars`

- 位置：`backend/src/qts/data/stores/parquet_store.py:27-41`
- 类型：`method`
- 签名：`def write_bars(self, bars: Iterable) -> None`
- 所属：`qts.data.stores.parquet_store.ParquetMarketDataStore`
- 作用：未写 docstring；静态推断为写入数据（名称：write bars）。
- 直接原始调用：`handle.write` x2, `grouped.items`, `grouped.setdefault`, `grouped.setdefault().append`, `json.dumps`, `list`, `path.exists`, `path.open`, `path.parent.mkdir`, `self._bar_to_json`, `self._path_for`, `self._read_file`, `sorted`
- 已解析到仓库内部的调用：`qts.data.stores.parquet_store.ParquetMarketDataStore._bar_to_json`, `qts.data.stores.parquet_store.ParquetMarketDataStore._path_for`, `qts.data.stores.parquet_store.ParquetMarketDataStore._read_file`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.stores.parquet_store.ParquetMarketDataStore.read_bars`

- 位置：`backend/src/qts/data/stores/parquet_store.py:43-61`
- 类型：`method`
- 签名：`def read_bars(self, *, instrument_id: InstrumentId, timeframe: str, start: datetime, end: datetime) -> tuple`
- 所属：`qts.data.stores.parquet_store.ParquetMarketDataStore`
- 作用：未写 docstring；静态推断为读取数据（名称：read bars）。
- 直接原始调用：`sorted` x2, `bars.extend`, `base.exists`, `base.glob`, `self._read_file`, `tuple`
- 已解析到仓库内部的调用：`qts.data.stores.parquet_store.ParquetMarketDataStore._read_file`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.stores.parquet_store.ParquetMarketDataStore._path_for`

- 位置：`backend/src/qts/data/stores/parquet_store.py:63-69`
- 类型：`method`
- 签名：`def _path_for(self, bar: Bar) -> Path`
- 所属：`qts.data.stores.parquet_store.ParquetMarketDataStore`
- 作用：未写 docstring；静态推断为所属类上的 `path for` 行为。
- 直接原始调用：`bar.start_time.date`, `bar.start_time.date().isoformat`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.stores.parquet_store.ParquetMarketDataStore.write_bars`

#### `qts.data.stores.parquet_store.ParquetMarketDataStore._read_file`

- 位置：`backend/src/qts/data/stores/parquet_store.py:71-73`
- 类型：`method`
- 签名：`def _read_file(self, path: Path) -> tuple`
- 所属：`qts.data.stores.parquet_store.ParquetMarketDataStore`
- 作用：未写 docstring；静态推断为所属类上的 `read file` 行为。
- 直接原始调用：`json.loads`, `line.strip`, `path.open`, `self._bar_from_json`, `tuple`
- 已解析到仓库内部的调用：`qts.data.stores.parquet_store.ParquetMarketDataStore._bar_from_json`
- 被以下仓库内部符号调用：`qts.data.stores.parquet_store.ParquetMarketDataStore.read_bars`, `qts.data.stores.parquet_store.ParquetMarketDataStore.write_bars`

#### `qts.data.stores.parquet_store.ParquetMarketDataStore._bar_to_json`

- 位置：`backend/src/qts/data/stores/parquet_store.py:76-93`
- 类型：`staticmethod`
- 签名：`def _bar_to_json(bar: Bar) -> dict`
- 所属：`qts.data.stores.parquet_store.ParquetMarketDataStore`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `bar to json` 行为。
- 直接原始调用：`str` x7, `bar.end_time.isoformat`, `bar.start_time.isoformat`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.stores.parquet_store.ParquetMarketDataStore.write_bars`

#### `qts.data.stores.parquet_store.ParquetMarketDataStore._bar_from_json`

- 位置：`backend/src/qts/data/stores/parquet_store.py:96-115`
- 类型：`staticmethod`
- 签名：`def _bar_from_json(payload: dict) -> Bar`
- 所属：`qts.data.stores.parquet_store.ParquetMarketDataStore`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `bar from json` 行为。
- 直接原始调用：`str` x12, `Decimal` x7, `bool` x2, `datetime.fromisoformat` x2, `Bar`, `InstrumentId`, `int`
- 已解析到仓库内部的调用：`qts.core.ids.InstrumentId`, `qts.domain.market_data.bar.Bar`
- 被以下仓库内部符号调用：`qts.data.stores.parquet_store.ParquetMarketDataStore._read_file`

### `backend/src/qts/data/subscriptions.py`

模块：`qts.data.subscriptions`

#### `qts.data.subscriptions.SourceStreamType`

- 位置：`backend/src/qts/data/subscriptions.py:12-17`
- 类型：`class`
- 签名：`class SourceStreamType(StrEnum)`
- 继承/基类：`StrEnum`
- 作用：Physical market data stream type.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.subscriptions.LogicalSubscription`

- 位置：`backend/src/qts/data/subscriptions.py:21-33`
- 类型：`class`
- 签名：`class LogicalSubscription`
- 装饰器：`dataclass()`
- 作用：Strategy-requested market data stream.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.actors.market_data_actor.MarketDataActor._subscribe`

#### `qts.data.subscriptions.LogicalSubscription.__post_init__`

- 位置：`backend/src/qts/data/subscriptions.py:29-33`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.data.subscriptions.LogicalSubscription`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x2, `self.requested_timeframe.strip`, `self.subscriber_id.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.subscriptions.LogicalSubscriptionKey`

- 位置：`backend/src/qts/data/subscriptions.py:37-42`
- 类型：`class`
- 签名：`class LogicalSubscriptionKey`
- 装饰器：`dataclass()`
- 作用：Deduplication key for strategy-facing subscribers.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.subscriptions.logical_key`

#### `qts.data.subscriptions.PhysicalSubscriptionKey`

- 位置：`backend/src/qts/data/subscriptions.py:46-58`
- 类型：`class`
- 签名：`class PhysicalSubscriptionKey`
- 装饰器：`dataclass()`
- 作用：Deduplication key for provider-facing subscriptions.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.subscriptions.plan_physical_subscription`

#### `qts.data.subscriptions.PhysicalSubscriptionKey.__post_init__`

- 位置：`backend/src/qts/data/subscriptions.py:54-58`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.data.subscriptions.PhysicalSubscriptionKey`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x2, `self.source_id.strip`, `self.source_timeframe.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.subscriptions.logical_key`

- 位置：`backend/src/qts/data/subscriptions.py:61-68`
- 类型：`module_function`
- 签名：`def logical_key(subscription: LogicalSubscription) -> LogicalSubscriptionKey`
- 作用：Return the logical fan-out key for a subscription.
- 直接原始调用：`LogicalSubscriptionKey`
- 已解析到仓库内部的调用：`qts.data.subscriptions.LogicalSubscriptionKey`
- 被以下仓库内部符号调用：`qts.runtime.actors.market_data_actor.MarketDataActor._subscribe`

#### `qts.data.subscriptions.plan_physical_subscription`

- 位置：`backend/src/qts/data/subscriptions.py:71-85`
- 类型：`module_function`
- 签名：`def plan_physical_subscription(subscription: LogicalSubscription, *, capabilities: FeedCapabilities) -> PhysicalSubscriptionKey`
- 作用：Map one logical subscription to its provider source subscription.
- 直接原始调用：`PhysicalSubscriptionKey`, `ValueError`, `capabilities.source_timeframe_for`
- 已解析到仓库内部的调用：`qts.data.subscriptions.PhysicalSubscriptionKey`
- 被以下仓库内部符号调用：`qts.runtime.actors.market_data_actor.MarketDataActor._subscribe`

### `backend/src/qts/data/validation_report.py`

模块：`qts.data.validation_report`

#### `qts.data.validation_report.DataValidationIssueCode`

- 位置：`backend/src/qts/data/validation_report.py:13-24`
- 类型：`class`
- 签名：`class DataValidationIssueCode(StrEnum)`
- 继承/基类：`StrEnum`
- 作用：Known market data validation issue codes.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.validation_report.DataValidationSeverity`

- 位置：`backend/src/qts/data/validation_report.py:27-32`
- 类型：`class`
- 签名：`class DataValidationSeverity(StrEnum)`
- 继承/基类：`StrEnum`
- 作用：Severity for data validation issues.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.validation_report.DataValidationIssue`

- 位置：`backend/src/qts/data/validation_report.py:36-41`
- 类型：`class`
- 签名：`class DataValidationIssue`
- 装饰器：`dataclass()`
- 作用：One validation issue for a bar sequence.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.validate_historical_sample`, `qts.data.validation_report._append_ohlc_issue`, `qts.data.validation_report.validate_bars`

#### `qts.data.validation_report.DataValidationReport`

- 位置：`backend/src/qts/data/validation_report.py:45-63`
- 类型：`class`
- 签名：`class DataValidationReport`
- 装饰器：`dataclass()`
- 作用：Validation result for a bar sequence.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.validate_historical_sample`, `qts.data.validation_report.validate_bars`

#### `qts.data.validation_report.DataValidationReport.valid`

- 位置：`backend/src/qts/data/validation_report.py:51-52`
- 类型：`property`
- 签名：`def valid(self) -> bool`
- 所属：`qts.data.validation_report.DataValidationReport`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为所属类上的 `valid` 行为。
- 直接原始调用：`any`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.validation_report.DataValidationReport.max_severity`

- 位置：`backend/src/qts/data/validation_report.py:55-63`
- 类型：`property`
- 签名：`def max_severity(self) -> DataValidationSeverity | None`
- 所属：`qts.data.validation_report.DataValidationReport`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为所属类上的 `max severity` 行为。
- 直接原始调用：`max`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.data.validation_report.validate_bars`

- 位置：`backend/src/qts/data/validation_report.py:66-140`
- 类型：`module_function`
- 签名：`def validate_bars(bars: tuple, *, session_interval: TimeInterval | None = None, expected_interval: timedelta | None = None) -> DataValidationReport`
- 作用：Validate bar ordering, overlap, and optional session containment.
- 直接原始调用：`DataValidationIssue` x6, `issues.append` x6, `bar.start_time.isoformat` x5, `tuple` x2, `DataValidationReport`, `ValueError`, `_append_ohlc_issue`, `int`, `previous.end_time.isoformat`, `session_interval.contains`, `sorted`, `timedelta`
- 已解析到仓库内部的调用：`qts.data.validation_report.DataValidationIssue`, `qts.data.validation_report.DataValidationReport`, `qts.data.validation_report._append_ohlc_issue`
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.validate_historical_sample`

#### `qts.data.validation_report._append_ohlc_issue`

- 位置：`backend/src/qts/data/validation_report.py:143-154`
- 类型：`module_function`
- 签名：`def _append_ohlc_issue(issues: list, bar: Bar) -> None`
- 作用：未写 docstring；静态推断为 `append ohlc issue` 函数，具体语义以实现为准。
- 直接原始调用：`DataValidationIssue`, `bar.start_time.isoformat`, `issues.append`, `max`, `min`
- 已解析到仓库内部的调用：`qts.data.validation_report.DataValidationIssue`
- 被以下仓库内部符号调用：`qts.data.validation_report.validate_bars`

### `backend/src/qts/domain/__init__.py`

模块：`qts.domain`

无类或函数定义。

### `backend/src/qts/domain/events/__init__.py`

模块：`qts.domain.events`

无类或函数定义。

### `backend/src/qts/domain/events/event.py`

模块：`qts.domain.events.event`

#### `qts.domain.events.event.BaseEvent`

- 位置：`backend/src/qts/domain/events/event.py:13-31`
- 类型：`class`
- 签名：`class BaseEvent`
- 装饰器：`dataclass()`
- 作用：Minimal event envelope used for traceable internal messages.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.event_store.FileEventStore._event_from_json`

#### `qts.domain.events.event.BaseEvent.__post_init__`

- 位置：`backend/src/qts/domain/events/event.py:24-31`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.domain.events.event.BaseEvent`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x3, `require_aware_datetime`, `self.event_type.strip`, `self.partition_key.strip`, `self.source.strip`
- 已解析到仓库内部的调用：`qts.core.time.require_aware_datetime`
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/domain/events/metadata.py`

模块：`qts.domain.events.metadata`

#### `qts.domain.events.metadata.EventMetadata`

- 位置：`backend/src/qts/domain/events/metadata.py:21-48`
- 类型：`class`
- 签名：`class EventMetadata`
- 装饰器：`dataclass()`
- 作用：Trace metadata carried by platform events.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.domain.events.metadata.EventMetadata.__post_init__`

- 位置：`backend/src/qts/domain/events/metadata.py:39-48`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.domain.events.metadata.EventMetadata`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x3, `require_aware_datetime` x2, `self.event_type.strip`, `self.partition_key.strip`
- 已解析到仓库内部的调用：`qts.core.time.require_aware_datetime`
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/domain/instruments/__init__.py`

模块：`qts.domain.instruments`

无类或函数定义。

### `backend/src/qts/domain/instruments/contract_spec.py`

模块：`qts.domain.instruments.contract_spec`

#### `qts.domain.instruments.contract_spec.SettlementType`

- 位置：`backend/src/qts/domain/instruments/contract_spec.py:10-14`
- 类型：`class`
- 签名：`class SettlementType(StrEnum)`
- 继承/基类：`StrEnum`
- 作用：How a contract settles.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.domain.instruments.contract_spec.ContractSpec`

- 位置：`backend/src/qts/domain/instruments/contract_spec.py:18-37`
- 类型：`class`
- 签名：`class ContractSpec`
- 装饰器：`dataclass()`
- 作用：Trading contract metadata required for valuation and order sizing.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._instrument_registry_for`, `qts.backtest.inputs.BacktestInputBuilder._instrument_for`

#### `qts.domain.instruments.contract_spec.ContractSpec.__post_init__`

- 位置：`backend/src/qts/domain/instruments/contract_spec.py:27-32`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.domain.instruments.contract_spec.ContractSpec`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`self._require_positive` x3, `ValueError`, `self.calendar_id.strip`
- 已解析到仓库内部的调用：`qts.domain.instruments.contract_spec.ContractSpec._require_positive`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.domain.instruments.contract_spec.ContractSpec._require_positive`

- 位置：`backend/src/qts/domain/instruments/contract_spec.py:35-37`
- 类型：`staticmethod`
- 签名：`def _require_positive(value: Decimal, name: str) -> None`
- 所属：`qts.domain.instruments.contract_spec.ContractSpec`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `require positive` 行为。
- 直接原始调用：`Decimal`, `ValueError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.domain.instruments.contract_spec.ContractSpec.__post_init__`

### `backend/src/qts/domain/instruments/derivative_spec.py`

模块：`qts.domain.instruments.derivative_spec`

#### `qts.domain.instruments.derivative_spec.OptionRight`

- 位置：`backend/src/qts/domain/instruments/derivative_spec.py:13-17`
- 类型：`class`
- 签名：`class OptionRight(StrEnum)`
- 继承/基类：`StrEnum`
- 作用：Option payoff direction.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.domain.instruments.derivative_spec.ExerciseStyle`

- 位置：`backend/src/qts/domain/instruments/derivative_spec.py:20-24`
- 类型：`class`
- 签名：`class ExerciseStyle(StrEnum)`
- 继承/基类：`StrEnum`
- 作用：Option exercise style.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.domain.instruments.derivative_spec.DerivativeSpec`

- 位置：`backend/src/qts/domain/instruments/derivative_spec.py:28-32`
- 类型：`class`
- 签名：`class DerivativeSpec`
- 装饰器：`dataclass()`
- 作用：Common derivative metadata.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.domain.instruments.derivative_spec.FutureSpec`

- 位置：`backend/src/qts/domain/instruments/derivative_spec.py:36-43`
- 类型：`class`
- 签名：`class FutureSpec(DerivativeSpec)`
- 继承/基类：`DerivativeSpec`
- 装饰器：`dataclass()`
- 作用：Future contract metadata.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.domain.instruments.derivative_spec.FutureSpec.__post_init__`

- 位置：`backend/src/qts/domain/instruments/derivative_spec.py:41-43`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.domain.instruments.derivative_spec.FutureSpec`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError`, `self.root_symbol.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.domain.instruments.derivative_spec.OptionSpec`

- 位置：`backend/src/qts/domain/instruments/derivative_spec.py:47-56`
- 类型：`class`
- 签名：`class OptionSpec(DerivativeSpec)`
- 继承/基类：`DerivativeSpec`
- 装饰器：`dataclass()`
- 作用：Option contract metadata.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.domain.instruments.derivative_spec.OptionSpec.__post_init__`

- 位置：`backend/src/qts/domain/instruments/derivative_spec.py:54-56`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.domain.instruments.derivative_spec.OptionSpec`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`Decimal`, `ValueError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/domain/instruments/instrument.py`

模块：`qts.domain.instruments.instrument`

#### `qts.domain.instruments.instrument.AssetClass`

- 位置：`backend/src/qts/domain/instruments/instrument.py:19-24`
- 类型：`class`
- 签名：`class AssetClass(StrEnum)`
- 继承/基类：`StrEnum`
- 作用：Supported instrument asset classes.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.domain.instruments.instrument.Instrument`

- 位置：`backend/src/qts/domain/instruments/instrument.py:28-49`
- 类型：`class`
- 签名：`class Instrument`
- 装饰器：`dataclass()`
- 作用：Tradable instrument identified by a stable internal InstrumentId.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._instrument_registry_for`, `qts.backtest.inputs.BacktestInputBuilder._instrument_for`

#### `qts.domain.instruments.instrument.Instrument.__post_init__`

- 位置：`backend/src/qts/domain/instruments/instrument.py:39-49`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.domain.instruments.instrument.Instrument`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x5, `isinstance` x2, `self.currency.strip`, `self.exchange.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/domain/market_data/__init__.py`

模块：`qts.domain.market_data`

无类或函数定义。

### `backend/src/qts/domain/market_data/bar.py`

模块：`qts.domain.market_data.bar`

#### `qts.domain.market_data.bar.Bar`

- 位置：`backend/src/qts/domain/market_data/bar.py:14-60`
- 类型：`class`
- 签名：`class Bar`
- 装饰器：`dataclass()`
- 作用：OHLCV bar over a half-open interval.
- 直接原始调用：`Decimal`, `dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter.normalize_bar`, `qts.data.bars.aggregator._aggregate_state`, `qts.data.historical.csv_dataset._row_to_bar`, `qts.data.stores.parquet_store.ParquetMarketDataStore._bar_from_json`, `qts.load.synthetic_market_data.generate_bars`

#### `qts.domain.market_data.bar.Bar.__post_init__`

- 位置：`backend/src/qts/domain/market_data/bar.py:33-51`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.domain.market_data.bar.Bar`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x6, `self._require_non_negative` x3, `TimeInterval`, `max`, `min`, `self.session_id.strip`, `self.timeframe.strip`
- 已解析到仓库内部的调用：`qts.core.time.TimeInterval`, `qts.domain.market_data.bar.Bar._require_non_negative`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.domain.market_data.bar.Bar.interval`

- 位置：`backend/src/qts/domain/market_data/bar.py:54-55`
- 类型：`property`
- 签名：`def interval(self) -> TimeInterval`
- 所属：`qts.domain.market_data.bar.Bar`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为所属类上的 `interval` 行为。
- 直接原始调用：`TimeInterval`
- 已解析到仓库内部的调用：`qts.core.time.TimeInterval`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.domain.market_data.bar.Bar._require_non_negative`

- 位置：`backend/src/qts/domain/market_data/bar.py:58-60`
- 类型：`staticmethod`
- 签名：`def _require_non_negative(value: Decimal, name: str) -> None`
- 所属：`qts.domain.market_data.bar.Bar`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `require non negative` 行为。
- 直接原始调用：`Decimal`, `ValueError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.domain.market_data.bar.Bar.__post_init__`

#### `qts.domain.market_data.bar.Quote`

- 位置：`backend/src/qts/domain/market_data/bar.py:64-83`
- 类型：`class`
- 签名：`class Quote`
- 装饰器：`dataclass()`
- 作用：Top-of-book quote.
- 直接原始调用：`Decimal` x2, `dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter.normalize_quote`

#### `qts.domain.market_data.bar.Quote.__post_init__`

- 位置：`backend/src/qts/domain/market_data/bar.py:74-79`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.domain.market_data.bar.Quote`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`Bar._require_non_negative` x2, `ValueError`, `require_aware_datetime`
- 已解析到仓库内部的调用：`qts.core.time.require_aware_datetime`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.domain.market_data.bar.Quote.spread`

- 位置：`backend/src/qts/domain/market_data/bar.py:82-83`
- 类型：`property`
- 签名：`def spread(self) -> Decimal`
- 所属：`qts.domain.market_data.bar.Quote`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为所属类上的 `spread` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.domain.market_data.bar.Tick`

- 位置：`backend/src/qts/domain/market_data/bar.py:87-97`
- 类型：`class`
- 签名：`class Tick`
- 装饰器：`dataclass()`
- 作用：Trade tick.
- 直接原始调用：`Decimal`, `dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter.normalize_tick`

#### `qts.domain.market_data.bar.Tick.__post_init__`

- 位置：`backend/src/qts/domain/market_data/bar.py:95-97`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.domain.market_data.bar.Tick`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`Bar._require_non_negative`, `require_aware_datetime`
- 已解析到仓库内部的调用：`qts.core.time.require_aware_datetime`
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/domain/orders/__init__.py`

模块：`qts.domain.orders`

无类或函数定义。

### `backend/src/qts/domain/portfolio/__init__.py`

模块：`qts.domain.portfolio`

无类或函数定义。

### `backend/src/qts/domain/risk/__init__.py`

模块：`qts.domain.risk`

无类或函数定义。

### `backend/src/qts/domain/risk/decision.py`

模块：`qts.domain.risk.decision`

#### `qts.domain.risk.decision.RiskDecisionStatus`

- 位置：`backend/src/qts/domain/risk/decision.py:10-15`
- 类型：`class`
- 签名：`class RiskDecisionStatus(StrEnum)`
- 继承/基类：`StrEnum`
- 作用：Risk check outcome.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.domain.risk.decision.RiskDecision`

- 位置：`backend/src/qts/domain/risk/decision.py:19-64`
- 类型：`class`
- 签名：`class RiskDecision`
- 装饰器：`dataclass()`
- 作用：Explicit result of a risk check.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.domain.risk.decision.RiskDecision.approve`

- 位置：`backend/src/qts/domain/risk/decision.py:29-35`
- 类型：`classmethod`
- 签名：`def approve(cls, *, rule_id: str | None = None, checked_at: datetime | None = None) -> RiskDecision`
- 所属：`qts.domain.risk.decision.RiskDecision`
- 装饰器：`classmethod`
- 作用：未写 docstring；静态推断为所属类上的 `approve` 行为。
- 直接原始调用：`cls`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.domain.risk.decision.RiskDecision.rejected`

- 位置：`backend/src/qts/domain/risk/decision.py:38-56`
- 类型：`classmethod`
- 签名：`def rejected(cls, reason_code: str, reason: str, *, rule_id: str | None = None, checked_at: datetime | None = None) -> RiskDecision`
- 所属：`qts.domain.risk.decision.RiskDecision`
- 装饰器：`classmethod`
- 作用：未写 docstring；静态推断为所属类上的 `rejected` 行为。
- 直接原始调用：`ValueError` x2, `cls`, `reason.strip`, `reason_code.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.domain.risk.decision.RiskDecision.approved`

- 位置：`backend/src/qts/domain/risk/decision.py:59-60`
- 类型：`property`
- 签名：`def approved(self) -> bool`
- 所属：`qts.domain.risk.decision.RiskDecision`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为所属类上的 `approved` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.domain.risk.decision.RiskDecision.reason_text`

- 位置：`backend/src/qts/domain/risk/decision.py:63-64`
- 类型：`property`
- 签名：`def reason_text(self) -> str | None`
- 所属：`qts.domain.risk.decision.RiskDecision`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为所属类上的 `reason text` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/domain/risk/request.py`

模块：`qts.domain.risk.request`

#### `qts.domain.risk.request.OrderRiskRequest`

- 位置：`backend/src/qts/domain/risk/request.py:14-35`
- 类型：`class`
- 签名：`class OrderRiskRequest`
- 装饰器：`dataclass()`
- 作用：Pre-trade risk input for a proposed order.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._process_order_delta`

#### `qts.domain.risk.request.OrderRiskRequest.__post_init__`

- 位置：`backend/src/qts/domain/risk/request.py:23-31`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.domain.risk.request.OrderRiskRequest`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`Decimal` x3, `ValueError` x3, `require_aware_datetime`
- 已解析到仓库内部的调用：`qts.core.time.require_aware_datetime`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.domain.risk.request.OrderRiskRequest.notional`

- 位置：`backend/src/qts/domain/risk/request.py:34-35`
- 类型：`property`
- 签名：`def notional(self) -> Decimal`
- 所属：`qts.domain.risk.request.OrderRiskRequest`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为所属类上的 `notional` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/execution/__init__.py`

模块：`qts.execution`

无类或函数定义。

### `backend/src/qts/execution/adapters/__init__.py`

模块：`qts.execution.adapters`

无类或函数定义。

### `backend/src/qts/execution/adapters/ibkr_order_execution.py`

模块：`qts.execution.adapters.ibkr_order_execution`

#### `qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionConnection`

- 位置：`backend/src/qts/execution/adapters/ibkr_order_execution.py:14-31`
- 类型：`class`
- 签名：`class IbkrOrderExecutionConnection`
- 装饰器：`dataclass()`
- 作用：IBKR order execution connection settings.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionConnection.__post_init__`

- 位置：`backend/src/qts/execution/adapters/ibkr_order_execution.py:23-31`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionConnection`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x4, `self.account_id.strip`, `self.host.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.adapters.ibkr_order_execution.IbkrOrderRequest`

- 位置：`backend/src/qts/execution/adapters/ibkr_order_execution.py:35-42`
- 类型：`class`
- 签名：`class IbkrOrderRequest`
- 装饰器：`dataclass()`
- 作用：IBKR order request produced at the adapter boundary.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionAdapter.to_order_request`

#### `qts.execution.adapters.ibkr_order_execution.IbkrExecutionReport`

- 位置：`backend/src/qts/execution/adapters/ibkr_order_execution.py:46-54`
- 类型：`class`
- 签名：`class IbkrExecutionReport`
- 装饰器：`dataclass()`
- 作用：IBKR execution report shape before normalization.
- 直接原始调用：`Decimal`, `dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionAdapter`

- 位置：`backend/src/qts/execution/adapters/ibkr_order_execution.py:57-86`
- 类型：`class`
- 签名：`class IbkrOrderExecutionAdapter`
- 作用：Maps internal orders to IBKR order requests and normalizes reports.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionAdapter.__init__`

- 位置：`backend/src/qts/execution/adapters/ibkr_order_execution.py:60-67`
- 类型：`method`
- 签名：`def __init__(self, *, connection: IbkrOrderExecutionConnection, symbol_mapping: BrokerSymbolMapping) -> None`
- 所属：`qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionAdapter`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionAdapter.to_order_request`

- 位置：`backend/src/qts/execution/adapters/ibkr_order_execution.py:69-76`
- 类型：`method`
- 签名：`def to_order_request(self, intent: OrderIntent) -> IbkrOrderRequest`
- 所属：`qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionAdapter`
- 作用：未写 docstring；静态推断为转换或序列化为指定目标表示（名称：to order request）。
- 直接原始调用：`IbkrOrderRequest`, `self._symbol_mapping.to_broker_symbol`
- 已解析到仓库内部的调用：`qts.execution.adapters.ibkr_order_execution.IbkrOrderRequest`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionAdapter.normalize_execution_report`

- 位置：`backend/src/qts/execution/adapters/ibkr_order_execution.py:78-86`
- 类型：`method`
- 签名：`def normalize_execution_report(self, report: IbkrExecutionReport) -> ExecutionReport`
- 所属：`qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionAdapter`
- 作用：未写 docstring；静态推断为所属类上的 `normalize execution report` 行为。
- 直接原始调用：`ExecutionReport`
- 已解析到仓库内部的调用：`qts.execution.order_manager.ExecutionReport`
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/execution/broker.py`

模块：`qts.execution.broker`

#### `qts.execution.broker.BrokerCapabilities`

- 位置：`backend/src/qts/execution/broker.py:15-52`
- 类型：`class`
- 签名：`class BrokerCapabilities`
- 装饰器：`dataclass()`
- 作用：Broker-supported live execution features.
- 直接原始调用：`frozenset` x3, `dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.execution.broker.FakeBrokerAdapter.capabilities`

#### `qts.execution.broker.BrokerCapabilities.__post_init__`

- 位置：`backend/src/qts/execution/broker.py:31-35`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.execution.broker.BrokerCapabilities`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x2, `Decimal`, `any`, `item.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.broker.BrokerCapabilities.supports_asset_class`

- 位置：`backend/src/qts/execution/broker.py:37-40`
- 类型：`method`
- 签名：`def supports_asset_class(self, asset_class: str) -> bool`
- 所属：`qts.execution.broker.BrokerCapabilities`
- 作用：未写 docstring；静态推断为所属类上的 `supports asset class` 行为。
- 直接原始调用：`ValueError`, `asset_class.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.broker.BrokerCapabilities.supports_order_type`

- 位置：`backend/src/qts/execution/broker.py:42-49`
- 类型：`method`
- 签名：`def supports_order_type(self, order_type: BrokerOrderType) -> bool`
- 所属：`qts.execution.broker.BrokerCapabilities`
- 作用：未写 docstring；静态推断为所属类上的 `supports order type` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.broker.BrokerCapabilities.supports_tif`

- 位置：`backend/src/qts/execution/broker.py:51-52`
- 类型：`method`
- 签名：`def supports_tif(self, time_in_force: TimeInForce) -> bool`
- 所属：`qts.execution.broker.BrokerCapabilities`
- 作用：未写 docstring；静态推断为所属类上的 `supports tif` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.broker.BrokerOrderType`

- 位置：`backend/src/qts/execution/broker.py:55-60`
- 类型：`class`
- 签名：`class BrokerOrderType(StrEnum)`
- 继承/基类：`StrEnum`
- 作用：Order types modeled before broker submission.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.broker.TimeInForce`

- 位置：`backend/src/qts/execution/broker.py:63-68`
- 类型：`class`
- 签名：`class TimeInForce(StrEnum)`
- 继承/基类：`StrEnum`
- 作用：Time-in-force values modeled at the execution boundary.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.broker.BrokerOrderRequest`

- 位置：`backend/src/qts/execution/broker.py:72-84`
- 类型：`class`
- 签名：`class BrokerOrderRequest`
- 装饰器：`dataclass()`
- 作用：Internal order request sent to the broker adapter boundary.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill`

#### `qts.execution.broker.BrokerOrderRequest.__post_init__`

- 位置：`backend/src/qts/execution/broker.py:82-84`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.execution.broker.BrokerOrderRequest`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`Decimal`, `ValueError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.broker.BrokerExecutionReportStatus`

- 位置：`backend/src/qts/execution/broker.py:87-94`
- 类型：`class`
- 签名：`class BrokerExecutionReportStatus(StrEnum)`
- 继承/基类：`StrEnum`
- 作用：Broker-boundary execution report status.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.broker.BrokerExecutionReport`

- 位置：`backend/src/qts/execution/broker.py:98-121`
- 类型：`class`
- 签名：`class BrokerExecutionReport`
- 装饰器：`dataclass()`
- 作用：Normalized broker callback before it reaches OrderManager.
- 直接原始调用：`Decimal`, `dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.execution.broker.FakeBrokerAdapter._report`

#### `qts.execution.broker.BrokerExecutionReport.__post_init__`

- 位置：`backend/src/qts/execution/broker.py:113-121`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.execution.broker.BrokerExecutionReport`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x4, `Decimal` x2, `self.broker_order_id.strip`, `self.report_id.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.broker.BrokerAdapter`

- 位置：`backend/src/qts/execution/broker.py:124-132`
- 类型：`class`
- 签名：`class BrokerAdapter(Protocol)`
- 继承/基类：`Protocol`
- 作用：Stable broker execution boundary.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.broker.BrokerAdapter.capabilities`

- 位置：`backend/src/qts/execution/broker.py:128-128`
- 类型：`property`
- 签名：`def capabilities(self) -> BrokerCapabilities`
- 所属：`qts.execution.broker.BrokerAdapter`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为所属类上的 `capabilities` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.broker.BrokerAdapter.submit_order`

- 位置：`backend/src/qts/execution/broker.py:130-130`
- 类型：`method`
- 签名：`def submit_order(self, request: BrokerOrderRequest) -> BrokerExecutionReport`
- 所属：`qts.execution.broker.BrokerAdapter`
- 作用：未写 docstring；静态推断为所属类上的 `submit order` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.broker.BrokerAdapter.cancel_order`

- 位置：`backend/src/qts/execution/broker.py:132-132`
- 类型：`method`
- 签名：`def cancel_order(self, order_id: OrderId) -> BrokerExecutionReport`
- 所属：`qts.execution.broker.BrokerAdapter`
- 作用：未写 docstring；静态推断为所属类上的 `cancel order` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.broker.FakeBrokerAdapter`

- 位置：`backend/src/qts/execution/broker.py:135-219`
- 类型：`class`
- 签名：`class FakeBrokerAdapter`
- 作用：Deterministic fake broker for live-beta tests and local runs.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill`

#### `qts.execution.broker.FakeBrokerAdapter.__init__`

- 位置：`backend/src/qts/execution/broker.py:138-142`
- 类型：`method`
- 签名：`def __init__(self, *, broker_id: BrokerId) -> None`
- 所属：`qts.execution.broker.FakeBrokerAdapter`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.broker.FakeBrokerAdapter.capabilities`

- 位置：`backend/src/qts/execution/broker.py:145-146`
- 类型：`property`
- 签名：`def capabilities(self) -> BrokerCapabilities`
- 所属：`qts.execution.broker.FakeBrokerAdapter`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为所属类上的 `capabilities` 行为。
- 直接原始调用：`BrokerCapabilities`
- 已解析到仓库内部的调用：`qts.execution.broker.BrokerCapabilities`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.broker.FakeBrokerAdapter.submit_order`

- 位置：`backend/src/qts/execution/broker.py:148-157`
- 类型：`method`
- 签名：`def submit_order(self, request: BrokerOrderRequest) -> BrokerExecutionReport`
- 所属：`qts.execution.broker.FakeBrokerAdapter`
- 作用：未写 docstring；静态推断为所属类上的 `submit order` 行为。
- 直接原始调用：`len`, `self._broker_order_ids.setdefault`, `self._report`
- 已解析到仓库内部的调用：`qts.execution.broker.FakeBrokerAdapter._report`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.broker.FakeBrokerAdapter.cancel_order`

- 位置：`backend/src/qts/execution/broker.py:159-165`
- 类型：`method`
- 签名：`def cancel_order(self, order_id: OrderId) -> BrokerExecutionReport`
- 所属：`qts.execution.broker.FakeBrokerAdapter`
- 作用：未写 docstring；静态推断为所属类上的 `cancel order` 行为。
- 直接原始调用：`self._report`
- 已解析到仓库内部的调用：`qts.execution.broker.FakeBrokerAdapter._report`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.broker.FakeBrokerAdapter.emit_fill`

- 位置：`backend/src/qts/execution/broker.py:167-194`
- 类型：`method`
- 签名：`def emit_fill(self, *, order_id: OrderId, quantity: Decimal, price: Decimal, fill_id: str) -> BrokerExecutionReport`
- 所属：`qts.execution.broker.FakeBrokerAdapter`
- 作用：未写 docstring；静态推断为所属类上的 `emit fill` 行为。
- 直接原始调用：`ValueError` x3, `Decimal` x2, `fill_id.strip`, `self._report`
- 已解析到仓库内部的调用：`qts.execution.broker.FakeBrokerAdapter._report`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.broker.FakeBrokerAdapter._report`

- 位置：`backend/src/qts/execution/broker.py:196-219`
- 类型：`method`
- 签名：`def _report(self, request: BrokerOrderRequest, *, broker_order_id: str, status: BrokerExecutionReportStatus, filled_quantity: Decimal = Decimal(), fill_price: Decimal | None = None, fill_id: str | None = None) -> BrokerExecutionReport`
- 所属：`qts.execution.broker.FakeBrokerAdapter`
- 作用：未写 docstring；静态推断为所属类上的 `report` 行为。
- 直接原始调用：`BrokerExecutionReport`
- 已解析到仓库内部的调用：`qts.execution.broker.BrokerExecutionReport`
- 被以下仓库内部符号调用：`qts.execution.broker.FakeBrokerAdapter.cancel_order`, `qts.execution.broker.FakeBrokerAdapter.emit_fill`, `qts.execution.broker.FakeBrokerAdapter.submit_order`

#### `qts.execution.broker.normalize_broker_execution_report`

- 位置：`backend/src/qts/execution/broker.py:222-232`
- 类型：`module_function`
- 签名：`def normalize_broker_execution_report(report: BrokerExecutionReport) -> ExecutionReport`
- 作用：Convert broker-boundary report into the OrderManager report type.
- 直接原始调用：`ExecutionReport`, `ExecutionReportStatus`
- 已解析到仓库内部的调用：`qts.execution.order_manager.ExecutionReport`, `qts.execution.order_manager.ExecutionReportStatus`
- 被以下仓库内部符号调用：`scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill`

### `backend/src/qts/execution/idempotency.py`

模块：`qts.execution.idempotency`

#### `qts.execution.idempotency.FillIdempotencyStore`

- 位置：`backend/src/qts/execution/idempotency.py:6-28`
- 类型：`class`
- 签名：`class FillIdempotencyStore`
- 作用：Tracks fill IDs that have already been applied.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.execution.order_manager.OrderManager.__init__`, `qts.runtime.actors.account_actor.AccountActor.__init__`

#### `qts.execution.idempotency.FillIdempotencyStore.__init__`

- 位置：`backend/src/qts/execution/idempotency.py:9-10`
- 类型：`method`
- 签名：`def __init__(self, seen: set[str] | None = None) -> None`
- 所属：`qts.execution.idempotency.FillIdempotencyStore`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：`set` x2
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.idempotency.FillIdempotencyStore.mark_seen`

- 位置：`backend/src/qts/execution/idempotency.py:12-18`
- 类型：`method`
- 签名：`def mark_seen(self, fill_id: str) -> bool`
- 所属：`qts.execution.idempotency.FillIdempotencyStore`
- 作用：未写 docstring；静态推断为所属类上的 `mark seen` 行为。
- 直接原始调用：`ValueError`, `fill_id.strip`, `self._seen.add`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.idempotency.FillIdempotencyStore.discard`

- 位置：`backend/src/qts/execution/idempotency.py:20-21`
- 类型：`method`
- 签名：`def discard(self, fill_id: str) -> None`
- 所属：`qts.execution.idempotency.FillIdempotencyStore`
- 作用：未写 docstring；静态推断为所属类上的 `discard` 行为。
- 直接原始调用：`self._seen.discard`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.idempotency.FillIdempotencyStore.snapshot`

- 位置：`backend/src/qts/execution/idempotency.py:23-24`
- 类型：`method`
- 签名：`def snapshot(self) -> tuple`
- 所属：`qts.execution.idempotency.FillIdempotencyStore`
- 作用：未写 docstring；静态推断为所属类上的 `snapshot` 行为。
- 直接原始调用：`sorted`, `tuple`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.idempotency.FillIdempotencyStore.restore`

- 位置：`backend/src/qts/execution/idempotency.py:27-28`
- 类型：`classmethod`
- 签名：`def restore(cls, seen: tuple) -> FillIdempotencyStore`
- 所属：`qts.execution.idempotency.FillIdempotencyStore`
- 装饰器：`classmethod`
- 作用：未写 docstring；静态推断为所属类上的 `restore` 行为。
- 直接原始调用：`cls`, `set`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.execution.order_manager.OrderManager.restore`

### `backend/src/qts/execution/order_manager.py`

模块：`qts.execution.order_manager`

#### `qts.execution.order_manager.OrderSide`

- 位置：`backend/src/qts/execution/order_manager.py:15-19`
- 类型：`class`
- 签名：`class OrderSide(StrEnum)`
- 继承/基类：`StrEnum`
- 作用：Order side.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill`

#### `qts.execution.order_manager.OrderIntent`

- 位置：`backend/src/qts/execution/order_manager.py:23-33`
- 类型：`class`
- 签名：`class OrderIntent`
- 装饰器：`dataclass()`
- 作用：Approved order instruction before broker submission.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._process_order_delta`, `qts.execution.order_manager.OrderManager.request_replace`, `scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill`

#### `qts.execution.order_manager.OrderIntent.__post_init__`

- 位置：`backend/src/qts/execution/order_manager.py:31-33`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.execution.order_manager.OrderIntent`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`Decimal`, `ValueError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.order_manager.CancelIntent`

- 位置：`backend/src/qts/execution/order_manager.py:37-41`
- 类型：`class`
- 签名：`class CancelIntent`
- 装饰器：`dataclass()`
- 作用：Intent to cancel an order through OrderManager.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill`

#### `qts.execution.order_manager.ReplaceIntent`

- 位置：`backend/src/qts/execution/order_manager.py:45-53`
- 类型：`class`
- 签名：`class ReplaceIntent`
- 装饰器：`dataclass()`
- 作用：Intent to replace an order through OrderManager.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.order_manager.ReplaceIntent.__post_init__`

- 位置：`backend/src/qts/execution/order_manager.py:51-53`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.execution.order_manager.ReplaceIntent`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`Decimal`, `ValueError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.order_manager.Order`

- 位置：`backend/src/qts/execution/order_manager.py:57-63`
- 类型：`class`
- 签名：`class Order`
- 装饰器：`dataclass()`
- 作用：Order snapshot owned by OrderManager.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.execution.order_manager.OrderManager._replace_order`, `qts.execution.order_manager.OrderManager.create_order`, `qts.execution.order_manager.OrderManager.request_replace`

#### `qts.execution.order_manager.ExecutionReportStatus`

- 位置：`backend/src/qts/execution/order_manager.py:66-73`
- 类型：`class`
- 签名：`class ExecutionReportStatus(StrEnum)`
- 继承/基类：`StrEnum`
- 作用：Normalized broker report status.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.execution.broker.normalize_broker_execution_report`

#### `qts.execution.order_manager.ExecutionReport`

- 位置：`backend/src/qts/execution/order_manager.py:80-102`
- 类型：`class`
- 签名：`class ExecutionReport`
- 装饰器：`dataclass()`
- 作用：Normalized broker execution report.
- 直接原始调用：`Decimal` x3, `dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine._BacktestExecutionAdapter.execute_market_order`, `qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionAdapter.normalize_execution_report`, `qts.execution.broker.normalize_broker_execution_report`, `qts.execution.simulator.fill_model.ImmediateFillModel.fill`

#### `qts.execution.order_manager.ExecutionReport.__post_init__`

- 位置：`backend/src/qts/execution/order_manager.py:92-102`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.execution.order_manager.ExecutionReport`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x5, `Decimal` x3, `self.broker_order_id.strip`, `self.report_id.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.order_manager.OrderFill`

- 位置：`backend/src/qts/execution/order_manager.py:106-116`
- 类型：`class`
- 签名：`class OrderFill`
- 装饰器：`dataclass()`
- 作用：OrderManager-validated fill event.
- 直接原始调用：`Decimal` x2, `dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.execution.order_manager.OrderManager._fills_for_report`

#### `qts.execution.order_manager.OrderManagerResult`

- 位置：`backend/src/qts/execution/order_manager.py:120-124`
- 类型：`class`
- 签名：`class OrderManagerResult`
- 装饰器：`dataclass()`
- 作用：Events emitted by processing an execution report.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.execution.order_manager.OrderManager.process_report`

#### `qts.execution.order_manager.OrderManagerSnapshot`

- 位置：`backend/src/qts/execution/order_manager.py:128-133`
- 类型：`class`
- 签名：`class OrderManagerSnapshot`
- 装饰器：`dataclass()`
- 作用：Serializable OrderManager state for reconnect/recovery.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.execution.order_manager.OrderManager.snapshot`

#### `qts.execution.order_manager.OrderManager`

- 位置：`backend/src/qts/execution/order_manager.py:136-276`
- 类型：`class`
- 签名：`class OrderManager`
- 作用：Owns order lifecycle and normalized execution reports.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.actors.order_manager_actor.OrderManagerActor.__init__`, `scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill`

#### `qts.execution.order_manager.OrderManager.__init__`

- 位置：`backend/src/qts/execution/order_manager.py:139-144`
- 类型：`method`
- 签名：`def __init__(self) -> None`
- 所属：`qts.execution.order_manager.OrderManager`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：`FillIdempotencyStore`
- 已解析到仓库内部的调用：`qts.execution.idempotency.FillIdempotencyStore`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.order_manager.OrderManager.create_order`

- 位置：`backend/src/qts/execution/order_manager.py:146-153`
- 类型：`method`
- 签名：`def create_order(self, intent: OrderIntent, *, risk_decision: RiskDecision) -> Order`
- 所属：`qts.execution.order_manager.OrderManager`
- 作用：未写 docstring；静态推断为创建对象或资源（名称：create order）。
- 直接原始调用：`Order`, `OrderStateMachine`, `ValueError`
- 已解析到仓库内部的调用：`qts.execution.order_manager.Order`, `qts.execution.order_state_machine.OrderStateMachine`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.order_manager.OrderManager.mark_sent`

- 位置：`backend/src/qts/execution/order_manager.py:155-162`
- 类型：`method`
- 签名：`def mark_sent(self, order_id: OrderId, *, broker_order_id: str) -> Order`
- 所属：`qts.execution.order_manager.OrderManager`
- 作用：未写 docstring；静态推断为所属类上的 `mark sent` 行为。
- 直接原始调用：`ValueError`, `broker_order_id.strip`, `machine.apply`, `self._replace_order`
- 已解析到仓库内部的调用：`qts.execution.order_manager.OrderManager._replace_order`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.order_manager.OrderManager.request_cancel`

- 位置：`backend/src/qts/execution/order_manager.py:164-166`
- 类型：`method`
- 签名：`def request_cancel(self, intent: CancelIntent) -> Order`
- 所属：`qts.execution.order_manager.OrderManager`
- 作用：未写 docstring；静态推断为所属类上的 `request cancel` 行为。
- 直接原始调用：`self._machines.apply`, `self._replace_order`
- 已解析到仓库内部的调用：`qts.execution.order_manager.OrderManager._replace_order`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.order_manager.OrderManager.request_replace`

- 位置：`backend/src/qts/execution/order_manager.py:168-186`
- 类型：`method`
- 签名：`def request_replace(self, intent: ReplaceIntent, *, risk_decision: RiskDecision) -> Order`
- 所属：`qts.execution.order_manager.OrderManager`
- 作用：未写 docstring；静态推断为所属类上的 `request replace` 行为。
- 直接原始调用：`Order`, `OrderIntent`, `ValueError`, `self._machines.apply`
- 已解析到仓库内部的调用：`qts.execution.order_manager.Order`, `qts.execution.order_manager.OrderIntent`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.order_manager.OrderManager.process_report`

- 位置：`backend/src/qts/execution/order_manager.py:188-193`
- 类型：`method`
- 签名：`def process_report(self, report: ExecutionReport) -> OrderManagerResult`
- 所属：`qts.execution.order_manager.OrderManager`
- 作用：未写 docstring；静态推断为所属类上的 `process report` 行为。
- 直接原始调用：`OrderManagerResult`, `self._event_for_report`, `self._fills_for_report`, `self._machines.apply`, `self._replace_order`
- 已解析到仓库内部的调用：`qts.execution.order_manager.OrderManager._event_for_report`, `qts.execution.order_manager.OrderManager._fills_for_report`, `qts.execution.order_manager.OrderManager._replace_order`, `qts.execution.order_manager.OrderManagerResult`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.order_manager.OrderManager.get_order`

- 位置：`backend/src/qts/execution/order_manager.py:195-196`
- 类型：`method`
- 签名：`def get_order(self, order_id: OrderId) -> Order`
- 所属：`qts.execution.order_manager.OrderManager`
- 作用：未写 docstring；静态推断为读取或返回值（名称：get order）。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.order_manager.OrderManager.discard_terminal_order`

- 位置：`backend/src/qts/execution/order_manager.py:198-207`
- 类型：`method`
- 签名：`def discard_terminal_order(self, order_id: OrderId) -> None`
- 所属：`qts.execution.order_manager.OrderManager`
- 作用：未写 docstring；静态推断为所属类上的 `discard terminal order` 行为。
- 直接原始调用：`ValueError`, `self._broker_to_order.pop`, `self._fill_ids.discard`, `self._fill_ids_by_order.pop`, `self._machines.pop`, `self._orders.pop`, `set`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.order_manager.OrderManager.snapshot`

- 位置：`backend/src/qts/execution/order_manager.py:209-214`
- 类型：`method`
- 签名：`def snapshot(self) -> OrderManagerSnapshot`
- 所属：`qts.execution.order_manager.OrderManager`
- 作用：未写 docstring；静态推断为所属类上的 `snapshot` 行为。
- 直接原始调用：`tuple` x2, `OrderManagerSnapshot`, `self._broker_to_order.items`, `self._fill_ids.snapshot`, `self._orders.values`
- 已解析到仓库内部的调用：`qts.execution.order_manager.OrderManagerSnapshot`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.order_manager.OrderManager.restore`

- 位置：`backend/src/qts/execution/order_manager.py:217-226`
- 类型：`classmethod`
- 签名：`def restore(cls, snapshot: OrderManagerSnapshot) -> OrderManager`
- 所属：`qts.execution.order_manager.OrderManager`
- 装饰器：`classmethod`
- 作用：未写 docstring；静态推断为所属类上的 `restore` 行为。
- 直接原始调用：`FillIdempotencyStore.restore`, `OrderStateMachine`, `cls`, `dict`
- 已解析到仓库内部的调用：`qts.execution.idempotency.FillIdempotencyStore.restore`, `qts.execution.order_state_machine.OrderStateMachine`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.order_manager.OrderManager._replace_order`

- 位置：`backend/src/qts/execution/order_manager.py:228-245`
- 类型：`method`
- 签名：`def _replace_order(self, order_id: OrderId, *, state: OrderState, broker_order_id: str | None = None) -> Order`
- 所属：`qts.execution.order_manager.OrderManager`
- 作用：未写 docstring；静态推断为所属类上的 `replace order` 行为。
- 直接原始调用：`Order`
- 已解析到仓库内部的调用：`qts.execution.order_manager.Order`
- 被以下仓库内部符号调用：`qts.execution.order_manager.OrderManager.mark_sent`, `qts.execution.order_manager.OrderManager.process_report`, `qts.execution.order_manager.OrderManager.request_cancel`

#### `qts.execution.order_manager.OrderManager._fills_for_report`

- 位置：`backend/src/qts/execution/order_manager.py:247-266`
- 类型：`method`
- 签名：`def _fills_for_report(self, order: Order, report: ExecutionReport) -> tuple`
- 所属：`qts.execution.order_manager.OrderManager`
- 作用：未写 docstring；静态推断为所属类上的 `fills for report` 行为。
- 直接原始调用：`Decimal`, `OrderFill`, `ValueError`, `self._fill_ids.mark_seen`, `self._fill_ids_by_order.setdefault`, `self._fill_ids_by_order.setdefault().add`, `set`
- 已解析到仓库内部的调用：`qts.execution.order_manager.OrderFill`
- 被以下仓库内部符号调用：`qts.execution.order_manager.OrderManager.process_report`

#### `qts.execution.order_manager.OrderManager._event_for_report`

- 位置：`backend/src/qts/execution/order_manager.py:269-276`
- 类型：`staticmethod`
- 签名：`def _event_for_report(status: ExecutionReportStatus) -> OrderEvent`
- 所属：`qts.execution.order_manager.OrderManager`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `event for report` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.execution.order_manager.OrderManager.process_report`

### `backend/src/qts/execution/order_state_machine.py`

模块：`qts.execution.order_state_machine`

#### `qts.execution.order_state_machine.OrderState`

- 位置：`backend/src/qts/execution/order_state_machine.py:9-20`
- 类型：`class`
- 签名：`class OrderState(StrEnum)`
- 继承/基类：`StrEnum`
- 作用：Internal order lifecycle states.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.order_state_machine.OrderEvent`

- 位置：`backend/src/qts/execution/order_state_machine.py:23-33`
- 类型：`class`
- 签名：`class OrderEvent(StrEnum)`
- 继承/基类：`StrEnum`
- 作用：Order lifecycle transition inputs.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.order_state_machine.OrderTransitionError`

- 位置：`backend/src/qts/execution/order_state_machine.py:36-37`
- 类型：`class`
- 签名：`class OrderTransitionError(ValueError)`
- 继承/基类：`ValueError`
- 作用：Raised when an order transition is invalid.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.execution.order_state_machine.OrderStateMachine.apply`

#### `qts.execution.order_state_machine.OrderStateMachine`

- 位置：`backend/src/qts/execution/order_state_machine.py:93-105`
- 类型：`class`
- 签名：`class OrderStateMachine`
- 装饰器：`dataclass()`
- 作用：Validate and apply order lifecycle transitions.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.execution.order_manager.OrderManager.create_order`, `qts.execution.order_manager.OrderManager.restore`

#### `qts.execution.order_state_machine.OrderStateMachine.apply`

- 位置：`backend/src/qts/execution/order_state_machine.py:98-105`
- 类型：`method`
- 签名：`def apply(self, event: OrderEvent) -> OrderState`
- 所属：`qts.execution.order_state_machine.OrderStateMachine`
- 作用：未写 docstring；静态推断为应用状态变更、规则或计算结果（名称：apply）。
- 直接原始调用：`OrderTransitionError`, `_DUPLICATE_TERMINAL_EVENTS.get`, `_TRANSITIONS.get`, `_TRANSITIONS.get().get`
- 已解析到仓库内部的调用：`qts.execution.order_state_machine.OrderTransitionError`
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/execution/simulator/__init__.py`

模块：`qts.execution.simulator`

无类或函数定义。

### `backend/src/qts/execution/simulator/fill_model.py`

模块：`qts.execution.simulator.fill_model`

#### `qts.execution.simulator.fill_model.ImmediateFillModel`

- 位置：`backend/src/qts/execution/simulator/fill_model.py:10-29`
- 类型：`class`
- 签名：`class ImmediateFillModel`
- 作用：Fills market orders at the provided market price.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.execution.simulator.simulated_broker.SimulatedBroker.__init__`

#### `qts.execution.simulator.fill_model.ImmediateFillModel.fill`

- 位置：`backend/src/qts/execution/simulator/fill_model.py:13-29`
- 类型：`method`
- 签名：`def fill(self, intent: OrderIntent, *, broker_order_id: str, market_price: Decimal) -> ExecutionReport`
- 所属：`qts.execution.simulator.fill_model.ImmediateFillModel`
- 作用：未写 docstring；静态推断为所属类上的 `fill` 行为。
- 直接原始调用：`Decimal`, `ExecutionReport`, `ValueError`
- 已解析到仓库内部的调用：`qts.execution.order_manager.ExecutionReport`
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/execution/simulator/simulated_broker.py`

模块：`qts.execution.simulator.simulated_broker`

#### `qts.execution.simulator.simulated_broker.SimulatedBroker`

- 位置：`backend/src/qts/execution/simulator/simulated_broker.py:11-28`
- 类型：`class`
- 签名：`class SimulatedBroker`
- 作用：Broker simulator with no external dependency.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.actors.execution_actor.ExecutionActor.__init__`

#### `qts.execution.simulator.simulated_broker.SimulatedBroker.__init__`

- 位置：`backend/src/qts/execution/simulator/simulated_broker.py:14-15`
- 类型：`method`
- 签名：`def __init__(self, fill_model: ImmediateFillModel | None = None) -> None`
- 所属：`qts.execution.simulator.simulated_broker.SimulatedBroker`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：`ImmediateFillModel`
- 已解析到仓库内部的调用：`qts.execution.simulator.fill_model.ImmediateFillModel`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.execution.simulator.simulated_broker.SimulatedBroker.execute_market_order`

- 位置：`backend/src/qts/execution/simulator/simulated_broker.py:17-28`
- 类型：`method`
- 签名：`def execute_market_order(self, intent: OrderIntent, *, broker_order_id: str, market_price: Decimal) -> ExecutionReport`
- 所属：`qts.execution.simulator.simulated_broker.SimulatedBroker`
- 作用：未写 docstring；静态推断为所属类上的 `execute market order` 行为。
- 直接原始调用：`self._fill_model.fill`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/factors/__init__.py`

模块：`qts.factors`

无类或函数定义。

### `backend/src/qts/factors/momentum.py`

模块：`qts.factors.momentum`

#### `qts.factors.momentum.FactorAsset`

- 位置：`backend/src/qts/factors/momentum.py:10-15`
- 类型：`class`
- 签名：`class FactorAsset(Protocol)`
- 继承/基类：`Protocol`
- 作用：Minimal asset shape required by factor ranking.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.factors.momentum.FactorAsset.symbol`

- 位置：`backend/src/qts/factors/momentum.py:14-15`
- 类型：`property`
- 签名：`def symbol(self) -> str`
- 所属：`qts.factors.momentum.FactorAsset`
- 装饰器：`property`
- 作用：Stable display symbol used for deterministic tie-breaking.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.factors.momentum.FactorScore`

- 位置：`backend/src/qts/factors/momentum.py:19-23`
- 类型：`class`
- 签名：`class FactorScore`
- 装饰器：`dataclass()`
- 作用：Single asset factor score.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.factors.momentum.MomentumFactor.compute`

#### `qts.factors.momentum.FactorResult`

- 位置：`backend/src/qts/factors/momentum.py:27-36`
- 类型：`class`
- 签名：`class FactorResult`
- 装饰器：`dataclass()`
- 作用：Ranked cross-sectional factor result.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.factors.momentum.MomentumFactor.compute`

#### `qts.factors.momentum.FactorResult.score`

- 位置：`backend/src/qts/factors/momentum.py:32-36`
- 类型：`method`
- 签名：`def score(self, asset: FactorAsset) -> Decimal`
- 所属：`qts.factors.momentum.FactorResult`
- 作用：未写 docstring；静态推断为所属类上的 `score` 行为。
- 直接原始调用：`KeyError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.factors.momentum.MomentumFactor`

- 位置：`backend/src/qts/factors/momentum.py:40-65`
- 类型：`class`
- 签名：`class MomentumFactor`
- 装饰器：`dataclass()`
- 作用：Compute simple period momentum as last / first - 1.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.strategy_sdk.factors.FactorFactory.momentum`

#### `qts.factors.momentum.MomentumFactor.__post_init__`

- 位置：`backend/src/qts/factors/momentum.py:45-47`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.factors.momentum.MomentumFactor`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.factors.momentum.MomentumFactor.compute`

- 位置：`backend/src/qts/factors/momentum.py:49-55`
- 类型：`method`
- 签名：`def compute(self, prices: dict) -> FactorResult`
- 所属：`qts.factors.momentum.MomentumFactor`
- 作用：未写 docstring；静态推断为计算派生值（名称：compute）。
- 直接原始调用：`tuple` x2, `FactorResult`, `FactorScore`, `prices.items`, `self._momentum`, `sorted`
- 已解析到仓库内部的调用：`qts.factors.momentum.FactorResult`, `qts.factors.momentum.FactorScore`, `qts.factors.momentum.MomentumFactor._momentum`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.factors.momentum.MomentumFactor._momentum`

- 位置：`backend/src/qts/factors/momentum.py:58-65`
- 类型：`staticmethod`
- 签名：`def _momentum(values: tuple, window: int) -> Decimal`
- 所属：`qts.factors.momentum.MomentumFactor`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `momentum` 行为。
- 直接原始调用：`Decimal` x2, `ValueError` x2, `len`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.factors.momentum.MomentumFactor.compute`

### `backend/src/qts/indicators/__init__.py`

模块：`qts.indicators`

无类或函数定义。

### `backend/src/qts/indicators/price/__init__.py`

模块：`qts.indicators.price`

无类或函数定义。

### `backend/src/qts/indicators/price/ema.py`

模块：`qts.indicators.price.ema`

#### `qts.indicators.price.ema.EMA`

- 位置：`backend/src/qts/indicators/price/ema.py:12-36`
- 类型：`class`
- 签名：`class EMA`
- 装饰器：`dataclass()`
- 作用：Incremental EMA using SMA as the warmup seed.
- 直接原始调用：`dataclass`, `field`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.indicators.price.ema.EMA.__post_init__`

- 位置：`backend/src/qts/indicators/price/ema.py:19-20`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.indicators.price.ema.EMA`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`RollingWindow`
- 已解析到仓库内部的调用：`qts.indicators.rolling.RollingWindow`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.indicators.price.ema.EMA.ready`

- 位置：`backend/src/qts/indicators/price/ema.py:23-24`
- 类型：`property`
- 签名：`def ready(self) -> bool`
- 所属：`qts.indicators.price.ema.EMA`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为读取数据（名称：ready）。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.indicators.price.ema.EMA.update`

- 位置：`backend/src/qts/indicators/price/ema.py:26-36`
- 类型：`method`
- 签名：`def update(self, price: Decimal) -> Decimal | None`
- 所属：`qts.indicators.price.ema.EMA`
- 作用：未写 docstring；静态推断为所属类上的 `update` 行为。
- 直接原始调用：`Decimal` x4, `self._warmup.append`, `sum`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/indicators/price/sma.py`

模块：`qts.indicators.price.sma`

#### `qts.indicators.price.sma.SMA`

- 位置：`backend/src/qts/indicators/price/sma.py:12-32`
- 类型：`class`
- 签名：`class SMA`
- 装饰器：`dataclass()`
- 作用：Incremental simple moving average.
- 直接原始调用：`dataclass`, `field`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.strategy_sdk.indicators.IndicatorFactory.sma`

#### `qts.indicators.price.sma.SMA.__post_init__`

- 位置：`backend/src/qts/indicators/price/sma.py:19-20`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.indicators.price.sma.SMA`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`RollingWindow`
- 已解析到仓库内部的调用：`qts.indicators.rolling.RollingWindow`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.indicators.price.sma.SMA.ready`

- 位置：`backend/src/qts/indicators/price/sma.py:23-24`
- 类型：`property`
- 签名：`def ready(self) -> bool`
- 所属：`qts.indicators.price.sma.SMA`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为读取数据（名称：ready）。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.indicators.price.sma.SMA.update`

- 位置：`backend/src/qts/indicators/price/sma.py:26-32`
- 类型：`method`
- 签名：`def update(self, price: Decimal) -> Decimal | None`
- 所属：`qts.indicators.price.sma.SMA`
- 作用：未写 docstring；静态推断为所属类上的 `update` 行为。
- 直接原始调用：`Decimal` x2, `self._values.append`, `sum`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/indicators/rolling.py`

模块：`qts.indicators.rolling`

#### `qts.indicators.rolling.RollingWindow`

- 位置：`backend/src/qts/indicators/rolling.py:14-45`
- 类型：`class`
- 签名：`class RollingWindow(Generic)`
- 继承/基类：`Generic`
- 装饰器：`dataclass()`
- 作用：Bounded FIFO buffer with warmup state.
- 直接原始调用：`dataclass`, `field`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.indicators.price.ema.EMA.__post_init__`, `qts.indicators.price.sma.SMA.__post_init__`, `qts.indicators.rolling.RollingWindow.restore`

#### `qts.indicators.rolling.RollingWindow.__post_init__`

- 位置：`backend/src/qts/indicators/rolling.py:20-23`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.indicators.rolling.RollingWindow`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError`, `deque`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.indicators.rolling.RollingWindow.ready`

- 位置：`backend/src/qts/indicators/rolling.py:26-27`
- 类型：`property`
- 签名：`def ready(self) -> bool`
- 所属：`qts.indicators.rolling.RollingWindow`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为读取数据（名称：ready）。
- 直接原始调用：`len`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.indicators.rolling.RollingWindow.append`

- 位置：`backend/src/qts/indicators/rolling.py:29-30`
- 类型：`method`
- 签名：`def append(self, value: T) -> None`
- 所属：`qts.indicators.rolling.RollingWindow`
- 作用：未写 docstring；静态推断为所属类上的 `append` 行为。
- 直接原始调用：`self._values.append`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.indicators.rolling.RollingWindow.snapshot`

- 位置：`backend/src/qts/indicators/rolling.py:32-33`
- 类型：`method`
- 签名：`def snapshot(self) -> tuple`
- 所属：`qts.indicators.rolling.RollingWindow`
- 作用：未写 docstring；静态推断为所属类上的 `snapshot` 行为。
- 直接原始调用：`tuple`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.indicators.rolling.RollingWindow.restore`

- 位置：`backend/src/qts/indicators/rolling.py:35-39`
- 类型：`method`
- 签名：`def restore(self, values: Iterable) -> RollingWindow`
- 所属：`qts.indicators.rolling.RollingWindow`
- 作用：未写 docstring；静态推断为所属类上的 `restore` 行为。
- 直接原始调用：`RollingWindow`, `restored.append`
- 已解析到仓库内部的调用：`qts.indicators.rolling.RollingWindow`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.indicators.rolling.RollingWindow.__iter__`

- 位置：`backend/src/qts/indicators/rolling.py:41-42`
- 类型：`method`
- 签名：`def __iter__(self) -> Iterator`
- 所属：`qts.indicators.rolling.RollingWindow`
- 作用：未写 docstring；实现 Python 协议方法 `__iter__`。
- 直接原始调用：`iter`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.indicators.rolling.RollingWindow.__len__`

- 位置：`backend/src/qts/indicators/rolling.py:44-45`
- 类型：`method`
- 签名：`def __len__(self) -> int`
- 所属：`qts.indicators.rolling.RollingWindow`
- 作用：未写 docstring；实现 Python 协议方法 `__len__`。
- 直接原始调用：`len`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/load/__init__.py`

模块：`qts.load`

无类或函数定义。

### `backend/src/qts/load/bootstrap.py`

模块：`qts.load.bootstrap`

#### `qts.load.bootstrap.bootstrap_local`

- 位置：`backend/src/qts/load/bootstrap.py:8-23`
- 类型：`module_function`
- 签名：`def bootstrap_local(root: Path) -> dict`
- 作用：Create local runtime directories and marker files safely.
- 直接原始调用：`str` x4, `data_dir.mkdir`, `logs_dir.mkdir`, `marker.write_text`, `root.mkdir`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`scripts.bootstrap.main`

### `backend/src/qts/load/synthetic_market_data.py`

模块：`qts.load.synthetic_market_data`

#### `qts.load.synthetic_market_data.SyntheticMarketDataConfig`

- 位置：`backend/src/qts/load/synthetic_market_data.py:14-29`
- 类型：`class`
- 签名：`class SyntheticMarketDataConfig`
- 装饰器：`dataclass()`
- 作用：未写 docstring；静态推断为定义 Synthetic Market Data Config 概念或数据结构。
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`scripts.run_load.main`

#### `qts.load.synthetic_market_data.SyntheticMarketDataConfig.__post_init__`

- 位置：`backend/src/qts/load/synthetic_market_data.py:23-29`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.load.synthetic_market_data.SyntheticMarketDataConfig`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x3, `self.session_id.strip`, `self.timeframe.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.load.synthetic_market_data.generate_bars`

- 位置：`backend/src/qts/load/synthetic_market_data.py:32-55`
- 类型：`module_function`
- 签名：`def generate_bars(config: SyntheticMarketDataConfig) -> tuple`
- 作用：未写 docstring；静态推断为 `generate bars` 函数，具体语义以实现为准。
- 直接原始调用：`timedelta` x2, `Bar`, `Decimal`, `bars.append`, `max`, `min`, `range`, `tuple`
- 已解析到仓库内部的调用：`qts.domain.market_data.bar.Bar`
- 被以下仓库内部符号调用：`scripts.run_load.main`

### `backend/src/qts/observability/__init__.py`

模块：`qts.observability`

无类或函数定义。

### `backend/src/qts/observability/audit.py`

模块：`qts.observability.audit`

#### `qts.observability.audit.AuditEvent`

- 位置：`backend/src/qts/observability/audit.py:10-25`
- 类型：`class`
- 签名：`class AuditEvent`
- 装饰器：`dataclass()`
- 作用：Operational or trading audit event.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.observability.audit.AuditEvent.__post_init__`

- 位置：`backend/src/qts/observability/audit.py:19-25`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.observability.audit.AuditEvent`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x3, `self.actor.strip`, `self.event_type.strip`, `self.message.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/observability/logging.py`

模块：`qts.observability.logging`

#### `qts.observability.logging.build_log_record`

- 位置：`backend/src/qts/observability/logging.py:14-39`
- 类型：`module_function`
- 签名：`def build_log_record(*, level: str, message: str, metadata: EventMetadata | None = None, fields: Mapping[str, object] | None = None) -> dict`
- 作用：Build a structured log record without exposing secret values.
- 直接原始调用：`ValueError` x3, `_is_secret_key`, `_metadata_fields`, `fields.items`, `key.strip`, `level.strip`, `message.strip`, `record.update`
- 已解析到仓库内部的调用：`qts.observability.logging._is_secret_key`, `qts.observability.logging._metadata_fields`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.observability.logging._metadata_fields`

- 位置：`backend/src/qts/observability/logging.py:42-64`
- 类型：`module_function`
- 签名：`def _metadata_fields(metadata: EventMetadata) -> dict`
- 作用：未写 docstring；静态推断为 `metadata fields` 函数，具体语义以实现为准。
- 直接原始调用：`str` x2, `metadata.bar_time.isoformat`, `metadata.event_time.isoformat`, `optional.items`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.observability.logging.build_log_record`

#### `qts.observability.logging._is_secret_key`

- 位置：`backend/src/qts/observability/logging.py:67-69`
- 类型：`module_function`
- 签名：`def _is_secret_key(key: str) -> bool`
- 作用：未写 docstring；静态推断为 `is secret key` 函数，具体语义以实现为准。
- 直接原始调用：`any`, `key.lower`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.observability.logging.build_log_record`

### `backend/src/qts/observability/metrics.py`

模块：`qts.observability.metrics`

#### `qts.observability.metrics.MetricsRegistry`

- 位置：`backend/src/qts/observability/metrics.py:10-55`
- 类型：`class`
- 签名：`class MetricsRegistry`
- 作用：Record counters and gauges with deterministic key formatting.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.observability.metrics.MetricsRegistry.__init__`

- 位置：`backend/src/qts/observability/metrics.py:13-14`
- 类型：`method`
- 签名：`def __init__(self) -> None`
- 所属：`qts.observability.metrics.MetricsRegistry`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.observability.metrics.MetricsRegistry.increment`

- 位置：`backend/src/qts/observability/metrics.py:16-24`
- 类型：`method`
- 签名：`def increment(self, name: str, *, amount: int = 1, tags: Mapping[str, str] | None = None) -> None`
- 所属：`qts.observability.metrics.MetricsRegistry`
- 作用：未写 docstring；静态推断为所属类上的 `increment` 行为。
- 直接原始调用：`int`, `self._metric_key`, `self._values.get`
- 已解析到仓库内部的调用：`qts.observability.metrics.MetricsRegistry._metric_key`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.observability.metrics.MetricsRegistry.gauge`

- 位置：`backend/src/qts/observability/metrics.py:26-29`
- 类型：`method`
- 签名：`def gauge(self, name: str, value: int | float, *, tags: Mapping[str, str] | None = None) -> None`
- 所属：`qts.observability.metrics.MetricsRegistry`
- 作用：未写 docstring；静态推断为所属类上的 `gauge` 行为。
- 直接原始调用：`self._metric_key`
- 已解析到仓库内部的调用：`qts.observability.metrics.MetricsRegistry._metric_key`
- 被以下仓库内部符号调用：`qts.observability.metrics.MetricsRegistry.observe_queue`

#### `qts.observability.metrics.MetricsRegistry.observe_queue`

- 位置：`backend/src/qts/observability/metrics.py:31-43`
- 类型：`method`
- 签名：`def observe_queue(self, name: str, mailbox: Mailbox, *, oldest_message_lag_seconds: float) -> None`
- 所属：`qts.observability.metrics.MetricsRegistry`
- 作用：未写 docstring；静态推断为所属类上的 `observe queue` 行为。
- 直接原始调用：`self.gauge` x2
- 已解析到仓库内部的调用：`qts.observability.metrics.MetricsRegistry.gauge`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.observability.metrics.MetricsRegistry.snapshot`

- 位置：`backend/src/qts/observability/metrics.py:45-46`
- 类型：`method`
- 签名：`def snapshot(self) -> dict`
- 所属：`qts.observability.metrics.MetricsRegistry`
- 作用：未写 docstring；静态推断为所属类上的 `snapshot` 行为。
- 直接原始调用：`dict`, `self._values.items`, `sorted`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.observability.metrics.MetricsRegistry._metric_key`

- 位置：`backend/src/qts/observability/metrics.py:49-55`
- 类型：`staticmethod`
- 签名：`def _metric_key(name: str, tags: Mapping[str, str] | None) -> str`
- 所属：`qts.observability.metrics.MetricsRegistry`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `metric key` 行为。
- 直接原始调用：`','.join`, `ValueError`, `name.strip`, `sorted`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.observability.metrics.MetricsRegistry.gauge`, `qts.observability.metrics.MetricsRegistry.increment`

### `backend/src/qts/portfolio/__init__.py`

模块：`qts.portfolio`

无类或函数定义。

### `backend/src/qts/portfolio/accounting/__init__.py`

模块：`qts.portfolio.accounting`

无类或函数定义。

### `backend/src/qts/portfolio/accounting/fill_accounting.py`

模块：`qts.portfolio.accounting.fill_accounting`

#### `qts.portfolio.accounting.fill_accounting.TradeSide`

- 位置：`backend/src/qts/portfolio/accounting/fill_accounting.py:14-18`
- 类型：`class`
- 签名：`class TradeSide(StrEnum)`
- 继承/基类：`StrEnum`
- 作用：Fill side.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.portfolio.accounting.fill_accounting.Fill`

- 位置：`backend/src/qts/portfolio/accounting/fill_accounting.py:22-41`
- 类型：`class`
- 签名：`class Fill`
- 装饰器：`dataclass()`
- 作用：Executed fill used by accounting.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.portfolio.accounting.fill_accounting.Fill.__post_init__`

- 位置：`backend/src/qts/portfolio/accounting/fill_accounting.py:33-41`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.portfolio.accounting.fill_accounting.Fill`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x4, `Decimal` x3, `self.currency.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.portfolio.accounting.fill_accounting.FillAccounting`

- 位置：`backend/src/qts/portfolio/accounting/fill_accounting.py:44-52`
- 类型：`class`
- 签名：`class FillAccounting`
- 作用：Fill accounting operations.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.portfolio.accounting.fill_accounting.FillAccounting.apply`

- 位置：`backend/src/qts/portfolio/accounting/fill_accounting.py:48-52`
- 类型：`staticmethod`
- 签名：`def apply(fill: Fill, *, cash_book: CashBook, position_book: PositionBook) -> None`
- 所属：`qts.portfolio.accounting.fill_accounting.FillAccounting`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为应用状态变更、规则或计算结果（名称：apply）。
- 直接原始调用：`cash_book.apply_delta`, `position_book.apply_delta`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/portfolio/cash_book.py`

模块：`qts.portfolio.cash_book`

#### `qts.portfolio.cash_book.CashBook`

- 位置：`backend/src/qts/portfolio/cash_book.py:11-33`
- 类型：`class`
- 签名：`class CashBook`
- 作用：Mutable cash balance book intended to be owned by AccountActor later.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.actors.account_actor.AccountActor.__init__`

#### `qts.portfolio.cash_book.CashBook.__init__`

- 位置：`backend/src/qts/portfolio/cash_book.py:14-15`
- 类型：`method`
- 签名：`def __init__(self, balances: Mapping[str, Decimal] | None = None) -> None`
- 所属：`qts.portfolio.cash_book.CashBook`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：`dict`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.portfolio.cash_book.CashBook.apply_delta`

- 位置：`backend/src/qts/portfolio/cash_book.py:17-19`
- 类型：`method`
- 签名：`def apply_delta(self, currency: str, amount_delta: Decimal) -> None`
- 所属：`qts.portfolio.cash_book.CashBook`
- 作用：未写 docstring；静态推断为应用状态变更、规则或计算结果（名称：apply delta）。
- 直接原始调用：`self._normalize_currency`, `self.balance`
- 已解析到仓库内部的调用：`qts.portfolio.cash_book.CashBook._normalize_currency`, `qts.portfolio.cash_book.CashBook.balance`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.portfolio.cash_book.CashBook.balance`

- 位置：`backend/src/qts/portfolio/cash_book.py:21-22`
- 类型：`method`
- 签名：`def balance(self, currency: str) -> Decimal`
- 所属：`qts.portfolio.cash_book.CashBook`
- 作用：未写 docstring；静态推断为所属类上的 `balance` 行为。
- 直接原始调用：`Decimal`, `self._balances.get`, `self._normalize_currency`
- 已解析到仓库内部的调用：`qts.portfolio.cash_book.CashBook._normalize_currency`
- 被以下仓库内部符号调用：`qts.portfolio.cash_book.CashBook.apply_delta`, `qts.portfolio.cash_book.CashBook.available`

#### `qts.portfolio.cash_book.CashBook.available`

- 位置：`backend/src/qts/portfolio/cash_book.py:24-26`
- 类型：`method`
- 签名：`def available(self, currency: str, *, reservations: ReservationBook) -> Decimal`
- 所属：`qts.portfolio.cash_book.CashBook`
- 作用：未写 docstring；静态推断为所属类上的 `available` 行为。
- 直接原始调用：`reservations.reserved`, `self._normalize_currency`, `self.balance`
- 已解析到仓库内部的调用：`qts.portfolio.cash_book.CashBook._normalize_currency`, `qts.portfolio.cash_book.CashBook.balance`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.portfolio.cash_book.CashBook._normalize_currency`

- 位置：`backend/src/qts/portfolio/cash_book.py:29-33`
- 类型：`staticmethod`
- 签名：`def _normalize_currency(currency: str) -> str`
- 所属：`qts.portfolio.cash_book.CashBook`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `normalize currency` 行为。
- 直接原始调用：`ValueError`, `currency.strip`, `currency.strip().upper`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.portfolio.cash_book.CashBook.apply_delta`, `qts.portfolio.cash_book.CashBook.available`, `qts.portfolio.cash_book.CashBook.balance`

### `backend/src/qts/portfolio/position_book.py`

模块：`qts.portfolio.position_book`

#### `qts.portfolio.position_book.Position`

- 位置：`backend/src/qts/portfolio/position_book.py:14-18`
- 类型：`class`
- 签名：`class Position`
- 装饰器：`dataclass()`
- 作用：Immutable position snapshot.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._process_intent`, `qts.portfolio.position_book.PositionBook.snapshot`

#### `qts.portfolio.position_book.PositionBook`

- 位置：`backend/src/qts/portfolio/position_book.py:21-39`
- 类型：`class`
- 签名：`class PositionBook`
- 作用：Mutable position book intended to be owned by AccountActor later.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.actors.account_actor.AccountActor.__init__`

#### `qts.portfolio.position_book.PositionBook.__init__`

- 位置：`backend/src/qts/portfolio/position_book.py:24-25`
- 类型：`method`
- 签名：`def __init__(self, positions: Mapping[InstrumentId, Decimal] | None = None) -> None`
- 所属：`qts.portfolio.position_book.PositionBook`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：`dict`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.portfolio.position_book.PositionBook.apply_delta`

- 位置：`backend/src/qts/portfolio/position_book.py:27-28`
- 类型：`method`
- 签名：`def apply_delta(self, instrument_id: InstrumentId, quantity_delta: Decimal) -> None`
- 所属：`qts.portfolio.position_book.PositionBook`
- 作用：未写 docstring；静态推断为应用状态变更、规则或计算结果（名称：apply delta）。
- 直接原始调用：`self.quantity`
- 已解析到仓库内部的调用：`qts.portfolio.position_book.PositionBook.quantity`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.portfolio.position_book.PositionBook.quantity`

- 位置：`backend/src/qts/portfolio/position_book.py:30-31`
- 类型：`method`
- 签名：`def quantity(self, instrument_id: InstrumentId) -> Decimal`
- 所属：`qts.portfolio.position_book.PositionBook`
- 作用：未写 docstring；静态推断为所属类上的 `quantity` 行为。
- 直接原始调用：`Decimal`, `self._positions.get`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.portfolio.position_book.PositionBook.apply_delta`

#### `qts.portfolio.position_book.PositionBook.snapshot`

- 位置：`backend/src/qts/portfolio/position_book.py:33-39`
- 类型：`method`
- 签名：`def snapshot(self) -> Mapping`
- 所属：`qts.portfolio.position_book.PositionBook`
- 作用：未写 docstring；静态推断为所属类上的 `snapshot` 行为。
- 直接原始调用：`MappingProxyType`, `Position`, `self._positions.items`
- 已解析到仓库内部的调用：`qts.portfolio.position_book.Position`
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/portfolio/reservation_book.py`

模块：`qts.portfolio.reservation_book`

#### `qts.portfolio.reservation_book.Reservation`

- 位置：`backend/src/qts/portfolio/reservation_book.py:12-17`
- 类型：`class`
- 签名：`class Reservation`
- 装饰器：`dataclass()`
- 作用：Cash reservation by order ID.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.portfolio.reservation_book.ReservationBook.reserve`

#### `qts.portfolio.reservation_book.ReservationBook`

- 位置：`backend/src/qts/portfolio/reservation_book.py:20-57`
- 类型：`class`
- 签名：`class ReservationBook`
- 作用：Idempotent cash reservations keyed by order ID.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.portfolio.reservation_book.ReservationBook.__init__`

- 位置：`backend/src/qts/portfolio/reservation_book.py:23-24`
- 类型：`method`
- 签名：`def __init__(self) -> None`
- 所属：`qts.portfolio.reservation_book.ReservationBook`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.portfolio.reservation_book.ReservationBook.reserve`

- 位置：`backend/src/qts/portfolio/reservation_book.py:26-36`
- 类型：`method`
- 签名：`def reserve(self, reservation_id: OrderId, currency: str, amount: Decimal) -> None`
- 所属：`qts.portfolio.reservation_book.ReservationBook`
- 作用：未写 docstring；静态推断为所属类上的 `reserve` 行为。
- 直接原始调用：`Decimal`, `Reservation`, `ValueError`, `self._normalize_currency`
- 已解析到仓库内部的调用：`qts.portfolio.reservation_book.Reservation`, `qts.portfolio.reservation_book.ReservationBook._normalize_currency`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.portfolio.reservation_book.ReservationBook.release`

- 位置：`backend/src/qts/portfolio/reservation_book.py:38-39`
- 类型：`method`
- 签名：`def release(self, reservation_id: OrderId) -> None`
- 所属：`qts.portfolio.reservation_book.ReservationBook`
- 作用：未写 docstring；静态推断为所属类上的 `release` 行为。
- 直接原始调用：`self._reservations.pop`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.portfolio.reservation_book.ReservationBook.reserved`

- 位置：`backend/src/qts/portfolio/reservation_book.py:41-50`
- 类型：`method`
- 签名：`def reserved(self, currency: str) -> Decimal`
- 所属：`qts.portfolio.reservation_book.ReservationBook`
- 作用：未写 docstring；静态推断为所属类上的 `reserved` 行为。
- 直接原始调用：`Decimal`, `self._normalize_currency`, `self._reservations.values`, `sum`
- 已解析到仓库内部的调用：`qts.portfolio.reservation_book.ReservationBook._normalize_currency`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.portfolio.reservation_book.ReservationBook._normalize_currency`

- 位置：`backend/src/qts/portfolio/reservation_book.py:53-57`
- 类型：`staticmethod`
- 签名：`def _normalize_currency(currency: str) -> str`
- 所属：`qts.portfolio.reservation_book.ReservationBook`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `normalize currency` 行为。
- 直接原始调用：`ValueError`, `currency.strip`, `currency.strip().upper`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.portfolio.reservation_book.ReservationBook.reserve`, `qts.portfolio.reservation_book.ReservationBook.reserved`

### `backend/src/qts/portfolio/valuation/__init__.py`

模块：`qts.portfolio.valuation`

无类或函数定义。

### `backend/src/qts/portfolio/valuation/models.py`

模块：`qts.portfolio.valuation.models`

#### `qts.portfolio.valuation.models.equity_notional`

- 位置：`backend/src/qts/portfolio/valuation/models.py:8-9`
- 类型：`module_function`
- 签名：`def equity_notional(*, quantity: Decimal, price: Decimal) -> Decimal`
- 作用：未写 docstring；静态推断为 `equity notional` 函数，具体语义以实现为准。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.portfolio.valuation.models.future_pnl`

- 位置：`backend/src/qts/portfolio/valuation/models.py:12-19`
- 类型：`module_function`
- 签名：`def future_pnl(*, contracts: Decimal, entry_price: Decimal, exit_price: Decimal, multiplier: Decimal) -> Decimal`
- 作用：未写 docstring；静态推断为 `future pnl` 函数，具体语义以实现为准。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.portfolio.valuation.models.option_premium_value`

- 位置：`backend/src/qts/portfolio/valuation/models.py:22-28`
- 类型：`module_function`
- 签名：`def option_premium_value(*, contracts: Decimal, option_price: Decimal, multiplier: Decimal) -> Decimal`
- 作用：未写 docstring；静态推断为 `option premium value` 函数，具体语义以实现为准。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/reconciliation.py`

模块：`qts.reconciliation`

#### `qts.reconciliation.DriftKind`

- 位置：`backend/src/qts/reconciliation.py:14-19`
- 类型：`class`
- 签名：`class DriftKind(StrEnum)`
- 继承/基类：`StrEnum`
- 作用：未写 docstring；静态推断为定义 Drift Kind 概念，继承/实现 StrEnum。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.reconciliation.OrderSnapshot`

- 位置：`backend/src/qts/reconciliation.py:23-34`
- 类型：`class`
- 签名：`class OrderSnapshot`
- 装饰器：`dataclass()`
- 作用：未写 docstring；静态推断为定义 Order Snapshot 概念或数据结构。
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.reconciliation.OrderSnapshot.__post_init__`

- 位置：`backend/src/qts/reconciliation.py:30-34`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.reconciliation.OrderSnapshot`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x2, `Decimal`, `self.status.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.reconciliation.PositionSnapshot`

- 位置：`backend/src/qts/reconciliation.py:38-40`
- 类型：`class`
- 签名：`class PositionSnapshot`
- 装饰器：`dataclass()`
- 作用：未写 docstring；静态推断为定义 Position Snapshot 概念或数据结构。
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.reconciliation.CashSnapshot`

- 位置：`backend/src/qts/reconciliation.py:44-50`
- 类型：`class`
- 签名：`class CashSnapshot`
- 装饰器：`dataclass()`
- 作用：未写 docstring；静态推断为定义 Cash Snapshot 概念或数据结构。
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.reconciliation.CashSnapshot.__post_init__`

- 位置：`backend/src/qts/reconciliation.py:48-50`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.reconciliation.CashSnapshot`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError`, `self.currency.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.reconciliation.ReconciliationSnapshot`

- 位置：`backend/src/qts/reconciliation.py:54-58`
- 类型：`class`
- 签名：`class ReconciliationSnapshot`
- 装饰器：`dataclass()`
- 作用：未写 docstring；静态推断为定义 Reconciliation Snapshot 概念或数据结构。
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.reconciliation.DriftItem`

- 位置：`backend/src/qts/reconciliation.py:62-74`
- 类型：`class`
- 签名：`class DriftItem`
- 装饰器：`dataclass()`
- 作用：未写 docstring；静态推断为定义 Drift Item 概念或数据结构。
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.reconciliation._compare_orders`, `qts.reconciliation._quantity_item`

#### `qts.reconciliation.DriftItem.to_dict`

- 位置：`backend/src/qts/reconciliation.py:68-74`
- 类型：`method`
- 签名：`def to_dict(self) -> dict`
- 所属：`qts.reconciliation.DriftItem`
- 作用：未写 docstring；静态推断为转换或序列化为指定目标表示（名称：to dict）。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.reconciliation.ReconciliationReport`

- 位置：`backend/src/qts/reconciliation.py:78-93`
- 类型：`class`
- 签名：`class ReconciliationReport`
- 装饰器：`dataclass()`
- 作用：未写 docstring；静态推断为定义 Reconciliation Report 概念或数据结构。
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.reconciliation.reconcile_snapshots`

#### `qts.reconciliation.ReconciliationReport.has_drift`

- 位置：`backend/src/qts/reconciliation.py:83-86`
- 类型：`property`
- 签名：`def has_drift(self) -> bool`
- 所属：`qts.reconciliation.ReconciliationReport`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为判断是否存在指定状态或能力（名称：has drift）。
- 直接原始调用：`any`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.reconciliation.ReconciliationReport.to_dict`

- 位置：`backend/src/qts/reconciliation.py:88-93`
- 类型：`method`
- 签名：`def to_dict(self) -> dict`
- 所属：`qts.reconciliation.ReconciliationReport`
- 作用：未写 docstring；静态推断为转换或序列化为指定目标表示（名称：to dict）。
- 直接原始调用：`item.to_dict`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.reconciliation.StartupReconciliationDecision`

- 位置：`backend/src/qts/reconciliation.py:97-102`
- 类型：`class`
- 签名：`class StartupReconciliationDecision`
- 装饰器：`dataclass()`
- 作用：Startup gate result derived from reconciliation drift.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.reconciliation.startup_reconciliation_gate`

#### `qts.reconciliation.startup_reconciliation_gate`

- 位置：`backend/src/qts/reconciliation.py:105-114`
- 类型：`module_function`
- 签名：`def startup_reconciliation_gate(report: ReconciliationReport) -> StartupReconciliationDecision`
- 作用：Block trading on startup when reconciliation contains critical drift.
- 直接原始调用：`StartupReconciliationDecision` x2
- 已解析到仓库内部的调用：`qts.reconciliation.StartupReconciliationDecision`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.reconciliation.reconcile_snapshots`

- 位置：`backend/src/qts/reconciliation.py:117-136`
- 类型：`module_function`
- 签名：`def reconcile_snapshots(*, internal: ReconciliationSnapshot, broker: ReconciliationSnapshot, tolerance: Decimal = Decimal()) -> ReconciliationReport`
- 作用：未写 docstring；静态推断为 `reconcile snapshots` 函数，具体语义以实现为准。
- 直接原始调用：`ValueError` x2, `Decimal`, `ReconciliationReport`, `_compare_cash`, `_compare_orders`, `_compare_positions`, `_drift_sort_key`, `sorted`, `tuple`
- 已解析到仓库内部的调用：`qts.reconciliation.ReconciliationReport`, `qts.reconciliation._compare_cash`, `qts.reconciliation._compare_orders`, `qts.reconciliation._compare_positions`, `qts.reconciliation._drift_sort_key`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.reconciliation._compare_orders`

- 位置：`backend/src/qts/reconciliation.py:139-167`
- 类型：`module_function`
- 签名：`def _compare_orders(internal: tuple, broker: tuple) -> list`
- 作用：未写 docstring；静态推断为 `compare orders` 函数，具体语义以实现为准。
- 直接原始调用：`_order_repr` x6, `DriftItem` x4, `items.append` x4, `left.get`, `left.keys`, `right.get`, `right.keys`, `sorted`
- 已解析到仓库内部的调用：`qts.reconciliation.DriftItem`, `qts.reconciliation._order_repr`
- 被以下仓库内部符号调用：`qts.reconciliation.reconcile_snapshots`

#### `qts.reconciliation._compare_positions`

- 位置：`backend/src/qts/reconciliation.py:170-183`
- 类型：`module_function`
- 签名：`def _compare_positions(internal: tuple, broker: tuple, tolerance: Decimal) -> list`
- 作用：未写 docstring；静态推断为 `compare positions` 函数，具体语义以实现为准。
- 直接原始调用：`_quantity_item`, `items.append`, `left.get`, `left.keys`, `right.get`, `right.keys`, `sorted`
- 已解析到仓库内部的调用：`qts.reconciliation._quantity_item`
- 被以下仓库内部符号调用：`qts.reconciliation.reconcile_snapshots`

#### `qts.reconciliation._compare_cash`

- 位置：`backend/src/qts/reconciliation.py:186-199`
- 类型：`module_function`
- 签名：`def _compare_cash(internal: tuple, broker: tuple, tolerance: Decimal) -> list`
- 作用：未写 docstring；静态推断为 `compare cash` 函数，具体语义以实现为准。
- 直接原始调用：`_quantity_item`, `items.append`, `left.get`, `left.keys`, `right.get`, `right.keys`, `sorted`
- 已解析到仓库内部的调用：`qts.reconciliation._quantity_item`
- 被以下仓库内部符号调用：`qts.reconciliation.reconcile_snapshots`

#### `qts.reconciliation._quantity_item`

- 位置：`backend/src/qts/reconciliation.py:202-220`
- 类型：`module_function`
- 签名：`def _quantity_item(key: str, internal: PositionSnapshot | CashSnapshot | None, broker: PositionSnapshot | CashSnapshot | None, tolerance: Decimal) -> DriftItem`
- 作用：未写 docstring；静态推断为 `quantity item` 函数，具体语义以实现为准。
- 直接原始调用：`_amount_repr` x4, `DriftItem` x3, `_amount` x2, `abs`
- 已解析到仓库内部的调用：`qts.reconciliation.DriftItem`, `qts.reconciliation._amount`, `qts.reconciliation._amount_repr`
- 被以下仓库内部符号调用：`qts.reconciliation._compare_cash`, `qts.reconciliation._compare_positions`

#### `qts.reconciliation._order_repr`

- 位置：`backend/src/qts/reconciliation.py:223-226`
- 类型：`module_function`
- 签名：`def _order_repr(order: OrderSnapshot | None) -> str | None`
- 作用：未写 docstring；静态推断为 `order repr` 函数，具体语义以实现为准。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.reconciliation._compare_orders`

#### `qts.reconciliation._amount`

- 位置：`backend/src/qts/reconciliation.py:229-232`
- 类型：`module_function`
- 签名：`def _amount(item: PositionSnapshot | CashSnapshot) -> Decimal`
- 作用：未写 docstring；静态推断为 `amount` 函数，具体语义以实现为准。
- 直接原始调用：`isinstance`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.reconciliation._amount_repr`, `qts.reconciliation._quantity_item`

#### `qts.reconciliation._amount_repr`

- 位置：`backend/src/qts/reconciliation.py:235-238`
- 类型：`module_function`
- 签名：`def _amount_repr(item: PositionSnapshot | CashSnapshot | None) -> str | None`
- 作用：未写 docstring；静态推断为 `amount repr` 函数，具体语义以实现为准。
- 直接原始调用：`_amount`, `str`
- 已解析到仓库内部的调用：`qts.reconciliation._amount`
- 被以下仓库内部符号调用：`qts.reconciliation._quantity_item`

#### `qts.reconciliation._drift_sort_key`

- 位置：`backend/src/qts/reconciliation.py:241-244`
- 类型：`module_function`
- 签名：`def _drift_sort_key(key: str) -> tuple`
- 作用：未写 docstring；静态推断为 `drift sort key` 函数，具体语义以实现为准。
- 直接原始调用：`key.split`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.reconciliation.reconcile_snapshots`

### `backend/src/qts/registry/__init__.py`

模块：`qts.registry`

无类或函数定义。

### `backend/src/qts/registry/broker_symbol_mapping.py`

模块：`qts.registry.broker_symbol_mapping`

#### `qts.registry.broker_symbol_mapping.BrokerSymbolMapping`

- 位置：`backend/src/qts/registry/broker_symbol_mapping.py:8-50`
- 类型：`class`
- 签名：`class BrokerSymbolMapping`
- 作用：Bidirectional mapping between internal IDs and one broker's symbols.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.__init__`

- 位置：`backend/src/qts/registry/broker_symbol_mapping.py:11-14`
- 类型：`method`
- 签名：`def __init__(self, broker_id: BrokerId) -> None`
- 所属：`qts.registry.broker_symbol_mapping.BrokerSymbolMapping`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.register`

- 位置：`backend/src/qts/registry/broker_symbol_mapping.py:16-22`
- 类型：`method`
- 签名：`def register(self, instrument_id: InstrumentId, broker_symbol: str) -> None`
- 所属：`qts.registry.broker_symbol_mapping.BrokerSymbolMapping`
- 作用：未写 docstring；静态推断为所属类上的 `register` 行为。
- 直接原始调用：`ValueError`, `self._normalize_broker_symbol`, `self._to_instrument.get`
- 已解析到仓库内部的调用：`qts.registry.broker_symbol_mapping.BrokerSymbolMapping._normalize_broker_symbol`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.to_broker_symbol`

- 位置：`backend/src/qts/registry/broker_symbol_mapping.py:24-28`
- 类型：`method`
- 签名：`def to_broker_symbol(self, instrument_id: InstrumentId) -> str`
- 所属：`qts.registry.broker_symbol_mapping.BrokerSymbolMapping`
- 作用：未写 docstring；静态推断为转换或序列化为指定目标表示（名称：to broker symbol）。
- 直接原始调用：`KeyError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.to_instrument_id`

- 位置：`backend/src/qts/registry/broker_symbol_mapping.py:30-37`
- 类型：`method`
- 签名：`def to_instrument_id(self, broker_symbol: str) -> InstrumentId`
- 所属：`qts.registry.broker_symbol_mapping.BrokerSymbolMapping`
- 作用：未写 docstring；静态推断为转换或序列化为指定目标表示（名称：to instrument id）。
- 直接原始调用：`KeyError`, `self._normalize_broker_symbol`
- 已解析到仓库内部的调用：`qts.registry.broker_symbol_mapping.BrokerSymbolMapping._normalize_broker_symbol`
- 被以下仓库内部符号调用：`qts.registry.broker_symbol_mapping.BrokerSymbolMapping.instrument_id_for_symbol`

#### `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.is_supported_symbol`

- 位置：`backend/src/qts/registry/broker_symbol_mapping.py:39-40`
- 类型：`method`
- 签名：`def is_supported_symbol(self, symbol: str) -> bool`
- 所属：`qts.registry.broker_symbol_mapping.BrokerSymbolMapping`
- 作用：未写 docstring；静态推断为判断布尔条件（名称：is supported symbol）。
- 直接原始调用：`self._normalize_broker_symbol`
- 已解析到仓库内部的调用：`qts.registry.broker_symbol_mapping.BrokerSymbolMapping._normalize_broker_symbol`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.instrument_id_for_symbol`

- 位置：`backend/src/qts/registry/broker_symbol_mapping.py:42-43`
- 类型：`method`
- 签名：`def instrument_id_for_symbol(self, symbol: str) -> InstrumentId`
- 所属：`qts.registry.broker_symbol_mapping.BrokerSymbolMapping`
- 作用：未写 docstring；静态推断为所属类上的 `instrument id for symbol` 行为。
- 直接原始调用：`self.to_instrument_id`
- 已解析到仓库内部的调用：`qts.registry.broker_symbol_mapping.BrokerSymbolMapping.to_instrument_id`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.broker_symbol_mapping.BrokerSymbolMapping._normalize_broker_symbol`

- 位置：`backend/src/qts/registry/broker_symbol_mapping.py:46-50`
- 类型：`staticmethod`
- 签名：`def _normalize_broker_symbol(broker_symbol: str) -> str`
- 所属：`qts.registry.broker_symbol_mapping.BrokerSymbolMapping`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `normalize broker symbol` 行为。
- 直接原始调用：`ValueError`, `broker_symbol.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.registry.broker_symbol_mapping.BrokerSymbolMapping.is_supported_symbol`, `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.register`, `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.to_instrument_id`

### `backend/src/qts/registry/calendar_registry.py`

模块：`qts.registry.calendar_registry`

#### `qts.registry.calendar_registry.MarketSession`

- 位置：`backend/src/qts/registry/calendar_registry.py:13-32`
- 类型：`class`
- 签名：`class MarketSession`
- 装饰器：`dataclass()`
- 作用：Internal half-open exchange session.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.registry.providers.comex_gold_calendar_provider.ComexGoldCalendarProvider.session_for`, `qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider.session_for`

#### `qts.registry.calendar_registry.MarketSession.__post_init__`

- 位置：`backend/src/qts/registry/calendar_registry.py:20-24`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.registry.calendar_registry.MarketSession`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x2, `self.calendar_id.strip`, `self.session_id.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.calendar_registry.MarketSession.open_time`

- 位置：`backend/src/qts/registry/calendar_registry.py:27-28`
- 类型：`property`
- 签名：`def open_time(self) -> datetime`
- 所属：`qts.registry.calendar_registry.MarketSession`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为打开资源或建立状态（名称：open time）。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.calendar_registry.MarketSession.close_time`

- 位置：`backend/src/qts/registry/calendar_registry.py:31-32`
- 类型：`property`
- 签名：`def close_time(self) -> datetime`
- 所属：`qts.registry.calendar_registry.MarketSession`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为关闭资源或头寸（名称：close time）。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.calendar_registry.CalendarProvider`

- 位置：`backend/src/qts/registry/calendar_registry.py:35-39`
- 类型：`class`
- 签名：`class CalendarProvider(Protocol)`
- 继承/基类：`Protocol`
- 作用：Provider interface for internal calendar session lookup.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.calendar_registry.CalendarProvider.session_for`

- 位置：`backend/src/qts/registry/calendar_registry.py:38-39`
- 类型：`method`
- 签名：`def session_for(self, session_date: date) -> MarketSession`
- 所属：`qts.registry.calendar_registry.CalendarProvider`
- 作用：Return the exchange session for a date.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.calendar_registry.CalendarRegistry`

- 位置：`backend/src/qts/registry/calendar_registry.py:42-58`
- 类型：`class`
- 签名：`class CalendarRegistry`
- 作用：Lookup table for calendar providers.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.calendar_registry.CalendarRegistry.__init__`

- 位置：`backend/src/qts/registry/calendar_registry.py:45-46`
- 类型：`method`
- 签名：`def __init__(self) -> None`
- 所属：`qts.registry.calendar_registry.CalendarRegistry`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.calendar_registry.CalendarRegistry.register`

- 位置：`backend/src/qts/registry/calendar_registry.py:48-51`
- 类型：`method`
- 签名：`def register(self, calendar_id: str, provider: CalendarProvider) -> None`
- 所属：`qts.registry.calendar_registry.CalendarRegistry`
- 作用：未写 docstring；静态推断为所属类上的 `register` 行为。
- 直接原始调用：`ValueError`, `calendar_id.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.calendar_registry.CalendarRegistry.session_for`

- 位置：`backend/src/qts/registry/calendar_registry.py:53-58`
- 类型：`method`
- 签名：`def session_for(self, calendar_id: str, session_date: date) -> MarketSession`
- 所属：`qts.registry.calendar_registry.CalendarRegistry`
- 作用：未写 docstring；静态推断为所属类上的 `session for` 行为。
- 直接原始调用：`KeyError`, `provider.session_for`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/registry/future_chain_registry.py`

模块：`qts.registry.future_chain_registry`

#### `qts.registry.future_chain_registry.FutureChain`

- 位置：`backend/src/qts/registry/future_chain_registry.py:11-21`
- 类型：`class`
- 签名：`class FutureChain`
- 装饰器：`dataclass()`
- 作用：Ordered concrete future contracts for a root symbol.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.future_chain_registry.FutureChain.__post_init__`

- 位置：`backend/src/qts/registry/future_chain_registry.py:17-21`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.registry.future_chain_registry.FutureChain`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x2, `self.root_symbol.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.future_chain_registry.ContinuousFutureRef`

- 位置：`backend/src/qts/registry/future_chain_registry.py:25-35`
- 类型：`class`
- 签名：`class ContinuousFutureRef`
- 装饰器：`dataclass()`
- 作用：Research/data reference to a rolling future contract.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.future_chain_registry.ContinuousFutureRef.__post_init__`

- 位置：`backend/src/qts/registry/future_chain_registry.py:31-35`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.registry.future_chain_registry.ContinuousFutureRef`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x2, `self.root_symbol.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.future_chain_registry.FutureChainRegistry`

- 位置：`backend/src/qts/registry/future_chain_registry.py:38-73`
- 类型：`class`
- 签名：`class FutureChainRegistry`
- 作用：Resolve future roots to concrete tradable contracts.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.future_chain_registry.FutureChainRegistry.__init__`

- 位置：`backend/src/qts/registry/future_chain_registry.py:41-42`
- 类型：`method`
- 签名：`def __init__(self) -> None`
- 所属：`qts.registry.future_chain_registry.FutureChainRegistry`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.future_chain_registry.FutureChainRegistry.register`

- 位置：`backend/src/qts/registry/future_chain_registry.py:44-45`
- 类型：`method`
- 签名：`def register(self, chain: FutureChain) -> None`
- 所属：`qts.registry.future_chain_registry.FutureChainRegistry`
- 作用：未写 docstring；静态推断为所属类上的 `register` 行为。
- 直接原始调用：`self._normalize_root`
- 已解析到仓库内部的调用：`qts.registry.future_chain_registry.FutureChainRegistry._normalize_root`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.future_chain_registry.FutureChainRegistry.resolve_contract`

- 位置：`backend/src/qts/registry/future_chain_registry.py:47-54`
- 类型：`method`
- 签名：`def resolve_contract(self, root_symbol: str, *, offset: int = 0) -> InstrumentId`
- 所属：`qts.registry.future_chain_registry.FutureChainRegistry`
- 作用：未写 docstring；静态推断为解析标识、引用或配置到目标对象（名称：resolve contract）。
- 直接原始调用：`KeyError`, `self._get_chain`
- 已解析到仓库内部的调用：`qts.registry.future_chain_registry.FutureChainRegistry._get_chain`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.future_chain_registry.FutureChainRegistry.require_tradable`

- 位置：`backend/src/qts/registry/future_chain_registry.py:56-59`
- 类型：`method`
- 签名：`def require_tradable(self, reference: InstrumentId | ContinuousFutureRef) -> InstrumentId`
- 所属：`qts.registry.future_chain_registry.FutureChainRegistry`
- 作用：未写 docstring；静态推断为所属类上的 `require tradable` 行为。
- 直接原始调用：`ValueError`, `isinstance`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.future_chain_registry.FutureChainRegistry._get_chain`

- 位置：`backend/src/qts/registry/future_chain_registry.py:61-66`
- 类型：`method`
- 签名：`def _get_chain(self, root_symbol: str) -> FutureChain`
- 所属：`qts.registry.future_chain_registry.FutureChainRegistry`
- 作用：未写 docstring；静态推断为所属类上的 `get chain` 行为。
- 直接原始调用：`KeyError`, `self._normalize_root`
- 已解析到仓库内部的调用：`qts.registry.future_chain_registry.FutureChainRegistry._normalize_root`
- 被以下仓库内部符号调用：`qts.registry.future_chain_registry.FutureChainRegistry.resolve_contract`

#### `qts.registry.future_chain_registry.FutureChainRegistry._normalize_root`

- 位置：`backend/src/qts/registry/future_chain_registry.py:69-73`
- 类型：`staticmethod`
- 签名：`def _normalize_root(root_symbol: str) -> str`
- 所属：`qts.registry.future_chain_registry.FutureChainRegistry`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `normalize root` 行为。
- 直接原始调用：`ValueError`, `root_symbol.strip`, `root_symbol.strip().upper`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.registry.future_chain_registry.FutureChainRegistry._get_chain`, `qts.registry.future_chain_registry.FutureChainRegistry.register`

### `backend/src/qts/registry/future_roll.py`

模块：`qts.registry.future_roll`

#### `qts.registry.future_roll.FutureContractCandidate`

- 位置：`backend/src/qts/registry/future_roll.py:16-32`
- 类型：`class`
- 签名：`class FutureContractCandidate`
- 装饰器：`dataclass()`
- 作用：One concrete futures contract candidate at a decision timestamp.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.HistoricalBarStream._emit_selected_session_rows`, `qts.data.historical.csv_dataset.HistoricalBarStream._iter_selected_contract_rows`

#### `qts.registry.future_roll.FutureContractCandidate.__post_init__`

- 位置：`backend/src/qts/registry/future_roll.py:26-32`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.registry.future_roll.FutureContractCandidate`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x3, `Decimal`, `self.root_symbol.strip`, `self.symbol.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.future_roll.FutureContractSelector`

- 位置：`backend/src/qts/registry/future_roll.py:35-41`
- 类型：`class`
- 签名：`class FutureContractSelector(Protocol)`
- 继承/基类：`Protocol`
- 作用：Select one concrete future from same-root same-time candidates.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.future_roll.FutureContractSelector.select`

- 位置：`backend/src/qts/registry/future_roll.py:38-41`
- 类型：`method`
- 签名：`def select(self, candidates: tuple) -> FutureContractCandidate`
- 所属：`qts.registry.future_roll.FutureContractSelector`
- 作用：未写 docstring；静态推断为所属类上的 `select` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.future_roll.HighestVolumeFutureContractSelector`

- 位置：`backend/src/qts/registry/future_roll.py:44-60`
- 类型：`class`
- 签名：`class HighestVolumeFutureContractSelector`
- 作用：Select the most liquid candidate for one root at one timestamp.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.inputs.BacktestInputBuilder._stream_configured_bars`

#### `qts.registry.future_roll.HighestVolumeFutureContractSelector.select`

- 位置：`backend/src/qts/registry/future_roll.py:47-60`
- 类型：`method`
- 签名：`def select(self, candidates: tuple) -> FutureContractCandidate`
- 所属：`qts.registry.future_roll.HighestVolumeFutureContractSelector`
- 作用：未写 docstring；静态推断为所属类上的 `select` 行为。
- 直接原始调用：`ValueError`, `max`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.future_roll.FutureRollSelection`

- 位置：`backend/src/qts/registry/future_roll.py:64-78`
- 类型：`class`
- 签名：`class FutureRollSelection`
- 装饰器：`dataclass()`
- 作用：Resolved concrete contract for a continuous future at one timestamp.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.HistoricalBarStream._emit_selected_session_rows`, `qts.data.historical.csv_dataset.HistoricalBarStream._iter_selected_contract_rows`

#### `qts.registry.future_roll.FutureRollSelection.__post_init__`

- 位置：`backend/src/qts/registry/future_roll.py:74-78`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.registry.future_roll.FutureRollSelection`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x2, `self.root_symbol.strip`, `self.source_symbol.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.future_roll.FutureRollRegistry`

- 位置：`backend/src/qts/registry/future_roll.py:81-206`
- 类型：`class`
- 签名：`class FutureRollRegistry`
- 作用：Resolve continuous futures to concrete contracts over time.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.inputs.BacktestInputBuilder._roll_registry`

#### `qts.registry.future_roll.FutureRollRegistry.__init__`

- 位置：`backend/src/qts/registry/future_roll.py:84-91`
- 类型：`method`
- 签名：`def __init__(self, *, retain_history: bool = True) -> None`
- 所属：`qts.registry.future_roll.FutureRollRegistry`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.future_roll.FutureRollRegistry.register_root`

- 位置：`backend/src/qts/registry/future_roll.py:93-113`
- 类型：`method`
- 签名：`def register_root(self, *, root_symbol: str, exchange: str, contracts: tuple) -> InstrumentId`
- 所属：`qts.registry.future_roll.FutureRollRegistry`
- 作用：未写 docstring；静态推断为所属类上的 `register root` 行为。
- 直接原始调用：`ValueError` x2, `exchange.strip` x2, `InstrumentId`, `dict.fromkeys`, `exchange.strip().upper`, `self._latest_prices_by_continuous.setdefault`, `self._normalize_root`, `self._selection_times_by_continuous.setdefault`, `self._selections_by_continuous.setdefault`, `tuple`
- 已解析到仓库内部的调用：`qts.core.ids.InstrumentId`, `qts.registry.future_roll.FutureRollRegistry._normalize_root`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.future_roll.FutureRollRegistry.continuous_instrument_id`

- 位置：`backend/src/qts/registry/future_roll.py:115-122`
- 类型：`method`
- 签名：`def continuous_instrument_id(self, root_symbol: str, *, offset: int = 0) -> InstrumentId`
- 所属：`qts.registry.future_roll.FutureRollRegistry`
- 作用：未写 docstring；静态推断为所属类上的 `continuous instrument id` 行为。
- 直接原始调用：`KeyError`, `ValueError`, `self._normalize_root`
- 已解析到仓库内部的调用：`qts.registry.future_roll.FutureRollRegistry._normalize_root`
- 被以下仓库内部符号调用：`qts.registry.future_roll.FutureRollRegistry.resolve_contract`

#### `qts.registry.future_roll.FutureRollRegistry.record_selection`

- 位置：`backend/src/qts/registry/future_roll.py:124-139`
- 类型：`method`
- 签名：`def record_selection(self, selection: FutureRollSelection) -> None`
- 所属：`qts.registry.future_roll.FutureRollRegistry`
- 作用：未写 docstring；静态推断为所属类上的 `record selection` 行为。
- 直接原始调用：`KeyError`, `ValueError`, `dict`, `latest_prices.update`, `replace`, `selection_times.append`, `selections.append`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.future_roll.FutureRollRegistry.is_continuous`

- 位置：`backend/src/qts/registry/future_roll.py:141-142`
- 类型：`method`
- 签名：`def is_continuous(self, instrument_id: InstrumentId) -> bool`
- 所属：`qts.registry.future_roll.FutureRollRegistry`
- 作用：未写 docstring；静态推断为判断布尔条件（名称：is continuous）。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.future_roll.FutureRollRegistry.resolve_contract`

- 位置：`backend/src/qts/registry/future_roll.py:144-159`
- 类型：`method`
- 签名：`def resolve_contract(self, reference: str | InstrumentId, *, as_of: datetime, offset: int = 0) -> InstrumentId`
- 所属：`qts.registry.future_roll.FutureRollRegistry`
- 作用：未写 docstring；静态推断为解析标识、引用或配置到目标对象（名称：resolve contract）。
- 直接原始调用：`ValueError`, `isinstance`, `self._selection_at`, `self.continuous_instrument_id`
- 已解析到仓库内部的调用：`qts.registry.future_roll.FutureRollRegistry._selection_at`, `qts.registry.future_roll.FutureRollRegistry.continuous_instrument_id`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.future_roll.FutureRollRegistry.related_contracts`

- 位置：`backend/src/qts/registry/future_roll.py:161-165`
- 类型：`method`
- 签名：`def related_contracts(self, continuous_instrument_id: InstrumentId) -> tuple`
- 所属：`qts.registry.future_roll.FutureRollRegistry`
- 作用：未写 docstring；静态推断为所属类上的 `related contracts` 行为。
- 直接原始调用：`KeyError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.future_roll.FutureRollRegistry.execution_price`

- 位置：`backend/src/qts/registry/future_roll.py:167-180`
- 类型：`method`
- 签名：`def execution_price(self, continuous_instrument_id: InstrumentId, concrete_instrument_id: InstrumentId, *, as_of: datetime) -> Decimal`
- 所属：`qts.registry.future_roll.FutureRollRegistry`
- 作用：未写 docstring；静态推断为所属类上的 `execution price` 行为。
- 直接原始调用：`KeyError`, `as_of.isoformat`, `self._selection_at`
- 已解析到仓库内部的调用：`qts.registry.future_roll.FutureRollRegistry._selection_at`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.future_roll.FutureRollRegistry._selection_at`

- 位置：`backend/src/qts/registry/future_roll.py:182-199`
- 类型：`method`
- 签名：`def _selection_at(self, continuous_instrument_id: InstrumentId, *, as_of: datetime) -> FutureRollSelection`
- 所属：`qts.registry.future_roll.FutureRollRegistry`
- 作用：未写 docstring；静态推断为所属类上的 `selection at` 行为。
- 直接原始调用：`KeyError` x2, `as_of.isoformat`, `bisect_right`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.registry.future_roll.FutureRollRegistry.execution_price`, `qts.registry.future_roll.FutureRollRegistry.resolve_contract`

#### `qts.registry.future_roll.FutureRollRegistry._normalize_root`

- 位置：`backend/src/qts/registry/future_roll.py:202-206`
- 类型：`staticmethod`
- 签名：`def _normalize_root(root_symbol: str) -> str`
- 所属：`qts.registry.future_roll.FutureRollRegistry`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `normalize root` 行为。
- 直接原始调用：`ValueError`, `root_symbol.strip`, `root_symbol.strip().upper`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.registry.future_roll.FutureRollRegistry.continuous_instrument_id`, `qts.registry.future_roll.FutureRollRegistry.register_root`

### `backend/src/qts/registry/instrument_registry.py`

模块：`qts.registry.instrument_registry`

#### `qts.registry.instrument_registry.InstrumentRegistry`

- 位置：`backend/src/qts/registry/instrument_registry.py:9-42`
- 类型：`class`
- 签名：`class InstrumentRegistry`
- 作用：Resolve user-facing symbols to internal instruments.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._instrument_registry_for`, `qts.backtest.inputs.BacktestInputBuilder._instrument_registry_for`

#### `qts.registry.instrument_registry.InstrumentRegistry.__init__`

- 位置：`backend/src/qts/registry/instrument_registry.py:12-14`
- 类型：`method`
- 签名：`def __init__(self) -> None`
- 所属：`qts.registry.instrument_registry.InstrumentRegistry`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.instrument_registry.InstrumentRegistry.register`

- 位置：`backend/src/qts/registry/instrument_registry.py:16-19`
- 类型：`method`
- 签名：`def register(self, user_symbol: str, instrument: Instrument) -> None`
- 所属：`qts.registry.instrument_registry.InstrumentRegistry`
- 作用：未写 docstring；静态推断为所属类上的 `register` 行为。
- 直接原始调用：`self._normalize_symbol`
- 已解析到仓库内部的调用：`qts.registry.instrument_registry.InstrumentRegistry._normalize_symbol`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.instrument_registry.InstrumentRegistry.resolve`

- 位置：`backend/src/qts/registry/instrument_registry.py:21-26`
- 类型：`method`
- 签名：`def resolve(self, user_symbol: str) -> InstrumentId`
- 所属：`qts.registry.instrument_registry.InstrumentRegistry`
- 作用：未写 docstring；静态推断为解析标识、引用或配置到目标对象（名称：resolve）。
- 直接原始调用：`KeyError`, `self._normalize_symbol`
- 已解析到仓库内部的调用：`qts.registry.instrument_registry.InstrumentRegistry._normalize_symbol`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.instrument_registry.InstrumentRegistry.get_instrument`

- 位置：`backend/src/qts/registry/instrument_registry.py:28-32`
- 类型：`method`
- 签名：`def get_instrument(self, instrument_id: InstrumentId) -> Instrument`
- 所属：`qts.registry.instrument_registry.InstrumentRegistry`
- 作用：未写 docstring；静态推断为读取或返回值（名称：get instrument）。
- 直接原始调用：`KeyError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.registry.instrument_registry.InstrumentRegistry.get_contract_spec`

#### `qts.registry.instrument_registry.InstrumentRegistry.get_contract_spec`

- 位置：`backend/src/qts/registry/instrument_registry.py:34-35`
- 类型：`method`
- 签名：`def get_contract_spec(self, instrument_id: InstrumentId) -> ContractSpec`
- 所属：`qts.registry.instrument_registry.InstrumentRegistry`
- 作用：未写 docstring；静态推断为读取或返回值（名称：get contract spec）。
- 直接原始调用：`self.get_instrument`
- 已解析到仓库内部的调用：`qts.registry.instrument_registry.InstrumentRegistry.get_instrument`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.instrument_registry.InstrumentRegistry._normalize_symbol`

- 位置：`backend/src/qts/registry/instrument_registry.py:38-42`
- 类型：`staticmethod`
- 签名：`def _normalize_symbol(user_symbol: str) -> str`
- 所属：`qts.registry.instrument_registry.InstrumentRegistry`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `normalize symbol` 行为。
- 直接原始调用：`ValueError`, `user_symbol.strip`, `user_symbol.strip().upper`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.registry.instrument_registry.InstrumentRegistry.register`, `qts.registry.instrument_registry.InstrumentRegistry.resolve`

### `backend/src/qts/registry/option_chain_registry.py`

模块：`qts.registry.option_chain_registry`

#### `qts.registry.option_chain_registry.OptionChainRegistry`

- 位置：`backend/src/qts/registry/option_chain_registry.py:12-58`
- 类型：`class`
- 签名：`class OptionChainRegistry`
- 作用：Lookup option instruments by underlying and simple filters.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.option_chain_registry.OptionChainRegistry.__init__`

- 位置：`backend/src/qts/registry/option_chain_registry.py:15-16`
- 类型：`method`
- 签名：`def __init__(self) -> None`
- 所属：`qts.registry.option_chain_registry.OptionChainRegistry`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.option_chain_registry.OptionChainRegistry.register`

- 位置：`backend/src/qts/registry/option_chain_registry.py:18-23`
- 类型：`method`
- 签名：`def register(self, option: Instrument) -> None`
- 所属：`qts.registry.option_chain_registry.OptionChainRegistry`
- 作用：未写 docstring；静态推断为所属类上的 `register` 行为。
- 直接原始调用：`ValueError`, `isinstance`, `self._chains.setdefault`, `self._chains.setdefault().append`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.option_chain_registry.OptionChainRegistry.options_for`

- 位置：`backend/src/qts/registry/option_chain_registry.py:25-29`
- 类型：`method`
- 签名：`def options_for(self, underlying: InstrumentId) -> list`
- 所属：`qts.registry.option_chain_registry.OptionChainRegistry`
- 作用：未写 docstring；静态推断为所属类上的 `options for` 行为。
- 直接原始调用：`KeyError`, `list`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.registry.option_chain_registry.OptionChainRegistry.find`

#### `qts.registry.option_chain_registry.OptionChainRegistry.find`

- 位置：`backend/src/qts/registry/option_chain_registry.py:31-58`
- 类型：`method`
- 签名：`def find(self, *, underlying: InstrumentId, expiry: date | None = None, strike: Decimal | None = None, right: OptionRight | None = None) -> list`
- 所属：`qts.registry.option_chain_registry.OptionChainRegistry`
- 作用：未写 docstring；静态推断为所属类上的 `find` 行为。
- 直接原始调用：`isinstance` x3, `self.options_for`
- 已解析到仓库内部的调用：`qts.registry.option_chain_registry.OptionChainRegistry.options_for`
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/registry/providers/__init__.py`

模块：`qts.registry.providers`

无类或函数定义。

### `backend/src/qts/registry/providers/comex_gold_calendar_provider.py`

模块：`qts.registry.providers.comex_gold_calendar_provider`

#### `qts.registry.providers.comex_gold_calendar_provider.ComexGoldCalendarProvider`

- 位置：`backend/src/qts/registry/providers/comex_gold_calendar_provider.py:12-37`
- 类型：`class`
- 签名：`class ComexGoldCalendarProvider`
- 作用：Regular COMEX Gold session provider for anchor-verified semantics.
- 直接原始调用：`ZoneInfo`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.providers.comex_gold_calendar_provider.ComexGoldCalendarProvider.session_for`

- 位置：`backend/src/qts/registry/providers/comex_gold_calendar_provider.py:18-37`
- 类型：`method`
- 签名：`def session_for(self, session_date: date) -> MarketSession`
- 所属：`qts.registry.providers.comex_gold_calendar_provider.ComexGoldCalendarProvider`
- 作用：未写 docstring；静态推断为所属类上的 `session for` 行为。
- 直接原始调用：`ZoneInfo` x2, `datetime.combine` x2, `time` x2, `MarketSession`, `TimeInterval`, `close_time.astimezone`, `open_time.astimezone`, `session_date.isoformat`, `timedelta`
- 已解析到仓库内部的调用：`qts.core.time.TimeInterval`, `qts.registry.calendar_registry.MarketSession`
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/registry/providers/exchange_calendar_provider.py`

模块：`qts.registry.providers.exchange_calendar_provider`

#### `qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider`

- 位置：`backend/src/qts/registry/providers/exchange_calendar_provider.py:14-41`
- 类型：`class`
- 签名：`class ExchangeCalendarProvider`
- 作用：Calendar provider backed by ``exchange-calendars``.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider.__init__`

- 位置：`backend/src/qts/registry/providers/exchange_calendar_provider.py:17-21`
- 类型：`method`
- 签名：`def __init__(self, calendar_id: str) -> None`
- 所属：`qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：`ValueError`, `calendar_id.strip`, `xc.get_calendar`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider.session_for`

- 位置：`backend/src/qts/registry/providers/exchange_calendar_provider.py:23-31`
- 类型：`method`
- 签名：`def session_for(self, session_date: date) -> MarketSession`
- 所属：`qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider`
- 作用：未写 docstring；静态推断为所属类上的 `session for` 行为。
- 直接原始调用：`self._to_datetime` x2, `MarketSession`, `TimeInterval`, `self._calendar.session_close`, `self._calendar.session_open`, `session_date.isoformat`
- 已解析到仓库内部的调用：`qts.core.time.TimeInterval`, `qts.registry.calendar_registry.MarketSession`, `qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider._to_datetime`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider._to_datetime`

- 位置：`backend/src/qts/registry/providers/exchange_calendar_provider.py:34-41`
- 类型：`staticmethod`
- 签名：`def _to_datetime(value: Any) -> datetime`
- 所属：`qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `to datetime` 行为。
- 直接原始调用：`isinstance` x2, `TypeError`, `hasattr`, `type`, `value.to_pydatetime`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider.session_for`

### `backend/src/qts/registry/symbol_resolution.py`

模块：`qts.registry.symbol_resolution`

#### `qts.registry.symbol_resolution.SourceSymbolResolver`

- 位置：`backend/src/qts/registry/symbol_resolution.py:12-17`
- 类型：`class`
- 签名：`class SourceSymbolResolver(Protocol)`
- 继承/基类：`Protocol`
- 作用：Resolve external source symbols into internal instrument IDs.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.symbol_resolution.SourceSymbolResolver.is_supported_symbol`

- 位置：`backend/src/qts/registry/symbol_resolution.py:15-15`
- 类型：`method`
- 签名：`def is_supported_symbol(self, symbol: str) -> bool`
- 所属：`qts.registry.symbol_resolution.SourceSymbolResolver`
- 作用：未写 docstring；静态推断为判断布尔条件（名称：is supported symbol）。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.symbol_resolution.SourceSymbolResolver.instrument_id_for_symbol`

- 位置：`backend/src/qts/registry/symbol_resolution.py:17-17`
- 类型：`method`
- 签名：`def instrument_id_for_symbol(self, symbol: str) -> InstrumentId`
- 所属：`qts.registry.symbol_resolution.SourceSymbolResolver`
- 作用：未写 docstring；静态推断为所属类上的 `instrument id for symbol` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.symbol_resolution.StaticSymbolResolver`

- 位置：`backend/src/qts/registry/symbol_resolution.py:21-53`
- 类型：`class`
- 签名：`class StaticSymbolResolver`
- 装饰器：`dataclass()`
- 作用：Resolve source symbols from an explicit symbol-to-instrument mapping.
- 直接原始调用：`dataclass`, `field`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.catalog.HistoricalCatalog._symbol_resolvers_for_load_config`

#### `qts.registry.symbol_resolution.StaticSymbolResolver.__post_init__`

- 位置：`backend/src/qts/registry/symbol_resolution.py:27-36`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.registry.symbol_resolution.StaticSymbolResolver`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x2, `object.__setattr__`, `self._normalize_symbol`, `self.instrument_ids.items`
- 已解析到仓库内部的调用：`qts.registry.symbol_resolution.StaticSymbolResolver._normalize_symbol`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.symbol_resolution.StaticSymbolResolver.is_supported_symbol`

- 位置：`backend/src/qts/registry/symbol_resolution.py:38-39`
- 类型：`method`
- 签名：`def is_supported_symbol(self, symbol: str) -> bool`
- 所属：`qts.registry.symbol_resolution.StaticSymbolResolver`
- 作用：未写 docstring；静态推断为判断布尔条件（名称：is supported symbol）。
- 直接原始调用：`self._normalize_symbol`
- 已解析到仓库内部的调用：`qts.registry.symbol_resolution.StaticSymbolResolver._normalize_symbol`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.symbol_resolution.StaticSymbolResolver.instrument_id_for_symbol`

- 位置：`backend/src/qts/registry/symbol_resolution.py:41-46`
- 类型：`method`
- 签名：`def instrument_id_for_symbol(self, symbol: str) -> InstrumentId`
- 所属：`qts.registry.symbol_resolution.StaticSymbolResolver`
- 作用：未写 docstring；静态推断为所属类上的 `instrument id for symbol` 行为。
- 直接原始调用：`ValueError`, `self._normalize_symbol`
- 已解析到仓库内部的调用：`qts.registry.symbol_resolution.StaticSymbolResolver._normalize_symbol`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.registry.symbol_resolution.StaticSymbolResolver._normalize_symbol`

- 位置：`backend/src/qts/registry/symbol_resolution.py:49-53`
- 类型：`staticmethod`
- 签名：`def _normalize_symbol(symbol: str) -> str`
- 所属：`qts.registry.symbol_resolution.StaticSymbolResolver`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `normalize symbol` 行为。
- 直接原始调用：`ValueError`, `symbol.strip`, `symbol.strip().upper`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.registry.symbol_resolution.StaticSymbolResolver.__post_init__`, `qts.registry.symbol_resolution.StaticSymbolResolver.instrument_id_for_symbol`, `qts.registry.symbol_resolution.StaticSymbolResolver.is_supported_symbol`

### `backend/src/qts/risk/__init__.py`

模块：`qts.risk`

无类或函数定义。

### `backend/src/qts/risk/config.py`

模块：`qts.risk.config`

#### `qts.risk.config.RiskRuleConfig`

- 位置：`backend/src/qts/risk/config.py:10-21`
- 类型：`class`
- 签名：`class RiskRuleConfig`
- 装饰器：`dataclass()`
- 作用：One configured risk rule.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.risk.config.RiskRuleConfig.__post_init__`

- 位置：`backend/src/qts/risk/config.py:17-21`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.risk.config.RiskRuleConfig`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x2, `self.name.strip`, `self.rule_id.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.risk.config.RiskConfig`

- 位置：`backend/src/qts/risk/config.py:25-40`
- 类型：`class`
- 签名：`class RiskConfig`
- 装饰器：`dataclass()`
- 作用：Account/strategy/product risk configuration.
- 直接原始调用：`dataclass`, `field`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.risk.config.RiskConfig.__post_init__`

- 位置：`backend/src/qts/risk/config.py:34-40`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.risk.config.RiskConfig`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x3, `Decimal` x2, `self.account_id.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/risk/kill_switch.py`

模块：`qts.risk.kill_switch`

#### `qts.risk.kill_switch.KillSwitchScopeType`

- 位置：`backend/src/qts/risk/kill_switch.py:12-16`
- 类型：`class`
- 签名：`class KillSwitchScopeType(StrEnum)`
- 继承/基类：`StrEnum`
- 作用：未写 docstring；静态推断为定义 Kill Switch Scope Type 概念，继承/实现 StrEnum。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.application.services.operations.OperationsService._scope_from_command`

#### `qts.risk.kill_switch.KillSwitchScope`

- 位置：`backend/src/qts/risk/kill_switch.py:20-41`
- 类型：`class`
- 签名：`class KillSwitchScope`
- 装饰器：`dataclass()`
- 作用：未写 docstring；静态推断为定义 Kill Switch Scope 概念或数据结构。
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.application.services.operations.OperationsService._scope_from_command`

#### `qts.risk.kill_switch.KillSwitchScope.global_scope`

- 位置：`backend/src/qts/risk/kill_switch.py:25-26`
- 类型：`classmethod`
- 签名：`def global_scope(cls) -> KillSwitchScope`
- 所属：`qts.risk.kill_switch.KillSwitchScope`
- 装饰器：`classmethod`
- 作用：未写 docstring；静态推断为所属类上的 `global scope` 行为。
- 直接原始调用：`cls`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.application.services.operations.OperationsService._scope_from_command`

#### `qts.risk.kill_switch.KillSwitchScope.account`

- 位置：`backend/src/qts/risk/kill_switch.py:29-30`
- 类型：`classmethod`
- 签名：`def account(cls, account_id: AccountId) -> KillSwitchScope`
- 所属：`qts.risk.kill_switch.KillSwitchScope`
- 装饰器：`classmethod`
- 作用：未写 docstring；静态推断为所属类上的 `account` 行为。
- 直接原始调用：`cls`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.risk.kill_switch.KillSwitchScope.strategy`

- 位置：`backend/src/qts/risk/kill_switch.py:33-34`
- 类型：`classmethod`
- 签名：`def strategy(cls, strategy_id: StrategyId) -> KillSwitchScope`
- 所属：`qts.risk.kill_switch.KillSwitchScope`
- 装饰器：`classmethod`
- 作用：未写 docstring；静态推断为所属类上的 `strategy` 行为。
- 直接原始调用：`cls`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.risk.kill_switch.KillSwitchScope.broker`

- 位置：`backend/src/qts/risk/kill_switch.py:37-38`
- 类型：`classmethod`
- 签名：`def broker(cls, broker_id: BrokerId) -> KillSwitchScope`
- 所属：`qts.risk.kill_switch.KillSwitchScope`
- 装饰器：`classmethod`
- 作用：未写 docstring；静态推断为所属类上的 `broker` 行为。
- 直接原始调用：`cls`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.risk.kill_switch.KillSwitchScope.reason_code`

- 位置：`backend/src/qts/risk/kill_switch.py:40-41`
- 类型：`method`
- 签名：`def reason_code(self) -> str`
- 所属：`qts.risk.kill_switch.KillSwitchScope`
- 作用：未写 docstring；静态推断为所属类上的 `reason code` 行为。
- 直接原始调用：`self.scope_type.value.upper`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.risk.kill_switch.KillSwitchState`

- 位置：`backend/src/qts/risk/kill_switch.py:45-48`
- 类型：`class`
- 签名：`class KillSwitchState`
- 装饰器：`dataclass()`
- 作用：未写 docstring；静态推断为定义 Kill Switch State 概念或数据结构。
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.risk.kill_switch.KillSwitchRegistry.activate`, `qts.risk.kill_switch.KillSwitchRegistry.deactivate`

#### `qts.risk.kill_switch.KillSwitchRegistry`

- 位置：`backend/src/qts/risk/kill_switch.py:51-103`
- 类型：`class`
- 签名：`class KillSwitchRegistry`
- 作用：Auditable in-memory kill-switch registry.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.application.services.operations.OperationsService.__init__`

#### `qts.risk.kill_switch.KillSwitchRegistry.__init__`

- 位置：`backend/src/qts/risk/kill_switch.py:54-55`
- 类型：`method`
- 签名：`def __init__(self) -> None`
- 所属：`qts.risk.kill_switch.KillSwitchRegistry`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.risk.kill_switch.KillSwitchRegistry.activate`

- 位置：`backend/src/qts/risk/kill_switch.py:57-62`
- 类型：`method`
- 签名：`def activate(self, scope: KillSwitchScope, *, reason: str) -> KillSwitchState`
- 所属：`qts.risk.kill_switch.KillSwitchRegistry`
- 作用：未写 docstring；静态推断为所属类上的 `activate` 行为。
- 直接原始调用：`KillSwitchState`, `ValueError`, `reason.strip`
- 已解析到仓库内部的调用：`qts.risk.kill_switch.KillSwitchState`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.risk.kill_switch.KillSwitchRegistry.deactivate`

- 位置：`backend/src/qts/risk/kill_switch.py:64-69`
- 类型：`method`
- 签名：`def deactivate(self, scope: KillSwitchScope, *, reason: str) -> KillSwitchState`
- 所属：`qts.risk.kill_switch.KillSwitchRegistry`
- 作用：未写 docstring；静态推断为所属类上的 `deactivate` 行为。
- 直接原始调用：`KillSwitchState`, `ValueError`, `reason.strip`
- 已解析到仓库内部的调用：`qts.risk.kill_switch.KillSwitchState`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.risk.kill_switch.KillSwitchRegistry.check_order`

- 位置：`backend/src/qts/risk/kill_switch.py:71-88`
- 类型：`method`
- 签名：`def check_order(self, request: OrderRiskRequest, *, account_id: AccountId, strategy_id: StrategyId | None, broker_id: BrokerId) -> RiskDecision`
- 所属：`qts.risk.kill_switch.KillSwitchRegistry`
- 作用：未写 docstring；静态推断为所属类上的 `check order` 行为。
- 直接原始调用：`RiskDecision.approve`, `RiskDecision.rejected`, `self._matching_scopes`, `self._states.get`, `state.scope.reason_code`
- 已解析到仓库内部的调用：`qts.risk.kill_switch.KillSwitchRegistry._matching_scopes`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.risk.kill_switch.KillSwitchRegistry._matching_scopes`

- 位置：`backend/src/qts/risk/kill_switch.py:91-103`
- 类型：`staticmethod`
- 签名：`def _matching_scopes(account_id: AccountId, strategy_id: StrategyId | None, broker_id: BrokerId) -> tuple`
- 所属：`qts.risk.kill_switch.KillSwitchRegistry`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `matching scopes` 行为。
- 直接原始调用：`KillSwitchScope.account`, `KillSwitchScope.broker`, `KillSwitchScope.global_scope`, `KillSwitchScope.strategy`, `scopes.append`, `tuple`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.risk.kill_switch.KillSwitchRegistry.check_order`

### `backend/src/qts/risk/margin/__init__.py`

模块：`qts.risk.margin`

无类或函数定义。

### `backend/src/qts/risk/risk_engine.py`

模块：`qts.risk.risk_engine`

#### `qts.risk.risk_engine.RiskEngine`

- 位置：`backend/src/qts/risk/risk_engine.py:11-22`
- 类型：`class`
- 签名：`class RiskEngine`
- 作用：Apply risk rules in order and return the first rejection.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine.__init__`, `qts.backtest.engine.BacktestEngine.from_config`

#### `qts.risk.risk_engine.RiskEngine.__init__`

- 位置：`backend/src/qts/risk/risk_engine.py:14-15`
- 类型：`method`
- 签名：`def __init__(self, rules: Iterable) -> None`
- 所属：`qts.risk.risk_engine.RiskEngine`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：`tuple`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.risk.risk_engine.RiskEngine.check`

- 位置：`backend/src/qts/risk/risk_engine.py:17-22`
- 类型：`method`
- 签名：`def check(self, request: OrderRiskRequest) -> RiskDecision`
- 所属：`qts.risk.risk_engine.RiskEngine`
- 作用：未写 docstring；静态推断为所属类上的 `check` 行为。
- 直接原始调用：`RiskDecision.approve`, `rule.check`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/risk/rule.py`

模块：`qts.risk.rule`

#### `qts.risk.rule.RiskRule`

- 位置：`backend/src/qts/risk/rule.py:10-14`
- 类型：`class`
- 签名：`class RiskRule(Protocol)`
- 继承/基类：`Protocol`
- 作用：A pre-trade risk rule.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.risk.rule.RiskRule.check`

- 位置：`backend/src/qts/risk/rule.py:13-14`
- 类型：`method`
- 签名：`def check(self, request: OrderRiskRequest) -> RiskDecision`
- 所属：`qts.risk.rule.RiskRule`
- 作用：Return an explicit risk decision.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/risk/rule_registry.py`

模块：`qts.risk.rule_registry`

#### `qts.risk.rule_registry.RiskRuleRegistry`

- 位置：`backend/src/qts/risk/rule_registry.py:13-28`
- 类型：`class`
- 签名：`class RiskRuleRegistry`
- 作用：Map configured rule names to executable risk rules.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.risk.rule_registry.RiskRuleRegistry.build`

- 位置：`backend/src/qts/risk/rule_registry.py:16-21`
- 类型：`method`
- 签名：`def build(self, config: RiskRuleConfig) -> RiskRule`
- 所属：`qts.risk.rule_registry.RiskRuleRegistry`
- 作用：未写 docstring；静态推断为组装对象、请求或运行上下文（名称：build）。
- 直接原始调用：`self._param` x2, `KeyError`, `MaxNotionalRule`, `MaxOrderQuantityRule`
- 已解析到仓库内部的调用：`qts.risk.rule_registry.RiskRuleRegistry._param`, `qts.risk.rules.max_notional.MaxNotionalRule`, `qts.risk.rules.max_order_qty.MaxOrderQuantityRule`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.risk.rule_registry.RiskRuleRegistry._param`

- 位置：`backend/src/qts/risk/rule_registry.py:24-28`
- 类型：`staticmethod`
- 签名：`def _param(config: RiskRuleConfig, name: str) -> Decimal`
- 所属：`qts.risk.rule_registry.RiskRuleRegistry`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `param` 行为。
- 直接原始调用：`KeyError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.risk.rule_registry.RiskRuleRegistry.build`

### `backend/src/qts/risk/rules/__init__.py`

模块：`qts.risk.rules`

无类或函数定义。

### `backend/src/qts/risk/rules/max_notional.py`

模块：`qts.risk.rules.max_notional`

#### `qts.risk.rules.max_notional.MaxNotionalRule`

- 位置：`backend/src/qts/risk/rules/max_notional.py:12-27`
- 类型：`class`
- 签名：`class MaxNotionalRule`
- 装饰器：`dataclass()`
- 作用：Reject orders whose notional exceeds a fixed limit.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine.__init__`, `qts.backtest.engine.BacktestEngine.from_config`, `qts.risk.rule_registry.RiskRuleRegistry.build`

#### `qts.risk.rules.max_notional.MaxNotionalRule.__post_init__`

- 位置：`backend/src/qts/risk/rules/max_notional.py:17-19`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.risk.rules.max_notional.MaxNotionalRule`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`Decimal`, `ValueError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.risk.rules.max_notional.MaxNotionalRule.check`

- 位置：`backend/src/qts/risk/rules/max_notional.py:21-27`
- 类型：`method`
- 签名：`def check(self, request: OrderRiskRequest) -> RiskDecision`
- 所属：`qts.risk.rules.max_notional.MaxNotionalRule`
- 作用：未写 docstring；静态推断为所属类上的 `check` 行为。
- 直接原始调用：`RiskDecision.approve`, `RiskDecision.rejected`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/risk/rules/max_order_qty.py`

模块：`qts.risk.rules.max_order_qty`

#### `qts.risk.rules.max_order_qty.MaxOrderQuantityRule`

- 位置：`backend/src/qts/risk/rules/max_order_qty.py:12-27`
- 类型：`class`
- 签名：`class MaxOrderQuantityRule`
- 装饰器：`dataclass()`
- 作用：Reject orders whose absolute quantity exceeds a fixed limit.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.risk.rule_registry.RiskRuleRegistry.build`

#### `qts.risk.rules.max_order_qty.MaxOrderQuantityRule.__post_init__`

- 位置：`backend/src/qts/risk/rules/max_order_qty.py:17-19`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.risk.rules.max_order_qty.MaxOrderQuantityRule`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`Decimal`, `ValueError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.risk.rules.max_order_qty.MaxOrderQuantityRule.check`

- 位置：`backend/src/qts/risk/rules/max_order_qty.py:21-27`
- 类型：`method`
- 签名：`def check(self, request: OrderRiskRequest) -> RiskDecision`
- 所属：`qts.risk.rules.max_order_qty.MaxOrderQuantityRule`
- 作用：未写 docstring；静态推断为所属类上的 `check` 行为。
- 直接原始调用：`RiskDecision.approve`, `RiskDecision.rejected`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/risk/rules/trading_session_rule.py`

模块：`qts.risk.rules.trading_session_rule`

#### `qts.risk.rules.trading_session_rule.SessionLookup`

- 位置：`backend/src/qts/risk/rules/trading_session_rule.py:13-17`
- 类型：`class`
- 签名：`class SessionLookup(Protocol)`
- 继承/基类：`Protocol`
- 作用：Calendar session lookup required by the rule.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.risk.rules.trading_session_rule.SessionLookup.session_for`

- 位置：`backend/src/qts/risk/rules/trading_session_rule.py:16-17`
- 类型：`method`
- 签名：`def session_for(self, calendar_id: str, session_date: date) -> MarketSession`
- 所属：`qts.risk.rules.trading_session_rule.SessionLookup`
- 作用：Return the internal market session for the date.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.risk.rules.trading_session_rule.TradingSessionRule`

- 位置：`backend/src/qts/risk/rules/trading_session_rule.py:21-40`
- 类型：`class`
- 签名：`class TradingSessionRule`
- 装饰器：`dataclass()`
- 作用：Reject orders whose order time is outside the configured session.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.risk.rules.trading_session_rule.TradingSessionRule.check`

- 位置：`backend/src/qts/risk/rules/trading_session_rule.py:28-40`
- 类型：`method`
- 签名：`def check(self, request: OrderRiskRequest) -> RiskDecision`
- 所属：`qts.risk.rules.trading_session_rule.TradingSessionRule`
- 作用：未写 docstring；静态推断为所属类上的 `check` 行为。
- 直接原始调用：`RiskDecision.rejected` x2, `RiskDecision.approve`, `self.calendar_registry.session_for`, `session.interval.contains`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/runtime/__init__.py`

模块：`qts.runtime`

无类或函数定义。

### `backend/src/qts/runtime/actor.py`

模块：`qts.runtime.actor`

#### `qts.runtime.actor.Actor`

- 位置：`backend/src/qts/runtime/actor.py:8-13`
- 类型：`class`
- 签名：`class Actor(ABC)`
- 继承/基类：`ABC`
- 作用：Base actor that handles messages serially through an ActorRef.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.actor.Actor.handle`

- 位置：`backend/src/qts/runtime/actor.py:12-13`
- 类型：`method`
- 签名：`def handle(self, message: object) -> None`
- 所属：`qts.runtime.actor.Actor`
- 装饰器：`abstractmethod`
- 作用：Handle one message.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/runtime/actor_ref.py`

模块：`qts.runtime.actor_ref`

#### `qts.runtime.actor_ref.ActorRef`

- 位置：`backend/src/qts/runtime/actor_ref.py:12-31`
- 类型：`class`
- 签名：`class ActorRef`
- 装饰器：`dataclass()`
- 作用：Message-only reference to an actor mailbox.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._market_data_ref_for`, `qts.backtest.engine.BacktestEngine._run_actor_loop`

#### `qts.runtime.actor_ref.ActorRef.tell`

- 位置：`backend/src/qts/runtime/actor_ref.py:18-19`
- 类型：`method`
- 签名：`def tell(self, message: object) -> None`
- 所属：`qts.runtime.actor_ref.ActorRef`
- 作用：未写 docstring；静态推断为所属类上的 `tell` 行为。
- 直接原始调用：`self.mailbox.put`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.actor_ref.ActorRef.process_one`

- 位置：`backend/src/qts/runtime/actor_ref.py:21-25`
- 类型：`method`
- 签名：`def process_one(self) -> bool`
- 所属：`qts.runtime.actor_ref.ActorRef`
- 作用：未写 docstring；静态推断为所属类上的 `process one` 行为。
- 直接原始调用：`self.actor.handle`, `self.mailbox.empty`, `self.mailbox.get`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.actor_ref.ActorRef.process_all`

#### `qts.runtime.actor_ref.ActorRef.process_all`

- 位置：`backend/src/qts/runtime/actor_ref.py:27-31`
- 类型：`method`
- 签名：`def process_all(self) -> int`
- 所属：`qts.runtime.actor_ref.ActorRef`
- 作用：未写 docstring；静态推断为所属类上的 `process all` 行为。
- 直接原始调用：`self.process_one`
- 已解析到仓库内部的调用：`qts.runtime.actor_ref.ActorRef.process_one`
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/runtime/actors/__init__.py`

模块：`qts.runtime.actors`

无类或函数定义。

### `backend/src/qts/runtime/actors/account_actor.py`

模块：`qts.runtime.actors.account_actor`

#### `qts.runtime.actors.account_actor.ApplyFill`

- 位置：`backend/src/qts/runtime/actors/account_actor.py:19-24`
- 类型：`class`
- 签名：`class ApplyFill`
- 装饰器：`dataclass()`
- 作用：Message instructing AccountActor to apply a validated fill.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.actors.order_manager_actor.OrderManagerActor._handle_report`

#### `qts.runtime.actors.account_actor.AccountSnapshot`

- 位置：`backend/src/qts/runtime/actors/account_actor.py:28-32`
- 类型：`class`
- 签名：`class AccountSnapshot`
- 装饰器：`dataclass()`
- 作用：Read-only account snapshot.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.actors.account_actor.AccountActor.snapshot`

#### `qts.runtime.actors.account_actor.AccountActor`

- 位置：`backend/src/qts/runtime/actors/account_actor.py:35-62`
- 类型：`class`
- 签名：`class AccountActor(Actor)`
- 继承/基类：`Actor`
- 作用：Owns account cash and position state.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._run_actor_loop`

#### `qts.runtime.actors.account_actor.AccountActor.__init__`

- 位置：`backend/src/qts/runtime/actors/account_actor.py:38-41`
- 类型：`method`
- 签名：`def __init__(self, initial_cash: Mapping[str, Decimal] | None = None) -> None`
- 所属：`qts.runtime.actors.account_actor.AccountActor`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：`CashBook`, `FillIdempotencyStore`, `PositionBook`
- 已解析到仓库内部的调用：`qts.execution.idempotency.FillIdempotencyStore`, `qts.portfolio.cash_book.CashBook`, `qts.portfolio.position_book.PositionBook`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.actors.account_actor.AccountActor.handle`

- 位置：`backend/src/qts/runtime/actors/account_actor.py:43-47`
- 类型：`method`
- 签名：`def handle(self, message: object) -> None`
- 所属：`qts.runtime.actors.account_actor.AccountActor`
- 作用：未写 docstring；静态推断为处理事件、命令或请求（名称：handle）。
- 直接原始调用：`TypeError`, `isinstance`, `self._apply_fill`, `type`
- 已解析到仓库内部的调用：`qts.runtime.actors.account_actor.AccountActor._apply_fill`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.actors.account_actor.AccountActor.snapshot`

- 位置：`backend/src/qts/runtime/actors/account_actor.py:49-53`
- 类型：`method`
- 签名：`def snapshot(self) -> AccountSnapshot`
- 所属：`qts.runtime.actors.account_actor.AccountActor`
- 作用：未写 docstring；静态推断为所属类上的 `snapshot` 行为。
- 直接原始调用：`AccountSnapshot`, `MappingProxyType`, `self._cash.balance`, `self._positions.snapshot`
- 已解析到仓库内部的调用：`qts.runtime.actors.account_actor.AccountSnapshot`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.actors.account_actor.AccountActor._apply_fill`

- 位置：`backend/src/qts/runtime/actors/account_actor.py:55-62`
- 类型：`method`
- 签名：`def _apply_fill(self, message: ApplyFill) -> None`
- 所属：`qts.runtime.actors.account_actor.AccountActor`
- 作用：未写 docstring；静态推断为所属类上的 `apply fill` 行为。
- 直接原始调用：`self._cash.apply_delta`, `self._fill_ids.mark_seen`, `self._positions.apply_delta`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.actors.account_actor.AccountActor.handle`

### `backend/src/qts/runtime/actors/execution_actor.py`

模块：`qts.runtime.actors.execution_actor`

#### `qts.runtime.actors.execution_actor.ExecutionAdapter`

- 位置：`backend/src/qts/runtime/actors/execution_actor.py:15-24`
- 类型：`class`
- 签名：`class ExecutionAdapter(Protocol)`
- 继承/基类：`Protocol`
- 作用：Execution boundary contract used by the actor.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.actors.execution_actor.ExecutionAdapter.execute_market_order`

- 位置：`backend/src/qts/runtime/actors/execution_actor.py:18-24`
- 类型：`method`
- 签名：`def execute_market_order(self, intent: OrderIntent, *, broker_order_id: str, market_price: Decimal) -> ExecutionReport`
- 所属：`qts.runtime.actors.execution_actor.ExecutionAdapter`
- 作用：未写 docstring；静态推断为所属类上的 `execute market order` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.actors.execution_actor.OrderExecutionRequest`

- 位置：`backend/src/qts/runtime/actors/execution_actor.py:28-33`
- 类型：`class`
- 签名：`class OrderExecutionRequest`
- 装饰器：`dataclass()`
- 作用：Message requesting order execution.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.actors.order_manager_actor.OrderManagerActor._handle_submit`

#### `qts.runtime.actors.execution_actor.ExecutionActor`

- 位置：`backend/src/qts/runtime/actors/execution_actor.py:36-57`
- 类型：`class`
- 签名：`class ExecutionActor(Actor)`
- 继承/基类：`Actor`
- 作用：Actor wrapper for an order execution adapter or simulator.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._run_actor_loop`

#### `qts.runtime.actors.execution_actor.ExecutionActor.__init__`

- 位置：`backend/src/qts/runtime/actors/execution_actor.py:39-46`
- 类型：`method`
- 签名：`def __init__(self, *, order_manager_ref: ActorRef, execution_adapter: ExecutionAdapter | None = None) -> None`
- 所属：`qts.runtime.actors.execution_actor.ExecutionActor`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：`SimulatedBroker`
- 已解析到仓库内部的调用：`qts.execution.simulator.simulated_broker.SimulatedBroker`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.actors.execution_actor.ExecutionActor.handle`

- 位置：`backend/src/qts/runtime/actors/execution_actor.py:48-57`
- 类型：`method`
- 签名：`def handle(self, message: object) -> None`
- 所属：`qts.runtime.actors.execution_actor.ExecutionActor`
- 作用：未写 docstring；静态推断为处理事件、命令或请求（名称：handle）。
- 直接原始调用：`TypeError`, `isinstance`, `self._execution_adapter.execute_market_order`, `self._order_manager_ref.tell`, `type`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/runtime/actors/market_data_actor.py`

模块：`qts.runtime.actors.market_data_actor`

#### `qts.runtime.actors.market_data_actor.MarketDataEvent`

- 位置：`backend/src/qts/runtime/actors/market_data_actor.py:29-32`
- 类型：`class`
- 签名：`class MarketDataEvent`
- 装饰器：`dataclass()`
- 作用：Normalized market data payload accepted by MarketDataActor.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._run_actor_loop`

#### `qts.runtime.actors.market_data_actor.SubscribeMarketData`

- 位置：`backend/src/qts/runtime/actors/market_data_actor.py:36-48`
- 类型：`class`
- 签名：`class SubscribeMarketData`
- 装饰器：`dataclass()`
- 作用：Message requesting strategy market data fan-out.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.actors.market_data_actor.SubscribeMarketData.__post_init__`

- 位置：`backend/src/qts/runtime/actors/market_data_actor.py:44-48`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.runtime.actors.market_data_actor.SubscribeMarketData`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x2, `self.subscriber_id.strip`, `self.timeframe.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.actors.market_data_actor.MarketDataActor`

- 位置：`backend/src/qts/runtime/actors/market_data_actor.py:51-206`
- 类型：`class`
- 签名：`class MarketDataActor(Actor)`
- 继承/基类：`Actor`
- 作用：Actor boundary for normalized market data events.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._market_data_ref_for`

#### `qts.runtime.actors.market_data_actor.MarketDataActor.__init__`

- 位置：`backend/src/qts/runtime/actors/market_data_actor.py:54-73`
- 类型：`method`
- 签名：`def __init__(self, subscribers: Iterable = (), *, aggregate_timeframe: str | None = None, exchange_timezone: str | tzinfo | None = None, feed: LiveFeedAdapter | None = None) -> None`
- 所属：`qts.runtime.actors.market_data_actor.MarketDataActor`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：`Timeframe.parse`, `ValueError`, `set`, `tuple`
- 已解析到仓库内部的调用：`qts.data.bars.timeframe.Timeframe.parse`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.actors.market_data_actor.MarketDataActor.handle`

- 位置：`backend/src/qts/runtime/actors/market_data_actor.py:75-91`
- 类型：`method`
- 签名：`def handle(self, message: object) -> None`
- 所属：`qts.runtime.actors.market_data_actor.MarketDataActor`
- 作用：未写 docstring；静态推断为处理事件、命令或请求（名称：handle）。
- 直接原始调用：`isinstance` x3, `self._publish` x2, `TypeError`, `aggregator.update`, `self._aggregator_for`, `self._publish_to_logical_subscribers`, `self._subscribe`, `type`
- 已解析到仓库内部的调用：`qts.runtime.actors.market_data_actor.MarketDataActor._aggregator_for`, `qts.runtime.actors.market_data_actor.MarketDataActor._publish`, `qts.runtime.actors.market_data_actor.MarketDataActor._publish_to_logical_subscribers`, `qts.runtime.actors.market_data_actor.MarketDataActor._subscribe`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.actors.market_data_actor.MarketDataActor.logical_subscription_count`

- 位置：`backend/src/qts/runtime/actors/market_data_actor.py:94-95`
- 类型：`property`
- 签名：`def logical_subscription_count(self) -> int`
- 所属：`qts.runtime.actors.market_data_actor.MarketDataActor`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为所属类上的 `logical subscription count` 行为。
- 直接原始调用：`len`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.actors.market_data_actor.MarketDataActor.physical_subscription_count`

- 位置：`backend/src/qts/runtime/actors/market_data_actor.py:98-99`
- 类型：`property`
- 签名：`def physical_subscription_count(self) -> int`
- 所属：`qts.runtime.actors.market_data_actor.MarketDataActor`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为所属类上的 `physical subscription count` 行为。
- 直接原始调用：`len`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.actors.market_data_actor.MarketDataActor._subscribe`

- 位置：`backend/src/qts/runtime/actors/market_data_actor.py:101-129`
- 类型：`method`
- 签名：`def _subscribe(self, message: SubscribeMarketData) -> None`
- 所属：`qts.runtime.actors.market_data_actor.MarketDataActor`
- 作用：未写 docstring；静态推断为所属类上的 `subscribe` 行为。
- 直接原始调用：`FeedSubscription`, `LogicalSubscription`, `logical_key`, `plan_physical_subscription`, `self._feed.subscribe`, `self._logical_subscribers.setdefault`, `self._physical_subscriptions.add`, `self._source_timeframe_by_logical.setdefault`, `self._subscription_id`
- 已解析到仓库内部的调用：`qts.data.live_feed.FeedSubscription`, `qts.data.subscriptions.LogicalSubscription`, `qts.data.subscriptions.logical_key`, `qts.data.subscriptions.plan_physical_subscription`, `qts.runtime.actors.market_data_actor.MarketDataActor._subscription_id`
- 被以下仓库内部符号调用：`qts.runtime.actors.market_data_actor.MarketDataActor.handle`

#### `qts.runtime.actors.market_data_actor.MarketDataActor._publish_to_logical_subscribers`

- 位置：`backend/src/qts/runtime/actors/market_data_actor.py:131-154`
- 类型：`method`
- 签名：`def _publish_to_logical_subscribers(self, payload: MarketDataPayload) -> None`
- 所属：`qts.runtime.actors.market_data_actor.MarketDataActor`
- 作用：未写 docstring；静态推断为所属类上的 `publish to logical subscribers` 行为。
- 直接原始调用：`self._publish_to` x2, `subscribers.values` x2, `aggregator.update`, `isinstance`, `self._logical_aggregator_for`, `self._logical_subscribers.items`, `self._publish`
- 已解析到仓库内部的调用：`qts.runtime.actors.market_data_actor.MarketDataActor._logical_aggregator_for`, `qts.runtime.actors.market_data_actor.MarketDataActor._publish`, `qts.runtime.actors.market_data_actor.MarketDataActor._publish_to`
- 被以下仓库内部符号调用：`qts.runtime.actors.market_data_actor.MarketDataActor.handle`

#### `qts.runtime.actors.market_data_actor.MarketDataActor._aggregator_for`

- 位置：`backend/src/qts/runtime/actors/market_data_actor.py:156-167`
- 类型：`method`
- 签名：`def _aggregator_for(self, bar: Bar) -> BarAggregator`
- 所属：`qts.runtime.actors.market_data_actor.MarketDataActor`
- 作用：未写 docstring；静态推断为所属类上的 `aggregator for` 行为。
- 直接原始调用：`BarAggregator`, `RuntimeError`, `self._aggregators.get`, `str`
- 已解析到仓库内部的调用：`qts.data.bars.aggregator.BarAggregator`
- 被以下仓库内部符号调用：`qts.runtime.actors.market_data_actor.MarketDataActor.handle`

#### `qts.runtime.actors.market_data_actor.MarketDataActor._logical_aggregator_for`

- 位置：`backend/src/qts/runtime/actors/market_data_actor.py:169-186`
- 类型：`method`
- 签名：`def _logical_aggregator_for(self, bar: Bar, *, source_timeframe: str, target_timeframe: str) -> BarAggregator`
- 所属：`qts.runtime.actors.market_data_actor.MarketDataActor`
- 作用：未写 docstring；静态推断为所属类上的 `logical aggregator for` 行为。
- 直接原始调用：`BarAggregator`, `RuntimeError`, `Timeframe.parse`, `self._aggregators.get`
- 已解析到仓库内部的调用：`qts.data.bars.aggregator.BarAggregator`, `qts.data.bars.timeframe.Timeframe.parse`
- 被以下仓库内部符号调用：`qts.runtime.actors.market_data_actor.MarketDataActor._publish_to_logical_subscribers`

#### `qts.runtime.actors.market_data_actor.MarketDataActor._publish`

- 位置：`backend/src/qts/runtime/actors/market_data_actor.py:188-190`
- 类型：`method`
- 签名：`def _publish(self, payload: MarketDataPayload) -> None`
- 所属：`qts.runtime.actors.market_data_actor.MarketDataActor`
- 作用：未写 docstring；静态推断为所属类上的 `publish` 行为。
- 直接原始调用：`subscriber.tell`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.actors.market_data_actor.MarketDataActor._publish_to_logical_subscribers`, `qts.runtime.actors.market_data_actor.MarketDataActor.handle`

#### `qts.runtime.actors.market_data_actor.MarketDataActor._publish_to`

- 位置：`backend/src/qts/runtime/actors/market_data_actor.py:193-195`
- 类型：`staticmethod`
- 签名：`def _publish_to(subscribers: Iterable, payload: MarketDataPayload) -> None`
- 所属：`qts.runtime.actors.market_data_actor.MarketDataActor`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `publish to` 行为。
- 直接原始调用：`subscriber.tell`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.actors.market_data_actor.MarketDataActor._publish_to_logical_subscribers`

#### `qts.runtime.actors.market_data_actor.MarketDataActor._subscription_id`

- 位置：`backend/src/qts/runtime/actors/market_data_actor.py:198-206`
- 类型：`staticmethod`
- 签名：`def _subscription_id(key: PhysicalSubscriptionKey) -> str`
- 所属：`qts.runtime.actors.market_data_actor.MarketDataActor`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `subscription id` 行为。
- 直接原始调用：`':'.join`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.actors.market_data_actor.MarketDataActor._subscribe`

### `backend/src/qts/runtime/actors/order_manager_actor.py`

模块：`qts.runtime.actors.order_manager_actor`

#### `qts.runtime.actors.order_manager_actor.SubmitOrder`

- 位置：`backend/src/qts/runtime/actors/order_manager_actor.py:19-25`
- 类型：`class`
- 签名：`class SubmitOrder`
- 装饰器：`dataclass()`
- 作用：Message to submit an approved order to an execution actor.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._process_order_delta`

#### `qts.runtime.actors.order_manager_actor.OrderManagerActor`

- 位置：`backend/src/qts/runtime/actors/order_manager_actor.py:28-93`
- 类型：`class`
- 签名：`class OrderManagerActor(Actor)`
- 继承/基类：`Actor`
- 作用：Actor-owned OrderManager wrapper.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._run_actor_loop`

#### `qts.runtime.actors.order_manager_actor.OrderManagerActor.__init__`

- 位置：`backend/src/qts/runtime/actors/order_manager_actor.py:31-42`
- 类型：`method`
- 签名：`def __init__(self, *, execution_ref: ActorRef, account_ref: ActorRef, multiplier_by_instrument: Mapping[InstrumentId, Decimal] | None = None) -> None`
- 所属：`qts.runtime.actors.order_manager_actor.OrderManagerActor`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：`OrderManager`, `dict`
- 已解析到仓库内部的调用：`qts.execution.order_manager.OrderManager`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.actors.order_manager_actor.OrderManagerActor.handle`

- 位置：`backend/src/qts/runtime/actors/order_manager_actor.py:44-51`
- 类型：`method`
- 签名：`def handle(self, message: object) -> None`
- 所属：`qts.runtime.actors.order_manager_actor.OrderManagerActor`
- 作用：未写 docstring；静态推断为处理事件、命令或请求（名称：handle）。
- 直接原始调用：`isinstance` x2, `TypeError`, `self._handle_report`, `self._handle_submit`, `type`
- 已解析到仓库内部的调用：`qts.runtime.actors.order_manager_actor.OrderManagerActor._handle_report`, `qts.runtime.actors.order_manager_actor.OrderManagerActor._handle_submit`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.actors.order_manager_actor.OrderManagerActor.get_order`

- 位置：`backend/src/qts/runtime/actors/order_manager_actor.py:53-54`
- 类型：`method`
- 签名：`def get_order(self, order_id: OrderId) -> Order`
- 所属：`qts.runtime.actors.order_manager_actor.OrderManagerActor`
- 作用：未写 docstring；静态推断为读取或返回值（名称：get order）。
- 直接原始调用：`self._manager.get_order`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.actors.order_manager_actor.OrderManagerActor.fills`

- 位置：`backend/src/qts/runtime/actors/order_manager_actor.py:57-58`
- 类型：`property`
- 签名：`def fills(self) -> tuple`
- 所属：`qts.runtime.actors.order_manager_actor.OrderManagerActor`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为所属类上的 `fills` 行为。
- 直接原始调用：`tuple`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.actors.order_manager_actor.OrderManagerActor.fill_count`

- 位置：`backend/src/qts/runtime/actors/order_manager_actor.py:61-62`
- 类型：`property`
- 签名：`def fill_count(self) -> int`
- 所属：`qts.runtime.actors.order_manager_actor.OrderManagerActor`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为所属类上的 `fill count` 行为。
- 直接原始调用：`len`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.actors.order_manager_actor.OrderManagerActor.fills_since`

- 位置：`backend/src/qts/runtime/actors/order_manager_actor.py:64-65`
- 类型：`method`
- 签名：`def fills_since(self, index: int) -> tuple`
- 所属：`qts.runtime.actors.order_manager_actor.OrderManagerActor`
- 作用：未写 docstring；静态推断为所属类上的 `fills since` 行为。
- 直接原始调用：`tuple`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.actors.order_manager_actor.OrderManagerActor.compact_for_streaming`

- 位置：`backend/src/qts/runtime/actors/order_manager_actor.py:67-70`
- 类型：`method`
- 签名：`def compact_for_streaming(self, order_ids: Iterable) -> None`
- 所属：`qts.runtime.actors.order_manager_actor.OrderManagerActor`
- 作用：未写 docstring；静态推断为所属类上的 `compact for streaming` 行为。
- 直接原始调用：`self._fills.clear`, `self._manager.discard_terminal_order`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.actors.order_manager_actor.OrderManagerActor._handle_submit`

- 位置：`backend/src/qts/runtime/actors/order_manager_actor.py:72-81`
- 类型：`method`
- 签名：`def _handle_submit(self, message: SubmitOrder) -> None`
- 所属：`qts.runtime.actors.order_manager_actor.OrderManagerActor`
- 作用：未写 docstring；静态推断为所属类上的 `handle submit` 行为。
- 直接原始调用：`OrderExecutionRequest`, `self._execution_ref.tell`, `self._manager.create_order`, `self._manager.mark_sent`
- 已解析到仓库内部的调用：`qts.runtime.actors.execution_actor.OrderExecutionRequest`
- 被以下仓库内部符号调用：`qts.runtime.actors.order_manager_actor.OrderManagerActor.handle`

#### `qts.runtime.actors.order_manager_actor.OrderManagerActor._handle_report`

- 位置：`backend/src/qts/runtime/actors/order_manager_actor.py:83-93`
- 类型：`method`
- 签名：`def _handle_report(self, message: ExecutionReport) -> None`
- 所属：`qts.runtime.actors.order_manager_actor.OrderManagerActor`
- 作用：未写 docstring；静态推断为所属类上的 `handle report` 行为。
- 直接原始调用：`ApplyFill`, `Decimal`, `self._account_ref.tell`, `self._fills.append`, `self._manager.process_report`, `self._multiplier_by_instrument.get`
- 已解析到仓库内部的调用：`qts.runtime.actors.account_actor.ApplyFill`
- 被以下仓库内部符号调用：`qts.runtime.actors.order_manager_actor.OrderManagerActor.handle`

### `backend/src/qts/runtime/actors/signal_aggregator_actor.py`

模块：`qts.runtime.actors.signal_aggregator_actor`

#### `qts.runtime.actors.signal_aggregator_actor.StrategySignalEvent`

- 位置：`backend/src/qts/runtime/actors/signal_aggregator_actor.py:14-18`
- 类型：`class`
- 签名：`class StrategySignalEvent`
- 装饰器：`dataclass()`
- 作用：Strategy intents emitted for one completed bar.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._run_actor_loop`

#### `qts.runtime.actors.signal_aggregator_actor.AggregatedSignalBatch`

- 位置：`backend/src/qts/runtime/actors/signal_aggregator_actor.py:22-26`
- 类型：`class`
- 签名：`class AggregatedSignalBatch`
- 装饰器：`dataclass()`
- 作用：Aggregated intents ready for portfolio/risk/order flow.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.actors.signal_aggregator_actor.SignalAggregatorActor.handle`

#### `qts.runtime.actors.signal_aggregator_actor.SignalAggregatorActor`

- 位置：`backend/src/qts/runtime/actors/signal_aggregator_actor.py:29-44`
- 类型：`class`
- 签名：`class SignalAggregatorActor(Actor)`
- 继承/基类：`Actor`
- 作用：Boundary for combining strategy signals before order flow.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._run_actor_loop`

#### `qts.runtime.actors.signal_aggregator_actor.SignalAggregatorActor.__init__`

- 位置：`backend/src/qts/runtime/actors/signal_aggregator_actor.py:32-33`
- 类型：`method`
- 签名：`def __init__(self, *, result_ref: ActorRef) -> None`
- 所属：`qts.runtime.actors.signal_aggregator_actor.SignalAggregatorActor`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.actors.signal_aggregator_actor.SignalAggregatorActor.handle`

- 位置：`backend/src/qts/runtime/actors/signal_aggregator_actor.py:35-44`
- 类型：`method`
- 签名：`def handle(self, message: object) -> None`
- 所属：`qts.runtime.actors.signal_aggregator_actor.SignalAggregatorActor`
- 作用：未写 docstring；静态推断为处理事件、命令或请求（名称：handle）。
- 直接原始调用：`AggregatedSignalBatch`, `TypeError`, `isinstance`, `self._result_ref.tell`, `type`
- 已解析到仓库内部的调用：`qts.runtime.actors.signal_aggregator_actor.AggregatedSignalBatch`
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/runtime/actors/strategy_actor.py`

模块：`qts.runtime.actors.strategy_actor`

#### `qts.runtime.actors.strategy_actor.StrategyBarEvent`

- 位置：`backend/src/qts/runtime/actors/strategy_actor.py:14-19`
- 类型：`class`
- 签名：`class StrategyBarEvent`
- 装饰器：`dataclass()`
- 作用：Completed strategy-facing bar delivered to a strategy actor.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._run_actor_loop`

#### `qts.runtime.actors.strategy_actor.StrategyBarResult`

- 位置：`backend/src/qts/runtime/actors/strategy_actor.py:23-27`
- 类型：`class`
- 签名：`class StrategyBarResult`
- 装饰器：`dataclass()`
- 作用：New strategy intents emitted while handling one bar.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.actors.strategy_actor.StrategyActor._handle_bar`

#### `qts.runtime.actors.strategy_actor.StrategyFinalize`

- 位置：`backend/src/qts/runtime/actors/strategy_actor.py:31-32`
- 类型：`class`
- 签名：`class StrategyFinalize`
- 装饰器：`dataclass()`
- 作用：Request strategy finalization.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._run_actor_loop`

#### `qts.runtime.actors.strategy_actor.StrategyFinalized`

- 位置：`backend/src/qts/runtime/actors/strategy_actor.py:36-39`
- 类型：`class`
- 签名：`class StrategyFinalized`
- 装饰器：`dataclass()`
- 作用：Strategy finalization completed.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.actors.strategy_actor.StrategyActor._handle_finalize`

#### `qts.runtime.actors.strategy_actor.StrategyActor`

- 位置：`backend/src/qts/runtime/actors/strategy_actor.py:42-84`
- 类型：`class`
- 签名：`class StrategyActor(Actor)`
- 继承/基类：`Actor`
- 作用：Actor-owned strategy instance and user-facing context.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._run_actor_loop`

#### `qts.runtime.actors.strategy_actor.StrategyActor.__init__`

- 位置：`backend/src/qts/runtime/actors/strategy_actor.py:45-55`
- 类型：`method`
- 签名：`def __init__(self, *, strategy: Strategy, context: StrategyContext, result_ref: ActorRef) -> None`
- 所属：`qts.runtime.actors.strategy_actor.StrategyActor`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：`self._strategy.initialize`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.actors.strategy_actor.StrategyActor.handle`

- 位置：`backend/src/qts/runtime/actors/strategy_actor.py:57-64`
- 类型：`method`
- 签名：`def handle(self, message: object) -> None`
- 所属：`qts.runtime.actors.strategy_actor.StrategyActor`
- 作用：未写 docstring；静态推断为处理事件、命令或请求（名称：handle）。
- 直接原始调用：`isinstance` x2, `TypeError`, `self._handle_bar`, `self._handle_finalize`, `type`
- 已解析到仓库内部的调用：`qts.runtime.actors.strategy_actor.StrategyActor._handle_bar`, `qts.runtime.actors.strategy_actor.StrategyActor._handle_finalize`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.actors.strategy_actor.StrategyActor._handle_bar`

- 位置：`backend/src/qts/runtime/actors/strategy_actor.py:66-77`
- 类型：`method`
- 签名：`def _handle_bar(self, message: StrategyBarEvent) -> None`
- 所属：`qts.runtime.actors.strategy_actor.StrategyActor`
- 作用：未写 docstring；静态推断为所属类上的 `handle bar` 行为。
- 直接原始调用：`StrategyBarResult`, `len`, `self._context.indicator.update_from_bar`, `self._result_ref.tell`, `self._strategy.on_bar`
- 已解析到仓库内部的调用：`qts.runtime.actors.strategy_actor.StrategyBarResult`
- 被以下仓库内部符号调用：`qts.runtime.actors.strategy_actor.StrategyActor.handle`

#### `qts.runtime.actors.strategy_actor.StrategyActor._handle_finalize`

- 位置：`backend/src/qts/runtime/actors/strategy_actor.py:79-84`
- 类型：`method`
- 签名：`def _handle_finalize(self) -> None`
- 所属：`qts.runtime.actors.strategy_actor.StrategyActor`
- 作用：未写 docstring；静态推断为所属类上的 `handle finalize` 行为。
- 直接原始调用：`StrategyFinalized`, `finalize`, `getattr`, `len`, `self._result_ref.tell`
- 已解析到仓库内部的调用：`qts.runtime.actors.strategy_actor.StrategyFinalized`
- 被以下仓库内部符号调用：`qts.runtime.actors.strategy_actor.StrategyActor.handle`

### `backend/src/qts/runtime/event_store.py`

模块：`qts.runtime.event_store`

#### `qts.runtime.event_store.EventStore`

- 位置：`backend/src/qts/runtime/event_store.py:15-22`
- 类型：`class`
- 签名：`class EventStore(Protocol)`
- 继承/基类：`Protocol`
- 作用：Append-only event store contract.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.event_store.EventStore.append`

- 位置：`backend/src/qts/runtime/event_store.py:18-18`
- 类型：`method`
- 签名：`def append(self, event: BaseEvent) -> int`
- 所属：`qts.runtime.event_store.EventStore`
- 作用：未写 docstring；静态推断为所属类上的 `append` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.event_store.EventStore.replay`

- 位置：`backend/src/qts/runtime/event_store.py:20-20`
- 类型：`method`
- 签名：`def replay(self, *, partition_key: str | None = None) -> tuple`
- 所属：`qts.runtime.event_store.EventStore`
- 作用：未写 docstring；静态推断为所属类上的 `replay` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.event_store.EventStore.by_correlation_id`

- 位置：`backend/src/qts/runtime/event_store.py:22-22`
- 类型：`method`
- 签名：`def by_correlation_id(self, correlation_id: CorrelationId) -> tuple`
- 所属：`qts.runtime.event_store.EventStore`
- 作用：未写 docstring；静态推断为所属类上的 `by correlation id` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.event_store.InMemoryEventStore`

- 位置：`backend/src/qts/runtime/event_store.py:25-45`
- 类型：`class`
- 签名：`class InMemoryEventStore`
- 作用：Deterministic append-only in-memory event store.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.event_store.InMemoryEventStore.__init__`

- 位置：`backend/src/qts/runtime/event_store.py:28-29`
- 类型：`method`
- 签名：`def __init__(self) -> None`
- 所属：`qts.runtime.event_store.InMemoryEventStore`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.event_store.InMemoryEventStore.append`

- 位置：`backend/src/qts/runtime/event_store.py:31-33`
- 类型：`method`
- 签名：`def append(self, event: BaseEvent) -> int`
- 所属：`qts.runtime.event_store.InMemoryEventStore`
- 作用：未写 docstring；静态推断为所属类上的 `append` 行为。
- 直接原始调用：`len`, `self._events.append`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.event_store.InMemoryEventStore.append_many`

#### `qts.runtime.event_store.InMemoryEventStore.append_many`

- 位置：`backend/src/qts/runtime/event_store.py:35-37`
- 类型：`method`
- 签名：`def append_many(self, events: Iterable) -> None`
- 所属：`qts.runtime.event_store.InMemoryEventStore`
- 作用：未写 docstring；静态推断为所属类上的 `append many` 行为。
- 直接原始调用：`self.append`
- 已解析到仓库内部的调用：`qts.runtime.event_store.InMemoryEventStore.append`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.event_store.InMemoryEventStore.replay`

- 位置：`backend/src/qts/runtime/event_store.py:39-42`
- 类型：`method`
- 签名：`def replay(self, *, partition_key: str | None = None) -> tuple`
- 所属：`qts.runtime.event_store.InMemoryEventStore`
- 作用：未写 docstring；静态推断为所属类上的 `replay` 行为。
- 直接原始调用：`tuple` x2
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.event_store.InMemoryEventStore.by_correlation_id`

- 位置：`backend/src/qts/runtime/event_store.py:44-45`
- 类型：`method`
- 签名：`def by_correlation_id(self, correlation_id: CorrelationId) -> tuple`
- 所属：`qts.runtime.event_store.InMemoryEventStore`
- 作用：未写 docstring；静态推断为所属类上的 `by correlation id` 行为。
- 直接原始调用：`tuple`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.event_store.FileEventStore`

- 位置：`backend/src/qts/runtime/event_store.py:48-103`
- 类型：`class`
- 签名：`class FileEventStore`
- 作用：JSONL event store for local deterministic recovery tests.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.event_store.FileEventStore.__init__`

- 位置：`backend/src/qts/runtime/event_store.py:51-52`
- 类型：`method`
- 签名：`def __init__(self, path: Path) -> None`
- 所属：`qts.runtime.event_store.FileEventStore`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.event_store.FileEventStore.append`

- 位置：`backend/src/qts/runtime/event_store.py:54-61`
- 类型：`method`
- 签名：`def append(self, event: BaseEvent) -> int`
- 所属：`qts.runtime.event_store.FileEventStore`
- 作用：未写 docstring；静态推断为所属类上的 `append` 行为。
- 直接原始调用：`handle.write` x2, `json.dumps`, `len`, `self._event_to_json`, `self._path.open`, `self._path.parent.mkdir`, `self.replay`
- 已解析到仓库内部的调用：`qts.runtime.event_store.FileEventStore._event_to_json`, `qts.runtime.event_store.FileEventStore.replay`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.event_store.FileEventStore.replay`

- 位置：`backend/src/qts/runtime/event_store.py:63-74`
- 类型：`method`
- 签名：`def replay(self, *, partition_key: str | None = None) -> tuple`
- 所属：`qts.runtime.event_store.FileEventStore`
- 作用：未写 docstring；静态推断为所属类上的 `replay` 行为。
- 直接原始调用：`events.append`, `json.loads`, `line.strip`, `self._event_from_json`, `self._path.exists`, `self._path.open`, `tuple`
- 已解析到仓库内部的调用：`qts.runtime.event_store.FileEventStore._event_from_json`
- 被以下仓库内部符号调用：`qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.FileEventStore.by_correlation_id`

#### `qts.runtime.event_store.FileEventStore.by_correlation_id`

- 位置：`backend/src/qts/runtime/event_store.py:76-77`
- 类型：`method`
- 签名：`def by_correlation_id(self, correlation_id: CorrelationId) -> tuple`
- 所属：`qts.runtime.event_store.FileEventStore`
- 作用：未写 docstring；静态推断为所属类上的 `by correlation id` 行为。
- 直接原始调用：`self.replay`, `tuple`
- 已解析到仓库内部的调用：`qts.runtime.event_store.FileEventStore.replay`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.event_store.FileEventStore._event_to_json`

- 位置：`backend/src/qts/runtime/event_store.py:80-89`
- 类型：`staticmethod`
- 签名：`def _event_to_json(event: BaseEvent) -> dict`
- 所属：`qts.runtime.event_store.FileEventStore`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `event to json` 行为。
- 直接原始调用：`event.event_time.isoformat`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.event_store.FileEventStore.append`

#### `qts.runtime.event_store.FileEventStore._event_from_json`

- 位置：`backend/src/qts/runtime/event_store.py:92-103`
- 类型：`staticmethod`
- 签名：`def _event_from_json(payload: dict) -> BaseEvent`
- 所属：`qts.runtime.event_store.FileEventStore`
- 装饰器：`staticmethod`
- 作用：未写 docstring；静态推断为所属类上的 `event from json` 行为。
- 直接原始调用：`str` x7, `BaseEvent`, `CausationId`, `CorrelationId`, `EventId`, `datetime.fromisoformat`
- 已解析到仓库内部的调用：`qts.core.ids.CausationId`, `qts.core.ids.CorrelationId`, `qts.core.ids.EventId`, `qts.domain.events.event.BaseEvent`
- 被以下仓库内部符号调用：`qts.runtime.event_store.FileEventStore.replay`

### `backend/src/qts/runtime/live.py`

模块：`qts.runtime.live`

#### `qts.runtime.live.LiveRuntimeState`

- 位置：`backend/src/qts/runtime/live.py:12-17`
- 类型：`class`
- 签名：`class LiveRuntimeState(StrEnum)`
- 继承/基类：`StrEnum`
- 作用：未写 docstring；静态推断为定义 Live Runtime State 概念，继承/实现 StrEnum。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.live.LiveMode`

- 位置：`backend/src/qts/runtime/live.py:20-25`
- 类型：`class`
- 签名：`class LiveMode(StrEnum)`
- 继承/基类：`StrEnum`
- 作用：Runtime mode with explicit live-trading permissions.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.live.LiveStartupConfig`

- 位置：`backend/src/qts/runtime/live.py:29-37`
- 类型：`class`
- 签名：`class LiveStartupConfig`
- 装饰器：`dataclass()`
- 作用：Startup guard inputs for live-capable runtime.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.live.LiveStartupDecision`

- 位置：`backend/src/qts/runtime/live.py:41-45`
- 类型：`class`
- 签名：`class LiveStartupDecision`
- 装饰器：`dataclass()`
- 作用：Result of startup guard validation.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.live.validate_live_startup`

#### `qts.runtime.live.validate_live_startup`

- 位置：`backend/src/qts/runtime/live.py:48-67`
- 类型：`module_function`
- 签名：`def validate_live_startup(config: LiveStartupConfig) -> LiveStartupDecision`
- 作用：Fail closed unless all live safety prerequisites are explicit.
- 直接原始调用：`', '.join`, `LiveStartupDecision`, `ValueError`
- 已解析到仓库内部的调用：`qts.runtime.live.LiveStartupDecision`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.live.LiveRuntimeStateMachine`

- 位置：`backend/src/qts/runtime/live.py:95-103`
- 类型：`class`
- 签名：`class LiveRuntimeStateMachine`
- 装饰器：`dataclass()`
- 作用：未写 docstring；静态推断为定义 Live Runtime State Machine 概念或数据结构。
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.live.LiveRuntime.__init__`

#### `qts.runtime.live.LiveRuntimeStateMachine.apply`

- 位置：`backend/src/qts/runtime/live.py:98-103`
- 类型：`method`
- 签名：`def apply(self, command: str) -> LiveRuntimeState`
- 所属：`qts.runtime.live.LiveRuntimeStateMachine`
- 作用：未写 docstring；静态推断为应用状态变更、规则或计算结果（名称：apply）。
- 直接原始调用：`ValueError`, `_TRANSITIONS.get`, `_TRANSITIONS.get().get`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.live.RuntimeOrderResult`

- 位置：`backend/src/qts/runtime/live.py:107-111`
- 类型：`class`
- 签名：`class RuntimeOrderResult`
- 装饰器：`dataclass()`
- 作用：未写 docstring；静态推断为定义 Runtime Order Result 概念或数据结构。
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.live.LiveRuntime.submit_order`

#### `qts.runtime.live.LiveRuntime`

- 位置：`backend/src/qts/runtime/live.py:114-158`
- 类型：`class`
- 签名：`class LiveRuntime`
- 作用：Small live-beta runtime wrapper over fake or real boundary adapters.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.live.LiveRuntime.__init__`

- 位置：`backend/src/qts/runtime/live.py:117-120`
- 类型：`method`
- 签名：`def __init__(self, *, broker: BrokerAdapter, feed: LiveFeedAdapter) -> None`
- 所属：`qts.runtime.live.LiveRuntime`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：`LiveRuntimeStateMachine`
- 已解析到仓库内部的调用：`qts.runtime.live.LiveRuntimeStateMachine`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.live.LiveRuntime.state`

- 位置：`backend/src/qts/runtime/live.py:123-124`
- 类型：`property`
- 签名：`def state(self) -> LiveRuntimeState`
- 所属：`qts.runtime.live.LiveRuntime`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为所属类上的 `state` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.live.LiveRuntime.feed`

- 位置：`backend/src/qts/runtime/live.py:127-128`
- 类型：`property`
- 签名：`def feed(self) -> LiveFeedAdapter`
- 所属：`qts.runtime.live.LiveRuntime`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为所属类上的 `feed` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.live.LiveRuntime.start`

- 位置：`backend/src/qts/runtime/live.py:130-132`
- 类型：`method`
- 签名：`def start(self) -> LiveRuntimeState`
- 所属：`qts.runtime.live.LiveRuntime`
- 作用：未写 docstring；静态推断为启动流程或服务（名称：start）。
- 直接原始调用：`self._machine.apply` x2
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.live.LiveRuntime.stop`

- 位置：`backend/src/qts/runtime/live.py:134-135`
- 类型：`method`
- 签名：`def stop(self) -> LiveRuntimeState`
- 所属：`qts.runtime.live.LiveRuntime`
- 作用：未写 docstring；静态推断为停止流程或服务（名称：stop）。
- 直接原始调用：`self._machine.apply`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.live.LiveRuntime.pause`

- 位置：`backend/src/qts/runtime/live.py:137-138`
- 类型：`method`
- 签名：`def pause(self) -> LiveRuntimeState`
- 所属：`qts.runtime.live.LiveRuntime`
- 作用：未写 docstring；静态推断为所属类上的 `pause` 行为。
- 直接原始调用：`self._machine.apply`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.live.LiveRuntime.resume`

- 位置：`backend/src/qts/runtime/live.py:140-141`
- 类型：`method`
- 签名：`def resume(self) -> LiveRuntimeState`
- 所属：`qts.runtime.live.LiveRuntime`
- 作用：未写 docstring；静态推断为所属类上的 `resume` 行为。
- 直接原始调用：`self._machine.apply`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.live.LiveRuntime.degrade`

- 位置：`backend/src/qts/runtime/live.py:143-144`
- 类型：`method`
- 签名：`def degrade(self) -> LiveRuntimeState`
- 所属：`qts.runtime.live.LiveRuntime`
- 作用：未写 docstring；静态推断为所属类上的 `degrade` 行为。
- 直接原始调用：`self._machine.apply`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.live.LiveRuntime.recover`

- 位置：`backend/src/qts/runtime/live.py:146-147`
- 类型：`method`
- 签名：`def recover(self) -> LiveRuntimeState`
- 所属：`qts.runtime.live.LiveRuntime`
- 作用：未写 docstring；静态推断为所属类上的 `recover` 行为。
- 直接原始调用：`self._machine.apply`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.live.LiveRuntime.submit_order`

- 位置：`backend/src/qts/runtime/live.py:149-158`
- 类型：`method`
- 签名：`def submit_order(self, request: BrokerOrderRequest) -> RuntimeOrderResult`
- 所属：`qts.runtime.live.LiveRuntime`
- 作用：未写 docstring；静态推断为所属类上的 `submit order` 行为。
- 直接原始调用：`RuntimeOrderResult` x3, `self._broker.submit_order`
- 已解析到仓库内部的调用：`qts.runtime.live.RuntimeOrderResult`
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/runtime/mailbox.py`

模块：`qts.runtime.mailbox`

#### `qts.runtime.mailbox.Mailbox`

- 位置：`backend/src/qts/runtime/mailbox.py:8-25`
- 类型：`class`
- 签名：`class Mailbox`
- 作用：Simple in-memory FIFO mailbox.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._market_data_ref_for`, `qts.backtest.engine.BacktestEngine._run_actor_loop`

#### `qts.runtime.mailbox.Mailbox.__init__`

- 位置：`backend/src/qts/runtime/mailbox.py:11-12`
- 类型：`method`
- 签名：`def __init__(self) -> None`
- 所属：`qts.runtime.mailbox.Mailbox`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：`deque`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.mailbox.Mailbox.size`

- 位置：`backend/src/qts/runtime/mailbox.py:15-16`
- 类型：`property`
- 签名：`def size(self) -> int`
- 所属：`qts.runtime.mailbox.Mailbox`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为所属类上的 `size` 行为。
- 直接原始调用：`len`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.mailbox.Mailbox.put`

- 位置：`backend/src/qts/runtime/mailbox.py:18-19`
- 类型：`method`
- 签名：`def put(self, message: object) -> None`
- 所属：`qts.runtime.mailbox.Mailbox`
- 作用：未写 docstring；静态推断为所属类上的 `put` 行为。
- 直接原始调用：`self._messages.append`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.mailbox.Mailbox.get`

- 位置：`backend/src/qts/runtime/mailbox.py:21-22`
- 类型：`method`
- 签名：`def get(self) -> object`
- 所属：`qts.runtime.mailbox.Mailbox`
- 作用：未写 docstring；静态推断为读取或返回值（名称：get）。
- 直接原始调用：`self._messages.popleft`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.mailbox.Mailbox.empty`

- 位置：`backend/src/qts/runtime/mailbox.py:24-25`
- 类型：`method`
- 签名：`def empty(self) -> bool`
- 所属：`qts.runtime.mailbox.Mailbox`
- 作用：未写 docstring；静态推断为所属类上的 `empty` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/runtime/partitioning.py`

模块：`qts.runtime.partitioning`

#### `qts.runtime.partitioning.AccountPartitionPolicy`

- 位置：`backend/src/qts/runtime/partitioning.py:11-15`
- 类型：`class`
- 签名：`class AccountPartitionPolicy`
- 作用：Partition live state and messages by internal account id.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.partitioning.AccountPartitionPolicy.partition_for`

- 位置：`backend/src/qts/runtime/partitioning.py:14-15`
- 类型：`method`
- 签名：`def partition_for(self, account_id: AccountId) -> str`
- 所属：`qts.runtime.partitioning.AccountPartitionPolicy`
- 作用：未写 docstring；静态推断为所属类上的 `partition for` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.partitioning.AccountBrokerMapping`

- 位置：`backend/src/qts/runtime/partitioning.py:19-34`
- 类型：`class`
- 签名：`class AccountBrokerMapping`
- 装饰器：`dataclass()`
- 作用：Boundary-only broker account mapping.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.partitioning.AccountBrokerMapping.__post_init__`

- 位置：`backend/src/qts/runtime/partitioning.py:26-28`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.runtime.partitioning.AccountBrokerMapping`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError`, `self.broker_account_id.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.partitioning.AccountBrokerMapping.boundary_payload`

- 位置：`backend/src/qts/runtime/partitioning.py:30-34`
- 类型：`method`
- 签名：`def boundary_payload(self) -> dict`
- 所属：`qts.runtime.partitioning.AccountBrokerMapping`
- 作用：未写 docstring；静态推断为所属类上的 `boundary payload` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.partitioning.AccountRiskConfig`

- 位置：`backend/src/qts/runtime/partitioning.py:38-52`
- 类型：`class`
- 签名：`class AccountRiskConfig`
- 装饰器：`dataclass()`
- 作用：Per-account live risk limits.
- 直接原始调用：`dataclass`, `field`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.partitioning.AccountRiskConfig.__post_init__`

- 位置：`backend/src/qts/runtime/partitioning.py:45-49`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.runtime.partitioning.AccountRiskConfig`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`Decimal` x2, `ValueError` x2, `any`, `self.instrument_limits.values`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.partitioning.AccountRiskConfig.limit_for`

- 位置：`backend/src/qts/runtime/partitioning.py:51-52`
- 类型：`method`
- 签名：`def limit_for(self, instrument_id: InstrumentId) -> Decimal`
- 所属：`qts.runtime.partitioning.AccountRiskConfig`
- 作用：未写 docstring；静态推断为所属类上的 `limit for` 行为。
- 直接原始调用：`self.instrument_limits.get`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/runtime/router.py`

模块：`qts.runtime.router`

#### `qts.runtime.router.RouteNotFoundError`

- 位置：`backend/src/qts/runtime/router.py:8-9`
- 类型：`class`
- 签名：`class RouteNotFoundError(KeyError)`
- 继承/基类：`KeyError`
- 作用：Raised when no actor route exists for a partition key.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.router.EventRouter.route`

#### `qts.runtime.router.EventRouter`

- 位置：`backend/src/qts/runtime/router.py:12-30`
- 类型：`class`
- 签名：`class EventRouter`
- 作用：Route messages to actor refs by a configured message attribute.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.router.EventRouter.__init__`

- 位置：`backend/src/qts/runtime/router.py:15-19`
- 类型：`method`
- 签名：`def __init__(self, *, partition_attr: str) -> None`
- 所属：`qts.runtime.router.EventRouter`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：`ValueError`, `partition_attr.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.router.EventRouter.register`

- 位置：`backend/src/qts/runtime/router.py:21-22`
- 类型：`method`
- 签名：`def register(self, key: object, actor_ref: ActorRef) -> None`
- 所属：`qts.runtime.router.EventRouter`
- 作用：未写 docstring；静态推断为所属类上的 `register` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.router.EventRouter.route`

- 位置：`backend/src/qts/runtime/router.py:24-30`
- 类型：`method`
- 签名：`def route(self, message: object) -> None`
- 所属：`qts.runtime.router.EventRouter`
- 作用：未写 docstring；静态推断为所属类上的 `route` 行为。
- 直接原始调用：`RouteNotFoundError`, `actor_ref.tell`, `getattr`
- 已解析到仓库内部的调用：`qts.runtime.router.RouteNotFoundError`
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/runtime/state_recovery.py`

模块：`qts.runtime.state_recovery`

#### `qts.runtime.state_recovery.StateSnapshot`

- 位置：`backend/src/qts/runtime/state_recovery.py:10-21`
- 类型：`class`
- 签名：`class StateSnapshot`
- 装饰器：`dataclass()`
- 作用：Serialized actor state snapshot envelope.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.state_recovery.StateSnapshot.__post_init__`

- 位置：`backend/src/qts/runtime/state_recovery.py:17-21`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.runtime.state_recovery.StateSnapshot`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x2, `self.actor_id.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.state_recovery.InMemorySnapshotStore`

- 位置：`backend/src/qts/runtime/state_recovery.py:24-36`
- 类型：`class`
- 签名：`class InMemorySnapshotStore`
- 作用：In-memory snapshot store for deterministic tests and local recovery.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.state_recovery.InMemorySnapshotStore.__init__`

- 位置：`backend/src/qts/runtime/state_recovery.py:27-28`
- 类型：`method`
- 签名：`def __init__(self) -> None`
- 所属：`qts.runtime.state_recovery.InMemorySnapshotStore`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.state_recovery.InMemorySnapshotStore.save`

- 位置：`backend/src/qts/runtime/state_recovery.py:30-31`
- 类型：`method`
- 签名：`def save(self, snapshot: StateSnapshot) -> None`
- 所属：`qts.runtime.state_recovery.InMemorySnapshotStore`
- 作用：未写 docstring；静态推断为保存数据或状态（名称：save）。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.runtime.state_recovery.InMemorySnapshotStore.load`

- 位置：`backend/src/qts/runtime/state_recovery.py:33-36`
- 类型：`method`
- 签名：`def load(self, actor_id: str) -> StateSnapshot | None`
- 所属：`qts.runtime.state_recovery.InMemorySnapshotStore`
- 作用：未写 docstring；静态推断为加载数据或配置（名称：load）。
- 直接原始调用：`ValueError`, `actor_id.strip`, `self._snapshots.get`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/strategy_sdk/__init__.py`

模块：`qts.strategy_sdk`

无类或函数定义。

### `backend/src/qts/strategy_sdk/asset_ref.py`

模块：`qts.strategy_sdk.asset_ref`

#### `qts.strategy_sdk.asset_ref.AssetRef`

- 位置：`backend/src/qts/strategy_sdk/asset_ref.py:13-26`
- 类型：`class`
- 签名：`class AssetRef`
- 装饰器：`dataclass()`
- 作用：Lightweight strategy-facing reference to an internal instrument.
- 直接原始调用：`dataclass`, `field`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.strategy_sdk.context.StrategyContext.future`, `qts.strategy_sdk.context.StrategyContext.option`, `qts.strategy_sdk.context.StrategyContext.symbol`

#### `qts.strategy_sdk.asset_ref.AssetRef.__post_init__`

- 位置：`backend/src/qts/strategy_sdk/asset_ref.py:20-23`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.strategy_sdk.asset_ref.AssetRef`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`MappingProxyType`, `ValueError`, `dict`, `object.__setattr__`, `self.symbol.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.strategy_sdk.asset_ref.AssetRef.__hash__`

- 位置：`backend/src/qts/strategy_sdk/asset_ref.py:25-26`
- 类型：`method`
- 签名：`def __hash__(self) -> int`
- 所属：`qts.strategy_sdk.asset_ref.AssetRef`
- 作用：未写 docstring；实现 Python 协议方法 `__hash__`。
- 直接原始调用：`hash`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/strategy_sdk/context.py`

模块：`qts.strategy_sdk.context`

#### `qts.strategy_sdk.context.SymbolResolver`

- 位置：`backend/src/qts/strategy_sdk/context.py:21-24`
- 类型：`class`
- 签名：`class SymbolResolver(Protocol)`
- 继承/基类：`Protocol`
- 作用：Platform-provided symbol resolution boundary.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.strategy_sdk.context.SymbolResolver.resolve`

- 位置：`backend/src/qts/strategy_sdk/context.py:24-24`
- 类型：`method`
- 签名：`def resolve(self, user_symbol: str) -> InstrumentId`
- 所属：`qts.strategy_sdk.context.SymbolResolver`
- 作用：未写 docstring；静态推断为解析标识、引用或配置到目标对象（名称：resolve）。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.strategy_sdk.context.FutureContractResolver`

- 位置：`backend/src/qts/strategy_sdk/context.py:27-30`
- 类型：`class`
- 签名：`class FutureContractResolver(Protocol)`
- 继承/基类：`Protocol`
- 作用：Platform-provided future chain resolution boundary.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.strategy_sdk.context.FutureContractResolver.resolve_contract`

- 位置：`backend/src/qts/strategy_sdk/context.py:30-30`
- 类型：`method`
- 签名：`def resolve_contract(self, root_symbol: str, *, offset: int = 0) -> InstrumentId`
- 所属：`qts.strategy_sdk.context.FutureContractResolver`
- 作用：未写 docstring；静态推断为解析标识、引用或配置到目标对象（名称：resolve contract）。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.strategy_sdk.context.ContinuousFutureResolver`

- 位置：`backend/src/qts/strategy_sdk/context.py:33-36`
- 类型：`class`
- 签名：`class ContinuousFutureResolver(Protocol)`
- 继承/基类：`Protocol`
- 作用：Platform-provided rolling future reference boundary.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.strategy_sdk.context.ContinuousFutureResolver.continuous_instrument_id`

- 位置：`backend/src/qts/strategy_sdk/context.py:36-36`
- 类型：`method`
- 签名：`def continuous_instrument_id(self, root_symbol: str, *, offset: int = 0) -> InstrumentId`
- 所属：`qts.strategy_sdk.context.ContinuousFutureResolver`
- 作用：未写 docstring；静态推断为所属类上的 `continuous instrument id` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.strategy_sdk.context.OptionContractRef`

- 位置：`backend/src/qts/strategy_sdk/context.py:39-43`
- 类型：`class`
- 签名：`class OptionContractRef(Protocol)`
- 继承/基类：`Protocol`
- 作用：Read-only option contract reference returned by the platform.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.strategy_sdk.context.OptionContractRef.instrument_id`

- 位置：`backend/src/qts/strategy_sdk/context.py:43-43`
- 类型：`property`
- 签名：`def instrument_id(self) -> InstrumentId`
- 所属：`qts.strategy_sdk.context.OptionContractRef`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为所属类上的 `instrument id` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.strategy_sdk.context.OptionContractResolver`

- 位置：`backend/src/qts/strategy_sdk/context.py:46-56`
- 类型：`class`
- 签名：`class OptionContractResolver(Protocol)`
- 继承/基类：`Protocol`
- 作用：Platform-provided option chain resolution boundary.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.strategy_sdk.context.OptionContractResolver.find`

- 位置：`backend/src/qts/strategy_sdk/context.py:49-56`
- 类型：`method`
- 签名：`def find(self, *, underlying: InstrumentId, expiry: date | None = None, strike: Decimal | None = None, right: OptionRight | None = None) -> Sequence`
- 所属：`qts.strategy_sdk.context.OptionContractResolver`
- 作用：未写 docstring；静态推断为所属类上的 `find` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.strategy_sdk.context.DataSubscription`

- 位置：`backend/src/qts/strategy_sdk/context.py:60-71`
- 类型：`class`
- 签名：`class DataSubscription`
- 装饰器：`dataclass()`
- 作用：Strategy-declared market data requirement.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.strategy_sdk.context.StrategyContext.subscribe`

#### `qts.strategy_sdk.context.DataSubscription.__post_init__`

- 位置：`backend/src/qts/strategy_sdk/context.py:67-71`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.strategy_sdk.context.DataSubscription`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`ValueError` x2, `self.timeframe.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.strategy_sdk.context.StrategyContext`

- 位置：`backend/src/qts/strategy_sdk/context.py:75-171`
- 类型：`class`
- 签名：`class StrategyContext`
- 装饰器：`dataclass()`
- 作用：User-facing strategy context.
- 直接原始调用：`field` x4, `dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._run_actor_loop`

#### `qts.strategy_sdk.context.StrategyContext.intents`

- 位置：`backend/src/qts/strategy_sdk/context.py:89-90`
- 类型：`property`
- 签名：`def intents(self) -> tuple`
- 所属：`qts.strategy_sdk.context.StrategyContext`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为所属类上的 `intents` 行为。
- 直接原始调用：`tuple`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.strategy_sdk.context.StrategyContext.subscriptions`

- 位置：`backend/src/qts/strategy_sdk/context.py:93-94`
- 类型：`property`
- 签名：`def subscriptions(self) -> tuple`
- 所属：`qts.strategy_sdk.context.StrategyContext`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为所属类上的 `subscriptions` 行为。
- 直接原始调用：`tuple`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.strategy_sdk.context.StrategyContext.symbol`

- 位置：`backend/src/qts/strategy_sdk/context.py:96-100`
- 类型：`method`
- 签名：`def symbol(self, user_symbol: str) -> AssetRef`
- 所属：`qts.strategy_sdk.context.StrategyContext`
- 作用：未写 docstring；静态推断为所属类上的 `symbol` 行为。
- 直接原始调用：`AssetRef`, `RuntimeError`, `self.instrument_registry.resolve`
- 已解析到仓库内部的调用：`qts.strategy_sdk.asset_ref.AssetRef`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.strategy_sdk.context.StrategyContext.future`

- 位置：`backend/src/qts/strategy_sdk/context.py:102-120`
- 类型：`method`
- 签名：`def future(self, root_symbol: str, *, contract: str = 'front') -> AssetRef`
- 所属：`qts.strategy_sdk.context.StrategyContext`
- 作用：未写 docstring；静态推断为所属类上的 `future` 行为。
- 直接原始调用：`AssetRef`, `RuntimeError`, `ValueError`, `callable`, `cast`, `cast().resolve_contract`, `continuous_id`, `getattr`
- 已解析到仓库内部的调用：`qts.strategy_sdk.asset_ref.AssetRef`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.strategy_sdk.context.StrategyContext.option`

- 位置：`backend/src/qts/strategy_sdk/context.py:122-141`
- 类型：`method`
- 签名：`def option(self, *, underlying: InstrumentId, expiry: date, strike: Decimal, right: OptionRight) -> AssetRef`
- 所属：`qts.strategy_sdk.context.StrategyContext`
- 作用：未写 docstring；静态推断为所属类上的 `option` 行为。
- 直接原始调用：`AssetRef`, `KeyError`, `RuntimeError`, `self.option_chain_registry.find`, `str`
- 已解析到仓库内部的调用：`qts.strategy_sdk.asset_ref.AssetRef`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.strategy_sdk.context.StrategyContext.target_percent`

- 位置：`backend/src/qts/strategy_sdk/context.py:143-146`
- 类型：`method`
- 签名：`def target_percent(self, asset: AssetRef, weight: Decimal) -> TargetIntent`
- 所属：`qts.strategy_sdk.context.StrategyContext`
- 作用：未写 docstring；静态推断为所属类上的 `target percent` 行为。
- 直接原始调用：`TargetIntent`, `self._emit`
- 已解析到仓库内部的调用：`qts.strategy_sdk.context.StrategyContext._emit`, `qts.strategy_sdk.target.TargetIntent`
- 被以下仓库内部符号调用：`qts.strategy_sdk.context.StrategyContext.rebalance`

#### `qts.strategy_sdk.context.StrategyContext.target_quantity`

- 位置：`backend/src/qts/strategy_sdk/context.py:148-151`
- 类型：`method`
- 签名：`def target_quantity(self, asset: AssetRef, quantity: Decimal) -> TargetIntent`
- 所属：`qts.strategy_sdk.context.StrategyContext`
- 作用：未写 docstring；静态推断为所属类上的 `target quantity` 行为。
- 直接原始调用：`TargetIntent`, `self._emit`
- 已解析到仓库内部的调用：`qts.strategy_sdk.context.StrategyContext._emit`, `qts.strategy_sdk.target.TargetIntent`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.strategy_sdk.context.StrategyContext.target_value`

- 位置：`backend/src/qts/strategy_sdk/context.py:153-156`
- 类型：`method`
- 签名：`def target_value(self, asset: AssetRef, value: Decimal) -> TargetIntent`
- 所属：`qts.strategy_sdk.context.StrategyContext`
- 作用：未写 docstring；静态推断为所属类上的 `target value` 行为。
- 直接原始调用：`TargetIntent`, `self._emit`
- 已解析到仓库内部的调用：`qts.strategy_sdk.context.StrategyContext._emit`, `qts.strategy_sdk.target.TargetIntent`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.strategy_sdk.context.StrategyContext.close`

- 位置：`backend/src/qts/strategy_sdk/context.py:158-159`
- 类型：`method`
- 签名：`def close(self, asset: AssetRef) -> TargetIntent`
- 所属：`qts.strategy_sdk.context.StrategyContext`
- 作用：未写 docstring；静态推断为关闭资源或头寸（名称：close）。
- 直接原始调用：`TargetIntent`, `self._emit`
- 已解析到仓库内部的调用：`qts.strategy_sdk.context.StrategyContext._emit`, `qts.strategy_sdk.target.TargetIntent`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.strategy_sdk.context.StrategyContext.rebalance`

- 位置：`backend/src/qts/strategy_sdk/context.py:161-162`
- 类型：`method`
- 签名：`def rebalance(self, weights: dict) -> tuple`
- 所属：`qts.strategy_sdk.context.StrategyContext`
- 作用：未写 docstring；静态推断为所属类上的 `rebalance` 行为。
- 直接原始调用：`self.target_percent`, `tuple`, `weights.items`
- 已解析到仓库内部的调用：`qts.strategy_sdk.context.StrategyContext.target_percent`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.strategy_sdk.context.StrategyContext.subscribe`

- 位置：`backend/src/qts/strategy_sdk/context.py:164-167`
- 类型：`method`
- 签名：`def subscribe(self, asset: AssetRef, *, timeframe: str, warmup: int = 1) -> DataSubscription`
- 所属：`qts.strategy_sdk.context.StrategyContext`
- 作用：未写 docstring；静态推断为所属类上的 `subscribe` 行为。
- 直接原始调用：`DataSubscription`, `self._subscriptions.append`
- 已解析到仓库内部的调用：`qts.strategy_sdk.context.DataSubscription`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.strategy_sdk.context.StrategyContext._emit`

- 位置：`backend/src/qts/strategy_sdk/context.py:169-171`
- 类型：`method`
- 签名：`def _emit(self, intent: TargetIntent) -> TargetIntent`
- 所属：`qts.strategy_sdk.context.StrategyContext`
- 作用：未写 docstring；静态推断为所属类上的 `emit` 行为。
- 直接原始调用：`self._intents.append`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.strategy_sdk.context.StrategyContext.close`, `qts.strategy_sdk.context.StrategyContext.target_percent`, `qts.strategy_sdk.context.StrategyContext.target_quantity`, `qts.strategy_sdk.context.StrategyContext.target_value`

### `backend/src/qts/strategy_sdk/data_view.py`

模块：`qts.strategy_sdk.data_view`

#### `qts.strategy_sdk.data_view.DataView`

- 位置：`backend/src/qts/strategy_sdk/data_view.py:16-43`
- 类型：`class`
- 签名：`class DataView`
- 装饰器：`dataclass()`
- 作用：Time-sliced market data exposed to strategies.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.historical_data_portal.HistoricalDataPortal.data_view`

#### `qts.strategy_sdk.data_view.DataView.close`

- 位置：`backend/src/qts/strategy_sdk/data_view.py:22-23`
- 类型：`method`
- 签名：`def close(self, asset: AssetRef) -> Decimal`
- 所属：`qts.strategy_sdk.data_view.DataView`
- 作用：未写 docstring；静态推断为关闭资源或头寸（名称：close）。
- 直接原始调用：`self.bar`
- 已解析到仓库内部的调用：`qts.strategy_sdk.data_view.DataView.bar`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.strategy_sdk.data_view.DataView.bar`

- 位置：`backend/src/qts/strategy_sdk/data_view.py:25-29`
- 类型：`method`
- 签名：`def bar(self, asset: AssetRef) -> Bar`
- 所属：`qts.strategy_sdk.data_view.DataView`
- 作用：未写 docstring；静态推断为所属类上的 `bar` 行为。
- 直接原始调用：`KeyError`, `self.history`
- 已解析到仓库内部的调用：`qts.strategy_sdk.data_view.DataView.history`
- 被以下仓库内部符号调用：`qts.strategy_sdk.data_view.DataView.close`

#### `qts.strategy_sdk.data_view.DataView.history`

- 位置：`backend/src/qts/strategy_sdk/data_view.py:31-43`
- 类型：`method`
- 签名：`def history(self, asset: AssetRef, bars: int, timeframe: str | None = None) -> tuple`
- 所属：`qts.strategy_sdk.data_view.DataView`
- 作用：未写 docstring；静态推断为所属类上的 `history` 行为。
- 直接原始调用：`ValueError`, `self.bars.get`, `tuple`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.strategy_sdk.data_view.DataView.bar`

### `backend/src/qts/strategy_sdk/factors.py`

模块：`qts.strategy_sdk.factors`

#### `qts.strategy_sdk.factors.FactorFactory`

- 位置：`backend/src/qts/strategy_sdk/factors.py:11-15`
- 类型：`class`
- 签名：`class FactorFactory`
- 装饰器：`dataclass()`
- 作用：Factory for user-created factors.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.strategy_sdk.factors.FactorFactory.momentum`

- 位置：`backend/src/qts/strategy_sdk/factors.py:14-15`
- 类型：`method`
- 签名：`def momentum(self, *, window: int) -> MomentumFactor`
- 所属：`qts.strategy_sdk.factors.FactorFactory`
- 作用：未写 docstring；静态推断为所属类上的 `momentum` 行为。
- 直接原始调用：`MomentumFactor`
- 已解析到仓库内部的调用：`qts.factors.momentum.MomentumFactor`
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/strategy_sdk/indicators.py`

模块：`qts.strategy_sdk.indicators`

#### `qts.strategy_sdk.indicators.AssetIndicator`

- 位置：`backend/src/qts/strategy_sdk/indicators.py:14-29`
- 类型：`class`
- 签名：`class AssetIndicator`
- 装饰器：`dataclass()`
- 作用：Indicator bound to a strategy asset reference.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.strategy_sdk.indicators.IndicatorFactory.sma`

#### `qts.strategy_sdk.indicators.AssetIndicator.ready`

- 位置：`backend/src/qts/strategy_sdk/indicators.py:21-22`
- 类型：`property`
- 签名：`def ready(self) -> bool`
- 所属：`qts.strategy_sdk.indicators.AssetIndicator`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为读取数据（名称：ready）。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.strategy_sdk.indicators.AssetIndicator.value`

- 位置：`backend/src/qts/strategy_sdk/indicators.py:25-26`
- 类型：`property`
- 签名：`def value(self) -> Decimal | None`
- 所属：`qts.strategy_sdk.indicators.AssetIndicator`
- 装饰器：`property`
- 作用：未写 docstring；静态推断为所属类上的 `value` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.strategy_sdk.indicators.AssetIndicator.update`

- 位置：`backend/src/qts/strategy_sdk/indicators.py:28-29`
- 类型：`method`
- 签名：`def update(self, price: Decimal) -> Decimal | None`
- 所属：`qts.strategy_sdk.indicators.AssetIndicator`
- 作用：未写 docstring；静态推断为所属类上的 `update` 行为。
- 直接原始调用：`self.indicator.update`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.strategy_sdk.indicators.IndicatorFactory`

- 位置：`backend/src/qts/strategy_sdk/indicators.py:33-46`
- 类型：`class`
- 签名：`class IndicatorFactory`
- 装饰器：`dataclass()`
- 作用：Factory for user-created indicators.
- 直接原始调用：`dataclass`, `field`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.strategy_sdk.indicators.IndicatorFactory.sma`

- 位置：`backend/src/qts/strategy_sdk/indicators.py:38-41`
- 类型：`method`
- 签名：`def sma(self, asset: AssetRef, window: int) -> AssetIndicator`
- 所属：`qts.strategy_sdk.indicators.IndicatorFactory`
- 作用：未写 docstring；静态推断为所属类上的 `sma` 行为。
- 直接原始调用：`AssetIndicator`, `SMA`, `self._created.append`
- 已解析到仓库内部的调用：`qts.indicators.price.sma.SMA`, `qts.strategy_sdk.indicators.AssetIndicator`
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.strategy_sdk.indicators.IndicatorFactory.update_from_bar`

- 位置：`backend/src/qts/strategy_sdk/indicators.py:43-46`
- 类型：`method`
- 签名：`def update_from_bar(self, bar: Bar) -> None`
- 所属：`qts.strategy_sdk.indicators.IndicatorFactory`
- 作用：未写 docstring；静态推断为所属类上的 `update from bar` 行为。
- 直接原始调用：`item.update`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/strategy_sdk/portfolio_view.py`

模块：`qts.strategy_sdk.portfolio_view`

#### `qts.strategy_sdk.portfolio_view.PortfolioPosition`

- 位置：`backend/src/qts/strategy_sdk/portfolio_view.py:15-19`
- 类型：`class`
- 签名：`class PortfolioPosition`
- 装饰器：`dataclass()`
- 作用：Read-only position snapshot.
- 直接原始调用：`Decimal` x2, `dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._portfolio_view`, `qts.strategy_sdk.portfolio_view.PortfolioView.position`

#### `qts.strategy_sdk.portfolio_view.PortfolioView`

- 位置：`backend/src/qts/strategy_sdk/portfolio_view.py:23-42`
- 类型：`class`
- 签名：`class PortfolioView`
- 装饰器：`dataclass()`
- 作用：Immutable user-facing portfolio snapshot.
- 直接原始调用：`dataclass`, `field`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine._portfolio_view`

#### `qts.strategy_sdk.portfolio_view.PortfolioView.__post_init__`

- 位置：`backend/src/qts/strategy_sdk/portfolio_view.py:30-31`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 所属：`qts.strategy_sdk.portfolio_view.PortfolioView`
- 作用：未写 docstring；dataclass 初始化后执行校验、规范化或派生字段设置。
- 直接原始调用：`MappingProxyType`, `dict`, `object.__setattr__`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.strategy_sdk.portfolio_view.PortfolioView.position`

- 位置：`backend/src/qts/strategy_sdk/portfolio_view.py:33-34`
- 类型：`method`
- 签名：`def position(self, asset: AssetRef) -> PortfolioPosition`
- 所属：`qts.strategy_sdk.portfolio_view.PortfolioView`
- 作用：未写 docstring；静态推断为所属类上的 `position` 行为。
- 直接原始调用：`PortfolioPosition`, `self.positions.get`
- 已解析到仓库内部的调用：`qts.strategy_sdk.portfolio_view.PortfolioPosition`
- 被以下仓库内部符号调用：`qts.strategy_sdk.portfolio_view.PortfolioView.exposure`

#### `qts.strategy_sdk.portfolio_view.PortfolioView.exposure`

- 位置：`backend/src/qts/strategy_sdk/portfolio_view.py:36-37`
- 类型：`method`
- 签名：`def exposure(self, asset: AssetRef) -> Decimal`
- 所属：`qts.strategy_sdk.portfolio_view.PortfolioView`
- 作用：未写 docstring；静态推断为所属类上的 `exposure` 行为。
- 直接原始调用：`self.position`
- 已解析到仓库内部的调用：`qts.strategy_sdk.portfolio_view.PortfolioView.position`
- 被以下仓库内部符号调用：`qts.strategy_sdk.portfolio_view.PortfolioView.weight`

#### `qts.strategy_sdk.portfolio_view.PortfolioView.weight`

- 位置：`backend/src/qts/strategy_sdk/portfolio_view.py:39-42`
- 类型：`method`
- 签名：`def weight(self, asset: AssetRef) -> Decimal`
- 所属：`qts.strategy_sdk.portfolio_view.PortfolioView`
- 作用：未写 docstring；静态推断为所属类上的 `weight` 行为。
- 直接原始调用：`Decimal` x2, `self.exposure`
- 已解析到仓库内部的调用：`qts.strategy_sdk.portfolio_view.PortfolioView.exposure`
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/strategy_sdk/strategy.py`

模块：`qts.strategy_sdk.strategy`

#### `qts.strategy_sdk.strategy.Strategy`

- 位置：`backend/src/qts/strategy_sdk/strategy.py:6-28`
- 类型：`class`
- 签名：`class Strategy`
- 作用：Base class for user strategies.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.strategy_sdk.strategy.Strategy.initialize`

- 位置：`backend/src/qts/strategy_sdk/strategy.py:9-10`
- 类型：`method`
- 签名：`def initialize(self, ctx: object) -> None`
- 所属：`qts.strategy_sdk.strategy.Strategy`
- 作用：未写 docstring；静态推断为所属类上的 `initialize` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.strategy_sdk.strategy.Strategy.on_bar`

- 位置：`backend/src/qts/strategy_sdk/strategy.py:12-13`
- 类型：`method`
- 签名：`def on_bar(self, ctx: object, bar: object) -> None`
- 所属：`qts.strategy_sdk.strategy.Strategy`
- 作用：未写 docstring；静态推断为响应事件或回调（名称：on bar）。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.strategy_sdk.strategy.Strategy.on_tick`

- 位置：`backend/src/qts/strategy_sdk/strategy.py:15-16`
- 类型：`method`
- 签名：`def on_tick(self, ctx: object, tick: object) -> None`
- 所属：`qts.strategy_sdk.strategy.Strategy`
- 作用：未写 docstring；静态推断为响应事件或回调（名称：on tick）。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.strategy_sdk.strategy.Strategy.on_timer`

- 位置：`backend/src/qts/strategy_sdk/strategy.py:18-19`
- 类型：`method`
- 签名：`def on_timer(self, ctx: object, timer: object) -> None`
- 所属：`qts.strategy_sdk.strategy.Strategy`
- 作用：未写 docstring；静态推断为响应事件或回调（名称：on timer）。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.strategy_sdk.strategy.Strategy.on_order_update`

- 位置：`backend/src/qts/strategy_sdk/strategy.py:21-22`
- 类型：`method`
- 签名：`def on_order_update(self, ctx: object, update: object) -> None`
- 所属：`qts.strategy_sdk.strategy.Strategy`
- 作用：未写 docstring；静态推断为响应事件或回调（名称：on order update）。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.strategy_sdk.strategy.Strategy.on_fill`

- 位置：`backend/src/qts/strategy_sdk/strategy.py:24-25`
- 类型：`method`
- 签名：`def on_fill(self, ctx: object, fill: object) -> None`
- 所属：`qts.strategy_sdk.strategy.Strategy`
- 作用：未写 docstring；静态推断为响应事件或回调（名称：on fill）。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.strategy_sdk.strategy.Strategy.finalize`

- 位置：`backend/src/qts/strategy_sdk/strategy.py:27-28`
- 类型：`method`
- 签名：`def finalize(self, ctx: object) -> None`
- 所属：`qts.strategy_sdk.strategy.Strategy`
- 作用：未写 docstring；静态推断为所属类上的 `finalize` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `backend/src/qts/strategy_sdk/target.py`

模块：`qts.strategy_sdk.target`

#### `qts.strategy_sdk.target.TargetIntentType`

- 位置：`backend/src/qts/strategy_sdk/target.py:12-18`
- 类型：`class`
- 签名：`class TargetIntentType(StrEnum)`
- 继承/基类：`StrEnum`
- 作用：Supported target intent kinds.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `qts.strategy_sdk.target.TargetIntent`

- 位置：`backend/src/qts/strategy_sdk/target.py:22-27`
- 类型：`class`
- 签名：`class TargetIntent`
- 装饰器：`dataclass()`
- 作用：Strategy-emitted intent, later handled by platform risk/order flow.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.strategy_sdk.context.StrategyContext.close`, `qts.strategy_sdk.context.StrategyContext.target_percent`, `qts.strategy_sdk.context.StrategyContext.target_quantity`, `qts.strategy_sdk.context.StrategyContext.target_value`

### `backend/src/qts/workers/__init__.py`

模块：`qts.workers`

无类或函数定义。

### `examples/__init__.py`

模块：`examples`

无类或函数定义。

### `examples/strategies/__init__.py`

模块：`examples.strategies`

无类或函数定义。

### `examples/strategies/gc_si_momentum.py`

模块：`examples.strategies.gc_si_momentum`

#### `examples.strategies.gc_si_momentum.GcSiMomentumStrategy`

- 位置：`examples/strategies/gc_si_momentum.py:12-52`
- 类型：`class`
- 签名：`class GcSiMomentumStrategy(Strategy)`
- 继承/基类：`Strategy`
- 作用：Simple moving-average momentum strategy for configured GC/SI symbols.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `examples.strategies.gc_si_momentum.GcSiMomentumStrategy.__init__`

- 位置：`examples/strategies/gc_si_momentum.py:15-31`
- 类型：`method`
- 签名：`def __init__(self, *, symbols: Iterable = ('GC', 'SI'), short_window: int = 1, long_window: int = 2) -> None`
- 所属：`examples.strategies.gc_si_momentum.GcSiMomentumStrategy`
- 作用：未写 docstring；初始化所属类实例并保存/校验构造参数。
- 直接原始调用：`ValueError` x3, `tuple`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `examples.strategies.gc_si_momentum.GcSiMomentumStrategy.initialize`

- 位置：`examples/strategies/gc_si_momentum.py:33-36`
- 类型：`method`
- 签名：`def initialize(self, ctx: StrategyContext) -> None`
- 所属：`examples.strategies.gc_si_momentum.GcSiMomentumStrategy`
- 作用：未写 docstring；静态推断为所属类上的 `initialize` 行为。
- 直接原始调用：`_asset_for_symbol`, `ctx.subscribe`, `tuple`
- 已解析到仓库内部的调用：`examples.strategies.gc_si_momentum._asset_for_symbol`
- 被以下仓库内部符号调用：无静态解析记录

#### `examples.strategies.gc_si_momentum.GcSiMomentumStrategy.on_bar`

- 位置：`examples/strategies/gc_si_momentum.py:38-52`
- 类型：`method`
- 签名：`def on_bar(self, ctx: Any, bar: object) -> None`
- 所属：`examples.strategies.gc_si_momentum.GcSiMomentumStrategy`
- 作用：未写 docstring；静态推断为响应事件或回调（名称：on bar）。
- 直接原始调用：`_average` x2, `Decimal`, `ctx.close`, `ctx.data.history`, `ctx.target_quantity`, `len`
- 已解析到仓库内部的调用：`examples.strategies.gc_si_momentum._average`
- 被以下仓库内部符号调用：无静态解析记录

#### `examples.strategies.gc_si_momentum._average`

- 位置：`examples/strategies/gc_si_momentum.py:55-57`
- 类型：`module_function`
- 签名：`def _average(values: Iterable) -> Decimal`
- 作用：未写 docstring；静态推断为 `average` 函数，具体语义以实现为准。
- 直接原始调用：`Decimal` x2, `len`, `sum`, `tuple`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`examples.strategies.gc_si_momentum.GcSiMomentumStrategy.on_bar`

#### `examples.strategies.gc_si_momentum._asset_for_symbol`

- 位置：`examples/strategies/gc_si_momentum.py:60-64`
- 类型：`module_function`
- 签名：`def _asset_for_symbol(ctx: StrategyContext, symbol: str) -> AssetRef`
- 作用：未写 docstring；静态推断为 `asset for symbol` 函数，具体语义以实现为准。
- 直接原始调用：`ctx.future`, `ctx.symbol`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`examples.strategies.gc_si_momentum.GcSiMomentumStrategy.initialize`

### `examples/strategies/moving_average_cross.py`

模块：`examples.strategies.moving_average_cross`

#### `examples.strategies.moving_average_cross.MovingAverageCross`

- 位置：`examples/strategies/moving_average_cross.py:8-23`
- 类型：`class`
- 签名：`class MovingAverageCross(Strategy)`
- 继承/基类：`Strategy`
- 作用：未写 docstring；静态推断为定义 Moving Average Cross 概念，继承/实现 Strategy。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `examples.strategies.moving_average_cross.MovingAverageCross.initialize`

- 位置：`examples/strategies/moving_average_cross.py:9-12`
- 类型：`method`
- 签名：`def initialize(self, ctx)`
- 所属：`examples.strategies.moving_average_cross.MovingAverageCross`
- 作用：未写 docstring；静态推断为所属类上的 `initialize` 行为。
- 直接原始调用：`ctx.indicator.sma` x2, `ctx.symbol`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `examples.strategies.moving_average_cross.MovingAverageCross.on_bar`

- 位置：`examples/strategies/moving_average_cross.py:14-23`
- 类型：`method`
- 签名：`def on_bar(self, ctx, data)`
- 所属：`examples.strategies.moving_average_cross.MovingAverageCross`
- 作用：未写 docstring；静态推断为响应事件或回调（名称：on bar）。
- 直接原始调用：`Decimal`, `ctx.close`, `ctx.data.close`, `ctx.target_percent`, `self.fast.update`, `self.slow.update`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

### `scripts/__init__.py`

模块：`scripts`

无类或函数定义。

### `scripts/bootstrap.py`

模块：`scripts.bootstrap`

#### `scripts.bootstrap.main`

- 位置：`scripts/bootstrap.py:11-12`
- 类型：`module_function`
- 签名：`def main() -> None`
- 作用：未写 docstring；静态推断为 `main` 函数，具体语义以实现为准。
- 直接原始调用：`Path`, `bootstrap_local`
- 已解析到仓库内部的调用：`qts.load.bootstrap.bootstrap_local`
- 被以下仓库内部符号调用：无静态解析记录

### `scripts/ibkr_collect_environment_evidence.py`

模块：`scripts.ibkr_collect_environment_evidence`

#### `scripts.ibkr_collect_environment_evidence.collect_environment_evidence`

- 位置：`scripts/ibkr_collect_environment_evidence.py:28-78`
- 类型：`module_function`
- 签名：`def collect_environment_evidence(*, config_path: Path = DEFAULT_CONFIG_PATH, output_dir: Path = DEFAULT_OUTPUT_DIR, dry_run: bool = False, label: str | None = None, timeout_seconds: float = 2.0) -> Path`
- 作用：Write a JSON evidence file and return its path.
- 直接原始调用：`_collect_network_evidence`, `_evidence_filename`, `_read_config`, `_summarize_config`, `_validate_ibkr_config`, `datetime.now`, `evidence_path.write_text`, `generated_at.isoformat`, `json.dumps`, `output_dir.mkdir`, `str`
- 已解析到仓库内部的调用：`scripts.ibkr_collect_environment_evidence._collect_network_evidence`, `scripts.ibkr_collect_environment_evidence._evidence_filename`, `scripts.ibkr_collect_environment_evidence._read_config`, `scripts.ibkr_collect_environment_evidence._summarize_config`, `scripts.ibkr_collect_environment_evidence._validate_ibkr_config`
- 被以下仓库内部符号调用：`scripts.ibkr_collect_environment_evidence.main`

#### `scripts.ibkr_collect_environment_evidence.main`

- 位置：`scripts/ibkr_collect_environment_evidence.py:81-119`
- 类型：`module_function`
- 签名：`def main() -> None`
- 作用：未写 docstring；静态推断为 `main` 函数，具体语义以实现为准。
- 直接原始调用：`parser.add_argument` x5, `argparse.ArgumentParser`, `collect_environment_evidence`, `parser.parse_args`, `print`
- 已解析到仓库内部的调用：`scripts.ibkr_collect_environment_evidence.collect_environment_evidence`
- 被以下仓库内部符号调用：无静态解析记录

#### `scripts.ibkr_collect_environment_evidence._read_config`

- 位置：`scripts/ibkr_collect_environment_evidence.py:122-127`
- 类型：`module_function`
- 签名：`def _read_config(config_path: Path) -> JsonObject`
- 作用：未写 docstring；静态推断为 `read config` 函数，具体语义以实现为准。
- 直接原始调用：`ValueError`, `config_path.open`, `isinstance`, `yaml.safe_load`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`scripts.ibkr_collect_environment_evidence.collect_environment_evidence`

#### `scripts.ibkr_collect_environment_evidence._summarize_config`

- 位置：`scripts/ibkr_collect_environment_evidence.py:130-164`
- 类型：`module_function`
- 签名：`def _summarize_config(config_payload: JsonObject) -> JsonObject`
- 作用：未写 docstring；静态推断为 `summarize config` 函数，具体语义以实现为准。
- 直接原始调用：`_mapping` x5, `config_payload.get` x5, `market_data.get` x4, `order_connection.get` x4, `connections.get` x2, `order_execution.get` x2, `secrets.get` x2, `str` x2, `_env_ref_status`, `bool`
- 已解析到仓库内部的调用：`scripts.ibkr_collect_environment_evidence._env_ref_status`, `scripts.ibkr_collect_environment_evidence._mapping`
- 被以下仓库内部符号调用：`scripts.ibkr_collect_environment_evidence.collect_environment_evidence`

#### `scripts.ibkr_collect_environment_evidence._validate_ibkr_config`

- 位置：`scripts/ibkr_collect_environment_evidence.py:167-208`
- 类型：`module_function`
- 签名：`def _validate_ibkr_config(config_payload: JsonObject) -> list`
- 作用：未写 docstring；静态推断为 `validate ibkr config` 函数，具体语义以实现为准。
- 直接原始调用：`errors.append` x10, `config_payload.get` x6, `_mapping` x5, `str` x4, `_validate_connection` x2, `connections.get` x2, `order_execution.get` x2, `secrets.get` x2, `account_id.strip`, `account_id.upper`, `account_id.upper().startswith`, `credential_env.strip`, `credential_env.upper`, `market_data.get`, `order_connection.get`, `risk_profile.lower`, `risk_profile.strip`, `username_env.strip`, `username_env.upper`
- 已解析到仓库内部的调用：`scripts.ibkr_collect_environment_evidence._mapping`, `scripts.ibkr_collect_environment_evidence._validate_connection`
- 被以下仓库内部符号调用：`scripts.ibkr_collect_environment_evidence.collect_environment_evidence`

#### `scripts.ibkr_collect_environment_evidence._validate_connection`

- 位置：`scripts/ibkr_collect_environment_evidence.py:211-221`
- 类型：`module_function`
- 签名：`def _validate_connection(name: str, payload: JsonObject, errors: list) -> None`
- 作用：未写 docstring；静态推断为 `validate connection` 函数，具体语义以实现为准。
- 直接原始调用：`errors.append` x3, `payload.get` x3, `isinstance` x2, `host.strip`, `str`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`scripts.ibkr_collect_environment_evidence._validate_ibkr_config`

#### `scripts.ibkr_collect_environment_evidence._collect_network_evidence`

- 位置：`scripts/ibkr_collect_environment_evidence.py:224-246`
- 类型：`module_function`
- 签名：`def _collect_network_evidence(config_payload: JsonObject, *, dry_run: bool, timeout_seconds: float) -> JsonObject`
- 作用：未写 docstring；静态推断为 `collect network evidence` 函数，具体语义以实现为准。
- 直接原始调用：`_mapping` x3, `_tcp_probe` x2, `connections.get` x2, `config_payload.get`
- 已解析到仓库内部的调用：`scripts.ibkr_collect_environment_evidence._mapping`, `scripts.ibkr_collect_environment_evidence._tcp_probe`
- 被以下仓库内部符号调用：`scripts.ibkr_collect_environment_evidence.collect_environment_evidence`

#### `scripts.ibkr_collect_environment_evidence._tcp_probe`

- 位置：`scripts/ibkr_collect_environment_evidence.py:249-268`
- 类型：`module_function`
- 签名：`def _tcp_probe(connection: JsonObject, timeout_seconds: float) -> JsonObject`
- 作用：未写 docstring；静态推断为 `tcp probe` 函数，具体语义以实现为准。
- 直接原始调用：`connection.get` x2, `isinstance`, `socket.create_connection`, `str`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`scripts.ibkr_collect_environment_evidence._collect_network_evidence`

#### `scripts.ibkr_collect_environment_evidence._env_ref_status`

- 位置：`scripts/ibkr_collect_environment_evidence.py:271-275`
- 类型：`module_function`
- 签名：`def _env_ref_status(env_name: str) -> JsonObject`
- 作用：未写 docstring；静态推断为 `env ref status` 函数，具体语义以实现为准。
- 直接原始调用：`bool`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`scripts.ibkr_collect_environment_evidence._summarize_config`

#### `scripts.ibkr_collect_environment_evidence._mapping`

- 位置：`scripts/ibkr_collect_environment_evidence.py:278-281`
- 类型：`module_function`
- 签名：`def _mapping(value: Any) -> JsonObject`
- 作用：未写 docstring；静态推断为 `mapping` 函数，具体语义以实现为准。
- 直接原始调用：`isinstance`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`scripts.ibkr_collect_environment_evidence._collect_network_evidence`, `scripts.ibkr_collect_environment_evidence._summarize_config`, `scripts.ibkr_collect_environment_evidence._validate_ibkr_config`

#### `scripts.ibkr_collect_environment_evidence._evidence_filename`

- 位置：`scripts/ibkr_collect_environment_evidence.py:284-287`
- 类型：`module_function`
- 签名：`def _evidence_filename(generated_at: datetime, label: str | None) -> str`
- 作用：未写 docstring；静态推断为 `evidence filename` 函数，具体语义以实现为准。
- 直接原始调用：`_safe_label`, `generated_at.strftime`
- 已解析到仓库内部的调用：`scripts.ibkr_collect_environment_evidence._safe_label`
- 被以下仓库内部符号调用：`scripts.ibkr_collect_environment_evidence.collect_environment_evidence`

#### `scripts.ibkr_collect_environment_evidence._safe_label`

- 位置：`scripts/ibkr_collect_environment_evidence.py:290-294`
- 类型：`module_function`
- 签名：`def _safe_label(label: str | None) -> str`
- 作用：未写 docstring；静态推断为 `safe label` 函数，具体语义以实现为准。
- 直接原始调用：`label.strip`, `re.sub`, `re.sub().strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`scripts.ibkr_collect_environment_evidence._evidence_filename`

### `scripts/ibkr_paper_order_lifecycle_drill.py`

模块：`scripts.ibkr_paper_order_lifecycle_drill`

#### `scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill`

- 位置：`scripts/ibkr_paper_order_lifecycle_drill.py:35-142`
- 类型：`module_function`
- 签名：`def run_paper_order_lifecycle_drill(*, config_path: Path = DEFAULT_CONFIG_PATH, output_dir: Path = DEFAULT_OUTPUT_DIR, label: str | None = None, instrument_id: str = 'EQUITY.US.NASDAQ.AAPL', broker_symbol: str = 'AAPL', side: str = 'buy', quantity: Decimal = Decimal(), limit_price: Decimal = Decimal()) -> Path`
- 作用：Run a paper-only limit-order lifecycle drill and write JSON evidence.
- 直接原始调用：`str` x3, `Decimal` x2, `ValueError` x2, `_execution_report_evidence` x2, `manager.process_report` x2, `normalize_broker_execution_report` x2, `AccountId`, `BrokerId`, `BrokerOrderRequest`, `CancelIntent`, `FakeBrokerAdapter`, `InstrumentId`, `OrderId`, `OrderIntent`, `OrderManager`, `OrderSide`, `RiskDecision.approve`, `StrategyId`, `_account_id`, `_evidence_filename`, `_read_config`, `_summarize_config`, `_validate_paper_only_ibkr_config`, `broker.cancel_order`, `broker.submit_order`, `datetime.now`, `evidence_path.write_text`, `generated_at.isoformat`, `generated_at.strftime`, `json.dumps`, `manager.create_order`, `manager.mark_sent`, `manager.request_cancel`, `output_dir.mkdir`
- 已解析到仓库内部的调用：`qts.core.ids.AccountId`, `qts.core.ids.BrokerId`, `qts.core.ids.InstrumentId`, `qts.core.ids.OrderId`, `qts.core.ids.StrategyId`, `qts.execution.broker.BrokerOrderRequest`, `qts.execution.broker.FakeBrokerAdapter`, `qts.execution.broker.normalize_broker_execution_report`, `qts.execution.order_manager.CancelIntent`, `qts.execution.order_manager.OrderIntent`, `qts.execution.order_manager.OrderManager`, `qts.execution.order_manager.OrderSide`, `scripts.ibkr_paper_order_lifecycle_drill._account_id`, `scripts.ibkr_paper_order_lifecycle_drill._evidence_filename`, `scripts.ibkr_paper_order_lifecycle_drill._execution_report_evidence`, `scripts.ibkr_paper_order_lifecycle_drill._read_config`, `scripts.ibkr_paper_order_lifecycle_drill._summarize_config`, `scripts.ibkr_paper_order_lifecycle_drill._validate_paper_only_ibkr_config`
- 被以下仓库内部符号调用：`scripts.ibkr_paper_order_lifecycle_drill.main`

#### `scripts.ibkr_paper_order_lifecycle_drill.main`

- 位置：`scripts/ibkr_paper_order_lifecycle_drill.py:145-185`
- 类型：`module_function`
- 签名：`def main() -> None`
- 作用：未写 docstring；静态推断为 `main` 函数，具体语义以实现为准。
- 直接原始调用：`parser.add_argument` x8, `Decimal` x2, `argparse.ArgumentParser`, `parser.parse_args`, `print`, `run_paper_order_lifecycle_drill`
- 已解析到仓库内部的调用：`scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill`
- 被以下仓库内部符号调用：无静态解析记录

#### `scripts.ibkr_paper_order_lifecycle_drill._read_config`

- 位置：`scripts/ibkr_paper_order_lifecycle_drill.py:188-193`
- 类型：`module_function`
- 签名：`def _read_config(config_path: Path) -> JsonObject`
- 作用：未写 docstring；静态推断为 `read config` 函数，具体语义以实现为准。
- 直接原始调用：`ValueError`, `config_path.open`, `isinstance`, `yaml.safe_load`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill`

#### `scripts.ibkr_paper_order_lifecycle_drill._validate_paper_only_ibkr_config`

- 位置：`scripts/ibkr_paper_order_lifecycle_drill.py:196-212`
- 类型：`module_function`
- 签名：`def _validate_paper_only_ibkr_config(config_payload: JsonObject) -> None`
- 作用：未写 docstring；静态推断为 `validate paper only ibkr config` 函数，具体语义以实现为准。
- 直接原始调用：`errors.append` x4, `_mapping` x3, `config_payload.get` x3, `connections.get` x2, `'; '.join`, `ValueError`, `_account_id`, `_account_id().upper`, `_account_id().upper().startswith`, `market_data.get`, `order_execution.get`
- 已解析到仓库内部的调用：`scripts.ibkr_paper_order_lifecycle_drill._account_id`, `scripts.ibkr_paper_order_lifecycle_drill._mapping`
- 被以下仓库内部符号调用：`scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill`

#### `scripts.ibkr_paper_order_lifecycle_drill._summarize_config`

- 位置：`scripts/ibkr_paper_order_lifecycle_drill.py:215-228`
- 类型：`module_function`
- 签名：`def _summarize_config(config_payload: JsonObject) -> JsonObject`
- 作用：未写 docstring；静态推断为 `summarize config` 函数，具体语义以实现为准。
- 直接原始调用：`order_connection.get` x4, `config_payload.get` x3, `_mapping` x2, `_account_id`, `connections.get`
- 已解析到仓库内部的调用：`scripts.ibkr_paper_order_lifecycle_drill._account_id`, `scripts.ibkr_paper_order_lifecycle_drill._mapping`
- 被以下仓库内部符号调用：`scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill`

#### `scripts.ibkr_paper_order_lifecycle_drill._execution_report_evidence`

- 位置：`scripts/ibkr_paper_order_lifecycle_drill.py:231-243`
- 类型：`module_function`
- 签名：`def _execution_report_evidence(report: object) -> JsonObject`
- 作用：未写 docstring；静态推断为 `execution report evidence` 函数，具体语义以实现为准。
- 直接原始调用：`str` x2, `TypeError`, `isinstance`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill`

#### `scripts.ibkr_paper_order_lifecycle_drill._account_id`

- 位置：`scripts/ibkr_paper_order_lifecycle_drill.py:246-247`
- 类型：`module_function`
- 签名：`def _account_id(config_payload: JsonObject) -> str`
- 作用：未写 docstring；静态推断为 `account id` 函数，具体语义以实现为准。
- 直接原始调用：`_mapping`, `_mapping().get`, `config_payload.get`, `str`
- 已解析到仓库内部的调用：`scripts.ibkr_paper_order_lifecycle_drill._mapping`
- 被以下仓库内部符号调用：`scripts.ibkr_paper_order_lifecycle_drill._summarize_config`, `scripts.ibkr_paper_order_lifecycle_drill._validate_paper_only_ibkr_config`, `scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill`

#### `scripts.ibkr_paper_order_lifecycle_drill._mapping`

- 位置：`scripts/ibkr_paper_order_lifecycle_drill.py:250-253`
- 类型：`module_function`
- 签名：`def _mapping(value: Any) -> JsonObject`
- 作用：未写 docstring；静态推断为 `mapping` 函数，具体语义以实现为准。
- 直接原始调用：`isinstance`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`scripts.ibkr_paper_order_lifecycle_drill._account_id`, `scripts.ibkr_paper_order_lifecycle_drill._summarize_config`, `scripts.ibkr_paper_order_lifecycle_drill._validate_paper_only_ibkr_config`

#### `scripts.ibkr_paper_order_lifecycle_drill._evidence_filename`

- 位置：`scripts/ibkr_paper_order_lifecycle_drill.py:256-259`
- 类型：`module_function`
- 签名：`def _evidence_filename(generated_at: datetime, label: str | None) -> str`
- 作用：未写 docstring；静态推断为 `evidence filename` 函数，具体语义以实现为准。
- 直接原始调用：`_safe_label`, `generated_at.strftime`
- 已解析到仓库内部的调用：`scripts.ibkr_paper_order_lifecycle_drill._safe_label`
- 被以下仓库内部符号调用：`scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill`

#### `scripts.ibkr_paper_order_lifecycle_drill._safe_label`

- 位置：`scripts/ibkr_paper_order_lifecycle_drill.py:262-266`
- 类型：`module_function`
- 签名：`def _safe_label(label: str | None) -> str`
- 作用：未写 docstring；静态推断为 `safe label` 函数，具体语义以实现为准。
- 直接原始调用：`label.strip`, `re.sub`, `re.sub().strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`scripts.ibkr_paper_order_lifecycle_drill._evidence_filename`

### `scripts/run_api.py`

模块：`scripts.run_api`

无类或函数定义。

### `scripts/run_backtest.py`

模块：`scripts.run_backtest`

#### `scripts.run_backtest.main`

- 位置：`scripts/run_backtest.py:14-40`
- 类型：`module_function`
- 签名：`def main(argv: Sequence[str] | None = None) -> int`
- 作用：未写 docstring；静态推断为 `main` 函数，具体语义以实现为准。
- 直接原始调用：`print` x11, `parser.add_argument` x2, `time.perf_counter` x2, `Path`, `argparse.ArgumentParser`, `json.dumps`, `json.loads`, `parser.parse_args`, `run.summary_path.read_text`, `run.summary_path.write_text`, `run_backtest`
- 已解析到仓库内部的调用：`qts.backtest.runner.run_backtest`
- 被以下仓库内部符号调用：无静态解析记录

### `scripts/run_load.py`

模块：`scripts.run_load`

#### `scripts.run_load.main`

- 位置：`scripts/run_load.py:13-25`
- 类型：`module_function`
- 签名：`def main() -> None`
- 作用：未写 docstring；静态推断为 `main` 函数，具体语义以实现为准。
- 直接原始调用：`Decimal` x2, `InstrumentId`, `SyntheticMarketDataConfig`, `datetime`, `generate_bars`, `len`, `print`
- 已解析到仓库内部的调用：`qts.core.ids.InstrumentId`, `qts.load.synthetic_market_data.SyntheticMarketDataConfig`, `qts.load.synthetic_market_data.generate_bars`
- 被以下仓库内部符号调用：无静态解析记录

### `scripts/run_paper.py`

模块：`scripts.run_paper`

#### `scripts.run_paper.main`

- 位置：`scripts/run_paper.py:8-16`
- 类型：`module_function`
- 签名：`def main() -> None`
- 作用：未写 docstring；静态推断为 `main` 函数，具体语义以实现为准。
- 直接原始调用：`Decimal`, `PaperRuntimeConfig`, `print`, `start_paper`
- 已解析到仓库内部的调用：`qts.application.commands.start_paper.PaperRuntimeConfig`, `qts.application.commands.start_paper.start_paper`
- 被以下仓库内部符号调用：无静态解析记录

### `scripts/run_paper_ibkr.py`

模块：`scripts.run_paper_ibkr`

无类或函数定义。

### `scripts/run_worker.py`

模块：`scripts.run_worker`

无类或函数定义。

### `scripts/validate_historical.py`

模块：`scripts.validate_historical`

#### `scripts.validate_historical.main`

- 位置：`scripts/validate_historical.py:15-65`
- 类型：`module_function`
- 签名：`def main(argv: Sequence[str] | None = None) -> int`
- 作用：未写 docstring；静态推断为 `main` 函数，具体语义以实现为准。
- 直接原始调用：`parser.add_argument` x5, `str` x3, `Path` x2, `HistoricalCatalog.from_legacy_root`, `argparse.ArgumentParser`, `args.output_dir.mkdir`, `bool`, `catalog.datasets.items`, `datetime.now`, `datetime.now().isoformat`, `json.dumps`, `list`, `output_path.write_text`, `parser.parse_args`, `print`, `sample.stats.as_dict`, `tuple`, `validate_historical_sample`
- 已解析到仓库内部的调用：`qts.data.historical.catalog.HistoricalCatalog.from_legacy_root`, `qts.data.historical.csv_dataset.validate_historical_sample`
- 被以下仓库内部符号调用：无静态解析记录

### `scripts/verify_guardrails.py`

模块：`scripts.verify_guardrails`

#### `scripts.verify_guardrails.GuardrailViolation`

- 位置：`scripts/verify_guardrails.py:104-113`
- 类型：`class`
- 签名：`class GuardrailViolation`
- 装饰器：`dataclass()`
- 作用：One architecture or domain-boundary guardrail violation.
- 直接原始调用：`dataclass`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`scripts.verify_guardrails._check_backtest_engine_cohesion`, `scripts.verify_guardrails._check_backtest_input_cohesion`, `scripts.verify_guardrails._check_backtest_runner_cohesion`, `scripts.verify_guardrails._check_forbidden_tokens`, `scripts.verify_guardrails._check_import`, `scripts.verify_guardrails._check_oop_helper_ownership`, `scripts.verify_guardrails._check_oop_public_factory_functions`, `scripts.verify_guardrails._check_shared_capability_placement`, `scripts.verify_guardrails._check_test_support_code`

#### `scripts.verify_guardrails.GuardrailViolation.format`

- 位置：`scripts/verify_guardrails.py:112-113`
- 类型：`method`
- 签名：`def format(self) -> str`
- 所属：`scripts.verify_guardrails.GuardrailViolation`
- 作用：未写 docstring；静态推断为格式化输出表示（名称：format）。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无静态解析记录

#### `scripts.verify_guardrails.run_guardrails`

- 位置：`scripts/verify_guardrails.py:116-127`
- 类型：`module_function`
- 签名：`def run_guardrails(repo_root: Path) -> list`
- 作用：Return all guardrail violations under the repository root.
- 直接原始调用：`sorted` x2, `_check_python_file`, `source_root.exists`, `source_root.rglob`, `violations.extend`
- 已解析到仓库内部的调用：`scripts.verify_guardrails._check_python_file`
- 被以下仓库内部符号调用：`scripts.verify_guardrails.main`

#### `scripts.verify_guardrails._check_python_file`

- 位置：`scripts/verify_guardrails.py:130-154`
- 类型：`module_function`
- 签名：`def _check_python_file(repo_root: Path, path: Path) -> list`
- 作用：未写 docstring；静态推断为 `check python file` 函数，具体语义以实现为准。
- 直接原始调用：`violations.extend` x10, `_has_allowed_prefix` x2, `path.relative_to` x2, `_check_backtest_engine_cohesion`, `_check_backtest_input_cohesion`, `_check_backtest_runner_cohesion`, `_check_broker_specific_code`, `_check_import`, `_check_oop_helper_ownership`, `_check_oop_public_factory_functions`, `_check_product_specific_code`, `_check_shared_capability_placement`, `_check_test_support_code`, `_iter_imports`, `ast.parse`, `path.read_text`, `str`
- 已解析到仓库内部的调用：`scripts.verify_guardrails._check_backtest_engine_cohesion`, `scripts.verify_guardrails._check_backtest_input_cohesion`, `scripts.verify_guardrails._check_backtest_runner_cohesion`, `scripts.verify_guardrails._check_broker_specific_code`, `scripts.verify_guardrails._check_import`, `scripts.verify_guardrails._check_oop_helper_ownership`, `scripts.verify_guardrails._check_oop_public_factory_functions`, `scripts.verify_guardrails._check_product_specific_code`, `scripts.verify_guardrails._check_shared_capability_placement`, `scripts.verify_guardrails._check_test_support_code`, `scripts.verify_guardrails._has_allowed_prefix`, `scripts.verify_guardrails._iter_imports`
- 被以下仓库内部符号调用：`scripts.verify_guardrails.run_guardrails`

#### `scripts.verify_guardrails._check_import`

- 位置：`scripts/verify_guardrails.py:157-189`
- 类型：`module_function`
- 签名：`def _check_import(relative_path: Path, qts_relative_path: Path, imported_module: str, line: int) -> list`
- 作用：未写 docstring；静态推断为 `check import` 函数，具体语义以实现为准。
- 直接原始调用：`GuardrailViolation` x2, `str` x2, `_is_forbidden_adapter_dependency`, `_is_forbidden_dependency`, `imported_module.split`, `imported_module.startswith`, `len`
- 已解析到仓库内部的调用：`scripts.verify_guardrails.GuardrailViolation`, `scripts.verify_guardrails._is_forbidden_adapter_dependency`, `scripts.verify_guardrails._is_forbidden_dependency`
- 被以下仓库内部符号调用：`scripts.verify_guardrails._check_python_file`

#### `scripts.verify_guardrails._is_forbidden_dependency`

- 位置：`scripts/verify_guardrails.py:192-217`
- 类型：`module_function`
- 签名：`def _is_forbidden_dependency(source_layer: str, imported_module: str, imported_layer: str) -> bool`
- 作用：未写 docstring；静态推断为 `is forbidden dependency` 函数，具体语义以实现为准。
- 直接原始调用：`imported_module.startswith` x2
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`scripts.verify_guardrails._check_import`

#### `scripts.verify_guardrails._is_forbidden_adapter_dependency`

- 位置：`scripts/verify_guardrails.py:220-228`
- 类型：`module_function`
- 签名：`def _is_forbidden_adapter_dependency(qts_relative_path: Path, imported_module: str) -> bool`
- 作用：未写 docstring；静态推断为 `is forbidden adapter dependency` 函数，具体语义以实现为准。
- 直接原始调用：`imported_module.startswith` x2
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`scripts.verify_guardrails._check_import`

#### `scripts.verify_guardrails._check_product_specific_code`

- 位置：`scripts/verify_guardrails.py:231-241`
- 类型：`module_function`
- 签名：`def _check_product_specific_code(relative_path: Path, tree: ast.AST) -> list`
- 作用：未写 docstring；静态推断为 `check product specific code` 函数，具体语义以实现为准。
- 直接原始调用：`_check_forbidden_tokens`
- 已解析到仓库内部的调用：`scripts.verify_guardrails._check_forbidden_tokens`
- 被以下仓库内部符号调用：`scripts.verify_guardrails._check_python_file`

#### `scripts.verify_guardrails._check_broker_specific_code`

- 位置：`scripts/verify_guardrails.py:244-254`
- 类型：`module_function`
- 签名：`def _check_broker_specific_code(relative_path: Path, tree: ast.AST) -> list`
- 作用：未写 docstring；静态推断为 `check broker specific code` 函数，具体语义以实现为准。
- 直接原始调用：`_check_forbidden_tokens`
- 已解析到仓库内部的调用：`scripts.verify_guardrails._check_forbidden_tokens`
- 被以下仓库内部符号调用：`scripts.verify_guardrails._check_python_file`

#### `scripts.verify_guardrails._check_test_support_code`

- 位置：`scripts/verify_guardrails.py:257-285`
- 类型：`module_function`
- 签名：`def _check_test_support_code(relative_path: Path, qts_relative_path: Path, tree: ast.AST) -> list`
- 作用：未写 docstring；静态推断为 `check test support code` 函数，具体语义以实现为准。
- 直接原始调用：`GuardrailViolation` x2, `str` x2, `violations.append` x2, `_contains_forbidden_token`, `_identifier_tokens`, `_node_identifier_name`, `ast.walk`, `getattr`, `path_tokens.intersection`
- 已解析到仓库内部的调用：`scripts.verify_guardrails.GuardrailViolation`, `scripts.verify_guardrails._contains_forbidden_token`, `scripts.verify_guardrails._identifier_tokens`, `scripts.verify_guardrails._node_identifier_name`
- 被以下仓库内部符号调用：`scripts.verify_guardrails._check_python_file`

#### `scripts.verify_guardrails._check_shared_capability_placement`

- 位置：`scripts/verify_guardrails.py:288-307`
- 类型：`module_function`
- 签名：`def _check_shared_capability_placement(relative_path: Path, qts_relative_path: Path) -> list`
- 作用：未写 docstring；静态推断为 `check shared capability placement` 函数，具体语义以实现为准。
- 直接原始调用：`GuardrailViolation`, `_has_allowed_prefix`, `_identifier_tokens`, `path_tokens.intersection`, `str`
- 已解析到仓库内部的调用：`scripts.verify_guardrails.GuardrailViolation`, `scripts.verify_guardrails._has_allowed_prefix`, `scripts.verify_guardrails._identifier_tokens`
- 被以下仓库内部符号调用：`scripts.verify_guardrails._check_python_file`

#### `scripts.verify_guardrails._check_oop_public_factory_functions`

- 位置：`scripts/verify_guardrails.py:310-337`
- 类型：`module_function`
- 签名：`def _check_oop_public_factory_functions(relative_path: Path, qts_relative_path: Path, tree: ast.AST) -> list`
- 作用：未写 docstring；静态推断为 `check oop public factory functions` 函数，具体语义以实现为准。
- 直接原始调用：`node.name.startswith` x2, `GuardrailViolation`, `isinstance`, `qts_relative_path.as_posix`, `str`, `violations.append`
- 已解析到仓库内部的调用：`scripts.verify_guardrails.GuardrailViolation`
- 被以下仓库内部符号调用：`scripts.verify_guardrails._check_python_file`

#### `scripts.verify_guardrails._check_oop_helper_ownership`

- 位置：`scripts/verify_guardrails.py:340-403`
- 类型：`module_function`
- 签名：`def _check_oop_helper_ownership(relative_path: Path, qts_relative_path: Path, tree: ast.AST) -> list`
- 作用：未写 docstring；静态推断为 `check oop helper ownership` 函数，具体语义以实现为准。
- 直接原始调用：`node.name.startswith` x4, `isinstance` x3, `len` x3, `GuardrailViolation` x2, `str` x2, `_node_references_name`, `qts_relative_path.as_posix`, `violations.append`
- 已解析到仓库内部的调用：`scripts.verify_guardrails.GuardrailViolation`, `scripts.verify_guardrails._node_references_name`
- 被以下仓库内部符号调用：`scripts.verify_guardrails._check_python_file`

#### `scripts.verify_guardrails._check_backtest_runner_cohesion`

- 位置：`scripts/verify_guardrails.py:406-459`
- 类型：`module_function`
- 签名：`def _check_backtest_runner_cohesion(relative_path: Path, qts_relative_path: Path, tree: ast.AST) -> list`
- 作用：未写 docstring；静态推断为 `check backtest runner cohesion` 函数，具体语义以实现为准。
- 直接原始调用：`GuardrailViolation` x3, `str` x3, `violations.append` x3, `_iter_imported_names`, `_iter_imports`, `ast.walk`, `imported_module.startswith`, `isinstance`
- 已解析到仓库内部的调用：`scripts.verify_guardrails.GuardrailViolation`, `scripts.verify_guardrails._iter_imported_names`, `scripts.verify_guardrails._iter_imports`
- 被以下仓库内部符号调用：`scripts.verify_guardrails._check_python_file`

#### `scripts.verify_guardrails._check_backtest_input_cohesion`

- 位置：`scripts/verify_guardrails.py:462-515`
- 类型：`module_function`
- 签名：`def _check_backtest_input_cohesion(relative_path: Path, qts_relative_path: Path, tree: ast.AST) -> list`
- 作用：未写 docstring；静态推断为 `check backtest input cohesion` 函数，具体语义以实现为准。
- 直接原始调用：`GuardrailViolation` x3, `str` x3, `violations.append` x3, `_iter_imported_names`, `_iter_imports`, `ast.walk`, `isinstance`
- 已解析到仓库内部的调用：`scripts.verify_guardrails.GuardrailViolation`, `scripts.verify_guardrails._iter_imported_names`, `scripts.verify_guardrails._iter_imports`
- 被以下仓库内部符号调用：`scripts.verify_guardrails._check_python_file`

#### `scripts.verify_guardrails._check_backtest_engine_cohesion`

- 位置：`scripts/verify_guardrails.py:518-555`
- 类型：`module_function`
- 签名：`def _check_backtest_engine_cohesion(relative_path: Path, qts_relative_path: Path, tree: ast.AST) -> list`
- 作用：未写 docstring；静态推断为 `check backtest engine cohesion` 函数，具体语义以实现为准。
- 直接原始调用：`GuardrailViolation` x2, `str` x2, `violations.append` x2, `_iter_imports`, `ast.walk`, `imported_module.startswith`, `isinstance`
- 已解析到仓库内部的调用：`scripts.verify_guardrails.GuardrailViolation`, `scripts.verify_guardrails._iter_imports`
- 被以下仓库内部符号调用：`scripts.verify_guardrails._check_python_file`

#### `scripts.verify_guardrails._check_forbidden_tokens`

- 位置：`scripts/verify_guardrails.py:558-588`
- 类型：`module_function`
- 签名：`def _check_forbidden_tokens(relative_path: Path, tree: ast.AST, *, tokens: frozenset, code: str, description: str) -> list`
- 作用：未写 docstring；静态推断为 `check forbidden tokens` 函数，具体语义以实现为准。
- 直接原始调用：`GuardrailViolation` x2, `_contains_forbidden_token` x2, `getattr` x2, `isinstance` x2, `str` x2, `violations.append` x2, `_node_identifier_name`, `ast.walk`
- 已解析到仓库内部的调用：`scripts.verify_guardrails.GuardrailViolation`, `scripts.verify_guardrails._contains_forbidden_token`, `scripts.verify_guardrails._node_identifier_name`
- 被以下仓库内部符号调用：`scripts.verify_guardrails._check_broker_specific_code`, `scripts.verify_guardrails._check_product_specific_code`

#### `scripts.verify_guardrails._node_identifier_name`

- 位置：`scripts/verify_guardrails.py:591-598`
- 类型：`module_function`
- 签名：`def _node_identifier_name(node: ast.AST) -> str | None`
- 作用：未写 docstring；静态推断为 `node identifier name` 函数，具体语义以实现为准。
- 直接原始调用：`isinstance` x5
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`scripts.verify_guardrails._check_forbidden_tokens`, `scripts.verify_guardrails._check_test_support_code`

#### `scripts.verify_guardrails._contains_forbidden_token`

- 位置：`scripts/verify_guardrails.py:601-602`
- 类型：`module_function`
- 签名：`def _contains_forbidden_token(value: str, forbidden_tokens: frozenset) -> bool`
- 作用：未写 docstring；静态推断为 `contains forbidden token` 函数，具体语义以实现为准。
- 直接原始调用：`_identifier_tokens`, `any`
- 已解析到仓库内部的调用：`scripts.verify_guardrails._identifier_tokens`
- 被以下仓库内部符号调用：`scripts.verify_guardrails._check_forbidden_tokens`, `scripts.verify_guardrails._check_test_support_code`

#### `scripts.verify_guardrails._node_references_name`

- 位置：`scripts/verify_guardrails.py:605-609`
- 类型：`module_function`
- 签名：`def _node_references_name(node: ast.AST, name: str) -> bool`
- 作用：未写 docstring；静态推断为 `node references name` 函数，具体语义以实现为准。
- 直接原始调用：`isinstance` x2, `any`, `ast.walk`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`scripts.verify_guardrails._check_oop_helper_ownership`

#### `scripts.verify_guardrails._identifier_tokens`

- 位置：`scripts/verify_guardrails.py:612-621`
- 类型：`module_function`
- 签名：`def _identifier_tokens(value: str) -> set`
- 作用：未写 docstring；静态推断为 `identifier tokens` 函数，具体语义以实现为准。
- 直接原始调用：`item.upper`, `part.upper`, `re.findall`, `re.split`, `set`, `tokens.add`, `tokens.update`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`scripts.verify_guardrails._check_shared_capability_placement`, `scripts.verify_guardrails._check_test_support_code`, `scripts.verify_guardrails._contains_forbidden_token`

#### `scripts.verify_guardrails._iter_imports`

- 位置：`scripts/verify_guardrails.py:624-631`
- 类型：`module_function`
- 签名：`def _iter_imports(tree: ast.AST) -> list`
- 作用：未写 docstring；静态推断为 `iter imports` 函数，具体语义以实现为准。
- 直接原始调用：`isinstance` x2, `ast.walk`, `imports.append`, `imports.extend`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`scripts.verify_guardrails._check_backtest_engine_cohesion`, `scripts.verify_guardrails._check_backtest_input_cohesion`, `scripts.verify_guardrails._check_backtest_runner_cohesion`, `scripts.verify_guardrails._check_python_file`

#### `scripts.verify_guardrails._iter_imported_names`

- 位置：`scripts/verify_guardrails.py:634-639`
- 类型：`module_function`
- 签名：`def _iter_imported_names(tree: ast.AST) -> list`
- 作用：未写 docstring；静态推断为 `iter imported names` 函数，具体语义以实现为准。
- 直接原始调用：`ast.walk`, `imports.extend`, `isinstance`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`scripts.verify_guardrails._check_backtest_input_cohesion`, `scripts.verify_guardrails._check_backtest_runner_cohesion`

#### `scripts.verify_guardrails._has_allowed_prefix`

- 位置：`scripts/verify_guardrails.py:642-643`
- 类型：`module_function`
- 签名：`def _has_allowed_prefix(path: Path, prefixes: tuple) -> bool`
- 作用：未写 docstring；静态推断为 `has allowed prefix` 函数，具体语义以实现为准。
- 直接原始调用：`any`, `len`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`scripts.verify_guardrails._check_python_file`, `scripts.verify_guardrails._check_shared_capability_placement`

#### `scripts.verify_guardrails.main`

- 位置：`scripts/verify_guardrails.py:646-655`
- 类型：`module_function`
- 签名：`def main() -> int`
- 作用：未写 docstring；静态推断为 `main` 函数，具体语义以实现为准。
- 直接原始调用：`print` x3, `Path.cwd`, `run_guardrails`, `violation.format`
- 已解析到仓库内部的调用：`scripts.verify_guardrails.run_guardrails`
- 被以下仓库内部符号调用：无静态解析记录

## 内部调用边

| 调用方 | 被调用方 |
|---|---|
| `examples.strategies.gc_si_momentum.GcSiMomentumStrategy.initialize` | `examples.strategies.gc_si_momentum._asset_for_symbol` |
| `examples.strategies.gc_si_momentum.GcSiMomentumStrategy.on_bar` | `examples.strategies.gc_si_momentum._average` |
| `qts.api.routes.accounts.account_snapshot` | `qts.api.schemas.common.AccountSnapshotSchema` |
| `qts.api.routes.backtests.submit_backtest` | `qts.application.dto.backtest.BacktestRequestDTO` |
| `qts.api.routes.backtests.submit_backtest` | `qts.application.services.backtest.BacktestService` |
| `qts.api.routes.health.health` | `qts.application.services.health.HealthService` |
| `qts.api.routes.operations.activate_kill_switch` | `qts.api.routes.operations.KillSwitchResponse` |
| `qts.api.routes.operations.activate_kill_switch` | `qts.api.routes.operations._require_operator` |
| `qts.api.routes.operations.activate_kill_switch` | `qts.application.dto.operations.KillSwitchCommandDTO` |
| `qts.api.routes.operations.pause_runtime` | `qts.api.routes.operations._require_operator` |
| `qts.api.routes.operations.pause_runtime.<locals>.command` | `qts.api.routes.operations.RuntimeCommandResponse` |
| `qts.api.routes.operations.resume_runtime` | `qts.api.routes.operations._require_operator` |
| `qts.api.routes.operations.resume_runtime.<locals>.command` | `qts.api.routes.operations.RuntimeCommandResponse` |
| `qts.api.routes.orders.order_status` | `qts.api.schemas.common.OrderStatusSchema` |
| `qts.api.routes.strategies.list_strategies` | `qts.api.schemas.common.StrategyStatusSchema` |
| `qts.api.routes.strategies.start_strategy` | `qts.api.schemas.common.StrategyStatusSchema` |
| `qts.api.routes.strategies.stop_strategy` | `qts.api.schemas.common.StrategyStatusSchema` |
| `qts.api.websocket.fill_adapter.order_fill_to_stream_dto` | `qts.api.websocket.dtos.StreamEventDTO` |
| `qts.api.websocket.manager.WebSocketConnectionManager.broadcast` | `qts.api.websocket.manager.WebSocketConnectionManager.disconnect` |
| `qts.application.commands.start_paper.start_paper` | `qts.application.commands.start_paper.PaperRuntime` |
| `qts.application.services.backtest.BacktestService.__init__` | `qts.api.websocket.manager.WebSocketConnectionManager.count` |
| `qts.application.services.backtest.BacktestService.submit` | `qts.application.dto.backtest.BacktestRunDTO` |
| `qts.application.services.health.HealthService.status` | `qts.application.dto.health.HealthStatusDTO` |
| `qts.application.services.operations.OperationsService.__init__` | `qts.risk.kill_switch.KillSwitchRegistry` |
| `qts.application.services.operations.OperationsService._scope_from_command` | `qts.risk.kill_switch.KillSwitchScope` |
| `qts.application.services.operations.OperationsService._scope_from_command` | `qts.risk.kill_switch.KillSwitchScope.global_scope` |
| `qts.application.services.operations.OperationsService._scope_from_command` | `qts.risk.kill_switch.KillSwitchScopeType` |
| `qts.application.services.operations.OperationsService.activate_kill_switch` | `qts.application.dto.operations.KillSwitchStateDTO` |
| `qts.application.services.operations.OperationsService.activate_kill_switch` | `qts.application.services.operations.OperationsService._scope_from_command` |
| `qts.application.services.operations.OperationsService.pause_runtime` | `qts.application.dto.operations.RuntimeStateDTO` |
| `qts.application.services.operations.OperationsService.resume_runtime` | `qts.application.dto.operations.RuntimeStateDTO` |
| `qts.application.services.strategy_service.StrategyLifecycleService.start` | `qts.application.services.strategy_service.StrategyLifecycleService._require_enabled` |
| `qts.application.services.strategy_service.StrategyLifecycleService.status` | `qts.application.services.strategy_service.StrategyLifecycleService._require_enabled` |
| `qts.application.services.strategy_service.StrategyLifecycleService.stop` | `qts.application.services.strategy_service.StrategyLifecycleService._require_enabled` |
| `qts.backtest.config.BacktestRunConfig` | `qts.backtest.config.RiskConfig` |
| `qts.backtest.config.BacktestRunConfig.__post_init__` | `qts.backtest.config.BacktestMarketDataReference` |
| `qts.backtest.config.BacktestRunConfig.__post_init__` | `qts.backtest.config.BacktestRunConfig._normalize_symbol` |
| `qts.backtest.config.BacktestRunConfig.__post_init__` | `qts.backtest.config.BacktestStrategyConfig` |
| `qts.backtest.config.BacktestRunConfig.__post_init__` | `qts.core.ids.InstrumentId` |
| `qts.backtest.config.BacktestRunConfig._parse_historical_data_reference` | `qts.backtest.config.BacktestMarketDataReference` |
| `qts.backtest.config.BacktestRunConfig._parse_market_data_reference` | `qts.backtest.config.BacktestMarketDataReference` |
| `qts.backtest.config.BacktestRunConfig.config_hash` | `qts.backtest.config.BacktestRunConfig._stable_hash` |
| `qts.backtest.config.BacktestRunConfig.config_hash` | `qts.backtest.config.BacktestRunConfig.to_payload` |
| `qts.backtest.config.BacktestRunConfig.from_yaml` | `qts.backtest.config.BacktestRunConfig._parse_datetime` |
| `qts.backtest.config.BacktestRunConfig.from_yaml` | `qts.backtest.config.BacktestRunConfig._parse_historical_data_reference` |
| `qts.backtest.config.BacktestRunConfig.from_yaml` | `qts.backtest.config.BacktestRunConfig._parse_market_data_reference` |
| `qts.backtest.config.BacktestRunConfig.from_yaml` | `qts.backtest.config.CostModelConfig` |
| `qts.backtest.config.BacktestRunConfig.from_yaml` | `qts.backtest.config.RiskConfig` |
| `qts.backtest.config.BacktestRunConfig.from_yaml` | `qts.backtest.config.RollPolicyConfig` |
| `qts.backtest.config.BacktestRunConfig.from_yaml` | `qts.core.ids.InstrumentId` |
| `qts.backtest.config.BacktestStrategyConfig.from_yaml` | `qts.backtest.config.BacktestStrategyConfig._parse_payload` |
| `qts.backtest.engine.BacktestEngine.__init__` | `qts.backtest.engine.BacktestCostModel` |
| `qts.backtest.engine.BacktestEngine.__init__` | `qts.risk.risk_engine.RiskEngine` |
| `qts.backtest.engine.BacktestEngine.__init__` | `qts.risk.rules.max_notional.MaxNotionalRule` |
| `qts.backtest.engine.BacktestEngine._equity_point` | `qts.backtest.engine.BacktestEngine._portfolio_view` |
| `qts.backtest.engine.BacktestEngine._equity_point` | `qts.backtest.report.EquityCurvePoint` |
| `qts.backtest.engine.BacktestEngine._instrument_registry_for` | `qts.backtest.engine.BacktestEngine._exchange_for` |
| `qts.backtest.engine.BacktestEngine._instrument_registry_for` | `qts.backtest.engine.BacktestEngine._multiplier_for` |
| `qts.backtest.engine.BacktestEngine._instrument_registry_for` | `qts.backtest.engine.BacktestEngine._symbol_for` |
| `qts.backtest.engine.BacktestEngine._instrument_registry_for` | `qts.domain.instruments.contract_spec.ContractSpec` |
| `qts.backtest.engine.BacktestEngine._instrument_registry_for` | `qts.domain.instruments.instrument.Instrument` |
| `qts.backtest.engine.BacktestEngine._instrument_registry_for` | `qts.registry.instrument_registry.InstrumentRegistry` |
| `qts.backtest.engine.BacktestEngine._ledger_rows` | `qts.backtest.report.TradeLedgerEntry` |
| `qts.backtest.engine.BacktestEngine._market_data_ref_for` | `qts.runtime.actor_ref.ActorRef` |
| `qts.backtest.engine.BacktestEngine._market_data_ref_for` | `qts.runtime.actors.market_data_actor.MarketDataActor` |
| `qts.backtest.engine.BacktestEngine._market_data_ref_for` | `qts.runtime.mailbox.Mailbox` |
| `qts.backtest.engine.BacktestEngine._portfolio_view` | `qts.backtest.engine.BacktestEngine._multiplier_for` |
| `qts.backtest.engine.BacktestEngine._portfolio_view` | `qts.strategy_sdk.portfolio_view.PortfolioPosition` |
| `qts.backtest.engine.BacktestEngine._portfolio_view` | `qts.strategy_sdk.portfolio_view.PortfolioView` |
| `qts.backtest.engine.BacktestEngine._process_intent` | `qts.backtest.engine.BacktestEngine._desired_quantity` |
| `qts.backtest.engine.BacktestEngine._process_intent` | `qts.backtest.engine.BacktestEngine._market_price_for_intent` |
| `qts.backtest.engine.BacktestEngine._process_intent` | `qts.backtest.engine.BacktestEngine._multiplier_for` |
| `qts.backtest.engine.BacktestEngine._process_intent` | `qts.backtest.engine.BacktestEngine._order_instrument_for_intent` |
| `qts.backtest.engine.BacktestEngine._process_intent` | `qts.backtest.engine.BacktestEngine._process_order_delta` |
| `qts.backtest.engine.BacktestEngine._process_intent` | `qts.backtest.engine.BacktestEngine._related_contracts_for` |
| `qts.backtest.engine.BacktestEngine._process_intent` | `qts.portfolio.position_book.Position` |
| `qts.backtest.engine.BacktestEngine._process_order_delta` | `qts.core.ids.OrderId` |
| `qts.backtest.engine.BacktestEngine._process_order_delta` | `qts.domain.risk.request.OrderRiskRequest` |
| `qts.backtest.engine.BacktestEngine._process_order_delta` | `qts.execution.order_manager.OrderIntent` |
| `qts.backtest.engine.BacktestEngine._process_order_delta` | `qts.runtime.actors.order_manager_actor.SubmitOrder` |
| `qts.backtest.engine.BacktestEngine._run_actor_loop` | `qts.backtest.engine.BacktestEngine._equity_point` |
| `qts.backtest.engine.BacktestEngine._run_actor_loop` | `qts.backtest.engine.BacktestEngine._history_limit_from_subscriptions` |
| `qts.backtest.engine.BacktestEngine._run_actor_loop` | `qts.backtest.engine.BacktestEngine._instrument_registry_for` |
| `qts.backtest.engine.BacktestEngine._run_actor_loop` | `qts.backtest.engine.BacktestEngine._market_data_ref_for` |
| `qts.backtest.engine.BacktestEngine._run_actor_loop` | `qts.backtest.engine.BacktestEngine._portfolio_view` |
| `qts.backtest.engine.BacktestEngine._run_actor_loop` | `qts.backtest.engine.BacktestEngine._process_intent` |
| `qts.backtest.engine.BacktestEngine._run_actor_loop` | `qts.backtest.engine.BacktestEngine._take_signal_batch` |
| `qts.backtest.engine.BacktestEngine._run_actor_loop` | `qts.backtest.engine.BacktestEngine._take_strategy_bar_result` |
| `qts.backtest.engine.BacktestEngine._run_actor_loop` | `qts.backtest.engine.BacktestEngine._take_strategy_finalized` |
| `qts.backtest.engine.BacktestEngine._run_actor_loop` | `qts.backtest.engine.BacktestEngine._update_rolling_prices` |
| `qts.backtest.engine.BacktestEngine._run_actor_loop` | `qts.backtest.engine._BacktestExecutionAdapter` |
| `qts.backtest.engine.BacktestEngine._run_actor_loop` | `qts.backtest.historical_data_portal.HistoricalDataPortal` |
| `qts.backtest.engine.BacktestEngine._run_actor_loop` | `qts.runtime.actor_ref.ActorRef` |
| `qts.backtest.engine.BacktestEngine._run_actor_loop` | `qts.runtime.actors.account_actor.AccountActor` |
| `qts.backtest.engine.BacktestEngine._run_actor_loop` | `qts.runtime.actors.execution_actor.ExecutionActor` |
| `qts.backtest.engine.BacktestEngine._run_actor_loop` | `qts.runtime.actors.market_data_actor.MarketDataEvent` |
| `qts.backtest.engine.BacktestEngine._run_actor_loop` | `qts.runtime.actors.order_manager_actor.OrderManagerActor` |
| `qts.backtest.engine.BacktestEngine._run_actor_loop` | `qts.runtime.actors.signal_aggregator_actor.SignalAggregatorActor` |
| `qts.backtest.engine.BacktestEngine._run_actor_loop` | `qts.runtime.actors.signal_aggregator_actor.StrategySignalEvent` |
| `qts.backtest.engine.BacktestEngine._run_actor_loop` | `qts.runtime.actors.strategy_actor.StrategyActor` |
| `qts.backtest.engine.BacktestEngine._run_actor_loop` | `qts.runtime.actors.strategy_actor.StrategyBarEvent` |
| `qts.backtest.engine.BacktestEngine._run_actor_loop` | `qts.runtime.actors.strategy_actor.StrategyFinalize` |
| `qts.backtest.engine.BacktestEngine._run_actor_loop` | `qts.runtime.mailbox.Mailbox` |
| `qts.backtest.engine.BacktestEngine._run_actor_loop` | `qts.strategy_sdk.context.StrategyContext` |
| `qts.backtest.engine.BacktestEngine.from_config` | `qts.backtest.engine.BacktestCostModel` |
| `qts.backtest.engine.BacktestEngine.from_config` | `qts.risk.risk_engine.RiskEngine` |
| `qts.backtest.engine.BacktestEngine.from_config` | `qts.risk.rules.max_notional.MaxNotionalRule` |
| `qts.backtest.engine.BacktestEngine.run_streaming` | `qts.backtest.engine.BacktestEngine._dataset_payload` |
| `qts.backtest.engine.BacktestEngine.run_streaming` | `qts.backtest.engine.BacktestEngine._run_actor_loop` |
| `qts.backtest.engine.BacktestEngine.run_streaming` | `qts.backtest.engine.BacktestEngine._stable_hash` |
| `qts.backtest.engine.BacktestEngine.run_streaming` | `qts.backtest.engine.BacktestEngine._zero_time` |
| `qts.backtest.engine.BacktestEngine.run_streaming` | `qts.backtest.engine.BacktestStreamResult` |
| `qts.backtest.engine.BacktestEngine.run_streaming` | `qts.backtest.report.EquityCurvePoint` |
| `qts.backtest.engine.BacktestEngine.run_streaming` | `qts.backtest.report.StreamingBacktestArtifactWriter` |
| `qts.backtest.engine.BacktestEngine.run_streaming` | `qts.core.ids.BacktestRunId` |
| `qts.backtest.engine._BacktestExecutionAdapter.execute_market_order` | `qts.execution.order_manager.ExecutionReport` |
| `qts.backtest.historical_data_portal.HistoricalDataPortal.data_view` | `qts.strategy_sdk.data_view.DataView` |
| `qts.backtest.historical_data_portal.HistoricalDataPortal.history` | `qts.backtest.historical_data_portal.HistoricalDataPortal.data_view` |
| `qts.backtest.inputs.BacktestInputBuilder._dataset_instrument_id` | `qts.core.ids.InstrumentId` |
| `qts.backtest.inputs.BacktestInputBuilder._dataset_metadata` | `qts.backtest.inputs.BacktestInputBuilder._dataset_instrument_id` |
| `qts.backtest.inputs.BacktestInputBuilder._dataset_metadata` | `qts.data.provenance.DatasetMetadata` |
| `qts.backtest.inputs.BacktestInputBuilder._instrument_for` | `qts.domain.instruments.contract_spec.ContractSpec` |
| `qts.backtest.inputs.BacktestInputBuilder._instrument_for` | `qts.domain.instruments.instrument.Instrument` |
| `qts.backtest.inputs.BacktestInputBuilder._instrument_registry_for` | `qts.backtest.inputs.BacktestInputBuilder._instrument_for` |
| `qts.backtest.inputs.BacktestInputBuilder._instrument_registry_for` | `qts.registry.instrument_registry.InstrumentRegistry` |
| `qts.backtest.inputs.BacktestInputBuilder._iter_root_bars` | `qts.backtest.inputs.BacktestInputBuilder._record_exchange_timezone` |
| `qts.backtest.inputs.BacktestInputBuilder._roll_registry` | `qts.registry.future_roll.FutureRollRegistry` |
| `qts.backtest.inputs.BacktestInputBuilder._stream_configured_bars` | `qts.backtest.inputs.BacktestInputBuilder._exchange_timezone_for` |
| `qts.backtest.inputs.BacktestInputBuilder._stream_configured_bars` | `qts.backtest.inputs.BacktestInputBuilder._iter_root_bars` |
| `qts.backtest.inputs.BacktestInputBuilder._stream_configured_bars` | `qts.backtest.inputs.BacktestInputBuilder._merge_ordered_bar_streams` |
| `qts.backtest.inputs.BacktestInputBuilder._stream_configured_bars` | `qts.data.historical.csv_dataset.iter_historical_bars` |
| `qts.backtest.inputs.BacktestInputBuilder._stream_configured_bars` | `qts.registry.future_roll.HighestVolumeFutureContractSelector` |
| `qts.backtest.inputs.BacktestInputBuilder.build` | `qts.backtest.inputs.BacktestInputBuilder._contract_multipliers_for` |
| `qts.backtest.inputs.BacktestInputBuilder.build` | `qts.backtest.inputs.BacktestInputBuilder._dataset_metadata` |
| `qts.backtest.inputs.BacktestInputBuilder.build` | `qts.backtest.inputs.BacktestInputBuilder._instrument_registry_for` |
| `qts.backtest.inputs.BacktestInputBuilder.build` | `qts.backtest.inputs.BacktestInputBuilder._roll_registry` |
| `qts.backtest.inputs.BacktestInputBuilder.build` | `qts.backtest.inputs.BacktestInputBuilder._stream_configured_bars` |
| `qts.backtest.inputs.BacktestInputBuilder.build` | `qts.backtest.inputs.BacktestInputBundle` |
| `qts.backtest.report.StreamingBacktestArtifactWriter.__init__` | `qts.backtest.report.StreamingEquityMetrics` |
| `qts.backtest.report.StreamingBacktestArtifactWriter.__init__` | `qts.backtest.report._NdjsonArtifact` |
| `qts.backtest.report.StreamingBacktestArtifactWriter.finalize` | `qts.backtest.report.StreamingBacktestArtifacts` |
| `qts.backtest.report.StreamingBacktestArtifactWriter.finalize` | `qts.backtest.report._stable_hash` |
| `qts.backtest.runner._catalog_load_config` | `qts.data.historical.catalog.HistoricalCatalogLoadConfig.from_historical_data_config` |
| `qts.backtest.runner._catalog_load_config` | `qts.data.historical.catalog.HistoricalCatalogLoadConfig.from_legacy_root` |
| `qts.backtest.runner.run_backtest` | `qts.backtest.config.BacktestRunConfig.from_yaml` |
| `qts.backtest.runner.run_backtest` | `qts.backtest.engine.BacktestEngine.from_config` |
| `qts.backtest.runner.run_backtest` | `qts.backtest.engine.BacktestEngine.run_streaming` |
| `qts.backtest.runner.run_backtest` | `qts.backtest.inputs.BacktestInputBuilder` |
| `qts.backtest.runner.run_backtest` | `qts.backtest.runner.BacktestRun` |
| `qts.backtest.runner.run_backtest` | `qts.backtest.runner._catalog_load_config` |
| `qts.backtest.runner.run_backtest` | `qts.backtest.runner._load_strategy` |
| `qts.backtest.runner.run_backtest` | `qts.backtest.runner._streaming_summary_payload` |
| `qts.backtest.runner.run_backtest` | `qts.data.historical.catalog.HistoricalCatalog.load` |
| `qts.config.ibkr.validate_ibkr_environment` | `qts.config.ibkr._contains_paper_reference` |
| `qts.core.time.TimeInterval.__post_init__` | `qts.core.time.require_aware_datetime` |
| `qts.core.time.TimeInterval.contains` | `qts.core.time.require_aware_datetime` |
| `qts.core.time.to_exchange_time` | `qts.core.time.require_aware_datetime` |
| `qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter.normalize_bar` | `qts.domain.market_data.bar.Bar` |
| `qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter.normalize_quote` | `qts.domain.market_data.bar.Quote` |
| `qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter.normalize_tick` | `qts.domain.market_data.bar.Tick` |
| `qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter.subscription_for` | `qts.data.adapters.ibkr_market_data.IbkrMarketDataSubscription` |
| `qts.data.bars.aggregator.BarAggregator._new_state_for` | `qts.core.time.TimeInterval` |
| `qts.data.bars.aggregator.BarAggregator._new_state_for` | `qts.data.bars.aggregator.AggregationState` |
| `qts.data.bars.aggregator.BarAggregator._new_state_for` | `qts.data.bars.alignment.clock_bucket_for` |
| `qts.data.bars.aggregator.BarAggregator.finish` | `qts.data.bars.aggregator.AggregationResult` |
| `qts.data.bars.aggregator.BarAggregator.finish` | `qts.data.bars.aggregator._aggregate_state` |
| `qts.data.bars.aggregator.BarAggregator.update` | `qts.data.bars.aggregator.AggregationResult` |
| `qts.data.bars.aggregator.BarAggregator.update` | `qts.data.bars.aggregator.AggregationState` |
| `qts.data.bars.aggregator.BarAggregator.update` | `qts.data.bars.aggregator.BarAggregator._new_state_for` |
| `qts.data.bars.aggregator.BarAggregator.update` | `qts.data.bars.aggregator._aggregate_state` |
| `qts.data.bars.aggregator.BarAggregator.update` | `qts.data.bars.aggregator._bar_inside_session` |
| `qts.data.bars.aggregator.BarAggregator.update` | `qts.data.bars.aggregator._same_stream_bucket` |
| `qts.data.bars.aggregator._aggregate_state` | `qts.data.bars.aggregator._aggregate_vwap` |
| `qts.data.bars.aggregator._aggregate_state` | `qts.data.bars.aggregator._last_open_interest` |
| `qts.data.bars.aggregator._aggregate_state` | `qts.data.bars.aggregator._sum_trade_count` |
| `qts.data.bars.aggregator._aggregate_state` | `qts.domain.market_data.bar.Bar` |
| `qts.data.bars.aggregator.aggregate_bars` | `qts.data.bars.aggregator.BarAggregator` |
| `qts.data.bars.alignment.clock_bucket_for` | `qts.core.time.TimeInterval` |
| `qts.data.bars.alignment.clock_bucket_for` | `qts.core.time.to_exchange_time` |
| `qts.data.bars.alignment.clock_bucket_for` | `qts.data.bars.alignment._duration_seconds` |
| `qts.data.historical.catalog.HistoricalCatalog._symbol_resolvers_for_load_config` | `qts.data.historical.catalog.HistoricalCatalog._chain_path_exists` |
| `qts.data.historical.catalog.HistoricalCatalog._symbol_resolvers_for_load_config` | `qts.registry.symbol_resolution.StaticSymbolResolver` |
| `qts.data.historical.catalog.HistoricalCatalog.from_historical_data_config` | `qts.data.historical.catalog.HistoricalCatalog._require_file` |
| `qts.data.historical.catalog.HistoricalCatalog.from_historical_data_config` | `qts.data.historical.catalog.HistoricalDataset` |
| `qts.data.historical.catalog.HistoricalCatalog.from_historical_data_config` | `qts.data.historical.chains.HistoricalChain.load` |
| `qts.data.historical.catalog.HistoricalCatalog.from_historical_data_config` | `qts.data.historical.csv_dataset.describe_csv_dataset` |
| `qts.data.historical.catalog.HistoricalCatalog.from_historical_data_config` | `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver` |
| `qts.data.historical.catalog.HistoricalCatalog.from_legacy_root` | `qts.data.historical.catalog.HistoricalCatalog._require_file` |
| `qts.data.historical.catalog.HistoricalCatalog.from_legacy_root` | `qts.data.historical.catalog.HistoricalDataset` |
| `qts.data.historical.catalog.HistoricalCatalog.from_legacy_root` | `qts.data.historical.chains.HistoricalChain.load` |
| `qts.data.historical.catalog.HistoricalCatalog.from_legacy_root` | `qts.data.historical.csv_dataset.describe_csv_dataset` |
| `qts.data.historical.catalog.HistoricalCatalog.from_legacy_root` | `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver` |
| `qts.data.historical.catalog.HistoricalCatalog.load` | `qts.data.historical.catalog.HistoricalCatalog._symbol_resolvers_for_load_config` |
| `qts.data.historical.catalog.HistoricalCatalog.load` | `qts.data.historical.catalog.HistoricalCatalog.from_historical_data_config` |
| `qts.data.historical.catalog.HistoricalCatalog.load` | `qts.data.historical.catalog.HistoricalCatalog.from_legacy_root` |
| `qts.data.historical.catalog.HistoricalCatalog.load` | `qts.data.historical.config.HistoricalDataConfig.from_yaml` |
| `qts.data.historical.catalog.HistoricalCatalogLoadConfig.__post_init__` | `qts.core.ids.InstrumentId` |
| `qts.data.historical.catalog.HistoricalCatalogLoadConfig.__post_init__` | `qts.data.historical.catalog.HistoricalCatalogLoadConfig._normalize_symbol` |
| `qts.data.historical.chains.HistoricalChain._parse_contract` | `qts.data.historical.chains.HistoricalChain._required_text` |
| `qts.data.historical.chains.HistoricalChain._parse_contract` | `qts.data.historical.chains.HistoricalContract` |
| `qts.data.historical.chains.HistoricalChain.instrument_id_for_symbol` | `qts.core.ids.InstrumentId` |
| `qts.data.historical.chains.HistoricalChain.instrument_id_for_symbol` | `qts.data.historical.chains.HistoricalChain.is_outright_symbol` |
| `qts.data.historical.chains.HistoricalChain.load` | `qts.data.historical.chains.HistoricalChain._exchange_code` |
| `qts.data.historical.chains.HistoricalChain.load` | `qts.data.historical.chains.HistoricalChain._parse_contract` |
| `qts.data.historical.chains.HistoricalChain.load` | `qts.data.historical.chains.HistoricalChain._required_decimal` |
| `qts.data.historical.chains.HistoricalChain.load` | `qts.data.historical.chains.HistoricalChain._required_text` |
| `qts.data.historical.config.HistoricalDataConfig._parse_bar_files` | `qts.data.historical.config.HistoricalBarFileConfig` |
| `qts.data.historical.config.HistoricalDataConfig._parse_catalogs` | `qts.data.historical.config.HistoricalDataCatalogConfig` |
| `qts.data.historical.config.HistoricalDataConfig._parse_catalogs` | `qts.data.historical.config.HistoricalDataConfig._parse_datasets` |
| `qts.data.historical.config.HistoricalDataConfig._parse_datasets` | `qts.data.historical.config.HistoricalDataConfig._parse_bar_files` |
| `qts.data.historical.config.HistoricalDataConfig._parse_datasets` | `qts.data.historical.config.HistoricalDatasetConfig` |
| `qts.data.historical.config.HistoricalDataConfig._parse_schemas` | `qts.data.historical.csv_format.HistoricalCsvSchema` |
| `qts.data.historical.config.HistoricalDataConfig._parse_store_defaults` | `qts.data.historical.config.HistoricalDataStoreDefaults` |
| `qts.data.historical.config.HistoricalDataConfig._parse_stores` | `qts.data.historical.config.HistoricalDataConfig._parse_store_defaults` |
| `qts.data.historical.config.HistoricalDataConfig._parse_stores` | `qts.data.historical.config.HistoricalDataStoreConfig` |
| `qts.data.historical.config.HistoricalDataConfig._select_bar_file` | `qts.data.historical.config.HistoricalBarFileConfig` |
| `qts.data.historical.config.HistoricalDataConfig._select_bar_file` | `qts.data.live_feed.FeedCapabilities` |
| `qts.data.historical.config.HistoricalDataConfig.from_yaml` | `qts.data.historical.config.HistoricalDataConfig._parse_catalogs` |
| `qts.data.historical.config.HistoricalDataConfig.from_yaml` | `qts.data.historical.config.HistoricalDataConfig._parse_schemas` |
| `qts.data.historical.config.HistoricalDataConfig.from_yaml` | `qts.data.historical.config.HistoricalDataConfig._parse_stores` |
| `qts.data.historical.config.HistoricalDataConfig.resolve_chain_path` | `qts.data.historical.config.HistoricalDataConfig.catalog` |
| `qts.data.historical.config.HistoricalDataConfig.resolve_chain_path` | `qts.data.historical.config.HistoricalDataConfig.store` |
| `qts.data.historical.config.HistoricalDataConfig.resolve_dataset` | `qts.data.historical.config.HistoricalDataConfig._csv_schema` |
| `qts.data.historical.config.HistoricalDataConfig.resolve_dataset` | `qts.data.historical.config.HistoricalDataConfig._select_bar_file` |
| `qts.data.historical.config.HistoricalDataConfig.resolve_dataset` | `qts.data.historical.config.HistoricalDataConfig.catalog` |
| `qts.data.historical.config.HistoricalDataConfig.resolve_dataset` | `qts.data.historical.config.HistoricalDataConfig.store` |
| `qts.data.historical.config.HistoricalDataConfig.resolve_dataset` | `qts.data.historical.config.HistoricalDatasetLocation` |
| `qts.data.historical.config.HistoricalDataStoreConfig.bars_path` | `qts.data.historical.config.HistoricalDataStoreConfig._join` |
| `qts.data.historical.config.HistoricalDataStoreConfig.bars_path` | `qts.data.historical.config.HistoricalDataStoreConfig._render_template` |
| `qts.data.historical.config.HistoricalDataStoreConfig.chain_path` | `qts.data.historical.config.HistoricalDataStoreConfig._join` |
| `qts.data.historical.config.HistoricalDataStoreConfig.chain_path` | `qts.data.historical.config.HistoricalDataStoreConfig._render_template` |
| `qts.data.historical.csv_dataset.HistoricalBarStream.__init__` | `qts.data.historical.csv_dataset.HistoricalCsvStats` |
| `qts.data.historical.csv_dataset.HistoricalBarStream.__iter__` | `qts.data.historical.csv_dataset.HistoricalBarStream._iter_all_supported_rows` |
| `qts.data.historical.csv_dataset.HistoricalBarStream.__iter__` | `qts.data.historical.csv_dataset.HistoricalBarStream._iter_selected_contract_rows` |
| `qts.data.historical.csv_dataset.HistoricalBarStream.__iter__` | `qts.data.historical.csv_dataset.HistoricalBarStream._iter_session_selected_contract_rows` |
| `qts.data.historical.csv_dataset.HistoricalBarStream.__iter__` | `qts.data.historical.csv_format.validate_historical_csv_columns` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._count_excluded_symbol` | `qts.data.historical.csv_dataset._is_spread_symbol` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._emit_selected_session_rows` | `qts.data.historical.csv_dataset.HistoricalBarStream._count_excluded_symbol` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._emit_selected_session_rows` | `qts.data.historical.csv_dataset.HistoricalBarStream._field` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._emit_selected_session_rows` | `qts.data.historical.csv_dataset.HistoricalBarStream._resolver_root` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._emit_selected_session_rows` | `qts.data.historical.csv_dataset._row_ohlcv` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._emit_selected_session_rows` | `qts.data.historical.csv_dataset._row_to_bar` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._emit_selected_session_rows` | `qts.data.historical.csv_format.historical_timeframe_delta` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._emit_selected_session_rows` | `qts.registry.future_roll.FutureContractCandidate` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._emit_selected_session_rows` | `qts.registry.future_roll.FutureRollSelection` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._iter_all_supported_rows` | `qts.data.historical.csv_dataset.HistoricalBarStream._count_excluded_symbol` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._iter_all_supported_rows` | `qts.data.historical.csv_dataset.HistoricalBarStream._field` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._iter_all_supported_rows` | `qts.data.historical.csv_dataset.HistoricalBarStream._timestamp` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._iter_all_supported_rows` | `qts.data.historical.csv_dataset._row_to_bar` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._iter_selected_contract_rows` | `qts.data.historical.csv_dataset.HistoricalBarStream._count_excluded_symbol` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._iter_selected_contract_rows` | `qts.data.historical.csv_dataset.HistoricalBarStream._field` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._iter_selected_contract_rows` | `qts.data.historical.csv_dataset.HistoricalBarStream._resolver_root` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._iter_selected_contract_rows` | `qts.data.historical.csv_dataset.HistoricalBarStream._timestamp_groups` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._iter_selected_contract_rows` | `qts.data.historical.csv_dataset._row_to_bar` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._iter_selected_contract_rows` | `qts.registry.future_roll.FutureContractCandidate` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._iter_selected_contract_rows` | `qts.registry.future_roll.FutureRollSelection` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._iter_session_selected_contract_rows` | `qts.data.historical.csv_dataset.HistoricalBarStream._emit_selected_session_rows` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._iter_session_selected_contract_rows` | `qts.data.historical.csv_dataset.HistoricalBarStream._timestamp_groups` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._resolver_root` | `qts.data.historical.csv_dataset._resolver_root` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._timestamp` | `qts.data.historical.csv_dataset.HistoricalBarStream._field` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._timestamp` | `qts.data.historical.csv_format.parse_historical_ts_event` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._timestamp_groups` | `qts.data.historical.csv_dataset.HistoricalBarStream._field` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._timestamp_groups` | `qts.data.historical.csv_format.parse_historical_ts_event` |
| `qts.data.historical.csv_dataset._as_symbol_resolver` | `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver` |
| `qts.data.historical.csv_dataset._row_ohlcv` | `qts.data.historical.csv_dataset._parse_ohlcv_values` |
| `qts.data.historical.csv_dataset._row_to_bar` | `qts.data.historical.csv_dataset._row_ohlcv` |
| `qts.data.historical.csv_dataset._row_to_bar` | `qts.data.historical.csv_format.historical_timeframe_delta` |
| `qts.data.historical.csv_dataset._row_to_bar` | `qts.data.historical.csv_format.parse_historical_ts_event` |
| `qts.data.historical.csv_dataset._row_to_bar` | `qts.domain.market_data.bar.Bar` |
| `qts.data.historical.csv_dataset.describe_csv_dataset` | `qts.data.historical.csv_dataset.CsvDatasetDescription` |
| `qts.data.historical.csv_dataset.describe_csv_dataset` | `qts.data.historical.csv_format.validate_historical_csv_columns` |
| `qts.data.historical.csv_dataset.iter_historical_bars` | `qts.data.historical.csv_dataset.HistoricalBarStream` |
| `qts.data.historical.csv_dataset.iter_historical_bars` | `qts.data.historical.csv_dataset._as_symbol_resolver` |
| `qts.data.historical.csv_dataset.validate_historical_sample` | `qts.data.historical.csv_dataset.HistoricalCsvStats` |
| `qts.data.historical.csv_dataset.validate_historical_sample` | `qts.data.historical.csv_dataset.HistoricalValidationSample` |
| `qts.data.historical.csv_dataset.validate_historical_sample` | `qts.data.historical.csv_dataset._as_symbol_resolver` |
| `qts.data.historical.csv_dataset.validate_historical_sample` | `qts.data.historical.csv_dataset._group_bars` |
| `qts.data.historical.csv_dataset.validate_historical_sample` | `qts.data.historical.csv_dataset._is_spread_symbol` |
| `qts.data.historical.csv_dataset.validate_historical_sample` | `qts.data.historical.csv_dataset._row_to_bar` |
| `qts.data.historical.csv_dataset.validate_historical_sample` | `qts.data.historical.csv_format.historical_timeframe_delta` |
| `qts.data.historical.csv_dataset.validate_historical_sample` | `qts.data.historical.csv_format.validate_historical_csv_columns` |
| `qts.data.historical.csv_dataset.validate_historical_sample` | `qts.data.validation_report.DataValidationIssue` |
| `qts.data.historical.csv_dataset.validate_historical_sample` | `qts.data.validation_report.DataValidationReport` |
| `qts.data.historical.csv_dataset.validate_historical_sample` | `qts.data.validation_report.validate_bars` |
| `qts.data.historical.csv_format.HistoricalCsvSchema.column_indices` | `qts.data.historical.csv_format.HistoricalCsvSchema.validate_columns` |
| `qts.data.historical.service.HistoricalMarketDataService.capabilities` | `qts.data.live_feed.FeedCapabilities` |
| `qts.data.historical.service.HistoricalMarketDataService.events` | `qts.data.historical.csv_dataset.iter_historical_bars` |
| `qts.data.historical.service.HistoricalMarketDataService.events` | `qts.data.live_feed.LiveFeedEvent` |
| `qts.data.historical.service.HistoricalMarketDataService.subscribe` | `qts.data.historical.service.HistoricalMarketDataService.capabilities` |
| `qts.data.historical.service.HistoricalMarketDataService.subscribe` | `qts.data.live_feed.LiveFeedSubscribed` |
| `qts.data.live_feed.FakeLiveFeedAdapter.capabilities` | `qts.data.live_feed.FeedCapabilities` |
| `qts.data.live_feed.FakeLiveFeedAdapter.emit` | `qts.data.live_feed.LiveFeedEvent` |
| `qts.data.live_feed.FakeLiveFeedAdapter.fail` | `qts.data.live_feed.LiveFeedFailure` |
| `qts.data.live_feed.FakeLiveFeedAdapter.subscribe` | `qts.data.live_feed.LiveFeedSubscribed` |
| `qts.data.live_feed.FeedCapabilities.source_timeframe_for` | `qts.data.live_feed.FeedCapabilities.supports_timeframe` |
| `qts.data.provenance.DatasetMetadata.__post_init__` | `qts.core.time.require_aware_datetime` |
| `qts.data.provenance.DatasetMetadata.__post_init__` | `qts.data.provenance.DatasetMetadata._require_text` |
| `qts.data.sessions.filter.filter_session_bars` | `qts.data.sessions.filter._bar_inside_session` |
| `qts.data.sessions.window.RegularSessionWindow.session_date_for_timestamp` | `qts.core.time.to_exchange_time` |
| `qts.data.sessions.window.RegularSessionWindow.session_id_for_timestamp` | `qts.data.sessions.window.RegularSessionWindow.session_date_for_timestamp` |
| `qts.data.stores.parquet_store.ParquetMarketDataStore._bar_from_json` | `qts.core.ids.InstrumentId` |
| `qts.data.stores.parquet_store.ParquetMarketDataStore._bar_from_json` | `qts.domain.market_data.bar.Bar` |
| `qts.data.stores.parquet_store.ParquetMarketDataStore._read_file` | `qts.data.stores.parquet_store.ParquetMarketDataStore._bar_from_json` |
| `qts.data.stores.parquet_store.ParquetMarketDataStore.read_bars` | `qts.data.stores.parquet_store.ParquetMarketDataStore._read_file` |
| `qts.data.stores.parquet_store.ParquetMarketDataStore.write_bars` | `qts.data.stores.parquet_store.ParquetMarketDataStore._bar_to_json` |
| `qts.data.stores.parquet_store.ParquetMarketDataStore.write_bars` | `qts.data.stores.parquet_store.ParquetMarketDataStore._path_for` |
| `qts.data.stores.parquet_store.ParquetMarketDataStore.write_bars` | `qts.data.stores.parquet_store.ParquetMarketDataStore._read_file` |
| `qts.data.subscriptions.logical_key` | `qts.data.subscriptions.LogicalSubscriptionKey` |
| `qts.data.subscriptions.plan_physical_subscription` | `qts.data.subscriptions.PhysicalSubscriptionKey` |
| `qts.data.validation_report._append_ohlc_issue` | `qts.data.validation_report.DataValidationIssue` |
| `qts.data.validation_report.validate_bars` | `qts.data.validation_report.DataValidationIssue` |
| `qts.data.validation_report.validate_bars` | `qts.data.validation_report.DataValidationReport` |
| `qts.data.validation_report.validate_bars` | `qts.data.validation_report._append_ohlc_issue` |
| `qts.domain.events.event.BaseEvent.__post_init__` | `qts.core.time.require_aware_datetime` |
| `qts.domain.events.metadata.EventMetadata.__post_init__` | `qts.core.time.require_aware_datetime` |
| `qts.domain.instruments.contract_spec.ContractSpec.__post_init__` | `qts.domain.instruments.contract_spec.ContractSpec._require_positive` |
| `qts.domain.market_data.bar.Bar.__post_init__` | `qts.core.time.TimeInterval` |
| `qts.domain.market_data.bar.Bar.__post_init__` | `qts.domain.market_data.bar.Bar._require_non_negative` |
| `qts.domain.market_data.bar.Bar.interval` | `qts.core.time.TimeInterval` |
| `qts.domain.market_data.bar.Quote.__post_init__` | `qts.core.time.require_aware_datetime` |
| `qts.domain.market_data.bar.Tick.__post_init__` | `qts.core.time.require_aware_datetime` |
| `qts.domain.risk.request.OrderRiskRequest.__post_init__` | `qts.core.time.require_aware_datetime` |
| `qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionAdapter.normalize_execution_report` | `qts.execution.order_manager.ExecutionReport` |
| `qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionAdapter.to_order_request` | `qts.execution.adapters.ibkr_order_execution.IbkrOrderRequest` |
| `qts.execution.broker.FakeBrokerAdapter._report` | `qts.execution.broker.BrokerExecutionReport` |
| `qts.execution.broker.FakeBrokerAdapter.cancel_order` | `qts.execution.broker.FakeBrokerAdapter._report` |
| `qts.execution.broker.FakeBrokerAdapter.capabilities` | `qts.execution.broker.BrokerCapabilities` |
| `qts.execution.broker.FakeBrokerAdapter.emit_fill` | `qts.execution.broker.FakeBrokerAdapter._report` |
| `qts.execution.broker.FakeBrokerAdapter.submit_order` | `qts.execution.broker.FakeBrokerAdapter._report` |
| `qts.execution.broker.normalize_broker_execution_report` | `qts.execution.order_manager.ExecutionReport` |
| `qts.execution.broker.normalize_broker_execution_report` | `qts.execution.order_manager.ExecutionReportStatus` |
| `qts.execution.order_manager.OrderManager.__init__` | `qts.execution.idempotency.FillIdempotencyStore` |
| `qts.execution.order_manager.OrderManager._fills_for_report` | `qts.execution.order_manager.OrderFill` |
| `qts.execution.order_manager.OrderManager._replace_order` | `qts.execution.order_manager.Order` |
| `qts.execution.order_manager.OrderManager.create_order` | `qts.execution.order_manager.Order` |
| `qts.execution.order_manager.OrderManager.create_order` | `qts.execution.order_state_machine.OrderStateMachine` |
| `qts.execution.order_manager.OrderManager.mark_sent` | `qts.execution.order_manager.OrderManager._replace_order` |
| `qts.execution.order_manager.OrderManager.process_report` | `qts.execution.order_manager.OrderManager._event_for_report` |
| `qts.execution.order_manager.OrderManager.process_report` | `qts.execution.order_manager.OrderManager._fills_for_report` |
| `qts.execution.order_manager.OrderManager.process_report` | `qts.execution.order_manager.OrderManager._replace_order` |
| `qts.execution.order_manager.OrderManager.process_report` | `qts.execution.order_manager.OrderManagerResult` |
| `qts.execution.order_manager.OrderManager.request_cancel` | `qts.execution.order_manager.OrderManager._replace_order` |
| `qts.execution.order_manager.OrderManager.request_replace` | `qts.execution.order_manager.Order` |
| `qts.execution.order_manager.OrderManager.request_replace` | `qts.execution.order_manager.OrderIntent` |
| `qts.execution.order_manager.OrderManager.restore` | `qts.execution.idempotency.FillIdempotencyStore.restore` |
| `qts.execution.order_manager.OrderManager.restore` | `qts.execution.order_state_machine.OrderStateMachine` |
| `qts.execution.order_manager.OrderManager.snapshot` | `qts.execution.order_manager.OrderManagerSnapshot` |
| `qts.execution.order_state_machine.OrderStateMachine.apply` | `qts.execution.order_state_machine.OrderTransitionError` |
| `qts.execution.simulator.fill_model.ImmediateFillModel.fill` | `qts.execution.order_manager.ExecutionReport` |
| `qts.execution.simulator.simulated_broker.SimulatedBroker.__init__` | `qts.execution.simulator.fill_model.ImmediateFillModel` |
| `qts.factors.momentum.MomentumFactor.compute` | `qts.factors.momentum.FactorResult` |
| `qts.factors.momentum.MomentumFactor.compute` | `qts.factors.momentum.FactorScore` |
| `qts.factors.momentum.MomentumFactor.compute` | `qts.factors.momentum.MomentumFactor._momentum` |
| `qts.indicators.price.ema.EMA.__post_init__` | `qts.indicators.rolling.RollingWindow` |
| `qts.indicators.price.sma.SMA.__post_init__` | `qts.indicators.rolling.RollingWindow` |
| `qts.indicators.rolling.RollingWindow.restore` | `qts.indicators.rolling.RollingWindow` |
| `qts.load.synthetic_market_data.generate_bars` | `qts.domain.market_data.bar.Bar` |
| `qts.observability.logging.build_log_record` | `qts.observability.logging._is_secret_key` |
| `qts.observability.logging.build_log_record` | `qts.observability.logging._metadata_fields` |
| `qts.observability.metrics.MetricsRegistry.gauge` | `qts.observability.metrics.MetricsRegistry._metric_key` |
| `qts.observability.metrics.MetricsRegistry.increment` | `qts.observability.metrics.MetricsRegistry._metric_key` |
| `qts.observability.metrics.MetricsRegistry.observe_queue` | `qts.observability.metrics.MetricsRegistry.gauge` |
| `qts.portfolio.cash_book.CashBook.apply_delta` | `qts.portfolio.cash_book.CashBook._normalize_currency` |
| `qts.portfolio.cash_book.CashBook.apply_delta` | `qts.portfolio.cash_book.CashBook.balance` |
| `qts.portfolio.cash_book.CashBook.available` | `qts.portfolio.cash_book.CashBook._normalize_currency` |
| `qts.portfolio.cash_book.CashBook.available` | `qts.portfolio.cash_book.CashBook.balance` |
| `qts.portfolio.cash_book.CashBook.balance` | `qts.portfolio.cash_book.CashBook._normalize_currency` |
| `qts.portfolio.position_book.PositionBook.apply_delta` | `qts.portfolio.position_book.PositionBook.quantity` |
| `qts.portfolio.position_book.PositionBook.snapshot` | `qts.portfolio.position_book.Position` |
| `qts.portfolio.reservation_book.ReservationBook.reserve` | `qts.portfolio.reservation_book.Reservation` |
| `qts.portfolio.reservation_book.ReservationBook.reserve` | `qts.portfolio.reservation_book.ReservationBook._normalize_currency` |
| `qts.portfolio.reservation_book.ReservationBook.reserved` | `qts.portfolio.reservation_book.ReservationBook._normalize_currency` |
| `qts.reconciliation._amount_repr` | `qts.reconciliation._amount` |
| `qts.reconciliation._compare_cash` | `qts.reconciliation._quantity_item` |
| `qts.reconciliation._compare_orders` | `qts.reconciliation.DriftItem` |
| `qts.reconciliation._compare_orders` | `qts.reconciliation._order_repr` |
| `qts.reconciliation._compare_positions` | `qts.reconciliation._quantity_item` |
| `qts.reconciliation._quantity_item` | `qts.reconciliation.DriftItem` |
| `qts.reconciliation._quantity_item` | `qts.reconciliation._amount` |
| `qts.reconciliation._quantity_item` | `qts.reconciliation._amount_repr` |
| `qts.reconciliation.reconcile_snapshots` | `qts.reconciliation.ReconciliationReport` |
| `qts.reconciliation.reconcile_snapshots` | `qts.reconciliation._compare_cash` |
| `qts.reconciliation.reconcile_snapshots` | `qts.reconciliation._compare_orders` |
| `qts.reconciliation.reconcile_snapshots` | `qts.reconciliation._compare_positions` |
| `qts.reconciliation.reconcile_snapshots` | `qts.reconciliation._drift_sort_key` |
| `qts.reconciliation.startup_reconciliation_gate` | `qts.reconciliation.StartupReconciliationDecision` |
| `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.instrument_id_for_symbol` | `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.to_instrument_id` |
| `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.is_supported_symbol` | `qts.registry.broker_symbol_mapping.BrokerSymbolMapping._normalize_broker_symbol` |
| `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.register` | `qts.registry.broker_symbol_mapping.BrokerSymbolMapping._normalize_broker_symbol` |
| `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.to_instrument_id` | `qts.registry.broker_symbol_mapping.BrokerSymbolMapping._normalize_broker_symbol` |
| `qts.registry.future_chain_registry.FutureChainRegistry._get_chain` | `qts.registry.future_chain_registry.FutureChainRegistry._normalize_root` |
| `qts.registry.future_chain_registry.FutureChainRegistry.register` | `qts.registry.future_chain_registry.FutureChainRegistry._normalize_root` |
| `qts.registry.future_chain_registry.FutureChainRegistry.resolve_contract` | `qts.registry.future_chain_registry.FutureChainRegistry._get_chain` |
| `qts.registry.future_roll.FutureRollRegistry.continuous_instrument_id` | `qts.registry.future_roll.FutureRollRegistry._normalize_root` |
| `qts.registry.future_roll.FutureRollRegistry.execution_price` | `qts.registry.future_roll.FutureRollRegistry._selection_at` |
| `qts.registry.future_roll.FutureRollRegistry.register_root` | `qts.core.ids.InstrumentId` |
| `qts.registry.future_roll.FutureRollRegistry.register_root` | `qts.registry.future_roll.FutureRollRegistry._normalize_root` |
| `qts.registry.future_roll.FutureRollRegistry.resolve_contract` | `qts.registry.future_roll.FutureRollRegistry._selection_at` |
| `qts.registry.future_roll.FutureRollRegistry.resolve_contract` | `qts.registry.future_roll.FutureRollRegistry.continuous_instrument_id` |
| `qts.registry.instrument_registry.InstrumentRegistry.get_contract_spec` | `qts.registry.instrument_registry.InstrumentRegistry.get_instrument` |
| `qts.registry.instrument_registry.InstrumentRegistry.register` | `qts.registry.instrument_registry.InstrumentRegistry._normalize_symbol` |
| `qts.registry.instrument_registry.InstrumentRegistry.resolve` | `qts.registry.instrument_registry.InstrumentRegistry._normalize_symbol` |
| `qts.registry.option_chain_registry.OptionChainRegistry.find` | `qts.registry.option_chain_registry.OptionChainRegistry.options_for` |
| `qts.registry.providers.comex_gold_calendar_provider.ComexGoldCalendarProvider.session_for` | `qts.core.time.TimeInterval` |
| `qts.registry.providers.comex_gold_calendar_provider.ComexGoldCalendarProvider.session_for` | `qts.registry.calendar_registry.MarketSession` |
| `qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider.session_for` | `qts.core.time.TimeInterval` |
| `qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider.session_for` | `qts.registry.calendar_registry.MarketSession` |
| `qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider.session_for` | `qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider._to_datetime` |
| `qts.registry.symbol_resolution.StaticSymbolResolver.__post_init__` | `qts.registry.symbol_resolution.StaticSymbolResolver._normalize_symbol` |
| `qts.registry.symbol_resolution.StaticSymbolResolver.instrument_id_for_symbol` | `qts.registry.symbol_resolution.StaticSymbolResolver._normalize_symbol` |
| `qts.registry.symbol_resolution.StaticSymbolResolver.is_supported_symbol` | `qts.registry.symbol_resolution.StaticSymbolResolver._normalize_symbol` |
| `qts.risk.kill_switch.KillSwitchRegistry.activate` | `qts.risk.kill_switch.KillSwitchState` |
| `qts.risk.kill_switch.KillSwitchRegistry.check_order` | `qts.risk.kill_switch.KillSwitchRegistry._matching_scopes` |
| `qts.risk.kill_switch.KillSwitchRegistry.deactivate` | `qts.risk.kill_switch.KillSwitchState` |
| `qts.risk.rule_registry.RiskRuleRegistry.build` | `qts.risk.rule_registry.RiskRuleRegistry._param` |
| `qts.risk.rule_registry.RiskRuleRegistry.build` | `qts.risk.rules.max_notional.MaxNotionalRule` |
| `qts.risk.rule_registry.RiskRuleRegistry.build` | `qts.risk.rules.max_order_qty.MaxOrderQuantityRule` |
| `qts.runtime.actor_ref.ActorRef.process_all` | `qts.runtime.actor_ref.ActorRef.process_one` |
| `qts.runtime.actors.account_actor.AccountActor.__init__` | `qts.execution.idempotency.FillIdempotencyStore` |
| `qts.runtime.actors.account_actor.AccountActor.__init__` | `qts.portfolio.cash_book.CashBook` |
| `qts.runtime.actors.account_actor.AccountActor.__init__` | `qts.portfolio.position_book.PositionBook` |
| `qts.runtime.actors.account_actor.AccountActor.handle` | `qts.runtime.actors.account_actor.AccountActor._apply_fill` |
| `qts.runtime.actors.account_actor.AccountActor.snapshot` | `qts.runtime.actors.account_actor.AccountSnapshot` |
| `qts.runtime.actors.execution_actor.ExecutionActor.__init__` | `qts.execution.simulator.simulated_broker.SimulatedBroker` |
| `qts.runtime.actors.market_data_actor.MarketDataActor.__init__` | `qts.data.bars.timeframe.Timeframe.parse` |
| `qts.runtime.actors.market_data_actor.MarketDataActor._aggregator_for` | `qts.data.bars.aggregator.BarAggregator` |
| `qts.runtime.actors.market_data_actor.MarketDataActor._logical_aggregator_for` | `qts.data.bars.aggregator.BarAggregator` |
| `qts.runtime.actors.market_data_actor.MarketDataActor._logical_aggregator_for` | `qts.data.bars.timeframe.Timeframe.parse` |
| `qts.runtime.actors.market_data_actor.MarketDataActor._publish_to_logical_subscribers` | `qts.runtime.actors.market_data_actor.MarketDataActor._logical_aggregator_for` |
| `qts.runtime.actors.market_data_actor.MarketDataActor._publish_to_logical_subscribers` | `qts.runtime.actors.market_data_actor.MarketDataActor._publish` |
| `qts.runtime.actors.market_data_actor.MarketDataActor._publish_to_logical_subscribers` | `qts.runtime.actors.market_data_actor.MarketDataActor._publish_to` |
| `qts.runtime.actors.market_data_actor.MarketDataActor._subscribe` | `qts.data.live_feed.FeedSubscription` |
| `qts.runtime.actors.market_data_actor.MarketDataActor._subscribe` | `qts.data.subscriptions.LogicalSubscription` |
| `qts.runtime.actors.market_data_actor.MarketDataActor._subscribe` | `qts.data.subscriptions.logical_key` |
| `qts.runtime.actors.market_data_actor.MarketDataActor._subscribe` | `qts.data.subscriptions.plan_physical_subscription` |
| `qts.runtime.actors.market_data_actor.MarketDataActor._subscribe` | `qts.runtime.actors.market_data_actor.MarketDataActor._subscription_id` |
| `qts.runtime.actors.market_data_actor.MarketDataActor.handle` | `qts.runtime.actors.market_data_actor.MarketDataActor._aggregator_for` |
| `qts.runtime.actors.market_data_actor.MarketDataActor.handle` | `qts.runtime.actors.market_data_actor.MarketDataActor._publish` |
| `qts.runtime.actors.market_data_actor.MarketDataActor.handle` | `qts.runtime.actors.market_data_actor.MarketDataActor._publish_to_logical_subscribers` |
| `qts.runtime.actors.market_data_actor.MarketDataActor.handle` | `qts.runtime.actors.market_data_actor.MarketDataActor._subscribe` |
| `qts.runtime.actors.order_manager_actor.OrderManagerActor.__init__` | `qts.execution.order_manager.OrderManager` |
| `qts.runtime.actors.order_manager_actor.OrderManagerActor._handle_report` | `qts.runtime.actors.account_actor.ApplyFill` |
| `qts.runtime.actors.order_manager_actor.OrderManagerActor._handle_submit` | `qts.runtime.actors.execution_actor.OrderExecutionRequest` |
| `qts.runtime.actors.order_manager_actor.OrderManagerActor.handle` | `qts.runtime.actors.order_manager_actor.OrderManagerActor._handle_report` |
| `qts.runtime.actors.order_manager_actor.OrderManagerActor.handle` | `qts.runtime.actors.order_manager_actor.OrderManagerActor._handle_submit` |
| `qts.runtime.actors.signal_aggregator_actor.SignalAggregatorActor.handle` | `qts.runtime.actors.signal_aggregator_actor.AggregatedSignalBatch` |
| `qts.runtime.actors.strategy_actor.StrategyActor._handle_bar` | `qts.runtime.actors.strategy_actor.StrategyBarResult` |
| `qts.runtime.actors.strategy_actor.StrategyActor._handle_finalize` | `qts.runtime.actors.strategy_actor.StrategyFinalized` |
| `qts.runtime.actors.strategy_actor.StrategyActor.handle` | `qts.runtime.actors.strategy_actor.StrategyActor._handle_bar` |
| `qts.runtime.actors.strategy_actor.StrategyActor.handle` | `qts.runtime.actors.strategy_actor.StrategyActor._handle_finalize` |
| `qts.runtime.event_store.FileEventStore._event_from_json` | `qts.core.ids.CausationId` |
| `qts.runtime.event_store.FileEventStore._event_from_json` | `qts.core.ids.CorrelationId` |
| `qts.runtime.event_store.FileEventStore._event_from_json` | `qts.core.ids.EventId` |
| `qts.runtime.event_store.FileEventStore._event_from_json` | `qts.domain.events.event.BaseEvent` |
| `qts.runtime.event_store.FileEventStore.append` | `qts.runtime.event_store.FileEventStore._event_to_json` |
| `qts.runtime.event_store.FileEventStore.append` | `qts.runtime.event_store.FileEventStore.replay` |
| `qts.runtime.event_store.FileEventStore.by_correlation_id` | `qts.runtime.event_store.FileEventStore.replay` |
| `qts.runtime.event_store.FileEventStore.replay` | `qts.runtime.event_store.FileEventStore._event_from_json` |
| `qts.runtime.event_store.InMemoryEventStore.append_many` | `qts.runtime.event_store.InMemoryEventStore.append` |
| `qts.runtime.live.LiveRuntime.__init__` | `qts.runtime.live.LiveRuntimeStateMachine` |
| `qts.runtime.live.LiveRuntime.submit_order` | `qts.runtime.live.RuntimeOrderResult` |
| `qts.runtime.live.validate_live_startup` | `qts.runtime.live.LiveStartupDecision` |
| `qts.runtime.router.EventRouter.route` | `qts.runtime.router.RouteNotFoundError` |
| `qts.strategy_sdk.context.StrategyContext.close` | `qts.strategy_sdk.context.StrategyContext._emit` |
| `qts.strategy_sdk.context.StrategyContext.close` | `qts.strategy_sdk.target.TargetIntent` |
| `qts.strategy_sdk.context.StrategyContext.future` | `qts.strategy_sdk.asset_ref.AssetRef` |
| `qts.strategy_sdk.context.StrategyContext.option` | `qts.strategy_sdk.asset_ref.AssetRef` |
| `qts.strategy_sdk.context.StrategyContext.rebalance` | `qts.strategy_sdk.context.StrategyContext.target_percent` |
| `qts.strategy_sdk.context.StrategyContext.subscribe` | `qts.strategy_sdk.context.DataSubscription` |
| `qts.strategy_sdk.context.StrategyContext.symbol` | `qts.strategy_sdk.asset_ref.AssetRef` |
| `qts.strategy_sdk.context.StrategyContext.target_percent` | `qts.strategy_sdk.context.StrategyContext._emit` |
| `qts.strategy_sdk.context.StrategyContext.target_percent` | `qts.strategy_sdk.target.TargetIntent` |
| `qts.strategy_sdk.context.StrategyContext.target_quantity` | `qts.strategy_sdk.context.StrategyContext._emit` |
| `qts.strategy_sdk.context.StrategyContext.target_quantity` | `qts.strategy_sdk.target.TargetIntent` |
| `qts.strategy_sdk.context.StrategyContext.target_value` | `qts.strategy_sdk.context.StrategyContext._emit` |
| `qts.strategy_sdk.context.StrategyContext.target_value` | `qts.strategy_sdk.target.TargetIntent` |
| `qts.strategy_sdk.data_view.DataView.bar` | `qts.strategy_sdk.data_view.DataView.history` |
| `qts.strategy_sdk.data_view.DataView.close` | `qts.strategy_sdk.data_view.DataView.bar` |
| `qts.strategy_sdk.factors.FactorFactory.momentum` | `qts.factors.momentum.MomentumFactor` |
| `qts.strategy_sdk.indicators.IndicatorFactory.sma` | `qts.indicators.price.sma.SMA` |
| `qts.strategy_sdk.indicators.IndicatorFactory.sma` | `qts.strategy_sdk.indicators.AssetIndicator` |
| `qts.strategy_sdk.portfolio_view.PortfolioView.exposure` | `qts.strategy_sdk.portfolio_view.PortfolioView.position` |
| `qts.strategy_sdk.portfolio_view.PortfolioView.position` | `qts.strategy_sdk.portfolio_view.PortfolioPosition` |
| `qts.strategy_sdk.portfolio_view.PortfolioView.weight` | `qts.strategy_sdk.portfolio_view.PortfolioView.exposure` |
| `scripts.bootstrap.main` | `qts.load.bootstrap.bootstrap_local` |
| `scripts.ibkr_collect_environment_evidence._collect_network_evidence` | `scripts.ibkr_collect_environment_evidence._mapping` |
| `scripts.ibkr_collect_environment_evidence._collect_network_evidence` | `scripts.ibkr_collect_environment_evidence._tcp_probe` |
| `scripts.ibkr_collect_environment_evidence._evidence_filename` | `scripts.ibkr_collect_environment_evidence._safe_label` |
| `scripts.ibkr_collect_environment_evidence._summarize_config` | `scripts.ibkr_collect_environment_evidence._env_ref_status` |
| `scripts.ibkr_collect_environment_evidence._summarize_config` | `scripts.ibkr_collect_environment_evidence._mapping` |
| `scripts.ibkr_collect_environment_evidence._validate_ibkr_config` | `scripts.ibkr_collect_environment_evidence._mapping` |
| `scripts.ibkr_collect_environment_evidence._validate_ibkr_config` | `scripts.ibkr_collect_environment_evidence._validate_connection` |
| `scripts.ibkr_collect_environment_evidence.collect_environment_evidence` | `scripts.ibkr_collect_environment_evidence._collect_network_evidence` |
| `scripts.ibkr_collect_environment_evidence.collect_environment_evidence` | `scripts.ibkr_collect_environment_evidence._evidence_filename` |
| `scripts.ibkr_collect_environment_evidence.collect_environment_evidence` | `scripts.ibkr_collect_environment_evidence._read_config` |
| `scripts.ibkr_collect_environment_evidence.collect_environment_evidence` | `scripts.ibkr_collect_environment_evidence._summarize_config` |
| `scripts.ibkr_collect_environment_evidence.collect_environment_evidence` | `scripts.ibkr_collect_environment_evidence._validate_ibkr_config` |
| `scripts.ibkr_collect_environment_evidence.main` | `scripts.ibkr_collect_environment_evidence.collect_environment_evidence` |
| `scripts.ibkr_paper_order_lifecycle_drill._account_id` | `scripts.ibkr_paper_order_lifecycle_drill._mapping` |
| `scripts.ibkr_paper_order_lifecycle_drill._evidence_filename` | `scripts.ibkr_paper_order_lifecycle_drill._safe_label` |
| `scripts.ibkr_paper_order_lifecycle_drill._summarize_config` | `scripts.ibkr_paper_order_lifecycle_drill._account_id` |
| `scripts.ibkr_paper_order_lifecycle_drill._summarize_config` | `scripts.ibkr_paper_order_lifecycle_drill._mapping` |
| `scripts.ibkr_paper_order_lifecycle_drill._validate_paper_only_ibkr_config` | `scripts.ibkr_paper_order_lifecycle_drill._account_id` |
| `scripts.ibkr_paper_order_lifecycle_drill._validate_paper_only_ibkr_config` | `scripts.ibkr_paper_order_lifecycle_drill._mapping` |
| `scripts.ibkr_paper_order_lifecycle_drill.main` | `scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill` |
| `scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill` | `qts.core.ids.AccountId` |
| `scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill` | `qts.core.ids.BrokerId` |
| `scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill` | `qts.core.ids.InstrumentId` |
| `scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill` | `qts.core.ids.OrderId` |
| `scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill` | `qts.core.ids.StrategyId` |
| `scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill` | `qts.execution.broker.BrokerOrderRequest` |
| `scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill` | `qts.execution.broker.FakeBrokerAdapter` |
| `scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill` | `qts.execution.broker.normalize_broker_execution_report` |
| `scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill` | `qts.execution.order_manager.CancelIntent` |
| `scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill` | `qts.execution.order_manager.OrderIntent` |
| `scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill` | `qts.execution.order_manager.OrderManager` |
| `scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill` | `qts.execution.order_manager.OrderSide` |
| `scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill` | `scripts.ibkr_paper_order_lifecycle_drill._account_id` |
| `scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill` | `scripts.ibkr_paper_order_lifecycle_drill._evidence_filename` |
| `scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill` | `scripts.ibkr_paper_order_lifecycle_drill._execution_report_evidence` |
| `scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill` | `scripts.ibkr_paper_order_lifecycle_drill._read_config` |
| `scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill` | `scripts.ibkr_paper_order_lifecycle_drill._summarize_config` |
| `scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill` | `scripts.ibkr_paper_order_lifecycle_drill._validate_paper_only_ibkr_config` |
| `scripts.run_backtest.main` | `qts.backtest.runner.run_backtest` |
| `scripts.run_load.main` | `qts.core.ids.InstrumentId` |
| `scripts.run_load.main` | `qts.load.synthetic_market_data.SyntheticMarketDataConfig` |
| `scripts.run_load.main` | `qts.load.synthetic_market_data.generate_bars` |
| `scripts.run_paper.main` | `qts.application.commands.start_paper.PaperRuntimeConfig` |
| `scripts.run_paper.main` | `qts.application.commands.start_paper.start_paper` |
| `scripts.validate_historical.main` | `qts.data.historical.catalog.HistoricalCatalog.from_legacy_root` |
| `scripts.validate_historical.main` | `qts.data.historical.csv_dataset.validate_historical_sample` |
| `scripts.verify_guardrails._check_backtest_engine_cohesion` | `scripts.verify_guardrails.GuardrailViolation` |
| `scripts.verify_guardrails._check_backtest_engine_cohesion` | `scripts.verify_guardrails._iter_imports` |
| `scripts.verify_guardrails._check_backtest_input_cohesion` | `scripts.verify_guardrails.GuardrailViolation` |
| `scripts.verify_guardrails._check_backtest_input_cohesion` | `scripts.verify_guardrails._iter_imported_names` |
| `scripts.verify_guardrails._check_backtest_input_cohesion` | `scripts.verify_guardrails._iter_imports` |
| `scripts.verify_guardrails._check_backtest_runner_cohesion` | `scripts.verify_guardrails.GuardrailViolation` |
| `scripts.verify_guardrails._check_backtest_runner_cohesion` | `scripts.verify_guardrails._iter_imported_names` |
| `scripts.verify_guardrails._check_backtest_runner_cohesion` | `scripts.verify_guardrails._iter_imports` |
| `scripts.verify_guardrails._check_broker_specific_code` | `scripts.verify_guardrails._check_forbidden_tokens` |
| `scripts.verify_guardrails._check_forbidden_tokens` | `scripts.verify_guardrails.GuardrailViolation` |
| `scripts.verify_guardrails._check_forbidden_tokens` | `scripts.verify_guardrails._contains_forbidden_token` |
| `scripts.verify_guardrails._check_forbidden_tokens` | `scripts.verify_guardrails._node_identifier_name` |
| `scripts.verify_guardrails._check_import` | `scripts.verify_guardrails.GuardrailViolation` |
| `scripts.verify_guardrails._check_import` | `scripts.verify_guardrails._is_forbidden_adapter_dependency` |
| `scripts.verify_guardrails._check_import` | `scripts.verify_guardrails._is_forbidden_dependency` |
| `scripts.verify_guardrails._check_oop_helper_ownership` | `scripts.verify_guardrails.GuardrailViolation` |
| `scripts.verify_guardrails._check_oop_helper_ownership` | `scripts.verify_guardrails._node_references_name` |
| `scripts.verify_guardrails._check_oop_public_factory_functions` | `scripts.verify_guardrails.GuardrailViolation` |
| `scripts.verify_guardrails._check_product_specific_code` | `scripts.verify_guardrails._check_forbidden_tokens` |
| `scripts.verify_guardrails._check_python_file` | `scripts.verify_guardrails._check_backtest_engine_cohesion` |
| `scripts.verify_guardrails._check_python_file` | `scripts.verify_guardrails._check_backtest_input_cohesion` |
| `scripts.verify_guardrails._check_python_file` | `scripts.verify_guardrails._check_backtest_runner_cohesion` |
| `scripts.verify_guardrails._check_python_file` | `scripts.verify_guardrails._check_broker_specific_code` |
| `scripts.verify_guardrails._check_python_file` | `scripts.verify_guardrails._check_import` |
| `scripts.verify_guardrails._check_python_file` | `scripts.verify_guardrails._check_oop_helper_ownership` |
| `scripts.verify_guardrails._check_python_file` | `scripts.verify_guardrails._check_oop_public_factory_functions` |
| `scripts.verify_guardrails._check_python_file` | `scripts.verify_guardrails._check_product_specific_code` |
| `scripts.verify_guardrails._check_python_file` | `scripts.verify_guardrails._check_shared_capability_placement` |
| `scripts.verify_guardrails._check_python_file` | `scripts.verify_guardrails._check_test_support_code` |
| `scripts.verify_guardrails._check_python_file` | `scripts.verify_guardrails._has_allowed_prefix` |
| `scripts.verify_guardrails._check_python_file` | `scripts.verify_guardrails._iter_imports` |
| `scripts.verify_guardrails._check_shared_capability_placement` | `scripts.verify_guardrails.GuardrailViolation` |
| `scripts.verify_guardrails._check_shared_capability_placement` | `scripts.verify_guardrails._has_allowed_prefix` |
| `scripts.verify_guardrails._check_shared_capability_placement` | `scripts.verify_guardrails._identifier_tokens` |
| `scripts.verify_guardrails._check_test_support_code` | `scripts.verify_guardrails.GuardrailViolation` |
| `scripts.verify_guardrails._check_test_support_code` | `scripts.verify_guardrails._contains_forbidden_token` |
| `scripts.verify_guardrails._check_test_support_code` | `scripts.verify_guardrails._identifier_tokens` |
| `scripts.verify_guardrails._check_test_support_code` | `scripts.verify_guardrails._node_identifier_name` |
| `scripts.verify_guardrails._contains_forbidden_token` | `scripts.verify_guardrails._identifier_tokens` |
| `scripts.verify_guardrails.main` | `scripts.verify_guardrails.run_guardrails` |
| `scripts.verify_guardrails.run_guardrails` | `scripts.verify_guardrails._check_python_file` |
