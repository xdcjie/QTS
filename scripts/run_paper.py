from __future__ import annotations

from decimal import Decimal

from qts.application.commands.start_paper import PaperRuntimeConfig, start_paper


def main() -> None:
    """Perform main."""
    runtime = start_paper(
        PaperRuntimeConfig(
            account_id="paper-local",
            initial_cash=Decimal("100000"),
            data_source="replay",
        )
    )
    print(runtime.status)


if __name__ == "__main__":
    main()
