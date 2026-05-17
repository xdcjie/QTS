"""Anchor: every state-touching FastAPI route appears in API_SCOPE_MATRIX."""

from __future__ import annotations


def test_every_app_route_has_scope_matrix_entry() -> None:
    from qts.api.app import create_app
    from qts.api.security import required_scope_for

    app = create_app()
    framework_public_paths = {
        "/health",
        "/health/liveness",
        "/health/readiness",
        "/health/startup",
        "/metrics",
        "/openapi.json",
        "/docs",
        "/docs/oauth2-redirect",
        "/redoc",
    }
    missing: list[tuple[str, str]] = []
    for route in app.routes:
        path = getattr(route, "path", None)
        methods = getattr(route, "methods", None)
        if path is None or methods is None:
            continue
        if path in framework_public_paths:
            continue
        if path.startswith("/ws"):
            continue
        for method in methods:
            if method in {"HEAD", "OPTIONS"}:
                continue
            if required_scope_for(method, path) is None:
                missing.append((method, path))
    assert missing == [], f"routes missing scope matrix entry: {missing}"
