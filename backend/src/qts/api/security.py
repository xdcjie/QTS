"""API authentication, authorization, CORS, and rate-limit helpers."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from collections import defaultdict, deque
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib import import_module
from pathlib import Path
from typing import Any, Protocol, cast

from fastapi import Header, HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

API_SCOPE_MATRIX: Mapping[tuple[str, str], str | None] = {
    ("GET", "/accounts/"): "accounts:read",
    ("GET", "/orders/"): "orders:read",
    ("GET", "/strategies"): "strategies:read",
    ("POST", "/strategies/"): "strategies:write",
    ("GET", "/backtests"): "backtests:read",
    ("POST", "/backtests"): "backtests:write",
    ("GET", "/operations/operator-status"): "runtime:read",
    ("POST", "/operations/runtime/"): "runtime:safety:write",
    ("POST", "/operations/kill-switches"): "runtime:safety:write",
}
DEFAULT_SCOPES = frozenset(
    {
        "backtests:read",
        "backtests:write",
        "strategies:read",
        "strategies:write",
        "accounts:read",
        "orders:read",
        "orders:write",
        "orders:cancel",
        "runtime:read",
        "runtime:safety:write",
    }
)


@dataclass(frozen=True, slots=True)
class Principal:
    """Authenticated API principal."""

    id: str
    kind: str
    scopes: frozenset[str]
    session_id: str | None = None
    issued_at: datetime | None = None
    expires_at: datetime | None = None
    operator: str | None = None

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("principal id must not be empty")
        if self.kind not in {"service", "human"}:
            raise ValueError("principal kind must be service or human")


class AuthBackend(Protocol):
    """Authentication backend contract."""

    def verify(self, authorization_header: str | None) -> Principal:
        """Verify an Authorization header and return a principal."""
        ...


class StaticTokenAuthBackend:
    """Hash-based static token backend for local development and CI."""

    def __init__(self, token_file: Path | None = None) -> None:
        self._principals = self._load(token_file)

    def verify(self, authorization_header: str | None) -> Principal:
        """Verify a bearer token against configured SHA-256 token hashes."""
        token = _bearer_token(authorization_header)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        try:
            return self._principals[token_hash]
        except KeyError as exc:
            raise HTTPException(status_code=401, detail="invalid bearer token") from exc

    @staticmethod
    def _load(token_file: Path | None) -> dict[str, Principal]:
        if token_file is None or not token_file.exists():
            return {
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
        yaml_module = import_module("yaml")
        data = (
            cast(
                Any,
                yaml_module.safe_load(token_file.read_text(encoding="utf-8")),
            )
            or {}
        )
        tokens = data.get("tokens", data)
        if not isinstance(tokens, dict):
            raise ValueError("static token file must contain a mapping")
        principals: dict[str, Principal] = {}
        for token_hash, payload in tokens.items():
            if not isinstance(payload, dict):
                raise ValueError("static token principal entries must be mappings")
            principals[str(token_hash)] = Principal(
                id=str(payload["id"]),
                kind=str(payload.get("kind", "service")),
                scopes=frozenset(str(scope) for scope in payload.get("scopes", ())),
                session_id=None
                if payload.get("session_id") is None
                else str(payload.get("session_id")),
            )
        return principals


class BearerJWTAuthBackend:
    """Minimal HS256 JWT verifier for service tokens."""

    def __init__(self, secret: str) -> None:
        if not secret.strip():
            raise ValueError("JWT secret must not be empty")
        self._secret = secret.encode()
        self._seen_jti: set[str] = set()

    def verify(self, authorization_header: str | None) -> Principal:
        """Verify a compact HS256 bearer JWT."""
        token = _bearer_token(authorization_header)
        header_b64, payload_b64, signature_b64 = token.split(".")
        signed = f"{header_b64}.{payload_b64}".encode()
        expected = hmac.new(self._secret, signed, hashlib.sha256).digest()
        observed = _base64url_decode(signature_b64)
        if not hmac.compare_digest(expected, observed):
            raise HTTPException(status_code=401, detail="invalid bearer token")
        payload = json.loads(_base64url_decode(payload_b64).decode())
        exp = payload.get("exp")
        if exp is not None and int(exp) <= int(time.time()):
            raise HTTPException(status_code=401, detail="bearer token expired")
        jti = payload.get("jti")
        if isinstance(jti, str):
            if jti in self._seen_jti:
                raise HTTPException(status_code=401, detail="bearer token replayed")
            self._seen_jti.add(jti)
        return Principal(
            id=str(payload.get("sub", "")),
            kind=str(payload.get("kind", "service")),
            scopes=frozenset(str(scope) for scope in payload.get("scopes", ())),
            session_id=None if payload.get("sid") is None else str(payload.get("sid")),
            issued_at=None
            if payload.get("iat") is None
            else datetime.fromtimestamp(int(payload["iat"]), tz=UTC),
            expires_at=None if exp is None else datetime.fromtimestamp(int(exp), tz=UTC),
        )


class ApiSecurityMiddleware(BaseHTTPMiddleware):
    """Authenticate every non-public API request and enforce scopes."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        auth_backend: AuthBackend,
        rate_limits: Mapping[str, int] | None = None,
    ) -> None:
        super().__init__(app)
        self._auth_backend = auth_backend
        self._rate_limits = dict(rate_limits or {"read": 60, "write": 30, "safety": 6})
        self._windows: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Authenticate, authorize, rate-limit, and continue."""
        if request.url.path == "/health":
            return await call_next(request)
        try:
            principal = self._auth_backend.verify(request.headers.get("Authorization"))
            required_scope = required_scope_for(request.method, request.url.path)
            if required_scope is not None and required_scope not in principal.scopes:
                return JSONResponse({"detail": "insufficient scope"}, status_code=403)
            if not self._consume_budget(principal, required_scope):
                return JSONResponse({"detail": "rate limit exceeded"}, status_code=429)
            request.state.principal = principal
        except HTTPException as exc:
            return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
        return await call_next(request)

    def _consume_budget(self, principal: Principal, scope: str | None) -> bool:
        kind = "safety" if scope == "runtime:safety:write" else "write" if scope else "read"
        budget = self._rate_limits[kind]
        key = f"{principal.id}:{kind}"
        now = time.monotonic()
        window = self._windows[key]
        while window and now - window[0] >= 60:
            window.popleft()
        if len(window) >= budget:
            return False
        window.append(now)
        return True


def required_scope_for(method: str, path: str) -> str | None:
    """Return the configured scope for a route."""
    normalized_method = method.upper()
    for (route_method, route_prefix), scope in API_SCOPE_MATRIX.items():
        if normalized_method == route_method and path.startswith(route_prefix):
            return scope
    return None


def require_scope(scope: str) -> Callable[[Principal], Principal]:
    """FastAPI dependency factory for route-level scope checks."""

    def dependency(principal: Principal) -> Principal:
        if scope not in principal.scopes:
            raise HTTPException(status_code=403, detail="insufficient scope")
        return principal

    return dependency


def get_principal(
    request: Request,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> Principal:
    """FastAPI dependency returning the authenticated principal."""
    principal = getattr(request.state, "principal", None)
    if isinstance(principal, Principal):
        return principal
    return default_auth_backend().verify(authorization)


def default_auth_backend() -> AuthBackend:
    """Build the configured default auth backend."""
    secret = os.getenv("QTS_API_JWT_SECRET")
    if secret:
        return BearerJWTAuthBackend(secret)
    token_path = os.getenv("QTS_API_STATIC_TOKENS")
    return StaticTokenAuthBackend(None if token_path is None else Path(token_path))


def _bearer_token(authorization_header: str | None) -> str:
    if authorization_header is None:
        raise HTTPException(status_code=401, detail="missing bearer token")
    scheme, _, token = authorization_header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(status_code=401, detail="missing bearer token")
    return token.strip()


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


__all__ = [
    "API_SCOPE_MATRIX",
    "ApiSecurityMiddleware",
    "AuthBackend",
    "BearerJWTAuthBackend",
    "DEFAULT_SCOPES",
    "Principal",
    "StaticTokenAuthBackend",
    "default_auth_backend",
    "get_principal",
    "require_scope",
    "required_scope_for",
]
