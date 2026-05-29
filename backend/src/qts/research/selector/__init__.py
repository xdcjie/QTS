"""Autonomous research candidate selection and validation gates."""

from qts.research.selector.gauntlet import (
    CapacityGate,
    CorrelationGate,
    CostStressGate,
    FailureWindowVetoGate,
    GateDecision,
    NoLookaheadGate,
    ValidationGauntlet,
    ValidationGauntletResult,
    WalkForwardGate,
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
    "CapacityGate",
    "CorrelationGate",
    "CostStressGate",
    "FailureWindowVetoGate",
    "GateDecision",
    "NoLookaheadGate",
    "RejectedCandidate",
    "SelectedCandidate",
    "SelectionPolicy",
    "SelectionResult",
    "ValidationGauntlet",
    "ValidationGauntletResult",
    "WalkForwardGate",
]
