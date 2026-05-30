"""QTS-FINAL-008: runtime command/control-plane domain error taxonomy."""

from __future__ import annotations

import pytest
from qts.core.errors import QTSError, QTSRuntimeError
from qts.runtime.errors import (
    RuntimeCommandNotBound,
    RuntimeCommandRejected,
    RuntimeSafetyViolation,
)


def test_runtime_errors_are_runtime_qts_errors() -> None:
    for error in (RuntimeCommandNotBound, RuntimeCommandRejected, RuntimeSafetyViolation):
        assert issubclass(error, QTSRuntimeError)
        assert issubclass(error, QTSError)


def test_runtime_command_not_bound_is_raisable_and_catchable() -> None:
    with pytest.raises(RuntimeCommandNotBound, match="no runtime"):
        raise RuntimeCommandNotBound("no runtime bound")

    # Catchable through the runtime base for broad operator handling.
    with pytest.raises(QTSRuntimeError):
        raise RuntimeCommandRejected("rejected")


def test_runtime_safety_violation_distinct_from_command_errors() -> None:
    assert not issubclass(RuntimeSafetyViolation, RuntimeCommandNotBound)
    assert not issubclass(RuntimeCommandNotBound, RuntimeSafetyViolation)
