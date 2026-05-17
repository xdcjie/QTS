#!/usr/bin/env python
"""Generate the backend FastAPI OpenAPI document used by frontend type generation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from qts.api.app import create_app


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default=str(Path("frontend/openapi.json")),
        help="Path to write the OpenAPI JSON document.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = Path(args.output)
    app = create_app()
    payload = app.openapi()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(f"wrote {output} ({len(json.dumps(payload))} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
