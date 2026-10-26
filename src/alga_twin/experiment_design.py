"""Local expected Fisher information for explicit proposed experiments.

Conditional on a supported current fit, a chosen model and fixed noise/initial
states. No priors, hidden regularization, pseudo-observations or confidence
intervals. Candidate ranking is among supplied feasible choices, not global.
"""

import json
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from .calibration import ErrorModel, JointFitResult, predict_run, with_values
from .calibration_provenance import run_provenance
from .model import Conditions
from .models import ModelBase, simulate_model
from .version import __version__

DESIGN_METHOD = (
    "Local expected Fisher information; fixed independent noise; D-information gain at profile-supported fit"
)


@dataclass(frozen=True)
class ExperimentCandidate:
    name: str
    conditions: Conditions
    initial_state: tuple[float, ...]
    duration_day: float
    sampling_times_day: tuple[float, ...]
    observables: tuple[str, ...]
    errors: ErrorModel
    temperature_c: float | None
    technical_replicates: int = 1

    def __post_init__(self):
        times = np.asarray(self.sampling_times_day, dtype=float)
        if not self.name.strip() or not np.isfinite(self.duration_day) or not 0 < self.duration_day <= 365:
            raise ValueError("Supply a candidate name and finite duration in (0,365] days")
        if (
            times.ndim != 1
            or not len(times)
            or not np.isfinite(times).all()
            or times[0] < 0
            or times[-1] > self.duration_day
            or np.any(np.diff(times) <= 0)
        ):
            raise ValueError("Sampling days must be finite, increasing, unique and inside [0,duration]")
        if not self.observables or len(set(self.observables)) != len(self.observables):
            raise ValueError("Supply unique observables")
        if (
            isinstance(self.technical_replicates, bool)
            or not isinstance(self.technical_replicates, int)
            or self.technical_replicates < 1
        ):
            raise ValueError("Technical replicate count must be a positive integer")


@dataclass(frozen=True)
class DesignResult:
    ranking: pd.DataFrame
    information_before: np.ndarray
    information_candidates: dict[str, np.ndarray]
    parameters: tuple[str, ...]
    context: dict
    method: str = DESIGN_METHOD

    @property
    def top3(self):
        return self.ranking.head(3).copy()

    def report(self):
        return {
            "method": self.method,
            "software_version": __version__,
            "ranking": self.ranking.to_dict("records"),
            "parameters": self.parameters,
            "information_before_normalized_coordinates": self.information_before.tolist(),
            "candidate_information_normalized_coordinates": {
                k: v.tolist() for k, v in self.information_candidates.items()
            },
            "context": self.context,
            "scope": "Expected local uncertainty reduction, not intervals, empirical coverage or independent validation",
        }


def _identity(value):
    return json.dumps(value, sort_keys=True, allow_nan=False)


def _bind_fit(runs, fit):
    values = fit.values()  # Never recover a hidden optimum from an unsupported fit.
    supplied = sorted((run_provenance(r) for r in runs), key=lambda r: r["run_id"])
    recorded = sorted(fit.provenance, key=lambda r: r["run_id"])
    if _identity(supplied) != _identity(recorded) or set(values) != set(fit.search):
        raise ValueError("Stale/mismatched fit: observations, model, provenance and search must match")
    nll = 0.0
    for run in runs:
        predicted, curve = predict_run(run, values)
        nll += fit.error_model.nll(
            run.observations.value.to_numpy(),
            predicted,
            run.observations.observable,
            curve.attrs["log_predictions"],
        )
    if not np.isclose(nll, fit.nll, rtol=1e-8, atol=1e-6):
        raise ValueError("Stale fit: noise or likelihood differs from the fitted job")
    return values


def _candidate_model(template, candidate, values):
    model = type(template)(
        dict(template.params),
        candidate.conditions,
        light=template.light,
        diurnal=template.diurnal,
        temperature_c=candidate.temperature_c,
    )
    initial = model.validate_initial(candidate.initial_state)
    if not np.allclose(
        initial[:2],
        [candidate.conditions.biomass_initial_g_L, candidate.conditions.nitrogen_initial_mg_L],
        rtol=1e-12,
        atol=1e-12,
    ):
        raise ValueError("Proposed initial X/N conflicts with conditions")
    units = dict(zip(model.states, model.state_units, strict=True))
    for observable in candidate.observables:
        if observable not in units or observable not in candidate.errors.scales:
            raise ValueError("Proposed observable/noise scale is missing or incompatible")
        unit = "dimensionless" if candidate.errors.kind == "log-normal" else units[observable]
        if candidate.errors.scales[observable][1] != unit:
            raise ValueError("Proposed noise units must match canonical units (log SD is dimensionless)")
    return with_values(model, values)


def candidate_prediction(template: ModelBase, candidate: ExperimentCandidate, values):
    """Return weighted mean coordinates plus real model trajectory; no fabricated data."""
    model = _candidate_model(template, candidate, values)
    times = np.unique(np.r_[0.0, candidate.sampling_times_day, candidate.duration_day])
    curve = simulate_model(
        model,
        times,
        candidate.initial_state,
        rtol=1e-8,
        atol=1e-10,
        max_step_day=0.5,
        log_nitrogen=candidate.initial_state[1] > 0,
    )
    indices = np.searchsorted(times, candidate.sampling_times_day)
    coordinates = []
    for state in candidate.observables:
        pred = curve[state].to_numpy()[indices]
        if candidate.errors.kind == "log-normal":
            if state == "N" and "log_N" in curve:
                pred = curve.log_N.to_numpy()[indices]
            else:
                if np.any(pred <= 0):
                    raise ValueError(
                        "Log-normal proposed measurements need positive predictions; no pseudocount"
                    )
                pred = np.log(pred)
        coordinates.extend(pred / candidate.errors.scales[state][0])
    result = np.tile(coordinates, candidate.technical_replicates)
    if not np.isfinite(result).all():
        raise ValueError("Non-finite proposed prediction")
    return result, curve


def _observed_coordinates(runs, values, errors):
    coordinates = []
    for run in runs:
        pred, curve = predict_run(run, values)
        if errors.kind == "log-normal":
            pred = curve.attrs["log_predictions"]
        sd = np.array([errors.scales[name][0] for name in run.observations.observable])
        coordinates.extend(pred / sd)
    return np.asarray(coordinates)


def _information(predict, fit, values, step, derivative_rtol):
    names = tuple(fit.search)
    z = np.array([fit.search[name].encode(values[name]) for name in names])
    if np.any(z <= step) or np.any(z >= 1 - step):
        raise ValueError("Fit too close to a search boundary for central Fisher differences")
    columns = []
    for i, name in enumerate(names):
        derivatives = []
        for h in (step, step / 2):
            plus, minus = dict(values), dict(values)
            plus[name], minus[name] = fit.search[name].decode(z[i] + h), fit.search[name].decode(z[i] - h)
            derivatives.append((predict(plus) - predict(minus)) / (2 * h))
        full, half = derivatives
        if np.linalg.norm(full - half) > derivative_rtol * max(np.linalg.norm(half), 1e-6):
            raise ValueError(f"Unstable sensitivity for {name}; change numerical controls before ranking")
        columns.append(half)
    jacobian = np.column_stack(columns)
    return jacobian.T @ jacobian


def rank_experiments(
    runs, fit: JointFitResult, candidates, *, step=1e-4, derivative_rtol=0.02, max_condition=1e12
):
    """Rank whole candidate runs individually added to the SAME current data.

    SD ratios and ellipsoid-volume reductions are local Fisher approximations,
    never profile confidence intervals. Numerical controls are exported. No
    automatic physical-feasibility/cost assertion is made about supplied choices.
    """
    runs, candidates = tuple(runs), tuple(candidates)
    if not runs or not candidates or len({c.name for c in candidates}) != len(candidates):
        raise ValueError("Supply fitted runs and uniquely named proposed candidates")
    if (
        not np.all(np.isfinite([step, derivative_rtol, max_condition]))
        or not 0 < step < 0.1
        or not 0 < derivative_rtol < 1
        or max_condition <= 1
    ):
        raise ValueError("Invalid numerical Fisher controls")
    values = _bind_fit(runs, fit)
    base = _information(
        lambda v: _observed_coordinates(runs, v, fit.error_model), fit, values, step, derivative_rtol
    )
    if not np.isfinite(base).all() or np.linalg.cond(base) > max_condition:
        raise ValueError(
            "Current Fisher matrix is singular/ill-conditioned; no regularized ranking is supplied"
        )
    try:
        np.linalg.cholesky(base)
    except np.linalg.LinAlgError as exc:
        raise ValueError("Current Fisher matrix is not positive definite") from exc
    logdet = np.linalg.slogdet(base)[1]
    variance = np.diag(np.linalg.inv(base))
    names, rows, information = tuple(fit.search), [], {}
    for candidate in candidates:
        # Validate even a parameter-insensitive candidate before differencing.
        candidate_prediction(runs[0].model, candidate, values)
        added = _information(
            lambda v, c=candidate: candidate_prediction(runs[0].model, c, v)[0],
            fit,
            values,
            step,
            derivative_rtol,
        )
        total = base + added
        gain = float(np.linalg.slogdet(total)[1] - logdet)
        if gain < -1e-8:
            raise ValueError("Numerically negative information gain; ranking refused")
        gain = max(0.0, gain)
        ratios = np.sqrt(np.diag(np.linalg.inv(total)) / variance)
        best = int(np.argmin(ratios))
        information[candidate.name] = added
        rows.append(
            {
                "candidate": candidate.name,
                "origin": "PROPOSED",
                "light_umol_m2_s": candidate.conditions.incident_light_umol_m2_s,
                "initial_N_mg_N_L": candidate.conditions.nitrogen_initial_mg_L,
                "duration_day": candidate.duration_day,
                "sampling_times_day": list(candidate.sampling_times_day),
                "scalar_measurements": len(candidate.sampling_times_day)
                * len(candidate.observables)
                * candidate.technical_replicates,
                "log_det_information_gain": gain,
                "local_ellipsoid_volume_reduction_fraction": float(-np.expm1(-gain / 2)),
                "local_sd_ratio_by_parameter": dict(zip(names, map(float, ratios), strict=True)),
                "reason": f"Adds information about {names[best]}; expected local SD ratio {ratios[best]:.3f}. "
                f"Light {candidate.conditions.incident_light_umol_m2_s:g}, initial N {candidate.conditions.nitrogen_initial_mg_L:g}; "
                f"{len(candidate.sampling_times_day)} sampling times over {candidate.duration_day:g} days. Conditional on supplied model/noise.",
            }
        )
    ranking = (
        pd.DataFrame(rows)
        .sort_values(["log_det_information_gain", "candidate"], ascending=[False, True])
        .reset_index(drop=True)
    )
    ranking.insert(0, "rank", np.arange(1, len(ranking) + 1))
    context = {
        "current_fit": fit.report(),
        "candidates": [asdict(c) for c in candidates],
        "step_in_normalized_search_coordinates": step,
        "derivative_rtol": derivative_rtol,
        "max_condition": max_condition,
        "base_condition_number": float(np.linalg.cond(base)),
        "assumptions": "Local plug-in fit; independent fixed noise; initial states/fixed parameters known; no cost normalization; no model-discrimination objective",
    }
    return DesignResult(ranking, base, information, names, context)
