# ResearchBook V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a read-only `ResearchBook` facade that gives notebooks and scripts a QuantBook-style way to request bounded QTS historical bars without exposing runtime, broker, actor, or order internals.

**Architecture:** `ResearchBookConfig` owns catalog construction inputs, `ResearchBook` owns read-only historical queries, and `HistoryRequest` describes one bounded query. The facade delegates to `HistoricalCatalog` and `HistoricalBarStream`; it does not own CSV parsing, futures roll rules, sessions, or backtest execution.

**Tech Stack:** Python dataclasses, existing `HistoricalCatalog`, existing `iter_historical_bars`, `pytest`, `ruff`, `mypy`.

---

## Domain Fact / Invariant

Research history access is read-only. It must preserve QTS `[start, end)` bar semantics,
`InstrumentId` identity, historical catalog provenance, and source/session rules owned by
`qts.data.historical`, `qts.data.sessions`, and `qts.registry`.

Correct owner or abstraction boundary:

- `qts.research.research_book` owns the research-facing facade and request validation.
- `qts.data.historical` owns CSV parsing and catalog loading.
- `qts.registry` owns instrument and futures roll semantics.

Forbidden shortcut:

- Do not parse CSV rows directly in `qts.research`.
- Do not expose `BacktestEngine`, actors, broker adapters, `RiskEngine`, or `OrderManagerActor`.
- Do not add a new storage dependency.

Required gates / verification:

- Unit tests for request validation and half-open bounded query behavior.
- Integration test proving `ResearchBook.from_backtest_config(...)` reads through `HistoricalCatalog`.
- `make guardrails`, `make test-unit`, and `make test-integration`.

## File Structure

| Path | Action | Responsibility |
|---|---|---|
| `backend/src/qts/research/research_book.py` | Create | ResearchBook config, request, result frame, and read-only history API |
| `backend/src/qts/research/__init__.py` | Modify | Export the public research facade |
| `docs/research/research_book_v1.md` | Create | Durable public research API contract |
| `tests/unit/research/test_research_book.py` | Create | Request/config/result behavior |
| `tests/integration/test_research_book_historical_catalog.py` | Create | Config-driven historical catalog integration |
| `docs/plan/2026-05-18_lean_research_workflow_status_matrix.md` | Modify | Record evidence after implementation |

## Acceptance Evidence

| Evidence | Command |
|---|---|
| First red request/config gate | `uv run pytest tests/unit/research/test_research_book.py::test_research_book_config_rejects_missing_catalog_reference -q` |
| Focused unit green | `uv run pytest tests/unit/research/test_research_book.py -q` |
| Catalog integration green | `uv run pytest tests/integration/test_research_book_historical_catalog.py -q` |
| Boundary gate | `make guardrails` |
| Normal verification | `make format && make lint && make typecheck && make test-unit` |

### Task 1: Add ResearchBook Contract Tests

**Files:**
- Create: `tests/unit/research/test_research_book.py`
- Create: `docs/research/research_book_v1.md`

- [ ] **Step 1: Write the failing config/request tests**

```python
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from qts.research import HistoryRequest, ResearchBookConfig


def test_research_book_config_rejects_missing_catalog_reference() -> None:
    with pytest.raises(ValueError, match="catalog_name is required"):
        ResearchBookConfig(
            data_config_path=Path("configs/data/historical.local.yaml"),
            catalog_name="",
            roots=("GC",),
            timeframe="1m",
        )


def test_history_request_uses_half_open_interval() -> None:
    request = HistoryRequest(
        root="GC",
        start=datetime(2026, 1, 1, tzinfo=UTC),
        end=datetime(2026, 1, 2, tzinfo=UTC),
        timeframe="1m",
    )

    assert request.includes(datetime(2026, 1, 1, tzinfo=UTC))
    assert not request.includes(datetime(2026, 1, 2, tzinfo=UTC))
```

- [ ] **Step 2: Run the red gate**

Run: `uv run pytest tests/unit/research/test_research_book.py::test_research_book_config_rejects_missing_catalog_reference -q`

Expected: fail with an import error for `HistoryRequest` or `ResearchBookConfig`.

- [ ] **Step 3: Write `docs/research/research_book_v1.md`**

Include this contract:

```markdown
# ResearchBook API v1

`ResearchBook` is a read-only research facade for notebooks and scripts.

It may:
- load a configured `HistoricalCatalog`;
- request bounded historical bars through QTS historical data boundaries;
- return deterministic row-like research frames;
- expose dataset IDs for experiment manifests.

It must not:
- mutate portfolio, account, order, runtime, or broker state;
- parse source CSV rows directly;
- create orders or target intents;
- redefine sessions, roll rules, or bar intervals.
```

### Task 2: Implement ResearchBook Value Objects

**Files:**
- Create: `backend/src/qts/research/research_book.py`
- Modify: `backend/src/qts/research/__init__.py`

- [ ] **Step 1: Add the minimal value objects**

```python
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from qts.core.time import TimeInterval, require_aware_datetime
from qts.data.historical.catalog import HistoricalCatalog, HistoricalCatalogLoadConfig
from qts.data.historical.csv_dataset import iter_historical_bars
from qts.domain.market_data import Bar


@dataclass(frozen=True, slots=True)
class ResearchBookConfig:
    data_config_path: Path
    catalog_name: str
    roots: tuple[str, ...]
    timeframe: str

    def __post_init__(self) -> None:
        if not self.catalog_name.strip():
            raise ValueError("catalog_name is required")
        if not self.roots:
            raise ValueError("roots must not be empty")
        if not self.timeframe.strip():
            raise ValueError("timeframe is required")
        object.__setattr__(self, "data_config_path", Path(self.data_config_path))


@dataclass(frozen=True, slots=True)
class HistoryRequest:
    root: str
    start: datetime
    end: datetime
    timeframe: str

    def __post_init__(self) -> None:
        TimeInterval(start=self.start, end=self.end)
        require_aware_datetime(self.start, name="start")
        require_aware_datetime(self.end, name="end")
        if not self.root.strip():
            raise ValueError("root is required")
        if not self.timeframe.strip():
            raise ValueError("timeframe is required")

    def includes(self, timestamp: datetime) -> bool:
        require_aware_datetime(timestamp, name="timestamp")
        return self.start <= timestamp < self.end


@dataclass(frozen=True, slots=True)
class ResearchHistoryFrame:
    bars: tuple[Bar, ...]

    def __iter__(self) -> Iterator[Bar]:
        return iter(self.bars)

    def __len__(self) -> int:
        return len(self.bars)
```

- [ ] **Step 2: Export from `qts.research`**

```python
from qts.research.research_book import (
    HistoryRequest,
    ResearchBook,
    ResearchBookConfig,
    ResearchHistoryFrame,
)
```

- [ ] **Step 3: Run the focused unit tests**

Run: `uv run pytest tests/unit/research/test_research_book.py -q`

Expected after full Task 2 implementation: tests pass.

### Task 3: Implement Read-Only History Queries

**Files:**
- Modify: `backend/src/qts/research/research_book.py`
- Create: `tests/integration/test_research_book_historical_catalog.py`

- [ ] **Step 1: Add failing history integration test**

```python
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from qts.research import HistoryRequest, ResearchBook, ResearchBookConfig


def test_research_book_history_uses_configured_historical_catalog() -> None:
    book = ResearchBook.from_config(
        ResearchBookConfig(
            data_config_path=Path("configs/data/historical.local.yaml"),
            catalog_name="research_futures",
            roots=("GC",),
            timeframe="1m",
        )
    )
    frame = book.history(
        HistoryRequest(
            root="GC",
            start=datetime(2010, 6, 6, 22, 0, tzinfo=UTC),
            end=datetime(2010, 6, 6, 22, 5, tzinfo=UTC),
            timeframe="1m",
        )
    )

    assert len(frame) > 0
    assert all(bar.start_time >= datetime(2010, 6, 6, 22, 0, tzinfo=UTC) for bar in frame)
    assert all(bar.start_time < datetime(2010, 6, 6, 22, 5, tzinfo=UTC) for bar in frame)
```

- [ ] **Step 2: Implement `ResearchBook`**

```python
class ResearchBook:
    """Read-only research facade over configured historical data."""

    def __init__(self, config: ResearchBookConfig, catalog: HistoricalCatalog) -> None:
        self._config = config
        self._catalog = catalog

    @classmethod
    def from_config(cls, config: ResearchBookConfig) -> ResearchBook:
        catalog = HistoricalCatalog.load(
            HistoricalCatalogLoadConfig.from_historical_market_data_config(
                config.data_config_path,
                catalog=config.catalog_name,
                roots=config.roots,
                requested_timeframe=config.timeframe,
            )
        )
        return cls(config=config, catalog=catalog)

    @property
    def dataset_ids(self) -> tuple[str, ...]:
        return tuple(
            f"{dataset.root}:{dataset.dataset.timeframe}:{dataset.dataset.path}"
            for dataset in self._catalog.datasets.values()
        )

    def history(self, request: HistoryRequest) -> ResearchHistoryFrame:
        root = request.root.strip().upper()
        dataset = self._catalog.datasets[root]
        stream = iter_historical_bars(
            dataset.csv_path,
            dataset.symbol_resolver,
            timeframe=request.timeframe,
            start=request.start,
            end=request.end,
            schema=dataset.csv_schema,
        )
        return ResearchHistoryFrame(bars=tuple(stream))
```

- [ ] **Step 3: Run integration test**

Run: `uv run pytest tests/integration/test_research_book_historical_catalog.py -q`

Expected: `1 passed`.

### Task 4: Verification And Matrix Update

**Files:**
- Modify: `docs/plan/2026-05-18_lean_research_workflow_status_matrix.md`

- [ ] **Step 1: Run required checks**

Run:

```bash
make format
make lint
make guardrails
make typecheck
uv run pytest tests/unit/research/test_research_book.py tests/integration/test_research_book_historical_catalog.py -q
```

Expected: all commands exit 0.

- [ ] **Step 2: Update status matrix**

Set RB-1 to `Complete` only after recording:

- first red gate command and failure mode;
- focused green commands;
- broad verification commands;
- commit hash.
