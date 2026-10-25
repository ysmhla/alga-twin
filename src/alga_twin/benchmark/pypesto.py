"""Run real pyPESTO optimization/profiles against the exported native PEtab model.

The established AlgaTwin gate controls reported estimates. pyPESTO is an
independent profile/optimum cross-check, not an alternative path around it.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd
import pypesto
from pypesto import optimize, profile

from ..calibration import predict_run


@dataclass(frozen=True)
class ProfileCrosscheck:
    profiles: pd.DataFrame
    best_nll: float
    version: str


def objective_value(runs, search, errors, coordinates):
    values = {name: p.decode(z) for (name, p), z in zip(search.items(), coordinates, strict=True)}
    total = 0.0
    for run in runs:
        predicted, trajectory = predict_run(run, values)
        total += errors.nll(
            run.observations.value.to_numpy(),
            predicted,
            run.observations.observable,
            trajectory.attrs["log_predictions"],
        )
    return total


def run_profiles(runs, search, errors) -> ProfileCrosscheck:
    names = list(search)
    initial = [spec.encode(spec.initial) for spec in search.values()]
    # Deliberately deterministic start points, as in the native profile gate.
    objective = pypesto.Objective(fun=lambda x: objective_value(runs, search, errors, x), x_names=names)
    problem = pypesto.Problem(
        objective=objective,
        lb=np.zeros(len(names)),
        ub=np.ones(len(names)),
        x_names=names,
        x_guesses=[initial, [0.25] * len(names), [0.75] * len(names)],
    )
    optimizer = optimize.ScipyOptimizer(method="Powell", options={"maxiter": 120, "xtol": 1e-6, "ftol": 1e-8})
    result = optimize.minimize(
        problem,
        optimizer=optimizer,
        n_starts=3,
        progress_bar=False,
        options=optimize.OptimizeOptions(allow_failed_starts=False),
        filename=None,
    )
    best = result.optimize_result.list[0]
    if not np.isfinite(best.fval) or best.exitflag != 0:
        raise RuntimeError("pyPESTO optimizer did not converge; no profile cross-check claimed")
    options = profile.ProfileOptions(
        default_step_size_absolute=0.1,
        default_step_size_relative=0,
        min_step_size_absolute=0.05,
        min_step_size_relative=0,
        max_step_size_absolute=0.1,
        max_step_size_relative=0,
        whole_path=True,
    )
    result = profile.parameter_profile(
        problem,
        result,
        optimizer,
        profile_options=options,
        next_guess_method="fixed_step",
        progress_bar=False,
        filename=None,
    )
    rows = []
    for i, (name, spec) in enumerate(search.items()):
        curve = result.profile_result.get_profiler_result(i_par=i)
        if curve is None or not np.all(np.isfinite(curve.fval_path)):
            raise RuntimeError("pyPESTO profile is missing/non-finite")
        flags = np.asarray(curve.exitflag_path, dtype=float)
        if np.any(flags[np.isfinite(flags)] != 0):
            raise RuntimeError("pyPESTO profile contains a failed Powell optimization")
        coordinate = curve.x_path[i]
        if coordinate.min() > 1e-6 or coordinate.max() < 1 - 1e-6:
            raise RuntimeError("pyPESTO profile did not cover the supplied bounds")
        for z, nll in zip(coordinate, curve.fval_path, strict=True):
            rows.append(
                {
                    "parameter": name,
                    "value": spec.decode(z),
                    "coordinate": float(z),
                    "nll": float(nll),
                    "delta_deviance": float(2 * (nll - best.fval)),
                    "engine": f"pyPESTO {pypesto.__version__}",
                }
            )
    return ProfileCrosscheck(
        pd.DataFrame(rows).sort_values(["parameter", "value"]), float(best.fval), pypesto.__version__
    )
