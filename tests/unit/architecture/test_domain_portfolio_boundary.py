from __future__ import annotations

import importlib.util
from pathlib import Path


def test_domain_portfolio_empty_package_is_not_a_source_boundary() -> None:
    assert not Path("backend/src/qts/domain/portfolio").exists()
    assert importlib.util.find_spec("qts.domain.portfolio") is None


def test_order_route_metadata_is_not_owned_by_domain() -> None:
    import qts.domain.orders as orders
    from qts.runtime.order_route_metadata import OrderRouteMetadata

    assert importlib.util.find_spec("qts.domain.orders.route_metadata") is None
    assert not hasattr(orders, "OrderRouteMetadata")
    assert OrderRouteMetadata.__module__ == "qts.runtime.order_route_metadata"
