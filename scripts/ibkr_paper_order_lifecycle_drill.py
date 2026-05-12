#!/usr/bin/env python
"""Run a paper-only IBKR order lifecycle drill."""

from __future__ import annotations

from qts.application.commands.ibkr_paper_order_lifecycle_drill import (
    main,
    run_paper_order_lifecycle_drill,
)

__all__ = ["run_paper_order_lifecycle_drill", "main"]

if __name__ == "__main__":
    main()
