import numpy as np

from alga_twin.demo import DEMO_CONDITIONS, DEMO_PARAMETERS, synthetic_experiment
from alga_twin.fitting import fit_experiment
from alga_twin.model import simulate


def test_fit_recovery_on_clean_synthetic_data():
    observations = simulate(np.linspace(0, 12, 13), DEMO_CONDITIONS, DEMO_PARAMETERS)
    result = fit_experiment(observations, DEMO_CONDITIONS, DEMO_PARAMETERS)
    assert result.success
    assert set(result.fitted_names) == {"mu_max_day", "biomass_yield_g_per_gN"}
    assert abs(result.parameters.mu_max_day - DEMO_PARAMETERS.mu_max_day) < 0.015
    assert abs(result.parameters.biomass_yield_g_per_gN - DEMO_PARAMETERS.biomass_yield_g_per_gN) < 0.15
    assert result.rmse_biomass_g_L < 0.005


def test_biomass_only_fit_keeps_yield_fixed():
    observations = synthetic_experiment()
    observations["nitrate_n_mg_L"] = np.nan
    result = fit_experiment(observations, DEMO_CONDITIONS, DEMO_PARAMETERS)
    assert result.success
    assert result.fitted_names == ("mu_max_day",)
    assert result.rmse_nitrogen_mg_L is None


def test_no_fitted_confidence_claims():
    result = fit_experiment(synthetic_experiment(), DEMO_CONDITIONS, DEMO_PARAMETERS)
    assert any("in-sample" in msg.lower() for msg in result.warnings)


def test_fit_rejects_identifiability_failure_no_light():
    from dataclasses import replace

    import pytest

    observations = synthetic_experiment()
    with pytest.raises(ValueError, match="cannot be identified"):
        fit_experiment(observations, replace(DEMO_CONDITIONS, incident_light_umol_m2_s=0), DEMO_PARAMETERS)


def test_legacy_adapter_withholds_points_on_flat_data():
    import pandas as pd

    from alga_twin.calibration import ErrorModel

    # Large explicit assay errors leave the profile uninformative.
    observations = simulate(np.linspace(0, 5, 8), DEMO_CONDITIONS, DEMO_PARAMETERS)
    result = fit_experiment(
        observations,
        DEMO_CONDITIONS,
        DEMO_PARAMETERS,
        errors=ErrorModel("additive", {"X": (100, "g_DW/liter"), "N": (1000, "mg_N/liter")}),
    )
    assert not result.success and result.parameters is None
    assert all(e.value is None for e in result.inference.estimates.values())
    assert isinstance(result.prediction, pd.DataFrame)
