"""Constrained, deterministic fit of identifiable subset of Monod-light parameters.

We intentionally hold K_N, K_I, extinction and loss rate fixed. Single-run
biomass trajectories do NOT identify the full biological model.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

from .model import Conditions, Parameters, conditions_for_observations, simulate


@dataclass(frozen=True)
class FitResult:
    parameters: Parameters
    fitted_names: tuple[str, ...]
    rmse_biomass_g_L: float
    rmse_nitrogen_mg_L: float | None
    success: bool
    message: str
    warnings: tuple[str, ...]
    prediction: pd.DataFrame


def fit_experiment(
    observations: pd.DataFrame,
    base_conditions: Conditions,
    fixed_parameters: Parameters | None = None,
    *,
    include_yield: bool = True,
) -> FitResult:
    """Fit mu_max; additionally fit yield when >=3 observed N points exist.

    Biomass and nitrogen residuals are scaled by *assumed* measurement noises,
    not experimental variance estimates. Fit metrics are in-sample, not
    estimates of predictive accuracy.
    """
    if fixed_parameters is None:
        raise ValueError("Supply explicit fixed parameters and their provenance")
    p = fixed_parameters
    p.validate()
    c = conditions_for_observations(observations, base_conditions)
    if c.nitrogen_initial_mg_L <= 0 or c.incident_light_umol_m2_s <= 0:
        raise ValueError(
            "Growth parameters cannot be identified without both initial nitrogen and incident light"
        )
    t = observations["time_day"].to_numpy(dtype=float)
    biomass = observations["biomass_g_L"].to_numpy(dtype=float)
    n_obs = observations["nitrate_n_mg_L"].to_numpy(dtype=float)
    include_nitrogen = include_yield and np.isfinite(n_obs).sum() >= 3
    fitted = ("mu_max_day", "biomass_yield_g_per_gN") if include_nitrogen else ("mu_max_day",)
    warnings = [
        "Only selected parameters were fitted; K_N, K_I, attenuation and loss rate remain fixed assumptions.",
        "A single cultivation run cannot establish reliable condition-transfer accuracy.",
        "In-sample fit quality is not independent experimental validation.",
    ]
    if not include_nitrogen:
        warnings.append(
            "Yield was held fixed: fewer than three nutrient observations or yield fitting disabled."
        )
    if len(observations) < 6:
        warnings.append("Few timepoints: estimated growth rate may be unstable.")
    if np.ptp(biomass) < 0.015:
        warnings.append("Very small biomass change: fitted growth rate may be weakly informative.")

    # Assumed observation noise floor, stated explicitly in user-facing reports.
    sigma_x = max(0.005, float(np.max(biomass) - np.min(biomass)) * 0.02)
    sigma_n = max(1.0, float(np.nanmax(n_obs) - np.nanmin(n_obs)) * 0.02) if np.isfinite(n_obs).any() else 1.0
    n_mask = np.isfinite(n_obs)

    def to_params(vec: np.ndarray) -> Parameters:
        if include_nitrogen:
            return replace(p, mu_max_day=float(vec[0]), biomass_yield_g_per_gN=float(vec[1]))
        return replace(p, mu_max_day=float(vec[0]))

    def residual(vec: np.ndarray) -> np.ndarray:
        pred = simulate(t, c, to_params(vec))
        res_x = (pred["biomass_g_L"].to_numpy() - biomass) / sigma_x
        if not include_nitrogen:
            return res_x
        res_n = (pred["nitrate_n_mg_L"].to_numpy()[n_mask] - n_obs[n_mask]) / sigma_n
        return np.concatenate((res_x, res_n))

    starts = [0.25, 0.65, 1.1, 1.8] if not include_nitrogen else [0.4, 1.0, 1.6]
    upper = [3.0, 25.0] if include_nitrogen else [3.0]
    lower = [0.01, 1.0] if include_nitrogen else [0.01]
    fits = []
    for initial_mu in starts:
        initial = (
            [initial_mu, float(np.clip(p.biomass_yield_g_per_gN, 1, 25))]
            if include_nitrogen
            else [initial_mu]
        )
        fitted_solution = least_squares(
            residual,
            initial,
            bounds=(lower, upper),
            max_nfev=180,
            xtol=1e-8,
            ftol=1e-8,
            gtol=1e-8,
        )
        fits.append(fitted_solution)
    best = min(fits, key=lambda item: float(np.dot(item.fun, item.fun)))
    parameters = to_params(best.x)
    pred = simulate(t, c, parameters)
    rmse_x = float(np.sqrt(np.mean((pred["biomass_g_L"].to_numpy() - biomass) ** 2)))
    rmse_n = (
        float(np.sqrt(np.mean((pred["nitrate_n_mg_L"].to_numpy()[n_mask] - n_obs[n_mask]) ** 2)))
        if include_nitrogen
        else None
    )
    if any(np.isclose(best.x, lower, atol=1e-3)) or any(np.isclose(best.x, upper, atol=1e-3)):
        warnings.append("One or more fitted parameters sit near optimisation bounds.")
    if len(best.x) > 1:
        singular = np.linalg.svd(best.jac, compute_uv=False)
        if singular[-1] < singular[0] * 1e-4:
            warnings.append("Local Jacobian is ill-conditioned; parameter estimates may not be unique.")
    return FitResult(
        parameters, fitted, rmse_x, rmse_n, bool(best.success), str(best.message), tuple(warnings), pred
    )
