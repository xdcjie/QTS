"""API authentication backend factory."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

from qts.api.security import (
    DEFAULT_SCOPES,
    AuthBackend,
    BearerJWTAuthBackend,
    Principal,
    StaticTokenAuthBackend,
)


def default_auth_backend() -> AuthBackend:
    """Build the configured default auth backend.

    Resolution order:
    1. ``QTS_API_JWT_SECRET`` set -> HS256 JWT backend.
    2. ``QTS_API_STATIC_TOKENS`` set -> static-token backend loaded from that file.
    3. ``QTS_API_DEV_TOKENS=1`` set -> built-in development tokens.
    4. Otherwise -> static-token backend with no principals (fail-closed).
    """
    secret = os.getenv("QTS_API_JWT_SECRET")
    if secret:
        return BearerJWTAuthBackend(secret)
    token_path = os.getenv("QTS_API_STATIC_TOKENS")
    if token_path is not None:
        return StaticTokenAuthBackend(Path(token_path))
    if os.getenv("QTS_API_DEV_TOKENS") == "1":
        return _DevDefaultTokenAuthBackend()
    return StaticTokenAuthBackend(None)


class _DevDefaultTokenAuthBackend(StaticTokenAuthBackend):
    """Development-only static-token backend with two built-in principals."""

    def __init__(self) -> None:
        self._principals = {
            hashlib.sha256(b"dev-token").hexdigest(): Principal(
                id="local-dev",
                kind="human",
                scopes=DEFAULT_SCOPES,
                session_id="local",
            ),
            hashlib.sha256(b"read-token").hexdigest(): Principal(
                id="local-read",
                kind="human",
                scopes=frozenset(scope for scope in DEFAULT_SCOPES if scope.endswith(":read")),
                session_id="local-read",
            ),
        }


__all__ = ["default_auth_backend"]
