# Workers Rules

This module contains process entrypoints and runtime composition.

Rules:

- Keep business logic out of workers.
- Workers should wire configuration, dependencies, and runtime lifecycle.
- Do not duplicate application service logic here.
