"""Contract tests for the shared research value-coercion helpers."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from qts.research.coercion import (
    float_mapping,
    iso_date,
    iso_datetime,
    nested_float_mapping,
    optional_bool,
    optional_decimal,
    optional_int,
    optional_mapping,
    optional_non_negative_int,
    optional_string_tuple,
    required_mapping,
    string_tuple,
)


def test_optional_scalars_pass_none_through() -> None:
    assert optional_decimal(None) is None
    assert optional_int(None) is None
    assert optional_string_tuple(None) is None
    assert optional_mapping(None) is None
    assert nested_float_mapping(None, field_name="x") is None


def test_optional_decimal_parses_and_rejects() -> None:
    assert optional_decimal("1.5") == Decimal("1.5")
    with pytest.raises(ValueError, match="must be a decimal"):
        optional_decimal("not-a-number")


def test_optional_bool_requires_real_bool() -> None:
    assert optional_bool(True) is True
    with pytest.raises(ValueError, match="must be a boolean"):
        optional_bool(1)


def test_optional_non_negative_int_rejects_negative() -> None:
    assert optional_non_negative_int("3") == 3
    assert optional_non_negative_int(None) is None
    with pytest.raises(ValueError, match="non-negative"):
        optional_non_negative_int(-1)


def test_string_tuple_normalizes_sequence() -> None:
    assert string_tuple(None) == ()
    assert string_tuple([1, "a"]) == ("1", "a")
    with pytest.raises(ValueError, match="must be a sequence"):
        string_tuple("scalar-not-allowed-as-list")  # str is not list|tuple


def test_required_mapping_demands_dict() -> None:
    assert required_mapping({"cfg": {"a": 1}}, "cfg") == {"a": 1}
    with pytest.raises(ValueError, match="must be a mapping"):
        required_mapping({"cfg": 5}, "cfg")


def test_float_mappings() -> None:
    assert float_mapping({"a": 1, "b": "2.5"}, field_name="m") == {"a": 1.0, "b": 2.5}
    with pytest.raises(ValueError, match="non-empty mapping"):
        float_mapping({}, field_name="m")
    assert nested_float_mapping({"x": {"a": 1}}, field_name="m") == {"x": {"a": 1.0}}


def test_iso_date_and_datetime() -> None:
    assert iso_date("2026-05-31", "d") == date(2026, 5, 31)
    assert iso_date(date(2026, 5, 31), "d") == date(2026, 5, 31)
    with pytest.raises(ValueError, match="must be an ISO date"):
        iso_date("31/05/2026", "d")

    # naive datetimes and bare dates are anchored to UTC; trailing Z is honored
    assert iso_datetime("2026-05-31", "t") == datetime(2026, 5, 31, tzinfo=UTC)
    assert iso_datetime("2026-05-31T12:00:00Z", "t") == datetime(2026, 5, 31, 12, tzinfo=UTC)
    naive = datetime(2026, 5, 31, 9, 30)
    assert iso_datetime(naive, "t") == naive.replace(tzinfo=UTC)
