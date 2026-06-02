"""Template for implementing a reviewed research factor.

This file is documentation material. Copy the shape into the real owning module
only after review approval and test design.
"""

from __future__ import annotations

from typing import Protocol


class FactorDataView(Protocol):
    """Minimal data interface expected by the factor template."""

    def close(self, asset: str) -> object:
        """Return close-price observations for an asset."""


class ReviewedFactorTemplate:
    """Reviewed factor implementation sketch."""

    name = "replace_with_reviewed_factor_name"

    def calculate(self, data: FactorDataView, asset: str) -> object:
        """Calculate the factor without looking at future observations."""
        raise NotImplementedError("implement from the reviewed FactorSpec")
