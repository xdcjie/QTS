#!/usr/bin/env python
"""Thin CLI wrapper for IBKR environment evidence collection."""

from qts.application.commands.ibkr_environment_evidence import (
    main as _command_main,
)


def main() -> None:
    """Run IBKR environment evidence collection command."""
    _command_main()


if __name__ == "__main__":
    main()
