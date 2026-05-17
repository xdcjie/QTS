"""Unit anchor: ParameterSpace + ParameterGrid cartesian product."""

from __future__ import annotations

from decimal import Decimal

import pytest
from qts.research.optimizer import ParameterGrid, ParameterSpace


def test_single_space_yields_value_per_combination() -> None:
    space = ParameterSpace(name="window", values=(5, 10, 20))
    grid = ParameterGrid(space)
    combinations = list(grid)
    assert combinations == [{"window": 5}, {"window": 10}, {"window": 20}]


def test_two_spaces_yield_cartesian_product_in_stable_order() -> None:
    grid = ParameterGrid(
        ParameterSpace(name="window", values=(5, 10)),
        ParameterSpace(name="threshold", values=(Decimal("0.1"), Decimal("0.2"))),
    )
    combinations = list(grid)
    assert combinations == [
        {"window": 5, "threshold": Decimal("0.1")},
        {"window": 5, "threshold": Decimal("0.2")},
        {"window": 10, "threshold": Decimal("0.1")},
        {"window": 10, "threshold": Decimal("0.2")},
    ]


def test_empty_space_rejected() -> None:
    with pytest.raises(ValueError, match="must contain at least one value"):
        ParameterSpace(name="window", values=())


def test_duplicate_parameter_names_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate parameter names"):
        ParameterGrid(
            ParameterSpace(name="window", values=(5,)),
            ParameterSpace(name="window", values=(10,)),
        )


def test_grid_size_matches_product_of_space_sizes() -> None:
    grid = ParameterGrid(
        ParameterSpace(name="a", values=(1, 2)),
        ParameterSpace(name="b", values=(3, 4, 5)),
        ParameterSpace(name="c", values=(6, 7)),
    )
    assert grid.size() == 12
