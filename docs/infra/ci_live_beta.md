# Live Beta CI Baseline

Required checks:

```bash
make format
make lint
make typecheck
make test-unit
make test-integration
make test-anchor
```

Milestone readiness uses:

```bash
make check
```

No live broker credentials are required or allowed in CI. Live-beta adapters in CI must use fake
broker/feed contracts.
