"""Narrow port and state object for runtime safety coordination.

``RuntimeSafetyController`` and ``RuntimeRollbackCoordinator`` must depend on a
narrow, explicit interface rather than reaching into ``RuntimeSession`` private
attributes. ``RuntimeSafetySessionPort`` declares exactly the session
collaborators those coordinators need, and ``RuntimeSafetyState`` owns the
kill-switch flag so the safety-critical state has a single owner reached only
through the port.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from qts.runtime.broker_runtime_topology import AccountRuntimePartition
    from qts.runtime.mode import RuntimeMode
    from qts.runtime.state import RuntimeSessionState


class RuntimeSafetyState:
    """Owns the kill-switch active flag for one runtime session.

    The flag is mutated only through :meth:`activate_kill_switch` /
    :meth:`deactivate_kill_switch` and read through :attr:`kill_switch_active`,
    so the safety-critical state is never poked as a loose session attribute.
    """

    __slots__ = ("_active",)

    def __init__(self, *, kill_switch_active: bool = False) -> None:
        """Create the state with an optional initial kill-switch value."""
        self._active = kill_switch_active

    @property
    def kill_switch_active(self) -> bool:
        """Return whether the kill switch is currently active."""
        return self._active

    def activate_kill_switch(self) -> None:
        """Mark the kill switch active (blocks new order submission)."""
        self._active = True

    def deactivate_kill_switch(self) -> None:
        """Clear the kill switch (resume order submission)."""
        self._active = False


@runtime_checkable
class RuntimeSafetySessionPort(Protocol):
    """Session collaborators required by runtime safety/rollback coordinators.

    Implemented by an adapter owned inside ``runtime/session.py``; coordinators
    receive the port and never touch ``RuntimeSession`` private attributes.
    """

    @property
    def safety_state(self) -> RuntimeSafetyState:
        """Return the session's owned kill-switch state."""
        ...

    @property
    def runtime_state(self) -> RuntimeSessionState:
        """Return the current runtime lifecycle state."""
        ...

    @property
    def mode(self) -> RuntimeMode:
        """Return the runtime mode (for the broker startup gate)."""
        ...

    @property
    def startup_decision(self) -> object:
        """Return the broker startup decision (for the broker startup gate)."""
        ...

    @property
    def run_id(self) -> str:
        """Return the run identifier value for audit evidence."""
        ...

    @property
    def primary_partition(self) -> AccountRuntimePartition:
        """Return the primary account runtime partition."""
        ...

    def account_partitions(self) -> tuple[AccountRuntimePartition, ...]:
        """Return all account runtime partitions."""
        ...

    def active_order_ids(self) -> tuple[str, ...]:
        """Return the ids of currently active orders."""
        ...

    def record_account_snapshots(self) -> tuple[str, ...]:
        """Persist account snapshots and return their evidence refs."""
        ...

    def write_event(self, kind: str, payload: Mapping[str, object]) -> None:
        """Append a normalized runtime event to the session event stream."""
        ...


__all__ = ["RuntimeSafetySessionPort", "RuntimeSafetyState"]
