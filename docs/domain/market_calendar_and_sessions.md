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

### Daylight-saving transition bar counts

`1380` is the **normal non-transition** count, not a universal invariant. The
exchange-local session window `[ET 18:00, ET 17:00)` is constant year-round, but
the resulting UTC interval — and therefore the number of one-minute `[start, end)`
slots that tile it — changes on US daylight-saving transition days:

| Day | Exchange-local window | UTC duration | 1-minute bars |
| --- | --- | --- | --- |
| normal | `[18:00, 17:00)` ET | 23h | `1380` |
| spring-forward (e.g. `2026-03-08`, clocks skip `02:00 -> 03:00` ET) | `[18:00, 17:00)` ET | 22h | `1320` |
| fall-back (e.g. `2026-11-01`, clocks repeat `01:00–02:00` ET) | `[18:00, 17:00)` ET | 24h | `1440` |

The count is derived from the DST-aware session interval
(`ComexGoldCalendarProvider.session_for(date).interval`), never from a fixed
23-hour window. Asserting `1380` (or `1440`/`1379`) unconditionally is incorrect
on transition days. Anchor: `tests/anchor/test_comex_dst_session_bars.py`.

## session_id assignment

Every `Bar` carries a `session_id` string equal to the **exchange-local close
date** for the session that contains the bar's start time. For overnight
futures the calendar date in `session_id` is **not** the same as the bar's
UTC calendar date — a GC 1m bar at `2026-01-05T22:30Z` (`ET 17:30` of
`2026-01-06` after DST) belongs to session_id `"2026-01-07"` because its
session opens at `ET 18:00` on `2026-01-06`.

The mapping is owned by `qts.data.sessions.RegularSessionWindow`. For
historical CSV sources it is derived from the chain's `trading_hours` +
`timezone_id` via `HistoricalChain.session_window()` and passed into
`iter_historical_bars`. Timestamps that fall inside a daily break
(e.g. `[ET 17:00, ET 18:00)` for GC) get `session_id = None` and are
**dropped before reaching downstream consumers** — neither the
strategy actor nor `BarTimeGridSynthesizer` ever sees a break-time row.

Forbidden: deriving session_id from `timestamp.astimezone(UTC).date()`;
labeling break-time bars with the surrounding session's id; bridging the
daily break with synthetic bars.

## Calendar-aware daily (`1d`) consolidation

`<1d` bars remain clock-aligned in exchange time; only `1d` consolidation is
session-aligned and must use the actual per-day session boundary. A fixed
`RegularSessionWindow` assumes every session shares the same open/close clock
times, which is wrong for:

- **holidays** — not a session; no `1d` bar may be produced for that date;
- **half-days / early closes** — the `1d` bar must close at the early close;
- **DST transition days** — the UTC interval shortens (spring-forward) or
  lengthens (fall-back) even though the exchange-local clock window is constant.

The session-interval dependency for `1d` consolidation is
`qts.data.sessions.SessionIntervalSource`
(`interval_for_session_id(session_id) -> TimeInterval | None`).
`RegularSessionWindow` satisfies it for fixed-window streams;
`qts.data.sessions.CalendarSessionIntervalSource` derives each day's interval
from a calendar provider — `ExchangeCalendarProvider.session_interval_for(date)`
for holiday/half-day awareness (returns `None` on a holiday) or
`ComexGoldCalendarProvider.session_interval_for(date)` for DST-aware COMEX
sessions. Anchor / gate: `tests/integration/test_daily_consolidation_special_sessions.py`.
