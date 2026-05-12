# 非 Test Python 类、函数、方法与调用关系全量清单

生成时间：2026-05-12T18:13:29+08:00

## 范围与口径

- 源范围：仓库内所有 `.py` 文件，排除 `tests/`、`test_*.py`、`*_test.py`、虚拟环境和构建目录。
- 包含：模块级函数、异步函数、类、实例方法、类方法、静态方法、属性方法、嵌套函数。
- 调用关系：基于 AST 提取每个函数/方法体内的直接 `Call` 表达式，并做可解析的内部符号匹配。
- 作用说明：优先使用源码 docstring 首句；无 docstring 时按符号名称静态推断。

## 汇总

- 非 test Python 文件数：222
- 成功解析文件数：222
- 解析失败文件数：0
- 符号总数：1101
- 类：320
- 函数/方法总数：781
- 模块级函数：145
- 方法/属性：634

### 按类型统计

| 类型 | 数量 |
|---|---:|
| `async_method` | 4 |
| `async_module_function` | 1 |
| `class` | 320 |
| `classmethod` | 35 |
| `method` | 483 |
| `module_function` | 144 |
| `nested_function` | 2 |
| `property` | 53 |
| `staticmethod` | 59 |

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
| `backend/src/qts/api/routes/operations.py` | `qts.api.routes.operations` | 6 |
| `backend/src/qts/api/routes/orders.py` | `qts.api.routes.orders` | 1 |
| `backend/src/qts/api/routes/strategies.py` | `qts.api.routes.strategies` | 3 |
| `backend/src/qts/api/schemas/__init__.py` | `qts.api.schemas` | 0 |
| `backend/src/qts/api/schemas/backtest_schema.py` | `qts.api.schemas.backtest_schema` | 2 |
| `backend/src/qts/api/schemas/common.py` | `qts.api.schemas.common` | 6 |
| `backend/src/qts/api/schemas/operations.py` | `qts.api.schemas.operations` | 5 |
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
| `backend/src/qts/backtest/config.py` | `qts.backtest.config` | 33 |
| `backend/src/qts/backtest/config_loader.py` | `qts.backtest.config_loader` | 5 |
| `backend/src/qts/backtest/dependencies.py` | `qts.backtest.dependencies` | 5 |
| `backend/src/qts/backtest/engine.py` | `qts.backtest.engine` | 5 |
| `backend/src/qts/backtest/historical_data_portal.py` | `qts.backtest.historical_data_portal` | 4 |
| `backend/src/qts/backtest/inputs.py` | `qts.backtest.inputs` | 15 |
| `backend/src/qts/backtest/instrument_context.py` | `qts.backtest.instrument_context` | 10 |
| `backend/src/qts/backtest/intent_processor.py` | `qts.backtest.intent_processor` | 6 |
| `backend/src/qts/backtest/portfolio_projection.py` | `qts.backtest.portfolio_projection` | 5 |
| `backend/src/qts/backtest/report.py` | `qts.backtest.report` | 22 |
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
| `backend/src/qts/data/historical/service.py` | `qts.data.historical.service` | 6 |
| `backend/src/qts/data/historical/symbols.py` | `qts.data.historical.symbols` | 4 |
| `backend/src/qts/data/historical/validation.py` | `qts.data.historical.validation` | 7 |
| `backend/src/qts/data/live/__init__.py` | `qts.data.live` | 0 |
| `backend/src/qts/data/live/adapter.py` | `qts.data.live.adapter` | 10 |
| `backend/src/qts/data/live/capabilities.py` | `qts.data.live.capabilities` | 4 |
| `backend/src/qts/data/live/events.py` | `qts.data.live.events` | 6 |
| `backend/src/qts/data/live/fake_adapter.py` | `qts.data.live.fake_adapter` | 8 |
| `backend/src/qts/data/live/reconnect.py` | `qts.data.live.reconnect` | 3 |
| `backend/src/qts/data/live_feed.py` | `qts.data.live_feed` | 0 |
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
| `backend/src/qts/execution/simulator/__init__.py` | `qts.execution.simulator` | 1 |
| `backend/src/qts/execution/simulator/backtest_execution_adapter.py` | `qts.execution.simulator.backtest_execution_adapter` | 3 |
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
| `backend/src/qts/quality/guardrails.py` | `qts.quality.guardrails` | 55 |
| `backend/src/qts/reconciliation/__init__.py` | `qts.reconciliation` | 0 |
| `backend/src/qts/reconciliation/drift.py` | `qts.reconciliation.drift` | 11 |
| `backend/src/qts/reconciliation/engine.py` | `qts.reconciliation.engine` | 6 |
| `backend/src/qts/reconciliation/report.py` | `qts.reconciliation.report` | 3 |
| `backend/src/qts/reconciliation/snapshots.py` | `qts.reconciliation.snapshots` | 6 |
| `backend/src/qts/reconciliation/startup_gate.py` | `qts.reconciliation.startup_gate` | 2 |
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
| `backend/src/qts/strategy_sdk/asset_resolver.py` | `qts.strategy_sdk.asset_resolver` | 16 |
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
| `scripts/ibkr_collect_environment_evidence.py` | `scripts.ibkr_collect_environment_evidence` | 2 |
| `scripts/ibkr_paper_order_lifecycle_drill.py` | `scripts.ibkr_paper_order_lifecycle_drill` | 2 |
| `scripts/run_api.py` | `scripts.run_api` | 1 |
| `scripts/run_backtest.py` | `scripts.run_backtest` | 1 |
| `scripts/run_load.py` | `scripts.run_load` | 1 |
| `scripts/run_paper.py` | `scripts.run_paper` | 1 |
| `scripts/run_paper_ibkr.py` | `scripts.run_paper_ibkr` | 1 |
| `scripts/run_worker.py` | `scripts.run_worker` | 1 |
| `scripts/validate_historical.py` | `scripts.validate_historical` | 1 |
| `scripts/verify_guardrails.py` | `scripts.verify_guardrails` | 0 |

## 符号清单

### `backend/src/qts/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/api/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/api/app.py`

- `qts.api.app.create_app`
  - 类型：`module_function`
  - 位置：`backend/src/qts/api/app.py:18`
  - 说明：Perform create_app.
  - 直接调用：`FastAPI`, `app.include_router`
  - 可解析内部调用：无

### `backend/src/qts/api/mappers.py`

- `qts.api.mappers.map_backtest_request_schema`
  - 类型：`module_function`
  - 位置：`backend/src/qts/api/mappers.py:12`
  - 说明：Map API input schema into an application DTO.
  - 直接调用：`BacktestRequestDTO`
  - 可解析内部调用：`qts.application.dto.backtest.BacktestRequestDTO`
- `qts.api.mappers.map_backtest_run_dto`
  - 类型：`module_function`
  - 位置：`backend/src/qts/api/mappers.py:18`
  - 说明：Map application output DTO into API response schema.
  - 直接调用：`BacktestRunSchema`
  - 可解析内部调用：`qts.api.schemas.backtest_schema.BacktestRunSchema`
- `qts.api.mappers.map_runtime_state_dto`
  - 类型：`module_function`
  - 位置：`backend/src/qts/api/mappers.py:24`
  - 说明：Map runtime state DTO into response payload.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.api.mappers.map_kill_switch_state_dto`
  - 类型：`module_function`
  - 位置：`backend/src/qts/api/mappers.py:30`
  - 说明：Map kill-switch state DTO into response payload.
  - 直接调用：无
  - 可解析内部调用：无

### `backend/src/qts/api/routes/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/api/routes/accounts.py`

- `qts.api.routes.accounts.account_snapshot`
  - 类型：`module_function`
  - 位置：`backend/src/qts/api/routes/accounts.py:13`
  - 说明：Perform account_snapshot.
  - 直接调用：`AccountSnapshotSchema`, `router.get`
  - 可解析内部调用：`qts.api.schemas.common.AccountSnapshotSchema`, `qts.runtime.mailbox.Mailbox.get`

### `backend/src/qts/api/routes/backtests.py`

- `qts.api.routes.backtests.submit_backtest`
  - 类型：`module_function`
  - 位置：`backend/src/qts/api/routes/backtests.py:19`
  - 说明：Submit a backtest request through the backtest application service.
  - 直接调用：`BacktestService`, `BacktestService.submit`, `map_backtest_request_schema`, `map_backtest_run_dto`, `router.post`
  - 可解析内部调用：`qts.api.mappers.map_backtest_request_schema`, `qts.api.mappers.map_backtest_run_dto`, `qts.application.services.backtest.BacktestService`, `qts.application.services.backtest.BacktestService.submit`

### `backend/src/qts/api/routes/health.py`

- `qts.api.routes.health.health`
  - 类型：`module_function`
  - 位置：`backend/src/qts/api/routes/health.py:13`
  - 说明：Perform health.
  - 直接调用：`HealthService`, `HealthService.status`, `router.get`
  - 可解析内部调用：`qts.application.services.health.HealthService`, `qts.application.services.health.HealthService.status`, `qts.runtime.mailbox.Mailbox.get`

### `backend/src/qts/api/routes/operations.py`

- `qts.api.routes.operations._require_operator`
  - 类型：`module_function`
  - 位置：`backend/src/qts/api/routes/operations.py:24`
  - 说明：Validate X-QTS-Operator header is present.
  - 直接调用：`HTTPException`, `operator.strip`
  - 可解析内部调用：无
- `qts.api.routes.operations.pause_runtime`
  - 类型：`module_function`
  - 位置：`backend/src/qts/api/routes/operations.py:31`
  - 说明：Pause runtime execution for all strategies and data actors.
  - 直接调用：`Header`, `RuntimeCommandResponseSchema`, `_idempotency.run`, `_operations.pause_runtime`, `_require_operator`, `command`, `map_runtime_state_dto`, `router.post`
  - 可解析内部调用：`qts.api.mappers.map_runtime_state_dto`, `qts.api.routes.operations._require_operator`, `qts.api.routes.operations.pause_runtime`, `qts.api.routes.operations.pause_runtime.command`, `qts.api.routes.operations.resume_runtime.command`, `qts.api.schemas.operations.RuntimeCommandResponseSchema`, `qts.api.services.command_idempotency.CommandIdempotencyStore.run`, `qts.application.services.operations.OperationsService.pause_runtime`, `qts.backtest.actor_loop.BacktestActorLoop.run`
- `qts.api.routes.operations.pause_runtime.command`
  - 类型：`nested_function`
  - 位置：`backend/src/qts/api/routes/operations.py:39`
  - 说明：Execute pause command and return updated runtime state.
  - 直接调用：`RuntimeCommandResponseSchema`, `_operations.pause_runtime`, `map_runtime_state_dto`
  - 可解析内部调用：`qts.api.mappers.map_runtime_state_dto`, `qts.api.routes.operations.pause_runtime`, `qts.api.schemas.operations.RuntimeCommandResponseSchema`, `qts.application.services.operations.OperationsService.pause_runtime`
- `qts.api.routes.operations.resume_runtime`
  - 类型：`module_function`
  - 位置：`backend/src/qts/api/routes/operations.py:51`
  - 说明：Resume runtime execution after an operator pause.
  - 直接调用：`Header`, `RuntimeCommandResponseSchema`, `_idempotency.run`, `_operations.resume_runtime`, `_require_operator`, `command`, `map_runtime_state_dto`, `router.post`
  - 可解析内部调用：`qts.api.mappers.map_runtime_state_dto`, `qts.api.routes.operations._require_operator`, `qts.api.routes.operations.pause_runtime.command`, `qts.api.routes.operations.resume_runtime`, `qts.api.routes.operations.resume_runtime.command`, `qts.api.schemas.operations.RuntimeCommandResponseSchema`, `qts.api.services.command_idempotency.CommandIdempotencyStore.run`, `qts.application.services.operations.OperationsService.resume_runtime`, `qts.backtest.actor_loop.BacktestActorLoop.run`
- `qts.api.routes.operations.resume_runtime.command`
  - 类型：`nested_function`
  - 位置：`backend/src/qts/api/routes/operations.py:59`
  - 说明：Execute resume command and return updated runtime state.
  - 直接调用：`RuntimeCommandResponseSchema`, `_operations.resume_runtime`, `map_runtime_state_dto`
  - 可解析内部调用：`qts.api.mappers.map_runtime_state_dto`, `qts.api.routes.operations.resume_runtime`, `qts.api.schemas.operations.RuntimeCommandResponseSchema`, `qts.application.services.operations.OperationsService.resume_runtime`
- `qts.api.routes.operations.activate_kill_switch`
  - 类型：`module_function`
  - 位置：`backend/src/qts/api/routes/operations.py:71`
  - 说明：Activate or refresh a kill-switch for a runtime scope.
  - 直接调用：`Header`, `KillSwitchCommandDTO`, `KillSwitchResponseSchema`, `_operations.activate_kill_switch`, `_require_operator`, `map_kill_switch_state_dto`, `router.post`
  - 可解析内部调用：`qts.api.mappers.map_kill_switch_state_dto`, `qts.api.routes.operations._require_operator`, `qts.api.routes.operations.activate_kill_switch`, `qts.api.schemas.operations.KillSwitchResponseSchema`, `qts.application.dto.operations.KillSwitchCommandDTO`, `qts.application.services.operations.OperationsService.activate_kill_switch`

### `backend/src/qts/api/routes/orders.py`

- `qts.api.routes.orders.order_status`
  - 类型：`module_function`
  - 位置：`backend/src/qts/api/routes/orders.py:13`
  - 说明：Perform order_status.
  - 直接调用：`OrderStatusSchema`, `router.get`
  - 可解析内部调用：`qts.api.schemas.common.OrderStatusSchema`, `qts.runtime.mailbox.Mailbox.get`

### `backend/src/qts/api/routes/strategies.py`

- `qts.api.routes.strategies.list_strategies`
  - 类型：`module_function`
  - 位置：`backend/src/qts/api/routes/strategies.py:13`
  - 说明：Perform list_strategies.
  - 直接调用：`StrategyStatusSchema`, `router.get`
  - 可解析内部调用：`qts.api.schemas.common.StrategyStatusSchema`, `qts.runtime.mailbox.Mailbox.get`
- `qts.api.routes.strategies.start_strategy`
  - 类型：`module_function`
  - 位置：`backend/src/qts/api/routes/strategies.py:19`
  - 说明：Perform start_strategy.
  - 直接调用：`StrategyStatusSchema`, `router.post`
  - 可解析内部调用：`qts.api.schemas.common.StrategyStatusSchema`
- `qts.api.routes.strategies.stop_strategy`
  - 类型：`module_function`
  - 位置：`backend/src/qts/api/routes/strategies.py:25`
  - 说明：Perform stop_strategy.
  - 直接调用：`StrategyStatusSchema`, `router.post`
  - 可解析内部调用：`qts.api.schemas.common.StrategyStatusSchema`

### `backend/src/qts/api/schemas/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/api/schemas/backtest_schema.py`

- `qts.api.schemas.backtest_schema.BacktestRequestSchema`
  - 类型：`class`
  - 位置：`backend/src/qts/api/schemas/backtest_schema.py:8`
  - 说明：HTTP request for submitting a backtest.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.api.schemas.backtest_schema.BacktestRunSchema`
  - 类型：`class`
  - 位置：`backend/src/qts/api/schemas/backtest_schema.py:14`
  - 说明：HTTP response for a submitted backtest.
  - 直接调用：无
  - 可解析内部调用：无

### `backend/src/qts/api/schemas/common.py`

- `qts.api.schemas.common.StrategyStatusSchema`
  - 类型：`class`
  - 位置：`backend/src/qts/api/schemas/common.py:8`
  - 说明：Strategy status response schema.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.api.schemas.common.AccountSnapshotSchema`
  - 类型：`class`
  - 位置：`backend/src/qts/api/schemas/common.py:15`
  - 说明：Account snapshot response schema.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.api.schemas.common.OrderStatusSchema`
  - 类型：`class`
  - 位置：`backend/src/qts/api/schemas/common.py:22`
  - 说明：Order status response schema.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.api.schemas.common.RiskRuleSchema`
  - 类型：`class`
  - 位置：`backend/src/qts/api/schemas/common.py:29`
  - 说明：Risk rule response schema.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.api.schemas.common.OperationalErrorSchema`
  - 类型：`class`
  - 位置：`backend/src/qts/api/schemas/common.py:36`
  - 说明：Operational error response schema.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.api.schemas.common.OperationalErrorSchema.from_exception`
  - 类型：`classmethod`
  - 位置：`backend/src/qts/api/schemas/common.py:44`
  - 说明：Perform from_exception.
  - 直接调用：`cls`
  - 可解析内部调用：无

### `backend/src/qts/api/schemas/operations.py`

- `qts.api.schemas.operations.RuntimeCommandResponseSchema`
  - 类型：`class`
  - 位置：`backend/src/qts/api/schemas/operations.py:10`
  - 说明：Payload for runtime pause/resume commands.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.api.schemas.operations.KillSwitchScopeSchema`
  - 类型：`class`
  - 位置：`backend/src/qts/api/schemas/operations.py:16`
  - 说明：Kill-switch scoping model.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.api.schemas.operations.KillSwitchCommandSchema`
  - 类型：`class`
  - 位置：`backend/src/qts/api/schemas/operations.py:25`
  - 说明：Kill-switch mutation command.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.api.schemas.operations.KillSwitchCommandSchema.validate_scope`
  - 类型：`method`
  - 位置：`backend/src/qts/api/schemas/operations.py:33`
  - 说明：Validate kill-switch command scope constraints.
  - 直接调用：`ValueError`, `model_validator`, `self.reason.strip`, `self.scope_id.strip`
  - 可解析内部调用：无
- `qts.api.schemas.operations.KillSwitchResponseSchema`
  - 类型：`class`
  - 位置：`backend/src/qts/api/schemas/operations.py:44`
  - 说明：Kill-switch current state response.
  - 直接调用：无
  - 可解析内部调用：无

### `backend/src/qts/api/services/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/api/services/command_idempotency.py`

- `qts.api.services.command_idempotency.CommandIdempotencyStore`
  - 类型：`class`
  - 位置：`backend/src/qts/api/services/command_idempotency.py:11`
  - 说明：Remember the first result for each command idempotency key.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.api.services.command_idempotency.CommandIdempotencyStore.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/api/services/command_idempotency.py:14`
  - 说明：Perform __init__.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.api.services.command_idempotency.CommandIdempotencyStore.run`
  - 类型：`method`
  - 位置：`backend/src/qts/api/services/command_idempotency.py:18`
  - 说明：Perform run.
  - 直接调用：`ValueError`, `command`, `key.strip`
  - 可解析内部调用：`qts.api.routes.operations.pause_runtime.command`, `qts.api.routes.operations.resume_runtime.command`

### `backend/src/qts/api/websocket/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/api/websocket/dtos.py`

- `qts.api.websocket.dtos.StreamEventDTO`
  - 类型：`class`
  - 位置：`backend/src/qts/api/websocket/dtos.py:10`
  - 说明：Public stream event DTO.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.api.websocket.dtos.StreamEventDTO.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/api/websocket/dtos.py:18`
  - 说明：Perform post init.
  - 直接调用：`ValueError`, `self.event_type.strip`
  - 可解析内部调用：无

### `backend/src/qts/api/websocket/events.py`

- `qts.api.websocket.events.event_stream`
  - 类型：`async_module_function`
  - 位置：`backend/src/qts/api/websocket/events.py:11`
  - 说明：Perform event_stream.
  - 直接调用：`router.websocket`, `websocket.accept`, `websocket.close`, `websocket.send_json`
  - 可解析内部调用：`qts.api.websocket.manager.JsonWebSocket.accept`, `qts.api.websocket.manager.JsonWebSocket.send_json`, `qts.backtest.report._NdjsonArtifact.close`, `qts.strategy_sdk.context.StrategyContext.close`, `qts.strategy_sdk.data_view.DataView.close`

### `backend/src/qts/api/websocket/fill_adapter.py`

- `qts.api.websocket.fill_adapter.order_fill_to_stream_dto`
  - 类型：`module_function`
  - 位置：`backend/src/qts/api/websocket/fill_adapter.py:11`
  - 说明：Convert an OrderManager-validated fill into a public stream event DTO.
  - 直接调用：`StreamEventDTO`, `datetime.now`, `str`
  - 可解析内部调用：`qts.api.websocket.dtos.StreamEventDTO`

### `backend/src/qts/api/websocket/manager.py`

- `qts.api.websocket.manager.JsonWebSocket`
  - 类型：`class`
  - 位置：`backend/src/qts/api/websocket/manager.py:8`
  - 说明：Minimal WebSocket protocol used by the connection manager.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.api.websocket.manager.JsonWebSocket.accept`
  - 类型：`async_method`
  - 位置：`backend/src/qts/api/websocket/manager.py:11`
  - 说明：Accept the WebSocket connection.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.api.websocket.manager.JsonWebSocket.send_json`
  - 类型：`async_method`
  - 位置：`backend/src/qts/api/websocket/manager.py:15`
  - 说明：Send a JSON-serializable payload.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.api.websocket.manager.WebSocketConnectionManager`
  - 类型：`class`
  - 位置：`backend/src/qts/api/websocket/manager.py:20`
  - 说明：Track WebSocket clients and broadcast JSON payloads.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.api.websocket.manager.WebSocketConnectionManager.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/api/websocket/manager.py:23`
  - 说明：Perform init.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.api.websocket.manager.WebSocketConnectionManager.count`
  - 类型：`property`
  - 位置：`backend/src/qts/api/websocket/manager.py:27`
  - 说明：Perform count.
  - 直接调用：`len`
  - 可解析内部调用：无
- `qts.api.websocket.manager.WebSocketConnectionManager.connect`
  - 类型：`async_method`
  - 位置：`backend/src/qts/api/websocket/manager.py:31`
  - 说明：Perform connect.
  - 直接调用：`self._connections.append`, `websocket.accept`
  - 可解析内部调用：`qts.api.websocket.manager.JsonWebSocket.accept`, `qts.indicators.rolling.RollingWindow.append`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`
- `qts.api.websocket.manager.WebSocketConnectionManager.disconnect`
  - 类型：`method`
  - 位置：`backend/src/qts/api/websocket/manager.py:36`
  - 说明：Perform disconnect.
  - 直接调用：`self._connections.remove`
  - 可解析内部调用：无
- `qts.api.websocket.manager.WebSocketConnectionManager.broadcast`
  - 类型：`async_method`
  - 位置：`backend/src/qts/api/websocket/manager.py:41`
  - 说明：Perform broadcast.
  - 直接调用：`self.disconnect`, `stale.append`, `tuple`, `websocket.send_json`
  - 可解析内部调用：`qts.api.websocket.manager.JsonWebSocket.send_json`, `qts.api.websocket.manager.WebSocketConnectionManager.disconnect`, `qts.indicators.rolling.RollingWindow.append`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`

### `backend/src/qts/application/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/application/commands/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/application/commands/ibkr_environment_evidence.py`

- `qts.application.commands.ibkr_environment_evidence.collect_environment_evidence`
  - 类型：`module_function`
  - 位置：`backend/src/qts/application/commands/ibkr_environment_evidence.py:26`
  - 说明：Collect observe-only evidence and return the output path.
  - 直接调用：`_collect_network_evidence`, `_evidence_filename`, `_merge_validation_errors`, `_read_config`, `_summarize_config`, `datetime.now`, `evidence_path.write_text`, `generated_at.isoformat`, `json.dumps`, `output_dir.mkdir`, `str`
  - 可解析内部调用：`qts.application.commands.ibkr_environment_evidence._collect_network_evidence`, `qts.application.commands.ibkr_environment_evidence._evidence_filename`, `qts.application.commands.ibkr_environment_evidence._merge_validation_errors`, `qts.application.commands.ibkr_environment_evidence._read_config`, `qts.application.commands.ibkr_environment_evidence._summarize_config`, `qts.application.commands.ibkr_paper_order_lifecycle_drill._evidence_filename`, `qts.application.commands.ibkr_paper_order_lifecycle_drill._read_config`, `qts.application.commands.ibkr_paper_order_lifecycle_drill._summarize_config`
- `qts.application.commands.ibkr_environment_evidence.main`
  - 类型：`module_function`
  - 位置：`backend/src/qts/application/commands/ibkr_environment_evidence.py:77`
  - 说明：CLI entrypoint for IBKR environment evidence collection.
  - 直接调用：`argparse.ArgumentParser`, `collect_environment_evidence`, `parser.add_argument`, `parser.parse_args`, `print`
  - 可解析内部调用：`qts.application.commands.ibkr_environment_evidence.collect_environment_evidence`, `scripts.ibkr_collect_environment_evidence.collect_environment_evidence`
- `qts.application.commands.ibkr_environment_evidence._read_config`
  - 类型：`module_function`
  - 位置：`backend/src/qts/application/commands/ibkr_environment_evidence.py:120`
  - 说明：Perform _read_config.
  - 直接调用：`IbkrEnvironmentConfig.from_yaml`, `str`
  - 可解析内部调用：`qts.config.ibkr.IbkrEnvironmentConfig.from_yaml`
- `qts.application.commands.ibkr_environment_evidence._summarize_config`
  - 类型：`module_function`
  - 位置：`backend/src/qts/application/commands/ibkr_environment_evidence.py:130`
  - 说明：Perform _summarize_config.
  - 直接调用：`_env_ref_status`, `bool`
  - 可解析内部调用：`qts.application.commands.ibkr_environment_evidence._env_ref_status`
- `qts.application.commands.ibkr_environment_evidence._merge_validation_errors`
  - 类型：`module_function`
  - 位置：`backend/src/qts/application/commands/ibkr_environment_evidence.py:166`
  - 说明：Perform _merge_validation_errors.
  - 直接调用：`collect_validation_errors`
  - 可解析内部调用：`qts.config.ibkr.collect_validation_errors`
- `qts.application.commands.ibkr_environment_evidence._collect_network_evidence`
  - 类型：`module_function`
  - 位置：`backend/src/qts/application/commands/ibkr_environment_evidence.py:178`
  - 说明：Perform _collect_network_evidence.
  - 直接调用：`_tcp_probe`
  - 可解析内部调用：`qts.application.commands.ibkr_environment_evidence._tcp_probe`
- `qts.application.commands.ibkr_environment_evidence._tcp_probe`
  - 类型：`module_function`
  - 位置：`backend/src/qts/application/commands/ibkr_environment_evidence.py:222`
  - 说明：Perform _tcp_probe.
  - 直接调用：`connection.get`, `isinstance`, `sock.close`, `socket.create_connection`, `str`
  - 可解析内部调用：`qts.backtest.report._NdjsonArtifact.close`, `qts.runtime.mailbox.Mailbox.get`, `qts.strategy_sdk.context.StrategyContext.close`, `qts.strategy_sdk.data_view.DataView.close`
- `qts.application.commands.ibkr_environment_evidence._env_ref_status`
  - 类型：`module_function`
  - 位置：`backend/src/qts/application/commands/ibkr_environment_evidence.py:247`
  - 说明：Perform _env_ref_status.
  - 直接调用：`bool`
  - 可解析内部调用：无
- `qts.application.commands.ibkr_environment_evidence._evidence_filename`
  - 类型：`module_function`
  - 位置：`backend/src/qts/application/commands/ibkr_environment_evidence.py:252`
  - 说明：Perform _evidence_filename.
  - 直接调用：`_safe_label`, `generated_at.strftime`
  - 可解析内部调用：`qts.application.commands.ibkr_environment_evidence._safe_label`, `qts.application.commands.ibkr_paper_order_lifecycle_drill._safe_label`
- `qts.application.commands.ibkr_environment_evidence._safe_label`
  - 类型：`module_function`
  - 位置：`backend/src/qts/application/commands/ibkr_environment_evidence.py:259`
  - 说明：Perform _safe_label.
  - 直接调用：`label.strip`, `re.sub`, `re.sub.strip`
  - 可解析内部调用：无

### `backend/src/qts/application/commands/ibkr_paper_order_lifecycle_drill.py`

- `qts.application.commands.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill`
  - 类型：`module_function`
  - 位置：`backend/src/qts/application/commands/ibkr_paper_order_lifecycle_drill.py:31`
  - 说明：Run a paper-only order-lifecycle drill and persist evidence.
  - 直接调用：`AccountId`, `BrokerId`, `BrokerOrderRequest`, `CancelIntent`, `Decimal`, `FakeBrokerAdapter`, `InstrumentId`, `OrderId`, `OrderIntent`, `OrderManager`, `OrderSide`, `RiskDecision.approve`, `StrategyId`, `ValueError`, `_evidence_filename`, `_execution_report_evidence`, `_read_config`, `_summarize_config`, `_validate_paper_only_ibkr_config`, `broker.cancel_order`, `broker.submit_order`, `datetime.now`, `evidence_path.write_text`, `generated_at.isoformat`, `generated_at.strftime`, `json.dumps`, `manager.create_order`, `manager.mark_sent`, `manager.process_report`, `manager.request_cancel`, `normalize_broker_execution_report`, `output_dir.mkdir`, `str`
  - 可解析内部调用：`qts.application.commands.ibkr_environment_evidence._evidence_filename`, `qts.application.commands.ibkr_environment_evidence._read_config`, `qts.application.commands.ibkr_environment_evidence._summarize_config`, `qts.application.commands.ibkr_paper_order_lifecycle_drill._evidence_filename`, `qts.application.commands.ibkr_paper_order_lifecycle_drill._execution_report_evidence`, `qts.application.commands.ibkr_paper_order_lifecycle_drill._read_config`, `qts.application.commands.ibkr_paper_order_lifecycle_drill._summarize_config`, `qts.application.commands.ibkr_paper_order_lifecycle_drill._validate_paper_only_ibkr_config`, `qts.core.ids.AccountId`, `qts.core.ids.BrokerId`, `qts.core.ids.InstrumentId`, `qts.core.ids.OrderId`, `qts.core.ids.StrategyId`, `qts.domain.orders.value_objects.CancelIntent`, `qts.domain.orders.value_objects.OrderIntent`, `qts.domain.orders.value_objects.OrderSide`, `qts.domain.risk.decision.RiskDecision.approve`, `qts.execution.broker.BrokerAdapter.cancel_order`, `qts.execution.broker.BrokerAdapter.submit_order`, `qts.execution.broker.BrokerOrderRequest`, `qts.execution.broker.FakeBrokerAdapter`, `qts.execution.broker.FakeBrokerAdapter.cancel_order`, `qts.execution.broker.FakeBrokerAdapter.submit_order`, `qts.execution.broker.normalize_broker_execution_report`, `qts.execution.order_manager.OrderManager`, `qts.execution.order_manager.OrderManager.create_order`, `qts.execution.order_manager.OrderManager.mark_sent`, `qts.execution.order_manager.OrderManager.process_report`, `qts.execution.order_manager.OrderManager.request_cancel`, `qts.runtime.live.LiveRuntime.submit_order`
- `qts.application.commands.ibkr_paper_order_lifecycle_drill.main`
  - 类型：`module_function`
  - 位置：`backend/src/qts/application/commands/ibkr_paper_order_lifecycle_drill.py:142`
  - 说明：CLI entrypoint for paper order lifecycle evidence.
  - 直接调用：`Decimal`, `argparse.ArgumentParser`, `parser.add_argument`, `parser.parse_args`, `print`, `run_paper_order_lifecycle_drill`
  - 可解析内部调用：`qts.application.commands.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill`, `scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill`
- `qts.application.commands.ibkr_paper_order_lifecycle_drill._read_config`
  - 类型：`module_function`
  - 位置：`backend/src/qts/application/commands/ibkr_paper_order_lifecycle_drill.py:187`
  - 说明：Perform _read_config.
  - 直接调用：`IbkrEnvironmentConfig.from_yaml`, `str`
  - 可解析内部调用：`qts.config.ibkr.IbkrEnvironmentConfig.from_yaml`
- `qts.application.commands.ibkr_paper_order_lifecycle_drill._validate_paper_only_ibkr_config`
  - 类型：`module_function`
  - 位置：`backend/src/qts/application/commands/ibkr_paper_order_lifecycle_drill.py:197`
  - 说明：Perform _validate_paper_only_ibkr_config.
  - 直接调用：`ValueError`, `collect_validation_errors`, `config.order_execution.account_id.upper`, `config.order_execution.account_id.upper.startswith`, `errors.append`, `errors.extend`, `join`
  - 可解析内部调用：`qts.config.ibkr.collect_validation_errors`, `qts.indicators.rolling.RollingWindow.append`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`
- `qts.application.commands.ibkr_paper_order_lifecycle_drill._summarize_config`
  - 类型：`module_function`
  - 位置：`backend/src/qts/application/commands/ibkr_paper_order_lifecycle_drill.py:221`
  - 说明：Perform _summarize_config.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.application.commands.ibkr_paper_order_lifecycle_drill._execution_report_evidence`
  - 类型：`module_function`
  - 位置：`backend/src/qts/application/commands/ibkr_paper_order_lifecycle_drill.py:237`
  - 说明：Perform _execution_report_evidence.
  - 直接调用：`TypeError`, `isinstance`, `str`
  - 可解析内部调用：无
- `qts.application.commands.ibkr_paper_order_lifecycle_drill._evidence_filename`
  - 类型：`module_function`
  - 位置：`backend/src/qts/application/commands/ibkr_paper_order_lifecycle_drill.py:251`
  - 说明：Perform _evidence_filename.
  - 直接调用：`_safe_label`, `generated_at.strftime`
  - 可解析内部调用：`qts.application.commands.ibkr_environment_evidence._safe_label`, `qts.application.commands.ibkr_paper_order_lifecycle_drill._safe_label`
- `qts.application.commands.ibkr_paper_order_lifecycle_drill._safe_label`
  - 类型：`module_function`
  - 位置：`backend/src/qts/application/commands/ibkr_paper_order_lifecycle_drill.py:258`
  - 说明：Perform _safe_label.
  - 直接调用：`label.strip`, `re.sub`, `re.sub.strip`
  - 可解析内部调用：无

### `backend/src/qts/application/commands/start_paper.py`

- `qts.application.commands.start_paper.PaperRuntimeConfig`
  - 类型：`class`
  - 位置：`backend/src/qts/application/commands/start_paper.py:10`
  - 说明：Paper runtime configuration without real broker credentials.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.application.commands.start_paper.PaperRuntimeConfig.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/application/commands/start_paper.py:18`
  - 说明：Perform __post_init__.
  - 直接调用：`Decimal`, `ValueError`, `self.account_id.strip`, `self.data_source.strip`
  - 可解析内部调用：无
- `qts.application.commands.start_paper.PaperRuntime`
  - 类型：`class`
  - 位置：`backend/src/qts/application/commands/start_paper.py:29`
  - 说明：Constructed paper runtime descriptor.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.application.commands.start_paper.start_paper`
  - 类型：`module_function`
  - 位置：`backend/src/qts/application/commands/start_paper.py:36`
  - 说明：Construct the paper runtime boundary without connecting to a real broker.
  - 直接调用：`PaperRuntime`
  - 可解析内部调用：`qts.application.commands.start_paper.PaperRuntime`

### `backend/src/qts/application/dto/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/application/dto/backtest.py`

- `qts.application.dto.backtest.BacktestRequestDTO`
  - 类型：`class`
  - 位置：`backend/src/qts/application/dto/backtest.py:9`
  - 说明：Stable application request for starting a backtest.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.application.dto.backtest.BacktestRequestDTO.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/application/dto/backtest.py:14`
  - 说明：Perform __post_init__.
  - 直接调用：`ValueError`, `self.strategy_name.strip`
  - 可解析内部调用：无
- `qts.application.dto.backtest.BacktestRunDTO`
  - 类型：`class`
  - 位置：`backend/src/qts/application/dto/backtest.py:21`
  - 说明：Stable application response for a submitted backtest.
  - 直接调用：无
  - 可解析内部调用：无

### `backend/src/qts/application/dto/health.py`

- `qts.application.dto.health.HealthStatusDTO`
  - 类型：`class`
  - 位置：`backend/src/qts/application/dto/health.py:9`
  - 说明：Stable health status response.
  - 直接调用：无
  - 可解析内部调用：无

### `backend/src/qts/application/dto/operations.py`

- `qts.application.dto.operations.RuntimeStateDTO`
  - 类型：`class`
  - 位置：`backend/src/qts/application/dto/operations.py:9`
  - 说明：Stable runtime state response.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.application.dto.operations.KillSwitchCommandDTO`
  - 类型：`class`
  - 位置：`backend/src/qts/application/dto/operations.py:16`
  - 说明：Stable kill-switch activation request.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.application.dto.operations.KillSwitchCommandDTO.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/application/dto/operations.py:23`
  - 说明：Perform __post_init__.
  - 直接调用：`ValueError`, `self.reason.strip`, `self.scope.strip`, `self.scope_id.strip`
  - 可解析内部调用：无
- `qts.application.dto.operations.KillSwitchStateDTO`
  - 类型：`class`
  - 位置：`backend/src/qts/application/dto/operations.py:34`
  - 说明：Stable kill-switch state response.
  - 直接调用：无
  - 可解析内部调用：无

### `backend/src/qts/application/dto/order_events.py`

- `qts.application.dto.order_events.OrderFillDTO`
  - 类型：`class`
  - 位置：`backend/src/qts/application/dto/order_events.py:10`
  - 说明：Stable fill event shape for public streams.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.application.dto.order_events.OrderFillDTO.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/application/dto/order_events.py:20`
  - 说明：Perform __post_init__.
  - 直接调用：`ValueError`, `self.fill_id.strip`, `self.instrument_id.strip`, `self.order_id.strip`, `self.side.strip`
  - 可解析内部调用：无

### `backend/src/qts/application/services/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/application/services/backtest.py`

- `qts.application.services.backtest.BacktestService`
  - 类型：`class`
  - 位置：`backend/src/qts/application/services/backtest.py:10`
  - 说明：Application boundary for backtest use cases.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.application.services.backtest.BacktestService.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/application/services/backtest.py:13`
  - 说明：Perform __init__.
  - 直接调用：`count`
  - 可解析内部调用：`qts.api.websocket.manager.WebSocketConnectionManager.count`
- `qts.application.services.backtest.BacktestService.submit`
  - 类型：`method`
  - 位置：`backend/src/qts/application/services/backtest.py:17`
  - 说明：Perform submit.
  - 直接调用：`BacktestRunDTO`, `next`
  - 可解析内部调用：`qts.application.dto.backtest.BacktestRunDTO`

### `backend/src/qts/application/services/health.py`

- `qts.application.services.health.HealthService`
  - 类型：`class`
  - 位置：`backend/src/qts/application/services/health.py:8`
  - 说明：Returns platform health without exposing internals.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.application.services.health.HealthService.status`
  - 类型：`method`
  - 位置：`backend/src/qts/application/services/health.py:11`
  - 说明：Perform status.
  - 直接调用：`HealthStatusDTO`
  - 可解析内部调用：`qts.application.dto.health.HealthStatusDTO`

### `backend/src/qts/application/services/interfaces.py`

- `qts.application.services.interfaces.AccountService`
  - 类型：`class`
  - 位置：`backend/src/qts/application/services/interfaces.py:8`
  - 说明：Account query service boundary.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.application.services.interfaces.AccountService.snapshot`
  - 类型：`method`
  - 位置：`backend/src/qts/application/services/interfaces.py:11`
  - 说明：Return an account snapshot.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.application.services.interfaces.OrderService`
  - 类型：`class`
  - 位置：`backend/src/qts/application/services/interfaces.py:16`
  - 说明：Order query service boundary.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.application.services.interfaces.OrderService.status`
  - 类型：`method`
  - 位置：`backend/src/qts/application/services/interfaces.py:19`
  - 说明：Return order status.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.application.services.interfaces.RiskService`
  - 类型：`class`
  - 位置：`backend/src/qts/application/services/interfaces.py:24`
  - 说明：Risk query service boundary.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.application.services.interfaces.RiskService.rules`
  - 类型：`method`
  - 位置：`backend/src/qts/application/services/interfaces.py:27`
  - 说明：Return configured risk rules.
  - 直接调用：无
  - 可解析内部调用：无

### `backend/src/qts/application/services/operations.py`

- `qts.application.services.operations.OperationsService`
  - 类型：`class`
  - 位置：`backend/src/qts/application/services/operations.py:9`
  - 说明：Owns operational state without leaking runtime internals into API routes.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.application.services.operations.OperationsService.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/application/services/operations.py:12`
  - 说明：Perform __init__.
  - 直接调用：`KillSwitchRegistry`
  - 可解析内部调用：`qts.risk.kill_switch.KillSwitchRegistry`
- `qts.application.services.operations.OperationsService.pause_runtime`
  - 类型：`method`
  - 位置：`backend/src/qts/application/services/operations.py:17`
  - 说明：Perform pause_runtime.
  - 直接调用：`RuntimeStateDTO`
  - 可解析内部调用：`qts.application.dto.operations.RuntimeStateDTO`
- `qts.application.services.operations.OperationsService.resume_runtime`
  - 类型：`method`
  - 位置：`backend/src/qts/application/services/operations.py:22`
  - 说明：Perform resume_runtime.
  - 直接调用：`RuntimeStateDTO`
  - 可解析内部调用：`qts.application.dto.operations.RuntimeStateDTO`
- `qts.application.services.operations.OperationsService.activate_kill_switch`
  - 类型：`method`
  - 位置：`backend/src/qts/application/services/operations.py:27`
  - 说明：Perform activate_kill_switch.
  - 直接调用：`KillSwitchStateDTO`, `self._kill_switches.activate`, `self._scope_from_command`
  - 可解析内部调用：`qts.application.dto.operations.KillSwitchStateDTO`, `qts.application.services.operations.OperationsService._scope_from_command`, `qts.risk.kill_switch.KillSwitchRegistry.activate`
- `qts.application.services.operations.OperationsService._scope_from_command`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/application/services/operations.py:39`
  - 说明：Perform _scope_from_command.
  - 直接调用：`KillSwitchScope`, `KillSwitchScope.global_scope`, `KillSwitchScopeType`
  - 可解析内部调用：`qts.risk.kill_switch.KillSwitchScope`, `qts.risk.kill_switch.KillSwitchScope.global_scope`, `qts.risk.kill_switch.KillSwitchScopeType`

### `backend/src/qts/application/services/strategy_service.py`

- `qts.application.services.strategy_service.StrategyLifecycleService`
  - 类型：`class`
  - 位置：`backend/src/qts/application/services/strategy_service.py:9`
  - 说明：Start, stop, and inspect configured strategy instances.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.application.services.strategy_service.StrategyLifecycleService.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/application/services/strategy_service.py:12`
  - 说明：Perform __init__.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.application.services.strategy_service.StrategyLifecycleService.add`
  - 类型：`method`
  - 位置：`backend/src/qts/application/services/strategy_service.py:21`
  - 说明：Perform add.
  - 直接调用：`ValueError`
  - 可解析内部调用：无
- `qts.application.services.strategy_service.StrategyLifecycleService.start`
  - 类型：`method`
  - 位置：`backend/src/qts/application/services/strategy_service.py:29`
  - 说明：Perform start.
  - 直接调用：`self._require_enabled`
  - 可解析内部调用：`qts.application.services.strategy_service.StrategyLifecycleService._require_enabled`
- `qts.application.services.strategy_service.StrategyLifecycleService.stop`
  - 类型：`method`
  - 位置：`backend/src/qts/application/services/strategy_service.py:35`
  - 说明：Perform stop.
  - 直接调用：`self._require_enabled`
  - 可解析内部调用：`qts.application.services.strategy_service.StrategyLifecycleService._require_enabled`
- `qts.application.services.strategy_service.StrategyLifecycleService.status`
  - 类型：`method`
  - 位置：`backend/src/qts/application/services/strategy_service.py:41`
  - 说明：Perform status.
  - 直接调用：`self._require_enabled`
  - 可解析内部调用：`qts.application.services.strategy_service.StrategyLifecycleService._require_enabled`
- `qts.application.services.strategy_service.StrategyLifecycleService.list_instances`
  - 类型：`method`
  - 位置：`backend/src/qts/application/services/strategy_service.py:46`
  - 说明：Perform list_instances.
  - 直接调用：`self._instances.values`, `tuple`
  - 可解析内部调用：无
- `qts.application.services.strategy_service.StrategyLifecycleService._require_enabled`
  - 类型：`method`
  - 位置：`backend/src/qts/application/services/strategy_service.py:50`
  - 说明：Perform _require_enabled.
  - 直接调用：`ValueError`
  - 可解析内部调用：无

### `backend/src/qts/application/strategy_lifecycle.py`

- `qts.application.strategy_lifecycle.StrategyStatus`
  - 类型：`class`
  - 位置：`backend/src/qts/application/strategy_lifecycle.py:14`
  - 说明：Configured strategy instance lifecycle status.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.application.strategy_lifecycle.StrategyInstance`
  - 类型：`class`
  - 位置：`backend/src/qts/application/strategy_lifecycle.py:22`
  - 说明：Configured runtime instance of a Strategy class.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.application.strategy_lifecycle.StrategyInstance.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/application/strategy_lifecycle.py:32`
  - 说明：Perform __post_init__.
  - 直接调用：`Decimal`, `ValueError`, `self.class_path.strip`
  - 可解析内部调用：无
- `qts.application.strategy_lifecycle.StrategyRegistry`
  - 类型：`class`
  - 位置：`backend/src/qts/application/strategy_lifecycle.py:40`
  - 说明：Safe registry for explicitly approved strategy classes.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.application.strategy_lifecycle.StrategyRegistry.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/application/strategy_lifecycle.py:43`
  - 说明：Perform __init__.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.application.strategy_lifecycle.StrategyRegistry.register`
  - 类型：`method`
  - 位置：`backend/src/qts/application/strategy_lifecycle.py:47`
  - 说明：Perform register.
  - 直接调用：`ValueError`, `class_path.strip`
  - 可解析内部调用：无
- `qts.application.strategy_lifecycle.StrategyRegistry.resolve`
  - 类型：`method`
  - 位置：`backend/src/qts/application/strategy_lifecycle.py:55`
  - 说明：Perform resolve.
  - 直接调用：`KeyError`
  - 可解析内部调用：无

### `backend/src/qts/backtest/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/backtest/actor_loop.py`

- `qts.backtest.actor_loop.BacktestActorLoopResult`
  - 类型：`class`
  - 位置：`backend/src/qts/backtest/actor_loop.py:43`
  - 说明：Result summary produced by an actor loop run.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.actor_loop.BacktestActorLoopResult.processed_bars`
  - 类型：`property`
  - 位置：`backend/src/qts/backtest/actor_loop.py:52`
  - 说明：Perform processed_bars.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.actor_loop.BacktestActorLoop`
  - 类型：`class`
  - 位置：`backend/src/qts/backtest/actor_loop.py:57`
  - 说明：Run backtest bars through strategy/order execution actors.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.actor_loop.BacktestActorLoop.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/actor_loop.py:60`
  - 说明：Perform __init__.
  - 直接调用：`dict`
  - 可解析内部调用：无
- `qts.backtest.actor_loop.BacktestActorLoop._take_strategy_bar_result`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/backtest/actor_loop.py:85`
  - 说明：Perform _take_strategy_bar_result.
  - 直接调用：`RuntimeError`, `TypeError`, `isinstance`, `mailbox.empty`, `mailbox.get`, `type`
  - 可解析内部调用：`qts.runtime.mailbox.Mailbox.empty`, `qts.runtime.mailbox.Mailbox.get`
- `qts.backtest.actor_loop.BacktestActorLoop._take_signal_batch`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/backtest/actor_loop.py:97`
  - 说明：Perform _take_signal_batch.
  - 直接调用：`RuntimeError`, `TypeError`, `isinstance`, `mailbox.empty`, `mailbox.get`, `type`
  - 可解析内部调用：`qts.runtime.mailbox.Mailbox.empty`, `qts.runtime.mailbox.Mailbox.get`
- `qts.backtest.actor_loop.BacktestActorLoop._take_strategy_finalized`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/backtest/actor_loop.py:109`
  - 说明：Perform _take_strategy_finalized.
  - 直接调用：`RuntimeError`, `TypeError`, `isinstance`, `mailbox.empty`, `mailbox.get`, `type`
  - 可解析内部调用：`qts.runtime.mailbox.Mailbox.empty`, `qts.runtime.mailbox.Mailbox.get`
- `qts.backtest.actor_loop.BacktestActorLoop._market_data_ref_for`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/actor_loop.py:120`
  - 说明：Perform _market_data_ref_for.
  - 直接调用：`ActorRef`, `Mailbox`, `MarketDataActor`, `RuntimeError`, `refs.get`
  - 可解析内部调用：`qts.runtime.actor_ref.ActorRef`, `qts.runtime.actors.market_data_actor.MarketDataActor`, `qts.runtime.mailbox.Mailbox`, `qts.runtime.mailbox.Mailbox.get`
- `qts.backtest.actor_loop.BacktestActorLoop._history_limit_from_subscriptions`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/backtest/actor_loop.py:154`
  - 说明：Perform _history_limit_from_subscriptions.
  - 直接调用：`max`
  - 可解析内部调用：无
- `qts.backtest.actor_loop.BacktestActorLoop._resolve_actor_classes`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/backtest/actor_loop.py:161`
  - 说明：Perform _resolve_actor_classes.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.actor_loop.BacktestActorLoop.run`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/actor_loop.py:169`
  - 说明：Perform run.
  - 直接调用：`AccountActor`, `ActorRef`, `BacktestActorLoopResult`, `ExecutionActor`, `HistoricalDataPortal`, `Mailbox`, `MarketDataEvent`, `OrderManagerActor`, `StrategyBarEvent`, `StrategyContext`, `StrategyFinalize`, `StrategySignalEvent`, `TypeError`, `account_actor.snapshot`, `defaultdict`, `history.append`, `isinstance`, `len`, `market_data_mailbox.empty`, `market_data_mailbox.get`, `market_data_ref.process_all`, `market_data_ref.tell`, `order_manager_actor.compact_for_streaming`, `portal.data_view`, `self._equity_point`, `self._history_limit_from_subscriptions`, `self._market_data_ref_for`, `self._portfolio_view`, `self._process_intent`, `self._resolve_actor_classes`, `self._take_signal_batch`, `self._take_strategy_bar_result`, `self._take_strategy_finalized`, `self._update_rolling_prices`, `signal_aggregator_actor`, `signal_ref.process_all`, `signal_ref.tell`, `sink.write_equity_point`, `sink.write_processed`, `strategy_actor`, `strategy_ref.process_all`, `strategy_ref.tell`, `type`
  - 可解析内部调用：`qts.application.services.interfaces.AccountService.snapshot`, `qts.backtest.actor_loop.BacktestActorLoop._history_limit_from_subscriptions`, `qts.backtest.actor_loop.BacktestActorLoop._market_data_ref_for`, `qts.backtest.actor_loop.BacktestActorLoop._resolve_actor_classes`, `qts.backtest.actor_loop.BacktestActorLoop._take_signal_batch`, `qts.backtest.actor_loop.BacktestActorLoop._take_strategy_bar_result`, `qts.backtest.actor_loop.BacktestActorLoop._take_strategy_finalized`, `qts.backtest.actor_loop.BacktestActorLoopResult`, `qts.backtest.historical_data_portal.HistoricalDataPortal`, `qts.backtest.historical_data_portal.HistoricalDataPortal.data_view`, `qts.backtest.report.StreamingBacktestArtifactWriter.write_equity_point`, `qts.backtest.sinks.BacktestStreamingSink.write_equity_point`, `qts.backtest.sinks.BacktestStreamingSink.write_processed`, `qts.execution.idempotency.FillIdempotencyStore.snapshot`, `qts.execution.order_manager.OrderManager.snapshot`, `qts.indicators.rolling.RollingWindow.append`, `qts.indicators.rolling.RollingWindow.snapshot`, `qts.observability.metrics.MetricsRegistry.snapshot`, `qts.portfolio.position_book.PositionBook.snapshot`, `qts.runtime.actor_ref.ActorRef`, `qts.runtime.actor_ref.ActorRef.process_all`, `qts.runtime.actor_ref.ActorRef.tell`, `qts.runtime.actors.account_actor.AccountActor`, `qts.runtime.actors.account_actor.AccountActor.snapshot`, `qts.runtime.actors.execution_actor.ExecutionActor`, `qts.runtime.actors.market_data_actor.MarketDataEvent`, `qts.runtime.actors.order_manager_actor.OrderManagerActor`, `qts.runtime.actors.order_manager_actor.OrderManagerActor.compact_for_streaming`, `qts.runtime.actors.signal_aggregator_actor.StrategySignalEvent`, `qts.runtime.actors.strategy_actor.StrategyBarEvent`, `qts.runtime.actors.strategy_actor.StrategyFinalize`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`, `qts.runtime.mailbox.Mailbox`, `qts.runtime.mailbox.Mailbox.empty`, `qts.runtime.mailbox.Mailbox.get`, `qts.strategy_sdk.context.StrategyContext`

### `backend/src/qts/backtest/config.py`

- `qts.backtest.config.BacktestCostModel`
  - 类型：`class`
  - 位置：`backend/src/qts/backtest/config.py:23`
  - 说明：Backtest execution fee and slippage assumptions.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.config.BacktestCostModel.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/config.py:29`
  - 说明：Validate and normalize decimal inputs.
  - 直接调用：`Decimal`, `ValueError`, `object.__setattr__`, `str`
  - 可解析内部调用：无
- `qts.backtest.config.BacktestCostModel.to_payload`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/config.py:42`
  - 说明：Serialize cost assumptions for hashing and reporting.
  - 直接调用：`str`
  - 可解析内部调用：无
- `qts.backtest.config.BacktestCostModel.slippage_model`
  - 类型：`property`
  - 位置：`backend/src/qts/backtest/config.py:50`
  - 说明：Describe whether slippage is modeled.
  - 直接调用：`Decimal`
  - 可解析内部调用：无
- `qts.backtest.config.BacktestCostModel.commission_model`
  - 类型：`property`
  - 位置：`backend/src/qts/backtest/config.py:55`
  - 说明：Describe commission handling for reports.
  - 直接调用：`Decimal`
  - 可解析内部调用：无
- `qts.backtest.config.BacktestEngineConfig`
  - 类型：`class`
  - 位置：`backend/src/qts/backtest/config.py:63`
  - 说明：Stable run-level inputs for constructing a backtest engine.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.config.BacktestEngineConfig.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/config.py:74`
  - 说明：Normalize and validate constructor inputs.
  - 直接调用：`Decimal`, `ValueError`, `dict`, `object.__setattr__`, `self.target_timeframe.strip`, `str`, `tuple`
  - 可解析内部调用：无
- `qts.backtest.config.BacktestEngineConfig.from_legacy_kwargs`
  - 类型：`classmethod`
  - 位置：`backend/src/qts/backtest/config.py:87`
  - 说明：Build from constructor-style legacy fields.
  - 直接调用：`BacktestCostModel`, `cls`, `dict`, `tuple`
  - 可解析内部调用：`qts.backtest.config.BacktestCostModel`
- `qts.backtest.config.BacktestEngineConfig.to_payload`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/config.py:109`
  - 说明：Serialize this engine config for stable hashing.
  - 直接调用：`dataset_metadata_payload`, `dict`, `self.cost_model.to_payload`, `str`, `tuple`
  - 可解析内部调用：`qts.backtest.config.BacktestCostModel.to_payload`, `qts.backtest.config.BacktestEngineConfig.to_payload`, `qts.backtest.config.BacktestMarketDataReference.to_payload`, `qts.backtest.config.BacktestRunConfig.to_payload`, `qts.backtest.config.BacktestStrategyConfig.to_payload`, `qts.backtest.config.CostModelConfig.to_payload`, `qts.backtest.config.RiskConfig.to_payload`, `qts.backtest.config.RollPolicyConfig.to_payload`, `qts.backtest.report.StreamingEquityMetrics.to_payload`, `qts.backtest.report.dataset_metadata_payload`, `qts.data.sessions.window.RegularSessionWindow.to_payload`
- `qts.backtest.config.CostModelConfig`
  - 类型：`class`
  - 位置：`backend/src/qts/backtest/config.py:128`
  - 说明：Explicit backtest cost model settings.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.config.CostModelConfig.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/config.py:134`
  - 说明：Perform __post_init__.
  - 直接调用：`Decimal`, `ValueError`, `object.__setattr__`, `str`
  - 可解析内部调用：无
- `qts.backtest.config.CostModelConfig.to_payload`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/config.py:147`
  - 说明：Perform to_payload.
  - 直接调用：`str`
  - 可解析内部调用：无
- `qts.backtest.config.RiskConfig`
  - 类型：`class`
  - 位置：`backend/src/qts/backtest/config.py:156`
  - 说明：Backtest risk settings.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.config.RiskConfig.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/config.py:161`
  - 说明：Perform __post_init__.
  - 直接调用：`Decimal`, `ValueError`, `object.__setattr__`, `str`
  - 可解析内部调用：无
- `qts.backtest.config.RiskConfig.to_payload`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/config.py:167`
  - 说明：Perform to_payload.
  - 直接调用：`str`
  - 可解析内部调用：无
- `qts.backtest.config.RollPolicyConfig`
  - 类型：`class`
  - 位置：`backend/src/qts/backtest/config.py:173`
  - 说明：Continuous futures roll policy for config-driven backtest runs.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.config.RollPolicyConfig.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/config.py:179`
  - 说明：Perform __post_init__.
  - 直接调用：`ValueError`, `object.__setattr__`, `self.method.strip`, `self.method.strip.lower`
  - 可解析内部调用：无
- `qts.backtest.config.RollPolicyConfig.to_payload`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/config.py:186`
  - 说明：Perform to_payload.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.config.BacktestMarketDataReference`
  - 类型：`class`
  - 位置：`backend/src/qts/backtest/config.py:192`
  - 说明：Market data source reference for one backtest run.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.config.BacktestMarketDataReference.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/config.py:199`
  - 说明：Perform __post_init__.
  - 直接调用：`Path`, `ValueError`, `object.__setattr__`, `self.catalog.strip`, `self.source.strip`, `self.source.strip.lower`
  - 可解析内部调用：无
- `qts.backtest.config.BacktestMarketDataReference.is_configured`
  - 类型：`property`
  - 位置：`backend/src/qts/backtest/config.py:218`
  - 说明：Perform is_configured.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.config.BacktestMarketDataReference.to_payload`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/config.py:222`
  - 说明：Perform to_payload.
  - 直接调用：`RuntimeError`, `str`
  - 可解析内部调用：无
- `qts.backtest.config.BacktestStrategyConfig`
  - 类型：`class`
  - 位置：`backend/src/qts/backtest/config.py:235`
  - 说明：Configured strategy instance referenced by a backtest run.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.config.BacktestStrategyConfig.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/config.py:245`
  - 说明：Perform __post_init__.
  - 直接调用：`Decimal`, `ValueError`, `dict`, `object.__setattr__`, `self.account_id.strip`, `self.class_path.strip`, `self.strategy_id.strip`, `str`
  - 可解析内部调用：无
- `qts.backtest.config.BacktestStrategyConfig.from_yaml`
  - 类型：`classmethod`
  - 位置：`backend/src/qts/backtest/config.py:259`
  - 说明：Perform from_yaml.
  - 直接调用：`ValueError`, `cls._parse_payload`, `isinstance`, `path.read_text`, `yaml.safe_load`
  - 可解析内部调用：`qts.backtest.config.BacktestStrategyConfig._parse_payload`
- `qts.backtest.config.BacktestStrategyConfig.to_payload`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/config.py:266`
  - 说明：Perform to_payload.
  - 直接调用：`str`
  - 可解析内部调用：无
- `qts.backtest.config.BacktestStrategyConfig._parse_payload`
  - 类型：`classmethod`
  - 位置：`backend/src/qts/backtest/config.py:278`
  - 说明：Perform _parse_payload.
  - 直接调用：`Decimal`, `ValueError`, `bool`, `cls`, `isinstance`, `payload.get`, `str`
  - 可解析内部调用：`qts.runtime.mailbox.Mailbox.get`
- `qts.backtest.config.BacktestRunConfig`
  - 类型：`class`
  - 位置：`backend/src/qts/backtest/config.py:298`
  - 说明：Complete identity for a backtest run.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.config.BacktestRunConfig.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/config.py:322`
  - 说明：Perform __post_init__.
  - 直接调用：`BacktestMarketDataReference`, `BacktestStrategyConfig`, `Decimal`, `InstrumentId`, `Path`, `ValueError`, `all`, `dict`, `isinstance`, `object.__setattr__`, `root.strip`, `self._normalize_symbol`, `self.historical_data.to_payload`, `self.instrument_ids.items`, `self.market_data.to_payload`, `self.strategy_class.strip`, `self.timeframe.strip`, `str`, `tuple`
  - 可解析内部调用：`qts.backtest.config.BacktestCostModel.to_payload`, `qts.backtest.config.BacktestEngineConfig.to_payload`, `qts.backtest.config.BacktestMarketDataReference`, `qts.backtest.config.BacktestMarketDataReference.to_payload`, `qts.backtest.config.BacktestRunConfig._normalize_symbol`, `qts.backtest.config.BacktestRunConfig.to_payload`, `qts.backtest.config.BacktestStrategyConfig`, `qts.backtest.config.BacktestStrategyConfig.to_payload`, `qts.backtest.config.CostModelConfig.to_payload`, `qts.backtest.config.RiskConfig.to_payload`, `qts.backtest.config.RollPolicyConfig.to_payload`, `qts.backtest.report.StreamingEquityMetrics.to_payload`, `qts.core.ids.InstrumentId`, `qts.data.historical.catalog.HistoricalCatalogLoadConfig._normalize_symbol`, `qts.data.sessions.window.RegularSessionWindow.to_payload`, `qts.registry.instrument_registry.InstrumentRegistry._normalize_symbol`, `qts.registry.symbol_resolution.StaticSymbolResolver._normalize_symbol`
- `qts.backtest.config.BacktestRunConfig.from_yaml`
  - 类型：`classmethod`
  - 位置：`backend/src/qts/backtest/config.py:388`
  - 说明：Perform from_yaml.
  - 直接调用：`BacktestConfigLoader.from_path`
  - 可解析内部调用：`qts.backtest.config_loader.BacktestConfigLoader.from_path`
- `qts.backtest.config.BacktestRunConfig.config_hash`
  - 类型：`property`
  - 位置：`backend/src/qts/backtest/config.py:395`
  - 说明：Perform config_hash.
  - 直接调用：`self.to_payload`, `stable_json_hash`
  - 可解析内部调用：`qts.backtest.config.BacktestCostModel.to_payload`, `qts.backtest.config.BacktestEngineConfig.to_payload`, `qts.backtest.config.BacktestMarketDataReference.to_payload`, `qts.backtest.config.BacktestRunConfig.to_payload`, `qts.backtest.config.BacktestStrategyConfig.to_payload`, `qts.backtest.config.CostModelConfig.to_payload`, `qts.backtest.config.RiskConfig.to_payload`, `qts.backtest.config.RollPolicyConfig.to_payload`, `qts.backtest.report.StreamingEquityMetrics.to_payload`, `qts.core.hashing.stable_json_hash`, `qts.data.sessions.window.RegularSessionWindow.to_payload`
- `qts.backtest.config.BacktestRunConfig.to_payload`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/config.py:399`
  - 说明：Perform to_payload.
  - 直接调用：`list`, `self.cost_model.to_payload`, `self.end.isoformat`, `self.instrument_ids.items`, `self.market_data.to_payload`, `self.risk_config.to_payload`, `self.roll_policy.to_payload`, `self.start.isoformat`, `self.strategy.to_payload`, `sorted`, `str`
  - 可解析内部调用：`qts.backtest.config.BacktestCostModel.to_payload`, `qts.backtest.config.BacktestEngineConfig.to_payload`, `qts.backtest.config.BacktestMarketDataReference.to_payload`, `qts.backtest.config.BacktestRunConfig.to_payload`, `qts.backtest.config.BacktestStrategyConfig.to_payload`, `qts.backtest.config.CostModelConfig.to_payload`, `qts.backtest.config.RiskConfig.to_payload`, `qts.backtest.config.RollPolicyConfig.to_payload`, `qts.backtest.report.StreamingEquityMetrics.to_payload`, `qts.data.sessions.window.RegularSessionWindow.to_payload`
- `qts.backtest.config.BacktestRunConfig._normalize_symbol`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/backtest/config.py:431`
  - 说明：Perform _normalize_symbol.
  - 直接调用：`ValueError`, `symbol.strip`, `symbol.strip.upper`
  - 可解析内部调用：无

### `backend/src/qts/backtest/config_loader.py`

- `qts.backtest.config_loader.BacktestConfigLoader`
  - 类型：`class`
  - 位置：`backend/src/qts/backtest/config_loader.py:24`
  - 说明：Load backtest configuration from YAML or payload dictionaries.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.config_loader.BacktestConfigLoader.from_path`
  - 类型：`classmethod`
  - 位置：`backend/src/qts/backtest/config_loader.py:28`
  - 说明：Perform from_path.
  - 直接调用：`ValueError`, `cls.from_payload`, `isinstance`, `path.read_text`, `yaml.safe_load`
  - 可解析内部调用：`qts.backtest.config_loader.BacktestConfigLoader.from_payload`, `qts.config.ibkr.IbkrEnvironmentConfig.from_payload`, `qts.data.historical.config.HistoricalDataConfig.from_payload`, `qts.data.historical.config_loader.HistoricalDataConfigLoader.from_payload`
- `qts.backtest.config_loader.BacktestConfigLoader.from_payload`
  - 类型：`classmethod`
  - 位置：`backend/src/qts/backtest/config_loader.py:36`
  - 说明：Perform from_payload.
  - 直接调用：`BacktestRunConfig`, `BacktestStrategyConfig.from_yaml`, `CostModelConfig`, `Decimal`, `InstrumentId`, `Path`, `RiskConfig`, `RollPolicyConfig`, `ValueError`, `bool`, `cast`, `cls._parse_datetime`, `cls._parse_market_data_reference`, `cost_payload.get`, `dict`, `instrument_ids_payload.items`, `int`, `isinstance`, `payload.get`, `risk_payload.get`, `roll_payload.get`, `str`, `tuple`
  - 可解析内部调用：`qts.backtest.config.BacktestRunConfig`, `qts.backtest.config.BacktestStrategyConfig.from_yaml`, `qts.backtest.config.CostModelConfig`, `qts.backtest.config.RiskConfig`, `qts.backtest.config.RollPolicyConfig`, `qts.backtest.config_loader.BacktestConfigLoader._parse_datetime`, `qts.backtest.config_loader.BacktestConfigLoader._parse_market_data_reference`, `qts.core.ids.InstrumentId`, `qts.risk.config.RiskConfig`, `qts.runtime.mailbox.Mailbox.get`
- `qts.backtest.config_loader.BacktestConfigLoader._parse_datetime`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/backtest/config_loader.py:112`
  - 说明：Perform _parse_datetime.
  - 直接调用：`ValueError`, `datetime.fromisoformat`, `isinstance`, `parsed.astimezone`, `value.replace`
  - 可解析内部调用：无
- `qts.backtest.config_loader.BacktestConfigLoader._parse_market_data_reference`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/backtest/config_loader.py:123`
  - 说明：Perform _parse_market_data_reference.
  - 直接调用：`BacktestMarketDataReference`, `Path`, `ValueError`, `isinstance`, `payload.get`, `str`
  - 可解析内部调用：`qts.backtest.config.BacktestMarketDataReference`, `qts.runtime.mailbox.Mailbox.get`

### `backend/src/qts/backtest/dependencies.py`

- `qts.backtest.dependencies.BacktestEngineDependencies`
  - 类型：`class`
  - 位置：`backend/src/qts/backtest/dependencies.py:30`
  - 说明：Runtime dependencies for constructing and running ``BacktestEngine``.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.dependencies.BacktestEngineDependencies.with_defaults`
  - 类型：`classmethod`
  - 位置：`backend/src/qts/backtest/dependencies.py:43`
  - 说明：Build runtime dependencies with stable defaults.
  - 直接调用：`Decimal`, `MaxNotionalRule`, `RiskEngine`, `cls`, `dict`
  - 可解析内部调用：`qts.risk.risk_engine.RiskEngine`, `qts.risk.rules.max_notional.MaxNotionalRule`
- `qts.backtest.dependencies.BacktestActorLoopConfig`
  - 类型：`class`
  - 位置：`backend/src/qts/backtest/dependencies.py:71`
  - 说明：Execution-loop runtime configuration.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.dependencies.BacktestActorLoopConfig.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/dependencies.py:78`
  - 说明：Normalize and validate loop runtime settings.
  - 直接调用：`Decimal`, `ValueError`, `object.__setattr__`, `str`
  - 可解析内部调用：无
- `qts.backtest.dependencies.BacktestActorLoopDependencies`
  - 类型：`class`
  - 位置：`backend/src/qts/backtest/dependencies.py:88`
  - 说明：Runtime collaborators and policy objects used by ``BacktestActorLoop``.
  - 直接调用：无
  - 可解析内部调用：无

### `backend/src/qts/backtest/engine.py`

- `qts.backtest.engine.BacktestStreamResult`
  - 类型：`class`
  - 位置：`backend/src/qts/backtest/engine.py:54`
  - 说明：Backtest result written to partitioned streaming artifacts.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.engine.BacktestEngine`
  - 类型：`class`
  - 位置：`backend/src/qts/backtest/engine.py:73`
  - 说明：Single-process backtest engine using the Strategy SDK and actor order flow.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.engine.BacktestEngine.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/engine.py:76`
  - 说明：Create an engine from explicit config and dependency objects.
  - 直接调用：`BacktestEngineConfig`, `BacktestEngineConfig.from_legacy_kwargs`, `BacktestEngineDependencies.with_defaults`, `BacktestInstrumentContext`, `BacktestIntentProcessor`, `BacktestPortfolioProjector`, `Decimal`, `ValueError`, `_BacktestExecutionAdapter`, `dict`, `isinstance`, `iter`, `str`, `tuple`
  - 可解析内部调用：`qts.backtest.config.BacktestEngineConfig`, `qts.backtest.config.BacktestEngineConfig.from_legacy_kwargs`, `qts.backtest.dependencies.BacktestEngineDependencies.with_defaults`, `qts.backtest.instrument_context.BacktestInstrumentContext`, `qts.backtest.intent_processor.BacktestIntentProcessor`, `qts.backtest.portfolio_projection.BacktestPortfolioProjector`
- `qts.backtest.engine.BacktestEngine.from_config`
  - 类型：`classmethod`
  - 位置：`backend/src/qts/backtest/engine.py:176`
  - 说明：Build an engine from a serialized backtest run config.
  - 直接调用：`BacktestCostModel`, `BacktestEngineConfig`, `BacktestEngineDependencies.with_defaults`, `MaxNotionalRule`, `RiskEngine`, `cls`, `config.to_payload`, `tuple`
  - 可解析内部调用：`qts.backtest.config.BacktestCostModel`, `qts.backtest.config.BacktestCostModel.to_payload`, `qts.backtest.config.BacktestEngineConfig`, `qts.backtest.config.BacktestEngineConfig.to_payload`, `qts.backtest.config.BacktestMarketDataReference.to_payload`, `qts.backtest.config.BacktestRunConfig.to_payload`, `qts.backtest.config.BacktestStrategyConfig.to_payload`, `qts.backtest.config.CostModelConfig.to_payload`, `qts.backtest.config.RiskConfig.to_payload`, `qts.backtest.config.RollPolicyConfig.to_payload`, `qts.backtest.dependencies.BacktestEngineDependencies.with_defaults`, `qts.backtest.report.StreamingEquityMetrics.to_payload`, `qts.data.sessions.window.RegularSessionWindow.to_payload`, `qts.risk.risk_engine.RiskEngine`, `qts.risk.rules.max_notional.MaxNotionalRule`
- `qts.backtest.engine.BacktestEngine.run_streaming`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/engine.py:217`
  - 说明：Run the backtest and write streaming artifacts.
  - 直接调用：`BacktestActorLoop`, `BacktestActorLoopConfig`, `BacktestActorLoopDependencies`, `BacktestRunId`, `BacktestStreamResult`, `BacktestStreamingSink`, `EquityCurvePoint`, `StreamingBacktestArtifactWriter`, `actor_loop.run`, `dataset_metadata_payload`, `self._cost_model.to_payload`, `self._instrument_context.instrument_registry`, `sink.write_equity_point`, `stable_json_hash`, `tuple`, `writer.finalize`, `zero_time`
  - 可解析内部调用：`qts.api.services.command_idempotency.CommandIdempotencyStore.run`, `qts.backtest.actor_loop.BacktestActorLoop`, `qts.backtest.actor_loop.BacktestActorLoop.run`, `qts.backtest.config.BacktestCostModel.to_payload`, `qts.backtest.config.BacktestEngineConfig.to_payload`, `qts.backtest.config.BacktestMarketDataReference.to_payload`, `qts.backtest.config.BacktestRunConfig.to_payload`, `qts.backtest.config.BacktestStrategyConfig.to_payload`, `qts.backtest.config.CostModelConfig.to_payload`, `qts.backtest.config.RiskConfig.to_payload`, `qts.backtest.config.RollPolicyConfig.to_payload`, `qts.backtest.dependencies.BacktestActorLoopConfig`, `qts.backtest.dependencies.BacktestActorLoopDependencies`, `qts.backtest.engine.BacktestStreamResult`, `qts.backtest.instrument_context.BacktestInstrumentContext.instrument_registry`, `qts.backtest.report.EquityCurvePoint`, `qts.backtest.report.StreamingBacktestArtifactWriter`, `qts.backtest.report.StreamingBacktestArtifactWriter.finalize`, `qts.backtest.report.StreamingBacktestArtifactWriter.write_equity_point`, `qts.backtest.report.StreamingEquityMetrics.to_payload`, `qts.backtest.report.dataset_metadata_payload`, `qts.backtest.report.zero_time`, `qts.backtest.sinks.BacktestStreamingSink`, `qts.backtest.sinks.BacktestStreamingSink.write_equity_point`, `qts.core.hashing.stable_json_hash`, `qts.core.ids.BacktestRunId`, `qts.data.sessions.window.RegularSessionWindow.to_payload`, `qts.strategy_sdk.strategy.Strategy.finalize`

### `backend/src/qts/backtest/historical_data_portal.py`

- `qts.backtest.historical_data_portal.HistoricalDataPortal`
  - 类型：`class`
  - 位置：`backend/src/qts/backtest/historical_data_portal.py:13`
  - 说明：Returns finalized bars visible as of a replay timestamp.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.historical_data_portal.HistoricalDataPortal.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/historical_data_portal.py:16`
  - 说明：Perform __init__.
  - 直接调用：`bars.items`, `sorted`, `tuple`
  - 可解析内部调用：无
- `qts.backtest.historical_data_portal.HistoricalDataPortal.data_view`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/historical_data_portal.py:23`
  - 说明：Perform data_view.
  - 直接调用：`DataView`
  - 可解析内部调用：`qts.strategy_sdk.data_view.DataView`
- `qts.backtest.historical_data_portal.HistoricalDataPortal.history`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/historical_data_portal.py:27`
  - 说明：Perform history.
  - 直接调用：`self.data_view`, `self.data_view.history`
  - 可解析内部调用：`qts.backtest.historical_data_portal.HistoricalDataPortal.data_view`, `qts.backtest.historical_data_portal.HistoricalDataPortal.history`, `qts.strategy_sdk.data_view.DataView.history`

### `backend/src/qts/backtest/inputs.py`

- `qts.backtest.inputs.BacktestInputBundle`
  - 类型：`class`
  - 位置：`backend/src/qts/backtest/inputs.py:22`
  - 说明：Streaming inputs and side-channel metadata required by a backtest run.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.inputs.BacktestInputBuilder`
  - 类型：`class`
  - 位置：`backend/src/qts/backtest/inputs.py:34`
  - 说明：Build replay-ready market data, registry, and provenance inputs.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.inputs.BacktestInputBuilder.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/inputs.py:37`
  - 说明：Perform __init__.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.inputs.BacktestInputBuilder.build`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/inputs.py:42`
  - 说明：Perform build.
  - 直接调用：`BacktestInputBundle`, `self._contract_multipliers_for`, `self._dataset_metadata`, `self._instrument_registry_for`, `self._roll_registry`, `self._stream_configured_bars`
  - 可解析内部调用：`qts.backtest.inputs.BacktestInputBuilder._contract_multipliers_for`, `qts.backtest.inputs.BacktestInputBuilder._dataset_metadata`, `qts.backtest.inputs.BacktestInputBuilder._instrument_registry_for`, `qts.backtest.inputs.BacktestInputBuilder._roll_registry`, `qts.backtest.inputs.BacktestInputBuilder._stream_configured_bars`, `qts.backtest.inputs.BacktestInputBundle`
- `qts.backtest.inputs.BacktestInputBuilder._roll_registry`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/inputs.py:62`
  - 说明：Perform _roll_registry.
  - 直接调用：`FutureRollRegistry`, `len`
  - 可解析内部调用：`qts.registry.future_roll.FutureRollRegistry`
- `qts.backtest.inputs.BacktestInputBuilder._stream_configured_bars`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/inputs.py:68`
  - 说明：Perform _stream_configured_bars.
  - 直接调用：`HighestVolumeFutureContractSelector`, `RuntimeError`, `ValueError`, `dataset.chain.instrument_id_for_symbol`, `enumerate`, `exchange_timezones.setdefault`, `iter_historical_bars`, `roll_registry.register_root`, `self._exchange_timezone_for`, `self._iter_root_bars`, `self._merge_ordered_bar_streams`, `set`, `streams.append`, `tuple`
  - 可解析内部调用：`qts.backtest.inputs.BacktestInputBuilder._exchange_timezone_for`, `qts.backtest.inputs.BacktestInputBuilder._iter_root_bars`, `qts.backtest.inputs.BacktestInputBuilder._merge_ordered_bar_streams`, `qts.data.historical.chains.HistoricalChain.instrument_id_for_symbol`, `qts.data.historical.csv_dataset.iter_historical_bars`, `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver.instrument_id_for_symbol`, `qts.indicators.rolling.RollingWindow.append`, `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.instrument_id_for_symbol`, `qts.registry.future_roll.FutureRollRegistry.register_root`, `qts.registry.future_roll.HighestVolumeFutureContractSelector`, `qts.registry.symbol_resolution.SourceSymbolResolver.instrument_id_for_symbol`, `qts.registry.symbol_resolution.StaticSymbolResolver.instrument_id_for_symbol`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`
- `qts.backtest.inputs.BacktestInputBuilder._iter_root_bars`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/inputs.py:135`
  - 说明：Perform _iter_root_bars.
  - 直接调用：`RuntimeError`, `bar.instrument_id.value.rsplit`, `len`, `roll_registry.record_selection`, `self._record_exchange_timezone`, `stream.stats.as_dict`
  - 可解析内部调用：`qts.backtest.inputs.BacktestInputBuilder._record_exchange_timezone`, `qts.data.historical.validation.HistoricalCsvStats.as_dict`, `qts.registry.future_roll.FutureRollRegistry.record_selection`
- `qts.backtest.inputs.BacktestInputBuilder._merge_ordered_bar_streams`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/backtest/inputs.py:175`
  - 说明：Perform _merge_ordered_bar_streams.
  - 直接调用：`heapq.heappop`, `heapq.heappush`, `next`
  - 可解析内部调用：无
- `qts.backtest.inputs.BacktestInputBuilder._record_exchange_timezone`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/backtest/inputs.py:199`
  - 说明：Perform _record_exchange_timezone.
  - 直接调用：`exchange_timezones.setdefault`
  - 可解析内部调用：无
- `qts.backtest.inputs.BacktestInputBuilder._exchange_timezone_for`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/backtest/inputs.py:210`
  - 说明：Perform _exchange_timezone_for.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.inputs.BacktestInputBuilder._instrument_registry_for`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/inputs.py:218`
  - 说明：Perform _instrument_registry_for.
  - 直接调用：`Decimal`, `InstrumentRegistry`, `RuntimeError`, `chain.instrument_id_for_symbol`, `registry.register`, `roll_registry.continuous_instrument_id`, `self._config.instrument_ids.items`, `self._instrument_for`, `set`
  - 可解析内部调用：`qts.application.strategy_lifecycle.StrategyRegistry.register`, `qts.backtest.inputs.BacktestInputBuilder._instrument_for`, `qts.data.historical.chains.HistoricalChain.instrument_id_for_symbol`, `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver.instrument_id_for_symbol`, `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.instrument_id_for_symbol`, `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.register`, `qts.registry.calendar_registry.CalendarRegistry.register`, `qts.registry.future_chain_registry.FutureChainRegistry.register`, `qts.registry.future_roll.FutureRollRegistry.continuous_instrument_id`, `qts.registry.instrument_registry.InstrumentRegistry`, `qts.registry.instrument_registry.InstrumentRegistry.register`, `qts.registry.option_chain_registry.OptionChainRegistry.register`, `qts.registry.symbol_resolution.SourceSymbolResolver.instrument_id_for_symbol`, `qts.registry.symbol_resolution.StaticSymbolResolver.instrument_id_for_symbol`, `qts.runtime.router.EventRouter.register`, `qts.strategy_sdk.asset_resolver.ContinuousFutureResolver.continuous_instrument_id`
- `qts.backtest.inputs.BacktestInputBuilder._instrument_for`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/backtest/inputs.py:273`
  - 说明：Perform _instrument_for.
  - 直接调用：`ContractSpec`, `Decimal`, `Instrument`
  - 可解析内部调用：`qts.domain.instruments.contract_spec.ContractSpec`, `qts.domain.instruments.instrument.Instrument`
- `qts.backtest.inputs.BacktestInputBuilder._dataset_metadata`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/inputs.py:298`
  - 说明：Perform _dataset_metadata.
  - 直接调用：`DatasetMetadata`, `self._config.end.isoformat`, `self._config.start.isoformat`, `self._dataset_instrument_id`, `str`, `tuple`
  - 可解析内部调用：`qts.backtest.inputs.BacktestInputBuilder._dataset_instrument_id`, `qts.data.provenance.DatasetMetadata`
- `qts.backtest.inputs.BacktestInputBuilder._dataset_instrument_id`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/backtest/inputs.py:322`
  - 说明：Perform _dataset_instrument_id.
  - 直接调用：`InstrumentId`
  - 可解析内部调用：`qts.core.ids.InstrumentId`
- `qts.backtest.inputs.BacktestInputBuilder._contract_multipliers_for`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/inputs.py:328`
  - 说明：Perform _contract_multipliers_for.
  - 直接调用：`chain.instrument_id_for_symbol`
  - 可解析内部调用：`qts.data.historical.chains.HistoricalChain.instrument_id_for_symbol`, `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver.instrument_id_for_symbol`, `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.instrument_id_for_symbol`, `qts.registry.symbol_resolution.SourceSymbolResolver.instrument_id_for_symbol`, `qts.registry.symbol_resolution.StaticSymbolResolver.instrument_id_for_symbol`

### `backend/src/qts/backtest/instrument_context.py`

- `qts.backtest.instrument_context.BacktestInstrumentContext`
  - 类型：`class`
  - 位置：`backend/src/qts/backtest/instrument_context.py:16`
  - 说明：Resolve backtest instrument IDs, roll targets, and instrument metadata.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.instrument_context.BacktestInstrumentContext.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/instrument_context.py:19`
  - 说明：Perform __init__.
  - 直接调用：`dict`, `tuple`
  - 可解析内部调用：无
- `qts.backtest.instrument_context.BacktestInstrumentContext.instrument_registry`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/instrument_context.py:34`
  - 说明：Perform instrument_registry.
  - 直接调用：`ContractSpec`, `Decimal`, `Instrument`, `InstrumentRegistry`, `RuntimeError`, `registry.register`, `seen.add`, `self._contract_multipliers.get`, `self._exchange_for`, `self._symbol_for`, `set`
  - 可解析内部调用：`qts.application.services.strategy_service.StrategyLifecycleService.add`, `qts.application.strategy_lifecycle.StrategyRegistry.register`, `qts.backtest.instrument_context.BacktestInstrumentContext._exchange_for`, `qts.backtest.instrument_context.BacktestInstrumentContext._symbol_for`, `qts.domain.instruments.contract_spec.ContractSpec`, `qts.domain.instruments.instrument.Instrument`, `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.register`, `qts.registry.calendar_registry.CalendarRegistry.register`, `qts.registry.future_chain_registry.FutureChainRegistry.register`, `qts.registry.instrument_registry.InstrumentRegistry`, `qts.registry.instrument_registry.InstrumentRegistry.register`, `qts.registry.option_chain_registry.OptionChainRegistry.register`, `qts.runtime.mailbox.Mailbox.get`, `qts.runtime.router.EventRouter.register`
- `qts.backtest.instrument_context.BacktestInstrumentContext.order_instrument_for_intent`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/instrument_context.py:68`
  - 说明：Perform order_instrument_for_intent.
  - 直接调用：`RuntimeError`, `self._future_roll_registry.resolve_contract`, `self.is_continuous`
  - 可解析内部调用：`qts.backtest.instrument_context.BacktestInstrumentContext.is_continuous`, `qts.registry.future_chain_registry.FutureChainRegistry.resolve_contract`, `qts.registry.future_roll.FutureRollRegistry.is_continuous`, `qts.registry.future_roll.FutureRollRegistry.resolve_contract`, `qts.strategy_sdk.asset_resolver.FutureContractResolver.resolve_contract`
- `qts.backtest.instrument_context.BacktestInstrumentContext.market_price_for_intent`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/instrument_context.py:79`
  - 说明：Perform market_price_for_intent.
  - 直接调用：`RuntimeError`, `self._future_roll_registry.execution_price`, `self.is_continuous`
  - 可解析内部调用：`qts.backtest.instrument_context.BacktestInstrumentContext.is_continuous`, `qts.registry.future_roll.FutureRollRegistry.execution_price`, `qts.registry.future_roll.FutureRollRegistry.is_continuous`
- `qts.backtest.instrument_context.BacktestInstrumentContext.update_rolling_prices`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/instrument_context.py:97`
  - 说明：Perform update_rolling_prices.
  - 直接调用：`self._future_roll_registry.execution_price`, `self._future_roll_registry.resolve_contract`, `self.is_continuous`
  - 可解析内部调用：`qts.backtest.instrument_context.BacktestInstrumentContext.is_continuous`, `qts.registry.future_chain_registry.FutureChainRegistry.resolve_contract`, `qts.registry.future_roll.FutureRollRegistry.execution_price`, `qts.registry.future_roll.FutureRollRegistry.is_continuous`, `qts.registry.future_roll.FutureRollRegistry.resolve_contract`, `qts.strategy_sdk.asset_resolver.FutureContractResolver.resolve_contract`
- `qts.backtest.instrument_context.BacktestInstrumentContext.related_contracts_for`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/instrument_context.py:118`
  - 说明：Perform related_contracts_for.
  - 直接调用：`RuntimeError`, `frozenset`, `self._future_roll_registry.related_contracts`, `self._related_contracts_by_continuous.get`, `self.is_continuous`
  - 可解析内部调用：`qts.backtest.instrument_context.BacktestInstrumentContext.is_continuous`, `qts.registry.future_roll.FutureRollRegistry.is_continuous`, `qts.registry.future_roll.FutureRollRegistry.related_contracts`, `qts.runtime.mailbox.Mailbox.get`
- `qts.backtest.instrument_context.BacktestInstrumentContext.is_continuous`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/instrument_context.py:136`
  - 说明：Perform is_continuous.
  - 直接调用：`self._future_roll_registry.is_continuous`
  - 可解析内部调用：`qts.backtest.instrument_context.BacktestInstrumentContext.is_continuous`, `qts.registry.future_roll.FutureRollRegistry.is_continuous`
- `qts.backtest.instrument_context.BacktestInstrumentContext._symbol_for`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/backtest/instrument_context.py:143`
  - 说明：Perform _symbol_for.
  - 直接调用：`instrument_id.value.rsplit`
  - 可解析内部调用：无
- `qts.backtest.instrument_context.BacktestInstrumentContext._exchange_for`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/backtest/instrument_context.py:148`
  - 说明：Perform _exchange_for.
  - 直接调用：`instrument_id.value.split`, `len`
  - 可解析内部调用：无

### `backend/src/qts/backtest/intent_processor.py`

- `qts.backtest.intent_processor.BacktestProcessedIntent`
  - 类型：`class`
  - 位置：`backend/src/qts/backtest/intent_processor.py:25`
  - 说明：Orders and fills generated for a single strategy intent.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.intent_processor.BacktestIntentProcessor`
  - 类型：`class`
  - 位置：`backend/src/qts/backtest/intent_processor.py:32`
  - 说明：Translate strategy target intents into validated, executed backtest orders.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.intent_processor.BacktestIntentProcessor.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/intent_processor.py:35`
  - 说明：Perform __init__.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.intent_processor.BacktestIntentProcessor.process_intent`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/intent_processor.py:47`
  - 说明：Process a single target intent and return produced orders/fills.
  - 直接调用：`BacktestProcessedIntent`, `Decimal`, `Position`, `account_actor.snapshot`, `enumerate`, `fills.extend`, `order_requests.append`, `orders.extend`, `self._desired_quantity`, `self._instrument_context.is_continuous`, `self._instrument_context.market_price_for_intent`, `self._instrument_context.order_instrument_for_intent`, `self._instrument_context.related_contracts_for`, `self._process_order_delta`, `snapshot.positions.get`, `snapshot.positions.items`, `tuple`
  - 可解析内部调用：`qts.application.services.interfaces.AccountService.snapshot`, `qts.backtest.instrument_context.BacktestInstrumentContext.is_continuous`, `qts.backtest.instrument_context.BacktestInstrumentContext.market_price_for_intent`, `qts.backtest.instrument_context.BacktestInstrumentContext.order_instrument_for_intent`, `qts.backtest.instrument_context.BacktestInstrumentContext.related_contracts_for`, `qts.backtest.intent_processor.BacktestIntentProcessor._desired_quantity`, `qts.backtest.intent_processor.BacktestIntentProcessor._process_order_delta`, `qts.backtest.intent_processor.BacktestProcessedIntent`, `qts.execution.idempotency.FillIdempotencyStore.snapshot`, `qts.execution.order_manager.OrderManager.snapshot`, `qts.indicators.rolling.RollingWindow.append`, `qts.indicators.rolling.RollingWindow.snapshot`, `qts.observability.metrics.MetricsRegistry.snapshot`, `qts.portfolio.position_book.Position`, `qts.portfolio.position_book.PositionBook.snapshot`, `qts.registry.future_roll.FutureRollRegistry.is_continuous`, `qts.runtime.actors.account_actor.AccountActor.snapshot`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`, `qts.runtime.mailbox.Mailbox.get`
- `qts.backtest.intent_processor.BacktestIntentProcessor._process_order_delta`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/intent_processor.py:136`
  - 说明：Perform _process_order_delta.
  - 直接调用：`BacktestProcessedIntent`, `Decimal`, `OrderId`, `OrderIntent`, `OrderRiskRequest`, `SubmitOrder`, `abs`, `account_ref.process_all`, `execution_ref.process_all`, `order_manager_actor.fills_since`, `order_manager_actor.get_order`, `order_manager_ref.process_all`, `order_manager_ref.tell`, `self._multiplier_for`, `self._risk_engine.check`
  - 可解析内部调用：`qts.backtest.intent_processor.BacktestProcessedIntent`, `qts.core.ids.OrderId`, `qts.domain.orders.value_objects.OrderIntent`, `qts.domain.risk.request.OrderRiskRequest`, `qts.execution.order_manager.OrderManager.get_order`, `qts.quality.guardrails.BacktestEngineCohesionRule.check`, `qts.quality.guardrails.BacktestInputCohesionRule.check`, `qts.quality.guardrails.BacktestRunnerCohesionRule.check`, `qts.quality.guardrails.BrokerSpecificRule.check`, `qts.quality.guardrails.GuardrailSuite.check`, `qts.quality.guardrails.ImportBoundaryRule.check`, `qts.quality.guardrails.OOPHelperOwnershipRule.check`, `qts.quality.guardrails.OOPPublicFactoryRule.check`, `qts.quality.guardrails.ProductSpecificRule.check`, `qts.quality.guardrails.Rule.check`, `qts.quality.guardrails.SharedCapabilityRule.check`, `qts.quality.guardrails.StrategySdkPublicSurfaceRule.check`, `qts.quality.guardrails.TestSupportRule.check`, `qts.risk.risk_engine.RiskEngine.check`, `qts.risk.rule.RiskRule.check`, `qts.risk.rules.max_notional.MaxNotionalRule.check`, `qts.risk.rules.max_order_qty.MaxOrderQuantityRule.check`, `qts.risk.rules.trading_session_rule.TradingSessionRule.check`, `qts.runtime.actor_ref.ActorRef.process_all`, `qts.runtime.actor_ref.ActorRef.tell`, `qts.runtime.actors.order_manager_actor.OrderManagerActor.fills_since`, `qts.runtime.actors.order_manager_actor.OrderManagerActor.get_order`, `qts.runtime.actors.order_manager_actor.SubmitOrder`
- `qts.backtest.intent_processor.BacktestIntentProcessor._desired_quantity`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/backtest/intent_processor.py:201`
  - 说明：Perform _desired_quantity.
  - 直接调用：`Decimal`, `ValueError`, `max`
  - 可解析内部调用：无

### `backend/src/qts/backtest/portfolio_projection.py`

- `qts.backtest.portfolio_projection.BacktestPortfolioProjector`
  - 类型：`class`
  - 位置：`backend/src/qts/backtest/portfolio_projection.py:15`
  - 说明：Compute portfolio state views and equity points for streaming backtests.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.portfolio_projection.BacktestPortfolioProjector.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/portfolio_projection.py:18`
  - 说明：Perform __init__.
  - 直接调用：`dict`
  - 可解析内部调用：无
- `qts.backtest.portfolio_projection.BacktestPortfolioProjector.multiplier_for`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/portfolio_projection.py:22`
  - 说明：Return multiplier used for portfolio valuation and risk checks.
  - 直接调用：`Decimal`, `self._multipliers.get`
  - 可解析内部调用：`qts.runtime.mailbox.Mailbox.get`
- `qts.backtest.portfolio_projection.BacktestPortfolioProjector.portfolio_view`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/portfolio_projection.py:27`
  - 说明：Perform portfolio_view.
  - 直接调用：`Decimal`, `PortfolioPosition`, `PortfolioView`, `latest_prices.get`, `positions.values`, `self.multiplier_for`, `snapshot.positions.items`, `sum`
  - 可解析内部调用：`qts.backtest.portfolio_projection.BacktestPortfolioProjector.multiplier_for`, `qts.runtime.mailbox.Mailbox.get`, `qts.strategy_sdk.portfolio_view.PortfolioPosition`, `qts.strategy_sdk.portfolio_view.PortfolioView`
- `qts.backtest.portfolio_projection.BacktestPortfolioProjector.equity_point`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/portfolio_projection.py:51`
  - 说明：Perform equity_point.
  - 直接调用：`EquityCurvePoint`, `self.portfolio_view`
  - 可解析内部调用：`qts.backtest.portfolio_projection.BacktestPortfolioProjector.portfolio_view`, `qts.backtest.report.EquityCurvePoint`

### `backend/src/qts/backtest/report.py`

- `qts.backtest.report.dataset_metadata_payload`
  - 类型：`module_function`
  - 位置：`backend/src/qts/backtest/report.py:17`
  - 说明：Serialize one dataset provenance row for reporting.
  - 直接调用：`item.created_at.isoformat`
  - 可解析内部调用：无
- `qts.backtest.report.zero_time`
  - 类型：`module_function`
  - 位置：`backend/src/qts/backtest/report.py:32`
  - 说明：Return the epoch boundary used for empty-equity bootstrap.
  - 直接调用：`datetime`
  - 可解析内部调用：无
- `qts.backtest.report.EquityCurvePoint`
  - 类型：`class`
  - 位置：`backend/src/qts/backtest/report.py:40`
  - 说明：One timestamped equity observation.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.report.TradeLedgerEntry`
  - 类型：`class`
  - 位置：`backend/src/qts/backtest/report.py:48`
  - 说明：Auditable row for a simulated fill.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.report._stable_hash`
  - 类型：`module_function`
  - 位置：`backend/src/qts/backtest/report.py:62`
  - 说明：Perform _stable_hash.
  - 直接调用：`stable_json_hash`
  - 可解析内部调用：`qts.core.hashing.stable_json_hash`
- `qts.backtest.report.StreamingEquityMetrics`
  - 类型：`class`
  - 位置：`backend/src/qts/backtest/report.py:67`
  - 说明：Incremental metrics for a streamed equity curve.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.report.StreamingEquityMetrics.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/report.py:70`
  - 说明：Perform __init__.
  - 直接调用：`Decimal`
  - 可解析内部调用：无
- `qts.backtest.report.StreamingEquityMetrics.update`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/report.py:78`
  - 说明：Perform update.
  - 直接调用：`Decimal`, `ValueError`
  - 可解析内部调用：无
- `qts.backtest.report.StreamingEquityMetrics.to_payload`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/report.py:95`
  - 说明：Perform to_payload.
  - 直接调用：`ValueError`
  - 可解析内部调用：无
- `qts.backtest.report.StreamingBacktestArtifacts`
  - 类型：`class`
  - 位置：`backend/src/qts/backtest/report.py:107`
  - 说明：Final paths and row counts for streamed backtest artifacts.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.report._NdjsonArtifact`
  - 类型：`class`
  - 位置：`backend/src/qts/backtest/report.py:116`
  - 说明：_NdjsonArtifact.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.report._NdjsonArtifact.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/report.py:119`
  - 说明：Perform __init__.
  - 直接调用：`hashlib.sha256`, `path.open`
  - 可解析内部调用：无
- `qts.backtest.report._NdjsonArtifact.write`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/report.py:126`
  - 说明：Perform write.
  - 直接调用：`json.dumps`, `line.encode`, `self._handle.write`, `self._hasher.update`
  - 可解析内部调用：`qts.backtest.report.StreamingEquityMetrics.update`, `qts.backtest.report._NdjsonArtifact.write`, `qts.data.bars.aggregator.BarAggregator.update`, `qts.indicators.price.ema.EMA.update`, `qts.indicators.price.sma.SMA.update`, `qts.strategy_sdk.indicators.AssetIndicator.update`
- `qts.backtest.report._NdjsonArtifact.close`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/report.py:141`
  - 说明：Perform close.
  - 直接调用：`self._handle.close`
  - 可解析内部调用：`qts.backtest.report._NdjsonArtifact.close`, `qts.strategy_sdk.context.StrategyContext.close`, `qts.strategy_sdk.data_view.DataView.close`
- `qts.backtest.report._NdjsonArtifact.content_hash`
  - 类型：`property`
  - 位置：`backend/src/qts/backtest/report.py:146`
  - 说明：Perform content_hash.
  - 直接调用：`self._hasher.hexdigest`
  - 可解析内部调用：无
- `qts.backtest.report.StreamingBacktestArtifactWriter`
  - 类型：`class`
  - 位置：`backend/src/qts/backtest/report.py:151`
  - 说明：Write large backtest outputs as line-delimited artifacts.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.report.StreamingBacktestArtifactWriter.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/report.py:156`
  - 说明：Perform __init__.
  - 直接调用：`StreamingEquityMetrics`, `_NdjsonArtifact`, `self._output_dir.mkdir`
  - 可解析内部调用：`qts.backtest.report.StreamingEquityMetrics`, `qts.backtest.report._NdjsonArtifact`
- `qts.backtest.report.StreamingBacktestArtifactWriter.write_order`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/report.py:166`
  - 说明：Perform write_order.
  - 直接调用：`write`
  - 可解析内部调用：`qts.backtest.report._NdjsonArtifact.write`
- `qts.backtest.report.StreamingBacktestArtifactWriter.write_fill`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/report.py:170`
  - 说明：Perform write_fill.
  - 直接调用：`write`
  - 可解析内部调用：`qts.backtest.report._NdjsonArtifact.write`
- `qts.backtest.report.StreamingBacktestArtifactWriter.write_trade_ledger`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/report.py:174`
  - 说明：Perform write_trade_ledger.
  - 直接调用：`write`
  - 可解析内部调用：`qts.backtest.report._NdjsonArtifact.write`
- `qts.backtest.report.StreamingBacktestArtifactWriter.write_equity_point`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/report.py:190`
  - 说明：Perform write_equity_point.
  - 直接调用：`self._equity_metrics.update`, `write`
  - 可解析内部调用：`qts.backtest.report.StreamingEquityMetrics.update`, `qts.backtest.report._NdjsonArtifact.write`, `qts.data.bars.aggregator.BarAggregator.update`, `qts.indicators.price.ema.EMA.update`, `qts.indicators.price.sma.SMA.update`, `qts.strategy_sdk.indicators.AssetIndicator.update`
- `qts.backtest.report.StreamingBacktestArtifactWriter.finalize`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/report.py:195`
  - 说明：Perform finalize.
  - 直接调用：`StreamingBacktestArtifacts`, `_stable_hash`, `artifact.close`, `artifact.path.replace`, `json.dumps`, `manifest_path.write_text`, `report_hash.removeprefix`, `self._artifacts.items`, `self._artifacts.values`, `self._equity_metrics.to_payload`, `str`
  - 可解析内部调用：`qts.backtest.config.BacktestCostModel.to_payload`, `qts.backtest.config.BacktestEngineConfig.to_payload`, `qts.backtest.config.BacktestMarketDataReference.to_payload`, `qts.backtest.config.BacktestRunConfig.to_payload`, `qts.backtest.config.BacktestStrategyConfig.to_payload`, `qts.backtest.config.CostModelConfig.to_payload`, `qts.backtest.config.RiskConfig.to_payload`, `qts.backtest.config.RollPolicyConfig.to_payload`, `qts.backtest.report.StreamingBacktestArtifacts`, `qts.backtest.report.StreamingEquityMetrics.to_payload`, `qts.backtest.report._NdjsonArtifact.close`, `qts.backtest.report._stable_hash`, `qts.data.sessions.window.RegularSessionWindow.to_payload`, `qts.strategy_sdk.context.StrategyContext.close`, `qts.strategy_sdk.data_view.DataView.close`

### `backend/src/qts/backtest/runner.py`

- `qts.backtest.runner.BacktestRun`
  - 类型：`class`
  - 位置：`backend/src/qts/backtest/runner.py:24`
  - 说明：Output of a backtest runner invocation.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.runner.BacktestRun.processed_bars`
  - 类型：`property`
  - 位置：`backend/src/qts/backtest/runner.py:34`
  - 说明：Perform processed_bars.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.runner.BacktestRun.report_hash`
  - 类型：`property`
  - 位置：`backend/src/qts/backtest/runner.py:39`
  - 说明：Perform report_hash.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.runner.run_backtest`
  - 类型：`module_function`
  - 位置：`backend/src/qts/backtest/runner.py:44`
  - 说明：Run a backtest and write partitioned streaming artifacts.
  - 直接调用：`BacktestEngine.from_config`, `BacktestEngine.from_config.run_streaming`, `BacktestInputBuilder`, `BacktestInputBuilder.build`, `BacktestRun`, `BacktestRunConfig.from_yaml`, `HistoricalCatalog.load`, `Path`, `_catalog_load_config`, `_load_strategy`, `_streaming_summary_payload`, `json.dumps`, `result.artifact_paths.items`, `summary_path.write_text`
  - 可解析内部调用：`qts.backtest.config.BacktestRunConfig.from_yaml`, `qts.backtest.engine.BacktestEngine.from_config`, `qts.backtest.engine.BacktestEngine.run_streaming`, `qts.backtest.inputs.BacktestInputBuilder`, `qts.backtest.inputs.BacktestInputBuilder.build`, `qts.backtest.runner.BacktestRun`, `qts.backtest.runner._catalog_load_config`, `qts.backtest.runner._load_strategy`, `qts.backtest.runner._streaming_summary_payload`, `qts.data.historical.catalog.HistoricalCatalog.load`
- `qts.backtest.runner._catalog_load_config`
  - 类型：`module_function`
  - 位置：`backend/src/qts/backtest/runner.py:87`
  - 说明：Perform _catalog_load_config.
  - 直接调用：`HistoricalCatalogLoadConfig.from_historical_data_config`, `HistoricalCatalogLoadConfig.from_legacy_root`, `RuntimeError`
  - 可解析内部调用：`qts.data.historical.catalog.HistoricalCatalogLoadConfig.from_historical_data_config`, `qts.data.historical.catalog.HistoricalCatalogLoadConfig.from_legacy_root`
- `qts.backtest.runner._load_strategy`
  - 类型：`module_function`
  - 位置：`backend/src/qts/backtest/runner.py:109`
  - 说明：Perform _load_strategy.
  - 直接调用：`ValueError`, `_import_strategy_module`, `_strategy_type_from_module`, `strategy_class.partition`, `strategy_class.rpartition`, `strategy_type`
  - 可解析内部调用：`qts.backtest.runner._import_strategy_module`, `qts.backtest.runner._strategy_type_from_module`
- `qts.backtest.runner._import_strategy_module`
  - 类型：`module_function`
  - 位置：`backend/src/qts/backtest/runner.py:121`
  - 说明：Load a module that defines the requested strategy class.
  - 直接调用：`Path`, `Path.with_suffix`, `importlib.import_module`, `importlib.util.module_from_spec`, `importlib.util.spec_from_file_location`, `module_name.split`, `module_path.exists`, `spec.loader.exec_module`
  - 可解析内部调用：无
- `qts.backtest.runner._strategy_type_from_module`
  - 类型：`module_function`
  - 位置：`backend/src/qts/backtest/runner.py:137`
  - 说明：Extract the strategy class from a strategy module.
  - 直接调用：`TypeError`, `ValueError`, `isinstance`, `issubclass`, `vars`, `vars.get`
  - 可解析内部调用：`qts.runtime.mailbox.Mailbox.get`
- `qts.backtest.runner._streaming_summary_payload`
  - 类型：`module_function`
  - 位置：`backend/src/qts/backtest/runner.py:151`
  - 说明：Perform _streaming_summary_payload.
  - 直接调用：`dataset_stats.values`, `item.get`, `str`, `sum`
  - 可解析内部调用：`qts.runtime.mailbox.Mailbox.get`

### `backend/src/qts/backtest/sinks.py`

- `qts.backtest.sinks.BacktestStreamingSink`
  - 类型：`class`
  - 位置：`backend/src/qts/backtest/sinks.py:13`
  - 说明：Write engine stream artifacts through a shared writer.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.sinks.BacktestStreamingSink.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/sinks.py:16`
  - 说明：Perform __init__.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.sinks.BacktestStreamingSink.order_count`
  - 类型：`property`
  - 位置：`backend/src/qts/backtest/sinks.py:22`
  - 说明：Perform order_count.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.backtest.sinks.BacktestStreamingSink.write_processed`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/sinks.py:26`
  - 说明：Perform write_processed.
  - 直接调用：`len`, `self._fill_payload`, `self._ledger_rows`, `self._order_payload`, `self._writer.write_fill`, `self._writer.write_order`, `self._writer.write_trade_ledger`
  - 可解析内部调用：`qts.backtest.report.StreamingBacktestArtifactWriter.write_fill`, `qts.backtest.report.StreamingBacktestArtifactWriter.write_order`, `qts.backtest.report.StreamingBacktestArtifactWriter.write_trade_ledger`, `qts.backtest.sinks.BacktestStreamingSink._fill_payload`, `qts.backtest.sinks.BacktestStreamingSink._ledger_rows`, `qts.backtest.sinks.BacktestStreamingSink._order_payload`
- `qts.backtest.sinks.BacktestStreamingSink.write_equity_point`
  - 类型：`method`
  - 位置：`backend/src/qts/backtest/sinks.py:42`
  - 说明：Perform write_equity_point.
  - 直接调用：`self._writer.write_equity_point`
  - 可解析内部调用：`qts.backtest.report.StreamingBacktestArtifactWriter.write_equity_point`, `qts.backtest.sinks.BacktestStreamingSink.write_equity_point`
- `qts.backtest.sinks.BacktestStreamingSink._ledger_rows`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/backtest/sinks.py:47`
  - 说明：Perform _ledger_rows.
  - 直接调用：`TradeLedgerEntry`, `tuple`
  - 可解析内部调用：`qts.backtest.report.TradeLedgerEntry`
- `qts.backtest.sinks.BacktestStreamingSink._order_payload`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/backtest/sinks.py:65`
  - 说明：Perform _order_payload.
  - 直接调用：`str`
  - 可解析内部调用：无
- `qts.backtest.sinks.BacktestStreamingSink._fill_payload`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/backtest/sinks.py:77`
  - 说明：Perform _fill_payload.
  - 直接调用：`str`
  - 可解析内部调用：无

### `backend/src/qts/config/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/config/ibkr.py`

- `qts.config.ibkr.IbkrConnectionConfig`
  - 类型：`class`
  - 位置：`backend/src/qts/config/ibkr.py:16`
  - 说明：IBKR connection settings for one boundary.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.config.ibkr.IbkrConnectionConfig.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/config/ibkr.py:24`
  - 说明：Perform __post_init__.
  - 直接调用：`ValueError`, `self.host.strip`, `self.source_id.strip`
  - 可解析内部调用：无
- `qts.config.ibkr.IbkrOrderExecutionConfig`
  - 类型：`class`
  - 位置：`backend/src/qts/config/ibkr.py:37`
  - 说明：IBKR order execution settings.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.config.ibkr.IbkrOrderExecutionConfig.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/config/ibkr.py:48`
  - 说明：Perform __post_init__.
  - 直接调用：`ValueError`, `self.account_id.strip`, `self.host.strip`, `self.risk_profile.strip`, `self.source_id.strip`
  - 可解析内部调用：无
- `qts.config.ibkr.IbkrSecretRefs`
  - 类型：`class`
  - 位置：`backend/src/qts/config/ibkr.py:65`
  - 说明：Environment variable names for IBKR credentials.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.config.ibkr.IbkrSecretRefs.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/config/ibkr.py:71`
  - 说明：Perform __post_init__.
  - 直接调用：`ValueError`, `self.password_env.strip`, `self.username_env.strip`
  - 可解析内部调用：无
- `qts.config.ibkr.IbkrEnvironmentConfig`
  - 类型：`class`
  - 位置：`backend/src/qts/config/ibkr.py:80`
  - 说明：IBKR runtime configuration split by external boundary.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.config.ibkr.IbkrEnvironmentConfig.from_payload`
  - 类型：`classmethod`
  - 位置：`backend/src/qts/config/ibkr.py:89`
  - 说明：Build a typed config from a mapping payload.
  - 直接调用：`ValueError`, `_as_mapping`, `_read_connection`, `_read_order_execution_config`, `_read_secret_refs`, `cls`, `payload.get`, `payload.get.strip`, `str`, `str.strip`
  - 可解析内部调用：`qts.config.ibkr._as_mapping`, `qts.config.ibkr._read_connection`, `qts.config.ibkr._read_order_execution_config`, `qts.config.ibkr._read_secret_refs`, `qts.runtime.mailbox.Mailbox.get`
- `qts.config.ibkr.IbkrEnvironmentConfig.from_yaml`
  - 类型：`classmethod`
  - 位置：`backend/src/qts/config/ibkr.py:119`
  - 说明：Load and validate environment config from YAML file.
  - 直接调用：`ValueError`, `cls.from_payload`, `isinstance`, `path.read_text`, `yaml.safe_load`
  - 可解析内部调用：`qts.backtest.config_loader.BacktestConfigLoader.from_payload`, `qts.config.ibkr.IbkrEnvironmentConfig.from_payload`, `qts.data.historical.config.HistoricalDataConfig.from_payload`, `qts.data.historical.config_loader.HistoricalDataConfigLoader.from_payload`
- `qts.config.ibkr.collect_validation_errors`
  - 类型：`module_function`
  - 位置：`backend/src/qts/config/ibkr.py:128`
  - 说明：Return validation errors for config without raising.
  - 直接调用：`str`, `str.split`, `validate_ibkr_environment`
  - 可解析内部调用：`qts.config.ibkr.validate_ibkr_environment`
- `qts.config.ibkr.validate_ibkr_environment`
  - 类型：`module_function`
  - 位置：`backend/src/qts/config/ibkr.py:140`
  - 说明：Validate paper/live separation without exposing secret values.
  - 直接调用：`ValueError`, `_contains_paper_reference`, `config.order_execution.account_id.upper`, `config.order_execution.account_id.upper.startswith`, `config.order_execution.risk_profile.lower`, `errors.append`, `join`, `live_client_ids.intersection`, `set`
  - 可解析内部调用：`qts.config.ibkr._contains_paper_reference`, `qts.indicators.rolling.RollingWindow.append`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`
- `qts.config.ibkr._as_mapping`
  - 类型：`module_function`
  - 位置：`backend/src/qts/config/ibkr.py:172`
  - 说明：Perform _as_mapping.
  - 直接调用：`ValueError`, `isinstance`, `path.split`
  - 可解析内部调用：无
- `qts.config.ibkr._read_connection`
  - 类型：`module_function`
  - 位置：`backend/src/qts/config/ibkr.py:186`
  - 说明：Perform _read_connection.
  - 直接调用：`IbkrConnectionConfig`, `ValueError`, `isinstance`, `payload.get`, `str`
  - 可解析内部调用：`qts.config.ibkr.IbkrConnectionConfig`, `qts.runtime.mailbox.Mailbox.get`
- `qts.config.ibkr._read_order_execution_config`
  - 类型：`module_function`
  - 位置：`backend/src/qts/config/ibkr.py:206`
  - 说明：Perform _read_order_execution_config.
  - 直接调用：`IbkrOrderExecutionConfig`, `_read_connection`, `payload.get`, `str`
  - 可解析内部调用：`qts.config.ibkr.IbkrOrderExecutionConfig`, `qts.config.ibkr._read_connection`, `qts.runtime.mailbox.Mailbox.get`
- `qts.config.ibkr._read_secret_refs`
  - 类型：`module_function`
  - 位置：`backend/src/qts/config/ibkr.py:227`
  - 说明：Perform _read_secret_refs.
  - 直接调用：`IbkrSecretRefs`, `payload.get`, `str`
  - 可解析内部调用：`qts.config.ibkr.IbkrSecretRefs`, `qts.runtime.mailbox.Mailbox.get`
- `qts.config.ibkr._contains_paper_reference`
  - 类型：`module_function`
  - 位置：`backend/src/qts/config/ibkr.py:235`
  - 说明：Perform _contains_paper_reference.
  - 直接调用：`secret_env_name.upper`
  - 可解析内部调用：无

### `backend/src/qts/core/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/core/hashing.py`

- `qts.core.hashing.stable_json_default`
  - 类型：`module_function`
  - 位置：`backend/src/qts/core/hashing.py:12`
  - 说明：Adapter used by :func:`stable_json_dumps` for non-native JSON types.
  - 直接调用：`TypeError`, `hasattr`, `isinstance`, `str`, `type`, `value.isoformat`
  - 可解析内部调用：无
- `qts.core.hashing.stable_json_dumps`
  - 类型：`module_function`
  - 位置：`backend/src/qts/core/hashing.py:24`
  - 说明：Serialize `payload` deterministically for stable hashing.
  - 直接调用：`json.dumps`
  - 可解析内部调用：无
- `qts.core.hashing.stable_json_hash`
  - 类型：`module_function`
  - 位置：`backend/src/qts/core/hashing.py:35`
  - 说明：Return a stable SHA-256 digest for a payload.
  - 直接调用：`hashlib.sha256`, `hashlib.sha256.hexdigest`, `stable_json_dumps`, `stable_json_dumps.encode`
  - 可解析内部调用：`qts.core.hashing.stable_json_dumps`

### `backend/src/qts/core/ids.py`

- `qts.core.ids._StringId`
  - 类型：`class`
  - 位置：`backend/src/qts/core/ids.py:9`
  - 说明：Base class for typed string identifiers.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.core.ids._StringId.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/core/ids.py:14`
  - 说明：Perform __post_init__.
  - 直接调用：`TypeError`, `ValueError`, `isinstance`, `self.value.strip`
  - 可解析内部调用：无
- `qts.core.ids._StringId.__str__`
  - 类型：`method`
  - 位置：`backend/src/qts/core/ids.py:22`
  - 说明：Perform __str__.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.core.ids.AccountId`
  - 类型：`class`
  - 位置：`backend/src/qts/core/ids.py:27`
  - 说明：Stable internal account identifier.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.core.ids.StrategyId`
  - 类型：`class`
  - 位置：`backend/src/qts/core/ids.py:31`
  - 说明：Stable internal strategy identifier.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.core.ids.InstrumentId`
  - 类型：`class`
  - 位置：`backend/src/qts/core/ids.py:35`
  - 说明：Stable internal instrument identifier.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.core.ids.OrderId`
  - 类型：`class`
  - 位置：`backend/src/qts/core/ids.py:39`
  - 说明：Stable internal order identifier.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.core.ids.BrokerId`
  - 类型：`class`
  - 位置：`backend/src/qts/core/ids.py:43`
  - 说明：Stable internal broker identifier.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.core.ids.EventId`
  - 类型：`class`
  - 位置：`backend/src/qts/core/ids.py:47`
  - 说明：Stable internal event identifier.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.core.ids.BacktestRunId`
  - 类型：`class`
  - 位置：`backend/src/qts/core/ids.py:51`
  - 说明：Stable identifier for a backtest run.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.core.ids.CorrelationId`
  - 类型：`class`
  - 位置：`backend/src/qts/core/ids.py:55`
  - 说明：Identifier grouping events in one business workflow.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.core.ids.CausationId`
  - 类型：`class`
  - 位置：`backend/src/qts/core/ids.py:59`
  - 说明：Identifier linking an event to the event that caused it.
  - 直接调用：无
  - 可解析内部调用：无

### `backend/src/qts/core/time.py`

- `qts.core.time.require_aware_datetime`
  - 类型：`module_function`
  - 位置：`backend/src/qts/core/time.py:10`
  - 说明：Validate that a datetime has an effective timezone.
  - 直接调用：`ValueError`, `value.utcoffset`
  - 可解析内部调用：无
- `qts.core.time.to_exchange_time`
  - 类型：`module_function`
  - 位置：`backend/src/qts/core/time.py:17`
  - 说明：Convert a timestamp representation into an exchange timezone.
  - 直接调用：`ZoneInfo`, `isinstance`, `require_aware_datetime`, `value.astimezone`
  - 可解析内部调用：`qts.core.time.require_aware_datetime`
- `qts.core.time.TimeInterval`
  - 类型：`class`
  - 位置：`backend/src/qts/core/time.py:28`
  - 说明：A half-open time interval with `[start, end)` membership.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.core.time.TimeInterval.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/core/time.py:34`
  - 说明：Perform __post_init__.
  - 直接调用：`ValueError`, `require_aware_datetime`
  - 可解析内部调用：`qts.core.time.require_aware_datetime`
- `qts.core.time.TimeInterval.duration`
  - 类型：`property`
  - 位置：`backend/src/qts/core/time.py:42`
  - 说明：Perform duration.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.core.time.TimeInterval.contains`
  - 类型：`method`
  - 位置：`backend/src/qts/core/time.py:46`
  - 说明：Perform contains.
  - 直接调用：`require_aware_datetime`
  - 可解析内部调用：`qts.core.time.require_aware_datetime`

### `backend/src/qts/data/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/data/adapters/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/data/adapters/ibkr_market_data.py`

- `qts.data.adapters.ibkr_market_data.IbkrMarketDataConnection`
  - 类型：`class`
  - 位置：`backend/src/qts/data/adapters/ibkr_market_data.py:15`
  - 说明：IBKR market data connection settings.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.adapters.ibkr_market_data.IbkrMarketDataConnection.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/data/adapters/ibkr_market_data.py:23`
  - 说明：Perform __post_init__.
  - 直接调用：`ValueError`, `self.host.strip`, `self.source_id.strip`
  - 可解析内部调用：无
- `qts.data.adapters.ibkr_market_data.IbkrMarketDataSubscription`
  - 类型：`class`
  - 位置：`backend/src/qts/data/adapters/ibkr_market_data.py:36`
  - 说明：IBKR market data subscription request at the adapter boundary.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter`
  - 类型：`class`
  - 位置：`backend/src/qts/data/adapters/ibkr_market_data.py:44`
  - 说明：Normalizes IBKR market data without owning order execution.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/data/adapters/ibkr_market_data.py:47`
  - 说明：Perform __init__.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter.subscription_for`
  - 类型：`method`
  - 位置：`backend/src/qts/data/adapters/ibkr_market_data.py:57`
  - 说明：Perform subscription_for.
  - 直接调用：`IbkrMarketDataSubscription`, `self._symbol_mapping.to_broker_symbol`
  - 可解析内部调用：`qts.data.adapters.ibkr_market_data.IbkrMarketDataSubscription`, `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.to_broker_symbol`
- `qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter.normalize_tick`
  - 类型：`method`
  - 位置：`backend/src/qts/data/adapters/ibkr_market_data.py:65`
  - 说明：Perform normalize_tick.
  - 直接调用：`Decimal`, `Tick`, `self._symbol_mapping.to_instrument_id`
  - 可解析内部调用：`qts.domain.market_data.bar.Tick`, `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.to_instrument_id`
- `qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter.normalize_quote`
  - 类型：`method`
  - 位置：`backend/src/qts/data/adapters/ibkr_market_data.py:81`
  - 说明：Perform normalize_quote.
  - 直接调用：`Decimal`, `Quote`, `self._symbol_mapping.to_instrument_id`
  - 可解析内部调用：`qts.domain.market_data.bar.Quote`, `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.to_instrument_id`
- `qts.data.adapters.ibkr_market_data.IbkrMarketDataAdapter.normalize_bar`
  - 类型：`method`
  - 位置：`backend/src/qts/data/adapters/ibkr_market_data.py:101`
  - 说明：Perform normalize_bar.
  - 直接调用：`Bar`, `Decimal`, `self._symbol_mapping.to_instrument_id`
  - 可解析内部调用：`qts.domain.market_data.bar.Bar`, `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.to_instrument_id`

### `backend/src/qts/data/bars/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/data/bars/aggregator.py`

- `qts.data.bars.aggregator.AggregationState`
  - 类型：`class`
  - 位置：`backend/src/qts/data/bars/aggregator.py:18`
  - 说明：Current in-progress aggregation bucket.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.bars.aggregator.AggregationState.aggregate_end`
  - 类型：`property`
  - 位置：`backend/src/qts/data/bars/aggregator.py:27`
  - 说明：Perform aggregate_end.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.bars.aggregator.AggregationResult`
  - 类型：`class`
  - 位置：`backend/src/qts/data/bars/aggregator.py:33`
  - 说明：Result returned by one incremental aggregator update.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.bars.aggregator.BarAggregator`
  - 类型：`class`
  - 位置：`backend/src/qts/data/bars/aggregator.py:40`
  - 说明：Stateful incremental bar aggregator for one ordered bar stream.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.bars.aggregator.BarAggregator.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/data/bars/aggregator.py:43`
  - 说明：Perform __init__.
  - 直接调用：`ValueError`
  - 可解析内部调用：无
- `qts.data.bars.aggregator.BarAggregator.update`
  - 类型：`method`
  - 位置：`backend/src/qts/data/bars/aggregator.py:58`
  - 说明：Add a lower-timeframe bar and return any completed aggregate bars.
  - 直接调用：`AggregationResult`, `AggregationState`, `_aggregate_state`, `_bar_inside_session`, `_same_stream_bucket`, `completed.append`, `self._new_state_for`, `tuple`
  - 可解析内部调用：`qts.data.bars.aggregator.AggregationResult`, `qts.data.bars.aggregator.AggregationState`, `qts.data.bars.aggregator.BarAggregator._new_state_for`, `qts.data.bars.aggregator._aggregate_state`, `qts.data.bars.aggregator._bar_inside_session`, `qts.data.bars.aggregator._same_stream_bucket`, `qts.data.sessions.filter._bar_inside_session`, `qts.indicators.rolling.RollingWindow.append`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`
- `qts.data.bars.aggregator.BarAggregator.finish`
  - 类型：`method`
  - 位置：`backend/src/qts/data/bars/aggregator.py:87`
  - 说明：Flush the current bucket as a partial aggregate when present.
  - 直接调用：`AggregationResult`, `_aggregate_state`
  - 可解析内部调用：`qts.data.bars.aggregator.AggregationResult`, `qts.data.bars.aggregator._aggregate_state`
- `qts.data.bars.aggregator.BarAggregator._new_state_for`
  - 类型：`method`
  - 位置：`backend/src/qts/data/bars/aggregator.py:96`
  - 说明：Perform _new_state_for.
  - 直接调用：`AggregationState`, `TimeInterval`, `clock_bucket_for`
  - 可解析内部调用：`qts.core.time.TimeInterval`, `qts.data.bars.aggregator.AggregationState`, `qts.data.bars.alignment.clock_bucket_for`
- `qts.data.bars.aggregator.aggregate_bars`
  - 类型：`module_function`
  - 位置：`backend/src/qts/data/bars/aggregator.py:110`
  - 说明：Aggregate bars into a higher clock-aligned timeframe.
  - 直接调用：`BarAggregator`, `aggregated.extend`, `aggregator.finish`, `aggregator.update`, `aggregators.setdefault`, `aggregators.values`, `sorted`
  - 可解析内部调用：`qts.backtest.report.StreamingEquityMetrics.update`, `qts.data.bars.aggregator.BarAggregator`, `qts.data.bars.aggregator.BarAggregator.finish`, `qts.data.bars.aggregator.BarAggregator.update`, `qts.indicators.price.ema.EMA.update`, `qts.indicators.price.sma.SMA.update`, `qts.strategy_sdk.indicators.AssetIndicator.update`
- `qts.data.bars.aggregator._bar_inside_session`
  - 类型：`module_function`
  - 位置：`backend/src/qts/data/bars/aggregator.py:139`
  - 说明：Perform _bar_inside_session.
  - 直接调用：`session.interval.contains`
  - 可解析内部调用：`qts.core.time.TimeInterval.contains`
- `qts.data.bars.aggregator._same_stream_bucket`
  - 类型：`module_function`
  - 位置：`backend/src/qts/data/bars/aggregator.py:144`
  - 说明：Perform _same_stream_bucket.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.bars.aggregator._aggregate_state`
  - 类型：`module_function`
  - 位置：`backend/src/qts/data/bars/aggregator.py:153`
  - 说明：Perform _aggregate_state.
  - 直接调用：`Bar`, `Decimal`, `ValueError`, `_aggregate_vwap`, `_last_open_interest`, `_sum_trade_count`, `all`, `max`, `min`, `str`, `sum`
  - 可解析内部调用：`qts.data.bars.aggregator._aggregate_vwap`, `qts.data.bars.aggregator._last_open_interest`, `qts.data.bars.aggregator._sum_trade_count`, `qts.domain.market_data.bar.Bar`
- `qts.data.bars.aggregator._aggregate_vwap`
  - 类型：`module_function`
  - 位置：`backend/src/qts/data/bars/aggregator.py:194`
  - 说明：Perform _aggregate_vwap.
  - 直接调用：`Decimal`, `sum`
  - 可解析内部调用：无
- `qts.data.bars.aggregator._last_open_interest`
  - 类型：`module_function`
  - 位置：`backend/src/qts/data/bars/aggregator.py:204`
  - 说明：Perform _last_open_interest.
  - 直接调用：`reversed`
  - 可解析内部调用：无
- `qts.data.bars.aggregator._sum_trade_count`
  - 类型：`module_function`
  - 位置：`backend/src/qts/data/bars/aggregator.py:212`
  - 说明：Perform _sum_trade_count.
  - 直接调用：`sum`
  - 可解析内部调用：无

### `backend/src/qts/data/bars/alignment.py`

- `qts.data.bars.alignment.clock_bucket_for`
  - 类型：`module_function`
  - 位置：`backend/src/qts/data/bars/alignment.py:11`
  - 说明：Return the exchange-clock bucket containing ``timestamp``.
  - 直接调用：`TimeInterval`, `ValueError`, `_duration_seconds`, `exchange_time.replace`, `int`, `timedelta`, `to_exchange_time`
  - 可解析内部调用：`qts.core.time.TimeInterval`, `qts.core.time.to_exchange_time`, `qts.data.bars.alignment._duration_seconds`
- `qts.data.bars.alignment._duration_seconds`
  - 类型：`module_function`
  - 位置：`backend/src/qts/data/bars/alignment.py:36`
  - 说明：Perform _duration_seconds.
  - 直接调用：`ValueError`, `duration.total_seconds`, `int`
  - 可解析内部调用：无

### `backend/src/qts/data/bars/pipeline.py`

- `qts.data.bars.pipeline.BarAggregationPipeline`
  - 类型：`class`
  - 位置：`backend/src/qts/data/bars/pipeline.py:15`
  - 说明：Own incremental aggregation state for bar streams in memory.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.bars.pipeline.BarAggregationPipeline.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/data/bars/pipeline.py:18`
  - 说明：Perform __init__.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.bars.pipeline.BarAggregationPipeline.aggregate`
  - 类型：`method`
  - 位置：`backend/src/qts/data/bars/pipeline.py:23`
  - 说明：Aggregate one 1+ minute bar into an explicit target timeframe.
  - 直接调用：`self._aggregation_key`, `self._aggregator_for`, `self._aggregator_for.update`
  - 可解析内部调用：`qts.backtest.report.StreamingEquityMetrics.update`, `qts.data.bars.aggregator.BarAggregator.update`, `qts.data.bars.pipeline.BarAggregationPipeline._aggregation_key`, `qts.data.bars.pipeline.BarAggregationPipeline._aggregator_for`, `qts.indicators.price.ema.EMA.update`, `qts.indicators.price.sma.SMA.update`, `qts.strategy_sdk.indicators.AssetIndicator.update`
- `qts.data.bars.pipeline.BarAggregationPipeline.aggregate_logical`
  - 类型：`method`
  - 位置：`backend/src/qts/data/bars/pipeline.py:29`
  - 说明：Aggregate bars from one source timeframe into a logical subscriber target.
  - 直接调用：`Timeframe.parse`, `self._aggregator_for`, `self._aggregator_for.update`, `self._logical_key`
  - 可解析内部调用：`qts.backtest.report.StreamingEquityMetrics.update`, `qts.data.bars.aggregator.BarAggregator.update`, `qts.data.bars.pipeline.BarAggregationPipeline._aggregator_for`, `qts.data.bars.pipeline.BarAggregationPipeline._logical_key`, `qts.data.bars.timeframe.Timeframe.parse`, `qts.indicators.price.ema.EMA.update`, `qts.indicators.price.sma.SMA.update`, `qts.strategy_sdk.indicators.AssetIndicator.update`
- `qts.data.bars.pipeline.BarAggregationPipeline._aggregator_for`
  - 类型：`method`
  - 位置：`backend/src/qts/data/bars/pipeline.py:42`
  - 说明：Perform _aggregator_for.
  - 直接调用：`BarAggregator`, `self._aggregators.get`
  - 可解析内部调用：`qts.data.bars.aggregator.BarAggregator`, `qts.runtime.mailbox.Mailbox.get`
- `qts.data.bars.pipeline.BarAggregationPipeline._aggregation_key`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/data/bars/pipeline.py:56`
  - 说明：Perform _aggregation_key.
  - 直接调用：`str`
  - 可解析内部调用：无
- `qts.data.bars.pipeline.BarAggregationPipeline._logical_key`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/data/bars/pipeline.py:61`
  - 说明：Perform _logical_key.
  - 直接调用：无
  - 可解析内部调用：无

### `backend/src/qts/data/bars/timeframe.py`

- `qts.data.bars.timeframe.AlignmentMode`
  - 类型：`class`
  - 位置：`backend/src/qts/data/bars/timeframe.py:10`
  - 说明：How bars for a timeframe align to time.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.bars.timeframe.Timeframe`
  - 类型：`class`
  - 位置：`backend/src/qts/data/bars/timeframe.py:29`
  - 说明：Bar timeframe with explicit alignment semantics.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.bars.timeframe.Timeframe.parse`
  - 类型：`classmethod`
  - 位置：`backend/src/qts/data/bars/timeframe.py:37`
  - 说明：Perform parse.
  - 直接调用：`ValueError`, `cls`, `value.strip`, `value.strip.lower`
  - 可解析内部调用：无
- `qts.data.bars.timeframe.Timeframe.__str__`
  - 类型：`method`
  - 位置：`backend/src/qts/data/bars/timeframe.py:50`
  - 说明：Perform __str__.
  - 直接调用：无
  - 可解析内部调用：无

### `backend/src/qts/data/feeds/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/data/feeds/replay_feed.py`

- `qts.data.feeds.replay_feed.ReplayFeed`
  - 类型：`class`
  - 位置：`backend/src/qts/data/feeds/replay_feed.py:12`
  - 说明：Deterministic replay feed over stored bars.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.feeds.replay_feed.ReplayFeed.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/data/feeds/replay_feed.py:15`
  - 说明：Perform __init__.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.feeds.replay_feed.ReplayFeed.events`
  - 类型：`method`
  - 位置：`backend/src/qts/data/feeds/replay_feed.py:19`
  - 说明：Perform events.
  - 直接调用：`self._store.read_bars`
  - 可解析内部调用：`qts.data.stores.base.MarketDataStore.read_bars`, `qts.data.stores.memory_store.InMemoryMarketDataStore.read_bars`, `qts.data.stores.parquet_store.ParquetMarketDataStore.read_bars`

### `backend/src/qts/data/historical/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/data/historical/catalog.py`

- `qts.data.historical.catalog.HistoricalDataset`
  - 类型：`class`
  - 位置：`backend/src/qts/data/historical/catalog.py:19`
  - 说明：One local historical dataset entry.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.historical.catalog.HistoricalDataset.normalize_root`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/data/historical/catalog.py:34`
  - 说明：Perform normalize_root.
  - 直接调用：`ValueError`, `root.strip`, `root.strip.upper`
  - 可解析内部调用：无
- `qts.data.historical.catalog.HistoricalCatalog`
  - 类型：`class`
  - 位置：`backend/src/qts/data/historical/catalog.py:43`
  - 说明：Explicit catalog for a local historical data layout.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.historical.catalog.HistoricalCatalog.load`
  - 类型：`classmethod`
  - 位置：`backend/src/qts/data/historical/catalog.py:51`
  - 说明：Load a catalog from one cohesive construction config.
  - 直接调用：`HistoricalDataConfig.from_yaml`, `RuntimeError`, `cls._symbol_resolvers_for_load_config`, `cls.from_historical_data_config`, `cls.from_legacy_root`
  - 可解析内部调用：`qts.data.historical.catalog.HistoricalCatalog._symbol_resolvers_for_load_config`, `qts.data.historical.catalog.HistoricalCatalog.from_historical_data_config`, `qts.data.historical.catalog.HistoricalCatalog.from_legacy_root`, `qts.data.historical.catalog.HistoricalCatalogLoadConfig.from_historical_data_config`, `qts.data.historical.catalog.HistoricalCatalogLoadConfig.from_legacy_root`, `qts.data.historical.config.HistoricalDataConfig.from_yaml`
- `qts.data.historical.catalog.HistoricalCatalog.from_legacy_root`
  - 类型：`classmethod`
  - 位置：`backend/src/qts/data/historical/catalog.py:80`
  - 说明：Load requested roots from a local historical data directory.
  - 直接调用：`HistoricalChain.load`, `HistoricalDataset`, `HistoricalDataset.normalize_root`, `HistoricalFutureChainSymbolResolver`, `ValueError`, `cls`, `cls._require_file`, `describe_csv_dataset`, `items`, `resolvers.get`, `root.lower`, `tuple`
  - 可解析内部调用：`qts.data.historical.catalog.HistoricalCatalog._require_file`, `qts.data.historical.catalog.HistoricalDataset`, `qts.data.historical.catalog.HistoricalDataset.normalize_root`, `qts.data.historical.chains.HistoricalChain.load`, `qts.data.historical.csv_dataset.describe_csv_dataset`, `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver`, `qts.runtime.mailbox.Mailbox.get`
- `qts.data.historical.catalog.HistoricalCatalog.from_historical_data_config`
  - 类型：`classmethod`
  - 位置：`backend/src/qts/data/historical/catalog.py:124`
  - 说明：Load requested roots from a project-level historical data catalog.
  - 直接调用：`FileNotFoundError`, `HistoricalChain.load`, `HistoricalDataset`, `HistoricalDataset.normalize_root`, `HistoricalFutureChainSymbolResolver`, `ValueError`, `cls`, `cls._require_file`, `config.catalog`, `config.resolve_dataset`, `config.store`, `describe_csv_dataset`, `items`, `resolvers.get`, `tuple`
  - 可解析内部调用：`qts.data.historical.catalog.HistoricalCatalog._require_file`, `qts.data.historical.catalog.HistoricalDataset`, `qts.data.historical.catalog.HistoricalDataset.normalize_root`, `qts.data.historical.chains.HistoricalChain.load`, `qts.data.historical.config.HistoricalDataConfig.catalog`, `qts.data.historical.config.HistoricalDataConfig.resolve_dataset`, `qts.data.historical.config.HistoricalDataConfig.store`, `qts.data.historical.csv_dataset.describe_csv_dataset`, `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver`, `qts.runtime.mailbox.Mailbox.get`
- `qts.data.historical.catalog.HistoricalCatalog._symbol_resolvers_for_load_config`
  - 类型：`classmethod`
  - 位置：`backend/src/qts/data/historical/catalog.py:186`
  - 说明：Perform _symbol_resolvers_for_load_config.
  - 直接调用：`StaticSymbolResolver`, `cls._chain_path_exists`
  - 可解析内部调用：`qts.data.historical.catalog.HistoricalCatalog._chain_path_exists`, `qts.registry.symbol_resolution.StaticSymbolResolver`
- `qts.data.historical.catalog.HistoricalCatalog._chain_path_exists`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/data/historical/catalog.py:206`
  - 说明：Perform _chain_path_exists.
  - 直接调用：`RuntimeError`, `chain_path.exists`, `exists`, `historical_data_config.resolve_chain_path`
  - 可解析内部调用：`qts.data.historical.config.HistoricalDataConfig.resolve_chain_path`
- `qts.data.historical.catalog.HistoricalCatalog._require_file`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/data/historical/catalog.py:223`
  - 说明：Perform _require_file.
  - 直接调用：`FileNotFoundError`, `Path`, `path.exists`, `path.relative_to`
  - 可解析内部调用：无
- `qts.data.historical.catalog.HistoricalCatalogLoadConfig`
  - 类型：`class`
  - 位置：`backend/src/qts/data/historical/catalog.py:234`
  - 说明：Construction inputs for a configured historical catalog.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.historical.catalog.HistoricalCatalogLoadConfig.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/catalog.py:244`
  - 说明：Perform __post_init__.
  - 直接调用：`HistoricalDataset.normalize_root`, `InstrumentId`, `Path`, `ValueError`, `isinstance`, `object.__setattr__`, `self._normalize_symbol`, `self.catalog_name.strip`, `self.instrument_ids.items`, `self.requested_timeframe.strip`, `str`, `tuple`
  - 可解析内部调用：`qts.backtest.config.BacktestRunConfig._normalize_symbol`, `qts.core.ids.InstrumentId`, `qts.data.historical.catalog.HistoricalCatalogLoadConfig._normalize_symbol`, `qts.data.historical.catalog.HistoricalDataset.normalize_root`, `qts.registry.instrument_registry.InstrumentRegistry._normalize_symbol`, `qts.registry.symbol_resolution.StaticSymbolResolver._normalize_symbol`
- `qts.data.historical.catalog.HistoricalCatalogLoadConfig.from_legacy_root`
  - 类型：`classmethod`
  - 位置：`backend/src/qts/data/historical/catalog.py:286`
  - 说明：Perform from_legacy_root.
  - 直接调用：`cls`
  - 可解析内部调用：无
- `qts.data.historical.catalog.HistoricalCatalogLoadConfig.from_historical_data_config`
  - 类型：`classmethod`
  - 位置：`backend/src/qts/data/historical/catalog.py:303`
  - 说明：Perform from_historical_data_config.
  - 直接调用：`cls`
  - 可解析内部调用：无
- `qts.data.historical.catalog.HistoricalCatalogLoadConfig._normalize_symbol`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/data/historical/catalog.py:322`
  - 说明：Perform _normalize_symbol.
  - 直接调用：`ValueError`, `symbol.strip`, `symbol.strip.upper`
  - 可解析内部调用：无

### `backend/src/qts/data/historical/chains.py`

- `qts.data.historical.chains.HistoricalContract`
  - 类型：`class`
  - 位置：`backend/src/qts/data/historical/chains.py:16`
  - 说明：One outright contract from a historical chain file.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.historical.chains.HistoricalChain`
  - 类型：`class`
  - 位置：`backend/src/qts/data/historical/chains.py:31`
  - 说明：Parsed historical futures chain.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.historical.chains.HistoricalChain.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/chains.py:44`
  - 说明：Perform __post_init__.
  - 直接调用：`contracts_by_symbol.setdefault`, `object.__setattr__`
  - 可解析内部调用：无
- `qts.data.historical.chains.HistoricalChain.contract_for_symbol`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/chains.py:55`
  - 说明：Perform contract_for_symbol.
  - 直接调用：`KeyError`
  - 可解析内部调用：无
- `qts.data.historical.chains.HistoricalChain.is_outright_symbol`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/chains.py:62`
  - 说明：Perform is_outright_symbol.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.historical.chains.HistoricalChain.instrument_id_for_symbol`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/chains.py:66`
  - 说明：Perform instrument_id_for_symbol.
  - 直接调用：`InstrumentId`, `ValueError`, `self.is_outright_symbol`
  - 可解析内部调用：`qts.core.ids.InstrumentId`, `qts.data.historical.chains.HistoricalChain.is_outright_symbol`
- `qts.data.historical.chains.HistoricalChain.load`
  - 类型：`classmethod`
  - 位置：`backend/src/qts/data/historical/chains.py:73`
  - 说明：Load a historical futures chain JSON file into typed metadata.
  - 直接调用：`ValueError`, `cls`, `cls._exchange_code`, `cls._parse_contract`, `cls._required_decimal`, `cls._required_text`, `isinstance`, `json.loads`, `path.read_text`, `payload.get`, `tuple`
  - 可解析内部调用：`qts.data.historical.chains.HistoricalChain._exchange_code`, `qts.data.historical.chains.HistoricalChain._parse_contract`, `qts.data.historical.chains.HistoricalChain._required_decimal`, `qts.data.historical.chains.HistoricalChain._required_text`, `qts.runtime.mailbox.Mailbox.get`
- `qts.data.historical.chains.HistoricalChain._parse_contract`
  - 类型：`classmethod`
  - 位置：`backend/src/qts/data/historical/chains.py:112`
  - 说明：Perform _parse_contract.
  - 直接调用：`HistoricalContract`, `ValueError`, `cls._required_text`, `date.fromisoformat`, `datetime.fromisoformat`, `datetime.fromisoformat.astimezone`, `isinstance`, `item.get`, `str`
  - 可解析内部调用：`qts.data.historical.chains.HistoricalChain._required_text`, `qts.data.historical.chains.HistoricalContract`, `qts.runtime.mailbox.Mailbox.get`
- `qts.data.historical.chains.HistoricalChain._required_text`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/data/historical/chains.py:143`
  - 说明：Perform _required_text.
  - 直接调用：`ValueError`, `isinstance`, `payload.get`, `value.strip`
  - 可解析内部调用：`qts.runtime.mailbox.Mailbox.get`
- `qts.data.historical.chains.HistoricalChain._required_decimal`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/data/historical/chains.py:151`
  - 说明：Perform _required_decimal.
  - 直接调用：`Decimal`, `ValueError`, `str`
  - 可解析内部调用：无
- `qts.data.historical.chains.HistoricalChain._exchange_code`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/data/historical/chains.py:161`
  - 说明：Perform _exchange_code.
  - 直接调用：`market.endswith`, `market.removesuffix`
  - 可解析内部调用：无

### `backend/src/qts/data/historical/config.py`

- `qts.data.historical.config.HistoricalDataStoreDefaults`
  - 类型：`class`
  - 位置：`backend/src/qts/data/historical/config.py:14`
  - 说明：Default metadata applied to datasets and bars in one historical store.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.historical.config.HistoricalDataStoreDefaults.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/config.py:22`
  - 说明：Perform __post_init__.
  - 直接调用：`ValueError`, `self.exchange_timezone.strip`, `self.normalization.strip`, `self.schema.strip`, `self.timezone_policy.strip`
  - 可解析内部调用：无
- `qts.data.historical.config.HistoricalDataStoreConfig`
  - 类型：`class`
  - 位置：`backend/src/qts/data/historical/config.py:35`
  - 说明：Project-level physical layout for a historical data store.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.historical.config.HistoricalDataStoreConfig.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/config.py:51`
  - 说明：Perform __post_init__.
  - 直接调用：`ValueError`, `self.bars_file_template.strip`, `self.chain_file_template.strip`, `self.exchange_timezone.strip`, `self.name.strip`, `self.normalization.strip`, `self.source_timeframe.strip`, `self.timezone_policy.strip`, `self.type.strip`, `str`, `str.strip`
  - 可解析内部调用：无
- `qts.data.historical.config.HistoricalDataStoreConfig.bars_path`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/config.py:72`
  - 说明：Perform bars_path.
  - 直接调用：`self._join`, `self._render_template`
  - 可解析内部调用：`qts.data.historical.config.HistoricalDataStoreConfig._join`, `qts.data.historical.config.HistoricalDataStoreConfig._render_template`
- `qts.data.historical.config.HistoricalDataStoreConfig.chain_path`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/config.py:77`
  - 说明：Perform chain_path.
  - 直接调用：`self._join`, `self._render_template`
  - 可解析内部调用：`qts.data.historical.config.HistoricalDataStoreConfig._join`, `qts.data.historical.config.HistoricalDataStoreConfig._render_template`
- `qts.data.historical.config.HistoricalDataStoreConfig._join`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/config.py:82`
  - 说明：Perform _join.
  - 直接调用：`path.is_absolute`
  - 可解析内部调用：无
- `qts.data.historical.config.HistoricalDataStoreConfig._render_template`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/data/historical/config.py:87`
  - 说明：Perform _render_template.
  - 直接调用：`HistoricalDatasetConfig.normalize_root`, `normalized_root.lower`, `template.format`
  - 可解析内部调用：`qts.data.historical.config.HistoricalDatasetConfig.normalize_root`, `qts.quality.guardrails.GuardrailViolation.format`
- `qts.data.historical.config.HistoricalBarFileConfig`
  - 类型：`class`
  - 位置：`backend/src/qts/data/historical/config.py:94`
  - 说明：One physical bar file for a dataset.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.historical.config.HistoricalBarFileConfig.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/config.py:104`
  - 说明：Perform __post_init__.
  - 直接调用：`ValueError`, `self.exchange_timezone.strip`, `self.file.strip`, `self.normalization.strip`, `self.schema.strip`, `self.timeframe.strip`, `self.timezone_policy.strip`
  - 可解析内部调用：无
- `qts.data.historical.config.HistoricalDatasetConfig`
  - 类型：`class`
  - 位置：`backend/src/qts/data/historical/config.py:121`
  - 说明：One product/data entry inside a historical data catalog.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.historical.config.HistoricalDatasetConfig.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/config.py:134`
  - 说明：Perform __post_init__.
  - 直接调用：`ValueError`, `self.asset_class.strip`, `self.bars_file.strip`, `self.chain_file.strip`, `self.exchange.strip`, `self.exchange_timezone.strip`, `self.root.strip`, `self.schema.strip`, `self.source_timeframe.strip`
  - 可解析内部调用：无
- `qts.data.historical.config.HistoricalDatasetConfig.requires_chain`
  - 类型：`property`
  - 位置：`backend/src/qts/data/historical/config.py:154`
  - 说明：Perform requires_chain.
  - 直接调用：`self.asset_class.strip`, `self.asset_class.strip.lower`
  - 可解析内部调用：无
- `qts.data.historical.config.HistoricalDatasetConfig.normalize_root`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/data/historical/config.py:159`
  - 说明：Perform normalize_root.
  - 直接调用：`ValueError`, `root.strip`, `root.strip.upper`
  - 可解析内部调用：无
- `qts.data.historical.config.HistoricalDataCatalogConfig`
  - 类型：`class`
  - 位置：`backend/src/qts/data/historical/config.py:168`
  - 说明：Logical catalog of historical datasets backed by one store.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.historical.config.HistoricalDataCatalogConfig.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/config.py:175`
  - 说明：Perform __post_init__.
  - 直接调用：`ValueError`, `self.name.strip`, `self.store.strip`
  - 可解析内部调用：无
- `qts.data.historical.config.HistoricalDatasetLocation`
  - 类型：`class`
  - 位置：`backend/src/qts/data/historical/config.py:186`
  - 说明：Resolved physical file paths for one catalog dataset.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.historical.config.HistoricalDataConfig`
  - 类型：`class`
  - 位置：`backend/src/qts/data/historical/config.py:202`
  - 说明：Project-level historical data stores and catalogs.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.historical.config.HistoricalDataConfig.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/config.py:209`
  - 说明：Perform __post_init__.
  - 直接调用：`ValueError`, `self.catalogs.values`
  - 可解析内部调用：无
- `qts.data.historical.config.HistoricalDataConfig.from_yaml`
  - 类型：`classmethod`
  - 位置：`backend/src/qts/data/historical/config.py:220`
  - 说明：Perform from_yaml.
  - 直接调用：`HistoricalDataConfigLoader.from_path`
  - 可解析内部调用：`qts.data.historical.config_loader.HistoricalDataConfigLoader.from_path`
- `qts.data.historical.config.HistoricalDataConfig.from_payload`
  - 类型：`classmethod`
  - 位置：`backend/src/qts/data/historical/config.py:227`
  - 说明：Perform from_payload.
  - 直接调用：`HistoricalDataConfigLoader.from_payload`, `ValueError`, `isinstance`
  - 可解析内部调用：`qts.data.historical.config_loader.HistoricalDataConfigLoader.from_payload`
- `qts.data.historical.config.HistoricalDataConfig.catalog`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/config.py:235`
  - 说明：Perform catalog.
  - 直接调用：`KeyError`
  - 可解析内部调用：无
- `qts.data.historical.config.HistoricalDataConfig.store`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/config.py:242`
  - 说明：Perform store.
  - 直接调用：`KeyError`
  - 可解析内部调用：无
- `qts.data.historical.config.HistoricalDataConfig.resolve_dataset`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/config.py:249`
  - 说明：Perform resolve_dataset.
  - 直接调用：`HistoricalDatasetConfig.normalize_root`, `HistoricalDatasetLocation`, `KeyError`, `self._csv_schema`, `self._select_bar_file`, `self.catalog`, `self.store`, `store.bars_path`, `store.chain_path`
  - 可解析内部调用：`qts.data.historical.config.HistoricalDataConfig._csv_schema`, `qts.data.historical.config.HistoricalDataConfig._select_bar_file`, `qts.data.historical.config.HistoricalDataConfig.catalog`, `qts.data.historical.config.HistoricalDataConfig.store`, `qts.data.historical.config.HistoricalDataStoreConfig.bars_path`, `qts.data.historical.config.HistoricalDataStoreConfig.chain_path`, `qts.data.historical.config.HistoricalDatasetConfig.normalize_root`, `qts.data.historical.config.HistoricalDatasetLocation`
- `qts.data.historical.config.HistoricalDataConfig.resolve_chain_path`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/config.py:296`
  - 说明：Resolve chain metadata path without selecting a concrete bar file.
  - 直接调用：`HistoricalDatasetConfig.normalize_root`, `KeyError`, `self.catalog`, `self.store`, `store.chain_path`
  - 可解析内部调用：`qts.data.historical.config.HistoricalDataConfig.catalog`, `qts.data.historical.config.HistoricalDataConfig.store`, `qts.data.historical.config.HistoricalDataStoreConfig.chain_path`, `qts.data.historical.config.HistoricalDatasetConfig.normalize_root`
- `qts.data.historical.config.HistoricalDataConfig._csv_schema`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/config.py:312`
  - 说明：Perform _csv_schema.
  - 直接调用：`KeyError`
  - 可解析内部调用：无
- `qts.data.historical.config.HistoricalDataConfig._select_bar_file`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/data/historical/config.py:322`
  - 说明：Perform _select_bar_file.
  - 直接调用：`FeedCapabilities`, `FeedCapabilities.source_timeframe_for`, `HistoricalBarFileConfig`, `RuntimeError`, `ValueError`, `frozenset`, `len`
  - 可解析内部调用：`qts.data.historical.config.HistoricalBarFileConfig`, `qts.data.live.capabilities.FeedCapabilities`, `qts.data.live.capabilities.FeedCapabilities.source_timeframe_for`

### `backend/src/qts/data/historical/config_loader.py`

- `qts.data.historical.config_loader.HistoricalDataConfigLoader`
  - 类型：`class`
  - 位置：`backend/src/qts/data/historical/config_loader.py:31`
  - 说明：Load historical data configuration from files or payload dictionaries.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.historical.config_loader.HistoricalDataConfigLoader.from_path`
  - 类型：`classmethod`
  - 位置：`backend/src/qts/data/historical/config_loader.py:35`
  - 说明：Perform from_path.
  - 直接调用：`ValueError`, `cls.from_payload`, `isinstance`, `path.read_text`, `yaml.safe_load`
  - 可解析内部调用：`qts.backtest.config_loader.BacktestConfigLoader.from_payload`, `qts.config.ibkr.IbkrEnvironmentConfig.from_payload`, `qts.data.historical.config.HistoricalDataConfig.from_payload`, `qts.data.historical.config_loader.HistoricalDataConfigLoader.from_payload`
- `qts.data.historical.config_loader.HistoricalDataConfigLoader.from_payload`
  - 类型：`classmethod`
  - 位置：`backend/src/qts/data/historical/config_loader.py:43`
  - 说明：Perform from_payload.
  - 直接调用：`HistoricalDataConfig`, `ValueError`, `cls._parse_catalogs`, `cls._parse_schemas`, `cls._parse_stores`, `isinstance`, `payload.get`, `raw_config.get`
  - 可解析内部调用：`qts.data.historical.config.HistoricalDataConfig`, `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_catalogs`, `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_schemas`, `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_stores`, `qts.runtime.mailbox.Mailbox.get`
- `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_stores`
  - 类型：`classmethod`
  - 位置：`backend/src/qts/data/historical/config_loader.py:57`
  - 说明：Perform _parse_stores.
  - 直接调用：`HistoricalDataStoreConfig`, `Path`, `ValueError`, `cls._parse_store_defaults`, `isinstance`, `payload.items`, `raw_store.get`, `str`
  - 可解析内部调用：`qts.data.historical.config.HistoricalDataStoreConfig`, `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_store_defaults`, `qts.runtime.mailbox.Mailbox.get`
- `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_store_defaults`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/data/historical/config_loader.py:95`
  - 说明：Perform _parse_store_defaults.
  - 直接调用：`HistoricalDataStoreDefaults`, `ValueError`, `isinstance`, `raw_defaults.get`, `raw_store.get`, `str`
  - 可解析内部调用：`qts.data.historical.config.HistoricalDataStoreDefaults`, `qts.runtime.mailbox.Mailbox.get`
- `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_catalogs`
  - 类型：`classmethod`
  - 位置：`backend/src/qts/data/historical/config_loader.py:127`
  - 说明：Perform _parse_catalogs.
  - 直接调用：`HistoricalDataCatalogConfig`, `ValueError`, `cls._parse_datasets`, `isinstance`, `payload.items`, `raw_catalog.get`, `str`
  - 可解析内部调用：`qts.data.historical.config.HistoricalDataCatalogConfig`, `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_datasets`, `qts.runtime.mailbox.Mailbox.get`
- `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_datasets`
  - 类型：`classmethod`
  - 位置：`backend/src/qts/data/historical/config_loader.py:148`
  - 说明：Perform _parse_datasets.
  - 直接调用：`HistoricalDatasetConfig`, `HistoricalDatasetConfig.normalize_root`, `ValueError`, `_DATASET_STORAGE_PATH_KEYS.intersection`, `cls._parse_bar_files`, `isinstance`, `join`, `payload.items`, `raw_dataset.get`, `sorted`, `str`
  - 可解析内部调用：`qts.data.historical.config.HistoricalDatasetConfig`, `qts.data.historical.config.HistoricalDatasetConfig.normalize_root`, `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_bar_files`, `qts.runtime.mailbox.Mailbox.get`
- `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_bar_files`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/data/historical/config_loader.py:199`
  - 说明：Perform _parse_bar_files.
  - 直接调用：`HistoricalBarFileConfig`, `ValueError`, `bars.append`, `isinstance`, `raw_bar.get`, `str`, `tuple`
  - 可解析内部调用：`qts.data.historical.config.HistoricalBarFileConfig`, `qts.indicators.rolling.RollingWindow.append`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`, `qts.runtime.mailbox.Mailbox.get`
- `qts.data.historical.config_loader.HistoricalDataConfigLoader._parse_schemas`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/data/historical/config_loader.py:236`
  - 说明：Perform _parse_schemas.
  - 直接调用：`HistoricalCsvSchema`, `ValueError`, `isinstance`, `payload.items`, `raw_schema.get`, `str`
  - 可解析内部调用：`qts.data.historical.csv_format.HistoricalCsvSchema`, `qts.runtime.mailbox.Mailbox.get`

### `backend/src/qts/data/historical/csv_dataset.py`

- `qts.data.historical.csv_dataset.CsvDatasetDescription`
  - 类型：`class`
  - 位置：`backend/src/qts/data/historical/csv_dataset.py:42`
  - 说明：Cheap metadata description for a historical CSV dataset.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.historical.csv_dataset.HistoricalBarStream`
  - 类型：`class`
  - 位置：`backend/src/qts/data/historical/csv_dataset.py:55`
  - 说明：Lazy iterable over historical bars with side-channel reader stats.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.historical.csv_dataset.HistoricalBarStream.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/csv_dataset.py:58`
  - 说明：Perform init.
  - 直接调用：`HistoricalCsvRowMapper`, `HistoricalCsvStats`
  - 可解析内部调用：`qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper`, `qts.data.historical.validation.HistoricalCsvStats`
- `qts.data.historical.csv_dataset.HistoricalBarStream.__iter__`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/csv_dataset.py:85`
  - 说明：Perform iter.
  - 直接调用：`csv.DictReader`, `self._csv_path.open`, `self._iter_all_supported_rows`, `self._iter_selected_contract_rows`, `self._iter_session_selected_contract_rows`, `tuple`, `validate_historical_csv_columns`
  - 可解析内部调用：`qts.data.historical.csv_dataset.HistoricalBarStream._iter_all_supported_rows`, `qts.data.historical.csv_dataset.HistoricalBarStream._iter_selected_contract_rows`, `qts.data.historical.csv_dataset.HistoricalBarStream._iter_session_selected_contract_rows`, `qts.data.historical.csv_format.validate_historical_csv_columns`
- `qts.data.historical.csv_dataset.HistoricalBarStream._iter_all_supported_rows`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/csv_dataset.py:99`
  - 说明：Perform iter all supported rows.
  - 直接调用：`self._count_excluded_symbol`, `self._field`, `self._row_mapper.to_bar`, `self._symbol_resolver.is_supported_symbol`, `self._timestamp`
  - 可解析内部调用：`qts.data.historical.csv_dataset.HistoricalBarStream._count_excluded_symbol`, `qts.data.historical.csv_dataset.HistoricalBarStream._field`, `qts.data.historical.csv_dataset.HistoricalBarStream._timestamp`, `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper._field`, `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper.to_bar`, `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver.is_supported_symbol`, `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.is_supported_symbol`, `qts.registry.symbol_resolution.SourceSymbolResolver.is_supported_symbol`, `qts.registry.symbol_resolution.StaticSymbolResolver.is_supported_symbol`
- `qts.data.historical.csv_dataset.HistoricalBarStream._iter_selected_contract_rows`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/csv_dataset.py:122`
  - 说明：Perform iter selected contract rows.
  - 直接调用：`FutureContractCandidate`, `FutureRollSelection`, `RuntimeError`, `candidates.append`, `contract_selector.select`, `len`, `replace`, `self._count_excluded_symbol`, `self._field`, `self._resolver_root`, `self._row_mapper.to_bar`, `self._symbol_resolver.is_supported_symbol`, `self._timestamp_groups`, `self.roll_selections.append`, `tuple`
  - 可解析内部调用：`qts.data.historical.csv_dataset.HistoricalBarStream._count_excluded_symbol`, `qts.data.historical.csv_dataset.HistoricalBarStream._field`, `qts.data.historical.csv_dataset.HistoricalBarStream._resolver_root`, `qts.data.historical.csv_dataset.HistoricalBarStream._timestamp_groups`, `qts.data.historical.csv_dataset._resolver_root`, `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper._field`, `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper.to_bar`, `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver.is_supported_symbol`, `qts.indicators.rolling.RollingWindow.append`, `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.is_supported_symbol`, `qts.registry.future_roll.FutureContractCandidate`, `qts.registry.future_roll.FutureContractSelector.select`, `qts.registry.future_roll.FutureRollSelection`, `qts.registry.future_roll.HighestVolumeFutureContractSelector.select`, `qts.registry.symbol_resolution.SourceSymbolResolver.is_supported_symbol`, `qts.registry.symbol_resolution.StaticSymbolResolver.is_supported_symbol`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`
- `qts.data.historical.csv_dataset.HistoricalBarStream._iter_session_selected_contract_rows`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/csv_dataset.py:183`
  - 说明：Perform iter session selected contract rows.
  - 直接调用：`RuntimeError`, `current_groups.append`, `self._emit_selected_session_rows`, `self._timestamp_groups`, `session_window.session_id_for_timestamp`
  - 可解析内部调用：`qts.data.historical.csv_dataset.HistoricalBarStream._emit_selected_session_rows`, `qts.data.historical.csv_dataset.HistoricalBarStream._timestamp_groups`, `qts.data.sessions.window.RegularSessionWindow.session_id_for_timestamp`, `qts.indicators.rolling.RollingWindow.append`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`
- `qts.data.historical.csv_dataset.HistoricalBarStream._emit_selected_session_rows`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/csv_dataset.py:229`
  - 说明：Perform emit selected session rows.
  - 直接调用：`Decimal`, `FutureContractCandidate`, `FutureRollSelection`, `closes_by_timestamp.append`, `contract_selector.select`, `defaultdict`, `historical_timeframe_delta`, `len`, `replace`, `rows_by_instrument.get`, `rows_by_timestamp.append`, `self._count_excluded_symbol`, `self._field`, `self._resolver_root`, `self._row_mapper.extract_ohlcv`, `self._row_mapper.to_bar`, `self._symbol_resolver.instrument_id_for_symbol`, `self._symbol_resolver.is_supported_symbol`, `self.roll_selections.append`, `total_volume_by_instrument.items`, `tuple`, `zip`
  - 可解析内部调用：`qts.data.historical.chains.HistoricalChain.instrument_id_for_symbol`, `qts.data.historical.csv_dataset.HistoricalBarStream._count_excluded_symbol`, `qts.data.historical.csv_dataset.HistoricalBarStream._field`, `qts.data.historical.csv_dataset.HistoricalBarStream._resolver_root`, `qts.data.historical.csv_dataset._resolver_root`, `qts.data.historical.csv_format.historical_timeframe_delta`, `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper._field`, `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper.extract_ohlcv`, `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper.to_bar`, `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver.instrument_id_for_symbol`, `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver.is_supported_symbol`, `qts.indicators.rolling.RollingWindow.append`, `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.instrument_id_for_symbol`, `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.is_supported_symbol`, `qts.registry.future_roll.FutureContractCandidate`, `qts.registry.future_roll.FutureContractSelector.select`, `qts.registry.future_roll.FutureRollSelection`, `qts.registry.future_roll.HighestVolumeFutureContractSelector.select`, `qts.registry.symbol_resolution.SourceSymbolResolver.instrument_id_for_symbol`, `qts.registry.symbol_resolution.SourceSymbolResolver.is_supported_symbol`, `qts.registry.symbol_resolution.StaticSymbolResolver.instrument_id_for_symbol`, `qts.registry.symbol_resolution.StaticSymbolResolver.is_supported_symbol`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`, `qts.runtime.mailbox.Mailbox.get`
- `qts.data.historical.csv_dataset.HistoricalBarStream._timestamp_groups`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/csv_dataset.py:316`
  - 说明：Perform timestamp groups.
  - 直接调用：`current_rows.append`, `parse_historical_ts_event`, `self._field`
  - 可解析内部调用：`qts.data.historical.csv_dataset.HistoricalBarStream._field`, `qts.data.historical.csv_format.parse_historical_ts_event`, `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper._field`, `qts.indicators.rolling.RollingWindow.append`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`
- `qts.data.historical.csv_dataset.HistoricalBarStream._count_excluded_symbol`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/csv_dataset.py:333`
  - 说明：Perform count excluded symbol.
  - 直接调用：`_is_spread_symbol`
  - 可解析内部调用：`qts.data.historical.csv_dataset._is_spread_symbol`, `qts.data.historical.validation._is_spread_symbol`
- `qts.data.historical.csv_dataset.HistoricalBarStream._resolver_root`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/csv_dataset.py:338`
  - 说明：Perform resolver root.
  - 直接调用：`_resolver_root`
  - 可解析内部调用：`qts.data.historical.csv_dataset._resolver_root`
- `qts.data.historical.csv_dataset.HistoricalBarStream._field`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/csv_dataset.py:341`
  - 说明：Perform field.
  - 直接调用：`self._schema.resolve_column`
  - 可解析内部调用：`qts.data.historical.csv_format.HistoricalCsvSchema.resolve_column`
- `qts.data.historical.csv_dataset.HistoricalBarStream._timestamp`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/csv_dataset.py:344`
  - 说明：Perform timestamp.
  - 直接调用：`parse_historical_ts_event`, `self._field`
  - 可解析内部调用：`qts.data.historical.csv_dataset.HistoricalBarStream._field`, `qts.data.historical.csv_format.parse_historical_ts_event`, `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper._field`
- `qts.data.historical.csv_dataset.describe_csv_dataset`
  - 类型：`module_function`
  - 位置：`backend/src/qts/data/historical/csv_dataset.py:348`
  - 说明：Read historical CSV identity metadata without materializing row data.
  - 直接调用：`CsvDatasetDescription`, `csv.reader`, `next`, `path.open`, `sum`, `tuple`, `validate_historical_csv_columns`
  - 可解析内部调用：`qts.data.historical.csv_dataset.CsvDatasetDescription`, `qts.data.historical.csv_format.validate_historical_csv_columns`
- `qts.data.historical.csv_dataset.iter_historical_bars`
  - 类型：`module_function`
  - 位置：`backend/src/qts/data/historical/csv_dataset.py:375`
  - 说明：Return a lazy stream of outright historical bars.
  - 直接调用：`HistoricalBarStream`, `_as_symbol_resolver`
  - 可解析内部调用：`qts.data.historical.csv_dataset.HistoricalBarStream`, `qts.data.historical.csv_dataset._as_symbol_resolver`
- `qts.data.historical.csv_dataset.validate_historical_sample`
  - 类型：`module_function`
  - 位置：`backend/src/qts/data/historical/csv_dataset.py:402`
  - 说明：Validate a bounded sample or full CSV when `sample_rows` is None.
  - 直接调用：`HistoricalDatasetValidator`, `HistoricalDatasetValidator.validate_sample`, `_as_symbol_resolver`
  - 可解析内部调用：`qts.data.historical.csv_dataset._as_symbol_resolver`, `qts.data.historical.validation.HistoricalDatasetValidator`, `qts.data.historical.validation.HistoricalDatasetValidator.validate_sample`
- `qts.data.historical.csv_dataset._resolver_root`
  - 类型：`module_function`
  - 位置：`backend/src/qts/data/historical/csv_dataset.py:420`
  - 说明：Perform resolver root.
  - 直接调用：`ValueError`, `isinstance`
  - 可解析内部调用：无
- `qts.data.historical.csv_dataset.RootSymbolResolver`
  - 类型：`class`
  - 位置：`backend/src/qts/data/historical/csv_dataset.py:430`
  - 说明：Protocol for symbol resolvers that provide a root identifier.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.historical.csv_dataset.RootSymbolResolver.root`
  - 类型：`property`
  - 位置：`backend/src/qts/data/historical/csv_dataset.py:434`
  - 说明：Return the root identifier.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.historical.csv_dataset._as_symbol_resolver`
  - 类型：`module_function`
  - 位置：`backend/src/qts/data/historical/csv_dataset.py:439`
  - 说明：Perform as symbol resolver.
  - 直接调用：`HistoricalFutureChainSymbolResolver`, `isinstance`
  - 可解析内部调用：`qts.data.historical.symbols.HistoricalFutureChainSymbolResolver`
- `qts.data.historical.csv_dataset._is_spread_symbol`
  - 类型：`module_function`
  - 位置：`backend/src/qts/data/historical/csv_dataset.py:447`
  - 说明：Perform is spread symbol.
  - 直接调用：无
  - 可解析内部调用：无

### `backend/src/qts/data/historical/csv_format.py`

- `qts.data.historical.csv_format.HistoricalCsvSchema`
  - 类型：`class`
  - 位置：`backend/src/qts/data/historical/csv_format.py:24`
  - 说明：Mapping from framework OHLCV semantics to concrete CSV columns.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.historical.csv_format.HistoricalCsvSchema.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/csv_format.py:36`
  - 说明：Perform __post_init__.
  - 直接调用：`ValueError`, `any`, `item.strip`, `self.instrument_id.strip`
  - 可解析内部调用：无
- `qts.data.historical.csv_format.HistoricalCsvSchema.required_columns`
  - 类型：`property`
  - 位置：`backend/src/qts/data/historical/csv_format.py:53`
  - 说明：Perform required_columns.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.historical.csv_format.HistoricalCsvSchema.validate_columns`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/csv_format.py:65`
  - 说明：Perform validate_columns.
  - 直接调用：`ValueError`, `join`, `tuple`
  - 可解析内部调用：无
- `qts.data.historical.csv_format.HistoricalCsvSchema.resolve_column`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/csv_format.py:73`
  - 说明：Resolve an OHLCV semantic field name to the configured CSV column.
  - 直接调用：`ValueError`
  - 可解析内部调用：无
- `qts.data.historical.csv_format.HistoricalCsvSchema.column_indices`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/csv_format.py:96`
  - 说明：Perform column_indices.
  - 直接调用：`enumerate`, `self.validate_columns`
  - 可解析内部调用：`qts.data.historical.csv_format.HistoricalCsvSchema.validate_columns`
- `qts.data.historical.csv_format.validate_historical_csv_columns`
  - 类型：`module_function`
  - 位置：`backend/src/qts/data/historical/csv_format.py:114`
  - 说明：Validate historical CSV columns against the configured schema.
  - 直接调用：`ValueError`, `join`, `schema.validate_columns`
  - 可解析内部调用：`qts.data.historical.csv_format.HistoricalCsvSchema.validate_columns`
- `qts.data.historical.csv_format.parse_historical_ts_event`
  - 类型：`module_function`
  - 位置：`backend/src/qts/data/historical/csv_format.py:131`
  - 说明：Parse a historical CSV UTC timestamp, accepting nanosecond text input.
  - 直接调用：`ValueError`, `datetime.fromisoformat`, `ljust`, `parsed.astimezone`, `text.split`, `value.endswith`, `value.removesuffix`
  - 可解析内部调用：无
- `qts.data.historical.csv_format.historical_timeframe_delta`
  - 类型：`module_function`
  - 位置：`backend/src/qts/data/historical/csv_format.py:146`
  - 说明：Return the duration represented by a supported historical timeframe.
  - 直接调用：`ValueError`, `int`, `timedelta`, `timeframe.endswith`
  - 可解析内部调用：无

### `backend/src/qts/data/historical/csv_row_mapper.py`

- `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper`
  - 类型：`class`
  - 位置：`backend/src/qts/data/historical/csv_row_mapper.py:21`
  - 说明：Map one validated CSV row to an OHLCV bar.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper.to_bar`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/csv_row_mapper.py:27`
  - 说明：Map a mapped row dict into a typed bar.
  - 直接调用：`Bar`, `historical_timeframe_delta`, `parse_historical_ts_event`, `self._field`, `self.extract_ohlcv`, `start_time.astimezone`, `start_time.astimezone.date`, `start_time.astimezone.date.isoformat`, `symbol_resolver.instrument_id_for_symbol`
  - 可解析内部调用：`qts.data.historical.chains.HistoricalChain.instrument_id_for_symbol`, `qts.data.historical.csv_dataset.HistoricalBarStream._field`, `qts.data.historical.csv_format.historical_timeframe_delta`, `qts.data.historical.csv_format.parse_historical_ts_event`, `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper._field`, `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper.extract_ohlcv`, `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver.instrument_id_for_symbol`, `qts.domain.market_data.bar.Bar`, `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.instrument_id_for_symbol`, `qts.registry.symbol_resolution.SourceSymbolResolver.instrument_id_for_symbol`, `qts.registry.symbol_resolution.StaticSymbolResolver.instrument_id_for_symbol`
- `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper.extract_ohlcv`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/csv_row_mapper.py:48`
  - 说明：Extract and validate OHLCV fields from a mapped row.
  - 直接调用：`self._field`, `self._parse_ohlcv_values`
  - 可解析内部调用：`qts.data.historical.csv_dataset.HistoricalBarStream._field`, `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper._field`, `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper._parse_ohlcv_values`
- `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper._field`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/csv_row_mapper.py:61`
  - 说明：Perform _field.
  - 直接调用：`self.schema.resolve_column`
  - 可解析内部调用：`qts.data.historical.csv_format.HistoricalCsvSchema.resolve_column`
- `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper._parse_ohlcv_values`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/data/historical/csv_row_mapper.py:66`
  - 说明：Perform _parse_ohlcv_values.
  - 直接调用：`Decimal`, `ValueError`, `max`, `min`
  - 可解析内部调用：无

### `backend/src/qts/data/historical/service.py`

- `qts.data.historical.service.HistoricalMarketDataService`
  - 类型：`class`
  - 位置：`backend/src/qts/data/historical/service.py:21`
  - 说明：Deterministic historical market data source with feed-like contracts.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.historical.service.HistoricalMarketDataService.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/service.py:32`
  - 说明：Perform __post_init__.
  - 直接调用：`ValueError`, `self.source_id.strip`, `self.source_timeframe.strip`
  - 可解析内部调用：无
- `qts.data.historical.service.HistoricalMarketDataService.capabilities`
  - 类型：`property`
  - 位置：`backend/src/qts/data/historical/service.py:40`
  - 说明：Perform capabilities.
  - 直接调用：`FeedCapabilities`, `frozenset`
  - 可解析内部调用：`qts.data.live.capabilities.FeedCapabilities`
- `qts.data.historical.service.HistoricalMarketDataService.subscribe`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/service.py:50`
  - 说明：Perform subscribe.
  - 直接调用：`MarketDataSubscribed`, `self.capabilities.source_timeframe_for`
  - 可解析内部调用：`qts.data.live.capabilities.FeedCapabilities.source_timeframe_for`, `qts.data.live.events.MarketDataSubscribed`
- `qts.data.historical.service.HistoricalMarketDataService.events`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/service.py:56`
  - 说明：Perform events.
  - 直接调用：`KeyError`, `LiveFeedEvent`, `ValueError`, `iter_historical_bars`, `subscription_id.strip`
  - 可解析内部调用：`qts.data.historical.csv_dataset.iter_historical_bars`, `qts.data.live.events.LiveFeedEvent`
- `qts.data.historical.service.ReplayMarketDataAdapter`
  - 类型：`class`
  - 位置：`backend/src/qts/data/historical/service.py:76`
  - 说明：Canonical replay-market-data adapter name for historical sources.
  - 直接调用：无
  - 可解析内部调用：无

### `backend/src/qts/data/historical/symbols.py`

- `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver`
  - 类型：`class`
  - 位置：`backend/src/qts/data/historical/symbols.py:12`
  - 说明：Resolve historical futures outright symbols through chain metadata.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver.root`
  - 类型：`property`
  - 位置：`backend/src/qts/data/historical/symbols.py:18`
  - 说明：Perform root.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver.is_supported_symbol`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/symbols.py:22`
  - 说明：Perform is_supported_symbol.
  - 直接调用：`self.chain.is_outright_symbol`
  - 可解析内部调用：`qts.data.historical.chains.HistoricalChain.is_outright_symbol`
- `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver.instrument_id_for_symbol`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/symbols.py:26`
  - 说明：Perform instrument_id_for_symbol.
  - 直接调用：`self.chain.instrument_id_for_symbol`
  - 可解析内部调用：`qts.data.historical.chains.HistoricalChain.instrument_id_for_symbol`, `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver.instrument_id_for_symbol`, `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.instrument_id_for_symbol`, `qts.registry.symbol_resolution.SourceSymbolResolver.instrument_id_for_symbol`, `qts.registry.symbol_resolution.StaticSymbolResolver.instrument_id_for_symbol`

### `backend/src/qts/data/historical/validation.py`

- `qts.data.historical.validation.HistoricalCsvStats`
  - 类型：`class`
  - 位置：`backend/src/qts/data/historical/validation.py:30`
  - 说明：Streaming counters for historical CSV validation.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.historical.validation.HistoricalCsvStats.as_dict`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/validation.py:40`
  - 说明：Perform as_dict.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.historical.validation.HistoricalValidationSample`
  - 类型：`class`
  - 位置：`backend/src/qts/data/historical/validation.py:53`
  - 说明：Validation report plus counters for one sampled historical file.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.historical.validation.HistoricalDatasetValidator`
  - 类型：`class`
  - 位置：`backend/src/qts/data/historical/validation.py:62`
  - 说明：Validate historical sample files and return domain-friendly diagnostics.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.historical.validation.HistoricalDatasetValidator.validate_sample`
  - 类型：`method`
  - 位置：`backend/src/qts/data/historical/validation.py:67`
  - 说明：Perform validate_sample.
  - 直接调用：`DataValidationIssue`, `DataValidationReport`, `HistoricalCsvRowMapper`, `HistoricalCsvStats`, `HistoricalValidationSample`, `ValueError`, `_group_bars`, `_group_bars.values`, `_is_spread_symbol`, `bars.append`, `csv.DictReader`, `csv_path.open`, `historical_timeframe_delta`, `issues.append`, `issues.extend`, `mapper.to_bar`, `resolver.is_supported_symbol`, `tuple`, `validate_bars`, `validate_historical_csv_columns`
  - 可解析内部调用：`qts.data.historical.csv_dataset._is_spread_symbol`, `qts.data.historical.csv_format.historical_timeframe_delta`, `qts.data.historical.csv_format.validate_historical_csv_columns`, `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper`, `qts.data.historical.csv_row_mapper.HistoricalCsvRowMapper.to_bar`, `qts.data.historical.symbols.HistoricalFutureChainSymbolResolver.is_supported_symbol`, `qts.data.historical.validation.HistoricalCsvStats`, `qts.data.historical.validation.HistoricalValidationSample`, `qts.data.historical.validation._group_bars`, `qts.data.historical.validation._is_spread_symbol`, `qts.data.validation_report.DataValidationIssue`, `qts.data.validation_report.DataValidationReport`, `qts.data.validation_report.validate_bars`, `qts.indicators.rolling.RollingWindow.append`, `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.is_supported_symbol`, `qts.registry.symbol_resolution.SourceSymbolResolver.is_supported_symbol`, `qts.registry.symbol_resolution.StaticSymbolResolver.is_supported_symbol`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`
- `qts.data.historical.validation._group_bars`
  - 类型：`module_function`
  - 位置：`backend/src/qts/data/historical/validation.py:142`
  - 说明：Perform _group_bars.
  - 直接调用：`append`, `defaultdict`
  - 可解析内部调用：`qts.indicators.rolling.RollingWindow.append`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`
- `qts.data.historical.validation._is_spread_symbol`
  - 类型：`module_function`
  - 位置：`backend/src/qts/data/historical/validation.py:150`
  - 说明：Perform _is_spread_symbol.
  - 直接调用：无
  - 可解析内部调用：无

### `backend/src/qts/data/live/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/data/live/adapter.py`

- `qts.data.live.adapter.LiveFeedAdapter`
  - 类型：`class`
  - 位置：`backend/src/qts/data/live/adapter.py:12`
  - 说明：Live market data feed adapter boundary.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.live.adapter.LiveFeedAdapter.capabilities`
  - 类型：`property`
  - 位置：`backend/src/qts/data/live/adapter.py:16`
  - 说明：Return feed capabilities.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.live.adapter.LiveFeedAdapter.subscribe`
  - 类型：`method`
  - 位置：`backend/src/qts/data/live/adapter.py:20`
  - 说明：Subscribe to a live feed stream.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.live.adapter.MarketDataAdapter`
  - 类型：`class`
  - 位置：`backend/src/qts/data/live/adapter.py:25`
  - 说明：Canonical market-data source adapter contract shared by live and replay feeds.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.live.adapter.MarketDataAdapter.capabilities`
  - 类型：`property`
  - 位置：`backend/src/qts/data/live/adapter.py:29`
  - 说明：Return feed capabilities.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.live.adapter.MarketDataAdapter.subscribe`
  - 类型：`method`
  - 位置：`backend/src/qts/data/live/adapter.py:33`
  - 说明：Subscribe to a source stream.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.live.adapter.ReplayMarketDataAdapter`
  - 类型：`class`
  - 位置：`backend/src/qts/data/live/adapter.py:38`
  - 说明：Canonical replay market-data adapter contract for historical sources.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.live.adapter.ReplayMarketDataAdapter.capabilities`
  - 类型：`property`
  - 位置：`backend/src/qts/data/live/adapter.py:42`
  - 说明：Return feed capabilities.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.live.adapter.ReplayMarketDataAdapter.subscribe`
  - 类型：`method`
  - 位置：`backend/src/qts/data/live/adapter.py:46`
  - 说明：Subscribe to a replay stream.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.live.adapter.ReplayMarketDataAdapter.events`
  - 类型：`method`
  - 位置：`backend/src/qts/data/live/adapter.py:50`
  - 说明：Iterate replay events for a subscription.
  - 直接调用：无
  - 可解析内部调用：无

### `backend/src/qts/data/live/capabilities.py`

- `qts.data.live.capabilities.FeedCapabilities`
  - 类型：`class`
  - 位置：`backend/src/qts/data/live/capabilities.py:11`
  - 说明：Feed-supported live market data capabilities.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.live.capabilities.FeedCapabilities.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/data/live/capabilities.py:21`
  - 说明：Perform post init.
  - 直接调用：`ValueError`, `any`, `item.strip`, `self.source_id.strip`
  - 可解析内部调用：无
- `qts.data.live.capabilities.FeedCapabilities.supports_timeframe`
  - 类型：`method`
  - 位置：`backend/src/qts/data/live/capabilities.py:29`
  - 说明：Return whether the requested timeframe is directly supported.
  - 直接调用：`ValueError`, `timeframe.strip`
  - 可解析内部调用：无
- `qts.data.live.capabilities.FeedCapabilities.source_timeframe_for`
  - 类型：`method`
  - 位置：`backend/src/qts/data/live/capabilities.py:35`
  - 说明：Return provider timeframe used to fulfill a requested timeframe.
  - 直接调用：`ValueError`, `requested_timeframe.strip`, `self.supports_timeframe`
  - 可解析内部调用：`qts.data.live.capabilities.FeedCapabilities.supports_timeframe`

### `backend/src/qts/data/live/events.py`

- `qts.data.live.events.FeedSubscription`
  - 类型：`class`
  - 位置：`backend/src/qts/data/live/events.py:14`
  - 说明：Internal live feed subscription request.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.live.events.FeedSubscription.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/data/live/events.py:21`
  - 说明：Perform post init.
  - 直接调用：`ValueError`, `self.subscription_id.strip`, `self.timeframe.strip`
  - 可解析内部调用：无
- `qts.data.live.events.MarketDataSubscribed`
  - 类型：`class`
  - 位置：`backend/src/qts/data/live/events.py:29`
  - 说明：Successful market-data source subscription acknowledgement.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.live.events.LiveFeedEvent`
  - 类型：`class`
  - 位置：`backend/src/qts/data/live/events.py:37`
  - 说明：Live feed payload emitted by a subscription.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.live.events.LiveFeedFailure`
  - 类型：`class`
  - 位置：`backend/src/qts/data/live/events.py:45`
  - 说明：Live feed failure notification.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.live.events.LiveFeedFailure.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/data/live/events.py:52`
  - 说明：Perform post init.
  - 直接调用：`ValueError`, `self.reason.strip`
  - 可解析内部调用：无

### `backend/src/qts/data/live/fake_adapter.py`

- `qts.data.live.fake_adapter.FakeLiveFeedAdapter`
  - 类型：`class`
  - 位置：`backend/src/qts/data/live/fake_adapter.py:16`
  - 说明：Deterministic fake live market data feed.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.live.fake_adapter.FakeLiveFeedAdapter.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/data/live/fake_adapter.py:19`
  - 说明：Perform init.
  - 直接调用：`ValueError`, `source_id.strip`
  - 可解析内部调用：无
- `qts.data.live.fake_adapter.FakeLiveFeedAdapter.capabilities`
  - 类型：`property`
  - 位置：`backend/src/qts/data/live/fake_adapter.py:34`
  - 说明：Return adapter capabilities.
  - 直接调用：`FeedCapabilities`
  - 可解析内部调用：`qts.data.live.capabilities.FeedCapabilities`
- `qts.data.live.fake_adapter.FakeLiveFeedAdapter.subscription_count`
  - 类型：`property`
  - 位置：`backend/src/qts/data/live/fake_adapter.py:39`
  - 说明：Return current active subscription count.
  - 直接调用：`len`
  - 可解析内部调用：无
- `qts.data.live.fake_adapter.FakeLiveFeedAdapter.subscribe`
  - 类型：`method`
  - 位置：`backend/src/qts/data/live/fake_adapter.py:43`
  - 说明：Accept a new subscription and acknowledge it.
  - 直接调用：`MarketDataSubscribed`
  - 可解析内部调用：`qts.data.live.events.MarketDataSubscribed`
- `qts.data.live.fake_adapter.FakeLiveFeedAdapter.emit`
  - 类型：`method`
  - 位置：`backend/src/qts/data/live/fake_adapter.py:48`
  - 说明：Emit a typed live feed event.
  - 直接调用：`LiveFeedEvent`
  - 可解析内部调用：`qts.data.live.events.LiveFeedEvent`
- `qts.data.live.fake_adapter.FakeLiveFeedAdapter.fail`
  - 类型：`method`
  - 位置：`backend/src/qts/data/live/fake_adapter.py:52`
  - 说明：Create a failure event for a tracked subscription.
  - 直接调用：`KeyError`, `LiveFeedFailure`
  - 可解析内部调用：`qts.data.live.events.LiveFeedFailure`
- `qts.data.live.fake_adapter.FakeMarketDataAdapter`
  - 类型：`class`
  - 位置：`backend/src/qts/data/live/fake_adapter.py:63`
  - 说明：Canonical fake adapter name used for market-data source tests.
  - 直接调用：无
  - 可解析内部调用：无

### `backend/src/qts/data/live/reconnect.py`

- `qts.data.live.reconnect.ReconnectPolicy`
  - 类型：`class`
  - 位置：`backend/src/qts/data/live/reconnect.py:11`
  - 说明：Deterministic reconnect backoff policy.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.live.reconnect.ReconnectPolicy.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/data/live/reconnect.py:19`
  - 说明：Perform post init.
  - 直接调用：`Decimal`, `ValueError`, `timedelta`
  - 可解析内部调用：无
- `qts.data.live.reconnect.ReconnectPolicy.delay_for_attempt`
  - 类型：`method`
  - 位置：`backend/src/qts/data/live/reconnect.py:29`
  - 说明：Return delay for given reconnect attempt, or None after max attempts.
  - 直接调用：`ValueError`, `float`, `min`, `self.initial_delay.total_seconds`, `timedelta`
  - 可解析内部调用：无

### `backend/src/qts/data/live_feed.py`

- 无类/函数/方法符号。

### `backend/src/qts/data/normalization/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/data/provenance.py`

- `qts.data.provenance.DatasetMetadata`
  - 类型：`class`
  - 位置：`backend/src/qts/data/provenance.py:13`
  - 说明：Stable reference to historical data used by simulation or research.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.provenance.DatasetMetadata.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/data/provenance.py:26`
  - 说明：Perform __post_init__.
  - 直接调用：`require_aware_datetime`, `self._require_text`
  - 可解析内部调用：`qts.core.time.require_aware_datetime`, `qts.data.provenance.DatasetMetadata._require_text`
- `qts.data.provenance.DatasetMetadata.reference`
  - 类型：`property`
  - 位置：`backend/src/qts/data/provenance.py:39`
  - 说明：Perform reference.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.provenance.DatasetMetadata._require_text`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/data/provenance.py:45`
  - 说明：Perform _require_text.
  - 直接调用：`ValueError`, `value.strip`
  - 可解析内部调用：无

### `backend/src/qts/data/sessions/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/data/sessions/filter.py`

- `qts.data.sessions.filter.SessionLookup`
  - 类型：`class`
  - 位置：`backend/src/qts/data/sessions/filter.py:13`
  - 说明：Calendar session lookup required by session filters.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.sessions.filter.SessionLookup.session_for`
  - 类型：`method`
  - 位置：`backend/src/qts/data/sessions/filter.py:16`
  - 说明：Return the internal market session for the date.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.sessions.filter.filter_session_bars`
  - 类型：`module_function`
  - 位置：`backend/src/qts/data/sessions/filter.py:20`
  - 说明：Return bars whose start and end fall inside the half-open session.
  - 直接调用：`_bar_inside_session`, `calendar_registry.session_for`
  - 可解析内部调用：`qts.data.bars.aggregator._bar_inside_session`, `qts.data.sessions.filter.SessionLookup.session_for`, `qts.data.sessions.filter._bar_inside_session`, `qts.registry.calendar_registry.CalendarProvider.session_for`, `qts.registry.calendar_registry.CalendarRegistry.session_for`, `qts.registry.providers.comex_gold_calendar_provider.ComexGoldCalendarProvider.session_for`, `qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider.session_for`, `qts.risk.rules.trading_session_rule.SessionLookup.session_for`
- `qts.data.sessions.filter._bar_inside_session`
  - 类型：`module_function`
  - 位置：`backend/src/qts/data/sessions/filter.py:33`
  - 说明：Perform _bar_inside_session.
  - 直接调用：`session.interval.contains`
  - 可解析内部调用：`qts.core.time.TimeInterval.contains`

### `backend/src/qts/data/sessions/window.py`

- `qts.data.sessions.window.RegularSessionWindow`
  - 类型：`class`
  - 位置：`backend/src/qts/data/sessions/window.py:12`
  - 说明：A recurring half-open exchange session window.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.sessions.window.RegularSessionWindow.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/data/sessions/window.py:23`
  - 说明：Perform __post_init__.
  - 直接调用：`ValueError`, `self.exchange_timezone.strip`
  - 可解析内部调用：无
- `qts.data.sessions.window.RegularSessionWindow.session_id_for_timestamp`
  - 类型：`method`
  - 位置：`backend/src/qts/data/sessions/window.py:30`
  - 说明：Return the exchange-local close-date session id containing timestamp.
  - 直接调用：`self.session_date_for_timestamp`, `session_date.isoformat`
  - 可解析内部调用：`qts.data.sessions.window.RegularSessionWindow.session_date_for_timestamp`
- `qts.data.sessions.window.RegularSessionWindow.session_date_for_timestamp`
  - 类型：`method`
  - 位置：`backend/src/qts/data/sessions/window.py:36`
  - 说明：Return the exchange-local close date for timestamp, or None if outside.
  - 直接调用：`local_timestamp.date`, `local_timestamp.time`, `timedelta`, `to_exchange_time`
  - 可解析内部调用：`qts.core.time.to_exchange_time`
- `qts.data.sessions.window.RegularSessionWindow.to_payload`
  - 类型：`method`
  - 位置：`backend/src/qts/data/sessions/window.py:51`
  - 说明：Return a stable JSON-serializable description of the session rule.
  - 直接调用：无
  - 可解析内部调用：无

### `backend/src/qts/data/stores/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/data/stores/base.py`

- `qts.data.stores.base.MarketDataStore`
  - 类型：`class`
  - 位置：`backend/src/qts/data/stores/base.py:13`
  - 说明：Store and read bars by internal instrument identity.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.stores.base.MarketDataStore.write_bars`
  - 类型：`method`
  - 位置：`backend/src/qts/data/stores/base.py:16`
  - 说明：Persist bars.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.stores.base.MarketDataStore.read_bars`
  - 类型：`method`
  - 位置：`backend/src/qts/data/stores/base.py:20`
  - 说明：Read bars for an interval.
  - 直接调用：无
  - 可解析内部调用：无

### `backend/src/qts/data/stores/memory_store.py`

- `qts.data.stores.memory_store.InMemoryMarketDataStore`
  - 类型：`class`
  - 位置：`backend/src/qts/data/stores/memory_store.py:13`
  - 说明：In-memory bar store for tests and local runs.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.stores.memory_store.InMemoryMarketDataStore.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/data/stores/memory_store.py:16`
  - 说明：Perform __init__.
  - 直接调用：`defaultdict`
  - 可解析内部调用：无
- `qts.data.stores.memory_store.InMemoryMarketDataStore.write_bars`
  - 类型：`method`
  - 位置：`backend/src/qts/data/stores/memory_store.py:20`
  - 说明：Perform write_bars.
  - 直接调用：`append`, `sort`
  - 可解析内部调用：`qts.indicators.rolling.RollingWindow.append`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`
- `qts.data.stores.memory_store.InMemoryMarketDataStore.read_bars`
  - 类型：`method`
  - 位置：`backend/src/qts/data/stores/memory_store.py:27`
  - 说明：Perform read_bars.
  - 直接调用：`self._bars.get`, `tuple`
  - 可解析内部调用：`qts.runtime.mailbox.Mailbox.get`

### `backend/src/qts/data/stores/parquet_store.py`

- `qts.data.stores.parquet_store.ParquetMarketDataStore`
  - 类型：`class`
  - 位置：`backend/src/qts/data/stores/parquet_store.py:21`
  - 说明：File-backed bar store partitioned by instrument, timeframe, and date.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.stores.parquet_store.ParquetMarketDataStore.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/data/stores/parquet_store.py:24`
  - 说明：Perform __init__.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.stores.parquet_store.ParquetMarketDataStore.write_bars`
  - 类型：`method`
  - 位置：`backend/src/qts/data/stores/parquet_store.py:28`
  - 说明：Perform write_bars.
  - 直接调用：`grouped.items`, `grouped.setdefault`, `grouped.setdefault.append`, `handle.write`, `json.dumps`, `list`, `path.exists`, `path.open`, `path.parent.mkdir`, `self._bar_to_json`, `self._path_for`, `self._read_file`, `sorted`
  - 可解析内部调用：`qts.backtest.report._NdjsonArtifact.write`, `qts.data.stores.parquet_store.ParquetMarketDataStore._bar_to_json`, `qts.data.stores.parquet_store.ParquetMarketDataStore._path_for`, `qts.data.stores.parquet_store.ParquetMarketDataStore._read_file`, `qts.indicators.rolling.RollingWindow.append`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`
- `qts.data.stores.parquet_store.ParquetMarketDataStore.read_bars`
  - 类型：`method`
  - 位置：`backend/src/qts/data/stores/parquet_store.py:45`
  - 说明：Perform read_bars.
  - 直接调用：`bars.extend`, `base.exists`, `base.glob`, `self._read_file`, `sorted`, `tuple`
  - 可解析内部调用：`qts.data.stores.parquet_store.ParquetMarketDataStore._read_file`
- `qts.data.stores.parquet_store.ParquetMarketDataStore._path_for`
  - 类型：`method`
  - 位置：`backend/src/qts/data/stores/parquet_store.py:66`
  - 说明：Perform _path_for.
  - 直接调用：`bar.start_time.date`, `bar.start_time.date.isoformat`
  - 可解析内部调用：无
- `qts.data.stores.parquet_store.ParquetMarketDataStore._read_file`
  - 类型：`method`
  - 位置：`backend/src/qts/data/stores/parquet_store.py:75`
  - 说明：Perform _read_file.
  - 直接调用：`json.loads`, `line.strip`, `path.open`, `self._bar_from_json`, `tuple`
  - 可解析内部调用：`qts.data.stores.parquet_store.ParquetMarketDataStore._bar_from_json`
- `qts.data.stores.parquet_store.ParquetMarketDataStore._bar_to_json`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/data/stores/parquet_store.py:81`
  - 说明：Perform _bar_to_json.
  - 直接调用：`bar.end_time.isoformat`, `bar.start_time.isoformat`, `str`
  - 可解析内部调用：无
- `qts.data.stores.parquet_store.ParquetMarketDataStore._bar_from_json`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/data/stores/parquet_store.py:102`
  - 说明：Perform _bar_from_json.
  - 直接调用：`Bar`, `Decimal`, `InstrumentId`, `bool`, `datetime.fromisoformat`, `int`, `str`
  - 可解析内部调用：`qts.core.ids.InstrumentId`, `qts.domain.market_data.bar.Bar`

### `backend/src/qts/data/subscriptions.py`

- `qts.data.subscriptions.SourceStreamType`
  - 类型：`class`
  - 位置：`backend/src/qts/data/subscriptions.py:12`
  - 说明：Physical market data stream type.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.subscriptions.LogicalSubscription`
  - 类型：`class`
  - 位置：`backend/src/qts/data/subscriptions.py:21`
  - 说明：Strategy-requested market data stream.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.subscriptions.LogicalSubscription.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/data/subscriptions.py:29`
  - 说明：Perform __post_init__.
  - 直接调用：`ValueError`, `self.requested_timeframe.strip`, `self.subscriber_id.strip`
  - 可解析内部调用：无
- `qts.data.subscriptions.LogicalSubscriptionKey`
  - 类型：`class`
  - 位置：`backend/src/qts/data/subscriptions.py:38`
  - 说明：Deduplication key for strategy-facing subscribers.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.subscriptions.PhysicalSubscriptionKey`
  - 类型：`class`
  - 位置：`backend/src/qts/data/subscriptions.py:47`
  - 说明：Deduplication key for provider-facing subscriptions.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.subscriptions.PhysicalSubscriptionKey.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/data/subscriptions.py:55`
  - 说明：Perform __post_init__.
  - 直接调用：`ValueError`, `self.source_id.strip`, `self.source_timeframe.strip`
  - 可解析内部调用：无
- `qts.data.subscriptions.logical_key`
  - 类型：`module_function`
  - 位置：`backend/src/qts/data/subscriptions.py:63`
  - 说明：Return the logical fan-out key for a subscription.
  - 直接调用：`LogicalSubscriptionKey`
  - 可解析内部调用：`qts.data.subscriptions.LogicalSubscriptionKey`
- `qts.data.subscriptions.plan_physical_subscription`
  - 类型：`module_function`
  - 位置：`backend/src/qts/data/subscriptions.py:73`
  - 说明：Map one logical subscription to its provider source subscription.
  - 直接调用：`PhysicalSubscriptionKey`, `ValueError`, `capabilities.source_timeframe_for`
  - 可解析内部调用：`qts.data.live.capabilities.FeedCapabilities.source_timeframe_for`, `qts.data.subscriptions.PhysicalSubscriptionKey`

### `backend/src/qts/data/validation_report.py`

- `qts.data.validation_report.DataValidationIssueCode`
  - 类型：`class`
  - 位置：`backend/src/qts/data/validation_report.py:13`
  - 说明：Known market data validation issue codes.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.validation_report.DataValidationSeverity`
  - 类型：`class`
  - 位置：`backend/src/qts/data/validation_report.py:27`
  - 说明：Severity for data validation issues.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.validation_report.DataValidationIssue`
  - 类型：`class`
  - 位置：`backend/src/qts/data/validation_report.py:36`
  - 说明：One validation issue for a bar sequence.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.validation_report.DataValidationReport`
  - 类型：`class`
  - 位置：`backend/src/qts/data/validation_report.py:45`
  - 说明：Validation result for a bar sequence.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.data.validation_report.DataValidationReport.valid`
  - 类型：`property`
  - 位置：`backend/src/qts/data/validation_report.py:51`
  - 说明：Perform valid.
  - 直接调用：`any`
  - 可解析内部调用：无
- `qts.data.validation_report.DataValidationReport.max_severity`
  - 类型：`property`
  - 位置：`backend/src/qts/data/validation_report.py:56`
  - 说明：Perform max_severity.
  - 直接调用：`max`
  - 可解析内部调用：无
- `qts.data.validation_report.validate_bars`
  - 类型：`module_function`
  - 位置：`backend/src/qts/data/validation_report.py:68`
  - 说明：Validate bar ordering, overlap, and optional session containment.
  - 直接调用：`DataValidationIssue`, `DataValidationReport`, `ValueError`, `_append_ohlc_issue`, `bar.start_time.isoformat`, `int`, `issues.append`, `previous.end_time.isoformat`, `session_interval.contains`, `sorted`, `timedelta`, `tuple`
  - 可解析内部调用：`qts.core.time.TimeInterval.contains`, `qts.data.validation_report.DataValidationIssue`, `qts.data.validation_report.DataValidationReport`, `qts.data.validation_report._append_ohlc_issue`, `qts.indicators.rolling.RollingWindow.append`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`
- `qts.data.validation_report._append_ohlc_issue`
  - 类型：`module_function`
  - 位置：`backend/src/qts/data/validation_report.py:145`
  - 说明：Perform _append_ohlc_issue.
  - 直接调用：`DataValidationIssue`, `bar.start_time.isoformat`, `issues.append`, `max`, `min`
  - 可解析内部调用：`qts.data.validation_report.DataValidationIssue`, `qts.indicators.rolling.RollingWindow.append`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`

### `backend/src/qts/domain/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/domain/events/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/domain/events/event.py`

- `qts.domain.events.event.BaseEvent`
  - 类型：`class`
  - 位置：`backend/src/qts/domain/events/event.py:13`
  - 说明：Minimal event envelope used for traceable internal messages.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.domain.events.event.BaseEvent.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/domain/events/event.py:24`
  - 说明：Perform __post_init__.
  - 直接调用：`ValueError`, `require_aware_datetime`, `self.event_type.strip`, `self.partition_key.strip`, `self.source.strip`
  - 可解析内部调用：`qts.core.time.require_aware_datetime`

### `backend/src/qts/domain/events/metadata.py`

- `qts.domain.events.metadata.EventMetadata`
  - 类型：`class`
  - 位置：`backend/src/qts/domain/events/metadata.py:21`
  - 说明：Trace metadata carried by platform events.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.domain.events.metadata.EventMetadata.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/domain/events/metadata.py:39`
  - 说明：Perform __post_init__.
  - 直接调用：`ValueError`, `require_aware_datetime`, `self.event_type.strip`, `self.partition_key.strip`
  - 可解析内部调用：`qts.core.time.require_aware_datetime`

### `backend/src/qts/domain/instruments/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/domain/instruments/contract_spec.py`

- `qts.domain.instruments.contract_spec.SettlementType`
  - 类型：`class`
  - 位置：`backend/src/qts/domain/instruments/contract_spec.py:10`
  - 说明：How a contract settles.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.domain.instruments.contract_spec.ContractSpec`
  - 类型：`class`
  - 位置：`backend/src/qts/domain/instruments/contract_spec.py:18`
  - 说明：Trading contract metadata required for valuation and order sizing.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.domain.instruments.contract_spec.ContractSpec.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/domain/instruments/contract_spec.py:27`
  - 说明：Perform __post_init__.
  - 直接调用：`ValueError`, `self._require_positive`, `self.calendar_id.strip`
  - 可解析内部调用：`qts.domain.instruments.contract_spec.ContractSpec._require_positive`
- `qts.domain.instruments.contract_spec.ContractSpec._require_positive`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/domain/instruments/contract_spec.py:36`
  - 说明：Perform _require_positive.
  - 直接调用：`Decimal`, `ValueError`
  - 可解析内部调用：无

### `backend/src/qts/domain/instruments/derivative_spec.py`

- `qts.domain.instruments.derivative_spec.OptionRight`
  - 类型：`class`
  - 位置：`backend/src/qts/domain/instruments/derivative_spec.py:13`
  - 说明：Option payoff direction.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.domain.instruments.derivative_spec.ExerciseStyle`
  - 类型：`class`
  - 位置：`backend/src/qts/domain/instruments/derivative_spec.py:20`
  - 说明：Option exercise style.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.domain.instruments.derivative_spec.DerivativeSpec`
  - 类型：`class`
  - 位置：`backend/src/qts/domain/instruments/derivative_spec.py:28`
  - 说明：Common derivative metadata.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.domain.instruments.derivative_spec.FutureSpec`
  - 类型：`class`
  - 位置：`backend/src/qts/domain/instruments/derivative_spec.py:36`
  - 说明：Future contract metadata.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.domain.instruments.derivative_spec.FutureSpec.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/domain/instruments/derivative_spec.py:41`
  - 说明：Perform __post_init__.
  - 直接调用：`ValueError`, `self.root_symbol.strip`
  - 可解析内部调用：无
- `qts.domain.instruments.derivative_spec.OptionSpec`
  - 类型：`class`
  - 位置：`backend/src/qts/domain/instruments/derivative_spec.py:48`
  - 说明：Option contract metadata.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.domain.instruments.derivative_spec.OptionSpec.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/domain/instruments/derivative_spec.py:55`
  - 说明：Perform __post_init__.
  - 直接调用：`Decimal`, `ValueError`
  - 可解析内部调用：无

### `backend/src/qts/domain/instruments/instrument.py`

- `qts.domain.instruments.instrument.AssetClass`
  - 类型：`class`
  - 位置：`backend/src/qts/domain/instruments/instrument.py:19`
  - 说明：Supported instrument asset classes.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.domain.instruments.instrument.Instrument`
  - 类型：`class`
  - 位置：`backend/src/qts/domain/instruments/instrument.py:28`
  - 说明：Tradable instrument identified by a stable internal InstrumentId.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.domain.instruments.instrument.Instrument.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/domain/instruments/instrument.py:39`
  - 说明：Perform __post_init__.
  - 直接调用：`ValueError`, `isinstance`, `self.currency.strip`, `self.exchange.strip`
  - 可解析内部调用：无

### `backend/src/qts/domain/market_data/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/domain/market_data/bar.py`

- `qts.domain.market_data.bar.Bar`
  - 类型：`class`
  - 位置：`backend/src/qts/domain/market_data/bar.py:14`
  - 说明：OHLCV bar over a half-open interval.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.domain.market_data.bar.Bar.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/domain/market_data/bar.py:33`
  - 说明：Perform __post_init__.
  - 直接调用：`TimeInterval`, `ValueError`, `max`, `min`, `self._require_non_negative`, `self.session_id.strip`, `self.timeframe.strip`
  - 可解析内部调用：`qts.core.time.TimeInterval`, `qts.domain.market_data.bar.Bar._require_non_negative`
- `qts.domain.market_data.bar.Bar.interval`
  - 类型：`property`
  - 位置：`backend/src/qts/domain/market_data/bar.py:55`
  - 说明：Perform interval.
  - 直接调用：`TimeInterval`
  - 可解析内部调用：`qts.core.time.TimeInterval`
- `qts.domain.market_data.bar.Bar._require_non_negative`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/domain/market_data/bar.py:60`
  - 说明：Perform _require_non_negative.
  - 直接调用：`Decimal`, `ValueError`
  - 可解析内部调用：无
- `qts.domain.market_data.bar.Quote`
  - 类型：`class`
  - 位置：`backend/src/qts/domain/market_data/bar.py:67`
  - 说明：Top-of-book quote.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.domain.market_data.bar.Quote.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/domain/market_data/bar.py:77`
  - 说明：Perform __post_init__.
  - 直接调用：`Bar._require_non_negative`, `ValueError`, `require_aware_datetime`
  - 可解析内部调用：`qts.core.time.require_aware_datetime`, `qts.domain.market_data.bar.Bar._require_non_negative`
- `qts.domain.market_data.bar.Quote.spread`
  - 类型：`property`
  - 位置：`backend/src/qts/domain/market_data/bar.py:86`
  - 说明：Perform spread.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.domain.market_data.bar.Tick`
  - 类型：`class`
  - 位置：`backend/src/qts/domain/market_data/bar.py:92`
  - 说明：Trade tick.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.domain.market_data.bar.Tick.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/domain/market_data/bar.py:100`
  - 说明：Perform __post_init__.
  - 直接调用：`Bar._require_non_negative`, `require_aware_datetime`
  - 可解析内部调用：`qts.core.time.require_aware_datetime`, `qts.domain.market_data.bar.Bar._require_non_negative`

### `backend/src/qts/domain/orders/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/domain/orders/value_objects.py`

- `qts.domain.orders.value_objects.OrderState`
  - 类型：`class`
  - 位置：`backend/src/qts/domain/orders/value_objects.py:12`
  - 说明：Execution lifecycle states for orders.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.domain.orders.value_objects.OrderSide`
  - 类型：`class`
  - 位置：`backend/src/qts/domain/orders/value_objects.py:26`
  - 说明：Order side.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.domain.orders.value_objects.OrderIntent`
  - 类型：`class`
  - 位置：`backend/src/qts/domain/orders/value_objects.py:34`
  - 说明：Approved order instruction before broker submission.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.domain.orders.value_objects.OrderIntent.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/domain/orders/value_objects.py:42`
  - 说明：Perform __post_init__.
  - 直接调用：`Decimal`, `ValueError`
  - 可解析内部调用：无
- `qts.domain.orders.value_objects.CancelIntent`
  - 类型：`class`
  - 位置：`backend/src/qts/domain/orders/value_objects.py:49`
  - 说明：Intent to cancel an order through OrderManager.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.domain.orders.value_objects.ReplaceIntent`
  - 类型：`class`
  - 位置：`backend/src/qts/domain/orders/value_objects.py:57`
  - 说明：Intent to replace an order through OrderManager.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.domain.orders.value_objects.ReplaceIntent.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/domain/orders/value_objects.py:63`
  - 说明：Perform __post_init__.
  - 直接调用：`Decimal`, `ValueError`
  - 可解析内部调用：无
- `qts.domain.orders.value_objects.Order`
  - 类型：`class`
  - 位置：`backend/src/qts/domain/orders/value_objects.py:70`
  - 说明：Order snapshot owned by OrderManager.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.domain.orders.value_objects.ExecutionReportStatus`
  - 类型：`class`
  - 位置：`backend/src/qts/domain/orders/value_objects.py:79`
  - 说明：Normalized broker report status.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.domain.orders.value_objects.ExecutionReport`
  - 类型：`class`
  - 位置：`backend/src/qts/domain/orders/value_objects.py:90`
  - 说明：Normalized broker execution report.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.domain.orders.value_objects.ExecutionReport.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/domain/orders/value_objects.py:102`
  - 说明：Perform __post_init__.
  - 直接调用：`Decimal`, `ValueError`, `self.broker_order_id.strip`, `self.report_id.strip`
  - 可解析内部调用：无
- `qts.domain.orders.value_objects.OrderFill`
  - 类型：`class`
  - 位置：`backend/src/qts/domain/orders/value_objects.py:117`
  - 说明：OrderManager-validated fill event.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.domain.orders.value_objects.OrderManagerResult`
  - 类型：`class`
  - 位置：`backend/src/qts/domain/orders/value_objects.py:131`
  - 说明：Events emitted by processing an execution report.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.domain.orders.value_objects.OrderManagerSnapshot`
  - 类型：`class`
  - 位置：`backend/src/qts/domain/orders/value_objects.py:139`
  - 说明：Serializable OrderManager state for reconnect/recovery.
  - 直接调用：无
  - 可解析内部调用：无

### `backend/src/qts/domain/portfolio/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/domain/risk/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/domain/risk/decision.py`

- `qts.domain.risk.decision.RiskDecisionStatus`
  - 类型：`class`
  - 位置：`backend/src/qts/domain/risk/decision.py:10`
  - 说明：Risk check outcome.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.domain.risk.decision.RiskDecision`
  - 类型：`class`
  - 位置：`backend/src/qts/domain/risk/decision.py:19`
  - 说明：Explicit result of a risk check.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.domain.risk.decision.RiskDecision.approve`
  - 类型：`classmethod`
  - 位置：`backend/src/qts/domain/risk/decision.py:29`
  - 说明：Perform approve.
  - 直接调用：`cls`
  - 可解析内部调用：无
- `qts.domain.risk.decision.RiskDecision.rejected`
  - 类型：`classmethod`
  - 位置：`backend/src/qts/domain/risk/decision.py:39`
  - 说明：Perform rejected.
  - 直接调用：`ValueError`, `cls`, `reason.strip`, `reason_code.strip`
  - 可解析内部调用：无
- `qts.domain.risk.decision.RiskDecision.approved`
  - 类型：`property`
  - 位置：`backend/src/qts/domain/risk/decision.py:61`
  - 说明：Perform approved.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.domain.risk.decision.RiskDecision.reason_text`
  - 类型：`property`
  - 位置：`backend/src/qts/domain/risk/decision.py:66`
  - 说明：Perform reason_text.
  - 直接调用：无
  - 可解析内部调用：无

### `backend/src/qts/domain/risk/request.py`

- `qts.domain.risk.request.OrderRiskRequest`
  - 类型：`class`
  - 位置：`backend/src/qts/domain/risk/request.py:14`
  - 说明：Pre-trade risk input for a proposed order.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.domain.risk.request.OrderRiskRequest.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/domain/risk/request.py:23`
  - 说明：Perform __post_init__.
  - 直接调用：`Decimal`, `ValueError`, `require_aware_datetime`
  - 可解析内部调用：`qts.core.time.require_aware_datetime`
- `qts.domain.risk.request.OrderRiskRequest.notional`
  - 类型：`property`
  - 位置：`backend/src/qts/domain/risk/request.py:35`
  - 说明：Perform notional.
  - 直接调用：无
  - 可解析内部调用：无

### `backend/src/qts/execution/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/execution/adapters/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/execution/adapters/ibkr_order_execution.py`

- `qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionConnection`
  - 类型：`class`
  - 位置：`backend/src/qts/execution/adapters/ibkr_order_execution.py:15`
  - 说明：IBKR order execution connection settings.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionConnection.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/execution/adapters/ibkr_order_execution.py:24`
  - 说明：Perform __post_init__.
  - 直接调用：`ValueError`, `self.account_id.strip`, `self.host.strip`
  - 可解析内部调用：无
- `qts.execution.adapters.ibkr_order_execution.IbkrOrderRequest`
  - 类型：`class`
  - 位置：`backend/src/qts/execution/adapters/ibkr_order_execution.py:37`
  - 说明：IBKR order request produced at the adapter boundary.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.execution.adapters.ibkr_order_execution.IbkrExecutionReport`
  - 类型：`class`
  - 位置：`backend/src/qts/execution/adapters/ibkr_order_execution.py:48`
  - 说明：IBKR execution report shape before normalization.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionAdapter`
  - 类型：`class`
  - 位置：`backend/src/qts/execution/adapters/ibkr_order_execution.py:59`
  - 说明：Maps internal orders to IBKR order requests and normalizes reports.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionAdapter.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/execution/adapters/ibkr_order_execution.py:62`
  - 说明：Perform __init__.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionAdapter.to_order_request`
  - 类型：`method`
  - 位置：`backend/src/qts/execution/adapters/ibkr_order_execution.py:72`
  - 说明：Perform to_order_request.
  - 直接调用：`IbkrOrderRequest`, `self._symbol_mapping.to_broker_symbol`
  - 可解析内部调用：`qts.execution.adapters.ibkr_order_execution.IbkrOrderRequest`, `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.to_broker_symbol`
- `qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionAdapter.normalize_execution_report`
  - 类型：`method`
  - 位置：`backend/src/qts/execution/adapters/ibkr_order_execution.py:82`
  - 说明：Perform normalize_execution_report.
  - 直接调用：`ExecutionReport`, `normalize_broker_status`
  - 可解析内部调用：`qts.domain.orders.value_objects.ExecutionReport`, `qts.execution.broker.normalize_broker_status`

### `backend/src/qts/execution/broker.py`

- `qts.execution.broker.BrokerCapabilities`
  - 类型：`class`
  - 位置：`backend/src/qts/execution/broker.py:20`
  - 说明：Broker-supported live execution features.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.execution.broker.BrokerCapabilities.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/execution/broker.py:36`
  - 说明：Perform post init.
  - 直接调用：`Decimal`, `ValueError`, `any`, `item.strip`
  - 可解析内部调用：无
- `qts.execution.broker.BrokerCapabilities.supports_asset_class`
  - 类型：`method`
  - 位置：`backend/src/qts/execution/broker.py:42`
  - 说明：Perform supports_asset_class.
  - 直接调用：`ValueError`, `asset_class.strip`
  - 可解析内部调用：无
- `qts.execution.broker.BrokerCapabilities.supports_order_type`
  - 类型：`method`
  - 位置：`backend/src/qts/execution/broker.py:48`
  - 说明：Perform supports_order_type.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.execution.broker.BrokerCapabilities.supports_tif`
  - 类型：`method`
  - 位置：`backend/src/qts/execution/broker.py:58`
  - 说明：Perform supports_tif.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.execution.broker.BrokerOrderType`
  - 类型：`class`
  - 位置：`backend/src/qts/execution/broker.py:63`
  - 说明：Order types modeled before broker submission.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.execution.broker.TimeInForce`
  - 类型：`class`
  - 位置：`backend/src/qts/execution/broker.py:71`
  - 说明：Time-in-force values modeled at the execution boundary.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.execution.broker.BrokerOrderRequest`
  - 类型：`class`
  - 位置：`backend/src/qts/execution/broker.py:80`
  - 说明：Internal order request sent to the broker adapter boundary.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.execution.broker.BrokerOrderRequest.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/execution/broker.py:90`
  - 说明：Perform post init.
  - 直接调用：`Decimal`, `ValueError`
  - 可解析内部调用：无
- `qts.execution.broker.BrokerExecutionReportStatus`
  - 类型：`class`
  - 位置：`backend/src/qts/execution/broker.py:95`
  - 说明：Broker-boundary execution report status.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.execution.broker.BrokerExecutionReport`
  - 类型：`class`
  - 位置：`backend/src/qts/execution/broker.py:106`
  - 说明：Normalized broker callback before it reaches OrderManager.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.execution.broker.BrokerExecutionReport.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/execution/broker.py:121`
  - 说明：Perform post init.
  - 直接调用：`Decimal`, `ValueError`, `self.broker_order_id.strip`, `self.report_id.strip`
  - 可解析内部调用：无
- `qts.execution.broker.BrokerAdapter`
  - 类型：`class`
  - 位置：`backend/src/qts/execution/broker.py:132`
  - 说明：Stable broker execution boundary.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.execution.broker.BrokerAdapter.capabilities`
  - 类型：`property`
  - 位置：`backend/src/qts/execution/broker.py:136`
  - 说明：Return broker capabilities.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.execution.broker.BrokerAdapter.submit_order`
  - 类型：`method`
  - 位置：`backend/src/qts/execution/broker.py:140`
  - 说明：Submit an order request.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.execution.broker.BrokerAdapter.cancel_order`
  - 类型：`method`
  - 位置：`backend/src/qts/execution/broker.py:144`
  - 说明：Cancel an order by internal ID.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.execution.broker.FakeBrokerAdapter`
  - 类型：`class`
  - 位置：`backend/src/qts/execution/broker.py:149`
  - 说明：Deterministic fake broker for live-beta tests and local runs.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.execution.broker.FakeBrokerAdapter.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/execution/broker.py:152`
  - 说明：Perform init.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.execution.broker.FakeBrokerAdapter.capabilities`
  - 类型：`property`
  - 位置：`backend/src/qts/execution/broker.py:159`
  - 说明：Perform capabilities.
  - 直接调用：`BrokerCapabilities`
  - 可解析内部调用：`qts.execution.broker.BrokerCapabilities`
- `qts.execution.broker.FakeBrokerAdapter.submit_order`
  - 类型：`method`
  - 位置：`backend/src/qts/execution/broker.py:163`
  - 说明：Perform submit_order.
  - 直接调用：`len`, `self._broker_order_ids.setdefault`, `self._report`
  - 可解析内部调用：`qts.execution.broker.FakeBrokerAdapter._report`
- `qts.execution.broker.FakeBrokerAdapter.cancel_order`
  - 类型：`method`
  - 位置：`backend/src/qts/execution/broker.py:175`
  - 说明：Perform cancel_order.
  - 直接调用：`self._report`
  - 可解析内部调用：`qts.execution.broker.FakeBrokerAdapter._report`
- `qts.execution.broker.FakeBrokerAdapter.emit_fill`
  - 类型：`method`
  - 位置：`backend/src/qts/execution/broker.py:184`
  - 说明：Perform emit_fill.
  - 直接调用：`Decimal`, `ValueError`, `fill_id.strip`, `self._report`
  - 可解析内部调用：`qts.execution.broker.FakeBrokerAdapter._report`
- `qts.execution.broker.FakeBrokerAdapter._report`
  - 类型：`method`
  - 位置：`backend/src/qts/execution/broker.py:214`
  - 说明：Perform report.
  - 直接调用：`BrokerExecutionReport`, `Decimal`
  - 可解析内部调用：`qts.execution.broker.BrokerExecutionReport`
- `qts.execution.broker.normalize_broker_status`
  - 类型：`module_function`
  - 位置：`backend/src/qts/execution/broker.py:240`
  - 说明：Map broker status to normalized execution status.
  - 直接调用：`ExecutionReportStatus`
  - 可解析内部调用：`qts.domain.orders.value_objects.ExecutionReportStatus`
- `qts.execution.broker.normalize_broker_execution_report`
  - 类型：`module_function`
  - 位置：`backend/src/qts/execution/broker.py:246`
  - 说明：Convert broker-boundary report into the OrderManager report type.
  - 直接调用：`ExecutionReport`, `normalize_broker_status`
  - 可解析内部调用：`qts.domain.orders.value_objects.ExecutionReport`, `qts.execution.broker.normalize_broker_status`

### `backend/src/qts/execution/idempotency.py`

- `qts.execution.idempotency.FillIdempotencyStore`
  - 类型：`class`
  - 位置：`backend/src/qts/execution/idempotency.py:6`
  - 说明：Tracks fill IDs that have already been applied.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.execution.idempotency.FillIdempotencyStore.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/execution/idempotency.py:9`
  - 说明：Perform __init__.
  - 直接调用：`set`
  - 可解析内部调用：无
- `qts.execution.idempotency.FillIdempotencyStore.mark_seen`
  - 类型：`method`
  - 位置：`backend/src/qts/execution/idempotency.py:13`
  - 说明：Perform mark_seen.
  - 直接调用：`ValueError`, `fill_id.strip`, `self._seen.add`
  - 可解析内部调用：`qts.application.services.strategy_service.StrategyLifecycleService.add`
- `qts.execution.idempotency.FillIdempotencyStore.discard`
  - 类型：`method`
  - 位置：`backend/src/qts/execution/idempotency.py:22`
  - 说明：Perform discard.
  - 直接调用：`self._seen.discard`
  - 可解析内部调用：`qts.execution.idempotency.FillIdempotencyStore.discard`
- `qts.execution.idempotency.FillIdempotencyStore.snapshot`
  - 类型：`method`
  - 位置：`backend/src/qts/execution/idempotency.py:26`
  - 说明：Perform snapshot.
  - 直接调用：`sorted`, `tuple`
  - 可解析内部调用：无
- `qts.execution.idempotency.FillIdempotencyStore.restore`
  - 类型：`classmethod`
  - 位置：`backend/src/qts/execution/idempotency.py:31`
  - 说明：Perform restore.
  - 直接调用：`cls`, `set`
  - 可解析内部调用：无

### `backend/src/qts/execution/order_manager.py`

- `qts.execution.order_manager.OrderManager`
  - 类型：`class`
  - 位置：`backend/src/qts/execution/order_manager.py:28`
  - 说明：Owns order lifecycle and normalized execution reports.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.execution.order_manager.OrderManager.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/execution/order_manager.py:31`
  - 说明：Perform __init__.
  - 直接调用：`FillIdempotencyStore`
  - 可解析内部调用：`qts.execution.idempotency.FillIdempotencyStore`
- `qts.execution.order_manager.OrderManager.create_order`
  - 类型：`method`
  - 位置：`backend/src/qts/execution/order_manager.py:39`
  - 说明：Perform create_order.
  - 直接调用：`Order`, `OrderStateMachine`, `ValueError`
  - 可解析内部调用：`qts.domain.orders.value_objects.Order`, `qts.execution.order_state_machine.OrderStateMachine`
- `qts.execution.order_manager.OrderManager.mark_sent`
  - 类型：`method`
  - 位置：`backend/src/qts/execution/order_manager.py:49`
  - 说明：Perform mark_sent.
  - 直接调用：`ValueError`, `broker_order_id.strip`, `machine.apply`, `self._replace_order`
  - 可解析内部调用：`qts.execution.order_manager.OrderManager._replace_order`, `qts.execution.order_state_machine.OrderStateMachine.apply`, `qts.portfolio.accounting.fill_accounting.FillAccounting.apply`, `qts.runtime.live.LiveRuntimeStateMachine.apply`
- `qts.execution.order_manager.OrderManager.request_cancel`
  - 类型：`method`
  - 位置：`backend/src/qts/execution/order_manager.py:59`
  - 说明：Perform request_cancel.
  - 直接调用：`apply`, `self._replace_order`
  - 可解析内部调用：`qts.execution.order_manager.OrderManager._replace_order`, `qts.execution.order_state_machine.OrderStateMachine.apply`, `qts.portfolio.accounting.fill_accounting.FillAccounting.apply`, `qts.runtime.live.LiveRuntimeStateMachine.apply`
- `qts.execution.order_manager.OrderManager.request_replace`
  - 类型：`method`
  - 位置：`backend/src/qts/execution/order_manager.py:64`
  - 说明：Perform request_replace.
  - 直接调用：`Order`, `OrderIntent`, `ValueError`, `apply`
  - 可解析内部调用：`qts.domain.orders.value_objects.Order`, `qts.domain.orders.value_objects.OrderIntent`, `qts.execution.order_state_machine.OrderStateMachine.apply`, `qts.portfolio.accounting.fill_accounting.FillAccounting.apply`, `qts.runtime.live.LiveRuntimeStateMachine.apply`
- `qts.execution.order_manager.OrderManager.process_report`
  - 类型：`method`
  - 位置：`backend/src/qts/execution/order_manager.py:85`
  - 说明：Perform process_report.
  - 直接调用：`OrderManagerResult`, `apply`, `self._event_for_report`, `self._fills_for_report`, `self._replace_order`
  - 可解析内部调用：`qts.domain.orders.value_objects.OrderManagerResult`, `qts.execution.order_manager.OrderManager._event_for_report`, `qts.execution.order_manager.OrderManager._fills_for_report`, `qts.execution.order_manager.OrderManager._replace_order`, `qts.execution.order_state_machine.OrderStateMachine.apply`, `qts.portfolio.accounting.fill_accounting.FillAccounting.apply`, `qts.runtime.live.LiveRuntimeStateMachine.apply`
- `qts.execution.order_manager.OrderManager.get_order`
  - 类型：`method`
  - 位置：`backend/src/qts/execution/order_manager.py:93`
  - 说明：Perform get_order.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.execution.order_manager.OrderManager.discard_terminal_order`
  - 类型：`method`
  - 位置：`backend/src/qts/execution/order_manager.py:97`
  - 说明：Perform discard_terminal_order.
  - 直接调用：`ValueError`, `self._broker_to_order.pop`, `self._fill_ids.discard`, `self._fill_ids_by_order.pop`, `self._machines.pop`, `self._orders.pop`, `set`
  - 可解析内部调用：`qts.execution.idempotency.FillIdempotencyStore.discard`
- `qts.execution.order_manager.OrderManager.snapshot`
  - 类型：`method`
  - 位置：`backend/src/qts/execution/order_manager.py:109`
  - 说明：Perform snapshot.
  - 直接调用：`OrderManagerSnapshot`, `self._broker_to_order.items`, `self._fill_ids.snapshot`, `self._orders.values`, `tuple`
  - 可解析内部调用：`qts.application.services.interfaces.AccountService.snapshot`, `qts.domain.orders.value_objects.OrderManagerSnapshot`, `qts.execution.idempotency.FillIdempotencyStore.snapshot`, `qts.execution.order_manager.OrderManager.snapshot`, `qts.indicators.rolling.RollingWindow.snapshot`, `qts.observability.metrics.MetricsRegistry.snapshot`, `qts.portfolio.position_book.PositionBook.snapshot`, `qts.runtime.actors.account_actor.AccountActor.snapshot`
- `qts.execution.order_manager.OrderManager.restore`
  - 类型：`classmethod`
  - 位置：`backend/src/qts/execution/order_manager.py:118`
  - 说明：Perform restore.
  - 直接调用：`FillIdempotencyStore.restore`, `OrderStateMachine`, `cls`, `dict`
  - 可解析内部调用：`qts.execution.idempotency.FillIdempotencyStore.restore`, `qts.execution.order_state_machine.OrderStateMachine`
- `qts.execution.order_manager.OrderManager._replace_order`
  - 类型：`method`
  - 位置：`backend/src/qts/execution/order_manager.py:130`
  - 说明：Perform _replace_order.
  - 直接调用：`Order`
  - 可解析内部调用：`qts.domain.orders.value_objects.Order`
- `qts.execution.order_manager.OrderManager._fills_for_report`
  - 类型：`method`
  - 位置：`backend/src/qts/execution/order_manager.py:150`
  - 说明：Perform _fills_for_report.
  - 直接调用：`Decimal`, `OrderFill`, `ValueError`, `self._fill_ids.mark_seen`, `self._fill_ids_by_order.setdefault`, `self._fill_ids_by_order.setdefault.add`, `set`
  - 可解析内部调用：`qts.application.services.strategy_service.StrategyLifecycleService.add`, `qts.domain.orders.value_objects.OrderFill`, `qts.execution.idempotency.FillIdempotencyStore.mark_seen`
- `qts.execution.order_manager.OrderManager._event_for_report`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/execution/order_manager.py:173`
  - 说明：Perform _event_for_report.
  - 直接调用：无
  - 可解析内部调用：无

### `backend/src/qts/execution/order_state_machine.py`

- `qts.execution.order_state_machine.OrderEvent`
  - 类型：`class`
  - 位置：`backend/src/qts/execution/order_state_machine.py:11`
  - 说明：Order lifecycle transition inputs.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.execution.order_state_machine.OrderTransitionError`
  - 类型：`class`
  - 位置：`backend/src/qts/execution/order_state_machine.py:24`
  - 说明：Raised when an order transition is invalid.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.execution.order_state_machine.OrderStateMachine`
  - 类型：`class`
  - 位置：`backend/src/qts/execution/order_state_machine.py:81`
  - 说明：Validate and apply order lifecycle transitions.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.execution.order_state_machine.OrderStateMachine.apply`
  - 类型：`method`
  - 位置：`backend/src/qts/execution/order_state_machine.py:86`
  - 说明：Perform apply.
  - 直接调用：`OrderTransitionError`, `_DUPLICATE_TERMINAL_EVENTS.get`, `_TRANSITIONS.get`, `_TRANSITIONS.get.get`
  - 可解析内部调用：`qts.execution.order_state_machine.OrderTransitionError`, `qts.runtime.mailbox.Mailbox.get`

### `backend/src/qts/execution/simulator/__init__.py`

- `qts.execution.simulator.__getattr__`
  - 类型：`module_function`
  - 位置：`backend/src/qts/execution/simulator/__init__.py:7`
  - 说明：Lazily expose backtest-only adapter without importing backtest during runtime setup.
  - 直接调用：`AttributeError`
  - 可解析内部调用：无

### `backend/src/qts/execution/simulator/backtest_execution_adapter.py`

- `qts.execution.simulator.backtest_execution_adapter.BacktestExecutionAdapter`
  - 类型：`class`
  - 位置：`backend/src/qts/execution/simulator/backtest_execution_adapter.py:14`
  - 说明：Apply deterministic commission and slippage assumptions for backtests.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.execution.simulator.backtest_execution_adapter.BacktestExecutionAdapter.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/execution/simulator/backtest_execution_adapter.py:19`
  - 说明：Validate and normalize cost-model-backed configuration.
  - 直接调用：`ValueError`
  - 可解析内部调用：无
- `qts.execution.simulator.backtest_execution_adapter.BacktestExecutionAdapter.execute_market_order`
  - 类型：`method`
  - 位置：`backend/src/qts/execution/simulator/backtest_execution_adapter.py:24`
  - 说明：Execute a market order with cost-model adjustments.
  - 直接调用：`Decimal`, `ExecutionReport`, `ValueError`, `abs`
  - 可解析内部调用：`qts.domain.orders.value_objects.ExecutionReport`

### `backend/src/qts/execution/simulator/fill_model.py`

- `qts.execution.simulator.fill_model.ImmediateFillModel`
  - 类型：`class`
  - 位置：`backend/src/qts/execution/simulator/fill_model.py:10`
  - 说明：Fills market orders at the provided market price.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.execution.simulator.fill_model.ImmediateFillModel.fill`
  - 类型：`method`
  - 位置：`backend/src/qts/execution/simulator/fill_model.py:13`
  - 说明：Perform fill.
  - 直接调用：`Decimal`, `ExecutionReport`, `ValueError`
  - 可解析内部调用：`qts.domain.orders.value_objects.ExecutionReport`

### `backend/src/qts/execution/simulator/simulated_broker.py`

- `qts.execution.simulator.simulated_broker.SimulatedBroker`
  - 类型：`class`
  - 位置：`backend/src/qts/execution/simulator/simulated_broker.py:11`
  - 说明：Broker simulator with no external dependency.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.execution.simulator.simulated_broker.SimulatedBroker.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/execution/simulator/simulated_broker.py:14`
  - 说明：Perform __init__.
  - 直接调用：`ImmediateFillModel`
  - 可解析内部调用：`qts.execution.simulator.fill_model.ImmediateFillModel`
- `qts.execution.simulator.simulated_broker.SimulatedBroker.execute_market_order`
  - 类型：`method`
  - 位置：`backend/src/qts/execution/simulator/simulated_broker.py:18`
  - 说明：Perform execute_market_order.
  - 直接调用：`self._fill_model.fill`
  - 可解析内部调用：`qts.execution.simulator.fill_model.ImmediateFillModel.fill`

### `backend/src/qts/factors/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/factors/momentum.py`

- `qts.factors.momentum.FactorAsset`
  - 类型：`class`
  - 位置：`backend/src/qts/factors/momentum.py:10`
  - 说明：Minimal asset shape required by factor ranking.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.factors.momentum.FactorAsset.symbol`
  - 类型：`property`
  - 位置：`backend/src/qts/factors/momentum.py:14`
  - 说明：Stable display symbol used for deterministic tie-breaking.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.factors.momentum.FactorScore`
  - 类型：`class`
  - 位置：`backend/src/qts/factors/momentum.py:19`
  - 说明：Single asset factor score.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.factors.momentum.FactorResult`
  - 类型：`class`
  - 位置：`backend/src/qts/factors/momentum.py:27`
  - 说明：Ranked cross-sectional factor result.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.factors.momentum.FactorResult.score`
  - 类型：`method`
  - 位置：`backend/src/qts/factors/momentum.py:32`
  - 说明：Perform score.
  - 直接调用：`KeyError`
  - 可解析内部调用：无
- `qts.factors.momentum.MomentumFactor`
  - 类型：`class`
  - 位置：`backend/src/qts/factors/momentum.py:41`
  - 说明：Compute simple period momentum as last / first - 1.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.factors.momentum.MomentumFactor.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/factors/momentum.py:46`
  - 说明：Perform __post_init__.
  - 直接调用：`ValueError`
  - 可解析内部调用：无
- `qts.factors.momentum.MomentumFactor.compute`
  - 类型：`method`
  - 位置：`backend/src/qts/factors/momentum.py:51`
  - 说明：Perform compute.
  - 直接调用：`FactorResult`, `FactorScore`, `prices.items`, `self._momentum`, `sorted`, `tuple`
  - 可解析内部调用：`qts.factors.momentum.FactorResult`, `qts.factors.momentum.FactorScore`, `qts.factors.momentum.MomentumFactor._momentum`
- `qts.factors.momentum.MomentumFactor._momentum`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/factors/momentum.py:61`
  - 说明：Perform _momentum.
  - 直接调用：`Decimal`, `ValueError`, `len`
  - 可解析内部调用：无

### `backend/src/qts/indicators/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/indicators/price/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/indicators/price/ema.py`

- `qts.indicators.price.ema.EMA`
  - 类型：`class`
  - 位置：`backend/src/qts/indicators/price/ema.py:12`
  - 说明：Incremental EMA using SMA as the warmup seed.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.indicators.price.ema.EMA.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/indicators/price/ema.py:19`
  - 说明：Perform __post_init__.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.indicators.price.ema.EMA.ready`
  - 类型：`property`
  - 位置：`backend/src/qts/indicators/price/ema.py:24`
  - 说明：Perform ready.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.indicators.price.ema.EMA.update`
  - 类型：`method`
  - 位置：`backend/src/qts/indicators/price/ema.py:28`
  - 说明：Perform update.
  - 直接调用：`Decimal`, `self._warmup.append`, `sum`
  - 可解析内部调用：`qts.indicators.rolling.RollingWindow.append`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`

### `backend/src/qts/indicators/price/sma.py`

- `qts.indicators.price.sma.SMA`
  - 类型：`class`
  - 位置：`backend/src/qts/indicators/price/sma.py:12`
  - 说明：Incremental simple moving average.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.indicators.price.sma.SMA.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/indicators/price/sma.py:19`
  - 说明：Perform __post_init__.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.indicators.price.sma.SMA.ready`
  - 类型：`property`
  - 位置：`backend/src/qts/indicators/price/sma.py:24`
  - 说明：Perform ready.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.indicators.price.sma.SMA.update`
  - 类型：`method`
  - 位置：`backend/src/qts/indicators/price/sma.py:28`
  - 说明：Perform update.
  - 直接调用：`Decimal`, `self._values.append`, `sum`
  - 可解析内部调用：`qts.indicators.rolling.RollingWindow.append`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`

### `backend/src/qts/indicators/rolling.py`

- `qts.indicators.rolling.RollingWindow`
  - 类型：`class`
  - 位置：`backend/src/qts/indicators/rolling.py:14`
  - 说明：Bounded FIFO buffer with warmup state.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.indicators.rolling.RollingWindow.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/indicators/rolling.py:20`
  - 说明：Perform __post_init__.
  - 直接调用：`ValueError`, `deque`
  - 可解析内部调用：无
- `qts.indicators.rolling.RollingWindow.ready`
  - 类型：`property`
  - 位置：`backend/src/qts/indicators/rolling.py:27`
  - 说明：Perform ready.
  - 直接调用：`len`
  - 可解析内部调用：无
- `qts.indicators.rolling.RollingWindow.append`
  - 类型：`method`
  - 位置：`backend/src/qts/indicators/rolling.py:31`
  - 说明：Perform append.
  - 直接调用：`self._values.append`
  - 可解析内部调用：`qts.indicators.rolling.RollingWindow.append`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`
- `qts.indicators.rolling.RollingWindow.snapshot`
  - 类型：`method`
  - 位置：`backend/src/qts/indicators/rolling.py:35`
  - 说明：Perform snapshot.
  - 直接调用：`tuple`
  - 可解析内部调用：无
- `qts.indicators.rolling.RollingWindow.restore`
  - 类型：`method`
  - 位置：`backend/src/qts/indicators/rolling.py:39`
  - 说明：Perform restore.
  - 直接调用：`restored.append`
  - 可解析内部调用：`qts.indicators.rolling.RollingWindow.append`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`
- `qts.indicators.rolling.RollingWindow.__iter__`
  - 类型：`method`
  - 位置：`backend/src/qts/indicators/rolling.py:46`
  - 说明：Perform __iter__.
  - 直接调用：`iter`
  - 可解析内部调用：无
- `qts.indicators.rolling.RollingWindow.__len__`
  - 类型：`method`
  - 位置：`backend/src/qts/indicators/rolling.py:50`
  - 说明：Perform __len__.
  - 直接调用：`len`
  - 可解析内部调用：无

### `backend/src/qts/load/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/load/bootstrap.py`

- `qts.load.bootstrap.bootstrap_local`
  - 类型：`module_function`
  - 位置：`backend/src/qts/load/bootstrap.py:8`
  - 说明：Create local runtime directories and marker files safely.
  - 直接调用：`data_dir.mkdir`, `logs_dir.mkdir`, `marker.write_text`, `root.mkdir`, `str`
  - 可解析内部调用：无

### `backend/src/qts/load/synthetic_market_data.py`

- `qts.load.synthetic_market_data.SyntheticMarketDataConfig`
  - 类型：`class`
  - 位置：`backend/src/qts/load/synthetic_market_data.py:14`
  - 说明：Configuration for deterministic synthetic market data.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.load.synthetic_market_data.SyntheticMarketDataConfig.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/load/synthetic_market_data.py:25`
  - 说明：Perform post init.
  - 直接调用：`ValueError`, `self.session_id.strip`, `self.timeframe.strip`
  - 可解析内部调用：无
- `qts.load.synthetic_market_data.generate_bars`
  - 类型：`module_function`
  - 位置：`backend/src/qts/load/synthetic_market_data.py:34`
  - 说明：Perform generate_bars.
  - 直接调用：`Bar`, `Decimal`, `bars.append`, `max`, `min`, `range`, `timedelta`, `tuple`
  - 可解析内部调用：`qts.domain.market_data.bar.Bar`, `qts.indicators.rolling.RollingWindow.append`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`

### `backend/src/qts/observability/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/observability/audit.py`

- `qts.observability.audit.AuditEvent`
  - 类型：`class`
  - 位置：`backend/src/qts/observability/audit.py:10`
  - 说明：Operational or trading audit event.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.observability.audit.AuditEvent.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/observability/audit.py:19`
  - 说明：Perform __post_init__.
  - 直接调用：`ValueError`, `self.actor.strip`, `self.event_type.strip`, `self.message.strip`
  - 可解析内部调用：无

### `backend/src/qts/observability/logging.py`

- `qts.observability.logging.build_log_record`
  - 类型：`module_function`
  - 位置：`backend/src/qts/observability/logging.py:14`
  - 说明：Build a structured log record without exposing secret values.
  - 直接调用：`ValueError`, `_is_secret_key`, `_metadata_fields`, `fields.items`, `key.strip`, `level.strip`, `message.strip`, `record.update`
  - 可解析内部调用：`qts.backtest.report.StreamingEquityMetrics.update`, `qts.data.bars.aggregator.BarAggregator.update`, `qts.indicators.price.ema.EMA.update`, `qts.indicators.price.sma.SMA.update`, `qts.observability.logging._is_secret_key`, `qts.observability.logging._metadata_fields`, `qts.strategy_sdk.indicators.AssetIndicator.update`
- `qts.observability.logging._metadata_fields`
  - 类型：`module_function`
  - 位置：`backend/src/qts/observability/logging.py:42`
  - 说明：Perform _metadata_fields.
  - 直接调用：`metadata.bar_time.isoformat`, `metadata.event_time.isoformat`, `optional.items`, `str`
  - 可解析内部调用：无
- `qts.observability.logging._is_secret_key`
  - 类型：`module_function`
  - 位置：`backend/src/qts/observability/logging.py:68`
  - 说明：Perform _is_secret_key.
  - 直接调用：`any`, `key.lower`
  - 可解析内部调用：无

### `backend/src/qts/observability/metrics.py`

- `qts.observability.metrics.MetricsRegistry`
  - 类型：`class`
  - 位置：`backend/src/qts/observability/metrics.py:10`
  - 说明：Record counters and gauges with deterministic key formatting.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.observability.metrics.MetricsRegistry.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/observability/metrics.py:13`
  - 说明：Perform __init__.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.observability.metrics.MetricsRegistry.increment`
  - 类型：`method`
  - 位置：`backend/src/qts/observability/metrics.py:17`
  - 说明：Perform increment.
  - 直接调用：`int`, `self._metric_key`, `self._values.get`
  - 可解析内部调用：`qts.observability.metrics.MetricsRegistry._metric_key`, `qts.runtime.mailbox.Mailbox.get`
- `qts.observability.metrics.MetricsRegistry.gauge`
  - 类型：`method`
  - 位置：`backend/src/qts/observability/metrics.py:28`
  - 说明：Perform gauge.
  - 直接调用：`self._metric_key`
  - 可解析内部调用：`qts.observability.metrics.MetricsRegistry._metric_key`
- `qts.observability.metrics.MetricsRegistry.observe_queue`
  - 类型：`method`
  - 位置：`backend/src/qts/observability/metrics.py:34`
  - 说明：Perform observe_queue.
  - 直接调用：`self.gauge`
  - 可解析内部调用：`qts.observability.metrics.MetricsRegistry.gauge`
- `qts.observability.metrics.MetricsRegistry.snapshot`
  - 类型：`method`
  - 位置：`backend/src/qts/observability/metrics.py:49`
  - 说明：Perform snapshot.
  - 直接调用：`dict`, `self._values.items`, `sorted`
  - 可解析内部调用：无
- `qts.observability.metrics.MetricsRegistry._metric_key`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/observability/metrics.py:54`
  - 说明：Perform _metric_key.
  - 直接调用：`ValueError`, `join`, `name.strip`, `sorted`
  - 可解析内部调用：无

### `backend/src/qts/portfolio/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/portfolio/accounting/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/portfolio/accounting/fill_accounting.py`

- `qts.portfolio.accounting.fill_accounting.TradeSide`
  - 类型：`class`
  - 位置：`backend/src/qts/portfolio/accounting/fill_accounting.py:14`
  - 说明：Fill side.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.portfolio.accounting.fill_accounting.Fill`
  - 类型：`class`
  - 位置：`backend/src/qts/portfolio/accounting/fill_accounting.py:22`
  - 说明：Executed fill used by accounting.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.portfolio.accounting.fill_accounting.Fill.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/portfolio/accounting/fill_accounting.py:33`
  - 说明：Perform __post_init__.
  - 直接调用：`Decimal`, `ValueError`, `self.currency.strip`
  - 可解析内部调用：无
- `qts.portfolio.accounting.fill_accounting.FillAccounting`
  - 类型：`class`
  - 位置：`backend/src/qts/portfolio/accounting/fill_accounting.py:45`
  - 说明：Fill accounting operations.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.portfolio.accounting.fill_accounting.FillAccounting.apply`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/portfolio/accounting/fill_accounting.py:49`
  - 说明：Perform apply.
  - 直接调用：`cash_book.apply_delta`, `position_book.apply_delta`
  - 可解析内部调用：`qts.portfolio.cash_book.CashBook.apply_delta`, `qts.portfolio.position_book.PositionBook.apply_delta`

### `backend/src/qts/portfolio/cash_book.py`

- `qts.portfolio.cash_book.CashBook`
  - 类型：`class`
  - 位置：`backend/src/qts/portfolio/cash_book.py:11`
  - 说明：Mutable cash balance book intended to be owned by AccountActor later.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.portfolio.cash_book.CashBook.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/portfolio/cash_book.py:14`
  - 说明：Perform __init__.
  - 直接调用：`dict`
  - 可解析内部调用：无
- `qts.portfolio.cash_book.CashBook.apply_delta`
  - 类型：`method`
  - 位置：`backend/src/qts/portfolio/cash_book.py:18`
  - 说明：Perform apply_delta.
  - 直接调用：`self._normalize_currency`, `self.balance`
  - 可解析内部调用：`qts.portfolio.cash_book.CashBook._normalize_currency`, `qts.portfolio.cash_book.CashBook.balance`, `qts.portfolio.reservation_book.ReservationBook._normalize_currency`
- `qts.portfolio.cash_book.CashBook.balance`
  - 类型：`method`
  - 位置：`backend/src/qts/portfolio/cash_book.py:23`
  - 说明：Perform balance.
  - 直接调用：`Decimal`, `self._balances.get`, `self._normalize_currency`
  - 可解析内部调用：`qts.portfolio.cash_book.CashBook._normalize_currency`, `qts.portfolio.reservation_book.ReservationBook._normalize_currency`, `qts.runtime.mailbox.Mailbox.get`
- `qts.portfolio.cash_book.CashBook.available`
  - 类型：`method`
  - 位置：`backend/src/qts/portfolio/cash_book.py:27`
  - 说明：Perform available.
  - 直接调用：`reservations.reserved`, `self._normalize_currency`, `self.balance`
  - 可解析内部调用：`qts.portfolio.cash_book.CashBook._normalize_currency`, `qts.portfolio.cash_book.CashBook.balance`, `qts.portfolio.reservation_book.ReservationBook._normalize_currency`, `qts.portfolio.reservation_book.ReservationBook.reserved`
- `qts.portfolio.cash_book.CashBook._normalize_currency`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/portfolio/cash_book.py:33`
  - 说明：Perform _normalize_currency.
  - 直接调用：`ValueError`, `currency.strip`, `currency.strip.upper`
  - 可解析内部调用：无

### `backend/src/qts/portfolio/position_book.py`

- `qts.portfolio.position_book.Position`
  - 类型：`class`
  - 位置：`backend/src/qts/portfolio/position_book.py:14`
  - 说明：Immutable position snapshot.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.portfolio.position_book.PositionBook`
  - 类型：`class`
  - 位置：`backend/src/qts/portfolio/position_book.py:21`
  - 说明：Mutable position book intended to be owned by AccountActor later.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.portfolio.position_book.PositionBook.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/portfolio/position_book.py:24`
  - 说明：Perform __init__.
  - 直接调用：`dict`
  - 可解析内部调用：无
- `qts.portfolio.position_book.PositionBook.apply_delta`
  - 类型：`method`
  - 位置：`backend/src/qts/portfolio/position_book.py:28`
  - 说明：Perform apply_delta.
  - 直接调用：`self.quantity`
  - 可解析内部调用：`qts.portfolio.position_book.PositionBook.quantity`
- `qts.portfolio.position_book.PositionBook.quantity`
  - 类型：`method`
  - 位置：`backend/src/qts/portfolio/position_book.py:32`
  - 说明：Perform quantity.
  - 直接调用：`Decimal`, `self._positions.get`
  - 可解析内部调用：`qts.runtime.mailbox.Mailbox.get`
- `qts.portfolio.position_book.PositionBook.snapshot`
  - 类型：`method`
  - 位置：`backend/src/qts/portfolio/position_book.py:36`
  - 说明：Perform snapshot.
  - 直接调用：`MappingProxyType`, `Position`, `self._positions.items`
  - 可解析内部调用：`qts.portfolio.position_book.Position`

### `backend/src/qts/portfolio/reservation_book.py`

- `qts.portfolio.reservation_book.Reservation`
  - 类型：`class`
  - 位置：`backend/src/qts/portfolio/reservation_book.py:12`
  - 说明：Cash reservation by order ID.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.portfolio.reservation_book.ReservationBook`
  - 类型：`class`
  - 位置：`backend/src/qts/portfolio/reservation_book.py:20`
  - 说明：Idempotent cash reservations keyed by order ID.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.portfolio.reservation_book.ReservationBook.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/portfolio/reservation_book.py:23`
  - 说明：Perform __init__.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.portfolio.reservation_book.ReservationBook.reserve`
  - 类型：`method`
  - 位置：`backend/src/qts/portfolio/reservation_book.py:27`
  - 说明：Perform reserve.
  - 直接调用：`Decimal`, `Reservation`, `ValueError`, `self._normalize_currency`
  - 可解析内部调用：`qts.portfolio.cash_book.CashBook._normalize_currency`, `qts.portfolio.reservation_book.Reservation`, `qts.portfolio.reservation_book.ReservationBook._normalize_currency`
- `qts.portfolio.reservation_book.ReservationBook.release`
  - 类型：`method`
  - 位置：`backend/src/qts/portfolio/reservation_book.py:40`
  - 说明：Perform release.
  - 直接调用：`self._reservations.pop`
  - 可解析内部调用：无
- `qts.portfolio.reservation_book.ReservationBook.reserved`
  - 类型：`method`
  - 位置：`backend/src/qts/portfolio/reservation_book.py:44`
  - 说明：Perform reserved.
  - 直接调用：`Decimal`, `self._normalize_currency`, `self._reservations.values`, `sum`
  - 可解析内部调用：`qts.portfolio.cash_book.CashBook._normalize_currency`, `qts.portfolio.reservation_book.ReservationBook._normalize_currency`
- `qts.portfolio.reservation_book.ReservationBook._normalize_currency`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/portfolio/reservation_book.py:57`
  - 说明：Perform _normalize_currency.
  - 直接调用：`ValueError`, `currency.strip`, `currency.strip.upper`
  - 可解析内部调用：无

### `backend/src/qts/portfolio/valuation/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/portfolio/valuation/models.py`

- `qts.portfolio.valuation.models.equity_notional`
  - 类型：`module_function`
  - 位置：`backend/src/qts/portfolio/valuation/models.py:8`
  - 说明：Perform equity_notional.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.portfolio.valuation.models.future_pnl`
  - 类型：`module_function`
  - 位置：`backend/src/qts/portfolio/valuation/models.py:13`
  - 说明：Perform future_pnl.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.portfolio.valuation.models.option_premium_value`
  - 类型：`module_function`
  - 位置：`backend/src/qts/portfolio/valuation/models.py:24`
  - 说明：Perform option_premium_value.
  - 直接调用：无
  - 可解析内部调用：无

### `backend/src/qts/quality/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/quality/guardrails.py`

- `qts.quality.guardrails.GuardrailViolation`
  - 类型：`class`
  - 位置：`backend/src/qts/quality/guardrails.py:118`
  - 说明：One architecture or domain-boundary guardrail violation.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.quality.guardrails.GuardrailViolation.format`
  - 类型：`method`
  - 位置：`backend/src/qts/quality/guardrails.py:126`
  - 说明：Perform format.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.quality.guardrails.Rule`
  - 类型：`class`
  - 位置：`backend/src/qts/quality/guardrails.py:131`
  - 说明：Pluggable guardrail rule interface.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.quality.guardrails.Rule.check`
  - 类型：`method`
  - 位置：`backend/src/qts/quality/guardrails.py:136`
  - 说明：Perform check.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.quality.guardrails.ImportBoundaryRule`
  - 类型：`class`
  - 位置：`backend/src/qts/quality/guardrails.py:150`
  - 说明：Validate package import boundary direction and adapter constraints.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.quality.guardrails.ImportBoundaryRule.check`
  - 类型：`method`
  - 位置：`backend/src/qts/quality/guardrails.py:155`
  - 说明：Perform check.
  - 直接调用：`_check_import`, `_iter_imports`, `violations.extend`
  - 可解析内部调用：`qts.quality.guardrails._check_import`, `qts.quality.guardrails._iter_imports`
- `qts.quality.guardrails.ProductSpecificRule`
  - 类型：`class`
  - 位置：`backend/src/qts/quality/guardrails.py:171`
  - 说明：Reject product hard-coding outside documented locations.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.quality.guardrails.ProductSpecificRule.check`
  - 类型：`method`
  - 位置：`backend/src/qts/quality/guardrails.py:176`
  - 说明：Perform check.
  - 直接调用：`_check_product_specific_code`, `_has_allowed_prefix`
  - 可解析内部调用：`qts.quality.guardrails._check_product_specific_code`, `qts.quality.guardrails._has_allowed_prefix`
- `qts.quality.guardrails.BrokerSpecificRule`
  - 类型：`class`
  - 位置：`backend/src/qts/quality/guardrails.py:189`
  - 说明：Reject broker hard-coding outside broker boundaries.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.quality.guardrails.BrokerSpecificRule.check`
  - 类型：`method`
  - 位置：`backend/src/qts/quality/guardrails.py:194`
  - 说明：Perform check.
  - 直接调用：`_check_broker_specific_code`, `_has_allowed_prefix`
  - 可解析内部调用：`qts.quality.guardrails._check_broker_specific_code`, `qts.quality.guardrails._has_allowed_prefix`
- `qts.quality.guardrails.TestSupportRule`
  - 类型：`class`
  - 位置：`backend/src/qts/quality/guardrails.py:207`
  - 说明：Reject test/anchor support in production source.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.quality.guardrails.TestSupportRule.check`
  - 类型：`method`
  - 位置：`backend/src/qts/quality/guardrails.py:212`
  - 说明：Perform check.
  - 直接调用：`_check_test_support_code`
  - 可解析内部调用：`qts.quality.guardrails._check_test_support_code`
- `qts.quality.guardrails.SharedCapabilityRule`
  - 类型：`class`
  - 位置：`backend/src/qts/quality/guardrails.py:223`
  - 说明：Reject shared capability semantics in source-specific modules.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.quality.guardrails.SharedCapabilityRule.check`
  - 类型：`method`
  - 位置：`backend/src/qts/quality/guardrails.py:228`
  - 说明：Perform check.
  - 直接调用：`_check_shared_capability_placement`
  - 可解析内部调用：`qts.quality.guardrails._check_shared_capability_placement`
- `qts.quality.guardrails.OOPPublicFactoryRule`
  - 类型：`class`
  - 位置：`backend/src/qts/quality/guardrails.py:239`
  - 说明：Reject module-level public factory names on stable concepts.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.quality.guardrails.OOPPublicFactoryRule.check`
  - 类型：`method`
  - 位置：`backend/src/qts/quality/guardrails.py:244`
  - 说明：Perform check.
  - 直接调用：`_check_oop_public_factory_functions`
  - 可解析内部调用：`qts.quality.guardrails._check_oop_public_factory_functions`
- `qts.quality.guardrails.OOPHelperOwnershipRule`
  - 类型：`class`
  - 位置：`backend/src/qts/quality/guardrails.py:255`
  - 说明：Reject helper ownership violations that should stay private.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.quality.guardrails.OOPHelperOwnershipRule.check`
  - 类型：`method`
  - 位置：`backend/src/qts/quality/guardrails.py:260`
  - 说明：Perform check.
  - 直接调用：`_check_oop_helper_ownership`
  - 可解析内部调用：`qts.quality.guardrails._check_oop_helper_ownership`
- `qts.quality.guardrails.BacktestRunnerCohesionRule`
  - 类型：`class`
  - 位置：`backend/src/qts/quality/guardrails.py:271`
  - 说明：Reject replay input assembly inside backtest runner.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.quality.guardrails.BacktestRunnerCohesionRule.check`
  - 类型：`method`
  - 位置：`backend/src/qts/quality/guardrails.py:276`
  - 说明：Perform check.
  - 直接调用：`_check_backtest_runner_cohesion`
  - 可解析内部调用：`qts.quality.guardrails._check_backtest_runner_cohesion`
- `qts.quality.guardrails.BacktestInputCohesionRule`
  - 类型：`class`
  - 位置：`backend/src/qts/quality/guardrails.py:287`
  - 说明：Reject catalog/data construction inside backtest input builder.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.quality.guardrails.BacktestInputCohesionRule.check`
  - 类型：`method`
  - 位置：`backend/src/qts/quality/guardrails.py:292`
  - 说明：Perform check.
  - 直接调用：`_check_backtest_input_cohesion`
  - 可解析内部调用：`qts.quality.guardrails._check_backtest_input_cohesion`
- `qts.quality.guardrails.BacktestEngineCohesionRule`
  - 类型：`class`
  - 位置：`backend/src/qts/quality/guardrails.py:303`
  - 说明：Reject historical replay assembly inside backtest engine.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.quality.guardrails.BacktestEngineCohesionRule.check`
  - 类型：`method`
  - 位置：`backend/src/qts/quality/guardrails.py:308`
  - 说明：Perform check.
  - 直接调用：`_check_backtest_engine_cohesion`
  - 可解析内部调用：`qts.quality.guardrails._check_backtest_engine_cohesion`
- `qts.quality.guardrails.StrategySdkPublicSurfaceRule`
  - 类型：`class`
  - 位置：`backend/src/qts/quality/guardrails.py:319`
  - 说明：Reject internal runtime/broker/risk symbols from strategy SDK modules.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.quality.guardrails.StrategySdkPublicSurfaceRule.check`
  - 类型：`method`
  - 位置：`backend/src/qts/quality/guardrails.py:324`
  - 说明：Perform check.
  - 直接调用：`_check_strategy_sdk_internal_leak`
  - 可解析内部调用：`qts.quality.guardrails._check_strategy_sdk_internal_leak`
- `qts.quality.guardrails.GuardrailSuite`
  - 类型：`class`
  - 位置：`backend/src/qts/quality/guardrails.py:335`
  - 说明：Execute a configured set of guardrail rules against Python files.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.quality.guardrails.GuardrailSuite.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/quality/guardrails.py:338`
  - 说明：Perform init.
  - 直接调用：`BacktestEngineCohesionRule`, `BacktestInputCohesionRule`, `BacktestRunnerCohesionRule`, `BrokerSpecificRule`, `ImportBoundaryRule`, `OOPHelperOwnershipRule`, `OOPPublicFactoryRule`, `ProductSpecificRule`, `SharedCapabilityRule`, `StrategySdkPublicSurfaceRule`, `TestSupportRule`
  - 可解析内部调用：`qts.quality.guardrails.BacktestEngineCohesionRule`, `qts.quality.guardrails.BacktestInputCohesionRule`, `qts.quality.guardrails.BacktestRunnerCohesionRule`, `qts.quality.guardrails.BrokerSpecificRule`, `qts.quality.guardrails.ImportBoundaryRule`, `qts.quality.guardrails.OOPHelperOwnershipRule`, `qts.quality.guardrails.OOPPublicFactoryRule`, `qts.quality.guardrails.ProductSpecificRule`, `qts.quality.guardrails.SharedCapabilityRule`, `qts.quality.guardrails.StrategySdkPublicSurfaceRule`, `qts.quality.guardrails.TestSupportRule`
- `qts.quality.guardrails.GuardrailSuite.check_file`
  - 类型：`method`
  - 位置：`backend/src/qts/quality/guardrails.py:353`
  - 说明：Perform check_file.
  - 直接调用：`rule.check`, `violations.extend`
  - 可解析内部调用：`qts.quality.guardrails.BacktestEngineCohesionRule.check`, `qts.quality.guardrails.BacktestInputCohesionRule.check`, `qts.quality.guardrails.BacktestRunnerCohesionRule.check`, `qts.quality.guardrails.BrokerSpecificRule.check`, `qts.quality.guardrails.GuardrailSuite.check`, `qts.quality.guardrails.ImportBoundaryRule.check`, `qts.quality.guardrails.OOPHelperOwnershipRule.check`, `qts.quality.guardrails.OOPPublicFactoryRule.check`, `qts.quality.guardrails.ProductSpecificRule.check`, `qts.quality.guardrails.Rule.check`, `qts.quality.guardrails.SharedCapabilityRule.check`, `qts.quality.guardrails.StrategySdkPublicSurfaceRule.check`, `qts.quality.guardrails.TestSupportRule.check`, `qts.risk.risk_engine.RiskEngine.check`, `qts.risk.rule.RiskRule.check`, `qts.risk.rules.max_notional.MaxNotionalRule.check`, `qts.risk.rules.max_order_qty.MaxOrderQuantityRule.check`, `qts.risk.rules.trading_session_rule.TradingSessionRule.check`
- `qts.quality.guardrails.GuardrailSuite.check`
  - 类型：`method`
  - 位置：`backend/src/qts/quality/guardrails.py:372`
  - 说明：Perform check.
  - 直接调用：`_check_python_file`, `sorted`, `source_root.exists`, `source_root.rglob`, `violations.extend`
  - 可解析内部调用：`qts.quality.guardrails._check_python_file`
- `qts.quality.guardrails.run_guardrails`
  - 类型：`module_function`
  - 位置：`backend/src/qts/quality/guardrails.py:386`
  - 说明：Return all guardrail violations under the repository root.
  - 直接调用：`GuardrailSuite`, `GuardrailSuite.check`
  - 可解析内部调用：`qts.quality.guardrails.GuardrailSuite`, `qts.quality.guardrails.GuardrailSuite.check`
- `qts.quality.guardrails._check_python_file`
  - 类型：`module_function`
  - 位置：`backend/src/qts/quality/guardrails.py:391`
  - 说明：Perform check python file.
  - 直接调用：`GuardrailSuite`, `GuardrailSuite.check_file`, `ast.parse`, `path.read_text`, `path.relative_to`, `str`
  - 可解析内部调用：`qts.data.bars.timeframe.Timeframe.parse`, `qts.quality.guardrails.GuardrailSuite`, `qts.quality.guardrails.GuardrailSuite.check_file`
- `qts.quality.guardrails._check_import`
  - 类型：`module_function`
  - 位置：`backend/src/qts/quality/guardrails.py:403`
  - 说明：Perform check import.
  - 直接调用：`GuardrailViolation`, `_is_forbidden_adapter_dependency`, `_is_forbidden_broker_adapter_dependency`, `_is_forbidden_dependency`, `imported_module.split`, `imported_module.startswith`, `len`, `str`
  - 可解析内部调用：`qts.quality.guardrails.GuardrailViolation`, `qts.quality.guardrails._is_forbidden_adapter_dependency`, `qts.quality.guardrails._is_forbidden_broker_adapter_dependency`, `qts.quality.guardrails._is_forbidden_dependency`
- `qts.quality.guardrails._is_forbidden_dependency`
  - 类型：`module_function`
  - 位置：`backend/src/qts/quality/guardrails.py:450`
  - 说明：Perform is forbidden dependency.
  - 直接调用：`imported_module.startswith`
  - 可解析内部调用：无
- `qts.quality.guardrails._is_forbidden_broker_adapter_dependency`
  - 类型：`module_function`
  - 位置：`backend/src/qts/quality/guardrails.py:478`
  - 说明：Perform is forbidden broker adapter dependency.
  - 直接调用：`any`, `imported_module.startswith`
  - 可解析内部调用：无
- `qts.quality.guardrails._is_forbidden_adapter_dependency`
  - 类型：`module_function`
  - 位置：`backend/src/qts/quality/guardrails.py:490`
  - 说明：Perform is forbidden adapter dependency.
  - 直接调用：`imported_module.startswith`
  - 可解析内部调用：无
- `qts.quality.guardrails._check_product_specific_code`
  - 类型：`module_function`
  - 位置：`backend/src/qts/quality/guardrails.py:501`
  - 说明：Perform check product specific code.
  - 直接调用：`_check_forbidden_tokens`
  - 可解析内部调用：`qts.quality.guardrails._check_forbidden_tokens`
- `qts.quality.guardrails._check_broker_specific_code`
  - 类型：`module_function`
  - 位置：`backend/src/qts/quality/guardrails.py:517`
  - 说明：Perform check broker specific code.
  - 直接调用：`_check_forbidden_tokens`
  - 可解析内部调用：`qts.quality.guardrails._check_forbidden_tokens`
- `qts.quality.guardrails._check_test_support_code`
  - 类型：`module_function`
  - 位置：`backend/src/qts/quality/guardrails.py:533`
  - 说明：Perform check test support code.
  - 直接调用：`GuardrailViolation`, `_contains_forbidden_token`, `_identifier_tokens`, `_node_identifier_name`, `ast.walk`, `getattr`, `path_tokens.intersection`, `str`, `violations.append`
  - 可解析内部调用：`qts.indicators.rolling.RollingWindow.append`, `qts.quality.guardrails.GuardrailViolation`, `qts.quality.guardrails._contains_forbidden_token`, `qts.quality.guardrails._identifier_tokens`, `qts.quality.guardrails._node_identifier_name`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`
- `qts.quality.guardrails._check_shared_capability_placement`
  - 类型：`module_function`
  - 位置：`backend/src/qts/quality/guardrails.py:564`
  - 说明：Perform check shared capability placement.
  - 直接调用：`GuardrailViolation`, `_has_allowed_prefix`, `_identifier_tokens`, `path_tokens.intersection`, `str`
  - 可解析内部调用：`qts.quality.guardrails.GuardrailViolation`, `qts.quality.guardrails._has_allowed_prefix`, `qts.quality.guardrails._identifier_tokens`
- `qts.quality.guardrails._check_oop_public_factory_functions`
  - 类型：`module_function`
  - 位置：`backend/src/qts/quality/guardrails.py:586`
  - 说明：Perform check oop public factory functions.
  - 直接调用：`GuardrailViolation`, `cast`, `isinstance`, `node.name.startswith`, `qts_relative_path.as_posix`, `str`, `violations.append`
  - 可解析内部调用：`qts.indicators.rolling.RollingWindow.append`, `qts.quality.guardrails.GuardrailViolation`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`
- `qts.quality.guardrails._check_oop_helper_ownership`
  - 类型：`module_function`
  - 位置：`backend/src/qts/quality/guardrails.py:617`
  - 说明：Perform check oop helper ownership.
  - 直接调用：`GuardrailViolation`, `_node_references_name`, `cast`, `isinstance`, `len`, `node.name.startswith`, `qts_relative_path.as_posix`, `str`, `violations.append`
  - 可解析内部调用：`qts.indicators.rolling.RollingWindow.append`, `qts.quality.guardrails.GuardrailViolation`, `qts.quality.guardrails._node_references_name`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`
- `qts.quality.guardrails._check_backtest_runner_cohesion`
  - 类型：`module_function`
  - 位置：`backend/src/qts/quality/guardrails.py:684`
  - 说明：Perform check backtest runner cohesion.
  - 直接调用：`GuardrailViolation`, `_iter_imported_names`, `_iter_imports`, `ast.walk`, `imported_module.startswith`, `isinstance`, `str`, `violations.append`
  - 可解析内部调用：`qts.indicators.rolling.RollingWindow.append`, `qts.quality.guardrails.GuardrailViolation`, `qts.quality.guardrails._iter_imported_names`, `qts.quality.guardrails._iter_imports`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`
- `qts.quality.guardrails._check_backtest_input_cohesion`
  - 类型：`module_function`
  - 位置：`backend/src/qts/quality/guardrails.py:740`
  - 说明：Perform check backtest input cohesion.
  - 直接调用：`GuardrailViolation`, `_iter_imported_names`, `_iter_imports`, `ast.walk`, `isinstance`, `str`, `violations.append`
  - 可解析内部调用：`qts.indicators.rolling.RollingWindow.append`, `qts.quality.guardrails.GuardrailViolation`, `qts.quality.guardrails._iter_imported_names`, `qts.quality.guardrails._iter_imports`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`
- `qts.quality.guardrails._check_backtest_engine_cohesion`
  - 类型：`module_function`
  - 位置：`backend/src/qts/quality/guardrails.py:796`
  - 说明：Perform check backtest engine cohesion.
  - 直接调用：`GuardrailViolation`, `_iter_imports`, `ast.walk`, `imported_module.startswith`, `isinstance`, `str`, `violations.append`
  - 可解析内部调用：`qts.indicators.rolling.RollingWindow.append`, `qts.quality.guardrails.GuardrailViolation`, `qts.quality.guardrails._iter_imports`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`
- `qts.quality.guardrails._check_strategy_sdk_internal_leak`
  - 类型：`module_function`
  - 位置：`backend/src/qts/quality/guardrails.py:836`
  - 说明：Perform check strategy sdk internal leak.
  - 直接调用：`GuardrailViolation`, `_iter_imported_names`, `_iter_imports`, `ast.walk`, `cast`, `getattr`, `imported_module.startswith`, `isinstance`, `str`, `violations.append`
  - 可解析内部调用：`qts.indicators.rolling.RollingWindow.append`, `qts.quality.guardrails.GuardrailViolation`, `qts.quality.guardrails._iter_imported_names`, `qts.quality.guardrails._iter_imports`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`
- `qts.quality.guardrails._check_forbidden_tokens`
  - 类型：`module_function`
  - 位置：`backend/src/qts/quality/guardrails.py:900`
  - 说明：Perform check forbidden tokens.
  - 直接调用：`GuardrailViolation`, `_contains_forbidden_token`, `_node_identifier_name`, `ast.walk`, `getattr`, `isinstance`, `str`, `violations.append`
  - 可解析内部调用：`qts.indicators.rolling.RollingWindow.append`, `qts.quality.guardrails.GuardrailViolation`, `qts.quality.guardrails._contains_forbidden_token`, `qts.quality.guardrails._node_identifier_name`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`
- `qts.quality.guardrails._node_identifier_name`
  - 类型：`module_function`
  - 位置：`backend/src/qts/quality/guardrails.py:933`
  - 说明：Perform node identifier name.
  - 直接调用：`isinstance`
  - 可解析内部调用：无
- `qts.quality.guardrails._contains_forbidden_token`
  - 类型：`module_function`
  - 位置：`backend/src/qts/quality/guardrails.py:943`
  - 说明：Perform contains forbidden token.
  - 直接调用：`_identifier_tokens`, `any`
  - 可解析内部调用：`qts.quality.guardrails._identifier_tokens`
- `qts.quality.guardrails._node_references_name`
  - 类型：`module_function`
  - 位置：`backend/src/qts/quality/guardrails.py:947`
  - 说明：Perform node references name.
  - 直接调用：`any`, `ast.walk`, `isinstance`
  - 可解析内部调用：无
- `qts.quality.guardrails._identifier_tokens`
  - 类型：`module_function`
  - 位置：`backend/src/qts/quality/guardrails.py:954`
  - 说明：Perform identifier tokens.
  - 直接调用：`item.upper`, `part.upper`, `re.findall`, `re.split`, `set`, `tokens.add`, `tokens.update`
  - 可解析内部调用：`qts.application.services.strategy_service.StrategyLifecycleService.add`, `qts.backtest.report.StreamingEquityMetrics.update`, `qts.data.bars.aggregator.BarAggregator.update`, `qts.indicators.price.ema.EMA.update`, `qts.indicators.price.sma.SMA.update`, `qts.strategy_sdk.indicators.AssetIndicator.update`
- `qts.quality.guardrails._iter_imports`
  - 类型：`module_function`
  - 位置：`backend/src/qts/quality/guardrails.py:966`
  - 说明：Perform iter imports.
  - 直接调用：`ast.walk`, `imports.append`, `imports.extend`, `isinstance`
  - 可解析内部调用：`qts.indicators.rolling.RollingWindow.append`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`
- `qts.quality.guardrails._iter_imported_names`
  - 类型：`module_function`
  - 位置：`backend/src/qts/quality/guardrails.py:976`
  - 说明：Perform iter imported names.
  - 直接调用：`ast.walk`, `imports.extend`, `isinstance`
  - 可解析内部调用：无
- `qts.quality.guardrails._has_allowed_prefix`
  - 类型：`module_function`
  - 位置：`backend/src/qts/quality/guardrails.py:984`
  - 说明：Perform has allowed prefix.
  - 直接调用：`any`, `len`
  - 可解析内部调用：无
- `qts.quality.guardrails.main`
  - 类型：`module_function`
  - 位置：`backend/src/qts/quality/guardrails.py:988`
  - 说明：Perform main.
  - 直接调用：`Path.cwd`, `print`, `run_guardrails`, `violation.format`
  - 可解析内部调用：`qts.quality.guardrails.GuardrailViolation.format`, `qts.quality.guardrails.run_guardrails`

### `backend/src/qts/reconciliation/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/reconciliation/drift.py`

- `qts.reconciliation.drift.DriftKind`
  - 类型：`class`
  - 位置：`backend/src/qts/reconciliation/drift.py:12`
  - 说明：Reconciliation drift categories.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.reconciliation.drift.DriftItem`
  - 类型：`class`
  - 位置：`backend/src/qts/reconciliation/drift.py:23`
  - 说明：Single discrepancy item between snapshots.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.reconciliation.drift.DriftItem.to_dict`
  - 类型：`method`
  - 位置：`backend/src/qts/reconciliation/drift.py:31`
  - 说明：Serialize drift for observability output.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.reconciliation.drift.compare_orders`
  - 类型：`module_function`
  - 位置：`backend/src/qts/reconciliation/drift.py:41`
  - 说明：Compare order snapshots and return drift entries.
  - 直接调用：`DriftItem`, `_order_repr`, `items.append`, `left.get`, `left.keys`, `right.get`, `right.keys`, `sorted`
  - 可解析内部调用：`qts.indicators.rolling.RollingWindow.append`, `qts.reconciliation.drift.DriftItem`, `qts.reconciliation.drift._order_repr`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`, `qts.runtime.mailbox.Mailbox.get`
- `qts.reconciliation.drift.compare_positions`
  - 类型：`module_function`
  - 位置：`backend/src/qts/reconciliation/drift.py:77`
  - 说明：Compare position snapshots and return drift entries.
  - 直接调用：`_quantity_item`, `items.append`, `left.get`, `left.keys`, `right.get`, `right.keys`, `sorted`
  - 可解析内部调用：`qts.indicators.rolling.RollingWindow.append`, `qts.reconciliation.drift._quantity_item`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`, `qts.runtime.mailbox.Mailbox.get`
- `qts.reconciliation.drift.compare_cash`
  - 类型：`module_function`
  - 位置：`backend/src/qts/reconciliation/drift.py:94`
  - 说明：Compare cash snapshots and return drift entries.
  - 直接调用：`_quantity_item`, `items.append`, `left.get`, `left.keys`, `right.get`, `right.keys`, `sorted`
  - 可解析内部调用：`qts.indicators.rolling.RollingWindow.append`, `qts.reconciliation.drift._quantity_item`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`, `qts.runtime.mailbox.Mailbox.get`
- `qts.reconciliation.drift.drift_sort_key`
  - 类型：`module_function`
  - 位置：`backend/src/qts/reconciliation/drift.py:111`
  - 说明：Stable sort order for reconciliation drift items.
  - 直接调用：`key.split`
  - 可解析内部调用：无
- `qts.reconciliation.drift._quantity_item`
  - 类型：`module_function`
  - 位置：`backend/src/qts/reconciliation/drift.py:118`
  - 说明：Build drift record for comparable quantity-like entries.
  - 直接调用：`DriftItem`, `_amount`, `_amount_repr`, `abs`
  - 可解析内部调用：`qts.reconciliation.drift.DriftItem`, `qts.reconciliation.drift._amount`, `qts.reconciliation.drift._amount_repr`
- `qts.reconciliation.drift._order_repr`
  - 类型：`module_function`
  - 位置：`backend/src/qts/reconciliation/drift.py:140`
  - 说明：Serialize one normalized order snapshot.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.reconciliation.drift._amount`
  - 类型：`module_function`
  - 位置：`backend/src/qts/reconciliation/drift.py:147`
  - 说明：Return numeric amount for an order-independent snapshot entry.
  - 直接调用：`isinstance`
  - 可解析内部调用：无
- `qts.reconciliation.drift._amount_repr`
  - 类型：`module_function`
  - 位置：`backend/src/qts/reconciliation/drift.py:154`
  - 说明：Serialize amount for drift output.
  - 直接调用：`_amount`, `str`
  - 可解析内部调用：`qts.reconciliation.drift._amount`

### `backend/src/qts/reconciliation/engine.py`

- `qts.reconciliation.engine.ReconciliationEngine`
  - 类型：`class`
  - 位置：`backend/src/qts/reconciliation/engine.py:13`
  - 说明：Deterministic snapshot reconciliation service.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.reconciliation.engine.ReconciliationEngine.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/reconciliation/engine.py:16`
  - 说明：Create the engine with a non-negative tolerance.
  - 直接调用：`Decimal`, `ValueError`
  - 可解析内部调用：无
- `qts.reconciliation.engine.ReconciliationEngine.reconcile`
  - 类型：`method`
  - 位置：`backend/src/qts/reconciliation/engine.py:22`
  - 说明：Reconcile two snapshots and return a drift report.
  - 直接调用：`reconcile_snapshots`, `self._effective_tolerance`
  - 可解析内部调用：`qts.reconciliation.engine.ReconciliationEngine._effective_tolerance`, `qts.reconciliation.engine.reconcile_snapshots`
- `qts.reconciliation.engine.ReconciliationEngine.startup_gate`
  - 类型：`method`
  - 位置：`backend/src/qts/reconciliation/engine.py:36`
  - 说明：Return startup decision from a drift report.
  - 直接调用：`startup_reconciliation_gate`
  - 可解析内部调用：`qts.reconciliation.startup_gate.startup_reconciliation_gate`
- `qts.reconciliation.engine.ReconciliationEngine._effective_tolerance`
  - 类型：`method`
  - 位置：`backend/src/qts/reconciliation/engine.py:40`
  - 说明：Resolve effective tolerance with validation.
  - 直接调用：`Decimal`, `ValueError`
  - 可解析内部调用：无
- `qts.reconciliation.engine.reconcile_snapshots`
  - 类型：`module_function`
  - 位置：`backend/src/qts/reconciliation/engine.py:49`
  - 说明：Compare broker and internal snapshots into a deterministic drift report.
  - 直接调用：`Decimal`, `ReconciliationReport`, `ValueError`, `compare_cash`, `compare_orders`, `compare_positions`, `drift_sort_key`, `sorted`, `tuple`
  - 可解析内部调用：`qts.reconciliation.drift.compare_cash`, `qts.reconciliation.drift.compare_orders`, `qts.reconciliation.drift.compare_positions`, `qts.reconciliation.drift.drift_sort_key`, `qts.reconciliation.report.ReconciliationReport`

### `backend/src/qts/reconciliation/report.py`

- `qts.reconciliation.report.ReconciliationReport`
  - 类型：`class`
  - 位置：`backend/src/qts/reconciliation/report.py:14`
  - 说明：Drift report for a single account.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.reconciliation.report.ReconciliationReport.has_drift`
  - 类型：`property`
  - 位置：`backend/src/qts/reconciliation/report.py:21`
  - 说明：True when report contains non-tolerable mismatch.
  - 直接调用：`any`
  - 可解析内部调用：无
- `qts.reconciliation.report.ReconciliationReport.to_dict`
  - 类型：`method`
  - 位置：`backend/src/qts/reconciliation/report.py:27`
  - 说明：Serialize reconciliation report.
  - 直接调用：`item.to_dict`
  - 可解析内部调用：`qts.reconciliation.drift.DriftItem.to_dict`, `qts.reconciliation.report.ReconciliationReport.to_dict`

### `backend/src/qts/reconciliation/snapshots.py`

- `qts.reconciliation.snapshots.OrderSnapshot`
  - 类型：`class`
  - 位置：`backend/src/qts/reconciliation/snapshots.py:13`
  - 说明：Normalized representation of an internal or broker order.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.reconciliation.snapshots.OrderSnapshot.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/reconciliation/snapshots.py:22`
  - 说明：Validate normalized order snapshot values.
  - 直接调用：`Decimal`, `ValueError`, `self.status.strip`
  - 可解析内部调用：无
- `qts.reconciliation.snapshots.PositionSnapshot`
  - 类型：`class`
  - 位置：`backend/src/qts/reconciliation/snapshots.py:31`
  - 说明：Normalized position entry used for reconciliation.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.reconciliation.snapshots.CashSnapshot`
  - 类型：`class`
  - 位置：`backend/src/qts/reconciliation/snapshots.py:39`
  - 说明：Normalized cash entry used for reconciliation.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.reconciliation.snapshots.CashSnapshot.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/reconciliation/snapshots.py:45`
  - 说明：Validate normalized cash snapshot values.
  - 直接调用：`ValueError`, `self.currency.strip`
  - 可解析内部调用：无
- `qts.reconciliation.snapshots.ReconciliationSnapshot`
  - 类型：`class`
  - 位置：`backend/src/qts/reconciliation/snapshots.py:52`
  - 说明：Normalized account snapshot used by the reconciliation engine.
  - 直接调用：无
  - 可解析内部调用：无

### `backend/src/qts/reconciliation/startup_gate.py`

- `qts.reconciliation.startup_gate.StartupReconciliationDecision`
  - 类型：`class`
  - 位置：`backend/src/qts/reconciliation/startup_gate.py:11`
  - 说明：Decision object returned before runtime startup.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.reconciliation.startup_gate.startup_reconciliation_gate`
  - 类型：`module_function`
  - 位置：`backend/src/qts/reconciliation/startup_gate.py:19`
  - 说明：Return startup decision based on whether report has critical drift.
  - 直接调用：`StartupReconciliationDecision`
  - 可解析内部调用：`qts.reconciliation.startup_gate.StartupReconciliationDecision`

### `backend/src/qts/registry/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/registry/broker_symbol_mapping.py`

- `qts.registry.broker_symbol_mapping.BrokerSymbolMapping`
  - 类型：`class`
  - 位置：`backend/src/qts/registry/broker_symbol_mapping.py:8`
  - 说明：Bidirectional mapping between internal IDs and one broker's symbols.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/broker_symbol_mapping.py:11`
  - 说明：Perform __init__.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.register`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/broker_symbol_mapping.py:17`
  - 说明：Perform register.
  - 直接调用：`ValueError`, `self._normalize_broker_symbol`, `self._to_instrument.get`
  - 可解析内部调用：`qts.registry.broker_symbol_mapping.BrokerSymbolMapping._normalize_broker_symbol`, `qts.runtime.mailbox.Mailbox.get`
- `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.to_broker_symbol`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/broker_symbol_mapping.py:26`
  - 说明：Perform to_broker_symbol.
  - 直接调用：`KeyError`
  - 可解析内部调用：无
- `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.to_instrument_id`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/broker_symbol_mapping.py:33`
  - 说明：Perform to_instrument_id.
  - 直接调用：`KeyError`, `self._normalize_broker_symbol`
  - 可解析内部调用：`qts.registry.broker_symbol_mapping.BrokerSymbolMapping._normalize_broker_symbol`
- `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.is_supported_symbol`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/broker_symbol_mapping.py:43`
  - 说明：Perform is_supported_symbol.
  - 直接调用：`self._normalize_broker_symbol`
  - 可解析内部调用：`qts.registry.broker_symbol_mapping.BrokerSymbolMapping._normalize_broker_symbol`
- `qts.registry.broker_symbol_mapping.BrokerSymbolMapping.instrument_id_for_symbol`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/broker_symbol_mapping.py:47`
  - 说明：Perform instrument_id_for_symbol.
  - 直接调用：`self.to_instrument_id`
  - 可解析内部调用：`qts.registry.broker_symbol_mapping.BrokerSymbolMapping.to_instrument_id`
- `qts.registry.broker_symbol_mapping.BrokerSymbolMapping._normalize_broker_symbol`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/registry/broker_symbol_mapping.py:52`
  - 说明：Perform _normalize_broker_symbol.
  - 直接调用：`ValueError`, `broker_symbol.strip`
  - 可解析内部调用：无

### `backend/src/qts/registry/calendar_registry.py`

- `qts.registry.calendar_registry.MarketSession`
  - 类型：`class`
  - 位置：`backend/src/qts/registry/calendar_registry.py:13`
  - 说明：Internal half-open exchange session.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.registry.calendar_registry.MarketSession.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/calendar_registry.py:20`
  - 说明：Perform __post_init__.
  - 直接调用：`ValueError`, `self.calendar_id.strip`, `self.session_id.strip`
  - 可解析内部调用：无
- `qts.registry.calendar_registry.MarketSession.open_time`
  - 类型：`property`
  - 位置：`backend/src/qts/registry/calendar_registry.py:28`
  - 说明：Perform open_time.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.registry.calendar_registry.MarketSession.close_time`
  - 类型：`property`
  - 位置：`backend/src/qts/registry/calendar_registry.py:33`
  - 说明：Perform close_time.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.registry.calendar_registry.CalendarProvider`
  - 类型：`class`
  - 位置：`backend/src/qts/registry/calendar_registry.py:38`
  - 说明：Provider interface for internal calendar session lookup.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.registry.calendar_registry.CalendarProvider.session_for`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/calendar_registry.py:41`
  - 说明：Return the exchange session for a date.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.registry.calendar_registry.CalendarRegistry`
  - 类型：`class`
  - 位置：`backend/src/qts/registry/calendar_registry.py:45`
  - 说明：Lookup table for calendar providers.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.registry.calendar_registry.CalendarRegistry.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/calendar_registry.py:48`
  - 说明：Perform __init__.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.registry.calendar_registry.CalendarRegistry.register`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/calendar_registry.py:52`
  - 说明：Perform register.
  - 直接调用：`ValueError`, `calendar_id.strip`
  - 可解析内部调用：无
- `qts.registry.calendar_registry.CalendarRegistry.session_for`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/calendar_registry.py:58`
  - 说明：Perform session_for.
  - 直接调用：`KeyError`, `provider.session_for`
  - 可解析内部调用：`qts.data.sessions.filter.SessionLookup.session_for`, `qts.registry.calendar_registry.CalendarProvider.session_for`, `qts.registry.calendar_registry.CalendarRegistry.session_for`, `qts.registry.providers.comex_gold_calendar_provider.ComexGoldCalendarProvider.session_for`, `qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider.session_for`, `qts.risk.rules.trading_session_rule.SessionLookup.session_for`

### `backend/src/qts/registry/future_chain_registry.py`

- `qts.registry.future_chain_registry.FutureChain`
  - 类型：`class`
  - 位置：`backend/src/qts/registry/future_chain_registry.py:11`
  - 说明：Ordered concrete future contracts for a root symbol.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.registry.future_chain_registry.FutureChain.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/future_chain_registry.py:17`
  - 说明：Perform __post_init__.
  - 直接调用：`ValueError`, `self.root_symbol.strip`
  - 可解析内部调用：无
- `qts.registry.future_chain_registry.ContinuousFutureRef`
  - 类型：`class`
  - 位置：`backend/src/qts/registry/future_chain_registry.py:26`
  - 说明：Research/data reference to a rolling future contract.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.registry.future_chain_registry.ContinuousFutureRef.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/future_chain_registry.py:32`
  - 说明：Perform __post_init__.
  - 直接调用：`ValueError`, `self.root_symbol.strip`
  - 可解析内部调用：无
- `qts.registry.future_chain_registry.FutureChainRegistry`
  - 类型：`class`
  - 位置：`backend/src/qts/registry/future_chain_registry.py:40`
  - 说明：Resolve future roots to concrete tradable contracts.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.registry.future_chain_registry.FutureChainRegistry.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/future_chain_registry.py:43`
  - 说明：Perform __init__.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.registry.future_chain_registry.FutureChainRegistry.register`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/future_chain_registry.py:47`
  - 说明：Perform register.
  - 直接调用：`self._normalize_root`
  - 可解析内部调用：`qts.registry.future_chain_registry.FutureChainRegistry._normalize_root`, `qts.registry.future_roll.FutureRollRegistry._normalize_root`
- `qts.registry.future_chain_registry.FutureChainRegistry.resolve_contract`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/future_chain_registry.py:51`
  - 说明：Perform resolve_contract.
  - 直接调用：`KeyError`, `self._get_chain`
  - 可解析内部调用：`qts.registry.future_chain_registry.FutureChainRegistry._get_chain`
- `qts.registry.future_chain_registry.FutureChainRegistry.require_tradable`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/future_chain_registry.py:61`
  - 说明：Perform require_tradable.
  - 直接调用：`ValueError`, `isinstance`
  - 可解析内部调用：无
- `qts.registry.future_chain_registry.FutureChainRegistry._get_chain`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/future_chain_registry.py:67`
  - 说明：Perform _get_chain.
  - 直接调用：`KeyError`, `self._normalize_root`
  - 可解析内部调用：`qts.registry.future_chain_registry.FutureChainRegistry._normalize_root`, `qts.registry.future_roll.FutureRollRegistry._normalize_root`
- `qts.registry.future_chain_registry.FutureChainRegistry._normalize_root`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/registry/future_chain_registry.py:76`
  - 说明：Perform _normalize_root.
  - 直接调用：`ValueError`, `root_symbol.strip`, `root_symbol.strip.upper`
  - 可解析内部调用：无

### `backend/src/qts/registry/future_roll.py`

- `qts.registry.future_roll.FutureContractCandidate`
  - 类型：`class`
  - 位置：`backend/src/qts/registry/future_roll.py:16`
  - 说明：One concrete futures contract candidate at a decision timestamp.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.registry.future_roll.FutureContractCandidate.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/future_roll.py:26`
  - 说明：Perform post init.
  - 直接调用：`Decimal`, `ValueError`, `self.root_symbol.strip`, `self.symbol.strip`
  - 可解析内部调用：无
- `qts.registry.future_roll.FutureContractSelector`
  - 类型：`class`
  - 位置：`backend/src/qts/registry/future_roll.py:35`
  - 说明：Select one concrete future from same-root same-time candidates.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.registry.future_roll.FutureContractSelector.select`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/future_roll.py:38`
  - 说明：Select a concrete future contract.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.registry.future_roll.HighestVolumeFutureContractSelector`
  - 类型：`class`
  - 位置：`backend/src/qts/registry/future_roll.py:46`
  - 说明：Select the most liquid candidate for one root at one timestamp.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.registry.future_roll.HighestVolumeFutureContractSelector.select`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/future_roll.py:49`
  - 说明：Perform select.
  - 直接调用：`ValueError`, `max`
  - 可解析内部调用：无
- `qts.registry.future_roll.FutureRollSelection`
  - 类型：`class`
  - 位置：`backend/src/qts/registry/future_roll.py:67`
  - 说明：Resolved concrete contract for a continuous future at one timestamp.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.registry.future_roll.FutureRollSelection.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/future_roll.py:77`
  - 说明：Perform post init.
  - 直接调用：`ValueError`, `self.root_symbol.strip`, `self.source_symbol.strip`
  - 可解析内部调用：无
- `qts.registry.future_roll.FutureRollRegistry`
  - 类型：`class`
  - 位置：`backend/src/qts/registry/future_roll.py:84`
  - 说明：Resolve continuous futures to concrete contracts over time.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.registry.future_roll.FutureRollRegistry.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/future_roll.py:87`
  - 说明：Perform init.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.registry.future_roll.FutureRollRegistry.register_root`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/future_roll.py:96`
  - 说明：Perform register_root.
  - 直接调用：`InstrumentId`, `ValueError`, `dict.fromkeys`, `exchange.strip`, `exchange.strip.upper`, `self._latest_prices_by_continuous.setdefault`, `self._normalize_root`, `self._selection_times_by_continuous.setdefault`, `self._selections_by_continuous.setdefault`, `tuple`
  - 可解析内部调用：`qts.core.ids.InstrumentId`, `qts.registry.future_chain_registry.FutureChainRegistry._normalize_root`, `qts.registry.future_roll.FutureRollRegistry._normalize_root`
- `qts.registry.future_roll.FutureRollRegistry.continuous_instrument_id`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/future_roll.py:119`
  - 说明：Perform continuous_instrument_id.
  - 直接调用：`KeyError`, `ValueError`, `self._normalize_root`
  - 可解析内部调用：`qts.registry.future_chain_registry.FutureChainRegistry._normalize_root`, `qts.registry.future_roll.FutureRollRegistry._normalize_root`
- `qts.registry.future_roll.FutureRollRegistry.record_selection`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/future_roll.py:129`
  - 说明：Perform record_selection.
  - 直接调用：`KeyError`, `ValueError`, `dict`, `latest_prices.update`, `replace`, `selection_times.append`, `selections.append`
  - 可解析内部调用：`qts.backtest.report.StreamingEquityMetrics.update`, `qts.data.bars.aggregator.BarAggregator.update`, `qts.indicators.price.ema.EMA.update`, `qts.indicators.price.sma.SMA.update`, `qts.indicators.rolling.RollingWindow.append`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`, `qts.strategy_sdk.indicators.AssetIndicator.update`
- `qts.registry.future_roll.FutureRollRegistry.is_continuous`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/future_roll.py:147`
  - 说明：Perform is_continuous.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.registry.future_roll.FutureRollRegistry.resolve_contract`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/future_roll.py:151`
  - 说明：Perform resolve_contract.
  - 直接调用：`ValueError`, `isinstance`, `self._selection_at`, `self.continuous_instrument_id`
  - 可解析内部调用：`qts.registry.future_roll.FutureRollRegistry._selection_at`, `qts.registry.future_roll.FutureRollRegistry.continuous_instrument_id`, `qts.strategy_sdk.asset_resolver.ContinuousFutureResolver.continuous_instrument_id`
- `qts.registry.future_roll.FutureRollRegistry.related_contracts`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/future_roll.py:169`
  - 说明：Perform related_contracts.
  - 直接调用：`KeyError`
  - 可解析内部调用：无
- `qts.registry.future_roll.FutureRollRegistry.execution_price`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/future_roll.py:176`
  - 说明：Perform execution_price.
  - 直接调用：`KeyError`, `as_of.isoformat`, `self._selection_at`
  - 可解析内部调用：`qts.registry.future_roll.FutureRollRegistry._selection_at`
- `qts.registry.future_roll.FutureRollRegistry._selection_at`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/future_roll.py:192`
  - 说明：Perform selection at.
  - 直接调用：`KeyError`, `as_of.isoformat`, `bisect_right`
  - 可解析内部调用：无
- `qts.registry.future_roll.FutureRollRegistry._normalize_root`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/registry/future_roll.py:212`
  - 说明：Perform normalize root.
  - 直接调用：`ValueError`, `root_symbol.strip`, `root_symbol.strip.upper`
  - 可解析内部调用：无

### `backend/src/qts/registry/instrument_registry.py`

- `qts.registry.instrument_registry.InstrumentRegistry`
  - 类型：`class`
  - 位置：`backend/src/qts/registry/instrument_registry.py:9`
  - 说明：Resolve user-facing symbols to internal instruments.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.registry.instrument_registry.InstrumentRegistry.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/instrument_registry.py:12`
  - 说明：Perform __init__.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.registry.instrument_registry.InstrumentRegistry.register`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/instrument_registry.py:17`
  - 说明：Perform register.
  - 直接调用：`self._normalize_symbol`
  - 可解析内部调用：`qts.backtest.config.BacktestRunConfig._normalize_symbol`, `qts.data.historical.catalog.HistoricalCatalogLoadConfig._normalize_symbol`, `qts.registry.instrument_registry.InstrumentRegistry._normalize_symbol`, `qts.registry.symbol_resolution.StaticSymbolResolver._normalize_symbol`
- `qts.registry.instrument_registry.InstrumentRegistry.resolve`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/instrument_registry.py:23`
  - 说明：Perform resolve.
  - 直接调用：`KeyError`, `self._normalize_symbol`
  - 可解析内部调用：`qts.backtest.config.BacktestRunConfig._normalize_symbol`, `qts.data.historical.catalog.HistoricalCatalogLoadConfig._normalize_symbol`, `qts.registry.instrument_registry.InstrumentRegistry._normalize_symbol`, `qts.registry.symbol_resolution.StaticSymbolResolver._normalize_symbol`
- `qts.registry.instrument_registry.InstrumentRegistry.get_instrument`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/instrument_registry.py:31`
  - 说明：Perform get_instrument.
  - 直接调用：`KeyError`
  - 可解析内部调用：无
- `qts.registry.instrument_registry.InstrumentRegistry.get_contract_spec`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/instrument_registry.py:38`
  - 说明：Perform get_contract_spec.
  - 直接调用：`self.get_instrument`
  - 可解析内部调用：`qts.registry.instrument_registry.InstrumentRegistry.get_instrument`
- `qts.registry.instrument_registry.InstrumentRegistry._normalize_symbol`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/registry/instrument_registry.py:43`
  - 说明：Perform _normalize_symbol.
  - 直接调用：`ValueError`, `user_symbol.strip`, `user_symbol.strip.upper`
  - 可解析内部调用：无

### `backend/src/qts/registry/option_chain_registry.py`

- `qts.registry.option_chain_registry.OptionChainRegistry`
  - 类型：`class`
  - 位置：`backend/src/qts/registry/option_chain_registry.py:12`
  - 说明：Lookup option instruments by underlying and simple filters.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.registry.option_chain_registry.OptionChainRegistry.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/option_chain_registry.py:15`
  - 说明：Perform __init__.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.registry.option_chain_registry.OptionChainRegistry.register`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/option_chain_registry.py:19`
  - 说明：Perform register.
  - 直接调用：`ValueError`, `isinstance`, `self._chains.setdefault`, `self._chains.setdefault.append`
  - 可解析内部调用：`qts.indicators.rolling.RollingWindow.append`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`
- `qts.registry.option_chain_registry.OptionChainRegistry.options_for`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/option_chain_registry.py:27`
  - 说明：Perform options_for.
  - 直接调用：`KeyError`, `list`
  - 可解析内部调用：无
- `qts.registry.option_chain_registry.OptionChainRegistry.find`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/option_chain_registry.py:34`
  - 说明：Perform find.
  - 直接调用：`isinstance`, `self.options_for`
  - 可解析内部调用：`qts.registry.option_chain_registry.OptionChainRegistry.options_for`

### `backend/src/qts/registry/providers/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/registry/providers/comex_gold_calendar_provider.py`

- `qts.registry.providers.comex_gold_calendar_provider.ComexGoldCalendarProvider`
  - 类型：`class`
  - 位置：`backend/src/qts/registry/providers/comex_gold_calendar_provider.py:12`
  - 说明：Regular COMEX Gold session provider for anchor-verified semantics.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.registry.providers.comex_gold_calendar_provider.ComexGoldCalendarProvider.session_for`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/providers/comex_gold_calendar_provider.py:18`
  - 说明：Perform session_for.
  - 直接调用：`MarketSession`, `TimeInterval`, `ZoneInfo`, `close_time.astimezone`, `datetime.combine`, `open_time.astimezone`, `session_date.isoformat`, `time`, `timedelta`
  - 可解析内部调用：`qts.core.time.TimeInterval`, `qts.registry.calendar_registry.MarketSession`

### `backend/src/qts/registry/providers/exchange_calendar_provider.py`

- `qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider`
  - 类型：`class`
  - 位置：`backend/src/qts/registry/providers/exchange_calendar_provider.py:14`
  - 说明：Calendar provider backed by ``exchange-calendars``.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/providers/exchange_calendar_provider.py:17`
  - 说明：Perform __init__.
  - 直接调用：`ValueError`, `calendar_id.strip`, `xc.get_calendar`
  - 可解析内部调用：无
- `qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider.session_for`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/providers/exchange_calendar_provider.py:24`
  - 说明：Perform session_for.
  - 直接调用：`MarketSession`, `TimeInterval`, `self._calendar.session_close`, `self._calendar.session_open`, `self._to_datetime`, `session_date.isoformat`
  - 可解析内部调用：`qts.core.time.TimeInterval`, `qts.registry.calendar_registry.MarketSession`, `qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider._to_datetime`
- `qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider._to_datetime`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/registry/providers/exchange_calendar_provider.py:36`
  - 说明：Perform _to_datetime.
  - 直接调用：`TypeError`, `hasattr`, `isinstance`, `type`, `value.to_pydatetime`
  - 可解析内部调用：无

### `backend/src/qts/registry/symbol_resolution.py`

- `qts.registry.symbol_resolution.SourceSymbolResolver`
  - 类型：`class`
  - 位置：`backend/src/qts/registry/symbol_resolution.py:12`
  - 说明：Resolve external source symbols into internal instrument IDs.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.registry.symbol_resolution.SourceSymbolResolver.is_supported_symbol`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/symbol_resolution.py:15`
  - 说明：Return whether the resolver knows how to map ``symbol``.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.registry.symbol_resolution.SourceSymbolResolver.instrument_id_for_symbol`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/symbol_resolution.py:19`
  - 说明：Resolve ``symbol`` to an internal ``InstrumentId``.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.registry.symbol_resolution.StaticSymbolResolver`
  - 类型：`class`
  - 位置：`backend/src/qts/registry/symbol_resolution.py:25`
  - 说明：Resolve source symbols from an explicit symbol-to-instrument mapping.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.registry.symbol_resolution.StaticSymbolResolver.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/symbol_resolution.py:31`
  - 说明：Perform __post_init__.
  - 直接调用：`ValueError`, `object.__setattr__`, `self._normalize_symbol`, `self.instrument_ids.items`
  - 可解析内部调用：`qts.backtest.config.BacktestRunConfig._normalize_symbol`, `qts.data.historical.catalog.HistoricalCatalogLoadConfig._normalize_symbol`, `qts.registry.instrument_registry.InstrumentRegistry._normalize_symbol`, `qts.registry.symbol_resolution.StaticSymbolResolver._normalize_symbol`
- `qts.registry.symbol_resolution.StaticSymbolResolver.is_supported_symbol`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/symbol_resolution.py:43`
  - 说明：Perform is_supported_symbol.
  - 直接调用：`self._normalize_symbol`
  - 可解析内部调用：`qts.backtest.config.BacktestRunConfig._normalize_symbol`, `qts.data.historical.catalog.HistoricalCatalogLoadConfig._normalize_symbol`, `qts.registry.instrument_registry.InstrumentRegistry._normalize_symbol`, `qts.registry.symbol_resolution.StaticSymbolResolver._normalize_symbol`
- `qts.registry.symbol_resolution.StaticSymbolResolver.instrument_id_for_symbol`
  - 类型：`method`
  - 位置：`backend/src/qts/registry/symbol_resolution.py:47`
  - 说明：Perform instrument_id_for_symbol.
  - 直接调用：`ValueError`, `self._normalize_symbol`
  - 可解析内部调用：`qts.backtest.config.BacktestRunConfig._normalize_symbol`, `qts.data.historical.catalog.HistoricalCatalogLoadConfig._normalize_symbol`, `qts.registry.instrument_registry.InstrumentRegistry._normalize_symbol`, `qts.registry.symbol_resolution.StaticSymbolResolver._normalize_symbol`
- `qts.registry.symbol_resolution.StaticSymbolResolver._normalize_symbol`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/registry/symbol_resolution.py:56`
  - 说明：Perform _normalize_symbol.
  - 直接调用：`ValueError`, `symbol.strip`, `symbol.strip.upper`
  - 可解析内部调用：无

### `backend/src/qts/risk/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/risk/config.py`

- `qts.risk.config.RiskRuleConfig`
  - 类型：`class`
  - 位置：`backend/src/qts/risk/config.py:10`
  - 说明：One configured risk rule.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.risk.config.RiskRuleConfig.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/risk/config.py:17`
  - 说明：Perform __post_init__.
  - 直接调用：`ValueError`, `self.name.strip`, `self.rule_id.strip`
  - 可解析内部调用：无
- `qts.risk.config.RiskConfig`
  - 类型：`class`
  - 位置：`backend/src/qts/risk/config.py:26`
  - 说明：Account/strategy/product risk configuration.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.risk.config.RiskConfig.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/risk/config.py:35`
  - 说明：Perform __post_init__.
  - 直接调用：`Decimal`, `ValueError`, `self.account_id.strip`
  - 可解析内部调用：无

### `backend/src/qts/risk/kill_switch.py`

- `qts.risk.kill_switch.KillSwitchScopeType`
  - 类型：`class`
  - 位置：`backend/src/qts/risk/kill_switch.py:12`
  - 说明：Supported kill-switch scopes.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.risk.kill_switch.KillSwitchScope`
  - 类型：`class`
  - 位置：`backend/src/qts/risk/kill_switch.py:22`
  - 说明：Kill-switch scope identity.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.risk.kill_switch.KillSwitchScope.global_scope`
  - 类型：`classmethod`
  - 位置：`backend/src/qts/risk/kill_switch.py:29`
  - 说明：Perform global_scope.
  - 直接调用：`cls`
  - 可解析内部调用：无
- `qts.risk.kill_switch.KillSwitchScope.account`
  - 类型：`classmethod`
  - 位置：`backend/src/qts/risk/kill_switch.py:34`
  - 说明：Perform account.
  - 直接调用：`cls`
  - 可解析内部调用：无
- `qts.risk.kill_switch.KillSwitchScope.strategy`
  - 类型：`classmethod`
  - 位置：`backend/src/qts/risk/kill_switch.py:39`
  - 说明：Perform strategy.
  - 直接调用：`cls`
  - 可解析内部调用：无
- `qts.risk.kill_switch.KillSwitchScope.broker`
  - 类型：`classmethod`
  - 位置：`backend/src/qts/risk/kill_switch.py:44`
  - 说明：Perform broker.
  - 直接调用：`cls`
  - 可解析内部调用：无
- `qts.risk.kill_switch.KillSwitchScope.reason_code`
  - 类型：`method`
  - 位置：`backend/src/qts/risk/kill_switch.py:48`
  - 说明：Perform reason_code.
  - 直接调用：`self.scope_type.value.upper`
  - 可解析内部调用：无
- `qts.risk.kill_switch.KillSwitchState`
  - 类型：`class`
  - 位置：`backend/src/qts/risk/kill_switch.py:54`
  - 说明：Kill-switch activation state.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.risk.kill_switch.KillSwitchRegistry`
  - 类型：`class`
  - 位置：`backend/src/qts/risk/kill_switch.py:62`
  - 说明：Auditable in-memory kill-switch registry.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.risk.kill_switch.KillSwitchRegistry.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/risk/kill_switch.py:65`
  - 说明：Perform init.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.risk.kill_switch.KillSwitchRegistry.activate`
  - 类型：`method`
  - 位置：`backend/src/qts/risk/kill_switch.py:68`
  - 说明：Perform activate.
  - 直接调用：`KillSwitchState`, `ValueError`, `reason.strip`
  - 可解析内部调用：`qts.risk.kill_switch.KillSwitchState`
- `qts.risk.kill_switch.KillSwitchRegistry.deactivate`
  - 类型：`method`
  - 位置：`backend/src/qts/risk/kill_switch.py:76`
  - 说明：Perform deactivate.
  - 直接调用：`KillSwitchState`, `ValueError`, `reason.strip`
  - 可解析内部调用：`qts.risk.kill_switch.KillSwitchState`
- `qts.risk.kill_switch.KillSwitchRegistry.check_order`
  - 类型：`method`
  - 位置：`backend/src/qts/risk/kill_switch.py:84`
  - 说明：Perform check_order.
  - 直接调用：`RiskDecision.approve`, `RiskDecision.rejected`, `self._matching_scopes`, `self._states.get`, `state.scope.reason_code`
  - 可解析内部调用：`qts.domain.risk.decision.RiskDecision.approve`, `qts.domain.risk.decision.RiskDecision.rejected`, `qts.risk.kill_switch.KillSwitchRegistry._matching_scopes`, `qts.risk.kill_switch.KillSwitchScope.reason_code`, `qts.runtime.mailbox.Mailbox.get`
- `qts.risk.kill_switch.KillSwitchRegistry._matching_scopes`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/risk/kill_switch.py:105`
  - 说明：Perform matching scopes.
  - 直接调用：`KillSwitchScope.account`, `KillSwitchScope.broker`, `KillSwitchScope.global_scope`, `KillSwitchScope.strategy`, `scopes.append`, `tuple`
  - 可解析内部调用：`qts.indicators.rolling.RollingWindow.append`, `qts.risk.kill_switch.KillSwitchScope.account`, `qts.risk.kill_switch.KillSwitchScope.broker`, `qts.risk.kill_switch.KillSwitchScope.global_scope`, `qts.risk.kill_switch.KillSwitchScope.strategy`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`

### `backend/src/qts/risk/margin/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/risk/risk_engine.py`

- `qts.risk.risk_engine.RiskEngine`
  - 类型：`class`
  - 位置：`backend/src/qts/risk/risk_engine.py:11`
  - 说明：Apply risk rules in order and return the first rejection.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.risk.risk_engine.RiskEngine.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/risk/risk_engine.py:14`
  - 说明：Perform __init__.
  - 直接调用：`tuple`
  - 可解析内部调用：无
- `qts.risk.risk_engine.RiskEngine.check`
  - 类型：`method`
  - 位置：`backend/src/qts/risk/risk_engine.py:18`
  - 说明：Perform check.
  - 直接调用：`RiskDecision.approve`, `rule.check`
  - 可解析内部调用：`qts.domain.risk.decision.RiskDecision.approve`, `qts.quality.guardrails.BacktestEngineCohesionRule.check`, `qts.quality.guardrails.BacktestInputCohesionRule.check`, `qts.quality.guardrails.BacktestRunnerCohesionRule.check`, `qts.quality.guardrails.BrokerSpecificRule.check`, `qts.quality.guardrails.GuardrailSuite.check`, `qts.quality.guardrails.ImportBoundaryRule.check`, `qts.quality.guardrails.OOPHelperOwnershipRule.check`, `qts.quality.guardrails.OOPPublicFactoryRule.check`, `qts.quality.guardrails.ProductSpecificRule.check`, `qts.quality.guardrails.Rule.check`, `qts.quality.guardrails.SharedCapabilityRule.check`, `qts.quality.guardrails.StrategySdkPublicSurfaceRule.check`, `qts.quality.guardrails.TestSupportRule.check`, `qts.risk.risk_engine.RiskEngine.check`, `qts.risk.rule.RiskRule.check`, `qts.risk.rules.max_notional.MaxNotionalRule.check`, `qts.risk.rules.max_order_qty.MaxOrderQuantityRule.check`, `qts.risk.rules.trading_session_rule.TradingSessionRule.check`

### `backend/src/qts/risk/rule.py`

- `qts.risk.rule.RiskRule`
  - 类型：`class`
  - 位置：`backend/src/qts/risk/rule.py:10`
  - 说明：A pre-trade risk rule.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.risk.rule.RiskRule.check`
  - 类型：`method`
  - 位置：`backend/src/qts/risk/rule.py:13`
  - 说明：Return an explicit risk decision.
  - 直接调用：无
  - 可解析内部调用：无

### `backend/src/qts/risk/rule_registry.py`

- `qts.risk.rule_registry.RiskRuleRegistry`
  - 类型：`class`
  - 位置：`backend/src/qts/risk/rule_registry.py:13`
  - 说明：Map configured rule names to executable risk rules.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.risk.rule_registry.RiskRuleRegistry.build`
  - 类型：`method`
  - 位置：`backend/src/qts/risk/rule_registry.py:16`
  - 说明：Perform build.
  - 直接调用：`KeyError`, `MaxNotionalRule`, `MaxOrderQuantityRule`, `self._param`
  - 可解析内部调用：`qts.risk.rule_registry.RiskRuleRegistry._param`, `qts.risk.rules.max_notional.MaxNotionalRule`, `qts.risk.rules.max_order_qty.MaxOrderQuantityRule`
- `qts.risk.rule_registry.RiskRuleRegistry._param`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/risk/rule_registry.py:25`
  - 说明：Perform _param.
  - 直接调用：`KeyError`
  - 可解析内部调用：无

### `backend/src/qts/risk/rules/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/risk/rules/max_notional.py`

- `qts.risk.rules.max_notional.MaxNotionalRule`
  - 类型：`class`
  - 位置：`backend/src/qts/risk/rules/max_notional.py:12`
  - 说明：Reject orders whose notional exceeds a fixed limit.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.risk.rules.max_notional.MaxNotionalRule.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/risk/rules/max_notional.py:17`
  - 说明：Perform __post_init__.
  - 直接调用：`Decimal`, `ValueError`
  - 可解析内部调用：无
- `qts.risk.rules.max_notional.MaxNotionalRule.check`
  - 类型：`method`
  - 位置：`backend/src/qts/risk/rules/max_notional.py:22`
  - 说明：Perform check.
  - 直接调用：`RiskDecision.approve`, `RiskDecision.rejected`
  - 可解析内部调用：`qts.domain.risk.decision.RiskDecision.approve`, `qts.domain.risk.decision.RiskDecision.rejected`

### `backend/src/qts/risk/rules/max_order_qty.py`

- `qts.risk.rules.max_order_qty.MaxOrderQuantityRule`
  - 类型：`class`
  - 位置：`backend/src/qts/risk/rules/max_order_qty.py:12`
  - 说明：Reject orders whose absolute quantity exceeds a fixed limit.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.risk.rules.max_order_qty.MaxOrderQuantityRule.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/risk/rules/max_order_qty.py:17`
  - 说明：Perform __post_init__.
  - 直接调用：`Decimal`, `ValueError`
  - 可解析内部调用：无
- `qts.risk.rules.max_order_qty.MaxOrderQuantityRule.check`
  - 类型：`method`
  - 位置：`backend/src/qts/risk/rules/max_order_qty.py:22`
  - 说明：Perform check.
  - 直接调用：`RiskDecision.approve`, `RiskDecision.rejected`
  - 可解析内部调用：`qts.domain.risk.decision.RiskDecision.approve`, `qts.domain.risk.decision.RiskDecision.rejected`

### `backend/src/qts/risk/rules/trading_session_rule.py`

- `qts.risk.rules.trading_session_rule.SessionLookup`
  - 类型：`class`
  - 位置：`backend/src/qts/risk/rules/trading_session_rule.py:13`
  - 说明：Calendar session lookup required by the rule.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.risk.rules.trading_session_rule.SessionLookup.session_for`
  - 类型：`method`
  - 位置：`backend/src/qts/risk/rules/trading_session_rule.py:16`
  - 说明：Return the internal market session for the date.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.risk.rules.trading_session_rule.TradingSessionRule`
  - 类型：`class`
  - 位置：`backend/src/qts/risk/rules/trading_session_rule.py:21`
  - 说明：Reject orders whose order time is outside the configured session.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.risk.rules.trading_session_rule.TradingSessionRule.check`
  - 类型：`method`
  - 位置：`backend/src/qts/risk/rules/trading_session_rule.py:28`
  - 说明：Perform check.
  - 直接调用：`RiskDecision.approve`, `RiskDecision.rejected`, `self.calendar_registry.session_for`, `session.interval.contains`
  - 可解析内部调用：`qts.core.time.TimeInterval.contains`, `qts.data.sessions.filter.SessionLookup.session_for`, `qts.domain.risk.decision.RiskDecision.approve`, `qts.domain.risk.decision.RiskDecision.rejected`, `qts.registry.calendar_registry.CalendarProvider.session_for`, `qts.registry.calendar_registry.CalendarRegistry.session_for`, `qts.registry.providers.comex_gold_calendar_provider.ComexGoldCalendarProvider.session_for`, `qts.registry.providers.exchange_calendar_provider.ExchangeCalendarProvider.session_for`, `qts.risk.rules.trading_session_rule.SessionLookup.session_for`

### `backend/src/qts/runtime/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/runtime/actor.py`

- `qts.runtime.actor.Actor`
  - 类型：`class`
  - 位置：`backend/src/qts/runtime/actor.py:8`
  - 说明：Base actor that handles messages serially through an ActorRef.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.actor.Actor.handle`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/actor.py:12`
  - 说明：Handle one message.
  - 直接调用：无
  - 可解析内部调用：无

### `backend/src/qts/runtime/actor_ref.py`

- `qts.runtime.actor_ref.ActorRef`
  - 类型：`class`
  - 位置：`backend/src/qts/runtime/actor_ref.py:12`
  - 说明：Message-only reference to an actor mailbox.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.actor_ref.ActorRef.tell`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/actor_ref.py:18`
  - 说明：Perform tell.
  - 直接调用：`self.mailbox.put`
  - 可解析内部调用：`qts.runtime.mailbox.Mailbox.put`
- `qts.runtime.actor_ref.ActorRef.process_one`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/actor_ref.py:22`
  - 说明：Perform process_one.
  - 直接调用：`self.actor.handle`, `self.mailbox.empty`, `self.mailbox.get`
  - 可解析内部调用：`qts.runtime.actor.Actor.handle`, `qts.runtime.actors.account_actor.AccountActor.handle`, `qts.runtime.actors.execution_actor.ExecutionActor.handle`, `qts.runtime.actors.market_data_actor.MarketDataActor.handle`, `qts.runtime.actors.order_manager_actor.OrderManagerActor.handle`, `qts.runtime.actors.signal_aggregator_actor.SignalAggregatorActor.handle`, `qts.runtime.actors.strategy_actor.StrategyActor.handle`, `qts.runtime.mailbox.Mailbox.empty`, `qts.runtime.mailbox.Mailbox.get`
- `qts.runtime.actor_ref.ActorRef.process_all`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/actor_ref.py:29`
  - 说明：Perform process_all.
  - 直接调用：`self.process_one`
  - 可解析内部调用：`qts.runtime.actor_ref.ActorRef.process_one`

### `backend/src/qts/runtime/actors/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/runtime/actors/account_actor.py`

- `qts.runtime.actors.account_actor.ApplyFill`
  - 类型：`class`
  - 位置：`backend/src/qts/runtime/actors/account_actor.py:19`
  - 说明：Message instructing AccountActor to apply a validated fill.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.actors.account_actor.AccountSnapshot`
  - 类型：`class`
  - 位置：`backend/src/qts/runtime/actors/account_actor.py:28`
  - 说明：Read-only account snapshot.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.actors.account_actor.AccountActor`
  - 类型：`class`
  - 位置：`backend/src/qts/runtime/actors/account_actor.py:35`
  - 说明：Owns account cash and position state.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.actors.account_actor.AccountActor.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/actors/account_actor.py:38`
  - 说明：Perform __init__.
  - 直接调用：`CashBook`, `FillIdempotencyStore`, `PositionBook`
  - 可解析内部调用：`qts.execution.idempotency.FillIdempotencyStore`, `qts.portfolio.cash_book.CashBook`, `qts.portfolio.position_book.PositionBook`
- `qts.runtime.actors.account_actor.AccountActor.handle`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/actors/account_actor.py:44`
  - 说明：Perform handle.
  - 直接调用：`TypeError`, `isinstance`, `self._apply_fill`, `type`
  - 可解析内部调用：`qts.runtime.actors.account_actor.AccountActor._apply_fill`
- `qts.runtime.actors.account_actor.AccountActor.snapshot`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/actors/account_actor.py:51`
  - 说明：Perform snapshot.
  - 直接调用：`AccountSnapshot`, `MappingProxyType`, `self._cash.balance`, `self._positions.snapshot`
  - 可解析内部调用：`qts.application.services.interfaces.AccountService.snapshot`, `qts.execution.idempotency.FillIdempotencyStore.snapshot`, `qts.execution.order_manager.OrderManager.snapshot`, `qts.indicators.rolling.RollingWindow.snapshot`, `qts.observability.metrics.MetricsRegistry.snapshot`, `qts.portfolio.cash_book.CashBook.balance`, `qts.portfolio.position_book.PositionBook.snapshot`, `qts.runtime.actors.account_actor.AccountActor.snapshot`, `qts.runtime.actors.account_actor.AccountSnapshot`
- `qts.runtime.actors.account_actor.AccountActor._apply_fill`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/actors/account_actor.py:58`
  - 说明：Perform _apply_fill.
  - 直接调用：`self._cash.apply_delta`, `self._fill_ids.mark_seen`, `self._positions.apply_delta`
  - 可解析内部调用：`qts.execution.idempotency.FillIdempotencyStore.mark_seen`, `qts.portfolio.cash_book.CashBook.apply_delta`, `qts.portfolio.position_book.PositionBook.apply_delta`

### `backend/src/qts/runtime/actors/execution_actor.py`

- `qts.runtime.actors.execution_actor.ExecutionAdapter`
  - 类型：`class`
  - 位置：`backend/src/qts/runtime/actors/execution_actor.py:15`
  - 说明：Execution boundary contract used by the actor.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.actors.execution_actor.ExecutionAdapter.execute_market_order`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/actors/execution_actor.py:18`
  - 说明：Execute a market order.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.actors.execution_actor.OrderExecutionRequest`
  - 类型：`class`
  - 位置：`backend/src/qts/runtime/actors/execution_actor.py:30`
  - 说明：Message requesting order execution.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.actors.execution_actor.ExecutionActor`
  - 类型：`class`
  - 位置：`backend/src/qts/runtime/actors/execution_actor.py:38`
  - 说明：Actor wrapper for an order execution adapter or simulator.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.actors.execution_actor.ExecutionActor.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/actors/execution_actor.py:41`
  - 说明：Perform init.
  - 直接调用：`SimulatedBroker`
  - 可解析内部调用：`qts.execution.simulator.simulated_broker.SimulatedBroker`
- `qts.runtime.actors.execution_actor.ExecutionActor.handle`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/actors/execution_actor.py:50`
  - 说明：Perform handle.
  - 直接调用：`TypeError`, `isinstance`, `self._execution_adapter.execute_market_order`, `self._order_manager_ref.tell`, `type`
  - 可解析内部调用：`qts.execution.simulator.backtest_execution_adapter.BacktestExecutionAdapter.execute_market_order`, `qts.execution.simulator.simulated_broker.SimulatedBroker.execute_market_order`, `qts.runtime.actor_ref.ActorRef.tell`, `qts.runtime.actors.execution_actor.ExecutionAdapter.execute_market_order`

### `backend/src/qts/runtime/actors/market_data_actor.py`

- `qts.runtime.actors.market_data_actor.MarketDataEvent`
  - 类型：`class`
  - 位置：`backend/src/qts/runtime/actors/market_data_actor.py:29`
  - 说明：Normalized market data payload accepted by MarketDataActor.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.actors.market_data_actor.SubscribeMarketData`
  - 类型：`class`
  - 位置：`backend/src/qts/runtime/actors/market_data_actor.py:36`
  - 说明：Message requesting strategy market data fan-out.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.actors.market_data_actor.SubscribeMarketData.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/actors/market_data_actor.py:44`
  - 说明：Perform __post_init__.
  - 直接调用：`ValueError`, `self.subscriber_id.strip`, `self.timeframe.strip`
  - 可解析内部调用：无
- `qts.runtime.actors.market_data_actor.MarketDataActor`
  - 类型：`class`
  - 位置：`backend/src/qts/runtime/actors/market_data_actor.py:52`
  - 说明：Actor boundary for normalized market data events.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.actors.market_data_actor.MarketDataActor.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/actors/market_data_actor.py:55`
  - 说明：Perform __init__.
  - 直接调用：`BarAggregationPipeline`, `Timeframe.parse`, `ValueError`, `set`, `tuple`
  - 可解析内部调用：`qts.data.bars.pipeline.BarAggregationPipeline`, `qts.data.bars.timeframe.Timeframe.parse`
- `qts.runtime.actors.market_data_actor.MarketDataActor.handle`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/actors/market_data_actor.py:79`
  - 说明：Perform handle.
  - 直接调用：`RuntimeError`, `TypeError`, `isinstance`, `self._aggregation_pipeline.aggregate`, `self._publish`, `self._publish_to_logical_subscribers`, `self._subscribe`, `type`
  - 可解析内部调用：`qts.data.bars.pipeline.BarAggregationPipeline.aggregate`, `qts.runtime.actors.market_data_actor.MarketDataActor._publish`, `qts.runtime.actors.market_data_actor.MarketDataActor._publish_to_logical_subscribers`, `qts.runtime.actors.market_data_actor.MarketDataActor._subscribe`
- `qts.runtime.actors.market_data_actor.MarketDataActor.logical_subscription_count`
  - 类型：`property`
  - 位置：`backend/src/qts/runtime/actors/market_data_actor.py:102`
  - 说明：Perform logical_subscription_count.
  - 直接调用：`len`
  - 可解析内部调用：无
- `qts.runtime.actors.market_data_actor.MarketDataActor.physical_subscription_count`
  - 类型：`property`
  - 位置：`backend/src/qts/runtime/actors/market_data_actor.py:107`
  - 说明：Perform physical_subscription_count.
  - 直接调用：`len`
  - 可解析内部调用：无
- `qts.runtime.actors.market_data_actor.MarketDataActor._subscribe`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/actors/market_data_actor.py:111`
  - 说明：Perform _subscribe.
  - 直接调用：`FeedSubscription`, `LogicalSubscription`, `logical_key`, `plan_physical_subscription`, `self._feed.subscribe`, `self._logical_subscribers.setdefault`, `self._physical_subscriptions.add`, `self._source_timeframe_by_logical.setdefault`, `self._subscription_id`
  - 可解析内部调用：`qts.application.services.strategy_service.StrategyLifecycleService.add`, `qts.data.historical.service.HistoricalMarketDataService.subscribe`, `qts.data.live.adapter.LiveFeedAdapter.subscribe`, `qts.data.live.adapter.MarketDataAdapter.subscribe`, `qts.data.live.adapter.ReplayMarketDataAdapter.subscribe`, `qts.data.live.events.FeedSubscription`, `qts.data.live.fake_adapter.FakeLiveFeedAdapter.subscribe`, `qts.data.subscriptions.LogicalSubscription`, `qts.data.subscriptions.logical_key`, `qts.data.subscriptions.plan_physical_subscription`, `qts.runtime.actors.market_data_actor.MarketDataActor._subscription_id`, `qts.strategy_sdk.context.StrategyContext.subscribe`, `qts.strategy_sdk.subscription_registry.StrategySubscriptionRegistry.subscribe`
- `qts.runtime.actors.market_data_actor.MarketDataActor._publish_to_logical_subscribers`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/actors/market_data_actor.py:142`
  - 说明：Perform _publish_to_logical_subscribers.
  - 直接调用：`RuntimeError`, `isinstance`, `self._aggregation_pipeline.aggregate_logical`, `self._logical_subscribers.items`, `self._publish`, `self._publish_to`, `subscribers.values`
  - 可解析内部调用：`qts.data.bars.pipeline.BarAggregationPipeline.aggregate_logical`, `qts.runtime.actors.market_data_actor.MarketDataActor._publish`, `qts.runtime.actors.market_data_actor.MarketDataActor._publish_to`
- `qts.runtime.actors.market_data_actor.MarketDataActor._publish`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/actors/market_data_actor.py:169`
  - 说明：Perform _publish.
  - 直接调用：`subscriber.tell`
  - 可解析内部调用：`qts.runtime.actor_ref.ActorRef.tell`
- `qts.runtime.actors.market_data_actor.MarketDataActor._publish_to`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/runtime/actors/market_data_actor.py:175`
  - 说明：Perform _publish_to.
  - 直接调用：`subscriber.tell`
  - 可解析内部调用：`qts.runtime.actor_ref.ActorRef.tell`
- `qts.runtime.actors.market_data_actor.MarketDataActor._subscription_id`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/runtime/actors/market_data_actor.py:181`
  - 说明：Perform _subscription_id.
  - 直接调用：`join`
  - 可解析内部调用：无

### `backend/src/qts/runtime/actors/order_manager_actor.py`

- `qts.runtime.actors.order_manager_actor.SubmitOrder`
  - 类型：`class`
  - 位置：`backend/src/qts/runtime/actors/order_manager_actor.py:19`
  - 说明：Message to submit an approved order to an execution actor.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.actors.order_manager_actor.OrderManagerActor`
  - 类型：`class`
  - 位置：`backend/src/qts/runtime/actors/order_manager_actor.py:28`
  - 说明：Actor-owned OrderManager wrapper.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.actors.order_manager_actor.OrderManagerActor.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/actors/order_manager_actor.py:31`
  - 说明：Perform __init__.
  - 直接调用：`OrderManager`, `dict`
  - 可解析内部调用：`qts.execution.order_manager.OrderManager`
- `qts.runtime.actors.order_manager_actor.OrderManagerActor.handle`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/actors/order_manager_actor.py:45`
  - 说明：Perform handle.
  - 直接调用：`TypeError`, `isinstance`, `self._handle_report`, `self._handle_submit`, `type`
  - 可解析内部调用：`qts.runtime.actors.order_manager_actor.OrderManagerActor._handle_report`, `qts.runtime.actors.order_manager_actor.OrderManagerActor._handle_submit`
- `qts.runtime.actors.order_manager_actor.OrderManagerActor.get_order`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/actors/order_manager_actor.py:55`
  - 说明：Perform get_order.
  - 直接调用：`self._manager.get_order`
  - 可解析内部调用：`qts.execution.order_manager.OrderManager.get_order`, `qts.runtime.actors.order_manager_actor.OrderManagerActor.get_order`
- `qts.runtime.actors.order_manager_actor.OrderManagerActor.fills`
  - 类型：`property`
  - 位置：`backend/src/qts/runtime/actors/order_manager_actor.py:60`
  - 说明：Perform fills.
  - 直接调用：`tuple`
  - 可解析内部调用：无
- `qts.runtime.actors.order_manager_actor.OrderManagerActor.fill_count`
  - 类型：`property`
  - 位置：`backend/src/qts/runtime/actors/order_manager_actor.py:65`
  - 说明：Perform fill_count.
  - 直接调用：`len`
  - 可解析内部调用：无
- `qts.runtime.actors.order_manager_actor.OrderManagerActor.fills_since`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/actors/order_manager_actor.py:69`
  - 说明：Perform fills_since.
  - 直接调用：`tuple`
  - 可解析内部调用：无
- `qts.runtime.actors.order_manager_actor.OrderManagerActor.compact_for_streaming`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/actors/order_manager_actor.py:73`
  - 说明：Perform compact_for_streaming.
  - 直接调用：`self._fills.clear`, `self._manager.discard_terminal_order`
  - 可解析内部调用：`qts.execution.order_manager.OrderManager.discard_terminal_order`
- `qts.runtime.actors.order_manager_actor.OrderManagerActor._handle_submit`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/actors/order_manager_actor.py:79`
  - 说明：Perform _handle_submit.
  - 直接调用：`OrderExecutionRequest`, `self._execution_ref.tell`, `self._manager.create_order`, `self._manager.mark_sent`
  - 可解析内部调用：`qts.execution.order_manager.OrderManager.create_order`, `qts.execution.order_manager.OrderManager.mark_sent`, `qts.runtime.actor_ref.ActorRef.tell`, `qts.runtime.actors.execution_actor.OrderExecutionRequest`
- `qts.runtime.actors.order_manager_actor.OrderManagerActor._handle_report`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/actors/order_manager_actor.py:91`
  - 说明：Perform _handle_report.
  - 直接调用：`ApplyFill`, `Decimal`, `self._account_ref.tell`, `self._fills.append`, `self._manager.process_report`, `self._multiplier_by_instrument.get`
  - 可解析内部调用：`qts.execution.order_manager.OrderManager.process_report`, `qts.indicators.rolling.RollingWindow.append`, `qts.runtime.actor_ref.ActorRef.tell`, `qts.runtime.actors.account_actor.ApplyFill`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`, `qts.runtime.mailbox.Mailbox.get`

### `backend/src/qts/runtime/actors/signal_aggregator_actor.py`

- `qts.runtime.actors.signal_aggregator_actor.StrategySignalEvent`
  - 类型：`class`
  - 位置：`backend/src/qts/runtime/actors/signal_aggregator_actor.py:14`
  - 说明：Strategy intents emitted for one completed bar.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.actors.signal_aggregator_actor.AggregatedSignalBatch`
  - 类型：`class`
  - 位置：`backend/src/qts/runtime/actors/signal_aggregator_actor.py:22`
  - 说明：Aggregated intents ready for portfolio/risk/order flow.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.actors.signal_aggregator_actor.SignalAggregatorActor`
  - 类型：`class`
  - 位置：`backend/src/qts/runtime/actors/signal_aggregator_actor.py:29`
  - 说明：Boundary for combining strategy signals before order flow.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.actors.signal_aggregator_actor.SignalAggregatorActor.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/actors/signal_aggregator_actor.py:32`
  - 说明：Perform __init__.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.actors.signal_aggregator_actor.SignalAggregatorActor.handle`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/actors/signal_aggregator_actor.py:36`
  - 说明：Perform handle.
  - 直接调用：`AggregatedSignalBatch`, `TypeError`, `isinstance`, `self._result_ref.tell`, `type`
  - 可解析内部调用：`qts.runtime.actor_ref.ActorRef.tell`, `qts.runtime.actors.signal_aggregator_actor.AggregatedSignalBatch`

### `backend/src/qts/runtime/actors/strategy_actor.py`

- `qts.runtime.actors.strategy_actor.StrategyBarEvent`
  - 类型：`class`
  - 位置：`backend/src/qts/runtime/actors/strategy_actor.py:14`
  - 说明：Completed strategy-facing bar delivered to a strategy actor.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.actors.strategy_actor.StrategyBarResult`
  - 类型：`class`
  - 位置：`backend/src/qts/runtime/actors/strategy_actor.py:23`
  - 说明：New strategy intents emitted while handling one bar.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.actors.strategy_actor.StrategyFinalize`
  - 类型：`class`
  - 位置：`backend/src/qts/runtime/actors/strategy_actor.py:31`
  - 说明：Request strategy finalization.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.actors.strategy_actor.StrategyFinalized`
  - 类型：`class`
  - 位置：`backend/src/qts/runtime/actors/strategy_actor.py:36`
  - 说明：Strategy finalization completed.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.actors.strategy_actor.StrategyActor`
  - 类型：`class`
  - 位置：`backend/src/qts/runtime/actors/strategy_actor.py:42`
  - 说明：Actor-owned strategy instance and user-facing context.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.actors.strategy_actor.StrategyActor.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/actors/strategy_actor.py:45`
  - 说明：Perform __init__.
  - 直接调用：`self._strategy.initialize`
  - 可解析内部调用：`examples.strategies.gc_si_momentum.GcSiMomentumStrategy.initialize`, `examples.strategies.moving_average_cross.MovingAverageCross.initialize`, `qts.strategy_sdk.strategy.Strategy.initialize`
- `qts.runtime.actors.strategy_actor.StrategyActor.handle`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/actors/strategy_actor.py:58`
  - 说明：Perform handle.
  - 直接调用：`TypeError`, `isinstance`, `self._handle_bar`, `self._handle_finalize`, `type`
  - 可解析内部调用：`qts.runtime.actors.strategy_actor.StrategyActor._handle_bar`, `qts.runtime.actors.strategy_actor.StrategyActor._handle_finalize`
- `qts.runtime.actors.strategy_actor.StrategyActor._handle_bar`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/actors/strategy_actor.py:68`
  - 说明：Perform _handle_bar.
  - 直接调用：`StrategyBarResult`, `len`, `self._context.indicator.update_from_bar`, `self._result_ref.tell`, `self._strategy.on_bar`
  - 可解析内部调用：`examples.strategies.gc_si_momentum.GcSiMomentumStrategy.on_bar`, `examples.strategies.moving_average_cross.MovingAverageCross.on_bar`, `qts.runtime.actor_ref.ActorRef.tell`, `qts.runtime.actors.strategy_actor.StrategyBarResult`, `qts.strategy_sdk.indicators.IndicatorFactory.update_from_bar`, `qts.strategy_sdk.strategy.Strategy.on_bar`
- `qts.runtime.actors.strategy_actor.StrategyActor._handle_finalize`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/actors/strategy_actor.py:82`
  - 说明：Perform _handle_finalize.
  - 直接调用：`StrategyFinalized`, `len`, `self._result_ref.tell`, `self._strategy.finalize`
  - 可解析内部调用：`qts.backtest.report.StreamingBacktestArtifactWriter.finalize`, `qts.runtime.actor_ref.ActorRef.tell`, `qts.runtime.actors.strategy_actor.StrategyFinalized`, `qts.strategy_sdk.strategy.Strategy.finalize`

### `backend/src/qts/runtime/event_store.py`

- `qts.runtime.event_store.EventStore`
  - 类型：`class`
  - 位置：`backend/src/qts/runtime/event_store.py:15`
  - 说明：Append-only event store contract.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.event_store.EventStore.append`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/event_store.py:18`
  - 说明：Append an event to the store and return its sequence index.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.event_store.EventStore.replay`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/event_store.py:22`
  - 说明：Replay events from the store, optionally filtered by partition key.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.event_store.EventStore.by_correlation_id`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/event_store.py:26`
  - 说明：Replay all events with a given correlation identifier.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.event_store.InMemoryEventStore`
  - 类型：`class`
  - 位置：`backend/src/qts/runtime/event_store.py:31`
  - 说明：Deterministic append-only in-memory event store.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.event_store.InMemoryEventStore.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/event_store.py:34`
  - 说明：Perform __init__.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.event_store.InMemoryEventStore.append`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/event_store.py:38`
  - 说明：Perform append.
  - 直接调用：`len`, `self._events.append`
  - 可解析内部调用：`qts.indicators.rolling.RollingWindow.append`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`
- `qts.runtime.event_store.InMemoryEventStore.append_many`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/event_store.py:43`
  - 说明：Perform append_many.
  - 直接调用：`self.append`
  - 可解析内部调用：`qts.indicators.rolling.RollingWindow.append`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`
- `qts.runtime.event_store.InMemoryEventStore.replay`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/event_store.py:48`
  - 说明：Perform replay.
  - 直接调用：`tuple`
  - 可解析内部调用：无
- `qts.runtime.event_store.InMemoryEventStore.by_correlation_id`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/event_store.py:54`
  - 说明：Perform by_correlation_id.
  - 直接调用：`tuple`
  - 可解析内部调用：无
- `qts.runtime.event_store.FileEventStore`
  - 类型：`class`
  - 位置：`backend/src/qts/runtime/event_store.py:59`
  - 说明：JSONL event store for local deterministic recovery tests.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.event_store.FileEventStore.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/event_store.py:62`
  - 说明：Perform __init__.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.event_store.FileEventStore.append`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/event_store.py:66`
  - 说明：Perform append.
  - 直接调用：`handle.write`, `json.dumps`, `len`, `self._event_to_json`, `self._path.open`, `self._path.parent.mkdir`, `self.replay`
  - 可解析内部调用：`qts.backtest.report._NdjsonArtifact.write`, `qts.runtime.event_store.EventStore.replay`, `qts.runtime.event_store.FileEventStore._event_to_json`, `qts.runtime.event_store.FileEventStore.replay`, `qts.runtime.event_store.InMemoryEventStore.replay`
- `qts.runtime.event_store.FileEventStore.replay`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/event_store.py:76`
  - 说明：Perform replay.
  - 直接调用：`events.append`, `json.loads`, `line.strip`, `self._event_from_json`, `self._path.exists`, `self._path.open`, `tuple`
  - 可解析内部调用：`qts.indicators.rolling.RollingWindow.append`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore._event_from_json`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`
- `qts.runtime.event_store.FileEventStore.by_correlation_id`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/event_store.py:90`
  - 说明：Perform by_correlation_id.
  - 直接调用：`self.replay`, `tuple`
  - 可解析内部调用：`qts.runtime.event_store.EventStore.replay`, `qts.runtime.event_store.FileEventStore.replay`, `qts.runtime.event_store.InMemoryEventStore.replay`
- `qts.runtime.event_store.FileEventStore._event_to_json`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/runtime/event_store.py:95`
  - 说明：Perform _event_to_json.
  - 直接调用：`event.event_time.isoformat`
  - 可解析内部调用：无
- `qts.runtime.event_store.FileEventStore._event_from_json`
  - 类型：`staticmethod`
  - 位置：`backend/src/qts/runtime/event_store.py:108`
  - 说明：Perform _event_from_json.
  - 直接调用：`BaseEvent`, `CausationId`, `CorrelationId`, `EventId`, `datetime.fromisoformat`, `str`
  - 可解析内部调用：`qts.core.ids.CausationId`, `qts.core.ids.CorrelationId`, `qts.core.ids.EventId`, `qts.domain.events.event.BaseEvent`

### `backend/src/qts/runtime/live.py`

- `qts.runtime.live.LiveRuntimeState`
  - 类型：`class`
  - 位置：`backend/src/qts/runtime/live.py:12`
  - 说明：Live runtime lifecycle states.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.live.LiveMode`
  - 类型：`class`
  - 位置：`backend/src/qts/runtime/live.py:22`
  - 说明：Runtime mode with explicit live-trading permissions.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.live.LiveStartupConfig`
  - 类型：`class`
  - 位置：`backend/src/qts/runtime/live.py:31`
  - 说明：Startup guard inputs for live-capable runtime.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.live.LiveStartupDecision`
  - 类型：`class`
  - 位置：`backend/src/qts/runtime/live.py:43`
  - 说明：Result of startup guard validation.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.live.validate_live_startup`
  - 类型：`module_function`
  - 位置：`backend/src/qts/runtime/live.py:50`
  - 说明：Fail closed unless all live safety prerequisites are explicit.
  - 直接调用：`LiveStartupDecision`, `ValueError`, `join`
  - 可解析内部调用：`qts.runtime.live.LiveStartupDecision`
- `qts.runtime.live.LiveRuntimeStateMachine`
  - 类型：`class`
  - 位置：`backend/src/qts/runtime/live.py:97`
  - 说明：Mutable live runtime state machine.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.live.LiveRuntimeStateMachine.apply`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/live.py:102`
  - 说明：Perform apply.
  - 直接调用：`ValueError`, `_TRANSITIONS.get`, `_TRANSITIONS.get.get`
  - 可解析内部调用：`qts.runtime.mailbox.Mailbox.get`
- `qts.runtime.live.RuntimeOrderResult`
  - 类型：`class`
  - 位置：`backend/src/qts/runtime/live.py:112`
  - 说明：Result of live runtime order submission.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.live.LiveRuntime`
  - 类型：`class`
  - 位置：`backend/src/qts/runtime/live.py:121`
  - 说明：Small live-beta runtime wrapper over fake or real boundary adapters.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.live.LiveRuntime.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/live.py:124`
  - 说明：Perform init.
  - 直接调用：`LiveRuntimeStateMachine`
  - 可解析内部调用：`qts.runtime.live.LiveRuntimeStateMachine`
- `qts.runtime.live.LiveRuntime.state`
  - 类型：`property`
  - 位置：`backend/src/qts/runtime/live.py:130`
  - 说明：Perform state.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.live.LiveRuntime.feed`
  - 类型：`property`
  - 位置：`backend/src/qts/runtime/live.py:135`
  - 说明：Perform feed.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.live.LiveRuntime.start`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/live.py:139`
  - 说明：Perform start.
  - 直接调用：`self._machine.apply`
  - 可解析内部调用：`qts.execution.order_state_machine.OrderStateMachine.apply`, `qts.portfolio.accounting.fill_accounting.FillAccounting.apply`, `qts.runtime.live.LiveRuntimeStateMachine.apply`
- `qts.runtime.live.LiveRuntime.stop`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/live.py:144`
  - 说明：Perform stop.
  - 直接调用：`self._machine.apply`
  - 可解析内部调用：`qts.execution.order_state_machine.OrderStateMachine.apply`, `qts.portfolio.accounting.fill_accounting.FillAccounting.apply`, `qts.runtime.live.LiveRuntimeStateMachine.apply`
- `qts.runtime.live.LiveRuntime.pause`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/live.py:148`
  - 说明：Perform pause.
  - 直接调用：`self._machine.apply`
  - 可解析内部调用：`qts.execution.order_state_machine.OrderStateMachine.apply`, `qts.portfolio.accounting.fill_accounting.FillAccounting.apply`, `qts.runtime.live.LiveRuntimeStateMachine.apply`
- `qts.runtime.live.LiveRuntime.resume`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/live.py:152`
  - 说明：Perform resume.
  - 直接调用：`self._machine.apply`
  - 可解析内部调用：`qts.execution.order_state_machine.OrderStateMachine.apply`, `qts.portfolio.accounting.fill_accounting.FillAccounting.apply`, `qts.runtime.live.LiveRuntimeStateMachine.apply`
- `qts.runtime.live.LiveRuntime.degrade`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/live.py:156`
  - 说明：Perform degrade.
  - 直接调用：`self._machine.apply`
  - 可解析内部调用：`qts.execution.order_state_machine.OrderStateMachine.apply`, `qts.portfolio.accounting.fill_accounting.FillAccounting.apply`, `qts.runtime.live.LiveRuntimeStateMachine.apply`
- `qts.runtime.live.LiveRuntime.recover`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/live.py:160`
  - 说明：Perform recover.
  - 直接调用：`self._machine.apply`
  - 可解析内部调用：`qts.execution.order_state_machine.OrderStateMachine.apply`, `qts.portfolio.accounting.fill_accounting.FillAccounting.apply`, `qts.runtime.live.LiveRuntimeStateMachine.apply`
- `qts.runtime.live.LiveRuntime.submit_order`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/live.py:164`
  - 说明：Perform submit_order.
  - 直接调用：`RuntimeOrderResult`, `self._broker.submit_order`
  - 可解析内部调用：`qts.execution.broker.BrokerAdapter.submit_order`, `qts.execution.broker.FakeBrokerAdapter.submit_order`, `qts.runtime.live.LiveRuntime.submit_order`, `qts.runtime.live.RuntimeOrderResult`

### `backend/src/qts/runtime/mailbox.py`

- `qts.runtime.mailbox.Mailbox`
  - 类型：`class`
  - 位置：`backend/src/qts/runtime/mailbox.py:8`
  - 说明：Simple in-memory FIFO mailbox.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.mailbox.Mailbox.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/mailbox.py:11`
  - 说明：Perform __init__.
  - 直接调用：`deque`
  - 可解析内部调用：无
- `qts.runtime.mailbox.Mailbox.size`
  - 类型：`property`
  - 位置：`backend/src/qts/runtime/mailbox.py:16`
  - 说明：Perform size.
  - 直接调用：`len`
  - 可解析内部调用：无
- `qts.runtime.mailbox.Mailbox.put`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/mailbox.py:20`
  - 说明：Perform put.
  - 直接调用：`self._messages.append`
  - 可解析内部调用：`qts.indicators.rolling.RollingWindow.append`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`
- `qts.runtime.mailbox.Mailbox.get`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/mailbox.py:24`
  - 说明：Perform get.
  - 直接调用：`self._messages.popleft`
  - 可解析内部调用：无
- `qts.runtime.mailbox.Mailbox.empty`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/mailbox.py:28`
  - 说明：Perform empty.
  - 直接调用：无
  - 可解析内部调用：无

### `backend/src/qts/runtime/partitioning.py`

- `qts.runtime.partitioning.AccountPartitionPolicy`
  - 类型：`class`
  - 位置：`backend/src/qts/runtime/partitioning.py:11`
  - 说明：Partition live state and messages by internal account id.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.partitioning.AccountPartitionPolicy.partition_for`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/partitioning.py:14`
  - 说明：Perform partition_for.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.partitioning.AccountBrokerMapping`
  - 类型：`class`
  - 位置：`backend/src/qts/runtime/partitioning.py:20`
  - 说明：Boundary-only broker account mapping.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.partitioning.AccountBrokerMapping.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/partitioning.py:27`
  - 说明：Perform __post_init__.
  - 直接调用：`ValueError`, `self.broker_account_id.strip`
  - 可解析内部调用：无
- `qts.runtime.partitioning.AccountBrokerMapping.boundary_payload`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/partitioning.py:32`
  - 说明：Perform boundary_payload.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.partitioning.AccountRiskConfig`
  - 类型：`class`
  - 位置：`backend/src/qts/runtime/partitioning.py:41`
  - 说明：Per-account live risk limits.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.partitioning.AccountRiskConfig.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/partitioning.py:48`
  - 说明：Perform __post_init__.
  - 直接调用：`Decimal`, `ValueError`, `any`, `self.instrument_limits.values`
  - 可解析内部调用：无
- `qts.runtime.partitioning.AccountRiskConfig.limit_for`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/partitioning.py:55`
  - 说明：Perform limit_for.
  - 直接调用：`self.instrument_limits.get`
  - 可解析内部调用：`qts.runtime.mailbox.Mailbox.get`

### `backend/src/qts/runtime/router.py`

- `qts.runtime.router.RouteNotFoundError`
  - 类型：`class`
  - 位置：`backend/src/qts/runtime/router.py:10`
  - 说明：Raised when no actor route exists for a partition key.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.router.EventRouter`
  - 类型：`class`
  - 位置：`backend/src/qts/runtime/router.py:14`
  - 说明：Route messages to actor refs by a message-derived key.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.router.EventRouter.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/router.py:17`
  - 说明：Perform __init__.
  - 直接调用：`TypeError`, `callable`
  - 可解析内部调用：无
- `qts.runtime.router.EventRouter.register`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/router.py:24`
  - 说明：Perform register.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.router.EventRouter.route`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/router.py:28`
  - 说明：Perform route.
  - 直接调用：`RouteNotFoundError`, `actor_ref.tell`, `self._key_for`
  - 可解析内部调用：`qts.runtime.actor_ref.ActorRef.tell`, `qts.runtime.router.RouteNotFoundError`

### `backend/src/qts/runtime/state_recovery.py`

- `qts.runtime.state_recovery.StateSnapshot`
  - 类型：`class`
  - 位置：`backend/src/qts/runtime/state_recovery.py:10`
  - 说明：Serialized actor state snapshot envelope.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.state_recovery.StateSnapshot.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/state_recovery.py:17`
  - 说明：Perform __post_init__.
  - 直接调用：`ValueError`, `self.actor_id.strip`
  - 可解析内部调用：无
- `qts.runtime.state_recovery.InMemorySnapshotStore`
  - 类型：`class`
  - 位置：`backend/src/qts/runtime/state_recovery.py:25`
  - 说明：In-memory snapshot store for deterministic tests and local recovery.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.state_recovery.InMemorySnapshotStore.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/state_recovery.py:28`
  - 说明：Perform __init__.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.state_recovery.InMemorySnapshotStore.save`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/state_recovery.py:32`
  - 说明：Perform save.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.runtime.state_recovery.InMemorySnapshotStore.load`
  - 类型：`method`
  - 位置：`backend/src/qts/runtime/state_recovery.py:36`
  - 说明：Perform load.
  - 直接调用：`ValueError`, `actor_id.strip`, `self._snapshots.get`
  - 可解析内部调用：`qts.runtime.mailbox.Mailbox.get`

### `backend/src/qts/strategy_sdk/__init__.py`

- 无类/函数/方法符号。

### `backend/src/qts/strategy_sdk/asset_ref.py`

- `qts.strategy_sdk.asset_ref.AssetRef`
  - 类型：`class`
  - 位置：`backend/src/qts/strategy_sdk/asset_ref.py:13`
  - 说明：Lightweight strategy-facing reference to an internal instrument.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.strategy_sdk.asset_ref.AssetRef.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/asset_ref.py:20`
  - 说明：Perform __post_init__.
  - 直接调用：`MappingProxyType`, `ValueError`, `dict`, `object.__setattr__`, `self.symbol.strip`
  - 可解析内部调用：无
- `qts.strategy_sdk.asset_ref.AssetRef.__hash__`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/asset_ref.py:26`
  - 说明：Perform __hash__.
  - 直接调用：`hash`
  - 可解析内部调用：无

### `backend/src/qts/strategy_sdk/asset_resolver.py`

- `qts.strategy_sdk.asset_resolver.SymbolResolver`
  - 类型：`class`
  - 位置：`backend/src/qts/strategy_sdk/asset_resolver.py:15`
  - 说明：Platform-provided symbol resolution boundary.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.strategy_sdk.asset_resolver.SymbolResolver.resolve`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/asset_resolver.py:18`
  - 说明：Perform resolve.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.strategy_sdk.asset_resolver.FutureContractResolver`
  - 类型：`class`
  - 位置：`backend/src/qts/strategy_sdk/asset_resolver.py:21`
  - 说明：Platform-provided future chain resolution boundary.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.strategy_sdk.asset_resolver.FutureContractResolver.resolve_contract`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/asset_resolver.py:24`
  - 说明：Perform resolve contract.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.strategy_sdk.asset_resolver.ContinuousFutureResolver`
  - 类型：`class`
  - 位置：`backend/src/qts/strategy_sdk/asset_resolver.py:28`
  - 说明：Platform-provided continuous future reference boundary.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.strategy_sdk.asset_resolver.ContinuousFutureResolver.continuous_instrument_id`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/asset_resolver.py:31`
  - 说明：Perform continuous instrument id.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.strategy_sdk.asset_resolver.OptionContractRef`
  - 类型：`class`
  - 位置：`backend/src/qts/strategy_sdk/asset_resolver.py:34`
  - 说明：Read-only option contract reference returned by the platform.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.strategy_sdk.asset_resolver.OptionContractRef.instrument_id`
  - 类型：`property`
  - 位置：`backend/src/qts/strategy_sdk/asset_resolver.py:38`
  - 说明：Perform instrument id.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.strategy_sdk.asset_resolver.OptionContractResolver`
  - 类型：`class`
  - 位置：`backend/src/qts/strategy_sdk/asset_resolver.py:41`
  - 说明：Platform-provided option chain resolution boundary.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.strategy_sdk.asset_resolver.OptionContractResolver.find`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/asset_resolver.py:44`
  - 说明：Perform find.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.strategy_sdk.asset_resolver.StrategyAssetResolver`
  - 类型：`class`
  - 位置：`backend/src/qts/strategy_sdk/asset_resolver.py:54`
  - 说明：Resolve user input symbols/roots/options into stable `AssetRef` objects.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.strategy_sdk.asset_resolver.StrategyAssetResolver.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/asset_resolver.py:57`
  - 说明：Perform init.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.strategy_sdk.asset_resolver.StrategyAssetResolver.resolve_symbol`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/asset_resolver.py:68`
  - 说明：Perform resolve_symbol.
  - 直接调用：`AssetRef`, `RuntimeError`, `self.instrument_registry.resolve`
  - 可解析内部调用：`qts.application.strategy_lifecycle.StrategyRegistry.resolve`, `qts.registry.instrument_registry.InstrumentRegistry.resolve`, `qts.strategy_sdk.asset_ref.AssetRef`, `qts.strategy_sdk.asset_resolver.SymbolResolver.resolve`
- `qts.strategy_sdk.asset_resolver.StrategyAssetResolver.resolve_future`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/asset_resolver.py:75`
  - 说明：Perform resolve_future.
  - 直接调用：`AssetRef`, `RuntimeError`, `ValueError`, `isinstance`, `self.future_chain_registry.continuous_instrument_id`, `self.future_chain_registry.resolve_contract`
  - 可解析内部调用：`qts.registry.future_chain_registry.FutureChainRegistry.resolve_contract`, `qts.registry.future_roll.FutureRollRegistry.continuous_instrument_id`, `qts.registry.future_roll.FutureRollRegistry.resolve_contract`, `qts.strategy_sdk.asset_ref.AssetRef`, `qts.strategy_sdk.asset_resolver.ContinuousFutureResolver.continuous_instrument_id`, `qts.strategy_sdk.asset_resolver.FutureContractResolver.resolve_contract`
- `qts.strategy_sdk.asset_resolver.StrategyAssetResolver.resolve_option`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/asset_resolver.py:93`
  - 说明：Resolve a user-level option selection to a concrete option asset.
  - 直接调用：`AssetRef`, `KeyError`, `RuntimeError`, `self._resolve_underlying_option_id`, `self.option_chain_registry.find`, `str`
  - 可解析内部调用：`qts.registry.option_chain_registry.OptionChainRegistry.find`, `qts.strategy_sdk.asset_ref.AssetRef`, `qts.strategy_sdk.asset_resolver.OptionContractResolver.find`, `qts.strategy_sdk.asset_resolver.StrategyAssetResolver._resolve_underlying_option_id`
- `qts.strategy_sdk.asset_resolver.StrategyAssetResolver._resolve_underlying_option_id`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/asset_resolver.py:116`
  - 说明：Resolve an option underlying from user-facing SDK input.
  - 直接调用：`isinstance`, `self.resolve_symbol`
  - 可解析内部调用：`qts.strategy_sdk.asset_resolver.StrategyAssetResolver.resolve_symbol`

### `backend/src/qts/strategy_sdk/context.py`

- `qts.strategy_sdk.context.StrategyContext`
  - 类型：`class`
  - 位置：`backend/src/qts/strategy_sdk/context.py:30`
  - 说明：User-facing strategy facade for data, assets, targets, and subscriptions.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.strategy_sdk.context.StrategyContext.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/context.py:46`
  - 说明：Initialize internal SDK collaborators.
  - 直接调用：`StrategyAssetResolver`
  - 可解析内部调用：`qts.strategy_sdk.asset_resolver.StrategyAssetResolver`
- `qts.strategy_sdk.context.StrategyContext.intents`
  - 类型：`property`
  - 位置：`backend/src/qts/strategy_sdk/context.py:55`
  - 说明：Return target intents emitted by the strategy.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.strategy_sdk.context.StrategyContext.subscriptions`
  - 类型：`property`
  - 位置：`backend/src/qts/strategy_sdk/context.py:60`
  - 说明：Return market data subscriptions requested by the strategy.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.strategy_sdk.context.StrategyContext.symbol`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/context.py:64`
  - 说明：Resolve a user-facing symbol such as ``AAPL``.
  - 直接调用：`self._asset_resolver.resolve_symbol`
  - 可解析内部调用：`qts.strategy_sdk.asset_resolver.StrategyAssetResolver.resolve_symbol`
- `qts.strategy_sdk.context.StrategyContext.future`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/context.py:68`
  - 说明：Resolve a futures root to a selectable contract reference.
  - 直接调用：`self._asset_resolver.resolve_future`
  - 可解析内部调用：`qts.strategy_sdk.asset_resolver.StrategyAssetResolver.resolve_future`
- `qts.strategy_sdk.context.StrategyContext.option`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/context.py:72`
  - 说明：Resolve an option by underlying symbol/ref and contract attributes.
  - 直接调用：`self._asset_resolver.resolve_option`
  - 可解析内部调用：`qts.strategy_sdk.asset_resolver.StrategyAssetResolver.resolve_option`
- `qts.strategy_sdk.context.StrategyContext.target_percent`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/context.py:88`
  - 说明：Emit a portfolio-weight target for an asset.
  - 直接调用：`TargetIntent`, `self._intent_emitter.emit`
  - 可解析内部调用：`qts.data.live.fake_adapter.FakeLiveFeedAdapter.emit`, `qts.strategy_sdk.target.TargetIntent`, `qts.strategy_sdk.target_emitter.TargetIntentEmitter.emit`
- `qts.strategy_sdk.context.StrategyContext.target_quantity`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/context.py:94`
  - 说明：Emit a quantity target for an asset.
  - 直接调用：`TargetIntent`, `self._intent_emitter.emit`
  - 可解析内部调用：`qts.data.live.fake_adapter.FakeLiveFeedAdapter.emit`, `qts.strategy_sdk.target.TargetIntent`, `qts.strategy_sdk.target_emitter.TargetIntentEmitter.emit`
- `qts.strategy_sdk.context.StrategyContext.target_value`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/context.py:100`
  - 说明：Emit a notional value target for an asset.
  - 直接调用：`TargetIntent`, `self._intent_emitter.emit`
  - 可解析内部调用：`qts.data.live.fake_adapter.FakeLiveFeedAdapter.emit`, `qts.strategy_sdk.target.TargetIntent`, `qts.strategy_sdk.target_emitter.TargetIntentEmitter.emit`
- `qts.strategy_sdk.context.StrategyContext.close`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/context.py:106`
  - 说明：Emit a target that closes an asset position.
  - 直接调用：`TargetIntent`, `self._intent_emitter.emit`
  - 可解析内部调用：`qts.data.live.fake_adapter.FakeLiveFeedAdapter.emit`, `qts.strategy_sdk.target.TargetIntent`, `qts.strategy_sdk.target_emitter.TargetIntentEmitter.emit`
- `qts.strategy_sdk.context.StrategyContext.rebalance`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/context.py:112`
  - 说明：Emit one percent target per asset in ``weights``.
  - 直接调用：`self.target_percent`, `tuple`, `weights.items`
  - 可解析内部调用：`qts.strategy_sdk.context.StrategyContext.target_percent`
- `qts.strategy_sdk.context.StrategyContext.subscribe`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/context.py:116`
  - 说明：Subscribe to bars for an asset and timeframe.
  - 直接调用：`DataSubscription`, `self._subscription_registry.subscribe`
  - 可解析内部调用：`qts.data.historical.service.HistoricalMarketDataService.subscribe`, `qts.data.live.adapter.LiveFeedAdapter.subscribe`, `qts.data.live.adapter.MarketDataAdapter.subscribe`, `qts.data.live.adapter.ReplayMarketDataAdapter.subscribe`, `qts.data.live.fake_adapter.FakeLiveFeedAdapter.subscribe`, `qts.strategy_sdk.context.StrategyContext.subscribe`, `qts.strategy_sdk.subscription_registry.DataSubscription`, `qts.strategy_sdk.subscription_registry.StrategySubscriptionRegistry.subscribe`

### `backend/src/qts/strategy_sdk/data_view.py`

- `qts.strategy_sdk.data_view.DataView`
  - 类型：`class`
  - 位置：`backend/src/qts/strategy_sdk/data_view.py:16`
  - 说明：Time-sliced market data exposed to strategies.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.strategy_sdk.data_view.DataView.close`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/data_view.py:22`
  - 说明：Perform close.
  - 直接调用：`self.bar`
  - 可解析内部调用：`qts.strategy_sdk.data_view.DataView.bar`
- `qts.strategy_sdk.data_view.DataView.bar`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/data_view.py:26`
  - 说明：Perform bar.
  - 直接调用：`KeyError`, `self.history`
  - 可解析内部调用：`qts.backtest.historical_data_portal.HistoricalDataPortal.history`, `qts.strategy_sdk.data_view.DataView.history`
- `qts.strategy_sdk.data_view.DataView.history`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/data_view.py:33`
  - 说明：Perform history.
  - 直接调用：`ValueError`, `self.bars.get`, `tuple`
  - 可解析内部调用：`qts.runtime.mailbox.Mailbox.get`

### `backend/src/qts/strategy_sdk/factors.py`

- `qts.strategy_sdk.factors.FactorFactory`
  - 类型：`class`
  - 位置：`backend/src/qts/strategy_sdk/factors.py:11`
  - 说明：Factory for user-created factors.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.strategy_sdk.factors.FactorFactory.momentum`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/factors.py:14`
  - 说明：Perform momentum.
  - 直接调用：`MomentumFactor`
  - 可解析内部调用：`qts.factors.momentum.MomentumFactor`

### `backend/src/qts/strategy_sdk/indicators.py`

- `qts.strategy_sdk.indicators.AssetIndicator`
  - 类型：`class`
  - 位置：`backend/src/qts/strategy_sdk/indicators.py:14`
  - 说明：Indicator bound to a strategy asset reference.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.strategy_sdk.indicators.AssetIndicator.ready`
  - 类型：`property`
  - 位置：`backend/src/qts/strategy_sdk/indicators.py:21`
  - 说明：Perform ready.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.strategy_sdk.indicators.AssetIndicator.value`
  - 类型：`property`
  - 位置：`backend/src/qts/strategy_sdk/indicators.py:26`
  - 说明：Perform value.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.strategy_sdk.indicators.AssetIndicator.update`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/indicators.py:30`
  - 说明：Perform update.
  - 直接调用：`self.indicator.update`
  - 可解析内部调用：`qts.backtest.report.StreamingEquityMetrics.update`, `qts.data.bars.aggregator.BarAggregator.update`, `qts.indicators.price.ema.EMA.update`, `qts.indicators.price.sma.SMA.update`, `qts.strategy_sdk.indicators.AssetIndicator.update`
- `qts.strategy_sdk.indicators.IndicatorFactory`
  - 类型：`class`
  - 位置：`backend/src/qts/strategy_sdk/indicators.py:36`
  - 说明：Factory for user-created indicators.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.strategy_sdk.indicators.IndicatorFactory.sma`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/indicators.py:41`
  - 说明：Perform sma.
  - 直接调用：`AssetIndicator`, `SMA`, `self._created.append`
  - 可解析内部调用：`qts.indicators.price.sma.SMA`, `qts.indicators.rolling.RollingWindow.append`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`, `qts.strategy_sdk.indicators.AssetIndicator`
- `qts.strategy_sdk.indicators.IndicatorFactory.update_from_bar`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/indicators.py:47`
  - 说明：Perform update_from_bar.
  - 直接调用：`item.update`
  - 可解析内部调用：`qts.backtest.report.StreamingEquityMetrics.update`, `qts.data.bars.aggregator.BarAggregator.update`, `qts.indicators.price.ema.EMA.update`, `qts.indicators.price.sma.SMA.update`, `qts.strategy_sdk.indicators.AssetIndicator.update`

### `backend/src/qts/strategy_sdk/portfolio_view.py`

- `qts.strategy_sdk.portfolio_view.PortfolioPosition`
  - 类型：`class`
  - 位置：`backend/src/qts/strategy_sdk/portfolio_view.py:15`
  - 说明：Read-only position snapshot.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.strategy_sdk.portfolio_view.PortfolioView`
  - 类型：`class`
  - 位置：`backend/src/qts/strategy_sdk/portfolio_view.py:23`
  - 说明：Immutable user-facing portfolio snapshot.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.strategy_sdk.portfolio_view.PortfolioView.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/portfolio_view.py:30`
  - 说明：Perform __post_init__.
  - 直接调用：`MappingProxyType`, `dict`, `object.__setattr__`
  - 可解析内部调用：无
- `qts.strategy_sdk.portfolio_view.PortfolioView.position`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/portfolio_view.py:34`
  - 说明：Perform position.
  - 直接调用：`PortfolioPosition`, `self.positions.get`
  - 可解析内部调用：`qts.runtime.mailbox.Mailbox.get`, `qts.strategy_sdk.portfolio_view.PortfolioPosition`
- `qts.strategy_sdk.portfolio_view.PortfolioView.exposure`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/portfolio_view.py:38`
  - 说明：Perform exposure.
  - 直接调用：`self.position`
  - 可解析内部调用：`qts.strategy_sdk.portfolio_view.PortfolioView.position`
- `qts.strategy_sdk.portfolio_view.PortfolioView.weight`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/portfolio_view.py:42`
  - 说明：Perform weight.
  - 直接调用：`Decimal`, `self.exposure`
  - 可解析内部调用：`qts.strategy_sdk.portfolio_view.PortfolioView.exposure`

### `backend/src/qts/strategy_sdk/strategy.py`

- `qts.strategy_sdk.strategy.Strategy`
  - 类型：`class`
  - 位置：`backend/src/qts/strategy_sdk/strategy.py:6`
  - 说明：Base class for user strategies.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.strategy_sdk.strategy.Strategy.initialize`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/strategy.py:9`
  - 说明：Perform initialize.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.strategy_sdk.strategy.Strategy.on_bar`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/strategy.py:13`
  - 说明：Perform on_bar.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.strategy_sdk.strategy.Strategy.on_tick`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/strategy.py:17`
  - 说明：Perform on_tick.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.strategy_sdk.strategy.Strategy.on_timer`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/strategy.py:21`
  - 说明：Perform on_timer.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.strategy_sdk.strategy.Strategy.on_order_update`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/strategy.py:25`
  - 说明：Perform on_order_update.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.strategy_sdk.strategy.Strategy.on_fill`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/strategy.py:29`
  - 说明：Perform on_fill.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.strategy_sdk.strategy.Strategy.finalize`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/strategy.py:33`
  - 说明：Perform finalize.
  - 直接调用：无
  - 可解析内部调用：无

### `backend/src/qts/strategy_sdk/subscription_registry.py`

- `qts.strategy_sdk.subscription_registry.DataSubscription`
  - 类型：`class`
  - 位置：`backend/src/qts/strategy_sdk/subscription_registry.py:11`
  - 说明：Strategy-declared market data requirement.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.strategy_sdk.subscription_registry.DataSubscription.__post_init__`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/subscription_registry.py:18`
  - 说明：Perform __post_init__.
  - 直接调用：`ValueError`, `self.timeframe.strip`
  - 可解析内部调用：无
- `qts.strategy_sdk.subscription_registry.StrategySubscriptionRegistry`
  - 类型：`class`
  - 位置：`backend/src/qts/strategy_sdk/subscription_registry.py:26`
  - 说明：Own strategy subscriptions and enforce invariant validation.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.strategy_sdk.subscription_registry.StrategySubscriptionRegistry.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/subscription_registry.py:29`
  - 说明：Perform __init__.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.strategy_sdk.subscription_registry.StrategySubscriptionRegistry.subscriptions`
  - 类型：`property`
  - 位置：`backend/src/qts/strategy_sdk/subscription_registry.py:34`
  - 说明：Perform subscriptions.
  - 直接调用：`tuple`
  - 可解析内部调用：无
- `qts.strategy_sdk.subscription_registry.StrategySubscriptionRegistry.subscribe`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/subscription_registry.py:38`
  - 说明：Perform subscribe.
  - 直接调用：`self._subscriptions.append`
  - 可解析内部调用：`qts.indicators.rolling.RollingWindow.append`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`

### `backend/src/qts/strategy_sdk/target.py`

- `qts.strategy_sdk.target.TargetIntentType`
  - 类型：`class`
  - 位置：`backend/src/qts/strategy_sdk/target.py:12`
  - 说明：Supported target intent kinds.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.strategy_sdk.target.TargetIntent`
  - 类型：`class`
  - 位置：`backend/src/qts/strategy_sdk/target.py:22`
  - 说明：Strategy-emitted intent, later handled by platform risk/order flow.
  - 直接调用：无
  - 可解析内部调用：无

### `backend/src/qts/strategy_sdk/target_emitter.py`

- `qts.strategy_sdk.target_emitter.TargetIntentEmitter`
  - 类型：`class`
  - 位置：`backend/src/qts/strategy_sdk/target_emitter.py:8`
  - 说明：Collect and emit `TargetIntent` values for one strategy context.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.strategy_sdk.target_emitter.TargetIntentEmitter.__init__`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/target_emitter.py:11`
  - 说明：Perform __init__.
  - 直接调用：无
  - 可解析内部调用：无
- `qts.strategy_sdk.target_emitter.TargetIntentEmitter.intents`
  - 类型：`property`
  - 位置：`backend/src/qts/strategy_sdk/target_emitter.py:16`
  - 说明：Perform intents.
  - 直接调用：`tuple`
  - 可解析内部调用：无
- `qts.strategy_sdk.target_emitter.TargetIntentEmitter.emit`
  - 类型：`method`
  - 位置：`backend/src/qts/strategy_sdk/target_emitter.py:20`
  - 说明：Perform emit.
  - 直接调用：`self._intents.append`
  - 可解析内部调用：`qts.indicators.rolling.RollingWindow.append`, `qts.runtime.event_store.EventStore.append`, `qts.runtime.event_store.FileEventStore.append`, `qts.runtime.event_store.InMemoryEventStore.append`

### `backend/src/qts/workers/__init__.py`

- 无类/函数/方法符号。

### `examples/__init__.py`

- 无类/函数/方法符号。

### `examples/strategies/__init__.py`

- 无类/函数/方法符号。

### `examples/strategies/gc_si_momentum.py`

- `examples.strategies.gc_si_momentum.GcSiMomentumStrategy`
  - 类型：`class`
  - 位置：`examples/strategies/gc_si_momentum.py:12`
  - 说明：Simple moving-average momentum strategy for configured GC/SI symbols.
  - 直接调用：无
  - 可解析内部调用：无
- `examples.strategies.gc_si_momentum.GcSiMomentumStrategy.__init__`
  - 类型：`method`
  - 位置：`examples/strategies/gc_si_momentum.py:15`
  - 说明：Perform init.
  - 直接调用：`ValueError`, `tuple`
  - 可解析内部调用：无
- `examples.strategies.gc_si_momentum.GcSiMomentumStrategy.initialize`
  - 类型：`method`
  - 位置：`examples/strategies/gc_si_momentum.py:33`
  - 说明：Perform initialize.
  - 直接调用：`_asset_for_symbol`, `ctx.subscribe`, `tuple`
  - 可解析内部调用：`examples.strategies.gc_si_momentum._asset_for_symbol`, `qts.data.historical.service.HistoricalMarketDataService.subscribe`, `qts.data.live.adapter.LiveFeedAdapter.subscribe`, `qts.data.live.adapter.MarketDataAdapter.subscribe`, `qts.data.live.adapter.ReplayMarketDataAdapter.subscribe`, `qts.data.live.fake_adapter.FakeLiveFeedAdapter.subscribe`, `qts.strategy_sdk.context.StrategyContext.subscribe`, `qts.strategy_sdk.subscription_registry.StrategySubscriptionRegistry.subscribe`
- `examples.strategies.gc_si_momentum.GcSiMomentumStrategy.on_bar`
  - 类型：`method`
  - 位置：`examples/strategies/gc_si_momentum.py:38`
  - 说明：Perform on bar.
  - 直接调用：`Decimal`, `_average`, `ctx.close`, `ctx.data.history`, `ctx.target_quantity`, `len`
  - 可解析内部调用：`examples.strategies.gc_si_momentum._average`, `qts.backtest.historical_data_portal.HistoricalDataPortal.history`, `qts.backtest.report._NdjsonArtifact.close`, `qts.strategy_sdk.context.StrategyContext.close`, `qts.strategy_sdk.context.StrategyContext.target_quantity`, `qts.strategy_sdk.data_view.DataView.close`, `qts.strategy_sdk.data_view.DataView.history`
- `examples.strategies.gc_si_momentum._average`
  - 类型：`module_function`
  - 位置：`examples/strategies/gc_si_momentum.py:55`
  - 说明：Perform average.
  - 直接调用：`Decimal`, `len`, `sum`, `tuple`
  - 可解析内部调用：无
- `examples.strategies.gc_si_momentum._asset_for_symbol`
  - 类型：`module_function`
  - 位置：`examples/strategies/gc_si_momentum.py:60`
  - 说明：Perform asset for symbol.
  - 直接调用：`ctx.future`, `ctx.symbol`
  - 可解析内部调用：`qts.factors.momentum.FactorAsset.symbol`, `qts.strategy_sdk.context.StrategyContext.future`, `qts.strategy_sdk.context.StrategyContext.symbol`

### `examples/strategies/moving_average_cross.py`

- `examples.strategies.moving_average_cross.MovingAverageCross`
  - 类型：`class`
  - 位置：`examples/strategies/moving_average_cross.py:8`
  - 说明：Perform MovingAverageCross.
  - 直接调用：无
  - 可解析内部调用：无
- `examples.strategies.moving_average_cross.MovingAverageCross.initialize`
  - 类型：`method`
  - 位置：`examples/strategies/moving_average_cross.py:9`
  - 说明：Perform initialize.
  - 直接调用：`ctx.indicator.sma`, `ctx.symbol`
  - 可解析内部调用：`qts.factors.momentum.FactorAsset.symbol`, `qts.strategy_sdk.context.StrategyContext.symbol`, `qts.strategy_sdk.indicators.IndicatorFactory.sma`
- `examples.strategies.moving_average_cross.MovingAverageCross.on_bar`
  - 类型：`method`
  - 位置：`examples/strategies/moving_average_cross.py:14`
  - 说明：Perform on bar.
  - 直接调用：`Decimal`, `ctx.close`, `ctx.data.close`, `ctx.target_percent`, `self.fast.update`, `self.slow.update`
  - 可解析内部调用：`qts.backtest.report.StreamingEquityMetrics.update`, `qts.backtest.report._NdjsonArtifact.close`, `qts.data.bars.aggregator.BarAggregator.update`, `qts.indicators.price.ema.EMA.update`, `qts.indicators.price.sma.SMA.update`, `qts.strategy_sdk.context.StrategyContext.close`, `qts.strategy_sdk.context.StrategyContext.target_percent`, `qts.strategy_sdk.data_view.DataView.close`, `qts.strategy_sdk.indicators.AssetIndicator.update`

### `scripts/__init__.py`

- 无类/函数/方法符号。

### `scripts/bootstrap.py`

- `scripts.bootstrap.main`
  - 类型：`module_function`
  - 位置：`scripts/bootstrap.py:11`
  - 说明：Perform main.
  - 直接调用：`Path`, `bootstrap_local`
  - 可解析内部调用：`qts.load.bootstrap.bootstrap_local`

### `scripts/ibkr_collect_environment_evidence.py`

- `scripts.ibkr_collect_environment_evidence.collect_environment_evidence`
  - 类型：`module_function`
  - 位置：`scripts/ibkr_collect_environment_evidence.py:14`
  - 说明：Run the legacy script entrypoint through the command module.
  - 直接调用：`_collect_environment_evidence`
  - 可解析内部调用：无
- `scripts.ibkr_collect_environment_evidence.main`
  - 类型：`module_function`
  - 位置：`scripts/ibkr_collect_environment_evidence.py:20`
  - 说明：Run IBKR environment evidence collection command.
  - 直接调用：`_command_main`
  - 可解析内部调用：无

### `scripts/ibkr_paper_order_lifecycle_drill.py`

- `scripts.ibkr_paper_order_lifecycle_drill.run_paper_order_lifecycle_drill`
  - 类型：`module_function`
  - 位置：`scripts/ibkr_paper_order_lifecycle_drill.py:14`
  - 说明：Run the command function through the legacy script entrypoint.
  - 直接调用：`_run_paper_order_lifecycle_drill`
  - 可解析内部调用：无
- `scripts.ibkr_paper_order_lifecycle_drill.main`
  - 类型：`module_function`
  - 位置：`scripts/ibkr_paper_order_lifecycle_drill.py:20`
  - 说明：Run paper order lifecycle drill command.
  - 直接调用：`_command_main`
  - 可解析内部调用：无

### `scripts/run_api.py`

- `scripts.run_api.main`
  - 类型：`module_function`
  - 位置：`scripts/run_api.py:9`
  - 说明：Start the QTS FastAPI application server.
  - 直接调用：`uvicorn.run`
  - 可解析内部调用：`qts.api.services.command_idempotency.CommandIdempotencyStore.run`, `qts.backtest.actor_loop.BacktestActorLoop.run`

### `scripts/run_backtest.py`

- `scripts.run_backtest.main`
  - 类型：`module_function`
  - 位置：`scripts/run_backtest.py:14`
  - 说明：Perform main.
  - 直接调用：`Path`, `argparse.ArgumentParser`, `json.dumps`, `json.loads`, `parser.add_argument`, `parser.parse_args`, `print`, `run.summary_path.read_text`, `run.summary_path.write_text`, `run_backtest`, `time.perf_counter`
  - 可解析内部调用：`qts.backtest.runner.run_backtest`

### `scripts/run_load.py`

- `scripts.run_load.main`
  - 类型：`module_function`
  - 位置：`scripts/run_load.py:13`
  - 说明：Perform main.
  - 直接调用：`Decimal`, `InstrumentId`, `SyntheticMarketDataConfig`, `datetime`, `generate_bars`, `len`, `print`
  - 可解析内部调用：`qts.core.ids.InstrumentId`, `qts.load.synthetic_market_data.SyntheticMarketDataConfig`, `qts.load.synthetic_market_data.generate_bars`

### `scripts/run_paper.py`

- `scripts.run_paper.main`
  - 类型：`module_function`
  - 位置：`scripts/run_paper.py:8`
  - 说明：Perform main.
  - 直接调用：`Decimal`, `PaperRuntimeConfig`, `print`, `start_paper`
  - 可解析内部调用：`qts.application.commands.start_paper.PaperRuntimeConfig`, `qts.application.commands.start_paper.start_paper`

### `scripts/run_paper_ibkr.py`

- `scripts.run_paper_ibkr.main`
  - 类型：`module_function`
  - 位置：`scripts/run_paper_ibkr.py:9`
  - 说明：Run the IBKR paper order lifecycle drill command.
  - 直接调用：`_run_paper_drill`
  - 可解析内部调用：无

### `scripts/run_worker.py`

- `scripts.run_worker.main`
  - 类型：`module_function`
  - 位置：`scripts/run_worker.py:7`
  - 说明：Emit compatibility-mode worker message for now.
  - 直接调用：`print`
  - 可解析内部调用：无

### `scripts/validate_historical.py`

- `scripts.validate_historical.main`
  - 类型：`module_function`
  - 位置：`scripts/validate_historical.py:15`
  - 说明：Perform main.
  - 直接调用：`HistoricalCatalog.from_legacy_root`, `Path`, `argparse.ArgumentParser`, `args.output_dir.mkdir`, `bool`, `catalog.datasets.items`, `datetime.now`, `datetime.now.isoformat`, `json.dumps`, `list`, `output_path.write_text`, `parser.add_argument`, `parser.parse_args`, `print`, `sample.stats.as_dict`, `str`, `tuple`, `validate_historical_sample`
  - 可解析内部调用：`qts.data.historical.catalog.HistoricalCatalog.from_legacy_root`, `qts.data.historical.csv_dataset.validate_historical_sample`, `qts.data.historical.validation.HistoricalCsvStats.as_dict`

### `scripts/verify_guardrails.py`

- 无类/函数/方法符号。

