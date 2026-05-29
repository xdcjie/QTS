"""Hierarchical actor path for naming and supervision topology."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ActorPath:
    """Hierarchical path that identifies an actor within the runtime tree.

    Format: ``/parent/child``.  Root actors have no parent and render as
    ``/name``.  This is optional; existing ActorRefs without paths continue
    to work normally.
    """

    name: str
    parent: ActorPath | None = None

    def __str__(self) -> str:
        """Render the path as ``/segment/segment``."""
        if self.parent is None:
            return f"/{self.name}"
        return f"{self.parent}/{self.name}"

    @classmethod
    def root(cls, name: str) -> ActorPath:
        """Create a root-level actor path (no parent)."""
        return cls(name=name, parent=None)

    def child(self, name: str) -> ActorPath:
        """Create a child path beneath this one."""
        return ActorPath(name=name, parent=self)

    @property
    def segments(self) -> tuple[str, ...]:
        """Return path segments from root to leaf."""
        if self.parent is None:
            return (self.name,)
        return (*self.parent.segments, self.name)


__all__ = ["ActorPath"]
