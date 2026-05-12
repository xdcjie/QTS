#!/usr/bin/env python
"""Thin CLI wrapper for IBKR environment evidence collection."""

from typing import Any

from qts.application.commands.ibkr_environment_evidence import (
    collect_environment_evidence as _collect_environment_evidence,
)
from qts.application.commands.ibkr_environment_evidence import (
    main as _command_main,
)


def collect_environment_evidence(*args: Any, **kwargs: Any) -> Any:
    """Run the legacy script entrypoint through the command module."""

    return _collect_environment_evidence(*args, **kwargs)


def main() -> None:
    """Run IBKR environment evidence collection command."""
    _command_main()


if __name__ == "__main__":
    main()
