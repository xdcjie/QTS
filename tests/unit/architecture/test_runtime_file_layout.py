"""Architecture checks for shared runtime file ownership."""

from __future__ import annotations


def test_shared_runtime_layout_exports_target_names() -> None:
    """Shared runtime concepts are available from their owning modules."""
    from qts.data.market_data_pipeline import MarketDataPipeline
    from qts.data.sources.replay_market_data_source import ReplayMarketDataSource
    from qts.data.sources.streaming_market_data_source import StreamingMarketDataSource
    from qts.execution.adapters.broker_execution_adapter import BrokerExecutionAdapter
    from qts.execution.adapters.simulated_execution_adapter import SimulatedExecutionAdapter
    from qts.reporting.backtest import BacktestReportWriter
    from qts.reporting.base import ReportWriter, RuntimeArtifactWriter
    from qts.reporting.broker_runtime import BrokerRuntimeEventReporter, BrokerRuntimeReportWriter
    from qts.runtime.config import BacktestRuntimeConfig, LiveRuntimeConfig, TradingRuntimeConfig
    from qts.runtime.execution_report_handler import ExecutionReportHandler
    from qts.runtime.intent_processing import OrderPlanBuilder, TargetIntentProcessor
    from qts.runtime.market_data_flow import MarketDataFlow
    from qts.runtime.sinks.backtest import BacktestRuntimeEventSink
    from qts.runtime.sinks.base import RuntimeEvent, RuntimeEventSink
    from qts.runtime.sinks.live import LiveRuntimeEventSink
    from qts.runtime.strategy_execution_pipeline import StrategyExecutionPipeline

    exported = {
        TradingRuntimeConfig,
        BacktestRuntimeConfig,
        LiveRuntimeConfig,
        ReplayMarketDataSource,
        StreamingMarketDataSource,
        MarketDataPipeline,
        MarketDataFlow,
        StrategyExecutionPipeline,
        TargetIntentProcessor,
        OrderPlanBuilder,
        SimulatedExecutionAdapter,
        BrokerExecutionAdapter,
        ExecutionReportHandler,
        RuntimeEvent,
        RuntimeEventSink,
        BacktestRuntimeEventSink,
        LiveRuntimeEventSink,
        ReportWriter,
        RuntimeArtifactWriter,
        BacktestReportWriter,
        BrokerRuntimeReportWriter,
        BrokerRuntimeEventReporter,
    }

    assert all(item.__name__ for item in exported)
