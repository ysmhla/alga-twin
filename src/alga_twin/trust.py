"""Transparent diagnostics for sensitivity and out-of-calibration scenarios.

These checks are heuristics and local sensitivity measures, NOT quantified
predictive uncertainty, statistical parameter confidence, or independent
validation.  They are intended to make limitations visible.
"""

from __future__ import annotations

from dataclasses import replace

import pandas as pd

from .model import Conditions, Parameters, simulate

_SENSITIVE_PARAMETERS = (
    "mu_max_day",
    "k_n_mg_L",
    "k_i_umol_m2_s",
    "biomass_yield_g_per_gN",
    "extinction_a0",
)


def local_sensitivity(
    conditions: Conditions, parameters: Parameters, *, days: float = 12.0, relative_step: float = 0.05
) -> pd.DataFrame:
    """Centered finite-difference elasticity of final biomass to fixed parameters.

    In particular this is NOT an identifiability diagnostic. Parameters that
    are zero at baseline have undefined log elasticity and are omitted.
    """
    if not (0 < days <= 365 and 0 < relative_step < 0.5):
        raise ValueError("days and relative_step outside supported bounds")
    base_final = float(simulate([0, days], conditions, parameters).biomass_g_L.iloc[-1])
    rows = []
    for name in _SENSITIVE_PARAMETERS:
        p0 = getattr(parameters, name)
        if p0 <= 0:
            continue
        lower = replace(parameters, **{name: p0 * (1 - relative_step)})
        upper = replace(parameters, **{name: p0 * (1 + relative_step)})
        y0 = float(simulate([0, days], conditions, lower).biomass_g_L.iloc[-1])
        y1 = float(simulate([0, days], conditions, upper).biomass_g_L.iloc[-1])
        sensitivity = (y1 - y0) / (2 * relative_step * base_final)
        rows.append(
            {
                "parameter": name,
                "elasticity": sensitivity,
                "absolute_elasticity": abs(sensitivity),
                "relative_step": relative_step,
            }
        )
    return pd.DataFrame(rows).sort_values("absolute_elasticity", ascending=False).reset_index(drop=True)


def scenario_warnings(
    calibrated_at: Conditions,
    proposed: Conditions,
    *,
    calibrated: bool,
    scenario_days: float,
    observed_days: float,
) -> list[str]:
    """Flag obvious departures from experiment conditions, without safety guarantees."""
    notes = []
    if not calibrated:
        return ["Model parameters have not been calibrated to an experimental dataset."]
    notes.append("A single-run calibration is not evidence of prediction accuracy under altered conditions.")
    for name, label in (
        ("incident_light_umol_m2_s", "Incident light"),
        ("nitrogen_initial_mg_L", "Initial nitrogen"),
        ("optical_path_m", "Optical path"),
    ):
        reference = getattr(calibrated_at, name)
        candidate = getattr(proposed, name)
        if reference == 0:
            changed = candidate != 0
        else:
            changed = abs(candidate / reference - 1) > 0.25
        if changed:
            notes.append(
                f"{label} differs by more than 25% from calibration conditions; extrapolation is unvalidated."
            )
    if scenario_days > observed_days * 1.25:
        notes.append("Prediction extends more than 25% beyond observed experiment duration.")
    return notes
