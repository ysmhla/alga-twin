"""Synthetic verification of model structure; no independent biological validation."""

from dataclasses import replace

import numpy as np
import pint
import pytest
from scipy.integrate import quad
from scipy.optimize import minimize_scalar

from alga_twin.demo import demo_model_parameters, demo_parameters
from alga_twin.model import Conditions, simulate
from alga_twin.models import (
    DroopModel,
    MonodModel,
    assert_state_units,
    ctmi,
    haldane,
    han_steady,
    han_to_haldane,
    simulate_model,
)
from alga_twin.optimum import (
    compensation_roots,
    optical_productivity,
    optimal_optical_depth,
    printed_eq9_depth,
)
from alga_twin.parameters import UNITS


@pytest.mark.parametrize("light", ["monod", "haldane", "han"])
@pytest.mark.parametrize("kind", ["monod", "droop"])
@pytest.mark.parametrize("loss", [0, 0.12])
def test_common_interface_conservation_and_nonnegativity(kind, light, loss):
    params = demo_model_parameters(kind, light, temperature=True, diurnal=True, loss_rate_day=loss)
    cls = MonodModel if kind == "monod" else DroopModel
    model = cls(params, Conditions(nitrogen_initial_mg_L=7), light=light, temperature_c=23, diurnal=True)
    initial = [0.1, 7] + ([0.09] if kind == "droop" else [])
    assert tuple(model.params) == tuple(params)
    assert_state_units(model)
    trajectory = simulate_model(model, np.linspace(0, 15, 101), initial)
    np.testing.assert_allclose(trajectory.total_n_mg_L, model.retained_nitrogen(initial), atol=5e-6)
    assert np.all(trajectory[list(model.states)].to_numpy() >= 0)
    assert np.max(np.diff(trajectory.N)) <= 1e-8
    assert np.min(np.diff(trajectory.removed_n_mg_L)) >= -1e-10
    if kind == "droop":
        assert trajectory.q.min() >= model.value("q_min") - 1e-8
        assert trajectory.q.max() <= model.value("q_max") + 1e-8
    if loss == 0:
        assert trajectory.removed_n_mg_L.max() == 0
    else:
        assert trajectory.removed_n_mg_L.iloc[-1] > 0


def test_baseline_adapter_reproduces_existing_simulator():
    p = demo_parameters()
    c = Conditions()
    t = np.linspace(0, 12, 50)
    old = simulate(t, c, p)
    new = simulate_model(MonodModel.from_baseline(p, c), t, [c.biomass_initial_g_L, c.nitrogen_initial_mg_L])
    np.testing.assert_allclose(new.X, old.biomass_g_L, rtol=1e-7, atol=1e-9)
    np.testing.assert_allclose(new.N, old.nitrate_n_mg_L, rtol=1e-7, atol=1e-7)


@pytest.mark.parametrize("kind", ["monod", "droop"])
@pytest.mark.parametrize("light", ["monod", "haldane", "han"])
def test_dark_limit_and_nitrogen_accounting(kind, light):
    params = demo_model_parameters(kind, light, loss_rate_day=0.1)
    model = (MonodModel if kind == "monod" else DroopModel)(
        params, Conditions(incident_light_umol_m2_s=0), light=light
    )
    state = [0.1, 70] + ([0.09] if kind == "droop" else [])
    result = simulate_model(model, np.linspace(0, 2, 20), state)
    np.testing.assert_allclose(result.X, 0.1 * np.exp(-0.1 * result.time_day), rtol=1e-8)
    np.testing.assert_allclose(result.total_n_mg_L, model.retained_nitrogen(state), atol=1e-7)
    if kind == "monod":
        np.testing.assert_allclose(result.N, 70)
    else:
        # Uptake/storage can continue in darkness, bounded by q_max; not growth.
        assert result.N.iloc[-1] < 70
        assert result.q.iloc[-1] > 0.09


def test_droop_stored_n_supports_growth_without_external_n():
    model = DroopModel(demo_model_parameters("droop"), Conditions(nitrogen_initial_mg_L=0))
    result = simulate_model(model, np.linspace(0, 30, 80), [0.1, 0, 0.09])
    np.testing.assert_allclose(result.N, 0)
    np.testing.assert_allclose(result.X * result.q, 0.009, atol=1e-10)
    assert result.X.iloc[-1] > 0.1
    assert result.q.iloc[-1] == pytest.approx(model.value("q_min"), abs=2e-6)
    np.testing.assert_allclose(model.rhs(0, [0.1, 0, model.value("q_min")]), 0, atol=1e-14)


def test_droop_quota_monod_limit_is_equilibrium_only():
    model = DroopModel(demo_model_parameters("droop"), Conditions())
    g = model.potential_growth(0, 0.1)
    max_effective, k_effective = model.monod_limit(g)
    for nitrogen in [0, 0.1, 1, 10, 100, 1e8]:
        q = model.equilibrium_quota(nitrogen, g)
        assert model.uptake(nitrogen, q) - g * (q - model.value("q_min")) == pytest.approx(0, abs=1e-14)
        growth = g * (1 - model.value("q_min") / q)
        assert growth == pytest.approx(max_effective * nitrogen / (k_effective + nitrogen), abs=1e-14)
    # Quota transients do not collapse to Monod: stored nitrogen permits growth at N=0.
    assert model.rhs(0, [0.1, 0, 0.09])[0] > 0


@pytest.mark.parametrize("kind", ["monod", "droop"])
def test_saturating_transparent_exponential_limit(kind):
    p = demo_model_parameters(kind, extinction_a0=0, background_extinction_m_inv=0)
    model = (MonodModel if kind == "monod" else DroopModel)(p, Conditions(incident_light_umol_m2_s=1e12))
    t = np.linspace(0, 1, 20)
    g = model.potential_growth(0, 0.1)
    if kind == "droop":
        q = model.equilibrium_quota(1e12, g)
        mu = g * (1 - model.value("q_min") / q)
        initial = [0.1, 1e12, q]
    else:
        mu = g
        initial = [0.1, 1e12]
    result = simulate_model(model, t, initial)
    np.testing.assert_allclose(result.X, 0.1 * np.exp(mu * t), rtol=1e-8)


def test_haldane_units_optimum_slopes_and_han_equivalence():
    p = demo_model_parameters(light="haldane")
    m, io, a = (p[n].value for n in ("mu_max_day", "i_opt", "alpha"))
    assert haldane(0, m, io, a) == 0
    assert haldane(io, m, io, a) == pytest.approx(m)
    assert haldane(1e-7, m, io, a) / 1e-7 == pytest.approx(a, rel=1e-7)
    assert haldane(io * 1000, m, io, a) < haldane(io, m, io, a)
    assert (UNITS(p["alpha"].unit) * UNITS(p["i_opt"].unit)).to("1/day").magnitude == 1
    h = demo_model_parameters(light="han")
    args = [h[n].value for n in ("han_sigma", "han_tau", "han_damage", "han_repair", "han_k")]
    transformed = han_to_haldane(*args)
    irradiance = np.r_[0, np.geomspace(1e-6, 1e6, 60)]
    np.testing.assert_allclose(han_steady(irradiance, *args), haldane(irradiance, *transformed), rtol=1e-12)
    # A+B+C=1 at steady state, independent of growth parameterisation.
    sigma, tau, kd, kr, _ = args
    for i in [0, 20, 2000]:
        b_over_a = tau * sigma * i
        c_over_a = kd * sigma * i * b_over_a / kr
        A = 1 / (1 + b_over_a + c_over_a)
        B, C = b_over_a * A, c_over_a * A
        assert A + B + C == pytest.approx(1)
        np.testing.assert_allclose(
            [
                -sigma * i * A + B / tau,
                sigma * i * A - B / tau + kr * C - kd * sigma * i * B,
                -kr * C + kd * sigma * i * B,
            ],
            0,
            atol=1e-12,
        )


def test_temperature_and_diurnal_limits():
    assert ctmi(25, 5, 25, 35) == pytest.approx(1)
    for temperature in [-10, 5, 35, 60]:
        assert ctmi(temperature, 5, 25, 35) == 0
    factors = [ctmi(t, 5, 25, 35) for t in np.linspace(5, 35, 1001)]
    assert min(factors) >= 0 and max(factors) <= 1
    with pytest.raises(ValueError, match="CTMI"):
        ctmi(10, 0, 10, 30)
    p = demo_model_parameters(temperature=True, diurnal=True)
    m = MonodModel(p, Conditions(), temperature_c=25, diurnal=True)
    assert m.incident_light(0) == pytest.approx(0)
    assert m.incident_light(0.25) == pytest.approx(m.conditions.incident_light_umol_m2_s)
    assert m.incident_light(0.75) == 0
    assert m.incident_light(1.25) == pytest.approx(m.incident_light(0.25))
    area = quad(m.incident_light, 0, 1, points=[0.5])[0]
    assert area == pytest.approx(2 * m.conditions.incident_light_umol_m2_s * m.value("daylight_day") / np.pi)
    cold = MonodModel(p, Conditions(), temperature_c=5, diurnal=True)
    assert cold.potential_growth(0.25, 0.1) == 0


@pytest.mark.parametrize("s", [1, 0.5])
def test_spatial_light_integration_clear_limit_and_thick_limit(s):
    params = demo_model_parameters(light="haldane", extinction_exponent=s)
    model = MonodModel(params, Conditions(), light="haldane")
    assert (UNITS(params["extinction_a0"].unit) * UNITS("g_DW/liter") ** s * UNITS("meter")).dimensionless
    x = 0.2
    depth = model.conditions.optical_path_m * (
        model.value("background_extinction_m_inv") + model.value("extinction_a0") * x**s
    )
    ref = quad(lambda y: float(model.light_growth(model.incident_light(0) * np.exp(-y))), 0, depth)[0] / depth
    assert model.potential_growth(0, x) == pytest.approx(ref, rel=1e-10)
    thick = MonodModel(
        demo_model_parameters(light="haldane", extinction_a0=1e6), Conditions(), light="haldane"
    )
    depth = thick.conditions.optical_path_m * (
        thick.value("background_extinction_m_inv") + thick.value("extinction_a0") * x
    )
    integrated = quad(lambda y: float(thick.light_growth(thick.incident_light(0) * np.exp(-y))), 0, np.inf)[0]
    assert thick.potential_growth(0, x) == pytest.approx(integrated / depth, rel=1e-9)
    clear = MonodModel(
        demo_model_parameters(light="haldane", extinction_a0=0, background_extinction_m_inv=0),
        Conditions(),
        light="haldane",
    )
    assert clear.potential_growth(0, x) == pytest.approx(clear.light_growth(clear.incident_light(0)))


def synthetic_optics():
    p = demo_model_parameters(light="haldane")
    return [p[n].value for n in ("mu_max_day", "i_opt", "alpha")]


def test_eq9_valid_branch_matches_independent_numerical_optimum():
    m, io, a = synthetic_optics()
    r, incident = m / 10, io
    printed = printed_eq9_depth(incident, m, io, a, r)
    # Independently transcribe printed Eq. 9's applicable first branch, instead
    # of only comparing two functions that share a compensation-root helper.
    b = m - r + 2 * r * m / (a * io)
    discriminant = (m - r) * (m - r + 4 * r * m / (a * io))
    literal_eq9 = np.log((2 * incident * r * m / (a * io**2)) / (b - np.sqrt(discriminant)))
    optimum = optimal_optical_depth(incident, m, io, a, r)
    assert optimum.optical_depth == pytest.approx(literal_eq9, rel=1e-10)
    independent = minimize_scalar(
        lambda y: -optical_productivity(y, incident, m, io, a, r), bounds=(0, 20), method="bounded"
    )
    assert optimum.optical_depth == pytest.approx(printed, rel=1e-10)
    assert optimum.optical_depth == pytest.approx(independent.x, abs=2e-6)
    assert haldane(incident * np.exp(-printed), m, io, a) == pytest.approx(r)


def test_printed_eq9_high_light_branch_is_local_minimum_regression():
    # No published numerical values are hard-coded. Derived from this repo's DEMO fixture.
    m, io, a = synthetic_optics()
    r, incident = m / 10, 40 * io
    assert haldane(incident, m, io, a) < r
    printed = printed_eq9_depth(incident, m, io, a, r)
    optimum = optimal_optical_depth(incident, m, io, a, r)
    f = lambda y: optical_productivity(y, incident, m, io, a, r)
    assert f(printed) < f(printed - 0.01) and f(printed) < f(printed + 0.01)
    assert f(optimum.optical_depth) > f(optimum.optical_depth - 0.01)
    assert f(optimum.optical_depth) > f(optimum.optical_depth + 0.01)
    assert optimum.productivity_day_inv > 0 > f(printed)
    grid = np.linspace(0, 20, 2001)
    assert optimum.productivity_day_inv >= max(f(y) for y in grid) - 1e-10
    for root in compensation_roots(m, io, a, r):
        assert haldane(root, m, io, a) == pytest.approx(r)


def test_optimum_boundaries_and_no_finite_zero_respiration_optimum():
    m, io, a = synthetic_optics()
    for incident, r in [(0, m / 10), (io, m), (io, 2 * m), (io * 1e-5, m / 10), (0, 0), (io * 1e15, m / 10)]:
        result = optimal_optical_depth(incident, m, io, a, r)
        assert result.finite and result.optical_depth == 0 and result.productivity_day_inv == 0
    no_loss = optimal_optical_depth(io, m, io, a, 0)
    assert not no_loss.finite and np.isinf(no_loss.optical_depth)
    assert no_loss.productivity_day_inv > optical_productivity(5, io, m, io, a, 0)


def test_missing_or_wrong_basis_parameters_never_execute():
    params = demo_model_parameters("droop")
    for bad_record in [
        replace(params["q_min"], unit="g_N/g_C", basis="nitrogen_per_carbon"),
        replace(params["q_min"], value=None, status="NO_SPECIES_DATA", tier="LITERATURE"),
    ]:
        with pytest.raises(ValueError):
            DroopModel({**params, "q_min": bad_record}, Conditions())
    with pytest.raises(pint.DimensionalityError):
        (UNITS("g_DW/liter") * UNITS("g_N/g_C")).to("mg_N/liter")
    with pytest.raises(ValueError, match="extinction exponent"):
        DroopModel({}, Conditions())


@pytest.mark.parametrize("state", [[-1, 5, 0.09], [0.1, -1, 0.09], [0.1, 5, 0.001], [0.1, 5, 1], [0.1, 5]])
def test_invalid_initial_states(state):
    model = DroopModel(demo_model_parameters("droop"), Conditions())
    with pytest.raises(ValueError):
        simulate_model(model, [0, 1], state)


def test_new_rate_units_and_explicit_parameter_guards():
    p = demo_model_parameters("droop", "han", temperature=True, diurnal=True)
    quantity = lambda name: UNITS(p[name].unit)
    photons = UNITS("micromole/meter**2/second")
    assert (quantity("han_sigma") * photons * quantity("han_tau")).dimensionless
    assert (
        (quantity("han_damage") / quantity("han_repair"))
        * quantity("han_tau")
        * (quantity("han_sigma") * photons) ** 2
    ).dimensionless
    (quantity("han_k") * quantity("han_sigma") * photons).to("1/day")
    (quantity("rho_max") * UNITS("g_DW/liter")).to("mg_N/liter/day")
    (quantity("rho_max") / quantity("q_min")).to("1/day")
    (quantity("loss_rate_day") * quantity("q_min") * UNITS("g_DW/liter")).to("mg_N/liter/day")
    for key, change in [
        ("han_tau", {"value": -1}),
        ("q_max", {"value": 0.01}),
        ("t_opt", {"value": 10}),
        ("daylight_day", {"value": 2}),
        ("q_min", {"species": "other species"}),
    ]:
        with pytest.raises(ValueError):
            DroopModel(
                {**p, key: replace(p[key], **change)},
                Conditions(),
                light="han",
                temperature_c=25,
                diurnal=True,
            )
    model = DroopModel(p, Conditions(), light="han", temperature_c=25, diurnal=True)
    with pytest.raises(TypeError):
        model.params["q_min"] = p["q_max"]
