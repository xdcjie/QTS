# VWAP Artifact Taxonomy

This document classifies every VWAP-related artifact in the repository into
allowed and forbidden categories, per `docs/architecture/system_flows.md`
FLOW-RESEARCH and FLOW-OPTIMIZER forbidden-shortcut rules.

## Categories

### A. Production strategy — allowed

Registered, promoted VWAP strategies that have passed `FLOW-PROMOTION` and are
deployable in paper or live mode.

| File | Description |
| --- | --- |
| `strategies/production/vwap_production_pullback.py` | Production VWAP pullback (GC + SI variants) |
| `configs/strategies/vwap_production_pullback_gc.yaml` | GC production strategy config |
| `configs/strategies/vwap_production_pullback_si.yaml` | SI production strategy config |
| `configs/backtest.vwap_production_pullback_gc.yaml` | GC backtest config for production variant |
| `configs/backtest.vwap_production_pullback_si.yaml` | SI backtest config for production variant |
| `configs/paper.vwap_production_pullback_gc.example.yaml` | GC paper example config |
| `configs/paper.vwap_production_pullback_si.example.yaml` | SI paper example config |
| `strategies/vwap_pullback/card.md` | Strategy lifecycle card for `vwap_pullback` (status, hypothesis, promotion gate) |
| `docs/runbooks/vwap_pullback_live_runbook.md` | Live runbook for vwap_pullback |

### B. Research strategy — allowed (under Research OS workflow)

Research strategies that enter through `scripts/run_research.py` with a
canonical `configs/research/` session config and a reviewed workflow YAML
under `configs/research/workflows/`.

| File | Description |
| --- | --- |
| `strategies/research/vwap_factor_research.py` | VWAP factor research strategy |
| `configs/strategies/vwap_factor_research.yaml` | Research strategy config |
| `configs/research/vwap.yaml` | Canonical VWAP research session config |
| `configs/backtest.vwap_factor_research.yaml` | VWAP factor research backtest config |
| `configs/backtest.vwap_factor_research_gc_15m_long_is.yaml` | GC 15m IS backtest variant |
| `configs/backtest.vwap_factor_research_gc_5m_long_is.yaml` | GC 5m IS backtest variant |
| `configs/backtest.vwap_factor_research_gc_long_is.yaml` | GC IS backtest variant |
| `configs/backtest.vwap_factor_research_si_15m_long_is.yaml` | SI 15m IS backtest variant |
| `configs/backtest.vwap_factor_research_si_5m_long_is.yaml` | SI 5m IS backtest variant |
| `configs/backtest.vwap_factor_research_si_long_is.yaml` | SI IS backtest variant |

### C. Campaign / search templates — allowed (canonical)

Research campaign, manifest template, and search-space configs that belong to
the Research OS workflow structure under `configs/research/`.

| File | Description |
| --- | --- |
| `configs/research/campaigns/gc_si_vwap_trend_alpha_research_v1.yaml` | Alpha research campaign |
| `configs/research/campaigns/gc_si_vwap_trend_clean_scan_v1.yaml` | Clean scan campaign |
| `configs/research/campaigns/gc_si_vwap_trend_holdout_v1.yaml` | Holdout campaign |
| `configs/research/campaigns/gc_si_vwap_trend_late_holdout_v1.yaml` | Late holdout campaign |
| `configs/research/campaigns/gc_si_vwap_trend_post_dst_holdout_v1.yaml` | Post-DST holdout campaign |
| `configs/research/campaigns/gc_vwap_trend_position_size_scan_v1.yaml` | Position size scan campaign |
| `configs/research/campaigns/gc_vwap_trend_robust_scan_v1.yaml` | Robust scan campaign |
| `configs/research/manifests/templates/gc_si_vwap_trend.yaml` | Manifest template |
| `configs/research/manifests/templates/gc_si_vwap_trend_position_sized.yaml` | Position-sized manifest template |
| `configs/research/search/gc_si_vwap_trend_alpha_space.yaml` | Alpha search space |
| `configs/research/search/gc_si_vwap_trend_clean_scan_winner_space.yaml` | Clean scan winner space |
| `configs/research/search/gc_si_vwap_trend_selected_holdout_space.yaml` | Selected holdout space |
| `configs/research/search/gc_vwap_trend_position_size_space.yaml` | Position size search space |
| `configs/research/search/gc_vwap_trend_robust_space.yaml` | Robust search space |

### D. Ad-hoc runner / config — FORBIDDEN

VWAP-specific ad-hoc runners and optimizer configs that bypass the Research OS
workflow. These must not exist or be reintroduced. Guardrail code:
`VWAP_ADHOC_RUNNER_FORBIDDEN`.

| Pattern | Rule |
| --- | --- |
| `scripts/research/run_vwap_*.py` | Ad-hoc VWAP runner — must not exist |
| `configs/optimizer/*vwap*` (yaml/yml) | VWAP optimizer config bypassing workflow gates — must not exist |

Also covered by broader guardrails:
- `RESEARCH_RUN_SCRIPT` rejects all `scripts/research/run_*_research.py` and
  `scripts/research/run_vwap_*.py`.
- `VWAP_OPTIMIZER_CONFIG` rejects `configs/optimizer/*vwap*` yaml/yml files.

The `VWAP_ADHOC_RUNNER_FORBIDDEN` rule provides a unified VWAP-specific guard
that checks both patterns together, making the forbidden boundary explicit.

### E. Example / demo artifacts — allowed but documented

Example and demo strategies that live under `examples/` and are not promoted
for paper/live use. Production strategies must not import these (enforced by
`PRODUCTION_STRATEGY_IMPORT` guardrail).

| File | Description |
| --- | --- |
| `examples/strategies/vwap_pullback_v2.py` | Example VWAP pullback v2 strategy |
| `configs/strategies/vwap_pullback.yaml` | Example strategy config (references example class) |
| `configs/backtest.vwap.example.yaml` | Example/demo backtest config |

### F. Tests — allowed

Unit, anchor, and integration tests for VWAP strategies. These are not VWAP
business artifacts; they verify strategy correctness.

| File | Description |
| --- | --- |
| `tests/anchor/test_vwap_pullback_v2_state_machine.py` | Anchor test for example v2 state machine |
| `tests/unit/strategies/test_vwap_factor_research.py` | Unit test for research strategy |
| `tests/unit/strategies/test_vwap_pullback.py` | Unit test for pullback strategy |
| `tests/unit/strategies/test_vwap_regime_pullback.py` | Unit test for regime pullback |
| `tests/unit/architecture/test_vwap_taxonomy.py` | Gate test for the VWAP taxonomy-presence guardrail itself |

## Guardrail enforcement

| Guardrail code | Pattern | What it catches |
| --- | --- | --- |
| `RESEARCH_RUN_SCRIPT` | `scripts/research/run_*_research.py`, `scripts/research/run_vwap_*.py` | All ad-hoc research runner scripts |
| `VWAP_OPTIMIZER_CONFIG` | `configs/optimizer/*vwap*.{yaml,yml}` | VWAP optimizer configs outside workflow gates |
| `VWAP_ADHOC_RUNNER_FORBIDDEN` | `scripts/research/run_vwap_*.py`, `configs/optimizer/*vwap*.{yaml,yml}` | Unified VWAP-specific ad-hoc artifact check |
| `VWAP_TAXONOMY_PRESENCE` | Every tracked file whose path contains `vwap` (this doc excepted) | Undocumented VWAP artifact missing a taxonomy entry |
| `PRODUCTION_STRATEGY_IMPORT` | Production code importing `examples.*` or `strategies.research.*` | Production importing non-promoted VWAP strategies |

## Canonical entrypoint for VWAP research

All VWAP research must enter through:

```bash
PYTHONPATH=backend/src uv run python scripts/run_research.py \
  --config configs/research/vwap.yaml \
  workflow configs/research/workflows/<workflow-config>
```

VWAP optimizer work must use a reviewed workflow YAML under
`configs/research/workflows/`, not a VWAP-specific optimizer YAML under
`configs/optimizer/`.