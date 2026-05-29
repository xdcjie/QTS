"""Autonomous research candidate selection and validation gates."""

from qts.research.selector.gauntlet import (
    CapacityGate,
    CorrelationGate,
    CostStressGate,
    DeflatedSharpeGate,
    FailureWindowVetoGate,
    GateDecision,
    NoLookaheadGate,
    PBOGate,
    ValidationGauntlet,
    ValidationGauntletResult,
    WalkForwardGate,
)
from qts.research.selector.multiplicity_adjustment import (
    CandidateStatistics,
    MultiplicityAdjustmentResult,
    ResearchMultiplicityAdjustment,
)
from qts.research.selector.selector import (
    CandidateSelector,
    RejectedCandidate,
    SelectedCandidate,
    SelectionPolicy,
    SelectionResult,
)

__all__ = [
    "CandidateSelector",
    "CandidateStatistics",
    "CapacityGate",
    "CorrelationGate",
    "CostStressGate",
    "DeflatedSharpeGate",
    "FailureWindowVetoGate",
    "GateDecision",
    "MultiplicityAdjustmentResult",
    "NoLookaheadGate",
    "PBOGate",
    "RejectedCandidate",
    "ResearchMultiplicityAdjustment",
    "SelectedCandidate",
    "SelectionPolicy",
    "SelectionResult",
    "ValidationGauntlet",
    "ValidationGauntletResult",
    "WalkForwardGate",
]
