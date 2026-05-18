# Signal Portfolio Construction V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an optional Insight-like signal layer and a minimal portfolio-construction model that converts signals into existing `TargetIntent` objects.

**Architecture:** `Signal` is a Strategy SDK value object, not an order. `PortfolioConstructionModel` consumes active signals and emits `TargetIntent` instances through existing SDK types. Existing direct target APIs remain unchanged for simple strategies.

**Tech Stack:** Python dataclasses, `StrEnum`, `Decimal`, existing `AssetRef`, existing `TargetIntent`, `pytest`, guardrails.

---

## Domain Fact / Invariant

Signals express forecasts; they are not portfolio state, risk decisions, orders, or fills.
The trading path remains:

```text
Signal -> PortfolioConstructionModel -> TargetIntent -> RiskEngine -> OrderManagerActor -> ExecutionActor -> AccountActor
```

Correct owner or abstraction boundary:

- `qts.strategy_sdk.signals` owns user-facing signal value objects.
- `qts.strategy_sdk.portfolio_construction` owns signal-to-target mapping.
- Runtime, risk, order, execution, and account actors keep their existing responsibilities.

Forbidden shortcut:

- Do not allow `Signal` to import execution, risk, runtime, broker adapters, `ContractSpec`, or `BrokerSymbolMapping`.
- Do not let portfolio construction place orders.
- Do not replace existing `ctx.target_*` APIs.

Required gates / verification:

- SDK unit tests proving validation and target conversion.
- Integration test proving generated `TargetIntent` still flows through existing risk/order path.
- `make guardrails` to protect Strategy SDK boundaries.

## File Structure

| Path | Action | Responsibility |
|---|---|---|
| `backend/src/qts/strategy_sdk/signals.py` | Create | Direction, horizon, confidence, source model, and group metadata |
| `backend/src/qts/strategy_sdk/portfolio_construction.py` | Create | Minimal equal-weight and explicit-weight signal-to-target construction |
| `backend/src/qts/strategy_sdk/context.py` | Modify | Optional `emit_signal` and `construct_targets` convenience methods |
| `backend/src/qts/strategy_sdk/__init__.py` | Modify | Export public SDK types |
| `docs/research/signal_model_v1.md` | Create | Durable signal/portfolio-construction contract |
| `docs/strategy_sdk/strategy_api.md` | Modify | Document optional signal path next to target APIs |
| `tests/unit/strategy_sdk/test_signals.py` | Create | Signal validation and grouping |
| `tests/unit/strategy_sdk/test_portfolio_construction.py` | Create | Signal-to-target mapping |
| `tests/integration/test_signal_portfolio_target_flow.py` | Create | Runtime path integration smoke |

## Acceptance Evidence

| Evidence | Command |
|---|---|
| First red signal gate | `uv run pytest tests/unit/strategy_sdk/test_signals.py::test_signal_requires_direction_and_source_model -q` |
| SDK unit green | `uv run pytest tests/unit/strategy_sdk/test_signals.py tests/unit/strategy_sdk/test_portfolio_construction.py -q` |
| Runtime path green | `uv run pytest tests/integration/test_signal_portfolio_target_flow.py -q` |
| Boundary green | `make guardrails` |
| Normal verification | `make format && make lint && make typecheck && make test-unit && make test-integration` |

### Task 1: Add Signal Value-Object Tests

**Files:**
- Create: `tests/unit/strategy_sdk/test_signals.py`

- [ ] **Step 1: Write the failing signal tests**

```python
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from qts.core.ids import InstrumentId
from qts.strategy_sdk.asset_ref import AssetRef
from qts.strategy_sdk.signals import Signal, SignalDirection


def _asset(symbol: str) -> AssetRef:
    return AssetRef(
        instrument_id=InstrumentId(f"EQUITY.US.NASDAQ.{symbol}"),
        symbol=symbol,
    )


def test_signal_requires_direction_and_source_model() -> None:
    asset = _asset("AAPL")
    with pytest.raises(ValueError, match="source_model is required"):
        Signal(
            asset=asset,
            direction=SignalDirection.UP,
            generated_at=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
            horizon=timedelta(days=1),
            source_model="",
        )


def test_signal_confidence_is_normalized_decimal() -> None:
    signal = Signal(
        asset=_asset("AAPL"),
        direction=SignalDirection.UP,
        generated_at=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
        horizon=timedelta(days=1),
        source_model="momentum-v1",
        confidence=Decimal("0.75"),
    )

    assert signal.confidence == Decimal("0.75")
```

- [ ] **Step 2: Run the red gate**

Run: `uv run pytest tests/unit/strategy_sdk/test_signals.py::test_signal_requires_direction_and_source_model -q`

Expected: fail with an import error for `qts.strategy_sdk.signals`.

### Task 2: Implement Signal Types

**Files:**
- Create: `backend/src/qts/strategy_sdk/signals.py`
- Modify: `backend/src/qts/strategy_sdk/__init__.py`

- [ ] **Step 1: Add minimal signal implementation**

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import StrEnum

from qts.core.time import require_aware_datetime
from qts.strategy_sdk.asset_ref import AssetRef


class SignalDirection(StrEnum):
    UP = "up"
    DOWN = "down"
    FLAT = "flat"


@dataclass(frozen=True, slots=True)
class Signal:
    asset: AssetRef
    direction: SignalDirection
    generated_at: datetime
    horizon: timedelta
    source_model: str
    confidence: Decimal = Decimal("1")
    magnitude: Decimal | None = None
    weight: Decimal | None = None
    group_id: str | None = None

    def __post_init__(self) -> None:
        require_aware_datetime(self.generated_at, name="generated_at")
        if self.horizon <= timedelta(0):
            raise ValueError("horizon must be positive")
        if not self.source_model.strip():
            raise ValueError("source_model is required")
        if self.confidence < Decimal("0") or self.confidence > Decimal("1"):
            raise ValueError("confidence must be in [0, 1]")
```

- [ ] **Step 2: Export public SDK types**

Add `Signal` and `SignalDirection` to `backend/src/qts/strategy_sdk/__init__.py`.

- [ ] **Step 3: Run signal unit tests**

Run: `uv run pytest tests/unit/strategy_sdk/test_signals.py -q`

Expected: tests pass.

### Task 3: Add Portfolio Construction

**Files:**
- Create: `backend/src/qts/strategy_sdk/portfolio_construction.py`
- Create: `tests/unit/strategy_sdk/test_portfolio_construction.py`

- [ ] **Step 1: Write failing portfolio-construction test**

```python
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.strategy_sdk.asset_ref import AssetRef
from qts.strategy_sdk.portfolio_construction import EqualWeightSignalPortfolioConstruction
from qts.strategy_sdk.signals import Signal, SignalDirection
from qts.strategy_sdk.target import TargetIntentType


def _asset(symbol: str) -> AssetRef:
    return AssetRef(
        instrument_id=InstrumentId(f"EQUITY.US.NASDAQ.{symbol}"),
        symbol=symbol,
    )


def test_equal_weight_construction_turns_up_down_flat_signals_into_targets() -> None:
    aapl = _asset("AAPL")
    msft = _asset("MSFT")
    model = EqualWeightSignalPortfolioConstruction(gross_exposure=Decimal("1"))

    targets = model.construct(
        (
            Signal(aapl, SignalDirection.UP, datetime(2026, 1, 2, tzinfo=UTC), timedelta(days=1), "m1"),
            Signal(msft, SignalDirection.DOWN, datetime(2026, 1, 2, tzinfo=UTC), timedelta(days=1), "m1"),
        )
    )

    assert [target.intent_type for target in targets] == [
        TargetIntentType.PERCENT,
        TargetIntentType.PERCENT,
    ]
    assert {target.asset: target.value for target in targets} == {
        aapl: Decimal("0.5"),
        msft: Decimal("-0.5"),
    }
```

- [ ] **Step 2: Implement minimal construction model**

```python
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from qts.strategy_sdk.signals import Signal, SignalDirection
from qts.strategy_sdk.target import TargetIntent, TargetIntentType


class PortfolioConstructionModel(Protocol):
    def construct(self, signals: tuple[Signal, ...]) -> tuple[TargetIntent, ...]:
        ...


@dataclass(frozen=True, slots=True)
class EqualWeightSignalPortfolioConstruction:
    gross_exposure: Decimal = Decimal("1")

    def __post_init__(self) -> None:
        if self.gross_exposure <= Decimal("0"):
            raise ValueError("gross_exposure must be positive")

    def construct(self, signals: tuple[Signal, ...]) -> tuple[TargetIntent, ...]:
        directional = tuple(signal for signal in signals if signal.direction != SignalDirection.FLAT)
        if not directional:
            return tuple(
                TargetIntent(signal.asset, TargetIntentType.CLOSE, None)
                for signal in signals
                if signal.direction == SignalDirection.FLAT
            )
        unit = self.gross_exposure / Decimal(len(directional))
        targets: list[TargetIntent] = []
        for signal in signals:
            if signal.direction == SignalDirection.FLAT:
                targets.append(TargetIntent(signal.asset, TargetIntentType.CLOSE, None))
            elif signal.direction == SignalDirection.UP:
                targets.append(TargetIntent(signal.asset, TargetIntentType.PERCENT, unit))
            else:
                targets.append(TargetIntent(signal.asset, TargetIntentType.PERCENT, -unit))
        return tuple(targets)
```

- [ ] **Step 3: Run portfolio construction tests**

Run: `uv run pytest tests/unit/strategy_sdk/test_portfolio_construction.py -q`

Expected: tests pass.

### Task 4: Context Convenience And Runtime Path Smoke

**Files:**
- Modify: `backend/src/qts/strategy_sdk/context.py`
- Create: `tests/integration/test_signal_portfolio_target_flow.py`
- Create: `docs/research/signal_model_v1.md`
- Modify: `docs/strategy_sdk/strategy_api.md`

- [ ] **Step 1: Add context convenience without changing existing target APIs**

Add private `_signals: list[Signal]`, property `signals`, and method:

```python
def emit_signal(self, signal: Signal) -> Signal:
    self._signals.append(signal)
    return signal

def construct_targets(
    self,
    model: PortfolioConstructionModel,
) -> tuple[TargetIntent, ...]:
    targets = model.construct(tuple(self._signals))
    for target in targets:
        self._intent_emitter.emit(target)
    return targets
```

- [ ] **Step 2: Add integration smoke**

The integration test should instantiate a small strategy that emits a signal,
constructs targets, and then run the existing backtest flow. Assert that the
manifest contains orders produced through the existing path and that no strategy
code imports execution/risk/runtime internals.

Run: `uv run pytest tests/integration/test_signal_portfolio_target_flow.py -q`

Expected: `1 passed`.

- [ ] **Step 3: Write durable docs**

`docs/research/signal_model_v1.md` must state:

- signals are forecasts, not orders;
- portfolio construction emits existing `TargetIntent`;
- risk/order/execution/account ownership is unchanged;
- direct target APIs remain supported.

### Task 5: Verification And Matrix Update

Run:

```bash
make format
make lint
make guardrails
make typecheck
uv run pytest tests/unit/strategy_sdk/test_signals.py tests/unit/strategy_sdk/test_portfolio_construction.py tests/integration/test_signal_portfolio_target_flow.py -q
```

Expected: all commands exit 0. Update the SIG-1 matrix row only after recording the first red gate, focused green evidence, broad verification, and commit hash.
