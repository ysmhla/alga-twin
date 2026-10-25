"""Conditional multi-run likelihood, reoptimized profiles and whole-run holdouts.

No implicit biological bounds or measurement variances. Profiles are numerical,
conditional on supplied fixed parameters/initial states/noise, not structural
identifiability proofs or independent biological validation. See CALIBRATION.md.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, replace
from itertools import product

import numpy as np
import pandas as pd
from scipy.optimize import brentq, least_squares
from scipy.stats import chi2

from .models import ModelBase, simulate_model

PROFILE_METHOD = (
    "Reoptimized profile likelihood; marginal chi-square(df=1) asymptotic cutoff; fixed noise scales"
)
_CONTROL_PARAMS = {"period_day", "daylight_day", "dawn_day"}


@dataclass(frozen=True)
class FitParameter:
    """User search bounds, never a source-reported physiological range."""

    low: float
    high: float
    initial: float
    scale: str = "log"

    def __post_init__(self):
        if not np.all(np.isfinite([self.low, self.high, self.initial])):
            raise ValueError("Search bounds/initial must be finite")
        if not self.low < self.high or not self.low <= self.initial <= self.high:
            raise ValueError("Require low < high with initial inside bounds")
        if self.scale not in {"log", "linear"} or (self.scale == "log" and self.low <= 0):
            raise ValueError("Choose linear or positive log search bounds")

    def decode(self, coordinate):
        if coordinate <= 0:
            return self.low
        if coordinate >= 1:
            return self.high
        if self.scale == "log":
            return float(np.exp(np.log(self.low) + coordinate * np.log(self.high / self.low)))
        return float(self.low + coordinate * (self.high - self.low))

    def encode(self, value):
        if self.scale == "log":
            return float(np.log(value / self.low) / np.log(self.high / self.low))
        return float((value - self.low) / (self.high - self.low))


@dataclass(frozen=True)
class ErrorModel:
    """Known/assumed fixed SD per observable: (sigma, canonical unit).

    Additive sigma has observation units; log-normal sigma is dimensionless.
    Log-normal prediction is the conditional median, not the arithmetic mean.
    """

    kind: str
    scales: dict[str, tuple[float, str]]

    def __post_init__(self):
        if self.kind not in {"additive", "log-normal"} or not self.scales:
            raise ValueError("Choose additive or log-normal with explicit noise scales")
        for sigma, unit in self.scales.values():
            if not np.isfinite(sigma) or sigma <= 0 or not unit:
                raise ValueError("Noise SD must be finite, positive and have an explicit unit")

    def residuals(self, observed, predicted, observable, log_predicted=None):
        sd = np.array([self.scales[name][0] for name in observable])
        if np.any(~np.isfinite(predicted)):
            raise ValueError("Non-finite prediction")
        if self.kind == "log-normal":
            if np.any(observed <= 0) or (log_predicted is None and np.any(predicted <= 0)):
                raise ValueError(
                    "Log-normal errors require positive observations and predictions; no pseudocount"
                )
            log_values = np.log(predicted) if log_predicted is None else log_predicted
            if np.any(~np.isfinite(log_values)):
                raise ValueError("Non-finite log predictions; no pseudocount or noise-floor substitution")
            return (log_values - np.log(observed)) / sd
        return (predicted - observed) / sd

    def nll(self, observed, predicted, observable, log_predicted=None):
        r = self.residuals(observed, predicted, observable, log_predicted)
        sd = np.array([self.scales[name][0] for name in observable])
        constants = np.log(sd) + 0.5 * np.log(2 * np.pi)
        if self.kind == "log-normal":
            constants += np.log(observed)  # Jacobian: density on the original measurement scale.
        return float(np.sum(0.5 * r**2 + constants))


@dataclass(frozen=True)
class CalibrationRun:
    run_id: str
    model: ModelBase
    initial_state: tuple[float, ...]
    observations: pd.DataFrame
    origin: str

    def __post_init__(self):
        if (
            not isinstance(self.run_id, str)
            or not self.run_id.strip()
            or self.origin not in {"SYNTHETIC", "MEASURED", "UNSPECIFIED"}
        ):
            raise ValueError("Run id and explicit SYNTHETIC/MEASURED/UNSPECIFIED origin are required")
        initial = self.model.validate_initial(self.initial_state)
        object.__setattr__(self, "initial_state", tuple(float(v) for v in initial))
        declared = [self.model.conditions.biomass_initial_g_L, self.model.conditions.nitrogen_initial_mg_L]
        if not np.allclose(initial[:2], declared, rtol=1e-12, atol=1e-12):
            raise ValueError(
                "Initial X/N conflicts with declared conditions; supply consistent explicit starting values"
            )
        required = {"time_day", "observable", "value", "unit", "replicate"}
        if set(self.observations.columns) != required or self.observations.empty:
            raise ValueError(f"Use nonempty long-form observations with columns {sorted(required)}")
        data = self.observations.copy(deep=True).reset_index(drop=True)
        if data.isna().any().any():
            raise ValueError("Missing observations/metadata must be omitted, not represented as NaN rows")
        for column in ("time_day", "value"):
            data[column] = pd.to_numeric(data[column], errors="raise")
            if not np.all(np.isfinite(data[column])):
                raise ValueError("Observations/times must be finite")
        if data.time_day.min() < 0 or not 0 < data.time_day.max() <= 365:
            raise ValueError("Observation days must be nonnegative with at least one positive day <=365")
        if not data.observable.isin(self.model.states).all():
            raise ValueError("Unknown observable for selected model")
        units = dict(zip(self.model.states, self.model.state_units, strict=True))
        if any(unit != units[obs] for obs, unit in zip(data.observable, data.unit, strict=True)):
            raise ValueError("Observation units must match canonical solver units; convert explicitly")
        if any(not str(item).strip() for item in data.replicate):
            raise ValueError("Replicate identifiers cannot be empty")
        data["replicate"] = data.replicate.astype(str)
        if data.duplicated(["time_day", "observable", "replicate"]).any():
            raise ValueError("Duplicate measurement identity; use distinct technical replicate ids")
        object.__setattr__(self, "observations", data)


def with_values(model: ModelBase, values: dict[str, float]) -> ModelBase:
    """Revoke source-value verification on fitted values; retain fixed evidence."""
    params = dict(model.params)
    for name, value in values.items():
        params[name] = replace(
            params[name],
            value=float(value),
            status="UNVERIFIED",
            low=None,
            high=None,
            evidence="fitted_value",
        )
    return type(model)(
        params, model.conditions, light=model.light, temperature_c=model.temperature_c, diurnal=model.diurnal
    )


def predict_run(run: CalibrationRun, values: dict[str, float]):
    times = np.unique(np.r_[0.0, run.observations.time_day])
    model = with_values(run.model, values)
    trajectory = simulate_model(
        model,
        times,
        run.initial_state,
        rtol=1e-8,
        atol=1e-10,
        max_step_day=0.5,
        log_nitrogen=run.initial_state[1] > 0,
    )
    rows = np.searchsorted(times, run.observations.time_day)
    cols = np.array([model.states.index(obs) for obs in run.observations.observable])
    predicted = trajectory[list(model.states)].to_numpy()[rows, cols]
    with np.errstate(divide="ignore"):
        logs = np.log(predicted)
    n_mask = run.observations.observable.to_numpy() == "N"
    if "log_N" in trajectory:
        logs[n_mask] = trajectory.log_N.to_numpy()[rows[n_mask]]
    trajectory.attrs["log_predictions"] = logs
    return predicted, trajectory


@dataclass(frozen=True)
class ParameterEstimate:
    value: float | None
    interval: tuple[float, float] | None
    unit: str
    status: str
    reason: str
    method: str = PROFILE_METHOD


@dataclass(frozen=True)
class JointFitResult:
    estimates: dict[str, ParameterEstimate]
    profiles: pd.DataFrame
    predictions: pd.DataFrame
    metrics: pd.DataFrame
    optimizer_success: bool
    nll: float
    confidence: float
    cutoff: float
    search: dict[str, FitParameter]
    error_model: ErrorModel
    provenance: tuple[dict, ...]
    flat_tolerance: float

    @property
    def supported(self):
        return self.optimizer_success and all(e.status == "IDENTIFIABLE" for e in self.estimates.values())

    def table(self):
        return pd.DataFrame([{"parameter": name, **asdict(e)} for name, e in self.estimates.items()])

    def values(self):
        if not self.supported:
            raise ValueError("NOT IDENTIFIABLE or unresolved profiles: refusing parameter point estimates")
        return {name: e.value for name, e in self.estimates.items()}

    def report(self):
        return {
            "supported": self.supported,
            "optimizer_success": self.optimizer_success,
            "estimates": {name: asdict(e) for name, e in self.estimates.items()},
            "interval_method": PROFILE_METHOD,
            "confidence": self.confidence,
            "cutoff": self.cutoff,
            "interval_scope": "Marginal asymptotic, conditional on fixed parameters, initial states and specified SDs",
            "search_bounds_not_literature_ranges": {name: asdict(p) for name, p in self.search.items()},
            "error_model": asdict(self.error_model),
            "flat_tolerance_delta_deviance": self.flat_tolerance,
            "nll_in_sample": self.nll,
            "metrics_in_sample": self.metrics.to_dict("records"),
            "runs": list(self.provenance),
            "scientific_status": "In-sample likelihood and numerical profiles; no independent biological validation",
        }


def _validate_problem(runs, search, errors):
    if not runs or not search or len({r.run_id for r in runs}) != len(runs):
        raise ValueError("Supply nonempty runs, unique run ids and explicit search bounds")
    reference = runs[0].model
    if len({r.origin for r in runs}) != 1:
        raise ValueError("Do not mix synthetic and measured runs in one likelihood")
    tiers = {p.tier for run in runs for p in run.model.params.values()}
    if "DEMO" in tiers and tiers != {"DEMO"}:
        raise ValueError("Do not mix DEMO and research parameter tiers across runs")
    observables = set()
    events, informative = set(), 0
    for run in runs:
        model = run.model
        if (type(model), model.light, model.diurnal, model.params.keys()) != (
            type(reference),
            reference.light,
            reference.diurnal,
            reference.params.keys(),
        ):
            raise ValueError("Joint runs must use the same nutrient/light/forcing model structure")
        for name, record in model.params.items():
            other = reference.params[name]
            if record.species != other.species or record.unit != other.unit or record.basis != other.basis:
                raise ValueError("Joint parameter species, units and bases must match")
            if name not in search and name not in _CONTROL_PARAMS and record.value != other.value:
                raise ValueError(f"Fixed shared parameter {name} differs across runs")
        if search.keys() - model.params.keys() or set(search) & (_CONTROL_PARAMS | {"extinction_exponent"}):
            raise ValueError("Unknown/inactive fitted parameter or forcing/exponent fitting not supported")
        observables.update(run.observations.observable)
        informative += int((run.observations.time_day > 0).sum())
        events.update((run.run_id, t) for t in run.observations.time_day if t > 0)
        # Check physical bounds before optimisation. Coupled quota/cardinal corners
        # are checked together, so invalid trial boxes cannot masquerade as flat fits.
        candidates = [{name: p.initial for name, p in search.items()}]
        for name, spec in search.items():
            candidates.extend({**candidates[0], name: edge} for edge in (spec.low, spec.high))
        for group in (("q_min", "q_max"), ("t_min", "t_opt", "t_max")):
            active = [name for name in group if name in search]
            for edges in product(*[(search[name].low, search[name].high) for name in active]):
                candidates.append({**candidates[0], **dict(zip(active, edges, strict=True))})
        for candidate in candidates:
            with_values(model, candidate).validate_initial(run.initial_state)
    if len(events) < 3 or informative < len(search) + 2:
        raise ValueError(
            "Too few informative points: need >=3 positive-time run/time events and >parameters+1 scalar measurements"
        )
    if not observables <= errors.scales.keys() or errors.scales.keys() - set(reference.states):
        raise ValueError("Supply an explicit noise scale for every observed state, with no unknown states")
    units = dict(zip(reference.states, reference.state_units, strict=True))
    for observable, (_, unit) in errors.scales.items():
        expected = units[observable] if errors.kind == "additive" else "dimensionless"
        if unit != expected:
            raise ValueError(f"Noise scale for {observable} must use {expected}")
    if errors.kind == "log-normal" and any((r.observations.value <= 0).any() for r in runs):
        raise ValueError(
            "Log-normal observations must be positive; zero/negative values require a different model"
        )


def fit_joint(
    runs,
    search: dict[str, FitParameter],
    errors: ErrorModel,
    *,
    confidence: float = 0.95,
    profile_points: int = 11,
    flat_tolerance: float = 1e-3,
    max_nfev: int = 120,
) -> JointFitResult:
    """Fit shared parameters, then reoptimize nuisance parameters at every profile point.

    Only two-sided, connected, interior profiles crossing the cutoff yield a
    point estimate/interval. Flat/open/failed/boundary/multimodal profiles do not.
    """
    runs = tuple(runs)
    _validate_problem(runs, search, errors)
    if not 0 < confidence < 1 or profile_points < 5 or profile_points % 2 == 0:
        raise ValueError("Confidence must lie in (0,1); use an odd profile grid >=5")
    if not np.isfinite(flat_tolerance) or flat_tolerance <= 0 or max_nfev < 1:
        raise ValueError("Positive flat tolerance and optimizer budget required")
    names = tuple(search)
    specs = tuple(search.values())
    x0 = np.array([p.encode(p.initial) for p in specs])
    cutoff = float(chi2.ppf(confidence, 1))

    def decode(vector):
        return {name: p.decode(x) for name, p, x in zip(names, specs, vector, strict=True)}

    def residual(vector):
        values = decode(vector)
        residuals = []
        for run in runs:
            predicted, trajectory = predict_run(run, values)
            residuals.append(
                errors.residuals(
                    run.observations.value.to_numpy(),
                    predicted,
                    run.observations.observable,
                    trajectory.attrs["log_predictions"],
                )
            )
        return np.concatenate(residuals)

    def optimize(starts, fixed=None):
        fixed = fixed or {}
        free = [i for i in range(len(names)) if i not in fixed]
        solutions = []
        seen = []
        for start in starts:
            candidate = np.asarray(start)[free]
            if any(np.allclose(candidate, previous, atol=1e-8) for previous in seen):
                continue
            seen.append(candidate)

            def expand(coordinate, start=start):
                full = np.array(start, dtype=float, copy=True)
                full[free] = coordinate
                for i, value in fixed.items():
                    full[i] = value
                return full

            if free:
                sol = least_squares(
                    lambda z: residual(expand(z)),
                    np.asarray(start)[free],
                    bounds=(0, 1),
                    diff_step=1e-4,
                    max_nfev=max_nfev,
                    ftol=1e-8,
                    xtol=1e-8,
                    gtol=1e-7,
                )
                vec, cost, success = expand(sol.x), float(2 * sol.cost), bool(sol.success)
            else:
                vec = expand([])
                r = residual(vec)
                cost, success = float(r @ r), True
            solutions.append((cost, vec, success))
        successful = [s for s in solutions if s[2]]
        return min(successful or solutions, key=lambda s: s[0])

    best_cost, best, success = optimize([x0, np.full(len(names), 0.25), np.full(len(names), 0.75)])
    rows, estimates = [], {}
    inconsistent = False
    for i, name in enumerate(names):
        cache = {}

        def profile(coordinate, cache=cache, i=i):
            key = round(float(coordinate), 14)
            if key not in cache:
                starts = [best]
                if cache:
                    nearest = cache[min(cache, key=lambda k: abs(k - key))][1]
                    if not np.allclose(nearest, best, atol=1e-7):
                        starts.append(nearest)
                cache[key] = optimize(starts, {i: float(coordinate)})
            return cache[key][0] - best_cost

        grid = sorted(
            set(np.linspace(0, 1, profile_points))
            | {float(best[i]), max(0.0, float(best[i]) - 0.01), min(1.0, float(best[i]) + 0.01)}
        )
        delta = np.array([profile(z) for z in grid])
        valid = success and all(sol[2] for sol in cache.values())
        reason, status, interval, value = "", "NOT IDENTIFIABLE", None, None
        if not valid:
            status, reason = (
                "PROFILE FAILED",
                "Optimizer/profile budget or convergence failed; no interval or estimate",
            )
        elif delta.min() < -max(1e-3, abs(best_cost) * 1e-6):
            inconsistent = True
            status, reason = "PROFILE FAILED", "Profile found a better optimum; increase multistart search"
        elif np.ptp(delta) <= flat_tolerance:
            reason = "Profile is flat over supplied search bounds; data cannot separate this parameter"
        elif (
            0.01 < best[i] < 0.99 and max(profile(best[i] - 0.01), profile(best[i] + 0.01)) <= flat_tolerance
        ):
            reason = "Profile has a flat minimum over a 0.02 search-coordinate neighborhood; no unique point supported at this resolution"
        elif min(best[i], 1 - best[i]) < 1e-4:
            reason = "Optimum lies at a search boundary; regular asymptotic interval is unsupported"
        elif delta[0] <= cutoff or delta[-1] <= cutoff:
            reason = "Profile does not cross the cutoff on both sides before the search bounds; expand bounds or collect data"
        else:
            accepted = np.flatnonzero(delta <= cutoff)
            if not len(accepted) or np.any(np.diff(accepted) > 1):
                reason = "Disconnected/multimodal profile region; no single estimate or interval reported"
            else:
                first, last = int(accepted[0]), int(accepted[-1])
                left = brentq(lambda z: profile(z) - cutoff, grid[first - 1], grid[first], xtol=1e-5)
                right = brentq(lambda z: profile(z) - cutoff, grid[last], grid[last + 1], xtol=1e-5)
                # New crossing evaluations must also converge and not discover a better optimum.
                if any(
                    not sol[2] or sol[0] < best_cost - max(1e-3, abs(best_cost) * 1e-6)
                    for sol in cache.values()
                ):
                    status, reason = "PROFILE FAILED", "Crossing refinement failed or found a better optimum"
                    inconsistent = True
                else:
                    status, reason = (
                        "IDENTIFIABLE",
                        "Connected two-sided profile within supplied bounds, conditional on specified assumptions",
                    )
                    value = specs[i].decode(best[i])
                    interval = (specs[i].decode(left), specs[i].decode(right))
        estimates[name] = ParameterEstimate(value, interval, runs[0].model.params[name].unit, status, reason)
        rows.extend(
            {
                "parameter": name,
                "value": specs[i].decode(z),
                "delta_deviance": cost - best_cost,
                "converged": ok,
            }
            for z, (cost, _, ok) in sorted(cache.items())
        )
    if inconsistent:
        estimates = {
            name: replace(
                e,
                value=None,
                interval=None,
                status="PROFILE FAILED",
                reason="Profile search invalidated the common optimum; estimates withheld",
            )
            for name, e in estimates.items()
        }
    values = decode(best)
    predictions, metrics, provenance, total_nll = [], [], [], 0.0
    for run in runs:
        predicted, trajectory = predict_run(run, values)
        frame = run.observations.copy()
        frame["run_id"], frame["predicted"] = run.run_id, predicted
        if errors.kind == "log-normal":
            frame["log_predicted"] = trajectory.attrs["log_predictions"]
        frame["split"], frame["origin"] = "in-sample", run.origin
        predictions.append(frame)
        total_nll += errors.nll(
            frame.value.to_numpy(), predicted, frame.observable, frame.get("log_predicted")
        )
        metrics.extend(_metrics(frame, "in-sample", errors))
        provenance.append(
            {
                "run_id": run.run_id,
                "origin": run.origin,
                "input_sha256": hashlib.sha256(run.observations.to_csv(index=False).encode()).hexdigest(),
                "kind": run.model.kind,
                "light": run.model.light,
                "temperature_c": run.model.temperature_c,
                "diurnal": run.model.diurnal,
                "conditions": asdict(run.model.conditions),
                "states": run.model.states,
                "state_units": run.model.state_units,
                "initial_state": run.initial_state,
                "parameters_before_fitting": [
                    {"parameter": name, **asdict(record)} for name, record in run.model.params.items()
                ],
            }
        )
    return JointFitResult(
        estimates,
        pd.DataFrame(rows),
        pd.concat(predictions, ignore_index=True),
        pd.DataFrame(metrics),
        success,
        total_nll,
        confidence,
        cutoff,
        dict(search),
        errors,
        tuple(provenance),
        flat_tolerance,
    )


def _metrics(frame, split, errors):
    rows = []
    for observable, data in frame.groupby("observable", sort=False):
        residual = data.predicted.to_numpy() - data.value.to_numpy()
        rows.append(
            {
                "run_id": data.run_id.iloc[0],
                "observable": observable,
                "split": split,
                "origin": data.origin.iloc[0],
                "n": len(data),
                "unit": data.unit.iloc[0],
                "rmse": float(np.sqrt(np.mean(residual**2))),
                "mae": float(np.mean(np.abs(residual))),
                "nll": errors.nll(
                    data.value.to_numpy(),
                    data.predicted.to_numpy(),
                    data.observable,
                    data.get("log_predicted"),
                ),
            }
        )
    return rows


@dataclass(frozen=True)
class CrossValidationResult:
    folds: pd.DataFrame
    metrics: pd.DataFrame
    predictions: pd.DataFrame
    method: str = "Leave-one-whole-run-out; refit and reprofile training runs only"


def leave_one_run_out(runs, search, errors, **fit_options):
    runs = tuple(runs)
    if len(runs) < 2:
        raise ValueError("Leave-one-run-out requires at least two independent culture runs")
    _validate_problem(runs, search, errors)
    folds, metrics, predictions = [], [], []
    for held_out in runs:
        training = [r for r in runs if r.run_id != held_out.run_id]
        try:
            result = fit_joint(training, search, errors, **fit_options)
        except (ValueError, RuntimeError) as exc:
            folds.append({"held_out": held_out.run_id, "status": "TRAINING FAILED", "reason": str(exc)})
            continue
        if not result.supported:
            folds.append(
                {
                    "held_out": held_out.run_id,
                    "status": "PROFILE FAILED"
                    if any(e.status == "PROFILE FAILED" for e in result.estimates.values())
                    else "NOT IDENTIFIABLE",
                    "reason": "; ".join(f"{name}: {e.reason}" for name, e in result.estimates.items()),
                }
            )
            continue
        frame = held_out.observations.copy()
        predicted, trajectory = predict_run(held_out, result.values())
        frame["predicted"] = predicted
        if errors.kind == "log-normal":
            frame["log_predicted"] = trajectory.attrs["log_predictions"]
        frame["run_id"], frame["origin"], frame["split"] = held_out.run_id, held_out.origin, "held-out"
        predictions.append(frame)
        metrics.extend(
            {**row, "held_out_fold": held_out.run_id} for row in _metrics(frame, "held-out", errors)
        )
        train = result.metrics.copy()
        train["held_out_fold"] = held_out.run_id
        metrics.extend(train.to_dict("records"))
        folds.append(
            {
                "held_out": held_out.run_id,
                "status": "SCORED",
                "reason": "Training profiles supported all fitted parameters",
            }
        )
    return CrossValidationResult(
        pd.DataFrame(folds),
        pd.DataFrame(metrics),
        pd.concat(predictions, ignore_index=True) if predictions else pd.DataFrame(),
    )
