#!/usr/bin/env python
"""Run the QTS API server."""

from __future__ import annotations

import uvicorn


def main() -> int:
    """Start the QTS FastAPI application server."""
    uvicorn.run(
        "qts.api.app:create_app",
        host="127.0.0.1",
        port=8000,
        factory=True,
        reload=False,
        app_dir="backend/src",
        log_config=None,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
