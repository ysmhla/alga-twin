"""Single-run baseline adapter with the same profile gate as joint calibration."""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
import pandas as pd

from .calibration import CalibrationRun, ErrorModel, FitParameter, JointFitResult, fit_joint
from .model import Conditions, Parameters, conditions_for_observations, simulate
from .models import MonodModel


@dataclass(frozen=True)
class FitResult:
    parameters: Parameters | None
    fitted_names: tuple[str, ...]
    rmse_biomass_g_L: float
    rmse_nitrogen_mg_L: float | None
    success: bool
    message: str
    warnings: tuple[str, ...]
    prediction: pd.DataFrame
    inference: JointFitResult


def fit_experiment(
    observations: pd.DataFrame,
    base_conditions: Conditions,
    fixed_parameters: Parameters | None = None,
    *,
    include_yield: bool = True,
    errors: ErrorModel | None = None,
    search: dict[str, FitParameter] | None = None,
) -> FitResult:
    """Fit baseline mu and optionally yield, with reoptimized profiles before reporting.

    Search/noise defaults are available ONLY for explicitly opted-in DEMO input.
    Initial observations condition the initial state and are excluded from fitting.
    Research calls require explicit search bounds and fixed noise scales.
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
    if observations.time_day.iloc[0] != 0:
        raise ValueError("Baseline input time must begin at zero")
    include_nitrogen = include_yield and np.isfinite(observations.nitrate_n_mg_L).sum() >= 3
    names = ("mu_max_day", "biomass_yield_g_per_gN") if include_nitrogen else ("mu_max_day",)
    if p.tier != "DEMO" and (errors is None or search is None):
        raise ValueError("Research fitting requires explicit noise scales and search bounds")
    notes = [
        "Only selected parameters were fitted; K_N, K_I, attenuation and loss remain fixed assumptions.",
        "Profiles are conditional on fixed parameters, initial states and specified measurement SDs.",
        "A single cultivation run cannot establish reliable condition-transfer accuracy.",
        "In-sample fit quality is not independent experimental validation.",
        "Initial X/N observations set initial conditions and are excluded from the likelihood.",
    ]
    if search is None:
        search = {"mu_max_day": FitParameter(0.01, 3, float(np.clip(p.mu_max_day, 0.01, 3)))}
        if include_nitrogen:
            search["biomass_yield_g_per_gN"] = FitParameter(
                1, 25, float(np.clip(p.biomass_yield_g_per_gN, 1, 25))
            )
        notes.append("DEMO search bounds are algorithm assumptions, not verified physiological ranges.")
    if set(search) != set(names):
        raise ValueError(
            f"The baseline adapter fits exactly {names}; use fit_joint for other parameters/models"
        )
    if errors is None:
        scales = {"X": (0.005, "g_DW/liter")}
        if include_nitrogen:
            scales["N"] = (1.0, "mg_N/liter")
        errors = ErrorModel("additive", scales)
        notes.append(
            "DEMO noise SD assumptions: X=0.005 g DW/L; N=1 mg N/L when used; not estimated from replicates."
        )
    if not include_nitrogen:
        notes.append("Yield held fixed; fewer than three nutrient observations or yield fitting disabled.")
    records = []
    for observable, column, unit in [
        ("X", "biomass_g_L", "g_DW/liter"),
        ("N", "nitrate_n_mg_L", "mg_N/liter"),
    ]:
        if observable == "N" and not include_nitrogen:
            continue
        for t, value in zip(observations.time_day, observations[column], strict=True):
            if t > 0 and np.isfinite(value):
                records.append(
                    {
                        "time_day": t,
                        "observable": observable,
                        "value": value,
                        "unit": unit,
                        "replicate": "single",
                    }
                )
    model = MonodModel.from_baseline(p, c)
    # DEMO names the parameter tier, not the origin of uploaded measurements.
    # This adapter makes no origin assertion for user CSV: joint callers supply it explicitly.
    run = CalibrationRun(
        "baseline-run",
        model,
        (c.biomass_initial_g_L, c.nitrogen_initial_mg_L),
        pd.DataFrame(records),
        "SYNTHETIC" if observations.attrs.get("origin") == "SYNTHETIC" else "UNSPECIFIED",
    )
    inference = fit_joint([run], search, errors, profile_points=7)
    parameters = None
    if inference.supported:
        parameters = replace(p, **inference.values())
        prediction = simulate(observations.time_day.to_numpy(), c, parameters)
        message = "Optimizer converged and selected profiles passed the conditional identifiability gate"
    else:
        message = "Calibration estimates withheld: " + "; ".join(
            f"{n}: {e.reason}" for n, e in inference.estimates.items()
        )
        notes.append(message)
        # A descriptive training curve is retained; no unsupported parameter vector escapes.
        frame = inference.predictions.pivot(index="time_day", columns="observable", values="predicted")
        frame = frame.reindex(observations.time_day)
        frame.loc[0, "X"], frame.loc[0, "N"] = c.biomass_initial_g_L, c.nitrogen_initial_mg_L
        if "N" not in frame:
            frame["N"] = np.nan
        prediction = frame.reset_index().rename(columns={"X": "biomass_g_L", "N": "nitrate_n_mg_L"})
    metrics = inference.metrics.set_index("observable")
    return FitResult(
        parameters,
        names,
        float(metrics.loc["X", "rmse"]),
        float(metrics.loc["N", "rmse"]) if include_nitrogen else None,
        inference.supported,
        message,
        tuple(notes),
        prediction,
        inference,
    )
