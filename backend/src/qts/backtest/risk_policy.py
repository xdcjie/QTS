"""Backtest risk/margin policy construction.

Owns turning a backtest run's risk config + instrument registry into a
``RiskEngine`` and an optional account-wide ``MarginCalculator``, so the engine
itself does not own risk-rule-registry or margin-calculator construction.
"""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal

from qts.domain.instruments import AssetClass
from qts.registry.instrument_registry import InstrumentRegistry
from qts.risk.config import RiskRuleConfig, RiskRuleName
from qts.risk.margin.calculator import MarginCalculator
from qts.risk.risk_engine import RiskEngine
from qts.risk.rule_registry import RiskRuleRegistry


class BacktestMarginPolicyResolver:
    """Resolve the account-wide margin rate/calculator from instrument specs."""

    def resolve_initial_margin_rate(
        self, instrument_registry: InstrumentRegistry | None
    ) -> Decimal | None:
        """Resolve a single account-wide initial-margin rate from the registry.

        The margin rate is a per-contract product fact owned by ``ContractSpec``.
        Returns ``None`` when no registered instrument configures a rate (margin
        enforcement stays disabled). When more than one distinct rate is
        configured the run is rejected, because the account-wide
        ``MarginCalculator`` cannot represent conflicting per-contract rates;
        this fails closed on misconfiguration rather than silently picking one.
        """
        if instrument_registry is None:
            return None
        missing_futures_margin = [
            instrument.instrument_id.value
            for instrument in instrument_registry.instruments()
            if instrument.asset_class is AssetClass.FUTURE
            and instrument.tradable
            and instrument.contract_spec.initial_margin_rate is None
        ]
        if missing_futures_margin:
            raise ValueError(
                "futures instruments missing initial_margin_rate: "
                + ", ".join(sorted(missing_futures_margin))
            )
        specs = instrument_registry.contract_specs()
        if not isinstance(specs, Iterable):
            raise TypeError("instrument_registry.contract_specs() must return an iterable")
        rates = {spec.initial_margin_rate for spec in specs if spec.initial_margin_rate is not None}
        if not rates:
            return None
        if len(rates) > 1:
            raise ValueError(
                "multiple distinct initial_margin_rate values configured; "
                "the account-wide margin gate requires a single rate"
            )
        return rates.pop()

    def margin_calculator(self, margin_rate: Decimal | None) -> MarginCalculator | None:
        """Return an account-wide ``MarginCalculator`` for the rate, or ``None``."""
        if margin_rate is None:
            return None
        return MarginCalculator(
            initial_margin_rate=margin_rate,
            maintenance_margin_rate=margin_rate,
        )


class BacktestRiskPolicyFactory:
    """Build the config-driven ``RiskEngine`` (+ optional margin) for a backtest run."""

    def __init__(self, margin_resolver: BacktestMarginPolicyResolver | None = None) -> None:
        self._margin_resolver = margin_resolver or BacktestMarginPolicyResolver()

    def build(
        self,
        *,
        max_notional: Decimal,
        instrument_registry: InstrumentRegistry | None,
    ) -> tuple[RiskEngine, MarginCalculator | None]:
        """Return the run's ``(RiskEngine, MarginCalculator | None)``."""
        margin_rate = self._margin_resolver.resolve_initial_margin_rate(instrument_registry)
        risk_engine = self.build_risk_engine(
            max_notional=max_notional,
            margin_enabled=margin_rate is not None,
        )
        return risk_engine, self._margin_resolver.margin_calculator(margin_rate)

    def build_risk_engine(self, *, max_notional: Decimal, margin_enabled: bool) -> RiskEngine:
        """Build the ``RiskEngine`` from the config-driven rule set."""
        return RiskEngine(
            list(
                RiskRuleRegistry().build_all(
                    self.risk_rule_configs(
                        max_notional=max_notional,
                        margin_enabled=margin_enabled,
                    )
                )
            )
        )

    @staticmethod
    def risk_rule_configs(
        *,
        max_notional: Decimal,
        margin_enabled: bool,
    ) -> tuple[RiskRuleConfig, ...]:
        """Return the config-driven risk rule set for a backtest run.

        ``MaxNotionalRule`` is always present (the historical default). The
        per-contract margin gate is appended only when a margin rate is
        resolvable from the instrument registry, so runs without a configured
        margin rate behave exactly as before (no fail-closed margin rejection).
        """
        configs = [
            RiskRuleConfig(
                rule_id="max_notional",
                name=RiskRuleName.MAX_NOTIONAL,
                params={"max_notional": max_notional},
            )
        ]
        if margin_enabled:
            configs.append(
                RiskRuleConfig(rule_id="margin_limit", name=RiskRuleName.MARGIN_LIMIT, params={})
            )
        return tuple(configs)


__all__ = ["BacktestMarginPolicyResolver", "BacktestRiskPolicyFactory"]
