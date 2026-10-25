"""Synthetic numerical fixtures; no new empirical parameter ranges are asserted."""

from dataclasses import replace

import numpy as np
import pandas as pd
import pint
import pytest

from alga_twin.demo import demo_parameters
from alga_twin.extinction import fit_extinction
from alga_twin.model import Conditions, Parameters, light_limitation, local_irradiance, simulate
from alga_twin.parameters import (
    SPECIES,
    Parameter,
    c_minutissima_preset,
    coefficient_unit,
    convert_extinction,
    provenance_rows,
)


def optical_data(a0=4.0, a1=0.7, s=1.0):
    """Construct measurements from a declared synthetic optical law, not lab data."""
    x = np.array([0, 0.04, 0.1, 0.22, 0.43, 0.8, 1.2])
    path = np.linspace(0.03, 0.09, len(x))
    incident = np.linspace(100, 200, len(x))
    return pd.DataFrame(
        {
            "biomass": x,
            "incident": incident,
            "transmitted": incident * np.exp(-(a0 * x**s + a1) * path),
            "path": path,
        }
    )


def test_no_silent_biological_defaults():
    with pytest.raises(TypeError):
        Parameters()
    with pytest.raises(ValueError, match="explicit parameters"):
        simulate([0, 1])


def test_species_catalogue_does_not_transfer_or_invent_ranges():
    preset = c_minutissima_preset()
    assert all(record.species == SPECIES for record in preset.values())
    for name in (
        "extinction_a0",
        "background_extinction_m_inv",
        "carbon_fraction",
        "mu_max_day",
        "ctmi_t_min",
        "ctmi_t_opt",
        "ctmi_t_max",
    ):
        assert preset[name].value is None and preset[name].status == "NO_SPECIES_DATA"
    assert all(record.low is None and record.high is None for record in preset.values())
    assert preset["oxygen_k_m"].status == "UNVERIFIED"
    assert "adopted" in preset["oxygen_n"].evidence
    assert preset["lot_t0"].basis == "reference_temperature"
    assert "haldane_mu_opt_day" in preset and preset["mu_max_day"].value is None


def test_demo_manifest_cannot_look_like_species_evidence():
    p = demo_parameters()
    rows = provenance_rows(p)
    assert len(rows) == 8
    assert all(row["status"] == "UNVERIFIED" and row["source"] is None for row in rows)
    assert all(row["tier"] == "DEMO" and row["species"] == "SYNTHETIC" for row in rows)
    user = Parameters(0.5, 2, 80, 5, 3, 0.2, 0, 1)
    assert all(row["status"] == "UNVERIFIED" for row in provenance_rows(user))


def test_override_revokes_verification_and_warns_without_mutating_source():
    # A schema fixture; the invented range is NOT attributed to a biological publication.
    record = Parameter(
        0.5,
        0.3,
        0.7,
        "1/day",
        "https://example.org/synthetic-test-fixture",
        "VERIFIED",
        "TEST ONLY",
        "Synthetic schema fixture; not literature evidence",
        "specific_growth",
        "LITERATURE",
        "reported_range",
    )
    p = replace(
        demo_parameters(),
        mu_max_day=0.5,
        tier="LITERATURE",
        species="TEST ONLY",
        provenance=(("mu_max_day", record),),
    )
    changed = replace(p, mu_max_day=0.9)
    row = provenance_rows(changed)[0]
    assert row["status"] == "UNVERIFIED" and row["override_warning"]
    assert record.value == 0.5 and record.status == "VERIFIED"
    assert record.override_warning(0.5) is None
    assert replace(record, low=None, high=None, evidence="reported_point").override_warning(50) is None


@pytest.mark.parametrize(
    "changes",
    [
        {"source": None},
        {"value": float("nan")},
        {"low": 0.2},
        {"tier": "DEMO"},
        {"status": "NO_SPECIES_DATA"},
        {"low": 0.1, "high": 0.7, "evidence": "reported_point"},
    ],
)
def test_invalid_evidence_rejected(changes):
    base = Parameter(
        0.5,
        None,
        None,
        "1/day",
        "https://example.org/synthetic-test-fixture",
        "VERIFIED",
        "TEST ONLY",
        "Synthetic schema test",
        "specific_growth",
        "LITERATURE",
        "reported_point",
    )
    with pytest.raises(ValueError):
        replace(base, **changes)


def test_carbon_conversion_needs_explicit_fraction():
    # Arithmetic fixture only; not a minutissima preset or recommended f_C.
    carbon = Parameter(
        0.2,
        None,
        None,
        "meter**2/g_C",
        None,
        "UNVERIFIED",
        "TEST ONLY",
        "Synthetic conversion test",
        "carbon",
        "DEMO",
        "synthetic",
    )
    with pytest.raises(ValueError, match="explicit.*f_C"):
        convert_extinction(carbon, 1)
    assert convert_extinction(carbon, 1, carbon_fraction=0.4) == pytest.approx(80)
    dw = replace(carbon, unit="meter**2/g_DW", basis="dry_weight")
    assert convert_extinction(dw, 1) == pytest.approx(200)
    with pytest.raises(pint.DimensionalityError):
        convert_extinction(replace(dw, unit="1/day"), 1)
    # A linear coefficient cannot be reused under a fractional exponent.
    with pytest.raises(pint.DimensionalityError):
        convert_extinction(dw, 0.5)


def test_provenance_rejects_wrong_units_in_active_model():
    p = demo_parameters()
    records = dict(p.provenance)
    records["extinction_a0"] = replace(records["extinction_a0"], unit="meter**2/g_C", basis="carbon")
    with pytest.raises(ValueError, match="units/basis"):
        replace(p, provenance=tuple(records.items())).validate()
    with pytest.raises(ValueError):
        coefficient_unit(0)


@pytest.mark.parametrize("s", [1.0, 0.4, 0.8])
def test_extinction_recovery_and_unit_invariance(s):
    data = optical_data(s=s)
    fit = fit_extinction(
        data,
        biomass_unit="g_DW/liter",
        path_unit="meter",
        light_unit="micromole/meter**2/second",
        sublinear=s < 1,
    )
    assert fit.a0.value == pytest.approx(4, rel=1e-5)
    assert fit.a1.value == pytest.approx(0.7, rel=1e-5)
    assert fit.exponent.value == pytest.approx(s, rel=1e-5)
    assert fit.r_squared == pytest.approx(1)
    assert fit.a0.status == "UNVERIFIED" and fit.a0.low is None
    converted = data.copy()
    converted["biomass"] *= 1000
    converted["path"] *= 100
    fit2 = fit_extinction(
        converted,
        biomass_unit="g_DW/meter**3",
        path_unit="centimeter",
        light_unit="micromole/meter**2/second",
        sublinear=s < 1,
    )
    assert fit2.a0.value == pytest.approx(fit.a0.value, rel=1e-5)


@pytest.mark.parametrize("bad", ["no_blank", "too_few", "zero_signal", "too_bright", "nan", "flat"])
def test_bad_or_uninformative_optical_data_rejected(bad):
    data = optical_data()
    if bad == "no_blank":
        data = data.iloc[1:]
    elif bad == "too_few":
        data = data.iloc[:3]
    elif bad == "zero_signal":
        data.loc[1, "transmitted"] = 0
    elif bad == "too_bright":
        data.loc[1, "transmitted"] = data.loc[1, "incident"] * 2
    elif bad == "nan":
        data.loc[1, "biomass"] = np.nan
    else:
        data["transmitted"] = data["incident"] * np.exp(-data["path"])
    with pytest.raises(ValueError):
        fit_extinction(
            data, biomass_unit="g_DW/liter", path_unit="meter", light_unit="micromole/meter**2/second"
        )


def test_optical_helper_rejects_od_carbon_and_wrong_light_units():
    for biomass_unit, light_unit in [
        ("dimensionless", "micromole/meter**2/second"),
        ("g_C/liter", "micromole/meter**2/second"),
        ("g_DW/liter", "watt/meter**2"),
    ]:
        with pytest.raises(pint.DimensionalityError):
            fit_extinction(
                optical_data(), biomass_unit=biomass_unit, path_unit="meter", light_unit=light_unit
            )


@pytest.mark.parametrize("s", [1.0, 0.5])
def test_optical_limiting_cases_and_mass_balance(s):
    p = demo_parameters(extinction_exponent=s)
    c = Conditions()
    z = np.linspace(0, c.optical_path_m, 20)
    np.testing.assert_allclose(
        local_irradiance(z, 0, c, p), c.incident_light_umol_m2_s * np.exp(-p.background_extinction_m_inv * z)
    )
    clear = replace(p, extinction_a0=0, background_extinction_m_inv=0)
    assert light_limitation(0.7, c, clear) == pytest.approx(
        c.incident_light_umol_m2_s / (p.k_i_umol_m2_s + c.incident_light_umol_m2_s)
    )
    result = simulate(np.linspace(0, 15, 151), c, p)
    conserved = result.biomass_g_L + p.biomass_yield_g_per_gN * result.nitrate_n_mg_L / 1000
    np.testing.assert_allclose(conserved, conserved.iloc[0], atol=2e-6)
    assert np.all(np.diff(result.nitrate_n_mg_L) <= 1e-8)
    dark = simulate([0, 2, 4], replace(c, incident_light_umol_m2_s=0), p)
    np.testing.assert_allclose(dark.biomass_g_L, c.biomass_initial_g_L)
    assert (result.biomass_g_L >= 0).all() and (result.nitrate_n_mg_L >= 0).all()


def test_s_one_reproduces_published_baseline_linear_formula():
    p, c = demo_parameters(), Conditions()
    z = np.array([0, 0.03, 0.05])
    expected = c.incident_light_umol_m2_s * np.exp(
        -(p.background_extinction_m_inv + p.extinction_a0 * 0.4) * z
    )
    np.testing.assert_allclose(local_irradiance(z, 0.4, c, p), expected)


def test_active_configuration_rejects_cross_species_provenance():
    p = demo_parameters()
    records = dict(p.provenance)
    records["extinction_a0"] = replace(records["extinction_a0"], species="OTHER SPECIES")
    with pytest.raises(ValueError, match="source species"):
        replace(p, provenance=tuple(records.items())).validate()
