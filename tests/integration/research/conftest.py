from __future__ import annotations

import pytest

from tests.support.research_provenance import force_clean_reproducibility


@pytest.fixture(autouse=True)
def clean_research_provenance(monkeypatch: pytest.MonkeyPatch) -> None:
    force_clean_reproducibility(monkeypatch)
