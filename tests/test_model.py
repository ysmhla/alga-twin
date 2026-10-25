from dataclasses import replace

import numpy as np
import pytest

from alga_twin.model import Conditions, Parameters, light_limitation, local_irradiance, simulate


def test_growth_and_mass_balance_without_loss():
    p = Parameters(loss_rate_day=0)
    c = Conditions()
    result = simulate(np.linspace(0, 14, 141), c, p)
    x = result.biomass_g_L.to_numpy()
    n = result.nitrate_n_mg_L.to_numpy()
    assert (x > 0).all() and (n >= 0).all()
    assert np.min(np.diff(x)) >= -1e-6
    assert np.max(np.diff(n)) <= 1e-6
    conserved = x + p.biomass_yield_g_per_gN * n / 1000
    np.testing.assert_allclose(conserved, np.full_like(conserved, conserved[0]), atol=2e-6)


def test_low_light_reduces_growth():
    c = Conditions()
    days = np.linspace(0, 4, 40)
    bright = simulate(days, replace(c,incident_light_umol_m2_s=250))
    dim = simulate(days, replace(c,incident_light_umol_m2_s=20))
    assert bright.biomass_g_L.iloc[-1] > dim.biomass_g_L.iloc[-1]
    assert light_limitation(1.0,c,Parameters()) < light_limitation(.1,c,Parameters())


def test_no_light_means_no_growth_for_default_no_loss():
    c = replace(Conditions(),incident_light_umol_m2_s=0)
    frame = simulate([0,2,4],c)
    np.testing.assert_allclose(frame.biomass_g_L, c.biomass_initial_g_L,atol=1e-9)
    np.testing.assert_allclose(frame.nitrate_n_mg_L,c.nitrogen_initial_mg_L,atol=1e-9)


def test_attenuation_monotone_with_depth():
    c,p=Conditions(),Parameters()
    values=local_irradiance(np.linspace(0,c.optical_path_m,25),0.5,c,p)
    assert np.all(np.diff(values)<=0)


@pytest.mark.parametrize("times", [[1,2], [0,0,1], [0,-1,2], [0,366], [0,float('nan')]])
def test_bad_time_grid_rejected(times):
    with pytest.raises(ValueError):
        simulate(times)


def test_invalid_conditions_rejected():
    with pytest.raises(ValueError):
        simulate([0,1],Conditions(nitrogen_initial_mg_L=-1))
