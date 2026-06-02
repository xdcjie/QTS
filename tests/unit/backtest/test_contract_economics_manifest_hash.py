"""Backtest manifest hash gate for contract economics and margin policy."""

from __future__ import annotations

from pathlib import Path


def test_backtest_reporting_records_contract_economics_and_margin_policy_hashes() -> None:
    source = Path("backend/src/qts/reporting/backtest.py").read_text(encoding="utf-8")

    assert "contract_economics_hash" in source
    assert "margin_policy_hash" in source
    assert '"contract_economics_hash": contract_economics_hash' in source
    assert '"margin_policy_hash": margin_policy_hash' in source
