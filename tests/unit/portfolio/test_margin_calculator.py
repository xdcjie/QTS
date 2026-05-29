"""Unit tests for MarginCalculator."""

from __future__ import annotations

from decimal import Decimal

import pytest
from qts.core.ids import InstrumentId
from qts.portfolio.holdings import Holding
from qts.risk.margin.calculator import MarginCalculator, MarginRequirement


def _iid(value: str) -> InstrumentId:
    return InstrumentId(value)


def _holding(instrument_id: InstrumentId, quantity: Decimal) -> Holding:
    return Holding(
        instrument_id=instrument_id,
        quantity=quantity,
        average_cost=Decimal("100"),
        realized_pnl=Decimal("0"),
    )


class TestMarginRequirementDataclass:
    """Tests for the MarginRequirement frozen dataclass."""

    def test_frozen(self) -> None:
        req = MarginRequirement(
            initial_margin=Decimal("500"),
            maintenance_margin=Decimal("400"),
            available_margin=Decimal("9500"),
        )
        with pytest.raises(AttributeError):
            req.initial_margin = Decimal("999")  # type: ignore[misc]


class TestMarginCalculatorConstruction:
    """Tests for MarginCalculator initialization and validation."""

    def test_default_rates(self) -> None:
        calc = MarginCalculator()
        assert calc._initial_margin_rate == Decimal("0.05")
        assert calc._maintenance_margin_rate == Decimal("0.04")

    def test_custom_rates(self) -> None:
        calc = MarginCalculator(
            initial_margin_rate=Decimal("0.10"),
            maintenance_margin_rate=Decimal("0.08"),
        )
        assert calc._initial_margin_rate == Decimal("0.10")
        assert calc._maintenance_margin_rate == Decimal("0.08")

    def test_negative_initial_rate_raises(self) -> None:
        with pytest.raises(ValueError, match="initial_margin_rate must be positive"):
            MarginCalculator(initial_margin_rate=Decimal("-0.05"))

    def test_zero_initial_rate_raises(self) -> None:
        with pytest.raises(ValueError, match="initial_margin_rate must be positive"):
            MarginCalculator(initial_margin_rate=Decimal("0"))

    def test_negative_maintenance_rate_raises(self) -> None:
        with pytest.raises(ValueError, match="maintenance_margin_rate must be positive"):
            MarginCalculator(maintenance_margin_rate=Decimal("-0.04"))

    def test_zero_maintenance_rate_raises(self) -> None:
        with pytest.raises(ValueError, match="maintenance_margin_rate must be positive"):
            MarginCalculator(maintenance_margin_rate=Decimal("0"))

    def test_maintenance_exceeds_initial_raises(self) -> None:
        with pytest.raises(
            ValueError, match="maintenance_margin_rate must not exceed initial_margin_rate"
        ):
            MarginCalculator(
                initial_margin_rate=Decimal("0.04"),
                maintenance_margin_rate=Decimal("0.05"),
            )


class TestMarginCalculatorRequirement:
    """Tests for MarginCalculator.margin_requirement computation."""

    def test_zero_positions_zero_margin(self) -> None:
        calc = MarginCalculator()
        result = calc.margin_requirement(
            positions={},
            marks={},
            multipliers={},
            account_equity=Decimal("10000"),
        )
        assert result.initial_margin == Decimal("0")
        assert result.maintenance_margin == Decimal("0")
        assert result.available_margin == Decimal("10000")

    def test_single_position_default_rates(self) -> None:
        """1 contract * $50 price * 100 multiplier = $5000 notional.
        initial = 5000 * 0.05 = 250, maintenance = 5000 * 0.04 = 200."""
        iid = _iid("ES")
        calc = MarginCalculator()
        result = calc.margin_requirement(
            positions={iid: _holding(iid, Decimal("1"))},
            marks={iid: Decimal("50")},
            multipliers={iid: Decimal("100")},
            account_equity=Decimal("10000"),
        )
        assert result.initial_margin == Decimal("250")
        assert result.maintenance_margin == Decimal("200")
        assert result.available_margin == Decimal("9750")

    def test_multiple_positions_aggregate(self) -> None:
        """Two positions: notional sums across all holdings."""
        es = _iid("ES")
        gc = _iid("GC")
        calc = MarginCalculator()
        result = calc.margin_requirement(
            positions={
                es: _holding(es, Decimal("2")),
                gc: _holding(gc, Decimal("3")),
            },
            marks={es: Decimal("50"), gc: Decimal("1800")},
            multipliers={es: Decimal("50"), gc: Decimal("100")},
            account_equity=Decimal("50000"),
        )
        # ES notional = 2 * 50 * 50 = 5000
        # GC notional = 3 * 1800 * 100 = 540000
        # total notional = 545000
        # initial = 545000 * 0.05 = 27250
        # maintenance = 545000 * 0.04 = 21800
        # available = 50000 - 27250 = 22750
        assert result.initial_margin == Decimal("27250")
        assert result.maintenance_margin == Decimal("21800")
        assert result.available_margin == Decimal("22750")

    def test_available_margin_equals_equity_minus_initial(self) -> None:
        iid = _iid("CL")
        calc = MarginCalculator()
        result = calc.margin_requirement(
            positions={iid: _holding(iid, Decimal("5"))},
            marks={iid: Decimal("70")},
            multipliers={iid: Decimal("1000")},
            account_equity=Decimal("50000"),
        )
        # notional = 5 * 70 * 1000 = 350000
        # initial = 350000 * 0.05 = 17500
        assert result.available_margin == Decimal("50000") - result.initial_margin

    def test_negative_available_margin_when_overleveraged(self) -> None:
        iid = _iid("ES")
        calc = MarginCalculator()
        result = calc.margin_requirement(
            positions={iid: _holding(iid, Decimal("100"))},
            marks={iid: Decimal("4500")},
            multipliers={iid: Decimal("50")},
            account_equity=Decimal("10000"),
        )
        # notional = 100 * 4500 * 50 = 22500000
        # initial = 22500000 * 0.05 = 1125000
        # available = 10000 - 1125000 = -1115000
        assert result.available_margin < Decimal("0")
        assert result.available_margin == Decimal("-1115000")

    def test_short_position_uses_abs_quantity(self) -> None:
        """Margin is the same for long and short of the same absolute size."""
        iid = _iid("ES")
        calc = MarginCalculator()
        result = calc.margin_requirement(
            positions={iid: _holding(iid, Decimal("-3"))},
            marks={iid: Decimal("4000")},
            multipliers={iid: Decimal("50")},
            account_equity=Decimal("100000"),
        )
        # notional = abs(-3) * 4000 * 50 = 600000
        # initial = 600000 * 0.05 = 30000
        assert result.initial_margin == Decimal("30000")
        assert result.maintenance_margin == Decimal("24000")

    def test_custom_rates(self) -> None:
        iid = _iid("GC")
        calc = MarginCalculator(
            initial_margin_rate=Decimal("0.10"),
            maintenance_margin_rate=Decimal("0.07"),
        )
        result = calc.margin_requirement(
            positions={iid: _holding(iid, Decimal("1"))},
            marks={iid: Decimal("1800")},
            multipliers={iid: Decimal("100")},
            account_equity=Decimal("50000"),
        )
        # notional = 1 * 1800 * 100 = 180000
        # initial = 180000 * 0.10 = 18000
        # maintenance = 180000 * 0.07 = 12600
        assert result.initial_margin == Decimal("18000")
        assert result.maintenance_margin == Decimal("12600")
        assert result.available_margin == Decimal("32000")

    def test_position_without_mark_skipped(self) -> None:
        """If a mark price is missing, the position contributes zero notional."""
        iid = _iid("ES")
        calc = MarginCalculator()
        result = calc.margin_requirement(
            positions={iid: _holding(iid, Decimal("5"))},
            marks={},  # no mark for ES
            multipliers={iid: Decimal("50")},
            account_equity=Decimal("10000"),
        )
        assert result.initial_margin == Decimal("0")
        assert result.available_margin == Decimal("10000")

    def test_flat_position_skipped(self) -> None:
        """Zero-quantity positions contribute no margin."""
        iid = _iid("ES")
        calc = MarginCalculator()
        result = calc.margin_requirement(
            positions={iid: _holding(iid, Decimal("0"))},
            marks={iid: Decimal("50")},
            multipliers={iid: Decimal("100")},
            account_equity=Decimal("10000"),
        )
        assert result.initial_margin == Decimal("0")
        assert result.available_margin == Decimal("10000")

    def test_default_multiplier_is_one(self) -> None:
        """When a multiplier is not supplied, it defaults to 1."""
        iid = _iid("STK")
        calc = MarginCalculator()
        result = calc.margin_requirement(
            positions={iid: _holding(iid, Decimal("100"))},
            marks={iid: Decimal("25")},
            multipliers={},  # no multiplier, defaults to 1
            account_equity=Decimal("50000"),
        )
        # notional = 100 * 25 * 1 = 2500
        # initial = 2500 * 0.05 = 125
        assert result.initial_margin == Decimal("125")
        assert result.maintenance_margin == Decimal("100")
