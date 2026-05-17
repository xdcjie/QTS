"""API authentication, authorization, CORS, and rate-limit helpers."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from collections import OrderedDict, defaultdict, deque
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

from qts.observability.audit import AuditEvent
from qts.observability.audit_sink import AuditSink, StderrJsonAuditSink
from qts.observability.audit_sink import now as _audit_now

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
WEBSOCKET_REQUIRED_SCOPE = "runtime:read"
_REPLAY_CACHE_CAPACITY = 2048


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
        if not self._principals:
            raise HTTPException(status_code=401, detail="auth backend not configured")
        token = _bearer_token(authorization_header)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        try:
            return self._principals[token_hash]
        except KeyError as exc:
            raise HTTPException(status_code=401, detail="invalid bearer token") from exc

    @staticmethod
    def _load(token_file: Path | None) -> dict[str, Principal]:
        if token_file is None or not token_file.exists():
            return {}
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

    def __init__(self, secret: str, *, replay_cache_capacity: int = _REPLAY_CACHE_CAPACITY) -> None:
        if not secret.strip():
            raise ValueError("JWT secret must not be empty")
        if replay_cache_capacity <= 0:
            raise ValueError("replay_cache_capacity must be positive")
        self._secret = secret.encode()
        self._seen_jti: OrderedDict[str, None] = OrderedDict()
        self._replay_cache_capacity = replay_cache_capacity

    def replay_cache_capacity(self) -> int:
        """Return the maximum jti replay cache size."""
        return self._replay_cache_capacity

    def seen_jti_size(self) -> int:
        """Return the current size of the jti replay cache."""
        return len(self._seen_jti)

    def verify(self, authorization_header: str | None) -> Principal:
        """Verify a compact HS256 bearer JWT."""
        token = _bearer_token(authorization_header)
        try:
            header_b64, payload_b64, signature_b64 = token.split(".")
        except ValueError as exc:
            raise HTTPException(status_code=401, detail="invalid bearer token") from exc
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
            self._seen_jti[jti] = None
            while len(self._seen_jti) > self._replay_cache_capacity:
                self._seen_jti.popitem(last=False)
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
        audit_sink: AuditSink | None = None,
    ) -> None:
        super().__init__(app)
        self._auth_backend = auth_backend
        self._rate_limits = dict(rate_limits or {"read": 60, "write": 30, "safety": 6})
        self._windows: dict[str, deque[float]] = defaultdict(deque)
        self._audit_sink: AuditSink = audit_sink or StderrJsonAuditSink()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Authenticate, authorize, rate-limit, and continue."""
        if request.url.path == "/health":
            return await call_next(request)
        principal: Principal | None = None
        response: Response
        try:
            principal = self._auth_backend.verify(request.headers.get("Authorization"))
            required_scope = required_scope_for(request.method, request.url.path)
            if required_scope is not None and required_scope not in principal.scopes:
                response = JSONResponse({"detail": "insufficient scope"}, status_code=403)
            elif not self._consume_budget(principal, required_scope):
                response = JSONResponse({"detail": "rate limit exceeded"}, status_code=429)
            else:
                request.state.principal = principal
                response = await call_next(request)
        except HTTPException as exc:
            response = JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
        self._emit_audit(request, principal, response.status_code)
        return response

    def _emit_audit(
        self,
        request: Request,
        principal: Principal | None,
        status_code: int,
    ) -> None:
        actor = principal.id if principal is not None else "anonymous"
        correlation_id = request.headers.get("X-Correlation-Id")
        self._audit_sink.write(
            AuditEvent(
                event_type="api.auth_decision",
                event_time=_audit_now(),
                actor=actor,
                message=f"{request.method} {request.url.path} {status_code}",
                correlation_id=correlation_id,
            )
        )

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


def verify_websocket_authorization(
    auth_backend: AuthBackend,
    authorization_header: str | None,
    *,
    required_scope: str = WEBSOCKET_REQUIRED_SCOPE,
) -> Principal:
    """Verify a WebSocket handshake authorization header and enforce scope.

    Raises `HTTPException` when the principal is invalid or under-scoped. The
    caller closes the socket with a websocket-style close code based on the
    HTTPException status.
    """
    principal = auth_backend.verify(authorization_header)
    if required_scope and required_scope not in principal.scopes:
        raise HTTPException(status_code=403, detail="insufficient scope")
    return principal


def default_auth_backend() -> AuthBackend:
    """Build the configured default auth backend.

    Resolution order:
    1. ``QTS_API_JWT_SECRET`` set → HS256 JWT backend.
    2. ``QTS_API_STATIC_TOKENS`` set → static-token backend loaded from that file.
    3. ``QTS_API_DEV_TOKENS=1`` set → built-in development tokens
       (``dev-token`` with full scopes, ``read-token`` with read-only scopes).
       This is the only opt-in to default tokens; production deployments must
       leave it unset.
    4. Otherwise → static-token backend with no principals (fail-closed).
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
    "WEBSOCKET_REQUIRED_SCOPE",
    "default_auth_backend",
    "get_principal",
    "require_scope",
    "required_scope_for",
    "verify_websocket_authorization",
]
