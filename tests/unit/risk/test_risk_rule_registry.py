"""Verify RiskRuleRegistry dispatches by RiskRuleName enum instead of raw strings."""

from __future__ import annotations

from decimal import Decimal

import pytest
from qts.risk.config import RiskRuleConfig, RiskRuleName
from qts.risk.rule_registry import RiskRuleRegistry
from qts.risk.rules.concentration_limit import ConcentrationLimitRule
from qts.risk.rules.intraday_loss_limit import IntradayLossLimitRule
from qts.risk.rules.leverage_limit import LeverageLimitRule
from qts.risk.rules.market_data_freshness import MarketDataFreshnessRiskRule
from qts.risk.rules.market_data_permission import MarketDataPermissionRiskRule
from qts.risk.rules.max_notional import MaxNotionalRule
from qts.risk.rules.max_order_qty import MaxOrderQuantityRule
from qts.risk.rules.order_spec_validity import OrderSpecValidityRule
from qts.risk.rules.position_limit import PositionLimitRule
from qts.risk.rules.volatility_adjusted_sizing import VolatilityAdjustedSizingRule


class TestRiskRuleRegistryEnumDispatch:
    """Registry must dispatch by typed RiskRuleName enum members."""

    @pytest.fixture()
    def registry(self) -> RiskRuleRegistry:
        return RiskRuleRegistry()

    def test_position_limit_by_enum(self, registry: RiskRuleRegistry) -> None:
        config = RiskRuleConfig(
            rule_id="r1",
            name=RiskRuleName.POSITION_LIMIT,
            params={"max_position": Decimal("10")},
        )
        rule = registry.build(config)
        assert isinstance(rule, PositionLimitRule)

    def test_leverage_limit_by_enum(self, registry: RiskRuleRegistry) -> None:
        config = RiskRuleConfig(
            rule_id="r2",
            name=RiskRuleName.LEVERAGE_LIMIT,
            params={"max_leverage": Decimal("3")},
        )
        rule = registry.build(config)
        assert isinstance(rule, LeverageLimitRule)

    def test_intraday_loss_limit_by_enum(self, registry: RiskRuleRegistry) -> None:
        config = RiskRuleConfig(
            rule_id="r3",
            name=RiskRuleName.INTRADAY_LOSS_LIMIT,
            params={"max_loss": Decimal("5000")},
        )
        rule = registry.build(config)
        assert isinstance(rule, IntradayLossLimitRule)

    def test_concentration_limit_by_enum(self, registry: RiskRuleRegistry) -> None:
        config = RiskRuleConfig(
            rule_id="r4",
            name=RiskRuleName.CONCENTRATION_LIMIT,
            params={"max_fraction": Decimal("0.25")},
        )
        rule = registry.build(config)
        assert isinstance(rule, ConcentrationLimitRule)

    def test_max_notional_by_enum(self, registry: RiskRuleRegistry) -> None:
        config = RiskRuleConfig(
            rule_id="r5",
            name=RiskRuleName.MAX_NOTIONAL,
            params={"max_notional": Decimal("100000")},
        )
        rule = registry.build(config)
        assert isinstance(rule, MaxNotionalRule)

    def test_max_order_qty_by_enum(self, registry: RiskRuleRegistry) -> None:
        config = RiskRuleConfig(
            rule_id="r6",
            name=RiskRuleName.MAX_ORDER_QTY,
            params={"max_quantity": Decimal("100")},
        )
        rule = registry.build(config)
        assert isinstance(rule, MaxOrderQuantityRule)

    def test_volatility_adjusted_sizing_by_enum(self, registry: RiskRuleRegistry) -> None:
        config = RiskRuleConfig(
            rule_id="r7",
            name=RiskRuleName.VOLATILITY_ADJUSTED_SIZING,
            params={"max_notional_per_volatility": Decimal("5000")},
        )
        rule = registry.build(config)
        assert isinstance(rule, VolatilityAdjustedSizingRule)

    def test_market_data_permission_by_enum(self, registry: RiskRuleRegistry) -> None:
        config = RiskRuleConfig(rule_id="r8", name=RiskRuleName.MARKET_DATA_PERMISSION, params={})
        rule = registry.build(config)
        assert isinstance(rule, MarketDataPermissionRiskRule)

    def test_market_data_freshness_by_enum(self, registry: RiskRuleRegistry) -> None:
        config = RiskRuleConfig(rule_id="r9", name=RiskRuleName.MARKET_DATA_FRESHNESS, params={})
        rule = registry.build(config)
        assert isinstance(rule, MarketDataFreshnessRiskRule)

    def test_order_spec_validity_by_enum(self, registry: RiskRuleRegistry) -> None:
        config = RiskRuleConfig(rule_id="r10", name=RiskRuleName.ORDER_SPEC_VALIDITY, params={})
        rule = registry.build(config)
        assert isinstance(rule, OrderSpecValidityRule)

    def test_string_name_is_coerced_to_enum(self) -> None:
        """Passing a plain string should be converted to RiskRuleName in __post_init__."""
        config = RiskRuleConfig(
            rule_id="r1",
            name="position_limit",  # type: ignore[arg-type]
            params={"max_position": Decimal("10")},
        )
        assert isinstance(config.name, RiskRuleName)
        assert config.name is RiskRuleName.POSITION_LIMIT

    def test_enum_value_matches_original_dispatch_string(self) -> None:
        """Every RiskRuleName member value must match the original dispatch string."""
        expected: dict[str, str] = {
            "POSITION_LIMIT": "position_limit",
            "LEVERAGE_LIMIT": "leverage_limit",
            "INTRADAY_LOSS_LIMIT": "intraday_loss_limit",
            "CONCENTRATION_LIMIT": "concentration_limit",
            "MAX_NOTIONAL": "max_notional",
            "MAX_ORDER_QTY": "max_order_quantity",
            "VOLATILITY_ADJUSTED_SIZING": "volatility_adjusted_sizing",
            "MARKET_DATA_PERMISSION": "market_data_permission",
            "MARKET_DATA_FRESHNESS": "market_data_freshness",
            "ORDER_SPEC_VALIDITY": "order_spec_validity",
        }
        for member_name, string_value in expected.items():
            member = RiskRuleName[member_name]
            assert member.value == string_value
            # StrEnum members are also strings, so equality with raw string holds.
            assert member == string_value

    def test_unknown_name_rejected_at_config_construction(self) -> None:
        """Invalid rule names raise ValueError at config construction, not at registry dispatch."""
        with pytest.raises(ValueError):
            RiskRuleConfig(rule_id="bad", name="nonexistent_rule", params={})  # type: ignore[arg-type]

    def test_build_all_preserves_declared_order(self) -> None:
        configs = (
            RiskRuleConfig(
                rule_id="r1",
                name=RiskRuleName.POSITION_LIMIT,
                params={"max_position": Decimal("10")},
            ),
            RiskRuleConfig(
                rule_id="r2",
                name=RiskRuleName.MAX_NOTIONAL,
                params={"max_notional": Decimal("1000")},
            ),
        )
        rules = RiskRuleRegistry().build_all(configs)
        assert [type(r).__name__ for r in rules] == ["PositionLimitRule", "MaxNotionalRule"]
