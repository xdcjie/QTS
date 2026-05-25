from __future__ import annotations

from datetime import UTC, datetime

import pytest
from qts.research import (
    FactorBucketSpec,
    PaperCandidateDiagnosticsGate,
    TradeDiagnostic,
    TradeDiagnosticsReport,
)


def test_trade_diagnostics_requires_r_pnl_mae_mfe() -> None:
    with pytest.raises(ValueError, match="R_pnl"):
        TradeDiagnostic(exit_reason="stop", mae_r=-0.5, mfe_r=0.7)
    with pytest.raises(ValueError, match="MAE_R"):
        TradeDiagnostic(exit_reason="stop", r_pnl=-1.0, mfe_r=0.7)
    with pytest.raises(ValueError, match="MFE_R"):
        TradeDiagnostic(exit_reason="stop", r_pnl=-1.0, mae_r=-0.5)
    with pytest.raises(ValueError, match="exit_reason"):
        TradeDiagnostic(r_pnl=-1.0, mae_r=-0.5, mfe_r=0.7)


def test_trade_diagnostics_groups_by_exit_reason() -> None:
    report = TradeDiagnosticsReport(
        trades=(
            TradeDiagnostic(r_pnl=1.0, mae_r=-0.2, mfe_r=1.4, exit_reason="target"),
            TradeDiagnostic(r_pnl=-0.5, mae_r=-1.0, mfe_r=0.3, exit_reason="stop"),
            TradeDiagnostic(r_pnl=0.5, mae_r=-0.4, mfe_r=0.8, exit_reason="target"),
        )
    )

    grouped = report.group_by_exit_reason()

    assert grouped["target"].trade_count == 2
    assert grouped["target"].average_r_pnl == pytest.approx(0.75)
    assert grouped["stop"].trade_count == 1


def test_trade_diagnostics_groups_by_time_bucket() -> None:
    report = TradeDiagnosticsReport(
        trades=(
            TradeDiagnostic(
                r_pnl=1.0,
                mae_r=-0.2,
                mfe_r=1.4,
                exit_reason="target",
                exited_at=datetime(2024, 1, 2, 9, 30, tzinfo=UTC),
            ),
            TradeDiagnostic(
                r_pnl=-0.5,
                mae_r=-1.0,
                mfe_r=0.3,
                exit_reason="stop",
                exited_at=datetime(2024, 1, 2, 15, 30, tzinfo=UTC),
            ),
        )
    )

    grouped = report.group_by_time_bucket(
        {
            "morning": (0, 12),
            "afternoon": (12, 24),
        }
    )

    assert grouped["morning"].trade_count == 1
    assert grouped["afternoon"].trade_count == 1


def test_trade_diagnostics_groups_by_quantity() -> None:
    report = TradeDiagnosticsReport(
        trades=(
            TradeDiagnostic(r_pnl=1.0, mae_r=-0.2, mfe_r=1.4, exit_reason="target", quantity=1),
            TradeDiagnostic(r_pnl=0.5, mae_r=-0.4, mfe_r=0.8, exit_reason="target", quantity=1),
            TradeDiagnostic(r_pnl=-0.5, mae_r=-1.0, mfe_r=0.3, exit_reason="stop", quantity=2),
        )
    )

    grouped = report.group_by_quantity()

    assert grouped["1"].trade_count == 2
    assert grouped["2"].trade_count == 1


def test_trade_diagnostics_groups_by_factor_buckets() -> None:
    report = TradeDiagnosticsReport(
        trades=(
            TradeDiagnostic(
                r_pnl=1.0,
                mae_r=-0.2,
                mfe_r=1.4,
                exit_reason="target",
                factor_values={"momentum": 0.8},
            ),
            TradeDiagnostic(
                r_pnl=-0.5,
                mae_r=-1.0,
                mfe_r=0.3,
                exit_reason="stop",
                factor_values={"momentum": -0.3},
            ),
        )
    )

    grouped = report.group_by_factor_buckets(
        FactorBucketSpec(
            factor_name="momentum",
            buckets=(("negative", None, 0.0), ("positive", 0.0, None)),
        )
    )

    assert grouped["negative"].trade_count == 1
    assert grouped["positive"].trade_count == 1


def test_missing_trade_diagnostics_blocks_paper_candidate() -> None:
    validation = PaperCandidateDiagnosticsGate().validate(None)
    assert validation.blocks_paper_candidate is True
    assert validation.missing_fields == ("trade_diagnostics",)

    invalid_report = TradeDiagnosticsReport(
        trades=(
            TradeDiagnostic(
                r_pnl=1.0,
                mae_r=-0.2,
                mfe_r=1.4,
                exit_reason="target",
                diagnostics_complete=False,
            ),
        )
    )
    assert PaperCandidateDiagnosticsGate().validate(invalid_report).blocks_paper_candidate is True

    valid_report = TradeDiagnosticsReport(
        trades=(TradeDiagnostic(r_pnl=1.0, mae_r=-0.2, mfe_r=1.4, exit_reason="target"),)
    )
    assert PaperCandidateDiagnosticsGate().validate(valid_report).blocks_paper_candidate is False
