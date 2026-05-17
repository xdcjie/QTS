"""Hardening anchors for the API security boundary."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time

import pytest


def _jwt(secret: bytes, payload: dict[str, object]) -> str:
    header = base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').rstrip(b"=")
    body = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    ).rstrip(b"=")
    signed = header + b"." + body
    signature = base64.urlsafe_b64encode(hmac.new(secret, signed, hashlib.sha256).digest()).rstrip(
        b"="
    )
    return (signed + b"." + signature).decode()


def test_static_token_backend_fails_closed_when_no_token_file_configured() -> None:
    from fastapi import HTTPException
    from qts.api.security import StaticTokenAuthBackend

    backend = StaticTokenAuthBackend(None)

    with pytest.raises(HTTPException) as info:
        backend.verify("Bearer dev-token")
    assert info.value.status_code == 401


def test_static_token_backend_loads_only_explicit_tokens(tmp_path: object) -> None:
    from pathlib import Path

    import yaml  # type: ignore[import-untyped]
    from qts.api.security import StaticTokenAuthBackend

    assert isinstance(tmp_path, Path)

    token = "secret-token"
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    token_file = tmp_path / "tokens.yaml"
    token_file.write_text(
        yaml.safe_dump(
            {
                "tokens": {
                    token_hash: {
                        "id": "explicit",
                        "kind": "service",
                        "scopes": ["runtime:read"],
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    backend = StaticTokenAuthBackend(token_file)
    principal = backend.verify(f"Bearer {token}")

    assert principal.id == "explicit"
    assert "runtime:read" in principal.scopes


def test_bearer_jwt_replay_cache_is_bounded() -> None:
    from qts.api.security import BearerJWTAuthBackend

    secret = b"unit-test-secret"
    backend = BearerJWTAuthBackend(secret.decode())

    now = int(time.time())
    for index in range(2200):
        token = _jwt(
            secret,
            {
                "sub": "u",
                "scopes": ["runtime:read"],
                "exp": now + 60,
                "jti": f"jti-{index}",
            },
        )
        backend.verify(f"Bearer {token}")

    assert backend.seen_jti_size() <= backend.replay_cache_capacity()


def test_bearer_jwt_rejects_replay_within_window() -> None:
    from fastapi import HTTPException
    from qts.api.security import BearerJWTAuthBackend

    secret = b"unit-test-secret"
    backend = BearerJWTAuthBackend(secret.decode())

    token = _jwt(
        secret,
        {
            "sub": "u",
            "scopes": ["runtime:read"],
            "exp": int(time.time()) + 60,
            "jti": "single-use",
        },
    )

    backend.verify(f"Bearer {token}")

    with pytest.raises(HTTPException) as info:
        backend.verify(f"Bearer {token}")
    assert info.value.status_code == 401
