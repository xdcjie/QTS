"""Architecture checks for shared runtime file ownership."""

from __future__ import annotations

import inspect


def test_shared_runtime_layout_exports_target_names() -> None:
    """Shared runtime concepts are available from their owning modules."""
    from qts.data.market_data_pipeline import MarketDataPipeline
    from qts.data.sources.replay_market_data_source import ReplayMarketDataSource
    from qts.data.sources.streaming_market_data_source import StreamingMarketDataSource
    from qts.execution import ExecutionAdapter
    from qts.execution.adapters.broker_execution_adapter import BrokerExecutionAdapter
    from qts.execution.adapters.simulated_execution_adapter import SimulatedExecutionAdapter
    from qts.reporting.backtest import BacktestReportWriter
    from qts.reporting.base import ReportWriter, RuntimeArtifactWriter
    from qts.reporting.broker_runtime import BrokerRuntimeEventReporter, BrokerRuntimeReportWriter
    from qts.runtime.config import BacktestRuntimeConfig, BrokerRuntimeConfig, TradingRuntimeConfig
    from qts.runtime.execution_report_handler import ExecutionReportHandler
    from qts.runtime.intent_processing import OrderPlanBuilder, TargetIntentProcessor
    from qts.runtime.market_data_flow import MarketDataFlow
    from qts.runtime.sinks.backtest import BacktestRuntimeEventSink
    from qts.runtime.sinks.base import RuntimeEvent, RuntimeEventSink
    from qts.runtime.sinks.broker_runtime import BrokerRuntimeEventSink
    from qts.runtime.strategy_execution_pipeline import StrategyExecutionPipeline

    exported = {
        TradingRuntimeConfig,
        BacktestRuntimeConfig,
        BrokerRuntimeConfig,
        ReplayMarketDataSource,
        StreamingMarketDataSource,
        MarketDataPipeline,
        MarketDataFlow,
        StrategyExecutionPipeline,
        TargetIntentProcessor,
        OrderPlanBuilder,
        ExecutionAdapter,
        SimulatedExecutionAdapter,
        BrokerExecutionAdapter,
        ExecutionReportHandler,
        RuntimeEvent,
        RuntimeEventSink,
        BacktestRuntimeEventSink,
        BrokerRuntimeEventSink,
        ReportWriter,
        RuntimeArtifactWriter,
        BacktestReportWriter,
        BrokerRuntimeReportWriter,
        BrokerRuntimeEventReporter,
    }

    assert all(item.__name__ for item in exported)


def test_execution_adapter_protocol_is_owned_by_execution_layer() -> None:
    """Runtime actors use the execution-layer protocol, not broker request types."""
    import qts.runtime.actors.execution_actor as execution_actor_module
    from qts.execution import ExecutionAdapter

    assert ExecutionAdapter.__module__ == "qts.execution.execution_adapter"

    source = inspect.getsource(execution_actor_module)

    assert "class ExecutionAdapter" not in source
    assert "BrokerAdapter" not in source
    assert "BrokerOrderRequest" not in source
    assert "BrokerExecutionReport" not in source
    assert "submit_order(" not in source
