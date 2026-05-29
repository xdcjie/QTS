"""Anchor smoke tests: core domain invariants that must never regress.

These tests cover five categories of domain invariants:
  a. Instrument identity -- InstrumentId is the internal identifier; asset class
     and derivative spec must be consistent.
  b. Bar interval -- all bars use [start, end) half-open intervals; end > start.
  c. Order side -- OrderSide is always a BUY/SELL enum, never a raw string.
  d. Risk decision -- RiskDecisionStatus is always APPROVED/REJECTED/MODIFIED;
     REJECTED decisions always carry a reason.
  e. Event ordering -- events have required fields present and validated.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest
from qts.core.ids import (
    CausationId,
    CorrelationId,
    EventId,
    InstrumentId,
    OrderId,
    StrategyId,
)
from qts.domain.events.event import BaseEvent
from qts.domain.events.metadata import EventMetadata
from qts.domain.instruments import (
    AssetClass,
    ContractSpec,
    FutureSpec,
    Instrument,
    OptionRight,
    OptionSpec,
    SettlementType,
)
from qts.domain.market_data import Bar
from qts.domain.orders.value_objects import OrderIntent, OrderSide
from qts.domain.risk.decision import RiskDecision, RiskDecisionStatus

# ---------------------------------------------------------------------------
# a. Instrument identity invariants
# ---------------------------------------------------------------------------


class TestInstrumentIdentityAnchors:
    """InstrumentId is the internal identifier; asset class and derivative
    spec must be consistent with the declared asset class."""

    def test_equity_must_not_have_derivative(self) -> None:
        """Equity instruments must not carry derivative metadata."""
        with pytest.raises(ValueError, match="equity instruments must not have derivative"):
            Instrument(
                instrument_id=InstrumentId("EQUITY.NYSE.AAPL"),
                asset_class=AssetClass.EQUITY,
                exchange="NYSE",
                currency="USD",
                contract_spec=ContractSpec(
                    tick_size=Decimal("0.01"),
                    lot_size=Decimal("1"),
                    multiplier=Decimal("1"),
                    settlement=SettlementType.CASH,
                    calendar_id="XNYS",
                ),
                derivative=FutureSpec(
                    expiry=date(2026, 6, 26),
                    underlying=InstrumentId("EQUITY.NYSE.AAPL"),
                    root_symbol="AAPL",
                ),
            )

    def test_future_requires_future_spec(self) -> None:
        """Future instruments must use FutureSpec, not OptionSpec."""
        with pytest.raises(ValueError, match="future instruments require FutureSpec"):
            Instrument(
                instrument_id=InstrumentId("FUTURE.COMEX.GC.202606"),
                asset_class=AssetClass.FUTURE,
                exchange="COMEX",
                currency="USD",
                contract_spec=ContractSpec(
                    tick_size=Decimal("0.10"),
                    lot_size=Decimal("1"),
                    multiplier=Decimal("100"),
                    settlement=SettlementType.PHYSICAL,
                    calendar_id="CMES",
                ),
                derivative=OptionSpec(
                    expiry=date(2026, 6, 26),
                    underlying=InstrumentId("FUTURE_ROOT.COMEX.GC"),
                    strike=Decimal("2300"),
                    right=OptionRight.CALL,
                ),
            )

    def test_option_requires_option_spec(self) -> None:
        """Option instruments must use OptionSpec, not FutureSpec."""
        with pytest.raises(ValueError, match="option instruments require OptionSpec"):
            Instrument(
                instrument_id=InstrumentId("OPTION.COMEX.GC.202606C2300"),
                asset_class=AssetClass.OPTION,
                exchange="COMEX",
                currency="USD",
                contract_spec=ContractSpec(
                    tick_size=Decimal("0.01"),
                    lot_size=Decimal("1"),
                    multiplier=Decimal("100"),
                    settlement=SettlementType.CASH,
                    calendar_id="CMES",
                ),
                derivative=FutureSpec(
                    expiry=date(2026, 6, 26),
                    underlying=InstrumentId("FUTURE_ROOT.COMEX.GC"),
                    root_symbol="GC",
                ),
            )

    def test_valid_future_instrument_constructs(self) -> None:
        """A well-formed future instrument with FutureSpec constructs cleanly."""
        instrument = Instrument(
            instrument_id=InstrumentId("FUTURE.COMEX.GC.202606"),
            asset_class=AssetClass.FUTURE,
            exchange="COMEX",
            currency="USD",
            contract_spec=ContractSpec(
                tick_size=Decimal("0.10"),
                lot_size=Decimal("1"),
                multiplier=Decimal("100"),
                settlement=SettlementType.PHYSICAL,
                calendar_id="CMES",
            ),
            derivative=FutureSpec(
                expiry=date(2026, 6, 26),
                underlying=InstrumentId("FUTURE_ROOT.COMEX.GC"),
                root_symbol="GC",
            ),
        )
        assert instrument.instrument_id == InstrumentId("FUTURE.COMEX.GC.202606")
        assert instrument.asset_class is AssetClass.FUTURE
        assert isinstance(instrument.derivative, FutureSpec)

    def test_instrument_id_rejects_empty(self) -> None:
        """InstrumentId must not be an empty string."""
        with pytest.raises(ValueError, match="must not be empty"):
            InstrumentId("")


# ---------------------------------------------------------------------------
# b. Bar interval invariants
# ---------------------------------------------------------------------------


class TestBarIntervalAnchors:
    """All bars use [start, end) half-open intervals; end must exceed start."""

    def test_bar_end_must_exceed_start(self) -> None:
        """A bar where end == start is invalid."""
        start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
        with pytest.raises(ValueError, match="start must be before end"):
            Bar(
                instrument_id=InstrumentId("FUTURE.COMEX.GC.202606"),
                start_time=start,
                end_time=start,
                timeframe="1m",
                session_id="2026-01-02",
                open=Decimal("100"),
                high=Decimal("101"),
                low=Decimal("99"),
                close=Decimal("100"),
            )

    def test_bar_end_before_start_is_invalid(self) -> None:
        """A bar where end < start is invalid."""
        start = datetime(2026, 1, 2, 14, 31, tzinfo=UTC)
        earlier = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
        with pytest.raises(ValueError, match="start must be before end"):
            Bar(
                instrument_id=InstrumentId("FUTURE.COMEX.GC.202606"),
                start_time=start,
                end_time=earlier,
                timeframe="1m",
                session_id="2026-01-02",
                open=Decimal("100"),
                high=Decimal("101"),
                low=Decimal("99"),
                close=Decimal("100"),
            )

    def test_bar_interval_is_half_open(self) -> None:
        """Bar interval includes start but excludes end."""
        start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
        end = start + timedelta(minutes=1)
        bar = Bar(
            instrument_id=InstrumentId("FUTURE.COMEX.GC.202606"),
            start_time=start,
            end_time=end,
            timeframe="1m",
            session_id="2026-01-02",
            open=Decimal("2350.10"),
            high=Decimal("2351.00"),
            low=Decimal("2349.80"),
            close=Decimal("2350.50"),
            volume=Decimal("42"),
        )
        assert bar.interval.contains(start)
        assert not bar.interval.contains(end)

    def test_bar_requires_aware_datetimes(self) -> None:
        """Bar start_time and end_time must be timezone-aware."""
        with pytest.raises(ValueError, match="timezone-aware"):
            Bar(
                instrument_id=InstrumentId("FUTURE.COMEX.GC.202606"),
                start_time=datetime(2026, 1, 2, 14, 30),
                end_time=datetime(2026, 1, 2, 14, 31),
                timeframe="1m",
                session_id="2026-01-02",
                open=Decimal("100"),
                high=Decimal("101"),
                low=Decimal("99"),
                close=Decimal("100"),
            )


# ---------------------------------------------------------------------------
# c. OrderSide invariants
# ---------------------------------------------------------------------------


class TestOrderSideAnchors:
    """OrderSide is always BUY or SELL enum, never raw strings."""

    def test_order_side_members_are_buy_and_sell_only(self) -> None:
        """The OrderSide enum has exactly BUY and SELL members."""
        member_names = {m.name for m in OrderSide}
        assert member_names == {"BUY", "SELL"}

    def test_order_side_is_str_enum(self) -> None:
        """OrderSide is a StrEnum, not a plain string."""
        assert isinstance(OrderSide.BUY, str)
        assert isinstance(OrderSide.SELL, str)
        # Must be enum members, not bare strings
        assert type(OrderSide.BUY) is OrderSide
        assert type(OrderSide.SELL) is OrderSide
        assert OrderSide("buy") is OrderSide.BUY
        assert OrderSide("sell") is OrderSide.SELL

    def test_order_intent_uses_enum_not_string(self) -> None:
        """OrderIntent.side must be an OrderSide enum member, not a plain str."""
        intent = OrderIntent(
            order_id=OrderId("ORD-001"),
            instrument_id=InstrumentId("FUTURE.COMEX.GC.202606"),
            side=OrderSide.BUY,
            quantity=Decimal("10"),
        )
        assert isinstance(intent.side, OrderSide)
        assert intent.side is OrderSide.BUY

    def test_invalid_order_side_raises(self) -> None:
        """Constructing OrderSide from an invalid string raises ValueError."""
        with pytest.raises(ValueError):
            OrderSide("hold")


# ---------------------------------------------------------------------------
# d. Risk decision invariants
# ---------------------------------------------------------------------------


class TestRiskDecisionAnchors:
    """RiskDecisionStatus is always APPROVED/REJECTED/MODIFIED;
    REJECTED decisions always carry a reason."""

    def test_risk_decision_status_members(self) -> None:
        """The RiskDecisionStatus enum has exactly APPROVED, REJECTED, MODIFIED."""
        member_names = {m.name for m in RiskDecisionStatus}
        assert member_names == {"APPROVED", "REJECTED", "MODIFIED"}

    def test_rejected_decision_requires_reason(self) -> None:
        """A REJECTED decision must always have a non-empty reason."""
        decision = RiskDecision.rejected(
            reason_code="MAX_POSITION",
            reason="Position exceeds maximum allowed",
        )
        assert decision.status is RiskDecisionStatus.REJECTED
        assert decision.reason is not None
        assert decision.reason.strip() != ""
        assert decision.reason_code is not None
        assert decision.reason_code.strip() != ""

    def test_rejected_decision_rejects_empty_reason_code(self) -> None:
        """Constructing a rejected decision with empty reason_code raises."""
        with pytest.raises(ValueError, match="reason_code must not be empty"):
            RiskDecision.rejected(reason_code="", reason="some reason")

    def test_rejected_decision_rejects_empty_reason(self) -> None:
        """Constructing a rejected decision with empty reason raises."""
        with pytest.raises(ValueError, match="reason must not be empty"):
            RiskDecision.rejected(reason_code="LIMIT", reason="")

    def test_approved_decision_has_no_reason(self) -> None:
        """An APPROVED decision has reason=None by default."""
        decision = RiskDecision.approve()
        assert decision.status is RiskDecisionStatus.APPROVED
        assert decision.reason is None
        assert decision.reason_code is None

    def test_modified_decision_status(self) -> None:
        """A MODIFIED decision can be constructed directly."""
        decision = RiskDecision(
            status=RiskDecisionStatus.MODIFIED,
            reason_code="SIZE_LIMIT",
            reason="Quantity reduced to position limit",
        )
        assert decision.status is RiskDecisionStatus.MODIFIED
        assert decision.reason is not None


# ---------------------------------------------------------------------------
# e. Event ordering invariants
# ---------------------------------------------------------------------------


class TestEventOrderingAnchors:
    """Events have required fields present and validated."""

    def test_base_event_requires_all_core_fields(self) -> None:
        """BaseEvent must carry event_id, event_type, event_time, source,
        and partition_key -- all non-empty."""
        event = BaseEvent(
            event_id=EventId("EVT-001"),
            event_type="order.submitted",
            event_time=datetime(2026, 1, 2, 9, 30, tzinfo=UTC),
            source="OrderManager",
            partition_key="ORD-001",
        )
        assert event.event_id == EventId("EVT-001")
        assert event.event_type == "order.submitted"
        assert event.source == "OrderManager"
        assert event.partition_key == "ORD-001"

    def test_base_event_rejects_empty_event_type(self) -> None:
        """BaseEvent with an empty event_type raises ValueError."""
        with pytest.raises(ValueError, match="event_type must not be empty"):
            BaseEvent(
                event_id=EventId("EVT-002"),
                event_type="",
                event_time=datetime(2026, 1, 2, 9, 30, tzinfo=UTC),
                source="OrderManager",
                partition_key="ORD-001",
            )

    def test_base_event_rejects_naive_datetime(self) -> None:
        """BaseEvent event_time must be timezone-aware."""
        with pytest.raises(ValueError, match="timezone-aware"):
            BaseEvent(
                event_id=EventId("EVT-003"),
                event_type="order.submitted",
                event_time=datetime(2026, 1, 2, 9, 30),
                source="OrderManager",
                partition_key="ORD-001",
            )

    def test_base_event_rejects_empty_source(self) -> None:
        """BaseEvent with an empty source raises ValueError."""
        with pytest.raises(ValueError, match="source must not be empty"):
            BaseEvent(
                event_id=EventId("EVT-004"),
                event_type="order.submitted",
                event_time=datetime(2026, 1, 2, 9, 30, tzinfo=UTC),
                source="",
                partition_key="ORD-001",
            )

    def test_event_metadata_requires_event_type_and_time(self) -> None:
        """EventMetadata enforces non-empty event_type and aware event_time."""
        meta = EventMetadata(
            event_id=EventId("EVT-005"),
            event_type="fill",
            event_time=datetime(2026, 1, 2, 9, 30, 5, tzinfo=UTC),
            source_actor="ExecutionActor",
            strategy_id=StrategyId("STRAT-1"),
        )
        assert meta.event_type == "fill"
        assert meta.strategy_id == StrategyId("STRAT-1")

    def test_event_metadata_rejects_empty_event_type(self) -> None:
        """EventMetadata with empty event_type raises ValueError."""
        with pytest.raises(ValueError, match="event_type must not be empty"):
            EventMetadata(
                event_id=EventId("EVT-006"),
                event_type="  ",
                event_time=datetime(2026, 1, 2, 9, 30, tzinfo=UTC),
            )

    def test_event_metadata_rejects_negative_seq(self) -> None:
        """EventMetadata seq, if provided, must be non-negative."""
        with pytest.raises(ValueError, match="seq must be non-negative"):
            EventMetadata(
                event_id=EventId("EVT-007"),
                event_type="fill",
                event_time=datetime(2026, 1, 2, 9, 30, tzinfo=UTC),
                seq=-1,
            )

    def test_base_event_optional_correlation_and_causation(self) -> None:
        """BaseEvent correlation_id and causation_id are optional trace
        fields that default to None."""
        event = BaseEvent(
            event_id=EventId("EVT-008"),
            event_type="order.accepted",
            event_time=datetime(2026, 1, 2, 9, 30, tzinfo=UTC),
            source="BrokerAdapter",
            partition_key="ORD-001",
            correlation_id=CorrelationId("CORR-001"),
            causation_id=CausationId("CAUS-001"),
        )
        assert event.correlation_id == CorrelationId("CORR-001")
        assert event.causation_id == CausationId("CAUS-001")

        # Without correlation/causation
        event_minimal = BaseEvent(
            event_id=EventId("EVT-009"),
            event_type="order.accepted",
            event_time=datetime(2026, 1, 2, 9, 30, tzinfo=UTC),
            source="BrokerAdapter",
            partition_key="ORD-001",
        )
        assert event_minimal.correlation_id is None
        assert event_minimal.causation_id is None
