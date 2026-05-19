from __future__ import annotations

import importlib.util
from pathlib import Path


def test_domain_portfolio_empty_package_is_not_a_source_boundary() -> None:
    assert not Path("backend/src/qts/domain/portfolio").exists()
    assert importlib.util.find_spec("qts.domain.portfolio") is None
