# Indicators Rules

This module contains internal indicator implementations.

Rules:

- Indicators should support warmup, ready state, incremental updates, and snapshot/restore.
- User-facing access should be exposed through Strategy SDK, not raw internal implementations.
- Keep indicator computations deterministic.
