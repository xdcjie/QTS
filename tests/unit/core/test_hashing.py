from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from qts.core.hashing import stable_json_hash
from qts.core.ids import InstrumentId


def test_stable_json_hash_is_deterministic_across_key_order() -> None:
    payload_a = {"b": Decimal("1"), "a": {"x": 1, "y": 2}}
    payload_b = {"a": {"y": 2, "x": 1}, "b": Decimal("1")}

    assert stable_json_hash(payload_a) == stable_json_hash(payload_b)


def test_stable_json_hash_supports_domain_value_types() -> None:
    payload = {
        "instrument_id": InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        "moment": datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
    }
    hashed = stable_json_hash(payload)
    assert hashed.startswith("sha256:")
