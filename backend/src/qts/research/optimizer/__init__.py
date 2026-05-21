"""Parameter-sweep optimizer (sequential grid; factory and pipeline-driven)."""

from qts.research.optimizer.constraints import (
    ConstraintDecision,
    MetricConstraint,
    OptimizationConstraint,
)
from qts.research.optimizer.job import BarsFactory, OptimizationJob, StrategyFactory
from qts.research.optimizer.parameter_space import ParameterGrid, ParameterSpace
from qts.research.optimizer.pipeline import BacktestPipelineJob, BacktestPipelineRunner
from qts.research.optimizer.result import OptimizationResult
from qts.research.optimizer.runner import OptimizationRunner, extract_objective_from_manifest
from qts.research.optimizer.validation import (
    OptimizerValidationSummary,
    OptimizerValidationSummaryWriter,
    derive_capital_metrics,
)
from qts.research.optimizer.walk_forward import (
    BacktestWalkForwardValidationJob,
    BacktestWalkForwardValidationRunner,
    WalkForwardPlan,
    WalkForwardSplit,
    WalkForwardValidationResult,
    WalkForwardValidationSummary,
)

__all__ = [
    "BacktestWalkForwardValidationJob",
    "BacktestWalkForwardValidationRunner",
    "BacktestPipelineJob",
    "BacktestPipelineRunner",
    "BarsFactory",
    "ConstraintDecision",
    "MetricConstraint",
    "OptimizationJob",
    "OptimizationConstraint",
    "OptimizationResult",
    "OptimizationRunner",
    "OptimizerValidationSummary",
    "OptimizerValidationSummaryWriter",
    "ParameterGrid",
    "ParameterSpace",
    "StrategyFactory",
    "WalkForwardPlan",
    "WalkForwardSplit",
    "WalkForwardValidationResult",
    "WalkForwardValidationSummary",
    "derive_capital_metrics",
    "extract_objective_from_manifest",
]
