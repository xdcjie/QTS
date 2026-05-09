from __future__ import annotations


def test_application_services_return_stable_dtos_without_actor_internals() -> None:
    from qts.application.dto.backtest import BacktestRequestDTO
    from qts.application.services import BacktestService, HealthService

    health = HealthService().status()
    result = BacktestService().submit(BacktestRequestDTO(strategy_name="smoke"))

    assert health.status == "ok"
    assert result.status == "accepted"
    assert result.run_id.startswith("bt-")
    assert not hasattr(result, "actor_ref")
    assert not hasattr(result, "mailbox")
