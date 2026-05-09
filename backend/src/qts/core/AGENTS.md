# Core Rules

This module contains foundational value objects and utilities only.

Rules:

- Keep this module tiny and stable.
- No dependency on domain, runtime, API, broker, database, or frontend modules.
- Put IDs, money, time interval helpers, base enums, and base errors here.
- Do not turn `core` into a dumping ground.
