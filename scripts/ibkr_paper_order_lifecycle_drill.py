#!/usr/bin/env python
"""Thin CLI wrapper for paper IBKR order lifecycle drill."""

from qts.application.commands.ibkr_paper_order_lifecycle_drill import (
    main as _command_main,
)


def main() -> None:
    """Run paper order lifecycle drill command."""
    _command_main()


if __name__ == "__main__":
    main()
