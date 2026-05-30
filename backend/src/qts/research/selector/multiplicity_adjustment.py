"""Multiple-testing / backtest-overfitting correction for research selection.

This module owns the statistical correction that protects autonomous research
candidate selection from selection bias: when ``N`` strategy configurations are
tried, the *maximum* observed Sharpe ratio inflates purely by chance. Ranking on
the raw Sharpe (or any raw composite) over-promotes lucky candidates. The
``ResearchMultiplicityAdjustment`` concept deflates the observed performance by
the number of trials and the realized higher moments, yielding an
``adjusted_score`` that selection and the promotion gates rank on instead.

Implemented quantities and their references:

* **Expected maximum Sharpe under N trials** — Bailey & Lopez de Prado (2014),
  "The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting
  and Non-Normality", *Journal of Portfolio Management* 40(5), eq. (5):

      E[max_N] ~= sigma_SR * [ (1 - gamma) * Z^-1(1 - 1/N)
                               + gamma * Z^-1(1 - 1/(N*e)) ]

  where ``gamma`` is the Euler-Mascheroni constant, ``Z^-1`` the inverse standard
  normal CDF, ``sigma_SR`` the cross-trial standard deviation of the trial Sharpe
  ratios, and ``e`` Euler's number. With ``N <= 1`` there is no multiplicity
  inflation and the expected maximum is ``0``.

* **Probabilistic Sharpe Ratio (PSR)** — Bailey & Lopez de Prado (2012), "The
  Sharpe Ratio Efficient Frontier", *Journal of Risk* 15(2):

      PSR(SR0) = Phi( (SR_hat - SR0) * sqrt(n - 1)
                      / sqrt(1 - skew*SR_hat + (kurt - 1)/4 * SR_hat^2) )

  ``SR_hat`` is the *non-annualized* (per-observation) observed Sharpe, ``n`` the
  number of return observations, ``skew``/``kurt`` the skewness and (non-excess)
  kurtosis of returns, and ``Phi`` the standard normal CDF.

* **Deflated Sharpe Ratio (DSR)** — Bailey & Lopez de Prado (2014): the PSR
  evaluated against the data-driven benchmark ``SR0 = E[max_N]``. DSR is the
  probability that the true Sharpe exceeds what would be expected as the best of
  ``N`` independent random trials; it decreases monotonically in ``N``.

* **Probability of Backtest Overfitting (PBO)** via Combinatorially-Symmetric
  Cross-Validation (CSCV) — Bailey, Borwein, Lopez de Prado & Zhu (2017), "The
  Probability of Backtest Overfitting", *Journal of Computational Finance* 20(4).
  The per-trial performance series is split into ``S`` disjoint blocks; over every
  ``C(S, S/2)`` train/test partition the in-sample best configuration's
  out-of-sample relative rank ``w`` in ``(0, 1)`` is mapped to the logit
  ``lambda = ln(w / (1 - w))``; ``PBO = P(lambda <= 0)``, the frequency with which
  the in-sample winner under-performs the median out of sample.

* **False Discovery Rate (FDR)** by family / generation — Benjamini & Hochberg
  (1995), "Controlling the False Discovery Rate", *JRSS B* 57(1). Given the
  per-candidate selection p-values within a family, the BH step-up procedure
  returns the discoveries that control the expected false-discovery proportion at
  level ``q``.

* **Trial-count-adjusted objective** — the raw selection objective penalized by
  the multiplicity haircut ``E[max_N] * sigma_SR``-scaled deflation. Concretely we
  subtract the expected-maximum Sharpe (in the same units as the objective's
  Sharpe term) so that adding trials lowers the score of every candidate.

The concept depends only on the Python standard library (``math``,
``statistics.NormalDist``, ``itertools``); no external numerics are required.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from itertools import combinations
from statistics import NormalDist
from typing import Any

# Euler-Mascheroni constant used in the expected-maximum-Sharpe approximation.
_EULER_MASCHERONI = 0.5772156649015329
_NORMAL = NormalDist()


def expected_maximum_sharpe(trial_count: int, trial_sharpe_std: float) -> float:
    """Return E[max_N], the expected maximum Sharpe over ``N`` random trials.

    Bailey & Lopez de Prado (2014), eq. (5). With ``trial_count <= 1`` or a
    non-positive cross-trial dispersion there is no multiple-testing inflation and
    the expected maximum is ``0.0``.
    """

    if trial_count <= 1 or trial_sharpe_std <= 0.0:
        return 0.0
    n = float(trial_count)
    first = _NORMAL.inv_cdf(1.0 - 1.0 / n)
    second = _NORMAL.inv_cdf(1.0 - 1.0 / (n * math.e))
    return trial_sharpe_std * ((1.0 - _EULER_MASCHERONI) * first + _EULER_MASCHERONI * second)


def probabilistic_sharpe_ratio(
    *,
    observed_sharpe: float,
    sample_size: int,
    skewness: float,
    kurtosis: float,
    benchmark_sharpe: float = 0.0,
) -> float:
    """Return PSR(benchmark) per Bailey & Lopez de Prado (2012).

    ``observed_sharpe`` is the non-annualized per-observation Sharpe, ``sample_size``
    the number of return observations, ``kurtosis`` the non-excess kurtosis
    (``3`` for a normal distribution). Returns ``0.0`` when the estimate is
    undefined (too few observations or a non-positive variance term).
    """

    if sample_size < 2:
        return 0.0
    variance_term = (
        1.0
        - skewness * observed_sharpe
        + (kurtosis - 1.0) / 4.0 * observed_sharpe * observed_sharpe
    )
    if variance_term <= 0.0:
        return 0.0
    sigma_sharpe = math.sqrt(variance_term / (sample_size - 1))
    if sigma_sharpe == 0.0:
        return 0.0
    z = (observed_sharpe - benchmark_sharpe) / sigma_sharpe
    return _NORMAL.cdf(z)


def deflated_sharpe_ratio(
    *,
    observed_sharpe: float,
    sample_size: int,
    skewness: float,
    kurtosis: float,
    trial_count: int,
    trial_sharpe_std: float,
) -> float:
    """Return the Deflated Sharpe Ratio (Bailey & Lopez de Prado 2014).

    DSR is PSR evaluated against the data-driven benchmark ``E[max_N]``. It
    decreases monotonically as ``trial_count`` grows, so more trials make the
    candidate harder to accept.
    """

    benchmark = expected_maximum_sharpe(trial_count, trial_sharpe_std)
    return probabilistic_sharpe_ratio(
        observed_sharpe=observed_sharpe,
        sample_size=sample_size,
        skewness=skewness,
        kurtosis=kurtosis,
        benchmark_sharpe=benchmark,
    )


def probability_of_backtest_overfitting(
    performance_matrix: Sequence[Sequence[float]],
    *,
    block_count: int = 8,
) -> float:
    """Return PBO via CSCV (Bailey, Borwein, Lopez de Prado & Zhu 2017).

    ``performance_matrix`` is ``rows x configs``: each row is one time slice and
    each column one trial configuration's performance in that slice (e.g. a Sharpe
    or return). The series is partitioned into ``block_count`` disjoint blocks; over
    every balanced train/test split the in-sample best configuration's
    out-of-sample logit rank is collected and ``PBO`` is the fraction with
    ``lambda <= 0``. Returns ``0.0`` when fewer than two configurations are
    supplied (no relative ranking is possible).
    """

    rows = [list(row) for row in performance_matrix]
    if not rows:
        return 0.0
    config_count = len(rows[0])
    if config_count < 2:
        return 0.0
    if any(len(row) != config_count for row in rows):
        raise ValueError("performance_matrix rows must all have the same width")
    if block_count < 2 or block_count % 2 != 0:
        raise ValueError("block_count must be an even integer >= 2")

    blocks = _even_blocks(rows, block_count)
    block_indices = range(len(blocks))
    logits: list[float] = []
    for train in combinations(block_indices, len(blocks) // 2):
        train_set = set(train)
        test = [index for index in block_indices if index not in train_set]
        in_sample = _block_means(blocks, train, config_count)
        out_sample = _block_means(blocks, test, config_count)
        best_config = max(range(config_count), key=lambda c: in_sample[c])
        relative_rank = _relative_rank(out_sample, best_config)
        logits.append(_logit(relative_rank))
    if not logits:
        return 0.0
    return sum(1 for value in logits if value <= 0.0) / len(logits)


def benjamini_hochberg_discoveries(
    p_values: Sequence[float],
    *,
    false_discovery_rate: float,
) -> tuple[int, ...]:
    """Return indices accepted by the BH step-up procedure (1995).

    Sorts the p-values ascending, finds the largest rank ``k`` with
    ``p_(k) <= (k / m) * q``, and returns the original indices of every candidate
    with a p-value at or below that threshold. An empty input returns ``()``.
    """

    if not 0.0 < false_discovery_rate <= 1.0:
        raise ValueError("false_discovery_rate must be in (0, 1]")
    total = len(p_values)
    if total == 0:
        return ()
    ordered = sorted(range(total), key=lambda index: p_values[index])
    threshold_rank = 0
    for rank, index in enumerate(ordered, start=1):
        if p_values[index] <= (rank / total) * false_discovery_rate:
            threshold_rank = rank
    if threshold_rank == 0:
        return ()
    accepted = ordered[:threshold_rank]
    return tuple(sorted(accepted))


def _even_blocks(
    rows: Sequence[Sequence[float]],
    block_count: int,
) -> tuple[tuple[Sequence[float], ...], ...]:
    """Split ``rows`` into ``block_count`` near-even contiguous blocks."""

    total = len(rows)
    if total < block_count:
        raise ValueError("performance_matrix needs at least block_count rows")
    base, remainder = divmod(total, block_count)
    blocks: list[tuple[Sequence[float], ...]] = []
    start = 0
    for block_index in range(block_count):
        size = base + (1 if block_index < remainder else 0)
        blocks.append(tuple(rows[start : start + size]))
        start += size
    return tuple(blocks)


def _block_means(
    blocks: Sequence[Sequence[Sequence[float]]],
    selected: Sequence[int],
    config_count: int,
) -> list[float]:
    """Return per-config mean performance across the selected blocks."""

    totals = [0.0] * config_count
    count = 0
    for block_index in selected:
        for row in blocks[block_index]:
            for config in range(config_count):
                totals[config] += float(row[config])
            count += 1
    if count == 0:
        return totals
    return [value / count for value in totals]


def _relative_rank(out_sample: Sequence[float], config: int) -> float:
    """Return the out-of-sample relative rank ``w`` in ``(0, 1)`` of ``config``.

    Rank ``1`` is the worst configuration; the rank is normalized by
    ``config_count + 1`` so ``w`` never reaches the ``0``/``1`` logit poles.
    """

    config_count = len(out_sample)
    order = sorted(range(config_count), key=lambda c: out_sample[c])
    rank = order.index(config) + 1
    return rank / (config_count + 1)


def _logit(value: float) -> float:
    return math.log(value / (1.0 - value))


@dataclass(frozen=True, slots=True)
class MultiplicityAdjustmentResult:
    """Per-candidate multiple-testing correction carrying raw and adjusted scores."""

    candidate_id: str
    raw_score: float
    adjusted_score: float
    observed_sharpe: float
    deflated_sharpe_ratio: float
    probabilistic_sharpe_ratio: float
    expected_maximum_sharpe: float
    probability_of_backtest_overfitting: float
    trial_count: int
    trial_sharpe_std: float
    sample_size: int
    skewness: float
    kurtosis: float
    fdr_significant: bool

    def __post_init__(self) -> None:
        if not self.candidate_id.strip():
            raise ValueError("candidate_id is required")
        if self.trial_count < 1:
            raise ValueError("trial_count must be positive")
        if self.sample_size < 0:
            raise ValueError("sample_size must be non-negative")

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready adjustment payload."""

        return {
            "adjusted_score": self.adjusted_score,
            "candidate_id": self.candidate_id,
            "deflated_sharpe_ratio": self.deflated_sharpe_ratio,
            "expected_maximum_sharpe": self.expected_maximum_sharpe,
            "fdr_significant": self.fdr_significant,
            "kurtosis": self.kurtosis,
            "observed_sharpe": self.observed_sharpe,
            "probabilistic_sharpe_ratio": self.probabilistic_sharpe_ratio,
            "probability_of_backtest_overfitting": self.probability_of_backtest_overfitting,
            "raw_score": self.raw_score,
            "sample_size": self.sample_size,
            "skewness": self.skewness,
            "trial_count": self.trial_count,
            "trial_sharpe_std": self.trial_sharpe_std,
        }


@dataclass(frozen=True, slots=True)
class CandidateStatistics:
    """Per-candidate statistical inputs the adjustment layer consumes.

    ``observed_sharpe`` is the non-annualized per-observation Sharpe, ``sample_size``
    the number of return observations behind it, and ``raw_score`` the selector's
    raw objective for the candidate. ``oos_returns`` (one return per time slice) is
    used to build the CSCV performance matrix; when omitted, PBO is reported as
    ``0.0`` for that candidate.
    """

    candidate_id: str
    raw_score: float
    observed_sharpe: float
    sample_size: int
    skewness: float = 0.0
    kurtosis: float = 3.0
    oos_returns: tuple[float, ...] = ()

    def __post_init__(self) -> None:
        if not self.candidate_id.strip():
            raise ValueError("candidate_id is required")
        if self.sample_size < 0:
            raise ValueError("sample_size must be non-negative")
        object.__setattr__(self, "oos_returns", tuple(float(value) for value in self.oos_returns))


@dataclass(frozen=True, slots=True)
class ResearchMultiplicityAdjustment:
    """Owns the family-level multiple-testing correction for a candidate set.

    Constructed with the family's trial count (the number of configurations tried,
    threaded from the search budget) and the correction policy. ``adjust`` consumes
    the per-candidate statistics and returns one ``MultiplicityAdjustmentResult``
    per candidate, deflating every raw score by the same trial-count haircut so that
    increasing ``trial_count`` lowers every adjusted score and raises the effective
    acceptance threshold.
    """

    trial_count: int
    false_discovery_rate: float = 0.10
    pbo_block_count: int = 8
    sharpe_penalty_weight: float = 1.0
    objective_sharpe_key: str = "oos_sharpe"
    composite_weights: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.trial_count < 1:
            raise ValueError("trial_count must be positive")
        if not 0.0 < self.false_discovery_rate <= 1.0:
            raise ValueError("false_discovery_rate must be in (0, 1]")
        if self.pbo_block_count < 2 or self.pbo_block_count % 2 != 0:
            raise ValueError("pbo_block_count must be an even integer >= 2")
        if self.sharpe_penalty_weight < 0.0:
            raise ValueError("sharpe_penalty_weight must be non-negative")

    def adjust(
        self,
        candidates: Sequence[CandidateStatistics],
    ) -> tuple[MultiplicityAdjustmentResult, ...]:
        """Return one adjustment result per candidate in input order."""

        if not candidates:
            return ()
        trial_sharpe_std = self._trial_sharpe_std(candidates)
        expected_max = expected_maximum_sharpe(self.trial_count, trial_sharpe_std)
        haircut = self.sharpe_penalty_weight * self._objective_sharpe_weight() * expected_max
        pbo_by_candidate = self._pbo_by_candidate(candidates)
        p_values = [self._selection_p_value(candidate) for candidate in candidates]
        significant = set(
            benjamini_hochberg_discoveries(p_values, false_discovery_rate=self.false_discovery_rate)
        )
        results: list[MultiplicityAdjustmentResult] = []
        for index, candidate in enumerate(candidates):
            psr = probabilistic_sharpe_ratio(
                observed_sharpe=candidate.observed_sharpe,
                sample_size=candidate.sample_size,
                skewness=candidate.skewness,
                kurtosis=candidate.kurtosis,
            )
            dsr = deflated_sharpe_ratio(
                observed_sharpe=candidate.observed_sharpe,
                sample_size=candidate.sample_size,
                skewness=candidate.skewness,
                kurtosis=candidate.kurtosis,
                trial_count=self.trial_count,
                trial_sharpe_std=trial_sharpe_std,
            )
            results.append(
                MultiplicityAdjustmentResult(
                    candidate_id=candidate.candidate_id,
                    raw_score=candidate.raw_score,
                    adjusted_score=candidate.raw_score - haircut,
                    observed_sharpe=candidate.observed_sharpe,
                    deflated_sharpe_ratio=dsr,
                    probabilistic_sharpe_ratio=psr,
                    expected_maximum_sharpe=expected_max,
                    probability_of_backtest_overfitting=pbo_by_candidate[candidate.candidate_id],
                    trial_count=self.trial_count,
                    trial_sharpe_std=trial_sharpe_std,
                    sample_size=candidate.sample_size,
                    skewness=candidate.skewness,
                    kurtosis=candidate.kurtosis,
                    fdr_significant=index in significant,
                )
            )
        return tuple(results)

    def _objective_sharpe_weight(self) -> float:
        weight = self.composite_weights.get(self.objective_sharpe_key)
        if weight is None:
            return 1.0
        return float(weight)

    @staticmethod
    def _trial_sharpe_std(candidates: Sequence[CandidateStatistics]) -> float:
        sharpes = [candidate.observed_sharpe for candidate in candidates]
        if len(sharpes) < 2:
            return 0.0
        mean = sum(sharpes) / len(sharpes)
        variance = sum((value - mean) ** 2 for value in sharpes) / (len(sharpes) - 1)
        return math.sqrt(variance) if variance > 0.0 else 0.0

    def _pbo_by_candidate(
        self,
        candidates: Sequence[CandidateStatistics],
    ) -> dict[str, float]:
        with_returns = [c for c in candidates if c.oos_returns]
        if len(with_returns) < 2:
            return {candidate.candidate_id: 0.0 for candidate in candidates}
        row_count = min(len(c.oos_returns) for c in with_returns)
        if row_count < self.pbo_block_count:
            return {candidate.candidate_id: 0.0 for candidate in candidates}
        matrix = [
            [candidate.oos_returns[row] for candidate in with_returns] for row in range(row_count)
        ]
        family_pbo = probability_of_backtest_overfitting(matrix, block_count=self.pbo_block_count)
        return {candidate.candidate_id: family_pbo for candidate in candidates}

    @staticmethod
    def _selection_p_value(candidate: CandidateStatistics) -> float:
        """Return the one-sided p-value that the true Sharpe is <= 0.

        Uses the normal approximation ``SR_hat * sqrt(sample_size)`` as the test
        statistic; ``p = 1 - Phi(z)``. With no observations the candidate cannot be
        distinguished from noise, so ``p = 1.0``.
        """

        if candidate.sample_size < 1:
            return 1.0
        z = candidate.observed_sharpe * math.sqrt(candidate.sample_size)
        return 1.0 - _NORMAL.cdf(z)


__all__ = [
    "CandidateStatistics",
    "MultiplicityAdjustmentResult",
    "ResearchMultiplicityAdjustment",
    "benjamini_hochberg_discoveries",
    "deflated_sharpe_ratio",
    "expected_maximum_sharpe",
    "probabilistic_sharpe_ratio",
    "probability_of_backtest_overfitting",
]
