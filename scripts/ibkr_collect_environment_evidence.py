#!/usr/bin/env python
"""Collect observe-only IBKR environment evidence."""

from __future__ import annotations

from qts.application.commands.ibkr_environment_evidence import (
    collect_environment_evidence,
    main,
)

__all__ = ["collect_environment_evidence", "main"]

if __name__ == "__main__":
    main()
