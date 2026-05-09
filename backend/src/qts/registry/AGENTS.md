# Registry Rules

This module owns instrument metadata, calendars, and symbol mappings.

Rules:

- InstrumentRegistry is the source of truth for instrument metadata.
- Broker symbols and market-data symbols must be mapped at system boundaries.
- Internal modules must use InstrumentId.
- Continuous futures are research/data references and must not be directly tradable.
- Option contracts must include underlying, expiry, strike, and right.
- Use `exchange-calendars` as the preferred base implementation for calendar behavior when supported, behind project interfaces.
