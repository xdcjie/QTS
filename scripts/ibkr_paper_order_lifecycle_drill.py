#!/usr/bin/env python
"""Thin CLI wrapper for paper IBKR order lifecycle drill."""

from typing import Any

from qts.application.commands.ibkr_paper_order_lifecycle_drill import (
    main as _command_main,
)
from qts.application.commands.ibkr_paper_order_lifecycle_drill import (
    run_paper_order_lifecycle_drill as _run_paper_order_lifecycle_drill,
)


def run_paper_order_lifecycle_drill(*args: Any, **kwargs: Any) -> Any:
    """Run the command function through the legacy script entrypoint."""

    return _run_paper_order_lifecycle_drill(*args, **kwargs)


def main() -> None:
    """Run paper order lifecycle drill command."""
    _command_main()


if __name__ == "__main__":
    main()
