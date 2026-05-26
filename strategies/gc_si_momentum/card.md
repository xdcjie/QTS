---
id: gc_si_momentum
owner: research
status: candidate
hypothesis: Gold and silver short-horizon momentum can be compared through a shared backtest evidence path.
entrypoint: examples.strategies.gc_si_momentum:GcSiMomentumStrategy
default_config: configs/strategies/gc_si_momentum.yaml
failure_conditions:
  - Default promotion gates reject the run because OOS metrics are missing.
  - Dataset snapshot or split evidence is incomplete.
  - No-lookahead or deterministic replay evidence is absent.
---

# GC/SI Momentum

Research candidate used by the manifest-driven smoke run. It is lifecycle
managed as research evidence only and requires explicit promotion gates before
paper or live use.
