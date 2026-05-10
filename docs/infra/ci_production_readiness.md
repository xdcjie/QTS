# Production Readiness CI Plan

CI must run:

- `make format`
- `make lint`
- `make typecheck`
- `make test-unit`
- `make test-integration`
- `make test-anchor`
- `make test-replay`
- `make test-reconciliation`

Slow soak checks remain separate from normal CI and run through `make test-soak` plus the manual paper/observation soak gate.
