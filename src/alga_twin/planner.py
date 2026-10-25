"""Bounded exploratory grid, with three-objective non-dominance tagging.

Not a laboratory recommendation. The numerical model is still illustrative
until calibrated and independently validated. A Pareto point is not a proven
optimum: it is non-dominated only among the sampled scenarios and metrics.
"""
from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd

from .model import Conditions, Parameters, simulate


def scenario_grid(
    conditions: Conditions,
    parameters: Parameters,
    *, days: float,
    max_light: float = 450.0,
    max_nitrogen: float = 150.0,
    steps: int = 7,
) -> pd.DataFrame:
    """Explore supplied discrete light/nitrogen budgets and identify sampled Pareto candidates.

    Objectives: maximize final dry biomass, minimize incident surface irradiance,
    minimize starting available nitrogen. No energy/cost model is assumed.
    """
    conditions.validate()
    parameters.validate()
    if not 1 <= days <= 60:
        raise ValueError("Planning horizon must be 1–60 days")
    if not 3 <= steps <= 12:
        raise ValueError("Grid steps must be 3–12")
    if not 0 < max_light <= 1200 or not 0 < max_nitrogen <= 10000:
        raise ValueError("Scenario upper bounds must be positive and within limits")
    light_values = np.linspace(0.0, max_light, steps)
    nitrogen_values = np.linspace(0.0, max_nitrogen, steps)
    rows = []
    for light in light_values:
        for nitrogen in nitrogen_values:
            scenario = replace(
                conditions,
                incident_light_umol_m2_s=float(light),
                nitrogen_initial_mg_L=float(nitrogen),
            )
            result = simulate([0, float(days)], scenario, parameters)
            final = float(result.biomass_g_L.iloc[-1])
            rows.append({
                "light_umol_m2_s": float(light),
                "initial_nitrogen_mg_L": float(nitrogen),
                "final_biomass_g_L": final,
                "biomass_gain_g_L": final - conditions.biomass_initial_g_L,
                "average_productivity_g_L_day": (final - conditions.biomass_initial_g_L) / days,
            })
    result = pd.DataFrame(rows)
    gains = result["final_biomass_g_L"].to_numpy()
    lights = result["light_umol_m2_s"].to_numpy()
    nitrogen = result["initial_nitrogen_mg_L"].to_numpy()
    dominated = np.zeros(len(result), dtype=bool)
    for idx in range(len(result)):
        better = (gains >= gains[idx] - 1e-8) & (lights <= lights[idx]) & (nitrogen <= nitrogen[idx])
        strictly = (gains > gains[idx] + 1e-8) | (lights < lights[idx]) | (nitrogen < nitrogen[idx])
        # Floating-point differences smaller than 1e-8 are not substantive biomass improvements.
        dominated[idx] = bool(np.any(better & strictly))
    result["sampled_pareto_candidate"] = ~dominated
    return result
