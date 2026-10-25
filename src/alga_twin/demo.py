"""Clearly synthetic, seeded measurements used solely for an interactive demo."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .model import Conditions, Parameters, simulate

DEMO_CONDITIONS = Conditions(
    biomass_initial_g_L=0.10,
    nitrogen_initial_mg_L=70.0,
    incident_light_umol_m2_s=180.0,
    optical_path_m=0.05,
)
DEMO_PARAMETERS = Parameters(mu_max_day=0.90, biomass_yield_g_per_gN=8.0)


def synthetic_experiment(seed: int = 42) -> pd.DataFrame:
    time = np.linspace(0, 12, 13)
    ideal = simulate(time, DEMO_CONDITIONS, DEMO_PARAMETERS)
    rng = np.random.default_rng(seed)
    observed = ideal.copy()
    observed["biomass_g_L"] = np.maximum(
        ideal["biomass_g_L"] + rng.normal(0.0, 0.004, len(time)), 0.001
    )
    observed["nitrate_n_mg_L"] = np.maximum(
        ideal["nitrate_n_mg_L"] + rng.normal(0.0, 1.2, len(time)), 0.0
    )
    # First observations are the exact initial conditions for a stable teaching example.
    observed.loc[0, "biomass_g_L"] = DEMO_CONDITIONS.biomass_initial_g_L
    observed.loc[0, "nitrate_n_mg_L"] = DEMO_CONDITIONS.nitrogen_initial_mg_L
    return observed
