from __future__ import annotations

import ast
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path


@dataclass(frozen=True)
class FactorTestAsset:
    symbol: str


def test_factor_has_name_and_version() -> None:
    from qts.factors import Factor, FactorWindow, MomentumFactor

    factor = MomentumFactor(window=3)

    assert isinstance(factor.name, str)
    assert factor.name == "momentum"
    assert isinstance(factor.version, str)
    assert factor.version == "1"
    assert isinstance(factor, Factor)
    assert factor.lookback == 3
    assert FactorWindow(prices={}, lookback=1).assets() == ()


def test_factor_is_deterministic() -> None:
    from qts.factors import FactorWindow, MomentumFactor

    aapl = FactorTestAsset("AAPL")
    msft = FactorTestAsset("MSFT")
    goog = FactorTestAsset("GOOG")
    factor = MomentumFactor(window=3)
    window = FactorWindow(
        prices={
            aapl: (Decimal("10"), Decimal("12"), Decimal("15")),
            msft: (Decimal("20"), Decimal("21"), Decimal("22")),
            goog: (Decimal("30"), Decimal("30"), Decimal("30")),
        },
        lookback=3,
    )

    result = factor.compute(window)
    repeat = factor.compute(window)

    assert [score.asset.symbol for score in result.ranked] == ["AAPL", "MSFT", "GOOG"]
    assert result.score(aapl) == Decimal("0.5")
    assert result.score(msft) == Decimal("0.1")
    assert result.score(goog) == Decimal("0")
    assert repeat == result


def test_factor_handles_missing_data_explicitly() -> None:
    from qts.factors import FactorWindow, MomentumFactor

    aapl = FactorTestAsset("AAPL")
    factor = MomentumFactor(window=3)
    window = FactorWindow(
        prices={aapl: (Decimal("10"), None, Decimal("15"))},
        lookback=3,
        missing_data="raise",
    )

    try:
        factor.compute(window)
    except ValueError as exc:
        assert "missing price" in str(exc)
        assert "AAPL" in str(exc)
    else:
        raise AssertionError("missing data must raise explicitly")


def test_factor_window_filters_universe() -> None:
    from qts.factors import FactorWindow, MomentumFactor

    aapl = FactorTestAsset("AAPL")
    msft = FactorTestAsset("MSFT")
    factor = MomentumFactor(window=2)
    window = FactorWindow(
        prices={
            aapl: (Decimal("10"), Decimal("15")),
            msft: (Decimal("20"), Decimal("21")),
        },
        universe=(msft,),
        lookback=2,
    )

    result = factor.compute(window)

    assert [score.asset.symbol for score in result.ranked] == ["MSFT"]
    assert result.score(msft) == Decimal("0.05")


def test_factor_package_has_no_runtime_execution_broker_imports() -> None:
    factor_dir = Path("backend/src/qts/factors")
    forbidden_prefixes = (
        "qts.runtime",
        "qts.execution",
        "qts.reconciliation",
        "qts.portfolio.account_actor",
        "qts.risk.risk_engine",
    )

    violations: list[str] = []
    for path in sorted(factor_dir.glob("*.py")):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith(forbidden_prefixes):
                        violations.append(f"{path}:{alias.name}")
            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith(forbidden_prefixes):
                    violations.append(f"{path}:{node.module}")

    assert violations == []


def test_factor_factory_creates_momentum_factor() -> None:
    from qts.strategy_sdk.factors import FactorFactory

    factor = FactorFactory().momentum(window=3)

    assert factor.window == 3
