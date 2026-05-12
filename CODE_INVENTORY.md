# 非 Test Python 类、函数、方法与调用关系全量清单

生成时间：2026-05-12T17:02:24+08:00

## 范围与口径

- 源范围：仓库内所有 `.py` 文件，排除 `tests/`、`test_*.py`、`*_test.py`、虚拟环境和构建目录。
- 包含：模块级函数、异步函数、类、实例方法、类方法、静态方法、属性方法、嵌套函数。
- 调用关系：基于 AST 提取每个函数/方法体内的直接 `Call` 表达式，并做可解析的内部符号匹配。
- 作用说明：优先使用源码 docstring 首句；无 docstring 时按符号名称静态推断。

## 汇总

- 非 test Python 文件数：52
- 成功解析文件数：208
- 解析失败文件数：0
- 符号总数：1075
- 类：311
- 函数/方法总数：764
- 模块级函数：138
- 方法/属性：626

### 按类型统计

| 类型 | 数量 |
|---|---:|
| `async_method` | 4 |
| `async_module_function` | 1 |
| `class` | 311 |
| `classmethod` | 33 |
| `method` | 475 |
| `module_function` | 137 |
| `nested_function` | 2 |
| `property` | 51 |
| `staticmethod` | 61 |

## 文件清单

| 文件 | 模块 | 符号数 |
|---|---|---:|
| `backend/src/qts/__init__.py` | `qts` | 0 |
| `backend/src/qts/api/__init__.py` | `qts.api` | 0 |
| `backend/src/qts/api/app.py` | `qts.api.app` | 1 |
| `backend/src/qts/api/mappers.py` | `qts.api.mappers` | 4 |
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
| `backend/src/qts/application/commands/ibkr_environment_evidence.py` | `qts.application.commands.ibkr_environment_evidence` | 10 |
| `backend/src/qts/application/commands/ibkr_paper_order_lifecycle_drill.py` | `qts.application.commands.ibkr_paper_order_lifecycle_drill` | 8 |
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
| `backend/src/qts/backtest/actor_loop.py` | `qts.backtest.actor_loop` | 11 |
| `backend/src/qts/backtest/config.py` | `qts.backtest.config` | 24 |
| `backend/src/qts/backtest/config_loader.py` | `qts.backtest.config_loader` | 5 |
| `backend/src/qts/backtest/engine.py` | `qts.backtest.engine` | 15 |
| `backend/src/qts/backtest/historical_data_portal.py` | `qts.backtest.historical_data_portal` | 4 |
| `backend/src/qts/backtest/inputs.py` | `qts.backtest.inputs` | 15 |
| `backend/src/qts/backtest/instrument_context.py` | `qts.backtest.instrument_context` | 10 |
| `backend/src/qts/backtest/intent_processor.py` | `qts.backtest.intent_processor` | 6 |
| `backend/src/qts/backtest/portfolio_projection.py` | `qts.backtest.portfolio_projection` | 5 |
| `backend/src/qts/backtest/report.py` | `qts.backtest.report` | 20 |
| `backend/src/qts/backtest/runner.py` | `qts.backtest.runner` | 9 |
| `backend/src/qts/backtest/sinks.py` | `qts.backtest.sinks` | 8 |
| `backend/src/qts/config/__init__.py` | `qts.config` | 0 |
| `backend/src/qts/config/ibkr.py` | `qts.config.ibkr` | 16 |
| `backend/src/qts/core/__init__.py` | `qts.core` | 0 |
| `backend/src/qts/core/hashing.py` | `qts.core.hashing` | 3 |
| `backend/src/qts/core/ids.py` | `qts.core.ids` | 12 |
| `backend/src/qts/core/time.py` | `qts.core.time` | 6 |
| `backend/src/qts/data/__init__.py` | `qts.data` | 0 |
| `backend/src/qts/data/adapters/__init__.py` | `qts.data.adapters` | 0 |
| `backend/src/qts/data/adapters/ibkr_market_data.py` | `qts.data.adapters.ibkr_market_data` | 9 |
| `backend/src/qts/data/bars/__init__.py` | `qts.data.bars` | 0 |
| `backend/src/qts/data/bars/aggregator.py` | `qts.data.bars.aggregator` | 15 |
| `backend/src/qts/data/bars/alignment.py` | `qts.data.bars.alignment` | 2 |
| `backend/src/qts/data/bars/pipeline.py` | `qts.data.bars.pipeline` | 7 |
| `backend/src/qts/data/bars/timeframe.py` | `qts.data.bars.timeframe` | 4 |
| `backend/src/qts/data/feeds/__init__.py` | `qts.data.feeds` | 0 |
| `backend/src/qts/data/feeds/replay_feed.py` | `qts.data.feeds.replay_feed` | 3 |
| `backend/src/qts/data/historical/__init__.py` | `qts.data.historical` | 0 |
| `backend/src/qts/data/historical/catalog.py` | `qts.data.historical.catalog` | 14 |
| `backend/src/qts/data/historical/chains.py` | `qts.data.historical.chains` | 11 |
| `backend/src/qts/data/historical/config.py` | `qts.data.historical.config` | 27 |
| `backend/src/qts/data/historical/config_loader.py` | `qts.data.historical.config_loader` | 9 |
| `backend/src/qts/data/historical/csv_dataset.py` | `qts.data.historical.csv_dataset` | 21 |
| `backend/src/qts/data/historical/csv_format.py` | `qts.data.historical.csv_format` | 9 |
| `backend/src/qts/data/historical/csv_row_mapper.py` | `qts.data.historical.csv_row_mapper` | 5 |
| `backend/src/qts/data/historical/service.py` | `qts.data.historical.service` | 5 |
| `backend/src/qts/data/historical/symbols.py` | `qts.data.historical.symbols` | 4 |
| `backend/src/qts/data/historical/validation.py` | `qts.data.historical.validation` | 7 |
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
| `backend/src/qts/domain/orders/value_objects.py` | `qts.domain.orders.value_objects` | 14 |
| `backend/src/qts/domain/portfolio/__init__.py` | `qts.domain.portfolio` | 0 |
| `backend/src/qts/domain/risk/__init__.py` | `qts.domain.risk` | 0 |
| `backend/src/qts/domain/risk/decision.py` | `qts.domain.risk.decision` | 6 |
| `backend/src/qts/domain/risk/request.py` | `qts.domain.risk.request` | 3 |
| `backend/src/qts/execution/__init__.py` | `qts.execution` | 0 |
| `backend/src/qts/execution/adapters/__init__.py` | `qts.execution.adapters` | 0 |
| `backend/src/qts/execution/adapters/ibkr_order_execution.py` | `qts.execution.adapters.ibkr_order_execution` | 8 |
| `backend/src/qts/execution/broker.py` | `qts.execution.broker` | 25 |
| `backend/src/qts/execution/idempotency.py` | `qts.execution.idempotency` | 6 |
| `backend/src/qts/execution/order_manager.py` | `qts.execution.order_manager` | 14 |
| `backend/src/qts/execution/order_state_machine.py` | `qts.execution.order_state_machine` | 4 |
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
| `backend/src/qts/quality/__init__.py` | `qts.quality` | 0 |
| `backend/src/qts/quality/guardrails.py` | `qts.quality.guardrails` | 52 |
| `backend/src/qts/reconciliation.py` | `qts.reconciliation` | 28 |
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
| `backend/src/qts/runtime/actors/market_data_actor.py` | `qts.runtime.actors.market_data_actor` | 13 |
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
| `backend/src/qts/strategy_sdk/asset_resolver.py` | `qts.strategy_sdk.asset_resolver` | 15 |
| `backend/src/qts/strategy_sdk/context.py` | `qts.strategy_sdk.context` | 13 |
| `backend/src/qts/strategy_sdk/data_view.py` | `qts.strategy_sdk.data_view` | 4 |
| `backend/src/qts/strategy_sdk/factors.py` | `qts.strategy_sdk.factors` | 2 |
| `backend/src/qts/strategy_sdk/indicators.py` | `qts.strategy_sdk.indicators` | 7 |
| `backend/src/qts/strategy_sdk/portfolio_view.py` | `qts.strategy_sdk.portfolio_view` | 6 |
| `backend/src/qts/strategy_sdk/strategy.py` | `qts.strategy_sdk.strategy` | 8 |
| `backend/src/qts/strategy_sdk/subscription_registry.py` | `qts.strategy_sdk.subscription_registry` | 6 |
| `backend/src/qts/strategy_sdk/target.py` | `qts.strategy_sdk.target` | 2 |
| `backend/src/qts/strategy_sdk/target_emitter.py` | `qts.strategy_sdk.target_emitter` | 4 |
| `backend/src/qts/workers/__init__.py` | `qts.workers` | 0 |
| `examples/__init__.py` | `examples` | 0 |
| `examples/strategies/__init__.py` | `examples.strategies` | 0 |
| `examples/strategies/gc_si_momentum.py` | `examples.strategies.gc_si_momentum` | 6 |
| `examples/strategies/moving_average_cross.py` | `examples.strategies.moving_average_cross` | 3 |
| `scripts/__init__.py` | `scripts` | 0 |
| `scripts/bootstrap.py` | `scripts.bootstrap` | 1 |
| `scripts/ibkr_collect_environment_evidence.py` | `scripts.ibkr_collect_environment_evidence` | 0 |
| `scripts/ibkr_paper_order_lifecycle_drill.py` | `scripts.ibkr_paper_order_lifecycle_drill` | 0 |
| `scripts/run_api.py` | `scripts.run_api` | 1 |
| `scripts/run_backtest.py` | `scripts.run_backtest` | 1 |
| `scripts/run_load.py` | `scripts.run_load` | 1 |
| `scripts/run_paper.py` | `scripts.run_paper` | 1 |
| `scripts/run_paper_ibkr.py` | `scripts.run_paper_ibkr` | 1 |
| `scripts/run_worker.py` | `scripts.run_worker` | 1 |
| `scripts/validate_historical.py` | `scripts.validate_historical` | 1 |
| `scripts/verify_guardrails.py` | `scripts.verify_guardrails` | 1 |

## 全量符号索引

| 文件:行 | 类型 | 符号 | 作用 | 内部调用数 | 原始调用数 |
|---|---|---|---|---:|---:|
| `backend/src/qts/api/app.py:18` | `module_function` | `qts.api.app.create_app` | Perform create_app. | 0 | 8 |
| `backend/src/qts/api/mappers.py:12` | `module_function` | `qts.api.mappers.map_backtest_request_schema` | Map API input schema into an application DTO. | 1 | 1 |
| `backend/src/qts/api/mappers.py:18` | `module_function` | `qts.api.mappers.map_backtest_run_dto` | Map application output DTO into API response schema. | 1 | 1 |
| `backend/src/qts/api/mappers.py:24` | `module_function` | `qts.api.mappers.map_runtime_state_dto` | Map runtime state DTO into response payload. | 0 | 0 |
| `backend/src/qts/api/mappers.py:30` | `module_function` | `qts.api.mappers.map_kill_switch_state_dto` | Map kill-switch state DTO into response payload. | 0 | 0 |
| `backend/src/qts/api/routes/accounts.py:13` | `module_function` | `qts.api.routes.accounts.account_snapshot` | Perform account_snapshot. | 1 | 1 |
| `backend/src/qts/api/routes/backtests.py:19` | `module_function` | `qts.api.routes.backtests.submit_backtest` | Submit a backtest request through the backtest application service. | 2 | 4 |
| `backend/src/qts/api/routes/health.py:13` | `module_function` | `qts.api.routes.health.health` | Perform health. | 0 | 2 |
| `backend/src/qts/api/routes/operations.py:21` | `class` | `qts.api.routes.operations.RuntimeCommandResponse` | Payload for runtime pause/resume commands. | 0 | 0 |
| `backend/src/qts/api/routes/operations.py:27` | `class` | `qts.api.routes.operations.KillSwitchScopeSchema` | Kill-switch scoping model. | 0 | 0 |
| `backend/src/qts/api/routes/operations.py:36` | `class` | `qts.api.routes.operations.KillSwitchCommand` | Kill-switch mutation command. | 0 | 0 |
| `backend/src/qts/api/routes/operations.py:44` | `method` | `qts.api.routes.operations.KillSwitchCommand.validate_scope` | Perform validate_scope. | 0 | 4 |
| `backend/src/qts/api/routes/operations.py:55` | `class` | `qts.api.routes.operations.KillSwitchResponse` | Kill-switch current state response. | 0 | 0 |
| `backend/src/qts/api/routes/operations.py:64` | `module_function` | `qts.api.routes.operations._require_operator` | Perform _require_operator. | 0 | 2 |
| `backend/src/qts/api/routes/operations.py:71` | `module_function` | `qts.api.routes.operations.pause_runtime` | Pause runtime execution for all strategies and data actors. | 4 | 6 |
| `backend/src/qts/api/routes/operations.py:78` | `nested_function` | `qts.api.routes.operations.command` | Perform command. | 2 | 3 |
| `backend/src/qts/api/routes/operations.py:90` | `module_function` | `qts.api.routes.operations.resume_runtime` | Resume runtime execution after an operator pause. | 4 | 6 |
| `backend/src/qts/api/routes/operations.py:97` | `nested_function` | `qts.api.routes.operations.command` | Perform command. | 2 | 3 |
| `backend/src/qts/api/routes/operations.py:109` | `module_function` | `qts.api.routes.operations.activate_kill_switch` | Activate or refresh a kill-switch for a runtime scope. | 3 | 5 |
| `backend/src/qts/api/routes/orders.py:13` | `module_function` | `qts.api.routes.orders.order_status` | Perform order_status. | 1 | 1 |
| `backend/src/qts/api/routes/strategies.py:13` | `module_function` | `qts.api.routes.strategies.list_strategies` | Perform list_strategies. | 1 | 1 |
| `backend/src/qts/api/routes/strategies.py:19` | `module_function` | `qts.api.routes.strategies.start_strategy` | Perform start_strategy. | 1 | 1 |
| `backend/src/qts/api/routes/strategies.py:25` | `module_function` | `qts.api.routes.strategies.stop_strategy` | Perform stop_strategy. | 1 | 1 |
| `backend/src/qts/api/schemas/backtest_schema.py:8` | `class` | `qts.api.schemas.backtest_schema.BacktestRequestSchema` | HTTP request for submitting a backtest. | 0 | 0 |
| `backend/src/qts/api/schemas/backtest_schema.py:14` | `class` | `qts.api.schemas.backtest_schema.BacktestRunSchema` | HTTP response for a submitted backtest. | 0 | 0 |
| `backend/src/qts/api/schemas/common.py:8` | `class` | `qts.api.schemas.common.StrategyStatusSchema` | Strategy status response schema. | 0 | 0 |
| `backend/src/qts/api/schemas/common.py:15` | `class` | `qts.api.schemas.common.AccountSnapshotSchema` | Account snapshot response schema. | 0 | 0 |
| `backend/src/qts/api/schemas/common.py:22` | `class` | `qts.api.schemas.common.OrderStatusSchema` | Order status response schema. | 0 | 0 |
| `backend/src/qts/api/schemas/common.py:29` | `class` | `qts.api.schemas.common.RiskRuleSchema` | Risk rule response schema. | 0 | 0 |
| `backend/src/qts/api/schemas/common.py:36` | `class` | `qts.api.schemas.common.OperationalErrorSchema` | Operational error response schema. | 0 | 0 |
| `backend/src/qts/api/schemas/common.py:44` | `classmethod` | `qts.api.schemas.common.OperationalErrorSchema.from_exception` | Perform from_exception. | 0 | 1 |
| `backend/src/qts/api/services/command_idempotency.py:11` | `class` | `qts.api.services.command_idempotency.CommandIdempotencyStore` | Remember the first result for each command idempotency key. | 0 | 0 |
| `backend/src/qts/api/services/command_idempotency.py:14` | `method` | `qts.api.services.command_idempotency.CommandIdempotencyStore.__init__` | Perform __init__. | 0 | 0 |
| `backend/src/qts/api/services/command_idempotency.py:18` | `method` | `qts.api.services.command_idempotency.CommandIdempotencyStore.run` | Perform run. | 0 | 3 |
| `backend/src/qts/api/websocket/dtos.py:10` | `class` | `qts.api.websocket.dtos.StreamEventDTO` | Public stream event DTO. | 0 | 0 |
| `backend/src/qts/api/websocket/dtos.py:18` | `method` | `qts.api.websocket.dtos.StreamEventDTO.__post_init__` | 未写 docstring；静态推断为所属类上的 `  post init  ` 行为。 | 0 | 2 |
| `backend/src/qts/api/websocket/events.py:11` | `async_module_function` | `qts.api.websocket.events.event_stream` | Perform event_stream. | 0 | 3 |
| `backend/src/qts/api/websocket/fill_adapter.py:11` | `module_function` | `qts.api.websocket.fill_adapter.order_fill_to_stream_dto` | Convert an OrderManager-validated fill into a public stream event DTO. | 1 | 4 |
| `backend/src/qts/api/websocket/manager.py:8` | `class` | `qts.api.websocket.manager.JsonWebSocket` | Minimal WebSocket protocol used by the connection manager. | 0 | 0 |
| `backend/src/qts/api/websocket/manager.py:11` | `async_method` | `qts.api.websocket.manager.JsonWebSocket.accept` | Accept the WebSocket connection. | 0 | 0 |
| `backend/src/qts/api/websocket/manager.py:15` | `async_method` | `qts.api.websocket.manager.JsonWebSocket.send_json` | Send a JSON-serializable payload. | 0 | 0 |
| `backend/src/qts/api/websocket/manager.py:20` | `class` | `qts.api.websocket.manager.WebSocketConnectionManager` | Track WebSocket clients and broadcast JSON payloads. | 0 | 0 |
| `backend/src/qts/api/websocket/manager.py:23` | `method` | `qts.api.websocket.manager.WebSocketConnectionManager.__init__` | 未写 docstring；静态推断为所属类上的 `  init  ` 行为。 | 0 | 0 |
| `backend/src/qts/api/websocket/manager.py:27` | `property` | `qts.api.websocket.manager.WebSocketConnectionManager.count` | Perform count. | 0 | 1 |
| `backend/src/qts/api/websocket/manager.py:31` | `async_method` | `qts.api.websocket.manager.WebSocketConnectionManager.connect` | Perform connect. | 0 | 2 |
| `backend/src/qts/api/websocket/manager.py:36` | `method` | `qts.api.websocket.manager.WebSocketConnectionManager.disconnect` | Perform disconnect. | 0 | 1 |
| `backend/src/qts/api/websocket/manager.py:41` | `async_method` | `qts.api.websocket.manager.WebSocketConnectionManager.broadcast` | Perform broadcast. | 1 | 4 |
| `backend/src/qts/application/commands/ibkr_environment_evidence.py:26` | `module_function` | `qts.application.commands.ibkr_environment_evidence.collect_environment_evidence` | Collect observe-only evidence and return the output path. | 5 | 11 |
| `backend/src/qts/application/commands/ibkr_environment_evidence.py:77` | `module_function` | `qts.application.commands.ibkr_environment_evidence.main` | CLI entrypoint for IBKR environment evidence collection. | 1 | 9 |
| `backend/src/qts/application/commands/ibkr_environment_evidence.py:120` | `module_function` | `qts.application.commands.ibkr_environment_evidence._read_config` | Perform _read_config. | 1 | 2 |
| `backend/src/qts/application/commands/ibkr_environment_evidence.py:130` | `module_function` | `qts.application.commands.ibkr_environment_evidence._summarize_config` | Perform _summarize_config. | 1 | 2 |
| `backend/src/qts/application/commands/ibkr_environment_evidence.py:166` | `module_function` | `qts.application.commands.ibkr_environment_evidence._merge_validation_errors` | Perform _merge_validation_errors. | 1 | 1 |
| `backend/src/qts/application/commands/ibkr_environment_evidence.py:178` | `module_function` | `qts.application.commands.ibkr_environment_evidence._collect_network_evidence` | Perform _collect_network_evidence. | 1 | 2 |
| `backend/src/qts/application/commands/ibkr_environment_evidence.py:222` | `module_function` | `qts.application.commands.ibkr_environment_evidence._tcp_probe` | Perform _tcp_probe. | 0 | 7 |
| `backend/src/qts/application/commands/ibkr_environment_evidence.py:247` | `module_function` | `qts.application.commands.ibkr_environment_evidence._env_ref_status` | Perform _env_ref_status. | 0 | 1 |
| `backend/src/qts/application/commands/ibkr_environment_evidence.py:252` | `module_function` | `qts.application.commands.ibkr_environment_evidence._evidence_filename` | Perform _evidence_filename. | 1 | 2 |
| `backend/src/qts/application/commands/ibkr_environment_evidence.py:259` | `module_function` | `qts.application.commands.ibkr_environment_evidence._safe_label` | Perform _safe_label. | 0 | 3 |
| `backend/src/qts/application/commands/ibkr_paper_order_lifecycle_drill.py:31` | `module_function` | `qts.application.commands.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill` | Run a paper-only order-lifecycle drill and persist evidence. | 14 | 40 |
| `backend/src/qts/application/commands/ibkr_paper_order_lifecycle_drill.py:142` | `module_function` | `qts.application.commands.ibkr_paper_order_lifecycle_drill.main` | CLI entrypoint for paper order lifecycle evidence. | 1 | 14 |
| `backend/src/qts/application/commands/ibkr_paper_order_lifecycle_drill.py:187` | `module_function` | `qts.application.commands.ibkr_paper_order_lifecycle_drill._read_config` | Perform _read_config. | 1 | 2 |
| `backend/src/qts/application/commands/ibkr_paper_order_lifecycle_drill.py:197` | `module_function` | `qts.application.commands.ibkr_paper_order_lifecycle_drill._validate_paper_only_ibkr_config` | Perform _validate_paper_only_ibkr_config. | 1 | 14 |
| `backend/src/qts/application/commands/ibkr_paper_order_lifecycle_drill.py:221` | `module_function` | `qts.application.commands.ibkr_paper_order_lifecycle_drill._summarize_config` | Perform _summarize_config. | 0 | 0 |
| `backend/src/qts/application/commands/ibkr_paper_order_lifecycle_drill.py:237` | `module_function` | `qts.application.commands.ibkr_paper_order_lifecycle_drill._execution_report_evidence` | Perform _execution_report_evidence. | 0 | 4 |
| `backend/src/qts/application/commands/ibkr_paper_order_lifecycle_drill.py:251` | `module_function` | `qts.application.commands.ibkr_paper_order_lifecycle_drill._evidence_filename` | Perform _evidence_filename. | 1 | 2 |
| `backend/src/qts/application/commands/ibkr_paper_order_lifecycle_drill.py:258` | `module_function` | `qts.application.commands.ibkr_paper_order_lifecycle_drill._safe_label` | Perform _safe_label. | 0 | 3 |
| `backend/src/qts/application/commands/start_paper.py:10` | `class` | `qts.application.commands.start_paper.PaperRuntimeConfig` | Paper runtime configuration without real broker credentials. | 0 | 0 |
| `backend/src/qts/application/commands/start_paper.py:18` | `method` | `qts.application.commands.start_paper.PaperRuntimeConfig.__post_init__` | Perform __post_init__. | 0 | 6 |
| `backend/src/qts/application/commands/start_paper.py:29` | `class` | `qts.application.commands.start_paper.PaperRuntime` | Constructed paper runtime descriptor. | 0 | 0 |
| `backend/src/qts/application/commands/start_paper.py:36` | `module_function` | `qts.application.commands.start_paper.start_paper` | Construct the paper runtime boundary without connecting to a real broker. | 1 | 1 |
| `backend/src/qts/application/dto/backtest.py:9` | `class` | `qts.application.dto.backtest.BacktestRequestDTO` | Stable application request for starting a backtest. | 0 | 0 |
| `backend/src/qts/application/dto/backtest.py:14` | `method` | `qts.application.dto.backtest.BacktestRequestDTO.__post_init__` | Perform __post_init__. | 0 | 2 |
| `backend/src/qts/application/dto/backtest.py:21` | `class` | `qts.application.dto.backtest.BacktestRunDTO` | Stable application response for a submitted backtest. | 0 | 0 |
| `backend/src/qts/application/dto/health.py:9` | `class` | `qts.application.dto.health.HealthStatusDTO` | Stable health status response. | 0 | 0 |
| `backend/src/qts/application/dto/operations.py:9` | `class` | `qts.application.dto.operations.RuntimeStateDTO` | Stable runtime state response. | 0 | 0 |
| `backend/src/qts/application/dto/operations.py:16` | `class` | `qts.application.dto.operations.KillSwitchCommandDTO` | Stable kill-switch activation request. | 0 | 0 |
| `backend/src/qts/application/dto/operations.py:23` | `method` | `qts.application.dto.operations.KillSwitchCommandDTO.__post_init__` | Perform __post_init__. | 0 | 6 |
| `backend/src/qts/application/dto/operations.py:34` | `class` | `qts.application.dto.operations.KillSwitchStateDTO` | Stable kill-switch state response. | 0 | 0 |
| `backend/src/qts/application/dto/order_events.py:10` | `class` | `qts.application.dto.order_events.OrderFillDTO` | Stable fill event shape for public streams. | 0 | 0 |
| `backend/src/qts/application/dto/order_events.py:20` | `method` | `qts.application.dto.order_events.OrderFillDTO.__post_init__` | Perform __post_init__. | 0 | 8 |
| `backend/src/qts/application/services/backtest.py:10` | `class` | `qts.application.services.backtest.BacktestService` | Application boundary for backtest use cases. | 0 | 0 |
| `backend/src/qts/application/services/backtest.py:13` | `method` | `qts.application.services.backtest.BacktestService.__init__` | Perform __init__. | 0 | 1 |
| `backend/src/qts/application/services/backtest.py:17` | `method` | `qts.application.services.backtest.BacktestService.submit` | Perform submit. | 0 | 2 |
| `backend/src/qts/application/services/health.py:8` | `class` | `qts.application.services.health.HealthService` | Returns platform health without exposing internals. | 0 | 0 |
| `backend/src/qts/application/services/health.py:11` | `method` | `qts.application.services.health.HealthService.status` | Perform status. | 0 | 1 |
| `backend/src/qts/application/services/interfaces.py:8` | `class` | `qts.application.services.interfaces.AccountService` | Account query service boundary. | 0 | 0 |
| `backend/src/qts/application/services/interfaces.py:11` | `method` | `qts.application.services.interfaces.AccountService.snapshot` | Return an account snapshot. | 0 | 0 |
| `backend/src/qts/application/services/interfaces.py:16` | `class` | `qts.application.services.interfaces.OrderService` | Order query service boundary. | 0 | 0 |
| `backend/src/qts/application/services/interfaces.py:19` | `method` | `qts.application.services.interfaces.OrderService.status` | Return order status. | 0 | 0 |
| `backend/src/qts/application/services/interfaces.py:24` | `class` | `qts.application.services.interfaces.RiskService` | Risk query service boundary. | 0 | 0 |
| `backend/src/qts/application/services/interfaces.py:27` | `method` | `qts.application.services.interfaces.RiskService.rules` | Return configured risk rules. | 0 | 0 |
| `backend/src/qts/application/services/operations.py:9` | `class` | `qts.application.services.operations.OperationsService` | Owns operational state without leaking runtime internals into API routes. | 0 | 0 |
| `backend/src/qts/application/services/operations.py:12` | `method` | `qts.application.services.operations.OperationsService.__init__` | Perform __init__. | 1 | 1 |
| `backend/src/qts/application/services/operations.py:17` | `method` | `qts.application.services.operations.OperationsService.pause_runtime` | Perform pause_runtime. | 0 | 1 |
| `backend/src/qts/application/services/operations.py:22` | `method` | `qts.application.services.operations.OperationsService.resume_runtime` | Perform resume_runtime. | 0 | 1 |
| `backend/src/qts/application/services/operations.py:27` | `method` | `qts.application.services.operations.OperationsService.activate_kill_switch` | Perform activate_kill_switch. | 1 | 3 |
| `backend/src/qts/application/services/operations.py:39` | `staticmethod` | `qts.application.services.operations.OperationsService._scope_from_command` | Perform _scope_from_command. | 3 | 3 |
| `backend/src/qts/application/services/strategy_service.py:9` | `class` | `qts.application.services.strategy_service.StrategyLifecycleService` | Start, stop, and inspect configured strategy instances. | 0 | 0 |
| `backend/src/qts/application/services/strategy_service.py:12` | `method` | `qts.application.services.strategy_service.StrategyLifecycleService.__init__` | Perform __init__. | 0 | 0 |
| `backend/src/qts/application/services/strategy_service.py:21` | `method` | `qts.application.services.strategy_service.StrategyLifecycleService.add` | Perform add. | 0 | 1 |
| `backend/src/qts/application/services/strategy_service.py:29` | `method` | `qts.application.services.strategy_service.StrategyLifecycleService.start` | Perform start. | 1 | 1 |
| `backend/src/qts/application/services/strategy_service.py:35` | `method` | `qts.application.services.strategy_service.StrategyLifecycleService.stop` | Perform stop. | 1 | 1 |
| `backend/src/qts/application/services/strategy_service.py:41` | `method` | `qts.application.services.strategy_service.StrategyLifecycleService.status` | Perform status. | 1 | 1 |
| `backend/src/qts/application/services/strategy_service.py:46` | `method` | `qts.application.services.strategy_service.StrategyLifecycleService.list_instances` | Perform list_instances. | 0 | 2 |
| `backend/src/qts/application/services/strategy_service.py:50` | `method` | `qts.application.services.strategy_service.StrategyLifecycleService._require_enabled` | Perform _require_enabled. | 0 | 1 |
| `backend/src/qts/application/strategy_lifecycle.py:14` | `class` | `qts.application.strategy_lifecycle.StrategyStatus` | Configured strategy instance lifecycle status. | 0 | 0 |
| `backend/src/qts/application/strategy_lifecycle.py:22` | `class` | `qts.application.strategy_lifecycle.StrategyInstance` | Configured runtime instance of a Strategy class. | 0 | 0 |
| `backend/src/qts/application/strategy_lifecycle.py:32` | `method` | `qts.application.strategy_lifecycle.StrategyInstance.__post_init__` | Perform __post_init__. | 0 | 4 |
| `backend/src/qts/application/strategy_lifecycle.py:40` | `class` | `qts.application.strategy_lifecycle.StrategyRegistry` | Safe registry for explicitly approved strategy classes. | 0 | 0 |
| `backend/src/qts/application/strategy_lifecycle.py:43` | `method` | `qts.application.strategy_lifecycle.StrategyRegistry.__init__` | Perform __init__. | 0 | 0 |
| `backend/src/qts/application/strategy_lifecycle.py:47` | `method` | `qts.application.strategy_lifecycle.StrategyRegistry.register` | Perform register. | 0 | 3 |
| `backend/src/qts/application/strategy_lifecycle.py:55` | `method` | `qts.application.strategy_lifecycle.StrategyRegistry.resolve` | Perform resolve. | 0 | 1 |
| `backend/src/qts/backtest/actor_loop.py:44` | `class` | `qts.backtest.actor_loop.BacktestActorLoopResult` | Result summary produced by an actor loop run. | 0 | 0 |
| `backend/src/qts/backtest/actor_loop.py:53` | `property` | `qts.backtest.actor_loop.BacktestActorLoopResult.processed_bars` | Perform processed_bars. | 0 | 0 |
| `backend/src/qts/backtest/actor_loop.py:58` | `class` | `qts.backtest.actor_loop.BacktestActorLoop` | Run backtest bars through strategy/order execution actors. | 0 | 0 |
| `backend/src/qts/backtest/actor_loop.py:61` | `method` | `qts.backtest.actor_loop.BacktestActorLoop.__init__` | Perform __init__. | 0 | 2 |
| `backend/src/qts/backtest/actor_loop.py:96` | `staticmethod` | `qts.backtest.actor_loop.BacktestActorLoop._take_strategy_bar_result` | Perform _take_strategy_bar_result. | 0 | 8 |
| `backend/src/qts/backtest/actor_loop.py:108` | `staticmethod` | `qts.backtest.actor_loop.BacktestActorLoop._take_signal_batch` | Perform _take_signal_batch. | 0 | 8 |
| `backend/src/qts/backtest/actor_loop.py:120` | `staticmethod` | `qts.backtest.actor_loop.BacktestActorLoop._take_strategy_finalized` | Perform _take_strategy_finalized. | 0 | 8 |
| `backend/src/qts/backtest/actor_loop.py:131` | `method` | `qts.backtest.actor_loop.BacktestActorLoop._market_data_ref_for` | Perform _market_data_ref_for. | 3 | 5 |
| `backend/src/qts/backtest/actor_loop.py:165` | `staticmethod` | `qts.backtest.actor_loop.BacktestActorLoop._history_limit_from_subscriptions` | Perform _history_limit_from_subscriptions. | 0 | 1 |
| `backend/src/qts/backtest/actor_loop.py:172` | `staticmethod` | `qts.backtest.actor_loop.BacktestActorLoop._resolve_actor_classes` | Perform _resolve_actor_classes. | 0 | 0 |
| `backend/src/qts/backtest/actor_loop.py:180` | `method` | `qts.backtest.actor_loop.BacktestActorLoop.run` | Perform run. | 17 | 66 |
| `backend/src/qts/backtest/config.py:20` | `class` | `qts.backtest.config.CostModelConfig` | Explicit backtest cost model settings. | 0 | 0 |
| `backend/src/qts/backtest/config.py:26` | `method` | `qts.backtest.config.CostModelConfig.__post_init__` | Perform __post_init__. | 0 | 10 |
| `backend/src/qts/backtest/config.py:39` | `method` | `qts.backtest.config.CostModelConfig.to_payload` | Perform to_payload. | 0 | 2 |
| `backend/src/qts/backtest/config.py:48` | `class` | `qts.backtest.config.RiskConfig` | Backtest risk settings. | 0 | 0 |
| `backend/src/qts/backtest/config.py:53` | `method` | `qts.backtest.config.RiskConfig.__post_init__` | Perform __post_init__. | 0 | 5 |
| `backend/src/qts/backtest/config.py:59` | `method` | `qts.backtest.config.RiskConfig.to_payload` | Perform to_payload. | 0 | 1 |
| `backend/src/qts/backtest/config.py:65` | `class` | `qts.backtest.config.RollPolicyConfig` | Continuous futures roll policy for config-driven backtest runs. | 0 | 0 |
| `backend/src/qts/backtest/config.py:71` | `method` | `qts.backtest.config.RollPolicyConfig.__post_init__` | Perform __post_init__. | 0 | 4 |
| `backend/src/qts/backtest/config.py:78` | `method` | `qts.backtest.config.RollPolicyConfig.to_payload` | Perform to_payload. | 0 | 0 |
| `backend/src/qts/backtest/config.py:84` | `class` | `qts.backtest.config.BacktestMarketDataReference` | Market data source reference for one backtest run. | 0 | 0 |
| `backend/src/qts/backtest/config.py:91` | `method` | `qts.backtest.config.BacktestMarketDataReference.__post_init__` | Perform __post_init__. | 0 | 11 |
| `backend/src/qts/backtest/config.py:110` | `property` | `qts.backtest.config.BacktestMarketDataReference.is_configured` | Perform is_configured. | 0 | 0 |
| `backend/src/qts/backtest/config.py:114` | `method` | `qts.backtest.config.BacktestMarketDataReference.to_payload` | Perform to_payload. | 0 | 2 |
| `backend/src/qts/backtest/config.py:127` | `class` | `qts.backtest.config.BacktestStrategyConfig` | Configured strategy instance referenced by a backtest run. | 0 | 0 |
| `backend/src/qts/backtest/config.py:137` | `method` | `qts.backtest.config.BacktestStrategyConfig.__post_init__` | Perform __post_init__. | 0 | 13 |
| `backend/src/qts/backtest/config.py:151` | `classmethod` | `qts.backtest.config.BacktestStrategyConfig.from_yaml` | Perform from_yaml. | 1 | 5 |
| `backend/src/qts/backtest/config.py:158` | `method` | `qts.backtest.config.BacktestStrategyConfig.to_payload` | Perform to_payload. | 0 | 1 |
| `backend/src/qts/backtest/config.py:170` | `classmethod` | `qts.backtest.config.BacktestStrategyConfig._parse_payload` | Perform _parse_payload. | 0 | 14 |
| `backend/src/qts/backtest/config.py:190` | `class` | `qts.backtest.config.BacktestRunConfig` | Complete identity for a backtest run. | 0 | 0 |
| `backend/src/qts/backtest/config.py:214` | `method` | `qts.backtest.config.BacktestRunConfig.__post_init__` | Perform __post_init__. | 4 | 50 |
| `backend/src/qts/backtest/config.py:280` | `classmethod` | `qts.backtest.config.BacktestRunConfig.from_yaml` | Perform from_yaml. | 0 | 1 |
| `backend/src/qts/backtest/config.py:287` | `property` | `qts.backtest.config.BacktestRunConfig.config_hash` | Perform config_hash. | 2 | 2 |
| `backend/src/qts/backtest/config.py:291` | `method` | `qts.backtest.config.BacktestRunConfig.to_payload` | Perform to_payload. | 0 | 14 |
| `backend/src/qts/backtest/config.py:323` | `staticmethod` | `qts.backtest.config.BacktestRunConfig._normalize_symbol` | Perform _normalize_symbol. | 0 | 3 |
| `backend/src/qts/backtest/config_loader.py:24` | `class` | `qts.backtest.config_loader.BacktestConfigLoader` | Load backtest configuration from YAML or payload dictionaries. | 0 | 0 |
| `backend/src/qts/backtest/config_loader.py:28` | `classmethod` | `qts.backtest.config_loader.BacktestConfigLoader.from_path` | Perform from_path. | 1 | 5 |
| `backend/src/qts/backtest/config_loader.py:36` | `classmethod` | `qts.backtest.config_loader.BacktestConfigLoader.from_payload` | Perform from_payload. | 8 | 61 |
| `backend/src/qts/backtest/config_loader.py:112` | `staticmethod` | `qts.backtest.config_loader.BacktestConfigLoader._parse_datetime` | Perform _parse_datetime. | 0 | 5 |
| `backend/src/qts/backtest/config_loader.py:123` | `staticmethod` | `qts.backtest.config_loader.BacktestConfigLoader._parse_market_data_reference` | Perform _parse_market_data_reference. | 1 | 9 |
| `backend/src/qts/backtest/engine.py:52` | `class` | `qts.backtest.engine.BacktestCostModel` | Explicit simulation cost assumptions included in reports. | 0 | 0 |
| `backend/src/qts/backtest/engine.py:59` | `method` | `qts.backtest.engine.BacktestCostModel.__post_init__` | Perform __post_init__. | 0 | 6 |
| `backend/src/qts/backtest/engine.py:68` | `method` | `qts.backtest.engine.BacktestCostModel.to_payload` | Perform to_payload. | 0 | 2 |
| `backend/src/qts/backtest/engine.py:77` | `property` | `qts.backtest.engine.BacktestCostModel.slippage_model` | Perform slippage_model. | 0 | 1 |
| `backend/src/qts/backtest/engine.py:82` | `property` | `qts.backtest.engine.BacktestCostModel.commission_model` | Perform commission_model. | 0 | 1 |
| `backend/src/qts/backtest/engine.py:90` | `class` | `qts.backtest.engine.BacktestStreamResult` | Backtest result written to partitioned streaming artifacts. | 0 | 0 |
| `backend/src/qts/backtest/engine.py:109` | `class` | `qts.backtest.engine.BacktestEngine` | Single-process backtest engine using the Strategy SDK and actor order flow. | 0 | 0 |
| `backend/src/qts/backtest/engine.py:112` | `method` | `qts.backtest.engine.BacktestEngine.__init__` | Perform __init__. | 6 | 14 |
| `backend/src/qts/backtest/engine.py:167` | `classmethod` | `qts.backtest.engine.BacktestEngine.from_config` | Perform from_config. | 3 | 5 |
| `backend/src/qts/backtest/engine.py:202` | `method` | `qts.backtest.engine.BacktestEngine.run_streaming` | Perform run_streaming. | 10 | 16 |
| `backend/src/qts/backtest/engine.py:267` | `staticmethod` | `qts.backtest.engine.BacktestEngine._dataset_payload` | Perform _dataset_payload. | 0 | 1 |
| `backend/src/qts/backtest/engine.py:282` | `staticmethod` | `qts.backtest.engine.BacktestEngine._zero_time` | Perform _zero_time. | 0 | 1 |
| `backend/src/qts/backtest/engine.py:289` | `class` | `qts.backtest.engine._BacktestExecutionAdapter` | _BacktestExecutionAdapter. | 0 | 0 |
| `backend/src/qts/backtest/engine.py:291` | `method` | `qts.backtest.engine._BacktestExecutionAdapter.__init__` | Perform __init__. | 0 | 0 |
| `backend/src/qts/backtest/engine.py:295` | `method` | `qts.backtest.engine._BacktestExecutionAdapter.execute_market_order` | Perform execute_market_order. | 0 | 5 |
| `backend/src/qts/backtest/historical_data_portal.py:13` | `class` | `qts.backtest.historical_data_portal.HistoricalDataPortal` | Returns finalized bars visible as of a replay timestamp. | 0 | 0 |
| `backend/src/qts/backtest/historical_data_portal.py:16` | `method` | `qts.backtest.historical_data_portal.HistoricalDataPortal.__init__` | Perform __init__. | 0 | 3 |
| `backend/src/qts/backtest/historical_data_portal.py:23` | `method` | `qts.backtest.historical_data_portal.HistoricalDataPortal.data_view` | Perform data_view. | 0 | 1 |
| `backend/src/qts/backtest/historical_data_portal.py:27` | `method` | `qts.backtest.historical_data_portal.HistoricalDataPortal.history` | Perform history. | 1 | 2 |
| `backend/src/qts/backtest/inputs.py:22` | `class` | `qts.backtest.inputs.BacktestInputBundle` | Streaming inputs and side-channel metadata required by a backtest run. | 0 | 0 |
| `backend/src/qts/backtest/inputs.py:34` | `class` | `qts.backtest.inputs.BacktestInputBuilder` | Build replay-ready market data, registry, and provenance inputs. | 0 | 0 |
| `backend/src/qts/backtest/inputs.py:37` | `method` | `qts.backtest.inputs.BacktestInputBuilder.__init__` | Perform __init__. | 0 | 0 |
| `backend/src/qts/backtest/inputs.py:42` | `method` | `qts.backtest.inputs.BacktestInputBuilder.build` | Perform build. | 6 | 6 |
| `backend/src/qts/backtest/inputs.py:62` | `method` | `qts.backtest.inputs.BacktestInputBuilder._roll_registry` | Perform _roll_registry. | 1 | 2 |
| `backend/src/qts/backtest/inputs.py:68` | `method` | `qts.backtest.inputs.BacktestInputBuilder._stream_configured_bars` | Perform _stream_configured_bars. | 5 | 16 |
| `backend/src/qts/backtest/inputs.py:135` | `method` | `qts.backtest.inputs.BacktestInputBuilder._iter_root_bars` | Perform _iter_root_bars. | 1 | 7 |
| `backend/src/qts/backtest/inputs.py:175` | `staticmethod` | `qts.backtest.inputs.BacktestInputBuilder._merge_ordered_bar_streams` | Perform _merge_ordered_bar_streams. | 0 | 5 |
| `backend/src/qts/backtest/inputs.py:199` | `staticmethod` | `qts.backtest.inputs.BacktestInputBuilder._record_exchange_timezone` | Perform _record_exchange_timezone. | 0 | 1 |
| `backend/src/qts/backtest/inputs.py:210` | `staticmethod` | `qts.backtest.inputs.BacktestInputBuilder._exchange_timezone_for` | Perform _exchange_timezone_for. | 0 | 0 |
| `backend/src/qts/backtest/inputs.py:218` | `method` | `qts.backtest.inputs.BacktestInputBuilder._instrument_registry_for` | Perform _instrument_registry_for. | 2 | 14 |
| `backend/src/qts/backtest/inputs.py:273` | `staticmethod` | `qts.backtest.inputs.BacktestInputBuilder._instrument_for` | Perform _instrument_for. | 0 | 3 |
| `backend/src/qts/backtest/inputs.py:298` | `method` | `qts.backtest.inputs.BacktestInputBuilder._dataset_metadata` | Perform _dataset_metadata. | 2 | 6 |
| `backend/src/qts/backtest/inputs.py:322` | `staticmethod` | `qts.backtest.inputs.BacktestInputBuilder._dataset_instrument_id` | Perform _dataset_instrument_id. | 1 | 2 |
| `backend/src/qts/backtest/inputs.py:328` | `method` | `qts.backtest.inputs.BacktestInputBuilder._contract_multipliers_for` | Perform _contract_multipliers_for. | 0 | 1 |
| `backend/src/qts/backtest/instrument_context.py:16` | `class` | `qts.backtest.instrument_context.BacktestInstrumentContext` | Resolve backtest instrument IDs, roll targets, and instrument metadata. | 0 | 0 |
| `backend/src/qts/backtest/instrument_context.py:19` | `method` | `qts.backtest.instrument_context.BacktestInstrumentContext.__init__` | Perform __init__. | 0 | 2 |
| `backend/src/qts/backtest/instrument_context.py:34` | `method` | `qts.backtest.instrument_context.BacktestInstrumentContext.instrument_registry` | Perform instrument_registry. | 3 | 13 |
| `backend/src/qts/backtest/instrument_context.py:68` | `method` | `qts.backtest.instrument_context.BacktestInstrumentContext.order_instrument_for_intent` | Perform order_instrument_for_intent. | 1 | 3 |
| `backend/src/qts/backtest/instrument_context.py:79` | `method` | `qts.backtest.instrument_context.BacktestInstrumentContext.market_price_for_intent` | Perform market_price_for_intent. | 1 | 3 |
| `backend/src/qts/backtest/instrument_context.py:97` | `method` | `qts.backtest.instrument_context.BacktestInstrumentContext.update_rolling_prices` | Perform update_rolling_prices. | 1 | 3 |
| `backend/src/qts/backtest/instrument_context.py:118` | `method` | `qts.backtest.instrument_context.BacktestInstrumentContext.related_contracts_for` | Perform related_contracts_for. | 1 | 6 |
| `backend/src/qts/backtest/instrument_context.py:136` | `method` | `qts.backtest.instrument_context.BacktestInstrumentContext.is_continuous` | Perform is_continuous. | 0 | 1 |
| `backend/src/qts/backtest/instrument_context.py:143` | `staticmethod` | `qts.backtest.instrument_context.BacktestInstrumentContext._symbol_for` | Perform _symbol_for. | 0 | 1 |
| `backend/src/qts/backtest/instrument_context.py:148` | `staticmethod` | `qts.backtest.instrument_context.BacktestInstrumentContext._exchange_for` | Perform _exchange_for. | 0 | 2 |
| `backend/src/qts/backtest/intent_processor.py:25` | `class` | `qts.backtest.intent_processor.BacktestProcessedIntent` | Orders and fills generated for a single strategy intent. | 0 | 0 |
| `backend/src/qts/backtest/intent_processor.py:32` | `class` | `qts.backtest.intent_processor.BacktestIntentProcessor` | Translate strategy target intents into validated, executed backtest orders. | 0 | 0 |
| `backend/src/qts/backtest/intent_processor.py:35` | `method` | `qts.backtest.intent_processor.BacktestIntentProcessor.__init__` | Perform __init__. | 0 | 0 |
| `backend/src/qts/backtest/intent_processor.py:47` | `method` | `qts.backtest.intent_processor.BacktestIntentProcessor.process_intent` | Process a single target intent and return produced orders/fills. | 4 | 23 |
| `backend/src/qts/backtest/intent_processor.py:136` | `method` | `qts.backtest.intent_processor.BacktestIntentProcessor._process_order_delta` | Perform _process_order_delta. | 3 | 21 |
| `backend/src/qts/backtest/intent_processor.py:201` | `staticmethod` | `qts.backtest.intent_processor.BacktestIntentProcessor._desired_quantity` | Perform _desired_quantity. | 0 | 4 |
| `backend/src/qts/backtest/portfolio_projection.py:15` | `class` | `qts.backtest.portfolio_projection.BacktestPortfolioProjector` | Compute portfolio state views and equity points for streaming backtests. | 0 | 0 |
| `backend/src/qts/backtest/portfolio_projection.py:18` | `method` | `qts.backtest.portfolio_projection.BacktestPortfolioProjector.__init__` | Perform __init__. | 0 | 1 |
| `backend/src/qts/backtest/portfolio_projection.py:22` | `method` | `qts.backtest.portfolio_projection.BacktestPortfolioProjector.multiplier_for` | Return multiplier used for portfolio valuation and risk checks. | 0 | 2 |
| `backend/src/qts/backtest/portfolio_projection.py:27` | `method` | `qts.backtest.portfolio_projection.BacktestPortfolioProjector.portfolio_view` | Perform portfolio_view. | 1 | 9 |
| `backend/src/qts/backtest/portfolio_projection.py:51` | `method` | `qts.backtest.portfolio_projection.BacktestPortfolioProjector.equity_point` | Perform equity_point. | 2 | 2 |
| `backend/src/qts/backtest/report.py:17` | `class` | `qts.backtest.report.EquityCurvePoint` | One timestamped equity observation. | 0 | 0 |
| `backend/src/qts/backtest/report.py:25` | `class` | `qts.backtest.report.TradeLedgerEntry` | Auditable row for a simulated fill. | 0 | 0 |
| `backend/src/qts/backtest/report.py:39` | `module_function` | `qts.backtest.report._stable_hash` | Perform _stable_hash. | 1 | 1 |
| `backend/src/qts/backtest/report.py:44` | `class` | `qts.backtest.report.StreamingEquityMetrics` | Incremental metrics for a streamed equity curve. | 0 | 0 |
| `backend/src/qts/backtest/report.py:47` | `method` | `qts.backtest.report.StreamingEquityMetrics.__init__` | Perform __init__. | 0 | 1 |
| `backend/src/qts/backtest/report.py:55` | `method` | `qts.backtest.report.StreamingEquityMetrics.update` | Perform update. | 0 | 3 |
| `backend/src/qts/backtest/report.py:72` | `method` | `qts.backtest.report.StreamingEquityMetrics.to_payload` | Perform to_payload. | 0 | 1 |
| `backend/src/qts/backtest/report.py:84` | `class` | `qts.backtest.report.StreamingBacktestArtifacts` | Final paths and row counts for streamed backtest artifacts. | 0 | 0 |
| `backend/src/qts/backtest/report.py:93` | `class` | `qts.backtest.report._NdjsonArtifact` | _NdjsonArtifact. | 0 | 0 |
| `backend/src/qts/backtest/report.py:95` | `method` | `qts.backtest.report._NdjsonArtifact.__init__` | Perform __init__. | 0 | 2 |
| `backend/src/qts/backtest/report.py:102` | `method` | `qts.backtest.report._NdjsonArtifact.write` | Perform write. | 0 | 4 |
| `backend/src/qts/backtest/report.py:117` | `method` | `qts.backtest.report._NdjsonArtifact.close` | Perform close. | 0 | 1 |
| `backend/src/qts/backtest/report.py:122` | `property` | `qts.backtest.report._NdjsonArtifact.content_hash` | Perform content_hash. | 0 | 1 |
| `backend/src/qts/backtest/report.py:127` | `class` | `qts.backtest.report.StreamingBacktestArtifactWriter` | Write large backtest outputs as line-delimited artifacts. | 0 | 0 |
| `backend/src/qts/backtest/report.py:132` | `method` | `qts.backtest.report.StreamingBacktestArtifactWriter.__init__` | Perform __init__. | 2 | 3 |
| `backend/src/qts/backtest/report.py:142` | `method` | `qts.backtest.report.StreamingBacktestArtifactWriter.write_order` | Perform write_order. | 0 | 1 |
| `backend/src/qts/backtest/report.py:146` | `method` | `qts.backtest.report.StreamingBacktestArtifactWriter.write_fill` | Perform write_fill. | 0 | 1 |
| `backend/src/qts/backtest/report.py:150` | `method` | `qts.backtest.report.StreamingBacktestArtifactWriter.write_trade_ledger` | Perform write_trade_ledger. | 0 | 1 |
| `backend/src/qts/backtest/report.py:166` | `method` | `qts.backtest.report.StreamingBacktestArtifactWriter.write_equity_point` | Perform write_equity_point. | 0 | 2 |
| `backend/src/qts/backtest/report.py:171` | `method` | `qts.backtest.report.StreamingBacktestArtifactWriter.finalize` | Perform finalize. | 2 | 14 |
| `backend/src/qts/backtest/runner.py:24` | `class` | `qts.backtest.runner.BacktestRun` | Output of a backtest runner invocation. | 0 | 0 |
| `backend/src/qts/backtest/runner.py:34` | `property` | `qts.backtest.runner.BacktestRun.processed_bars` | Perform processed_bars. | 0 | 0 |
| `backend/src/qts/backtest/runner.py:39` | `property` | `qts.backtest.runner.BacktestRun.report_hash` | Perform report_hash. | 0 | 0 |
| `backend/src/qts/backtest/runner.py:44` | `module_function` | `qts.backtest.runner.run_backtest` | Run a backtest and write partitioned streaming artifacts. | 9 | 14 |
| `backend/src/qts/backtest/runner.py:87` | `module_function` | `qts.backtest.runner._catalog_load_config` | Perform _catalog_load_config. | 2 | 4 |
| `backend/src/qts/backtest/runner.py:109` | `module_function` | `qts.backtest.runner._load_strategy` | Perform _load_strategy. | 2 | 6 |
| `backend/src/qts/backtest/runner.py:121` | `module_function` | `qts.backtest.runner._import_strategy_module` | Load a module that defines the requested strategy class. | 0 | 8 |
| `backend/src/qts/backtest/runner.py:137` | `module_function` | `qts.backtest.runner._strategy_type_from_module` | Extract the strategy class from a strategy module. | 0 | 7 |
| `backend/src/qts/backtest/runner.py:151` | `module_function` | `qts.backtest.runner._streaming_summary_payload` | Perform _streaming_summary_payload. | 0 | 10 |
| `backend/src/qts/backtest/sinks.py:13` | `class` | `qts.backtest.sinks.BacktestStreamingSink` | Write engine stream artifacts through a shared writer. | 0 | 0 |
| `backend/src/qts/backtest/sinks.py:16` | `method` | `qts.backtest.sinks.BacktestStreamingSink.__init__` | Perform __init__. | 0 | 0 |
| `backend/src/qts/backtest/sinks.py:22` | `property` | `qts.backtest.sinks.BacktestStreamingSink.order_count` | Perform order_count. | 0 | 0 |
| `backend/src/qts/backtest/sinks.py:26` | `method` | `qts.backtest.sinks.BacktestStreamingSink.write_processed` | Perform write_processed. | 3 | 7 |
| `backend/src/qts/backtest/sinks.py:42` | `method` | `qts.backtest.sinks.BacktestStreamingSink.write_equity_point` | Perform write_equity_point. | 0 | 1 |
| `backend/src/qts/backtest/sinks.py:47` | `staticmethod` | `qts.backtest.sinks.BacktestStreamingSink._ledger_rows` | Perform _ledger_rows. | 1 | 2 |
| `backend/src/qts/backtest/sinks.py:65` | `staticmethod` | `qts.backtest.sinks.BacktestStreamingSink._order_payload` | Perform _order_payload. | 0 | 1 |
| `backend/src/qts/backtest/sinks.py:77` | `staticmethod` | `qts.backtest.sinks.BacktestStreamingSink._fill_payload` | Perform _fill_payload. | 0 | 4 |
| `backend/src/qts/config/ibkr.py:16` | `class` | `qts.config.ibkr.IbkrConnectionConfig` | IBKR connection settings for one boundary. | 0 | 0 |
| `backend/src/qts/config/ibkr.py:24` | `method` | `qts.config.ibkr.IbkrConnectionConfig.__post_init__` | Perform __post_init__. | 0 | 6 |
| `backend/src/qts/config/ibkr.py:37` | `class` | `qts.config.ibkr.IbkrOrderExecutionConfig` | IBKR order execution settings. | 0 | 0 |
| `backend/src/qts/config/ibkr.py:48` | `method` | `qts.config.ibkr.IbkrOrderExecutionConfig.__post_init__` | Perform __post_init__. | 0 | 10 |
| `backend/src/qts/config/ibkr.py:65` | `class` | `qts.config.ibkr.IbkrSecretRefs` | Environment variable names for IBKR credentials. | 0 | 0 |
| `backend/src/qts/config/ibkr.py:71` | `method` | `qts.config.ibkr.IbkrSecretRefs.__post_init__` | Perform __post_init__. | 0 | 4 |
| `backend/src/qts/config/ibkr.py:80` | `class` | `qts.config.ibkr.IbkrEnvironmentConfig` | IBKR runtime configuration split by external boundary. | 0 | 0 |
| `backend/src/qts/config/ibkr.py:89` | `classmethod` | `qts.config.ibkr.IbkrEnvironmentConfig.from_payload` | Build a typed config from a mapping payload. | 4 | 17 |
| `backend/src/qts/config/ibkr.py:119` | `classmethod` | `qts.config.ibkr.IbkrEnvironmentConfig.from_yaml` | Load and validate environment config from YAML file. | 1 | 5 |
| `backend/src/qts/config/ibkr.py:128` | `module_function` | `qts.config.ibkr.collect_validation_errors` | Return validation errors for config without raising. | 1 | 3 |
| `backend/src/qts/config/ibkr.py:140` | `module_function` | `qts.config.ibkr.validate_ibkr_environment` | Validate paper/live separation without exposing secret values. | 1 | 14 |
| `backend/src/qts/config/ibkr.py:172` | `module_function` | `qts.config.ibkr._as_mapping` | Perform _as_mapping. | 0 | 6 |
| `backend/src/qts/config/ibkr.py:186` | `module_function` | `qts.config.ibkr._read_connection` | Perform _read_connection. | 1 | 11 |
| `backend/src/qts/config/ibkr.py:206` | `module_function` | `qts.config.ibkr._read_order_execution_config` | Perform _read_order_execution_config. | 2 | 7 |
| `backend/src/qts/config/ibkr.py:227` | `module_function` | `qts.config.ibkr._read_secret_refs` | Perform _read_secret_refs. | 1 | 5 |
| `backend/src/qts/config/ibkr.py:235` | `module_function` | `qts.config.ibkr._contains_paper_reference` | Perform _contains_paper_reference. | 0 | 1 |
| `backend/src/qts/core/hashing.py:12` | `module_function` | `qts.core.hashing.stable_json_default` | Adapter used by :func:`stable_json_dumps` for non-native JSON types. | 0 | 8 |
| `backend/src/qts/core/hashing.py:24` | `module_function` | `qts.core.hashing.stable_json_dumps` | Serialize `payload` deterministically for stable hashing. | 0 | 1 |
| `backend/src/qts/core/hashing.py:35` | `module_function` | `qts.core.hashing.stable_json_hash` | Return a stable SHA-256 digest for a payload. | 1 | 4 |
| `backend/src/qts/core/ids.py:9` | `class` | `qts.core.ids._StringId` | Base class for typed string identifiers. | 0 | 0 |
| `backend/src/qts/core/ids.py:14` | `method` | `qts.core.ids._StringId.__post_init__` | Perform __post_init__. | 0 | 4 |
| `backend/src/qts/core/ids.py:22` | `method` | `qts.core.ids._StringId.__str__` | Perform __str__. | 0 | 0 |
| `backend/src/qts/core/ids.py:27` | `class` | `qts.core.ids.AccountId` | Stable internal account identifier. | 0 | 0 |
| `backend/src/qts/core/ids.py:31` | `class` | `qts.core.ids.StrategyId` | Stable internal strategy identifier. | 0 | 0 |
| `backend/src/qts/core/ids.py:35` | `class` | `qts.core.ids.InstrumentId` | Stable internal instrument identifier. | 0 | 0 |
| `backend/src/qts/core/ids.py:39` | `class` | `qts.core.ids.OrderId` | Stable internal order identifier. | 0 | 0 |
| `backend/src/qts/core/ids.py:43` | `class` | `qts.core.ids.BrokerId` | Stable internal broker identifier. | 0 | 0 |
| `backend/src/qts/core/ids.py:47` | `class` | `qts.core.ids.EventId` | Stable internal event identifier. | 0 | 0 |
| `backend/src/qts/core/ids.py:51` | `class` | `qts.core.ids.BacktestRunId` | Stable identifier for a backtest run. | 0 | 0 |
| `backend/src/qts/core/ids.py:55` | `class` | `qts.core.ids.CorrelationId` | Identifier grouping events in one business workflow. | 0 | 0 |
| `backend/src/qts/core/ids.py:59` | `class` | `qts.core.ids.CausationId` | Identifier linking an event to the event that caused it. | 0 | 0 |
| `backend/src/qts/core/time.py:10` | `module_function` | `qts.core.time.require_aware_datetime` | Validate that a datetime has an effective timezone. | 0 | 2 |
| `backend/src/qts/core/time.py:17` | `module_function` | `qts.core.time.to_exchange_time` | Convert a timestamp representation into an exchange timezone. | 1 | 4 |
| `backend/src/qts/core/time.py:28` | `class` | `qts.core.time.TimeInterval` | A half-open time interval with `[start, end)` membership. | 0 | 0 |
| `backend/src/qts/core/time.py:34` | `method` | `qts.core.time.TimeInterval.__post_init__` | Perform __post_init__. | 1 | 3 |
| `backend/src/qts/core/time.py:42` | `property` | `qts.core.time.TimeInterval.duration` | Perform duration. | 0 | 0 |
| `backend/src/qts/core/time.py:46` | `method` | `qts.core.time.TimeInterval.contains` | Perform contains. | 1 | 1 |
| `backend/src/qts/data/adapters/ibkr_market_data.py:15` | `class` | `qts.data.adapters.ibkr_market_data.IbkrMarketDataConnection` | IBKR market data connection settings. | 0 | 0 |
| `backend/src/qts/data/adapters/ibkr_market_data.py:23` | `method` | `qts.data.adapters.ibkr_market_data.IbkrMarketDataConnection.__post_init__` | Perform __post_init__. | 0 | 6 |
| `backend/src/qts/data/adapters/ibkr_market_data.py:36` | `class` | `qts.data.adapters.ibkr_market_data.IbkrMarketDataSubscription` | IBKR market data subscription request at the adapter boundary. | 0 | 0 |
| `backend/src/qts/data/adapters/ibkr_market_data.py:44` | `class` | `qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter` | Normalizes IBKR market data without owning order execution. | 0 | 0 |
| `backend/src/qts/data/adapters/ibkr_market_data.py:47` | `method` | `qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter.__init__` | Perform __init__. | 0 | 0 |
| `backend/src/qts/data/adapters/ibkr_market_data.py:57` | `method` | `qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter.subscription_for` | Perform subscription_for. | 1 | 2 |
| `backend/src/qts/data/adapters/ibkr_market_data.py:65` | `method` | `qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter.normalize_tick` | Perform normalize_tick. | 0 | 2 |
| `backend/src/qts/data/adapters/ibkr_market_data.py:81` | `method` | `qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter.normalize_quote` | Perform normalize_quote. | 0 | 2 |
| `backend/src/qts/data/adapters/ibkr_market_data.py:101` | `method` | `qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter.normalize_bar` | Perform normalize_bar. | 0 | 2 |
| `backend/src/qts/data/bars/aggregator.py:18` | `class` | `qts.data.bars.aggregator.AggregationState` | Current in-progress aggregation bucket. | 0 | 0 |
| `backend/src/qts/data/bars/aggregator.py:27` | `property` | `qts.data.bars.aggregator.AggregationState.aggregate_end` | Perform aggregate_end. | 0 | 0 |
| `backend/src/qts/data/bars/aggregator.py:33` | `class` | `qts.data.bars.aggregator.AggregationResult` | Result returned by one incremental aggregator update. | 0 | 0 |
| `backend/src/qts/data/bars/aggregator.py:40` | `class` | `qts.data.bars.aggregator.BarAggregator` | Stateful incremental bar aggregator for one ordered bar stream. | 0 | 0 |
| `backend/src/qts/data/bars/aggregator.py:43` | `method` | `qts.data.bars.aggregator.BarAggregator.__init__` | Perform __init__. | 0 | 1 |
| `backend/src/qts/data/bars/aggregator.py:58` | `method` | `qts.data.bars.aggregator.BarAggregator.update` | Add a lower-timeframe bar and return any completed aggregate bars. | 6 | 11 |
| `backend/src/qts/data/bars/aggregator.py:87` | `method` | `qts.data.bars.aggregator.BarAggregator.finish` | Flush the current bucket as a partial aggregate when present. | 2 | 3 |
| `backend/src/qts/data/bars/aggregator.py:96` | `method` | `qts.data.bars.aggregator.BarAggregator._new_state_for` | Perform _new_state_for. | 3 | 3 |
| `backend/src/qts/data/bars/aggregator.py:110` | `module_function` | `qts.data.bars.aggregator.aggregate_bars` | Aggregate bars into a higher clock-aligned timeframe. | 1 | 9 |
| `backend/src/qts/data/bars/aggregator.py:139` | `module_function` | `qts.data.bars.aggregator._bar_inside_session` | Perform _bar_inside_session. | 0 | 1 |
| `backend/src/qts/data/bars/aggregator.py:144` | `module_function` | `qts.data.bars.aggregator._same_stream_bucket` | Perform _same_stream_bucket. | 0 | 0 |
| `backend/src/qts/data/bars/aggregator.py:153` | `module_function` | `qts.data.bars.aggregator._aggregate_state` | Perform _aggregate_state. | 3 | 13 |
| `backend/src/qts/data/bars/aggregator.py:194` | `module_function` | `qts.data.bars.aggregator._aggregate_vwap` | Perform _aggregate_vwap. | 0 | 4 |
| `backend/src/qts/data/bars/aggregator.py:204` | `module_function` | `qts.data.bars.aggregator._last_open_interest` | Perform _last_open_interest. | 0 | 1 |
| `backend/src/qts/data/bars/aggregator.py:212` | `module_function` | `qts.data.bars.aggregator._sum_trade_count` | Perform _sum_trade_count. | 0 | 1 |
| `backend/src/qts/data/bars/alignment.py:11` | `module_function` | `qts.data.bars.alignment.clock_bucket_for` | Return the exchange-clock bucket containing ``timestamp``. | 3 | 7 |
| `backend/src/qts/data/bars/alignment.py:36` | `module_function` | `qts.data.bars.alignment._duration_seconds` | Perform _duration_seconds. | 0 | 4 |
| `backend/src/qts/data/bars/pipeline.py:15` | `class` | `qts.data.bars.pipeline.BarAggregationPipeline` | Own incremental aggregation state for bar streams in memory. | 0 | 0 |
| `backend/src/qts/data/bars/pipeline.py:18` | `method` | `qts.data.bars.pipeline.BarAggregationPipeline.__init__` | Perform __init__. | 0 | 0 |
| `backend/src/qts/data/bars/pipeline.py:23` | `method` | `qts.data.bars.pipeline.BarAggregationPipeline.aggregate` | Aggregate one 1+ minute bar into an explicit target timeframe. | 2 | 3 |
| `backend/src/qts/data/bars/pipeline.py:29` | `method` | `qts.data.bars.pipeline.BarAggregationPipeline.aggregate_logical` | Aggregate bars from one source timeframe into a logical subscriber target. | 3 | 4 |
| `backend/src/qts/data/bars/pipeline.py:42` | `method` | `qts.data.bars.pipeline.BarAggregationPipeline._aggregator_for` | Perform _aggregator_for. | 1 | 2 |
| `backend/src/qts/data/bars/pipeline.py:56` | `staticmethod` | `qts.data.bars.pipeline.BarAggregationPipeline._aggregation_key` | Perform _aggregation_key. | 0 | 1 |
| `backend/src/qts/data/bars/pipeline.py:61` | `staticmethod` | `qts.data.bars.pipeline.BarAggregationPipeline._logical_key` | Perform _logical_key. | 0 | 0 |
| `backend/src/qts/data/bars/timeframe.py:10` | `class` | `qts.data.bars.timeframe.AlignmentMode` | How bars for a timeframe align to time. | 0 | 0 |
| `backend/src/qts/data/bars/timeframe.py:29` | `class` | `qts.data.bars.timeframe.Timeframe` | Bar timeframe with explicit alignment semantics. | 0 | 0 |
| `backend/src/qts/data/bars/timeframe.py:37` | `classmethod` | `qts.data.bars.timeframe.Timeframe.parse` | Perform parse. | 0 | 5 |
| `backend/src/qts/data/bars/timeframe.py:50` | `method` | `qts.data.bars.timeframe.Timeframe.__str__` | Perform __str__. | 0 | 0 |
| `backend/src/qts/data/feeds/replay_feed.py:12` | `class` | `qts.data.feeds.replay_feed.ReplayFeed` | Deterministic replay feed over stored bars. | 0 | 0 |
| `backend/src/qts/data/feeds/replay_feed.py:15` | `method` | `qts.data.feeds.replay_feed.ReplayFeed.__init__` | Perform __init__. | 0 | 0 |
| `backend/src/qts/data/feeds/replay_feed.py:19` | `method` | `qts.data.feeds.replay_feed.ReplayFeed.events` | Perform events. | 0 | 1 |
| `backend/src/qts/data/historical/catalog.py:19` | `class` | `qts.data.historical.catalog.HistoricalDataset` | One local historical dataset entry. | 0 | 0 |
| `backend/src/qts/data/historical/catalog.py:34` | `staticmethod` | `qts.data.historical.catalog.HistoricalDataset.normalize_root` | Perform normalize_root. | 0 | 3 |
| `backend/src/qts/data/historical/catalog.py:43` | `class` | `qts.data.historical.catalog.HistoricalCatalog` | Explicit catalog for a local historical data layout. | 0 | 0 |
| `backend/src/qts/data/historical/catalog.py:51` | `classmethod` | `qts.data.historical.catalog.HistoricalCatalog.load` | Load a catalog from one cohesive construction config. | 4 | 6 |
| `backend/src/qts/data/historical/catalog.py:80` | `classmethod` | `qts.data.historical.catalog.HistoricalCatalog.from_legacy_root` | Load requested roots from a local historical data directory. | 6 | 14 |
| `backend/src/qts/data/historical/catalog.py:124` | `classmethod` | `qts.data.historical.catalog.HistoricalCatalog.from_historical_data_config` | Load requested roots from a project-level historical data catalog. | 6 | 17 |
| `backend/src/qts/data/historical/catalog.py:186` | `classmethod` | `qts.data.historical.catalog.HistoricalCatalog._symbol_resolvers_for_load_config` | Perform _symbol_resolvers_for_load_config. | 2 | 2 |
| `backend/src/qts/data/historical/catalog.py:206` | `staticmethod` | `qts.data.historical.catalog.HistoricalCatalog._chain_path_exists` | Perform _chain_path_exists. | 0 | 4 |
| `backend/src/qts/data/historical/catalog.py:223` | `staticmethod` | `qts.data.historical.catalog.HistoricalCatalog._require_file` | Perform _require_file. | 0 | 4 |
| `backend/src/qts/data/historical/catalog.py:234` | `class` | `qts.data.historical.catalog.HistoricalCatalogLoadConfig` | Construction inputs for a configured historical catalog. | 0 | 0 |
| `backend/src/qts/data/historical/catalog.py:244` | `method` | `qts.data.historical.catalog.HistoricalCatalogLoadConfig.__post_init__` | Perform __post_init__. | 3 | 22 |
| `backend/src/qts/data/historical/catalog.py:286` | `classmethod` | `qts.data.historical.catalog.HistoricalCatalogLoadConfig.from_legacy_root` | Perform from_legacy_root. | 0 | 1 |
| `backend/src/qts/data/historical/catalog.py:303` | `classmethod` | `qts.data.historical.catalog.HistoricalCatalogLoadConfig.from_historical_data_config` | Perform from_historical_data_config. | 0 | 1 |
| `backend/src/qts/data/historical/catalog.py:322` | `staticmethod` | `qts.data.historical.catalog.HistoricalCatalogLoadConfig._normalize_symbol` | Perform _normalize_symbol. | 0 | 3 |
| `backend/src/qts/data/historical/chains.py:16` | `class` | `qts.data.historical.chains.HistoricalContract` | One outright contract from a historical chain file. | 0 | 0 |
| `backend/src/qts/data/historical/chains.py:31` | `class` | `qts.data.historical.chains.HistoricalChain` | Parsed historical futures chain. | 0 | 0 |
| `backend/src/qts/data/historical/chains.py:44` | `method` | `qts.data.historical.chains.HistoricalChain.__post_init__` | Perform __post_init__. | 0 | 2 |
| `backend/src/qts/data/historical/chains.py:55` | `method` | `qts.data.historical.chains.HistoricalChain.contract_for_symbol` | Perform contract_for_symbol. | 0 | 1 |
| `backend/src/qts/data/historical/chains.py:62` | `method` | `qts.data.historical.chains.HistoricalChain.is_outright_symbol` | Perform is_outright_symbol. | 0 | 0 |
| `backend/src/qts/data/historical/chains.py:66` | `method` | `qts.data.historical.chains.HistoricalChain.instrument_id_for_symbol` | Perform instrument_id_for_symbol. | 2 | 3 |
| `backend/src/qts/data/historical/chains.py:73` | `classmethod` | `qts.data.historical.chains.HistoricalChain.load` | Load a historical futures chain JSON file into typed metadata. | 4 | 16 |
| `backend/src/qts/data/historical/chains.py:112` | `classmethod` | `qts.data.historical.chains.HistoricalChain._parse_contract` | Perform _parse_contract. | 2 | 13 |
| `backend/src/qts/data/historical/chains.py:143` | `staticmethod` | `qts.data.historical.chains.HistoricalChain._required_text` | Perform _required_text. | 0 | 4 |
| `backend/src/qts/data/historical/chains.py:151` | `staticmethod` | `qts.data.historical.chains.HistoricalChain._required_decimal` | Perform _required_decimal. | 0 | 5 |
| `backend/src/qts/data/historical/chains.py:161` | `staticmethod` | `qts.data.historical.chains.HistoricalChain._exchange_code` | Perform _exchange_code. | 0 | 2 |
| `backend/src/qts/data/historical/config.py:14` | `class` | `qts.data.historical.config.HistoricalDataStoreDefaults` | Default metadata applied to datasets and bars in one historical store. | 0 | 0 |
| `backend/src/qts/data/historical/config.py:22` | `method` | `qts.data.historical.config.HistoricalDataStoreDefaults.__post_init__` | Perform __post_init__. | 0 | 8 |
| `backend/src/qts/data/historical/config.py:35` | `class` | `qts.data.historical.config.HistoricalDataStoreConfig` | Project-level physical layout for a historical data store. | 0 | 0 |
| `backend/src/qts/data/historical/config.py:51` | `method` | `qts.data.historical.config.HistoricalDataStoreConfig.__post_init__` | Perform __post_init__. | 0 | 19 |
| `backend/src/qts/data/historical/config.py:72` | `method` | `qts.data.historical.config.HistoricalDataStoreConfig.bars_path` | Perform bars_path. | 2 | 2 |
| `backend/src/qts/data/historical/config.py:77` | `method` | `qts.data.historical.config.HistoricalDataStoreConfig.chain_path` | Perform chain_path. | 2 | 2 |
| `backend/src/qts/data/historical/config.py:82` | `method` | `qts.data.historical.config.HistoricalDataStoreConfig._join` | Perform _join. | 0 | 1 |
| `backend/src/qts/data/historical/config.py:87` | `staticmethod` | `qts.data.historical.config.HistoricalDataStoreConfig._render_template` | Perform _render_template. | 1 | 3 |
| `backend/src/qts/data/historical/config.py:94` | `class` | `qts.data.historical.config.HistoricalBarFileConfig` | One physical bar file for a dataset. | 0 | 0 |
| `backend/src/qts/data/historical/config.py:104` | `method` | `qts.data.historical.config.HistoricalBarFileConfig.__post_init__` | Perform __post_init__. | 0 | 12 |
| `backend/src/qts/data/historical/config.py:121` | `class` | `qts.data.historical.config.HistoricalDatasetConfig` | One product/data entry inside a historical data catalog. | 0 | 0 |
| `backend/src/qts/data/historical/config.py:134` | `method` | `qts.data.historical.config.HistoricalDatasetConfig.__post_init__` | Perform __post_init__. | 0 | 16 |
| `backend/src/qts/data/historical/config.py:154` | `property` | `qts.data.historical.config.HistoricalDatasetConfig.requires_chain` | Perform requires_chain. | 0 | 2 |
| `backend/src/qts/data/historical/config.py:159` | `staticmethod` | `qts.data.historical.config.HistoricalDatasetConfig.normalize_root` | Perform normalize_root. | 0 | 3 |
| `backend/src/qts/data/historical/config.py:168` | `class` | `qts.data.historical.config.HistoricalDataCatalogConfig` | Logical catalog of historical datasets backed by one store. | 0 | 0 |
| `backend/src/qts/data/historical/config.py:175` | `method` | `qts.data.historical.config.HistoricalDataCatalogConfig.__post_init__` | Perform __post_init__. | 0 | 5 |
| `backend/src/qts/data/historical/config.py:186` | `class` | `qts.data.historical.config.HistoricalDatasetLocation` | Resolved physical file paths for one catalog dataset. | 0 | 0 |
| `backend/src/qts/data/historical/config.py:202` | `class` | `qts.data.historical.config.HistoricalDataConfig` | Project-level historical data stores and catalogs. | 0 | 0 |
| `backend/src/qts/data/historical/config.py:209` | `method` | `qts.data.historical.config.HistoricalDataConfig.__post_init__` | Perform __post_init__. | 0 | 4 |
| `backend/src/qts/data/historical/config.py:220` | `classmethod` | `qts.data.historical.config.HistoricalDataConfig.from_yaml` | Perform from_yaml. | 0 | 1 |
| `backend/src/qts/data/historical/config.py:227` | `classmethod` | `qts.data.historical.config.HistoricalDataConfig.from_payload` | Perform from_payload. | 0 | 3 |
| `backend/src/qts/data/historical/config.py:235` | `method` | `qts.data.historical.config.HistoricalDataConfig.catalog` | Perform catalog. | 0 | 1 |
| `backend/src/qts/data/historical/config.py:242` | `method` | `qts.data.historical.config.HistoricalDataConfig.store` | Perform store. | 0 | 1 |
| `backend/src/qts/data/historical/config.py:249` | `method` | `qts.data.historical.config.HistoricalDataConfig.resolve_dataset` | Perform resolve_dataset. | 6 | 9 |
| `backend/src/qts/data/historical/config.py:296` | `method` | `qts.data.historical.config.HistoricalDataConfig.resolve_chain_path` | Resolve chain metadata path without selecting a concrete bar file. | 3 | 5 |
| `backend/src/qts/data/historical/config.py:312` | `method` | `qts.data.historical.config.HistoricalDataConfig._csv_schema` | Perform _csv_schema. | 0 | 1 |
| `backend/src/qts/data/historical/config.py:322` | `staticmethod` | `qts.data.historical.config.HistoricalDataConfig._select_bar_file` | Perform _select_bar_file. | 3 | 7 |
| `backend/src/qts/data/historical/config_loader.py:31` | `class` | `qts.data.historical.config_loader.HistoricalDataConfigLoader` | Load historical data configuration from files or payload dictionaries. | 0 | 0 |
| `backend/src/qts/data/historical/config_loader.py:35` | `classmethod` | `qts.data.historical.config_loader.HistoricalDataConfigLoader.from_path` | Perform from_path. | 1 | 5 |
| `backend/src/qts/data/historical/config_loader.py:43` | `classmethod` | `qts.data.historical.config_loader.HistoricalDataConfigLoader.from_payload` | Perform from_payload. | 4 | 12 |
| `backend/src/qts/data/historical/config_loader.py:57` | `classmethod` | `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_stores` | Perform _parse_stores. | 2 | 31 |
| `backend/src/qts/data/historical/config_loader.py:95` | `staticmethod` | `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_store_defaults` | Perform _parse_store_defaults. | 1 | 16 |
| `backend/src/qts/data/historical/config_loader.py:127` | `classmethod` | `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_catalogs` | Perform _parse_catalogs. | 2 | 13 |
| `backend/src/qts/data/historical/config_loader.py:148` | `classmethod` | `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_datasets` | Perform _parse_datasets. | 3 | 26 |
| `backend/src/qts/data/historical/config_loader.py:199` | `staticmethod` | `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_bar_files` | Perform _parse_bar_files. | 1 | 19 |
| `backend/src/qts/data/historical/config_loader.py:236` | `staticmethod` | `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_schemas` | Perform _parse_schemas. | 1 | 17 |
| `backend/src/qts/data/historical/csv_dataset.py:42` | `class` | `qts.data.historical.csv_dataset.CsvDatasetDescription` | Cheap metadata description for a historical CSV dataset. | 0 | 0 |
| `backend/src/qts/data/historical/csv_dataset.py:55` | `class` | `qts.data.historical.csv_dataset.HistoricalBarStream` | Lazy iterable over historical bars with side-channel reader stats. | 0 | 0 |
| `backend/src/qts/data/historical/csv_dataset.py:58` | `method` | `qts.data.historical.csv_dataset.HistoricalBarStream.__init__` | 未写 docstring；静态推断为所属类上的 `  init  ` 行为。 | 2 | 2 |
| `backend/src/qts/data/historical/csv_dataset.py:85` | `method` | `qts.data.historical.csv_dataset.HistoricalBarStream.__iter__` | 未写 docstring；静态推断为所属类上的 `  iter  ` 行为。 | 4 | 7 |
| `backend/src/qts/data/historical/csv_dataset.py:99` | `method` | `qts.data.historical.csv_dataset.HistoricalBarStream._iter_all_supported_rows` | 未写 docstring；静态推断为所属类上的 ` iter all supported rows` 行为。 | 3 | 5 |
| `backend/src/qts/data/historical/csv_dataset.py:122` | `method` | `qts.data.historical.csv_dataset.HistoricalBarStream._iter_selected_contract_rows` | 未写 docstring；静态推断为所属类上的 ` iter selected contract rows` 行为。 | 6 | 15 |
| `backend/src/qts/data/historical/csv_dataset.py:183` | `method` | `qts.data.historical.csv_dataset.HistoricalBarStream._iter_session_selected_contract_rows` | 未写 docstring；静态推断为所属类上的 ` iter session selected contract rows` 行为。 | 2 | 8 |
| `backend/src/qts/data/historical/csv_dataset.py:229` | `method` | `qts.data.historical.csv_dataset.HistoricalBarStream._emit_selected_session_rows` | 未写 docstring；静态推断为所属类上的 ` emit selected session rows` 行为。 | 6 | 22 |
| `backend/src/qts/data/historical/csv_dataset.py:316` | `method` | `qts.data.historical.csv_dataset.HistoricalBarStream._timestamp_groups` | 未写 docstring；静态推断为所属类上的 ` timestamp groups` 行为。 | 2 | 4 |
| `backend/src/qts/data/historical/csv_dataset.py:333` | `method` | `qts.data.historical.csv_dataset.HistoricalBarStream._count_excluded_symbol` | 未写 docstring；静态推断为所属类上的 ` count excluded symbol` 行为。 | 1 | 1 |
| `backend/src/qts/data/historical/csv_dataset.py:338` | `method` | `qts.data.historical.csv_dataset.HistoricalBarStream._resolver_root` | 未写 docstring；静态推断为所属类上的 ` resolver root` 行为。 | 1 | 1 |
| `backend/src/qts/data/historical/csv_dataset.py:341` | `method` | `qts.data.historical.csv_dataset.HistoricalBarStream._field` | 未写 docstring；静态推断为所属类上的 ` field` 行为。 | 0 | 1 |
| `backend/src/qts/data/historical/csv_dataset.py:344` | `method` | `qts.data.historical.csv_dataset.HistoricalBarStream._timestamp` | 未写 docstring；静态推断为所属类上的 ` timestamp` 行为。 | 2 | 2 |
| `backend/src/qts/data/historical/csv_dataset.py:348` | `module_function` | `qts.data.historical.csv_dataset.describe_csv_dataset` | Read historical CSV identity metadata without materializing row data. | 2 | 7 |
| `backend/src/qts/data/historical/csv_dataset.py:375` | `module_function` | `qts.data.historical.csv_dataset.iter_historical_bars` | Return a lazy stream of outright historical bars. | 2 | 2 |
| `backend/src/qts/data/historical/csv_dataset.py:402` | `module_function` | `qts.data.historical.csv_dataset.validate_historical_sample` | Validate a bounded sample or full CSV when `sample_rows` is None. | 3 | 3 |
| `backend/src/qts/data/historical/csv_dataset.py:420` | `module_function` | `qts.data.historical.csv_dataset._resolver_root` | 未写 docstring；静态推断为 ` resolver root` 函数，具体语义以实现为准。 | 0 | 3 |
| `backend/src/qts/data/historical/csv_dataset.py:430` | `class` | `qts.data.historical.csv_dataset.RootSymbolResolver` | Protocol for symbol resolvers that provide a root identifier. | 0 | 0 |
| `backend/src/qts/data/historical/csv_dataset.py:434` | `property` | `qts.data.historical.csv_dataset.RootSymbolResolver.root` | Return the root identifier. | 0 | 0 |
| `backend/src/qts/data/historical/csv_dataset.py:439` | `module_function` | `qts.data.historical.csv_dataset._as_symbol_resolver` | 未写 docstring；静态推断为 ` as symbol resolver` 函数，具体语义以实现为准。 | 1 | 2 |
| `backend/src/qts/data/historical/csv_dataset.py:447` | `module_function` | `qts.data.historical.csv_dataset._is_spread_symbol` | 未写 docstring；静态推断为 ` is spread symbol` 函数，具体语义以实现为准。 | 0 | 0 |
| `backend/src/qts/data/historical/csv_format.py:24` | `class` | `qts.data.historical.csv_format.HistoricalCsvSchema` | Mapping from framework OHLCV semantics to concrete CSV columns. | 0 | 0 |
| `backend/src/qts/data/historical/csv_format.py:36` | `method` | `qts.data.historical.csv_format.HistoricalCsvSchema.__post_init__` | Perform __post_init__. | 0 | 5 |
| `backend/src/qts/data/historical/csv_format.py:53` | `property` | `qts.data.historical.csv_format.HistoricalCsvSchema.required_columns` | Perform required_columns. | 0 | 0 |
| `backend/src/qts/data/historical/csv_format.py:65` | `method` | `qts.data.historical.csv_format.HistoricalCsvSchema.validate_columns` | Perform validate_columns. | 0 | 4 |
| `backend/src/qts/data/historical/csv_format.py:73` | `method` | `qts.data.historical.csv_format.HistoricalCsvSchema.resolve_column` | Resolve an OHLCV semantic field name to the configured CSV column. | 0 | 2 |
| `backend/src/qts/data/historical/csv_format.py:96` | `method` | `qts.data.historical.csv_format.HistoricalCsvSchema.column_indices` | Perform column_indices. | 1 | 2 |
| `backend/src/qts/data/historical/csv_format.py:114` | `module_function` | `qts.data.historical.csv_format.validate_historical_csv_columns` | Validate historical CSV columns against the configured schema. | 0 | 4 |
| `backend/src/qts/data/historical/csv_format.py:131` | `module_function` | `qts.data.historical.csv_format.parse_historical_ts_event` | Parse a historical CSV UTC timestamp, accepting nanosecond text input. | 0 | 7 |
| `backend/src/qts/data/historical/csv_format.py:146` | `module_function` | `qts.data.historical.csv_format.historical_timeframe_delta` | Return the duration represented by a supported historical timeframe. | 0 | 11 |
| `backend/src/qts/data/historical/csv_row_mapper.py:21` | `class` | `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper` | Map one validated CSV row to an OHLCV bar. | 0 | 0 |
| `backend/src/qts/data/historical/csv_row_mapper.py:27` | `method` | `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper.to_bar` | Map a mapped row dict into a typed bar. | 4 | 10 |
| `backend/src/qts/data/historical/csv_row_mapper.py:48` | `method` | `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper.extract_ohlcv` | Extract and validate OHLCV fields from a mapped row. | 2 | 6 |
| `backend/src/qts/data/historical/csv_row_mapper.py:61` | `method` | `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper._field` | Perform _field. | 0 | 1 |
| `backend/src/qts/data/historical/csv_row_mapper.py:66` | `staticmethod` | `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper._parse_ohlcv_values` | Perform _parse_ohlcv_values. | 0 | 12 |
| `backend/src/qts/data/historical/service.py:16` | `class` | `qts.data.historical.service.HistoricalMarketDataService` | Deterministic historical market data source with feed-like contracts. | 0 | 0 |
| `backend/src/qts/data/historical/service.py:27` | `method` | `qts.data.historical.service.HistoricalMarketDataService.__post_init__` | Perform __post_init__. | 0 | 4 |
| `backend/src/qts/data/historical/service.py:35` | `property` | `qts.data.historical.service.HistoricalMarketDataService.capabilities` | Perform capabilities. | 1 | 2 |
| `backend/src/qts/data/historical/service.py:45` | `method` | `qts.data.historical.service.HistoricalMarketDataService.subscribe` | Perform subscribe. | 1 | 2 |
| `backend/src/qts/data/historical/service.py:51` | `method` | `qts.data.historical.service.HistoricalMarketDataService.events` | Perform events. | 2 | 5 |
| `backend/src/qts/data/historical/symbols.py:12` | `class` | `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver` | Resolve historical futures outright symbols through chain metadata. | 0 | 0 |
| `backend/src/qts/data/historical/symbols.py:18` | `property` | `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver.root` | Perform root. | 0 | 0 |
| `backend/src/qts/data/historical/symbols.py:22` | `method` | `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver.is_supported_symbol` | Perform is_supported_symbol. | 0 | 1 |
| `backend/src/qts/data/historical/symbols.py:26` | `method` | `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver.instrument_id_for_symbol` | Perform instrument_id_for_symbol. | 0 | 1 |
| `backend/src/qts/data/historical/validation.py:30` | `class` | `qts.data.historical.validation.HistoricalCsvStats` | Streaming counters for historical CSV validation. | 0 | 0 |
| `backend/src/qts/data/historical/validation.py:40` | `method` | `qts.data.historical.validation.HistoricalCsvStats.as_dict` | Perform as_dict. | 0 | 0 |
| `backend/src/qts/data/historical/validation.py:53` | `class` | `qts.data.historical.validation.HistoricalValidationSample` | Validation report plus counters for one sampled historical file. | 0 | 0 |
| `backend/src/qts/data/historical/validation.py:62` | `class` | `qts.data.historical.validation.HistoricalDatasetValidator` | Validate historical sample files and return domain-friendly diagnostics. | 0 | 0 |
| `backend/src/qts/data/historical/validation.py:67` | `method` | `qts.data.historical.validation.HistoricalDatasetValidator.validate_sample` | Perform validate_sample. | 10 | 25 |
| `backend/src/qts/data/historical/validation.py:142` | `module_function` | `qts.data.historical.validation._group_bars` | Perform _group_bars. | 0 | 2 |
| `backend/src/qts/data/historical/validation.py:150` | `module_function` | `qts.data.historical.validation._is_spread_symbol` | Perform _is_spread_symbol. | 0 | 0 |
| `backend/src/qts/data/live_feed.py:17` | `class` | `qts.data.live_feed.FeedCapabilities` | Feed-supported live market data features. | 0 | 0 |
| `backend/src/qts/data/live_feed.py:27` | `method` | `qts.data.live_feed.FeedCapabilities.__post_init__` | 未写 docstring；静态推断为所属类上的 `  post init  ` 行为。 | 0 | 6 |
| `backend/src/qts/data/live_feed.py:35` | `method` | `qts.data.live_feed.FeedCapabilities.supports_timeframe` | Perform supports_timeframe. | 0 | 2 |
| `backend/src/qts/data/live_feed.py:41` | `method` | `qts.data.live_feed.FeedCapabilities.source_timeframe_for` | Return the provider timeframe needed to satisfy a requested bar stream. | 1 | 5 |
| `backend/src/qts/data/live_feed.py:74` | `class` | `qts.data.live_feed.FeedSubscription` | Internal live feed subscription request. | 0 | 0 |
| `backend/src/qts/data/live_feed.py:81` | `method` | `qts.data.live_feed.FeedSubscription.__post_init__` | 未写 docstring；静态推断为所属类上的 `  post init  ` 行为。 | 0 | 4 |
| `backend/src/qts/data/live_feed.py:89` | `class` | `qts.data.live_feed.LiveFeedSubscribed` | Successful live feed subscription acknowledgement. | 0 | 0 |
| `backend/src/qts/data/live_feed.py:97` | `class` | `qts.data.live_feed.LiveFeedEvent` | Live feed payload emitted by a subscription. | 0 | 0 |
| `backend/src/qts/data/live_feed.py:105` | `class` | `qts.data.live_feed.LiveFeedFailure` | Live feed failure notification. | 0 | 0 |
| `backend/src/qts/data/live_feed.py:112` | `method` | `qts.data.live_feed.LiveFeedFailure.__post_init__` | 未写 docstring；静态推断为所属类上的 `  post init  ` 行为。 | 0 | 2 |
| `backend/src/qts/data/live_feed.py:118` | `class` | `qts.data.live_feed.ReconnectPolicy` | Deterministic reconnect backoff policy. | 0 | 0 |
| `backend/src/qts/data/live_feed.py:126` | `method` | `qts.data.live_feed.ReconnectPolicy.__post_init__` | 未写 docstring；静态推断为所属类上的 `  post init  ` 行为。 | 0 | 6 |
| `backend/src/qts/data/live_feed.py:136` | `method` | `qts.data.live_feed.ReconnectPolicy.delay_for_attempt` | Perform delay_for_attempt. | 0 | 5 |
| `backend/src/qts/data/live_feed.py:146` | `class` | `qts.data.live_feed.LiveFeedAdapter` | Live market data feed adapter boundary. | 0 | 0 |
| `backend/src/qts/data/live_feed.py:150` | `property` | `qts.data.live_feed.LiveFeedAdapter.capabilities` | Return feed capabilities. | 0 | 0 |
| `backend/src/qts/data/live_feed.py:154` | `method` | `qts.data.live_feed.LiveFeedAdapter.subscribe` | Subscribe to a live feed stream. | 0 | 0 |
| `backend/src/qts/data/live_feed.py:159` | `class` | `qts.data.live_feed.FakeLiveFeedAdapter` | Deterministic fake live market data feed. | 0 | 0 |
| `backend/src/qts/data/live_feed.py:162` | `method` | `qts.data.live_feed.FakeLiveFeedAdapter.__init__` | 未写 docstring；静态推断为所属类上的 `  init  ` 行为。 | 0 | 3 |
| `backend/src/qts/data/live_feed.py:177` | `property` | `qts.data.live_feed.FakeLiveFeedAdapter.capabilities` | Perform capabilities. | 1 | 1 |
| `backend/src/qts/data/live_feed.py:182` | `property` | `qts.data.live_feed.FakeLiveFeedAdapter.subscription_count` | Perform subscription_count. | 0 | 1 |
| `backend/src/qts/data/live_feed.py:186` | `method` | `qts.data.live_feed.FakeLiveFeedAdapter.subscribe` | Perform subscribe. | 1 | 1 |
| `backend/src/qts/data/live_feed.py:191` | `method` | `qts.data.live_feed.FakeLiveFeedAdapter.emit` | Perform emit. | 1 | 1 |
| `backend/src/qts/data/live_feed.py:195` | `method` | `qts.data.live_feed.FakeLiveFeedAdapter.fail` | Perform fail. | 1 | 2 |
| `backend/src/qts/data/provenance.py:13` | `class` | `qts.data.provenance.DatasetMetadata` | Stable reference to historical data used by simulation or research. | 0 | 0 |
| `backend/src/qts/data/provenance.py:26` | `method` | `qts.data.provenance.DatasetMetadata.__post_init__` | Perform __post_init__. | 2 | 8 |
| `backend/src/qts/data/provenance.py:39` | `property` | `qts.data.provenance.DatasetMetadata.reference` | Perform reference. | 0 | 0 |
| `backend/src/qts/data/provenance.py:45` | `staticmethod` | `qts.data.provenance.DatasetMetadata._require_text` | Perform _require_text. | 0 | 2 |
| `backend/src/qts/data/sessions/filter.py:13` | `class` | `qts.data.sessions.filter.SessionLookup` | Calendar session lookup required by session filters. | 0 | 0 |
| `backend/src/qts/data/sessions/filter.py:16` | `method` | `qts.data.sessions.filter.SessionLookup.session_for` | Return the internal market session for the date. | 0 | 0 |
| `backend/src/qts/data/sessions/filter.py:20` | `module_function` | `qts.data.sessions.filter.filter_session_bars` | Return bars whose start and end fall inside the half-open session. | 1 | 2 |
| `backend/src/qts/data/sessions/filter.py:33` | `module_function` | `qts.data.sessions.filter._bar_inside_session` | Perform _bar_inside_session. | 0 | 1 |
| `backend/src/qts/data/sessions/window.py:12` | `class` | `qts.data.sessions.window.RegularSessionWindow` | A recurring half-open exchange session window. | 0 | 0 |
| `backend/src/qts/data/sessions/window.py:23` | `method` | `qts.data.sessions.window.RegularSessionWindow.__post_init__` | Perform __post_init__. | 0 | 3 |
| `backend/src/qts/data/sessions/window.py:30` | `method` | `qts.data.sessions.window.RegularSessionWindow.session_id_for_timestamp` | Return the exchange-local close-date session id containing timestamp. | 1 | 2 |
| `backend/src/qts/data/sessions/window.py:36` | `method` | `qts.data.sessions.window.RegularSessionWindow.session_date_for_timestamp` | Return the exchange-local close date for timestamp, or None if outside. | 1 | 6 |
| `backend/src/qts/data/sessions/window.py:51` | `method` | `qts.data.sessions.window.RegularSessionWindow.to_payload` | Return a stable JSON-serializable description of the session rule. | 0 | 0 |
| `backend/src/qts/data/stores/base.py:13` | `class` | `qts.data.stores.base.MarketDataStore` | Store and read bars by internal instrument identity. | 0 | 0 |
| `backend/src/qts/data/stores/base.py:16` | `method` | `qts.data.stores.base.MarketDataStore.write_bars` | Persist bars. | 0 | 0 |
| `backend/src/qts/data/stores/base.py:20` | `method` | `qts.data.stores.base.MarketDataStore.read_bars` | Read bars for an interval. | 0 | 0 |
| `backend/src/qts/data/stores/memory_store.py:13` | `class` | `qts.data.stores.memory_store.InMemoryMarketDataStore` | In-memory bar store for tests and local runs. | 0 | 0 |
| `backend/src/qts/data/stores/memory_store.py:16` | `method` | `qts.data.stores.memory_store.InMemoryMarketDataStore.__init__` | Perform __init__. | 0 | 1 |
| `backend/src/qts/data/stores/memory_store.py:20` | `method` | `qts.data.stores.memory_store.InMemoryMarketDataStore.write_bars` | Perform write_bars. | 0 | 2 |
| `backend/src/qts/data/stores/memory_store.py:27` | `method` | `qts.data.stores.memory_store.InMemoryMarketDataStore.read_bars` | Perform read_bars. | 0 | 2 |
| `backend/src/qts/data/stores/parquet_store.py:21` | `class` | `qts.data.stores.parquet_store.ParquetMarketDataStore` | File-backed bar store partitioned by instrument, timeframe, and date. | 0 | 0 |
| `backend/src/qts/data/stores/parquet_store.py:24` | `method` | `qts.data.stores.parquet_store.ParquetMarketDataStore.__init__` | Perform __init__. | 0 | 0 |
| `backend/src/qts/data/stores/parquet_store.py:28` | `method` | `qts.data.stores.parquet_store.ParquetMarketDataStore.write_bars` | Perform write_bars. | 3 | 14 |
| `backend/src/qts/data/stores/parquet_store.py:45` | `method` | `qts.data.stores.parquet_store.ParquetMarketDataStore.read_bars` | Perform read_bars. | 1 | 7 |
| `backend/src/qts/data/stores/parquet_store.py:66` | `method` | `qts.data.stores.parquet_store.ParquetMarketDataStore._path_for` | Perform _path_for. | 0 | 2 |
| `backend/src/qts/data/stores/parquet_store.py:75` | `method` | `qts.data.stores.parquet_store.ParquetMarketDataStore._read_file` | Perform _read_file. | 1 | 5 |
| `backend/src/qts/data/stores/parquet_store.py:81` | `staticmethod` | `qts.data.stores.parquet_store.ParquetMarketDataStore._bar_to_json` | Perform _bar_to_json. | 0 | 9 |
| `backend/src/qts/data/stores/parquet_store.py:102` | `staticmethod` | `qts.data.stores.parquet_store.ParquetMarketDataStore._bar_from_json` | Perform _bar_from_json. | 1 | 26 |
| `backend/src/qts/data/subscriptions.py:12` | `class` | `qts.data.subscriptions.SourceStreamType` | Physical market data stream type. | 0 | 0 |
| `backend/src/qts/data/subscriptions.py:21` | `class` | `qts.data.subscriptions.LogicalSubscription` | Strategy-requested market data stream. | 0 | 0 |
| `backend/src/qts/data/subscriptions.py:29` | `method` | `qts.data.subscriptions.LogicalSubscription.__post_init__` | Perform __post_init__. | 0 | 4 |
| `backend/src/qts/data/subscriptions.py:38` | `class` | `qts.data.subscriptions.LogicalSubscriptionKey` | Deduplication key for strategy-facing subscribers. | 0 | 0 |
| `backend/src/qts/data/subscriptions.py:47` | `class` | `qts.data.subscriptions.PhysicalSubscriptionKey` | Deduplication key for provider-facing subscriptions. | 0 | 0 |
| `backend/src/qts/data/subscriptions.py:55` | `method` | `qts.data.subscriptions.PhysicalSubscriptionKey.__post_init__` | Perform __post_init__. | 0 | 4 |
| `backend/src/qts/data/subscriptions.py:63` | `module_function` | `qts.data.subscriptions.logical_key` | Return the logical fan-out key for a subscription. | 1 | 1 |
| `backend/src/qts/data/subscriptions.py:73` | `module_function` | `qts.data.subscriptions.plan_physical_subscription` | Map one logical subscription to its provider source subscription. | 1 | 3 |
| `backend/src/qts/data/validation_report.py:13` | `class` | `qts.data.validation_report.DataValidationIssueCode` | Known market data validation issue codes. | 0 | 0 |
| `backend/src/qts/data/validation_report.py:27` | `class` | `qts.data.validation_report.DataValidationSeverity` | Severity for data validation issues. | 0 | 0 |
| `backend/src/qts/data/validation_report.py:36` | `class` | `qts.data.validation_report.DataValidationIssue` | One validation issue for a bar sequence. | 0 | 0 |
| `backend/src/qts/data/validation_report.py:45` | `class` | `qts.data.validation_report.DataValidationReport` | Validation result for a bar sequence. | 0 | 0 |
| `backend/src/qts/data/validation_report.py:51` | `property` | `qts.data.validation_report.DataValidationReport.valid` | Perform valid. | 0 | 1 |
| `backend/src/qts/data/validation_report.py:56` | `property` | `qts.data.validation_report.DataValidationReport.max_severity` | Perform max_severity. | 0 | 1 |
| `backend/src/qts/data/validation_report.py:68` | `module_function` | `qts.data.validation_report.validate_bars` | Validate bar ordering, overlap, and optional session containment. | 3 | 27 |
| `backend/src/qts/data/validation_report.py:145` | `module_function` | `qts.data.validation_report._append_ohlc_issue` | Perform _append_ohlc_issue. | 1 | 5 |
| `backend/src/qts/domain/events/event.py:13` | `class` | `qts.domain.events.event.BaseEvent` | Minimal event envelope used for traceable internal messages. | 0 | 0 |
| `backend/src/qts/domain/events/event.py:24` | `method` | `qts.domain.events.event.BaseEvent.__post_init__` | Perform __post_init__. | 1 | 7 |
| `backend/src/qts/domain/events/metadata.py:21` | `class` | `qts.domain.events.metadata.EventMetadata` | Trace metadata carried by platform events. | 0 | 0 |
| `backend/src/qts/domain/events/metadata.py:39` | `method` | `qts.domain.events.metadata.EventMetadata.__post_init__` | Perform __post_init__. | 1 | 7 |
| `backend/src/qts/domain/instruments/contract_spec.py:10` | `class` | `qts.domain.instruments.contract_spec.SettlementType` | How a contract settles. | 0 | 0 |
| `backend/src/qts/domain/instruments/contract_spec.py:18` | `class` | `qts.domain.instruments.contract_spec.ContractSpec` | Trading contract metadata required for valuation and order sizing. | 0 | 0 |
| `backend/src/qts/domain/instruments/contract_spec.py:27` | `method` | `qts.domain.instruments.contract_spec.ContractSpec.__post_init__` | Perform __post_init__. | 1 | 5 |
| `backend/src/qts/domain/instruments/contract_spec.py:36` | `staticmethod` | `qts.domain.instruments.contract_spec.ContractSpec._require_positive` | Perform _require_positive. | 0 | 2 |
| `backend/src/qts/domain/instruments/derivative_spec.py:13` | `class` | `qts.domain.instruments.derivative_spec.OptionRight` | Option payoff direction. | 0 | 0 |
| `backend/src/qts/domain/instruments/derivative_spec.py:20` | `class` | `qts.domain.instruments.derivative_spec.ExerciseStyle` | Option exercise style. | 0 | 0 |
| `backend/src/qts/domain/instruments/derivative_spec.py:28` | `class` | `qts.domain.instruments.derivative_spec.DerivativeSpec` | Common derivative metadata. | 0 | 0 |
| `backend/src/qts/domain/instruments/derivative_spec.py:36` | `class` | `qts.domain.instruments.derivative_spec.FutureSpec` | Future contract metadata. | 0 | 0 |
| `backend/src/qts/domain/instruments/derivative_spec.py:41` | `method` | `qts.domain.instruments.derivative_spec.FutureSpec.__post_init__` | Perform __post_init__. | 0 | 2 |
| `backend/src/qts/domain/instruments/derivative_spec.py:48` | `class` | `qts.domain.instruments.derivative_spec.OptionSpec` | Option contract metadata. | 0 | 0 |
| `backend/src/qts/domain/instruments/derivative_spec.py:55` | `method` | `qts.domain.instruments.derivative_spec.OptionSpec.__post_init__` | Perform __post_init__. | 0 | 2 |
| `backend/src/qts/domain/instruments/instrument.py:19` | `class` | `qts.domain.instruments.instrument.AssetClass` | Supported instrument asset classes. | 0 | 0 |
| `backend/src/qts/domain/instruments/instrument.py:28` | `class` | `qts.domain.instruments.instrument.Instrument` | Tradable instrument identified by a stable internal InstrumentId. | 0 | 0 |
| `backend/src/qts/domain/instruments/instrument.py:39` | `method` | `qts.domain.instruments.instrument.Instrument.__post_init__` | Perform __post_init__. | 0 | 9 |
| `backend/src/qts/domain/market_data/bar.py:14` | `class` | `qts.domain.market_data.bar.Bar` | OHLCV bar over a half-open interval. | 0 | 0 |
| `backend/src/qts/domain/market_data/bar.py:33` | `method` | `qts.domain.market_data.bar.Bar.__post_init__` | Perform __post_init__. | 2 | 14 |
| `backend/src/qts/domain/market_data/bar.py:55` | `property` | `qts.domain.market_data.bar.Bar.interval` | Perform interval. | 1 | 1 |
| `backend/src/qts/domain/market_data/bar.py:60` | `staticmethod` | `qts.domain.market_data.bar.Bar._require_non_negative` | Perform _require_non_negative. | 0 | 2 |
| `backend/src/qts/domain/market_data/bar.py:67` | `class` | `qts.domain.market_data.bar.Quote` | Top-of-book quote. | 0 | 0 |
| `backend/src/qts/domain/market_data/bar.py:77` | `method` | `qts.domain.market_data.bar.Quote.__post_init__` | Perform __post_init__. | 2 | 4 |
| `backend/src/qts/domain/market_data/bar.py:86` | `property` | `qts.domain.market_data.bar.Quote.spread` | Perform spread. | 0 | 0 |
| `backend/src/qts/domain/market_data/bar.py:92` | `class` | `qts.domain.market_data.bar.Tick` | Trade tick. | 0 | 0 |
| `backend/src/qts/domain/market_data/bar.py:100` | `method` | `qts.domain.market_data.bar.Tick.__post_init__` | Perform __post_init__. | 2 | 2 |
| `backend/src/qts/domain/orders/value_objects.py:12` | `class` | `qts.domain.orders.value_objects.OrderState` | Execution lifecycle states for orders. | 0 | 0 |
| `backend/src/qts/domain/orders/value_objects.py:26` | `class` | `qts.domain.orders.value_objects.OrderSide` | Order side. | 0 | 0 |
| `backend/src/qts/domain/orders/value_objects.py:34` | `class` | `qts.domain.orders.value_objects.OrderIntent` | Approved order instruction before broker submission. | 0 | 0 |
| `backend/src/qts/domain/orders/value_objects.py:42` | `method` | `qts.domain.orders.value_objects.OrderIntent.__post_init__` | Perform __post_init__. | 0 | 2 |
| `backend/src/qts/domain/orders/value_objects.py:49` | `class` | `qts.domain.orders.value_objects.CancelIntent` | Intent to cancel an order through OrderManager. | 0 | 0 |
| `backend/src/qts/domain/orders/value_objects.py:57` | `class` | `qts.domain.orders.value_objects.ReplaceIntent` | Intent to replace an order through OrderManager. | 0 | 0 |
| `backend/src/qts/domain/orders/value_objects.py:63` | `method` | `qts.domain.orders.value_objects.ReplaceIntent.__post_init__` | Perform __post_init__. | 0 | 2 |
| `backend/src/qts/domain/orders/value_objects.py:70` | `class` | `qts.domain.orders.value_objects.Order` | Order snapshot owned by OrderManager. | 0 | 0 |
| `backend/src/qts/domain/orders/value_objects.py:79` | `class` | `qts.domain.orders.value_objects.ExecutionReportStatus` | Normalized broker report status. | 0 | 0 |
| `backend/src/qts/domain/orders/value_objects.py:90` | `class` | `qts.domain.orders.value_objects.ExecutionReport` | Normalized broker execution report. | 0 | 0 |
| `backend/src/qts/domain/orders/value_objects.py:102` | `method` | `qts.domain.orders.value_objects.ExecutionReport.__post_init__` | Perform __post_init__. | 0 | 10 |
| `backend/src/qts/domain/orders/value_objects.py:117` | `class` | `qts.domain.orders.value_objects.OrderFill` | OrderManager-validated fill event. | 0 | 0 |
| `backend/src/qts/domain/orders/value_objects.py:131` | `class` | `qts.domain.orders.value_objects.OrderManagerResult` | Events emitted by processing an execution report. | 0 | 0 |
| `backend/src/qts/domain/orders/value_objects.py:139` | `class` | `qts.domain.orders.value_objects.OrderManagerSnapshot` | Serializable OrderManager state for reconnect/recovery. | 0 | 0 |
| `backend/src/qts/domain/risk/decision.py:10` | `class` | `qts.domain.risk.decision.RiskDecisionStatus` | Risk check outcome. | 0 | 0 |
| `backend/src/qts/domain/risk/decision.py:19` | `class` | `qts.domain.risk.decision.RiskDecision` | Explicit result of a risk check. | 0 | 0 |
| `backend/src/qts/domain/risk/decision.py:29` | `classmethod` | `qts.domain.risk.decision.RiskDecision.approve` | Perform approve. | 0 | 1 |
| `backend/src/qts/domain/risk/decision.py:39` | `classmethod` | `qts.domain.risk.decision.RiskDecision.rejected` | Perform rejected. | 0 | 5 |
| `backend/src/qts/domain/risk/decision.py:61` | `property` | `qts.domain.risk.decision.RiskDecision.approved` | Perform approved. | 0 | 0 |
| `backend/src/qts/domain/risk/decision.py:66` | `property` | `qts.domain.risk.decision.RiskDecision.reason_text` | Perform reason_text. | 0 | 0 |
| `backend/src/qts/domain/risk/request.py:14` | `class` | `qts.domain.risk.request.OrderRiskRequest` | Pre-trade risk input for a proposed order. | 0 | 0 |
| `backend/src/qts/domain/risk/request.py:23` | `method` | `qts.domain.risk.request.OrderRiskRequest.__post_init__` | Perform __post_init__. | 1 | 7 |
| `backend/src/qts/domain/risk/request.py:35` | `property` | `qts.domain.risk.request.OrderRiskRequest.notional` | Perform notional. | 0 | 0 |
| `backend/src/qts/execution/adapters/ibkr_order_execution.py:15` | `class` | `qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionConnection` | IBKR order execution connection settings. | 0 | 0 |
| `backend/src/qts/execution/adapters/ibkr_order_execution.py:24` | `method` | `qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionConnection.__post_init__` | Perform __post_init__. | 0 | 6 |
| `backend/src/qts/execution/adapters/ibkr_order_execution.py:37` | `class` | `qts.execution.adapters.ibkr_order_execution.IbkrOrderRequest` | IBKR order request produced at the adapter boundary. | 0 | 0 |
| `backend/src/qts/execution/adapters/ibkr_order_execution.py:48` | `class` | `qts.execution.adapters.ibkr_order_execution.IbkrExecutionReport` | IBKR execution report shape before normalization. | 0 | 0 |
| `backend/src/qts/execution/adapters/ibkr_order_execution.py:59` | `class` | `qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionAdapter` | Maps internal orders to IBKR order requests and normalizes reports. | 0 | 0 |
| `backend/src/qts/execution/adapters/ibkr_order_execution.py:62` | `method` | `qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionAdapter.__init__` | Perform __init__. | 0 | 0 |
| `backend/src/qts/execution/adapters/ibkr_order_execution.py:72` | `method` | `qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionAdapter.to_order_request` | Perform to_order_request. | 1 | 2 |
| `backend/src/qts/execution/adapters/ibkr_order_execution.py:82` | `method` | `qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionAdapter.normalize_execution_report` | Perform normalize_execution_report. | 1 | 2 |
| `backend/src/qts/execution/broker.py:15` | `class` | `qts.execution.broker.BrokerCapabilities` | Broker-supported live execution features. | 0 | 0 |
| `backend/src/qts/execution/broker.py:31` | `method` | `qts.execution.broker.BrokerCapabilities.__post_init__` | 未写 docstring；静态推断为所属类上的 `  post init  ` 行为。 | 0 | 5 |
| `backend/src/qts/execution/broker.py:37` | `method` | `qts.execution.broker.BrokerCapabilities.supports_asset_class` | Perform supports_asset_class. | 0 | 2 |
| `backend/src/qts/execution/broker.py:43` | `method` | `qts.execution.broker.BrokerCapabilities.supports_order_type` | Perform supports_order_type. | 0 | 0 |
| `backend/src/qts/execution/broker.py:53` | `method` | `qts.execution.broker.BrokerCapabilities.supports_tif` | Perform supports_tif. | 0 | 0 |
| `backend/src/qts/execution/broker.py:58` | `class` | `qts.execution.broker.BrokerOrderType` | Order types modeled before broker submission. | 0 | 0 |
| `backend/src/qts/execution/broker.py:66` | `class` | `qts.execution.broker.TimeInForce` | Time-in-force values modeled at the execution boundary. | 0 | 0 |
| `backend/src/qts/execution/broker.py:75` | `class` | `qts.execution.broker.BrokerOrderRequest` | Internal order request sent to the broker adapter boundary. | 0 | 0 |
| `backend/src/qts/execution/broker.py:85` | `method` | `qts.execution.broker.BrokerOrderRequest.__post_init__` | 未写 docstring；静态推断为所属类上的 `  post init  ` 行为。 | 0 | 2 |
| `backend/src/qts/execution/broker.py:90` | `class` | `qts.execution.broker.BrokerExecutionReportStatus` | Broker-boundary execution report status. | 0 | 0 |
| `backend/src/qts/execution/broker.py:101` | `class` | `qts.execution.broker.BrokerExecutionReport` | Normalized broker callback before it reaches OrderManager. | 0 | 0 |
| `backend/src/qts/execution/broker.py:116` | `method` | `qts.execution.broker.BrokerExecutionReport.__post_init__` | 未写 docstring；静态推断为所属类上的 `  post init  ` 行为。 | 0 | 8 |
| `backend/src/qts/execution/broker.py:127` | `class` | `qts.execution.broker.BrokerAdapter` | Stable broker execution boundary. | 0 | 0 |
| `backend/src/qts/execution/broker.py:131` | `property` | `qts.execution.broker.BrokerAdapter.capabilities` | Return broker capabilities. | 0 | 0 |
| `backend/src/qts/execution/broker.py:135` | `method` | `qts.execution.broker.BrokerAdapter.submit_order` | Submit an order request. | 0 | 0 |
| `backend/src/qts/execution/broker.py:139` | `method` | `qts.execution.broker.BrokerAdapter.cancel_order` | Cancel an order by internal ID. | 0 | 0 |
| `backend/src/qts/execution/broker.py:144` | `class` | `qts.execution.broker.FakeBrokerAdapter` | Deterministic fake broker for live-beta tests and local runs. | 0 | 0 |
| `backend/src/qts/execution/broker.py:147` | `method` | `qts.execution.broker.FakeBrokerAdapter.__init__` | 未写 docstring；静态推断为所属类上的 `  init  ` 行为。 | 0 | 0 |
| `backend/src/qts/execution/broker.py:154` | `property` | `qts.execution.broker.FakeBrokerAdapter.capabilities` | Perform capabilities. | 1 | 1 |
| `backend/src/qts/execution/broker.py:158` | `method` | `qts.execution.broker.FakeBrokerAdapter.submit_order` | Perform submit_order. | 1 | 3 |
| `backend/src/qts/execution/broker.py:170` | `method` | `qts.execution.broker.FakeBrokerAdapter.cancel_order` | Perform cancel_order. | 1 | 1 |
| `backend/src/qts/execution/broker.py:179` | `method` | `qts.execution.broker.FakeBrokerAdapter.emit_fill` | Perform emit_fill. | 1 | 7 |
| `backend/src/qts/execution/broker.py:209` | `method` | `qts.execution.broker.FakeBrokerAdapter._report` | 未写 docstring；静态推断为所属类上的 ` report` 行为。 | 1 | 1 |
| `backend/src/qts/execution/broker.py:235` | `module_function` | `qts.execution.broker.normalize_broker_status` | Map broker status to normalized execution status. | 0 | 1 |
| `backend/src/qts/execution/broker.py:241` | `module_function` | `qts.execution.broker.normalize_broker_execution_report` | Convert broker-boundary report into the OrderManager report type. | 1 | 2 |
| `backend/src/qts/execution/idempotency.py:6` | `class` | `qts.execution.idempotency.FillIdempotencyStore` | Tracks fill IDs that have already been applied. | 0 | 0 |
| `backend/src/qts/execution/idempotency.py:9` | `method` | `qts.execution.idempotency.FillIdempotencyStore.__init__` | Perform __init__. | 0 | 2 |
| `backend/src/qts/execution/idempotency.py:13` | `method` | `qts.execution.idempotency.FillIdempotencyStore.mark_seen` | Perform mark_seen. | 0 | 3 |
| `backend/src/qts/execution/idempotency.py:22` | `method` | `qts.execution.idempotency.FillIdempotencyStore.discard` | Perform discard. | 0 | 1 |
| `backend/src/qts/execution/idempotency.py:26` | `method` | `qts.execution.idempotency.FillIdempotencyStore.snapshot` | Perform snapshot. | 0 | 2 |
| `backend/src/qts/execution/idempotency.py:31` | `classmethod` | `qts.execution.idempotency.FillIdempotencyStore.restore` | Perform restore. | 0 | 2 |
| `backend/src/qts/execution/order_manager.py:28` | `class` | `qts.execution.order_manager.OrderManager` | Owns order lifecycle and normalized execution reports. | 0 | 0 |
| `backend/src/qts/execution/order_manager.py:31` | `method` | `qts.execution.order_manager.OrderManager.__init__` | Perform __init__. | 1 | 1 |
| `backend/src/qts/execution/order_manager.py:39` | `method` | `qts.execution.order_manager.OrderManager.create_order` | Perform create_order. | 1 | 3 |
| `backend/src/qts/execution/order_manager.py:49` | `method` | `qts.execution.order_manager.OrderManager.mark_sent` | Perform mark_sent. | 1 | 4 |
| `backend/src/qts/execution/order_manager.py:59` | `method` | `qts.execution.order_manager.OrderManager.request_cancel` | Perform request_cancel. | 1 | 2 |
| `backend/src/qts/execution/order_manager.py:64` | `method` | `qts.execution.order_manager.OrderManager.request_replace` | Perform request_replace. | 0 | 4 |
| `backend/src/qts/execution/order_manager.py:85` | `method` | `qts.execution.order_manager.OrderManager.process_report` | Perform process_report. | 3 | 5 |
| `backend/src/qts/execution/order_manager.py:93` | `method` | `qts.execution.order_manager.OrderManager.get_order` | Perform get_order. | 0 | 0 |
| `backend/src/qts/execution/order_manager.py:97` | `method` | `qts.execution.order_manager.OrderManager.discard_terminal_order` | Perform discard_terminal_order. | 0 | 7 |
| `backend/src/qts/execution/order_manager.py:109` | `method` | `qts.execution.order_manager.OrderManager.snapshot` | Perform snapshot. | 0 | 6 |
| `backend/src/qts/execution/order_manager.py:118` | `classmethod` | `qts.execution.order_manager.OrderManager.restore` | Perform restore. | 2 | 4 |
| `backend/src/qts/execution/order_manager.py:130` | `method` | `qts.execution.order_manager.OrderManager._replace_order` | Perform _replace_order. | 0 | 1 |
| `backend/src/qts/execution/order_manager.py:150` | `method` | `qts.execution.order_manager.OrderManager._fills_for_report` | Perform _fills_for_report. | 0 | 7 |
| `backend/src/qts/execution/order_manager.py:173` | `staticmethod` | `qts.execution.order_manager.OrderManager._event_for_report` | Perform _event_for_report. | 0 | 0 |
| `backend/src/qts/execution/order_state_machine.py:11` | `class` | `qts.execution.order_state_machine.OrderEvent` | Order lifecycle transition inputs. | 0 | 0 |
| `backend/src/qts/execution/order_state_machine.py:24` | `class` | `qts.execution.order_state_machine.OrderTransitionError` | Raised when an order transition is invalid. | 0 | 0 |
| `backend/src/qts/execution/order_state_machine.py:81` | `class` | `qts.execution.order_state_machine.OrderStateMachine` | Validate and apply order lifecycle transitions. | 0 | 0 |
| `backend/src/qts/execution/order_state_machine.py:86` | `method` | `qts.execution.order_state_machine.OrderStateMachine.apply` | Perform apply. | 1 | 4 |
| `backend/src/qts/execution/simulator/fill_model.py:10` | `class` | `qts.execution.simulator.fill_model.ImmediateFillModel` | Fills market orders at the provided market price. | 0 | 0 |
| `backend/src/qts/execution/simulator/fill_model.py:13` | `method` | `qts.execution.simulator.fill_model.ImmediateFillModel.fill` | Perform fill. | 0 | 3 |
| `backend/src/qts/execution/simulator/simulated_broker.py:11` | `class` | `qts.execution.simulator.simulated_broker.SimulatedBroker` | Broker simulator with no external dependency. | 0 | 0 |
| `backend/src/qts/execution/simulator/simulated_broker.py:14` | `method` | `qts.execution.simulator.simulated_broker.SimulatedBroker.__init__` | Perform __init__. | 1 | 1 |
| `backend/src/qts/execution/simulator/simulated_broker.py:18` | `method` | `qts.execution.simulator.simulated_broker.SimulatedBroker.execute_market_order` | Perform execute_market_order. | 0 | 1 |
| `backend/src/qts/factors/momentum.py:10` | `class` | `qts.factors.momentum.FactorAsset` | Minimal asset shape required by factor ranking. | 0 | 0 |
| `backend/src/qts/factors/momentum.py:14` | `property` | `qts.factors.momentum.FactorAsset.symbol` | Stable display symbol used for deterministic tie-breaking. | 0 | 0 |
| `backend/src/qts/factors/momentum.py:19` | `class` | `qts.factors.momentum.FactorScore` | Single asset factor score. | 0 | 0 |
| `backend/src/qts/factors/momentum.py:27` | `class` | `qts.factors.momentum.FactorResult` | Ranked cross-sectional factor result. | 0 | 0 |
| `backend/src/qts/factors/momentum.py:32` | `method` | `qts.factors.momentum.FactorResult.score` | Perform score. | 0 | 1 |
| `backend/src/qts/factors/momentum.py:41` | `class` | `qts.factors.momentum.MomentumFactor` | Compute simple period momentum as last / first - 1. | 0 | 0 |
| `backend/src/qts/factors/momentum.py:46` | `method` | `qts.factors.momentum.MomentumFactor.__post_init__` | Perform __post_init__. | 0 | 1 |
| `backend/src/qts/factors/momentum.py:51` | `method` | `qts.factors.momentum.MomentumFactor.compute` | Perform compute. | 3 | 7 |
| `backend/src/qts/factors/momentum.py:61` | `staticmethod` | `qts.factors.momentum.MomentumFactor._momentum` | Perform _momentum. | 0 | 5 |
| `backend/src/qts/indicators/price/ema.py:12` | `class` | `qts.indicators.price.ema.EMA` | Incremental EMA using SMA as the warmup seed. | 0 | 0 |
| `backend/src/qts/indicators/price/ema.py:19` | `method` | `qts.indicators.price.ema.EMA.__post_init__` | Perform __post_init__. | 0 | 1 |
| `backend/src/qts/indicators/price/ema.py:24` | `property` | `qts.indicators.price.ema.EMA.ready` | Perform ready. | 0 | 0 |
| `backend/src/qts/indicators/price/ema.py:28` | `method` | `qts.indicators.price.ema.EMA.update` | Perform update. | 0 | 6 |
| `backend/src/qts/indicators/price/sma.py:12` | `class` | `qts.indicators.price.sma.SMA` | Incremental simple moving average. | 0 | 0 |
| `backend/src/qts/indicators/price/sma.py:19` | `method` | `qts.indicators.price.sma.SMA.__post_init__` | Perform __post_init__. | 0 | 1 |
| `backend/src/qts/indicators/price/sma.py:24` | `property` | `qts.indicators.price.sma.SMA.ready` | Perform ready. | 0 | 0 |
| `backend/src/qts/indicators/price/sma.py:28` | `method` | `qts.indicators.price.sma.SMA.update` | Perform update. | 0 | 4 |
| `backend/src/qts/indicators/rolling.py:14` | `class` | `qts.indicators.rolling.RollingWindow` | Bounded FIFO buffer with warmup state. | 0 | 0 |
| `backend/src/qts/indicators/rolling.py:20` | `method` | `qts.indicators.rolling.RollingWindow.__post_init__` | Perform __post_init__. | 0 | 2 |
| `backend/src/qts/indicators/rolling.py:27` | `property` | `qts.indicators.rolling.RollingWindow.ready` | Perform ready. | 0 | 1 |
| `backend/src/qts/indicators/rolling.py:31` | `method` | `qts.indicators.rolling.RollingWindow.append` | Perform append. | 0 | 1 |
| `backend/src/qts/indicators/rolling.py:35` | `method` | `qts.indicators.rolling.RollingWindow.snapshot` | Perform snapshot. | 0 | 1 |
| `backend/src/qts/indicators/rolling.py:39` | `method` | `qts.indicators.rolling.RollingWindow.restore` | Perform restore. | 0 | 2 |
| `backend/src/qts/indicators/rolling.py:46` | `method` | `qts.indicators.rolling.RollingWindow.__iter__` | Perform __iter__. | 0 | 1 |
| `backend/src/qts/indicators/rolling.py:50` | `method` | `qts.indicators.rolling.RollingWindow.__len__` | Perform __len__. | 0 | 1 |
| `backend/src/qts/load/bootstrap.py:8` | `module_function` | `qts.load.bootstrap.bootstrap_local` | Create local runtime directories and marker files safely. | 0 | 8 |
| `backend/src/qts/load/synthetic_market_data.py:14` | `class` | `qts.load.synthetic_market_data.SyntheticMarketDataConfig` | Configuration for deterministic synthetic market data. | 0 | 0 |
| `backend/src/qts/load/synthetic_market_data.py:25` | `method` | `qts.load.synthetic_market_data.SyntheticMarketDataConfig.__post_init__` | 未写 docstring；静态推断为所属类上的 `  post init  ` 行为。 | 0 | 5 |
| `backend/src/qts/load/synthetic_market_data.py:34` | `module_function` | `qts.load.synthetic_market_data.generate_bars` | Perform generate_bars. | 0 | 9 |
| `backend/src/qts/observability/audit.py:10` | `class` | `qts.observability.audit.AuditEvent` | Operational or trading audit event. | 0 | 0 |
| `backend/src/qts/observability/audit.py:19` | `method` | `qts.observability.audit.AuditEvent.__post_init__` | Perform __post_init__. | 0 | 6 |
| `backend/src/qts/observability/logging.py:14` | `module_function` | `qts.observability.logging.build_log_record` | Build a structured log record without exposing secret values. | 2 | 10 |
| `backend/src/qts/observability/logging.py:42` | `module_function` | `qts.observability.logging._metadata_fields` | Perform _metadata_fields. | 0 | 5 |
| `backend/src/qts/observability/logging.py:68` | `module_function` | `qts.observability.logging._is_secret_key` | Perform _is_secret_key. | 0 | 2 |
| `backend/src/qts/observability/metrics.py:10` | `class` | `qts.observability.metrics.MetricsRegistry` | Record counters and gauges with deterministic key formatting. | 0 | 0 |
| `backend/src/qts/observability/metrics.py:13` | `method` | `qts.observability.metrics.MetricsRegistry.__init__` | Perform __init__. | 0 | 0 |
| `backend/src/qts/observability/metrics.py:17` | `method` | `qts.observability.metrics.MetricsRegistry.increment` | Perform increment. | 1 | 3 |
| `backend/src/qts/observability/metrics.py:28` | `method` | `qts.observability.metrics.MetricsRegistry.gauge` | Perform gauge. | 1 | 1 |
| `backend/src/qts/observability/metrics.py:34` | `method` | `qts.observability.metrics.MetricsRegistry.observe_queue` | Perform observe_queue. | 1 | 2 |
| `backend/src/qts/observability/metrics.py:49` | `method` | `qts.observability.metrics.MetricsRegistry.snapshot` | Perform snapshot. | 0 | 3 |
| `backend/src/qts/observability/metrics.py:54` | `staticmethod` | `qts.observability.metrics.MetricsRegistry._metric_key` | Perform _metric_key. | 0 | 4 |
| `backend/src/qts/portfolio/accounting/fill_accounting.py:14` | `class` | `qts.portfolio.accounting.fill_accounting.TradeSide` | Fill side. | 0 | 0 |
| `backend/src/qts/portfolio/accounting/fill_accounting.py:22` | `class` | `qts.portfolio.accounting.fill_accounting.Fill` | Executed fill used by accounting. | 0 | 0 |
| `backend/src/qts/portfolio/accounting/fill_accounting.py:33` | `method` | `qts.portfolio.accounting.fill_accounting.Fill.__post_init__` | Perform __post_init__. | 0 | 8 |
| `backend/src/qts/portfolio/accounting/fill_accounting.py:45` | `class` | `qts.portfolio.accounting.fill_accounting.FillAccounting` | Fill accounting operations. | 0 | 0 |
| `backend/src/qts/portfolio/accounting/fill_accounting.py:49` | `staticmethod` | `qts.portfolio.accounting.fill_accounting.FillAccounting.apply` | Perform apply. | 0 | 2 |
| `backend/src/qts/portfolio/cash_book.py:11` | `class` | `qts.portfolio.cash_book.CashBook` | Mutable cash balance book intended to be owned by AccountActor later. | 0 | 0 |
| `backend/src/qts/portfolio/cash_book.py:14` | `method` | `qts.portfolio.cash_book.CashBook.__init__` | Perform __init__. | 0 | 1 |
| `backend/src/qts/portfolio/cash_book.py:18` | `method` | `qts.portfolio.cash_book.CashBook.apply_delta` | Perform apply_delta. | 2 | 2 |
| `backend/src/qts/portfolio/cash_book.py:23` | `method` | `qts.portfolio.cash_book.CashBook.balance` | Perform balance. | 1 | 3 |
| `backend/src/qts/portfolio/cash_book.py:27` | `method` | `qts.portfolio.cash_book.CashBook.available` | Perform available. | 2 | 3 |
| `backend/src/qts/portfolio/cash_book.py:33` | `staticmethod` | `qts.portfolio.cash_book.CashBook._normalize_currency` | Perform _normalize_currency. | 0 | 3 |
| `backend/src/qts/portfolio/position_book.py:14` | `class` | `qts.portfolio.position_book.Position` | Immutable position snapshot. | 0 | 0 |
| `backend/src/qts/portfolio/position_book.py:21` | `class` | `qts.portfolio.position_book.PositionBook` | Mutable position book intended to be owned by AccountActor later. | 0 | 0 |
| `backend/src/qts/portfolio/position_book.py:24` | `method` | `qts.portfolio.position_book.PositionBook.__init__` | Perform __init__. | 0 | 1 |
| `backend/src/qts/portfolio/position_book.py:28` | `method` | `qts.portfolio.position_book.PositionBook.apply_delta` | Perform apply_delta. | 1 | 1 |
| `backend/src/qts/portfolio/position_book.py:32` | `method` | `qts.portfolio.position_book.PositionBook.quantity` | Perform quantity. | 0 | 2 |
| `backend/src/qts/portfolio/position_book.py:36` | `method` | `qts.portfolio.position_book.PositionBook.snapshot` | Perform snapshot. | 1 | 3 |
| `backend/src/qts/portfolio/reservation_book.py:12` | `class` | `qts.portfolio.reservation_book.Reservation` | Cash reservation by order ID. | 0 | 0 |
| `backend/src/qts/portfolio/reservation_book.py:20` | `class` | `qts.portfolio.reservation_book.ReservationBook` | Idempotent cash reservations keyed by order ID. | 0 | 0 |
| `backend/src/qts/portfolio/reservation_book.py:23` | `method` | `qts.portfolio.reservation_book.ReservationBook.__init__` | Perform __init__. | 0 | 0 |
| `backend/src/qts/portfolio/reservation_book.py:27` | `method` | `qts.portfolio.reservation_book.ReservationBook.reserve` | Perform reserve. | 2 | 4 |
| `backend/src/qts/portfolio/reservation_book.py:40` | `method` | `qts.portfolio.reservation_book.ReservationBook.release` | Perform release. | 0 | 1 |
| `backend/src/qts/portfolio/reservation_book.py:44` | `method` | `qts.portfolio.reservation_book.ReservationBook.reserved` | Perform reserved. | 1 | 4 |
| `backend/src/qts/portfolio/reservation_book.py:57` | `staticmethod` | `qts.portfolio.reservation_book.ReservationBook._normalize_currency` | Perform _normalize_currency. | 0 | 3 |
| `backend/src/qts/portfolio/valuation/models.py:8` | `module_function` | `qts.portfolio.valuation.models.equity_notional` | Perform equity_notional. | 0 | 0 |
| `backend/src/qts/portfolio/valuation/models.py:13` | `module_function` | `qts.portfolio.valuation.models.future_pnl` | Perform future_pnl. | 0 | 0 |
| `backend/src/qts/portfolio/valuation/models.py:24` | `module_function` | `qts.portfolio.valuation.models.option_premium_value` | Perform option_premium_value. | 0 | 0 |
| `backend/src/qts/quality/guardrails.py:110` | `class` | `qts.quality.guardrails.GuardrailViolation` | One architecture or domain-boundary guardrail violation. | 0 | 0 |
| `backend/src/qts/quality/guardrails.py:118` | `method` | `qts.quality.guardrails.GuardrailViolation.format` | Perform format. | 0 | 0 |
| `backend/src/qts/quality/guardrails.py:123` | `class` | `qts.quality.guardrails.Rule` | Pluggable guardrail rule interface. | 0 | 0 |
| `backend/src/qts/quality/guardrails.py:128` | `method` | `qts.quality.guardrails.Rule.check` | Perform check. | 0 | 0 |
| `backend/src/qts/quality/guardrails.py:142` | `class` | `qts.quality.guardrails.ImportBoundaryRule` | Validate package import boundary direction and adapter constraints. | 0 | 0 |
| `backend/src/qts/quality/guardrails.py:147` | `method` | `qts.quality.guardrails.ImportBoundaryRule.check` | Perform check. | 2 | 3 |
| `backend/src/qts/quality/guardrails.py:163` | `class` | `qts.quality.guardrails.ProductSpecificRule` | Reject product hard-coding outside documented locations. | 0 | 0 |
| `backend/src/qts/quality/guardrails.py:168` | `method` | `qts.quality.guardrails.ProductSpecificRule.check` | Perform check. | 2 | 2 |
| `backend/src/qts/quality/guardrails.py:181` | `class` | `qts.quality.guardrails.BrokerSpecificRule` | Reject broker hard-coding outside broker boundaries. | 0 | 0 |
| `backend/src/qts/quality/guardrails.py:186` | `method` | `qts.quality.guardrails.BrokerSpecificRule.check` | Perform check. | 2 | 2 |
| `backend/src/qts/quality/guardrails.py:199` | `class` | `qts.quality.guardrails.TestSupportRule` | Reject test/anchor support in production source. | 0 | 0 |
| `backend/src/qts/quality/guardrails.py:204` | `method` | `qts.quality.guardrails.TestSupportRule.check` | Perform check. | 1 | 1 |
| `backend/src/qts/quality/guardrails.py:215` | `class` | `qts.quality.guardrails.SharedCapabilityRule` | Reject shared capability semantics in source-specific modules. | 0 | 0 |
| `backend/src/qts/quality/guardrails.py:220` | `method` | `qts.quality.guardrails.SharedCapabilityRule.check` | Perform check. | 1 | 1 |
| `backend/src/qts/quality/guardrails.py:231` | `class` | `qts.quality.guardrails.OOPPublicFactoryRule` | Reject module-level public factory names on stable concepts. | 0 | 0 |
| `backend/src/qts/quality/guardrails.py:236` | `method` | `qts.quality.guardrails.OOPPublicFactoryRule.check` | Perform check. | 1 | 1 |
| `backend/src/qts/quality/guardrails.py:247` | `class` | `qts.quality.guardrails.OOPHelperOwnershipRule` | Reject helper ownership violations that should stay private. | 0 | 0 |
| `backend/src/qts/quality/guardrails.py:252` | `method` | `qts.quality.guardrails.OOPHelperOwnershipRule.check` | Perform check. | 1 | 1 |
| `backend/src/qts/quality/guardrails.py:263` | `class` | `qts.quality.guardrails.BacktestRunnerCohesionRule` | Reject replay input assembly inside backtest runner. | 0 | 0 |
| `backend/src/qts/quality/guardrails.py:268` | `method` | `qts.quality.guardrails.BacktestRunnerCohesionRule.check` | Perform check. | 1 | 1 |
| `backend/src/qts/quality/guardrails.py:279` | `class` | `qts.quality.guardrails.BacktestInputCohesionRule` | Reject catalog/data construction inside backtest input builder. | 0 | 0 |
| `backend/src/qts/quality/guardrails.py:284` | `method` | `qts.quality.guardrails.BacktestInputCohesionRule.check` | Perform check. | 1 | 1 |
| `backend/src/qts/quality/guardrails.py:295` | `class` | `qts.quality.guardrails.BacktestEngineCohesionRule` | Reject historical replay assembly inside backtest engine. | 0 | 0 |
| `backend/src/qts/quality/guardrails.py:300` | `method` | `qts.quality.guardrails.BacktestEngineCohesionRule.check` | Perform check. | 1 | 1 |
| `backend/src/qts/quality/guardrails.py:311` | `class` | `qts.quality.guardrails.GuardrailSuite` | Execute a configured set of guardrail rules against Python files. | 0 | 0 |
| `backend/src/qts/quality/guardrails.py:314` | `method` | `qts.quality.guardrails.GuardrailSuite.__init__` | 未写 docstring；静态推断为所属类上的 `  init  ` 行为。 | 10 | 10 |
| `backend/src/qts/quality/guardrails.py:328` | `method` | `qts.quality.guardrails.GuardrailSuite.check_file` | Perform check_file. | 0 | 2 |
| `backend/src/qts/quality/guardrails.py:347` | `method` | `qts.quality.guardrails.GuardrailSuite.check` | Perform check. | 1 | 6 |
| `backend/src/qts/quality/guardrails.py:361` | `module_function` | `qts.quality.guardrails.run_guardrails` | Return all guardrail violations under the repository root. | 2 | 2 |
| `backend/src/qts/quality/guardrails.py:366` | `module_function` | `qts.quality.guardrails._check_python_file` | 未写 docstring；静态推断为 ` check python file` 函数，具体语义以实现为准。 | 2 | 7 |
| `backend/src/qts/quality/guardrails.py:378` | `module_function` | `qts.quality.guardrails._check_import` | 未写 docstring；静态推断为 ` check import` 函数，具体语义以实现为准。 | 4 | 12 |
| `backend/src/qts/quality/guardrails.py:425` | `module_function` | `qts.quality.guardrails._is_forbidden_dependency` | 未写 docstring；静态推断为 ` is forbidden dependency` 函数，具体语义以实现为准。 | 0 | 2 |
| `backend/src/qts/quality/guardrails.py:453` | `module_function` | `qts.quality.guardrails._is_forbidden_broker_adapter_dependency` | 未写 docstring；静态推断为 ` is forbidden broker adapter dependency` 函数，具体语义以实现为准。 | 0 | 2 |
| `backend/src/qts/quality/guardrails.py:465` | `module_function` | `qts.quality.guardrails._is_forbidden_adapter_dependency` | 未写 docstring；静态推断为 ` is forbidden adapter dependency` 函数，具体语义以实现为准。 | 0 | 2 |
| `backend/src/qts/quality/guardrails.py:476` | `module_function` | `qts.quality.guardrails._check_product_specific_code` | 未写 docstring；静态推断为 ` check product specific code` 函数，具体语义以实现为准。 | 1 | 1 |
| `backend/src/qts/quality/guardrails.py:492` | `module_function` | `qts.quality.guardrails._check_broker_specific_code` | 未写 docstring；静态推断为 ` check broker specific code` 函数，具体语义以实现为准。 | 1 | 1 |
| `backend/src/qts/quality/guardrails.py:508` | `module_function` | `qts.quality.guardrails._check_test_support_code` | 未写 docstring；静态推断为 ` check test support code` 函数，具体语义以实现为准。 | 4 | 12 |
| `backend/src/qts/quality/guardrails.py:539` | `module_function` | `qts.quality.guardrails._check_shared_capability_placement` | 未写 docstring；静态推断为 ` check shared capability placement` 函数，具体语义以实现为准。 | 3 | 5 |
| `backend/src/qts/quality/guardrails.py:561` | `module_function` | `qts.quality.guardrails._check_oop_public_factory_functions` | 未写 docstring；静态推断为 ` check oop public factory functions` 函数，具体语义以实现为准。 | 1 | 8 |
| `backend/src/qts/quality/guardrails.py:592` | `module_function` | `qts.quality.guardrails._check_oop_helper_ownership` | 未写 docstring；静态推断为 ` check oop helper ownership` 函数，具体语义以实现为准。 | 2 | 18 |
| `backend/src/qts/quality/guardrails.py:659` | `module_function` | `qts.quality.guardrails._check_backtest_runner_cohesion` | 未写 docstring；静态推断为 ` check backtest runner cohesion` 函数，具体语义以实现为准。 | 3 | 14 |
| `backend/src/qts/quality/guardrails.py:715` | `module_function` | `qts.quality.guardrails._check_backtest_input_cohesion` | 未写 docstring；静态推断为 ` check backtest input cohesion` 函数，具体语义以实现为准。 | 3 | 13 |
| `backend/src/qts/quality/guardrails.py:771` | `module_function` | `qts.quality.guardrails._check_backtest_engine_cohesion` | 未写 docstring；静态推断为 ` check backtest engine cohesion` 函数，具体语义以实现为准。 | 2 | 10 |
| `backend/src/qts/quality/guardrails.py:811` | `module_function` | `qts.quality.guardrails._check_forbidden_tokens` | 未写 docstring；静态推断为 ` check forbidden tokens` 函数，具体语义以实现为准。 | 3 | 14 |
| `backend/src/qts/quality/guardrails.py:844` | `module_function` | `qts.quality.guardrails._node_identifier_name` | 未写 docstring；静态推断为 ` node identifier name` 函数，具体语义以实现为准。 | 0 | 5 |
| `backend/src/qts/quality/guardrails.py:854` | `module_function` | `qts.quality.guardrails._contains_forbidden_token` | 未写 docstring；静态推断为 ` contains forbidden token` 函数，具体语义以实现为准。 | 1 | 2 |
| `backend/src/qts/quality/guardrails.py:858` | `module_function` | `qts.quality.guardrails._node_references_name` | 未写 docstring；静态推断为 ` node references name` 函数，具体语义以实现为准。 | 0 | 4 |
| `backend/src/qts/quality/guardrails.py:865` | `module_function` | `qts.quality.guardrails._identifier_tokens` | 未写 docstring；静态推断为 ` identifier tokens` 函数，具体语义以实现为准。 | 0 | 7 |
| `backend/src/qts/quality/guardrails.py:877` | `module_function` | `qts.quality.guardrails._iter_imports` | 未写 docstring；静态推断为 ` iter imports` 函数，具体语义以实现为准。 | 0 | 5 |
| `backend/src/qts/quality/guardrails.py:887` | `module_function` | `qts.quality.guardrails._iter_imported_names` | 未写 docstring；静态推断为 ` iter imported names` 函数，具体语义以实现为准。 | 0 | 3 |
| `backend/src/qts/quality/guardrails.py:895` | `module_function` | `qts.quality.guardrails._has_allowed_prefix` | 未写 docstring；静态推断为 ` has allowed prefix` 函数，具体语义以实现为准。 | 0 | 2 |
| `backend/src/qts/quality/guardrails.py:899` | `module_function` | `qts.quality.guardrails.main` | Perform main. | 1 | 6 |
| `backend/src/qts/reconciliation.py:14` | `class` | `qts.reconciliation.DriftKind` | Reconciliation outcome categories. | 0 | 0 |
| `backend/src/qts/reconciliation.py:25` | `class` | `qts.reconciliation.OrderSnapshot` | Normalized representation of an internal/broker order for reconciliation. | 0 | 0 |
| `backend/src/qts/reconciliation.py:34` | `method` | `qts.reconciliation.OrderSnapshot.__post_init__` | Perform __post_init__. | 0 | 4 |
| `backend/src/qts/reconciliation.py:43` | `class` | `qts.reconciliation.PositionSnapshot` | Normalized instrument position used in reconciliation. | 0 | 0 |
| `backend/src/qts/reconciliation.py:51` | `class` | `qts.reconciliation.CashSnapshot` | Normalized cash balance used in reconciliation. | 0 | 0 |
| `backend/src/qts/reconciliation.py:57` | `method` | `qts.reconciliation.CashSnapshot.__post_init__` | Perform __post_init__. | 0 | 2 |
| `backend/src/qts/reconciliation.py:64` | `class` | `qts.reconciliation.ReconciliationSnapshot` | Complete account snapshot used by the reconciliation engine. | 0 | 0 |
| `backend/src/qts/reconciliation.py:74` | `class` | `qts.reconciliation.DriftItem` | Single reconciliation difference entry. | 0 | 0 |
| `backend/src/qts/reconciliation.py:82` | `method` | `qts.reconciliation.DriftItem.to_dict` | Perform to_dict. | 0 | 0 |
| `backend/src/qts/reconciliation.py:93` | `class` | `qts.reconciliation.ReconciliationReport` | Drift report for a single account. | 0 | 0 |
| `backend/src/qts/reconciliation.py:100` | `property` | `qts.reconciliation.ReconciliationReport.has_drift` | Perform has_drift. | 0 | 1 |
| `backend/src/qts/reconciliation.py:106` | `method` | `qts.reconciliation.ReconciliationReport.to_dict` | Perform to_dict. | 0 | 1 |
| `backend/src/qts/reconciliation.py:116` | `class` | `qts.reconciliation.StartupReconciliationDecision` | Startup gate result derived from reconciliation drift. | 0 | 0 |
| `backend/src/qts/reconciliation.py:124` | `class` | `qts.reconciliation.ReconciliationEngine` | Deterministic snapshot reconciliation service. | 0 | 0 |
| `backend/src/qts/reconciliation.py:127` | `method` | `qts.reconciliation.ReconciliationEngine.__init__` | Perform __init__. | 0 | 2 |
| `backend/src/qts/reconciliation.py:133` | `method` | `qts.reconciliation.ReconciliationEngine.reconcile` | Reconcile two snapshots and return drift report. | 2 | 2 |
| `backend/src/qts/reconciliation.py:148` | `method` | `qts.reconciliation.ReconciliationEngine.startup_gate` | Return startup decision based on reconciliation drift. | 1 | 1 |
| `backend/src/qts/reconciliation.py:152` | `method` | `qts.reconciliation.ReconciliationEngine._effective_tolerance` | Perform _effective_tolerance. | 0 | 2 |
| `backend/src/qts/reconciliation.py:161` | `module_function` | `qts.reconciliation.startup_reconciliation_gate` | Block trading on startup when reconciliation contains critical drift. | 1 | 2 |
| `backend/src/qts/reconciliation.py:173` | `module_function` | `qts.reconciliation.reconcile_snapshots` | Compare broker and internal snapshots into a deterministic drift report. | 5 | 10 |
| `backend/src/qts/reconciliation.py:196` | `module_function` | `qts.reconciliation._compare_orders` | Perform _compare_orders. | 2 | 19 |
| `backend/src/qts/reconciliation.py:228` | `module_function` | `qts.reconciliation._compare_positions` | Perform _compare_positions. | 1 | 7 |
| `backend/src/qts/reconciliation.py:245` | `module_function` | `qts.reconciliation._compare_cash` | Perform _compare_cash. | 1 | 7 |
| `backend/src/qts/reconciliation.py:262` | `module_function` | `qts.reconciliation._quantity_item` | Perform _quantity_item. | 3 | 10 |
| `backend/src/qts/reconciliation.py:284` | `module_function` | `qts.reconciliation._order_repr` | Perform _order_repr. | 0 | 0 |
| `backend/src/qts/reconciliation.py:291` | `module_function` | `qts.reconciliation._amount` | Perform _amount. | 0 | 1 |
| `backend/src/qts/reconciliation.py:298` | `module_function` | `qts.reconciliation._amount_repr` | Perform _amount_repr. | 1 | 2 |
| `backend/src/qts/reconciliation.py:305` | `module_function` | `qts.reconciliation._drift_sort_key` | Perform _drift_sort_key. | 0 | 1 |
| `backend/src/qts/registry/broker_symbol_mapping.py:8` | `class` | `qts.registry.broker_symbol_mapping.BrokerSymbolMapping` | Bidirectional mapping between internal IDs and one broker's symbols. | 0 | 0 |
| `backend/src/qts/registry/broker_symbol_mapping.py:11` | `method` | `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.__init__` | Perform __init__. | 0 | 0 |
| `backend/src/qts/registry/broker_symbol_mapping.py:17` | `method` | `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.register` | Perform register. | 1 | 3 |
| `backend/src/qts/registry/broker_symbol_mapping.py:26` | `method` | `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.to_broker_symbol` | Perform to_broker_symbol. | 0 | 1 |
| `backend/src/qts/registry/broker_symbol_mapping.py:33` | `method` | `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.to_instrument_id` | Perform to_instrument_id. | 1 | 2 |
| `backend/src/qts/registry/broker_symbol_mapping.py:43` | `method` | `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.is_supported_symbol` | Perform is_supported_symbol. | 1 | 1 |
| `backend/src/qts/registry/broker_symbol_mapping.py:47` | `method` | `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.instrument_id_for_symbol` | Perform instrument_id_for_symbol. | 1 | 1 |
| `backend/src/qts/registry/broker_symbol_mapping.py:52` | `staticmethod` | `qts.registry.broker_symbol_mapping.BrokerSymbolMapping._normalize_broker_symbol` | Perform _normalize_broker_symbol. | 0 | 2 |
| `backend/src/qts/registry/calendar_registry.py:13` | `class` | `qts.registry.calendar_registry.MarketSession` | Internal half-open exchange session. | 0 | 0 |
| `backend/src/qts/registry/calendar_registry.py:20` | `method` | `qts.registry.calendar_registry.MarketSession.__post_init__` | Perform __post_init__. | 0 | 4 |
| `backend/src/qts/registry/calendar_registry.py:28` | `property` | `qts.registry.calendar_registry.MarketSession.open_time` | Perform open_time. | 0 | 0 |
| `backend/src/qts/registry/calendar_registry.py:33` | `property` | `qts.registry.calendar_registry.MarketSession.close_time` | Perform close_time. | 0 | 0 |
| `backend/src/qts/registry/calendar_registry.py:38` | `class` | `qts.registry.calendar_registry.CalendarProvider` | Provider interface for internal calendar session lookup. | 0 | 0 |
| `backend/src/qts/registry/calendar_registry.py:41` | `method` | `qts.registry.calendar_registry.CalendarProvider.session_for` | Return the exchange session for a date. | 0 | 0 |
| `backend/src/qts/registry/calendar_registry.py:45` | `class` | `qts.registry.calendar_registry.CalendarRegistry` | Lookup table for calendar providers. | 0 | 0 |
| `backend/src/qts/registry/calendar_registry.py:48` | `method` | `qts.registry.calendar_registry.CalendarRegistry.__init__` | Perform __init__. | 0 | 0 |
| `backend/src/qts/registry/calendar_registry.py:52` | `method` | `qts.registry.calendar_registry.CalendarRegistry.register` | Perform register. | 0 | 2 |
| `backend/src/qts/registry/calendar_registry.py:58` | `method` | `qts.registry.calendar_registry.CalendarRegistry.session_for` | Perform session_for. | 0 | 2 |
| `backend/src/qts/registry/future_chain_registry.py:11` | `class` | `qts.registry.future_chain_registry.FutureChain` | Ordered concrete future contracts for a root symbol. | 0 | 0 |
| `backend/src/qts/registry/future_chain_registry.py:17` | `method` | `qts.registry.future_chain_registry.FutureChain.__post_init__` | Perform __post_init__. | 0 | 3 |
| `backend/src/qts/registry/future_chain_registry.py:26` | `class` | `qts.registry.future_chain_registry.ContinuousFutureRef` | Research/data reference to a rolling future contract. | 0 | 0 |
| `backend/src/qts/registry/future_chain_registry.py:32` | `method` | `qts.registry.future_chain_registry.ContinuousFutureRef.__post_init__` | Perform __post_init__. | 0 | 3 |
| `backend/src/qts/registry/future_chain_registry.py:40` | `class` | `qts.registry.future_chain_registry.FutureChainRegistry` | Resolve future roots to concrete tradable contracts. | 0 | 0 |
| `backend/src/qts/registry/future_chain_registry.py:43` | `method` | `qts.registry.future_chain_registry.FutureChainRegistry.__init__` | Perform __init__. | 0 | 0 |
| `backend/src/qts/registry/future_chain_registry.py:47` | `method` | `qts.registry.future_chain_registry.FutureChainRegistry.register` | Perform register. | 1 | 1 |
| `backend/src/qts/registry/future_chain_registry.py:51` | `method` | `qts.registry.future_chain_registry.FutureChainRegistry.resolve_contract` | Perform resolve_contract. | 1 | 2 |
| `backend/src/qts/registry/future_chain_registry.py:61` | `method` | `qts.registry.future_chain_registry.FutureChainRegistry.require_tradable` | Perform require_tradable. | 0 | 2 |
| `backend/src/qts/registry/future_chain_registry.py:67` | `method` | `qts.registry.future_chain_registry.FutureChainRegistry._get_chain` | Perform _get_chain. | 1 | 2 |
| `backend/src/qts/registry/future_chain_registry.py:76` | `staticmethod` | `qts.registry.future_chain_registry.FutureChainRegistry._normalize_root` | Perform _normalize_root. | 0 | 3 |
| `backend/src/qts/registry/future_roll.py:16` | `class` | `qts.registry.future_roll.FutureContractCandidate` | One concrete futures contract candidate at a decision timestamp. | 0 | 0 |
| `backend/src/qts/registry/future_roll.py:26` | `method` | `qts.registry.future_roll.FutureContractCandidate.__post_init__` | 未写 docstring；静态推断为所属类上的 `  post init  ` 行为。 | 0 | 6 |
| `backend/src/qts/registry/future_roll.py:35` | `class` | `qts.registry.future_roll.FutureContractSelector` | Select one concrete future from same-root same-time candidates. | 0 | 0 |
| `backend/src/qts/registry/future_roll.py:38` | `method` | `qts.registry.future_roll.FutureContractSelector.select` | Select a concrete future contract. | 0 | 0 |
| `backend/src/qts/registry/future_roll.py:46` | `class` | `qts.registry.future_roll.HighestVolumeFutureContractSelector` | Select the most liquid candidate for one root at one timestamp. | 0 | 0 |
| `backend/src/qts/registry/future_roll.py:49` | `method` | `qts.registry.future_roll.HighestVolumeFutureContractSelector.select` | Perform select. | 0 | 2 |
| `backend/src/qts/registry/future_roll.py:67` | `class` | `qts.registry.future_roll.FutureRollSelection` | Resolved concrete contract for a continuous future at one timestamp. | 0 | 0 |
| `backend/src/qts/registry/future_roll.py:77` | `method` | `qts.registry.future_roll.FutureRollSelection.__post_init__` | 未写 docstring；静态推断为所属类上的 `  post init  ` 行为。 | 0 | 4 |
| `backend/src/qts/registry/future_roll.py:84` | `class` | `qts.registry.future_roll.FutureRollRegistry` | Resolve continuous futures to concrete contracts over time. | 0 | 0 |
| `backend/src/qts/registry/future_roll.py:87` | `method` | `qts.registry.future_roll.FutureRollRegistry.__init__` | 未写 docstring；静态推断为所属类上的 `  init  ` 行为。 | 0 | 0 |
| `backend/src/qts/registry/future_roll.py:96` | `method` | `qts.registry.future_roll.FutureRollRegistry.register_root` | Perform register_root. | 2 | 12 |
| `backend/src/qts/registry/future_roll.py:119` | `method` | `qts.registry.future_roll.FutureRollRegistry.continuous_instrument_id` | Perform continuous_instrument_id. | 1 | 3 |
| `backend/src/qts/registry/future_roll.py:129` | `method` | `qts.registry.future_roll.FutureRollRegistry.record_selection` | Perform record_selection. | 0 | 7 |
| `backend/src/qts/registry/future_roll.py:147` | `method` | `qts.registry.future_roll.FutureRollRegistry.is_continuous` | Perform is_continuous. | 0 | 0 |
| `backend/src/qts/registry/future_roll.py:151` | `method` | `qts.registry.future_roll.FutureRollRegistry.resolve_contract` | Perform resolve_contract. | 2 | 4 |
| `backend/src/qts/registry/future_roll.py:169` | `method` | `qts.registry.future_roll.FutureRollRegistry.related_contracts` | Perform related_contracts. | 0 | 1 |
| `backend/src/qts/registry/future_roll.py:176` | `method` | `qts.registry.future_roll.FutureRollRegistry.execution_price` | Perform execution_price. | 1 | 3 |
| `backend/src/qts/registry/future_roll.py:192` | `method` | `qts.registry.future_roll.FutureRollRegistry._selection_at` | 未写 docstring；静态推断为所属类上的 ` selection at` 行为。 | 0 | 4 |
| `backend/src/qts/registry/future_roll.py:212` | `staticmethod` | `qts.registry.future_roll.FutureRollRegistry._normalize_root` | 未写 docstring；静态推断为所属类上的 ` normalize root` 行为。 | 0 | 3 |
| `backend/src/qts/registry/instrument_registry.py:9` | `class` | `qts.registry.instrument_registry.InstrumentRegistry` | Resolve user-facing symbols to internal instruments. | 0 | 0 |
| `backend/src/qts/registry/instrument_registry.py:12` | `method` | `qts.registry.instrument_registry.InstrumentRegistry.__init__` | Perform __init__. | 0 | 0 |
| `backend/src/qts/registry/instrument_registry.py:17` | `method` | `qts.registry.instrument_registry.InstrumentRegistry.register` | Perform register. | 1 | 1 |
| `backend/src/qts/registry/instrument_registry.py:23` | `method` | `qts.registry.instrument_registry.InstrumentRegistry.resolve` | Perform resolve. | 1 | 2 |
| `backend/src/qts/registry/instrument_registry.py:31` | `method` | `qts.registry.instrument_registry.InstrumentRegistry.get_instrument` | Perform get_instrument. | 0 | 1 |
| `backend/src/qts/registry/instrument_registry.py:38` | `method` | `qts.registry.instrument_registry.InstrumentRegistry.get_contract_spec` | Perform get_contract_spec. | 1 | 1 |
| `backend/src/qts/registry/instrument_registry.py:43` | `staticmethod` | `qts.registry.instrument_registry.InstrumentRegistry._normalize_symbol` | Perform _normalize_symbol. | 0 | 3 |
| `backend/src/qts/registry/option_chain_registry.py:12` | `class` | `qts.registry.option_chain_registry.OptionChainRegistry` | Lookup option instruments by underlying and simple filters. | 0 | 0 |
| `backend/src/qts/registry/option_chain_registry.py:15` | `method` | `qts.registry.option_chain_registry.OptionChainRegistry.__init__` | Perform __init__. | 0 | 0 |
| `backend/src/qts/registry/option_chain_registry.py:19` | `method` | `qts.registry.option_chain_registry.OptionChainRegistry.register` | Perform register. | 0 | 4 |
| `backend/src/qts/registry/option_chain_registry.py:27` | `method` | `qts.registry.option_chain_registry.OptionChainRegistry.options_for` | Perform options_for. | 0 | 2 |
| `backend/src/qts/registry/option_chain_registry.py:34` | `method` | `qts.registry.option_chain_registry.OptionChainRegistry.find` | Perform find. | 1 | 4 |
| `backend/src/qts/registry/providers/comex_gold_calendar_provider.py:12` | `class` | `qts.registry.providers.comex_gold_calendar_provider.ComexGoldCalendarProvider` | Regular COMEX Gold session provider for anchor-verified semantics. | 0 | 0 |
| `backend/src/qts/registry/providers/comex_gold_calendar_provider.py:18` | `method` | `qts.registry.providers.comex_gold_calendar_provider.ComexGoldCalendarProvider.session_for` | Perform session_for. | 2 | 12 |
| `backend/src/qts/registry/providers/exchange_calendar_provider.py:14` | `class` | `qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider` | Calendar provider backed by ``exchange-calendars``. | 0 | 0 |
| `backend/src/qts/registry/providers/exchange_calendar_provider.py:17` | `method` | `qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider.__init__` | Perform __init__. | 0 | 3 |
| `backend/src/qts/registry/providers/exchange_calendar_provider.py:24` | `method` | `qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider.session_for` | Perform session_for. | 3 | 7 |
| `backend/src/qts/registry/providers/exchange_calendar_provider.py:36` | `staticmethod` | `qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider._to_datetime` | Perform _to_datetime. | 0 | 6 |
| `backend/src/qts/registry/symbol_resolution.py:12` | `class` | `qts.registry.symbol_resolution.SourceSymbolResolver` | Resolve external source symbols into internal instrument IDs. | 0 | 0 |
| `backend/src/qts/registry/symbol_resolution.py:15` | `method` | `qts.registry.symbol_resolution.SourceSymbolResolver.is_supported_symbol` | Return whether the resolver knows how to map ``symbol``. | 0 | 0 |
| `backend/src/qts/registry/symbol_resolution.py:19` | `method` | `qts.registry.symbol_resolution.SourceSymbolResolver.instrument_id_for_symbol` | Resolve ``symbol`` to an internal ``InstrumentId``. | 0 | 0 |
| `backend/src/qts/registry/symbol_resolution.py:25` | `class` | `qts.registry.symbol_resolution.StaticSymbolResolver` | Resolve source symbols from an explicit symbol-to-instrument mapping. | 0 | 0 |
| `backend/src/qts/registry/symbol_resolution.py:31` | `method` | `qts.registry.symbol_resolution.StaticSymbolResolver.__post_init__` | Perform __post_init__. | 1 | 5 |
| `backend/src/qts/registry/symbol_resolution.py:43` | `method` | `qts.registry.symbol_resolution.StaticSymbolResolver.is_supported_symbol` | Perform is_supported_symbol. | 1 | 1 |
| `backend/src/qts/registry/symbol_resolution.py:47` | `method` | `qts.registry.symbol_resolution.StaticSymbolResolver.instrument_id_for_symbol` | Perform instrument_id_for_symbol. | 1 | 2 |
| `backend/src/qts/registry/symbol_resolution.py:56` | `staticmethod` | `qts.registry.symbol_resolution.StaticSymbolResolver._normalize_symbol` | Perform _normalize_symbol. | 0 | 3 |
| `backend/src/qts/risk/config.py:10` | `class` | `qts.risk.config.RiskRuleConfig` | One configured risk rule. | 0 | 0 |
| `backend/src/qts/risk/config.py:17` | `method` | `qts.risk.config.RiskRuleConfig.__post_init__` | Perform __post_init__. | 0 | 4 |
| `backend/src/qts/risk/config.py:26` | `class` | `qts.risk.config.RiskConfig` | Account/strategy/product risk configuration. | 0 | 0 |
| `backend/src/qts/risk/config.py:35` | `method` | `qts.risk.config.RiskConfig.__post_init__` | Perform __post_init__. | 0 | 6 |
| `backend/src/qts/risk/kill_switch.py:12` | `class` | `qts.risk.kill_switch.KillSwitchScopeType` | Supported kill-switch scopes. | 0 | 0 |
| `backend/src/qts/risk/kill_switch.py:22` | `class` | `qts.risk.kill_switch.KillSwitchScope` | Kill-switch scope identity. | 0 | 0 |
| `backend/src/qts/risk/kill_switch.py:29` | `classmethod` | `qts.risk.kill_switch.KillSwitchScope.global_scope` | Perform global_scope. | 0 | 1 |
| `backend/src/qts/risk/kill_switch.py:34` | `classmethod` | `qts.risk.kill_switch.KillSwitchScope.account` | Perform account. | 0 | 1 |
| `backend/src/qts/risk/kill_switch.py:39` | `classmethod` | `qts.risk.kill_switch.KillSwitchScope.strategy` | Perform strategy. | 0 | 1 |
| `backend/src/qts/risk/kill_switch.py:44` | `classmethod` | `qts.risk.kill_switch.KillSwitchScope.broker` | Perform broker. | 0 | 1 |
| `backend/src/qts/risk/kill_switch.py:48` | `method` | `qts.risk.kill_switch.KillSwitchScope.reason_code` | Perform reason_code. | 0 | 1 |
| `backend/src/qts/risk/kill_switch.py:54` | `class` | `qts.risk.kill_switch.KillSwitchState` | Kill-switch activation state. | 0 | 0 |
| `backend/src/qts/risk/kill_switch.py:62` | `class` | `qts.risk.kill_switch.KillSwitchRegistry` | Auditable in-memory kill-switch registry. | 0 | 0 |
| `backend/src/qts/risk/kill_switch.py:65` | `method` | `qts.risk.kill_switch.KillSwitchRegistry.__init__` | 未写 docstring；静态推断为所属类上的 `  init  ` 行为。 | 0 | 0 |
| `backend/src/qts/risk/kill_switch.py:68` | `method` | `qts.risk.kill_switch.KillSwitchRegistry.activate` | Perform activate. | 1 | 3 |
| `backend/src/qts/risk/kill_switch.py:76` | `method` | `qts.risk.kill_switch.KillSwitchRegistry.deactivate` | Perform deactivate. | 1 | 3 |
| `backend/src/qts/risk/kill_switch.py:84` | `method` | `qts.risk.kill_switch.KillSwitchRegistry.check_order` | Perform check_order. | 1 | 5 |
| `backend/src/qts/risk/kill_switch.py:105` | `staticmethod` | `qts.risk.kill_switch.KillSwitchRegistry._matching_scopes` | 未写 docstring；静态推断为所属类上的 ` matching scopes` 行为。 | 4 | 6 |
| `backend/src/qts/risk/risk_engine.py:11` | `class` | `qts.risk.risk_engine.RiskEngine` | Apply risk rules in order and return the first rejection. | 0 | 0 |
| `backend/src/qts/risk/risk_engine.py:14` | `method` | `qts.risk.risk_engine.RiskEngine.__init__` | Perform __init__. | 0 | 1 |
| `backend/src/qts/risk/risk_engine.py:18` | `method` | `qts.risk.risk_engine.RiskEngine.check` | Perform check. | 0 | 2 |
| `backend/src/qts/risk/rule.py:10` | `class` | `qts.risk.rule.RiskRule` | A pre-trade risk rule. | 0 | 0 |
| `backend/src/qts/risk/rule.py:13` | `method` | `qts.risk.rule.RiskRule.check` | Return an explicit risk decision. | 0 | 0 |
| `backend/src/qts/risk/rule_registry.py:13` | `class` | `qts.risk.rule_registry.RiskRuleRegistry` | Map configured rule names to executable risk rules. | 0 | 0 |
| `backend/src/qts/risk/rule_registry.py:16` | `method` | `qts.risk.rule_registry.RiskRuleRegistry.build` | Perform build. | 3 | 5 |
| `backend/src/qts/risk/rule_registry.py:25` | `staticmethod` | `qts.risk.rule_registry.RiskRuleRegistry._param` | Perform _param. | 0 | 1 |
| `backend/src/qts/risk/rules/max_notional.py:12` | `class` | `qts.risk.rules.max_notional.MaxNotionalRule` | Reject orders whose notional exceeds a fixed limit. | 0 | 0 |
| `backend/src/qts/risk/rules/max_notional.py:17` | `method` | `qts.risk.rules.max_notional.MaxNotionalRule.__post_init__` | Perform __post_init__. | 0 | 2 |
| `backend/src/qts/risk/rules/max_notional.py:22` | `method` | `qts.risk.rules.max_notional.MaxNotionalRule.check` | Perform check. | 0 | 2 |
| `backend/src/qts/risk/rules/max_order_qty.py:12` | `class` | `qts.risk.rules.max_order_qty.MaxOrderQuantityRule` | Reject orders whose absolute quantity exceeds a fixed limit. | 0 | 0 |
| `backend/src/qts/risk/rules/max_order_qty.py:17` | `method` | `qts.risk.rules.max_order_qty.MaxOrderQuantityRule.__post_init__` | Perform __post_init__. | 0 | 2 |
| `backend/src/qts/risk/rules/max_order_qty.py:22` | `method` | `qts.risk.rules.max_order_qty.MaxOrderQuantityRule.check` | Perform check. | 0 | 2 |
| `backend/src/qts/risk/rules/trading_session_rule.py:13` | `class` | `qts.risk.rules.trading_session_rule.SessionLookup` | Calendar session lookup required by the rule. | 0 | 0 |
| `backend/src/qts/risk/rules/trading_session_rule.py:16` | `method` | `qts.risk.rules.trading_session_rule.SessionLookup.session_for` | Return the internal market session for the date. | 0 | 0 |
| `backend/src/qts/risk/rules/trading_session_rule.py:21` | `class` | `qts.risk.rules.trading_session_rule.TradingSessionRule` | Reject orders whose order time is outside the configured session. | 0 | 0 |
| `backend/src/qts/risk/rules/trading_session_rule.py:28` | `method` | `qts.risk.rules.trading_session_rule.TradingSessionRule.check` | Perform check. | 0 | 5 |
| `backend/src/qts/runtime/actor.py:8` | `class` | `qts.runtime.actor.Actor` | Base actor that handles messages serially through an ActorRef. | 0 | 0 |
| `backend/src/qts/runtime/actor.py:12` | `method` | `qts.runtime.actor.Actor.handle` | Handle one message. | 0 | 0 |
| `backend/src/qts/runtime/actor_ref.py:12` | `class` | `qts.runtime.actor_ref.ActorRef` | Message-only reference to an actor mailbox. | 0 | 0 |
| `backend/src/qts/runtime/actor_ref.py:18` | `method` | `qts.runtime.actor_ref.ActorRef.tell` | Perform tell. | 0 | 1 |
| `backend/src/qts/runtime/actor_ref.py:22` | `method` | `qts.runtime.actor_ref.ActorRef.process_one` | Perform process_one. | 0 | 3 |
| `backend/src/qts/runtime/actor_ref.py:29` | `method` | `qts.runtime.actor_ref.ActorRef.process_all` | Perform process_all. | 1 | 1 |
| `backend/src/qts/runtime/actors/account_actor.py:19` | `class` | `qts.runtime.actors.account_actor.ApplyFill` | Message instructing AccountActor to apply a validated fill. | 0 | 0 |
| `backend/src/qts/runtime/actors/account_actor.py:28` | `class` | `qts.runtime.actors.account_actor.AccountSnapshot` | Read-only account snapshot. | 0 | 0 |
| `backend/src/qts/runtime/actors/account_actor.py:35` | `class` | `qts.runtime.actors.account_actor.AccountActor` | Owns account cash and position state. | 0 | 0 |
| `backend/src/qts/runtime/actors/account_actor.py:38` | `method` | `qts.runtime.actors.account_actor.AccountActor.__init__` | Perform __init__. | 3 | 3 |
| `backend/src/qts/runtime/actors/account_actor.py:44` | `method` | `qts.runtime.actors.account_actor.AccountActor.handle` | Perform handle. | 1 | 4 |
| `backend/src/qts/runtime/actors/account_actor.py:51` | `method` | `qts.runtime.actors.account_actor.AccountActor.snapshot` | Perform snapshot. | 1 | 4 |
| `backend/src/qts/runtime/actors/account_actor.py:58` | `method` | `qts.runtime.actors.account_actor.AccountActor._apply_fill` | Perform _apply_fill. | 0 | 3 |
| `backend/src/qts/runtime/actors/execution_actor.py:15` | `class` | `qts.runtime.actors.execution_actor.ExecutionAdapter` | Execution boundary contract used by the actor. | 0 | 0 |
| `backend/src/qts/runtime/actors/execution_actor.py:18` | `method` | `qts.runtime.actors.execution_actor.ExecutionAdapter.execute_market_order` | Execute a market order. | 0 | 0 |
| `backend/src/qts/runtime/actors/execution_actor.py:30` | `class` | `qts.runtime.actors.execution_actor.OrderExecutionRequest` | Message requesting order execution. | 0 | 0 |
| `backend/src/qts/runtime/actors/execution_actor.py:38` | `class` | `qts.runtime.actors.execution_actor.ExecutionActor` | Actor wrapper for an order execution adapter or simulator. | 0 | 0 |
| `backend/src/qts/runtime/actors/execution_actor.py:41` | `method` | `qts.runtime.actors.execution_actor.ExecutionActor.__init__` | 未写 docstring；静态推断为所属类上的 `  init  ` 行为。 | 1 | 1 |
| `backend/src/qts/runtime/actors/execution_actor.py:50` | `method` | `qts.runtime.actors.execution_actor.ExecutionActor.handle` | Perform handle. | 0 | 5 |
| `backend/src/qts/runtime/actors/market_data_actor.py:29` | `class` | `qts.runtime.actors.market_data_actor.MarketDataEvent` | Normalized market data payload accepted by MarketDataActor. | 0 | 0 |
| `backend/src/qts/runtime/actors/market_data_actor.py:36` | `class` | `qts.runtime.actors.market_data_actor.SubscribeMarketData` | Message requesting strategy market data fan-out. | 0 | 0 |
| `backend/src/qts/runtime/actors/market_data_actor.py:44` | `method` | `qts.runtime.actors.market_data_actor.SubscribeMarketData.__post_init__` | Perform __post_init__. | 0 | 4 |
| `backend/src/qts/runtime/actors/market_data_actor.py:52` | `class` | `qts.runtime.actors.market_data_actor.MarketDataActor` | Actor boundary for normalized market data events. | 0 | 0 |
| `backend/src/qts/runtime/actors/market_data_actor.py:55` | `method` | `qts.runtime.actors.market_data_actor.MarketDataActor.__init__` | Perform __init__. | 2 | 5 |
| `backend/src/qts/runtime/actors/market_data_actor.py:79` | `method` | `qts.runtime.actors.market_data_actor.MarketDataActor.handle` | Perform handle. | 3 | 11 |
| `backend/src/qts/runtime/actors/market_data_actor.py:102` | `property` | `qts.runtime.actors.market_data_actor.MarketDataActor.logical_subscription_count` | Perform logical_subscription_count. | 0 | 1 |
| `backend/src/qts/runtime/actors/market_data_actor.py:107` | `property` | `qts.runtime.actors.market_data_actor.MarketDataActor.physical_subscription_count` | Perform physical_subscription_count. | 0 | 1 |
| `backend/src/qts/runtime/actors/market_data_actor.py:111` | `method` | `qts.runtime.actors.market_data_actor.MarketDataActor._subscribe` | Perform _subscribe. | 5 | 9 |
| `backend/src/qts/runtime/actors/market_data_actor.py:142` | `method` | `qts.runtime.actors.market_data_actor.MarketDataActor._publish_to_logical_subscribers` | Perform _publish_to_logical_subscribers. | 2 | 9 |
| `backend/src/qts/runtime/actors/market_data_actor.py:169` | `method` | `qts.runtime.actors.market_data_actor.MarketDataActor._publish` | Perform _publish. | 0 | 1 |
| `backend/src/qts/runtime/actors/market_data_actor.py:175` | `staticmethod` | `qts.runtime.actors.market_data_actor.MarketDataActor._publish_to` | Perform _publish_to. | 0 | 1 |
| `backend/src/qts/runtime/actors/market_data_actor.py:181` | `staticmethod` | `qts.runtime.actors.market_data_actor.MarketDataActor._subscription_id` | Perform _subscription_id. | 0 | 1 |
| `backend/src/qts/runtime/actors/order_manager_actor.py:19` | `class` | `qts.runtime.actors.order_manager_actor.SubmitOrder` | Message to submit an approved order to an execution actor. | 0 | 0 |
| `backend/src/qts/runtime/actors/order_manager_actor.py:28` | `class` | `qts.runtime.actors.order_manager_actor.OrderManagerActor` | Actor-owned OrderManager wrapper. | 0 | 0 |
| `backend/src/qts/runtime/actors/order_manager_actor.py:31` | `method` | `qts.runtime.actors.order_manager_actor.OrderManagerActor.__init__` | Perform __init__. | 1 | 2 |
| `backend/src/qts/runtime/actors/order_manager_actor.py:45` | `method` | `qts.runtime.actors.order_manager_actor.OrderManagerActor.handle` | Perform handle. | 2 | 6 |
| `backend/src/qts/runtime/actors/order_manager_actor.py:55` | `method` | `qts.runtime.actors.order_manager_actor.OrderManagerActor.get_order` | Perform get_order. | 0 | 1 |
| `backend/src/qts/runtime/actors/order_manager_actor.py:60` | `property` | `qts.runtime.actors.order_manager_actor.OrderManagerActor.fills` | Perform fills. | 0 | 1 |
| `backend/src/qts/runtime/actors/order_manager_actor.py:65` | `property` | `qts.runtime.actors.order_manager_actor.OrderManagerActor.fill_count` | Perform fill_count. | 0 | 1 |
| `backend/src/qts/runtime/actors/order_manager_actor.py:69` | `method` | `qts.runtime.actors.order_manager_actor.OrderManagerActor.fills_since` | Perform fills_since. | 0 | 1 |
| `backend/src/qts/runtime/actors/order_manager_actor.py:73` | `method` | `qts.runtime.actors.order_manager_actor.OrderManagerActor.compact_for_streaming` | Perform compact_for_streaming. | 0 | 2 |
| `backend/src/qts/runtime/actors/order_manager_actor.py:79` | `method` | `qts.runtime.actors.order_manager_actor.OrderManagerActor._handle_submit` | Perform _handle_submit. | 1 | 4 |
| `backend/src/qts/runtime/actors/order_manager_actor.py:91` | `method` | `qts.runtime.actors.order_manager_actor.OrderManagerActor._handle_report` | Perform _handle_report. | 1 | 6 |
| `backend/src/qts/runtime/actors/signal_aggregator_actor.py:14` | `class` | `qts.runtime.actors.signal_aggregator_actor.StrategySignalEvent` | Strategy intents emitted for one completed bar. | 0 | 0 |
| `backend/src/qts/runtime/actors/signal_aggregator_actor.py:22` | `class` | `qts.runtime.actors.signal_aggregator_actor.AggregatedSignalBatch` | Aggregated intents ready for portfolio/risk/order flow. | 0 | 0 |
| `backend/src/qts/runtime/actors/signal_aggregator_actor.py:29` | `class` | `qts.runtime.actors.signal_aggregator_actor.SignalAggregatorActor` | Boundary for combining strategy signals before order flow. | 0 | 0 |
| `backend/src/qts/runtime/actors/signal_aggregator_actor.py:32` | `method` | `qts.runtime.actors.signal_aggregator_actor.SignalAggregatorActor.__init__` | Perform __init__. | 0 | 0 |
| `backend/src/qts/runtime/actors/signal_aggregator_actor.py:36` | `method` | `qts.runtime.actors.signal_aggregator_actor.SignalAggregatorActor.handle` | Perform handle. | 1 | 5 |
| `backend/src/qts/runtime/actors/strategy_actor.py:14` | `class` | `qts.runtime.actors.strategy_actor.StrategyBarEvent` | Completed strategy-facing bar delivered to a strategy actor. | 0 | 0 |
| `backend/src/qts/runtime/actors/strategy_actor.py:23` | `class` | `qts.runtime.actors.strategy_actor.StrategyBarResult` | New strategy intents emitted while handling one bar. | 0 | 0 |
| `backend/src/qts/runtime/actors/strategy_actor.py:31` | `class` | `qts.runtime.actors.strategy_actor.StrategyFinalize` | Request strategy finalization. | 0 | 0 |
| `backend/src/qts/runtime/actors/strategy_actor.py:36` | `class` | `qts.runtime.actors.strategy_actor.StrategyFinalized` | Strategy finalization completed. | 0 | 0 |
| `backend/src/qts/runtime/actors/strategy_actor.py:42` | `class` | `qts.runtime.actors.strategy_actor.StrategyActor` | Actor-owned strategy instance and user-facing context. | 0 | 0 |
| `backend/src/qts/runtime/actors/strategy_actor.py:45` | `method` | `qts.runtime.actors.strategy_actor.StrategyActor.__init__` | Perform __init__. | 0 | 1 |
| `backend/src/qts/runtime/actors/strategy_actor.py:58` | `method` | `qts.runtime.actors.strategy_actor.StrategyActor.handle` | Perform handle. | 2 | 6 |
| `backend/src/qts/runtime/actors/strategy_actor.py:68` | `method` | `qts.runtime.actors.strategy_actor.StrategyActor._handle_bar` | Perform _handle_bar. | 1 | 5 |
| `backend/src/qts/runtime/actors/strategy_actor.py:82` | `method` | `qts.runtime.actors.strategy_actor.StrategyActor._handle_finalize` | Perform _handle_finalize. | 1 | 4 |
| `backend/src/qts/runtime/event_store.py:15` | `class` | `qts.runtime.event_store.EventStore` | Append-only event store contract. | 0 | 0 |
| `backend/src/qts/runtime/event_store.py:18` | `method` | `qts.runtime.event_store.EventStore.append` | Append an event to the store and return its sequence index. | 0 | 0 |
| `backend/src/qts/runtime/event_store.py:22` | `method` | `qts.runtime.event_store.EventStore.replay` | Replay events from the store, optionally filtered by partition key. | 0 | 0 |
| `backend/src/qts/runtime/event_store.py:26` | `method` | `qts.runtime.event_store.EventStore.by_correlation_id` | Replay all events with a given correlation identifier. | 0 | 0 |
| `backend/src/qts/runtime/event_store.py:31` | `class` | `qts.runtime.event_store.InMemoryEventStore` | Deterministic append-only in-memory event store. | 0 | 0 |
| `backend/src/qts/runtime/event_store.py:34` | `method` | `qts.runtime.event_store.InMemoryEventStore.__init__` | Perform __init__. | 0 | 0 |
| `backend/src/qts/runtime/event_store.py:38` | `method` | `qts.runtime.event_store.InMemoryEventStore.append` | Perform append. | 0 | 2 |
| `backend/src/qts/runtime/event_store.py:43` | `method` | `qts.runtime.event_store.InMemoryEventStore.append_many` | Perform append_many. | 1 | 1 |
| `backend/src/qts/runtime/event_store.py:48` | `method` | `qts.runtime.event_store.InMemoryEventStore.replay` | Perform replay. | 0 | 2 |
| `backend/src/qts/runtime/event_store.py:54` | `method` | `qts.runtime.event_store.InMemoryEventStore.by_correlation_id` | Perform by_correlation_id. | 0 | 1 |
| `backend/src/qts/runtime/event_store.py:59` | `class` | `qts.runtime.event_store.FileEventStore` | JSONL event store for local deterministic recovery tests. | 0 | 0 |
| `backend/src/qts/runtime/event_store.py:62` | `method` | `qts.runtime.event_store.FileEventStore.__init__` | Perform __init__. | 0 | 0 |
| `backend/src/qts/runtime/event_store.py:66` | `method` | `qts.runtime.event_store.FileEventStore.append` | Perform append. | 2 | 8 |
| `backend/src/qts/runtime/event_store.py:76` | `method` | `qts.runtime.event_store.FileEventStore.replay` | Perform replay. | 1 | 7 |
| `backend/src/qts/runtime/event_store.py:90` | `method` | `qts.runtime.event_store.FileEventStore.by_correlation_id` | Perform by_correlation_id. | 1 | 2 |
| `backend/src/qts/runtime/event_store.py:95` | `staticmethod` | `qts.runtime.event_store.FileEventStore._event_to_json` | Perform _event_to_json. | 0 | 1 |
| `backend/src/qts/runtime/event_store.py:108` | `staticmethod` | `qts.runtime.event_store.FileEventStore._event_from_json` | Perform _event_from_json. | 3 | 12 |
| `backend/src/qts/runtime/live.py:12` | `class` | `qts.runtime.live.LiveRuntimeState` | Live runtime lifecycle states. | 0 | 0 |
| `backend/src/qts/runtime/live.py:22` | `class` | `qts.runtime.live.LiveMode` | Runtime mode with explicit live-trading permissions. | 0 | 0 |
| `backend/src/qts/runtime/live.py:31` | `class` | `qts.runtime.live.LiveStartupConfig` | Startup guard inputs for live-capable runtime. | 0 | 0 |
| `backend/src/qts/runtime/live.py:43` | `class` | `qts.runtime.live.LiveStartupDecision` | Result of startup guard validation. | 0 | 0 |
| `backend/src/qts/runtime/live.py:50` | `module_function` | `qts.runtime.live.validate_live_startup` | Fail closed unless all live safety prerequisites are explicit. | 1 | 3 |
| `backend/src/qts/runtime/live.py:97` | `class` | `qts.runtime.live.LiveRuntimeStateMachine` | Mutable live runtime state machine. | 0 | 0 |
| `backend/src/qts/runtime/live.py:102` | `method` | `qts.runtime.live.LiveRuntimeStateMachine.apply` | Perform apply. | 0 | 3 |
| `backend/src/qts/runtime/live.py:112` | `class` | `qts.runtime.live.RuntimeOrderResult` | Result of live runtime order submission. | 0 | 0 |
| `backend/src/qts/runtime/live.py:121` | `class` | `qts.runtime.live.LiveRuntime` | Small live-beta runtime wrapper over fake or real boundary adapters. | 0 | 0 |
| `backend/src/qts/runtime/live.py:124` | `method` | `qts.runtime.live.LiveRuntime.__init__` | 未写 docstring；静态推断为所属类上的 `  init  ` 行为。 | 1 | 1 |
| `backend/src/qts/runtime/live.py:130` | `property` | `qts.runtime.live.LiveRuntime.state` | Perform state. | 0 | 0 |
| `backend/src/qts/runtime/live.py:135` | `property` | `qts.runtime.live.LiveRuntime.feed` | Perform feed. | 0 | 0 |
| `backend/src/qts/runtime/live.py:139` | `method` | `qts.runtime.live.LiveRuntime.start` | Perform start. | 0 | 2 |
| `backend/src/qts/runtime/live.py:144` | `method` | `qts.runtime.live.LiveRuntime.stop` | Perform stop. | 0 | 1 |
| `backend/src/qts/runtime/live.py:148` | `method` | `qts.runtime.live.LiveRuntime.pause` | Perform pause. | 0 | 1 |
| `backend/src/qts/runtime/live.py:152` | `method` | `qts.runtime.live.LiveRuntime.resume` | Perform resume. | 0 | 1 |
| `backend/src/qts/runtime/live.py:156` | `method` | `qts.runtime.live.LiveRuntime.degrade` | Perform degrade. | 0 | 1 |
| `backend/src/qts/runtime/live.py:160` | `method` | `qts.runtime.live.LiveRuntime.recover` | Perform recover. | 0 | 1 |
| `backend/src/qts/runtime/live.py:164` | `method` | `qts.runtime.live.LiveRuntime.submit_order` | Perform submit_order. | 1 | 4 |
| `backend/src/qts/runtime/mailbox.py:8` | `class` | `qts.runtime.mailbox.Mailbox` | Simple in-memory FIFO mailbox. | 0 | 0 |
| `backend/src/qts/runtime/mailbox.py:11` | `method` | `qts.runtime.mailbox.Mailbox.__init__` | Perform __init__. | 0 | 1 |
| `backend/src/qts/runtime/mailbox.py:16` | `property` | `qts.runtime.mailbox.Mailbox.size` | Perform size. | 0 | 1 |
| `backend/src/qts/runtime/mailbox.py:20` | `method` | `qts.runtime.mailbox.Mailbox.put` | Perform put. | 0 | 1 |
| `backend/src/qts/runtime/mailbox.py:24` | `method` | `qts.runtime.mailbox.Mailbox.get` | Perform get. | 0 | 1 |
| `backend/src/qts/runtime/mailbox.py:28` | `method` | `qts.runtime.mailbox.Mailbox.empty` | Perform empty. | 0 | 0 |
| `backend/src/qts/runtime/partitioning.py:11` | `class` | `qts.runtime.partitioning.AccountPartitionPolicy` | Partition live state and messages by internal account id. | 0 | 0 |
| `backend/src/qts/runtime/partitioning.py:14` | `method` | `qts.runtime.partitioning.AccountPartitionPolicy.partition_for` | Perform partition_for. | 0 | 0 |
| `backend/src/qts/runtime/partitioning.py:20` | `class` | `qts.runtime.partitioning.AccountBrokerMapping` | Boundary-only broker account mapping. | 0 | 0 |
| `backend/src/qts/runtime/partitioning.py:27` | `method` | `qts.runtime.partitioning.AccountBrokerMapping.__post_init__` | Perform __post_init__. | 0 | 2 |
| `backend/src/qts/runtime/partitioning.py:32` | `method` | `qts.runtime.partitioning.AccountBrokerMapping.boundary_payload` | Perform boundary_payload. | 0 | 0 |
| `backend/src/qts/runtime/partitioning.py:41` | `class` | `qts.runtime.partitioning.AccountRiskConfig` | Per-account live risk limits. | 0 | 0 |
| `backend/src/qts/runtime/partitioning.py:48` | `method` | `qts.runtime.partitioning.AccountRiskConfig.__post_init__` | Perform __post_init__. | 0 | 6 |
| `backend/src/qts/runtime/partitioning.py:55` | `method` | `qts.runtime.partitioning.AccountRiskConfig.limit_for` | Perform limit_for. | 0 | 1 |
| `backend/src/qts/runtime/router.py:10` | `class` | `qts.runtime.router.RouteNotFoundError` | Raised when no actor route exists for a partition key. | 0 | 0 |
| `backend/src/qts/runtime/router.py:14` | `class` | `qts.runtime.router.EventRouter` | Route messages to actor refs by a message-derived key. | 0 | 0 |
| `backend/src/qts/runtime/router.py:17` | `method` | `qts.runtime.router.EventRouter.__init__` | Perform __init__. | 0 | 2 |
| `backend/src/qts/runtime/router.py:24` | `method` | `qts.runtime.router.EventRouter.register` | Perform register. | 0 | 0 |
| `backend/src/qts/runtime/router.py:28` | `method` | `qts.runtime.router.EventRouter.route` | Perform route. | 1 | 3 |
| `backend/src/qts/runtime/state_recovery.py:10` | `class` | `qts.runtime.state_recovery.StateSnapshot` | Serialized actor state snapshot envelope. | 0 | 0 |
| `backend/src/qts/runtime/state_recovery.py:17` | `method` | `qts.runtime.state_recovery.StateSnapshot.__post_init__` | Perform __post_init__. | 0 | 3 |
| `backend/src/qts/runtime/state_recovery.py:25` | `class` | `qts.runtime.state_recovery.InMemorySnapshotStore` | In-memory snapshot store for deterministic tests and local recovery. | 0 | 0 |
| `backend/src/qts/runtime/state_recovery.py:28` | `method` | `qts.runtime.state_recovery.InMemorySnapshotStore.__init__` | Perform __init__. | 0 | 0 |
| `backend/src/qts/runtime/state_recovery.py:32` | `method` | `qts.runtime.state_recovery.InMemorySnapshotStore.save` | Perform save. | 0 | 0 |
| `backend/src/qts/runtime/state_recovery.py:36` | `method` | `qts.runtime.state_recovery.InMemorySnapshotStore.load` | Perform load. | 0 | 3 |
| `backend/src/qts/strategy_sdk/asset_ref.py:13` | `class` | `qts.strategy_sdk.asset_ref.AssetRef` | Lightweight strategy-facing reference to an internal instrument. | 0 | 0 |
| `backend/src/qts/strategy_sdk/asset_ref.py:20` | `method` | `qts.strategy_sdk.asset_ref.AssetRef.__post_init__` | Perform __post_init__. | 0 | 5 |
| `backend/src/qts/strategy_sdk/asset_ref.py:26` | `method` | `qts.strategy_sdk.asset_ref.AssetRef.__hash__` | Perform __hash__. | 0 | 1 |
| `backend/src/qts/strategy_sdk/asset_resolver.py:15` | `class` | `qts.strategy_sdk.asset_resolver.SymbolResolver` | Platform-provided symbol resolution boundary. | 0 | 0 |
| `backend/src/qts/strategy_sdk/asset_resolver.py:18` | `method` | `qts.strategy_sdk.asset_resolver.SymbolResolver.resolve` | 未写 docstring；静态推断为所属类上的 `resolve` 行为。 | 0 | 0 |
| `backend/src/qts/strategy_sdk/asset_resolver.py:21` | `class` | `qts.strategy_sdk.asset_resolver.FutureContractResolver` | Platform-provided future chain resolution boundary. | 0 | 0 |
| `backend/src/qts/strategy_sdk/asset_resolver.py:24` | `method` | `qts.strategy_sdk.asset_resolver.FutureContractResolver.resolve_contract` | 未写 docstring；静态推断为所属类上的 `resolve contract` 行为。 | 0 | 0 |
| `backend/src/qts/strategy_sdk/asset_resolver.py:28` | `class` | `qts.strategy_sdk.asset_resolver.ContinuousFutureResolver` | Platform-provided continuous future reference boundary. | 0 | 0 |
| `backend/src/qts/strategy_sdk/asset_resolver.py:31` | `method` | `qts.strategy_sdk.asset_resolver.ContinuousFutureResolver.continuous_instrument_id` | 未写 docstring；静态推断为所属类上的 `continuous instrument id` 行为。 | 0 | 0 |
| `backend/src/qts/strategy_sdk/asset_resolver.py:34` | `class` | `qts.strategy_sdk.asset_resolver.OptionContractRef` | Read-only option contract reference returned by the platform. | 0 | 0 |
| `backend/src/qts/strategy_sdk/asset_resolver.py:38` | `property` | `qts.strategy_sdk.asset_resolver.OptionContractRef.instrument_id` | 未写 docstring；静态推断为所属类上的 `instrument id` 属性行为。 | 0 | 0 |
| `backend/src/qts/strategy_sdk/asset_resolver.py:41` | `class` | `qts.strategy_sdk.asset_resolver.OptionContractResolver` | Platform-provided option chain resolution boundary. | 0 | 0 |
| `backend/src/qts/strategy_sdk/asset_resolver.py:44` | `method` | `qts.strategy_sdk.asset_resolver.OptionContractResolver.find` | 未写 docstring；静态推断为所属类上的 `find` 行为。 | 0 | 0 |
| `backend/src/qts/strategy_sdk/asset_resolver.py:54` | `class` | `qts.strategy_sdk.asset_resolver.StrategyAssetResolver` | Resolve user input symbols/roots/options into stable `AssetRef` objects. | 0 | 0 |
| `backend/src/qts/strategy_sdk/asset_resolver.py:57` | `method` | `qts.strategy_sdk.asset_resolver.StrategyAssetResolver.__init__` | 未写 docstring；静态推断为所属类上的 `  init  ` 行为。 | 0 | 0 |
| `backend/src/qts/strategy_sdk/asset_resolver.py:68` | `method` | `qts.strategy_sdk.asset_resolver.StrategyAssetResolver.resolve_symbol` | Perform resolve_symbol. | 1 | 3 |
| `backend/src/qts/strategy_sdk/asset_resolver.py:75` | `method` | `qts.strategy_sdk.asset_resolver.StrategyAssetResolver.resolve_future` | Perform resolve_future. | 1 | 6 |
| `backend/src/qts/strategy_sdk/asset_resolver.py:93` | `method` | `qts.strategy_sdk.asset_resolver.StrategyAssetResolver.resolve_option` | Perform resolve_option. | 1 | 5 |
| `backend/src/qts/strategy_sdk/context.py:30` | `class` | `qts.strategy_sdk.context.StrategyContext` | User-facing strategy context. | 0 | 0 |
| `backend/src/qts/strategy_sdk/context.py:46` | `method` | `qts.strategy_sdk.context.StrategyContext.__post_init__` | Perform __post_init__. | 1 | 1 |
| `backend/src/qts/strategy_sdk/context.py:55` | `property` | `qts.strategy_sdk.context.StrategyContext.intents` | Perform intents. | 0 | 0 |
| `backend/src/qts/strategy_sdk/context.py:60` | `property` | `qts.strategy_sdk.context.StrategyContext.subscriptions` | Perform subscriptions. | 0 | 0 |
| `backend/src/qts/strategy_sdk/context.py:64` | `method` | `qts.strategy_sdk.context.StrategyContext.symbol` | Perform symbol. | 0 | 1 |
| `backend/src/qts/strategy_sdk/context.py:68` | `method` | `qts.strategy_sdk.context.StrategyContext.future` | Perform future. | 0 | 1 |
| `backend/src/qts/strategy_sdk/context.py:72` | `method` | `qts.strategy_sdk.context.StrategyContext.option` | Perform option. | 0 | 1 |
| `backend/src/qts/strategy_sdk/context.py:88` | `method` | `qts.strategy_sdk.context.StrategyContext.target_percent` | Perform target_percent. | 1 | 2 |
| `backend/src/qts/strategy_sdk/context.py:94` | `method` | `qts.strategy_sdk.context.StrategyContext.target_quantity` | Perform target_quantity. | 1 | 2 |
| `backend/src/qts/strategy_sdk/context.py:100` | `method` | `qts.strategy_sdk.context.StrategyContext.target_value` | Perform target_value. | 1 | 2 |
| `backend/src/qts/strategy_sdk/context.py:106` | `method` | `qts.strategy_sdk.context.StrategyContext.close` | Perform close. | 1 | 2 |
| `backend/src/qts/strategy_sdk/context.py:112` | `method` | `qts.strategy_sdk.context.StrategyContext.rebalance` | Perform rebalance. | 1 | 3 |
| `backend/src/qts/strategy_sdk/context.py:116` | `method` | `qts.strategy_sdk.context.StrategyContext.subscribe` | Perform subscribe. | 1 | 2 |
| `backend/src/qts/strategy_sdk/data_view.py:16` | `class` | `qts.strategy_sdk.data_view.DataView` | Time-sliced market data exposed to strategies. | 0 | 0 |
| `backend/src/qts/strategy_sdk/data_view.py:22` | `method` | `qts.strategy_sdk.data_view.DataView.close` | Perform close. | 1 | 1 |
| `backend/src/qts/strategy_sdk/data_view.py:26` | `method` | `qts.strategy_sdk.data_view.DataView.bar` | Perform bar. | 1 | 2 |
| `backend/src/qts/strategy_sdk/data_view.py:33` | `method` | `qts.strategy_sdk.data_view.DataView.history` | Perform history. | 0 | 3 |
| `backend/src/qts/strategy_sdk/factors.py:11` | `class` | `qts.strategy_sdk.factors.FactorFactory` | Factory for user-created factors. | 0 | 0 |
| `backend/src/qts/strategy_sdk/factors.py:14` | `method` | `qts.strategy_sdk.factors.FactorFactory.momentum` | Perform momentum. | 1 | 1 |
| `backend/src/qts/strategy_sdk/indicators.py:14` | `class` | `qts.strategy_sdk.indicators.AssetIndicator` | Indicator bound to a strategy asset reference. | 0 | 0 |
| `backend/src/qts/strategy_sdk/indicators.py:21` | `property` | `qts.strategy_sdk.indicators.AssetIndicator.ready` | Perform ready. | 0 | 0 |
| `backend/src/qts/strategy_sdk/indicators.py:26` | `property` | `qts.strategy_sdk.indicators.AssetIndicator.value` | Perform value. | 0 | 0 |
| `backend/src/qts/strategy_sdk/indicators.py:30` | `method` | `qts.strategy_sdk.indicators.AssetIndicator.update` | Perform update. | 0 | 1 |
| `backend/src/qts/strategy_sdk/indicators.py:36` | `class` | `qts.strategy_sdk.indicators.IndicatorFactory` | Factory for user-created indicators. | 0 | 0 |
| `backend/src/qts/strategy_sdk/indicators.py:41` | `method` | `qts.strategy_sdk.indicators.IndicatorFactory.sma` | Perform sma. | 2 | 3 |
| `backend/src/qts/strategy_sdk/indicators.py:47` | `method` | `qts.strategy_sdk.indicators.IndicatorFactory.update_from_bar` | Perform update_from_bar. | 0 | 1 |
| `backend/src/qts/strategy_sdk/portfolio_view.py:15` | `class` | `qts.strategy_sdk.portfolio_view.PortfolioPosition` | Read-only position snapshot. | 0 | 0 |
| `backend/src/qts/strategy_sdk/portfolio_view.py:23` | `class` | `qts.strategy_sdk.portfolio_view.PortfolioView` | Immutable user-facing portfolio snapshot. | 0 | 0 |
| `backend/src/qts/strategy_sdk/portfolio_view.py:30` | `method` | `qts.strategy_sdk.portfolio_view.PortfolioView.__post_init__` | Perform __post_init__. | 0 | 3 |
| `backend/src/qts/strategy_sdk/portfolio_view.py:34` | `method` | `qts.strategy_sdk.portfolio_view.PortfolioView.position` | Perform position. | 1 | 2 |
| `backend/src/qts/strategy_sdk/portfolio_view.py:38` | `method` | `qts.strategy_sdk.portfolio_view.PortfolioView.exposure` | Perform exposure. | 1 | 1 |
| `backend/src/qts/strategy_sdk/portfolio_view.py:42` | `method` | `qts.strategy_sdk.portfolio_view.PortfolioView.weight` | Perform weight. | 1 | 3 |
| `backend/src/qts/strategy_sdk/strategy.py:6` | `class` | `qts.strategy_sdk.strategy.Strategy` | Base class for user strategies. | 0 | 0 |
| `backend/src/qts/strategy_sdk/strategy.py:9` | `method` | `qts.strategy_sdk.strategy.Strategy.initialize` | Perform initialize. | 0 | 0 |
| `backend/src/qts/strategy_sdk/strategy.py:13` | `method` | `qts.strategy_sdk.strategy.Strategy.on_bar` | Perform on_bar. | 0 | 0 |
| `backend/src/qts/strategy_sdk/strategy.py:17` | `method` | `qts.strategy_sdk.strategy.Strategy.on_tick` | Perform on_tick. | 0 | 0 |
| `backend/src/qts/strategy_sdk/strategy.py:21` | `method` | `qts.strategy_sdk.strategy.Strategy.on_timer` | Perform on_timer. | 0 | 0 |
| `backend/src/qts/strategy_sdk/strategy.py:25` | `method` | `qts.strategy_sdk.strategy.Strategy.on_order_update` | Perform on_order_update. | 0 | 0 |
| `backend/src/qts/strategy_sdk/strategy.py:29` | `method` | `qts.strategy_sdk.strategy.Strategy.on_fill` | Perform on_fill. | 0 | 0 |
| `backend/src/qts/strategy_sdk/strategy.py:33` | `method` | `qts.strategy_sdk.strategy.Strategy.finalize` | Perform finalize. | 0 | 0 |
| `backend/src/qts/strategy_sdk/subscription_registry.py:11` | `class` | `qts.strategy_sdk.subscription_registry.DataSubscription` | Strategy-declared market data requirement. | 0 | 0 |
| `backend/src/qts/strategy_sdk/subscription_registry.py:18` | `method` | `qts.strategy_sdk.subscription_registry.DataSubscription.__post_init__` | Perform __post_init__. | 0 | 3 |
| `backend/src/qts/strategy_sdk/subscription_registry.py:26` | `class` | `qts.strategy_sdk.subscription_registry.StrategySubscriptionRegistry` | Own strategy subscriptions and enforce invariant validation. | 0 | 0 |
| `backend/src/qts/strategy_sdk/subscription_registry.py:29` | `method` | `qts.strategy_sdk.subscription_registry.StrategySubscriptionRegistry.__init__` | Perform __init__. | 0 | 0 |
| `backend/src/qts/strategy_sdk/subscription_registry.py:34` | `property` | `qts.strategy_sdk.subscription_registry.StrategySubscriptionRegistry.subscriptions` | Perform subscriptions. | 0 | 1 |
| `backend/src/qts/strategy_sdk/subscription_registry.py:38` | `method` | `qts.strategy_sdk.subscription_registry.StrategySubscriptionRegistry.subscribe` | Perform subscribe. | 0 | 1 |
| `backend/src/qts/strategy_sdk/target.py:12` | `class` | `qts.strategy_sdk.target.TargetIntentType` | Supported target intent kinds. | 0 | 0 |
| `backend/src/qts/strategy_sdk/target.py:22` | `class` | `qts.strategy_sdk.target.TargetIntent` | Strategy-emitted intent, later handled by platform risk/order flow. | 0 | 0 |
| `backend/src/qts/strategy_sdk/target_emitter.py:8` | `class` | `qts.strategy_sdk.target_emitter.TargetIntentEmitter` | Collect and emit `TargetIntent` values for one strategy context. | 0 | 0 |
| `backend/src/qts/strategy_sdk/target_emitter.py:11` | `method` | `qts.strategy_sdk.target_emitter.TargetIntentEmitter.__init__` | Perform __init__. | 0 | 0 |
| `backend/src/qts/strategy_sdk/target_emitter.py:16` | `property` | `qts.strategy_sdk.target_emitter.TargetIntentEmitter.intents` | Perform intents. | 0 | 1 |
| `backend/src/qts/strategy_sdk/target_emitter.py:20` | `method` | `qts.strategy_sdk.target_emitter.TargetIntentEmitter.emit` | Perform emit. | 0 | 1 |
| `examples/strategies/gc_si_momentum.py:12` | `class` | `examples.strategies.gc_si_momentum.GcSiMomentumStrategy` | Simple moving-average momentum strategy for configured GC/SI symbols. | 0 | 0 |
| `examples/strategies/gc_si_momentum.py:15` | `method` | `examples.strategies.gc_si_momentum.GcSiMomentumStrategy.__init__` | 未写 docstring；静态推断为所属类上的 `  init  ` 行为。 | 0 | 4 |
| `examples/strategies/gc_si_momentum.py:33` | `method` | `examples.strategies.gc_si_momentum.GcSiMomentumStrategy.initialize` | 未写 docstring；静态推断为所属类上的 `initialize` 行为。 | 1 | 3 |
| `examples/strategies/gc_si_momentum.py:38` | `method` | `examples.strategies.gc_si_momentum.GcSiMomentumStrategy.on_bar` | 未写 docstring；静态推断为所属类上的 `on bar` 行为。 | 1 | 7 |
| `examples/strategies/gc_si_momentum.py:55` | `module_function` | `examples.strategies.gc_si_momentum._average` | 未写 docstring；静态推断为 ` average` 函数，具体语义以实现为准。 | 0 | 5 |
| `examples/strategies/gc_si_momentum.py:60` | `module_function` | `examples.strategies.gc_si_momentum._asset_for_symbol` | 未写 docstring；静态推断为 ` asset for symbol` 函数，具体语义以实现为准。 | 0 | 2 |
| `examples/strategies/moving_average_cross.py:8` | `class` | `examples.strategies.moving_average_cross.MovingAverageCross` | 未写 docstring；静态推断为定义类对应的领域概念。 | 0 | 0 |
| `examples/strategies/moving_average_cross.py:9` | `method` | `examples.strategies.moving_average_cross.MovingAverageCross.initialize` | 未写 docstring；静态推断为所属类上的 `initialize` 行为。 | 0 | 3 |
| `examples/strategies/moving_average_cross.py:14` | `method` | `examples.strategies.moving_average_cross.MovingAverageCross.on_bar` | 未写 docstring；静态推断为所属类上的 `on bar` 行为。 | 0 | 6 |
| `scripts/bootstrap.py:11` | `module_function` | `scripts.bootstrap.main` | Perform main. | 1 | 2 |
| `scripts/run_api.py:9` | `module_function` | `scripts.run_api.main` | Start the QTS FastAPI application server. | 0 | 1 |
| `scripts/run_backtest.py:14` | `module_function` | `scripts.run_backtest.main` | Perform main. | 1 | 23 |
| `scripts/run_load.py:13` | `module_function` | `scripts.run_load.main` | Perform main. | 3 | 8 |
| `scripts/run_paper.py:8` | `module_function` | `scripts.run_paper.main` | Perform main. | 2 | 4 |
| `scripts/run_paper_ibkr.py:9` | `module_function` | `scripts.run_paper_ibkr.main` | Run the IBKR paper order lifecycle drill command. | 0 | 1 |
| `scripts/run_worker.py:7` | `module_function` | `scripts.run_worker.main` | Emit compatibility-mode worker message for now. | 0 | 1 |
| `scripts/validate_historical.py:15` | `module_function` | `scripts.validate_historical.main` | Perform main. | 2 | 25 |
| `scripts/verify_guardrails.py:22` | `module_function` | `scripts.verify_guardrails.main` | Perform main. | 1 | 1 |

### `qts.api.app`

模块：`qts.api.app`

#### `qts.api.app.create_app`
- 位置：`backend/src/qts/api/app.py:18`
- 类型：`module_function`
- 签名：`def create_app() -> FastAPI`
- 作用：Perform create_app.
- 直接原始调用：`app.include_router` x7, `FastAPI`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.api.mappers`

模块：`qts.api.mappers`

#### `qts.api.mappers.map_backtest_request_schema`
- 位置：`backend/src/qts/api/mappers.py:12`
- 类型：`module_function`
- 签名：`def map_backtest_request_schema(request: BacktestRequestSchema) -> BacktestRequestDTO`
- 作用：Map API input schema into an application DTO.
- 直接原始调用：`BacktestRequestDTO`
- 已解析到仓库内部的调用：`qts.application.dto.backtest.BacktestRequestDTO`
- 被以下仓库内部符号调用：`qts.api.routes.backtests.submit_backtest`

#### `qts.api.mappers.map_backtest_run_dto`
- 位置：`backend/src/qts/api/mappers.py:18`
- 类型：`module_function`
- 签名：`def map_backtest_run_dto(run: BacktestRunDTO) -> BacktestRunSchema`
- 作用：Map application output DTO into API response schema.
- 直接原始调用：`BacktestRunSchema`
- 已解析到仓库内部的调用：`qts.api.schemas.backtest_schema.BacktestRunSchema`
- 被以下仓库内部符号调用：`qts.api.routes.backtests.submit_backtest`

#### `qts.api.mappers.map_runtime_state_dto`
- 位置：`backend/src/qts/api/mappers.py:24`
- 类型：`module_function`
- 签名：`def map_runtime_state_dto(state: RuntimeStateDTO) -> dict[str, Any]`
- 作用：Map runtime state DTO into response payload.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.api.routes.operations.command`, `qts.api.routes.operations.pause_runtime`, `qts.api.routes.operations.resume_runtime`

#### `qts.api.mappers.map_kill_switch_state_dto`
- 位置：`backend/src/qts/api/mappers.py:30`
- 类型：`module_function`
- 签名：`def map_kill_switch_state_dto(state: KillSwitchStateDTO) -> dict[str, Any]`
- 作用：Map kill-switch state DTO into response payload.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.api.routes.operations.activate_kill_switch`

### `qts.api.routes.accounts`

模块：`qts.api.routes.accounts`

#### `qts.api.routes.accounts.account_snapshot`
- 位置：`backend/src/qts/api/routes/accounts.py:13`
- 类型：`module_function`
- 签名：`def account_snapshot(account_id: str) -> AccountSnapshotSchema`
- 作用：Perform account_snapshot.
- 直接原始调用：`AccountSnapshotSchema`
- 已解析到仓库内部的调用：`qts.api.schemas.common.AccountSnapshotSchema`
- 被以下仓库内部符号调用：无

### `qts.api.routes.backtests`

模块：`qts.api.routes.backtests`

#### `qts.api.routes.backtests.submit_backtest`
- 位置：`backend/src/qts/api/routes/backtests.py:19`
- 类型：`module_function`
- 签名：`def submit_backtest(request: BacktestRequestSchema) -> BacktestRunSchema`
- 作用：Submit a backtest request through the backtest application service.
- 直接原始调用：`BacktestService`, `BacktestService.submit`, `map_backtest_request_schema`, `map_backtest_run_dto`
- 已解析到仓库内部的调用：`qts.api.mappers.map_backtest_request_schema`, `qts.api.mappers.map_backtest_run_dto`
- 被以下仓库内部符号调用：无

### `qts.api.routes.health`

模块：`qts.api.routes.health`

#### `qts.api.routes.health.health`
- 位置：`backend/src/qts/api/routes/health.py:13`
- 类型：`module_function`
- 签名：`def health() -> dict[str, str]`
- 作用：Perform health.
- 直接原始调用：`HealthService`, `HealthService.status`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.api.routes.operations`

模块：`qts.api.routes.operations`

#### `qts.api.routes.operations.RuntimeCommandResponse`
- 位置：`backend/src/qts/api/routes/operations.py:21`
- 类型：`class`
- 签名：`class RuntimeCommandResponse(BaseModel)`
- 作用：Payload for runtime pause/resume commands.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.api.routes.operations.command`, `qts.api.routes.operations.pause_runtime`, `qts.api.routes.operations.resume_runtime`

#### `qts.api.routes.operations.KillSwitchScopeSchema`
- 位置：`backend/src/qts/api/routes/operations.py:27`
- 类型：`class`
- 签名：`class KillSwitchScopeSchema(StrEnum)`
- 作用：Kill-switch scoping model.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.api.routes.operations.KillSwitchCommand`
- 位置：`backend/src/qts/api/routes/operations.py:36`
- 类型：`class`
- 签名：`class KillSwitchCommand(BaseModel)`
- 作用：Kill-switch mutation command.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.api.routes.operations.KillSwitchCommand.validate_scope`
- 位置：`backend/src/qts/api/routes/operations.py:44`
- 类型：`method`
- 签名：`def validate_scope(self) -> KillSwitchCommand`
- 作用：Perform validate_scope.
- 直接原始调用：`ValueError` x2, `self.reason.strip`, `self.scope_id.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.api.routes.operations.KillSwitchResponse`
- 位置：`backend/src/qts/api/routes/operations.py:55`
- 类型：`class`
- 签名：`class KillSwitchResponse(BaseModel)`
- 作用：Kill-switch current state response.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.api.routes.operations.activate_kill_switch`

#### `qts.api.routes.operations._require_operator`
- 位置：`backend/src/qts/api/routes/operations.py:64`
- 类型：`module_function`
- 签名：`def _require_operator(operator: str | None) -> None`
- 作用：Perform _require_operator.
- 直接原始调用：`HTTPException`, `operator.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.api.routes.operations.activate_kill_switch`, `qts.api.routes.operations.pause_runtime`, `qts.api.routes.operations.resume_runtime`

#### `qts.api.routes.operations.pause_runtime`
- 位置：`backend/src/qts/api/routes/operations.py:71`
- 类型：`module_function`
- 签名：`def pause_runtime(idempotency_key: Annotated[str | None, Header(alias='Idempotency-Key')]=None, operator: Annotated[str | None, Header(alias='X-QTS-Operator')]=None) -> RuntimeCommandResponse`
- 作用：Pause runtime execution for all strategies and data actors.
- 直接原始调用：`RuntimeCommandResponse`, `_idempotency.run`, `_operations.pause_runtime`, `_require_operator`, `command`, `map_runtime_state_dto`
- 已解析到仓库内部的调用：`qts.api.routes.operations._require_operator`, `qts.api.mappers.map_runtime_state_dto`, `qts.api.routes.operations.RuntimeCommandResponse`, `qts.api.routes.operations.command`
- 被以下仓库内部符号调用：无

#### `qts.api.routes.operations.command`
- 位置：`backend/src/qts/api/routes/operations.py:78`
- 类型：`nested_function`
- 签名：`def command() -> RuntimeCommandResponse`
- 作用：Perform command.
- 直接原始调用：`RuntimeCommandResponse`, `_operations.pause_runtime`, `map_runtime_state_dto`
- 已解析到仓库内部的调用：`qts.api.mappers.map_runtime_state_dto`, `qts.api.routes.operations.RuntimeCommandResponse`
- 被以下仓库内部符号调用：`qts.api.routes.operations.pause_runtime`, `qts.api.routes.operations.resume_runtime`

#### `qts.api.routes.operations.resume_runtime`
- 位置：`backend/src/qts/api/routes/operations.py:90`
- 类型：`module_function`
- 签名：`def resume_runtime(idempotency_key: Annotated[str | None, Header(alias='Idempotency-Key')]=None, operator: Annotated[str | None, Header(alias='X-QTS-Operator')]=None) -> RuntimeCommandResponse`
- 作用：Resume runtime execution after an operator pause.
- 直接原始调用：`RuntimeCommandResponse`, `_idempotency.run`, `_operations.resume_runtime`, `_require_operator`, `command`, `map_runtime_state_dto`
- 已解析到仓库内部的调用：`qts.api.routes.operations._require_operator`, `qts.api.mappers.map_runtime_state_dto`, `qts.api.routes.operations.RuntimeCommandResponse`, `qts.api.routes.operations.command`
- 被以下仓库内部符号调用：无

#### `qts.api.routes.operations.command`
- 位置：`backend/src/qts/api/routes/operations.py:97`
- 类型：`nested_function`
- 签名：`def command() -> RuntimeCommandResponse`
- 作用：Perform command.
- 直接原始调用：`RuntimeCommandResponse`, `_operations.resume_runtime`, `map_runtime_state_dto`
- 已解析到仓库内部的调用：`qts.api.mappers.map_runtime_state_dto`, `qts.api.routes.operations.RuntimeCommandResponse`
- 被以下仓库内部符号调用：`qts.api.routes.operations.pause_runtime`, `qts.api.routes.operations.resume_runtime`

#### `qts.api.routes.operations.activate_kill_switch`
- 位置：`backend/src/qts/api/routes/operations.py:109`
- 类型：`module_function`
- 签名：`def activate_kill_switch(command: KillSwitchCommand, operator: Annotated[str | None, Header(alias='X-QTS-Operator')]=None) -> KillSwitchResponse`
- 作用：Activate or refresh a kill-switch for a runtime scope.
- 直接原始调用：`KillSwitchCommandDTO`, `KillSwitchResponse`, `_operations.activate_kill_switch`, `_require_operator`, `map_kill_switch_state_dto`
- 已解析到仓库内部的调用：`qts.api.routes.operations._require_operator`, `qts.api.mappers.map_kill_switch_state_dto`, `qts.api.routes.operations.KillSwitchResponse`
- 被以下仓库内部符号调用：无

### `qts.api.routes.orders`

模块：`qts.api.routes.orders`

#### `qts.api.routes.orders.order_status`
- 位置：`backend/src/qts/api/routes/orders.py:13`
- 类型：`module_function`
- 签名：`def order_status(order_id: str) -> OrderStatusSchema`
- 作用：Perform order_status.
- 直接原始调用：`OrderStatusSchema`
- 已解析到仓库内部的调用：`qts.api.schemas.common.OrderStatusSchema`
- 被以下仓库内部符号调用：无

### `qts.api.routes.strategies`

模块：`qts.api.routes.strategies`

#### `qts.api.routes.strategies.list_strategies`
- 位置：`backend/src/qts/api/routes/strategies.py:13`
- 类型：`module_function`
- 签名：`def list_strategies() -> list[StrategyStatusSchema]`
- 作用：Perform list_strategies.
- 直接原始调用：`StrategyStatusSchema`
- 已解析到仓库内部的调用：`qts.api.schemas.common.StrategyStatusSchema`
- 被以下仓库内部符号调用：无

#### `qts.api.routes.strategies.start_strategy`
- 位置：`backend/src/qts/api/routes/strategies.py:19`
- 类型：`module_function`
- 签名：`def start_strategy(strategy_id: str) -> StrategyStatusSchema`
- 作用：Perform start_strategy.
- 直接原始调用：`StrategyStatusSchema`
- 已解析到仓库内部的调用：`qts.api.schemas.common.StrategyStatusSchema`
- 被以下仓库内部符号调用：无

#### `qts.api.routes.strategies.stop_strategy`
- 位置：`backend/src/qts/api/routes/strategies.py:25`
- 类型：`module_function`
- 签名：`def stop_strategy(strategy_id: str) -> StrategyStatusSchema`
- 作用：Perform stop_strategy.
- 直接原始调用：`StrategyStatusSchema`
- 已解析到仓库内部的调用：`qts.api.schemas.common.StrategyStatusSchema`
- 被以下仓库内部符号调用：无

### `qts.api.schemas.backtest_schema`

模块：`qts.api.schemas.backtest_schema`

#### `qts.api.schemas.backtest_schema.BacktestRequestSchema`
- 位置：`backend/src/qts/api/schemas/backtest_schema.py:8`
- 类型：`class`
- 签名：`class BacktestRequestSchema(BaseModel)`
- 作用：HTTP request for submitting a backtest.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.api.schemas.backtest_schema.BacktestRunSchema`
- 位置：`backend/src/qts/api/schemas/backtest_schema.py:14`
- 类型：`class`
- 签名：`class BacktestRunSchema(BaseModel)`
- 作用：HTTP response for a submitted backtest.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.api.mappers.map_backtest_run_dto`

### `qts.api.schemas.common`

模块：`qts.api.schemas.common`

#### `qts.api.schemas.common.StrategyStatusSchema`
- 位置：`backend/src/qts/api/schemas/common.py:8`
- 类型：`class`
- 签名：`class StrategyStatusSchema(BaseModel)`
- 作用：Strategy status response schema.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.api.routes.strategies.list_strategies`, `qts.api.routes.strategies.start_strategy`, `qts.api.routes.strategies.stop_strategy`

#### `qts.api.schemas.common.AccountSnapshotSchema`
- 位置：`backend/src/qts/api/schemas/common.py:15`
- 类型：`class`
- 签名：`class AccountSnapshotSchema(BaseModel)`
- 作用：Account snapshot response schema.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.api.routes.accounts.account_snapshot`

#### `qts.api.schemas.common.OrderStatusSchema`
- 位置：`backend/src/qts/api/schemas/common.py:22`
- 类型：`class`
- 签名：`class OrderStatusSchema(BaseModel)`
- 作用：Order status response schema.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.api.routes.orders.order_status`

#### `qts.api.schemas.common.RiskRuleSchema`
- 位置：`backend/src/qts/api/schemas/common.py:29`
- 类型：`class`
- 签名：`class RiskRuleSchema(BaseModel)`
- 作用：Risk rule response schema.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.api.schemas.common.OperationalErrorSchema`
- 位置：`backend/src/qts/api/schemas/common.py:36`
- 类型：`class`
- 签名：`class OperationalErrorSchema(BaseModel)`
- 作用：Operational error response schema.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.api.schemas.common.OperationalErrorSchema.from_exception`
- 位置：`backend/src/qts/api/schemas/common.py:44`
- 类型：`classmethod`
- 签名：`def from_exception(cls, *, code: str, message: str, exc: Exception) -> OperationalErrorSchema`
- 作用：Perform from_exception.
- 直接原始调用：`cls`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.api.services.command_idempotency`

模块：`qts.api.services.command_idempotency`

#### `qts.api.services.command_idempotency.CommandIdempotencyStore`
- 位置：`backend/src/qts/api/services/command_idempotency.py:11`
- 类型：`class`
- 签名：`class CommandIdempotencyStore`
- 作用：Remember the first result for each command idempotency key.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.api.services.command_idempotency.CommandIdempotencyStore.__init__`
- 位置：`backend/src/qts/api/services/command_idempotency.py:14`
- 类型：`method`
- 签名：`def __init__(self) -> None`
- 作用：Perform __init__.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.api.services.command_idempotency.CommandIdempotencyStore.run`
- 位置：`backend/src/qts/api/services/command_idempotency.py:18`
- 类型：`method`
- 签名：`def run(self, key: str, command: Callable[[], T]) -> T`
- 作用：Perform run.
- 直接原始调用：`ValueError`, `command`, `key.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.api.websocket.dtos`

模块：`qts.api.websocket.dtos`

#### `qts.api.websocket.dtos.StreamEventDTO`
- 位置：`backend/src/qts/api/websocket/dtos.py:10`
- 类型：`class`
- 签名：`class StreamEventDTO`
- 作用：Public stream event DTO.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.api.websocket.fill_adapter.order_fill_to_stream_dto`

#### `qts.api.websocket.dtos.StreamEventDTO.__post_init__`
- 位置：`backend/src/qts/api/websocket/dtos.py:18`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：未写 docstring；静态推断为所属类上的 `  post init  ` 行为。
- 直接原始调用：`ValueError`, `self.event_type.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.api.websocket.events`

模块：`qts.api.websocket.events`

#### `qts.api.websocket.events.event_stream`
- 位置：`backend/src/qts/api/websocket/events.py:11`
- 类型：`async_module_function`
- 签名：`async def event_stream(websocket: WebSocket) -> None`
- 作用：Perform event_stream.
- 直接原始调用：`websocket.accept`, `websocket.close`, `websocket.send_json`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.api.websocket.fill_adapter`

模块：`qts.api.websocket.fill_adapter`

#### `qts.api.websocket.fill_adapter.order_fill_to_stream_dto`
- 位置：`backend/src/qts/api/websocket/fill_adapter.py:11`
- 类型：`module_function`
- 签名：`def order_fill_to_stream_dto(fill: OrderFillDTO, *, correlation_id: str | None=None) -> StreamEventDTO`
- 作用：Convert an OrderManager-validated fill into a public stream event DTO.
- 直接原始调用：`str` x2, `StreamEventDTO`, `datetime.now`
- 已解析到仓库内部的调用：`qts.api.websocket.dtos.StreamEventDTO`
- 被以下仓库内部符号调用：无

### `qts.api.websocket.manager`

模块：`qts.api.websocket.manager`

#### `qts.api.websocket.manager.JsonWebSocket`
- 位置：`backend/src/qts/api/websocket/manager.py:8`
- 类型：`class`
- 签名：`class JsonWebSocket(Protocol)`
- 作用：Minimal WebSocket protocol used by the connection manager.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.api.websocket.manager.JsonWebSocket.accept`
- 位置：`backend/src/qts/api/websocket/manager.py:11`
- 类型：`async_method`
- 签名：`async def accept(self) -> None`
- 作用：Accept the WebSocket connection.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.api.websocket.manager.JsonWebSocket.send_json`
- 位置：`backend/src/qts/api/websocket/manager.py:15`
- 类型：`async_method`
- 签名：`async def send_json(self, data: object) -> None`
- 作用：Send a JSON-serializable payload.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.api.websocket.manager.WebSocketConnectionManager`
- 位置：`backend/src/qts/api/websocket/manager.py:20`
- 类型：`class`
- 签名：`class WebSocketConnectionManager`
- 作用：Track WebSocket clients and broadcast JSON payloads.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.api.websocket.manager.WebSocketConnectionManager.__init__`
- 位置：`backend/src/qts/api/websocket/manager.py:23`
- 类型：`method`
- 签名：`def __init__(self) -> None`
- 作用：未写 docstring；静态推断为所属类上的 `  init  ` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.api.websocket.manager.WebSocketConnectionManager.count`
- 位置：`backend/src/qts/api/websocket/manager.py:27`
- 类型：`property`
- 签名：`def count(self) -> int`
- 作用：Perform count.
- 直接原始调用：`len`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.api.websocket.manager.WebSocketConnectionManager.connect`
- 位置：`backend/src/qts/api/websocket/manager.py:31`
- 类型：`async_method`
- 签名：`async def connect(self, websocket: JsonWebSocket) -> None`
- 作用：Perform connect.
- 直接原始调用：`self._connections.append`, `websocket.accept`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.api.websocket.manager.WebSocketConnectionManager.disconnect`
- 位置：`backend/src/qts/api/websocket/manager.py:36`
- 类型：`method`
- 签名：`def disconnect(self, websocket: JsonWebSocket) -> None`
- 作用：Perform disconnect.
- 直接原始调用：`self._connections.remove`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.api.websocket.manager.WebSocketConnectionManager.broadcast`

#### `qts.api.websocket.manager.WebSocketConnectionManager.broadcast`
- 位置：`backend/src/qts/api/websocket/manager.py:41`
- 类型：`async_method`
- 签名：`async def broadcast(self, payload: object) -> None`
- 作用：Perform broadcast.
- 直接原始调用：`self.disconnect`, `stale.append`, `tuple`, `websocket.send_json`
- 已解析到仓库内部的调用：`qts.api.websocket.manager.WebSocketConnectionManager.disconnect`
- 被以下仓库内部符号调用：无

### `qts.application.commands.ibkr_environment_evidence`

模块：`qts.application.commands.ibkr_environment_evidence`

#### `qts.application.commands.ibkr_environment_evidence.collect_environment_evidence`
- 位置：`backend/src/qts/application/commands/ibkr_environment_evidence.py:26`
- 类型：`module_function`
- 签名：`def collect_environment_evidence(*, config_path: Path=DEFAULT_CONFIG_PATH, output_dir: Path=DEFAULT_OUTPUT_DIR, dry_run: bool=False, label: str | None=None, timeout_seconds: float=2.0) -> Path`
- 作用：Collect observe-only evidence and return the output path.
- 直接原始调用：`_collect_network_evidence`, `_evidence_filename`, `_merge_validation_errors`, `_read_config`, `_summarize_config`, `datetime.now`, `evidence_path.write_text`, `generated_at.isoformat`, `json.dumps`, `output_dir.mkdir`, `str`
- 已解析到仓库内部的调用：`qts.application.commands.ibkr_environment_evidence._read_config`, `qts.application.commands.ibkr_environment_evidence._merge_validation_errors`, `qts.application.commands.ibkr_environment_evidence._collect_network_evidence`, `qts.application.commands.ibkr_environment_evidence._summarize_config`, `qts.application.commands.ibkr_environment_evidence._evidence_filename`
- 被以下仓库内部符号调用：`qts.application.commands.ibkr_environment_evidence.main`

#### `qts.application.commands.ibkr_environment_evidence.main`
- 位置：`backend/src/qts/application/commands/ibkr_environment_evidence.py:77`
- 类型：`module_function`
- 签名：`def main() -> None`
- 作用：CLI entrypoint for IBKR environment evidence collection.
- 直接原始调用：`parser.add_argument` x5, `argparse.ArgumentParser`, `collect_environment_evidence`, `parser.parse_args`, `print`
- 已解析到仓库内部的调用：`qts.application.commands.ibkr_environment_evidence.collect_environment_evidence`
- 被以下仓库内部符号调用：无

#### `qts.application.commands.ibkr_environment_evidence._read_config`
- 位置：`backend/src/qts/application/commands/ibkr_environment_evidence.py:120`
- 类型：`module_function`
- 签名：`def _read_config(config_path: Path) -> tuple[IbkrEnvironmentConfig | None, list[str]]`
- 作用：Perform _read_config.
- 直接原始调用：`IbkrEnvironmentConfig.from_yaml`, `str`
- 已解析到仓库内部的调用：`qts.config.ibkr.IbkrEnvironmentConfig.from_yaml`
- 被以下仓库内部符号调用：`qts.application.commands.ibkr_environment_evidence.collect_environment_evidence`

#### `qts.application.commands.ibkr_environment_evidence._summarize_config`
- 位置：`backend/src/qts/application/commands/ibkr_environment_evidence.py:130`
- 类型：`module_function`
- 签名：`def _summarize_config(config: IbkrEnvironmentConfig | None) -> JsonObject`
- 作用：Perform _summarize_config.
- 直接原始调用：`_env_ref_status`, `bool`
- 已解析到仓库内部的调用：`qts.application.commands.ibkr_environment_evidence._env_ref_status`
- 被以下仓库内部符号调用：`qts.application.commands.ibkr_environment_evidence.collect_environment_evidence`

#### `qts.application.commands.ibkr_environment_evidence._merge_validation_errors`
- 位置：`backend/src/qts/application/commands/ibkr_environment_evidence.py:166`
- 类型：`module_function`
- 签名：`def _merge_validation_errors(parse_errors: list[str], config: IbkrEnvironmentConfig | None) -> list[str]`
- 作用：Perform _merge_validation_errors.
- 直接原始调用：`collect_validation_errors`
- 已解析到仓库内部的调用：`qts.config.ibkr.collect_validation_errors`
- 被以下仓库内部符号调用：`qts.application.commands.ibkr_environment_evidence.collect_environment_evidence`

#### `qts.application.commands.ibkr_environment_evidence._collect_network_evidence`
- 位置：`backend/src/qts/application/commands/ibkr_environment_evidence.py:178`
- 类型：`module_function`
- 签名：`def _collect_network_evidence(config: IbkrEnvironmentConfig | None, *, dry_run: bool, timeout_seconds: float) -> JsonObject`
- 作用：Perform _collect_network_evidence.
- 直接原始调用：`_tcp_probe` x2
- 已解析到仓库内部的调用：`qts.application.commands.ibkr_environment_evidence._tcp_probe`
- 被以下仓库内部符号调用：`qts.application.commands.ibkr_environment_evidence.collect_environment_evidence`

#### `qts.application.commands.ibkr_environment_evidence._tcp_probe`
- 位置：`backend/src/qts/application/commands/ibkr_environment_evidence.py:222`
- 类型：`module_function`
- 签名：`def _tcp_probe(connection: JsonObject, timeout_seconds: float) -> JsonObject`
- 作用：Perform _tcp_probe.
- 直接原始调用：`connection.get` x2, `str` x2, `isinstance`, `sock.close`, `socket.create_connection`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.application.commands.ibkr_environment_evidence._collect_network_evidence`

#### `qts.application.commands.ibkr_environment_evidence._env_ref_status`
- 位置：`backend/src/qts/application/commands/ibkr_environment_evidence.py:247`
- 类型：`module_function`
- 签名：`def _env_ref_status(name: str) -> JsonObject`
- 作用：Perform _env_ref_status.
- 直接原始调用：`bool`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.application.commands.ibkr_environment_evidence._summarize_config`

#### `qts.application.commands.ibkr_environment_evidence._evidence_filename`
- 位置：`backend/src/qts/application/commands/ibkr_environment_evidence.py:252`
- 类型：`module_function`
- 签名：`def _evidence_filename(generated_at: datetime, label: str | None) -> str`
- 作用：Perform _evidence_filename.
- 直接原始调用：`_safe_label`, `generated_at.strftime`
- 已解析到仓库内部的调用：`qts.application.commands.ibkr_environment_evidence._safe_label`
- 被以下仓库内部符号调用：`qts.application.commands.ibkr_environment_evidence.collect_environment_evidence`

#### `qts.application.commands.ibkr_environment_evidence._safe_label`
- 位置：`backend/src/qts/application/commands/ibkr_environment_evidence.py:259`
- 类型：`module_function`
- 签名：`def _safe_label(label: str | None) -> str`
- 作用：Perform _safe_label.
- 直接原始调用：`label.strip`, `re.sub`, `re.sub.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.application.commands.ibkr_environment_evidence._evidence_filename`

### `qts.application.commands.ibkr_paper_order_lifecycle_drill`

模块：`qts.application.commands.ibkr_paper_order_lifecycle_drill`

#### `qts.application.commands.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill`
- 位置：`backend/src/qts/application/commands/ibkr_paper_order_lifecycle_drill.py:31`
- 类型：`module_function`
- 签名：`def run_paper_order_lifecycle_drill(*, config_path: Path=DEFAULT_CONFIG_PATH, output_dir: Path=DEFAULT_OUTPUT_DIR, label: str | None=None, instrument_id: str='EQUITY.US.NASDAQ.AAPL', broker_symbol: str='AAPL', side: str='buy', quantity: Decimal=Decimal('1'), limit_price: Decimal=Decimal('1')) -> Path`
- 作用：Run a paper-only order-lifecycle drill and persist evidence.
- 直接原始调用：`str` x3, `Decimal` x2, `ValueError` x2, `_execution_report_evidence` x2, `manager.process_report` x2, `normalize_broker_execution_report` x2, `AccountId`, `BrokerId`, `BrokerOrderRequest`, `CancelIntent`, `FakeBrokerAdapter`, `InstrumentId`, `OrderId`, `OrderIntent`, `OrderManager`, `OrderSide`, `RiskDecision.approve`, `StrategyId`, `_evidence_filename`, `_read_config`, `_summarize_config`, `_validate_paper_only_ibkr_config`, `broker.cancel_order`, `broker.submit_order`, `datetime.now`, `evidence_path.write_text`, `generated_at.isoformat`, `generated_at.strftime`, `json.dumps`, `manager.create_order`, `manager.mark_sent`, `manager.request_cancel`, `output_dir.mkdir`
- 已解析到仓库内部的调用：`qts.application.commands.ibkr_paper_order_lifecycle_drill._read_config`, `qts.application.commands.ibkr_paper_order_lifecycle_drill._validate_paper_only_ibkr_config`, `qts.core.ids.OrderId`, `qts.core.ids.AccountId`, `qts.core.ids.InstrumentId`, `qts.execution.order_manager.OrderManager`, `qts.execution.broker.FakeBrokerAdapter`, `qts.core.ids.BrokerId`, `qts.execution.broker.BrokerOrderRequest`, `qts.core.ids.StrategyId`, `qts.execution.broker.normalize_broker_execution_report`, `qts.application.commands.ibkr_paper_order_lifecycle_drill._summarize_config`, `qts.application.commands.ibkr_paper_order_lifecycle_drill._execution_report_evidence`, `qts.application.commands.ibkr_paper_order_lifecycle_drill._evidence_filename`
- 被以下仓库内部符号调用：`qts.application.commands.ibkr_paper_order_lifecycle_drill.main`

#### `qts.application.commands.ibkr_paper_order_lifecycle_drill.main`
- 位置：`backend/src/qts/application/commands/ibkr_paper_order_lifecycle_drill.py:142`
- 类型：`module_function`
- 签名：`def main() -> None`
- 作用：CLI entrypoint for paper order lifecycle evidence.
- 直接原始调用：`parser.add_argument` x8, `Decimal` x2, `argparse.ArgumentParser`, `parser.parse_args`, `print`, `run_paper_order_lifecycle_drill`
- 已解析到仓库内部的调用：`qts.application.commands.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill`
- 被以下仓库内部符号调用：无

#### `qts.application.commands.ibkr_paper_order_lifecycle_drill._read_config`
- 位置：`backend/src/qts/application/commands/ibkr_paper_order_lifecycle_drill.py:187`
- 类型：`module_function`
- 签名：`def _read_config(config_path: Path) -> tuple[IbkrEnvironmentConfig | None, list[str]]`
- 作用：Perform _read_config.
- 直接原始调用：`IbkrEnvironmentConfig.from_yaml`, `str`
- 已解析到仓库内部的调用：`qts.config.ibkr.IbkrEnvironmentConfig.from_yaml`
- 被以下仓库内部符号调用：`qts.application.commands.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill`

#### `qts.application.commands.ibkr_paper_order_lifecycle_drill._validate_paper_only_ibkr_config`
- 位置：`backend/src/qts/application/commands/ibkr_paper_order_lifecycle_drill.py:197`
- 类型：`module_function`
- 签名：`def _validate_paper_only_ibkr_config(config: IbkrEnvironmentConfig | None, parse_errors: list[str]) -> None`
- 作用：Perform _validate_paper_only_ibkr_config.
- 直接原始调用：`'; '.join` x3, `ValueError` x3, `errors.append` x3, `errors.extend` x2, `collect_validation_errors`, `config.order_execution.account_id.upper`, `config.order_execution.account_id.upper.startswith`
- 已解析到仓库内部的调用：`qts.config.ibkr.collect_validation_errors`
- 被以下仓库内部符号调用：`qts.application.commands.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill`

#### `qts.application.commands.ibkr_paper_order_lifecycle_drill._summarize_config`
- 位置：`backend/src/qts/application/commands/ibkr_paper_order_lifecycle_drill.py:221`
- 类型：`module_function`
- 签名：`def _summarize_config(config: IbkrEnvironmentConfig) -> JsonObject`
- 作用：Perform _summarize_config.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.application.commands.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill`

#### `qts.application.commands.ibkr_paper_order_lifecycle_drill._execution_report_evidence`
- 位置：`backend/src/qts/application/commands/ibkr_paper_order_lifecycle_drill.py:237`
- 类型：`module_function`
- 签名：`def _execution_report_evidence(report: ExecutionReport) -> JsonObject`
- 作用：Perform _execution_report_evidence.
- 直接原始调用：`str` x2, `TypeError`, `isinstance`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.application.commands.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill`

#### `qts.application.commands.ibkr_paper_order_lifecycle_drill._evidence_filename`
- 位置：`backend/src/qts/application/commands/ibkr_paper_order_lifecycle_drill.py:251`
- 类型：`module_function`
- 签名：`def _evidence_filename(generated_at: datetime, label: str | None) -> str`
- 作用：Perform _evidence_filename.
- 直接原始调用：`_safe_label`, `generated_at.strftime`
- 已解析到仓库内部的调用：`qts.application.commands.ibkr_paper_order_lifecycle_drill._safe_label`
- 被以下仓库内部符号调用：`qts.application.commands.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill`

#### `qts.application.commands.ibkr_paper_order_lifecycle_drill._safe_label`
- 位置：`backend/src/qts/application/commands/ibkr_paper_order_lifecycle_drill.py:258`
- 类型：`module_function`
- 签名：`def _safe_label(label: str | None) -> str`
- 作用：Perform _safe_label.
- 直接原始调用：`label.strip`, `re.sub`, `re.sub.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.application.commands.ibkr_paper_order_lifecycle_drill._evidence_filename`

### `qts.application.commands.start_paper`

模块：`qts.application.commands.start_paper`

#### `qts.application.commands.start_paper.PaperRuntimeConfig`
- 位置：`backend/src/qts/application/commands/start_paper.py:10`
- 类型：`class`
- 签名：`class PaperRuntimeConfig`
- 作用：Paper runtime configuration without real broker credentials.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`scripts.run_paper.main`

#### `qts.application.commands.start_paper.PaperRuntimeConfig.__post_init__`
- 位置：`backend/src/qts/application/commands/start_paper.py:18`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError` x3, `Decimal`, `self.account_id.strip`, `self.data_source.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.application.commands.start_paper.PaperRuntime`
- 位置：`backend/src/qts/application/commands/start_paper.py:29`
- 类型：`class`
- 签名：`class PaperRuntime`
- 作用：Constructed paper runtime descriptor.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.application.commands.start_paper.start_paper`

#### `qts.application.commands.start_paper.start_paper`
- 位置：`backend/src/qts/application/commands/start_paper.py:36`
- 类型：`module_function`
- 签名：`def start_paper(config: PaperRuntimeConfig) -> PaperRuntime`
- 作用：Construct the paper runtime boundary without connecting to a real broker.
- 直接原始调用：`PaperRuntime`
- 已解析到仓库内部的调用：`qts.application.commands.start_paper.PaperRuntime`
- 被以下仓库内部符号调用：`scripts.run_paper.main`

### `qts.application.dto.backtest`

模块：`qts.application.dto.backtest`

#### `qts.application.dto.backtest.BacktestRequestDTO`
- 位置：`backend/src/qts/application/dto/backtest.py:9`
- 类型：`class`
- 签名：`class BacktestRequestDTO`
- 作用：Stable application request for starting a backtest.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.api.mappers.map_backtest_request_schema`

#### `qts.application.dto.backtest.BacktestRequestDTO.__post_init__`
- 位置：`backend/src/qts/application/dto/backtest.py:14`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError`, `self.strategy_name.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.application.dto.backtest.BacktestRunDTO`
- 位置：`backend/src/qts/application/dto/backtest.py:21`
- 类型：`class`
- 签名：`class BacktestRunDTO`
- 作用：Stable application response for a submitted backtest.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.application.dto.health`

模块：`qts.application.dto.health`

#### `qts.application.dto.health.HealthStatusDTO`
- 位置：`backend/src/qts/application/dto/health.py:9`
- 类型：`class`
- 签名：`class HealthStatusDTO`
- 作用：Stable health status response.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.application.dto.operations`

模块：`qts.application.dto.operations`

#### `qts.application.dto.operations.RuntimeStateDTO`
- 位置：`backend/src/qts/application/dto/operations.py:9`
- 类型：`class`
- 签名：`class RuntimeStateDTO`
- 作用：Stable runtime state response.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.application.dto.operations.KillSwitchCommandDTO`
- 位置：`backend/src/qts/application/dto/operations.py:16`
- 类型：`class`
- 签名：`class KillSwitchCommandDTO`
- 作用：Stable kill-switch activation request.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.application.dto.operations.KillSwitchCommandDTO.__post_init__`
- 位置：`backend/src/qts/application/dto/operations.py:23`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError` x3, `self.reason.strip`, `self.scope.strip`, `self.scope_id.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.application.dto.operations.KillSwitchStateDTO`
- 位置：`backend/src/qts/application/dto/operations.py:34`
- 类型：`class`
- 签名：`class KillSwitchStateDTO`
- 作用：Stable kill-switch state response.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.application.dto.order_events`

模块：`qts.application.dto.order_events`

#### `qts.application.dto.order_events.OrderFillDTO`
- 位置：`backend/src/qts/application/dto/order_events.py:10`
- 类型：`class`
- 签名：`class OrderFillDTO`
- 作用：Stable fill event shape for public streams.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.application.dto.order_events.OrderFillDTO.__post_init__`
- 位置：`backend/src/qts/application/dto/order_events.py:20`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError` x4, `self.fill_id.strip`, `self.instrument_id.strip`, `self.order_id.strip`, `self.side.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.application.services.backtest`

模块：`qts.application.services.backtest`

#### `qts.application.services.backtest.BacktestService`
- 位置：`backend/src/qts/application/services/backtest.py:10`
- 类型：`class`
- 签名：`class BacktestService`
- 作用：Application boundary for backtest use cases.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.application.services.backtest.BacktestService.__init__`
- 位置：`backend/src/qts/application/services/backtest.py:13`
- 类型：`method`
- 签名：`def __init__(self) -> None`
- 作用：Perform __init__.
- 直接原始调用：`count`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.application.services.backtest.BacktestService.submit`
- 位置：`backend/src/qts/application/services/backtest.py:17`
- 类型：`method`
- 签名：`def submit(self, request: BacktestRequestDTO) -> BacktestRunDTO`
- 作用：Perform submit.
- 直接原始调用：`BacktestRunDTO`, `next`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.application.services.health`

模块：`qts.application.services.health`

#### `qts.application.services.health.HealthService`
- 位置：`backend/src/qts/application/services/health.py:8`
- 类型：`class`
- 签名：`class HealthService`
- 作用：Returns platform health without exposing internals.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.application.services.health.HealthService.status`
- 位置：`backend/src/qts/application/services/health.py:11`
- 类型：`method`
- 签名：`def status(self) -> HealthStatusDTO`
- 作用：Perform status.
- 直接原始调用：`HealthStatusDTO`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.application.services.interfaces`

模块：`qts.application.services.interfaces`

#### `qts.application.services.interfaces.AccountService`
- 位置：`backend/src/qts/application/services/interfaces.py:8`
- 类型：`class`
- 签名：`class AccountService(Protocol)`
- 作用：Account query service boundary.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.application.services.interfaces.AccountService.snapshot`
- 位置：`backend/src/qts/application/services/interfaces.py:11`
- 类型：`method`
- 签名：`def snapshot(self, account_id: str) -> object`
- 作用：Return an account snapshot.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.application.services.interfaces.OrderService`
- 位置：`backend/src/qts/application/services/interfaces.py:16`
- 类型：`class`
- 签名：`class OrderService(Protocol)`
- 作用：Order query service boundary.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.application.services.interfaces.OrderService.status`
- 位置：`backend/src/qts/application/services/interfaces.py:19`
- 类型：`method`
- 签名：`def status(self, order_id: str) -> object`
- 作用：Return order status.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.application.services.interfaces.RiskService`
- 位置：`backend/src/qts/application/services/interfaces.py:24`
- 类型：`class`
- 签名：`class RiskService(Protocol)`
- 作用：Risk query service boundary.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.application.services.interfaces.RiskService.rules`
- 位置：`backend/src/qts/application/services/interfaces.py:27`
- 类型：`method`
- 签名：`def rules(self, account_id: str) -> object`
- 作用：Return configured risk rules.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.application.services.operations`

模块：`qts.application.services.operations`

#### `qts.application.services.operations.OperationsService`
- 位置：`backend/src/qts/application/services/operations.py:9`
- 类型：`class`
- 签名：`class OperationsService`
- 作用：Owns operational state without leaking runtime internals into API routes.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.application.services.operations.OperationsService.__init__`
- 位置：`backend/src/qts/application/services/operations.py:12`
- 类型：`method`
- 签名：`def __init__(self, *, kill_switches: KillSwitchRegistry | None=None) -> None`
- 作用：Perform __init__.
- 直接原始调用：`KillSwitchRegistry`
- 已解析到仓库内部的调用：`qts.risk.kill_switch.KillSwitchRegistry`
- 被以下仓库内部符号调用：无

#### `qts.application.services.operations.OperationsService.pause_runtime`
- 位置：`backend/src/qts/application/services/operations.py:17`
- 类型：`method`
- 签名：`def pause_runtime(self) -> RuntimeStateDTO`
- 作用：Perform pause_runtime.
- 直接原始调用：`RuntimeStateDTO`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.application.services.operations.OperationsService.resume_runtime`
- 位置：`backend/src/qts/application/services/operations.py:22`
- 类型：`method`
- 签名：`def resume_runtime(self) -> RuntimeStateDTO`
- 作用：Perform resume_runtime.
- 直接原始调用：`RuntimeStateDTO`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.application.services.operations.OperationsService.activate_kill_switch`
- 位置：`backend/src/qts/application/services/operations.py:27`
- 类型：`method`
- 签名：`def activate_kill_switch(self, command: KillSwitchCommandDTO) -> KillSwitchStateDTO`
- 作用：Perform activate_kill_switch.
- 直接原始调用：`KillSwitchStateDTO`, `self._kill_switches.activate`, `self._scope_from_command`
- 已解析到仓库内部的调用：`qts.application.services.operations.OperationsService._scope_from_command`
- 被以下仓库内部符号调用：无

#### `qts.application.services.operations.OperationsService._scope_from_command`
- 位置：`backend/src/qts/application/services/operations.py:39`
- 类型：`staticmethod`
- 签名：`def _scope_from_command(command: KillSwitchCommandDTO) -> KillSwitchScope`
- 作用：Perform _scope_from_command.
- 直接原始调用：`KillSwitchScope`, `KillSwitchScope.global_scope`, `KillSwitchScopeType`
- 已解析到仓库内部的调用：`qts.risk.kill_switch.KillSwitchScopeType`, `qts.risk.kill_switch.KillSwitchScope.global_scope`, `qts.risk.kill_switch.KillSwitchScope`
- 被以下仓库内部符号调用：`qts.application.services.operations.OperationsService.activate_kill_switch`

### `qts.application.services.strategy_service`

模块：`qts.application.services.strategy_service`

#### `qts.application.services.strategy_service.StrategyLifecycleService`
- 位置：`backend/src/qts/application/services/strategy_service.py:9`
- 类型：`class`
- 签名：`class StrategyLifecycleService`
- 作用：Start, stop, and inspect configured strategy instances.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.application.services.strategy_service.StrategyLifecycleService.__init__`
- 位置：`backend/src/qts/application/services/strategy_service.py:12`
- 类型：`method`
- 签名：`def __init__(self, instances: tuple[StrategyInstance, ...]=()) -> None`
- 作用：Perform __init__.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.application.services.strategy_service.StrategyLifecycleService.add`
- 位置：`backend/src/qts/application/services/strategy_service.py:21`
- 类型：`method`
- 签名：`def add(self, instance: StrategyInstance) -> None`
- 作用：Perform add.
- 直接原始调用：`ValueError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.application.services.strategy_service.StrategyLifecycleService.start`
- 位置：`backend/src/qts/application/services/strategy_service.py:29`
- 类型：`method`
- 签名：`def start(self, strategy_id: StrategyId) -> StrategyStatus`
- 作用：Perform start.
- 直接原始调用：`self._require_enabled`
- 已解析到仓库内部的调用：`qts.application.services.strategy_service.StrategyLifecycleService._require_enabled`
- 被以下仓库内部符号调用：无

#### `qts.application.services.strategy_service.StrategyLifecycleService.stop`
- 位置：`backend/src/qts/application/services/strategy_service.py:35`
- 类型：`method`
- 签名：`def stop(self, strategy_id: StrategyId) -> StrategyStatus`
- 作用：Perform stop.
- 直接原始调用：`self._require_enabled`
- 已解析到仓库内部的调用：`qts.application.services.strategy_service.StrategyLifecycleService._require_enabled`
- 被以下仓库内部符号调用：无

#### `qts.application.services.strategy_service.StrategyLifecycleService.status`
- 位置：`backend/src/qts/application/services/strategy_service.py:41`
- 类型：`method`
- 签名：`def status(self, strategy_id: StrategyId) -> StrategyStatus`
- 作用：Perform status.
- 直接原始调用：`self._require_enabled`
- 已解析到仓库内部的调用：`qts.application.services.strategy_service.StrategyLifecycleService._require_enabled`
- 被以下仓库内部符号调用：无

#### `qts.application.services.strategy_service.StrategyLifecycleService.list_instances`
- 位置：`backend/src/qts/application/services/strategy_service.py:46`
- 类型：`method`
- 签名：`def list_instances(self) -> tuple[StrategyInstance, ...]`
- 作用：Perform list_instances.
- 直接原始调用：`self._instances.values`, `tuple`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.application.services.strategy_service.StrategyLifecycleService._require_enabled`
- 位置：`backend/src/qts/application/services/strategy_service.py:50`
- 类型：`method`
- 签名：`def _require_enabled(self, strategy_id: StrategyId) -> None`
- 作用：Perform _require_enabled.
- 直接原始调用：`ValueError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.application.services.strategy_service.StrategyLifecycleService.start`, `qts.application.services.strategy_service.StrategyLifecycleService.status`, `qts.application.services.strategy_service.StrategyLifecycleService.stop`

### `qts.application.strategy_lifecycle`

模块：`qts.application.strategy_lifecycle`

#### `qts.application.strategy_lifecycle.StrategyStatus`
- 位置：`backend/src/qts/application/strategy_lifecycle.py:14`
- 类型：`class`
- 签名：`class StrategyStatus(StrEnum)`
- 作用：Configured strategy instance lifecycle status.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.application.strategy_lifecycle.StrategyInstance`
- 位置：`backend/src/qts/application/strategy_lifecycle.py:22`
- 类型：`class`
- 签名：`class StrategyInstance`
- 作用：Configured runtime instance of a Strategy class.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.application.strategy_lifecycle.StrategyInstance.__post_init__`
- 位置：`backend/src/qts/application/strategy_lifecycle.py:32`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError` x2, `Decimal`, `self.class_path.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.application.strategy_lifecycle.StrategyRegistry`
- 位置：`backend/src/qts/application/strategy_lifecycle.py:40`
- 类型：`class`
- 签名：`class StrategyRegistry`
- 作用：Safe registry for explicitly approved strategy classes.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.application.strategy_lifecycle.StrategyRegistry.__init__`
- 位置：`backend/src/qts/application/strategy_lifecycle.py:43`
- 类型：`method`
- 签名：`def __init__(self) -> None`
- 作用：Perform __init__.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.application.strategy_lifecycle.StrategyRegistry.register`
- 位置：`backend/src/qts/application/strategy_lifecycle.py:47`
- 类型：`method`
- 签名：`def register(self, class_path: str, strategy_cls: type[Strategy]) -> None`
- 作用：Perform register.
- 直接原始调用：`ValueError` x2, `class_path.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.application.strategy_lifecycle.StrategyRegistry.resolve`
- 位置：`backend/src/qts/application/strategy_lifecycle.py:55`
- 类型：`method`
- 签名：`def resolve(self, class_path: str) -> type[Strategy]`
- 作用：Perform resolve.
- 直接原始调用：`KeyError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.backtest.actor_loop`

模块：`qts.backtest.actor_loop`

#### `qts.backtest.actor_loop.BacktestActorLoopResult`
- 位置：`backend/src/qts/backtest/actor_loop.py:44`
- 类型：`class`
- 签名：`class BacktestActorLoopResult`
- 作用：Result summary produced by an actor loop run.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.actor_loop.BacktestActorLoop.run`

#### `qts.backtest.actor_loop.BacktestActorLoopResult.processed_bars`
- 位置：`backend/src/qts/backtest/actor_loop.py:53`
- 类型：`property`
- 签名：`def processed_bars(self) -> int`
- 作用：Perform processed_bars.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.actor_loop.BacktestActorLoop`
- 位置：`backend/src/qts/backtest/actor_loop.py:58`
- 类型：`class`
- 签名：`class BacktestActorLoop`
- 作用：Run backtest bars through strategy/order execution actors.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine.run_streaming`

#### `qts.backtest.actor_loop.BacktestActorLoop.__init__`
- 位置：`backend/src/qts/backtest/actor_loop.py:61`
- 类型：`method`
- 签名：`def __init__(self, *, strategy: Strategy, bars: Iterable[Bar], initial_cash: Decimal, target_timeframe: str | None=None, exchange_timezone_by_instrument: Mapping[InstrumentId, str | tzinfo] | None=None, warmup_bars: int=0, instrument_registry: InstrumentRegistry, future_roll_registry: FutureRollRegistry | None=None, contract_multipliers: Mapping[InstrumentId, Decimal] | None=None, execution_adapter: ExecutionAdapter | None=None, process_intent: ProcessIntentHandler, portfolio_view: PortfolioViewBuilder, equity_point: EquityPointBuilder, update_rolling_prices: RollingPriceUpdater) -> None`
- 作用：Perform __init__.
- 直接原始调用：`dict` x2
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.actor_loop.BacktestActorLoop._take_strategy_bar_result`
- 位置：`backend/src/qts/backtest/actor_loop.py:96`
- 类型：`staticmethod`
- 签名：`def _take_strategy_bar_result(mailbox: Mailbox) -> StrategyBarResult`
- 作用：Perform _take_strategy_bar_result.
- 直接原始调用：`RuntimeError` x2, `mailbox.empty` x2, `TypeError`, `isinstance`, `mailbox.get`, `type`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.actor_loop.BacktestActorLoop.run`

#### `qts.backtest.actor_loop.BacktestActorLoop._take_signal_batch`
- 位置：`backend/src/qts/backtest/actor_loop.py:108`
- 类型：`staticmethod`
- 签名：`def _take_signal_batch(mailbox: Mailbox) -> AggregatedSignalBatch`
- 作用：Perform _take_signal_batch.
- 直接原始调用：`RuntimeError` x2, `mailbox.empty` x2, `TypeError`, `isinstance`, `mailbox.get`, `type`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.actor_loop.BacktestActorLoop.run`

#### `qts.backtest.actor_loop.BacktestActorLoop._take_strategy_finalized`
- 位置：`backend/src/qts/backtest/actor_loop.py:120`
- 类型：`staticmethod`
- 签名：`def _take_strategy_finalized(mailbox: Mailbox) -> StrategyFinalized`
- 作用：Perform _take_strategy_finalized.
- 直接原始调用：`RuntimeError` x2, `mailbox.empty` x2, `TypeError`, `isinstance`, `mailbox.get`, `type`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.actor_loop.BacktestActorLoop.run`

#### `qts.backtest.actor_loop.BacktestActorLoop._market_data_ref_for`
- 位置：`backend/src/qts/backtest/actor_loop.py:131`
- 类型：`method`
- 签名：`def _market_data_ref_for(self, bar: Bar, *, refs: dict[tuple[str | None, str | tzinfo | None], ActorRef], subscriber: ActorRef) -> ActorRef`
- 作用：Perform _market_data_ref_for.
- 直接原始调用：`ActorRef`, `Mailbox`, `MarketDataActor`, `RuntimeError`, `refs.get`
- 已解析到仓库内部的调用：`qts.runtime.actor_ref.ActorRef`, `qts.runtime.actors.market_data_actor.MarketDataActor`, `qts.runtime.mailbox.Mailbox`
- 被以下仓库内部符号调用：`qts.backtest.actor_loop.BacktestActorLoop.run`

#### `qts.backtest.actor_loop.BacktestActorLoop._history_limit_from_subscriptions`
- 位置：`backend/src/qts/backtest/actor_loop.py:165`
- 类型：`staticmethod`
- 签名：`def _history_limit_from_subscriptions(ctx: StrategyContext) -> int | None`
- 作用：Perform _history_limit_from_subscriptions.
- 直接原始调用：`max`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.actor_loop.BacktestActorLoop.run`

#### `qts.backtest.actor_loop.BacktestActorLoop._resolve_actor_classes`
- 位置：`backend/src/qts/backtest/actor_loop.py:172`
- 类型：`staticmethod`
- 签名：`def _resolve_actor_classes() -> tuple[type, type]`
- 作用：Perform _resolve_actor_classes.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.actor_loop.BacktestActorLoop.run`

#### `qts.backtest.actor_loop.BacktestActorLoop.run`
- 位置：`backend/src/qts/backtest/actor_loop.py:180`
- 类型：`method`
- 签名：`def run(self, *, sink: BacktestStreamingSink, prune_history: bool, compact_orders: bool) -> BacktestActorLoopResult`
- 作用：Perform run.
- 直接原始调用：`ActorRef` x9, `Mailbox` x8, `account_actor.snapshot` x4, `len` x2, `self._equity_point` x2, `sink.write_equity_point` x2, `strategy_ref.process_all` x2, `strategy_ref.tell` x2, `AccountActor`, `BacktestActorLoopResult`, `ExecutionActor`, `HistoricalDataPortal`, `MarketDataEvent`, `OrderManagerActor`, `StrategyBarEvent`, `StrategyContext`, `StrategyFinalize`, `StrategySignalEvent`, `TypeError`, `defaultdict`, `history.append`, `isinstance`, `market_data_mailbox.empty`, `market_data_mailbox.get`, `market_data_ref.process_all`, `market_data_ref.tell`, `order_manager_actor.compact_for_streaming`, `portal.data_view`, `self._history_limit_from_subscriptions`, `self._market_data_ref_for`, `self._portfolio_view`, `self._process_intent`, `self._resolve_actor_classes`, `self._take_signal_batch`, `self._take_strategy_bar_result`, `self._take_strategy_finalized`, `self._update_rolling_prices`, `signal_aggregator_actor`, `signal_ref.process_all`, `signal_ref.tell`, `sink.write_processed`, `strategy_actor`, `type`
- 已解析到仓库内部的调用：`qts.runtime.actors.account_actor.AccountActor`, `qts.runtime.actor_ref.ActorRef`, `qts.runtime.mailbox.Mailbox`, `qts.runtime.actors.order_manager_actor.OrderManagerActor`, `qts.runtime.actors.execution_actor.ExecutionActor`, `qts.backtest.actor_loop.BacktestActorLoop._resolve_actor_classes`, `qts.backtest.actor_loop.BacktestActorLoop._history_limit_from_subscriptions`, `qts.backtest.actor_loop.BacktestActorLoop._market_data_ref_for`, `qts.runtime.actors.market_data_actor.MarketDataEvent`, `qts.backtest.historical_data_portal.HistoricalDataPortal`, `qts.backtest.actor_loop.BacktestActorLoop._take_strategy_bar_result`, `qts.backtest.actor_loop.BacktestActorLoop._take_signal_batch`, `qts.runtime.actors.strategy_actor.StrategyBarEvent`, `qts.runtime.actors.signal_aggregator_actor.StrategySignalEvent`, `qts.runtime.actors.strategy_actor.StrategyFinalize`, `qts.backtest.actor_loop.BacktestActorLoop._take_strategy_finalized`, `qts.backtest.actor_loop.BacktestActorLoopResult`
- 被以下仓库内部符号调用：无

### `qts.backtest.config`

模块：`qts.backtest.config`

#### `qts.backtest.config.CostModelConfig`
- 位置：`backend/src/qts/backtest/config.py:20`
- 类型：`class`
- 签名：`class CostModelConfig`
- 作用：Explicit backtest cost model settings.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.config_loader.BacktestConfigLoader.from_payload`

#### `qts.backtest.config.CostModelConfig.__post_init__`
- 位置：`backend/src/qts/backtest/config.py:26`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`Decimal` x4, `ValueError` x2, `object.__setattr__` x2, `str` x2
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.config.CostModelConfig.to_payload`
- 位置：`backend/src/qts/backtest/config.py:39`
- 类型：`method`
- 签名：`def to_payload(self) -> dict[str, str]`
- 作用：Perform to_payload.
- 直接原始调用：`str` x2
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.config.RiskConfig`
- 位置：`backend/src/qts/backtest/config.py:48`
- 类型：`class`
- 签名：`class RiskConfig`
- 作用：Backtest risk settings.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.config_loader.BacktestConfigLoader.from_payload`

#### `qts.backtest.config.RiskConfig.__post_init__`
- 位置：`backend/src/qts/backtest/config.py:53`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`Decimal` x2, `ValueError`, `object.__setattr__`, `str`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.config.RiskConfig.to_payload`
- 位置：`backend/src/qts/backtest/config.py:59`
- 类型：`method`
- 签名：`def to_payload(self) -> dict[str, str]`
- 作用：Perform to_payload.
- 直接原始调用：`str`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.config.RollPolicyConfig`
- 位置：`backend/src/qts/backtest/config.py:65`
- 类型：`class`
- 签名：`class RollPolicyConfig`
- 作用：Continuous futures roll policy for config-driven backtest runs.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.config_loader.BacktestConfigLoader.from_payload`

#### `qts.backtest.config.RollPolicyConfig.__post_init__`
- 位置：`backend/src/qts/backtest/config.py:71`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError`, `object.__setattr__`, `self.method.strip`, `self.method.strip.lower`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.config.RollPolicyConfig.to_payload`
- 位置：`backend/src/qts/backtest/config.py:78`
- 类型：`method`
- 签名：`def to_payload(self) -> dict[str, object]`
- 作用：Perform to_payload.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.config.BacktestMarketDataReference`
- 位置：`backend/src/qts/backtest/config.py:84`
- 类型：`class`
- 签名：`class BacktestMarketDataReference`
- 作用：Market data source reference for one backtest run.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.config.BacktestRunConfig.__post_init__`, `qts.backtest.config_loader.BacktestConfigLoader._parse_market_data_reference`

#### `qts.backtest.config.BacktestMarketDataReference.__post_init__`
- 位置：`backend/src/qts/backtest/config.py:91`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError` x4, `object.__setattr__` x3, `Path`, `self.catalog.strip`, `self.source.strip`, `self.source.strip.lower`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.config.BacktestMarketDataReference.is_configured`
- 位置：`backend/src/qts/backtest/config.py:110`
- 类型：`property`
- 签名：`def is_configured(self) -> bool`
- 作用：Perform is_configured.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.config.BacktestMarketDataReference.to_payload`
- 位置：`backend/src/qts/backtest/config.py:114`
- 类型：`method`
- 签名：`def to_payload(self) -> dict[str, str] | None`
- 作用：Perform to_payload.
- 直接原始调用：`RuntimeError`, `str`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.config.BacktestStrategyConfig`
- 位置：`backend/src/qts/backtest/config.py:127`
- 类型：`class`
- 签名：`class BacktestStrategyConfig`
- 作用：Configured strategy instance referenced by a backtest run.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.config.BacktestRunConfig.__post_init__`

#### `qts.backtest.config.BacktestStrategyConfig.__post_init__`
- 位置：`backend/src/qts/backtest/config.py:137`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError` x4, `Decimal` x2, `object.__setattr__` x2, `dict`, `self.account_id.strip`, `self.class_path.strip`, `self.strategy_id.strip`, `str`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.config.BacktestStrategyConfig.from_yaml`
- 位置：`backend/src/qts/backtest/config.py:151`
- 类型：`classmethod`
- 签名：`def from_yaml(cls, path: Path) -> BacktestStrategyConfig`
- 作用：Perform from_yaml.
- 直接原始调用：`ValueError`, `cls._parse_payload`, `isinstance`, `path.read_text`, `yaml.safe_load`
- 已解析到仓库内部的调用：`qts.backtest.config.BacktestStrategyConfig._parse_payload`
- 被以下仓库内部符号调用：`qts.backtest.config_loader.BacktestConfigLoader.from_payload`

#### `qts.backtest.config.BacktestStrategyConfig.to_payload`
- 位置：`backend/src/qts/backtest/config.py:158`
- 类型：`method`
- 签名：`def to_payload(self) -> dict[str, Any]`
- 作用：Perform to_payload.
- 直接原始调用：`str`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.config.BacktestStrategyConfig._parse_payload`
- 位置：`backend/src/qts/backtest/config.py:170`
- 类型：`classmethod`
- 签名：`def _parse_payload(cls, payload: dict[str, Any]) -> BacktestStrategyConfig`
- 作用：Perform _parse_payload.
- 直接原始调用：`payload.get` x5, `str` x4, `Decimal`, `ValueError`, `bool`, `cls`, `isinstance`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.config.BacktestStrategyConfig.from_yaml`

#### `qts.backtest.config.BacktestRunConfig`
- 位置：`backend/src/qts/backtest/config.py:190`
- 类型：`class`
- 签名：`class BacktestRunConfig`
- 作用：Complete identity for a backtest run.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.config_loader.BacktestConfigLoader.from_payload`

#### `qts.backtest.config.BacktestRunConfig.__post_init__`
- 位置：`backend/src/qts/backtest/config.py:214`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`object.__setattr__` x14, `ValueError` x10, `isinstance` x4, `BacktestMarketDataReference` x2, `Decimal` x2, `Path` x2, `dict` x2, `str` x2, `tuple` x2, `BacktestStrategyConfig`, `InstrumentId`, `all`, `root.strip`, `self._normalize_symbol`, `self.historical_data.to_payload`, `self.instrument_ids.items`, `self.market_data.to_payload`, `self.strategy_class.strip`, `self.timeframe.strip`
- 已解析到仓库内部的调用：`qts.backtest.config.BacktestMarketDataReference`, `qts.backtest.config.BacktestStrategyConfig`, `qts.backtest.config.BacktestRunConfig._normalize_symbol`, `qts.core.ids.InstrumentId`
- 被以下仓库内部符号调用：无

#### `qts.backtest.config.BacktestRunConfig.from_yaml`
- 位置：`backend/src/qts/backtest/config.py:280`
- 类型：`classmethod`
- 签名：`def from_yaml(cls, path: Path) -> BacktestRunConfig`
- 作用：Perform from_yaml.
- 直接原始调用：`BacktestConfigLoader.from_path`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.runner.run_backtest`

#### `qts.backtest.config.BacktestRunConfig.config_hash`
- 位置：`backend/src/qts/backtest/config.py:287`
- 类型：`property`
- 签名：`def config_hash(self) -> str`
- 作用：Perform config_hash.
- 直接原始调用：`self.to_payload`, `stable_json_hash`
- 已解析到仓库内部的调用：`qts.core.hashing.stable_json_hash`, `qts.backtest.config.BacktestRunConfig.to_payload`
- 被以下仓库内部符号调用：无

#### `qts.backtest.config.BacktestRunConfig.to_payload`
- 位置：`backend/src/qts/backtest/config.py:291`
- 类型：`method`
- 签名：`def to_payload(self) -> dict[str, Any]`
- 作用：Perform to_payload.
- 直接原始调用：`str` x3, `list` x2, `self.cost_model.to_payload`, `self.end.isoformat`, `self.instrument_ids.items`, `self.market_data.to_payload`, `self.risk_config.to_payload`, `self.roll_policy.to_payload`, `self.start.isoformat`, `self.strategy.to_payload`, `sorted`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.config.BacktestRunConfig.config_hash`

#### `qts.backtest.config.BacktestRunConfig._normalize_symbol`
- 位置：`backend/src/qts/backtest/config.py:323`
- 类型：`staticmethod`
- 签名：`def _normalize_symbol(symbol: str) -> str`
- 作用：Perform _normalize_symbol.
- 直接原始调用：`ValueError`, `symbol.strip`, `symbol.strip.upper`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.config.BacktestRunConfig.__post_init__`

### `qts.backtest.config_loader`

模块：`qts.backtest.config_loader`

#### `qts.backtest.config_loader.BacktestConfigLoader`
- 位置：`backend/src/qts/backtest/config_loader.py:24`
- 类型：`class`
- 签名：`class BacktestConfigLoader`
- 作用：Load backtest configuration from YAML or payload dictionaries.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.config_loader.BacktestConfigLoader.from_path`
- 位置：`backend/src/qts/backtest/config_loader.py:28`
- 类型：`classmethod`
- 签名：`def from_path(cls, path: Path) -> BacktestRunConfig`
- 作用：Perform from_path.
- 直接原始调用：`ValueError`, `cls.from_payload`, `isinstance`, `path.read_text`, `yaml.safe_load`
- 已解析到仓库内部的调用：`qts.backtest.config_loader.BacktestConfigLoader.from_payload`
- 被以下仓库内部符号调用：无

#### `qts.backtest.config_loader.BacktestConfigLoader.from_payload`
- 位置：`backend/src/qts/backtest/config_loader.py:36`
- 类型：`classmethod`
- 签名：`def from_payload(cls, payload: Mapping[str, Any]) -> BacktestRunConfig`
- 作用：Perform from_payload.
- 直接原始调用：`str` x12, `payload.get` x10, `ValueError` x6, `isinstance` x5, `Decimal` x4, `Path` x2, `cls._parse_datetime` x2, `cls._parse_market_data_reference` x2, `cost_payload.get` x2, `roll_payload.get` x2, `tuple` x2, `BacktestRunConfig`, `BacktestStrategyConfig.from_yaml`, `CostModelConfig`, `InstrumentId`, `RiskConfig`, `RollPolicyConfig`, `bool`, `cast`, `dict`, `instrument_ids_payload.items`, `int`, `risk_payload.get`
- 已解析到仓库内部的调用：`qts.backtest.config.BacktestStrategyConfig.from_yaml`, `qts.backtest.config.BacktestRunConfig`, `qts.backtest.config_loader.BacktestConfigLoader._parse_datetime`, `qts.backtest.config_loader.BacktestConfigLoader._parse_market_data_reference`, `qts.backtest.config.CostModelConfig`, `qts.backtest.config.RiskConfig`, `qts.backtest.config.RollPolicyConfig`, `qts.core.ids.InstrumentId`
- 被以下仓库内部符号调用：`qts.backtest.config_loader.BacktestConfigLoader.from_path`

#### `qts.backtest.config_loader.BacktestConfigLoader._parse_datetime`
- 位置：`backend/src/qts/backtest/config_loader.py:112`
- 类型：`staticmethod`
- 签名：`def _parse_datetime(value: datetime | str) -> datetime`
- 作用：Perform _parse_datetime.
- 直接原始调用：`ValueError`, `datetime.fromisoformat`, `isinstance`, `parsed.astimezone`, `value.replace`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.config_loader.BacktestConfigLoader.from_payload`

#### `qts.backtest.config_loader.BacktestConfigLoader._parse_market_data_reference`
- 位置：`backend/src/qts/backtest/config_loader.py:123`
- 类型：`staticmethod`
- 签名：`def _parse_market_data_reference(payload: object) -> BacktestMarketDataReference`
- 作用：Perform _parse_market_data_reference.
- 直接原始调用：`str` x3, `BacktestMarketDataReference` x2, `Path`, `ValueError`, `isinstance`, `payload.get`
- 已解析到仓库内部的调用：`qts.backtest.config.BacktestMarketDataReference`
- 被以下仓库内部符号调用：`qts.backtest.config_loader.BacktestConfigLoader.from_payload`

### `qts.backtest.engine`

模块：`qts.backtest.engine`

#### `qts.backtest.engine.BacktestCostModel`
- 位置：`backend/src/qts/backtest/engine.py:52`
- 类型：`class`
- 签名：`class BacktestCostModel`
- 作用：Explicit simulation cost assumptions included in reports.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine.__init__`, `qts.backtest.engine.BacktestEngine.from_config`

#### `qts.backtest.engine.BacktestCostModel.__post_init__`
- 位置：`backend/src/qts/backtest/engine.py:59`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError` x3, `Decimal` x2, `self.latency_model.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.engine.BacktestCostModel.to_payload`
- 位置：`backend/src/qts/backtest/engine.py:68`
- 类型：`method`
- 签名：`def to_payload(self) -> dict[str, str]`
- 作用：Perform to_payload.
- 直接原始调用：`str` x2
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.engine.BacktestCostModel.slippage_model`
- 位置：`backend/src/qts/backtest/engine.py:77`
- 类型：`property`
- 签名：`def slippage_model(self) -> str`
- 作用：Perform slippage_model.
- 直接原始调用：`Decimal`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.engine.BacktestCostModel.commission_model`
- 位置：`backend/src/qts/backtest/engine.py:82`
- 类型：`property`
- 签名：`def commission_model(self) -> str`
- 作用：Perform commission_model.
- 直接原始调用：`Decimal`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.engine.BacktestStreamResult`
- 位置：`backend/src/qts/backtest/engine.py:90`
- 类型：`class`
- 签名：`class BacktestStreamResult`
- 作用：Backtest result written to partitioned streaming artifacts.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine.run_streaming`

#### `qts.backtest.engine.BacktestEngine`
- 位置：`backend/src/qts/backtest/engine.py:109`
- 类型：`class`
- 签名：`class BacktestEngine`
- 作用：Single-process backtest engine using the Strategy SDK and actor order flow.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.engine.BacktestEngine.__init__`
- 位置：`backend/src/qts/backtest/engine.py:112`
- 类型：`method`
- 签名：`def __init__(self, *, strategy: Strategy, bars: Iterable[Bar], initial_cash: Decimal, risk_engine: RiskEngine | None=None, dataset_metadata: Iterable[DatasetMetadata]=(), config: dict[str, Any] | None=None, strategy_version: str | None=None, cost_model: BacktestCostModel | None=None, contract_multipliers: Mapping[InstrumentId, Decimal] | None=None, future_roll_registry: FutureRollRegistry | None=None, warmup_bars: int=0, target_timeframe: str | None=None, exchange_timezone_by_instrument: Mapping[InstrumentId, str | tzinfo] | None=None, instrument_registry: InstrumentRegistry | None=None) -> None`
- 作用：Perform __init__.
- 直接原始调用：`dict` x2, `iter` x2, `tuple` x2, `BacktestCostModel`, `BacktestInstrumentContext`, `BacktestIntentProcessor`, `BacktestPortfolioProjector`, `Decimal`, `MaxNotionalRule`, `RiskEngine`, `isinstance`
- 已解析到仓库内部的调用：`qts.backtest.engine.BacktestCostModel`, `qts.risk.risk_engine.RiskEngine`, `qts.risk.rules.max_notional.MaxNotionalRule`, `qts.backtest.instrument_context.BacktestInstrumentContext`, `qts.backtest.portfolio_projection.BacktestPortfolioProjector`, `qts.backtest.intent_processor.BacktestIntentProcessor`
- 被以下仓库内部符号调用：无

#### `qts.backtest.engine.BacktestEngine.from_config`
- 位置：`backend/src/qts/backtest/engine.py:167`
- 类型：`classmethod`
- 签名：`def from_config(cls, config: BacktestRunConfig, *, bars: Iterable[Bar], strategy: Strategy, instrument_registry: InstrumentRegistry | None=None, dataset_metadata: Iterable[DatasetMetadata]=(), future_roll_registry: FutureRollRegistry | None=None, exchange_timezone_by_instrument: Mapping[InstrumentId, str | tzinfo] | None=None, contract_multipliers: Mapping[InstrumentId, Decimal] | None=None) -> BacktestEngine`
- 作用：Perform from_config.
- 直接原始调用：`BacktestCostModel`, `MaxNotionalRule`, `RiskEngine`, `cls`, `config.to_payload`
- 已解析到仓库内部的调用：`qts.backtest.engine.BacktestCostModel`, `qts.risk.risk_engine.RiskEngine`, `qts.risk.rules.max_notional.MaxNotionalRule`
- 被以下仓库内部符号调用：`qts.backtest.runner.run_backtest`

#### `qts.backtest.engine.BacktestEngine.run_streaming`
- 位置：`backend/src/qts/backtest/engine.py:202`
- 类型：`method`
- 签名：`def run_streaming(self, output_dir: Any) -> BacktestStreamResult`
- 作用：Perform run_streaming.
- 直接原始调用：`BacktestActorLoop`, `BacktestRunId`, `BacktestStreamResult`, `BacktestStreamingSink`, `EquityCurvePoint`, `StreamingBacktestArtifactWriter`, `_BacktestExecutionAdapter`, `actor_loop.run`, `self._cost_model.to_payload`, `self._dataset_payload`, `self._instrument_context.instrument_registry`, `self._zero_time`, `sink.write_equity_point`, `stable_json_hash`, `tuple`, `writer.finalize`
- 已解析到仓库内部的调用：`qts.backtest.report.StreamingBacktestArtifactWriter`, `qts.backtest.sinks.BacktestStreamingSink`, `qts.backtest.actor_loop.BacktestActorLoop`, `qts.backtest.engine._BacktestExecutionAdapter`, `qts.backtest.report.EquityCurvePoint`, `qts.backtest.engine.BacktestEngine._zero_time`, `qts.core.hashing.stable_json_hash`, `qts.backtest.engine.BacktestEngine._dataset_payload`, `qts.backtest.engine.BacktestStreamResult`, `qts.core.ids.BacktestRunId`
- 被以下仓库内部符号调用：无

#### `qts.backtest.engine.BacktestEngine._dataset_payload`
- 位置：`backend/src/qts/backtest/engine.py:267`
- 类型：`staticmethod`
- 签名：`def _dataset_payload(item: DatasetMetadata) -> dict[str, Any]`
- 作用：Perform _dataset_payload.
- 直接原始调用：`item.created_at.isoformat`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine.run_streaming`

#### `qts.backtest.engine.BacktestEngine._zero_time`
- 位置：`backend/src/qts/backtest/engine.py:282`
- 类型：`staticmethod`
- 签名：`def _zero_time() -> Any`
- 作用：Perform _zero_time.
- 直接原始调用：`datetime`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine.run_streaming`

#### `qts.backtest.engine._BacktestExecutionAdapter`
- 位置：`backend/src/qts/backtest/engine.py:289`
- 类型：`class`
- 签名：`class _BacktestExecutionAdapter`
- 作用：_BacktestExecutionAdapter.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine.run_streaming`

#### `qts.backtest.engine._BacktestExecutionAdapter.__init__`
- 位置：`backend/src/qts/backtest/engine.py:291`
- 类型：`method`
- 签名：`def __init__(self, cost_model: BacktestCostModel) -> None`
- 作用：Perform __init__.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.engine._BacktestExecutionAdapter.execute_market_order`
- 位置：`backend/src/qts/backtest/engine.py:295`
- 类型：`method`
- 签名：`def execute_market_order(self, intent: OrderIntent, *, broker_order_id: str, market_price: Decimal) -> ExecutionReport`
- 作用：Perform execute_market_order.
- 直接原始调用：`Decimal` x2, `ExecutionReport`, `ValueError`, `abs`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.backtest.historical_data_portal`

模块：`qts.backtest.historical_data_portal`

#### `qts.backtest.historical_data_portal.HistoricalDataPortal`
- 位置：`backend/src/qts/backtest/historical_data_portal.py:13`
- 类型：`class`
- 签名：`class HistoricalDataPortal`
- 作用：Returns finalized bars visible as of a replay timestamp.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.actor_loop.BacktestActorLoop.run`

#### `qts.backtest.historical_data_portal.HistoricalDataPortal.__init__`
- 位置：`backend/src/qts/backtest/historical_data_portal.py:16`
- 类型：`method`
- 签名：`def __init__(self, bars: Mapping[InstrumentId, Iterable[Bar]]) -> None`
- 作用：Perform __init__.
- 直接原始调用：`bars.items`, `sorted`, `tuple`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.historical_data_portal.HistoricalDataPortal.data_view`
- 位置：`backend/src/qts/backtest/historical_data_portal.py:23`
- 类型：`method`
- 签名：`def data_view(self, *, as_of: datetime) -> DataView`
- 作用：Perform data_view.
- 直接原始调用：`DataView`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.historical_data_portal.HistoricalDataPortal.history`

#### `qts.backtest.historical_data_portal.HistoricalDataPortal.history`
- 位置：`backend/src/qts/backtest/historical_data_portal.py:27`
- 类型：`method`
- 签名：`def history(self, asset: AssetRef, *, as_of: datetime, bars: int, timeframe: str | None=None) -> tuple[Bar, ...]`
- 作用：Perform history.
- 直接原始调用：`self.data_view`, `self.data_view.history`
- 已解析到仓库内部的调用：`qts.backtest.historical_data_portal.HistoricalDataPortal.data_view`
- 被以下仓库内部符号调用：无

### `qts.backtest.inputs`

模块：`qts.backtest.inputs`

#### `qts.backtest.inputs.BacktestInputBundle`
- 位置：`backend/src/qts/backtest/inputs.py:22`
- 类型：`class`
- 签名：`class BacktestInputBundle`
- 作用：Streaming inputs and side-channel metadata required by a backtest run.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.inputs.BacktestInputBuilder.build`

#### `qts.backtest.inputs.BacktestInputBuilder`
- 位置：`backend/src/qts/backtest/inputs.py:34`
- 类型：`class`
- 签名：`class BacktestInputBuilder`
- 作用：Build replay-ready market data, registry, and provenance inputs.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.runner.run_backtest`

#### `qts.backtest.inputs.BacktestInputBuilder.__init__`
- 位置：`backend/src/qts/backtest/inputs.py:37`
- 类型：`method`
- 签名：`def __init__(self, config: BacktestRunConfig, catalog: HistoricalCatalog) -> None`
- 作用：Perform __init__.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.inputs.BacktestInputBuilder.build`
- 位置：`backend/src/qts/backtest/inputs.py:42`
- 类型：`method`
- 签名：`def build(self) -> BacktestInputBundle`
- 作用：Perform build.
- 直接原始调用：`BacktestInputBundle`, `self._contract_multipliers_for`, `self._dataset_metadata`, `self._instrument_registry_for`, `self._roll_registry`, `self._stream_configured_bars`
- 已解析到仓库内部的调用：`qts.backtest.inputs.BacktestInputBuilder._roll_registry`, `qts.backtest.inputs.BacktestInputBuilder._stream_configured_bars`, `qts.backtest.inputs.BacktestInputBundle`, `qts.backtest.inputs.BacktestInputBuilder._instrument_registry_for`, `qts.backtest.inputs.BacktestInputBuilder._dataset_metadata`, `qts.backtest.inputs.BacktestInputBuilder._contract_multipliers_for`
- 被以下仓库内部符号调用：`qts.backtest.runner.run_backtest`

#### `qts.backtest.inputs.BacktestInputBuilder._roll_registry`
- 位置：`backend/src/qts/backtest/inputs.py:62`
- 类型：`method`
- 签名：`def _roll_registry(self) -> FutureRollRegistry | None`
- 作用：Perform _roll_registry.
- 直接原始调用：`FutureRollRegistry`, `len`
- 已解析到仓库内部的调用：`qts.registry.future_roll.FutureRollRegistry`
- 被以下仓库内部符号调用：`qts.backtest.inputs.BacktestInputBuilder.build`

#### `qts.backtest.inputs.BacktestInputBuilder._stream_configured_bars`
- 位置：`backend/src/qts/backtest/inputs.py:68`
- 类型：`method`
- 签名：`def _stream_configured_bars(self, catalog: HistoricalCatalog, *, roll_registry: FutureRollRegistry | None) -> tuple[Iterator[Bar], dict[str, dict[str, int]], dict[InstrumentId, str]]`
- 作用：Perform _stream_configured_bars.
- 直接原始调用：`dataset.chain.instrument_id_for_symbol` x2, `exchange_timezones.setdefault` x2, `HighestVolumeFutureContractSelector`, `RuntimeError`, `ValueError`, `enumerate`, `iter_historical_bars`, `roll_registry.register_root`, `self._exchange_timezone_for`, `self._iter_root_bars`, `self._merge_ordered_bar_streams`, `set`, `streams.append`, `tuple`
- 已解析到仓库内部的调用：`qts.backtest.inputs.BacktestInputBuilder._exchange_timezone_for`, `qts.data.historical.csv_dataset.iter_historical_bars`, `qts.registry.future_roll.HighestVolumeFutureContractSelector`, `qts.backtest.inputs.BacktestInputBuilder._iter_root_bars`, `qts.backtest.inputs.BacktestInputBuilder._merge_ordered_bar_streams`
- 被以下仓库内部符号调用：`qts.backtest.inputs.BacktestInputBuilder.build`

#### `qts.backtest.inputs.BacktestInputBuilder._iter_root_bars`
- 位置：`backend/src/qts/backtest/inputs.py:135`
- 类型：`method`
- 签名：`def _iter_root_bars(self, root: str, stream: HistoricalBarStream, *, requested: set[str], rolling_root: bool, roll_registry: FutureRollRegistry | None, stats: dict[str, dict[str, int]], exchange_timezones: dict[InstrumentId, str], exchange_timezone: str | None) -> Iterator[Bar]`
- 作用：Perform _iter_root_bars.
- 直接原始调用：`self._record_exchange_timezone` x2, `RuntimeError`, `bar.instrument_id.value.rsplit`, `len`, `roll_registry.record_selection`, `stream.stats.as_dict`
- 已解析到仓库内部的调用：`qts.backtest.inputs.BacktestInputBuilder._record_exchange_timezone`
- 被以下仓库内部符号调用：`qts.backtest.inputs.BacktestInputBuilder._stream_configured_bars`

#### `qts.backtest.inputs.BacktestInputBuilder._merge_ordered_bar_streams`
- 位置：`backend/src/qts/backtest/inputs.py:175`
- 类型：`staticmethod`
- 签名：`def _merge_ordered_bar_streams(streams: list[tuple[int, Iterator[Bar]]]) -> Iterator[Bar]`
- 作用：Perform _merge_ordered_bar_streams.
- 直接原始调用：`heapq.heappush` x2, `next` x2, `heapq.heappop`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.inputs.BacktestInputBuilder._stream_configured_bars`

#### `qts.backtest.inputs.BacktestInputBuilder._record_exchange_timezone`
- 位置：`backend/src/qts/backtest/inputs.py:199`
- 类型：`staticmethod`
- 签名：`def _record_exchange_timezone(bar: Bar, *, exchange_timezones: dict[InstrumentId, str], exchange_timezone: str | None) -> None`
- 作用：Perform _record_exchange_timezone.
- 直接原始调用：`exchange_timezones.setdefault`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.inputs.BacktestInputBuilder._iter_root_bars`

#### `qts.backtest.inputs.BacktestInputBuilder._exchange_timezone_for`
- 位置：`backend/src/qts/backtest/inputs.py:210`
- 类型：`staticmethod`
- 签名：`def _exchange_timezone_for(dataset: HistoricalDataset) -> str | None`
- 作用：Perform _exchange_timezone_for.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.inputs.BacktestInputBuilder._stream_configured_bars`

#### `qts.backtest.inputs.BacktestInputBuilder._instrument_registry_for`
- 位置：`backend/src/qts/backtest/inputs.py:218`
- 类型：`method`
- 签名：`def _instrument_registry_for(self, catalog: HistoricalCatalog, *, roll_registry: FutureRollRegistry | None) -> InstrumentRegistry`
- 作用：Perform _instrument_registry_for.
- 直接原始调用：`registry.register` x3, `self._instrument_for` x3, `Decimal` x2, `InstrumentRegistry`, `RuntimeError`, `chain.instrument_id_for_symbol`, `roll_registry.continuous_instrument_id`, `self._config.instrument_ids.items`, `set`
- 已解析到仓库内部的调用：`qts.registry.instrument_registry.InstrumentRegistry`, `qts.backtest.inputs.BacktestInputBuilder._instrument_for`
- 被以下仓库内部符号调用：`qts.backtest.inputs.BacktestInputBuilder.build`

#### `qts.backtest.inputs.BacktestInputBuilder._instrument_for`
- 位置：`backend/src/qts/backtest/inputs.py:273`
- 类型：`staticmethod`
- 签名：`def _instrument_for(instrument_id: InstrumentId, *, exchange: str, currency: str, tick_size: Decimal, multiplier: Decimal, calendar_id: str, asset_class: AssetClass=AssetClass.EQUITY) -> Instrument`
- 作用：Perform _instrument_for.
- 直接原始调用：`ContractSpec`, `Decimal`, `Instrument`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.inputs.BacktestInputBuilder._instrument_registry_for`

#### `qts.backtest.inputs.BacktestInputBuilder._dataset_metadata`
- 位置：`backend/src/qts/backtest/inputs.py:298`
- 类型：`method`
- 签名：`def _dataset_metadata(self, catalog: HistoricalCatalog) -> tuple[DatasetMetadata, ...]`
- 作用：Perform _dataset_metadata.
- 直接原始调用：`DatasetMetadata`, `self._config.end.isoformat`, `self._config.start.isoformat`, `self._dataset_instrument_id`, `str`, `tuple`
- 已解析到仓库内部的调用：`qts.data.provenance.DatasetMetadata`, `qts.backtest.inputs.BacktestInputBuilder._dataset_instrument_id`
- 被以下仓库内部符号调用：`qts.backtest.inputs.BacktestInputBuilder.build`

#### `qts.backtest.inputs.BacktestInputBuilder._dataset_instrument_id`
- 位置：`backend/src/qts/backtest/inputs.py:322`
- 类型：`staticmethod`
- 签名：`def _dataset_instrument_id(root: str, dataset: HistoricalDataset) -> InstrumentId`
- 作用：Perform _dataset_instrument_id.
- 直接原始调用：`InstrumentId` x2
- 已解析到仓库内部的调用：`qts.core.ids.InstrumentId`
- 被以下仓库内部符号调用：`qts.backtest.inputs.BacktestInputBuilder._dataset_metadata`

#### `qts.backtest.inputs.BacktestInputBuilder._contract_multipliers_for`
- 位置：`backend/src/qts/backtest/inputs.py:328`
- 类型：`method`
- 签名：`def _contract_multipliers_for(self, catalog: HistoricalCatalog) -> dict[InstrumentId, Decimal]`
- 作用：Perform _contract_multipliers_for.
- 直接原始调用：`chain.instrument_id_for_symbol`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.inputs.BacktestInputBuilder.build`

### `qts.backtest.instrument_context`

模块：`qts.backtest.instrument_context`

#### `qts.backtest.instrument_context.BacktestInstrumentContext`
- 位置：`backend/src/qts/backtest/instrument_context.py:16`
- 类型：`class`
- 签名：`class BacktestInstrumentContext`
- 作用：Resolve backtest instrument IDs, roll targets, and instrument metadata.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine.__init__`

#### `qts.backtest.instrument_context.BacktestInstrumentContext.__init__`
- 位置：`backend/src/qts/backtest/instrument_context.py:19`
- 类型：`method`
- 签名：`def __init__(self, *, future_roll_registry: FutureRollRegistry | None=None, instrument_registry: InstrumentRegistry | None=None, registry_bars: Sequence[Bar] | None=None, contract_multipliers: Mapping[InstrumentId, Decimal] | None=None) -> None`
- 作用：Perform __init__.
- 直接原始调用：`dict`, `tuple`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.instrument_context.BacktestInstrumentContext.instrument_registry`
- 位置：`backend/src/qts/backtest/instrument_context.py:34`
- 类型：`method`
- 签名：`def instrument_registry(self) -> InstrumentRegistry`
- 作用：Perform instrument_registry.
- 直接原始调用：`Decimal` x3, `ContractSpec`, `Instrument`, `InstrumentRegistry`, `RuntimeError`, `registry.register`, `seen.add`, `self._contract_multipliers.get`, `self._exchange_for`, `self._symbol_for`, `set`
- 已解析到仓库内部的调用：`qts.registry.instrument_registry.InstrumentRegistry`, `qts.backtest.instrument_context.BacktestInstrumentContext._symbol_for`, `qts.backtest.instrument_context.BacktestInstrumentContext._exchange_for`
- 被以下仓库内部符号调用：无

#### `qts.backtest.instrument_context.BacktestInstrumentContext.order_instrument_for_intent`
- 位置：`backend/src/qts/backtest/instrument_context.py:68`
- 类型：`method`
- 签名：`def order_instrument_for_intent(self, intent: TargetIntent, *, bar: Bar) -> InstrumentId`
- 作用：Perform order_instrument_for_intent.
- 直接原始调用：`RuntimeError`, `self._future_roll_registry.resolve_contract`, `self.is_continuous`
- 已解析到仓库内部的调用：`qts.backtest.instrument_context.BacktestInstrumentContext.is_continuous`
- 被以下仓库内部符号调用：无

#### `qts.backtest.instrument_context.BacktestInstrumentContext.market_price_for_intent`
- 位置：`backend/src/qts/backtest/instrument_context.py:79`
- 类型：`method`
- 签名：`def market_price_for_intent(self, intent: TargetIntent, *, instrument_id: InstrumentId, bar: Bar) -> Decimal`
- 作用：Perform market_price_for_intent.
- 直接原始调用：`RuntimeError`, `self._future_roll_registry.execution_price`, `self.is_continuous`
- 已解析到仓库内部的调用：`qts.backtest.instrument_context.BacktestInstrumentContext.is_continuous`
- 被以下仓库内部符号调用：无

#### `qts.backtest.instrument_context.BacktestInstrumentContext.update_rolling_prices`
- 位置：`backend/src/qts/backtest/instrument_context.py:97`
- 类型：`method`
- 签名：`def update_rolling_prices(self, bar: Bar, *, latest_prices: dict[InstrumentId, Decimal]) -> None`
- 作用：Perform update_rolling_prices.
- 直接原始调用：`self._future_roll_registry.execution_price`, `self._future_roll_registry.resolve_contract`, `self.is_continuous`
- 已解析到仓库内部的调用：`qts.backtest.instrument_context.BacktestInstrumentContext.is_continuous`
- 被以下仓库内部符号调用：无

#### `qts.backtest.instrument_context.BacktestInstrumentContext.related_contracts_for`
- 位置：`backend/src/qts/backtest/instrument_context.py:118`
- 类型：`method`
- 签名：`def related_contracts_for(self, continuous_instrument_id: InstrumentId) -> frozenset[InstrumentId]`
- 作用：Perform related_contracts_for.
- 直接原始调用：`RuntimeError` x2, `frozenset`, `self._future_roll_registry.related_contracts`, `self._related_contracts_by_continuous.get`, `self.is_continuous`
- 已解析到仓库内部的调用：`qts.backtest.instrument_context.BacktestInstrumentContext.is_continuous`
- 被以下仓库内部符号调用：无

#### `qts.backtest.instrument_context.BacktestInstrumentContext.is_continuous`
- 位置：`backend/src/qts/backtest/instrument_context.py:136`
- 类型：`method`
- 签名：`def is_continuous(self, instrument_id: InstrumentId) -> bool`
- 作用：Perform is_continuous.
- 直接原始调用：`self._future_roll_registry.is_continuous`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.instrument_context.BacktestInstrumentContext.market_price_for_intent`, `qts.backtest.instrument_context.BacktestInstrumentContext.order_instrument_for_intent`, `qts.backtest.instrument_context.BacktestInstrumentContext.related_contracts_for`, `qts.backtest.instrument_context.BacktestInstrumentContext.update_rolling_prices`

#### `qts.backtest.instrument_context.BacktestInstrumentContext._symbol_for`
- 位置：`backend/src/qts/backtest/instrument_context.py:143`
- 类型：`staticmethod`
- 签名：`def _symbol_for(instrument_id: InstrumentId) -> str`
- 作用：Perform _symbol_for.
- 直接原始调用：`instrument_id.value.rsplit`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.instrument_context.BacktestInstrumentContext.instrument_registry`

#### `qts.backtest.instrument_context.BacktestInstrumentContext._exchange_for`
- 位置：`backend/src/qts/backtest/instrument_context.py:148`
- 类型：`staticmethod`
- 签名：`def _exchange_for(instrument_id: InstrumentId) -> str`
- 作用：Perform _exchange_for.
- 直接原始调用：`instrument_id.value.split`, `len`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.instrument_context.BacktestInstrumentContext.instrument_registry`

### `qts.backtest.intent_processor`

模块：`qts.backtest.intent_processor`

#### `qts.backtest.intent_processor.BacktestProcessedIntent`
- 位置：`backend/src/qts/backtest/intent_processor.py:25`
- 类型：`class`
- 签名：`class BacktestProcessedIntent`
- 作用：Orders and fills generated for a single strategy intent.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.intent_processor.BacktestIntentProcessor._process_order_delta`, `qts.backtest.intent_processor.BacktestIntentProcessor.process_intent`

#### `qts.backtest.intent_processor.BacktestIntentProcessor`
- 位置：`backend/src/qts/backtest/intent_processor.py:32`
- 类型：`class`
- 签名：`class BacktestIntentProcessor`
- 作用：Translate strategy target intents into validated, executed backtest orders.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine.__init__`

#### `qts.backtest.intent_processor.BacktestIntentProcessor.__init__`
- 位置：`backend/src/qts/backtest/intent_processor.py:35`
- 类型：`method`
- 签名：`def __init__(self, *, risk_engine: RiskEngine, instrument_context: BacktestInstrumentContext, multiplier_for: Callable[[InstrumentId], Decimal]) -> None`
- 作用：Perform __init__.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.intent_processor.BacktestIntentProcessor.process_intent`
- 位置：`backend/src/qts/backtest/intent_processor.py:47`
- 类型：`method`
- 签名：`def process_intent(self, intent: TargetIntent, *, bar: Bar, account_actor: AccountActor, order_manager_actor: OrderManagerActor, order_manager_ref: ActorRef, execution_ref: ActorRef, account_ref: ActorRef, order_number: int) -> BacktestProcessedIntent`
- 作用：Process a single target intent and return produced orders/fills.
- 直接原始调用：`Decimal` x3, `BacktestProcessedIntent` x2, `order_requests.append` x2, `self._instrument_context.market_price_for_intent` x2, `tuple` x2, `Position`, `account_actor.snapshot`, `enumerate`, `fills.extend`, `orders.extend`, `self._desired_quantity`, `self._instrument_context.is_continuous`, `self._instrument_context.order_instrument_for_intent`, `self._instrument_context.related_contracts_for`, `self._process_order_delta`, `snapshot.positions.get`, `snapshot.positions.items`
- 已解析到仓库内部的调用：`qts.portfolio.position_book.Position`, `qts.backtest.intent_processor.BacktestIntentProcessor._desired_quantity`, `qts.backtest.intent_processor.BacktestProcessedIntent`, `qts.backtest.intent_processor.BacktestIntentProcessor._process_order_delta`
- 被以下仓库内部符号调用：无

#### `qts.backtest.intent_processor.BacktestIntentProcessor._process_order_delta`
- 位置：`backend/src/qts/backtest/intent_processor.py:136`
- 类型：`method`
- 签名：`def _process_order_delta(self, *, instrument_id: InstrumentId, quantity_delta: Decimal, market_price: Decimal, order_time: datetime | None, order_manager_actor: OrderManagerActor, order_manager_ref: ActorRef, execution_ref: ActorRef, account_ref: ActorRef, order_number: int) -> BacktestProcessedIntent`
- 作用：Perform _process_order_delta.
- 直接原始调用：`BacktestProcessedIntent` x4, `Decimal` x2, `order_manager_actor.get_order` x2, `order_manager_ref.process_all` x2, `OrderId`, `OrderIntent`, `OrderRiskRequest`, `SubmitOrder`, `abs`, `account_ref.process_all`, `execution_ref.process_all`, `order_manager_actor.fills_since`, `order_manager_ref.tell`, `self._multiplier_for`, `self._risk_engine.check`
- 已解析到仓库内部的调用：`qts.backtest.intent_processor.BacktestProcessedIntent`, `qts.core.ids.OrderId`, `qts.runtime.actors.order_manager_actor.SubmitOrder`
- 被以下仓库内部符号调用：`qts.backtest.intent_processor.BacktestIntentProcessor.process_intent`

#### `qts.backtest.intent_processor.BacktestIntentProcessor._desired_quantity`
- 位置：`backend/src/qts/backtest/intent_processor.py:201`
- 类型：`staticmethod`
- 签名：`def _desired_quantity(intent: TargetIntent, *, current_quantity: Decimal, bar: Bar) -> Decimal`
- 作用：Perform _desired_quantity.
- 直接原始调用：`ValueError` x2, `Decimal`, `max`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.intent_processor.BacktestIntentProcessor.process_intent`

### `qts.backtest.portfolio_projection`

模块：`qts.backtest.portfolio_projection`

#### `qts.backtest.portfolio_projection.BacktestPortfolioProjector`
- 位置：`backend/src/qts/backtest/portfolio_projection.py:15`
- 类型：`class`
- 签名：`class BacktestPortfolioProjector`
- 作用：Compute portfolio state views and equity points for streaming backtests.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine.__init__`

#### `qts.backtest.portfolio_projection.BacktestPortfolioProjector.__init__`
- 位置：`backend/src/qts/backtest/portfolio_projection.py:18`
- 类型：`method`
- 签名：`def __init__(self, contract_multipliers: Mapping[InstrumentId, Decimal] | None=None) -> None`
- 作用：Perform __init__.
- 直接原始调用：`dict`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.portfolio_projection.BacktestPortfolioProjector.multiplier_for`
- 位置：`backend/src/qts/backtest/portfolio_projection.py:22`
- 类型：`method`
- 签名：`def multiplier_for(self, instrument_id: InstrumentId) -> Decimal`
- 作用：Return multiplier used for portfolio valuation and risk checks.
- 直接原始调用：`Decimal`, `self._multipliers.get`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.portfolio_projection.BacktestPortfolioProjector.portfolio_view`

#### `qts.backtest.portfolio_projection.BacktestPortfolioProjector.portfolio_view`
- 位置：`backend/src/qts/backtest/portfolio_projection.py:27`
- 类型：`method`
- 签名：`def portfolio_view(self, snapshot: AccountSnapshot, latest_prices: Mapping[InstrumentId, Decimal]) -> PortfolioView`
- 作用：Perform portfolio_view.
- 直接原始调用：`Decimal` x2, `PortfolioPosition`, `PortfolioView`, `latest_prices.get`, `positions.values`, `self.multiplier_for`, `snapshot.positions.items`, `sum`
- 已解析到仓库内部的调用：`qts.backtest.portfolio_projection.BacktestPortfolioProjector.multiplier_for`
- 被以下仓库内部符号调用：`qts.backtest.portfolio_projection.BacktestPortfolioProjector.equity_point`

#### `qts.backtest.portfolio_projection.BacktestPortfolioProjector.equity_point`
- 位置：`backend/src/qts/backtest/portfolio_projection.py:51`
- 类型：`method`
- 签名：`def equity_point(self, bar: Bar, snapshot: AccountSnapshot, latest_prices: Mapping[InstrumentId, Decimal]) -> EquityCurvePoint`
- 作用：Perform equity_point.
- 直接原始调用：`EquityCurvePoint`, `self.portfolio_view`
- 已解析到仓库内部的调用：`qts.backtest.report.EquityCurvePoint`, `qts.backtest.portfolio_projection.BacktestPortfolioProjector.portfolio_view`
- 被以下仓库内部符号调用：无

### `qts.backtest.report`

模块：`qts.backtest.report`

#### `qts.backtest.report.EquityCurvePoint`
- 位置：`backend/src/qts/backtest/report.py:17`
- 类型：`class`
- 签名：`class EquityCurvePoint`
- 作用：One timestamped equity observation.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine.run_streaming`, `qts.backtest.portfolio_projection.BacktestPortfolioProjector.equity_point`

#### `qts.backtest.report.TradeLedgerEntry`
- 位置：`backend/src/qts/backtest/report.py:25`
- 类型：`class`
- 签名：`class TradeLedgerEntry`
- 作用：Auditable row for a simulated fill.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.sinks.BacktestStreamingSink._ledger_rows`

#### `qts.backtest.report._stable_hash`
- 位置：`backend/src/qts/backtest/report.py:39`
- 类型：`module_function`
- 签名：`def _stable_hash(payload: Any) -> str`
- 作用：Perform _stable_hash.
- 直接原始调用：`stable_json_hash`
- 已解析到仓库内部的调用：`qts.core.hashing.stable_json_hash`
- 被以下仓库内部符号调用：`qts.backtest.report.StreamingBacktestArtifactWriter.finalize`

#### `qts.backtest.report.StreamingEquityMetrics`
- 位置：`backend/src/qts/backtest/report.py:44`
- 类型：`class`
- 签名：`class StreamingEquityMetrics`
- 作用：Incremental metrics for a streamed equity curve.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.report.StreamingBacktestArtifactWriter.__init__`

#### `qts.backtest.report.StreamingEquityMetrics.__init__`
- 位置：`backend/src/qts/backtest/report.py:47`
- 类型：`method`
- 签名：`def __init__(self) -> None`
- 作用：Perform __init__.
- 直接原始调用：`Decimal`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.report.StreamingEquityMetrics.update`
- 位置：`backend/src/qts/backtest/report.py:55`
- 类型：`method`
- 签名：`def update(self, equity: Decimal) -> None`
- 作用：Perform update.
- 直接原始调用：`Decimal` x2, `ValueError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.report.StreamingEquityMetrics.to_payload`
- 位置：`backend/src/qts/backtest/report.py:72`
- 类型：`method`
- 签名：`def to_payload(self) -> dict[str, Decimal | int]`
- 作用：Perform to_payload.
- 直接原始调用：`ValueError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.report.StreamingBacktestArtifacts`
- 位置：`backend/src/qts/backtest/report.py:84`
- 类型：`class`
- 签名：`class StreamingBacktestArtifacts`
- 作用：Final paths and row counts for streamed backtest artifacts.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.report.StreamingBacktestArtifactWriter.finalize`

#### `qts.backtest.report._NdjsonArtifact`
- 位置：`backend/src/qts/backtest/report.py:93`
- 类型：`class`
- 签名：`class _NdjsonArtifact`
- 作用：_NdjsonArtifact.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.report.StreamingBacktestArtifactWriter.__init__`

#### `qts.backtest.report._NdjsonArtifact.__init__`
- 位置：`backend/src/qts/backtest/report.py:95`
- 类型：`method`
- 签名：`def __init__(self, path: Path) -> None`
- 作用：Perform __init__.
- 直接原始调用：`hashlib.sha256`, `path.open`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.report._NdjsonArtifact.write`
- 位置：`backend/src/qts/backtest/report.py:102`
- 类型：`method`
- 签名：`def write(self, payload: dict[str, Any]) -> None`
- 作用：Perform write.
- 直接原始调用：`json.dumps`, `line.encode`, `self._handle.write`, `self._hasher.update`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.report._NdjsonArtifact.close`
- 位置：`backend/src/qts/backtest/report.py:117`
- 类型：`method`
- 签名：`def close(self) -> None`
- 作用：Perform close.
- 直接原始调用：`self._handle.close`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.report._NdjsonArtifact.content_hash`
- 位置：`backend/src/qts/backtest/report.py:122`
- 类型：`property`
- 签名：`def content_hash(self) -> str`
- 作用：Perform content_hash.
- 直接原始调用：`self._hasher.hexdigest`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.report.StreamingBacktestArtifactWriter`
- 位置：`backend/src/qts/backtest/report.py:127`
- 类型：`class`
- 签名：`class StreamingBacktestArtifactWriter`
- 作用：Write large backtest outputs as line-delimited artifacts.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine.run_streaming`

#### `qts.backtest.report.StreamingBacktestArtifactWriter.__init__`
- 位置：`backend/src/qts/backtest/report.py:132`
- 类型：`method`
- 签名：`def __init__(self, output_dir: Path) -> None`
- 作用：Perform __init__.
- 直接原始调用：`StreamingEquityMetrics`, `_NdjsonArtifact`, `self._output_dir.mkdir`
- 已解析到仓库内部的调用：`qts.backtest.report._NdjsonArtifact`, `qts.backtest.report.StreamingEquityMetrics`
- 被以下仓库内部符号调用：无

#### `qts.backtest.report.StreamingBacktestArtifactWriter.write_order`
- 位置：`backend/src/qts/backtest/report.py:142`
- 类型：`method`
- 签名：`def write_order(self, payload: dict[str, Any]) -> None`
- 作用：Perform write_order.
- 直接原始调用：`self._artifacts['orders'].write`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.report.StreamingBacktestArtifactWriter.write_fill`
- 位置：`backend/src/qts/backtest/report.py:146`
- 类型：`method`
- 签名：`def write_fill(self, payload: dict[str, Any]) -> None`
- 作用：Perform write_fill.
- 直接原始调用：`self._artifacts['fills'].write`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.report.StreamingBacktestArtifactWriter.write_trade_ledger`
- 位置：`backend/src/qts/backtest/report.py:150`
- 类型：`method`
- 签名：`def write_trade_ledger(self, row: TradeLedgerEntry) -> None`
- 作用：Perform write_trade_ledger.
- 直接原始调用：`self._artifacts['trade_ledger'].write`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.report.StreamingBacktestArtifactWriter.write_equity_point`
- 位置：`backend/src/qts/backtest/report.py:166`
- 类型：`method`
- 签名：`def write_equity_point(self, point: EquityCurvePoint) -> None`
- 作用：Perform write_equity_point.
- 直接原始调用：`self._artifacts['equity_curve'].write`, `self._equity_metrics.update`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.report.StreamingBacktestArtifactWriter.finalize`
- 位置：`backend/src/qts/backtest/report.py:171`
- 类型：`method`
- 签名：`def finalize(self, *, config_hash: str, dataset_metadata: tuple[dict[str, Any], ...], cost_model: dict[str, Any], processed_bars: int, warmup_bars: int, trading_bars: int, final_cash: Decimal, strategy_version: str) -> tuple[str, str, dict[str, Any], StreamingBacktestArtifacts]`
- 作用：Perform finalize.
- 直接原始调用：`self._artifacts.items` x3, `str` x2, `StreamingBacktestArtifacts`, `_stable_hash`, `artifact.close`, `artifact.path.replace`, `json.dumps`, `manifest_path.write_text`, `report_hash.removeprefix`, `self._artifacts.values`, `self._equity_metrics.to_payload`
- 已解析到仓库内部的调用：`qts.backtest.report._stable_hash`, `qts.backtest.report.StreamingBacktestArtifacts`
- 被以下仓库内部符号调用：无

### `qts.backtest.runner`

模块：`qts.backtest.runner`

#### `qts.backtest.runner.BacktestRun`
- 位置：`backend/src/qts/backtest/runner.py:24`
- 类型：`class`
- 签名：`class BacktestRun`
- 作用：Output of a backtest runner invocation.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.runner.run_backtest`

#### `qts.backtest.runner.BacktestRun.processed_bars`
- 位置：`backend/src/qts/backtest/runner.py:34`
- 类型：`property`
- 签名：`def processed_bars(self) -> int`
- 作用：Perform processed_bars.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.runner.BacktestRun.report_hash`
- 位置：`backend/src/qts/backtest/runner.py:39`
- 类型：`property`
- 签名：`def report_hash(self) -> str`
- 作用：Perform report_hash.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.runner.run_backtest`
- 位置：`backend/src/qts/backtest/runner.py:44`
- 类型：`module_function`
- 签名：`def run_backtest(config_path: Path, *, output_dir: Path=Path('runs/backtests')) -> BacktestRun`
- 作用：Run a backtest and write partitioned streaming artifacts.
- 直接原始调用：`BacktestEngine.from_config`, `BacktestEngine.from_config.run_streaming`, `BacktestInputBuilder`, `BacktestInputBuilder.build`, `BacktestRun`, `BacktestRunConfig.from_yaml`, `HistoricalCatalog.load`, `Path`, `_catalog_load_config`, `_load_strategy`, `_streaming_summary_payload`, `json.dumps`, `result.artifact_paths.items`, `summary_path.write_text`
- 已解析到仓库内部的调用：`qts.backtest.config.BacktestRunConfig.from_yaml`, `qts.data.historical.catalog.HistoricalCatalog.load`, `qts.backtest.runner._catalog_load_config`, `qts.backtest.inputs.BacktestInputBuilder.build`, `qts.backtest.inputs.BacktestInputBuilder`, `qts.backtest.runner._load_strategy`, `qts.backtest.engine.BacktestEngine.from_config`, `qts.backtest.runner._streaming_summary_payload`, `qts.backtest.runner.BacktestRun`
- 被以下仓库内部符号调用：`scripts.run_backtest.main`

#### `qts.backtest.runner._catalog_load_config`
- 位置：`backend/src/qts/backtest/runner.py:87`
- 类型：`module_function`
- 签名：`def _catalog_load_config(config: BacktestRunConfig) -> HistoricalCatalogLoadConfig`
- 作用：Perform _catalog_load_config.
- 直接原始调用：`RuntimeError` x2, `HistoricalCatalogLoadConfig.from_historical_data_config`, `HistoricalCatalogLoadConfig.from_legacy_root`
- 已解析到仓库内部的调用：`qts.data.historical.catalog.HistoricalCatalogLoadConfig.from_historical_data_config`, `qts.data.historical.catalog.HistoricalCatalogLoadConfig.from_legacy_root`
- 被以下仓库内部符号调用：`qts.backtest.runner.run_backtest`

#### `qts.backtest.runner._load_strategy`
- 位置：`backend/src/qts/backtest/runner.py:109`
- 类型：`module_function`
- 签名：`def _load_strategy(strategy_class: str, params: dict[str, Any]) -> Strategy`
- 作用：Perform _load_strategy.
- 直接原始调用：`ValueError`, `_import_strategy_module`, `_strategy_type_from_module`, `strategy_class.partition`, `strategy_class.rpartition`, `strategy_type`
- 已解析到仓库内部的调用：`qts.backtest.runner._import_strategy_module`, `qts.backtest.runner._strategy_type_from_module`
- 被以下仓库内部符号调用：`qts.backtest.runner.run_backtest`

#### `qts.backtest.runner._import_strategy_module`
- 位置：`backend/src/qts/backtest/runner.py:121`
- 类型：`module_function`
- 签名：`def _import_strategy_module(module_name: str) -> ModuleType`
- 作用：Load a module that defines the requested strategy class.
- 直接原始调用：`Path`, `Path.with_suffix`, `importlib.import_module`, `importlib.util.module_from_spec`, `importlib.util.spec_from_file_location`, `module_name.split`, `module_path.exists`, `spec.loader.exec_module`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.runner._load_strategy`

#### `qts.backtest.runner._strategy_type_from_module`
- 位置：`backend/src/qts/backtest/runner.py:137`
- 类型：`module_function`
- 签名：`def _strategy_type_from_module(module: ModuleType, class_name: str) -> type[Strategy]`
- 作用：Extract the strategy class from a strategy module.
- 直接原始调用：`TypeError` x2, `ValueError`, `isinstance`, `issubclass`, `vars`, `vars.get`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.runner._load_strategy`

#### `qts.backtest.runner._streaming_summary_payload`
- 位置：`backend/src/qts/backtest/runner.py:151`
- 类型：`module_function`
- 签名：`def _streaming_summary_payload(result: BacktestStreamResult, *, manifest_path: Path, dataset_stats: dict[str, dict[str, int]]) -> dict[str, Any]`
- 作用：Perform _streaming_summary_payload.
- 直接原始调用：`dataset_stats.values` x4, `sum` x4, `item.get`, `str`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.runner.run_backtest`

### `qts.backtest.sinks`

模块：`qts.backtest.sinks`

#### `qts.backtest.sinks.BacktestStreamingSink`
- 位置：`backend/src/qts/backtest/sinks.py:13`
- 类型：`class`
- 签名：`class BacktestStreamingSink`
- 作用：Write engine stream artifacts through a shared writer.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine.run_streaming`

#### `qts.backtest.sinks.BacktestStreamingSink.__init__`
- 位置：`backend/src/qts/backtest/sinks.py:16`
- 类型：`method`
- 签名：`def __init__(self, writer: StreamingBacktestArtifactWriter) -> None`
- 作用：Perform __init__.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.sinks.BacktestStreamingSink.order_count`
- 位置：`backend/src/qts/backtest/sinks.py:22`
- 类型：`property`
- 签名：`def order_count(self) -> int`
- 作用：Perform order_count.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.sinks.BacktestStreamingSink.write_processed`
- 位置：`backend/src/qts/backtest/sinks.py:26`
- 类型：`method`
- 签名：`def write_processed(self, *, orders: tuple[Order, ...], fills: tuple[OrderFill, ...], bar: Bar) -> None`
- 作用：Perform write_processed.
- 直接原始调用：`len`, `self._fill_payload`, `self._ledger_rows`, `self._order_payload`, `self._writer.write_fill`, `self._writer.write_order`, `self._writer.write_trade_ledger`
- 已解析到仓库内部的调用：`qts.backtest.sinks.BacktestStreamingSink._order_payload`, `qts.backtest.sinks.BacktestStreamingSink._fill_payload`, `qts.backtest.sinks.BacktestStreamingSink._ledger_rows`
- 被以下仓库内部符号调用：无

#### `qts.backtest.sinks.BacktestStreamingSink.write_equity_point`
- 位置：`backend/src/qts/backtest/sinks.py:42`
- 类型：`method`
- 签名：`def write_equity_point(self, point: EquityCurvePoint) -> None`
- 作用：Perform write_equity_point.
- 直接原始调用：`self._writer.write_equity_point`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.backtest.sinks.BacktestStreamingSink._ledger_rows`
- 位置：`backend/src/qts/backtest/sinks.py:47`
- 类型：`staticmethod`
- 签名：`def _ledger_rows(fills: Iterable[OrderFill], *, bar: Bar) -> tuple[TradeLedgerEntry, ...]`
- 作用：Perform _ledger_rows.
- 直接原始调用：`TradeLedgerEntry`, `tuple`
- 已解析到仓库内部的调用：`qts.backtest.report.TradeLedgerEntry`
- 被以下仓库内部符号调用：`qts.backtest.sinks.BacktestStreamingSink.write_processed`

#### `qts.backtest.sinks.BacktestStreamingSink._order_payload`
- 位置：`backend/src/qts/backtest/sinks.py:65`
- 类型：`staticmethod`
- 签名：`def _order_payload(order: Order) -> dict[str, Any]`
- 作用：Perform _order_payload.
- 直接原始调用：`str`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.sinks.BacktestStreamingSink.write_processed`

#### `qts.backtest.sinks.BacktestStreamingSink._fill_payload`
- 位置：`backend/src/qts/backtest/sinks.py:77`
- 类型：`staticmethod`
- 签名：`def _fill_payload(fill: OrderFill) -> dict[str, Any]`
- 作用：Perform _fill_payload.
- 直接原始调用：`str` x4
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.sinks.BacktestStreamingSink.write_processed`

### `qts.config.ibkr`

模块：`qts.config.ibkr`

#### `qts.config.ibkr.IbkrConnectionConfig`
- 位置：`backend/src/qts/config/ibkr.py:16`
- 类型：`class`
- 签名：`class IbkrConnectionConfig`
- 作用：IBKR connection settings for one boundary.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.config.ibkr._read_connection`

#### `qts.config.ibkr.IbkrConnectionConfig.__post_init__`
- 位置：`backend/src/qts/config/ibkr.py:24`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError` x4, `self.host.strip`, `self.source_id.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.config.ibkr.IbkrOrderExecutionConfig`
- 位置：`backend/src/qts/config/ibkr.py:37`
- 类型：`class`
- 签名：`class IbkrOrderExecutionConfig`
- 作用：IBKR order execution settings.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.config.ibkr._read_order_execution_config`

#### `qts.config.ibkr.IbkrOrderExecutionConfig.__post_init__`
- 位置：`backend/src/qts/config/ibkr.py:48`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError` x6, `self.account_id.strip`, `self.host.strip`, `self.risk_profile.strip`, `self.source_id.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.config.ibkr.IbkrSecretRefs`
- 位置：`backend/src/qts/config/ibkr.py:65`
- 类型：`class`
- 签名：`class IbkrSecretRefs`
- 作用：Environment variable names for IBKR credentials.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.config.ibkr._read_secret_refs`

#### `qts.config.ibkr.IbkrSecretRefs.__post_init__`
- 位置：`backend/src/qts/config/ibkr.py:71`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError` x2, `self.password_env.strip`, `self.username_env.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.config.ibkr.IbkrEnvironmentConfig`
- 位置：`backend/src/qts/config/ibkr.py:80`
- 类型：`class`
- 签名：`class IbkrEnvironmentConfig`
- 作用：IBKR runtime configuration split by external boundary.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.config.ibkr.IbkrEnvironmentConfig.from_payload`
- 位置：`backend/src/qts/config/ibkr.py:89`
- 类型：`classmethod`
- 签名：`def from_payload(cls, payload: Mapping[str, Any]) -> IbkrEnvironmentConfig`
- 作用：Build a typed config from a mapping payload.
- 直接原始调用：`_as_mapping` x5, `ValueError` x2, `payload.get` x2, `str` x2, `_read_connection`, `_read_order_execution_config`, `_read_secret_refs`, `cls`, `payload.get.strip`, `str.strip`
- 已解析到仓库内部的调用：`qts.config.ibkr._as_mapping`, `qts.config.ibkr._read_connection`, `qts.config.ibkr._read_order_execution_config`, `qts.config.ibkr._read_secret_refs`
- 被以下仓库内部符号调用：`qts.config.ibkr.IbkrEnvironmentConfig.from_yaml`

#### `qts.config.ibkr.IbkrEnvironmentConfig.from_yaml`
- 位置：`backend/src/qts/config/ibkr.py:119`
- 类型：`classmethod`
- 签名：`def from_yaml(cls, path: Path) -> IbkrEnvironmentConfig`
- 作用：Load and validate environment config from YAML file.
- 直接原始调用：`ValueError`, `cls.from_payload`, `isinstance`, `path.read_text`, `yaml.safe_load`
- 已解析到仓库内部的调用：`qts.config.ibkr.IbkrEnvironmentConfig.from_payload`
- 被以下仓库内部符号调用：`qts.application.commands.ibkr_environment_evidence._read_config`, `qts.application.commands.ibkr_paper_order_lifecycle_drill._read_config`

#### `qts.config.ibkr.collect_validation_errors`
- 位置：`backend/src/qts/config/ibkr.py:128`
- 类型：`module_function`
- 签名：`def collect_validation_errors(config: IbkrEnvironmentConfig, *, paper_client_ids: Set[int] | None=None) -> list[str]`
- 作用：Return validation errors for config without raising.
- 直接原始调用：`str`, `str.split`, `validate_ibkr_environment`
- 已解析到仓库内部的调用：`qts.config.ibkr.validate_ibkr_environment`
- 被以下仓库内部符号调用：`qts.application.commands.ibkr_environment_evidence._merge_validation_errors`, `qts.application.commands.ibkr_paper_order_lifecycle_drill._validate_paper_only_ibkr_config`

#### `qts.config.ibkr.validate_ibkr_environment`
- 位置：`backend/src/qts/config/ibkr.py:140`
- 类型：`module_function`
- 签名：`def validate_ibkr_environment(config: IbkrEnvironmentConfig, *, paper_client_ids: Set[int] | None=None) -> None`
- 作用：Validate paper/live separation without exposing secret values.
- 直接原始调用：`errors.append` x5, `_contains_paper_reference` x2, `'; '.join`, `ValueError`, `config.order_execution.account_id.upper`, `config.order_execution.account_id.upper.startswith`, `config.order_execution.risk_profile.lower`, `live_client_ids.intersection`, `set`
- 已解析到仓库内部的调用：`qts.config.ibkr._contains_paper_reference`
- 被以下仓库内部符号调用：`qts.config.ibkr.collect_validation_errors`

#### `qts.config.ibkr._as_mapping`
- 位置：`backend/src/qts/config/ibkr.py:172`
- 类型：`module_function`
- 签名：`def _as_mapping(payload: Any, path: str) -> Mapping[str, Any]`
- 作用：Perform _as_mapping.
- 直接原始调用：`ValueError` x3, `isinstance` x2, `path.split`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.config.ibkr.IbkrEnvironmentConfig.from_payload`

#### `qts.config.ibkr._read_connection`
- 位置：`backend/src/qts/config/ibkr.py:186`
- 类型：`module_function`
- 签名：`def _read_connection(payload: Mapping[str, Any], path: str) -> IbkrConnectionConfig`
- 作用：Perform _read_connection.
- 直接原始调用：`payload.get` x4, `ValueError` x2, `isinstance` x2, `str` x2, `IbkrConnectionConfig`
- 已解析到仓库内部的调用：`qts.config.ibkr.IbkrConnectionConfig`
- 被以下仓库内部符号调用：`qts.config.ibkr.IbkrEnvironmentConfig.from_payload`, `qts.config.ibkr._read_order_execution_config`

#### `qts.config.ibkr._read_order_execution_config`
- 位置：`backend/src/qts/config/ibkr.py:206`
- 类型：`module_function`
- 签名：`def _read_order_execution_config(connection: Mapping[str, Any], payload: Mapping[str, Any]) -> IbkrOrderExecutionConfig`
- 作用：Perform _read_order_execution_config.
- 直接原始调用：`payload.get` x3, `str` x2, `IbkrOrderExecutionConfig`, `_read_connection`
- 已解析到仓库内部的调用：`qts.config.ibkr._read_connection`, `qts.config.ibkr.IbkrOrderExecutionConfig`
- 被以下仓库内部符号调用：`qts.config.ibkr.IbkrEnvironmentConfig.from_payload`

#### `qts.config.ibkr._read_secret_refs`
- 位置：`backend/src/qts/config/ibkr.py:227`
- 类型：`module_function`
- 签名：`def _read_secret_refs(payload: Mapping[str, Any]) -> IbkrSecretRefs`
- 作用：Perform _read_secret_refs.
- 直接原始调用：`payload.get` x2, `str` x2, `IbkrSecretRefs`
- 已解析到仓库内部的调用：`qts.config.ibkr.IbkrSecretRefs`
- 被以下仓库内部符号调用：`qts.config.ibkr.IbkrEnvironmentConfig.from_payload`

#### `qts.config.ibkr._contains_paper_reference`
- 位置：`backend/src/qts/config/ibkr.py:235`
- 类型：`module_function`
- 签名：`def _contains_paper_reference(secret_env_name: str) -> bool`
- 作用：Perform _contains_paper_reference.
- 直接原始调用：`secret_env_name.upper`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.config.ibkr.validate_ibkr_environment`

### `qts.core.hashing`

模块：`qts.core.hashing`

#### `qts.core.hashing.stable_json_default`
- 位置：`backend/src/qts/core/hashing.py:12`
- 类型：`module_function`
- 签名：`def stable_json_default(value: object) -> object`
- 作用：Adapter used by :func:`stable_json_dumps` for non-native JSON types.
- 直接原始调用：`isinstance` x3, `TypeError`, `hasattr`, `str`, `type`, `value.isoformat`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.core.hashing.stable_json_dumps`
- 位置：`backend/src/qts/core/hashing.py:24`
- 类型：`module_function`
- 签名：`def stable_json_dumps(payload: Any) -> str`
- 作用：Serialize `payload` deterministically for stable hashing.
- 直接原始调用：`json.dumps`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.core.hashing.stable_json_hash`

#### `qts.core.hashing.stable_json_hash`
- 位置：`backend/src/qts/core/hashing.py:35`
- 类型：`module_function`
- 签名：`def stable_json_hash(payload: Any) -> str`
- 作用：Return a stable SHA-256 digest for a payload.
- 直接原始调用：`hashlib.sha256`, `hashlib.sha256.hexdigest`, `stable_json_dumps`, `stable_json_dumps.encode`
- 已解析到仓库内部的调用：`qts.core.hashing.stable_json_dumps`
- 被以下仓库内部符号调用：`qts.backtest.config.BacktestRunConfig.config_hash`, `qts.backtest.engine.BacktestEngine.run_streaming`, `qts.backtest.report._stable_hash`

### `qts.core.ids`

模块：`qts.core.ids`

#### `qts.core.ids._StringId`
- 位置：`backend/src/qts/core/ids.py:9`
- 类型：`class`
- 签名：`class _StringId`
- 作用：Base class for typed string identifiers.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.core.ids._StringId.__post_init__`
- 位置：`backend/src/qts/core/ids.py:14`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`TypeError`, `ValueError`, `isinstance`, `self.value.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.core.ids._StringId.__str__`
- 位置：`backend/src/qts/core/ids.py:22`
- 类型：`method`
- 签名：`def __str__(self) -> str`
- 作用：Perform __str__.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.core.ids.AccountId`
- 位置：`backend/src/qts/core/ids.py:27`
- 类型：`class`
- 签名：`class AccountId(_StringId)`
- 作用：Stable internal account identifier.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.application.commands.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill`

#### `qts.core.ids.StrategyId`
- 位置：`backend/src/qts/core/ids.py:31`
- 类型：`class`
- 签名：`class StrategyId(_StringId)`
- 作用：Stable internal strategy identifier.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.application.commands.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill`

#### `qts.core.ids.InstrumentId`
- 位置：`backend/src/qts/core/ids.py:35`
- 类型：`class`
- 签名：`class InstrumentId(_StringId)`
- 作用：Stable internal instrument identifier.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.application.commands.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill`, `qts.backtest.config.BacktestRunConfig.__post_init__`, `qts.backtest.config_loader.BacktestConfigLoader.from_payload`, `qts.backtest.inputs.BacktestInputBuilder._dataset_instrument_id`, `qts.data.historical.catalog.HistoricalCatalogLoadConfig.__post_init__`, `qts.data.historical.chains.HistoricalChain.instrument_id_for_symbol`, `qts.data.stores.parquet_store.ParquetMarketDataStore._bar_from_json`, `qts.registry.future_roll.FutureRollRegistry.register_root`, `scripts.run_load.main`

#### `qts.core.ids.OrderId`
- 位置：`backend/src/qts/core/ids.py:39`
- 类型：`class`
- 签名：`class OrderId(_StringId)`
- 作用：Stable internal order identifier.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.application.commands.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill`, `qts.backtest.intent_processor.BacktestIntentProcessor._process_order_delta`

#### `qts.core.ids.BrokerId`
- 位置：`backend/src/qts/core/ids.py:43`
- 类型：`class`
- 签名：`class BrokerId(_StringId)`
- 作用：Stable internal broker identifier.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.application.commands.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill`

#### `qts.core.ids.EventId`
- 位置：`backend/src/qts/core/ids.py:47`
- 类型：`class`
- 签名：`class EventId(_StringId)`
- 作用：Stable internal event identifier.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.event_store.FileEventStore._event_from_json`

#### `qts.core.ids.BacktestRunId`
- 位置：`backend/src/qts/core/ids.py:51`
- 类型：`class`
- 签名：`class BacktestRunId(_StringId)`
- 作用：Stable identifier for a backtest run.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine.run_streaming`

#### `qts.core.ids.CorrelationId`
- 位置：`backend/src/qts/core/ids.py:55`
- 类型：`class`
- 签名：`class CorrelationId(_StringId)`
- 作用：Identifier grouping events in one business workflow.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.event_store.FileEventStore._event_from_json`

#### `qts.core.ids.CausationId`
- 位置：`backend/src/qts/core/ids.py:59`
- 类型：`class`
- 签名：`class CausationId(_StringId)`
- 作用：Identifier linking an event to the event that caused it.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.event_store.FileEventStore._event_from_json`

### `qts.core.time`

模块：`qts.core.time`

#### `qts.core.time.require_aware_datetime`
- 位置：`backend/src/qts/core/time.py:10`
- 类型：`module_function`
- 签名：`def require_aware_datetime(value: datetime, *, name: str) -> None`
- 作用：Validate that a datetime has an effective timezone.
- 直接原始调用：`ValueError`, `value.utcoffset`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.core.time.TimeInterval.__post_init__`, `qts.core.time.TimeInterval.contains`, `qts.core.time.to_exchange_time`, `qts.data.provenance.DatasetMetadata.__post_init__`, `qts.domain.events.event.BaseEvent.__post_init__`, `qts.domain.events.metadata.EventMetadata.__post_init__`, `qts.domain.market_data.bar.Quote.__post_init__`, `qts.domain.market_data.bar.Tick.__post_init__`, `qts.domain.risk.request.OrderRiskRequest.__post_init__`

#### `qts.core.time.to_exchange_time`
- 位置：`backend/src/qts/core/time.py:17`
- 类型：`module_function`
- 签名：`def to_exchange_time(value: datetime, exchange_timezone: str | tzinfo) -> datetime`
- 作用：Convert a timestamp representation into an exchange timezone.
- 直接原始调用：`ZoneInfo`, `isinstance`, `require_aware_datetime`, `value.astimezone`
- 已解析到仓库内部的调用：`qts.core.time.require_aware_datetime`
- 被以下仓库内部符号调用：`qts.data.bars.alignment.clock_bucket_for`, `qts.data.sessions.window.RegularSessionWindow.session_date_for_timestamp`

#### `qts.core.time.TimeInterval`
- 位置：`backend/src/qts/core/time.py:28`
- 类型：`class`
- 签名：`class TimeInterval`
- 作用：A half-open time interval with `[start, end)` membership.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.bars.aggregator.BarAggregator._new_state_for`, `qts.data.bars.alignment.clock_bucket_for`, `qts.domain.market_data.bar.Bar.__post_init__`, `qts.domain.market_data.bar.Bar.interval`, `qts.registry.providers.comex_gold_calendar_provider.ComexGoldCalendarProvider.session_for`, `qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider.session_for`

#### `qts.core.time.TimeInterval.__post_init__`
- 位置：`backend/src/qts/core/time.py:34`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`require_aware_datetime` x2, `ValueError`
- 已解析到仓库内部的调用：`qts.core.time.require_aware_datetime`
- 被以下仓库内部符号调用：无

#### `qts.core.time.TimeInterval.duration`
- 位置：`backend/src/qts/core/time.py:42`
- 类型：`property`
- 签名：`def duration(self) -> timedelta`
- 作用：Perform duration.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.core.time.TimeInterval.contains`
- 位置：`backend/src/qts/core/time.py:46`
- 类型：`method`
- 签名：`def contains(self, value: datetime) -> bool`
- 作用：Perform contains.
- 直接原始调用：`require_aware_datetime`
- 已解析到仓库内部的调用：`qts.core.time.require_aware_datetime`
- 被以下仓库内部符号调用：无

### `qts.data.adapters.ibkr_market_data`

模块：`qts.data.adapters.ibkr_market_data`

#### `qts.data.adapters.ibkr_market_data.IbkrMarketDataConnection`
- 位置：`backend/src/qts/data/adapters/ibkr_market_data.py:15`
- 类型：`class`
- 签名：`class IbkrMarketDataConnection`
- 作用：IBKR market data connection settings.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.adapters.ibkr_market_data.IbkrMarketDataConnection.__post_init__`
- 位置：`backend/src/qts/data/adapters/ibkr_market_data.py:23`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError` x4, `self.host.strip`, `self.source_id.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.adapters.ibkr_market_data.IbkrMarketDataSubscription`
- 位置：`backend/src/qts/data/adapters/ibkr_market_data.py:36`
- 类型：`class`
- 签名：`class IbkrMarketDataSubscription`
- 作用：IBKR market data subscription request at the adapter boundary.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter.subscription_for`

#### `qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter`
- 位置：`backend/src/qts/data/adapters/ibkr_market_data.py:44`
- 类型：`class`
- 签名：`class IbkrMarketDataAdapter`
- 作用：Normalizes IBKR market data without owning order execution.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter.__init__`
- 位置：`backend/src/qts/data/adapters/ibkr_market_data.py:47`
- 类型：`method`
- 签名：`def __init__(self, *, connection: IbkrMarketDataConnection, symbol_mapping: BrokerSymbolMapping) -> None`
- 作用：Perform __init__.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter.subscription_for`
- 位置：`backend/src/qts/data/adapters/ibkr_market_data.py:57`
- 类型：`method`
- 签名：`def subscription_for(self, instrument_id: InstrumentId) -> IbkrMarketDataSubscription`
- 作用：Perform subscription_for.
- 直接原始调用：`IbkrMarketDataSubscription`, `self._symbol_mapping.to_broker_symbol`
- 已解析到仓库内部的调用：`qts.data.adapters.ibkr_market_data.IbkrMarketDataSubscription`
- 被以下仓库内部符号调用：无

#### `qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter.normalize_tick`
- 位置：`backend/src/qts/data/adapters/ibkr_market_data.py:65`
- 类型：`method`
- 签名：`def normalize_tick(self, *, broker_symbol: str, time: datetime, price: Decimal, size: Decimal=Decimal('0')) -> Tick`
- 作用：Perform normalize_tick.
- 直接原始调用：`Tick`, `self._symbol_mapping.to_instrument_id`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter.normalize_quote`
- 位置：`backend/src/qts/data/adapters/ibkr_market_data.py:81`
- 类型：`method`
- 签名：`def normalize_quote(self, *, broker_symbol: str, time: datetime, bid_price: Decimal, ask_price: Decimal, bid_size: Decimal=Decimal('0'), ask_size: Decimal=Decimal('0')) -> Quote`
- 作用：Perform normalize_quote.
- 直接原始调用：`Quote`, `self._symbol_mapping.to_instrument_id`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter.normalize_bar`
- 位置：`backend/src/qts/data/adapters/ibkr_market_data.py:101`
- 类型：`method`
- 签名：`def normalize_bar(self, *, broker_symbol: str, start_time: datetime, end_time: datetime, timeframe: str, session_id: str, open: Decimal, high: Decimal, low: Decimal, close: Decimal, volume: Decimal=Decimal('0'), vwap: Decimal | None=None, open_interest: Decimal | None=None, trade_count: int | None=None, is_complete: bool=False, is_partial: bool=False) -> Bar`
- 作用：Perform normalize_bar.
- 直接原始调用：`Bar`, `self._symbol_mapping.to_instrument_id`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.data.bars.aggregator`

模块：`qts.data.bars.aggregator`

#### `qts.data.bars.aggregator.AggregationState`
- 位置：`backend/src/qts/data/bars/aggregator.py:18`
- 类型：`class`
- 签名：`class AggregationState`
- 作用：Current in-progress aggregation bucket.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.bars.aggregator.BarAggregator._new_state_for`, `qts.data.bars.aggregator.BarAggregator.update`

#### `qts.data.bars.aggregator.AggregationState.aggregate_end`
- 位置：`backend/src/qts/data/bars/aggregator.py:27`
- 类型：`property`
- 签名：`def aggregate_end(self) -> datetime`
- 作用：Perform aggregate_end.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.bars.aggregator.AggregationResult`
- 位置：`backend/src/qts/data/bars/aggregator.py:33`
- 类型：`class`
- 签名：`class AggregationResult`
- 作用：Result returned by one incremental aggregator update.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.bars.aggregator.BarAggregator.finish`, `qts.data.bars.aggregator.BarAggregator.update`

#### `qts.data.bars.aggregator.BarAggregator`
- 位置：`backend/src/qts/data/bars/aggregator.py:40`
- 类型：`class`
- 签名：`class BarAggregator`
- 作用：Stateful incremental bar aggregator for one ordered bar stream.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.bars.aggregator.aggregate_bars`, `qts.data.bars.pipeline.BarAggregationPipeline._aggregator_for`

#### `qts.data.bars.aggregator.BarAggregator.__init__`
- 位置：`backend/src/qts/data/bars/aggregator.py:43`
- 类型：`method`
- 签名：`def __init__(self, *, target_timeframe: Timeframe, exchange_timezone: str | tzinfo, session: MarketSession | None=None) -> None`
- 作用：Perform __init__.
- 直接原始调用：`ValueError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.bars.aggregator.BarAggregator.update`
- 位置：`backend/src/qts/data/bars/aggregator.py:58`
- 类型：`method`
- 签名：`def update(self, bar: Bar) -> AggregationResult`
- 作用：Add a lower-timeframe bar and return any completed aggregate bars.
- 直接原始调用：`AggregationResult` x2, `_aggregate_state` x2, `completed.append` x2, `AggregationState`, `_bar_inside_session`, `_same_stream_bucket`, `self._new_state_for`, `tuple`
- 已解析到仓库内部的调用：`qts.data.bars.aggregator.AggregationResult`, `qts.data.bars.aggregator._bar_inside_session`, `qts.data.bars.aggregator.BarAggregator._new_state_for`, `qts.data.bars.aggregator._same_stream_bucket`, `qts.data.bars.aggregator._aggregate_state`, `qts.data.bars.aggregator.AggregationState`
- 被以下仓库内部符号调用：无

#### `qts.data.bars.aggregator.BarAggregator.finish`
- 位置：`backend/src/qts/data/bars/aggregator.py:87`
- 类型：`method`
- 签名：`def finish(self) -> AggregationResult`
- 作用：Flush the current bucket as a partial aggregate when present.
- 直接原始调用：`AggregationResult` x2, `_aggregate_state`
- 已解析到仓库内部的调用：`qts.data.bars.aggregator.AggregationResult`, `qts.data.bars.aggregator._aggregate_state`
- 被以下仓库内部符号调用：无

#### `qts.data.bars.aggregator.BarAggregator._new_state_for`
- 位置：`backend/src/qts/data/bars/aggregator.py:96`
- 类型：`method`
- 签名：`def _new_state_for(self, bar: Bar) -> AggregationState`
- 作用：Perform _new_state_for.
- 直接原始调用：`AggregationState`, `TimeInterval`, `clock_bucket_for`
- 已解析到仓库内部的调用：`qts.data.bars.alignment.clock_bucket_for`, `qts.data.bars.aggregator.AggregationState`, `qts.core.time.TimeInterval`
- 被以下仓库内部符号调用：`qts.data.bars.aggregator.BarAggregator.update`

#### `qts.data.bars.aggregator.aggregate_bars`
- 位置：`backend/src/qts/data/bars/aggregator.py:110`
- 类型：`module_function`
- 签名：`def aggregate_bars(bars: Iterable[Bar], *, target_timeframe: Timeframe, exchange_timezone: str | tzinfo, session: MarketSession | None=None) -> list[Bar]`
- 作用：Aggregate bars into a higher clock-aligned timeframe.
- 直接原始调用：`aggregated.extend` x2, `sorted` x2, `BarAggregator`, `aggregator.finish`, `aggregator.update`, `aggregators.setdefault`, `aggregators.values`
- 已解析到仓库内部的调用：`qts.data.bars.aggregator.BarAggregator`
- 被以下仓库内部符号调用：无

#### `qts.data.bars.aggregator._bar_inside_session`
- 位置：`backend/src/qts/data/bars/aggregator.py:139`
- 类型：`module_function`
- 签名：`def _bar_inside_session(bar: Bar, session: MarketSession) -> bool`
- 作用：Perform _bar_inside_session.
- 直接原始调用：`session.interval.contains`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.bars.aggregator.BarAggregator.update`

#### `qts.data.bars.aggregator._same_stream_bucket`
- 位置：`backend/src/qts/data/bars/aggregator.py:144`
- 类型：`module_function`
- 签名：`def _same_stream_bucket(left: AggregationState, right: AggregationState) -> bool`
- 作用：Perform _same_stream_bucket.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.bars.aggregator.BarAggregator.update`

#### `qts.data.bars.aggregator._aggregate_state`
- 位置：`backend/src/qts/data/bars/aggregator.py:153`
- 类型：`module_function`
- 签名：`def _aggregate_state(state: AggregationState) -> Bar`
- 作用：Perform _aggregate_state.
- 直接原始调用：`ValueError` x3, `Bar`, `Decimal`, `_aggregate_vwap`, `_last_open_interest`, `_sum_trade_count`, `all`, `max`, `min`, `str`, `sum`
- 已解析到仓库内部的调用：`qts.data.bars.aggregator._aggregate_vwap`, `qts.data.bars.aggregator._last_open_interest`, `qts.data.bars.aggregator._sum_trade_count`
- 被以下仓库内部符号调用：`qts.data.bars.aggregator.BarAggregator.finish`, `qts.data.bars.aggregator.BarAggregator.update`

#### `qts.data.bars.aggregator._aggregate_vwap`
- 位置：`backend/src/qts/data/bars/aggregator.py:194`
- 类型：`module_function`
- 签名：`def _aggregate_vwap(bars: tuple[Bar, ...], total_volume: Decimal) -> Decimal | None`
- 作用：Perform _aggregate_vwap.
- 直接原始调用：`Decimal` x3, `sum`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.bars.aggregator._aggregate_state`

#### `qts.data.bars.aggregator._last_open_interest`
- 位置：`backend/src/qts/data/bars/aggregator.py:204`
- 类型：`module_function`
- 签名：`def _last_open_interest(bars: tuple[Bar, ...]) -> Decimal | None`
- 作用：Perform _last_open_interest.
- 直接原始调用：`reversed`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.bars.aggregator._aggregate_state`

#### `qts.data.bars.aggregator._sum_trade_count`
- 位置：`backend/src/qts/data/bars/aggregator.py:212`
- 类型：`module_function`
- 签名：`def _sum_trade_count(bars: tuple[Bar, ...]) -> int | None`
- 作用：Perform _sum_trade_count.
- 直接原始调用：`sum`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.bars.aggregator._aggregate_state`

### `qts.data.bars.alignment`

模块：`qts.data.bars.alignment`

#### `qts.data.bars.alignment.clock_bucket_for`
- 位置：`backend/src/qts/data/bars/alignment.py:11`
- 类型：`module_function`
- 签名：`def clock_bucket_for(timestamp: datetime, timeframe: Timeframe, exchange_timezone: str | tzinfo) -> TimeInterval`
- 作用：Return the exchange-clock bucket containing ``timestamp``.
- 直接原始调用：`TimeInterval`, `ValueError`, `_duration_seconds`, `exchange_time.replace`, `int`, `timedelta`, `to_exchange_time`
- 已解析到仓库内部的调用：`qts.core.time.to_exchange_time`, `qts.data.bars.alignment._duration_seconds`, `qts.core.time.TimeInterval`
- 被以下仓库内部符号调用：`qts.data.bars.aggregator.BarAggregator._new_state_for`

#### `qts.data.bars.alignment._duration_seconds`
- 位置：`backend/src/qts/data/bars/alignment.py:36`
- 类型：`module_function`
- 签名：`def _duration_seconds(duration: timedelta) -> int`
- 作用：Perform _duration_seconds.
- 直接原始调用：`ValueError` x2, `duration.total_seconds`, `int`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.bars.alignment.clock_bucket_for`

### `qts.data.bars.pipeline`

模块：`qts.data.bars.pipeline`

#### `qts.data.bars.pipeline.BarAggregationPipeline`
- 位置：`backend/src/qts/data/bars/pipeline.py:15`
- 类型：`class`
- 签名：`class BarAggregationPipeline`
- 作用：Own incremental aggregation state for bar streams in memory.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.actors.market_data_actor.MarketDataActor.__init__`

#### `qts.data.bars.pipeline.BarAggregationPipeline.__init__`
- 位置：`backend/src/qts/data/bars/pipeline.py:18`
- 类型：`method`
- 签名：`def __init__(self, exchange_timezone: str | tzinfo) -> None`
- 作用：Perform __init__.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.bars.pipeline.BarAggregationPipeline.aggregate`
- 位置：`backend/src/qts/data/bars/pipeline.py:23`
- 类型：`method`
- 签名：`def aggregate(self, bar: Bar, target_timeframe: Timeframe) -> tuple[Bar, ...]`
- 作用：Aggregate one 1+ minute bar into an explicit target timeframe.
- 直接原始调用：`self._aggregation_key`, `self._aggregator_for`, `self._aggregator_for.update`
- 已解析到仓库内部的调用：`qts.data.bars.pipeline.BarAggregationPipeline._aggregation_key`, `qts.data.bars.pipeline.BarAggregationPipeline._aggregator_for`
- 被以下仓库内部符号调用：无

#### `qts.data.bars.pipeline.BarAggregationPipeline.aggregate_logical`
- 位置：`backend/src/qts/data/bars/pipeline.py:29`
- 类型：`method`
- 签名：`def aggregate_logical(self, bar: Bar, *, source_timeframe: str, target_timeframe: str) -> tuple[Bar, ...]`
- 作用：Aggregate bars from one source timeframe into a logical subscriber target.
- 直接原始调用：`Timeframe.parse`, `self._aggregator_for`, `self._aggregator_for.update`, `self._logical_key`
- 已解析到仓库内部的调用：`qts.data.bars.timeframe.Timeframe.parse`, `qts.data.bars.pipeline.BarAggregationPipeline._logical_key`, `qts.data.bars.pipeline.BarAggregationPipeline._aggregator_for`
- 被以下仓库内部符号调用：无

#### `qts.data.bars.pipeline.BarAggregationPipeline._aggregator_for`
- 位置：`backend/src/qts/data/bars/pipeline.py:42`
- 类型：`method`
- 签名：`def _aggregator_for(self, key: tuple[object, ...], target_timeframe: Timeframe) -> BarAggregator`
- 作用：Perform _aggregator_for.
- 直接原始调用：`BarAggregator`, `self._aggregators.get`
- 已解析到仓库内部的调用：`qts.data.bars.aggregator.BarAggregator`
- 被以下仓库内部符号调用：`qts.data.bars.pipeline.BarAggregationPipeline.aggregate`, `qts.data.bars.pipeline.BarAggregationPipeline.aggregate_logical`

#### `qts.data.bars.pipeline.BarAggregationPipeline._aggregation_key`
- 位置：`backend/src/qts/data/bars/pipeline.py:56`
- 类型：`staticmethod`
- 签名：`def _aggregation_key(bar: Bar, timeframe: Timeframe) -> tuple[object, ...]`
- 作用：Perform _aggregation_key.
- 直接原始调用：`str`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.bars.pipeline.BarAggregationPipeline.aggregate`

#### `qts.data.bars.pipeline.BarAggregationPipeline._logical_key`
- 位置：`backend/src/qts/data/bars/pipeline.py:61`
- 类型：`staticmethod`
- 签名：`def _logical_key(bar: Bar, source_timeframe: str, target_timeframe: str) -> tuple[object, ...]`
- 作用：Perform _logical_key.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.bars.pipeline.BarAggregationPipeline.aggregate_logical`

### `qts.data.bars.timeframe`

模块：`qts.data.bars.timeframe`

#### `qts.data.bars.timeframe.AlignmentMode`
- 位置：`backend/src/qts/data/bars/timeframe.py:10`
- 类型：`class`
- 签名：`class AlignmentMode(StrEnum)`
- 作用：How bars for a timeframe align to time.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.bars.timeframe.Timeframe`
- 位置：`backend/src/qts/data/bars/timeframe.py:29`
- 类型：`class`
- 签名：`class Timeframe`
- 作用：Bar timeframe with explicit alignment semantics.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.bars.timeframe.Timeframe.parse`
- 位置：`backend/src/qts/data/bars/timeframe.py:37`
- 类型：`classmethod`
- 签名：`def parse(cls, value: str) -> Timeframe`
- 作用：Perform parse.
- 直接原始调用：`cls` x2, `ValueError`, `value.strip`, `value.strip.lower`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.bars.pipeline.BarAggregationPipeline.aggregate_logical`, `qts.runtime.actors.market_data_actor.MarketDataActor.__init__`

#### `qts.data.bars.timeframe.Timeframe.__str__`
- 位置：`backend/src/qts/data/bars/timeframe.py:50`
- 类型：`method`
- 签名：`def __str__(self) -> str`
- 作用：Perform __str__.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.data.feeds.replay_feed`

模块：`qts.data.feeds.replay_feed`

#### `qts.data.feeds.replay_feed.ReplayFeed`
- 位置：`backend/src/qts/data/feeds/replay_feed.py:12`
- 类型：`class`
- 签名：`class ReplayFeed`
- 作用：Deterministic replay feed over stored bars.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.feeds.replay_feed.ReplayFeed.__init__`
- 位置：`backend/src/qts/data/feeds/replay_feed.py:15`
- 类型：`method`
- 签名：`def __init__(self, store: MarketDataStore) -> None`
- 作用：Perform __init__.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.feeds.replay_feed.ReplayFeed.events`
- 位置：`backend/src/qts/data/feeds/replay_feed.py:19`
- 类型：`method`
- 签名：`def events(self, *, instrument_id: InstrumentId, timeframe: str, start: datetime, end: datetime) -> tuple[Bar, ...]`
- 作用：Perform events.
- 直接原始调用：`self._store.read_bars`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.data.historical.catalog`

模块：`qts.data.historical.catalog`

#### `qts.data.historical.catalog.HistoricalDataset`
- 位置：`backend/src/qts/data/historical/catalog.py:19`
- 类型：`class`
- 签名：`class HistoricalDataset`
- 作用：One local historical dataset entry.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.catalog.HistoricalCatalog.from_historical_data_config`, `qts.data.historical.catalog.HistoricalCatalog.from_legacy_root`

#### `qts.data.historical.catalog.HistoricalDataset.normalize_root`
- 位置：`backend/src/qts/data/historical/catalog.py:34`
- 类型：`staticmethod`
- 签名：`def normalize_root(root: str) -> str`
- 作用：Perform normalize_root.
- 直接原始调用：`ValueError`, `root.strip`, `root.strip.upper`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.catalog.HistoricalCatalog.from_historical_data_config`, `qts.data.historical.catalog.HistoricalCatalog.from_legacy_root`, `qts.data.historical.catalog.HistoricalCatalogLoadConfig.__post_init__`

#### `qts.data.historical.catalog.HistoricalCatalog`
- 位置：`backend/src/qts/data/historical/catalog.py:43`
- 类型：`class`
- 签名：`class HistoricalCatalog`
- 作用：Explicit catalog for a local historical data layout.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.historical.catalog.HistoricalCatalog.load`
- 位置：`backend/src/qts/data/historical/catalog.py:51`
- 类型：`classmethod`
- 签名：`def load(cls, config: HistoricalCatalogLoadConfig) -> HistoricalCatalog`
- 作用：Load a catalog from one cohesive construction config.
- 直接原始调用：`RuntimeError` x2, `HistoricalDataConfig.from_yaml`, `cls._symbol_resolvers_for_load_config`, `cls.from_historical_data_config`, `cls.from_legacy_root`
- 已解析到仓库内部的调用：`qts.data.historical.config.HistoricalDataConfig.from_yaml`, `qts.data.historical.catalog.HistoricalCatalog._symbol_resolvers_for_load_config`, `qts.data.historical.catalog.HistoricalCatalog.from_historical_data_config`, `qts.data.historical.catalog.HistoricalCatalog.from_legacy_root`
- 被以下仓库内部符号调用：`qts.backtest.runner.run_backtest`

#### `qts.data.historical.catalog.HistoricalCatalog.from_legacy_root`
- 位置：`backend/src/qts/data/historical/catalog.py:80`
- 类型：`classmethod`
- 签名：`def from_legacy_root(cls, root_path: Path, *, roots: tuple[str, ...], symbol_resolvers: Mapping[str, SourceSymbolResolver] | None=None, count_rows: bool=False) -> HistoricalCatalog`
- 作用：Load requested roots from a local historical data directory.
- 直接原始调用：`HistoricalDataset.normalize_root` x2, `cls._require_file` x2, `HistoricalChain.load`, `HistoricalDataset`, `HistoricalFutureChainSymbolResolver`, `ValueError`, `cls`, `describe_csv_dataset`, `resolvers.get`, `root.lower`, `symbol_resolvers or {}.items`, `tuple`
- 已解析到仓库内部的调用：`qts.data.historical.catalog.HistoricalDataset.normalize_root`, `qts.data.historical.catalog.HistoricalCatalog._require_file`, `qts.data.historical.csv_dataset.describe_csv_dataset`, `qts.data.historical.catalog.HistoricalDataset`, `qts.data.historical.chains.HistoricalChain.load`, `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver`
- 被以下仓库内部符号调用：`qts.data.historical.catalog.HistoricalCatalog.load`, `scripts.validate_historical.main`

#### `qts.data.historical.catalog.HistoricalCatalog.from_historical_data_config`
- 位置：`backend/src/qts/data/historical/catalog.py:124`
- 类型：`classmethod`
- 签名：`def from_historical_data_config(cls, config: HistoricalDataConfig, *, catalog: str, roots: tuple[str, ...], symbol_resolvers: Mapping[str, SourceSymbolResolver] | None=None, count_rows: bool=False, requested_timeframe: str | None=None) -> HistoricalCatalog`
- 作用：Load requested roots from a project-level historical data catalog.
- 直接原始调用：`HistoricalDataset.normalize_root` x2, `cls._require_file` x2, `FileNotFoundError`, `HistoricalChain.load`, `HistoricalDataset`, `HistoricalFutureChainSymbolResolver`, `ValueError`, `cls`, `config.catalog`, `config.resolve_dataset`, `config.store`, `describe_csv_dataset`, `resolvers.get`, `symbol_resolvers or {}.items`, `tuple`
- 已解析到仓库内部的调用：`qts.data.historical.catalog.HistoricalDataset.normalize_root`, `qts.data.historical.catalog.HistoricalCatalog._require_file`, `qts.data.historical.csv_dataset.describe_csv_dataset`, `qts.data.historical.catalog.HistoricalDataset`, `qts.data.historical.chains.HistoricalChain.load`, `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver`
- 被以下仓库内部符号调用：`qts.data.historical.catalog.HistoricalCatalog.load`

#### `qts.data.historical.catalog.HistoricalCatalog._symbol_resolvers_for_load_config`
- 位置：`backend/src/qts/data/historical/catalog.py:186`
- 类型：`classmethod`
- 签名：`def _symbol_resolvers_for_load_config(cls, config: HistoricalCatalogLoadConfig, *, historical_data_config: HistoricalDataConfig | None) -> dict[str, StaticSymbolResolver]`
- 作用：Perform _symbol_resolvers_for_load_config.
- 直接原始调用：`StaticSymbolResolver`, `cls._chain_path_exists`
- 已解析到仓库内部的调用：`qts.registry.symbol_resolution.StaticSymbolResolver`, `qts.data.historical.catalog.HistoricalCatalog._chain_path_exists`
- 被以下仓库内部符号调用：`qts.data.historical.catalog.HistoricalCatalog.load`

#### `qts.data.historical.catalog.HistoricalCatalog._chain_path_exists`
- 位置：`backend/src/qts/data/historical/catalog.py:206`
- 类型：`staticmethod`
- 签名：`def _chain_path_exists(config: HistoricalCatalogLoadConfig, root: str, *, historical_data_config: HistoricalDataConfig | None) -> bool`
- 作用：Perform _chain_path_exists.
- 直接原始调用：`RuntimeError`, `chain_path.exists`, `config.legacy_root_path / 'chains' / f'{root}.json'.exists`, `historical_data_config.resolve_chain_path`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.catalog.HistoricalCatalog._symbol_resolvers_for_load_config`

#### `qts.data.historical.catalog.HistoricalCatalog._require_file`
- 位置：`backend/src/qts/data/historical/catalog.py:223`
- 类型：`staticmethod`
- 签名：`def _require_file(path: Path, root_path: Path) -> None`
- 作用：Perform _require_file.
- 直接原始调用：`FileNotFoundError`, `Path`, `path.exists`, `path.relative_to`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.catalog.HistoricalCatalog.from_historical_data_config`, `qts.data.historical.catalog.HistoricalCatalog.from_legacy_root`

#### `qts.data.historical.catalog.HistoricalCatalogLoadConfig`
- 位置：`backend/src/qts/data/historical/catalog.py:234`
- 类型：`class`
- 签名：`class HistoricalCatalogLoadConfig`
- 作用：Construction inputs for a configured historical catalog.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.historical.catalog.HistoricalCatalogLoadConfig.__post_init__`
- 位置：`backend/src/qts/data/historical/catalog.py:244`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`object.__setattr__` x6, `ValueError` x5, `Path` x2, `HistoricalDataset.normalize_root`, `InstrumentId`, `isinstance`, `self._normalize_symbol`, `self.catalog_name.strip`, `self.instrument_ids.items`, `self.requested_timeframe.strip`, `str`, `tuple`
- 已解析到仓库内部的调用：`qts.data.historical.catalog.HistoricalDataset.normalize_root`, `qts.data.historical.catalog.HistoricalCatalogLoadConfig._normalize_symbol`, `qts.core.ids.InstrumentId`
- 被以下仓库内部符号调用：无

#### `qts.data.historical.catalog.HistoricalCatalogLoadConfig.from_legacy_root`
- 位置：`backend/src/qts/data/historical/catalog.py:286`
- 类型：`classmethod`
- 签名：`def from_legacy_root(cls, root_path: Path, *, roots: tuple[str, ...], instrument_ids: Mapping[str, InstrumentId] | None=None, requested_timeframe: str | None=None) -> HistoricalCatalogLoadConfig`
- 作用：Perform from_legacy_root.
- 直接原始调用：`cls`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.runner._catalog_load_config`

#### `qts.data.historical.catalog.HistoricalCatalogLoadConfig.from_historical_data_config`
- 位置：`backend/src/qts/data/historical/catalog.py:303`
- 类型：`classmethod`
- 签名：`def from_historical_data_config(cls, config_path: Path, *, catalog: str, roots: tuple[str, ...], instrument_ids: Mapping[str, InstrumentId] | None=None, requested_timeframe: str | None=None) -> HistoricalCatalogLoadConfig`
- 作用：Perform from_historical_data_config.
- 直接原始调用：`cls`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.runner._catalog_load_config`

#### `qts.data.historical.catalog.HistoricalCatalogLoadConfig._normalize_symbol`
- 位置：`backend/src/qts/data/historical/catalog.py:322`
- 类型：`staticmethod`
- 签名：`def _normalize_symbol(symbol: str) -> str`
- 作用：Perform _normalize_symbol.
- 直接原始调用：`ValueError`, `symbol.strip`, `symbol.strip.upper`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.catalog.HistoricalCatalogLoadConfig.__post_init__`

### `qts.data.historical.chains`

模块：`qts.data.historical.chains`

#### `qts.data.historical.chains.HistoricalContract`
- 位置：`backend/src/qts/data/historical/chains.py:16`
- 类型：`class`
- 签名：`class HistoricalContract`
- 作用：One outright contract from a historical chain file.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.chains.HistoricalChain._parse_contract`

#### `qts.data.historical.chains.HistoricalChain`
- 位置：`backend/src/qts/data/historical/chains.py:31`
- 类型：`class`
- 签名：`class HistoricalChain`
- 作用：Parsed historical futures chain.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.historical.chains.HistoricalChain.__post_init__`
- 位置：`backend/src/qts/data/historical/chains.py:44`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`contracts_by_symbol.setdefault`, `object.__setattr__`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.historical.chains.HistoricalChain.contract_for_symbol`
- 位置：`backend/src/qts/data/historical/chains.py:55`
- 类型：`method`
- 签名：`def contract_for_symbol(self, symbol: str) -> HistoricalContract`
- 作用：Perform contract_for_symbol.
- 直接原始调用：`KeyError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.historical.chains.HistoricalChain.is_outright_symbol`
- 位置：`backend/src/qts/data/historical/chains.py:62`
- 类型：`method`
- 签名：`def is_outright_symbol(self, symbol: str) -> bool`
- 作用：Perform is_outright_symbol.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.chains.HistoricalChain.instrument_id_for_symbol`

#### `qts.data.historical.chains.HistoricalChain.instrument_id_for_symbol`
- 位置：`backend/src/qts/data/historical/chains.py:66`
- 类型：`method`
- 签名：`def instrument_id_for_symbol(self, symbol: str) -> InstrumentId`
- 作用：Perform instrument_id_for_symbol.
- 直接原始调用：`InstrumentId`, `ValueError`, `self.is_outright_symbol`
- 已解析到仓库内部的调用：`qts.data.historical.chains.HistoricalChain.is_outright_symbol`, `qts.core.ids.InstrumentId`
- 被以下仓库内部符号调用：无

#### `qts.data.historical.chains.HistoricalChain.load`
- 位置：`backend/src/qts/data/historical/chains.py:73`
- 类型：`classmethod`
- 签名：`def load(cls, path: Path) -> HistoricalChain`
- 作用：Load a historical futures chain JSON file into typed metadata.
- 直接原始调用：`cls._required_text` x5, `cls._required_decimal` x2, `ValueError`, `cls`, `cls._exchange_code`, `cls._parse_contract`, `isinstance`, `json.loads`, `path.read_text`, `payload.get`, `tuple`
- 已解析到仓库内部的调用：`qts.data.historical.chains.HistoricalChain._required_text`, `qts.data.historical.chains.HistoricalChain._exchange_code`, `qts.data.historical.chains.HistoricalChain._required_decimal`, `qts.data.historical.chains.HistoricalChain._parse_contract`
- 被以下仓库内部符号调用：`qts.data.historical.catalog.HistoricalCatalog.from_historical_data_config`, `qts.data.historical.catalog.HistoricalCatalog.from_legacy_root`

#### `qts.data.historical.chains.HistoricalChain._parse_contract`
- 位置：`backend/src/qts/data/historical/chains.py:112`
- 类型：`classmethod`
- 签名：`def _parse_contract(cls, payload: object, *, root: str, exchange: str, chain_currency: str, chain_tick_size: Decimal, chain_multiplier: Decimal, chain_calendar: str) -> HistoricalContract`
- 作用：Perform _parse_contract.
- 直接原始调用：`cls._required_text` x3, `item.get` x2, `str` x2, `HistoricalContract`, `ValueError`, `date.fromisoformat`, `datetime.fromisoformat`, `datetime.fromisoformat.astimezone`, `isinstance`
- 已解析到仓库内部的调用：`qts.data.historical.chains.HistoricalChain._required_text`, `qts.data.historical.chains.HistoricalContract`
- 被以下仓库内部符号调用：`qts.data.historical.chains.HistoricalChain.load`

#### `qts.data.historical.chains.HistoricalChain._required_text`
- 位置：`backend/src/qts/data/historical/chains.py:143`
- 类型：`staticmethod`
- 签名：`def _required_text(payload: dict[str, Any], field: str) -> str`
- 作用：Perform _required_text.
- 直接原始调用：`ValueError`, `isinstance`, `payload.get`, `value.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.chains.HistoricalChain._parse_contract`, `qts.data.historical.chains.HistoricalChain.load`

#### `qts.data.historical.chains.HistoricalChain._required_decimal`
- 位置：`backend/src/qts/data/historical/chains.py:151`
- 类型：`staticmethod`
- 签名：`def _required_decimal(payload: dict[str, Any], field: str) -> Decimal`
- 作用：Perform _required_decimal.
- 直接原始调用：`Decimal` x2, `ValueError` x2, `str`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.chains.HistoricalChain.load`

#### `qts.data.historical.chains.HistoricalChain._exchange_code`
- 位置：`backend/src/qts/data/historical/chains.py:161`
- 类型：`staticmethod`
- 签名：`def _exchange_code(market: str) -> str`
- 作用：Perform _exchange_code.
- 直接原始调用：`market.endswith`, `market.removesuffix`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.chains.HistoricalChain.load`

### `qts.data.historical.config`

模块：`qts.data.historical.config`

#### `qts.data.historical.config.HistoricalDataStoreDefaults`
- 位置：`backend/src/qts/data/historical/config.py:14`
- 类型：`class`
- 签名：`class HistoricalDataStoreDefaults`
- 作用：Default metadata applied to datasets and bars in one historical store.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_store_defaults`

#### `qts.data.historical.config.HistoricalDataStoreDefaults.__post_init__`
- 位置：`backend/src/qts/data/historical/config.py:22`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError` x4, `self.exchange_timezone.strip`, `self.normalization.strip`, `self.schema.strip`, `self.timezone_policy.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.historical.config.HistoricalDataStoreConfig`
- 位置：`backend/src/qts/data/historical/config.py:35`
- 类型：`class`
- 签名：`class HistoricalDataStoreConfig`
- 作用：Project-level physical layout for a historical data store.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_stores`

#### `qts.data.historical.config.HistoricalDataStoreConfig.__post_init__`
- 位置：`backend/src/qts/data/historical/config.py:51`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError` x9, `self.bars_file_template.strip`, `self.chain_file_template.strip`, `self.exchange_timezone.strip`, `self.name.strip`, `self.normalization.strip`, `self.source_timeframe.strip`, `self.timezone_policy.strip`, `self.type.strip`, `str`, `str.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.historical.config.HistoricalDataStoreConfig.bars_path`
- 位置：`backend/src/qts/data/historical/config.py:72`
- 类型：`method`
- 签名：`def bars_path(self, root: str, *, override: str | None=None) -> Path`
- 作用：Perform bars_path.
- 直接原始调用：`self._join`, `self._render_template`
- 已解析到仓库内部的调用：`qts.data.historical.config.HistoricalDataStoreConfig._render_template`, `qts.data.historical.config.HistoricalDataStoreConfig._join`
- 被以下仓库内部符号调用：无

#### `qts.data.historical.config.HistoricalDataStoreConfig.chain_path`
- 位置：`backend/src/qts/data/historical/config.py:77`
- 类型：`method`
- 签名：`def chain_path(self, root: str, *, override: str | None=None) -> Path`
- 作用：Perform chain_path.
- 直接原始调用：`self._join`, `self._render_template`
- 已解析到仓库内部的调用：`qts.data.historical.config.HistoricalDataStoreConfig._render_template`, `qts.data.historical.config.HistoricalDataStoreConfig._join`
- 被以下仓库内部符号调用：无

#### `qts.data.historical.config.HistoricalDataStoreConfig._join`
- 位置：`backend/src/qts/data/historical/config.py:82`
- 类型：`method`
- 签名：`def _join(self, path: Path) -> Path`
- 作用：Perform _join.
- 直接原始调用：`path.is_absolute`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.config.HistoricalDataStoreConfig.bars_path`, `qts.data.historical.config.HistoricalDataStoreConfig.chain_path`

#### `qts.data.historical.config.HistoricalDataStoreConfig._render_template`
- 位置：`backend/src/qts/data/historical/config.py:87`
- 类型：`staticmethod`
- 签名：`def _render_template(template: str, root: str) -> str`
- 作用：Perform _render_template.
- 直接原始调用：`HistoricalDatasetConfig.normalize_root`, `normalized_root.lower`, `template.format`
- 已解析到仓库内部的调用：`qts.data.historical.config.HistoricalDatasetConfig.normalize_root`
- 被以下仓库内部符号调用：`qts.data.historical.config.HistoricalDataStoreConfig.bars_path`, `qts.data.historical.config.HistoricalDataStoreConfig.chain_path`

#### `qts.data.historical.config.HistoricalBarFileConfig`
- 位置：`backend/src/qts/data/historical/config.py:94`
- 类型：`class`
- 签名：`class HistoricalBarFileConfig`
- 作用：One physical bar file for a dataset.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.config.HistoricalDataConfig._select_bar_file`, `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_bar_files`

#### `qts.data.historical.config.HistoricalBarFileConfig.__post_init__`
- 位置：`backend/src/qts/data/historical/config.py:104`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError` x6, `self.exchange_timezone.strip`, `self.file.strip`, `self.normalization.strip`, `self.schema.strip`, `self.timeframe.strip`, `self.timezone_policy.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.historical.config.HistoricalDatasetConfig`
- 位置：`backend/src/qts/data/historical/config.py:121`
- 类型：`class`
- 签名：`class HistoricalDatasetConfig`
- 作用：One product/data entry inside a historical data catalog.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_datasets`

#### `qts.data.historical.config.HistoricalDatasetConfig.__post_init__`
- 位置：`backend/src/qts/data/historical/config.py:134`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError` x8, `self.asset_class.strip`, `self.bars_file.strip`, `self.chain_file.strip`, `self.exchange.strip`, `self.exchange_timezone.strip`, `self.root.strip`, `self.schema.strip`, `self.source_timeframe.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.historical.config.HistoricalDatasetConfig.requires_chain`
- 位置：`backend/src/qts/data/historical/config.py:154`
- 类型：`property`
- 签名：`def requires_chain(self) -> bool`
- 作用：Perform requires_chain.
- 直接原始调用：`self.asset_class.strip`, `self.asset_class.strip.lower`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.historical.config.HistoricalDatasetConfig.normalize_root`
- 位置：`backend/src/qts/data/historical/config.py:159`
- 类型：`staticmethod`
- 签名：`def normalize_root(root: str) -> str`
- 作用：Perform normalize_root.
- 直接原始调用：`ValueError`, `root.strip`, `root.strip.upper`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.config.HistoricalDataConfig.resolve_chain_path`, `qts.data.historical.config.HistoricalDataConfig.resolve_dataset`, `qts.data.historical.config.HistoricalDataStoreConfig._render_template`, `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_datasets`

#### `qts.data.historical.config.HistoricalDataCatalogConfig`
- 位置：`backend/src/qts/data/historical/config.py:168`
- 类型：`class`
- 签名：`class HistoricalDataCatalogConfig`
- 作用：Logical catalog of historical datasets backed by one store.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_catalogs`

#### `qts.data.historical.config.HistoricalDataCatalogConfig.__post_init__`
- 位置：`backend/src/qts/data/historical/config.py:175`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError` x3, `self.name.strip`, `self.store.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.historical.config.HistoricalDatasetLocation`
- 位置：`backend/src/qts/data/historical/config.py:186`
- 类型：`class`
- 签名：`class HistoricalDatasetLocation`
- 作用：Resolved physical file paths for one catalog dataset.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.config.HistoricalDataConfig.resolve_dataset`

#### `qts.data.historical.config.HistoricalDataConfig`
- 位置：`backend/src/qts/data/historical/config.py:202`
- 类型：`class`
- 签名：`class HistoricalDataConfig`
- 作用：Project-level historical data stores and catalogs.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.config_loader.HistoricalDataConfigLoader.from_payload`

#### `qts.data.historical.config.HistoricalDataConfig.__post_init__`
- 位置：`backend/src/qts/data/historical/config.py:209`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError` x3, `self.catalogs.values`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.historical.config.HistoricalDataConfig.from_yaml`
- 位置：`backend/src/qts/data/historical/config.py:220`
- 类型：`classmethod`
- 签名：`def from_yaml(cls, path: Path) -> HistoricalDataConfig`
- 作用：Perform from_yaml.
- 直接原始调用：`HistoricalDataConfigLoader.from_path`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.catalog.HistoricalCatalog.load`

#### `qts.data.historical.config.HistoricalDataConfig.from_payload`
- 位置：`backend/src/qts/data/historical/config.py:227`
- 类型：`classmethod`
- 签名：`def from_payload(cls, payload: object) -> HistoricalDataConfig`
- 作用：Perform from_payload.
- 直接原始调用：`HistoricalDataConfigLoader.from_payload`, `ValueError`, `isinstance`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.historical.config.HistoricalDataConfig.catalog`
- 位置：`backend/src/qts/data/historical/config.py:235`
- 类型：`method`
- 签名：`def catalog(self, name: str) -> HistoricalDataCatalogConfig`
- 作用：Perform catalog.
- 直接原始调用：`KeyError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.config.HistoricalDataConfig.resolve_chain_path`, `qts.data.historical.config.HistoricalDataConfig.resolve_dataset`

#### `qts.data.historical.config.HistoricalDataConfig.store`
- 位置：`backend/src/qts/data/historical/config.py:242`
- 类型：`method`
- 签名：`def store(self, name: str) -> HistoricalDataStoreConfig`
- 作用：Perform store.
- 直接原始调用：`KeyError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.config.HistoricalDataConfig.resolve_chain_path`, `qts.data.historical.config.HistoricalDataConfig.resolve_dataset`

#### `qts.data.historical.config.HistoricalDataConfig.resolve_dataset`
- 位置：`backend/src/qts/data/historical/config.py:249`
- 类型：`method`
- 签名：`def resolve_dataset(self, catalog_name: str, root: str, *, requested_timeframe: str | None=None) -> HistoricalDatasetLocation`
- 作用：Perform resolve_dataset.
- 直接原始调用：`HistoricalDatasetConfig.normalize_root`, `HistoricalDatasetLocation`, `KeyError`, `self._csv_schema`, `self._select_bar_file`, `self.catalog`, `self.store`, `store.bars_path`, `store.chain_path`
- 已解析到仓库内部的调用：`qts.data.historical.config.HistoricalDatasetConfig.normalize_root`, `qts.data.historical.config.HistoricalDataConfig.catalog`, `qts.data.historical.config.HistoricalDataConfig.store`, `qts.data.historical.config.HistoricalDataConfig._select_bar_file`, `qts.data.historical.config.HistoricalDatasetLocation`, `qts.data.historical.config.HistoricalDataConfig._csv_schema`
- 被以下仓库内部符号调用：无

#### `qts.data.historical.config.HistoricalDataConfig.resolve_chain_path`
- 位置：`backend/src/qts/data/historical/config.py:296`
- 类型：`method`
- 签名：`def resolve_chain_path(self, catalog_name: str, root: str) -> Path | None`
- 作用：Resolve chain metadata path without selecting a concrete bar file.
- 直接原始调用：`HistoricalDatasetConfig.normalize_root`, `KeyError`, `self.catalog`, `self.store`, `store.chain_path`
- 已解析到仓库内部的调用：`qts.data.historical.config.HistoricalDatasetConfig.normalize_root`, `qts.data.historical.config.HistoricalDataConfig.catalog`, `qts.data.historical.config.HistoricalDataConfig.store`
- 被以下仓库内部符号调用：无

#### `qts.data.historical.config.HistoricalDataConfig._csv_schema`
- 位置：`backend/src/qts/data/historical/config.py:312`
- 类型：`method`
- 签名：`def _csv_schema(self, name: str | None) -> HistoricalCsvSchema`
- 作用：Perform _csv_schema.
- 直接原始调用：`KeyError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.config.HistoricalDataConfig.resolve_dataset`

#### `qts.data.historical.config.HistoricalDataConfig._select_bar_file`
- 位置：`backend/src/qts/data/historical/config.py:322`
- 类型：`staticmethod`
- 签名：`def _select_bar_file(*, catalog_name: str, root: str, dataset: HistoricalDatasetConfig, store: HistoricalDataStoreConfig, requested_timeframe: str | None) -> HistoricalBarFileConfig`
- 作用：Perform _select_bar_file.
- 直接原始调用：`FeedCapabilities`, `FeedCapabilities.source_timeframe_for`, `HistoricalBarFileConfig`, `RuntimeError`, `ValueError`, `frozenset`, `len`
- 已解析到仓库内部的调用：`qts.data.historical.config.HistoricalBarFileConfig`, `qts.data.live_feed.FeedCapabilities.source_timeframe_for`, `qts.data.live_feed.FeedCapabilities`
- 被以下仓库内部符号调用：`qts.data.historical.config.HistoricalDataConfig.resolve_dataset`

### `qts.data.historical.config_loader`

模块：`qts.data.historical.config_loader`

#### `qts.data.historical.config_loader.HistoricalDataConfigLoader`
- 位置：`backend/src/qts/data/historical/config_loader.py:31`
- 类型：`class`
- 签名：`class HistoricalDataConfigLoader`
- 作用：Load historical data configuration from files or payload dictionaries.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.historical.config_loader.HistoricalDataConfigLoader.from_path`
- 位置：`backend/src/qts/data/historical/config_loader.py:35`
- 类型：`classmethod`
- 签名：`def from_path(cls, path: Path) -> HistoricalDataConfig`
- 作用：Perform from_path.
- 直接原始调用：`ValueError`, `cls.from_payload`, `isinstance`, `path.read_text`, `yaml.safe_load`
- 已解析到仓库内部的调用：`qts.data.historical.config_loader.HistoricalDataConfigLoader.from_payload`
- 被以下仓库内部符号调用：无

#### `qts.data.historical.config_loader.HistoricalDataConfigLoader.from_payload`
- 位置：`backend/src/qts/data/historical/config_loader.py:43`
- 类型：`classmethod`
- 签名：`def from_payload(cls, payload: object) -> HistoricalDataConfig`
- 作用：Perform from_payload.
- 直接原始调用：`raw_config.get` x3, `ValueError` x2, `isinstance` x2, `HistoricalDataConfig`, `cls._parse_catalogs`, `cls._parse_schemas`, `cls._parse_stores`, `payload.get`
- 已解析到仓库内部的调用：`qts.data.historical.config.HistoricalDataConfig`, `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_stores`, `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_catalogs`, `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_schemas`
- 被以下仓库内部符号调用：`qts.data.historical.config_loader.HistoricalDataConfigLoader.from_path`

#### `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_stores`
- 位置：`backend/src/qts/data/historical/config_loader.py:57`
- 类型：`classmethod`
- 签名：`def _parse_stores(cls, payload: object) -> dict[str, HistoricalDataStoreConfig]`
- 作用：Perform _parse_stores.
- 直接原始调用：`str` x10, `raw_store.get` x9, `Path` x3, `ValueError` x3, `isinstance` x3, `HistoricalDataStoreConfig`, `cls._parse_store_defaults`, `payload.items`
- 已解析到仓库内部的调用：`qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_store_defaults`, `qts.data.historical.config.HistoricalDataStoreConfig`
- 被以下仓库内部符号调用：`qts.data.historical.config_loader.HistoricalDataConfigLoader.from_payload`

#### `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_store_defaults`
- 位置：`backend/src/qts/data/historical/config_loader.py:95`
- 类型：`staticmethod`
- 签名：`def _parse_store_defaults(raw_store: Mapping[str, object]) -> HistoricalDataStoreDefaults`
- 作用：Perform _parse_store_defaults.
- 直接原始调用：`str` x5, `raw_defaults.get` x4, `raw_store.get` x4, `HistoricalDataStoreDefaults`, `ValueError`, `isinstance`
- 已解析到仓库内部的调用：`qts.data.historical.config.HistoricalDataStoreDefaults`
- 被以下仓库内部符号调用：`qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_stores`

#### `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_catalogs`
- 位置：`backend/src/qts/data/historical/config_loader.py:127`
- 类型：`classmethod`
- 签名：`def _parse_catalogs(cls, payload: object) -> dict[str, HistoricalDataCatalogConfig]`
- 作用：Perform _parse_catalogs.
- 直接原始调用：`ValueError` x4, `isinstance` x4, `HistoricalDataCatalogConfig`, `cls._parse_datasets`, `payload.items`, `raw_catalog.get`, `str`
- 已解析到仓库内部的调用：`qts.data.historical.config.HistoricalDataCatalogConfig`, `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_datasets`
- 被以下仓库内部符号调用：`qts.data.historical.config_loader.HistoricalDataConfigLoader.from_payload`

#### `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_datasets`
- 位置：`backend/src/qts/data/historical/config_loader.py:148`
- 类型：`classmethod`
- 签名：`def _parse_datasets(cls, payload: Mapping[object, object]) -> dict[str, HistoricalDatasetConfig]`
- 作用：Perform _parse_datasets.
- 直接原始调用：`raw_dataset.get` x7, `str` x7, `ValueError` x3, `isinstance` x2, `', '.join`, `HistoricalDatasetConfig`, `HistoricalDatasetConfig.normalize_root`, `_DATASET_STORAGE_PATH_KEYS.intersection`, `cls._parse_bar_files`, `payload.items`, `sorted`
- 已解析到仓库内部的调用：`qts.data.historical.config.HistoricalDatasetConfig.normalize_root`, `qts.data.historical.config.HistoricalDatasetConfig`, `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_bar_files`
- 被以下仓库内部符号调用：`qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_catalogs`

#### `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_bar_files`
- 位置：`backend/src/qts/data/historical/config_loader.py:199`
- 类型：`staticmethod`
- 签名：`def _parse_bar_files(payload: object) -> tuple[HistoricalBarFileConfig, ...]`
- 作用：Perform _parse_bar_files.
- 直接原始调用：`raw_bar.get` x6, `str` x6, `ValueError` x2, `isinstance` x2, `HistoricalBarFileConfig`, `bars.append`, `tuple`
- 已解析到仓库内部的调用：`qts.data.historical.config.HistoricalBarFileConfig`
- 被以下仓库内部符号调用：`qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_datasets`

#### `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_schemas`
- 位置：`backend/src/qts/data/historical/config_loader.py:236`
- 类型：`staticmethod`
- 签名：`def _parse_schemas(payload: object) -> dict[str, HistoricalCsvSchema]`
- 作用：Perform _parse_schemas.
- 直接原始调用：`str` x8, `ValueError` x3, `isinstance` x3, `HistoricalCsvSchema`, `payload.items`, `raw_schema.get`
- 已解析到仓库内部的调用：`qts.data.historical.csv_format.HistoricalCsvSchema`
- 被以下仓库内部符号调用：`qts.data.historical.config_loader.HistoricalDataConfigLoader.from_payload`

### `qts.data.historical.csv_dataset`

模块：`qts.data.historical.csv_dataset`

#### `qts.data.historical.csv_dataset.CsvDatasetDescription`
- 位置：`backend/src/qts/data/historical/csv_dataset.py:42`
- 类型：`class`
- 签名：`class CsvDatasetDescription`
- 作用：Cheap metadata description for a historical CSV dataset.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.describe_csv_dataset`

#### `qts.data.historical.csv_dataset.HistoricalBarStream`
- 位置：`backend/src/qts/data/historical/csv_dataset.py:55`
- 类型：`class`
- 签名：`class HistoricalBarStream`
- 作用：Lazy iterable over historical bars with side-channel reader stats.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.iter_historical_bars`

#### `qts.data.historical.csv_dataset.HistoricalBarStream.__init__`
- 位置：`backend/src/qts/data/historical/csv_dataset.py:58`
- 类型：`method`
- 签名：`def __init__(self, *, csv_path: Path, symbol_resolver: SourceSymbolResolver, timeframe: str, start: datetime | None=None, end: datetime | None=None, contract_selector: FutureContractSelector | None=None, continuous_instrument_id: InstrumentId | None=None, session_window: RegularSessionWindow | None=None, schema: HistoricalCsvSchema | None=None) -> None`
- 作用：未写 docstring；静态推断为所属类上的 `  init  ` 行为。
- 直接原始调用：`HistoricalCsvRowMapper`, `HistoricalCsvStats`
- 已解析到仓库内部的调用：`qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper`, `qts.data.historical.validation.HistoricalCsvStats`
- 被以下仓库内部符号调用：无

#### `qts.data.historical.csv_dataset.HistoricalBarStream.__iter__`
- 位置：`backend/src/qts/data/historical/csv_dataset.py:85`
- 类型：`method`
- 签名：`def __iter__(self) -> Iterator[Bar]`
- 作用：未写 docstring；静态推断为所属类上的 `  iter  ` 行为。
- 直接原始调用：`csv.DictReader`, `self._csv_path.open`, `self._iter_all_supported_rows`, `self._iter_selected_contract_rows`, `self._iter_session_selected_contract_rows`, `tuple`, `validate_historical_csv_columns`
- 已解析到仓库内部的调用：`qts.data.historical.csv_format.validate_historical_csv_columns`, `qts.data.historical.csv_dataset.HistoricalBarStream._iter_all_supported_rows`, `qts.data.historical.csv_dataset.HistoricalBarStream._iter_session_selected_contract_rows`, `qts.data.historical.csv_dataset.HistoricalBarStream._iter_selected_contract_rows`
- 被以下仓库内部符号调用：无

#### `qts.data.historical.csv_dataset.HistoricalBarStream._iter_all_supported_rows`
- 位置：`backend/src/qts/data/historical/csv_dataset.py:99`
- 类型：`method`
- 签名：`def _iter_all_supported_rows(self, reader: csv.DictReader[str]) -> Iterator[Bar]`
- 作用：未写 docstring；静态推断为所属类上的 ` iter all supported rows` 行为。
- 直接原始调用：`self._count_excluded_symbol`, `self._field`, `self._row_mapper.to_bar`, `self._symbol_resolver.is_supported_symbol`, `self._timestamp`
- 已解析到仓库内部的调用：`qts.data.historical.csv_dataset.HistoricalBarStream._field`, `qts.data.historical.csv_dataset.HistoricalBarStream._timestamp`, `qts.data.historical.csv_dataset.HistoricalBarStream._count_excluded_symbol`
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.HistoricalBarStream.__iter__`

#### `qts.data.historical.csv_dataset.HistoricalBarStream._iter_selected_contract_rows`
- 位置：`backend/src/qts/data/historical/csv_dataset.py:122`
- 类型：`method`
- 签名：`def _iter_selected_contract_rows(self, reader: csv.DictReader[str]) -> Iterator[Bar]`
- 作用：未写 docstring；静态推断为所属类上的 ` iter selected contract rows` 行为。
- 直接原始调用：`FutureContractCandidate`, `FutureRollSelection`, `RuntimeError`, `candidates.append`, `contract_selector.select`, `len`, `replace`, `self._count_excluded_symbol`, `self._field`, `self._resolver_root`, `self._row_mapper.to_bar`, `self._symbol_resolver.is_supported_symbol`, `self._timestamp_groups`, `self.roll_selections.append`, `tuple`
- 已解析到仓库内部的调用：`qts.data.historical.csv_dataset.HistoricalBarStream._timestamp_groups`, `qts.data.historical.csv_dataset.HistoricalBarStream._field`, `qts.registry.future_roll.FutureRollSelection`, `qts.data.historical.csv_dataset.HistoricalBarStream._count_excluded_symbol`, `qts.registry.future_roll.FutureContractCandidate`, `qts.data.historical.csv_dataset.HistoricalBarStream._resolver_root`
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.HistoricalBarStream.__iter__`

#### `qts.data.historical.csv_dataset.HistoricalBarStream._iter_session_selected_contract_rows`
- 位置：`backend/src/qts/data/historical/csv_dataset.py:183`
- 类型：`method`
- 签名：`def _iter_session_selected_contract_rows(self, reader: csv.DictReader[str]) -> Iterator[Bar]`
- 作用：未写 docstring；静态推断为所属类上的 ` iter session selected contract rows` 行为。
- 直接原始调用：`self._emit_selected_session_rows` x3, `RuntimeError` x2, `current_groups.append`, `self._timestamp_groups`, `session_window.session_id_for_timestamp`
- 已解析到仓库内部的调用：`qts.data.historical.csv_dataset.HistoricalBarStream._timestamp_groups`, `qts.data.historical.csv_dataset.HistoricalBarStream._emit_selected_session_rows`
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.HistoricalBarStream.__iter__`

#### `qts.data.historical.csv_dataset.HistoricalBarStream._emit_selected_session_rows`
- 位置：`backend/src/qts/data/historical/csv_dataset.py:229`
- 类型：`method`
- 签名：`def _emit_selected_session_rows(self, session_id: str, groups: list[tuple[datetime, list[dict[str, str]]]], *, contract_selector: FutureContractSelector) -> Iterator[Bar]`
- 作用：未写 docstring；静态推断为所属类上的 ` emit selected session rows` 行为。
- 直接原始调用：`Decimal`, `FutureContractCandidate`, `FutureRollSelection`, `closes_by_timestamp.append`, `contract_selector.select`, `defaultdict`, `historical_timeframe_delta`, `len`, `replace`, `rows_by_instrument.get`, `rows_by_timestamp.append`, `self._count_excluded_symbol`, `self._field`, `self._resolver_root`, `self._row_mapper.extract_ohlcv`, `self._row_mapper.to_bar`, `self._symbol_resolver.instrument_id_for_symbol`, `self._symbol_resolver.is_supported_symbol`, `self.roll_selections.append`, `total_volume_by_instrument.items`, `tuple`, `zip`
- 已解析到仓库内部的调用：`qts.data.historical.csv_format.historical_timeframe_delta`, `qts.data.historical.csv_dataset.HistoricalBarStream._field`, `qts.data.historical.csv_dataset.HistoricalBarStream._count_excluded_symbol`, `qts.registry.future_roll.FutureContractCandidate`, `qts.data.historical.csv_dataset.HistoricalBarStream._resolver_root`, `qts.registry.future_roll.FutureRollSelection`
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.HistoricalBarStream._iter_session_selected_contract_rows`

#### `qts.data.historical.csv_dataset.HistoricalBarStream._timestamp_groups`
- 位置：`backend/src/qts/data/historical/csv_dataset.py:316`
- 类型：`method`
- 签名：`def _timestamp_groups(self, reader: csv.DictReader[str]) -> Iterator[tuple[datetime, list[dict[str, str]]]]`
- 作用：未写 docstring；静态推断为所属类上的 ` timestamp groups` 行为。
- 直接原始调用：`parse_historical_ts_event` x2, `current_rows.append`, `self._field`
- 已解析到仓库内部的调用：`qts.data.historical.csv_dataset.HistoricalBarStream._field`, `qts.data.historical.csv_format.parse_historical_ts_event`
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.HistoricalBarStream._iter_selected_contract_rows`, `qts.data.historical.csv_dataset.HistoricalBarStream._iter_session_selected_contract_rows`

#### `qts.data.historical.csv_dataset.HistoricalBarStream._count_excluded_symbol`
- 位置：`backend/src/qts/data/historical/csv_dataset.py:333`
- 类型：`method`
- 签名：`def _count_excluded_symbol(self, symbol: str) -> None`
- 作用：未写 docstring；静态推断为所属类上的 ` count excluded symbol` 行为。
- 直接原始调用：`_is_spread_symbol`
- 已解析到仓库内部的调用：`qts.data.historical.csv_dataset._is_spread_symbol`
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.HistoricalBarStream._emit_selected_session_rows`, `qts.data.historical.csv_dataset.HistoricalBarStream._iter_all_supported_rows`, `qts.data.historical.csv_dataset.HistoricalBarStream._iter_selected_contract_rows`

#### `qts.data.historical.csv_dataset.HistoricalBarStream._resolver_root`
- 位置：`backend/src/qts/data/historical/csv_dataset.py:338`
- 类型：`method`
- 签名：`def _resolver_root(self) -> str`
- 作用：未写 docstring；静态推断为所属类上的 ` resolver root` 行为。
- 直接原始调用：`_resolver_root`
- 已解析到仓库内部的调用：`qts.data.historical.csv_dataset._resolver_root`
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.HistoricalBarStream._emit_selected_session_rows`, `qts.data.historical.csv_dataset.HistoricalBarStream._iter_selected_contract_rows`

#### `qts.data.historical.csv_dataset.HistoricalBarStream._field`
- 位置：`backend/src/qts/data/historical/csv_dataset.py:341`
- 类型：`method`
- 签名：`def _field(self, row: dict[str, str], semantic_name: str) -> str`
- 作用：未写 docstring；静态推断为所属类上的 ` field` 行为。
- 直接原始调用：`self._schema.resolve_column`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.HistoricalBarStream._emit_selected_session_rows`, `qts.data.historical.csv_dataset.HistoricalBarStream._iter_all_supported_rows`, `qts.data.historical.csv_dataset.HistoricalBarStream._iter_selected_contract_rows`, `qts.data.historical.csv_dataset.HistoricalBarStream._timestamp`, `qts.data.historical.csv_dataset.HistoricalBarStream._timestamp_groups`

#### `qts.data.historical.csv_dataset.HistoricalBarStream._timestamp`
- 位置：`backend/src/qts/data/historical/csv_dataset.py:344`
- 类型：`method`
- 签名：`def _timestamp(self, row: dict[str, str]) -> datetime`
- 作用：未写 docstring；静态推断为所属类上的 ` timestamp` 行为。
- 直接原始调用：`parse_historical_ts_event`, `self._field`
- 已解析到仓库内部的调用：`qts.data.historical.csv_format.parse_historical_ts_event`, `qts.data.historical.csv_dataset.HistoricalBarStream._field`
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.HistoricalBarStream._iter_all_supported_rows`

#### `qts.data.historical.csv_dataset.describe_csv_dataset`
- 位置：`backend/src/qts/data/historical/csv_dataset.py:348`
- 类型：`module_function`
- 签名：`def describe_csv_dataset(path: Path, *, root: str, timeframe: str='1m', count_rows: bool=False, schema: HistoricalCsvSchema | None=None) -> CsvDatasetDescription`
- 作用：Read historical CSV identity metadata without materializing row data.
- 直接原始调用：`CsvDatasetDescription`, `csv.reader`, `next`, `path.open`, `sum`, `tuple`, `validate_historical_csv_columns`
- 已解析到仓库内部的调用：`qts.data.historical.csv_format.validate_historical_csv_columns`, `qts.data.historical.csv_dataset.CsvDatasetDescription`
- 被以下仓库内部符号调用：`qts.data.historical.catalog.HistoricalCatalog.from_historical_data_config`, `qts.data.historical.catalog.HistoricalCatalog.from_legacy_root`

#### `qts.data.historical.csv_dataset.iter_historical_bars`
- 位置：`backend/src/qts/data/historical/csv_dataset.py:375`
- 类型：`module_function`
- 签名：`def iter_historical_bars(csv_path: Path, symbol_resolver: SourceSymbolResolver | HistoricalChain, *, timeframe: str='1m', start: datetime | None=None, end: datetime | None=None, contract_selector: FutureContractSelector | None=None, continuous_instrument_id: InstrumentId | None=None, session_window: RegularSessionWindow | None=None, schema: HistoricalCsvSchema | None=None) -> HistoricalBarStream`
- 作用：Return a lazy stream of outright historical bars.
- 直接原始调用：`HistoricalBarStream`, `_as_symbol_resolver`
- 已解析到仓库内部的调用：`qts.data.historical.csv_dataset.HistoricalBarStream`, `qts.data.historical.csv_dataset._as_symbol_resolver`
- 被以下仓库内部符号调用：`qts.backtest.inputs.BacktestInputBuilder._stream_configured_bars`, `qts.data.historical.service.HistoricalMarketDataService.events`

#### `qts.data.historical.csv_dataset.validate_historical_sample`
- 位置：`backend/src/qts/data/historical/csv_dataset.py:402`
- 类型：`module_function`
- 签名：`def validate_historical_sample(csv_path: Path, symbol_resolver: SourceSymbolResolver | HistoricalChain, *, sample_rows: int | None, timeframe: str='1m', schema: HistoricalCsvSchema | None=None) -> HistoricalValidationSample`
- 作用：Validate a bounded sample or full CSV when `sample_rows` is None.
- 直接原始调用：`HistoricalDatasetValidator`, `HistoricalDatasetValidator.validate_sample`, `_as_symbol_resolver`
- 已解析到仓库内部的调用：`qts.data.historical.validation.HistoricalDatasetValidator.validate_sample`, `qts.data.historical.validation.HistoricalDatasetValidator`, `qts.data.historical.csv_dataset._as_symbol_resolver`
- 被以下仓库内部符号调用：`scripts.validate_historical.main`

#### `qts.data.historical.csv_dataset._resolver_root`
- 位置：`backend/src/qts/data/historical/csv_dataset.py:420`
- 类型：`module_function`
- 签名：`def _resolver_root(symbol_resolver: SourceSymbolResolver) -> str`
- 作用：未写 docstring；静态推断为 ` resolver root` 函数，具体语义以实现为准。
- 直接原始调用：`ValueError` x2, `isinstance`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.HistoricalBarStream._resolver_root`

#### `qts.data.historical.csv_dataset.RootSymbolResolver`
- 位置：`backend/src/qts/data/historical/csv_dataset.py:430`
- 类型：`class`
- 签名：`class RootSymbolResolver(Protocol)`
- 作用：Protocol for symbol resolvers that provide a root identifier.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.historical.csv_dataset.RootSymbolResolver.root`
- 位置：`backend/src/qts/data/historical/csv_dataset.py:434`
- 类型：`property`
- 签名：`def root(self) -> str`
- 作用：Return the root identifier.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.historical.csv_dataset._as_symbol_resolver`
- 位置：`backend/src/qts/data/historical/csv_dataset.py:439`
- 类型：`module_function`
- 签名：`def _as_symbol_resolver(value: SourceSymbolResolver | HistoricalChain) -> SourceSymbolResolver`
- 作用：未写 docstring；静态推断为 ` as symbol resolver` 函数，具体语义以实现为准。
- 直接原始调用：`HistoricalFutureChainSymbolResolver`, `isinstance`
- 已解析到仓库内部的调用：`qts.data.historical.symbols.HistoricalFutureChainSymbolResolver`
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.iter_historical_bars`, `qts.data.historical.csv_dataset.validate_historical_sample`

#### `qts.data.historical.csv_dataset._is_spread_symbol`
- 位置：`backend/src/qts/data/historical/csv_dataset.py:447`
- 类型：`module_function`
- 签名：`def _is_spread_symbol(symbol: str) -> bool`
- 作用：未写 docstring；静态推断为 ` is spread symbol` 函数，具体语义以实现为准。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.HistoricalBarStream._count_excluded_symbol`

### `qts.data.historical.csv_format`

模块：`qts.data.historical.csv_format`

#### `qts.data.historical.csv_format.HistoricalCsvSchema`
- 位置：`backend/src/qts/data/historical/csv_format.py:24`
- 类型：`class`
- 签名：`class HistoricalCsvSchema`
- 作用：Mapping from framework OHLCV semantics to concrete CSV columns.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_schemas`

#### `qts.data.historical.csv_format.HistoricalCsvSchema.__post_init__`
- 位置：`backend/src/qts/data/historical/csv_format.py:36`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError` x2, `any`, `item.strip`, `self.instrument_id.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.historical.csv_format.HistoricalCsvSchema.required_columns`
- 位置：`backend/src/qts/data/historical/csv_format.py:53`
- 类型：`property`
- 签名：`def required_columns(self) -> tuple[str, ...]`
- 作用：Perform required_columns.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.historical.csv_format.HistoricalCsvSchema.validate_columns`
- 位置：`backend/src/qts/data/historical/csv_format.py:65`
- 类型：`method`
- 签名：`def validate_columns(self, columns: Iterable[str]) -> tuple[str, ...]`
- 作用：Perform validate_columns.
- 直接原始调用：`tuple` x2, `','.join`, `ValueError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.csv_format.HistoricalCsvSchema.column_indices`

#### `qts.data.historical.csv_format.HistoricalCsvSchema.resolve_column`
- 位置：`backend/src/qts/data/historical/csv_format.py:73`
- 类型：`method`
- 签名：`def resolve_column(self, semantic_name: str) -> str`
- 作用：Resolve an OHLCV semantic field name to the configured CSV column.
- 直接原始调用：`ValueError` x2
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.historical.csv_format.HistoricalCsvSchema.column_indices`
- 位置：`backend/src/qts/data/historical/csv_format.py:96`
- 类型：`method`
- 签名：`def column_indices(self, columns: Iterable[str]) -> dict[str, int]`
- 作用：Perform column_indices.
- 直接原始调用：`enumerate`, `self.validate_columns`
- 已解析到仓库内部的调用：`qts.data.historical.csv_format.HistoricalCsvSchema.validate_columns`
- 被以下仓库内部符号调用：无

#### `qts.data.historical.csv_format.validate_historical_csv_columns`
- 位置：`backend/src/qts/data/historical/csv_format.py:114`
- 类型：`module_function`
- 签名：`def validate_historical_csv_columns(columns: tuple[str, ...], *, schema: HistoricalCsvSchema | None=None) -> None`
- 作用：Validate historical CSV columns against the configured schema.
- 直接原始调用：`','.join` x2, `ValueError`, `schema.validate_columns`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.HistoricalBarStream.__iter__`, `qts.data.historical.csv_dataset.describe_csv_dataset`, `qts.data.historical.validation.HistoricalDatasetValidator.validate_sample`

#### `qts.data.historical.csv_format.parse_historical_ts_event`
- 位置：`backend/src/qts/data/historical/csv_format.py:131`
- 类型：`module_function`
- 签名：`def parse_historical_ts_event(value: str) -> datetime`
- 作用：Parse a historical CSV UTC timestamp, accepting nanosecond text input.
- 直接原始调用：`ValueError`, `datetime.fromisoformat`, `parsed.astimezone`, `rest[:6].ljust`, `text.split`, `value.endswith`, `value.removesuffix`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.HistoricalBarStream._timestamp`, `qts.data.historical.csv_dataset.HistoricalBarStream._timestamp_groups`, `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper.to_bar`

#### `qts.data.historical.csv_format.historical_timeframe_delta`
- 位置：`backend/src/qts/data/historical/csv_format.py:146`
- 类型：`module_function`
- 签名：`def historical_timeframe_delta(timeframe: str) -> timedelta`
- 作用：Return the duration represented by a supported historical timeframe.
- 直接原始调用：`timedelta` x4, `int` x3, `timeframe.endswith` x3, `ValueError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.HistoricalBarStream._emit_selected_session_rows`, `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper.to_bar`, `qts.data.historical.validation.HistoricalDatasetValidator.validate_sample`

### `qts.data.historical.csv_row_mapper`

模块：`qts.data.historical.csv_row_mapper`

#### `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper`
- 位置：`backend/src/qts/data/historical/csv_row_mapper.py:21`
- 类型：`class`
- 签名：`class HistoricalCsvRowMapper`
- 作用：Map one validated CSV row to an OHLCV bar.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.HistoricalBarStream.__init__`, `qts.data.historical.validation.HistoricalDatasetValidator.validate_sample`

#### `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper.to_bar`
- 位置：`backend/src/qts/data/historical/csv_row_mapper.py:27`
- 类型：`method`
- 签名：`def to_bar(self, row: Mapping[str, str], *, symbol_resolver: SourceSymbolResolver) -> Bar`
- 作用：Map a mapped row dict into a typed bar.
- 直接原始调用：`self._field` x2, `Bar`, `historical_timeframe_delta`, `parse_historical_ts_event`, `self.extract_ohlcv`, `start_time.astimezone`, `start_time.astimezone.date`, `start_time.astimezone.date.isoformat`, `symbol_resolver.instrument_id_for_symbol`
- 已解析到仓库内部的调用：`qts.data.historical.csv_format.parse_historical_ts_event`, `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper._field`, `qts.data.historical.csv_format.historical_timeframe_delta`, `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper.extract_ohlcv`
- 被以下仓库内部符号调用：无

#### `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper.extract_ohlcv`
- 位置：`backend/src/qts/data/historical/csv_row_mapper.py:48`
- 类型：`method`
- 签名：`def extract_ohlcv(self, row: Mapping[str, str]) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal]`
- 作用：Extract and validate OHLCV fields from a mapped row.
- 直接原始调用：`self._field` x5, `self._parse_ohlcv_values`
- 已解析到仓库内部的调用：`qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper._parse_ohlcv_values`, `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper._field`
- 被以下仓库内部符号调用：`qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper.to_bar`

#### `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper._field`
- 位置：`backend/src/qts/data/historical/csv_row_mapper.py:61`
- 类型：`method`
- 签名：`def _field(self, row: Mapping[str, str], semantic_name: str) -> str`
- 作用：Perform _field.
- 直接原始调用：`self.schema.resolve_column`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper.extract_ohlcv`, `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper.to_bar`

#### `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper._parse_ohlcv_values`
- 位置：`backend/src/qts/data/historical/csv_row_mapper.py:66`
- 类型：`staticmethod`
- 签名：`def _parse_ohlcv_values(*, open_value: str, high_value: str, low_value: str, close_value: str, volume_value: str) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal]`
- 作用：Perform _parse_ohlcv_values.
- 直接原始调用：`Decimal` x6, `ValueError` x4, `max`, `min`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper.extract_ohlcv`

### `qts.data.historical.service`

模块：`qts.data.historical.service`

#### `qts.data.historical.service.HistoricalMarketDataService`
- 位置：`backend/src/qts/data/historical/service.py:16`
- 类型：`class`
- 签名：`class HistoricalMarketDataService`
- 作用：Deterministic historical market data source with feed-like contracts.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.historical.service.HistoricalMarketDataService.__post_init__`
- 位置：`backend/src/qts/data/historical/service.py:27`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError` x2, `self.source_id.strip`, `self.source_timeframe.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.historical.service.HistoricalMarketDataService.capabilities`
- 位置：`backend/src/qts/data/historical/service.py:35`
- 类型：`property`
- 签名：`def capabilities(self) -> FeedCapabilities`
- 作用：Perform capabilities.
- 直接原始调用：`FeedCapabilities`, `frozenset`
- 已解析到仓库内部的调用：`qts.data.live_feed.FeedCapabilities`
- 被以下仓库内部符号调用：无

#### `qts.data.historical.service.HistoricalMarketDataService.subscribe`
- 位置：`backend/src/qts/data/historical/service.py:45`
- 类型：`method`
- 签名：`def subscribe(self, subscription: FeedSubscription) -> LiveFeedSubscribed`
- 作用：Perform subscribe.
- 直接原始调用：`LiveFeedSubscribed`, `self.capabilities.source_timeframe_for`
- 已解析到仓库内部的调用：`qts.data.live_feed.LiveFeedSubscribed`
- 被以下仓库内部符号调用：无

#### `qts.data.historical.service.HistoricalMarketDataService.events`
- 位置：`backend/src/qts/data/historical/service.py:51`
- 类型：`method`
- 签名：`def events(self, subscription_id: str) -> Iterator[LiveFeedEvent]`
- 作用：Perform events.
- 直接原始调用：`KeyError`, `LiveFeedEvent`, `ValueError`, `iter_historical_bars`, `subscription_id.strip`
- 已解析到仓库内部的调用：`qts.data.historical.csv_dataset.iter_historical_bars`, `qts.data.live_feed.LiveFeedEvent`
- 被以下仓库内部符号调用：无

### `qts.data.historical.symbols`

模块：`qts.data.historical.symbols`

#### `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver`
- 位置：`backend/src/qts/data/historical/symbols.py:12`
- 类型：`class`
- 签名：`class HistoricalFutureChainSymbolResolver`
- 作用：Resolve historical futures outright symbols through chain metadata.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.catalog.HistoricalCatalog.from_historical_data_config`, `qts.data.historical.catalog.HistoricalCatalog.from_legacy_root`, `qts.data.historical.csv_dataset._as_symbol_resolver`

#### `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver.root`
- 位置：`backend/src/qts/data/historical/symbols.py:18`
- 类型：`property`
- 签名：`def root(self) -> str`
- 作用：Perform root.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver.is_supported_symbol`
- 位置：`backend/src/qts/data/historical/symbols.py:22`
- 类型：`method`
- 签名：`def is_supported_symbol(self, symbol: str) -> bool`
- 作用：Perform is_supported_symbol.
- 直接原始调用：`self.chain.is_outright_symbol`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver.instrument_id_for_symbol`
- 位置：`backend/src/qts/data/historical/symbols.py:26`
- 类型：`method`
- 签名：`def instrument_id_for_symbol(self, symbol: str) -> InstrumentId`
- 作用：Perform instrument_id_for_symbol.
- 直接原始调用：`self.chain.instrument_id_for_symbol`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.data.historical.validation`

模块：`qts.data.historical.validation`

#### `qts.data.historical.validation.HistoricalCsvStats`
- 位置：`backend/src/qts/data/historical/validation.py:30`
- 类型：`class`
- 签名：`class HistoricalCsvStats`
- 作用：Streaming counters for historical CSV validation.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.HistoricalBarStream.__init__`, `qts.data.historical.validation.HistoricalDatasetValidator.validate_sample`

#### `qts.data.historical.validation.HistoricalCsvStats.as_dict`
- 位置：`backend/src/qts/data/historical/validation.py:40`
- 类型：`method`
- 签名：`def as_dict(self) -> dict[str, int]`
- 作用：Perform as_dict.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.historical.validation.HistoricalValidationSample`
- 位置：`backend/src/qts/data/historical/validation.py:53`
- 类型：`class`
- 签名：`class HistoricalValidationSample`
- 作用：Validation report plus counters for one sampled historical file.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.validation.HistoricalDatasetValidator.validate_sample`

#### `qts.data.historical.validation.HistoricalDatasetValidator`
- 位置：`backend/src/qts/data/historical/validation.py:62`
- 类型：`class`
- 签名：`class HistoricalDatasetValidator`
- 作用：Validate historical sample files and return domain-friendly diagnostics.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.validate_historical_sample`

#### `qts.data.historical.validation.HistoricalDatasetValidator.validate_sample`
- 位置：`backend/src/qts/data/historical/validation.py:67`
- 类型：`method`
- 签名：`def validate_sample(self, csv_path: Path, symbol_resolver: SourceSymbolResolver, *, sample_rows: int | None, timeframe: str='1m', schema: HistoricalCsvSchema | None=None) -> HistoricalValidationSample`
- 作用：Perform validate_sample.
- 直接原始调用：`tuple` x4, `DataValidationIssue` x2, `issues.append` x2, `DataValidationReport`, `HistoricalCsvRowMapper`, `HistoricalCsvStats`, `HistoricalValidationSample`, `ValueError`, `_group_bars`, `_group_bars.values`, `_is_spread_symbol`, `bars.append`, `csv.DictReader`, `csv_path.open`, `historical_timeframe_delta`, `issues.extend`, `mapper.to_bar`, `resolver.is_supported_symbol`, `validate_bars`, `validate_historical_csv_columns`
- 已解析到仓库内部的调用：`qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper`, `qts.data.historical.validation.HistoricalCsvStats`, `qts.data.historical.csv_format.validate_historical_csv_columns`, `qts.data.historical.validation._is_spread_symbol`, `qts.data.validation_report.DataValidationIssue`, `qts.data.historical.validation._group_bars`, `qts.data.validation_report.validate_bars`, `qts.data.historical.csv_format.historical_timeframe_delta`, `qts.data.historical.validation.HistoricalValidationSample`, `qts.data.validation_report.DataValidationReport`
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.validate_historical_sample`

#### `qts.data.historical.validation._group_bars`
- 位置：`backend/src/qts/data/historical/validation.py:142`
- 类型：`module_function`
- 签名：`def _group_bars(bars: list[Bar]) -> dict[InstrumentId, list[Bar]]`
- 作用：Perform _group_bars.
- 直接原始调用：`defaultdict`, `grouped[bar.instrument_id].append`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.validation.HistoricalDatasetValidator.validate_sample`

#### `qts.data.historical.validation._is_spread_symbol`
- 位置：`backend/src/qts/data/historical/validation.py:150`
- 类型：`module_function`
- 签名：`def _is_spread_symbol(symbol: str) -> bool`
- 作用：Perform _is_spread_symbol.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.validation.HistoricalDatasetValidator.validate_sample`

### `qts.data.live_feed`

模块：`qts.data.live_feed`

#### `qts.data.live_feed.FeedCapabilities`
- 位置：`backend/src/qts/data/live_feed.py:17`
- 类型：`class`
- 签名：`class FeedCapabilities`
- 作用：Feed-supported live market data features.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.config.HistoricalDataConfig._select_bar_file`, `qts.data.historical.service.HistoricalMarketDataService.capabilities`, `qts.data.live_feed.FakeLiveFeedAdapter.capabilities`

#### `qts.data.live_feed.FeedCapabilities.__post_init__`
- 位置：`backend/src/qts/data/live_feed.py:27`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：未写 docstring；静态推断为所属类上的 `  post init  ` 行为。
- 直接原始调用：`ValueError` x3, `any`, `item.strip`, `self.source_id.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.live_feed.FeedCapabilities.supports_timeframe`
- 位置：`backend/src/qts/data/live_feed.py:35`
- 类型：`method`
- 签名：`def supports_timeframe(self, timeframe: str) -> bool`
- 作用：Perform supports_timeframe.
- 直接原始调用：`ValueError`, `timeframe.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.live_feed.FeedCapabilities.source_timeframe_for`

#### `qts.data.live_feed.FeedCapabilities.source_timeframe_for`
- 位置：`backend/src/qts/data/live_feed.py:41`
- 类型：`method`
- 签名：`def source_timeframe_for(self, requested_timeframe: str) -> str`
- 作用：Return the provider timeframe needed to satisfy a requested bar stream.
- 直接原始调用：`ValueError` x3, `requested_timeframe.strip`, `self.supports_timeframe`
- 已解析到仓库内部的调用：`qts.data.live_feed.FeedCapabilities.supports_timeframe`
- 被以下仓库内部符号调用：`qts.data.historical.config.HistoricalDataConfig._select_bar_file`

#### `qts.data.live_feed.FeedSubscription`
- 位置：`backend/src/qts/data/live_feed.py:74`
- 类型：`class`
- 签名：`class FeedSubscription`
- 作用：Internal live feed subscription request.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.actors.market_data_actor.MarketDataActor._subscribe`

#### `qts.data.live_feed.FeedSubscription.__post_init__`
- 位置：`backend/src/qts/data/live_feed.py:81`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：未写 docstring；静态推断为所属类上的 `  post init  ` 行为。
- 直接原始调用：`ValueError` x2, `self.subscription_id.strip`, `self.timeframe.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.live_feed.LiveFeedSubscribed`
- 位置：`backend/src/qts/data/live_feed.py:89`
- 类型：`class`
- 签名：`class LiveFeedSubscribed`
- 作用：Successful live feed subscription acknowledgement.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.service.HistoricalMarketDataService.subscribe`, `qts.data.live_feed.FakeLiveFeedAdapter.subscribe`

#### `qts.data.live_feed.LiveFeedEvent`
- 位置：`backend/src/qts/data/live_feed.py:97`
- 类型：`class`
- 签名：`class LiveFeedEvent`
- 作用：Live feed payload emitted by a subscription.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.service.HistoricalMarketDataService.events`, `qts.data.live_feed.FakeLiveFeedAdapter.emit`

#### `qts.data.live_feed.LiveFeedFailure`
- 位置：`backend/src/qts/data/live_feed.py:105`
- 类型：`class`
- 签名：`class LiveFeedFailure`
- 作用：Live feed failure notification.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.live_feed.FakeLiveFeedAdapter.fail`

#### `qts.data.live_feed.LiveFeedFailure.__post_init__`
- 位置：`backend/src/qts/data/live_feed.py:112`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：未写 docstring；静态推断为所属类上的 `  post init  ` 行为。
- 直接原始调用：`ValueError`, `self.reason.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.live_feed.ReconnectPolicy`
- 位置：`backend/src/qts/data/live_feed.py:118`
- 类型：`class`
- 签名：`class ReconnectPolicy`
- 作用：Deterministic reconnect backoff policy.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.live_feed.ReconnectPolicy.__post_init__`
- 位置：`backend/src/qts/data/live_feed.py:126`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：未写 docstring；静态推断为所属类上的 `  post init  ` 行为。
- 直接原始调用：`ValueError` x4, `Decimal`, `timedelta`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.live_feed.ReconnectPolicy.delay_for_attempt`
- 位置：`backend/src/qts/data/live_feed.py:136`
- 类型：`method`
- 签名：`def delay_for_attempt(self, attempt: int) -> timedelta | None`
- 作用：Perform delay_for_attempt.
- 直接原始调用：`ValueError`, `float`, `min`, `self.initial_delay.total_seconds`, `timedelta`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.live_feed.LiveFeedAdapter`
- 位置：`backend/src/qts/data/live_feed.py:146`
- 类型：`class`
- 签名：`class LiveFeedAdapter(Protocol)`
- 作用：Live market data feed adapter boundary.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.live_feed.LiveFeedAdapter.capabilities`
- 位置：`backend/src/qts/data/live_feed.py:150`
- 类型：`property`
- 签名：`def capabilities(self) -> FeedCapabilities`
- 作用：Return feed capabilities.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.live_feed.LiveFeedAdapter.subscribe`
- 位置：`backend/src/qts/data/live_feed.py:154`
- 类型：`method`
- 签名：`def subscribe(self, subscription: FeedSubscription) -> LiveFeedSubscribed`
- 作用：Subscribe to a live feed stream.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.live_feed.FakeLiveFeedAdapter`
- 位置：`backend/src/qts/data/live_feed.py:159`
- 类型：`class`
- 签名：`class FakeLiveFeedAdapter`
- 作用：Deterministic fake live market data feed.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.live_feed.FakeLiveFeedAdapter.__init__`
- 位置：`backend/src/qts/data/live_feed.py:162`
- 类型：`method`
- 签名：`def __init__(self, *, source_id: str, capabilities: FeedCapabilities | None=None) -> None`
- 作用：未写 docstring；静态推断为所属类上的 `  init  ` 行为。
- 直接原始调用：`ValueError` x2, `source_id.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.live_feed.FakeLiveFeedAdapter.capabilities`
- 位置：`backend/src/qts/data/live_feed.py:177`
- 类型：`property`
- 签名：`def capabilities(self) -> FeedCapabilities`
- 作用：Perform capabilities.
- 直接原始调用：`FeedCapabilities`
- 已解析到仓库内部的调用：`qts.data.live_feed.FeedCapabilities`
- 被以下仓库内部符号调用：无

#### `qts.data.live_feed.FakeLiveFeedAdapter.subscription_count`
- 位置：`backend/src/qts/data/live_feed.py:182`
- 类型：`property`
- 签名：`def subscription_count(self) -> int`
- 作用：Perform subscription_count.
- 直接原始调用：`len`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.live_feed.FakeLiveFeedAdapter.subscribe`
- 位置：`backend/src/qts/data/live_feed.py:186`
- 类型：`method`
- 签名：`def subscribe(self, subscription: FeedSubscription) -> LiveFeedSubscribed`
- 作用：Perform subscribe.
- 直接原始调用：`LiveFeedSubscribed`
- 已解析到仓库内部的调用：`qts.data.live_feed.LiveFeedSubscribed`
- 被以下仓库内部符号调用：无

#### `qts.data.live_feed.FakeLiveFeedAdapter.emit`
- 位置：`backend/src/qts/data/live_feed.py:191`
- 类型：`method`
- 签名：`def emit(self, payload: LiveFeedPayload) -> LiveFeedEvent`
- 作用：Perform emit.
- 直接原始调用：`LiveFeedEvent`
- 已解析到仓库内部的调用：`qts.data.live_feed.LiveFeedEvent`
- 被以下仓库内部符号调用：无

#### `qts.data.live_feed.FakeLiveFeedAdapter.fail`
- 位置：`backend/src/qts/data/live_feed.py:195`
- 类型：`method`
- 签名：`def fail(self, subscription_id: str, *, reason: str) -> LiveFeedFailure`
- 作用：Perform fail.
- 直接原始调用：`KeyError`, `LiveFeedFailure`
- 已解析到仓库内部的调用：`qts.data.live_feed.LiveFeedFailure`
- 被以下仓库内部符号调用：无

### `qts.data.provenance`

模块：`qts.data.provenance`

#### `qts.data.provenance.DatasetMetadata`
- 位置：`backend/src/qts/data/provenance.py:13`
- 类型：`class`
- 签名：`class DatasetMetadata`
- 作用：Stable reference to historical data used by simulation or research.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.inputs.BacktestInputBuilder._dataset_metadata`

#### `qts.data.provenance.DatasetMetadata.__post_init__`
- 位置：`backend/src/qts/data/provenance.py:26`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`self._require_text` x7, `require_aware_datetime`
- 已解析到仓库内部的调用：`qts.data.provenance.DatasetMetadata._require_text`, `qts.core.time.require_aware_datetime`
- 被以下仓库内部符号调用：无

#### `qts.data.provenance.DatasetMetadata.reference`
- 位置：`backend/src/qts/data/provenance.py:39`
- 类型：`property`
- 签名：`def reference(self) -> str`
- 作用：Perform reference.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.provenance.DatasetMetadata._require_text`
- 位置：`backend/src/qts/data/provenance.py:45`
- 类型：`staticmethod`
- 签名：`def _require_text(value: str, name: str) -> None`
- 作用：Perform _require_text.
- 直接原始调用：`ValueError`, `value.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.provenance.DatasetMetadata.__post_init__`

### `qts.data.sessions.filter`

模块：`qts.data.sessions.filter`

#### `qts.data.sessions.filter.SessionLookup`
- 位置：`backend/src/qts/data/sessions/filter.py:13`
- 类型：`class`
- 签名：`class SessionLookup(Protocol)`
- 作用：Calendar session lookup required by session filters.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.sessions.filter.SessionLookup.session_for`
- 位置：`backend/src/qts/data/sessions/filter.py:16`
- 类型：`method`
- 签名：`def session_for(self, calendar_id: str, session_date: date) -> MarketSession`
- 作用：Return the internal market session for the date.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.sessions.filter.filter_session_bars`
- 位置：`backend/src/qts/data/sessions/filter.py:20`
- 类型：`module_function`
- 签名：`def filter_session_bars(bars: Iterable[Bar], *, calendar_registry: SessionLookup, calendar_id: str, session_date: date) -> list[Bar]`
- 作用：Return bars whose start and end fall inside the half-open session.
- 直接原始调用：`_bar_inside_session`, `calendar_registry.session_for`
- 已解析到仓库内部的调用：`qts.data.sessions.filter._bar_inside_session`
- 被以下仓库内部符号调用：无

#### `qts.data.sessions.filter._bar_inside_session`
- 位置：`backend/src/qts/data/sessions/filter.py:33`
- 类型：`module_function`
- 签名：`def _bar_inside_session(bar: Bar, session: MarketSession) -> bool`
- 作用：Perform _bar_inside_session.
- 直接原始调用：`session.interval.contains`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.sessions.filter.filter_session_bars`

### `qts.data.sessions.window`

模块：`qts.data.sessions.window`

#### `qts.data.sessions.window.RegularSessionWindow`
- 位置：`backend/src/qts/data/sessions/window.py:12`
- 类型：`class`
- 签名：`class RegularSessionWindow`
- 作用：A recurring half-open exchange session window.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.sessions.window.RegularSessionWindow.__post_init__`
- 位置：`backend/src/qts/data/sessions/window.py:23`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError` x2, `self.exchange_timezone.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.sessions.window.RegularSessionWindow.session_id_for_timestamp`
- 位置：`backend/src/qts/data/sessions/window.py:30`
- 类型：`method`
- 签名：`def session_id_for_timestamp(self, timestamp: datetime) -> str | None`
- 作用：Return the exchange-local close-date session id containing timestamp.
- 直接原始调用：`self.session_date_for_timestamp`, `session_date.isoformat`
- 已解析到仓库内部的调用：`qts.data.sessions.window.RegularSessionWindow.session_date_for_timestamp`
- 被以下仓库内部符号调用：无

#### `qts.data.sessions.window.RegularSessionWindow.session_date_for_timestamp`
- 位置：`backend/src/qts/data/sessions/window.py:36`
- 类型：`method`
- 签名：`def session_date_for_timestamp(self, timestamp: datetime) -> date | None`
- 作用：Return the exchange-local close date for timestamp, or None if outside.
- 直接原始调用：`local_timestamp.date` x3, `local_timestamp.time`, `timedelta`, `to_exchange_time`
- 已解析到仓库内部的调用：`qts.core.time.to_exchange_time`
- 被以下仓库内部符号调用：`qts.data.sessions.window.RegularSessionWindow.session_id_for_timestamp`

#### `qts.data.sessions.window.RegularSessionWindow.to_payload`
- 位置：`backend/src/qts/data/sessions/window.py:51`
- 类型：`method`
- 签名：`def to_payload(self) -> dict[str, str]`
- 作用：Return a stable JSON-serializable description of the session rule.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.data.stores.base`

模块：`qts.data.stores.base`

#### `qts.data.stores.base.MarketDataStore`
- 位置：`backend/src/qts/data/stores/base.py:13`
- 类型：`class`
- 签名：`class MarketDataStore(Protocol)`
- 作用：Store and read bars by internal instrument identity.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.stores.base.MarketDataStore.write_bars`
- 位置：`backend/src/qts/data/stores/base.py:16`
- 类型：`method`
- 签名：`def write_bars(self, bars: Iterable[Bar]) -> None`
- 作用：Persist bars.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.stores.base.MarketDataStore.read_bars`
- 位置：`backend/src/qts/data/stores/base.py:20`
- 类型：`method`
- 签名：`def read_bars(self, *, instrument_id: InstrumentId, timeframe: str, start: datetime, end: datetime) -> tuple[Bar, ...]`
- 作用：Read bars for an interval.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.data.stores.memory_store`

模块：`qts.data.stores.memory_store`

#### `qts.data.stores.memory_store.InMemoryMarketDataStore`
- 位置：`backend/src/qts/data/stores/memory_store.py:13`
- 类型：`class`
- 签名：`class InMemoryMarketDataStore`
- 作用：In-memory bar store for tests and local runs.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.stores.memory_store.InMemoryMarketDataStore.__init__`
- 位置：`backend/src/qts/data/stores/memory_store.py:16`
- 类型：`method`
- 签名：`def __init__(self) -> None`
- 作用：Perform __init__.
- 直接原始调用：`defaultdict`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.stores.memory_store.InMemoryMarketDataStore.write_bars`
- 位置：`backend/src/qts/data/stores/memory_store.py:20`
- 类型：`method`
- 签名：`def write_bars(self, bars: Iterable[Bar]) -> None`
- 作用：Perform write_bars.
- 直接原始调用：`self._bars[key].append`, `self._bars[key].sort`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.stores.memory_store.InMemoryMarketDataStore.read_bars`
- 位置：`backend/src/qts/data/stores/memory_store.py:27`
- 类型：`method`
- 签名：`def read_bars(self, *, instrument_id: InstrumentId, timeframe: str, start: datetime, end: datetime) -> tuple[Bar, ...]`
- 作用：Perform read_bars.
- 直接原始调用：`self._bars.get`, `tuple`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.data.stores.parquet_store`

模块：`qts.data.stores.parquet_store`

#### `qts.data.stores.parquet_store.ParquetMarketDataStore`
- 位置：`backend/src/qts/data/stores/parquet_store.py:21`
- 类型：`class`
- 签名：`class ParquetMarketDataStore`
- 作用：File-backed bar store partitioned by instrument, timeframe, and date.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.stores.parquet_store.ParquetMarketDataStore.__init__`
- 位置：`backend/src/qts/data/stores/parquet_store.py:24`
- 类型：`method`
- 签名：`def __init__(self, root: Path) -> None`
- 作用：Perform __init__.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.stores.parquet_store.ParquetMarketDataStore.write_bars`
- 位置：`backend/src/qts/data/stores/parquet_store.py:28`
- 类型：`method`
- 签名：`def write_bars(self, bars: Iterable[Bar]) -> None`
- 作用：Perform write_bars.
- 直接原始调用：`handle.write` x2, `grouped.items`, `grouped.setdefault`, `grouped.setdefault.append`, `json.dumps`, `list`, `path.exists`, `path.open`, `path.parent.mkdir`, `self._bar_to_json`, `self._path_for`, `self._read_file`, `sorted`
- 已解析到仓库内部的调用：`qts.data.stores.parquet_store.ParquetMarketDataStore._path_for`, `qts.data.stores.parquet_store.ParquetMarketDataStore._read_file`, `qts.data.stores.parquet_store.ParquetMarketDataStore._bar_to_json`
- 被以下仓库内部符号调用：无

#### `qts.data.stores.parquet_store.ParquetMarketDataStore.read_bars`
- 位置：`backend/src/qts/data/stores/parquet_store.py:45`
- 类型：`method`
- 签名：`def read_bars(self, *, instrument_id: InstrumentId, timeframe: str, start: datetime, end: datetime) -> tuple[Bar, ...]`
- 作用：Perform read_bars.
- 直接原始调用：`sorted` x2, `bars.extend`, `base.exists`, `base.glob`, `self._read_file`, `tuple`
- 已解析到仓库内部的调用：`qts.data.stores.parquet_store.ParquetMarketDataStore._read_file`
- 被以下仓库内部符号调用：无

#### `qts.data.stores.parquet_store.ParquetMarketDataStore._path_for`
- 位置：`backend/src/qts/data/stores/parquet_store.py:66`
- 类型：`method`
- 签名：`def _path_for(self, bar: Bar) -> Path`
- 作用：Perform _path_for.
- 直接原始调用：`bar.start_time.date`, `bar.start_time.date.isoformat`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.stores.parquet_store.ParquetMarketDataStore.write_bars`

#### `qts.data.stores.parquet_store.ParquetMarketDataStore._read_file`
- 位置：`backend/src/qts/data/stores/parquet_store.py:75`
- 类型：`method`
- 签名：`def _read_file(self, path: Path) -> tuple[Bar, ...]`
- 作用：Perform _read_file.
- 直接原始调用：`json.loads`, `line.strip`, `path.open`, `self._bar_from_json`, `tuple`
- 已解析到仓库内部的调用：`qts.data.stores.parquet_store.ParquetMarketDataStore._bar_from_json`
- 被以下仓库内部符号调用：`qts.data.stores.parquet_store.ParquetMarketDataStore.read_bars`, `qts.data.stores.parquet_store.ParquetMarketDataStore.write_bars`

#### `qts.data.stores.parquet_store.ParquetMarketDataStore._bar_to_json`
- 位置：`backend/src/qts/data/stores/parquet_store.py:81`
- 类型：`staticmethod`
- 签名：`def _bar_to_json(bar: Bar) -> dict[str, Any]`
- 作用：Perform _bar_to_json.
- 直接原始调用：`str` x7, `bar.end_time.isoformat`, `bar.start_time.isoformat`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.stores.parquet_store.ParquetMarketDataStore.write_bars`

#### `qts.data.stores.parquet_store.ParquetMarketDataStore._bar_from_json`
- 位置：`backend/src/qts/data/stores/parquet_store.py:102`
- 类型：`staticmethod`
- 签名：`def _bar_from_json(payload: dict[str, Any]) -> Bar`
- 作用：Perform _bar_from_json.
- 直接原始调用：`str` x12, `Decimal` x7, `bool` x2, `datetime.fromisoformat` x2, `Bar`, `InstrumentId`, `int`
- 已解析到仓库内部的调用：`qts.core.ids.InstrumentId`
- 被以下仓库内部符号调用：`qts.data.stores.parquet_store.ParquetMarketDataStore._read_file`

### `qts.data.subscriptions`

模块：`qts.data.subscriptions`

#### `qts.data.subscriptions.SourceStreamType`
- 位置：`backend/src/qts/data/subscriptions.py:12`
- 类型：`class`
- 签名：`class SourceStreamType(StrEnum)`
- 作用：Physical market data stream type.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.subscriptions.LogicalSubscription`
- 位置：`backend/src/qts/data/subscriptions.py:21`
- 类型：`class`
- 签名：`class LogicalSubscription`
- 作用：Strategy-requested market data stream.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.actors.market_data_actor.MarketDataActor._subscribe`

#### `qts.data.subscriptions.LogicalSubscription.__post_init__`
- 位置：`backend/src/qts/data/subscriptions.py:29`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError` x2, `self.requested_timeframe.strip`, `self.subscriber_id.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.subscriptions.LogicalSubscriptionKey`
- 位置：`backend/src/qts/data/subscriptions.py:38`
- 类型：`class`
- 签名：`class LogicalSubscriptionKey`
- 作用：Deduplication key for strategy-facing subscribers.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.subscriptions.logical_key`

#### `qts.data.subscriptions.PhysicalSubscriptionKey`
- 位置：`backend/src/qts/data/subscriptions.py:47`
- 类型：`class`
- 签名：`class PhysicalSubscriptionKey`
- 作用：Deduplication key for provider-facing subscriptions.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.subscriptions.plan_physical_subscription`

#### `qts.data.subscriptions.PhysicalSubscriptionKey.__post_init__`
- 位置：`backend/src/qts/data/subscriptions.py:55`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError` x2, `self.source_id.strip`, `self.source_timeframe.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.subscriptions.logical_key`
- 位置：`backend/src/qts/data/subscriptions.py:63`
- 类型：`module_function`
- 签名：`def logical_key(subscription: LogicalSubscription) -> LogicalSubscriptionKey`
- 作用：Return the logical fan-out key for a subscription.
- 直接原始调用：`LogicalSubscriptionKey`
- 已解析到仓库内部的调用：`qts.data.subscriptions.LogicalSubscriptionKey`
- 被以下仓库内部符号调用：`qts.runtime.actors.market_data_actor.MarketDataActor._subscribe`

#### `qts.data.subscriptions.plan_physical_subscription`
- 位置：`backend/src/qts/data/subscriptions.py:73`
- 类型：`module_function`
- 签名：`def plan_physical_subscription(subscription: LogicalSubscription, *, capabilities: FeedCapabilities) -> PhysicalSubscriptionKey`
- 作用：Map one logical subscription to its provider source subscription.
- 直接原始调用：`PhysicalSubscriptionKey`, `ValueError`, `capabilities.source_timeframe_for`
- 已解析到仓库内部的调用：`qts.data.subscriptions.PhysicalSubscriptionKey`
- 被以下仓库内部符号调用：`qts.runtime.actors.market_data_actor.MarketDataActor._subscribe`

### `qts.data.validation_report`

模块：`qts.data.validation_report`

#### `qts.data.validation_report.DataValidationIssueCode`
- 位置：`backend/src/qts/data/validation_report.py:13`
- 类型：`class`
- 签名：`class DataValidationIssueCode(StrEnum)`
- 作用：Known market data validation issue codes.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.validation_report.DataValidationSeverity`
- 位置：`backend/src/qts/data/validation_report.py:27`
- 类型：`class`
- 签名：`class DataValidationSeverity(StrEnum)`
- 作用：Severity for data validation issues.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.validation_report.DataValidationIssue`
- 位置：`backend/src/qts/data/validation_report.py:36`
- 类型：`class`
- 签名：`class DataValidationIssue`
- 作用：One validation issue for a bar sequence.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.validation.HistoricalDatasetValidator.validate_sample`, `qts.data.validation_report._append_ohlc_issue`, `qts.data.validation_report.validate_bars`

#### `qts.data.validation_report.DataValidationReport`
- 位置：`backend/src/qts/data/validation_report.py:45`
- 类型：`class`
- 签名：`class DataValidationReport`
- 作用：Validation result for a bar sequence.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.validation.HistoricalDatasetValidator.validate_sample`, `qts.data.validation_report.validate_bars`

#### `qts.data.validation_report.DataValidationReport.valid`
- 位置：`backend/src/qts/data/validation_report.py:51`
- 类型：`property`
- 签名：`def valid(self) -> bool`
- 作用：Perform valid.
- 直接原始调用：`any`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.validation_report.DataValidationReport.max_severity`
- 位置：`backend/src/qts/data/validation_report.py:56`
- 类型：`property`
- 签名：`def max_severity(self) -> DataValidationSeverity | None`
- 作用：Perform max_severity.
- 直接原始调用：`max`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.data.validation_report.validate_bars`
- 位置：`backend/src/qts/data/validation_report.py:68`
- 类型：`module_function`
- 签名：`def validate_bars(bars: tuple[Bar, ...], *, session_interval: TimeInterval | None=None, expected_interval: timedelta | None=None) -> DataValidationReport`
- 作用：Validate bar ordering, overlap, and optional session containment.
- 直接原始调用：`DataValidationIssue` x6, `issues.append` x6, `bar.start_time.isoformat` x5, `tuple` x2, `DataValidationReport`, `ValueError`, `_append_ohlc_issue`, `int`, `previous.end_time.isoformat`, `session_interval.contains`, `sorted`, `timedelta`
- 已解析到仓库内部的调用：`qts.data.validation_report.DataValidationIssue`, `qts.data.validation_report._append_ohlc_issue`, `qts.data.validation_report.DataValidationReport`
- 被以下仓库内部符号调用：`qts.data.historical.validation.HistoricalDatasetValidator.validate_sample`

#### `qts.data.validation_report._append_ohlc_issue`
- 位置：`backend/src/qts/data/validation_report.py:145`
- 类型：`module_function`
- 签名：`def _append_ohlc_issue(issues: list[DataValidationIssue], bar: Bar) -> None`
- 作用：Perform _append_ohlc_issue.
- 直接原始调用：`DataValidationIssue`, `bar.start_time.isoformat`, `issues.append`, `max`, `min`
- 已解析到仓库内部的调用：`qts.data.validation_report.DataValidationIssue`
- 被以下仓库内部符号调用：`qts.data.validation_report.validate_bars`

### `qts.domain.events.event`

模块：`qts.domain.events.event`

#### `qts.domain.events.event.BaseEvent`
- 位置：`backend/src/qts/domain/events/event.py:13`
- 类型：`class`
- 签名：`class BaseEvent`
- 作用：Minimal event envelope used for traceable internal messages.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.domain.events.event.BaseEvent.__post_init__`
- 位置：`backend/src/qts/domain/events/event.py:24`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError` x3, `require_aware_datetime`, `self.event_type.strip`, `self.partition_key.strip`, `self.source.strip`
- 已解析到仓库内部的调用：`qts.core.time.require_aware_datetime`
- 被以下仓库内部符号调用：无

### `qts.domain.events.metadata`

模块：`qts.domain.events.metadata`

#### `qts.domain.events.metadata.EventMetadata`
- 位置：`backend/src/qts/domain/events/metadata.py:21`
- 类型：`class`
- 签名：`class EventMetadata`
- 作用：Trace metadata carried by platform events.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.domain.events.metadata.EventMetadata.__post_init__`
- 位置：`backend/src/qts/domain/events/metadata.py:39`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError` x3, `require_aware_datetime` x2, `self.event_type.strip`, `self.partition_key.strip`
- 已解析到仓库内部的调用：`qts.core.time.require_aware_datetime`
- 被以下仓库内部符号调用：无

### `qts.domain.instruments.contract_spec`

模块：`qts.domain.instruments.contract_spec`

#### `qts.domain.instruments.contract_spec.SettlementType`
- 位置：`backend/src/qts/domain/instruments/contract_spec.py:10`
- 类型：`class`
- 签名：`class SettlementType(StrEnum)`
- 作用：How a contract settles.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.domain.instruments.contract_spec.ContractSpec`
- 位置：`backend/src/qts/domain/instruments/contract_spec.py:18`
- 类型：`class`
- 签名：`class ContractSpec`
- 作用：Trading contract metadata required for valuation and order sizing.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.domain.instruments.contract_spec.ContractSpec.__post_init__`
- 位置：`backend/src/qts/domain/instruments/contract_spec.py:27`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`self._require_positive` x3, `ValueError`, `self.calendar_id.strip`
- 已解析到仓库内部的调用：`qts.domain.instruments.contract_spec.ContractSpec._require_positive`
- 被以下仓库内部符号调用：无

#### `qts.domain.instruments.contract_spec.ContractSpec._require_positive`
- 位置：`backend/src/qts/domain/instruments/contract_spec.py:36`
- 类型：`staticmethod`
- 签名：`def _require_positive(value: Decimal, name: str) -> None`
- 作用：Perform _require_positive.
- 直接原始调用：`Decimal`, `ValueError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.domain.instruments.contract_spec.ContractSpec.__post_init__`

### `qts.domain.instruments.derivative_spec`

模块：`qts.domain.instruments.derivative_spec`

#### `qts.domain.instruments.derivative_spec.OptionRight`
- 位置：`backend/src/qts/domain/instruments/derivative_spec.py:13`
- 类型：`class`
- 签名：`class OptionRight(StrEnum)`
- 作用：Option payoff direction.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.domain.instruments.derivative_spec.ExerciseStyle`
- 位置：`backend/src/qts/domain/instruments/derivative_spec.py:20`
- 类型：`class`
- 签名：`class ExerciseStyle(StrEnum)`
- 作用：Option exercise style.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.domain.instruments.derivative_spec.DerivativeSpec`
- 位置：`backend/src/qts/domain/instruments/derivative_spec.py:28`
- 类型：`class`
- 签名：`class DerivativeSpec`
- 作用：Common derivative metadata.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.domain.instruments.derivative_spec.FutureSpec`
- 位置：`backend/src/qts/domain/instruments/derivative_spec.py:36`
- 类型：`class`
- 签名：`class FutureSpec(DerivativeSpec)`
- 作用：Future contract metadata.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.domain.instruments.derivative_spec.FutureSpec.__post_init__`
- 位置：`backend/src/qts/domain/instruments/derivative_spec.py:41`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError`, `self.root_symbol.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.domain.instruments.derivative_spec.OptionSpec`
- 位置：`backend/src/qts/domain/instruments/derivative_spec.py:48`
- 类型：`class`
- 签名：`class OptionSpec(DerivativeSpec)`
- 作用：Option contract metadata.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.domain.instruments.derivative_spec.OptionSpec.__post_init__`
- 位置：`backend/src/qts/domain/instruments/derivative_spec.py:55`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`Decimal`, `ValueError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.domain.instruments.instrument`

模块：`qts.domain.instruments.instrument`

#### `qts.domain.instruments.instrument.AssetClass`
- 位置：`backend/src/qts/domain/instruments/instrument.py:19`
- 类型：`class`
- 签名：`class AssetClass(StrEnum)`
- 作用：Supported instrument asset classes.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.domain.instruments.instrument.Instrument`
- 位置：`backend/src/qts/domain/instruments/instrument.py:28`
- 类型：`class`
- 签名：`class Instrument`
- 作用：Tradable instrument identified by a stable internal InstrumentId.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.domain.instruments.instrument.Instrument.__post_init__`
- 位置：`backend/src/qts/domain/instruments/instrument.py:39`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError` x5, `isinstance` x2, `self.currency.strip`, `self.exchange.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.domain.market_data.bar`

模块：`qts.domain.market_data.bar`

#### `qts.domain.market_data.bar.Bar`
- 位置：`backend/src/qts/domain/market_data/bar.py:14`
- 类型：`class`
- 签名：`class Bar`
- 作用：OHLCV bar over a half-open interval.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.domain.market_data.bar.Bar.__post_init__`
- 位置：`backend/src/qts/domain/market_data/bar.py:33`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError` x6, `self._require_non_negative` x3, `TimeInterval`, `max`, `min`, `self.session_id.strip`, `self.timeframe.strip`
- 已解析到仓库内部的调用：`qts.core.time.TimeInterval`, `qts.domain.market_data.bar.Bar._require_non_negative`
- 被以下仓库内部符号调用：无

#### `qts.domain.market_data.bar.Bar.interval`
- 位置：`backend/src/qts/domain/market_data/bar.py:55`
- 类型：`property`
- 签名：`def interval(self) -> TimeInterval`
- 作用：Perform interval.
- 直接原始调用：`TimeInterval`
- 已解析到仓库内部的调用：`qts.core.time.TimeInterval`
- 被以下仓库内部符号调用：无

#### `qts.domain.market_data.bar.Bar._require_non_negative`
- 位置：`backend/src/qts/domain/market_data/bar.py:60`
- 类型：`staticmethod`
- 签名：`def _require_non_negative(value: Decimal, name: str) -> None`
- 作用：Perform _require_non_negative.
- 直接原始调用：`Decimal`, `ValueError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.domain.market_data.bar.Bar.__post_init__`, `qts.domain.market_data.bar.Quote.__post_init__`, `qts.domain.market_data.bar.Tick.__post_init__`

#### `qts.domain.market_data.bar.Quote`
- 位置：`backend/src/qts/domain/market_data/bar.py:67`
- 类型：`class`
- 签名：`class Quote`
- 作用：Top-of-book quote.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.domain.market_data.bar.Quote.__post_init__`
- 位置：`backend/src/qts/domain/market_data/bar.py:77`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`Bar._require_non_negative` x2, `ValueError`, `require_aware_datetime`
- 已解析到仓库内部的调用：`qts.core.time.require_aware_datetime`, `qts.domain.market_data.bar.Bar._require_non_negative`
- 被以下仓库内部符号调用：无

#### `qts.domain.market_data.bar.Quote.spread`
- 位置：`backend/src/qts/domain/market_data/bar.py:86`
- 类型：`property`
- 签名：`def spread(self) -> Decimal`
- 作用：Perform spread.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.domain.market_data.bar.Tick`
- 位置：`backend/src/qts/domain/market_data/bar.py:92`
- 类型：`class`
- 签名：`class Tick`
- 作用：Trade tick.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.domain.market_data.bar.Tick.__post_init__`
- 位置：`backend/src/qts/domain/market_data/bar.py:100`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`Bar._require_non_negative`, `require_aware_datetime`
- 已解析到仓库内部的调用：`qts.core.time.require_aware_datetime`, `qts.domain.market_data.bar.Bar._require_non_negative`
- 被以下仓库内部符号调用：无

### `qts.domain.orders.value_objects`

模块：`qts.domain.orders.value_objects`

#### `qts.domain.orders.value_objects.OrderState`
- 位置：`backend/src/qts/domain/orders/value_objects.py:12`
- 类型：`class`
- 签名：`class OrderState(StrEnum)`
- 作用：Execution lifecycle states for orders.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.domain.orders.value_objects.OrderSide`
- 位置：`backend/src/qts/domain/orders/value_objects.py:26`
- 类型：`class`
- 签名：`class OrderSide(StrEnum)`
- 作用：Order side.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.domain.orders.value_objects.OrderIntent`
- 位置：`backend/src/qts/domain/orders/value_objects.py:34`
- 类型：`class`
- 签名：`class OrderIntent`
- 作用：Approved order instruction before broker submission.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.domain.orders.value_objects.OrderIntent.__post_init__`
- 位置：`backend/src/qts/domain/orders/value_objects.py:42`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`Decimal`, `ValueError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.domain.orders.value_objects.CancelIntent`
- 位置：`backend/src/qts/domain/orders/value_objects.py:49`
- 类型：`class`
- 签名：`class CancelIntent`
- 作用：Intent to cancel an order through OrderManager.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.domain.orders.value_objects.ReplaceIntent`
- 位置：`backend/src/qts/domain/orders/value_objects.py:57`
- 类型：`class`
- 签名：`class ReplaceIntent`
- 作用：Intent to replace an order through OrderManager.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.domain.orders.value_objects.ReplaceIntent.__post_init__`
- 位置：`backend/src/qts/domain/orders/value_objects.py:63`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`Decimal`, `ValueError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.domain.orders.value_objects.Order`
- 位置：`backend/src/qts/domain/orders/value_objects.py:70`
- 类型：`class`
- 签名：`class Order`
- 作用：Order snapshot owned by OrderManager.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.domain.orders.value_objects.ExecutionReportStatus`
- 位置：`backend/src/qts/domain/orders/value_objects.py:79`
- 类型：`class`
- 签名：`class ExecutionReportStatus(StrEnum)`
- 作用：Normalized broker report status.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.domain.orders.value_objects.ExecutionReport`
- 位置：`backend/src/qts/domain/orders/value_objects.py:90`
- 类型：`class`
- 签名：`class ExecutionReport`
- 作用：Normalized broker execution report.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.domain.orders.value_objects.ExecutionReport.__post_init__`
- 位置：`backend/src/qts/domain/orders/value_objects.py:102`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError` x5, `Decimal` x3, `self.broker_order_id.strip`, `self.report_id.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.domain.orders.value_objects.OrderFill`
- 位置：`backend/src/qts/domain/orders/value_objects.py:117`
- 类型：`class`
- 签名：`class OrderFill`
- 作用：OrderManager-validated fill event.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.domain.orders.value_objects.OrderManagerResult`
- 位置：`backend/src/qts/domain/orders/value_objects.py:131`
- 类型：`class`
- 签名：`class OrderManagerResult`
- 作用：Events emitted by processing an execution report.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.domain.orders.value_objects.OrderManagerSnapshot`
- 位置：`backend/src/qts/domain/orders/value_objects.py:139`
- 类型：`class`
- 签名：`class OrderManagerSnapshot`
- 作用：Serializable OrderManager state for reconnect/recovery.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.domain.risk.decision`

模块：`qts.domain.risk.decision`

#### `qts.domain.risk.decision.RiskDecisionStatus`
- 位置：`backend/src/qts/domain/risk/decision.py:10`
- 类型：`class`
- 签名：`class RiskDecisionStatus(StrEnum)`
- 作用：Risk check outcome.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.domain.risk.decision.RiskDecision`
- 位置：`backend/src/qts/domain/risk/decision.py:19`
- 类型：`class`
- 签名：`class RiskDecision`
- 作用：Explicit result of a risk check.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.domain.risk.decision.RiskDecision.approve`
- 位置：`backend/src/qts/domain/risk/decision.py:29`
- 类型：`classmethod`
- 签名：`def approve(cls, *, rule_id: str | None=None, checked_at: datetime | None=None) -> RiskDecision`
- 作用：Perform approve.
- 直接原始调用：`cls`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.domain.risk.decision.RiskDecision.rejected`
- 位置：`backend/src/qts/domain/risk/decision.py:39`
- 类型：`classmethod`
- 签名：`def rejected(cls, reason_code: str, reason: str, *, rule_id: str | None=None, checked_at: datetime | None=None) -> RiskDecision`
- 作用：Perform rejected.
- 直接原始调用：`ValueError` x2, `cls`, `reason.strip`, `reason_code.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.domain.risk.decision.RiskDecision.approved`
- 位置：`backend/src/qts/domain/risk/decision.py:61`
- 类型：`property`
- 签名：`def approved(self) -> bool`
- 作用：Perform approved.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.domain.risk.decision.RiskDecision.reason_text`
- 位置：`backend/src/qts/domain/risk/decision.py:66`
- 类型：`property`
- 签名：`def reason_text(self) -> str | None`
- 作用：Perform reason_text.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.domain.risk.request`

模块：`qts.domain.risk.request`

#### `qts.domain.risk.request.OrderRiskRequest`
- 位置：`backend/src/qts/domain/risk/request.py:14`
- 类型：`class`
- 签名：`class OrderRiskRequest`
- 作用：Pre-trade risk input for a proposed order.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.domain.risk.request.OrderRiskRequest.__post_init__`
- 位置：`backend/src/qts/domain/risk/request.py:23`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`Decimal` x3, `ValueError` x3, `require_aware_datetime`
- 已解析到仓库内部的调用：`qts.core.time.require_aware_datetime`
- 被以下仓库内部符号调用：无

#### `qts.domain.risk.request.OrderRiskRequest.notional`
- 位置：`backend/src/qts/domain/risk/request.py:35`
- 类型：`property`
- 签名：`def notional(self) -> Decimal`
- 作用：Perform notional.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.execution.adapters.ibkr_order_execution`

模块：`qts.execution.adapters.ibkr_order_execution`

#### `qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionConnection`
- 位置：`backend/src/qts/execution/adapters/ibkr_order_execution.py:15`
- 类型：`class`
- 签名：`class IbkrOrderExecutionConnection`
- 作用：IBKR order execution connection settings.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionConnection.__post_init__`
- 位置：`backend/src/qts/execution/adapters/ibkr_order_execution.py:24`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError` x4, `self.account_id.strip`, `self.host.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.execution.adapters.ibkr_order_execution.IbkrOrderRequest`
- 位置：`backend/src/qts/execution/adapters/ibkr_order_execution.py:37`
- 类型：`class`
- 签名：`class IbkrOrderRequest`
- 作用：IBKR order request produced at the adapter boundary.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionAdapter.to_order_request`

#### `qts.execution.adapters.ibkr_order_execution.IbkrExecutionReport`
- 位置：`backend/src/qts/execution/adapters/ibkr_order_execution.py:48`
- 类型：`class`
- 签名：`class IbkrExecutionReport`
- 作用：IBKR execution report shape before normalization.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionAdapter`
- 位置：`backend/src/qts/execution/adapters/ibkr_order_execution.py:59`
- 类型：`class`
- 签名：`class IbkrOrderExecutionAdapter`
- 作用：Maps internal orders to IBKR order requests and normalizes reports.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionAdapter.__init__`
- 位置：`backend/src/qts/execution/adapters/ibkr_order_execution.py:62`
- 类型：`method`
- 签名：`def __init__(self, *, connection: IbkrOrderExecutionConnection, symbol_mapping: BrokerSymbolMapping) -> None`
- 作用：Perform __init__.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionAdapter.to_order_request`
- 位置：`backend/src/qts/execution/adapters/ibkr_order_execution.py:72`
- 类型：`method`
- 签名：`def to_order_request(self, intent: OrderIntent) -> IbkrOrderRequest`
- 作用：Perform to_order_request.
- 直接原始调用：`IbkrOrderRequest`, `self._symbol_mapping.to_broker_symbol`
- 已解析到仓库内部的调用：`qts.execution.adapters.ibkr_order_execution.IbkrOrderRequest`
- 被以下仓库内部符号调用：无

#### `qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionAdapter.normalize_execution_report`
- 位置：`backend/src/qts/execution/adapters/ibkr_order_execution.py:82`
- 类型：`method`
- 签名：`def normalize_execution_report(self, report: IbkrExecutionReport) -> ExecutionReport`
- 作用：Perform normalize_execution_report.
- 直接原始调用：`ExecutionReport`, `normalize_broker_status`
- 已解析到仓库内部的调用：`qts.execution.broker.normalize_broker_status`
- 被以下仓库内部符号调用：无

### `qts.execution.broker`

模块：`qts.execution.broker`

#### `qts.execution.broker.BrokerCapabilities`
- 位置：`backend/src/qts/execution/broker.py:15`
- 类型：`class`
- 签名：`class BrokerCapabilities`
- 作用：Broker-supported live execution features.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.execution.broker.FakeBrokerAdapter.capabilities`

#### `qts.execution.broker.BrokerCapabilities.__post_init__`
- 位置：`backend/src/qts/execution/broker.py:31`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：未写 docstring；静态推断为所属类上的 `  post init  ` 行为。
- 直接原始调用：`ValueError` x2, `Decimal`, `any`, `item.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.execution.broker.BrokerCapabilities.supports_asset_class`
- 位置：`backend/src/qts/execution/broker.py:37`
- 类型：`method`
- 签名：`def supports_asset_class(self, asset_class: str) -> bool`
- 作用：Perform supports_asset_class.
- 直接原始调用：`ValueError`, `asset_class.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.execution.broker.BrokerCapabilities.supports_order_type`
- 位置：`backend/src/qts/execution/broker.py:43`
- 类型：`method`
- 签名：`def supports_order_type(self, order_type: BrokerOrderType) -> bool`
- 作用：Perform supports_order_type.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.execution.broker.BrokerCapabilities.supports_tif`
- 位置：`backend/src/qts/execution/broker.py:53`
- 类型：`method`
- 签名：`def supports_tif(self, time_in_force: TimeInForce) -> bool`
- 作用：Perform supports_tif.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.execution.broker.BrokerOrderType`
- 位置：`backend/src/qts/execution/broker.py:58`
- 类型：`class`
- 签名：`class BrokerOrderType(StrEnum)`
- 作用：Order types modeled before broker submission.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.execution.broker.TimeInForce`
- 位置：`backend/src/qts/execution/broker.py:66`
- 类型：`class`
- 签名：`class TimeInForce(StrEnum)`
- 作用：Time-in-force values modeled at the execution boundary.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.execution.broker.BrokerOrderRequest`
- 位置：`backend/src/qts/execution/broker.py:75`
- 类型：`class`
- 签名：`class BrokerOrderRequest`
- 作用：Internal order request sent to the broker adapter boundary.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.application.commands.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill`

#### `qts.execution.broker.BrokerOrderRequest.__post_init__`
- 位置：`backend/src/qts/execution/broker.py:85`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：未写 docstring；静态推断为所属类上的 `  post init  ` 行为。
- 直接原始调用：`Decimal`, `ValueError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.execution.broker.BrokerExecutionReportStatus`
- 位置：`backend/src/qts/execution/broker.py:90`
- 类型：`class`
- 签名：`class BrokerExecutionReportStatus(StrEnum)`
- 作用：Broker-boundary execution report status.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.execution.broker.BrokerExecutionReport`
- 位置：`backend/src/qts/execution/broker.py:101`
- 类型：`class`
- 签名：`class BrokerExecutionReport`
- 作用：Normalized broker callback before it reaches OrderManager.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.execution.broker.FakeBrokerAdapter._report`

#### `qts.execution.broker.BrokerExecutionReport.__post_init__`
- 位置：`backend/src/qts/execution/broker.py:116`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：未写 docstring；静态推断为所属类上的 `  post init  ` 行为。
- 直接原始调用：`ValueError` x4, `Decimal` x2, `self.broker_order_id.strip`, `self.report_id.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.execution.broker.BrokerAdapter`
- 位置：`backend/src/qts/execution/broker.py:127`
- 类型：`class`
- 签名：`class BrokerAdapter(Protocol)`
- 作用：Stable broker execution boundary.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.execution.broker.BrokerAdapter.capabilities`
- 位置：`backend/src/qts/execution/broker.py:131`
- 类型：`property`
- 签名：`def capabilities(self) -> BrokerCapabilities`
- 作用：Return broker capabilities.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.execution.broker.BrokerAdapter.submit_order`
- 位置：`backend/src/qts/execution/broker.py:135`
- 类型：`method`
- 签名：`def submit_order(self, request: BrokerOrderRequest) -> BrokerExecutionReport`
- 作用：Submit an order request.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.execution.broker.BrokerAdapter.cancel_order`
- 位置：`backend/src/qts/execution/broker.py:139`
- 类型：`method`
- 签名：`def cancel_order(self, order_id: OrderId) -> BrokerExecutionReport`
- 作用：Cancel an order by internal ID.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.execution.broker.FakeBrokerAdapter`
- 位置：`backend/src/qts/execution/broker.py:144`
- 类型：`class`
- 签名：`class FakeBrokerAdapter`
- 作用：Deterministic fake broker for live-beta tests and local runs.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.application.commands.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill`

#### `qts.execution.broker.FakeBrokerAdapter.__init__`
- 位置：`backend/src/qts/execution/broker.py:147`
- 类型：`method`
- 签名：`def __init__(self, *, broker_id: BrokerId) -> None`
- 作用：未写 docstring；静态推断为所属类上的 `  init  ` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.execution.broker.FakeBrokerAdapter.capabilities`
- 位置：`backend/src/qts/execution/broker.py:154`
- 类型：`property`
- 签名：`def capabilities(self) -> BrokerCapabilities`
- 作用：Perform capabilities.
- 直接原始调用：`BrokerCapabilities`
- 已解析到仓库内部的调用：`qts.execution.broker.BrokerCapabilities`
- 被以下仓库内部符号调用：无

#### `qts.execution.broker.FakeBrokerAdapter.submit_order`
- 位置：`backend/src/qts/execution/broker.py:158`
- 类型：`method`
- 签名：`def submit_order(self, request: BrokerOrderRequest) -> BrokerExecutionReport`
- 作用：Perform submit_order.
- 直接原始调用：`len`, `self._broker_order_ids.setdefault`, `self._report`
- 已解析到仓库内部的调用：`qts.execution.broker.FakeBrokerAdapter._report`
- 被以下仓库内部符号调用：无

#### `qts.execution.broker.FakeBrokerAdapter.cancel_order`
- 位置：`backend/src/qts/execution/broker.py:170`
- 类型：`method`
- 签名：`def cancel_order(self, order_id: OrderId) -> BrokerExecutionReport`
- 作用：Perform cancel_order.
- 直接原始调用：`self._report`
- 已解析到仓库内部的调用：`qts.execution.broker.FakeBrokerAdapter._report`
- 被以下仓库内部符号调用：无

#### `qts.execution.broker.FakeBrokerAdapter.emit_fill`
- 位置：`backend/src/qts/execution/broker.py:179`
- 类型：`method`
- 签名：`def emit_fill(self, *, order_id: OrderId, quantity: Decimal, price: Decimal, fill_id: str) -> BrokerExecutionReport`
- 作用：Perform emit_fill.
- 直接原始调用：`ValueError` x3, `Decimal` x2, `fill_id.strip`, `self._report`
- 已解析到仓库内部的调用：`qts.execution.broker.FakeBrokerAdapter._report`
- 被以下仓库内部符号调用：无

#### `qts.execution.broker.FakeBrokerAdapter._report`
- 位置：`backend/src/qts/execution/broker.py:209`
- 类型：`method`
- 签名：`def _report(self, request: BrokerOrderRequest, *, broker_order_id: str, status: BrokerExecutionReportStatus, filled_quantity: Decimal=Decimal('0'), fill_price: Decimal | None=None, fill_id: str | None=None) -> BrokerExecutionReport`
- 作用：未写 docstring；静态推断为所属类上的 ` report` 行为。
- 直接原始调用：`BrokerExecutionReport`
- 已解析到仓库内部的调用：`qts.execution.broker.BrokerExecutionReport`
- 被以下仓库内部符号调用：`qts.execution.broker.FakeBrokerAdapter.cancel_order`, `qts.execution.broker.FakeBrokerAdapter.emit_fill`, `qts.execution.broker.FakeBrokerAdapter.submit_order`

#### `qts.execution.broker.normalize_broker_status`
- 位置：`backend/src/qts/execution/broker.py:235`
- 类型：`module_function`
- 签名：`def normalize_broker_status(status: BrokerExecutionReportStatus) -> ExecutionReportStatus`
- 作用：Map broker status to normalized execution status.
- 直接原始调用：`ExecutionReportStatus`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionAdapter.normalize_execution_report`, `qts.execution.broker.normalize_broker_execution_report`

#### `qts.execution.broker.normalize_broker_execution_report`
- 位置：`backend/src/qts/execution/broker.py:241`
- 类型：`module_function`
- 签名：`def normalize_broker_execution_report(report: BrokerExecutionReport) -> ExecutionReport`
- 作用：Convert broker-boundary report into the OrderManager report type.
- 直接原始调用：`ExecutionReport`, `normalize_broker_status`
- 已解析到仓库内部的调用：`qts.execution.broker.normalize_broker_status`
- 被以下仓库内部符号调用：`qts.application.commands.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill`

### `qts.execution.idempotency`

模块：`qts.execution.idempotency`

#### `qts.execution.idempotency.FillIdempotencyStore`
- 位置：`backend/src/qts/execution/idempotency.py:6`
- 类型：`class`
- 签名：`class FillIdempotencyStore`
- 作用：Tracks fill IDs that have already been applied.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.execution.order_manager.OrderManager.__init__`, `qts.runtime.actors.account_actor.AccountActor.__init__`

#### `qts.execution.idempotency.FillIdempotencyStore.__init__`
- 位置：`backend/src/qts/execution/idempotency.py:9`
- 类型：`method`
- 签名：`def __init__(self, seen: set[str] | None=None) -> None`
- 作用：Perform __init__.
- 直接原始调用：`set` x2
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.execution.idempotency.FillIdempotencyStore.mark_seen`
- 位置：`backend/src/qts/execution/idempotency.py:13`
- 类型：`method`
- 签名：`def mark_seen(self, fill_id: str) -> bool`
- 作用：Perform mark_seen.
- 直接原始调用：`ValueError`, `fill_id.strip`, `self._seen.add`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.execution.idempotency.FillIdempotencyStore.discard`
- 位置：`backend/src/qts/execution/idempotency.py:22`
- 类型：`method`
- 签名：`def discard(self, fill_id: str) -> None`
- 作用：Perform discard.
- 直接原始调用：`self._seen.discard`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.execution.idempotency.FillIdempotencyStore.snapshot`
- 位置：`backend/src/qts/execution/idempotency.py:26`
- 类型：`method`
- 签名：`def snapshot(self) -> tuple[str, ...]`
- 作用：Perform snapshot.
- 直接原始调用：`sorted`, `tuple`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.execution.idempotency.FillIdempotencyStore.restore`
- 位置：`backend/src/qts/execution/idempotency.py:31`
- 类型：`classmethod`
- 签名：`def restore(cls, seen: tuple[str, ...]) -> FillIdempotencyStore`
- 作用：Perform restore.
- 直接原始调用：`cls`, `set`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.execution.order_manager.OrderManager.restore`

### `qts.execution.order_manager`

模块：`qts.execution.order_manager`

#### `qts.execution.order_manager.OrderManager`
- 位置：`backend/src/qts/execution/order_manager.py:28`
- 类型：`class`
- 签名：`class OrderManager`
- 作用：Owns order lifecycle and normalized execution reports.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.application.commands.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill`, `qts.runtime.actors.order_manager_actor.OrderManagerActor.__init__`

#### `qts.execution.order_manager.OrderManager.__init__`
- 位置：`backend/src/qts/execution/order_manager.py:31`
- 类型：`method`
- 签名：`def __init__(self) -> None`
- 作用：Perform __init__.
- 直接原始调用：`FillIdempotencyStore`
- 已解析到仓库内部的调用：`qts.execution.idempotency.FillIdempotencyStore`
- 被以下仓库内部符号调用：无

#### `qts.execution.order_manager.OrderManager.create_order`
- 位置：`backend/src/qts/execution/order_manager.py:39`
- 类型：`method`
- 签名：`def create_order(self, intent: OrderIntent, *, risk_decision: RiskDecision) -> Order`
- 作用：Perform create_order.
- 直接原始调用：`Order`, `OrderStateMachine`, `ValueError`
- 已解析到仓库内部的调用：`qts.execution.order_state_machine.OrderStateMachine`
- 被以下仓库内部符号调用：无

#### `qts.execution.order_manager.OrderManager.mark_sent`
- 位置：`backend/src/qts/execution/order_manager.py:49`
- 类型：`method`
- 签名：`def mark_sent(self, order_id: OrderId, *, broker_order_id: str) -> Order`
- 作用：Perform mark_sent.
- 直接原始调用：`ValueError`, `broker_order_id.strip`, `machine.apply`, `self._replace_order`
- 已解析到仓库内部的调用：`qts.execution.order_manager.OrderManager._replace_order`
- 被以下仓库内部符号调用：无

#### `qts.execution.order_manager.OrderManager.request_cancel`
- 位置：`backend/src/qts/execution/order_manager.py:59`
- 类型：`method`
- 签名：`def request_cancel(self, intent: CancelIntent) -> Order`
- 作用：Perform request_cancel.
- 直接原始调用：`self._machines[intent.order_id].apply`, `self._replace_order`
- 已解析到仓库内部的调用：`qts.execution.order_manager.OrderManager._replace_order`
- 被以下仓库内部符号调用：无

#### `qts.execution.order_manager.OrderManager.request_replace`
- 位置：`backend/src/qts/execution/order_manager.py:64`
- 类型：`method`
- 签名：`def request_replace(self, intent: ReplaceIntent, *, risk_decision: RiskDecision) -> Order`
- 作用：Perform request_replace.
- 直接原始调用：`Order`, `OrderIntent`, `ValueError`, `self._machines[intent.order_id].apply`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.execution.order_manager.OrderManager.process_report`
- 位置：`backend/src/qts/execution/order_manager.py:85`
- 类型：`method`
- 签名：`def process_report(self, report: ExecutionReport) -> OrderManagerResult`
- 作用：Perform process_report.
- 直接原始调用：`OrderManagerResult`, `self._event_for_report`, `self._fills_for_report`, `self._machines[order_id].apply`, `self._replace_order`
- 已解析到仓库内部的调用：`qts.execution.order_manager.OrderManager._event_for_report`, `qts.execution.order_manager.OrderManager._replace_order`, `qts.execution.order_manager.OrderManager._fills_for_report`
- 被以下仓库内部符号调用：无

#### `qts.execution.order_manager.OrderManager.get_order`
- 位置：`backend/src/qts/execution/order_manager.py:93`
- 类型：`method`
- 签名：`def get_order(self, order_id: OrderId) -> Order`
- 作用：Perform get_order.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.execution.order_manager.OrderManager.discard_terminal_order`
- 位置：`backend/src/qts/execution/order_manager.py:97`
- 类型：`method`
- 签名：`def discard_terminal_order(self, order_id: OrderId) -> None`
- 作用：Perform discard_terminal_order.
- 直接原始调用：`ValueError`, `self._broker_to_order.pop`, `self._fill_ids.discard`, `self._fill_ids_by_order.pop`, `self._machines.pop`, `self._orders.pop`, `set`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.execution.order_manager.OrderManager.snapshot`
- 位置：`backend/src/qts/execution/order_manager.py:109`
- 类型：`method`
- 签名：`def snapshot(self) -> OrderManagerSnapshot`
- 作用：Perform snapshot.
- 直接原始调用：`tuple` x2, `OrderManagerSnapshot`, `self._broker_to_order.items`, `self._fill_ids.snapshot`, `self._orders.values`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.execution.order_manager.OrderManager.restore`
- 位置：`backend/src/qts/execution/order_manager.py:118`
- 类型：`classmethod`
- 签名：`def restore(cls, snapshot: OrderManagerSnapshot) -> OrderManager`
- 作用：Perform restore.
- 直接原始调用：`FillIdempotencyStore.restore`, `OrderStateMachine`, `cls`, `dict`
- 已解析到仓库内部的调用：`qts.execution.order_state_machine.OrderStateMachine`, `qts.execution.idempotency.FillIdempotencyStore.restore`
- 被以下仓库内部符号调用：无

#### `qts.execution.order_manager.OrderManager._replace_order`
- 位置：`backend/src/qts/execution/order_manager.py:130`
- 类型：`method`
- 签名：`def _replace_order(self, order_id: OrderId, *, state: OrderState, broker_order_id: str | None=None) -> Order`
- 作用：Perform _replace_order.
- 直接原始调用：`Order`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.execution.order_manager.OrderManager.mark_sent`, `qts.execution.order_manager.OrderManager.process_report`, `qts.execution.order_manager.OrderManager.request_cancel`

#### `qts.execution.order_manager.OrderManager._fills_for_report`
- 位置：`backend/src/qts/execution/order_manager.py:150`
- 类型：`method`
- 签名：`def _fills_for_report(self, order: Order, report: ExecutionReport) -> tuple[OrderFill, ...]`
- 作用：Perform _fills_for_report.
- 直接原始调用：`Decimal`, `OrderFill`, `ValueError`, `self._fill_ids.mark_seen`, `self._fill_ids_by_order.setdefault`, `self._fill_ids_by_order.setdefault.add`, `set`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.execution.order_manager.OrderManager.process_report`

#### `qts.execution.order_manager.OrderManager._event_for_report`
- 位置：`backend/src/qts/execution/order_manager.py:173`
- 类型：`staticmethod`
- 签名：`def _event_for_report(status: ExecutionReportStatus) -> OrderEvent`
- 作用：Perform _event_for_report.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.execution.order_manager.OrderManager.process_report`

### `qts.execution.order_state_machine`

模块：`qts.execution.order_state_machine`

#### `qts.execution.order_state_machine.OrderEvent`
- 位置：`backend/src/qts/execution/order_state_machine.py:11`
- 类型：`class`
- 签名：`class OrderEvent(StrEnum)`
- 作用：Order lifecycle transition inputs.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.execution.order_state_machine.OrderTransitionError`
- 位置：`backend/src/qts/execution/order_state_machine.py:24`
- 类型：`class`
- 签名：`class OrderTransitionError(ValueError)`
- 作用：Raised when an order transition is invalid.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.execution.order_state_machine.OrderStateMachine.apply`

#### `qts.execution.order_state_machine.OrderStateMachine`
- 位置：`backend/src/qts/execution/order_state_machine.py:81`
- 类型：`class`
- 签名：`class OrderStateMachine`
- 作用：Validate and apply order lifecycle transitions.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.execution.order_manager.OrderManager.create_order`, `qts.execution.order_manager.OrderManager.restore`

#### `qts.execution.order_state_machine.OrderStateMachine.apply`
- 位置：`backend/src/qts/execution/order_state_machine.py:86`
- 类型：`method`
- 签名：`def apply(self, event: OrderEvent) -> OrderState`
- 作用：Perform apply.
- 直接原始调用：`OrderTransitionError`, `_DUPLICATE_TERMINAL_EVENTS.get`, `_TRANSITIONS.get`, `_TRANSITIONS.get.get`
- 已解析到仓库内部的调用：`qts.execution.order_state_machine.OrderTransitionError`
- 被以下仓库内部符号调用：无

### `qts.execution.simulator.fill_model`

模块：`qts.execution.simulator.fill_model`

#### `qts.execution.simulator.fill_model.ImmediateFillModel`
- 位置：`backend/src/qts/execution/simulator/fill_model.py:10`
- 类型：`class`
- 签名：`class ImmediateFillModel`
- 作用：Fills market orders at the provided market price.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.execution.simulator.simulated_broker.SimulatedBroker.__init__`

#### `qts.execution.simulator.fill_model.ImmediateFillModel.fill`
- 位置：`backend/src/qts/execution/simulator/fill_model.py:13`
- 类型：`method`
- 签名：`def fill(self, intent: OrderIntent, *, broker_order_id: str, market_price: Decimal) -> ExecutionReport`
- 作用：Perform fill.
- 直接原始调用：`Decimal`, `ExecutionReport`, `ValueError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.execution.simulator.simulated_broker`

模块：`qts.execution.simulator.simulated_broker`

#### `qts.execution.simulator.simulated_broker.SimulatedBroker`
- 位置：`backend/src/qts/execution/simulator/simulated_broker.py:11`
- 类型：`class`
- 签名：`class SimulatedBroker`
- 作用：Broker simulator with no external dependency.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.actors.execution_actor.ExecutionActor.__init__`

#### `qts.execution.simulator.simulated_broker.SimulatedBroker.__init__`
- 位置：`backend/src/qts/execution/simulator/simulated_broker.py:14`
- 类型：`method`
- 签名：`def __init__(self, fill_model: ImmediateFillModel | None=None) -> None`
- 作用：Perform __init__.
- 直接原始调用：`ImmediateFillModel`
- 已解析到仓库内部的调用：`qts.execution.simulator.fill_model.ImmediateFillModel`
- 被以下仓库内部符号调用：无

#### `qts.execution.simulator.simulated_broker.SimulatedBroker.execute_market_order`
- 位置：`backend/src/qts/execution/simulator/simulated_broker.py:18`
- 类型：`method`
- 签名：`def execute_market_order(self, intent: OrderIntent, *, broker_order_id: str, market_price: Decimal) -> ExecutionReport`
- 作用：Perform execute_market_order.
- 直接原始调用：`self._fill_model.fill`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.factors.momentum`

模块：`qts.factors.momentum`

#### `qts.factors.momentum.FactorAsset`
- 位置：`backend/src/qts/factors/momentum.py:10`
- 类型：`class`
- 签名：`class FactorAsset(Protocol)`
- 作用：Minimal asset shape required by factor ranking.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.factors.momentum.FactorAsset.symbol`
- 位置：`backend/src/qts/factors/momentum.py:14`
- 类型：`property`
- 签名：`def symbol(self) -> str`
- 作用：Stable display symbol used for deterministic tie-breaking.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.factors.momentum.FactorScore`
- 位置：`backend/src/qts/factors/momentum.py:19`
- 类型：`class`
- 签名：`class FactorScore`
- 作用：Single asset factor score.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.factors.momentum.MomentumFactor.compute`

#### `qts.factors.momentum.FactorResult`
- 位置：`backend/src/qts/factors/momentum.py:27`
- 类型：`class`
- 签名：`class FactorResult`
- 作用：Ranked cross-sectional factor result.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.factors.momentum.MomentumFactor.compute`

#### `qts.factors.momentum.FactorResult.score`
- 位置：`backend/src/qts/factors/momentum.py:32`
- 类型：`method`
- 签名：`def score(self, asset: FactorAsset) -> Decimal`
- 作用：Perform score.
- 直接原始调用：`KeyError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.factors.momentum.MomentumFactor`
- 位置：`backend/src/qts/factors/momentum.py:41`
- 类型：`class`
- 签名：`class MomentumFactor`
- 作用：Compute simple period momentum as last / first - 1.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.strategy_sdk.factors.FactorFactory.momentum`

#### `qts.factors.momentum.MomentumFactor.__post_init__`
- 位置：`backend/src/qts/factors/momentum.py:46`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.factors.momentum.MomentumFactor.compute`
- 位置：`backend/src/qts/factors/momentum.py:51`
- 类型：`method`
- 签名：`def compute(self, prices: dict[FactorAsset, tuple[Decimal, ...]]) -> FactorResult`
- 作用：Perform compute.
- 直接原始调用：`tuple` x2, `FactorResult`, `FactorScore`, `prices.items`, `self._momentum`, `sorted`
- 已解析到仓库内部的调用：`qts.factors.momentum.FactorScore`, `qts.factors.momentum.MomentumFactor._momentum`, `qts.factors.momentum.FactorResult`
- 被以下仓库内部符号调用：无

#### `qts.factors.momentum.MomentumFactor._momentum`
- 位置：`backend/src/qts/factors/momentum.py:61`
- 类型：`staticmethod`
- 签名：`def _momentum(values: tuple[Decimal, ...], window: int) -> Decimal`
- 作用：Perform _momentum.
- 直接原始调用：`Decimal` x2, `ValueError` x2, `len`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.factors.momentum.MomentumFactor.compute`

### `qts.indicators.price.ema`

模块：`qts.indicators.price.ema`

#### `qts.indicators.price.ema.EMA`
- 位置：`backend/src/qts/indicators/price/ema.py:12`
- 类型：`class`
- 签名：`class EMA`
- 作用：Incremental EMA using SMA as the warmup seed.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.indicators.price.ema.EMA.__post_init__`
- 位置：`backend/src/qts/indicators/price/ema.py:19`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`RollingWindow[Decimal]`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.indicators.price.ema.EMA.ready`
- 位置：`backend/src/qts/indicators/price/ema.py:24`
- 类型：`property`
- 签名：`def ready(self) -> bool`
- 作用：Perform ready.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.indicators.price.ema.EMA.update`
- 位置：`backend/src/qts/indicators/price/ema.py:28`
- 类型：`method`
- 签名：`def update(self, price: Decimal) -> Decimal | None`
- 作用：Perform update.
- 直接原始调用：`Decimal` x4, `self._warmup.append`, `sum`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.indicators.price.sma`

模块：`qts.indicators.price.sma`

#### `qts.indicators.price.sma.SMA`
- 位置：`backend/src/qts/indicators/price/sma.py:12`
- 类型：`class`
- 签名：`class SMA`
- 作用：Incremental simple moving average.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.strategy_sdk.indicators.IndicatorFactory.sma`

#### `qts.indicators.price.sma.SMA.__post_init__`
- 位置：`backend/src/qts/indicators/price/sma.py:19`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`RollingWindow[Decimal]`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.indicators.price.sma.SMA.ready`
- 位置：`backend/src/qts/indicators/price/sma.py:24`
- 类型：`property`
- 签名：`def ready(self) -> bool`
- 作用：Perform ready.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.indicators.price.sma.SMA.update`
- 位置：`backend/src/qts/indicators/price/sma.py:28`
- 类型：`method`
- 签名：`def update(self, price: Decimal) -> Decimal | None`
- 作用：Perform update.
- 直接原始调用：`Decimal` x2, `self._values.append`, `sum`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.indicators.rolling`

模块：`qts.indicators.rolling`

#### `qts.indicators.rolling.RollingWindow`
- 位置：`backend/src/qts/indicators/rolling.py:14`
- 类型：`class`
- 签名：`class RollingWindow(Generic[T])`
- 作用：Bounded FIFO buffer with warmup state.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.indicators.rolling.RollingWindow.__post_init__`
- 位置：`backend/src/qts/indicators/rolling.py:20`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError`, `deque`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.indicators.rolling.RollingWindow.ready`
- 位置：`backend/src/qts/indicators/rolling.py:27`
- 类型：`property`
- 签名：`def ready(self) -> bool`
- 作用：Perform ready.
- 直接原始调用：`len`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.indicators.rolling.RollingWindow.append`
- 位置：`backend/src/qts/indicators/rolling.py:31`
- 类型：`method`
- 签名：`def append(self, value: T) -> None`
- 作用：Perform append.
- 直接原始调用：`self._values.append`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.indicators.rolling.RollingWindow.snapshot`
- 位置：`backend/src/qts/indicators/rolling.py:35`
- 类型：`method`
- 签名：`def snapshot(self) -> tuple[T, ...]`
- 作用：Perform snapshot.
- 直接原始调用：`tuple`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.indicators.rolling.RollingWindow.restore`
- 位置：`backend/src/qts/indicators/rolling.py:39`
- 类型：`method`
- 签名：`def restore(self, values: Iterable[T]) -> RollingWindow[T]`
- 作用：Perform restore.
- 直接原始调用：`RollingWindow[T]`, `restored.append`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.indicators.rolling.RollingWindow.__iter__`
- 位置：`backend/src/qts/indicators/rolling.py:46`
- 类型：`method`
- 签名：`def __iter__(self) -> Iterator[T]`
- 作用：Perform __iter__.
- 直接原始调用：`iter`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.indicators.rolling.RollingWindow.__len__`
- 位置：`backend/src/qts/indicators/rolling.py:50`
- 类型：`method`
- 签名：`def __len__(self) -> int`
- 作用：Perform __len__.
- 直接原始调用：`len`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.load.bootstrap`

模块：`qts.load.bootstrap`

#### `qts.load.bootstrap.bootstrap_local`
- 位置：`backend/src/qts/load/bootstrap.py:8`
- 类型：`module_function`
- 签名：`def bootstrap_local(root: Path) -> dict[str, str]`
- 作用：Create local runtime directories and marker files safely.
- 直接原始调用：`str` x4, `data_dir.mkdir`, `logs_dir.mkdir`, `marker.write_text`, `root.mkdir`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`scripts.bootstrap.main`

### `qts.load.synthetic_market_data`

模块：`qts.load.synthetic_market_data`

#### `qts.load.synthetic_market_data.SyntheticMarketDataConfig`
- 位置：`backend/src/qts/load/synthetic_market_data.py:14`
- 类型：`class`
- 签名：`class SyntheticMarketDataConfig`
- 作用：Configuration for deterministic synthetic market data.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`scripts.run_load.main`

#### `qts.load.synthetic_market_data.SyntheticMarketDataConfig.__post_init__`
- 位置：`backend/src/qts/load/synthetic_market_data.py:25`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：未写 docstring；静态推断为所属类上的 `  post init  ` 行为。
- 直接原始调用：`ValueError` x3, `self.session_id.strip`, `self.timeframe.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.load.synthetic_market_data.generate_bars`
- 位置：`backend/src/qts/load/synthetic_market_data.py:34`
- 类型：`module_function`
- 签名：`def generate_bars(config: SyntheticMarketDataConfig) -> tuple[Bar, ...]`
- 作用：Perform generate_bars.
- 直接原始调用：`timedelta` x2, `Bar`, `Decimal`, `bars.append`, `max`, `min`, `range`, `tuple`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`scripts.run_load.main`

### `qts.observability.audit`

模块：`qts.observability.audit`

#### `qts.observability.audit.AuditEvent`
- 位置：`backend/src/qts/observability/audit.py:10`
- 类型：`class`
- 签名：`class AuditEvent`
- 作用：Operational or trading audit event.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.observability.audit.AuditEvent.__post_init__`
- 位置：`backend/src/qts/observability/audit.py:19`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError` x3, `self.actor.strip`, `self.event_type.strip`, `self.message.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.observability.logging`

模块：`qts.observability.logging`

#### `qts.observability.logging.build_log_record`
- 位置：`backend/src/qts/observability/logging.py:14`
- 类型：`module_function`
- 签名：`def build_log_record(*, level: str, message: str, metadata: EventMetadata | None=None, fields: Mapping[str, object] | None=None) -> dict[str, object]`
- 作用：Build a structured log record without exposing secret values.
- 直接原始调用：`ValueError` x3, `_is_secret_key`, `_metadata_fields`, `fields.items`, `key.strip`, `level.strip`, `message.strip`, `record.update`
- 已解析到仓库内部的调用：`qts.observability.logging._metadata_fields`, `qts.observability.logging._is_secret_key`
- 被以下仓库内部符号调用：无

#### `qts.observability.logging._metadata_fields`
- 位置：`backend/src/qts/observability/logging.py:42`
- 类型：`module_function`
- 签名：`def _metadata_fields(metadata: EventMetadata) -> dict[str, object]`
- 作用：Perform _metadata_fields.
- 直接原始调用：`str` x2, `metadata.bar_time.isoformat`, `metadata.event_time.isoformat`, `optional.items`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.observability.logging.build_log_record`

#### `qts.observability.logging._is_secret_key`
- 位置：`backend/src/qts/observability/logging.py:68`
- 类型：`module_function`
- 签名：`def _is_secret_key(key: str) -> bool`
- 作用：Perform _is_secret_key.
- 直接原始调用：`any`, `key.lower`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.observability.logging.build_log_record`

### `qts.observability.metrics`

模块：`qts.observability.metrics`

#### `qts.observability.metrics.MetricsRegistry`
- 位置：`backend/src/qts/observability/metrics.py:10`
- 类型：`class`
- 签名：`class MetricsRegistry`
- 作用：Record counters and gauges with deterministic key formatting.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.observability.metrics.MetricsRegistry.__init__`
- 位置：`backend/src/qts/observability/metrics.py:13`
- 类型：`method`
- 签名：`def __init__(self) -> None`
- 作用：Perform __init__.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.observability.metrics.MetricsRegistry.increment`
- 位置：`backend/src/qts/observability/metrics.py:17`
- 类型：`method`
- 签名：`def increment(self, name: str, *, amount: int=1, tags: Mapping[str, str] | None=None) -> None`
- 作用：Perform increment.
- 直接原始调用：`int`, `self._metric_key`, `self._values.get`
- 已解析到仓库内部的调用：`qts.observability.metrics.MetricsRegistry._metric_key`
- 被以下仓库内部符号调用：无

#### `qts.observability.metrics.MetricsRegistry.gauge`
- 位置：`backend/src/qts/observability/metrics.py:28`
- 类型：`method`
- 签名：`def gauge(self, name: str, value: int | float, *, tags: Mapping[str, str] | None=None) -> None`
- 作用：Perform gauge.
- 直接原始调用：`self._metric_key`
- 已解析到仓库内部的调用：`qts.observability.metrics.MetricsRegistry._metric_key`
- 被以下仓库内部符号调用：`qts.observability.metrics.MetricsRegistry.observe_queue`

#### `qts.observability.metrics.MetricsRegistry.observe_queue`
- 位置：`backend/src/qts/observability/metrics.py:34`
- 类型：`method`
- 签名：`def observe_queue(self, name: str, mailbox: Mailbox, *, oldest_message_lag_seconds: float) -> None`
- 作用：Perform observe_queue.
- 直接原始调用：`self.gauge` x2
- 已解析到仓库内部的调用：`qts.observability.metrics.MetricsRegistry.gauge`
- 被以下仓库内部符号调用：无

#### `qts.observability.metrics.MetricsRegistry.snapshot`
- 位置：`backend/src/qts/observability/metrics.py:49`
- 类型：`method`
- 签名：`def snapshot(self) -> dict[str, int | float]`
- 作用：Perform snapshot.
- 直接原始调用：`dict`, `self._values.items`, `sorted`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.observability.metrics.MetricsRegistry._metric_key`
- 位置：`backend/src/qts/observability/metrics.py:54`
- 类型：`staticmethod`
- 签名：`def _metric_key(name: str, tags: Mapping[str, str] | None) -> str`
- 作用：Perform _metric_key.
- 直接原始调用：`','.join`, `ValueError`, `name.strip`, `sorted`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.observability.metrics.MetricsRegistry.gauge`, `qts.observability.metrics.MetricsRegistry.increment`

### `qts.portfolio.accounting.fill_accounting`

模块：`qts.portfolio.accounting.fill_accounting`

#### `qts.portfolio.accounting.fill_accounting.TradeSide`
- 位置：`backend/src/qts/portfolio/accounting/fill_accounting.py:14`
- 类型：`class`
- 签名：`class TradeSide(StrEnum)`
- 作用：Fill side.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.portfolio.accounting.fill_accounting.Fill`
- 位置：`backend/src/qts/portfolio/accounting/fill_accounting.py:22`
- 类型：`class`
- 签名：`class Fill`
- 作用：Executed fill used by accounting.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.portfolio.accounting.fill_accounting.Fill.__post_init__`
- 位置：`backend/src/qts/portfolio/accounting/fill_accounting.py:33`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError` x4, `Decimal` x3, `self.currency.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.portfolio.accounting.fill_accounting.FillAccounting`
- 位置：`backend/src/qts/portfolio/accounting/fill_accounting.py:45`
- 类型：`class`
- 签名：`class FillAccounting`
- 作用：Fill accounting operations.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.portfolio.accounting.fill_accounting.FillAccounting.apply`
- 位置：`backend/src/qts/portfolio/accounting/fill_accounting.py:49`
- 类型：`staticmethod`
- 签名：`def apply(fill: Fill, *, cash_book: CashBook, position_book: PositionBook) -> None`
- 作用：Perform apply.
- 直接原始调用：`cash_book.apply_delta`, `position_book.apply_delta`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.portfolio.cash_book`

模块：`qts.portfolio.cash_book`

#### `qts.portfolio.cash_book.CashBook`
- 位置：`backend/src/qts/portfolio/cash_book.py:11`
- 类型：`class`
- 签名：`class CashBook`
- 作用：Mutable cash balance book intended to be owned by AccountActor later.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.actors.account_actor.AccountActor.__init__`

#### `qts.portfolio.cash_book.CashBook.__init__`
- 位置：`backend/src/qts/portfolio/cash_book.py:14`
- 类型：`method`
- 签名：`def __init__(self, balances: Mapping[str, Decimal] | None=None) -> None`
- 作用：Perform __init__.
- 直接原始调用：`dict`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.portfolio.cash_book.CashBook.apply_delta`
- 位置：`backend/src/qts/portfolio/cash_book.py:18`
- 类型：`method`
- 签名：`def apply_delta(self, currency: str, amount_delta: Decimal) -> None`
- 作用：Perform apply_delta.
- 直接原始调用：`self._normalize_currency`, `self.balance`
- 已解析到仓库内部的调用：`qts.portfolio.cash_book.CashBook._normalize_currency`, `qts.portfolio.cash_book.CashBook.balance`
- 被以下仓库内部符号调用：无

#### `qts.portfolio.cash_book.CashBook.balance`
- 位置：`backend/src/qts/portfolio/cash_book.py:23`
- 类型：`method`
- 签名：`def balance(self, currency: str) -> Decimal`
- 作用：Perform balance.
- 直接原始调用：`Decimal`, `self._balances.get`, `self._normalize_currency`
- 已解析到仓库内部的调用：`qts.portfolio.cash_book.CashBook._normalize_currency`
- 被以下仓库内部符号调用：`qts.portfolio.cash_book.CashBook.apply_delta`, `qts.portfolio.cash_book.CashBook.available`

#### `qts.portfolio.cash_book.CashBook.available`
- 位置：`backend/src/qts/portfolio/cash_book.py:27`
- 类型：`method`
- 签名：`def available(self, currency: str, *, reservations: ReservationBook) -> Decimal`
- 作用：Perform available.
- 直接原始调用：`reservations.reserved`, `self._normalize_currency`, `self.balance`
- 已解析到仓库内部的调用：`qts.portfolio.cash_book.CashBook._normalize_currency`, `qts.portfolio.cash_book.CashBook.balance`
- 被以下仓库内部符号调用：无

#### `qts.portfolio.cash_book.CashBook._normalize_currency`
- 位置：`backend/src/qts/portfolio/cash_book.py:33`
- 类型：`staticmethod`
- 签名：`def _normalize_currency(currency: str) -> str`
- 作用：Perform _normalize_currency.
- 直接原始调用：`ValueError`, `currency.strip`, `currency.strip.upper`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.portfolio.cash_book.CashBook.apply_delta`, `qts.portfolio.cash_book.CashBook.available`, `qts.portfolio.cash_book.CashBook.balance`

### `qts.portfolio.position_book`

模块：`qts.portfolio.position_book`

#### `qts.portfolio.position_book.Position`
- 位置：`backend/src/qts/portfolio/position_book.py:14`
- 类型：`class`
- 签名：`class Position`
- 作用：Immutable position snapshot.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.intent_processor.BacktestIntentProcessor.process_intent`, `qts.portfolio.position_book.PositionBook.snapshot`

#### `qts.portfolio.position_book.PositionBook`
- 位置：`backend/src/qts/portfolio/position_book.py:21`
- 类型：`class`
- 签名：`class PositionBook`
- 作用：Mutable position book intended to be owned by AccountActor later.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.actors.account_actor.AccountActor.__init__`

#### `qts.portfolio.position_book.PositionBook.__init__`
- 位置：`backend/src/qts/portfolio/position_book.py:24`
- 类型：`method`
- 签名：`def __init__(self, positions: Mapping[InstrumentId, Decimal] | None=None) -> None`
- 作用：Perform __init__.
- 直接原始调用：`dict`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.portfolio.position_book.PositionBook.apply_delta`
- 位置：`backend/src/qts/portfolio/position_book.py:28`
- 类型：`method`
- 签名：`def apply_delta(self, instrument_id: InstrumentId, quantity_delta: Decimal) -> None`
- 作用：Perform apply_delta.
- 直接原始调用：`self.quantity`
- 已解析到仓库内部的调用：`qts.portfolio.position_book.PositionBook.quantity`
- 被以下仓库内部符号调用：无

#### `qts.portfolio.position_book.PositionBook.quantity`
- 位置：`backend/src/qts/portfolio/position_book.py:32`
- 类型：`method`
- 签名：`def quantity(self, instrument_id: InstrumentId) -> Decimal`
- 作用：Perform quantity.
- 直接原始调用：`Decimal`, `self._positions.get`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.portfolio.position_book.PositionBook.apply_delta`

#### `qts.portfolio.position_book.PositionBook.snapshot`
- 位置：`backend/src/qts/portfolio/position_book.py:36`
- 类型：`method`
- 签名：`def snapshot(self) -> Mapping[InstrumentId, Position]`
- 作用：Perform snapshot.
- 直接原始调用：`MappingProxyType`, `Position`, `self._positions.items`
- 已解析到仓库内部的调用：`qts.portfolio.position_book.Position`
- 被以下仓库内部符号调用：无

### `qts.portfolio.reservation_book`

模块：`qts.portfolio.reservation_book`

#### `qts.portfolio.reservation_book.Reservation`
- 位置：`backend/src/qts/portfolio/reservation_book.py:12`
- 类型：`class`
- 签名：`class Reservation`
- 作用：Cash reservation by order ID.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.portfolio.reservation_book.ReservationBook.reserve`

#### `qts.portfolio.reservation_book.ReservationBook`
- 位置：`backend/src/qts/portfolio/reservation_book.py:20`
- 类型：`class`
- 签名：`class ReservationBook`
- 作用：Idempotent cash reservations keyed by order ID.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.portfolio.reservation_book.ReservationBook.__init__`
- 位置：`backend/src/qts/portfolio/reservation_book.py:23`
- 类型：`method`
- 签名：`def __init__(self) -> None`
- 作用：Perform __init__.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.portfolio.reservation_book.ReservationBook.reserve`
- 位置：`backend/src/qts/portfolio/reservation_book.py:27`
- 类型：`method`
- 签名：`def reserve(self, reservation_id: OrderId, currency: str, amount: Decimal) -> None`
- 作用：Perform reserve.
- 直接原始调用：`Decimal`, `Reservation`, `ValueError`, `self._normalize_currency`
- 已解析到仓库内部的调用：`qts.portfolio.reservation_book.ReservationBook._normalize_currency`, `qts.portfolio.reservation_book.Reservation`
- 被以下仓库内部符号调用：无

#### `qts.portfolio.reservation_book.ReservationBook.release`
- 位置：`backend/src/qts/portfolio/reservation_book.py:40`
- 类型：`method`
- 签名：`def release(self, reservation_id: OrderId) -> None`
- 作用：Perform release.
- 直接原始调用：`self._reservations.pop`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.portfolio.reservation_book.ReservationBook.reserved`
- 位置：`backend/src/qts/portfolio/reservation_book.py:44`
- 类型：`method`
- 签名：`def reserved(self, currency: str) -> Decimal`
- 作用：Perform reserved.
- 直接原始调用：`Decimal`, `self._normalize_currency`, `self._reservations.values`, `sum`
- 已解析到仓库内部的调用：`qts.portfolio.reservation_book.ReservationBook._normalize_currency`
- 被以下仓库内部符号调用：无

#### `qts.portfolio.reservation_book.ReservationBook._normalize_currency`
- 位置：`backend/src/qts/portfolio/reservation_book.py:57`
- 类型：`staticmethod`
- 签名：`def _normalize_currency(currency: str) -> str`
- 作用：Perform _normalize_currency.
- 直接原始调用：`ValueError`, `currency.strip`, `currency.strip.upper`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.portfolio.reservation_book.ReservationBook.reserve`, `qts.portfolio.reservation_book.ReservationBook.reserved`

### `qts.portfolio.valuation.models`

模块：`qts.portfolio.valuation.models`

#### `qts.portfolio.valuation.models.equity_notional`
- 位置：`backend/src/qts/portfolio/valuation/models.py:8`
- 类型：`module_function`
- 签名：`def equity_notional(*, quantity: Decimal, price: Decimal) -> Decimal`
- 作用：Perform equity_notional.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.portfolio.valuation.models.future_pnl`
- 位置：`backend/src/qts/portfolio/valuation/models.py:13`
- 类型：`module_function`
- 签名：`def future_pnl(*, contracts: Decimal, entry_price: Decimal, exit_price: Decimal, multiplier: Decimal) -> Decimal`
- 作用：Perform future_pnl.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.portfolio.valuation.models.option_premium_value`
- 位置：`backend/src/qts/portfolio/valuation/models.py:24`
- 类型：`module_function`
- 签名：`def option_premium_value(*, contracts: Decimal, option_price: Decimal, multiplier: Decimal) -> Decimal`
- 作用：Perform option_premium_value.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.quality.guardrails`

模块：`qts.quality.guardrails`

#### `qts.quality.guardrails.GuardrailViolation`
- 位置：`backend/src/qts/quality/guardrails.py:110`
- 类型：`class`
- 签名：`class GuardrailViolation`
- 作用：One architecture or domain-boundary guardrail violation.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.quality.guardrails._check_backtest_engine_cohesion`, `qts.quality.guardrails._check_backtest_input_cohesion`, `qts.quality.guardrails._check_backtest_runner_cohesion`, `qts.quality.guardrails._check_forbidden_tokens`, `qts.quality.guardrails._check_import`, `qts.quality.guardrails._check_oop_helper_ownership`, `qts.quality.guardrails._check_oop_public_factory_functions`, `qts.quality.guardrails._check_shared_capability_placement`, `qts.quality.guardrails._check_test_support_code`

#### `qts.quality.guardrails.GuardrailViolation.format`
- 位置：`backend/src/qts/quality/guardrails.py:118`
- 类型：`method`
- 签名：`def format(self) -> str`
- 作用：Perform format.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.quality.guardrails.Rule`
- 位置：`backend/src/qts/quality/guardrails.py:123`
- 类型：`class`
- 签名：`class Rule(Protocol)`
- 作用：Pluggable guardrail rule interface.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.quality.guardrails.Rule.check`
- 位置：`backend/src/qts/quality/guardrails.py:128`
- 类型：`method`
- 签名：`def check(self, *, relative_path: Path, qts_relative_path: Path, tree: ast.AST) -> list[GuardrailViolation]`
- 作用：Perform check.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.quality.guardrails.ImportBoundaryRule`
- 位置：`backend/src/qts/quality/guardrails.py:142`
- 类型：`class`
- 签名：`class ImportBoundaryRule`
- 作用：Validate package import boundary direction and adapter constraints.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.quality.guardrails.GuardrailSuite.__init__`

#### `qts.quality.guardrails.ImportBoundaryRule.check`
- 位置：`backend/src/qts/quality/guardrails.py:147`
- 类型：`method`
- 签名：`def check(self, *, relative_path: Path, qts_relative_path: Path, tree: ast.AST) -> list[GuardrailViolation]`
- 作用：Perform check.
- 直接原始调用：`_check_import`, `_iter_imports`, `violations.extend`
- 已解析到仓库内部的调用：`qts.quality.guardrails._iter_imports`, `qts.quality.guardrails._check_import`
- 被以下仓库内部符号调用：无

#### `qts.quality.guardrails.ProductSpecificRule`
- 位置：`backend/src/qts/quality/guardrails.py:163`
- 类型：`class`
- 签名：`class ProductSpecificRule`
- 作用：Reject product hard-coding outside documented locations.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.quality.guardrails.GuardrailSuite.__init__`

#### `qts.quality.guardrails.ProductSpecificRule.check`
- 位置：`backend/src/qts/quality/guardrails.py:168`
- 类型：`method`
- 签名：`def check(self, *, relative_path: Path, qts_relative_path: Path, tree: ast.AST) -> list[GuardrailViolation]`
- 作用：Perform check.
- 直接原始调用：`_check_product_specific_code`, `_has_allowed_prefix`
- 已解析到仓库内部的调用：`qts.quality.guardrails._has_allowed_prefix`, `qts.quality.guardrails._check_product_specific_code`
- 被以下仓库内部符号调用：无

#### `qts.quality.guardrails.BrokerSpecificRule`
- 位置：`backend/src/qts/quality/guardrails.py:181`
- 类型：`class`
- 签名：`class BrokerSpecificRule`
- 作用：Reject broker hard-coding outside broker boundaries.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.quality.guardrails.GuardrailSuite.__init__`

#### `qts.quality.guardrails.BrokerSpecificRule.check`
- 位置：`backend/src/qts/quality/guardrails.py:186`
- 类型：`method`
- 签名：`def check(self, *, relative_path: Path, qts_relative_path: Path, tree: ast.AST) -> list[GuardrailViolation]`
- 作用：Perform check.
- 直接原始调用：`_check_broker_specific_code`, `_has_allowed_prefix`
- 已解析到仓库内部的调用：`qts.quality.guardrails._has_allowed_prefix`, `qts.quality.guardrails._check_broker_specific_code`
- 被以下仓库内部符号调用：无

#### `qts.quality.guardrails.TestSupportRule`
- 位置：`backend/src/qts/quality/guardrails.py:199`
- 类型：`class`
- 签名：`class TestSupportRule`
- 作用：Reject test/anchor support in production source.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.quality.guardrails.GuardrailSuite.__init__`

#### `qts.quality.guardrails.TestSupportRule.check`
- 位置：`backend/src/qts/quality/guardrails.py:204`
- 类型：`method`
- 签名：`def check(self, *, relative_path: Path, qts_relative_path: Path, tree: ast.AST) -> list[GuardrailViolation]`
- 作用：Perform check.
- 直接原始调用：`_check_test_support_code`
- 已解析到仓库内部的调用：`qts.quality.guardrails._check_test_support_code`
- 被以下仓库内部符号调用：无

#### `qts.quality.guardrails.SharedCapabilityRule`
- 位置：`backend/src/qts/quality/guardrails.py:215`
- 类型：`class`
- 签名：`class SharedCapabilityRule`
- 作用：Reject shared capability semantics in source-specific modules.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.quality.guardrails.GuardrailSuite.__init__`

#### `qts.quality.guardrails.SharedCapabilityRule.check`
- 位置：`backend/src/qts/quality/guardrails.py:220`
- 类型：`method`
- 签名：`def check(self, *, relative_path: Path, qts_relative_path: Path, tree: ast.AST) -> list[GuardrailViolation]`
- 作用：Perform check.
- 直接原始调用：`_check_shared_capability_placement`
- 已解析到仓库内部的调用：`qts.quality.guardrails._check_shared_capability_placement`
- 被以下仓库内部符号调用：无

#### `qts.quality.guardrails.OOPPublicFactoryRule`
- 位置：`backend/src/qts/quality/guardrails.py:231`
- 类型：`class`
- 签名：`class OOPPublicFactoryRule`
- 作用：Reject module-level public factory names on stable concepts.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.quality.guardrails.GuardrailSuite.__init__`

#### `qts.quality.guardrails.OOPPublicFactoryRule.check`
- 位置：`backend/src/qts/quality/guardrails.py:236`
- 类型：`method`
- 签名：`def check(self, *, relative_path: Path, qts_relative_path: Path, tree: ast.AST) -> list[GuardrailViolation]`
- 作用：Perform check.
- 直接原始调用：`_check_oop_public_factory_functions`
- 已解析到仓库内部的调用：`qts.quality.guardrails._check_oop_public_factory_functions`
- 被以下仓库内部符号调用：无

#### `qts.quality.guardrails.OOPHelperOwnershipRule`
- 位置：`backend/src/qts/quality/guardrails.py:247`
- 类型：`class`
- 签名：`class OOPHelperOwnershipRule`
- 作用：Reject helper ownership violations that should stay private.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.quality.guardrails.GuardrailSuite.__init__`

#### `qts.quality.guardrails.OOPHelperOwnershipRule.check`
- 位置：`backend/src/qts/quality/guardrails.py:252`
- 类型：`method`
- 签名：`def check(self, *, relative_path: Path, qts_relative_path: Path, tree: ast.AST) -> list[GuardrailViolation]`
- 作用：Perform check.
- 直接原始调用：`_check_oop_helper_ownership`
- 已解析到仓库内部的调用：`qts.quality.guardrails._check_oop_helper_ownership`
- 被以下仓库内部符号调用：无

#### `qts.quality.guardrails.BacktestRunnerCohesionRule`
- 位置：`backend/src/qts/quality/guardrails.py:263`
- 类型：`class`
- 签名：`class BacktestRunnerCohesionRule`
- 作用：Reject replay input assembly inside backtest runner.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.quality.guardrails.GuardrailSuite.__init__`

#### `qts.quality.guardrails.BacktestRunnerCohesionRule.check`
- 位置：`backend/src/qts/quality/guardrails.py:268`
- 类型：`method`
- 签名：`def check(self, *, relative_path: Path, qts_relative_path: Path, tree: ast.AST) -> list[GuardrailViolation]`
- 作用：Perform check.
- 直接原始调用：`_check_backtest_runner_cohesion`
- 已解析到仓库内部的调用：`qts.quality.guardrails._check_backtest_runner_cohesion`
- 被以下仓库内部符号调用：无

#### `qts.quality.guardrails.BacktestInputCohesionRule`
- 位置：`backend/src/qts/quality/guardrails.py:279`
- 类型：`class`
- 签名：`class BacktestInputCohesionRule`
- 作用：Reject catalog/data construction inside backtest input builder.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.quality.guardrails.GuardrailSuite.__init__`

#### `qts.quality.guardrails.BacktestInputCohesionRule.check`
- 位置：`backend/src/qts/quality/guardrails.py:284`
- 类型：`method`
- 签名：`def check(self, *, relative_path: Path, qts_relative_path: Path, tree: ast.AST) -> list[GuardrailViolation]`
- 作用：Perform check.
- 直接原始调用：`_check_backtest_input_cohesion`
- 已解析到仓库内部的调用：`qts.quality.guardrails._check_backtest_input_cohesion`
- 被以下仓库内部符号调用：无

#### `qts.quality.guardrails.BacktestEngineCohesionRule`
- 位置：`backend/src/qts/quality/guardrails.py:295`
- 类型：`class`
- 签名：`class BacktestEngineCohesionRule`
- 作用：Reject historical replay assembly inside backtest engine.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.quality.guardrails.GuardrailSuite.__init__`

#### `qts.quality.guardrails.BacktestEngineCohesionRule.check`
- 位置：`backend/src/qts/quality/guardrails.py:300`
- 类型：`method`
- 签名：`def check(self, *, relative_path: Path, qts_relative_path: Path, tree: ast.AST) -> list[GuardrailViolation]`
- 作用：Perform check.
- 直接原始调用：`_check_backtest_engine_cohesion`
- 已解析到仓库内部的调用：`qts.quality.guardrails._check_backtest_engine_cohesion`
- 被以下仓库内部符号调用：无

#### `qts.quality.guardrails.GuardrailSuite`
- 位置：`backend/src/qts/quality/guardrails.py:311`
- 类型：`class`
- 签名：`class GuardrailSuite`
- 作用：Execute a configured set of guardrail rules against Python files.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.quality.guardrails._check_python_file`, `qts.quality.guardrails.run_guardrails`

#### `qts.quality.guardrails.GuardrailSuite.__init__`
- 位置：`backend/src/qts/quality/guardrails.py:314`
- 类型：`method`
- 签名：`def __init__(self, rules: tuple[Rule, ...] | None=None) -> None`
- 作用：未写 docstring；静态推断为所属类上的 `  init  ` 行为。
- 直接原始调用：`BacktestEngineCohesionRule`, `BacktestInputCohesionRule`, `BacktestRunnerCohesionRule`, `BrokerSpecificRule`, `ImportBoundaryRule`, `OOPHelperOwnershipRule`, `OOPPublicFactoryRule`, `ProductSpecificRule`, `SharedCapabilityRule`, `TestSupportRule`
- 已解析到仓库内部的调用：`qts.quality.guardrails.ImportBoundaryRule`, `qts.quality.guardrails.ProductSpecificRule`, `qts.quality.guardrails.BrokerSpecificRule`, `qts.quality.guardrails.TestSupportRule`, `qts.quality.guardrails.SharedCapabilityRule`, `qts.quality.guardrails.OOPPublicFactoryRule`, `qts.quality.guardrails.OOPHelperOwnershipRule`, `qts.quality.guardrails.BacktestRunnerCohesionRule`, `qts.quality.guardrails.BacktestInputCohesionRule`, `qts.quality.guardrails.BacktestEngineCohesionRule`
- 被以下仓库内部符号调用：无

#### `qts.quality.guardrails.GuardrailSuite.check_file`
- 位置：`backend/src/qts/quality/guardrails.py:328`
- 类型：`method`
- 签名：`def check_file(self, *, relative_path: Path, qts_relative_path: Path, tree: ast.AST) -> list[GuardrailViolation]`
- 作用：Perform check_file.
- 直接原始调用：`rule.check`, `violations.extend`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.quality.guardrails._check_python_file`

#### `qts.quality.guardrails.GuardrailSuite.check`
- 位置：`backend/src/qts/quality/guardrails.py:347`
- 类型：`method`
- 签名：`def check(self, repo_root: Path) -> list[GuardrailViolation]`
- 作用：Perform check.
- 直接原始调用：`sorted` x2, `_check_python_file`, `source_root.exists`, `source_root.rglob`, `violations.extend`
- 已解析到仓库内部的调用：`qts.quality.guardrails._check_python_file`
- 被以下仓库内部符号调用：`qts.quality.guardrails.run_guardrails`

#### `qts.quality.guardrails.run_guardrails`
- 位置：`backend/src/qts/quality/guardrails.py:361`
- 类型：`module_function`
- 签名：`def run_guardrails(repo_root: Path) -> list[GuardrailViolation]`
- 作用：Return all guardrail violations under the repository root.
- 直接原始调用：`GuardrailSuite`, `GuardrailSuite.check`
- 已解析到仓库内部的调用：`qts.quality.guardrails.GuardrailSuite.check`, `qts.quality.guardrails.GuardrailSuite`
- 被以下仓库内部符号调用：`qts.quality.guardrails.main`

#### `qts.quality.guardrails._check_python_file`
- 位置：`backend/src/qts/quality/guardrails.py:366`
- 类型：`module_function`
- 签名：`def _check_python_file(repo_root: Path, path: Path) -> list[GuardrailViolation]`
- 作用：未写 docstring；静态推断为 ` check python file` 函数，具体语义以实现为准。
- 直接原始调用：`path.relative_to` x2, `GuardrailSuite`, `GuardrailSuite.check_file`, `ast.parse`, `path.read_text`, `str`
- 已解析到仓库内部的调用：`qts.quality.guardrails.GuardrailSuite.check_file`, `qts.quality.guardrails.GuardrailSuite`
- 被以下仓库内部符号调用：`qts.quality.guardrails.GuardrailSuite.check`

#### `qts.quality.guardrails._check_import`
- 位置：`backend/src/qts/quality/guardrails.py:378`
- 类型：`module_function`
- 签名：`def _check_import(relative_path: Path, qts_relative_path: Path, imported_module: str, line: int) -> list[GuardrailViolation]`
- 作用：未写 docstring；静态推断为 ` check import` 函数，具体语义以实现为准。
- 直接原始调用：`GuardrailViolation` x3, `str` x3, `_is_forbidden_adapter_dependency`, `_is_forbidden_broker_adapter_dependency`, `_is_forbidden_dependency`, `imported_module.split`, `imported_module.startswith`, `len`
- 已解析到仓库内部的调用：`qts.quality.guardrails._is_forbidden_broker_adapter_dependency`, `qts.quality.guardrails.GuardrailViolation`, `qts.quality.guardrails._is_forbidden_dependency`, `qts.quality.guardrails._is_forbidden_adapter_dependency`
- 被以下仓库内部符号调用：`qts.quality.guardrails.ImportBoundaryRule.check`

#### `qts.quality.guardrails._is_forbidden_dependency`
- 位置：`backend/src/qts/quality/guardrails.py:425`
- 类型：`module_function`
- 签名：`def _is_forbidden_dependency(source_layer: str, imported_module: str, imported_layer: str) -> bool`
- 作用：未写 docstring；静态推断为 ` is forbidden dependency` 函数，具体语义以实现为准。
- 直接原始调用：`imported_module.startswith` x2
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.quality.guardrails._check_import`

#### `qts.quality.guardrails._is_forbidden_broker_adapter_dependency`
- 位置：`backend/src/qts/quality/guardrails.py:453`
- 类型：`module_function`
- 签名：`def _is_forbidden_broker_adapter_dependency(qts_relative_path: Path, imported_module: str) -> bool`
- 作用：未写 docstring；静态推断为 ` is forbidden broker adapter dependency` 函数，具体语义以实现为准。
- 直接原始调用：`any`, `imported_module.startswith`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.quality.guardrails._check_import`

#### `qts.quality.guardrails._is_forbidden_adapter_dependency`
- 位置：`backend/src/qts/quality/guardrails.py:465`
- 类型：`module_function`
- 签名：`def _is_forbidden_adapter_dependency(qts_relative_path: Path, imported_module: str) -> bool`
- 作用：未写 docstring；静态推断为 ` is forbidden adapter dependency` 函数，具体语义以实现为准。
- 直接原始调用：`imported_module.startswith` x2
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.quality.guardrails._check_import`

#### `qts.quality.guardrails._check_product_specific_code`
- 位置：`backend/src/qts/quality/guardrails.py:476`
- 类型：`module_function`
- 签名：`def _check_product_specific_code(relative_path: Path, qts_relative_path: Path, tree: ast.AST) -> list[GuardrailViolation]`
- 作用：未写 docstring；静态推断为 ` check product specific code` 函数，具体语义以实现为准。
- 直接原始调用：`_check_forbidden_tokens`
- 已解析到仓库内部的调用：`qts.quality.guardrails._check_forbidden_tokens`
- 被以下仓库内部符号调用：`qts.quality.guardrails.ProductSpecificRule.check`

#### `qts.quality.guardrails._check_broker_specific_code`
- 位置：`backend/src/qts/quality/guardrails.py:492`
- 类型：`module_function`
- 签名：`def _check_broker_specific_code(relative_path: Path, qts_relative_path: Path, tree: ast.AST) -> list[GuardrailViolation]`
- 作用：未写 docstring；静态推断为 ` check broker specific code` 函数，具体语义以实现为准。
- 直接原始调用：`_check_forbidden_tokens`
- 已解析到仓库内部的调用：`qts.quality.guardrails._check_forbidden_tokens`
- 被以下仓库内部符号调用：`qts.quality.guardrails.BrokerSpecificRule.check`

#### `qts.quality.guardrails._check_test_support_code`
- 位置：`backend/src/qts/quality/guardrails.py:508`
- 类型：`module_function`
- 签名：`def _check_test_support_code(relative_path: Path, qts_relative_path: Path, tree: ast.AST) -> list[GuardrailViolation]`
- 作用：未写 docstring；静态推断为 ` check test support code` 函数，具体语义以实现为准。
- 直接原始调用：`GuardrailViolation` x2, `str` x2, `violations.append` x2, `_contains_forbidden_token`, `_identifier_tokens`, `_node_identifier_name`, `ast.walk`, `getattr`, `path_tokens.intersection`
- 已解析到仓库内部的调用：`qts.quality.guardrails._identifier_tokens`, `qts.quality.guardrails.GuardrailViolation`, `qts.quality.guardrails._node_identifier_name`, `qts.quality.guardrails._contains_forbidden_token`
- 被以下仓库内部符号调用：`qts.quality.guardrails.TestSupportRule.check`

#### `qts.quality.guardrails._check_shared_capability_placement`
- 位置：`backend/src/qts/quality/guardrails.py:539`
- 类型：`module_function`
- 签名：`def _check_shared_capability_placement(relative_path: Path, qts_relative_path: Path) -> list[GuardrailViolation]`
- 作用：未写 docstring；静态推断为 ` check shared capability placement` 函数，具体语义以实现为准。
- 直接原始调用：`GuardrailViolation`, `_has_allowed_prefix`, `_identifier_tokens`, `path_tokens.intersection`, `str`
- 已解析到仓库内部的调用：`qts.quality.guardrails._has_allowed_prefix`, `qts.quality.guardrails._identifier_tokens`, `qts.quality.guardrails.GuardrailViolation`
- 被以下仓库内部符号调用：`qts.quality.guardrails.SharedCapabilityRule.check`

#### `qts.quality.guardrails._check_oop_public_factory_functions`
- 位置：`backend/src/qts/quality/guardrails.py:561`
- 类型：`module_function`
- 签名：`def _check_oop_public_factory_functions(relative_path: Path, qts_relative_path: Path, tree: ast.AST) -> list[GuardrailViolation]`
- 作用：未写 docstring；静态推断为 ` check oop public factory functions` 函数，具体语义以实现为准。
- 直接原始调用：`node.name.startswith` x2, `GuardrailViolation`, `cast`, `isinstance`, `qts_relative_path.as_posix`, `str`, `violations.append`
- 已解析到仓库内部的调用：`qts.quality.guardrails.GuardrailViolation`
- 被以下仓库内部符号调用：`qts.quality.guardrails.OOPPublicFactoryRule.check`

#### `qts.quality.guardrails._check_oop_helper_ownership`
- 位置：`backend/src/qts/quality/guardrails.py:592`
- 类型：`module_function`
- 签名：`def _check_oop_helper_ownership(relative_path: Path, qts_relative_path: Path, tree: ast.AST) -> list[GuardrailViolation]`
- 作用：未写 docstring；静态推断为 ` check oop helper ownership` 函数，具体语义以实现为准。
- 直接原始调用：`node.name.startswith` x4, `isinstance` x3, `len` x3, `GuardrailViolation` x2, `str` x2, `_node_references_name`, `cast`, `qts_relative_path.as_posix`, `violations.append`
- 已解析到仓库内部的调用：`qts.quality.guardrails.GuardrailViolation`, `qts.quality.guardrails._node_references_name`
- 被以下仓库内部符号调用：`qts.quality.guardrails.OOPHelperOwnershipRule.check`

#### `qts.quality.guardrails._check_backtest_runner_cohesion`
- 位置：`backend/src/qts/quality/guardrails.py:659`
- 类型：`module_function`
- 签名：`def _check_backtest_runner_cohesion(relative_path: Path, qts_relative_path: Path, tree: ast.AST) -> list[GuardrailViolation]`
- 作用：未写 docstring；静态推断为 ` check backtest runner cohesion` 函数，具体语义以实现为准。
- 直接原始调用：`GuardrailViolation` x3, `str` x3, `violations.append` x3, `_iter_imported_names`, `_iter_imports`, `ast.walk`, `imported_module.startswith`, `isinstance`
- 已解析到仓库内部的调用：`qts.quality.guardrails._iter_imports`, `qts.quality.guardrails.GuardrailViolation`, `qts.quality.guardrails._iter_imported_names`
- 被以下仓库内部符号调用：`qts.quality.guardrails.BacktestRunnerCohesionRule.check`

#### `qts.quality.guardrails._check_backtest_input_cohesion`
- 位置：`backend/src/qts/quality/guardrails.py:715`
- 类型：`module_function`
- 签名：`def _check_backtest_input_cohesion(relative_path: Path, qts_relative_path: Path, tree: ast.AST) -> list[GuardrailViolation]`
- 作用：未写 docstring；静态推断为 ` check backtest input cohesion` 函数，具体语义以实现为准。
- 直接原始调用：`GuardrailViolation` x3, `str` x3, `violations.append` x3, `_iter_imported_names`, `_iter_imports`, `ast.walk`, `isinstance`
- 已解析到仓库内部的调用：`qts.quality.guardrails._iter_imports`, `qts.quality.guardrails.GuardrailViolation`, `qts.quality.guardrails._iter_imported_names`
- 被以下仓库内部符号调用：`qts.quality.guardrails.BacktestInputCohesionRule.check`

#### `qts.quality.guardrails._check_backtest_engine_cohesion`
- 位置：`backend/src/qts/quality/guardrails.py:771`
- 类型：`module_function`
- 签名：`def _check_backtest_engine_cohesion(relative_path: Path, qts_relative_path: Path, tree: ast.AST) -> list[GuardrailViolation]`
- 作用：未写 docstring；静态推断为 ` check backtest engine cohesion` 函数，具体语义以实现为准。
- 直接原始调用：`GuardrailViolation` x2, `str` x2, `violations.append` x2, `_iter_imports`, `ast.walk`, `imported_module.startswith`, `isinstance`
- 已解析到仓库内部的调用：`qts.quality.guardrails._iter_imports`, `qts.quality.guardrails.GuardrailViolation`
- 被以下仓库内部符号调用：`qts.quality.guardrails.BacktestEngineCohesionRule.check`

#### `qts.quality.guardrails._check_forbidden_tokens`
- 位置：`backend/src/qts/quality/guardrails.py:811`
- 类型：`module_function`
- 签名：`def _check_forbidden_tokens(relative_path: Path, tree: ast.AST, *, tokens: frozenset[str], code: str, description: str) -> list[GuardrailViolation]`
- 作用：未写 docstring；静态推断为 ` check forbidden tokens` 函数，具体语义以实现为准。
- 直接原始调用：`GuardrailViolation` x2, `_contains_forbidden_token` x2, `getattr` x2, `isinstance` x2, `str` x2, `violations.append` x2, `_node_identifier_name`, `ast.walk`
- 已解析到仓库内部的调用：`qts.quality.guardrails._node_identifier_name`, `qts.quality.guardrails._contains_forbidden_token`, `qts.quality.guardrails.GuardrailViolation`
- 被以下仓库内部符号调用：`qts.quality.guardrails._check_broker_specific_code`, `qts.quality.guardrails._check_product_specific_code`

#### `qts.quality.guardrails._node_identifier_name`
- 位置：`backend/src/qts/quality/guardrails.py:844`
- 类型：`module_function`
- 签名：`def _node_identifier_name(node: ast.AST) -> str | None`
- 作用：未写 docstring；静态推断为 ` node identifier name` 函数，具体语义以实现为准。
- 直接原始调用：`isinstance` x5
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.quality.guardrails._check_forbidden_tokens`, `qts.quality.guardrails._check_test_support_code`

#### `qts.quality.guardrails._contains_forbidden_token`
- 位置：`backend/src/qts/quality/guardrails.py:854`
- 类型：`module_function`
- 签名：`def _contains_forbidden_token(value: str, forbidden_tokens: frozenset[str]) -> bool`
- 作用：未写 docstring；静态推断为 ` contains forbidden token` 函数，具体语义以实现为准。
- 直接原始调用：`_identifier_tokens`, `any`
- 已解析到仓库内部的调用：`qts.quality.guardrails._identifier_tokens`
- 被以下仓库内部符号调用：`qts.quality.guardrails._check_forbidden_tokens`, `qts.quality.guardrails._check_test_support_code`

#### `qts.quality.guardrails._node_references_name`
- 位置：`backend/src/qts/quality/guardrails.py:858`
- 类型：`module_function`
- 签名：`def _node_references_name(node: ast.AST, name: str) -> bool`
- 作用：未写 docstring；静态推断为 ` node references name` 函数，具体语义以实现为准。
- 直接原始调用：`isinstance` x2, `any`, `ast.walk`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.quality.guardrails._check_oop_helper_ownership`

#### `qts.quality.guardrails._identifier_tokens`
- 位置：`backend/src/qts/quality/guardrails.py:865`
- 类型：`module_function`
- 签名：`def _identifier_tokens(value: str) -> set[str]`
- 作用：未写 docstring；静态推断为 ` identifier tokens` 函数，具体语义以实现为准。
- 直接原始调用：`item.upper`, `part.upper`, `re.findall`, `re.split`, `set`, `tokens.add`, `tokens.update`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.quality.guardrails._check_shared_capability_placement`, `qts.quality.guardrails._check_test_support_code`, `qts.quality.guardrails._contains_forbidden_token`

#### `qts.quality.guardrails._iter_imports`
- 位置：`backend/src/qts/quality/guardrails.py:877`
- 类型：`module_function`
- 签名：`def _iter_imports(tree: ast.AST) -> list[tuple[str, int]]`
- 作用：未写 docstring；静态推断为 ` iter imports` 函数，具体语义以实现为准。
- 直接原始调用：`isinstance` x2, `ast.walk`, `imports.append`, `imports.extend`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.quality.guardrails.ImportBoundaryRule.check`, `qts.quality.guardrails._check_backtest_engine_cohesion`, `qts.quality.guardrails._check_backtest_input_cohesion`, `qts.quality.guardrails._check_backtest_runner_cohesion`

#### `qts.quality.guardrails._iter_imported_names`
- 位置：`backend/src/qts/quality/guardrails.py:887`
- 类型：`module_function`
- 签名：`def _iter_imported_names(tree: ast.AST) -> list[tuple[str, str, int]]`
- 作用：未写 docstring；静态推断为 ` iter imported names` 函数，具体语义以实现为准。
- 直接原始调用：`ast.walk`, `imports.extend`, `isinstance`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.quality.guardrails._check_backtest_input_cohesion`, `qts.quality.guardrails._check_backtest_runner_cohesion`

#### `qts.quality.guardrails._has_allowed_prefix`
- 位置：`backend/src/qts/quality/guardrails.py:895`
- 类型：`module_function`
- 签名：`def _has_allowed_prefix(path: Path, prefixes: tuple[tuple[str, ...], ...]) -> bool`
- 作用：未写 docstring；静态推断为 ` has allowed prefix` 函数，具体语义以实现为准。
- 直接原始调用：`any`, `len`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.quality.guardrails.BrokerSpecificRule.check`, `qts.quality.guardrails.ProductSpecificRule.check`, `qts.quality.guardrails._check_shared_capability_placement`

#### `qts.quality.guardrails.main`
- 位置：`backend/src/qts/quality/guardrails.py:899`
- 类型：`module_function`
- 签名：`def main() -> int`
- 作用：Perform main.
- 直接原始调用：`print` x3, `Path.cwd`, `run_guardrails`, `violation.format`
- 已解析到仓库内部的调用：`qts.quality.guardrails.run_guardrails`
- 被以下仓库内部符号调用：`scripts.verify_guardrails.main`

### `qts.reconciliation`

模块：`qts.reconciliation`

#### `qts.reconciliation.DriftKind`
- 位置：`backend/src/qts/reconciliation.py:14`
- 类型：`class`
- 签名：`class DriftKind(StrEnum)`
- 作用：Reconciliation outcome categories.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.reconciliation.OrderSnapshot`
- 位置：`backend/src/qts/reconciliation.py:25`
- 类型：`class`
- 签名：`class OrderSnapshot`
- 作用：Normalized representation of an internal/broker order for reconciliation.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.reconciliation.OrderSnapshot.__post_init__`
- 位置：`backend/src/qts/reconciliation.py:34`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError` x2, `Decimal`, `self.status.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.reconciliation.PositionSnapshot`
- 位置：`backend/src/qts/reconciliation.py:43`
- 类型：`class`
- 签名：`class PositionSnapshot`
- 作用：Normalized instrument position used in reconciliation.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.reconciliation.CashSnapshot`
- 位置：`backend/src/qts/reconciliation.py:51`
- 类型：`class`
- 签名：`class CashSnapshot`
- 作用：Normalized cash balance used in reconciliation.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.reconciliation.CashSnapshot.__post_init__`
- 位置：`backend/src/qts/reconciliation.py:57`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError`, `self.currency.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.reconciliation.ReconciliationSnapshot`
- 位置：`backend/src/qts/reconciliation.py:64`
- 类型：`class`
- 签名：`class ReconciliationSnapshot`
- 作用：Complete account snapshot used by the reconciliation engine.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.reconciliation.DriftItem`
- 位置：`backend/src/qts/reconciliation.py:74`
- 类型：`class`
- 签名：`class DriftItem`
- 作用：Single reconciliation difference entry.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.reconciliation._compare_orders`, `qts.reconciliation._quantity_item`

#### `qts.reconciliation.DriftItem.to_dict`
- 位置：`backend/src/qts/reconciliation.py:82`
- 类型：`method`
- 签名：`def to_dict(self) -> dict[str, str | None]`
- 作用：Perform to_dict.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.reconciliation.ReconciliationReport`
- 位置：`backend/src/qts/reconciliation.py:93`
- 类型：`class`
- 签名：`class ReconciliationReport`
- 作用：Drift report for a single account.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.reconciliation.reconcile_snapshots`

#### `qts.reconciliation.ReconciliationReport.has_drift`
- 位置：`backend/src/qts/reconciliation.py:100`
- 类型：`property`
- 签名：`def has_drift(self) -> bool`
- 作用：Perform has_drift.
- 直接原始调用：`any`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.reconciliation.ReconciliationReport.to_dict`
- 位置：`backend/src/qts/reconciliation.py:106`
- 类型：`method`
- 签名：`def to_dict(self) -> dict[str, Any]`
- 作用：Perform to_dict.
- 直接原始调用：`item.to_dict`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.reconciliation.StartupReconciliationDecision`
- 位置：`backend/src/qts/reconciliation.py:116`
- 类型：`class`
- 签名：`class StartupReconciliationDecision`
- 作用：Startup gate result derived from reconciliation drift.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.reconciliation.startup_reconciliation_gate`

#### `qts.reconciliation.ReconciliationEngine`
- 位置：`backend/src/qts/reconciliation.py:124`
- 类型：`class`
- 签名：`class ReconciliationEngine`
- 作用：Deterministic snapshot reconciliation service.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.reconciliation.ReconciliationEngine.__init__`
- 位置：`backend/src/qts/reconciliation.py:127`
- 类型：`method`
- 签名：`def __init__(self, *, tolerance: Decimal=Decimal('0')) -> None`
- 作用：Perform __init__.
- 直接原始调用：`Decimal`, `ValueError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.reconciliation.ReconciliationEngine.reconcile`
- 位置：`backend/src/qts/reconciliation.py:133`
- 类型：`method`
- 签名：`def reconcile(self, *, internal: ReconciliationSnapshot, broker: ReconciliationSnapshot, tolerance: Decimal | None=None) -> ReconciliationReport`
- 作用：Reconcile two snapshots and return drift report.
- 直接原始调用：`reconcile_snapshots`, `self._effective_tolerance`
- 已解析到仓库内部的调用：`qts.reconciliation.reconcile_snapshots`, `qts.reconciliation.ReconciliationEngine._effective_tolerance`
- 被以下仓库内部符号调用：无

#### `qts.reconciliation.ReconciliationEngine.startup_gate`
- 位置：`backend/src/qts/reconciliation.py:148`
- 类型：`method`
- 签名：`def startup_gate(self, report: ReconciliationReport) -> StartupReconciliationDecision`
- 作用：Return startup decision based on reconciliation drift.
- 直接原始调用：`startup_reconciliation_gate`
- 已解析到仓库内部的调用：`qts.reconciliation.startup_reconciliation_gate`
- 被以下仓库内部符号调用：无

#### `qts.reconciliation.ReconciliationEngine._effective_tolerance`
- 位置：`backend/src/qts/reconciliation.py:152`
- 类型：`method`
- 签名：`def _effective_tolerance(self, override: Decimal | None) -> Decimal`
- 作用：Perform _effective_tolerance.
- 直接原始调用：`Decimal`, `ValueError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.reconciliation.ReconciliationEngine.reconcile`

#### `qts.reconciliation.startup_reconciliation_gate`
- 位置：`backend/src/qts/reconciliation.py:161`
- 类型：`module_function`
- 签名：`def startup_reconciliation_gate(report: ReconciliationReport) -> StartupReconciliationDecision`
- 作用：Block trading on startup when reconciliation contains critical drift.
- 直接原始调用：`StartupReconciliationDecision` x2
- 已解析到仓库内部的调用：`qts.reconciliation.StartupReconciliationDecision`
- 被以下仓库内部符号调用：`qts.reconciliation.ReconciliationEngine.startup_gate`

#### `qts.reconciliation.reconcile_snapshots`
- 位置：`backend/src/qts/reconciliation.py:173`
- 类型：`module_function`
- 签名：`def reconcile_snapshots(*, internal: ReconciliationSnapshot, broker: ReconciliationSnapshot, tolerance: Decimal=Decimal('0')) -> ReconciliationReport`
- 作用：Compare broker and internal snapshots into a deterministic drift report.
- 直接原始调用：`ValueError` x2, `Decimal`, `ReconciliationReport`, `_compare_cash`, `_compare_orders`, `_compare_positions`, `_drift_sort_key`, `sorted`, `tuple`
- 已解析到仓库内部的调用：`qts.reconciliation._compare_orders`, `qts.reconciliation._compare_positions`, `qts.reconciliation._compare_cash`, `qts.reconciliation.ReconciliationReport`, `qts.reconciliation._drift_sort_key`
- 被以下仓库内部符号调用：`qts.reconciliation.ReconciliationEngine.reconcile`

#### `qts.reconciliation._compare_orders`
- 位置：`backend/src/qts/reconciliation.py:196`
- 类型：`module_function`
- 签名：`def _compare_orders(internal: tuple[OrderSnapshot, ...], broker: tuple[OrderSnapshot, ...]) -> list[DriftItem]`
- 作用：Perform _compare_orders.
- 直接原始调用：`_order_repr` x6, `DriftItem` x4, `items.append` x4, `left.get`, `left.keys`, `right.get`, `right.keys`, `sorted`
- 已解析到仓库内部的调用：`qts.reconciliation.DriftItem`, `qts.reconciliation._order_repr`
- 被以下仓库内部符号调用：`qts.reconciliation.reconcile_snapshots`

#### `qts.reconciliation._compare_positions`
- 位置：`backend/src/qts/reconciliation.py:228`
- 类型：`module_function`
- 签名：`def _compare_positions(internal: tuple[PositionSnapshot, ...], broker: tuple[PositionSnapshot, ...], tolerance: Decimal) -> list[DriftItem]`
- 作用：Perform _compare_positions.
- 直接原始调用：`_quantity_item`, `items.append`, `left.get`, `left.keys`, `right.get`, `right.keys`, `sorted`
- 已解析到仓库内部的调用：`qts.reconciliation._quantity_item`
- 被以下仓库内部符号调用：`qts.reconciliation.reconcile_snapshots`

#### `qts.reconciliation._compare_cash`
- 位置：`backend/src/qts/reconciliation.py:245`
- 类型：`module_function`
- 签名：`def _compare_cash(internal: tuple[CashSnapshot, ...], broker: tuple[CashSnapshot, ...], tolerance: Decimal) -> list[DriftItem]`
- 作用：Perform _compare_cash.
- 直接原始调用：`_quantity_item`, `items.append`, `left.get`, `left.keys`, `right.get`, `right.keys`, `sorted`
- 已解析到仓库内部的调用：`qts.reconciliation._quantity_item`
- 被以下仓库内部符号调用：`qts.reconciliation.reconcile_snapshots`

#### `qts.reconciliation._quantity_item`
- 位置：`backend/src/qts/reconciliation.py:262`
- 类型：`module_function`
- 签名：`def _quantity_item(key: str, internal: PositionSnapshot | CashSnapshot | None, broker: PositionSnapshot | CashSnapshot | None, tolerance: Decimal) -> DriftItem`
- 作用：Perform _quantity_item.
- 直接原始调用：`_amount_repr` x4, `DriftItem` x3, `_amount` x2, `abs`
- 已解析到仓库内部的调用：`qts.reconciliation.DriftItem`, `qts.reconciliation._amount_repr`, `qts.reconciliation._amount`
- 被以下仓库内部符号调用：`qts.reconciliation._compare_cash`, `qts.reconciliation._compare_positions`

#### `qts.reconciliation._order_repr`
- 位置：`backend/src/qts/reconciliation.py:284`
- 类型：`module_function`
- 签名：`def _order_repr(order: OrderSnapshot | None) -> str | None`
- 作用：Perform _order_repr.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.reconciliation._compare_orders`

#### `qts.reconciliation._amount`
- 位置：`backend/src/qts/reconciliation.py:291`
- 类型：`module_function`
- 签名：`def _amount(item: PositionSnapshot | CashSnapshot) -> Decimal`
- 作用：Perform _amount.
- 直接原始调用：`isinstance`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.reconciliation._amount_repr`, `qts.reconciliation._quantity_item`

#### `qts.reconciliation._amount_repr`
- 位置：`backend/src/qts/reconciliation.py:298`
- 类型：`module_function`
- 签名：`def _amount_repr(item: PositionSnapshot | CashSnapshot | None) -> str | None`
- 作用：Perform _amount_repr.
- 直接原始调用：`_amount`, `str`
- 已解析到仓库内部的调用：`qts.reconciliation._amount`
- 被以下仓库内部符号调用：`qts.reconciliation._quantity_item`

#### `qts.reconciliation._drift_sort_key`
- 位置：`backend/src/qts/reconciliation.py:305`
- 类型：`module_function`
- 签名：`def _drift_sort_key(key: str) -> tuple[int, str]`
- 作用：Perform _drift_sort_key.
- 直接原始调用：`key.split`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.reconciliation.reconcile_snapshots`

### `qts.registry.broker_symbol_mapping`

模块：`qts.registry.broker_symbol_mapping`

#### `qts.registry.broker_symbol_mapping.BrokerSymbolMapping`
- 位置：`backend/src/qts/registry/broker_symbol_mapping.py:8`
- 类型：`class`
- 签名：`class BrokerSymbolMapping`
- 作用：Bidirectional mapping between internal IDs and one broker's symbols.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.__init__`
- 位置：`backend/src/qts/registry/broker_symbol_mapping.py:11`
- 类型：`method`
- 签名：`def __init__(self, broker_id: BrokerId) -> None`
- 作用：Perform __init__.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.register`
- 位置：`backend/src/qts/registry/broker_symbol_mapping.py:17`
- 类型：`method`
- 签名：`def register(self, instrument_id: InstrumentId, broker_symbol: str) -> None`
- 作用：Perform register.
- 直接原始调用：`ValueError`, `self._normalize_broker_symbol`, `self._to_instrument.get`
- 已解析到仓库内部的调用：`qts.registry.broker_symbol_mapping.BrokerSymbolMapping._normalize_broker_symbol`
- 被以下仓库内部符号调用：无

#### `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.to_broker_symbol`
- 位置：`backend/src/qts/registry/broker_symbol_mapping.py:26`
- 类型：`method`
- 签名：`def to_broker_symbol(self, instrument_id: InstrumentId) -> str`
- 作用：Perform to_broker_symbol.
- 直接原始调用：`KeyError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.to_instrument_id`
- 位置：`backend/src/qts/registry/broker_symbol_mapping.py:33`
- 类型：`method`
- 签名：`def to_instrument_id(self, broker_symbol: str) -> InstrumentId`
- 作用：Perform to_instrument_id.
- 直接原始调用：`KeyError`, `self._normalize_broker_symbol`
- 已解析到仓库内部的调用：`qts.registry.broker_symbol_mapping.BrokerSymbolMapping._normalize_broker_symbol`
- 被以下仓库内部符号调用：`qts.registry.broker_symbol_mapping.BrokerSymbolMapping.instrument_id_for_symbol`

#### `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.is_supported_symbol`
- 位置：`backend/src/qts/registry/broker_symbol_mapping.py:43`
- 类型：`method`
- 签名：`def is_supported_symbol(self, symbol: str) -> bool`
- 作用：Perform is_supported_symbol.
- 直接原始调用：`self._normalize_broker_symbol`
- 已解析到仓库内部的调用：`qts.registry.broker_symbol_mapping.BrokerSymbolMapping._normalize_broker_symbol`
- 被以下仓库内部符号调用：无

#### `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.instrument_id_for_symbol`
- 位置：`backend/src/qts/registry/broker_symbol_mapping.py:47`
- 类型：`method`
- 签名：`def instrument_id_for_symbol(self, symbol: str) -> InstrumentId`
- 作用：Perform instrument_id_for_symbol.
- 直接原始调用：`self.to_instrument_id`
- 已解析到仓库内部的调用：`qts.registry.broker_symbol_mapping.BrokerSymbolMapping.to_instrument_id`
- 被以下仓库内部符号调用：无

#### `qts.registry.broker_symbol_mapping.BrokerSymbolMapping._normalize_broker_symbol`
- 位置：`backend/src/qts/registry/broker_symbol_mapping.py:52`
- 类型：`staticmethod`
- 签名：`def _normalize_broker_symbol(broker_symbol: str) -> str`
- 作用：Perform _normalize_broker_symbol.
- 直接原始调用：`ValueError`, `broker_symbol.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.registry.broker_symbol_mapping.BrokerSymbolMapping.is_supported_symbol`, `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.register`, `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.to_instrument_id`

### `qts.registry.calendar_registry`

模块：`qts.registry.calendar_registry`

#### `qts.registry.calendar_registry.MarketSession`
- 位置：`backend/src/qts/registry/calendar_registry.py:13`
- 类型：`class`
- 签名：`class MarketSession`
- 作用：Internal half-open exchange session.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.registry.providers.comex_gold_calendar_provider.ComexGoldCalendarProvider.session_for`, `qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider.session_for`

#### `qts.registry.calendar_registry.MarketSession.__post_init__`
- 位置：`backend/src/qts/registry/calendar_registry.py:20`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError` x2, `self.calendar_id.strip`, `self.session_id.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.registry.calendar_registry.MarketSession.open_time`
- 位置：`backend/src/qts/registry/calendar_registry.py:28`
- 类型：`property`
- 签名：`def open_time(self) -> datetime`
- 作用：Perform open_time.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.registry.calendar_registry.MarketSession.close_time`
- 位置：`backend/src/qts/registry/calendar_registry.py:33`
- 类型：`property`
- 签名：`def close_time(self) -> datetime`
- 作用：Perform close_time.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.registry.calendar_registry.CalendarProvider`
- 位置：`backend/src/qts/registry/calendar_registry.py:38`
- 类型：`class`
- 签名：`class CalendarProvider(Protocol)`
- 作用：Provider interface for internal calendar session lookup.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.registry.calendar_registry.CalendarProvider.session_for`
- 位置：`backend/src/qts/registry/calendar_registry.py:41`
- 类型：`method`
- 签名：`def session_for(self, session_date: date) -> MarketSession`
- 作用：Return the exchange session for a date.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.registry.calendar_registry.CalendarRegistry`
- 位置：`backend/src/qts/registry/calendar_registry.py:45`
- 类型：`class`
- 签名：`class CalendarRegistry`
- 作用：Lookup table for calendar providers.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.registry.calendar_registry.CalendarRegistry.__init__`
- 位置：`backend/src/qts/registry/calendar_registry.py:48`
- 类型：`method`
- 签名：`def __init__(self) -> None`
- 作用：Perform __init__.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.registry.calendar_registry.CalendarRegistry.register`
- 位置：`backend/src/qts/registry/calendar_registry.py:52`
- 类型：`method`
- 签名：`def register(self, calendar_id: str, provider: CalendarProvider) -> None`
- 作用：Perform register.
- 直接原始调用：`ValueError`, `calendar_id.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.registry.calendar_registry.CalendarRegistry.session_for`
- 位置：`backend/src/qts/registry/calendar_registry.py:58`
- 类型：`method`
- 签名：`def session_for(self, calendar_id: str, session_date: date) -> MarketSession`
- 作用：Perform session_for.
- 直接原始调用：`KeyError`, `provider.session_for`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.registry.future_chain_registry`

模块：`qts.registry.future_chain_registry`

#### `qts.registry.future_chain_registry.FutureChain`
- 位置：`backend/src/qts/registry/future_chain_registry.py:11`
- 类型：`class`
- 签名：`class FutureChain`
- 作用：Ordered concrete future contracts for a root symbol.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.registry.future_chain_registry.FutureChain.__post_init__`
- 位置：`backend/src/qts/registry/future_chain_registry.py:17`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError` x2, `self.root_symbol.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.registry.future_chain_registry.ContinuousFutureRef`
- 位置：`backend/src/qts/registry/future_chain_registry.py:26`
- 类型：`class`
- 签名：`class ContinuousFutureRef`
- 作用：Research/data reference to a rolling future contract.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.registry.future_chain_registry.ContinuousFutureRef.__post_init__`
- 位置：`backend/src/qts/registry/future_chain_registry.py:32`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError` x2, `self.root_symbol.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.registry.future_chain_registry.FutureChainRegistry`
- 位置：`backend/src/qts/registry/future_chain_registry.py:40`
- 类型：`class`
- 签名：`class FutureChainRegistry`
- 作用：Resolve future roots to concrete tradable contracts.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.registry.future_chain_registry.FutureChainRegistry.__init__`
- 位置：`backend/src/qts/registry/future_chain_registry.py:43`
- 类型：`method`
- 签名：`def __init__(self) -> None`
- 作用：Perform __init__.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.registry.future_chain_registry.FutureChainRegistry.register`
- 位置：`backend/src/qts/registry/future_chain_registry.py:47`
- 类型：`method`
- 签名：`def register(self, chain: FutureChain) -> None`
- 作用：Perform register.
- 直接原始调用：`self._normalize_root`
- 已解析到仓库内部的调用：`qts.registry.future_chain_registry.FutureChainRegistry._normalize_root`
- 被以下仓库内部符号调用：无

#### `qts.registry.future_chain_registry.FutureChainRegistry.resolve_contract`
- 位置：`backend/src/qts/registry/future_chain_registry.py:51`
- 类型：`method`
- 签名：`def resolve_contract(self, root_symbol: str, *, offset: int=0) -> InstrumentId`
- 作用：Perform resolve_contract.
- 直接原始调用：`KeyError`, `self._get_chain`
- 已解析到仓库内部的调用：`qts.registry.future_chain_registry.FutureChainRegistry._get_chain`
- 被以下仓库内部符号调用：无

#### `qts.registry.future_chain_registry.FutureChainRegistry.require_tradable`
- 位置：`backend/src/qts/registry/future_chain_registry.py:61`
- 类型：`method`
- 签名：`def require_tradable(self, reference: InstrumentId | ContinuousFutureRef) -> InstrumentId`
- 作用：Perform require_tradable.
- 直接原始调用：`ValueError`, `isinstance`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.registry.future_chain_registry.FutureChainRegistry._get_chain`
- 位置：`backend/src/qts/registry/future_chain_registry.py:67`
- 类型：`method`
- 签名：`def _get_chain(self, root_symbol: str) -> FutureChain`
- 作用：Perform _get_chain.
- 直接原始调用：`KeyError`, `self._normalize_root`
- 已解析到仓库内部的调用：`qts.registry.future_chain_registry.FutureChainRegistry._normalize_root`
- 被以下仓库内部符号调用：`qts.registry.future_chain_registry.FutureChainRegistry.resolve_contract`

#### `qts.registry.future_chain_registry.FutureChainRegistry._normalize_root`
- 位置：`backend/src/qts/registry/future_chain_registry.py:76`
- 类型：`staticmethod`
- 签名：`def _normalize_root(root_symbol: str) -> str`
- 作用：Perform _normalize_root.
- 直接原始调用：`ValueError`, `root_symbol.strip`, `root_symbol.strip.upper`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.registry.future_chain_registry.FutureChainRegistry._get_chain`, `qts.registry.future_chain_registry.FutureChainRegistry.register`

### `qts.registry.future_roll`

模块：`qts.registry.future_roll`

#### `qts.registry.future_roll.FutureContractCandidate`
- 位置：`backend/src/qts/registry/future_roll.py:16`
- 类型：`class`
- 签名：`class FutureContractCandidate`
- 作用：One concrete futures contract candidate at a decision timestamp.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.HistoricalBarStream._emit_selected_session_rows`, `qts.data.historical.csv_dataset.HistoricalBarStream._iter_selected_contract_rows`

#### `qts.registry.future_roll.FutureContractCandidate.__post_init__`
- 位置：`backend/src/qts/registry/future_roll.py:26`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：未写 docstring；静态推断为所属类上的 `  post init  ` 行为。
- 直接原始调用：`ValueError` x3, `Decimal`, `self.root_symbol.strip`, `self.symbol.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.registry.future_roll.FutureContractSelector`
- 位置：`backend/src/qts/registry/future_roll.py:35`
- 类型：`class`
- 签名：`class FutureContractSelector(Protocol)`
- 作用：Select one concrete future from same-root same-time candidates.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.registry.future_roll.FutureContractSelector.select`
- 位置：`backend/src/qts/registry/future_roll.py:38`
- 类型：`method`
- 签名：`def select(self, candidates: tuple[FutureContractCandidate, ...]) -> FutureContractCandidate`
- 作用：Select a concrete future contract.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.registry.future_roll.HighestVolumeFutureContractSelector`
- 位置：`backend/src/qts/registry/future_roll.py:46`
- 类型：`class`
- 签名：`class HighestVolumeFutureContractSelector`
- 作用：Select the most liquid candidate for one root at one timestamp.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.inputs.BacktestInputBuilder._stream_configured_bars`

#### `qts.registry.future_roll.HighestVolumeFutureContractSelector.select`
- 位置：`backend/src/qts/registry/future_roll.py:49`
- 类型：`method`
- 签名：`def select(self, candidates: tuple[FutureContractCandidate, ...]) -> FutureContractCandidate`
- 作用：Perform select.
- 直接原始调用：`ValueError`, `max`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.registry.future_roll.FutureRollSelection`
- 位置：`backend/src/qts/registry/future_roll.py:67`
- 类型：`class`
- 签名：`class FutureRollSelection`
- 作用：Resolved concrete contract for a continuous future at one timestamp.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.csv_dataset.HistoricalBarStream._emit_selected_session_rows`, `qts.data.historical.csv_dataset.HistoricalBarStream._iter_selected_contract_rows`

#### `qts.registry.future_roll.FutureRollSelection.__post_init__`
- 位置：`backend/src/qts/registry/future_roll.py:77`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：未写 docstring；静态推断为所属类上的 `  post init  ` 行为。
- 直接原始调用：`ValueError` x2, `self.root_symbol.strip`, `self.source_symbol.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.registry.future_roll.FutureRollRegistry`
- 位置：`backend/src/qts/registry/future_roll.py:84`
- 类型：`class`
- 签名：`class FutureRollRegistry`
- 作用：Resolve continuous futures to concrete contracts over time.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.inputs.BacktestInputBuilder._roll_registry`

#### `qts.registry.future_roll.FutureRollRegistry.__init__`
- 位置：`backend/src/qts/registry/future_roll.py:87`
- 类型：`method`
- 签名：`def __init__(self, *, retain_history: bool=True) -> None`
- 作用：未写 docstring；静态推断为所属类上的 `  init  ` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.registry.future_roll.FutureRollRegistry.register_root`
- 位置：`backend/src/qts/registry/future_roll.py:96`
- 类型：`method`
- 签名：`def register_root(self, *, root_symbol: str, exchange: str, contracts: tuple[InstrumentId, ...]) -> InstrumentId`
- 作用：Perform register_root.
- 直接原始调用：`ValueError` x2, `exchange.strip` x2, `InstrumentId`, `dict.fromkeys`, `exchange.strip.upper`, `self._latest_prices_by_continuous.setdefault`, `self._normalize_root`, `self._selection_times_by_continuous.setdefault`, `self._selections_by_continuous.setdefault`, `tuple`
- 已解析到仓库内部的调用：`qts.registry.future_roll.FutureRollRegistry._normalize_root`, `qts.core.ids.InstrumentId`
- 被以下仓库内部符号调用：无

#### `qts.registry.future_roll.FutureRollRegistry.continuous_instrument_id`
- 位置：`backend/src/qts/registry/future_roll.py:119`
- 类型：`method`
- 签名：`def continuous_instrument_id(self, root_symbol: str, *, offset: int=0) -> InstrumentId`
- 作用：Perform continuous_instrument_id.
- 直接原始调用：`KeyError`, `ValueError`, `self._normalize_root`
- 已解析到仓库内部的调用：`qts.registry.future_roll.FutureRollRegistry._normalize_root`
- 被以下仓库内部符号调用：`qts.registry.future_roll.FutureRollRegistry.resolve_contract`

#### `qts.registry.future_roll.FutureRollRegistry.record_selection`
- 位置：`backend/src/qts/registry/future_roll.py:129`
- 类型：`method`
- 签名：`def record_selection(self, selection: FutureRollSelection) -> None`
- 作用：Perform record_selection.
- 直接原始调用：`KeyError`, `ValueError`, `dict`, `latest_prices.update`, `replace`, `selection_times.append`, `selections.append`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.registry.future_roll.FutureRollRegistry.is_continuous`
- 位置：`backend/src/qts/registry/future_roll.py:147`
- 类型：`method`
- 签名：`def is_continuous(self, instrument_id: InstrumentId) -> bool`
- 作用：Perform is_continuous.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.registry.future_roll.FutureRollRegistry.resolve_contract`
- 位置：`backend/src/qts/registry/future_roll.py:151`
- 类型：`method`
- 签名：`def resolve_contract(self, reference: str | InstrumentId, *, as_of: datetime, offset: int=0) -> InstrumentId`
- 作用：Perform resolve_contract.
- 直接原始调用：`ValueError`, `isinstance`, `self._selection_at`, `self.continuous_instrument_id`
- 已解析到仓库内部的调用：`qts.registry.future_roll.FutureRollRegistry.continuous_instrument_id`, `qts.registry.future_roll.FutureRollRegistry._selection_at`
- 被以下仓库内部符号调用：无

#### `qts.registry.future_roll.FutureRollRegistry.related_contracts`
- 位置：`backend/src/qts/registry/future_roll.py:169`
- 类型：`method`
- 签名：`def related_contracts(self, continuous_instrument_id: InstrumentId) -> tuple[InstrumentId, ...]`
- 作用：Perform related_contracts.
- 直接原始调用：`KeyError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.registry.future_roll.FutureRollRegistry.execution_price`
- 位置：`backend/src/qts/registry/future_roll.py:176`
- 类型：`method`
- 签名：`def execution_price(self, continuous_instrument_id: InstrumentId, concrete_instrument_id: InstrumentId, *, as_of: datetime) -> Decimal`
- 作用：Perform execution_price.
- 直接原始调用：`KeyError`, `as_of.isoformat`, `self._selection_at`
- 已解析到仓库内部的调用：`qts.registry.future_roll.FutureRollRegistry._selection_at`
- 被以下仓库内部符号调用：无

#### `qts.registry.future_roll.FutureRollRegistry._selection_at`
- 位置：`backend/src/qts/registry/future_roll.py:192`
- 类型：`method`
- 签名：`def _selection_at(self, continuous_instrument_id: InstrumentId, *, as_of: datetime) -> FutureRollSelection`
- 作用：未写 docstring；静态推断为所属类上的 ` selection at` 行为。
- 直接原始调用：`KeyError` x2, `as_of.isoformat`, `bisect_right`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.registry.future_roll.FutureRollRegistry.execution_price`, `qts.registry.future_roll.FutureRollRegistry.resolve_contract`

#### `qts.registry.future_roll.FutureRollRegistry._normalize_root`
- 位置：`backend/src/qts/registry/future_roll.py:212`
- 类型：`staticmethod`
- 签名：`def _normalize_root(root_symbol: str) -> str`
- 作用：未写 docstring；静态推断为所属类上的 ` normalize root` 行为。
- 直接原始调用：`ValueError`, `root_symbol.strip`, `root_symbol.strip.upper`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.registry.future_roll.FutureRollRegistry.continuous_instrument_id`, `qts.registry.future_roll.FutureRollRegistry.register_root`

### `qts.registry.instrument_registry`

模块：`qts.registry.instrument_registry`

#### `qts.registry.instrument_registry.InstrumentRegistry`
- 位置：`backend/src/qts/registry/instrument_registry.py:9`
- 类型：`class`
- 签名：`class InstrumentRegistry`
- 作用：Resolve user-facing symbols to internal instruments.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.inputs.BacktestInputBuilder._instrument_registry_for`, `qts.backtest.instrument_context.BacktestInstrumentContext.instrument_registry`

#### `qts.registry.instrument_registry.InstrumentRegistry.__init__`
- 位置：`backend/src/qts/registry/instrument_registry.py:12`
- 类型：`method`
- 签名：`def __init__(self) -> None`
- 作用：Perform __init__.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.registry.instrument_registry.InstrumentRegistry.register`
- 位置：`backend/src/qts/registry/instrument_registry.py:17`
- 类型：`method`
- 签名：`def register(self, user_symbol: str, instrument: Instrument) -> None`
- 作用：Perform register.
- 直接原始调用：`self._normalize_symbol`
- 已解析到仓库内部的调用：`qts.registry.instrument_registry.InstrumentRegistry._normalize_symbol`
- 被以下仓库内部符号调用：无

#### `qts.registry.instrument_registry.InstrumentRegistry.resolve`
- 位置：`backend/src/qts/registry/instrument_registry.py:23`
- 类型：`method`
- 签名：`def resolve(self, user_symbol: str) -> InstrumentId`
- 作用：Perform resolve.
- 直接原始调用：`KeyError`, `self._normalize_symbol`
- 已解析到仓库内部的调用：`qts.registry.instrument_registry.InstrumentRegistry._normalize_symbol`
- 被以下仓库内部符号调用：无

#### `qts.registry.instrument_registry.InstrumentRegistry.get_instrument`
- 位置：`backend/src/qts/registry/instrument_registry.py:31`
- 类型：`method`
- 签名：`def get_instrument(self, instrument_id: InstrumentId) -> Instrument`
- 作用：Perform get_instrument.
- 直接原始调用：`KeyError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.registry.instrument_registry.InstrumentRegistry.get_contract_spec`

#### `qts.registry.instrument_registry.InstrumentRegistry.get_contract_spec`
- 位置：`backend/src/qts/registry/instrument_registry.py:38`
- 类型：`method`
- 签名：`def get_contract_spec(self, instrument_id: InstrumentId) -> ContractSpec`
- 作用：Perform get_contract_spec.
- 直接原始调用：`self.get_instrument`
- 已解析到仓库内部的调用：`qts.registry.instrument_registry.InstrumentRegistry.get_instrument`
- 被以下仓库内部符号调用：无

#### `qts.registry.instrument_registry.InstrumentRegistry._normalize_symbol`
- 位置：`backend/src/qts/registry/instrument_registry.py:43`
- 类型：`staticmethod`
- 签名：`def _normalize_symbol(user_symbol: str) -> str`
- 作用：Perform _normalize_symbol.
- 直接原始调用：`ValueError`, `user_symbol.strip`, `user_symbol.strip.upper`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.registry.instrument_registry.InstrumentRegistry.register`, `qts.registry.instrument_registry.InstrumentRegistry.resolve`

### `qts.registry.option_chain_registry`

模块：`qts.registry.option_chain_registry`

#### `qts.registry.option_chain_registry.OptionChainRegistry`
- 位置：`backend/src/qts/registry/option_chain_registry.py:12`
- 类型：`class`
- 签名：`class OptionChainRegistry`
- 作用：Lookup option instruments by underlying and simple filters.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.registry.option_chain_registry.OptionChainRegistry.__init__`
- 位置：`backend/src/qts/registry/option_chain_registry.py:15`
- 类型：`method`
- 签名：`def __init__(self) -> None`
- 作用：Perform __init__.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.registry.option_chain_registry.OptionChainRegistry.register`
- 位置：`backend/src/qts/registry/option_chain_registry.py:19`
- 类型：`method`
- 签名：`def register(self, option: Instrument) -> None`
- 作用：Perform register.
- 直接原始调用：`ValueError`, `isinstance`, `self._chains.setdefault`, `self._chains.setdefault.append`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.registry.option_chain_registry.OptionChainRegistry.options_for`
- 位置：`backend/src/qts/registry/option_chain_registry.py:27`
- 类型：`method`
- 签名：`def options_for(self, underlying: InstrumentId) -> list[Instrument]`
- 作用：Perform options_for.
- 直接原始调用：`KeyError`, `list`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.registry.option_chain_registry.OptionChainRegistry.find`

#### `qts.registry.option_chain_registry.OptionChainRegistry.find`
- 位置：`backend/src/qts/registry/option_chain_registry.py:34`
- 类型：`method`
- 签名：`def find(self, *, underlying: InstrumentId, expiry: date | None=None, strike: Decimal | None=None, right: OptionRight | None=None) -> list[Instrument]`
- 作用：Perform find.
- 直接原始调用：`isinstance` x3, `self.options_for`
- 已解析到仓库内部的调用：`qts.registry.option_chain_registry.OptionChainRegistry.options_for`
- 被以下仓库内部符号调用：无

### `qts.registry.providers.comex_gold_calendar_provider`

模块：`qts.registry.providers.comex_gold_calendar_provider`

#### `qts.registry.providers.comex_gold_calendar_provider.ComexGoldCalendarProvider`
- 位置：`backend/src/qts/registry/providers/comex_gold_calendar_provider.py:12`
- 类型：`class`
- 签名：`class ComexGoldCalendarProvider`
- 作用：Regular COMEX Gold session provider for anchor-verified semantics.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.registry.providers.comex_gold_calendar_provider.ComexGoldCalendarProvider.session_for`
- 位置：`backend/src/qts/registry/providers/comex_gold_calendar_provider.py:18`
- 类型：`method`
- 签名：`def session_for(self, session_date: date) -> MarketSession`
- 作用：Perform session_for.
- 直接原始调用：`ZoneInfo` x2, `datetime.combine` x2, `time` x2, `MarketSession`, `TimeInterval`, `close_time.astimezone`, `open_time.astimezone`, `session_date.isoformat`, `timedelta`
- 已解析到仓库内部的调用：`qts.registry.calendar_registry.MarketSession`, `qts.core.time.TimeInterval`
- 被以下仓库内部符号调用：无

### `qts.registry.providers.exchange_calendar_provider`

模块：`qts.registry.providers.exchange_calendar_provider`

#### `qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider`
- 位置：`backend/src/qts/registry/providers/exchange_calendar_provider.py:14`
- 类型：`class`
- 签名：`class ExchangeCalendarProvider`
- 作用：Calendar provider backed by ``exchange-calendars``.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider.__init__`
- 位置：`backend/src/qts/registry/providers/exchange_calendar_provider.py:17`
- 类型：`method`
- 签名：`def __init__(self, calendar_id: str) -> None`
- 作用：Perform __init__.
- 直接原始调用：`ValueError`, `calendar_id.strip`, `xc.get_calendar`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider.session_for`
- 位置：`backend/src/qts/registry/providers/exchange_calendar_provider.py:24`
- 类型：`method`
- 签名：`def session_for(self, session_date: date) -> MarketSession`
- 作用：Perform session_for.
- 直接原始调用：`self._to_datetime` x2, `MarketSession`, `TimeInterval`, `self._calendar.session_close`, `self._calendar.session_open`, `session_date.isoformat`
- 已解析到仓库内部的调用：`qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider._to_datetime`, `qts.registry.calendar_registry.MarketSession`, `qts.core.time.TimeInterval`
- 被以下仓库内部符号调用：无

#### `qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider._to_datetime`
- 位置：`backend/src/qts/registry/providers/exchange_calendar_provider.py:36`
- 类型：`staticmethod`
- 签名：`def _to_datetime(value: Any) -> datetime`
- 作用：Perform _to_datetime.
- 直接原始调用：`isinstance` x2, `TypeError`, `hasattr`, `type`, `value.to_pydatetime`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider.session_for`

### `qts.registry.symbol_resolution`

模块：`qts.registry.symbol_resolution`

#### `qts.registry.symbol_resolution.SourceSymbolResolver`
- 位置：`backend/src/qts/registry/symbol_resolution.py:12`
- 类型：`class`
- 签名：`class SourceSymbolResolver(Protocol)`
- 作用：Resolve external source symbols into internal instrument IDs.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.registry.symbol_resolution.SourceSymbolResolver.is_supported_symbol`
- 位置：`backend/src/qts/registry/symbol_resolution.py:15`
- 类型：`method`
- 签名：`def is_supported_symbol(self, symbol: str) -> bool`
- 作用：Return whether the resolver knows how to map ``symbol``.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.registry.symbol_resolution.SourceSymbolResolver.instrument_id_for_symbol`
- 位置：`backend/src/qts/registry/symbol_resolution.py:19`
- 类型：`method`
- 签名：`def instrument_id_for_symbol(self, symbol: str) -> InstrumentId`
- 作用：Resolve ``symbol`` to an internal ``InstrumentId``.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.registry.symbol_resolution.StaticSymbolResolver`
- 位置：`backend/src/qts/registry/symbol_resolution.py:25`
- 类型：`class`
- 签名：`class StaticSymbolResolver`
- 作用：Resolve source symbols from an explicit symbol-to-instrument mapping.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.data.historical.catalog.HistoricalCatalog._symbol_resolvers_for_load_config`

#### `qts.registry.symbol_resolution.StaticSymbolResolver.__post_init__`
- 位置：`backend/src/qts/registry/symbol_resolution.py:31`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError` x2, `object.__setattr__`, `self._normalize_symbol`, `self.instrument_ids.items`
- 已解析到仓库内部的调用：`qts.registry.symbol_resolution.StaticSymbolResolver._normalize_symbol`
- 被以下仓库内部符号调用：无

#### `qts.registry.symbol_resolution.StaticSymbolResolver.is_supported_symbol`
- 位置：`backend/src/qts/registry/symbol_resolution.py:43`
- 类型：`method`
- 签名：`def is_supported_symbol(self, symbol: str) -> bool`
- 作用：Perform is_supported_symbol.
- 直接原始调用：`self._normalize_symbol`
- 已解析到仓库内部的调用：`qts.registry.symbol_resolution.StaticSymbolResolver._normalize_symbol`
- 被以下仓库内部符号调用：无

#### `qts.registry.symbol_resolution.StaticSymbolResolver.instrument_id_for_symbol`
- 位置：`backend/src/qts/registry/symbol_resolution.py:47`
- 类型：`method`
- 签名：`def instrument_id_for_symbol(self, symbol: str) -> InstrumentId`
- 作用：Perform instrument_id_for_symbol.
- 直接原始调用：`ValueError`, `self._normalize_symbol`
- 已解析到仓库内部的调用：`qts.registry.symbol_resolution.StaticSymbolResolver._normalize_symbol`
- 被以下仓库内部符号调用：无

#### `qts.registry.symbol_resolution.StaticSymbolResolver._normalize_symbol`
- 位置：`backend/src/qts/registry/symbol_resolution.py:56`
- 类型：`staticmethod`
- 签名：`def _normalize_symbol(symbol: str) -> str`
- 作用：Perform _normalize_symbol.
- 直接原始调用：`ValueError`, `symbol.strip`, `symbol.strip.upper`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.registry.symbol_resolution.StaticSymbolResolver.__post_init__`, `qts.registry.symbol_resolution.StaticSymbolResolver.instrument_id_for_symbol`, `qts.registry.symbol_resolution.StaticSymbolResolver.is_supported_symbol`

### `qts.risk.config`

模块：`qts.risk.config`

#### `qts.risk.config.RiskRuleConfig`
- 位置：`backend/src/qts/risk/config.py:10`
- 类型：`class`
- 签名：`class RiskRuleConfig`
- 作用：One configured risk rule.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.risk.config.RiskRuleConfig.__post_init__`
- 位置：`backend/src/qts/risk/config.py:17`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError` x2, `self.name.strip`, `self.rule_id.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.risk.config.RiskConfig`
- 位置：`backend/src/qts/risk/config.py:26`
- 类型：`class`
- 签名：`class RiskConfig`
- 作用：Account/strategy/product risk configuration.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.risk.config.RiskConfig.__post_init__`
- 位置：`backend/src/qts/risk/config.py:35`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError` x3, `Decimal` x2, `self.account_id.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.risk.kill_switch`

模块：`qts.risk.kill_switch`

#### `qts.risk.kill_switch.KillSwitchScopeType`
- 位置：`backend/src/qts/risk/kill_switch.py:12`
- 类型：`class`
- 签名：`class KillSwitchScopeType(StrEnum)`
- 作用：Supported kill-switch scopes.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.application.services.operations.OperationsService._scope_from_command`

#### `qts.risk.kill_switch.KillSwitchScope`
- 位置：`backend/src/qts/risk/kill_switch.py:22`
- 类型：`class`
- 签名：`class KillSwitchScope`
- 作用：Kill-switch scope identity.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.application.services.operations.OperationsService._scope_from_command`

#### `qts.risk.kill_switch.KillSwitchScope.global_scope`
- 位置：`backend/src/qts/risk/kill_switch.py:29`
- 类型：`classmethod`
- 签名：`def global_scope(cls) -> KillSwitchScope`
- 作用：Perform global_scope.
- 直接原始调用：`cls`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.application.services.operations.OperationsService._scope_from_command`, `qts.risk.kill_switch.KillSwitchRegistry._matching_scopes`

#### `qts.risk.kill_switch.KillSwitchScope.account`
- 位置：`backend/src/qts/risk/kill_switch.py:34`
- 类型：`classmethod`
- 签名：`def account(cls, account_id: AccountId) -> KillSwitchScope`
- 作用：Perform account.
- 直接原始调用：`cls`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.risk.kill_switch.KillSwitchRegistry._matching_scopes`

#### `qts.risk.kill_switch.KillSwitchScope.strategy`
- 位置：`backend/src/qts/risk/kill_switch.py:39`
- 类型：`classmethod`
- 签名：`def strategy(cls, strategy_id: StrategyId) -> KillSwitchScope`
- 作用：Perform strategy.
- 直接原始调用：`cls`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.risk.kill_switch.KillSwitchRegistry._matching_scopes`

#### `qts.risk.kill_switch.KillSwitchScope.broker`
- 位置：`backend/src/qts/risk/kill_switch.py:44`
- 类型：`classmethod`
- 签名：`def broker(cls, broker_id: BrokerId) -> KillSwitchScope`
- 作用：Perform broker.
- 直接原始调用：`cls`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.risk.kill_switch.KillSwitchRegistry._matching_scopes`

#### `qts.risk.kill_switch.KillSwitchScope.reason_code`
- 位置：`backend/src/qts/risk/kill_switch.py:48`
- 类型：`method`
- 签名：`def reason_code(self) -> str`
- 作用：Perform reason_code.
- 直接原始调用：`self.scope_type.value.upper`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.risk.kill_switch.KillSwitchState`
- 位置：`backend/src/qts/risk/kill_switch.py:54`
- 类型：`class`
- 签名：`class KillSwitchState`
- 作用：Kill-switch activation state.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.risk.kill_switch.KillSwitchRegistry.activate`, `qts.risk.kill_switch.KillSwitchRegistry.deactivate`

#### `qts.risk.kill_switch.KillSwitchRegistry`
- 位置：`backend/src/qts/risk/kill_switch.py:62`
- 类型：`class`
- 签名：`class KillSwitchRegistry`
- 作用：Auditable in-memory kill-switch registry.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.application.services.operations.OperationsService.__init__`

#### `qts.risk.kill_switch.KillSwitchRegistry.__init__`
- 位置：`backend/src/qts/risk/kill_switch.py:65`
- 类型：`method`
- 签名：`def __init__(self) -> None`
- 作用：未写 docstring；静态推断为所属类上的 `  init  ` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.risk.kill_switch.KillSwitchRegistry.activate`
- 位置：`backend/src/qts/risk/kill_switch.py:68`
- 类型：`method`
- 签名：`def activate(self, scope: KillSwitchScope, *, reason: str) -> KillSwitchState`
- 作用：Perform activate.
- 直接原始调用：`KillSwitchState`, `ValueError`, `reason.strip`
- 已解析到仓库内部的调用：`qts.risk.kill_switch.KillSwitchState`
- 被以下仓库内部符号调用：无

#### `qts.risk.kill_switch.KillSwitchRegistry.deactivate`
- 位置：`backend/src/qts/risk/kill_switch.py:76`
- 类型：`method`
- 签名：`def deactivate(self, scope: KillSwitchScope, *, reason: str) -> KillSwitchState`
- 作用：Perform deactivate.
- 直接原始调用：`KillSwitchState`, `ValueError`, `reason.strip`
- 已解析到仓库内部的调用：`qts.risk.kill_switch.KillSwitchState`
- 被以下仓库内部符号调用：无

#### `qts.risk.kill_switch.KillSwitchRegistry.check_order`
- 位置：`backend/src/qts/risk/kill_switch.py:84`
- 类型：`method`
- 签名：`def check_order(self, request: OrderRiskRequest, *, account_id: AccountId, strategy_id: StrategyId | None, broker_id: BrokerId) -> RiskDecision`
- 作用：Perform check_order.
- 直接原始调用：`RiskDecision.approve`, `RiskDecision.rejected`, `self._matching_scopes`, `self._states.get`, `state.scope.reason_code`
- 已解析到仓库内部的调用：`qts.risk.kill_switch.KillSwitchRegistry._matching_scopes`
- 被以下仓库内部符号调用：无

#### `qts.risk.kill_switch.KillSwitchRegistry._matching_scopes`
- 位置：`backend/src/qts/risk/kill_switch.py:105`
- 类型：`staticmethod`
- 签名：`def _matching_scopes(account_id: AccountId, strategy_id: StrategyId | None, broker_id: BrokerId) -> tuple[KillSwitchScope, ...]`
- 作用：未写 docstring；静态推断为所属类上的 ` matching scopes` 行为。
- 直接原始调用：`KillSwitchScope.account`, `KillSwitchScope.broker`, `KillSwitchScope.global_scope`, `KillSwitchScope.strategy`, `scopes.append`, `tuple`
- 已解析到仓库内部的调用：`qts.risk.kill_switch.KillSwitchScope.global_scope`, `qts.risk.kill_switch.KillSwitchScope.account`, `qts.risk.kill_switch.KillSwitchScope.broker`, `qts.risk.kill_switch.KillSwitchScope.strategy`
- 被以下仓库内部符号调用：`qts.risk.kill_switch.KillSwitchRegistry.check_order`

### `qts.risk.risk_engine`

模块：`qts.risk.risk_engine`

#### `qts.risk.risk_engine.RiskEngine`
- 位置：`backend/src/qts/risk/risk_engine.py:11`
- 类型：`class`
- 签名：`class RiskEngine`
- 作用：Apply risk rules in order and return the first rejection.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine.__init__`, `qts.backtest.engine.BacktestEngine.from_config`

#### `qts.risk.risk_engine.RiskEngine.__init__`
- 位置：`backend/src/qts/risk/risk_engine.py:14`
- 类型：`method`
- 签名：`def __init__(self, rules: Iterable[RiskRule]) -> None`
- 作用：Perform __init__.
- 直接原始调用：`tuple`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.risk.risk_engine.RiskEngine.check`
- 位置：`backend/src/qts/risk/risk_engine.py:18`
- 类型：`method`
- 签名：`def check(self, request: OrderRiskRequest) -> RiskDecision`
- 作用：Perform check.
- 直接原始调用：`RiskDecision.approve`, `rule.check`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.risk.rule`

模块：`qts.risk.rule`

#### `qts.risk.rule.RiskRule`
- 位置：`backend/src/qts/risk/rule.py:10`
- 类型：`class`
- 签名：`class RiskRule(Protocol)`
- 作用：A pre-trade risk rule.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.risk.rule.RiskRule.check`
- 位置：`backend/src/qts/risk/rule.py:13`
- 类型：`method`
- 签名：`def check(self, request: OrderRiskRequest) -> RiskDecision`
- 作用：Return an explicit risk decision.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.risk.rule_registry`

模块：`qts.risk.rule_registry`

#### `qts.risk.rule_registry.RiskRuleRegistry`
- 位置：`backend/src/qts/risk/rule_registry.py:13`
- 类型：`class`
- 签名：`class RiskRuleRegistry`
- 作用：Map configured rule names to executable risk rules.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.risk.rule_registry.RiskRuleRegistry.build`
- 位置：`backend/src/qts/risk/rule_registry.py:16`
- 类型：`method`
- 签名：`def build(self, config: RiskRuleConfig) -> RiskRule`
- 作用：Perform build.
- 直接原始调用：`self._param` x2, `KeyError`, `MaxNotionalRule`, `MaxOrderQuantityRule`
- 已解析到仓库内部的调用：`qts.risk.rules.max_notional.MaxNotionalRule`, `qts.risk.rule_registry.RiskRuleRegistry._param`, `qts.risk.rules.max_order_qty.MaxOrderQuantityRule`
- 被以下仓库内部符号调用：无

#### `qts.risk.rule_registry.RiskRuleRegistry._param`
- 位置：`backend/src/qts/risk/rule_registry.py:25`
- 类型：`staticmethod`
- 签名：`def _param(config: RiskRuleConfig, name: str) -> Decimal`
- 作用：Perform _param.
- 直接原始调用：`KeyError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.risk.rule_registry.RiskRuleRegistry.build`

### `qts.risk.rules.max_notional`

模块：`qts.risk.rules.max_notional`

#### `qts.risk.rules.max_notional.MaxNotionalRule`
- 位置：`backend/src/qts/risk/rules/max_notional.py:12`
- 类型：`class`
- 签名：`class MaxNotionalRule`
- 作用：Reject orders whose notional exceeds a fixed limit.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.engine.BacktestEngine.__init__`, `qts.backtest.engine.BacktestEngine.from_config`, `qts.risk.rule_registry.RiskRuleRegistry.build`

#### `qts.risk.rules.max_notional.MaxNotionalRule.__post_init__`
- 位置：`backend/src/qts/risk/rules/max_notional.py:17`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`Decimal`, `ValueError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.risk.rules.max_notional.MaxNotionalRule.check`
- 位置：`backend/src/qts/risk/rules/max_notional.py:22`
- 类型：`method`
- 签名：`def check(self, request: OrderRiskRequest) -> RiskDecision`
- 作用：Perform check.
- 直接原始调用：`RiskDecision.approve`, `RiskDecision.rejected`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.risk.rules.max_order_qty`

模块：`qts.risk.rules.max_order_qty`

#### `qts.risk.rules.max_order_qty.MaxOrderQuantityRule`
- 位置：`backend/src/qts/risk/rules/max_order_qty.py:12`
- 类型：`class`
- 签名：`class MaxOrderQuantityRule`
- 作用：Reject orders whose absolute quantity exceeds a fixed limit.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.risk.rule_registry.RiskRuleRegistry.build`

#### `qts.risk.rules.max_order_qty.MaxOrderQuantityRule.__post_init__`
- 位置：`backend/src/qts/risk/rules/max_order_qty.py:17`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`Decimal`, `ValueError`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.risk.rules.max_order_qty.MaxOrderQuantityRule.check`
- 位置：`backend/src/qts/risk/rules/max_order_qty.py:22`
- 类型：`method`
- 签名：`def check(self, request: OrderRiskRequest) -> RiskDecision`
- 作用：Perform check.
- 直接原始调用：`RiskDecision.approve`, `RiskDecision.rejected`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.risk.rules.trading_session_rule`

模块：`qts.risk.rules.trading_session_rule`

#### `qts.risk.rules.trading_session_rule.SessionLookup`
- 位置：`backend/src/qts/risk/rules/trading_session_rule.py:13`
- 类型：`class`
- 签名：`class SessionLookup(Protocol)`
- 作用：Calendar session lookup required by the rule.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.risk.rules.trading_session_rule.SessionLookup.session_for`
- 位置：`backend/src/qts/risk/rules/trading_session_rule.py:16`
- 类型：`method`
- 签名：`def session_for(self, calendar_id: str, session_date: date) -> MarketSession`
- 作用：Return the internal market session for the date.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.risk.rules.trading_session_rule.TradingSessionRule`
- 位置：`backend/src/qts/risk/rules/trading_session_rule.py:21`
- 类型：`class`
- 签名：`class TradingSessionRule`
- 作用：Reject orders whose order time is outside the configured session.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.risk.rules.trading_session_rule.TradingSessionRule.check`
- 位置：`backend/src/qts/risk/rules/trading_session_rule.py:28`
- 类型：`method`
- 签名：`def check(self, request: OrderRiskRequest) -> RiskDecision`
- 作用：Perform check.
- 直接原始调用：`RiskDecision.rejected` x2, `RiskDecision.approve`, `self.calendar_registry.session_for`, `session.interval.contains`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.runtime.actor`

模块：`qts.runtime.actor`

#### `qts.runtime.actor.Actor`
- 位置：`backend/src/qts/runtime/actor.py:8`
- 类型：`class`
- 签名：`class Actor(ABC)`
- 作用：Base actor that handles messages serially through an ActorRef.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.actor.Actor.handle`
- 位置：`backend/src/qts/runtime/actor.py:12`
- 类型：`method`
- 签名：`def handle(self, message: object) -> None`
- 作用：Handle one message.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.runtime.actor_ref`

模块：`qts.runtime.actor_ref`

#### `qts.runtime.actor_ref.ActorRef`
- 位置：`backend/src/qts/runtime/actor_ref.py:12`
- 类型：`class`
- 签名：`class ActorRef`
- 作用：Message-only reference to an actor mailbox.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.actor_loop.BacktestActorLoop._market_data_ref_for`, `qts.backtest.actor_loop.BacktestActorLoop.run`

#### `qts.runtime.actor_ref.ActorRef.tell`
- 位置：`backend/src/qts/runtime/actor_ref.py:18`
- 类型：`method`
- 签名：`def tell(self, message: object) -> None`
- 作用：Perform tell.
- 直接原始调用：`self.mailbox.put`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.actor_ref.ActorRef.process_one`
- 位置：`backend/src/qts/runtime/actor_ref.py:22`
- 类型：`method`
- 签名：`def process_one(self) -> bool`
- 作用：Perform process_one.
- 直接原始调用：`self.actor.handle`, `self.mailbox.empty`, `self.mailbox.get`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.actor_ref.ActorRef.process_all`

#### `qts.runtime.actor_ref.ActorRef.process_all`
- 位置：`backend/src/qts/runtime/actor_ref.py:29`
- 类型：`method`
- 签名：`def process_all(self) -> int`
- 作用：Perform process_all.
- 直接原始调用：`self.process_one`
- 已解析到仓库内部的调用：`qts.runtime.actor_ref.ActorRef.process_one`
- 被以下仓库内部符号调用：无

### `qts.runtime.actors.account_actor`

模块：`qts.runtime.actors.account_actor`

#### `qts.runtime.actors.account_actor.ApplyFill`
- 位置：`backend/src/qts/runtime/actors/account_actor.py:19`
- 类型：`class`
- 签名：`class ApplyFill`
- 作用：Message instructing AccountActor to apply a validated fill.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.actors.order_manager_actor.OrderManagerActor._handle_report`

#### `qts.runtime.actors.account_actor.AccountSnapshot`
- 位置：`backend/src/qts/runtime/actors/account_actor.py:28`
- 类型：`class`
- 签名：`class AccountSnapshot`
- 作用：Read-only account snapshot.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.actors.account_actor.AccountActor.snapshot`

#### `qts.runtime.actors.account_actor.AccountActor`
- 位置：`backend/src/qts/runtime/actors/account_actor.py:35`
- 类型：`class`
- 签名：`class AccountActor(Actor)`
- 作用：Owns account cash and position state.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.actor_loop.BacktestActorLoop.run`

#### `qts.runtime.actors.account_actor.AccountActor.__init__`
- 位置：`backend/src/qts/runtime/actors/account_actor.py:38`
- 类型：`method`
- 签名：`def __init__(self, initial_cash: Mapping[str, Decimal] | None=None) -> None`
- 作用：Perform __init__.
- 直接原始调用：`CashBook`, `FillIdempotencyStore`, `PositionBook`
- 已解析到仓库内部的调用：`qts.portfolio.cash_book.CashBook`, `qts.portfolio.position_book.PositionBook`, `qts.execution.idempotency.FillIdempotencyStore`
- 被以下仓库内部符号调用：无

#### `qts.runtime.actors.account_actor.AccountActor.handle`
- 位置：`backend/src/qts/runtime/actors/account_actor.py:44`
- 类型：`method`
- 签名：`def handle(self, message: object) -> None`
- 作用：Perform handle.
- 直接原始调用：`TypeError`, `isinstance`, `self._apply_fill`, `type`
- 已解析到仓库内部的调用：`qts.runtime.actors.account_actor.AccountActor._apply_fill`
- 被以下仓库内部符号调用：无

#### `qts.runtime.actors.account_actor.AccountActor.snapshot`
- 位置：`backend/src/qts/runtime/actors/account_actor.py:51`
- 类型：`method`
- 签名：`def snapshot(self) -> AccountSnapshot`
- 作用：Perform snapshot.
- 直接原始调用：`AccountSnapshot`, `MappingProxyType`, `self._cash.balance`, `self._positions.snapshot`
- 已解析到仓库内部的调用：`qts.runtime.actors.account_actor.AccountSnapshot`
- 被以下仓库内部符号调用：无

#### `qts.runtime.actors.account_actor.AccountActor._apply_fill`
- 位置：`backend/src/qts/runtime/actors/account_actor.py:58`
- 类型：`method`
- 签名：`def _apply_fill(self, message: ApplyFill) -> None`
- 作用：Perform _apply_fill.
- 直接原始调用：`self._cash.apply_delta`, `self._fill_ids.mark_seen`, `self._positions.apply_delta`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.actors.account_actor.AccountActor.handle`

### `qts.runtime.actors.execution_actor`

模块：`qts.runtime.actors.execution_actor`

#### `qts.runtime.actors.execution_actor.ExecutionAdapter`
- 位置：`backend/src/qts/runtime/actors/execution_actor.py:15`
- 类型：`class`
- 签名：`class ExecutionAdapter(Protocol)`
- 作用：Execution boundary contract used by the actor.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.actors.execution_actor.ExecutionAdapter.execute_market_order`
- 位置：`backend/src/qts/runtime/actors/execution_actor.py:18`
- 类型：`method`
- 签名：`def execute_market_order(self, intent: OrderIntent, *, broker_order_id: str, market_price: Decimal) -> ExecutionReport`
- 作用：Execute a market order.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.actors.execution_actor.OrderExecutionRequest`
- 位置：`backend/src/qts/runtime/actors/execution_actor.py:30`
- 类型：`class`
- 签名：`class OrderExecutionRequest`
- 作用：Message requesting order execution.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.actors.order_manager_actor.OrderManagerActor._handle_submit`

#### `qts.runtime.actors.execution_actor.ExecutionActor`
- 位置：`backend/src/qts/runtime/actors/execution_actor.py:38`
- 类型：`class`
- 签名：`class ExecutionActor(Actor)`
- 作用：Actor wrapper for an order execution adapter or simulator.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.actor_loop.BacktestActorLoop.run`

#### `qts.runtime.actors.execution_actor.ExecutionActor.__init__`
- 位置：`backend/src/qts/runtime/actors/execution_actor.py:41`
- 类型：`method`
- 签名：`def __init__(self, *, order_manager_ref: ActorRef, execution_adapter: ExecutionAdapter | None=None) -> None`
- 作用：未写 docstring；静态推断为所属类上的 `  init  ` 行为。
- 直接原始调用：`SimulatedBroker`
- 已解析到仓库内部的调用：`qts.execution.simulator.simulated_broker.SimulatedBroker`
- 被以下仓库内部符号调用：无

#### `qts.runtime.actors.execution_actor.ExecutionActor.handle`
- 位置：`backend/src/qts/runtime/actors/execution_actor.py:50`
- 类型：`method`
- 签名：`def handle(self, message: object) -> None`
- 作用：Perform handle.
- 直接原始调用：`TypeError`, `isinstance`, `self._execution_adapter.execute_market_order`, `self._order_manager_ref.tell`, `type`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.runtime.actors.market_data_actor`

模块：`qts.runtime.actors.market_data_actor`

#### `qts.runtime.actors.market_data_actor.MarketDataEvent`
- 位置：`backend/src/qts/runtime/actors/market_data_actor.py:29`
- 类型：`class`
- 签名：`class MarketDataEvent`
- 作用：Normalized market data payload accepted by MarketDataActor.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.actor_loop.BacktestActorLoop.run`

#### `qts.runtime.actors.market_data_actor.SubscribeMarketData`
- 位置：`backend/src/qts/runtime/actors/market_data_actor.py:36`
- 类型：`class`
- 签名：`class SubscribeMarketData`
- 作用：Message requesting strategy market data fan-out.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.actors.market_data_actor.SubscribeMarketData.__post_init__`
- 位置：`backend/src/qts/runtime/actors/market_data_actor.py:44`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError` x2, `self.subscriber_id.strip`, `self.timeframe.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.actors.market_data_actor.MarketDataActor`
- 位置：`backend/src/qts/runtime/actors/market_data_actor.py:52`
- 类型：`class`
- 签名：`class MarketDataActor(Actor)`
- 作用：Actor boundary for normalized market data events.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.actor_loop.BacktestActorLoop._market_data_ref_for`

#### `qts.runtime.actors.market_data_actor.MarketDataActor.__init__`
- 位置：`backend/src/qts/runtime/actors/market_data_actor.py:55`
- 类型：`method`
- 签名：`def __init__(self, subscribers: Iterable[ActorRef]=(), *, aggregate_timeframe: str | None=None, exchange_timezone: str | tzinfo | None=None, feed: LiveFeedAdapter | None=None) -> None`
- 作用：Perform __init__.
- 直接原始调用：`BarAggregationPipeline`, `Timeframe.parse`, `ValueError`, `set`, `tuple`
- 已解析到仓库内部的调用：`qts.data.bars.timeframe.Timeframe.parse`, `qts.data.bars.pipeline.BarAggregationPipeline`
- 被以下仓库内部符号调用：无

#### `qts.runtime.actors.market_data_actor.MarketDataActor.handle`
- 位置：`backend/src/qts/runtime/actors/market_data_actor.py:79`
- 类型：`method`
- 签名：`def handle(self, message: object) -> None`
- 作用：Perform handle.
- 直接原始调用：`isinstance` x3, `self._publish` x2, `RuntimeError`, `TypeError`, `self._aggregation_pipeline.aggregate`, `self._publish_to_logical_subscribers`, `self._subscribe`, `type`
- 已解析到仓库内部的调用：`qts.runtime.actors.market_data_actor.MarketDataActor._subscribe`, `qts.runtime.actors.market_data_actor.MarketDataActor._publish`, `qts.runtime.actors.market_data_actor.MarketDataActor._publish_to_logical_subscribers`
- 被以下仓库内部符号调用：无

#### `qts.runtime.actors.market_data_actor.MarketDataActor.logical_subscription_count`
- 位置：`backend/src/qts/runtime/actors/market_data_actor.py:102`
- 类型：`property`
- 签名：`def logical_subscription_count(self) -> int`
- 作用：Perform logical_subscription_count.
- 直接原始调用：`len`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.actors.market_data_actor.MarketDataActor.physical_subscription_count`
- 位置：`backend/src/qts/runtime/actors/market_data_actor.py:107`
- 类型：`property`
- 签名：`def physical_subscription_count(self) -> int`
- 作用：Perform physical_subscription_count.
- 直接原始调用：`len`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.actors.market_data_actor.MarketDataActor._subscribe`
- 位置：`backend/src/qts/runtime/actors/market_data_actor.py:111`
- 类型：`method`
- 签名：`def _subscribe(self, message: SubscribeMarketData) -> None`
- 作用：Perform _subscribe.
- 直接原始调用：`FeedSubscription`, `LogicalSubscription`, `logical_key`, `plan_physical_subscription`, `self._feed.subscribe`, `self._logical_subscribers.setdefault`, `self._physical_subscriptions.add`, `self._source_timeframe_by_logical.setdefault`, `self._subscription_id`
- 已解析到仓库内部的调用：`qts.data.subscriptions.LogicalSubscription`, `qts.data.subscriptions.logical_key`, `qts.data.subscriptions.plan_physical_subscription`, `qts.data.live_feed.FeedSubscription`, `qts.runtime.actors.market_data_actor.MarketDataActor._subscription_id`
- 被以下仓库内部符号调用：`qts.runtime.actors.market_data_actor.MarketDataActor.handle`

#### `qts.runtime.actors.market_data_actor.MarketDataActor._publish_to_logical_subscribers`
- 位置：`backend/src/qts/runtime/actors/market_data_actor.py:142`
- 类型：`method`
- 签名：`def _publish_to_logical_subscribers(self, payload: MarketDataPayload) -> None`
- 作用：Perform _publish_to_logical_subscribers.
- 直接原始调用：`self._publish_to` x2, `subscribers.values` x2, `RuntimeError`, `isinstance`, `self._aggregation_pipeline.aggregate_logical`, `self._logical_subscribers.items`, `self._publish`
- 已解析到仓库内部的调用：`qts.runtime.actors.market_data_actor.MarketDataActor._publish`, `qts.runtime.actors.market_data_actor.MarketDataActor._publish_to`
- 被以下仓库内部符号调用：`qts.runtime.actors.market_data_actor.MarketDataActor.handle`

#### `qts.runtime.actors.market_data_actor.MarketDataActor._publish`
- 位置：`backend/src/qts/runtime/actors/market_data_actor.py:169`
- 类型：`method`
- 签名：`def _publish(self, payload: MarketDataPayload) -> None`
- 作用：Perform _publish.
- 直接原始调用：`subscriber.tell`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.actors.market_data_actor.MarketDataActor._publish_to_logical_subscribers`, `qts.runtime.actors.market_data_actor.MarketDataActor.handle`

#### `qts.runtime.actors.market_data_actor.MarketDataActor._publish_to`
- 位置：`backend/src/qts/runtime/actors/market_data_actor.py:175`
- 类型：`staticmethod`
- 签名：`def _publish_to(subscribers: Iterable[ActorRef], payload: MarketDataPayload) -> None`
- 作用：Perform _publish_to.
- 直接原始调用：`subscriber.tell`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.actors.market_data_actor.MarketDataActor._publish_to_logical_subscribers`

#### `qts.runtime.actors.market_data_actor.MarketDataActor._subscription_id`
- 位置：`backend/src/qts/runtime/actors/market_data_actor.py:181`
- 类型：`staticmethod`
- 签名：`def _subscription_id(key: PhysicalSubscriptionKey) -> str`
- 作用：Perform _subscription_id.
- 直接原始调用：`':'.join`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.actors.market_data_actor.MarketDataActor._subscribe`

### `qts.runtime.actors.order_manager_actor`

模块：`qts.runtime.actors.order_manager_actor`

#### `qts.runtime.actors.order_manager_actor.SubmitOrder`
- 位置：`backend/src/qts/runtime/actors/order_manager_actor.py:19`
- 类型：`class`
- 签名：`class SubmitOrder`
- 作用：Message to submit an approved order to an execution actor.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.intent_processor.BacktestIntentProcessor._process_order_delta`

#### `qts.runtime.actors.order_manager_actor.OrderManagerActor`
- 位置：`backend/src/qts/runtime/actors/order_manager_actor.py:28`
- 类型：`class`
- 签名：`class OrderManagerActor(Actor)`
- 作用：Actor-owned OrderManager wrapper.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.actor_loop.BacktestActorLoop.run`

#### `qts.runtime.actors.order_manager_actor.OrderManagerActor.__init__`
- 位置：`backend/src/qts/runtime/actors/order_manager_actor.py:31`
- 类型：`method`
- 签名：`def __init__(self, *, execution_ref: ActorRef, account_ref: ActorRef, multiplier_by_instrument: Mapping[InstrumentId, Decimal] | None=None) -> None`
- 作用：Perform __init__.
- 直接原始调用：`OrderManager`, `dict`
- 已解析到仓库内部的调用：`qts.execution.order_manager.OrderManager`
- 被以下仓库内部符号调用：无

#### `qts.runtime.actors.order_manager_actor.OrderManagerActor.handle`
- 位置：`backend/src/qts/runtime/actors/order_manager_actor.py:45`
- 类型：`method`
- 签名：`def handle(self, message: object) -> None`
- 作用：Perform handle.
- 直接原始调用：`isinstance` x2, `TypeError`, `self._handle_report`, `self._handle_submit`, `type`
- 已解析到仓库内部的调用：`qts.runtime.actors.order_manager_actor.OrderManagerActor._handle_submit`, `qts.runtime.actors.order_manager_actor.OrderManagerActor._handle_report`
- 被以下仓库内部符号调用：无

#### `qts.runtime.actors.order_manager_actor.OrderManagerActor.get_order`
- 位置：`backend/src/qts/runtime/actors/order_manager_actor.py:55`
- 类型：`method`
- 签名：`def get_order(self, order_id: OrderId) -> Order`
- 作用：Perform get_order.
- 直接原始调用：`self._manager.get_order`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.actors.order_manager_actor.OrderManagerActor.fills`
- 位置：`backend/src/qts/runtime/actors/order_manager_actor.py:60`
- 类型：`property`
- 签名：`def fills(self) -> tuple[OrderFill, ...]`
- 作用：Perform fills.
- 直接原始调用：`tuple`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.actors.order_manager_actor.OrderManagerActor.fill_count`
- 位置：`backend/src/qts/runtime/actors/order_manager_actor.py:65`
- 类型：`property`
- 签名：`def fill_count(self) -> int`
- 作用：Perform fill_count.
- 直接原始调用：`len`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.actors.order_manager_actor.OrderManagerActor.fills_since`
- 位置：`backend/src/qts/runtime/actors/order_manager_actor.py:69`
- 类型：`method`
- 签名：`def fills_since(self, index: int) -> tuple[OrderFill, ...]`
- 作用：Perform fills_since.
- 直接原始调用：`tuple`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.actors.order_manager_actor.OrderManagerActor.compact_for_streaming`
- 位置：`backend/src/qts/runtime/actors/order_manager_actor.py:73`
- 类型：`method`
- 签名：`def compact_for_streaming(self, order_ids: Iterable[OrderId]) -> None`
- 作用：Perform compact_for_streaming.
- 直接原始调用：`self._fills.clear`, `self._manager.discard_terminal_order`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.actors.order_manager_actor.OrderManagerActor._handle_submit`
- 位置：`backend/src/qts/runtime/actors/order_manager_actor.py:79`
- 类型：`method`
- 签名：`def _handle_submit(self, message: SubmitOrder) -> None`
- 作用：Perform _handle_submit.
- 直接原始调用：`OrderExecutionRequest`, `self._execution_ref.tell`, `self._manager.create_order`, `self._manager.mark_sent`
- 已解析到仓库内部的调用：`qts.runtime.actors.execution_actor.OrderExecutionRequest`
- 被以下仓库内部符号调用：`qts.runtime.actors.order_manager_actor.OrderManagerActor.handle`

#### `qts.runtime.actors.order_manager_actor.OrderManagerActor._handle_report`
- 位置：`backend/src/qts/runtime/actors/order_manager_actor.py:91`
- 类型：`method`
- 签名：`def _handle_report(self, message: ExecutionReport) -> None`
- 作用：Perform _handle_report.
- 直接原始调用：`ApplyFill`, `Decimal`, `self._account_ref.tell`, `self._fills.append`, `self._manager.process_report`, `self._multiplier_by_instrument.get`
- 已解析到仓库内部的调用：`qts.runtime.actors.account_actor.ApplyFill`
- 被以下仓库内部符号调用：`qts.runtime.actors.order_manager_actor.OrderManagerActor.handle`

### `qts.runtime.actors.signal_aggregator_actor`

模块：`qts.runtime.actors.signal_aggregator_actor`

#### `qts.runtime.actors.signal_aggregator_actor.StrategySignalEvent`
- 位置：`backend/src/qts/runtime/actors/signal_aggregator_actor.py:14`
- 类型：`class`
- 签名：`class StrategySignalEvent`
- 作用：Strategy intents emitted for one completed bar.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.actor_loop.BacktestActorLoop.run`

#### `qts.runtime.actors.signal_aggregator_actor.AggregatedSignalBatch`
- 位置：`backend/src/qts/runtime/actors/signal_aggregator_actor.py:22`
- 类型：`class`
- 签名：`class AggregatedSignalBatch`
- 作用：Aggregated intents ready for portfolio/risk/order flow.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.actors.signal_aggregator_actor.SignalAggregatorActor.handle`

#### `qts.runtime.actors.signal_aggregator_actor.SignalAggregatorActor`
- 位置：`backend/src/qts/runtime/actors/signal_aggregator_actor.py:29`
- 类型：`class`
- 签名：`class SignalAggregatorActor(Actor)`
- 作用：Boundary for combining strategy signals before order flow.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.actors.signal_aggregator_actor.SignalAggregatorActor.__init__`
- 位置：`backend/src/qts/runtime/actors/signal_aggregator_actor.py:32`
- 类型：`method`
- 签名：`def __init__(self, *, result_ref: ActorRef) -> None`
- 作用：Perform __init__.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.actors.signal_aggregator_actor.SignalAggregatorActor.handle`
- 位置：`backend/src/qts/runtime/actors/signal_aggregator_actor.py:36`
- 类型：`method`
- 签名：`def handle(self, message: object) -> None`
- 作用：Perform handle.
- 直接原始调用：`AggregatedSignalBatch`, `TypeError`, `isinstance`, `self._result_ref.tell`, `type`
- 已解析到仓库内部的调用：`qts.runtime.actors.signal_aggregator_actor.AggregatedSignalBatch`
- 被以下仓库内部符号调用：无

### `qts.runtime.actors.strategy_actor`

模块：`qts.runtime.actors.strategy_actor`

#### `qts.runtime.actors.strategy_actor.StrategyBarEvent`
- 位置：`backend/src/qts/runtime/actors/strategy_actor.py:14`
- 类型：`class`
- 签名：`class StrategyBarEvent`
- 作用：Completed strategy-facing bar delivered to a strategy actor.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.actor_loop.BacktestActorLoop.run`

#### `qts.runtime.actors.strategy_actor.StrategyBarResult`
- 位置：`backend/src/qts/runtime/actors/strategy_actor.py:23`
- 类型：`class`
- 签名：`class StrategyBarResult`
- 作用：New strategy intents emitted while handling one bar.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.actors.strategy_actor.StrategyActor._handle_bar`

#### `qts.runtime.actors.strategy_actor.StrategyFinalize`
- 位置：`backend/src/qts/runtime/actors/strategy_actor.py:31`
- 类型：`class`
- 签名：`class StrategyFinalize`
- 作用：Request strategy finalization.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.actor_loop.BacktestActorLoop.run`

#### `qts.runtime.actors.strategy_actor.StrategyFinalized`
- 位置：`backend/src/qts/runtime/actors/strategy_actor.py:36`
- 类型：`class`
- 签名：`class StrategyFinalized`
- 作用：Strategy finalization completed.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.actors.strategy_actor.StrategyActor._handle_finalize`

#### `qts.runtime.actors.strategy_actor.StrategyActor`
- 位置：`backend/src/qts/runtime/actors/strategy_actor.py:42`
- 类型：`class`
- 签名：`class StrategyActor(Actor)`
- 作用：Actor-owned strategy instance and user-facing context.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.actors.strategy_actor.StrategyActor.__init__`
- 位置：`backend/src/qts/runtime/actors/strategy_actor.py:45`
- 类型：`method`
- 签名：`def __init__(self, *, strategy: Strategy, context: StrategyContext, result_ref: ActorRef) -> None`
- 作用：Perform __init__.
- 直接原始调用：`self._strategy.initialize`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.actors.strategy_actor.StrategyActor.handle`
- 位置：`backend/src/qts/runtime/actors/strategy_actor.py:58`
- 类型：`method`
- 签名：`def handle(self, message: object) -> None`
- 作用：Perform handle.
- 直接原始调用：`isinstance` x2, `TypeError`, `self._handle_bar`, `self._handle_finalize`, `type`
- 已解析到仓库内部的调用：`qts.runtime.actors.strategy_actor.StrategyActor._handle_bar`, `qts.runtime.actors.strategy_actor.StrategyActor._handle_finalize`
- 被以下仓库内部符号调用：无

#### `qts.runtime.actors.strategy_actor.StrategyActor._handle_bar`
- 位置：`backend/src/qts/runtime/actors/strategy_actor.py:68`
- 类型：`method`
- 签名：`def _handle_bar(self, message: StrategyBarEvent) -> None`
- 作用：Perform _handle_bar.
- 直接原始调用：`StrategyBarResult`, `len`, `self._context.indicator.update_from_bar`, `self._result_ref.tell`, `self._strategy.on_bar`
- 已解析到仓库内部的调用：`qts.runtime.actors.strategy_actor.StrategyBarResult`
- 被以下仓库内部符号调用：`qts.runtime.actors.strategy_actor.StrategyActor.handle`

#### `qts.runtime.actors.strategy_actor.StrategyActor._handle_finalize`
- 位置：`backend/src/qts/runtime/actors/strategy_actor.py:82`
- 类型：`method`
- 签名：`def _handle_finalize(self) -> None`
- 作用：Perform _handle_finalize.
- 直接原始调用：`StrategyFinalized`, `len`, `self._result_ref.tell`, `self._strategy.finalize`
- 已解析到仓库内部的调用：`qts.runtime.actors.strategy_actor.StrategyFinalized`
- 被以下仓库内部符号调用：`qts.runtime.actors.strategy_actor.StrategyActor.handle`

### `qts.runtime.event_store`

模块：`qts.runtime.event_store`

#### `qts.runtime.event_store.EventStore`
- 位置：`backend/src/qts/runtime/event_store.py:15`
- 类型：`class`
- 签名：`class EventStore(Protocol)`
- 作用：Append-only event store contract.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.event_store.EventStore.append`
- 位置：`backend/src/qts/runtime/event_store.py:18`
- 类型：`method`
- 签名：`def append(self, event: BaseEvent) -> int`
- 作用：Append an event to the store and return its sequence index.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.event_store.EventStore.replay`
- 位置：`backend/src/qts/runtime/event_store.py:22`
- 类型：`method`
- 签名：`def replay(self, *, partition_key: str | None=None) -> tuple[BaseEvent, ...]`
- 作用：Replay events from the store, optionally filtered by partition key.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.event_store.EventStore.by_correlation_id`
- 位置：`backend/src/qts/runtime/event_store.py:26`
- 类型：`method`
- 签名：`def by_correlation_id(self, correlation_id: CorrelationId) -> tuple[BaseEvent, ...]`
- 作用：Replay all events with a given correlation identifier.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.event_store.InMemoryEventStore`
- 位置：`backend/src/qts/runtime/event_store.py:31`
- 类型：`class`
- 签名：`class InMemoryEventStore`
- 作用：Deterministic append-only in-memory event store.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.event_store.InMemoryEventStore.__init__`
- 位置：`backend/src/qts/runtime/event_store.py:34`
- 类型：`method`
- 签名：`def __init__(self) -> None`
- 作用：Perform __init__.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.event_store.InMemoryEventStore.append`
- 位置：`backend/src/qts/runtime/event_store.py:38`
- 类型：`method`
- 签名：`def append(self, event: BaseEvent) -> int`
- 作用：Perform append.
- 直接原始调用：`len`, `self._events.append`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.event_store.InMemoryEventStore.append_many`

#### `qts.runtime.event_store.InMemoryEventStore.append_many`
- 位置：`backend/src/qts/runtime/event_store.py:43`
- 类型：`method`
- 签名：`def append_many(self, events: Iterable[BaseEvent]) -> None`
- 作用：Perform append_many.
- 直接原始调用：`self.append`
- 已解析到仓库内部的调用：`qts.runtime.event_store.InMemoryEventStore.append`
- 被以下仓库内部符号调用：无

#### `qts.runtime.event_store.InMemoryEventStore.replay`
- 位置：`backend/src/qts/runtime/event_store.py:48`
- 类型：`method`
- 签名：`def replay(self, *, partition_key: str | None=None) -> tuple[BaseEvent, ...]`
- 作用：Perform replay.
- 直接原始调用：`tuple` x2
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.event_store.InMemoryEventStore.by_correlation_id`
- 位置：`backend/src/qts/runtime/event_store.py:54`
- 类型：`method`
- 签名：`def by_correlation_id(self, correlation_id: CorrelationId) -> tuple[BaseEvent, ...]`
- 作用：Perform by_correlation_id.
- 直接原始调用：`tuple`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.event_store.FileEventStore`
- 位置：`backend/src/qts/runtime/event_store.py:59`
- 类型：`class`
- 签名：`class FileEventStore`
- 作用：JSONL event store for local deterministic recovery tests.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.event_store.FileEventStore.__init__`
- 位置：`backend/src/qts/runtime/event_store.py:62`
- 类型：`method`
- 签名：`def __init__(self, path: Path) -> None`
- 作用：Perform __init__.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.event_store.FileEventStore.append`
- 位置：`backend/src/qts/runtime/event_store.py:66`
- 类型：`method`
- 签名：`def append(self, event: BaseEvent) -> int`
- 作用：Perform append.
- 直接原始调用：`handle.write` x2, `json.dumps`, `len`, `self._event_to_json`, `self._path.open`, `self._path.parent.mkdir`, `self.replay`
- 已解析到仓库内部的调用：`qts.runtime.event_store.FileEventStore.replay`, `qts.runtime.event_store.FileEventStore._event_to_json`
- 被以下仓库内部符号调用：无

#### `qts.runtime.event_store.FileEventStore.replay`
- 位置：`backend/src/qts/runtime/event_store.py:76`
- 类型：`method`
- 签名：`def replay(self, *, partition_key: str | None=None) -> tuple[BaseEvent, ...]`
- 作用：Perform replay.
- 直接原始调用：`events.append`, `json.loads`, `line.strip`, `self._event_from_json`, `self._path.exists`, `self._path.open`, `tuple`
- 已解析到仓库内部的调用：`qts.runtime.event_store.FileEventStore._event_from_json`
- 被以下仓库内部符号调用：`qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.FileEventStore.by_correlation_id`

#### `qts.runtime.event_store.FileEventStore.by_correlation_id`
- 位置：`backend/src/qts/runtime/event_store.py:90`
- 类型：`method`
- 签名：`def by_correlation_id(self, correlation_id: CorrelationId) -> tuple[BaseEvent, ...]`
- 作用：Perform by_correlation_id.
- 直接原始调用：`self.replay`, `tuple`
- 已解析到仓库内部的调用：`qts.runtime.event_store.FileEventStore.replay`
- 被以下仓库内部符号调用：无

#### `qts.runtime.event_store.FileEventStore._event_to_json`
- 位置：`backend/src/qts/runtime/event_store.py:95`
- 类型：`staticmethod`
- 签名：`def _event_to_json(event: BaseEvent) -> dict[str, Any]`
- 作用：Perform _event_to_json.
- 直接原始调用：`event.event_time.isoformat`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.event_store.FileEventStore.append`

#### `qts.runtime.event_store.FileEventStore._event_from_json`
- 位置：`backend/src/qts/runtime/event_store.py:108`
- 类型：`staticmethod`
- 签名：`def _event_from_json(payload: dict[str, Any]) -> BaseEvent`
- 作用：Perform _event_from_json.
- 直接原始调用：`str` x7, `BaseEvent`, `CausationId`, `CorrelationId`, `EventId`, `datetime.fromisoformat`
- 已解析到仓库内部的调用：`qts.core.ids.EventId`, `qts.core.ids.CorrelationId`, `qts.core.ids.CausationId`
- 被以下仓库内部符号调用：`qts.runtime.event_store.FileEventStore.replay`

### `qts.runtime.live`

模块：`qts.runtime.live`

#### `qts.runtime.live.LiveRuntimeState`
- 位置：`backend/src/qts/runtime/live.py:12`
- 类型：`class`
- 签名：`class LiveRuntimeState(StrEnum)`
- 作用：Live runtime lifecycle states.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.live.LiveMode`
- 位置：`backend/src/qts/runtime/live.py:22`
- 类型：`class`
- 签名：`class LiveMode(StrEnum)`
- 作用：Runtime mode with explicit live-trading permissions.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.live.LiveStartupConfig`
- 位置：`backend/src/qts/runtime/live.py:31`
- 类型：`class`
- 签名：`class LiveStartupConfig`
- 作用：Startup guard inputs for live-capable runtime.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.live.LiveStartupDecision`
- 位置：`backend/src/qts/runtime/live.py:43`
- 类型：`class`
- 签名：`class LiveStartupDecision`
- 作用：Result of startup guard validation.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.live.validate_live_startup`

#### `qts.runtime.live.validate_live_startup`
- 位置：`backend/src/qts/runtime/live.py:50`
- 类型：`module_function`
- 签名：`def validate_live_startup(config: LiveStartupConfig) -> LiveStartupDecision`
- 作用：Fail closed unless all live safety prerequisites are explicit.
- 直接原始调用：`', '.join`, `LiveStartupDecision`, `ValueError`
- 已解析到仓库内部的调用：`qts.runtime.live.LiveStartupDecision`
- 被以下仓库内部符号调用：无

#### `qts.runtime.live.LiveRuntimeStateMachine`
- 位置：`backend/src/qts/runtime/live.py:97`
- 类型：`class`
- 签名：`class LiveRuntimeStateMachine`
- 作用：Mutable live runtime state machine.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.live.LiveRuntime.__init__`

#### `qts.runtime.live.LiveRuntimeStateMachine.apply`
- 位置：`backend/src/qts/runtime/live.py:102`
- 类型：`method`
- 签名：`def apply(self, command: str) -> LiveRuntimeState`
- 作用：Perform apply.
- 直接原始调用：`ValueError`, `_TRANSITIONS.get`, `_TRANSITIONS.get.get`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.live.RuntimeOrderResult`
- 位置：`backend/src/qts/runtime/live.py:112`
- 类型：`class`
- 签名：`class RuntimeOrderResult`
- 作用：Result of live runtime order submission.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.live.LiveRuntime.submit_order`

#### `qts.runtime.live.LiveRuntime`
- 位置：`backend/src/qts/runtime/live.py:121`
- 类型：`class`
- 签名：`class LiveRuntime`
- 作用：Small live-beta runtime wrapper over fake or real boundary adapters.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.live.LiveRuntime.__init__`
- 位置：`backend/src/qts/runtime/live.py:124`
- 类型：`method`
- 签名：`def __init__(self, *, broker: BrokerAdapter, feed: LiveFeedAdapter) -> None`
- 作用：未写 docstring；静态推断为所属类上的 `  init  ` 行为。
- 直接原始调用：`LiveRuntimeStateMachine`
- 已解析到仓库内部的调用：`qts.runtime.live.LiveRuntimeStateMachine`
- 被以下仓库内部符号调用：无

#### `qts.runtime.live.LiveRuntime.state`
- 位置：`backend/src/qts/runtime/live.py:130`
- 类型：`property`
- 签名：`def state(self) -> LiveRuntimeState`
- 作用：Perform state.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.live.LiveRuntime.feed`
- 位置：`backend/src/qts/runtime/live.py:135`
- 类型：`property`
- 签名：`def feed(self) -> LiveFeedAdapter`
- 作用：Perform feed.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.live.LiveRuntime.start`
- 位置：`backend/src/qts/runtime/live.py:139`
- 类型：`method`
- 签名：`def start(self) -> LiveRuntimeState`
- 作用：Perform start.
- 直接原始调用：`self._machine.apply` x2
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.live.LiveRuntime.stop`
- 位置：`backend/src/qts/runtime/live.py:144`
- 类型：`method`
- 签名：`def stop(self) -> LiveRuntimeState`
- 作用：Perform stop.
- 直接原始调用：`self._machine.apply`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.live.LiveRuntime.pause`
- 位置：`backend/src/qts/runtime/live.py:148`
- 类型：`method`
- 签名：`def pause(self) -> LiveRuntimeState`
- 作用：Perform pause.
- 直接原始调用：`self._machine.apply`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.live.LiveRuntime.resume`
- 位置：`backend/src/qts/runtime/live.py:152`
- 类型：`method`
- 签名：`def resume(self) -> LiveRuntimeState`
- 作用：Perform resume.
- 直接原始调用：`self._machine.apply`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.live.LiveRuntime.degrade`
- 位置：`backend/src/qts/runtime/live.py:156`
- 类型：`method`
- 签名：`def degrade(self) -> LiveRuntimeState`
- 作用：Perform degrade.
- 直接原始调用：`self._machine.apply`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.live.LiveRuntime.recover`
- 位置：`backend/src/qts/runtime/live.py:160`
- 类型：`method`
- 签名：`def recover(self) -> LiveRuntimeState`
- 作用：Perform recover.
- 直接原始调用：`self._machine.apply`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.live.LiveRuntime.submit_order`
- 位置：`backend/src/qts/runtime/live.py:164`
- 类型：`method`
- 签名：`def submit_order(self, request: BrokerOrderRequest) -> RuntimeOrderResult`
- 作用：Perform submit_order.
- 直接原始调用：`RuntimeOrderResult` x3, `self._broker.submit_order`
- 已解析到仓库内部的调用：`qts.runtime.live.RuntimeOrderResult`
- 被以下仓库内部符号调用：无

### `qts.runtime.mailbox`

模块：`qts.runtime.mailbox`

#### `qts.runtime.mailbox.Mailbox`
- 位置：`backend/src/qts/runtime/mailbox.py:8`
- 类型：`class`
- 签名：`class Mailbox`
- 作用：Simple in-memory FIFO mailbox.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.backtest.actor_loop.BacktestActorLoop._market_data_ref_for`, `qts.backtest.actor_loop.BacktestActorLoop.run`

#### `qts.runtime.mailbox.Mailbox.__init__`
- 位置：`backend/src/qts/runtime/mailbox.py:11`
- 类型：`method`
- 签名：`def __init__(self) -> None`
- 作用：Perform __init__.
- 直接原始调用：`deque`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.mailbox.Mailbox.size`
- 位置：`backend/src/qts/runtime/mailbox.py:16`
- 类型：`property`
- 签名：`def size(self) -> int`
- 作用：Perform size.
- 直接原始调用：`len`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.mailbox.Mailbox.put`
- 位置：`backend/src/qts/runtime/mailbox.py:20`
- 类型：`method`
- 签名：`def put(self, message: object) -> None`
- 作用：Perform put.
- 直接原始调用：`self._messages.append`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.mailbox.Mailbox.get`
- 位置：`backend/src/qts/runtime/mailbox.py:24`
- 类型：`method`
- 签名：`def get(self) -> object`
- 作用：Perform get.
- 直接原始调用：`self._messages.popleft`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.mailbox.Mailbox.empty`
- 位置：`backend/src/qts/runtime/mailbox.py:28`
- 类型：`method`
- 签名：`def empty(self) -> bool`
- 作用：Perform empty.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.runtime.partitioning`

模块：`qts.runtime.partitioning`

#### `qts.runtime.partitioning.AccountPartitionPolicy`
- 位置：`backend/src/qts/runtime/partitioning.py:11`
- 类型：`class`
- 签名：`class AccountPartitionPolicy`
- 作用：Partition live state and messages by internal account id.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.partitioning.AccountPartitionPolicy.partition_for`
- 位置：`backend/src/qts/runtime/partitioning.py:14`
- 类型：`method`
- 签名：`def partition_for(self, account_id: AccountId) -> str`
- 作用：Perform partition_for.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.partitioning.AccountBrokerMapping`
- 位置：`backend/src/qts/runtime/partitioning.py:20`
- 类型：`class`
- 签名：`class AccountBrokerMapping`
- 作用：Boundary-only broker account mapping.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.partitioning.AccountBrokerMapping.__post_init__`
- 位置：`backend/src/qts/runtime/partitioning.py:27`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError`, `self.broker_account_id.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.partitioning.AccountBrokerMapping.boundary_payload`
- 位置：`backend/src/qts/runtime/partitioning.py:32`
- 类型：`method`
- 签名：`def boundary_payload(self) -> dict[str, str]`
- 作用：Perform boundary_payload.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.partitioning.AccountRiskConfig`
- 位置：`backend/src/qts/runtime/partitioning.py:41`
- 类型：`class`
- 签名：`class AccountRiskConfig`
- 作用：Per-account live risk limits.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.partitioning.AccountRiskConfig.__post_init__`
- 位置：`backend/src/qts/runtime/partitioning.py:48`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`Decimal` x2, `ValueError` x2, `any`, `self.instrument_limits.values`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.partitioning.AccountRiskConfig.limit_for`
- 位置：`backend/src/qts/runtime/partitioning.py:55`
- 类型：`method`
- 签名：`def limit_for(self, instrument_id: InstrumentId) -> Decimal`
- 作用：Perform limit_for.
- 直接原始调用：`self.instrument_limits.get`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.runtime.router`

模块：`qts.runtime.router`

#### `qts.runtime.router.RouteNotFoundError`
- 位置：`backend/src/qts/runtime/router.py:10`
- 类型：`class`
- 签名：`class RouteNotFoundError(KeyError)`
- 作用：Raised when no actor route exists for a partition key.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.runtime.router.EventRouter.route`

#### `qts.runtime.router.EventRouter`
- 位置：`backend/src/qts/runtime/router.py:14`
- 类型：`class`
- 签名：`class EventRouter`
- 作用：Route messages to actor refs by a message-derived key.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.router.EventRouter.__init__`
- 位置：`backend/src/qts/runtime/router.py:17`
- 类型：`method`
- 签名：`def __init__(self, *, key_for: Callable[[object], Hashable]) -> None`
- 作用：Perform __init__.
- 直接原始调用：`TypeError`, `callable`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.router.EventRouter.register`
- 位置：`backend/src/qts/runtime/router.py:24`
- 类型：`method`
- 签名：`def register(self, key: object, actor_ref: ActorRef) -> None`
- 作用：Perform register.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.router.EventRouter.route`
- 位置：`backend/src/qts/runtime/router.py:28`
- 类型：`method`
- 签名：`def route(self, message: object) -> None`
- 作用：Perform route.
- 直接原始调用：`RouteNotFoundError`, `actor_ref.tell`, `self._key_for`
- 已解析到仓库内部的调用：`qts.runtime.router.RouteNotFoundError`
- 被以下仓库内部符号调用：无

### `qts.runtime.state_recovery`

模块：`qts.runtime.state_recovery`

#### `qts.runtime.state_recovery.StateSnapshot`
- 位置：`backend/src/qts/runtime/state_recovery.py:10`
- 类型：`class`
- 签名：`class StateSnapshot`
- 作用：Serialized actor state snapshot envelope.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.state_recovery.StateSnapshot.__post_init__`
- 位置：`backend/src/qts/runtime/state_recovery.py:17`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError` x2, `self.actor_id.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.state_recovery.InMemorySnapshotStore`
- 位置：`backend/src/qts/runtime/state_recovery.py:25`
- 类型：`class`
- 签名：`class InMemorySnapshotStore`
- 作用：In-memory snapshot store for deterministic tests and local recovery.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.state_recovery.InMemorySnapshotStore.__init__`
- 位置：`backend/src/qts/runtime/state_recovery.py:28`
- 类型：`method`
- 签名：`def __init__(self) -> None`
- 作用：Perform __init__.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.state_recovery.InMemorySnapshotStore.save`
- 位置：`backend/src/qts/runtime/state_recovery.py:32`
- 类型：`method`
- 签名：`def save(self, snapshot: StateSnapshot) -> None`
- 作用：Perform save.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.runtime.state_recovery.InMemorySnapshotStore.load`
- 位置：`backend/src/qts/runtime/state_recovery.py:36`
- 类型：`method`
- 签名：`def load(self, actor_id: str) -> StateSnapshot | None`
- 作用：Perform load.
- 直接原始调用：`ValueError`, `actor_id.strip`, `self._snapshots.get`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.strategy_sdk.asset_ref`

模块：`qts.strategy_sdk.asset_ref`

#### `qts.strategy_sdk.asset_ref.AssetRef`
- 位置：`backend/src/qts/strategy_sdk/asset_ref.py:13`
- 类型：`class`
- 签名：`class AssetRef`
- 作用：Lightweight strategy-facing reference to an internal instrument.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.strategy_sdk.asset_resolver.StrategyAssetResolver.resolve_future`, `qts.strategy_sdk.asset_resolver.StrategyAssetResolver.resolve_option`, `qts.strategy_sdk.asset_resolver.StrategyAssetResolver.resolve_symbol`

#### `qts.strategy_sdk.asset_ref.AssetRef.__post_init__`
- 位置：`backend/src/qts/strategy_sdk/asset_ref.py:20`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`MappingProxyType`, `ValueError`, `dict`, `object.__setattr__`, `self.symbol.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.asset_ref.AssetRef.__hash__`
- 位置：`backend/src/qts/strategy_sdk/asset_ref.py:26`
- 类型：`method`
- 签名：`def __hash__(self) -> int`
- 作用：Perform __hash__.
- 直接原始调用：`hash`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.strategy_sdk.asset_resolver`

模块：`qts.strategy_sdk.asset_resolver`

#### `qts.strategy_sdk.asset_resolver.SymbolResolver`
- 位置：`backend/src/qts/strategy_sdk/asset_resolver.py:15`
- 类型：`class`
- 签名：`class SymbolResolver(Protocol)`
- 作用：Platform-provided symbol resolution boundary.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.asset_resolver.SymbolResolver.resolve`
- 位置：`backend/src/qts/strategy_sdk/asset_resolver.py:18`
- 类型：`method`
- 签名：`def resolve(self, user_symbol: str) -> InstrumentId`
- 作用：未写 docstring；静态推断为所属类上的 `resolve` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.asset_resolver.FutureContractResolver`
- 位置：`backend/src/qts/strategy_sdk/asset_resolver.py:21`
- 类型：`class`
- 签名：`class FutureContractResolver(Protocol)`
- 作用：Platform-provided future chain resolution boundary.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.asset_resolver.FutureContractResolver.resolve_contract`
- 位置：`backend/src/qts/strategy_sdk/asset_resolver.py:24`
- 类型：`method`
- 签名：`def resolve_contract(self, root_symbol: str, *, offset: int=0) -> InstrumentId`
- 作用：未写 docstring；静态推断为所属类上的 `resolve contract` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.asset_resolver.ContinuousFutureResolver`
- 位置：`backend/src/qts/strategy_sdk/asset_resolver.py:28`
- 类型：`class`
- 签名：`class ContinuousFutureResolver(Protocol)`
- 作用：Platform-provided continuous future reference boundary.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.asset_resolver.ContinuousFutureResolver.continuous_instrument_id`
- 位置：`backend/src/qts/strategy_sdk/asset_resolver.py:31`
- 类型：`method`
- 签名：`def continuous_instrument_id(self, root_symbol: str, *, offset: int=0) -> InstrumentId`
- 作用：未写 docstring；静态推断为所属类上的 `continuous instrument id` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.asset_resolver.OptionContractRef`
- 位置：`backend/src/qts/strategy_sdk/asset_resolver.py:34`
- 类型：`class`
- 签名：`class OptionContractRef(Protocol)`
- 作用：Read-only option contract reference returned by the platform.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.asset_resolver.OptionContractRef.instrument_id`
- 位置：`backend/src/qts/strategy_sdk/asset_resolver.py:38`
- 类型：`property`
- 签名：`def instrument_id(self) -> InstrumentId`
- 作用：未写 docstring；静态推断为所属类上的 `instrument id` 属性行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.asset_resolver.OptionContractResolver`
- 位置：`backend/src/qts/strategy_sdk/asset_resolver.py:41`
- 类型：`class`
- 签名：`class OptionContractResolver(Protocol)`
- 作用：Platform-provided option chain resolution boundary.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.asset_resolver.OptionContractResolver.find`
- 位置：`backend/src/qts/strategy_sdk/asset_resolver.py:44`
- 类型：`method`
- 签名：`def find(self, *, underlying: InstrumentId, expiry: date | None=None, strike: Decimal | None=None, right: OptionRight | None=None) -> Sequence[OptionContractRef]`
- 作用：未写 docstring；静态推断为所属类上的 `find` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.asset_resolver.StrategyAssetResolver`
- 位置：`backend/src/qts/strategy_sdk/asset_resolver.py:54`
- 类型：`class`
- 签名：`class StrategyAssetResolver`
- 作用：Resolve user input symbols/roots/options into stable `AssetRef` objects.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.strategy_sdk.context.StrategyContext.__post_init__`

#### `qts.strategy_sdk.asset_resolver.StrategyAssetResolver.__init__`
- 位置：`backend/src/qts/strategy_sdk/asset_resolver.py:57`
- 类型：`method`
- 签名：`def __init__(self, *, instrument_registry: SymbolResolver | None=None, future_chain_registry: FutureContractResolver | ContinuousFutureResolver | None=None, option_chain_registry: OptionContractResolver | None=None) -> None`
- 作用：未写 docstring；静态推断为所属类上的 `  init  ` 行为。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.asset_resolver.StrategyAssetResolver.resolve_symbol`
- 位置：`backend/src/qts/strategy_sdk/asset_resolver.py:68`
- 类型：`method`
- 签名：`def resolve_symbol(self, user_symbol: str) -> AssetRef`
- 作用：Perform resolve_symbol.
- 直接原始调用：`AssetRef`, `RuntimeError`, `self.instrument_registry.resolve`
- 已解析到仓库内部的调用：`qts.strategy_sdk.asset_ref.AssetRef`
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.asset_resolver.StrategyAssetResolver.resolve_future`
- 位置：`backend/src/qts/strategy_sdk/asset_resolver.py:75`
- 类型：`method`
- 签名：`def resolve_future(self, root_symbol: str, *, contract: str='front') -> AssetRef`
- 作用：Perform resolve_future.
- 直接原始调用：`AssetRef`, `RuntimeError`, `ValueError`, `isinstance`, `self.future_chain_registry.continuous_instrument_id`, `self.future_chain_registry.resolve_contract`
- 已解析到仓库内部的调用：`qts.strategy_sdk.asset_ref.AssetRef`
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.asset_resolver.StrategyAssetResolver.resolve_option`
- 位置：`backend/src/qts/strategy_sdk/asset_resolver.py:93`
- 类型：`method`
- 签名：`def resolve_option(self, *, underlying: InstrumentId, expiry: date, strike: Decimal, right: OptionRight) -> AssetRef`
- 作用：Perform resolve_option.
- 直接原始调用：`AssetRef`, `KeyError`, `RuntimeError`, `self.option_chain_registry.find`, `str`
- 已解析到仓库内部的调用：`qts.strategy_sdk.asset_ref.AssetRef`
- 被以下仓库内部符号调用：无

### `qts.strategy_sdk.context`

模块：`qts.strategy_sdk.context`

#### `qts.strategy_sdk.context.StrategyContext`
- 位置：`backend/src/qts/strategy_sdk/context.py:30`
- 类型：`class`
- 签名：`class StrategyContext`
- 作用：User-facing strategy context.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.context.StrategyContext.__post_init__`
- 位置：`backend/src/qts/strategy_sdk/context.py:46`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`StrategyAssetResolver`
- 已解析到仓库内部的调用：`qts.strategy_sdk.asset_resolver.StrategyAssetResolver`
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.context.StrategyContext.intents`
- 位置：`backend/src/qts/strategy_sdk/context.py:55`
- 类型：`property`
- 签名：`def intents(self) -> tuple[TargetIntent, ...]`
- 作用：Perform intents.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.context.StrategyContext.subscriptions`
- 位置：`backend/src/qts/strategy_sdk/context.py:60`
- 类型：`property`
- 签名：`def subscriptions(self) -> tuple[DataSubscription, ...]`
- 作用：Perform subscriptions.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.context.StrategyContext.symbol`
- 位置：`backend/src/qts/strategy_sdk/context.py:64`
- 类型：`method`
- 签名：`def symbol(self, user_symbol: str) -> AssetRef`
- 作用：Perform symbol.
- 直接原始调用：`self._asset_resolver.resolve_symbol`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.context.StrategyContext.future`
- 位置：`backend/src/qts/strategy_sdk/context.py:68`
- 类型：`method`
- 签名：`def future(self, root_symbol: str, *, contract: str='front') -> AssetRef`
- 作用：Perform future.
- 直接原始调用：`self._asset_resolver.resolve_future`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.context.StrategyContext.option`
- 位置：`backend/src/qts/strategy_sdk/context.py:72`
- 类型：`method`
- 签名：`def option(self, *, underlying: InstrumentId, expiry: date, strike: Decimal, right: OptionRight) -> AssetRef`
- 作用：Perform option.
- 直接原始调用：`self._asset_resolver.resolve_option`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.context.StrategyContext.target_percent`
- 位置：`backend/src/qts/strategy_sdk/context.py:88`
- 类型：`method`
- 签名：`def target_percent(self, asset: AssetRef, weight: Decimal) -> TargetIntent`
- 作用：Perform target_percent.
- 直接原始调用：`TargetIntent`, `self._intent_emitter.emit`
- 已解析到仓库内部的调用：`qts.strategy_sdk.target.TargetIntent`
- 被以下仓库内部符号调用：`qts.strategy_sdk.context.StrategyContext.rebalance`

#### `qts.strategy_sdk.context.StrategyContext.target_quantity`
- 位置：`backend/src/qts/strategy_sdk/context.py:94`
- 类型：`method`
- 签名：`def target_quantity(self, asset: AssetRef, quantity: Decimal) -> TargetIntent`
- 作用：Perform target_quantity.
- 直接原始调用：`TargetIntent`, `self._intent_emitter.emit`
- 已解析到仓库内部的调用：`qts.strategy_sdk.target.TargetIntent`
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.context.StrategyContext.target_value`
- 位置：`backend/src/qts/strategy_sdk/context.py:100`
- 类型：`method`
- 签名：`def target_value(self, asset: AssetRef, value: Decimal) -> TargetIntent`
- 作用：Perform target_value.
- 直接原始调用：`TargetIntent`, `self._intent_emitter.emit`
- 已解析到仓库内部的调用：`qts.strategy_sdk.target.TargetIntent`
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.context.StrategyContext.close`
- 位置：`backend/src/qts/strategy_sdk/context.py:106`
- 类型：`method`
- 签名：`def close(self, asset: AssetRef) -> TargetIntent`
- 作用：Perform close.
- 直接原始调用：`TargetIntent`, `self._intent_emitter.emit`
- 已解析到仓库内部的调用：`qts.strategy_sdk.target.TargetIntent`
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.context.StrategyContext.rebalance`
- 位置：`backend/src/qts/strategy_sdk/context.py:112`
- 类型：`method`
- 签名：`def rebalance(self, weights: dict[AssetRef, Decimal]) -> tuple[TargetIntent, ...]`
- 作用：Perform rebalance.
- 直接原始调用：`self.target_percent`, `tuple`, `weights.items`
- 已解析到仓库内部的调用：`qts.strategy_sdk.context.StrategyContext.target_percent`
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.context.StrategyContext.subscribe`
- 位置：`backend/src/qts/strategy_sdk/context.py:116`
- 类型：`method`
- 签名：`def subscribe(self, asset: AssetRef, *, timeframe: str, warmup: int=1) -> DataSubscription`
- 作用：Perform subscribe.
- 直接原始调用：`DataSubscription`, `self._subscription_registry.subscribe`
- 已解析到仓库内部的调用：`qts.strategy_sdk.subscription_registry.DataSubscription`
- 被以下仓库内部符号调用：无

### `qts.strategy_sdk.data_view`

模块：`qts.strategy_sdk.data_view`

#### `qts.strategy_sdk.data_view.DataView`
- 位置：`backend/src/qts/strategy_sdk/data_view.py:16`
- 类型：`class`
- 签名：`class DataView`
- 作用：Time-sliced market data exposed to strategies.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.data_view.DataView.close`
- 位置：`backend/src/qts/strategy_sdk/data_view.py:22`
- 类型：`method`
- 签名：`def close(self, asset: AssetRef) -> Decimal`
- 作用：Perform close.
- 直接原始调用：`self.bar`
- 已解析到仓库内部的调用：`qts.strategy_sdk.data_view.DataView.bar`
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.data_view.DataView.bar`
- 位置：`backend/src/qts/strategy_sdk/data_view.py:26`
- 类型：`method`
- 签名：`def bar(self, asset: AssetRef) -> Bar`
- 作用：Perform bar.
- 直接原始调用：`KeyError`, `self.history`
- 已解析到仓库内部的调用：`qts.strategy_sdk.data_view.DataView.history`
- 被以下仓库内部符号调用：`qts.strategy_sdk.data_view.DataView.close`

#### `qts.strategy_sdk.data_view.DataView.history`
- 位置：`backend/src/qts/strategy_sdk/data_view.py:33`
- 类型：`method`
- 签名：`def history(self, asset: AssetRef, bars: int, timeframe: str | None=None) -> tuple[Bar, ...]`
- 作用：Perform history.
- 直接原始调用：`ValueError`, `self.bars.get`, `tuple`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.strategy_sdk.data_view.DataView.bar`

### `qts.strategy_sdk.factors`

模块：`qts.strategy_sdk.factors`

#### `qts.strategy_sdk.factors.FactorFactory`
- 位置：`backend/src/qts/strategy_sdk/factors.py:11`
- 类型：`class`
- 签名：`class FactorFactory`
- 作用：Factory for user-created factors.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.factors.FactorFactory.momentum`
- 位置：`backend/src/qts/strategy_sdk/factors.py:14`
- 类型：`method`
- 签名：`def momentum(self, *, window: int) -> MomentumFactor`
- 作用：Perform momentum.
- 直接原始调用：`MomentumFactor`
- 已解析到仓库内部的调用：`qts.factors.momentum.MomentumFactor`
- 被以下仓库内部符号调用：无

### `qts.strategy_sdk.indicators`

模块：`qts.strategy_sdk.indicators`

#### `qts.strategy_sdk.indicators.AssetIndicator`
- 位置：`backend/src/qts/strategy_sdk/indicators.py:14`
- 类型：`class`
- 签名：`class AssetIndicator`
- 作用：Indicator bound to a strategy asset reference.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.strategy_sdk.indicators.IndicatorFactory.sma`

#### `qts.strategy_sdk.indicators.AssetIndicator.ready`
- 位置：`backend/src/qts/strategy_sdk/indicators.py:21`
- 类型：`property`
- 签名：`def ready(self) -> bool`
- 作用：Perform ready.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.indicators.AssetIndicator.value`
- 位置：`backend/src/qts/strategy_sdk/indicators.py:26`
- 类型：`property`
- 签名：`def value(self) -> Decimal | None`
- 作用：Perform value.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.indicators.AssetIndicator.update`
- 位置：`backend/src/qts/strategy_sdk/indicators.py:30`
- 类型：`method`
- 签名：`def update(self, price: Decimal) -> Decimal | None`
- 作用：Perform update.
- 直接原始调用：`self.indicator.update`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.indicators.IndicatorFactory`
- 位置：`backend/src/qts/strategy_sdk/indicators.py:36`
- 类型：`class`
- 签名：`class IndicatorFactory`
- 作用：Factory for user-created indicators.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.indicators.IndicatorFactory.sma`
- 位置：`backend/src/qts/strategy_sdk/indicators.py:41`
- 类型：`method`
- 签名：`def sma(self, asset: AssetRef, window: int) -> AssetIndicator`
- 作用：Perform sma.
- 直接原始调用：`AssetIndicator`, `SMA`, `self._created.append`
- 已解析到仓库内部的调用：`qts.strategy_sdk.indicators.AssetIndicator`, `qts.indicators.price.sma.SMA`
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.indicators.IndicatorFactory.update_from_bar`
- 位置：`backend/src/qts/strategy_sdk/indicators.py:47`
- 类型：`method`
- 签名：`def update_from_bar(self, bar: Bar) -> None`
- 作用：Perform update_from_bar.
- 直接原始调用：`item.update`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.strategy_sdk.portfolio_view`

模块：`qts.strategy_sdk.portfolio_view`

#### `qts.strategy_sdk.portfolio_view.PortfolioPosition`
- 位置：`backend/src/qts/strategy_sdk/portfolio_view.py:15`
- 类型：`class`
- 签名：`class PortfolioPosition`
- 作用：Read-only position snapshot.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.strategy_sdk.portfolio_view.PortfolioView.position`

#### `qts.strategy_sdk.portfolio_view.PortfolioView`
- 位置：`backend/src/qts/strategy_sdk/portfolio_view.py:23`
- 类型：`class`
- 签名：`class PortfolioView`
- 作用：Immutable user-facing portfolio snapshot.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.portfolio_view.PortfolioView.__post_init__`
- 位置：`backend/src/qts/strategy_sdk/portfolio_view.py:30`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`MappingProxyType`, `dict`, `object.__setattr__`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.portfolio_view.PortfolioView.position`
- 位置：`backend/src/qts/strategy_sdk/portfolio_view.py:34`
- 类型：`method`
- 签名：`def position(self, asset: AssetRef) -> PortfolioPosition`
- 作用：Perform position.
- 直接原始调用：`PortfolioPosition`, `self.positions.get`
- 已解析到仓库内部的调用：`qts.strategy_sdk.portfolio_view.PortfolioPosition`
- 被以下仓库内部符号调用：`qts.strategy_sdk.portfolio_view.PortfolioView.exposure`

#### `qts.strategy_sdk.portfolio_view.PortfolioView.exposure`
- 位置：`backend/src/qts/strategy_sdk/portfolio_view.py:38`
- 类型：`method`
- 签名：`def exposure(self, asset: AssetRef) -> Decimal`
- 作用：Perform exposure.
- 直接原始调用：`self.position`
- 已解析到仓库内部的调用：`qts.strategy_sdk.portfolio_view.PortfolioView.position`
- 被以下仓库内部符号调用：`qts.strategy_sdk.portfolio_view.PortfolioView.weight`

#### `qts.strategy_sdk.portfolio_view.PortfolioView.weight`
- 位置：`backend/src/qts/strategy_sdk/portfolio_view.py:42`
- 类型：`method`
- 签名：`def weight(self, asset: AssetRef) -> Decimal`
- 作用：Perform weight.
- 直接原始调用：`Decimal` x2, `self.exposure`
- 已解析到仓库内部的调用：`qts.strategy_sdk.portfolio_view.PortfolioView.exposure`
- 被以下仓库内部符号调用：无

### `qts.strategy_sdk.strategy`

模块：`qts.strategy_sdk.strategy`

#### `qts.strategy_sdk.strategy.Strategy`
- 位置：`backend/src/qts/strategy_sdk/strategy.py:6`
- 类型：`class`
- 签名：`class Strategy`
- 作用：Base class for user strategies.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.strategy.Strategy.initialize`
- 位置：`backend/src/qts/strategy_sdk/strategy.py:9`
- 类型：`method`
- 签名：`def initialize(self, ctx: object) -> None`
- 作用：Perform initialize.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.strategy.Strategy.on_bar`
- 位置：`backend/src/qts/strategy_sdk/strategy.py:13`
- 类型：`method`
- 签名：`def on_bar(self, ctx: object, bar: object) -> None`
- 作用：Perform on_bar.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.strategy.Strategy.on_tick`
- 位置：`backend/src/qts/strategy_sdk/strategy.py:17`
- 类型：`method`
- 签名：`def on_tick(self, ctx: object, tick: object) -> None`
- 作用：Perform on_tick.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.strategy.Strategy.on_timer`
- 位置：`backend/src/qts/strategy_sdk/strategy.py:21`
- 类型：`method`
- 签名：`def on_timer(self, ctx: object, timer: object) -> None`
- 作用：Perform on_timer.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.strategy.Strategy.on_order_update`
- 位置：`backend/src/qts/strategy_sdk/strategy.py:25`
- 类型：`method`
- 签名：`def on_order_update(self, ctx: object, update: object) -> None`
- 作用：Perform on_order_update.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.strategy.Strategy.on_fill`
- 位置：`backend/src/qts/strategy_sdk/strategy.py:29`
- 类型：`method`
- 签名：`def on_fill(self, ctx: object, fill: object) -> None`
- 作用：Perform on_fill.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.strategy.Strategy.finalize`
- 位置：`backend/src/qts/strategy_sdk/strategy.py:33`
- 类型：`method`
- 签名：`def finalize(self, ctx: object) -> None`
- 作用：Perform finalize.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.strategy_sdk.subscription_registry`

模块：`qts.strategy_sdk.subscription_registry`

#### `qts.strategy_sdk.subscription_registry.DataSubscription`
- 位置：`backend/src/qts/strategy_sdk/subscription_registry.py:11`
- 类型：`class`
- 签名：`class DataSubscription`
- 作用：Strategy-declared market data requirement.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.strategy_sdk.context.StrategyContext.subscribe`

#### `qts.strategy_sdk.subscription_registry.DataSubscription.__post_init__`
- 位置：`backend/src/qts/strategy_sdk/subscription_registry.py:18`
- 类型：`method`
- 签名：`def __post_init__(self) -> None`
- 作用：Perform __post_init__.
- 直接原始调用：`ValueError` x2, `self.timeframe.strip`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.subscription_registry.StrategySubscriptionRegistry`
- 位置：`backend/src/qts/strategy_sdk/subscription_registry.py:26`
- 类型：`class`
- 签名：`class StrategySubscriptionRegistry`
- 作用：Own strategy subscriptions and enforce invariant validation.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.subscription_registry.StrategySubscriptionRegistry.__init__`
- 位置：`backend/src/qts/strategy_sdk/subscription_registry.py:29`
- 类型：`method`
- 签名：`def __init__(self) -> None`
- 作用：Perform __init__.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.subscription_registry.StrategySubscriptionRegistry.subscriptions`
- 位置：`backend/src/qts/strategy_sdk/subscription_registry.py:34`
- 类型：`property`
- 签名：`def subscriptions(self) -> tuple[DataSubscription, ...]`
- 作用：Perform subscriptions.
- 直接原始调用：`tuple`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.subscription_registry.StrategySubscriptionRegistry.subscribe`
- 位置：`backend/src/qts/strategy_sdk/subscription_registry.py:38`
- 类型：`method`
- 签名：`def subscribe(self, subscription: DataSubscription) -> DataSubscription`
- 作用：Perform subscribe.
- 直接原始调用：`self._subscriptions.append`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `qts.strategy_sdk.target`

模块：`qts.strategy_sdk.target`

#### `qts.strategy_sdk.target.TargetIntentType`
- 位置：`backend/src/qts/strategy_sdk/target.py:12`
- 类型：`class`
- 签名：`class TargetIntentType(StrEnum)`
- 作用：Supported target intent kinds.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.target.TargetIntent`
- 位置：`backend/src/qts/strategy_sdk/target.py:22`
- 类型：`class`
- 签名：`class TargetIntent`
- 作用：Strategy-emitted intent, later handled by platform risk/order flow.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`qts.strategy_sdk.context.StrategyContext.close`, `qts.strategy_sdk.context.StrategyContext.target_percent`, `qts.strategy_sdk.context.StrategyContext.target_quantity`, `qts.strategy_sdk.context.StrategyContext.target_value`

### `qts.strategy_sdk.target_emitter`

模块：`qts.strategy_sdk.target_emitter`

#### `qts.strategy_sdk.target_emitter.TargetIntentEmitter`
- 位置：`backend/src/qts/strategy_sdk/target_emitter.py:8`
- 类型：`class`
- 签名：`class TargetIntentEmitter`
- 作用：Collect and emit `TargetIntent` values for one strategy context.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.target_emitter.TargetIntentEmitter.__init__`
- 位置：`backend/src/qts/strategy_sdk/target_emitter.py:11`
- 类型：`method`
- 签名：`def __init__(self) -> None`
- 作用：Perform __init__.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.target_emitter.TargetIntentEmitter.intents`
- 位置：`backend/src/qts/strategy_sdk/target_emitter.py:16`
- 类型：`property`
- 签名：`def intents(self) -> tuple[TargetIntent, ...]`
- 作用：Perform intents.
- 直接原始调用：`tuple`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `qts.strategy_sdk.target_emitter.TargetIntentEmitter.emit`
- 位置：`backend/src/qts/strategy_sdk/target_emitter.py:20`
- 类型：`method`
- 签名：`def emit(self, intent: TargetIntent) -> TargetIntent`
- 作用：Perform emit.
- 直接原始调用：`self._intents.append`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `examples.strategies.gc_si_momentum`

模块：`examples.strategies.gc_si_momentum`

#### `examples.strategies.gc_si_momentum.GcSiMomentumStrategy`
- 位置：`examples/strategies/gc_si_momentum.py:12`
- 类型：`class`
- 签名：`class GcSiMomentumStrategy(Strategy)`
- 作用：Simple moving-average momentum strategy for configured GC/SI symbols.
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `examples.strategies.gc_si_momentum.GcSiMomentumStrategy.__init__`
- 位置：`examples/strategies/gc_si_momentum.py:15`
- 类型：`method`
- 签名：`def __init__(self, *, symbols: Iterable[str]=('GC', 'SI'), short_window: int=1, long_window: int=2) -> None`
- 作用：未写 docstring；静态推断为所属类上的 `  init  ` 行为。
- 直接原始调用：`ValueError` x3, `tuple`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `examples.strategies.gc_si_momentum.GcSiMomentumStrategy.initialize`
- 位置：`examples/strategies/gc_si_momentum.py:33`
- 类型：`method`
- 签名：`def initialize(self, ctx: StrategyContext) -> None`
- 作用：未写 docstring；静态推断为所属类上的 `initialize` 行为。
- 直接原始调用：`_asset_for_symbol`, `ctx.subscribe`, `tuple`
- 已解析到仓库内部的调用：`examples.strategies.gc_si_momentum._asset_for_symbol`
- 被以下仓库内部符号调用：无

#### `examples.strategies.gc_si_momentum.GcSiMomentumStrategy.on_bar`
- 位置：`examples/strategies/gc_si_momentum.py:38`
- 类型：`method`
- 签名：`def on_bar(self, ctx: Any, bar: object) -> None`
- 作用：未写 docstring；静态推断为所属类上的 `on bar` 行为。
- 直接原始调用：`_average` x2, `Decimal`, `ctx.close`, `ctx.data.history`, `ctx.target_quantity`, `len`
- 已解析到仓库内部的调用：`examples.strategies.gc_si_momentum._average`
- 被以下仓库内部符号调用：无

#### `examples.strategies.gc_si_momentum._average`
- 位置：`examples/strategies/gc_si_momentum.py:55`
- 类型：`module_function`
- 签名：`def _average(values: Iterable[Decimal]) -> Decimal`
- 作用：未写 docstring；静态推断为 ` average` 函数，具体语义以实现为准。
- 直接原始调用：`Decimal` x2, `len`, `sum`, `tuple`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`examples.strategies.gc_si_momentum.GcSiMomentumStrategy.on_bar`

#### `examples.strategies.gc_si_momentum._asset_for_symbol`
- 位置：`examples/strategies/gc_si_momentum.py:60`
- 类型：`module_function`
- 签名：`def _asset_for_symbol(ctx: StrategyContext, symbol: str) -> AssetRef`
- 作用：未写 docstring；静态推断为 ` asset for symbol` 函数，具体语义以实现为准。
- 直接原始调用：`ctx.future`, `ctx.symbol`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：`examples.strategies.gc_si_momentum.GcSiMomentumStrategy.initialize`

### `examples.strategies.moving_average_cross`

模块：`examples.strategies.moving_average_cross`

#### `examples.strategies.moving_average_cross.MovingAverageCross`
- 位置：`examples/strategies/moving_average_cross.py:8`
- 类型：`class`
- 签名：`class MovingAverageCross(Strategy)`
- 作用：未写 docstring；静态推断为定义类对应的领域概念。
- 直接原始调用：无
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `examples.strategies.moving_average_cross.MovingAverageCross.initialize`
- 位置：`examples/strategies/moving_average_cross.py:9`
- 类型：`method`
- 签名：`def initialize(self, ctx)`
- 作用：未写 docstring；静态推断为所属类上的 `initialize` 行为。
- 直接原始调用：`ctx.indicator.sma` x2, `ctx.symbol`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

#### `examples.strategies.moving_average_cross.MovingAverageCross.on_bar`
- 位置：`examples/strategies/moving_average_cross.py:14`
- 类型：`method`
- 签名：`def on_bar(self, ctx, data)`
- 作用：未写 docstring；静态推断为所属类上的 `on bar` 行为。
- 直接原始调用：`Decimal`, `ctx.close`, `ctx.data.close`, `ctx.target_percent`, `self.fast.update`, `self.slow.update`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `scripts.bootstrap`

模块：`scripts.bootstrap`

#### `scripts.bootstrap.main`
- 位置：`scripts/bootstrap.py:11`
- 类型：`module_function`
- 签名：`def main() -> None`
- 作用：Perform main.
- 直接原始调用：`Path`, `bootstrap_local`
- 已解析到仓库内部的调用：`qts.load.bootstrap.bootstrap_local`
- 被以下仓库内部符号调用：无

### `scripts.run_api`

模块：`scripts.run_api`

#### `scripts.run_api.main`
- 位置：`scripts/run_api.py:9`
- 类型：`module_function`
- 签名：`def main() -> int`
- 作用：Start the QTS FastAPI application server.
- 直接原始调用：`uvicorn.run`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `scripts.run_backtest`

模块：`scripts.run_backtest`

#### `scripts.run_backtest.main`
- 位置：`scripts/run_backtest.py:14`
- 类型：`module_function`
- 签名：`def main(argv: Sequence[str] | None=None) -> int`
- 作用：Perform main.
- 直接原始调用：`print` x11, `parser.add_argument` x2, `time.perf_counter` x2, `Path`, `argparse.ArgumentParser`, `json.dumps`, `json.loads`, `parser.parse_args`, `run.summary_path.read_text`, `run.summary_path.write_text`, `run_backtest`
- 已解析到仓库内部的调用：`qts.backtest.runner.run_backtest`
- 被以下仓库内部符号调用：无

### `scripts.run_load`

模块：`scripts.run_load`

#### `scripts.run_load.main`
- 位置：`scripts/run_load.py:13`
- 类型：`module_function`
- 签名：`def main() -> None`
- 作用：Perform main.
- 直接原始调用：`Decimal` x2, `InstrumentId`, `SyntheticMarketDataConfig`, `datetime`, `generate_bars`, `len`, `print`
- 已解析到仓库内部的调用：`qts.load.synthetic_market_data.generate_bars`, `qts.load.synthetic_market_data.SyntheticMarketDataConfig`, `qts.core.ids.InstrumentId`
- 被以下仓库内部符号调用：无

### `scripts.run_paper`

模块：`scripts.run_paper`

#### `scripts.run_paper.main`
- 位置：`scripts/run_paper.py:8`
- 类型：`module_function`
- 签名：`def main() -> None`
- 作用：Perform main.
- 直接原始调用：`Decimal`, `PaperRuntimeConfig`, `print`, `start_paper`
- 已解析到仓库内部的调用：`qts.application.commands.start_paper.start_paper`, `qts.application.commands.start_paper.PaperRuntimeConfig`
- 被以下仓库内部符号调用：无

### `scripts.run_paper_ibkr`

模块：`scripts.run_paper_ibkr`

#### `scripts.run_paper_ibkr.main`
- 位置：`scripts/run_paper_ibkr.py:9`
- 类型：`module_function`
- 签名：`def main() -> int`
- 作用：Run the IBKR paper order lifecycle drill command.
- 直接原始调用：`_run_paper_drill`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `scripts.run_worker`

模块：`scripts.run_worker`

#### `scripts.run_worker.main`
- 位置：`scripts/run_worker.py:7`
- 类型：`module_function`
- 签名：`def main() -> int`
- 作用：Emit compatibility-mode worker message for now.
- 直接原始调用：`print`
- 已解析到仓库内部的调用：无
- 被以下仓库内部符号调用：无

### `scripts.validate_historical`

模块：`scripts.validate_historical`

#### `scripts.validate_historical.main`
- 位置：`scripts/validate_historical.py:15`
- 类型：`module_function`
- 签名：`def main(argv: Sequence[str] | None=None) -> int`
- 作用：Perform main.
- 直接原始调用：`parser.add_argument` x5, `str` x3, `Path` x2, `HistoricalCatalog.from_legacy_root`, `argparse.ArgumentParser`, `args.output_dir.mkdir`, `bool`, `catalog.datasets.items`, `datetime.now`, `datetime.now.isoformat`, `json.dumps`, `list`, `output_path.write_text`, `parser.parse_args`, `print`, `sample.stats.as_dict`, `tuple`, `validate_historical_sample`
- 已解析到仓库内部的调用：`qts.data.historical.catalog.HistoricalCatalog.from_legacy_root`, `qts.data.historical.csv_dataset.validate_historical_sample`
- 被以下仓库内部符号调用：无

### `scripts.verify_guardrails`

模块：`scripts.verify_guardrails`

#### `scripts.verify_guardrails.main`
- 位置：`scripts/verify_guardrails.py:22`
- 类型：`module_function`
- 签名：`def main() -> int`
- 作用：Perform main.
- 直接原始调用：`_guardrails.main`
- 已解析到仓库内部的调用：`qts.quality.guardrails.main`
- 被以下仓库内部符号调用：无

## 内部调用边（静态解析）

| 来源 | 目标 |
|---|---|
| `examples.strategies.gc_si_momentum.GcSiMomentumStrategy.initialize` | `examples.strategies.gc_si_momentum._asset_for_symbol` |
| `examples.strategies.gc_si_momentum.GcSiMomentumStrategy.on_bar` | `examples.strategies.gc_si_momentum._average` |
| `qts.api.mappers.map_backtest_request_schema` | `qts.application.dto.backtest.BacktestRequestDTO` |
| `qts.api.mappers.map_backtest_run_dto` | `qts.api.schemas.backtest_schema.BacktestRunSchema` |
| `qts.api.routes.accounts.account_snapshot` | `qts.api.schemas.common.AccountSnapshotSchema` |
| `qts.api.routes.backtests.submit_backtest` | `qts.api.mappers.map_backtest_request_schema` |
| `qts.api.routes.backtests.submit_backtest` | `qts.api.mappers.map_backtest_run_dto` |
| `qts.api.routes.operations.activate_kill_switch` | `qts.api.routes.operations._require_operator` |
| `qts.api.routes.operations.activate_kill_switch` | `qts.api.mappers.map_kill_switch_state_dto` |
| `qts.api.routes.operations.activate_kill_switch` | `qts.api.routes.operations.KillSwitchResponse` |
| `qts.api.routes.operations.command` | `qts.api.mappers.map_runtime_state_dto` |
| `qts.api.routes.operations.command` | `qts.api.routes.operations.RuntimeCommandResponse` |
| `qts.api.routes.operations.command` | `qts.api.mappers.map_runtime_state_dto` |
| `qts.api.routes.operations.command` | `qts.api.routes.operations.RuntimeCommandResponse` |
| `qts.api.routes.operations.pause_runtime` | `qts.api.routes.operations._require_operator` |
| `qts.api.routes.operations.pause_runtime` | `qts.api.mappers.map_runtime_state_dto` |
| `qts.api.routes.operations.pause_runtime` | `qts.api.routes.operations.RuntimeCommandResponse` |
| `qts.api.routes.operations.pause_runtime` | `qts.api.routes.operations.command` |
| `qts.api.routes.operations.resume_runtime` | `qts.api.routes.operations._require_operator` |
| `qts.api.routes.operations.resume_runtime` | `qts.api.mappers.map_runtime_state_dto` |
| `qts.api.routes.operations.resume_runtime` | `qts.api.routes.operations.RuntimeCommandResponse` |
| `qts.api.routes.operations.resume_runtime` | `qts.api.routes.operations.command` |
| `qts.api.routes.orders.order_status` | `qts.api.schemas.common.OrderStatusSchema` |
| `qts.api.routes.strategies.list_strategies` | `qts.api.schemas.common.StrategyStatusSchema` |
| `qts.api.routes.strategies.start_strategy` | `qts.api.schemas.common.StrategyStatusSchema` |
| `qts.api.routes.strategies.stop_strategy` | `qts.api.schemas.common.StrategyStatusSchema` |
| `qts.api.websocket.fill_adapter.order_fill_to_stream_dto` | `qts.api.websocket.dtos.StreamEventDTO` |
| `qts.api.websocket.manager.WebSocketConnectionManager.broadcast` | `qts.api.websocket.manager.WebSocketConnectionManager.disconnect` |
| `qts.application.commands.ibkr_environment_evidence._collect_network_evidence` | `qts.application.commands.ibkr_environment_evidence._tcp_probe` |
| `qts.application.commands.ibkr_environment_evidence._evidence_filename` | `qts.application.commands.ibkr_environment_evidence._safe_label` |
| `qts.application.commands.ibkr_environment_evidence._merge_validation_errors` | `qts.config.ibkr.collect_validation_errors` |
| `qts.application.commands.ibkr_environment_evidence._read_config` | `qts.config.ibkr.IbkrEnvironmentConfig.from_yaml` |
| `qts.application.commands.ibkr_environment_evidence._summarize_config` | `qts.application.commands.ibkr_environment_evidence._env_ref_status` |
| `qts.application.commands.ibkr_environment_evidence.collect_environment_evidence` | `qts.application.commands.ibkr_environment_evidence._read_config` |
| `qts.application.commands.ibkr_environment_evidence.collect_environment_evidence` | `qts.application.commands.ibkr_environment_evidence._merge_validation_errors` |
| `qts.application.commands.ibkr_environment_evidence.collect_environment_evidence` | `qts.application.commands.ibkr_environment_evidence._collect_network_evidence` |
| `qts.application.commands.ibkr_environment_evidence.collect_environment_evidence` | `qts.application.commands.ibkr_environment_evidence._summarize_config` |
| `qts.application.commands.ibkr_environment_evidence.collect_environment_evidence` | `qts.application.commands.ibkr_environment_evidence._evidence_filename` |
| `qts.application.commands.ibkr_environment_evidence.main` | `qts.application.commands.ibkr_environment_evidence.collect_environment_evidence` |
| `qts.application.commands.ibkr_paper_order_lifecycle_drill._evidence_filename` | `qts.application.commands.ibkr_paper_order_lifecycle_drill._safe_label` |
| `qts.application.commands.ibkr_paper_order_lifecycle_drill._read_config` | `qts.config.ibkr.IbkrEnvironmentConfig.from_yaml` |
| `qts.application.commands.ibkr_paper_order_lifecycle_drill._validate_paper_only_ibkr_config` | `qts.config.ibkr.collect_validation_errors` |
| `qts.application.commands.ibkr_paper_order_lifecycle_drill.main` | `qts.application.commands.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill` |
| `qts.application.commands.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill` | `qts.application.commands.ibkr_paper_order_lifecycle_drill._read_config` |
| `qts.application.commands.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill` | `qts.application.commands.ibkr_paper_order_lifecycle_drill._validate_paper_only_ibkr_config` |
| `qts.application.commands.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill` | `qts.core.ids.OrderId` |
| `qts.application.commands.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill` | `qts.core.ids.AccountId` |
| `qts.application.commands.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill` | `qts.core.ids.InstrumentId` |
| `qts.application.commands.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill` | `qts.execution.order_manager.OrderManager` |
| `qts.application.commands.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill` | `qts.execution.broker.FakeBrokerAdapter` |
| `qts.application.commands.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill` | `qts.core.ids.BrokerId` |
| `qts.application.commands.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill` | `qts.execution.broker.BrokerOrderRequest` |
| `qts.application.commands.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill` | `qts.core.ids.StrategyId` |
| `qts.application.commands.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill` | `qts.execution.broker.normalize_broker_execution_report` |
| `qts.application.commands.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill` | `qts.application.commands.ibkr_paper_order_lifecycle_drill._summarize_config` |
| `qts.application.commands.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill` | `qts.application.commands.ibkr_paper_order_lifecycle_drill._execution_report_evidence` |
| `qts.application.commands.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill` | `qts.application.commands.ibkr_paper_order_lifecycle_drill._evidence_filename` |
| `qts.application.commands.start_paper.start_paper` | `qts.application.commands.start_paper.PaperRuntime` |
| `qts.application.services.operations.OperationsService.__init__` | `qts.risk.kill_switch.KillSwitchRegistry` |
| `qts.application.services.operations.OperationsService._scope_from_command` | `qts.risk.kill_switch.KillSwitchScopeType` |
| `qts.application.services.operations.OperationsService._scope_from_command` | `qts.risk.kill_switch.KillSwitchScope.global_scope` |
| `qts.application.services.operations.OperationsService._scope_from_command` | `qts.risk.kill_switch.KillSwitchScope` |
| `qts.application.services.operations.OperationsService.activate_kill_switch` | `qts.application.services.operations.OperationsService._scope_from_command` |
| `qts.application.services.strategy_service.StrategyLifecycleService.start` | `qts.application.services.strategy_service.StrategyLifecycleService._require_enabled` |
| `qts.application.services.strategy_service.StrategyLifecycleService.status` | `qts.application.services.strategy_service.StrategyLifecycleService._require_enabled` |
| `qts.application.services.strategy_service.StrategyLifecycleService.stop` | `qts.application.services.strategy_service.StrategyLifecycleService._require_enabled` |
| `qts.backtest.actor_loop.BacktestActorLoop._market_data_ref_for` | `qts.runtime.actor_ref.ActorRef` |
| `qts.backtest.actor_loop.BacktestActorLoop._market_data_ref_for` | `qts.runtime.actors.market_data_actor.MarketDataActor` |
| `qts.backtest.actor_loop.BacktestActorLoop._market_data_ref_for` | `qts.runtime.mailbox.Mailbox` |
| `qts.backtest.actor_loop.BacktestActorLoop.run` | `qts.runtime.actors.account_actor.AccountActor` |
| `qts.backtest.actor_loop.BacktestActorLoop.run` | `qts.runtime.actor_ref.ActorRef` |
| `qts.backtest.actor_loop.BacktestActorLoop.run` | `qts.runtime.mailbox.Mailbox` |
| `qts.backtest.actor_loop.BacktestActorLoop.run` | `qts.runtime.actors.order_manager_actor.OrderManagerActor` |
| `qts.backtest.actor_loop.BacktestActorLoop.run` | `qts.runtime.actors.execution_actor.ExecutionActor` |
| `qts.backtest.actor_loop.BacktestActorLoop.run` | `qts.backtest.actor_loop.BacktestActorLoop._resolve_actor_classes` |
| `qts.backtest.actor_loop.BacktestActorLoop.run` | `qts.backtest.actor_loop.BacktestActorLoop._history_limit_from_subscriptions` |
| `qts.backtest.actor_loop.BacktestActorLoop.run` | `qts.backtest.actor_loop.BacktestActorLoop._market_data_ref_for` |
| `qts.backtest.actor_loop.BacktestActorLoop.run` | `qts.runtime.actors.market_data_actor.MarketDataEvent` |
| `qts.backtest.actor_loop.BacktestActorLoop.run` | `qts.backtest.historical_data_portal.HistoricalDataPortal` |
| `qts.backtest.actor_loop.BacktestActorLoop.run` | `qts.backtest.actor_loop.BacktestActorLoop._take_strategy_bar_result` |
| `qts.backtest.actor_loop.BacktestActorLoop.run` | `qts.backtest.actor_loop.BacktestActorLoop._take_signal_batch` |
| `qts.backtest.actor_loop.BacktestActorLoop.run` | `qts.runtime.actors.strategy_actor.StrategyBarEvent` |
| `qts.backtest.actor_loop.BacktestActorLoop.run` | `qts.runtime.actors.signal_aggregator_actor.StrategySignalEvent` |
| `qts.backtest.actor_loop.BacktestActorLoop.run` | `qts.runtime.actors.strategy_actor.StrategyFinalize` |
| `qts.backtest.actor_loop.BacktestActorLoop.run` | `qts.backtest.actor_loop.BacktestActorLoop._take_strategy_finalized` |
| `qts.backtest.actor_loop.BacktestActorLoop.run` | `qts.backtest.actor_loop.BacktestActorLoopResult` |
| `qts.backtest.config.BacktestRunConfig.__post_init__` | `qts.backtest.config.BacktestMarketDataReference` |
| `qts.backtest.config.BacktestRunConfig.__post_init__` | `qts.backtest.config.BacktestStrategyConfig` |
| `qts.backtest.config.BacktestRunConfig.__post_init__` | `qts.backtest.config.BacktestRunConfig._normalize_symbol` |
| `qts.backtest.config.BacktestRunConfig.__post_init__` | `qts.core.ids.InstrumentId` |
| `qts.backtest.config.BacktestRunConfig.config_hash` | `qts.core.hashing.stable_json_hash` |
| `qts.backtest.config.BacktestRunConfig.config_hash` | `qts.backtest.config.BacktestRunConfig.to_payload` |
| `qts.backtest.config.BacktestStrategyConfig.from_yaml` | `qts.backtest.config.BacktestStrategyConfig._parse_payload` |
| `qts.backtest.config_loader.BacktestConfigLoader._parse_market_data_reference` | `qts.backtest.config.BacktestMarketDataReference` |
| `qts.backtest.config_loader.BacktestConfigLoader.from_path` | `qts.backtest.config_loader.BacktestConfigLoader.from_payload` |
| `qts.backtest.config_loader.BacktestConfigLoader.from_payload` | `qts.backtest.config.BacktestStrategyConfig.from_yaml` |
| `qts.backtest.config_loader.BacktestConfigLoader.from_payload` | `qts.backtest.config.BacktestRunConfig` |
| `qts.backtest.config_loader.BacktestConfigLoader.from_payload` | `qts.backtest.config_loader.BacktestConfigLoader._parse_datetime` |
| `qts.backtest.config_loader.BacktestConfigLoader.from_payload` | `qts.backtest.config_loader.BacktestConfigLoader._parse_market_data_reference` |
| `qts.backtest.config_loader.BacktestConfigLoader.from_payload` | `qts.backtest.config.CostModelConfig` |
| `qts.backtest.config_loader.BacktestConfigLoader.from_payload` | `qts.backtest.config.RiskConfig` |
| `qts.backtest.config_loader.BacktestConfigLoader.from_payload` | `qts.backtest.config.RollPolicyConfig` |
| `qts.backtest.config_loader.BacktestConfigLoader.from_payload` | `qts.core.ids.InstrumentId` |
| `qts.backtest.engine.BacktestEngine.__init__` | `qts.backtest.engine.BacktestCostModel` |
| `qts.backtest.engine.BacktestEngine.__init__` | `qts.risk.risk_engine.RiskEngine` |
| `qts.backtest.engine.BacktestEngine.__init__` | `qts.risk.rules.max_notional.MaxNotionalRule` |
| `qts.backtest.engine.BacktestEngine.__init__` | `qts.backtest.instrument_context.BacktestInstrumentContext` |
| `qts.backtest.engine.BacktestEngine.__init__` | `qts.backtest.portfolio_projection.BacktestPortfolioProjector` |
| `qts.backtest.engine.BacktestEngine.__init__` | `qts.backtest.intent_processor.BacktestIntentProcessor` |
| `qts.backtest.engine.BacktestEngine.from_config` | `qts.backtest.engine.BacktestCostModel` |
| `qts.backtest.engine.BacktestEngine.from_config` | `qts.risk.risk_engine.RiskEngine` |
| `qts.backtest.engine.BacktestEngine.from_config` | `qts.risk.rules.max_notional.MaxNotionalRule` |
| `qts.backtest.engine.BacktestEngine.run_streaming` | `qts.backtest.report.StreamingBacktestArtifactWriter` |
| `qts.backtest.engine.BacktestEngine.run_streaming` | `qts.backtest.sinks.BacktestStreamingSink` |
| `qts.backtest.engine.BacktestEngine.run_streaming` | `qts.backtest.actor_loop.BacktestActorLoop` |
| `qts.backtest.engine.BacktestEngine.run_streaming` | `qts.backtest.engine._BacktestExecutionAdapter` |
| `qts.backtest.engine.BacktestEngine.run_streaming` | `qts.backtest.report.EquityCurvePoint` |
| `qts.backtest.engine.BacktestEngine.run_streaming` | `qts.backtest.engine.BacktestEngine._zero_time` |
| `qts.backtest.engine.BacktestEngine.run_streaming` | `qts.core.hashing.stable_json_hash` |
| `qts.backtest.engine.BacktestEngine.run_streaming` | `qts.backtest.engine.BacktestEngine._dataset_payload` |
| `qts.backtest.engine.BacktestEngine.run_streaming` | `qts.backtest.engine.BacktestStreamResult` |
| `qts.backtest.engine.BacktestEngine.run_streaming` | `qts.core.ids.BacktestRunId` |
| `qts.backtest.historical_data_portal.HistoricalDataPortal.history` | `qts.backtest.historical_data_portal.HistoricalDataPortal.data_view` |
| `qts.backtest.inputs.BacktestInputBuilder._dataset_instrument_id` | `qts.core.ids.InstrumentId` |
| `qts.backtest.inputs.BacktestInputBuilder._dataset_metadata` | `qts.data.provenance.DatasetMetadata` |
| `qts.backtest.inputs.BacktestInputBuilder._dataset_metadata` | `qts.backtest.inputs.BacktestInputBuilder._dataset_instrument_id` |
| `qts.backtest.inputs.BacktestInputBuilder._instrument_registry_for` | `qts.registry.instrument_registry.InstrumentRegistry` |
| `qts.backtest.inputs.BacktestInputBuilder._instrument_registry_for` | `qts.backtest.inputs.BacktestInputBuilder._instrument_for` |
| `qts.backtest.inputs.BacktestInputBuilder._iter_root_bars` | `qts.backtest.inputs.BacktestInputBuilder._record_exchange_timezone` |
| `qts.backtest.inputs.BacktestInputBuilder._roll_registry` | `qts.registry.future_roll.FutureRollRegistry` |
| `qts.backtest.inputs.BacktestInputBuilder._stream_configured_bars` | `qts.backtest.inputs.BacktestInputBuilder._exchange_timezone_for` |
| `qts.backtest.inputs.BacktestInputBuilder._stream_configured_bars` | `qts.data.historical.csv_dataset.iter_historical_bars` |
| `qts.backtest.inputs.BacktestInputBuilder._stream_configured_bars` | `qts.registry.future_roll.HighestVolumeFutureContractSelector` |
| `qts.backtest.inputs.BacktestInputBuilder._stream_configured_bars` | `qts.backtest.inputs.BacktestInputBuilder._iter_root_bars` |
| `qts.backtest.inputs.BacktestInputBuilder._stream_configured_bars` | `qts.backtest.inputs.BacktestInputBuilder._merge_ordered_bar_streams` |
| `qts.backtest.inputs.BacktestInputBuilder.build` | `qts.backtest.inputs.BacktestInputBuilder._roll_registry` |
| `qts.backtest.inputs.BacktestInputBuilder.build` | `qts.backtest.inputs.BacktestInputBuilder._stream_configured_bars` |
| `qts.backtest.inputs.BacktestInputBuilder.build` | `qts.backtest.inputs.BacktestInputBundle` |
| `qts.backtest.inputs.BacktestInputBuilder.build` | `qts.backtest.inputs.BacktestInputBuilder._instrument_registry_for` |
| `qts.backtest.inputs.BacktestInputBuilder.build` | `qts.backtest.inputs.BacktestInputBuilder._dataset_metadata` |
| `qts.backtest.inputs.BacktestInputBuilder.build` | `qts.backtest.inputs.BacktestInputBuilder._contract_multipliers_for` |
| `qts.backtest.instrument_context.BacktestInstrumentContext.instrument_registry` | `qts.registry.instrument_registry.InstrumentRegistry` |
| `qts.backtest.instrument_context.BacktestInstrumentContext.instrument_registry` | `qts.backtest.instrument_context.BacktestInstrumentContext._symbol_for` |
| `qts.backtest.instrument_context.BacktestInstrumentContext.instrument_registry` | `qts.backtest.instrument_context.BacktestInstrumentContext._exchange_for` |
| `qts.backtest.instrument_context.BacktestInstrumentContext.market_price_for_intent` | `qts.backtest.instrument_context.BacktestInstrumentContext.is_continuous` |
| `qts.backtest.instrument_context.BacktestInstrumentContext.order_instrument_for_intent` | `qts.backtest.instrument_context.BacktestInstrumentContext.is_continuous` |
| `qts.backtest.instrument_context.BacktestInstrumentContext.related_contracts_for` | `qts.backtest.instrument_context.BacktestInstrumentContext.is_continuous` |
| `qts.backtest.instrument_context.BacktestInstrumentContext.update_rolling_prices` | `qts.backtest.instrument_context.BacktestInstrumentContext.is_continuous` |
| `qts.backtest.intent_processor.BacktestIntentProcessor._process_order_delta` | `qts.backtest.intent_processor.BacktestProcessedIntent` |
| `qts.backtest.intent_processor.BacktestIntentProcessor._process_order_delta` | `qts.core.ids.OrderId` |
| `qts.backtest.intent_processor.BacktestIntentProcessor._process_order_delta` | `qts.runtime.actors.order_manager_actor.SubmitOrder` |
| `qts.backtest.intent_processor.BacktestIntentProcessor.process_intent` | `qts.portfolio.position_book.Position` |
| `qts.backtest.intent_processor.BacktestIntentProcessor.process_intent` | `qts.backtest.intent_processor.BacktestIntentProcessor._desired_quantity` |
| `qts.backtest.intent_processor.BacktestIntentProcessor.process_intent` | `qts.backtest.intent_processor.BacktestProcessedIntent` |
| `qts.backtest.intent_processor.BacktestIntentProcessor.process_intent` | `qts.backtest.intent_processor.BacktestIntentProcessor._process_order_delta` |
| `qts.backtest.portfolio_projection.BacktestPortfolioProjector.equity_point` | `qts.backtest.report.EquityCurvePoint` |
| `qts.backtest.portfolio_projection.BacktestPortfolioProjector.equity_point` | `qts.backtest.portfolio_projection.BacktestPortfolioProjector.portfolio_view` |
| `qts.backtest.portfolio_projection.BacktestPortfolioProjector.portfolio_view` | `qts.backtest.portfolio_projection.BacktestPortfolioProjector.multiplier_for` |
| `qts.backtest.report.StreamingBacktestArtifactWriter.__init__` | `qts.backtest.report._NdjsonArtifact` |
| `qts.backtest.report.StreamingBacktestArtifactWriter.__init__` | `qts.backtest.report.StreamingEquityMetrics` |
| `qts.backtest.report.StreamingBacktestArtifactWriter.finalize` | `qts.backtest.report._stable_hash` |
| `qts.backtest.report.StreamingBacktestArtifactWriter.finalize` | `qts.backtest.report.StreamingBacktestArtifacts` |
| `qts.backtest.report._stable_hash` | `qts.core.hashing.stable_json_hash` |
| `qts.backtest.runner._catalog_load_config` | `qts.data.historical.catalog.HistoricalCatalogLoadConfig.from_historical_data_config` |
| `qts.backtest.runner._catalog_load_config` | `qts.data.historical.catalog.HistoricalCatalogLoadConfig.from_legacy_root` |
| `qts.backtest.runner._load_strategy` | `qts.backtest.runner._import_strategy_module` |
| `qts.backtest.runner._load_strategy` | `qts.backtest.runner._strategy_type_from_module` |
| `qts.backtest.runner.run_backtest` | `qts.backtest.config.BacktestRunConfig.from_yaml` |
| `qts.backtest.runner.run_backtest` | `qts.data.historical.catalog.HistoricalCatalog.load` |
| `qts.backtest.runner.run_backtest` | `qts.backtest.runner._catalog_load_config` |
| `qts.backtest.runner.run_backtest` | `qts.backtest.inputs.BacktestInputBuilder.build` |
| `qts.backtest.runner.run_backtest` | `qts.backtest.inputs.BacktestInputBuilder` |
| `qts.backtest.runner.run_backtest` | `qts.backtest.runner._load_strategy` |
| `qts.backtest.runner.run_backtest` | `qts.backtest.engine.BacktestEngine.from_config` |
| `qts.backtest.runner.run_backtest` | `qts.backtest.runner._streaming_summary_payload` |
| `qts.backtest.runner.run_backtest` | `qts.backtest.runner.BacktestRun` |
| `qts.backtest.sinks.BacktestStreamingSink._ledger_rows` | `qts.backtest.report.TradeLedgerEntry` |
| `qts.backtest.sinks.BacktestStreamingSink.write_processed` | `qts.backtest.sinks.BacktestStreamingSink._order_payload` |
| `qts.backtest.sinks.BacktestStreamingSink.write_processed` | `qts.backtest.sinks.BacktestStreamingSink._fill_payload` |
| `qts.backtest.sinks.BacktestStreamingSink.write_processed` | `qts.backtest.sinks.BacktestStreamingSink._ledger_rows` |
| `qts.config.ibkr.IbkrEnvironmentConfig.from_payload` | `qts.config.ibkr._as_mapping` |
| `qts.config.ibkr.IbkrEnvironmentConfig.from_payload` | `qts.config.ibkr._read_connection` |
| `qts.config.ibkr.IbkrEnvironmentConfig.from_payload` | `qts.config.ibkr._read_order_execution_config` |
| `qts.config.ibkr.IbkrEnvironmentConfig.from_payload` | `qts.config.ibkr._read_secret_refs` |
| `qts.config.ibkr.IbkrEnvironmentConfig.from_yaml` | `qts.config.ibkr.IbkrEnvironmentConfig.from_payload` |
| `qts.config.ibkr._read_connection` | `qts.config.ibkr.IbkrConnectionConfig` |
| `qts.config.ibkr._read_order_execution_config` | `qts.config.ibkr._read_connection` |
| `qts.config.ibkr._read_order_execution_config` | `qts.config.ibkr.IbkrOrderExecutionConfig` |
| `qts.config.ibkr._read_secret_refs` | `qts.config.ibkr.IbkrSecretRefs` |
| `qts.config.ibkr.collect_validation_errors` | `qts.config.ibkr.validate_ibkr_environment` |
| `qts.config.ibkr.validate_ibkr_environment` | `qts.config.ibkr._contains_paper_reference` |
| `qts.core.hashing.stable_json_hash` | `qts.core.hashing.stable_json_dumps` |
| `qts.core.time.TimeInterval.__post_init__` | `qts.core.time.require_aware_datetime` |
| `qts.core.time.TimeInterval.contains` | `qts.core.time.require_aware_datetime` |
| `qts.core.time.to_exchange_time` | `qts.core.time.require_aware_datetime` |
| `qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter.subscription_for` | `qts.data.adapters.ibkr_market_data.IbkrMarketDataSubscription` |
| `qts.data.bars.aggregator.BarAggregator._new_state_for` | `qts.data.bars.alignment.clock_bucket_for` |
| `qts.data.bars.aggregator.BarAggregator._new_state_for` | `qts.data.bars.aggregator.AggregationState` |
| `qts.data.bars.aggregator.BarAggregator._new_state_for` | `qts.core.time.TimeInterval` |
| `qts.data.bars.aggregator.BarAggregator.finish` | `qts.data.bars.aggregator.AggregationResult` |
| `qts.data.bars.aggregator.BarAggregator.finish` | `qts.data.bars.aggregator._aggregate_state` |
| `qts.data.bars.aggregator.BarAggregator.update` | `qts.data.bars.aggregator.AggregationResult` |
| `qts.data.bars.aggregator.BarAggregator.update` | `qts.data.bars.aggregator._bar_inside_session` |
| `qts.data.bars.aggregator.BarAggregator.update` | `qts.data.bars.aggregator.BarAggregator._new_state_for` |
| `qts.data.bars.aggregator.BarAggregator.update` | `qts.data.bars.aggregator._same_stream_bucket` |
| `qts.data.bars.aggregator.BarAggregator.update` | `qts.data.bars.aggregator._aggregate_state` |
| `qts.data.bars.aggregator.BarAggregator.update` | `qts.data.bars.aggregator.AggregationState` |
| `qts.data.bars.aggregator._aggregate_state` | `qts.data.bars.aggregator._aggregate_vwap` |
| `qts.data.bars.aggregator._aggregate_state` | `qts.data.bars.aggregator._last_open_interest` |
| `qts.data.bars.aggregator._aggregate_state` | `qts.data.bars.aggregator._sum_trade_count` |
| `qts.data.bars.aggregator.aggregate_bars` | `qts.data.bars.aggregator.BarAggregator` |
| `qts.data.bars.alignment.clock_bucket_for` | `qts.core.time.to_exchange_time` |
| `qts.data.bars.alignment.clock_bucket_for` | `qts.data.bars.alignment._duration_seconds` |
| `qts.data.bars.alignment.clock_bucket_for` | `qts.core.time.TimeInterval` |
| `qts.data.bars.pipeline.BarAggregationPipeline._aggregator_for` | `qts.data.bars.aggregator.BarAggregator` |
| `qts.data.bars.pipeline.BarAggregationPipeline.aggregate` | `qts.data.bars.pipeline.BarAggregationPipeline._aggregation_key` |
| `qts.data.bars.pipeline.BarAggregationPipeline.aggregate` | `qts.data.bars.pipeline.BarAggregationPipeline._aggregator_for` |
| `qts.data.bars.pipeline.BarAggregationPipeline.aggregate_logical` | `qts.data.bars.timeframe.Timeframe.parse` |
| `qts.data.bars.pipeline.BarAggregationPipeline.aggregate_logical` | `qts.data.bars.pipeline.BarAggregationPipeline._logical_key` |
| `qts.data.bars.pipeline.BarAggregationPipeline.aggregate_logical` | `qts.data.bars.pipeline.BarAggregationPipeline._aggregator_for` |
| `qts.data.historical.catalog.HistoricalCatalog._symbol_resolvers_for_load_config` | `qts.registry.symbol_resolution.StaticSymbolResolver` |
| `qts.data.historical.catalog.HistoricalCatalog._symbol_resolvers_for_load_config` | `qts.data.historical.catalog.HistoricalCatalog._chain_path_exists` |
| `qts.data.historical.catalog.HistoricalCatalog.from_historical_data_config` | `qts.data.historical.catalog.HistoricalDataset.normalize_root` |
| `qts.data.historical.catalog.HistoricalCatalog.from_historical_data_config` | `qts.data.historical.catalog.HistoricalCatalog._require_file` |
| `qts.data.historical.catalog.HistoricalCatalog.from_historical_data_config` | `qts.data.historical.csv_dataset.describe_csv_dataset` |
| `qts.data.historical.catalog.HistoricalCatalog.from_historical_data_config` | `qts.data.historical.catalog.HistoricalDataset` |
| `qts.data.historical.catalog.HistoricalCatalog.from_historical_data_config` | `qts.data.historical.chains.HistoricalChain.load` |
| `qts.data.historical.catalog.HistoricalCatalog.from_historical_data_config` | `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver` |
| `qts.data.historical.catalog.HistoricalCatalog.from_legacy_root` | `qts.data.historical.catalog.HistoricalDataset.normalize_root` |
| `qts.data.historical.catalog.HistoricalCatalog.from_legacy_root` | `qts.data.historical.catalog.HistoricalCatalog._require_file` |
| `qts.data.historical.catalog.HistoricalCatalog.from_legacy_root` | `qts.data.historical.csv_dataset.describe_csv_dataset` |
| `qts.data.historical.catalog.HistoricalCatalog.from_legacy_root` | `qts.data.historical.catalog.HistoricalDataset` |
| `qts.data.historical.catalog.HistoricalCatalog.from_legacy_root` | `qts.data.historical.chains.HistoricalChain.load` |
| `qts.data.historical.catalog.HistoricalCatalog.from_legacy_root` | `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver` |
| `qts.data.historical.catalog.HistoricalCatalog.load` | `qts.data.historical.config.HistoricalDataConfig.from_yaml` |
| `qts.data.historical.catalog.HistoricalCatalog.load` | `qts.data.historical.catalog.HistoricalCatalog._symbol_resolvers_for_load_config` |
| `qts.data.historical.catalog.HistoricalCatalog.load` | `qts.data.historical.catalog.HistoricalCatalog.from_historical_data_config` |
| `qts.data.historical.catalog.HistoricalCatalog.load` | `qts.data.historical.catalog.HistoricalCatalog.from_legacy_root` |
| `qts.data.historical.catalog.HistoricalCatalogLoadConfig.__post_init__` | `qts.data.historical.catalog.HistoricalDataset.normalize_root` |
| `qts.data.historical.catalog.HistoricalCatalogLoadConfig.__post_init__` | `qts.data.historical.catalog.HistoricalCatalogLoadConfig._normalize_symbol` |
| `qts.data.historical.catalog.HistoricalCatalogLoadConfig.__post_init__` | `qts.core.ids.InstrumentId` |
| `qts.data.historical.chains.HistoricalChain._parse_contract` | `qts.data.historical.chains.HistoricalChain._required_text` |
| `qts.data.historical.chains.HistoricalChain._parse_contract` | `qts.data.historical.chains.HistoricalContract` |
| `qts.data.historical.chains.HistoricalChain.instrument_id_for_symbol` | `qts.data.historical.chains.HistoricalChain.is_outright_symbol` |
| `qts.data.historical.chains.HistoricalChain.instrument_id_for_symbol` | `qts.core.ids.InstrumentId` |
| `qts.data.historical.chains.HistoricalChain.load` | `qts.data.historical.chains.HistoricalChain._required_text` |
| `qts.data.historical.chains.HistoricalChain.load` | `qts.data.historical.chains.HistoricalChain._exchange_code` |
| `qts.data.historical.chains.HistoricalChain.load` | `qts.data.historical.chains.HistoricalChain._required_decimal` |
| `qts.data.historical.chains.HistoricalChain.load` | `qts.data.historical.chains.HistoricalChain._parse_contract` |
| `qts.data.historical.config.HistoricalDataConfig._select_bar_file` | `qts.data.historical.config.HistoricalBarFileConfig` |
| `qts.data.historical.config.HistoricalDataConfig._select_bar_file` | `qts.data.live_feed.FeedCapabilities.source_timeframe_for` |
| `qts.data.historical.config.HistoricalDataConfig._select_bar_file` | `qts.data.live_feed.FeedCapabilities` |
| `qts.data.historical.config.HistoricalDataConfig.resolve_chain_path` | `qts.data.historical.config.HistoricalDatasetConfig.normalize_root` |
| `qts.data.historical.config.HistoricalDataConfig.resolve_chain_path` | `qts.data.historical.config.HistoricalDataConfig.catalog` |
| `qts.data.historical.config.HistoricalDataConfig.resolve_chain_path` | `qts.data.historical.config.HistoricalDataConfig.store` |
| `qts.data.historical.config.HistoricalDataConfig.resolve_dataset` | `qts.data.historical.config.HistoricalDatasetConfig.normalize_root` |
| `qts.data.historical.config.HistoricalDataConfig.resolve_dataset` | `qts.data.historical.config.HistoricalDataConfig.catalog` |
| `qts.data.historical.config.HistoricalDataConfig.resolve_dataset` | `qts.data.historical.config.HistoricalDataConfig.store` |
| `qts.data.historical.config.HistoricalDataConfig.resolve_dataset` | `qts.data.historical.config.HistoricalDataConfig._select_bar_file` |
| `qts.data.historical.config.HistoricalDataConfig.resolve_dataset` | `qts.data.historical.config.HistoricalDatasetLocation` |
| `qts.data.historical.config.HistoricalDataConfig.resolve_dataset` | `qts.data.historical.config.HistoricalDataConfig._csv_schema` |
| `qts.data.historical.config.HistoricalDataStoreConfig._render_template` | `qts.data.historical.config.HistoricalDatasetConfig.normalize_root` |
| `qts.data.historical.config.HistoricalDataStoreConfig.bars_path` | `qts.data.historical.config.HistoricalDataStoreConfig._render_template` |
| `qts.data.historical.config.HistoricalDataStoreConfig.bars_path` | `qts.data.historical.config.HistoricalDataStoreConfig._join` |
| `qts.data.historical.config.HistoricalDataStoreConfig.chain_path` | `qts.data.historical.config.HistoricalDataStoreConfig._render_template` |
| `qts.data.historical.config.HistoricalDataStoreConfig.chain_path` | `qts.data.historical.config.HistoricalDataStoreConfig._join` |
| `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_bar_files` | `qts.data.historical.config.HistoricalBarFileConfig` |
| `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_catalogs` | `qts.data.historical.config.HistoricalDataCatalogConfig` |
| `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_catalogs` | `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_datasets` |
| `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_datasets` | `qts.data.historical.config.HistoricalDatasetConfig.normalize_root` |
| `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_datasets` | `qts.data.historical.config.HistoricalDatasetConfig` |
| `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_datasets` | `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_bar_files` |
| `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_schemas` | `qts.data.historical.csv_format.HistoricalCsvSchema` |
| `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_store_defaults` | `qts.data.historical.config.HistoricalDataStoreDefaults` |
| `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_stores` | `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_store_defaults` |
| `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_stores` | `qts.data.historical.config.HistoricalDataStoreConfig` |
| `qts.data.historical.config_loader.HistoricalDataConfigLoader.from_path` | `qts.data.historical.config_loader.HistoricalDataConfigLoader.from_payload` |
| `qts.data.historical.config_loader.HistoricalDataConfigLoader.from_payload` | `qts.data.historical.config.HistoricalDataConfig` |
| `qts.data.historical.config_loader.HistoricalDataConfigLoader.from_payload` | `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_stores` |
| `qts.data.historical.config_loader.HistoricalDataConfigLoader.from_payload` | `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_catalogs` |
| `qts.data.historical.config_loader.HistoricalDataConfigLoader.from_payload` | `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_schemas` |
| `qts.data.historical.csv_dataset.HistoricalBarStream.__init__` | `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper` |
| `qts.data.historical.csv_dataset.HistoricalBarStream.__init__` | `qts.data.historical.validation.HistoricalCsvStats` |
| `qts.data.historical.csv_dataset.HistoricalBarStream.__iter__` | `qts.data.historical.csv_format.validate_historical_csv_columns` |
| `qts.data.historical.csv_dataset.HistoricalBarStream.__iter__` | `qts.data.historical.csv_dataset.HistoricalBarStream._iter_all_supported_rows` |
| `qts.data.historical.csv_dataset.HistoricalBarStream.__iter__` | `qts.data.historical.csv_dataset.HistoricalBarStream._iter_session_selected_contract_rows` |
| `qts.data.historical.csv_dataset.HistoricalBarStream.__iter__` | `qts.data.historical.csv_dataset.HistoricalBarStream._iter_selected_contract_rows` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._count_excluded_symbol` | `qts.data.historical.csv_dataset._is_spread_symbol` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._emit_selected_session_rows` | `qts.data.historical.csv_format.historical_timeframe_delta` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._emit_selected_session_rows` | `qts.data.historical.csv_dataset.HistoricalBarStream._field` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._emit_selected_session_rows` | `qts.data.historical.csv_dataset.HistoricalBarStream._count_excluded_symbol` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._emit_selected_session_rows` | `qts.registry.future_roll.FutureContractCandidate` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._emit_selected_session_rows` | `qts.data.historical.csv_dataset.HistoricalBarStream._resolver_root` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._emit_selected_session_rows` | `qts.registry.future_roll.FutureRollSelection` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._iter_all_supported_rows` | `qts.data.historical.csv_dataset.HistoricalBarStream._field` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._iter_all_supported_rows` | `qts.data.historical.csv_dataset.HistoricalBarStream._timestamp` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._iter_all_supported_rows` | `qts.data.historical.csv_dataset.HistoricalBarStream._count_excluded_symbol` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._iter_selected_contract_rows` | `qts.data.historical.csv_dataset.HistoricalBarStream._timestamp_groups` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._iter_selected_contract_rows` | `qts.data.historical.csv_dataset.HistoricalBarStream._field` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._iter_selected_contract_rows` | `qts.registry.future_roll.FutureRollSelection` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._iter_selected_contract_rows` | `qts.data.historical.csv_dataset.HistoricalBarStream._count_excluded_symbol` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._iter_selected_contract_rows` | `qts.registry.future_roll.FutureContractCandidate` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._iter_selected_contract_rows` | `qts.data.historical.csv_dataset.HistoricalBarStream._resolver_root` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._iter_session_selected_contract_rows` | `qts.data.historical.csv_dataset.HistoricalBarStream._timestamp_groups` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._iter_session_selected_contract_rows` | `qts.data.historical.csv_dataset.HistoricalBarStream._emit_selected_session_rows` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._resolver_root` | `qts.data.historical.csv_dataset._resolver_root` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._timestamp` | `qts.data.historical.csv_format.parse_historical_ts_event` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._timestamp` | `qts.data.historical.csv_dataset.HistoricalBarStream._field` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._timestamp_groups` | `qts.data.historical.csv_dataset.HistoricalBarStream._field` |
| `qts.data.historical.csv_dataset.HistoricalBarStream._timestamp_groups` | `qts.data.historical.csv_format.parse_historical_ts_event` |
| `qts.data.historical.csv_dataset._as_symbol_resolver` | `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver` |
| `qts.data.historical.csv_dataset.describe_csv_dataset` | `qts.data.historical.csv_format.validate_historical_csv_columns` |
| `qts.data.historical.csv_dataset.describe_csv_dataset` | `qts.data.historical.csv_dataset.CsvDatasetDescription` |
| `qts.data.historical.csv_dataset.iter_historical_bars` | `qts.data.historical.csv_dataset.HistoricalBarStream` |
| `qts.data.historical.csv_dataset.iter_historical_bars` | `qts.data.historical.csv_dataset._as_symbol_resolver` |
| `qts.data.historical.csv_dataset.validate_historical_sample` | `qts.data.historical.validation.HistoricalDatasetValidator.validate_sample` |
| `qts.data.historical.csv_dataset.validate_historical_sample` | `qts.data.historical.validation.HistoricalDatasetValidator` |
| `qts.data.historical.csv_dataset.validate_historical_sample` | `qts.data.historical.csv_dataset._as_symbol_resolver` |
| `qts.data.historical.csv_format.HistoricalCsvSchema.column_indices` | `qts.data.historical.csv_format.HistoricalCsvSchema.validate_columns` |
| `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper.extract_ohlcv` | `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper._parse_ohlcv_values` |
| `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper.extract_ohlcv` | `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper._field` |
| `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper.to_bar` | `qts.data.historical.csv_format.parse_historical_ts_event` |
| `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper.to_bar` | `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper._field` |
| `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper.to_bar` | `qts.data.historical.csv_format.historical_timeframe_delta` |
| `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper.to_bar` | `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper.extract_ohlcv` |
| `qts.data.historical.service.HistoricalMarketDataService.capabilities` | `qts.data.live_feed.FeedCapabilities` |
| `qts.data.historical.service.HistoricalMarketDataService.events` | `qts.data.historical.csv_dataset.iter_historical_bars` |
| `qts.data.historical.service.HistoricalMarketDataService.events` | `qts.data.live_feed.LiveFeedEvent` |
| `qts.data.historical.service.HistoricalMarketDataService.subscribe` | `qts.data.live_feed.LiveFeedSubscribed` |
| `qts.data.historical.validation.HistoricalDatasetValidator.validate_sample` | `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper` |
| `qts.data.historical.validation.HistoricalDatasetValidator.validate_sample` | `qts.data.historical.validation.HistoricalCsvStats` |
| `qts.data.historical.validation.HistoricalDatasetValidator.validate_sample` | `qts.data.historical.csv_format.validate_historical_csv_columns` |
| `qts.data.historical.validation.HistoricalDatasetValidator.validate_sample` | `qts.data.historical.validation._is_spread_symbol` |
| `qts.data.historical.validation.HistoricalDatasetValidator.validate_sample` | `qts.data.validation_report.DataValidationIssue` |
| `qts.data.historical.validation.HistoricalDatasetValidator.validate_sample` | `qts.data.historical.validation._group_bars` |
| `qts.data.historical.validation.HistoricalDatasetValidator.validate_sample` | `qts.data.validation_report.validate_bars` |
| `qts.data.historical.validation.HistoricalDatasetValidator.validate_sample` | `qts.data.historical.csv_format.historical_timeframe_delta` |
| `qts.data.historical.validation.HistoricalDatasetValidator.validate_sample` | `qts.data.historical.validation.HistoricalValidationSample` |
| `qts.data.historical.validation.HistoricalDatasetValidator.validate_sample` | `qts.data.validation_report.DataValidationReport` |
| `qts.data.live_feed.FakeLiveFeedAdapter.capabilities` | `qts.data.live_feed.FeedCapabilities` |
| `qts.data.live_feed.FakeLiveFeedAdapter.emit` | `qts.data.live_feed.LiveFeedEvent` |
| `qts.data.live_feed.FakeLiveFeedAdapter.fail` | `qts.data.live_feed.LiveFeedFailure` |
| `qts.data.live_feed.FakeLiveFeedAdapter.subscribe` | `qts.data.live_feed.LiveFeedSubscribed` |
| `qts.data.live_feed.FeedCapabilities.source_timeframe_for` | `qts.data.live_feed.FeedCapabilities.supports_timeframe` |
| `qts.data.provenance.DatasetMetadata.__post_init__` | `qts.data.provenance.DatasetMetadata._require_text` |
| `qts.data.provenance.DatasetMetadata.__post_init__` | `qts.core.time.require_aware_datetime` |
| `qts.data.sessions.filter.filter_session_bars` | `qts.data.sessions.filter._bar_inside_session` |
| `qts.data.sessions.window.RegularSessionWindow.session_date_for_timestamp` | `qts.core.time.to_exchange_time` |
| `qts.data.sessions.window.RegularSessionWindow.session_id_for_timestamp` | `qts.data.sessions.window.RegularSessionWindow.session_date_for_timestamp` |
| `qts.data.stores.parquet_store.ParquetMarketDataStore._bar_from_json` | `qts.core.ids.InstrumentId` |
| `qts.data.stores.parquet_store.ParquetMarketDataStore._read_file` | `qts.data.stores.parquet_store.ParquetMarketDataStore._bar_from_json` |
| `qts.data.stores.parquet_store.ParquetMarketDataStore.read_bars` | `qts.data.stores.parquet_store.ParquetMarketDataStore._read_file` |
| `qts.data.stores.parquet_store.ParquetMarketDataStore.write_bars` | `qts.data.stores.parquet_store.ParquetMarketDataStore._path_for` |
| `qts.data.stores.parquet_store.ParquetMarketDataStore.write_bars` | `qts.data.stores.parquet_store.ParquetMarketDataStore._read_file` |
| `qts.data.stores.parquet_store.ParquetMarketDataStore.write_bars` | `qts.data.stores.parquet_store.ParquetMarketDataStore._bar_to_json` |
| `qts.data.subscriptions.logical_key` | `qts.data.subscriptions.LogicalSubscriptionKey` |
| `qts.data.subscriptions.plan_physical_subscription` | `qts.data.subscriptions.PhysicalSubscriptionKey` |
| `qts.data.validation_report._append_ohlc_issue` | `qts.data.validation_report.DataValidationIssue` |
| `qts.data.validation_report.validate_bars` | `qts.data.validation_report.DataValidationIssue` |
| `qts.data.validation_report.validate_bars` | `qts.data.validation_report._append_ohlc_issue` |
| `qts.data.validation_report.validate_bars` | `qts.data.validation_report.DataValidationReport` |
| `qts.domain.events.event.BaseEvent.__post_init__` | `qts.core.time.require_aware_datetime` |
| `qts.domain.events.metadata.EventMetadata.__post_init__` | `qts.core.time.require_aware_datetime` |
| `qts.domain.instruments.contract_spec.ContractSpec.__post_init__` | `qts.domain.instruments.contract_spec.ContractSpec._require_positive` |
| `qts.domain.market_data.bar.Bar.__post_init__` | `qts.core.time.TimeInterval` |
| `qts.domain.market_data.bar.Bar.__post_init__` | `qts.domain.market_data.bar.Bar._require_non_negative` |
| `qts.domain.market_data.bar.Bar.interval` | `qts.core.time.TimeInterval` |
| `qts.domain.market_data.bar.Quote.__post_init__` | `qts.core.time.require_aware_datetime` |
| `qts.domain.market_data.bar.Quote.__post_init__` | `qts.domain.market_data.bar.Bar._require_non_negative` |
| `qts.domain.market_data.bar.Tick.__post_init__` | `qts.core.time.require_aware_datetime` |
| `qts.domain.market_data.bar.Tick.__post_init__` | `qts.domain.market_data.bar.Bar._require_non_negative` |
| `qts.domain.risk.request.OrderRiskRequest.__post_init__` | `qts.core.time.require_aware_datetime` |
| `qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionAdapter.normalize_execution_report` | `qts.execution.broker.normalize_broker_status` |
| `qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionAdapter.to_order_request` | `qts.execution.adapters.ibkr_order_execution.IbkrOrderRequest` |
| `qts.execution.broker.FakeBrokerAdapter._report` | `qts.execution.broker.BrokerExecutionReport` |
| `qts.execution.broker.FakeBrokerAdapter.cancel_order` | `qts.execution.broker.FakeBrokerAdapter._report` |
| `qts.execution.broker.FakeBrokerAdapter.capabilities` | `qts.execution.broker.BrokerCapabilities` |
| `qts.execution.broker.FakeBrokerAdapter.emit_fill` | `qts.execution.broker.FakeBrokerAdapter._report` |
| `qts.execution.broker.FakeBrokerAdapter.submit_order` | `qts.execution.broker.FakeBrokerAdapter._report` |
| `qts.execution.broker.normalize_broker_execution_report` | `qts.execution.broker.normalize_broker_status` |
| `qts.execution.order_manager.OrderManager.__init__` | `qts.execution.idempotency.FillIdempotencyStore` |
| `qts.execution.order_manager.OrderManager.create_order` | `qts.execution.order_state_machine.OrderStateMachine` |
| `qts.execution.order_manager.OrderManager.mark_sent` | `qts.execution.order_manager.OrderManager._replace_order` |
| `qts.execution.order_manager.OrderManager.process_report` | `qts.execution.order_manager.OrderManager._event_for_report` |
| `qts.execution.order_manager.OrderManager.process_report` | `qts.execution.order_manager.OrderManager._replace_order` |
| `qts.execution.order_manager.OrderManager.process_report` | `qts.execution.order_manager.OrderManager._fills_for_report` |
| `qts.execution.order_manager.OrderManager.request_cancel` | `qts.execution.order_manager.OrderManager._replace_order` |
| `qts.execution.order_manager.OrderManager.restore` | `qts.execution.order_state_machine.OrderStateMachine` |
| `qts.execution.order_manager.OrderManager.restore` | `qts.execution.idempotency.FillIdempotencyStore.restore` |
| `qts.execution.order_state_machine.OrderStateMachine.apply` | `qts.execution.order_state_machine.OrderTransitionError` |
| `qts.execution.simulator.simulated_broker.SimulatedBroker.__init__` | `qts.execution.simulator.fill_model.ImmediateFillModel` |
| `qts.factors.momentum.MomentumFactor.compute` | `qts.factors.momentum.FactorScore` |
| `qts.factors.momentum.MomentumFactor.compute` | `qts.factors.momentum.MomentumFactor._momentum` |
| `qts.factors.momentum.MomentumFactor.compute` | `qts.factors.momentum.FactorResult` |
| `qts.observability.logging.build_log_record` | `qts.observability.logging._metadata_fields` |
| `qts.observability.logging.build_log_record` | `qts.observability.logging._is_secret_key` |
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
| `qts.portfolio.reservation_book.ReservationBook.reserve` | `qts.portfolio.reservation_book.ReservationBook._normalize_currency` |
| `qts.portfolio.reservation_book.ReservationBook.reserve` | `qts.portfolio.reservation_book.Reservation` |
| `qts.portfolio.reservation_book.ReservationBook.reserved` | `qts.portfolio.reservation_book.ReservationBook._normalize_currency` |
| `qts.quality.guardrails.BacktestEngineCohesionRule.check` | `qts.quality.guardrails._check_backtest_engine_cohesion` |
| `qts.quality.guardrails.BacktestInputCohesionRule.check` | `qts.quality.guardrails._check_backtest_input_cohesion` |
| `qts.quality.guardrails.BacktestRunnerCohesionRule.check` | `qts.quality.guardrails._check_backtest_runner_cohesion` |
| `qts.quality.guardrails.BrokerSpecificRule.check` | `qts.quality.guardrails._has_allowed_prefix` |
| `qts.quality.guardrails.BrokerSpecificRule.check` | `qts.quality.guardrails._check_broker_specific_code` |
| `qts.quality.guardrails.GuardrailSuite.__init__` | `qts.quality.guardrails.ImportBoundaryRule` |
| `qts.quality.guardrails.GuardrailSuite.__init__` | `qts.quality.guardrails.ProductSpecificRule` |
| `qts.quality.guardrails.GuardrailSuite.__init__` | `qts.quality.guardrails.BrokerSpecificRule` |
| `qts.quality.guardrails.GuardrailSuite.__init__` | `qts.quality.guardrails.TestSupportRule` |
| `qts.quality.guardrails.GuardrailSuite.__init__` | `qts.quality.guardrails.SharedCapabilityRule` |
| `qts.quality.guardrails.GuardrailSuite.__init__` | `qts.quality.guardrails.OOPPublicFactoryRule` |
| `qts.quality.guardrails.GuardrailSuite.__init__` | `qts.quality.guardrails.OOPHelperOwnershipRule` |
| `qts.quality.guardrails.GuardrailSuite.__init__` | `qts.quality.guardrails.BacktestRunnerCohesionRule` |
| `qts.quality.guardrails.GuardrailSuite.__init__` | `qts.quality.guardrails.BacktestInputCohesionRule` |
| `qts.quality.guardrails.GuardrailSuite.__init__` | `qts.quality.guardrails.BacktestEngineCohesionRule` |
| `qts.quality.guardrails.GuardrailSuite.check` | `qts.quality.guardrails._check_python_file` |
| `qts.quality.guardrails.ImportBoundaryRule.check` | `qts.quality.guardrails._iter_imports` |
| `qts.quality.guardrails.ImportBoundaryRule.check` | `qts.quality.guardrails._check_import` |
| `qts.quality.guardrails.OOPHelperOwnershipRule.check` | `qts.quality.guardrails._check_oop_helper_ownership` |
| `qts.quality.guardrails.OOPPublicFactoryRule.check` | `qts.quality.guardrails._check_oop_public_factory_functions` |
| `qts.quality.guardrails.ProductSpecificRule.check` | `qts.quality.guardrails._has_allowed_prefix` |
| `qts.quality.guardrails.ProductSpecificRule.check` | `qts.quality.guardrails._check_product_specific_code` |
| `qts.quality.guardrails.SharedCapabilityRule.check` | `qts.quality.guardrails._check_shared_capability_placement` |
| `qts.quality.guardrails.TestSupportRule.check` | `qts.quality.guardrails._check_test_support_code` |
| `qts.quality.guardrails._check_backtest_engine_cohesion` | `qts.quality.guardrails._iter_imports` |
| `qts.quality.guardrails._check_backtest_engine_cohesion` | `qts.quality.guardrails.GuardrailViolation` |
| `qts.quality.guardrails._check_backtest_input_cohesion` | `qts.quality.guardrails._iter_imports` |
| `qts.quality.guardrails._check_backtest_input_cohesion` | `qts.quality.guardrails.GuardrailViolation` |
| `qts.quality.guardrails._check_backtest_input_cohesion` | `qts.quality.guardrails._iter_imported_names` |
| `qts.quality.guardrails._check_backtest_runner_cohesion` | `qts.quality.guardrails._iter_imports` |
| `qts.quality.guardrails._check_backtest_runner_cohesion` | `qts.quality.guardrails.GuardrailViolation` |
| `qts.quality.guardrails._check_backtest_runner_cohesion` | `qts.quality.guardrails._iter_imported_names` |
| `qts.quality.guardrails._check_broker_specific_code` | `qts.quality.guardrails._check_forbidden_tokens` |
| `qts.quality.guardrails._check_forbidden_tokens` | `qts.quality.guardrails._node_identifier_name` |
| `qts.quality.guardrails._check_forbidden_tokens` | `qts.quality.guardrails._contains_forbidden_token` |
| `qts.quality.guardrails._check_forbidden_tokens` | `qts.quality.guardrails.GuardrailViolation` |
| `qts.quality.guardrails._check_import` | `qts.quality.guardrails._is_forbidden_broker_adapter_dependency` |
| `qts.quality.guardrails._check_import` | `qts.quality.guardrails.GuardrailViolation` |
| `qts.quality.guardrails._check_import` | `qts.quality.guardrails._is_forbidden_dependency` |
| `qts.quality.guardrails._check_import` | `qts.quality.guardrails._is_forbidden_adapter_dependency` |
| `qts.quality.guardrails._check_oop_helper_ownership` | `qts.quality.guardrails.GuardrailViolation` |
| `qts.quality.guardrails._check_oop_helper_ownership` | `qts.quality.guardrails._node_references_name` |
| `qts.quality.guardrails._check_oop_public_factory_functions` | `qts.quality.guardrails.GuardrailViolation` |
| `qts.quality.guardrails._check_product_specific_code` | `qts.quality.guardrails._check_forbidden_tokens` |
| `qts.quality.guardrails._check_python_file` | `qts.quality.guardrails.GuardrailSuite.check_file` |
| `qts.quality.guardrails._check_python_file` | `qts.quality.guardrails.GuardrailSuite` |
| `qts.quality.guardrails._check_shared_capability_placement` | `qts.quality.guardrails._has_allowed_prefix` |
| `qts.quality.guardrails._check_shared_capability_placement` | `qts.quality.guardrails._identifier_tokens` |
| `qts.quality.guardrails._check_shared_capability_placement` | `qts.quality.guardrails.GuardrailViolation` |
| `qts.quality.guardrails._check_test_support_code` | `qts.quality.guardrails._identifier_tokens` |
| `qts.quality.guardrails._check_test_support_code` | `qts.quality.guardrails.GuardrailViolation` |
| `qts.quality.guardrails._check_test_support_code` | `qts.quality.guardrails._node_identifier_name` |
| `qts.quality.guardrails._check_test_support_code` | `qts.quality.guardrails._contains_forbidden_token` |
| `qts.quality.guardrails._contains_forbidden_token` | `qts.quality.guardrails._identifier_tokens` |
| `qts.quality.guardrails.main` | `qts.quality.guardrails.run_guardrails` |
| `qts.quality.guardrails.run_guardrails` | `qts.quality.guardrails.GuardrailSuite.check` |
| `qts.quality.guardrails.run_guardrails` | `qts.quality.guardrails.GuardrailSuite` |
| `qts.reconciliation.ReconciliationEngine.reconcile` | `qts.reconciliation.reconcile_snapshots` |
| `qts.reconciliation.ReconciliationEngine.reconcile` | `qts.reconciliation.ReconciliationEngine._effective_tolerance` |
| `qts.reconciliation.ReconciliationEngine.startup_gate` | `qts.reconciliation.startup_reconciliation_gate` |
| `qts.reconciliation._amount_repr` | `qts.reconciliation._amount` |
| `qts.reconciliation._compare_cash` | `qts.reconciliation._quantity_item` |
| `qts.reconciliation._compare_orders` | `qts.reconciliation.DriftItem` |
| `qts.reconciliation._compare_orders` | `qts.reconciliation._order_repr` |
| `qts.reconciliation._compare_positions` | `qts.reconciliation._quantity_item` |
| `qts.reconciliation._quantity_item` | `qts.reconciliation.DriftItem` |
| `qts.reconciliation._quantity_item` | `qts.reconciliation._amount_repr` |
| `qts.reconciliation._quantity_item` | `qts.reconciliation._amount` |
| `qts.reconciliation.reconcile_snapshots` | `qts.reconciliation._compare_orders` |
| `qts.reconciliation.reconcile_snapshots` | `qts.reconciliation._compare_positions` |
| `qts.reconciliation.reconcile_snapshots` | `qts.reconciliation._compare_cash` |
| `qts.reconciliation.reconcile_snapshots` | `qts.reconciliation.ReconciliationReport` |
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
| `qts.registry.future_roll.FutureRollRegistry.register_root` | `qts.registry.future_roll.FutureRollRegistry._normalize_root` |
| `qts.registry.future_roll.FutureRollRegistry.register_root` | `qts.core.ids.InstrumentId` |
| `qts.registry.future_roll.FutureRollRegistry.resolve_contract` | `qts.registry.future_roll.FutureRollRegistry.continuous_instrument_id` |
| `qts.registry.future_roll.FutureRollRegistry.resolve_contract` | `qts.registry.future_roll.FutureRollRegistry._selection_at` |
| `qts.registry.instrument_registry.InstrumentRegistry.get_contract_spec` | `qts.registry.instrument_registry.InstrumentRegistry.get_instrument` |
| `qts.registry.instrument_registry.InstrumentRegistry.register` | `qts.registry.instrument_registry.InstrumentRegistry._normalize_symbol` |
| `qts.registry.instrument_registry.InstrumentRegistry.resolve` | `qts.registry.instrument_registry.InstrumentRegistry._normalize_symbol` |
| `qts.registry.option_chain_registry.OptionChainRegistry.find` | `qts.registry.option_chain_registry.OptionChainRegistry.options_for` |
| `qts.registry.providers.comex_gold_calendar_provider.ComexGoldCalendarProvider.session_for` | `qts.registry.calendar_registry.MarketSession` |
| `qts.registry.providers.comex_gold_calendar_provider.ComexGoldCalendarProvider.session_for` | `qts.core.time.TimeInterval` |
| `qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider.session_for` | `qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider._to_datetime` |
| `qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider.session_for` | `qts.registry.calendar_registry.MarketSession` |
| `qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider.session_for` | `qts.core.time.TimeInterval` |
| `qts.registry.symbol_resolution.StaticSymbolResolver.__post_init__` | `qts.registry.symbol_resolution.StaticSymbolResolver._normalize_symbol` |
| `qts.registry.symbol_resolution.StaticSymbolResolver.instrument_id_for_symbol` | `qts.registry.symbol_resolution.StaticSymbolResolver._normalize_symbol` |
| `qts.registry.symbol_resolution.StaticSymbolResolver.is_supported_symbol` | `qts.registry.symbol_resolution.StaticSymbolResolver._normalize_symbol` |
| `qts.risk.kill_switch.KillSwitchRegistry._matching_scopes` | `qts.risk.kill_switch.KillSwitchScope.global_scope` |
| `qts.risk.kill_switch.KillSwitchRegistry._matching_scopes` | `qts.risk.kill_switch.KillSwitchScope.account` |
| `qts.risk.kill_switch.KillSwitchRegistry._matching_scopes` | `qts.risk.kill_switch.KillSwitchScope.broker` |
| `qts.risk.kill_switch.KillSwitchRegistry._matching_scopes` | `qts.risk.kill_switch.KillSwitchScope.strategy` |
| `qts.risk.kill_switch.KillSwitchRegistry.activate` | `qts.risk.kill_switch.KillSwitchState` |
| `qts.risk.kill_switch.KillSwitchRegistry.check_order` | `qts.risk.kill_switch.KillSwitchRegistry._matching_scopes` |
| `qts.risk.kill_switch.KillSwitchRegistry.deactivate` | `qts.risk.kill_switch.KillSwitchState` |
| `qts.risk.rule_registry.RiskRuleRegistry.build` | `qts.risk.rules.max_notional.MaxNotionalRule` |
| `qts.risk.rule_registry.RiskRuleRegistry.build` | `qts.risk.rule_registry.RiskRuleRegistry._param` |
| `qts.risk.rule_registry.RiskRuleRegistry.build` | `qts.risk.rules.max_order_qty.MaxOrderQuantityRule` |
| `qts.runtime.actor_ref.ActorRef.process_all` | `qts.runtime.actor_ref.ActorRef.process_one` |
| `qts.runtime.actors.account_actor.AccountActor.__init__` | `qts.portfolio.cash_book.CashBook` |
| `qts.runtime.actors.account_actor.AccountActor.__init__` | `qts.portfolio.position_book.PositionBook` |
| `qts.runtime.actors.account_actor.AccountActor.__init__` | `qts.execution.idempotency.FillIdempotencyStore` |
| `qts.runtime.actors.account_actor.AccountActor.handle` | `qts.runtime.actors.account_actor.AccountActor._apply_fill` |
| `qts.runtime.actors.account_actor.AccountActor.snapshot` | `qts.runtime.actors.account_actor.AccountSnapshot` |
| `qts.runtime.actors.execution_actor.ExecutionActor.__init__` | `qts.execution.simulator.simulated_broker.SimulatedBroker` |
| `qts.runtime.actors.market_data_actor.MarketDataActor.__init__` | `qts.data.bars.timeframe.Timeframe.parse` |
| `qts.runtime.actors.market_data_actor.MarketDataActor.__init__` | `qts.data.bars.pipeline.BarAggregationPipeline` |
| `qts.runtime.actors.market_data_actor.MarketDataActor._publish_to_logical_subscribers` | `qts.runtime.actors.market_data_actor.MarketDataActor._publish` |
| `qts.runtime.actors.market_data_actor.MarketDataActor._publish_to_logical_subscribers` | `qts.runtime.actors.market_data_actor.MarketDataActor._publish_to` |
| `qts.runtime.actors.market_data_actor.MarketDataActor._subscribe` | `qts.data.subscriptions.LogicalSubscription` |
| `qts.runtime.actors.market_data_actor.MarketDataActor._subscribe` | `qts.data.subscriptions.logical_key` |
| `qts.runtime.actors.market_data_actor.MarketDataActor._subscribe` | `qts.data.subscriptions.plan_physical_subscription` |
| `qts.runtime.actors.market_data_actor.MarketDataActor._subscribe` | `qts.data.live_feed.FeedSubscription` |
| `qts.runtime.actors.market_data_actor.MarketDataActor._subscribe` | `qts.runtime.actors.market_data_actor.MarketDataActor._subscription_id` |
| `qts.runtime.actors.market_data_actor.MarketDataActor.handle` | `qts.runtime.actors.market_data_actor.MarketDataActor._subscribe` |
| `qts.runtime.actors.market_data_actor.MarketDataActor.handle` | `qts.runtime.actors.market_data_actor.MarketDataActor._publish` |
| `qts.runtime.actors.market_data_actor.MarketDataActor.handle` | `qts.runtime.actors.market_data_actor.MarketDataActor._publish_to_logical_subscribers` |
| `qts.runtime.actors.order_manager_actor.OrderManagerActor.__init__` | `qts.execution.order_manager.OrderManager` |
| `qts.runtime.actors.order_manager_actor.OrderManagerActor._handle_report` | `qts.runtime.actors.account_actor.ApplyFill` |
| `qts.runtime.actors.order_manager_actor.OrderManagerActor._handle_submit` | `qts.runtime.actors.execution_actor.OrderExecutionRequest` |
| `qts.runtime.actors.order_manager_actor.OrderManagerActor.handle` | `qts.runtime.actors.order_manager_actor.OrderManagerActor._handle_submit` |
| `qts.runtime.actors.order_manager_actor.OrderManagerActor.handle` | `qts.runtime.actors.order_manager_actor.OrderManagerActor._handle_report` |
| `qts.runtime.actors.signal_aggregator_actor.SignalAggregatorActor.handle` | `qts.runtime.actors.signal_aggregator_actor.AggregatedSignalBatch` |
| `qts.runtime.actors.strategy_actor.StrategyActor._handle_bar` | `qts.runtime.actors.strategy_actor.StrategyBarResult` |
| `qts.runtime.actors.strategy_actor.StrategyActor._handle_finalize` | `qts.runtime.actors.strategy_actor.StrategyFinalized` |
| `qts.runtime.actors.strategy_actor.StrategyActor.handle` | `qts.runtime.actors.strategy_actor.StrategyActor._handle_bar` |
| `qts.runtime.actors.strategy_actor.StrategyActor.handle` | `qts.runtime.actors.strategy_actor.StrategyActor._handle_finalize` |
| `qts.runtime.event_store.FileEventStore._event_from_json` | `qts.core.ids.EventId` |
| `qts.runtime.event_store.FileEventStore._event_from_json` | `qts.core.ids.CorrelationId` |
| `qts.runtime.event_store.FileEventStore._event_from_json` | `qts.core.ids.CausationId` |
| `qts.runtime.event_store.FileEventStore.append` | `qts.runtime.event_store.FileEventStore.replay` |
| `qts.runtime.event_store.FileEventStore.append` | `qts.runtime.event_store.FileEventStore._event_to_json` |
| `qts.runtime.event_store.FileEventStore.by_correlation_id` | `qts.runtime.event_store.FileEventStore.replay` |
| `qts.runtime.event_store.FileEventStore.replay` | `qts.runtime.event_store.FileEventStore._event_from_json` |
| `qts.runtime.event_store.InMemoryEventStore.append_many` | `qts.runtime.event_store.InMemoryEventStore.append` |
| `qts.runtime.live.LiveRuntime.__init__` | `qts.runtime.live.LiveRuntimeStateMachine` |
| `qts.runtime.live.LiveRuntime.submit_order` | `qts.runtime.live.RuntimeOrderResult` |
| `qts.runtime.live.validate_live_startup` | `qts.runtime.live.LiveStartupDecision` |
| `qts.runtime.router.EventRouter.route` | `qts.runtime.router.RouteNotFoundError` |
| `qts.strategy_sdk.asset_resolver.StrategyAssetResolver.resolve_future` | `qts.strategy_sdk.asset_ref.AssetRef` |
| `qts.strategy_sdk.asset_resolver.StrategyAssetResolver.resolve_option` | `qts.strategy_sdk.asset_ref.AssetRef` |
| `qts.strategy_sdk.asset_resolver.StrategyAssetResolver.resolve_symbol` | `qts.strategy_sdk.asset_ref.AssetRef` |
| `qts.strategy_sdk.context.StrategyContext.__post_init__` | `qts.strategy_sdk.asset_resolver.StrategyAssetResolver` |
| `qts.strategy_sdk.context.StrategyContext.close` | `qts.strategy_sdk.target.TargetIntent` |
| `qts.strategy_sdk.context.StrategyContext.rebalance` | `qts.strategy_sdk.context.StrategyContext.target_percent` |
| `qts.strategy_sdk.context.StrategyContext.subscribe` | `qts.strategy_sdk.subscription_registry.DataSubscription` |
| `qts.strategy_sdk.context.StrategyContext.target_percent` | `qts.strategy_sdk.target.TargetIntent` |
| `qts.strategy_sdk.context.StrategyContext.target_quantity` | `qts.strategy_sdk.target.TargetIntent` |
| `qts.strategy_sdk.context.StrategyContext.target_value` | `qts.strategy_sdk.target.TargetIntent` |
| `qts.strategy_sdk.data_view.DataView.bar` | `qts.strategy_sdk.data_view.DataView.history` |
| `qts.strategy_sdk.data_view.DataView.close` | `qts.strategy_sdk.data_view.DataView.bar` |
| `qts.strategy_sdk.factors.FactorFactory.momentum` | `qts.factors.momentum.MomentumFactor` |
| `qts.strategy_sdk.indicators.IndicatorFactory.sma` | `qts.strategy_sdk.indicators.AssetIndicator` |
| `qts.strategy_sdk.indicators.IndicatorFactory.sma` | `qts.indicators.price.sma.SMA` |
| `qts.strategy_sdk.portfolio_view.PortfolioView.exposure` | `qts.strategy_sdk.portfolio_view.PortfolioView.position` |
| `qts.strategy_sdk.portfolio_view.PortfolioView.position` | `qts.strategy_sdk.portfolio_view.PortfolioPosition` |
| `qts.strategy_sdk.portfolio_view.PortfolioView.weight` | `qts.strategy_sdk.portfolio_view.PortfolioView.exposure` |
| `scripts.bootstrap.main` | `qts.load.bootstrap.bootstrap_local` |
| `scripts.run_backtest.main` | `qts.backtest.runner.run_backtest` |
| `scripts.run_load.main` | `qts.load.synthetic_market_data.generate_bars` |
| `scripts.run_load.main` | `qts.load.synthetic_market_data.SyntheticMarketDataConfig` |
| `scripts.run_load.main` | `qts.core.ids.InstrumentId` |
| `scripts.run_paper.main` | `qts.application.commands.start_paper.start_paper` |
| `scripts.run_paper.main` | `qts.application.commands.start_paper.PaperRuntimeConfig` |
| `scripts.validate_historical.main` | `qts.data.historical.catalog.HistoricalCatalog.from_legacy_root` |
| `scripts.validate_historical.main` | `qts.data.historical.csv_dataset.validate_historical_sample` |
| `scripts.verify_guardrails.main` | `qts.quality.guardrails.main` |