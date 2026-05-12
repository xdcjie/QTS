#!/usr/bin/env python
"""Run a background worker entrypoint (compatibility placeholder)."""

from __future__ import annotations


def main() -> int:
    """Emit compatibility-mode worker message for now."""
    print(
        "qts background worker mode is not yet implemented; "
        "use application orchestrators (run_paper/run_backtest) instead."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
