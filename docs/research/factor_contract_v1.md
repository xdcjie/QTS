# Factor Research Contract v1

## Scope

`qts.factors` is the research-only boundary for cross-sectional factor computation.
Factor code must not import runtime, execution, broker, reconciliation, account actor, or risk
engine modules. Strategy-facing access can wrap factors, but the factor contract is owned here.

## Protocol

```python
class Factor(Protocol):
    name: str
    version: str

    def compute(self, window: FactorWindow) -> FactorResult: ...
```

`name` is the stable factor family name. `version` is the semantic contract version for a factor
implementation. A change that alters input interpretation, missing-data behavior, ranking, or score
meaning requires a new version.

## FactorWindow

`FactorWindow` is a deterministic, time-sliced input:

- `prices`: mapping from asset to ordered price observations.
- `lookback`: trailing observation count available to the factor.
- `universe`: optional tuple limiting which assets are scored.
- `missing_data`: either `raise` or `drop`.

Factors must use only the trailing lookback observations. For intraday and session-aware data, the
producer of the window owns calendar alignment; the factor sees an already-aligned `[start, end)`
research slice and must not look outside it.

When `universe` is omitted, assets are processed in symbol order for deterministic tie handling.
When `universe` is provided, only those assets are considered. An asset missing from `prices`, an
asset with too few observations, or a `None` observation is explicit missing data.

## Missing Data

`missing_data="raise"` raises `ValueError` with the affected asset symbol. This is the default and is
preferred for tests and research runs that require complete inputs.

`missing_data="drop"` excludes assets with missing or insufficient data from the result. Dropping is
asset-local; other assets in the same window are still scored.

## FactorResult

`FactorResult.ranked` is a tuple of `FactorScore` values sorted by descending score. Ties are broken
by ascending asset symbol. Higher scores rank first. `FactorResult.score(asset)` returns the score for
an included asset and raises `KeyError` when the asset was not scored.

## MomentumFactor v1

`MomentumFactor(window=N)` has:

- `name = "momentum"`
- `version = "1"`
- `lookback = N`
- score: `last_price / first_price - 1` over the trailing `N` observations

The first price in the lookback window must be non-zero. Missing prices follow the window policy.

## Required Gates

Every factor must have tests covering:

- `name` and `version`
- deterministic output
- explicit missing-data behavior
- universe filtering behavior
- output ranking convention
- lookback window definition
- no runtime, execution, broker, reconciliation, account actor, or risk engine imports
