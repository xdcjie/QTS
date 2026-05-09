from __future__ import annotations

from decimal import Decimal


def test_paper_runtime_can_be_constructed_without_real_broker_credentials() -> None:
    from qts.application.commands.start_paper import PaperRuntimeConfig, start_paper

    runtime = start_paper(
        PaperRuntimeConfig(
            account_id="paper-local",
            initial_cash=Decimal("100000"),
            data_source="replay",
        )
    )

    assert runtime.status == "constructed"
    assert runtime.config.simulated_broker
