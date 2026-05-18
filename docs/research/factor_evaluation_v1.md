# Factor Evaluation Artifacts V1

## Scope

`qts.research.factor_evaluation` evaluates already-computed cross-sectional
`FactorResult` snapshots against aligned historical forward returns. It owns
research metrics and deterministic JSON artifacts only.

It does not compute factors, run backtests, create orders, emit target intents,
or import runtime, execution, broker, risk, account, or Strategy SDK internals.
Factor computation remains owned by `qts.factors`.

## Input

`FactorEvaluationInput` contains:

- `as_of`: the factor snapshot date.
- `factor_name` and `factor_version`: the evaluated factor identity.
- `factor_result`: ranked factor scores from `qts.factors`.
- `forward_returns`: historical forward returns keyed by scored asset symbol.
- `bucket_count`: the cross-sectional bucket count used for turnover.
- `previous_factor_result`: optional prior ranked snapshot for turnover.

Forward returns are evaluation labels. They must not be used to compute factor
scores.

## Metrics

Rank IC is Spearman rank correlation between factor score ranks and forward
return ranks for scored assets that have forward returns. Ties use average
ranks. At least two scored assets with forward returns are required.

Long-short spread V1 is the top-ranked available forward return minus the
bottom-ranked available forward return after excluding assets with missing
forward returns.

Coverage is:

```text
scored assets with forward returns / scored assets
```

Missing forward returns are excluded from rank IC and spread calculations. They
are recorded in `missing_symbols`, while `scored_count` records the full ranked
cross-section and `return_count` records the number of scored assets with
forward returns.

Turnover is the current top-bucket membership change versus the previous
snapshot:

```text
1 - retained current top-bucket symbols / current top-bucket symbols
```

The top bucket size is `ceil(scored_count / bucket_count)` with a minimum of
one asset. The first snapshot has `turnover = null` because there is no prior
bucket to compare.

## Artifacts

`FactorEvaluationArtifactWriter` writes deterministic JSON with:

- `sort_keys=True`;
- two-space indentation;
- trailing newline;
- `Decimal` values serialized as strings;
- missing symbols serialized as a JSON list.

The resulting artifact path can be passed to `ExperimentManifestWriter` through
`ExperimentManifestConfig.artifact_paths`, where manifest hashing remains owned
by `qts.research.experiment_manifest`.
