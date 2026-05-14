#!/usr/bin/env python
"""Run the IBKR paper order lifecycle drill."""

from __future__ import annotations

from qts.application.commands.ibkr_paper_order_lifecycle_drill import (
    main as _run_paper_drill,
)


def main() -> int:
    """Run the IBKR paper order lifecycle drill command."""
    _run_paper_drill()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
