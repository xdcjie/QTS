# Research Strategy Boundaries

Research strategies are strategy-lab artifacts. They can generate evidence, but
they are not paper/live/production strategies and they must not become runtime
configuration by file movement alone.

## Boundaries

- `strategies/research/` contains research-only candidates, broad parameter
  surfaces, diagnostics harnesses, and experiment code.
- `strategies/production/` contains reviewed strategy implementations with a
  stable public configuration surface.
- `examples/strategies/` contains examples and demos. Example code cannot be a
  promotion candidate unless it is migrated to a reviewed strategy boundary.
- Production strategies must not import from `strategies.research` or
  `examples.strategies`.

Research evidence is not paper/live/production approval. Research evidence !=
paper/live/production behavior.

## Migration Path

A research strategy may move toward production only through an explicit review
packet:

1. Record the idea, hypothesis, source, edge type, kill criteria, and trial
   budget.
2. Run research through the canonical `FLOW-RESEARCH` entrypoint and produce
   deterministic manifests, reports, diagnostics, and evidence bundle records.
3. Create a `PromotionPacketV2` that cites `evidence_bundle_id`,
   `source_module`, `target_module`, structured metrics/data-quality/
   reproducibility evidence, and paper-readiness review records.
4. Move only the reviewed implementation boundary into `strategies/production/`.
   Do not reuse a research module as production code by importing it directly.
5. Run `FLOW-PROMOTION` human review for the exact build, config hash, account,
   risk profile, capital limit, and runtime mode.

Optimizer ranking, backtest PnL, report text, and evidence bundles can support
review, but none of them enable paper/live behavior without a promotion decision.
