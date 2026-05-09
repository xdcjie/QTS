# Domain Rules

This module contains pure trading domain models and invariants.

Rules:

- No API, database, broker, network, thread, or actor runtime dependencies.
- Use immutable value objects for IDs, instruments, events, orders, fills, and positions where practical.
- Use `InstrumentId` internally; never use broker symbols as domain identifiers.
- Domain correctness comes before implementation convenience.
- Financial invariants must be covered by anchor tests when relevant.
- Do not add framework dependencies here.
