# ADR 0005: exchange-calendars as Preferred Calendar Component

## Decision

Use `exchange-calendars` as the preferred base implementation for exchange calendars when supported.

## Rationale

Market calendar logic is complex and should not be custom-built unnecessarily.

## Consequence

The library must be wrapped behind project interfaces and validated with anchor tests for product-specific session rules.
