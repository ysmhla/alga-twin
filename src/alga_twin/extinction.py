"""Estimate effective extinction from user-supplied transmission and dry biomass.

These are in-sample optical estimates, not literature priors or biological validation.
No images, plots or publications are digitised by this module.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

from .parameters import SPECIES, UNITS, Parameter, coefficient_unit


@dataclass(frozen=True)
class ExtinctionFit:
    a0: Parameter
    a1: Parameter
    exponent: Parameter
    residuals: pd.DataFrame
    r_squared: float | None
    method: str
    biomass_domain_g_dw_L: tuple[float, float]


def fit_extinction(
    observations: pd.DataFrame,
    *,
    biomass_unit: str,
    path_unit: str,
    light_unit: str,
    sublinear: bool = False,
    species: str = SPECIES,
) -> ExtinctionFit:
    """Fit epsilon = a0*X**s+a1 in m^-1, X in g DW/L; fit s only if requested.

    Required columns: biomass, incident, transmitted, path. Include a medium
    blank and >=3 distinct positive dry biomasses (>=5 for free s). A measurement
    with transmitted > incident, zero signal, or no finite path is rejected.
    Units must be selected explicitly; OD and carbon cannot be mistaken for DW.
    """
    required = ["biomass", "incident", "transmitted", "path"]
    if not set(required).issubset(observations.columns):
        raise ValueError("Required columns: biomass, incident, transmitted, path")
    raw = observations[required].to_numpy(dtype=float)
    if not np.isfinite(raw).all():
        raise ValueError("Measurements must be finite, without missing values")
    x = (raw[:, 0] * UNITS(biomass_unit)).to("g_DW/liter").magnitude
    path = (raw[:, 3] * UNITS(path_unit)).to("meter").magnitude
    incident = (raw[:, 1] * UNITS(light_unit)).to("micromole/meter**2/second").magnitude
    transmitted = (raw[:, 2] * UNITS(light_unit)).to("micromole/meter**2/second").magnitude
    if np.any(x < 0) or np.any(path <= 0) or np.any(transmitted <= 0) or np.any(incident <= 0):
        raise ValueError("Dry biomass must be nonnegative; path and light signals must be positive")
    if np.any(transmitted > incident):
        raise ValueError("Transmitted light exceeds incident light; check blank, sensor and geometry")
    needed = 5 if sublinear else 3
    if not np.any(x == 0) or len(np.unique(x[x > 0])) < needed:
        raise ValueError(
            f"Include a medium blank (biomass=0) and >= {needed} distinct positive dry biomasses"
        )
    epsilon = np.log(incident / transmitted) / path
    if np.ptp(epsilon) < 1e-10:
        raise ValueError("No measurable extinction change: absorption coefficient/exponent not identifiable")
    blank = float(np.mean(epsilon[x == 0]))
    scale = float(x.max())
    u = x / scale

    def prediction(v):
        s = v[2] if sublinear else 1.0
        return v[0] * u**s + v[1]

    amplitude = max(float(epsilon.max() - blank), 1e-12)
    initial = [amplitude, max(blank, 0)] + ([0.5] if sublinear else [])
    lower = [0, 0] + ([1e-4] if sublinear else [])
    upper = [np.inf, np.inf] + ([1.0] if sublinear else [])
    fit = least_squares(
        lambda v: prediction(v) - epsilon,
        initial,
        bounds=(lower, upper),
        ftol=1e-12,
        xtol=1e-12,
        gtol=1e-12,
        max_nfev=2000,
    )
    singular = np.linalg.svd(fit.jac, compute_uv=False)
    if not fit.success or singular[-1] <= singular[0] * 1e-8 or fit.x[0] < 1e-8:
        raise ValueError("Optical fit is not identifiable; add informative transmission measurements")
    s = float(fit.x[2]) if sublinear else 1.0
    a0 = float(fit.x[0] / scale**s)
    a1 = float(fit.x[1])
    fitted = prediction(fit.x)
    residual = epsilon - fitted
    sst = float(np.sum((epsilon - np.mean(epsilon)) ** 2))
    method = (
        "Constrained nonlinear least squares on log-transmission/path; free s"
        if sublinear
        else ("Constrained least squares on log-transmission/path; s fixed at 1")
    )
    context = "User measurements; assumes matched sensor spectrum/geometry and medium blank; " + method

    def record(value, unit, basis):
        return Parameter(
            value,
            None,
            None,
            unit,
            None,
            "UNVERIFIED",
            species,
            context,
            basis,
            "MEASURED",
            "user_measured_estimate",
        )

    return ExtinctionFit(
        record(a0, coefficient_unit(s), "dry_weight"),
        record(a1, "1/meter", "medium"),
        record(s, "dimensionless", "dimensionless"),
        pd.DataFrame(
            {
                "biomass_g_dw_L": x,
                "observed_epsilon_m_inv": epsilon,
                "fitted_epsilon_m_inv": fitted,
                "residual_m_inv": residual,
            }
        ),
        None if sst == 0 else 1 - float(residual @ residual) / sst,
        method,
        (float(x.min()), float(x.max())),
    )
