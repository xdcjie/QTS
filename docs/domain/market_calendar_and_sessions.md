# Market Calendar and Sessions

## Preferred implementation

Use `exchange-calendars` as the default implementation aid for exchange sessions, holidays, opens, closes, and special sessions when supported.

## Correctness rule

The calendar library is not the source of truth for project-level financial invariants. If a product-specific rule differs from the library, implement an adapter/override and add anchor tests.

## Time model

- Sessions use half-open intervals: `[start, end)`.
- Session definitions are domain facts.
- UTC, ET, CST, and local machine time are timestamp representations.
- Timezone conversion must not change session semantics.

## COMEX Gold anchor

If COMEX Gold regular session is `[ET 18:00, ET 17:00)`, then:

- The session is exchange-time defined.
- A full normal session lasts 23 hours.
- Excluding holidays and early-close / late-open sessions, 1-minute bars should count `23 * 60 = 1380`.
- Producing 1440, 1379, or timezone-dependent counts for the same full session is incorrect.

The implementation must preserve this as a product-specific override when a generic calendar library
does not directly expose the contract session in this form. The session date is the close date: a
regular session for `2026-01-06` opens at `2026-01-05 18:00 ET` and closes at
`2026-01-06 17:00 ET`, represented internally as the same half-open interval in UTC.
