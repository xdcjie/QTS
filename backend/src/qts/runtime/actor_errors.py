"""Actor-specific error types for the runtime actor model."""

from __future__ import annotations


class ActorAskTimeoutError(Exception):
    """Raised when ask() exceeds its configured timeout.

    This replaces the implicit MailboxTimeoutError that ask() previously
    propagated, giving callers a domain-specific exception to catch and
    handle in live-critical broker callbacks.
    """


class ActorUnhandledMessageError(Exception):
    """Raised when an actor cannot handle a message type.

    Replaces the previous ``raise TypeError(f"unsupported message: ...")``
    pattern in actor handle() methods so that message-dispatch errors are
    distinguishable from type-validation errors in test and production code.
    """


__all__ = ["ActorAskTimeoutError", "ActorUnhandledMessageError"]
