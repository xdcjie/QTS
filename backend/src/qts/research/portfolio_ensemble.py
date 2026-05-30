"""Research-only portfolio ensemble evaluation from completed equity curves."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime
from decimal import Decimal
from itertools import pairwise, product
from pathlib import Path
from typing import Any

import numpy as np


def evaluate_portfolio_ensemble(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluate completed backtest equity curves as a research-only allocation."""

    allocation_name = _required_text(payload, "allocation_name")
    legs = _legs_from_payload(payload.get("legs"))
    loaded_legs = tuple(_loaded_leg(leg) for leg in legs)
    equity_curve = _combined_equity_curve(loaded_legs)
    reporting_grid = _reporting_grid(payload)
    metric_curve = _metric_curve(equity_curve, reporting_grid)
    total_weight = sum((leg["weight"] for leg in loaded_legs), Decimal("0"))
    leg_weights = {leg["name"]: leg["weight"] / total_weight for leg in loaded_legs}
    metrics = _metrics(metric_curve)
    return {
        "allocation_name": allocation_name,
        "end": equity_curve[-1][0].isoformat(),
        "equity_curve": [
            {"equity": str(equity), "time": timestamp.isoformat()}
            for timestamp, equity in equity_curve
        ],
        "leg_count": len(leg_weights),
        "leg_weights": {name: str(weight) for name, weight in sorted(leg_weights.items())},
        "full_curve_metrics": {
            "max_drawdown": str(_max_drawdown(equity_curve)),
            "total_return": str((equity_curve[-1][1] / equity_curve[0][1]) - Decimal("1")),
        },
        "metric_point_count": len(metric_curve),
        "metrics": {key: str(value) for key, value in sorted(metrics.items())},
        "not_tradable_config": True,
        "point_count": len(equity_curve),
        "reporting_grid": reporting_grid,
        "research_only": True,
        "source_manifest_paths": [str(leg["manifest_path"]) for leg in loaded_legs],
        "start": equity_curve[0][0].isoformat(),
    }


def scan_portfolio_ensemble_allocations(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Scan a discrete static-weight grid over completed equity curves."""

    scan_name = _required_text(payload, "scan_name")
    periods = _string_tuple(payload.get("periods"), field_name="portfolio_ensemble_scan.periods")
    candidates = _scan_candidates(payload.get("candidates"), periods=periods)
    reporting_grid = _reporting_grid(payload)
    weight_step = Decimal(str(payload.get("weight_step", "0.25")))
    if weight_step <= Decimal("0") or weight_step > Decimal("1"):
        raise ValueError("portfolio_ensemble_scan.weight_step must be in (0, 1]")
    top_n = int(payload.get("top_n", 10))
    if top_n <= 0:
        raise ValueError("portfolio_ensemble_scan.top_n must be positive")
    max_active_legs = int(payload.get("max_active_legs", len(candidates)))
    if max_active_legs <= 0:
        raise ValueError("portfolio_ensemble_scan.max_active_legs must be positive")
    baseline_period = str(payload.get("baseline_period", periods[0]))
    post_periods = _string_tuple(
        payload.get("post_periods", periods[1:]),
        field_name="portfolio_ensemble_scan.post_periods",
    )
    score_periods = _string_tuple(
        payload.get("score_periods", periods),
        field_name="portfolio_ensemble_scan.score_periods",
    )
    _validate_period_subset((baseline_period,), periods, field_name="baseline_period")
    _validate_period_subset(post_periods, periods, field_name="post_periods")
    _validate_period_subset(score_periods, periods, field_name="score_periods")
    period_roles = _period_roles(payload.get("period_roles"))
    report_only_periods = _report_only_periods(periods, period_roles=period_roles)
    _reject_report_only_score_periods(
        (baseline_period,),
        period_roles=period_roles,
        field_name="baseline_period",
    )
    _reject_report_only_score_periods(
        post_periods,
        period_roles=period_roles,
        field_name="post_periods",
    )
    _reject_report_only_score_periods(
        score_periods,
        period_roles=period_roles,
        field_name="score_periods",
    )
    constraints = _scan_constraints(payload.get("constraints"))
    loaded = _scan_loaded_periods(candidates, periods)
    period_matrices = _scan_period_matrices(candidates, loaded, periods, reporting_grid)
    allocations = []
    for weights in _weight_vectors(len(candidates), weight_step, max_active_legs):
        allocation = _scan_allocation(
            candidates,
            period_matrices,
            periods,
            weights,
            baseline_period=baseline_period,
            post_periods=post_periods,
            score_periods=score_periods,
            constraints=constraints,
        )
        allocations.append(allocation)
    allocations.sort(
        key=lambda item: (item["meets_constraints"], item["score"]),
        reverse=True,
    )
    return {
        "allocation_overfit_warning": _ALLOCATION_OVERFIT_WARNING,
        "candidate_count": len(candidates),
        "constraints": {key: str(value) for key, value in sorted(constraints.items())},
        "evaluated_allocation_count": len(allocations),
        "not_tradable_config": True,
        "periods": list(periods),
        "post_periods": list(post_periods),
        "report_only_periods": list(report_only_periods),
        "reporting_grid": reporting_grid,
        "research_only": True,
        "score_periods": list(score_periods),
        "satisfying_allocation_count": sum(
            1 for allocation in allocations if allocation["meets_constraints"]
        ),
        "scan_name": scan_name,
        "top_allocations": [_json_decimal_ready(item) for item in allocations[:top_n]],
        "weight_step": str(weight_step),
    }


def scan_volatility_managed_allocations(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Scan no-lookahead volatility-managed allocations over completed equity curves."""

    scan_name = _required_text(payload, "scan_name")
    periods = _string_tuple(
        payload.get("periods"),
        field_name="portfolio_volatility_managed_scan.periods",
    )
    candidates = _scan_candidates(payload.get("candidates"), periods=periods)
    reporting_grid = _reporting_grid(payload)
    selection_periods = _string_tuple(
        payload.get("selection_periods", periods),
        field_name="portfolio_volatility_managed_scan.selection_periods",
    )
    _validate_period_subset(selection_periods, periods, field_name="selection_periods")
    baseline_period = str(payload.get("baseline_period", selection_periods[0]))
    _validate_period_subset((baseline_period,), periods, field_name="baseline_period")
    post_selection_periods = _string_tuple(
        payload.get("post_selection_periods", selection_periods[1:]),
        field_name="portfolio_volatility_managed_scan.post_selection_periods",
    )
    _validate_period_subset(
        post_selection_periods,
        selection_periods,
        field_name="post_selection_periods",
    )
    period_roles = _period_roles(payload.get("period_roles"))
    report_only_periods = _report_only_periods(periods, period_roles=period_roles)
    _reject_report_only_score_periods(
        (baseline_period,),
        period_roles=period_roles,
        field_name="baseline_period",
    )
    _reject_report_only_score_periods(
        selection_periods,
        period_roles=period_roles,
        field_name="selection_periods",
    )
    _reject_report_only_score_periods(
        post_selection_periods,
        period_roles=period_roles,
        field_name="post_selection_periods",
    )
    constraints = _volatility_managed_constraints(payload.get("constraints"))
    parameter_sets = _volatility_managed_parameter_sets(payload.get("parameter_grid"))
    loaded = _scan_loaded_periods(candidates, periods)
    period_matrices = _scan_period_matrices(candidates, loaded, periods, reporting_grid)
    allocations = []
    for parameters in parameter_sets:
        allocations.append(
            _volatility_managed_allocation(
                period_matrices,
                periods,
                parameters,
                baseline_period=baseline_period,
                selection_periods=selection_periods,
                post_selection_periods=post_selection_periods,
                constraints=constraints,
            )
        )
    allocations.sort(
        key=lambda item: (item["meets_constraints"], item["score"]),
        reverse=True,
    )
    return {
        "allocation_overfit_warning": _ALLOCATION_OVERFIT_WARNING,
        "candidate_count": len(candidates),
        "constraints": {key: str(value) for key, value in sorted(constraints.items())},
        "evaluated_parameter_count": len(parameter_sets),
        "not_tradable_config": True,
        "periods": list(periods),
        "post_selection_periods": list(post_selection_periods),
        "report_only_periods": list(report_only_periods),
        "reporting_grid": reporting_grid,
        "research_only": True,
        "satisfying_allocation_count": sum(
            1 for allocation in allocations if allocation["meets_constraints"]
        ),
        "scan_name": scan_name,
        "selection_periods": list(selection_periods),
        "top_allocations": [_json_decimal_ready(item) for item in allocations[:10]],
        "uses_prior_returns_only": True,
    }


def _legs_from_payload(value: Any) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, list | tuple) or not value:
        raise ValueError("portfolio_ensemble.legs must be a non-empty list")
    legs: list[dict[str, Any]] = []
    names: set[str] = set()
    for index, raw_leg in enumerate(value):
        if not isinstance(raw_leg, Mapping):
            raise ValueError(f"portfolio_ensemble.legs[{index}] must be a mapping")
        name = _required_text(raw_leg, "name")
        if name in names:
            raise ValueError("portfolio ensemble leg names must be unique")
        names.add(name)
        weight = Decimal(str(raw_leg.get("weight", "1")))
        if weight <= Decimal("0"):
            raise ValueError("portfolio ensemble leg weight must be positive")
        legs.append(
            {
                "manifest_path": Path(_required_text(raw_leg, "manifest_path")),
                "name": name,
                "weight": weight,
            }
        )
    return tuple(legs)


def _scan_candidates(value: Any, *, periods: tuple[str, ...]) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, list | tuple) or not value:
        raise ValueError("portfolio_ensemble_scan.candidates must be a non-empty list")
    candidates: list[dict[str, Any]] = []
    names: set[str] = set()
    for index, raw_candidate in enumerate(value):
        if not isinstance(raw_candidate, Mapping):
            raise ValueError(f"portfolio_ensemble_scan.candidates[{index}] must be a mapping")
        name = _required_text(raw_candidate, "name")
        if name in names:
            raise ValueError("portfolio ensemble scan candidate names must be unique")
        names.add(name)
        raw_manifests = raw_candidate.get("period_manifests")
        if not isinstance(raw_manifests, Mapping):
            raise ValueError("portfolio_ensemble_scan.candidate.period_manifests is required")
        period_manifests = {}
        for period in periods:
            raw_path = raw_manifests.get(period)
            if not isinstance(raw_path, str) or not raw_path.strip():
                raise ValueError(f"candidate {name} missing manifest for period {period}")
            period_manifests[period] = Path(raw_path)
        candidates.append({"name": name, "period_manifests": period_manifests})
    return tuple(candidates)


def _scan_constraints(value: Any) -> dict[str, Decimal]:
    raw_constraints = value if isinstance(value, Mapping) else {}
    return {
        "max_full_drawdown": Decimal(str(raw_constraints.get("max_full_drawdown", "1"))),
        "min_baseline_annual_return": Decimal(
            str(raw_constraints.get("min_baseline_annual_return", "-1"))
        ),
        "min_post_annual_return": Decimal(str(raw_constraints.get("min_post_annual_return", "-1"))),
    }


def _volatility_managed_constraints(value: Any) -> dict[str, Decimal]:
    raw_constraints = value if isinstance(value, Mapping) else {}
    return {
        "max_selection_drawdown": Decimal(str(raw_constraints.get("max_selection_drawdown", "1"))),
        "min_baseline_annual_return": Decimal(
            str(raw_constraints.get("min_baseline_annual_return", "-1"))
        ),
        "min_selection_post_annual_return": Decimal(
            str(raw_constraints.get("min_selection_post_annual_return", "-1"))
        ),
    }


def _period_roles(value: Any) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError("period_roles must be a mapping")
    roles = {str(period): str(role) for period, role in value.items()}
    unsupported = sorted(set(roles.values()) - _PERIOD_ROLES)
    if unsupported:
        raise ValueError(f"unsupported period roles: {unsupported}")
    return roles


def _reject_report_only_score_periods(
    periods: tuple[str, ...],
    *,
    period_roles: Mapping[str, str],
    field_name: str,
) -> None:
    for period in periods:
        role = period_roles.get(period)
        if role in _REPORT_ONLY_PERIOD_ROLES:
            raise ValueError(f"{role} report-only period {period} cannot be used in {field_name}")


def _report_only_periods(
    periods: tuple[str, ...],
    *,
    period_roles: Mapping[str, str],
) -> tuple[str, ...]:
    return tuple(
        period for period in periods if period_roles.get(period) in _REPORT_ONLY_PERIOD_ROLES
    )


def _volatility_managed_parameter_sets(value: Any) -> tuple[dict[str, Any], ...]:
    raw_grid = value if isinstance(value, Mapping) else {}
    lookback_grid = _int_grid(raw_grid.get("lookback_days", (63,)))
    max_gross_grid = _decimal_grid(raw_grid.get("max_gross_exposure", ("1",)))
    max_leg_grid = _decimal_grid(raw_grid.get("max_leg_weight", ("1",)))
    min_history_grid = _int_grid(raw_grid.get("min_history_days", (20,)))
    min_trailing_grid = _decimal_grid(raw_grid.get("min_trailing_return", ("0",)))
    target_vol_grid = _decimal_grid(raw_grid.get("target_annual_vol", ("0.20",)))
    top_n_grid = _int_grid(raw_grid.get("top_n_legs", (1,)))
    parameter_sets = []
    for (
        lookback_days,
        max_gross_exposure,
        max_leg_weight,
        min_history_days,
        min_trailing_return,
        target_annual_vol,
        top_n_legs,
    ) in product(
        lookback_grid,
        max_gross_grid,
        max_leg_grid,
        min_history_grid,
        min_trailing_grid,
        target_vol_grid,
        top_n_grid,
    ):
        if lookback_days <= 0:
            raise ValueError("lookback_days must be positive")
        if min_history_days <= 0:
            raise ValueError("min_history_days must be positive")
        if top_n_legs <= 0:
            raise ValueError("top_n_legs must be positive")
        if max_gross_exposure <= Decimal("0"):
            raise ValueError("max_gross_exposure must be positive")
        if max_leg_weight <= Decimal("0") or max_leg_weight > Decimal("1"):
            raise ValueError("max_leg_weight must be in (0, 1]")
        if target_annual_vol <= Decimal("0"):
            raise ValueError("target_annual_vol must be positive")
        parameter_sets.append(
            {
                "lookback_days": lookback_days,
                "max_gross_exposure": max_gross_exposure,
                "max_leg_weight": max_leg_weight,
                "min_history_days": min_history_days,
                "min_trailing_return": min_trailing_return,
                "target_annual_vol": target_annual_vol,
                "top_n_legs": top_n_legs,
            }
        )
    return tuple(parameter_sets)


def _int_grid(value: Any) -> tuple[int, ...]:
    values = value if isinstance(value, list | tuple) else (value,)
    return tuple(int(item) for item in values)


def _decimal_grid(value: Any) -> tuple[Decimal, ...]:
    values = value if isinstance(value, list | tuple) else (value,)
    return tuple(Decimal(str(item)) for item in values)


def _scan_loaded_periods(
    candidates: tuple[dict[str, Any], ...],
    periods: tuple[str, ...],
) -> dict[str, dict[str, dict[str, Any]]]:
    loaded: dict[str, dict[str, dict[str, Any]]] = {}
    for period in periods:
        period_legs = {}
        for candidate in candidates:
            name = str(candidate["name"])
            path = candidate["period_manifests"][period]
            period_legs[name] = _loaded_leg(
                {"manifest_path": path, "name": name, "weight": Decimal("1")}
            )
        loaded[period] = period_legs
    return loaded


def _scan_period_matrices(
    candidates: tuple[dict[str, Any], ...],
    loaded: Mapping[str, Mapping[str, dict[str, Any]]],
    periods: tuple[str, ...],
    reporting_grid: str,
) -> dict[str, dict[str, Any]]:
    matrices: dict[str, dict[str, Any]] = {}
    candidate_names = tuple(str(candidate["name"]) for candidate in candidates)
    for period in periods:
        period_legs = tuple(loaded[period][name] for name in candidate_names)
        timeline = _aligned_timeline(period_legs)
        rows = []
        for leg in period_legs:
            rows.append(_normalized_equity_series(leg["points"], timeline))
        matrices[period] = {
            "metric_indices": _metric_indices(timeline, reporting_grid),
            "series": np.asarray(rows, dtype=float),
            "timeline": timeline,
        }
    return matrices


def _aligned_timeline(loaded_legs: tuple[dict[str, Any], ...]) -> tuple[datetime, ...]:
    start = max(leg["points"][0][0] for leg in loaded_legs)
    end = min(leg["points"][-1][0] for leg in loaded_legs)
    if start > end:
        raise ValueError("portfolio ensemble legs do not have overlapping equity history")
    timeline = tuple(
        sorted(
            {
                point_time
                for leg in loaded_legs
                for point_time, _equity in leg["points"]
                if start <= point_time <= end
            }
        )
    )
    if len(timeline) < 2:
        raise ValueError("portfolio ensemble requires at least two aligned equity points")
    return timeline


def _normalized_equity_series(
    points: tuple[tuple[datetime, Decimal], ...],
    timeline: tuple[datetime, ...],
) -> list[float]:
    cursor = _point_index_at_or_before(points, timeline[0])
    base_equity = points[cursor][1]
    if base_equity <= Decimal("0"):
        raise ValueError("portfolio ensemble base equity must be positive")
    series: list[float] = []
    for timestamp in timeline:
        while cursor + 1 < len(points) and points[cursor + 1][0] <= timestamp:
            cursor += 1
        series.append(float(points[cursor][1] / base_equity))
    return series


def _metric_indices(timeline: tuple[datetime, ...], reporting_grid: str) -> tuple[int, ...]:
    if reporting_grid == "native":
        return tuple(range(len(timeline)))
    first_date = timeline[0].astimezone(UTC).date()
    by_date: dict[date, int] = {}
    for index, timestamp in enumerate(timeline):
        date_key = timestamp.astimezone(UTC).date()
        if date_key != first_date:
            by_date[date_key] = index
    metric_indices = (0, *tuple(by_date[key] for key in sorted(by_date)))
    if len(metric_indices) < 2:
        raise ValueError("portfolio ensemble daily_utc reporting requires at least two days")
    return metric_indices


def _weight_vectors(
    candidate_count: int,
    weight_step: Decimal,
    max_active_legs: int,
) -> tuple[tuple[Decimal, ...], ...]:
    units = int((Decimal("1") / weight_step).to_integral_exact())
    vectors: list[tuple[Decimal, ...]] = []

    def walk(index: int, remaining: int, current: list[int]) -> None:
        if index == candidate_count - 1:
            vector = (*current, remaining)
            if 0 < sum(1 for item in vector if item) <= max_active_legs:
                vectors.append(tuple(Decimal(item) * weight_step for item in vector))
            return
        for value in range(remaining + 1):
            walk(index + 1, remaining - value, [*current, value])

    walk(0, units, [])
    return tuple(vectors)


def _scan_allocation(
    candidates: tuple[dict[str, Any], ...],
    period_matrices: Mapping[str, Mapping[str, Any]],
    periods: tuple[str, ...],
    weights: tuple[Decimal, ...],
    *,
    baseline_period: str,
    post_periods: tuple[str, ...],
    score_periods: tuple[str, ...],
    constraints: Mapping[str, Decimal],
) -> dict[str, Any]:
    active = [(candidate, weight) for candidate, weight in zip(candidates, weights, strict=True)]
    weight_array = np.asarray([float(weight) for weight in weights], dtype=float)
    period_metrics: dict[str, dict[str, Decimal]] = {}
    for period in periods:
        matrix = period_matrices[period]
        equity = weight_array @ matrix["series"]
        metrics = _float_metrics(matrix["timeline"], equity, matrix["metric_indices"])
        period_metrics[period] = {
            "annual_return": metrics["annual_return"],
            "full_curve_max_drawdown": metrics["full_curve_max_drawdown"],
            "sharpe_ratio": metrics["sharpe_ratio"],
            "total_return": metrics["total_return"],
        }
    baseline_return = period_metrics[baseline_period]["annual_return"]
    min_post_return = min(period_metrics[period]["annual_return"] for period in post_periods)
    min_post_sharpe = min(period_metrics[period]["sharpe_ratio"] for period in post_periods)
    max_full_drawdown = max(
        period_metrics[period]["full_curve_max_drawdown"] for period in score_periods
    )
    meets_constraints = (
        baseline_return >= constraints["min_baseline_annual_return"]
        and min_post_return >= constraints["min_post_annual_return"]
        and max_full_drawdown <= constraints["max_full_drawdown"]
    )
    score = (
        min_post_return + (baseline_return * Decimal("0.5")) - (max_full_drawdown * Decimal("0.25"))
    )
    return {
        "meets_constraints": meets_constraints,
        "metrics": period_metrics,
        "summary": {
            "baseline_annual_return": baseline_return,
            "max_full_drawdown": max_full_drawdown,
            "min_post_annual_return": min_post_return,
            "min_post_sharpe_ratio": min_post_sharpe,
        },
        "score": score,
        "weights": {
            str(candidate["name"]): weight for candidate, weight in active if weight > Decimal("0")
        },
    }


def _volatility_managed_allocation(
    period_matrices: Mapping[str, Mapping[str, Any]],
    periods: tuple[str, ...],
    parameters: Mapping[str, Any],
    *,
    baseline_period: str,
    selection_periods: tuple[str, ...],
    post_selection_periods: tuple[str, ...],
    constraints: Mapping[str, Decimal],
) -> dict[str, Any]:
    period_metrics: dict[str, dict[str, Decimal]] = {}
    for period in periods:
        period_metrics[period] = _volatility_managed_period_metrics(
            period_matrices[period],
            parameters,
        )
    baseline_return = period_metrics[baseline_period]["annual_return"]
    min_post_return = min(
        period_metrics[period]["annual_return"] for period in post_selection_periods
    )
    min_post_sharpe = min(
        period_metrics[period]["sharpe_ratio"] for period in post_selection_periods
    )
    max_selection_drawdown = max(
        period_metrics[period]["full_curve_max_drawdown"] for period in selection_periods
    )
    meets_constraints = (
        baseline_return >= constraints["min_baseline_annual_return"]
        and min_post_return >= constraints["min_selection_post_annual_return"]
        and max_selection_drawdown <= constraints["max_selection_drawdown"]
    )
    score = (
        min_post_return
        + (baseline_return * Decimal("0.5"))
        - (max_selection_drawdown * Decimal("0.25"))
    )
    return {
        "meets_constraints": meets_constraints,
        "metrics": period_metrics,
        "parameters": dict(parameters),
        "score": score,
        "summary": {
            "baseline_annual_return": baseline_return,
            "max_selection_drawdown": max_selection_drawdown,
            "min_selection_post_annual_return": min_post_return,
            "min_selection_post_sharpe_ratio": min_post_sharpe,
        },
    }


def _volatility_managed_period_metrics(
    matrix: Mapping[str, Any],
    parameters: Mapping[str, Any],
) -> dict[str, Decimal]:
    metric_indices = matrix["metric_indices"]
    timeline = tuple(matrix["timeline"][index] for index in metric_indices)
    series = matrix["series"][:, list(metric_indices)]
    if series.shape[1] < 2:
        raise ValueError("volatility managed allocation requires at least two metric points")
    returns = (series[:, 1:] / series[:, :-1]) - 1.0
    equity = np.ones(returns.shape[1] + 1, dtype=float)
    active_days = 0
    gross_exposure_total = 0.0
    for return_index in range(returns.shape[1]):
        weights, gross_exposure = _volatility_managed_interval_weights(
            returns,
            return_index,
            parameters,
        )
        if gross_exposure > 0:
            active_days += 1
            gross_exposure_total += gross_exposure
        interval_return = gross_exposure * float(weights @ returns[:, return_index])
        equity[return_index + 1] = equity[return_index] * (1.0 + interval_return)
        if equity[return_index + 1] <= 0:
            raise ValueError("volatility managed allocation equity became non-positive")
    metrics = _float_metrics(timeline, equity, tuple(range(len(timeline))))
    return {
        **metrics,
        "active_day_fraction": Decimal(str(active_days / returns.shape[1])),
        "average_gross_exposure": Decimal(
            str(gross_exposure_total / active_days if active_days else 0.0)
        ),
    }


def _volatility_managed_interval_weights(
    returns: np.ndarray[Any, Any],
    return_index: int,
    parameters: Mapping[str, Any],
) -> tuple[np.ndarray[Any, Any], float]:
    candidate_count = returns.shape[0]
    empty_weights = np.zeros(candidate_count, dtype=float)
    lookback_days = int(parameters["lookback_days"])
    min_history_days = int(parameters["min_history_days"])
    if return_index < min_history_days:
        return empty_weights, 0.0
    history_start = max(0, return_index - lookback_days)
    history = returns[:, history_start:return_index]
    if history.shape[1] < min_history_days:
        return empty_weights, 0.0
    trailing_returns = np.prod(1.0 + history, axis=1) - 1.0
    qualified = trailing_returns >= float(parameters["min_trailing_return"])
    if not bool(np.any(qualified)):
        return empty_weights, 0.0
    ranked_indices = np.argsort(trailing_returns)[::-1]
    selected = [index for index in ranked_indices if qualified[index]][
        : int(parameters["top_n_legs"])
    ]
    if not selected:
        return empty_weights, 0.0
    selected_array = np.asarray(selected, dtype=int)
    selected_history = history[selected_array, :]
    volatility = _annualized_history_volatility(selected_history)
    inverse_volatility = 1.0 / volatility
    selected_weights = inverse_volatility / float(np.sum(inverse_volatility))
    max_leg_weight = float(parameters["max_leg_weight"])
    selected_weights = np.minimum(selected_weights, max_leg_weight)
    weights = empty_weights.copy()
    weights[selected_array] = selected_weights
    portfolio_history = weights @ history
    portfolio_volatility = float(
        _annualized_history_volatility(portfolio_history.reshape(1, -1))[0]
    )
    target_annual_vol = float(parameters["target_annual_vol"])
    max_gross_exposure = float(parameters["max_gross_exposure"])
    gross_exposure = min(max_gross_exposure, target_annual_vol / portfolio_volatility)
    return weights, gross_exposure


def _annualized_history_volatility(history: np.ndarray[Any, Any]) -> np.ndarray[Any, Any]:
    stddev = np.std(history, axis=1)
    mean_abs = np.mean(np.abs(history), axis=1)
    daily_volatility = np.maximum(np.maximum(stddev, mean_abs), 1e-8)
    annualized = daily_volatility * math.sqrt(252.0)
    return np.asarray(annualized, dtype=float)


def _float_metrics(
    timeline: tuple[datetime, ...],
    equity: np.ndarray[Any, Any],
    metric_indices: tuple[int, ...],
) -> dict[str, Decimal]:
    metric_equity = equity[list(metric_indices)]
    first = float(metric_equity[0])
    last = float(metric_equity[-1])
    years = (timeline[metric_indices[-1]] - timeline[metric_indices[0]]).total_seconds() / 31557600
    total_return = (last / first) - 1.0
    annual_return = (last / first) ** (1.0 / years) - 1.0 if years > 0 else 0.0
    returns = (metric_equity[1:] / metric_equity[:-1]) - 1.0
    stddev = float(np.std(returns)) if len(returns) else 0.0
    mean_return = float(np.mean(returns)) if len(returns) else 0.0
    periods_per_year = len(returns) / years if years > 0 else 0.0
    sharpe = (mean_return / stddev) * math.sqrt(periods_per_year) if stddev > 0 else 0.0
    running_peak = np.maximum.accumulate(equity)
    drawdowns = (running_peak - equity) / running_peak
    return {
        "annual_return": Decimal(str(annual_return)),
        "full_curve_max_drawdown": Decimal(str(float(np.max(drawdowns)))),
        "sharpe_ratio": Decimal(str(sharpe)),
        "total_return": Decimal(str(total_return)),
    }


def _reporting_grid(payload: Mapping[str, Any]) -> str:
    value = str(payload.get("reporting_grid", "native")).strip()
    if value not in {"daily_utc", "native"}:
        raise ValueError("portfolio_ensemble.reporting_grid must be native or daily_utc")
    return value


def _loaded_leg(leg: Mapping[str, Any]) -> dict[str, Any]:
    manifest_path = Path(leg["manifest_path"])
    if not manifest_path.exists():
        raise FileNotFoundError(f"portfolio ensemble manifest not found: {manifest_path}")
    manifest = _read_json_object(manifest_path)
    equity_path = _equity_curve_artifact_path(manifest, manifest_path)
    return {
        "manifest_path": manifest_path,
        "name": str(leg["name"]),
        "points": _read_equity_curve(equity_path),
        "weight": leg["weight"],
    }


def _combined_equity_curve(
    loaded_legs: tuple[dict[str, Any], ...],
) -> tuple[tuple[datetime, Decimal], ...]:
    start = max(leg["points"][0][0] for leg in loaded_legs)
    end = min(leg["points"][-1][0] for leg in loaded_legs)
    if start > end:
        raise ValueError("portfolio ensemble legs do not have overlapping equity history")
    timeline = sorted(
        {
            point_time
            for leg in loaded_legs
            for point_time, _equity in leg["points"]
            if start <= point_time <= end
        }
    )
    if len(timeline) < 2:
        raise ValueError("portfolio ensemble requires at least two aligned equity points")
    total_weight = sum((leg["weight"] for leg in loaded_legs), Decimal("0"))
    cursors = [_point_index_at_or_before(leg["points"], start) for leg in loaded_legs]
    base_equities = [
        leg["points"][cursor][1] for leg, cursor in zip(loaded_legs, cursors, strict=True)
    ]
    if any(base_equity <= Decimal("0") for base_equity in base_equities):
        raise ValueError("portfolio ensemble base equity must be positive")
    equity_curve: list[tuple[datetime, Decimal]] = []
    for timestamp in timeline:
        combined = Decimal("0")
        for index, leg in enumerate(loaded_legs):
            points = leg["points"]
            cursor = cursors[index]
            while cursor + 1 < len(points) and points[cursor + 1][0] <= timestamp:
                cursor += 1
            cursors[index] = cursor
            combined += (leg["weight"] / total_weight) * (points[cursor][1] / base_equities[index])
        equity_curve.append((timestamp, combined))
    return tuple(equity_curve)


def _point_index_at_or_before(
    points: tuple[tuple[datetime, Decimal], ...],
    timestamp: datetime,
) -> int:
    index = 0
    while index + 1 < len(points) and points[index + 1][0] <= timestamp:
        index += 1
    return index


def _equity_curve_artifact_path(manifest: Mapping[str, Any], manifest_path: Path) -> Path:
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, Mapping):
        raise ValueError(f"manifest is missing artifacts mapping: {manifest_path}")
    equity_artifact = artifacts.get("equity_curve")
    if not isinstance(equity_artifact, Mapping):
        raise ValueError(f"manifest is missing equity_curve artifact: {manifest_path}")
    raw_path = equity_artifact.get("path")
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise ValueError(f"manifest equity_curve artifact path is required: {manifest_path}")
    artifact_path = Path(raw_path)
    if ".partial." in artifact_path.name or artifact_path.name.startswith("."):
        raise ValueError(f"partial equity curve artifact is not valid: {artifact_path}")
    if not artifact_path.is_absolute() and not artifact_path.exists():
        artifact_path = manifest_path.parent / artifact_path
    if not artifact_path.exists():
        raise FileNotFoundError(f"equity curve artifact not found: {artifact_path}")
    return artifact_path


def _read_equity_curve(path: Path) -> tuple[tuple[datetime, Decimal], ...]:
    points: list[tuple[datetime, Decimal]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, Mapping):
            raise ValueError(f"equity curve row must be a JSON object: {path}:{line_number}")
        point = (
            _parse_datetime(row.get("time"), path=path, line_number=line_number),
            Decimal(str(row["equity"])),
        )
        if point[1] <= Decimal("0"):
            raise ValueError(f"equity curve equity values must be positive: {path}")
        if points and point[0] < points[-1][0]:
            raise ValueError(f"equity curve timestamps must be increasing: {path}")
        if points and point[0] == points[-1][0]:
            points[-1] = point
        else:
            points.append(point)
    if len(points) < 2:
        raise ValueError(f"equity curve artifact must contain at least two rows: {path}")
    return tuple(points)


def _metric_curve(
    equity_curve: tuple[tuple[datetime, Decimal], ...],
    reporting_grid: str,
) -> tuple[tuple[datetime, Decimal], ...]:
    if reporting_grid == "native":
        return equity_curve
    first_date = equity_curve[0][0].astimezone(UTC).date()
    by_date: dict[date, tuple[datetime, Decimal]] = {}
    for timestamp, equity in equity_curve:
        date_key = timestamp.astimezone(UTC).date()
        if date_key != first_date:
            by_date[date_key] = (timestamp, equity)
    metric_curve = (equity_curve[0], *tuple(by_date[key] for key in sorted(by_date)))
    if len(metric_curve) < 2:
        raise ValueError("portfolio ensemble daily_utc reporting requires at least two days")
    return metric_curve


def _read_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON artifact must be an object: {path}")
    return payload


def _parse_datetime(value: Any, *, path: Path, line_number: int) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"equity curve time is required: {path}:{line_number}")
    text = value.strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    parsed = datetime.fromisoformat(text)
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def _metrics(equity_curve: tuple[tuple[datetime, Decimal], ...]) -> dict[str, Decimal]:
    first = equity_curve[0][1]
    last = equity_curve[-1][1]
    returns = [
        (current[1] / previous[1]) - Decimal("1") for previous, current in pairwise(equity_curve)
    ]
    return {
        "compounding_annual_return": _compounding_annual_return(equity_curve),
        "max_drawdown": _max_drawdown(equity_curve),
        "sharpe_ratio": _sharpe_ratio(equity_curve, returns),
        "total_return": (last / first) - Decimal("1"),
        "volatility_annual": _volatility_annual(equity_curve, returns),
    }


def _compounding_annual_return(equity_curve: tuple[tuple[datetime, Decimal], ...]) -> Decimal:
    years = _elapsed_years(equity_curve)
    if years <= Decimal("0"):
        return Decimal("0")
    total_growth = equity_curve[-1][1] / equity_curve[0][1]
    return Decimal(str(float(total_growth) ** (1.0 / float(years)) - 1.0))


def _volatility_annual(
    equity_curve: tuple[tuple[datetime, Decimal], ...],
    returns: Sequence[Decimal],
) -> Decimal:
    stddev = _stddev(returns)
    if stddev == Decimal("0"):
        return Decimal("0")
    return stddev * _periods_per_year(equity_curve, returns).sqrt()


def _sharpe_ratio(
    equity_curve: tuple[tuple[datetime, Decimal], ...],
    returns: Sequence[Decimal],
) -> Decimal:
    stddev = _stddev(returns)
    if stddev == Decimal("0"):
        return Decimal("0")
    return (_mean(returns) / stddev) * _periods_per_year(equity_curve, returns).sqrt()


def _periods_per_year(
    equity_curve: tuple[tuple[datetime, Decimal], ...],
    returns: Sequence[Decimal],
) -> Decimal:
    years = _elapsed_years(equity_curve)
    if years <= Decimal("0"):
        return Decimal("0")
    return Decimal(len(returns)) / years


def _elapsed_years(equity_curve: tuple[tuple[datetime, Decimal], ...]) -> Decimal:
    seconds = Decimal(str((equity_curve[-1][0] - equity_curve[0][0]).total_seconds()))
    return seconds / Decimal("31557600")


def _max_drawdown(equity_curve: tuple[tuple[datetime, Decimal], ...]) -> Decimal:
    peak = equity_curve[0][1]
    max_drawdown = Decimal("0")
    for _timestamp, equity in equity_curve:
        if equity > peak:
            peak = equity
        drawdown = (peak - equity) / peak
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    return max_drawdown


def _mean(values: Sequence[Decimal]) -> Decimal:
    if not values:
        return Decimal("0")
    return sum(values, Decimal("0")) / Decimal(len(values))


def _stddev(values: Sequence[Decimal]) -> Decimal:
    if len(values) < 2:
        return Decimal("0")
    mean = _mean(values)
    variance = sum(((value - mean) ** 2 for value in values), Decimal("0")) / Decimal(len(values))
    return variance.sqrt()


def _required_text(payload: Mapping[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required")
    return value.strip()


def _string_tuple(value: Any, *, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, list | tuple) or not value:
        raise ValueError(f"{field_name} must be a non-empty sequence")
    return tuple(str(item) for item in value)


def _validate_period_subset(
    selected_periods: tuple[str, ...],
    periods: tuple[str, ...],
    *,
    field_name: str,
) -> None:
    available = set(periods)
    missing = [period for period in selected_periods if period not in available]
    if missing:
        raise ValueError(f"{field_name} references unknown periods: {missing}")


def _json_decimal_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_decimal_ready(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_json_decimal_ready(item) for item in value]
    return value


__all__ = [
    "evaluate_portfolio_ensemble",
    "scan_portfolio_ensemble_allocations",
    "scan_volatility_managed_allocations",
]

_SCORING_PERIOD_ROLES = frozenset({"anchor", "selection", "validation"})
_REPORT_ONLY_PERIOD_ROLES = frozenset({"holdout_report_only", "true_oos_report_only"})
_ALLOCATION_OVERFIT_WARNING = (
    "Allocation scan is research-only evidence and is not a tradable runtime config."
)
_PERIOD_ROLES = _SCORING_PERIOD_ROLES | _REPORT_ONLY_PERIOD_ROLES
