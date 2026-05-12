from qts.execution.simulator.fill_model import ImmediateFillModel
from qts.execution.simulator.simulated_broker import SimulatedBroker

__all__ = ["BacktestExecutionAdapter", "ImmediateFillModel", "SimulatedBroker"]


def __getattr__(name: str) -> object:
    """Lazily expose backtest-only adapter without importing backtest during runtime setup."""
    if name == "BacktestExecutionAdapter":
        from qts.execution.simulator.backtest_execution_adapter import BacktestExecutionAdapter

        return BacktestExecutionAdapter
    raise AttributeError(name)
