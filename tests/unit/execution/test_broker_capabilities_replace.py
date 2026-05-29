"""Gate tests: BrokerCapabilities.supports_replace flag and its payload (DR-026)."""

from __future__ import annotations

from qts.core.ids import BrokerId
from qts.execution.broker import BrokerCapabilities


def test_supports_replace_defaults_to_false() -> None:
    capabilities = BrokerCapabilities(broker_id=BrokerId("simulated"))
    assert capabilities.supports_replace is False


def test_supports_replace_can_be_enabled() -> None:
    capabilities = BrokerCapabilities(broker_id=BrokerId("ibkr"), supports_replace=True)
    assert capabilities.supports_replace is True


def test_supports_replace_is_exported_in_manifest_payload() -> None:
    capabilities = BrokerCapabilities(broker_id=BrokerId("ibkr"), supports_replace=True)
    payload = capabilities.to_manifest_payload()
    assert payload["supports_replace"] is True
